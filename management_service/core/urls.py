from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuditLogViewSet,
    ConversationViewSet,
    ExchangeView,
    KnowledgeDocumentViewSet,
    MessageViewSet,
    RuleConfigViewSet,
)


router = DefaultRouter()
router.register("conversations", ConversationViewSet)
router.register("messages", MessageViewSet)
router.register("audit-logs", AuditLogViewSet)
router.register("rules", RuleConfigViewSet)
router.register("knowledge-documents", KnowledgeDocumentViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("exchanges/", ExchangeView.as_view(), name="exchange"),
]
