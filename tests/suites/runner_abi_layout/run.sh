#!/usr/bin/env bash
set -euo pipefail

# Layout-drift guard for the host↔worker shm ABI.
#
# Compiles a small C printer against the C ABI header at test time,
# runs it to harvest sizeof / offsetof / constant values, then parses
# the Swift PWShmLayout enum that mirrors those constants on the host
# side. Every printer line must map to a PWShmLayout constant with the
# identical numeric value; every PWShmLayout constant must have a
# corresponding printer line.
#
# This catches a class of bug that parser-only source_drift cannot:
# compiler-applied struct padding can shift a Swift-mirrored offset
# out of agreement with the C side without the textual constants in
# the header changing at all. The printer's offsetof() values are
# ground truth.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_abi_layout"
SUITE_DIR="${ROOT_DIR}/tests/suites/runner_abi_layout"
ABI_HEADER_DIR="${ROOT_DIR}/controller/tools/pw_probe_runner"
SWIFT_LAYOUT_FILE="${ROOT_DIR}/runner/CWorker.swift"

# ----------------------------------------------------------------------
# Case 1: c_swift_layout_agreement
# ----------------------------------------------------------------------
PW_TEST_ID="c_swift_layout_agreement"
test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "build" "compile printer against pw_probe_runner_abi.h"

require_clang || exit 0
require_macos_sdk || exit 0

PRINTER_BIN="${PW_TEST_ARTIFACTS}/printer"
PRINTER_OUT="${PW_TEST_ARTIFACTS}/printer.out"
PRINTER_ERR="${PW_TEST_ARTIFACTS}/printer.err"

if ! /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -O2 -std=c11 \
       -I "${ABI_HEADER_DIR}" \
       -o "${PRINTER_BIN}" \
       "${SUITE_DIR}/printer.c" 2>"${PRINTER_ERR}"; then
  test_fail "printer.c failed to compile against pw_probe_runner_abi.h" \
    "{\"compile_error_log\":\"${PRINTER_ERR}\"}"
fi

test_step "run" "harvest sizeof / offsetof from C-side printer"

if ! "${PRINTER_BIN}" >"${PRINTER_OUT}" 2>>"${PRINTER_ERR}"; then
  test_fail "printer execution failed" \
    "{\"stderr_log\":\"${PRINTER_ERR}\",\"stdout_log\":\"${PRINTER_OUT}\"}"
fi

test_step "compare" "diff printer output against Swift PWShmLayout"

DIFF_REPORT="${PW_TEST_ARTIFACTS}/diff.json"
if ! PW_PRINTER_OUT="${PRINTER_OUT}" \
     PW_SWIFT_LAYOUT_FILE="${SWIFT_LAYOUT_FILE}" \
     PW_DIFF_REPORT="${DIFF_REPORT}" \
     /usr/bin/python3 - <<'PY'
import json
import os
import re
import sys
from pathlib import Path

printer_out = Path(os.environ["PW_PRINTER_OUT"]).read_text(encoding="utf-8")
swift_text = Path(os.environ["PW_SWIFT_LAYOUT_FILE"]).read_text(encoding="utf-8")
diff_report = Path(os.environ["PW_DIFF_REPORT"])


def to_camel(snake: str) -> str:
    parts = snake.lower().split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def title_first(s: str) -> str:
    return (s[0].upper() + s[1:]) if s else s


# Map each printer key to the PWShmLayout constant name we expect to
# find in CWorker.swift. The mapping is mechanical and bidirectional —
# adding a new printer line that maps to a name not in this table will
# raise, forcing the table to stay current as the layout grows.
def swift_name_for(printer_key: str) -> str:
    if printer_key == "PW_PROBE_RUNNER_ABI_VERSION":
        return "abiVersion"
    if printer_key.startswith("PW_SHM_"):
        return to_camel(printer_key[len("PW_SHM_"):])
    if printer_key == "sizeof.pw_shm_header_t":
        return "headerBytes"
    if printer_key == "sizeof.pw_shm_slot_t":
        return "slotBytes"
    if printer_key == "sizeof.pw_shm_param_t":
        return "paramBytes"
    if printer_key.startswith("offsetof.pw_shm_header_t."):
        field = printer_key[len("offsetof.pw_shm_header_t."):]
        return to_camel(field) + "Offset"
    if printer_key.startswith("offsetof.pw_shm_slot_t."):
        field = printer_key[len("offsetof.pw_shm_slot_t."):]
        return "slot" + title_first(to_camel(field)) + "Offset"
    if printer_key.startswith("offsetof.pw_shm_param_t."):
        field = printer_key[len("offsetof.pw_shm_param_t."):]
        return "param" + title_first(to_camel(field)) + "Offset"
    if printer_key == "region.slots_offset":
        return "slotsOffset"
    if printer_key == "region.params_offset":
        return "paramsOffset"
    raise SystemExit(
        f"no Swift mapping defined for printer key {printer_key!r}; "
        "update swift_name_for() in tests/suites/runner_abi_layout/run.sh"
    )


printer_values: dict[str, int] = {}
for line in printer_out.splitlines():
    line = line.strip()
    if not line:
        continue
    if "=" not in line:
        raise SystemExit(f"malformed printer line (no '='): {line!r}")
    key, value = line.split("=", 1)
    try:
        printer_values[key] = int(value)
    except ValueError as e:
        raise SystemExit(f"non-integer printer value: {line!r} ({e})")

# Parse PWShmLayout constants out of CWorker.swift. The regex
# tolerates Int / UInt32 (and any future numeric type) since the
# value comparison is what's load-bearing, not the declared type.
layout_block_match = re.search(
    r"public enum PWShmLayout\s*\{(?P<body>.*?)\n\}",
    swift_text,
    re.DOTALL,
)
if not layout_block_match:
    raise SystemExit("could not locate `public enum PWShmLayout { ... }` in CWorker.swift")
layout_body = layout_block_match.group("body")

swift_values: dict[str, int] = {}
const_re = re.compile(
    r"public\s+static\s+let\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*[A-Za-z0-9_]+\s*=\s*(?P<value>[^\n]+)"
)
for m in const_re.finditer(layout_body):
    name = m.group("name")
    raw = m.group("value").strip()
    # Strip trailing comments and whitespace.
    raw = re.sub(r"//.*$", "", raw).strip()
    # Some constants are computed (e.g., regionBytes = headerBytes + ...).
    # Resolve them by evaluating against the already-collected values.
    if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
        swift_values[name] = int(raw)
        continue
    try:
        # Allow simple arithmetic over previously-declared constants.
        swift_values[name] = int(eval(raw, {"__builtins__": {}}, swift_values))
    except Exception as e:
        raise SystemExit(
            f"could not parse PWShmLayout constant {name!r} = {raw!r}: {e}"
        )

mismatches: list[dict] = []
missing_in_swift: list[str] = []
covered_swift: set[str] = set()

for c_key, c_val in sorted(printer_values.items()):
    swift_key = swift_name_for(c_key)
    covered_swift.add(swift_key)
    if swift_key not in swift_values:
        missing_in_swift.append(swift_key)
        continue
    if swift_values[swift_key] != c_val:
        mismatches.append({
            "c_key": c_key,
            "swift_key": swift_key,
            "c_value": c_val,
            "swift_value": swift_values[swift_key],
        })

# Catch the reverse direction: a Swift constant nobody on the C side
# verifies. Skip the two version constants whose printer keys live
# under different names — abiVersion is already covered via
# PW_PROBE_RUNNER_ABI_VERSION.
swift_only = sorted(set(swift_values.keys()) - covered_swift)

report = {
    "printer_value_count": len(printer_values),
    "swift_value_count": len(swift_values),
    "mismatches": mismatches,
    "missing_in_swift": missing_in_swift,
    "missing_in_printer": swift_only,
}
diff_report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

problems: list[str] = []
if mismatches:
    for m in mismatches:
        problems.append(
            f"value disagrees for {m['c_key']!r} → {m['swift_key']!r}: "
            f"C={m['c_value']} vs Swift={m['swift_value']}"
        )
if missing_in_swift:
    for k in missing_in_swift:
        problems.append(
            f"Swift PWShmLayout missing constant {k!r} (C side reports a value for it)"
        )
if swift_only:
    for k in swift_only:
        problems.append(
            f"Swift PWShmLayout has constant {k!r} with no corresponding C-side check "
            f"(extend printer.c to emit a sizeof / offsetof / macro mapping to {k!r})"
        )

if problems:
    sys.stderr.write("layout drift detected:\n")
    for p in problems:
        sys.stderr.write("  - " + p + "\n")
    sys.exit(1)

print(f"ok: {len(printer_values)} C↔Swift layout values agree")
PY
then
  test_fail "C↔Swift layout values disagree" "{\"diff_report\":\"${DIFF_REPORT}\"}"
fi

test_pass "C and Swift PWShmLayout agree on every macro / sizeof / offsetof" \
  "{\"diff_report\":\"${DIFF_REPORT}\"}"
