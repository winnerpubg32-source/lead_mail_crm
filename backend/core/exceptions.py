"""Consistent API error envelope for the whole product.

Success responses are plain payloads, errors always look like::

    {"error": {"code": "not_found", "message": "...", "details": {...}}}
"""

from __future__ import annotations

from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_429_TOO_MANY_REQUESTS: "throttled",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "server_error",
}


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Wrap DRF's default handler so every failure shares one JSON shape."""
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=getattr(exc, "message_dict", exc.messages))

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    code = getattr(exc, "default_code", None) or ERROR_CODES.get(response.status_code, "error")
    detail = response.data
    details = detail if isinstance(detail, dict) else {}

    if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
        detail = detail["detail"]

    response.data = {
        "error": {
            "code": str(code) if not isinstance(exc, Http404 | ObjectDoesNotExist) else "not_found",
            "message": str(detail)
            if not isinstance(detail, dict)
            else "Request could not be processed.",
            "details": details,
        }
    }
    return response


class ServiceUnavailable(APIException):
    """Raised when a dependency (database, redis, broker) is not reachable."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Service temporarily unavailable."
    default_code = "service_unavailable"
