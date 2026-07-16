---
description: "Initialize or refresh progressive AI Team context pointers for the active coding tools."
---

# AI Team Init Context

Specify CLI runs this initializer during project initialization. It is not a
runtime dependency of individual AI Team role skills.

1. During `specify init`, execute the packaged Team context initializer once.
2. Role skills read and execute
   `.specify/extensions/team/docs/context-bootstrap.md` through the level
   required by the active role.
3. If initialization reports that the Team extension is absent, stop and repair the
   installation. Do not continue with an ungoverned role prompt.

The script merges a short managed pointer into `AGENTS.md` and the rule file of
each detected supported integration. It preserves all content outside the
managed markers and is safe to run repeatedly.
