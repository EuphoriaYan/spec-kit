# Feature Specification Format

`spec.md` is a reviewed local snapshot of an accepted Feature Record or legacy
Feature Issue. It is created by `speckit.team.specify` in record-backed mode or
by `speckit.team.plan-and-task` in legacy Issue mode. Bugfix work does not use
this file.

```markdown
---
schema: ai-team-feature-spec/v1
work_id: "<issue-number-or-prefixed-id>"
work_type: feature
primary_issue: "<absolute-issue-url-or-local-requirement-record>"
feature_record: "<repository-relative-feature-record-or-empty>"
issue_status: "<status/accept-for-online-or-accepted-for-local>"
issue_source:
  kind: "<online-issue-or-local-record>"
  repository: "<host/owner/repository>"
  issue_number: "<number>"
  updated_at: "<remote-updated-time>"
  body_hash: "<hash-of-normalized-accepted-body>"
approval:
  decided_by: "<human-or-governance-body>"
  decision_source: "<online-issue-or-conversation>"
  evidence_url: "<issue-or-decision-comment-url-or-empty>"
  evidence_record: "<accepted-feature-record-or-empty>"
privacy_boundary: public-safe
---

# Feature Specification

## User Stories

### US-001: <Story title>

As a <user>, I want <capability>, so that <value>.

- Preconditions:
- Main scenario:
- Boundary or failure scenario:
- Verification (`VER-001`):

## Scope

## Non-Goals

## Open Questions
```

Use one section per independently understandable User Story. Give every
Verification a stable `VER-###` ID. `Verification`
means the observable behavior that later Plan, Tasks, self-tests, and review
can trace. It is not the governance decision represented by `status/accept`.

For an online Issue, summarize its current body and accepted discussion. For a
record-backed Feature, read the accepted Feature Record and its parent
Requirement authority. A parent without an Issue URL uses its accepted local
Requirement Record; never require an Issue label in that mode. Include a change
only when a human decision clearly accepts it. Do not merge suggestions,
rejected alternatives, or unresolved discussion into the Feature
specification.
