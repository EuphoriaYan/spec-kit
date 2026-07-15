---
description: "Create or refine an internal enhancement record and sanitized handoff requirement for confidential enterprise feature work."
---

# AI Team Requirement Handoff

Use this before feature or new-project implementation when the user has
confidential enterprise demand, a private draft, a project charter, or internal
approval discussion that should not start in the public coding repository.

Public feature requests do not need this command by default. They can start as
coding repository issues or SDD feature requests.

## User Input

```text
$ARGUMENTS
```

## Goal

Move confidential feature intent through the internal-only enhancement
repository without leaking raw customer demand into the coding repository.
This capability authors the private requirement and sanitized handoff; it does
not accept the Feature. Acceptance is a repository decision made by the
Technical Committee or delegated authority outside any skill.

## Repository Model

```text
enhancement-internal    internal-only feature traceability, approval, wave plan, handoff URLs
coding repository       source, public issues, public-safe plans, evidence, PRs
```

Feature implementation references either:

- a public coding issue URL for public work; or
- a sanitized handoff requirement URL for confidential enterprise work.

## Required Reading

- `.specify/extensions/team/ai-team-config.yml`;
- `.specify/<category>/<work_id>/work-context.yml` and `context-pack.md` when
  the feature was already routed from a coding workspace;
- [docs/issue-lifecycle.md](../../docs/issue-lifecycle.md) or installed equivalent;
- private enhancement issue or draft only when the current operator has access;
- handoff RFC conventions under the internal enhancement repository;
- coding repository module index only enough to name likely affected modules.

## Procedure

1. Confirm the request is a new feature, new project, or public behavior, not a
   bug.
2. If the feature is public, prefer a coding repository issue and return to
   `speckit.team.specify`.
3. Work in `enhancement-internal` when raw demand, commercial context, or
   unapproved acceptance discussion is needed. The issue must use `type/feature`
   and exactly one status label from `status/new-issue`, `status/accept`,
   `status/working`, or `status/close`.
4. Reject or reroute any enhancement-internal issue labeled `type/bugfix` or
   describing a bug fix. Bug fixes belong in coding repository issues and start
   with `speckit.team.specify`.
5. Produce a sanitized handoff requirement with:
   - problem or goal;
   - user scenario and value;
   - scope and non-goals;
   - affected coding repository and likely modules;
   - target repository or project creation intent when the work is a new
     project;
   - approval route: maintainer, Technical Committee, release owner, or
     delegated owner;
   - wave plan;
   - acceptance expectations;
   - privacy note describing what was intentionally excluded;
   - whether the coding repository may link the handoff URL or must use a
     public-safe summary.
6. Update or create the Work Context Package with the handoff requirement URL,
   status, approval route, current wave, and next command.
7. Return the handoff URL. The next step is either repository review by the
   Technical Committee or delegated authority, or `speckit.team.specify` when
   the coding-side Issue and Spec still need to be produced.

## Output Shape

```text
Requirement handoff:
- task id:
- context path:
- private source used: no / yes
- handoff requirement URL:
- public-safe summary:
- coding repository may link handoff URL: yes / no / not applicable
- type label: type/feature
- status label: status/new-issue / status/accept / status/working / status/close
- approval route:
- current wave:
- affected coding repository:
- new project target:
- likely modules:
- privacy exclusions:
- next command:
```

## Stop Conditions

Stop before coding when:

- confidential enterprise work has no accepted handoff requirement or
  public-safe summary;
- an enhancement-internal issue is labeled or behaving as a bug fix;
- raw customer demand would be copied into the coding repository;
- the handoff requirement has no status or approval route;
- public SPI/API, dependency, license, security, compatibility, or migration
  impact is unresolved.
