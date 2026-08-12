
from datetime import (
    date,
    datetime,
    timezone,
)
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
from backend.app.models.attendance_submission_audit import (
    AttendanceSubmissionAudit,
)
from backend.app.schemas.attendance_daily import (
    DailyAttendanceRecordRead,
    DailyAttendanceSubmissionAuditRead,
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
class AttendanceSubmissionLockedError(
    ValueError
):
    pass
class AttendanceSubmitterRequiredError(
    ValueError
):
    pass
class AttendanceSubmitterScopeError(
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
def _sync_record_leave_snapshot(
    database: Session,
    *,
    record: AttendanceRecord,
    approved_leave: AttendanceLeave | None,
) -> None:
    existing_snapshot = database.scalar(
        select(
            AttendanceRecordLeaveSnapshot
        ).where(
            AttendanceRecordLeaveSnapshot
            .attendance_record_id
            == record.id
        )
    )
    if (
        record.status != "on_leave"
        or approved_leave is None
    ):
        if existing_snapshot is not None:
            database.delete(
                existing_snapshot
            )
        return
    if existing_snapshot is None:
        database.add(
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
        return
    existing_snapshot.attendance_leave_id = (
        approved_leave.id
    )
    existing_snapshot.leave_type = (
        approved_leave.leave_type
    )
    existing_snapshot.leave_reason = (
        approved_leave.reason
    )
    existing_snapshot.leave_from_date = (
        approved_leave.from_date
    )
    existing_snapshot.leave_to_date = (
        approved_leave.to_date
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
    approved_leave_by_employee_id: dict[
        int,
        AttendanceLeave,
    ] = {}
    submission_audit = database.scalar(
        select(
            AttendanceSubmissionAudit
        ).where(
            AttendanceSubmissionAudit
            .attendance_date
            == attendance_date,
            AttendanceSubmissionAudit
            .team_id
            == team_id,
            AttendanceSubmissionAudit
            .shift_id
            == shift_id,
        )
    )
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
        approved_leaves = list(
            database.scalars(
                select(
                    AttendanceLeave
                ).where(
                    AttendanceLeave
                    .employee_id
                    .in_(employee_ids),
                    AttendanceLeave.status
                    == "approved",
                    AttendanceLeave.from_date
                    <= attendance_date,
                    AttendanceLeave.to_date
                    >= attendance_date,
                )
            ).all()
        )
        approved_leave_by_employee_id = {
            leave.employee_id:
                leave
            for leave in approved_leaves
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
        approved_leave = (
            approved_leave_by_employee_id
            .get(employee.id)
        )
        if (
            weekday_name
            in employee.weekly_holidays
        ):
            suggested_status = (
                "weekly_holiday"
            )
        elif approved_leave is not None:
            suggested_status = "on_leave"
        else:
            suggested_status = "present"
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
                approved_leave_id=(
                    approved_leave.id
                    if approved_leave
                    is not None
                    else None
                ),
                approved_leave_type=(
                    approved_leave.leave_type
                    if approved_leave
                    is not None
                    else None
                ),
                approved_leave_reason=(
                    approved_leave.reason
                    if approved_leave
                    is not None
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
        submission_audit=(
            DailyAttendanceSubmissionAuditRead
            .model_validate(
                submission_audit
            )
            if submission_audit
            is not None
            else None
        ),
    )
def submit_daily_attendance(
    database: Session,
    *,
    request: DailyAttendanceSubmit,
    recorded_by_id: int,
    recorded_by_email: str = "",
    submitted_by_employee_id: int | None = None,
    is_admin_submission: bool = True,
    allow_update: bool = True,
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
    selected_submitter = None
    if not is_admin_submission:
        if submitted_by_employee_id is None:
            raise (
                AttendanceSubmitterRequiredError(
                    "Select the employee who is "
                    "submitting this attendance."
                )
            )
        selected_submitter = (
            roster_by_id.get(
                submitted_by_employee_id
            )
        )
        if selected_submitter is None:
            raise (
                AttendanceSubmitterScopeError(
                    "The selected submitter must "
                    "belong to this team and shift."
                )
            )
    if (
        not allow_update
        and roster_ids
    ):
        existing_record_id = (
            database.scalar(
                select(
                    AttendanceRecord.id
                )
                .where(
                    AttendanceRecord
                    .attendance_date
                    == request.attendance_date,
                    AttendanceRecord
                    .employee_id
                    .in_(roster_ids),
                )
                .limit(1)
            )
        )
        if existing_record_id is not None:
            raise (
                AttendanceSubmissionLockedError(
                    "Attendance for this date, "
                    "team and shift has already "
                    "been submitted. Employee "
                    "accounts cannot edit a "
                    "submitted roster."
                )
            )
    approved_leave_by_employee_id: dict[
        int,
        AttendanceLeave,
    ] = {}
    if roster_ids:
        approved_leaves = list(
            database.scalars(
                select(
                    AttendanceLeave
                ).where(
                    AttendanceLeave
                    .employee_id
                    .in_(roster_ids),
                    AttendanceLeave.status
                    == "approved",
                    AttendanceLeave.from_date
                    <= request.attendance_date,
                    AttendanceLeave.to_date
                    >= request.attendance_date,
                )
            ).all()
        )
        approved_leave_by_employee_id = {
            leave.employee_id:
                leave
            for leave in approved_leaves
        }
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
        _sync_record_leave_snapshot(
            database,
            record=record,
            approved_leave=(
                approved_leave_by_employee_id
                .get(record.employee_id)
            ),
        )
    account_email = (
        recorded_by_email.strip()
        or f"user:{recorded_by_id}"
    )
    submission_audit = database.scalar(
        select(
            AttendanceSubmissionAudit
        ).where(
            AttendanceSubmissionAudit
            .attendance_date
            == request.attendance_date,
            AttendanceSubmissionAudit
            .team_id
            == request.team_id,
            AttendanceSubmissionAudit
            .shift_id
            == request.shift_id,
        )
    )
    now = datetime.now(
        timezone.utc
    )
    if submission_audit is None:
        submission_audit = (
            AttendanceSubmissionAudit(
                attendance_date=(
                    request.attendance_date
                ),
                team_id=request.team_id,
                shift_id=request.shift_id,
                submitted_by_user_id=(
                    recorded_by_id
                ),
                submitted_account_email=(
                    account_email
                ),
                submitted_by_employee_id=(
                    selected_submitter.id
                    if selected_submitter
                    is not None
                    else None
                ),
                submitted_by_employee_code=(
                    selected_submitter
                    .employee_code
                    if selected_submitter
                    is not None
                    else None
                ),
                submitted_by_employee_name=(
                    selected_submitter
                    .full_name
                    if selected_submitter
                    is not None
                    else None
                ),
                submitted_at=now,
                last_updated_by_user_id=(
                    recorded_by_id
                ),
                last_updated_account_email=(
                    account_email
                ),
                last_updated_at=now,
            )
        )
        database.add(
            submission_audit
        )
    else:
        submission_audit            .last_updated_by_user_id = (
                recorded_by_id
            )
        submission_audit            .last_updated_account_email = (
                account_email
            )
        submission_audit            .last_updated_at = now
    database.commit()
    for record in saved_records:
        database.refresh(record)
    database.refresh(
        submission_audit
    )
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
        submission_audit=(
            DailyAttendanceSubmissionAuditRead
            .model_validate(
                submission_audit
            )
        ),
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
