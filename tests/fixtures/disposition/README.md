# Disposition record fixtures

Captured envelopes for the disposition record contract
(`tests/FAILURE-PROPAGATION-CONTRACT.md` → Worker disposition record). The
independent checker `tests/lib/lifecycle_oracle.py` and the offline controls in
`tests/suites/blackbox_e2e/disposition_controls.py` consume the current fixture.

- `response14/a1_expected.json`: an unmodified live capture of the `a1` specimen
  from `witness_contract/worker_attempt_in_flight_at_deadline`. Its build stamp,
  binary hashes and worker source identity identify the producer. The controls
  accept it and reject named mutations; Rust unit tests use its runner reply
  as the known-good disposition record. Missing-record controls remove the
  record from a copy of this current-format fixture.
- `a1_known_loss.json`: a preserved response-9, envelope-2 capture. It witnesses
  the deadline, SIGKILL request, reaped signal and attempt-0 started progress
  while that controller reported `termination_cause: unknown`. Rejection
  controls refuse it before reading claims. It is never an acceptance baseline.

Both carry disabled log capture; log evidence supplies no worker cause.
`response14/a1_specimen.json` is the exact submitted request for the current
capture. Refresh it together with the envelope from a passing live case.
Previous-envelope rejection uses constructed controls; superseded acceptance
captures remain available in Git.
