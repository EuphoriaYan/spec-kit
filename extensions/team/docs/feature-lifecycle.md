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
-> top-level design (L0) and review
-> Project Requirement Issue
-> human acceptance
-> module design (L1) and review
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
-> optional existing top-level design (L0) / module design (L1) context
-> optional architecture impact/delta
-> Feature Split and review
-> repository Feature Records and per-Feature decisions
-> per-Feature SDD
-> release tracking
```

Top-level design (L0) and module design (L1) are optional for an existing
project. Missing architecture documents
never block an ordinary Feature and must not be replaced with empty files.
Material architecture impact still requires an explicit delta and human review.

## Per-Feature SDD

```text
accepted Feature Record
-> Specify
-> interface and data structure design (L2), then Plan-and-Task
-> Plan Review and deterministic readiness checks
-> Implement code, tests, evidence, and architecture updates
-> online PR (preferred) or explicit local-diff review target
-> Review
-> human merge
-> release update
-> Complete backfills merge/release facts and marks the Feature done
```

Repository Feature Records are configurable committed artifacts. The default
location is recommended as `docs/features/`, but the first Feature Split must
ask the user and lock the chosen path before writing files. Local work packages
default to `.specify/<feature_id>/`; legacy `.specify/feature/<work_id>/`
packages remain readable.

Feature acceptance, detailed behavior confirmation, and delivery phase are
separate. `acceptance` confirms that the Feature is worth doing and that its
broad boundary is suitable for SDD. `behavior_acceptance` confirms the
team-visible User Stories and observable Verification written back by Specify.
Specify must display the exact Feature Record path, the written-back User
Stories, and every Verification ID before applying the configured
`feature_tracking.behavior_confirmation.mode`:

- `required` blocks leaving `specifying` until a named human decision is
  recorded;
- `advisory` presents the same review package and recommends confirmation, but
  an explicit human choice may continue without recording it;
- `disabled` delegates the decision to another workflow and does not write a
  local behavior decision.

New Team config templates use `required`. Existing repository configs that do
not contain the policy remain `advisory`, so an extension upgrade does not
retroactively block in-flight Features. Skills cannot accept requirements,
approve architecture/Plans, or merge PRs on behalf of humans.

Online pull requests are the preferred review authority. A local review may
advance a Feature only when explicitly requested and when the Feature Record
stores an immutable Git commit or sha256 patch revision in
`delivery.review_target`; sentinel text such as `local=true` is never a PR URL.

Review stops at `ready-to-merge`. `speckit.team.complete` is the only normal
Feature closure entry: it consumes already-existing merge and release facts,
validates them, and backfills the Feature Record to `done`. Complete does not
perform the merge, create the release, deploy, mutate the Catalog, or close the
parent Requirement.

Completion evidence is versioned as an opt-in repository policy. New Team
configs set `feature_tracking.completion.validation: required`. Repositories
whose older config omits the block use `legacy-compatible`: a historical
`done` record with none of the new release/completion fields remains valid, but
a partially populated new bundle is rejected. Running Team Complete always
writes the complete bundle. Teams may migrate old records and then explicitly
switch to `required`.

Git verification defaults to `best-effort`. Full immutable commit hashes and
safe `git-tag:<tag>` names may be backfilled when a shallow clone or maintenance
checkout cannot resolve remote history. When both facts exist locally, the tag
must contain the merged commit. Teams that guarantee a complete local object
database may select `git_verification: strict`. The operator's current `HEAD`
is never treated as release authority.

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
