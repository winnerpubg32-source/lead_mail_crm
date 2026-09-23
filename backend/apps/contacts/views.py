"""
Contacts API views — placeholder for a later phase.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class ContactsRootView(APIView):
    """``GET /api/v1/contacts/`` — reports that the module is registered but empty."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()

    @extend_schema(responses={200: None}, summary="Contacts module status")
    def get(self, request):
        return Response(
            {
                "module": "contacts",
                "status": "not_implemented",
                "phase": 1,
                "message": "Foundation only. Contacts ships in a later phase.",
                "planned": [
                    "Contact model linked to Company and Lead",
                    "E-mail normalisation + validation status (valid / risky / invalid)",
                    "Role detection for decision-maker targeting",
                ],
            }
        )
