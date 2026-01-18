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

for script in "${ROOT_DIR}/tests/suites/opt_in/"*.sh; do
  if [[ "$(basename "${script}")" == "run.sh" ]]; then
    continue
  fi
  run_test "${script}"
done

if [[ ${failures} -ne 0 ]]; then
  exit 1
fi
