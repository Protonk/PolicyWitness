# Disposition record fixtures

Captured envelopes for the disposition record contract
(`tests/FAILURE-PROPAGATION-CONTRACT.md` → Worker disposition record). The
independent checker `tests/lib/lifecycle_oracle.py` and the offline controls in
`tests/suites/blackbox_e2e/disposition_controls.py` consume the current fixture.

- `response14/a1_expected.json`: a live capture of the `a1` specimen from
  `witness_contract/worker_attempt_in_flight_at_deadline`, carried at the current
  controller envelope: the top-level `schema_version` follows an envelope bump
  that leaves this frame's keys unchanged; the reply and every record are the
  captured bytes. Its build stamp,
  binary hashes and worker source identity identify the producer. The controls
  accept it and reject named mutations; Rust unit tests use its runner reply
  as the known-good disposition record. Missing-record controls remove the
  record from a copy of this current-format fixture.
- `a1_expected.json`: a preserved response-13, envelope-6 capture of the same
  specimen. Current readers reject its response version. It remains evidence
  of that producer and is not rewritten into the current format.
- `a1_known_loss.json`: a preserved response-9, envelope-2 capture. It witnesses
  the deadline, SIGKILL request, reaped signal and attempt-0 started progress
  while that controller reported `termination_cause: unknown`. Rejection
  controls refuse it before reading claims. It is never an acceptance baseline.

All three carry disabled log capture; log evidence supplies no worker cause.
