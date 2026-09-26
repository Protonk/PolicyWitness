#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_byoxpc registry_recovery
test_require_pw
test_step registry "exercise real CLI persistence, launchd observations, pending cleanup and recovery"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "registry recovery controls failed" \
  "${ROOT_DIR}/tests/suites/runner_byoxpc/opt_in/registry_recovery.py" "${PW_TEST_ARTIFACTS}" "${PW_APP_DIR}" "${PW_BIN}"
test_pass "registry state survives partial installation and cleanup; live owned services are absent after recovery"
