
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
from backend.app.schemas.attendance import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeUpdate,
    ShiftCreate,
    ShiftRead,
    ShiftUpdate,
    TeamCreate,
    TeamRead,
    TeamUpdate,
)
from backend.app.services import (
    attendance_service,
)
router = APIRouter(
    prefix="/api/attendance",
    tags=["Attendance Management"],
)
def raise_not_found(
    error: Exception,
) -> None:
    raise HTTPException(
        status_code=(
            status.HTTP_404_NOT_FOUND
        ),
        detail=str(error),
    ) from error
def raise_conflict(
    error: Exception,
) -> None:
    raise HTTPException(
        status_code=(
            status.HTTP_409_CONFLICT
        ),
        detail=str(error),
    ) from error
@router.post(
    "/teams",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an attendance team",
)
def create_team(
    request: TeamCreate,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> TeamRead:
    try:
        team = (
            attendance_service
            .create_team(
                database=database,
                request=request,
                created_by_id=(
                    current_user.id
                ),
            )
        )
    except (
        attendance_service
        .DuplicateTeamError
    ) as error:
        raise_conflict(error)
    return TeamRead.model_validate(team)
@router.get(
    "/teams",
    response_model=list[TeamRead],
    summary="List attendance teams",
)
def read_teams(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> list[TeamRead]:
    return [
        TeamRead.model_validate(team)
        for team in (
            attendance_service
            .list_teams(database)
        )
    ]
@router.get(
    "/teams/{team_id}",
    response_model=TeamRead,
    summary="Read an attendance team",
)
def read_team(
    team_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> TeamRead:
    try:
        team = attendance_service.get_team(
            database,
            team_id,
        )
    except (
        attendance_service
        .TeamNotFoundError
    ) as error:
        raise_not_found(error)
    return TeamRead.model_validate(team)
@router.patch(
    "/teams/{team_id}",
    response_model=TeamRead,
    summary="Update an attendance team",
)
def update_team(
    team_id: int,
    request: TeamUpdate,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> TeamRead:
    try:
        team = (
            attendance_service
            .update_team(
                database=database,
                team_id=team_id,
                request=request,
            )
        )
    except (
        attendance_service
        .TeamNotFoundError
    ) as error:
        raise_not_found(error)
    except (
        attendance_service
        .DuplicateTeamError
    ) as error:
        raise_conflict(error)
    return TeamRead.model_validate(team)
@router.delete(
    "/teams/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an empty team",
)
def delete_team(
    team_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> None:
    try:
        attendance_service.delete_team(
            database,
            team_id,
        )
    except (
        attendance_service
        .TeamNotFoundError
    ) as error:
        raise_not_found(error)
    except (
        attendance_service
        .AttendanceDependencyError
    ) as error:
        raise_conflict(error)
@router.post(
    "/shifts",
    response_model=ShiftRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an attendance shift",
)
def create_shift(
    request: ShiftCreate,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> ShiftRead:
    try:
        shift = (
            attendance_service
            .create_shift(
                database=database,
                request=request,
                created_by_id=(
                    current_user.id
                ),
            )
        )
    except (
        attendance_service
        .DuplicateShiftError
    ) as error:
        raise_conflict(error)
    return ShiftRead.model_validate(shift)
@router.get(
    "/shifts",
    response_model=list[ShiftRead],
    summary="List attendance shifts",
)
def read_shifts(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> list[ShiftRead]:
    return [
        ShiftRead.model_validate(shift)
        for shift in (
            attendance_service
            .list_shifts(database)
        )
    ]
@router.get(
    "/shifts/{shift_id}",
    response_model=ShiftRead,
    summary="Read an attendance shift",
)
def read_shift(
    shift_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> ShiftRead:
    try:
        shift = (
            attendance_service
            .get_shift(
                database,
                shift_id,
            )
        )
    except (
        attendance_service
        .ShiftNotFoundError
    ) as error:
        raise_not_found(error)
    return ShiftRead.model_validate(
        shift
    )
@router.patch(
    "/shifts/{shift_id}",
    response_model=ShiftRead,
    summary="Update an attendance shift",
)
def update_shift(
    shift_id: int,
    request: ShiftUpdate,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> ShiftRead:
    try:
        shift = (
            attendance_service
            .update_shift(
                database=database,
                shift_id=shift_id,
                request=request,
            )
        )
    except (
        attendance_service
        .ShiftNotFoundError
    ) as error:
        raise_not_found(error)
    except (
        attendance_service
        .DuplicateShiftError
    ) as error:
        raise_conflict(error)
    return ShiftRead.model_validate(
        shift
    )
@router.delete(
    "/shifts/{shift_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an unused shift",
)
def delete_shift(
    shift_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> None:
    try:
        attendance_service.delete_shift(
            database,
            shift_id,
        )
    except (
        attendance_service
        .ShiftNotFoundError
    ) as error:
        raise_not_found(error)
    except (
        attendance_service
        .AttendanceDependencyError
    ) as error:
        raise_conflict(error)
@router.post(
    "/employees",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an attendance employee",
)
def create_employee(
    request: EmployeeCreate,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> EmployeeRead:
    try:
        employee = (
            attendance_service
            .create_employee(
                database=database,
                request=request,
                created_by_id=(
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
        raise_not_found(error)
    except (
        attendance_service
        .DuplicateEmployeeCodeError
    ) as error:
        raise_conflict(error)
    return EmployeeRead.model_validate(
        employee
    )
@router.get(
    "/employees",
    response_model=list[EmployeeRead],
    summary="List attendance employees",
)
def read_employees(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    team_id: int | None = Query(
        default=None,
        gt=0,
    ),
    shift_id: int | None = Query(
        default=None,
        gt=0,
    ),
    is_active: bool | None = Query(
        default=None,
    ),
) -> list[EmployeeRead]:
    try:
        employees = (
            attendance_service
            .list_employees(
                database=database,
                team_id=team_id,
                shift_id=shift_id,
                is_active=is_active,
            )
        )
    except (
        attendance_service
        .TeamNotFoundError,
        attendance_service
        .ShiftNotFoundError,
    ) as error:
        raise_not_found(error)
    return [
        EmployeeRead.model_validate(
            employee
        )
        for employee in employees
    ]
@router.get(
    "/employees/{employee_id}",
    response_model=EmployeeRead,
    summary="Read an attendance employee",
)
def read_employee(
    employee_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> EmployeeRead:
    try:
        employee = (
            attendance_service
            .get_employee(
                database,
                employee_id,
            )
        )
    except (
        attendance_service
        .EmployeeNotFoundError
    ) as error:
        raise_not_found(error)
    return EmployeeRead.model_validate(
        employee
    )
@router.patch(
    "/employees/{employee_id}",
    response_model=EmployeeRead,
    summary="Update an attendance employee",
)
def update_employee(
    employee_id: int,
    request: EmployeeUpdate,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> EmployeeRead:
    try:
        employee = (
            attendance_service
            .update_employee(
                database=database,
                employee_id=employee_id,
                request=request,
            )
        )
    except (
        attendance_service
        .EmployeeNotFoundError,
        attendance_service
        .TeamNotFoundError,
        attendance_service
        .ShiftNotFoundError,
    ) as error:
        raise_not_found(error)
    except (
        attendance_service
        .DuplicateEmployeeCodeError
    ) as error:
        raise_conflict(error)
    return EmployeeRead.model_validate(
        employee
    )
@router.delete(
    "/employees/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete an employee",
)
def delete_employee(
    employee_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> None:
    try:
        attendance_service.delete_employee(
            database,
            employee_id,
        )
    except (
        attendance_service
        .EmployeeNotFoundError
    ) as error:
        raise_not_found(error)
