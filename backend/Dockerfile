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

# Mount a persistent volume at /app/data on the hosting platform — this is the
# single directory that must survive restarts/redeploys (SQLite file + ChromaDB
# store both live here, per config.py's DATA_DIR derivation).
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data
VOLUME ["/app/data"]

USER appuser

EXPOSE 8000

# Boot sequence, every restart: migrate, then (re-)seed. `app.db.seed` and
# `app.db.index_vectors` are both idempotent — seed_all() checks each anime's slug
# before inserting, seed_admin_user() only creates/promotes (never overwrites a
# changed password), and index_facts() upserts by fact_id — so on a fresh, empty
# Railway volume this is what actually populates the launch-corpus anime/character
# data and its vector index, and on every later boot it's a fast no-op.
#
# Deliberately NOT a "copy a pre-built database into the volume" step: the local
# dev aniferret.db/chroma_store are gitignored (dev-only, and aniferret.db carries
# live user rows with real password hashes — must never ship in an image), so a
# platform building from the GitHub repo would never have them. seed_all() draws
# from SEED_ANIME in app/db/seed.py instead — committed Python source, no binary
# blob, and it never touches the `user` table at all.
#
# ${PORT:-8000} supports platforms (Render/Railway/Fly) that inject their own PORT
# env var; falls back to 8000 for a plain `docker run`.
CMD ["sh", "-c", "alembic upgrade head && python -m app.db.seed && python -m app.db.index_vectors && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
