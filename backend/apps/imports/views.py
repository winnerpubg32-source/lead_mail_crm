"""
Imports API views — placeholder for a later phase.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class ImportsRootView(APIView):
    """``GET /api/v1/imports/`` — reports that the module is registered but empty."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="Imports module status")
    def get(self, request):
        return Response(
            {
                "module": "imports",
                "status": "not_implemented",
                "phase": 1,
                "message": "Foundation only. Imports ships in a later phase.",
                "planned": [
                    "Upload endpoint with column mapping",
                    "Celery chunked processing for large files",
                    "Row-level error reporting and rollback",
                ],
            }
        )
