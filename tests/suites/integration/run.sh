#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_begin "integration" "cli.integration"

export PW_INTEGRATION=1

LOG_PATH="${PW_TEST_ARTIFACTS}/cargo-test-integration.log"

test_step "cargo_test_integration" "cargo test --test cli_contract"
set +e
cargo test --manifest-path "${ROOT_DIR}/controller/Cargo.toml" --test cli_contract >"${LOG_PATH}" 2>&1
status=$?
set -e

if [[ ${status} -ne 0 ]]; then
  test_fail "cargo test --test cli_contract failed" "{\"log_path\":\"${LOG_PATH}\"}"
fi

test_pass "integration tests ok" "{\"log_path\":\"${LOG_PATH}\"}"
