#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract example_round_trip
test_require_pw

# This case holds no specimen. It runs the selected app directly, retains the
# raw stdout, stderr and exit status of every invocation, and submits the
# emitted bytes unchanged.
CHECKER="${ROOT_DIR}/tests/suites/witness_contract/check_example_round_trip.py"
CAPTURE="${PW_TEST_ARTIFACTS}/capture"
mkdir "${CAPTURE}"

invoke() {
  local prefix="$1"
  shift
  local status=0
  printf '%s\n' "${PW_BIN}" "$@" >"${prefix}.command"
  "${PW_BIN}" "$@" >"${prefix}.stdout" 2>"${prefix}.stderr" || status=$?
  printf '%s\n' "${status}" >"${prefix}.exit"
}

test_step emit "print the app's version and its example twice"
invoke "${CAPTURE}/version" --version
invoke "${CAPTURE}/example-1" example
invoke "${CAPTURE}/example-2" example

test_step prepare "gate the phased emission and independently check both derivatives"
if ! "${PW_PYTHON}" -B -S "${CHECKER}" prepare "${CAPTURE}" "${PW_APP_DIR}" \
    "${ROOT_DIR}/docs/contract/public.json" >"${PW_TEST_ARTIFACTS}/prepare.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/prepare.log" >&2 || true
  test_fail "the emitted document was not submitted (report: ${CAPTURE}/report.json)"
fi

test_step run "submit emitted, flat and actor forms with their own before/after samples"
for form in emitted flat actor; do
  directory="${CAPTURE}/${form}"
  input="${directory}/input.json"
  if [[ "${form}" == emitted ]]; then
    directory="${CAPTURE}"
    input="${CAPTURE}/example-1.stdout"
  fi
  test_run_logged "${PW_TEST_ARTIFACTS}/${form}-before.log" "target observation before ${form} failed" \
    "${PW_PYTHON}" -B -S "${CHECKER}" observe "${CAPTURE}" "${form}" before
  invoke "${directory}/run" run "${input}"
  test_run_logged "${PW_TEST_ARTIFACTS}/${form}-after.log" "target observation after ${form} failed" \
    "${PW_PYTHON}" -B -S "${CHECKER}" observe "${CAPTURE}" "${form}" after
done
for directory in "${CAPTURE}"/refusals/*/; do
  invoke "${directory}run" run "${directory}input.json"
done

test_step check "read the retained captures"
test_check_python "${PW_TEST_ARTIFACTS}/check.log" "example round trip failed (report: ${CAPTURE}/report.json)" \
  "${CHECKER}" evaluate "${CAPTURE}"
test_step named "submit each named emission on the example help card unchanged, with that name's own checker"
invoke "${CAPTURE}/help-example" help example
NAMES="$(awk '/^[^ ]/ && NF == 2 { print $2 }' "${CAPTURE}/help-example.stdout")"
[[ -n "${NAMES}" ]] || test_fail "the example help card heads no named specimen"
for name in ${NAMES}; do
  [[ "${name}" =~ ^[a-z0-9_-]+$ ]] || test_fail "unexpected example name on the help card: ${name}"
  NAMED="${CAPTURE}/${name}"
  NAMED_CHECK="${ROOT_DIR}/tests/suites/witness_contract/check_${name}_example.py"
  [[ -f "${NAMED_CHECK}" ]] || test_fail "the app publishes example ${name}, which has no round-trip checker"
  mkdir "${NAMED}"
  invoke "${NAMED}/emit" example "${name}"
  test_check_python "${NAMED}/prepare.log" "${name} emission or target prerequisite failed" \
    "${NAMED_CHECK}" prepare "${NAMED}"
  invoke "${NAMED}/run" run "${NAMED}/emit.stdout"
  test_check_python "${NAMED}/check.log" "${name} round trip failed" \
    "${NAMED_CHECK}" check "${NAMED}"
done
test_pass "every emission the help card heads and the ordinary derivatives meet their independent expectations; all six refusal inputs stop at their boundaries" "{}"
