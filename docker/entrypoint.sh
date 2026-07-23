#!/bin/sh
set -e

alembic upgrade head
python scripts/seed.py
exec "$@"
