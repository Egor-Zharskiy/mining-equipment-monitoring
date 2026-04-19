# Working Rules

This file captures the collaboration rules for this project. It is the
authoritative reference after session reloads.

## Collaboration Protocol
- Work by git-flow. Branch naming should be agreed before starting a feature.
- Before any non-documentation changes, propose a plan and get approval.
- Code must be production-quality: clean structure, clear naming, typed, and consistent.
- After every change, update docs to reflect the new state.
- Documentation updates may be done without extra confirmation.
- In test and demo data, human-readable text fields must be filled in Russian.
- Technical identifiers such as codes may remain stable in English when used as system keys.

## Stage Completion Checklist
After finishing each stage, always do the following before declaring it complete:

1. Write and/or update automated tests for that stage.
2. Ensure the tests cover:
   - happy path
   - access control
   - main negative scenarios
   - basic edge cases
3. Perform a self-review of the code:
   - architecture
   - logic duplication
   - access rights
   - migrations
   - possible bugs
4. Fix the issues found during self-review.
5. Verify that the new stage does not break already implemented modules.
6. At the end, provide a short report:
   - what was implemented
   - what tests were added
   - what exactly is covered
   - what risks or uncovered areas remain

## Interaction Template
Use this session flow unless explicitly overridden:
1. Restate the request and collect missing context.
2. Propose a short plan.
3. Implement changes.
4. Report tests (or state they were not run).
5. Update docs after each change.

## Context Persistence
Session context does not persist after reloads. All important state, progress,
and decisions must be written into docs.
