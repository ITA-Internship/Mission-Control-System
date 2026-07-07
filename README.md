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

Create a .env file from the example file:
```bash
cp .env.example .env
```

For Windows PowerShell, use:
```bash
copy .env.example .env
```

After that, open the .env file and update the values if needed.

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
python manage.py seed_db
```

### Running Test
```bash
python manage.py test
```

For more details, see [Development](docs/development.md).

## Documentation
- [Contributing](CONTRIBUTING.md)
- [API Reference](docs/api.md)
- [Architecture](docs/architecture.md)
- [Contributing](CONTRIBUTING.md)
- [Environment variables](docs/configuration.md)
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
