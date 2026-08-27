---
name: research-loop
description: Pursue an active theoretical or computational research Goal with minimal file-backed memory of key claims, hard dependencies, evidence, and restart state. Use for long-running research; report readiness without starting proof refactoring or paper drafting.
---

# Research Loop

Pursue the active Goal autonomously. The Goal is the only control plane; this
skill preserves enough durable state for long runs without imposing a fixed
stage plan, frontier policy, or mandatory method.

## Durable research memory

Use one research root for the active Goal. Prefer the nearest current or parent
directory containing `KEY_RESULTS.graph.json`; otherwise use the
user-designated project root or current workspace. Use an explicit root when
discovery is ambiguous.

For a new research root, initialize the three memory files without overwriting
existing work:

```bash
python3 <skill-directory>/scripts/research_graph.py --root <research-root> init
```

Maintain only these research-memory records:

- `KEY_RESULTS.md`: canonical important claims, exact scope, status, and
  load-bearing support;
- `KEY_RESULTS.graph.json`: sparse hard `requires` dependencies, selected
  evidence paths, Goal roots, and review digests;
- `RESEARCH_LOG.md`: reusable derivations, diagnostics, failed routes, and
  consequential decisions.

Before any durable write, identify the exact mathematical delta; if there is no
new or changed claim or reusable outcome of an event listed below, write
nothing. Packaging, recap, and ordinary reasoning are not new claims.

Write admitted entries for a mathematician who knows the subject but has not
seen the conversation. The entry heading and opening must state the object,
scope, and literal result without relying on a coined label. State the estimate,
implication, obstruction, theorem, counterexample, or computed result first.
Define nonstandard shorthand before use and retain it only if reused. As a
deletion test, remove local labels (for example, `mechanism`, `bridge`,
`package`, `audit`, `closure`, `trap`, `tube`, or `cone`) and progress
adjectives; if the entry no longer says what can be checked, disproved, or
reproduced, rewrite or omit it.

Read [graph-memory.md](references/graph-memory.md) before creating or migrating
the graph, changing dependency structure, revising an upstream claim, managing
evidence or digests, or running a graph audit.

Format ledger claims as
`### KR-ID — Exact claim title [Status]`, using exactly `Open`,
`Conditional`, `Proved`, `Rejected`, or `Superseded`. A `Proved`
claim must state its real scope and may depend only on proved prerequisites.
Only explicit `requires` edges are hard dependencies; exploratory and
alternative routes need not enter a Goal root's closure.

Use the helper's `next-id` command for a new claim and prefer the numeric ID
alone. An optional uppercase suffix is allowed only when it is one established
mathematical term already used in the literal title. Do not create compressed
compound labels or rename existing IDs solely to enforce this convention.

Numerical, empirical, or exploratory support remains `Conditional` unless it
meets the Goal's declared proof standard. If a `Proved` claim in the active
hard closure depends on a computation or another external artifact, register
its verifier and irreducible inputs as evidence and record the reproduction
command and trust boundary.

Treat conversation history as disposable. Keep one short
`## Current restart point` near the top of `RESEARCH_LOG.md`, replacing it
only at a material checkpoint. Record the Goal roots, state, last safe
checkpoint, and next safe action as pointers instead of duplicating derivations.

### Bounded retrieval

Inspect file size without loading the body when a memory file may be large. If
`KEY_RESULTS.md` or `RESEARCH_LOG.md` exceeds 2,000 lines or 200 KiB, never
print or read the whole file into model context merely to recover state or
locate one result.

- Start from `Current restart point`.
- Use graph `summary TARGET` for a compact closure view and `show CLAIM` for
  one bounded exact ledger section. For an oversized section, use targeted
  ranges; request `show --full` only when the whole section is necessary.
- Search the log by exact heading, `KR-*` reference, or targeted keyword, then
  read only the bounded relevant section.
- Do not migrate, renumber, or index historical log entries merely because a
  file is large.

## Work on events, not turns

- Update the ledger and affected hard edges after a substantive claim is added,
  strengthened, weakened, rejected, or superseded.
- Change graph roots only when the Goal or its success criterion changes.
- Append to the log only when an argument, experiment, failure, or decision is
  likely to matter later. Ordinary reasoning needs no file update.
- Give a log entry a heading that states its question or conclusion. For a
  rejected route, record the exact failed implication, estimate, sign, or
  counterexample so the route is not repeated without new information.

At a material research-progress checkpoint, state the current obstruction and
what changed. If repeated checkpoints cannot identify a narrower obstruction,
a new viable mechanism, or a rigorously excluded route, audit the line of
attack and choose a materially different one.

Difficulty is not a stopping condition. When a route stalls, inspect upstream
assumptions, test a counterexample or diagnostic, split a smaller intermediate
claim, reformulate without silently changing the Goal, or return to an
independent unresolved branch.

Declare `STALLED` only when progress requires an external condition or an
explicit user decision that cannot be supplied safely. Preserve a concrete
restart point; do not present mathematical difficulty, slow progress,
inconclusive evidence, or a transient runtime failure as completion.

## Conditional procedures

- For a load-bearing external theorem, attribution, current literature claim,
  or missing full text, read
  [literature-use.md](references/literature-use.md).
- When the Goal appears satisfied or the user asks for readiness, read
  [completion.md](references/completion.md) and perform its closure,
  reproduction, digest, and reporting checks.

Keep an unresolved Goal active until completion passes or the user explicitly
pauses or clears it. A readiness result does not authorize
`$proof-refactor`, `$proof-to-paper`, manuscript drafting, or creation of
their downstream artifacts; each requires the user's explicit approval.
