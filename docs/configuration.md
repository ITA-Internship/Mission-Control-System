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
DB_PASSWORD=change-me
DB_HOST=localhost
DB_PORT=5433

# Redis
REDIS_URL=redis://redis:6379/0

# pgAdmin
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=change-me
```

Alternative Docker `web` container database settings:

```env
DB_HOST=db
DB_PORT=5432
```

For Docker-based development, the `web` container uses `DB_HOST=db` and `DB_PORT=5432`, because `db` is the PostgreSQL service name inside Docker Compose.

For local development without Docker, `DB_HOST` should usually be set to `localhost`.

In this project, local development uses `DB_PORT=5433` so the Docker PostgreSQL container does not conflict with a local PostgreSQL instance that may already be using port `5432`.
