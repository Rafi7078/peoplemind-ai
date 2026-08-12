from datetime import (
    datetime,
)
from pathlib import Path
import secrets
import string
from sqlalchemy import (
    func,
    select,
)
from backend.app.core.security import (
    hash_password,
)
from backend.app.db.database import (
    Base,
    SessionLocal,
    engine,
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
ACCOUNT_CONFIGS = [
    {
        "label": (
            "Labelmaster Early Morning"
        ),
        "email": (
            "labelmaster.early@example.com"
        ),
        "team": "Labelmaster",
        "shift": "Early Morning",
    },
    {
        "label": (
            "Labelmaster Morning"
        ),
        "email": (
            "labelmaster.morning@example.com"
        ),
        "team": "Labelmaster",
        "shift": "Morning",
    },
    {
        "label": (
            "Labelmaster Evening"
        ),
        "email": (
            "labelmaster.evening@example.com"
        ),
        "team": "Labelmaster",
        "shift": "Evening",
    },
    {
        "label": (
            "Labelmaster Night"
        ),
        "email": (
            "labelmaster.night@example.com"
        ),
        "team": "Labelmaster",
        "shift": "Night",
    },
    {
        "label": "CVAT",
        "email": (
            "cvat.attendance@example.com"
        ),
        "team": "CVAT",
        "shift": None,
    },
    {
        "label": "QA",
        "email": (
            "qa.attendance@example.com"
        ),
        "team": "QA",
        "shift": None,
    },
    {
        "label": "DevOps",
        "email": (
            "devops.attendance@example.com"
        ),
        "team": "DevOps",
        "shift": None,
    },
]
REQUIRED_SHIFTS = [
    "Early Morning",
    "Morning",
    "Evening",
    "Night",
]
def make_password() -> str:
    alphabet = (
        string.ascii_letters
        + string.digits
        + "!@#$%&*"
    )
    while True:
        password = "".join(
            secrets.choice(alphabet)
            for _ in range(18)
        )
        if (
            any(
                character.islower()
                for character in password
            )
            and any(
                character.isupper()
                for character in password
            )
            and any(
                character.isdigit()
                for character in password
            )
            and any(
                character in "!@#$%&*"
                for character in password
            )
        ):
            return password
def find_team(
    database,
    name: str,
):
    return database.scalar(
        select(
            AttendanceTeam
        ).where(
            func.lower(
                AttendanceTeam.name
            )
            == name.lower()
        )
    )
def find_shift(
    database,
    name: str,
):
    return database.scalar(
        select(
            AttendanceShift
        ).where(
            func.lower(
                AttendanceShift.name
            )
            == name.lower()
        )
    )
def ensure_team(
    database,
    *,
    name: str,
    admin_id: int,
):
    team = find_team(
        database,
        name,
    )
    if team is not None:
        return team, False
    team = AttendanceTeam(
        name=name,
        status="active",
        created_by_id=admin_id,
    )
    database.add(team)
    database.flush()
    return team, True
def ensure_shift(
    database,
    *,
    name: str,
    admin_id: int,
):
    shift = find_shift(
        database,
        name,
    )
    if shift is not None:
        return shift, False
    shift = AttendanceShift(
        name=name,
        status="active",
        created_by_id=admin_id,
    )
    database.add(shift)
    database.flush()
    return shift, True
def main() -> None:
    Base.metadata.create_all(
        bind=engine
    )
    credential_lines = [
        (
            "PEOPLEMIND AI - "
            "ATTENDANCE LOGIN ACCOUNTS"
        ),
        "=" * 55,
        "",
    ]
    with SessionLocal() as database:
        admin = database.scalar(
            select(
                User
            )
            .where(
                User.is_admin.is_(True),
                User.is_active.is_(True),
            )
            .order_by(
                User.id.asc()
            )
        )
        if admin is None:
            raise SystemExit(
                "No active HR/Admin account "
                "was found."
            )
        credential_lines.extend(
            [
                "1. HR / ADMIN",
                f"Email: {admin.email}",
                (
                    "Password: existing "
                    "Admin password (unchanged)"
                ),
                "Access: Full system",
                "",
            ]
        )
        print("")
        print(
            "HR/Admin account:"
        )
        print(
            f"  {admin.email}"
        )
        required_teams = {
            item["team"]
            for item in ACCOUNT_CONFIGS
        }
        for team_name in sorted(
            required_teams
        ):
            team, created = ensure_team(
                database,
                name=team_name,
                admin_id=admin.id,
            )
            if created:
                print(
                    "Created team: "
                    f"{team.name}"
                )
        for shift_name in REQUIRED_SHIFTS:
            shift, created = ensure_shift(
                database,
                name=shift_name,
                admin_id=admin.id,
            )
            if created:
                print(
                    "Created shift: "
                    f"{shift.name}"
                )
        database.commit()
        account_number = 2
        for config in ACCOUNT_CONFIGS:
            email = config[
                "email"
            ].lower()
            team = find_team(
                database,
                config["team"],
            )
            if team is None:
                raise RuntimeError(
                    "Required team missing: "
                    + config["team"]
                )
            shift = None
            if config["shift"]:
                shift = find_shift(
                    database,
                    config["shift"],
                )
                if shift is None:
                    raise RuntimeError(
                        "Required shift missing: "
                        + config["shift"]
                    )
            user = database.scalar(
                select(
                    User
                ).where(
                    User.email == email
                )
            )
            password = None
            if user is None:
                password = (
                    make_password()
                )
                user = User(
                    email=email,
                    hashed_password=(
                        hash_password(
                            password
                        )
                    ),
                    is_active=True,
                    is_admin=False,
                )
                database.add(user)
                database.flush()
                action = "CREATED"
            else:
                if user.is_admin:
                    raise RuntimeError(
                        "Attendance email "
                        "belongs to Admin: "
                        + email
                    )
                user.is_active = True
                action = "EXISTING"
            scope = database.scalar(
                select(
                    UserAttendanceScope
                ).where(
                    UserAttendanceScope.user_id
                    == user.id
                )
            )
            if scope is None:
                scope = UserAttendanceScope(
                    user_id=user.id,
                    team_id=team.id,
                    shift_id=(
                        shift.id
                        if shift is not None
                        else None
                    ),
                )
                database.add(scope)
            else:
                scope.team_id = team.id
                scope.shift_id = (
                    shift.id
                    if shift is not None
                    else None
                )
            database.commit()
            print(
                f"{action}: "
                f"{config['label']} -> "
                f"{email}"
            )
            credential_lines.extend(
                [
                    (
                        f"{account_number}. "
                        f"{config['label']}"
                    ),
                    f"Email: {email}",
                ]
            )
            if password is not None:
                credential_lines.append(
                    f"Password: {password}"
                )
            else:
                credential_lines.append(
                    "Password: existing "
                    "password unchanged"
                )
            credential_lines.append(
                "Team: "
                + config["team"]
            )
            if shift is None:
                credential_lines.append(
                    "Shift: Dynamic team shifts"
                )
            else:
                credential_lines.append(
                    "Shift: "
                    + shift.name
                )
            credential_lines.extend(
                [
                    (
                        "Access: Daily "
                        "Attendance only"
                    ),
                    "",
                ]
            )
            account_number += 1
    credentials_dir = Path(
        "data"
    )
    credentials_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )
    credential_path = (
        credentials_dir
        / (
            "attendance_account_"
            "credentials_"
            f"{timestamp}_LOCAL.txt"
        )
    )
    credential_path.write_text(
        "\n".join(
            credential_lines
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    print("")
    print(
        "Attendance account setup "
        "completed."
    )
    print(
        "Credential file saved locally:"
    )
    print(
        credential_path.resolve()
    )
    print("")
    print(
        "Do not commit or share "
        "the credential file."
    )
if __name__ == "__main__":
    main()
