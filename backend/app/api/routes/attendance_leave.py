
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
from backend.app.schemas.attendance_leave import (
    AttendanceLeaveCreate,
    AttendanceLeaveListRead,
    AttendanceLeaveRead,
    AttendanceLeaveUpdate,
    LeaveStatus,
)
from backend.app.services import (
    attendance_leave_service,
)
router = APIRouter(
    prefix="/api/attendance/leaves",
    tags=["Attendance Leave"],
)
@router.post(
    "",
    response_model=AttendanceLeaveRead,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
def create_attendance_leave(
    request: AttendanceLeaveCreate,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> AttendanceLeaveRead:
    try:
        return (
            attendance_leave_service
            .create_leave(
                database=database,
                request=request,
                created_by_id=(
                    current_user.id
                ),
            )
        )
    except (
        attendance_leave_service
        .AttendanceLeaveEmployeeNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    except (
        attendance_leave_service
        .AttendanceLeaveOverlapError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(error),
        ) from error
@router.get(
    "",
    response_model=AttendanceLeaveListRead,
)
def read_attendance_leaves(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    employee_id: int | None = Query(
        default=None,
        gt=0,
    ),
    leave_status: LeaveStatus | None = Query(
        default=None,
        alias="status",
    ),
    date_from: date | None = Query(
        default=None,
    ),
    date_to: date | None = Query(
        default=None,
    ),
) -> AttendanceLeaveListRead:
    try:
        items = (
            attendance_leave_service
            .list_leaves(
                database=database,
                employee_id=employee_id,
                leave_status=leave_status,
                date_from=date_from,
                date_to=date_to,
            )
        )
    except (
        attendance_leave_service
        .AttendanceLeaveRangeError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(error),
        ) from error
    return AttendanceLeaveListRead(
        total=len(items),
        items=items,
    )
@router.get(
    "/{leave_id}",
    response_model=AttendanceLeaveRead,
)
def read_attendance_leave(
    leave_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> AttendanceLeaveRead:
    try:
        return (
            attendance_leave_service
            .get_leave(
                database,
                leave_id,
            )
        )
    except (
        attendance_leave_service
        .AttendanceLeaveNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
@router.patch(
    "/{leave_id}",
    response_model=AttendanceLeaveRead,
)
def update_attendance_leave(
    leave_id: int,
    request: AttendanceLeaveUpdate,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> AttendanceLeaveRead:
    try:
        return (
            attendance_leave_service
            .update_leave(
                database=database,
                leave_id=leave_id,
                request=request,
                acted_by_id=(
                    current_user.id
                ),
            )
        )
    except (
        attendance_leave_service
        .AttendanceLeaveNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    except (
        attendance_leave_service
        .AttendanceLeaveOverlapError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(error),
        ) from error
    except (
        attendance_leave_service
        .AttendanceLeaveRangeError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(error),
        ) from error
