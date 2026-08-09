# Project And Feature Lifecycle

Team separates the preferred online requirement ledger, repository Feature
Records, and local SDD work packages. When online Issue publication is
unavailable, an explicitly selected repository-local Requirement Record may
temporarily anchor the flow; it is a degraded collaboration mode and should be
replaced with a verified Issue URL when practical.

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
-> online PR (preferred) or explicit local-diff review target
-> Review
-> human merge
-> release update
```

Repository Feature Records are configurable committed artifacts. The default
location is recommended as `docs/features/`, but the first Feature Split must
ask the user and lock the chosen path before writing files. Local work packages
default to `.specify/<feature_id>/`; legacy `.specify/feature/<work_id>/`
packages remain readable.

Feature acceptance, detailed behavior confirmation, and delivery phase are
separate. `acceptance` confirms that the Feature is worth doing and that its
broad boundary is suitable for SDD. `behavior_acceptance` confirms the
simplified User Stories and observable Verification written back by Specify.
Specify must display the exact Feature Record path, the written-back User
Stories, and every Verification ID before asking a named human to confirm. The
Feature cannot leave `specifying` until that confirmation is recorded. Skills
cannot accept requirements, approve architecture/Plans, or merge PRs on behalf
of humans.

Online pull requests are the preferred review authority. A local review may
advance a Feature only when explicitly requested and when the Feature Record
stores an immutable Git commit or sha256 patch revision in
`delivery.review_target`; sentinel text such as `local=true` is never a PR URL.

## Approval Authority

State transitions follow the available authority instead of assuming every
draft has an Issue:

- an online Issue uses verified `status/accept` or `status/working` labels;
- a repository-local Requirement or Feature Record uses its structured
  `acceptance` decision;
- a local architecture or Plan review uses the named decision persisted in the
  reviewed artifact.

When a user explicitly approves the currently presented local Gate in
conversation, the active Skill records `accepted`, the named human, UTC time,
and `decision_source: conversation`, then validates the updated artifact. It
never asks for an Issue label or HTTP decision URL when no Issue exists.
Ambiguous acknowledgements are not approval, and an agent never supplies the
human decision itself.

## Requirement Authority

The normal authority is a verified online Requirement Issue URL because it
supports team visibility, durable discussion, and clear governance. If all
configured publication adapters are unavailable, Requirement may offer a
local record under `docs/requirements/` after explaining the trade-off and
receiving an explicit human choice. A local record must use a stable
`REQ-NNN` ID and contain a named, timestamped `accepted` or `working` decision
before Feature Split. Creating the file never grants acceptance.
