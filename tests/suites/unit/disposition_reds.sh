#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

# Non-default case: the disposition record plan's #[ignore]d Rust reds.
# rust.unit runs the whole crate, so these carry #[ignore] with the plan's
# reason and run explicitly here, keeping the default battery green while --all
# and --suite opt_in still exercise them. Each is selected by its exact name with
# --include-ignored, so the same selector keeps running it after promotion.
# Red by design until the controller change lands. See tests/OPT_IN_TESTS.md.
test_begin "unit" "rust.disposition_reds"

LOG_PATH="${PW_TEST_ARTIFACTS}/cargo-test-ignored.log"
PREFIX="run_flow::tests::"
# Exact test name -> the assertion message that identifies its expected red.
declare -a TESTS=(
  "conflicting_status_representation_is_not_silently_resolved|exit_code 0 beside term_signal 9 is an invalid status pair; an unqualified disposition (signaled) resolves it silently"
  "conflicting_status_reports_the_status_rule|B1: exit_code 0 beside term_signal 9 must be reported as a status conflict"
  "disposition_record_projects_witnessed_host_cleanup_cause|E1: the controller ignores the carried disposition record and reports a generic cause"
  "record_contradicting_its_basis_is_withheld|E1: an assembled claim that contradicts its basis must be withheld, not re-derived"
)
NAMES=()
for entry in "${TESTS[@]}"; do NAMES+=("${PREFIX}${entry%%|*}"); done

test_step "cargo_test_ignored" "run the exact disposition tests, including ignored ones (B1, E1)"
set +e
cargo test --manifest-path "${ROOT_DIR}/controller/Cargo.toml" --bin policy-witness -- --include-ignored --exact "${NAMES[@]}" >"${LOG_PATH}" 2>&1
status=$?
set -e

# Every named test must have run; classify each result.
RED=0; GREEN=0; UNEXPECTED=0
for entry in "${TESTS[@]}"; do
  name="${PREFIX}${entry%%|*}"; message="${entry#*|}"
  if grep -Fxq "test ${name} ... ok" "${LOG_PATH}"; then
    GREEN=$((GREEN + 1))
  elif grep -Fxq "test ${name} ... FAILED" "${LOG_PATH}"; then
    if grep -Fq "${message}" "${LOG_PATH}"; then RED=$((RED + 1)); else UNEXPECTED=$((UNEXPECTED + 1)); fi
  else
    test_fail "disposition test did not run: ${name} (exit ${status})" "{\"log_path\":\"${LOG_PATH}\"}"
  fi
done
if ! grep -Eq "^running ${#TESTS[@]} tests$" "${LOG_PATH}"; then
  test_fail "unexpected test selection; expected exactly ${#TESTS[@]} tests to run" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${UNEXPECTED}" -ne 0 ]]; then
  test_fail "disposition test(s) failed without their expected assertion (${UNEXPECTED}); build, equipment or unrelated failure" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${RED}" -ne 0 ]]; then
  test_fail "behavioral reds still open: ${RED} of ${#TESTS[@]} (${GREEN} promoted); expected until the controller change lands" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${status}" -ne 0 ]]; then
  test_fail "cargo exited ${status} although every disposition test passed" "{\"log_path\":\"${LOG_PATH}\"}"
fi
test_pass "all ${#TESTS[@]} disposition tests pass; they remain selectable after removing #[ignore]" "{\"log_path\":\"${LOG_PATH}\"}"
