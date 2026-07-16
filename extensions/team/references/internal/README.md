# Internal Reference Lifecycle

This directory contains source material owned by the Team extension. A file is
not obsolete merely because it is not currently installed into a role Skill.
Every file must be classified below before it is added, moved, or deleted.

## Active Skill Resources

These files are installed by `extension.yml` into a specific Skill. The Skill
must explicitly read the installed target when that phase needs it.

| Source | Installed for | Purpose |
|---|---|---|
| `context.md` | Plan-and-Task | Resume an existing work context without relying on chat history |
| `feature-spec.md` | Plan-and-Task | Reconstruct the accepted Feature stories into `spec.md` |
| `handoff-spec-sync.md` | Plan-and-Task | Consume an authorized confidential handoff without committing private text |
| `implement-pr.md` | Implement | Load PR submission rules only after implementation verification |

## Reserved Capability Sources

These files preserve reviewed behavior that has not yet been fully migrated to
an installed role Skill. They are intentionally not installed at runtime. Do
not delete one only because `extension.yml` does not reference it. First either
migrate its still-valid rules into the named destination and add tests, or
record an explicit human decision that the capability is no longer required.

| Source | Intended destination | Missing migration |
|---|---|---|
| `pr.md` | Implement and Fix | Generic repository routing, privacy, evidence, and multi-Issue submission checks |
| `review.md` | Review | Cross-work-type routing, Bugfix evidence, compatibility triggers, and grouped-Issue checks |
| `requirement.md` | Specify or a confidential-demand Skill | Sanitized handoff authoring, wave plan, privacy exclusions, and approval routing |
| `workspace.md` | Team installer or setup capability | Interactive repository roles, handoff URL policy, and workspace contract summary |
| `support.md` | Support audit capability | Executable Skill, Knowledge, and Memory inventory procedure |
| `memory-consolidate.md` | Memory maintenance capability | Callable promotion workflow around the existing memory adapter |
| `release-archive.md` | Release maintenance capability | Callable release archive procedure and evidence output |
| `retrospect.md` | Failure evolution capability | Callable failure classification and durable-control feedback loop |

## Migrated Sources

`init-context.md` was removed after its complete behavior moved to
`scripts/init_role_context.py`, `docs/context-bootstrap.md`, and the Team setup
path in Specify CLI. Those sources now own installation, managed agent-rule
pointers, repeatable refresh, and progressive role context.

## Change Rule

For an active resource, update its owning Skill and installation declaration in
the same change. For a reserved source, preserve it until migration or explicit
deprecation is reviewed. A migration is complete only when the destination is
callable after installation and tests cover the transferred stop conditions.
