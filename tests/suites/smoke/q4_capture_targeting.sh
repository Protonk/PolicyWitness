#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

CURRENT_STEP=""

test_begin "smoke" "xpc.q4_capture_targeting"

fail() {
  test_fail "${CURRENT_STEP:-q4 capture targeting failed}"
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

step "capture_auto_and_client" "inherit_child capture targeting (child-network-deny forces a real deny line)"
PY_STATUS=0
/usr/bin/python3 - "${PW}" "${OUT_DIR}" "${DENY_PATH}" <<'PY' || PY_STATUS=$?
import json
import os
import subprocess
import sys
from pathlib import Path

pw, out_dir, deny_path = sys.argv[1:]
out_dir = Path(out_dir)

attempts = [
    ("default", {}),
    ("range_iso", {"PW_CAPTURE_SANDBOX_LOGS_WINDOW": "range_iso"}),
]

def capture_info(obj):
    data = obj.get("data") or {}
    cap = data.get("host_sandbox_log_capture") or {}
    obs = cap.get("observer_report", {}).get("data", {})
    witness = data.get("witness") or {}
    events = witness.get("events") or []
    return {
        "capture_status": cap.get("capture_status"),
        "pid_source": cap.get("pid_source"),
        "target": cap.get("target"),
        "observed_deny": obs.get("observed_deny"),
        "observed_lines": obs.get("observed_lines"),
        "witness_capture_status": witness.get("sandbox_log_capture_status"),
        "network_attempt": any(ev.get("phase") == "child_network_attempt" for ev in events),
    }

def run_cmd(label, cmd, env):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    (out_dir / f"{label}.json").write_text(proc.stdout)
    (out_dir / f"{label}.stderr.txt").write_text(proc.stderr)
    (out_dir / f"{label}.rc.txt").write_text(str(proc.returncode))
    try:
        return json.loads(proc.stdout), None
    except Exception as exc:
        return None, f"{label} stdout not JSON: {exc}"

attempt_results = []
chosen = None

for idx, (attempt_label, extra_env) in enumerate(attempts):
    suffix = "" if idx == 0 else f"_{attempt_label}"
    env = os.environ.copy()
    env.update(extra_env)

    # child-network-deny is a diagnostic control: force a child-side deny line so targeting can be validated.
    auto_cmd = [
        pw, "xpc", "run", "--capture-sandbox-logs",
        "--profile", "temporary_exception",
        "inherit_child", "--scenario", "dynamic_extension",
        "--path", deny_path, "--allow-unsafe-path", "--child-network-deny",
    ]
    client_cmd = [
        pw, "xpc", "run", "--capture-sandbox-logs", "--capture-sandbox-logs-target", "client",
        "--profile", "temporary_exception",
        "inherit_child", "--scenario", "dynamic_extension",
        "--path", deny_path, "--allow-unsafe-path", "--child-network-deny",
    ]

    auto_data, err = run_cmd(f"auto{suffix}", auto_cmd, env)
    if err:
        summary = {"status": "fail", "reason": err}
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
        raise SystemExit(1)
    client_data, err = run_cmd(f"client{suffix}", client_cmd, env)
    if err:
        summary = {"status": "fail", "reason": err}
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
        raise SystemExit(1)

    info_auto = capture_info(auto_data)
    info_client = capture_info(client_data)
    attempt = {
        "label": attempt_label,
        "auto": info_auto,
        "client": info_client,
        "files": {
            "auto": str(out_dir / f"auto{suffix}.json"),
            "client": str(out_dir / f"client{suffix}.json"),
        },
    }
    attempt_results.append(attempt)

    if info_auto.get("capture_status") == "captured" and info_client.get("capture_status") == "captured":
        if info_auto.get("observed_deny") is True:
            chosen = attempt
            break

summary = {"status": "pass", "reason": "ok", "attempts": attempt_results}

if chosen is None:
    if any(
        attempt["auto"].get("capture_status") != "captured"
        or attempt["client"].get("capture_status") != "captured"
        for attempt in attempt_results
    ):
        summary["status"] = "skip"
        summary["reason"] = "sandbox log capture not available"
    else:
        summary["status"] = "skip"
        summary["reason"] = "auto capture observed no deny lines; child-network-deny should force denies, so targeting cannot be validated"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(2)

info_auto = chosen["auto"]
info_client = chosen["client"]
summary["chosen_attempt"] = chosen["label"]
summary["auto"] = info_auto
summary["client"] = info_client
summary["files"] = chosen["files"]

if info_auto.get("pid_source") != "child_pid":
    summary["status"] = "fail"
    summary["reason"] = f"auto pid_source expected child_pid, got {info_auto.get('pid_source')!r}"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(1)

if info_client.get("pid_source") != "client_pid":
    summary["status"] = "fail"
    summary["reason"] = f"client pid_source expected client_pid, got {info_client.get('pid_source')!r}"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(1)

if info_auto.get("network_attempt") is not True or info_client.get("network_attempt") is not True:
    summary["status"] = "fail"
    summary["reason"] = "missing child_network_attempt event (diagnostic child-network-deny did not run)"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(1)

if info_auto.get("observed_deny") is not True:
    summary["status"] = "skip"
    summary["reason"] = "auto capture observed no deny lines; child-network-deny should force denies, so targeting cannot be validated"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(2)

if info_client.get("observed_deny") is not False:
    summary["status"] = "fail"
    summary["reason"] = f"client observed_deny expected false, got {info_client.get('observed_deny')!r}"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(1)

if info_auto.get("witness_capture_status") != "captured":
    summary["status"] = "fail"
    summary["reason"] = "witness capture status not captured for auto"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(1)

if info_client.get("witness_capture_status") != "captured":
    summary["status"] = "fail"
    summary["reason"] = "witness capture status not captured for client"
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    raise SystemExit(1)

(out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
PY

if [[ ${PY_STATUS} -eq 2 ]]; then
  test_skip "q4 capture targeting inconclusive (see artifacts)"
  exit 0
fi
if [[ ${PY_STATUS} -ne 0 ]]; then
  test_fail "q4 capture targeting validation failed (see ${OUT_DIR}/summary.json)"
fi

test_pass "q4 capture targeting ok" "{}"
