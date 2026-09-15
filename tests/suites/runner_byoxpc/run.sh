#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"

if [[ -z "${PW_TEST_OUT_DIR:-}" ]]; then
  export PW_TEST_OUT_DIR="${ROOT_DIR}/tests/out"
fi

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
export PW_BIN

source "${ROOT_DIR}/tests/lib/scripts.sh"
source "${ROOT_DIR}/tests/lib/testlib.sh"

export PW_TEST_SUITE_OVERRIDE="runner_byoxpc"
unset PW_TEST_RUNNER_MODE
unset PW_TEST_RUNNER_SERVICE
unset PW_TEST_RUNNER_EXPECT_KIND

failures=0
if test_selected runner_auth_external; then
  test_run_scripts "${ROOT_DIR}/tests/suites/runner_byoxpc/opt_in/runner_auth_external.sh" || failures=1
fi

if ! test_selected runner_install; then exit "${failures}"; fi

RUNNER_ENV_PATH="${PW_TEST_OUT_DIR}/suites/runner_byoxpc/runner_install/artifacts/runner_env.json"
export PW_TEST_RUNNER_ENV_PATH="${RUNNER_ENV_PATH}"

if ! test_run_scripts "${ROOT_DIR}/tests/suites/runner_byoxpc/runner_install.sh"; then
  exit 1
fi
if [[ ! -f "${RUNNER_ENV_PATH}" ]]; then
  exit "${failures}"
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

export PW_TEST_RUNNER_MODE="byoxpc"
export PW_TEST_RUNNER_SERVICE="${SERVICE_NAME}"
export PW_TEST_RUNNER_EXPECT_KIND="byoxpc"

if [[ -n "${PW_TEST_CASES+x}" ]]; then
  # Each selected leaf gets its own process. A failed specimen cannot suppress
  # an independent later specimen; the shared runner is removed by the trap.
  while IFS= read -r leaf; do
    case "$leaf" in
      runner_install|runner_auth_external) continue ;;
      specimen_file_read_deny) script="smoke/pw_specimen_smoke.sh" ;;
      BBX-001) script="blackbox_e2e/bbx_001.sh" ;;
      BBX-002) script="blackbox_e2e/bbx_002.sh" ;;
      core_*|opt_*) script="blackbox_menagerie/run.sh" ;;
      *) echo "unknown BYOXPC leaf: $leaf" >&2; exit 2 ;;
    esac
    PW_TEST_CASES="$leaf" test_run_scripts "${ROOT_DIR}/tests/suites/${script}" || failures=1
  done <<< "${PW_TEST_CASES}"
else
  test_run_scripts \
    "${ROOT_DIR}/tests/suites/smoke/pw_specimen_smoke.sh" \
    "${ROOT_DIR}/tests/suites/blackbox_menagerie/run.sh" \
    "${ROOT_DIR}/tests/suites/blackbox_e2e/run.sh" || failures=1
fi
exit "${failures}"
