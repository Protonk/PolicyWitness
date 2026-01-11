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

run_test "${ROOT_DIR}/tests/suites/smoke/experiments_tri_run.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/xpc_app_smoke.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/q1_dlopen_external.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/q2_inherit_child_dynamic_extension.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/q3_session_consume.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/q4_capture_targeting.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/q4_capture_targeting_synthetic.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/xpc.fence_capture.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/pw_lab_signposts.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/pw_lab_scenarios.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/pw_lab_tui_ungetch.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/pw_lab_tui_pty.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/q5_update_file_rename_delta.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/q6_bookmark_ferry.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/q7_gatekeeper_connection.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/q8_attribution_bounds.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/inherit_child_fixtures.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/update_file_rename_delta_fixtures.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/xpc_session_smoke.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/quarantine_smoke.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/observer_smoke.sh"

if [[ ${failures} -ne 0 ]]; then
  exit 1
fi
