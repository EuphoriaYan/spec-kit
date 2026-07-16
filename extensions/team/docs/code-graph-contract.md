# CodeGraph And Impact Contract

Load this contract only when Plan-and-Task or Bug Assess needs architecture
impact evidence. Source code is implementation truth; CodeGraph is the required
projection tied to one exact source revision, not a replaceable adapter.

## Preconditions

1. Run `codegraph version`. Stop if the command is unavailable.
2. For an existing project, require `.codegraph/codegraph.db`. Run
   `codegraph init` when the repository has not been indexed yet.
3. Run `codegraph status`. Stop if the index is incomplete, stale, truncated,
   or does not describe the current working tree.
4. For a zero-to-one project with no source, record a zero-source baseline and
   re-index immediately after the first runnable source skeleton exists.

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

An available `codegraph_explore` MCP tool may be used. The CLI is the portable
path for every supported AI Coding tool.

## Evidence

Write the reviewable result under the active work root:

```text
.specify/<category>/<work_id>/codegraph/summary.md
```

Record:

- CodeGraph version, status, source revision, and working-tree state;
- exact queries or MCP calls used;
- affected symbols, files, modules, callers, callees, and tests;
- public contracts, data paths, and dependency directions;
- existing abstractions and reuse candidates;
- expected change radius and minimum verification surface;
- API, SPI, configuration, schema, event, database, and middleware effects;
- compatibility, migration, rollback, and required human review;
- uncertainty, missing relationships, and graph/source disagreements.

Do not create a separate generic impact artifact. The Plan or Bugfix assessment
may summarize these conclusions, but must link to this evidence. Do not commit
`.codegraph/` index data; it is local derived state.

## Minimal Slice Rule

Inspect only the graph radius needed to establish responsibilities, contracts,
dependencies, tests, reuse opportunities, and likely impact. Expand only when
calls, shared state, public contracts, configuration, schemas, or test evidence
cross the initial boundary.

## Stop Conditions

Stop instead of substituting grep or an invented source-structure fallback
when:

- CodeGraph or its existing-project index is unavailable;
- the index is incomplete, stale, or tied to another working tree;
- the query cannot distinguish similarly named symbols or modules;
- graph evidence contradicts current source;
- the required read scope exceeds the approved Permission Envelope.

When graph and source disagree, report the conflict and refresh the index.
