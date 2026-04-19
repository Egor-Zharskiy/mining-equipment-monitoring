# Current Project Status

## Already Implemented
The following backend functionality is already implemented or started:

### Access / Identity
- users
- roles
- permissions
- role-permission relationships
- basic authorization model
- JWT-based authentication (if already implemented in codebase)
- foundational access control module

### Equipment Registry
- equipment types
- equipment catalog
- CRUD for equipment types and equipment
- equipment metadata and type assignment

### Monitoring Parameters
- parameter catalog
- equipment type to parameter bindings
- CRUD for parameters
- binding API for equipment type parameters
- API tests for success paths, access control, filtering, and core negative scenarios

### Threshold Rules
- threshold rules by equipment type and parameter
- CRUD for threshold rules
- validation against equipment type parameter bindings
- threshold ordering validation
- permission-protected API for read and management operations
- API tests for success paths, filtering, access control, and negative scenarios

### Telemetry Ingestion
- raw telemetry readings storage
- telemetry ingestion API with RBAC protection
- validation against existing equipment and parameter catalog
- validation against equipment type parameter bindings
- history queries with equipment, parameter, and date filters
- API tests for success paths, access control, filtering, and core negative scenarios

### Equipment State Evaluation
- telemetry evaluation against active threshold rules
- metric status calculation: `normal`, `warning`, `critical`
- current per-parameter state snapshots for equipment
- aggregated current equipment state snapshots
- automatic state updates during telemetry ingestion
- equipment state read API with detailed parameter state view
- API tests for transitions, recovery, filtering, access control, and negative scenarios

### Events
- automatic monitoring event generation from state transitions
- parameter-level events for `warning`, `critical`, and recovery to `normal`
- equipment-level events for `warning`, `critical`, and recovery to `normal`
- events read API with filtering by equipment, parameter, severity, and type
- API tests for generation, recovery transitions, filtering, access control, and negative scenarios

### Maintenance
- maintenance plans for equipment types or specific equipment units
- maintenance tasks bound to concrete equipment units
- maintenance completion records
- permission-protected maintenance API for planning, task execution, and record history
- validation of plan target compatibility and task completion flow
- API tests for happy path, access control, filtering, negative scenarios, and edge cases

### Notifications
- internal notifications for authenticated users
- email-channel notification records for important events and upcoming maintenance
- real SMTP email delivery for email-channel notifications when `MAIL_ENABLED=true`
- automatic notifications for critical and warning events are enabled by default and can be disabled through `ENABLE_RUNTIME_NOTIFICATIONS=false`
- automatic notifications for upcoming maintenance tasks are enabled by default and can be disabled through `ENABLE_RUNTIME_NOTIFICATIONS=false`
- manual notification creation API for administrative users
- notification read API with filters, unread count, and mark-as-read flow
- API tests for happy path, access control, negative scenarios, and edge cases
- SMTP delivery is controlled by `MAIL_ENABLED` and configured through environment variables:
  `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`,
  `MAIL_FROM_EMAIL`, `MAIL_FROM_NAME`, `MAIL_USE_TLS`, `MAIL_USE_SSL`

### Analytics
- dashboard-oriented analytics endpoints
- overview endpoint with equipment, event, maintenance, and notification totals
- equipment status distribution with per-type breakdown
- event analytics by severity, type, and timeline
- telemetry history API for charts with summary statistics
- maintenance workload analytics including overdue and upcoming tasks
- notification analytics by channel, type, and read state
- API tests for happy path, access control, negative scenarios, and edge cases

### Audit
- audit log storage for important successful write actions
- automatic audit records for authentication, catalog management, threshold rules, telemetry ingestion, maintenance actions, notifications, and user/role/permission changes
- audit read API with filtering by actor, action, resource, and date range
- API tests for happy path, access control, negative scenarios, and edge cases

## Current Focus
Audit is implemented. The current roadmap stages are complete through MVP scope.

The access module should be treated as the base for all future modules.

## What Is Considered Done at This Stage
- user model exists
- role model exists
- permissions model exists
- permissions are assigned through roles
- base access checks / permission logic exists
- the system has enough identity structure to continue implementing business modules
- equipment type model exists
- equipment model exists
- parameter model exists
- equipment type parameter binding model exists
- threshold rule model exists
- telemetry reading model exists
- telemetry evaluation model exists
- equipment parameter state model exists
- equipment state model exists
- event model exists
- maintenance plan model exists
- maintenance task model exists
- maintenance record model exists
- notification model exists
- analytics read API exists over monitoring, events, maintenance, and notifications data
- audit log model and audit read API exist

## What Must Be Preserved
- current auth/access architecture
- existing project structure
- separation of layers
- clean code style
- consistency in naming and patterns

## What Should Not Be Reworked Without Good Reason
- existing access-control design
- users / roles / permissions domain boundaries
- already working route/service/repository contracts

## Current Project Direction
Core MVP stages from access control through audit are implemented.

The next active target should be chosen from post-MVP hardening or enhancements, for example:

1. audit improvements
2. notification delivery hardening
3. analytics optimization

## Important Reminder
This is a bachelor diploma backend project.
Priorities:
- clear architecture
- domain logic
- clean DB model
- realistic API design
- explainability for diploma defense

## Local Development Data
- On 2026-03-23, the local development database was manually populated with Stage 3 test data for `parameters` and `equipment_type_parameters`.
- On 2026-03-23, the local development database was manually populated with Stage 4 base data for `threshold_rules`.
- Details are documented in `docs/local-data.md`.
