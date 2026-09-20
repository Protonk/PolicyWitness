#!/usr/bin/env python3
"""Render the limits inventory and copy its shared section into the user guide.

References identify owners, not proof of values. Compiled C, Swift and Rust
tests compare implementation values with this manifest independently.
--check verifies both documents without writing. --stage-guide copies the
checked guide for distribution without regenerating stale documentation.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- BEGIN GENERATED LIMITS -->"
END = "<!-- END GENERATED LIMITS -->"
COVERAGE_START = "<!-- BEGIN GENERATED LIMIT COVERAGE -->"
COVERAGE_END = "<!-- END GENERATED LIMIT COVERAGE -->"
SHARED_START = "<!-- BEGIN SHARED LIMITS -->"
SHARED_END = "<!-- END SHARED LIMITS -->"
GUIDE_START = "<!-- BEGIN COPIED LIMITS -->"
GUIDE_END = "<!-- END COPIED LIMITS -->"
SECTIONS = {
    "admission": "Specimen admission",
    "execution": "Execution budgets",
    "transport": "Queries and transport",
    "evidence": "Evidence capture",
    "helper": "Diagnostic helpers",
}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_limits(path: Path, root: Path = ROOT):
    data = json.loads(path.read_text(), object_pairs_hook=unique_object)
    if set(data) != {"schema_version", "limits"} or data["schema_version"] != 1:
        raise ValueError("expected limits manifest schema_version 1")
    if not isinstance(data["limits"], list) or not data["limits"]:
        raise ValueError("limits must be a nonempty list")
    seen = set()
    fields = {"id", "section", "title", "value", "unit", "counting", "effect",
              "control", "sources", "checks", "behavior"}
    for item in data["limits"]:
        if set(item) != fields:
            raise ValueError(f"unexpected/missing fields: {item.get('id')}")
        ident = item["id"]
        if not re.fullmatch(r"[a-z][a-z0-9_]*", ident) or ident in seen:
            raise ValueError(f"invalid/duplicate limit id: {ident}")
        seen.add(ident)
        if type(item["value"]) is not int or item["value"] <= 0:
            raise ValueError(f"{ident}: value must be a positive integer")
        if item["section"] not in SECTIONS:
            raise ValueError(f"{ident}: unknown section")
        if item["unit"] not in {"UTF-8 bytes", "bytes", "items", "milliseconds", "levels", "records"}:
            raise ValueError(f"{ident}: unknown unit")
        for key in ("title", "counting", "effect", "control", "behavior"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError(f"{ident}: empty {key}")
        for key in ("sources", "checks"):
            if not isinstance(item[key], list) or not item[key]:
                raise ValueError(f"{ident}: missing {key}")
            for ref in item[key]:
                expected = {"path", "symbol", "kind"} if key == "checks" else {"path", "symbol"}
                if set(ref) != expected:
                    raise ValueError(f"{ident}: malformed {key} reference")
                path = Path(ref["path"])
                if path.is_absolute() or ".." in path.parts or not (root / path).is_file():
                    raise ValueError(f"{ident}: missing/invalid reference {path}")
                if not ref["symbol"] or ref["symbol"] not in (root / path).read_text():
                    raise ValueError(f"{ident}: missing symbol {ref['symbol']} in {path}")
                if key == "checks" and ref["kind"] not in {"value", "boundary", "path"}:
                    raise ValueError(f"{ident}: unknown check kind")
        if not any(ref["kind"] == "value" for ref in item["checks"]):
            raise ValueError(f"{ident}: no implementation-value check owner")
    if {item["section"] for item in data["limits"]} != set(SECTIONS):
        raise ValueError("each documented section needs entries")
    return data["limits"]


def cell(text):
    return text.replace("|", "\\|").replace("\n", " ")


def reference(ref):
    # Repository-relative paths in JSON become document-relative links here.
    return f"[`{ref['symbol']}`](../{ref['path']})"


def render(limits):
    lines = [START, "", "Values are maxima unless labelled as defaults."]
    for section, title in SECTIONS.items():
        lines += ["", f"## {title}", "", "| Limit | Value | Counting and consequence | Control |",
                  "| --- | --- | --- | --- |"]
        for item in limits:
            if item["section"] != section:
                continue
            lines.append("| " + " | ".join(map(cell, [
                f"{item['title']} (`{item['id']}`)",
                f"{item['value']:,} {item['unit']}",
                item['counting'] + " " + item['effect'], item['control']])) + " |")
    return "\n".join(lines) + "\n\n" + END


def render_coverage(limits):
    lines = [COVERAGE_START, "", "## Grounding and coverage", "",
              "Value checks compare the inventory with compiled constants, constructed defaults or actual returned bytes. Boundary checks exercise a limit and its consequence; path checks cover related behavior without proving the exact boundary. A source reference alone is not a value check. Coverage notes below identify where behavior remains source-inspected.", "",
              "| Limit ID | Implementation | Permanent checks | Behavioral coverage |",
              "| --- | --- | --- | --- |"]
    for item in limits:
        lines.append("| " + " | ".join(map(cell, [f"`{item['id']}`",
            "; ".join(reference(ref) for ref in item['sources']),
            "; ".join(f"{ref['kind']}: {reference(ref)}" for ref in item['checks']),
            item['behavior']])) + " |")
    return "\n".join(lines) + "\n\n" + COVERAGE_END


def block_bounds(text, start, end):
    if text.count(start) != 1 or text.count(end) != 1 or text.index(end) < text.index(start):
        raise ValueError(f"expected exactly one ordered block: {start} ... {end}")
    return text.index(start), text.index(end) + len(end)


def replace_block(text, start, end, replacement):
    begin, finish = block_bounds(text, start, end)
    return text[:begin] + replacement + text[finish:]


def update_document(text, limits):
    text = replace_block(text, START, END, render(limits))
    return replace_block(text, COVERAGE_START, COVERAGE_END, render_coverage(limits))


def update_guide(text, limits_document):
    begin, finish = block_bounds(limits_document, SHARED_START, SHARED_END)
    shared = limits_document[begin + len(SHARED_START):finish - len(SHARED_END)].strip()
    # The source uses level-two headings; nest them under the guide's Limits
    # heading. All explanatory prose and table contents are copied verbatim.
    shared = re.sub(r"^## ", "### ", shared, flags=re.MULTILINE)
    return replace_block(text, GUIDE_START, GUIDE_END,
                         GUIDE_START + "\n\n" + shared + "\n\n" + GUIDE_END)


def prose_lines(text):
    """Ignore fenced examples when inspecting this guide's Markdown links."""
    fence = None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            delimiter = match.group(1)
            if fence is None:
                fence = delimiter
            elif delimiter[0] == fence[0] and len(delimiter) >= len(fence):
                fence = None
        elif fence is None:
            yield line


def validate_guide(text, limits):
    """Check the standalone text; never resolve links against repository files."""
    begin, finish = block_bounds(text, GUIDE_START, GUIDE_END)
    copied = text[begin + len(GUIDE_START):finish - len(GUIDE_END)]
    for item in limits:
        if copied.count(f"(`{item['id']}`)") != 1:
            raise ValueError(f"guide must contain exactly one limits row: {item['id']}")
    # The shared section uses inline links only, and must need no companion
    # files or web pages. Reject reference links/definitions rather than
    # assuming they can be resolved in a standalone release asset.
    prose = "\n".join(prose_lines(copied))
    if re.search(r"\]\s*\[|^\s*\[[^]\n]+\]:|<https?://", prose, re.MULTILINE):
        raise ValueError("copied limits must use inline internal links only")
    for target in re.findall(r"\]\(([^)]+)\)", prose):
        if not target.startswith("#"):
            raise ValueError(f"copied limits depend on another document: {target}")

    # Headings in this guide use ATX syntax. Match the punctuation-stripped
    # anchors used by its Markdown links, including duplicate-heading suffixes.
    anchors = set()
    prose = "\n".join(prose_lines(text))
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", prose, re.MULTILINE):
        base = re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")
        anchor = base
        suffix = 0
        while anchor in anchors:
            suffix += 1
            anchor = f"{base}-{suffix}"
        anchors.add(anchor)
    if "limits" not in anchors:
        raise ValueError("guide is missing its Limits heading")
    for target in re.findall(r"\]\((#[^)]+)\)", prose):
        if target[1:] not in anchors:
            raise ValueError(f"guide has an unresolved internal link: {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check both documents; do not write")
    mode.add_argument("--stage-guide", type=Path, metavar="PATH",
                      help="check both documents, then copy the guide to PATH")
    args = parser.parse_args()
    path = ROOT / "docs/LIMITS.md"
    guide_path = ROOT / "docs/PolicyWitness.md"
    try:
        limits = load_limits(ROOT / "docs/limits.json")
        before = path.read_text()
        after = update_document(before, limits)
        # Derive the copy from the freshly rendered source, even when the
        # on-disk tables were stale. Validate both inputs before any writes.
        guide_bytes = guide_path.read_bytes()
        guide_before = guide_bytes.decode("utf-8")
        guide_after = update_guide(guide_before, after)
        validate_guide(guide_after, limits)
        if args.check or args.stage_guide is not None:
            stale = [name for name, old, new in [
                ("LIMITS.md", before, after), ("PolicyWitness.md", guide_before, guide_after)]
                if old != new]
            if stale:
                raise ValueError(f"stale {', '.join(stale)}; run python3 docs/generate_limits.py")
            if args.stage_guide is not None:
                args.stage_guide.write_bytes(guide_bytes)
        else:
            if before != after:
                path.write_text(after)
            if guide_before != guide_after:
                guide_path.write_text(guide_after)
        print(f"ok: {len(limits)} limits; " +
              (f"guide staged at {args.stage_guide}" if args.stage_guide is not None else
               "both documents current" if args.check else "LIMITS.md generated and guide copy updated"))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        print(f"limits: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
