# Rule: SQLAlchemy & Database Migrations (Alembic)

All database models and schema migrations in `backend/app/db/` and `backend/alembic/` must strictly adhere to these standards:

1. **Async SQLAlchemy 2.0 ORM:**
   - Use `DeclarativeBase` for all model definitions.
   - Use `Mapped[...]` and `mapped_column(...)` type annotations exclusively.
   - Always define explicit foreign key relationships with appropriate `ondelete` strategies (`CASCADE`, `SET NULL`).

2. **Schema & Indexing Performance:**
   - Add explicit indexes (`index=True`) on foreign key columns, user lookup keys, and query filters (`mal_id`, `anilist_id`, `user_id`, `anime_id`).
   - Use UTC timezone-aware datetimes (`datetime.now(timezone.utc)`) for `created_at` and `updated_at` timestamps.

3. **Alembic Migration Discipline:**
   - Never modify production database tables manually or alter SQLAlchemy models without generating an Alembic migration script (`alembic revision --autogenerate -m "description"`).
   - Verify both `upgrade()` and `downgrade()` functions in every migration revision script.

4. **Cross-Database Compatibility (SQLite Dev / PostgreSQL Prod):**
   - Avoid engine-specific column types (e.g. use generic `JSON` or `String` wrappers rather than PostgreSQL-only `JSONB` or `ARRAY` without fallback handlers).
