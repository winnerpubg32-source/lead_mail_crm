#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Backend container entrypoint.
#
# Waits for PostgreSQL, applies migrations (idempotent) and then execs whatever
# command docker compose passed (runserver in development, gunicorn in prod).
# ---------------------------------------------------------------------------
set -euo pipefail

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

echo "[entrypoint] waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}…"
for attempt in $(seq 1 60); do
  if python - <<'PY' 2>/dev/null
import os
import socket

host = os.environ.get("POSTGRES_HOST", "postgres")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
with socket.create_connection((host, port), timeout=2):
    pass
PY
  then
    echo "[entrypoint] PostgreSQL is accepting connections."
    break
  fi
  if [ "$attempt" -eq 60 ]; then
    echo "[entrypoint] PostgreSQL did not become ready in time." >&2
    exit 1
  fi
  sleep 1
done

echo "[entrypoint] applying database migrations…"
python manage.py migrate --noinput

if [ "${DJANGO_COLLECTSTATIC:-1}" = "1" ] && [ "${DJANGO_SETTINGS_MODULE%%/*}" = "config.settings.production" ]; then
  echo "[entrypoint] collecting static files…"
  python manage.py collectstatic --noinput
fi

echo "[entrypoint] starting: $*"
exec "$@"
