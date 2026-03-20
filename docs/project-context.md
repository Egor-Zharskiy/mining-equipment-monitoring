# Project Context

## Project Title
Backend for a bachelor diploma project:
**Web application for monitoring the technical condition of mining equipment**

## General Context
This project is focused on the **backend only**.

We do **not** implement:
- real sensors
- IoT protocols
- telemetry collection infrastructure
- device gateways

We assume that the system receives **ready telemetry data through API**.

## Core Idea
The core of the system is:
- receiving telemetry data for mining equipment
- storing telemetry history
- evaluating equipment condition
- detecting deviations from threshold rules
- registering events
- supporting maintenance workflows
- sending notifications
- providing data for dashboards and analytics

## Technology Stack
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 Async
- Alembic
- Pydantic v2
- Redis (optional for caching / background jobs / realtime)
- JWT authentication
- Docker

## Architectural Principles
- modular backend architecture
- layered structure:
  - models
  - schemas
  - repositories
  - services
  - routes
  - dependencies
  - core
- business logic must not be placed in routes
- repository layer handles DB access
- service layer handles domain logic
- routes should stay thin
- code should be clean, typed, extensible, and suitable for a diploma project

## Main User Roles
- `admin` — manages users, roles, permissions, equipment, threshold rules, and system configuration
- `manager` — reads equipment, events, analytics, maintenance data
- `technician` — works with maintenance tasks and operational equipment-related actions

## Main Planned Domains
1. Access Control
2. Equipment Registry
3. Monitoring
4. Events
5. Maintenance
6. Notifications
7. Analytics
8. Audit

## Main Planned Database Entities
- users
- roles
- permissions
- role_permissions
- equipment_types
- equipment
- parameters
- equipment_type_parameters
- telemetry_readings
- threshold_rules
- equipment_state
- events
- maintenance_plans
- maintenance_tasks
- maintenance_records
- notifications
- audit_logs

## Important Domain Rules
- equipment belongs to an equipment type
- equipment type defines supported monitored parameters
- telemetry readings come through API
- each reading is evaluated against threshold rules
- each metric can have a status: `normal`, `warning`, `critical`
- overall equipment state is derived from metric evaluations
- if at least one metric is critical, equipment state is critical
- if no critical metrics exist but at least one warning metric exists, equipment state is warning
- otherwise equipment state is normal
- state changes should create events
- important events can trigger notifications
- maintenance is linked to equipment and supports operational workflows

## Implementation Notes
- keep the system production-like, not toy-like
- do not collapse everything into a single CRUD file
- prefer explicit, readable structure
- preserve project consistency when adding new modules