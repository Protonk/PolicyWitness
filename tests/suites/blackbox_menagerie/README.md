# blackbox_menagerie

End-to-end black-box suite that exercises specimen ingestion and evidence
correlation using real SBPL inputs and compiled profile blobs. Fixtures are
copied locally from PAWL evidence; the suite never reads external evidence at
runtime.

## Invariants

- One specimen -> one PWRunner instance; runner applies one sandbox and exits.
- Every probe step includes sandbox_check and an attempted operation, and both
  are validated together.
- Probe actions are idempotent and scoped under a per-run root.

## Case families

- Strict subpath allow with explicit denies outside the allow root.
- Read-only profile with a non-sandbox failure (ENOENT) control.
- Mach-lookup allow/deny with a missing-service control.
- Canonicalization boundary cases (alias vs canonical spelling); expected
  mismatches are recorded as evidence via mismatch_reason.
- Compiled-blob profiles to exercise compiled-bytes ingestion; these cases may
  skip when profile registration is not permitted.

## Fixtures and manifests

- Manifest: `tests/fixtures/blackbox_menagerie/cases/core.json`
- SBPL sources: `tests/fixtures/blackbox_menagerie/sbpl/`
- Compiled blobs: `tests/fixtures/blackbox_menagerie/compiled/`

## Adding cases

1. Drop SBPL or compiled blob under `tests/fixtures/blackbox_menagerie/`.
2. Add a case entry to `tests/fixtures/blackbox_menagerie/cases/core.json` with
   steps and expectations.
3. Use mismatch_reason when you want a mismatch to be recorded as evidence
   rather than a failure.

Run:

```
./tests/run.sh --suite blackbox_menagerie
```
