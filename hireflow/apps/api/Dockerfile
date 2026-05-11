FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Preserve monorepo layout so that `from apps.api.routers import ...`
# and `from packages.db.models import ...` both resolve correctly.
COPY apps/ /app/apps/
COPY packages/ /app/packages/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Copy startup script (runs migrations then starts uvicorn)
COPY apps/api/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Railway injects $PORT; fall back to 8000 for local Docker Compose
CMD ["/app/start.sh"]
