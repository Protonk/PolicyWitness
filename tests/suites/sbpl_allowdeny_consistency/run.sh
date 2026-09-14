#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

exec bash "${ROOT_DIR}/tests/suites/sbpl_allowdeny_consistency/sbpl_allowdeny_v1.sh"
