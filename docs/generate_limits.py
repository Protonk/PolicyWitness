#!/usr/bin/env python3
"""Render the reviewed limits inventory; --check is read-only.

References identify owners, not proof of values. Compiled C, Swift and Rust
tests compare implementation values with this manifest independently.
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
    lines = [START, "", "Generated from [limits.json](limits.json). Values are maxima unless labelled as defaults."]
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
    lines += ["", "## Grounding and coverage", "",
              "Value checks compare the inventory with compiled constants, constructed defaults or actual returned bytes. Boundary checks exercise a limit and its consequence; path checks cover related behavior without proving the exact boundary. A source reference alone is not a value check. Coverage notes below identify where behavior remains source-inspected.", "",
              "| Limit ID | Implementation | Permanent checks | Behavioral coverage |",
              "| --- | --- | --- | --- |"]
    for item in limits:
        lines.append("| " + " | ".join(map(cell, [f"`{item['id']}`",
            "; ".join(reference(ref) for ref in item['sources']),
            "; ".join(f"{ref['kind']}: {reference(ref)}" for ref in item['checks']),
            item['behavior']])) + " |")
    return "\n".join(lines) + "\n\n" + END


def update_document(text, limits):
    if text.count(START) != 1 or text.count(END) != 1 or text.index(END) < text.index(START):
        raise ValueError("LIMITS.md must contain exactly one ordered generated block")
    start, end = text.index(START), text.index(END) + len(END)
    return text[:start] + render(limits) + text[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail on stale tables; do not write")
    args = parser.parse_args()
    path = ROOT / "docs/LIMITS.md"
    try:
        limits = load_limits(ROOT / "docs/limits.json")
        before = path.read_text()
        after = update_document(before, limits)
        if args.check and before != after:
            raise ValueError("stale LIMITS.md; run python3 docs/generate_limits.py")
        if not args.check and before != after:
            path.write_text(after)
        print(f"ok: {len(limits)} limits; document {'current' if args.check else 'generated'}")
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        print(f"limits: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
