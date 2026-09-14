#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SUITE_DIR="${ROOT_DIR}/tests/suites/runner_validator_failure"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin runner_validator_failure transcript_controls
test_step fixture "verify the checked-in validator transcripts directly"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" \
  "validator fixture controls failed" \
  "${SUITE_DIR}/check.py" fixture "${PW_TEST_ARTIFACTS}"
test_pass "validator fixture returns the specified partial transcript and drains all probes"

failures=0
for variant in eof malformed; do
  if ! bash "${SUITE_DIR}/case.sh" "${variant}"; then failures=1; fi
done
exit "${failures}"
