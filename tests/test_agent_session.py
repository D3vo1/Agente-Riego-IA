"""El agente recuerda los datos de la conversacion y limita la memoria."""

import asyncio
from types import SimpleNamespace

from app.agent import IrrigationAgent
from app.config import Settings


class EmptyKnowledgeBase:
    def count(self) -> int:
        return 0

    def search(self, query: str, top_k: int, max_distance: float | None = None):
        return []


class FakeLLM:
    def __init__(self) -> None:
        self.calls = []

    async def ainvoke(self, messages):
        self.calls.append(messages)
        return SimpleNamespace(content="Respuesta de prueba.")


def make_agent(**settings) -> tuple[IrrigationAgent, FakeLLM]:
    llm = FakeLLM()
    agent = IrrigationAgent(
        Settings(groq_api_key="gsk_prueba", **settings),
        knowledge_base=EmptyKnowledgeBase(),
    )
    agent._get_llm = lambda: llm
    return agent, llm


def test_facts_from_previous_messages_reach_rules_and_context() -> None:
    agent, llm = make_agent()
    asyncio.run(agent.chat("Tengo jitomate en suelo arenoso", "s1"))
    result = asyncio.run(agent.chat("La humedad del suelo es 20 %", "s1"))

    assert result.facts["cultivo"] == "tomate"
    assert result.facts["humedad_suelo"] == 20
    assert "R-SUELO-01" in result.rules_fired
    assert result.bayes_probability is not None and result.bayes_probability > 0.6
    assert "'cultivo': 'tomate'" in llm.calls[-1][0].content
    assert len(llm.calls[-1]) == 4  # sistema + turno previo (2) + mensaje nuevo


def test_sessions_do_not_share_facts() -> None:
    agent, _ = make_agent()
    asyncio.run(agent.chat("Tengo jitomate", "a"))
    result = asyncio.run(agent.chat("humedad 20 %", "b"))
    assert result.facts["cultivo"] is None


def test_clear_history_forgets_facts() -> None:
    agent, _ = make_agent()
    asyncio.run(agent.chat("Tengo jitomate", "s1"))
    assert agent.clear_history("s1") is True
    result = asyncio.run(agent.chat("humedad 20 %", "s1"))
    assert result.facts["cultivo"] is None


def test_oldest_session_is_dropped_when_limit_is_reached() -> None:
    agent, _ = make_agent(max_sessions=2)
    for session_id in ("a", "b", "c"):
        asyncio.run(agent.chat("hola", session_id))
    assert agent.clear_history("a") is False
    assert agent.clear_history("c") is True


def test_disabled_rules_from_management_are_applied() -> None:
    agent, _ = make_agent()
    agent.set_disabled_rules({"R-TEMP-01"})
    result = asyncio.run(agent.chat("tomate con humedad 20 % y temperatura 35", "s1"))
    assert "R-TEMP-01" not in result.rules_fired
    assert "R-HUM-01" in result.rules_fired
