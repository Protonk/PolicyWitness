#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

CURRENT_STEP=""

test_begin "smoke" "xpc.q4_capture_targeting_synthetic"

fail() {
  test_fail "${CURRENT_STEP:-q4 capture targeting synthetic failed}"
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

step "synthetic_deny_log" "inherit_child synthetic log marker (capture pipeline control)"
PY_STATUS=0
/usr/bin/python3 - "${PW}" "${OUT_DIR}" "${DENY_PATH}" <<'PY' || PY_STATUS=$?
import json
import subprocess
import sys
from pathlib import Path

pw, out_dir, deny_path = sys.argv[1:]
out_dir = Path(out_dir)

# child-synthetic-deny-log emits a known log marker + witness event to validate capture targeting.
cmd = [
    pw, "xpc", "run", "--capture-sandbox-logs",
    "--profile", "temporary_exception",
    "inherit_child", "--scenario", "dynamic_extension",
    "--path", deny_path, "--allow-unsafe-path", "--child-synthetic-deny-log",
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

result = data.get("result") or {}
if result.get("ok") is not True:
    summary.update({"status": "fail", "reason": f"result.ok not true: {result!r}"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

cap = (data.get("data") or {}).get("host_sandbox_log_capture") or {}
obs = (cap.get("observer_report") or {}).get("data") or {}
witness = (data.get("data") or {}).get("witness") or {}
events = witness.get("events") or []

summary["capture_status"] = cap.get("capture_status")
summary["pid_source"] = cap.get("pid_source")
summary["observed_deny"] = obs.get("observed_deny")

if summary["capture_status"] != "captured":
    summary.update({"status": "skip", "reason": "sandbox log capture unavailable"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(2)

if summary["pid_source"] != "child_pid":
    summary.update({"status": "fail", "reason": f"expected child_pid, got {summary['pid_source']!r}"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

if summary["observed_deny"] is not True:
    summary.update({"status": "fail", "reason": "expected observed_deny=true from synthetic marker (capture pipeline control)"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

synthetic_events = [ev for ev in events if ev.get("phase") == "child_synthetic_deny_log"]
if not synthetic_events:
    summary.update({"status": "fail", "reason": "missing child_synthetic_deny_log event in witness (synthetic marker not emitted)"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

synthetic = synthetic_events[0].get("details") or {}
summary["synthetic_event"] = synthetic
if str(synthetic.get("synthetic", "")).lower() != "true":
    summary.update({"status": "fail", "reason": "synthetic event not marked synthetic"})
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

(out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
PY

if [[ ${PY_STATUS} -eq 2 ]]; then
  test_skip "q4 synthetic deny log inconclusive (see artifacts)"
  exit 0
fi
if [[ ${PY_STATUS} -ne 0 ]]; then
  test_fail "q4 synthetic deny log validation failed (see ${OUT_DIR}/summary.json)"
fi

test_pass "q4 synthetic deny log ok" "{}"
