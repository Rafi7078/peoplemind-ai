
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
        "attendance-admin@example.com"
    )
    with TestingSessionLocal() as database:
        user = User(
            email=email,
            hashed_password="not-used",
            is_active=True,
            is_admin=True,
        )
        database.add(user)
        database.commit()
    token = create_access_token(
        subject=email
    )
    return {
        "Authorization": (
            f"Bearer {token}"
        )
    }
def create_team(
    client: TestClient,
    headers: dict[str, str],
    name: str = "Labelmaster",
) -> dict:
    response = client.post(
        "/api/attendance/teams",
        headers=headers,
        json={
            "name": name,
            "description": (
                "Data annotation team"
            ),
            "status": "active",
        },
    )
    assert response.status_code == 201
    return response.json()
def create_shift(
    client: TestClient,
    headers: dict[str, str],
    name: str = "Morning",
) -> dict:
    response = client.post(
        "/api/attendance/shifts",
        headers=headers,
        json={
            "name": name,
            "status": "active",
        },
    )
    assert response.status_code == 201
    return response.json()
def create_employee(
    client: TestClient,
    headers: dict[str, str],
    *,
    team_id: int,
    shift_id: int,
    employee_code: str = "EMP001",
    full_name: str = "Abdullah",
) -> dict:
    response = client.post(
        "/api/attendance/employees",
        headers=headers,
        json={
            "employee_code":
                employee_code,
            "full_name": full_name,
            "designation": "Team Lead",
            "team_id": team_id,
            "shift_id": shift_id,
            "weekly_holidays": [
                "Friday",
                "Saturday",
            ],
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()
def test_attendance_requires_authentication():
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/teams"
        )
    assert response.status_code == 401
def test_admin_can_create_list_and_update_team():
    headers = create_admin_headers()
    with TestClient(app) as client:
        team = create_team(
            client,
            headers,
        )
        list_response = client.get(
            "/api/attendance/teams",
            headers=headers,
        )
        update_response = client.patch(
            (
                "/api/attendance/teams/"
                f"{team['id']}"
            ),
            headers=headers,
            json={
                "name":
                    "Labelmaster Team",
                "description":
                    "Updated team",
            },
        )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert update_response.status_code == 200
    assert (
        update_response.json()["name"]
        == "Labelmaster Team"
    )
def test_duplicate_team_name_is_rejected():
    headers = create_admin_headers()
    with TestClient(app) as client:
        create_team(
            client,
            headers,
        )
        response = client.post(
            "/api/attendance/teams",
            headers=headers,
            json={
                "name": "Labelmaster",
                "status": "active",
            },
        )
    assert response.status_code == 409
def test_admin_can_create_list_and_update_shift():
    headers = create_admin_headers()
    with TestClient(app) as client:
        shift = create_shift(
            client,
            headers,
        )
        list_response = client.get(
            "/api/attendance/shifts",
            headers=headers,
        )
        update_response = client.patch(
            (
                "/api/attendance/shifts/"
                f"{shift['id']}"
            ),
            headers=headers,
            json={
                "name": "Early Morning",
            },
        )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert update_response.status_code == 200
    assert (
        update_response.json()["name"]
        == "Early Morning"
    )
def test_duplicate_shift_name_is_rejected():
    headers = create_admin_headers()
    with TestClient(app) as client:
        create_shift(
            client,
            headers,
        )
        response = client.post(
            "/api/attendance/shifts",
            headers=headers,
            json={
                "name": "Morning",
                "status": "active",
            },
        )
    assert response.status_code == 409
def test_admin_can_create_employee():
    headers = create_admin_headers()
    with TestClient(app) as client:
        team = create_team(
            client,
            headers,
        )
        shift = create_shift(
            client,
            headers,
        )
        employee = create_employee(
            client,
            headers,
            team_id=team["id"],
            shift_id=shift["id"],
        )
    assert (
        employee["employee_code"]
        == "EMP001"
    )
    assert (
        employee["weekly_holidays"]
        == [
            "Friday",
            "Saturday",
        ]
    )
def test_duplicate_employee_code_is_rejected():
    headers = create_admin_headers()
    with TestClient(app) as client:
        team = create_team(
            client,
            headers,
        )
        shift = create_shift(
            client,
            headers,
        )
        create_employee(
            client,
            headers,
            team_id=team["id"],
            shift_id=shift["id"],
        )
        response = client.post(
            "/api/attendance/employees",
            headers=headers,
            json={
                "employee_code":
                    "EMP001",
                "full_name":
                    "Another Person",
                "designation":
                    "Analyst",
                "team_id": team["id"],
                "shift_id":
                    shift["id"],
                "weekly_holidays": [],
                "is_active": True,
            },
        )
    assert response.status_code == 409
def test_employee_list_supports_team_shift_and_active_filters():
    headers = create_admin_headers()
    with TestClient(app) as client:
        lm_team = create_team(
            client,
            headers,
            "Labelmaster",
        )
        qa_team = create_team(
            client,
            headers,
            "QA",
        )
        morning = create_shift(
            client,
            headers,
            "Morning",
        )
        night = create_shift(
            client,
            headers,
            "Night",
        )
        create_employee(
            client,
            headers,
            team_id=lm_team["id"],
            shift_id=morning["id"],
            employee_code="EMP001",
            full_name="Employee One",
        )
        second = create_employee(
            client,
            headers,
            team_id=qa_team["id"],
            shift_id=night["id"],
            employee_code="EMP002",
            full_name="Employee Two",
        )
        client.patch(
            (
                "/api/attendance/employees/"
                f"{second['id']}"
            ),
            headers=headers,
            json={
                "is_active": False,
            },
        )
        team_response = client.get(
            (
                "/api/attendance/employees"
                f"?team_id={lm_team['id']}"
            ),
            headers=headers,
        )
        shift_response = client.get(
            (
                "/api/attendance/employees"
                f"?shift_id={night['id']}"
            ),
            headers=headers,
        )
        active_response = client.get(
            (
                "/api/attendance/employees"
                "?is_active=true"
            ),
            headers=headers,
        )
    assert len(team_response.json()) == 1
    assert len(shift_response.json()) == 1
    assert len(active_response.json()) == 1
def test_employee_can_move_to_another_team_and_shift():
    headers = create_admin_headers()
    with TestClient(app) as client:
        first_team = create_team(
            client,
            headers,
            "Labelmaster",
        )
        second_team = create_team(
            client,
            headers,
            "QA",
        )
        morning = create_shift(
            client,
            headers,
            "Morning",
        )
        night = create_shift(
            client,
            headers,
            "Night",
        )
        employee = create_employee(
            client,
            headers,
            team_id=first_team["id"],
            shift_id=morning["id"],
        )
        response = client.patch(
            (
                "/api/attendance/employees/"
                f"{employee['id']}"
            ),
            headers=headers,
            json={
                "team_id":
                    second_team["id"],
                "shift_id":
                    night["id"],
            },
        )
    assert response.status_code == 200
    updated = response.json()
    assert (
        updated["team_id"]
        == second_team["id"]
    )
    assert (
        updated["shift_id"]
        == night["id"]
    )
def test_employee_can_be_deactivated():
    headers = create_admin_headers()
    with TestClient(app) as client:
        team = create_team(
            client,
            headers,
        )
        shift = create_shift(
            client,
            headers,
        )
        employee = create_employee(
            client,
            headers,
            team_id=team["id"],
            shift_id=shift["id"],
        )
        response = client.patch(
            (
                "/api/attendance/employees/"
                f"{employee['id']}"
            ),
            headers=headers,
            json={
                "is_active": False,
            },
        )
    assert response.status_code == 200
    assert (
        response.json()["is_active"]
        is False
    )
def test_weekly_holiday_duplicates_are_rejected():
    headers = create_admin_headers()
    with TestClient(app) as client:
        team = create_team(
            client,
            headers,
        )
        shift = create_shift(
            client,
            headers,
        )
        response = client.post(
            "/api/attendance/employees",
            headers=headers,
            json={
                "employee_code":
                    "EMP001",
                "full_name":
                    "Employee One",
                "designation":
                    "Analyst",
                "team_id": team["id"],
                "shift_id":
                    shift["id"],
                "weekly_holidays": [
                    "Friday",
                    "Friday",
                ],
            },
        )
    assert response.status_code == 422
def test_team_with_employees_cannot_be_deleted():
    headers = create_admin_headers()
    with TestClient(app) as client:
        team = create_team(
            client,
            headers,
        )
        shift = create_shift(
            client,
            headers,
        )
        create_employee(
            client,
            headers,
            team_id=team["id"],
            shift_id=shift["id"],
        )
        response = client.delete(
            (
                "/api/attendance/teams/"
                f"{team['id']}"
            ),
            headers=headers,
        )
    assert response.status_code == 409
def test_shift_with_employees_cannot_be_deleted():
    headers = create_admin_headers()
    with TestClient(app) as client:
        team = create_team(
            client,
            headers,
        )
        shift = create_shift(
            client,
            headers,
        )
        create_employee(
            client,
            headers,
            team_id=team["id"],
            shift_id=shift["id"],
        )
        response = client.delete(
            (
                "/api/attendance/shifts/"
                f"{shift['id']}"
            ),
            headers=headers,
        )
    assert response.status_code == 409
def test_employee_can_be_permanently_deleted():
    headers = create_admin_headers()
    with TestClient(app) as client:
        team = create_team(
            client,
            headers,
        )
        shift = create_shift(
            client,
            headers,
        )
        employee = create_employee(
            client,
            headers,
            team_id=team["id"],
            shift_id=shift["id"],
        )
        response = client.delete(
            (
                "/api/attendance/employees/"
                f"{employee['id']}"
            ),
            headers=headers,
        )
    assert response.status_code == 204
    with TestingSessionLocal() as database:
        count = database.scalar(
            select(
                func.count(
                    AttendanceEmployee.id
                )
            )
        )
    assert count == 0
def test_empty_team_and_shift_can_be_deleted():
    headers = create_admin_headers()
    with TestClient(app) as client:
        team = create_team(
            client,
            headers,
        )
        shift = create_shift(
            client,
            headers,
        )
        team_response = client.delete(
            (
                "/api/attendance/teams/"
                f"{team['id']}"
            ),
            headers=headers,
        )
        shift_response = client.delete(
            (
                "/api/attendance/shifts/"
                f"{shift['id']}"
            ),
            headers=headers,
        )
    assert team_response.status_code == 204
    assert shift_response.status_code == 204
    with TestingSessionLocal() as database:
        team_count = database.scalar(
            select(
                func.count(
                    AttendanceTeam.id
                )
            )
        )
        shift_count = database.scalar(
            select(
                func.count(
                    AttendanceShift.id
                )
            )
        )
    assert team_count == 0
    assert shift_count == 0
