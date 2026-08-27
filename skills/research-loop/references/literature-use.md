# Targeted Literature Use

Use this protocol only when literature can resolve a concrete uncertainty in
the active Goal. Stop when the needed statement, scope, attribution, or access
status is established; citation volume is not progress.

## Decision rule

Look up literature when at least one of these holds:

- a load-bearing step imports an external theorem, definition, estimate, or
  convention whose exact hypotheses or conclusion have not been checked;
- a known result may remove a hard obstruction or materially redirect the
  current line of attack;
- the Goal requires source verification, priority, novelty, or a current
  state-of-the-art assessment;
- a specific source is cited but the relevant full text is unavailable.

Do not search merely to decorate a proved internal derivation, collect a broad
bibliography, or postpone a tractable proof attempt. An abstract, snippet, or
secondary citation is not enough for a load-bearing imported theorem.

## Source order

1. Search likely local PDFs, BibTeX files, and source notes by title, author,
   DOI, or distinctive theorem terms. Read only the relevant pages or sections.
2. If local material is insufficient, use a bounded web search and prefer the
   original paper, arXiv record, official publisher page, author copy, or
   institutional repository. Verify current literature claims online; do not
   infer absence or novelty from one failed query.
3. If full text is necessary and missing, download only the identified paper or
   bounded list under explicit authorization. Prefer a legitimate open copy.
   Use authenticated browser access only when authorized, and ask the user to
   complete login, SSO, MFA, or CAPTCHA; never inspect credentials, bypass
   access controls, or purchase access. Reuse a matching local copy, and verify
   that a new file is an openable PDF matching the DOI or title.

## Research memory

- In `KEY_RESULTS.md`, cite a load-bearing source near the imported statement
  and record the exact theorem, proposition, equation, page, or section plus
  the hypothesis mapping actually used.
- Add a downloaded local PDF to graph `evidence` only when it is load-bearing
  for the current root closure. Ordinary background citations stay out of the
  graph.
- In `RESEARCH_LOG.md`, retain a source audit, failed access route, or literature
  decision only when it will prevent repeated work. Paraphrase; do not copy
  large passages.
- Distinguish what the source proves, what is derived in this project, and what
  is only inferred. If assumptions have not been matched, keep the dependent
  claim `Conditional` or `Open`.
