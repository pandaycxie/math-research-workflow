# Proof Refactoring Rules

Use these rules to improve a validated proof without changing its mathematics.

## Build the proof DAG first

Work backward from each canonical Goal root. Before writing explanatory prose,
create the smallest DAG that exposes the theorem, the results it actually uses,
and their logical order.

Use numeric node IDs `PF-001`, `PF-002`, and so on. IDs are unique; titles are
ordinary mathematical retrieval text and may repeat. Do not add mnemonic
suffixes or coin a title to distinguish two nodes.

Each node in `proof.graph.json` has exactly:

- `title`: a short literal mathematical title;
- `statement`: the exact mathematical assertion used in the proof;
- `requires`: direct `PF-*` prerequisites;
- `sources`: one or more canonical `KR-*` claims supporting the node.

Every node must lie in a proof root's closure. Omit discovery order, failed
routes, unused alternatives, commentary-only nodes, and organizational stages.
An elementary inference belongs in the proof of a sourced node rather than in
an unsourced DAG node. The DAG is derived exposition metadata; it does not
change canonical claims or their `requires` edges.

Write each DAG node in `proof.md` under
`### PF-ID — Mathematical title`, with the exact `statement` first. The title may
repeat another title. The statement, hypotheses, and source mapping distinguish
the nodes.

## Decide what remains a node

Keep a result separate when it is used more than once, isolates a reusable
technique or invariant, has independent mathematical interest, would interrupt
the main argument, or defines a real literature, computation, or formal-
verification boundary.

Inline routine one-use facts. Combine adjacent estimates only when they have
the same assumptions, method, and consumer. Prefer an already proved stronger
statement over a chain of weaker statements, but do not remove a genuinely
load-bearing hypothesis or dependency.

A reorganization is expository when it follows directly from proved material.
It becomes new research when it needs a nontrivial new claim, changes a domain
or quantifier, or changes the hard dependency relation. Route the latter case
back to `$research-loop`.

Before handoff, every claim in the canonical root closure must support at least
one proof node, including inlined and technical support. If a shorter route
truly makes a canonical dependency unnecessary, stop and return that dependency
change to `$research-loop`; do not silently omit, alter, or archive it here.

## Require mathematical payload

Every paragraph in the reader-facing proof must do at least one of the
following:

- state a definition, hypothesis, or mathematical conclusion;
- give the formula, estimate, sign relation, or case distinction used next;
- map the hypotheses of an imported result;
- perform an inference from already stated facts;
- state a precise computational, formal, or literature trust boundary;
- provide concise canonical traceability.

Delete a paragraph if removing it changes none of those. A route preview,
technique name, or claim that a step is key, exact, sharp, canonical, or clear
does not carry an inference by itself.

For a load-bearing estimate, eigenvalue derivative formula, positive-system
argument, or asymptotic theorem, write the relevant identity or sign structure
and the hypotheses that make it applicable. Never replace a mathematical
inference with a reference to code.

For a calculation-heavy inference, state the target and exact inputs. Use
multiline display math, such as an `aligned` chain, to expose substitutions,
cancellations, integrations by parts, boundary terms, domain restrictions, and
load-bearing signs or constants. Break at meaningful transformations, briefly
justify non-obvious transitions, and end with the exact implication used next.
`Standard`, `straightforward`, or `after simplification` is not a proof step;
compress only algebra fixed by adjacent displayed lines.

Do not externalize a load-bearing analytic derivation merely to shorten prose.
Put a long derivation in a named technical subsection of its `PF-*` section; a
`KR-*` or log reference supplies traceability, not proof.

## Use mathematical terminology

Prefer terminology already used in the canonical source or standard in the
subject. Introduce a nonstandard term only after defining its mathematical
referent and only when repeated use materially shortens the proof.

Remove or rewrite reader-facing gate, bridge, package, stage, pipeline,
architecture, or similar organizational names; one-use coined terms; dense
noun stacks; and labels derived only from file names or discovery history.
`PF-*` and `KR-*` IDs may appear in headings or traceability, but they are not
mathematical explanations.

## Separate proof from technical verification

State what a technical module proves, why that exact statement is needed, and
how it enters the next inference. Keep coefficient tables, generated witnesses,
tactic scripts, interval subdivisions, and repetitive case checks in their
existing certificate or formal layer. Such data may remain external only when
`proof.md` states the exact finite proposition, its analytic role, and the trust
boundary.

## Semantic audit

Compare the proof and proof DAG with the canonical closure. Check theorem
hypotheses and conclusions; spaces, domains, boundary conditions, gauges, and
normalizations; endpoint and uniformity claims; imported-theorem hypotheses;
computational interpretations; dependency order; and absence of circularity.

Then make two bounded passes over the reader-facing proof:

1. **Undefined-symbol audit.** Read in order. Before the first load-bearing use
   of every nonstandard symbol, function, operator, parameter, index, or named
   object, require a local definition or an unambiguous definition already in
   scope. State any domain, quantifier, or parameter dependence needed for the
   inference. A heading, source ID, or later definition does not count.
2. **Dependency-edge audit.** Check every direct edge `PF-A -> PF-B` once. In
   the `PF-B` section, locate the formula or sentence that uses the mathematical
   statement of `PF-A` and performs the inference needed by `PF-B`. A bare
   citation such as “by PF-A” or “combining the preceding results” does not
   count. If no such use exists, write the inference or remove the spurious
   derived edge; if this reveals a changed canonical hard dependency, return it
   to `$research-loop`.

Do not create a separate audit report unless the user asks for one. Do not use
word counts, keyword counts, or invented terminology scores as pass criteria.

Cold-read the proof once without project-internal terminology. Remove every
paragraph that fails the mathematical-payload test and every new reader-facing
term that is neither standard, source-established, nor mathematically defined.
If a load-bearing sentence cannot be mapped to a DAG node, canonical claim,
evidence artifact, or fully written elementary inference, it is not ready.
