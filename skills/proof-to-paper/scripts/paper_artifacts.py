#!/usr/bin/env python3
"""Initialize, freeze, and verify a proof-to-paper manuscript artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
KIND = "proof-to-paper-artifact-manifest"
MANIFEST_NAME = "artifact-manifest.json"
REQUIRED_FILES = ("main.tex", "references.bib", "output/pdf/main.pdf")
TOP_LEVEL_KEYS = {"schema_version", "kind", "files"}
SHA256_DIGEST = re.compile(r"sha256:[0-9a-f]{64}$")


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def is_within(path: Path, boundary: Path) -> bool:
    try:
        path.relative_to(boundary)
    except ValueError:
        return False
    return True


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def resolve_manuscript(value: Path) -> Path:
    return value.expanduser().resolve()


def required_paths(manuscript: Path) -> tuple[dict[str, Path], list[str]]:
    paths: dict[str, Path] = {}
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        path = (manuscript / relative).resolve()
        if not is_within(path, manuscript):
            errors.append(f"required file escapes manuscript directory: {relative}")
        elif not path.is_file():
            errors.append(f"required file is missing: {relative}")
        else:
            try:
                with path.open("rb") as handle:
                    handle.read(1)
            except OSError as error:
                errors.append(f"required file is not readable: {relative} ({error})")
            else:
                paths[relative] = path
    return paths, errors


def initialize(root: Path) -> int:
    root = root.expanduser().resolve()
    if not root.is_dir():
        print_json({"ok": False, "errors": [f"root is not a directory: {root}"]})
        return 1

    stem = f"manuscript_{date.today():%Y%m%d}"
    manuscript = root / stem
    suffix = 2
    while manuscript.exists():
        manuscript = root / f"{stem}-{suffix}"
        suffix += 1

    (manuscript / "output" / "pdf").mkdir(parents=True)
    bibliography = manuscript / "references.bib"
    bibliography.touch()
    print_json(
        {
            "ok": True,
            "manuscript": str(manuscript),
            "created": ["references.bib", "output/pdf/"],
        }
    )
    return 0


def make_manifest(paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "files": {relative: file_sha256(paths[relative]) for relative in REQUIRED_FILES},
    }


def freeze(manuscript: Path, replace: bool) -> int:
    manuscript = resolve_manuscript(manuscript)
    if not manuscript.is_dir():
        print_json(
            {"ok": False, "errors": [f"manuscript is not a directory: {manuscript}"]}
        )
        return 1
    paths, errors = required_paths(manuscript)
    if errors:
        print_json({"ok": False, "errors": errors})
        return 1

    manifest = make_manifest(paths)
    manifest_path = manuscript / MANIFEST_NAME
    if manifest_path.exists() and not is_within(manifest_path.resolve(), manuscript):
        print_json({"ok": False, "errors": ["manifest escapes manuscript directory"]})
        return 1
    encoded = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if manifest_path.exists() and not replace:
        try:
            current = manifest_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            print_json({"ok": False, "errors": [f"cannot read manifest: {error}"]})
            return 1
        if current != encoded:
            print_json(
                {
                    "ok": False,
                    "errors": [
                        "artifact-manifest.json already exists with different "
                        "content; rerun freeze with --replace after review"
                    ],
                }
            )
            return 1
    try:
        manifest_path.write_text(encoded, encoding="utf-8")
    except OSError as error:
        print_json({"ok": False, "errors": [f"cannot write manifest: {error}"]})
        return 1

    print_json({"ok": True, "manuscript": str(manuscript), "manifest": manifest})
    return 0


def check(manuscript: Path) -> int:
    manuscript = resolve_manuscript(manuscript)
    if not manuscript.is_dir():
        print_json(
            {"ok": False, "errors": [f"manuscript is not a directory: {manuscript}"]}
        )
        return 1
    paths, errors = required_paths(manuscript)
    manifest_path = manuscript / MANIFEST_NAME
    if manifest_path.exists() and not is_within(manifest_path.resolve(), manuscript):
        errors.append("manifest escapes manuscript directory")
        print_json({"ok": False, "errors": errors})
        return 1
    if not manifest_path.is_file():
        errors.append(f"manifest is missing: {MANIFEST_NAME}")
        print_json({"ok": False, "errors": errors})
        return 1

    try:
        with manifest_path.open(encoding="utf-8") as handle:
            manifest = json.load(handle, object_pairs_hook=unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as error:
        errors.append(f"cannot read manifest: {error}")
        print_json({"ok": False, "errors": errors})
        return 1

    if not isinstance(manifest, dict):
        errors.append("manifest root must be a JSON object")
    else:
        missing = sorted(TOP_LEVEL_KEYS - set(manifest))
        unknown = sorted(set(manifest) - TOP_LEVEL_KEYS)
        if missing:
            errors.append(f"manifest is missing keys: {', '.join(missing)}")
        if unknown:
            errors.append(f"manifest has unknown keys: {', '.join(unknown)}")
        if (
            type(manifest.get("schema_version")) is not int
            or manifest.get("schema_version") != SCHEMA_VERSION
        ):
            errors.append(f"schema_version must be {SCHEMA_VERSION}")
        if manifest.get("kind") != KIND:
            errors.append(f"kind must be {KIND}")
        files = manifest.get("files")
        if not isinstance(files, dict):
            errors.append("files must be a JSON object")
        else:
            if set(files) != set(REQUIRED_FILES):
                errors.append("files keys must equal the required artifact paths")
            for relative in REQUIRED_FILES:
                expected = files.get(relative)
                if not isinstance(expected, str) or not SHA256_DIGEST.fullmatch(expected):
                    errors.append(f"invalid SHA-256 digest for {relative}")
                elif relative in paths:
                    current = file_sha256(paths[relative])
                    if current != expected:
                        errors.append(
                            f"digest mismatch for {relative}: manifest {expected}, "
                            f"current {current}"
                        )

    if errors:
        print_json({"ok": False, "errors": errors})
        return 1
    print_json(
        {"ok": True, "manuscript": str(manuscript), "manifest": str(manifest_path)}
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a manuscript directory")
    init_parser.add_argument("--root", type=Path, required=True, help="Project root")

    freeze_parser = subparsers.add_parser(
        "freeze", help="Hash the reviewed source, bibliography, and PDF"
    )
    freeze_parser.add_argument("--manuscript", type=Path, required=True)
    freeze_parser.add_argument(
        "--replace", action="store_true", help="Replace a stale manifest"
    )

    check_parser = subparsers.add_parser(
        "check", help="Verify required files and frozen hashes"
    )
    check_parser.add_argument("--manuscript", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "init":
        return initialize(args.root)
    if args.command == "freeze":
        return freeze(args.manuscript, args.replace)
    return check(args.manuscript)


if __name__ == "__main__":
    raise SystemExit(main())
