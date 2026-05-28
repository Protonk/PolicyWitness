# source_drift

Cross-checks the runner source manifests for drift between the
on-disk file set, `build.sh`'s `XPC_RUNNER_*_FILE` references, and
`runner/Package.swift`'s `sources:` arrays. A file added to one
manifest but not the other never ships to the missing path — the
production binary loses the file, or the unit-test target does, with
no other signal.

## Invariants

- The three sources of truth (disk, build.sh, Package.swift) must
  agree on the runner/ root file set.
- Subdirectories under `runner/services/`, `runner/runner-client/`,
  `runner/Tests/`, and `runner/include/` are managed separately and
  are not part of the check.

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
