# Disposition record plan

This plan repairs one class of evidence flaw: a fact is witnessed and published
in the envelope, but the conclusion field that should be derived from it is
computed from a hand-picked subset that leaves the fact out. The envelope then
says "unknown" or "incomplete" about something it already knows. The repair is
a single host-witnessed disposition record, derived once from the full
lifecycle fact set, carried in the runner reply, and projected into every
downstream conclusion field instead of re-derived there.

The plan has two halves that matter equally. The reproduction chain lets you
observe the flaw at every layer before changing anything, and re-observe the
repair afterwards. The eventual-behavior section states what the envelope must
say once the record exists. The test battery and the exact code changes are
deliberately left open; the acceptance observations are not.

Read [AGENTS.md → Core ideas](../AGENTS.md#core-ideas) first. "No dishonest
attribution" is the principle this plan serves, not one it relaxes: a host
saying "I killed the worker because my deadline expired while attempt 0 was in
flight" is a first-person record of its own action, not an attribution to the
sandbox.

## Vocabulary

- **Fact field**: a value written by the layer that observed it, without
  interpretation. `runner_subprocess.termination_request`, `poll_stop_reason`,
  `term_signal`, `worker_evidence.progress`, and each slot's `completed` flag
  are fact fields.
- **Conclusion field**: a value derived from fact fields for a reader.
  `runner_sandbox_diagnostics.termination_cause`, `attempt.outcome`,
  `attempt.missing_reason`, and `comparison.limitations` are conclusion fields.
- **Witnessed**: known to the host because the host did it or read it from
  shared memory it owns. **Inferred**: matched from an outside source, such as
  a unified-log line with the worker's PID. Only witnessed facts feed the
  record. Inference keeps its own separately labelled fields.
- **Projection**: a conclusion field computed as a total function of the
  record, with no additional inputs.
- **Seam**: a `_test_overrides` key or a specimen that drives a real fault at
  a real boundary. The rules for seams are in
  [runner/AGENTS.md](../runner/AGENTS.md).

## STR chain

Each link has a command, the observation it must produce, what that
establishes, and what to do if it does not. Do not skip links: a later link
only means something if the earlier ones held. All runs use `--no-log-capture`
so a run costs its worker budget and nothing else.

Preconditions. A signed build exists at `dist/PolicyWitness.app`; if not, run
`make build` (see [docs/SIGNING.md](../docs/SIGNING.md)). You are not inside a
sandboxed automation harness; if XPC lookup is refused, see
[AGENTS.md → Sandboxed automation harnesses](../AGENTS.md#sandboxed-automation-harnesses)
and rerun the same commands outside it. Nothing here goes through
`tests/run.sh`, so the checkout lock is not involved.

```sh
cd "$(git rev-parse --show-toplevel)"
PW=dist/PolicyWitness.app/Contents/MacOS/policy-witness
W=$(mktemp -d)
$PW --version | head -c 400; echo
```

### Link 1: baseline envelope

```sh
cat > "$W/control.json" <<JSON
{ "schema_version": 1, "specimen_id": "control",
  "policy": { "format": "sbpl", "sbpl_source": "(version 1) (allow default)" },
  "probe_plan": [
    { "step_id": "hosts",
      "sandbox_check": { "operation": "file-read-data", "filter": { "kind": "path", "value": "/etc/hosts" } },
      "attempt": { "kind": "file", "action": "open_read", "target": "/etc/hosts" } } ] }
JSON
/usr/bin/time -p $PW run --no-log-capture "$W/control.json" > "$W/control.out.json"; echo "rc=$?"
```

Expect `rc=0` and a real time well under one second. In the envelope,
`data.runner_result.normalized_outcome` is `ok`, `runner_subprocess.poll_stop_reason`
is `done`, `partial_steps` is `false`, `worker_evidence.progress` decodes to
operation 10 (finished), phase 2 (returned), no index, and the single step's
`attempt.outcome` is `ok`. This establishes that the live path works and fixes
the shape a healthy reply has. If this link fails, nothing later is about the
disposition record; debug the environment first.

### Link 2: a blocking in-process attempt

```sh
mkfifo "$W/blocker.fifo"
cat > "$W/fifo.json" <<JSON
{ "schema_version": 1, "specimen_id": "fifo_then_file",
  "policy": { "format": "sbpl", "sbpl_source": "(version 1) (allow default)" },
  "probe_plan": [
    { "step_id": "fifo",
      "sandbox_check": { "operation": "file-read-data", "filter": { "kind": "path", "value": "$W/blocker.fifo" } },
      "attempt": { "kind": "file", "action": "open_read", "target": "$W/blocker.fifo" } },
    { "step_id": "hosts",
      "sandbox_check": { "operation": "file-read-data", "filter": { "kind": "path", "value": "/etc/hosts" } },
      "attempt": { "kind": "file", "action": "open_read", "target": "/etc/hosts" } } ] }
JSON
/usr/bin/time -p $PW run --no-log-capture "$W/fifo.json" > "$W/fifo.out.json"; echo "rc=$?"
```

Expect `rc=1` and a real time between 60 and 80 seconds. The worker's
`open(O_RDONLY)` on a FIFO with no writer blocks at
[pw_probe_runner.c](tools/pw_probe_runner/pw_probe_runner.c) in
`attempt_file_open_read`; the only backstop is the host's whole-phase sentinel
wait in `timeoutMsForCWorker` in
[CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift),
nominally 60 s and observed longer because the poll loop's per-iteration cost
adds to it. If the run returns in under a second, the FIFO had a writer or the
path was not a FIFO; recreate it and confirm with `ls -l "$W/blocker.fifo"`
(the mode string starts with `p`). Do not open the FIFO from another shell
while the run is in progress.

### Link 3: the facts are in the envelope

```sh
python3 - "$W/fifo.out.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))['data']['runner_result']
s = r['runner_subprocess']
print('normalized_outcome     ', r['normalized_outcome'])
print('poll_stop_reason       ', s['poll_stop_reason'])
print('exit_requested         ', s['exit_requested'])
print('termination_request    ', s['termination_request'])
print('term_signal / reaped   ', s['term_signal'], s['reaped'])
print('done_observed / partial', s['done_observed'], s['partial_steps'])
print('progress               ', s['worker_evidence']['progress'])
print('error                  ', r['error'])
PY
```

Expected observation:

| Field | Value |
| --- | --- |
| `normalized_outcome` | `runner_timeout` |
| `poll_stop_reason` | `sentinel_deadline` |
| `exit_requested` | `true` |
| `termination_request` | `{"rc": 0, "signal": 9}` |
| `term_signal`, `reaped` | `9`, `true` |
| `done_observed`, `partial_steps` | `false`, `true` |
| `progress` | `{"operation": 9, "phase": 1, "index": 0, "raw": 152043521}` |
| `error` | `pw-probe-runner sentinel deadline expired; host requested SIGKILL during cleanup` |

This establishes that the host published a complete first-person account: its
deadline fired, it requested SIGKILL and the request succeeded, the reaped
signal matches, and the last progress word the worker wrote says attempt index
0 started and never returned. Operation 9 is `PW_OP_ATTEMPT` and phase 1 is
`PW_PROGRESS_STARTED` in
[pw_probe_runner_abi.h](tools/pw_probe_runner/pw_probe_runner_abi.h); the word
is encoded by `pw_progress` in
[pw_worker_evidence.h](tools/pw_probe_runner/pw_worker_evidence.h) as
`(op << 24) | (phase << 20) | (index + 1)`, and 152043521 decodes exactly.

### Link 4: the conclusions ignore those facts

```sh
python3 - "$W/fifo.out.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))['data']
for st in d['runner_result']['steps']:
    a = st['attempt']
    print(st['step_id'], a['outcome'], a['missing_reason'], a['result_source'],
          [l for l in st.get('comparison', {}).get('limitations', []) if l.startswith('attempt')])
g = d['runner_sandbox_diagnostics']
print('process_disposition', g['process_disposition'], '| termination_cause', g['termination_cause'])
PY
```

Expected observation:

| Step | `outcome` | `missing_reason` | `result_source` |
| --- | --- | --- | --- |
| `fifo` | `not_run_worker_died` | `slot_incomplete` | `synthetic` |
| `hosts` | `not_run_worker_died` | `slot_incomplete` | `synthetic` |

and `process_disposition` is `signaled` with `termination_cause` equal to
`unknown`.

This establishes the flaw at two layers. The step that was in flight when the
host killed the worker and the step the worker never reached are reported
identically. The controller reports the cause of a kill the host itself sent as
unknown, while the prose `error` string one object away states it. The
information exists; the conclusions did not consume it.

### Link 5: the derivations do not read the facts

```sh
grep -n "progress" runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift
grep -n "termination_request\|poll_stop_reason\|exit_requested" controller/src/*.rs
```

Expect the first command to print nothing. The per-step derivation in
`CWorkerOrchestrator.swift`, in the block that sets `attempt.missing_reason`
to `slot_incomplete`, consults only the slot's `completed` flag. Expect the
second command to print exactly one line, a test fixture literal in
`run_flow.rs` that sets `termination_request` to null. The controller's
`synthesize_runner_sandbox_diagnostics` in
[run_flow.rs](src/run_flow.rs) reads `reaped`, `term_signal` and `exit_code`
and emits `unknown` for every signaled disposition.

This establishes the mechanism: not a bug in reading the facts, but derivations
written without them.

### Link 6: the tests pin the discard

```sh
grep -n 'termination_cause, Some("unknown")' controller/src/run_flow.rs
grep -n "termination_cause" tests/suites/witness_contract/check_termination_correlation.py \
  tests/suites/witness_contract/check_pre_apply_failure.py tests/suites/blackbox_e2e/checker_controls.py
grep -n "partial_steps" tests/suites/runner_outcome_runner_timeout/check.py
```

Expect four Rust assertions that `termination_cause` is `unknown` for
signaled, nonzero-exit and unconfirmed dispositions; a Python assertion that a
self-signaled worker yields `unknown`; a pre-apply assertion that
`termination_cause` is in `(None, 'unknown', 'undetermined')`; and the
runner-timeout suite asserting `partial_steps is False`.

This establishes two things. The oracles that must move are enumerable, so the
repair is not open-ended. And the existing timeout seam, `worker_post_apply_hang_ms`,
hangs after every attempt has completed, so no existing suite models
termination with an attempt in flight; the FIFO specimen is a genuinely new
seam.

### Re-running the chain after the repair

Links 1 and 2 are unchanged. Links 3 and 4 must produce the observations under
"Eventual behavior" below. Link 5 must show both derivation sites consuming the
record. Link 6 must show the flipped oracles.

## Eventual behavior

### The rule

Every conclusion field about worker termination or attempt completeness is a
projection of one record, `runner_subprocess.disposition`, computed by one
function in the runner host from witnessed facts only. No downstream layer
re-derives from a subset. When the record cannot determine a value, the
conclusion says so with a value that names the missing witness, never with a
generic unknown. `unknown` survives only where the host genuinely has no
first-person account.

### The record

`runner_subprocess.disposition` is present whenever `runner_subprocess` is.

- `terminated_by`: a closed set. Each value names the witnessed facts it is
  derived from; the derivation is a table, not prose.

  | Value | Witnessed facts |
  | --- | --- |
  | `clean_exit` | reaped, `exit_code == 0`, no `termination_request` |
  | `nonzero_exit` | reaped, `exit_code != 0`, no `termination_request` |
  | `host_sentinel_deadline` | `poll_stop_reason == sentinel_deadline`, `termination_request.rc == 0`, reaped `term_signal == termination_request.signal` |
  | `host_exit_grace` | `poll_stop_reason == done`, exit requested, `termination_request.rc == 0`, reaped signal matches |
  | `unrequested_signal` | reaped with a `term_signal` and no `termination_request` whose signal matches |
  | `unwitnessed` | not reaped, kill request failed, or wait errors broke ownership |

  Other `poll_stop_reason` values (`policy_write_error`, `child_reaped`,
  `wait_error`) map into this set by the same table; extend the table rather
  than the prose if a value has no row.
- `last_progress`: the worker's progress word decoded to names, with the raw
  word retained. `operation` is the `PW_OP_*` name, `phase` is `started` or
  `returned`, `step_id` is the plan's step ID when the operation is per-step,
  otherwise null. An unrecognized code keeps its number and a null name; the
  host still never invents recognition.
- Per-step `attempt.lifecycle`, projected onto each step in `steps[]`:

  | Value | Derivation |
  | --- | --- |
  | `completed` | slot `completed` flag set |
  | `interrupted_in_flight` | not completed; `last_progress` is `attempt`/`started` with this step's index |
  | `not_reached` | not completed; `last_progress` precedes this step's attempt |
  | `returned_unpublished` | not completed; `last_progress` is past this step's attempt. A protocol anomaly, surfaced not hidden |

  The worker releases `completed` inside `run_attempt` before writing the
  returned progress word, so `returned_unpublished` is unreachable through the
  shipped worker and its presence is itself evidence.

Existing spellings stay. `attempt.outcome` keeps `not_run_worker_died` and
`attempt.missing_reason` keeps `slot_incomplete`; both already mean "no
completed result, which may have started". `lifecycle` is the field that says
which. `comparison.limitations` must let a reader tell in-flight from
not-reached without leaving the step object; whether that is a new limitation
entry or the reader consulting `attempt.lifecycle` is an implementation choice.

### Projections

- The controller's `runner_sandbox_diagnostics.termination_cause` is a
  projection of `terminated_by`: `host_sentinel_deadline` and `host_exit_grace`
  pass through; `clean_exit` stays null; `unrequested_signal` and `unwitnessed`
  become `unknown`, which is now exactly the honest meaning: the host has no
  first-person account. `nonzero_exit` is a decision point; the recommended
  value is `worker_exit`, and the pre-apply witness's allowed set must be
  revised so it still forbids sandbox and policy claims without pinning the
  old placeholder.
- The prose `error` string in the reply is generated from the record. The
  substrings the runner-timeout suite matches today (`pw-probe-runner`,
  `sentinel deadline`, `host requested SIGKILL`) either remain or that oracle
  moves in the same change.
- `normalized_outcome` does not change. The classifier keeps its inputs; the
  record adds detail beneath an outcome, never a new outcome.
- Log-correlation fields (`capture_status`, `correlation_status`, `first_deny`,
  `permission_failures_without_record`) do not change and do not feed the
  record. They are inferred, the record is witnessed, and the two stay
  separately labelled.

### The FIFO envelope after the repair

Link 3's fact fields are unchanged. Link 4 prints:

| Step | `outcome` | `missing_reason` | `lifecycle` |
| --- | --- | --- | --- |
| `fifo` | `not_run_worker_died` | `slot_incomplete` | `interrupted_in_flight` |
| `hosts` | `not_run_worker_died` | `slot_incomplete` | `not_reached` |

with `runner_subprocess.disposition` equal to

```json
{ "terminated_by": "host_sentinel_deadline",
  "last_progress": { "operation": "attempt", "phase": "started", "step_id": "fifo", "raw": 152043521 } }
```

and `runner_sandbox_diagnostics.termination_cause` equal to
`host_sentinel_deadline`. `normalized_outcome` is still `runner_timeout`.

### Expected dispositions across seams

These are the acceptance observations for the completeness oracle. Each row is
a real fault at a real boundary; none fakes a result.

| Seam | `terminated_by` | `last_progress` | Step lifecycles | `termination_cause` |
| --- | --- | --- | --- | --- |
| Link 1 control | `clean_exit` | `finished`/`returned` | all `completed` | null |
| Link 2 FIFO | `host_sentinel_deadline` | `attempt`/`started`/`fifo` | `interrupted_in_flight`, `not_reached` | `host_sentinel_deadline` |
| tight `worker_timeout_ms` + `worker_post_apply_hang_ms` | `host_sentinel_deadline` | `attempt`/`returned`/last step | all `completed` | `host_sentinel_deadline` |
| `worker_post_apply_kill_signal: 9` | `unrequested_signal` | `attempt`/`returned`/last step | all `completed` | `unknown` |
| tight `worker_timeout_ms` + `worker_pre_ready_hang_ms` | `host_sentinel_deadline` | an operation before `apply` | all `not_reached` | `host_sentinel_deadline` |
| worker exits nonzero before apply | `nonzero_exit` | the failing operation | all `not_reached` | decision point above |
| spawn failure, no worker | no record; `runner_subprocess` absent | none | absent | null with `process_disposition` `no_worker` |

The FIFO seam is slow at production budgets. Pair the FIFO specimen with a
short `worker_timeout_ms` override to make it fast; that override re-routes
the host-side deadline only, which is exactly the boundary in question, so the
pairing satisfies the seam rules in [runner/AGENTS.md](../runner/AGENTS.md).
This pairing was confirmed against the current build: with
`"_test_overrides": {"worker_timeout_ms": 2000}` the run returns in seconds,
links 3 and 4 print the same observations, and the reply mirrors the override
under `test_overrides`.

### The completeness oracle

A test that, for every seam in the table above, asserts that no conclusion
field reads `unknown`, `slot_incomplete` without a `lifecycle`, or a null
`terminated_by` when the fact fields that determine it are present in the same
reply. This is the guard that stops the next field from being added the way
`termination_cause` was. It asserts determinacy, not specific values; the
specific values are the table.

## Where things live

Fact sources:

- Host kill decision and `termination_request`: `process.terminate()` and the
  grace loop after the poll loop in
  [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift); `poll_stop_reason`
  values are assigned in the same file's poll loop.
- Progress decoding: `decodeWorkerEvidence` in `CWorker.swift`;
  `PWWorkerProgress` in
  [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift).
- Progress publication: `pw_progress` in
  [pw_worker_evidence.h](tools/pw_probe_runner/pw_worker_evidence.h); the
  attempt loop and `run_attempt`'s `completed` release in
  [pw_probe_runner.c](tools/pw_probe_runner/pw_probe_runner.c); operation and
  phase codes in [pw_probe_runner_abi.h](tools/pw_probe_runner/pw_probe_runner_abi.h).
- Reply types: `PWRunnerSubprocess`, `PWRunnerTerminationRequest`,
  `PWWorkerEvidence` in `PWRunnerAPI.swift`.

Derivation sites that become projections:

- `buildAttemptResult` and the `missing_reason` block in
  [CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift);
  `computeComparison` in the same file for the limitations entry.
- `synthesize_runner_sandbox_diagnostics` and `RunnerSandboxDiagnostics` in
  [run_flow.rs](src/run_flow.rs).

Oracles that pin the current behavior and must move:

- `run_flow.rs` unit tests asserting `termination_cause == Some("unknown")`.
- `tests/suites/witness_contract/check_termination_correlation.py` (self-signal
  yields `unknown`; under the record that row is `unrequested_signal`, which
  still projects to `unknown`, so this one may hold as written).
- `tests/suites/witness_contract/check_pre_apply_failure.py` (allowed set for
  `termination_cause`).
- `tests/suites/blackbox_e2e/checker_controls.py` (synthesizes
  `runner_sandbox_diagnostics`).
- `tests/suites/runner_outcome_runner_timeout/check.py` (error prose
  substrings; `partial_steps`).
- `tests/fixtures/contract/response_shape.json`, compared by
  `ContractVersionTests` in the `runner_unit` suite; the
  `reply.runner_subprocess` block gains `disposition`.

Documents that describe the fields:

- [tests/FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md):
  the `not_run_worker_died` paragraph, the `termination_cause="unknown"`
  sentence, and the attempts paragraph under acceptance observations.
- [docs/PolicyWitness.md](../docs/PolicyWitness.md): the step-channels
  paragraph and the denial-log correlation section.
- [controller/README.md](README.md): the `runner_sandbox_diagnostics` bullet.
- [runner/README.md](../runner/README.md): the `not_run_worker_died` bullet and
  the `worker_evidence` paragraph.

## Versioning

Apply [docs/CONTRACT.md](../docs/CONTRACT.md) as written. Adding
`disposition` and `attempt.lifecycle` never bumps; an absent field means
unknown. `termination_cause` changes meaning for readers that matched on
`unknown`, so the controller envelope bumps; edit
[docs/contract.json](../docs/contract.json), run
`python3 docs/generate_contract.py`, and move only the tests for this change.
The worker ABI does not change: every input to the record already crosses the
shared-memory boundary today. Do not add per-slot lifecycle state to the ABI
in this change; the global progress word plus per-slot `completed` determines
every lifecycle value.

## Order of work

1. Add the mid-attempt seam: a FIFO specimen paired with a short
   `worker_timeout_ms`, registered the way the seam rules require. Confirm it
   reproduces link 4's observation against the unchanged build. This is the
   oracle everything else is measured against.
2. Host: one function that takes the full lifecycle fact set and returns the
   record. Attach it to the reply. Project `attempt.lifecycle`. Generate the
   `error` prose from it. Update the golden reply shape.
3. Controller: consume `terminated_by` for `termination_cause`. Flip the Rust
   oracles. Bump the controller envelope.
4. Documents and contract manifest.
5. The completeness oracle over every seam in the table.
6. Re-run the STR chain and record the link 3 and 4 observations in the
   change.

Verification for the whole change follows the limits recipe:
`cargo test --manifest-path controller/Cargo.toml`, then `tests/run.sh --suite
source_drift --suite runner_unit --suite runner_outcome_runner_timeout --suite
witness_contract --suite blackbox_e2e` against a normal signed build, then the
default battery.

## Out of scope, and where it plugs in

- A per-attempt deadline for in-process attempts (the flaw the FIFO exposes at
  the worker layer). It is a separate change with its own limit entry. When it
  lands, a per-step `deadline_fired` fact feeds `lifecycle` as one more value,
  through the same function; it must not grow its own path to the top.
- Any causal claim from log correlation. `first_deny` stays a reference, not a
  cause, until a separate evidence contract exists.
- Any change to `normalized_outcome` or to the comparison verdicts.
