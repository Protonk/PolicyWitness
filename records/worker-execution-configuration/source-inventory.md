# Execution configuration: source inventory

Baseline: `503156f0693dd8a22acf633efccdc93e300f2ebc`.
Scope: the source-inventory portion of the associated
[execution-configuration plan](../../runner/Sources/PWRunnerCore/EXECUTION-CONFIGURATION-PLAN.md).
This is source inspection, not a new execution observation. No application,
fixture, process experiment, build, test, environment probe or production edit
was run. Exec-supervision and descriptor decisions remain pending; this record
does not select a mode flag, request form, schema or new lifecycle fields.

The existing evidence already separates several useful questions. Which
service/helpers were selected, which controls were supplied, which allowances
were resolved, and which native boundaries were observed are different facts.
An override object is insufficient as an ordinary/instrumented classifier.

## Request, selection and provenance

| Layer | Source and current fact | Limit of the fact |
| --- | --- | --- |
| Controller request | [run_flow.rs](../../controller/src/run_flow.rs), `run`: reads once, admits the version, resolves runner selection and policy augments, strips controller selection fields and serializes one held request for delivery/fallback compilation. `_test_overrides` remains in that request. | The envelope does not retain the entire held request or a hash identifying all control values. `request_path` does not preserve the file's contents. A retained specimen remains necessary when echo is absent or sanitized. |
| Service selection | [runner_select.rs](../../controller/src/runner_select.rs), `resolve_runner_target_with_registry`, `runner_provenance_from_target`: standard versus BYOXPC, service/bundle/executable identity, registry ID and available per-role signature/entitlement metadata. | These are selected-runner facts. BYOXPC and requested interventions are independent axes. Helper-path overrides do not replace the selected bundle's signature/entitlement records with the substituted file's metadata. |
| Selected helper bytes | [dossier.rs](../../controller/src/dossier.rs), `Binaries::observe`, `helper_record`, `compare`: service, worker, validator and issuer paths compared with app-manifest roles before invocation. Built-in manifest-selected roles can be null; copies/overrides can be `match`, `mismatch` or `unavailable`. Absolute regular files can be hashed; relative, empty, malformed, unreadable, overlong or NUL-containing selections have bounded unavailable records. | Hashing selected bytes is not proof those bytes launched. Null is manifest-based selection, not an independent fresh hash. Byte equality is distinct from signing/entitlements and from runtime identity. Records can exist for roles never invoked. A path equal to the manifest-selected path produces the same null shorthand even when explicitly supplied. |
| Request admission | [PWRunnerAPI.swift](../../runner/Sources/PWRunnerCore/PWRunnerAPI.swift), `PWRunnerTestOverrides.init(from:)`: closed keys, optional strings, representable integers; missing/null values decode as nil. [CWorkerOrchestrator.swift](../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), `requestAdmissionFailure`: path byte/NUL checks. | Numeric acceptance is not native-argument acceptance. Several values are ignored, floored or rejected later. A relative path is not categorically refused by this path-admission layer; the controller correctly declines to resolve it using its own cwd. |
| Reply echo | `CWorkerOrchestrator.run` and [ProbeRunner.swift](../../runner/Sources/PWRunnerCore/ProbeRunner.swift), `requestRefusalReply`: echo the decoded supplied object, not a consumed/effective projection. `admissionRefusalReply` independently removes each unsafe path. | `{}` and inert values can be echoed. Meaning/admission refusals can echo controls before any driver ran. Decode failure, `already_ran`, client transport failure, some service early replies and minimal reporting failure can omit them. Omission does not establish that no controls were submitted. |
| Execution | [PWRunnerService.swift](../../runner/Sources/PWRunnerCore/PWRunnerService.swift), `runSpecimen`, selects worker and validator paths; `CWorkerOrchestrator.run` selects the issuer and translates controls into driver inputs. | Resolution is not invocation. An issuer is selected only when an extension declaration creates a session; validator launch needs an eligible reached phase, successful application, available collection budget and queries. |

The dossier is assembled before invocation and survives subsequent failures.
Its policy hashes identify selected policy source, not all execution controls.
`runner_subprocess.worker_evidence.abi_identity` is host-selected source identity;
the [wire contract](../../docs/CONTRACT.md#internal-hostworker-identity) explicitly
does not treat it as child authentication or evidence of reaching ABI validation.

## Supplied controls and resolution

The authoritative key table is the
[runner reference](../../runner/README.md#test-seam-_test_overrides).
The following adds the source-level distinction needed for a later design.

| Supplied control | Current resolution or gate | Existing observation |
| --- | --- | --- |
| `worker_executable_path` | Supplied string or bundle-local `pw-probe-runner`. | Selected-byte dossier; spawn failure outcome/diagnostic, or worker PID/publications/host lifecycle. A successful spawn has no worker-path field independent of echo/dossier. |
| `validator_executable_path` | Supplied string, otherwise executable bundle-local `sb_api_validator` with a computed app-level fallback if that file is not executable; used only for a reached collection with eligible queries. | Selected-byte dossier; native `validator_spawn_failure.executable_path`/return code, or phase validator PID, records, I/O and lifecycle. Successful validator records do not authenticate the executable. |
| `issuer_executable_path` | Supplied string or bundle-local `pw-extension-issuer`; `ExtensionSession` first checks executable availability and target preparation. No declaration means no session. | Selected-byte dossier; extension preparation/issuance status. Once launch is attempted, `issuer.executable_path`, spawn failure or PID, call-boundary/result publication and native result. Early availability/preparation failure can leave no issuer subprocess object. |
| `worker_timeout_ms` | `timeoutMsForCWorker`: default 120,000; supplied values floored to 50 ms, then `HostWaitClock` saturates the nanosecond conversion at `UInt64.max / 1_000_000` milliseconds. Changes host sentinel allowance, not native exec budget. | Reached `sentinel_wait.budget_ms`, elapsed/excluded time and stop. `poll_stop_reason: sentinel_deadline` establishes exhaustion of this host allowance; echo alone does not. |
| `validator_io_timeout_ms` | `timeoutMsForValidator`: default 30,000; supplied proposal floored to 50 ms, with no cap in this helper. Each phase then caps it by remaining aggregate allowance after planning, possibly below 50 ms. | Collection status and native collection stop/bytes/errors. A timeout diagnostic can include the actual deadline, but there is no structured per-collection I/O allowance field on successful collections. |
| `validator_total_timeout_ms` | Aggregate allowance `max(1, min(30_000, supplied ?? 30_000))`; planning and synchronous collection charge it across phases. | `collection_status: budget_exhausted` and unavailable query evidence can establish exhaustion; no structured initial/residual allowance or per-phase charge is retained. Sentinel `excluded_ms` is not a per-phase resolution record. |
| `worker_pre_ready_hang_ms` | Positive values become native argv; C accepts up to 60,000. `nanosleep` occurs after compile/optional capture and before ready/apply. Nonpositive values are omitted. | Ready/sentinel waits and worker readiness/application/progress can bound what followed. No dedicated entered/returned/result record for this sleep, and its return is not checked. |
| `worker_post_apply_hang_ms` | Positive values become native argv; C accepts up to 60,000. Sleep follows all phases and token erasure, before `done`. Nonpositive values are omitted. | Completed phases/slots, absent `done`, sentinel exhaustion and host cleanup describe a steered-timeout scenario. They do not uniquely prove the sleep call or requested duration occurred. No sleep result is recorded. |
| `worker_post_apply_kill_signal` | Positive values become argv; C accepts 1–31. After phases/erasure it calls `kill(getpid(), signal)` before `done`. Nonpositive values are omitted. | Reaped `term_signal` establishes fatal disposition; completed phases and missing `done` localize observed progress. The self-signal call/return is not separately published, and matching requested/observed signals do not uniquely identify their sender. Failed/nonfatal/ignored delivery may reach `done`. |
| `worker_kill_before_publish_slot` | Nonnegative values become argv; C accepts indexes 0–255. An index outside the actual plan is accepted but never reached. The matching slot calls SIGKILL after attempt dispatch returns and before completed publication (dispatch can itself refuse without a native attempt). | Started progress without immutable result, reaped signal and disposition describe the observed boundary. They do not expose the unreported native return or prove the signal's origin merely from echo. |

Resolution sources: `CWorkerOrchestrator.run`, `timeoutMsForCWorker`,
`timeoutMsForValidator`; [CWorker.swift](../../runner/Sources/PWRunnerCore/CWorker.swift),
`CWorkerInput`, `runCWorker` argv construction; the C worker's
[`parse_args`, `run_attempt`, `main`](../../controller/tools/pw_probe_runner/pw_probe_runner.c);
[ExtensionSession initializer](../../runner/Sources/PWRunnerCore/ExtensionIssuer.swift);
[`runValidator`](../../runner/Sources/PWRunnerCore/ValidatorClient.swift).

Native argv rejection precedes mapping/publications, so an echoed positive
value outside its C bound can terminate the worker before the intended seam.
For example, a 60,001 ms hang is not a 60,001 ms observed sleep. The host does
not replace the echo with a clamped native value.

Not every driver setting is a request control. `CWorkerInput` also has readiness
(1,000 ms), policy transfer (5,000 ms), exit grace (1,000 ms), internal proceed/
ordinal controls and internal exec deadline/budget inputs. Ordinary C defaults
are a 60,000 ms release wait, 10,000 ms per-exec deadline and 115,000 ms active
exec-plan allowance. These have different origins and accounting domains.
The CLI's default 240,000 ms RPC allowance is another independent setting;
`data.timeout_ms` describes it. A finite allowance does not imply a total
lifecycle bound or confirmed descendant cleanup.

## Source-derived examples

These are illustrative branches, not newly executed runs.

| Example | What can be said using existing fields | What cannot be inferred |
| --- | --- | --- |
| Ordinary request, no overrides | Retained specimen has no controls; selection/provenance names the standard or BYOXPC service. Reached host wait records report actual configured budgets; worker/phase/native records describe execution. | Null echo by itself does not prove the request lacked controls, or that the binary/environment matched an ordinary baseline. |
| Effective host allowance: `worker_timeout_ms: 1` | Source resolves 50 ms. A reached `sentinel_wait.budget_ms: 50` establishes the configured host allowance; `sentinel_deadline` separately establishes exhaustion. | The submitted `1` is not the resolved budget. A 50 ms allowance does not prove timeout, shorten the C exec budget or bound final cleanup. |
| Steered fatal scenario: post-apply signal 9 | If all phases completed, `done` is absent and confirmed reap reports signal 9, observations establish completed phase work and abnormal worker exit. Echo/source give the requested intervention context. | They do not prove signal sender, sandbox cause, a native return hidden before publication, or descendant cleanup. |
| Inert: `{}`, sleep 0/negative, or explicit default timeout | Echo may be non-null; no positive sleep argv is generated, or resolved timeout equals ordinary default. | Presence cannot classify changed execution. “Explicitly requested” and “different from default” are separate facts. |
| Accepted but unreached slot index | Index 200 with a one-step plan passes native range admission but never reaches the matching slot. | Echo cannot establish an intervention or a failure. |
| Unreached helper | Issuer override without an extension; validator override with no eligible queries; signal/hang paired with earlier compile failure. Selected-byte dossier and/or echo may exist while relevant phase/child records establish no corresponding launch/progression. | A selected nonexistent validator path cannot establish a failed spawn when no native spawn was attempted. An unrelated early failure does not test the requested late intervention. |
| Refused or lost before echo | Overlong/NUL path admission, malformed request, XPC failure or minimal reporting failure. Dossier, structured refusal and retained request have different available subsets. | Missing echoed values cannot be normalized to default controls; unsafe original bytes must not be reintroduced to fill the gap. |

## Readers and observations usable now

The [Swift API](../../runner/Sources/PWRunnerCore/PWRunnerAPI.swift),
`PWRunnerRunResult.init(from:)`, admits only the current response version and
decodes `test_overrides` as supplied typed controls. Its encoder validates
evidence/comparison relationships; neither path resolves controls into a
configuration record. The [Swift client](../../runner/Clients/PWRunnerClient/main.swift)
forwards successful reply bytes; its synthesized transport replies have no
request echo. [run_flow.rs](../../controller/src/run_flow.rs), `admit_reply`,
gives delivery failure precedence and gates versioned interpretation while
preserving parsed replies. [disposition.rs](../../controller/src/disposition.rs),
`execution_diagnostics`, validates and projects lifecycle evidence; it does not
infer intervention success from echo. The independent
[Python consumer](../../tests/lib/consumer.py) gates versions, checks shape
goldens and evidence rules, and likewise has no override-effect classifier.
The [contract](../../docs/CONTRACT.md) requires coordinated producer/reader/
fixture review if fields or meanings change; this inventory does not select
a version change.

An observation/applicability record can be built outside the app schema today:

- Retain the submitted specimen and invocation, source revision, app manifest/
  build provenance, selected-runner dossier and exact envelope. Preserve which
  evidence is local/gitignored when linking it.
- State requested controls exactly; list resolved static settings as deductions
  from the named source revision, and reached `PWHostWait` budgets as host
  observations. Keep unresolved dynamic validator budgets explicitly unknown.
- Cite observed native boundaries, publication/collection/ordering evidence,
  process status and independent cleanup facts separately. Label source-derived
  expectations and unattributed outcomes as such.
- Give each document claim its own applicability conditions: source/binary
  revision, role selected, specimen, observation stage, intervention and observed
  result. A launch snapshot under pre-ready/post-phase sleeps can support that
  sampled state with those controls; it does not automatically support ordinary
  timings, deny-policy reachability, unseen descriptor identity/access mode or
  current-source equivalence after a refactor.

This suffices to describe why an observation such as L is conditional without
adding a new application “instrumented” mode. It cannot invent missing
observations; the parent documentation workstream owns the representation and
applicability decision.

## Gaps to stage

Independent of exec supervision:

- Correct existing overclaims. `PWRunnerAPI.swift`'s `PWRunnerTestOverrides`
  preamble says presence flags a non-production run and “Any override consumed”
  is mirrored. The implementation mirrors supplied controls, including inert
  and unreached ones; absence on early replies is ambiguous. `CWorkerInput`
  comments promising a termination signal/timeout from requested controls also
  need the same conditional reading. `dossier.rs`'s module phrase “what ran it”
  should be read as pre-invocation selection, as its detailed contract already
  specifies. These are documentation corrections, not evidence discoveries.
- Decide whether retaining the request outside the envelope is sufficient for
  unreached/unechoed controls. A universal absence/presence mode inference is
  already unsound, regardless of future exec design.
- Exact dynamic validator allowance and aggregate accounting are not available
  as structured successful-run observations. Source-derived defaults and echo
  cannot reconstruct elapsed planning or residual per-phase budgets.
- Requested sleeps and self-signals have no dedicated native entry/return
  observation. If future consumers need proof of those interventions, existing
  lifecycle outcomes are insufficient; whether such proof is useful remains a
  design question. There is no need to add fields merely to label a retained
  controlled experiment accurately.
- Default validator resolution has an additional source-level gap: `defaultValidatorExecutablePath` tests bundle-local executability and otherwise computes an app-level path, while `Binaries::observe` records the bundle-local default. On that fallback branch, the dossier need not describe the path the host actually chooses. This does not establish that the intact current bundle takes that branch. The successful validator subprocess has no resolved path field; a failed spawn does.
- Selected paths/hashes/signatures have different observers and times. Existing
  pre-invocation byte hashes must not become runtime authentication by renaming
  them. BYOXPC selection remains independent of controls.

Await exec/descriptor outcomes:

- Any resolved execution account must describe the eventual owner of launch,
  stream collection, cancellation, leader wait and descendant/group cleanup;
  deciding fields now would encode guarantees still under investigation.
- The meaning of completion, deadline/grace parameters and independently
  observed cleanup should come from the selected supervisor design. A generic
  “effective override” flag cannot supply these facts.
- Descriptor applicability must use the descriptor investigation's actual
  object/access-mode and ownership evidence. A configuration declaration cannot
  certify an inheritance boundary or retroactively upgrade old snapshots.

No proposed request split or production build variant is needed to finish this
inventory. A later design can compare a smaller documentation/observation
clarification against explicit resolved configuration after those dependencies
settle.
