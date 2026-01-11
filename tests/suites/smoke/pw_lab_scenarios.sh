#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="smoke"
PW_TEST_ID="pw_lab_scenarios"

OUT_DIR="${PW_TEST_OUT_DIR}/suites/${PW_TEST_SUITE}/${PW_TEST_ID}"
LAB_TOOL="${ROOT_DIR}/tools/pwlab/pw-lab"
SCENARIO_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_lab/scenario_basic.yaml"
RUN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_lab/run_basic"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "dry_run" "parse scenario fixture and emit plan"

if [[ ! -x "${LAB_TOOL}" ]]; then
  test_fail "pw-lab tool is missing or not executable: ${LAB_TOOL}"
fi

mkdir -p "${OUT_DIR}/dry_run"
"${LAB_TOOL}" run "${SCENARIO_FIXTURE}" --dry-run --outdir "${OUT_DIR}/dry_run"

if [[ ! -f "${OUT_DIR}/dry_run/plan.json" ]]; then
  test_fail "dry-run did not emit plan.json"
fi

test_step "inspect" "inspect fixture run summary"

CONF="$("${LAB_TOOL}" inspect --json "${RUN_FIXTURE}" | /usr/bin/python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("uncertainty", {}).get("confidence", ""))')"

if [[ "${CONF}" != "high" ]]; then
  test_fail "expected confidence=high (got: ${CONF})"
fi

test_step "diff" "diff identical fixture runs"

if ! "${LAB_TOOL}" diff "${RUN_FIXTURE}" "${RUN_FIXTURE}" >/dev/null; then
  test_fail "diff reported changes for identical runs"
fi

test_pass "pw-lab scenarios ok" "{}"
