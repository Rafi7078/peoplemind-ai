from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI
from backend.app.api.routes.auth import router as auth_router
from backend.app.core.config import settings
from backend.app.db.database import Base, engine
from backend.app.models.user import User  # noqa: F401
@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield
app = FastAPI(
    title="PeopleMind AI API",
    description=(
        "Backend API for the PeopleMind AI HR Intelligence "
        "and Management Assistant."
    ),
    version="0.2.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)
app.include_router(auth_router)
@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Welcome to PeopleMind AI",
        "status": "running",
    }
@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {
        "service": "PeopleMind AI API",
        "status": "healthy",
        "version": "0.2.0",
    }
