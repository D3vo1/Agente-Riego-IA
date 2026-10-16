"""Configuración central de la aplicación."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Valores configurables mediante variables de entorno."""

    groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    temperature: float = float(os.getenv("TEMPERATURE", "0.2"))
    max_history_messages: int = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))


settings = Settings()

