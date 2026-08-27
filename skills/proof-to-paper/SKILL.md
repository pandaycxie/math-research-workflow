---
name: proof-to-paper
description: After explicit user approval, convert a completed mathematical proof corpus, validated research-loop closure, or current proof-refactor handoff into synchronized publication-ready LaTeX manuscripts. Do not start from a readiness report alone or repair central proof gaps.
---

# Proof to Paper

## Objective

Turn validated mathematical work into two rigorous, compact English manuscripts without strengthening the hypotheses, weakening the conclusions, or hiding proof gaps.

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

If the files reveal a missing dependency or central gap, stop before drafting
or freeze the current draft, issue a concise research-gap report, and wait for
the user to decide whether to resume `$research-loop`. Never repair the gap in
paper prose.

## Deliverables

Create a new, suitably named folder without overwriting existing work. Unless the repository has a better convention, use:

```text
manuscript_versions_YYYYMMDD/
├── references.bib
├── submission_version/
│   ├── main.tex
│   └── output/pdf/main.pdf
└── reader_version/
    ├── main.tex
    └── output/pdf/reader_version.pdf
```

Use one authoritative bibliography, shared or mechanically synchronized. Both versions must compile independently.

Both `submission_version/main.tex` and `reader_version/main.tex` must include
a rendered table of contents. Unless venue-specific requirements explicitly
prohibit it, place `\tableofcontents` after the front matter and before the
introduction, and set the table-of-contents depth to two so that major sections
and their first-level subsections are visible. Keep the entries synchronized
with the final section hierarchy and verify that page numbers and hyperlinks
are current after the final clean build.

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

## Manuscript Architecture

Topologically sort the exposition by proof dependency. Prefer five to eight
major sections. Every generated manuscript must contain a table of contents;
use a depth-two table of contents by default so that major sections and their
first-level subsections are visible. Avoid a few enormous subsections that
hide decisive steps.

The introduction must contain:

- the precise problem and variational setting;
- the closest literature and the exact unresolved point;
- the new results, with assumptions and scope visible;
- the main theorem statements;
- a compact proof architecture showing how the principal modules interact.

Give each section a clear mathematical contract: its inputs, output, and downstream consumer. Use result-driven titles. Separate logically independent proof routes, such as profile selection and energy asymptotics. Place supporting results before their use when practical. Remove proof diaries, audit terminology, internal gate names, and obsolete failed approaches.

With a current proof-refactor handoff, preserve its proof spine, lemma
dispositions, technical boundary, and terminology cleanup unless
self-containedness or venue requirements demand a change. Verify every
mathematical adjustment against the canonical source.

## Writing Standard

Unless the user explicitly requests another language, write every generated
file entirely in English, including LaTeX, Markdown, captions, tables, code
comments, and ancillary documentation. Conversation may follow the user's
language.

- Treat compactness as a standing preference after correctness, exact scope,
  local verifiability, structural understanding, and venue requirements.
  Prefer the shortest sound proof architecture, not the shortest prose;
  exclude optional extensions and repetition, but retain enough detail for a
  skeptical expert reader to check every load-bearing transition locally.
- Among mathematically complete proof routes, prefer the shortest one with the
  least auxiliary notation, intermediate lemmas, case splitting, and repeated
  argument. Compress routine steps or cite a precise prior result, but never
  omit a load-bearing step or hide it behind “standard.”
- Be academic, restrained, precise, and plain. If no author is specified, calibrate the high-level style against Yong Yu's published papers: theorem-first organization, compact transitions, and proof-focused prose. Never copy phrasing.
- Let definitions, estimates, identities, and formulas carry the argument. Every prose sentence should motivate, define, connect, qualify, or conclude something mathematically necessary.
- A technique name is not a proof. A load-bearing passage must display or state
  the formula, weighted identity, sign structure, hypotheses, and conclusion
  that make the step work; phrases such as “by an Agmon estimate”,
  “Hellmann--Feynman applies”, “the system is cooperative”, or “standard
  asymptotic integration” cannot carry the inference by themselves.
- In analysis-oriented manuscripts, do not use fraktur fonts. Prefer ordinary
  Roman, Greek, calligraphic, or standard operator notation unless the user
  explicitly requires preserving fraktur notation.
- Typeset every initial-value or boundary-value problem as one braced system,
  using `cases` or an equivalent system environment, with each differential
  equation, initial condition, and boundary condition on its own line. Do not
  run multiple conditions together on one display line.
- Delete filler, hype, conversational asides, repeated scope defenses, and claims of obviousness. Reserve words such as “exact” and “sharp” for statements that are literally exact or sharp.
- Define every symbol before use. Quantify variables and constants. Keep energy conventions, coordinates, orientations, gauges, and scaling factors explicit and consistent.
- State each assumption once and track where it is used. Do not introduce extra assumptions for convenience.
- Give referee-level proofs of load-bearing estimates. Do not hide a new compactness, coercivity, matching, regularity, or liminf argument behind “standard.”
- Use primary, authoritative references. Verify current metadata, theorem numbers, hypotheses, and the claim supported by each citation. Include foundational and directly adjacent work without citation padding.
- Use mathematically informative abstracts, titles, keywords, and section openings. Omit a conclusion section unless it adds genuine mathematical content.

When style calibration is needed, inspect a small representative set of the named author's papers supplied locally or obtained from authoritative sources; extract structural traits rather than wording.

## Two Synchronized Versions

### Submission version

Make `submission_version/main.tex` concise, formal, self-contained, and publication-ready. Keep motivation proportional to its mathematical value. The introduction may be substantial; proofs should be economical but complete.

### Reader version

Make `reader_version/main.tex` a guided proof version for the author. Preserve the same assumptions, theorem conclusions, conventions, numbered mathematical statements, equation labels, and bibliography. Add only expository support:

- a reading order and dependency map;
- a notation or length-scale table when useful;
- brief section contracts;
- proof ideas before the hardest modules;
- checkpoints explaining what has just been proved and where it is used.

The reader version must never be mathematically stale or weaker. Port every mathematical correction to both versions before review.
Reader-only notes may aid navigation or motivation, but every explanation
needed to verify a proof must remain in the shared mathematical core.

## Production Workflow

1. Preserve the original proof artifacts and create the new manuscript folder.
2. Confirm the incoming claim inventory and dependency graph, or create them
   only for a standalone proof corpus. Validate an optional proof-refactor
   handoff without treating it as a second claim ledger.
3. Verify the literature and calibrate the requested writing style.
4. Design the section hierarchy and theorem dependency map.
5. Draft a locally checkable synchronized mathematical core, then edit the
   submission version for concision and annotate the reader version.
6. Perform a line-by-line self-audit and compare both versions against the core-result ledger after every mathematical repair.
7. Clean-build both manuscripts, verify that each PDF contains the table of
   contents with current entries, page numbers, and hyperlinks, and visually
   inspect the PDFs.
8. Freeze the sources and PDFs, record their hashes, and begin the independent review loop.

## Aggressive Review–Revision Loop

Use independent reviewers or subagents when available. Reviewers must work read-only on a frozen version and compile only in temporary directories.

Run at least these passes:

1. **Mathematical referee:** search for literal counterexamples and audit quantifiers, signs, coefficients, scaling, boundary conditions, gauges, compactness, regularity, coercivity domains, artificial interfaces, and subsequence versus full-sequence claims.
2. **Dependency referee:** test non-circularity, theorem scope, hidden assumptions, availability of every input before use, and agreement between statements and proofs.
3. **Literature and exposition referee:** verify citations and metadata; audit
   structure, notation, academic tone, redundancy, and synchronization of the
   two versions. Cold-read representative load-bearing passages and fail any
   passage whose logic depends on an unexplained technique name or abstract
   label.
4. **TeX and PDF referee:** clean-compile, check labels and citations, inspect metadata, and visually examine every page for clipping, overflow, broken formulas, blank pages, or stale output.

Classify findings as fatal, major, or minor. Treat every unresolved correctness, support, synchronization, or production defect as `FAIL`; optional stylistic preferences are non-blocking unless they expose a concrete defect. Consolidate findings, repair them in one batch when possible, rebuild both versions, freeze new hashes, and repeat the exact-hash review. Do not claim `PASS` for a stale PDF or a source different from the reviewed hash. A reviewer must not silently edit the frozen manuscript.

Stop only when all independent reviews return `PASS` with no residual major or
minor issue, or when a genuine mathematical gap requires pausing for the user
to decide whether to return to the research stage.

## Acceptance Criteria

- Both manuscripts clean-compile independently.
- There are no unresolved actionable errors, warnings, references, citations, duplicated definitions, or layout defects. Document any verified benign class or tool warning.
- Every cited claim is supported by the cited source and every bibliographic record is current.
- Every load-bearing transition is locally checkable; no technique name or
  abstract label substitutes for its operative formula, hypotheses, or sign
  mechanism.
- The theorem hierarchy is visible from the introduction, table of contents, and section openings.
- Both generated manuscripts contain a current, rendered table of contents at
  depth two by default, unless a documented venue requirement explicitly
  prohibits it.
- The reader and submission versions agree mathematically.
- Every PDF page has been visually inspected.
- Final source and PDF hashes match the versions that passed review.

Deliver the two source paths, the two PDF paths, a concise account of the proof
architecture, and the final review verdict. Remove any standalone-mode
temporary ledger and other audit debris from the manuscript tree unless the
user requests them.
