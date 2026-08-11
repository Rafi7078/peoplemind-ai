from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.candidates import (
    router as candidates_router,
)
from backend.app.api.routes.jobs import (
    router as jobs_router,
)
from backend.app.api.routes.attendance import (
    router as attendance_router,
)
from backend.app.api.routes.attendance_daily import (
    router as attendance_daily_router,
)
from backend.app.api.routes.attendance_history import (
    router as attendance_history_router,
)
from backend.app.api.routes.attendance_leave import (
    router as attendance_leave_router,
)
from backend.app.api.routes.attendance_analytics import (
    router as attendance_analytics_router,
)
from backend.app.api.routes.attendance_employee_monthly import (
    router as attendance_employee_monthly_router,
)
from backend.app.api.routes.documents import (
    router as documents_router,
)
from backend.app.core.config import settings
from backend.app.db.database import Base, engine
from backend.app.models.candidate_cv import (  # noqa: F401
    CandidateCV,
)
from backend.app.models.candidate_cv_page import (  # noqa: F401
    CandidateCVPage,
)
from backend.app.models.candidate_profile import (  # noqa: F401
    CandidateProfile,
)
from backend.app.models.candidate_ats_result import (  # noqa: F401
    CandidateATSResult,
)
from backend.app.models.job_profile import (  # noqa: F401
    JobProfile,
)
from backend.app.models.job_candidate_assignment import (  # noqa: F401
    JobCandidateAssignment,
)
from backend.app.models.job_match_result import (  # noqa: F401
    JobMatchResult,
)
from backend.app.models.job_candidate_review import (  # noqa: F401
    JobCandidateReview,
)
from backend.app.models.attendance_team import (  # noqa: F401
    AttendanceTeam,
)
from backend.app.models.attendance_shift import (  # noqa: F401
    AttendanceShift,
)
from backend.app.models.attendance_employee import (  # noqa: F401
    AttendanceEmployee,
)
from backend.app.models.attendance_record import (  # noqa: F401
    AttendanceRecord,
)
from backend.app.models.attendance_record_snapshot import (  # noqa: F401
    AttendanceRecordSnapshot,
)
from backend.app.models.attendance_leave import (  # noqa: F401
    AttendanceLeave,
)
from backend.app.models.document import Document  # noqa: F401
from backend.app.models.document_chunk import (  # noqa: F401
    DocumentChunk,
)
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
    version="0.7.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)

allowed_origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(attendance_router)
app.include_router(attendance_daily_router)
app.include_router(attendance_history_router)
app.include_router(attendance_leave_router)
app.include_router(attendance_analytics_router)
app.include_router(attendance_employee_monthly_router)
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
        "version": "0.7.0",
    }
