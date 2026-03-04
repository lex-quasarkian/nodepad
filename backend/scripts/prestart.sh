#! /usr/bin/env bash

set -e
set -x

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$BACKEND_DIR"

# Let the DB start
uv run python app/backend_pre_start.py

# Run migrations
uv run alembic upgrade head

# Create initial data in DB
uv run python app/initial_data.py
