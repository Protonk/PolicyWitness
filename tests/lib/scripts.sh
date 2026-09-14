#!/usr/bin/env bash
# Run each child in its own Bash process. The caller owns selection, phase
# boundaries, environment, and cleanup; children own their case reports.
test_run_scripts() {
  if [[ $# -eq 0 ]]; then
    echo "test_run_scripts: no child scripts supplied" >&2
    return 1
  fi
  local script failures=0
  for script in "$@"; do
    if bash "${script}"; then
      :
    else
      failures=1
    fi
  done
  return "${failures}"
}
