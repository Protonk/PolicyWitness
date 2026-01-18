#!/usr/bin/env bash

testlib_root() {
  local lib_dir
  lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "${lib_dir}/../.." && pwd
}

now_ms() {
  /usr/bin/python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
}

gen_run_id() {
  local stamp
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  local suffix
  suffix="$(/usr/bin/python3 - <<'PY'
import uuid
print(uuid.uuid4().hex[:8])
PY
)"
  echo "${stamp}_${suffix}"
}

testlib_init() {
  local root
  root="$(testlib_root)"

  if [[ -z "${PW_TEST_RUN_ID:-}" ]]; then
    PW_TEST_RUN_ID="$(gen_run_id)"
    export PW_TEST_RUN_ID
  fi
  if [[ -z "${PW_TEST_OUT_DIR:-}" ]]; then
    PW_TEST_OUT_DIR="${root}/tests/out"
    export PW_TEST_OUT_DIR
  fi
  if [[ -z "${PW_TEST_EVENTS:-}" ]]; then
    PW_TEST_EVENTS="${PW_TEST_OUT_DIR}/events.jsonl"
    export PW_TEST_EVENTS
  fi

  mkdir -p "${PW_TEST_OUT_DIR}/suites"
}

write_json_line() {
  local line="$1"
  local path="$2"
  mkdir -p "$(dirname "${path}")"
  printf '%s\n' "${line}" >> "${path}"
}

emit_event() {
  local status="$1"
  local step="$2"
  local message="$3"
  local data_json="${4:-}"
  local duration_ms="${5:-}"

  local ts_ms
  ts_ms="$(now_ms)"

  PW_EVENT_STATUS="${status}" \
  PW_EVENT_STEP="${step}" \
  PW_EVENT_MESSAGE="${message}" \
  PW_EVENT_DATA="${data_json}" \
  PW_EVENT_DURATION_MS="${duration_ms}" \
  PW_EVENT_TS_MS="${ts_ms}" \
  /usr/bin/python3 - <<'PY'
import json
import os

def maybe_int(value):
    try:
        return int(value)
    except Exception:
        return None

data_raw = os.environ.get("PW_EVENT_DATA", "")
if data_raw:
    try:
        data = json.loads(data_raw)
    except Exception:
        data = {"raw": data_raw}
else:
    data = None

event = {
    "schema_version": 1,
    "kind": "test_event",
    "run_id": os.environ.get("PW_TEST_RUN_ID", ""),
    "suite": os.environ.get("PW_TEST_SUITE", ""),
    "test_id": os.environ.get("PW_TEST_ID", ""),
    "step": os.environ.get("PW_EVENT_STEP", ""),
    "status": os.environ.get("PW_EVENT_STATUS", ""),
    "ts_unix_ms": maybe_int(os.environ.get("PW_EVENT_TS_MS")),
    "duration_ms": maybe_int(os.environ.get("PW_EVENT_DURATION_MS")),
    "message": os.environ.get("PW_EVENT_MESSAGE", ""),
    "data": data,
}

print(json.dumps(event, sort_keys=True))
PY
}

test_log() {
  local message="$1"
  local suite="${PW_TEST_SUITE:-unknown}"
  local test_id="${PW_TEST_ID:-unknown}"
  if [[ -n "${PW_TEST_QUIET:-}" ]]; then
    return 0
  fi
  echo "==> [${suite}/${test_id}] ${message}"
}

test_log_force() {
  local message="$1"
  local suite="${PW_TEST_SUITE:-unknown}"
  local test_id="${PW_TEST_ID:-unknown}"
  echo "==> [${suite}/${test_id}] ${message}"
}

test_begin() {
  local suite="$1"
  local test_id="$2"

  testlib_init

  PW_TEST_SUITE="${suite}"
  PW_TEST_ID="${test_id}"
  PW_TEST_START_MS="$(now_ms)"
  PW_TEST_DIR="${PW_TEST_OUT_DIR}/suites/${suite}/${test_id}"
  PW_TEST_EVENTS_LOCAL="${PW_TEST_DIR}/events.jsonl"
  PW_TEST_REPORT="${PW_TEST_DIR}/report.json"
  PW_TEST_ARTIFACTS="${PW_TEST_DIR}/artifacts"

  export PW_TEST_SUITE PW_TEST_ID PW_TEST_START_MS
  export PW_TEST_DIR PW_TEST_EVENTS_LOCAL PW_TEST_REPORT PW_TEST_ARTIFACTS

  mkdir -p "${PW_TEST_ARTIFACTS}"

  test_log "start"
  local event_line
  event_line="$(emit_event "start" "test_start" "start")"
  write_json_line "${event_line}" "${PW_TEST_EVENTS}"
  write_json_line "${event_line}" "${PW_TEST_EVENTS_LOCAL}"
}

test_step() {
  local step="$1"
  local message="${2:-$1}"

  PW_TEST_CURRENT_STEP="${step}"
  export PW_TEST_CURRENT_STEP

  test_log "${message}"
  local event_line
  event_line="$(emit_event "info" "${step}" "${message}")"
  write_json_line "${event_line}" "${PW_TEST_EVENTS}"
  write_json_line "${event_line}" "${PW_TEST_EVENTS_LOCAL}"
}

write_report() {
  local status="$1"
  local message="$2"
  local duration_ms="$3"

  PW_REPORT_STATUS="${status}" \
  PW_REPORT_MESSAGE="${message}" \
  PW_REPORT_DURATION_MS="${duration_ms}" \
  /usr/bin/python3 - <<'PY'
import json
import os

def maybe_int(value):
    try:
        return int(value)
    except Exception:
        return None

report = {
    "schema_version": 1,
    "suite": os.environ.get("PW_TEST_SUITE", ""),
    "test_id": os.environ.get("PW_TEST_ID", ""),
    "status": os.environ.get("PW_REPORT_STATUS", ""),
    "message": os.environ.get("PW_REPORT_MESSAGE", ""),
    "duration_ms": maybe_int(os.environ.get("PW_REPORT_DURATION_MS")),
    "artifacts_dir": os.environ.get("PW_TEST_ARTIFACTS", ""),
    "notes": [],
}

path = os.environ.get("PW_TEST_REPORT", "")
if not path:
    raise SystemExit("missing PW_TEST_REPORT path")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2, sort_keys=True)
PY
}

test_pass() {
  local message="${1:-ok}"
  local data_json="${2:-}"
  local end_ms
  end_ms="$(now_ms)"
  local duration_ms=$((end_ms - ${PW_TEST_START_MS:-end_ms}))

  local event_line
  event_line="$(emit_event "pass" "test_end" "${message}" "${data_json}" "${duration_ms}")"
  write_json_line "${event_line}" "${PW_TEST_EVENTS}"
  write_json_line "${event_line}" "${PW_TEST_EVENTS_LOCAL}"
  write_report "pass" "${message}" "${duration_ms}"
  test_log "pass: ${message}"
}

test_pass_note() {
  local message="${1:-ok}"
  local data_json="${2:-}"
  local end_ms
  end_ms="$(now_ms)"
  local duration_ms=$((end_ms - ${PW_TEST_START_MS:-end_ms}))

  local event_line
  event_line="$(emit_event "pass" "test_end" "${message}" "${data_json}" "${duration_ms}")"
  write_json_line "${event_line}" "${PW_TEST_EVENTS}"
  write_json_line "${event_line}" "${PW_TEST_EVENTS_LOCAL}"
  write_report "pass" "${message}" "${duration_ms}"
  test_log_force "${message}"
}

test_fail() {
  local message="${1:-failed}"
  local data_json="${2:-}"
  local end_ms
  end_ms="$(now_ms)"
  local duration_ms=$((end_ms - ${PW_TEST_START_MS:-end_ms}))

  local event_line
  event_line="$(emit_event "fail" "test_end" "${message}" "${data_json}" "${duration_ms}")"
  if [[ -n "${PW_TEST_EVENTS:-}" ]]; then
    write_json_line "${event_line}" "${PW_TEST_EVENTS}"
  fi
  if [[ -n "${PW_TEST_EVENTS_LOCAL:-}" ]]; then
    write_json_line "${event_line}" "${PW_TEST_EVENTS_LOCAL}"
  fi
  write_report "fail" "${message}" "${duration_ms}"
  echo "FAIL: [${PW_TEST_SUITE:-unknown}/${PW_TEST_ID:-unknown}] ${message}" 1>&2
  exit 1
}

test_skip() {
  local message="${1:-skipped}"
  local data_json="${2:-}"
  local end_ms
  end_ms="$(now_ms)"
  local duration_ms=$((end_ms - ${PW_TEST_START_MS:-end_ms}))

  local event_line
  event_line="$(emit_event "skip" "test_end" "${message}" "${data_json}" "${duration_ms}")"
  write_json_line "${event_line}" "${PW_TEST_EVENTS}"
  write_json_line "${event_line}" "${PW_TEST_EVENTS_LOCAL}"
  write_report "skip" "${message}" "${duration_ms}"
  test_log "skip: ${message}"
}

skip_missing_pw_app() {
  local pw_bin="$1"
  test_skip "PolicyWitness.app is missing or not built at ${pw_bin}"
}

require_pw_app() {
  local pw_bin="$1"
  if [[ ! -x "${pw_bin}" ]]; then
    skip_missing_pw_app "${pw_bin}"
    return 1
  fi
  return 0
}

skip_missing_runner_bundle() {
  local bundle_path="$1"
  test_skip "runner bundle missing at ${bundle_path}"
}

require_runner_bundle() {
  local bundle_path="$1"
  if [[ ! -d "${bundle_path}" ]]; then
    skip_missing_runner_bundle "${bundle_path}"
    return 1
  fi
  return 0
}

skip_missing_clang() {
  test_skip "clang not available (install Xcode Command Line Tools)"
}

require_clang() {
  local clang_path
  clang_path="$(/usr/bin/xcrun --sdk macosx --find clang 2>/dev/null || true)"
  if [[ -z "${clang_path}" || ! -x "${clang_path}" ]]; then
    skip_missing_clang
    return 1
  fi
  echo "${clang_path}"
}

skip_missing_macos_sdk() {
  test_skip "macOS SDK not available (install Xcode Command Line Tools)"
}

require_macos_sdk() {
  local sdkroot
  sdkroot="$(/usr/bin/xcrun --sdk macosx --show-sdk-path 2>/dev/null || true)"
  if [[ -z "${sdkroot}" || ! -d "${sdkroot}" ]]; then
    skip_missing_macos_sdk
    return 1
  fi
  echo "${sdkroot}"
}

skip_runner_install_non_gui() {
  local data_json="${1:-}"
  test_skip "runner install blocked (non-GUI session); run from a logged-in Terminal" "${data_json}"
}

skip_runner_install_failed() {
  local data_json="${1:-}"
  test_skip "runner install failed (see artifacts)" "${data_json}"
}

skip_sandbox_restriction() {
  local data_json="${1:-}"
  test_skip "runner unavailable due to sandbox restriction (see artifacts)" "${data_json}"
}

skip_sandbox_log_observer_unavailable() {
  local data_json="${1:-}"
  test_skip "sandbox-log-observer unavailable on this host (see artifacts)" "${data_json}"
}

has_gui_launchd_domain() {
  local uid
  uid="$(/usr/bin/id -u 2>/dev/null || true)"
  if [[ -z "${uid}" ]]; then
    return 1
  fi
  /bin/launchctl print "gui/${uid}" >/dev/null 2>&1
}

cleanup_runner_service() {
  local pw_bin="$1"
  local service_name="$2"
  local scope="${3:-user}"

  if [[ -z "${service_name}" ]]; then
    return 0
  fi

  if [[ "${scope}" == "system" ]]; then
    /bin/launchctl bootout "system/${service_name}" >/dev/null 2>&1 || true
    if [[ -n "${pw_bin}" && -x "${pw_bin}" ]]; then
      "${pw_bin}" runner remove --service-name "${service_name}" --skip-bootout >/dev/null 2>&1 || true
    fi
    rm -f "/Library/LaunchDaemons/${service_name}.plist" >/dev/null 2>&1 || true
  else
    /bin/launchctl bootout "gui/$(/usr/bin/id -u)/${service_name}" >/dev/null 2>&1 || true
    if [[ -n "${pw_bin}" && -x "${pw_bin}" ]]; then
      "${pw_bin}" runner remove --service-name "${service_name}" --skip-bootout >/dev/null 2>&1 || true
    fi
    rm -f "${HOME}/Library/LaunchAgents/${service_name}.plist" >/dev/null 2>&1 || true
  fi
}

render_specimen_with_runner() {
  local input_path="$1"
  local output_path="$2"
  local mode="${PW_TEST_RUNNER_MODE:-}"
  local service="${PW_TEST_RUNNER_SERVICE:-}"

  if [[ -z "${mode}" && -z "${service}" ]]; then
    if [[ "${input_path}" != "${output_path}" ]]; then
      mkdir -p "$(dirname "${output_path}")"
      cp "${input_path}" "${output_path}"
    fi
    return 0
  fi

  mkdir -p "$(dirname "${output_path}")"
  /usr/bin/python3 - "${input_path}" "${output_path}" "${mode}" "${service}" <<'PY'
import json
import sys
from pathlib import Path

input_path, output_path, mode, service = sys.argv[1:5]
data = json.loads(Path(input_path).read_text(encoding="utf-8"))

runner = data.get("runner") or {}
if mode:
    runner["mode"] = mode
if service:
    runner["service"] = service
if runner:
    data["runner"] = runner

Path(output_path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

assert_runner_kind() {
  local run_json="$1"
  local expected="${PW_TEST_RUNNER_EXPECT_KIND:-}"

  if [[ -z "${expected}" ]]; then
    return 0
  fi

  /usr/bin/python3 - "${run_json}" "${expected}" <<'PY'
import json
import sys
from pathlib import Path

run_path, expected = sys.argv[1:3]
env = json.loads(Path(run_path).read_text(encoding="utf-8"))
kind = (env.get("data", {}) or {}).get("runner_provenance", {}).get("runner_kind")
if kind != expected:
    print(f"expected runner_kind={expected!r} (got {kind!r})")
    raise SystemExit(1)
PY
}
