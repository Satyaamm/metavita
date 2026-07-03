# MetaVita API — multi-stage build.
# Build context must be the repo root: docker build -f apps/api/Dockerfile .
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: libmagic for filetype sniffing; build tools for any wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 curl \
    && rm -rf /var/lib/apt/lists/*

# Install the workspace packages first (path deps), then the API.
COPY packages/runtime /app/packages/runtime
COPY packages/providers /app/packages/providers
RUN pip install ./packages/runtime ./packages/providers

COPY apps/api /app/apps/api
RUN pip install ./apps/api

# Non-root runtime user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Run migrations then serve. DATABASE_URL etc. come from the environment.
CMD ["sh", "-c", "cd /app/apps/api && alembic upgrade head && uvicorn metavita_api.main:app --host 0.0.0.0 --port 8000"]
