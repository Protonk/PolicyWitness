#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

# Select the disposition regressions by exact name and require every result.
# These tests also run in rust.unit's full binary batch.
test_begin "unit" "rust.disposition_reds"

LOG_PATH="${PW_TEST_ARTIFACTS}/cargo-test-ignored.log"
declare -a NAMES=(
  "porcelain_admission::tests::typed_conflicting_status_preserves_the_native_pair_and_rule"
  "porcelain_admission::tests::typed_host_cleanup_cause_requires_all_independent_observations"
  "porcelain_admission::tests::typed_final_status_requires_its_native_witness_basis"
  "porcelain_admission::tests::typed_lifecycle_refuses_status_claim_without_owned_reap"
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
