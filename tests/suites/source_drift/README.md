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
  (`Sources/PWRunnerCore`, `Sources/PWCWorkerShim`), so moving a file
  within a target is
  invisible here; only adding/removing a compiled file trips the diff.
- `runner/Tests/`, `runner/Clients/`, `runner/Services/`, and
  `runner/augments/` are managed separately and are not part of the
  source-set check.

The shared prediction-unavailable operation/filter set in `ProbeRunner.swift`
must agree with the user guide. Both Swift callers use that single set;
independent runner unit tests pin their exclusion behavior.
The checker also requires `planValidatorQueries` to branch on the shared set's
`contains` call and rejects host-local pair collections, literal operation/filter
entries and shadowing of the shared symbol. Comments, string examples and uses
outside the planner cannot satisfy the membership check. This is a mechanical
source convention, not a Swift semantic analysis; a deliberate refactor of the
condition requires reviewing the guard alongside the runtime unit tests.

The registry checks also compare catalog suite names with suite directories and
the coverage table, and require Baseline suites to have default catalog cases.
They also lock the `_test_overrides` key table in `runner/README.md` to the
stored properties of `PWRunnerTestOverrides`, since that table is the only
documented key list, and keep the shared first paragraph of the sandboxed-harness
note identical across `AGENTS.md`, `runner/README.md` and `tests/README.md`,
since that note is carried in three places on purpose.
Public-command controls separately verify selection and actual execution.

## Success criteria

- The check script exits 0 and prints a one-line summary of how many
  files each manifest carries.
- Any disagreement fails the suite with a per-file diff naming which
  manifests contain the file and which don't.

## Fixtures

- Source-set checks read live files. Limits controls create disposable checkouts
  containing the actual generator, documents and referenced source files.
- Planner controls run the actual checker in a disposable checkout with a
  three-pair mirror, an extra fourth pair, inferred literal entries, shadowing,
  and missing/comment-only/string-only membership checks. Formatting and
  commented/string examples remain accepted. Inputs and command receipts are
  retained, and the restored fixture must pass.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

- `<run>/suites/source_drift/runner_source_manifests_agree/artifacts/check.log`
- `<run>/suites/source_drift/runner_source_manifests_agree/artifacts/planner-controls/`
- `<run>/suites/source_drift/limits_documentation/artifacts/limits.log`
- `<run>/suites/source_drift/contract_versions/artifacts/contract.log`

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

The `contract_versions` case checks [`docs/contract.json`](../../../docs/contract.json)
against every generated copy in code and documents, exercises the real generator in
a disposable checkout with changed, stale, broken-marker and malformed inputs, and
proves a stale copy stops the build before signing. Compiled values are compared
elsewhere: `runner_abi_layout` (C), `runner_unit` (Swift) and the Rust unit tests.
See [`docs/CONTRACT.md`](../../../docs/CONTRACT.md).
