from collections.abc import Generator
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool
from backend.app.core.security import (
    create_access_token,
)
from backend.app.db.database import (
    Base,
    get_db,
)
from backend.app.main import app
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
from backend.app.models.user import User
test_engine = create_engine(
    "sqlite://",
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)
def override_get_db() -> Generator[
    Session,
    None,
    None,
]:
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()
@pytest.fixture(autouse=True)
def prepare_environment() -> Generator[
    None,
    None,
    None,
]:
    Base.metadata.drop_all(
        bind=test_engine
    )
    Base.metadata.create_all(
        bind=test_engine
    )
    app.dependency_overrides[
        get_db
    ] = override_get_db
    yield
    app.dependency_overrides.pop(
        get_db,
        None,
    )
def create_admin_headers() -> dict[
    str,
    str,
]:
    email = (
        "monthly-admin@example.com"
    )
    with TestingSessionLocal() as database:
        database.add(
            User(
                email=email,
                hashed_password="unused",
                is_active=True,
                is_admin=True,
            )
        )
        database.commit()
    token = create_access_token(
        subject=email
    )
    return {
        "Authorization":
            f"Bearer {token}"
    }
def seed_monthly_data() -> dict[
    str,
    int,
]:
    with TestingSessionLocal() as database:
        admin = database.query(
            User
        ).first()
        assert admin is not None
        team = AttendanceTeam(
            name="Labelmaster",
            status="active",
            created_by_id=admin.id,
        )
        shift = AttendanceShift(
            name="Night",
            status="active",
            created_by_id=admin.id,
        )
        database.add_all(
            [
                team,
                shift,
            ]
        )
        database.flush()
        employee = AttendanceEmployee(
            employee_code="EMP023",
            full_name="Pritom",
            designation=(
                "Data Annotation Analyst"
            ),
            team_id=team.id,
            shift_id=shift.id,
            weekly_holidays=[
                "Tuesday",
                "Wednesday",
            ],
            is_active=True,
            created_by_id=admin.id,
        )
        database.add(employee)
        database.flush()
        records = [
            AttendanceRecord(
                employee_id=employee.id,
                attendance_date=date(
                    2026,
                    8,
                    1,
                ),
                team_id=team.id,
                shift_id=shift.id,
                status="present",
                note=None,
                recorded_by_id=admin.id,
            ),
            AttendanceRecord(
                employee_id=employee.id,
                attendance_date=date(
                    2026,
                    8,
                    2,
                ),
                team_id=team.id,
                shift_id=shift.id,
                status="absent",
                note="No show",
                recorded_by_id=admin.id,
            ),
            AttendanceRecord(
                employee_id=employee.id,
                attendance_date=date(
                    2026,
                    8,
                    3,
                ),
                team_id=team.id,
                shift_id=shift.id,
                status="on_leave",
                note=None,
                recorded_by_id=admin.id,
            ),
            AttendanceRecord(
                employee_id=employee.id,
                attendance_date=date(
                    2026,
                    8,
                    4,
                ),
                team_id=team.id,
                shift_id=shift.id,
                status="weekly_holiday",
                note=None,
                recorded_by_id=admin.id,
            ),
            AttendanceRecord(
                employee_id=employee.id,
                attendance_date=date(
                    2026,
                    7,
                    31,
                ),
                team_id=team.id,
                shift_id=shift.id,
                status="present",
                note=None,
                recorded_by_id=admin.id,
            ),
        ]
        database.add_all(
            records
        )
        database.flush()
        august_records = [
            record
            for record in records
            if record.attendance_date.month
            == 8
        ]
        for record in august_records:
            database.add(
                AttendanceRecordSnapshot(
                    attendance_record_id=(
                        record.id
                    ),
                    employee_code=(
                        "HIST023"
                    ),
                    full_name=(
                        "Historical Pritom"
                    ),
                    designation=(
                        "Historical Analyst"
                    ),
                    team_name=(
                        "Historical Labelmaster"
                    ),
                    shift_name=(
                        "Historical Night"
                    ),
                )
            )
        leave_record = records[2]
        database.add(
            AttendanceRecordLeaveSnapshot(
                attendance_record_id=(
                    leave_record.id
                ),
                attendance_leave_id=99,
                leave_type="annual",
                leave_reason=(
                    "Family trip"
                ),
                leave_from_date=date(
                    2026,
                    8,
                    3,
                ),
                leave_to_date=date(
                    2026,
                    8,
                    5,
                ),
            )
        )
        database.commit()
        return {
            "employee_id":
                employee.id,
        }
def test_monthly_report_requires_authentication():
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/employees/"
            "1/monthly-report",
            params={
                "year": 2026,
                "month": 8,
            },
        )
    assert response.status_code == 401
def test_monthly_report_returns_404_for_unknown_employee():
    headers = create_admin_headers()
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/employees/"
            "999/monthly-report",
            headers=headers,
            params={
                "year": 2026,
                "month": 8,
            },
        )
    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Attendance employee not found."
    )
def test_monthly_report_calculates_summary_and_rate():
    headers = create_admin_headers()
    data = seed_monthly_data()
    with TestClient(app) as client:
        response = client.get(
            (
                "/api/attendance/employees/"
                f"{data['employee_id']}"
                "/monthly-report"
            ),
            headers=headers,
            params={
                "year": 2026,
                "month": 8,
            },
        )
    assert response.status_code == 200
    summary = (
        response.json()["summary"]
    )
    assert summary["days_in_month"] == 31
    assert summary["recorded_days"] == 4
    assert (
        summary["not_recorded_days"]
        == 27
    )
    assert (
        summary["working_day_records"]
        == 3
    )
    assert summary["present"] == 1
    assert summary["absent"] == 1
    assert summary["on_leave"] == 1
    assert (
        summary["weekly_holiday"]
        == 1
    )
    assert (
        summary["attendance_rate"]
        == 33.33
    )
def test_monthly_report_builds_full_calendar_with_not_recorded_days():
    headers = create_admin_headers()
    data = seed_monthly_data()
    with TestClient(app) as client:
        response = client.get(
            (
                "/api/attendance/employees/"
                f"{data['employee_id']}"
                "/monthly-report"
            ),
            headers=headers,
            params={
                "year": 2026,
                "month": 8,
            },
        )
    assert response.status_code == 200
    days = response.json()["days"]
    assert len(days) == 31
    assert days[0][
        "attendance_date"
    ] == "2026-08-01"
    assert days[-1][
        "attendance_date"
    ] == "2026-08-31"
    fifth = next(
        item
        for item in days
        if item[
            "attendance_date"
        ] == "2026-08-05"
    )
    assert (
        fifth["status"]
        == "not_recorded"
    )
    assert (
        fifth["is_recorded"]
        is False
    )
    assert fifth["record_id"] is None
def test_monthly_report_preserves_leave_snapshot_details():
    headers = create_admin_headers()
    data = seed_monthly_data()
    with TestClient(app) as client:
        response = client.get(
            (
                "/api/attendance/employees/"
                f"{data['employee_id']}"
                "/monthly-report"
            ),
            headers=headers,
            params={
                "year": 2026,
                "month": 8,
            },
        )
    assert response.status_code == 200
    leave_day = next(
        item
        for item in response.json()[
            "days"
        ]
        if item[
            "attendance_date"
        ] == "2026-08-03"
    )
    assert (
        leave_day["status"]
        == "on_leave"
    )
    assert (
        leave_day["leave_id"]
        == 99
    )
    assert (
        leave_day["leave_type"]
        == "annual"
    )
    assert (
        leave_day["leave_reason"]
        == "Family trip"
    )
    assert (
        leave_day["leave_from_date"]
        == "2026-08-03"
    )
    assert (
        leave_day["leave_to_date"]
        == "2026-08-05"
    )
def test_monthly_report_uses_historical_snapshot_identity():
    headers = create_admin_headers()
    data = seed_monthly_data()
    with TestingSessionLocal() as database:
        employee = database.get(
            AttendanceEmployee,
            data["employee_id"],
        )
        assert employee is not None
        employee.full_name = (
            "Current Changed Name"
        )
        database.commit()
    with TestClient(app) as client:
        response = client.get(
            (
                "/api/attendance/employees/"
                f"{data['employee_id']}"
                "/monthly-report"
            ),
            headers=headers,
            params={
                "year": 2026,
                "month": 8,
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert (
        body["employee_code"]
        == "HIST023"
    )
    assert (
        body["full_name"]
        == "Historical Pritom"
    )
    assert (
        body["designation"]
        == "Historical Analyst"
    )
    assert (
        body["team_name"]
        == "Historical Labelmaster"
    )
    assert (
        body["shift_name"]
        == "Historical Night"
    )
def test_monthly_report_does_not_include_other_month_records():
    headers = create_admin_headers()
    data = seed_monthly_data()
    with TestClient(app) as client:
        response = client.get(
            (
                "/api/attendance/employees/"
                f"{data['employee_id']}"
                "/monthly-report"
            ),
            headers=headers,
            params={
                "year": 2026,
                "month": 8,
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["month_label"] == (
        "August 2026"
    )
    assert (
        body["summary"]["recorded_days"]
        == 4
    )
    assert all(
        day["attendance_date"].startswith(
            "2026-08-"
        )
        for day in body["days"]
    )
def test_monthly_report_validates_month_and_year():
    headers = create_admin_headers()
    with TestClient(app) as client:
        invalid_month = client.get(
            "/api/attendance/employees/"
            "1/monthly-report",
            headers=headers,
            params={
                "year": 2026,
                "month": 13,
            },
        )
        invalid_year = client.get(
            "/api/attendance/employees/"
            "1/monthly-report",
            headers=headers,
            params={
                "year": 1999,
                "month": 8,
            },
        )
    assert (
        invalid_month.status_code
        == 422
    )
    assert (
        invalid_year.status_code
        == 422
    )

def test_monthly_csv_export_returns_calendar():
    headers = create_admin_headers()
    data = seed_monthly_data()
    with TestClient(app) as client:
        response = client.get(
            (
                "/api/attendance/employees/"
                f"{data['employee_id']}"
                "/monthly-report.csv"
            ),
            headers=headers,
            params={
                "year": 2026,
                "month": 8,
            },
        )
    assert response.status_code == 200
    assert (
        "text/csv"
        in response.headers[
            "content-type"
        ]
    )
    assert (
        "employee_attendance_"
        in response.headers[
            "content-disposition"
        ]
    )
    text = response.content.decode(
        "utf-8-sig"
    )
    assert (
        "Employee Monthly Attendance Report"
        in text
    )
    assert "Historical Pritom" in text
    assert "2026-08-03" in text
    assert "On Leave" in text
    assert "Family trip" in text
    assert "2026-08-05" in text
    assert "Not Recorded" in text
def test_monthly_pdf_export_returns_valid_pdf():
    from io import BytesIO
    from pypdf import PdfReader
    headers = create_admin_headers()
    data = seed_monthly_data()
    with TestClient(app) as client:
        response = client.get(
            (
                "/api/attendance/employees/"
                f"{data['employee_id']}"
                "/monthly-report.pdf"
            ),
            headers=headers,
            params={
                "year": 2026,
                "month": 8,
            },
        )
    assert response.status_code == 200
    assert (
        response.headers[
            "content-type"
        ]
        == "application/pdf"
    )
    assert response.content.startswith(
        b"%PDF"
    )
    assert (
        "employee_attendance_"
        in response.headers[
            "content-disposition"
        ]
    )
    reader = PdfReader(
        BytesIO(
            response.content
        )
    )
    assert len(reader.pages) >= 1
    text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )
    assert (
        "EMPLOYEE MONTHLY ATTENDANCE REPORT"
        in text
    )
    assert "Historical Pritom" in text
    assert "August 2026" in text
    assert "On Leave" in text
    assert "Annual" in text
    assert "Family trip" in text
    assert "Not Recorded" in text
