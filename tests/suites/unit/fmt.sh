#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_begin "unit" "rust.fmt"

LOG_PATH="${PW_TEST_ARTIFACTS}/cargo-fmt-check.log"

test_step "cargo_fmt_check" "cargo fmt -- --check (controller crate)"
set +e
cargo fmt --manifest-path "${ROOT_DIR}/controller/Cargo.toml" -- --check >"${LOG_PATH}" 2>&1
status=$?
set -e

if [[ ${status} -ne 0 ]]; then
  test_fail "cargo fmt --check reported differences; run cargo fmt in controller/" "{\"log_path\":\"${LOG_PATH}\"}"
fi

test_pass "rustfmt clean" "{\"log_path\":\"${LOG_PATH}\"}"
