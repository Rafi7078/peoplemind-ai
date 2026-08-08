
from collections.abc import Generator
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
        "history-admin@example.com"
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
            status="active",
            created_by_id=admin.id,
        )
        shift = AttendanceShift(
            name="Night",
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
                    weekly_holidays=[],
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
def submit_report(
    client: TestClient,
    headers: dict[str, str],
    *,
    attendance_date: str,
    team_id: int,
    shift_id: int,
    employee_ids: list[int],
    statuses: list[str],
):
    entries = []
    for employee_id, status in zip(
        employee_ids,
        statuses,
        strict=True,
    ):
        entries.append(
            {
                "employee_id":
                    employee_id,
                "status": status,
                "note": (
                    "Approved leave"
                    if status
                    == "on_leave"
                    else None
                ),
            }
        )
    return client.post(
        "/api/attendance/daily",
        headers=headers,
        json={
            "attendance_date":
                attendance_date,
            "team_id": team_id,
            "shift_id": shift_id,
            "entries": entries,
        },
    )
def test_history_requires_authentication():
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/history"
        )
    assert response.status_code == 401
def test_history_lists_saved_report_summary():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation()
    with TestClient(app) as client:
        save_response = submit_report(
            client,
            headers,
            attendance_date=(
                "2026-08-12"
            ),
            team_id=team_id,
            shift_id=shift_id,
            employee_ids=employee_ids,
            statuses=[
                "present",
                "on_leave",
            ],
        )
        history_response = client.get(
            "/api/attendance/history",
            headers=headers,
        )
    assert save_response.status_code == 200
    assert history_response.status_code == 200
    body = history_response.json()
    assert body["total_reports"] == 1
    item = body["items"][0]
    assert item["team_name"] == "Labelmaster"
    assert item["shift_name"] == "Night"
    assert item["summary"] == {
        "total_members": 2,
        "present": 1,
        "absent": 0,
        "on_leave": 1,
        "weekly_holiday": 0,
    }
def test_history_date_filters_work():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    with TestClient(app) as client:
        first = submit_report(
            client,
            headers,
            attendance_date=(
                "2026-08-12"
            ),
            team_id=team_id,
            shift_id=shift_id,
            employee_ids=employee_ids,
            statuses=["present"],
        )
        second = submit_report(
            client,
            headers,
            attendance_date=(
                "2026-08-13"
            ),
            team_id=team_id,
            shift_id=shift_id,
            employee_ids=employee_ids,
            statuses=["absent"],
        )
        response = client.get(
            "/api/attendance/history",
            headers=headers,
            params={
                "date_from":
                    "2026-08-13",
                "date_to":
                    "2026-08-13",
            },
        )
    assert first.status_code == 200
    assert second.status_code == 200
    assert response.status_code == 200
    body = response.json()
    assert body["total_reports"] == 1
    assert (
        body["items"][0]
        ["attendance_date"]
        == "2026-08-13"
    )
def test_report_returns_employee_details():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    with TestClient(app) as client:
        save_response = submit_report(
            client,
            headers,
            attendance_date=(
                "2026-08-12"
            ),
            team_id=team_id,
            shift_id=shift_id,
            employee_ids=employee_ids,
            statuses=["on_leave"],
        )
        response = client.get(
            "/api/attendance/history/report",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert save_response.status_code == 200
    assert response.status_code == 200
    body = response.json()
    assert (
        body["employees"][0]
        ["employee_code"]
        == "EMP001"
    )
    assert (
        body["employees"][0]
        ["full_name"]
        == "Employee 1"
    )
    assert (
        body["employees"][0]
        ["status"]
        == "on_leave"
    )
    assert (
        body["employees"][0]
        ["note"]
        == "Approved leave"
    )
def test_report_snapshot_survives_profile_changes():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    with TestClient(app) as client:
        save_response = submit_report(
            client,
            headers,
            attendance_date=(
                "2026-08-12"
            ),
            team_id=team_id,
            shift_id=shift_id,
            employee_ids=employee_ids,
            statuses=["present"],
        )
        assert save_response.status_code == 200
        with TestingSessionLocal() as database:
            employee = database.get(
                AttendanceEmployee,
                employee_ids[0],
            )
            team = database.get(
                AttendanceTeam,
                team_id,
            )
            shift = database.get(
                AttendanceShift,
                shift_id,
            )
            assert employee is not None
            assert team is not None
            assert shift is not None
            employee.full_name = (
                "Renamed Employee"
            )
            employee.designation = (
                "Changed Designation"
            )
            team.name = "Renamed Team"
            shift.name = "Renamed Shift"
            database.commit()
        response = client.get(
            "/api/attendance/history/report",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert (
        body["team_name"]
        == "Labelmaster"
    )
    assert (
        body["shift_name"]
        == "Night"
    )
    assert (
        body["employees"][0]
        ["full_name"]
        == "Employee 1"
    )
    assert (
        body["employees"][0]
        ["designation"]
        == "Data Annotation Analyst"
    )
def test_missing_report_returns_404():
    headers = create_admin_headers()
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/history/report",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id": 999,
                "shift_id": 999,
            },
        )
    assert response.status_code == 404
def test_resubmit_updates_record_but_keeps_one_snapshot():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    with TestClient(app) as client:
        first = submit_report(
            client,
            headers,
            attendance_date=(
                "2026-08-12"
            ),
            team_id=team_id,
            shift_id=shift_id,
            employee_ids=employee_ids,
            statuses=["present"],
        )
        second = submit_report(
            client,
            headers,
            attendance_date=(
                "2026-08-12"
            ),
            team_id=team_id,
            shift_id=shift_id,
            employee_ids=employee_ids,
            statuses=["absent"],
        )
        history_response = client.get(
            "/api/attendance/history",
            headers=headers,
        )
    assert first.status_code == 200
    assert second.status_code == 200
    assert (
        history_response.status_code
        == 200
    )
    body = history_response.json()
    assert body["total_reports"] == 1
    assert (
        body["items"][0]
        ["summary"]["absent"]
        == 1
    )
    with TestingSessionLocal() as database:
        snapshot_count = database.scalar(
            select(
                func.count(
                    AttendanceRecordSnapshot
                    .id
                )
            )
        )
    assert snapshot_count == 1
