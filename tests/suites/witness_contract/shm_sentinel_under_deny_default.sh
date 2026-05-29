#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="shm_sentinel_under_deny_default"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "C harness applies (deny default), writes applied sentinel to pre-touched shm, parent observes"

# This test depends on a tiny verification harness that proves the
# post-apply shared-memory sentinel path works under bare (deny default).
# The harness mmaps an anonymous shared region, pre-touches every page,
# applies a (deny default) policy, then writes a sentinel byte via a
# memory store (no syscall) and spins. The parent reads the byte.
#
# The harness lives at tests/suites/witness_contract/harness/sentinel_harness
# once R8's verification work lands. Until then, this test reports PHASE 0.
HARNESS="${ROOT_DIR}/tests/suites/witness_contract/harness/sentinel_harness"
if [[ ! -x "${HARNESS}" ]]; then
  test_fail "PHASE 0 — sentinel harness binary not present at ${HARNESS} (passes when R8 verification lands as part of Step 1)" "{}"
fi

RUN_LOG="${PW_TEST_ARTIFACTS}/run.log"
set +e
"${HARNESS}" >"${RUN_LOG}" 2>&1
RC=$?
set -e
if [[ "${RC}" -ne 0 ]]; then
  TAIL="$(tail -n 10 "${RUN_LOG}" | sed 's/"/\\"/g')"
  test_fail "sentinel harness exited rc=${RC}; tail: ${TAIL}" "{\"log\":\"${RUN_LOG}\"}"
fi

# Harness contract: prints `sentinel_observed=1` on success.
if ! grep -q 'sentinel_observed=1' "${RUN_LOG}"; then
  test_fail "harness did not report sentinel_observed=1" "{\"log\":\"${RUN_LOG}\"}"
fi

test_pass "shared-memory sentinel visible to parent under (deny default)" "{}"
