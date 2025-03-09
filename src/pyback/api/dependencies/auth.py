from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from pyback.config.settings import AuthSettings
from pyback.core.exceptions import UnauthorizedError
from pyback.db.models.user import User
from pyback.db.postgres import PostgresDatabase
from pyback.db.repositories.users import UserRepository
from pyback.services.auth import AuthService

from .common import get_auth_settings
from .db import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_auth_service(
    db: Annotated[PostgresDatabase, Depends(get_db)],
) -> AuthService:
    """Inject AuthService with UserRepository."""
    return AuthService(UserRepository(db))


async def get_current_user(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_settings: Annotated[AuthSettings, Depends(get_auth_settings)],
) -> User:
    """Get current user from token."""
    user = await auth_service.get_current_active_user(token, auth_settings)
    request.state.user = user
    return user


def admin_required(user: User = Depends(get_current_user)) -> User:
    """Ensure the current user has administrative privileges.

    Raises:
        UnauthorizedError: If the current user is not an admin.

    Returns:
        User: The authenticated admin user.
    """
    if not user.is_admin:
        raise UnauthorizedError
    return user
