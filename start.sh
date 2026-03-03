#!/bin/bash

# Hugging Face Spaces provides the port via $SPACE_PORT, defaults to 7860
PORT=${SPACE_PORT:-7860}

echo "Starting FastAPI Server on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT &

echo "Starting RQ Worker..."
python -m app.worker.worker
