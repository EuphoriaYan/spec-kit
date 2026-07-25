---
description: "Clarify a project or existing-project requirement, establish required project-level context, and publish one Requirement Issue."
---

# Spec Kit Team Requirement

Own the entry into repository-backed Feature delivery. Produce one durable
Project/Requirement Issue; never create one remote Issue per Feature.

## Input

```text
$ARGUMENTS
```

Accept:

- `mode=new-project` for a project from 0 to 1;
- `mode=existing-project` for a new requirement in an existing project;
- a natural-language requirement;
- an existing Requirement Issue URL to resume.

If mode is ambiguous, ask one focused question. Defects belong to
`speckit.team.assess`.

## Requirement Clarification

Clarify the project or requirement goal, users, value, scope, non-goals,
observable outcomes, external prerequisites, privacy boundary, target
repository, and important quality constraints. A broad requirement may contain
many Features; do not prematurely turn subsystems or implementation layers into
Features.

## New-Project L0 Stage

For `mode=new-project`, create or update the repository's project-level L0
system-context document before publishing the Requirement Issue. Use the
configured architecture path when present, otherwise propose
`docs/architecture/l0-system-context.md`.

L0 covers goals, actors, external systems, system boundary, deployment context,
quality attributes, security/compliance boundary, and project-level
constraints. It must not contain subsystem or per-Feature implementation
design.

Present the L0 design and ask a human to choose:

- **accept L0**: record the named reviewer and continue;
- **revise L0**: revise the requested part and repeat the review;
- **pause**: preserve the draft and stop.

The Skill never approves L0 on behalf of a human.

## Existing-Project Rule

For `mode=existing-project`, do not require L0 or L1 documents. If they exist,
record their paths as optional context. If they do not exist, report
`architecture context: not-present` and continue without creating placeholder
documents or failing the Requirement flow.

## Requirement Issue

Publish one Project/Requirement Issue after clarification and, for a new
project, after L0 review. Include:

- requirement mode and scope;
- users, value, scenarios, scope, and non-goals;
- observable outcomes;
- external prerequisites;
- accepted L0 reference for a new project;
- optional existing architecture references for an existing project;
- explicit statement that Feature decomposition follows acceptance.

Use `type/feature` and `status/new-issue` until repositories configure
dedicated project/requirement labels. Publishing never grants acceptance.
Governance changes the Issue to `status/accept` outside this Skill.

Use an authenticated repository integration or CLI. For GitCode, read
`references/gitcode-host-contract.md` and perform its capability probe. Fall
back to complete paste-ready Markdown when publication is unavailable.

## Output

```text
Team Requirement Result:
- mode: new-project / existing-project
- Requirement Issue:
- status: published-new-issue / output-only / revise / paused / blocked
- requirement scope:
- L0: accepted / optional-existing / not-present / not-applicable
- L0 reviewer:
- optional L1 reference:
- target repository:
- next requirement gate: human status/accept
- next Skill after acceptance: speckit.team.feature-split
```

Stop on unresolved privacy boundaries, missing new-project L0 acceptance,
unreadable supplied Requirement Issues, or user pause.
