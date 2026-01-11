#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

CURRENT_STEP=""

test_begin "smoke" "xpc.q8_attribution_bounds"

fail() {
  test_fail "${CURRENT_STEP:-q8 attribution bounds failed}"
}

trap fail ERR

step() {
  CURRENT_STEP="$1"
  test_step "$1" "${2:-$1}"
}

PW="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
OUT_DIR="${PW_TEST_ARTIFACTS}"
DENY_PATH="/private/var/db/launchd.db/com.apple.launchd/overrides.plist"

if [[ ! -x "${PW}" ]]; then
  test_fail "missing or non-executable PolicyWitness launcher at: ${PW}"
fi

if [[ ! -e "${DENY_PATH}" ]]; then
  test_skip "deny path missing on this host: ${DENY_PATH}"
  exit 0
fi

mkdir -p "${OUT_DIR}"

step "attribution_bounds" "seatbelt deny evidence vs POSIX deny (no deny evidence)"
PY_STATUS=0
/usr/bin/python3 - "${PW}" "${OUT_DIR}" "${DENY_PATH}" <<'PY' || PY_STATUS=$?
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

pw, out_dir, deny_path = sys.argv[1:]
out_dir = Path(out_dir)

def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")

def run_pw(label, args):
    cmd = [pw] + args
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

def capture_info(obj):
    data = obj.get("data") or {}
    cap = data.get("host_sandbox_log_capture") or {}
    obs = cap.get("observer_report", {}).get("data", {})
    return {
        "capture_status": cap.get("capture_status"),
        "observed_deny": obs.get("observed_deny"),
        "observed_lines": obs.get("observed_lines"),
    }

summary = {"status": "pass", "reason": "ok"}

# Run A: known seatbelt deny path.
deny_data, err = run_pw("seatbelt_deny", [
    "xpc", "run", "--profile", "minimal", "--capture-sandbox-logs",
    "fs_op", "--op", "open_read", "--path", deny_path, "--allow-unsafe-path",
])
if err:
    summary.update({"status": "fail", "reason": err})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

# Create a tmp file inside the harness.
create_data, err = run_pw("posix_create", [
    "xpc", "run", "--profile", "minimal",
    "fs_op", "--op", "create", "--path-class", "tmp", "--target", "specimen_file",
    "--name", "pw_q8_posix_deny.txt", "--no-cleanup",
])
if err:
    summary.update({"status": "fail", "reason": err})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

file_path = (create_data.get("data") or {}).get("details", {}).get("file_path")
if not file_path:
    summary.update({"status": "fail", "reason": "posix_create missing file_path"})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

file_path = Path(str(file_path))
try:
    os.chmod(file_path, 0)
except Exception as exc:
    summary.update({"status": "fail", "reason": f"chmod 000 failed: {exc}"})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

posix_data, err = run_pw("posix_deny", [
    "xpc", "run", "--profile", "minimal", "--capture-sandbox-logs",
    "fs_op", "--op", "open_read", "--path", str(file_path), "--allow-unsafe-path",
])

try:
    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    file_path.unlink(missing_ok=True)
except Exception:
    pass

if err:
    summary.update({"status": "fail", "reason": err})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

deny_result = deny_data.get("result") or {}
posix_result = posix_data.get("result") or {}

deny_capture = capture_info(deny_data)
posix_capture = capture_info(posix_data)

summary["deny"] = {
    "result_ok": deny_result.get("ok"),
    "normalized_outcome": deny_result.get("normalized_outcome"),
    "capture_status": deny_capture.get("capture_status"),
    "observed_deny": deny_capture.get("observed_deny"),
}
summary["posix"] = {
    "result_ok": posix_result.get("ok"),
    "normalized_outcome": posix_result.get("normalized_outcome"),
    "capture_status": posix_capture.get("capture_status"),
    "observed_deny": posix_capture.get("observed_deny"),
}

if deny_result.get("ok") is True:
    summary.update({"status": "skip", "reason": "deny_path is not denied on this host"})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(2)

if deny_capture.get("capture_status") != "captured":
    summary.update({"status": "skip", "reason": "sandbox log capture unavailable for deny path"})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(2)

if deny_capture.get("observed_deny") is not True:
    summary.update({"status": "fail", "reason": "seatbelt deny path missing observed_deny evidence"})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

if posix_result.get("ok") is True:
    summary.update({"status": "fail", "reason": "posix deny unexpectedly succeeded"})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

if posix_capture.get("capture_status") != "captured":
    summary.update({"status": "skip", "reason": "sandbox log capture unavailable for posix path"})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(2)

if posix_capture.get("observed_deny") is True:
    summary.update({"status": "fail", "reason": "posix deny emitted sandbox deny evidence"})
    write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

write_text(out_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True))
PY

if [[ ${PY_STATUS} -eq 2 ]]; then
  test_skip "q8 attribution bounds inconclusive (see artifacts)"
  exit 0
fi
if [[ ${PY_STATUS} -ne 0 ]]; then
  test_fail "q8 attribution bounds validation failed (see ${OUT_DIR}/summary.json)"
fi

test_pass "q8 attribution bounds ok" "{}"
