
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
from backend.app.models.attendance_record_leave_snapshot import (
    AttendanceRecordLeaveSnapshot,
)
from backend.app.models.attendance_leave import (
    AttendanceLeave,
)
from backend.app.models.attendance_shift import (
    AttendanceShift,
)
from backend.app.models.attendance_team import (
    AttendanceTeam,
)
from backend.app.schemas.attendance_history import (
    AttendanceHistoryEmployeeRead,
    AttendanceHistoryItem,
    AttendanceHistoryListRead,
    AttendanceHistoryReportRead,
)
from backend.app.services.attendance_daily_service import (
    build_summary,
)
class AttendanceHistoryNotFoundError(
    ValueError
):
    pass
class AttendanceHistoryRangeError(
    ValueError
):
    pass
def _history_statement():
    return (
        select(
            AttendanceRecord,
            AttendanceRecordSnapshot,
            AttendanceRecordLeaveSnapshot,
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
            AttendanceRecordLeaveSnapshot,
            AttendanceRecordLeaveSnapshot
            .attendance_record_id
            == AttendanceRecord.id,
        )
        .outerjoin(
            AttendanceEmployee,
            AttendanceEmployee.id
            == AttendanceRecord
            .employee_id,
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
    )
def _snapshot_values(
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
def _backfill_legacy_leave_snapshot(
    database: Session,
    *,
    record: AttendanceRecord,
) -> AttendanceRecordLeaveSnapshot | None:
    if record.status != "on_leave":
        return None
    approved_leave = database.scalar(
        select(
            AttendanceLeave
        )
        .where(
            AttendanceLeave.employee_id
            == record.employee_id,
            AttendanceLeave.status
            == "approved",
            AttendanceLeave.from_date
            <= record.attendance_date,
            AttendanceLeave.to_date
            >= record.attendance_date,
        )
        .order_by(
            AttendanceLeave.id.asc()
        )
    )
    if approved_leave is None:
        return None
    snapshot = (
        AttendanceRecordLeaveSnapshot(
            attendance_record_id=record.id,
            attendance_leave_id=(
                approved_leave.id
            ),
            leave_type=(
                approved_leave.leave_type
            ),
            leave_reason=(
                approved_leave.reason
            ),
            leave_from_date=(
                approved_leave.from_date
            ),
            leave_to_date=(
                approved_leave.to_date
            ),
        )
    )
    database.add(snapshot)
    database.flush()
    return snapshot
def list_attendance_history(
    database: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    team_id: int | None = None,
    shift_id: int | None = None,
) -> AttendanceHistoryListRead:
    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise AttendanceHistoryRangeError(
            "date_from cannot be later "
            "than date_to."
        )
    statement = _history_statement()
    if date_from is not None:
        statement = statement.where(
            AttendanceRecord
            .attendance_date
            >= date_from
        )
    if date_to is not None:
        statement = statement.where(
            AttendanceRecord
            .attendance_date
            <= date_to
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
        .desc(),
        AttendanceRecord.team_id.asc(),
        AttendanceRecord.shift_id.asc(),
        AttendanceRecord.employee_id.asc(),
    )
    rows = database.execute(
        statement
    ).all()
    grouped: dict[
        tuple[date, int, int],
        dict,
    ] = {}
    for (
        record,
        snapshot,
        leave_snapshot,
        employee,
        team,
        shift,
    ) in rows:
        (
            _employee_code,
            _full_name,
            _designation,
            team_name,
            shift_name,
        ) = _snapshot_values(
            record=record,
            snapshot=snapshot,
            employee=employee,
            team=team,
            shift=shift,
        )
        key = (
            record.attendance_date,
            record.team_id,
            record.shift_id,
        )
        if key not in grouped:
            grouped[key] = {
                "team_name": team_name,
                "shift_name": shift_name,
                "records": [],
                "last_updated_at":
                    record.updated_at,
            }
        grouped[key][
            "records"
        ].append(record)
        if (
            record.updated_at
            > grouped[key][
                "last_updated_at"
            ]
        ):
            grouped[key][
                "last_updated_at"
            ] = record.updated_at
    items: list[
        AttendanceHistoryItem
    ] = []
    for (
        attendance_date,
        grouped_team_id,
        grouped_shift_id,
    ), data in grouped.items():
        items.append(
            AttendanceHistoryItem(
                attendance_date=(
                    attendance_date
                ),
                team_id=grouped_team_id,
                team_name=data[
                    "team_name"
                ],
                shift_id=grouped_shift_id,
                shift_name=data[
                    "shift_name"
                ],
                summary=build_summary(
                    data["records"]
                ),
                last_updated_at=data[
                    "last_updated_at"
                ],
            )
        )
    items.sort(
        key=lambda item: (
            item.attendance_date,
            item.team_id,
            item.shift_id,
        ),
        reverse=True,
    )
    return AttendanceHistoryListRead(
        total_reports=len(items),
        items=items,
    )
def get_attendance_report(
    database: Session,
    *,
    attendance_date: date,
    team_id: int,
    shift_id: int,
) -> AttendanceHistoryReportRead:
    statement = (
        _history_statement()
        .where(
            AttendanceRecord
            .attendance_date
            == attendance_date,
            AttendanceRecord.team_id
            == team_id,
            AttendanceRecord.shift_id
            == shift_id,
        )
        .order_by(
            AttendanceRecord
            .employee_id
            .asc()
        )
    )
    rows = database.execute(
        statement
    ).all()
    if not rows:
        raise AttendanceHistoryNotFoundError(
            "No saved attendance report "
            "was found for the selected "
            "date, team and shift."
        )
    employees: list[
        AttendanceHistoryEmployeeRead
    ] = []
    records: list[
        AttendanceRecord
    ] = []
    report_team_name: str | None = None
    report_shift_name: str | None = None
    last_updated_at = None
    leave_snapshot_backfilled = False
    for (
        record,
        snapshot,
        leave_snapshot,
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
        ) = _snapshot_values(
            record=record,
            snapshot=snapshot,
            employee=employee,
            team=team,
            shift=shift,
        )
        report_team_name = (
            report_team_name
            or team_name
        )
        report_shift_name = (
            report_shift_name
            or shift_name
        )
        if (
            last_updated_at is None
            or record.updated_at
            > last_updated_at
        ):
            last_updated_at = (
                record.updated_at
            )
        records.append(record)
        if (
            record.status == "on_leave"
            and leave_snapshot is None
        ):
            leave_snapshot = (
                _backfill_legacy_leave_snapshot(
                    database,
                    record=record,
                )
            )
            if leave_snapshot is not None:
                leave_snapshot_backfilled = (
                    True
                )
        employees.append(
            AttendanceHistoryEmployeeRead(
                record_id=record.id,
                employee_id=(
                    record.employee_id
                ),
                employee_code=(
                    employee_code
                ),
                full_name=full_name,
                designation=designation,
                status=record.status,
                note=record.note,
                leave_id=(
                    leave_snapshot
                    .attendance_leave_id
                    if (
                        record.status
                        == "on_leave"
                        and leave_snapshot
                        is not None
                    )
                    else None
                ),
                leave_type=(
                    leave_snapshot.leave_type
                    if (
                        record.status
                        == "on_leave"
                        and leave_snapshot
                        is not None
                    )
                    else None
                ),
                leave_reason=(
                    leave_snapshot.leave_reason
                    if (
                        record.status
                        == "on_leave"
                        and leave_snapshot
                        is not None
                    )
                    else None
                ),
                leave_from_date=(
                    leave_snapshot
                    .leave_from_date
                    if (
                        record.status
                        == "on_leave"
                        and leave_snapshot
                        is not None
                    )
                    else None
                ),
                leave_to_date=(
                    leave_snapshot
                    .leave_to_date
                    if (
                        record.status
                        == "on_leave"
                        and leave_snapshot
                        is not None
                    )
                    else None
                ),
                updated_at=(
                    record.updated_at
                ),
            )
        )
    employees.sort(
        key=lambda item:
            item.employee_code
    )
    assert report_team_name is not None
    assert report_shift_name is not None
    assert last_updated_at is not None
    if leave_snapshot_backfilled:
        database.commit()
    return AttendanceHistoryReportRead(
        attendance_date=(
            attendance_date
        ),
        team_id=team_id,
        team_name=report_team_name,
        shift_id=shift_id,
        shift_name=report_shift_name,
        summary=build_summary(
            records
        ),
        employees=employees,
        last_updated_at=(
            last_updated_at
        ),
    )
