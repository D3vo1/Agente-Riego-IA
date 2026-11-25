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
