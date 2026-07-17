# Task-Scoped Knowledge and Memory

Use the installed `scripts/memory_adapter.py` to load only guidance relevant to
the current role, work type, and affected modules.

```text
python scripts/memory_adapter.py retrieve \
  --project-root <repo-root> \
  --role <role> \
  --work-type <feature|bugfix> \
  --module <module-path>
```

Resolve the script relative to the installed Skill directory. Add one
`--module` for each affected module. Omit modules only before impact analysis
has identified them, then retrieve again with the resolved scope. Department
memory is excluded unless the repository has an approved internal namespace
and the user explicitly requests `--include-department`.

Apply the result in this order:

1. current source, tests, Issue, accepted Plan, and human decisions;
2. binding Knowledge under `docs/ai-team/knowledge/rules/`;
3. enterprise and explicitly requested department Memory as advisory context.

Never treat local or department Memory as a coding rule. Never infer that an
unscoped, unmatched, expired, proposed, or superseded card applies. Use `*`
only when a reviewed card explicitly declares project-wide scope. If binding Knowledge
conflicts with current source or an accepted decision, report the conflict and
stop for reconciliation rather than silently choosing one.
