# Disposition record fixtures

Captured envelopes for the disposition record contract
(`tests/FAILURE-PROPAGATION-CONTRACT.md` → Worker disposition record). The
independent checker `tests/lib/lifecycle_oracle.py` and the offline controls in
`tests/suites/blackbox_e2e/disposition_controls.py` consume the current fixture.

- `response23/a1_expected.json`: an unmodified live capture of the `a1` specimen
  from `witness_contract/worker_attempt_in_flight_at_deadline`. Its build stamp,
  binary hashes and worker source identity identify the producer. The controls
  accept it and reject named mutations; Rust unit tests use its runner reply
  as the known-good disposition record. Missing-record controls remove the
  record from a copy of this current-format fixture.
- `a1_known_loss.json`: a preserved response-9, envelope-2 capture. It witnesses
  the deadline, SIGKILL request, reaped signal and attempt-0 started progress
  while that controller reported `termination_cause: unknown`. It is retained
  evidence with no executable consumer and is never an acceptance baseline.

`response23/a1_specimen.json` is the exact submitted request for the current
capture; the two refresh together, as described below.
Previous-envelope rejection uses constructed controls; superseded acceptance
captures remain available in Git.

## Refresh

A response or controller-envelope version bump makes the readers reject the
current capture. Capture a new pair, without editing its contents; the
`responseNN/` directory names the runner response schema. Run
`witness_contract/worker_attempt_in_flight_at_deadline` against the final
candidate and copy `artifacts/a1/run.json` and `artifacts/a1/specimen.json`
from its case directory here as `responseNN/a1_expected.json` and
`responseNN/a1_specimen.json`. For a response schema change, bump `schema_version` in
`../contract/path_diagnostics.json` (one value per case) and replace
`../contract/response_shape.json` with the `response_shape.candidate.json`
that `runner_unit` writes when the golden disagrees. Retain the capture run in
`tests/RETAINED.json`. The checker captures under
[`../blackbox_e2e/checker/`](../blackbox_e2e/checker/README.md) refresh with
the same bump.
