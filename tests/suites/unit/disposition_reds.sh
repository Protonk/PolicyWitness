#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

# Non-default case: the disposition record plan's #[ignore]d Rust reds.
# rust.unit runs the whole crate, so these carry #[ignore] with the plan's
# reason and run explicitly here, keeping the default battery green while --all and
# --suite opt_in still exercise them. Red by design until the controller change
# lands; promotion removes the attribute. See tests/OPT_IN_TESTS.md.
test_begin "unit" "rust.disposition_reds"

LOG_PATH="${PW_TEST_ARTIFACTS}/cargo-test-ignored.log"
TEST_NAME="run_flow::tests::conflicting_status_representation_is_not_silently_resolved"

test_step "cargo_test_ignored" "run exact disposition test ${TEST_NAME}, including ignored tests (B1)"
set +e
cargo test --manifest-path "${ROOT_DIR}/controller/Cargo.toml" --bin policy-witness -- --include-ignored --exact "${TEST_NAME}" >"${LOG_PATH}" 2>&1
status=$?
set -e

if [[ ${status} -ne 0 ]]; then
  if [[ ${status} -eq 101 ]] &&
     grep -Fxq "test ${TEST_NAME} ... FAILED" "${LOG_PATH}" &&
     grep -Fq 'test result: FAILED. 0 passed; 1 failed; 0 ignored;' "${LOG_PATH}" &&
     grep -Fq 'exit_code 0 beside term_signal 9 is an invalid status pair; an unqualified disposition (signaled) resolves it silently' "${LOG_PATH}"; then
    test_fail "B1 behavioral red: conflicting status silently resolved as signaled" "{\"log_path\":\"${LOG_PATH}\"}"
  fi
  test_fail "disposition test execution failed without the expected B1 assertion (exit ${status})" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if ! grep -Fxq "test ${TEST_NAME} ... ok" "${LOG_PATH}" ||
   ! grep -Fq 'test result: ok. 1 passed; 0 failed; 0 ignored;' "${LOG_PATH}"; then
  test_fail "the exact disposition test did not run successfully: ${TEST_NAME}" "{\"log_path\":\"${LOG_PATH}\"}"
fi

test_pass "disposition test passes; it remains selectable after removing #[ignore]" "{\"log_path\":\"${LOG_PATH}\"}"
