from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.documents import (
    router as documents_router,
)
from backend.app.core.config import settings
from backend.app.db.database import Base, engine
from backend.app.models.document import Document  # noqa: F401
from backend.app.models.document_page import (  # noqa: F401
    DocumentPage,
)
from backend.app.models.user import User  # noqa: F401
@asynccontextmanager
async def lifespan(
    application: FastAPI,
) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield
app = FastAPI(
    title="PeopleMind AI API",
    description=(
        "Backend API for the PeopleMind AI HR Intelligence "
        "and Management Assistant."
    ),
    version="0.4.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)
app.include_router(auth_router)
app.include_router(documents_router)
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
        "version": "0.4.0",
    }
