# runner_abi_layout

Layout-drift guard for the shared-memory ABI between the runner host
(Swift) and `pw-probe-runner` (C). Catches mis-numbered `PWShmLayout`
constants and shifted struct offsets that parser-only `source_drift`
cannot model.

## What it does

1. Compiles `printer.c` against
   `controller/tools/pw_probe_runner/pw_probe_runner_abi.h` at test
   time (via `xcrun clang`).
2. Runs the printer to harvest `sizeof`, `offsetof`, and `#define`
   values from the C side — these are ground truth, including any
   compiler-applied struct padding.
3. Parses the `PWShmLayout` enum out of `runner/Sources/PWRunnerCore/CWorker.swift`,
   resolving derived constants (e.g. `regionBytes = headerBytes +
   maxSteps * slotBytes + maxParams * paramBytes`).
4. For every printer line, derives the expected Swift constant name
   via a mechanical mapping and asserts the numeric values agree.
5. Bidirectional: a Swift `PWShmLayout` constant with no
   corresponding printer line is also a failure (it means the C side
   stops verifying it).

## When it fails

- Bumping `PW_SHM_SLOT_BYTES` in the C header without updating
  `PWShmLayout.slotBytes` (or vice versa).
- Adding a field to `pw_shm_slot_t` (which shifts every subsequent
  offset) without updating the matching Swift `slot*Offset` constants.
- Adding a `PWShmLayout` constant without emitting a corresponding
  printer line.

The failure report (under
`tests/out/suites/runner_abi_layout/c_swift_layout_agreement/artifacts/diff.json`)
names which keys disagree and the two values, so the fix is
mechanical.

## Naming convention

The driver's `swift_name_for()` mapping table is the authoritative
spec for printer-key → Swift-constant naming. Brief summary:

| printer key                                      | Swift constant            |
|--------------------------------------------------|---------------------------|
| `PW_PROBE_RUNNER_ABI_VERSION`                    | `abiVersion`              |
| `PW_SHM_HEADER_BYTES`                            | `headerBytes`             |
| `PW_SHM_SLOT_BYTES`                              | `slotBytes`               |
| `sizeof.pw_shm_slot_t`                           | `slotBytes` (cross-check) |
| `offsetof.pw_shm_header_t.exit_requested`        | `exitRequestedOffset`     |
| `offsetof.pw_shm_slot_t.errno_val`               | `slotErrnoValOffset`      |
| `offsetof.pw_shm_param_t.value`                  | `paramValueOffset`        |
| `region.slots_offset`                            | `slotsOffset`             |
| `region.params_offset`                           | `paramsOffset`            |

Adding a new printer key that doesn't fit the table raises a clear
error pointing at `swift_name_for()`. Adding a Swift constant
without a printer line raises a "missing_in_printer" error.

## Why this is separate from `source_drift`

`source_drift` parses Swift and C textually. It can verify enum
agreement (e.g., `PWAttemptKind.execSpawn = 8` matches
`PW_ATTEMPT_EXEC_SPAWN = 8`) because enum values are literal in
both sources. It cannot verify struct-field offsets: those depend
on compiler padding the parser doesn't model.

`runner_abi_layout` invokes the actual compiler. If clang lays out
the struct differently than the header's documented offsets imply,
`offsetof()` reports the real address. The two suites are
complementary; both belong in the default tier.

## Run

```
./tests/run.sh --suite runner_abi_layout
```

No app-bundle dependency — only requires the Xcode CommandLineTools
clang + macOS SDK. Fast (compiles ~50 LOC, prints ~40 lines, diffs
in Python).

## Artifacts

- `tests/out/suites/runner_abi_layout/c_swift_layout_agreement/artifacts/printer` — compiled printer binary
- `tests/out/suites/runner_abi_layout/c_swift_layout_agreement/artifacts/printer.out` — KEY=VALUE harvest
- `tests/out/suites/runner_abi_layout/c_swift_layout_agreement/artifacts/diff.json` — per-key comparison report
