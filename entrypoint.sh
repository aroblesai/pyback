#!/bin/sh
echo "Waiting for database to be ready..."
sleep 5

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting the application..."
uv run pyback
