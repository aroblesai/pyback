from datetime import timedelta
from typing import Annotated

from fastapi import Depends
import jwt
from jwt import PyJWTError
from jwt.exceptions import ExpiredSignatureError

from pyback.api.dependencies.common import get_auth_settings
from pyback.api.dependencies.db import get_db
from pyback.api.models.auth import Token, TokenData
from pyback.config.settings import AuthSettings
from pyback.core.auth import create_access_token, verify_password
from pyback.core.exceptions import (
    ExpiredTokenError,
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundError,
)
from pyback.db.models.user import User
from pyback.db.repositories.users import UserRepository


class AuthService:
    """Service class handling authentication and authorization business logic.

    This class provides methods for user authentication, token management,
    and user verification. It implements JWT-based authentication flow and
    integrates with the user repository for data access.

    Attributes:
        user_repo (UserRepository): Repository for user-related database operations.
    """

    def __init__(self, user_repo: UserRepository | None):
        """Initialize the AuthService.

        Args:
            user_repo (UserRepository | None): Repository for user operations.
                If None, creates a new repository using the default database
                connection.
        """
        self.user_repo = user_repo or UserRepository(get_db())

    async def get_active_user_by_email(self, email: str) -> User | None:
        """Retrieve an active user by their email address.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            User | None: The user if found and active.

        Raises:
            InvalidCredentialsError: If the user is not found.
            NotFoundError: If the user is found but not active.
        """
        user = await self.user_repo.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError
        if not user.is_active:
            raise NotFoundError
        return user

    async def get_current_active_user(
        self,
        token,
        auth_settings: Annotated[AuthSettings, Depends(get_auth_settings)],
    ) -> User:
        """Get the current active user from a JWT token.

        Args:
            token: The JWT token to validate.
            auth_settings (AuthSettings): Authentication settings for token validation.

        Returns:
            User: The current active user.

        Raises:
            InvalidCredentialsError: If the token is invalid or user not found.
        """
        token_data = await self.get_token_data(token, auth_settings)
        if token_data is None or token_data.email is None:
            raise InvalidCredentialsError
        token_email: str = token_data.email
        user = await self.get_active_user_by_email(token_email)
        if user is None:
            raise NotFoundError
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate a user with their email and password.

        Args:
            email (str): The user's email address.
            password (str): The user's password in plain text.

        Returns:
            User | None: The authenticated user if credentials are valid,
                None otherwise.

        Raises:
            InvalidCredentialsError: If the user is not found.
            NotFoundError: If the user is found but not active.
        """
        user = await self.get_active_user_by_email(email)
        if user and verify_password(password, user.hashed_password):
            return user
        return None

    async def get_access_token(
        self,
        user: User,
        auth_settings: Annotated[AuthSettings, Depends(get_auth_settings)],
    ) -> Token:
        """Generate a JWT access token for a user.

        Args:
            user (User): The user to generate the token for.
            auth_settings (AuthSettings): Authentication settings for token generation.

        Returns:
            Token: An object containing the generated access token.
        """
        if auth_settings.JWT_EXPIRE_MINUTES is None:
            raise ValueError("JWT_EXPIRE_MINUTES must be set in AuthSettings")
        access_token_expires = timedelta(
            minutes=auth_settings.JWT_EXPIRE_MINUTES,
        )
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires,
        )
        return Token(access_token=access_token)

    async def get_token_data(
        self,
        token,
        auth_settings: Annotated[AuthSettings, Depends(get_auth_settings)],
    ) -> TokenData:
        """Decode and validate a JWT token.

        Args:
            token: The JWT token to decode and validate.
            auth_settings (AuthSettings): Authentication settings for token validation.

        Returns:
            TokenData: The decoded token data containing the user's email.

        Raises:
            ExpiredTokenError: If the token has expired.
            InvalidTokenError: If the token is malformed or invalid.
        """
        if auth_settings.JWT_SECRET is None:
            raise ValueError("JWT_SECRET must be set in AuthSettings")
        try:
            payload = jwt.decode(
                token,
                auth_settings.JWT_SECRET.get_secret_value(),
                algorithms=[auth_settings.JWT_ALGORITHM],
            )
            email: str = payload.get("sub")
            if email is None:
                raise InvalidTokenError
            return TokenData(email=email)
        except ExpiredSignatureError:
            raise ExpiredTokenError
        except PyJWTError:
            raise InvalidTokenError
