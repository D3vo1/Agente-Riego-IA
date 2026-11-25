"""Cliente de gestion: clave de API y lectura de reglas desactivadas."""

import asyncio

import httpx

from app import management_client as module
from app.config import Settings
from app.management_client import ManagementClient


def use_transport(monkeypatch, handler) -> list[httpx.Request]:
    seen: list[httpx.Request] = []
    real_client = httpx.AsyncClient

    def recording(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    monkeypatch.setattr(
        module.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(recording), **kwargs),
    )
    return seen


def test_disabled_rules_are_read_and_key_is_sent(monkeypatch) -> None:
    seen = use_transport(
        monkeypatch,
        lambda request: httpx.Response(
            200,
            json=[
                {"code": "R-TEMP-01", "enabled": False},
                {"code": "R-HUM-01", "enabled": True},
            ],
        ),
    )
    client = ManagementClient(Settings(management_api_key="secreta"))
    assert asyncio.run(client.fetch_disabled_rules()) == {"R-TEMP-01"}
    assert seen[0].headers["X-API-Key"] == "secreta"
    assert seen[0].url.path == "/api/rules/"


def test_unreachable_service_keeps_current_rules(monkeypatch) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin conexion", request=request)

    use_transport(monkeypatch, fail)
    assert asyncio.run(ManagementClient(Settings()).fetch_disabled_rules()) is None


def test_log_exchange_reports_failure(monkeypatch) -> None:
    use_transport(monkeypatch, lambda request: httpx.Response(403))
    client = ManagementClient(Settings())
    logged = asyncio.run(
        client.log_exchange(
            session_id="s", question="q", answer="a", sources=[], rules=[], bayes_probability=None
        )
    )
    assert logged is False
