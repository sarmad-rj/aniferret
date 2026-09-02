from fastapi import APIRouter

from app.api.v1.endpoints import (
    anime,
    auth,
    dossier,
    franchises,
    group_session,
    health,
    query,
    sources,
    watch_progress,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(anime.router)
api_router.include_router(dossier.router)
api_router.include_router(query.router)
api_router.include_router(group_session.router)
api_router.include_router(sources.router)
api_router.include_router(franchises.router)
api_router.include_router(auth.router)
api_router.include_router(watch_progress.router)
