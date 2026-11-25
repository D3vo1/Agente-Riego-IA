"""Agente de riego con RAG, reglas y razonamiento bayesiano."""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.bayes import bayes_estimator
from app.config import Settings, settings
from app.rag import ChromaKnowledgeBase
from app.rules import IrrigationFacts, IrrigationRuleEngine


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
- Los hechos del analisis determinista acumulan lo que el usuario dijo en
  mensajes anteriores de esta conversacion; no vuelvas a pedir lo que ya dio.
- Si el cultivo no esta en la base de conocimiento, dilo y aclara que los
  umbrales son genericos.
- La humedad ambiental o relativa no es humedad del suelo; no las confundas.
""".strip()


@dataclass
class SessionState:
    """Memoria volatil de una conversacion: mensajes y hechos acumulados."""

    messages: list[BaseMessage] = field(default_factory=list)
    facts: IrrigationFacts = field(default_factory=IrrigationFacts)


@dataclass
class AgentResponse:
    answer: str
    sources: list[str] = field(default_factory=list)
    rules_fired: list[str] = field(default_factory=list)
    bayes_probability: float | None = None
    reasoning: list[str] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    missing_data: list[str] = field(default_factory=list)


class AgentNotConfiguredError(RuntimeError):
    """La clave de Groq todavia no esta configurada."""


class IrrigationAgent:
    """Orquesta conversacion, recuperacion, reglas y probabilidad."""

    def __init__(
        self,
        config: Settings = settings,
        knowledge_base: ChromaKnowledgeBase | None = None,
        rule_engine: IrrigationRuleEngine | None = None,
    ) -> None:
        self.config = config
        self._llm: ChatGroq | None = None
        self.knowledge_base = knowledge_base or ChromaKnowledgeBase(config.vector_db_path)
        self.rule_engine = rule_engine or IrrigationRuleEngine()
        # Orden de uso reciente: al superar max_sessions se olvida la mas antigua.
        self._sessions: OrderedDict[str, SessionState] = OrderedDict()

    def _session(self, session_id: str) -> SessionState:
        state = self._sessions.get(session_id)
        if state is None:
            state = SessionState()
            self._sessions[session_id] = state
            while len(self._sessions) > max(1, self.config.max_sessions):
                self._sessions.popitem(last=False)
        else:
            self._sessions.move_to_end(session_id)
        return state

    def set_disabled_rules(self, codes: set[str]) -> None:
        """Aplica la configuracion de reglas que viene del servicio de gestion."""

        self.rule_engine.disabled_rules = set(codes)

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
        state = self._session(session_id)
        rules = self.rule_engine.evaluate(clean_message, previous=state.facts)
        bayes = bayes_estimator.estimate(rules.facts)

        try:
            chunks = await asyncio.to_thread(
                self.knowledge_base.search,
                clean_message,
                self.config.rag_top_k,
                self.config.rag_max_distance,
            )
        except RuntimeError:
            chunks = []

        context = self._build_context(chunks, rules, bayes)
        recent_messages = state.messages[-self.config.max_history_messages :]
        messages = [SystemMessage(content=f"{SYSTEM_PROMPT}\n\n{context}"), *recent_messages]
        messages.append(HumanMessage(content=clean_message))

        response: Any = await self._get_llm().ainvoke(messages)
        answer = response.content if isinstance(response.content, str) else str(response.content)
        state.messages.extend([HumanMessage(content=clean_message), AIMessage(content=answer)])
        # Solo se guardan los hechos cuando el modelo respondio sin error.
        state.facts = rules.facts

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
            facts=self._facts_summary(rules.facts),
            missing_data=rules.missing_data,
        )

    @staticmethod
    def _facts_summary(facts: IrrigationFacts) -> dict[str, Any]:
        return {
            "cultivo": facts.crop,
            "cultivo_no_reconocido": facts.unknown_crop,
            "suelo": facts.soil,
            "humedad_suelo": facts.moisture,
            "humedad_ambiental": facts.air_humidity,
            "temperatura": facts.temperature,
            "lluvia_esperada": facts.rain_expected,
        }

    @staticmethod
    def _build_context(chunks, rules, bayes) -> str:
        knowledge = "\n\n".join(
            f"[Fuente: {chunk.source}]\n{chunk.content}" for chunk in chunks
        ) or "No se recuperaron fragmentos documentales para esta consulta."
        facts = IrrigationAgent._facts_summary(rules.facts)
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
        return self._sessions.pop(session_id, None) is not None


agent = IrrigationAgent()
