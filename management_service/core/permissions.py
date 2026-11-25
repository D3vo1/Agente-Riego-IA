"""Permisos de la API de gestion."""

import hmac

from django.conf import settings
from rest_framework.permissions import BasePermission


class HasManagementApiKey(BasePermission):
    """Exige la cabecera ``X-API-Key`` cuando ``MANAGEMENT_API_KEY`` esta definida.

    El personal autenticado en el admin de Django tambien puede usar la API
    navegable. Sin clave configurada el servicio queda abierto, como en el
    entorno local del curso.
    """

    message = "Falta la cabecera X-API-Key o no es valida."

    def has_permission(self, request, view) -> bool:
        expected = getattr(settings, "MANAGEMENT_API_KEY", "")
        if not expected:
            return True
        if request.user and request.user.is_authenticated and request.user.is_staff:
            return True
        provided = request.headers.get("X-API-Key", "")
        return hmac.compare_digest(provided.encode(), expected.encode())
