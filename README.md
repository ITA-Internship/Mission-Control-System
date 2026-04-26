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
- [Installation](#installation)
- [Configuration](#configuration)
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

## 🚀 Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 13+
- Docker & Docker Compose (optional)
- Git

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/mehalyna/Mission-Control-System.git
cd Mission-Control-System

# Copy environment configuration
cp .env.example .env

# Edit .env with your configuration
nano .env

# Build and start containers
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access the application at http://localhost:8000
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/mehalyna/Mission-Control-System.git
cd Mission-Control-System

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database in .env
cp .env.example .env
nano .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=drone_management
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# External Storage (AWS S3 Example)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=drone-videos
AWS_S3_REGION_NAME=us-east-1

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0

# Security
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
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

```bash
# Format code with Black
black .

# Lint with flake8
flake8 .

# Type checking with mypy
mypy .
```

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
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
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
- Repository: [Mission-Control-System](https://github.com/mehalyna/Mission-Control-System)

## 🙏 Acknowledgments

- Django and Django REST Framework communities
- PostgreSQL development team
- All contributors and users of this system

---

**Built with ❤️ for military units managing FPV drone operations**
