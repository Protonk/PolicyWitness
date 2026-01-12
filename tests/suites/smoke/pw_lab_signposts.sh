#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="smoke"
PW_TEST_ID="pw_lab_signposts"

FIXTURE="${ROOT_DIR}/tests/fixtures/pw_lab/signpost_stream.jsonl"
LAB_TOOL="${ROOT_DIR}/tools/pwlab/pw-lab"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "validate" "validate lab signpost stream fixture"

OUT_DIR="${PW_TEST_ARTIFACTS}"

if [[ ! -x "${LAB_TOOL}" ]]; then
  test_fail "pw-lab tool is missing or not executable: ${LAB_TOOL}"
fi
if [[ ! -f "${FIXTURE}" ]]; then
  test_fail "missing fixture: ${FIXTURE}"
fi

if ! "${LAB_TOOL}" signposts validate --input "${FIXTURE}"; then
  test_fail "pw-lab signposts validate failed"
fi

test_step "timeline" "render timeline from signpost fixture"

mkdir -p "${OUT_DIR}"
TIMELINE_OUT="${OUT_DIR}/timeline.txt"
"${LAB_TOOL}" timeline --input "${FIXTURE}" > "${TIMELINE_OUT}"

if ! rg -q "pw.fence.waiting" "${TIMELINE_OUT}"; then
  test_fail "timeline missing pw.fence.waiting span"
fi
if ! rg -q "pw.probe.exec" "${TIMELINE_OUT}"; then
  test_fail "timeline missing pw.probe.exec span"
fi

test_pass "pw-lab signpost fixture ok" "{}"
