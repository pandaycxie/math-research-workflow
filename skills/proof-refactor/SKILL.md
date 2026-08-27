---
name: proof-refactor
description: Refactor a completed, research-loop-validated proof closure into a compact, locally checkable proof and digest-bound handoff. Requires explicit user approval; do not repair mathematical gaps or draft a manuscript.
---

# Proof Refactor

## Objective

Turn a completed research proof into a conceptually compressed, locally
checkable proof whose main idea, necessary lemmas, technical boundary, and
canonical claim support are easy to inspect. Preserve exact theorem scope and
mathematical traceability.

This skill creates a derived exposition view. `KEY_RESULTS.md`,
`KEY_RESULTS.graph.json`, and their listed evidence remain the only canonical
mathematical source.

## Authorization and entry gate

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
gate ad hoc.

If the canonical completion check fails, stop with `RETURN TO RESEARCH` and
report the exact failing claims or evidence. Do not turn an incomplete closure
into polished prose.

## Source preservation

- Treat the canonical ledger, graph, evidence, and log as read-only.
- Create a new output directory and never overwrite a prior refactor.
- Read only in-scope claim sections, load-bearing evidence descriptions, and
  targeted log entries needed to understand the proof route.
- Do not create a second claim inventory, dependency graph, status ledger, or
  bibliography.

If a shorter route needs a new nontrivial load-bearing lemma, a changed theorem
scope, or a changed hard dependency, stop and route that work back to
`$research-loop`. Reordering or directly combining already proved material is
allowed; new research is not.

## Refactoring standard

Read [references/refactoring-rules.md](references/refactoring-rules.md) before
refactoring. In particular:

- work backward from the root theorem rather than following discovery order;
- expose the obstacle, decisive structure, key estimate, and final assembly;
- inline routine one-use facts unless separation materially improves reuse,
  understanding, auditability, or the computational/formal trust boundary;
- keep long technical obligations outside the main spine without hiding them;
- prefer standard mathematical language and formulas over invented internal
  labels;
- map every load-bearing sentence to canonical claim IDs or listed evidence.

Optimize the proof architecture, not the word count. Every load-bearing step
must state the actual formula, estimate, sign structure, hypothesis mapping,
or certificate conclusion that performs the inference. Merely naming a tool
such as an Agmon estimate, Hellmann--Feynman, cooperativity, or standard
asymptotic integration is not an explanation.

## Deliverables

Initialize a nonconflicting dated output folder with the bundled helper:

```bash
python <proof-refactor-directory>/scripts/validate_handoff.py \
  --root PROJECT_ROOT --init
```

The completed artifact has this layout:

```text
proof_refactor_YYYYMMDD/
├── proof.md
└── handoff.json
```

`proof.md` is not a manuscript. Use the language requested by the user;
otherwise preserve the dominant language of the canonical proof material. The
initializer creates an empty `proof.md`; the handoff helper creates
`handoff.json` after semantic review. Include only what the proof needs:

- the exact theorem scope and source roots;
- a concise account of the core mathematical idea;
- the refactored proof in logical order;
- separately retained technical or machine-verified obligations;
- the computational, formal, and literature trust boundary;
- claim-level traceability and any remaining expository risk.

Do not create LaTeX submission files, an abstract, introduction, venue format,
or a new literature review. Those belong to `$proof-to-paper` after separate
user approval.

## Handoff and exit review

After the semantic proof view is complete and before creating or validating its
handoff, read [references/handoff.md](references/handoff.md). Follow its schema,
validator command, final source audit, and failure routing. Do not report
`REFACTORED READY` until both the canonical closure and handoff remain current.
