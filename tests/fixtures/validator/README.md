# Validator transcript fixture

`validator.py` implements the test side of the `--batch <worker PID>` NDJSON
protocol without PW imports. Copy it into a case's artifact directory and
place `eof.json` or `malformed.json` next to it as `validator.case.json`.
The failure tests copy checked-in code and data; they do not generate programs.

The fixture reads all three probes before responding. Each transcript selects
probe 1 then probe 0, returns deny and allow respectively, and copies the
actual step IDs, operations, and filter metadata. `eof` then exits zero;
`malformed` writes `invalid-verdict:<third step ID>` and exits zero. That
malformed line must be the parse error reported by PW. A ten-second alarm
bounds a caller that never finishes writing its probes.

`validator.received.json` records the target worker PID and incoming probes;
`validator.emitted.ndjson` retains the exact emitted bytes. These let the tests
prove all three queries reached the validator, the replies were reversed,
and the third prediction is missing because of the transcript rather than
host-side filtering. Fixture setup/protocol failures do not count as intended
validator degradation.

`runner_validator_failure/transcript_controls` checks both transcripts directly
with fresh IDs and targets. The CLI contract then checks accepted verdicts,
completed attempts, and missing-prediction semantics independently of the
fixture's transcript configuration.
