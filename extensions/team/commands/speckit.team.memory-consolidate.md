---
description: "Capture a reviewed lesson or decision, and promote durable coding guidance into task-scoped project Knowledge."
---

# Team Memory Consolidation

Consolidate completed work or an explicit human decision without turning raw
notes into project policy. This is a support Skill, not a release gate, and may
run after a Feature, Bugfix, incident, review cycle, or architecture decision.

## User Input

```text
$ARGUMENTS
```

Accept a source work item or evidence URL, the lesson or decision to preserve,
its intended scope, and an optional requested tier. Also accept a direct request
such as "remember this lesson for the payment module" or "make this reviewed
coding standard apply to Feature implementation and review".

## Consolidate

1. Read `references/memory-tiers.md`. Inspect the cited source, tests, Issue,
   Plan, PR, or decision record. Do not consolidate remembered chat alone.
2. Remove credentials, customer-sensitive text, commercial context, raw
   transcripts, and unrelated implementation detail.
3. Classify the card as `memory_type: decision` or `memory_type: attempt` and
   choose local, department, or enterprise tier. Default uncertain and
   unreviewed material to local or department Memory with
   `authority: advisory`.
4. Create one Markdown card in the managed staging directory defined by
   `references/memory-tiers.md`, with YAML frontmatter containing at least:

   ```yaml
   tier: department
   memory_type: attempt
   privacy: internal
   owner: team-name
   authority: advisory
   status: active
   scope:
     roles: [plan-and-task, implement, review]
     work_types: [feature]
     modules: [src/payment]
   evidence: [https://host/org/repo/pull/123]
   ```

   Scope is mandatory for automatic retrieval. Use `*` explicitly for a
   genuinely project-wide role, work type, or module rule; an omitted scope is
   stored but never injected automatically.

5. Persist it with the installed adapter:

   ```text
   python scripts/memory_adapter.py persist --project-root <repo> \
     --source <staging-card> --tier <tier> [--backend file|mem0]
   ```

   The file backend is the default. Use mem0 only with an approved namespace
   and privacy boundary. Local and department paths remain Git-ignored.

## Promote A Requirement

A coding convention recorded as Memory remains advisory. Promote it only when
the user explicitly asks to make it project guidance and provides the human
owner's approval, approval time, evidence, and scope.

1. Persist the reviewed card as enterprise Memory with
   `authority: approved-guidance`, `status: active`, `approved_by`,
   `approved_at`, `evidence`, and a non-empty `scope`.
2. Ask one human decision only if that approval is absent or ambiguous. Do not
   let the model approve its own rule.
3. Choose the narrowest knowledge type: `architecture-rule`,
   `coding-standard`, `compatibility-rule`, `operations-rule`,
   `security-rule`, or `test-rule`.
4. Run:

   ```text
   python scripts/memory_adapter.py promote --project-root <repo> \
     --source <enterprise-card> --knowledge-type <type>
   ```

The generated rule under `docs/ai-team/knowledge/rules/` is binding project
Knowledge and enters Git review. Requirements that can be checked
deterministically should also become a test, gate, or Code Graph rule; this
Skill recommends that follow-up but does not invent or install it silently.

## Output

Report the card path, tier, authority, owner, scope, evidence, privacy review,
and whether a Knowledge promotion or executable follow-up was requested.
Clearly distinguish `advisory Memory` from `binding Knowledge`.
