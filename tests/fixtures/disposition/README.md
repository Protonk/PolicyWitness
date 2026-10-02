# Disposition record fixtures

Constructed and captured envelopes for the disposition record contract
(`tests/FAILURE-PROPAGATION-CONTRACT.md` → Worker disposition record). The
independent checker `tests/lib/lifecycle_oracle.py` and the offline controls in
`tests/suites/blackbox_e2e/disposition_controls.py` consume them.

- `a1_known_loss.json`: a real envelope captured from the
  `worker_attempt_in_flight_at_deadline` case's `a1` specimen against the build
  that predates the record (response 9, envelope 2). It witnesses the deadline,
  the SIGKILL request, the reaped signal and the attempt 0 started progress
  while that controller reported `termination_cause: unknown`. Readers refuse
  it as an unsupported version before any claim is read. Missing-record
  controls remove the record from the current-shaped `a1_expected.json`.
  It is never a baseline for unrelated rejection controls.
- `a1_expected.json`: a live envelope of the same `a1` specimen captured from
  the current build under the current contract (controller envelope 5,
  response 13): the host facts, the carried record, the per-step lifecycle
  objects and limitations, the uniform `data.specimen` dossier and the
  projected `host_sentinel_deadline`, `sentinel_deadline` and `signaled`. The
  controls accept it and reject named mutations of it; the controller's own
  unit tests read it as the known-good disposition reply.
