#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

source "${ROOT_DIR}/tests/lib/scripts.sh"

scripts=()
for script in "${ROOT_DIR}/tests/suites/opt_in/"*.sh; do
  if [[ "$(basename "${script}")" == "run.sh" ]]; then
    continue
  fi
  scripts+=("${script}")
done

test_run_scripts "${scripts[@]}"
