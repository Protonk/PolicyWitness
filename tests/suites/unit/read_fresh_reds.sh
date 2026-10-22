#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

# The read_fresh denial-log association controls. Each requires a candidate
# for a submitted read_fresh attempt from a matching file-read-data event;
# without read_fresh eligibility the event stays unassociated. While red they
# carry #[ignore] and run here by exact name with --include-ignored, so the
# same selector keeps running them after promotion. A failure counts as the
# expected red only when that test's own failure output carries its registered
# assertion message. A missing test, a build or equipment error, or any other
# failure is reported separately.
test_begin "unit" "rust.read_fresh_reds"

LOG_PATH="${PW_TEST_ARTIFACTS}/cargo-test-ignored.log"
# Exact test name -> the assertion message that identifies its expected red.
declare -a TESTS=(
  "sandbox_log::tests::read_fresh_attempt_is_a_file_read_data_candidate|read_fresh red [matcher, completed attempt]: file-read-data event 0 on /attempt names no candidate"
  "sandbox_log::tests::read_fresh_candidate_needs_no_completed_attempt_evidence|read_fresh red [matcher, unpublished attempt]: file-read-data event 0 on /attempt names no candidate"
  "run_flow::tests::fresh_read_candidate_survives_probe_plan_assembly|read_fresh red [envelope, probe_plan]: the relevant event names no candidate for s"
  "run_flow::tests::fresh_read_candidate_survives_phased_assembly|read_fresh red [envelope, phases]: the relevant event names no candidate for s"
  "run_flow::tests::repeated_fresh_reads_share_one_ambiguous_event|read_fresh red [envelope, repeated phases]: the relevant event names neither s1 nor s2"
  "run_flow::tests::open_read_and_fresh_read_share_one_ambiguous_event|read_fresh red [envelope, mixed open_read]: the relevant event names o but not f"
)
NAMES=()
for entry in "${TESTS[@]}"; do NAMES+=("${entry%%|*}"); done

# One test's own failure output: from its stdout header to the next header or
# the closing failure list. A message elsewhere in the log cannot classify it.
failure_output() {
  awk -v header="---- $1 stdout ----" '
    $0 == header { found = 1; next }
    found && (/^---- .* stdout ----$/ || $0 == "failures:") { exit }
    found { print }
  ' "${LOG_PATH}"
}

test_step "cargo_test_ignored" "run the exact read_fresh association tests, including ignored ones"
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
    if failure_output "${name}" | grep -Fq "${message}"; then
      RED=$((RED + 1))
    else
      UNEXPECTED=$((UNEXPECTED + 1))
      test_log "failed without its registered assertion: ${name}"
    fi
  else
    test_fail "read_fresh association test did not run: ${name} (exit ${status})" "{\"log_path\":\"${LOG_PATH}\"}"
  fi
done
if ! grep -Eq "^running ${#TESTS[@]} tests$" "${LOG_PATH}"; then
  test_fail "unexpected test selection; expected exactly ${#TESTS[@]} tests to run" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${UNEXPECTED}" -ne 0 ]]; then
  test_fail "read_fresh association test(s) failed without their registered assertion (${UNEXPECTED}); build, equipment or unrelated failure" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${RED}" -ne 0 ]]; then
  test_fail "read_fresh association reds: ${RED} of ${#TESTS[@]} failed at their registered missing-candidate assertion (${GREEN} pass); expected only without read_fresh eligibility" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if [[ "${status}" -ne 0 ]]; then
  test_fail "cargo exited ${status} although every read_fresh association test passed" "{\"log_path\":\"${LOG_PATH}\"}"
fi
test_pass "all ${#TESTS[@]} read_fresh association tests pass; they remain selectable by exact name" "{\"log_path\":\"${LOG_PATH}\"}"
