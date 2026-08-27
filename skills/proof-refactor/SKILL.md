---
name: proof-refactor
description: After explicit user approval, refactor a validated research-loop proof closure into a conceptually compressed, locally checkable proof view with claim traceability and a digest-bound handoff for proof-to-paper. Do not repair new mathematical gaps or draft a manuscript.
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
with `check --strict --complete`, passing `--root PROJECT_ROOT` when needed. Do
not assume a repository-local copy of the helper. Use the verified Goal roots
and their complete `requires` closure as scope; the readiness report is only a
routing summary.

If the canonical completion check fails, stop with `RETURN TO RESEARCH` and
report the exact failing claims or evidence. Do not turn an incomplete closure
into polished prose.

## Source preservation

- Treat the canonical ledger, graph, evidence, and log as read-only.
- Create a new output directory and never overwrite a prior refactor.
- Read only in-scope claim sections, load-bearing evidence descriptions, and
  targeted log entries needed to understand the proof route.
- Record the current Goal roots and root digests before writing the derived
  proof.
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

For analysis-oriented work, do not introduce fraktur notation. Prefer
ordinary Roman, Greek, or calligraphic symbols; if the canonical source uses a
fraktur symbol, choose a conventional replacement and state the mapping once.

## Deliverables

Create a new folder such as:

```text
proof_refactor_YYYYMMDD/
├── proof.md
└── handoff.json
```

`proof.md` is not a manuscript. Unless the user explicitly requests another
language, write every generated file in English, including prose in Markdown,
comments, tables, and ancillary documentation. Conversation may follow the
user's language. Include only what the proof needs:

- the exact theorem scope and source roots;
- a concise account of the core mathematical idea;
- the refactored proof in logical order;
- separately retained technical or machine-verified obligations;
- the computational, formal, and literature trust boundary;
- claim-level traceability and any remaining expository risk.

Do not create LaTeX submission files, an abstract, introduction, venue format,
or a new literature review. Those belong to `$proof-to-paper` after separate
user approval.

## Handoff contract

After semantic review, write the minimal `handoff.json`:

```json
{
  "schema_version": 1,
  "kind": "proof-refactor-handoff",
  "status": "validated",
  "source": {
    "graph": "KEY_RESULTS.graph.json",
    "roots": ["KR-001"],
    "root_digests": {"KR-001": "sha256:<64 lowercase hex>"}
  },
  "proof": "proof.md",
  "proof_sha256": "sha256:<64 lowercase hex>"
}
```

The graph path must be exactly `KEY_RESULTS.graph.json` in the research root;
old or alternate graph copies are not valid handoff sources. The proof path is
relative to the handoff directory. The manifest binds the derived view to the
complete current root set and recorded root digests; it does not claim to
validate the mathematics by itself.

Use the bundled validator:

```text
python scripts/validate_handoff.py --root PROJECT_ROOT PATH/TO/handoff.json
```

The validator checks schema, path containment, source roots/digests, and the
proof byte hash. It deliberately does not duplicate DAG, ledger, evidence, or
freshness validation from `$research-loop`.

## Exit review and routing

Before reporting success:

1. audit the refactored proof against every claim in the source closure;
2. confirm that assumptions, definitions, domains, quantifiers, signs, and
   conclusions did not change;
3. rerun relevant existing certificate or formal checks when the rewritten
   exposition relies on their precise outputs;
4. cold-read the load-bearing passages without project-internal context and
   repair any passage whose inference is carried only by a technique name;
5. rerun `check --strict --complete` to detect concurrent canonical changes;
6. validate `handoff.json` against the current files.

Report `REFACTORED READY` only when the canonical closure is still complete,
the proof is traceable, and the handoff validator passes. This status does not
authorize paper drafting.

Use these failure routes:

- canonical completion failure or a genuine central gap: `RETURN TO RESEARCH`;
- changed source roots/digests or proof hash: `STALE OR INVALID HANDOFF`;
- intact source but incomplete exposition mapping: remain in `$proof-refactor`
  and repair the derived proof.

After `REFACTORED READY`, ask whether the user wants to start
`$proof-to-paper`, rerun refactoring, or stop. Never invoke the next skill
without explicit drafting approval.
