"""
Leads API views — placeholder for a later phase.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class LeadsRootView(APIView):
    """``GET /api/v1/leads/`` — reports that the module is registered but empty."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="Leads module status")
    def get(self, request):
        return Response(
            {
                "module": "leads",
                "status": "not_implemented",
                "phase": 1,
                "message": "Foundation only. Leads ships in a later phase.",
                "planned": [
                    "Lead model with status pipeline and qualification signals",
                    "Lead scoring inputs from the AI engine",
                    "Assignment / ownership rules",
                ],
            }
        )
