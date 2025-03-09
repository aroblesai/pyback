import uuid

from sqlalchemy import Boolean, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from pyback.db.models.base import Base


class User(Base):
    """Represents a user in the system.

    This model defines the structure and attributes of a user entity in the database.
    It includes personal information, authentication details, and user status flags.

    Attributes:
        id (UUID): Unique identifier for the user, automatically generated.
        first_name (str): User's first name, limited to 100 characters.
        last_name (str): User's last name, limited to 100 characters.
        email (str): User's email address, limited to 255 characters, must be unique.
        hashed_password (str): Securely hashed password for the user.
        is_admin (bool): Flag indicating whether the user has administrative privileges.
        is_active (bool): Flag indicating whether the user account is active.
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
        doc="Unique identifier for the user.",
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="User's first name.",
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="User's last name.",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="User's email address.",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Securely hashed password for the user.",
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        doc="Flag indicating whether the user has administrative privileges.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        doc="Flag indicating whether the user account is active.",
    )

    # Adding unique index on the email column
    __table_args__ = (Index(None, "email", unique=True),)
