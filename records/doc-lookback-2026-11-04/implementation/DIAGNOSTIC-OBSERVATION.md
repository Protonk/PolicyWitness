# Diagnostic retention and bounded observation

User approved retaining existing host observations in the fixture, keeping
timings and assertions unchanged, then running a bounded observation and
returning with a recommendation. Fresh Astra `retain_setup_diagnostics` prepared
the change; root reviewed the diff, executed the tests and checked receipts.
The agent also reviewed the completed evidence without further execution.
Fifteen specialists have participated; none remain active.

## Change

Only `tests/fixtures/host_setup/SetupControls.swift` and its README changed in
this tranche. The fixture retains optional `CWorkerOutput` from both result
branches and serializes a `worker_observation` projection after the existing
lifecycle and cleanup observations. It includes PID, ready-byte receipt,
ready/sentinel/grace waits, polling and cleanup reasons, exit request,
termination request, reap, exit status, signal, wait errors and collection basis.
Absent output is JSON null; unavailable optional members are omitted.

Production sources, observer, setup recipe/checker, sensitivity transformations,
existing outcome/cleanup fields and 100/200/200 ms allowances are unchanged.
No new channel or clock read is introduced during child execution. Existing
source transformation anchors remain intact. No distribution rebuild or
worker-identity regeneration is needed for this fixture-only change.

The original ten prepared-file hashes remain unchanged. The two additional
file hashes and patch are retained in `implementation/setup-diagnostics-state.json`
and `implementation/setup-diagnostics.patch` (SHA-256
`a470c63f5be9ad78482f6d021823d100d38537c552ed9af416a0c2670f0d5e0b`).
The tested files remained unchanged through execution; `git diff --check` passed.

## Execution and observations

One dispatcher invocation ran outside the automation sandbox:

```sh
env -u PYTHONOPTIMIZE PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-repairs-05 tests/run.sh \
  --case runner_unit/host_setup_controls \
  --case runner_unit/host_setup_oracle_sensitivity
```

Run ID `20261105T031404Z_f3cd7dbb`: both selected cases passed, zero skipped or
unrun, no harness errors and zero recorded sleep. Duration: 40,016 ms.
The controls compile copied sources and do not use the signed app; artifact
integrity is therefore null. No second execution occurred in this tranche.

All 115 scenario receipts have the new field: 25 populated worker observations,
45 explicit nulls for worker setup refusals and 45 explicit nulls for issuer
scenarios. Every populated observation has exit code 0, confirmed reap, no
termination request or signal, no wait errors or clock fault, collection after
confirmed reap, and its independent child receipt.

Each recipe's first observer invocation (`worker-baseline`) exhausted its
sentinel allowance and reaped normally during exit grace:

| Recipe | Ready wait ms / stop | Sentinel ms | Grace ms |
| --- | --- | --- | --- |
| Ordinary setup | 100 / deadline | 200 | 0 |
| Sensitivity baseline | 101 / deadline | 200 | 12 |
| Wrong ready direction | 0 / EOF | 200 | 81 |
| Wrong shared-memory argument | 100 / deadline | 200 | 23 |
| Partial unmap | 102 / deadline | 200 | 0 |

The remaining 20 populated observations reaped during sentinel polling and did
not enter grace; ready waits were 0–12 ms and sentinel waits 0–52 ms. These are
host wait/reap observations, not measurements of child startup or receipt
creation. They show a first-invocation timing difference and that the first
observers needed exit grace in this run. They do not establish why the earlier
receipts were missing, or whether earlier children were killed by the host.

The field-only change is compatible with ordinary, mutated and rejected-checker
controls. Null output on actual setup refusals was observed. Preservation of a
nonnull partial output on a failure branch is implemented but was not exercised
by this run; all populated observations came from successful result branches.
No direct failure-diagnostic observation is claimed.

## Recommendation

Retain the diagnostics and keep deadlines and assertions unchanged. The first
instrumented execution passed, so the earlier missing receipts still lack an
exit/termination explanation. A deadline increase based only on these passes
would not establish the cause.

If pursuing further characterization now, use at most two additional focused
executions with this instrumentation, stopping at the first missing receipt to
inspect the captured status, waits and termination request. If neither
reproduces, stop repeated trials, retain the issue as unresolved fixture
flakiness, and resume the documentation work after review. The positive cases
already establish their bounded observations; this recommendation does not
claim the flake is repaired. Any timing or child instrumentation change should
follow the observed failure branch.

No additional runs or fixes have started. This is the requested review point.

## Retention

Owned output is `tests/out/runs/doc-lookback-repairs-05`. Its original console
and listed selection were attached under the checkout lock after verifying
terminal run/owner IDs, as `test-console.log` and `requested-selection.json`.
`implementation/diagnostic-observation.json` records the terminal accounting,
all 115 receipt paths/hashes and projected observations. Prior runs remain
unchanged, including their failures. Receipt files retain the full independent
child facts and host facts separately.
