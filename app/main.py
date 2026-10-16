"""API FastAPI del agente conversacional de riego inteligente."""

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse

from app.agent import AgentNotConfiguredError, agent
from app.config import settings
from app.schemas import ChatRequest, ChatResponse, HealthResponse, MessageResponse


app = FastAPI(
    title="Agente Inteligente de Riego",
    version="1.0.0",
    description=(
        "Microservicio académico de un agente conversacional mínimo construido "
        "con LangChain, Groq y FastAPI. Esta versión no utiliza RAG."
    ),
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home() -> HTMLResponse:
    """Muestra una interfaz web mínima para conversar con el agente."""

    page = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(page.read_text(encoding="utf-8"))


@app.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health() -> HealthResponse:
    """Permite comprobar que el servicio está activo."""

    return HealthResponse(
        status="ok",
        service="agente-riego-ia",
        groq_configured=bool(settings.groq_api_key),
        model=settings.groq_model,
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["Agente"],
)
async def chat(payload: ChatRequest) -> ChatResponse:
    """Envía un mensaje al agente y devuelve su respuesta."""

    session_id = payload.session_id or str(uuid4())
    try:
        answer = await agent.chat(payload.message, session_id)
    except AgentNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "No fue posible consultar el modelo de Groq. Verifica la clave, "
                "el modelo configurado y tu conexión a internet."
            ),
        ) from exc

    return ChatResponse(
        answer=answer,
        session_id=session_id,
        model=settings.groq_model,
    )


@app.delete(
    "/chat/{session_id}",
    response_model=MessageResponse,
    tags=["Agente"],
)
async def clear_chat(session_id: str) -> MessageResponse:
    """Reinicia la memoria temporal de una conversación."""

    removed = agent.clear_history(session_id)
    message = "Conversación reiniciada." if removed else "La sesión no tenía historial."
    return MessageResponse(message=message)

