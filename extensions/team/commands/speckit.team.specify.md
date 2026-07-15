---
description: "Business/Product role for turning plain-language demand or a reported defect into a reviewed Issue and a unified Team specification."
---

# Spec Kit Team Specify

Own the Business/Product role. Start from the user's language, not an
implementation proposal. Produce the primary collaboration Issue before
architecture planning or task decomposition.

## Bootstrap

1. Run `python .specify/extensions/team/scripts/init_role_context.py`.
2. Read the invariant and Business/Product sections of
   `.specify/extensions/team/docs/context-bootstrap.md`.
3. Load only these references when needed:
   - `.specify/extensions/team/docs/work-item-layout.md` for the canonical directory and files;
   - `.specify/extensions/team/references/internal/intake.md` for classification and privacy;
   - `.specify/extensions/team/docs/issue-lifecycle.md` for Issue labels and state;
   - `.specify/extensions/team/docs/repository-boundary.md` for public or confidential placement.

Do not load architecture or implementation chat history.

## Input

```text
$ARGUMENTS
```

## Flow

1. Classify the request as `bug`, `feature`, `new-project`, or `unclear`.
2. When the input is an existing
   `.specify/ai-team/intake/<intake_slug>/issue-draft.md`, load its sibling
   `request.md` and `specify-checklist.md`, verify that they remain inside the
   local Intake root, and resume from the first blocking checklist item. Do not
   restart discovery or discard answered items.
3. For a request without a stable Issue, create or resume
   `.specify/ai-team/intake/<intake_slug>/` using
   `templates/specify-checklist-template.md` and
   `templates/issue-draft-template.md`. Preserve the user's original wording in
   `request.md`.
4. Fill the Specify Checklist from user statements and repository evidence
   before asking questions. Then clarify progressively:
   - ask one focused blocking question at a time;
   - update the checklist and Issue draft after every answer;
   - do not ask for information already present in the request or source;
   - distinguish facts, user decisions, assumptions, and unresolved questions;
   - do not prescribe implementation or infer a Bug root cause.
   After each update, run `python
   .specify/extensions/team/scripts/check_specify_intake.py --intake-slug
   <intake_slug>` and use its `next` result to select the next question. The
   script checks completeness; it never supplies an answer.
   Continue until required common checks and the matching Feature/new-project or
   Bugfix checks are `ready`; mark only the non-matching type section
   `not-applicable`. A pending item that
   changes scope, publication safety, or testability blocks publication.
5. Resolve the repository and privacy boundary. Ask a focused question whenever
   classification or publication safety changes the route.
6. Create or refine one primary Issue draft:
   - Feature/new project: User Stories, value, scenarios, scope, non-goals,
     acceptance points, privacy, and target release when decided.
   - Bug: observable behavior, expected behavior, reproduction evidence,
     impact, environment, and acceptance for the fix.
7. Present the exact Issue title, body, target repository, labels, unresolved
   non-blocking questions, and local draft path only after the Intake check
   returns `ready`. Ask the user to choose exactly one publication action:
   - `publish automatically`: use the configured repository tool;
   - `save draft only`: do not publish and return the local `issue-draft.md` path;
   - `revise`: continue the clarification loop and present the updated draft;
   - `stop`: do not publish and return the retained local draft path.
   Saving or stopping publication is not a rejection of the requirement and
   must not add `state/rejected`. This publication choice is the only approval
   owned by this skill.
8. After `publish automatically`, publish only when the configured repository
   tool is available. If publication fails or no tool is available, keep
   `publication_status: not-published`, return the draft path and failure, and
   stop without pretending an Issue exists. New Issues use one matching
   `type/feature` or `type/bug` label and
   exactly one lifecycle state label: `state/draft`. Publication approval must
   not add `state/accepted`.
   Never assign `state/accepted`; publication does not imply acceptance.
9. Resolve one stable `work_id` from the created/linked Issue or approved
   requirement identifier. Do not use a display title as identity.
10. Normalize the directory category to `feature` or `bugfix`, then create
   `.specify/<category>/<work_id>/spec.md` from the internal Team template.
   Feature/new-project specs contain prioritized, independently testable User
   Stories. Bugfix specs contain observation, expected behavior, reproduction,
   environment, impact, and fix acceptance.
   New draft work leaves `approval.decided_by` and `approval.evidence_url`
   empty. For an already accepted Issue, copy the named decision maker and the
   exact Issue/comment URL only after reading that repository evidence; never
   infer or self-author an acceptance record.
11. Create or update `work-context.yml` beside `spec.md`. Record category,
   `work_id`, primary Issue, phase, and the Spec path. Do not create the formal
   work directory until a stable Issue or approved requirement identifier
   exists.
12. Run a unified Issue/Spec check. Revise only the failed fields.

The Technical Committee's `state/accepted` decision is outside this skill. Do
not ask for it, simulate it, or continue into architecture planning. When an
existing Issue is already `state/accepted`, report that fact without changing
it, and synchronize only its verifiable approval reference;
`speckit.team.plan-and-task` remains a separate invocation.

Never wait for `plan-and-task.md` to create the primary Issue. Do not use
`speckit.taskstoissues` for the primary work item. Optional child execution
tickets remain subordinate to the primary Issue.

## Output

```text
Team Specify Result:
- work type:
- work ID: stable ID or `not-assigned-before-publication`
- primary Issue URL or approved draft:
- Specify Checklist: .specify/ai-team/intake/<intake_slug>/specify-checklist.md
- retained Issue draft: .specify/ai-team/intake/<intake_slug>/issue-draft.md
- issue state:
- spec: .specify/<feature|bugfix>/<work_id>/spec.md or `not-created-before-publication`
- user stories or reproduction:
- acceptance points:
- privacy boundary:
- unresolved questions:
- publication decision: published-automatically / saved-draft / revise / stopped / not-needed
- next step: publish Issue / Technical Committee decision / speckit.team.plan-and-task / blocked
- result: published-draft / saved-draft / ready-for-external-decision / already-accepted / revise / blocked
```

Stop before architecture work when the Issue is unpublished, Feature Issue and
Spec disagree, private demand would leak, or acceptance criteria are not
testable.
