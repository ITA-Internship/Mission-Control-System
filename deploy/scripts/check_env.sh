#!/bin/bash

REQUIRED_VARS=(
    "DB_NAME"
    "DB_USER"
    "DB_PASSWORD"
    "REDIS_PASSWORD"
    "PGADMIN_DEFAULT_EMAIL"
    "PGADMIN_DEFAULT_PASSWORD"
    "DJANGO_SECRET_KEY"
)
ENV_FILE=".env"

echo "Running environment validation..."

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE file is missing!"
    exit 1
fi

missing_vars=0

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^$var=" "$ENV_FILE"; then
        echo "Error: Required environment variable $var is missing in $ENV_FILE"
        missing_vars=1
    fi
done

if [ $missing_vars -eq 1 ]; then
    echo "Environment validation failed. Deployment aborted."
    exit 1
else
    echo "Environment validation passed."
    exit 0
fi
