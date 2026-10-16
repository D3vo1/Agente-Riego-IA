"""Pruebas del microservicio sin consumir la API real de Groq."""

from fastapi.testclient import TestClient

from app.agent import IrrigationAgent
from app.config import Settings
from app.main import app, agent


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
    async def fake_chat(message: str, session_id: str) -> str:
        assert message == "¿Cuándo debo regar?"
        assert session_id == "prueba"
        return "Riega según la humedad, el cultivo y las condiciones climáticas."

    monkeypatch.setattr(agent, "chat", fake_chat)
    response = client.post(
        "/chat",
        json={"message": "¿Cuándo debo regar?", "session_id": "prueba"},
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == "prueba"
    assert "humedad" in response.json()["answer"]


def test_clear_unknown_session() -> None:
    response = client.delete("/chat/sesion-inexistente")
    assert response.status_code == 200
    assert response.json()["message"] == "La sesión no tenía historial."


def test_groq_client_can_be_created_without_network_call() -> None:
    test_settings = Settings(groq_api_key="gsk_clave_de_prueba")
    test_agent = IrrigationAgent(test_settings)
    assert test_agent._get_llm().model_name == test_settings.groq_model
