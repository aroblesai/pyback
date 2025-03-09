from uuid import UUID

from pyback.api.dependencies.db import get_db
from pyback.api.models.user import UserCreate, UserUpdate
from pyback.core.auth import get_password_hash
from pyback.db.models.user import User
from pyback.db.repositories.users import UserRepository


class UserService:
    """Handles business logic for user management."""

    def __init__(self, user_repo: UserRepository | None):
        self.user_repo = user_repo or UserRepository(get_db())

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return str(get_password_hash(password))

    async def create_user(self, user: UserCreate) -> User:
        """Creates a new user with a hashed password."""
        hashed_password = self.hash_password(user.password)
        return await self.user_repo.create(user, hashed_password)

    async def get_user(self, user_id: UUID) -> User | None:
        """Get a user by ID."""
        return await self.user_repo.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        return await self.user_repo.get_by_email(email)

    async def list_active_users(self) -> list[User]:
        """Get all active users."""
        return await self.user_repo.list_active_users()

    async def update_user(
        self,
        user_id: UUID,
        user_update: UserUpdate,
    ) -> User | None:
        """Update user information."""
        return await self.user_repo.update(user_id, user_update)

    async def update_password(self, user_id: UUID, new_password: str) -> None:
        """Update a user's password."""
        hashed_password = self.hash_password(new_password)
        await self.user_repo.update_password(user_id, hashed_password)

    async def delete_user(self, user_id: UUID) -> None:
        """Soft delete a user."""
        await self.user_repo.delete(user_id)

    async def reactivate_user(self, user_id: UUID) -> None:
        """Reactivate a soft-deleted user."""
        await self.user_repo.reactivate_user(user_id)
