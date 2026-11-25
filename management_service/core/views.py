"""Vistas REST y contrato de intercambio con FastAPI."""

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuditLog, Conversation, KnowledgeDocument, Message, RuleConfig
from .serializers import (
    AuditLogSerializer,
    ConversationSerializer,
    ExchangeSerializer,
    KnowledgeDocumentSerializer,
    MessageSerializer,
    RuleConfigSerializer,
)


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.prefetch_related("messages").all()
    serializer_class = ConversationSerializer


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Message.objects.select_related("conversation").all()
    serializer_class = MessageSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer


class RuleConfigViewSet(viewsets.ModelViewSet):
    queryset = RuleConfig.objects.all()
    serializer_class = RuleConfigSerializer


class KnowledgeDocumentViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeDocument.objects.all()
    serializer_class = KnowledgeDocumentSerializer


class ExchangeView(APIView):
    """Recibe una interaccion completa desde el microservicio FastAPI."""

    @transaction.atomic
    def post(self, request):
        serializer = ExchangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        conversation, _ = Conversation.objects.get_or_create(session_id=data["session_id"])
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=data["question"],
        )
        metadata = {
            "sources": data.get("sources", []),
            "rules": data.get("rules", []),
            "bayes_probability": data.get("bayes_probability"),
        }
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=data["answer"],
            metadata=metadata,
        )
        AuditLog.objects.create(
            event="agent_exchange",
            session_id=data["session_id"],
            details=metadata,
        )
        return Response(
            {"status": "stored", "conversation_id": conversation.id},
            status=status.HTTP_201_CREATED,
        )
