FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc tesseract-ocr libtesseract-dev \
    # Playwright dependencies
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 && \
    rm -rf /var/lib/apt/lists/*

COPY apps/worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    # Install playwright browser for LinkedIn automation (best-effort; skip on failure)
    playwright install chromium || echo "Playwright chromium install skipped (non-fatal)"

COPY apps/ /app/apps/
COPY packages/ /app/packages/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "apps/worker/main.py"]
