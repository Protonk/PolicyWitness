# Bounded characterization of missing observer receipts

The user authorized at least one and at most two additional test starts before
reconvening. Root ran the unchanged focused case twice; both passed. Fresh Astra
`characterize_setup_flake` inspected source and existing receipts without edits
or execution. Root reviewed its source anchors and conclusions. Fourteen
specialists have participated in the lookback; this investigator is finished.

## Observations

Each new command ran outside the automation sandbox with assertions enabled:

```sh
env -u PYTHONOPTIMIZE PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-repairs-03 tests/run.sh --case runner_unit/host_setup_oracle_sensitivity
env -u PYTHONOPTIMIZE PW_TEST_OUT_DIR=tests/out/runs/doc-lookback-repairs-04 tests/run.sh --case runner_unit/host_setup_oracle_sensitivity
```

| Run suffix | Run ID | Baseline | Wrong ready direction | Wrong shared-memory argument | Partial unmap |
| --- | --- | --- | --- | --- | --- |
| 01 | `20261105T025009Z_d5dead5d` | Pass | Pass | Missing child | Missing child |
| 02 | `20261105T030143Z_908ddc80` | Pass | Missing child | Pass | Pass |
| 03 | `20261105T030620Z_7f63d81d` | Pass | Pass | Pass | Pass |
| 04 | `20261105T030702Z_8928390b` | Pass | Pass | Pass | Pass |

Run 01 included 82 other passing cases. Runs 02–04 selected only this case.
Runs 03 and 04 completed in 31,349 ms and 30,588 ms, respectively. Every
execution of the case reports zero system-sleep overlap. Each passing variant
completed its 23 recipe scenarios and the required checker controls; failures
aborted that variant's recipe at its first `worker-baseline` scenario.

The 46 retained copied-input files match across all four runs. The tracked
patch and ten prepared-file hashes remain identical to the pre-build snapshot.
No rebuild or source edit occurred. Each case builds fresh fixture products;
different output paths are compiled into observer binaries, so this is source
identity, not a claim that all executable bytes match. This case does not use
the signed distribution app.

In all three failed variants, the first observer's receipt path was absent
after the host returned. Native spawn rc 0, child PID, host reap and fixture
cleanup were recorded; the per-scenario log was empty. Failure moving between
variants with identical copied inputs establishes intermittent behavior of the
control. These four sequential runs are not an estimate of its failure rate.
Passing later runs neither explain nor erase earlier failures.

## What the source establishes

The independent observer deliberately does not implement the worker protocol.
It inspects descriptors before opening its receipt, then writes JSON and exits
(`tests/fixtures/host_setup/observer.c:10–26`). Python removes the old receipt
before each invocation and records `child: null` only when the new path is
absent (`tests/suites/runner_unit/host_setup_controls.py:138–143`). Ordinary
interruption after successful creation would instead tend to leave partial
JSON and raise a decode error. This narrows the missing-path observation but
does not identify why creation failed.

The 100 ms ready allowance is not a kill deadline. The ready wait ends on
byte, EOF, error or expiry (`runner/Sources/PWRunnerCore/ActorSession.swift:401–425`).
The single-worker driver then permits a 200 ms sentinel interval
(`runner/Sources/PWRunnerCore/CWorker.swift:1058–1151`), followed by a 200 ms
exit grace (`ActorSession.swift:530–553`), with earlier reap ending these waits.
Only an unreaped, still-owned child reaches SIGKILL
(`CWorker.swift:1030–1035`). Wrong ready direction can remove the writer and
cause immediate EOF, bypassing the ready allowance, but sentinel and grace
still follow. This does not explain failures in the other variants.

The fixture discards the observations needed to distinguish mechanisms:
`tests/fixtures/host_setup/SetupControls.swift:157–160` reduces `CWorkerOutput`
to a PID string, losing exit code, signal, termination request, wait errors,
poll reason and wait records already available from `ActorSession.swift:648–695`.
Its later `host_reaped` check observes ECHILD (`SetupControls.swift:174–179`),
which does not distinguish normal completion from a killed or crashed child.

Receipt-open failure silently returns 91, and close failure returns 92
(`observer.c:16,26`); errno is not logged and individual writes are unchecked.
Startup failure, a crash before receipt creation, a receipt-open error and host
termination before creation can therefore yield the same retained observation.

## Assessment and proposed next step

Startup/scheduling delay followed by cleanup before receipt creation is a
plausible hypothesis. A child exit before creation, including an open error or
startup failure, is also compatible. External deletion or path mismatch has
less supporting evidence. The fixed first-scenario order and early abort mean
the first-invocation pattern alone cannot establish a cold-start cause.

Before changing any allowance, add fixture-only retention of the existing
worker output: ready/sentinel/grace waits, poll stop, exit status, termination
request and wait errors. Keep the legacy checker and timing unchanged so the
new fields explain a failure without making it pass. Preserve descriptor
observation before acquiring any diagnostic channel. Add error diagnostics if
native receipt creation/close failures need differentiation. A later controlled
timing change should follow the observed branch; increasing 100 ms alone cannot
characterize an EOF path.

This is a proposal, not an implemented repair. Both allowed new executions are
complete; no further test starts, edits or documentation-owner dispatches have
occurred. The control now has complete positive observations as well as its
unresolved failures. Review its reliability before moving on.

## Evidence retention

Original runs remain under `tests/out/runs/doc-lookback-repairs-01` through
`-04`. Within each, `run.json` and
`suites/runner_unit/host_setup_oracle_sensitivity/artifacts/controls/` retain
accounting, input inventories, exact copied sources, builds, variant results,
raw receipts and independent observations. New console transcripts were
attached as `test-console.log` under the checkout lock after verifying terminal
run and owner identities. `implementation/flakiness-characterization.json`
records run, transcript and source hashes and comparison results. No failure
record was overwritten or credited as a pass.
