#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

cc -Wall -Wextra -O2 -std=c11 -o "$ROOT/sb_api_validator" "$ROOT/sb_api_validator.c"
codesign -s - -f --entitlements "$ROOT/debug.ent" "$ROOT/sb_api_validator"
