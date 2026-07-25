# Project And Feature Lifecycle

Team separates the remote requirement ledger, repository Feature Records, and
local SDD work packages.

## Project From 0 To 1

```text
overall requirement
-> clarification
-> L0 design and review
-> Project Requirement Issue
-> human acceptance
-> L1 design and review
-> Feature Catalog
-> Feature Split Review
-> repository Feature Records and per-Feature decisions
-> per-Feature SDD
-> project integration and release acceptance
```

## Existing-Project Requirement

```text
new requirement
-> Requirement Issue
-> human acceptance
-> optional existing L0/L1 context
-> optional architecture impact/delta
-> Feature Split and review
-> repository Feature Records and per-Feature decisions
-> per-Feature SDD
-> release tracking
```

L0/L1 are optional for an existing project. Missing architecture documents
never block an ordinary Feature and must not be replaced with empty files.
Material architecture impact still requires an explicit delta and human review.

## Per-Feature SDD

```text
accepted Feature Record
-> Specify
-> Plan-and-Task (L2)
-> Plan Review and deterministic readiness checks
-> Implement code, tests, evidence, and architecture updates
-> PR
-> Review
-> human merge
-> release update
```

Repository Feature Records are configurable committed artifacts. The default
location is recommended as `docs/features/`, but the first Feature Split must
ask the user and lock the chosen path before writing files. Local work packages
default to `.specify/<feature_id>/`; legacy `.specify/feature/<work_id>/`
packages remain readable.

Feature acceptance and delivery phase are separate. Skills cannot accept
requirements, approve architecture/Plans, or merge PRs on behalf of humans.
