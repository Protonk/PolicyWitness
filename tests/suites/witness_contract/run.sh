#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SUITE_DIR="${ROOT_DIR}/tests/suites/witness_contract"

source "${ROOT_DIR}/tests/lib/scripts.sh"

# Order is alphabetical except happy_path_baseline runs first as the
# regression sentinel — if the baseline fails, every other failure
# becomes ambiguous.
scripts=(
  "${SUITE_DIR}/happy_path_baseline.sh"

  "${SUITE_DIR}/attempt_outcome_matrix_enforced.sh"
  "${SUITE_DIR}/bug_report_returns_attempts.sh"
  "${SUITE_DIR}/bug_report_returns_verdicts.sh"
  "${SUITE_DIR}/create_existing_file_preserves_contents.sh"
  "${SUITE_DIR}/debuggable_mode_rejected.sh"
# drift_surfaced_in_envelope removed: its original premise (BBX-001
# mach-lookup global-name drift) was a wrong-filter-ID bug, not real
# drift, and was fixed by GLOBAL_NAME=2. All other known op+filter
# unreliabilities (iokit, sysctl) are now classified
# prediction_unavailable — also not drift. Reintroduce when a real
# current drift case is identified that the R10 steps[].drift field
# should surface.
  "${SUITE_DIR}/runner_sandbox_diagnostics_on_denied.sh"
  "${SUITE_DIR}/instrumentation_field_rejected.sh"
  "${SUITE_DIR}/prediction_target_is_independent_of_attempt_target.sh"
  "${SUITE_DIR}/shm_sentinel_under_deny_default.sh"
  "${SUITE_DIR}/validator_decode_failure_reports_degraded.sh"
  "${SUITE_DIR}/validator_spawn_failed_reports_degraded.sh"
  "${SUITE_DIR}/validator_subprocess_populated.sh"
  "${SUITE_DIR}/validator_unavailable_reports_degraded.sh"
  "${SUITE_DIR}/worker_post_apply_hang_seam.sh"
  "${SUITE_DIR}/drift_determination_via_validator_seam.sh"
)
test_run_scripts "${scripts[@]}"
