# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**Lafaom** is a well-architected FastAPI application that serves as an educational and job marketplace platform. The application uses a domain-driven architecture with comprehensive user management, permissions, blog functionality, job offers, and payment processing.

## Development Commands

### Local Development (Docker)
```bash
# Start the entire application with database and dependencies
docker-compose up

# Start only the database (useful for local development)
docker-compose up db

# Build and rebuild containers
docker-compose build
```

### Local Development (Direct)
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI development server
uvicorn src.main:app --reload --env-file .development.env --host 0.0.0.0 --port 8000

# Alternative using the provided script
chmod +x start && ./start
```

### Database Operations
```bash
# Create a new migration
alembic revision --autogenerate -m "Your migration message"

# Apply pending migrations
alembic upgrade head

# Downgrade to previous migration
alembic downgrade -1

# Show migration history
alembic history
```

### Code Quality
```bash
# Format code with Black
black src/

# Check formatting without making changes
black --diff src/
black --check src/

# Lint code with Flake8
flake8 src/

# Run both formatting and linting
black src/ && flake8 src/
```

### Celery Background Tasks
```bash
# Start Celery worker (local development)
celery -A src.main.celery worker -Q lafaom_default,lafaom_high_priority --loglevel=info

# Start Celery Beat scheduler (local development)
celery -A src.main.celery beat --schedule=celerybeat-schedule -l info

# Monitor Celery with Flower (if configured)
celery -A src.main.celery flower

# Using Docker (recommended)
docker-compose up celery_worker celery_beat
```

### Testing
```bash
# Run tests (add when test suite exists)
pytest

# Run specific test file
pytest tests/test_user.py

# Run with coverage
pytest --cov=src
```

## Architecture Overview

### Domain Structure
The application follows a **domain-driven design** with each domain module containing:

- **`models.py`**: SQLModel database models with relationships
- **`schemas.py`**: Pydantic models for request/response validation
- **`service.py`**: Business logic layer with async database operations
- **`router.py`**: FastAPI route definitions with dependency injection
- **`dependencies.py`**: Custom dependency functions for validation/authorization

### Current Domains
- **`auth/`**: Authentication, JWT tokens, OAuth, permission management
- **`user/`**: User management, roles, permissions, profiles
- **`blog/`**: Blog posts, categories, content management
- **`job_offers/`**: Job listings, applications, attachments
- **`payments/`**: Payment processing, CinetPay integration
- **`system/`**: System-wide configurations and utilities
- **`training/`**: Educational content and course management

### Database Architecture
- **Base Models**: `CustomBaseModel` (int ID) and `CustomBaseUUIDModel` (UUID) with automatic timestamps
- **Async Operations**: All database operations use AsyncSession for better performance
- **Soft Deletes**: Models support soft deletion through `delete_at` field
- **Relationships**: Comprehensive SQLModel relationships between domains
- **Migrations**: Alembic handles database schema changes

### Authentication & Authorization
- **Firebase Integration**: Firebase Admin SDK for token validation
- **JWT Tokens**: Custom JWT implementation with access/refresh tokens
- **Permission System**: Fine-grained permissions with role-based access control
- **Dependency Injection**: `check_permissions()` decorator for route protection

### Background Tasks (Celery)
- **Queues**: `lafaom_default`, `lafaom_high_priority`, `lafaom_low_priority`
- **Redis Backend**: Used for both broker and result backend
- **Custom Task Decorator**: `custom_celery_task` with exponential backoff
- **Scheduled Tasks**: Celery Beat for periodic task execution

### Configuration Management
- **Environment-based**: Uses Pydantic Settings with `.env` file loading
- **Multi-environment**: Supports development, staging, production configurations
- **External Services**: SMTP, Mailgun, AWS S3, CinetPay, Firebase, Sentry configurations

## Development Patterns

### Adding New Domain
1. Create new directory under `src/api/new_domain/`
2. Implement the five core files: `models.py`, `schemas.py`, `service.py`, `router.py`, `dependencies.py`
3. Add models to migrations: Import in `migrations/env.py`
4. Register router in `src/main.py`
5. Add appropriate permissions to `PermissionEnum`

### Database Model Guidelines
- Inherit from `CustomBaseModel` (int ID) or `CustomBaseUUIDModel` (UUID ID)
- Use SQLModel Field() for column definitions with proper constraints
- Define relationships using Relationship() with appropriate back_populates
- Add event listeners for automatic timestamp updates when needed

### Service Layer Patterns
- All services use dependency injection: `session: AsyncSession = Depends(get_session_async)`
- Use async/await for all database operations
- Implement proper error handling with custom exceptions
- Follow the filter/pagination pattern for list endpoints

### API Endpoint Patterns
- Use appropriate HTTP methods: GET (read), POST (create), PUT (update), DELETE (delete)
- Implement comprehensive request/response schemas
- Use dependency injection for authentication: `Depends(check_permissions([PermissionEnum.CAN_VIEW_X]))`
- Return standardized response schemas inheriting from `BaseOutSuccess`

### Permission Management
- All sensitive endpoints require permission checks
- Permissions are defined in `PermissionEnum`
- Use `check_permissions()` dependency with required permission list
- Support both user-level and role-based permissions

## Infrastructure Notes

### Docker Setup
- **Multi-stage build** with Python 3.10.15-slim base image
- **Non-root user** (fastapi) for security
- **Volume mounts** for development and file uploads
- **Network separation** for database and redis connections

### Database Configuration
- **PostgreSQL** as primary database (configurable via DATABASE_URL)
- **Connection pooling** handled by SQLAlchemy async engine
- **Migration management** through Alembic with environment-specific configs

### Redis Integration
- **Cache layer**: Used for temporary data storage and rate limiting
- **Session management**: Handles user sessions and temporary tokens
- **Celery broker**: Background task queue management

### File Upload Handling
- **Local storage**: Default file upload to `src/static/uploads/`
- **AWS S3 support**: Configurable cloud storage option
- **Security**: Proper file validation and size limits

## API Documentation

The application provides interactive API documentation:
- **Swagger UI**: Available at `/docs` when running
- **ReDoc**: Available at `/redoc` when running
- **OpenAPI Schema**: Generated automatically from route definitions

## Key Environment Variables

Create `.env` file with these essential variables:
```env
ENV=development
DATABASE_URL=postgresql://user:password@localhost:5432/lafaom
SECRET_KEY=your-secret-key
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/0
```

## Development Guidelines

### Code Style
- **Black formatting**: Max line length 88 characters
- **Flake8 linting**: Extended ignore E203, W503 for Black compatibility
- **Type hints**: Use Python type annotations throughout
- **Async patterns**: Prefer async/await for I/O operations

### Error Handling
- Use custom `ErrorMessage` enum for consistent error codes
- Return structured error responses using `BaseOutFail` schema
- Implement proper HTTP status codes (400, 401, 403, 404, 500)

### Security Considerations
- Never commit sensitive data (API keys, passwords, tokens)
- Use environment variables for all configuration
- Implement proper CORS settings for production
- Validate all input data using Pydantic schemas

### Performance Optimization
- Use async database sessions for concurrent operations
- Implement database indexing on frequently queried fields
- Use Redis caching for expensive operations
- Optimize database queries with proper joins and selections