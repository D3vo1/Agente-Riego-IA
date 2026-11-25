"""Modelos persistentes del microservicio de gestion."""

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="irrigation_conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.session_id


class Message(models.Model):
    ROLE_CHOICES = [("user", "Usuario"), ("assistant", "Agente")]
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=12, choices=ROLE_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class AuditLog(models.Model):
    event = models.CharField(max_length=80)
    session_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class RuleConfig(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField()
    enabled = models.BooleanField(default=True)
    parameters = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class KnowledgeDocument(models.Model):
    name = models.CharField(max_length=255, unique=True)
    path = models.CharField(max_length=500)
    active = models.BooleanField(default=True)
    checksum = models.CharField(max_length=64, blank=True)
    indexed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name
