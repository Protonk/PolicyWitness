# smoke

Quick end-to-end checks against a built app bundle. These scripts are shared
and invoked by the BYOXPC runner suite.

## Invariants

- Runs the CLI against small fixtures using the runner selected by the suite.
- `runner_caller_auth` first exercises the selected, unmodified app and inspects
  its signing arrangement, then uses its real client in disposable, signed app
  copies under `/private/tmp`. A same-team client with a disallowed identifier
  and an ad-hoc client retain identical bytes
  across their restricted/relaxed pairs. Adding the identifier to the allowlist,
  or disabling caller authentication for the ad-hoc control, must enable the
  request and its independently observed file write. An unchanged authorized
  client must also reach each restricted service after the rejected request.

## Success criteria

- Specimen smoke scripts exit 0 and produce `result.ok=true`.
- Caller-auth success requires both positive file effects and bounded negative
  responses with marker bytes preserved through fixture process cleanup.
  Missing-service lookup failures and timeouts are equipment failures, not
  authorization evidence. Actual successful
  relaxed-policy runs must fail the rejection checker with both completion and
  file-effect diagnostics; a real missing-service run must fail it as equipment.
- Fixture signatures are applied inside-out and verified, retain the production
  entitlements and hardened runtime, and have independently inspected team/identifier metadata.
  The selected app's file hashes, modes, and symlink targets must remain unchanged.

## Fixtures

- `tests/fixtures/pw_runner/specimen_file_read_deny.json`

## Artifacts

- `tests/out/suites/<suite>/<test_id>/artifacts/*` (suite is `smoke` when run directly).
- Caller-auth artifacts include signing commands/metadata, modified service plists,
  requests, raw client output, before/after marker bytes, checker controls, source
  inventories, and fixture process cleanup. No runner registry installation is used.

Run:

```
./tests/run.sh --suite smoke
```

The caller-auth checker also requires response schema 5 from both successful XPC
replies and real client-generated XPC errors. Every returned step must contain
explicit signal null; rejected calls retain empty steps and absent subprocess
metadata alongside the existing authorization and file-effect controls.
