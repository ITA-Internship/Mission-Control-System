## Troubleshooting

### Docker command does not work

Make sure Docker Desktop is installed and running.

Check Docker version:

```bash
docker --version
```

Check Docker Compose version:

```bash
docker compose version
```

If `docker compose` does not work, try:

```bash
docker-compose --version
```

### Port 8000 is already in use

Another process may already be using port `8000`.

Run the Django server on another port:

```bash
python manage.py runserver 8001
```

Then open:

```text
http://127.0.0.1:8001/
```

### Database connection error

Check that the database is running.

For Docker:

```bash
docker compose ps
```

Check container logs:

```bash
docker compose logs db
docker compose logs web
```

Also make sure that database values in `.env` are correct.

For Docker, `DB_HOST` should usually be:

```env
DB_HOST=db
```

For local development, `DB_HOST` should usually be:

```env
DB_HOST=localhost
```

### ModuleNotFoundError or missing package error

Make sure the virtual environment is activated and dependencies are installed:

```bash
pip install -r requirements.txt
```

### manage.py not found

Make sure you are in the project root directory.

You should see `manage.py` in the current folder.

Check current files:

```bash
ls
```

### Migrations do not work

Check migration status:

```bash
python manage.py showmigrations
```

Then try applying migrations again:

```bash
python manage.py migrate
```

### Environment variables are not loaded

Make sure the `.env` file exists in the project root directory.

Check files:

```bash
ls -a
```

If `.env` does not exist, create it from the example file:

```bash
cp .env.example .env
```

For Windows PowerShell:

```bash
copy .env.example .env
```
