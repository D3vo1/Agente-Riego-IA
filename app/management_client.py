"""Cliente tolerante a fallos para el microservicio Django de gestion."""

from __future__ import annotations

import httpx

from app.config import Settings, settings


class ManagementClient:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config

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
                    f"{self.config.django_service_url.rstrip('/')}/api/exchanges/",
                    json=payload,
                )
                response.raise_for_status()
            return True
        except (httpx.HTTPError, ValueError):
            return False


management_client = ManagementClient()
