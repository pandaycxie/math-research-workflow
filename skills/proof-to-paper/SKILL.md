---
name: proof-to-paper
description: Turn a completed proof corpus, validated research-loop closure, or current proof-refactor handoff into one publication-ready LaTeX manuscript. Requires explicit drafting approval; do not repair central proof gaps.
---

# Proof to Paper

## Objective

Turn validated mathematical work into one publication-ready LaTeX manuscript
without strengthening hypotheses, weakening conclusions, or hiding proof gaps.

## Authorization and inputs

Start paperization only when the user explicitly asks to run `$proof-to-paper`
or otherwise clearly approves drafting the paper. Research completion, a
readiness report, a status question, or a request to inspect this skill is not
authorization.

Use one authoritative input:

- a validated `$research-loop` root closure;
- a current `$proof-refactor` handoff backed by that closure; or
- a completed standalone proof corpus supplied or approved by the user.

For a research-loop input, locate its bundled graph helper and run
`check --strict --complete`, passing `--root PROJECT_ROOT` when needed. Treat
the canonical ledger, graph, evidence, roots, and hard closure as authoritative;
the readiness report is only a routing summary. Read only in-scope claim
sections, load-bearing evidence, and targeted log entries. Do not duplicate the
incoming ledger or broaden the scope without approval.

For a proof-refactor input, also run its bundled handoff validator. Use
`proof.md` as the preferred exposition only when its source roots, digests, and
proof hash remain current, and verify its load-bearing steps against canonical
claim traceability.

If the handoff is stale or invalid while the canonical closure still passes,
ask whether to rerun `$proof-refactor` or draft directly from the canonical
closure. A traceability defect returns to `$proof-refactor`; only a genuine
canonical gap returns to `$research-loop`.

If a required upstream skill, helper, or validator cannot be located, stop and
report the missing dependency rather than recreating its validation gate.

If the files reveal a missing dependency or central gap, stop before drafting
or freeze the current draft and report the gap. Never repair it in paper prose.

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
completion claim. Do not create synchronized reader and submission variants.

## Entry checks

Before drafting:

- fix the approved theorem scope and proof source;
- reconcile notation, normalization, domains, signs, gauges, scaling, and
  subsequence versus full-sequence statements;
- include a computational claim as a theorem only when its declared proof
  standard supports that status;
- for a standalone corpus only, create the smallest temporary claim inventory
  needed to prevent omissions or circular exposition;
- stop if a central gap remains.

## Drafting and completion

After the entry checks pass and before outlining or drafting, read
[manuscript-standard.md](references/manuscript-standard.md). It defines the
proof-dependent architecture, writing standard, and bibliography policy.

Before the first clean build, frozen review, or completion claim, read
[production-review.md](references/production-review.md). Follow its production
workflow and acceptance criteria; do not report completion while any required
review remains unresolved.
