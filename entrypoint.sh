#!/bin/sh
set -e

case "$RUN_MIGRATIONS" in
    true|True|1|yes|YES)
        echo "Running database migrations..."
        python manage.py migrate --noinput
        ;;
esac

exec "$@"
