#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_mach_service_liveness"
PW_TEST_ID="pwrunner_survives_mach_service_launch"

# The BYOXPC host executable, addressed the way the generated LaunchAgent does.
PWRUNNER_BIN="${PWRUNNER_BIN:-${PW_APP_DIR}/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "launch" "launch PWRunner directly with --mach-service and assert it does not abort"

if [[ ! -x "${PWRUNNER_BIN}" ]]; then
  # Same shape as the built-app skip elsewhere: an unbuilt tree skips, not fails.
  skip_missing_pw_app "${PWRUNNER_BIN}"
  exit 0
fi

STDERR_LOG="${PW_TEST_ARTIFACTS}/pwrunner.stderr.log"
SVC="com.pw.test.liveness.$$"

# Launch the runner exactly the way a BYOXPC LaunchAgent does: the executable
# directly, with `--mach-service <name>`. We deliberately do NOT bootstrap it
# under launchd (it holds no MachServices receive right here), so it never
# services a connection in this suite. That is fine: a correctly built runner
# binds NSXPCListener(machServiceName:) and settles into its run loop, staying
# alive. A runner that (incorrectly) calls NSXPCListener.service() aborts
# immediately under xpc_main ("An XPC Service cannot be run directly.") — the
# exact regression that made `runner verify` return xpc_timeout.
"${PWRUNNER_BIN}" --mach-service "${SVC}" >/dev/null 2>"${STDERR_LOG}" &
RUNNER_PID=$!
trap 'kill "${RUNNER_PID}" 2>/dev/null || true' EXIT

# Give it a beat to either settle into the run loop (correct) or abort (broken).
sleep 0.5

# NOTE: kill -0 can't tell "alive" from "exited but not yet reaped" for our own
# child (an aborted child is a zombie until we wait for it, and kill -0 succeeds
# on zombies). Read the process STATE instead: a zombie shows "Z".
STATE="$(ps -o stat= -p "${RUNNER_PID}" 2>/dev/null | awk '{print $1}')"

# Clean up the process regardless of outcome.
kill "${RUNNER_PID}" 2>/dev/null || true
RC=0
wait "${RUNNER_PID}" 2>/dev/null || RC=$?

case "${STATE}" in
  "" | Z*)
    data_json="$(printf '{"exit_status":%s,"process_state":"%s","stderr_log":"%s"}' \
      "${RC}" "${STATE}" "${STDERR_LOG}")"
    test_fail "PWRunner did not stay alive under --mach-service (state='${STATE}', exit ${RC}); regressed to NSXPCListener.service()?" "${data_json}"
    ;;
  *)
    data_json="$(printf '{"process_state":"%s"}' "${STATE}")"
    test_pass "PWRunner stayed alive under --mach-service (bound a mach-service listener)" "${data_json}"
    ;;
esac
