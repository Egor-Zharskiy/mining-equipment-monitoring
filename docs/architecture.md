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

## Current Structure

```text
app/
  api/
    v1/
      endpoints/
      router.py
  core/
    monitoring.py
    events.py
  config/
    app_config.py
    auth_config.py
    db_config.py
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

This milestone has already been passed. The project now contains implemented
stages for:

1. access control
2. equipment registry
3. monitoring parameter catalog
4. threshold rules
5. telemetry ingestion
6. equipment state evaluation
7. events

## Current State

- The application is composed through `main.py` and `app/api/v1/router.py`.
- Database access is centralized in `app/db/session.py`.
- Configuration is split into `app/config/*`.
- The current implemented business modules are users/RBAC, equipment registry,
  monitoring parameters, threshold rules, telemetry readings, equipment states,
  and events.
