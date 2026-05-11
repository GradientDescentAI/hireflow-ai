#!/bin/sh
set -e

echo "==> Running database migrations..."
cd /app
python -m alembic -c packages/db/migrations/alembic.ini upgrade head

echo "==> Seeding demo data (idempotent)..."
python apps/api/seed.py

echo "==> Starting API server..."
exec uvicorn apps.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
