#!/usr/bin/env python3
"""Copy completed managed runs into an inert, deduplicated evidence archive.

Run under the repository checkout lock. This never alters managed ownership,
pins or cleanup state. Blob paths deliberately cannot serve as active run paths.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    parser.add_argument("--superseded", action="append", default=[],
                        help="Preserve run receipts, app inventory and failed cases; successful case observations are replaced by a complete new run.")
    parser.add_argument("runs", nargs="+")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    destination = (root / args.destination).resolve()
    destination.relative_to(root / "records")
    destination.mkdir(exist_ok=False)
    superseded = {(root / name).resolve() for name in args.superseded}
    archive_path = destination / "evidence.tar.gz"
    manifest = {
        "schema_version": 1,
        "kind": "inert identified copies of current terminal runs and explicitly scoped superseded evidence",
        "ownership_note": "Original paths/IDs are historical identities. Blob copies do not relocate ownership, prove cleanup or authorize replay/pruning.",
        "runs": [],
        "files": [],
        "symlinks": [],
        "directories": [],
        "omissions": [],
        "archive": "evidence.tar.gz",
    }
    blobs = {}
    with tarfile.open(archive_path, "w:gz") as archive:
        for name in args.runs:
            run_root = (root / name).resolve()
            run_root.relative_to(root / "tests/out/runs")
            owner_bytes = (run_root / "owner.json").read_bytes()
            run_bytes = (run_root / "run.json").read_bytes()
            owner, run = json.loads(owner_bytes), json.loads(run_bytes)
            assert owner["run_id"] == run["run_id"]
            assert owner["out_dir"] == run["configuration"]["out_dir"] == str(run_root)
            assert run["finished_at_unix_ms"] >= owner["started_at_unix_ms"]
            failures = {"suites/" + case["id"] for case in run["case_results"] if case["status"] != "pass"}
            limited = run_root in superseded
            manifest["runs"].append({
                "original_path": str(run_root.relative_to(root)),
                "run_id": run["run_id"],
                "run_sha256": digest(run_bytes),
                "case_outcome_counts": run["case_outcome_counts"],
                "completion": run["completion"],
                "copy_scope": "root receipts, artifact integrity and failed cases" if limited else "complete run tree",
            })
            for path in sorted([run_root, *run_root.rglob("*")]):
                relative = path.relative_to(run_root)
                if limited and len(relative.parts) > 1:
                    name = str(relative)
                    if relative.parts[0] != "artifact-integrity" and not any(name == prefix or name.startswith(prefix + "/") for prefix in failures):
                        continue
                item = {"original_path": str(path.relative_to(root)), "run_id": run["run_id"], "mode": path.lstat().st_mode}
                if path.is_symlink():
                    item["target"] = str(path.readlink())
                    manifest["symlinks"].append(item)
                elif path.is_dir():
                    manifest["directories"].append(item)
                elif path.is_file():
                    data = path.read_bytes()
                    checksum = digest(data)
                    member = "blobs/" + checksum
                    if checksum not in blobs:
                        info = tarfile.TarInfo(member)
                        info.size = len(data)
                        info.mode = 0o444
                        archive.addfile(info, io.BytesIO(data))
                        blobs[checksum] = len(data)
                    item.update({"sha256": checksum, "bytes": len(data), "member": member})
                    manifest["files"].append(item)
                else:
                    raise RuntimeError("Unexpected special file: " + str(path))
            assert (run_root / "owner.json").read_bytes() == owner_bytes
            assert (run_root / "run.json").read_bytes() == run_bytes
            if limited:
                manifest["omissions"].extend({
                    "original_path": str(run_root.relative_to(root) / "suites" / case["id"]),
                    "run_id": run["run_id"],
                    "reason": "Superseded passing case; root accounting retained, fresh complete run supplies current observation credit.",
                } for case in run["case_results"] if case["status"] == "pass")
    verified = set()
    with tarfile.open(archive_path, "r|gz") as archive:
        for member in archive:
            checksum = member.name.removeprefix("blobs/")
            assert member.isfile() and checksum in blobs and checksum not in verified
            data = archive.extractfile(member).read()
            assert len(data) == blobs[checksum] and digest(data) == checksum
            verified.add(checksum)
    assert verified == set(blobs)
    manifest.update({
        "unique_blobs": len(blobs),
        "unique_uncompressed_bytes": sum(blobs.values()),
        "archive_bytes": archive_path.stat().st_size,
        "archive_sha256": digest(archive_path.read_bytes()),
        "all_blob_hashes_read_back_and_verified": True,
    })
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({key: manifest[key] for key in ("runs", "unique_blobs", "unique_uncompressed_bytes", "archive_bytes", "archive_sha256", "all_blob_hashes_read_back_and_verified")}, indent=2))


if __name__ == "__main__":
    main()
