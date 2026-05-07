#!/bin/sh
set -e

# Run migrations only on container startup (not on restarts via exec re-invocations).
# The migrate command is idempotent by itself, but running it on every restart
# adds unnecessary latency and risk. This guard ensures it only runs once per
# container lifecycle.
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
fi

exec "$@"
