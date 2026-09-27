# Disposition record plan

This plan addresses conclusions that lose evidence, overstate evidence, or
disagree about the same evidence. The motivating failure is a witnessed fact
published in the envelope but omitted from a downstream derivation: the reply
says "unknown" about something it can establish. Repairing that loss must not
introduce the opposite error, a confident answer unsupported by the available
observations.

The proposed repair is one canonical worker disposition record, resolved once
in the runner host and carried in the reply. It preserves independent lifecycle
observations, their validity and scope, supported claims, and specific reasons
for unresolved or conflicting claims. Worker lifecycle conclusions project
from that account. An independent acceptance oracle checks required claims,
forbidden claims, and the handling of uncertainty and inconsistency against
the underlying observations, without calling the production resolver.

This remains a plan. First finish planning the app-code actions and the
decisions they depend on; the eventual execution order is **contract → tests →
app code**. The reproduction chain establishes the existing flaw. The sections
below specify the intended guarantees, the implementation boundaries, and the
red tests, each written against observations from the current build. The exact
wire shape is still to be fixed in the contract stage; this document does not
claim that the new oracle exists.

Read [AGENTS.md → Core ideas](../AGENTS.md#core-ideas) first. "No dishonest
attribution" is the principle this plan serves, not one it relaxes. The host
can record its deadline, termination request and return, and reaped status.
It can also retain a worker publication that attempt 0 started without a
completed result. These observations supply neither a sandbox cause nor the
exact instruction at which execution stopped.

## Vocabulary

- **Fact field**: a value written by the layer that observed it, without
  interpretation. `runner_subprocess.termination_request`, `poll_stop_reason`,
  `term_signal`, `worker_evidence.progress`, and each slot's `completed` flag
  are fact fields.
- **Conclusion field**: a value derived from fact fields for a reader.
  `runner_sandbox_diagnostics.termination_cause`, `attempt.outcome`,
  `attempt.missing_reason`, and `comparison.limitations` are conclusion fields.
- **Witnessed**: an observation with an identified owner. A host action is a
  host observation; progress and slot results are worker publications acquired
  by the host. Reading a publication does not expand what that publication
  proves. **Inferred**: matched from an outside source, such as a unified-log
  line with the worker's PID. Inference keeps its own separately labelled fields
  and does not feed this record.
- **Claim**: an answer to a particular lifecycle question, with declared
  sufficient witnesses and disqualifying conditions. Unrelated claims can have
  different certainty in the same run.
- **Uncertainty**: available, valid observations leave a particular question
  unresolved. Missing, unrecognized, or unusable observations need distinct
  reasons; they do not establish false or a contradiction.
- **Inconsistency**: observations conflict under a stated protocol rule after
  their identity, validity, and observation scope have been established. It
  identifies a conflict in the account, not automatically a defect in the
  worker or a policy cause.
- **Observation scope**: the worker/slot identity and collection conditions
  under which observations can be related. A stable terminal snapshot and
  separate reads while a child may still run support different claims.
- **Projection**: a registered conclusion computed as a total function of the
  canonical record, with no additional lifecycle observations or re-derivation.
  The record must contain, or immutably include, every input that projection
  requires. The projection inventory below bounds this promise.
- **Seam**: a `_test_overrides` key or a specimen that drives a real fault at
  a real boundary. The rules for seams are in
  [runner/AGENTS.md](../runner/AGENTS.md).

## STR chain

Each link has a command, the observation it must produce, what that
establishes, and what to do if it does not. Do not skip links: a later link
only means something if the earlier ones held. All runs use `--no-log-capture`
to remove log-archive collection cost; startup, validator collection, polling
and cleanup can still contribute to elapsed time.

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

This establishes the relevant observations: the host's deadline fired, it
requested SIGKILL and the request succeeded, the reaped signal matches, and
the last progress word publishes attempt index 0's started boundary without a
later returned publication or completed slot. It does not establish the exact
instruction at termination or absence of an operation effect. Operation 9 is
`PW_OP_ATTEMPT` and phase 1 is
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

This establishes the flaw at two layers. The step with a published started
boundary and no result and the later step not reached in this terminal
snapshot are reported identically. The controller's generic unknown omits
the known host cleanup sequence, while the prose `error` string one object
away describes it. The information exists; the conclusions did not consume it.

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

### Link 6: the tests pin the current conclusions

```sh
grep -nF 'termination_cause, Some("unknown")' controller/src/run_flow.rs
grep -n "termination_cause" tests/suites/witness_contract/check_termination_correlation.py \
  tests/suites/witness_contract/check_pre_apply_failure.py tests/suites/blackbox_e2e/checker_controls.py
grep -n "partial_steps" tests/suites/runner_outcome_runner_timeout/check.py
```

Expect four Rust assertions that `termination_cause` is `unknown` for
signaled, nonzero-exit and unconfirmed dispositions; a Python assertion that a
self-signaled worker yields `unknown`; a pre-apply assertion that
`termination_cause` is in `(None, 'unknown', 'undetermined')`; and the
runner-timeout suite asserting `partial_steps is False`.

This establishes two things. The oracles that depend on the current
conclusions are enumerable; which of them move and which stay is decided under
"Where things live". And the existing hang seam fires after all attempts, so no
existing suite models the FIFO's started-without-result boundary.

### Re-running the chain after the repair

Links 1 through 3 are unchanged. Link 4, read together with the lifecycle
reasons chosen in the contract stage, must satisfy the acceptance observations
below. Link 5 must show both derivation sites consuming the canonical account.
Link 6 must show the oracle changes listed under "Where things live".

## Eventual behavior

### The rule and its scope

For each registered lifecycle conclusion, consume all relevant valid
observations, retain the basis for the answer, and state only what that basis
establishes. Resolve once in the runner host; project the result downstream.
The guarantees are:

1. **Completeness**: sufficient witnesses require the supported claim; a
   blanket unknown must not discard it.
2. **Soundness**: a claim without sufficient witnesses is forbidden. A
   successful kill request is not a reap, a started publication is not an
   operation result, and a completed slot is not proof of successful effect.
3. **Consistency**: projections of the same claim agree. Independent facts,
   such as deadline expiry and eventual clean exit, can coexist.
4. **Locality**: uncertainty or a conflict affects the claims that depend on
   it, not every observation in the run.
5. **Preservation**: later failures and reply forwarding retain earlier
   evidence and its limits. Explicit minimal reporting failure remains the
   existing exception to evidence retention.

The first implementation owns worker lifecycle and attempt-publication
conclusions. It also preserves their account through reply encoding, controller
forwarding, and supported legacy decoding. Validator and exec-child evidence
remain independently owned; the extension rules below apply when their
conclusions are brought under this contract. There is no promise that every
field in the envelope derives from one worker record.

### The canonical record must be sufficient

New worker replies carry `runner_subprocess.disposition` whenever they carry
`runner_subprocess`. No worker means no invented worker record. Absence in an
older reply means unavailable under the compatibility rules, not a negative
observation.

The record is an account of observations and claims, not just an enum and a
progress word. The following are required dimensions; their exact Swift and
JSON representation is a contract-stage decision:

| Dimension | Required content and limits |
| --- | --- |
| Polling and cleanup | Why collection stopped, exit-request publication, cleanup trigger, termination request/result, wait observations. Deadline, exhausted exit grace, and cleanup after an error remain distinct. |
| Process status | Successful-reap witness and observed exit or signal; unconfirmed status has a specific reason. Intervention does not replace status. |
| Worker publications | Application/completion, decoded and raw progress, relevant failure publications and publication validity. Ownership stays with the worker even though the host reads them. |
| Per-step evidence | Submitted step identity/order and attempt support, slot presence and completion publication, and any published result fields needed by a registered projection. A completed no-op for an unsupported request is not a completed requested operation. |
| Observation scope | Identity association and the collection basis that permits temporal relationships, including whether the worker could still advance between reads. |
| Claims and issues | Supported answers with their basis, unresolved questions with reasons, and conflicts with the rule and observations involved. |

The canonical resolver's input must contain or immutably include all these
dependencies. Existing raw fact fields remain authoritative observations;
reuse them rather than creating separately mutable copies. A basis reference
must resolve within the same retained reply, including a degraded reply.
Projections receive the resolved record, not a record plus opportunistic
lifecycle inputs.

A single exclusive `terminated_by` value is insufficient as the canonical
representation. It would lose a deadline followed by voluntary exit, a failed
kill followed by a confirmed exit, or an earlier worker failure followed by
cleanup. If a compact summary is retained, it is a registered projection of
the independent dimensions and never replaces them.

Progress retains its raw word, numeric operation/phase/index, optional known
names, and validated association to a step. Unknown codes remain transportable.
Parameter indices are not step indices. Temporal order comes from the worker
protocol, not numeric opcode order: proceed is operation 11 but precedes
attempt operation 9.

### Uncertainty, inconsistency, and the observation boundary

Resolve each question separately. Known termination-request facts can coexist
with uncertain final status and known completed results. Absence, observed
false, unrecognized values, malformed observations, and conflicting usable
observations are distinct states. Unsupported or inapplicable questions are
also explicit; they are not missing evidence.

| Observations | Required interpretation |
| --- | --- |
| Successful host kill request, no successful reap | Request/result known; final status unresolved because reaping is unconfirmed. |
| Failed kill, followed by a valid reap with exit 0 | Consistent failed intervention and clean exit. Preserve both. |
| A single final reap represented as both exit 0 and signal 9 | Conflicting status representation; retain the observations and identify the status rule violated. |
| Slot read incomplete, later progress read beyond it, child possibly still running | The reads can describe different moments. A publication-protocol violation is not established. |
| Valid stable terminal snapshot, incomplete slot, valid progress beyond that slot | Conflict with the specified completion-before-return/next-attempt publication rule. Do not invent a result or automatically blame the worker. |
| Unknown progress code, valid completed slot | Progress-dependent questions may be unresolved; the completed result remains known. |
| Missing progress and incomplete slot | Attempt reachability unresolved; absence does not establish that the attempt never began. |

For a conflict, first establish that the observations are valid and concern the
same worker/slot and an observation scope where the rule applies. Otherwise
identify the missing association or collection witness. Reporting an
inconsistency says the account cannot satisfy that rule; it does not identify
whether producer, collection, decoding, or an incomplete model caused it.

The current host reads completion flags before decoding progress. If cleanup
fails and the worker can still run, those reads are not one atomic snapshot.
The implementation must record enough collection context to limit conclusions,
or establish a justified observation protocol before making stronger ones.
Reaping followed by all relevant reads can establish a stable worker snapshot;
the mere fact that cleanup was attempted cannot. No progress value permits
reading an unpublished slot payload.

The lifecycle wording must carry the same limits. A started boundary with no
published result must not imply that a particular syscall was still executing
at termination, and an unreaped worker must not be described as definitively
interrupted. A publication conflict is established only by the stable,
same-slot combination in the table above (rule D5), never by the bare
combination of an incomplete slot and later progress.

### Claim requirements and projection inventory

Each rule needs minimal sufficient witness sets, disqualifying conditions,
required and forbidden claims, and the result of missing or conflicting
witnesses. Alternative sufficient bases must be explicit. These seed rules
bound the contract; the contract stage completes their tables before tests or
app implementation.

| Rule | Claim requirement | Forbidden shortcut |
| --- | --- | --- |
| D1: process status | Successful reap plus one valid status representation establishes exit or signal, independent of kill success. | Decode unconfirmed wait storage; require a successful kill to retain an independently reaped exit. |
| D2: host action | Direct host observation establishes deadline, exit request, cleanup trigger, and kill return separately. | Infer exhausted grace from `done` plus a kill; a wait error may have ended grace early. |
| D3: started/publication | Valid started progress associated with this step establishes a started boundary; supported attempt plus valid completed slot establishes a published result. | Treat association alone as evidence of execution, started as a native result, completed as successful effect, or an unsupported no-op as the requested operation. |
| D4: not reached | Valid known protocol position before a step, with stable terminal scope and no conflicting completion evidence, establishes that the worker never reached that attempt boundary. | Infer not-reached from missing progress, an unfamiliar opcode, an absent slot, or a live snapshot. |
| D5: publication conflict | Valid association, stable terminal scope, and mutually incompatible progress/completion publications establish a scoped conflict. | Declare a protocol violation from reads that can describe different moments. |
| D6: preservation | Independent earlier publications, stop reasons, interventions, and final status survive summary selection and later faults. | Replace a deadline with clean exit, or a worker failure/result with cleanup failure. |
| D7: projection | Each registered output carries the same claim and limits as its canonical source. | Derive a competing lifecycle answer from a convenient subset or error prose. |
| D8: transport | Encoding, forwarding, degradation and legacy decoding preserve evidence or explicitly identify its absence under the applicable contract. | Interpret an omitted field as observed false; let a minimal reply claim evidence retention. |

Register each lifecycle-derived field, its source claim, dependencies, absence
semantics, owner and compatibility behavior. The initial inventory is:

| Projection | Responsibility |
| --- | --- |
| `runner_sandbox_diagnostics.process_disposition` and `termination_cause` | Project independent final status and bounded host-action detail; preserve no-worker and legacy absence semantics. |
| `runner_subprocess.partial_steps` | Project slot publication completeness without asserting that an operation never began. |
| `attempt.lifecycle` and its reasons/issues | Distinguish supported completed result, started without result, proven not-reached, unsupported/inapplicable, and unresolved/conflicting questions. Exact wire spellings remain open. |
| Lifecycle-related `attempt.outcome`, `missing_reason`, `result_source`, and `comparison.limitations` | Agree with the same step account. Completed attempt outcome mapping retains its native-result inputs; it is not replaced by lifecycle classification. |
| Worker-lifecycle clauses of `error` | Render the canonical facts and limits while retaining independently owned worker/validator/setup diagnostics and summary precedence. |

Existing spellings `not_run_worker_died` and `slot_incomplete` remain
compatibility summaries for no completed supported result, which may have
started. The new step detail must make the distinction available within the
step object and distinguish uncertainty from conflict. Do not redefine these
old spellings as proof of death or non-execution.

For the FIFO case, `termination_cause: host_sentinel_deadline` is the intended
projection of observed deadline, host termination request, and matching reaped
signal. Its contract describes this witnessed host cleanup sequence, not
exclusive signal-sender attribution or a sandbox cause. The remaining cause
mappings are on the decision list. Unknown external signal cause can coexist
with fully known signal disposition.

A legacy `unknown` or null may remain in a compatibility projection where its
contract requires it; the new account names the unresolved question and reason.
There is no global ban on unknown values and no global confidence enum that
erases usable evidence.

`normalized_outcome` values and their precedence do not change. The existing
classifier may retain its inputs; consistency controls check it against the
account without requiring it to become a disposition projection. A deadline
followed by voluntary exit remains `runner_timeout`; an earlier published
worker failure still takes precedence over later cleanup. Only lifecycle
clauses of the prose error are generated from this record, not every error
from every observer.

Additional step limitations must not silently change agreement, order, drift,
or sandbox attribution.

### Acceptance observations across boundaries

These are semantic requirements and existing ways to reach observations; the
red-test specifications below turn them into tests. Exact lifecycle/reason
strings and cause mappings are finalized in the contract stage.

| Scenario | Required account |
| --- | --- |
| Link 1 control | Known clean exit, completed supported result, no cleanup termination, ordinary successful summary. |
| Link 2 FIFO | Deadline; successful host SIGKILL request; reaped signal 9; FIFO boundary started with no published result; following attempt proven not reached; `runner_timeout`; `termination_cause: host_sentinel_deadline`. |
| Completed prefix, then FIFO, then another file | Preserve the completed prefix independently of the two distinct missing-result accounts. |
| Deadline during a long post-apply hang | All completed results survive the deadline and host termination; last progress need not name an incomplete attempt. |
| Deadline followed by voluntary exit during grace | Deadline and exit 0 both survive; no termination request is invented; completed results and `runner_timeout` coexist. |
| Post-apply self-signal | Completed results and reaped signal survive; no host termination request or sandbox cause is invented. Host knowledge does not identify the signal's sender. |
| Pre-apply deadline with known valid progress | Deadline/cleanup and no reached attempts survive, subject to the same scope and association rules. |
| Nonzero exit before apply | Exit is known when reaped; operation failure and not-reached claims require their own publications and scope. Exit code alone supplies neither. |
| Failure publication followed by deadline or cleanup fault | The failure and later independent observations all survive; existing summary precedence holds. |
| Failed kill/reap or host wait error | Preserve request/result, wait errors and every valid result; final status and reachability remain unresolved where their witnesses are absent. |
| No worker spawned | No worker disposition object. Any synthesized requested-step results retain no-worker/slot-unavailable reasons, not worker execution claims. |

The production FIFO budget is slow. Pair the specimen with
`"_test_overrides": {"worker_timeout_ms": 2000}` for a short run; assert the
echoed override as well as the failure observations. This changes the host
deadline, not the worker result; against the current build the pairing returns
in seconds with links 3 and 4 unchanged and the override mirrored under
`test_overrides`. A completed prefix makes one run expose all three relevant
publication situations.

The grace-exit boundary is reachable with an allow-default file specimen and
`worker_timeout_ms: 300`, `worker_post_apply_hang_ms: 800`; test A4 records
the observed values. Timing is equipment, not the oracle. Existing driver
controls also exercise late completion during grace with an explicit grace
budget.

## The independent acceptance oracle

### What it checks

The oracle checks the claim requirements against source observations. It checks
the resulting record and each registered projection, rather than merely
rejecting `unknown` when a convenient field is present. For every claim it
must distinguish:

- **Required**: one of the declared sufficient witness sets is present and
  valid, with no relevant disqualifying condition.
- **Forbidden**: the asserted answer lacks a sufficient basis or violates a
  declared constraint.
- **Unresolved**: the named missing, unrecognized, or unusable witness explains
  why that question cannot be answered.
- **Conflicting**: identified observations violate a named rule in a scope
  where that rule applies. Unaffected claims retain their own bases.

Applicability is explicit so unsupported requests are not forced into a
required/unknown execution claim. Unknown external cause must not invalidate a
known exit status; missing progress must not invalidate a completed slot.

### Independence and finite scope

Author a small acceptance table from the public claim rules, separately from
the production resolver. Hand-reviewed examples anchor each rule. The checker
reads the original observations, validates supporting evidence and constraints,
and checks the output. It must not call the production resolver/projections to
produce expected values, trust producer-supplied basis labels without checking
them, or copy its branch ladder into a second language.

Preservation checks also compare supplied or independently observed inputs with
the serialized account. Checking only the final envelope cannot detect a fact
discarded before that envelope was assembled. Keep interpretation, production,
and transport claims separate so the oracle's reach is explicit.

Use exhaustive combinations over a declared finite abstraction, with raw
numeric boundaries and unfamiliar values sampled separately. Candidate axes
include:

| Axis | Distinctions the model must retain |
| --- | --- |
| Reaping/status | Missing or unconfirmed; valid exit; valid signal; conflicting representation. |
| Intervention/stop | No request; request succeeded/failed; deadline, done, wait/transfer error; known or unavailable cleanup trigger. |
| Progress | Absent; known before/current/after a step; unknown operation/phase; invalid or mismatched index. |
| Slot/request | Absent/incomplete/completed; supported/unsupported; valid/ambiguous association. |
| Collection scope | Stable terminal observations; potentially advancing worker; unavailable scope. |
| Other publications | Absent/valid/invalid worker failure or completion, including coexistence with cleanup observations. |

The contract-stage model must state which combinations are coherent, which
are contradictory, which are merely unresolved, and which are inapplicable.
Do not discard contradictory combinations from the test domain: they exercise
conflict reporting. Model the current serial attempt order and cover empty
plans, first/last steps, and out-of-range associations. Explain why any
equivalence-class reduction preserves the claims under test; do not call a
sample exhaustive over a larger domain.

Constructed combinations establish interpretation, not live reachability or a
kernel cause. Real boundary controls establish observation production, and
round-trip/CLI controls establish transport. The attainable guarantee is
exhaustive interpretation within the declared model plus exercised production
and transport paths, not proof that every real execution is modeled. Unmodeled
observations retain an explicit unresolved path.

### Properties beyond individual rows

1. Removing every sufficient basis for a claim removes that certainty and
   names what is missing. Removing one basis must not erase a claim supported
   by another.
2. Adding compatible observations preserves independently established facts.
   Contradictory additions surface a conflict; there is no unconditional rule
   that confidence can only increase.
3. Later cleanup faults do not erase earlier valid publications or stop
   reasons. Uncertainty and conflicts remain local to dependent claims.
4. Changing unrelated log records, diagnostic wording, or irrelevant values
   does not alter lifecycle claims.
5. Projections and transport satisfy D7 and D8. Degradation may withhold
   comparisons under the existing reply contract while retaining the lifecycle
   account; it must not leave a surviving contradictory claim.
6. An independent negative control must demonstrate that the checker rejects
   each kind of unsupported, contradictory, or discarded claim it claims to
   detect. A checker that accepts every output cannot pass its own controls.

## App-code action plan to finish first

These actions describe implementation boundaries and dependencies.

1. **Collection and provenance — CWorker.swift.** Audit every poll stop,
   cleanup exit, and final read. Preserve independent stop/intervention/status
   facts. Record a direct cleanup-trigger witness if a public claim needs to
   distinguish grace exhaustion from wait-error cleanup. Decide how the host
   establishes stable terminal scope and how it reports potentially advancing
   reads. Keep completed-slot acquire gates; do not infer coherence from kill
   success.
2. **Canonical input and resolver — PWRunnerAPI.swift and
   CWorkerOrchestrator.swift.** Define the evidence dependencies, per-question
   results and issue representation. Choose one inspectable resolver over
   immutable inputs, with explicit rule tables and total handling of missing,
   unfamiliar, malformed and conflicting observations. Include step support,
   identity, slot publication and relevant failure evidence; do not resolve
   separately in the subprocess and step builders.
3. **Runner projections — CWorkerOrchestrator.swift.** Resolve once after
   collection. Project subprocess detail, partial steps, lifecycle-related
   attempt fields, comparison limitations and lifecycle error clauses from the
   account. Keep completed native-result mapping and independently owned
   diagnostics intact. Preserve existing summary precedence and comparison
   verdicts.
4. **Controller projections — run_flow.rs.** Consume the account for process
   disposition and bounded termination detail. Specify the conservative
   behavior for absent older records and unknown future values; do not
   reconstruct the new account from a subset or parse prose. Keep log
   correlation independent.
5. **Encoding and consumers — PWRunnerAPI.swift, reply boundary, and existing
   readers.** Preserve raw evidence and structured issues in normal and
   evidence-preserving degraded replies. Distinguish a representable observed
   conflict from an invalid assembled claim that encoding must reject. Avoid a
   rejection/degradation loop that loses the very conflict being reported.
   Keep minimal reporting failure and old-response absence semantics explicit.
6. **Integration inventory.** Map each action to its contract clauses,
   projection entries, shape fixture and red tests. Update the
   relevant docs and version decisions through the contract stage.

### Decisions to settle in planning and contract work

- Exact record/claim/issue wire shape, immutable basis references, lifecycle
  spellings, and consumer access to step-local reasons.
- Collection scope evidence and the cleanup-trigger facts required by the
  selected public claims; which cases must remain unresolved.
- Complete termination-cause mappings, including nonzero exit, failed cleanup,
  wait errors, and deadline followed by voluntary exit. A null cause must not
  remove a known deadline from the account or diagnostic.
- Which dependencies each projection owns; how lifecycle prose composes with
  other diagnostics without taking over their causal claims.
- Finite model and oracle inventory enforcement, legacy/unknown-value behavior,
  and required version changes.

These decisions may refine the app-code action plan. They must not weaken any
of the five guarantees to accommodate an implementation shortcut.

## Red-test specifications

This section specifies the tests the contract stage resolves and the test
stage implements. It is written against the current build: every live
observation quoted here was produced by the shipped app, and every "red today"
statement names the field that is wrong now. Exact lifecycle spellings remain
open, so each specification says how it stays valid under any spelling the
contract chooses, or says that it is blocked on the wire shape.

### Conventions

**Two waves.** Wave 1 reds assert on fields that exist today and are wrong
today, or on inputs the controller can already be handed as JSON. They go red
on the unchanged build for a behavioral reason. Wave 2 reds need the resolver
API or a new reply field; until the contract stage fixes the shape they are
specified but not runnable, and a missing key or a compile failure is not their
red. Do not promote a wave 2 test by asserting on a placeholder spelling.

**Four input classes, four homes.** Live boundaries run the CLI through
`RunCapture` in a `witness_contract` case. Driver fault controls run the
production host driver against the `worker_lifecycle` fixture in `runner_unit`.
Constructed interpretation cases build `CWorkerOutput` values, in the style of
`workerOut` in `HostOutcomeClassifierTests`, and feed the resolver or the step
builder directly. Transport fixtures are constructed JSON handed to the
controller's `synthesize_runner_sandbox_diagnostics`, to `recover_evidence`, or
to the reply encoder. A failure in one class says nothing about another.

**Spelling-agnostic assertions.** Where a new field's name is open, the
assertion is phrased over the lifecycle view of a step: the `attempt` object
with every key of the response-9 golden shape removed except `outcome`,
`missing_reason` and `result_source`. Two steps are distinguishable when their
lifecycle views differ. Today the view is those three keys, so two incomplete
steps are never distinguishable. Tests that name a cause value reference one
constant in `tests/lib` so a rename touches one place.

**Per-test record.** Each specification below carries: the rule protected and
the regression it detects; the input class, source observations and scope; the
required, forbidden, unresolved or conflicting claims and the evidence that
must stay unaffected; the red assertion and the layer it fails at; the
counterexample that must keep passing; and cleanup, timing and registration.

**Seam rules.** No new `_test_overrides` key is needed. The FIFO specimen is a
real blocking target, and `worker_timeout_ms` re-routes only the host
deadline. Tests that need a publication pattern the shipped worker cannot
produce use a new `worker_lifecycle` fixture mode, which publishes with the
real ABI protocol and never applies a sandbox.

### Area A: live loss of known facts

Home: one new `witness_contract` case, `worker_attempt_in_flight_at_deadline`,
with a wrapper shell script in the existing style and a Python check that runs
three specimens through `RunCapture` with `--no-log-capture` and
`--timeout-ms 20000`. Each specimen uses `(version 1) (allow default)`, a FIFO
created with `mkfifo` inside a `TemporaryDirectory` under `/private/tmp`, and
`"_test_overrides": {"worker_timeout_ms": 2000}`. The test never opens the FIFO.
Before removing the directory it asserts `runner_subprocess.reaped` is true, so
no worker outlives the test. Expected wall time per specimen is about four
seconds. Register the case in `tests/catalog.json`, add a section to the suite
README beside "Completed observations after a worker timeout", and extend the
`witness_contract` row of the suite coverage table.

**A1. Host cleanup after a deadline is reported as a cause (wave 1).**
Protects D2, D7 and completeness; detects the controller discarding the host's
own termination record. Input: the two-step FIFO specimen from link 2. Observed
today: `poll_stop_reason` `sentinel_deadline`, `termination_request`
`{"rc": 0, "signal": 9}`, `term_signal` 9, `reaped` true, `process_disposition`
`signaled`, `termination_cause` `unknown`. Required: `termination_cause` equals
the contract constant for host cleanup after a sentinel deadline. Forbidden:
`unknown`, and any value that attributes the signal to the sandbox. Unaffected:
`normalized_outcome` stays `runner_timeout`; the error prose keeps its deadline
and SIGKILL clauses. Red today at the controller envelope: the value is
`unknown`. Must keep passing: `worker_termination_and_log_correlation`, where
the self-signaled worker has `term_signal` 9 and no `termination_request` and
`termination_cause` stays `unknown`.

**A2. The in-flight step and the unreached step are distinguishable (wave 1).**
Protects D3, D4 and locality; detects two different missing-result accounts
collapsing into one. Input: the same run as A1. Observed today: progress
`{"operation": 9, "phase": 1, "index": 0}`, both steps `not_run_worker_died`,
`slot_incomplete`, `synthetic`, and `attempt:slot_incomplete` in both
limitation lists. Required: the lifecycle views of `fifo` and `hosts` differ;
both keep `not_run_worker_died` and `slot_incomplete`; each step's comparison
lets a reader tell in-flight from not-reached without leaving the step object.
Forbidden: any claim that a syscall was executing at termination, and any
result for `hosts`. Red today at the runner step builder, visible in the
envelope: the two views are identical. Must keep passing: the pre-apply witness
and `worker_sparse_failure`, which pin `slot_incomplete` and
`not_run_worker_died` for incomplete slots.

**A3. A completed prefix survives termination with an attempt in flight
(wave 1, preservation plus red).** Protects D6 and locality; detects the record
or its projections erasing completed results. Input: a three-step plan,
`/etc/hosts`, the FIFO, `/etc/hosts`. Observed today: step `first` has
`outcome` `ok`, `result_source` `worker`, `rc` 0 and conclusion `agreement`;
progress index is 1; `partial_steps` is true; the two later steps are identical
`slot_incomplete`. Required: `first` keeps every one of those values after the
repair; `fifo` and `after` are distinguishable as in A2. The preservation half
passes today and is listed as such. The red half is A2's assertion at index 1.
Cleanup and timing as for the case.

**A4. A deadline followed by voluntary exit is not reported as a plain clean
exit (wave 1).** Protects D2, D6 and the decision-list rule that a null cause
must not remove a known deadline. Input: a single `/etc/hosts` step with
`"_test_overrides": {"worker_timeout_ms": 300, "worker_post_apply_hang_ms": 800}`.
Observed today, in under a second: `poll_stop_reason` `sentinel_deadline`,
`exit_requested` true, `termination_request` absent, `exit_code` 0, `reaped`
true, `done_observed` true, `partial_steps` false, progress
`{"operation": 10, "phase": 2}`, `normalized_outcome` `runner_timeout`, and the
controller diagnostics `process_disposition` `clean_exit` with
`termination_cause` null. Required: the diagnostics object carries the
deadline observation in a registered field; `process_disposition` remains a
true statement about final status; no termination request is invented; the
completed step and `runner_timeout` survive. Forbidden: any kill or signal
claim. Red today at the controller envelope: nothing in
`runner_sandbox_diagnostics` mentions the stop reason. The assertion is that a
registered field of that object equals `sentinel_deadline`; the field name is
the contract's. Timing is equipment: if the worker reaches `done` before the
deadline the run is `ok` and the test must report a setup failure, not a
behavioral result. Must keep passing: link 1's control, where the diagnostics
carry no deadline.

### Area B: missing, unfamiliar, malformed and conflicting evidence

Home: a new `runner_unit` file, `DispositionResolverTests.swift`, registered in
the `main.swift` registry per [runner/AGENTS.md](../runner/AGENTS.md), plus
Rust tests in the `run_flow.rs` test module. Constructed cases extend the
`workerOut` builder with slots and a `workerEvidence` value carrying a progress
word. Every case states which questions it leaves unresolved and asserts the
unaffected claims explicitly.

**B1. A conflicting status representation is not silently resolved (wave 1,
Rust).** Protects D1; detects the controller picking the first of two
incompatible status fields. Input: runner JSON from the `worker` helper with
`reaped` true, `exit_code` 0 and `term_signal` 9 together. Today the
controller reports `signaled` because it checks the signal first. Required: a
conflict indication naming the status rule. Forbidden: unqualified `signaled`
or `clean_exit`, and any `termination_cause` other than the conflict's own
value. Unaffected: `worker_pid`, capture and correlation fields. Red today at
`synthesize_runner_sandbox_diagnostics`. Must keep passing:
`unconfirmed_reap_does_not_manufacture_clean_disposition_from_status_storage`.

**B2. Missing progress leaves reachability unresolved (wave 2).** Protects D4
and the uncertainty table's last row. Input: constructed output with an
incomplete slot and `workerEvidence` nil, then with progress nil. Required: the
step's lifecycle question is unresolved with a reason naming missing progress;
`missing_reason` stays `slot_incomplete`. Forbidden: not-reached and
started-boundary claims. Blocked on the reason representation.

**B3. An unrecognized progress operation does not disturb a completed result
(wave 2).** Protects D3, D6 and locality. Input: two slots, both completed,
progress operation 200 phase 1 index 0. Required: both steps keep `outcome`
`ok` and `result_source` `worker`; progress-dependent questions are unresolved
with a reason naming the unrecognized code; the raw word survives. Forbidden:
not-reached for any step, and any reclassification of `normalized_outcome`. The
first requirement passes today through the existing step builder and is a
preservation control; the reason is the red.

**B4. A successful kill request without a reap leaves status unresolved
(wave 2, reason only).** Protects D1 and D2. Input: `reaped` false,
`termination_request` `{"rc": 0, "signal": 9}`, no status. Required: the
request and its result are claimed; final status is unresolved because reaping
is unconfirmed. Forbidden: `signaled`. The forbidden half is already covered by
the Rust test named under B1 and by "successful kill followed by failed reap
does not decode wait storage" in `CWorkerLifecycleTests`; both are preservation
controls. The named reason is the red.

**B5. An out-of-range progress index invalidates association, not the run
(wave 2).** Protects D3 and D4. Input: two slots, progress attempt started with
index 2, then the largest index the word's 20-bit item field can carry.
Required: association
invalid with a reason; every step's reachability unresolved; completed slots,
if any, keep their results. Forbidden: in-flight or not-reached claims for any
step. Include the empty plan with an attempt progress word as a row.

**B6. A completed unsupported slot is not a completed requested operation
(wave 2).** Protects D3's last forbidden shortcut. Input: a step whose attempt
kind the worker does not implement, so the worker writes `ENOSYS` and completes
the slot. Required: the step is inapplicable or unsupported in the lifecycle
account and `missing_reason` stays `attempt_not_supported`. Forbidden: a
completed-result claim. The `missing_reason` half passes today.

### Area C: collection scope and publication boundaries

Home: `runner_unit`, using the `worker_lifecycle` fixture through helpers in
the style of `evidenceFixture`, plus constructed cases in
`DispositionResolverTests.swift`. The fixture's `started_attempt` mode publishes
applied, progress attempt started index 0 and a poisoned slot, then exits 0 on
`exit_requested` without completing. Its `late_publication` mode does the same
and then completes the slot, publishes attempt returned and `done` during
grace. Both are real publications under the real protocol.

**C1. Late publication during grace is a completed result with a retained
deadline (preservation, wave 2 for scope).** Protects D3 and D6. "cleanup
publication preserves completed slot without erasing deadline" in
`WorkerEvidenceTests` already asserts `sentinel_deadline`, `done`, the completed
slot, progress phase 2 and `runner_timeout`; it must keep passing. The wave 2
red asserts the account records a stable terminal scope, because the final
reads follow a successful reap, and a completed lifecycle for the step.

**C2. A started boundary with a clean exit is neither not-reached nor
interrupted by the host (wave 1).** Protects D2, D3 and soundness; detects the
in-flight case being described as a kill. Input: a two-slot plan against
`started_attempt`; the fixture publishes progress only for index 0. Observed
facts: `sentinel_deadline`, `exit_code` 0, no termination request, slot 0
incomplete with its poison unread, slot 1 incomplete, progress attempt started
index 0. Required: the lifecycle views of the two steps differ; slot 0's
`rc` reads 0, never 12345. Forbidden: any kill or signal claim, and not-reached
for slot 0. Red today at `buildStepResults`: the two views are identical. Must
keep passing: "started attempt with unpublished poison has no completed
result", which pins the poison guard.

**C3. Reads that can describe different moments do not establish a conflict
(wave 2).** Protects D5 and the observation boundary. Input: constructed
output with `reaped` false, a failed kill (`rc` -1, `EPERM`), slot 0
incomplete, progress attempt returned index 0. Required: unresolved with a
reason naming the non-terminal collection scope. Forbidden: a conflict claim, a
not-reached claim, and any claim that the worker violated the publication
protocol.

**C4. A stable snapshot with incompatible publications is a scoped conflict
(wave 2).** Protects D5 and locality. Input: constructed output with `reaped`
true, `exit_code` 0, slot 0 completed, slot 1 incomplete, progress attempt
returned index 1. Required: a conflict naming the completion-before-return
rule, scoped to slot 1; slot 0 keeps its result; final status stays known.
Forbidden: an invented result for slot 1, and blaming the worker or a policy.

**C5. The same conflict produced by a real publication (wave 2, new fixture
mode).** Protects D5 through production rather than interpretation. Add a
`skip_publication` mode to the fixture that publishes attempt started and
attempt returned for index 0 without completing the slot, then `done`, then
exits 0 on `exit_requested`. Document the mode in the fixture README. Required
and forbidden claims as C4. The fixture, not the test, owns the process; the
test asserts a successful reap.

### Area D: claim-rule combinations and evidence changes

Home: `DispositionResolverTests.swift` for the enumeration and a table module
in `TestKit` for the independent expectations. All wave 2 for execution; the
table and its self-checks are wave 1 deliverables because they need no
resolver.

**D-model.** The finite domain, two slots unless stated:

| Axis | Values |
| --- | --- |
| Status | unreaped; exit 0; exit 17; signal 9; exit 0 and signal 9 together |
| Stop and intervention | `done` with no request; `sentinel_deadline` with no request; `sentinel_deadline` with kill `rc` 0; `sentinel_deadline` with kill `rc` -1 `EPERM`; `wait_error` with no request; `policy_write_error` |
| Progress | absent; apply started; attempt started index 0; attempt started index 1; attempt returned index 1; finished returned; operation 200; attempt started index 2 |
| Slots | none completed; first completed; both completed; second unsupported and completed |
| Scope | derived: stable when reaped, otherwise live |

The product is about one thousand rows. Each row is classified coherent,
contradictory, unresolved or inapplicable by the independent table, which is
authored from D1 through D8 and reviewed by hand at these cells: attempt
started index 2, operation 200, exit 0 with signal 9, unreaped with any
progress beyond a slot, and `policy_write_error` with any completed slot.
Contradictory rows stay in the domain. Raw numeric boundaries, the phase value
3 and the largest 20-bit item value, are a separate sweep of a dozen rows.

**D-props.** Over every coherent row: removing each sufficient basis for a
claim removes exactly that claim and names the missing witness; adding a
compatible completed slot changes only that step's claim; replacing the
diagnostic text or appending log events changes nothing. Over every
contradictory row: the conflict names its rule and every claim outside the
conflict's scope is unchanged from the nearest coherent row.

**D-self.** The independent table must reject a hand-written wrong answer for
each rule, D1 through D8, before the resolver exists. A table that accepts any
answer has no authority, and this is the check that establishes it.

### Area E: projection agreement and checker rejection controls

**E1. The controller projects a carried record and never re-derives (wave 1,
Rust).** Protects D7 and D8. The controller reads JSON, so the record can be
constructed before the runner produces it. Input: runner JSON with the
disposition object as the contract names it, carrying host cleanup after a
sentinel deadline, together with the matching raw facts. Required:
`termination_cause` equals the contract constant. Red today: the controller
ignores the object and reports `unknown`. Three counterexamples must keep
passing on the same test: the same JSON without the record reports `unknown`;
the record with an unrecognized future value reports `unknown`; raw facts that
would imply a cause, with a record that says otherwise, follow the record.
Blocked only on the object's spelling, not on the runner.

**E2. The independent checker rejects each kind of wrong output (wave 1,
Python).** Protects the oracle's own authority. Home: a new module in
`tests/lib`, exercised from `checker_controls.py` under `blackbox_e2e` with its
existing `reject=True` mechanism. Inputs are the live A1 envelope stored as a
fixture and four mutations: drop `termination_request` while keeping a host
cleanup cause (claim without basis); set `exit_code` 0 beside `term_signal` 9
(conflict must be flagged); keep every fact and set `termination_cause` to
`unknown` (loss must be flagged, and this is the control that recognizes
today's behavior); make the two steps' lifecycle views identical under a
started index 0 (indistinguishable must be flagged). Each mutation must be
rejected with the rule named. The unmutated envelope, once the repair lands,
must be accepted; until then the checker records it as the known loss.

**E3. The error prose agrees with the record (preservation, then wave 2).**
Today `classify` already writes "host requested SIGKILL during cleanup" only
when a termination request exists, and "no termination requested" otherwise;
A1 and A4 pin both. The wave 2 red asserts the clause is generated from the
record, by constructing a record and a prose string that disagree and requiring
encoding to refuse the assembled result.

### Area F: encoding, degradation, legacy absence and unknown values

**F1. Round trip preserves the record and transports unknown values
(wave 2).** Protects D8. Encode a result carrying the record, decode it, and
compare. A `terminated_by` value the decoder does not recognize must decode
and re-encode unchanged. Home: `ContractVersionTests` or a sibling.

**F2. A degraded reply keeps the account or says it lost it (wave 2).**
Protects D8 and preservation. Using the `ReplyFailureTests` pattern, inject an
invariant rejection on a result carrying the record. Required: the degraded
reply retains `runner_subprocess` with the record while comparisons are
withheld and `reporting_failure.evidence_retained` is true; the minimal
fallback, which has `steps` empty, reports `evidence_retained` false and
carries no lifecycle claim. Forbidden: a rejection loop in which the conflict
being reported is what the encoder rejects.

**F3. Legacy replies stay legacy (wave 1, preservation).** Protects D8 and
the compatibility rules. A schema-9 reply without the record through the
controller yields `unknown` for a signaled disposition and null for a clean
exit; both pass today and are the counterexamples in E1. The wave 2 addition
has `recover_evidence` report the lifecycle account as `not_reported` for such
replies rather than absent, following its existing `not_reported` convention.

**F4. The reply shape golden changes (mechanical, not evidence).** Adding the
record fails `ContractVersionTests` until
`tests/fixtures/contract/response_shape.json` is regenerated and reviewed. That
failure is expected and is not one of the reds above.

### Preservation controls that already pass

These must keep passing through every stage and are listed so the test stage
does not mistake them for reds:

- `WorkerEvidenceTests`: "cleanup publication preserves completed slot without
  erasing deadline"; "started attempt with unpublished poison has no completed
  result".
- `CWorkerLifecycleTests`: "completed report survives independent nonzero
  exit"; "completed report survives independent signal"; "failed kill permits
  only nonblocking reap and no invented status"; "successful kill followed by
  failed reap does not decode wait storage"; "poll failure survives successful
  cleanup without claiming deadline expiry".
- `run_flow.rs`: `unconfirmed_reap_does_not_manufacture_clean_disposition_from_status_storage`;
  `capture_conditions_do_not_change_execution_status_or_cause`;
  `successful_run_keeps_correlations_without_a_termination_cause`.
- `witness_contract`: `worker_post_apply_hang_seam` and
  `worker_termination_and_log_correlation`, whose `unknown` for a self-signal
  remains correct under the record.
- `runner_outcome_runner_timeout`: the empty-plan control, including its
  `partial_steps is False` and its error prose substrings.

### Registration summary

| Home | Additions |
| --- | --- |
| `tests/catalog.json`, `tests/suites/witness_contract/` | Case `worker_attempt_in_flight_at_deadline`: wrapper script, Python check, README section, coverage-table note. |
| `runner/Tests/PWRunnerCoreTests/` | `DispositionResolverTests.swift` and its registry line; the D-model table in `TestKit`; a two-slot fixture helper. |
| `tests/fixtures/worker_lifecycle/` | `skip_publication` mode and its README entry. |
| `controller/src/run_flow.rs` | Tests B1 and E1 beside the existing diagnostics tests. |
| `tests/lib/`, `tests/suites/blackbox_e2e/` | The lifecycle checker module, the stored A1 envelope, and the E2 rejection controls. |
| `tests/fixtures/contract/response_shape.json` | Regenerated after the contract stage. |

No new `NormalizedOutcome` or `AttemptOutcome` value is introduced, so the
matrices in [tests/COVERAGE.md](../tests/COVERAGE.md) do not change. If the
contract stage chooses a new `AttemptOutcome` value instead of a separate
lifecycle field, the attempt matrix must gain that row in the same change.

## Where things live

Fact sources and implementation boundaries:

- [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift):
  `process.terminate()`, polling/grace/final reads, `CWorkerOutput`,
  `decodeWorkerEvidence`, and `ChildProcessState`.
- [CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift):
  subprocess/step builders, `computeComparison`, classification and error
  assembly.
- [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift):
  reply types, coding and invariants; the service reply boundary is in
  [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift).
- [pw_worker_evidence.h](tools/pw_probe_runner/pw_worker_evidence.h),
  [pw_probe_runner.c](tools/pw_probe_runner/pw_probe_runner.c), and
  [pw_probe_runner_abi.h](tools/pw_probe_runner/pw_probe_runner_abi.h):
  progress publication, attempt completion ordering, and numeric codes.
- [run_flow.rs](src/run_flow.rs):
  `synthesize_runner_sandbox_diagnostics` and `RunnerSandboxDiagnostics`.

Existing controls whose expectations move. The controls that must keep
passing unchanged are listed under "Preservation controls that already pass".

- Rust diagnostics tests in `run_flow.rs`: the assertions that pin `unknown`
  for a host-requested kill move to the contract constant; those for a
  self-signal and an unconfirmed reap stay.
- `tests/suites/witness_contract/check_pre_apply_failure.py`: its allowed set
  for `termination_cause` is revised so it still forbids sandbox and policy
  claims without pinning the old placeholder.
- `tests/suites/blackbox_e2e/checker_controls.py` and
  `tests/lib/consumer.py`: extended per E2 and F3.
- `tests/fixtures/contract/response_shape.json` and the field-complete reply
  that `ContractVersionTests` constructs: regenerated per F4. A shape golden
  alone does not establish semantic correctness.

Contract and explanatory documents:

- [tests/FAILURE-PROPAGATION-CONTRACT.md](../tests/FAILURE-PROPAGATION-CONTRACT.md):
  host observations, publication scope, failure precedence, attempt meaning,
  reply degradation, and the registered claim/projection requirements.
- [docs/PolicyWitness.md](../docs/PolicyWitness.md):
  step channels and diagnostic interpretation.
- [controller/README.md](README.md) and
  [runner/README.md](../runner/README.md):
  disposition, missing results, and evidence ownership.

## Versioning

Apply [docs/CONTRACT.md](../docs/CONTRACT.md) to the completed wire design.
Adding optional `disposition` and lifecycle detail alone does not bump:
absence in older replies is unavailable evidence. New mandatory reader
requirements or changes to existing field meaning do require the appropriate
version bump; do not label those changes merely additive.

The intended change to controller `termination_cause` semantics requires an
envelope bump; whether the completed response invariants require a response
bump is on the decision list. Edit [docs/contract.json](../docs/contract.json),
run `python3 docs/generate_contract.py`, and move only tests that depend on the
changed contract.

No worker ABI change is planned. Host observations plus existing publications
support the bounded claims above; they do not determine every lifecycle answer.
Uncertainty is a valid result when more detailed worker instrumentation would
be needed. Any proposal to change shared-memory layout or handshake is a
separate scope/version decision, not an incidental implementation detail.

## Order of work

Planning order and execution order are distinct:

1. **Finish the app-code action plan.** Close the implementation-boundary and
   evidence-sufficiency decisions above. Do not implement the application
   during this planning pass.
2. **Contract.** Complete the observation validity/scope rules, claim tables,
   projection inventory, wire representation, legacy behavior and finite model.
   Update the authoritative contract and applicable manifests/generated
   versions before app implementation. Resolve the open spellings in the
   red-test specifications against this contract.
3. **Tests.** Implement independent acceptance/rejection controls and the
   specified live/driver/transport tests. Establish the intended behavioral
   reds against unchanged app logic and record the preservation controls that
   already pass. If a new API cannot yet be called, separate that integration
   gap from the independently demonstrated wrong behavior. Review expected
   shape changes against the contract; do not generate an oracle from the
   eventual implementation.
4. **App code.** Implement the planned collection, canonical resolution,
   runner/controller projection and encoding work against those tests. Do not
   weaken the oracle to match convenient output. A necessary contract change
   returns to contract, then tests, before dependent app code.
5. **Verify.** Re-run the STR chain and selected boundary cases, check the
   independent oracle and transport guarantees, then run the required suites.
   Describe the final behavior and any remaining explicit uncertainty.

For the eventual app change, run
`cargo test --manifest-path controller/Cargo.toml`, then
`tests/run.sh --suite source_drift --suite runner_unit --suite runner_outcome_runner_timeout --suite witness_contract --suite blackbox_e2e`
against a normal signed build, then the default battery. Add the cases in
the registration summary to that list as they land. Changes to the wait,
release store or ordering eligibility also require the opt-in
`witness_contract/order_barrier_mutations` control under the repository rules.
Updating this plan alone calls for document/link consistency checks, not that
app verification battery.

## Extension rules and exclusions

The general category extends across observation boundaries. When adding a
validator, exec-child, or other conclusion, identify its owner, facts, validity
and scope; register its claim requirements and projections; carry uncertainty
and conflict reasons through serialization; and extend the independent oracle.
Keep separate observers' accounts and identities explicit. This is a reusable
contract discipline, not a requirement to move every subsystem into the worker
record in this implementation.

- A per-attempt deadline for in-process attempts remains separate work with
  its own limit entry. A future deadline fact joins the relevant attempt
  account with its own witnesses; it does not replace publication or effect
  evidence and does not create a second downstream derivation.
- Causal claims from log correlation remain outside this contract.
  `first_deny` stays a reference.
- `normalized_outcome` values, precedence and comparison verdicts keep their
  current contracts, as stated under "Claim requirements and projection
  inventory".
- This work does not add execution tracing, exact syscall-interruption
  attribution, a global lifecycle timeout, or new cleanup ownership.
