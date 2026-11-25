"""API FastAPI del agente conversacional de riego inteligente."""

from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse

from app.agent import AgentNotConfiguredError, agent
from app.config import settings
from app.management_client import management_client
from app.schemas import ChatRequest, ChatResponse, HealthResponse, MessageResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Prepara el indice documental sin impedir el arranque ante un fallo."""

    try:
        agent.ensure_knowledge_base()
    except Exception:
        pass
    yield


app = FastAPI(
    title="Agente Inteligente de Riego",
    version="2.0.0",
    description=(
        "Microservicio academico con RAG, base vectorial Chroma, reglas de "
        "produccion y razonamiento bayesiano."
    ),
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home() -> HTMLResponse:
    """Muestra una interfaz web mínima para conversar con el agente."""

    page = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(page.read_text(encoding="utf-8"))


@app.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health() -> HealthResponse:
    """Permite comprobar que el servicio está activo."""

    try:
        chunk_count = agent.knowledge_base.count()
    except Exception:
        chunk_count = 0
    return HealthResponse(
        status="ok",
        service="agente-riego-ia",
        groq_configured=bool(settings.groq_api_key),
        model=settings.groq_model,
        rag_ready=chunk_count > 0,
        knowledge_chunks=chunk_count,
        django_logging_enabled=settings.django_logging_enabled,
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
        result = await agent.chat(payload.message, session_id)
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

    logged = await management_client.log_exchange(
        session_id=session_id,
        question=payload.message,
        answer=result.answer,
        sources=result.sources,
        rules=result.rules_fired,
        bayes_probability=result.bayes_probability,
    )
    return ChatResponse(
        answer=result.answer,
        session_id=session_id,
        model=settings.groq_model,
        sources=result.sources,
        rules_fired=result.rules_fired,
        bayes_probability=result.bayes_probability,
        reasoning=result.reasoning,
        management_logged=logged,
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

