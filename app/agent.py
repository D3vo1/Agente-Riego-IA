"""Agente de riego con RAG, reglas y razonamiento bayesiano."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.bayes import bayes_estimator
from app.config import Settings, settings
from app.rag import ChromaKnowledgeBase
from app.rules import rule_engine


SYSTEM_PROMPT = """
Eres AgroRiego, un agente academico especializado en riego inteligente y uso
responsable del agua. Responde en espanol claro, profesional y breve.

Combinas tres tipos de razonamiento:
1. Conocimiento recuperado de una base documental RAG.
2. Reglas deterministas de seguridad y decision.
3. Una estimacion bayesiana demostrativa de necesidad de riego.

Reglas obligatorias:
- Distingue los datos aportados por el usuario de los supuestos.
- Fundamenta la respuesta en el contexto recuperado cuando sea pertinente.
- Menciona las fuentes con el formato [Fuente: nombre-del-archivo].
- Explica de forma sencilla las reglas activadas y la incertidumbre.
- Nunca afirmes que leiste sensores, consultaste clima en tiempo real o
  accionaste bombas o valvulas.
- Los umbrales y probabilidades son academicos; recomienda verificar las
  condiciones reales y calibrar el sistema con apoyo agronomico.
- Ante riesgo electrico, fuga, inundacion, contaminacion o equipo danado,
  recomienda detener el sistema de forma segura y solicitar revision tecnica.
- Si faltan datos esenciales, solicita cultivo, etapa, suelo o sustrato,
  humedad, clima y sistema de riego.
""".strip()


@dataclass
class AgentResponse:
    answer: str
    sources: list[str] = field(default_factory=list)
    rules_fired: list[str] = field(default_factory=list)
    bayes_probability: float | None = None
    reasoning: list[str] = field(default_factory=list)


class AgentNotConfiguredError(RuntimeError):
    """La clave de Groq todavia no esta configurada."""


class IrrigationAgent:
    """Orquesta conversacion, recuperacion, reglas y probabilidad."""

    def __init__(
        self,
        config: Settings = settings,
        knowledge_base: ChromaKnowledgeBase | None = None,
    ) -> None:
        self.config = config
        self._llm: ChatGroq | None = None
        self.knowledge_base = knowledge_base or ChromaKnowledgeBase(config.vector_db_path)
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

    def ensure_knowledge_base(self) -> int:
        """Crea el indice inicial cuando la coleccion esta vacia."""

        if self.knowledge_base.count() == 0 and self.config.knowledge_dir.exists():
            return self.knowledge_base.ingest_directory(self.config.knowledge_dir)
        return self.knowledge_base.count()

    async def chat(self, message: str, session_id: str) -> AgentResponse:
        clean_message = message.strip()
        rules = rule_engine.evaluate(clean_message)
        bayes = bayes_estimator.estimate(rules.facts)

        try:
            chunks = await asyncio.to_thread(
                self.knowledge_base.search, clean_message, self.config.rag_top_k
            )
        except RuntimeError:
            chunks = []

        context = self._build_context(chunks, rules, bayes)
        history = self._histories[session_id]
        recent_messages = history.messages[-self.config.max_history_messages :]
        messages = [SystemMessage(content=f"{SYSTEM_PROMPT}\n\n{context}"), *recent_messages]
        messages.append(HumanMessage(content=clean_message))

        response: Any = await self._get_llm().ainvoke(messages)
        answer = response.content if isinstance(response.content, str) else str(response.content)
        history.add_user_message(clean_message)
        history.add_ai_message(answer)

        sources = list(dict.fromkeys(chunk.source for chunk in chunks))
        reasoning = list(rules.recommendations)
        if bayes.explanation:
            reasoning.append(bayes.explanation)
        return AgentResponse(
            answer=answer,
            sources=sources,
            rules_fired=rules.fired_rules,
            bayes_probability=bayes.probability,
            reasoning=reasoning,
        )

    @staticmethod
    def _build_context(chunks, rules, bayes) -> str:
        knowledge = "\n\n".join(
            f"[Fuente: {chunk.source}]\n{chunk.content}" for chunk in chunks
        ) or "No se recuperaron fragmentos documentales para esta consulta."
        facts = {
            "cultivo": rules.facts.crop,
            "suelo": rules.facts.soil,
            "humedad": rules.facts.moisture,
            "temperatura": rules.facts.temperature,
            "lluvia_esperada": rules.facts.rain_expected,
        }
        probability = (
            f"{bayes.probability * 100:.1f} %" if bayes.probability is not None else "no calculada"
        )
        return (
            "CONTEXTO RAG\n"
            f"{knowledge}\n\n"
            "ANALISIS DETERMINISTA\n"
            f"Hechos: {facts}\n"
            f"Reglas activadas: {rules.fired_rules or ['ninguna']}\n"
            f"Recomendaciones: {rules.recommendations or ['ninguna']}\n"
            f"Datos faltantes: {rules.missing_data or ['ninguno']}\n\n"
            "ANALISIS PROBABILISTICO\n"
            f"Probabilidad demostrativa de necesidad de riego: {probability}.\n"
            f"Explicacion: {bayes.explanation}"
        )

    def clear_history(self, session_id: str) -> bool:
        return self._histories.pop(session_id, None) is not None


agent = IrrigationAgent()
