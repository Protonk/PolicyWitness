#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

CURRENT_STEP=""

test_begin "smoke" "xpc.q7_gatekeeper_connection"

fail() {
  test_fail "${CURRENT_STEP:-q7 gatekeeper connection failed}"
}

trap fail ERR

step() {
  CURRENT_STEP="$1"
  test_step "$1" "${2:-$1}"
}

PW="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
OUT_DIR="${PW_TEST_ARTIFACTS}"
SERVICE_BUNDLE_ID="com.yourteam.policy-witness.ProbeService_gatekeeper"

if [[ ! -x "${PW}" ]]; then
  test_fail "missing or non-executable PolicyWitness launcher at: ${PW}"
fi

mkdir -p "${OUT_DIR}"

step "gatekeeper_runs" "gatekeeper reject vs accept"
PY_STATUS=0
/usr/bin/python3 - "${PW}" "${OUT_DIR}" "${SERVICE_BUNDLE_ID}" <<'PY' || PY_STATUS=$?
import json
import os
import subprocess
import sys
from pathlib import Path

pw, out_dir, bundle_id = sys.argv[1:]
out_dir = Path(out_dir)

def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")

def run_cmd(label, cmd):
    write_text(out_dir / f"{label}.cmd.txt", " ".join(cmd) + "\n")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    write_text(out_dir / f"{label}.stderr.txt", proc.stderr)
    write_text(out_dir / f"{label}.rc.txt", str(proc.returncode) + "\n")
    write_text(out_dir / f"{label}.json", proc.stdout)
    try:
        data = json.loads(proc.stdout)
    except Exception as exc:
        return None, f"{label}: stdout not JSON: {exc}"
    return data, None

def find_service_variant(profiles_path, bundle_id):
    try:
        profiles = json.loads(Path(profiles_path).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return False
    for profile in profiles.get("profiles", []):
        for variant in profile.get("variants", []):
            if variant.get("bundle_id") == bundle_id:
                return True
    return False

pw_path = Path(pw).resolve()
app_root = pw_path.parents[2] if len(pw_path.parents) >= 3 else None
profiles_path = app_root / "Contents/Resources/Evidence/profiles.json" if app_root else None

if not profiles_path or not profiles_path.exists() or not find_service_variant(profiles_path, bundle_id):
    write_text(out_dir / "summary.json", json.dumps({
        "status": "skip",
        "reason": f"missing gatekeeper service in profiles.json: {profiles_path}",
        "service_bundle_id": bundle_id,
    }, indent=2, sort_keys=True))
    raise SystemExit(2)

container_root = Path.home() / "Library/Containers" / bundle_id / "Data"
mode_path = container_root / "Library/Application Support/PolicyWitness/gatekeeper_mode"
mode_path.parent.mkdir(parents=True, exist_ok=True)

def set_mode(value):
    mode_path.write_text(value + "\n", encoding="utf-8")

summary = {"status": "pass", "reason": "ok", "service_bundle_id": bundle_id}

set_mode("reject")
reject_cmd = [pw, "xpc", "run", "--service", bundle_id, "capabilities_snapshot"]
reject_data, err = run_cmd("reject", reject_cmd)
if err:
    summary.update({"status": "fail", "reason": err})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

set_mode("accept")
accept_cmd = [pw, "xpc", "run", "--service", bundle_id, "capabilities_snapshot"]
accept_data, err = run_cmd("accept", accept_cmd)
if err:
    summary.update({"status": "fail", "reason": err})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

def check_reject(data):
    result = data.get("result") or {}
    payload = data.get("data") or {}
    details = payload.get("details") or {}
    layer = payload.get("layer_attribution") or {}
    if result.get("ok") is not False:
        return "reject: expected result.ok=false"
    if result.get("normalized_outcome") != "xpc_error":
        return f"reject: expected normalized_outcome=xpc_error, got {result.get('normalized_outcome')!r}"
    probe_id = payload.get("probe_id")
    if probe_id not in (None, ""):
        return f"reject: expected probe_id to be empty, got {probe_id!r}"
    if details.get("service_bundle_id") != bundle_id:
        return "reject: missing or mismatched service_bundle_id"
    if not details.get("xpc_error_domain") or details.get("xpc_error_code") is None:
        return "reject: missing xpc_error_domain/xpc_error_code"
    other = layer.get("other") or ""
    if "openSession" not in other:
        return f"reject: expected layer_attribution.other to mention openSession, got {other!r}"
    return None

def check_accept(data):
    result = data.get("result") or {}
    payload = data.get("data") or {}
    if result.get("ok") is not True:
        return f"accept: expected result.ok=true, got {result!r}"
    if payload.get("probe_id") != "capabilities_snapshot":
        return f"accept: expected probe_id=capabilities_snapshot, got {payload.get('probe_id')!r}"
    return None

reject_err = check_reject(reject_data)
if reject_err:
    summary.update({"status": "fail", "reason": reject_err})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

accept_err = check_accept(accept_data)
if accept_err:
    summary.update({"status": "fail", "reason": accept_err})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

summary["reject"] = {
    "normalized_outcome": (reject_data.get("result") or {}).get("normalized_outcome"),
    "xpc_error_domain": (reject_data.get("data") or {}).get("details", {}).get("xpc_error_domain"),
    "xpc_error_code": (reject_data.get("data") or {}).get("details", {}).get("xpc_error_code"),
}
summary["accept"] = {
    "normalized_outcome": (accept_data.get("result") or {}).get("normalized_outcome"),
}

write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
PY

if [[ ${PY_STATUS} -eq 2 ]]; then
  test_skip "q7 gatekeeper service missing (rebuild to include ProbeService_gatekeeper)"
  exit 0
fi
if [[ ${PY_STATUS} -ne 0 ]]; then
  test_fail "q7 gatekeeper validation failed (see ${OUT_DIR}/summary.json)"
fi

test_pass "q7 gatekeeper connection ok" "{}"
