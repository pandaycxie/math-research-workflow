from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_handoff.py"
DIGEST_ONE = "sha256:" + "1" * 64
DIGEST_TWO = "sha256:" + "2" * 64


class ValidateHandoffCLITest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.output = self.root / "proof_refactor_test"
        self.output.mkdir()
        self.graph = self.root / "KEY_RESULTS.graph.json"
        self.proof = self.output / "proof.md"
        self.proof_graph = self.output / "proof.graph.json"
        self.handoff = self.output / "handoff.json"
        self.proof.write_text(
            "# Refactored proof\n\n"
            "### PF-001 — Source theorems\n\n"
            "Both source theorems hold.\n",
            encoding="utf-8",
        )
        self.write_graph(self.default_graph())
        self.write_proof_graph(self.default_proof_graph())
        self.write_handoff(self.default_handoff())

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def default_graph(self) -> dict[str, Any]:
        return {
            "roots": ["KR-001", "KR-002"],
            "root_digests": {"KR-001": DIGEST_ONE, "KR-002": DIGEST_TWO},
            "requires": {"KR-001": [], "KR-002": []},
        }

    def default_proof_graph(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "proof-refactor-dag",
            "roots": ["PF-001"],
            "nodes": {
                "PF-001": {
                    "title": "Source theorems",
                    "statement": "Both source theorems hold.",
                    "requires": [],
                    "sources": ["KR-001", "KR-002"],
                }
            },
        }

    def proof_digest(self, path: Path | None = None) -> str:
        proof = self.proof if path is None else path
        return "sha256:" + hashlib.sha256(proof.read_bytes()).hexdigest()

    def proof_graph_digest(self, path: Path | None = None) -> str:
        graph = self.proof_graph if path is None else path
        return "sha256:" + hashlib.sha256(graph.read_bytes()).hexdigest()

    def default_handoff(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "proof-refactor-handoff",
            "status": "validated",
            "source": {
                "graph": "KEY_RESULTS.graph.json",
                "roots": ["KR-001", "KR-002"],
                "root_digests": {"KR-001": DIGEST_ONE, "KR-002": DIGEST_TWO},
            },
            "proof": "proof.md",
            "proof_sha256": self.proof_digest(),
        }

    def default_v2_handoff(self) -> dict[str, Any]:
        handoff = self.default_handoff()
        handoff["schema_version"] = 2
        handoff["proof_graph"] = "proof.graph.json"
        handoff["proof_graph_sha256"] = self.proof_graph_digest()
        return handoff

    def write_graph(self, value: Any) -> None:
        self.graph.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def write_handoff(self, value: Any, path: Path | None = None) -> None:
        target = self.handoff if path is None else path
        target.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def write_proof_graph(self, value: Any) -> None:
        self.proof_graph.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def run_command(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def run_validator(
        self, handoff: Path | None = None
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        target = self.handoff if handoff is None else handoff
        completed = self.run_command("--root", str(self.root), str(target))
        return completed, json.loads(completed.stdout)

    def run_creator(self) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        completed = self.run_command(
            "--root",
            str(self.root),
            "--create",
            "--proof",
            self.proof.name,
            str(self.handoff),
        )
        return completed, json.loads(completed.stdout)

    def assert_invalid(self, substring: str) -> None:
        completed, payload = self.run_validator()
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertFalse(payload["ok"])
        self.assertTrue(any(substring in error for error in payload["errors"]), payload)

    def assert_creator_invalid(self, substring: str) -> None:
        if self.handoff.exists():
            self.handoff.unlink()
        completed, payload = self.run_creator()
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertFalse(payload["ok"])
        self.assertTrue(any(substring in error for error in payload["errors"]), payload)
        self.assertFalse(self.handoff.exists())

    def test_minimal_valid_handoff(self) -> None:
        completed, payload = self.run_validator()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["legacy"])
        self.assertEqual(payload["roots"], ["KR-001", "KR-002"])
        self.assertEqual(payload["proof_sha256"], self.proof_digest())

    def test_v2_handoff_validates_dag_and_reports_mapping(self) -> None:
        self.write_handoff(self.default_v2_handoff())
        completed, payload = self.run_validator()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["legacy"])
        self.assertEqual(payload["proof_nodes"], 1)
        self.assertEqual(payload["mapped_source_claims"], ["KR-001", "KR-002"])
        self.assertEqual(payload["unmapped_source_claims"], [])

    def test_create_builds_and_validates_handoff(self) -> None:
        self.handoff.unlink()
        completed, payload = self.run_creator()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["created"])
        manifest = json.loads(self.handoff.read_text(encoding="utf-8"))
        self.assertEqual(manifest, self.default_v2_handoff())

    def test_create_refuses_to_overwrite_handoff(self) -> None:
        completed, payload = self.run_creator()
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(any("already exists" in error for error in payload["errors"]))

    def test_create_rejects_invalid_graph_binding(self) -> None:
        self.handoff.unlink()
        graph = self.default_graph()
        graph["root_digests"].pop("KR-002")
        self.write_graph(graph)

        completed, payload = self.run_creator()
        self.assertEqual(completed.returncode, 1)
        self.assertTrue(
            any("keys must equal roots" in error for error in payload["errors"])
        )
        self.assertFalse(self.handoff.exists())

    def test_init_creates_minimal_nonconflicting_layout(self) -> None:
        first = self.run_command("--root", str(self.root), "--init")
        first_payload = json.loads(first.stdout)
        second = self.run_command("--root", str(self.root), "--init")
        second_payload = json.loads(second.stdout)

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        first_output = Path(first_payload["output"])
        second_output = Path(second_payload["output"])
        self.assertEqual(second_output.name, first_output.name + "-2")
        self.assertTrue((first_output / "proof.md").is_file())
        initialized_graph = first_output / "proof.graph.json"
        self.assertTrue(initialized_graph.is_file())
        self.assertEqual(
            json.loads(initialized_graph.read_text(encoding="utf-8"))["nodes"], {}
        )
        self.assertFalse((first_output / "handoff.json").exists())

    def test_graph_root_order_is_not_semantic(self) -> None:
        graph = self.default_graph()
        graph["roots"].reverse()
        self.write_graph(graph)

        completed, payload = self.run_validator()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["ok"])

    def test_duplicate_node_titles_are_allowed(self) -> None:
        proof_graph = self.default_proof_graph()
        proof_graph["nodes"]["PF-001"]["requires"] = ["PF-002"]
        proof_graph["nodes"]["PF-002"] = {
            "title": "Source theorems",
            "statement": "The first source theorem holds.",
            "requires": [],
            "sources": ["KR-001"],
        }
        self.write_proof_graph(proof_graph)
        self.proof.write_text(
            "# Refactored proof\n\n"
            "### PF-001 — Source theorems\n\n"
            "Both source theorems hold.\n\n"
            "### PF-002 — Source theorems\n\n"
            "The first source theorem holds.\n",
            encoding="utf-8",
        )

        self.handoff.unlink()
        completed, payload = self.run_creator()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["proof_nodes"], 2)

    def test_proof_graph_rejects_cycle_orphan_and_unknown_source(self) -> None:
        proof_graph = self.default_proof_graph()
        proof_graph["nodes"]["PF-001"]["requires"] = ["PF-001"]
        self.write_proof_graph(proof_graph)
        self.assert_creator_invalid("requires itself")

        proof_graph = self.default_proof_graph()
        proof_graph["nodes"]["PF-002"] = {
            "title": "Unused result",
            "statement": "An unused result holds.",
            "requires": [],
            "sources": ["KR-001"],
        }
        self.write_proof_graph(proof_graph)
        self.proof.write_text(
            self.proof.read_text(encoding="utf-8")
            + "\n### PF-002 — Unused result\n\nAn unused result holds.\n",
            encoding="utf-8",
        )
        self.assert_creator_invalid("outside every root closure")

        self.write_proof_graph(self.default_proof_graph())
        proof_graph = self.default_proof_graph()
        proof_graph["nodes"]["PF-001"]["sources"] = ["KR-001", "KR-999"]
        self.write_proof_graph(proof_graph)
        self.proof.write_text(
            "# Refactored proof\n\n"
            "### PF-001 — Source theorems\n\n"
            "Both source theorems hold.\n",
            encoding="utf-8",
        )
        self.assert_creator_invalid("outside canonical root closure")

    def test_proof_section_must_start_with_exact_statement(self) -> None:
        proof_graph = self.default_proof_graph()
        proof_graph["nodes"]["PF-001"]["statement"] = "A different statement."
        self.write_proof_graph(proof_graph)
        self.assert_creator_invalid("must begin with its exact statement")

    def test_proof_graph_must_account_for_complete_canonical_closure(self) -> None:
        graph = self.default_graph()
        graph["requires"]["KR-001"] = ["KR-003"]
        graph["requires"]["KR-003"] = []
        self.write_graph(graph)

        self.assert_creator_invalid(
            "does not account for canonical closure claims: KR-003"
        )

    def test_changed_proof_graph_is_rejected(self) -> None:
        self.write_handoff(self.default_v2_handoff())
        proof_graph = self.default_proof_graph()
        proof_graph["nodes"]["PF-001"]["title"] = "Changed title"
        self.write_proof_graph(proof_graph)
        self.assert_invalid("does not match proof graph bytes")

    def test_noncanonical_graph_copy_is_rejected(self) -> None:
        archived = self.root / "archived.graph.json"
        archived.write_text(self.graph.read_text(encoding="utf-8"), encoding="utf-8")
        manifest = self.default_handoff()
        manifest["source"]["graph"] = archived.name
        self.write_handoff(manifest)

        self.assert_invalid("source.graph must be KEY_RESULTS.graph.json")

    def test_changed_proof_is_rejected(self) -> None:
        self.proof.write_text("# Altered proof\n", encoding="utf-8")
        self.assert_invalid("does not match proof bytes")

    def test_schema_constants_and_exact_keys(self) -> None:
        variants: list[tuple[str, dict[str, Any], str]] = []
        for field, value in (
            ("schema_version", 3),
            ("schema_version", True),
            ("kind", "other"),
            ("status", "draft"),
        ):
            manifest = self.default_handoff()
            manifest[field] = value
            variants.append((f"{field}={value!r}", manifest, field))

        missing = self.default_handoff()
        missing.pop("proof")
        variants.append(("missing top-level", missing, "missing keys"))
        unknown = self.default_handoff()
        unknown["claims"] = []
        variants.append(("unknown top-level", unknown, "unknown keys"))
        missing_source = self.default_handoff()
        missing_source["source"].pop("graph")
        variants.append(("missing source", missing_source, "source is missing keys"))
        unknown_source = self.default_handoff()
        unknown_source["source"]["ledger"] = "KEY_RESULTS.md"
        variants.append(("unknown source", unknown_source, "source has unknown keys"))

        for label, manifest, expected in variants:
            with self.subTest(label=label):
                self.write_handoff(manifest)
                self.assert_invalid(expected)

    def test_graph_root_drift_is_rejected(self) -> None:
        for roots in (
            ["KR-001"],
            ["KR-001", "KR-002", "KR-003"],
            ["KR-001", "KR-003"],
        ):
            with self.subTest(roots=roots):
                graph = self.default_graph()
                graph["roots"] = roots
                self.write_graph(graph)
                self.assert_invalid("roots do not match")

    def test_digest_drift_and_key_mismatch_are_rejected(self) -> None:
        graph = self.default_graph()
        graph["root_digests"]["KR-001"] = "sha256:" + "3" * 64
        self.write_graph(graph)
        self.assert_invalid("root_digests do not match")

        self.write_graph(self.default_graph())
        manifest = self.default_handoff()
        manifest["source"]["root_digests"].pop("KR-002")
        self.write_handoff(manifest)
        self.assert_invalid("keys must equal source.roots")

    def test_path_escape_and_absolute_paths_are_rejected(self) -> None:
        outside_proof = self.root / "outside.md"
        outside_proof.write_text("outside\n", encoding="utf-8")
        variants: list[tuple[str, dict[str, Any], str]] = []

        relative_proof = self.default_handoff()
        relative_proof["proof"] = "../outside.md"
        variants.append(("proof escape", relative_proof, "proof escapes"))

        absolute_proof = self.default_handoff()
        absolute_proof["proof"] = str(self.proof)
        variants.append(("absolute proof", absolute_proof, "proof must be relative"))

        graph_escape = self.default_handoff()
        graph_escape["source"]["graph"] = "../outside.json"
        variants.append(
            (
                "graph escape",
                graph_escape,
                "source.graph must be KEY_RESULTS.graph.json",
            )
        )

        absolute_graph = self.default_handoff()
        absolute_graph["source"]["graph"] = str(self.graph)
        variants.append(
            (
                "absolute graph",
                absolute_graph,
                "source.graph must be KEY_RESULTS.graph.json",
            )
        )

        for label, manifest, expected in variants:
            with self.subTest(label=label):
                self.write_handoff(manifest)
                self.assert_invalid(expected)

        with tempfile.TemporaryDirectory() as external_directory:
            external_handoff = Path(external_directory) / "handoff.json"
            self.write_handoff(self.default_handoff(), external_handoff)
            completed, payload = self.run_validator(external_handoff)
            self.assertEqual(completed.returncode, 1)
            self.assertTrue(
                any("escapes research root" in item for item in payload["errors"])
            )

    def test_symlinks_cannot_escape_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as external_directory:
            external = Path(external_directory)
            external_proof = external / "proof.md"
            external_proof.write_text("external proof\n", encoding="utf-8")
            proof_link = self.output / "linked-proof.md"
            try:
                proof_link.symlink_to(external_proof)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")

            manifest = self.default_handoff()
            manifest["proof"] = proof_link.name
            manifest["proof_sha256"] = self.proof_digest(external_proof)
            self.write_handoff(manifest)
            self.assert_invalid("proof escapes")

            external_graph = external / "graph.json"
            external_graph.write_text(
                json.dumps(self.default_graph()) + "\n", encoding="utf-8"
            )
            self.graph.unlink()
            self.graph.symlink_to(external_graph)
            self.write_handoff(self.default_handoff())
            self.assert_invalid("source.graph escapes")

    def test_missing_files_and_bad_digest_are_rejected(self) -> None:
        manifest = self.default_handoff()
        manifest["proof"] = "missing.md"
        self.write_handoff(manifest)
        self.assert_invalid("proof is not a readable file")

        self.graph.unlink()
        self.write_handoff(self.default_handoff())
        self.assert_invalid("source.graph is not a readable file")

        self.write_graph(self.default_graph())
        manifest = self.default_handoff()
        manifest["proof_sha256"] = "ABC"
        self.write_handoff(manifest)
        self.assert_invalid("proof_sha256")

    def test_malformed_duplicate_and_nonobject_json_are_rejected(self) -> None:
        for label, text in (
            ("malformed", "{"),
            (
                "duplicate",
                '{"schema_version":1,"schema_version":1,"kind":"x"}',
            ),
            ("nonobject", "[]"),
        ):
            with self.subTest(label=label):
                self.handoff.write_text(text, encoding="utf-8")
                completed, payload = self.run_validator()
                self.assertEqual(completed.returncode, 1)
                self.assertFalse(payload["ok"])

        self.write_handoff(self.default_handoff())
        self.graph.write_text('{"roots":[],"roots":[]}', encoding="utf-8")
        self.assert_invalid("cannot read source graph")

    def test_usage_errors_return_two(self) -> None:
        completed = self.run_command()
        self.assertEqual(completed.returncode, 2)
        completed = self.run_command("--root", str(self.root))
        self.assertEqual(completed.returncode, 2)

    def test_research_closure_semantics_are_deliberately_delegated(self) -> None:
        graph = self.default_graph()
        graph.update(
            {
                "schema_version": 999,
                "ledger": "missing.md",
                "requires": {"KR-001": ["MISSING"]},
                "evidence": {"KR-001": ["missing.pdf"]},
            }
        )
        self.write_graph(graph)

        completed, payload = self.run_validator()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
