#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

CURRENT_STEP=""

test_begin "smoke" "inherit_child.q2_dynamic_extension"

fail() {
  test_fail "${CURRENT_STEP:-q2 inherit_child dynamic_extension failed}"
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

step "inherit_child_dynamic_extension" "inherit_child dynamic_extension (acquire vs use witness)"
RUN_JSON="${OUT_DIR}/inherit-child-dynamic-extension.json"
"${PW}" xpc run --profile temporary_exception inherit_child --scenario dynamic_extension --path "${DENY_PATH}" --allow-unsafe-path >"${RUN_JSON}"

step "validate_witness" "validate acquire vs use witness fields"
PY_STATUS=0
/usr/bin/python3 - "${RUN_JSON}" "${OUT_DIR}/summary.json" <<'PY' || PY_STATUS=$?
import json
import sys
from pathlib import Path

run_path, summary_path = sys.argv[1:]

data = json.loads(Path(run_path).read_text(encoding="utf-8", errors="replace"))

summary = {"status": "pass", "reason": "ok"}

if data.get("kind") != "probe_response":
    summary["status"] = "fail"
    summary["reason"] = f"unexpected kind: {data.get('kind')!r}"
    Path(summary_path).write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

result = data.get("result") or {}
if result.get("ok") is not True:
    summary["status"] = "fail"
    summary["reason"] = f"result.ok not true: {result!r}"
    Path(summary_path).write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

witness = (data.get("data") or {}).get("witness") or {}
cap_results = witness.get("capability_results")
if not isinstance(cap_results, list):
    summary["status"] = "fail"
    summary["reason"] = "missing witness.capability_results"
    Path(summary_path).write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

file_fd = None
for cap in cap_results:
    if isinstance(cap, dict) and cap.get("cap_id") == "file_fd":
        file_fd = cap
        break

if file_fd is None:
    summary["status"] = "fail"
    summary["reason"] = "missing capability_results entry for file_fd"
    Path(summary_path).write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

for key in ("parent_acquire", "child_acquire", "child_use"):
    if key not in file_fd:
        summary["status"] = "fail"
        summary["reason"] = f"missing file_fd.{key}"
        Path(summary_path).write_text(json.dumps(summary, indent=2, sort_keys=True))
        raise SystemExit(1)

parent = file_fd.get("parent_acquire") or {}
child_use = file_fd.get("child_use") or {}

if parent.get("rc") not in (0, "0"):
    summary["status"] = "fail"
    summary["reason"] = f"parent_acquire.rc not ok: {parent!r}"
    Path(summary_path).write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

if child_use.get("rc") not in (0, "0"):
    summary["status"] = "fail"
    summary["reason"] = f"child_use.rc not ok: {child_use!r}"
    Path(summary_path).write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

summary.update({
    "status": "pass",
    "reason": "ok",
    "outcome_summary": witness.get("outcome_summary"),
    "file_fd": file_fd,
})
Path(summary_path).write_text(json.dumps(summary, indent=2, sort_keys=True))
PY

if [[ ${PY_STATUS} -ne 0 ]]; then
  test_fail "q2 inherit_child dynamic_extension validation failed (see ${OUT_DIR}/summary.json)"
fi

test_pass "q2 inherit_child dynamic_extension ok" "{}"
