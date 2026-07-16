# Internal Skill Resources

This directory contains progressively loaded runtime resources owned by the
six Team Skills. Every Markdown file here must be installed by `extension.yml`
and explicitly read by its owning Skill.

## Active Skill Resources

These files are installed by `extension.yml` into a specific Skill. The Skill
must explicitly read the installed target when that phase needs it.

| Source | Installed for | Purpose |
|---|---|---|
| `context.md` | Plan-and-Task, Assess, Fix, Implement, Review | Resume Feature or Bugfix work without relying on chat history |
| `feature-spec.md` | Plan-and-Task | Reconstruct the accepted Feature stories into `spec.md` |
| `handoff-spec-sync.md` | Plan-and-Task | Consume an authorized confidential handoff without committing private text |
| `implement-pr.md` | Implement | Load PR submission rules only after implementation verification |

## Change Rule

Update a resource, its owning Skill, and its installation declaration in the
same change. Rules that belong to a primary role flow must live in that Skill
or one of its installed resources. Project-wide explanation belongs in
`docs/`; executable non-Skill behavior belongs in scripts or setup code. Do not
keep uninstalled command drafts or reserved capability sources here.
