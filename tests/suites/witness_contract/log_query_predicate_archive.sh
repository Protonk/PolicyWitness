#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"
test_selected log_query_predicate_archive || exit 0
test_begin "${PW_TEST_SUITE_OVERRIDE:-witness_contract}" log_query_predicate_archive
export PW_LOG_ARCHIVE_EVIDENCE="${PW_TEST_ARTIFACTS}/queries"
LOG_PATH="${PW_TEST_ARTIFACTS}/archive-query.log"
set +e
cargo test --manifest-path "${ROOT_DIR}/controller/Cargo.toml" --bin sandbox-log-observer \
  tests::log_query_predicate_archive -- --ignored --exact --nocapture >"${LOG_PATH}" 2>&1
status=$?
set -e
if [[ ${status} -ne 0 ]]; then
  test_fail "required OS archive query failed (missing data/access, supervision or selection error)" "{\"log_path\":\"${LOG_PATH}\"}"
fi
if ! grep -q 'test result: ok. 1 passed' "${LOG_PATH}"; then
  test_fail "archive query control did not execute exactly one passing test" "{\"log_path\":\"${LOG_PATH}\"}"
fi
test_pass "production OS query and parser match the independent archive manifest" "{\"log_path\":\"${LOG_PATH}\"}"
