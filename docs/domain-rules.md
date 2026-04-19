# Domain Rules

## Equipment vs Telemetry
`equipment` stores static information about an equipment unit:
- name
- code
- serial number
- location
- description
- optional technical specifications

Telemetry is stored separately and represents time-based measurements.

## Specifications
`equipment.specifications` is used only for static technical properties, for example:
- engine_power_kw
- bucket_capacity_m3
- weight_tons

It is not used for dynamic monitoring metrics.

## Monitoring Model
Monitoring metrics are not stored in the equipment table.

They are modeled through:
- parameters
- equipment_type_parameters
- telemetry_readings
- threshold_rules
- equipment_state
- events

## Parameter Evaluation Logic
Each incoming metric is evaluated against threshold rules.

A metric status can be:
- `normal`
- `warning`
- `critical`

Thresholds may include:
- `warning_min`
- `warning_max`
- `critical_min`
- `critical_max`

## Overall Equipment State Logic
The overall equipment status is derived from metric statuses:
- if any metric is `critical` → equipment is `critical`
- else if any metric is `warning` → equipment is `warning`
- else → equipment is `normal`

## Event Generation
Events should be created when:
- a metric exceeds threshold
- equipment changes state
- equipment recovers
- maintenance conditions are met

## Notification Logic
Notifications are created based on important events.
Some notifications are internal only.
Some notifications may also be delivered by email.

## Main Principle
The equipment table stores the identity of the monitored asset.
Telemetry tables store what happens to that asset over time.
State tables store the current derived condition.
Event tables store meaningful incidents and transitions.