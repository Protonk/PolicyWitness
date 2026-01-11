#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

CURRENT_STEP=""

test_begin "smoke" "sandbox_extension.q5_update_file_rename_delta"

fail() {
  test_fail "${CURRENT_STEP:-q5 update_file_rename_delta failed}"
}

trap fail ERR

step() {
  CURRENT_STEP="$1"
  test_step "$1" "${2:-$1}"
}

PW="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
OUT_DIR="${PW_TEST_ARTIFACTS}"

if [[ ! -x "${PW}" ]]; then
  test_fail "missing or non-executable PolicyWitness launcher at: ${PW}"
fi

mkdir -p "${OUT_DIR}"

step "update_file_rename_delta" "run update_file_rename_delta and check evidence fields"
PY_STATUS=0
/usr/bin/python3 - "${PW}" "${OUT_DIR}" <<'PY' || PY_STATUS=$?
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

pw, out_dir = sys.argv[1:]
out_dir = Path(out_dir)

harness_base = Path("/tmp/policy-witness-harness")
harness_base.mkdir(parents=True, exist_ok=True)
run_dir = Path(subprocess.check_output(["/usr/bin/mktemp", "-d", f"{harness_base}/q5-update-file-rename-delta-XXXXXX"]).decode("utf-8").strip())

old_path = run_dir / f"pw_old_{uuid.uuid4().hex[:8]}.txt"
new_path = run_dir / f"pw_new_{uuid.uuid4().hex[:8]}.txt"
old_path.write_text("pw rename-retarget test\n", encoding="utf-8")

cmd = [
    pw, "xpc", "run",
    "--profile", "temporary_exception",
    "sandbox_extension",
    "--op", "update_file_rename_delta",
    "--class", "com.apple.app-sandbox.read",
    "--path", str(old_path),
    "--new-path", str(new_path),
    "--wait-for-external-rename",
]

(out_dir / "run.cmd.txt").write_text(" ".join(cmd) + "\n")
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

time.sleep(1.0)
try:
    os.rename(old_path, new_path)
except Exception as exc:
    proc.kill()
    (out_dir / "summary.json").write_text(json.dumps({
        "status": "fail",
        "reason": f"host rename failed: {exc}",
        "old_path": str(old_path),
        "new_path": str(new_path),
    }, indent=2))
    raise SystemExit(1)

stdout, stderr = proc.communicate(timeout=240)
(out_dir / "run.json").write_text(stdout)
(out_dir / "run.stderr.txt").write_text(stderr)

try:
    obj = json.loads(stdout)
except Exception as exc:
    (out_dir / "summary.json").write_text(json.dumps({
        "status": "fail",
        "reason": f"stdout not JSON: {exc}",
    }, indent=2))
    raise SystemExit(1)

details = (obj.get("data") or {}).get("details") or {}

def count_keys(substr):
    return len([k for k in details.keys() if substr in k])

summary = {
    "status": "pass",
    "reason": "ok",
    "result_ok": obj.get("result", {}).get("ok"),
    "result_normalized_outcome": obj.get("result", {}).get("normalized_outcome"),
    "old_path": str(old_path),
    "new_path": str(new_path),
    "evidence_counts": {
        "delta_old_open_transition": count_keys("delta_old_open_transition"),
        "delta_new_open_transition": count_keys("delta_new_open_transition"),
        "open_outcome": count_keys("open_outcome"),
        "changed_access": count_keys("changed_access"),
        "access_after_update": count_keys("access_after_update"),
    },
}

missing = []
if summary["evidence_counts"]["delta_old_open_transition"] == 0:
    missing.append("delta_old_open_transition")
if summary["evidence_counts"]["delta_new_open_transition"] == 0:
    missing.append("delta_new_open_transition")
if summary["evidence_counts"]["open_outcome"] == 0:
    missing.append("open_outcome")
if summary["evidence_counts"]["changed_access"] == 0:
    missing.append("changed_access")

if missing:
    summary["status"] = "fail"
    summary["reason"] = f"missing expected evidence keys: {missing}"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(1)

# Consistency check: if any update_by_fileid_*_changed_access is true, its
# access_after_update_by_fileid_*_new_open_outcome should not be 'deny'.
for key, value in details.items():
    if not key.endswith("_changed_access"):
        continue
    if not key.startswith("update_by_fileid_"):
        continue
    if str(value).lower() != "true":
        continue
    suffix = key[len("update_by_fileid_") : -len("_changed_access")]
    outcome_key = f"access_after_update_by_fileid_{suffix}_new_open_outcome"
    outcome = details.get(outcome_key)
    if outcome is None:
        summary["status"] = "fail"
        summary["reason"] = f"missing {outcome_key} for changed_access=true"
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
        raise SystemExit(1)
    if str(outcome).lower() == "deny":
        summary["status"] = "fail"
        summary["reason"] = f"inconsistent: {key}=true but {outcome_key} is deny"
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
        raise SystemExit(1)

(out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
PY

if [[ ${PY_STATUS} -ne 0 ]]; then
  test_fail "q5 update_file_rename_delta validation failed (see ${OUT_DIR}/summary.json)"
fi

test_pass "q5 update_file_rename_delta ok" "{}"
