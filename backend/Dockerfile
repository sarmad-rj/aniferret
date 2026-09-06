# syntax=docker/dockerfile:1

# --- builder: compile deps into a venv, discarded after this stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- runtime: slim image, non-root, no build toolchain ---
FROM python:3.11-slim

RUN useradd --create-home --uid 1000 appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Required in production (set these on the hosting platform, not baked into the
# image): JWT_SECRET_KEY (random per-process otherwise — sessions won't survive a
# restart across multiple instances), CORS_ORIGINS (JSON array, e.g.
# ["https://your-app.vercel.app"]), GEMINI_API_KEY (optional — app degrades to
# deterministic fallbacks without it). ADMIN_EMAIL + ADMIN_PASSWORD (optional, but
# it's the *only* way to get an admin account in a deployed environment — there is
# no public self-service admin registration by design): set both and the CMD below
# provisions/promotes that account on every boot, idempotently, via seed_admin_user().
ENV DATA_DIR=/app/data \
    DATABASE_URL=sqlite+aiosqlite:////app/data/aniferret.db \
    CHROMA_PERSIST_DIR=/app/data/chroma_store

WORKDIR /app
COPY --chown=appuser:appuser . .

# Ensure /app/data directory exists with proper permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data && chmod 755 /app/data

USER appuser

EXPOSE 8000

# Boot sequence with retry logic: wait for volume to stabilize before migrations
CMD ["/bin/bash", "-c", "\
  for attempt in {1..5}; do \
    echo \"Attempt $attempt: waiting for volume to stabilize...\"; \
    if [ -w /app/data ]; then \
      echo \"Volume is writable\"; \
      alembic upgrade head && python -m app.db.seed && python -m app.db.index_vectors && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}; \
      exit $?; \
    fi; \
    sleep 2; \
  done; \
  echo \"ERROR: /app/data is not writable after 5 attempts\"; \
  exit 1 \
"]

