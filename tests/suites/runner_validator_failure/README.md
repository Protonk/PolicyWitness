# runner_validator_failure

Validator failure must preserve accepted verdicts, completed attempt evidence,
and their association with probe steps. Run with:

```sh
tests/run.sh --suite runner_validator_failure
```

This baseline suite needs the built app and Python 3, and must run outside an
automation sandbox. Missing prerequisites fail. It has three cases:

- `transcript_controls`: directly check the shared validator fixture's input
  receipt, reversed reply order, distinct verdicts, and EOF/malformed tail.
- `validator_unavailable_reports_degraded`: two valid replies for three probes,
  followed by clean EOF. Require `validator_unavailable` and a 2-of-3 shortfall.
- `validator_decode_failure_reports_degraded`: the same accepted replies followed
  by malformed JSON. Require `validator_decode_failure` naming that malformed line.

Both CLI cases use `_test_overrides.validator_executable_path` and require that
exact override to be mirrored. They run three distinguishable operations against
freshly seeded files: an allowed write, a denied write, and a denied access check.
The first file must change to nonempty content; the others must retain their
bytes. The envelope must preserve `ok`, `open_failed`, and `access_failed`, with
paths, error evidence, and permission errno values attached to the right steps.

The validator returns deny for the second step before allow for the first.
Results must retain probe-plan order while associating these accepted verdicts
by step ID. Allow/success has drift=false; deny/permission failure has
directional consistency and drift=null. The unanswered third step must have the current
missing-verdict representation: `sandbox_check.outcome="error"`, a missing-verdict
diagnostic, and an explicitly present `drift:null`. All three queries must appear
in the fixture's received transcript, ruling out an upstream prediction skip.
The run must be degraded (`result.ok=false`, nonzero CLI/runner rc), while worker
and validator exit cleanly and the worker reports complete steps.

Artifacts retain the specimen, full envelope, copied fixture/transcript, input
receipt, emitted bytes, file snapshots, and assertion logs. No worker ABI or
Swift types are used by the fixture or contract assertions.

CLI execution uses `tests/lib/run_capture.py`. Its `capture.json` retains command,
exit status, timing, and any harness intervention alongside raw `run.json` and
`pw.stderr`. The test checks independent file effects before decoding the
envelope and retains ownership of the expected nonzero exit and degradation.
Direct capture controls live in the `run_capture` suite.

The matching `witness_contract` scripts call `case.sh` with their original suite
name. This keeps their existing entry points while sharing the same assertions.

The shell entry point uses `tests/lib/case.sh` for setup and logged checks.
Case IDs, checker arguments, and artifact paths remain defined by this suite.
The `shell_helpers` controls verify failure propagation and report/log behavior.
