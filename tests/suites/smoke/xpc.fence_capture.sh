#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

CURRENT_STEP=""

test_begin "smoke" "xpc.fence_capture"

fail() {
  test_fail "${CURRENT_STEP:-fence capture failed}"
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

step "fence_capture" "fenced xpc run with capture flags"
PY_STATUS=0
/usr/bin/python3 - "${PW}" "${OUT_DIR}" <<'PY' || PY_STATUS=$?
import json
import subprocess
import sys
from pathlib import Path

pw, out_dir = sys.argv[1:]
out_dir = Path(out_dir)

cmd = [
    pw, "xpc", "run",
    "--profile", "minimal",
    "--capture-sandbox-logs",
    "--capture-signposts",
    "fs_op", "--op", "stat", "--path-class", "tmp",
]

(out_dir / "run.cmd.txt").write_text(" ".join(cmd) + "\n")
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
(out_dir / "run.stderr.txt").write_text(proc.stderr)
(out_dir / "run.rc.txt").write_text(str(proc.returncode))
(out_dir / "run.json").write_text(proc.stdout)

summary = {"status": "pass", "reason": "ok"}
try:
    data = json.loads(proc.stdout)
except Exception as exc:
    summary.update({"status": "fail", "reason": f"stdout not JSON: {exc}"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

if data.get("kind") != "probe_response":
    summary.update({"status": "fail", "reason": f"unexpected kind {data.get('kind')!r}"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

payload = data.get("data") or {}
fence = payload.get("fence") or {}
if fence.get("enabled") is not True:
    summary.update({"status": "fail", "reason": "missing data.fence.enabled=true"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

if fence.get("status") != "released":
    summary.update({"status": "fail", "reason": f"unexpected fence status {fence.get('status')!r}"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

collectors = fence.get("armed_collectors") or []
if not isinstance(collectors, list) or "sandbox_logs" not in collectors or "signposts" not in collectors:
    summary.update({"status": "fail", "reason": f"armed_collectors missing expected entries: {collectors!r}"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

if not fence.get("wait_path"):
    summary.update({"status": "fail", "reason": "missing fence wait_path"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

cap = payload.get("host_sandbox_log_capture") or {}
summary["capture_status"] = cap.get("capture_status")
summary["window_kind"] = (cap.get("window") or {}).get("kind")
summary["window_source"] = cap.get("window_source")

if cap.get("capture_status") != "captured":
    summary.update({"status": "skip", "reason": "sandbox log capture unavailable"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(2)

if summary["window_kind"] != "range":
    summary.update({"status": "fail", "reason": f"expected window.kind=range, got {summary['window_kind']!r}"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

if summary["window_source"] != "fence":
    summary.update({"status": "fail", "reason": f"expected window_source='fence', got {summary['window_source']!r}"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

(out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
PY

if [[ ${PY_STATUS} -eq 2 ]]; then
  test_skip "fence capture inconclusive (see artifacts)"
  exit 0
fi
if [[ ${PY_STATUS} -ne 0 ]]; then
  test_fail "fence capture validation failed (see ${OUT_DIR}/summary.json)"
fi

test_pass "fence capture ok" "{}"
