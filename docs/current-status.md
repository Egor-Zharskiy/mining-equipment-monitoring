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

## Current Focus
We are moving from threshold configuration toward telemetry ingestion.

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
Now the project should move into business modules in the following general order:

1. telemetry ingestion
2. equipment state evaluation
3. events
4. maintenance
5. notifications
6. analytics
7. audit improvements

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
