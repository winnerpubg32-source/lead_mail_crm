"""
Project-wide error handlers.

Django's built-in 404/500 pages return HTML. API clients (and the React
dashboard) need the same JSON error envelope as the rest of the API, so any
request under ``/api/`` is answered with JSON while browser requests keep the
standard Django pages.
"""

from __future__ import annotations

from django.http import JsonResponse
from django.views.defaults import page_not_found, server_error

API_PREFIX = "/api/"

API_MESSAGES = {
    400: ("bad_request", "The request could not be understood."),
    403: ("forbidden", "You do not have permission to perform this action."),
    404: ("not_found", "The requested resource was not found."),
    405: ("method_not_allowed", "This HTTP method is not allowed here."),
    500: ("server_error", "An unexpected error occurred."),
}


def _wants_json(request) -> bool:
    return request.path.startswith(API_PREFIX) or "application/json" in request.headers.get(
        "Accept", ""
    )


def _json_error(request, status_code: int) -> JsonResponse:
    code, message = API_MESSAGES[status_code]
    return JsonResponse(
        {"error": {"code": code, "message": message, "details": {}}}, status=status_code
    )


def not_found(request, exception=None):
    if _wants_json(request):
        return _json_error(request, 404)
    return page_not_found(request, exception)


def bad_request(request, exception=None):
    if _wants_json(request):
        return _json_error(request, 400)
    return JsonResponse(
        {"error": {"code": "bad_request", "message": str(exception), "details": {}}}, status=400
    )


def permission_denied(request, exception=None):
    if _wants_json(request):
        return _json_error(request, 403)
    return _json_error(request, 403)


def server_error_handler(request):  # pragma: no cover - hard to trigger in tests
    if _wants_json(request):
        return _json_error(request, 500)
    return server_error(request)
