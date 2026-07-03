# MetaVita ingestion worker (Arq).
# Build context must be the repo root: docker build -f apps/worker/Dockerfile .
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY packages/runtime /app/packages/runtime
COPY packages/providers /app/packages/providers
RUN pip install ./packages/runtime ./packages/providers

COPY apps/api /app/apps/api
COPY apps/worker /app/apps/worker
RUN pip install ./apps/api ./apps/worker

RUN useradd --create-home --uid 10001 appuser
USER appuser

CMD ["arq", "metavita_worker.worker.WorkerSettings"]
