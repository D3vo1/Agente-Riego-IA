"""Base vectorial Chroma y recuperacion de conocimiento para RAG."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import re
from typing import Iterable
import unicodedata


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

# Palabras vacias del espanol: sin ellas, una pregunta fuera del dominio ya no
# se parece a los documentos solo por compartir "de", "la" o "que".
STOPWORDS = frozenset(
    """
    a al algo algun alguna algunas alguno algunos ante antes aqui asi aun bien
    cada como con contra cual cuales cuando cuanto de del desde donde dos e el
    ella ellas ellos en entre era es esa esas ese eso esos esta estan estar
    estas este esto estos fue ha hace hacer han hasta hay la las le les lo los
    mas me mi mis mucho muy nada ni no nos o otra otro para pero poco por porque
    puede que quien se segun ser si sin sobre son su sus tambien tan te tener
    tengo tiene todo tu un una uno unos unas usted y ya yo
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Minusculas, sin acentos, sin palabras vacias y con un singular simple."""

    decomposed = unicodedata.normalize("NFKD", text.lower())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    tokens = []
    for token in TOKEN_PATTERN.findall(plain):
        if token in STOPWORDS or len(token) < 2:
            continue
        if len(token) > 4 and token.endswith("es"):
            token = token[:-2]
        elif len(token) > 3 and token.endswith("s"):
            token = token[:-1]
        tokens.append(token)
    return tokens


@dataclass
class RetrievedChunk:
    content: str
    source: str
    chunk_id: str
    distance: float | None = None


class HashingEmbedder:
    """Embeddings locales reproducibles sin descargar modelos adicionales."""

    def __init__(self, dimensions: int = 1024) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = tokenize(text)
        features = tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
        for feature in features:
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            # Solo pesos positivos: la distancia coseno queda entre 0 y 1 y
            # vale 1 cuando la consulta no comparte ningun termino.
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_many(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


class ChromaKnowledgeBase:
    """Administra ingesta y recuperacion en una coleccion persistente Chroma."""

    def __init__(self, persist_directory: Path, collection_name: str = "agro_riego_v2") -> None:
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.embedder = HashingEmbedder()
        self._client = None
        self._collection = None

    def _get_collection(self):
        if self._collection is None:
            try:
                import chromadb
            except ImportError as exc:
                raise RuntimeError(
                    "ChromaDB no esta instalado. Ejecuta scripts\\instalar.bat o pip install -r requirements.txt."
                ) from exc
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self.persist_directory))
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def count(self) -> int:
        return int(self._get_collection().count())

    def reset(self) -> None:
        collection = self._get_collection()
        if collection.count():
            ids = collection.get(include=[]).get("ids", [])
            if ids:
                collection.delete(ids=ids)

    def ingest_directory(self, knowledge_directory: Path, reset: bool = True) -> int:
        knowledge_directory = Path(knowledge_directory)
        if reset:
            self.reset()

        records: list[tuple[str, str, dict[str, str]]] = []
        for path in sorted(knowledge_directory.rglob("*")):
            if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            relative = path.relative_to(knowledge_directory).as_posix()
            for index, chunk in enumerate(split_text(text)):
                chunk_id = hashlib.sha1(f"{relative}:{index}:{chunk}".encode()).hexdigest()
                records.append((chunk_id, chunk, {"source": relative, "chunk": str(index)}))

        if not records:
            return 0

        collection = self._get_collection()
        batch_size = 100
        for start in range(0, len(records), batch_size):
            batch = records[start : start + batch_size]
            ids = [item[0] for item in batch]
            documents = [item[1] for item in batch]
            metadatas = [item[2] for item in batch]
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=self.embedder.embed_many(documents),
            )
        return len(records)

    def search(
        self, query: str, top_k: int = 4, max_distance: float | None = None
    ) -> list[RetrievedChunk]:
        """Recupera fragmentos; descarta los que superan ``max_distance``."""

        collection = self._get_collection()
        if collection.count() == 0:
            return []
        result = collection.query(
            query_embeddings=[self.embedder.embed(query)],
            n_results=max(1, top_k),
            include=["documents", "metadatas", "distances"],
        )
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        ids = (result.get("ids") or [[]])[0]
        return [
            RetrievedChunk(
                content=document,
                source=(metadata or {}).get("source", "desconocida"),
                chunk_id=chunk_id,
                distance=distance,
            )
            for document, metadata, distance, chunk_id in zip(
                documents, metadatas, distances, ids
            )
            if max_distance is None or distance is None or distance <= max_distance
        ]


def split_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """Divide por parrafos y aplica solapamiento de caracteres."""

    clean = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not clean:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + chunk_size)
        if end < len(clean):
            boundary = clean.rfind("\n\n", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary
        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(clean):
            break
        start = max(start + 1, end - overlap)
    return chunks
