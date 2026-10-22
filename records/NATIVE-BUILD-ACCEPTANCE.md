# Native build and current versions acceptance

Implementation of [NATIVE-BUILD-PLAN.md](../NATIVE-BUILD-PLAN.md), assessed
on 2026-10-21 on macOS 26.7.1 (25G241). The changes were uncommitted on
`95b1017c1760665d34d47e7012a471fff0d444b5` when the runs below executed.

`build.sh` now refuses, before anything else runs, unless
`hw.optional.arm64` reads `1` and `sysctl.proc_translated` reads `0`. The
`meson.build` diagnostic ends at the host, the arm64 cross builds and the
Intel `cpu_relax` branches are gone, and the worker identity is regenerated.
The provenance reader, archive verification, publication and release cleanup
accept only the current record and output; the unread fixture generations
are removed. The sealed provenance notes are unchanged and the record stays at
schema 2.

## Acceptance evidence

All paths under `tests/out/` below are gitignored evidence available only in
this local checkout. Console transcripts, the source snapshot and the local
archive verification are attached under the default run's
[`acceptance/`](../tests/out/runs/native-default-20261021/acceptance/)
directory.

| Check | Result | Evidence |
|---|---|---|
| Fresh partial signed build, `BUILD_XPC=0 PW_FRESH_BUILD=1`, scratch `DIST_DIR` | Passed | [Transcript](../tests/out/runs/native-default-20261021/acceptance/build-partial-fresh.log) |
| Fresh full signed build, `make build PW_FRESH_BUILD=1` | Passed; eight thin arm64 executables | [Transcript](../tests/out/runs/native-default-20261021/acceptance/build-full-fresh.log) |
| `preflight/translated_build_refusal_controls` | Passed; 20 translated runs (both variants, both entry points) refused at admission; the dispatcher's `rosetta` probe read `1` | [Run](../tests/out/runs/native-translated-20261021/run.json) `20261022T010115Z_b0c0fd58` |
| `preflight/build_refusal_controls` | Passed; 87 controls and 16 bypass demonstrations, the three native builder mutations among them; no sleep | [Run](../tests/out/runs/native-refusals-20261021-2/run.json) `20261022T013118Z_54c759dd` |
| Full default battery against the fresh candidate | 198/198 passed; zero skips, unrun cases, harness errors or sleep; app valid before and unchanged after | [Run](../tests/out/runs/native-default-20261021/run.json) `20261022T022026Z_29c23174` |
| `witness_contract/order_barrier_mutations` | Passed; baseline accepted, both bypasses rejected | [Run](../tests/out/runs/native-order-barrier-20261021/run.json) `20261022T033448Z_dfc9b7b9` |
| Local `dist/archive/` verification with the updated reader | v0.3.2 verified; v0.2.7, v0.2.8 and v0.3.0 refused for a missing provenance object, v0.3.1 for its version 1 record; every archive unchanged | [Report](../tests/out/runs/native-default-20261021/acceptance/local-archive-verification.json) |

The default battery carries the offline checks the plan names: all eight
`source_drift` cases with the generators' checks, `build_provenance_controls`,
`dispatcher/artifact_controls`, `dispatcher/selection_controls` (the
Rosetta equipment control) and the release controls.

Commands ran outside any automation sandbox, with `SDKROOT`, `CPATH`,
`LIBRARY_PATH`, `MANPATH` and `PYTHONOPTIMIZE` unset:

```sh
env -u SDKROOT -u CPATH -u LIBRARY_PATH -u MANPATH -u PYTHONOPTIMIZE \
  BUILD_XPC=0 PW_FRESH_BUILD=1 DIST_DIR=<scratch> \
  IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' ./build.sh

env -u SDKROOT -u CPATH -u LIBRARY_PATH -u MANPATH -u PYTHONOPTIMIZE \
  make build PW_FRESH_BUILD=1 \
  IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'

env -u SDKROOT -u CPATH -u LIBRARY_PATH -u MANPATH -u PYTHONOPTIMIZE \
  PW_APP_DIR="$PWD/dist/PolicyWitness.app" \
  PW_TEST_OUT_DIR=tests/out/runs/<run> tests/run.sh [--case <id> ...]
```

## Source and artifact identity

The [source snapshot](../tests/out/runs/native-default-20261021/acceptance/source-before-default.json)
was taken immediately before the default battery: 838 entries, SHA-256
`6013f6074105a1684fc7ce588a5036a8d17cb61fdef9bde8da7d55656058366e` over the
canonical JSON map of paths, modes, contents and symlink targets. The
[post-battery snapshot](../tests/out/runs/native-default-20261021/acceptance/source-after-default.json)
differs only by this record's first draft. The order barrier run, the
evidence attachment and this record followed; nothing else changed.

The fresh full build preceded the translated, refusal, default and order
barrier runs. After it, only this record, the sleep record, BUILD.md prose
rewrapping and the refusal control module's docstring changed; none is a
build input, and the refusal and translated runs started after the docstring
edit. This applicability statement is a review judgment, separate from the
snapshot comparison.

The ZIP SHA-256 is
`dc412c1471c67af752db93e8bd7ce600d378b5f1e12039a467e475948617ac46`; the
worker identity is
`0da3a70ace265bd082e7a51e03ddc4cc2f84c366781d2d1b17a4d749fb891093`. The
[artifact hash list](../tests/out/runs/native-default-20261021/acceptance/artifacts.json)
also identifies the sealed manifest, the provenance record and each
executable. The record's `meson_machines` build machine is `darwin aarch64`
and rustc's host `aarch64-apple-darwin`; its two notes are the unchanged
strings.

The v0.3.2 verification ran `release_runs.verify_release` on
`dist/archive/v0.3.2` with the working-tree readers whose hashes the report
lists, unchanged since. It covers the original `release.json`
(`6c297867…`), ZIP (`e7e8dba6…`), guide, `SHA256SUMS`, archived provenance
(`bc22eb42…`) and the portable bundle's `manifest.json` (`c51ad3e4…`); the
report holds the full hashes and a before/after inventory of each archive.

## Uncredited and failed runs

These remain in `tests/out/runs/` and are not credited:

- `native-dev-1`, `native-dev-2` and `native-dev-3` were development runs.
  `native-dev-2` failed `source_drift/contract_versions`: its stand-in
  developer directory control runs `build.sh` under a profile allowing only
  bash, dirname and xcode-select to execute, so the guard's sysctl probes
  were denied and the builder refusal came first. The profile now also
  allows `/usr/sbin/sysctl`, and the control again reaches the direct Python
  refusal it tests.
- `native-refusals-20261021` (`20261022T010124Z_46fd4676`) failed after 78
  control records when the lid closed and the machine slept for 636 seconds;
  the build that ran first after wake could not reach the timestamp service.
  The dispatcher marked the failure as overlapping sleep.
  `records/SLEEP-TIMESTAMP-SIGNING-FAILURE.md` describes it. The credited run
  is the complete rerun above.
- The development shakedown of `native_builder_required` and `meson_target`
  through `build_refusals.py --only`
  ([transcript](../tests/out/runs/native-default-20261021/acceptance/refusals-dev.log))
  and a direct run of the translated control preceded the managed runs.

## Implementation notes

- The guard represents an empty read as `<empty>` and a failed probe as
  `<failed: status N>`. Under the sandbox profile the arm64 read exits zero
  and prints nothing, which `control_unconfirmed_machine` and the helper's
  startup gate observe. The `source_drift` pin also forbids executing
  `/usr/sbin/sysctl` and observes both probes reported as
  `<failed: status 126>` without `set -e` exiting. That is a launch failure;
  a nonzero exit from sysctl itself (an unknown OID on an Intel Mac) and an
  arm64 value of `0` still rest on the guard's code.
- Publication now verifies every archive, so one without portable test
  evidence is refused before any `git` or `gh` call, matching the removal of
  older archives without portable bundles from SIGNING.md.
- Release cleanup keeps acceptance output without its owner record and
  lifetime lock, with the reason `acceptance ownership has no lifetime lock`,
  and its retention entry stays.
- The dispatcher's `rosetta` probe record is attached to each invocation that
  required it, under `equipment` in `run.json`.
- No Rust source changed; Cargo tests were not run separately.
