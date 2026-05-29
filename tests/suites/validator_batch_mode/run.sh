#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="validator_batch_mode"
PW_TEST_ID="batch_ndjson_roundtrip"
SB_VALIDATOR="${PW_APP_DIR}/Contents/MacOS/sb_api_validator"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "smoke" "sb_api_validator --batch reads NDJSON probes from stdin and writes NDJSON verdicts to stdout"

if [[ ! -x "${SB_VALIDATOR}" ]]; then
  test_skip "missing ${SB_VALIDATOR} — run ./build.sh first" "{}"
  exit 0
fi

# Use the test's own PID as the target. Unsandboxed processes return
# allow for most operations, so all probes succeed except those that
# deliberately exercise the error paths (parse, bad_filter).
TARGET_PID="$$"

REQUEST_FILE="${PW_TEST_ARTIFACTS}/probes.ndjson"
RESPONSE_FILE="${PW_TEST_ARTIFACTS}/verdicts.ndjson"

# Mixed-filter request covering all four currently-supported batch
# filter shapes plus four error paths that must surface as
# parse_error/bad_filter verdicts (not abort the run). The two
# trailing error rows (e_trail, the 64KiB overlong line) regression
# the parser hardening from the post-Step-4 audit (findings 1 + 2).
{
  printf '%s\n' '{"step_id":"s1","operation":"file-read-data","filter_type":"PATH","filter_value":"/etc/hosts"}'
  printf '%s\n' '{"step_id":"s2","operation":"mach-lookup","filter_type":"GLOBAL_NAME","filter_value":"com.apple.cfprefsd.xpc.daemon"}'
  printf '%s\n' '{"step_id":"s3","operation":"network-outbound","filter_type":"NONE"}'
  printf '\n'
  printf '%s\n' '{"step_id":"e1","operation":"x","filter_type":"BAD","filter_value":"y"}'
  printf '%s\n' '{"step_id":"e2","operation":"x","filter_type":"PATH"}'
  printf '%s\n' '{not valid json}'
  # Trailing garbage after closing } — must be rejected as one
  # parse_error, not silently accepted (audit finding 1).
  printf '%s\n' '{"step_id":"e_trail","operation":"network-outbound","filter_type":"NONE"} garbage'
  # Overlong physical line (~80 KiB > 64 KiB buffer cap) — must
  # produce exactly one parse_error verdict and drain the rest
  # before reading the next line, not split the line into chunks
  # and emit multiple verdicts (audit finding 2).
  /usr/bin/python3 -c 'print("x" * 80000)'
  # A valid probe AFTER the overlong line proves the drain worked.
  printf '%s\n' '{"step_id":"after_overlong","operation":"network-outbound","filter_type":"NONE"}'
} >"${REQUEST_FILE}"

set +e
"${SB_VALIDATOR}" --batch "${TARGET_PID}" <"${REQUEST_FILE}" >"${RESPONSE_FILE}" 2>"${PW_TEST_ARTIFACTS}/validator.stderr"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  STDERR="$(head -3 "${PW_TEST_ARTIFACTS}/validator.stderr" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "sb_api_validator --batch exited rc=${RC}; stderr: ${STDERR}" "{\"stderr\":\"${PW_TEST_ARTIFACTS}/validator.stderr\"}"
fi

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
set +e
/usr/bin/python3 - "${RESPONSE_FILE}" >"${ASSERT_LOG}" 2>&1 <<'PY'
import json, sys
from pathlib import Path

lines = [ln for ln in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if ln.strip()]
# 8 probes (1 blank line skipped) → 8 verdicts:
#   s1 s2 s3 (allow) + e1 (bad_filter) + e2 (parse_error) +
#   not-valid-json (null step_id, parse_error) + e_trail (parse_error,
#   trailing garbage) + overlong (null step_id, parse_error) +
#   after_overlong (allow). That's 9 produced verdicts; check.
if len(lines) != 9:
    raise SystemExit(f"expected 9 verdict lines, got {len(lines)}: {lines!r}")

verdicts = [json.loads(ln) for ln in lines]

# Index by step_id where available; null step_ids for unrecoverable parse errors.
by_step = {}
nulls = []
for v in verdicts:
    sid = v.get("step_id")
    if sid is None:
        nulls.append(v)
    else:
        by_step[sid] = v

# Three happy-path probes: outcome=allow, rc=0, errno=0.
for sid, expected_filter_type in [("s1", "PATH"), ("s2", "GLOBAL_NAME"), ("s3", "NONE")]:
    v = by_step.get(sid)
    if v is None:
        raise SystemExit(f"missing verdict for step {sid}: {verdicts!r}")
    if v.get("outcome") != "allow":
        raise SystemExit(f"step {sid} expected outcome=allow, got {v}")
    if v.get("filter_type") != expected_filter_type:
        raise SystemExit(f"step {sid} filter_type mismatch: got {v.get('filter_type')!r}")
    if v.get("rc") != 0:
        raise SystemExit(f"step {sid} expected rc=0, got {v.get('rc')!r}")

# e1: bad_filter (filter_type=BAD with filter_value present)
e1 = by_step.get("e1")
if e1 is None or e1.get("outcome") != "bad_filter":
    raise SystemExit(f"step e1 expected outcome=bad_filter, got {e1!r}")

# e2: parse_error (PATH filter missing filter_value); step_id should
# survive into the verdict because parse_probe_line preserves
# partially-parsed fields on failure.
e2 = by_step.get("e2")
if e2 is None or e2.get("outcome") != "parse_error":
    raise SystemExit(f"step e2 expected outcome=parse_error, got {e2!r}")
if "filter_value" not in (e2.get("error") or ""):
    raise SystemExit(f"step e2 error message should mention filter_value, got {e2.get('error')!r}")

# e_trail: trailing garbage after closing } must be rejected, not
# silently accepted (audit finding 1). step_id was parsed before the
# trailing-content check fires, so it survives into the verdict.
e_trail = by_step.get("e_trail")
if e_trail is None or e_trail.get("outcome") != "parse_error":
    raise SystemExit(f"step e_trail expected outcome=parse_error for trailing garbage, got {e_trail!r}")
if "trailing" not in (e_trail.get("error") or ""):
    raise SystemExit(f"step e_trail error should mention trailing content, got {e_trail.get('error')!r}")

# after_overlong: the valid probe AFTER the 80 KiB overlong line must
# produce a verdict (audit finding 2 — the drain must work).
after = by_step.get("after_overlong")
if after is None or after.get("outcome") != "allow":
    raise SystemExit(f"step after_overlong expected outcome=allow (drain worked), got {after!r}")

# Null step_ids: the "not valid json" line + the overlong line each
# emit one parse_error verdict with null step_id. Exactly 2 expected.
if len(nulls) != 2:
    raise SystemExit(f"expected 2 null-step-id parse errors, got {len(nulls)}: {nulls!r}")
for v in nulls:
    if v.get("outcome") != "parse_error":
        raise SystemExit(f"null-step verdict expected outcome=parse_error, got {v!r}")
# One of them should specifically mention the 64 KiB cap so the
# overlong-line code path is exercised, not just any other null
# parse_error.
if not any("64 KiB" in (v.get("error") or "") for v in nulls):
    raise SystemExit(f"expected one null-step verdict to mention the 64 KiB cap (overlong-line path), got {nulls!r}")

# Schema/shape invariant: every verdict has kind+schema_version.
for v in verdicts:
    if v.get("kind") != "sb_api_validator_verdict":
        raise SystemExit(f"missing/bad kind in verdict: {v!r}")
    if v.get("schema_version") != 1:
        raise SystemExit(f"unexpected schema_version: {v!r}")

print("ok: 9 verdicts validated (4 allow + 1 bad_filter + 4 parse_error)")
PY
ASSERT_RC=$?
set -e

if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

SUMMARY="$(tail -1 "${ASSERT_LOG}")"
test_pass "${SUMMARY}" "{\"request\":\"${REQUEST_FILE}\",\"response\":\"${RESPONSE_FILE}\"}"
