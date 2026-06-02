# source_drift

Cross-checks the runner source manifest for drift between the on-disk
source tree and `build.sh`'s `XPC_RUNNER_*` references. The test-only
SwiftPM package (`runner/Package.swift`) follows convention and
auto-discovers the same files (no `sources:` arrays to drift), so the
SwiftPM source set equals on-disk by construction; the comparison that
can actually ship a broken `PWRunner.xpc` is build.sh vs the tree. A
file added under `Sources/PWRunnerCore/` but not wired into build.sh
(or vice versa) never reaches the production binary — with no other
signal.

## Invariants

- The two sources of truth (the on-disk `runner/Sources/` tree and
  build.sh's `XPC_RUNNER_*_FILE` / `XPC_RUNNER_*_SHIM` set) must agree
  on the compiled file set, compared as `runner/`-relative paths.
- Discovery is recursive under the target dirs
  (`Sources/PWRunnerCore`, `Sources/PWSandboxCheckShim`,
  `Sources/PWCWorkerShim`), so moving a file within a target is
  invisible here; only adding/removing a compiled file trips the diff.
- `runner/Tests/`, `runner/Clients/`, `runner/Services/`, and
  `runner/augments/` are managed separately and are not part of the
  source-set check.

## Success criteria

- The check script exits 0 and prints a one-line summary of how many
  files each manifest carries.
- Any disagreement fails the suite with a per-file diff naming which
  manifests contain the file and which don't.

## Fixtures

- None. The check parses live source on disk.

## Artifacts

- `tests/out/suites/source_drift/<test_id>/artifacts/check.log`

## Run

```
./tests/run.sh --suite source_drift
```

No build required — runs in <100ms.
