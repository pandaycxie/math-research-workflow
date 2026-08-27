# Manuscript standard

Read this reference after the paperization entry gate passes and before
outlining or drafting the manuscript.

## Sources and navigation

Use one authoritative bibliography. The manuscript must compile independently.

`main.tex` must include a rendered table of contents. Unless a venue requirement
explicitly prohibits it, place `\tableofcontents` after the front matter and
before the introduction, and set its depth to two. Keep entries, page numbers,
and hyperlinks current after the final clean build.

## Manuscript architecture

Topologically sort the exposition by proof dependency. Prefer five to eight
major sections and avoid a few enormous subsections that hide decisive steps.

The introduction must contain:

- the precise problem and variational setting;
- the closest literature and the exact unresolved point;
- the new results, with assumptions and scope visible;
- the main theorem statements;
- a compact proof architecture showing how the principal modules interact.

Give each section a clear mathematical contract: its inputs, output, and
downstream consumer. Use result-driven titles. Separate logically independent
proof routes and place supporting results before their use when practical.
Remove proof diaries, audit terminology, internal gate names, and obsolete
failed approaches.

With a current proof-refactor handoff, preserve its proof spine, lemma
dispositions, technical boundary, and terminology cleanup unless
self-containedness or venue requirements demand a change. Verify every
mathematical adjustment against the canonical source.

## Writing standard

Unless the user explicitly requests another language, write every generated
file entirely in English, including LaTeX, Markdown, captions, tables, code
comments, and ancillary documentation. Conversation may follow the user's
language.

- Treat compactness as a preference after correctness, exact scope, local
  verifiability, structural understanding, and venue requirements. Prefer the
  shortest sound proof architecture, not the shortest prose.
- Among mathematically complete routes, prefer the one with the least auxiliary
  notation, intermediate lemmas, case splitting, and repetition. Never omit a
  load-bearing step or hide it behind “standard.”
- Be academic, restrained, precise, and plain. Use theorem-first organization,
  compact transitions, and proof-focused prose unless the user or venue
  requires otherwise. Never imitate or copy an author's phrasing.
- Let definitions, estimates, identities, and formulas carry the argument.
  Every sentence should motivate, define, connect, qualify, or conclude
  something mathematically necessary.
- A technique name is not a proof. State the formula, sign structure,
  hypotheses, and conclusion that make every load-bearing use work.
- In an analysis-oriented manuscript, avoid fraktur fonts unless the user
  explicitly requires preserving them.
- Typeset each initial-value or boundary-value problem as one braced system,
  with every equation and condition on its own line.
- Delete filler, hype, conversational asides, repeated scope defenses, and
  unsupported claims of obviousness, exactness, or sharpness.
- Define every symbol before use. Quantify variables and constants. Keep
  conventions, orientations, gauges, and scaling factors explicit.
- State each assumption once and track its use. Do not add assumptions for
  convenience.
- Give referee-level proofs of load-bearing estimates. Do not hide a new
  compactness, coercivity, matching, regularity, or liminf argument behind
  “standard.”
- Use primary, authoritative references. Verify metadata, theorem locations,
  hypotheses, and the claim supported by each citation.
- Use informative abstracts, titles, keywords, and section openings. Omit a
  conclusion unless it adds genuine mathematical content.

When the user requests calibration to a named author or venue, inspect a small
representative set of authoritative examples and extract structural traits
rather than wording.

## Publication version

Make `main.tex` concise, formal, self-contained, and publication-ready. Keep
motivation proportional to its mathematical value; proofs should be economical
but complete. Add a dependency map, notation table, section contracts, or proof
ideas only when they materially improve verification or navigation.
