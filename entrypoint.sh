#!/bin/sh
set -e

case "$RUN_MIGRATIONS" in
    true|True|1|yes|YES)
        echo "Running database migrations..."
        python manage.py migrate --noinput
        ;;
esac

case "$DEBUG" in
    false|False|0|no|NO)
        echo "Disabling known seeded users outside local development..."
        python manage.py disable_seeded_users
        ;;
esac

case "$RUN_MIGRATIONS" in
    true|True|1|yes|YES)
        echo "Running database migrations..."
        python manage.py migrate --noinput
        ;;
esac

echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
