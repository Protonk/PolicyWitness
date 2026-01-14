#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="blackbox_e2e"
PW_TEST_ID="BBX-003"

PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
SPECIMEN_TEMPLATE="${ROOT_DIR}/tests/fixtures/blackbox_e2e/BBX-003/specimen.template.json"
EXPECTED_JSON="${ROOT_DIR}/tests/fixtures/blackbox_e2e/BBX-003/expected.json"
COMPILED_B64_PATH="${ROOT_DIR}/tests/fixtures/blackbox_e2e/BBX-003/profile.compiled.b64"
VALIDATE_PY="${ROOT_DIR}/tests/suites/blackbox_e2e/validate_run.py"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "compiled profile bytes + denial via D + attempt"

if [[ ! -x "${PW_BIN}" ]]; then
  test_skip "PolicyWitness.app is missing or not built at ${PW_BIN}"
  exit 0
fi
if [[ ! -f "${SPECIMEN_TEMPLATE}" ]]; then
  test_fail "fixture missing: ${SPECIMEN_TEMPLATE}"
fi
if [[ ! -f "${EXPECTED_JSON}" ]]; then
  test_fail "fixture missing: ${EXPECTED_JSON}"
fi
if [[ ! -f "${COMPILED_B64_PATH}" ]]; then
  test_fail "compiled profile blob missing: ${COMPILED_B64_PATH}"
fi

COMPILED_B64="$(tr -d '\n' <"${COMPILED_B64_PATH}")"
if [[ -z "${COMPILED_B64}" ]] || [[ "${COMPILED_B64}" == "__REPLACE_WITH_COMPILED_PROFILE_B64__" ]]; then
  test_fail "compiled profile blob not set: ${COMPILED_B64_PATH}"
fi

WORK_ROOT="${PW_TEST_ARTIFACTS}/workspace"
ALLOW_DIR="${WORK_ROOT}/allow-read"
ALLOW_FILE="${ALLOW_DIR}/existing.txt"

mkdir -p "${ALLOW_DIR}"
printf 'seed\n' >"${ALLOW_FILE}"

SPECIMEN_JSON="${PW_TEST_ARTIFACTS}/specimen.rendered.json"

/usr/bin/python3 - "${SPECIMEN_TEMPLATE}" "${SPECIMEN_JSON}" "${ALLOW_FILE}" "${COMPILED_B64}" <<'PY'
import json
import os
import sys
from pathlib import Path

template_path, out_path, allow_file, compiled_b64 = sys.argv[1:5]

template = json.loads(Path(template_path).read_text(encoding="utf-8"))

def rp(p: str) -> str:
    return os.path.realpath(p)

allow_file_rp = rp(allow_file)

template["policy"]["compiled_profile_b64"] = compiled_b64

for step in template.get("probe_plan", []):
    attempt = step.get("attempt") or {}
    sandbox_check = step.get("sandbox_check") or {}
    filt = sandbox_check.get("filter") or {}

    if attempt.get("kind") == "file":
        if attempt.get("target") == "__ALLOW_READ_FILE__":
            attempt["target"] = allow_file_rp
            filt["value"] = allow_file_rp

Path(out_path).write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_JSON}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  set +e
  SKIP_REASON="$(
    /usr/bin/python3 - "${RUN_STDOUT}" 2>/dev/null <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    env = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)

err = (env.get("result") or {}).get("error") or ""
if "sandbox_register_profile failed: Operation not permitted" in err:
    print("compiled profile registration not permitted on this host")
    raise SystemExit(0)

runner_err = ((env.get("data") or {}).get("runner_result") or {}).get("error") or ""
if "sandbox_register_profile failed: Operation not permitted" in runner_err:
    print("compiled profile registration not permitted on this host")
    raise SystemExit(0)

raise SystemExit(1)
PY
  )"
  STATUS=$?
  set -e

  if [[ ${STATUS} -eq 0 ]]; then
    test_skip "${SKIP_REASON}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
    exit 0
  fi

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
