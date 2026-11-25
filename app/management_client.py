"""Cliente tolerante a fallos para el microservicio Django de gestion."""

from __future__ import annotations

import logging

import httpx

from app.config import Settings, settings


logger = logging.getLogger(__name__)


class ManagementClient:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config

    @property
    def _base_url(self) -> str:
        return f"{self.config.django_service_url.rstrip('/')}/api"

    @property
    def _headers(self) -> dict[str, str]:
        if self.config.management_api_key:
            return {"X-API-Key": self.config.management_api_key}
        return {}

    async def log_exchange(
        self,
        *,
        session_id: str,
        question: str,
        answer: str,
        sources: list[str],
        rules: list[str],
        bayes_probability: float | None,
    ) -> bool:
        if not self.config.django_logging_enabled:
            return False
        payload = {
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "sources": sources,
            "rules": rules,
            "bayes_probability": bayes_probability,
        }
        try:
            async with httpx.AsyncClient(timeout=self.config.django_timeout_seconds) as client:
                response = await client.post(
                    f"{self._base_url}/exchanges/", json=payload, headers=self._headers
                )
                response.raise_for_status()
            return True
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("No se pudo registrar la conversacion en Django: %s", exc)
            return False

    async def fetch_disabled_rules(self) -> set[str] | None:
        """Devuelve los codigos de regla desactivados en Django.

        ``None`` significa que el servicio no respondio y deben conservarse
        las reglas actuales.
        """

        if not self.config.django_logging_enabled:
            return None
        try:
            async with httpx.AsyncClient(timeout=self.config.django_timeout_seconds) as client:
                response = await client.get(f"{self._base_url}/rules/", headers=self._headers)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("No se pudo leer la configuracion de reglas en Django: %s", exc)
            return None
        items = data.get("results", data) if isinstance(data, dict) else data
        return {
            str(item["code"])
            for item in items
            if isinstance(item, dict) and "code" in item and not item.get("enabled", True)
        }


management_client = ManagementClient()
