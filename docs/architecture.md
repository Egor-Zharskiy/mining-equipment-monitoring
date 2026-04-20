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
    logging_config.py
    monitoring.py
    events.py
  config/
    app_config.py
    auth_config.py
    db_config.py
    mail_config.py
  db/
    base.py
    session.py
  models/
  repositories/
  schemas/
  services/
  tests/
frontend/
  src/
    api/
    auth/
    components/
    layout/
    pages/
scripts/
  seed_demo.py
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

## Observability

The API configures centralized logging in `app/core/logging_config.py`.

Runtime controls:

- `LOG_LEVEL`: standard Python logging level, defaults to `INFO`.
- `LOG_FORMAT`: `plain` or `json`, defaults to `plain`.
- `LOG_REQUESTS`: enables request access logs, defaults to `true`.

Every HTTP request receives an `X-Request-ID` response header. If the client
passes `X-Request-ID`, the same value is reused; otherwise the API generates a
new id. The request id is attached to logs through an async context variable, so
business logs from the same request can be correlated.

Logged business events include telemetry ingestion, state evaluation, monitoring
event creation, notification creation and email delivery, maintenance task
changes, audit log creation, and authentication outcomes. Request bodies,
passwords, access tokens, and SMTP secrets are intentionally not logged.

Email delivery is intentionally outside the critical HTTP response path.
Notification records are created in the request transaction, while the external
SMTP send is scheduled as a detached async task. If SMTP is unavailable, the API
request still succeeds and the failure is logged.

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
8. maintenance
9. notifications
10. analytics
11. audit

## Frontend Architecture

The frontend is a React application under `frontend/`. It calls the backend API
through `frontend/src/api/*`, stores auth state through the auth provider, and
uses permission-aware routing/navigation for access control in the UI.

Demo fallback data has been removed. Frontend pages now rely on real backend
responses and render empty/error states when the API has no data or fails.

The events page includes the operational follow-up flow for creating a
maintenance task from a monitoring event.

## Demo Data

Local demo data is created by `scripts/seed_demo.py`. The script is idempotent
and creates users, catalog data, telemetry, events, notifications, maintenance
plans, and maintenance tasks for manual checks and defense demos.

## Current State

- The application is composed through `main.py` and `app/api/v1/router.py`.
- Database access is centralized in `app/db/session.py`.
- Configuration is split into `app/config/*`.
- The current implemented business modules are users/RBAC, equipment registry,
  monitoring parameters, threshold rules, telemetry readings, equipment states,
  events, maintenance, notifications, analytics, and audit.
- The latest verification baseline is `121` passing backend tests, passing
  frontend lint/build, and a passing live HTTP E2E smoke scenario.
