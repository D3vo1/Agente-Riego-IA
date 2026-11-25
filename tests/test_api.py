"""Pruebas del microservicio sin consumir la API real de Groq."""

from fastapi.testclient import TestClient

from app.agent import AgentResponse, IrrigationAgent
from app.config import Settings
from app.main import app, agent, management_client


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home_loads() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "AgroRiego IA" in response.text


def test_chat_validates_empty_message() -> None:
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_returns_agent_response(monkeypatch) -> None:
    async def fake_chat(message: str, session_id: str) -> AgentResponse:
        assert message == "¿Cuándo debo regar?"
        assert session_id == "prueba"
        return AgentResponse(
            answer="Riega según la humedad, el cultivo y las condiciones climáticas.",
            sources=["01_principios_riego.md"],
            rules_fired=["R-HUM-01"],
            bayes_probability=0.8,
        )

    async def fake_log_exchange(**kwargs) -> bool:
        return True

    monkeypatch.setattr(agent, "chat", fake_chat)
    monkeypatch.setattr(management_client, "log_exchange", fake_log_exchange)
    response = client.post(
        "/chat",
        json={"message": "¿Cuándo debo regar?", "session_id": "prueba"},
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == "prueba"
    assert "humedad" in response.json()["answer"]
    assert response.json()["sources"] == ["01_principios_riego.md"]
    assert response.json()["management_logged"] is True


def test_clear_unknown_session() -> None:
    response = client.delete("/chat/sesion-inexistente")
    assert response.status_code == 200
    assert response.json()["message"] == "La sesión no tenía historial."


def test_groq_client_can_be_created_without_network_call() -> None:
    test_settings = Settings(groq_api_key="gsk_clave_de_prueba")
    test_agent = IrrigationAgent(test_settings)
    assert test_agent._get_llm().model_name == test_settings.groq_model
