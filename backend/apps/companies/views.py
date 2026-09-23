"""
Companies API views — placeholder for a later phase.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class CompaniesRootView(APIView):
    """``GET /api/v1/companies/`` — reports that the module is registered but empty."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="Companies module status")
    def get(self, request):
        return Response(
            {
                "module": "companies",
                "status": "not_implemented",
                "phase": 1,
                "message": "Foundation only. Companies ships in a later phase.",
                "planned": [
                    "Company model with normalised domain + industry taxonomy",
                    "Deduplication by domain name during import",
                    "Bulk endpoints for large datasets",
                ],
            }
        )
