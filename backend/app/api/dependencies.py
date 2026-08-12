from typing import Annotated
import jwt
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session
from backend.app.core.security import (
    decode_access_token,
)
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.services.auth_service import (
    get_user_by_email,
)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)
DatabaseDependency = Annotated[
    Session,
    Depends(get_db),
]
TokenDependency = Annotated[
    str,
    Depends(oauth2_scheme),
]
def get_authenticated_user(
    token: TokenDependency,
    database: DatabaseDependency,
) -> User:
    credentials_error = HTTPException(
        status_code=(
            status.HTTP_401_UNAUTHORIZED
        ),
        detail=(
            "Could not validate "
            "authentication credentials."
        ),
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )
    try:
        payload = decode_access_token(
            token
        )
        email = payload.get("sub")
        if (
            not isinstance(email, str)
            or not email
        ):
            raise credentials_error
    except (
        InvalidTokenError,
        jwt.PyJWTError,
    ):
        raise credentials_error
    user = get_user_by_email(
        database,
        email,
    )
    if (
        user is None
        or not user.is_active
    ):
        raise credentials_error
    return user
AuthenticatedUserDependency = Annotated[
    User,
    Depends(get_authenticated_user),
]
def get_current_user(
    user: AuthenticatedUserDependency,
) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "HR/Admin access required."
            ),
        )
    return user
CurrentUserDependency = Annotated[
    User,
    Depends(get_current_user),
]
