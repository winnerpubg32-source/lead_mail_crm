"""
Root URL configuration.

Everything the product exposes lives under ``/api/`` so the frontend only ever
needs one base URL (see ``config/api_urls.py`` for the versioned app routes).
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

# JSON error envelope for /api/ requests (see config/handlers.py).
handler400 = "config.handlers.bad_request"
handler403 = "config.handlers.permission_denied"
handler404 = "config.handlers.not_found"
handler500 = "config.handlers.server_error_handler"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("config.api_urls")),
]

if settings.DEBUG:
    # API schema + Swagger UI are only exposed while developing.
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="api-schema"),
            name="api-docs",
        ),
    ]
