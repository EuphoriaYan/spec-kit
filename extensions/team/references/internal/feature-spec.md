# Feature Specification Format

`spec.md` is a reviewed local snapshot of an accepted Feature Issue. It is
created by `speckit.team.plan-and-task`, not by Specify. Bugfix work does not
use this file.

```markdown
---
schema: ai-team-feature-spec/v1
work_id: "<issue-number-or-prefixed-id>"
work_type: feature
primary_issue: "<absolute-issue-url>"
issue_status: status/accept
issue_source:
  repository: "<host/owner/repository>"
  issue_number: "<number>"
  updated_at: "<remote-updated-time>"
  body_hash: "<hash-of-normalized-accepted-body>"
approval:
  decided_by: "<human-or-governance-body>"
  evidence_url: "<issue-or-decision-comment-url>"
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

Before writing the snapshot, summarize the current Issue body and discussion.
The accepted Issue body is primary. Include a change from comments only when a
human decision comment clearly accepts it. Do not merge suggestions, rejected
alternatives, or unresolved discussion into the Feature specification.
