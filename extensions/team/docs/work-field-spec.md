# Work Identity

Feature planning and Bugfix assessment begin at different points, so they use
different local keys instead of pretending one field covers both lifecycles.

## Feature

| Field | Values | Meaning |
|---|---|---|
| `work_type` | `feature`, `new-project`, `template` | routes to Feature planning |
| `work_id` | stable safe identifier | names `.specify/feature/<work_id>/` |

Use the numeric Issue ID for coding-repository work and
`enhancement-<issue-id>` for enhancement-repository work. The value must match
`[A-Za-z0-9][A-Za-z0-9._-]{0,127}`. The absolute Issue URL is the global
authority.

## Bugfix

| Field | Values | Meaning |
|---|---|---|
| `work_type` | `bugfix` | routes to Assess, Fix, and Review |
| `bug_slug` | stable safe slug | names `.specify/bugfix/<bug_slug>/` |

Assess may create `bug_slug` from a raw symptom without an Issue. Once the
assessment is approved, keep that slug stable. Fix uses the approved assessment
as its authority and records a supplied Issue URL in `fix.md` when present.

Several Bug Issues may share one `bug_slug` only when one root-cause change
resolves them together. Map every supplied Issue to its own reproduction and
verification evidence.
