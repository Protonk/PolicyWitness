# blackbox_menagerie

End-to-end black-box suite that exercises specimen ingestion and evidence
correlation using real SBPL inputs. These scripts are
shared and invoked by the BYOXPC runner suite.

## Invariants

- Each specimen launches a fresh XPC host and worker; the worker applies one
  sandbox and exits.
- Every probe step includes sandbox_check and an attempted operation, and both
  are validated together. Step IDs are unique and retain their expected order.
- Probe actions are idempotent and scoped under a per-run root.

## Case families

- Strict subpath allow with explicit denies outside the allow root.
- Read-only profile with a non-sandbox failure (ENOENT) control.
- Mach-lookup allow/deny with a missing-service control.
- Canonicalization boundary cases (alias vs canonical spelling); expected
  mismatches are recorded as evidence via mismatch_reason.

## Success criteria

- Every evidence check must pass. Failures accumulate across channels and steps.
- Expected mismatches are recorded as evidence (via `mismatch_reason`).
- If an annotated mismatch is absent, the case skips only after all evidence
  checks pass. A missing or incorrect result always takes precedence over that
  pending skip. `prediction_unavailable` is checked as evidence, never skipped.

`run_case.py` handles the specimen and invocation; `validate_run.py` checks the
captured JSON. Both this suite and `blackbox_e2e` use `tests/lib/blackbox.py` for
envelope, step identity/order, required fields, scalar types, and explicit
prediction/attempt/errno/drift expectations. Missing fields are distinct from
explicit nulls, and booleans cannot stand in for integers. This suite retains
its policy-hash requirement, file observations, and policy/mismatch decisions.

## Fixtures and manifests

- Manifest: `tests/fixtures/blackbox_menagerie/cases/core.json`
- SBPL sources: `tests/fixtures/blackbox_menagerie/sbpl/`

`validation_controls` runs before the live cases, even without a built app.
It drives both checker CLIs with the independently authored missing-path
envelope under `tests/fixtures/blackbox_e2e/checker/` and explicit expectations
in `checker_controls.py`. Controls cover valid allow/deny/unavailable/error
shapes, missing versus null fields, boolean/integer confusion, duplicate and
reordered IDs, malformed channels, and combined failures. Menagerie controls
also require a later failure to defeat an earlier pending mismatch skip, and
protect the policy-hash, file-observation, and annotated-mismatch checks.
The controls import neither the shared checker nor production code.

## Artifacts

- `tests/out/suites/<suite>/<case>/artifacts/*` (suite is `blackbox_menagerie` when run directly).
- Validation controls retain each input, expectation file, exit status, and
  diagnostics, separately for each checker CLI.

## Adding cases

1. Drop SBPL under `tests/fixtures/blackbox_menagerie/`.
2. Add a case entry to `tests/fixtures/blackbox_menagerie/cases/core.json` with
   steps and expectations.
3. Use mismatch_reason when you want a mismatch to be recorded as evidence
   rather than a failure.

Run:

```
./tests/run.sh --suite blackbox_menagerie
```
