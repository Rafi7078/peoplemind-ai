import calendar
from datetime import (
    date,
    timedelta,
)
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.attendance_employee import (
    AttendanceEmployee,
)
from backend.app.models.attendance_record import (
    AttendanceRecord,
)
from backend.app.models.attendance_record_leave_snapshot import (
    AttendanceRecordLeaveSnapshot,
)
from backend.app.models.attendance_record_snapshot import (
    AttendanceRecordSnapshot,
)
from backend.app.models.attendance_shift import (
    AttendanceShift,
)
from backend.app.models.attendance_team import (
    AttendanceTeam,
)
from backend.app.schemas.attendance_employee_monthly import (
    AttendanceEmployeeMonthlyReportRead,
    AttendanceMonthlyDayRead,
    AttendanceMonthlySummary,
)
class AttendanceEmployeeNotFoundError(
    ValueError
):
    pass
def _snapshot_or_current(
    snapshot_value: str | None,
    current_value: str,
) -> str:
    if (
        snapshot_value is not None
        and snapshot_value.strip()
    ):
        return snapshot_value
    return current_value
def get_employee_monthly_report(
    database: Session,
    *,
    employee_id: int,
    year: int,
    month: int,
) -> AttendanceEmployeeMonthlyReportRead:
    employee = database.get(
        AttendanceEmployee,
        employee_id,
    )
    if employee is None:
        raise AttendanceEmployeeNotFoundError(
            "Attendance employee not found."
        )
    team = database.get(
        AttendanceTeam,
        employee.team_id,
    )
    shift = database.get(
        AttendanceShift,
        employee.shift_id,
    )
    current_team_name = (
        team.name
        if team is not None
        else f"Team #{employee.team_id}"
    )
    current_shift_name = (
        shift.name
        if shift is not None
        else f"Shift #{employee.shift_id}"
    )
    days_in_month = calendar.monthrange(
        year,
        month,
    )[1]
    date_from = date(
        year,
        month,
        1,
    )
    date_to = date(
        year,
        month,
        days_in_month,
    )
    statement = (
        select(
            AttendanceRecord,
            AttendanceRecordSnapshot,
            AttendanceRecordLeaveSnapshot,
            AttendanceTeam,
            AttendanceShift,
        )
        .outerjoin(
            AttendanceRecordSnapshot,
            AttendanceRecordSnapshot
            .attendance_record_id
            == AttendanceRecord.id,
        )
        .outerjoin(
            AttendanceRecordLeaveSnapshot,
            AttendanceRecordLeaveSnapshot
            .attendance_record_id
            == AttendanceRecord.id,
        )
        .outerjoin(
            AttendanceTeam,
            AttendanceTeam.id
            == AttendanceRecord.team_id,
        )
        .outerjoin(
            AttendanceShift,
            AttendanceShift.id
            == AttendanceRecord.shift_id,
        )
        .where(
            AttendanceRecord.employee_id
            == employee_id,
            AttendanceRecord.attendance_date
            >= date_from,
            AttendanceRecord.attendance_date
            <= date_to,
        )
        .order_by(
            AttendanceRecord
            .attendance_date
            .asc()
        )
    )
    rows = database.execute(
        statement
    ).all()
    rows_by_date = {
        record.attendance_date: (
            record,
            snapshot,
            leave_snapshot,
            record_team,
            record_shift,
        )
        for (
            record,
            snapshot,
            leave_snapshot,
            record_team,
            record_shift,
        ) in rows
    }
    # The report header uses the latest historical
    # snapshot inside the selected month when available.
    # This prevents later profile edits from silently
    # rewriting an already-recorded monthly report.
    profile_employee_code = (
        employee.employee_code
    )
    profile_full_name = (
        employee.full_name
    )
    profile_designation = (
        employee.designation
    )
    profile_team_id = (
        employee.team_id
    )
    profile_team_name = (
        current_team_name
    )
    profile_shift_id = (
        employee.shift_id
    )
    profile_shift_name = (
        current_shift_name
    )
    if rows:
        (
            latest_record,
            latest_snapshot,
            _,
            latest_team,
            latest_shift,
        ) = rows[-1]
        profile_team_id = (
            latest_record.team_id
        )
        profile_shift_id = (
            latest_record.shift_id
        )
        latest_team_name = (
            latest_team.name
            if latest_team is not None
            else (
                f"Team #"
                f"{latest_record.team_id}"
            )
        )
        latest_shift_name = (
            latest_shift.name
            if latest_shift is not None
            else (
                f"Shift #"
                f"{latest_record.shift_id}"
            )
        )
        if latest_snapshot is not None:
            profile_employee_code = (
                latest_snapshot.employee_code
            )
            profile_full_name = (
                latest_snapshot.full_name
            )
            profile_designation = (
                latest_snapshot.designation
            )
            profile_team_name = (
                latest_snapshot.team_name
            )
            profile_shift_name = (
                latest_snapshot.shift_name
            )
        else:
            profile_team_name = (
                latest_team_name
            )
            profile_shift_name = (
                latest_shift_name
            )
    counts = {
        "present": 0,
        "absent": 0,
        "on_leave": 0,
        "weekly_holiday": 0,
    }
    days: list[
        AttendanceMonthlyDayRead
    ] = []
    current_date = date_from
    while current_date <= date_to:
        row = rows_by_date.get(
            current_date
        )
        if row is None:
            days.append(
                AttendanceMonthlyDayRead(
                    attendance_date=(
                        current_date
                    ),
                    weekday=(
                        current_date.strftime(
                            "%A"
                        )
                    ),
                    status="not_recorded",
                    is_recorded=False,
                    team_name=(
                        profile_team_name
                    ),
                    shift_name=(
                        profile_shift_name
                    ),
                )
            )
            current_date += timedelta(
                days=1
            )
            continue
        (
            record,
            snapshot,
            leave_snapshot,
            record_team,
            record_shift,
        ) = row
        if record.status in counts:
            counts[
                record.status
            ] += 1
        record_team_name = (
            record_team.name
            if record_team is not None
            else (
                f"Team #{record.team_id}"
            )
        )
        record_shift_name = (
            record_shift.name
            if record_shift is not None
            else (
                f"Shift #{record.shift_id}"
            )
        )
        if snapshot is not None:
            record_team_name = (
                _snapshot_or_current(
                    snapshot.team_name,
                    record_team_name,
                )
            )
            record_shift_name = (
                _snapshot_or_current(
                    snapshot.shift_name,
                    record_shift_name,
                )
            )
        days.append(
            AttendanceMonthlyDayRead(
                attendance_date=(
                    current_date
                ),
                weekday=(
                    current_date.strftime(
                        "%A"
                    )
                ),
                status=record.status,
                is_recorded=True,
                record_id=record.id,
                note=record.note,
                team_name=(
                    record_team_name
                ),
                shift_name=(
                    record_shift_name
                ),
                leave_id=(
                    leave_snapshot
                    .attendance_leave_id
                    if leave_snapshot
                    is not None
                    else None
                ),
                leave_type=(
                    leave_snapshot
                    .leave_type
                    if leave_snapshot
                    is not None
                    else None
                ),
                leave_reason=(
                    leave_snapshot
                    .leave_reason
                    if leave_snapshot
                    is not None
                    else None
                ),
                leave_from_date=(
                    leave_snapshot
                    .leave_from_date
                    if leave_snapshot
                    is not None
                    else None
                ),
                leave_to_date=(
                    leave_snapshot
                    .leave_to_date
                    if leave_snapshot
                    is not None
                    else None
                ),
                updated_at=(
                    record.updated_at
                ),
            )
        )
        current_date += timedelta(
            days=1
        )
    recorded_days = len(rows)
    not_recorded_days = (
        days_in_month
        - recorded_days
    )
    working_day_records = (
        counts["present"]
        + counts["absent"]
        + counts["on_leave"]
    )
    attendance_rate = (
        (
            counts["present"]
            / working_day_records
            * 100
        )
        if working_day_records
        else 0.0
    )
    return (
        AttendanceEmployeeMonthlyReportRead(
            employee_id=employee.id,
            employee_code=(
                profile_employee_code
            ),
            full_name=(
                profile_full_name
            ),
            designation=(
                profile_designation
            ),
            team_id=(
                profile_team_id
            ),
            team_name=(
                profile_team_name
            ),
            shift_id=(
                profile_shift_id
            ),
            shift_name=(
                profile_shift_name
            ),
            year=year,
            month=month,
            month_label=(
                f"{calendar.month_name[month]} "
                f"{year}"
            ),
            summary=(
                AttendanceMonthlySummary(
                    days_in_month=(
                        days_in_month
                    ),
                    recorded_days=(
                        recorded_days
                    ),
                    not_recorded_days=(
                        not_recorded_days
                    ),
                    working_day_records=(
                        working_day_records
                    ),
                    present=(
                        counts["present"]
                    ),
                    absent=(
                        counts["absent"]
                    ),
                    on_leave=(
                        counts["on_leave"]
                    ),
                    weekly_holiday=(
                        counts[
                            "weekly_holiday"
                        ]
                    ),
                    attendance_rate=round(
                        attendance_rate,
                        2,
                    ),
                )
            ),
            days=days,
        )
    )
