"""Serializadores de la API de gestion."""

from rest_framework import serializers

from .models import AuditLog, Conversation, KnowledgeDocument, Message, RuleConfig


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "session_id", "user", "created_at", "updated_at", "messages"]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"


class RuleConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleConfig
        fields = "__all__"


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeDocument
        fields = "__all__"


class ExchangeSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=100)
    question = serializers.CharField()
    answer = serializers.CharField()
    sources = serializers.ListField(child=serializers.CharField(), required=False)
    rules = serializers.ListField(child=serializers.CharField(), required=False)
    bayes_probability = serializers.FloatField(allow_null=True, required=False)
