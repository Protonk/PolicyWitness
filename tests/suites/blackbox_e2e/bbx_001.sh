#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="blackbox_e2e"
PW_TEST_ID="BBX-001"

PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
PROFILE_SBPL="${ROOT_DIR}/tests/fixtures/blackbox_e2e/BBX-001/profile.sbpl"
SPECIMEN_TEMPLATE="${ROOT_DIR}/tests/fixtures/blackbox_e2e/BBX-001/specimen.template.json"
EXPECTED_JSON="${ROOT_DIR}/tests/fixtures/blackbox_e2e/BBX-001/expected.json"
VALIDATE_PY="${ROOT_DIR}/tests/suites/blackbox_e2e/validate_run.py"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "SBPL params + deny-signal on file-write"

if [[ ! -x "${PW_BIN}" ]]; then
  test_skip "PolicyWitness.app is missing or not built at ${PW_BIN}"
  exit 0
fi
if [[ ! -f "${PROFILE_SBPL}" ]]; then
  test_fail "fixture missing: ${PROFILE_SBPL}"
fi
if [[ ! -f "${SPECIMEN_TEMPLATE}" ]]; then
  test_fail "fixture missing: ${SPECIMEN_TEMPLATE}"
fi
if [[ ! -f "${EXPECTED_JSON}" ]]; then
  test_fail "fixture missing: ${EXPECTED_JSON}"
fi

WORK_ROOT="${PW_TEST_ARTIFACTS}/workspace"
ALLOW_DIR="${WORK_ROOT}/allow-write"
DENY_DIR="${WORK_ROOT}/deny-write"
ALLOW_FILE="${ALLOW_DIR}/existing.txt"
DENY_FILE="${DENY_DIR}/existing.txt"

mkdir -p "${ALLOW_DIR}" "${DENY_DIR}"
printf 'seed\n' >"${ALLOW_FILE}"
printf 'seed\n' >"${DENY_FILE}"

SPECIMEN_JSON="${PW_TEST_ARTIFACTS}/specimen.rendered.json"

/usr/bin/python3 - "${PROFILE_SBPL}" "${SPECIMEN_TEMPLATE}" "${SPECIMEN_JSON}" "${ALLOW_FILE}" "${DENY_FILE}" "${ALLOW_DIR}" "${DENY_DIR}" <<'PY'
import json
import os
import sys
from pathlib import Path

sbpl_path, template_path, out_path, allow_file, deny_file, allow_dir, deny_dir = sys.argv[1:8]

sbpl = Path(sbpl_path).read_text(encoding="utf-8")
template = json.loads(Path(template_path).read_text(encoding="utf-8"))

def rp(p: str) -> str:
    return os.path.realpath(p)

allow_dir_rp = rp(allow_dir)
deny_dir_rp = rp(deny_dir)
allow_file_rp = rp(allow_file)
deny_file_rp = rp(deny_file)

template["policy"]["sbpl_source"] = sbpl
template["policy"]["params"]["ALLOW_WRITE_DIR"] = allow_dir_rp
template["policy"]["params"]["DENY_WRITE_DIR"] = deny_dir_rp

for step in template.get("probe_plan", []):
    attempt = step.get("attempt") or {}
    sandbox_check = step.get("sandbox_check") or {}
    filt = sandbox_check.get("filter") or {}

    if attempt.get("kind") == "file":
        if attempt.get("target") == "__ALLOW_WRITE_FILE__":
            attempt["target"] = allow_file_rp
            filt["value"] = allow_file_rp
        elif attempt.get("target") == "__DENY_WRITE_FILE__":
            attempt["target"] = deny_file_rp
            filt["value"] = deny_file_rp

Path(out_path).write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_JSON}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  test_fail "policy-witness run failed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

set +e
VALIDATE_OUT="$(${VALIDATE_PY} "${RUN_STDOUT}" "${EXPECTED_JSON}" 2>&1)"
STATUS=$?
set -e

if [[ ${STATUS} -ne 0 ]]; then
  if [[ ${STATUS} -eq 3 ]]; then
    VALIDATE_OUT="${VALIDATE_OUT//$'\n'/ }"
    test_skip "${VALIDATE_OUT}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
    exit 0
  fi
  VALIDATE_OUT="${VALIDATE_OUT//$'\n'/ }"
  test_fail "${VALIDATE_OUT}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

test_pass "blackbox e2e ok" "{}"
