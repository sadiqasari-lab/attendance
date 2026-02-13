# Inspire Attendance System

Enterprise multi-tenant attendance management system with biometric verification, GPS geofencing, and real-time monitoring.

## Features

- **Multi-tenant architecture** — tenant-isolated data with group-level organization
- **Biometric attendance** — face recognition enrollment and liveness verification
- **GPS geofencing** — configurable geofence zones with radius validation
- **Real-time dashboard** — WebSocket-powered live attendance map and stats
- **Shift management** — flexible shifts with grace periods and overnight support
- **Approval workflows** — attendance corrections, device changes, leave requests
- **Offline support** — offline clock-in/out with sync and conflict resolution
- **Reports & export** — Excel/PDF attendance reports with date range filtering
- **Audit logging** — full audit trail for compliance
- **Arabic/RTL support** — full i18n with English and Arabic

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5, Django REST Framework, Channels (WebSocket) |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, Zustand |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7, Celery |
| Auth | JWT (SimpleJWT) with token rotation and blacklisting |
| Biometric | face_recognition (dlib), AES-256 encrypted templates |
| Deployment | Docker, Nginx, Gunicorn + Uvicorn |

## Project Structure

```
attendance/
  backend/
    apps/
      accounts/       # User model, auth, employee profiles
      attendance/     # Shifts, policies, clock-in/out, validators
      approvals/      # Generic approval workflow
      biometric/      # Face enrollment and verification
      core/           # Base models, middleware, permissions, audit
      devices/        # Device registration and management
      integration/    # HRIS webhook integration
      projects/       # Project and assignment management
      tenants/        # Tenant, group, department models
    config/           # Django settings (base, dev, production)
  frontend/
    src/
      components/     # Shared UI components (layout, common)
      modules/        # Feature pages (auth, dashboard, attendance, etc.)
      services/       # API client and service layer
      store/          # Zustand state stores (auth, theme)
      types/          # TypeScript type definitions
      i18n/           # Internationalization (en, ar)
  nginx/              # Nginx configs (dev HTTP, prod HTTPS)
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.12+ (for backend development)

### 1. Clone and configure

```bash
git clone <repository-url>
cd attendance
cp .env.example .env
# Edit .env — at minimum change SECRET_KEY, passwords, and BIOMETRIC_ENCRYPTION_KEY
```

### 2. Start services

```bash
docker compose up -d
```

This starts PostgreSQL, Redis, the Django backend (with migrations), Celery worker, and Celery beat.

### 3. Create a superuser

```bash
docker compose exec backend python manage.py createsuperuser
```

### 4. Frontend development

```bash
cd frontend
npm install
npm run dev        # starts dev server on http://localhost:3000
```

The Vite dev server proxies `/api` requests to the backend at `localhost:8000`.

### 5. Run tests

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

## API Documentation

When running locally, interactive API docs are available at:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

In production, API docs require authentication.

## Environment Variables

See `.env.example` for all available configuration. Key variables:

| Variable | Description |
|----------|------------|
| `DJANGO_SECRET_KEY` | Django secret key (required, must be unique per environment) |
| `DJANGO_SETTINGS_MODULE` | `config.settings.development` or `config.settings.production` |
| `POSTGRES_*` | Database connection settings |
| `REDIS_URL` | Redis connection for channels and caching |
| `CELERY_BROKER_URL` | Celery message broker URL |
| `BIOMETRIC_ENCRYPTION_KEY` | AES-256 key for biometric template encryption |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | JWT access token lifetime (default: 30) |

## Production Deployment

See `.env.production.example` for production-specific configuration. Key differences from development:

- `DJANGO_DEBUG=False`
- `DJANGO_SETTINGS_MODULE=config.settings.production`
- SSL/HSTS enabled, secure cookies
- Structured JSON logging for log aggregation
- Stricter rate limiting (20/min anonymous, 200/min authenticated)

### HTTPS with Nginx

Production Nginx config is at `nginx/nginx.prod.conf`. Mount TLS certificates at:

```
/etc/nginx/ssl/fullchain.pem
/etc/nginx/ssl/privkey.pem
```

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push:

1. **Backend** — pytest against PostgreSQL + Redis services
2. **Frontend** — ESLint, TypeScript type check, Vitest tests
3. **Docker** — builds and pushes to GHCR (only after tests pass)

## License

Proprietary. All rights reserved.
