#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="${PW_TEST_SUITE_OVERRIDE:-blackbox_e2e}"
PW_TEST_ID="BBX-002"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
PROFILE_SBPL="${ROOT_DIR}/tests/fixtures/blackbox_e2e/BBX-002/profile.sbpl"
SPECIMEN_TEMPLATE="${ROOT_DIR}/tests/fixtures/blackbox_e2e/BBX-002/specimen.template.json"
EXPECTED_JSON="${ROOT_DIR}/tests/fixtures/blackbox_e2e/BBX-002/expected.json"
VALIDATE_PY="${ROOT_DIR}/tests/suites/blackbox_e2e/validate_run.py"

INVALID_MACH_SERVICE="com.example.policywitness.invalid"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "plain SBPL + negative controls"

if ! require_pw_app "${PW_BIN}"; then
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
ALLOW_DIR="${WORK_ROOT}/allow-read"
ALLOW_FILE="${ALLOW_DIR}/existing.txt"
MISSING_FILE="${WORK_ROOT}/does-not-exist.txt"

mkdir -p "${ALLOW_DIR}"
printf 'seed\n' >"${ALLOW_FILE}"

SPECIMEN_JSON="${PW_TEST_ARTIFACTS}/specimen.rendered.json"

/usr/bin/python3 - "${PROFILE_SBPL}" "${SPECIMEN_TEMPLATE}" "${SPECIMEN_JSON}" "${ALLOW_FILE}" "${MISSING_FILE}" "${INVALID_MACH_SERVICE}" <<'PY'
import json
import os
import sys
from pathlib import Path

sbpl_path, template_path, out_path, allow_file, missing_file, invalid_service = sys.argv[1:7]

sbpl = Path(sbpl_path).read_text(encoding="utf-8")
template = json.loads(Path(template_path).read_text(encoding="utf-8"))

def rp(p: str) -> str:
    return os.path.realpath(p)

allow_file_rp = rp(allow_file)
missing_file_rp = rp(missing_file)

template["policy"]["sbpl_source"] = sbpl

for step in template.get("probe_plan", []):
    attempt = step.get("attempt") or {}
    sandbox_check = step.get("sandbox_check") or {}
    filt = sandbox_check.get("filter") or {}

    if attempt.get("kind") == "file":
        if attempt.get("target") == "__ALLOW_READ_FILE__":
            attempt["target"] = allow_file_rp
            filt["value"] = allow_file_rp
        elif attempt.get("target") == "__MISSING_FILE__":
            attempt["target"] = missing_file_rp
            filt["value"] = missing_file_rp
    elif attempt.get("kind") == "mach_lookup":
        if attempt.get("target") == "__INVALID_MACH_SERVICE__":
            attempt["target"] = invalid_service
            filt["value"] = invalid_service

Path(out_path).write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

render_specimen_with_runner "${SPECIMEN_JSON}" "${SPECIMEN_JSON}"

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

KIND_ERR="$(assert_runner_kind "${RUN_STDOUT}")" || test_fail "${KIND_ERR}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"

test_pass "blackbox e2e ok" "{}"
