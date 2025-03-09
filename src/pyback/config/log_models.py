from __future__ import annotations
from enum import Enum

from pydantic import BaseModel, ConfigDict


class LogLevel(str, Enum):
    """Valid logging levels."""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BaseConfig(BaseModel):
    """Base configuration model with common settings."""

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ConsoleConfig(BaseConfig):
    """Console logging configuration."""

    enabled: bool = True
    format: str
    colorize: bool = True
    diagnose: bool = True
    backtrace: bool = True


class FileConfig(BaseConfig):
    """File logging configuration."""

    enabled: bool = False
    format: str
    path: str = "logs/app.log"
    rotation: str = "10 MB"
    retention: str = "1 week"
    compression: str = "zip"


class JsonConfig(BaseConfig):
    """JSON file logging configuration."""

    enabled: bool = False
    path: str = "logs/app.json"
    rotation: str = "10 MB"
    retention: str = "1 week"
    compression: str = "zip"


class LoggingConfig(BaseConfig):
    """Main logging configuration."""

    level: LogLevel = LogLevel.INFO
    console: ConsoleConfig
    file: FileConfig
    json_file: JsonConfig
