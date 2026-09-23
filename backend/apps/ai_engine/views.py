"""
AI engine API views — placeholder for a later phase.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class AiEngineRootView(APIView):
    """``GET /api/v1/ai-engine/`` — reports that the module is registered but empty."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="AI engine module status")
    def get(self, request):
        return Response(
            {
                "module": "ai_engine",
                "status": "not_implemented",
                "phase": 1,
                "message": "Foundation only. AI engine ships in a later phase.",
                "planned": [
                    "Provider abstraction (OpenAI / Anthropic / local)",
                    "Prompt templates with brand voice controls",
                    "Cost + token accounting per generation",
                ],
            }
        )
