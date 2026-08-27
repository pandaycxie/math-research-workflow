#!/usr/bin/env python3
"""Create or validate a proof-refactor handoff and its byte-level bindings.

This intentionally does not validate the research DAG, ledger, evidence, or
root freshness. Run research-loop's ``check --strict --complete`` separately.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
KIND = "proof-refactor-handoff"
STATUS = "validated"
CANONICAL_GRAPH = "KEY_RESULTS.graph.json"
TOP_LEVEL_KEYS = {
    "schema_version",
    "kind",
    "status",
    "source",
    "proof",
    "proof_sha256",
}
SOURCE_KEYS = {"graph", "roots", "root_digests"}
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


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=unique_object)


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def exact_keys(
    value: dict[str, Any], expected: set[str], label: str, errors: list[str]
) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        errors.append(f"{label} is missing keys: {', '.join(missing)}")
    if unknown:
        errors.append(f"{label} has unknown keys: {', '.join(unknown)}")


def is_within(path: Path, boundary: Path) -> bool:
    try:
        path.relative_to(boundary)
    except ValueError:
        return False
    return True


def readable_file(path: Path, label: str, errors: list[str]) -> bool:
    if not path.is_file():
        errors.append(f"{label} is not a readable file: {path}")
        return False
    try:
        with path.open("rb") as handle:
            handle.read(1)
    except OSError as error:
        errors.append(f"{label} is not readable: {path} ({error})")
        return False
    return True


def resolve_relative_file(
    value: Any,
    *,
    base: Path,
    boundary: Path,
    label: str,
    errors: list[str],
) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{label} must be a non-empty relative path")
        return None
    relative = Path(value)
    if relative.is_absolute():
        errors.append(f"{label} must be relative")
        return None
    resolved = (base / relative).resolve()
    if not is_within(resolved, boundary):
        errors.append(f"{label} escapes its allowed directory: {value}")
        return None
    if not readable_file(resolved, label, errors):
        return None
    return resolved


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def initialize(root: Path) -> int:
    stem = f"proof_refactor_{date.today():%Y%m%d}"
    output = root / stem
    suffix = 2
    while output.exists():
        output = root / f"{stem}-{suffix}"
        suffix += 1
    try:
        output.mkdir()
        (output / "proof.md").touch()
    except OSError as error:
        print_json({"ok": False, "errors": [f"cannot initialize refactor: {error}"]})
        return 1
    print_json(
        {"ok": True, "output": str(output), "created": ["proof.md"]}
    )
    return 0


def create_manifest(root: Path, handoff: Path, proof_value: Path) -> list[str]:
    errors: list[str] = []
    if not handoff.parent.is_dir():
        return [f"handoff parent is not a directory: {handoff.parent}"]
    if handoff.exists() or handoff.is_symlink():
        return [f"handoff already exists: {handoff}"]

    proof = (
        proof_value.expanduser().resolve()
        if proof_value.expanduser().is_absolute()
        else (handoff.parent / proof_value.expanduser()).resolve()
    )
    if not is_within(proof, handoff.parent):
        errors.append("proof path escapes handoff directory")
    elif not readable_file(proof, "proof", errors):
        pass

    graph_path = (root / CANONICAL_GRAPH).resolve()
    if not is_within(graph_path, root):
        errors.append("canonical graph escapes research root")
    elif not readable_file(graph_path, "source.graph", errors):
        pass

    graph: Any = None
    if not errors:
        try:
            graph = load_json(graph_path)
        except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as error:
            errors.append(f"cannot read source graph: {error}")
    if errors:
        return errors
    if not isinstance(graph, dict):
        return ["source graph root must be a JSON object"]

    roots = graph.get("roots")
    roots_valid = not (
        not isinstance(roots, list)
        or not roots
        or not all(isinstance(item, str) and item for item in roots)
    )
    if not roots_valid:
        errors.append("source graph roots must be a non-empty list of strings")
    elif len(set(roots)) != len(roots):
        errors.append("source graph roots contains duplicates")
        roots_valid = False

    root_digests = graph.get("root_digests")
    if not isinstance(root_digests, dict):
        errors.append("source graph root_digests must be a JSON object")
    elif roots_valid:
        if set(root_digests) != set(roots):
            errors.append("source graph root_digests keys must equal roots")
        for claim_id, digest in root_digests.items():
            if not isinstance(digest, str) or not SHA256_DIGEST.fullmatch(digest):
                errors.append(f"invalid SHA-256 digest for source root {claim_id}")
    if errors:
        return errors

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "status": STATUS,
        "source": {
            "graph": CANONICAL_GRAPH,
            "roots": roots,
            "root_digests": root_digests,
        },
        "proof": proof.relative_to(handoff.parent).as_posix(),
        "proof_sha256": file_sha256(proof),
    }
    try:
        handoff.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        return [f"cannot write handoff: {error}"]
    return []


def validate_manifest(
    root: Path, handoff: Path, data: Any
) -> tuple[list[str], Path | None, Path | None, list[str], str | None]:
    errors: list[str] = []
    graph_path: Path | None = None
    proof_path: Path | None = None
    roots: list[str] = []
    proof_digest: str | None = None

    if not isinstance(data, dict):
        return ["handoff root must be a JSON object"], None, None, roots, None
    exact_keys(data, TOP_LEVEL_KEYS, "handoff", errors)

    if (
        type(data.get("schema_version")) is not int
        or data.get("schema_version") != SCHEMA_VERSION
    ):
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if data.get("kind") != KIND:
        errors.append(f"kind must be {KIND}")
    if data.get("status") != STATUS:
        errors.append(f"status must be {STATUS}")

    source = data.get("source")
    root_digests: dict[str, str] = {}
    if not isinstance(source, dict):
        errors.append("source must be a JSON object")
    else:
        exact_keys(source, SOURCE_KEYS, "source", errors)

        raw_roots = source.get("roots")
        if (
            not isinstance(raw_roots, list)
            or not raw_roots
            or not all(isinstance(item, str) and item for item in raw_roots)
        ):
            errors.append("source.roots must be a non-empty list of strings")
        elif len(set(raw_roots)) != len(raw_roots):
            errors.append("source.roots contains duplicates")
        else:
            roots = raw_roots

        raw_digests = source.get("root_digests")
        if not isinstance(raw_digests, dict):
            errors.append("source.root_digests must be a JSON object")
        elif not all(isinstance(key, str) for key in raw_digests):
            errors.append("source.root_digests keys must be strings")
        else:
            root_digests = raw_digests
            if roots and set(root_digests) != set(roots):
                errors.append("source.root_digests keys must equal source.roots")
            for claim_id, digest in root_digests.items():
                if not isinstance(digest, str) or not SHA256_DIGEST.fullmatch(digest):
                    errors.append(f"invalid SHA-256 digest for source root {claim_id}")

        graph_value = source.get("graph")
        if graph_value != CANONICAL_GRAPH:
            errors.append(f"source.graph must be {CANONICAL_GRAPH}")
        else:
            graph_path = resolve_relative_file(
                graph_value,
                base=root,
                boundary=root,
                label="source.graph",
                errors=errors,
            )

    raw_proof_digest = data.get("proof_sha256")
    if not isinstance(raw_proof_digest, str) or not SHA256_DIGEST.fullmatch(
        raw_proof_digest
    ):
        errors.append("proof_sha256 must be sha256 followed by 64 lowercase hex digits")
    else:
        proof_digest = raw_proof_digest

    proof_path = resolve_relative_file(
        data.get("proof"),
        base=handoff.parent,
        boundary=handoff.parent,
        label="proof",
        errors=errors,
    )

    if graph_path is not None:
        try:
            graph = load_json(graph_path)
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            DuplicateKeyError,
        ) as error:
            errors.append(f"cannot read source graph: {error}")
        else:
            if not isinstance(graph, dict):
                errors.append("source graph root must be a JSON object")
            else:
                graph_roots = graph.get("roots")
                if not isinstance(graph_roots, list) or not all(
                    isinstance(item, str) for item in graph_roots
                ):
                    errors.append("source graph roots must be a list of strings")
                elif len(set(graph_roots)) != len(graph_roots):
                    errors.append("source graph roots contains duplicates")
                elif roots and set(graph_roots) != set(roots):
                    errors.append(
                        "handoff roots do not match current source graph roots"
                    )

                graph_digests = graph.get("root_digests")
                if not isinstance(graph_digests, dict):
                    errors.append("source graph root_digests must be a JSON object")
                elif root_digests != graph_digests:
                    errors.append(
                        "handoff root_digests do not match current source graph"
                    )

    if proof_path is not None and proof_digest is not None:
        try:
            current_digest = file_sha256(proof_path)
        except OSError as error:
            errors.append(f"cannot hash proof: {error}")
        else:
            if current_digest != proof_digest:
                errors.append(
                    "proof_sha256 does not match proof bytes; "
                    f"manifest {proof_digest}, current {current_digest}"
                )

    return errors, graph_path, proof_path, roots, proof_digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Research root")
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--init",
        action="store_true",
        help="Create a nonconflicting refactor directory and empty proof.md",
    )
    action.add_argument(
        "--create",
        action="store_true",
        help="Create the handoff from the canonical graph and proof bytes",
    )
    parser.add_argument(
        "--proof",
        type=Path,
        help="Proof path, relative to the handoff directory unless absolute",
    )
    parser.add_argument("handoff", type=Path, nargs="?", help="Path to handoff.json")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print_json({"ok": False, "errors": [f"root is not a directory: {root}"]})
        return 1

    if args.init:
        if args.handoff is not None or args.proof is not None:
            print_json(
                {"ok": False, "errors": ["--init does not accept handoff or --proof"]}
            )
            return 1
        return initialize(root)
    if args.handoff is None:
        parser.error("handoff path is required unless --init is used")

    handoff_arg = args.handoff.expanduser()
    handoff = (
        handoff_arg.resolve()
        if handoff_arg.is_absolute()
        else (root / handoff_arg).resolve()
    )
    if not is_within(handoff, root):
        print_json({"ok": False, "errors": ["handoff path escapes research root"]})
        return 1
    if args.create:
        if args.proof is None:
            print_json({"ok": False, "errors": ["--create requires --proof"]})
            return 1
        errors = create_manifest(root, handoff, args.proof)
        if errors:
            print_json({"ok": False, "errors": errors})
            return 1
    elif args.proof is not None:
        print_json({"ok": False, "errors": ["--proof requires --create"]})
        return 1
    errors: list[str] = []
    if not readable_file(handoff, "handoff", errors):
        print_json({"ok": False, "errors": errors})
        return 1

    try:
        data = load_json(handoff)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as error:
        print_json({"ok": False, "errors": [f"cannot read handoff: {error}"]})
        return 1

    errors, graph, proof, roots, proof_digest = validate_manifest(root, handoff, data)
    if errors:
        print_json({"ok": False, "errors": errors})
        return 1

    print_json(
        {
            "ok": True,
            "root": str(root),
            "handoff": str(handoff),
            "graph": str(graph),
            "proof": str(proof),
            "roots": roots,
            "proof_sha256": proof_digest,
            "created": args.create,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
