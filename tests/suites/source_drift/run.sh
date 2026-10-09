#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="source_drift"
PW_TEST_ID="runner_source_manifests_agree"

if test_selected "${PW_TEST_ID}"; then
  test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
  test_step "diff" "compare runner/ on-disk source set against meson.build"

  CHECK_PY="${ROOT_DIR}/tests/suites/source_drift/check.py"
  RUN_LOG="${PW_TEST_ARTIFACTS}/check.log"

  set +e
  /usr/bin/python3 "${CHECK_PY}" >"${RUN_LOG}" 2>&1
  RC=$?
  set -e

  if [[ "${RC}" -ne 0 ]]; then
    TAIL="$(tail -n 20 "${RUN_LOG}" | sed 's/"/\\"/g')"
    test_fail "manifests disagree: ${TAIL}" "{\"log\":\"${RUN_LOG}\"}"
  fi

  SUMMARY="$(tail -n 1 "${RUN_LOG}")"
  test_step "planner" "reject host exclusion mirrors and missing shared membership checks"
  if ! /usr/bin/python3 -B "${ROOT_DIR}/tests/suites/source_drift/check_planner.py" \
      "${PW_TEST_ARTIFACTS}/planner-controls" >"${PW_TEST_ARTIFACTS}/planner-controls.log" 2>&1; then
    test_fail "planner source controls failed" "{\"log\":\"${PW_TEST_ARTIFACTS}/planner-controls.log\"}"
  fi
  test_pass "${SUMMARY}" "{\"log\":\"${RUN_LOG}\"}"
fi

PW_TEST_ID="limits_documentation"
if test_selected "${PW_TEST_ID}"; then
  test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
  test_step limits "check inventory, the matrix table, copied questions, rules and guide, staging controls and documentation links"
  RUN_LOG="${PW_TEST_ARTIFACTS}/limits.log"
  if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/source_drift/limits.py" >"${RUN_LOG}" 2>&1; then
    test_fail "limits documentation controls failed" "{\"log\":\"${RUN_LOG}\"}"
  fi
  test_pass "limits, matrix table, questions and reading-rule copies agree; standalone guide, staging and rejection controls pass" "{\"log\":\"${RUN_LOG}\"}"
fi

PW_TEST_ID="contract_versions"
if test_selected "${PW_TEST_ID}"; then
  test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
  test_step contract "check generated contract copies, generator controls and manifest validation"
  RUN_LOG="${PW_TEST_ARTIFACTS}/contract.log"
  if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/source_drift/contract.py" >"${RUN_LOG}" 2>&1; then
    test_fail "contract version controls failed" "{\"log\":\"${RUN_LOG}\"}"
  fi
  test_pass "contract manifest and every generated copy agree; generator and build controls pass" "{\"log\":\"${RUN_LOG}\"}"
fi

PW_TEST_ID="architecture_documentation"
if test_selected "${PW_TEST_ID}"; then
  test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
  test_step architecture "check the architecture manifest against its dot, SVG stamp and document copies; citation, stale-copy and refusal controls"
  RUN_LOG="${PW_TEST_ARTIFACTS}/architecture.log"
  if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/source_drift/architecture.py" >"${RUN_LOG}" 2>&1; then
    test_fail "architecture documentation controls failed" "{\"log\":\"${RUN_LOG}\"}"
  fi
  test_pass "architecture manifest, dot files, SVG stamps and document regions agree; citation and stale-copy controls pass" "{\"log\":\"${RUN_LOG}\"}"
fi

PW_TEST_ID="build_documentation"
if test_selected "${PW_TEST_ID}"; then
  test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
  test_step rules "compare the build manifest with build.sh, meson.build, the Makefile, the inventories and the baseline"
  RUN_LOG="${PW_TEST_ARTIFACTS}/build-rules.log"
  if ! /usr/bin/python3 -B "${ROOT_DIR}/tests/suites/source_drift/build_rules.py" >"${RUN_LOG}" 2>&1; then
    test_fail "build documentation rules disagree" "{\"log\":\"${RUN_LOG}\"}"
  fi
  test_step build "check the build manifest against its dot, SVG stamp and document copies; citation, stale-copy, parser and mutation controls"
  RUN_LOG="${PW_TEST_ARTIFACTS}/build.log"
  if ! /usr/bin/python3 -B "${ROOT_DIR}/tests/suites/source_drift/build.py" >"${RUN_LOG}" 2>&1; then
    test_fail "build documentation controls failed" "{\"log\":\"${RUN_LOG}\"}"
  fi
  test_pass "build manifest, dot file, SVG stamp and document regions agree with the script; grounding rules, parser refusals and mutation controls pass" "{\"log\":\"${RUN_LOG}\"}"
fi

PW_TEST_ID="generator_contract"
if test_selected "${PW_TEST_ID}"; then
  test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
  test_step generators "check uniform generator contracts and mutation controls"
  RUN_LOG="${PW_TEST_ARTIFACTS}/generators.log"
  if ! /usr/bin/python3 -B "${ROOT_DIR}/tests/suites/source_drift/generators.py" >"${RUN_LOG}" 2>&1; then
    test_fail "generator contract controls failed" "{\"log\":\"${RUN_LOG}\"}"
  fi
  test_pass "generator contracts and mutation controls pass" "{\"log\":\"${RUN_LOG}\"}"
fi
