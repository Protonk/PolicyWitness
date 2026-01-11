#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

CURRENT_STEP=""

test_begin "smoke" "xpc.q3_session_consume"

fail() {
  test_fail "${CURRENT_STEP:-q3 session consume failed}"
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

step "session_consume" "issue token + consume in a single session"
PY_STATUS=0
/usr/bin/python3 - "${PW}" "${OUT_DIR}" "${DENY_PATH}" <<'PY' || PY_STATUS=$?
import json
import subprocess
import sys
from pathlib import Path

pw, out_dir, deny_path = sys.argv[1:]
out_dir = Path(out_dir)

issue_cmd = [
    pw, "xpc", "run",
    "--profile", "temporary_exception",
    "sandbox_extension",
    "--op", "issue_file",
    "--class", "com.apple.app-sandbox.read",
    "--path", deny_path,
    "--allow-unsafe-path",
]

issue = subprocess.run(issue_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
(out_dir / "issue.json").write_text(issue.stdout)
(out_dir / "issue.stderr.txt").write_text(issue.stderr)
(out_dir / "issue.rc.txt").write_text(str(issue.returncode))

try:
    issue_json = json.loads(issue.stdout)
except Exception as exc:
    (out_dir / "summary.json").write_text(json.dumps({
        "status": "fail",
        "reason": f"issue stdout not JSON: {exc}",
    }, indent=2))
    raise SystemExit(1)

token = ((issue_json.get("data") or {}).get("details") or {}).get("token")
if not token:
    (out_dir / "summary.json").write_text(json.dumps({
        "status": "fail",
        "reason": "missing token from issue response",
    }, indent=2))
    raise SystemExit(1)

session_cmd = [pw, "xpc", "session", "--profile", "minimal"]
proc = subprocess.Popen(session_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
commands = [
    {"command": "run_probe", "probe_id": "fs_op", "argv": ["--op", "open_read", "--path", deny_path]},
    {"command": "run_probe", "probe_id": "sandbox_extension", "argv": ["--op", "consume", "--token", token]},
    {"command": "run_probe", "probe_id": "fs_op", "argv": ["--op", "open_read", "--path", deny_path]},
    {"command": "close_session"},
]
proc.stdin.write("\n".join(json.dumps(c) for c in commands) + "\n")
proc.stdin.flush()
stdout, stderr = proc.communicate(timeout=240)
(out_dir / "session.jsonl").write_text(stdout)
(out_dir / "session.stderr.txt").write_text(stderr)
(out_dir / "session.rc.txt").write_text(str(proc.returncode))

lines = [line for line in stdout.splitlines() if line.strip()]
entries = [json.loads(line) for line in lines]
probe_resps = [e for e in entries if e.get("kind") == "probe_response"]
session_ready = next((e for e in entries if e.get("kind") == "xpc_session_event" and (e.get("data") or {}).get("event") == "session_ready"), None)

summary = {
    "probe_count": len(probe_resps),
    "session_ready_pid": (session_ready or {}).get("data", {}).get("pid"),
    "probe_sequence": [
        {
            "ok": (r.get("result") or {}).get("ok"),
            "normalized_outcome": (r.get("result") or {}).get("normalized_outcome"),
            "service_pid": ((r.get("data") or {}).get("details") or {}).get("service_pid"),
        }
        for r in probe_resps
    ],
}

if len(probe_resps) < 3:
    summary["status"] = "fail"
    summary["reason"] = "missing probe responses"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(1)

pid0 = summary["probe_sequence"][0]["service_pid"]
for entry in summary["probe_sequence"]:
    if entry["service_pid"] != pid0:
        summary["status"] = "fail"
        summary["reason"] = "service pid changed within session"
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
        raise SystemExit(1)

if summary["session_ready_pid"] is not None and str(summary["session_ready_pid"]) != str(pid0):
    summary["status"] = "fail"
    summary["reason"] = "session_ready pid differs from probe pid"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(1)

before_ok = summary["probe_sequence"][0]["ok"]
consume_ok = summary["probe_sequence"][1]["ok"]
after_ok = summary["probe_sequence"][2]["ok"]

if before_ok is True:
    summary["status"] = "skip"
    summary["reason"] = "open_read succeeded before consume (deny path not denied on this host)"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(2)

if consume_ok is not True:
    summary["status"] = "fail"
    summary["reason"] = "consume did not succeed"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(1)

if after_ok is not True:
    summary["status"] = "fail"
    summary["reason"] = "open_read did not succeed after consume"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(1)

summary["status"] = "pass"
summary["reason"] = "ok"
(out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
PY

if [[ ${PY_STATUS} -eq 2 ]]; then
  test_skip "q3 session consume inconclusive (see artifacts)"
  exit 0
fi
if [[ ${PY_STATUS} -ne 0 ]]; then
  test_fail "q3 session consume validation failed (see ${OUT_DIR}/summary.json)"
fi

test_pass "q3 session consume ok" "{}"
