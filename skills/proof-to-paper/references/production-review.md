# Production and review

Read this reference before the first clean build, frozen review, or completion
claim.

## Production workflow

1. Preserve the original proof artifacts and create the new manuscript folder.
2. Confirm the incoming claim inventory and dependency graph, or create them
   only for a standalone proof corpus. Validate an optional proof-refactor
   handoff without treating it as a second claim ledger.
3. Verify load-bearing literature and any requested venue or style constraints.
4. Draft a locally checkable manuscript in proof-dependency order. Audit every
   changed mathematical passage against its canonical support.
5. Clean-build the manuscript, resolve actionable compiler and bibliography
   diagnostics, and inspect the PDF for layout defects.
6. Freeze the reviewed source, bibliography, and PDF with the bundled helper:

   ```bash
   python <proof-to-paper-directory>/scripts/paper_artifacts.py freeze \
     --manuscript PATH/TO/manuscript_YYYYMMDD
   ```

7. Review exactly those frozen bytes. Run the deterministic final check:

   ```bash
   python <proof-to-paper-directory>/scripts/paper_artifacts.py check \
     --manuscript PATH/TO/manuscript_YYYYMMDD
   ```

## Review–revision loop

Review the following dimensions separately enough that one does not mask
another:

- mathematical scope and dependencies: hypotheses, quantifiers, signs,
  normalizations, boundary conditions, non-circularity, and agreement between
  statements and proofs;
- sources and exposition: citation support, notation, terminology, and local
  checkability of every load-bearing transition;
- production: clean compilation, labels, citations, metadata, and PDF layout.

Independent reviewers are optional and require user authorization. A reviewer
works read-only on frozen files. Correctness, source-support, and production
defects block completion; purely stylistic preferences do not. After an
approved repair, rebuild, run `freeze --replace`, and review the new frozen
bytes before rerunning `check`.

## Acceptance criteria

- The manuscript clean-compiles independently.
- No unresolved actionable errors, warnings, references, citations,
  duplicated definitions, or layout defects remain. Document any verified
  benign warning class.
- Every cited claim is supported by its source and every bibliographic record
  is current.
- Every load-bearing transition is locally checkable; no technique name or
  abstract label substitutes for its operative formula, hypotheses, or sign
  mechanism.
- The proof architecture and theorem hierarchy are clear at the level needed
  by the manuscript and venue.
- The compiled PDF has been inspected for layout and stale-output defects.
- Final source and PDF hashes match the reviewed versions.
- The bundled artifact helper's `check` command passes.

Deliver the source path, PDF path, concise proof-architecture summary, and final
review verdict. Remove standalone-mode temporary ledger and audit debris from
the manuscript tree unless the user requests them.
