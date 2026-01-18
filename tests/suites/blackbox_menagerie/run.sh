#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="${PW_TEST_SUITE_OVERRIDE:-blackbox_menagerie}"

MANIFEST="${ROOT_DIR}/tests/fixtures/blackbox_menagerie/cases/core.json"
FIXTURES_ROOT="${ROOT_DIR}/tests/fixtures/blackbox_menagerie"
RUN_CASE="${ROOT_DIR}/tests/suites/blackbox_menagerie/run_case.py"
PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"

if [[ ! -f "${MANIFEST}" ]]; then
  echo "missing manifest: ${MANIFEST}" 1>&2
  exit 1
fi
if [[ ! -x "${RUN_CASE}" ]]; then
  echo "missing runner: ${RUN_CASE}" 1>&2
  exit 1
fi

case_list=$( /usr/bin/python3 - <<'PY'
import json
from pathlib import Path
manifest = Path("tests/fixtures/blackbox_menagerie/cases/core.json")
records = json.loads(manifest.read_text())
for case in records.get("cases") or []:
    case_id = case.get("case_id")
    desc = case.get("description") or "menagerie case"
    print(f"{case_id}\t{desc}")
PY
)

if [[ ! -x "${PW_BIN}" ]]; then
  while IFS=$'\t' read -r case_id desc; do
    PW_TEST_ID="${case_id}"
    test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
    test_step "run" "${desc}"
    skip_missing_pw_app "${PW_BIN}"
  done <<< "${case_list}"
  exit 0
fi

while IFS=$'\t' read -r case_id desc; do
  PW_TEST_ID="${case_id}"
  test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
  test_step "run" "${desc}"

  set +e
  OUTPUT=$("${RUN_CASE}" \
    --manifest "${MANIFEST}" \
    --case "${case_id}" \
    --artifacts "${PW_TEST_ARTIFACTS}" \
    --fixtures "${FIXTURES_ROOT}" \
    --pw-bin "${PW_BIN}" 2>&1)
  STATUS=$?
  set -e

  OUTPUT="${OUTPUT//$'\n'/ }"
  if [[ ${STATUS} -eq 0 ]]; then
    test_pass "${OUTPUT}" "{}"
  elif [[ ${STATUS} -eq 3 ]]; then
    test_skip "${OUTPUT}" "{}"
  else
    test_fail "${OUTPUT}" "{}"
  fi
done <<< "${case_list}"
