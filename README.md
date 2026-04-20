# Mining Equipment Monitoring

Web application for monitoring the technical condition of mining equipment based
on telemetry, threshold rules, events, maintenance workflows, notifications, and
analytics.

The project was built as a bachelor diploma MVP. The main goal is not only to
store telemetry, but to turn incoming measurements into operational decisions:
equipment states, monitoring events, maintenance tasks, notifications, audit
records, and dashboard analytics.

## What The System Does

- Manages users, roles, permissions, and JWT authentication.
- Stores equipment types and concrete equipment units.
- Defines monitoring parameters and binds them to equipment types.
- Stores threshold rules for normal, warning, and critical states.
- Accepts telemetry readings through API.
- Evaluates telemetry against threshold rules.
- Maintains current equipment and parameter state snapshots.
- Generates monitoring events for warning, critical, and recovery transitions.
- Creates maintenance plans, maintenance tasks, and completion records.
- Creates internal and email-channel notifications.
- Sends SMTP emails in the background when mail delivery is enabled.
- Stores audit logs for important write actions.
- Provides analytics endpoints for dashboard screens.
- Provides a React frontend connected to real backend API data.

## Tech Stack

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy 2.x async ORM
- PostgreSQL
- Alembic
- PyJWT
- pytest

### Frontend

- React 19
- Vite
- Material UI
- TanStack Query
- Recharts
- Axios

## Repository Structure

```text
app/
  api/v1/endpoints/      FastAPI route handlers
  config/                application, auth, database, and mail config
  core/                  shared constants, logging, domain helpers
  db/                    SQLAlchemy engine/session setup
  models/                ORM models
  repositories/          data access layer
  schemas/               Pydantic schemas
  services/              business logic
  tests/                 backend tests
alembic/                 database migrations
docs/                    local project documentation
frontend/                React frontend
scripts/seed_demo.py     repeatable local demo data
main.py                  FastAPI application entry point
docker-compose.yaml      local PostgreSQL service
```

## Main Business Flow

```text
Telemetry reading
  -> threshold evaluation
  -> parameter state update
  -> equipment state update
  -> warning/critical/recovery event
  -> notification records
  -> optional background SMTP delivery
  -> maintenance task from event
  -> audit trail
  -> analytics dashboards
```

## Requirements

- Python 3.12
- Poetry
- Node.js and npm
- Docker or local PostgreSQL

## Environment Variables

Create `.env` in the project root. Do not commit real secrets.

Minimal local example:

```dotenv
PG_USER=admin
PG_PASSWORD=admin
PG_DB=mine_equip
PG_EXTERNAL_PORT=5434
PG_INTERNAL_PORT=5432

SQLALCHEMY_URL_LOCAL=postgresql+asyncpg://admin:admin@localhost:5434/mine_equip

AUTH_SECRET_KEY=change-this-local-secret
AUTH_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=60

CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

ENABLE_RUNTIME_NOTIFICATIONS=true

MAIL_ENABLED=false
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM_EMAIL=
MAIL_FROM_NAME="Mining Equipment Monitoring"
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_TIMEOUT_SECONDS=10

LOG_LEVEL=INFO
LOG_FORMAT=plain
LOG_REQUESTS=true
```

Frontend may use:

```dotenv
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

If `VITE_API_URL` is not set, the frontend uses
`http://localhost:8000/api/v1` by default.

## Local Setup

### 1. Start PostgreSQL

```bash
docker compose up -d mining_equipment_db
```

The current `docker-compose.yaml` is focused on the database service. Backend and
frontend are started manually during development.

### 2. Install Backend Dependencies

```bash
poetry install
```

### 3. Apply Migrations

```bash
poetry run alembic upgrade head
```

### 4. Seed Demo Data

```bash
poetry run python scripts/seed_demo.py
```

The seed is idempotent and safe to run multiple times.

Demo users:

```text
admin:      demo.admin@example.com / Demo12345!
manager:    demo.manager@example.com / Demo12345!
technician: demo.technician@example.com / Demo12345!
```

Demo equipment codes:

```text
DEMO-HT-118
DEMO-EX-204
DEMO-DR-32
```

### 5. Run Backend

```bash
poetry run uvicorn main:app --host 127.0.0.1 --port 8000
```

Backend URLs:

```text
API:         http://127.0.0.1:8000/api/v1
Swagger UI:  http://127.0.0.1:8000/docs
OpenAPI:     http://127.0.0.1:8000/openapi.json
```

### 6. Run Frontend

```bash
cd frontend
npm install
VITE_API_URL=http://127.0.0.1:8000/api/v1 npm run dev -- --host 127.0.0.1 --port 5173
```

Frontend URL:

```text
http://127.0.0.1:5173
```

## Verification

Backend tests:

```bash
poetry run pytest -q app/tests
```

Frontend lint:

```bash
cd frontend
npm run lint
```

Frontend production build:

```bash
cd frontend
npm run build
```

Latest verified baseline:

```text
Backend tests: 121 passed
Frontend lint: passed
Frontend build: passed
Live HTTP E2E smoke scenario: 21/21 checks passed
```

## Demo Scenario For Defense

1. Start PostgreSQL, backend, and frontend.
2. Run `poetry run python scripts/seed_demo.py`.
3. Log in as `demo.admin@example.com`.
4. Open dashboard and verify equipment, events, maintenance, and notifications.
5. Open equipment details for `DEMO-HT-118`.
6. Send a normal telemetry reading and verify `normal` evaluation.
7. Send a critical telemetry reading and verify critical equipment/event state.
8. Open events and create a maintenance task from the critical event.
9. Open maintenance tasks and verify the created task.
10. Open notifications and audit logs.
11. Log in as `demo.manager@example.com` and verify restricted write access.
12. Log in as `demo.technician@example.com` and verify operational permissions.

## Permissions And Roles

The project uses permission-based access control. Roles are collections of
permissions, and endpoints check permissions explicitly.

Default demo roles:

- `admin`: full platform access.
- `manager`: read-heavy role for monitoring, analytics, users, and audit.
- `technician`: operational role for telemetry, events, and maintenance work.

## Notifications And Email

Notifications are stored in the database for internal and email channels.

When `MAIL_ENABLED=false`, the system creates email-channel notification records
but does not contact SMTP.

When `MAIL_ENABLED=true`, the system attempts real SMTP delivery. SMTP work is
scheduled outside the primary HTTP response path, so slow or unavailable SMTP
does not block telemetry ingestion or maintenance task creation.

## Logging

Centralized logging is configured in `app/core/logging_config.py`.

Important runtime controls:

- `LOG_LEVEL`: logging level, default `INFO`.
- `LOG_FORMAT`: `plain` or `json`, default `plain`.
- `LOG_REQUESTS`: request logging toggle, default `true`.

Every HTTP response includes `X-Request-ID`. If a request already contains that
header, the same value is reused. Otherwise the backend generates a new request
id and attaches it to logs.

The backend logs business events such as authentication, telemetry ingestion,
state evaluation, event creation, notification creation, email delivery,
maintenance changes, and audit log creation. Passwords, access tokens, and SMTP
secrets are not logged.

## Documentation

Local documentation is kept in `docs/`:

- `docs/current-status.md` — current project status and latest verification.
- `docs/architecture.md` — architecture and module layout.
- `docs/domain-rules.md` — domain rules.
- `docs/local-data.md` — local seed and manual data notes.
- `docs/roadmap.md` — implemented roadmap stages.
- `docs/session-summary.md` — compact development history.

## Current Status

The diploma MVP scope is implemented:

- access control
- equipment registry
- monitoring parameters
- threshold rules
- telemetry ingestion
- equipment state evaluation
- events
- maintenance
- notifications
- analytics
- audit
- frontend screens for the main workflows
- reproducible local demo seed
- centralized logging
- non-blocking SMTP delivery path

Optional post-MVP features such as Excel export, WebSocket realtime updates,
Redis caching, GPS maps, SMS, ERP integration, and ML predictions are not
required for the current MVP.
