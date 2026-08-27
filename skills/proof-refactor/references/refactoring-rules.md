# Proof Refactoring Rules

Use these rules to improve a validated proof without changing its mathematics.

## Find the explanatory spine

Read backward from each Goal root. Identify:

- the obstruction that makes the theorem nontrivial;
- the structural idea that overcomes it;
- the decisive estimates or classifications;
- the final assembly from those facts to the theorem.

Discovery chronology, failed routes, parameter tuning, and witness generation
do not belong in the main spine unless they explain an otherwise mysterious
choice.

## Decide what remains a lemma

Keep a result separate when at least one of these is materially true:

- it is used more than once;
- it isolates a reusable technique or invariant;
- it has independent mathematical interest;
- its proof is long enough to interrupt the main argument;
- it defines a clear literature, computation, or formal-verification boundary.

Inline routine facts that are used once and immediately. Combine adjacent
estimates when they have the same assumptions, method, and consumer. Do not
inline a result merely to reduce the lemma count when separation makes a hard
step easier to verify.

For each in-scope canonical claim, record one disposition in the traceability
section of `proof.md`: main spine, retained lemma, inlined, technical support,
machine/formal support, or not used by the shorter route. A claim omitted from
the exposition is not deleted from canonical research memory.

## Shorter proof routes

Prefer an already proved stronger statement over a chain of weaker statements.
Look for repeated uses of one invariant, comparison principle, monotone
quantity, convexity argument, duality, or algebraic identity. Replace repeated
instances with one clear argument when the existing closure proves that
replacement.

A reorganization is expository when it follows directly from proved material.
It becomes new research when it needs a nontrivial new claim, changes a domain
or quantifier, removes a genuinely load-bearing assumption, or changes the hard
dependency relation. Route the latter case back to `$research-loop`.

Prefer a shorter dependency route, not shorter prose. After compression, a
reader must still be able to reconstruct each load-bearing inference locally.

## Calculation detail

For each calculation-heavy inference, state the target and exact inputs; display
enough intermediate equalities or inequalities to expose substitutions,
cancellations, integrations by parts, boundary terms, domain restrictions, and
load-bearing signs or constants. Compress routine algebra only when adjacent
lines determine it. Use multiline display math for long calculations—for
example, an `aligned` chain—with breaks at meaningful transformations and brief
reasons for non-obvious transitions. Words such as `standard`, `straightforward`,
`after simplification`, or `this closes` do not replace a step. End with the
exact implication that advances the proof.

Compression removes discovery history, duplicate routes, and routine
repetition—not analytic derivations. Put long derivations in named technical
subsections of `proof.md` and cite them from the main spine; `KR-*` or log
references provide traceability only. Machine tables may remain external only
if `proof.md` states the exact proposition, analytic role, and trust boundary.

## Separate human explanation from technical verification

Let the main proof state what a technical module proves, why that statement is
the needed one, and how it feeds the next step. Keep finite interval slices,
large coefficient tables, generated witnesses, tactic scripts, and repetitive
case checks in their existing certificate or formal layer. Never replace a
missing mathematical bridge with a reference to code.

## Terminology discipline

Prefer standard vocabulary. State the object, formula, or property before
naming it. A nonstandard term is justified only if it has a precise referent,
is reused, shortens later reasoning, and cannot be replaced naturally by a
standard term.

A technique name is not a proof step. For a load-bearing use of an estimate,
eigenvalue derivative formula, positive-system argument, or asymptotic theorem,
write the relevant identity or sign structure and the hypotheses that make it
applicable before naming or citing the technique.

Remove or rewrite:

- one-use coined terms;
- internal gate, package, stage, pipeline, or architecture names;
- dense noun stacks made from several adjectives;
- labels that merely restate a file name or discovery history;
- claims that a construction is exact, sharp, canonical, or transparent
  without a literal mathematical reason.

Stable `KR-*` identifiers may remain in traceability notes, but they are not
reader-facing mathematical terminology. Pair an identifier with the literal
result or its local proof location rather than copying an opaque mnemonic as
the explanation.

## Semantic audit

Compare the refactored proof with the canonical closure, not only with the
readiness summary. Check:

- theorem hypotheses and conclusions;
- function spaces, domains, boundary conditions, gauges, and normalizations;
- open versus closed endpoints and uniform versus pointwise statements;
- every imported theorem's hypothesis mapping;
- every computational statement's analytic interpretation;
- availability of each result before its use;
- absence of circular explanation.

If a sentence cannot be mapped to a canonical claim, evidence artifact, or a
fully written elementary inference, it is not ready for handoff.
