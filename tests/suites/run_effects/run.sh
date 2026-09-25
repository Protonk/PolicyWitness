#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SUITE_DIR="${ROOT_DIR}/tests/suites/run_effects"

source "${ROOT_DIR}/tests/lib/scripts.sh"

# Controls run first: if an expectation accepts a wrong observation, the live
# cases below prove nothing.
scripts=(
  "${SUITE_DIR}/checker_controls.sh"
  "${SUITE_DIR}/file_actions_have_exact_effects.sh"
  "${SUITE_DIR}/exec_helper_effect_is_real.sh"
  "${SUITE_DIR}/run_installs_nothing.sh"
)
test_run_scripts "${scripts[@]}"
