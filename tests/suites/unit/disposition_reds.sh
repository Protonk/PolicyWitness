#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

# Select the disposition regressions by exact name and require every result.
# These tests also run in rust.unit's full binary batch.
test_begin "unit" "rust.disposition_reds"

LOG_PATH="${PW_TEST_ARTIFACTS}/cargo-test-ignored.log"
declare -a NAMES=(
  "disposition::tests::conflicting_status_representation_is_not_silently_resolved"
  "disposition::tests::conflicting_status_reports_the_status_rule"
  "disposition::tests::disposition_record_projects_witnessed_host_cleanup_cause"
  "disposition::tests::record_contradicting_its_basis_is_withheld"
)

test_step "cargo_test_ignored" "run the exact disposition tests for status conflict, projection and withholding"
set +e
cargo test --manifest-path "${ROOT_DIR}/controller/Cargo.toml" --bin policy-witness -- --include-ignored --exact "${NAMES[@]}" >"${LOG_PATH}" 2>&1
status=$?
set -e

for name in "${NAMES[@]}"; do
  if grep -Fxq "test ${name} ... FAILED" "${LOG_PATH}"; then
    test_fail "disposition test failed: ${name} (exit ${status})" "{\"log_path\":\"${LOG_PATH}\"}"
  elif ! grep -Fxq "test ${name} ... ok" "${LOG_PATH}"; then
    test_fail "disposition test did not run or pass: ${name} (exit ${status})" "{\"log_path\":\"${LOG_PATH}\"}"
  fi
done
if ! grep -Eq "^running ${#NAMES[@]} tests$" "${LOG_PATH}"; then
  test_fail "unexpected test selection; expected exactly ${#NAMES[@]} tests to run" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${status}" -ne 0 ]]; then
  test_fail "cargo exited ${status} although every disposition test passed" "{\"log_path\":\"${LOG_PATH}\"}"
fi
test_pass "all ${#NAMES[@]} disposition tests pass" "{\"log_path\":\"${LOG_PATH}\"}"
