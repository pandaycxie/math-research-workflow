# Handoff and exit review

Read this reference after the semantic proof view is complete and before
creating or validating its handoff.

## Derived proof DAG

`proof.graph.json` is a compact, noncanonical DAG with this exact shape:

```json
{
  "schema_version": 1,
  "kind": "proof-refactor-dag",
  "roots": ["PF-001"],
  "nodes": {
    "PF-001": {
      "title": "Literal mathematical title",
      "statement": "Exact mathematical statement",
      "requires": [],
      "sources": ["KR-001"]
    }
  }
}
```

Use numeric `PF-*` IDs. Titles need not be unique. Every node must have at
least one canonical source, appear in a proof root's closure, and have exactly
one matching `### PF-ID — Title` section in `proof.md`. The section must begin
with the node's exact `statement`. The helper rejects cycles, dangling edges,
orphan nodes, incomplete canonical closure coverage, sources outside the
current canonical root closure, and proof roots that do not map the canonical
Goal roots.

These checks establish structure and byte-level consistency, not mathematical
truth. A genuinely unnecessary canonical dependency must return to
`$research-loop`; this helper never alters research memory.

## Handoff creation and contract

After semantic review, create `handoff.json` from the canonical graph, proof,
and proof DAG:

```bash
python3 <proof-refactor-directory>/scripts/validate_handoff.py \
  --root PROJECT_ROOT --create --proof proof.md \
  PATH/TO/handoff.json
```

The helper uses `proof.graph.json` beside the handoff unless
`--proof-graph PATH` is given. New handoffs use schema version 2:

```json
{
  "schema_version": 2,
  "kind": "proof-refactor-handoff",
  "status": "validated",
  "source": {
    "graph": "KEY_RESULTS.graph.json",
    "roots": ["KR-001"],
    "root_digests": {"KR-001": "sha256:<64 lowercase hex>"}
  },
  "proof": "proof.md",
  "proof_sha256": "sha256:<64 lowercase hex>",
  "proof_graph": "proof.graph.json",
  "proof_graph_sha256": "sha256:<64 lowercase hex>"
}
```

The canonical graph path must be exactly `KEY_RESULTS.graph.json` in the
research root. Proof and proof-DAG paths are relative to the handoff directory.
The manifest binds the derived files to the complete current root set and
recorded root digests. Legacy schema-version-1 handoffs without a proof DAG
remain readable but are not produced for new refactors.

For later validation without rewriting the handoff, run:

```bash
python3 <proof-refactor-directory>/scripts/validate_handoff.py \
  --root PROJECT_ROOT PATH/TO/handoff.json
```

The validator does not replace `$research-loop`'s completion, evidence, or
freshness checks.

## Exit review and routing

Before reporting success:

1. audit every proof-DAG node and edge against its canonical sources;
2. perform the undefined-symbol audit from
   [refactoring-rules.md](refactoring-rules.md);
3. perform the dependency-edge audit from
   [refactoring-rules.md](refactoring-rules.md);
4. confirm that assumptions, definitions, domains, quantifiers, signs, and
   conclusions did not change;
5. rerun relevant certificate or formal checks when the proof uses their exact
   outputs;
6. apply the mathematical-payload and terminology audits from
   [refactoring-rules.md](refactoring-rules.md);
7. rerun `check --strict --complete` to detect concurrent canonical changes;
8. validate `handoff.json` against the current files.

Report `REFACTORED READY` only when the canonical closure remains complete,
the proof DAG is minimal and traceable, the reader-facing proof is locally
checkable, and the handoff passes.

Use these failure routes:

- canonical completion failure or a genuine central gap: `RETURN TO RESEARCH`;
- changed source roots, digests, proof bytes, or proof-DAG bytes:
  `STALE OR INVALID HANDOFF`;
- intact sources but incomplete DAG mapping or exposition: remain in
  `$proof-refactor` and repair the derived artifact.

This status does not authorize paper drafting. Never invoke `$proof-to-paper`
without the user's explicit drafting approval.
