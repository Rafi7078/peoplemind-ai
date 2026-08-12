from sqlalchemy import (
    select,
)
from sqlalchemy.orm import Session
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
from backend.app.schemas.attendance_access import (
    AttendanceAllowedShiftRead,
    DailyAttendanceAccessRead,
)
class AttendanceUserProfileError(
    PermissionError
):
    pass
class AttendanceUserScopeError(
    PermissionError
):
    pass
def _team_allowed_shifts(
    database: Session,
    *,
    team_id: int,
) -> list[
    AttendanceAllowedShiftRead
]:
    shift_ids = list(
        database.scalars(
            select(
                AttendanceEmployee.shift_id
            )
            .where(
                AttendanceEmployee.team_id
                == team_id,
                AttendanceEmployee.is_active
                .is_(True),
            )
            .distinct()
        ).all()
    )
    if not shift_ids:
        return []
    shifts = list(
        database.scalars(
            select(
                AttendanceShift
            )
            .where(
                AttendanceShift.id.in_(
                    shift_ids
                )
            )
            .order_by(
                AttendanceShift.name.asc()
            )
        ).all()
    )
    return [
        AttendanceAllowedShiftRead(
            id=shift.id,
            name=shift.name,
        )
        for shift in shifts
    ]
def get_daily_access(
    database: Session,
    *,
    user: User,
) -> DailyAttendanceAccessRead:
    if user.is_admin:
        return DailyAttendanceAccessRead(
            role="admin",
            is_admin=True,
            scope_type="admin",
            allowed_shifts=[],
        )
    scope = database.scalar(
        select(
            UserAttendanceScope
        ).where(
            UserAttendanceScope.user_id
            == user.id
        )
    )
    if scope is None:
        raise AttendanceUserProfileError(
            "This account has no attendance "
            "scope assigned."
        )
    team = database.get(
        AttendanceTeam,
        scope.team_id,
    )
    if team is None:
        raise AttendanceUserProfileError(
            "The assigned attendance team "
            "could not be found."
        )
    if scope.shift_id is not None:
        shift = database.get(
            AttendanceShift,
            scope.shift_id,
        )
        if shift is None:
            raise AttendanceUserProfileError(
                "The assigned attendance shift "
                "could not be found."
            )
        return DailyAttendanceAccessRead(
            role="attendance",
            is_admin=False,
            team_id=team.id,
            team_name=team.name,
            shift_id=shift.id,
            shift_name=shift.name,
            scope_type="team_shift",
            allowed_shifts=[
                AttendanceAllowedShiftRead(
                    id=shift.id,
                    name=shift.name,
                )
            ],
        )
    return DailyAttendanceAccessRead(
        role="attendance",
        is_admin=False,
        team_id=team.id,
        team_name=team.name,
        shift_id=None,
        shift_name=None,
        scope_type="team",
        allowed_shifts=(
            _team_allowed_shifts(
                database,
                team_id=team.id,
            )
        ),
    )
def require_daily_scope(
    database: Session,
    *,
    user: User,
    team_id: int,
    shift_id: int,
) -> DailyAttendanceAccessRead:
    access = get_daily_access(
        database,
        user=user,
    )
    if access.is_admin:
        return access
    if access.team_id != team_id:
        raise AttendanceUserScopeError(
            "This attendance account may "
            "only access its assigned team."
        )
    allowed_shift_ids = {
        item.id
        for item in access.allowed_shifts
    }
    if shift_id not in allowed_shift_ids:
        raise AttendanceUserScopeError(
            "This attendance account may "
            "not access the selected shift."
        )
    return access
