# Failure reporting routes

This inventory separates admission from runtime observations. Acceptance evidence below identifies which routes were exercised and which
coverage gaps remain. Capacities and time budgets are
unchanged. Authoritative field contracts live beside the Swift decoder/API and in
FAILURE-PROPAGATION-CONTRACT.md.

## Admission

All worker capacity refusals use one host-owned `admission_failure` record on the
runner result: `origin=runner_host`, `field`, `actual`, `maximum`, `unit`, and
optional `step_id`/`parameter_key`/`index`. Counts are items; strings are UTF-8
payload bytes excluding NUL. No child or worker report exists for this refusal.

| Boundary / detector | Available facts and former loss | Route | Acceptance | Status |
| --- | --- | --- | --- | --- |
| Source / host and defensive C worker | UTF-8 byte length, 262143 maximum; previously only child guard | Shared admission record; keep C guard independently | exact/over/multibyte host and CLI; direct C guard | implemented and verified; see acceptance below |
| Steps and parameters / host | counts, 256/1024 maxima; separate prose-only errors | Same admission record and forwarding | both counts exact/over, absence of process | implemented and verified; see acceptance below |
| Step ID, target / host | 63/511 payload bytes, step identity | Same record | exact/over/multibyte for both | implemented and verified; see acceptance below |
| Parameter key/value / host | 127/383 payload bytes, key | Same record | exact/over/multibyte for both | implemented and verified; see acceptance below |
| Exec args / host | 15 supplied items, 127 bytes each, step/index | Same record | count exact/over; bytes exact/over/multibyte | implemented and verified; see acceptance below |
| sbpl-check / helper | 4 MiB admission, helper outcome survives; note conflates rejection with compile failure | `policy_check_status` and independent helper note | refusal vs compilation failure vs success | implemented and verified; see acceptance below |

## Runtime

| Boundary / detector | Available facts and former loss | Route | Acceptance | Status |
| --- | --- | --- | --- | --- |
| Policy transfer / host | write errno/count plus final worker publications and wait status | Existing `policy_transfer_error` + worker evidence | interrupted pipe below admission cap; independent C guard | verified; see acceptance below |
| Validator lifecycle / host | kill return/errno, wait errors, successfully reaped status; unchecked status formerly looked clean | Shared child lifecycle implementation; `validator_subprocess` | driver + classifier + JSON: failed kill/wait, abnormal exit after verdicts | implemented and verified; see acceptance below |
| Validator request frame / C reader | 65536-byte buffer, null-ID parse_error; count previously hid missing prediction | accepted records at run scope; expected-ID accounting | real CLI overlong operation between two valid probes | implemented and verified; see acceptance below |
| Validator association / host | submitted query tuples and accepted records; an ID-only join could misattribute a prediction | unique ID plus matching operation/filter type/value in step join; all records and association faults retained | duplicate/unexpected/null IDs and wrong query fields, no reassignment | implemented and verified; see acceptance below |
| Changing path after attempt / host | recomputing eligibility after create/unlink could change the original query decision | immutable pre-attempt submitted probe or exclusion reason; absent validator cannot satisfy expected queries | real CLI unlink plus mixed/all-excluded create plans | implemented and verified |
| Validator stdout collection / host | input failure formerly abandoned unread output | stop writes, drain under original deadline; independent read/decode faults and collection stop | deterministic >32 KiB after closed input, EOF and deadline controls | implemented; corrective acceptance below |
| Reply UTF-8 / host | raw bytes and frame offset; whole-stream conversion erased preceding verdicts | byte framing then strict decode, host fault and bounded rejected bytes | valid prefix + invalid UTF-8 CLI, split multibyte and incomplete tail | implemented and verified; see acceptance below |
| Reply JSON/structure / host | syntactic vs structural failure; missing rc formerly invented allow/deny prediction | separate decode fault kinds; no invalid accepted verdict | malformed JSON, missing/null/wrong rc, valid no-native/unfamiliar diagnostics; fixture CLI | implemented and verified; see acceptance below |
| Controller capture / all three JSON receivers | exact full received length, retained 1 MiB prefix; parse failure blamed producer | stream byte counts/cap + local truncation diagnosis | valid oversized producer, malformed within cap, multibyte cut | implemented and verified; see acceptance below |
| Controller UTF-8 / all three JSON receivers | lossy text conversion could repair invalid producer bytes into valid JSON | parse original untruncated bytes; replacement text is context only | real invalid-UTF-8 runner/helper/observer producers are rejected | implemented and verified in Rust |
| Helper response structure / controller | valid JSON could claim ok without compiled observation | invalid_reply plus retained original envelope, compiled=null | missing observation and unfamiliar diagnostics through real subprocess receivers | implemented; corrective acceptance below |
| Observer native text conversion / log observer | native bytes become replacement text before JSON serialization | existing lossy conversion; strict downstream JSON cannot recover bytes | source review; no raw pathname-fidelity control | unresolved producer-side fidelity limitation |
| Denial correlation / controller | independent predictions, events, completed attempt provenance | existing reference-based correlation, no termination cause | retained regression tests with incomplete attempts | verified; see acceptance below |
| Optional profile capture / worker+host | 1 MiB region, publication/extent/digests | explicit unavailable with reason, independent of specimen result | capture suite, refusal controls | verified; see acceptance below |
| Exec stdout/stderr / worker | 1023 payload bytes each and truncation observations | existing per-stream truncation marker | exec output tests | verified; see acceptance below |
| Request decoding/admission / host/client | no worker exists; owning receiver has validation/decode error | existing bad_request; absent child records | bad-request and black-box controls | verified |
| Library and child spawn / host | dlopen/posix_spawn errors, no child PID on failure | existing owner error and spawn outcomes | libsandbox/worker/validator spawn CLI controls | verified |
| shm/pipe setup / host | failed native setup, no report available | existing shmSetupFailed/pipeFailed, no invented child report | classifier control plus source review | reviewed; native resource-exhaustion/setup failures not separately injected |
| XPC loss and reply encoding/decoding / client/host | receiver error or absent reply; worker report may have existed | existing xpc error/timeout/proxy labels; independent fallback only for xpc_error | route review; normal reply/caller-auth/JSON controls | limitation: no new destructive XPC-loss or reply-encoding fault injection; lost inner evidence remains unavailable |
| Readiness and deadlines / host/client | ready hint, actual polling stop, process status | existing host records and timeout summaries | worker lifecycle/readiness regressions; validator driver I/O deadline; client timeout route/constants reviewed | verified for worker/validator; client timer not separately forced |
| Open undrained policy pipe / host | blocking write precedes sentinel polling | documented limitation | no transfer deadline added | deferred: requires separate liveness design |
| Early/dependency/reporting-crash stderr | no mapped report may exist, process status lacks text | documented coverage gap | no capture experiment adopted | deferred: destination/resources, pre-mapping coverage, draining/backpressure, byte loss, EOF and cleanup need evaluation |
| End-to-end deadline | nominal worker 60s polling, synchronous validator 30s I/O, client default 240s | phase-specific evidence; budgets unchanged | no global deadline claim | limitation: transfer/readiness/hook/cleanup are distinct; successful kill still has blocking final wait |
| Full validator/controller buffering | complete received bytes held before decoding/prefix selection | counts describe received data, not memory bound | byte accounting controls | limitation: no streaming allocation bound |

## Validator record contract

NDJSON is framed on byte LF, then decoded strictly as
UTF-8 and parsed as JSON. Empty lines are ignored. The final nonempty fragment is
parsed (including an incomplete UTF-8 tail, which is a decode fault). Stop at the
first rejected frame, preserving earlier accepted records. Fault context is the
first 256 bytes in base64, with frame byte count, offset and explicit truncation;
these bytes are never an accepted verdict. I/O and decode faults are independent.

Every record must be an object with `kind=sb_api_validator_verdict`, integer
`schema_version=1`, a present string-or-null `step_id`, and nonempty string
`outcome`. Optional known string and integer fields must have those types or be
null; booleans/fractional numbers are not integers. Allow/deny require nonempty
step ID, operation and filter_type plus integer `rc` and `errno`. Diagnostic
outcomes (including unfamiliar outcomes) require a string `error`; native fields
may be absent/null. Diagnostics with integer `rc` retain it. Extra fields survive
in the raw JSON line; recognition of outcome names is not an acceptance allowlist.

Only a unique record matching a requested ID and its submitted operation/filter
type/value can supply that step's prediction. Diagnostics may omit query metadata;
any supplied metadata must agree. Duplicate
IDs provide no unique prediction; unexpected/null-ID records remain at run scope.
Missing/duplicate/unexpected/unassociated/query-mismatch evidence makes the run unavailable;
legitimate uniquely associated per-step diagnostics keep their existing semantics.
Clean process disposition and successful transport/decoding are independent
requirements for `ok`, even with complete ID coverage.

## Acceptance evidence

Signed-build evidence: [correction acceptance index](out/failure-propagation-corrections/README.md).
The earlier [step-2 index](out/failure-propagation-2/README.md) remains retained.

- All six admission rows: `failure_boundaries/admission` makes 30 CLI runs covering
  every exact/over and multibyte boundary, structured values/identity, absent
  processes on rejection and actual completion on admission. Shared production
  `workerAdmissionFailure` returns one `.admissionFailed` shape; one assembler
  forwards it. The C/Swift layout suite verifies the unchanged shared source cap.
- Worker defensive source guard: `runner_c_worker_harness/policy_overflow_refused`
  checks real C publication (operation 2/code 2/detail 262143), absent native call,
  and exit 7. `worker_sparse_failure` and `WorkerEvidenceTests` separately retain
  admitted-size interrupted-transfer EPIPE with report present/absent and failed
  cleanup. No bypass of normal host admission was added.
- Validator lifecycle/framing/structure/association: `ValidatorEvidenceTests`,
  `failure_boundaries/validator_frames`, `validator_association`,
  `validator_overlong_request`, `validator_removed_target`, and existing partial
  validator suites. Shared `ChildProcessState` supplies both drivers' actual
  kill/wait observations. Record acceptance and association are separate reusable
  functions; assembly/classification use actual submitted queries, not record count.
  Valid per-step diagnostics keep existing semantics; unfamiliar diagnostics are
  preserved; the broader mutation experiment below extends these controls.
- Controller capture/UTF-8: Rust runner-client, sbpl-check and observer receiver tests use real subprocess output,
  independently verify complete oversized producer JSON, and check exact byte
  metadata, local loss, malformed within-cap JSON, invalid UTF-8 and multibyte cut.
  This path stays distinct from the validator's NDJSON decoder because the
  controller receives one JSON envelope and has a separate prefix cap.
- Helper admission: `failure_boundaries/fallback_helper` observes the shipped
  helper's 4 MiB refusal. Rust tests check the actual startup-note function for
  admission/compile failure/success/unavailability; no missing worker stage is
  inferred from any helper result.
- Correlation: Rust controls include ABI-6 incomplete-attempt provenance with an
  independent prediction and kernel event. The live termination/log-correlation
  witness preserves the run and raw events; candidate association is not cause.
- Optional capture: ABI/capture-helper and Swift capture refusal/digest/extent
  controls. Exec output: CLI args/stderr and stdout truncation-marker controls.
  Both streams use the same bounded C reader; stderr truncation is not separately
  forced. Optional capture does not set specimen failure.
- Earlier setup/readiness: CLI bad-request, library/spawn, readiness/deadline,
  caller-auth and black-box controls pass. Setup and transport fault-injection
  gaps are explicitly listed above; those rows do not claim every OS failure was
  induced. Every listed route has an owner, acceptance or a stated limitation.

No capacity or production timeout was raised. Early stderr and the open undrained
policy pipe remain deferred. Successful kill can still block in final reap;
failed cleanup can leave a child unreaped. Full output buffering remains. These
limits prevent a claim that all failures are bounded or always reportable.

## Audit corrective acceptance

The step 2 evidence remains retained. Audit findings C1–C7 and G1–G6 are
addressed by the corrective implementation and acceptance below; the log
observer producer-fidelity limitation is explicitly unresolved.
BBX workspaces use test-owned `/private/tmp` paths with before/after artifact
copies and exit cleanup. This avoids testing Desktop privacy consent as if it
were SBPL enforcement. Existing TCC entries are outside this correction.

The log observer itself converts native log bytes with UTF-8 replacement before
serializing JSON. Strict controller decoding cannot restore those original
pathname bytes. Producer-side raw pathname fidelity remains an unresolved,
separately scoped observation limitation.

| Audit findings | Correction and acceptance route |
| --- | --- |
| C1/G2 | Bind to actual submitted query; mismatch transcripts vary every query field independently, retain the raw record and require non-ok plus absent step prediction/drift. `failure_boundaries/validator_association`. |
| C2/G6 | Keep diagnostic provenance, authoritative native_rc=null and legacy rc=-1; no-query-metadata diagnostic control in `validator_frames`; public error prose corrected. |
| C3 | Freeze submitted/excluded plan before attempts; `validator_removed_target` covers unlink and mixed/all-excluded creates. |
| C4 | Response 6 nullable query PID, explicit null on admission and no host substitution; stored response-5 integer PID still decodes. |
| C5/C6/C7/G3 | All three controller receivers share strict original-byte decoding, exact counts and cap semantics. Rust subprocess controls cover invalid UTF-8, oversized valid JSON, malformed and missing helper observations, retained diagnostics and null native facts. |
| G1 | Deterministic closed-input fixture emits over 32 KiB after closure; driver controls retain verdict/UTF-8 fault at EOF or preserve write and read-deadline errors together under the original budget. |
| G4 | Shared BBX scratch paths avoid Desktop; retain before/after copies and clean up. Installed BYOXPC controls exercise both cases. |
| G5 | Required missing binaries/fixture environment throw TestFailure; wrapper rejects internal SKIP/FAIL. Negative equipment run must reach a normal failed summary. |
| Directional drift | Actual DAC EACCES with a separately denied prediction retains drift=false without claiming sandbox cause; direct OS control and restored-permission run remain. |

Corrective acceptance: [index and exact commands](out/failure-propagation-corrections/README.md),
[case/integrity audit](out/failure-propagation-corrections/acceptance.json),
[build/source hashes](out/failure-propagation-corrections/accepted-build.json).
The latest results cover 93 distinct passing catalog cases, 256/256 Swift tests,
106/106 Rust unit tests and 10 CLI integration tests. The broad run's sole
failure exposed a legacy null-PID decode fallback; the corrected decoder and
all 14 final focused cases pass. All inspected app snapshots remain valid and
unchanged. Both installed BYOXPC BBX cases pass; all four standard/BYOXPC BBX
workspaces are removed with before/after artifacts retained. The deliberate
missing-equipment run reaches 205/256 with 51 ordinary required-equipment
failures, zero internal skips, and exit 1 rather than a crash. It is negative
control evidence, not an acceptance failure. Step-3 acceptance below extends this verified baseline.

## Unfamiliar-code transport experiment

The step-3 controls extend the earlier single-code witness without adding any
production registrations or mappings. The supported worker ABI, response and
request versions remain 6/6/1. Production behavior is unchanged.

| Boundary | Control and claim | Limits |
| --- | --- | --- |
| Worker publication → Swift → runner JSON → XPC client → controller | `witness_contract/unfamiliar_diagnostic_transport`: independent alpha/beta payloads, including unknown operation/kind and known operation with unknown code; exact code/result/errno/index/detail/text and authoritative worker PID | Controlled producer, no native-call attribution. Incompatible control changes the version word in the current layout. |
| Structural publication and text | Same CLI control plus `DiagnosticTransportTests`: absent/unpublished/invalid payloads, incompatible version, invalid extent and real 4095-byte text truncation | Numeric preservation does not promise unavailable text or future ABI support. |
| Host failure beside worker record | Actual admitted-size EPIPE remains under policy_transfer_error beside beta; exit 23, incomplete attempts and non-ok summary remain | Fixture worker reports are controlled; EPIPE is an actual host observation. |
| Validator → Swift → runner/client/controller | Two unfamiliar diagnostic records and complete raw JSON survive a UTF-8 receiver fault beside a fixture-supplied allow record and an independently checked real-worker file change. Clean EOF preserves existing diagnostic semantics | The transcript producer never calls sandbox_check; even the allow/native-result fields are supplied test data. Record co-preservation establishes no causal relationship. |
| All controller JSON receivers | Rust real subprocess controls compare complete runner/helper/observer envelopes, including supplied failure reports, and contrast with oversized valid JSON | Helper/observer capture functions are exercised directly; supplied failure reports do not establish real XPC-loss, compiler or kernel-log failures. |
| Mutation sensitivity | Known-code-only worker decoding, known-outcome-only validator forwarding and shared receiver detail removal must fail preservation controls | Temporary mutations are excluded from restored source and final signed app; they are negative controls, not acceptance. |

Real worker success, compile failure, interrupted transfer, lifecycle, timeout,
partial-validator, receiver-rejection and admission controls remain required
regressions. The earlier liveness, stderr, buffering and log-pathname limitations
remain unchanged. Retained experiment evidence is indexed in
[step 3](out/failure-propagation-3/README.md).

Step-3 acceptance: all 49 selected catalog cases pass, with 258/258 Swift tests,
109/109 Rust unit tests and 10 CLI integration tests; no internal Swift SKIP/FAIL.
All eleven CLI transport controls pass. Known-code worker filtering causes five
CLI control failures and a normal 253/258 Swift summary; validator filtering
causes both validator CLI controls and the direct control to fail (257/258).
Shared-receiver detail removal fails all three new Rust receiver controls.
The final signed app is valid/unchanged and all mutation sources are restored
byte-for-byte. See the [acceptance audit](out/failure-propagation-3/acceptance.json)
for exact commands, paths, hashes, negative controls and limitations. No production
recognition-dependent boundary was found in the exercised routes.

The [step-3 closeout](out/failure-propagation-3/closeout/README.md) verifies the
retained results and restored sources against the current signed app, with only
documentation differences from the tested snapshot. Its corrected coverage
claims separate fixture-supplied fields from observed host/receiver/process facts
and real-worker effects. All seven step-3 requirements are complete; interpretation
of joined observations and consumer recovery remain in steps 4–5.
