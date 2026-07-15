# <Module Name>

## Module Card

| Field | Value |
|---|---|
| Module ID | `<stable-module-id>` |
| Primary owner | `<team-or-person>` |
| Review route | `<CODEOWNERS-path, team, or reviewer group>` |
| Source roots | `<project-relative paths>` |
| Public contracts | `<API, SPI, events, schemas, config, or none>` |
| Direct dependencies | `<module IDs and version/contract expectations>` |
| Test entry points | `<commands or project-relative test paths>` |

## Responsibility

Describe what this module owns and what it deliberately does not own.

## Boundary Rules

State the allowed dependency direction, data ownership, extension points, and
operations that callers must use instead of editing module internals.

## Change Guidance

Record the local design patterns, reuse points, compatibility promises, and
verification commands an AI coding tool must preserve.

Update this file when module ownership, responsibility, public contracts,
dependency direction, or test entry points change. `CODEOWNERS` may automate
review routing, but it does not replace this architecture-facing module card.
