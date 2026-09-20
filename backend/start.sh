#!/usr/bin/env bash
# Fail immediately if any command fails
set -e

echo "========================================================"
echo "🌸 Sakhi AI Production Startup"
echo "========================================================"

echo "🌸 Step 1: Running Alembic database migrations..."
alembic upgrade head
echo "✅ Database migrations applied successfully."

echo "🌸 Step 2: Starting Sakhi AI Uvicorn server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
