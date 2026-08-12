from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool
from backend.app.core.security import (
    hash_password,
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
from backend.app.models.user_attendance_scope import (
    UserAttendanceScope,
)
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
def seed_access_data() -> dict[str, int]:
    with TestingSessionLocal() as database:
        admin = User(
            email="admin@example.com",
            hashed_password=hash_password(
                "AdminPassword123!"
            ),
            is_active=True,
            is_admin=True,
        )
        label_night_user = User(
            email="labelnight@example.com",
            hashed_password=hash_password(
                "LabelNightPassword123!"
            ),
            is_active=True,
            is_admin=False,
        )
        cvat_user = User(
            email="cvat@example.com",
            hashed_password=hash_password(
                "CvatPassword123!"
            ),
            is_active=True,
            is_admin=False,
        )
        database.add_all(
            [
                admin,
                label_night_user,
                cvat_user,
            ]
        )
        database.flush()
        labelmaster = AttendanceTeam(
            name="Labelmaster",
            status="active",
            created_by_id=admin.id,
        )
        cvat = AttendanceTeam(
            name="CVAT",
            status="active",
            created_by_id=admin.id,
        )
        night = AttendanceShift(
            name="Night",
            status="active",
            created_by_id=admin.id,
        )
        morning = AttendanceShift(
            name="Morning",
            status="active",
            created_by_id=admin.id,
        )
        evening = AttendanceShift(
            name="Evening",
            status="active",
            created_by_id=admin.id,
        )
        database.add_all(
            [
                labelmaster,
                cvat,
                night,
                morning,
                evening,
            ]
        )
        database.flush()
        label_employee = (
            AttendanceEmployee(
                employee_code="EMP023",
                full_name="Salman",
                designation=(
                    "Data Annotation Analyst"
                ),
                team_id=labelmaster.id,
                shift_id=night.id,
                weekly_holidays=[],
                is_active=True,
                created_by_id=admin.id,
            )
        )
        label_teammate = (
            AttendanceEmployee(
                employee_code="EMP024",
                full_name="Pritom",
                designation=(
                    "Data Annotation Analyst"
                ),
                team_id=labelmaster.id,
                shift_id=night.id,
                weekly_holidays=[],
                is_active=True,
                created_by_id=admin.id,
            )
        )
        cvat_morning = (
            AttendanceEmployee(
                employee_code="CVAT001",
                full_name="CVAT Morning",
                designation=(
                    "Data Annotation Analyst"
                ),
                team_id=cvat.id,
                shift_id=morning.id,
                weekly_holidays=[],
                is_active=True,
                created_by_id=admin.id,
            )
        )
        cvat_evening = (
            AttendanceEmployee(
                employee_code="CVAT002",
                full_name="CVAT Evening",
                designation=(
                    "Data Annotation Analyst"
                ),
                team_id=cvat.id,
                shift_id=evening.id,
                weekly_holidays=[],
                is_active=True,
                created_by_id=admin.id,
            )
        )
        database.add_all(
            [
                label_employee,
                label_teammate,
                cvat_morning,
                cvat_evening,
            ]
        )
        database.flush()
        database.add_all(
            [
                UserAttendanceScope(
                    user_id=label_night_user.id,
                    team_id=labelmaster.id,
                    shift_id=night.id,
                ),
                UserAttendanceScope(
                    user_id=cvat_user.id,
                    team_id=cvat.id,
                    shift_id=None,
                ),
            ]
        )
        database.commit()
        return {
            "labelmaster_id":
                labelmaster.id,
            "cvat_id":
                cvat.id,
            "night_id":
                night.id,
            "morning_id":
                morning.id,
            "evening_id":
                evening.id,
            "label_employee_id":
                label_employee.id,
            "label_teammate_id":
                label_teammate.id,
            "cvat_morning_id":
                cvat_morning.id,
            "cvat_evening_id":
                cvat_evening.id,
        }
def login(
    email: str,
    password: str,
) -> dict[str, str]:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            data={
                "username": email,
                "password": password,
            },
        )
    assert response.status_code == 200
    return {
        "Authorization":
            "Bearer "
            + response.json()[
                "access_token"
            ]
    }
def test_attendance_account_can_login():
    seed_access_data()
    headers = login(
        "labelnight@example.com",
        "LabelNightPassword123!",
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/auth/me",
            headers=headers,
        )
    assert response.status_code == 200
    assert (
        response.json()["is_admin"]
        is False
    )
def test_attendance_account_cannot_access_admin_api():
    seed_access_data()
    headers = login(
        "labelnight@example.com",
        "LabelNightPassword123!",
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/teams",
            headers=headers,
        )
    assert response.status_code == 403
def test_fixed_shift_account_reads_own_scope():
    data = seed_access_data()
    headers = login(
        "labelnight@example.com",
        "LabelNightPassword123!",
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/daily/access",
            headers=headers,
        )
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "attendance"
    assert (
        body["scope_type"]
        == "team_shift"
    )
    assert (
        body["team_id"]
        == data["labelmaster_id"]
    )
    assert (
        body["shift_id"]
        == data["night_id"]
    )
    assert len(
        body["allowed_shifts"]
    ) == 1
def test_fixed_shift_account_cannot_access_other_shift():
    data = seed_access_data()
    headers = login(
        "labelnight@example.com",
        "LabelNightPassword123!",
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/daily/roster",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id":
                    data["labelmaster_id"],
                "shift_id":
                    data["morning_id"],
            },
        )
    assert response.status_code == 403
def test_team_account_gets_dynamic_team_shifts():
    data = seed_access_data()
    headers = login(
        "cvat@example.com",
        "CvatPassword123!",
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/daily/access",
            headers=headers,
        )
    assert response.status_code == 200
    body = response.json()
    assert body["scope_type"] == "team"
    assert body["team_id"] == data["cvat_id"]
    assert body["shift_id"] is None
    shift_ids = {
        item["id"]
        for item in body[
            "allowed_shifts"
        ]
    }
    assert shift_ids == {
        data["morning_id"],
        data["evening_id"],
    }
def test_team_account_can_load_allowed_shift():
    data = seed_access_data()
    headers = login(
        "cvat@example.com",
        "CvatPassword123!",
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/daily/roster",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id":
                    data["cvat_id"],
                "shift_id":
                    data["morning_id"],
            },
        )
    assert response.status_code == 200
    assert (
        response.json()["total_members"]
        == 1
    )
def test_team_account_cannot_access_other_team():
    data = seed_access_data()
    headers = login(
        "cvat@example.com",
        "CvatPassword123!",
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/attendance/daily/roster",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-12",
                "team_id":
                    data["labelmaster_id"],
                "shift_id":
                    data["night_id"],
            },
        )
    assert response.status_code == 403
def test_attendance_account_submits_once_and_admin_can_correct():
    data = seed_access_data()
    attendance_headers = login(
        "labelnight@example.com",
        "LabelNightPassword123!",
    )
    admin_headers = login(
        "admin@example.com",
        "AdminPassword123!",
    )
    payload = {
        "attendance_date":
            "2026-08-12",
        "team_id":
            data["labelmaster_id"],
        "shift_id":
            data["night_id"],
        "submitted_by_employee_id":
            data["label_employee_id"],
        "entries": [
            {
                "employee_id":
                    data["label_employee_id"],
                "status": "present",
                "note": None,
            },
            {
                "employee_id":
                    data["label_teammate_id"],
                "status": "present",
                "note": None,
            },
        ],
    }
    with TestClient(app) as client:
        first = client.post(
            "/api/attendance/daily",
            headers=attendance_headers,
            json=payload,
        )
        second = client.post(
            "/api/attendance/daily",
            headers=attendance_headers,
            json=payload,
        )
        payload["entries"][1][
            "status"
        ] = "absent"
        admin_update = client.post(
            "/api/attendance/daily",
            headers=admin_headers,
            json=payload,
        )
    assert first.status_code == 200
    assert second.status_code == 409
    assert admin_update.status_code == 200
    assert (
        admin_update.json()[
            "summary"
        ]["absent"]
        == 1
    )
def test_attendance_account_requires_actual_submitter():
    data = seed_access_data()
    headers = login(
        "labelnight@example.com",
        "LabelNightPassword123!",
    )
    payload = {
        "attendance_date":
            "2026-08-13",
        "team_id":
            data["labelmaster_id"],
        "shift_id":
            data["night_id"],
        "entries": [
            {
                "employee_id":
                    data["label_employee_id"],
                "status": "present",
                "note": None,
            },
            {
                "employee_id":
                    data["label_teammate_id"],
                "status": "present",
                "note": None,
            },
        ],
    }
    with TestClient(app) as client:
        response = client.post(
            "/api/attendance/daily",
            headers=headers,
            json=payload,
        )
    assert response.status_code == 422
    assert (
        "Select the employee"
        in response.json()["detail"]
    )
def test_submitter_must_belong_to_same_roster():
    data = seed_access_data()
    headers = login(
        "labelnight@example.com",
        "LabelNightPassword123!",
    )
    payload = {
        "attendance_date":
            "2026-08-13",
        "team_id":
            data["labelmaster_id"],
        "shift_id":
            data["night_id"],
        "submitted_by_employee_id":
            data["cvat_morning_id"],
        "entries": [
            {
                "employee_id":
                    data["label_employee_id"],
                "status": "present",
                "note": None,
            },
            {
                "employee_id":
                    data["label_teammate_id"],
                "status": "present",
                "note": None,
            },
        ],
    }
    with TestClient(app) as client:
        response = client.post(
            "/api/attendance/daily",
            headers=headers,
            json=payload,
        )
    assert response.status_code == 422
    assert (
        "must belong to this team and shift"
        in response.json()["detail"]
    )
def test_submission_audit_snapshots_actual_submitter():
    data = seed_access_data()
    headers = login(
        "labelnight@example.com",
        "LabelNightPassword123!",
    )
    payload = {
        "attendance_date":
            "2026-08-13",
        "team_id":
            data["labelmaster_id"],
        "shift_id":
            data["night_id"],
        "submitted_by_employee_id":
            data["label_employee_id"],
        "entries": [
            {
                "employee_id":
                    data["label_employee_id"],
                "status": "present",
                "note": None,
            },
            {
                "employee_id":
                    data["label_teammate_id"],
                "status": "present",
                "note": None,
            },
        ],
    }
    with TestClient(app) as client:
        submitted = client.post(
            "/api/attendance/daily",
            headers=headers,
            json=payload,
        )
        roster = client.get(
            "/api/attendance/daily/roster",
            headers=headers,
            params={
                "attendance_date":
                    "2026-08-13",
                "team_id":
                    data["labelmaster_id"],
                "shift_id":
                    data["night_id"],
            },
        )
    assert submitted.status_code == 200
    assert roster.status_code == 200
    audit = roster.json()[
        "submission_audit"
    ]
    assert audit is not None
    assert (
        audit["submitted_account_email"]
        == "labelnight@example.com"
    )
    assert (
        audit["submitted_by_employee_id"]
        == data["label_employee_id"]
    )
    assert (
        audit["submitted_by_employee_code"]
        == "EMP023"
    )
    assert (
        audit["submitted_by_employee_name"]
        == "Salman"
    )
def test_admin_correction_preserves_original_submitter():
    data = seed_access_data()
    attendance_headers = login(
        "labelnight@example.com",
        "LabelNightPassword123!",
    )
    admin_headers = login(
        "admin@example.com",
        "AdminPassword123!",
    )
    payload = {
        "attendance_date":
            "2026-08-13",
        "team_id":
            data["labelmaster_id"],
        "shift_id":
            data["night_id"],
        "submitted_by_employee_id":
            data["label_employee_id"],
        "entries": [
            {
                "employee_id":
                    data["label_employee_id"],
                "status": "present",
                "note": None,
            },
            {
                "employee_id":
                    data["label_teammate_id"],
                "status": "present",
                "note": None,
            },
        ],
    }
    with TestClient(app) as client:
        first = client.post(
            "/api/attendance/daily",
            headers=attendance_headers,
            json=payload,
        )
        assert first.status_code == 200
        payload["entries"][1][
            "status"
        ] = "absent"
        corrected = client.post(
            "/api/attendance/daily",
            headers=admin_headers,
            json=payload,
        )
        assert corrected.status_code == 200
        roster = client.get(
            "/api/attendance/daily/roster",
            headers=admin_headers,
            params={
                "attendance_date":
                    "2026-08-13",
                "team_id":
                    data["labelmaster_id"],
                "shift_id":
                    data["night_id"],
            },
        )
    assert roster.status_code == 200
    audit = roster.json()[
        "submission_audit"
    ]
    assert (
        audit["submitted_account_email"]
        == "labelnight@example.com"
    )
    assert (
        audit["submitted_by_employee_code"]
        == "EMP023"
    )
    assert (
        audit["submitted_by_employee_name"]
        == "Salman"
    )
    assert (
        audit["last_updated_account_email"]
        == "admin@example.com"
    )
def test_admin_can_submit_without_employee_submitter():
    data = seed_access_data()
    admin_headers = login(
        "admin@example.com",
        "AdminPassword123!",
    )
    payload = {
        "attendance_date":
            "2026-08-13",
        "team_id":
            data["labelmaster_id"],
        "shift_id":
            data["night_id"],
        "entries": [
            {
                "employee_id":
                    data["label_employee_id"],
                "status": "present",
                "note": None,
            },
            {
                "employee_id":
                    data["label_teammate_id"],
                "status": "present",
                "note": None,
            },
        ],
    }
    with TestClient(app) as client:
        response = client.post(
            "/api/attendance/daily",
            headers=admin_headers,
            json=payload,
        )
    assert response.status_code == 200
    audit = response.json()[
        "submission_audit"
    ]
    assert (
        audit["submitted_account_email"]
        == "admin@example.com"
    )
    assert (
        audit["submitted_by_employee_id"]
        is None
    )
    assert (
        audit["submitted_by_employee_code"]
        is None
    )
    assert (
        audit["submitted_by_employee_name"]
        is None
    )
