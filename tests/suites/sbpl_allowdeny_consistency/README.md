# sbpl_allowdeny_consistency

Runs the v1 smoke fixture twice through the built CLI. Each run has four
steps: two file writes and the fixture's two Mach lookups. File targets and
step IDs are random, and seed bytes are generated separately for each run.
The second run keeps the probe plan fixed and reverses only the allow/deny
policy parameter bindings, after restoring both files.

## Invariants

- The test reads the files itself before consulting PW's JSON. The allowed
  write leaves changed, nonempty data; the denied file retains every seed byte.
  An open that only truncates the file does not pass the write-effect check.
- These effects reverse when the parameter bindings reverse.
- Both runs complete successfully without `_test_overrides`; the file verdicts,
  exit codes, errno fields, and path fields agree with the external evidence.
- All four step IDs survive. The Mach steps are checked for presence only;
  this test does not establish Mach service liveness or lookup correctness.

## Running and artifacts

Run `tests/run.sh --suite sbpl_allowdeny_consistency` outside an automation
sandbox (request escalation there). Missing builds and run failures fail the
test. Unified log capture is disabled; it is not this test's oracle.

Artifacts include both specimens and envelopes, stderr, `assert.log`, and
separate `.before` / `.after` byte snapshots for each file in each round.
