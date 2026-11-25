"""Esquemas de entrada y salida de la API."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Mensaje enviado por el usuario."""

    message: str = Field(
        min_length=1,
        max_length=2_000,
        description="Pregunta o mensaje para el agente de riego.",
        examples=["¿Debo regar mi cultivo de tomate si la humedad del suelo es 18 %?"],
    )
    session_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Identificador opcional para conservar el contexto de la conversación.",
        examples=["usuario-demo"],
    )


class ChatResponse(BaseModel):
    """Respuesta producida por el agente."""

    answer: str
    session_id: str
    model: str
    sources: list[str] = Field(default_factory=list)
    rules_fired: list[str] = Field(default_factory=list)
    bayes_probability: float | None = None
    reasoning: list[str] = Field(default_factory=list)
    management_logged: bool = False


class HealthResponse(BaseModel):
    """Estado básico del microservicio."""

    status: str
    service: str
    groq_configured: bool
    model: str
    rag_ready: bool
    knowledge_chunks: int
    django_logging_enabled: bool


class MessageResponse(BaseModel):
    """Respuesta simple para operaciones administrativas."""

    message: str

