## Environment Variables

The project uses environment variables to store configuration values.

Create a `.env` file from the example file:

```bash
cp .env.example .env
```

For Windows PowerShell, use:

```bash
copy .env.example .env
```

After that, open the `.env` file and update the values if needed.

Example `.env` configuration:

```env
# Django settings
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
RUN_MIGRATIONS=True

# Database settings
DB_NAME=drone_fleet_db
DB_USER=drone_fleet_user
DB_PASSWORD=replace-with-a-strong-database-password
DB_HOST=localhost
DB_PORT=5433

# Redis
REDIS_PASSWORD=replace-with-a-strong-redis-password

# pgAdmin
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=replace-with-a-strong-pgadmin-password
```

Alternative Docker `web` container database settings:

```env
DB_HOST=db
DB_PORT=5432
```

For Docker-based development, the `web` container uses `DB_HOST=db` and `DB_PORT=5432`, because `db` is the PostgreSQL service name inside Docker Compose.

When Redis is enabled in Docker Compose, the `web` container builds its internal `REDIS_URL` from `REDIS_PASSWORD`, so set a strong local password in `.env`.

For local development without Docker, `DB_HOST` should usually be set to `localhost`.

In this project, local development uses `DB_PORT=5433` so the Docker PostgreSQL container does not conflict with a local PostgreSQL instance that may already be using port `5432`.

For safer local development, the Docker Compose ports for PostgreSQL, Redis, pgAdmin, and Nginx are bound to `127.0.0.1`, so they are reachable from the host machine only and are not exposed on the wider network by default.

Redis is also configured with `requirepass`, so local tools that connect to it must use the password from `REDIS_PASSWORD`.

Nginx sits in front of Gunicorn and applies basic request buffering and timeout limits to reduce exposure to slow-header, slow-body, and connection-exhaustion style attacks during local Docker-based runs.

The bundled Nginx config also adds:
- basic per-IP connection limits
- stricter rate limiting for account activation and password reset routes
- proxy buffering for upstream requests
- common security headers such as `X-Frame-Options` and `X-Content-Type-Options`

## Production HTTPS and Transport Security

Production deployments must use HTTPS for all external traffic.

The recommended deployment topology is:

```text
Client
  -> HTTPS load balancer or reverse proxy
  -> Nginx
  -> Gunicorn
  -> Django
```

The trusted load balancer or reverse proxy must:

* listen on HTTPS port `443` using a valid TLS certificate;
* redirect all public HTTP traffic from port `80` to HTTPS;
* remove any client-provided `X-Forwarded-Proto` header;
* set `X-Forwarded-Proto: https` for requests received over HTTPS;
* be the only component allowed to connect directly to the bundled Nginx listener.

The following settings must be enabled in the production environment:

```env
DEBUG=False

ALLOWED_HOSTS=api.example.com
CSRF_TRUSTED_ORIGINS=https://api.example.com

# Host header used by internal Docker health checks.
# It must match one of the values in ALLOWED_HOSTS.
HEALTHCHECK_HOST=api.example.com

SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True

SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

Do not include `http://`, `https://`, ports, or URL paths in
`ALLOWED_HOSTS` or `HEALTHCHECK_HOST`.

For the initial HSTS rollout, use a short duration:

```env
SECURE_HSTS_SECONDS=3600
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
```

Increase `SECURE_HSTS_SECONDS` and enable `SECURE_HSTS_INCLUDE_SUBDOMAINS`
and `SECURE_HSTS_PRELOAD` only after confirming that the main domain, all
subdomains, and all external resources work correctly over HTTPS.

Local development continues to use HTTP. Keep the local transport security
settings disabled as shown in `.env.example`:

```env
HEALTHCHECK_HOST=localhost

SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False

SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
```
