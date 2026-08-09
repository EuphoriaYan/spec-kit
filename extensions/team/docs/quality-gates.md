# Configurable Quality Gates

Team projects may opt into a versioned rules manifest with schema
`speckit-quality-rules/v1`. The extension does not impose a universal coding
standard. Each repository owns its rules and enables them with
`quality_gates.mode` in `.specify/team/ai-team-config.yml`:

- `disabled`: compatibility default; do not evaluate a pack;
- `advisory`: evaluate and retain evidence without blocking the command;
- `required`: return a non-zero status for `NO-GO`.

Once a repository selects `required`, a missing or invalid rules manifest is
itself `NO-GO`. Every result records the pack ID, semantic version, and manifest
SHA-256 so CI and reviewers can identify the exact rules used.

Rules use one of three engines:

- `command`: execute an argv list without a shell, such as build or test;
- `static`: deterministic `forbidden-regex`, `required-regex`, or
  `forbidden-path` checks over selected changed files;
- `model-as-judge`: the reviewer evaluates the stated instruction against the
  diff and selected project context, then records structured evidence.

Every rule declares `required` or `advisory` enforcement. A failed required
rule produces `NO-GO`. A failed advisory rule produces `GO-WITH-RISK` when no
required rule fails. A missing Model-as-Judge result is `not-assessed` and
fails closed.

## Human exception boundary

Only a failed `model-as-judge` rule may be reduced from `NO-GO` to
`GO-WITH-RISK`, and only with a named human decision, timestamp, and concrete
reason in `speckit-quality-overrides/v1`. Command and static results cannot be
overridden through this mechanism, and an unassessed model rule cannot be
waived as though it had produced a false positive. The reviewer reports the
conclusion and evidence; a human performs any merge.

Typical review use:

```text
python scripts/run_quality_gates.py --project-root <repo> \
  --phase reviewing --role reviewer --base <target-branch> \
  --judge-results <work-root>/evidence/model-judge-results.yml \
  --overrides <work-root>/evidence/quality-overrides.yml \
  --output <work-root>/evidence/quality-gate.json
```

For implementation, omit judge inputs and select only deterministic engines:

```text
python scripts/run_quality_gates.py --project-root <repo> \
  --phase implementing --role developer --engine command --engine static
```
