#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"
test_begin unit rust.observer_admission
LOG_PATH="${PW_TEST_ARTIFACTS}/observer-admission.log"
NAME=sandbox_log::tests::observer_admission_precedes_all_body_interpretation
status=0
cargo test --manifest-path "${ROOT_DIR}/controller/Cargo.toml" --bin policy-witness -- --include-ignored --exact "$NAME" >"$LOG_PATH" 2>&1 || status=$?
if ! grep -Fxq 'running 1 test' "$LOG_PATH"; then test_fail "regression did not run" "{\"log_path\":\"$LOG_PATH\"}"; fi
if [[ $status -ne 0 ]]; then test_fail "observer admission regression failed" "{\"log_path\":\"$LOG_PATH\"}"; fi
test_pass "observer admission control passed" "{\"log_path\":\"$LOG_PATH\"}"
