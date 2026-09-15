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

The suite uses `tests/lib/blackbox.py` for envelope shape, exact step identity
and order, required evidence fields, scalar types, and expected prediction,
attempt-success and drift values. Expectations come from the request and
test-owned witness records. Compatibility fields remain required: `rc` agrees
with `exit_code`, and `errno` agrees with `syscall_errno`, including their types.
Successful attempts here require explicit null errno values; denied writes
require integer EPERM/EACCES. Nullable path fields remain present. Optional
attempt `error` text may be absent or null.

The isolation adapter retains its independent process identities, specimen
attribution, expected paths, attempt outcomes, exec output and file observations.
Shared diagnostics are prefixed with the recipient's label. Steps are matched
to expectations by ID even after an ordering error, so a reordered response
cannot misattribute a later diagnostic or suppress the remaining checks.

## Controls

The same envelope checker must reject twelve corruptions of the successful
captures: whole envelopes, each individual step, a prediction, and an attempt
copied from the other run, in both directions. Step IDs remain identical.
The prediction-only control repairs the worker PID to the recipient's PID,
requiring the path and decision assertions themselves to detect the swap.
Failures must identify the recipient and the mismatched evidence fields.

Both runs' denied attempts receive a fixed 24-case matrix of single-field
deletions, nulls and booleans. Required fields must reject invalid evidence;
optional `error` omissions must pass. Successful steps separately reject missing
or boolean errno evidence. Alias disagreements with otherwise valid types must
fail, while matching EPERM and EACCES aliases both pass. The unmodified captures
are positive controls, including explicit null on successful attempts.

Each run has paired ordered/reordered controls for valid evidence and for an
exec attempt that contradicts its expected success. Reordering must add exactly
one order error and preserve the multiset of all other diagnostics, including
the moved attempt's attribution. Extra, lost, and duplicated step errors fail;
diagnostic line order is unconstrained. The ordered inputs must independently
pass or report the specified attempt failure, so agreement alone cannot pass.

Combined controls also require both a malformed prediction and a missing alias
on another step. Every rejected case requires the relevant diagnostic, not merely an
exception or an unrelated assertion failure. All controls use the actual suite
checker and retain their candidate envelopes and diagnostics.

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

The shell entry point uses `tests/lib/case.sh` for setup and logged checks.
Case IDs, checker arguments, and artifact paths remain defined by this suite.
The `shell_helpers` controls verify failure propagation and report/log behavior.
