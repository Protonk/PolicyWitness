#!/usr/bin/env python3
"""
build-evidence.py

Generates a build-time evidence BOM for a built PolicyWitness.app bundle, typically under:
  dist/PolicyWitness.app/Contents/Resources/Evidence/

This repo is now specimen-first: sandbox policy variation is driven by the
`PWRunner` XPC service applying SBPL at runtime, not by proliferating different
entitlement-signed XPC service families.

Evidence artifacts:
  - manifest.json: hashes + metadata for embedded tools and services
  - symbols.json: exported `_pw_*` marker symbols (best-effort)

Intentionally not generated:
  - profiles.json (legacy entitlement-profile inventory)
"""

import argparse
import hashlib
import json
import plistlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def lc_uuid(path: Path) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["/usr/bin/dwarfdump", "--uuid", str(path)],
            stderr=subprocess.STDOUT,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    for line in out.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0] == "UUID:":
            return parts[1]
    return None


def _extract_plist_bytes(blob: bytes) -> Optional[bytes]:
    idx = blob.find(b"<?xml")
    if idx == -1:
        idx = blob.find(b"<plist")
    if idx == -1:
        return None
    return blob[idx:]


def _parse_codesign_entitlements_text(text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    array_stack: list[Tuple[int, list[Any]]] = []

    for raw in text.splitlines():
        if not raw:
            continue
        if raw.startswith("Executable="):
            continue

        stripped = raw.lstrip("\t")
        indent = len(raw) - len(stripped)

        while array_stack and indent <= array_stack[-1][0]:
            array_stack.pop()

        if stripped.startswith("[Key] "):
            current_key = stripped[len("[Key] ") :].strip()
            continue
        if stripped.startswith("[Value]"):
            continue
        if stripped.startswith("[Array]"):
            if current_key:
                arr: list[Any] = []
                result[current_key] = arr
                array_stack.append((indent, arr))
                current_key = None
            continue
        if stripped.startswith("[Bool] "):
            val = stripped[len("[Bool] ") :].strip().lower() == "true"
            if array_stack:
                array_stack[-1][1].append(val)
            elif current_key:
                result[current_key] = val
                current_key = None
            continue
        if stripped.startswith("[String] "):
            val = stripped[len("[String] ") :].strip()
            if array_stack:
                array_stack[-1][1].append(val)
            elif current_key:
                result[current_key] = val
                current_key = None
            continue
        if stripped.startswith("[Integer] "):
            try:
                val = int(stripped[len("[Integer] ") :].strip())
            except ValueError:
                continue
            if array_stack:
                array_stack[-1][1].append(val)
            elif current_key:
                result[current_key] = val
                current_key = None
            continue
    return result


def entitlements_from_codesign(path: Path) -> Tuple[Dict[str, Any], Optional[str]]:
    try:
        proc = subprocess.run(
            ["/usr/bin/codesign", "-d", "--entitlements", "-", "--", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return {}, f"codesign failed: {exc}"

    combined = proc.stdout + proc.stderr
    plist_bytes = _extract_plist_bytes(combined)
    if plist_bytes:
        try:
            data = plistlib.loads(plist_bytes)
        except Exception as exc:  # noqa: BLE001
            return {}, f"entitlements parse error: {exc}"
        if isinstance(data, dict):
            return data, None
        return {}, "entitlements parse error: unexpected plist type"

    text = combined.decode("utf-8", errors="ignore")
    parsed = _parse_codesign_entitlements_text(text)
    if parsed:
        return parsed, None
    return {}, None


def exported_pw_symbols(path: Path) -> Tuple[list[str], Optional[str]]:
    try:
        out = subprocess.check_output(
            ["/usr/bin/nm", "-g", str(path)],
            stderr=subprocess.STDOUT,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return [], f"nm failed: {exc}"

    symbols = set()
    for line in out.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        if len(parts) == 2 and parts[0] == "U":
            continue
        sym_type = parts[-2] if len(parts) >= 2 else ""
        if sym_type == "U":
            continue
        sym = parts[-1]
        if sym.startswith("_pw_"):
            symbols.add(sym[1:])
    return sorted(symbols), None


def read_plist(path: Path) -> Dict[str, Any]:
    with path.open("rb") as fh:
        data = plistlib.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"unexpected plist type at {path}: {type(data)}")
    return data


def rel_path(app_bundle: Path, path: Path) -> str:
    return str(path.resolve().relative_to(app_bundle.resolve()))


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Evidence BOM for a PolicyWitness.app bundle")
    ap.add_argument("--app-bundle", required=True, help="Path to a PolicyWitness.app bundle")
    ap.add_argument("--app-entitlements", required=True, help="Path to main app entitlements plist")
    args = ap.parse_args()

    app_bundle = Path(args.app_bundle).resolve()
    contents_dir = app_bundle / "Contents"
    evidence_dir = contents_dir / "Resources" / "Evidence"
    xpc_dir = contents_dir / "XPCServices"

    if not contents_dir.exists():
        print(f"ERROR: missing app bundle Contents: {contents_dir}", file=sys.stderr)
        return 2

    if evidence_dir.exists():
        shutil.rmtree(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    app_info = read_plist(contents_dir / "Info.plist")
    app_bundle_id = app_info.get("CFBundleIdentifier")
    app_entitlements = read_plist(Path(args.app_entitlements))

    entries: list[Dict[str, Any]] = []

    # Embedded helper tools under Contents/MacOS (signed separately; host-side).
    helper_names = [
        "pw-runner-client",
        "sb_api_validator",
        "sandbox-log-observer",
        "sbpl-preflight",
    ]
    for name in helper_names:
        helper_path = contents_dir / "MacOS" / name
        if not helper_path.exists():
            continue
        entitlements, err = entitlements_from_codesign(helper_path)
        entry: Dict[str, Any] = {
            "id": name,
            "kind": "helper",
            "rel_path": rel_path(app_bundle, helper_path),
            "sha256": sha256_file(helper_path),
            "lc_uuid": lc_uuid(helper_path) or "",
            "entitlements": entitlements,
        }
        if err:
            entry["entitlements_error"] = err
        entries.append(entry)

    # Embedded XPC services under Contents/XPCServices (signed separately; runner boundary).
    if xpc_dir.exists():
        for svc_bundle in sorted(xpc_dir.glob("*.xpc")):
            info_path = svc_bundle / "Contents" / "Info.plist"
            if not info_path.exists():
                continue
            info = read_plist(info_path)
            bundle_id = info.get("CFBundleIdentifier")
            svc_name = svc_bundle.stem
            svc_bin = svc_bundle / "Contents" / "MacOS" / svc_name
            if not svc_bin.exists():
                continue
            entitlements, err = entitlements_from_codesign(svc_bin)
            entry = {
                "id": bundle_id or svc_name,
                "bundle_id": bundle_id,
                "kind": "xpc-service",
                "service_name": svc_name,
                "rel_path": rel_path(app_bundle, svc_bin),
                "sha256": sha256_file(svc_bin),
                "lc_uuid": lc_uuid(svc_bin) or "",
                "entitlements": entitlements,
            }
            if err:
                entry["entitlements_error"] = err
            entries.append(entry)

    symbols_entries: list[Dict[str, Any]] = []
    for entry in entries:
        abs_path = app_bundle / entry["rel_path"]
        syms, err = exported_pw_symbols(abs_path)
        if err:
            symbols_entries.append(
                {
                    "id": entry["id"],
                    "bundle_id": entry.get("bundle_id"),
                    "rel_path": entry["rel_path"],
                    "symbols": [],
                    "error": err,
                }
            )
            continue
        if syms:
            symbols_entries.append(
                {
                    "id": entry["id"],
                    "bundle_id": entry.get("bundle_id"),
                    "rel_path": entry["rel_path"],
                    "symbols": syms,
                }
            )

    symbols_manifest = {"generated_at": utc_now(), "entries": symbols_entries}
    symbols_path = evidence_dir / "symbols.json"
    with symbols_path.open("w", encoding="utf-8") as fh:
        json.dump(symbols_manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")

    entries.append(
        {
            "id": "evidence.symbols",
            "kind": "evidence",
            "rel_path": rel_path(app_bundle, symbols_path),
            "sha256": sha256_file(symbols_path),
        }
    )

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "app_bundle_id": app_bundle_id,
        "app_binary_rel_path": "Contents/MacOS/policy-witness",
        "app_entitlements": app_entitlements,
        "entries": entries,
        "notes": [
            "Main app binary hash is omitted because the manifest is signed by the app bundle.",
        ],
    }

    manifest_path = evidence_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
