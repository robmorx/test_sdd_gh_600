<!--
Sync Impact Report (temporary review material — remove before committing this file)
- Version change: unversioned (template placeholders only) → 1.0.0
- Modified principles: none — this is the initial ratification; all five principles are new
- Added sections:
  - Core Principles — I. Test Coverage for Every Endpoint
  - Core Principles — II. No Destructive Database Operations Without Approval
  - Core Principles — III. One Task at a Time
  - Core Principles — IV. No New Dependencies Without Justification
  - Core Principles — V. Spec-Only Minimal Scope
  - Safety and Operational Constraints
  - Development Workflow and Review Gates
  - Governance
- Removed sections: none
- Follow-up TODOs: none — every placeholder in the resolved template was resolved from the
  user-supplied principles or from repository context (first-idea.md)
- Open question for the reviewer: PROJECT_NAME was inferred as "DevLog" from first-idea.md;
  rename it if the project is called something else
-->

# DevLog Constitution

## Core Principles

### I. Test Coverage for Every Endpoint
- Every endpoint MUST have automated tests that exercise it before it is considered complete.
- Tests MUST cover the success path, the validation/authorization failure path, and the
  server-error path of the endpoint under test.
- The test and the endpoint MUST land in the same change; a merge MUST NOT introduce an
  endpoint without its corresponding test.
- Tests MUST be deterministic and MUST NOT depend on live network calls or external services;
  external boundaries MUST be replaced with fixtures, fakes, or in-memory doubles.
- A change that alters endpoint behavior MUST update or extend the existing test in the same
  change; obsolete assertions MUST be removed rather than left to fail.
- Rationale: an endpoint without a test is an unverified public contract; regressions surface
  in production instead of in CI.

### II. No Destructive Database Operations Without Explicit Approval
- Destructive database operations MUST NOT be executed until the user gives explicit approval
  for that specific operation, in the conversation, immediately before it runs.
- Destructive operations include, at minimum: `DROP`, `TRUNCATE`, bulk `DELETE` (mass or
  unbounded by an explicit filter), schema resets, migrations that drop or rewrite existing
  data, `prisma migrate reset`, `db push --force`, seed/factory resets, and any script that
  recreates, wipes, or replaces a database or its schema.
- Approval MUST NOT be inferred from silence, from approval given for a different command or
  environment, or from general permission to continue working.
- When a destructive operation appears necessary, the workflow MUST stop, state the exact
  command, the target database and environment, and the scope of data loss, and MUST propose a
  non-destructive alternative (backup, disposable test database, additive migration, reversible
  script) before asking for approval.
- Rationale: data loss is irreversible and cannot be repaired by a later commit, so consent
  must be explicit, per operation, and informed.

### III. One Task at a Time
- Work MUST be performed one task at a time, following the order defined by the task plan.
- After a task is finished, the agent MUST stop and present the result for review, and MUST NOT
  begin the next task until the user has reviewed and approved it.
- A task counts as finished only when its code, its tests, and the evidence that they pass are
  all in place; partially implemented tasks MUST be reported as incomplete rather than hidden.
- Rationale: sequential, reviewable steps keep each diff small and auditable, and preserve a
  veto point where the user can redirect the work before errors compound.

### IV. No New Dependencies Without Justification
- No new runtime or development dependency may be added until the agent has explained to the
  user why it is required, what it replaces, and which alternatives were considered.
- The explanation MUST be given before the dependency is introduced, and the dependency MUST
  wait for the user's approval; a dependency already present in the tree is not pre-approved
  for new uses.
- The standard library and already-approved dependencies MUST be preferred; a new dependency is
  justified only when the existing stack demonstrably cannot satisfy the requirement.
- Approved dependencies MUST be pinned to a specific version and recorded in the project's
  manifest and lockfile.
- Rationale: dependencies are permanent maintenance, licensing, and supply-chain obligations
  and must never enter the project as an unconsidered side effect of a task.

### V. Spec-Only Minimal Scope
- The implementation MUST contain only the behavior explicitly described in the approved
  specification; no feature, endpoint, command, flag, screen, or abstraction outside the spec
  may be added.
- Functionality that is implied but not written in the spec MUST be raised as a clarification
  and approved before it is implemented.
- Unrequested refactoring, generalization, and opportunistic cleanup MUST be excluded from a
  feature change and deferred to a separate, explicitly requested task.
- Rationale: the spec is the contract under review; unrequested scope enlarges the test
  surface and the defect surface without any agreement to absorb it.

## Safety and Operational Constraints

- Environment targeting: destructive commands MUST never be pointed at a production, shared, or
  remote database. Disposable local or containerized test databases MUST be used for
  destructive verification instead.
- Non-destructive verification is the default: migrations MUST be additive where possible, and
  schema verification MUST be performed against a temporary database rather than the working
  one.
- Test data: automated tests MUST operate against ephemeral fixtures or transaction-scoped
  data and MUST NOT mutate the developer database.
- Dependency hygiene: manifest and lockfile MUST be updated together; transitive dependency
  additions inherited from a new package are part of the justification and MUST be disclosed.
- Scope: principle V is binding at all times; if an approved spec and this constitution
  conflict, the constitution wins until the user resolves the conflict explicitly.

## Development Workflow and Review Gates

- The workflow follows the Spec Kit sequence: specify → clarify → plan → tasks → implement,
  with each stage producing an artifact that the next stage consumes.
- Implementation proceeds strictly in task-plan order, one task per cycle, and each cycle ends
  with a stop for user review (see Principle III).
- A task is ready for review only when every gate below passes:
  1. The implementation matches the approved spec and adds nothing outside it.
  2. Every endpoint touched or added has automated tests covering success and failure paths.
  3. The full test suite passes.
  4. No destructive database operation was executed without recorded explicit approval.
  5. No dependency was added without a recorded explanation and approval.
  6. The change is committed with a message that describes the task it completes.
- Review requests MUST list the gates that were verified and the commands or evidence used to
  verify them, so the reviewer can check the claims cheaply.
- A failing gate MUST block the task from being reported as complete; the blocker MUST be
  stated explicitly rather than worked around silently.

## Governance

- This constitution is the highest-authority document in this project. Where a plan, task
  list, prompt, or convention conflicts with it, the constitution prevails and the conflict
  MUST be raised for resolution instead of being silently ignored.
- Amendments: propose changes through `/speckit.constitution`, stating the rationale and the
  affected principles, and update `Last Amended` on the same day the change is accepted.
  Amendments take effect when the user confirms them; until then the previous version stands.
- Versioning policy (semantic versioning of the constitution itself):
  - MAJOR: a principle is removed, redefined, or weakened, or a non-negotiable rule is relaxed.
  - MINOR: a principle or section is added, or existing guidance is materially expanded.
  - PATCH: clarifications, wording, typo fixes, or other non-semantic refinements.
- Compliance review: every task completion and every code review MUST verify the five core
  principles. Violations MUST be reported to the user with the offending command or change and
  MUST be resolved before the task is closed.
- Exceptions: any deviation from a non-negotiable rule requires explicit user approval recorded
  in the task notes or the review message, together with the reason and the compensating
  measure. Unrecorded deviations are violations.
- Unresolved items are tracked as `TODO(<FIELD_NAME>): <explanation>` markers in this file and
  MUST be listed in the Sync Impact Report until they are closed.
- The Sync Impact Report is temporary review material: it is generated by each amendment and
  MUST be removed before the amended constitution is committed.

**Version**: 1.0.0 | **Ratified**: 2026-10-20 | **Last Amended**: 2026-10-20
