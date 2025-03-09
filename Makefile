# Colors for help message
BLUE := \033[36m
NC := \033[0m

.DEFAULT_GOAL := help

.PHONY: help install dev docker-* db-* test lint docs clean

# ---------------------------
# Development Setup
# ---------------------------
setup: ## Install dev dependencies and setup pre-commit
	uv pip install -e ".[dev]"
	uv sync --all-extras --frozen
	uv run pre-commit install

install: ## Install package in regular mode
	uv pip install -e .

# ---------------------------
# Development
# ---------------------------
sync: ## Sync dependencies with uv
	uv sync --frozen

lint: ## Run ruff linter
	uv run ruff check

typecheck: ## Run mypy type checker
	uv run mypy

format: ## Format code with ruff
	uv run ruff check --fix
	uv run ruff format

pre-commit: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

build: ## Build Python package
	uv pip install build
	uv run python -m build

# ---------------------------
# Application
# ---------------------------
run: ## Run the pyback application
	uv run pyback

# ---------------------------
# Database
# ---------------------------
db-migrate: ## Apply all pending migrations
	docker compose exec app uv run alembic upgrade head

db-revision: ## Create a new migration revision
	@read -p "Enter migration message: " message; \
	docker compose exec app uv run alembic revision --autogenerate -m "$$message"

db-rollback: ## Rollback the most recent migration
	docker compose exec app uv run alembic downgrade -1

db-history: ## Show migration history
	docker compose exec app uv run alembic history

db-current: ## Show current migration version
	docker compose exec app uv run alembic current

db-shell: ## Open a PostgreSQL shell in the database container
	docker compose exec db psql -U postgres

# ---------------------------
# Docker
# ---------------------------
docker-build: ## Build Docker containers
	docker compose build

docker-up: ## Start Docker containers in detached mode
	docker compose -f docker-compose.yml up -d

docker-up-build: ## Build and start Docker containers in detached mode
	docker compose -f docker-compose.yml up -d --build

docker-up-tests: ## Build and start Docker containers in detached mode with tests
	docker compose up -d

docker-down: ## Stop Docker containers
	docker compose down

docker-restart: ## Restart Docker containers
	docker compose restart

docker-logs: ## View container logs
	docker compose logs -f

docker-clean: ## Remove all containers, images, and volumes
	docker compose down -v --rmi all

# ---------------------------
# Testing
# ---------------------------
test: ## Run tests
	docker compose up --build --abort-on-container-exit --exit-code-from test

# ---------------------------
# Documentation
# ---------------------------
docs-serve: ## Serve documentation locally
	uv run mkdocs serve

docs-build: ## Build documentation
	uv run mkdocs build --clean

# ---------------------------
# GitHub Actions
# ---------------------------
act: ## Run GitHub Actions locally with act
	act --rebuild push --eventpath .github/test-events/push_event.json --secret-file .github/act/.secrets

# ---------------------------
# Cleanup
# ---------------------------
clean: ## Remove Python cache files and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} \; 2>/dev/null || true
	find . -type d -name "*.egg" -exec rm -rf {} \; 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} \; 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} \; 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} \; 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} \; 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} \; 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} \; 2>/dev/null || true

# ---------------------------
# Help
# ---------------------------
help: ## Display this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'
