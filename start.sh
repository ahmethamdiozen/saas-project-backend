#!/bin/bash
set -e

PORT=${PORT:-8000}

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI server on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4 &

echo "Starting RQ Worker..."
python -m app.worker.worker
