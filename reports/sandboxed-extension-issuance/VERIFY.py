#!/usr/bin/env python3
"""Verify archive preservation offline; never execute experimental equipment."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def anchors(path):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    result = set(re.findall(r'<a\s+(?:name|id)=["\']([^"\']+)', text))
    counts = Counter()
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, flags=re.M):
        heading = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", heading)
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        number = counts[slug]
        counts[slug] += 1
        result.add(slug + ("-" + str(number) if number else ""))
    return result


def main():
    manifest = read_json(ROOT / "ARCHIVE.json")
    failures = []
    expected_paths = set()
    originals = 0
    for item in manifest["files"]:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe archive inventory path")
        expected_paths.add(relative.as_posix())
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            failures.append("missing/non-regular inventory file: " + str(relative))
            continue
        data = path.read_bytes()
        if sha256(data) != item["sha256"] or len(data) != item["bytes"]:
            failures.append("archive content mismatch: " + str(relative))
        if "original_sha256" in item:
            originals += 1
            if item["transformation"] == "unchanged" and sha256(data) != item["original_sha256"]:
                failures.append("original content mismatch: " + str(relative))
    actual_paths = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
                    if p.is_file() and "local" not in p.relative_to(ROOT).parts
                    and "__pycache__" not in p.relative_to(ROOT).parts}
    if actual_paths != expected_paths | {"ARCHIVE.json"}:
        difference = actual_paths ^ (expected_paths | {"ARCHIVE.json"})
        failures.append("portable file inventory differs: " + repr(sorted(difference)))

    trials = sorted((ROOT / "evidence/trials").glob("*/trial.json"))
    counts = Counter()
    event_count = 0
    for path in trials:
        record = read_json(path)
        trial = record["trial"]
        counts[(trial["block"], trial["arrangement"])] += 1
        schedule = read_json(ROOT / trial["schedule_ref"])
        if (trial["diagnostic"] or trial["revision"] != "r1"
                or schedule["sequence"][trial["position"] - 1] != trial["arrangement"]):
            failures.append("planned-trial inventory mismatch: " + trial["id"])
        raw = [json.loads(line) for line in
               (path.parent / "native-events.jsonl").read_text().splitlines()]
        if raw != record["events"]:
            failures.append("assembled events differ from NDJSON: " + trial["id"])
        event_count += len(raw)
    expected = Counter({(b, "C" + str(c)): 1 for b in (1, 2, 3) for c in range(8)})
    if len(trials) != 24 or counts != expected or event_count != 2112:
        failures.append("24-trial/2112-event preservation inventory differs")

    links = read_json(ROOT / "LINKS.json")
    declared = Counter((v["document"], v["target"]) for v in
                       links["relative_links"] + links["historical_exceptions"])
    observed = Counter()
    for path in ROOT.rglob("*.md"):
        relative = path.relative_to(ROOT)
        if "local" in relative.parts:
            continue
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if not target.startswith(("http://", "https://", "mailto:")):
                observed[(relative.as_posix(), target)] += 1
    if observed != declared:
        failures.append("relative-link inventory differs from LINKS.json")
    for item in links["relative_links"]:
        document = ROOT / item["document"]
        target, _, fragment = item["target"].partition("#")
        path = (document.parent / unquote(target)).resolve() if target else document
        if not path.is_relative_to(ROOT) or not path.exists():
            failures.append("unresolved archive link: " + repr(item))
        elif fragment and path.suffix == ".md" and unquote(fragment) not in anchors(path):
            failures.append("unresolved archive anchor: " + repr(item))
    for item in links["historical_exceptions"]:
        kind = item["classification"]
        allowed = ((kind == "historical_source_snapshot" and item["document"].startswith("evidence/"))
                   or (kind == "unchanged_upstream_source_link" and item["document"].startswith("browser-sandbox-sources/sources/"))
                   or (kind == "checkout_local_historical_context" and item["target"].startswith(("../../tests/out/", "../../dist/archive/"))))
        if not allowed:
            failures.append("unrecognized historical-link exception: " + repr(item))

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    # This is the packet's original offline hash/Git-blob verifier, not upstream
    # code or experimental equipment. Neither verifier creates output files.
    result = subprocess.run([sys.executable, "-B", "-S", str(ROOT / "browser-sandbox-sources/VERIFY.py")], check=False)
    if result.returncode:
        return result.returncode
    print(f"Verified {len(expected_paths)} inventoried files, including {originals} relocated originals.")
    print("Preserved 24 planned r1 trials and 2,112 original NDJSON events.")
    print(f"Resolved {len(links['relative_links'])} archive-relative links; {len(links['historical_exceptions'])} historical link occurrences explicitly accounted for.")
    print("Offline preservation only: no native experiments, builds, signing, or acceptance reruns.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        print("Preservation verification could not complete: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
