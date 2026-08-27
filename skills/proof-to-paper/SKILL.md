---
name: proof-to-paper
description: Turn a completed proof corpus, validated research-loop closure, or current proof-refactor handoff into one publication-ready LaTeX manuscript. Requires explicit drafting approval; do not repair central proof gaps.
---

# Proof to Paper

## Objective

Turn validated mathematical work into one rigorous, compact English manuscript
without strengthening hypotheses, weakening conclusions, or hiding proof gaps.

## Authorization and research handoff

Start paperization only when the user explicitly asks to run `$proof-to-paper`
or otherwise clearly approves drafting the paper. Research completion, a
readiness report, a status question, or a request to inspect this skill is not
authorization.

When invoked after `$research-loop`:

- treat `KEY_RESULTS.md` as the canonical claim ledger and
  `KEY_RESULTS.graph.json` roots plus their `requires` closure as the incoming
  paper scope;
- verify the closure with the bundled graph helper from the available
  `$research-loop` skill, passing `--root PROJECT_ROOT` when needed; do not
  assume a repository-local skill path. Then read only the closure's claim
  sections, load-bearing evidence, and targeted `RESEARCH_LOG.md` entries;
- use the readiness report as a routing summary, but verify the current files;
- keep claims outside the root closure excluded unless the user broadens the
  scope explicitly;
- reuse the canonical ledger and graph instead of building temporary
  duplicates.

When a `$proof-refactor` handoff is supplied:

- rerun the canonical `$research-loop` `check --strict --complete`; the
  handoff's `validated` status never substitutes for this gate;
- run the validator from the available `$proof-refactor` skill with the
  research root and `handoff.json`; do not assume a repository-local skill
  path;
- use `proof.md` as the preferred proof architecture only when the source
  roots/digests and proof hash are current;
- continue treating the canonical ledger, graph, and evidence as authoritative
  for theorem scope, dependencies, and correctness;
- verify every refactored proof step against its canonical claim traceability.

If the handoff is stale or invalid while the canonical closure still passes,
do not report a research gap. Ask whether to rerun `$proof-refactor` or bypass
the derived view and draft directly from the canonical closure. If the derived
proof has a traceability defect but the canonical proof is intact, return to
`$proof-refactor`; only a genuine canonical gap returns to `$research-loop`.

If a required upstream skill, helper, or validator cannot be located, stop and
report the missing dependency. Do not replace its validation gate with an ad
hoc approximation.

If the files reveal a missing dependency or central gap, stop before drafting
or freeze the current draft, issue a concise research-gap report, and wait for
the user to decide whether to resume `$research-loop`. Never repair the gap in
paper prose.

## Deliverables

Initialize a new manuscript directory with the bundled helper; it selects a
nonconflicting dated path and does not overwrite existing work:

```bash
python <proof-to-paper-directory>/scripts/paper_artifacts.py init \
  --root PROJECT_ROOT
```

The completed artifact has this layout:

```text
manuscript_YYYYMMDD/
├── references.bib
├── main.tex
├── output/pdf/main.pdf
└── artifact-manifest.json
```

The initializer creates the directory structure and empty bibliography. Write
the mathematical manuscript as `main.tex` and build `output/pdf/main.pdf`.
The artifact helper creates `artifact-manifest.json` only after the reviewed
source, bibliography, and PDF are frozen; its final check must pass before a
completion claim.

## Entry Gate

Before drafting:

1. Determine the approved scope. For a research-loop handoff, use the verified
   root closure; otherwise read the proof artifacts in scope.
2. For each in-scope claim, verify its canonical status and classify the
   evidence modality only where needed; do not recreate classifications already
   settled by the research ledger.
3. Include a computational or local-model claim as a theorem only when it has
   a written rigorous proof or a validated computer-assisted proof. Otherwise
   keep it outside the main conclusions.
4. If no canonical research ledger and dependency graph exist, build the
   smallest temporary claim inventory needed for paperization. Do not duplicate
   an incoming research-loop ledger.
5. Reconcile notation, normalization, signs, gauges, scaling conventions, subsequence/full-sequence claims, and theorem scope.
6. If a central gap remains, stop with a research-gap report and await the
   user's decision. Never convert a gap into a hidden assumption or a
   publishable theorem.

## Drafting and completion

After the entry gate passes and before outlining or drafting, read
[manuscript-standard.md](references/manuscript-standard.md). It defines the
proof-dependent architecture, writing standard, and bibliography policy.

Before the first clean build, frozen review, or completion claim, read
[production-review.md](references/production-review.md). Follow its production
workflow and acceptance criteria; do not report completion while any required
review remains unresolved.
