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

run_test "${ROOT_DIR}/tests/suites/anomalies/sbpl_allowdeny_v1.sh"
run_test "${ROOT_DIR}/tests/suites/anomalies/sonoma_cross_check.sh"

if [[ ${failures} -ne 0 ]]; then
  exit 1
fi
