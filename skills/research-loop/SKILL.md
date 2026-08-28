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

Before any durable write or update, read
[memory-writing.md](references/memory-writing.md) and apply its admission,
calculation, replacement, and post-write checks. If there is no exact new or
changed mathematical statement or reusable event outcome, write nothing.

Read [graph-memory.md](references/graph-memory.md) before creating or migrating
the graph, changing dependency structure, revising an upstream claim, managing
evidence or digests, or running a graph audit.

Format ledger claims as
`### KR-ID — Exact claim title [Status]`, using exactly `Open`,
`Conditional`, `Proved`, `Rejected`, or `Superseded`. A `Proved`
claim must state its real scope and may depend only on proved prerequisites.
Only explicit `requires` edges are hard dependencies; exploratory and
alternative routes need not enter a Goal root's closure.

Treat `KEY_RESULTS.md` as a theorem ledger, not a research narrative: keep an
open target statement-only, and keep proved, conditional, or rejected results
with their shortest locally checkable support. Put routes and chronology in the
log; never omit mathematical scope or proof steps merely for brevity. Apply the
status-specific rules in [memory-writing.md](references/memory-writing.md).

Exclusion from a Goal root's closure is a retrieval decision, not by itself a
reason to erase a still-valid proved theorem. Apply the proved-result
retention rule in [memory-writing.md](references/memory-writing.md): keep
reusable off-route theorems as unrooted Key Results and move only their long
proof detail outside the default retrieval package.

Report a proof or mark a claim `Proved` only when each load-bearing inference is
locally checkable. Show calculation inputs, intermediate equalities or
inequalities, boundary terms, and domain and sign conditions; `standard` or
`after simplification` is not a step. Compress only algebra fixed by adjacent
displayed lines. Prefer multiline display math for long calculations, with
breaks at mathematically meaningful transformations. Put long load-bearing
derivations in registered evidence and link the exact relevant section from the
concise claim; use the log for reusable exploration and route diagnostics.

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

After a context loss, task switch, or explicit restart, run `resume` first.
It returns only the exact restart section, compact Goal-root summaries, and
titles and statuses of claims referenced by the restart section. If it refuses
because a memory bound or reference check fails, run `check --memory` and fix
that stated defect; do not bypass the refusal by reading whole memory files.

Inspect file size without loading the body when a memory file may be large. If
`KEY_RESULTS.md` or `RESEARCH_LOG.md` exceeds 2,000 lines or 200 KiB, never
print or read the whole file into model context merely to recover state or
locate one result.

- Use `summary TARGET` for a compact closure view and `show CLAIM` for one
  bounded exact claim. If it is too large, use `show CLAIM --range START:END`;
  use `--full` only after deciding the entire section is required.
- Use `log-find QUERY` to retrieve matching headings and line metadata, then
  `log-show --line N` or `log-show --heading TEXT`. Use `--range START:END`
  for an oversized section.
- `order`, `impact`, `find`, and `log-find` have bounded default output.
  Increase `--limit` only for a stated need.
- Do not migrate, renumber, summarize, or index historical entries merely
  because a file is large. Retrieval pruning never changes the source record.

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
