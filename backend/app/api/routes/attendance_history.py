
import csv
from datetime import date
from io import StringIO
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Response,
    status,
)
from backend.app.api.dependencies import (
    CurrentUserDependency,
    DatabaseDependency,
)
from backend.app.schemas.attendance_history import (
    AttendanceHistoryListRead,
    AttendanceHistoryReportRead,
)
from backend.app.services import (
    attendance_history_service,
    attendance_pdf_service,
)
router = APIRouter(
    prefix="/api/attendance/history",
    tags=["Attendance History"],
)
@router.get(
    "",
    response_model=(
        AttendanceHistoryListRead
    ),
    summary=(
        "List saved attendance reports"
    ),
)
def read_attendance_history(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    date_from: date | None = Query(
        default=None
    ),
    date_to: date | None = Query(
        default=None
    ),
    team_id: int | None = Query(
        default=None,
        gt=0,
    ),
    shift_id: int | None = Query(
        default=None,
        gt=0,
    ),
) -> AttendanceHistoryListRead:
    try:
        return (
            attendance_history_service
            .list_attendance_history(
                database=database,
                date_from=date_from,
                date_to=date_to,
                team_id=team_id,
                shift_id=shift_id,
            )
        )
    except (
        attendance_history_service
        .AttendanceHistoryRangeError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(error),
        ) from error
def _csv_safe(
    value: object | None,
) -> str:
    if value is None:
        return ""
    text = str(value)
    if (
        text.lstrip()
        .startswith(
            (
                "=",
                "+",
                "-",
                "@",
            )
        )
    ):
        return "'" + text
    return text
def _format_attendance_status(
    value: str,
) -> str:
    return (
        value.replace(
            "_",
            " ",
        )
        .title()
    )
@router.get(
    "/report.pdf",
    response_class=Response,
    summary=(
        "Download attendance report as PDF"
    ),
)
def download_attendance_report_pdf(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    attendance_date: date = Query(),
    team_id: int = Query(gt=0),
    shift_id: int = Query(gt=0),
) -> Response:
    try:
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
    except (
        attendance_history_service
        .AttendanceHistoryNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    pdf_content = (
        attendance_pdf_service
        .build_attendance_report_pdf(
            report
        )
    )
    filename = (
        "attendance_"
        f"{attendance_date.isoformat()}"
        f"_team_{team_id}"
        f"_shift_{shift_id}.pdf"
    )
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                'attachment; filename="'
                + filename
                + '"'
            )
        },
    )
@router.get(
    "/report.csv",
    response_class=Response,
    summary=(
        "Download attendance report as CSV"
    ),
)
def download_attendance_report_csv(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    attendance_date: date = Query(),
    team_id: int = Query(gt=0),
    shift_id: int = Query(gt=0),
) -> Response:
    try:
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
    except (
        attendance_history_service
        .AttendanceHistoryNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    output = StringIO(
        newline=""
    )
    writer = csv.writer(output)
    writer.writerow(
        [
            "Attendance Report",
        ]
    )
    writer.writerow(
        [
            "Date",
            report
            .attendance_date
            .isoformat(),
        ]
    )
    writer.writerow(
        [
            "Team",
            _csv_safe(
                report.team_name
            ),
        ]
    )
    writer.writerow(
        [
            "Shift",
            _csv_safe(
                report.shift_name
            ),
        ]
    )
    writer.writerow([])
    writer.writerow(
        [
            "Attendance Summary",
            "Count",
        ]
    )
    writer.writerow(
        [
            "Total Members",
            report.summary.total_members,
        ]
    )
    writer.writerow(
        [
            "Present",
            report.summary.present,
        ]
    )
    writer.writerow(
        [
            "Absent",
            report.summary.absent,
        ]
    )
    writer.writerow(
        [
            "On Leave",
            report.summary.on_leave,
        ]
    )
    writer.writerow(
        [
            "Weekly Holiday",
            report.summary.weekly_holiday,
        ]
    )
    writer.writerow([])
    writer.writerow(
        [
            "Employee ID",
            "Employee Code",
            "Employee Name",
            "Designation",
            "Status",
            "Leave Type",
            "Leave Reason",
            "Leave From",
            "Leave To",
            "Note",
        ]
    )
    for employee in report.employees:
        writer.writerow(
            [
                employee.employee_id,
                _csv_safe(
                    employee.employee_code
                ),
                _csv_safe(
                    employee.full_name
                ),
                _csv_safe(
                    employee.designation
                ),
                _format_attendance_status(
                    employee.status
                ),
                (
                    _format_attendance_status(
                        employee.leave_type
                    )
                    if employee.leave_type
                    is not None
                    else ""
                ),
                _csv_safe(
                    employee.leave_reason
                ),
                (
                    employee.leave_from_date
                    .isoformat()
                    if employee.leave_from_date
                    is not None
                    else ""
                ),
                (
                    employee.leave_to_date
                    .isoformat()
                    if employee.leave_to_date
                    is not None
                    else ""
                ),
                _csv_safe(
                    employee.note
                ),
            ]
        )
    filename = (
        "attendance_"
        f"{attendance_date.isoformat()}"
        f"_team_{team_id}"
        f"_shift_{shift_id}.csv"
    )
    content = (
        "\ufeff"
        + output.getvalue()
    )
    return Response(
        content=content,
        media_type=(
            "text/csv; charset=utf-8"
        ),
        headers={
            "Content-Disposition": (
                'attachment; filename="'
                + filename
                + '"'
            )
        },
    )
@router.get(
    "/report",
    response_model=(
        AttendanceHistoryReportRead
    ),
    summary=(
        "Read a saved attendance report"
    ),
)
def read_attendance_report(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    attendance_date: date = Query(),
    team_id: int = Query(gt=0),
    shift_id: int = Query(gt=0),
) -> AttendanceHistoryReportRead:
    try:
        return (
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
    except (
        attendance_history_service
        .AttendanceHistoryNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
from backend.app.schemas.attendance_deletion import (
    AttendanceDeletionRead,
    AttendanceDeletionRequest,
)
from backend.app.services import (
    attendance_delete_service,
)
@router.delete(
    "/report",
    response_model=AttendanceDeletionRead,
    summary=(
        "Delete a saved attendance report"
    ),
)
def delete_attendance_report(
    request: AttendanceDeletionRequest,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    attendance_date: date = Query(),
    team_id: int = Query(gt=0),
    shift_id: int = Query(gt=0),
) -> AttendanceDeletionRead:
    try:
        return (
            attendance_delete_service
            .delete_attendance_report(
                database=database,
                attendance_date=(
                    attendance_date
                ),
                team_id=team_id,
                shift_id=shift_id,
                reason=request.reason,
                deleted_by_user_id=(
                    current_user.id
                ),
                deleted_by_email=(
                    current_user.email
                ),
            )
        )
    except (
        attendance_history_service
        .AttendanceHistoryNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
