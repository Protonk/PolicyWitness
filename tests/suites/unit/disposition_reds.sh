#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

# Non-default case: the disposition record plan's #[ignore]d Rust reds.
# rust.unit runs the whole crate, so these carry #[ignore] with the plan's
# reason and run only here, keeping the default battery green while --all and
# --suite opt_in still exercise them. Red by design until the controller change
# lands; promotion removes the attribute. See tests/OPT_IN_TESTS.md.
test_begin "unit" "rust.disposition_reds"

LOG_PATH="${PW_TEST_ARTIFACTS}/cargo-test-ignored.log"
FILTER="conflicting_status_representation"

test_step "cargo_test_ignored" "cargo test --bins -- --ignored ${FILTER} (disposition plan B1)"
set +e
cargo test --manifest-path "${ROOT_DIR}/controller/Cargo.toml" --bins -- --ignored "${FILTER}" >"${LOG_PATH}" 2>&1
status=$?
set -e

if [[ ${status} -ne 0 ]]; then
  test_fail "ignored disposition reds still fail (expected until the record lands)" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if ! grep -Eq 'test result: ok\. [1-9][0-9]* passed' "${LOG_PATH}"; then
  test_fail "no ignored disposition test ran; check the filter ${FILTER}" "{\"log_path\":\"${LOG_PATH}\"}"
fi

test_pass "ignored disposition reds pass; promote them by removing #[ignore]" "{\"log_path\":\"${LOG_PATH}\"}"
