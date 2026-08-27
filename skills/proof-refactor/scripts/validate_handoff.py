#!/usr/bin/env python3
"""Create or validate a proof-refactor DAG and digest-bound handoff.

This validates the derived proof structure and byte bindings. Run
research-loop's ``check --strict --complete`` separately for canonical
research validity, evidence, and root freshness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from bisect import bisect_right
from datetime import date
from pathlib import Path
from typing import Any


HANDOFF_SCHEMA_VERSION = 2
LEGACY_HANDOFF_SCHEMA_VERSION = 1
PROOF_GRAPH_SCHEMA_VERSION = 1
HANDOFF_KIND = "proof-refactor-handoff"
PROOF_GRAPH_KIND = "proof-refactor-dag"
STATUS = "validated"
CANONICAL_GRAPH = "KEY_RESULTS.graph.json"
DEFAULT_PROOF_GRAPH = "proof.graph.json"
HANDOFF_KEYS = {
    1: {
        "schema_version",
        "kind",
        "status",
        "source",
        "proof",
        "proof_sha256",
    },
    2: {
        "schema_version",
        "kind",
        "status",
        "source",
        "proof",
        "proof_sha256",
        "proof_graph",
        "proof_graph_sha256",
    },
}
SOURCE_KEYS = {"graph", "roots", "root_digests"}
PROOF_GRAPH_KEYS = {"schema_version", "kind", "roots", "nodes"}
PROOF_NODE_KEYS = {"title", "statement", "requires", "sources"}
SHA256_DIGEST = re.compile(r"sha256:[0-9a-f]{64}$")
PROOF_NODE_ID = re.compile(r"PF-[0-9]+$")
SOURCE_CLAIM_ID = re.compile(r"KR-[0-9]+(?:-[A-Z][A-Z0-9]*)?$")
PROOF_HEADING = re.compile(r"^###\s+(PF-[0-9]+)\s+[—-]\s+(.+?)\s*$")
TOP_LEVEL_BOUNDARY = re.compile(r"^#{1,2}\s+")
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
FENCE_CLOSE = re.compile(r"^ {0,3}(`+|~+)[ \t]*$")
INITIAL_PROOF_GRAPH: dict[str, Any] = {
    "schema_version": PROOF_GRAPH_SCHEMA_VERSION,
    "kind": PROOF_GRAPH_KIND,
    "roots": [],
    "nodes": {},
}


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


def string_list(
    value: Any,
    label: str,
    errors: list[str],
    *,
    nonempty: bool = False,
) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{label} must be a list of strings")
        return []
    if nonempty and not value:
        errors.append(f"{label} must not be empty")
    if len(set(value)) != len(value):
        errors.append(f"{label} contains duplicates")
    return value


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


def resolve_create_file(
    value: Path,
    *,
    handoff_parent: Path,
    label: str,
    errors: list[str],
) -> Path | None:
    expanded = value.expanduser()
    resolved = (
        expanded.resolve()
        if expanded.is_absolute()
        else (handoff_parent / expanded).resolve()
    )
    if not is_within(resolved, handoff_parent):
        errors.append(f"{label} path escapes handoff directory")
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
        (output / DEFAULT_PROOF_GRAPH).write_text(
            json.dumps(INITIAL_PROOF_GRAPH, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        print_json({"ok": False, "errors": [f"cannot initialize refactor: {error}"]})
        return 1
    print_json(
        {
            "ok": True,
            "output": str(output),
            "created": ["proof.md", DEFAULT_PROOF_GRAPH],
        }
    )
    return 0


def proof_sections(text: str, errors: list[str]) -> dict[str, dict[str, str]]:
    headings: list[tuple[int, int, str, str]] = []
    boundaries: list[int] = []
    fence: tuple[str, int] | None = None
    offset = 0

    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        if fence is not None:
            closing = FENCE_CLOSE.fullmatch(content)
            if (
                closing is not None
                and closing.group(1)[0] == fence[0]
                and len(closing.group(1)) >= fence[1]
            ):
                fence = None
            offset += len(line)
            continue

        opening = FENCE_OPEN.fullmatch(content)
        if opening is not None:
            marker, info = opening.groups()
            if marker[0] == "~" or "`" not in info:
                fence = (marker[0], len(marker))
                offset += len(line)
                continue

        heading = PROOF_HEADING.fullmatch(content)
        if heading is not None:
            headings.append((offset, offset + len(line), *heading.groups()))
        elif TOP_LEVEL_BOUNDARY.match(content):
            boundaries.append(offset)
        offset += len(line)

    sections: dict[str, dict[str, str]] = {}
    for index, (start, body_start, node_id, title) in enumerate(headings):
        candidates = [len(text)]
        if index + 1 < len(headings):
            candidates.append(headings[index + 1][0])
        boundary_index = bisect_right(boundaries, start)
        if boundary_index < len(boundaries):
            candidates.append(boundaries[boundary_index])
        if node_id in sections:
            errors.append(f"proof has duplicate section heading: {node_id}")
            continue
        sections[node_id] = {
            "title": title.strip(),
            "body": text[body_start : min(candidates)],
        }
    return sections


def find_cycle(requires: dict[str, list[str]]) -> list[str] | None:
    visited: set[str] = set()
    active: list[str] = []
    active_set: set[str] = set()

    def visit(node_id: str) -> list[str] | None:
        if node_id in active_set:
            start = active.index(node_id)
            return active[start:] + [node_id]
        if node_id in visited:
            return None
        active.append(node_id)
        active_set.add(node_id)
        for dependency in requires.get(node_id, []):
            if dependency in requires:
                cycle = visit(dependency)
                if cycle:
                    return cycle
        active.pop()
        active_set.remove(node_id)
        visited.add(node_id)
        return None

    for node_id in requires:
        cycle = visit(node_id)
        if cycle:
            return cycle
    return None


def reachable_nodes(requires: dict[str, list[str]], roots: list[str]) -> set[str]:
    reached: set[str] = set()
    stack = list(roots)
    while stack:
        node_id = stack.pop()
        if node_id in reached or node_id not in requires:
            continue
        reached.add(node_id)
        stack.extend(requires[node_id])
    return reached


def canonical_closure(
    graph: dict[str, Any], roots: list[str], errors: list[str]
) -> set[str]:
    raw_requires = graph.get("requires")
    if not isinstance(raw_requires, dict):
        errors.append("source graph requires must be a JSON object for DAG validation")
        return set()

    reached: set[str] = set()
    active: set[str] = set()

    def visit(claim_id: str) -> None:
        if claim_id in reached:
            return
        if claim_id in active:
            errors.append(f"source graph cycle encountered at {claim_id}")
            return
        raw_dependencies = raw_requires.get(claim_id)
        if not isinstance(raw_dependencies, list) or not all(
            isinstance(item, str) for item in raw_dependencies
        ):
            errors.append(
                f"source graph closure claim {claim_id} has no string-list requires entry"
            )
            return
        active.add(claim_id)
        for dependency in raw_dependencies:
            visit(dependency)
        active.remove(claim_id)
        reached.add(claim_id)

    for root_id in roots:
        visit(root_id)
    return reached


def validate_proof_graph(
    data: Any,
    proof_text: str,
    source_graph: dict[str, Any],
    source_roots: list[str],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    summary: dict[str, Any] = {
        "proof_nodes": 0,
        "mapped_source_claims": [],
        "unmapped_source_claims": [],
    }
    if not isinstance(data, dict):
        return ["proof graph root must be a JSON object"], summary
    exact_keys(data, PROOF_GRAPH_KEYS, "proof graph", errors)
    if (
        type(data.get("schema_version")) is not int
        or data.get("schema_version") != PROOF_GRAPH_SCHEMA_VERSION
    ):
        errors.append(
            f"proof graph schema_version must be {PROOF_GRAPH_SCHEMA_VERSION}"
        )
    if data.get("kind") != PROOF_GRAPH_KIND:
        errors.append(f"proof graph kind must be {PROOF_GRAPH_KIND}")

    roots = string_list(data.get("roots"), "proof graph roots", errors, nonempty=True)
    for node_id in roots:
        if not PROOF_NODE_ID.fullmatch(node_id):
            errors.append(f"invalid proof root ID: {node_id}")

    raw_nodes = data.get("nodes")
    if not isinstance(raw_nodes, dict) or not raw_nodes:
        errors.append("proof graph nodes must be a non-empty JSON object")
        raw_nodes = {}

    requires: dict[str, list[str]] = {}
    sources: dict[str, list[str]] = {}
    titles: dict[str, str] = {}
    statements: dict[str, str] = {}
    for node_id, raw_node in raw_nodes.items():
        if not isinstance(node_id, str) or not PROOF_NODE_ID.fullmatch(node_id):
            errors.append(f"invalid proof node ID: {node_id!r}")
            continue
        if not isinstance(raw_node, dict):
            errors.append(f"proof node {node_id} must be a JSON object")
            continue
        exact_keys(raw_node, PROOF_NODE_KEYS, f"proof node {node_id}", errors)

        title = raw_node.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"proof node {node_id} title must be a non-empty string")
        else:
            titles[node_id] = title.strip()

        statement = raw_node.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            errors.append(f"proof node {node_id} statement must be a non-empty string")
        else:
            statements[node_id] = statement.strip()

        node_requires = string_list(
            raw_node.get("requires"), f"proof node {node_id} requires", errors
        )
        node_sources = string_list(
            raw_node.get("sources"),
            f"proof node {node_id} sources",
            errors,
            nonempty=True,
        )
        requires[node_id] = node_requires
        sources[node_id] = node_sources

        for dependency in node_requires:
            if not PROOF_NODE_ID.fullmatch(dependency):
                errors.append(
                    f"proof node {node_id} has invalid dependency {dependency}"
                )
            elif dependency == node_id:
                errors.append(f"proof node {node_id} requires itself")
        for claim_id in node_sources:
            if not SOURCE_CLAIM_ID.fullmatch(claim_id):
                errors.append(
                    f"proof node {node_id} has invalid source claim {claim_id}"
                )

    summary["proof_nodes"] = len(requires)
    for root_id in roots:
        if root_id not in requires:
            errors.append(f"proof root is not indexed: {root_id}")
    for node_id, dependencies in requires.items():
        for dependency in dependencies:
            if PROOF_NODE_ID.fullmatch(dependency) and dependency not in requires:
                errors.append(
                    f"proof node {node_id} requires unknown node {dependency}"
                )

    cycle = find_cycle(requires)
    if cycle:
        errors.append("proof graph cycle: " + " -> ".join(cycle))
    reached = reachable_nodes(requires, roots)
    orphaned = sorted(set(requires) - reached)
    if orphaned:
        errors.append(
            "proof graph has nodes outside every root closure: " + ", ".join(orphaned)
        )

    sections = proof_sections(proof_text, errors)
    extra_sections = sorted(set(sections) - set(requires))
    if extra_sections:
        errors.append(
            "proof has PF sections absent from proof graph: "
            + ", ".join(extra_sections)
        )
    for node_id in requires:
        section = sections.get(node_id)
        if section is None:
            errors.append(f"proof graph node has no proof section: {node_id}")
            continue
        expected_title = titles.get(node_id)
        if expected_title is not None and section["title"] != expected_title:
            errors.append(
                f"proof section title does not match proof graph node {node_id}"
            )
        statement = statements.get(node_id)
        if statement is not None and not section["body"].lstrip().startswith(statement):
            errors.append(
                f"proof section {node_id} must begin with its exact statement"
            )

    source_closure = canonical_closure(source_graph, source_roots, errors)
    mapped = {
        claim_id for node_sources in sources.values() for claim_id in node_sources
    }
    outside = sorted(mapped - source_closure)
    if outside:
        errors.append(
            "proof graph sources outside canonical root closure: " + ", ".join(outside)
        )
    root_sources = {
        claim_id for root_id in roots for claim_id in sources.get(root_id, [])
    }
    missing_root_sources = sorted(set(source_roots) - root_sources)
    if missing_root_sources:
        errors.append(
            "proof roots do not directly map canonical Goal roots: "
            + ", ".join(missing_root_sources)
        )

    summary["mapped_source_claims"] = sorted(mapped & source_closure)
    summary["unmapped_source_claims"] = sorted(source_closure - mapped)
    if summary["unmapped_source_claims"]:
        errors.append(
            "proof graph does not account for canonical closure claims: "
            + ", ".join(summary["unmapped_source_claims"])
        )
    return errors, summary


def source_graph_metadata(
    graph: Any, errors: list[str]
) -> tuple[list[str], dict[str, str]]:
    if not isinstance(graph, dict):
        errors.append("source graph root must be a JSON object")
        return [], {}
    roots = string_list(graph.get("roots"), "source graph roots", errors, nonempty=True)
    root_digests = graph.get("root_digests")
    if not isinstance(root_digests, dict):
        errors.append("source graph root_digests must be a JSON object")
        return roots, {}
    if roots and set(root_digests) != set(roots):
        errors.append("source graph root_digests keys must equal roots")
    digests: dict[str, str] = {}
    for claim_id, digest in root_digests.items():
        if not isinstance(claim_id, str):
            errors.append("source graph root_digests keys must be strings")
        elif not isinstance(digest, str) or not SHA256_DIGEST.fullmatch(digest):
            errors.append(f"invalid SHA-256 digest for source root {claim_id}")
        else:
            digests[claim_id] = digest
    return roots, digests


def create_manifest(
    root: Path,
    handoff: Path,
    proof_value: Path,
    proof_graph_value: Path,
) -> list[str]:
    errors: list[str] = []
    if not handoff.parent.is_dir():
        return [f"handoff parent is not a directory: {handoff.parent}"]
    if handoff.exists() or handoff.is_symlink():
        return [f"handoff already exists: {handoff}"]

    proof = resolve_create_file(
        proof_value,
        handoff_parent=handoff.parent,
        label="proof",
        errors=errors,
    )
    proof_graph = resolve_create_file(
        proof_graph_value,
        handoff_parent=handoff.parent,
        label="proof graph",
        errors=errors,
    )
    graph_path = (root / CANONICAL_GRAPH).resolve()
    if not is_within(graph_path, root):
        errors.append("canonical graph escapes research root")
    elif not readable_file(graph_path, "source.graph", errors):
        pass
    if errors:
        return errors

    try:
        source_graph = load_json(graph_path)
        proof_graph_data = load_json(proof_graph)
        proof_text = proof.read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as error:
        return [f"cannot read refactor source: {error}"]

    roots, root_digests = source_graph_metadata(source_graph, errors)
    if isinstance(source_graph, dict):
        graph_errors, _ = validate_proof_graph(
            proof_graph_data, proof_text, source_graph, roots
        )
        errors.extend(graph_errors)
    if errors:
        return errors

    manifest = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "kind": HANDOFF_KIND,
        "status": STATUS,
        "source": {
            "graph": CANONICAL_GRAPH,
            "roots": roots,
            "root_digests": root_digests,
        },
        "proof": proof.relative_to(handoff.parent).as_posix(),
        "proof_sha256": file_sha256(proof),
        "proof_graph": proof_graph.relative_to(handoff.parent).as_posix(),
        "proof_graph_sha256": file_sha256(proof_graph),
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
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    result: dict[str, Any] = {
        "schema_version": None,
        "graph": None,
        "proof": None,
        "proof_graph": None,
        "roots": [],
        "proof_sha256": None,
        "proof_graph_sha256": None,
        "proof_nodes": 0,
        "mapped_source_claims": [],
        "unmapped_source_claims": [],
    }
    if not isinstance(data, dict):
        return ["handoff root must be a JSON object"], result

    raw_version = data.get("schema_version")
    version = raw_version if type(raw_version) is int else None
    expected_keys = HANDOFF_KEYS.get(version, HANDOFF_KEYS[HANDOFF_SCHEMA_VERSION])
    exact_keys(data, expected_keys, "handoff", errors)
    if version not in HANDOFF_KEYS:
        errors.append(
            "schema_version must be 1 (legacy) or " + str(HANDOFF_SCHEMA_VERSION)
        )
    result["schema_version"] = version
    if data.get("kind") != HANDOFF_KIND:
        errors.append(f"kind must be {HANDOFF_KIND}")
    if data.get("status") != STATUS:
        errors.append(f"status must be {STATUS}")

    roots: list[str] = []
    root_digests: dict[str, str] = {}
    graph_path: Path | None = None
    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source must be a JSON object")
    else:
        exact_keys(source, SOURCE_KEYS, "source", errors)
        roots = string_list(source.get("roots"), "source.roots", errors, nonempty=True)
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

    proof_digest = data.get("proof_sha256")
    if not isinstance(proof_digest, str) or not SHA256_DIGEST.fullmatch(proof_digest):
        errors.append("proof_sha256 must be sha256 followed by 64 lowercase hex digits")
        proof_digest = None
    proof_path = resolve_relative_file(
        data.get("proof"),
        base=handoff.parent,
        boundary=handoff.parent,
        label="proof",
        errors=errors,
    )

    proof_graph_path: Path | None = None
    proof_graph_digest: str | None = None
    if version == HANDOFF_SCHEMA_VERSION:
        proof_graph_digest = data.get("proof_graph_sha256")
        if not isinstance(proof_graph_digest, str) or not SHA256_DIGEST.fullmatch(
            proof_graph_digest
        ):
            errors.append(
                "proof_graph_sha256 must be sha256 followed by 64 lowercase hex digits"
            )
            proof_graph_digest = None
        proof_graph_path = resolve_relative_file(
            data.get("proof_graph"),
            base=handoff.parent,
            boundary=handoff.parent,
            label="proof graph",
            errors=errors,
        )

    source_graph: Any = None
    if graph_path is not None:
        try:
            source_graph = load_json(graph_path)
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            DuplicateKeyError,
        ) as error:
            errors.append(f"cannot read source graph: {error}")
        else:
            current_errors: list[str] = []
            graph_roots, graph_digests = source_graph_metadata(
                source_graph, current_errors
            )
            errors.extend(current_errors)
            if roots and set(graph_roots) != set(roots):
                errors.append("handoff roots do not match current source graph roots")
            if root_digests != graph_digests:
                errors.append("handoff root_digests do not match current source graph")

    if proof_path is not None and proof_digest is not None:
        if file_sha256(proof_path) != proof_digest:
            errors.append(
                "proof_sha256 does not match proof bytes; "
                f"manifest {proof_digest}, current {file_sha256(proof_path)}"
            )

    if proof_graph_path is not None and proof_graph_digest is not None:
        current_graph_digest = file_sha256(proof_graph_path)
        if current_graph_digest != proof_graph_digest:
            errors.append(
                "proof_graph_sha256 does not match proof graph bytes; "
                f"manifest {proof_graph_digest}, current {current_graph_digest}"
            )

    if (
        version == HANDOFF_SCHEMA_VERSION
        and proof_path is not None
        and proof_graph_path is not None
        and isinstance(source_graph, dict)
    ):
        try:
            proof_text = proof_path.read_text(encoding="utf-8")
            proof_graph_data = load_json(proof_graph_path)
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            DuplicateKeyError,
        ) as error:
            errors.append(f"cannot read proof graph: {error}")
        else:
            graph_errors, graph_summary = validate_proof_graph(
                proof_graph_data, proof_text, source_graph, roots
            )
            errors.extend(graph_errors)
            result.update(graph_summary)

    result.update(
        {
            "graph": graph_path,
            "proof": proof_path,
            "proof_graph": proof_graph_path,
            "roots": roots,
            "proof_sha256": proof_digest,
            "proof_graph_sha256": proof_graph_digest,
        }
    )
    return errors, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Research root")
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--init",
        action="store_true",
        help="Create a nonconflicting refactor directory and minimal files",
    )
    action.add_argument(
        "--create",
        action="store_true",
        help="Create the handoff from canonical and derived proof files",
    )
    parser.add_argument(
        "--proof",
        type=Path,
        help="Proof path, relative to the handoff directory unless absolute",
    )
    parser.add_argument(
        "--proof-graph",
        type=Path,
        help=f"Proof DAG path (default for --create: {DEFAULT_PROOF_GRAPH})",
    )
    parser.add_argument("handoff", type=Path, nargs="?", help="Path to handoff.json")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print_json({"ok": False, "errors": [f"root is not a directory: {root}"]})
        return 1

    if args.init:
        if (
            args.handoff is not None
            or args.proof is not None
            or args.proof_graph is not None
        ):
            print_json(
                {
                    "ok": False,
                    "errors": [
                        "--init does not accept handoff, --proof, or --proof-graph"
                    ],
                }
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
        proof_graph_value = args.proof_graph or Path(DEFAULT_PROOF_GRAPH)
        errors = create_manifest(root, handoff, args.proof, proof_graph_value)
        if errors:
            print_json({"ok": False, "errors": errors})
            return 1
    elif args.proof is not None or args.proof_graph is not None:
        print_json(
            {"ok": False, "errors": ["--proof and --proof-graph require --create"]}
        )
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

    errors, result = validate_manifest(root, handoff, data)
    if errors:
        print_json({"ok": False, "errors": errors})
        return 1

    print_json(
        {
            "ok": True,
            "root": str(root),
            "handoff": str(handoff),
            "schema_version": result["schema_version"],
            "legacy": result["schema_version"] == LEGACY_HANDOFF_SCHEMA_VERSION,
            "graph": str(result["graph"]),
            "proof": str(result["proof"]),
            "proof_graph": (
                str(result["proof_graph"])
                if result["proof_graph"] is not None
                else None
            ),
            "roots": result["roots"],
            "proof_sha256": result["proof_sha256"],
            "proof_graph_sha256": result["proof_graph_sha256"],
            "proof_nodes": result["proof_nodes"],
            "mapped_source_claims": result["mapped_source_claims"],
            "unmapped_source_claims": result["unmapped_source_claims"],
            "created": args.create,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
