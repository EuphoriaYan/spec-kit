# Planning Code Graph Contract

Load this contract only when Plan-and-Task generates, attaches, or validates
Code Graph evidence. Source code is implementation truth; graph output is a
projection tied to one exact source revision.

## Artifact Shape

Store the smallest useful slice under the active work root:

```text
codegraph/
|-- nodes.jsonl
|-- edges.jsonl
|-- summary.md
`-- adapter-report.md
```

Use stable node IDs. Include applicable node kinds such as `repository`,
`module`, `package`, `file`, `class`, `interface`, `function`, `method`,
`config`, and `test`. Include inferable relationships such as `contains`,
`imports`, `calls`, `implements`, `extends`, `reads_config`, `tests`, and
`depends_on`.

## Required Evidence

Record in `summary.md`:

- work type, work ID, and source revision;
- likely owner module and adjacent modules;
- affected public contracts, callers, callees, configuration, and data paths;
- tests connected to affected nodes;
- existing abstractions or reuse candidates;
- likely change paths and change radius;
- missing evidence and confidence.

Record in `adapter-report.md`:

- adapter name and version, or `source-structure-fallback`;
- command or read-only method used;
- source revision;
- attempted and skipped evidence;
- license or network review when an external adapter is used;
- fallback reason and limitations.

The evidence file named by `plan-and-task.md` must exist and name the same
source revision as the Plan.

## Minimal Slice Rule

Inspect only the source and graph radius needed to establish module ownership,
contracts, dependencies, related tests, reuse opportunities, and likely impact.
Expand to adjacent modules only when imports, calls, shared state, public
contracts, configuration, schemas, or test evidence cross the initial boundary.

## Fallback Rule

When no configured adapter is available, build a source-structure fallback from
repository layout, build metadata, imports, symbols, tests, and targeted search.
Record the fallback and its confidence; do not claim semantic edges that source
evidence cannot establish.

A fallback alone is insufficient for public API or SPI changes, class or public
module addition/removal, dependency-direction changes, cross-module semantics,
security-sensitive data flow, or schema/wire-format changes unless an authorized
human accepts the missing evidence.

Read `references/code-graph-adapters.md` only when an adapter must be selected
or its license, installation, or network behavior must be evaluated.
