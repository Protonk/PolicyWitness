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

- The suite is included in the default battery, including regression guards
  against re-introduction of removed request fields (`instrumentation`) and
  runner modes (`runner.mode=debuggable`).
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
- The validator shortfall and decode-failure cases share the checked-in
  `tests/fixtures/validator` transcripts and `runner_validator_failure`
  contract checks. Both require reversed partial verdicts to retain step
  association, all three completed attempts to retain their actual outcomes,
  and the unanswered prediction to have an explicit error and `drift:null`.
  These two cases also run in the baseline `runner_validator_failure` suite.

## Independent prediction and attempt targets

`prediction_target_is_independent_of_attempt_target` runs two ordinary CLI
specimens with the real validator and no test overrides. Both attempt writes to
two existing files: the policy allows A and denies B. After restoring the same
seed bytes, the second run swaps only the prediction targets. Policy, attempts,
and random step IDs stay fixed. The test reads and retains external file bytes
before decoding PW's JSON: A must change to nonempty data and B must retain every
seed byte in both runs.

The matching run requires allow/success and deny/permission-failure, both with
`drift=false`. The swapped run requires deny/success with `drift=true` and
allow/permission-failure with `drift=null`. This deliberately compares different
targets to check independent channel routing; it makes no compiler-bug claim.
Redirecting a validator query to `attempt.target` must fail even if the envelope
continues to echo the requested filter value. The existing classifier and
steered-validator tests retain their separate contracts.

The case checks step identity/order, raw attempt evidence and compatibility
aliases, prediction and attempt paths, worker/validator completion, and drift.
Shared black-box checks collect both prediction failures rather than stopping
after the first mismatch. `RunCapture` retains each request, raw envelope,
stderr, and capture metadata under `matching/` and `swapped/`; these directories
also contain expectations, byte snapshots, and diagnostics. The case needs the
built app and live XPC; missing equipment fails. Log capture is disabled.

Run it independently with:

```sh
tests/run.sh --case witness_contract/prediction_target_is_independent_of_attempt_target
```

## Artifacts

- `tests/out/suites/witness_contract/<test_id>/artifacts/*`

## Run

```
./tests/run.sh --suite witness_contract
```

Included in the default battery. The catalog shares the two partial-validator
failure cases with `runner_validator_failure`, executing each canonical case once.
