from typing import Any

from fastapi import Request
from fastapi.responses import ORJSONResponse


class InvalidTokenError(Exception):
    """Exception for token authentication."""

    def __init__(self, detail: str = "Invalid or missing authentication token"):
        """Initialize the InvalidTokenError.

        Args:
            detail (str, optional): Detailed error message.
            Defaults to a generic token authentication error.
        """
        self.detail = detail


class ExpiredTokenError(Exception):
    """Exception for token expiration."""

    def __init__(self, detail: str = "Authentication token has expired"):
        """Initialize the ExpiredTokenError.

        Args:
            detail (str, optional): Detailed error message.
            Defaults to a generic token expiration error.
        """
        self.detail = detail


class InvalidCredentialsError(Exception):
    """Exception for token validity."""

    def __init__(self, detail: str = "Could not validate credentials"):
        """Initialize the InvalidCredentialsError.

        Args:
            detail (str, optional): Detailed error message.
            Defaults to a generic credential validation error.
        """
        self.detail = detail


class UnauthorizedError(Exception):
    """Exception for unauthorized access."""

    def __init__(self, detail: str = "Permission denied"):
        """Initialize the UnauthorizedError.

        Args:
            detail (str, optional): Detailed error message.
            Defaults to a generic permission denial error.
        """
        self.detail = detail


class BadRequestError(Exception):
    """Exception for bad requests."""

    def __init__(self, detail: str = "Bad request"):
        """Initialize the BadRequestError.

        Args:
            detail (str, optional): Detailed error message.
            Defaults to a generic bad request error.
        """
        self.detail = detail


class NotFoundError(Exception):
    """Exception for not found resources."""

    def __init__(self, detail: str = "Resource not found"):
        """Initialize the NotFoundError.

        Args:
            detail (str, optional): Detailed error message.
            Defaults to a generic resource not found error.
        """
        self.detail = detail


class ConflictError(Exception):
    """Exception for resource conflicts."""

    def __init__(self, detail: str = "Resource conflict"):
        """Initialize the ConflictError.

        Args:
            detail (str, optional): Detailed error message.
            Defaults to a generic resource conflict error.
        """
        self.detail = detail


class ValidationExceptionError(Exception):
    """Exception for validation errors."""

    def __init__(self, detail: str = "Validation error"):
        """Initialize the ValidationExceptionError.

        Args:
            detail (str, optional): Detailed error message.
            Defaults to a generic validation error.
        """
        self.detail = detail


class InternalError(Exception):
    """Exception for internal errors."""

    def __init__(self, detail: str = "Internal server errors"):
        """Initialize the InternalError.

        Args:
            detail (str, optional): Detailed error message.
            Defaults to a generic internal server error.
        """
        self.detail = detail


def create_error_handler(status_code: int):
    """Create a generic error handler for the given status code.

    Args:
        status_code: HTTP status code to return

    Returns:
        Exception handler function
    """

    async def handler(request: Request, exc: Any) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status_code,
            content={"detail": exc.detail},
        )

    return handler


def create_auth_error_handler(status_code: int):
    """Create an authentication error handler for the given status code.

    Args:
        status_code: HTTP status code to return

    Returns:
        Exception handler function
    """

    async def handler(request: Request, exc: Any) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status_code,
            content={"detail": exc.detail},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return handler
