from typing import Annotated
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
)
from backend.app.api.dependencies import (
    AuthenticatedUserDependency,
    DatabaseDependency,
)
from backend.app.core.security import (
    create_access_token,
)
from backend.app.schemas.auth import (
    Token,
    UserRead,
)
from backend.app.services.auth_service import (
    authenticate_user,
)
router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)
@router.post(
    "/login",
    response_model=Token,
    summary="Log in to PeopleMind AI",
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    database: DatabaseDependency,
) -> Token:
    user = authenticate_user(
        database=database,
        email=form_data.username,
        password=form_data.password,
    )
    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Incorrect email or password."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )
    token = create_access_token(
        subject=user.email
    )
    return Token(
        access_token=token
    )
@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the logged-in user profile",
)
def read_current_user(
    current_user:
        AuthenticatedUserDependency,
) -> UserRead:
    return UserRead.model_validate(
        current_user
    )
