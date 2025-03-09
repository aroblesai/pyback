from datetime import datetime
import json
from pathlib import Path
import sys
import tomllib
from typing import Any, TypedDict

from loguru import logger
from pydantic import ValidationError

from pyback.api.dependencies.common import get_settings

from .log_models import LoggingConfig


class LogLevel(TypedDict):
    """Represents a log level with its properties."""

    name: str
    no: int
    icon: str


class LogProcess(TypedDict):
    """Represents a process in logging context."""

    name: str


class LogThread(TypedDict):
    """Represents a thread in logging context."""

    name: str


class LogFile(TypedDict):
    """Represents a file in logging context."""

    name: str


class LogRecord(TypedDict, total=False):
    """Represents a complete log record with all possible fields."""

    level: LogLevel
    time: datetime
    message: str
    file: LogFile | None
    module: str | None
    function: str | None
    line: int | None
    extra: dict[str, Any] | None
    exception: Any | None
    process: LogProcess | None
    thread: LogThread | None


def load_log_config(config_path: Path) -> LoggingConfig | None:
    """Load logging configuration from a TOML file.

    Args:
        config_path: Path to the TOML configuration file

    Returns:
        LoggingConfig object if successful, None otherwise
    """
    if not config_path.is_file():
        logger.info(
            f"Config file not found: {config_path}, using default logging settings",
        )
        return None
    try:
        with config_path.open(mode="rb") as f:
            data = tomllib.load(f)
        config = data.get("logging", {})
    except tomllib.TOMLDecodeError as e:
        logger.error(f"Error decoding TOML config file: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading logging settings from config file: {e}")
        return None

    try:
        return LoggingConfig.model_validate(config)
    except ValidationError as e:
        logger.error(f"Failed to set up log config: {e}")
        return None


def serialize_record(record: dict) -> str:
    """Serialize a log record to a JSON string.

    Args:
        record (dict): The log record to serialize.

    Returns:
        str: A JSON string representation of the log record.
    """
    subset = {
        "level": getattr(record["level"], "name", None),
        "level_no": getattr(record["level"], "no", None),
        "level_icon": getattr(record["level"], "icon", None),
        "time": record.get("time", datetime.now()).isoformat(),
        "timestamp": record.get("time", datetime.now()).timestamp(),
        "message": record.get("message"),
        "file": getattr(record["file"], "name", None),
        "module": record.get("module"),
        "function": record.get("function"),
        "line": record.get("line"),
        "context": record.get("extra"),
        "exception": record.get("exception"),
        "process": getattr(record["process"], "name", None),
        "thread": getattr(record["thread"], "name", None),
    }
    return json.dumps(subset, ensure_ascii=False)


def custom_formatter(record: dict) -> str:
    """Custom formatter for log records.

    This formatter converts the log record to a JSON string and escapes curly braces
    to prevent issues with string formatting.

    Args:
        record (dict): The log record to format.

    Returns:
        str: A formatted string with escaped curly braces and a newline.
    """
    json_str = serialize_record(record)
    safe_str = json_str.replace("{", "{{").replace("}", "}}")
    return safe_str + "\n"


def setup_logging(config: LoggingConfig | None) -> None:
    """Set up logging configuration based on the provided config.

    Args:
        config: LoggingConfig object containing logging configuration
    """
    if config is None:
        return

    # Remove all existing handlers.
    logger.remove()

    # Add console sink if enabled.
    if config.console.enabled:
        logger.add(
            sys.stdout,
            level=config.level.value,
            colorize=config.console.colorize,
            format=config.console.format,
            diagnose=config.console.diagnose,
            backtrace=config.console.backtrace,
            enqueue=True,
        )

    # Add file sink if enabled.
    if config.file.enabled:
        logger.add(
            config.file.path,
            level=config.level.value,
            format=config.file.format,
            rotation=config.file.rotation,
            retention=config.file.retention,
            compression=config.file.compression,
            encoding="utf-8",
            enqueue=True,
        )

    # Add JSON sink if enabled.
    if config.json_file.enabled:
        logger.add(
            config.json_file.path,
            level=config.level.value,
            format=custom_formatter,
            rotation=config.json_file.rotation,
            retention=config.json_file.retention,
            compression=config.json_file.compression,
            encoding="utf-8",
            enqueue=True,
        )


def initialize_logging() -> None:
    """Initialize logging system with configuration from settings."""
    log_config = load_log_config(get_settings()._cfg_toml_path)
    setup_logging(log_config)
    logger.info("Logging initialized")
