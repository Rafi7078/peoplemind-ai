
from collections.abc import Generator
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import (
    create_engine,
    func,
    select,
)
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
    email = "daily-admin@example.com"
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
def create_foundation(
    *,
    employee_count: int = 2,
) -> tuple[int, int, list[int]]:
    with TestingSessionLocal() as database:
        admin = database.scalar(
            select(User)
        )
        assert admin is not None
        team = AttendanceTeam(
            name="Labelmaster",
            description=None,
            status="active",
            created_by_id=admin.id,
        )
        shift = AttendanceShift(
            name="Night",
            description=None,
            status="active",
            created_by_id=admin.id,
        )
        database.add_all(
            [team, shift]
        )
        database.flush()
        employees = []
        for index in range(
            1,
            employee_count + 1,
        ):
            employee = (
                AttendanceEmployee(
                    employee_code=(
                        f"EMP{index:03d}"
                    ),
                    full_name=(
                        f"Employee {index}"
                    ),
                    designation=(
                        "Data Annotation Analyst"
                    ),
                    team_id=team.id,
                    shift_id=shift.id,
                    weekly_holidays=(
                        ["Monday", "Tuesday"]
                        if index == 1
                        else []
                    ),
                    is_active=True,
                    created_by_id=admin.id,
                )
            )
            database.add(employee)
            employees.append(employee)
        database.commit()
        return (
            team.id,
            shift.id,
            [
                employee.id
                for employee in employees
            ],
        )
def test_daily_roster_requires_authentication():
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/daily/roster",
            params={
                "attendance_date":
                    "2026-08-10",
                "team_id": 1,
                "shift_id": 1,
            },
        )
    assert response.status_code == 401
def test_weekly_holiday_is_suggested():
    headers = create_admin_headers()
    team_id, shift_id, _ = (
        create_foundation()
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/daily/roster",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-10",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert (
        body["items"][0]
        ["suggested_status"]
        == "weekly_holiday"
    )
def test_non_holiday_defaults_to_present():
    headers = create_admin_headers()
    team_id, shift_id, _ = (
        create_foundation()
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/daily/roster",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert response.status_code == 200
    assert (
        response.json()["items"][0]
        ["suggested_status"]
        == "present"
    )
def test_submit_daily_attendance_and_summary():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation()
    with TestClient(app) as client:
        response = client.post(
            "/api/attendance/daily",
            headers=headers,
            json={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
                "entries": [
                    {
                        "employee_id":
                            employee_ids[0],
                        "status":
                            "present",
                    },
                    {
                        "employee_id":
                            employee_ids[1],
                        "status":
                            "absent",
                        "note":
                            "No attendance reported.",
                    },
                ],
            },
        )
    assert response.status_code == 200
    summary = (
        response.json()["summary"]
    )
    assert summary == {
        "total_members": 2,
        "present": 1,
        "absent": 1,
        "on_leave": 0,
        "weekly_holiday": 0,
    }
def test_incomplete_roster_is_rejected():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation()
    with TestClient(app) as client:
        response = client.post(
            "/api/attendance/daily",
            headers=headers,
            json={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
                "entries": [
                    {
                        "employee_id":
                            employee_ids[0],
                        "status":
                            "present",
                    },
                ],
            },
        )
    assert response.status_code == 409
def test_duplicate_employee_entry_is_rejected():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/attendance/daily",
            headers=headers,
            json={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
                "entries": [
                    {
                        "employee_id":
                            employee_ids[0],
                        "status":
                            "present",
                    },
                    {
                        "employee_id":
                            employee_ids[0],
                        "status":
                            "absent",
                    },
                ],
            },
        )
    assert response.status_code == 422
def test_resubmit_updates_without_duplicate():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    payload = {
        "attendance_date":
            "2026-08-12",
        "team_id": team_id,
        "shift_id": shift_id,
        "entries": [
            {
                "employee_id":
                    employee_ids[0],
                "status": "present",
            },
        ],
    }
    with TestClient(app) as client:
        first = client.post(
            "/api/attendance/daily",
            headers=headers,
            json=payload,
        )
        payload["entries"][0][
            "status"
        ] = "on_leave"
        second = client.post(
            "/api/attendance/daily",
            headers=headers,
            json=payload,
        )
    assert first.status_code == 200
    assert second.status_code == 200
    with TestingSessionLocal() as database:
        count = database.scalar(
            select(
                func.count(
                    AttendanceRecord.id
                )
            )
        )
        record = database.scalar(
            select(
                AttendanceRecord
            )
        )
    assert count == 1
    assert record is not None
    assert record.status == "on_leave"
def test_roster_returns_saved_status():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    with TestClient(app) as client:
        save_response = client.post(
            "/api/attendance/daily",
            headers=headers,
            json={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
                "entries": [
                    {
                        "employee_id":
                            employee_ids[0],
                        "status":
                            "absent",
                        "note":
                            "Confirmed absent",
                    },
                ],
            },
        )
        roster_response = client.get(
            "/api/attendance/daily/roster",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert save_response.status_code == 200
    assert roster_response.status_code == 200
    item = (
        roster_response.json()
        ["items"][0]
    )
    assert (
        item["saved_status"]
        == "absent"
    )
    assert (
        item["note"]
        == "Confirmed absent"
    )
def test_attendance_record_keeps_team_shift_snapshot():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/attendance/daily",
            headers=headers,
            json={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
                "entries": [
                    {
                        "employee_id":
                            employee_ids[0],
                        "status":
                            "present",
                    },
                ],
            },
        )
    assert response.status_code == 200
    with TestingSessionLocal() as database:
        record = database.scalar(
            select(
                AttendanceRecord
            )
        )
    assert record is not None
    assert record.team_id == team_id
    assert record.shift_id == shift_id
def test_empty_roster_cannot_be_submitted():
    headers = create_admin_headers()
    with TestingSessionLocal() as database:
        admin = database.scalar(
            select(User)
        )
        assert admin is not None
        team = AttendanceTeam(
            name="QA",
            status="active",
            created_by_id=admin.id,
        )
        shift = AttendanceShift(
            name="Evening",
            status="active",
            created_by_id=admin.id,
        )
        database.add_all(
            [team, shift]
        )
        database.commit()
        team_id = team.id
        shift_id = shift.id
    with TestClient(app) as client:
        response = client.post(
            "/api/attendance/daily",
            headers=headers,
            json={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
                "entries": [
                    {
                        "employee_id": 999,
                        "status":
                            "present",
                    },
                ],
            },
        )
    assert response.status_code == 409
def test_note_is_trimmed_and_saved():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/attendance/daily",
            headers=headers,
            json={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
                "entries": [
                    {
                        "employee_id":
                            employee_ids[0],
                        "status":
                            "on_leave",
                        "note":
                            "  Casual leave  ",
                    },
                ],
            },
        )
    assert response.status_code == 200
    assert (
        response.json()
        ["records"][0]["note"]
        == "Casual leave"
    )
def test_invalid_team_returns_404():
    headers = create_admin_headers()
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/daily/roster",
            headers=headers,
            params={
                "attendance_date":
                    str(date(
                        2026,
                        8,
                        12,
                    )),
                "team_id": 999,
                "shift_id": 999,
            },
        )
    assert response.status_code == 404
