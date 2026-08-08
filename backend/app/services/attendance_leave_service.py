
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.attendance_employee import (
    AttendanceEmployee,
)
from backend.app.models.attendance_leave import (
    AttendanceLeave,
)
from backend.app.schemas.attendance_leave import (
    AttendanceLeaveCreate,
    AttendanceLeaveUpdate,
    LeaveStatus,
)
class AttendanceLeaveNotFoundError(
    ValueError
):
    pass
class AttendanceLeaveEmployeeNotFoundError(
    ValueError
):
    pass
class AttendanceLeaveOverlapError(
    ValueError
):
    pass
class AttendanceLeaveRangeError(
    ValueError
):
    pass
def get_leave(
    database: Session,
    leave_id: int,
) -> AttendanceLeave:
    leave = database.get(
        AttendanceLeave,
        leave_id,
    )
    if leave is None:
        raise AttendanceLeaveNotFoundError(
            "Leave record not found."
        )
    return leave
def _get_employee(
    database: Session,
    employee_id: int,
) -> AttendanceEmployee:
    employee = database.get(
        AttendanceEmployee,
        employee_id,
    )
    if employee is None:
        raise (
            AttendanceLeaveEmployeeNotFoundError(
                "Attendance employee "
                "not found."
            )
        )
    return employee
def _check_overlap(
    database: Session,
    *,
    employee_id: int,
    from_date: date,
    to_date: date,
    status: str,
    exclude_leave_id: int | None = None,
) -> None:
    if status == "cancelled":
        return
    statement = select(
        AttendanceLeave
    ).where(
        AttendanceLeave.employee_id
        == employee_id,
        AttendanceLeave.status.in_(
            [
                "pending",
                "approved",
            ]
        ),
        AttendanceLeave.from_date
        <= to_date,
        AttendanceLeave.to_date
        >= from_date,
    )
    if exclude_leave_id is not None:
        statement = statement.where(
            AttendanceLeave.id
            != exclude_leave_id
        )
    existing = database.scalar(
        statement
    )
    if existing is not None:
        raise AttendanceLeaveOverlapError(
            "This employee already has "
            "a pending or approved leave "
            "that overlaps the selected "
            "date range."
        )
def create_leave(
    database: Session,
    *,
    request: AttendanceLeaveCreate,
    created_by_id: int,
) -> AttendanceLeave:
    _get_employee(
        database,
        request.employee_id,
    )
    _check_overlap(
        database,
        employee_id=request.employee_id,
        from_date=request.from_date,
        to_date=request.to_date,
        status=request.status,
    )
    leave = AttendanceLeave(
        employee_id=request.employee_id,
        leave_type=request.leave_type,
        from_date=request.from_date,
        to_date=request.to_date,
        reason=request.reason,
        status=request.status,
        created_by_id=created_by_id,
        approved_by_id=(
            created_by_id
            if request.status == "approved"
            else None
        ),
    )
    database.add(leave)
    database.commit()
    database.refresh(leave)
    return leave
def update_leave(
    database: Session,
    *,
    leave_id: int,
    request: AttendanceLeaveUpdate,
    acted_by_id: int,
) -> AttendanceLeave:
    leave = get_leave(
        database,
        leave_id,
    )
    changes = request.model_dump(
        exclude_unset=True
    )
    next_from_date = changes.get(
        "from_date",
        leave.from_date,
    )
    next_to_date = changes.get(
        "to_date",
        leave.to_date,
    )
    next_status: LeaveStatus = (
        changes.get(
            "status",
            leave.status,
        )
    )
    if next_from_date > next_to_date:
        raise AttendanceLeaveRangeError(
            "from_date cannot be later "
            "than to_date."
        )
    _check_overlap(
        database,
        employee_id=leave.employee_id,
        from_date=next_from_date,
        to_date=next_to_date,
        status=next_status,
        exclude_leave_id=leave.id,
    )
    for field_name, value in changes.items():
        setattr(
            leave,
            field_name,
            value,
        )
    if (
        leave.status == "approved"
        and leave.approved_by_id is None
    ):
        leave.approved_by_id = (
            acted_by_id
        )
    database.commit()
    database.refresh(leave)
    return leave
def list_leaves(
    database: Session,
    *,
    employee_id: int | None = None,
    leave_status: LeaveStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[AttendanceLeave]:
    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise AttendanceLeaveRangeError(
            "date_from cannot be later "
            "than date_to."
        )
    statement = select(
        AttendanceLeave
    )
    if employee_id is not None:
        statement = statement.where(
            AttendanceLeave.employee_id
            == employee_id
        )
    if leave_status is not None:
        statement = statement.where(
            AttendanceLeave.status
            == leave_status
        )
    if date_from is not None:
        statement = statement.where(
            AttendanceLeave.to_date
            >= date_from
        )
    if date_to is not None:
        statement = statement.where(
            AttendanceLeave.from_date
            <= date_to
        )
    statement = statement.order_by(
        AttendanceLeave.from_date.desc(),
        AttendanceLeave.id.desc(),
    )
    return list(
        database.scalars(
            statement
        ).all()
    )
