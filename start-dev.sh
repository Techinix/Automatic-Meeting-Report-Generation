#!/bin/sh

# Run DB migrations
alembic upgrade head

# Start the application in development mode with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
