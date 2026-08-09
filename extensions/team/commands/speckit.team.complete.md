---
description: "Close one reviewed Feature by backfilling already-existing merge and release facts."
---

# Spec Kit Team Complete

Close one repository-tracked Feature after humans and delivery systems have
already merged and released it. This Skill performs final validation and
Feature Record backfill only. It does not approve or merge a PR, create a
release, move a tag, deploy software, change the Feature Catalog, or close the
parent Requirement.

## Input

```text
$ARGUMENTS
```

Require:

- `feature_id=<FEAT-NNN>`;
- the actual merged Git commit;
- the delivered release name;
- stable release evidence: an HTTP(S) release URL or `git-tag:<tag>`;
- the named human responsible for closing the Feature.

## Flow

1. Resolve the configured Feature Record with `feature_records.py`. Require
   accepted detailed behavior, complete Definition of Done, a verified review
   target, and `delivery.phase: ready-to-merge`.
2. Read the PR or local review evidence and confirm that the supplied merge
   commit is the actual integrated revision. Read the release page or tag and
   confirm that it contains that commit. Stop when either fact is proposed,
   pending, unverifiable, or inconsistent.
3. Show the user the exact Feature Record path and the values that will be
   backfilled: merged commit, delivered release, release evidence, closing
   human, and completion time. Ask for confirmation when any supplied value
   came from conversation rather than an authenticated read. Never infer a
   successful merge or release from a `GO` review.
4. Run:

   ```text
   scripts/complete_feature.py --feature-id <id> \
     --merged-commit <sha> --delivered-in <release> \
     --release-evidence <url-or-git-tag:tag> \
     --completed-by "<human name>"
   ```

   The helper verifies that the commit exists in the repository, that tag
   evidence contains it when a tag is used, and that the legal transition is
   `ready-to-merge -> done`. It restores the original Feature Record if final
   validation fails.
5. Re-read the Feature Record and report the persisted facts. When the parent
   Requirement authority is online, optionally prepare a public-safe completion
   handoff containing Feature ID, release, evidence, and remaining Features.
   Posting that handoff does not close the parent Requirement or declare its
   full scope complete.

## Output

```text
Team Complete Result:
- Feature ID and Record:
- previous phase: ready-to-merge
- merged commit:
- delivered release:
- release evidence:
- completed by and at:
- parent Requirement handoff: posted / paste-required / skipped
- mutations not performed: merge, release, deploy, Catalog, parent closure
- result: done / blocked
```

Stop if review is not complete, the Feature is not `ready-to-merge`, the merge
commit is not contained in the current repository, release evidence is absent
or inconsistent, or the closing human is unnamed.
