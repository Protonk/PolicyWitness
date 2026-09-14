#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

source "${ROOT_DIR}/tests/lib/scripts.sh"

scripts=(
  "${ROOT_DIR}/tests/suites/blackbox_e2e/checker_controls.sh"
  "${ROOT_DIR}/tests/suites/blackbox_e2e/bbx_001.sh"
  "${ROOT_DIR}/tests/suites/blackbox_e2e/bbx_002.sh"
)
test_run_scripts "${scripts[@]}"
