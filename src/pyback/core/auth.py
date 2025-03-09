from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from pyback.api.dependencies.common import get_auth_settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that a plain text password matches a hashed password.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password for comparison.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    # Hash the plain password with the same salt and compare
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hashes a plain text password using bcrypt.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    # Generate a salt
    salt = bcrypt.gensalt()
    # Hash the password with the generated salt
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    # Return the hashed password as a string
    return hashed_password.decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token with optional custom expiration.

    This function generates a JSON Web Token (JWT) with the provided data and
    an expiration time. If no expiration delta is provided, it uses the default
    session time-to-live (TTL) from authentication settings.

    Args:
        data (dict): The payload data to be encoded in the token.
        expires_delta (timedelta, optional): Custom expiration time.
            Defaults to None, which uses the default session TTL.

    Returns:
        str: A JWT access token encoded with the provided data and expiration.
    """
    to_encode = data.copy()
    auth_settings = get_auth_settings()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=auth_settings.SESSION_TTL_MIN)
    to_encode.update({"exp": expire})
    encoded_jwt = str(
        jwt.encode(
            to_encode,
            auth_settings.JWT_SECRET.get_secret_value(),
            algorithm=auth_settings.JWT_ALGORITHM,
        ),
    )
    return encoded_jwt
