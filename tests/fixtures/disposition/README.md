# Disposition record fixtures

Constructed and captured envelopes for the disposition record contract
(`tests/FAILURE-PROPAGATION-CONTRACT.md` → Worker disposition record). The
independent checker `tests/lib/lifecycle_oracle.py` and the offline controls in
`tests/suites/blackbox_e2e/disposition_controls.py` consume them.

- `a1_known_loss.json`: a real envelope captured from the
  `worker_attempt_in_flight_at_deadline` case's `a1` specimen against the build
  that predates the record (response 9). It witnesses the deadline, the SIGKILL
  request, the reaped signal and the attempt 0 started progress while the
  controller reports `termination_cause: unknown` and both steps carry identical
  compatibility triples. It is accepted as the legacy reply it is; with its
  version raised to the record version it is rejected for the missing record.
  It is never a baseline for unrelated rejection controls.
- `a1_expected.json`: the expected output for the same witnessed raw facts under
  the contract: the three new host facts, the record built from the reviewed
  `a1_fifo_in_flight` claim row, the per-step lifecycle objects and limitations,
  and the projected `host_sentinel_deadline`, `sentinel_deadline` and `signaled`.
  It is an expected-output fixture built before the app produces the record, not
  a claimed live result. The controls accept it and reject named mutations of it.
