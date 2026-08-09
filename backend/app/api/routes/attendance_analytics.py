from datetime import date
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)
from backend.app.api.dependencies import (
    CurrentUserDependency,
    DatabaseDependency,
)
from backend.app.schemas.attendance_analytics import (
    AttendanceAnalyticsRead,
)
from backend.app.services import (
    attendance_analytics_service,
)
router = APIRouter(
    prefix="/api/attendance/analytics",
    tags=["Attendance Analytics"],
)
@router.get(
    "",
    response_model=(
        AttendanceAnalyticsRead
    ),
    summary=(
        "Read attendance analytics"
    ),
)
def read_attendance_analytics(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    date_from: date = Query(),
    date_to: date = Query(),
    team_id: int | None = Query(
        default=None,
        gt=0,
    ),
    shift_id: int | None = Query(
        default=None,
        gt=0,
    ),
) -> AttendanceAnalyticsRead:
    try:
        return (
            attendance_analytics_service
            .get_attendance_analytics(
                database,
                date_from=date_from,
                date_to=date_to,
                team_id=team_id,
                shift_id=shift_id,
            )
        )
    except (
        attendance_analytics_service
        .AttendanceAnalyticsRangeError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error
