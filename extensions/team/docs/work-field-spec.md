# Work Identity

Team skills pass only two identity fields:

| Field | Values | Meaning |
|---|---|---|
| `work_type` | `feature`, `new-project`, `template`, `bugfix` | routes to a canonical category |
| `work_id` | stable safe identifier | names the third-level directory |

`feature`, `new-project`, and `template` map to `.specify/feature/<work_id>/`.
`bugfix` maps to `.specify/bugfix/<work_id>/`.

Use the numeric Issue ID for coding-repository work and
`enhancement-<issue-id>` for enhancement-repository work. The value must match
`[A-Za-z0-9][A-Za-z0-9._-]{0,127}`. The absolute Issue URL is the global
identity. A title, branch name, or chat-generated slug is not stable identity.

Several Issues may share one `work_id` only when one root-cause change resolves
them together. Record one primary Issue and list the others in the work context
and Plan; each Issue still needs its own reproduction and verification evidence.
