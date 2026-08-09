from datetime import date
from sqlalchemy import select
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
from backend.app.models.attendance_shift import (
    AttendanceShift,
)
from backend.app.models.attendance_team import (
    AttendanceTeam,
)
from backend.app.schemas.attendance_analytics import (
    AttendanceAnalyticsCounts,
    AttendanceAnalyticsDailyItem,
    AttendanceAnalyticsEmployeeItem,
    AttendanceAnalyticsRead,
    AttendanceAnalyticsShiftItem,
    AttendanceAnalyticsTeamItem,
)
class AttendanceAnalyticsRangeError(
    ValueError
):
    pass
def _new_counts() -> dict[str, int]:
    return {
        "total_records": 0,
        "present": 0,
        "absent": 0,
        "on_leave": 0,
        "weekly_holiday": 0,
    }
def _add_status(
    counts: dict[str, int],
    status: str,
) -> None:
    counts[
        "total_records"
    ] += 1
    if status in {
        "present",
        "absent",
        "on_leave",
        "weekly_holiday",
    }:
        counts[status] += 1
def _build_counts(
    counts: dict[str, int],
) -> AttendanceAnalyticsCounts:
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
    return AttendanceAnalyticsCounts(
        total_records=(
            counts["total_records"]
        ),
        working_day_records=(
            working_day_records
        ),
        present=counts["present"],
        absent=counts["absent"],
        on_leave=counts["on_leave"],
        weekly_holiday=(
            counts["weekly_holiday"]
        ),
        attendance_rate=round(
            attendance_rate,
            2,
        ),
    )
def _identity_values(
    *,
    record: AttendanceRecord,
    snapshot: (
        AttendanceRecordSnapshot
        | None
    ),
    employee: AttendanceEmployee | None,
    team: AttendanceTeam | None,
    shift: AttendanceShift | None,
) -> tuple[
    str,
    str,
    str,
    str,
    str,
]:
    employee_code = (
        snapshot.employee_code
        if snapshot is not None
        else (
            employee.employee_code
            if employee is not None
            else (
                f"Employee #{record.employee_id}"
            )
        )
    )
    full_name = (
        snapshot.full_name
        if snapshot is not None
        else (
            employee.full_name
            if employee is not None
            else "Unknown employee"
        )
    )
    designation = (
        snapshot.designation
        if snapshot is not None
        else (
            employee.designation
            if employee is not None
            else "Unknown designation"
        )
    )
    team_name = (
        snapshot.team_name
        if snapshot is not None
        else (
            team.name
            if team is not None
            else f"Team #{record.team_id}"
        )
    )
    shift_name = (
        snapshot.shift_name
        if snapshot is not None
        else (
            shift.name
            if shift is not None
            else f"Shift #{record.shift_id}"
        )
    )
    return (
        employee_code,
        full_name,
        designation,
        team_name,
        shift_name,
    )
def get_attendance_analytics(
    database: Session,
    *,
    date_from: date,
    date_to: date,
    team_id: int | None = None,
    shift_id: int | None = None,
) -> AttendanceAnalyticsRead:
    if date_from > date_to:
        raise AttendanceAnalyticsRangeError(
            "date_from cannot be later "
            "than date_to."
        )
    statement = (
        select(
            AttendanceRecord,
            AttendanceRecordSnapshot,
            AttendanceEmployee,
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
            AttendanceEmployee,
            AttendanceEmployee.id
            == AttendanceRecord.employee_id,
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
            AttendanceRecord.attendance_date
            >= date_from,
            AttendanceRecord.attendance_date
            <= date_to,
        )
    )
    if team_id is not None:
        statement = statement.where(
            AttendanceRecord.team_id
            == team_id
        )
    if shift_id is not None:
        statement = statement.where(
            AttendanceRecord.shift_id
            == shift_id
        )
    statement = statement.order_by(
        AttendanceRecord
        .attendance_date
        .asc(),
        AttendanceRecord
        .employee_id
        .asc(),
    )
    rows = database.execute(
        statement
    ).all()
    overall = _new_counts()
    daily: dict[
        date,
        dict[str, int],
    ] = {}
    teams: dict[
        int,
        dict,
    ] = {}
    shifts: dict[
        int,
        dict,
    ] = {}
    employees: dict[
        tuple[int, int, int],
        dict,
    ] = {}
    for (
        record,
        snapshot,
        employee,
        team,
        shift,
    ) in rows:
        (
            employee_code,
            full_name,
            designation,
            team_name,
            shift_name,
        ) = _identity_values(
            record=record,
            snapshot=snapshot,
            employee=employee,
            team=team,
            shift=shift,
        )
        _add_status(
            overall,
            record.status,
        )
        daily_counts = daily.setdefault(
            record.attendance_date,
            _new_counts(),
        )
        _add_status(
            daily_counts,
            record.status,
        )
        team_data = teams.setdefault(
            record.team_id,
            {
                "team_name":
                    team_name,
                "counts":
                    _new_counts(),
            },
        )
        _add_status(
            team_data["counts"],
            record.status,
        )
        shift_data = shifts.setdefault(
            record.shift_id,
            {
                "shift_name":
                    shift_name,
                "counts":
                    _new_counts(),
            },
        )
        _add_status(
            shift_data["counts"],
            record.status,
        )
        employee_key = (
            record.employee_id,
            record.team_id,
            record.shift_id,
        )
        employee_data = (
            employees.setdefault(
                employee_key,
                {
                    "employee_code":
                        employee_code,
                    "full_name":
                        full_name,
                    "designation":
                        designation,
                    "team_name":
                        team_name,
                    "shift_name":
                        shift_name,
                    "counts":
                        _new_counts(),
                },
            )
        )
        _add_status(
            employee_data["counts"],
            record.status,
        )
    daily_items = [
        AttendanceAnalyticsDailyItem(
            attendance_date=(
                attendance_date
            ),
            **_build_counts(
                counts
            ).model_dump(),
        )
        for attendance_date, counts
        in sorted(
            daily.items(),
            key=lambda item:
                item[0],
        )
    ]
    team_items = [
        AttendanceAnalyticsTeamItem(
            team_id=item_team_id,
            team_name=data[
                "team_name"
            ],
            **_build_counts(
                data["counts"]
            ).model_dump(),
        )
        for item_team_id, data
        in teams.items()
    ]
    team_items.sort(
        key=lambda item: (
            item.team_name.lower(),
            item.team_id,
        )
    )
    shift_items = [
        AttendanceAnalyticsShiftItem(
            shift_id=item_shift_id,
            shift_name=data[
                "shift_name"
            ],
            **_build_counts(
                data["counts"]
            ).model_dump(),
        )
        for item_shift_id, data
        in shifts.items()
    ]
    shift_items.sort(
        key=lambda item: (
            item.shift_name.lower(),
            item.shift_id,
        )
    )
    employee_items = []
    for (
        employee_id,
        item_team_id,
        item_shift_id,
    ), data in employees.items():
        employee_items.append(
            AttendanceAnalyticsEmployeeItem(
                employee_id=employee_id,
                employee_code=data[
                    "employee_code"
                ],
                full_name=data[
                    "full_name"
                ],
                designation=data[
                    "designation"
                ],
                team_id=item_team_id,
                team_name=data[
                    "team_name"
                ],
                shift_id=item_shift_id,
                shift_name=data[
                    "shift_name"
                ],
                **_build_counts(
                    data["counts"]
                ).model_dump(),
            )
        )
    employee_items.sort(
        key=lambda item: (
            item.employee_code.lower(),
            item.team_name.lower(),
            item.shift_name.lower(),
        )
    )
    return AttendanceAnalyticsRead(
        date_from=date_from,
        date_to=date_to,
        team_id=team_id,
        shift_id=shift_id,
        summary=_build_counts(
            overall
        ),
        daily_trend=daily_items,
        teams=team_items,
        shifts=shift_items,
        employees=employee_items,
    )
