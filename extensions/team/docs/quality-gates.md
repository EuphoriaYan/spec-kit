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
SHA-256 so the implementing AI and reviewers can identify the exact rules used.
The runner is a local coding tool. CI/CD may repeat it, but the Team workflow
must not postpone the first quality check until CI.

Rules use one of four engines:

- `command`: execute an argv list without a shell, such as build or test;
- `static`: deterministic `forbidden-regex`, `required-regex`, or
  `forbidden-path` checks over selected changed files;
- `external`: evaluate a normalized report from an external scanner such as
  CVGS. The rule selects the tool, severities, statuses, best-effort baseline
  states, and either all files or only changed files;
- `model-as-judge`: the reviewer evaluates the stated instruction against the
  diff and selected project context, then records structured evidence.

Every rule declares `required` or `advisory` enforcement. A failed required
rule produces `NO-GO`. A failed advisory rule produces `GO-WITH-RISK` when no
required rule fails. A missing Model-as-Judge result is `not-assessed` and
fails closed.

## Human exception boundary

Only a failed `model-as-judge` rule may be reduced from `NO-GO` to
`GO-WITH-RISK`, and only with a named human decision, timestamp, and concrete
reason in `speckit-quality-overrides/v1`. Command, static, and external results cannot be
overridden through this mechanism, and an unassessed model rule cannot be
waived as though it had produced a false positive. The reviewer reports the
conclusion and evidence; a human performs any merge.

## External finding evidence

External reports are evidence, not edit instructions. Do not mechanically
rewrite code from a scanner message before checking the rule's applicability
to the file and construct. A production-only `assert` rule reported under
`tests/`, a file-path rule reported on URL construction, or a prohibition on
raising `SystemExit` reported on an exception handler are examples that need
triage rather than automatic rewriting.

Normalize XLSX, CSV, or JSON reports before running the gate:

```text
python scripts/import_quality_findings.py \
  --input <scanner-export.xlsx> \
  --tool cvgs \
  --source-revision <reviewed-commit> \
  --output <work-root>/evidence/external-quality-findings.yml
```

For a repeat scan, pass the last accepted normalized report with `--baseline`.
The importer performs a best-effort comparison using the scanner tool, rule,
repository path, and normalized message while deliberately ignoring line
movement. It records `matched` or `new`; without a baseline it records
`unknown`. These values are comparison hints, not stable identities and not
waivers. Duplicate findings are compared by occurrence count. Keep the source
report name, SHA-256, generation time, tool version when known, and scanned
source revision in the normalized artifact. When `require_source_revision` is
enabled, the gate verifies that this revision is the current full `HEAD`; a
stale or unverifiable report fails closed.

The importer omits source snippets by default because scanner exports may
contain credentials, private prompts, host paths, or customer data. Use
`--include-snippets` only for an approved local evidence need, keep the result
under the Git-ignored work root, and do not paste raw snippets into an Issue or
PR when rule, path, line, report hash, and optional scanner-native ID are
sufficient.

Scanner status and review disposition are separate facts. An `ignored` finding
is not treated as reviewed unless the report records a reviewer, review time,
reason, and outcome. An ignored finding without that audit trail fails an
external rule whose `require_reviewed_ignored` setting is enabled (the
default). False-positive decisions belong in the scanner or its exported audit
fields; do not use the quality override file to bypass external, command, or
static results.

## Local prevention during AI coding

Quality prevention starts before source edits and does not require CI/CD:

1. Inspect the repository's own lint, format, type, test, security, and build
   configuration plus the applicable rules manifest.
2. Select only rules relevant to the planned paths and constructs. Record a
   compact `Quality Prevention Notes` section; do not turn one scanner example
   into a universal coding rule.
3. Run enabled `command` and `static` rules locally as a preflight to expose the
   starting baseline.
4. After each coherent edit batch or completed Task, run the narrowest relevant
   local formatter, lint, type, test, and deterministic gate checks. Fix newly
   introduced failures before continuing.
5. Run the broader planned verification once implementation is complete.

An older external report can inform the notes by showing recurring rule and
path patterns, but it is historical advisory context unless the repository can
run that scanner locally and explicitly configures it as required. Absence of a
fresh external report must not by itself prevent ordinary AI coding under the
default/advisory setup. CI/CD, when present, is secondary confirmation.

Typical review use:

```text
python scripts/run_quality_gates.py --project-root <repo> \
  --phase reviewing --role reviewer --base <target-branch> \
  --external-findings <work-root>/evidence/external-quality-findings.yml \
  --judge-results <work-root>/evidence/model-judge-results.yml \
  --overrides <work-root>/evidence/quality-overrides.yml \
  --output <work-root>/evidence/quality-gate.json
```

For local implementation preflight and edit-batch checks, omit judge inputs and
select deterministic engines:

```text
python scripts/run_quality_gates.py --project-root <repo> \
  --phase implementing --role developer --engine command --engine static \
  --output <work-root>/evidence/quality-gate-local.json
```

Pass `--engine external --external-findings ...` separately only when a current
or historical report is available and useful. Do not make this optional input
the primary prevention mechanism.

If an external rule is enabled but its matching normalized report is absent,
the result is `not-assessed`. Required mode fails closed; advisory mode records
`GO-WITH-RISK`. Retain the normalized artifact beside the gate JSON so Review
can cite report provenance and distinguish source defects from scanner false
positives.
