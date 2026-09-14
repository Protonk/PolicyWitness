#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

testlib_init

RUN_START_MS="$(now_ms)"
RUN_OUT_RAW="${PW_TEST_OUT_DIR}"
RUN_OUT="$(
  PW_TEST_ROOT="${ROOT_DIR}" \
  PW_TEST_OUT_RAW="${RUN_OUT_RAW}" \
  /usr/bin/python3 - <<'PY'
import os
import os.path

root = os.environ["PW_TEST_ROOT"]
raw = os.environ["PW_TEST_OUT_RAW"]

if os.path.isabs(raw):
    out = os.path.normpath(raw)
else:
    out = os.path.normpath(os.path.join(root, raw))

print(os.path.abspath(out))
PY
)"

if [[ -z "${RUN_OUT}" ]]; then
  echo "ERROR: PW_TEST_OUT_DIR resolved to an empty path" 1>&2
  exit 2
fi
if [[ "${RUN_OUT}" == "/" ]]; then
  echo "ERROR: refusing to use '/' as PW_TEST_OUT_DIR" 1>&2
  exit 2
fi

DEFAULT_OUT="${ROOT_DIR}/tests/out"
case "${RUN_OUT}" in
  "${DEFAULT_OUT}"| "${DEFAULT_OUT}/"*)
    ;;
  *)
    echo "ERROR: PW_TEST_OUT_DIR must be within ${DEFAULT_OUT} (got: ${RUN_OUT})" 1>&2
    exit 2
    ;;
esac

PW_TEST_OUT_DIR="${RUN_OUT}"
PW_TEST_EVENTS="${PW_TEST_OUT_DIR}/events.jsonl"
export PW_TEST_OUT_DIR PW_TEST_EVENTS

# This repo's test loops are designed to be agent-friendly: overwrite the prior run
# so external tooling can just read stable paths under tests/out/.
rm -rf "${RUN_OUT}"
mkdir -p "${RUN_OUT}"

suites=()
describe=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --suite)
      suites+=("${2:?missing suite name}")
      shift 2
      ;;
    --all)
      suites=()
      shift 1
      ;;
    --describe)
      describe=1
      shift 1
      ;;
    -h|--help)
      cat <<'EOF'
usage:
  tests/run.sh --all
  tests/run.sh --suite <preflight|source_drift|shell_helpers|dispatcher|unit|integration|runner_unit|runner_apply_isolation_v2|runner_apply_isolation_v3|runner_outcome_libsandbox_unavailable|runner_outcome_worker_spawn_failed|runner_outcome_runner_timeout|runner_outcome_bad_request|runner_ready_byte_resilience|runner_filter_iokit_registry_entry_class|runner_filter_iokit_user_client_class|runner_filter_sysctl_name|validator_batch_mode|runner_validator_failure|runner_abi_layout|runner_c_worker_harness|runner_use_c_worker|runner_mach_service_liveness|runner_live_worker_identity|runner_exec_dac|runner_exec_lifecycle|runner_exec_inheritance|runner_specimen_isolation|exec_fixture|run_capture|runner_byoxpc|smoke|blackbox_menagerie|blackbox_e2e|sbpl_allowdeny_consistency|witness_contract> [--suite <name> ...]
  tests/run.sh --describe [--all|--suite <name> ...]
EOF
      exit 0
      ;;
    *)
      echo "unknown argument: $1" 1>&2
      exit 2
      ;;
  esac
done

if [[ ${#suites[@]} -eq 0 ]]; then
  suites=(preflight source_drift shell_helpers dispatcher unit integration runner_unit runner_apply_isolation_v2 runner_apply_isolation_v3 runner_outcome_libsandbox_unavailable runner_outcome_worker_spawn_failed runner_outcome_runner_timeout runner_outcome_bad_request runner_ready_byte_resilience runner_filter_iokit_registry_entry_class runner_filter_iokit_user_client_class runner_filter_sysctl_name validator_batch_mode runner_validator_failure runner_abi_layout runner_c_worker_harness runner_use_c_worker runner_mach_service_liveness sbpl_allowdeny_consistency runner_live_worker_identity runner_exec_dac exec_fixture run_capture runner_exec_lifecycle runner_exec_inheritance runner_specimen_isolation)
fi

if [[ ${describe} -eq 1 ]]; then
  echo "==> [describe] suite map (tests/README.md)"
  if [[ -f "${ROOT_DIR}/tests/README.md" ]]; then
    cat "${ROOT_DIR}/tests/README.md"
  else
    echo "missing: ${ROOT_DIR}/tests/README.md" 1>&2
  fi
fi

# One dispatcher reconciles process exits with the evidence each suite emits.
# Its final decision supplies both run.json.ok and this command's exit status.
exec /usr/bin/python3 "${ROOT_DIR}/tests/lib/suite_run.py" \
  "${ROOT_DIR}" "${RUN_OUT}" "${PW_TEST_RUN_ID}" "${RUN_START_MS}" "${suites[@]}"
