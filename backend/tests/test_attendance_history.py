
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


def test_csv_export_requires_authentication():
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/history/report.csv",
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id": 1,
                "shift_id": 1,
            },
        )
    assert response.status_code == 401
def test_csv_export_contains_report_and_summary():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=2
    )
    with TestClient(app) as client:
        saved = submit_report(
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
        response = client.get(
            "/api/attendance/history/report.csv",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert saved.status_code == 200
    assert response.status_code == 200
    assert (
        "text/csv"
        in response.headers[
            "content-type"
        ]
    )
    text = response.text
    assert "Attendance Report" in text
    assert "Labelmaster" in text
    assert "Night" in text
    assert "Total Members,2" in text
    assert "Present,1" in text
    assert "On Leave,1" in text
    assert "Leave Type" in text
    assert "Leave Reason" in text
    assert "Leave From" in text
    assert "Leave To" in text
    assert "Employee 1" in text
    assert "Employee 2" in text
def test_csv_export_has_attachment_filename():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    with TestClient(app) as client:
        saved = submit_report(
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
        response = client.get(
            "/api/attendance/history/report.csv",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert saved.status_code == 200
    assert response.status_code == 200
    disposition = (
        response.headers[
            "content-disposition"
        ]
    )
    assert "attachment" in disposition
    assert (
        "attendance_2026-08-12"
        in disposition
    )
def test_csv_export_neutralizes_formula_cells():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    with TestingSessionLocal() as database:
        employee = database.get(
            AttendanceEmployee,
            employee_ids[0],
        )
        assert employee is not None
        employee.full_name = "=2+2"
        database.commit()
    with TestClient(app) as client:
        saved = submit_report(
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
        response = client.get(
            "/api/attendance/history/report.csv",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert saved.status_code == 200
    assert response.status_code == 200
    assert "'=2+2" in response.text


def _create_approved_leave(
    *,
    employee_id: int,
    leave_type: str,
    from_date: str,
    to_date: str,
    reason: str | None,
) -> int:
    with TestingSessionLocal() as database:
        admin = database.scalar(
            select(User)
        )
        assert admin is not None
        leave = AttendanceLeave(
            employee_id=employee_id,
            leave_type=leave_type,
            from_date=date.fromisoformat(
                from_date
            ),
            to_date=date.fromisoformat(
                to_date
            ),
            reason=reason,
            status="approved",
            created_by_id=admin.id,
            approved_by_id=admin.id,
        )
        database.add(leave)
        database.commit()
        database.refresh(leave)
        return leave.id
def test_report_preserves_approved_leave_snapshot():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    leave_id = _create_approved_leave(
        employee_id=employee_ids[0],
        leave_type="annual",
        from_date="2026-08-12",
        to_date="2026-08-13",
        reason="Family trip",
    )
    with TestClient(app) as client:
        saved = submit_report(
            client,
            headers,
            attendance_date="2026-08-12",
            team_id=team_id,
            shift_id=shift_id,
            employee_ids=employee_ids,
            statuses=["on_leave"],
        )
        assert saved.status_code == 200
    with TestingSessionLocal() as database:
        snapshot = database.scalar(
            select(
                AttendanceRecordLeaveSnapshot
            )
        )
        assert snapshot is not None
        assert snapshot.leave_type == "annual"
        assert (
            snapshot.leave_reason
            == "Family trip"
        )
        leave = database.get(
            AttendanceLeave,
            leave_id,
        )
        assert leave is not None
        leave.leave_type = "sick"
        leave.reason = "Changed later"
        leave.status = "cancelled"
        database.commit()
    with TestClient(app) as client:
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
        csv_response = client.get(
            "/api/attendance/history/report.csv",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert response.status_code == 200
    employee = (
        response.json()["employees"][0]
    )
    assert employee["status"] == "on_leave"
    assert employee["leave_id"] == leave_id
    assert employee["leave_type"] == "annual"
    assert (
        employee["leave_reason"]
        == "Family trip"
    )
    assert (
        employee["leave_from_date"]
        == "2026-08-12"
    )
    assert (
        employee["leave_to_date"]
        == "2026-08-13"
    )
    assert csv_response.status_code == 200
    assert "Annual" in csv_response.text
    assert "Family trip" in csv_response.text
    assert "2026-08-12" in csv_response.text
    assert "2026-08-13" in csv_response.text
def test_report_backfills_legacy_leave_snapshot():
    headers = create_admin_headers()
    (
        team_id,
        shift_id,
        employee_ids,
    ) = create_foundation(
        employee_count=1
    )
    with TestClient(app) as client:
        saved = submit_report(
            client,
            headers,
            attendance_date="2026-08-14",
            team_id=team_id,
            shift_id=shift_id,
            employee_ids=employee_ids,
            statuses=["on_leave"],
        )
    assert saved.status_code == 200
    with TestingSessionLocal() as database:
        initial_snapshot = database.scalar(
            select(
                AttendanceRecordLeaveSnapshot
            )
        )
        assert initial_snapshot is None
    leave_id = _create_approved_leave(
        employee_id=employee_ids[0],
        leave_type="casual",
        from_date="2026-08-14",
        to_date="2026-08-14",
        reason="Personal work",
    )
    with TestClient(app) as client:
        first_report = client.get(
            "/api/attendance/history/report",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-14",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert first_report.status_code == 200
    first_employee = (
        first_report.json()
        ["employees"][0]
    )
    assert (
        first_employee["leave_type"]
        == "casual"
    )
    assert (
        first_employee["leave_reason"]
        == "Personal work"
    )
    with TestingSessionLocal() as database:
        snapshots = list(
            database.scalars(
                select(
                    AttendanceRecordLeaveSnapshot
                )
            ).all()
        )
        assert len(snapshots) == 1
        leave = database.get(
            AttendanceLeave,
            leave_id,
        )
        assert leave is not None
        leave.leave_type = "sick"
        leave.reason = "Later change"
        leave.status = "cancelled"
        database.commit()
    with TestClient(app) as client:
        second_report = client.get(
            "/api/attendance/history/report",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-14",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert second_report.status_code == 200
    second_employee = (
        second_report.json()
        ["employees"][0]
    )
    assert (
        second_employee["leave_type"]
        == "casual"
    )
    assert (
        second_employee["leave_reason"]
        == "Personal work"
    )
