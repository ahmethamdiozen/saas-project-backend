#!/bin/bash

export PYTHONUNBUFFERED=1

echo "--- 🚀 LOG: Application starting up... ---"

# Port setup
export PORT=${SPACE_PORT:-7860}
echo "--- 🚀 LOG: Target Port is $PORT ---"

# Environment Variable Audit
echo "--- 🚀 LOG: Auditing Environment Variables... ---"
[ -z "$DATABASE_URL" ] && echo "❌ ERROR: DATABASE_URL is MISSING" || echo "✅ DATABASE_URL is set"
[ -z "$REDIS_URL" ] && echo "❌ ERROR: REDIS_URL is MISSING" || echo "✅ REDIS_URL is set"
[ -z "$OPENAI_API_KEY" ] && echo "❌ ERROR: OPENAI_API_KEY is MISSING" || echo "✅ OPENAI_API_KEY is set"
[ -z "$SECRET_KEY" ] && echo "❌ ERROR: SECRET_KEY is MISSING" || echo "✅ SECRET_KEY is set"

# Start API
echo "--- 🚀 LOG: Launching FastAPI Server... ---"
uvicorn app.main:app --host 0.0.0.0 --port $PORT &

# Start Worker (Foreground to keep container alive and catch crashes)
echo "--- 🚀 LOG: Launching RQ Worker... ---"
python -m app.worker.worker
