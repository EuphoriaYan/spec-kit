# CodeGraph And Impact Contract

Load this contract only when Plan-and-Task or Assess needs architecture impact
evidence. Source code is implementation truth; CodeGraph is the required local
projection tied to one exact source revision.

## Preconditions

1. Run `codegraph version` and require a supported 1.x release.
2. For an existing project, when `.codegraph/codegraph.db` does not exist, stop
   and ask the user whether to initialize the local derived index. Run
   `codegraph init` only after explicit confirmation, or give the command to the
   user to run themselves.
3. Run `codegraph status`. If it reports pending files, run `codegraph sync` and
   check status again before analysis.
4. Stop when the index is incomplete, tied to a different checkout, or still
   stale after synchronization.
5. For a zero-to-one project with no source, record a zero-source baseline and
   run `codegraph init` immediately after the first runnable source skeleton
   exists.

The CLI is the portable path for every supported AI coding tool. An available
`codegraph_explore` MCP tool may be used for queries, but MCP configuration is
not required when the CLI is available.

## Queries

Start with the smallest query that establishes the affected structure:

```text
codegraph explore "<feature, flow, module, or failure question>"
codegraph node <symbol-or-file>
codegraph callers <symbol>
codegraph callees <symbol>
codegraph impact <symbol>
codegraph affected <changed-files>
```

## Evidence

Write one reviewable summary under the active work root:

```text
Feature: .specify/feature/<work_id>/codegraph/summary.md
Bugfix:  .specify/bugfix/<bug_slug>/codegraph/summary.md
```

Record:

- CodeGraph version and status;
- source revision and working-tree state;
- exact CLI queries or MCP calls used;
- affected symbols, files, modules, callers, callees, and tests;
- public contracts, data paths, and dependency directions;
- existing abstractions and reuse candidates;
- expected change radius and minimum verification surface;
- API, SPI, configuration, schema, event, database, and middleware effects;
- compatibility, migration, rollback, and required human review;
- uncertainty, missing relationships, and graph/source disagreements.

Do not create a second generic impact artifact. The Plan or Bugfix assessment
summarizes these conclusions and links to this evidence. Do not commit the
`.codegraph/` index.

## Minimal Slice Rule

Inspect only the graph radius needed to establish responsibilities, contracts,
dependencies, tests, reuse opportunities, and likely impact. Expand only when
calls, shared state, public contracts, configuration, schemas, or test evidence
cross the initial boundary.

## Stop Conditions

Stop instead of substituting grep or inventing a source-structure fallback when:

- CodeGraph or its existing-project index is unavailable;
- the index remains incomplete or stale after synchronization;
- the query cannot distinguish similarly named symbols or modules;
- graph evidence contradicts current source;
- the required read scope exceeds the approved Permission Envelope.

When graph and source disagree, report the conflict and refresh the index. Do
not use CodeGraph output to override source code.
