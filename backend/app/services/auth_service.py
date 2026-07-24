from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.security import verify_password
from backend.app.models.user import User
def get_user_by_email(database: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    statement = select(User).where(User.email == normalized_email)
    return database.scalar(statement)
def authenticate_user(
    database: Session,
    email: str,
    password: str,
) -> User | None:
    user = get_user_by_email(database, email)
    if user is None:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
