from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base model for user information.

    Attributes:
        email (EmailStr): User's email address, with a maximum length of 255 characters.
    """

    email: EmailStr = Field(max_length=255)


class UserCreate(UserBase):
    """Model for creating a new user.

    Attributes:
        password (str): User's password, between 8 and 30 characters long.
        first_name (str): User's first name, between 2 and 100 characters long.
        last_name (str): User's last name, between 2 and 100 characters long.
    """

    password: str = Field(min_length=8, max_length=30)
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)

    @field_validator("password", "first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that the input is not an empty string or whitespace.

        Args:
            v (str): The input string to validate.

        Raises:
            ValueError: If the input is an empty string or contains only whitespace.

        Returns:
            str: The validated input string.
        """
        if v.strip() == "":
            raise ValueError("Name cannot be empty or contain only whitespace")
        return v


class UserUpdate(BaseModel):
    """Model for updating user information.

    Attributes:
        first_name (str | None): Optional new first name for the user.
        last_name (str | None): Optional new last name for the user.
    """

    first_name: str | None = None
    last_name: str | None = None


class User(UserBase):
    """Model representing a complete user profile.

    Attributes:
        id (UUID): Unique identifier for the user, generated automatically.
        first_name (str): User's first name.
        last_name (str): User's last name.
        created_at (datetime): Timestamp of user account creation.
        updated_at (datetime): Timestamp of last user profile update.
        is_admin (bool): Flag indicating if the user has administrative privileges.
        is_active (bool): Flag indicating if the user account is active.
    """

    id: UUID = Field(default_factory=uuid4)
    first_name: str
    last_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_admin: bool = False
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)
