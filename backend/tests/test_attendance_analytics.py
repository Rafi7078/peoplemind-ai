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
        "analytics-admin@example.com"
    )
    with TestingSessionLocal() as database:
        user = User(
            email=email,
            hashed_password="unused",
            is_active=True,
            is_admin=True,
        )
        database.add(user)
        database.commit()
    token = create_access_token(
        subject=email
    )
    return {
        "Authorization":
            f"Bearer {token}"
    }
def seed_analytics_data():
    with TestingSessionLocal() as database:
        admin = database.query(
            User
        ).first()
        assert admin is not None
        team_one = AttendanceTeam(
            name="Labelmaster",
            status="active",
            created_by_id=admin.id,
        )
        team_two = AttendanceTeam(
            name="CVAT",
            status="active",
            created_by_id=admin.id,
        )
        shift_one = AttendanceShift(
            name="Night",
            status="active",
            created_by_id=admin.id,
        )
        shift_two = AttendanceShift(
            name="Morning",
            status="active",
            created_by_id=admin.id,
        )
        database.add_all(
            [
                team_one,
                team_two,
                shift_one,
                shift_two,
            ]
        )
        database.flush()
        employee_one = AttendanceEmployee(
            employee_code="EMP001",
            full_name="Employee One",
            designation=(
                "Data Annotation Analyst"
            ),
            team_id=team_one.id,
            shift_id=shift_one.id,
            weekly_holidays=[],
            is_active=True,
            created_by_id=admin.id,
        )
        employee_two = AttendanceEmployee(
            employee_code="EMP002",
            full_name="Employee Two",
            designation=(
                "Data Annotation Analyst"
            ),
            team_id=team_one.id,
            shift_id=shift_one.id,
            weekly_holidays=[],
            is_active=True,
            created_by_id=admin.id,
        )
        employee_three = AttendanceEmployee(
            employee_code="EMP003",
            full_name="Employee Three",
            designation=(
                "Data Annotation Analyst"
            ),
            team_id=team_two.id,
            shift_id=shift_two.id,
            weekly_holidays=[],
            is_active=True,
            created_by_id=admin.id,
        )
        database.add_all(
            [
                employee_one,
                employee_two,
                employee_three,
            ]
        )
        database.flush()
        records = [
            AttendanceRecord(
                employee_id=employee_one.id,
                attendance_date=date(
                    2026,
                    8,
                    8,
                ),
                team_id=team_one.id,
                shift_id=shift_one.id,
                status="present",
                note=None,
                recorded_by_id=admin.id,
            ),
            AttendanceRecord(
                employee_id=employee_two.id,
                attendance_date=date(
                    2026,
                    8,
                    8,
                ),
                team_id=team_one.id,
                shift_id=shift_one.id,
                status="weekly_holiday",
                note=None,
                recorded_by_id=admin.id,
            ),
            AttendanceRecord(
                employee_id=employee_one.id,
                attendance_date=date(
                    2026,
                    8,
                    9,
                ),
                team_id=team_one.id,
                shift_id=shift_one.id,
                status="absent",
                note=None,
                recorded_by_id=admin.id,
            ),
            AttendanceRecord(
                employee_id=employee_two.id,
                attendance_date=date(
                    2026,
                    8,
                    9,
                ),
                team_id=team_one.id,
                shift_id=shift_one.id,
                status="on_leave",
                note=None,
                recorded_by_id=admin.id,
            ),
            AttendanceRecord(
                employee_id=employee_three.id,
                attendance_date=date(
                    2026,
                    8,
                    9,
                ),
                team_id=team_two.id,
                shift_id=shift_two.id,
                status="present",
                note=None,
                recorded_by_id=admin.id,
            ),
        ]
        database.add_all(
            records
        )
        database.commit()
        return {
            "team_one_id":
                team_one.id,
            "team_two_id":
                team_two.id,
            "shift_one_id":
                shift_one.id,
            "shift_two_id":
                shift_two.id,
            "employee_one_id":
                employee_one.id,
        }
def test_analytics_requires_authentication():
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/analytics",
            params={
                "date_from":
                    "2026-08-08",
                "date_to":
                    "2026-08-09",
            },
        )
    assert response.status_code == 401
def test_analytics_calculates_summary_and_rate():
    headers = create_admin_headers()
    seed_analytics_data()
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/analytics",
            headers=headers,
            params={
                "date_from":
                    "2026-08-08",
                "date_to":
                    "2026-08-09",
            },
        )
    assert response.status_code == 200
    body = response.json()
    summary = body["summary"]
    assert summary[
        "total_records"
    ] == 5
    assert summary[
        "working_day_records"
    ] == 4
    assert summary["present"] == 2
    assert summary["absent"] == 1
    assert summary["on_leave"] == 1
    assert summary[
        "weekly_holiday"
    ] == 1
    assert summary[
        "attendance_rate"
    ] == 50.0
def test_weekly_holiday_is_excluded_from_rate():
    headers = create_admin_headers()
    data = seed_analytics_data()
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/analytics",
            headers=headers,
            params={
                "date_from":
                    "2026-08-08",
                "date_to":
                    "2026-08-08",
                "team_id":
                    data["team_one_id"],
            },
        )
    assert response.status_code == 200
    summary = (
        response.json()["summary"]
    )
    assert summary[
        "total_records"
    ] == 2
    assert summary[
        "working_day_records"
    ] == 1
    assert summary["present"] == 1
    assert summary[
        "weekly_holiday"
    ] == 1
    assert summary[
        "attendance_rate"
    ] == 100.0
def test_analytics_filters_team_and_shift():
    headers = create_admin_headers()
    data = seed_analytics_data()
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/analytics",
            headers=headers,
            params={
                "date_from":
                    "2026-08-08",
                "date_to":
                    "2026-08-09",
                "team_id":
                    data["team_two_id"],
                "shift_id":
                    data["shift_two_id"],
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"][
        "total_records"
    ] == 1
    assert body["summary"][
        "present"
    ] == 1
    assert len(
        body["teams"]
    ) == 1
    assert (
        body["teams"][0]
        ["team_name"]
        == "CVAT"
    )
    assert len(
        body["shifts"]
    ) == 1
    assert (
        body["shifts"][0]
        ["shift_name"]
        == "Morning"
    )
def test_analytics_returns_daily_and_employee_breakdown():
    headers = create_admin_headers()
    seed_analytics_data()
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/analytics",
            headers=headers,
            params={
                "date_from":
                    "2026-08-08",
                "date_to":
                    "2026-08-09",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert len(
        body["daily_trend"]
    ) == 2
    assert (
        body["daily_trend"][0]
        ["attendance_date"]
        == "2026-08-08"
    )
    assert (
        body["daily_trend"][0]
        ["attendance_rate"]
        == 100.0
    )
    assert len(
        body["employees"]
    ) == 3
    employee_one = next(
        item
        for item in body[
            "employees"
        ]
        if item["employee_code"]
        == "EMP001"
    )
    assert (
        employee_one[
            "total_records"
        ]
        == 2
    )
    assert (
        employee_one["present"]
        == 1
    )
    assert (
        employee_one["absent"]
        == 1
    )
    assert (
        employee_one[
            "attendance_rate"
        ]
        == 50.0
    )
def test_analytics_empty_range_returns_zero_summary():
    headers = create_admin_headers()
    seed_analytics_data()
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/analytics",
            headers=headers,
            params={
                "date_from":
                    "2026-07-01",
                "date_to":
                    "2026-07-02",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"][
        "total_records"
    ] == 0
    assert body["summary"][
        "attendance_rate"
    ] == 0.0
    assert body[
        "daily_trend"
    ] == []
    assert body[
        "employees"
    ] == []
def test_analytics_rejects_invalid_date_range():
    headers = create_admin_headers()
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/analytics",
            headers=headers,
            params={
                "date_from":
                    "2026-08-10",
                "date_to":
                    "2026-08-01",
            },
        )
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == (
            "date_from cannot be later "
            "than date_to."
        )
    )
def test_analytics_uses_historical_snapshot_names():
    headers = create_admin_headers()
    data = seed_analytics_data()
    with TestingSessionLocal() as database:
        record = (
            database.query(
                AttendanceRecord
            )
            .filter(
                AttendanceRecord
                .employee_id
                == data[
                    "employee_one_id"
                ]
            )
            .first()
        )
        assert record is not None
        database.add(
            AttendanceRecordSnapshot(
                attendance_record_id=(
                    record.id
                ),
                employee_code="OLD001",
                full_name="Historical Name",
                designation=(
                    "Historical Designation"
                ),
                team_name="Historical Team",
                shift_name="Historical Shift",
            )
        )
        database.commit()
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/analytics",
            headers=headers,
            params={
                "date_from":
                    "2026-08-08",
                "date_to":
                    "2026-08-08",
            },
        )
    assert response.status_code == 200
    historical = next(
        item
        for item in response.json()[
            "employees"
        ]
        if item[
            "employee_code"
        ] == "OLD001"
    )
    assert (
        historical["full_name"]
        == "Historical Name"
    )
    assert (
        historical["team_name"]
        == "Historical Team"
    )
