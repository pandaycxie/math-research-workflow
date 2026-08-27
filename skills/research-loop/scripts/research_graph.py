#!/usr/bin/env python3
"""Validate and inspect a research project's sparse KEY_RESULTS dependency index."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from bisect import bisect_right
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = ("Open", "Conditional", "Proved", "Rejected", "Superseded")
SUPPORTED_SCHEMA_VERSIONS = (2, 3)
SHOW_MAX_LINES = 400
SHOW_MAX_BYTES = 32 * 1024
FIND_DEFAULT_LIMIT = 20
FIND_MAX_LIMIT = 100
CLAIM_TOKEN = r"KR-[0-9]+(?:-[A-Z][A-Z0-9]*)?"
CLAIM_ID = re.compile(rf"{CLAIM_TOKEN}$")
CLAIM_NUMBER = re.compile(r"KR-([0-9]+)(?:-[A-Z][A-Z0-9]*)?$")
SHA256_DIGEST = re.compile(r"sha256:[0-9a-f]{64}$")
HEADING = re.compile(
    r"^###\s+(KR-\S+)\s+[—-]\s+(.+?)\s+\[([^\]]+)\]\s*$",
)
TOP_LEVEL_BOUNDARY = re.compile(r"^#{1,2}\s+")
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
FENCE_CLOSE = re.compile(r"^ {0,3}(`+|~+)[ \t]*$")

INITIAL_LEDGER = """# Key Results

Add important claims as:

`### KR-001 — Mathematical object and conclusion [Open]`
"""

INITIAL_LOG = """# Research Log

## Current restart point

- Goal roots: none yet
- State: initialized
- Last safe checkpoint: research memory created
- Next safe action: define the active Goal and first important claim
"""

INITIAL_GRAPH: dict[str, Any] = {
    "schema_version": 3,
    "ledger": "KEY_RESULTS.md",
    "roots": [],
    "requires": {},
    "evidence": {},
    "root_digests": {},
}


def resolve_root(explicit_root: Path | None, graph_arg: Path | None) -> Path:
    """Select a root independently of where this global skill is installed."""
    if explicit_root is not None:
        return explicit_root.expanduser().resolve()
    if graph_arg is not None:
        graph = graph_arg.expanduser()
        if not graph.is_absolute():
            graph = Path.cwd() / graph
        return graph.resolve().parent
    start = Path.cwd().resolve()
    for candidate in (start, *start.parents):
        if (candidate / "KEY_RESULTS.graph.json").is_file():
            return candidate
    return start


def resolve_graph(
    root: Path, explicit_root: Path | None, graph_arg: Path | None
) -> Path:
    if graph_arg is None:
        return root / "KEY_RESULTS.graph.json"
    graph = graph_arg.expanduser()
    if graph.is_absolute():
        return graph.resolve()
    base = root if explicit_root is not None else Path.cwd()
    return (base / graph).resolve()


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def bounded_find_limit(value: str) -> int:
    try:
        limit = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("limit must be an integer") from error
    if not 1 <= limit <= FIND_MAX_LIMIT:
        raise argparse.ArgumentTypeError(
            f"limit must be between 1 and {FIND_MAX_LIMIT}"
        )
    return limit


def initialize_memory(root: Path, graph_path: Path, dry_run: bool) -> None:
    files = {
        root / "KEY_RESULTS.md": INITIAL_LEDGER,
        graph_path: json.dumps(INITIAL_GRAPH, indent=2, ensure_ascii=False) + "\n",
        root / "RESEARCH_LOG.md": INITIAL_LOG,
    }
    existing = [str(path) for path in files if path.exists()]
    if existing:
        raise FileExistsError(
            "refusing to overwrite existing research memory: " + ", ".join(existing)
        )
    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print_json(
        {
            "ok": True,
            "dry_run": dry_run,
            "root": str(root),
            "files": [str(path) for path in files],
        }
    )


def load_graph(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("graph root must be a JSON object")
    return value


def status_from_label(label: str) -> str | None:
    label = label.strip()
    return label if label in ALLOWED_STATUSES else None


def canonical_section(section: str) -> str:
    """Normalize inconsequential trailing whitespace for review digests."""
    return "\n".join(line.rstrip() for line in section.splitlines()).strip() + "\n"


def markdown_structure(
    text: str,
) -> tuple[list[tuple[int, str, str, str]], list[int]]:
    """Find claim headings and higher-level boundaries outside code fences."""
    headings: list[tuple[int, str, str, str]] = []
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

        heading = HEADING.fullmatch(content)
        if heading is not None:
            headings.append((offset, *heading.groups()))
        elif TOP_LEVEL_BOUNDARY.match(content):
            boundaries.append(offset)
        offset += len(line)

    return headings, boundaries


def load_ledger(
    root: Path, ledger_name: str, errors: list[str]
) -> dict[str, dict[str, str | None]]:
    ledger = (root / ledger_name).resolve()
    try:
        ledger.relative_to(root.resolve())
    except ValueError:
        errors.append(f"ledger escapes research root: {ledger_name}")
        return {}
    if not ledger.is_file():
        errors.append(f"ledger does not exist: {ledger_name}")
        return {}

    text = ledger.read_text(encoding="utf-8")
    claims: dict[str, dict[str, str | None]] = {}
    headings, boundaries = markdown_structure(text)
    for index, (section_start, claim_id, title, label) in enumerate(headings):
        if not CLAIM_ID.fullmatch(claim_id):
            errors.append(f"invalid claim id in ledger heading: {claim_id}")
            continue
        if claim_id in claims:
            errors.append(f"duplicate ledger heading: {claim_id}")
            continue
        candidates = [len(text)]
        if index + 1 < len(headings):
            candidates.append(headings[index + 1][0])
        boundary_index = bisect_right(boundaries, section_start)
        if boundary_index < len(boundaries):
            candidates.append(boundaries[boundary_index])
        section_end = min(candidates)
        claims[claim_id] = {
            "title": title.strip(),
            "label": label.strip(),
            "status": status_from_label(label),
            "section": canonical_section(text[section_start:section_end]),
        }
    return claims


def next_claim_id(ledger_claims: dict[str, dict[str, str | None]]) -> str:
    numbers: list[tuple[int, int]] = []
    for claim_id in ledger_claims:
        match = CLAIM_NUMBER.fullmatch(claim_id)
        if match is not None:
            number = match.group(1)
            numbers.append((int(number), len(number)))
    next_number = max((number for number, _ in numbers), default=0) + 1
    width = max((width for _, width in numbers), default=3)
    return f"KR-{next_number:0{max(3, width)}d}"


def find_claims(
    query: str,
    ledger_claims: dict[str, dict[str, str | None]],
    limit: int,
) -> tuple[list[dict[str, str | None]], int]:
    terms = query.casefold().split()
    if not terms:
        raise ValueError("find query must contain a non-whitespace character")
    matches: list[dict[str, str | None]] = []
    total = 0
    for claim_id, claim in ledger_claims.items():
        title = str(claim["title"])
        haystack = f"{claim_id} {title}".casefold()
        if all(term in haystack for term in terms):
            total += 1
            if len(matches) < limit:
                matches.append(
                    {
                        "id": claim_id,
                        "title": title,
                        "status": claim["status"],
                    }
                )
    return matches, total


def string_list(value: Any, field: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{field} must be a list of strings")
        return []
    return value


def find_cycle(requires: dict[str, list[str]]) -> list[str] | None:
    visited: set[str] = set()
    active: list[str] = []
    active_set: set[str] = set()

    def visit(claim_id: str) -> list[str] | None:
        if claim_id in active_set:
            start = active.index(claim_id)
            return active[start:] + [claim_id]
        if claim_id in visited:
            return None
        active.append(claim_id)
        active_set.add(claim_id)
        for dependency in requires.get(claim_id, []):
            if dependency in requires:
                cycle = visit(dependency)
                if cycle:
                    return cycle
        active.pop()
        active_set.remove(claim_id)
        visited.add(claim_id)
        return None

    for claim_id in requires:
        cycle = visit(claim_id)
        if cycle:
            return cycle
    return None


def validate(
    data: dict[str, Any], root: Path
) -> tuple[
    list[str],
    list[str],
    dict[str, list[str]],
    list[str],
    dict[str, dict[str, str | None]],
    dict[str, list[str]],
    dict[str, str],
]:
    errors: list[str] = []
    warnings: list[str] = []
    schema_version = data.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(
            "schema_version must be one of "
            + ", ".join(map(str, SUPPORTED_SCHEMA_VERSIONS))
        )
    elif schema_version == 2:
        warnings.append(
            "schema_version 2 has no root-closure freshness guard; "
            "upgrade before the next completion claim"
        )

    ledger_name = data.get("ledger")
    if not isinstance(ledger_name, str) or not ledger_name:
        errors.append("ledger must be a non-empty string")
        ledger_name = "KEY_RESULTS.md"
    ledger_claims = load_ledger(root, ledger_name, errors)

    raw_requires = data.get("requires")
    if not isinstance(raw_requires, dict):
        errors.append("requires must be an object mapping claim IDs to lists")
        raw_requires = {}

    requires: dict[str, list[str]] = {}
    for claim_id, raw_dependencies in raw_requires.items():
        if not isinstance(claim_id, str) or not CLAIM_ID.fullmatch(claim_id):
            errors.append(f"invalid claim id in requires: {claim_id!r}")
            continue
        dependencies = string_list(raw_dependencies, f"requires.{claim_id}", errors)
        if len(set(dependencies)) != len(dependencies):
            errors.append(f"{claim_id} has duplicate dependencies")
        requires[claim_id] = dependencies

    raw_evidence = data.get("evidence", {})
    if not isinstance(raw_evidence, dict):
        errors.append("evidence must be an object mapping claim IDs to path lists")
        raw_evidence = {}
    evidence: dict[str, list[str]] = {}
    for claim_id, raw_paths in raw_evidence.items():
        if not isinstance(claim_id, str) or not CLAIM_ID.fullmatch(claim_id):
            errors.append(f"invalid claim id in evidence: {claim_id!r}")
            continue
        paths = string_list(raw_paths, f"evidence.{claim_id}", errors)
        if len(set(paths)) != len(paths):
            errors.append(f"{claim_id} has duplicate evidence paths")
        evidence[claim_id] = paths

    raw_root_digests = data.get("root_digests", {})
    if not isinstance(raw_root_digests, dict):
        errors.append("root_digests must be an object mapping root IDs to digests")
        raw_root_digests = {}
    root_digests: dict[str, str] = {}
    for claim_id, digest in raw_root_digests.items():
        if not isinstance(claim_id, str) or not CLAIM_ID.fullmatch(claim_id):
            errors.append(f"invalid claim id in root_digests: {claim_id!r}")
        elif not isinstance(digest, str) or not SHA256_DIGEST.fullmatch(digest):
            errors.append(f"invalid SHA-256 digest for root {claim_id}")
        else:
            root_digests[claim_id] = digest

    roots = string_list(data.get("roots"), "roots", errors)
    if len(set(roots)) != len(roots):
        errors.append("roots contains duplicates")

    for root_id in roots:
        if not CLAIM_ID.fullmatch(root_id):
            errors.append(f"invalid claim id in roots: {root_id}")
        elif root_id not in requires:
            errors.append(f"root is not indexed: {root_id}")

    for claim_id, dependencies in requires.items():
        ledger_claim = ledger_claims.get(claim_id)
        if ledger_claim is None:
            errors.append(f"indexed claim has no ledger heading: {claim_id}")
        elif ledger_claim["status"] is None:
            errors.append(
                f"{claim_id} has unsupported ledger status [{ledger_claim['label']}]"
            )

        for dependency in dependencies:
            if not CLAIM_ID.fullmatch(dependency):
                errors.append(
                    f"invalid dependency claim id in requires.{claim_id}: {dependency}"
                )
                continue
            if dependency == claim_id:
                errors.append(f"{claim_id} requires itself")
            elif dependency not in requires:
                errors.append(f"{claim_id} requires unindexed claim {dependency}")

            dependency_claim = ledger_claims.get(dependency)
            if (
                ledger_claim is not None
                and ledger_claim["status"] == "Proved"
                and dependency_claim is not None
                and dependency_claim["status"] != "Proved"
            ):
                errors.append(
                    f"proved claim {claim_id} has unproved dependency {dependency}"
                )

    for claim_id in evidence:
        if claim_id not in requires:
            errors.append(f"evidence belongs to unindexed claim: {claim_id}")

    extra_digest_roots = sorted(set(root_digests) - set(roots))
    if extra_digest_roots:
        warnings.append(
            "root_digests contains non-root claims: " + ", ".join(extra_digest_roots)
        )

    cycle = find_cycle(requires)
    if cycle:
        errors.append("requires cycle: " + " -> ".join(cycle))
    return (
        errors,
        warnings,
        requires,
        roots,
        ledger_claims,
        evidence,
        root_digests,
    )


def resolve_evidence(root: Path, relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        raise ValueError(f"evidence path must be relative: {relative_path}")
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"evidence escapes research root: {relative_path}") from error
    return resolved


def evidence_errors(root: Path, evidence: dict[str, list[str]]) -> list[str]:
    errors: list[str] = []
    for claim_id, paths in evidence.items():
        for relative_path in paths:
            try:
                path = resolve_evidence(root, relative_path)
            except ValueError as error:
                errors.append(f"{claim_id}: {error}")
                continue
            if not path.is_file():
                errors.append(
                    f"{claim_id} evidence is not a readable file: {relative_path}"
                )
                continue
            try:
                with path.open("rb") as handle:
                    handle.read(1)
            except OSError as error:
                errors.append(
                    f"{claim_id} evidence is not readable: {relative_path} ({error})"
                )
    return errors


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def closure_order(requires: dict[str, list[str]], target: str) -> list[str]:
    if target not in requires:
        raise KeyError(f"unknown claim: {target}")
    visited: set[str] = set()
    order: list[str] = []

    def visit(claim_id: str) -> None:
        if claim_id in visited:
            return
        for dependency in requires[claim_id]:
            visit(dependency)
        visited.add(claim_id)
        order.append(claim_id)

    visit(target)
    return order


def closure_digest(
    root: Path,
    target: str,
    requires: dict[str, list[str]],
    ledger_claims: dict[str, dict[str, str | None]],
    evidence: dict[str, list[str]],
) -> str:
    claims: list[dict[str, Any]] = []
    for claim_id in sorted(closure_order(requires, target)):
        evidence_records = []
        for relative_path in sorted(evidence.get(claim_id, [])):
            path = resolve_evidence(root, relative_path)
            evidence_records.append(
                {"path": relative_path, "sha256": file_sha256(path)}
            )
        claims.append(
            {
                "id": claim_id,
                "requires": sorted(requires[claim_id]),
                "section": ledger_claims[claim_id]["section"],
                "evidence": evidence_records,
            }
        )
    payload = json.dumps(
        {"digest_schema": 1, "root": target, "claims": claims},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def has_alternate_path(
    requires: dict[str, list[str]], source: str, target: str
) -> bool:
    seen: set[str] = set()
    stack = [dependency for dependency in requires[source] if dependency != target]
    while stack:
        claim_id = stack.pop()
        if claim_id == target:
            return True
        if claim_id in seen:
            continue
        seen.add(claim_id)
        stack.extend(requires.get(claim_id, []))
    return False


def strict_findings(
    root: Path,
    requires: dict[str, list[str]],
    roots: list[str],
    ledger_claims: dict[str, dict[str, str | None]],
    evidence: dict[str, list[str]],
    root_digests: dict[str, str],
    verbose: bool = False,
    include_digests: bool = True,
) -> tuple[list[str], list[str], dict[str, str]]:
    errors = evidence_errors(root, evidence)
    warnings: list[str] = []

    invalid_labels = sorted(
        claim_id for claim_id, claim in ledger_claims.items() if claim["status"] is None
    )
    if invalid_labels:
        errors.append(
            "ledger claims have noncanonical status labels: "
            + ", ".join(invalid_labels)
        )

    unindexed = sorted(set(ledger_claims) - set(requires))
    if unindexed:
        if verbose:
            warnings.append(
                "unindexed ledger claims (allowed by the sparse schema): "
                + ", ".join(unindexed)
            )
        else:
            warnings.append(
                f"unindexed ledger claims: {len(unindexed)} "
                "(allowed by the sparse schema; use --verbose for IDs)"
            )

    redundant = sorted(
        f"{claim_id}->{dependency}"
        for claim_id, dependencies in requires.items()
        for dependency in dependencies
        if has_alternate_path(requires, claim_id, dependency)
    )
    if redundant:
        if verbose:
            warnings.append(
                "transitively implied edges "
                "(retain only when direct meaning matters): " + ", ".join(redundant)
            )
        else:
            warnings.append(
                f"transitively implied edges: {len(redundant)} "
                "(retain only when direct meaning matters; use --verbose for edges)"
            )

    current_digests: dict[str, str] = {}
    if not errors and include_digests:
        for root_id in roots:
            current = closure_digest(root, root_id, requires, ledger_claims, evidence)
            current_digests[root_id] = current
            recorded = root_digests.get(root_id)
            if recorded != current:
                state = "missing" if recorded is None else "stale"
                warnings.append(
                    f"root {root_id} closure digest is {state}; expected {current}"
                )
    return errors, warnings, current_digests


def readability_findings(
    ledger_claims: dict[str, dict[str, str | None]],
    verbose: bool = False,
) -> tuple[dict[str, int], list[str]]:
    """Report structural proxies only; do not judge mathematical vocabulary."""
    empty: list[str] = []
    oversized: list[str] = []
    mnemonic_ids = 0
    for claim_id, claim in ledger_claims.items():
        section = str(claim["section"])
        body = "\n".join(section.splitlines()[1:]).strip()
        if not body:
            empty.append(claim_id)
        if (
            len(section.splitlines()) > SHOW_MAX_LINES
            or len(section.encode("utf-8")) > SHOW_MAX_BYTES
        ):
            oversized.append(claim_id)
        if CLAIM_NUMBER.fullmatch(claim_id) and claim_id.count("-") == 2:
            mnemonic_ids += 1

    warnings: list[str] = []
    for label, claim_ids in (
        ("empty ledger claim sections", empty),
        ("oversized ledger claim sections", oversized),
    ):
        if not claim_ids:
            continue
        if verbose:
            warnings.append(f"{label}: " + ", ".join(claim_ids))
        else:
            warnings.append(
                f"{label}: {len(claim_ids)} "
                "(use --strict --readability --verbose for IDs)"
            )

    return (
        {
            "claims_checked": len(ledger_claims),
            "empty_sections": len(empty),
            "oversized_sections": len(oversized),
            "mnemonic_ids": mnemonic_ids,
        },
        warnings,
    )


def summarize_root(
    schema_version: Any,
    root: Path,
    target: str,
    requires: dict[str, list[str]],
    roots: list[str],
    ledger_claims: dict[str, dict[str, str | None]],
    evidence: dict[str, list[str]],
    root_digests: dict[str, str],
) -> dict[str, Any]:
    order = closure_order(requires, target)
    configured_root = target in roots
    status_counts = Counter(ledger_claims[claim_id]["status"] for claim_id in order)
    unresolved = [
        {"id": claim_id, "status": ledger_claims[claim_id]["status"]}
        for claim_id in order
        if ledger_claims[claim_id]["status"] != "Proved"
    ]
    closure_evidence = {
        claim_id: evidence[claim_id] for claim_id in order if claim_id in evidence
    }
    evidence_paths = sorted(
        {
            relative_path
            for paths in closure_evidence.values()
            for relative_path in paths
        }
    )
    evidence_problems = evidence_errors(root, closure_evidence)

    recorded_digest = root_digests.get(target)
    if not configured_root:
        digest_state = "untracked"
        expected_digest = None
    elif schema_version != 3:
        digest_state = "unsupported"
        expected_digest = None
    elif evidence_problems:
        digest_state = "unavailable"
        expected_digest = None
    else:
        current_digest = closure_digest(root, target, requires, ledger_claims, evidence)
        if recorded_digest is None:
            digest_state = "missing"
            expected_digest = current_digest
        elif recorded_digest != current_digest:
            digest_state = "stale"
            expected_digest = current_digest
        else:
            digest_state = "fresh"
            expected_digest = None

    return {
        "target": target,
        "target_title": ledger_claims[target]["title"],
        "configured_root": configured_root,
        "closure_size": len(order),
        "status_counts": dict(sorted(status_counts.items())),
        "unresolved": unresolved,
        "unresolved_titles": {
            item["id"]: ledger_claims[str(item["id"])]["title"]
            for item in unresolved
        },
        "evidence_files": len(evidence_paths),
        "digest_state": digest_state,
        "expected_digest": expected_digest,
        "evidence_errors": evidence_problems,
        "ready": (
            configured_root
            and schema_version == 3
            and not unresolved
            and not evidence_problems
            and digest_state == "fresh"
        ),
    }


def completion_errors(
    schema_version: Any,
    root: Path,
    requires: dict[str, list[str]],
    roots: list[str],
    ledger_claims: dict[str, dict[str, str | None]],
    evidence: dict[str, list[str]],
    root_digests: dict[str, str],
) -> tuple[list[str], dict[str, str]]:
    errors: list[str] = []
    current_digests: dict[str, str] = {}
    if not roots:
        return ["complete check requires at least one root"], current_digests
    if schema_version != 3:
        errors.append(
            "complete check requires schema_version 3 and reviewed root digests"
        )
    selected = {
        claim_id for root_id in roots for claim_id in closure_order(requires, root_id)
    }
    closure_evidence = {
        claim_id: evidence[claim_id] for claim_id in selected if claim_id in evidence
    }
    evidence_problems = evidence_errors(root, closure_evidence)
    errors.extend(evidence_problems)
    for root_id in roots:
        for claim_id in closure_order(requires, root_id):
            status = ledger_claims[claim_id]["status"]
            if status != "Proved":
                errors.append(
                    f"root {root_id} has unproved closure claim {claim_id}: {status}"
                )
        if not evidence_problems:
            current = closure_digest(root, root_id, requires, ledger_claims, evidence)
            current_digests[root_id] = current
            recorded = root_digests.get(root_id)
            if recorded != current:
                state = "missing" if recorded is None else "stale"
                errors.append(
                    f"root {root_id} closure digest is {state}; expected {current}"
                )
    return errors, current_digests


def impact(requires: dict[str, list[str]], source: str) -> tuple[list[str], list[str]]:
    if source not in requires:
        raise KeyError(f"unknown claim: {source}")
    reverse: dict[str, list[str]] = defaultdict(list)
    for claim_id, dependencies in requires.items():
        for dependency in dependencies:
            reverse[dependency].append(claim_id)
    direct = sorted(reverse[source])
    seen: set[str] = set()
    queue: deque[str] = deque(direct)
    while queue:
        claim_id = queue.popleft()
        if claim_id in seen:
            continue
        seen.add(claim_id)
        queue.extend(reverse[claim_id])
    return direct, sorted(seen)


def print_dot(
    requires: dict[str, list[str]],
    ledger_claims: dict[str, dict[str, str | None]],
    target: str | None,
) -> None:
    selected = set(closure_order(requires, target)) if target else set(requires)
    colors = {
        "Proved": "#b7e4c7",
        "Conditional": "#ffe8a1",
        "Open": "#dbeafe",
        "Rejected": "#fecaca",
        "Superseded": "#e5e7eb",
    }
    print("digraph research_claims {")
    print('  rankdir="LR";')
    for claim_id in sorted(selected):
        claim = ledger_claims[claim_id]
        title = str(claim["title"]).replace('"', r"\"")
        color = colors.get(str(claim["status"]), "white")
        print(
            f'  "{claim_id}" [label="{claim_id}\\n{title}", '
            f'style="filled", fillcolor="{color}"];'
        )
    for claim_id in sorted(selected):
        for dependency in requires[claim_id]:
            if dependency in selected:
                print(f'  "{dependency}" -> "{claim_id}";')
    print("}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        help="Research root (default: nearest parent containing the graph)",
    )
    parser.add_argument(
        "--graph",
        type=Path,
        help="Graph JSON path (default: ROOT/KEY_RESULTS.graph.json)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    init_parser = commands.add_parser(
        "init", help="Create minimal research-memory files without overwriting"
    )
    init_parser.add_argument(
        "--dry-run", action="store_true", help="Show files without creating them"
    )
    check_parser = commands.add_parser(
        "check", help="Validate ledger links, statuses, and DAG"
    )
    check_parser.add_argument(
        "--complete",
        action="store_true",
        help="Also require Proved, fresh schema-v3 root closures",
    )
    check_parser.add_argument(
        "--strict",
        action="store_true",
        help="Audit all ledger statuses, evidence paths, omissions, and sparse edges",
    )
    check_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Expand strict warning IDs and edges",
    )
    check_parser.add_argument(
        "--readability",
        action="store_true",
        help="Report non-blocking structural readability risks",
    )
    commands.add_parser(
        "next-id", help="Return the next append-only numeric claim ID"
    )
    find_parser = commands.add_parser(
        "find", help="Search claim IDs and titles with bounded output"
    )
    find_parser.add_argument("query")
    find_parser.add_argument(
        "--limit",
        type=bounded_find_limit,
        default=FIND_DEFAULT_LIMIT,
        help=f"Maximum matches to return (default: {FIND_DEFAULT_LIMIT})",
    )
    summary_parser = commands.add_parser(
        "summary", help="Summarize one indexed claim closure"
    )
    summary_parser.add_argument("target")
    show_parser = commands.add_parser(
        "show", help="Print one bounded exact ledger claim section"
    )
    show_parser.add_argument("claim")
    show_parser.add_argument(
        "--full", action="store_true", help="Allow an oversized claim section"
    )
    order_parser = commands.add_parser(
        "order", help="Show dependency-first closure order"
    )
    order_parser.add_argument("target")
    impact_parser = commands.add_parser(
        "impact", help="Show claims affected by changing one claim"
    )
    impact_parser.add_argument("claim")
    dot_parser = commands.add_parser("dot", help="Emit Graphviz DOT")
    dot_parser.add_argument("--target", help="Restrict to one claim's closure")
    args = parser.parse_args()
    if args.command == "check" and args.verbose and not args.strict:
        parser.error("--verbose requires --strict")

    root = resolve_root(args.root, args.graph)
    graph_path = resolve_graph(root, args.root, args.graph)

    try:
        if args.command == "init":
            initialize_memory(root, graph_path, args.dry_run)
            return 0

        data = load_graph(graph_path)
        (
            errors,
            warnings,
            requires,
            roots,
            ledger_claims,
            evidence,
            root_digests,
        ) = validate(data, root)
        if args.command == "check":
            current_digests: dict[str, str] = {}
            readability: dict[str, int] | None = None
            if args.strict and not errors:
                strict_errors, strict_warnings, current_digests = strict_findings(
                    root,
                    requires,
                    roots,
                    ledger_claims,
                    evidence,
                    root_digests,
                    args.verbose,
                    not args.complete,
                )
                errors.extend(strict_errors)
                warnings.extend(strict_warnings)
            if args.readability:
                readability, readability_warnings = readability_findings(
                    ledger_claims, args.verbose
                )
                warnings.extend(readability_warnings)
            if args.complete and not errors:
                completion_problems, current_digests = completion_errors(
                    data.get("schema_version"),
                    root,
                    requires,
                    roots,
                    ledger_claims,
                    evidence,
                    root_digests,
                )
                errors.extend(completion_problems)
            status_counts = Counter(
                ledger_claims[claim_id]["status"]
                for claim_id in requires
                if claim_id in ledger_claims
                and ledger_claims[claim_id]["status"] is not None
            )
            print_json(
                {
                    "ok": not errors,
                    "root": str(root),
                    "graph": str(graph_path),
                    "schema_version": data.get("schema_version"),
                    "complete": args.complete,
                    "strict": args.strict,
                    "verbose": args.verbose,
                    "readability": readability,
                    "roots": roots,
                    "current_root_digests": current_digests,
                    "claims": len(requires),
                    "requires_edges": sum(map(len, requires.values())),
                    "status_counts": dict(sorted(status_counts.items())),
                    "warnings": warnings,
                    "errors": errors,
                }
            )
            return 0 if not errors else 1
        if errors:
            print_json({"ok": False, "warnings": warnings, "errors": errors})
            return 1

        if args.command == "next-id":
            print_json({"next_id": next_claim_id(ledger_claims)})
        elif args.command == "find":
            matches, total = find_claims(args.query, ledger_claims, args.limit)
            print_json(
                {
                    "query": args.query,
                    "limit": args.limit,
                    "total_matches": total,
                    "truncated": total > args.limit,
                    "matches": matches,
                }
            )
        elif args.command == "summary":
            summary = summarize_root(
                data.get("schema_version"),
                root,
                args.target,
                requires,
                roots,
                ledger_claims,
                evidence,
                root_digests,
            )
            print_json(
                {
                    "root": str(root),
                    "graph": str(graph_path),
                    "warnings": warnings,
                    **summary,
                }
            )
            return 1 if summary["evidence_errors"] else 0
        elif args.command == "show":
            claim = ledger_claims.get(args.claim)
            if claim is None:
                raise KeyError(f"unknown ledger claim: {args.claim}")
            section = claim["section"]
            section_lines = len(section.splitlines())
            section_bytes = len(section.encode("utf-8"))
            if not args.full and (
                section_lines > SHOW_MAX_LINES or section_bytes > SHOW_MAX_BYTES
            ):
                raise ValueError(
                    f"claim {args.claim} is too large for bounded show "
                    f"({section_lines} lines, {section_bytes} bytes); "
                    "use targeted file ranges or rerun show --full deliberately"
                )
            print(section, end="")
        elif args.command == "order":
            order = closure_order(requires, args.target)
            print_json(
                {
                    "target": args.target,
                    "order": order,
                    "titles": {
                        claim_id: ledger_claims[claim_id]["title"]
                        for claim_id in order
                    },
                }
            )
        elif args.command == "impact":
            direct, transitive = impact(requires, args.claim)
            print_json(
                {
                    "claim": args.claim,
                    "claim_title": ledger_claims[args.claim]["title"],
                    "direct": direct,
                    "transitive": transitive,
                    "titles": {
                        claim_id: ledger_claims[claim_id]["title"]
                        for claim_id in transitive
                    },
                }
            )
        elif args.command == "dot":
            print_dot(requires, ledger_claims, args.target)
        return 0
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as error:
        print(f"research_graph: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
