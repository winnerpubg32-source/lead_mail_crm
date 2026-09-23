"""
Campaigns API views — placeholder for a later phase.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class CampaignsRootView(APIView):
    """``GET /api/v1/campaigns/`` — reports that the module is registered but empty."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="Campaigns module status")
    def get(self, request):
        return Response(
            {
                "module": "campaigns",
                "status": "not_implemented",
                "phase": 1,
                "message": "Foundation only. Campaigns ships in a later phase.",
                "planned": [
                    "Campaign + CampaignStep models",
                    "Audience builder on top of leads",
                    "Execution orchestration wired to the e-mail engine",
                ],
            }
        )
