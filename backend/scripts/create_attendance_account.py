from getpass import getpass
from email_validator import (
    EmailNotValidError,
    validate_email,
)
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
def read_email() -> str:
    while True:
        raw = input(
            "Attendance account email: "
        ).strip().lower()
        try:
            result = validate_email(
                raw,
                check_deliverability=False,
            )
            return result.normalized.lower()
        except EmailNotValidError as error:
            print(
                f"Invalid email: {error}"
            )
def read_password() -> str:
    while True:
        password = getpass(
            "Password: "
        )
        confirmation = getpass(
            "Confirm password: "
        )
        if password != confirmation:
            print(
                "Passwords did not match."
            )
            continue
        if len(password) < 12:
            print(
                "Password must be at least "
                "12 characters."
            )
            continue
        if not any(
            character.isalpha()
            for character in password
        ):
            print(
                "Password must contain "
                "a letter."
            )
            continue
        if not any(
            character.isdigit()
            for character in password
        ):
            print(
                "Password must contain "
                "a number."
            )
            continue
        return password
def main() -> None:
    Base.metadata.create_all(
        bind=engine
    )
    team_name = input(
        "Assigned team name: "
    ).strip()
    shift_name = input(
        "Assigned shift name "
        "(leave blank for whole team): "
    ).strip()
    with SessionLocal() as database:
        team = database.scalar(
            select(
                AttendanceTeam
            ).where(
                func.lower(
                    AttendanceTeam.name
                )
                == team_name.lower()
            )
        )
        if team is None:
            raise SystemExit(
                "Attendance team not found."
            )
        shift = None
        if shift_name:
            shift = database.scalar(
                select(
                    AttendanceShift
                ).where(
                    func.lower(
                        AttendanceShift.name
                    )
                    == shift_name.lower()
                )
            )
            if shift is None:
                raise SystemExit(
                    "Attendance shift not found."
                )
        email = read_email()
        existing_user = database.scalar(
            select(
                User
            ).where(
                User.email == email
            )
        )
        if existing_user is not None:
            raise SystemExit(
                "A user with this email "
                "already exists."
            )
        password = read_password()
        user = User(
            email=email,
            hashed_password=(
                hash_password(password)
            ),
            is_active=True,
            is_admin=False,
        )
        database.add(user)
        database.flush()
        database.add(
            UserAttendanceScope(
                user_id=user.id,
                team_id=team.id,
                shift_id=(
                    shift.id
                    if shift is not None
                    else None
                ),
            )
        )
        database.commit()
        print("")
        print(
            "Attendance account created."
        )
        print(
            f"Email: {email}"
        )
        print(
            f"Team: {team.name}"
        )
        if shift is None:
            print(
                "Shift scope: ALL ACTIVE "
                "TEAM SHIFTS"
            )
        else:
            print(
                f"Shift scope: {shift.name}"
            )
        print(
            "Role: attendance"
        )
if __name__ == "__main__":
    main()
