# 🚁 FPV Drone Fleet Management System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A comprehensive web-based application designed to support military units in managing and tracking FPV (First Person View) drones throughout their entire operational lifecycle.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running with Docker](#running-with-docker)
- [Running Locally](#running-locally)
- [Django Admin](#django-admin)
- [Troubleshooting](#troubleshooting)
- [User Roles](#user-roles)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

The FPV Drone Fleet Management System provides centralized control over drone inventory, technical specifications, mission usage, maintenance processes, and write-off procedures. The platform supports secure storage and management of mission-related video data using external storage solutions.

**Key Objectives:**
- ✅ Centralized drone inventory management
- ✅ Technical specifications and configurations tracking
- ✅ Combat mission recording and monitoring
- ✅ Maintenance and repair lifecycle management
- ✅ Controlled drone decommissioning (write-off process)
- ✅ Secure mission video data storage and retrieval
- ✅ Role-based access control (RBAC)
- ✅ Scalable, API-first architecture

## ✨ Features

### 🔧 Core Modules

#### 1. Drone Inventory Management
- Create and manage drone records
- Store identification and classification data
- Track drone status (active, in mission, damaged, under repair, written off)
- Advanced filtering and search capabilities

#### 2. Technical Specifications Module
- Hardware configuration tracking (frame, motors, battery, camera)
- Performance metrics (speed, range, flight time)
- Firmware and communication parameters

#### 3. Mission Management
- Register and track missions
- Assign drones and operators
- Record mission details (location, duration, result)
- Link mission outcomes to drone condition
- Attach mission video data

#### 4. Maintenance & Repair Module
- Register defects and issues
- Track repair status and actions
- Record replaced components
- Maintain comprehensive repair history

#### 5. Write-Off Management
- Record drone decommissioning events
- Document write-off reasons (loss, destruction, critical damage)
- Preserve historical data for auditing

#### 6. Video Storage Module
- Upload mission video files to external storage
- Store and manage video metadata
- Link videos to missions and drones
- Secure, role-based access control

#### 7. Administration & User Management
- User registration and management
- Role assignment and access control
- Account activation/deactivation
- Comprehensive audit logging

## 🛠 Technology Stack

### Backend
- **Python** - Core programming language
- **Django** - Web framework
- **Django REST Framework** - RESTful API development
- **PostgreSQL** - Primary database

### Frontend
- **Bootstrap + Django Templates** - Responsive UI
- **React** (optional) - Advanced interactive components

### Storage
- **PostgreSQL** - Structured data storage
- **External Storage** for video files:
  - AWS S3 / Azure Blob / Google Cloud Storage
  - MinIO (S3-compatible)
  - Remote file server

### Infrastructure
- **Docker** - Containerized deployment
- **Nginx** - Web server and reverse proxy
- **Gunicorn** - Python WSGI HTTP server
- **Redis + Celery** - Background task processing (optional)

## 🏗 System Architecture

The system follows a modular monolithic architecture with clear separation of concerns:

```
mission_control/
├── accounts/          # User and role management
├── drones/            # Drone inventory
├── missions/          # Mission tracking
├── repairs/           # Maintenance management
├── writeoff/          # Decommissioning
├── media/             # Video file handling
├── reports/           # Analytics and reporting
└── config/            # Project configuration
```

This modular structure enables future evolution into microservices architecture if needed.

## 🚀 Getting Started

This section explains how to set up and run the project from scratch.

The project can be started in two ways:

- with Docker, which is recommended for most developers;
- locally, using Python and a local database setup.

## ✅ Prerequisites

Before starting, make sure you have the following tools installed:

- Git
- Python 3.10+
- pip
- Docker Desktop
- Docker Compose

If you want to run the project locally without Docker, you also need PostgreSQL installed on your machine.

## 📥 Clone the Repository

First, clone the project from GitHub:

```bash
git clone https://github.com/ITA-Internship/Mission-Control-System.git
cd Mission-Control-System
```

## ⚙️ Environment Variables

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

## 🐳 Running with Docker

Docker is the easiest way to start the project because it runs the application and required services in containers.

Build and start the containers:

```bash
docker compose up --build
```

If your system uses the older Docker Compose command, use:

```bash
docker-compose up --build
```

The `web` container runs migrations automatically on startup when `RUN_MIGRATIONS=True`.

If you want to run them manually, use:

```bash
docker compose exec web python manage.py migrate
```

Verify migration status:

```bash
docker compose exec web python manage.py showmigrations
```

Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

The application should be available at:

```text
http://localhost:8000/
```

The Django admin panel should be available at:

```text
http://localhost:8000/admin/
```

If pgAdmin is enabled in Docker Compose, it should be available at:

```text
http://localhost:5050/
```

## 💻 Running Locally

Use this option if you want to run the Django project directly on your machine without Docker.

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment.

For Linux or macOS:

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

Install project dependencies:

```bash
pip install -r requirements.txt
```

Create the `.env` file:

```bash
cp .env.example .env
```

For Windows PowerShell:

```bash
copy .env.example .env
```

Make sure the database settings in `.env` are correct.

For local development with Docker PostgreSQL:

```env
DB_HOST=localhost
DB_PORT=5433
```

Apply database migrations:

```bash
python manage.py migrate
```

Verify migration status:

```bash
python manage.py showmigrations
```

Create an admin user:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

The application should be available at:

```text
http://127.0.0.1:8000/
```

## 🛠 Database Migrations

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

If you are using Docker, the equivalent verification command is:

```bash
docker compose exec web python manage.py showmigrations
```

Manual post-migration step:

```bash
python manage.py createsuperuser
```

Or in Docker:

```bash
docker compose exec web python manage.py createsuperuser
```

## Seed Demo Data

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
```

Docker usage:

```bash
docker compose exec web python manage.py seed_db
docker compose exec web python manage.py seed_db --clear
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

## 🔐 Django Admin

To access the Django admin panel, first create a superuser:

```bash
python manage.py createsuperuser
```

Then start the server and open:

```text
http://127.0.0.1:8000/admin/
```

Log in with the username and password created in the previous step.

## 🧯 Troubleshooting

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

## 📌 Useful Commands

Start Docker containers:

```bash
docker compose up --build
```

Stop Docker containers:

```bash
docker compose down
```

Stop Docker containers and remove volumes:

```bash
docker compose down -v
```

View logs:

```bash
docker compose logs
```

View logs for the web container:

```bash
docker compose logs web
```

Run Django migrations in Docker:

```bash
docker compose exec web python manage.py migrate
```

Create a Django superuser in Docker:

```bash
docker compose exec web python manage.py createsuperuser
```

Run tests locally:

```bash
python manage.py test
```

## 👥 User Roles

The system supports role-based access control with the following roles:

| Role | Permissions |
|------|-------------|
| **Admin** | Full system access, user and role management |
| **Commander/Manager** | System oversight, reporting, decision-making |
| **Operator** | Mission creation and drone usage tracking |
| **Technician** | Maintenance and repair management |
| **Viewer** | Read-only access to system data |

## 📚 API Documentation

The system provides a comprehensive RESTful API. Once the application is running, access the API documentation at:

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`

### Example Endpoints

```bash
# Authentication
POST /api/auth/login/
POST /api/auth/logout/

# Drones
GET    /api/drones/
POST   /api/drones/
GET    /api/drones/{id}/
PUT    /api/drones/{id}/
DELETE /api/drones/{id}/

# Missions
GET    /api/missions/
POST   /api/missions/
GET    /api/missions/{id}/

# Repairs
GET    /api/repairs/
POST   /api/repairs/

# Videos
POST   /api/videos/upload/
GET    /api/videos/{id}/
```

## 🔒 Security Features

- ✅ JWT or session-based authentication
- ✅ Role-based access control (RBAC)
- ✅ Secure file upload with validation
- ✅ Comprehensive audit logging
- ✅ CSRF protection
- ✅ SQL injection prevention
- ✅ XSS protection

## 📊 Non-Functional Requirements

### Performance
- Efficient database query optimization
- Pagination and filtering support
- Optimized API response times
- Caching strategies

### Scalability
- API-first architecture
- External file storage integration
- Stateless backend design
- Containerized deployment
- Modular application structure

### Usability
- Simple and intuitive interface
- Responsive design for multiple devices
- Progressive web app capabilities

## 🧪 Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
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

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b task#xx-amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Coding Standards
- Follow PEP 8 style guide
- Write comprehensive tests
- Document all public APIs
- Use meaningful commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

**Project Maintainer**: mehalyna

- GitHub: [@mehalyna](https://github.com/mehalyna)
- Repository: [Mission-Control-System](https://github.com/ITA-Internship/Mission-Control-System)

## 🙏 Acknowledgments

- Django and Django REST Framework communities
- PostgreSQL development team
- All contributors and users of this system

---

**Built with ❤️ for military units managing FPV drone operations**
