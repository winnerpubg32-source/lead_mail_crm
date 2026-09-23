"""
OutreachOS — base Django settings.

Every environment specific value is read from environment variables so the same
code base can run locally, in Docker Compose and in production without edits.
See ``.env.example`` in the repository root for the full list of variables.

Phase 1 note: only the foundation is configured here (database, DRF, CORS,
Celery, Redis). No business logic (SMTP, AI, imports, campaign execution) is
wired up yet — those modules are stubbed out under ``apps/``.
"""

from __future__ import annotations

from pathlib import Path

import environ

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# BASE_DIR  -> <repo>/backend
# ROOT_DIR  -> <repo>
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
# Load order: real environment variables always win. The repository root .env
# (used by docker compose) is read first, then an optional backend/.env.
env = environ.Env()

for env_file in (ROOT_DIR / ".env", BASE_DIR / ".env"):
    if env_file.exists():
        env.read_env(str(env_file))

APP_NAME = env("APP_NAME", default="OutreachOS")
ENVIRONMENT = env("ENVIRONMENT", default="development")

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-development-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
]

# OutreachOS domain apps. Every module is registered from day one so later
# phases only need to add models/tasks/serializers — never new plumbing.
LOCAL_APPS = [
    "core",
    "apps.accounts",
    "apps.companies",
    "apps.contacts",
    "apps.leads",
    "apps.imports",
    "apps.campaigns",
    "apps.email_engine",
    "apps.ai_engine",
    "apps.crm",
    "apps.analytics",
    "apps.suppression",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Database — PostgreSQL
# ---------------------------------------------------------------------------
# DATABASE_URL is the preferred configuration; the explicit POSTGRES_* values
# are used when it is absent (they are what docker compose injects).
DATABASE_URL = env("DATABASE_URL", default="")

if DATABASE_URL:
    _db = env.db("DATABASE_URL")
    _db.setdefault("CONN_MAX_AGE", env.int("POSTGRES_CONN_MAX_AGE", default=60))
    if _db["ENGINE"].endswith("postgresql"):
        _db.setdefault("OPTIONS", {}).setdefault(
            "connect_timeout", env.int("POSTGRES_CONNECT_TIMEOUT", default=5)
        )
    DATABASES = {"default": _db}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", default="outreachos"),
            "USER": env("POSTGRES_USER", default="outreachos"),
            "PASSWORD": env("POSTGRES_PASSWORD", default="outreachos"),
            "HOST": env("POSTGRES_HOST", default="localhost"),
            "PORT": env("POSTGRES_PORT", default="5432"),
            "CONN_MAX_AGE": env.int("POSTGRES_CONN_MAX_AGE", default=60),
            "OPTIONS": {"connect_timeout": env.int("POSTGRES_CONNECT_TIMEOUT", default=5)},
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
# Phase 1 ships a *basic* auth structure: a custom user model with e-mail login
# plus DRF session/token authentication. Password policy, 2FA, teams, roles and
# invitation flows are scheduled for a later phase.
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = env("DJANGO_LANGUAGE_CODE", default="en-us")
TIME_ZONE = env("DJANGO_TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = env("DJANGO_STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_URL = env("DJANGO_MEDIA_URL", default="/media/")
MEDIA_ROOT = Path(env("DJANGO_MEDIA_ROOT", default=str(BASE_DIR / "media")))

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    # TokenAuthentication is listed first so unauthenticated API calls receive
    # a 401 with a WWW-Authenticate challenge instead of a bare 403.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Foundation only: endpoints are open in Phase 1 so the dashboard can be
    # developed against the API without a login flow. Switch to IsAuthenticated
    # when authentication lands.
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.DefaultPagination",
    "PAGE_SIZE": env.int("API_PAGE_SIZE", default=25),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "OutreachOS API",
    "DESCRIPTION": (
        "B2B lead outreach & CRM API. Phase 1 exposes infrastructure endpoints "
        "(health, authentication basics) only."
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=False)
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)
CORS_ALLOW_CREDENTIALS = env.bool("CORS_ALLOW_CREDENTIALS", default=True)

# ---------------------------------------------------------------------------
# Redis & Celery
# ---------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_DEFAULT_QUEUE = env("CELERY_TASK_DEFAULT_QUEUE", default="outreachos")
CELERY_TASK_TIME_LIMIT = env.int("CELERY_TASK_TIME_LIMIT", default=600)
CELERY_TASK_SOFT_TIME_LIMIT = env.int("CELERY_TASK_SOFT_TIME_LIMIT", default=540)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# Phase 1 has no scheduled jobs yet; periodic tasks (daily counter reset, import
# polling) are added together with the features that need them.

# ---------------------------------------------------------------------------
# OutreachOS domain configuration
# ---------------------------------------------------------------------------
# Guard rails from the product brief. Consumed by the dashboard today, enforced
# by the email engine in a later phase.
OUTREACH_DAILY_EMAIL_LIMIT = env.int("OUTREACH_DAILY_EMAIL_LIMIT", default=90)
OUTREACH_TIMEZONE = env("OUTREACH_TIMEZONE", default="UTC")

# ---------------------------------------------------------------------------
# E-mail
# ---------------------------------------------------------------------------
# Marketing e-mail delivery (SMTP credentials, throttling) is intentionally not
# implemented in Phase 1 — the console backend keeps the foundation runnable.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="OutreachOS <no-reply@outreachos.local>")

# ---------------------------------------------------------------------------
# Frontend integration
# ---------------------------------------------------------------------------
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
