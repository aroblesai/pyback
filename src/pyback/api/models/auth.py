from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Model representing the login request payload.

    Attributes:
        email (EmailStr): The email address of the user attempting to log in.
        password (str): The user's password for authentication.
    """

    email: EmailStr
    password: str


class Token(BaseModel):
    """Model representing an authentication token.

    Attributes:
        access_token (str): The JWT access token for authentication.
        token_type (str, optional): The type of token, defaults to "bearer".
    """

    access_token: str
    token_type: str = "bearer"  # noqa: S105


class TokenData(BaseModel):
    """Model representing decoded token data.

    Attributes:
        email (EmailStr | None, optional): The email associated with the token,
        can be None if no email is present.
    """

    email: EmailStr | None = None
