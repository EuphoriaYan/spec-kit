---
description: "Turn an unanchored plain-language request into read-only impact evidence, a reviewed issue, and a resumable formal workflow handoff."
---

# AI Team Intake

Handle a request that does not yet have a coding issue or confidential
requirement handoff. Intake is not formal SDD and must not edit product source.

## User Input

```text
$ARGUMENTS
```

## Local Artifacts

Use `.specify/ai-team/intake/<intake_slug>/`:

```text
intake.yml              # resolved classification, privacy, recommendation, approvals
request.md              # concise user wording; never copy confidential text publicly
impact-summary.md       # links to Code Graph or source-structure evidence
issue-draft.md          # proposed issue body and labels
result.yml              # created URL and formal workflow resume information
```

These are provisional local workflow artifacts. Do not commit them merely to
start work. Durable formal context begins under
`.specify/ai-team/work/<work_slug>/` after a work item exists.

## Mode: Analyze

1. Preserve the user's original intent in `request.md` and assign a safe,
   lower-kebab `intake_slug`.
2. Classify provisionally as `bug`, `feature`, or `unclear`. Ask one focused
   question only when bug versus feature changes the repository or approval
   route.
3. Classify publication as `public-safe`, `confidential`, or `unknown`. Never
   publish `unknown` or confidential text to a public coding repository.
4. Create only an analysis Permission Envelope. Read source, tests, module
   ownership, history, and Code Graph; do not edit product source or create a
   formal Spec Kit feature directory.
5. Record likely modules, reuse candidates, contracts at risk, expected change
   radius, and evidence gaps.
6. Write `intake.yml` with this machine-readable contract before asking for the
   boundary review:

```yaml
work_type: bug | feature
privacy_class: public-safe | confidential
planning_mode: standard | compact
feature_decision: not-applicable | draft | accepted
feature_approver:
feature_approver_role:
```

`work_type=auto` is allowed only as input to this analysis. It must be resolved
to `bug` or `feature` in `intake.yml`; otherwise the review must be revised or
rejected and no formal workflow may start.

## Mode: Draft

Create `issue-draft.md` from the request and impact evidence. It must contain:

```yaml
---
title: <public-safe issue title>
type_label: type/bug | type/feature
target_repository: owner/repository
---
```

- observable problem or desired behavior;
- affected users and acceptance examples;
- work type and target repository;
- likely modules and current architecture impact;
- public API/SPI/config/schema/dependency flags;
- validation expected and known unknowns;
- proposed labels: exactly one `type/*` and `state/draft`;
- recommended planning mode with reasons and mandatory fallback conditions.

Recommend Compact only for an existing project when evidence shows a local or
single-module change, a clear reuse path, no public-contract or migration
change, no security/privacy or critical-dependency decision, and simple
rollback. Words such as "small" or "quick" are not evidence. AI recommends;
the human gate selects.

## Publication And Routing

Publication is not an AI prose action. After the draft review reaches
`approve`, `ai-team-intake` invokes the installed deterministic script:

```text
python .specify/extensions/ai-team/scripts/intake_router.py publish \
  --run-id <run-id> --intake-slug <slug>
python .specify/extensions/ai-team/scripts/intake_router.py route \
  --run-id <run-id> --intake-slug <slug>
```

The script verifies both gate decisions, validates the draft against
`intake.yml`, publishes through the configured GitHub CLI adapter, records the
returned URL in `result.yml`, and launches the formal workflow with structured
arguments. Before side effects:

1. Record the approving human and whether they are authorized to accept a
   feature for the Technical Committee or delegated authority.
2. Use the configured repository adapter. The bundled implementation is
   `github-cli`; other platforms must replace the adapter contract rather than
   falling back to an invented URL.
3. Apply `type/bug` or `type/feature` and one state label. A newly reported bug
   may proceed after issue creation. A feature remains `state/draft` unless the
   authorized feature decision is recorded; only then may it move to
   `state/accepted`.
4. Write the returned issue URL, labels, approver, selected planning mode, and
   next action to `result.yml`.
5. Let `intake_router.py route` launch the next workflow; do not ask the user to
   type the CLI command:

```text
bug -> ai-team-bugfix with coding_issue_url and generated bug work_slug
accepted feature -> ai-team-sdd with coding_issue_url and human-selected planning_mode
draft feature -> stop with a resumable chat instruction for feature review
confidential feature -> route to enhancement-internal; do not create a public coding issue
```

For an accepted Compact feature, invoke `ai-team-sdd` with
`planning_mode=compact`. That formal workflow repeats the post-impact Compact
eligibility gate before Plan and Tasks. If the formal impact result is broader,
restart in Standard mode.

## Stop Conditions

Stop without publishing or editing source when:

- repository visibility is unknown and the request may be confidential;
- the issue target or authenticated publication adapter is unavailable;
- issue body and analyzed request disagree;
- no human approved the issue draft;
- a feature lacks Technical Committee or delegated acceptance;
- Compact was selected without qualifying impact evidence;
- issue creation did not return a verifiable URL.
