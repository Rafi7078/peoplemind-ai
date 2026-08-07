
from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy.orm import Session
from backend.app.models.attendance_employee import (
    AttendanceEmployee,
)
from backend.app.models.attendance_shift import (
    AttendanceShift,
)
from backend.app.models.attendance_team import (
    AttendanceTeam,
)
from backend.app.schemas.attendance import (
    EmployeeCreate,
    EmployeeUpdate,
    ShiftCreate,
    ShiftUpdate,
    TeamCreate,
    TeamUpdate,
)
class TeamNotFoundError(
    LookupError
):
    pass
class ShiftNotFoundError(
    LookupError
):
    pass
class EmployeeNotFoundError(
    LookupError
):
    pass
class DuplicateTeamError(
    ValueError
):
    pass
class DuplicateShiftError(
    ValueError
):
    pass
class DuplicateEmployeeCodeError(
    ValueError
):
    pass
class AttendanceDependencyError(
    ValueError
):
    pass
def get_team(
    database: Session,
    team_id: int,
) -> AttendanceTeam:
    team = database.get(
        AttendanceTeam,
        team_id,
    )
    if team is None:
        raise TeamNotFoundError(
            "The requested team was not found."
        )
    return team
def list_teams(
    database: Session,
) -> list[AttendanceTeam]:
    statement = (
        select(AttendanceTeam)
        .order_by(
            AttendanceTeam.name.asc()
        )
    )
    return list(
        database.scalars(
            statement
        ).all()
    )
def create_team(
    database: Session,
    request: TeamCreate,
    created_by_id: int,
) -> AttendanceTeam:
    team = AttendanceTeam(
        name=request.name,
        description=request.description,
        status=request.status,
        created_by_id=created_by_id,
    )
    database.add(team)
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise DuplicateTeamError(
            "A team with this name "
            "already exists."
        ) from error
    database.refresh(team)
    return team
def update_team(
    database: Session,
    team_id: int,
    request: TeamUpdate,
) -> AttendanceTeam:
    team = get_team(
        database,
        team_id,
    )
    update_values = request.model_dump(
        exclude_unset=True
    )
    for field_name, value in (
        update_values.items()
    ):
        setattr(
            team,
            field_name,
            value,
        )
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise DuplicateTeamError(
            "A team with this name "
            "already exists."
        ) from error
    database.refresh(team)
    return team
def delete_team(
    database: Session,
    team_id: int,
) -> None:
    team = get_team(
        database,
        team_id,
    )
    member_count = database.scalar(
        select(
            func.count(
                AttendanceEmployee.id
            )
        ).where(
            AttendanceEmployee.team_id
            == team_id
        )
    ) or 0
    if member_count > 0:
        raise AttendanceDependencyError(
            "This team still has employees. "
            "Move, deactivate or delete its "
            "employees before permanently "
            "deleting the team."
        )
    database.delete(team)
    database.commit()
def get_shift(
    database: Session,
    shift_id: int,
) -> AttendanceShift:
    shift = database.get(
        AttendanceShift,
        shift_id,
    )
    if shift is None:
        raise ShiftNotFoundError(
            "The requested shift was not found."
        )
    return shift
def list_shifts(
    database: Session,
) -> list[AttendanceShift]:
    statement = (
        select(AttendanceShift)
        .order_by(
            AttendanceShift.name.asc()
        )
    )
    return list(
        database.scalars(
            statement
        ).all()
    )
def create_shift(
    database: Session,
    request: ShiftCreate,
    created_by_id: int,
) -> AttendanceShift:
    shift = AttendanceShift(
        name=request.name,
        description=request.description,
        status=request.status,
        created_by_id=created_by_id,
    )
    database.add(shift)
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise DuplicateShiftError(
            "A shift with this name "
            "already exists."
        ) from error
    database.refresh(shift)
    return shift
def update_shift(
    database: Session,
    shift_id: int,
    request: ShiftUpdate,
) -> AttendanceShift:
    shift = get_shift(
        database,
        shift_id,
    )
    update_values = request.model_dump(
        exclude_unset=True
    )
    for field_name, value in (
        update_values.items()
    ):
        setattr(
            shift,
            field_name,
            value,
        )
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise DuplicateShiftError(
            "A shift with this name "
            "already exists."
        ) from error
    database.refresh(shift)
    return shift
def delete_shift(
    database: Session,
    shift_id: int,
) -> None:
    shift = get_shift(
        database,
        shift_id,
    )
    member_count = database.scalar(
        select(
            func.count(
                AttendanceEmployee.id
            )
        ).where(
            AttendanceEmployee.shift_id
            == shift_id
        )
    ) or 0
    if member_count > 0:
        raise AttendanceDependencyError(
            "This shift is still assigned "
            "to employees. Move those "
            "employees before permanently "
            "deleting the shift."
        )
    database.delete(shift)
    database.commit()
def get_employee(
    database: Session,
    employee_id: int,
) -> AttendanceEmployee:
    employee = database.get(
        AttendanceEmployee,
        employee_id,
    )
    if employee is None:
        raise EmployeeNotFoundError(
            "The requested employee "
            "was not found."
        )
    return employee
def list_employees(
    database: Session,
    *,
    team_id: int | None = None,
    shift_id: int | None = None,
    is_active: bool | None = None,
) -> list[AttendanceEmployee]:
    statement = select(
        AttendanceEmployee
    )
    if team_id is not None:
        get_team(
            database,
            team_id,
        )
        statement = statement.where(
            AttendanceEmployee.team_id
            == team_id
        )
    if shift_id is not None:
        get_shift(
            database,
            shift_id,
        )
        statement = statement.where(
            AttendanceEmployee.shift_id
            == shift_id
        )
    if is_active is not None:
        statement = statement.where(
            AttendanceEmployee.is_active
            == is_active
        )
    statement = statement.order_by(
        AttendanceEmployee.employee_code.asc()
    )
    return list(
        database.scalars(
            statement
        ).all()
    )
def create_employee(
    database: Session,
    request: EmployeeCreate,
    created_by_id: int,
) -> AttendanceEmployee:
    get_team(
        database,
        request.team_id,
    )
    get_shift(
        database,
        request.shift_id,
    )
    employee = AttendanceEmployee(
        employee_code=(
            request.employee_code
        ),
        full_name=request.full_name,
        designation=request.designation,
        team_id=request.team_id,
        shift_id=request.shift_id,
        weekly_holidays=[
            str(day)
            for day in (
                request.weekly_holidays
            )
        ],
        is_active=request.is_active,
        created_by_id=created_by_id,
    )
    database.add(employee)
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise DuplicateEmployeeCodeError(
            "An employee with this "
            "employee ID already exists."
        ) from error
    database.refresh(employee)
    return employee
def update_employee(
    database: Session,
    employee_id: int,
    request: EmployeeUpdate,
) -> AttendanceEmployee:
    employee = get_employee(
        database,
        employee_id,
    )
    update_values = request.model_dump(
        exclude_unset=True
    )
    if (
        "team_id" in update_values
        and update_values["team_id"]
        is not None
    ):
        get_team(
            database,
            update_values["team_id"],
        )
    if (
        "shift_id" in update_values
        and update_values["shift_id"]
        is not None
    ):
        get_shift(
            database,
            update_values["shift_id"],
        )
    for field_name, value in (
        update_values.items()
    ):
        if (
            field_name
            == "weekly_holidays"
            and value is not None
        ):
            value = [
                str(day)
                for day in value
            ]
        setattr(
            employee,
            field_name,
            value,
        )
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise DuplicateEmployeeCodeError(
            "An employee with this "
            "employee ID already exists."
        ) from error
    database.refresh(employee)
    return employee
def delete_employee(
    database: Session,
    employee_id: int,
) -> None:
    employee = get_employee(
        database,
        employee_id,
    )
    database.delete(employee)
    database.commit()
