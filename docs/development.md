## Development

### Running Tests

```bash
# Run all tests
python manage.py test
```

### Code Quality

This project uses `pre-commit` to automatically enforce code quality standards. We use **Black** (formatting), **isort** (import sorting), and **Flake8** (linting).

***Local Setup:***

To run checks automatically before each commit, run:
```bash
pip install pre-commit
pre-commit install
```

***Manual Run:***

To check all files without making a commit:
```bash
pre-commit run --all-files
```

***Continuous Integration (CI):***

GitHub Actions are configured to automatically run these checks on all Pull Requests and pushes to the develop and main branches.

### Database Migrations

Migrations are used to create and update database tables.

Create new migrations after changing Django models:

```bash
python manage.py makemigrations
```

Apply migrations to the database:

```bash
python manage.py migrate
```

Check migration status:

```bash
python manage.py showmigrations
```

Verify that model tables were created in PostgreSQL by running the application and checking that the core apps (`accounts`, `roles`, `drones`, Django auth/admin/session tables) appear in the database after migration.

For this project, the initial migration flow was verified with:

```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py showmigrations
```

### Seed Demo Data

The project includes a Django management command for loading representative demo data for the existing user, drone, and mission models.

Security note: `seed_db` is intended for isolated local development only. Do not run it in shared, staging, or production-like environments.

When the app starts with `DEBUG=False`, the container entrypoint also runs `python manage.py disable_seeded_users` to deactivate any previously created seeded demo accounts.

Run the full seed:

```bash
python manage.py seed_db --password "LocalSeedPassword123!"
```

Clear only the managed seed records and recreate them:

```bash
python manage.py seed_db --clear --password "LocalSeedPassword123!"
```

Seed a single module:

```bash
python manage.py seed_db --module users --password "LocalSeedPassword123!"
python manage.py seed_db --module missions
python manage.py seed_db --module drones
python manage.py seed_db --module repairs
```

Use a specific temporary password for seeded users:

```bash
python manage.py seed_db --module users --password "LocalSeedPassword123!"
```

Or set `SEED_DEFAULT_PASSWORD` in your local `.env` before running the command. If users are seeded and no password is provided, `seed_db` stops with an error instead of generating or printing credentials.

The seeded dataset includes demo accounts across the main system roles so that local RBAC flows can be tested quickly. Treat all seeded credentials as local-only development data and replace or disable them outside your own machine.

Seeded users are marked with `must_change_password=True`. That flag is cleared after the user sets a new password through activation, password reset, or the change-password endpoint.

Notes about the seeded dataset:

- The command is idempotent and updates existing seed records instead of duplicating them.
- Only existing models and existing status choices are used.
- Mission operator and drone assignment details are stored in mission notes because the current schema does not yet contain dedicated assignment tables.

### Updating API Documentation
If you make any changes to API endpoints, the [API Reference](api.md) must be updated.

The update process involves two steps: exporting the latest OpenAPI schema and converting it into Markdown.

If you don't have the required tools installed yet, run:
```bash
pip install drf-spectacular openapi-markdown
```

1. Generate the latest OpenAPI schema:
```bash
python manage.py spectacular --file schema.yml
```

2. Convert the schema into the Markdown file:
```bash
openapi2markdown schema.yml docs/api.md
```
