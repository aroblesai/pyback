# Pyback

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Pyback** (v0.1.0) is a modern asynchronous backend boilerplate built with **FastAPI**, **PostgreSQL** and **SQLAlchemy**. It follows industry best practices and comes preconfigured with essential features for building robust and scalable APIs.

_Note: This project requires Python 3.12+ and uses `uv` as the package manager for improved dependency resolution and installation speed._

## Features

- FastAPI: High-performance async framework for building APIs with automatic OpenAPI documentation
- Pydantic: Type-safe data validation and settings management
- SQLAlchemy: Powerful ORM with async support for flexible database operations
- Alembic: Automatic database migrations to manage schema changes
- UV Package Manager: Modern Python package manager for faster dependency resolution
- Clean Architecture: Separation of concerns for better maintainability and testing
- JWT Authentication: Secure authentication system with protected routes
- Docker Support: Easy containerization for consistent development and deployment
- CI/CD Pipeline: GitHub Actions workflows for continuous integration
- Pre-commit Hooks: Automated code quality checks before commits
- Rate Limiting: Protection against abuse and resource overuse using Redis
- MkDocs: Comprehensive documentation system

## Quick Start

```bash
# Clone and enter directory
git clone https://github.com/aroblesai/pyback.git

cd pyback

# Initialize the virtual environment with uv
uv venv

# Copy the example environment file and configure it
cp .env.example .env

# Install the package
make install

# Start the application with Docker
make docker-up

# Access the API documentation
# Open http://localhost:8000/docs
```

## Getting Started

### 1. Initial Setup

First, ensure you have the following prerequisites installed:

- Python 3.12+
- Docker and Docker Compose
- UV package manager

1. Install uv (follow instructions [here](https://docs.astral.sh/uv/#getting-started))

2. Clone the repository and set up your development environment:

```bash
# Clone the repository
git clone https://github.com/aroblesai/pyback.git
cd pyback
```

and then initialize the environment:

```bash
uv venv
```

The project uses two main configuration files:

- **Environment Variables (.env)**:

  ```bash
  # Copy the example environment file
  cp .env.example .env

  # Open .env and configure these essential variables:

  # App
  SERVER_PORT=8000

  # Postgres
  POSTGRES_PORT=5432
  POSTGRES_DB=pyback
  POSTGRES_USER=postgres
  POSTGRES_PASSWORD=Password1234
  PGUSER=pybackuser
  PGPASSWORD=Password1234

  # PGAdmin4
  PGADMIN_PORT=8080
  PGADMIN_DEFAULT_EMAIL=pybackuser@pyback.com
  PGADMIN_DEFAULT_PASSWORD=Password1234

  # Redis
  REDIS_PORT=6379

  # Authentication
  JWT_SECRET=mysecretkey
  ```

- **Application Configuration (config.toml)**:

  ```bash
  # Edit config.toml to set up your application.
  # Make sure these values are consistent with your .env file:

  [app]
  SERVER_PORT = 8000

  [db.postgres]
  POSTGRES_PORT = 5432
  POSTGRES_DB = "pyback"
  PGUSER = "pybackuser"

  [db.redis]
  REDIS_PORT = 6379
  ```

> 💡 **Important**:
>
> Normally passwords and secrets should not be stored in the config file. They should be stored in environment variables or a secrets manager.
> The pair `POSTGRES_USER` and `POSTGRES_PASSWORD` are used to create the database and the user. The pair `PGUSER` and `PGPASSWORD` are used to connect to the database.
> Make sure port values and database parameters are consistent with your `.env` file.

3. Install package

```bash
# Install package in regular mode
uv pip install -e .
```

or

```bash
make install
```

4. (Optional) Install dev dependencies and setup pre-commit hooks:

```bash
uv pip install -e ".[dev]"
uv sync --all-extras --frozen
uv run pre-commit install
```

or

```bash
make setup
```

### 2. Run Application

Start the FastAPI application database and other services using Docker Compose:

```bash
docker compose -f docker-compose.yml up -d
```

or

```bash
make docker-up
```

### 3. Verify Application

1. **Check Application Logs**:

```bash
# Check logs for all services
make docker-logs
```

2. **Check API Documentation**:

   - Open http://localhost:8000/docs for Swagger UI

### 4. Database Setup

Creating the PostgreSQL migrations:

1. Make changes to your database models
2. Generate migration:

```bash
docker compose exec app uv run alembic revision --autogenerate -m "Initial migration"
```

or

```bash
# Initialize migration with message
make db-revision
```

> ✍ **Note**:
>
> Migrations will be automatically applied when you start the application using Docker Compose so there is no need to run `uv run alembic upgrade head` manually.

### 5. Run Tests

Start the test and other services using Docker Compose:

```bash
docker compose up --build --abort-on-container-exit --exit-code-from test
```

or

```bash
make test
```

## Project Structure

```yaml
docs/                           # Documentation directory
src/                            # Source code
│
├── pyback/                     # Main package
│   ├── api/                    # API module
│   │   ├── dependencies/       # API dependencies
│   │   ├── middleware/         # API middleware
│   │   ├── models/             # API models
│   │   ├── routes/             # API routes
│   │
│   ├── config/                 # Configuration module
│   ├── core/                   # Core functionality
│   ├── db/                     # Database module
│   │   ├── init/               # DB initialization
│   │   ├── migrations/         # Alembic migrations
│   │   ├── models/             # DB models
│   │   ├── repositories/       # Repository pattern implementations
│   │   ├── postgres.py         # PostgreSQL connection
│   │   └── redis.py            # Redis connection
│   │
│   └── services/               # Service layer
│       └── main.py             # Main service
│
├── tests/                      # Test directory
│
├── .dockerignore               # Docker ignore file
├── .env                        # Environment variables
├── .env.example                # Example environment file
├── .gitattributes              # Git attributes
├── .gitignore                  # Git ignore file
├── .pre-commit-config.yaml     # Pre-commit hooks configuration
├── .python-version             # Python version (pyenv)
├── alembic.ini                 # Alembic configuration
├── config.toml                 # Application configuration
├── docker-compose.override.yml # Docker Compose override for testing
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker build instructions
├── Dockerfile.test             # Docker file for testing
├── entrypoint.sh               # Docker entrypoint script
├── LICENSE                     # Project license
├── Makefile                    # Project build/management commands
├── mkdocs.yml                  # MkDocs configuration
├── pyproject.toml              # Python project metadata/dependencies
├── README.md                   # Project documentation
└── uv.lock                     # uv package manager lock file
```

Pyback follows a clean architecture pattern, promoting separation of concerns and maintainability:

1. **API Layer** (`src/pyback/api/`):

   - Routes: Define API endpoints and HTTP methods.
   - Dependencies: Manage request dependencies and middleware.
   - Models: Pydantic models for request/response serialization.

2. **Service Layer** (`src/pyback/services/`):

   - Implement business logic.
   - Coordinate between API and data access layers.

3. **Data Access Layer** (`src/pyback/db/`):

   - Models: SQLAlchemy ORM models.
   - Repositories: Database operations and queries.
   - Migrations: Alembic migration scripts.

4. **Core** (`src/pyback/core/`):

   - Shared utilities, exceptions, and core functionality.

This layered approach ensures:

- Clear separation between API contracts, business logic, and data access.
- Easier testing and mocking of components.
- Flexibility to change underlying technologies with minimal impact.

## Best Practices and Optimization

### Code Quality

- Follow PEP 8 style guide and use `ruff` for consistent code formatting
- Use type hints and `mypy` for static type checking
- Write comprehensive docstrings for modules, classes, and functions
- Keep functions small and focused on a single responsibility
- Use meaningful variable and function names

### Performance Optimization

#### Database Optimization

- Use SQLAlchemy's asyncio extensions for non-blocking database operations
- Implement database indexing for frequently queried fields
- Use connection pooling to manage database connections efficiently

## Contributing

We welcome contributions to Pyback! Here's how you can help:

1. **Fork the Repository**

   - Create a fork of this repository
   - Clone your fork locally

2. **Create a Branch**

   - Create a new branch for your feature/fix
   - Use a meaningful branch name (e.g., `feature/new-auth-method` or `fix/database-connection`)

3. **Make Your Changes**

   - Write clean, documented code
   - Follow the project's code style
   - Add tests for new features
   - Update documentation as needed

4. **Test Your Changes**

   - Run the test suite: `make test`
   - Run linting: `make lint`
   - Run type checking: `make typecheck`

5. **Submit a Pull Request**
   - Push your changes to your fork
   - Create a pull request from your branch to our main branch
   - Provide a clear description of the changes
   - Reference any related issues

### Development Guidelines

- Write tests for new features
- Update documentation for significant changes
- Follow the project's code style
- Keep pull requests focused on a single change
- Add appropriate error handling
- Include type hints for new code

## Troubleshooting

### Common Issues and Solutions

1. **Database Connection Errors**:

   - Ensure PostgreSQL is running: `docker compose ps`
   - Check database credentials in `.env`
   - Verify network connectivity to the database container

2. **Migration Failures**:

   - Ensure you're running migrations from the project root
   - Check for conflicting migration versions

3. **API Errors**:

   - Check FastAPI logs for detailed error messages
   - Verify API request format matches expected schema
   - Ensure all required environment variables are set

4. **Docker Issues**:
   - Rebuild containers after significant changes: `make docker-clean && make docker-up-build`
   - Check Docker logs: `make docker-logs`
   - Ensure Docker daemon is running and you have necessary permissions

### Debugging Tips

1. Use FastAPI's built-in debugging tools by setting the desired logging level in your configuration.
2. Initialize FastAPI with `reload=True` to enable auto-reloading during development.
3. Implement comprehensive logging throughout your application for easier troubleshooting. Set the logging level to `DEBUG` for detailed logs.
4. Use `docker exec` to interact with running containers for debugging containerized services.
5. Double-check your environment variables and configuration settings to ensure they are correctly set up.

## License

This project is licensed under the MIT License.
