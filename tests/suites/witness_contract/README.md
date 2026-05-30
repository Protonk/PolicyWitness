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

- The suite is **off the default battery** because it carries a few
  load-bearing regression guards against re-introduction of removed
  request fields (`instrumentation`) and runner modes
  (`runner.mode=debuggable`).
- `happy_path_baseline.sh` is the regression sentinel — it must pass
  in every run. If it fails, stop and investigate before continuing.
- Tests are stateless: named for what they assert, not for any
  plan-row number.

## Success criteria

- Every test passes.

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

Not invoked by `tests/run.sh --all` — run on demand.
