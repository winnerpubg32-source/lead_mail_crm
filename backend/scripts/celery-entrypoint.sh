#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Celery worker / beat entrypoint.
#
# Phase 1 ships no tasks, but the broker wiring is verified here so the first
# background job added in a later phase runs without infrastructure changes.
# ---------------------------------------------------------------------------
set -euo pipefail

echo "[celery] waiting for Redis at ${REDIS_URL:-redis://redis:6379/0}…"
for attempt in $(seq 1 60); do
  if python - <<'PY' 2>/dev/null
import os
import redis

url = os.environ.get("CELERY_BROKER_URL", os.environ.get("REDIS_URL", "redis://redis:6379/0"))
redis.Redis.from_url(url, socket_connect_timeout=2).ping()
PY
  then
    echo "[celery] Redis is reachable."
    break
  fi
  if [ "$attempt" -eq 60 ]; then
    echo "[celery] Redis did not become ready in time." >&2
    exit 1
  fi
  sleep 1
done

echo "[celery] starting: $*"
exec "$@"
