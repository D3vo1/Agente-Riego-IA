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


class HealthResponse(BaseModel):
    """Estado básico del microservicio."""

    status: str
    service: str
    groq_configured: bool
    model: str


class MessageResponse(BaseModel):
    """Respuesta simple para operaciones administrativas."""

    message: str

