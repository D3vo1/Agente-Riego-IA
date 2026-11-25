"""Comando para indexar la base documental en Chroma."""

from app.config import settings
from app.rag import ChromaKnowledgeBase


def main() -> None:
    knowledge_base = ChromaKnowledgeBase(settings.vector_db_path)
    count = knowledge_base.ingest_directory(settings.knowledge_dir, reset=True)
    print(f"Ingesta terminada: {count} fragmentos almacenados en Chroma.")


if __name__ == "__main__":
    main()
