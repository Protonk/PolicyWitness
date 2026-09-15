#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SUITE_DIR="${ROOT_DIR}/tests/suites/runner_validator_failure"
source "${ROOT_DIR}/tests/lib/case.sh"

if test_selected transcript_controls; then
test_begin runner_validator_failure transcript_controls
test_step fixture "verify the checked-in validator transcripts directly"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" \
  "validator fixture controls failed" \
  "${SUITE_DIR}/check.py" fixture "${PW_TEST_ARTIFACTS}"
test_pass "validator fixture returns the specified partial transcript and drains all probes"

fi

failures=0
for variant in eof malformed; do
  if [[ "$variant" == eof ]]; then id=validator_unavailable_reports_degraded; else id=validator_decode_failure_reports_degraded; fi
  test_selected "$id" || continue
  if ! bash "${SUITE_DIR}/case.sh" "${variant}"; then failures=1; fi
done
exit "${failures}"
