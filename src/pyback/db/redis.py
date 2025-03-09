from fastapi_limiter import FastAPILimiter
from loguru import logger
import redis.asyncio as redis

from pyback.api.dependencies.common import get_redis_settings


class RedisDatabase:
    """An asynchronous Redis database interface for managing connections and operations.

    This class provides a high-level, asynchronous interface for interacting with
    a Redis database, supporting connection management, rate limiting initialization,
    and database cleaning operations.

    Attributes:
        _dsn (str): Redis connection string (Data Source Name).
        _client (Optional[redis.Redis]): Asynchronous Redis client instance.
    """

    def __init__(self, dsn: str) -> None:
        """Initialize the Redis database interface.

        Args:
            dsn (str): Redis connection string (Data Source Name).
        """
        self._dsn: str = dsn
        self._client = None

    async def connect(self) -> None:
        """Establish a connection to the Redis database and initialize FastAPILimiter.

        This method initializes the Redis client, tests the connection, and sets up
        the FastAPILimiter for rate limiting functionality.

        Raises:
            redis.ConnectionError: If unable to connect to Redis.
            redis.TimeoutError: If the connection attempt times out.
            redis.RedisError: For general Redis-related errors.
            Exception: For any other unexpected errors during initialization.
        """
        try:
            logger.info("Initializing Redis connection...")
            self._client = redis.from_url(
                self._dsn,
                decode_responses=True,
                socket_timeout=1,
                socket_connect_timeout=1,
                retry_on_timeout=True,
            )
            # Test the connection
            if self._client:
                await self._client.ping()
            logger.info("Redis connection initialized successfully.")
            await FastAPILimiter.init(self._client)
            logger.info("FastAPILimiter initialized successfully.")

        except redis.ConnectionError as e:
            logger.error("Failed to connect to Redis: {}", e)
            raise
        except redis.TimeoutError as e:
            logger.error("Redis connection timed out: {}", e)
            raise
        except redis.RedisError as e:
            logger.error("Redis error: {}", e)
            raise
        except Exception as e:
            logger.error(f"Error initializing Redis connection: {e}")
            raise

    async def disconnect(self) -> None:
        """Close the Redis connection and shut down FastAPILimiter.

        This method should be called when shutting down the application to properly
        clean up Redis resources and close connections.

        Raises:
            redis.ConnectionError: If there's an error closing the Redis connection.
            redis.RedisError: For general Redis-related errors during disconnection.
            redis.TimeoutError: If the disconnection attempt times out.
            Exception: For any other unexpected errors during disconnection.
        """
        if self._client is not None:
            try:
                await FastAPILimiter.close()
                await self._client.aclose()
                logger.info("Redis connection closed")
            except redis.ConnectionError as e:
                logger.error("Error closing Redis connection: {}", e)
                raise
            except redis.RedisError as e:
                logger.error("Redis error: {}", e)
                raise
            except redis.TimeoutError as e:
                logger.error("Redis connection timed out: {}", e)
                raise
            except Exception as e:
                logger.error("Error closing Redis connection: {}", e)
                raise

    async def clean(self) -> None:
        """Flush all data from the Redis database.

        This method removes all keys from the current database, effectively
        clearing all stored data.

        Raises:
            Exception: If there's an error flushing the Redis database.
        """
        if self._client is not None:
            try:
                await self._client.flushall()
            except Exception as e:
                logger.error("Error flushing Redis database: {}", e)
                raise


redis_db: RedisDatabase = RedisDatabase(str(get_redis_settings().redis_dsn))
"""
A global instance of the RedisDatabase class, initialized with the Redis connection
string obtained from the application settings.
"""
