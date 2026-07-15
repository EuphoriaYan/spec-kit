# Issue Lifecycle

AI Team work is tracked with repository issues and labels. Issues are the
human-visible work ledger; Work Context Packages are only the AI reload context.

The first user message does not need an existing issue. Specify performs only
the privacy/classification preparation needed to publish safely. The Specify
role owns the demand record: one primary Issue plus one matching `spec.md`. The
requesting human approves the exact publication target, body, and labels inside
the skill. Publication creates `state/draft`; it never grants architecture
approval. The Technical Committee or delegated authority later changes a
Feature Issue to `state/accepted` outside the skill. Plan-and-Task may start only
after that repository decision is visible.

Create the primary Feature Issue before Plan and Tasks. It explains who needs
what, why it matters, the accepted scope, and how success is observed. It is
not an implementation checklist. `plan-and-task.md` is created later from the accepted
Spec and Plan and may contain LLD-level work. Spec Kit's optional
`speckit.taskstoissues` command is not part of the AI Team primary work-item
flow. Any child execution tickets created from Tasks must link to, and remain
subordinate to, the primary Feature Issue.

## Repository Roles

| Repository | Purpose | Allowed type labels |
|---|---|---|
| `enhancement_internal` | internal-only traceability for confidential enterprise feature demand | `type/feature` only |
| coding repository | public or project-controlled feature and bug work | `type/feature`, `type/bug` |

`enhancement_internal` is not a customer-facing repository. Enterprise
customers should not be expected to see it. Its purpose is internal traceability
for private demand, discussion, approval, wave planning, and sanitized handoff
URLs used by coding work.

Bug fixes do not belong in `enhancement_internal`. File bug issues in the
coding repository and start `speckit.team.specify` with the Bug Issue.

## State Labels

Every AI Team issue should have exactly one state label:

| State label | Meaning | Typical next state |
|---|---|---|
| `state/draft` | intake exists, scope or acceptance is not ready | `state/accepted`, `state/rejected`, `state/closed`, `state/superseded` |
| `state/accepted` | owner or Technical Committee accepted the work for planning | `state/working`, `state/superseded` |
| `state/working` | implementation or active planning is in progress | `state/finished`, `state/superseded` |
| `state/finished` | implementation and evidence are complete, awaiting closure or release bookkeeping | `state/closed` |
| `state/rejected` | proposal was not accepted before work started | terminal |
| `state/closed` | work is complete or intentionally closed with reason | terminal |
| `state/superseded` | replaced by another issue or requirement | terminal |

Do not use issue title, branch name, or local file path as the stable identity.
Use the issue URL plus the work slug rules in [work-field-spec.md](work-field-spec.md).

## Several Issues In One Change

A PR may close several coding issues only when they describe different
symptoms of one root-cause change. Keep one primary issue, list the others as
`also_resolves_issue_urls`, and map every issue to separate reproduction and
verification evidence. Use separate work units when root cause, approved
scope, rollback, or release risk differs.

## Handoff URLs

When coding work implements a feature from `enhancement_internal`, the relevant
role skill receives the internal issue or handoff URL.
The URL is allowed only when the operator and coding repository visibility are
permitted to read it. Public coding repositories should use a public-safe
summary instead of private internal links.
