#!/usr/bin/env python3
"""
build-evidence.py

Generates the build-time evidence for a built PolicyWitness.app bundle, under:
  dist/PolicyWitness.app/Contents/Resources/Evidence/

This repo is specimen-first: sandbox policy variation is driven by the
`PWRunner` XPC service applying SBPL at runtime, not by proliferating different
entitlement-signed XPC service families.

Evidence artifacts:
  - manifest.json: hashes + metadata for embedded tools and services
  - symbols.json: exported `_pw_*` marker symbols (best-effort)
  - provenance.json: the build's provenance record (tests/lib/build_provenance.py)

The record comes from one of two sources. A build passes `--build-session`,
the session file build.sh kept through its steps, with `--root` and
`--identity`; the record then holds that build's observations. A test tool
that replaces executables in a signed copy passes `--substitution-of` with the
baseline app: the record keeps the baseline's source, toolchain and
configuration, names the replaced executables, and describes the copy's
bytes; it never claims the replaced bytes came from the recorded build.
Without either, no record can be written and the script refuses.

Intentionally not generated:
  - profiles.json (legacy entitlement-profile inventory)
"""

import argparse
import copy
import hashlib
import json
import plistlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import build_provenance  # noqa: E402
import signer_check  # noqa: E402


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


def signature_facts(path: Path) -> Dict[str, Any]:
    """The bounded signature facts the record keeps for one nested signature, read from codesign's display."""
    try:
        found = signer_check.signature(path)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return dict(status="unreadable", kind=exc.__class__.__name__)
    return signer_check.facts(found)


def worker_reported_identity(app: Path) -> Optional[str]:
    worker = app / build_provenance.SERVICE / "Contents/MacOS/pw-probe-runner"
    if not worker.is_file():
        return None
    found = build_provenance.probe([worker, "--version"])
    if found["status"] != "ok":
        return None
    match = re.search(r"\babi_identity=([0-9a-f]{64})\b", found["line"])
    return match.group(1) if match else None


def substitution_record(baseline: Path, app: Path, identity: str, entries: list) -> Dict[str, Any]:
    """A record for a test copy whose executables were replaced after the baseline's recorded build."""
    source_path = baseline / build_provenance.RECORD_PATH
    try:
        baseline_record = json.loads(source_path.read_bytes())
    except (OSError, ValueError) as exc:
        raise build_provenance.Refusal(f"the baseline app carries no readable record: {exc}", 2)
    if not isinstance(baseline_record, dict) or baseline_record.get("schema_version") != build_provenance.SCHEMA_VERSION:
        raise build_provenance.Refusal("the baseline record has an unsupported schema", 2)
    baseline_outputs = {o.get("rel_path"): o for o in baseline_record.get("outputs", []) if isinstance(o, dict)}
    manifest_hashes = {e["rel_path"]: e.get("sha256") for e in entries if isinstance(e, dict)}
    outputs, replaced = [], []
    for relative in build_provenance.shipped_outputs(app):
        path = app / relative
        metadata = build_provenance.output_metadata(path)
        if metadata.get("status") != "ok":
            raise build_provenance.Refusal(f"{relative}: load commands are not readable", 2)
        if len(metadata["tools"]) > build_provenance.TOOLS_LIMIT:
            raise build_provenance.Refusal(f"{relative}: {len(metadata['tools'])} build tools in LC_BUILD_VERSION exceed the record's bounds", 2)
        # The copy's own bytes: a substituted executable outside the output target is described as it is, and the
        # record's validation then refuses it; nothing is carried over from the baseline's observation.
        observed = build_provenance.output_observation(path)
        if observed["problems"]:
            raise build_provenance.Refusal(f"{relative}: the output target cannot be observed ({'; '.join(observed['problems'])})", 2)
        entry: Dict[str, Any] = dict(rel_path=relative, uuid=metadata["uuid"], platform=metadata["platform"],
                                     minos=metadata["minos"], sdk=metadata["sdk"], tools=metadata["tools"],
                                     architectures=observed["architectures"], container=observed["container"])
        before = baseline_outputs.get(relative, {})
        if relative != build_provenance.CONTROLLER:
            entry["sha256"] = sha256_file(path)
            if manifest_hashes.get(relative) != entry["sha256"]:
                raise build_provenance.Refusal(f"{relative}: the manifest records {manifest_hashes.get(relative)} but the bundle bytes hash to {entry['sha256']}", 2)
            entry["signature"] = signature_facts(path)
            same = before.get("sha256") == entry["sha256"]
        else:
            entry["sha256"] = None
            entry["note"] = "the controller is sealed by the app signature after this record; its final hash is in the release record"
            same = before.get("uuid") == entry["uuid"]
        if not same:
            replaced.append(relative)
        if relative in build_provenance.CARGO_TARGETS:
            entry["cargo"] = copy.deepcopy(before.get("cargo")) if same and before.get("cargo") else dict(
                status="substituted", note="replaced in a test copy after the recorded build; Cargo made no judgment about these bytes")
        outputs.append(entry)
    record = dict(schema_version=build_provenance.SCHEMA_VERSION, generated_at=utc_now(),
                  source=copy.deepcopy(baseline_record.get("source", {})),
                  toolchain=copy.deepcopy(baseline_record.get("toolchain", {})),
                  configuration=copy.deepcopy(baseline_record.get("configuration", {})),
                  outputs=outputs,
                  signing=dict(identity=identity,
                               nested=[dict(rel_path=o["rel_path"], **{k: o["signature"].get(k) for k in ("leaf", "team", "timestamp")})
                                       for o in outputs if "signature" in o],
                               note="the app seal is made after this record and verified afterwards"),
                  limits=list(baseline_record.get("limits", [])) + [
                      "test copy: the executables listed under configuration.substitution were replaced after the recorded build; "
                      "the baseline's toolchain and configuration do not describe them"])
    reported = worker_reported_identity(app)
    record["source"]["worker_identity"] = reported if reported else "unknown"
    record["configuration"]["substitution"] = dict(
        baseline_record_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(), replaced=replaced,
        note="a signed test copy assembled from a baseline app with these executables replaced")
    forbidden = build_provenance.forbidden_content(json.dumps(record, sort_keys=True), dict(__import__("os").environ))
    if forbidden:
        raise build_provenance.Refusal("the record would publish " + forbidden, 2)
    return record


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Evidence BOM for a PolicyWitness.app bundle")
    ap.add_argument("--app-bundle", required=True, help="Path to a PolicyWitness.app bundle")
    ap.add_argument("--app-entitlements", required=True, help="Path to main app entitlements plist")
    ap.add_argument("--build-session", help="the build session file build.sh kept; the record comes from its observations")
    ap.add_argument("--root", help="the checkout the build session belongs to (with --build-session)")
    ap.add_argument("--identity", help="the signing identity the nested signatures name")
    ap.add_argument("--substitution-of", help="baseline app of a test copy whose executables were replaced")
    args = ap.parse_args()

    app_bundle = Path(args.app_bundle).resolve()
    contents_dir = app_bundle / "Contents"
    evidence_dir = contents_dir / "Resources" / "Evidence"
    xpc_dir = contents_dir / "XPCServices"

    if not contents_dir.exists():
        print(f"ERROR: missing app bundle Contents: {contents_dir}", file=sys.stderr)
        return 2
    if bool(args.build_session) == bool(args.substitution_of):
        print("ERROR: provenance requires exactly one of --build-session (with --root and --identity) or --substitution-of (with --identity)", file=sys.stderr)
        return 2
    if args.build_session and not (args.root and args.identity):
        print("ERROR: --build-session requires --root and --identity", file=sys.stderr)
        return 2
    if args.substitution_of and not args.identity:
        print("ERROR: --substitution-of requires --identity", file=sys.stderr)
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
        "sbpl-check",
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

            # Sibling binaries inside the XPC bundle's MacOS dir (e.g.
            # pw-probe-runner, sb_api_validator, pw-extension-issuer). These are signed
            # individually before the XPC bundle seal is computed so
            # the bundle codesign records their hashes; we surface
            # them here so an evidence consumer can see the embedded
            # helper's sha256 / lc_uuid / entitlements without having
            # to descend into the bundle.
            svc_macos_dir = svc_bundle / "Contents" / "MacOS"
            for sibling in sorted(svc_macos_dir.iterdir()):
                if sibling.name == svc_name or not sibling.is_file():
                    continue
                sib_entitlements, sib_err = entitlements_from_codesign(sibling)
                sib_entry: Dict[str, Any] = {
                    "id": f"{svc_name}/{sibling.name}",
                    "bundle_id": bundle_id,
                    "kind": "xpc-embedded-helper",
                    "service_name": svc_name,
                    "rel_path": rel_path(app_bundle, sibling),
                    "sha256": sha256_file(sibling),
                    "lc_uuid": lc_uuid(sibling) or "",
                    "entitlements": sib_entitlements,
                }
                if sib_err:
                    sib_entry["entitlements_error"] = sib_err
                entries.append(sib_entry)

    # Named SBPL augments under Contents/Resources/Augments/. Augments
    # are controller-resolved fragments that mutate the policy bytes
    # the runner compiles, so downstream consumers need provenance for
    # the shipped contents (sha256) just as they do for Mach-O
    # helpers. Augments are not executables, so we omit lc_uuid /
    # entitlements / symbol-table fields.
    augments_dir = contents_dir / "Resources" / "Augments"
    if augments_dir.exists():
        for augment_path in sorted(augments_dir.glob("*.sb")):
            if not augment_path.is_file():
                continue
            entries.append({
                "id": f"augments/{augment_path.name}",
                "kind": "augment",
                "rel_path": rel_path(app_bundle, augment_path),
                "sha256": sha256_file(augment_path),
            })

    symbols_entries: list[Dict[str, Any]] = []
    for entry in entries:
        # Augments and other non-Mach-O resources have no exported
        # symbol table; skip them rather than asking `nm` to fail.
        if entry.get("kind") == "augment":
            continue
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

    # The provenance record describes the signed bytes the manifest lists; it is
    # written before the manifest so the manifest's entry seals its hash too.
    try:
        if args.build_session:
            # The session is read under the verified hold, through the admitted target directory.
            expected = Path(args.root).absolute() / build_provenance.TARGET / build_provenance.SESSION_NAME
            if Path(args.build_session).absolute() != expected:
                raise build_provenance.Refusal(f"the build session lives at {expected}, not {args.build_session}", 2)
            with build_provenance.build_scope(Path(args.root)) as state:
                record = build_provenance.collect(state.session, app_bundle, state.root, args.identity,
                                                  manifest_entries=entries, signature=signature_facts)
        else:
            record = substitution_record(Path(args.substitution_of).resolve(), app_bundle, args.identity, entries)
    except build_provenance.Refusal as exc:
        print(f"ERROR: provenance: {exc}", file=sys.stderr)
        return 2
    provenance_path = evidence_dir / "provenance.json"
    with provenance_path.open("w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
        fh.write("\n")
    entries.append(
        {
            "id": "evidence.provenance",
            "kind": "evidence",
            "rel_path": rel_path(app_bundle, provenance_path),
            "sha256": sha256_file(provenance_path),
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
