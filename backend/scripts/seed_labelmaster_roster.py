import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )
from sqlalchemy import func, select
from backend.app.db.database import SessionLocal
from backend.app.models.attendance_employee import AttendanceEmployee
from backend.app.models.attendance_shift import AttendanceShift
from backend.app.models.attendance_team import AttendanceTeam
from backend.app.models.user import User
ROSTER = [
    ("EMP001", "Abdullah", "Team Lead", "Morning", ["Friday", "Saturday"]),
    ("EMP002", "Nusrat", "Data Annotation Analyst", "Early Morning", ["Tuesday", "Wednesday"]),
    ("EMP003", "Sumya", "Data Annotation Analyst", "Early Morning", ["Tuesday", "Wednesday"]),
    ("EMP004", "Sanjida", "Data Annotation Analyst", "Early Morning", ["Saturday", "Sunday"]),
    ("EMP005", "Prome", "Data Annotation Analyst", "Morning", ["Thursday", "Friday"]),
    ("EMP006", "Meem", "Data Annotation Analyst", "Morning", ["Thursday", "Friday"]),
    ("EMP007", "Razia", "Data Annotation Analyst", "Morning", ["Friday", "Saturday"]),
    ("EMP008", "Raka", "Data Annotation Analyst", "Morning", ["Friday", "Saturday"]),
    ("EMP009", "Taposhi", "Data Annotation Analyst", "Morning", ["Friday", "Saturday"]),
    ("EMP010", "Joya", "Data Annotation Analyst", "Morning", ["Saturday", "Sunday"]),
    ("EMP011", "Sneha", "Data Annotation Analyst", "Morning", ["Friday", "Saturday"]),
    ("EMP012", "Rimi", "Data Annotation Analyst", "Morning", ["Thursday", "Friday"]),
    ("EMP013", "Tahmina", "Data Annotation Analyst", "Morning", ["Thursday", "Friday"]),
    ("EMP014", "Orin", "Data Annotation Analyst", "Morning", ["Saturday", "Sunday"]),
    ("EMP015", "Turjo", "Data Annotation Analyst", "Morning", ["Sunday", "Monday"]),
    ("EMP017", "Hazera", "Data Annotation Analyst", "Morning", ["Tuesday", "Wednesday"]),
    ("EMP019", "Antor", "Data Annotation Analyst", "Evening", ["Tuesday", "Wednesday"]),
    ("EMP020", "Azad", "Data Annotation Analyst", "Evening", ["Friday", "Saturday"]),
    ("EMP021", "Rakib", "Data Annotation Analyst", "Evening", ["Sunday", "Monday"]),
    ("EMP022", "Mehedi", "Data Annotation Analyst", "Evening", ["Sunday", "Monday"]),
    ("EMP023", "Salman", "Data Annotation Analyst", "Night", ["Monday", "Tuesday"]),
    ("EMP024", "Pritom", "Data Annotation Analyst", "Night", ["Tuesday", "Wednesday"]),
    ("EMP025", "Soumik", "Data Annotation Analyst", "Night", ["Sunday", "Monday"]),
    ("EMP026", "Sabith", "Data Annotation Analyst", "Night", ["Tuesday", "Wednesday"]),
    ("EMP027", "Fahim", "Data Annotation Analyst", "Night", ["Wednesday", "Thursday"]),
    ("EMP028", "Shoaib", "Data Annotation Analyst", "Night", ["Sunday", "Monday"]),
    ("EMP029", "Hemall", "Data Annotation Analyst", "Night", ["Monday", "Tuesday"]),
    ("EMP030", "Rahman", "Data Annotation Analyst", "Night", ["Tuesday", "Wednesday"]),
    ("EMP031", "Shanto", "Data Annotation Analyst", "Night", ["Wednesday", "Thursday"]),
]
REQUIRED_SHIFTS = [
    "Early Morning",
    "Morning",
    "Evening",
    "Night",
]
def normalized_team_name(value: str) -> str:
    return "".join(
        character.lower()
        for character in value
        if character.isalnum()
    )
with SessionLocal() as database:
    admin = database.scalar(
        select(User)
        .where(
            User.is_admin.is_(True),
            User.is_active.is_(True),
        )
        .order_by(User.id.asc())
    )
    if admin is None:
        raise SystemExit(
            "No active admin user was found. "
            "Log in / create the normal admin first."
        )
    teams = list(
        database.scalars(
            select(AttendanceTeam)
        ).all()
    )
    matching_teams = [
        team
        for team in teams
        if normalized_team_name(team.name)
        == "labelmaster"
    ]
    if len(matching_teams) > 1:
        raise SystemExit(
            "More than one Labelmaster-like team exists. "
            "Please remove the duplicate before seeding."
        )
    if matching_teams:
        team = matching_teams[0]
        if team.name != "Labelmaster":
            print(
                f"Normalizing team name: "
                f"{team.name!r} -> 'Labelmaster'"
            )
            team.name = "Labelmaster"
        team.status = "active"
    else:
        team = AttendanceTeam(
            name="Labelmaster",
            description="Data annotation team",
            status="active",
            created_by_id=admin.id,
        )
        database.add(team)
        database.flush()
        print("Created team: Labelmaster")
    shift_by_name = {}
    for shift_name in REQUIRED_SHIFTS:
        shift = database.scalar(
            select(AttendanceShift)
            .where(
                func.lower(
                    AttendanceShift.name
                )
                == shift_name.lower()
            )
        )
        if shift is None:
            shift = AttendanceShift(
                name=shift_name,
                description=None,
                status="active",
                created_by_id=admin.id,
            )
            database.add(shift)
            database.flush()
            print(
                f"Created shift: {shift_name}"
            )
        else:
            shift.status = "active"
        shift_by_name[
            shift_name
        ] = shift
    database.flush()
    created_count = 0
    skipped_count = 0
    for (
        employee_code,
        full_name,
        designation,
        shift_name,
        weekly_holidays,
    ) in ROSTER:
        existing = database.scalar(
            select(AttendanceEmployee)
            .where(
                AttendanceEmployee.employee_code
                == employee_code
            )
        )
        if existing is not None:
            skipped_count += 1
            print(
                f"SKIP {employee_code}: "
                f"already exists as "
                f"{existing.full_name}"
            )
            continue
        employee = AttendanceEmployee(
            employee_code=employee_code,
            full_name=full_name,
            designation=designation,
            team_id=team.id,
            shift_id=(
                shift_by_name[
                    shift_name
                ].id
            ),
            weekly_holidays=weekly_holidays,
            is_active=True,
            created_by_id=admin.id,
        )
        database.add(employee)
        created_count += 1
        print(
            f"ADD  {employee_code} "
            f"{full_name} -> {shift_name}"
        )
    database.commit()
    labelmaster_count = database.scalar(
        select(
            func.count(
                AttendanceEmployee.id
            )
        ).where(
            AttendanceEmployee.team_id
            == team.id
        )
    ) or 0
    print("")
    print("=" * 55)
    print("LABELMASTER ROSTER SEED COMPLETE")
    print("=" * 55)
    print(
        f"Created this run : {created_count}"
    )
    print(
        f"Already existing : {skipped_count}"
    )
    print(
        f"Labelmaster total: {labelmaster_count}"
    )
    print("")
    print(
        "Source screenshots contain "
        "29 visible employees."
    )
    print(
        "EMP016 and EMP018 were not visible "
        "and were intentionally not invented."
    )
