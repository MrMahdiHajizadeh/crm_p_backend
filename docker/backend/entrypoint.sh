#!/bin/bash
set -e

DBHOST="${DBHOST:-db}"
DBPORT="${DBPORT:-5432}"

if [ -n "${DBHOST:-}" ] || [ -n "${DBNAME:-}" ]; then
  echo "Waiting for PostgreSQL at ${DBHOST}:${DBPORT}..."
  retries=0
  max_retries=60
  while ! python - <<'PY' 2>/dev/null
import os
import socket
host = os.environ.get("DBHOST", "db")
port = int(os.environ.get("DBPORT", "5432"))
with socket.create_connection((host, port), timeout=2):
    pass
PY
  do
      retries=$((retries + 1))
      if [ "$retries" -ge "$max_retries" ]; then
          echo "ERROR: Could not connect to PostgreSQL after $max_retries attempts."
          exit 1
      fi
      echo "  PostgreSQL not ready yet (attempt $retries/$max_retries)..."
      sleep 2
  done
  echo "PostgreSQL is ready."
else
  echo "No database host configured; skipping PostgreSQL wait."
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating default admin user (if needed)..."
python manage.py create_default_admin

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting production server (Gunicorn)..."
exec gunicorn crm.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -