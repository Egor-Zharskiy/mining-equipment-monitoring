# Session Summary

This file is a compact summary of the work completed in the current dialogue.
Use it as a quick re-entry point after a session reload.

## Collaboration Rules
- Work by git-flow.
- Agree the branch before starting a new feature.
- Before non-documentation changes, first propose a plan and get approval.
- After every change, update documentation.
- Documentation-only updates may be made without extra approval.
- In test and demo data, human-readable text fields must be in Russian.
- Session chat context is not persistent, so important decisions must be written into docs.
- After each completed stage:
  - update or add automated tests for the stage
  - cover happy path, access control, main negative scenarios, and basic edge cases
  - perform self-review of architecture, duplication, access rights, migrations, and possible bugs
  - fix the issues found during self-review
  - verify that existing modules are not broken
  - provide a short completion report with implemented scope, added tests, coverage, and remaining risks

## Completed Project Stages
- Stage 1: access control foundation
  - users, roles, permissions
  - JWT auth
  - permission-based access checks
- Stage 2: equipment registry
  - `equipment_types`
  - `equipment`
  - CRUD, business validations, API tests
- Stage 3: monitoring parameters
  - `parameters`
  - `equipment_type_parameters`
  - CRUD, bindings, business validations, API tests
- Stage 4: threshold rules
  - `threshold_rules`
  - CRUD, threshold validation, RBAC permissions, API tests
- Stage 5: telemetry ingestion
  - `telemetry_readings`
  - raw telemetry ingestion, validation, history queries, API tests
- Stage 6: equipment state evaluation
  - `telemetry_evaluations`
  - `equipment_parameter_states`
  - `equipment_states`
  - metric status calculation, state aggregation, API tests
- Stage 7: events
  - `events`
  - transition-based event generation and read API
- Stage 8: maintenance
  - `maintenance_plans`
  - `maintenance_tasks`
  - `maintenance_records`
  - planning, task execution, and maintenance history API
- Stage 9: notifications
  - `notifications`
  - automatic and manual user notifications
  - unread counter and mark-as-read flow

## Current Branch
- Current branch: `main`
- Latest pushed commit: `689e2e9 Finalize monitoring MVP hardening`
- `main` is synchronized with `origin/main` after the MVP hardening commit.

## Stage 4 Details
- Added `threshold_rules` table, model, schemas, repository, service, routes, and tests.
- Added RBAC permissions:
  - `threshold_rules.read`
  - `threshold_rules.manage`
- Added validation rules:
  - rule allowed only for an existing `equipment_type_parameters` binding
  - at least one threshold value must be set
  - threshold ordering must be logically consistent
  - duplicate rules by `equipment_type_id + parameter_id` are forbidden
  - `PATCH` validates the final combined state, not only incoming fields

## Stage 5 Details
- Added `telemetry_readings` table, model, schemas, repository, service, routes, and tests.
- Reused existing RBAC permissions:
  - `telemetry.read`
  - `telemetry.create`
- Added validation rules:
  - reading allowed only for an existing `equipment`
  - reading allowed only for an existing `parameter`
  - parameter must be assigned to the target equipment type through `equipment_type_parameters`
  - `measured_at` must include timezone information
  - `measured_at` cannot be more than 5 minutes in the future
- Added read endpoints with filtering by:
  - `equipment_id`
  - `parameter_id`
  - `date_from`
  - `date_to`
  - `limit`

## Stage 6 Details
- Added `telemetry_evaluations`, `equipment_parameter_states`, and `equipment_states` tables with models, repositories, services, routes, and tests.
- Added automatic telemetry evaluation during ingestion using active `threshold_rules`.
- Added metric status calculation rules:
  - `critical` when value violates `critical_min` or `critical_max`
  - `warning` when value violates `warning_min` or `warning_max` without reaching `critical`
  - `normal` otherwise
- Added current per-parameter state snapshots for each equipment unit.
- Added aggregated equipment status derivation rules:
  - if any parameter is `critical` -> equipment is `critical`
  - else if any parameter is `warning` -> equipment is `warning`
  - else -> equipment is `normal`
- Added current equipment state read endpoints:
  - list with optional status filter
  - detailed per-equipment current state with parameter snapshots

## Stage 7 Details
- Added `events` table, model, repository, service, routes, and tests.
- Added automatic event generation for meaningful state transitions:
  - `parameter_warning`
  - `parameter_critical`
  - `parameter_recovered`
  - `equipment_warning`
  - `equipment_critical`
  - `equipment_recovered`
- Added event read endpoints with filtering by:
  - `equipment_id`
  - `parameter_id`
  - `severity`
  - `event_type`
  - `limit`
- Events are generated from Stage 6 state transitions, not directly from raw telemetry.

## Stage 8 Details
- Added `maintenance_plans`, `maintenance_tasks`, and `maintenance_records` tables with models, repositories, services, routes, and tests.
- Added maintenance plans targeted to either:
  - `equipment_type`
  - specific `equipment`
- Added maintenance task flow:
  - create task manually
  - optionally create task from an active maintenance plan
  - move task to `in_progress`
  - complete task through a dedicated completion endpoint
- Added maintenance completion history:
  - completion creates a `maintenance_record`
  - task status is moved to `done`
  - duplicate completion is rejected
- Added maintenance API filters for:
  - plans by target and `is_active`
  - tasks by `equipment_id`, `status`, `priority`, `assigned_to_user_id`
  - records by `equipment_id`, `task_id`, `performed_by_user_id`, and date range
- Added RBAC protection:
  - `maintenance.read`
  - `maintenance.manage`
- Added validation rules:
  - maintenance plan must target exactly one entity
  - maintenance plan requires `interval_hours` or `interval_days`
  - inactive maintenance plan cannot create tasks
  - plan target must be compatible with target equipment
  - task completion must go through the completion endpoint
- completed or cancelled tasks cannot be completed again
- record date range filters validate `date_from <= date_to`

## Stage 9 Details
- Added `notifications` table with model, repository, service, routes, and tests.
- Added notification channels:
  - `internal`
  - `email`
- Added notification types:
  - `event_critical`
  - `event_warning`
  - `upcoming_maintenance`
  - `manual`
- Added automatic notification generation for:
  - critical monitoring events
  - warning monitoring events
  - upcoming maintenance tasks due within the configured window
- Added runtime feature flag:
  - `ENABLE_RUNTIME_NOTIFICATIONS`
  - automatic notification generation is enabled by default and can be disabled with `ENABLE_RUNTIME_NOTIFICATIONS=false`
  - manual notification API and notification read API remain available
- Added manual notification creation endpoint for users with `notifications.manage`.
- Added notification read flow for users with `notifications.read`:
  - list notifications
  - filter by channel, type, and read status
  - get a single notification
  - unread count
  - mark as read
- Added real SMTP delivery support for email-channel notifications:
  - delivery is enabled only when `MAIL_ENABLED=true`
  - SMTP settings are read from `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM_EMAIL`, `MAIL_FROM_NAME`, `MAIL_USE_TLS`, and `MAIL_USE_SSL`
  - if SMTP delivery is disabled or fails, the notification record remains available in the system
- Added validation rules:
  - notification recipient must exist
  - notification channel filter must be supported
  - notification type filter must be supported
  - notification read access is limited to the recipient
  - upcoming maintenance notification is not duplicated on repeated task updates
- Email notifications are stored as notification-channel records; external email delivery is available through SMTP configuration.

## Verification Already Performed
- `poetry run alembic upgrade head` completed successfully.
- `poetry run pytest -q` completed successfully with `102 passed` after Stage 9 implementation.
- Manual smoke-checks through real API requests were performed for:
  - auth
  - equipment types
  - parameters
  - equipment type parameters
  - threshold rules
  - telemetry readings
  - equipment states
  - events
  - maintenance plans
  - maintenance tasks
  - maintenance records
  - notifications

## Local Development Data
- Local DB contains manual demo data for:
  - `parameters`
  - `equipment_type_parameters`
  - `threshold_rules`
- Details are tracked in `docs/local-data.md`.
- Base threshold rules were inserted for all current equipment type parameter bindings.

## Final Hardening
- Access control was tightened for `roles` and `permissions` endpoints.
- Bearer authentication now rejects inactive users even when they still hold a valid token.
- `PATCH` behavior for nullable fields was corrected so explicit `null` clears values instead of being ignored.
- Legacy unused entry points `db.py` and `app/routes/base_router.py` were removed from the active codebase.

## Current Functional Scope
The backend currently supports:
- authentication and permission checks
- user, role, and permission management foundation
- equipment types and equipment registry
- monitoring parameter catalog
- parameter-to-equipment-type bindings
- threshold rule management
- raw telemetry ingestion and telemetry history queries
- telemetry evaluation and current equipment state snapshots
- automatic monitoring event generation and event journal queries
- maintenance planning, maintenance task execution, and maintenance history
- internal and email-channel notification records with automatic and manual creation flows

## Next Logical Step
- Post-MVP hardening or enhancement track selection

## Stage 10 Completed
- Implemented analytics endpoints for:
  - `/analytics/overview`
  - `/analytics/equipment-status`
  - `/analytics/events`
  - `/analytics/telemetry-history`
  - `/analytics/maintenance`
  - `/analytics/notifications`
- Added read-only analytics layer:
  - repository aggregations over equipment states, events, telemetry history, maintenance tasks, and notifications
  - service-level validation and response shaping for dashboard use cases
- Added API tests covering:
  - happy path dashboard aggregation flows
  - access control via `analytics.read`
  - core negative scenarios for invalid filters and unknown entities
  - edge cases such as equipment without current state and empty telemetry history
- During Stage 10 self-review, fixed a Stage 9 bug:
  - upcoming maintenance notifications were incorrectly created for already overdue tasks
  - notification generation now skips `due_at < now` and only targets truly upcoming tasks
- Verification:
  - `poetry run pytest -q app/tests/api/test_analytics_api.py` -> `6 passed`
  - `poetry run pytest -q app/tests/api/test_notification_api.py app/tests/api/test_analytics_api.py` -> `14 passed`
  - `poetry run pytest -q` -> `108 passed in 500.57s`

## After Analytics
- audit improvements

## Stage 11 Completed
- Implemented audit log storage and read API:
  - `/audit-logs/`
  - `/audit-logs/{audit_log_id}`
- Added automatic audit records for important successful write actions including:
  - authentication login
  - users, roles, permissions
  - equipment types, equipment, parameter bindings, parameters
  - threshold rules
  - telemetry ingestion
  - maintenance plans and tasks
  - manual notification creation and mark-as-read
- Added API tests covering:
  - happy path audit capture and filtering
  - access control via `audit.read`
  - negative scenarios such as invalid date range and unknown ids
  - edge cases including sanitized sensitive fields and absence of audit rows for failed mutations
- Verification:
  - `poetry run alembic upgrade head`
  - `poetry run pytest -q app/tests/api/test_audit_api.py app/tests/api/test_auth_and_access_api.py app/tests/api/test_equipment_api.py` -> `21 passed`
  - `poetry run pytest -q app/tests/api/test_parameter_api.py app/tests/api/test_threshold_rule_api.py` -> `31 passed`
  - `poetry run pytest -q` -> `113 passed in 322.90s`

## After Audit
- choose post-MVP hardening or enhancement scope

## Final MVP Hardening Completed
- Removed frontend demo-data fallback:
  - deleted `frontend/src/api/demoData.js`
  - deleted `frontend/src/components/DataFallbackNotice.jsx`
  - frontend pages now use real API data, empty states, and error alerts instead of mocked fallback data
- Added centralized backend logging:
  - `app/core/logging_config.py`
  - request logging middleware in `main.py`
  - `X-Request-ID` response header and request-id propagation into business logs
  - `LOG_LEVEL`, `LOG_FORMAT`, and `LOG_REQUESTS` runtime controls
- Added business logs for:
  - authentication outcomes
  - telemetry ingestion and processing
  - equipment state evaluation and status changes
  - monitoring event creation
  - notification creation and email delivery
  - maintenance task creation, updates, and completion
  - audit log creation
- Hardened email delivery:
  - email-channel notifications are still stored in the database
  - real SMTP delivery is still controlled by `MAIL_ENABLED`
  - SMTP send attempts are detached from the primary HTTP response path through `asyncio.create_task`
  - slow or unavailable SMTP no longer blocks telemetry ingestion or maintenance task creation
  - delivered email notifications are marked with `delivered_at` when delivery succeeds
- Added event follow-up workflow:
  - `POST /events/{event_id}/maintenance-task`
  - requires `events.read` and `maintenance.manage`
  - creates a maintenance task for the event equipment
  - writes audit action `create_from_event`
  - frontend events page has a `Задача ТО` action and dialog
- Added `scripts/seed_demo.py`:
  - idempotent local demo seed
  - creates demo users, equipment types, equipment, parameters, bindings, threshold rules, telemetry, events, maintenance plan, open task, and completed task
  - uses disabled email delivery internally to avoid real SMTP sends during seeding
- Demo credentials after seed:
  - `demo.admin@example.com` / `Demo12345!`
  - `demo.manager@example.com` / `Demo12345!`
  - `demo.technician@example.com` / `Demo12345!`
- Demo equipment codes after seed:
  - `DEMO-HT-118`
  - `DEMO-EX-204`
  - `DEMO-DR-32`

## Final Verification
- `poetry run python scripts/seed_demo.py` -> completed successfully
- `poetry run pytest -q app/tests` -> `121 passed`
- `npm run lint` -> passed
- `npm run build` -> passed
- live HTTP E2E smoke scenario -> `21/21` checks passed
- backend and frontend were started locally:
  - backend: `http://127.0.0.1:8000`
  - frontend: `http://127.0.0.1:5173`
- live HTTP scenario covered:
  - frontend availability
  - backend OpenAPI availability
  - demo user login
  - analytics overview and dashboard endpoints
  - seed equipment and parameter lookup
  - normal telemetry ingestion
  - critical telemetry ingestion
  - critical event generation
  - maintenance task creation from event
  - notification unread count
  - audit log read API
  - RBAC denial for manager without `maintenance.manage`
  - RBAC denial for manager without `telemetry.create`
- SMTP non-blocking check with `MAIL_ENABLED=true`:
  - maintenance task creation returned `201` in `0.08s`
  - SMTP itself timed out in the local environment, but the API request was not blocked or crashed

## Current Verdict
- Backend MVP business logic is working for the implemented diploma scope.
- Frontend is wired to real backend data and builds successfully.
- The remaining high-value work is documentation and packaging:
  - README
  - `.env.example`
  - defense demo checklist
  - optional CI
- Optional post-MVP features such as Excel export, WebSocket realtime updates, Redis caching, SMS, GPS maps, and ML predictions are not required for the current diploma MVP.
