"""
Development settings — the default for ``manage.py`` and docker compose.

Relaxed security so the stack is comfortable to work with locally. Never use
these values for a public deployment.
"""

from __future__ import annotations

from .base import *
from .base import env

DEBUG = env.bool("DJANGO_DEBUG", default=True)

# The frontend is served by Vite (and proxied preview hosts) during
# development, so the Django host allow-list is intentionally permissive here.
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)

# Django's own staticfile view serves vendor assets in DEBUG, so WhiteNoise is
# removed from the stack locally (it stays in production.py).
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m.lower()]

# Vendor static files (DRF, admin) are served straight from the source tree.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}
