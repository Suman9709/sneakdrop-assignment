# Running Sneakdrop locally

## Prerequisites

- Docker Desktop with Docker Compose v2.
- Optional: Python 3.14 and Pipenv, only when running Django outside Docker.

## Docker (recommended)

From the project root (`sneakdrop-assignment`):

```powershell
Copy-Item .env.example .env
docker compose -f docker.compose.yml up --build
```

The first start builds the backend and frontend images, creates PostgreSQL and
Redis volumes, runs Django migrations, then starts Django on
http://localhost:8000 and Vite on http://localhost:3000. Celery worker and beat
start after Django passes its database health check.
PostgreSQL and Redis are intentionally internal to the Compose network, avoiding
collisions with services already running on your machine.

Use `docker compose -f docker.compose.yml down` to stop the stack. Add `-v` only
when you deliberately want to erase the local PostgreSQL and Redis data.

## Run Django without Docker

Start PostgreSQL and Redis yourself, copy `.env.example` to `.env`, and make
sure `POSTGRES_HOST` and `REDIS_URL` refer to those local services. Then:

```powershell
Set-Location backend
pipenv sync --dev
pipenv run python manage.py migrate
pipenv run python manage.py runserver
```

## Current scope

The Docker, PostgreSQL, Redis, Django, and Celery foundation is configured.
The domain models, API endpoints, reservation/payment workflow, and
application-specific UI behavior still need to be implemented for the
assignment itself.
