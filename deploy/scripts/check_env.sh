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
        | tr -d '\r' \
        | sed -E "s/^[[:space:]]+//; s/[[:space:]]+#.*$//; s/[[:space:]]+$//; s/^\"(.*)\"$/\1/; s/^'(.*)'$/\1/"
}

normalize_boolean() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

is_true() {
    case "$(normalize_boolean "$1")" in
        true|1|yes|on) return 0 ;;
        *) return 1 ;;
    esac
}

is_false() {
    case "$(normalize_boolean "$1")" in
        false|0|no|off) return 0 ;;
        *) return 1 ;;
    esac
}

validation_failed=0

for var in "${REQUIRED_VARS[@]}"; do
    value="$(get_env_value "$var")"

    if [ -z "$value" ]; then
        echo "Error: Required environment variable $var is missing or empty."
        validation_failed=1
    fi
done

debug_value="$(get_env_value "DEBUG")"

if ! is_false "$debug_value"; then
    echo "Error: DEBUG must be False in production."
    validation_failed=1
fi

for var in "${REQUIRED_TRUE_VARS[@]}"; do
    value="$(get_env_value "$var")"

    if ! is_true "$value"; then
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

allowed_hosts="$(get_env_value "ALLOWED_HOSTS")"
healthcheck_host="$(get_env_value "HEALTHCHECK_HOST")"
healthcheck_host_allowed=0

IFS=',' read -r -a allowed_host_entries <<< "$allowed_hosts"

for allowed_host in "${allowed_host_entries[@]}"; do
    allowed_host="$(
        printf '%s' "$allowed_host" \
            | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//'
    )"

    if [ "$allowed_host" = "$healthcheck_host" ]; then
        healthcheck_host_allowed=1
        break
    fi
done

if [ "$healthcheck_host_allowed" -ne 1 ]; then
    echo "Error: HEALTHCHECK_HOST must be one of the ALLOWED_HOSTS values."
    validation_failed=1
fi

if [ "$validation_failed" -ne 0 ]; then
    echo "Production environment validation failed. Deployment aborted."
    exit 1
fi

echo "Production environment validation passed."
