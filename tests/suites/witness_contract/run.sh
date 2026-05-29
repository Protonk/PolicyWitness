#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SUITE_DIR="${ROOT_DIR}/tests/suites/witness_contract"

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

# Order is alphabetical except happy_path_baseline runs first as the
# regression sentinel — if the baseline fails, every other PHASE 0
# failure becomes ambiguous.
run_test "${SUITE_DIR}/happy_path_baseline.sh"

run_test "${SUITE_DIR}/attempt_outcome_matrix_enforced.sh"
run_test "${SUITE_DIR}/bug_report_returns_attempts.sh"
run_test "${SUITE_DIR}/bug_report_returns_verdicts.sh"
run_test "${SUITE_DIR}/debuggable_mode_rejected.sh"
run_test "${SUITE_DIR}/drift_surfaced_in_envelope.sh"
run_test "${SUITE_DIR}/first_deny_diagnostic_populated.sh"
run_test "${SUITE_DIR}/instrumentation_field_rejected.sh"
run_test "${SUITE_DIR}/shm_sentinel_under_deny_default.sh"
run_test "${SUITE_DIR}/validator_handles_none_filter.sh"
run_test "${SUITE_DIR}/validator_spawn_failed_reports_degraded.sh"
run_test "${SUITE_DIR}/validator_subprocess_populated.sh"
run_test "${SUITE_DIR}/worker_post_apply_hang_seam.sh"

if [[ ${failures} -ne 0 ]]; then
  exit 1
fi
