"""
CRM API views — placeholder for a later phase.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class CrmRootView(APIView):
    """``GET /api/v1/crm/`` — reports that the module is registered but empty."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="CRM module status")
    def get(self, request):
        return Response(
            {
                "module": "crm",
                "status": "not_implemented",
                "phase": 1,
                "message": "Foundation only. CRM ships in a later phase.",
                "planned": [
                    "Deal model with stages and amounts",
                    "Notes + tasks attached to leads and contacts",
                    "Unified activity feed",
                ],
            }
        )
