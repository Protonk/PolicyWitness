#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

if [[ -z "${PW_TEST_OUT_DIR:-}" ]]; then
  export PW_TEST_OUT_DIR="${ROOT_DIR}/tests/out"
fi

PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
export PW_BIN

failures=0

run_test() {
  local script="$1"
  set +e
  bash "${script}"
  local status=$?
  set -e
  if [[ ${status} -ne 0 ]]; then
    failures=1
  fi
}

export PW_TEST_SUITE_OVERRIDE="runner_machme"
unset PW_TEST_RUNNER_MODE
unset PW_TEST_RUNNER_SERVICE
unset PW_TEST_RUNNER_EXPECT_KIND

RUNNER_ENV_PATH="${PW_TEST_OUT_DIR}/suites/runner_machme/runner_install/artifacts/runner_env.json"
export PW_TEST_RUNNER_ENV_PATH="${RUNNER_ENV_PATH}"

run_test "${ROOT_DIR}/tests/suites/runner_machme/runner_install.sh"
if [[ ${failures} -ne 0 ]]; then
  exit 1
fi
if [[ ! -f "${RUNNER_ENV_PATH}" ]]; then
  exit 0
fi

read -r RUNNER_ID SERVICE_NAME < <(/usr/bin/python3 - "${RUNNER_ENV_PATH}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(env.get("runner_id", ""), env.get("service_name", ""))
PY
)
if [[ -z "${RUNNER_ID}" || -z "${SERVICE_NAME}" ]]; then
  echo "missing runner_id/service_name in ${RUNNER_ENV_PATH}" 1>&2
  exit 1
fi

cleanup() {
  if [[ -n "${RUNNER_ID:-}" ]]; then
    "${PW_BIN}" runner remove --id "${RUNNER_ID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

export PW_TEST_RUNNER_MODE="machme"
export PW_TEST_RUNNER_SERVICE="${SERVICE_NAME}"
export PW_TEST_RUNNER_EXPECT_KIND="machme"

run_test "${ROOT_DIR}/tests/suites/smoke/pw_specimen_smoke.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/pw_instrumentation_execmem.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/pw_instrumentation_invalid_phase.sh"
run_test "${ROOT_DIR}/tests/suites/blackbox_menagerie/run.sh"
run_test "${ROOT_DIR}/tests/suites/blackbox_e2e/run.sh"

if [[ ${failures} -ne 0 ]]; then
  exit 1
fi
