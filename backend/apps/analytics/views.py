"""
Analytics API views — placeholder for a later phase.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class AnalyticsRootView(APIView):
    """``GET /api/v1/analytics/`` — reports that the module is registered but empty."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="Analytics module status")
    def get(self, request):
        return Response(
            {
                "module": "analytics",
                "status": "not_implemented",
                "phase": 1,
                "message": "Foundation only. Analytics ships in a later phase.",
                "planned": [
                    "Nightly aggregation into metric tables",
                    "KPI endpoints for the dashboard cards",
                    "Source and campaign performance breakdowns",
                ],
            }
        )
