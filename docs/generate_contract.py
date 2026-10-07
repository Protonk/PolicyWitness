#!/usr/bin/env python3
"""Copy the wire contract versions from docs/contract.json into code and docs.

contract.json is the only hand-edited copy of these numbers. Every other copy
sits inside a marked region that this script rewrites, so a version change is
one edit to the JSON plus one regeneration. --check verifies every region
without writing. Nothing loads the JSON at run time: each language reads its
own generated copy, and tests compare those copies with the manifest.

Generator invariants (tests/suites/source_drift/README.md): G1 gives each
marked region one owner and preserves all other bytes; malformed pairs stop
before any write. G2 makes regeneration idempotent. G3 makes --check read-only,
nonzero for stale copies, and mandatory before signing. G4 checks the copies'
source references; G6 keeps the owning manifest independent of its outputs.
G11's shared drift rule verifies symbol-form prose links and heading anchors.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "docs/contract.json"
KEYS = ("request_schema", "response_schema", "controller_envelope")
TITLES = {"request_schema": "request schema", "response_schema": "response schema",
          "controller_envelope": "controller envelope"}
BEGIN = "BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)"
END = "END GENERATED CONTRACT VERSIONS"
TABLE_BEGIN = "<!-- BEGIN GENERATED CONTRACT TABLE -->"
TABLE_END = "<!-- END GENERATED CONTRACT TABLE -->"

# Where each number lives besides the manifest. Paths are repository-relative;
# the CONTRACT.md table is rendered from this list, so it cannot go stale.
COPIES = {
    "request_schema": [("runner/Sources/PWRunnerCore/PWRunnerAPI.swift", "PWContract.requestSchema"),
                       ("controller/src/json_contract.rs", "REQUEST_SCHEMA_VERSION"),
                       ("tests/lib/contract.py", "REQUEST_SCHEMA")],
    "response_schema": [("runner/Sources/PWRunnerCore/PWRunnerAPI.swift", "PWContract.responseSchema"),
                        ("controller/src/json_contract.rs", "RESPONSE_SCHEMA_VERSION"),
                        ("tests/lib/contract.py", "RESPONSE_SCHEMA")],
    "controller_envelope": [("controller/src/json_contract.rs", "SCHEMA_VERSION"),
                            ("tests/lib/contract.py", "CONTROLLER_ENVELOPE")],
}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_versions(path: Path) -> dict:
    data = json.loads(path.read_text(), object_pairs_hook=unique_object)
    if not isinstance(data, dict) or set(data) != {"schema_version", "versions"} or data["schema_version"] != 1:
        raise ValueError("expected contract manifest schema_version 1 with a versions object")
    versions = data["versions"]
    if not isinstance(versions, dict) or set(versions) != set(KEYS):
        raise ValueError("versions must hold exactly: " + ", ".join(KEYS))
    for key in KEYS:
        if type(versions[key]) is not int or versions[key] < 1:
            raise ValueError(f"{key}: version must be a positive integer")
    return {key: versions[key] for key in KEYS}


def sentence(v):
    return ("Current wire contracts: " + ", ".join(f"{TITLES[k]} {v[k]}" for k in KEYS)
            + ". Each number is a separate contract. `docs/contract.json` owns these numbers;"
            " the internal host/worker boundary uses a generated source identity.")


def table(v):
    lines = ["| Contract | Version | Generated copies |", "| --- | --- | --- |"]
    for key in KEYS:
        copies = "; ".join(f"[`{symbol}`](../{path})" for path, symbol in COPIES[key])
        lines.append(f"| {TITLES[key]} (`{key}`) | {v[key]} | {copies} |")
    return "\n".join(lines)


def region(open_comment, close_comment, indent=""):
    return (f"{indent}{open_comment}{BEGIN}{close_comment}",
            f"{indent}{open_comment}{END}{close_comment}")


TARGETS = {
    "runner/Sources/PWRunnerCore/PWRunnerAPI.swift": [
        (*region("// ", ""), lambda v: "\n".join([
            "/// Wire contract versions. Edit docs/contract.json and regenerate; never edit here.",
            "enum PWContract {",
            f"    static let requestSchema: Int = {v['request_schema']}",
            f"    static let responseSchema: Int = {v['response_schema']}",
            "}"]))],
    "controller/src/json_contract.rs": [
        (*region("// ", ""), lambda v: "\n".join([
            f"pub const SCHEMA_VERSION: u32 = {v['controller_envelope']};",
            "/// The accepted request contract, independent of implementation revisions.",
            f"pub const REQUEST_SCHEMA_VERSION: u32 = {v['request_schema']};",
            "/// The one runner response schema this controller reads; any other version is refused.",
            f"pub const RESPONSE_SCHEMA_VERSION: u32 = {v['response_schema']};"]))],
    "tests/lib/contract.py": [
        (*region("# ", ""), lambda v: "\n".join(f"{k.upper()} = {v[k]}" for k in KEYS))],
    "docs/CONTRACT.md": [(*region("<!-- ", " -->"), sentence), (TABLE_BEGIN, TABLE_END, table)],
    "docs/PolicyWitness.md": [(*region("<!-- ", " -->"), sentence)],
    "runner/README.md": [(*region("<!-- ", " -->"), sentence)],
    "controller/README.md": [(*region("<!-- ", " -->"), sentence)],
}


def block_bounds(text, start, end):
    if text.count(start) != 1 or text.count(end) != 1 or text.index(end) < text.index(start):
        raise ValueError(f"expected exactly one ordered block: {start} ... {end}")
    return text.index(start), text.index(end) + len(end)


def replace_block(text, start, end, body):
    begin, finish = block_bounds(text, start, end)
    return text[:begin] + start + "\n" + body + "\n" + end + text[finish:]


def render_all(root: Path, versions):
    """Read and render every target before anything is written."""
    results = []
    for rel, regions in TARGETS.items():
        before = (root / rel).read_text()
        after = before
        for start, end, render in regions:
            after = replace_block(after, start, end, render(versions))
        results.append((rel, before, after))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify every generated copy; do not write")
    args = parser.parse_args()
    try:
        versions = load_versions(ROOT / MANIFEST)
        results = render_all(ROOT, versions)
        stale = [rel for rel, before, after in results if before != after]
        if args.check:
            if stale:
                raise ValueError(f"stale {', '.join(stale)}; run python3 docs/generate_contract.py")
        else:
            for rel, before, after in results:
                if before != after:
                    (ROOT / rel).write_text(after)
        summary = ", ".join(f"{TITLES[k]} {versions[k]}" for k in KEYS)
        print(f"ok: {summary}; " + ("all generated copies current" if args.check else
                                    f"{len(stale)} file(s) regenerated"))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        print(f"contract: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
