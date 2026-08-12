from datetime import date
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)
from backend.app.api.dependencies import (
    AuthenticatedUserDependency,
    DatabaseDependency,
)
from backend.app.schemas.attendance_access import (
    DailyAttendanceAccessRead,
)
from backend.app.schemas.attendance_daily import (
    DailyAttendanceSubmissionRead,
    DailyAttendanceSubmit,
    DailyRosterRead,
)
from backend.app.services import (
    attendance_access_service,
    attendance_daily_service,
    attendance_service,
)
router = APIRouter(
    prefix="/api/attendance/daily",
    tags=["Daily Attendance"],
)
@router.get(
    "/access",
    response_model=(
        DailyAttendanceAccessRead
    ),
    summary=(
        "Read current user's "
        "daily attendance access"
    ),
)
def read_daily_access(
    current_user:
        AuthenticatedUserDependency,
    database: DatabaseDependency,
) -> DailyAttendanceAccessRead:
    try:
        return (
            attendance_access_service
            .get_daily_access(
                database,
                user=current_user,
            )
        )
    except (
        attendance_access_service
        .AttendanceUserProfileError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(error),
        ) from error
@router.get(
    "/roster",
    response_model=DailyRosterRead,
    summary=(
        "Load the daily attendance roster"
    ),
)
def read_daily_roster(
    current_user:
        AuthenticatedUserDependency,
    database: DatabaseDependency,
    attendance_date: date = Query(),
    team_id: int = Query(gt=0),
    shift_id: int = Query(gt=0),
) -> DailyRosterRead:
    try:
        attendance_access_service\
            .require_daily_scope(
                database,
                user=current_user,
                team_id=team_id,
                shift_id=shift_id,
            )
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
        attendance_access_service
        .AttendanceUserProfileError,
        attendance_access_service
        .AttendanceUserScopeError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(error),
        ) from error
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
    current_user:
        AuthenticatedUserDependency,
    database: DatabaseDependency,
) -> DailyAttendanceSubmissionRead:
    try:
        attendance_access_service\
            .require_daily_scope(
                database,
                user=current_user,
                team_id=request.team_id,
                shift_id=request.shift_id,
            )
        return (
            attendance_daily_service
            .submit_daily_attendance(
                database=database,
                request=request,
                recorded_by_id=(
                    current_user.id
                ),
                recorded_by_email=(
                    current_user.email
                ),
                submitted_by_employee_id=(
                    request
                    .submitted_by_employee_id
                ),
                is_admin_submission=(
                    current_user.is_admin
                ),
                allow_update=(
                    current_user.is_admin
                ),
            )
        )
    except (
        attendance_access_service
        .AttendanceUserProfileError,
        attendance_access_service
        .AttendanceUserScopeError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(error),
        ) from error
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
        .AttendanceSubmitterRequiredError,
        attendance_daily_service
        .AttendanceSubmitterScopeError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
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
        attendance_daily_service
        .AttendanceSubmissionLockedError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(error),
        ) from error
