#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="smoke"
PW_TEST_ID="pw_lab_inside"

LAB_TOOL="${ROOT_DIR}/tools/pwlab/pw-lab"
PW_BIN="${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "inside_json" "pw-lab inside emits parseable JSON with stable keys"

OUT_DIR="${PW_TEST_ARTIFACTS}"

if [[ ! -x "${LAB_TOOL}" ]]; then
  test_fail "pw-lab tool is missing or not executable: ${LAB_TOOL}"
fi

if [[ ! -x "${PW_BIN}" ]]; then
  test_skip "missing PolicyWitness binary (build the app): ${PW_BIN}"
  exit 0
fi

mkdir -p "${OUT_DIR}"
INSIDE_JSON="${OUT_DIR}/inside.json"

"${LAB_TOOL}" inside --pw "${PW_BIN}" --profile minimal > "${INSIDE_JSON}"

/usr/bin/python3 - "${INSIDE_JSON}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))

assert isinstance(obj.get("inside"), bool)
assert "checked" in obj and isinstance(obj["checked"], list)
assert "trigger" in obj  # can be null
assert "service_names" in obj and isinstance(obj["service_names"], list)
PY

test_pass "pw-lab inside ok" "{}"
