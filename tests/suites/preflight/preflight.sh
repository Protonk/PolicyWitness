#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

OUT_PATH=""
CURRENT_STEP=""

usage() {
  cat <<'EOF'
usage:
  tests/suites/preflight/preflight.sh [--out <path>]

notes:
  - requires complete bundle layout, valid signatures, and matching manifest hashes
  - does not execute any artifacts (codesign inspection only)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out)
      OUT_PATH="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" 1>&2
      usage
      exit 2
      ;;
  esac
done

test_begin "preflight" "codesign.preflight"

fail() {
  test_fail "${CURRENT_STEP:-preflight failed}"
}

trap fail ERR

step() {
  CURRENT_STEP="$1"
  test_step "$1" "${2:-$1}"
}

if [[ -z "${OUT_PATH}" ]]; then
  OUT_PATH="${PW_TEST_ARTIFACTS}/preflight.json"
fi

mkdir -p "$(dirname "${OUT_PATH}")"

APP_PATH="${PW_APP_DIR}"

step "artifact_inspection" "verify bundle components, signatures, and evidence hashes"
/usr/bin/python3 "${ROOT_DIR}/tests/lib/artifact.py" "${APP_PATH}" "${OUT_PATH}"

test_pass "bundle signatures and evidence hashes agree" "{\"out_path\":\"${OUT_PATH}\"}"
