
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
from backend.app.schemas.attendance_daily import (
    DailyAttendanceSubmissionRead,
    DailyAttendanceSubmit,
    DailyRosterRead,
)
from backend.app.services import (
    attendance_daily_service,
    attendance_service,
)
router = APIRouter(
    prefix="/api/attendance/daily",
    tags=["Daily Attendance"],
)
@router.get(
    "/roster",
    response_model=DailyRosterRead,
    summary=(
        "Load the daily attendance roster"
    ),
)
def read_daily_roster(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    attendance_date: date = Query(),
    team_id: int = Query(gt=0),
    shift_id: int = Query(gt=0),
) -> DailyRosterRead:
    try:
        return (
            attendance_daily_service
            .get_daily_roster(
                database=database,
                attendance_date=(
                    attendance_date
                ),
                team_id=team_id,
                shift_id=shift_id,
            )
        )
    except (
        attendance_service
        .TeamNotFoundError,
        attendance_service
        .ShiftNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
@router.post(
    "",
    response_model=(
        DailyAttendanceSubmissionRead
    ),
    summary=(
        "Submit or update daily attendance"
    ),
)
def save_daily_attendance(
    request: DailyAttendanceSubmit,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> DailyAttendanceSubmissionRead:
    try:
        return (
            attendance_daily_service
            .submit_daily_attendance(
                database=database,
                request=request,
                recorded_by_id=(
                    current_user.id
                ),
            )
        )
    except (
        attendance_service
        .TeamNotFoundError,
        attendance_service
        .ShiftNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    except (
        attendance_daily_service
        .AttendanceRosterEmptyError,
        attendance_daily_service
        .AttendanceRosterMismatchError,
        attendance_daily_service
        .AttendanceRecordConflictError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(error),
        ) from error
