# Requirement Responsibility And Pull Request Boundary

Classify accepted requirements before designing Tasks. The classification is
about who owns the capability, not which team first noticed it.

## Responsibility classes

- `business-software`: behavior owned by the product or scenario repository;
- `framework`: reusable runtime, SDK, platform, protocol, or cross-product
  behavior owned by a framework module or repository;
- `external-prerequisite`: a required provider, credential, policy, dataset, or
  capability that this work cannot implement.

Do not turn a framework or external prerequisite into a business-software Task
merely to make the current Feature appear complete. Record `BLOCKED` or a
linked delivery unit when the responsible owner has not supplied it.

## May business and framework changes use one PR?

Yes, but only when all of the following are true:

1. both changes are in the same repository;
2. they implement one atomic accepted outcome and neither change is useful as
   an independently released framework capability;
3. the framework change is minimal, backward compatible, and can share the
   business change's release and rollback boundary;
4. business and framework paths have separate Tasks and self-tests;
5. both review routes are named, and the framework or contract owner has
   explicitly accepted the combined boundary;
6. the PR description makes the two responsibility classes and their evidence
   independently reviewable.

Use `linked-prs` by default when repositories, owners, release cadence,
compatibility policy, rollout, or rollback differ. A GitHub pull request is one
branch comparison into one base repository; cross-repository delivery therefore
uses linked PRs rather than pretending that one PR covers both repositories.

For linked PRs, state dependency order and the exact contract/version/commit
that unblocks the dependent PR. Do not merge the dependent business PR while a
required framework contract is still provisional.

## Mechanical record

`plan-and-task.md` records:

- a `delivery_strategy` front-matter object;
- one `Requirement Responsibility Matrix` row for every accepted User Story;
- the target repository, delivery unit, dependency, and review route.

The deterministic Plan check rejects missing classifications, a combined PR
across repositories, or a combined business/framework PR without an atomic
scope, shared rollback, and named framework-owner decision evidence.
