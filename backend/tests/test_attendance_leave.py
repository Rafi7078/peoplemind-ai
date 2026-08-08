
from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import (
    create_engine,
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
    email = "leave-admin@example.com"
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
def create_employee(
    *,
    weekly_holidays: list[str]
    | None = None,
) -> tuple[int, int, int]:
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
        employee = AttendanceEmployee(
            employee_code="EMP001",
            full_name="Employee One",
            designation=(
                "Data Annotation Analyst"
            ),
            team_id=team.id,
            shift_id=shift.id,
            weekly_holidays=(
                weekly_holidays or []
            ),
            is_active=True,
            created_by_id=admin.id,
        )
        database.add(employee)
        database.commit()
        return (
            employee.id,
            team.id,
            shift.id,
        )
def create_leave(
    client: TestClient,
    headers: dict[str, str],
    *,
    employee_id: int,
    leave_status: str = "pending",
    from_date: str = "2026-08-10",
    to_date: str = "2026-08-12",
):
    return client.post(
        "/api/attendance/leaves",
        headers=headers,
        json={
            "employee_id": employee_id,
            "leave_type": "casual",
            "from_date": from_date,
            "to_date": to_date,
            "reason": "Family matter",
            "status": leave_status,
        },
    )
def test_leave_requires_authentication():
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/leaves"
        )
    assert response.status_code == 401
def test_create_approved_leave():
    headers = create_admin_headers()
    employee_id, _, _ = (
        create_employee()
    )
    with TestClient(app) as client:
        response = create_leave(
            client,
            headers,
            employee_id=employee_id,
            leave_status="approved",
        )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "approved"
    assert body["leave_type"] == "casual"
    assert body["approved_by_id"] is not None
def test_invalid_leave_range_is_rejected():
    headers = create_admin_headers()
    employee_id, _, _ = (
        create_employee()
    )
    with TestClient(app) as client:
        response = create_leave(
            client,
            headers,
            employee_id=employee_id,
            from_date="2026-08-15",
            to_date="2026-08-10",
        )
    assert response.status_code == 422
def test_overlapping_leave_is_rejected():
    headers = create_admin_headers()
    employee_id, _, _ = (
        create_employee()
    )
    with TestClient(app) as client:
        first = create_leave(
            client,
            headers,
            employee_id=employee_id,
        )
        second = create_leave(
            client,
            headers,
            employee_id=employee_id,
            from_date="2026-08-12",
            to_date="2026-08-14",
        )
    assert first.status_code == 201
    assert second.status_code == 409
def test_cancelled_leave_no_longer_blocks_overlap():
    headers = create_admin_headers()
    employee_id, _, _ = (
        create_employee()
    )
    with TestClient(app) as client:
        first = create_leave(
            client,
            headers,
            employee_id=employee_id,
        )
        assert first.status_code == 201
        leave_id = first.json()["id"]
        cancelled = client.patch(
            f"/api/attendance/leaves/{leave_id}",
            headers=headers,
            json={
                "status": "cancelled",
            },
        )
        second = create_leave(
            client,
            headers,
            employee_id=employee_id,
        )
    assert cancelled.status_code == 200
    assert second.status_code == 201
def test_leave_list_filters_work():
    headers = create_admin_headers()
    employee_id, _, _ = (
        create_employee()
    )
    with TestClient(app) as client:
        created = create_leave(
            client,
            headers,
            employee_id=employee_id,
            leave_status="approved",
        )
        response = client.get(
            "/api/attendance/leaves",
            headers=headers,
            params={
                "status": "approved",
                "date_from":
                    "2026-08-11",
                "date_to":
                    "2026-08-11",
            },
        )
    assert created.status_code == 201
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert (
        body["items"][0]["status"]
        == "approved"
    )
def test_pending_leave_can_be_approved():
    headers = create_admin_headers()
    employee_id, _, _ = (
        create_employee()
    )
    with TestClient(app) as client:
        created = create_leave(
            client,
            headers,
            employee_id=employee_id,
        )
        leave_id = created.json()["id"]
        response = client.patch(
            f"/api/attendance/leaves/{leave_id}",
            headers=headers,
            json={
                "status": "approved",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["approved_by_id"] is not None
def test_approved_leave_suggests_on_leave():
    headers = create_admin_headers()
    (
        employee_id,
        team_id,
        shift_id,
    ) = create_employee()
    with TestClient(app) as client:
        created = create_leave(
            client,
            headers,
            employee_id=employee_id,
            leave_status="approved",
        )
        response = client.get(
            "/api/attendance/daily/roster",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-11",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert created.status_code == 201
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert (
        item["suggested_status"]
        == "on_leave"
    )
    assert (
        item["approved_leave_type"]
        == "casual"
    )
    assert (
        item["approved_leave_reason"]
        == "Family matter"
    )
def test_weekly_holiday_has_priority_over_leave():
    headers = create_admin_headers()
    (
        employee_id,
        team_id,
        shift_id,
    ) = create_employee(
        weekly_holidays=["Tuesday"]
    )
    with TestClient(app) as client:
        created = create_leave(
            client,
            headers,
            employee_id=employee_id,
            leave_status="approved",
        )
        response = client.get(
            "/api/attendance/daily/roster",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-11",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert created.status_code == 201
    assert response.status_code == 200
    assert (
        response.json()["items"][0]
        ["suggested_status"]
        == "weekly_holiday"
    )
def test_pending_leave_does_not_suggest_on_leave():
    headers = create_admin_headers()
    (
        employee_id,
        team_id,
        shift_id,
    ) = create_employee()
    with TestClient(app) as client:
        created = create_leave(
            client,
            headers,
            employee_id=employee_id,
            leave_status="pending",
        )
        response = client.get(
            "/api/attendance/daily/roster",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-11",
                "team_id": team_id,
                "shift_id": shift_id,
            },
        )
    assert created.status_code == 201
    assert response.status_code == 200
    assert (
        response.json()["items"][0]
        ["suggested_status"]
        == "present"
    )
