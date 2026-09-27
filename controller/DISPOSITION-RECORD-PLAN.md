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
below specify the intended guarantees and implementation boundaries, with
explicit space for the user or another agent to describe desired red tests.
Those specifications and the exact wire shape are still to be completed before
implementation; this document does not claim that the new oracle exists.

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

These are semantic requirements and existing ways to reach observations, not
completed red-test specifications. Exact lifecycle/reason strings and cause
mappings are finalized in the contract stage.

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
`worker_timeout_ms: 300`, `worker_post_apply_hang_ms: 800`. Check the actual
observations: timing is equipment, not the oracle. The required account is
`sentinel_deadline`, no termination request, reaped exit 0, final completed
publications, and `runner_timeout`. Existing driver controls also exercise
late completion during grace with an explicit grace budget.

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

Plan these actions before specifying the detailed red tests. They describe
implementation boundaries and dependencies.

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
   projection entries, shape fixture and eventual red tests. Update the
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

## Reserved space: desired red-test specifications

**Open for the user or a subsequent agent.** The acceptance observations and
oracle properties above are requirements, not a finished test battery. Do not
silently treat this section as completed or replace it with tests that only
mirror the eventual resolver.

| Specification area | Status / space for desired controls |
| --- | --- |
| Live loss of known facts: FIFO, completed prefix, late completion | Open — describe the precise assertion that fails before repair and its supporting raw witnesses. |
| Missing, unfamiliar, malformed and conflicting evidence | Open — specify independent expected questions, reasons and unaffected claims. |
| Collection scope and publication boundaries | Open — describe controls separating stable contradictions from valid observations at different moments. |
| Claim-rule combinations and evidence changes | Open — define the finite domain, independent acceptance cases, and removal/addition/irrelevance controls. |
| Projection agreement and checker rejection controls | Open — choose deliberately wrong outputs or implementation mutations and explain which rule must reject each. |
| Encoding, degradation, legacy absence and unknown values | Open — specify where evidence and limits must survive, or where loss must be explicitly reported. |

For each proposed red test, leave room to record:

- Rule/projection protected and the concrete regression it detects.
- Source observations, owner/identity/scope, and whether the input is a live
  boundary, driver fault control, constructed interpretation case, or transport
  fixture.
- Required, forbidden, unresolved or conflicting claims, including unaffected
  evidence; independently justified expected values.
- Expected red assertion and the layer where it fails. A setup failure or an
  accidental compile failure does not establish the desired behavioral red.
- Any counterexample that must still pass, cleanup ownership, timing/budget
  assumptions, and intended test location/registration.

Use existing seam rules in [runner/AGENTS.md](../runner/AGENTS.md). Do not add
request overrides that fabricate answers. Narrow native-call controls and
constructed classifier inputs remain appropriate for unreliable failure
boundaries, with their attribution and cleanup limits stated. Some preservation
controls should already pass; identify them separately from the required reds.

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

Existing controls to review, not indiscriminately flip:

- Rust diagnostics tests in `run_flow.rs`: some unknown-cause cases remain
  correct while known host-action cases gain detail.
- `tests/suites/witness_contract/check_termination_correlation.py` and
  `check_pre_apply_failure.py`: preserve the limits on external signal and
  policy attribution.
- `tests/suites/runner_outcome_runner_timeout/check.py`: preserve completed
  post-apply-hang slots; the FIFO needs different partial-step expectations.
- `tests/suites/blackbox_e2e/checker_controls.py` and
  `tests/lib/consumer.py`: independent rejection controls and stored replies.
- `runner/Tests/PWRunnerCoreTests/`: `CWorkerTests`,
  `CWorkerLifecycleTests`, `WorkerEvidenceTests`,
  `HostOutcomeClassifierTests`, `EnvelopeInvariantTests`,
  `ReplyFailureTests`, and `DiagnosticTransportTests`.
- `tests/fixtures/contract/response_shape.json` and the field-complete reply
  that `ContractVersionTests` constructs: acknowledge the new record and
  reasons after deciding the contract. A shape golden alone does not establish
  semantic correctness.

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
   evidence-sufficiency decisions above, keeping the future red-test slots open
   for explicit specification. Do not implement the application during this
   planning pass.
2. **Contract.** Complete the observation validity/scope rules, claim tables,
   projection inventory, wire representation, legacy behavior and finite model.
   Update the authoritative contract and applicable manifests/generated
   versions before app implementation. Resolve the desired red-test
   specifications against this contract.
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
against a normal signed build, then the default battery. Add any suites
required by the completed red-test specifications. Changes to the wait,
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
