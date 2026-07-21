# Executable Tutorial And Evidence Step Contract

Use this contract when a Feature delivers a tutorial, runbook, deployment
procedure, acceptance walkthrough, or another multi-step operator workflow.
Ordinary code-only Features do not need an evidence-step manifest.

Every step must be either:

- `deterministic`: fixed prerequisites, action, and exact assertion;
- `evaluable`: a named fixture/invariant/metric and an objective evaluation
  policy.

Every execution uses exactly one result:

- `PASS`: the stated assertion passed and evidence is named;
- `FAIL`: the action ran and the assertion failed;
- `BLOCKED`: a required capability or contract is unavailable;
- `NOT_RUN`: an optional or external execution condition was not supplied.

`BLOCKED` and `NOT_RUN` require a concrete `missing_condition`. Every step
requires a recovery action. A subjective statement such as “looks correct” is
not evidence.

Use `evidence-steps.yml` with schema `ai-team-evidence-steps/v1`. Run the
installed checker:

```text
python scripts/check_evidence_steps.py path/to/evidence-steps.yml
```

The checker validates structure and classification. It does not execute shell
commands or turn self-asserted provider claims into conformance evidence.
