from fastapi import APIRouter, Depends

from pyback.api.dependencies.auth import get_auth_service
from pyback.api.dependencies.common import get_auth_settings
from pyback.api.dependencies.rate_limit import rate_limit
from pyback.api.dependencies.users import get_user_service
from pyback.api.models.auth import LoginRequest, Token
from pyback.api.models.user import User, UserCreate
from pyback.config.rate_limit import RateLimitConfig
from pyback.config.settings import AuthSettings
from pyback.core.exceptions import ConflictError, InvalidCredentialsError
from pyback.services.auth import AuthService
from pyback.services.users import UserService


router = APIRouter()


@router.post(
    "/token",
    response_model=Token,
    dependencies=[
        Depends(
            rate_limit(
                RateLimitConfig.Scope.PUBLIC,
                times=5,
                seconds=60,
                prefix="login",
            ),
        ),
    ],
)
async def login_for_access_token(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    auth_settings: AuthSettings = Depends(get_auth_settings),
):
    """Authenticate a user and generate an access token.

    This endpoint handles user login by verifying credentials and generating
    a JWT access token for authenticated users.

    Args:
        login_data (LoginRequest): User's login credentials containing email and
        password.
        auth_service (AuthService): Service for handling authentication operations.
        auth_settings (AuthSettings): Authentication configuration settings.

    Raises:
        InvalidCredentialsError: If the provided email or password is incorrect.

    Returns:
        Token: A JWT access token for the authenticated user.
    """
    user = await auth_service.authenticate(login_data.email, login_data.password)
    if not user:
        raise InvalidCredentialsError("Incorrect email or password")
    return await auth_service.get_access_token(user, auth_settings)


@router.post(
    "/signup",
    response_model=User,
    status_code=201,
    dependencies=[
        Depends(
            rate_limit(
                RateLimitConfig.Scope.PUBLIC,
                times=3,
                seconds=300,
                prefix="signup",
            ),
        ),
    ],
)
async def create_user(
    user: UserCreate,
    users_service: UserService = Depends(get_user_service),
):
    """Create a new user."""
    try:
        new_user = await users_service.create_user(user)
        return new_user
    except ValueError as e:
        raise ConflictError(str(e))
