#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

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

run_test "${ROOT_DIR}/tests/suites/smoke/pw_specimen_smoke.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/pw_runner_smoke_v1.sh"

if [[ ${failures} -ne 0 ]]; then
  exit 1
fi
