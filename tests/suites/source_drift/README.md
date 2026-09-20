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

The registry checks also compare catalog suite names with suite directories and
the coverage table, and require Baseline suites to have default catalog cases.
Public-command controls separately verify selection and actual execution.

## Success criteria

- The check script exits 0 and prints a one-line summary of how many
  files each manifest carries.
- Any disagreement fails the suite with a per-file diff naming which
  manifests contain the file and which don't.

## Fixtures

- Source-set checks read live files. Limits controls create disposable checkouts
  containing the actual generator, documents and referenced source files.

## Artifacts

- `tests/out/suites/source_drift/runner_source_manifests_agree/artifacts/check.log`
- `tests/out/suites/source_drift/limits_documentation/artifacts/limits.log`

## Run

```
./tests/run.sh --suite source_drift
```

No build required. The `limits_documentation` case checks
[`docs/limits.json`](../../../docs/limits.json), generated tables, the user guide's
copied limits, and local documentation links. Controls exercise the real
generator command with stale, missing and altered content; preserve both source
files and an existing staged guide on rejection; and validate a staged guide
after removing its source checkout. Internal-anchor and companion-file checks
also reject defects introduced into the shared source, even when generation
would otherwise copy them consistently. A build control proves stale guide
content stops before signing or output creation. The suite does
not compare production constants: those checks belong to `runner_abi_layout`,
`runner_unit` and the Rust unit tests. See the maintenance instructions in
[`docs/LIMITS.md`](../../../docs/LIMITS.md).
