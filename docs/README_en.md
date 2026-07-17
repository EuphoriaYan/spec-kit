# Documentation Management

[中文主文档](README.md)

This directory contains three different surfaces: human-facing AI Team docs,
advanced upstream Spec Kit references, and course materials.

Human-facing AI Team docs use Chinese primary files and `_en` English backups:

- repository and documentation home;
- installation;
- six-skill quick start and user journeys;
- upgrade;
- local development;
- Team extension maintainer guide.

Installation details have one authoritative guide. Skill inputs, outputs, and
journeys have one authoritative quick start. Other pages summarize and link.
Update each English backup in the same PR as its Chinese primary.

AI runtime contracts remain English with stable paths and no `_en` duplicate:

- `extensions/team/commands/`;
- `extensions/team/references/`;
- resources installed by `extensions/team/extension.yml`;
- context bootstrap, templates, checks, and managed agent rules.

Upstream `concepts/`, `reference/`, `guides/`, `community/`, and `install/`
content remains advanced reference rather than the AI Team onboarding path.

