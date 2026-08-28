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
SHOW_MAX_LINES = 200
SHOW_MAX_BYTES = 16 * 1024
LOG_SHOW_MAX_LINES = 160
LOG_SHOW_MAX_BYTES = 12 * 1024
RESTART_MAX_LINES = 40
RESTART_MAX_BYTES = 6 * 1024
RESUME_MAX_BYTES = 12 * 1024
RESUME_UNRESOLVED_LIMIT = 8
LIST_MAX_BYTES = 12 * 1024
LIST_DEFAULT_LIMIT = 50
LIST_MAX_LIMIT = 100
FIND_DEFAULT_LIMIT = 20
FIND_MAX_LIMIT = 100
RESEARCH_LOG = "RESEARCH_LOG.md"
RESTART_HEADING = "Current restart point"
CLAIM_TOKEN = r"KR-[0-9]+(?:-[A-Z][A-Z0-9]*)?"
CLAIM_ID = re.compile(rf"{CLAIM_TOKEN}$")
CLAIM_REFERENCE = re.compile(
    r"(?<![A-Za-z0-9_])KR-[0-9]+(?:-[A-Za-z0-9]+)*(?![A-Za-z0-9_-])"
)
CLAIM_NUMBER = re.compile(r"KR-([0-9]+)(?:-[A-Z][A-Z0-9]*)?$")
SHA256_DIGEST = re.compile(r"sha256:[0-9a-f]{64}$")
HEADING = re.compile(
    r"^###\s+(KR-\S+)\s+[—-]\s+(.+?)\s+\[([^\]]+)\]\s*$",
)
TOP_LEVEL_BOUNDARY = re.compile(r"^#{1,2}\s+")
LOG_HEADING = re.compile(r"^##\s+(.+?)\s*$")
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


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


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


def render_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def print_json(value: Any) -> None:
    print(render_json(value), end="")


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


def bounded_list_limit(value: str) -> int:
    try:
        limit = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("limit must be an integer") from error
    if not 1 <= limit <= LIST_MAX_LIMIT:
        raise argparse.ArgumentTypeError(
            f"limit must be between 1 and {LIST_MAX_LIMIT}"
        )
    return limit


def line_range(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([1-9][0-9]*):([1-9][0-9]*)", value)
    if match is None:
        raise argparse.ArgumentTypeError("range must have the form START:END")
    start, end = map(int, match.groups())
    if end < start:
        raise argparse.ArgumentTypeError("range END must not precede START")
    if end - start + 1 > SHOW_MAX_LINES:
        raise argparse.ArgumentTypeError(
            f"range may contain at most {SHOW_MAX_LINES} lines"
        )
    return start, end


def unique_claim_references(text: str) -> list[str]:
    return list(dict.fromkeys(CLAIM_REFERENCE.findall(text)))


def resolve_claim_references(
    text: str,
    ledger_claims: dict[str, dict[str, str | None]],
) -> tuple[list[str], list[str], dict[str, str], dict[str, list[str]]]:
    raw_references = unique_claim_references(text)
    by_number: dict[str, list[str]] = defaultdict(list)
    for claim_id in ledger_claims:
        match = CLAIM_NUMBER.fullmatch(claim_id)
        if match is not None:
            by_number[match.group(1)].append(claim_id)

    resolved: list[str] = []
    unknown: list[str] = []
    aliases: dict[str, str] = {}
    ambiguous: dict[str, list[str]] = {}
    for reference in raw_references:
        canonical: str | None = None
        if reference in ledger_claims:
            canonical = reference
        elif reference.count("-") == 1:
            match = CLAIM_NUMBER.fullmatch(reference)
            candidates = (
                by_number.get(match.group(1), [])
                if match is not None
                else []
            )
            if len(candidates) == 1:
                canonical = candidates[0]
                aliases[reference] = canonical
            elif len(candidates) > 1:
                ambiguous[reference] = sorted(candidates)
        if canonical is None:
            if reference not in ambiguous:
                unknown.append(reference)
            continue
        if canonical not in resolved:
            resolved.append(canonical)
    return resolved, unknown, aliases, ambiguous


def section_measure(section: str) -> tuple[int, int]:
    return len(section.splitlines()), len(section.encode("utf-8"))


def exact_line_slice(
    section: str,
    selected: tuple[int, int] | None,
    max_lines: int,
    max_bytes: int,
    label: str,
    allow_full: bool,
) -> str:
    lines = section.splitlines(keepends=True)
    total_lines, total_bytes = section_measure(section)
    if selected is None:
        chosen = section
        chosen_lines = total_lines
        chosen_bytes = total_bytes
    else:
        start, end = selected
        if start > total_lines:
            raise ValueError(
                f"{label} range starts after its final line {total_lines}"
            )
        if end > total_lines:
            raise ValueError(
                f"{label} range ends after its final line {total_lines}"
            )
        chosen = "".join(lines[start - 1 : end])
        chosen_lines, chosen_bytes = section_measure(chosen)
    if not allow_full and (chosen_lines > max_lines or chosen_bytes > max_bytes):
        raise ValueError(
            f"{label} is too large for bounded show/output "
            f"({chosen_lines} lines, {chosen_bytes} bytes; full section "
            f"{total_lines} lines, {total_bytes} bytes); use a smaller --range "
            "or rerun with --full deliberately"
        )
    return chosen


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
        value = json.load(handle, object_pairs_hook=unique_object)
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


def load_research_log(root: Path) -> tuple[str, list[dict[str, Any]]]:
    path = (root / RESEARCH_LOG).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"research log escapes research root: {RESEARCH_LOG}") from error
    if not path.is_file():
        raise FileNotFoundError(f"research log does not exist: {RESEARCH_LOG}")
    text = path.read_text(encoding="utf-8")
    headings: list[tuple[int, int, str]] = []
    fence: tuple[str, int] | None = None
    offset = 0
    line_number = 1
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
        else:
            opening = FENCE_OPEN.fullmatch(content)
            if opening is not None:
                marker, info = opening.groups()
                if marker[0] == "~" or "`" not in info:
                    fence = (marker[0], len(marker))
            else:
                heading = LOG_HEADING.fullmatch(content)
                if heading is not None:
                    headings.append((offset, line_number, heading.group(1).strip()))
        offset += len(line)
        line_number += 1

    sections: list[dict[str, Any]] = []
    for index, (start, heading_line, title) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(text)
        sections.append(
            {
                "line": heading_line,
                "title": title,
                "section": text[start:end],
            }
        )
    return text, sections


def restart_section(log_sections: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [item for item in log_sections if item["title"] == RESTART_HEADING]
    if not matches:
        raise ValueError(f"research log has no '## {RESTART_HEADING}' section")
    if len(matches) != 1:
        lines = ", ".join(str(item["line"]) for item in matches)
        raise ValueError(
            f"research log has multiple '## {RESTART_HEADING}' sections at lines "
            + lines
        )
    return matches[0]


def find_log_sections(
    query: str,
    sections: list[dict[str, Any]],
    ledger_claims: dict[str, dict[str, str | None]],
    limit: int,
) -> tuple[list[dict[str, Any]], int]:
    terms = query.casefold().split()
    if not terms:
        raise ValueError("log-find query must contain a non-whitespace character")
    matches: list[dict[str, Any]] = []
    total = 0
    for item in sections:
        section = str(item["section"])
        if all(term in section.casefold() for term in terms):
            total += 1
            if len(matches) < limit:
                references, unknown, aliases, ambiguous = resolve_claim_references(
                    section, ledger_claims
                )
                matches.append(
                    {
                        "line": item["line"],
                        "title": item["title"],
                        "claim_references": references,
                        "legacy_aliases": aliases,
                        "unknown_claim_references": unknown,
                        "ambiguous_claim_references": ambiguous,
                    }
                )
    return matches, total


def select_log_section(
    sections: list[dict[str, Any]], heading: str | None, heading_line: int | None
) -> dict[str, Any]:
    if heading_line is not None:
        matches = [item for item in sections if item["line"] == heading_line]
        if not matches:
            raise KeyError(f"no research-log section begins at line {heading_line}")
        return matches[0]
    assert heading is not None
    matches = [item for item in sections if item["title"] == heading]
    if not matches:
        raise KeyError(f"unknown research-log heading: {heading}")
    if len(matches) != 1:
        lines = ", ".join(str(item["line"]) for item in matches)
        raise ValueError(
            f"research-log heading is ambiguous at lines {lines}; use --line"
        )
    return matches[0]


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


def compact_root_summary(
    root_id: str,
    requires: dict[str, list[str]],
    ledger_claims: dict[str, dict[str, str | None]],
) -> dict[str, Any]:
    order = closure_order(requires, root_id)
    status_counts = Counter(ledger_claims[claim_id]["status"] for claim_id in order)
    unresolved_all = [
        {
            "id": claim_id,
            "title": ledger_claims[claim_id]["title"],
            "status": ledger_claims[claim_id]["status"],
        }
        for claim_id in order
        if ledger_claims[claim_id]["status"] != "Proved"
    ]
    unresolved = unresolved_all[:RESUME_UNRESOLVED_LIMIT]
    return {
        "id": root_id,
        "title": ledger_claims[root_id]["title"],
        "status": ledger_claims[root_id]["status"],
        "closure_size": len(order),
        "status_counts": dict(sorted(status_counts.items())),
        "unresolved_total": len(unresolved_all),
        "unresolved_truncated": len(unresolved) < len(unresolved_all),
        "unresolved": unresolved,
    }


def payload_with_size(value: dict[str, Any]) -> tuple[dict[str, Any], int]:
    payload = dict(value)
    payload["output_bytes"] = 0
    for _ in range(4):
        size = len(render_json(payload).encode("utf-8"))
        if payload["output_bytes"] == size:
            return payload, size
        payload["output_bytes"] = size
    size = len(render_json(payload).encode("utf-8"))
    payload["output_bytes"] = size
    return payload, len(render_json(payload).encode("utf-8"))


def build_resume_payload(
    root: Path,
    graph_path: Path,
    roots: list[str],
    requires: dict[str, list[str]],
    ledger_claims: dict[str, dict[str, str | None]],
    restart: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    restart_text = str(restart["section"])
    references, unknown, aliases, ambiguous = resolve_claim_references(
        restart_text, ledger_claims
    )
    if unknown or ambiguous:
        raise ValueError("cannot build resume payload from unresolved claim references")
    payload = {
        "root": str(root),
        "graph": str(graph_path),
        "restart": {
            "line": restart["line"],
            "lines": section_measure(restart_text)[0],
            "bytes": section_measure(restart_text)[1],
            "text": restart_text,
        },
        "roots": [
            compact_root_summary(root_id, requires, ledger_claims)
            for root_id in roots
        ],
        "referenced_claims": [
            {
                "id": claim_id,
                "title": ledger_claims[claim_id]["title"],
                "status": ledger_claims[claim_id]["status"],
                "indexed": claim_id in requires,
            }
            for claim_id in references
            if claim_id in ledger_claims
        ],
        "legacy_aliases": aliases,
    }
    return payload_with_size(payload)


def memory_findings(
    root: Path,
    graph_path: Path,
    ledger_name: str,
    roots: list[str],
    requires: dict[str, list[str]],
    ledger_claims: dict[str, dict[str, str | None]],
    log_text: str,
    log_sections: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str], list[str], dict[str, Any] | None]:
    errors: list[str] = []
    warnings: list[str] = []
    restart = restart_section(log_sections)
    restart_text = str(restart["section"])
    restart_lines, restart_bytes = section_measure(restart_text)
    references, unknown_references, aliases, ambiguous_references = (
        resolve_claim_references(restart_text, ledger_claims)
    )
    unknown_references = sorted(unknown_references)
    missing_roots = sorted(set(roots) - set(references))

    if restart_lines > RESTART_MAX_LINES:
        errors.append(
            f"restart point has {restart_lines} lines; maximum is "
            f"{RESTART_MAX_LINES}"
        )
    if restart_bytes > RESTART_MAX_BYTES:
        errors.append(
            f"restart point has {restart_bytes} bytes; maximum is "
            f"{RESTART_MAX_BYTES}"
        )
    if unknown_references:
        errors.append(
            "restart point references unknown claims: "
            + ", ".join(unknown_references)
        )
    if ambiguous_references:
        errors.append(
            "restart point has ambiguous numeric claim references: "
            + "; ".join(
                f"{reference} -> {', '.join(candidates)}"
                for reference, candidates in sorted(ambiguous_references.items())
            )
        )
    if missing_roots:
        errors.append(
            "restart point does not reference configured roots: "
            + ", ".join(missing_roots)
        )
    if not references and roots:
        warnings.append("restart point contains no claim references")

    resume_payload: dict[str, Any] | None = None
    resume_bytes: int | None = None
    if not unknown_references and not ambiguous_references and not missing_roots:
        resume_payload, resume_bytes = build_resume_payload(
            root,
            graph_path,
            roots,
            requires,
            ledger_claims,
            restart,
        )
        if resume_bytes > RESUME_MAX_BYTES:
            errors.append(
                f"projected resume output has {resume_bytes} bytes; maximum is "
                f"{RESUME_MAX_BYTES}"
            )

    ledger_text = (root / ledger_name).read_text(encoding="utf-8")
    ledger_lines, ledger_bytes = section_measure(ledger_text)
    log_lines, log_bytes = section_measure(log_text)
    report = {
        "ledger": {"lines": ledger_lines, "bytes": ledger_bytes},
        "research_log": {
            "lines": log_lines,
            "bytes": log_bytes,
            "sections": len(log_sections),
            "event_sections": sum(
                1 for item in log_sections if item["title"] != RESTART_HEADING
            ),
        },
        "restart": {
            "line": restart["line"],
            "lines": restart_lines,
            "bytes": restart_bytes,
            "max_lines": RESTART_MAX_LINES,
            "max_bytes": RESTART_MAX_BYTES,
            "claim_references": references,
            "legacy_aliases": aliases,
            "unknown_claim_references": unknown_references,
            "ambiguous_claim_references": ambiguous_references,
            "missing_root_references": missing_roots,
        },
        "projected_resume_bytes": resume_bytes,
        "max_resume_bytes": RESUME_MAX_BYTES,
    }
    return report, errors, warnings, resume_payload


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


def bounded_order_payload(
    target: str,
    order: list[str],
    ledger_claims: dict[str, dict[str, str | None]],
    limit: int,
) -> dict[str, Any]:
    selected = order[:limit]
    while True:
        payload = {
            "target": target,
            "target_title": ledger_claims[target]["title"],
            "limit": limit,
            "total": len(order),
            "truncated": len(selected) < len(order),
            "order": selected,
            "titles": {
                claim_id: ledger_claims[claim_id]["title"]
                for claim_id in selected
            },
        }
        if len(render_json(payload).encode("utf-8")) <= LIST_MAX_BYTES:
            return payload
        if not selected:
            raise ValueError(
                f"order metadata exceeds the {LIST_MAX_BYTES}-byte output budget"
            )
        selected.pop()


def bounded_impact_payload(
    claim_id: str,
    direct: list[str],
    transitive: list[str],
    ledger_claims: dict[str, dict[str, str | None]],
    limit: int,
) -> dict[str, Any]:
    ordered = direct + [item for item in transitive if item not in set(direct)]
    selected = ordered[:limit]
    direct_set = set(direct)
    while True:
        selected_direct = [item for item in selected if item in direct_set]
        payload = {
            "claim": claim_id,
            "claim_title": ledger_claims[claim_id]["title"],
            "limit": limit,
            "direct_total": len(direct),
            "transitive_total": len(transitive),
            "truncated": len(selected) < len(ordered),
            "direct": selected_direct,
            "transitive": selected,
            "titles": {
                item: ledger_claims[item]["title"] for item in selected
            },
        }
        if len(render_json(payload).encode("utf-8")) <= LIST_MAX_BYTES:
            return payload
        if not selected:
            raise ValueError(
                f"impact metadata exceeds the {LIST_MAX_BYTES}-byte output budget"
            )
        selected.pop()


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
    check_parser.add_argument(
        "--memory",
        action="store_true",
        help="Validate the bounded restart point and projected resume output",
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
    show_parser.add_argument(
        "--range",
        dest="line_range",
        type=line_range,
        help="Print exact claim-relative lines START:END",
    )
    commands.add_parser(
        "resume", help="Emit one bounded exact restart package"
    )
    log_find_parser = commands.add_parser(
        "log-find", help="Search log headings, claim references, and exact terms"
    )
    log_find_parser.add_argument("query")
    log_find_parser.add_argument(
        "--limit",
        type=bounded_find_limit,
        default=FIND_DEFAULT_LIMIT,
        help=f"Maximum matches to return (default: {FIND_DEFAULT_LIMIT})",
    )
    log_show_parser = commands.add_parser(
        "log-show", help="Print one bounded exact research-log section"
    )
    log_selector = log_show_parser.add_mutually_exclusive_group(required=True)
    log_selector.add_argument("--heading", help="Exact level-two log heading text")
    log_selector.add_argument(
        "--line", type=int, dest="heading_line", help="Heading line from log-find"
    )
    log_show_parser.add_argument(
        "--full", action="store_true", help="Allow an oversized log section"
    )
    log_show_parser.add_argument(
        "--range",
        dest="line_range",
        type=line_range,
        help="Print exact section-relative lines START:END",
    )
    order_parser = commands.add_parser(
        "order", help="Show dependency-first closure order"
    )
    order_parser.add_argument("target")
    order_parser.add_argument(
        "--limit",
        type=bounded_list_limit,
        default=LIST_DEFAULT_LIMIT,
        help=f"Maximum claim rows to return (default: {LIST_DEFAULT_LIMIT})",
    )
    impact_parser = commands.add_parser(
        "impact", help="Show claims affected by changing one claim"
    )
    impact_parser.add_argument("claim")
    impact_parser.add_argument(
        "--limit",
        type=bounded_list_limit,
        default=LIST_DEFAULT_LIMIT,
        help=f"Maximum affected claim rows to return (default: {LIST_DEFAULT_LIMIT})",
    )
    dot_parser = commands.add_parser("dot", help="Emit Graphviz DOT")
    dot_parser.add_argument("--target", help="Restrict to one claim's closure")
    args = parser.parse_args()
    if args.command == "check" and args.verbose and not args.strict:
        parser.error("--verbose requires --strict")
    if args.command in {"show", "log-show"} and args.full and args.line_range:
        parser.error("--full and --range are mutually exclusive")
    if args.command == "log-show" and args.heading_line is not None:
        if args.heading_line < 1:
            parser.error("--line must be positive")

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
            memory: dict[str, Any] | None = None
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
            if args.memory:
                try:
                    log_text, log_sections = load_research_log(root)
                    memory, memory_errors, memory_warnings, _ = memory_findings(
                        root,
                        graph_path,
                        str(data.get("ledger", "KEY_RESULTS.md")),
                        roots,
                        requires,
                        ledger_claims,
                        log_text,
                        log_sections,
                    )
                    errors.extend(memory_errors)
                    warnings.extend(memory_warnings)
                except (OSError, ValueError) as error:
                    errors.append(str(error))
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
                    "memory": memory,
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
            section = exact_line_slice(
                str(claim["section"]),
                args.line_range,
                SHOW_MAX_LINES,
                SHOW_MAX_BYTES,
                f"claim {args.claim}",
                args.full,
            )
            print(section, end="")
        elif args.command == "resume":
            log_text, log_sections = load_research_log(root)
            _, memory_errors, _, resume_payload = memory_findings(
                root,
                graph_path,
                str(data.get("ledger", "KEY_RESULTS.md")),
                roots,
                requires,
                ledger_claims,
                log_text,
                log_sections,
            )
            if memory_errors:
                raise ValueError("; ".join(memory_errors))
            assert resume_payload is not None
            print_json(resume_payload)
        elif args.command == "log-find":
            _, log_sections = load_research_log(root)
            matches, total = find_log_sections(
                args.query, log_sections, ledger_claims, args.limit
            )
            payload = {
                "query": args.query,
                "limit": args.limit,
                "total_matches": total,
                "truncated": total > len(matches),
                "matches": matches,
            }
            while (
                len(render_json(payload).encode("utf-8")) > LIST_MAX_BYTES
                and payload["matches"]
            ):
                payload["matches"].pop()
                payload["truncated"] = True
            if len(render_json(payload).encode("utf-8")) > LIST_MAX_BYTES:
                raise ValueError(
                    f"log-find metadata exceeds the {LIST_MAX_BYTES}-byte budget"
                )
            print_json(payload)
        elif args.command == "log-show":
            _, log_sections = load_research_log(root)
            item = select_log_section(
                log_sections, args.heading, args.heading_line
            )
            section = exact_line_slice(
                str(item["section"]),
                args.line_range,
                LOG_SHOW_MAX_LINES,
                LOG_SHOW_MAX_BYTES,
                f"research-log section at line {item['line']}",
                args.full,
            )
            print(section, end="")
        elif args.command == "order":
            order = closure_order(requires, args.target)
            print_json(
                bounded_order_payload(
                    args.target, order, ledger_claims, args.limit
                )
            )
        elif args.command == "impact":
            direct, transitive = impact(requires, args.claim)
            print_json(
                bounded_impact_payload(
                    args.claim,
                    direct,
                    transitive,
                    ledger_claims,
                    args.limit,
                )
            )
        elif args.command == "dot":
            print_dot(requires, ledger_claims, args.target)
        return 0
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as error:
        print(f"research_graph: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
