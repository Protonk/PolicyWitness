#!/usr/bin/env bash
set -euo pipefail
SUITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../runner_validator_failure" && pwd)"
exec bash "${SUITE_DIR}/case.sh" malformed witness_contract
