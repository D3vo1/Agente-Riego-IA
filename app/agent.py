"""Agente conversacional mínimo construido con LangChain y Groq."""

from collections import defaultdict
from typing import Any

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import Settings, settings


SYSTEM_PROMPT = """
Eres AgroRiego, un agente conversacional especializado en riego inteligente y
uso responsable del agua. Responde en español claro, profesional y breve.

Tus objetivos son:
1. Orientar sobre riego, humedad del suelo, horarios, cultivos y seguridad.
2. Explicar el razonamiento detrás de cada recomendación.
3. Pedir los datos que falten antes de dar una recomendación muy específica:
   cultivo, etapa, tipo de suelo o sustrato, humedad, clima y sistema de riego.

Reglas obligatorias:
- Esta es una versión académica inicial sin sensores, actuadores ni RAG.
- Nunca afirmes que leíste sensores, consultaste el clima en tiempo real o
  accionaste bombas o válvulas.
- No inventes mediciones. Distingue entre datos aportados por el usuario y
  supuestos.
- No ordenes un riego automático. Presenta la respuesta como recomendación y
  pide verificar físicamente las condiciones del cultivo.
- Ante riesgo eléctrico, fuga, inundación, contaminación o equipo dañado,
  recomienda detener el sistema de forma segura y solicitar revisión técnica.
- Si la pregunta no es del dominio, contesta brevemente y redirige al tema de
  riego inteligente.
""".strip()


class AgentNotConfiguredError(RuntimeError):
    """La clave de Groq todavía no está configurada."""


class IrrigationAgent:
    """Mantiene conversaciones en memoria y consulta un modelo alojado en Groq."""

    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self._llm: ChatGroq | None = None
        self._histories: dict[str, InMemoryChatMessageHistory] = defaultdict(
            InMemoryChatMessageHistory
        )

    def _get_llm(self) -> ChatGroq:
        if not self.config.groq_api_key:
            raise AgentNotConfiguredError(
                "Falta GROQ_API_KEY. Copia .env.example como .env y agrega tu clave de Groq."
            )

        if self._llm is None:
            self._llm = ChatGroq(
                api_key=self.config.groq_api_key,
                model=self.config.groq_model,
                temperature=self.config.temperature,
                max_retries=2,
            )
        return self._llm

    async def chat(self, message: str, session_id: str) -> str:
        """Genera una respuesta y conserva una ventana breve del historial."""

        history = self._histories[session_id]
        recent_messages = history.messages[-self.config.max_history_messages :]
        messages = [SystemMessage(content=SYSTEM_PROMPT), *recent_messages]
        messages.append(HumanMessage(content=message.strip()))

        response: Any = await self._get_llm().ainvoke(messages)
        answer = response.content
        if not isinstance(answer, str):
            answer = str(answer)

        history.add_user_message(message.strip())
        history.add_ai_message(answer)
        return answer

    def clear_history(self, session_id: str) -> bool:
        """Elimina el historial volátil de una sesión."""

        return self._histories.pop(session_id, None) is not None


agent = IrrigationAgent()

