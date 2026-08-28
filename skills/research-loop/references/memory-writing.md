# Mathematical memory writes

Read this reference immediately before creating, replacing, or appending any
durable research-memory record.

## Admit a write

First state the exact delta in one sentence. Choose exactly one destination:

- write no record for recap, planning, ordinary algebra, repeated evidence, or
  a reformulation with unchanged mathematical content;
- update or add a Key Result only when a claim's statement, scope, hypotheses,
  status, hard dependencies, or load-bearing proof changes;
- append one research-log event for a reusable derivation, a reproducible
  computation, an exact failed implication, a counterexample, or a decision
  that changes the next calculation;
- use a registered evidence file for long generated output, long mechanical
  algebra, code, or irreducible computational inputs.

Search titles with `find` and relevant log metadata with `log-find` before
adding a record. Replace the existing claim when the delta changes that claim;
do not append a second account of the same result.

## Retain proved results while pruning routes

Do not demote or erase a still-valid, locally checkable proved claim solely
because it is absent from the active proof route. Keep it as an unrooted Key
Result when at least one of the following holds:

- it gives an exact rigidity, equality classification, coercivity, selector,
  compactness, or obstruction statement;
- it excludes a nontrivial class of competitors or confines a possible
  counterexample to a strictly smaller regime;
- it supplies a reusable hypothesis-to-conclusion endpoint for another route;
- reconstructing it would require substantial analysis or create a material
  risk of losing hypotheses, constants, equality cases, or boundary terms.

State the theorem's exact scope in its hypotheses and conclusion. Put an
explanatory non-implication in the log unless the non-implication is itself a
precise reusable mathematical result; in that case record it as a separate Key
Result. Use literal retrieval terms in the title, keep the theorem out of every
Goal root's hard closure unless it is actually required, and bind long proof
details as evidence. Unrooted claims do not enter `resume` or a root summary by
default, so bounded retrieval does not require mathematical deletion.

Demote a result to the log or evidence only when its claim is an exact
duplicate, has been superseded, is false or inapplicable under the current
definitions, or no longer has a locally checkable proof. Prune redundant
derivations, abandoned route scaffolding, and repeated narrative before
pruning a proved reusable theorem.

## State mathematics before naming it

A record must be intelligible to a mathematician who has not read the
conversation. Its heading and first paragraph state:

1. the objects, variables, domain, and quantified range;
2. the hypotheses actually used;
3. the exact equality, inequality, implication, obstruction, counterexample,
   or open target;
4. the status and every unresolved endpoint, sign, regularity, or numerical
   assumption.

Define every nonstandard symbol before using it. Do not replace a statement by
an invented noun such as “bridge”, “gate”, “package”, “mechanism”, “closure”,
or “certificate”. Such a word is permitted only after the literal mathematical
statement is present and only if it shortens later references. Delete the word
as a test: if the remaining text no longer specifies something checkable,
rewrite the record.

## Write theorem-ledger entries by status

Keep research narration out of `KEY_RESULTS.md` without deleting mathematics:

- `Open`: only the definitions, hypotheses, and exact open statement.
- `Conditional` or `Proved`: the exact statement and shortest locally
  checkable derivation or proof spine.
- `Rejected`: the failed assertion and its calculation, obstruction, or
  counterexample.
- `Superseded`: identify the replacement claim and retain no duplicate proof;
  preserve any non-duplicated valid theorem as its own Key Result.

Put motivation, chronology, route comparisons, preliminary targets, next
actions, and literature inventories in `RESEARCH_LOG.md`. Never move or delete
a hypothesis, endpoint, regularity or sign condition, constant, equality case,
or load-bearing proof step merely for brevity.

## Record a calculation

For every load-bearing calculation, include enough consecutive lines to check
the transition from the stated inputs. A Key Result or its linked evidence must
show:

- the definition substituted and the domain of integration or summation;
- intermediate equalities and inequalities;
- the theorem, identity, sign, monotonicity, or bound used at each non-algebraic
  step;
- boundary terms, endpoint values, constants, and inequality directions;
- the final expression and the range on which it proves the stated claim.

For example, do not write “simplification gives the bound”. Write the actual
chain in the form

$$
A(t)
= \int_a^b F(t,x)\,dx
= B(t)+[G(t,x)]_{x=a}^{x=b}
\le B(t)+C(t),
$$

and state why the boundary expression is at most $C(t)$ for every allowed
$t$. Numerical evidence includes inputs, precision or interval enclosure,
reproduction command, and the distinction between proved rounding bounds and
floating-point observations.

Keep the shortest locally checkable proof spine in `KEY_RESULTS.md`. An `Open`
or `Superseded` entry should normally fit within 40 lines and 4 KiB. A
`Conditional`, `Proved`, or `Rejected` entry should normally fit within 160
lines and 12 KiB. These are readability budgets, not permission to omit proof
steps. If a proof-bearing claim exceeds its budget, split genuine intermediate
theorems into Key Results or put long mechanical detail in one registered
evidence file and cite the exact sections or line ranges that justify the
claim. Do not duplicate the same long derivation in the ledger and log.

## Update dependencies and status

Use `next-id` only for a genuinely new claim. A `Proved` claim may have only
`Proved` hard prerequisites. When an existing claim is strengthened,
weakened, rejected, or superseded:

1. replace its statement and status rather than retaining a contradictory
   current version;
2. update its `requires` and evidence entries;
3. run `impact CLAIM` and recheck every affected descendant before retaining
   its status;
4. leave affected Goal-root digests stale until that review is complete.

## Keep restart state bounded

Maintain exactly one `## Current restart point` near the top of
`RESEARCH_LOG.md`. Replace it; never append another copy. It contains only:

- Goal-root IDs; `resume` supplies their current statuses from the ledger and
  graph, so do not copy status words into this section;
- the last safe proved or conditional claim IDs;
- the active target as a literal formula or implication;
- the next concrete calculation or verification;
- IDs of failed routes that must not be repeated without a new hypothesis.

The section must be at most 40 lines and 6 KiB. It points to derivations instead
of copying them. A log event should normally stay below 80 lines and 8 KiB; if
more is mathematically necessary, preserve it in evidence and keep a literal
outcome plus exact pointer in the log.

## Verify the write

After a durable change:

1. run `check --memory`, and run `check --strict` after structural or
   evidence changes;
2. retrieve each changed claim with `show` and the new log event with
   `log-show` to confirm exact section boundaries;
3. run `resume` and verify that the returned next action follows from the
   cited statuses and formulas;
4. correct the record immediately if any reference is missing, ambiguous,
   stale, or outside the output budget.
