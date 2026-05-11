#!/bin/sh
set -e

echo "==> Running database migrations..."
cd /app
python -m alembic -c packages/db/migrations/alembic.ini upgrade head

echo "==> Starting API server..."
exec uvicorn apps.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
