#!/bin/bash

set -e

echo "Waiting for postgres..."
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 2
done

echo "Postgres is up - running migrations"
alembic upgrade head

echo "Migrations applied - starting app"
exec uvicorn src.main:app --host 0.0.0.0 --port 8001
