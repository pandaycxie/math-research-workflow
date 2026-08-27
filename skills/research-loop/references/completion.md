# Completion and readiness

Read this reference only when the Goal appears satisfied or the user asks for
a readiness assessment.

## Closure review

Run the bundled helper with both locations explicit; do not assume that the
research project contains a copy of the skill's `scripts` directory:

```bash
python3 <skill-directory>/scripts/research_graph.py --root <research-root> check --strict --complete
```

Completion requires schema version 3, at least one Goal root, a fully proved
hard-dependency closure, readable listed evidence, and a current reviewed root
digest.

When a digest is missing or stale:

1. inspect the dependency-first `order ROOT` closure;
2. verify every claim's exact scope and hard prerequisites;
3. re-run or independently verify every load-bearing computational
   reproduction command;
4. confirm that external theorem hypotheses and trust boundaries are recorded;
5. copy the expected digest into `root_digests` only after that review;
6. rerun `check --strict --complete`.

If the check fails, continue research. Report `NOT READY` only when the user
asks for readiness or the research is genuinely blocked.

## Paperization Readiness Report

After the completion check passes, issue a `READY`
**Paperization Readiness Report** containing:

- the Goal and root claim IDs;
- the main proved result and exact scope;
- dependency-closure size and status, plus the checking command;
- load-bearing evidence paths, external sources, and reproduction commands;
- excluded open, conditional, rejected, or superseded claims;
- remaining mathematical, empirical, computational, and expository risks;
- the user's next decision: proof refactoring, direct paperization, continued
  research, or stopping.

Generate the report from canonical files and targeted log entries. Do not
create a separate handoff artifact unless requested.

A `READY` report authorizes neither `$proof-refactor` nor
`$proof-to-paper`. Do not create their artifact directories, conduct a
manuscript-oriented literature review, or draft paper text until the user
explicitly approves the corresponding work.
