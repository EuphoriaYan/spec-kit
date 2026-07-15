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
2. Resolve the repository and privacy boundary. Ask one focused question when
   classification or publication safety changes the route.
3. Create or refine one primary Issue draft:
   - Feature/new project: User Stories, value, scenarios, scope, non-goals,
     acceptance points, privacy, and target release when decided.
   - Bug: observable behavior, expected behavior, reproduction evidence,
     impact, environment, and acceptance for the fix.
4. Present the exact Issue title, body, target repository, and labels. Ask the
   user to `approve publication`, `revise`, or `reject`. Revise until approved
   or rejected. This is the only approval owned by this skill.
5. After publication approval, publish through the configured repository tool
   when available. Otherwise return the approved draft for human publication
   and stop. New Issues use one matching `type/feature` or `type/bug` label and
   exactly one lifecycle state label: `state/draft`. Publication approval must
   not add `state/accepted`.
   Never assign `state/accepted`; publication does not imply acceptance.
6. Resolve one stable `work_id` from the created/linked Issue or approved
   requirement identifier. Do not use a display title as identity.
7. Normalize the directory category to `feature` or `bugfix`, then create
   `.specify/<category>/<work_id>/spec.md` from the internal Team template.
   Feature/new-project specs contain prioritized, independently testable User
   Stories. Bugfix specs contain observation, expected behavior, reproduction,
   environment, impact, and fix acceptance.
8. Create or update `work-context.yml` beside `spec.md`. Record category,
   `work_id`, primary Issue, phase, and the Spec path. Do not create the formal
   work directory until a stable Issue or approved requirement identifier
   exists.
9. Run a unified Issue/Spec check. Revise only the failed fields.

The Technical Committee's `state/accepted` decision is outside this skill. Do
not ask for it, simulate it, or continue into architecture planning. When an
existing Issue is already `state/accepted`, report that fact without changing
it; `speckit.team.plan-and-task` remains a separate invocation.

Never wait for `plan-and-task.md` to create the primary Issue. Do not use
`speckit.taskstoissues` for the primary work item. Optional child execution
tickets remain subordinate to the primary Issue.

## Output

```text
Team Specify Result:
- work type:
- work ID:
- primary Issue URL or approved draft:
- issue state:
- spec: .specify/<feature|bugfix>/<work_id>/spec.md
- user stories or reproduction:
- acceptance points:
- privacy boundary:
- unresolved questions:
- publication decision: approved / revise / rejected / not-needed
- next step: publish Issue / Technical Committee decision / speckit.team.plan-and-task / blocked
- result: published-draft / ready-for-external-decision / already-accepted / revise / blocked
```

Stop before architecture work when the Issue is unpublished, Feature Issue and
Spec disagree, private demand would leak, or acceptance criteria are not
testable.
