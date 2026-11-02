#!/bin/sh
# The checkout-lock wrapper is the only execution entry point for this pilot.
set -eu
pilot_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
pilot_root=$(CDPATH= cd -- "$pilot_dir/../.." && pwd)
cd "$pilot_root"
exec "$pilot_root/tests/lib/python.sh" "$pilot_dir/driver.py" "$@"
