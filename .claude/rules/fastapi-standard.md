# Rule: Official FastAPI & Pydantic v2 Conventions

All backend code in `backend/` must strictly follow these official FastAPI and Pydantic v2 standards:

1. **Strict Pydantic v2 Models:**
   - Use `pydantic.BaseModel` with explicit field type annotations for all request/response schemas.
   - Use `Field(..., description=...)` for validation rules, min/max values, and descriptions.
   - Use `ConfigDict(from_attributes=True)` instead of deprecated `orm_mode = True`.

2. **API Endpoints & Routing:**
   - Organize routes using `APIRouter` per domain module (`routers/anime.py`, `routers/dossiers.py`, `routers/lore.py`).
   - Specify `response_model` and explicit `status_code` (`status.HTTP_200_OK`, `status.HTTP_201_CREATED`) on every decorator.
   - Use `HTTPException` with precise detail dicts or error strings for failures.

3. **Async & Dependency Injection:**
   - Use `async def` handlers for all asynchronous I/O (database queries via SQLAlchemy async session, external HTTP calls via `httpx`).
   - Enforce authentication and database session lifecycle via FastAPI `Depends()`.

4. **Security & Secrets:**
   - Read configuration via `pydantic-settings` (`BaseSettings`). Never access un-parsed raw OS environments directly in business logic.
