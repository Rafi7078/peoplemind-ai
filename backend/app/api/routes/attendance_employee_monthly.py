from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from backend.app.api.dependencies import (
    CurrentUserDependency,
    DatabaseDependency,
)
from backend.app.schemas.attendance_employee_monthly import (
    AttendanceEmployeeMonthlyReportRead,
)
from backend.app.services import (
    attendance_employee_monthly_export_service,
    attendance_employee_monthly_service,
)
router = APIRouter(
    prefix="/api/attendance/employees",
    tags=[
        "Attendance Employee Reports"
    ],
)
def _get_report(
    *,
    database: DatabaseDependency,
    employee_id: int,
    year: int,
    month: int,
) -> AttendanceEmployeeMonthlyReportRead:
    try:
        return (
            attendance_employee_monthly_service
            .get_employee_monthly_report(
                database,
                employee_id=employee_id,
                year=year,
                month=month,
            )
        )
    except (
        attendance_employee_monthly_service
        .AttendanceEmployeeNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
@router.get(
    "/{employee_id}/monthly-report",
    response_model=(
        AttendanceEmployeeMonthlyReportRead
    ),
    summary=(
        "Read an employee monthly "
        "attendance report"
    ),
)
def read_employee_monthly_report(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    employee_id: int = Path(
        gt=0,
    ),
    year: int = Query(
        ge=2000,
        le=2100,
    ),
    month: int = Query(
        ge=1,
        le=12,
    ),
) -> AttendanceEmployeeMonthlyReportRead:
    return _get_report(
        database=database,
        employee_id=employee_id,
        year=year,
        month=month,
    )
@router.get(
    "/{employee_id}/monthly-report.csv",
    summary=(
        "Download an employee monthly "
        "attendance CSV report"
    ),
)
def download_employee_monthly_csv(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    employee_id: int = Path(
        gt=0,
    ),
    year: int = Query(
        ge=2000,
        le=2100,
    ),
    month: int = Query(
        ge=1,
        le=12,
    ),
) -> Response:
    report = _get_report(
        database=database,
        employee_id=employee_id,
        year=year,
        month=month,
    )
    content = (
        attendance_employee_monthly_export_service
        .build_monthly_csv(
            report
        )
    )
    filename = (
        "employee_attendance_"
        f"{report.employee_code}_"
        f"{year}-{month:02d}.csv"
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
    "/{employee_id}/monthly-report.pdf",
    summary=(
        "Download an employee monthly "
        "attendance PDF report"
    ),
)
def download_employee_monthly_pdf(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    employee_id: int = Path(
        gt=0,
    ),
    year: int = Query(
        ge=2000,
        le=2100,
    ),
    month: int = Query(
        ge=1,
        le=12,
    ),
) -> Response:
    report = _get_report(
        database=database,
        employee_id=employee_id,
        year=year,
        month=month,
    )
    content = (
        attendance_employee_monthly_export_service
        .build_monthly_pdf(
            report
        )
    )
    filename = (
        "employee_attendance_"
        f"{report.employee_code}_"
        f"{year}-{month:02d}.pdf"
    )
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                'attachment; filename="'
                + filename
                + '"'
            )
        },
    )
