#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

# Non-default case: the BYOXPC remediation plan's #[ignore]d Rust reds.
# rust.unit runs the whole crate, so these carry #[ignore] with the plan's
# reason and run explicitly here, keeping the default battery green while --all
# and --suite opt_in still exercise them. Each is selected by its exact name with
# --include-ignored, so the same selector keeps running it after promotion.
# Red by design until Group 3 of docs/BYOXPC-REMEDIATION-PLAN.md lands.
test_begin "unit" "rust.byoxpc_reds"

LOG_PATH="${PW_TEST_ARTIFACTS}/cargo-test-ignored.log"
# Exact test name -> the assertion message that identifies its expected red.
declare -a TESTS=(
  "runner_manager::tests::false_valued_key_does_not_satisfy_a_requirement|a required key present with value false must be refused"
  "runner_select::tests::selection_refuses_a_false_valued_required_key|a required key present with value false must be refused"
)
NAMES=()
for entry in "${TESTS[@]}"; do NAMES+=("${entry%%|*}"); done

test_step "cargo_test_ignored" "run the exact BYOXPC selection tests, including ignored ones (false-valued keys)"
set +e
cargo test --manifest-path "${ROOT_DIR}/controller/Cargo.toml" --bin policy-witness -- --include-ignored --exact "${NAMES[@]}" >"${LOG_PATH}" 2>&1
status=$?
set -e

# Every named test must have run; classify each result.
RED=0; GREEN=0; UNEXPECTED=0
for entry in "${TESTS[@]}"; do
  name="${entry%%|*}"; message="${entry#*|}"
  if grep -Fxq "test ${name} ... ok" "${LOG_PATH}"; then
    GREEN=$((GREEN + 1))
  elif grep -Fxq "test ${name} ... FAILED" "${LOG_PATH}"; then
    if grep -Fq "${message}" "${LOG_PATH}"; then RED=$((RED + 1)); else UNEXPECTED=$((UNEXPECTED + 1)); fi
  else
    test_fail "BYOXPC selection test did not run: ${name} (exit ${status})" "{\"log_path\":\"${LOG_PATH}\"}"
  fi
done
if ! grep -Eq "^running ${#TESTS[@]} tests$" "${LOG_PATH}"; then
  test_fail "unexpected test selection; expected exactly ${#TESTS[@]} tests to run" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${UNEXPECTED}" -ne 0 ]]; then
  test_fail "BYOXPC selection test(s) failed without their expected assertion (${UNEXPECTED}); build, equipment or unrelated failure" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${RED}" -ne 0 ]]; then
  test_fail "behavioral reds still open: ${RED} of ${#TESTS[@]} (${GREEN} promoted); expected until Group 3 of the BYOXPC remediation plan lands" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${status}" -ne 0 ]]; then
  test_fail "cargo exited ${status} although every BYOXPC selection test passed" "{\"log_path\":\"${LOG_PATH}\"}"
fi
test_pass "all ${#TESTS[@]} BYOXPC selection tests pass; they remain selectable after removing #[ignore]" "{\"log_path\":\"${LOG_PATH}\"}"
