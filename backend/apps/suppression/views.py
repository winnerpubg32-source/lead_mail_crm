"""
Suppression API views — placeholder for a later phase.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class SuppressionRootView(APIView):
    """``GET /api/v1/suppression/`` — reports that the module is registered but empty."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="Suppression module status")
    def get(self, request):
        return Response(
            {
                "module": "suppression",
                "status": "not_implemented",
                "phase": 1,
                "message": "Foundation only. Suppression ships in a later phase.",
                "planned": [
                    "Suppression entries checked before every send",
                    "One-click unsubscribe endpoint",
                    "Imported suppression lists",
                ],
            }
        )
