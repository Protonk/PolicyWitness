#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

CURRENT_STEP=""

test_begin "smoke" "inherit_child.q6_bookmark_ferry"

fail() {
  test_fail "${CURRENT_STEP:-q6 bookmark_ferry failed}"
}

trap fail ERR

step() {
  CURRENT_STEP="$1"
  test_step "$1" "${2:-$1}"
}

PW="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
OUT_DIR="${PW_TEST_ARTIFACTS}"

if [[ ! -x "${PW}" ]]; then
  test_fail "missing or non-executable PolicyWitness launcher at: ${PW}"
fi

mkdir -p "${OUT_DIR}"

step "bookmark_ferry_move" "inherit_child bookmark_ferry (move)"
MOVE_JSON="${OUT_DIR}/inherit-child-bookmark-move.json"
"${PW}" xpc run --profile bookmarks_app_scope inherit_child --scenario bookmark_ferry \
  --path-class tmp --target specimen_file --name pw_q6_bookmark.txt --create --bookmark-move \
  >"${MOVE_JSON}"

step "bookmark_ferry_invalid" "inherit_child bookmark_ferry (invalid payload)"
INVALID_JSON="${OUT_DIR}/inherit-child-bookmark-invalid.json"
"${PW}" xpc run --profile bookmarks_app_scope inherit_child --scenario bookmark_ferry \
  --path-class tmp --target specimen_file --name pw_q6_bookmark_bad.txt --create --bookmark-invalid \
  >"${INVALID_JSON}"

step "validate_witness" "validate bookmark resolve/start/access separation"
PY_STATUS=0
/usr/bin/python3 - "${MOVE_JSON}" "${INVALID_JSON}" "${OUT_DIR}/summary.json" <<'PY' || PY_STATUS=$?
import json
import sys
from pathlib import Path

move_path, invalid_path, summary_path = sys.argv[1:]

def fail(reason, summary):
    summary["status"] = "fail"
    summary["reason"] = reason
    Path(summary_path).write_text(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(1)

def load_json(path, summary, label):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        fail(f"{label}: stdout not JSON: {exc}", summary)
    if data.get("kind") != "probe_response":
        fail(f"{label}: unexpected kind {data.get('kind')!r}", summary)
    return data

def find_bookmark(data):
    witness = (data.get("data") or {}).get("witness") or {}
    cap_results = witness.get("capability_results")
    if not isinstance(cap_results, list):
        return None, "missing witness.capability_results"
    for cap in cap_results:
        if isinstance(cap, dict) and cap.get("cap_id") == "bookmark":
            return cap, None
    return None, "missing capability_results entry for bookmark"

def intish(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value.lstrip("-").isdigit():
            return int(value)
    return None

def boolish(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "false"):
            return lowered == "true"
    return None

summary = {"status": "pass", "reason": "ok"}

move_data = load_json(move_path, summary, "move")
invalid_data = load_json(invalid_path, summary, "invalid")

move_bookmark, move_err = find_bookmark(move_data)
if move_bookmark is None:
    fail(f"move: {move_err}", summary)

invalid_bookmark, invalid_err = find_bookmark(invalid_data)
if invalid_bookmark is None:
    fail(f"invalid: {invalid_err}", summary)

def check_bookmark(label, cap, require_error):
    bookmark = cap.get("bookmark")
    if not isinstance(bookmark, dict):
        fail(f"{label}: missing bookmark details", summary)
    child_acquire = cap.get("child_acquire")
    child_use = cap.get("child_use")
    if not isinstance(child_acquire, dict) or not isinstance(child_use, dict):
        fail(f"{label}: missing child acquire/use details", summary)
    missing = [k for k in ("resolve_rc", "start_accessing", "access_rc") if k not in bookmark]
    if missing:
        fail(f"{label}: missing bookmark fields {missing}", summary)
    resolve_rc = intish(bookmark.get("resolve_rc"))
    access_rc = intish(bookmark.get("access_rc"))
    start_accessing = boolish(bookmark.get("start_accessing"))

    if resolve_rc is None:
        fail(f"{label}: resolve_rc not int-like", summary)
    if access_rc is None:
        fail(f"{label}: access_rc not int-like", summary)
    if start_accessing is None:
        fail(f"{label}: start_accessing missing or not bool-like", summary)

    child_use_rc = intish((child_use or {}).get("rc"))
    if child_use_rc is None:
        fail(f"{label}: child_use.rc missing", summary)
    if child_use_rc != access_rc:
        fail(f"{label}: child_use.rc {child_use_rc} != bookmark.access_rc {access_rc}", summary)

    if require_error:
        if resolve_rc == 0:
            fail(f"{label}: expected resolve_rc != 0 for invalid bookmark", summary)
        if access_rc == 0:
            fail(f"{label}: expected access_rc != 0 when resolve fails", summary)
        if start_accessing is True:
            fail(f"{label}: start_accessing true despite resolve failure", summary)
        has_error = (
            bool(bookmark.get("resolve_error")) or
            bool(bookmark.get("resolve_error_domain")) or
            bookmark.get("resolve_error_code") is not None
        )
        if not has_error:
            fail(f"{label}: missing resolve error details", summary)

    return {
        "resolve_rc": resolve_rc,
        "start_accessing": start_accessing,
        "access_rc": access_rc,
        "resolve_error_domain": bookmark.get("resolve_error_domain"),
        "resolve_error_code": bookmark.get("resolve_error_code"),
    }

summary["move"] = {
    "result_ok": (move_data.get("result") or {}).get("ok"),
    "normalized_outcome": (move_data.get("result") or {}).get("normalized_outcome"),
}
summary["move"].update(check_bookmark("move", move_bookmark, require_error=False))

summary["invalid"] = {
    "result_ok": (invalid_data.get("result") or {}).get("ok"),
    "normalized_outcome": (invalid_data.get("result") or {}).get("normalized_outcome"),
}
summary["invalid"].update(check_bookmark("invalid", invalid_bookmark, require_error=True))

Path(summary_path).write_text(json.dumps(summary, indent=2, sort_keys=True))
PY

if [[ ${PY_STATUS} -ne 0 ]]; then
  test_fail "q6 bookmark_ferry validation failed (see ${OUT_DIR}/summary.json)"
fi

test_pass "q6 bookmark_ferry ok" "{}"
