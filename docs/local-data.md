# Local Data

This file documents manual data loaded into the local development database.
It is not part of Alembic migrations and is intended only for local testing.

## 2026-03-23 Stage 3 Manual Seed

The local database was manually populated with test data for monitoring
parameters and equipment type parameter bindings.

### Parameters
- `temperature` — Температура (`C`)
- `vibration` — Вибрация (`mm/s`)
- `pressure` — Давление (`bar`)
- `engine_hours` — Моточасы (`h`)
- `load` — Нагрузка (`%`)
- `fuel_level` — Уровень топлива (`%`)
- `oil_pressure` — Давление масла (`bar`)
- `hydraulic_temperature` — Температура гидросистемы (`C`)

### Equipment Type Bindings
- `Буровая установка`: `temperature`, `vibration`, `pressure`, `engine_hours`, `load`, `fuel_level`
- `Дробилка`: `temperature`, `vibration`, `load`, `oil_pressure`
- `Самосвал`: `engine_hours`, `fuel_level`, `oil_pressure`, `temperature`, `load`
- `Экскаватор`: `engine_hours`, `hydraulic_temperature`, `pressure`, `fuel_level`, `load`

### Notes
- Data was inserted directly into the local database without Alembic migration.
- Inserts were made idempotent to avoid duplicate rows on repeated execution.
- On 2026-03-23, parameter `name` and `description` fields were normalized to Russian for local demo data.
- The current local database state contains 20 equipment type parameter bindings.

## 2026-03-23 Stage 4 Manual Seed

The local database was manually populated with base threshold rules for all
existing `equipment_type_parameters` bindings.

### Threshold Rule Templates
- `Температура`: warning max `80.0`, critical max `95.0`
- `Вибрация`: warning max `7.5`, critical max `12.0`
- `Давление`: warning min `4.0`, warning max `10.0`, critical min `2.5`, critical max `12.0`
- `Моточасы`: warning max `450.0`, critical max `500.0`
- `Нагрузка`: warning max `85.0`, critical max `95.0`
- `Уровень топлива`: warning min `20.0`, critical min `10.0`
- `Давление масла`: warning min `2.0`, warning max `6.5`, critical min `1.0`, critical max `8.0`
- `Температура гидросистемы`: warning max `75.0`, critical max `90.0`

### Stage 4 Coverage in Local DB
- Threshold rules were created for all 20 current equipment type parameter bindings.
- Human-readable values in local demo data remain in Russian.

## 2026-03-31 Stage 5 Manual Seed

The local database was manually populated with a minimal set of raw telemetry
history records for local API checks.

### Telemetry Readings
- `Буровая установка СБШ-01` (`DR-001`) — `temperature` = `72.5000`
- `Дробилка КСД-01` (`CR-001`) — `vibration` = `6.8000`
- `Самосвал БЕЛАЗ-01` (`HT-001`) — `fuel_level` = `58.0000`
- `Экскаватор ЭКГ-01` (`EXC-001`) — `hydraulic_temperature` = `68.2000`

### Notes
- Data was inserted directly into the local database without Alembic migration.
- Inserts were made idempotent by fixed record identifiers to avoid duplicates on repeated execution.
- Each telemetry record uses an existing `equipment` and a parameter already assigned through `equipment_type_parameters`.
- The current local database state contains 4 telemetry readings.

## 2026-04-20 Demo Seed Script

Local demo data is now standardized through `scripts/seed_demo.py`.
The script is intended for repeatable local testing and diploma defense
scenarios. It is idempotent and may be run multiple times.

### Run Command

```bash
poetry run python scripts/seed_demo.py
```

### Demo Users
- `demo.admin@example.com` / `Demo12345!` — admin role
- `demo.manager@example.com` / `Demo12345!` — manager role
- `demo.technician@example.com` / `Demo12345!` — technician role

### Demo Equipment
- `DEMO-HT-118` — `Демо: самосвал HT-118`
- `DEMO-EX-204` — `Демо: экскаватор EX-204`
- `DEMO-DR-32` — `Демо: буровая установка DR-32`

### Demo Monitoring Parameters
- `demo_engine_temperature` — temperature-style parameter for engine checks
- `demo_vibration` — vibration-style parameter
- `demo_hydraulic_pressure` — pressure-style parameter

### Demo Thresholds
- engine temperature:
  - warning max `80`
  - critical max `95`
- vibration:
  - warning max `6`
  - critical max `10`
- hydraulic pressure:
  - warning min `12`
  - critical min `10`

### Demo Telemetry and Workflow Data
- critical telemetry for `DEMO-HT-118` engine temperature
- warning telemetry for `DEMO-HT-118` vibration
- warning telemetry for `DEMO-EX-204` engine temperature
- normal telemetry for `DEMO-DR-32` hydraulic pressure
- maintenance plan for chassis diagnostics
- open maintenance task for checking the truck engine
- completed maintenance task and record for excavator diagnostics

### Notes
- The seed uses application services where appropriate, so telemetry can create evaluations, states, events, and notifications.
- The seed disables real SMTP delivery internally to avoid sending emails during local data preparation.
- Seed data is local demo data and must not be turned into Alembic migration data without a separate product decision.
