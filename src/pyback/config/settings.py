from collections.abc import Callable
from pathlib import Path
import tomllib
from tomllib import TOMLDecodeError
from typing import Any, Final, Literal

from loguru import logger
from pydantic import BaseModel, Field, PostgresDsn, RedisDsn, SecretStr, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


SettingsDict = dict[str, Any]
"""Type alias for a dictionary containing settings key-value pairs."""

TomlLoader = Callable[[], dict[str, Any]]
"""Type alias for a function that loads and returns TOML configuration."""

ServerLogLevel = Literal["debug", "info", "warning", "error", "critical"]
"""Type definition for valid server log levels."""


class AuthSettings(BaseModel):
    """Settings for authentication configuration.

    Attributes:
        JWT_SECRET: Secret key for JWT token generation and validation.
        JWT_ALGORITHM: Algorithm used for JWT token encryption, defaults to "HS256".
        JWT_SESSION_TTL_MIN: Session time-to-live in minutes, must be greater than 0.
        JWT_EXPIRE_MINUTES: Optional JWT token expiration time in minutes.
    """

    JWT_SECRET: SecretStr | None = None
    JWT_ALGORITHM: str = "HS256"
    JWT_SESSION_TTL_MIN: int = Field(
        default=60,
        description="Default session time-to-live in minutes",
        gt=0,
    )
    JWT_EXPIRE_MINUTES: int | None = None


class AppSettings(BaseModel):
    """Settings for application server configuration.

    Attributes:
        SERVER_HOST: Host address for the server, defaults to "app".
        SERVER_PORT: Port number for the server, defaults to 8000.
        SERVER_LOG_LEVEL: Logging level for the server, defaults to "info".
        SERVER_RELOAD: Flag to enable auto-reload for development, defaults to False.
    """

    SERVER_HOST: str = "app"
    SERVER_PORT: int = 8000
    SERVER_LOG_LEVEL: str = "info"
    SERVER_RELOAD: bool = False

    @field_validator("SERVER_LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validates that the log level is one of the allowed values.

        Args:
            v (str): The log level value to validate.

        Returns:
            str: The normalized (lowercase) log level.

        Raises:
            ValueError: If the log level is not one of the allowed values.
        """
        normalized = v.lower()
        if normalized not in ("debug", "info", "warning", "error", "critical"):
            raise ValueError(f"Invalid log level: {v}")
        return normalized


class PostgresSettings(BaseModel):
    """Settings for PostgreSQL database configuration.

    Attributes:
        POSTGRES_HOST: Database host address, defaults to "db".
        POSTGRES_PORT: Database port number, defaults to 5432.
        POSTGRES_DB: Database name, defaults to "postgres".
        PGUSER: Database user name, defaults to "postgres".
        PGPASSWORD: Database password.
        DEBUG: Enable debug mode for database operations.
    """

    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    PGUSER: str = "postgres"
    PGPASSWORD: SecretStr | None = None
    DEBUG: bool = False

    @property
    def postgres_dsn(self) -> PostgresDsn:
        """Constructs and returns the PostgreSQL connection string.

        Returns:
            PostgresDsn: A complete PostgreSQL connection URL including credentials.
        """
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.PGUSER,
            password=self.PGPASSWORD.get_secret_value() if self.PGPASSWORD else None,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )


class RedisSettings(BaseModel):
    """Settings for Redis configuration.

    Attributes:
        REDIS_HOST: Redis server host address, defaults to "redis".
        REDIS_PORT: Redis server port number, defaults to 6379.
        REDIS_DB: Redis database number, defaults to 0.
    """

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def redis_dsn(self) -> RedisDsn:
        """Constructs and returns the Redis connection string.

        Returns:
            RedisDsn: A complete Redis connection URL.
        """
        return RedisDsn.build(
            scheme="redis",
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            path=f"/{self.REDIS_DB}",
        )


class DBSettings(BaseModel):
    """Settings for database configuration.

    Attributes:
        postgres (PostgresSettings): PostgreSQL database configuration settings.
        redis (RedisSettings): Redis database configuration settings.
    """

    postgres: PostgresSettings = Field(default_factory=lambda: PostgresSettings())
    redis: RedisSettings = Field(default_factory=lambda: RedisSettings())


class Settings(BaseSettings):
    """Application settings with strong typing and validation.

    Loads configuration from environment variables, .env file, and config.toml
    with a defined priority order.
    """

    # Core paths
    BASE_DIR: Final[Path] = Path(__file__).resolve().parents[3]
    _cfg_toml_path: Final[Path] = BASE_DIR / "config.toml"
    _dot_env_path: Final[Path] = BASE_DIR / ".env"

    # Pydantic configuration
    model_config = SettingsConfigDict(
        env_file=_dot_env_path,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Auth settings
    JWT_SECRET: SecretStr

    # Database settings
    PGPASSWORD: SecretStr

    app: AppSettings = Field(
        default_factory=lambda: AppSettings(),
        description="Server app configuration",
    )

    auth: AuthSettings = Field(
        default_factory=lambda: AuthSettings(),
        description="Security configuration",
    )

    db: DBSettings = Field(
        default_factory=DBSettings,
        description="Database configuration",
    )

    def model_post_init(self, _context) -> None:
        """Post-initialization hook to set up sensitive settings.

        This method is called after the initial model initialization and is responsible
        for setting up sensitive configuration values like JWT secret and database
        passwords. It ensures that these sensitive values are properly set from
        environment variables or other sources.

        Args:
            _context: Context passed during initialization (unused in this
                      implementation).
        """
        if hasattr(self, "auth"):
            self.auth.JWT_SECRET = SecretStr(
                self.JWT_SECRET.get_secret_value(),
            )
        if hasattr(self.db, "postgres"):
            self.db.postgres.PGPASSWORD = SecretStr(self.PGPASSWORD.get_secret_value())

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...] | Callable[[], dict[str, Any]]:
        """Customize and prioritize configuration sources for settings.

        This method defines the order and sources of configuration settings,
        allowing for a flexible and hierarchical configuration loading process.
        The priority of configuration sources is as follows:
        1. Initialization settings (highest priority)
        2. Environment variables
        3. TOML configuration file
        4. Dotenv file
        5. File secret settings (lowest priority)

        Args:
            settings_cls (type[BaseSettings]): The settings class being configured.
            init_settings (PydanticBaseSettingsSource): Passed during initialization.
            env_settings (PydanticBaseSettingsSource): Environment variable settings.
            dotenv_settings (PydanticBaseSettingsSource): .env file settings.
            file_secret_settings (PydanticBaseSettingsSource): File-based secrets.

        Returns:
            tuple[PydanticBaseSettingsSource, ...] | Callable[[], dict[str, Any]]:
                A tuple of settings sources or a callable that returns a configuration
                dictionary.
        """

        def load_toml_settings() -> dict[str, Any]:
            try:
                toml_path = cls._cfg_toml_path
                with toml_path.open(mode="rb") as f:
                    config = tomllib.load(f)
                logger.info(f"Loaded configuration from file: {toml_path}")
                return config
            except TOMLDecodeError as e:
                logger.error(f"Error decoding TOML config file: {e}")
                raise
            except FileNotFoundError:
                logger.error(f"Config file not found at {toml_path}")
                raise
            except Exception as e:
                logger.error(f"Error loading TOML config file: {e}")
                raise

        return (
            init_settings,
            env_settings,
            load_toml_settings,
            dotenv_settings,
            file_secret_settings,
        )
