#!/usr/bin/env python3
"""One-off record validation: structure, counts and frozen-source quotations.

This checks transcription, not the semantic classifications or completeness.
Run from the repository root with one or more inventory/review JSON paths.
"""
import collections
import functools
import json
from pathlib import Path
import subprocess
import sys


@functools.lru_cache(None)
def source(revision, path):
    return subprocess.check_output(
        ["git", "show", f"{revision}:{path}"], text=True
    ).splitlines(keepends=True)


def verify(path):
    data = json.loads(Path(path).read_text())
    revision = data["revision"]
    errors = []
    quote_count = 0

    def walk(value, location):
        nonlocal quote_count
        if isinstance(value, dict):
            if {"path", "start_line", "end_line", "quote"} <= value.keys():
                quote_count += 1
                try:
                    lines = source(revision, value["path"])
                    start, end = value["start_line"], value["end_line"]
                    if not (isinstance(start, int) and isinstance(end, int)
                            and 1 <= start <= end <= len(lines)):
                        raise ValueError("invalid line range")
                    if not value["quote"] or value["quote"] not in "".join(lines[start - 1:end]):
                        raise ValueError("quote is not an exact substring of line range")
                except (ValueError, subprocess.CalledProcessError) as exc:
                    errors.append(f"{location}: {exc}")
            for key, item in value.items():
                walk(item, f"{location}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{location}[{index}]")

    walk(data, "root")
    rows = data.get("entries", data.get("decisions", []))
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate row IDs")
    counts = collections.Counter()
    for row in rows:
        ident = row["id"]
        bucket, split = row.get("bucket"), row.get("split")
        if bucket not in {"A1", "B1"}:
            errors.append(f"{ident}: invalid bucket")
        if (bucket == "A1" and split is not None) or (bucket == "B1" and split not in {"C2", "D2"}):
            errors.append(f"{ident}: invalid split")
        if row.get("confidence") not in {"high", "medium", "low"}:
            errors.append(f"{ident}: invalid confidence")
        if split == "C2" and (not row.get("trigger") or row["trigger"]["path"] != "docs/WORKER.md"):
            errors.append(f"{ident}: missing WORKER trigger")
        if "entries" in data:
            required = {"id", "layer", "path", "start_line", "end_line", "quote", "context", "proposition", "bucket", "secondary_role", "rationale", "confidence", "inference_blocked", "split", "trigger", "external_origin", "duplicates", "notes"}
            if not required <= row.keys():
                errors.append(f"{ident}: missing fields {sorted(required - row.keys())}")
            if bucket == "B1" and not row.get("inference_blocked"):
                errors.append(f"{ident}: missing blocked inference")
            if split == "D2" and (not isinstance(row.get("external_origin"), dict) or row["external_origin"].get("status") not in {"identified", "hypothesized", "unknown"}):
                errors.append(f"{ident}: missing external-origin status")
        counts[f"{row.get('layer', 'review')}:{bucket}:{split or '-'}"] += 1
    return {"path": str(path), "revision": revision, "rows": len(rows),
            "quoted_references": quote_count, "counts": dict(sorted(counts.items())),
            "errors": errors, "passed": not errors}


if __name__ == "__main__":
    results = [verify(path) for path in sys.argv[1:]]
    print(json.dumps(results, indent=2))
    sys.exit(0 if results and all(result["passed"] for result in results) else 1)
