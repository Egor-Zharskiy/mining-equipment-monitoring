# Backend Roadmap

## Goal
Build a backend for a web application that monitors the technical condition of mining equipment based on telemetry received through API.

---

## Stage 1 — Access Control
### Scope
- users
- roles
- permissions
- role_permissions
- JWT auth
- authorization rules

### Status
Implemented / in progress.

---

## Stage 2 — Equipment Registry
### Entities
- equipment_types
- equipment

### Scope
- create and manage equipment types
- create and manage equipment units
- store equipment metadata:
  - name
  - code
  - serial number
  - location
  - description
  - optional specifications
- link each equipment item to an equipment type

### Expected Result
The system knows what physical units are being monitored.

### Status
Implemented.

---

## Stage 3 — Monitoring Parameters
### Entities
- parameters
- equipment_type_parameters

### Scope
- define available monitoring parameters
- examples:
  - temperature
  - vibration
  - pressure
  - engine_hours
  - load
- define which parameters apply to which equipment types

### Expected Result
The system knows which metrics are relevant for each equipment type.

### Status
Implemented.

---

## Stage 4 — Threshold Rules
### Entities
- threshold_rules

### Scope
- define normal / warning / critical boundaries
- support:
  - warning_min
  - warning_max
  - critical_min
  - critical_max
- rules may be defined by equipment type and parameter

### Expected Result
The system can evaluate whether a metric is within normal range.

---

## Stage 5 — Telemetry Ingestion
### Entities
- telemetry_readings

### Scope
- receive telemetry data through API
- validate incoming payload
- store historical readings
- link each reading to:
  - equipment
  - parameter
  - measurement timestamp

### Expected Result
The system accumulates metric history.

---

## Stage 6 — Equipment State Evaluation
### Entities
- equipment_state

### Scope
- evaluate each incoming metric against threshold rules
- determine metric status:
  - normal
  - warning
  - critical
- derive overall equipment state
- update current state snapshot for each equipment item

### Expected Result
The system becomes a true monitoring system, not just storage.

---

## Stage 7 — Events
### Entities
- events

### Scope
- create events when:
  - metric exceeds threshold
  - equipment state changes
  - equipment recovers
  - maintenance-related conditions occur
- support filtering and history views

### Expected Result
The system provides a business-meaningful event journal.

---

## Stage 8 — Maintenance
### Entities
- maintenance_plans
- maintenance_tasks
- maintenance_records

### Scope
- define maintenance plans
- generate or manage maintenance tasks
- mark maintenance as completed
- store maintenance history

### Expected Result
Monitoring is connected with operational maintenance workflows.

---

## Stage 9 — Notifications
### Entities
- notifications

### Scope
- internal notifications
- email notifications
- trigger notifications for:
  - critical events
  - important warnings
  - upcoming maintenance

### Expected Result
The system not only detects issues but also informs responsible users.

---

## Stage 10 — Analytics
### Scope
- provide endpoints for dashboards
- counts by equipment status
- event counts by period
- parameter history for charts
- statistics by equipment type
- optional reliability indicators

### Expected Result
Frontend can display useful dashboards and trends.

---

## Stage 11 — Audit
### Entities
- audit_logs

### Scope
- track important user actions
- store who changed what and when

### Expected Result
Administrative actions become traceable.

---

## Not Mandatory for MVP
These features are optional and not part of the core first implementation:
- WebSocket realtime delivery
- GPS maps
- SMS notifications
- ERP / 1C integration
- PWA / QR workflows
- photo/video attachments
- ML / predictive analytics

## Optional Enhancements
- Redis caching
- background jobs
- Excel export
- advanced reporting
