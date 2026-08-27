from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "paper_artifacts.py"


class PaperArtifactsCLITest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_command(
        self, *arguments: str
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return completed, json.loads(completed.stdout)

    def initialize(self) -> Path:
        completed, payload = self.run_command("init", "--root", str(self.root))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(payload["ok"])
        return Path(payload["manuscript"])

    def complete_artifact(self, manuscript: Path) -> None:
        (manuscript / "main.tex").write_text("manuscript\n", encoding="utf-8")
        (manuscript / "references.bib").write_text("@book{x}\n", encoding="utf-8")
        (manuscript / "output" / "pdf" / "main.pdf").write_bytes(b"%PDF-test\n")

    def test_init_creates_minimal_nonconflicting_layout(self) -> None:
        first = self.initialize()
        second = self.initialize()

        self.assertNotEqual(first, second)
        self.assertTrue(first.name.startswith("manuscript_"))
        self.assertEqual(second.name, first.name + "-2")
        self.assertTrue((first / "references.bib").is_file())
        self.assertTrue((first / "output" / "pdf").is_dir())
        self.assertFalse((first / "main.tex").exists())
        self.assertFalse((first / "artifact-manifest.json").exists())

    def test_freeze_then_check_succeeds(self) -> None:
        manuscript = self.initialize()
        self.complete_artifact(manuscript)

        frozen, freeze_payload = self.run_command(
            "freeze", "--manuscript", str(manuscript)
        )
        checked, check_payload = self.run_command(
            "check", "--manuscript", str(manuscript)
        )

        self.assertEqual(frozen.returncode, 0, frozen.stderr)
        self.assertTrue(freeze_payload["ok"])
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertTrue(check_payload["ok"])
        manifest = json.loads(
            (manuscript / "artifact-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(manifest["files"]),
            {"main.tex", "references.bib", "output/pdf/main.pdf"},
        )

    def test_check_detects_drift(self) -> None:
        manuscript = self.initialize()
        self.complete_artifact(manuscript)
        frozen, _ = self.run_command("freeze", "--manuscript", str(manuscript))
        self.assertEqual(frozen.returncode, 0, frozen.stderr)

        (manuscript / "main.tex").write_text("changed\n", encoding="utf-8")
        checked, payload = self.run_command("check", "--manuscript", str(manuscript))

        self.assertEqual(checked.returncode, 1)
        self.assertTrue(any("digest mismatch for main.tex" in error for error in payload["errors"]))

    def test_refreeze_requires_explicit_replace(self) -> None:
        manuscript = self.initialize()
        self.complete_artifact(manuscript)
        frozen, _ = self.run_command("freeze", "--manuscript", str(manuscript))
        self.assertEqual(frozen.returncode, 0, frozen.stderr)
        (manuscript / "main.tex").write_text("reviewed revision\n", encoding="utf-8")

        refused, payload = self.run_command("freeze", "--manuscript", str(manuscript))
        replaced, replacement = self.run_command(
            "freeze", "--manuscript", str(manuscript), "--replace"
        )

        self.assertEqual(refused.returncode, 1)
        self.assertTrue(any("--replace" in error for error in payload["errors"]))
        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        self.assertTrue(replacement["ok"])

    def test_missing_file_and_manifest_escape_are_rejected(self) -> None:
        manuscript = self.initialize()
        missing, payload = self.run_command("freeze", "--manuscript", str(manuscript))
        self.assertEqual(missing.returncode, 1)
        self.assertTrue(any("main.tex" in error for error in payload["errors"]))

        self.complete_artifact(manuscript)
        with tempfile.TemporaryDirectory() as external_directory:
            external = Path(external_directory) / "manifest.json"
            external.write_text("{}\n", encoding="utf-8")
            link = manuscript / "artifact-manifest.json"
            try:
                link.symlink_to(external)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")
            frozen, payload = self.run_command(
                "freeze", "--manuscript", str(manuscript), "--replace"
            )
            self.assertEqual(frozen.returncode, 1)
            self.assertTrue(any("manifest escapes" in item for item in payload["errors"]))


if __name__ == "__main__":
    unittest.main()
