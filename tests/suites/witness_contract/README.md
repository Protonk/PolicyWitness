# witness_contract

Pins the load-bearing behaviors PolicyWitness contracts to provide:
verdicts in the envelope, attempts in the envelope, drift between the
two surfaced explicitly, validator failures attributed honestly, removed
fields rejected, the test seam functioning, and the source-drift
guardrail enforcing the audit trail.

Each test asserts one contract claim. The suite reads as a
behavior specification — what PolicyWitness promises, regardless of
the architecture behind it.

## Invariants

- The suite is **off the default battery** during the runner reshape
  (`RUNNER-RESHAPE-PLAN.md`). Most tests are expected to fail until
  the corresponding plan row lands; each failure prints a precise
  "PASSES WHEN: …" line naming the gating row.
- `happy_path_baseline.sh` passes today and should pass after every
  step of the reshape. If it ever fails mid-refactor, stop and
  investigate before continuing.
- Tests are stateless: named for what they assert, not for the row
  number that gates them. When the reshape is complete and the suite
  is fully green, it promotes to a permanent regression suite.

## Success criteria

- Every test passes. Today: only `happy_path_baseline` does.
- Once fully green, the suite migrates from this `Contract` tier into
  `Baseline` and runs in the default battery.

## Fixtures

- Specimens are generated inline per test.
- `happy_path_baseline` uses a stable `(version 1) (allow default)`
  policy with one file read step.

## Artifacts

- `tests/out/suites/witness_contract/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite witness_contract
```

Not invoked by `tests/run.sh --all` during the reshape — run on demand.
