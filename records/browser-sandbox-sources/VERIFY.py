#!/usr/bin/env python3
"""Verify this source packet offline. Does not import or execute upstream code."""
from pathlib import Path
import hashlib
import json
import sys


def main() -> int:
    root = Path(__file__).resolve().parent
    failures = []
    try:
        manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
        checksums = (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        listed = set()
        for row in checksums:
            expected, name = row.split("  ", 1)
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Unsafe checksum path: {name}")
            path = root / relative
            listed.add(name)
            if path.is_symlink() or not path.is_file():
                failures.append(f"Missing or non-regular file: {name}")
                continue
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                failures.append(f"SHA-256 mismatch: {name}")
        for item in manifest["files"]:
            name = item["local_path"]
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Unsafe manifest path: {name}")
            path = root / relative
            if path.is_symlink() or not path.is_file():
                failures.append(f"Missing or non-regular upstream file: {name}")
                continue
            data = path.read_bytes()
            blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
            if hashlib.sha1(blob).hexdigest() != item["git_blob_sha1"]:
                failures.append(f"Git blob mismatch: {name}")
            if hashlib.sha256(data).hexdigest() != item["sha256"]:
                failures.append(f"Manifest SHA-256 mismatch: {name}")
            if len(data) != item["bytes"]:
                failures.append(f"Size mismatch: {name}")
            if name not in listed:
                failures.append(f"Upstream file omitted from SHA256SUMS: {name}")
        source_names = {str(p.relative_to(root)) for p in (root / "sources").rglob("*") if p.is_file()}
        manifest_names = {item["local_path"] for item in manifest["files"]}
        if source_names != manifest_names:
            failures.append("Source directory and manifest inventory differ")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Verification could not complete: {exc}", file=sys.stderr)
        return 2
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Verified {len(checksums)} packaged files and {len(manifest['files'])} upstream Git blob identities.")
    print("Integrity is checked against the included records; no network or runtime verification was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
