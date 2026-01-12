#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="smoke"
PW_TEST_ID="pw_lab_tui_ungetch"

LAB_TOOL="${ROOT_DIR}/tools/pwlab/pw-lab"
RUN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_lab/run_basic"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run_tui_script" "run tui with ungetch script"

if [[ ! -t 0 || ! -t 1 ]]; then
  test_skip "tty required for curses (stdin/stdout not a tty)"
  exit 0
fi

if [[ ! -x "${LAB_TOOL}" ]]; then
  test_fail "pw-lab tool is missing or not executable: ${LAB_TOOL}"
fi

if [[ ! -d "${RUN_FIXTURE}" ]]; then
  test_fail "pw-lab fixture missing: ${RUN_FIXTURE}"
fi

STATE_JSON="${PW_TEST_ARTIFACTS}/tui_state.json"
TUI_STDOUT="${PW_TEST_ARTIFACTS}/tui.stdout.txt"
TUI_STDERR="${PW_TEST_ARTIFACTS}/tui.stderr.txt"

PW_LAB_TUI_SCRIPT="TAB,TAB,q" \
PW_LAB_TUI_TEST_OUT="${STATE_JSON}" \
TERM="${TERM:-xterm-256color}" \
  "${LAB_TOOL}" tui "${RUN_FIXTURE}" >"${TUI_STDOUT}" 2>"${TUI_STDERR}"

/usr/bin/python3 - "${STATE_JSON}" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if data.get("field_key") != "ok":
    raise SystemExit(f"expected field_key=ok (got {data.get('field_key')!r})")
if data.get("field_value") != "Y":
    raise SystemExit(f"expected field_value=Y (got {data.get('field_value')!r})")
PY

test_pass "pw-lab tui ungetch ok" "{}"
