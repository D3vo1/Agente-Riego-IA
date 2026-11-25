from pathlib import Path

from app.rag import ChromaKnowledgeBase, HashingEmbedder, split_text


def test_hashing_embeddings_are_deterministic() -> None:
    embedder = HashingEmbedder(dimensions=64)
    first = embedder.embed("humedad baja en tomate")
    second = embedder.embed("humedad baja en tomate")
    assert first == second
    assert len(first) == 64


def test_split_text_creates_overlapping_chunks() -> None:
    text = "A" * 700 + "\n\n" + "B" * 700
    chunks = split_text(text, chunk_size=800, overlap=100)
    assert len(chunks) >= 2


def test_chroma_ingestion_and_search(tmp_path: Path) -> None:
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    (knowledge / "riego.md").write_text(
        "El suelo arenoso drena rapido. La humedad baja requiere inspeccion del cultivo.",
        encoding="utf-8",
    )
    database = ChromaKnowledgeBase(tmp_path / "chroma", collection_name="test_collection")
    assert database.ingest_directory(knowledge) == 1
    results = database.search("humedad baja en suelo arenoso", top_k=1)
    assert results
    assert results[0].source == "riego.md"


def test_off_topic_questions_retrieve_nothing(tmp_path: Path) -> None:
    database = ChromaKnowledgeBase(tmp_path / "chroma", collection_name="test_off_topic")
    database.ingest_directory(Path("knowledge"))
    assert database.search("¿Quién ganó el mundial?", top_k=4, max_distance=0.95) == []
    assert database.search("Cuál es la capital de Francia", top_k=4, max_distance=0.95) == []


def test_on_topic_questions_find_the_right_document(tmp_path: Path) -> None:
    database = ChromaKnowledgeBase(tmp_path / "chroma", collection_name="test_on_topic")
    database.ingest_directory(Path("knowledge"))
    results = database.search("fuga eléctrica en la bomba", top_k=4, max_distance=0.95)
    assert results[0].source == "05_seguridad.md"
    results = database.search("mi sensor marca valores raros", top_k=4, max_distance=0.95)
    assert results[0].source == "04_sensores_datos.md"
