from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any, Generic, TypeVar

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from pyback.api.dependencies.common import get_postgres_settings


T = TypeVar("T", bound=SQLModel)


class PostgresDatabase(Generic[T]):
    """A generic asynchronous PostgreSQL database interface.

    This class provides a high-level interface for interacting with a PostgreSQL
    database using SQLModel and SQLAlchemy's async functionality. It supports
    generic typing for type-safe database operations.

    Type Parameters:
        T: A type variable bound to SQLModel, representing the model type for
            database operations.

    Attributes:
        _dsn (str): Database connection string.
        _debug (bool): Flag to enable debug logging.
        _engine (Any): SQLAlchemy async engine instance.
        _async_session (async_sessionmaker[AsyncSession] | None): Session factory for
            creating database sessions.
    """

    def __init__(
        self,
        dsn: str,
        debug: bool = False,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
        pool_pre_ping: bool = True,
    ) -> None:
        """Initialize the PostgreSQL database interface.

        Args:
            dsn (str): Database connection string (Data Source Name).
            debug (bool, optional): Enable debug mode for SQL query logging.
                Defaults to False.
            pool_size (int, optional): The size of the connection pool.
                Defaults to 20.
            max_overflow (int, optional): The maximum number of connections to allow
                beyond the pool_size. Defaults to 10.
            pool_timeout (int, optional): Seconds to wait before timing out on getting
                a connection from the pool. Defaults to 30.
            pool_recycle (int, optional): Seconds after which a connection is recycled.
                Defaults to 1800 (30 minutes).
            pool_pre_ping (bool, optional): If True, emits a test statement on checkout
                to verify the connection is still viable. Defaults to True.
        """
        self._dsn: str = dsn
        self._debug: bool = debug
        self._engine: Any = None
        self._async_session: async_sessionmaker[AsyncSession] | None = None

        # Connection pool settings
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._pool_timeout = pool_timeout
        self._pool_recycle = pool_recycle
        self._pool_pre_ping = pool_pre_ping

        # Statistics
        self._connection_attempts = 0
        self._connection_errors = 0

    async def connect(self) -> None:
        """Establish a connection to the PostgreSQL database.

        This method initializes the database engine and session maker, and tests
        the connection by executing a simple query.

        Raises:
            Exception: If connection initialization fails.
        """
        try:
            logger.info("Initializing PostgreSQL connection...")
            self._connection_attempts += 1

            # Create the async engine with pool configuration
            self._engine = create_async_engine(
                self._dsn,
                echo=self._debug,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                pool_timeout=self._pool_timeout,
                pool_recycle=self._pool_recycle,
                pool_pre_ping=self._pool_pre_ping,
            )

            # Create the async session maker
            self._async_session = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False,
            )

            # Test the connection
            async with self._engine.connect() as conn:
                await conn.execute(select(1))

            logger.info("PostgreSQL connection initialized successfully.")

        except Exception as e:
            self._connection_errors += 1
            logger.error(f"Error initializing PostgreSQL connection: {e}")
            raise

    async def disconnect(self) -> None:
        """Close the database connection and dispose of the engine.

        This method should be called when shutting down the application to properly
        clean up database resources.

        Raises:
            Exception: If closing the connection fails.
        """
        if self._engine is not None:
            try:
                logger.info("Closing PostgreSQL connection...")
                await self._engine.dispose()
                logger.info("PostgreSQL connection closed successfully.")
            except Exception as e:
                logger.error(f"Error closing PostgreSQL connection: {e}")
                raise

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Context manager for database sessions.

        This provides a convenient way to handle sessions using `async with` syntax.
        The session is automatically closed when the context manager exits.

        Yields:
            AsyncSession: An asynchronous database session.

        Raises:
            ConnectionError: If the database is not initialized.
        """
        if self._async_session is None:
            raise ConnectionError("Database is not initialized. Call connect() first.")

        session = self._async_session()
        try:
            yield session
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """Check if the database connection is healthy.

        Returns:
            bool: True if the connection is healthy, False otherwise.
        """
        if self._engine is None:
            return False

        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get database connection statistics.

        Returns:
            dict[str, Any]: Dictionary with connection statistics.
        """
        stats = {
            "connection_attempts": self._connection_attempts,
            "connection_errors": self._connection_errors,
        }

        if self._engine is not None:
            pool = self._engine.pool
            stats.update(
                {
                    "pool_size": self._pool_size,
                    "connections_in_use": pool.size(),
                    "overflow_connections": pool.overflow(),
                },
            )

        return stats

    async def fetch_one(
        self,
        model: type[T],
        *conditions: Any,
        session: AsyncSession | None = None,
    ) -> T | None:
        """Fetch a single record from the database that matches the given conditions.

        Args:
            model (type[T]): The SQLModel class representing the database table.
            *conditions (Any): Variable number of filter conditions.
            session (Optional[AsyncSession], optional): Optional session to use.
                If None, a new session will be created. Defaults to None.

        Returns:
            T | None: The matching record if found, None otherwise.

        Raises:
            ConnectionError: If the database is not initialized.
        """
        if self._async_session is None:
            raise ConnectionError("Database is not initialized. Call connect() first.")

        if session is not None:
            # Use provided session
            query = select(model).filter(*conditions)
            result = await session.exec(query)
            record = result.one_or_none()
            return record[0] if record else None
        else:
            # Create new session
            async with self.session() as session:
                query = select(model).filter(*conditions)
                result = await session.exec(query)
                record = result.one_or_none()
                return record[0] if record else None

    async def fetch_all(
        self,
        model: type[T],
        *conditions: Any,
        session: AsyncSession | None = None,
    ) -> list[T]:
        """Fetch all records from the database that match the given conditions.

        Args:
            model (type[T]): The SQLModel class representing the database table.
            *conditions (Any): Variable number of filter conditions.
            session (Optional[AsyncSession], optional): Optional session to use.
                If None, a new session will be created. Defaults to None.

        Returns:
            list[T]: List of matching records.

        Raises:
            ConnectionError: If the database is not initialized.
        """
        if self._async_session is None:
            raise ConnectionError("Database is not initialized. Call connect() first.")

        if session is not None:
            # Use provided session
            query = select(model).filter(*conditions)
            result = await session.exec(query)
            records = result.all()
            return [record[0] for record in records]
        else:
            # Create new session
            async with self.session() as session:
                query = select(model).filter(*conditions)
                result = await session.exec(query)
                records = result.all()
                return [record[0] for record in records]

    async def execute_with_transaction(
        self,
        operation: Annotated[str, text],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a database operation within a transaction.

        This method supports both raw SQL queries and method calls. For SQL operations,
        it handles SELECT, UPDATE, and DELETE operations differently.

        Args:
            operation (str | text): SQL query string or method name to execute.
            *args (Any): Positional arguments for the operation.
            **kwargs (Any): Keyword arguments for the operation.

        Returns:
            Any: Result of the operation. For SELECT queries, returns all matching
                records. For UPDATE/DELETE queries, returns the number of affected rows.

        Raises:
            ConnectionError: If the database is not initialized.
            SQLAlchemyError: If a database error occurs.
            Exception: If any other unexpected error occurs.
        """
        if not self._async_session:
            raise ConnectionError("Database is not initialized. Call connect() first.")

        async with self.session() as session:
            try:
                async with session.begin():
                    if isinstance(operation, str) and hasattr(self, operation):
                        # Execute method if operation is a method name
                        result = await getattr(self, operation)(
                            session,
                            *args,
                            **kwargs,
                        )
                    else:
                        # Execute raw SQL query with parameters
                        if kwargs.get("parameters"):
                            stmt = text(operation).params(**kwargs["parameters"])
                        else:
                            stmt = text(operation)

                        result = await session.exec(stmt)

                        # UPDATE/DELETE. Return the number of rows affected
                        if operation.upper().startswith(("UPDATE", "DELETE")):
                            return result.rowcount

                        # For SELECT operations, return the results
                        return result.all() if "SELECT" in operation.upper() else result

                return result

            except SQLAlchemyError as e:
                logger.error(f"Database error occurred: {e}")
                raise
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                raise

    async def add(self, model: T, session: AsyncSession | None = None) -> T:
        """Add a new record to the database.

        Args:
            model (T): The model instance to add to the database.
            session (Optional[AsyncSession], optional): Optional session to use.
                If None, a new session will be created and transaction managed.
                Defaults to None.

        Returns:
            T: The added model instance with refreshed data from the database.

        Raises:
            ConnectionError: If the database is not initialized.
        """
        if self._async_session is None:
            raise ConnectionError("Database is not initialized. Call connect() first.")

        if session is not None:
            # Use provided session (caller manages transaction)
            session.add(model)
            await session.flush()  # Flush but don't commit - caller manages transaction
            await session.refresh(model)
            return model
        else:
            # Create new session and manage transaction
            async with self.session() as session:
                session.add(model)
                await session.commit()
                await session.refresh(model)
                return model

    async def update(self, model: T, session: AsyncSession | None = None) -> T:
        """Update an existing record in the database.

        Args:
            model (T): The model instance to update.
            session (Optional[AsyncSession], optional): Optional session to use.
                If None, a new session will be created and transaction managed.
                Defaults to None.

        Returns:
            T: The updated model instance with refreshed data from the database.

        Raises:
            ConnectionError: If the database is not initialized.
        """
        if self._async_session is None:
            raise ConnectionError("Database is not initialized. Call connect() first.")

        if session is not None:
            # Use provided session (caller manages transaction)
            session.add(model)
            await session.flush()
            await session.refresh(model)
            return model
        else:
            # Create new session and manage transaction
            async with self.session() as session:
                session.add(model)
                await session.commit()
                await session.refresh(model)
                return model

    async def delete(self, model: T, session: AsyncSession | None = None) -> None:
        """Delete a record from the database.

        Args:
            model (T): The model instance to delete.
            session (Optional[AsyncSession], optional): Optional session to use.
                If None, a new session will be created and transaction managed.
                Defaults to None.

        Raises:
            ConnectionError: If the database is not initialized.
        """
        if self._async_session is None:
            raise ConnectionError("Database is not initialized. Call connect() first.")

        if session is not None:
            # Use provided session (caller manages transaction)
            await session.delete(model)
            await session.flush()  # Flush but don't commit - caller manages transaction
        else:
            # Create new session and manage transaction
            async with self.session() as session:
                await session.delete(model)
                await session.commit()


# Create database instance with improved pool configuration
pgdb: PostgresDatabase = PostgresDatabase(
    str(get_postgres_settings().postgres_dsn),
    get_postgres_settings().DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
