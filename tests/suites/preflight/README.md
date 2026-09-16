# preflight

Read-only artifact inspection, with opt-in controls using real signatures.
Offline release controls also exercise the release procedure's decision points.

## Invariants

- Requires expected executables/resources, valid strict signatures for the app,
  service, and helpers, and matching hashes for every manifest entry. Required
  helper entries cannot silently disappear from the manifest.
- Never executes `policy-witness` or the runner.
- The shared `tests/lib/artifact.py` inspector also gates app-dependent selections
  in the public dispatcher. It never repairs a failed artifact.

## Success criteria

- `codesign.preflight` succeeds only when the inspector reports no errors.
- `signed_artifact_controls` copies the selected app to `/private/tmp`, checks a
  valid copy, removes a helper, damages a code page, and restores the helper.
  It then changes the copied runner's plist and re-signs inside-out with the
  matching Developer ID while retaining the old manifest. All signatures must
  verify, but inspection must reject the stale runner hash. No copy is launched;
  cleanup removes only the temporary directory and checks the source inventory.
- `release_controls` accepts a recognized Apple acceptance with extra fields and
  stops on agreement errors, unknown responses, pending/rejected/unknown status,
  wrong submission IDs, ambiguous duplicate fields, simulated timeouts, and changed input archives. Independent
  call receipts require exactly one submission and at most one bounded wait.
  Archive controls use real ZIPs and real layout/manifest/inventory checks, with
  simulated signature success and independent extraction/staple/execution tools.
  They cover missing helpers, stale evidence, missing staples, failed XPC runs,
  skipped cases, wrong runner provenance, mutation, and corrupt ZIPs, while a
  usable local source app remains untouched. Real signature semantics are covered
  separately by `signed_artifact_controls`.

## Fixtures

- `tests/fixtures/caller_auth/bundle.py`: copying, signing, and command receipts.
- `dispatcher/artifact_controls`: offline real-file mutations with independent
  simulated codesign; verifies gating, case receipts, and final inventories.
- `tests/fixtures/release/tools.py`: controlled external-tool boundary and receipts.

## Artifacts

- `tests/out/suites/preflight/codesign.preflight/artifacts/preflight.json`

Run:

```
./tests/run.sh --case preflight/codesign.preflight
./tests/run.sh --case preflight/signed_artifact_controls
./tests/run.sh --case preflight/release_controls
```
