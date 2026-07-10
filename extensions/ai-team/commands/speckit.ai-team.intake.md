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
intake.yml              # classification, privacy, recommendation, approvals
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

## Mode: Draft

Create `issue-draft.md` from the request and impact evidence. It must contain:

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

## Mode: Publish

The preceding workflow gate is approval of the exact draft, publication
target, and planning recommendation. Before side effects:

1. Record the approving human and whether they are authorized to accept a
   feature for the Technical Committee or delegated authority.
2. Use the configured repository adapter. Prefer an installed platform skill,
   MCP integration, or authenticated CLI/API. For GitHub, `gh issue create` is
   an acceptable adapter. Do not invent a URL when publication fails.
3. Apply `type/bug` or `type/feature` and one state label. A newly reported bug
   may proceed after issue creation. A feature remains `state/draft` unless the
   authorized feature decision is recorded; only then may it move to
   `state/accepted`.
4. Write the returned issue URL, labels, approver, selected planning mode, and
   next action to `result.yml`.
5. Launch the next workflow on the user's behalf; do not ask the user to type
   the CLI command:

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
