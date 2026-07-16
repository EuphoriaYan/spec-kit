---
description: "Fetch a handoff requirement URL into the active Team work directory"
scripts:
  sh: scripts/bash/sync-handoff-spec.sh --json
  ps: scripts/powershell/Sync-HandoffSpec.ps1 -Json
---

# Handoff Spec Sync

Run before Team planning when an authorized confidential requirement URL is in
scope. The caller must provide `work_type`, `work_id`, and the URL.

The script resolves `.specify/<feature|bugfix>/<work_id>/`, preserves public
`spec.md`, and writes the fetched effective content to gitignored
`spec.override.md`.

Read the JSON result as follows:

- `SKIPPED: true`: no handoff URL was available.
- `WORK_DIR`: canonical work item directory.
- `SPEC`: public specification path.
- `EFFECTIVE_SPEC`: `spec.override.md` when fetched, otherwise `spec.md`.
- `SPEC_BOOTSTRAPPED`: whether the script created a public URL pointer.

Accept only `https://` URLs. Stop when the category/ID is missing, the URL is
unauthorized, or fetching fails. Never invent private requirement content.
