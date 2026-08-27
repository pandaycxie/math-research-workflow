# Handoff and exit review

Read this reference after the semantic proof view is complete and before
creating or validating its handoff.

## Handoff creation and contract

After semantic review, create `handoff.json` from the canonical graph and proof
bytes with the bundled helper:

```bash
python <proof-refactor-directory>/scripts/validate_handoff.py \
  --root PROJECT_ROOT --create --proof proof.md \
  PATH/TO/handoff.json
```

The helper writes and immediately validates this minimal manifest:

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
complete current root set and recorded root digests; it does not validate the
mathematics by itself.

For a later validation without rewriting the handoff, run:

```bash
python <proof-refactor-directory>/scripts/validate_handoff.py \
  --root PROJECT_ROOT PATH/TO/handoff.json
```

The validator checks schema, path containment, source roots and digests, and
the proof byte hash. It does not duplicate DAG, ledger, evidence, or freshness
validation from `$research-loop`.

## Exit review and routing

Before reporting success:

1. audit the refactored proof against every claim in the source closure;
2. confirm that assumptions, definitions, domains, quantifiers, signs, and
   conclusions did not change;
3. rerun relevant existing certificate or formal checks when the rewritten
   exposition relies on their precise outputs;
4. cold-read load-bearing passages without project-internal context and repair
   any inference carried only by a technique name;
5. rerun `check --strict --complete` to detect concurrent canonical changes;
6. validate `handoff.json` against the current files.

Report `REFACTORED READY` only when the canonical closure is still complete,
the proof is traceable, and the handoff validator passes. This status does not
authorize paper drafting.

Use these failure routes:

- canonical completion failure or a genuine central gap: `RETURN TO RESEARCH`;
- changed source roots, digests, or proof hash: `STALE OR INVALID HANDOFF`;
- intact source but incomplete exposition mapping: remain in `$proof-refactor`
  and repair the derived proof.

After `REFACTORED READY`, ask whether the user wants to start
`$proof-to-paper`, rerun refactoring, or stop. Never invoke the next skill
without explicit drafting approval.
