# Research Workflow Skills

A small collection of Codex skills for long-running mathematical research,
from durable research memory to proof refactoring and paper drafting.
The workflow separates open-ended research, proof refinement, and manuscript production while preserving traceability between stages.

## Skills

| Skill | Purpose |
| --- | --- |
| `research-loop` | Pursue an active research goal while keeping minimal file-backed memory. |
| `literature-download` | Retrieve a small, authorized set of academic PDFs through legitimate access routes. |
| `proof-refactor` | Turn a validated proof closure into a compact, locally checkable proof view. |
| `proof-to-paper` | Convert a completed proof corpus or handoff into synchronized LaTeX manuscripts. |

Each skill is self-contained under [`skills/`](skills/). Start with
[`skills/research-loop/SKILL.md`](skills/research-loop/SKILL.md) for the overall
workflow.

## Install locally

Copy only the skills you want into a project-local `.agents/skills` directory:

```bash
mkdir -p .agents/skills
cp -R skills/research-loop .agents/skills/
```

Or copy them into your personal Codex skills directory to make them available
across projects.

## Initialize research memory

From any research project:

```bash
python3 /path/to/research-loop/scripts/research_graph.py \
  --root /path/to/research-project init
```

The command creates only `KEY_RESULTS.md`, `KEY_RESULTS.graph.json`, and
`RESEARCH_LOG.md`. It refuses to overwrite any existing file. Add `--dry-run`
to preview the paths.

## Test

The repository currently uses only the Python standard library:

```bash
python3 -m unittest discover -s skills/research-loop/tests -v
python3 -m unittest discover -s skills/proof-refactor/tests -v
```

The tests create temporary examples at runtime, so the repository does not
need a committed fixture directory.

## Trust boundary

The validators check the structure and internal consistency of declared
research memory: claim identifiers, dependency cycles, evidence paths, status
rules, and review-digest freshness. They do **not** prove mathematical claims,
judge whether cited sources are correct, or establish that an external program
is safe. A human or trusted research process must review the actual arguments,
source hypotheses, and reproduction commands before marking a claim `Proved`
or recording a root digest.

## Status

Experimental. Interfaces and file formats may change while the workflow is
tested on real research projects.
