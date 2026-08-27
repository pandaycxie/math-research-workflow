# Graph and ledger memory

Read this reference only when creating or migrating research memory, changing
hard dependencies, revising an upstream claim, managing evidence or review
digests, or auditing the graph.

## Initialization and claim format

If the memory files are absent, use the bundled initializer:

```bash
python3 <skill-directory>/scripts/research_graph.py --root <research-root> init
```

The command creates the three minimal memory files and refuses to overwrite an
existing one. Its graph starts as:

```json
{"schema_version": 3, "ledger": "KEY_RESULTS.md", "roots": [], "requires": {}, "evidence": {}, "root_digests": {}}
```

Every claim ID has the form `KR-<number>` or `KR-<number>-<MNEMONIC>`, such as
`KR-001`, `KR-030-COERCIVITY`, or the legacy form `KR-189-FULLRADIUSL3`. A
mnemonic starts with an uppercase letter and may contain uppercase letters or
digits. Use `next-id` to allocate the next append-only number and keep
zero-padding consistent. Prefer the numeric form. An optional suffix must be
one established mathematical term already present in the literal title; do not
compress several ideas into a newly coined label. Existing mnemonic IDs remain
valid and need not be renamed.

Format headings as `### KR-ID — Exact claim title [Status]`. Ordinary
`###` subheadings inside a claim remain part of that claim and its review
digest. A claim ends at the next canonical claim heading or a higher-level
Markdown section outside fenced code blocks.

Use exactly `Open`, `Conditional`, `Proved`, `Rejected`, or
`Superseded`. Put qualifications in the claim body or split mixed
proved/open content into separate claims. A logically proved implication may
state its assumptions in its exact scope; do not disguise an unresolved Goal
as an unconditional proved root.

## Readable claim and log records

The identifier helps retrieval; the title and first paragraph must carry the
mathematics. In `KEY_RESULTS.md`:

- state the object and the scoped conclusion, open question, or obstruction in
  the title;
- put the exact estimate, implication, obstruction, theorem, or question first;
- retain only the shortest checkable support, limitations, and useful file
  pointers in the claim; keep exploration and chronology in the log.

In `RESEARCH_LOG.md`, use a literal question or conclusion as the heading and
state the outcome first. A failed route should identify the failed inequality,
sign, implication, or counterexample rather than only name the route. Do not
force a rigid template when the mathematics is already locally clear.

For example, replace “the coercivity gate closes” with a literal statement such
as `$Q[u] \ge c\lVert u\rVert^2$ on the orthogonal complement of the kernel`.
Replace “the compactness bridge fails” with the actual missing implication or
counterexample.

## Hard dependencies and revision

Only explicit `requires` edges block a claim or determine proof order.
Narrative references and alternative proof routes are not dependencies. A
`Proved` claim may require only proved claims.

After changing an upstream claim, run `impact CLAIM` and re-review its
descendants before trusting them. Leave affected root digests stale until the
review is complete. When the Goal or success criterion changes, update
`roots` and remove obsolete root digests.

## Evidence and review digests

Keep `evidence` small. Map only claims with external load-bearing artifacts
to relative files inside the research root. For a computationally proved claim
in the active hard closure, list the verifier and irreducible inputs, record a
reproduction command in the ledger, and explain what remains trusted rather
than checked.

The helper hashes listed evidence but never executes it during ordinary
checks. A `root_digests` entry is a review acknowledgement, not mathematical
proof. It covers the root's canonical claim sections, hard edges, and listed
evidence contents. Record or refresh it only after reviewing the
dependency-first closure and satisfying its reproduction obligations.

Schema version 2 remains readable for inspection, but completion requires
schema version 3.

## Helper commands

The bundled `scripts/research_graph.py` validates and retrieves memory; it
never chooses a research step.

- `check`: validate ledger links, statuses, and the DAG after structural
  changes.
- `check --strict`: audit all status labels and listed evidence paths.
  Unindexed ledger claims and transitively implied edges are compact warnings;
  add `--verbose` only when their identities are needed.
- `check --readability`: report only structural readability risks and an
  informational mnemonic count, without changing validity or completion.
- `next-id`: return the next append-only numeric claim ID.
- `find QUERY`: search claim IDs and literal titles with bounded output.
- `summary TARGET`: show one indexed closure's size, statuses, evidence,
  digest freshness, readiness, and target title.
- `show CLAIM`: print one bounded exact ledger section; use `--full` only
  after deliberately deciding that an oversized section is necessary.
- `impact CLAIM`: list descendants and their titles after an upstream revision.
- `order CLAIM`: print a dependency-first closure order with titles.
- `dot`: emit a Graphviz view.

The helper discovers the nearest parent graph. Pass `--root PATH` when the
intended project is ambiguous or `--graph PATH` for an explicit graph.
