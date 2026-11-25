"""Configuración central de la aplicación."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Valores configurables mediante variables de entorno."""

    groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
    temperature: float = float(os.getenv("TEMPERATURE", "0.2"))
    max_history_messages: int = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "4"))
    vector_db_path: Path = Path(os.getenv("VECTOR_DB_PATH", "data/chroma"))
    knowledge_dir: Path = Path(os.getenv("KNOWLEDGE_DIR", "knowledge"))
    django_service_url: str = os.getenv(
        "DJANGO_SERVICE_URL", "http://127.0.0.1:8001"
    ).strip()
    django_logging_enabled: bool = os.getenv(
        "DJANGO_LOGGING_ENABLED", "true"
    ).strip().lower() in {"1", "true", "yes", "si", "sí"}
    django_timeout_seconds: float = float(os.getenv("DJANGO_TIMEOUT_SECONDS", "2.0"))


settings = Settings()

