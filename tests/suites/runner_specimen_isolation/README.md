# runner_specimen_isolation

Public CLI contract for two overlapping specimens through the bundled runner.
Both use identical random step IDs, distinct specimen IDs, stderr markers and
file targets, and opposite allow/deny patterns. No `_test_overrides`, worker ABI,
production imports, log capture, or external runner installation are used.

The shared exec fixture holds each run at its first step. The observer obtains
helper PIDs from kernel socket credentials and follows libproc parentage to
the worker and XPC host. All six identities must be distinct. Both trees must
respond while held, and all four seeded files must still contain their seeds.

B is released first. It must finish with its helper tree, worker, and XPC host
stopped (independently observed OS exit events), its allowed
file changed with nonempty data, and its denied file unchanged. A must still
answer, have the same OS process identities, and retain its untouched files.
After releasing A, its opposite file effects must occur without changing B's
files. Each JSON envelope must match its own specimen, OS-observed worker and
exec child, stdout/stderr, ordered steps, paths, predictions, and attempts.

## Controls

The same envelope checker must reject twelve corruptions of the successful
captures: whole envelopes, each individual step, a prediction, and an attempt
copied from the other run, in both directions. Step IDs remain identical.
The prediction-only control repairs the worker PID to the recipient's PID,
requiring the path and decision assertions themselves to detect the swap.
Failures must identify the recipient and the mismatched evidence fields.

`exec_fixture` independently tests the observer: two direct process trees are
live together, releasing B leaves A responsive with unchanged process identity,
and the liveness assertion rejects the exited B tree. Process snapshots are
checked against directly launched PIDs, parentage, and executable paths.

## Running and artifacts

Run `tests/run.sh --suite exec_fixture --suite runner_specimen_isolation` outside
an automation sandbox. Both suites are in the default battery. Missing builds,
toolchain errors, failed rendezvous, and unavailable process metadata fail.

Rendezvous and CLI waits are bounded; the real ten-second exec deadline remains
active, and the helper retains its 45-second backstop. The coordinator uses
socket handshakes rather than sleeps to establish overlap. Cleanup runs after
the observations and assertions, so cleanup cannot supply the claimed evidence.

Artifacts retain both specimens/envelopes, process snapshots, an event timeline,
before/held/after file bytes, and every corrupted envelope with its diagnostics.

`tests/lib/run_capture.py` prepares both specimens before either CLI starts,
captures each run's raw output separately, and records command/exit/timing and
harness intervention in each run's `capture.json`. The test owns the gates,
independent observations, and expected results. Capture cleanup runs after those
assertions, and JSON is decoded only after the independent file observations.
Direct capture controls live in the `run_capture` suite.
