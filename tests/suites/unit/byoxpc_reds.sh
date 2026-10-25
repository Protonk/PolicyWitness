#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

# Select the BYOXPC requirement regressions by exact name and require every result.
# These tests also run in rust.unit's full binary batch.
test_begin "unit" "rust.byoxpc_reds"

LOG_PATH="${PW_TEST_ARTIFACTS}/cargo-test-ignored.log"
declare -a NAMES=(
  "runner_manager::tests::false_valued_key_does_not_satisfy_a_requirement"
  "runner_select::tests::selection_refuses_a_false_valued_required_key"
)

test_step "cargo_test_ignored" "run the exact BYOXPC selection tests for false-valued keys"
set +e
cargo test --manifest-path "${ROOT_DIR}/controller/Cargo.toml" --bin policy-witness -- --include-ignored --exact "${NAMES[@]}" >"${LOG_PATH}" 2>&1
status=$?
set -e

for name in "${NAMES[@]}"; do
  if grep -Fxq "test ${name} ... FAILED" "${LOG_PATH}"; then
    test_fail "BYOXPC selection test failed: ${name} (exit ${status})" "{\"log_path\":\"${LOG_PATH}\"}"
  elif ! grep -Fxq "test ${name} ... ok" "${LOG_PATH}"; then
    test_fail "BYOXPC selection test did not run or pass: ${name} (exit ${status})" "{\"log_path\":\"${LOG_PATH}\"}"
  fi
done
if ! grep -Eq "^running ${#NAMES[@]} tests$" "${LOG_PATH}"; then
  test_fail "unexpected test selection; expected exactly ${#NAMES[@]} tests to run" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${status}" -ne 0 ]]; then
  test_fail "cargo exited ${status} although every BYOXPC selection test passed" "{\"log_path\":\"${LOG_PATH}\"}"
fi
test_pass "all ${#NAMES[@]} BYOXPC selection tests pass" "{\"log_path\":\"${LOG_PATH}\"}"
