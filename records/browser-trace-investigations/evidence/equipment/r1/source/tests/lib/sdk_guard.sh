#!/bin/bash
# Safe to source before Python or any developer-tool shim. Keep SDKROOT intact.
# An explicit argument lets make validate its variable before exporting recipes.
pw_sdk_guard() {
  local request="${1-${SDKROOT-}}" selected version
  [[ -n "$request" ]] || return 0
  if ! selected="$(/usr/bin/xcrun --sdk "$request" --show-sdk-path 2>/dev/null)" ||
     [[ ! -d "$selected" ]] ||
     ! version="$(/usr/bin/xcrun --sdk "$selected" --show-sdk-version 2>/dev/null)" ||
     [[ ! "$version" =~ ^[0-9]+(\.[0-9]+)*$ ]]; then
    printf 'ERROR: admission: SDKROOT=%s does not resolve to an SDK with a numeric version\n' "$request" >&2
    return 2
  fi
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  pw_sdk_guard "$@"
fi
