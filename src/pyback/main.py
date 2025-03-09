from contextlib import asynccontextmanager
import sys

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from loguru import logger
import uvicorn

from pyback.api.dependencies.common import get_settings
from pyback.api.middleware.processing_time import ProcessingTimeMiddleware
from pyback.api.models.common import Tags
from pyback.api.routes import auth, root, users
from pyback.config.logging_config import initialize_logging
from pyback.core.exceptions import (
    BadRequestError,
    ConflictError,
    ExpiredTokenError,
    InternalError,
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundError,
    UnauthorizedError,
    ValidationExceptionError,
    create_auth_error_handler,
    create_error_handler,
)
from pyback.db.postgres import pgdb
from pyback.db.redis import redis_db


def create_application() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Async FastAPI PostgreSQL Backend",
        description="",
        summary="Template for building FastAPI applications with PostgreSQL and Redis",
        version="0.0.1",
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
        root_path="/api/v1",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.add_middleware(ProcessingTimeMiddleware)

    # Include routers
    app.include_router(root.router, tags=[Tags.general])
    app.include_router(auth.router, prefix="/auth", tags=[Tags.auth])
    app.include_router(users.router, prefix="/users", tags=[Tags.users])

    # Register exception handlers
    register_exception_handlers(app)

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    try:
        initialize_logging()
        logger.info("🚀 Starting up application...")
        await pgdb.connect()
        logger.info("Database connected")
        await redis_db.connect()
        logger.info("Redis connected")
        yield
    except Exception as e:
        logger.exception("Error during startup: {}", e)
        raise
    finally:
        logger.info("Shutting down application...")
        await pgdb.disconnect()
        await redis_db.disconnect()


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for the application.

    Args:
        app: FastAPI application instance
    """
    exception_handlers = {
        InvalidTokenError: create_auth_error_handler(status.HTTP_401_UNAUTHORIZED),
        ExpiredTokenError: create_auth_error_handler(status.HTTP_401_UNAUTHORIZED),
        InvalidCredentialsError: create_auth_error_handler(
            status.HTTP_401_UNAUTHORIZED,
        ),
        UnauthorizedError: create_error_handler(status.HTTP_403_FORBIDDEN),
        BadRequestError: create_error_handler(status.HTTP_400_BAD_REQUEST),
        NotFoundError: create_error_handler(status.HTTP_404_NOT_FOUND),
        ConflictError: create_error_handler(status.HTTP_409_CONFLICT),
        ValidationExceptionError: create_error_handler(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        InternalError: create_error_handler(status.HTTP_500_INTERNAL_SERVER_ERROR),
    }

    for exception_class, handler in exception_handlers.items():
        app.add_exception_handler(exception_class, handler)


def get_application() -> FastAPI:
    """Get the configured FastAPI application instance.

    Returns:
        Configured FastAPI application
    """
    try:
        settings = get_settings()
        logger.info(f"Application settings loaded successfully: {settings}")
        return create_application()
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        sys.exit(1)


app = get_application()


def main():
    """Run the FastAPI application using Uvicorn server."""
    settings = get_settings()
    uvicorn.run(
        "pyback.main:app",
        host=settings.app.SERVER_HOST,
        port=settings.app.SERVER_PORT,
        reload=settings.app.SERVER_RELOAD,
        log_level=settings.app.SERVER_LOG_LEVEL,
    )


if __name__ == "__main__":
    main()
