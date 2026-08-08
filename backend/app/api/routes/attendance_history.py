
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
from backend.app.schemas.attendance_history import (
    AttendanceHistoryListRead,
    AttendanceHistoryReportRead,
)
from backend.app.services import (
    attendance_history_service,
)
router = APIRouter(
    prefix="/api/attendance/history",
    tags=["Attendance History"],
)
@router.get(
    "",
    response_model=(
        AttendanceHistoryListRead
    ),
    summary=(
        "List saved attendance reports"
    ),
)
def read_attendance_history(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    date_from: date | None = Query(
        default=None
    ),
    date_to: date | None = Query(
        default=None
    ),
    team_id: int | None = Query(
        default=None,
        gt=0,
    ),
    shift_id: int | None = Query(
        default=None,
        gt=0,
    ),
) -> AttendanceHistoryListRead:
    try:
        return (
            attendance_history_service
            .list_attendance_history(
                database=database,
                date_from=date_from,
                date_to=date_to,
                team_id=team_id,
                shift_id=shift_id,
            )
        )
    except (
        attendance_history_service
        .AttendanceHistoryRangeError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(error),
        ) from error
@router.get(
    "/report",
    response_model=(
        AttendanceHistoryReportRead
    ),
    summary=(
        "Read a saved attendance report"
    ),
)
def read_attendance_report(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    attendance_date: date = Query(),
    team_id: int = Query(gt=0),
    shift_id: int = Query(gt=0),
) -> AttendanceHistoryReportRead:
    try:
        return (
            attendance_history_service
            .get_attendance_report(
                database=database,
                attendance_date=(
                    attendance_date
                ),
                team_id=team_id,
                shift_id=shift_id,
            )
        )
    except (
        attendance_history_service
        .AttendanceHistoryNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
