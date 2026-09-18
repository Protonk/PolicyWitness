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

Additional checked-in transcripts return two valid replies then invalid UTF-8,
an incomplete allow/deny record, an unfamiliar diagnostic, a duplicate ID or an
unexpected ID. `failure_boundaries` copies each transcript beside the unchanged
fixture executable and compares the retained emitted bytes with host evidence.
The unfamiliar diagnostic includes an extra numeric code in raw JSON. These
transcripts test the real receiver; they do not classify normal validator output
as corrupt. Byte output is written and retained without text replacement.

Responses may override returned query fields with `fields` or remove them with
`omit`, independently of the recorded incoming probes. Wrong-query controls
cover operation, filter type, filter value and missing required filter value.
The unfamiliar diagnostic omits query metadata and native results.
