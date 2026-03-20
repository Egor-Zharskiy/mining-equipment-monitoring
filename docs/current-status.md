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

## Current Focus
We are now moving from the access-control foundation to the domain part of the system.

The access module should be treated as the base for all future modules.

## What Is Considered Done at This Stage
- user model exists
- role model exists
- permissions model exists
- permissions are assigned through roles
- base access checks / permission logic exists
- the system has enough identity structure to continue implementing business modules

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

1. equipment types and equipment
2. monitoring parameters
3. type-parameter bindings
4. threshold rules
5. telemetry ingestion
6. equipment state evaluation
7. events
8. maintenance
9. notifications
10. analytics
11. audit improvements

## Important Reminder
This is a bachelor diploma backend project.
Priorities:
- clear architecture
- domain logic
- clean DB model
- realistic API design
- explainability for diploma defense