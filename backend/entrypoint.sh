#!/bin/sh
set -eu

echo "Running database migrations..."
alembic upgrade head

echo "Loading synthetic demo data..."
python scripts/seed.py

echo "Starting ReUse Campus API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
