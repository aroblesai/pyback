from uuid import UUID

from pyback.api.models.user import UserCreate, UserUpdate
from pyback.db.models.user import User
from pyback.db.postgres import PostgresDatabase


class UserRepository:
    """Handles database interactions for the User entity."""

    def __init__(self, db: PostgresDatabase):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email."""
        return await self.db.fetch_one(User, User.email == email)

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Fetch a user by ID."""
        return await self.db.fetch_one(User, User.id == user_id)

    async def create(self, user: UserCreate, hashed_password: str) -> User:
        """Create a new user."""
        # Check if user already exists by email
        existing_user = await self.get_by_email(user.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        new_user = User()
        new_user.email = user.email
        new_user.first_name = user.first_name
        new_user.last_name = user.last_name
        new_user.hashed_password = hashed_password
        new_user.is_active = True
        new_user.is_admin = False

        return await self.db.add(new_user)

    async def update(self, user_id: UUID, user_update: UserUpdate) -> User | None:
        """Update user information."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        if not update_data:
            return user

        for key, value in update_data.items():
            setattr(user, key, value)

        return await self.db.update(user)

    async def update_password(
        self,
        user_id: UUID,
        new_hashed_password: str,
    ) -> User | None:
        """Update the user's password."""
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        user.hashed_password = new_hashed_password
        return await self.db.update(user)

    async def delete(self, user_id: UUID) -> User | None:
        """Soft delete a user by setting is_active to False."""
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        user.is_active = False
        return await self.db.update(user)

    async def list_active_users(self) -> list[User]:
        """List all active users."""
        return await self.db.fetch_all(User, User.is_active)

    async def reactivate_user(self, user_id: UUID) -> User | None:
        """Reactivate a soft-deleted user."""
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        user.is_active = True
        return await self.db.update(user)
