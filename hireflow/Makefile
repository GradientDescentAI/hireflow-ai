.PHONY: up down logs migrate shell-api shell-worker test lint fmt

up:
	docker compose up --build -d
	@echo "API: http://localhost:8000  MinIO console: http://localhost:9001"

down:
	docker compose down

logs:
	docker compose logs -f api worker

migrate:
	docker compose run --rm migrate

shell-api:
	docker compose exec api bash

shell-worker:
	docker compose exec worker bash

# ── Infrastructure only (Postgres + Redis + MinIO) ─────────
infra:
	docker compose --env-file .env up -d postgres redis minio
	@echo "✅ Postgres :5432  Redis :6379  MinIO :9000 (console :9001)"

# ── Local dev (no Docker for api/worker) ───────────────────
dev-api:
	@set -a && . ./.env && set +a && \
	  PYTHONPATH=$(shell pwd) \
	  uvicorn apps.api.main:app --reload --port 8000 \
	    --reload-dir apps/api --reload-dir packages

dev-worker:
	@set -a && . ./.env && set +a && \
	  PYTHONPATH=$(shell pwd) \
	  python -m apps.worker.main

dev: infra
	@echo ""
	@echo "  Now run in separate terminals:"
	@echo "    make migrate         ← run once on first start"
	@echo "    make dev-api         ← FastAPI :8000"
	@echo "    make dev-worker      ← LangGraph consumer"
	@echo "    cd ../frontend && npm run dev  ← Next.js :3000"
	@echo ""

# ── Database ──────────────────────────────────────────────
db-revision:
	docker compose exec api alembic -c packages/db/migrations/alembic.ini revision --autogenerate -m "$(msg)"

db-upgrade:
	docker compose exec api alembic -c packages/db/migrations/alembic.ini upgrade head

db-downgrade:
	docker compose exec api alembic -c packages/db/migrations/alembic.ini downgrade -1

# ── Tests ─────────────────────────────────────────────────
test:
	docker compose exec api pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

# ── Code quality ──────────────────────────────────────────
lint:
	ruff check .

fmt:
	ruff format .
	isort .
