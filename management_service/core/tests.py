from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import AuditLog, Conversation, Message


class ExchangeApiTests(APITestCase):
    def test_exchange_persists_conversation_messages_and_audit(self):
        response = self.client.post(
            reverse("exchange"),
            {
                "session_id": "demo",
                "question": "Humedad 18 % en tomate",
                "answer": "Conviene revisar el riego.",
                "sources": ["01_principios_riego.md"],
                "rules": ["R-HUM-01"],
                "bayes_probability": 0.8,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 2)
        self.assertEqual(AuditLog.objects.count(), 1)


EXCHANGE = {
    "session_id": "demo-clave",
    "question": "Humedad 18 % en tomate",
    "answer": "Conviene revisar el riego.",
}


@override_settings(MANAGEMENT_API_KEY="clave-de-prueba")
class ApiKeyTests(APITestCase):
    def test_request_without_key_is_rejected(self):
        response = self.client.post(reverse("exchange"), EXCHANGE, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_request_with_wrong_key_is_rejected(self):
        response = self.client.get("/api/rules/", HTTP_X_API_KEY="otra")
        self.assertEqual(response.status_code, 403)

    def test_request_with_key_is_accepted(self):
        response = self.client.post(
            reverse("exchange"), EXCHANGE, format="json", HTTP_X_API_KEY="clave-de-prueba"
        )
        self.assertEqual(response.status_code, 201)
