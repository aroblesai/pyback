from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pyback.db.postgres import PostgresDatabase
    from pyback.db.redis import RedisDatabase

from pyback.db.postgres import pgdb
from pyback.db.redis import redis_db


def get_db() -> "PostgresDatabase":
    """Retrieve the PostgreSQL database connection.

    Raises:
        RuntimeError: If the PostgreSQL session manager is not initialized.

    Returns:
        PostgresDatabase: An initialized PostgreSQL database connection.
    """
    if pgdb is None:
        raise RuntimeError("PostgreSQL session manager instance not initialized")
    return pgdb


def get_redis_db() -> "RedisDatabase":
    """Retrieve the Redis database connection.

    Raises:
        RuntimeError: If the Redis client manager is not initialized.

    Returns:
        RedisDatabase: An initialized Redis database connection.
    """
    if redis_db is None:
        raise RuntimeError("Redis client manager instance not initialized")
    return redis_db
