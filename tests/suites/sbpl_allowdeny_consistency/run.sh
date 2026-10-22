#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# A wrapper that starts its children without the case library resolves the
# pinned interpreter for them the way testlib.sh does for a case.
source "${ROOT_DIR}/tests/lib/python_start.sh"
pw_python_start || exit 2

exec bash "${ROOT_DIR}/tests/suites/sbpl_allowdeny_consistency/sbpl_allowdeny_v1.sh"
