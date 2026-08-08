
from datetime import date
from sqlalchemy import (
    select,
)
from sqlalchemy.orm import Session
from backend.app.models.attendance_employee import (
    AttendanceEmployee,
)
from backend.app.models.attendance_record import (
    AttendanceRecord,
)
from backend.app.models.attendance_record_snapshot import (
    AttendanceRecordSnapshot,
)
from backend.app.schemas.attendance_daily import (
    DailyAttendanceRecordRead,
    DailyAttendanceSubmissionRead,
    DailyAttendanceSubmit,
    DailyAttendanceSummary,
    DailyRosterItem,
    DailyRosterRead,
)
from backend.app.services import (
    attendance_service,
)
class AttendanceRosterEmptyError(
    ValueError
):
    pass
class AttendanceRosterMismatchError(
    ValueError
):
    pass
class AttendanceRecordConflictError(
    ValueError
):
    pass
def _ensure_record_snapshot(
    database: Session,
    *,
    record: AttendanceRecord,
    employee: AttendanceEmployee,
    team_name: str,
    shift_name: str,
) -> None:
    existing_snapshot = database.scalar(
        select(
            AttendanceRecordSnapshot
        ).where(
            AttendanceRecordSnapshot
            .attendance_record_id
            == record.id
        )
    )
    if existing_snapshot is not None:
        return
    database.add(
        AttendanceRecordSnapshot(
            attendance_record_id=record.id,
            employee_code=(
                employee.employee_code
            ),
            full_name=employee.full_name,
            designation=(
                employee.designation
            ),
            team_name=team_name,
            shift_name=shift_name,
        )
    )
def get_daily_roster(
    database: Session,
    *,
    attendance_date: date,
    team_id: int,
    shift_id: int,
) -> DailyRosterRead:
    team = attendance_service.get_team(
        database,
        team_id,
    )
    shift = attendance_service.get_shift(
        database,
        shift_id,
    )
    employees = list(
        database.scalars(
            select(
                AttendanceEmployee
            )
            .where(
                AttendanceEmployee.team_id
                == team_id,
                AttendanceEmployee.shift_id
                == shift_id,
                AttendanceEmployee.is_active
                .is_(True),
            )
            .order_by(
                AttendanceEmployee
                .employee_code
                .asc()
            )
        ).all()
    )
    employee_ids = [
        employee.id
        for employee in employees
    ]
    records_by_employee_id: dict[
        int,
        AttendanceRecord,
    ] = {}
    if employee_ids:
        records = list(
            database.scalars(
                select(
                    AttendanceRecord
                ).where(
                    AttendanceRecord
                    .attendance_date
                    == attendance_date,
                    AttendanceRecord
                    .employee_id
                    .in_(employee_ids),
                )
            ).all()
        )
        records_by_employee_id = {
            record.employee_id:
                record
            for record in records
        }
    weekday_name = (
        attendance_date.strftime(
            "%A"
        )
    )
    items: list[
        DailyRosterItem
    ] = []
    for employee in employees:
        record = (
            records_by_employee_id
            .get(employee.id)
        )
        suggested_status = (
            "weekly_holiday"
            if weekday_name
            in employee.weekly_holidays
            else "present"
        )
        items.append(
            DailyRosterItem(
                employee_id=employee.id,
                employee_code=(
                    employee.employee_code
                ),
                full_name=(
                    employee.full_name
                ),
                designation=(
                    employee.designation
                ),
                team_id=employee.team_id,
                shift_id=employee.shift_id,
                weekly_holidays=list(
                    employee
                    .weekly_holidays
                ),
                suggested_status=(
                    suggested_status
                ),
                saved_status=(
                    record.status
                    if record is not None
                    else None
                ),
                note=(
                    record.note
                    if record is not None
                    else None
                ),
                record_id=(
                    record.id
                    if record is not None
                    else None
                ),
            )
        )
    return DailyRosterRead(
        attendance_date=attendance_date,
        team_id=team.id,
        team_name=team.name,
        shift_id=shift.id,
        shift_name=shift.name,
        total_members=len(items),
        items=items,
    )
def submit_daily_attendance(
    database: Session,
    *,
    request: DailyAttendanceSubmit,
    recorded_by_id: int,
) -> DailyAttendanceSubmissionRead:
    team = attendance_service.get_team(
        database,
        request.team_id,
    )
    shift = attendance_service.get_shift(
        database,
        request.shift_id,
    )
    roster = list(
        database.scalars(
            select(
                AttendanceEmployee
            )
            .where(
                AttendanceEmployee.team_id
                == request.team_id,
                AttendanceEmployee.shift_id
                == request.shift_id,
                AttendanceEmployee.is_active
                .is_(True),
            )
            .order_by(
                AttendanceEmployee
                .employee_code
                .asc()
            )
        ).all()
    )
    if not roster:
        raise AttendanceRosterEmptyError(
            "No active employees are "
            "assigned to this team and "
            "shift."
        )
    roster_by_id = {
        employee.id:
            employee
        for employee in roster
    }
    roster_ids = set(
        roster_by_id
    )
    submitted_ids = {
        entry.employee_id
        for entry in request.entries
    }
    if (
        submitted_ids
        != roster_ids
    ):
        missing_ids = sorted(
            roster_ids
            - submitted_ids
        )
        unexpected_ids = sorted(
            submitted_ids
            - roster_ids
        )
        details: list[str] = []
        if missing_ids:
            details.append(
                "missing employee ID(s): "
                + ", ".join(
                    str(value)
                    for value
                    in missing_ids
                )
            )
        if unexpected_ids:
            details.append(
                "unexpected employee ID(s): "
                + ", ".join(
                    str(value)
                    for value
                    in unexpected_ids
                )
            )
        raise AttendanceRosterMismatchError(
            "Attendance must include the "
            "complete active roster for "
            "the selected team and shift. "
            + "; ".join(details)
        )
    saved_records: list[
        AttendanceRecord
    ] = []
    for entry in request.entries:
        existing = database.scalar(
            select(
                AttendanceRecord
            ).where(
                AttendanceRecord
                .employee_id
                == entry.employee_id,
                AttendanceRecord
                .attendance_date
                == request.attendance_date,
            )
        )
        if (
            existing is not None
            and (
                existing.team_id
                != request.team_id
                or existing.shift_id
                != request.shift_id
            )
        ):
            raise AttendanceRecordConflictError(
                "An attendance record "
                "already exists for employee "
                f"{entry.employee_id} on "
                f"{request.attendance_date} "
                "under another team or shift."
            )
        if existing is None:
            record = AttendanceRecord(
                employee_id=(
                    entry.employee_id
                ),
                attendance_date=(
                    request
                    .attendance_date
                ),
                team_id=request.team_id,
                shift_id=request.shift_id,
                status=entry.status,
                note=entry.note,
                recorded_by_id=(
                    recorded_by_id
                ),
            )
            database.add(record)
            saved_records.append(
                record
            )
        else:
            existing.status = (
                entry.status
            )
            existing.note = entry.note
            existing.recorded_by_id = (
                recorded_by_id
            )
            saved_records.append(
                existing
            )
    database.flush()
    for record in saved_records:
        employee = roster_by_id[
            record.employee_id
        ]
        _ensure_record_snapshot(
            database,
            record=record,
            employee=employee,
            team_name=team.name,
            shift_name=shift.name,
        )
    database.commit()
    for record in saved_records:
        database.refresh(record)
    summary = build_summary(
        saved_records
    )
    return DailyAttendanceSubmissionRead(
        attendance_date=(
            request.attendance_date
        ),
        team_id=team.id,
        team_name=team.name,
        shift_id=shift.id,
        shift_name=shift.name,
        summary=summary,
        records=[
            DailyAttendanceRecordRead
            .model_validate(record)
            for record in saved_records
        ],
    )
def build_summary(
    records: list[
        AttendanceRecord
    ],
) -> DailyAttendanceSummary:
    counts = {
        "present": 0,
        "absent": 0,
        "on_leave": 0,
        "weekly_holiday": 0,
    }
    for record in records:
        counts[record.status] += 1
    return DailyAttendanceSummary(
        total_members=len(records),
        present=counts["present"],
        absent=counts["absent"],
        on_leave=counts["on_leave"],
        weekly_holiday=(
            counts["weekly_holiday"]
        ),
    )
