# AI Team Context Bootstrap

Run this bootstrap at the start of every AI Team role, after every resume or
context compression, and before producing a phase artifact or gate result.
Do not rely on remembered chat content when a repository artifact exists.

## Level 0: Always Load

1. Confirm the repository root, repository role, active AI integration, and
   current branch.
2. Resolve exactly one `work_id`, category (`feature` or `bugfix`), primary
   work item, and current phase. Load
   `.specify/<category>/<work_id>/work-context.yml` and `context-pack.md` when
   they exist.
3. Treat source code and approved native artifacts as authoritative:
   `spec.md` for intended behavior, `plan-and-task.md` for architecture and
   execution, `plan-and-task-check.md` for readiness, Issue labels and recorded
   approvals for human decisions, and the Evidence Board for verification.
4. Stop when the work item, phase, repository boundary, owner decision, or
   public-contract authority is missing or contradictory. Never fill those
   gaps from chat memory.

If no stable work item exists, remain in Intake or Specify. Do not create a
formal Plan, Tasks, or implementation context yet.

## Level 1: Load Only For The Active Role

### Business / Product: Specify

Load the user's current request, the primary Issue or Issue draft, the native
spec template, and any customer-safe requirement handoff. Do not load an old
implementation plan as product intent. Produce one `spec.md` for one primary
Issue; that specification may contain multiple independently testable user
stories.

### Architect / Module Owner: Plan And Task

Load the accepted Issue, `spec.md` (or gitignored `spec.override.md` when the
private handoff mechanism produced it), repository architecture guidance,
relevant module documentation, and a Code Graph slice or source-structure
fallback. Produce `plan-and-task.md`, then run `scripts/check_plan_and_task.py`
to generate `plan-and-task-check.md`. Every implementation task must own or
reference a minimum self-test set; a model must not hand-write a passing check.

## Level 2: Expand On Evidence, Not Curiosity

Load release, security, dependency, operations, memory, or adjacent-module
material only when the current change touches that concern. Record why the
context radius expanded in the Work Context Package.

## Refresh Check

Before handing off or returning a gate result, re-read the current work item,
the artifact being produced, and `work-context.yml`. If they disagree, stop and
request human reconciliation. Update the Work Context Package with the last
completed command, current phase, produced artifacts, missing evidence, and
next command.
