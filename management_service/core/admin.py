from django.contrib import admin

from .models import AuditLog, Conversation, KnowledgeDocument, Message, RuleConfig


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("session_id", "user", "created_at", "updated_at")
    search_fields = ("session_id",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("content", "conversation__session_id")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("event", "session_id", "created_at")
    list_filter = ("event",)


admin.site.register(RuleConfig)
admin.site.register(KnowledgeDocument)
