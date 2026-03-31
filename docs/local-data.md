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
