# F2 reservation repair design

Source preparation: `b471226a`. The F2 investigation records an ungated lost
refusal and separate 4097 observations before execution and after a completed
effect. The user accepted reservation before submission, authorized continuation,
and explicitly allowed schema changes. This design implements that direction;
F1 remains unresolved. Historical failures remain unattributed.

## Result and boundaries

Every supported client acquires an effect-free reservation before sending a
specimen. The client can reconnect while acquiring. It irrevocably stops
acquiring before invoking execution. Neither a transport error nor an explicit
execution-method refusal permits replay. A missing reply can still mean completed
work; the repair does not promise exactly-once delivery or receipt.

Fresh host/worker ownership, request decoding, worker/validator orchestration,
collection/release ordering and host-result construction remain intact. There
is no durable result store, execution deduplication, host pool or legacy
execution fallback. The existing 50 ms terminal reply flush delay remains a
best-effort delay, not a delivery guarantee.

## Versions and installation

- Add `runner_protocol: 2` to docs/contract.json. Generate its Swift, Rust and
  Python constants and the signed service plist's `PWRunnerProtocolVersion`.
  This owns the external RPC/control messages and client capture format.
  Replace the independently authored RUNNER_PROTOCOL_VERSION constant.
- Bump controller envelope 8 to 9: raw helper stdout changes from a host-shaped
  response to a client capture; submission observations have separate authority,
  and the old runner_acquisition refusal array is removed.
- Keep specimen request 5 and host response 24: their shapes, parsing and
  execution meanings do not change. A transport rejection is not a specimen
  bad_request or a manufactured host RunResult.
- The old execution-capable `runSpecimen(_:withReply:)` selector is no longer
  exported. Old direct clients cannot execute on a new host. Current clients
  require the reservation RPC and never downgrade after a failed call.
- New installation requires the service's integer protocol marker to match.
  Check it before installation mutations and read it back after signing. Record
  that advertised value; it is not proof of working RPC support. This permits
  --skip-bootstrap without making a live probe a prerequisite for installation.
  Actual run/verify independently admit the reservation response before submission.
- Existing registry records remain readable regardless of execution protocol.
  Protocol 1 or unknown versions refuse run/verify selection with an upgrade
  diagnostic; list, status, reconcile and owned removal remain usable. Do not
  bump the registry format or rewrite old records. Built-in selection remains
  manifest-based and uses the mandatory current protocol, without plist fallback.

## RPC and host state

Use Data for control JSON and retain the existing Data specimen/result boundary:

```swift
@objc protocol PWRunnerProtocol {
    func reserveRunner(_ request: Data, withReply reply: @escaping (Data) -> Void)
    func runReservedSpecimen(_ request: Data, reservation: String,
        withReply reply: @escaping (Bool, Data) -> Void)
}
```

The execution callback Boolean identifies the payload format: true means an
ordinary host RunResult; false means a protocol control refusal. It does not
mean that a worker ran or an effect completed. A valid reservation consumes its
slot before specimen decoding, so malformed specimens still consume one host
and return the existing bad_request RunResult.

Reservation requests contain only protocol_version, a fresh attempt UUID and
requested lease_ms. They never contain specimen bytes, policies or probe plans.
The host admits the integer version and closed bounded structure before claiming
a slot. Grant replies identify protocol_version, status, echoed attempt UUID,
host PID, a process-local host instance UUID, reservation UUID and granted lease.
Occupied replies identify status and the host instance without granting anything.
Invalid input/unsupported protocol replies never claim a slot. Execution control
refusals name wrong, expired, absent, consumed or clock_error reservations without inventing
host execution results. Unknown/malformed control responses stop acquisition.

Host identity in these replies is host-reported, not independently observed
kernel-generation evidence. The connection identity is a server-created value
attached to the existing per-connection service object, not a caller PID or
caller-supplied UUID. The reservation UUID is valid only on that same connection.
Caller signing checks remain unchanged.

| Host-wide state | Event | Next state and action |
| --- | --- | --- |
| Free | Valid reserve | Reserved(connection, reservation, fixed expiry); arm expiry observation and return grant. |
| Reserved | Matching submission before expiry | Executing; consume slot atomically, then decode and orchestrate outside lock. |
| Reserved | Expiry or owner invalidation | Retiring; schedule owned exit without executing. Never reuse the slot. |
| Executing | Request/result path completes | Retiring; invoke reply and schedule existing terminal exit once. |
| Executing | Client invalidation or old lease callback | No state change; existing worker/validator ownership finishes normally. |
| Any occupied state | Other reservation or invalid submission | Refuse; do not execute or terminate the owner. |
| Retiring | Exit | Process ends; no further grants. |

All state changes use one host-wide lock. Submission checks expiry under that
same lock, even if the expiry callback has not run. Expiry/invalidation callbacks
must match the still-Reserved owner and reservation before changing state;
cancelling a timer alone is insufficient. Return scheduling actions from locked
transitions and invoke callbacks, encoding, orchestration and exit scheduling
outside the lock. There is exactly one retirement owner. A refused connection
does not schedule exit for another request.

## Client state and budget

One helper process owns connection acquisition and submission for both run and
runner verify. Remove the controller's execution-reacquisition loop. Read the
whole held specimen as today, but retain it locally until the grant is admitted.

Use a single serial state owner for connection callbacks, attempt cancellation,
deadline checks and the submission decision. Every callback carries an attempt
identity; a callback from an abandoned attempt cannot grant, execute or replace
the current result. Invalidate an abandoned connection before starting the next.
Only the current attempt's complete valid grant can advance to submission.

Immediately before calling runReservedSpecimen, check the deadline and atomically
mark submission `invoked`. This is deliberately conservative: even loss in the
tiny interval before the actual method invocation remains submitted/unknown.
After this transition, no code path reconnects or invokes execution again,
including a control refusal, timeout, interruption, invalidation, malformed reply
or 4097. Missing helper output is also not grounds for controller replay.

At the existing controller acquisition boundary, establish an absolute deadline
from mach_continuous_time and pass it to the single helper. This includes helper
launch and stdin delivery; the helper must not start a fresh full allowance.
Direct helper invocation without that controller deadline starts its allowance
after input is read and before opening a connection. Use the same system-wide
tick basis and checked/saturating timebase conversion in both languages. This
clock advances during sleep (as specified by the SDK mach_time.h). Host leases
have their own local deadline on that basis. A delayed timer only prompts a
fresh deadline/state check; it does not grant extra lease time.

New bounded controls, documented in limits.json with independent boundary tests:

| Limit | Value | Meaning |
| --- | --- | --- |
| Reservation lease maximum | 5000 ms | Grant min(requested remaining allowance, maximum); no renewal. |
| Reservation RPC wait | 5000 ms | Also bounded by remaining overall allowance. Timeout invalidates this unused connection. |
| Acquisition attempts | 256 | Stop explicitly at attempt_limit; do not discard earlier attempt evidence. This may end before the overall timeout. |
| Minimum reacquisition delay | 100 ms | Also bounded by remaining overall allowance; scheduling can take longer. No sleep after successful acquisition. |
| Control request/reply cap | 64 KiB | Check before JSON decoding; excess is a protocol failure. |
| Retained error message | 1024 UTF-8 bytes | Preserve domain/code and explicit message truncation; do not infer cause from prose. |
| Retained error domain | 128 UTF-8 bytes | Preserve explicit domain truncation. Error stages/reasons are closed vocabulary; no arbitrary userInfo dictionary is retained. |

The client allowance covers acquisition and waiting for the execution reply.
Host worker/validator budgets remain independently owned. A client timeout after
submission does not cancel or kill the executing worker.

## Client capture and readers

The helper always emits a `kind: runner_client_capture`, protocol_version 2
frame, including on transport failure; it no longer prints a synthetic
PWRunnerRunResult. The frame contains:

- Client PID and elapsed/overall-budget observations on the named clock basis.
- Acquisition attempts in order: ordinal, start/end elapsed milliseconds,
  outcome, received control byte count/hash, admitted control status and
  host-reported identity/lease when available, and bounded structured error.
  Do not publish reservation credentials or pretend these are kernel receipts.
- Acquisition stop reason: granted, overall_deadline, attempt_limit,
  protocol_error or local_error. Earlier transport failures remain in attempts.
- Submission state `not_invoked` or `invoked` and optional invocation elapsed
  time. An invoked submission refers to the last granted attempt.
- Terminal event: runner_reply, xpc_error, xpc_timeout, acquisition_failed,
  submission_refused, protocol_error or local_error, with error stage and native
  domain/code where observed.
- Nullable runner reply capture: received/retained byte counts, truncation
  marker and exact base64 bytes. Empty received data differs from no reply.
  Control refusal observations remain separate from this host-result payload.

The successful grant's credential is used only in memory; evidence records its
association through the attempt/host identity. Control byte hashes identify the
received bytes but are not full control-message retention. Unsupported control
versions supply no recovered grant or execution claims.

The controller retains the parsed capture or rejected parsed value at
runner_client.transport, its admission status/error separately, and existing
stdout/stderr capture diagnostics. Missing or inadmissible capture yields an
explicit unknown submission state in the controller's projection; never coerce
it to not_invoked. Keep the capture origin distinct from the host reply origin.

Admission order is local stdin delivery error, complete capture/version,
structural/state invariants, encoded-byte/count integrity, then the existing
host JSON/version/semantic admission. Unsupported parsed captures are opaque;
retain them without interpreting descendants. Truncated outer stdout is never
parsed. No host-derived diagnostics or worker identity may come from the capture.

runner_result contains only the received parsed host body, unchanged, including
unsupported parsed bodies when retained for diagnosis. A client/acquisition
failure leaves it null. Malformed bytes stay in the capture; versioned host
claims remain withheld exactly as today. runner verify uses the same admission
path and retains the capture, rather than projecting a PID from unadmitted JSON.

| Observation | Controller result |
| --- | --- |
| Valid capture, host reply | Existing response admission, classification and diagnostics. |
| Valid capture, XPC error/timeout after invocation | xpc_error/xpc_timeout, unknown execution, null host result, no replay. |
| Grant received, overall deadline reached before invocation | Retain acquisition granted, submission not_invoked and terminal xpc_timeout; execution was not invoked. Invalidate the reserved connection. |
| Valid capture, acquisition exhausted | xpc_acquisition_failed (or xpc_timeout for overall_deadline), known not invoked, null host result. |
| Valid capture, execution control refusal | xpc_submission_refused, invoked but host refused, no replay. |
| Missing/malformed/unsupported capture | Explicit missing/malformed/unsupported_runner_client outcome, submission unknown, no replay. |
| Local request delivery failed | Existing tool_error precedence, retain any capture without execution claims. |

The fallback compiler may run only for an admitted client terminal xpc_error,
against the same held request bytes. Its independent compilation still says
nothing about execution or the cause of XPC loss. Unsupported/malformed capture
or host reply supplies no fallback eligibility. Add bounded protocol-error and
local-error classifications without disguising them as a host bad_request.

Prove that base64 expansion of the existing maximum host reply plus the maximum
capture metadata fits the existing controller output cap. Exceeding a retention
cap remains explicit loss, never a complete reply. Update envelope shape goldens
from the owning producer and independent Python controls; host reply shape should
remain unchanged. Request and response version tests continue independently.

## Implementation owners and verification

Host/client: PWRunnerAPI, a shared transport-wire owner, service admission and
listener, and client session/entry. Keep a client session helper in the client
directory with explicit Meson membership and a direct compiled control that
executes that production helper. Preserve Swift service unit seams, replacing
old Boolean-admission controls with reservation state controls. Update their
mutation anchors; a compiler failure is not a successful mutation rejection.

Controller: runner_client/capture admission, run_flow, runner_commands,
runner_select, bundle metadata and registry protocol admission. Remove the
obsolete runner_acquisition loop and its evidence projection. Preserve held
request input, selection provenance and removal ownership. Contract generator,
build membership/account, worker identity and architecture account changes go
through their owning generators.

Independent consumers: tests/lib/consumer.py, capture/state controls, document
version handling, generated envelope golden and applicable blackbox checkers.
Raw-client callers must read the new frame and separately admit its host reply.
Adapt single_use and bad_neighbor_claims to assert reservation acquisition and
one effect per submission; do not retain expectations requiring the removed
legacy execution/refusal mechanism. Preserve their underlying isolation,
coexistence, deadline and independently observed cleanup obligations.

The old F2 fixture cannot validate reservation unchanged. Its historical source
and retained results stay recoverable. New reservation-boundary controls may
reuse trace/effect/cleanup helpers, but must state their actual intervention and
cannot reinterpret the original investigative pass as repair acceptance.

Required controls before acceptance:

1. State/unit: simultaneous reservations; wrong connection/token; duplicate
   submission; both expiry/submission race orders; late expiry after execution;
   disconnect while executing; malformed specimen after valid reservation;
   nonowner refusal cannot retire the owner. Assert actual orchestration entries.
2. Client/unit: late grants after cancellation, error/submission races, absolute
   deadline including launch/delivery, attempt and byte limits, and exactly one
   execution invocation after the submission decision. Controls use the production
   state logic, not a second model of it.
3. Reader rejection: impossible state/terminal combinations, invalid versions,
   base64/count mismatch, truncated captures, malformed/unsupported host replies,
   and missing capture after a recorded invocation. Preserve unknowns and raw
   rejected records; independent controls must reject invented nonexecution.
4. Live XPC: lost grant and lost occupied response followed by fresh acquisition;
   concurrent reservations; wrong/stale/reused reservation; abandonment/expiry
   and independently observed host generation exit. All nonexecuting paths have
   separate effect targets and no orchestration entry in the trace.
5. Live no-replay: complete an independent append effect, reap the worker, lose
   the execution reply, and observe exactly one byte and no second submission.
   Also lose the helper capture after invocation and establish no controller
   relaunch. Missing capture must remain unknown.
6. Compatibility: old-client/new-host and new-client/old-host produce no specimen
   effect; old registry selection refuses while list/reconcile/remove still work;
   malformed/unknown/missing installation markers refuse without owned-resource
   leakage. Marker admission and real RPC support remain distinct observations.
7. Normal signed build: default battery and affected admission/transport/native
   suites, runner_unit, unit, integration, source_drift, runner_abi_layout,
   runner_c_worker_harness, failure_boundaries and relevant runner_validator_failure
   and witness_contract cases. Explicitly run extensions_byoxpc, single_use,
   bad_neighbor_claims, new reservation controls and applicable registry/auth
   controls. Retain required Swift refactor verification and reconcile reuse.

Commit the design before production edits. Commit coordinated implementation,
regeneration and controls before the signed acceptance build. Record source/app
identities, failures and replacements without changing earlier credit. Seal F2
only after the normal signed workload and independent loss controls pass; an
instrumented case alone cannot do so. F1 and the remaining workset disposition
stay separate.

Design review: primary source review plus read-only independent reviews by
swift_design and review_public_extension. Both support the mandatory protocol,
connection-bound state transitions, separate capture admission and no-replay
boundary. Their compatibility alternatives were superseded by the user's
explicit permission to change versions. Final review added the grant/deadline
boundary and bounded every native-error string so the capture-size argument is
finite. No production behavior changed during design preparation.

## Implementation review and verification preparation

The candidate makes the version changes mandatory, including typed signed plist
advertisement checks before install mutation and after signing. A connection
lifetime token under the admission lock prevents an RPC queued after invalidation
from acquiring a lease. This is per connection, with no growing host-wide set.

Review tightened deadline admission for late execution replies, distinguished
clock failure from observed expiry, bounded host PID admission consistently with
both readers, and preserved invoked state on submission proxy failures. These
have focused controls in the actual state owners. They do not attribute the
historical failures or replace signed live verification.

Host reply retention is 64 MiB rather than the design's initial 50 MiB proposal:
the existing informative maximal reply is 52,843,694 bytes. A capture-only JSON
encoder avoids escaping base64 slashes; otherwise some retained byte patterns
would double the encoded expansion. The host result encoder stays unchanged.
Boundary controls cover the retention cap and a deliberately overfull metadata
frame beneath the existing 152 MiB controller stdout cap.

The current live apparatus is `runner_byoxpc/reservation_controls`. It imports
the original experiment's arrangement and durable cleanup equipment, but replaces
its protocol-1 source gates and executable case with reservation and capture
controls. Original results and fixture source remain recoverable at `7d3b57a5`.
`single_use` and `bad_neighbor_claims` now inspect pre-submission occupied control
observations rather than fabricated host outcomes or controller re-acquisition
records. A bounded request ends not-invoked/timeout; independently observed
occupied owner identities and file effects retain the acceptance obligations.
Ordinary back-to-back timing does not have to produce a race to pass.

Envelope-8 live fixtures require new untouched captures from the documented five
owning cases. They will be refreshed only after building this candidate. The
shape golden will be generated by its Rust owner and reviewed. No live fixture
will be relabeled by editing its schema or synthesizing capture provenance.

## Candidate preparation evidence

- `34496c0f` implements the reviewed candidate. Signed v0.3.3 build 1012,
  worker identity `86df53a3a899259bc529c8f819a54da08c33b90b679166770c43f6f5afed7d18`.
- `f2-reservation-prepare-01`, run `20261030T012416Z_d4b8acaf`: 11/20 cases
  pass. All 488 Swift assertions and the actual client/admission mutation
  controls pass. Nine case failures are localized to the pending envelope
  golden or documentation metadata/owner declarations. The generated envelope-9
  golden was reviewed and installed at `74c7ec56`; no live capture was edited.
- `f2-reservation-harvest-01`, run `20261030T012829Z_a810b0bf`, test source
  `74c7ec56`, same app: 13/15 pass. Rust unit and all five owning live fixture
  cases pass. Their untouched envelope-9 captures replace the current fixtures.
  Source-list mutation setup still required the added client-session membership.
  The reservation fixture completed lost grant, lost execution reply, lost helper
  capture and unsupported control arrangements. Independent-driver arrangements
  were incomplete. Every one of its nine cleanup receipts verified removal.

During that run the user supplied a screenshot of a Desktop-access prompt for
PWRunner.xpc and reported refusing twice. The run completed before an interrupt
could be sent. Subsequent public list/reconcile were empty. The exact access was
not independently traced: the failed arrangements all launched their new signed
driver from Desktop case scratch, and host caller authentication inspects caller
signing identity. Runtime driver, app and request files are consequently staged
in the arrangement-owned `/private/tmp` directory; compiler products remain in
scratch, exact signed-byte equality is recorded, and the durable cleanup
contract owns runtime deletion. No privacy database or permission is modified.
This correction requires a new live run; the earlier failures remain failures.

The raw-client caller-auth control also required protocol-2 adaptation. It now
reads native rejection-route diagnostics from bounded acquisition attempts and
expects overall-deadline/non-invocation, preserving same-byte positive controls,
independent file effects, missing-service rejection and final post-cleanup byte
inspection. It does not treat timeout alone as proof of caller rejection.

Both preparation runs are pinned in tests/RETAINED.json; raw output is local and
gitignored. Their source identities and the app's identity remain distinct.
Neither is whole-candidate acceptance.

`f2-reservation-controls-02`, `20261030T013614Z_2756615a`, test source
`a7289abf`, same signed build 1012, completed four passing cases and one failure.
Source-list mutations and independent comparison/checker controls pass; all nine
reservation arrangements now pass with verified cleanup after runtime relocation.
The caller-auth check retained its route assertion and exposed an introduced
client diagnostic regression: the generic interruption callback advances the
attempt before its richer native RPC error can be retained. Every captured
failure in that restricted arrangement was generic `interrupted`.

The narrow correction removes only the client's generic connection callbacks.
The pending RPC's error callback owns the native diagnostic; existing reservation
and overall deadlines still bound missing callbacks. Server invalidation and
reservation lifetime handlers remain. No schema, state transition or replay rule
changes. Independent review found no new correctness hazard; signed caller-auth
and reply-loss reruns must establish the exercised behavior. This run is pinned,
including its failure, separately from the corrected candidate.

`f2-reservation-errors-03`, `20261030T014038Z_7b9f5ac7`, clean `3e24e476`
and signed build 1015: actual client controls and all nine live reservation
arrangements pass, with every cleanup verified. Caller-auth still fails its
unchanged route requirement. Domain/code are now retained, but Foundation's
localizedDescription is only an abbreviated helper-error summary. The prior
client retained a detailed native description. The correction selects only
NSDebugDescriptionErrorKey when present, falling back to localizedDescription,
then applies the same UTF-8 bound and truncation flag. It never copies arbitrary
userInfo. A focused at/over-boundary Swift assertion pins that preference. The
worker identity regenerates because this shared source belongs to its
conservative digest closure; worker execution logic is unchanged.

## Signed candidate and combined verification

Candidate `4407d0aedb84a9f4af7cf133803e05fbdaa174c7` is signed v0.3.3
build 1016, worker identity
`87c9ac8e3b6dec120ae1c6a5a726fde3ddfc338907bf26a0e91d12efde176336`.
`f2-native-route-04`, run `20261030T014440Z_1028993a`, passes the caller-auth
case with native route diagnostics, independent restrictions and positive
controls. Its attached build log identifies this candidate.

`f2-reservation-final-01`, run `20261030T014533Z_3f5dbde2`, executes all 202
defaults, all 21 BYOXPC cases and six refactor opt-ins: native_clock,
exec-inheritance mutations, order-barrier mutations, exec-reader mutations,
reaped-ack mutation and extensions_byoxpc. All 229 finish: 225 pass, four fail,
with no sleep, skips, unrun cases or changed app bytes. The four suite-exit
errors correspond to these failures. All 21 BYOXPC cases pass; all nine
reservation arrangements complete with verified cleanup. Default registry and
reconcile inspection afterward show no records, candidates or inspection
errors. The original unwitnessed-worker directory remains protected.

The remaining failures identify constructed test inputs that were not fully
adapted to envelope 9's exact captured-host-byte invariant:

- `runner_unit/pwrunner_core_unit_executable`: all 488 Swift assertions pass;
  its Rust/Python policy-transfer replay changes the constructed host record
  without updating the capture. Original driver replies remain unchanged.
- `runner_filter_sysctl_name/checker_controls`: its recapture call also runs
  on deliberately malformed top-level JSON. Those inputs must pass unchanged.
- `runner_specimen_isolation/overlapping_runs_keep_evidence_separate`: live
  overlap completes, but authored optional-diagnostic omissions retain stale
  captured bytes. Recapture only the constructed host mutations.
- `blackbox_menagerie/validation_controls`: its authored policy hash and host
  variants likewise retain stale bytes. Preserve malformed outer carriers.

The repair belongs at these test construction sites, not in reader admission.
Keep live originals and negative transport controls intact. The normal signed
app remains applicable because the corrections are Python controls and an
embedded Python script inside Rust's cfg(test) module. Rerun all changed owners,
Rust checks and affected source/documentation checks before assigning credit.
The existing registry-recovery case now also contains the design's public
installation-marker and protocol-1 registry cleanup controls. Their execution
and the replacement checks remain to complete; the failed run stays failed and
pinned. Both runs above
and their console logs are retained in gitignored tests/out/runs/ and indexed
in tests/RETAINED.json.
