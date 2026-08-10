# Architecture And Delivery Flow

Team SDD separates stable architecture decisions from the implementation
strategy used to deliver one Feature. The levels are different zoom levels,
not a document-count target.

## Top-Level Design (L0): System Context And Top-Level Modules

Top-level design (L0) states what the system is, its primary users and external inputs/outputs,
its boundary, and the first decomposition into top-level modules. It does not
define classes, packages, files, or implementation algorithms.

## Module Design (L1): Module Semantics And Submodules

Module design (L1) defines what each top-level module is responsible for, its inputs and
outputs, its owned data, its collaboration with other modules, and its next
decomposition into stable submodules. It does not prescribe task sequencing or
per-file edits.

## Feature Split And Specify

Feature Split selects independently valuable delivery units against the
top-level design (L0) and module design (L1).
Specify then makes one accepted Feature behavior precise. Its simplified User
Stories and Verification are written back to the Feature Record and confirmed
by a human before technical planning.

## Interface And Data Structure Design (L2)

Interface and data structure design (L2) describes the stable internal logical
components needed by the accepted Feature, their responsibilities, data flow,
interfaces, data formats, and dependency direction. It may add or update shared
contracts. It stops before class names,
file lists, code-level algorithms, and contributor assignments.

An existing interface and data structure design (L2) may be reused when it
already supports the Feature. When no interface and data structure design (L2)
change is needed, record the reviewed reason instead of creating an empty
document.

## Plan: Implementation And Delivery Strategy

Plan changes viewpoint. It explains how the accepted behavior and reviewed
interface and data structure design (L2) will be delivered in the current codebase: reuse choices, module change
sequence, compatibility, migration, test strategy, PR boundaries, risk, and
rollback. Plan must reference architecture rather than redraw it at a coarser
level.

## Tasks: Executable Work Packages

Tasks turn the Plan into independently assignable work packages with exact
paths, dependencies, completion criteria, and self-tests. A Task does not
invent a new module boundary or shared contract.

The normal order is:

```text
Requirement -> top-level design (L0) -> module design (L1) -> Feature Split
-> Specify and behavior confirmation -> interface and data structure design
(L2)/shared-contract review -> Plan review -> Tasks -> Implement -> Review
```

For an existing system, reuse valid top-level design (L0), module design (L1),
and interface and data structure design (L2) assets and create only reviewed
deltas. Missing architecture never justifies empty placeholder documents.

## Shared Contracts

A shared contract is a repository architecture asset used by two or more
Features or modules. Keep accepted contracts under a team-chosen architecture
path such as `docs/architecture/contracts/`; Feature Records reference them by
repository-relative path.

Individual Feature work may propose a candidate interface locally. It is not a
team contract until affected contributors compare candidates, agree on one
semantic owner and behavior, record compatibility expectations, and complete
human architecture review. Optional owner and collaborator fields help routing
but may be left blank when responsibility is managed outside the repository.
