from functools import lru_cache

from pyback.config.settings import Settings


@lru_cache
def get_settings() -> Settings:
    """Load and cache the Settings instance.

    Returns:
        Settings: Cached Settings instance
    """
    return Settings()


def get_auth_settings():
    """Retrieve authentication-specific settings.

    Returns:
        AuthSettings: Authentication configuration settings.
    """
    return get_settings().auth


def get_postgres_settings():
    """Retrieve PostgreSQL database settings.

    Returns:
        PostgresSettings: PostgreSQL database configuration
        settings.
    """
    return get_settings().db.postgres


def get_redis_settings():
    """Retrieve Redis database settings.

    Returns:
        RedisSettings: Redis database configuration settings.
    """
    return get_settings().db.redis
