#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

# The BYOXPC remediation plan's selection controller tests, promoted from red.
# rust.unit runs the whole crate too; this case keeps them individually
# selectable by exact name (with --include-ignored, so the selector was the
# same while they carried #[ignore]) and classifies build, equipment and
# unrelated failures separately from their own assertions.
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
  test_fail "behavioral reds still open: ${RED} of ${#TESTS[@]} (${GREEN} promoted); they were promoted and must stay green" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${status}" -ne 0 ]]; then
  test_fail "cargo exited ${status} although every BYOXPC selection test passed" "{\"log_path\":\"${LOG_PATH}\"}"
fi
test_pass "all ${#TESTS[@]} BYOXPC selection tests pass; they remain selectable after removing #[ignore]" "{\"log_path\":\"${LOG_PATH}\"}"
