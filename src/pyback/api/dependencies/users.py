from typing import Annotated

from fastapi import Depends

from pyback.db.postgres import PostgresDatabase
from pyback.db.repositories.users import UserRepository
from pyback.services.users import UserService

from .db import get_db


async def get_user_service(db: Annotated[PostgresDatabase, Depends(get_db)]):
    """Inject UserService with UserRepository."""
    return UserService(UserRepository(db))
