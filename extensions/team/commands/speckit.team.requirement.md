---
description: "Clarify a project or existing-project requirement, establish required project-level context, and publish one Requirement Issue."
---

# Spec Kit Team Requirement

Own the entry into repository-backed Feature delivery. Prefer one durable
online Project/Requirement Issue for team collaboration and unambiguous
governance; never create one remote Issue per Feature. A repository-local
Requirement Record is a degraded fallback, not an equal default.

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

## New-Project Top-Level Design (L0) Stage

For `mode=new-project`, create or update the repository's project-level
top-level design (L0)
system-context document before publishing the Requirement Issue. Use the
configured architecture path when present, otherwise propose
`docs/architecture/l0-system-context.md`.

Top-level design (L0) covers goals, actors, external systems, system boundary, deployment context,
quality attributes, security/compliance boundary, and project-level
constraints. It must not contain subsystem or per-Feature implementation
design.

Present the top-level design (L0) and ask a human to choose:

- **accept top-level design (L0)**: record the named reviewer and continue;
- **revise top-level design (L0)**: revise the requested part and repeat the review;
- **pause**: preserve the draft and stop.

The Skill never approves top-level design (L0) on behalf of a human.

## Existing-Project Rule

For `mode=existing-project`, do not require top-level design (L0) or module
design (L1) documents. If they exist,
record their paths as optional context. If they do not exist, report
`architecture context: not-present` and continue without creating placeholder
documents or failing the Requirement flow.

## Requirement Issue

Publish one Project/Requirement Issue after clarification and, for a new
project, after top-level design (L0) review. Include:

- requirement mode and scope;
- users, value, scenarios, scope, and non-goals;
- observable outcomes;
- external prerequisites;
- accepted top-level design (L0) reference for a new project;
- optional existing architecture references for an existing project;
- explicit statement that Feature decomposition follows acceptance.

Use `type/feature` and `status/new-issue` until repositories configure
dedicated project/requirement labels. Publishing never grants acceptance.
Governance changes the Issue to `status/accept` outside this Skill.

Use an authenticated repository integration or CLI first. For GitCode, read
`references/gitcode-host-contract.md` and perform its capability probe. Verify
the created Issue by reading back its stable URL before reporting success.

When online publication is unavailable after the configured adapters were
attempted, explain that an online URL is preferred because it improves team
visibility, decision attribution, and resistance to stale or mistaken local
state. Offer these choices:

- retry or manually publish the complete paste-ready Issue Markdown;
- explicitly continue with a repository-local Requirement Record;
- pause.

Do not silently select the local fallback. When the human chooses it, create a
stable `REQ-NNN` record under the configured
`issue_publishing.local_requirement_fallback.root` (default
`docs/requirements/`) from
`references/requirement-record-template.md`. Record `source.type:
local-record`, the failed publication reason, mode, architecture references,
the named human and UTC time that selected the fallback, and
`acceptance.status: proposed`. The human may later record `accepted` or
`working` with `decided_by` and `decided_at`. When publication becomes
available, create and verify the online Issue, link it to the local history,
and use the URL as the superseding authority. Never treat file creation as Requirement
acceptance. Run `scripts/check_feature_record.py --requirement-record
<repository-relative-path>` after creation.

When the current user explicitly accepts the local Requirement in conversation,
do not ask them to edit YAML and do not wait for an Issue label that cannot
exist. Confirm that the decision applies to the current Requirement Gate, obtain
the human decision name only when it is not already known, and run:

```text
scripts/check_feature_record.py \
  --requirement-record <repository-relative-path> \
  --record-verbal-acceptance-by <named-human> \
  --require-accepted
```

This records `accepted`, the named human, UTC time, and
`decision_source: conversation` before validation. Ordinary acknowledgements
such as “好的” or “继续看看” are not acceptance. Explicit phrases such as
“批准”, “接受”, or “accept REQ-001” are acceptance for the currently presented
Gate. The Skill records the human decision; it never creates one.

## Output

```text
Team Requirement Result:
- mode: new-project / existing-project
- Requirement authority: verified online Issue URL / local Requirement Record
- status: published-new-issue / local-fallback / output-only / revise / paused / blocked
- requirement scope:
- top-level design (L0): accepted / optional-existing / not-present / not-applicable
- top-level design (L0) reviewer:
- optional module design (L1) reference:
- target repository:
- next requirement gate: human status/accept online, or accepted/working with named decision in the local fallback
- next Skill after acceptance: speckit.team.feature-split
```

Stop on unresolved privacy boundaries, missing new-project top-level design
(L0) acceptance,
unreadable supplied Requirement Issues, or user pause.
