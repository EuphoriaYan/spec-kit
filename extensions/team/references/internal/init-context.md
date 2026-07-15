---
description: "Initialize or refresh progressive AI Team context pointers for the active coding tools."
---

# AI Team Init Context

Run this command automatically before every AI Team role command. Users should
not need to invoke it manually.

1. From the repository root, run:

   ```text
   python .specify/extensions/team/scripts/init_role_context.py
   ```

2. Read and execute
   `.specify/extensions/team/docs/context-bootstrap.md` through the level
   required by the active role.
3. If the script reports that the AI Team bundle is absent, stop and repair the
   installation. Do not continue with an ungoverned role prompt.

The script merges a short managed pointer into `AGENTS.md` and the rule file of
each detected supported integration. It preserves all content outside the
managed markers and is safe to run repeatedly.
