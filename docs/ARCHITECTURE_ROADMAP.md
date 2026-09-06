# AniFerret Architecture Roadmap — Postgres + pgvector + Async Ingestion

Current deployment (SQLite + local ChromaDB on a persistent-disk container) is a
deliberate stopgap, not the end state. This document specs the next-phase migration.

## 1. Why move off SQLite + local ChromaDB

Two independent, file-based stores today:
- `aiosqlite` — `Character`, `Faction`, `TemporalFact`, etc., in `aniferret.db`.
- `ChromaDB` (`PersistentClient`) — a **separate copy** of each `TemporalFact`'s text +
  metadata, re-embedded and indexed independently in `chroma_store/`.

This split is workable at 4 titles but doesn't scale, and it has a real failure mode
we already hit in production data: **gate drift**. Spoiler gating is enforced twice —
once in `query_service.answer_query()` (Python, against SQLite) and again in
`vector_store.semantic_search()` (Chroma's own `where` filter, against its own copy).
When a `TemporalFact` changes in SQLite and the vector store isn't re-indexed to
match, the two stores disagree about what exists — which is exactly what happened
after an early, abandoned dynamic-ingestion attempt: 36 orphaned Chroma entries for
characters that no longer existed in the SQL data (`Lola`, `Ross`, and others) kept
surfacing in Lore Assistant answers until they were manually purged and re-indexed.
Nothing caught this automatically, because there are two systems of record for one
decision.

**Target:** Postgres (Supabase or Neon, both offer managed pgvector) as the single
source of truth for both structured facts and their embeddings.

```
CREATE TABLE temporal_fact (
    fact_id             SERIAL PRIMARY KEY,
    anime_id            INT REFERENCES anime(id) ON DELETE CASCADE,
    subject             TEXT NOT NULL,
    predicate           TEXT NOT NULL,
    object              TEXT NOT NULL,
    source_citation     TEXT NOT NULL,
    first_revealed_at   TEXT NOT NULL,           -- checkpoint string, e.g. "S1E45"
    revealed_ordinal    INT NOT NULL,             -- checkpoint_to_ordinal(first_revealed_at), indexed
    first_hinted_at     TEXT,
    confidence          FLOAT NOT NULL,
    source              TEXT NOT NULL DEFAULT 'curated',
    embedding           VECTOR(384)               -- same dim as the current DefaultEmbeddingFunction
);
CREATE INDEX temporal_fact_embedding_idx ON temporal_fact
    USING hnsw (embedding vector_cosine_ops);
```

## 2. Unified temporal filtering — the actual mechanism

Today, `semantic_search()` runs a Chroma metadata `where` filter, then a *separate*
Python `is_revealed()` check already happened upstream in `query_service.py` against
SQLite. With `embedding` living in the same row as `first_revealed_at`, both
similarity ranking and spoiler gating become **one SQL query, one source of truth**:

```sql
SELECT subject, predicate, object, source_citation
FROM temporal_fact
WHERE anime_id = :anime_id
  AND revealed_ordinal <= :current_ep_ordinal   -- the entire reveal engine, in the WHERE clause
ORDER BY embedding <-> :query_embedding
LIMIT 3;
```

There is no longer a second copy that can go stale, and no code path where a fact
could be similarity-ranked before its gate check runs — the gate is structurally
part of the same query that finds it, not a filter applied to a result set that was
computed elsewhere. This directly closes the class of bug described in §1.

`reveal_engine.checkpoint_to_ordinal()` stays exactly as-is — it becomes the function
that populates `revealed_ordinal` at write time, not a runtime filter.

## 3. Async background ingestion (Inngest or QStash)

`POST /anime/import` today runs synchronously end-to-end in one request: Jikan +
AniList metadata, full roster fetch, then up to 40 characters × 2 Gemini calls each
(fact extraction + debut detection). This is already the concrete reason dynamic
ingestion isn't turned on for the 4 launch titles — one Gemini quota hiccup mid-run
silently drops characters, and the whole thing has to complete inside a single HTTP
request/response window (a hard wall on Vercel-style serverless deploys, and a poor
experience even on a long-running container).

**Target shape:**
- `POST /anime/import` enqueues one job and returns `202 Accepted` + a job id
  immediately — metadata fetch happens synchronously (fast, cheap), but roster
  ingestion does not.
- Each character becomes its own retryable step (Inngest: a `step.run()`; QStash: a
  separate published message) — a single rate-limited or failed Gemini call retries
  in isolation instead of aborting the whole import.
- `GET /anime/import/{job_id}` (new endpoint) reports progress — `n/40 characters
  processed` — so the frontend can poll instead of holding one long request open.
- Failed characters land in a dead-letter state with the reason (`quota_exceeded`,
  `low_confidence_debut`, etc.) instead of silently vanishing from the roster, which
  is what happens today.

Inngest is the better fit if this backend gains more multi-step workflows over time
(built-in step retries, function-level observability); QStash is the simpler choice
if this stays a single job type (plain HTTP callback queue, less infrastructure to
run). Either sits in front of the same `ingestion_service.py` logic — this is a
transport change, not a rewrite of the extraction logic itself.

## 4. Migration sequencing

1. Stand up Postgres (Supabase/Neon) alongside the current SQLite deploy; port the
   existing Alembic migration chain to Postgres-compatible DDL (already mostly
   portable — the models use generic SQLAlchemy types, per the project's
   cross-database convention).
2. Add the `embedding` column + backfill via the existing `DefaultEmbeddingFunction`
   (or upgrade the embedding model at the same time, since this is a one-time
   backfill regardless).
3. Cut `vector_store.py` over to pgvector queries; delete the Chroma dependency and
   `chroma_store/` volume entirely — this is a net simplification, not just a swap.
4. Introduce the job queue for `import_anime` only after the data layer migration
   lands, so retried ingestion jobs write into the already-unified store.
