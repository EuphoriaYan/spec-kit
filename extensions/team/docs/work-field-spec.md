# Work Identity

Team skills pass only two identity fields:

| Field | Values | Meaning |
|---|---|---|
| `work_type` | `feature`, `new-project`, `template`, `bugfix` | routes to a canonical category |
| `work_id` | stable safe identifier | names the third-level directory |

`feature`, `new-project`, and `template` map to `.specify/feature/<work_id>/`.
`bugfix` maps to `.specify/bugfix/<work_id>/`.

Prefer the primary Issue number or a durable requirement ID. The value must
match `[A-Za-z0-9][A-Za-z0-9._-]{0,127}`. A title, branch name, chat-generated
slug and temporary display name are not stable identities.

Several Issues may share one `work_id` only when one root-cause change resolves
them together. Record one primary Issue and list the others in `spec.md`; each
Issue still needs its own reproduction or acceptance evidence.
