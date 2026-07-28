#!/bin/bash

ENV_FILE="${ENV_FILE:-.env}"

REQUIRED_VARS=(
    "DB_NAME"
    "DB_USER"
    "DB_PASSWORD"
    "REDIS_PASSWORD"
    "PGADMIN_DEFAULT_EMAIL"
    "PGADMIN_DEFAULT_PASSWORD"
    "DJANGO_SECRET_KEY"
    "DEBUG"
    "ALLOWED_HOSTS"
    "CSRF_TRUSTED_ORIGINS"
    "HEALTHCHECK_HOST"
    "SESSION_COOKIE_SECURE"
    "CSRF_COOKIE_SECURE"
    "SECURE_SSL_REDIRECT"
    "SECURE_HSTS_SECONDS"
    "SECURE_HSTS_INCLUDE_SUBDOMAINS"
    "SECURE_HSTS_PRELOAD"
)

REQUIRED_TRUE_VARS=(
    "SESSION_COOKIE_SECURE"
    "CSRF_COOKIE_SECURE"
    "SECURE_SSL_REDIRECT"
)

echo "Running production environment validation..."

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE file is missing."
    exit 1
fi

get_env_value() {
    grep -E "^${1}=" "$ENV_FILE" \
        | tail -n 1 \
        | cut -d "=" -f 2- \
        | tr -d '\r'
}

normalize_boolean() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

validation_failed=0

for var in "${REQUIRED_VARS[@]}"; do
    value="$(get_env_value "$var")"

    if [ -z "$value" ]; then
        echo "Error: Required environment variable $var is missing or empty."
        validation_failed=1
    fi
done

debug_value="$(normalize_boolean "$(get_env_value "DEBUG")")"

if [ "$debug_value" != "false" ]; then
    echo "Error: DEBUG must be False in production."
    validation_failed=1
fi

for var in "${REQUIRED_TRUE_VARS[@]}"; do
    value="$(normalize_boolean "$(get_env_value "$var")")"

    if [ "$value" != "true" ]; then
        echo "Error: $var must be True in production."
        validation_failed=1
    fi
done

hsts_seconds="$(get_env_value "SECURE_HSTS_SECONDS")"

case "$hsts_seconds" in
    ""|*[!0-9]*)
        echo "Error: SECURE_HSTS_SECONDS must be a positive integer."
        validation_failed=1
        ;;
    0)
        echo "Error: SECURE_HSTS_SECONDS must be greater than zero."
        validation_failed=1
        ;;
esac

if [ "$validation_failed" -ne 0 ]; then
    echo "Production environment validation failed. Deployment aborted."
    exit 1
fi

echo "Production environment validation passed."
