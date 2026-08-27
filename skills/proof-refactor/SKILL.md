---
name: proof-refactor
description: Refactor a completed, research-loop-validated proof closure into a compact, locally checkable proof, minimal derived proof DAG, and digest-bound handoff. Requires explicit user approval; do not repair mathematical gaps or draft a manuscript.
---

# Proof Refactor

## Objective

Turn a completed research proof into a compact, locally checkable proof and a
small derived proof DAG. The DAG records only the mathematical results used in
the refactored proof and their actual logical dependencies. Preserve exact
theorem scope and mathematical traceability.

This skill creates a derived exposition view. `KEY_RESULTS.md`,
`KEY_RESULTS.graph.json`, and their listed evidence remain the only canonical
mathematical source.

## Authorization and entry check

Start only when the user explicitly asks to run `$proof-refactor` or clearly
requests refactoring of a completed proof. A research readiness report, skill
inspection, or request to draft a paper is not by itself authorization to
create refactoring artifacts.

Locate the research root and run the available `$research-loop` graph helper
with `check --strict --complete --readability`, passing `--root PROJECT_ROOT`
when needed. Do not assume a repository-local copy of the helper. Use the
verified Goal roots and their complete `requires` closure as scope; the
readiness report is only a routing summary.

For each root, use `order ROOT` for dependency-first claim IDs and titles, then
use `show CLAIM` for exact bounded sections. Use `find QUERY` only when the
relevant claim is not yet known. Treat IDs and titles as navigation rather than
mathematical content or reader-facing terminology.

If the required `$research-loop` skill or helper cannot be located, stop and
report the missing dependency. Do not bypass or reimplement the completion
check ad hoc.

If the canonical completion check fails, stop with `RETURN TO RESEARCH` and
report the exact failing claims or evidence. Do not turn an incomplete closure
into polished prose.

## Source preservation

- Treat the canonical ledger, graph, evidence, and log as read-only.
- Create a new output directory and never overwrite a prior refactor.
- Read only in-scope claim sections, load-bearing evidence descriptions, and
  targeted log entries needed to understand the proof route.
- Do not create a second canonical claim inventory, research dependency graph,
  status ledger, or bibliography. `proof.graph.json` is a derived exposition
  graph and never replaces canonical research memory.

If a shorter route needs a new nontrivial load-bearing lemma, a changed theorem
scope, or a changed hard dependency, stop and route that work back to
`$research-loop`. Reordering or directly combining already proved material is
allowed; new research is not.

## Refactoring standard

Read [references/refactoring-rules.md](references/refactoring-rules.md) before
refactoring. In particular:

- work backward from the root theorem rather than following discovery order;
- build and validate the minimal proof DAG before writing explanatory prose;
- inline routine one-use facts unless separation materially improves reuse,
  understanding, auditability, or the computational/formal trust boundary;
- keep long analytic derivations outside the main spine without hiding them,
  and leave repetitive machine or formal data in its certificate layer;
- prefer standard mathematical language and formulas over invented internal
  labels;
- map every load-bearing sentence to canonical claim IDs or listed evidence.

Use numeric `PF-*` node IDs as stable navigation keys. Node titles are not
identifiers and may repeat. Each node must begin with its literal mathematical
statement; do not coin a title merely to make it unique.

Optimize the logical dependency structure, not the word count. Every
load-bearing step must state the actual formula, estimate, sign structure,
hypothesis mapping, or certificate conclusion that performs the inference.
Merely naming a tool
such as an Agmon estimate, Hellmann--Feynman, cooperativity, or standard
asymptotic integration is not an explanation.

Before handoff, perform the two bounded cold-read passes in
`references/refactoring-rules.md`: the undefined-symbol audit and the
dependency-edge audit. These are semantic checks, not keyword scores or schema
validation; a passing handoff validator does not replace them.

## Deliverables

Initialize a nonconflicting dated output folder with the bundled helper:

```bash
python3 <proof-refactor-directory>/scripts/validate_handoff.py \
  --root PROJECT_ROOT --init
```

The completed artifact has this layout:

```text
proof_refactor_YYYYMMDD/
├── proof.md
├── proof.graph.json
└── handoff.json
```

`proof.md` is not a manuscript. Use the language requested by the user;
otherwise preserve the dominant language of the canonical proof material. The
initializer creates an empty `proof.md` and minimal `proof.graph.json`; the
handoff helper creates `handoff.json` after semantic review. Include only what
the proof needs:

- the exact theorem scope and source roots;
- the refactored proof in logical order;
- separately retained technical or machine-verified obligations;
- the computational, formal, and literature trust boundary;
- node-level canonical source mappings and any remaining expository risk.

An overview is optional. Keep it only when it states the actual obstruction,
identity, estimate, or sign structure that makes the later proof easier to
check; route-preview prose alone is not a deliverable.

Do not create LaTeX submission files, an abstract, introduction, venue format,
or a new literature review. Those belong to `$proof-to-paper` after separate
user approval.

## Handoff and exit review

After the semantic proof view is complete and before creating or validating its
handoff, read [references/handoff.md](references/handoff.md). Follow its schema,
validator command, final source audit, and failure routing. Do not report
`REFACTORED READY` until both the canonical closure and handoff remain current.
