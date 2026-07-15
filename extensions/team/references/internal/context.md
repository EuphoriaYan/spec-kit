# Internal Context Resume

Use the canonical work directory from `docs/work-item-layout.md`:

```text
.specify/<feature|bugfix>/<work_id>/
```

## Open

1. Normalize `work_type` to `feature` or `bugfix` and validate `work_id`.
2. Open `work-context.yml` when present.
3. Read `spec.override.md` before `spec.md` only when the override exists and
   the current permission allows private requirement access.
4. Read `plan-and-task.md` and `plan-and-task-check.md` only for planning resume.
5. Expand to Code Graph, permissions, or evidence only when the current phase
   requires them.

## Create

After a stable Issue or requirement ID exists, create a minimal
`work-context.yml` and `context-pack.md` beside `spec.md`. Do not create a
second work directory or mirror complete artifact contents.

## Stop

Stop for human reconciliation when category, work ID, primary Issue, privacy
boundary, source revision, or artifact phase disagree. Never recover missing
facts from remembered chat when repository artifacts exist.
