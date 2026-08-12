from datetime import date
from sqlalchemy import (
    delete,
    select,
)
from sqlalchemy.orm import Session
from backend.app.models.attendance_deletion_audit import (
    AttendanceDeletionAudit,
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
from backend.app.models.attendance_submission_audit import (
    AttendanceSubmissionAudit,
)
from backend.app.schemas.attendance_deletion import (
    AttendanceDeletionRead,
)
from backend.app.services import (
    attendance_history_service,
)
def delete_attendance_report(
    database: Session,
    *,
    attendance_date: date,
    team_id: int,
    shift_id: int,
    reason: str,
    deleted_by_user_id: int,
    deleted_by_email: str,
) -> AttendanceDeletionRead:
    report = (
        attendance_history_service
        .get_attendance_report(
            database=database,
            attendance_date=(
                attendance_date
            ),
            team_id=team_id,
            shift_id=shift_id,
        )
    )
    records = list(
        database.scalars(
            select(
                AttendanceRecord
            ).where(
                AttendanceRecord
                .attendance_date
                == attendance_date,
                AttendanceRecord.team_id
                == team_id,
                AttendanceRecord.shift_id
                == shift_id,
            )
        ).all()
    )
    if not records:
        raise (
            attendance_history_service
            .AttendanceHistoryNotFoundError(
                "No saved attendance report "
                "was found for the selected "
                "date, team and shift."
            )
        )
    record_ids = [
        record.id
        for record in records
    ]
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
    deletion_audit = (
        AttendanceDeletionAudit(
            attendance_date=(
                attendance_date
            ),
            team_id=team_id,
            team_name=report.team_name,
            shift_id=shift_id,
            shift_name=report.shift_name,
            deleted_record_count=(
                len(records)
            ),
            reason=reason,
            deleted_by_user_id=(
                deleted_by_user_id
            ),
            deleted_by_email=(
                deleted_by_email
            ),
            original_account_email=(
                submission_audit
                .submitted_account_email
                if submission_audit
                is not None
                else None
            ),
            original_submitter_code=(
                submission_audit
                .submitted_by_employee_code
                if submission_audit
                is not None
                else None
            ),
            original_submitter_name=(
                submission_audit
                .submitted_by_employee_name
                if submission_audit
                is not None
                else None
            ),
        )
    )
    database.add(
        deletion_audit
    )
    database.flush()
    database.execute(
        delete(
            AttendanceRecordLeaveSnapshot
        ).where(
            AttendanceRecordLeaveSnapshot
            .attendance_record_id
            .in_(record_ids)
        )
    )
    database.execute(
        delete(
            AttendanceRecordSnapshot
        ).where(
            AttendanceRecordSnapshot
            .attendance_record_id
            .in_(record_ids)
        )
    )
    database.execute(
        delete(
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
    database.execute(
        delete(
            AttendanceRecord
        ).where(
            AttendanceRecord.id
            .in_(record_ids)
        )
    )
    database.commit()
    database.refresh(
        deletion_audit
    )
    return (
        AttendanceDeletionRead
        .model_validate(
            deletion_audit
        )
    )
