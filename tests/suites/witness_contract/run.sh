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
# regression sentinel — if the baseline fails, every other failure
# becomes ambiguous.
run_test "${SUITE_DIR}/happy_path_baseline.sh"

run_test "${SUITE_DIR}/attempt_outcome_matrix_enforced.sh"
run_test "${SUITE_DIR}/bug_report_returns_attempts.sh"
run_test "${SUITE_DIR}/bug_report_returns_verdicts.sh"
run_test "${SUITE_DIR}/debuggable_mode_rejected.sh"
# drift_surfaced_in_envelope removed: its original premise (BBX-001
# mach-lookup global-name drift) was a wrong-filter-ID bug, not real
# drift, and was fixed by GLOBAL_NAME=2. All other known op+filter
# unreliabilities (iokit, sysctl) are now classified
# prediction_unavailable — also not drift. Reintroduce when a real
# current drift case is identified that the R10 steps[].drift field
# should surface.
run_test "${SUITE_DIR}/first_deny_diagnostic_populated.sh"
run_test "${SUITE_DIR}/instrumentation_field_rejected.sh"
run_test "${SUITE_DIR}/shm_sentinel_under_deny_default.sh"
run_test "${SUITE_DIR}/validator_spawn_failed_reports_degraded.sh"
run_test "${SUITE_DIR}/validator_subprocess_populated.sh"
run_test "${SUITE_DIR}/worker_post_apply_hang_seam.sh"

if [[ ${failures} -ne 0 ]]; then
  exit 1
fi
