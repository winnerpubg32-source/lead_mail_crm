"""
Email engine API views — placeholder for a later phase.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class EmailEngineRootView(APIView):
    """``GET /api/v1/email-engine/`` — reports that the module is registered but empty."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="Email engine module status")
    def get(self, request):
        return Response(
            {
                "module": "email_engine",
                "status": "not_implemented",
                "phase": 1,
                "message": "Foundation only. Email engine ships in a later phase.",
                "planned": [
                    "Daily send budget with Redis counter (max 90/day)",
                    "Per-mailbox SMTP configuration stored encrypted",
                    "Bounce/complaint handling and automatic suppression",
                ],
            }
        )
