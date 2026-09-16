# preflight

Read-only artifact inspection, with opt-in controls using real signatures.

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

## Fixtures

- `tests/fixtures/caller_auth/bundle.py`: copying, signing, and command receipts.
- `dispatcher/artifact_controls`: offline real-file mutations with independent
  simulated codesign; verifies gating, case receipts, and final inventories.

## Artifacts

- `tests/out/suites/preflight/codesign.preflight/artifacts/preflight.json`

Run:

```
./tests/run.sh --case preflight/codesign.preflight
./tests/run.sh --case preflight/signed_artifact_controls
```
