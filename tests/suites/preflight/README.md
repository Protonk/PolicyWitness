# preflight

Codesign and entitlements inspection only (no execution).

## Invariants

- Reads codesign metadata for the built app and embedded XPC services.
- Never executes `policy-witness` or the runner.

## Success criteria

- Codesign verification succeeds and a preflight report is written.

## Fixtures

- None.

## Artifacts

- `tests/out/suites/preflight/codesign.preflight/artifacts/preflight.json`

Run:

```
./tests/run.sh --suite preflight
```
