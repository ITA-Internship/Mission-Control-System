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

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

### Seed Demo Data

The project includes a Django management command for loading representative demo data for the existing user, drone, and mission models.

Run the full seed:

```bash
python manage.py seed_db
```

Clear only the managed seed records and recreate them:

```bash
python manage.py seed_db --clear
```

Seed a single module:

```bash
python manage.py seed_db --module users
python manage.py seed_db --module missions
python manage.py seed_db --module drones
python manage.py seed_db --module repairs
```

Default seeded password for all demo accounts:

```text
Test@1234
```

Seeded demo accounts:

| Role | Username |
|------|----------|
| Admin | `root.admin` |
| Admin | `admin.ops` |
| Commander | `commander.north` |
| Commander | `commander.south` |
| Operator | `operator.alpha` |
| Operator | `operator.bravo` |
| Operator | `operator.charlie` |
| Technician | `tech.airframe` |
| Technician | `tech.electro` |
| Viewer | `viewer.ops` |
| Viewer | `viewer.audit` |

Notes about the seeded dataset:

- The command is idempotent and updates existing seed records instead of duplicating them.
- Only existing models and existing status choices are used.
- Mission operator and drone assignment details are stored in mission notes because the current schema does not yet contain dedicated assignment tables.
