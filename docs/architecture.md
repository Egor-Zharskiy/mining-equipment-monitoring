# Project Architecture

## Goal

`FastAPI` backend for the `mining-equipment-monitoring` project focused on mining equipment condition monitoring.

## Project Identity

- Repository name: `mining-equipment-monitoring`
- Application title: `Mining Equipment Monitoring API`
- Main package root: `app`

## Core Stack

- `FastAPI` for the HTTP API
- `SQLAlchemy 2.x` + `asyncpg` for PostgreSQL access
- `Alembic` for migrations
- `Pydantic Settings` for configuration
- `pytest` for testing

## Target Structure

```text
app/
  api/
    v1/
      endpoints/
      router.py
  core/
    settings.py
  db/
    base.py
    session.py
  models/
  repositories/
  schemas/
  services/
  tests/
main.py
docs/
  architecture.md
```

## Layers

### `api`

HTTP layer. This is where routes, dependencies, response codes, and API versioning live.

### `core`

Application configuration: environment variables, project settings, and shared constants.

### `db`

Database connection, declarative base, and session infrastructure.

### `models`

ORM models for PostgreSQL tables.

### `schemas`

Pydantic request and response schemas for the API.

### `repositories`

Isolated data access. This layer works with ORM models and SQLAlchemy queries.

### `services`

Business logic. It orchestrates repositories and encapsulates domain rules.

### `tests`

Unit and integration tests.

## Recommended Data Flow

`request -> api endpoint -> service -> repository -> db`

## Nearest MVP

1. Introduce a single `Settings` entry point.
2. Move database session management into `app/db/session.py`.
3. Add `api/v1/router.py` as the route composition entry point.
4. Extract the first domain module, for example:
   - users
   - equipment
   - telemetry
   - events and alerts
5. Add Alembic migrations.
6. Add tests for core endpoints and services.

## Current State

- The project already contains `main.py`, `db.py`, a base route, and one user ORM model.
- A local `.venv` environment was created with Python `3.12.0`.
- The new structure scaffold was added without removing existing files so migration can happen incrementally.
