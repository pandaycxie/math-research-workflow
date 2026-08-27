from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "research_graph.py"


class ResearchGraphCLITest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_ledger(self, text: str) -> None:
        (self.root / "KEY_RESULTS.md").write_text(text, encoding="utf-8")

    def write_graph(self, graph: dict[str, Any]) -> None:
        (self.root / "KEY_RESULTS.graph.json").write_text(
            json.dumps(graph, indent=2) + "\n", encoding="utf-8"
        )

    def run_command(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def run_json(
        self, *arguments: str
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        completed = self.run_command(*arguments)
        return completed, json.loads(completed.stdout)

    def make_basic_fixture(
        self, *, schema_version: int = 3, root_status: str = "Proved"
    ) -> dict[str, Any]:
        self.write_ledger(
            """# Fixture

### KR-001 — Upstream lemma [Proved]

The upstream statement is exact.

### KR-002 — Root theorem [{root_status}]

The root uses KR-001.
""".format(root_status=root_status)
        )
        (self.root / "evidence.txt").write_text("verified witness\n", encoding="utf-8")
        graph = {
            "schema_version": schema_version,
            "ledger": "KEY_RESULTS.md",
            "roots": ["KR-002"],
            "requires": {"KR-001": [], "KR-002": ["KR-001"]},
            "evidence": {"KR-002": ["evidence.txt"]},
            "root_digests": {},
        }
        if schema_version == 2:
            graph.pop("evidence")
            graph.pop("root_digests")
        self.write_graph(graph)
        return graph

    def stamp_root(self, graph: dict[str, Any]) -> str:
        completed, payload = self.run_json("check", "--strict")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        digest = payload["current_root_digests"]["KR-002"]
        graph["root_digests"] = {"KR-002": digest}
        self.write_graph(graph)
        return digest

    def test_init_creates_minimal_memory_without_overwriting(self) -> None:
        completed, payload = self.run_json("init")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["dry_run"])
        self.assertTrue((self.root / "KEY_RESULTS.md").is_file())
        self.assertTrue((self.root / "KEY_RESULTS.graph.json").is_file())
        self.assertTrue((self.root / "RESEARCH_LOG.md").is_file())

        graph = json.loads(
            (self.root / "KEY_RESULTS.graph.json").read_text(encoding="utf-8")
        )
        self.assertEqual(graph["schema_version"], 3)
        self.assertEqual(graph["roots"], [])
        self.assertEqual(graph["requires"], {})

        completed, payload = self.run_json("next-id")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["next_id"], "KR-001")

        completed = self.run_command("init")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("refusing to overwrite", completed.stderr)

    def test_init_dry_run_creates_nothing(self) -> None:
        completed, payload = self.run_json("init", "--dry-run")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["dry_run"])
        self.assertFalse((self.root / "KEY_RESULTS.md").exists())
        self.assertFalse((self.root / "KEY_RESULTS.graph.json").exists())
        self.assertFalse((self.root / "RESEARCH_LOG.md").exists())

    def test_duplicate_graph_keys_are_rejected(self) -> None:
        self.write_ledger(
            """# Fixture

### KR-001 — Root theorem [Proved]

The claim is proved.
"""
        )
        (self.root / "KEY_RESULTS.graph.json").write_text(
            '{"schema_version":3,"ledger":"KEY_RESULTS.md",'
            '"roots":["KR-001"],"roots":[],"requires":{"KR-001":[]},'
            '"evidence":{},"root_digests":{}}\n',
            encoding="utf-8",
        )

        completed = self.run_command("check")

        self.assertEqual(completed.returncode, 2)
        self.assertIn("duplicate JSON key: roots", completed.stderr)

    def test_next_id_uses_append_only_number_and_accepts_existing_mnemonic(self) -> None:
        self.write_ledger(
            """# Fixture

### KR-007-FULLRADIUSL3 — Full-radius L3 estimate [Proved]

The quadratic form has a positive lower bound.

### KR-010 — A later numerical claim [Open]

The claim remains open.
"""
        )
        self.write_graph(
            {
                "schema_version": 3,
                "ledger": "KEY_RESULTS.md",
                "roots": [],
                "requires": {
                    "KR-007-FULLRADIUSL3": [],
                    "KR-010": [],
                },
                "evidence": {},
                "root_digests": {},
            }
        )

        completed, payload = self.run_json("next-id")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["next_id"], "KR-011")

    def test_find_searches_ids_and_titles_with_bounded_output(self) -> None:
        self.write_ledger(
            """# Fixture

### KR-001 — Uniform coercivity for radial perturbations [Proved]

First result.

### KR-002 — Uniform coercivity for angular perturbations [Open]

Second result.

### KR-003 — Compactness of minimizing sequences [Conditional]

Third result.
"""
        )
        self.write_graph(
            {
                "schema_version": 3,
                "ledger": "KEY_RESULTS.md",
                "roots": [],
                "requires": {"KR-001": [], "KR-002": []},
                "evidence": {},
                "root_digests": {},
            }
        )

        completed, payload = self.run_json(
            "find", "UNIFORM coercivity", "--limit", "1"
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["total_matches"], 2)
        self.assertTrue(payload["truncated"])
        self.assertEqual(payload["matches"][0]["id"], "KR-001")

        completed, payload = self.run_json("find", "KR-003")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            payload["matches"][0]["title"], "Compactness of minimizing sequences"
        )

    def test_schema_v2_is_readable_but_cannot_complete(self) -> None:
        self.make_basic_fixture(schema_version=2)

        completed, payload = self.run_json("check")
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(any("schema_version 2" in item for item in payload["warnings"]))

        completed, payload = self.run_json("check", "--complete")
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(
            any("requires schema_version 3" in item for item in payload["errors"])
        )

        completed, payload = self.run_json("summary", "KR-002")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(payload["digest_state"], "unsupported")
        self.assertIsNone(payload["expected_digest"])
        self.assertFalse(payload["ready"])

    def test_cycle_is_rejected(self) -> None:
        self.write_ledger(
            """# Fixture

### KR-001 — First [Proved]

First.

### KR-002 — Second [Proved]

Second.
"""
        )
        self.write_graph(
            {
                "schema_version": 3,
                "ledger": "KEY_RESULTS.md",
                "roots": ["KR-002"],
                "requires": {"KR-001": ["KR-002"], "KR-002": ["KR-001"]},
                "evidence": {},
                "root_digests": {},
            }
        )

        completed, payload = self.run_json("check")
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(any("requires cycle" in item for item in payload["errors"]))

    def test_noncanonical_status_is_rejected(self) -> None:
        self.make_basic_fixture(root_status="Proved; sharp localization Open")

        completed, payload = self.run_json("check")
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(
            any("unsupported ledger status" in item for item in payload["errors"])
        )

    def test_strict_rejects_noncanonical_status_on_unindexed_claim(self) -> None:
        graph = self.make_basic_fixture()
        ledger = (self.root / "KEY_RESULTS.md").read_text(encoding="utf-8")
        self.write_ledger(
            ledger
            + """
### KR-003 — Mixed background [Proved; residual Open]

Background only.
"""
        )
        self.write_graph(graph)

        completed, payload = self.run_json("check")
        self.assertEqual(completed.returncode, 0)
        completed, payload = self.run_json("check", "--strict")
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(
            any("noncanonical status labels" in item for item in payload["errors"])
        )

    def test_missing_evidence_is_rejected_by_strict_check(self) -> None:
        graph = self.make_basic_fixture()
        graph["evidence"] = {"KR-002": ["missing.txt"]}
        self.write_graph(graph)

        completed, payload = self.run_json("check", "--strict")
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(any("missing.txt" in item for item in payload["errors"]))

    def test_digest_becomes_stale_after_upstream_change(self) -> None:
        graph = self.make_basic_fixture()
        self.stamp_root(graph)

        completed, payload = self.run_json("check", "--strict", "--complete")
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(payload["ok"])

        ledger = (self.root / "KEY_RESULTS.md").read_text(encoding="utf-8")
        self.write_ledger(ledger.replace("statement is exact", "scope is narrower"))
        completed, payload = self.run_json("check", "--strict", "--complete")
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(any("is stale" in item for item in payload["errors"]))

    def test_digest_includes_internal_level_three_headings(self) -> None:
        self.write_ledger(
            """# Fixture

### KR-001 — Root theorem [Proved]

Claim summary.

### Proof details

Load-bearing argument version A.
"""
        )
        graph = {
            "schema_version": 3,
            "ledger": "KEY_RESULTS.md",
            "roots": ["KR-001"],
            "requires": {"KR-001": []},
            "evidence": {},
            "root_digests": {},
        }
        self.write_graph(graph)

        completed, payload = self.run_json("check", "--strict")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        graph["root_digests"] = {
            "KR-001": payload["current_root_digests"]["KR-001"]
        }
        self.write_graph(graph)

        ledger = (self.root / "KEY_RESULTS.md").read_text(encoding="utf-8")
        self.write_ledger(
            ledger.replace(
                "Load-bearing argument version A.",
                "Load-bearing argument version B.",
            )
        )
        completed, payload = self.run_json("check", "--strict", "--complete")
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(any("is stale" in item for item in payload["errors"]))

    def test_digest_includes_content_after_heading_inside_code_fence(self) -> None:
        self.write_ledger(
            """# Fixture

### KR-001 — Root theorem [Proved]

```markdown
## Example heading, not a section boundary
```

Load-bearing argument version A.
"""
        )
        graph = {
            "schema_version": 3,
            "ledger": "KEY_RESULTS.md",
            "roots": ["KR-001"],
            "requires": {"KR-001": []},
            "evidence": {},
            "root_digests": {},
        }
        self.write_graph(graph)
        completed, payload = self.run_json("check", "--strict")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        graph["root_digests"] = {
            "KR-001": payload["current_root_digests"]["KR-001"]
        }
        self.write_graph(graph)

        ledger = (self.root / "KEY_RESULTS.md").read_text(encoding="utf-8")
        self.write_ledger(ledger.replace("version A", "version B"))
        completed, payload = self.run_json("check", "--strict", "--complete")
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(any("is stale" in item for item in payload["errors"]))

    def test_claim_heading_inside_code_fence_is_not_parsed(self) -> None:
        self.write_ledger(
            """# Fixture

### KR-001 — Real claim [Proved]

~~~markdown
### KR-999 — Example only [Open]
~~~

Real claim continuation.
"""
        )
        self.write_graph(
            {
                "schema_version": 3,
                "ledger": "KEY_RESULTS.md",
                "roots": ["KR-001"],
                "requires": {"KR-001": []},
                "evidence": {},
                "root_digests": {},
            }
        )

        completed, payload = self.run_json("check", "--strict")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(any("unindexed ledger claims" in item for item in payload["warnings"]))
        completed = self.run_command("show", "KR-001")
        self.assertIn("KR-999", completed.stdout)
        self.assertIn("Real claim continuation.", completed.stdout)
        completed = self.run_command("show", "KR-999")
        self.assertEqual(completed.returncode, 2)

    def test_summary_reports_fresh_ready_root(self) -> None:
        graph = self.make_basic_fixture()
        digest = self.stamp_root(graph)

        completed, payload = self.run_json("summary", "KR-002")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["configured_root"])
        self.assertEqual(payload["target_title"], "Root theorem")
        self.assertEqual(payload["closure_size"], 2)
        self.assertEqual(payload["status_counts"], {"Proved": 2})
        self.assertEqual(payload["unresolved"], [])
        self.assertEqual(payload["evidence_files"], 1)
        self.assertEqual(payload["digest_state"], "fresh")
        self.assertIsNone(payload["expected_digest"])
        self.assertTrue(payload["ready"])

        (self.root / "evidence.txt").write_text("changed witness\n", encoding="utf-8")
        completed, payload = self.run_json("summary", "KR-002")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["digest_state"], "stale")
        self.assertNotEqual(payload["expected_digest"], digest)
        self.assertFalse(payload["ready"])

    def test_summary_reports_unresolved_root(self) -> None:
        self.make_basic_fixture(root_status="Open")

        completed, payload = self.run_json("summary", "KR-002")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["status_counts"], {"Open": 1, "Proved": 1})
        self.assertEqual(payload["unresolved"], [{"id": "KR-002", "status": "Open"}])
        self.assertEqual(payload["unresolved_titles"], {"KR-002": "Root theorem"})
        self.assertEqual(payload["digest_state"], "missing")
        self.assertRegex(payload["expected_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertFalse(payload["ready"])

    def test_summary_allows_an_indexed_nonroot(self) -> None:
        graph = self.make_basic_fixture()
        graph["evidence"]["KR-001"] = ["missing-upstream.txt"]
        self.write_graph(graph)

        completed, payload = self.run_json("summary", "KR-001")
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertFalse(payload["configured_root"])
        self.assertEqual(payload["closure_size"], 1)
        self.assertEqual(payload["digest_state"], "untracked")
        self.assertTrue(payload["evidence_errors"])
        self.assertFalse(payload["ready"])

    def test_summary_checks_only_its_closure_evidence(self) -> None:
        graph = self.make_basic_fixture()
        ledger = (self.root / "KEY_RESULTS.md").read_text(encoding="utf-8")
        self.write_ledger(
            ledger
            + """
### KR-003 — Unrelated result [Proved]

Unrelated.
"""
        )
        graph["requires"]["KR-003"] = []
        self.stamp_root(graph)
        graph["evidence"]["KR-003"] = ["outside-missing.txt"]
        self.write_graph(graph)

        completed, payload = self.run_json("summary", "KR-002")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["digest_state"], "fresh")
        self.assertIsNone(payload["expected_digest"])

        graph["evidence"]["KR-001"] = ["inside-missing.txt"]
        self.write_graph(graph)
        completed, payload = self.run_json("summary", "KR-002")
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(payload["digest_state"], "unavailable")
        self.assertTrue(
            any("inside-missing.txt" in item for item in payload["evidence_errors"])
        )

    def test_strict_warnings_are_compact_unless_verbose(self) -> None:
        self.write_ledger(
            """# Fixture

### KR-001 — Base [Proved]

Base.

### KR-002 — Middle [Proved]

Middle.

### KR-003 — Root [Proved]

Root.

### KR-004 — Background [Open]

Background.
"""
        )
        self.write_graph(
            {
                "schema_version": 3,
                "ledger": "KEY_RESULTS.md",
                "roots": ["KR-003"],
                "requires": {
                    "KR-001": [],
                    "KR-002": ["KR-001"],
                    "KR-003": ["KR-001", "KR-002"],
                },
                "evidence": {},
                "root_digests": {},
            }
        )

        completed, payload = self.run_json("check", "--strict")
        self.assertEqual(completed.returncode, 0)
        warnings = "\n".join(payload["warnings"])
        self.assertIn("unindexed ledger claims: 1", warnings)
        self.assertIn("transitively implied edges: 1", warnings)
        self.assertNotIn("KR-004", warnings)
        self.assertNotIn("KR-003->KR-001", warnings)

        completed, payload = self.run_json("check", "--strict", "--verbose")
        self.assertEqual(completed.returncode, 0)
        warnings = "\n".join(payload["warnings"])
        self.assertIn("KR-004", warnings)
        self.assertIn("KR-003->KR-001", warnings)

    def test_verbose_requires_strict(self) -> None:
        self.make_basic_fixture()

        completed = self.run_command("check", "--verbose")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("--verbose requires --strict", completed.stderr)

    def test_existing_inspection_commands_still_work(self) -> None:
        self.make_basic_fixture()

        completed = self.run_command("show", "KR-001")
        self.assertEqual(completed.returncode, 0)
        self.assertIn("### KR-001 — Upstream lemma [Proved]", completed.stdout)
        self.assertIn("The upstream statement is exact.", completed.stdout)
        self.assertNotIn("### KR-002", completed.stdout)

        completed, payload = self.run_json("order", "KR-002")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(payload["order"], ["KR-001", "KR-002"])
        self.assertEqual(
            payload["titles"],
            {"KR-001": "Upstream lemma", "KR-002": "Root theorem"},
        )

        completed, payload = self.run_json("impact", "KR-001")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(payload["direct"], ["KR-002"])
        self.assertEqual(payload["transitive"], ["KR-002"])
        self.assertEqual(payload["claim_title"], "Upstream lemma")
        self.assertEqual(payload["titles"], {"KR-002": "Root theorem"})

        completed = self.run_command("dot", "--target", "KR-002")
        self.assertEqual(completed.returncode, 0)
        self.assertIn('"KR-001" -> "KR-002";', completed.stdout)

    def test_show_refuses_oversized_section_without_explicit_full(self) -> None:
        body = "\n".join(f"Line {index}." for index in range(401))
        self.write_ledger(
            f"# Fixture\n\n### KR-001 — Long claim [Proved]\n\n{body}\n"
        )
        self.write_graph(
            {
                "schema_version": 3,
                "ledger": "KEY_RESULTS.md",
                "roots": ["KR-001"],
                "requires": {"KR-001": []},
                "evidence": {},
                "root_digests": {},
            }
        )

        completed = self.run_command("show", "KR-001")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("too large for bounded show", completed.stderr)
        self.assertEqual(completed.stdout, "")

        completed, payload = self.run_json("check", "--readability")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["readability"]["oversized_sections"], 1)
        self.assertTrue(
            any(
                "oversized ledger claim sections: 1" in item
                for item in payload["warnings"]
            )
        )

        completed = self.run_command("show", "KR-001", "--full")
        self.assertEqual(completed.returncode, 0)
        self.assertIn("Line 400.", completed.stdout)

    def test_readability_warning_does_not_block_completion(self) -> None:
        graph = self.make_basic_fixture()
        self.stamp_root(graph)
        ledger = (self.root / "KEY_RESULTS.md").read_text(encoding="utf-8")
        self.write_ledger(
            ledger
            + """
### KR-003-MEMO — Background note without a body [Open]
"""
        )

        completed, payload = self.run_json("check", "--complete", "--readability")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["readability"]["empty_sections"], 1)
        self.assertEqual(payload["readability"]["mnemonic_ids"], 1)
        self.assertTrue(
            any(
                "empty ledger claim sections: 1" in item
                for item in payload["warnings"]
            )
        )


if __name__ == "__main__":
    unittest.main()
