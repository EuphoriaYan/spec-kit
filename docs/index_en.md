# AI Team Spec Kit Documentation

[中文主文档](index.md)

AI Team Spec Kit installs one collaboration model into Codex, Claude Code,
Cursor, and Trae. Users start from chat; six role Skills hand work off through
Issues, plans, tasks, source, and verification evidence.

Start with:

1. [Installation](installation_en.md)
2. [Six-Skill Quick Start](quickstart_en.md)
3. [Upgrade](upgrade_en.md)
4. [Local Development](local-development_en.md)

```text
Feature: Specify -> Issue acceptance -> Plan-and-Task -> Implement
         -> Review/Assess/Fix -> PR -> human merge

Bugfix: Assess -> Fix -> Review/Assess/Fix -> optional PR -> human merge
```

Humans remain responsible for requirement acceptance, HLD and public
interfaces, dependency/security/license/incompatibility decisions, Plan scope
expansion, and final merge.
