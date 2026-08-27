# Production and review

Read this reference before the first clean build, frozen review, or completion
claim.

## Production workflow

1. Preserve the original proof artifacts and create the new manuscript folder.
2. Confirm the incoming claim inventory and dependency graph, or create them
   only for a standalone proof corpus. Validate an optional proof-refactor
   handoff without treating it as a second claim ledger.
3. Verify the literature and calibrate any requested writing style.
4. Design the section hierarchy and theorem dependency map.
5. Draft a locally checkable synchronized mathematical core, then edit the
   submission version for concision and annotate the reader version.
6. Perform a line-by-line self-audit and compare both versions against the
   core-result ledger after every mathematical repair.
7. Clean-build both manuscripts; verify current table-of-contents entries,
   page numbers, and hyperlinks; visually inspect both PDFs.
8. Freeze the sources and PDFs, record their hashes, and begin review.

## Review–revision loop

Use independent reviewers or subagents only when the user has authorized that
review mode and it is available. Otherwise perform the same passes separately
and sequentially. Reviewers must work read-only on a frozen version and compile
only in temporary directories.

Run at least these passes:

1. **Mathematical referee:** search for literal counterexamples and audit
   quantifiers, signs, coefficients, scaling, boundary conditions, gauges,
   compactness, regularity, coercivity domains, artificial interfaces, and
   subsequence versus full-sequence claims.
2. **Dependency referee:** test non-circularity, theorem scope, hidden
   assumptions, availability of every input before use, and agreement between
   statements and proofs.
3. **Literature and exposition referee:** verify citations and metadata; audit
   structure, notation, tone, redundancy, and synchronization. Fail a
   load-bearing passage whose logic depends on an unexplained technique name.
4. **TeX and PDF referee:** clean-compile, check labels and citations, inspect
   metadata, and visually examine every page for clipping, overflow, broken
   formulas, blank pages, or stale output.

Classify findings as fatal, major, or minor. Treat every unresolved
correctness, support, synchronization, or production defect as `FAIL`;
optional stylistic preferences are non-blocking unless they expose a concrete
defect. Consolidate repairs when practical, rebuild both versions, freeze new
hashes, and repeat exact-hash review. Do not claim `PASS` for a stale PDF or a
source different from the reviewed hash. A reviewer must not silently edit the
frozen manuscript.

Stop only when all required reviews return `PASS` with no residual major or
minor issue, or when a genuine mathematical gap requires the user's decision
about returning to research.

## Acceptance criteria

- Both manuscripts clean-compile independently.
- No unresolved actionable errors, warnings, references, citations,
  duplicated definitions, or layout defects remain. Document any verified
  benign warning class.
- Every cited claim is supported by its source and every bibliographic record
  is current.
- Every load-bearing transition is locally checkable; no technique name or
  abstract label substitutes for its operative formula, hypotheses, or sign
  mechanism.
- The theorem hierarchy is visible from the introduction, table of contents,
  and section openings.
- Both manuscripts contain a current rendered table of contents at depth two,
  unless a documented venue requirement prohibits it.
- The reader and submission versions agree mathematically.
- Every PDF page has been visually inspected.
- Final source and PDF hashes match the reviewed versions.

Deliver the two source paths, the two PDF paths, a concise proof-architecture
summary, and the final review verdict. Remove standalone-mode temporary ledger
and audit debris from the manuscript tree unless the user requests them.
