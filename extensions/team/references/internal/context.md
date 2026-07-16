# Internal Context Resume

Use exactly one canonical work root:

```text
Feature: .specify/feature/<work_id>/
Bugfix:  .specify/bugfix/<bug_slug>/
```

## Open Feature

1. Require `category: feature` and validate `work_id`.
2. Open `work-context.yml` when present.
3. Read `spec.override.md` before `spec.md` only with current permission.
4. Load Plan, check, permissions, Code Graph, or evidence only for the active
   phase.

## Open Bugfix

1. Require `category: bugfix` and validate `bug_slug`.
2. Open `work-context.yml` when present, then read `assessment.md`.
3. Load `fix.md`, `test.md`, Code Graph, or evidence only when the recorded
   phase requires them.
4. If an older Bugfix root has no context files, reconstruct a minimal package
   from its native artifacts; do not invent missing facts.

## Create Or Update

Keep `work-context.yml` machine-readable and `context-pack.md` concise. Record
identity, source summary, phase, source revision, artifact paths, unresolved
items, last completed Skill, and next Skill. Preserve unknown fields and never
mirror complete artifact contents.

## Stop

Stop for human reconciliation when category, identity, source, privacy
boundary, source revision, or artifact phase disagree. Never select the newest
directory silently or recover missing facts from remembered chat.
