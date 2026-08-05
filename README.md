# FPV Drone Fleet Management System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Backend API for FPV drone fleet management designed to track the entire operational lifecycle of drones in military units.

## Prerequisites

Before starting, make sure you have the following tools installed:

- Git
- Python 3.10+
- pip
- Docker Desktop
- Docker Compose

If you want to run the project locally without Docker, you also need PostgreSQL installed on your machine.

## Quick Start

### Clone the Repository
Clone the project from GitHub:
```bash
git clone https://github.com/ITA-Internship/Mission-Control-System.git
cd Mission-Control-System
```

### Environment Variables
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

For more details, see [Configuration](docs/configuration.md).

### Running with Docker

Docker is the easiest way to start the project because it runs the application and required services in containers.

1. Build and start the containers:
```bash
docker compose up --build
```

The web container runs migrations automatically on startup when `RUN_MIGRATIONS=True`.

2. Create an admin user.

Follow the `createsuperuser` command instructions in the [Common Commands](#common-commands) section below.

3. Access the services:
   - application: http://localhost:8000/
   - Django admin: http://localhost:8000/admin/
   - pgAdmin (if enabled): http://localhost:5050/

Docker Compose exposes `Nginx` on port `8000`. `Gunicorn` stays inside the Docker network and is no longer reachable directly from the host.

### Running Locally

Use this option if you want to run the Django project directly on your machine without Docker.

1. Environment setup:

Create a virtual environment:
```bash
python -m venv venv
```
Activate the virtual environment (Linux/macOS):
```bash
source venv/bin/activate
```
For Windows PowerShell:
```bash
venv\Scripts\activate
```
For Git Bash on Windows:
```bash
source venv/Scripts/activate
```
2. Install Dependencies & Configure Env:

```bash
pip install -r requirements.txt
```

> **Native dependency — libmagic.** Media uploads are content-validated with
> `python-magic`, which needs the native **libmagic** library at runtime.
> Without it, `python manage.py test` (and any upload) fails with
> `ImportError: failed to find libmagic`.
>
> - **Docker** (recommended for local runs): already included in the image — no
>   action needed.
> - **Linux/macOS:** install the system library, e.g. `apt-get install libmagic1`
>   or `brew install libmagic`.
> - **Windows:** `python-magic` does **not** bundle the DLLs. Either run through
>   Docker, or additionally `pip install python-magic-bin` to get the native
>   binaries.
>
> (Video duration extraction similarly needs `ffmpeg` on the `PATH`; it is in
> the Docker image.)

Copy environment variables and make sure the database settings in .env are correct.

3. Database & Admin Setup:

Run migrations and create an admin user. See the exact commands in the [Common Commands](#common-commands) section.

4. Start Development Server:

```bash
python manage.py runserver
```
The application should be available at http://127.0.0.1:8000/.

## Project structure

The system follows a modular monolithic architecture with clear separation of concerns:

```
Mission-Control-System/
├── accounts/          # User and role management, RBAC implementation
├── common/            # Shared functionality
├── drones/            # Drone inventory
├── media/             # Video file handling
├── missions/          # Mission tracking
├── repairs/           # Maintenance management
├── roles/             # Role definitions
└── config/            # Project configuration
```

## Common commands

> Note for Docker users: prefix all `manage.py` commands with `docker compose exec web`.

### Database Migrations

Create new migrations after changing Django models:
```bash
python manage.py makemigrations
```
Apply migrations to the database:
```bash
python manage.py migrate
```

### User Management
Create an admin user:
```bash
python manage.py createsuperuser
```

### Seed Demo Data
Populate the database with development data:
```bash
python manage.py seed_db --password "LocalSeedPassword123!"
```

### Running Test
```bash
python manage.py test
```

For more details, see [Development](docs/development.md).

## Session Authentication

The frontend uses a centralized authentication state provided by
`AuthProvider`. When the application starts, it requests
`GET /api/accounts/users/me/` and exposes the current session as
`loading`, `authenticated`, or `unauthenticated`.

Authentication is restored from the backend session cookie after a
browser refresh. Authentication cookies and session identifiers are
not stored in `localStorage` or `sessionStorage`.

Protected routes use the shared authentication state:

- unauthenticated users are redirected to `/login`;
- users with `must_change_password=true` are redirected to
  `/change-password/required`;
- protected routes remain inaccessible until the required password
  change is completed;
- direct navigation, page refresh, and browser Back/Forward navigation
  use the same access-control logic.

A validated internal destination can be preserved through the
`returnTo` query parameter. External, malformed, protocol-relative,
and authentication-loop destinations are rejected. The fallback
destination is `/my-profile`.

After a required password change, the frontend refreshes
`GET /api/accounts/users/me/`, verifies that
`must_change_password=false`, updates the shared authentication state,
and redirects only after the refresh completes.

Logout ends only the current backend session. The frontend clears its
shared authentication state only after a successful logout response.
A failed logout keeps the authenticated state and displays a safe
error.

Authentication errors are handled consistently:

- session-related `401` and `403` responses clear stale authentication
  state and redirect to login;
- genuine authorization `403` responses display an access-denied
  message;
- CSRF failures refresh CSRF state and retry an unsafe request once;
- `429`, network, and server failures display safe messages.

Session-authentication endpoints:

```text
GET  /api/accounts/login/
POST /api/accounts/login/
POST /api/accounts/logout/
GET  /api/accounts/users/me/
POST /api/accounts/users/me/change-password/
```

### Local Authentication Verification

1. Open `/my-profile` without an authenticated session.
2. Verify the redirect to `/login`.
3. Sign in using a seeded user.
4. Verify that a required password change redirects to
   `/change-password/required`.
5. Verify that `/my-profile` remains inaccessible before changing the
   password.
6. Change the password.
7. Verify that authentication state is refreshed before redirecting.
8. Verify navigation to `/my-profile` or the preserved `returnTo`
   destination.
9. Refresh the browser and verify that the session is restored.
10. Sign out.
11. Verify that protected routes and
    `GET /api/accounts/users/me/` are no longer accessible.

## Documentation
- [Contributing](CONTRIBUTING.md)
- [API Reference](docs/api.md)
- [Architecture](docs/architecture.md)
- [Contributing](CONTRIBUTING.md)
- [Configuration](docs/configuration.md)
- [Deployment](docs/deployment.md)
- [Development](docs/development.md)
- [RBAC permission matrix Reference](docs/rbac.md)
- [Roadmap](docs/roadmap.md)
- [Troubleshooting](docs/troubleshooting.md)

### API Documentation

The system provides a comprehensive RESTful API. Once the application is running, access the API documentation at:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

**Project Maintainer**: mehalyna

- GitHub: [@mehalyna](https://github.com/mehalyna)
- Repository: [Mission-Control-System](https://github.com/ITA-Internship/Mission-Control-System)

## Acknowledgments

- Django and Django REST Framework communities
- PostgreSQL development team
- All contributors and users of this system

---

**Built with ❤️ for military units managing FPV drone operations**
