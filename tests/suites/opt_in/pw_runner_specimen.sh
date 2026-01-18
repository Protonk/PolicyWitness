#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec "${ROOT_DIR}/tests/suites/runner_debuggable/opt_in/pw_runner_specimen.sh"
