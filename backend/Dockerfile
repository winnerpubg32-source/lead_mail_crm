# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# OutreachOS backend image (Django + DRF + Celery)
#
# Targets:
#   development (default) — Django's autoreloading dev server
#   production            — gunicorn, non-root user, collected static files
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.development

WORKDIR /app

# Runtime dependencies: libpq for PostgreSQL, curl for container healthchecks.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# --- development ------------------------------------------------------------
FROM base AS development

COPY requirements/base.txt requirements/base.txt
COPY requirements/dev.txt requirements/dev.txt
RUN pip install -r requirements/dev.txt

COPY . .

RUN chmod +x scripts/entrypoint.sh scripts/celery-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# --- production -------------------------------------------------------------
FROM base AS production

ENV DJANGO_SETTINGS_MODULE=config.settings.production

COPY requirements/base.txt requirements/base.txt
COPY requirements/prod.txt requirements/prod.txt
RUN pip install -r requirements/prod.txt

COPY . .

RUN chmod +x scripts/entrypoint.sh scripts/celery-entrypoint.sh \
    && addgroup --system django \
    && adduser --system --ingroup django django \
    && chown -R django:django /app
USER django

EXPOSE 8000
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-"]
