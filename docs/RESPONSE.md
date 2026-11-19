# Responses: reading the available evidence

A response accounts for the boundaries reached and the observations collected.
Start with the process status and outer envelope, then establish which carried
records were admitted before interpreting their fields. This developer account
connects those readings to their complete public statements below.
[REQUEST](REQUEST.md) follows declarations and admission;
[CONTRACT](CONTRACT.md) traces commitments to their owners and support.

## Read the run from the outside in

The outer shape comes from `Envelope<T>` in
[json_contract.rs](../controller/src/json_contract.rs). This is an abbreviated
shape, with ellipses standing for members shown in the reference, not a captured
run or a complete JSON document:

```text
{
  "build": { "contract": …, "commit": …, "describe": …, "number": …, "version": … },
  "data": { … },
  "generated_at_unix_ms": …,
  "kind": "run",
  "result": { "ok": …, "rc": null, "exit_code": …,
              "normalized_outcome": …, "errno": null, "error": …,
              "stderr": null, "stdout": null }
}
```

Capture the controller process's exit status separately from stdout. For a
completed `run` publication, the [selected result](#contract-envelope-data-select)
supplies both `result.exit_code` and the process status. An independent caller
can compare those observations. A JSON field by itself is no observation of
how the process ended.

`build` identifies the controller that emitted the envelope. Nested client and
host identities identify their respective producers; matching strings do not
establish successful execution. `generated_at_unix_ms` is rendering wall time;
use the particular child and ordering records for their own intervals. The
[identity reference](#read-producer-identities) connects these fields to the
[derivation rules](CONTRACT.md#contract-identity-public).

Read `result` before following `data`, but do not stop there. Admitted host
`finished` selects `ok: true` and exit 0 even when an attempt failed or the
controller found inconsistent carried relationships. Failed attempts, integrity
findings and experiment completion answer different questions. The
[result and admission rules](#read-the-envelope-reference) retain the conditions
that make the mapping applicable; a decoded `finished` label beside an admission
refusal does not satisfy them.

Publication is an earlier event. Successful `example` or `test-input read` prints a
request document, not this envelope. Their exit 0 means complete publication;
`example` additionally carries its build's admission promise, while `test-input read`
does not. A later `run` supplies its own refusal, execution and collection
account. The [publication comparison](REQUEST.md) explains these entry points.

## Follow the producer and the retained record

The principal routes from `data` are:

| Start here | What to read next |
| --- | --- |
| `request_failure` | [Refusal code, location and stopped boundary](#read-refusals). Its absence does not establish completed execution. |
| `runner_client` | [Controller process observations and client transport capture](#read-invocation-and-transport). A stdin-write count, an execution-call observation and a host reply are different evidence. |
| `runner_result` | [Host execution record](#read-the-host-report), followed by the phase, actor, step and lifecycle records it carries. Retention and admission have separate rules. |
| `runner_sandbox_diagnostics` | [Controller assessments](#read-controller-findings), including what an integrity finding withholds. |
| `specimen` | [Held-input and equipment dossier](#read-the-dossier), which can be partial even on an early failure. |
| `policy_check` or `actor_policy_checks` | [Independent fallback compiler captures](#read-policy-observations), subject to fallback eligibility. |

The controller directly observes its client process, request writing and output
collection. The client carries reservation, submission and transport observations.
The host carries worker publications, validator records and its own supervision
observations. The controller then checks relationships among admitted records.
Follow the [process and channel account](ARCHITECTURE.md#evidence-channels-and-ownership)
when deciding whose observation supports a claim. A controller assessment is
not a second native measurement, and retained bytes are not automatically
admitted semantic evidence.

## Read absence and incomplete execution precisely

The field signature states whether a key is required, omitted on absence or
present with null. Apply that local rule before interpreting an empty-looking
record. In particular:

- Missing `request_failure` means the selected result supplied no such record.
  It is not an affirmative admission or completion record.
- Null `runner_result` means there is no decodable host reply. An admitted client
  capture can still hold exact rejected or truncated bytes.
- Null `runner_sandbox_diagnostics` accompanies earlier refusals and tool errors.
  An admitted completion without a host reply can instead have a no-worker
  assessment. A withheld assessment has its own supporting findings.
- A synthetic attempt with `no_completed_result` lacks a completed worker-slot
  publication. It does not establish that no native operation happened.

These cases are resolved by the [payload fields](#contract-envelope-data),
[transport admission](#contract-transport-client-admit),
[attempt provenance](#contract-steps-attempt) and
[worker publication account](#read-process-and-publication-evidence), not by one
rule that every absent value means failure or nonexecution.

An admitted capture saying `not_invoked` identifies the client's execution-call
boundary as not crossed. A missing or refused capture leaves submission
`unknown`. An `invoked` observation does not establish host receipt or admission;
effects can outlive a lost reply. The [once-only invocation protocol](ARCHITECTURE.md#contract-transport-delivery)
explains why that uncertainty does not authorize automatic resubmission.

An eligible fallback compilation is an independent compiler invocation. It can
supply policy information after a transport error without establishing any
worker progress. Similarly, a permission-shaped failure identifies an observed
failure class; it does not establish sandbox cause. `query_first` supports the
bounded collection-before-release ordering claim, not agreement between a
prediction and enforcement. Follow [step interpretation](#contract-steps-assessment)
and [process evidence](#read-process-and-publication-evidence) before drawing
those conclusions.

## Read the published example

Use the current app's `example` output as the input. Its complete content is
[extracted from the owning constant](REQUEST.md#contract-request-specimen-example);
[the round-trip case](../tests/suites/witness_contract/README.md#the-apps-own-example)
retains that selected app's raw emissions, submitted bytes, outputs and process
statuses. The following excerpt is the second action's two operands in
[EXAMPLE_DOCUMENT](../controller/src/example_document.rs), with its step label
omitted. It is input, not a run transcript:

```json
{
  "sandbox_check": {
    "operation": "file-read-metadata",
    "filter": { "kind": "path", "value": "/usr/share/dict/propernames" }
  },
  "attempt": {
    "kind": "file",
    "action": "read_fresh",
    "target": "/usr/share/dict/connectives"
  }
}
```

The query names B and the attempt reads C. First locate the corresponding
[step](#contract-steps-step), confirm the echoed operands and provenance, and
read the two records independently. The validator's answer about B predicts
nothing about the fresh read of C. The read's descriptor identity, byte count
and returned bytes support that operation's observation; the case's independent
samples establish correspondence with its target.

The maintained checker divides the evidence rather than treating exit 0 as an
answer key:

| Evidence in the exercise | Justified reading under the checker's conditions |
| --- | --- |
| Successful emission and matching version/plist identity | A complete build-bound document was published. Its own subsequent submission still supplies the admission observation. |
| No request refusal, admitted producers, matching policy digest and echoed operands | The associated report concerns the submitted workload at those checked boundaries. |
| Captured process exit 0 and admitted host `finished` | The experiment completed under the outer result mapping. The third attempt can still be `open_failed` with `EPERM`. |
| Separate expected answers and attempt results | Each channel met its independently authored workload expectation. The checker never compares prediction with enforcement or assigns the failed open to the policy. |
| Fresh-read identity and prefix matching independent samples of C | The returned read corresponds to those sampled descriptor and content observations, under the case's unchanged-target conditions. |

The [checker](../tests/suites/witness_contract/check_example_round_trip.py) owns
the workload and expected native results independently of the policy text.
Before each submission it requires readable regular A, B and C targets with
distinct identities, nonempty prefixes and a distinguishable C prefix. It
samples them again afterward; sampled equality does not prove continuous
stability or identify the object a native query consulted. Missing prerequisites
or missing/ambiguous associations cannot earn a native pass.

The emitted phased form, flat derivative and actor derivative each have their
own submission, observations and report rows. Only the first is what `example`
publishes. The [constructed actor fixture](../tests/fixtures/example_round_trip/README.md)
is hypothetical input to reader controls, not a captured native run. Use the
case's retained artifacts for a particular execution and keep its build and
source provenance with any execution credit.

## Follow one saved read input

The controlled-read case starts with the app's
[`test-input read` publication](REQUEST.md#contract-request-specimen-emit_test_input)
and keeps the saved input across changes to its target. The harness owns the
file and its changes; publication prepares no fixture. The
[maintained workload](../tests/suites/witness_contract/README.md#controlled-read-input)
and [checker](../tests/suites/witness_contract/check_test_input.py) provide three
instructive comparisons:

| Passage | Expected distinction to inspect |
| --- | --- |
| `allowed_a` → `replaced_a` | Identical saved input names the same path, but replacement gives the opened descriptor and independent sample a different inode. Equal content does not identify the object. |
| `replaced_a` → `suffix_a` | The returned prefix remains equal while a suffix outside it changes the observer's full-file digest. The worker's bounded read does not observe that suffix. |
| `suffix_a` → `bound_a` | The returned count and prefix remain equal when the suffix is removed. Returning a full bound does not establish EOF. |

These are the workload's separately authored expectations, not claimed new
captures. The run's `distinctions.json` records the actual comparisons and their
outcomes; the [control implementation](../tests/suites/witness_contract/test_input_controls.py)
checks sensitivity to stale captures, wrong generations and missing samples.

Follow the [fresh-read record](#contract-steps-fresh_read) to its
[aggregate projection](#contract-steps-assessment-fresh_read_aggregate). The
worker acquires a descriptor during the released action, records reached open,
stat, read and close observations, then publishes completion. The aggregate's
ordered failure selection and record consistency do not reopen the path or
compare it with the harness's file. [WORKER](WORKER.md#acquisitions-inside-attempts)
follows that acquisition and publication; the independent
[file observer](../tests/lib/file_observation.py) supplies different evidence
through its own descriptor.

Before/after samples establish only their sampled relationship. The observer's
full-file sample does not mean the worker read the whole file. In the crossed
`read-ba` workload, query B and read A also retain different operands even when
the files have equal content: descriptor identity distinguishes the read object,
and the query keeps its own native answer. A change to acquisition timing,
publication or the observer can deserve review with unchanged publisher and
help bytes; [CONTRACT](CONTRACT.md) provides the paths back to those commitments.

## Read the envelope reference

The complete frame, result and payload statements keep result selection beside its admission conditions. Nested native returns retain their own scopes.

<!-- BEGIN GENERATED CONTRACT envelope -->
<a id="contract-envelope"></a>
## The controller envelope

<a id="contract-envelope-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [The controller envelope](#contract-envelope) and its descendants.** Constructed outcomes preserve nested native evidence and select success only for finished. A real fixture child exposes delivery refusal precedence. Rendering serializes the borrowed payload once. Context: Read completion/admission/frame code and the named constructed or fixture-child checks. Evidence limit: Check reading. The fixture child is a controlled protocol writer; native kernel execution is separate evidence. [Evidence details](CONTRACT.md#contract-envelope-support-details).

<a id="contract-envelope-run"></a>
### Run envelope

Actor: [Controller](CONTRACT.md#contract-identity-definitions-controller). Boundary: run envelope presentation. Entry: cli run. Recipient: cli caller. Reports: run envelope. Record `run_envelope`: `rust.RunEnvelope`.

- <a id="contract-envelope-run-build"></a>**`build`** ([Build identification](#contract-identity-build)): The emitting binary's embedded build stamp, separate from nested producers.
- <a id="contract-envelope-run-data"></a>**`data`** ([Run payload](#contract-envelope-data)): Run payload, retaining observations under their admission and collection conditions.
- <a id="contract-envelope-run-generated_at_unix_ms"></a>**`generated_at_unix_ms`** (integer): Emitter wall-clock time at rendering, in milliseconds since the Unix epoch. An unavailable pre-epoch duration becomes zero. Child spans and continuous-clock ordering have separate observations.
- <a id="contract-envelope-run-kind"></a>**`kind`** (string): `run` identifies specimen execution.
- <a id="contract-envelope-run-result"></a>**`result`** ([Operation result](#contract-envelope-result)): The controller operation's result. Nested native and child returns retain their own scopes.

<a id="contract-envelope-result"></a>
### Operation result

Record `result`: `rust.JsonResult`.

- <a id="contract-envelope-result-ok"></a>**`ok`** (boolean): For an admitted specimen result, true exactly when the host outcome is `finished`. Evidence findings and failed individual attempts can coexist with true. Other commands define success for their own operation.
- <a id="contract-envelope-result-rc"></a>**`rc`** (integer ∪ null): Optional native-style result slot. Controller/helper-created results leave it null; native attempt returns remain in their nested records.
- <a id="contract-envelope-result-exit_code"></a>**`exit_code`** (integer ∪ null): Selected controller/helper exit status. For a run: zero for admitted `finished`, one for an execution/refusal outcome, two for tool or input-handling errors.
- <a id="contract-envelope-result-normalized_outcome"></a>**`normalized_outcome`** (string ∪ null): Selected operation label. An admitted host outcome is copied; controller and client admission failures use the classifications below.
- <a id="contract-envelope-result-errno"></a>**`errno`** (integer ∪ null): Optional native errno slot. Controller/helper-created results leave it null; nested errno values concern their own operations.
- <a id="contract-envelope-result-error"></a>**`error`** (string ∪ null): Human-readable diagnostic, null on successful controller/helper results. After execution admission, precedence is host error, client `stdout_capture_error`, client `stdout_parse_error`, then a generic unsuccessful-run message.
- <a id="contract-envelope-result-stderr"></a>**`stderr`** (string ∪ null): Optional captured text slot. Controller/helper-created results leave it null; client and child capture text stays in its own record.
- <a id="contract-envelope-result-stdout"></a>**`stdout`** (string ∪ null): Optional captured text slot. Controller/helper-created results leave it null; typed nested data carries the report.

<a id="contract-envelope-data"></a>
### Run payload

Actor: [Controller](CONTRACT.md#contract-identity-definitions-controller). Boundary: run payload assembly. Entry: cli run. Recipient: cli caller. Reports: run envelope. Record `run_data`: `rust.RunData`.

- <a id="contract-envelope-data-runner_sandbox_diagnostics"></a>**`runner_sandbox_diagnostics`** ([Execution diagnostics](#contract-diagnostics-execution) ∪ null): Assessments after client/reply admission. Null for earlier refusals and tool errors. An admitted execution with no host report can still produce the controller's no-worker assessment.
- <a id="contract-envelope-data-specimen"></a>**`specimen`** ([Run dossier](#contract-dossier-specimen)): Held-input, equipment and provenance observations, including partial records on failure.
- <a id="contract-envelope-data-policy_check"></a>**`policy_check`** ([Fallback helper capture](#contract-policy-fallback) ∪ null): Independent helper capture after an eligible admitted client-terminal `xpc_error`. Null when fallback was not invoked.
- <a id="contract-envelope-data-actor_policy_checks"></a>**`actor_policy_checks`** (array of [Per-actor fallback capture](#contract-policy-actor_check)?): Captures for actor declarations carrying a sandbox.policy object, in request order, when fallback is eligible. Collection of these policy objects precedes host admission of sandbox mode. Omitted when fallback is ineligible or the request contains no actor policy objects.
- <a id="contract-envelope-data-timeout_ms"></a>**`timeout_ms`** (integer ∪ null): Selected runner-client wait budget in milliseconds when argument parsing supplied it; null when no usable configuration was obtained.
- <a id="contract-envelope-data-runner_client"></a>**`runner_client`** ([Controller observation of the client process](#contract-transport-client) ∪ null): Client invocation, capture and delivery account. Null when the client was not invoked or launch failed before a capture returned.
- <a id="contract-envelope-data-runner_result"></a>**`runner_result`** ([Execution record](#contract-reply-record) ∪ null): Structurally decoded host reply when available, retained even if a later label gate refuses admission. Null when there is no decodable reply; an accepted capture can retain its exact bytes separately.
- <a id="contract-envelope-data-request_failure"></a>**`request_failure`** ([Projected request refusal](#contract-refusals-projection)?): Controller refusal code/path, or the host refusal projected from an admitted `bad_request` reply. Omitted when the selected result supplies none.

<a id="contract-envelope-data-success_findings"></a>
#### Success and findings

Uses [Select the public result](#contract-envelope-data-select).

For an admitted reply, `result.ok` and process exit describe the host completion
outcome. They do not certify successful attempts or successful controller
relationship checks. A `finished` reply with integrity findings remains true/0;
callers inspect the observations and findings for those separate conclusions.

<a id="contract-envelope-data-select"></a>
#### Select the public result

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at run completion after admission. Entry: cli run. Recipient: cli caller. Reports: run envelope. Select the first matching case in the listed order. Applies when present(`envelope.data.runner_result`). Client capture and host reply admission have succeeded. Follows [Apply reply-wide findings](#contract-diagnostics-execution-reply_checks). Compute diagnostics independently of the admitted host outcome and the selected run result.

`finished` can coexist with a failed file open or an integrity finding.
The observations and supported assessments state what the run establishes.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-envelope-data-select-finished"></a>1. Admitted finished outcome | `envelope.data.runner_result.normalized_outcome` = `"finished"` | [set_value(`envelope.result.ok`, `true`), set_value(`envelope.result.exit_code`, `0`), set_value(`envelope.result.normalized_outcome`, `envelope.data.runner_result.normalized_outcome`), retain_records(`envelope.data.runner_result`)]. |
| <a id="contract-envelope-data-select-other"></a>2. Other admitted outcome | `true` | [set_value(`envelope.result.ok`, `false`), set_value(`envelope.result.exit_code`, `1`), set_value(`envelope.result.normalized_outcome`, `envelope.data.runner_result.normalized_outcome`), retain_records(`envelope.data.runner_result`)]. |

<a id="contract-envelope-data-classification"></a>
#### Controller classifications

| Value or boundary | Result and retained account |
| --- | --- |
| `bad_request` | Decoded request admission refused; exit 1, structured refusal when supplied, dossier retained. |
| `tool_error` | CLI/input/configuration, client launch or request delivery failed; exit 2. A returned client capture remains on delivery refusal. |
| `missing_runner_client` | No retained client capture; exit 1. |
| `unsupported_runner_client` | Client producer/schema admission failed; exit 1, bounded rejected bytes retained. |
| `malformed_runner_client` | Client frame or capture semantics failed; exit 1, bounded rejected bytes retained. |
| `runner_reply_truncated` | Accepted capture says host bytes were truncated; exit 1, prefix retained. |
| `unsupported_runner_response` | Host schema/public identity failed; exit 1, captured bytes retained. |
| `malformed_runner_response` | Host decoding, capacity or label check failed; exit 1. A structurally decoded report remains when the later gate refused it. |
| `xpc_error`, `xpc_timeout` | Admitted client reports that transport failure; exit 1. xpc_error alone can permit fallback compilation. |
| `xpc_acquisition_failed`, `xpc_submission_refused`, `xpc_protocol_error` | Client reports acquisition failure, reservation refusal or protocol error; exit 1. |
| `runner_client_error` | Another admitted client local-terminal failure; exit 1. |
| `runner_response_unavailable` | Completion has no host result to supply an outcome; exit 1. |
| Other admitted host label | Retain the label and select exit 1; only exact `finished` selects run success. |

<a id="contract-envelope-data-admit"></a>
#### Boundary precedence

[Controller](CONTRACT.md#contract-identity-definitions-controller) checks at received run data admission. Entry: cli run. Recipient: cli caller. Reports: run envelope. The first failed condition selects the consequence. Check request delivery error first, then client failure (capture admission, host frame admission and transport terminal), then decoded host producer identity and host capacity/profile-label admission. A delivery failure yields tool_error/exit 2; another refused boundary yields its classification/exit 1. Retain the available capture and structurally decoded reply, with runner_sandbox_diagnostics null. Eligible xpc_error can add independent fallback compilation.

Admission precedes evidence interpretation. The same held request supplies
client delivery and eligible ordinary fallback compilation; the helper
result describes its separate compiler invocation.

<a id="contract-envelope-data-failed_attempt"></a>
#### A finished run with a failed attempt

An admitted report says `finished` while a step says `open_failed` with
errno 1. The controller emits result.ok true and exit 0, retains the step's
reported rc and errno and computes evidence findings independently. The
step's rc is operation-specific; this example does not prescribe its value.
<!-- END GENERATED CONTRACT envelope -->

## Read producer identities

Use the emitting build and admitted producer records at their points of use. [CONTRACT](CONTRACT.md#contract-identity-public) owns derivation and exact identity admission; these fields describe the values returned.

<!-- BEGIN GENERATED CONTRACT identity -->
<a id="contract-identity-build"></a>
### Build identification

Record `build_stamp`: `rust.BuildStamp`.

Every controller and compiler-helper envelope carries these string fields
under `build`. They identify the emitting binary's compiled context.

- <a id="contract-identity-build-contract"></a>**`contract`** (string): The public identity embedded in the emitting binary. Receiving boundaries use the exact value according to their identity-admission rule. Uses [Exact admission identity](CONTRACT.md#contract-identity-public-contract), [Release and development forms](CONTRACT.md#contract-identity-public-forms), [Direct compilation contexts](CONTRACT.md#contract-identity-public-direct).
- <a id="contract-identity-build-version"></a>**`version`** (string): The packaged build's version string. `build.sh` uses nonempty `PW_VERSION` when supplied; otherwise it takes the leading three-part version from its Git describe value, falling back to `0.0.0`. Direct Rust compilation reads `PW_BUILD_VERSION`, falling back to `unknown` when absent.
- <a id="contract-identity-build-number"></a>**`number`** (string): The build-number string. `build.sh` uses nonempty `PW_BUILD_NUMBER` when supplied, otherwise the Git commit count, falling back to `0`. Direct Rust compilation reads `PW_BUILD_NUMBER`, falling back to `unknown` when absent.
- <a id="contract-identity-build-describe"></a>**`describe`** (string): The descriptive source coordinate compiled into the producer. `build.sh` uses `git describe --tags --match 'v[0-9]*' --always --dirty`, falling back to `unknown`. Direct Rust compilation reads `PW_BUILD_DESCRIBE` with an absent value falling back to `unknown`.
- <a id="contract-identity-build-commit"></a>**`commit`** (string): The Git HEAD object name observed by the packaged build, or `unknown` when unavailable. Direct Rust compilation reads `PW_BUILD_COMMIT` with an absent value falling back to `unknown`. Describe and commit report provenance; identity admission compares the contract field.

<a id="contract-identity-build-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Build identification](#contract-identity-build) and its descendants.** Envelope build fields are strings, contract is embedded, and the version command's reported contract matches the independently read candidate plist. Context: Read build shell derivation and shared Rust serializer; read unit checks and integration command/plist assertions. Evidence limit: Integration checks populated packaged provenance; override and missing-Git fallback branches have source support. [Evidence details](CONTRACT.md#contract-identity-build-support-details).

<a id="contract-identity-producer"></a>
### Host producer identification

Record `producer`: `PWProducer`.

The host's typed reply carries this producer record. Each field comes from the
host's compiled build context.

- <a id="contract-identity-producer-contract"></a>**`contract`** (string): The host's public identity, independently compared by a receiver before the reply's execution records supply interpretations. Uses [Exact admission identity](CONTRACT.md#contract-identity-public-contract), [Release and development forms](CONTRACT.md#contract-identity-public-forms), [Direct compilation contexts](CONTRACT.md#contract-identity-public-direct).
- <a id="contract-identity-producer-describe"></a>**`describe`** (string): The host build's descriptive Git coordinate, or `unknown` in the ordinary unbound Swift build context. Packaged context generation supplies the observed build description. Uses [Describe](#contract-identity-build-describe).
- <a id="contract-identity-producer-commit"></a>**`commit`** (string): The host build's observed Git HEAD object name, or `unknown` when the compiled context has no such observation. Identity admission uses `contract`; this field retains the host's provenance. Uses [Commit](#contract-identity-build-commit).

<a id="contract-identity-producer-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Host producer identification](#contract-identity-producer) and its descendants.** PWProducer.current copies the compiled contract/describe/commit context; bound reply decoding compares producer.contract before decoding descendants. Context: Read the complete producer declaration/current constructor, generated Swift context producer, ordinary fallback context and Rust bound-frame path. Evidence limit: Source reading only; component signing, live peer association and a fresh packaged producer run require their respective evidence. [Evidence details](CONTRACT.md#contract-identity-producer-support-details).
<!-- END GENERATED CONTRACT identity -->

## Read the host report

Enter through `data.runner_result` after checking the applicable admission. Follow its steps, phases and actors to the evidence families below; its summary outcome does not replace their observations.

<!-- BEGIN GENERATED CONTRACT reply -->
<a id="contract-reply"></a>
## The host report

Actor: [Runner host](CONTRACT.md#contract-identity-definitions-host). Boundary: host reply assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply.

<a id="contract-reply-record"></a>
### Execution record

Record `host_report`: `PWRunnerRunResult`.

The host produces this record after execution or as a refusal. A received
record's admissibility and supported assessments have their respective
recipient boundaries.

- <a id="contract-reply-record-producer"></a>**`producer`** ([Host producer identification](#contract-identity-producer)): The host build context. Its public contract string is checked before a recipient interprets the body.
- <a id="contract-reply-record-specimen_id"></a>**`specimen_id`** (string): The admitted specimen identifier. A JSON-decode refusal uses `<decode_failed>`; refusal construction sanitizes an unavailable or over-capacity identifier.
- <a id="contract-reply-record-run_kind"></a>**`run_kind`** (string?): The caller's optional label, echoed when available and within admitted bounds. It labels the experiment and does not select an execution algorithm.
- <a id="contract-reply-record-rc"></a>**`rc`** (integer): Zero for `finished`, one for a classified refusal or failure. Native operations and child exit statuses have separate fields.
- <a id="contract-reply-record-normalized_outcome"></a>**`normalized_outcome`** (string): The host outcome, with the meanings below.
- <a id="contract-reply-record-error"></a>**`error`** (string?): Human-readable diagnostic, omitted on ordinary success. Published failure, host supervision and collection details can coexist here; their structured observations retain their own origins.
- <a id="contract-reply-record-pid"></a>**`pid`** (integer): For ordinary execution, the collected worker PID when worker output exists, otherwise the host PID. For actor execution, the host PID. Actor launch and subprocess records identify each worker.
- <a id="contract-reply-record-bundle_id"></a>**`bundle_id`** (string?): The host bundle's CFBundleIdentifier when available.
- <a id="contract-reply-record-policy_format"></a>**`policy_format`** (string?): The ordinary policy format when available; decode refusal uses `unknown`. Actor policies carry their formats in actor records.
- <a id="contract-reply-record-policy_sha256"></a>**`policy_sha256`** (string (hex)?): SHA-256 of the ordinary supplied source's UTF-8 bytes, as lowercase hexadecimal. It identifies the source observed by the host. Compiled-object and consumed-parameter identities have separate receipt fields. Actor form uses per-actor source hashes.
- <a id="contract-reply-record-compiled_profile"></a>**`compiled_profile`** ([Receipt](#contract-profile-receipt)?): The ordinary worker's opt-in receipt when collected output supplies it. Actor receipts belong to their actor records.
- <a id="contract-reply-record-sandboxed_after_apply"></a>**`sandboxed_after_apply`** (boolean?): The ordinary driver's observed applied publication when worker output exists. False leaves application unobserved by this flag; native failure publications and actor application assessments supply their own evidence. Actor form omits this top-level flag.
- <a id="contract-reply-record-steps"></a>**`steps`** (array of [Probe result](#contract-steps-step)): Probe rows in declared action order, with query, attempt and comparison observations. Refusals before worker execution and the minimal reporting fallback use an empty array.
- <a id="contract-reply-record-runner_subprocess"></a>**`runner_subprocess`** ([Worker subprocess](#contract-lifecycle-worker)?): Collected worker supervision, publication and disposition. Absent when no worker output supplies it; actor subprocess accounts live in actor records.
- <a id="contract-reply-record-admission_failure"></a>**`admission_failure`** ([Capacity refusal](#contract-refusals-admission)?): Capacity or embedded-NUL refusal details when that admission branch is reached.
- <a id="contract-reply-record-request_failure"></a>**`request_failure`** ([Runner request refusal](#contract-refusals-request)?): Structured code/path and, when applicable, expected identity for the refusal selected by the reached decoding or admission branch.
- <a id="contract-reply-record-phases"></a>**`phases`** (array of [Phase collection and execution](#contract-actor_evidence-phase)): Declared phases in schedule order, including reached and unreached phases when orchestration produces that account. Rows separate arrival, collection, completion and ordering.
- <a id="contract-reply-record-extension_events"></a>**`extension_events`** (array of [Extension event](#contract-extensions-event)?): Extension action observations with actor, phase and action association. Ordinary probe-only execution can omit this field; actor assembly supplies its event array.
- <a id="contract-reply-record-test_overrides"></a>**`test_overrides`** ([Execution overrides](REQUEST.md#contract-request-overrides)?): Accepted instrumentation echoed by orchestration, with refusal sanitation where required. It identifies the selected execution configuration.
- <a id="contract-reply-record-reporting_failure"></a>**`reporting_failure`** ([Reporting failure](#contract-reply-failure)?): Host validation or encoding failure and the fallback's retention state.
- <a id="contract-reply-record-execution_form"></a>**`execution_form`** (string?): `actors` identifies actor assembly. The ordinary producer omits the field. Recipient checks define the consequence of other carried values.
- <a id="contract-reply-record-actors"></a>**`actors`** (array of [Actor process account](#contract-actor_evidence-actor)?): Per-actor declaration, setup, application, launch and subprocess accounts. Preparation refusal can supply declaration records before launch; their presence alone does not establish launch.
- <a id="contract-reply-record-transfers"></a>**`transfers`** (array of [Host transfer observation](#contract-extensions-transfer)?): Host observations of extension delivery attempts and recipient acknowledgements.
- <a id="contract-reply-record-resources"></a>**`resources`** ([Resource tables](#contract-extensions-resources)?): Specimen-local token, delivery and handle records with their ownership and available production/use observations.
- <a id="contract-reply-record-schedule"></a>**`schedule`** ([Schedule account](#contract-actor_evidence-schedule)?): Actor scheduling waits, budgets and cancellation. Cancellation is a scheduling decision, separate from each actor's collected exit evidence.
- <a id="contract-reply-record-preparation_failure"></a>**`preparation_failure`** ([Actor preparation refusal](#contract-equipment-preparation_failure)?): Actor preparation failure selected before scheduler launch. Declarations and equipment observations from that preparation can remain present.
- <a id="contract-reply-record-equipment_inventory"></a>**`equipment_inventory`** ([Observed service inventory](#contract-equipment-inventory)?): Host read and validation of the sealed worker inventory.
- <a id="contract-reply-record-equipment_bindings"></a>**`equipment_bindings`** (array of [Static worker binding](#contract-equipment-binding)?): Static worker binding observations referenced by actor equipment assignments and preparation failures.
- <a id="contract-reply-record-equipment_entitlements"></a>**`equipment_entitlements`** (array of [Entitlement read-back](#contract-equipment-entitlements)?): Requested and observed entitlements used by preparation and live association.
- <a id="contract-reply-record-authority_setup"></a>**`authority_setup`** ([Authority setup account](#contract-equipment-authority_setup)?): Host and worker authority-setup publications, including acquired operation cells and cleanup evidence under their own publication rules.

<a id="contract-reply-record-assemble"></a>
#### Assemble execution evidence

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at host reply assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Assemble the aggregate summary and available observations without replacing native operation returns with the summary. Ordinary and actor-owned fields use their respective locations.

Ordinary classification examines worker failure, publication and supervision
before validator collection. If the worker side remains successful, the first
unsuccessful phase collection selects the summary; all collection records
remain. Actor orchestration reports each actor and selects the aggregate in a
fixed order. The first actor, in actor order, whose launch, setup, publication
or supervision record fails selects the summary; a declared-unapplied actor's
declared setup stands in for application in that judgment. Otherwise the first
unsuccessful phase collection, in schedule order, selects it under the ordinary
rule for that collection's validator result and allowance, whatever the owning
actor's sandbox mode. Otherwise a cancelled schedule selects `runner_failed`.
All actor and collection records remain.

<a id="contract-reply-record-outcomes"></a>
#### Host outcomes

| Value | Host commitment |
| --- | --- |
| `finished` | Execution and required collection completed under the classifier's conditions; each attempt retains its own result. |
| `bad_request` | Reached decoding/admission refused the specimen before worker or validator execution. |
| `bad_policy` | The host could not identify the ordinary source under its structural policy check. |
| `worker_spawn_failed` | The driver could not spawn the worker. |
| `runner_timeout` | Host sentinel or policy-transfer deadline expired, subject to higher-precedence published worker failures. Expiry of the actor schedule's execution allowance is reported as `runner_failed`. |
| `runner_failed` | Worker preparation/application/publication, host apparatus or supervision failed, or required observations are unusable. |
| `validator_spawn_failed` | Worker classification succeeded and validator spawn failed. |
| `validator_no_reply` | Worker classification succeeded and validator query delivery or verdict reading failed. |
| `validator_decode_failure` | Worker classification succeeded and validator parsing or typed decoding failed. |
| `validator_unavailable` | Required collection was not invoked, its budget/clock failed, or validator supervision/association was unusable. |
| `runner_reporting_failed` | The host failed to validate or encode its assembled report and entered reporting fallback. |

<a id="contract-reply-record-classification"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Execution record](#contract-reply-record) and its descendants.** Constructed worker/validator outputs select aggregate outcomes; published native failure and unobserved application retain separate meanings. Actor replies assembled from a real one-actor schedule with a supplied collection result select the same summary for an applied and a declared-unapplied actor: finished for a clean collection, the validator outcome for a failed spawn, decode or read, runner_failed for a failed validator pipe or query serialization, and validator_unavailable for an exhausted allowance. Signed-CLI actor specimens with a nonexistent validator and with an undecodable reply exit 1 with the failed summary in both modes beside an independently observed write. Assembly source establishes field locations and PID selection. Context: Read classifier branches, ordinary/actor assembly, source hashing, the classifier controls, the assembled-reply rows and the CLI specimens. Evidence limit: Check reading. PID placement, actor-order precedence and cancellation have source support here. The assembled-reply rows supply the validator result at assembly, so no validator ran; the CLI specimens cover one actor, one phase, a failed spawn and one JSON decode fault. No run is credited. [Evidence details](CONTRACT.md#contract-reply-record-classification-details).

<a id="contract-reply-failure"></a>
### Reporting failure

Record `failure`: `PWRunnerReportingFailure`.

- <a id="contract-reply-failure-origin"></a>**`origin`** (string): `runner_host` identifies whose validation or encoding failed.
- <a id="contract-reply-failure-diagnostic"></a>**`diagnostic`** (string): The failed validation/encoding diagnostic. The minimal fallback also includes the subsequent rich-fallback failure.
- <a id="contract-reply-failure-original_rc"></a>**`original_rc`** (integer): Code from the original assembled report, retained as diagnostic context.
- <a id="contract-reply-failure-original_normalized_outcome"></a>**`original_normalized_outcome`** (string): Outcome from the original assembled report, retained as diagnostic context.
- <a id="contract-reply-failure-original_error"></a>**`original_error`** (string?): Original aggregate error when present.
- <a id="contract-reply-failure-evidence_retained"></a>**`evidence_retained`** (boolean): True identifies the rich fallback: original fields remain apart from the producer/summary/reporting-failure metadata and removed step comparisons. False identifies the independent minimal fallback with scalar context and empty steps/phases.

<a id="contract-reply-failure-associations"></a>
#### Reporting-failure associations

Uses [Publish a report or fallback](#contract-reply-failure-publish), [Reader applicability](#contract-actor_evidence-actor-reader_scope).

Reporting-failure admission checks the degraded form and applicable receiver
context. It does not certify ordinary actor/phase associations in retained
records. Those records may preserve the inconsistency that caused reporting
failure. Worker-local lifecycle checks continue at their stated scope; no
comparison or query-order conclusion is recovered from retained raw records.

<a id="contract-reply-failure-publish"></a>
#### Publish a report or fallback

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at host response encoding. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. The first failed condition selects the consequence. Validate and encode the assembled report. If either operation fails, copy that report into a rich fallback, replace the producer and aggregate summary, preserve the original summary as reporting-failure diagnostics, and remove step comparisons. Validate and encode the rich fallback. If either operation fails again, use the independent minimal writer with original specimen/run/bundle/policy identity, PID and summary diagnostics. If that writer fails, return empty bytes.

The rich fallback preserves observations that triggered rejection. Empty reply bytes reach the
recipient's decoding failure.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-reply-failure-publish-summary"></a>Fallback summary | Applies when present(`reply.reporting_failure`). [set_value(`reply.rc`, `1`), set_value(`reply.normalized_outcome`, `"runner_reporting_failed"`), set_value(`reply.reporting_failure.origin`, `"runner_host"`)]. |
| <a id="contract-reply-failure-publish-rich"></a>Rich fallback comparisons | Binding `s`: entry in `reply.steps`. For each `s`. Applies when (present(`reply.reporting_failure`) and `reply.reporting_failure.evidence_retained`). [withhold(`reply.steps[s].comparison`)]. |
| <a id="contract-reply-failure-publish-minimal"></a>Minimal fallback arrays | Applies when (present(`reply.reporting_failure`) and not (`reply.reporting_failure.evidence_retained`)). [set_value(`reply.steps`, []), set_value(`reply.phases`, [])]. |
| <a id="contract-reply-failure-publish-producer"></a>Fallback producer identity | Applies when present(`reply.reporting_failure`). [set_value(`reply.producer.contract`, [Contract](#contract-identity-build-contract)), set_value(`reply.producer.describe`, [Describe](#contract-identity-build-describe)), set_value(`reply.producer.commit`, [Commit](#contract-identity-build-commit))]. |

<a id="contract-reply-failure-publish-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Publish a report or fallback](#contract-reply-failure-publish).** Constructed reporting defects trigger rich fallback, preserve other projected fields and remove comparisons; malformed fallback markers refuse. Independent minimal/empty paths are read in source. Context: Read report validation, fallback writers and constructed binary reply controls. Evidence limit: No new execution credit. Fallback validation establishes the degraded form, not ordinary association consistency in retained records. [Evidence details](CONTRACT.md#contract-reply-failure-publish-support-details).
<!-- END GENERATED CONTRACT reply -->

## Read refusals

Use the structured code and whole path to locate the selected problem, then return to the corresponding [request declaration](REQUEST.md). The reached decoder branch chooses the refusal; the vocabulary table is not a universal precedence list.

<!-- BEGIN GENERATED CONTRACT refusals -->
<a id="contract-refusals"></a>
## Request refusals and retained evidence

A refusal identifies the boundary that stopped the request or a later interpretation. Input refusals carry machine-readable code and location; transport and reporting failures retain the observations supplied by their own channels.

<a id="contract-refusals-request"></a>
### Runner request refusal

Record `request_failure`: `PWRunnerRequestFailure`.

The host supplies this record for decoding, meaning and capacity refusal. Its human error string explains the category; readers use the structured fields for machine classification.

- <a id="contract-refusals-request-code"></a>**`code`** (string): Producer's refusal category. Admitted vocabulary: open; displayed list: illustrative: `"invalid_json"`, `"missing_field"`, `"missing_value"`, `"type_mismatch"`, `"unknown_field"`, `"unsupported_contract"`, `"admission_refused"`. Unfamiliar values: An unfamiliar code remains an unclassified refusal category; its producer text and path are retained as evidence.
- <a id="contract-refusals-request-path"></a>**`path`** (array of string ∪ null): Object keys and decimal array indexes locating the rejected input; [] names the root. Retain the entire path only through <!-- span limits.request_failure_path_components.value_unit -->8 items<!-- /span -->, with each component through <!-- span limits.request_failure_path_component.value_unit -->63 UTF-8 bytes<!-- /span -->; otherwise null withholds it.
- <a id="contract-refusals-request-expected_contract"></a>**`expected_contract`** (string?): Current expected public identity supplied for refusal at `contract`; omitted otherwise. It identifies the receiver's expected assertion.

<a id="contract-refusals-request-select"></a>
#### Refuse at the first reached boundary

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at request decoding and admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Report the first failure reached by the actual decoder or admission branch. Check contract before unknown root fields; at a decoded closed object choose its lexicographically first unknown key before decoding its declared fields. Complete decoded capacity checks before meaning admission.

The ordinary and actor plan branches have different required fields and ordered checks. There is one request_failure per refusal. Its code and path locate the selected problem; correcting it may reveal the next problem.

<a id="contract-refusals-request-consequence"></a>
#### Stop children and preserve safe metadata

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at pre-child request refusal. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. [set_value(`reply.normalized_outcome`, `"bad_request"`), set_value(`reply.rc`, `1`), set_value(`reply.steps`, [])]. Uses [Specimen](REQUEST.md#contract-request-specimen). Start no worker or validator for the refused request. Retain metadata under its independent echo rule.

<a id="contract-refusals-request-families"></a>
#### Current refusal families

| Category | Current code examples and condition |
| --- | --- |
| JSON and required values | `invalid_json`, `invalid_value`, `missing_field`, `missing_value`, `type_mismatch`; decoder structure or required-value failure. |
| Public identity and closed objects | `unsupported_contract`; assertion differs or expected identity is unbound. `unknown_field`; undeclared object key. |
| Plan form and identifiers | `exclusive_plan_forms`, `actors_require_phases`, `empty_phases`, `empty_actors`, `empty_actor_id`, `empty_phase_id`, `empty_step_id`, `duplicate_actor_id`, `duplicate_phase_id`, `duplicate_step_id`, `actor_without_phases`. |
| Policy and query | `unresolved_augments`, `unsupported_policy_format`, `missing_policy_source`, `invalid_capture_nonce`, `empty_operation`, `unknown_filter_kind`, `missing_filter_value`. |
| Attempt and applicability | `unsupported_attempt`, `relative_exec_target`, `inapplicable_field`. Inapplicability includes non-exec args, ordinary actor-only fields, disabled-capture nonce, extraneous extension operands, an experimental submission's control in an ordinary request's override block and an override block with any member in an experimental submission. |
| Actor and equipment | `unsupported_sandbox_mode`, `unsupported_equipment`, `unknown_actor`, `empty_entitlement`, `duplicate_entitlement`, `invalid_termination_dependency`, `empty_equipment_overrides`, `relative_equipment_path`. |
| Extension grammar and ownership | `unsupported_extension_action`, `unsupported_extension_family`, `unsupported_extension_authority`, `relative_extension_target`, `empty_reference`, `duplicate_reference`, `unknown_token_reference`, `unknown_delivery_reference`, `unknown_handle_reference`, `wrong_owner_reference`, `repeated_release` and `extension_exec_unsupported` for reference assignment, ownership, release and exec participation. |
| Capacity | `admission_refused`; exact count, unit and available association are in admission_failure. |

Each code's condition remains attached to its owning input rule. This list supplies current examples for the open code vocabulary.

<a id="contract-refusals-request-compound_order"></a>
#### Branch-local refusal precedence

Each entry reports the first failure reached in its own traversal. CLI parsing, controller identity and selector checks, augmentation, host decoding, capacity and meaning admission remain distinct boundaries.

<a id="contract-refusals-request-compound_order-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Branch-local refusal precedence](#contract-refusals-request-compound_order).** Controller preparation and typed host meaning admission have their own ordered branches. Context: Static review of the cited producer and assertion branches. Evidence limit: The matrix checks selected neighbouring failures and their corrections through actual CLI and direct-host entries. [Evidence details](CONTRACT.md#contract-refusals-request-compound_order-disposition_support-details).

<a id="contract-refusals-request-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Runner request refusal](#contract-refusals-request) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Context: Review of the named producer branches. Evidence limit: Read identity-before-unknown, unknown-field and actor parameter-path assertions. The code examples are source-derived, with the reference-family details owned by extensions. [Evidence details](CONTRACT.md#contract-refusals-request-support-details).

<a id="contract-refusals-controller"></a>
### Controller request refusal

Record `controller`: `rust.RequestFailure`.

The controller supplies this shape for its JSON, assertion, selector and augmentation boundaries. Its location has the same bounded whole-path meaning as the runner shape.

- <a id="contract-refusals-controller-code"></a>**`code`** (string): Producer's refusal category. Admitted vocabulary: open; displayed list: illustrative: `"invalid_json"`, `"missing_value"`, `"type_mismatch"`, `"missing_field"`, `"unsupported_contract"`, `"unknown_field"`, `"invalid_value"`, `"conflicting_selector"`, `"augment_unavailable"`, `"missing_policy_source"`. Unfamiliar values: An unfamiliar code remains an unclassified refusal category; its producer text and path are retained as evidence.
- <a id="contract-refusals-controller-path"></a>**`path`** (array of string ∪ null): Object keys and decimal array indexes locating the rejected input; [] names the root. Retain the entire path only through <!-- span limits.request_failure_path_components.value_unit -->8 items<!-- /span -->, with each component through <!-- span limits.request_failure_path_component.value_unit -->63 UTF-8 bytes<!-- /span -->; otherwise null withholds it.
- <a id="contract-refusals-controller-expected_contract"></a>**`expected_contract`** (string?): Current expected public identity supplied for refusal at `contract`; omitted otherwise. It identifies the receiver's expected assertion.

<a id="contract-refusals-controller-consequence"></a>
#### Controller pre-invocation refusal

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at CLI preparation. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. [set_value(`envelope.result.ok`, `false`), set_value(`envelope.data.runner_client`, `null`), set_value(`envelope.data.runner_result`, `null`), set_value(`envelope.data.runner_sandbox_diagnostics`, `null`), retain_records(`envelope.data.specimen`)]. Uses [Controller selection options](REQUEST.md#contract-request-options), [Augment resolution](REQUEST.md#contract-policy-augments). Select bad_request for malformed JSON, missing or wrong contract assertions, malformed selector values or augmentation refusal. Select tool_error for argument parsing, missing or unreadable input and target resolution. Argument parsing precedes input reading; a retained target-resolution error takes precedence over an augmentation error. Preserve the diagnostic and structured refusal available at that stage.

These results identify local refusal, while the client capture owns whether a later invocation was attempted.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-refusals-controller-consequence-request_refusal"></a>Selected request refusal | Requires `envelope.result.normalized_outcome` = `"bad_request"`. [set_value(`envelope.result.exit_code`, `1`)]. |
| <a id="contract-refusals-controller-consequence-tool_failure"></a>Selected tool failure | Requires `envelope.result.normalized_outcome` = `"tool_error"`. [set_value(`envelope.result.exit_code`, `2`)]. |
| <a id="contract-refusals-controller-consequence-class"></a>Selected local class | Requires `envelope.result.normalized_outcome` ∈ [`"bad_request"`, `"tool_error"`]. |

<a id="contract-refusals-controller-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Controller request refusal](#contract-refusals-controller) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Context: Review of the named producer branches. Evidence limit: The checks cover exact identity admission and UTF-8 path-component and depth withholding. [Evidence details](CONTRACT.md#contract-refusals-controller-support-details).

<a id="contract-refusals-projection"></a>
### Projected request refusal

Record `projection`: `rust.RequestFailureProjection`.

The controller's run data projects either its own request refusal or the admitted runner reply's request_failure. Serialization emits the selected record directly, preserving its code, path and optional expected_contract.

| Alternative | Record |
| --- | --- |
| `Controller` | [Controller request refusal](#contract-refusals-controller) |
| `Runner` | [Runner request refusal](#contract-refusals-request) |

<a id="contract-refusals-projection-controller"></a>
#### Controller variant

The `Controller` variant carries `rust.RequestFailure` from local preparation.

<a id="contract-refusals-projection-runner"></a>
#### Runner variant

The `Runner` variant carries `PWRunnerRequestFailure` from the admitted host reply.

<a id="contract-refusals-projection-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Projected request refusal](#contract-refusals-projection) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. [Evidence details](CONTRACT.md#contract-refusals-projection-support-details).

<a id="contract-refusals-admission"></a>
### Capacity refusal

Record `admission`: `PWRunnerAdmissionFailure`.

Counts describe the complete submitted value. The reply uses the same admission rules to select a refusal and to decide which metadata it can echo.

- <a id="contract-refusals-admission-origin"></a>**`origin`** (string): Admission authority. Current pre-launch capacity refusals use `runner_host`.
- <a id="contract-refusals-admission-field"></a>**`field`** (string): The capacity rule's field name, including actor policy ownership where retained.
- <a id="contract-refusals-admission-actual"></a>**`actual`** (integer): Measured submitted count in the named unit.
- <a id="contract-refusals-admission-maximum"></a>**`maximum`** (integer): Maximum accepted count in the same unit; embedded-NUL rules use zero.
- <a id="contract-refusals-admission-unit"></a>**`unit`** (string): `utf8_bytes` counts encoded string bytes, `items` counts collection members, and `nul_bytes` counts embedded zero bytes in a native C-string input. Admitted vocabulary: closed; displayed list: exhaustive: `"utf8_bytes"`, `"items"`, `"nul_bytes"`.
- <a id="contract-refusals-admission-step_id"></a>**`step_id`** (string?): Associated step label when it is independently safe to echo; withheld when the label itself fails its bound.
- <a id="contract-refusals-admission-step_index"></a>**`step_index`** (integer?): Flattened probe position when the capacity rule refers to a probe. The host reconstructs phase/action paths from the original plan.
- <a id="contract-refusals-admission-parameter_key"></a>**`parameter_key`** (string?): Affected parameter key only when it can be echoed in full within its own key bound. Key failures withhold the key; value failures may retain a safe key.
- <a id="contract-refusals-admission-index"></a>**`index`** (integer?): Associated item position, such as argv or phase position, supplied by the specific capacity rule.

<a id="contract-refusals-admission-echo"></a>
#### Sanitize every echoed field

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at capacity-refusal reply assembly. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Independently inspect every echoed metadata value: replace an unsafe specimen_id with <admission_refused>, omit unsafe run_kind, use unknown for unsafe ordinary policy format, drop unsafe override paths, and withhold unsafe step IDs or parameter keys. Preserve the exact capacity counts.

A parameter key can fit the parameter capacity yet exceed the smaller path-component bound. Such a refusal may retain admission_failure.parameter_key while request_failure.path is null.

<a id="contract-refusals-admission-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Capacity refusal](#contract-refusals-admission) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Context: Review of the named producer branches. Evidence limit: The cited controls cover actor parameter count, UTF-8 and NUL boundaries, safe keys and path withholding. [Evidence details](CONTRACT.md#contract-refusals-admission-support-details).

<a id="contract-refusals-examples"></a>
### Refusal and unavailable-prediction examples

<a id="contract-refusals-examples-misspelling"></a>
#### Misspelled capture request

Given a correctly asserted ordinary specimen, a policy member `capture_compiled_profiel` is an unknown field. The host returns `bad_request`, with code `unknown_field` and path `["policy","capture_compiled_profiel"]`; the controller exits 1. A worker or validator is not launched for this refusal. Correcting the spelling to `capture_compiled_profile: true` also requires a valid `capture_nonce`.

A target-absence check made by a teaching control is separate evidence of the file state. The structured refusal identifies the stopped admission boundary.

<a id="contract-refusals-examples-absent_path"></a>
#### Absent query path and successful creation

A paired probe can query `file-write-create` with a path that does not exist at planning time, then attempt `file/create` at that path. The planner reports `prediction_unavailable`; the attempt remains eligible to run. A successful native create/open and an independent newly-created-file check answer different observations. Later realpath diagnostics can resolve a path the earlier query planner could not resolve.

<a id="contract-refusals-examples-workflow"></a>
#### Refusal correction workflows

The capture correction chain changes the misspelled capture option, then supplies a valid nonce, then reaches application and capture. The same intent is exercised through CLI and direct-host entries. Each refused input retains its first diagnostic and no child effect; each successful correction retains its request, reply and independently checked target effect.

<a id="contract-refusals-examples-workflow-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Refusal correction workflows](#contract-refusals-examples-workflow).** Controller refusals precede invocation at their own preparation boundaries. Context: Static review of the cited producer and assertion branches. Evidence limit: This owner describes the concrete correction chain; the guide presentation has its own workflow validation. [Evidence details](CONTRACT.md#contract-refusals-examples-workflow-disposition_support-details).

<a id="contract-refusals-examples-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Refusal and unavailable-prediction examples](#contract-refusals-examples) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Context: Review of the named producer branches. Evidence limit: The request corpus checks refusal fields; the correction workflow and independent file effects have their own support. [Evidence details](CONTRACT.md#contract-refusals-examples-support-details).

<a id="contract-refusals-later"></a>
### Failures after invocation

Later failures have different consequences from pre-child input refusal. Their owning transport, lifecycle and reporting records preserve the boundary actually observed.

<a id="contract-refusals-later-boundaries"></a>
#### Distinguish a stopped boundary

A client `xpc_timeout` records expiry of the client's wait without a host reply. A host `runner_timeout` may arrive in a successfully delivered client reply, with client exit 0 and controller exit 1.

Worker or validator launch failure belongs to the respective child record. Preserve the records that were actually received while reading each failure at its own scope.

<a id="contract-refusals-later-boundaries-disposition_support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Distinguish a stopped boundary](#contract-refusals-later-boundaries).** Delivery/capture precedence, successive reporting writers and controller reply admission retain separate consequences. Evidence limit: Constructed writer and reader controls, source-built child controls and native selected-app outcomes retain their individual evidence grades. [Evidence details](CONTRACT.md#contract-refusals-later-boundaries-disposition_support-details).
<!-- END GENERATED CONTRACT refusals -->

## Read invocation and transport

Enter through `data.runner_client`. Read controller process observations separately from admitted client statements about acquisition and submission. The complete exchange is in [ARCHITECTURE](ARCHITECTURE.md#contract-transport-delivery).

<!-- BEGIN GENERATED CONTRACT transport -->
<a id="contract-transport"></a>
## Delivery to the host

The controller, client and host report different boundaries. A client can hold a reservation without invoking execution, invoke execution without receiving a reply, or receive bytes that its controller refuses to interpret.

<a id="contract-transport-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Delivery to the host](#contract-transport) and its descendants.** Source defines all imported fields, reservation state transitions, capture gates, preservation and deadline boundaries. Controlled tests establish retry/invocation accounting, connection binding, bound-control admission, byte preservation and delivery-error precedence. Context: Read the cited producer/receiver declarations and branches; check citations identify the assertions read. Evidence limit: The Swift session checks inject clock, scheduler and connection boundaries. Rust process controls use controlled child programs. Live XPC, signed foreign-host nonreceipt and large native replies require separate execution evidence. [Evidence details](CONTRACT.md#contract-transport-support-details).

<a id="contract-transport-capture"></a>
### Client capture

Record `capture`: `PWRunnerClientCapture`.

- <a id="contract-transport-capture-kind"></a>**`kind`** (string): `runner_client_capture` identifies the client observation record.
- <a id="contract-transport-capture-contract"></a>**`contract`** (string): Client producer’s public identity. The controller admits it independently of the embedded host reply’s producer.
- <a id="contract-transport-capture-client_pid"></a>**`client_pid`** (integer): PID reported by the runner-client process; distinct from every host, worker and validator PID.
- <a id="contract-transport-capture-clock"></a>**`clock`** (string): `mach_continuous_time_ns` names the capture’s continuous-clock readings.
- <a id="contract-transport-capture-clock_available"></a>**`clock_available`** (boolean): Whether the client retained a usable monotonic continuous clock through its terminal decision. False accompanies a clock_error local failure.
- <a id="contract-transport-capture-started_continuous_ns"></a>**`started_continuous_ns`** (integer?): Client session’s initial valid clock reading in nanoseconds, when available.
- <a id="contract-transport-capture-deadline_continuous_ns"></a>**`deadline_continuous_ns`** (integer?): Absolute deadline in the same clock coordinate, inherited from the controller or derived locally when invoked directly.
- <a id="contract-transport-capture-ended_continuous_ns"></a>**`ended_continuous_ns`** (integer?): Last valid sample at terminal completion; absent after clock failure.
- <a id="contract-transport-capture-timeout_ms"></a>**`timeout_ms`** (integer): Positive nominal allowance supplied to the client, in milliseconds. The inherited absolute deadline accounts for time already spent before the session starts.
- <a id="contract-transport-capture-attempts"></a>**`attempts`** (array of [Acquisition attempt](#contract-transport-acquisition)): Acquisition attempts in invocation order, with one-based ordinals and unique attempt UUIDs.
- <a id="contract-transport-capture-acquisition_stop"></a>**`acquisition_stop`** (string): `granted`, `overall_deadline`, `attempt_limit`, `protocol_error` or `local_error`. Granted remains true even if a later pre-invocation stop prevents submission.
- <a id="contract-transport-capture-submission"></a>**`submission`** ([Submission observation](#contract-transport-invocation)): The client’s irreversible execution-invocation observation.
- <a id="contract-transport-capture-terminal"></a>**`terminal`** (string): One of `runner_reply`, `submission_refused`, `xpc_error`, `xpc_timeout`, `acquisition_failed`, `protocol_error` or `local_error`, naming the client’s final event.
- <a id="contract-transport-capture-error"></a>**`error`** ([Client error](#contract-transport-error)?): Bounded client-local or XPC diagnostic associated with a failure terminal.
- <a id="contract-transport-capture-runner_reply"></a>**`runner_reply`** ([Retained host reply](#contract-transport-retained_reply)?): Host-result bytes accepted by the client before its deadline. Presence establishes receipt of the result callback; the controller separately admits the frame and evidence.
- <a id="contract-transport-capture-submission_refusal"></a>**`submission_refusal`** ([Retained control observation](#contract-transport-control_observation)?): Count/hash and, after control admission, status and reason of a host submission refusal. Malformed control bytes retain only count/hash.

**timeout_ms.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-transport-capture-timeout_ms-positive"></a>Positive effective allowance | Requires `capture.timeout_ms` > `0`. |

**attempts.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-transport-capture-attempts-bounded"></a>Bounded acquisition count | Requires count(`capture.attempts`) ≤ `256 items` (`reservation_attempts`) . |

<a id="contract-transport-acquisition"></a>
### Acquisition attempt

Record `acquisition`: `PWRunnerAcquisitionAttempt`.

- <a id="contract-transport-acquisition-ordinal"></a>**`ordinal`** (integer): One-based position in the capture’s acquisition-attempt array.
- <a id="contract-transport-acquisition-attempt_id"></a>**`attempt_id`** (string): UUID generated for this attempt. The client requires matching acquisition replies.
- <a id="contract-transport-acquisition-started_elapsed_ms"></a>**`started_elapsed_ms`** (integer?): Elapsed whole milliseconds from the client session’s initial continuous-clock sample at attempt start, when available.
- <a id="contract-transport-acquisition-ended_elapsed_ms"></a>**`ended_elapsed_ms`** (integer?): Elapsed whole milliseconds when this attempt ended, when available; a later clock fault can leave it absent.
- <a id="contract-transport-acquisition-outcome"></a>**`outcome`** (string): `granted`, `occupied`, `transport_error`, `timeout`, `protocol_error` or `local_error`. Only acquisition transport loss, occupied status and an RPC timeout can lead to another acquisition attempt.
- <a id="contract-transport-acquisition-control"></a>**`control`** ([Retained control observation](#contract-transport-control_observation)?): Received reservation-control count/hash and any admitted peer fields.
- <a id="contract-transport-acquisition-error"></a>**`error`** ([Client error](#contract-transport-error)?): Failure diagnostic for this attempt. A granted or occupied attempt instead carries its admitted control.

<a id="contract-transport-control_observation"></a>
### Retained control observation

Record `control_observation`: `PWRunnerControlObservation`.

- <a id="contract-transport-control_observation-bytes_received"></a>**`bytes_received`** (integer): Byte count of the complete received control data, including a control that fails admission.
- <a id="contract-transport-control_observation-sha256"></a>**`sha256`** (string (hex)): SHA-256 of those complete bytes, projected as lowercase hexadecimal.
- <a id="contract-transport-control_observation-status"></a>**`status`** (string?): Control status retained only after the client admits the control.
- <a id="contract-transport-control_observation-host_pid"></a>**`host_pid`** (integer?): Admitted peer-reported host PID.
- <a id="contract-transport-control_observation-host_instance"></a>**`host_instance`** (string?): Admitted peer-reported admission-owner UUID.
- <a id="contract-transport-control_observation-lease_ms"></a>**`lease_ms`** (integer?): Admitted grant lifetime when the control carries one.
- <a id="contract-transport-control_observation-reason"></a>**`reason`** (string?): Admitted submission-refusal reason when present.

<a id="contract-transport-invocation"></a>
### Submission observation

Record `invocation`: `PWRunnerSubmission`.

- <a id="contract-transport-invocation-state"></a>**`state`** (string): `not_invoked` until the client crosses its execution-call boundary, then permanently `invoked`.
- <a id="contract-transport-invocation-invoked_elapsed_ms"></a>**`invoked_elapsed_ms`** (integer?): Elapsed whole milliseconds at that boundary. Absent for not_invoked; clock-failure capture retains only a value actually sampled.

<a id="contract-transport-retained_reply"></a>
### Retained host reply

Record `retained_reply`: `PWRunnerReplyCapture`.

- <a id="contract-transport-retained_reply-bytes_received"></a>**`bytes_received`** (integer): Length of the complete host-result Data received by the client.
- <a id="contract-transport-retained_reply-bytes_retained"></a>**`bytes_retained`** (integer): Length of its retained prefix, the smaller of bytes_received and <!-- span limits.client_reply_retention.value_unit -->96,468,992 bytes<!-- /span -->.
- <a id="contract-transport-retained_reply-truncated"></a>**`truncated`** (boolean): True exactly when bytes_retained is smaller than bytes_received. The controller refuses a truncated host frame before structural decoding.
- <a id="contract-transport-retained_reply-data_base64"></a>**`data_base64`** (string (base64)): Exact retained host bytes, kept as bytes internally and rendered as base64 at public JSON projection.

**truncated.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-transport-retained_reply-truncated-arithmetic"></a>Retention arithmetic | Requires (`retained_reply.truncated` = `retained_reply.bytes_retained` < `retained_reply.bytes_received` and `retained_reply.bytes_retained` ≤ `retained_reply.bytes_received` and `retained_reply.bytes_retained` ≤ `96,468,992 bytes` (`client_reply_retention`) and implies(`retained_reply.bytes_received` ≤ `96,468,992 bytes` (`client_reply_retention`) , `retained_reply.bytes_retained` = `retained_reply.bytes_received`) and implies(`retained_reply.bytes_received` > `96,468,992 bytes` (`client_reply_retention`) , `retained_reply.bytes_retained` = `96,468,992 bytes` (`client_reply_retention`) )). |

**data_base64.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-transport-retained_reply-data_base64-extent"></a>Exact retained byte extent | Requires byte_length(`retained_reply.data_base64`) = `retained_reply.bytes_retained`. |

<a id="contract-transport-retained_reply-source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Retained host reply](#contract-transport-retained_reply) and its descendants.** The constructor retains the bounded Data prefix, its original and retained lengths, and their inequality flag. [Evidence details](CONTRACT.md#contract-transport-retained_reply-source-details).

<a id="contract-transport-error"></a>
### Client error

Record `error`: `PWRunnerTransportError`.

- <a id="contract-transport-error-stage"></a>**`stage`** (string): Boundary at which the client reported the error: `local`, `acquisition` or `submission`.
- <a id="contract-transport-error-reason"></a>**`reason`** (string): Machine classification for the boundary, including `clock_error`, `encoding_failed`, `input_read_failed`, `xpc_error`, `proxy_type_mismatch`, `rpc_timeout`, `overall_deadline`, `attempt_limit`, `control_too_large`, `unsupported_protocol` and `invalid_control`. The capture reader checks stage/reason/terminal compatibility.
- <a id="contract-transport-error-domain"></a>**`domain`** (string?): Native NSError domain when available, bounded to <!-- span limits.client_error_domain.value_unit -->128 UTF-8 bytes<!-- /span --> without splitting a scalar.
- <a id="contract-transport-error-code"></a>**`code`** (integer?): Native NSError numeric code when available. Its value belongs to that error domain.
- <a id="contract-transport-error-message"></a>**`message`** (string): Native debug diagnostic when available, otherwise localized or supplied client text; bounded to <!-- span limits.client_error_message.value_unit -->1,024 UTF-8 bytes<!-- /span --> without splitting a scalar.
- <a id="contract-transport-error-domain_truncated"></a>**`domain_truncated`** (boolean): Whether the original native domain exceeded its retained-byte allowance.
- <a id="contract-transport-error-message_truncated"></a>**`message_truncated`** (boolean): Whether the original message exceeded its retained-byte allowance.

<a id="contract-transport-client"></a>
### Controller observation of the client process

Record `client`: `rust.RunnerClientRun`.

- <a id="contract-transport-client-argv"></a>**`argv`** (array of string): Controller-selected client executable and arguments, including connection flags, deadline and stdin-request mode.
- <a id="contract-transport-client-started_at_unix_ms"></a>**`started_at_unix_ms`** (integer): Controller wall-clock milliseconds immediately before launching and feeding the client.
- <a id="contract-transport-client-ended_at_unix_ms"></a>**`ended_at_unix_ms`** (integer): Controller wall-clock milliseconds after child-output collection and request-writer completion. Wall-clock reversals remain visible.
- <a id="contract-transport-client-exit_code"></a>**`exit_code`** (integer): Client process exit code, or 1 when process status supplies no numeric exit code. A zero client exit accompanies delivery of host-result bytes and leaves host outcome to its own report.
- <a id="contract-transport-client-request_delivery"></a>**`request_delivery`** ([Request stdin delivery](#contract-transport-request_delivery) ∪ null): Controller’s stdin-writer observation for the one held serialized request.
- <a id="contract-transport-client-transport"></a>**`transport`** ([Transport alternatives](#contract-transport-transport_value) ∪ null): Admitted typed client capture or a rejected retained-byte projection; null when no bytes are retained.
- <a id="contract-transport-client-transport_admission"></a>**`transport_admission`** (string): `accepted`, `missing`, `unsupported`, `malformed` or `delivery_failed`, naming the controller’s client-capture admission decision.
- <a id="contract-transport-client-transport_error"></a>**`transport_error`** (string ∪ null): Diagnostic explaining capture refusal or absence; null for accepted capture.
- <a id="contract-transport-client-submission"></a>**`submission`** (string): Admitted capture’s invoked/not_invoked state, otherwise `unknown`.
- <a id="contract-transport-client-runner_reply_error"></a>**`runner_reply_error`** (string ∪ null): Diagnostic for a truncated, unsupported or malformed embedded host frame. Its exact retained bytes remain in the admitted client capture.
- <a id="contract-transport-client-stdout_parse_error"></a>**`stdout_parse_error`** (string ∪ null): Binary frame/schema/producer decoding diagnostic when decoding was attempted. Retention loss is recorded independently before decoding.
- <a id="contract-transport-client-stdout_truncated"></a>**`stdout_truncated`** (boolean): Whether complete client stdout exceeded the retained prefix allowance.
- <a id="contract-transport-client-stdout_capture_error"></a>**`stdout_capture_error`** (string ∪ null): Retention-loss diagnostic; this blocks capture decoding even if the prefix resembles a valid frame.
- <a id="contract-transport-client-stdout_bytes_received"></a>**`stdout_bytes_received`** (integer ∪ null): Original stdout byte count after complete process-output collection.
- <a id="contract-transport-client-stdout_bytes_retained"></a>**`stdout_bytes_retained`** (integer ∪ null): Retained stdout prefix length, before binary frame admission.
- <a id="contract-transport-client-stderr_bytes_received"></a>**`stderr_bytes_received`** (integer ∪ null): Original stderr byte count after complete process-output collection.
- <a id="contract-transport-client-stderr_bytes_retained"></a>**`stderr_bytes_retained`** (integer ∪ null): Retained stderr prefix length before diagnostic text conversion.
- <a id="contract-transport-client-capture_limit_bytes"></a>**`capture_limit_bytes`** (integer): Per-stream prefix-retention allowance, currently <!-- span limits.controller_output.value_unit -->285,212,672 bytes<!-- /span --> for the runner client.
- <a id="contract-transport-client-stderr"></a>**`stderr`** (string): Retained stderr converted to UTF-8 text with replacement for invalid bytes.
- <a id="contract-transport-client-stderr_truncated"></a>**`stderr_truncated`** (boolean): Whether complete stderr exceeded its retained prefix allowance.

<a id="contract-transport-client-admit"></a>
#### Admit client and host observations

[Controller](CONTRACT.md#contract-identity-definitions-controller) checks at completed client stdout and nested host frame. Entry: cli run, runner verify. Recipient: cli caller. Reports: run envelope, runner verify. Uses [Exact admission identity](CONTRACT.md#contract-identity-public-contract). The client process and input writer completed collection. Give request-delivery failure precedence; otherwise refuse retention loss, missing capture, unsupported producer/schema or inconsistent capture. Admit the host frame separately only when its retained bytes are complete. Keep raw received bytes at the boundary that received them.

Delivery failure yields controller `tool_error` and exit 2 while retaining available client bytes. Admitted capture semantics check chronology, UUIDs, terminal combinations, control fields and retained lengths. Unsupported or malformed capture withholds submission knowledge and host interpretation. An admitted capture’s `runner_reply` can still be refused as `runner_reply_truncated`, `unsupported_runner_response` or `malformed_runner_response`. Host semantic admission follows structural decoding.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-transport-client-admit-delivery"></a>Input delivery takes precedence | Requires implies((present(`client.request_delivery`) and present(`client.request_delivery.error`)), (`client.transport_admission` = `"delivery_failed"` and `client.transport_error` = `client.request_delivery.error` and `client.submission` = `"unknown"` and absent(`client.stdout_parse_error`) and absent(`client.runner_reply_error`))). |
| <a id="contract-transport-client-admit-retention"></a>Retention loss precedes decoding | Requires implies((not ((present(`client.request_delivery`) and present(`client.request_delivery.error`))) and present(`client.stdout_capture_error`)), (`client.transport_admission` = `"malformed"` and `client.transport_error` = `client.stdout_capture_error` and `client.submission` = `"unknown"` and absent(`client.stdout_parse_error`) and absent(`client.runner_reply_error`))). |
| <a id="contract-transport-client-admit-missing"></a>Empty retained capture | Requires implies((not ((present(`client.request_delivery`) and present(`client.request_delivery.error`))) and absent(`client.stdout_capture_error`) and `client.stdout_bytes_retained` = `0`), (`client.transport_admission` = `"missing"` and `client.transport_error` = `"runner client produced no capture"` and `client.submission` = `"unknown"` and absent(`client.stdout_parse_error`) and absent(`client.runner_reply_error`))). |

<a id="contract-transport-client-admit-selection_source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Admit client and host observations](#contract-transport-client-admit).** Completed collection first selects input-delivery error, then retained-output loss, then an empty capture. These paths preserve unknown submission and skip both frame decoders. [Evidence details](CONTRACT.md#contract-transport-client-admit-selection_source-details).

<a id="contract-transport-request_delivery"></a>
### Request stdin delivery

Record `request_delivery`: `rust.RequestDelivery`.

- <a id="contract-transport-request_delivery-bytes_written"></a>**`bytes_written`** (integer): Number of request bytes accepted by the child’s stdin pipe according to the controller’s writes.
- <a id="contract-transport-request_delivery-error"></a>**`error`** (string ∪ null): First terminal write error, including a zero-length write. Null records successful delivery by the writer; child receipt remains a separate observation.

<a id="contract-transport-transport_value"></a>
### Transport alternatives

Record `transport_value`: `rust.TransportCapture`.

The Rust enum is untagged: JSON contains the chosen alternative’s fields directly. `transport_admission` names which interpretation the controller established.

| Alternative | Record |
| --- | --- |
| `Rejected` | [Rejected client stdout](#contract-transport-rejected) |
| `Typed` | [Client capture](#contract-transport-capture) |

<a id="contract-transport-rejected"></a>
### Rejected client stdout

Record `rejected`: `rust.TransportCapture.Rejected`.

- <a id="contract-transport-rejected-format"></a>**`format`** (string): `porcelain` identifies the expected client-output encoding at this collection boundary.
- <a id="contract-transport-rejected-data_base64"></a>**`data_base64`** (string (base64)): Exact retained stdout prefix, projected as base64. It can contain arbitrary, malformed or foreign bytes.
<!-- END GENERATED CONTRACT transport -->

## Read policy observations

Import inventories and fallback captures describe their own reads or compiler invocations. They do not establish which files a worker compiler later read or whether a worker applied the policy. [Request policy declarations](REQUEST.md#contract-policy-spec) identify what was supplied.

<!-- BEGIN GENERATED CONTRACT policy -->
<a id="contract-policy-imports"></a>
### Literal import inventory

Record `imports`: `rust.ImportInventory`.

Absolute import names are checked as supplied. Other names are sought first under `/System/Library/Sandbox/Profiles`, then `/usr/share/sandbox`, with the literal name unchanged. The resolver follows literal imports recursively; an unevaluable import argument, unreadable/nonregular file or invalid UTF-8 scan input records an incomplete inventory.

- <a id="contract-policy-imports-records"></a>**`records`** (array of [One import observation](#contract-dossier-import_record)): Observed import records sorted by resolved path (empty for unresolved), then literal name. Each resolved file is opened once, checked as a regular file, and its held bytes are both hashed and scanned. Canonical resolved files and unresolved names are deduplicated.
- <a id="contract-policy-imports-truncated"></a>**`truncated`** (boolean): True when the walk reached its <!-- span limits.helper_import_depth.value_unit -->8 levels<!-- /span --> depth bound or <!-- span limits.helper_import_count.value_unit -->64 records<!-- /span --> record bound; retained records describe the partial walk.
- <a id="contract-policy-imports-cycle"></a>**`cycle`** (array of string ∪ null): First cycle found by revisiting a canonical path already in the active traversal chain, reported in literal import-name order. Null means the walk found no cycle.
- <a id="contract-policy-imports-policy_closure_sha256"></a>**`policy_closure_sha256`** (string): SHA-256 of source bytes, byte 0x1F, then newline-joined sorted strings of each successfully hashed resolved path, one space and its SHA-256. The separator is included for an empty inventory. Failed imports remain error records and contribute no path/hash line.

<a id="contract-policy-imports-holds"></a>
#### Separate reads and their identities

[Controller](CONTRACT.md#contract-identity-definitions-controller), [Compiler helper](CONTRACT.md#contract-identity-definitions-helper), [Worker](CONTRACT.md#contract-identity-definitions-worker) acts at policy preparation and import reads. Entry: cli run, standalone helper, xpc execute. Recipient: caller, report reader. Reports: run envelope, helper envelope, runner reply. Bind each digest to the bytes held by its producing read. The controller dossier walk, fallback helper walk and worker native compiler perform their own reads. Preserve import errors and bounds beside each inventory.

Files named by imports can change between these independent reads. A literal inventory describes the producer's walk; the worker compiled-profile receipt has its own observation boundary.

<a id="contract-policy-imports-native_import_agreement"></a>
#### Literal import evidence scope

The inventory walks literal imports using its documented two-directory search order and records the bytes read during that walk. The directory order is a platform convention. Native compilation examples establish their selected literal imports; collision precedence, macro-generated dependencies and files changing between independent reads retain their own evidence limits.

<a id="contract-policy-imports-native_import_agreement-disposition_support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Literal import evidence scope](#contract-policy-imports-native_import_agreement).** The scanner follows IMPORT_SEARCH_PATHS and records each resolved file read. Evidence limit: The source records that collision precedence was not established by the cited platform exploration. [Evidence details](CONTRACT.md#contract-policy-imports-native_import_agreement-disposition_support-details).

<a id="contract-policy-imports-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Literal import inventory](#contract-policy-imports) and its descendants.** The adjacent field meanings and operations follow the named implementation. Evidence limit: Full inventory traversal and hashing implementation read. Native search-order observations are inherited from the source comments, not reproduced here. [Evidence details](CONTRACT.md#contract-policy-imports-support-details).

<a id="contract-policy-fallback"></a>
### Fallback helper capture

Record `fallback`: `rust.PolicyCheckCapture`.

- <a id="contract-policy-fallback-status"></a>**`status`** (string): Capture result, or the exact normalized_outcome from a supported helper envelope. Current capture statuses are unavailable, capture_error, parse_error, tool_error and invalid_reply. Admitted vocabulary: open; displayed list: illustrative: `"unavailable"`, `"capture_error"`, `"parse_error"`, `"tool_error"`, `"invalid_reply"`, `"ok"`, `"compile_error"`, `"setup_error"`, `"bad_request"`, `"policy_too_large"`. Unfamiliar values: A nonempty unfamiliar helper outcome is copied when kind and public identity are supported; its meaning remains producer-supplied.
- <a id="contract-policy-fallback-tool_exit_code"></a>**`tool_exit_code`** (integer): Helper process exit code, or the capture's fallback value when unavailable.
- <a id="contract-policy-fallback-envelope"></a>**`envelope`** (JSON value ∪ null): Whole parsed helper envelope retained unchanged when stdout parsed, including unsupported envelopes. Null means no retained parsed object.
- <a id="contract-policy-fallback-stdout_raw"></a>**`stdout_raw`** (string ∪ null): Retained textual stdout used for capture diagnosis.
- <a id="contract-policy-fallback-stdout_parse_error"></a>**`stdout_parse_error`** (string ∪ null): Parse diagnosis when retained stdout could not be decoded as the helper JSON value.
- <a id="contract-policy-fallback-stdout_truncated"></a>**`stdout_truncated`** (boolean): Whether stdout retention truncated the child's output; truncation prevents interpreting a parsed prefix as the complete reply.
- <a id="contract-policy-fallback-stdout_capture_error"></a>**`stdout_capture_error`** (string ∪ null): Capture loss diagnosis, which takes precedence over parsing and helper interpretation.
- <a id="contract-policy-fallback-stdout_bytes_received"></a>**`stdout_bytes_received`** (integer ∪ null): Count of stdout bytes observed by capture.
- <a id="contract-policy-fallback-stdout_bytes_retained"></a>**`stdout_bytes_retained`** (integer ∪ null): Count of stdout bytes retained within the capture limit.
- <a id="contract-policy-fallback-stderr_bytes_received"></a>**`stderr_bytes_received`** (integer ∪ null): Count of stderr bytes observed by capture.
- <a id="contract-policy-fallback-stderr_bytes_retained"></a>**`stderr_bytes_retained`** (integer ∪ null): Count of stderr bytes retained within the capture limit.
- <a id="contract-policy-fallback-capture_limit_bytes"></a>**`capture_limit_bytes`** (integer): Per-stream retention limit, <!-- span limits.policy_helper_output.value_unit -->8,388,608 bytes<!-- /span -->.
- <a id="contract-policy-fallback-stderr"></a>**`stderr`** (string): Retained stderr text, including diagnostic output when the helper produced no envelope.
- <a id="contract-policy-fallback-stderr_truncated"></a>**`stderr_truncated`** (boolean): Whether stderr exceeded its retained capture capacity.

<a id="contract-policy-fallback-classify"></a>
#### Fallback eligibility and classification

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at admitted client capture after xpc error. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Invoke the fallback helper when client transport admission is accepted, request delivery has no error, and the admitted client capture has terminal xpc_error. Deliver the held request on stdin. Report launch or delivery failure as unavailable; only after successful launch and delivery apply capture_error, parse_error, absent-output tool_error, then raw envelope identity/kind validation. Copy a supported envelope's nonempty outcome into status.

Support requires kind `sbpl_check`, the current non-unbound `build.contract`, and a nonempty string normalized_outcome. The capture preserves the envelope and helper process exit independently; compiler observations retain their own process owner.

<a id="contract-policy-fallback-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Fallback helper capture](#contract-policy-fallback) and its descendants.** The adjacent field meanings and operations follow the named implementation. Context: Review of the named producer branches. Evidence limit: Capture parsing, fallback eligibility and call sites, supported-outcome control and constructed fallback-selection control read; no execution credited. The malformed actor-mode policy-object path is source-read. Detailed text-byte capture mechanics are shared with the transport surface. [Evidence details](CONTRACT.md#contract-policy-fallback-support-details).

<a id="contract-policy-actor_check"></a>
### Per-actor fallback capture

Record `actor_check`: `rust.ActorPolicyCheck`.

When fallback is eligible, the controller checks each actor carrying a policy object in request order, sending a separate policy-only request. A malformed mode remains a host-admission question; the controller collected these policy objects before host execution.

- <a id="contract-policy-actor_check-actor_id"></a>**`actor_id`** (string ∪ null): Actor label copied from the policy-bearing actor declaration when it is a string; null otherwise.
- <a id="contract-policy-actor_check-policy_check"></a>**`policy_check`** ([Fallback helper capture](#contract-policy-fallback)): Independent helper capture for this actor's selected policy object.

<a id="contract-policy-actor_check-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Per-actor fallback capture](#contract-policy-actor_check) and its descendants.** The adjacent field meanings and operations follow the named implementation. [Evidence details](CONTRACT.md#contract-policy-actor_check-support-details).
<!-- END GENERATED CONTRACT policy -->

## Read predictions and attempts

Enter through the host report’s step list, preserving phase and actor association. Read provenance and operands before returns, then the comparison’s observation and ordering assessments. [Paired request operands](REQUEST.md#contract-probes-step) explain why the two channels can concern different targets.

<!-- BEGIN GENERATED CONTRACT steps -->
<a id="contract-steps"></a>
## Predictions, attempts and comparison

Actor: [Runner host](CONTRACT.md#contract-identity-definitions-host). Boundary: step evidence assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply.

<a id="contract-steps-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Predictions, attempts and comparison](#contract-steps) and its descendants.** Imported fields receive their producer meanings, channel origins and observation boundaries. Context: Read definitions alongside assembly, native payload decoding, the worker's descriptor-path capture and path enrichment. Evidence limit: Source support; specific rules have separately graded check owners. [Evidence details](CONTRACT.md#contract-steps-support-details).

<a id="contract-steps-step"></a>
### Probe result

Record `step`: `PWRunnerStepResult`.

- <a id="contract-steps-step-phase_id"></a>**`phase_id`** (string): Identifier of the containing declared phase; normalized flat-step requests use `main`.
- <a id="contract-steps-step-step_id"></a>**`step_id`** (string): Identifier of the declared probe action, associated within its phase and actor.
- <a id="contract-steps-step-sandbox_check"></a>**`sandbox_check`** ([Query-channel result](#contract-steps-query)): Query-channel result from the associated validator record or a synthetic unavailable result.
- <a id="contract-steps-step-attempt"></a>**`attempt`** ([Attempt-channel result](#contract-steps-attempt)): Worker action result, including publication provenance and retained native observations.
- <a id="contract-steps-step-comparison"></a>**`comparison`** ([Comparison assessment](#contract-steps-comparison)?): Host assessment of observation, submitted scopes and reply.phases[p].ordering.
- <a id="contract-steps-step-actor_id"></a>**`actor_id`** (string?): Actor whose process owns this probe in actor form; omitted in ordinary execution.

<a id="contract-steps-query"></a>
### Query-channel result

Record `query`: `PWRunnerSandboxCheckResult`.

- <a id="contract-steps-query-result_source"></a>**`result_source`** (string?): `validator` means a uniquely associated accepted record supplied the result; `synthetic` means the host constructed an unavailable result.
- <a id="contract-steps-query-native_rc"></a>**`native_rc`** (integer; present when result_source has a value; may be null): Native return carried by an associated allow, deny or error record. Synthetic results carry explicit null when result_source is present.
- <a id="contract-steps-query-missing_reason"></a>**`missing_reason`** (string?): `query_not_requested` for a planner exclusion, `validator_not_invoked` when collection never ran, or `validator_no_verdict` when it produced no associated record.
- <a id="contract-steps-query-rc"></a>**`rc`** (integer): An associated record supplies its carried return, or -1 if that record omits the return. A planner exclusion uses -1. With no associated verdict, the host supplies 0 and an error outcome. Provenance and outcome qualify this number.
- <a id="contract-steps-query-outcome"></a>**`outcome`** (string): `allow` or `deny` is the associated answer; `unsupported_operation` retains that diagnostic. Other accepted diagnostics project as `error`. Planner exclusion yields `prediction_unavailable`.
- <a id="contract-steps-query-pid"></a>**`pid`** (integer ∪ null): PID targeted by this phase's validator collection when worker output supplies it. The ordering assessment states whether the required live-worker interval was established.
- <a id="contract-steps-query-operation"></a>**`operation`** (string): The admitted query operation.
- <a id="contract-steps-query-filter_kind"></a>**`filter_kind`** (string): The normalized query filter name.
- <a id="contract-steps-query-filter_value"></a>**`filter_value`** (string ∪ null): The supplied request value. A none-filter native query uses no value even when this echoed field is present.
- <a id="contract-steps-query-filter_type_id"></a>**`filter_type_id`** (integer ∪ null): Native filter identifier retained from the associated record when supplied.
- <a id="contract-steps-query-errno"></a>**`errno`** (integer ∪ null): Errno retained from the validator record, belonging to the query channel.
- <a id="contract-steps-query-error"></a>**`error`** (string ∪ null): The validator diagnostic or host explanation of an unavailable result.
- <a id="contract-steps-query-path_diagnostics"></a>**`path_diagnostics`** ([Query path observations](#contract-steps-query_paths)?): Host observations after orchestration for a nonempty path-filter value.

<a id="contract-steps-verdict"></a>
### Accepted validator record

Record `verdict`: `ValidatorVerdict`.

- <a id="contract-steps-verdict-step_id"></a>**`step_id`** (string ∪ null): Step identifier carried by the frame, or null when absent. Unknown, duplicate and unassigned records remain retained as received.
- <a id="contract-steps-verdict-operation"></a>**`operation`** (string?): Operation carried by the frame, omitted when absent.
- <a id="contract-steps-verdict-filter_type"></a>**`filter_type`** (string?): Filter spelling carried by the frame, omitted when absent.
- <a id="contract-steps-verdict-filter_type_id"></a>**`filter_type_id`** (integer?): Numeric native filter identifier carried by the frame, omitted when absent.
- <a id="contract-steps-verdict-filter_value"></a>**`filter_value`** (string?): Value carried by the frame, omitted when absent; a NONE query has no native filter value.
- <a id="contract-steps-verdict-rc"></a>**`rc`** (integer?): Native or diagnostic return carried by the frame, omitted when absent.
- <a id="contract-steps-verdict-errno"></a>**`errno`** (integer?): Query errno carried by the frame, omitted when absent.
- <a id="contract-steps-verdict-outcome"></a>**`outcome`** (string): The accepted frame's outcome string. Admitted vocabulary: open; displayed list: illustrative: `"allow"`, `"deny"`, `"error"`, `"unsupported_operation"`. Unfamiliar values: Retain an unfamiliar diagnostic outcome with its error string; assign only its recorded diagnostic meaning.
- <a id="contract-steps-verdict-error"></a>**`error`** (string?): The frame diagnostic, omitted when absent.
- <a id="contract-steps-verdict-raw_line"></a>**`raw_line`** (string): Accepted UTF-8 frame text. A receiver-owned decode-fault record retains rejected frame bytes separately.

<a id="contract-steps-attempt"></a>
### Attempt-channel result

Record `attempt`: `PWRunnerAttemptResult`.

- <a id="contract-steps-attempt-requested_kind"></a>**`requested_kind`** (string?): Declared attempt kind, echoed independently of completion.
- <a id="contract-steps-attempt-requested_action"></a>**`requested_action`** (string?): Declared action, echoed independently of completion.
- <a id="contract-steps-attempt-result_source"></a>**`result_source`** (string?): `worker` means a supported action's slot published completion; `synthetic` means the host supplied an unavailable or unsupported result.
- <a id="contract-steps-attempt-missing_reason"></a>**`missing_reason`** (string?): `attempt_not_supported`, `slot_absent` or `slot_incomplete` identifies the synthetic result's reason.
- <a id="contract-steps-attempt-lifecycle"></a>**`lifecycle`** ([Per-attempt lifecycle projection](#contract-lifecycle-attempt)?): Resolved reach, entry, completion and interruption claims under the subprocess disposition's supporting observations.
- <a id="contract-steps-attempt-fresh_read"></a>**`fresh_read`** ([Fresh-descriptor read](#contract-steps-fresh_read)?): Completed read_fresh action's open, descriptor-stat, bounded read and close observations.
- <a id="contract-steps-attempt-fresh_write"></a>**`fresh_write`** ([Fresh-descriptor write or creation](#contract-steps-fresh_write)?): Completed write_fresh or create_fresh action's native sequence and descriptor metadata.
- <a id="contract-steps-attempt-exec_observation"></a>**`exec_observation`** ([Spawned-command observation](#contract-lifecycle-exec)?): Worker observations of spawn, child wait, output collection and cleanup.
- <a id="contract-steps-attempt-rc"></a>**`rc`** (integer): Completed worker slot return; zero maps to ok. Synthetic unsupported or incomplete actions use -1. Exec can return nonzero after successful spawning because of the child's result.
- <a id="contract-steps-attempt-errno"></a>**`errno`** (integer ∪ null): Completed slot's nonzero errno, when retained. Fresh-operation details separately record their own failed calls.
- <a id="contract-steps-attempt-outcome"></a>**`outcome`** (string): A completed zero return yields `ok`. Nonzero returns map by action to `open_failed`, `read_failed`, `write_failed`, `unlink_failed`, `access_failed`, `lookup_failed`, `sysctl_failed` or `exec_failed`. Synthetic slots yield `no_completed_result` or `unsupported`.
- <a id="contract-steps-attempt-error"></a>**`error`** (string?): Action diagnostic from the completed slot or explanation of a synthetic result.
- <a id="contract-steps-attempt-requested_path"></a>**`requested_path`** (string ∪ null): Submitted target string, including service and sysctl names for those kinds.
- <a id="contract-steps-attempt-path_diagnostics"></a>**`path_diagnostics`** ([Attempt path observations](#contract-steps-attempt_paths)?): Host observations after orchestration for a nonempty file or exec target.
- <a id="contract-steps-attempt-observed_path"></a>**`observed_path`** (string ∪ null): Path observation supplied by the worker slot when available.
- <a id="contract-steps-attempt-child_pid"></a>**`child_pid`** (integer?): Completed exec slot's child PID: zero when no child was spawned. A positive value supports the comparison's spawned_child observation.
- <a id="contract-steps-attempt-child_exit_code"></a>**`child_exit_code`** (integer?): Completed exec slot's child exit code, using -1 until a normal child exit is observed.
- <a id="contract-steps-attempt-child_term_signal"></a>**`child_term_signal`** (integer?): Completed exec slot's terminating signal, using zero until a signaled child termination is observed.
- <a id="contract-steps-attempt-stdout"></a>**`stdout`** (string?): Captured child stdout, omitted when empty. The worker retains at most <!-- span limits.exec_stream.value_unit -->1,023 bytes<!-- /span --> for this stream; an overflow marker occupies part of that allowance.
- <a id="contract-steps-attempt-stderr"></a>**`stderr`** (string?): Captured child stderr, omitted when empty. The worker retains at most <!-- span limits.exec_stream.value_unit -->1,023 bytes<!-- /span --> for this stream; an overflow marker occupies part of that allowance.

<a id="contract-steps-comparison"></a>
### Comparison assessment

Record `comparison`: `PWRunnerComparison`.

- <a id="contract-steps-comparison-observation"></a>**`observation`** (string): `succeeded`, `permission_failure`, `other_failure` or `unavailable`, classified from the attempt channel by the rule below. Uses [Classify an observation](#contract-steps-assessment-observe).
- <a id="contract-steps-comparison-observation_basis"></a>**`observation_basis`** (string): Supporting observation: `spawned_child`, `completed_worker_status`, `permission_errno`, `bootstrap_permission_result` or `no_completed_worker_result`. Uses [Classify an observation](#contract-steps-assessment-observe).
- <a id="contract-steps-comparison-operation_relation"></a>**`operation_relation`** (string): `matched` means the query equals the action's mapped operation; `different` means those strings differ; `unresolved` means the mapping cannot assign a single operation. Uses [Submitted operation and target](#contract-steps-assessment-relations).
- <a id="contract-steps-comparison-target_relation"></a>**`target_relation`** (string): `same_submitted` or `different_submitted` compares submitted strings when the query filter matches the action's mapped filter and both strings exist; otherwise `unresolved`. Uses [Submitted operation and target](#contract-steps-assessment-relations).
- <a id="contract-steps-comparison-order"></a>**`order`** (string): `query_first` places this eligible prediction before this phase's attempt batch with required worker lifetime and setup established. `unestablished` retains the channels without that temporal assessment. Uses [Establish query order](#contract-steps-assessment-order).
- <a id="contract-steps-comparison-limitations"></a>**`limitations`** (array of string): Planner exclusions as `query_plan:path_unresolved_at_planning`, `query_plan:prediction_unavailable_pair` or `query_plan:unrecognized_filter_kind`. Lifecycle summaries add `attempt:started_without_result`, `attempt:not_reached`, `attempt:unsupported`, `attempt:lifecycle_unresolved` or `attempt:lifecycle_conflicting` for their corresponding noncompleted state; completed adds none. Ordinary reporting and controller checks require this closed vocabulary.

<a id="contract-steps-ordering"></a>
### Collection and release observations

Record `ordering`: `PWRunnerOrdering`.

- <a id="contract-steps-ordering-collection_closed_before_proceed"></a>**`collection_closed_before_proceed`** (boolean): The host closed this phase's collection before performing its release store.
- <a id="contract-steps-ordering-proceed_set"></a>**`proceed_set`** (boolean): The host performed this phase's release store.
- <a id="contract-steps-ordering-proceed_observed"></a>**`proceed_observed`** (boolean): The worker published acknowledgement of this phase's release.
- <a id="contract-steps-ordering-validator_disposition"></a>**`validator_disposition`** (string): `not_invoked` when the hook never ran; `not_needed` when it ran without queries; `not_spawned` when queries existed without validator output; `reaped` for confirmed reap; otherwise `unconfirmed`.
- <a id="contract-steps-ordering-worker_lifetime_established"></a>**`worker_lifetime_established`** (boolean): Host-established worker ownership through release acknowledgement. Later cleanup has its own disposition.
- <a id="contract-steps-ordering-protocol_violations"></a>**`protocol_violations`** (array of string): Sorted unique driver and assembly findings about the collection/release/acknowledgement protocol.

<a id="contract-steps-query_paths"></a>
### Query path observations

Record `query_paths`: `PWRunnerPathDiagnostics`.

- <a id="contract-steps-query_paths-observer"></a>**`observer`** (string?): `runner_host` identifies the observing component.
- <a id="contract-steps-query_paths-stage"></a>**`stage`** (string?): `after_orchestration` identifies the observation interval.
- <a id="contract-steps-query_paths-input"></a>**`input`** (string): Nonempty submitted path-filter value.
- <a id="contract-steps-query_paths-realpath_resolved"></a>**`realpath_resolved`** (string; omitted when named in same_as_input; otherwise present, possibly null): Successful host realpath result, or null when resolution failed after orchestration.
- <a id="contract-steps-query_paths-firmlink_resolved"></a>**`firmlink_resolved`** (string; omitted when named in same_as_input; otherwise present, possibly null): Firmlink-mapped realpath result, or mapped input after standard /etc, /tmp and /var substitutions when realpath failed. Null means no mapping was available.
- <a id="contract-steps-query_paths-same_as_input"></a>**`same_as_input`** (array of string): Names of available resolved fields whose UTF-8 bytes equal input; those equal-valued keys are omitted. A differing form is carried as a string; an unavailable form is explicit null.

<a id="contract-steps-attempt_paths"></a>
### Attempt path observations

Record `attempt_paths`: `PWRunnerAttemptPathDiagnostics`.

- <a id="contract-steps-attempt_paths-observer"></a>**`observer`** (string?): `runner_host` identifies the observing component.
- <a id="contract-steps-attempt_paths-stage"></a>**`stage`** (string?): `after_orchestration` identifies the observation interval.
- <a id="contract-steps-attempt_paths-input"></a>**`input`** (string): Nonempty submitted file or exec target.
- <a id="contract-steps-attempt_paths-realpath_resolved"></a>**`realpath_resolved`** (string; omitted when named in same_as_input; otherwise present, possibly null): Successful host realpath result after orchestration, following the leaf, or null when unavailable.
- <a id="contract-steps-attempt_paths-parent_realpath_resolved"></a>**`parent_realpath_resolved`** (string; omitted when named in same_as_input; otherwise present, possibly null): Realpath-resolved parent with the literal leaf appended for an eligible absolute path, or null when unavailable. A symlink leaf remains named by this form.
- <a id="contract-steps-attempt_paths-same_as_input"></a>**`same_as_input`** (array of string): Names of available resolved fields whose UTF-8 bytes equal input; those equal-valued keys are omitted. A differing form is carried as a string; an unavailable form is explicit null.

<a id="contract-steps-identity"></a>
### File identity observation

Record `identity`: `PWFileIdentity`.

- <a id="contract-steps-identity-device"></a>**`device`** (integer): The stat observation's device number.
- <a id="contract-steps-identity-inode"></a>**`inode`** (integer): The stat observation's inode number.
- <a id="contract-steps-identity-mode"></a>**`mode`** (integer): The stat observation's file type and mode bits.
- <a id="contract-steps-identity-uid"></a>**`uid`** (integer): The stat observation's owning user identifier.
- <a id="contract-steps-identity-gid"></a>**`gid`** (integer): The stat observation's owning group identifier.

<a id="contract-steps-stat"></a>
### File metadata observation

Record `stat`: `PWRunnerFileStat`.

- <a id="contract-steps-stat-rc"></a>**`rc`** (integer): Native lstat or fstat return at this position in the operation sequence.
- <a id="contract-steps-stat-errno"></a>**`errno`** (integer?): Errno from a failed metadata call.
- <a id="contract-steps-stat-identity"></a>**`identity`** ([File identity observation](#contract-steps-identity)?): Device, inode, mode, uid and gid from a successful metadata call.
- <a id="contract-steps-stat-size"></a>**`size`** (integer?): Byte length from a successful metadata call.

<a id="contract-steps-fresh_read"></a>
### Fresh-descriptor read

Record `fresh_read`: `PWRunnerFreshRead`.

- <a id="contract-steps-fresh_read-open_rc"></a>**`open_rc`** (integer): Descriptor from open with O_RDONLY and O_CLOEXEC, or -1 on failure.
- <a id="contract-steps-fresh_read-open_errno"></a>**`open_errno`** (integer?): Errno from failed open.
- <a id="contract-steps-fresh_read-read_rc"></a>**`read_rc`** (integer?): Byte count from the bounded read, or -1 on failure; absent when open failed.
- <a id="contract-steps-fresh_read-read_errno"></a>**`read_errno`** (integer?): Errno from failed read.
- <a id="contract-steps-fresh_read-stat_rc"></a>**`stat_rc`** (integer?): Return from descriptor fstat, present after successful open.
- <a id="contract-steps-fresh_read-stat_errno"></a>**`stat_errno`** (integer?): Errno from failed descriptor stat.
- <a id="contract-steps-fresh_read-identity"></a>**`identity`** ([File identity observation](#contract-steps-identity)?): Identity from successful descriptor stat.
- <a id="contract-steps-fresh_read-close_rc"></a>**`close_rc`** (integer?): Return from closing the descriptor, present after successful open.
- <a id="contract-steps-fresh_read-close_errno"></a>**`close_errno`** (integer?): Errno from failed close.
- <a id="contract-steps-fresh_read-content_hex"></a>**`content_hex`** (string (hex)?): Bytes actually read as hexadecimal, including the empty string for a zero-byte read. Absent when no valid read result supplied bytes.

<a id="contract-steps-fresh_write"></a>
### Fresh-descriptor write or creation

Record `fresh_write`: `PWRunnerFreshWrite`.

- <a id="contract-steps-fresh_write-open_rc"></a>**`open_rc`** (integer): Descriptor from open with O_WRONLY and O_CLOEXEC, additionally O_CREAT and O_EXCL with mode 0600 for creation, or -1 on failure.
- <a id="contract-steps-fresh_write-open_errno"></a>**`open_errno`** (integer?): Errno from failed open.
- <a id="contract-steps-fresh_write-truncate_rc"></a>**`truncate_rc`** (integer?): Return from ftruncate(fd, 0) for write_fresh after successful open; absent for creation or failed open.
- <a id="contract-steps-fresh_write-truncate_errno"></a>**`truncate_errno`** (integer?): Errno from failed truncate.
- <a id="contract-steps-fresh_write-write_rc"></a>**`write_rc`** (integer?): Return from writing byte x after creation or successful truncation. One is complete, zero is a short write, -1 is failure; absent when writing was not reached.
- <a id="contract-steps-fresh_write-write_errno"></a>**`write_errno`** (integer?): Errno from a failed write. A short write retains its count without an invented errno.
- <a id="contract-steps-fresh_write-close_rc"></a>**`close_rc`** (integer?): Return from closing an opened descriptor.
- <a id="contract-steps-fresh_write-close_errno"></a>**`close_errno`** (integer?): Errno from failed close.
- <a id="contract-steps-fresh_write-preopen_stat"></a>**`preopen_stat`** ([File metadata observation](#contract-steps-stat)?): Creation's pre-open lstat diagnostic, including absence or existing-object metadata.
- <a id="contract-steps-fresh_write-opened_stat"></a>**`opened_stat`** ([File metadata observation](#contract-steps-stat)?): Descriptor metadata immediately after successful open.
- <a id="contract-steps-fresh_write-truncated_stat"></a>**`truncated_stat`** ([File metadata observation](#contract-steps-stat)?): Descriptor metadata after the write_fresh truncate call, including a failed truncate.
- <a id="contract-steps-fresh_write-written_stat"></a>**`written_stat`** ([File metadata observation](#contract-steps-stat)?): Descriptor metadata after the attempted write, including a failed or short write.

<a id="contract-steps-assessment"></a>
### Interpreting the observations

Binding `p`: entry in `reply.phases`. Binding `s`: entry in `reply.steps`. Association restriction for `s`: `reply.steps[s].phase_id` = `reply.phases[p].phase_id`.

<a id="contract-steps-assessment-assembly"></a>
#### Assemble the two channels

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at step evidence assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Associate validator records and completed worker slots with the declared probe, retain their separate provenance and native observations, and synthesize an unavailable channel when its required observation is absent.

An excluded query remains synthetic even when an unexpected validator frame
carries its step identifier. A completed slot is used only for a supported
attempt. The native answer is the validator-sourced allow or deny value;
the ordering assessment supplies its live-worker temporal meaning.

<a id="contract-steps-assessment-assembly-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Assemble the two channels](#contract-steps-assessment-assembly).** Completed, incomplete, absent and unsupported slots map to distinct provenance and outcomes; action mapping preserves exec child observations. Context: Read complete step assembly and constructed attempt-mapping controls. Evidence limit: Check reading. Integrated query association has the validator collection's own support. [Evidence details](CONTRACT.md#contract-steps-assessment-assembly-support-details).

<a id="contract-steps-assessment-order"></a>
#### Establish query order

[Runner host](CONTRACT.md#contract-identity-definitions-host) checks at per-step ordering assessment. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. For each `p`, `s`. Applies when (absent(`reply.reporting_failure`) and present(`reply.steps[s].comparison`)). The first failed condition selects the consequence.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-steps-assessment-order-success"></a>Established order | On success, set_value(`reply.steps[s].comparison.order`, `"query_first"`). |
| <a id="contract-steps-assessment-order-failure"></a>Unestablished order | On failure, set_value(`reply.steps[s].comparison.order`, `"unestablished"`). |
| <a id="contract-steps-assessment-order-chain"></a>Collection chain | Requires (present(`reply.phases[p].ordering`) and `reply.phases[p].ordering.collection_closed_before_proceed` and `reply.phases[p].ordering.proceed_set` and `reply.phases[p].ordering.proceed_observed` and `reply.phases[p].ordering.worker_lifetime_established` and count(`reply.phases[p].ordering.protocol_violations`) = `0`). |
| <a id="contract-steps-assessment-order-setup"></a>Setup | Ordinary execution has observed successful application; actor execution has established the actor's declared applied or unapplied setup. |
| <a id="contract-steps-assessment-order-native"></a>Native answer | Requires (`reply.steps[s].sandbox_check.result_source` = `"validator"` and present(`reply.steps[s].sandbox_check.native_rc`) and present(`reply.steps[s].sandbox_check.errno`) and `reply.steps[s].sandbox_check.rc` = `reply.steps[s].sandbox_check.native_rc` and ((`reply.steps[s].sandbox_check.outcome` = `"allow"` and `reply.steps[s].sandbox_check.native_rc` = `0`) or (`reply.steps[s].sandbox_check.outcome` = `"deny"` and `reply.steps[s].sandbox_check.native_rc` = `1` and `reply.steps[s].sandbox_check.errno` = `0`))). |
| <a id="contract-steps-assessment-order-association"></a>Unique association | Binding `v`: entry in `reply.phases[p].validator_subprocess.records`. Association restriction for `v`: `reply.phases[p].validator_subprocess.records[v].step_id` = `reply.steps[s].step_id`. Requires (present(`reply.phases[p].validator_subprocess`) and present(`reply.phases[p].validator_subprocess.records`) and matches(`v`) = `1`). The query targets the associated live worker PID. For a filter kind outside the known request vocabulary, the native filter type is the uppercase spelling of that kind. Identifier and query-metadata equality in this join is equality of UTF-8 bytes; canonically equivalent spellings with different bytes do not match. |
| <a id="contract-steps-assessment-order-association-identity"></a>Unique association › Exact retained query identity | For each `p`, `s`, `v`. Requires (`reply.phases[p].validator_subprocess.records[v].operation` = `reply.steps[s].sandbox_check.operation` and `reply.phases[p].validator_subprocess.records[v].outcome` = `reply.steps[s].sandbox_check.outcome` and `reply.phases[p].validator_subprocess.records[v].rc` = `reply.steps[s].sandbox_check.native_rc` and `reply.phases[p].validator_subprocess.records[v].errno` = `reply.steps[s].sandbox_check.errno` and implies(`reply.steps[s].sandbox_check.filter_kind` ∈ [`"none"`, `"path"`, `"global_name"`, `"local_name"`, `"iokit_registry_entry_class"`, `"iokit_user_client_class"`, `"sysctl_name"`], ((`reply.steps[s].sandbox_check.filter_kind` = `"none"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"NONE"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"path"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"PATH"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"global_name"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"GLOBAL_NAME"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"local_name"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"LOCAL_NAME"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"iokit_registry_entry_class"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"IOKIT_REGISTRY_ENTRY_CLASS"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"iokit_user_client_class"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"IOKIT_USER_CLIENT_CLASS"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"sysctl_name"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"SYSCTL_NAME"`))) and ((`reply.steps[s].sandbox_check.filter_kind` = `"none"` and absent(`reply.phases[p].validator_subprocess.records[v].filter_value`)) or (`reply.steps[s].sandbox_check.filter_kind` ≠ `"none"` and `reply.phases[p].validator_subprocess.records[v].filter_value` = `reply.steps[s].sandbox_check.filter_value`))). |

<a id="contract-steps-assessment-order-source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Establish query order](#contract-steps-assessment-order) and its descendants.** Ordering first counts all records for the step ID, then compares the selected record and native value. Production supplies its live worker PID; reporting validation supplies the associated reported worker PID. [Evidence details](CONTRACT.md#contract-steps-assessment-order-source-details).

<a id="contract-steps-assessment-order-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Establish query order](#contract-steps-assessment-order) and its descendants.** Native answer eligibility and the collection/release/acknowledgement chain are independently required; producer association is exact within the phase and compares identifier and query-metadata bytes. Context: Read eligibility, ordering construction, phase adaptation and ordering controls. Evidence limit: Source and check reading; no new execution or mutation-control run is credited. [Evidence details](CONTRACT.md#contract-steps-assessment-order-support-details).

<a id="contract-steps-assessment-meaning"></a>
#### Temporal meaning

Each probe retains its prediction eligibility when another query fails.
A consume, release or other action earlier in the batch can change the
state a later attempt encounters. Submitted-string relations and path
observations retain their respective intervals and identities.

<a id="contract-steps-assessment-observe"></a>
#### Classify an observation

[Runner host](CONTRACT.md#contract-identity-definitions-host) checks at step evidence assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Binding `r`: entry in `reply.steps`. For each `r`. Select the first matching case in the listed order. Applies when present(`reply.steps[r].comparison`).

A permission classification records the shape of the native failure.
Attribution to a particular enforcing mechanism requires supporting
evidence.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-steps-assessment-observe-spawned"></a>1. Spawn observed | (`reply.steps[r].attempt.result_source` = `"worker"` and `reply.steps[r].attempt.requested_kind` = `"exec"` and present(`reply.steps[r].attempt.child_pid`) and `reply.steps[r].attempt.child_pid` > `0`) | [set_value(`reply.steps[r].comparison.observation`, `"succeeded"`), set_value(`reply.steps[r].comparison.observation_basis`, `"spawned_child"`)]. A positive child PID records spawning even when the child's later status fails. |
| <a id="contract-steps-assessment-observe-completed"></a>2. Completed success | (`reply.steps[r].attempt.result_source` = `"worker"` and `reply.steps[r].attempt.outcome` = `"ok"` and `reply.steps[r].attempt.rc` = `0`) | [set_value(`reply.steps[r].comparison.observation`, `"succeeded"`), set_value(`reply.steps[r].comparison.observation_basis`, `"completed_worker_status"`)]. |
| <a id="contract-steps-assessment-observe-permission"></a>3. Permission errno | (`reply.steps[r].attempt.result_source` = `"worker"` and `reply.steps[r].attempt.rc` ≠ `0` and `reply.steps[r].attempt.outcome` ∈ [`"open_failed"`, `"read_failed"`, `"write_failed"`, `"unlink_failed"`, `"access_failed"`, `"sysctl_failed"`, `"exec_failed"`] and `reply.steps[r].attempt.errno` ∈ [`1`, `13`]) | [set_value(`reply.steps[r].comparison.observation`, `"permission_failure"`), set_value(`reply.steps[r].comparison.observation_basis`, `"permission_errno"`)]. Darwin EPERM and EACCES supply the numeric errno alternatives at this boundary. |
| <a id="contract-steps-assessment-observe-bootstrap"></a>4. Bootstrap permission result | (`reply.steps[r].attempt.result_source` = `"worker"` and `reply.steps[r].attempt.rc` ≠ `0` and `reply.steps[r].attempt.outcome` = `"lookup_failed"` and `reply.steps[r].attempt.error` = `"bootstrap_look_up: kr=1100"`) | [set_value(`reply.steps[r].comparison.observation`, `"permission_failure"`), set_value(`reply.steps[r].comparison.observation_basis`, `"bootstrap_permission_result"`)]. |
| <a id="contract-steps-assessment-observe-other"></a>5. Other completed failure | (`reply.steps[r].attempt.result_source` = `"worker"` and `reply.steps[r].attempt.rc` ≠ `0`) | [set_value(`reply.steps[r].comparison.observation`, `"other_failure"`), set_value(`reply.steps[r].comparison.observation_basis`, `"completed_worker_status"`)]. |
| <a id="contract-steps-assessment-observe-unavailable"></a>6. Unavailable observation | `true` | [set_value(`reply.steps[r].comparison.observation`, `"unavailable"`), set_value(`reply.steps[r].comparison.observation_basis`, `"no_completed_worker_result"`)]. |

<a id="contract-steps-assessment-observe-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Classify an observation](#contract-steps-assessment-observe) and its descendants.** Every scenario-matrix row's constructed attempt result yields its expected observation and basis: a spawned child with either exit status, completed success, permission errno, the bootstrap permission result, another completed failure and a missing result. Context: Read the producer's branch order and the table-driven reader over the scenario matrix. Evidence limit: Constructed attempt results were read. Integrated matrix cases own the live rows, without execution credit here. [Evidence details](CONTRACT.md#contract-steps-assessment-observe-support-details).

<a id="contract-steps-assessment-relations"></a>
#### Submitted operation and target

| Attempt | Mapped operation | Mapped filter |
| --- | --- | --- |
| file/open_read, file/access, file/read_fresh | file-read-data | path |
| file/open_write, file/write_fresh | file-write-data | path |
| file/unlink | file-write-unlink | path |
| mach_lookup/bootstrap_look_up | mach-lookup | global_name |
| sysctl/read | sysctl-read | sysctl_name |
| exec/spawn | process-exec* | path |
| file/create, file/create_fresh | unresolved compound operation | path |

`process-exec*` predicts target admission; spawn and child observations
record the subsequent operation. Other wildcard query spellings have an
unresolved operation relation. Target equality compares submitted strings;
runtime object identity requires its own observations.

<a id="contract-steps-assessment-relations-unlink"></a>
##### Unlink and later observations

A completed worker unlink with `outcome: ok` and `rc: 0` records removal at
that action. A same-phase query's `query_first` places it before unlink.
Across phases, completion and arrival publications establish sequencing.
A later query can follow unlink and recreation of the same spelling;
these observations belong to their respective objects and times.

<a id="contract-steps-assessment-relations-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Submitted operation and target](#contract-steps-assessment-relations) and its descendants.** The scenario matrix checks mapped operations, submitted relations, order and limitation values, including spawn and unlink distinctions. Context: Read the producer, matrix adapter and shared reading rules with their scenario descriptions. Evidence limit: Constructed controls were read. Corresponding integrated cases own live filesystem scenarios, without execution credit here. [Evidence details](CONTRACT.md#contract-steps-assessment-relations-support-details).

<a id="contract-steps-assessment-fresh"></a>
#### Observe fresh descriptors

[Worker](CONTRACT.md#contract-identity-definitions-worker) acts at released probe action. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Uses [Project the fresh-read aggregate](#contract-steps-assessment-fresh_read_aggregate), [Project the fresh-write aggregate](#contract-steps-assessment-fresh_write_aggregate). Open a new descriptor during the released action, perform the action-specific native sequence and publish each reached operation when the slot completes.

A successful read records the bytes actually returned.

Unreached operations remain absent.

<a id="contract-steps-assessment-fresh-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Observe fresh descriptors](#contract-steps-assessment-fresh).** Completed publication gates detailed payloads; fresh-write controls distinguish creation, truncate, short write, metadata precedence and absent operations. Context: Read native sequences, shared-memory decoding, step construction and fresh-write controls. Evidence limit: Fresh-read sequencing is source-supported here. Constructed controls establish record consistency; live effects have integrated owners. [Evidence details](CONTRACT.md#contract-steps-assessment-fresh-support-details).

<a id="contract-steps-assessment-paths"></a>
#### Add host path observations

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at after orchestration. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. For each `p`, `s`. Resolve qualifying query and attempt paths through the host filesystem after orchestration. Preserve independent realpath, parent-form and firmlink observations and their unavailable results.

A missing leaf can have
a parent form and a null realpath form. The submitted
comparison operands remain preserved.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-steps-assessment-paths-attempt"></a>Attempt path input | Applies when (`reply.steps[s].attempt.requested_kind` ∈ [`"file"`, `"exec"`] and present(`reply.steps[s].attempt.requested_path`) and `reply.steps[s].attempt.requested_path` ≠ `""`). [set_value(`reply.steps[s].attempt.path_diagnostics.input`, `reply.steps[s].attempt.requested_path`), set_value(`reply.steps[s].attempt.path_diagnostics.observer`, `"runner_host"`), set_value(`reply.steps[s].attempt.path_diagnostics.stage`, `"after_orchestration"`)]. |
| <a id="contract-steps-assessment-paths-attempt_presence"></a>Attempt path input applicability | Requires implies((`reply.steps[s].attempt.requested_kind` ∈ [`"file"`, `"exec"`] and present(`reply.steps[s].attempt.requested_path`) and `reply.steps[s].attempt.requested_path` ≠ `""`), present(`reply.steps[s].attempt.path_diagnostics`)). |
| <a id="contract-steps-assessment-paths-query"></a>Query path input | Applies when (`reply.steps[s].sandbox_check.filter_kind` = `"path"` and present(`reply.steps[s].sandbox_check.filter_value`) and `reply.steps[s].sandbox_check.filter_value` ≠ `""`). [set_value(`reply.steps[s].sandbox_check.path_diagnostics.input`, `reply.steps[s].sandbox_check.filter_value`), set_value(`reply.steps[s].sandbox_check.path_diagnostics.observer`, `"runner_host"`), set_value(`reply.steps[s].sandbox_check.path_diagnostics.stage`, `"after_orchestration"`)]. |
| <a id="contract-steps-assessment-paths-query_presence"></a>Query path input applicability | Requires implies((`reply.steps[s].sandbox_check.filter_kind` = `"path"` and present(`reply.steps[s].sandbox_check.filter_value`) and `reply.steps[s].sandbox_check.filter_value` ≠ `""`), present(`reply.steps[s].sandbox_check.path_diagnostics`)). |

<a id="contract-steps-assessment-paths-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Add host path observations](#contract-steps-assessment-paths).** Path controls create parents and symlinks, distinguish missing and symlink leaves, skip non-path attempts and preserve separate query observations. Context: Read enrichment, helpers and path controls, including exact UTF-8 retention. Evidence limit: Check reading; the observations retain the host's after-orchestration interval. [Evidence details](CONTRACT.md#contract-steps-assessment-paths-support-details).

<a id="contract-steps-assessment-fresh_read_aggregate"></a>
#### Project the fresh-read aggregate

[Worker](CONTRACT.md#contract-identity-definitions-worker), [Runner host](CONTRACT.md#contract-identity-definitions-host) reports at completed native aggregate projection. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. For each `p`, `s`. Select the first matching case in the listed order. Applies when (`reply.steps[s].attempt.requested_kind` = `"file"` and `reply.steps[s].attempt.requested_action` = `"read_fresh"` and `reply.steps[s].attempt.result_source` = `"worker"` and present(`reply.steps[s].attempt.fresh_read`)).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-steps-assessment-fresh_read_aggregate-open_errno"></a>1. open failure with errno | (present(`reply.steps[s].attempt.fresh_read.open_rc`) and `reply.steps[s].attempt.fresh_read.open_rc` < `0` and present(`reply.steps[s].attempt.fresh_read.open_errno`) and `reply.steps[s].attempt.fresh_read.open_errno` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"read_failed"`), set_value(`reply.steps[s].attempt.errno`, `reply.steps[s].attempt.fresh_read.open_errno`)]. |
| <a id="contract-steps-assessment-fresh_read_aggregate-open_zero"></a>2. open failure without nonzero errno | (present(`reply.steps[s].attempt.fresh_read.open_rc`) and `reply.steps[s].attempt.fresh_read.open_rc` < `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"read_failed"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |
| <a id="contract-steps-assessment-fresh_read_aggregate-stat_errno"></a>3. stat failure with errno | (present(`reply.steps[s].attempt.fresh_read.stat_rc`) and `reply.steps[s].attempt.fresh_read.stat_rc` ≠ `0` and present(`reply.steps[s].attempt.fresh_read.stat_errno`) and `reply.steps[s].attempt.fresh_read.stat_errno` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"read_failed"`), set_value(`reply.steps[s].attempt.errno`, `reply.steps[s].attempt.fresh_read.stat_errno`)]. |
| <a id="contract-steps-assessment-fresh_read_aggregate-stat_zero"></a>4. stat failure without nonzero errno | (present(`reply.steps[s].attempt.fresh_read.stat_rc`) and `reply.steps[s].attempt.fresh_read.stat_rc` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"read_failed"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |
| <a id="contract-steps-assessment-fresh_read_aggregate-read_errno"></a>5. read failure with errno | (present(`reply.steps[s].attempt.fresh_read.read_rc`) and `reply.steps[s].attempt.fresh_read.read_rc` < `0` and present(`reply.steps[s].attempt.fresh_read.read_errno`) and `reply.steps[s].attempt.fresh_read.read_errno` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"read_failed"`), set_value(`reply.steps[s].attempt.errno`, `reply.steps[s].attempt.fresh_read.read_errno`)]. |
| <a id="contract-steps-assessment-fresh_read_aggregate-read_zero"></a>6. read failure without nonzero errno | (present(`reply.steps[s].attempt.fresh_read.read_rc`) and `reply.steps[s].attempt.fresh_read.read_rc` < `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"read_failed"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |
| <a id="contract-steps-assessment-fresh_read_aggregate-close_errno"></a>7. close failure with errno | (present(`reply.steps[s].attempt.fresh_read.close_rc`) and `reply.steps[s].attempt.fresh_read.close_rc` ≠ `0` and present(`reply.steps[s].attempt.fresh_read.close_errno`) and `reply.steps[s].attempt.fresh_read.close_errno` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"read_failed"`), set_value(`reply.steps[s].attempt.errno`, `reply.steps[s].attempt.fresh_read.close_errno`)]. |
| <a id="contract-steps-assessment-fresh_read_aggregate-close_zero"></a>8. close failure without nonzero errno | (present(`reply.steps[s].attempt.fresh_read.close_rc`) and `reply.steps[s].attempt.fresh_read.close_rc` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"read_failed"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |
| <a id="contract-steps-assessment-fresh_read_aggregate-success"></a>9. Successful aggregate | `true` | [set_value(`reply.steps[s].attempt.rc`, `0`), set_value(`reply.steps[s].attempt.outcome`, `"ok"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |

<a id="contract-steps-assessment-fresh_read_aggregate-source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Project the fresh-read aggregate](#contract-steps-assessment-fresh_read_aggregate) and its descendants.** Native code preserves the first failed reached descriptor operation; the host maps the completed aggregate rc and converts errno zero to null. Creation pre-open stat stays diagnostic. [Evidence details](CONTRACT.md#contract-steps-assessment-fresh_read_aggregate-source-details).

<a id="contract-steps-assessment-fresh_write_aggregate"></a>
#### Project the fresh-write aggregate

[Worker](CONTRACT.md#contract-identity-definitions-worker), [Runner host](CONTRACT.md#contract-identity-definitions-host) reports at completed native aggregate projection. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. For each `p`, `s`. Select the first matching case in the listed order. Applies when (`reply.steps[s].attempt.requested_kind` = `"file"` and `reply.steps[s].attempt.requested_action` ∈ [`"write_fresh"`, `"create_fresh"`] and `reply.steps[s].attempt.result_source` = `"worker"` and present(`reply.steps[s].attempt.fresh_write`)).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-steps-assessment-fresh_write_aggregate-open_errno"></a>1. open failure with errno | (present(`reply.steps[s].attempt.fresh_write.open_rc`) and `reply.steps[s].attempt.fresh_write.open_rc` < `0` and present(`reply.steps[s].attempt.fresh_write.open_errno`) and `reply.steps[s].attempt.fresh_write.open_errno` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `reply.steps[s].attempt.fresh_write.open_errno`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-open_zero"></a>2. open failure without nonzero errno | (present(`reply.steps[s].attempt.fresh_write.open_rc`) and `reply.steps[s].attempt.fresh_write.open_rc` < `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-opened_stat_errno"></a>3. opened stat failure with errno | (present(`reply.steps[s].attempt.fresh_write.opened_stat`) and present(`reply.steps[s].attempt.fresh_write.opened_stat.rc`) and `reply.steps[s].attempt.fresh_write.opened_stat.rc` ≠ `0` and present(`reply.steps[s].attempt.fresh_write.opened_stat.errno`) and `reply.steps[s].attempt.fresh_write.opened_stat.errno` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `reply.steps[s].attempt.fresh_write.opened_stat.errno`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-opened_stat_zero"></a>4. opened stat failure without nonzero errno | (present(`reply.steps[s].attempt.fresh_write.opened_stat`) and present(`reply.steps[s].attempt.fresh_write.opened_stat.rc`) and `reply.steps[s].attempt.fresh_write.opened_stat.rc` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-truncate_errno"></a>5. truncate failure with errno | (`reply.steps[s].attempt.requested_action` = `"write_fresh"` and present(`reply.steps[s].attempt.fresh_write.truncate_rc`) and `reply.steps[s].attempt.fresh_write.truncate_rc` ≠ `0` and present(`reply.steps[s].attempt.fresh_write.truncate_errno`) and `reply.steps[s].attempt.fresh_write.truncate_errno` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `reply.steps[s].attempt.fresh_write.truncate_errno`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-truncate_zero"></a>6. truncate failure without nonzero errno | (`reply.steps[s].attempt.requested_action` = `"write_fresh"` and present(`reply.steps[s].attempt.fresh_write.truncate_rc`) and `reply.steps[s].attempt.fresh_write.truncate_rc` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-truncated_stat_errno"></a>7. truncated stat failure with errno | (`reply.steps[s].attempt.requested_action` = `"write_fresh"` and present(`reply.steps[s].attempt.fresh_write.truncated_stat`) and present(`reply.steps[s].attempt.fresh_write.truncated_stat.rc`) and `reply.steps[s].attempt.fresh_write.truncated_stat.rc` ≠ `0` and present(`reply.steps[s].attempt.fresh_write.truncated_stat.errno`) and `reply.steps[s].attempt.fresh_write.truncated_stat.errno` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `reply.steps[s].attempt.fresh_write.truncated_stat.errno`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-truncated_stat_zero"></a>8. truncated stat failure without nonzero errno | (`reply.steps[s].attempt.requested_action` = `"write_fresh"` and present(`reply.steps[s].attempt.fresh_write.truncated_stat`) and present(`reply.steps[s].attempt.fresh_write.truncated_stat.rc`) and `reply.steps[s].attempt.fresh_write.truncated_stat.rc` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-write_errno"></a>9. write failure with errno | (present(`reply.steps[s].attempt.fresh_write.write_rc`) and `reply.steps[s].attempt.fresh_write.write_rc` ≠ `1` and present(`reply.steps[s].attempt.fresh_write.write_errno`) and `reply.steps[s].attempt.fresh_write.write_errno` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `reply.steps[s].attempt.fresh_write.write_errno`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-write_zero"></a>10. write failure without nonzero errno | (present(`reply.steps[s].attempt.fresh_write.write_rc`) and `reply.steps[s].attempt.fresh_write.write_rc` ≠ `1`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-written_stat_errno"></a>11. written stat failure with errno | (present(`reply.steps[s].attempt.fresh_write.written_stat`) and present(`reply.steps[s].attempt.fresh_write.written_stat.rc`) and `reply.steps[s].attempt.fresh_write.written_stat.rc` ≠ `0` and present(`reply.steps[s].attempt.fresh_write.written_stat.errno`) and `reply.steps[s].attempt.fresh_write.written_stat.errno` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `reply.steps[s].attempt.fresh_write.written_stat.errno`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-written_stat_zero"></a>12. written stat failure without nonzero errno | (present(`reply.steps[s].attempt.fresh_write.written_stat`) and present(`reply.steps[s].attempt.fresh_write.written_stat.rc`) and `reply.steps[s].attempt.fresh_write.written_stat.rc` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-close_errno"></a>13. close failure with errno | (present(`reply.steps[s].attempt.fresh_write.close_rc`) and `reply.steps[s].attempt.fresh_write.close_rc` ≠ `0` and present(`reply.steps[s].attempt.fresh_write.close_errno`) and `reply.steps[s].attempt.fresh_write.close_errno` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `reply.steps[s].attempt.fresh_write.close_errno`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-close_zero"></a>14. close failure without nonzero errno | (present(`reply.steps[s].attempt.fresh_write.close_rc`) and `reply.steps[s].attempt.fresh_write.close_rc` ≠ `0`) | [set_value(`reply.steps[s].attempt.rc`, `-1`), set_value(`reply.steps[s].attempt.outcome`, `"write_failed"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |
| <a id="contract-steps-assessment-fresh_write_aggregate-success"></a>15. Successful aggregate | `true` | [set_value(`reply.steps[s].attempt.rc`, `0`), set_value(`reply.steps[s].attempt.outcome`, `"ok"`), set_value(`reply.steps[s].attempt.errno`, `null`)]. |

<a id="contract-steps-assessment-fresh_write_aggregate-source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Project the fresh-write aggregate](#contract-steps-assessment-fresh_write_aggregate) and its descendants.** Native code preserves the first failed reached descriptor operation; the host maps the completed aggregate rc and converts errno zero to null. Creation pre-open stat stays diagnostic. [Evidence details](CONTRACT.md#contract-steps-assessment-fresh_write_aggregate-source-details).
<!-- END GENERATED CONTRACT steps -->

## Read actors and phase ownership

Actor-form reports place application, equipment and process observations under their associated actor. Phase activation, completion and termination dependencies have separate observations. Follow the [actor declarations](REQUEST.md#contract-actors) when locating the owning schedule.

<!-- BEGIN GENERATED CONTRACT actor_evidence -->
<a id="contract-actor_evidence"></a>
## Actor and phase evidence

<a id="contract-actor_evidence-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Actor and phase evidence](#contract-actor_evidence) and its descendants.** Imported public field definitions joined to producer/decoder/assessment meanings; explicit rule and evidence gaps preserve scope. Evidence limit: No execution credit is claimed by this owner. [Evidence details](CONTRACT.md#contract-actor_evidence-support-details).

<a id="contract-actor_evidence-actor"></a>
### Actor process account

Record `ae_actor`: `PWRunnerActorResult`.

The host emits actors in request order. Each actor owns its launch, worker publications, policy receipt, equipment read-back and lifecycle account.

- <a id="contract-actor_evidence-actor-actor_id"></a>**`actor_id`** (string): Submitted actor identifier that binds this row to its phases and resources. Ordinary semantic replies require nonempty, NUL-free actor identifiers within their admitted UTF-8 capacity, distinct identifiers and request order.
- <a id="contract-actor_evidence-actor-index"></a>**`index`** (integer): Zero-based position in the admitted actor list.
- <a id="contract-actor_evidence-actor-mode"></a>**`mode`** (string): Submitted sandbox mode, apply or unapplied. Admitted vocabulary: closed; displayed list: exhaustive: `"apply"`, `"unapplied"`.
- <a id="contract-actor_evidence-actor-policy_format"></a>**`policy_format`** (string?): Selected policy representation for an apply actor, when provided.
- <a id="contract-actor_evidence-actor-policy_sha256"></a>**`policy_sha256`** (string (hex)?): Host SHA-256 of the selected submitted source bytes after controller augmentation.
- <a id="contract-actor_evidence-actor-policy_received_sha256"></a>**`policy_received_sha256`** (string (hex)?): Worker SHA-256 of the bytes it actually read before compilation, when published.
- <a id="contract-actor_evidence-actor-setup_status"></a>**`setup_status`** (string): Host setup classification: not_launched, launch_refused, transfer_failed, applied, unapplied_declared, setup_failed, authority_setup_failed, exited_before_setup or setup_timeout. Admitted vocabulary: closed; displayed list: exhaustive: `"not_launched"`, `"launch_refused"`, `"transfer_failed"`, `"applied"`, `"unapplied_declared"`, `"setup_failed"`, `"authority_setup_failed"`, `"exited_before_setup"`, `"setup_timeout"`.
- <a id="contract-actor_evidence-actor-applied"></a>**`applied`** (boolean?): Acquired worker applied flag for apply mode when output exists; absent for an unapplied declaration or unavailable output.
- <a id="contract-actor_evidence-actor-application_count"></a>**`application_count`** (integer): Zero or one from the final acquired applied publication, retained even when a setup deadline already ended eligibility.
- <a id="contract-actor_evidence-actor-launch"></a>**`launch`** ([Actor launch context](#contract-actor_evidence-launch)?): Host-arranged launch context once this actor process was spawned.
- <a id="contract-actor_evidence-actor-subprocess"></a>**`subprocess`** ([Worker subprocess](#contract-lifecycle-worker)?): This actor's worker lifecycle and publication account.
- <a id="contract-actor_evidence-actor-compiled_profile"></a>**`compiled_profile`** ([Receipt](#contract-profile-receipt)?): Receipt from this actor's requested compiled-profile capture, when the host has a capture result.
- <a id="contract-actor_evidence-actor-visits"></a>**`visits`** (array of integer): In an ordinary semantic reply, the exact ordered list of one-based global phase ordinals declared for this actor, including visits whose activation never occurred. Membership comes from each phase's declared owner.
- <a id="contract-actor_evidence-actor-equipment"></a>**`equipment`** ([Actor equipment selection](#contract-equipment-actor)?): Requested and resolved worker role, entitlement requirement assessment and live execution observation.
- <a id="contract-actor_evidence-actor-application"></a>**`application`** ([Application assessment](#contract-actor_evidence-application)?): Host application-boundary assessment with its evidence basis.
- <a id="contract-actor_evidence-actor-owned_reap"></a>**`owned_reap`** ([Owned child ending](#contract-lifecycle-owned_reap)?): Host-owned waitpid ending retained for this actor and referenced by dependent termination gates.

<a id="contract-actor_evidence-actor-account"></a>
#### Actor ownership and reporting scope

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at actor reply assembly. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Applies when present(`request.actors`). Assemble each actor's row from its declaration, launch/driver output and its own shared publications; phases retain their declared actor and action ownership. Retain the actor-indexed account and separately report schedule observations. In an ordinary executed reply, each declared action has its ordered step or extension-event record even when execution evidence is unresolved. Preparation refusals and retained reporting failures carry the distinct contents stated below.

A preparation refusal retains declarations and preparation observations while
its execution tables remain empty. A retained reporting-failure reply carries
the assembled observations and the reporting conflict, with comparison claims
removed. Its applicable guarantee is the degraded report's form: retained
actor, phase and resource associations remain available for inspection as
assembled. Ordinary consistency assessments apply on the ordinary reply path.

<a id="contract-actor_evidence-actor-reader_scope"></a>
#### Reader applicability

Uses [Check families and applicability](#contract-diagnostics-execution-families), [Publish a report or fallback](#contract-reply-failure-publish).

The host self-check, controller semantic reader and general canonical-JSON
consumer check ordinary actor relationships when `reporting_failure` is
absent. Recipient checks compare declarations and observations carried in the
reply; they do not independently compare those declarations with the submitted
request. The host owns request-to-reply assembly.

A preparation refusal belongs to the actor execution form and retains
its admitted declarations: actor order, IDs and visits, phase order and owner,
actor visit numbers and action IDs. It carries no launch, arrival, completion,
proceed publication, step, extension-event, transfer or resource entry. Each
actor has zero successful applications. Its host authority scope is
`not_attempted`, with empty region and custody tables. The actor event table
is present, including when empty.

Phase and actor identifiers are nonempty and NUL-free within their admitted
UTF-8 capacities. Action identifiers use that same capacity and NUL rule;
ordinary-form actions admit an empty identifier, while actor-form actions require a
nonempty one. Declaration uniqueness and exact schedule membership apply
separately from that string grammar.

A reporting-failure reply is checked for its degradation form and applicable
compiled-profile context. Host validation, controller admission and the general consumer apply that
scope. The actor/extension readers check ordinary semantic relationships when
the reporting-failure record is absent. The lifecycle receipt reader separately checks each
retained worker's claims and controller projection; findings from that
assessment describe the retained worker evidence.

<a id="contract-actor_evidence-actor-reader_scope-support"></a>
**Support: [executed](CONTRACT.md#contract-support-grades) for [Reader applicability](#contract-actor_evidence-actor-reader_scope).** Constructed typed preparation, declaration and degradation neighbours retain separate host, controller, general-consumer and worker-lifecycle judgments. Context: Whole canonical runner-unit case passed with zero recorded system sleep. Swift judgments over 142 typed frames were retained before encoding; exact-one Rust replay carried 143 frames including the real writer-cap fallback through envelopes, then independent Python readers completed all rows and seven JSON-only controls. Evidence limit: The corpus uses constructed records and independently expected interpretations. Eleven application-positive pairs, degradation admission, the exact contradictory-worker D1 finding and retained actor projections have separate assertions. JSON-only normalization has its own domain. Native occurrence of each constructed context has separate observation owners. [Evidence details](CONTRACT.md#contract-actor_evidence-actor-reader_scope-support-details).

<a id="contract-actor_evidence-actor-reader_scope-setup_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Reader applicability](#contract-actor_evidence-actor-reader_scope).** An apply-mode actor cannot declare unapplied setup in an ordinary reply; rich degradation retains the conflicting declaration without comparisons. Context: A constructed valid actor reply changes only setup_status. Host reporting, controller admission and the general consumer own the ordinary identity check; the extension subreader has a narrower scope. Evidence limit: Source and check reading. The constructed mismatch is not evidence of a native scheduler producing it; execution of the corrected reader remains separately recorded. [Evidence details](CONTRACT.md#contract-actor_evidence-actor-reader_scope-setup_support-details).

<a id="contract-actor_evidence-launch"></a>
### Actor launch context

Record `ae_launch`: `PWRunnerActorLaunch`.

The host starts each actor as a fresh process with explicit standard streams and descriptor inheritance.

- <a id="contract-actor_evidence-launch-pid"></a>**`pid`** (integer): PID obtained from this actor's successful spawn.
- <a id="contract-actor_evidence-launch-parent_pid"></a>**`parent_pid`** (integer): PID of the runner host that spawned the actor.
- <a id="contract-actor_evidence-launch-environment"></a>**`environment`** (string): empty: the host supplies an empty environment to the actor process.
- <a id="contract-actor_evidence-launch-standard_streams"></a>**`standard_streams`** (string): stdin_policy_pipe_stdout_stderr_null_device: stdin carries policy bytes, while stdout and stderr are attached to the null device.
- <a id="contract-actor_evidence-launch-inherited_descriptors"></a>**`inherited_descriptors`** (array of integer): Explicit inherited descriptor numbers: 0 policy input, 3 shared evidence, 4 readiness, and 5 only when an authority region is mapped for the actor.

<a id="contract-actor_evidence-application"></a>
### Application assessment

Record `ae_application`: `PWRunnerActorApplication`.

- <a id="contract-actor_evidence-application-state"></a>**`state`** (string): not_requested, not_attempted, observed or unobserved. observed identifies evidence of the apply boundary, including a native apply failure; unobserved retains an unresolved result. Admitted vocabulary: closed; displayed list: exhaustive: `"not_requested"`, `"not_attempted"`, `"observed"`, `"unobserved"`.
- <a id="contract-actor_evidence-application-basis"></a>**`basis`** (string): The specific declaration, launch state or worker/authority publication supporting state. The eleven permitted state/basis pairs are defined by the application rule below. Admitted vocabulary: closed; displayed list: exhaustive: `"unapplied_declaration"`, `"worker_not_launched"`, `"applied_publication"`, `"terminal_authority_setup_refusal"`, `"apply_failure_publication"`, `"terminal_input_refusal"`, `"terminal_parameter_refusal"`, `"terminal_compile_refusal"`, `"terminal_timing_refusal"`, `"apply_call_boundary_without_result"`, `"no_eligible_apply_publication"`.

<a id="contract-actor_evidence-application-authority_association"></a>
#### Associated authority rows

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at actor reply assembly. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Binding `a`: entry in `reply.actors`. Binding `w`: entry in `reply.authority_setup.workers`. Association restriction for `w`: (`w` = `a` and present(`reply.authority_setup.workers[w].actor_index`) and `reply.authority_setup.workers[w].actor_index` = `a` and present(`reply.authority_setup.workers[w].actor_id`) and `reply.authority_setup.workers[w].actor_id` = `reply.actors[a].actor_id`). For each `a`. Applies when (present(`request.actors`) and present(`reply.actors`) and `reply.execution_form` = `"actors"` and absent(`reply.reporting_failure`)).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actor_evidence-application-authority_association-entry"></a>One associated entry for each actor | Requires (present(`reply.authority_setup`) and count(`reply.authority_setup.workers`) = count(`reply.actors`) and matches(`w`) = `1`). |

<a id="contract-actor_evidence-application-classify"></a>
#### Application classification

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at actor reply assembly. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Binding `a`: entry in `reply.actors`. Binding `t`: entry in `reply.authority_setup.workers`. Association restriction for `t`: (`t` = `a` and present(`reply.authority_setup.workers[t].publication`) and `reply.authority_setup.workers[t].publication` = `"observed"` and present(`reply.authority_setup.workers[t].disposition`) and `reply.authority_setup.workers[t].disposition` = `"terminal_required_failure"` and absent(`reply.authority_setup.workers[t].integrity_errors`)). For each `a`. Select the first matching case in the listed order. Applies when (present(`request.actors`) and present(`reply.actors`) and `reply.execution_form` = `"actors"` and absent(`reply.reporting_failure`)).

Preparation refusals classify their
unlaunched rows through the first two branches. An unavailable native
authority observation is reported as an entry with publication `not_observed`.

These are the host's production assignments. Recipient checks separately
validate the carried associations, permitted state/basis pairs and source
precedence. A reporting-failure reply retains the earlier assessment under
its own reporting scope.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-actor_evidence-application-classify-unapplied"></a>1. Unapplied declaration | `reply.actors[a].mode` = `"unapplied"` | [set_value(`reply.actors[a].application.state`, `"not_requested"`), set_value(`reply.actors[a].application.basis`, `"unapplied_declaration"`)]. |
| <a id="contract-actor_evidence-application-classify-unlaunched"></a>2. Worker absent | absent(`reply.actors[a].launch`) | [set_value(`reply.actors[a].application.state`, `"not_attempted"`), set_value(`reply.actors[a].application.basis`, `"worker_not_launched"`)]. |
| <a id="contract-actor_evidence-application-classify-applied"></a>3. Applied flag | (present(`reply.actors[a].applied`) and `reply.actors[a].applied` = `true`) | [set_value(`reply.actors[a].application.state`, `"observed"`), set_value(`reply.actors[a].application.basis`, `"applied_publication"`)]. |
| <a id="contract-actor_evidence-application-classify-authority"></a>4. Authority refusal | (present(`reply.authority_setup`) and matches(`t`) = `1`) | [set_value(`reply.actors[a].application.state`, `"not_attempted"`), set_value(`reply.actors[a].application.basis`, `"terminal_authority_setup_refusal"`)]. |
| <a id="contract-actor_evidence-application-classify-apply_failure"></a>5. Native apply failure | (present(`reply.actors[a].subprocess`) and present(`reply.actors[a].subprocess.worker_evidence`) and `reply.actors[a].subprocess.worker_evidence.failure_state` = `"published"` and present(`reply.actors[a].subprocess.worker_evidence.failure`) and `reply.actors[a].subprocess.worker_evidence.failure.operation` = `8` and `reply.actors[a].subprocess.worker_evidence.failure.code` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `1` and present(`reply.actors[a].subprocess.worker_evidence.failure.native_result`) and `reply.actors[a].subprocess.worker_evidence.failure.native_result` ≠ `0`) | [set_value(`reply.actors[a].application.state`, `"observed"`), set_value(`reply.actors[a].application.basis`, `"apply_failure_publication"`)]. |
| <a id="contract-actor_evidence-application-classify-input"></a>6. Input refusal | (present(`reply.actors[a].subprocess`) and present(`reply.actors[a].subprocess.worker_evidence`) and `reply.actors[a].subprocess.worker_evidence.failure_state` = `"published"` and present(`reply.actors[a].subprocess.worker_evidence.failure`) and ((`reply.actors[a].subprocess.worker_evidence.failure.operation` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.code` ∈ [`4`, `7`, `10`, `12`] and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `0`) or (`reply.actors[a].subprocess.worker_evidence.failure.operation` = `2` and `reply.actors[a].subprocess.worker_evidence.failure.code` ∈ [`2`, `3`, `9`, `13`]))) | [set_value(`reply.actors[a].application.state`, `"not_attempted"`), set_value(`reply.actors[a].application.basis`, `"terminal_input_refusal"`)]. |
| <a id="contract-actor_evidence-application-classify-parameter"></a>7. Parameter refusal | (present(`reply.actors[a].subprocess`) and present(`reply.actors[a].subprocess.worker_evidence`) and `reply.actors[a].subprocess.worker_evidence.failure_state` = `"published"` and present(`reply.actors[a].subprocess.worker_evidence.failure`) and ((`reply.actors[a].subprocess.worker_evidence.failure.operation` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.code` = `5` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `0`) or (`reply.actors[a].subprocess.worker_evidence.failure.operation` = `3` and `reply.actors[a].subprocess.worker_evidence.failure.code` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `2`) or (`reply.actors[a].subprocess.worker_evidence.failure.operation` = `4` and ((`reply.actors[a].subprocess.worker_evidence.failure.code` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `1`) or (`reply.actors[a].subprocess.worker_evidence.failure.code` = `6` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `0`))))) | [set_value(`reply.actors[a].application.state`, `"not_attempted"`), set_value(`reply.actors[a].application.basis`, `"terminal_parameter_refusal"`)]. |
| <a id="contract-actor_evidence-application-classify-compile"></a>8. Compile refusal | (present(`reply.actors[a].subprocess`) and present(`reply.actors[a].subprocess.worker_evidence`) and `reply.actors[a].subprocess.worker_evidence.failure_state` = `"published"` and present(`reply.actors[a].subprocess.worker_evidence.failure`) and `reply.actors[a].subprocess.worker_evidence.failure.operation` = `5` and `reply.actors[a].subprocess.worker_evidence.failure.code` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `2`) | [set_value(`reply.actors[a].application.state`, `"not_attempted"`), set_value(`reply.actors[a].application.basis`, `"terminal_compile_refusal"`)]. |
| <a id="contract-actor_evidence-application-classify-timing"></a>9. Timing refusal | (present(`reply.actors[a].subprocess`) and present(`reply.actors[a].subprocess.worker_evidence`) and `reply.actors[a].subprocess.worker_evidence.failure_state` = `"published"` and present(`reply.actors[a].subprocess.worker_evidence.failure`) and `reply.actors[a].subprocess.worker_evidence.failure.operation` = `12` and ((`reply.actors[a].subprocess.worker_evidence.failure.code` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `1`) or (`reply.actors[a].subprocess.worker_evidence.failure.code` = `14` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `0`) or (`reply.actors[a].subprocess.worker_evidence.failure.code` = `15` and `reply.actors[a].subprocess.worker_evidence.failure.detail` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `0`))) | [set_value(`reply.actors[a].application.state`, `"not_attempted"`), set_value(`reply.actors[a].application.basis`, `"terminal_timing_refusal"`)]. |
| <a id="contract-actor_evidence-application-classify-boundary"></a>10. Apply boundary without result | (present(`reply.actors[a].subprocess`) and present(`reply.actors[a].subprocess.worker_evidence`) and present(`reply.actors[a].subprocess.worker_evidence.progress`) and `reply.actors[a].subprocess.worker_evidence.progress.operation` = `8` and `reply.actors[a].subprocess.worker_evidence.progress.stage` ∈ [`1`, `2`]) | [set_value(`reply.actors[a].application.state`, `"unobserved"`), set_value(`reply.actors[a].application.basis`, `"apply_call_boundary_without_result"`)]. |
| <a id="contract-actor_evidence-application-classify-remaining"></a>11. Remaining evidence | `true` | [set_value(`reply.actors[a].application.state`, `"unobserved"`), set_value(`reply.actors[a].application.basis`, `"no_eligible_apply_publication"`)]. |

<a id="contract-actor_evidence-application-late_application"></a>
#### Setup deadline and later application

Final collection preserves a later applied publication and derives application_count from it after setup eligibility has ended. A setup_timeout can therefore coexist with applied true, count 1 and application state observed with basis applied_publication. The affected actor remains ineligible for phase activation and query collection.

<a id="contract-actor_evidence-application-late_application-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Setup deadline and later application](#contract-actor_evidence-application-late_application).** Final collection retains application independently of earlier setup eligibility. Context: Static review of the cited producer and assertion branches. Evidence limit: The read controls use 40 ms setup, 150 ms pre-ready delay and 1000 ms grace, then retain the production reply. Their timing observation is bounded to that schedule. [Evidence details](CONTRACT.md#contract-actor_evidence-application-late_application-disposition_support-details).

<a id="contract-actor_evidence-phase"></a>
### Phase collection and execution

Record `ae_phase`: `PWRunnerPhaseResult`.

The host reports phases in declared schedule order. Observation fields record activation's consequences separately from the declared phase and action identities.

- <a id="contract-actor_evidence-phase-phase_id"></a>**`phase_id`** (string): Submitted phase identifier used by its action records and validator collection. Ordinary semantic replies require a nonempty, NUL-free identifier within its admitted UTF-8 capacity. The declared phase order determines its ordinal.
- <a id="contract-actor_evidence-phase-ordinal"></a>**`ordinal`** (integer): One-based position in the global phase schedule.
- <a id="contract-actor_evidence-phase-action_ids"></a>**`action_ids`** (array of string): Declared action identifiers in phase order, retained even when actions produce no execution observations.
- <a id="contract-actor_evidence-phase-arrival_observed"></a>**`arrival_observed`** (boolean): Whether the host acquired the active worker's arrival publication for this visit.
- <a id="contract-actor_evidence-phase-completion_observed"></a>**`completion_observed`** (boolean): Whether the host acquired completion for this visit.
- <a id="contract-actor_evidence-phase-collection_status"></a>**`collection_status`** (string): collected, not_needed, budget_exhausted, clock_unavailable or not_reached. collected identifies an invoked collection even when validator I/O or decoding later fails. Admitted vocabulary: closed; displayed list: exhaustive: `"collected"`, `"not_needed"`, `"budget_exhausted"`, `"clock_unavailable"`, `"not_reached"`.
- <a id="contract-actor_evidence-phase-ordering"></a>**`ordering`** ([Collection and release observations](#contract-steps-ordering)?): Collection/release order observations for this phase, including host proceed store and worker acknowledgement.
- <a id="contract-actor_evidence-phase-validator_subprocess"></a>**`validator_subprocess`** ([Validator subprocess](#contract-lifecycle-validator)?): Child-process and accepted-verdict account for this phase's validator collection.
- <a id="contract-actor_evidence-phase-validator_spawn_failure"></a>**`validator_spawn_failure`** ([Native spawn failure](#contract-lifecycle-spawn_failure)?): Native validator spawn failure before a validator child existed.
- <a id="contract-actor_evidence-phase-actor_id"></a>**`actor_id`** (string?): Actor owning this phase in actor form; absent for the single-worker form.
- <a id="contract-actor_evidence-phase-actor_visit"></a>**`actor_visit`** (integer?): One-based visit number within this actor's declared visits, distinct from global ordinal.
- <a id="contract-actor_evidence-phase-visit_timing"></a>**`visit_timing`** ([Visit intervals](#contract-actor_evidence-timing)?): Host-measured intervals for reached visit boundaries; missing intervals retain unavailable clock/boundary observations.
- <a id="contract-actor_evidence-phase-termination_gate"></a>**`termination_gate`** ([Termination dependency](#contract-actor_evidence-gate)?): Dependency observation for a phase declaring after_termination, including gates left not_reached.
- <a id="contract-actor_evidence-phase-activation_observation"></a>**`activation_observation`** ([Host activation observation](#contract-actor_evidence-activation)?): Host release-store observation which activates this phase, with its actor-local capture ordinal and optional time.

<a id="contract-actor_evidence-activation"></a>
### Host activation observation

Record `ae_activation`: `PWRunnerActorActivation`.

- <a id="contract-actor_evidence-activation-capture_ordinal"></a>**`capture_ordinal`** (integer): Positive sequence position of this host activation store among observations of the same child.
- <a id="contract-actor_evidence-activation-observed_ns"></a>**`observed_ns`** (integer?): Host monotonic time in nanoseconds after the store, when the clock supplied it.

<a id="contract-actor_evidence-timing"></a>
### Visit intervals

Record `ae_timing`: `PWRunnerVisitTiming`.

Each interval measures two host observations in milliseconds; an unavailable or backward clock leaves that interval absent.

- <a id="contract-actor_evidence-timing-activation_to_arrival_ms"></a>**`activation_to_arrival_ms`** (integer?): Time between the host activation store and acquired worker arrival.
- <a id="contract-actor_evidence-timing-collection_ms"></a>**`collection_ms`** (integer?): Time spent in the phase's synchronous query-collection hook.
- <a id="contract-actor_evidence-timing-arrival_to_release_ms"></a>**`arrival_to_release_ms`** (integer?): Time from observed arrival to the host proceed release store.
- <a id="contract-actor_evidence-timing-release_to_completion_ms"></a>**`release_to_completion_ms`** (integer?): Time from the release store to acquired worker completion.

<a id="contract-actor_evidence-schedule"></a>
### Schedule account

Record `ae_schedule`: `PWRunnerScheduleRecord`.

- <a id="contract-actor_evidence-schedule-setup_wait"></a>**`setup_wait`** ([Measured host wait](#contract-lifecycle-host_wait)?): Measured shared setup wait for the actor set.
- <a id="contract-actor_evidence-schedule-execution_wait"></a>**`execution_wait`** ([Measured host wait](#contract-lifecycle-host_wait)?): Measured schedule traversal wait, with collection excluded when separately budgeted.
- <a id="contract-actor_evidence-schedule-lifetime_budget_ms"></a>**`lifetime_budget_ms`** (integer): Overall actor-run lifetime allowance, <!-- span limits.actor_lifetime_cutoff.value_unit -->180,000 milliseconds<!-- /span --> in the production plan.
- <a id="contract-actor_evidence-schedule-collection_budget_ms"></a>**`collection_budget_ms`** (integer): Recorded production maximum for aggregate query collection across actor phases: <!-- span limits.actor_collection_allowance.value_unit -->30,000 milliseconds<!-- /span -->. The host reports this maximum even when the `validator_total_timeout_ms` test control reduces the allowance used for collection.
- <a id="contract-actor_evidence-schedule-cancelled"></a>**`cancelled`** (string?): Recorded schedule cancellation reason, such as preparation_refused, execution_allowance_exhausted, an equipment failure or termination_dependency followed by its outcome; absent when no cancellation was recorded.

<a id="contract-actor_evidence-gate"></a>
### Termination dependency

Record `ae_gate`: `PWRunnerTerminationGate`.

The gate belongs to the dependent phase and observes the named source actor after that source’s final scheduled visit was activated.

- <a id="contract-actor_evidence-gate-source_actor_id"></a>**`source_actor_id`** (string): Different actor named by the dependent phase's after_termination declaration.
- <a id="contract-actor_evidence-gate-source_final_phase_id"></a>**`source_final_phase_id`** (string): Source actor's last declared phase, which must precede the dependent phase in the global schedule.
- <a id="contract-actor_evidence-gate-condition"></a>**`condition`** (string): terminated, the supported dependency condition. Admitted vocabulary: closed; displayed list: exhaustive: `"terminated"`.
- <a id="contract-actor_evidence-gate-outcome"></a>**`outcome`** (string): not_reached, satisfied, timed_out, ownership_lost, clock_unavailable, source_unavailable, source_departure_requested or execution_allowance_exhausted; each is defined by the gate rule below. Admitted vocabulary: closed; displayed list: exhaustive: `"not_reached"`, `"satisfied"`, `"timed_out"`, `"ownership_lost"`, `"clock_unavailable"`, `"source_unavailable"`, `"source_departure_requested"`, `"execution_allowance_exhausted"`.
- <a id="contract-actor_evidence-gate-wait"></a>**`wait`** ([Measured host wait](#contract-lifecycle-host_wait)?): Host dependency wait, with budget capped at <!-- span limits.actor_termination_wait.value_unit -->5,000 milliseconds<!-- /span --> and charged to remaining execution allowance. Absent for not_reached.
- <a id="contract-actor_evidence-gate-observation"></a>**`observation`** ([Owned-ending reference](#contract-lifecycle-reap_reference)?): Reference to the source actor's owned ending captured by the evaluated gate, when available; a late ending can remain beside a failed gate.
- <a id="contract-actor_evidence-gate-activation_eligible"></a>**`activation_eligible`** (boolean): True exactly for a satisfied gate, allowing this dependent phase to proceed to activation.
- <a id="contract-actor_evidence-gate-capture_ordinal"></a>**`capture_ordinal`** (integer?): Capture of the gate result in the source child's host-observation sequence; absent for not_reached and when no source session supplies a sequence.

<a id="contract-actor_evidence-gate-prepared_association"></a>
#### Prepared actor phase and gate records

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at prepared actor reply assembly. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Binding `q`: entry in `request.phases`. Binding `p`: entry in `reply.phases`. Association restriction for `p`: `p` = `q`. Applies when (present(`request.actors`) and `reply.execution_form` = `"actors"` and absent(`reply.preparation_failure`) and absent(`reply.reporting_failure`)).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actor_evidence-gate-prepared_association-cardinality"></a>Phase cardinality | Requires (present(`request.phases`) and count(`reply.phases`) = count(`request.phases`)). |
| <a id="contract-actor_evidence-gate-prepared_association-rows"></a>Each phase and declared gate | For each `q`, `p`. Requires (`reply.phases[p].phase_id` = `request.phases[q].phase_id` and `reply.phases[p].ordinal` = (`q` + `1`) and `reply.phases[p].actor_id` = `request.phases[q].actor_id` and implies(present(`request.phases[q].after_termination`), (present(`reply.phases[p].termination_gate`) and `reply.phases[p].termination_gate.source_actor_id` = `request.phases[q].after_termination.actor_id`)) and implies(absent(`request.phases[q].after_termination`), absent(`reply.phases[p].termination_gate`))). The scheduler installs every declared gate before cancellation, allowance and dependent availability checks, then assembly copies that gate into the phase row. Its source final phase comes from the source actor's last preceding phase in the normalized plan. Preparation refusals carry their separate before-launch phase account. |

<a id="contract-actor_evidence-gate-evaluate"></a>
#### Evaluating and applying the dependency

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at serial actor schedule before dependent activation. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Binding `q`: entry in `request.phases`. Binding `p`: entry in `reply.phases`. Association restriction for `p`: `p` = `q`. For each `q`, `p`. Applies when (present(`request.actors`) and present(`request.phases`) and present(`request.phases[q].after_termination`) and `reply.execution_form` = `"actors"` and absent(`reply.preparation_failure`) and absent(`reply.reporting_failure`)). Requires [Phase cardinality](#contract-actor_evidence-gate-prepared_association-cardinality), [Each phase and declared gate](#contract-actor_evidence-gate-prepared_association-rows). Evaluate only after the schedule remains uncancelled, its allowance is positive, and the dependent actor session, usable setup, unstopped state and visit are available. Evaluation first checks the source session and final declared phase activation; unavailable source evidence gives source_unavailable. A failed evaluated gate prevents dependent activation, collection and release, and cancels every later scheduled phase regardless of its actor. Cleanup and final collection continue for launched actors.

The dependency wait observes the owned source child without requesting its
departure. Its budget is the lesser of <!-- span limits.actor_termination_wait.value_unit -->5,000 milliseconds<!-- /span --> and the remaining
execution allowance in whole milliseconds. Deadline samples and final elapsed
accounting govern satisfaction. These are charged-wait conditions; operating
system scheduling determines when the host next runs.

A failed evaluated gate sets `schedule.cancelled` to
`termination_dependency:<outcome>`. Later phases retain their declarations
with collection `not_reached`, false arrival/completion and absent activation
and visit timing. Their own gates remain `not_reached`. Final cleanup may add
the source's later owned ending while the failed gate keeps the observation
reference captured during its evaluation.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actor_evidence-gate-evaluate-eligibility_assignment"></a>Eligibility assigned by evaluation | set_value(`reply.phases[p].termination_gate.activation_eligible`, `reply.phases[p].termination_gate.outcome` = `"satisfied"`). |
| <a id="contract-actor_evidence-gate-evaluate-satisfied"></a>Satisfied | Value: `"satisfied"`. The source final activation precedes a natural owned reap in its child sequence; both timestamps exist and activation time is at most reap time. Ownership is unbroken, departure_requested is false, budget is positive, deadline samples permit the reap, and final wait has a valid elapsed interval at most budget. The gate closes after the source's owned ending. A normal exit or signaled ending can qualify; natural means the host had not requested departure. Source final-phase completion is a separate observation from activation and owned termination. |
| <a id="contract-actor_evidence-gate-evaluate-not_reached"></a>Unreached | Value: `"not_reached"`. Cancellation, exhausted schedule allowance or an unavailable dependent actor or visit stopped traversal before this gate was evaluated. Its wait, observation and capture ordinal are absent and eligibility is false. An unavailable dependent actor can leave this gate unreached while later otherwise eligible phases remain schedulable. |
| <a id="contract-actor_evidence-gate-evaluate-source_unavailable"></a>Source unavailable | Value: `"source_unavailable"`. The source session, final activation, or required activation-before-ending order was unavailable. |
| <a id="contract-actor_evidence-gate-evaluate-execution_allowance_exhausted"></a>No remaining gate allowance | Value: `"execution_allowance_exhausted"`. Evaluation began with no positive whole-millisecond gate budget. |
| <a id="contract-actor_evidence-gate-evaluate-clock_unavailable"></a>Timing unavailable | Value: `"clock_unavailable"`. A deadline sample, required activation/reap time or final elapsed accounting was unavailable or moved backward. Retained fields provide the available context for this timing failure. |
| <a id="contract-actor_evidence-gate-evaluate-timed_out"></a>Gate timeout | Value: `"timed_out"`. The deadline or wait expired, including after a reap, or final elapsed time exceeded budget. A retained reap reference establishes that capture while this outcome records failure to establish timely satisfaction. |
| <a id="contract-actor_evidence-gate-evaluate-ownership_lost"></a>Ownership lost | Value: `"ownership_lost"`. The host's uninterrupted source ownership was lost or its source wait failed. |
| <a id="contract-actor_evidence-gate-evaluate-source_departure_requested"></a>Departure requested | Value: `"source_departure_requested"`. The host had requested the source's departure before the eligible ending. |

<a id="contract-actor_evidence-gate-check"></a>
#### Checking a carried gate

[Controller](CONTRACT.md#contract-identity-definitions-controller) checks at semantic assessment after reply admission. Entry: cli run. Recipient: cli caller. Reports: runner reply. Binding `p`: entry in `reply.phases`. Binding `s`: entry in `reply.actors`. Binding `f`: entry in `reply.phases`. Association restriction for `s`: `reply.actors[s].actor_id` = `reply.phases[p].termination_gate.source_actor_id`. Association restriction for `f`: `reply.phases[f].phase_id` = `reply.phases[p].termination_gate.source_final_phase_id`. Applies when (absent(`reply.reporting_failure`) and `reply.execution_form` = `"actors"` and present(`reply.phases[p].termination_gate`)). The check retains each failed condition it finds. Resolve source and final-phase joins before using s or f; missing, nonfinal, same-actor or nonpreceding associations are findings. Check owned PID/native-status agreement, all conditional gate captures, independent actor setup/equipment eligibility and activation timing.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actor_evidence-gate-check-failed"></a>Failed carried-gate requirement | On failure, [set_value(`envelope.data.runner_sandbox_diagnostics.disposition_integrity`, `"invalid"`), set_value(`envelope.data.runner_sandbox_diagnostics.process_disposition`, `"withheld"`), set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"unknown"`), retain_records(`reply`), retain_assessments(`envelope.data.runner_sandbox_diagnostics.actors`)]. Uses [Select the public result](#contract-envelope-data-select). Append the actor_evidence finding for the failed requirement, with subject_path naming this phase's inspected termination_gate. Run result and exit status continue to follow their result-selection rule. |
| <a id="contract-actor_evidence-gate-check-unreached"></a>Unreached shape | Requires implies(`reply.phases[p].termination_gate.outcome` = `"not_reached"`, (absent(`reply.phases[p].termination_gate.wait`) and absent(`reply.phases[p].termination_gate.observation`) and absent(`reply.phases[p].termination_gate.capture_ordinal`))). |
| <a id="contract-actor_evidence-gate-check-timely"></a>Timely satisfied wait | Requires implies(`reply.phases[p].termination_gate.outcome` = `"satisfied"`, (present(`reply.phases[p].termination_gate.wait`) and `reply.phases[p].termination_gate.wait.budget_ms` > `0` and `reply.phases[p].termination_gate.wait.budget_ms` ≤ `5000` and present(`reply.phases[p].termination_gate.wait.elapsed_ms`) and `reply.phases[p].termination_gate.wait.elapsed_ms` ≤ `reply.phases[p].termination_gate.wait.budget_ms` and `reply.phases[p].termination_gate.wait.clock_fault` = `false` and absent(`reply.phases[p].termination_gate.wait.native_errno`))). Every present gate wait has budget 0–5000 and absent excluded time. An evaluated gate has a wait whose stop matches its outcome. |
| <a id="contract-actor_evidence-gate-check-sequence"></a>Source sequence | Requires implies(`reply.phases[p].termination_gate.outcome` = `"satisfied"`, (present(`reply.phases[f].activation_observation`) and present(`reply.actors[s].owned_reap`) and `reply.phases[f].activation_observation.capture_ordinal` < `reply.actors[s].owned_reap.capture_ordinal` and `reply.actors[s].owned_reap.capture_ordinal` < `reply.phases[p].termination_gate.capture_ordinal` and `reply.actors[s].owned_reap.ownership_unbroken` = `true` and `reply.actors[s].owned_reap.departure_requested` = `false`)). The referenced ending matches the source actor's valid PID/native wait status, has stage `schedule` or `termination_gate`, and has the reference's positive ordinal. Final activation and reap timestamps must exist in nondecreasing order; a timestamped dependent activation is at or after the reap. |
| <a id="contract-actor_evidence-gate-check-eligibility"></a>Eligibility consequence | Binding `d`: entry in `reply.actors`. Association restriction for `d`: (present(`reply.phases[p].actor_id`) and `reply.actors[d].actor_id` = `reply.phases[p].actor_id` and `reply.actors[d].setup_status` ∈ [`"applied"`, `"unapplied_declared"`] and present(`reply.actors[d].equipment`) and `reply.actors[d].equipment.execution.eligible` = `true`). For each `p`. Requires (implies(`reply.phases[p].termination_gate.activation_eligible` = `true`, (`reply.phases[p].termination_gate.outcome` = `"satisfied"` and present(`reply.actors`) and matches(`d`) > `0`)) and implies(`reply.phases[p].termination_gate.activation_eligible` = `false`, (absent(`reply.phases[p].activation_observation`) and absent(`reply.phases[p].visit_timing`) and `reply.phases[p].arrival_observed` = `false` and `reply.phases[p].collection_status` = `"not_reached"` and (absent(`reply.phases[p].ordering`) or (`reply.phases[p].ordering.proceed_set` = `false` and `reply.phases[p].ordering.proceed_observed` = `false`))))). |

<a id="contract-actor_evidence-gate-timeout_example"></a>
#### A timeout followed by cleanup

The source completes its final phase but remains alive when the dependency
times out. The dependent phase receives no activation, collection or release.
Cleanup later reaps the source; the gate remains `timed_out`.

<a id="contract-actor_evidence-gate-timeout_example-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [A timeout followed by cleanup](#contract-actor_evidence-gate-timeout_example) and its descendants.** Source phase completion, timeout, withheld dependent activation/collection/release, later source reap and unchanged timeout. Context: Real fixture child with post-apply hang and 50 ms execution allowance; test source inspected. Evidence limit: No execution credit; this assertion covers scheduler observations with shortened allowance, not public JSON or an additional later actor. [Evidence details](CONTRACT.md#contract-actor_evidence-gate-timeout_example-support-details).

<a id="contract-actor_evidence-gate-cancellation_evidence"></a>
#### Known gap: Termination cancellation reach

A failed evaluated termination dependency cancels every remaining scheduled phase, including later work owned by another actor. A dependent actor that is ineligible before gate evaluation has a not_reached gate and does not create that dependency failure. Whether cancellation should have narrower reach remains a maintainer decision.

<a id="contract-actor_evidence-gate-cancellation_evidence-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Termination cancellation reach](#contract-actor_evidence-gate-cancellation_evidence).** An evaluated failed gate sets global schedule cancellation; an unreached gate has a different path. Context: Static review of the cited producer and assertion branches. Evidence limit: The control distinguishes a three-worker evaluated timeout from an ineligible-dependent neighbour and retains final collection. [Evidence details](CONTRACT.md#contract-actor_evidence-gate-cancellation_evidence-disposition_support-details).

<a id="contract-actor_evidence-owned_endings"></a>
### Observation sequences

<a id="contract-actor_evidence-owned_endings-sequence"></a>
#### Actor-local sequence

The host maintains one observation counter for each owned child. Each activation
of that actor, its owned reap and each evaluated gate waiting for it consumes
the next ordinal. Source final activation, source reap and gate closure are
comparable within that source sequence. The dependent actor's activation has
its own sequence; its timestamp supplies the cross-process temporal comparison.
A `not_reached` gate consumes no gate-capture ordinal.
<!-- END GENERATED CONTRACT actor_evidence -->

## Read process and publication evidence

Use child observations and publication records when a report is incomplete. A requested termination, observed ending, reap, published operation and collected result have different meanings. The claim states and conflicts below retain those distinctions.

<!-- BEGIN GENERATED CONTRACT lifecycle -->
<a id="contract-lifecycle"></a>
## Process and operation observations

<a id="contract-lifecycle-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Process and operation observations](#contract-lifecycle) and its descendants.** Imported public field definitions joined to producer/decoder/assessment meanings; explicit rule and evidence gaps preserve scope. [Evidence details](CONTRACT.md#contract-lifecycle-support-details).

<a id="contract-lifecycle-worker"></a>
### Worker subprocess

Record `lc_worker`: `PWRunnerSubprocess`.

The host retains one process account for the fresh worker. Actor replies put this account on its actor; single-worker replies put it at run scope.

- <a id="contract-lifecycle-worker-pid"></a>**`pid`** (integer): PID returned by successful worker spawn and used for host waits and cleanup.
- <a id="contract-lifecycle-worker-term_signal"></a>**`term_signal`** (integer?): Signal decoded from a successful waitpid result for this child. A recorded cleanup request alone supplies no value here.
- <a id="contract-lifecycle-worker-exit_code"></a>**`exit_code`** (integer?): Exit status decoded after waitpid returned this child; zero is an observed exit status. Missing status stays unknown.
- <a id="contract-lifecycle-worker-partial_steps"></a>**`partial_steps`** (boolean): True when the canonical disposition contains any slot other than completed; false means all represented slots completed.
- <a id="contract-lifecycle-worker-worker_evidence"></a>**`worker_evidence`** ([Worker publication snapshot](#contract-lifecycle-worker_evidence)?): Acquired worker publication snapshot, including independent progress, failure, diagnostic and policy-read observations.
- <a id="contract-lifecycle-worker-policy_transfer_timeout"></a>**`policy_transfer_timeout`** ([Policy-pipe timeout](#contract-lifecycle-transfer_timeout)?): Host policy-pipe deadline observation with accepted-write counts.
- <a id="contract-lifecycle-worker-policy_transfer_error"></a>**`policy_transfer_error`** ([Policy-pipe write error](#contract-lifecycle-transfer_error)?): Host policy-pipe native write failure with accepted-write counts.
- <a id="contract-lifecycle-worker-ready_byte_received"></a>**`ready_byte_received`** (boolean?): Whether the host read the worker's readiness byte. False records the missing hint at that boundary.
- <a id="contract-lifecycle-worker-done_observed"></a>**`done_observed`** (boolean?): Final acquire observation of the worker's done flag after cleanup. Earlier polling termination remains in poll_stop_reason.
- <a id="contract-lifecycle-worker-poll_stop_reason"></a>**`poll_stop_reason`** (string?): Why host publication polling ended. Only sentinel_deadline names exhaustion of that polling allowance; later cleanup preserves this recorded reason. Admitted vocabulary: open; displayed list: illustrative: `"done"`, `"child_reaped"`, `"sentinel_deadline"`, `"wait_error"`, `"policy_write_error"`, `"policy_transfer_deadline"`. Unfamiliar values: The host string is retained; an unfamiliar reason establishes only that recorded reason, and gains no known timeout or cause meaning.
- <a id="contract-lifecycle-worker-exit_requested"></a>**`exit_requested`** (boolean?): Whether the host performed the release store asking the worker to exit. Worker receipt is a separate observation.
- <a id="contract-lifecycle-worker-termination_request"></a>**`termination_request`** ([Host termination request](#contract-lifecycle-termination)?): Host kill call, its requested signal and native return. Absence means no retained request.
- <a id="contract-lifecycle-worker-reaped"></a>**`reaped`** (boolean?): True when waitpid returned this child PID; false explicitly records unconfirmed disposition. Absence means the observation is unavailable.
- <a id="contract-lifecycle-worker-wait_errors"></a>**`wait_errors`** (array of [Failed host wait](#contract-lifecycle-wait_error)?): Failed host waitpid calls, including recovered EINTR. Empty means none observed; absence means unavailable.
- <a id="contract-lifecycle-worker-cleanup_trigger"></a>**`cleanup_trigger`** (string?): Why the host requested exit, derived at final collection from the stop reason it held when it stored the request: sentinel_deadline gives deadline_expiry; done and, in the actor form, schedule_complete, ended_before_arrival and ended_before_completion give completion; child_reaped gives child_reaped; wait_error gives poll_wait_error; policy_write_error and policy_transfer_deadline give policy_transfer_error and policy_transfer_timeout. Any other stop reason is carried unchanged. The value restates poll_stop_reason and is not a second observation. Admitted vocabulary: open; displayed list: illustrative: `"deadline_expiry"`, `"completion"`, `"child_reaped"`, `"poll_wait_error"`, `"policy_transfer_error"`, `"policy_transfer_timeout"`. Unfamiliar values: The host string is retained; a value outside this list is a stop reason carried unchanged, and selects no termination cause label.
- <a id="contract-lifecycle-worker-grace_end"></a>**`grace_end`** (string?): How the post-request grace stage ended: not_entered, reaped_during_grace, exhausted or wait_error.
- <a id="contract-lifecycle-worker-collection_basis"></a>**`collection_basis`** (string?): Whether final reads followed a confirmed reap: after_confirmed_reap, execution_may_continue or unavailable. This controls terminal absence claims.
- <a id="contract-lifecycle-worker-ready_wait"></a>**`ready_wait`** ([Measured host wait](#contract-lifecycle-host_wait)?): Measured monotonic wait for the readiness hint, present when that stage ran. The production allowance is <!-- span limits.worker_ready_wait.value_unit -->1,000 milliseconds<!-- /span --> after successful policy delivery and readiness-pipe setup; actor setup can reduce it to the remaining shared setup allowance. The record carries the allowance actually assigned. Expiry leaves the readiness hint absent and execution continues.
- <a id="contract-lifecycle-worker-sentinel_wait"></a>**`sentinel_wait`** ([Measured host wait](#contract-lifecycle-host_wait)?): Measured publication wait, with synchronous validator collection charged separately through excluded_ms.
- <a id="contract-lifecycle-worker-exit_grace_wait"></a>**`exit_grace_wait`** ([Measured host wait](#contract-lifecycle-host_wait)?): Measured monotonic wait for departure after the host exit request, present when that stage ran. Its production allowance is <!-- span limits.worker_exit_grace.value_unit -->1,000 milliseconds<!-- /span -->; subsequent termination and final reap retain their own observations.
- <a id="contract-lifecycle-worker-disposition"></a>**`disposition`** ([Canonical worker disposition](#contract-lifecycle-disposition)?): Host-resolved lifecycle questions, step claims and conflicts. Ordinary subprocess reporting supplies this account and derives compatibility fields from it.

**partial_steps.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-lifecycle-worker-partial_steps-canonical"></a>Canonical incomplete-slot flag | Binding `c`: entry in `lc_worker.disposition.steps`. Association restriction for `c`: `lc_worker.disposition.steps[c].slot` ≠ `"completed"`. Requires implies(present(`lc_worker.disposition`), `lc_worker.partial_steps` = matches(`c`) > `0`). |

**disposition.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-lifecycle-worker-disposition-signal_value"></a>Supported signal value | Requires implies((present(`lc_worker.disposition`) and `lc_worker.disposition.questions.final_status.state` = `"supported"` and `lc_worker.disposition.questions.final_status.answer` = `"signal"`), (present(`lc_worker.disposition.questions.final_status.value`) and is_variant(`lc_worker.disposition.questions.final_status.value`, `"Integer"`) and variant(`lc_worker.disposition.questions.final_status.value`, `"Integer"`) = `lc_worker.term_signal`)). |
| <a id="contract-lifecycle-worker-disposition-exit_value"></a>Supported exit_code value | Requires implies((present(`lc_worker.disposition`) and `lc_worker.disposition.questions.final_status.state` = `"supported"` and `lc_worker.disposition.questions.final_status.answer` = `"exit_code"`), (present(`lc_worker.disposition.questions.final_status.value`) and is_variant(`lc_worker.disposition.questions.final_status.value`, `"Integer"`) and variant(`lc_worker.disposition.questions.final_status.value`, `"Integer"`) = `lc_worker.exit_code`)). |
| <a id="contract-lifecycle-worker-disposition-status_issue_exists"></a>Conflicting status issue exists | Requires implies((present(`lc_worker.disposition`) and `lc_worker.disposition.questions.final_status.state` = `"conflicting"`), count(`lc_worker.disposition.issues`) > `0`). |
| <a id="contract-lifecycle-worker-disposition-status_issue"></a>First status conflict issue | Binding `i`: entry in `lc_worker.disposition.issues`. Association restriction for `i`: `i` = `0`. For each `i`. Requires implies((present(`lc_worker.disposition`) and `lc_worker.disposition.questions.final_status.state` = `"conflicting"`), (`lc_worker.disposition.issues[i].kind` = `"conflict"` and `lc_worker.disposition.issues[i].rule` = `"D1"` and `lc_worker.disposition.issues[i].question` = `"final_status"` and absent(`lc_worker.disposition.issues[i].step_index`) and `lc_worker.disposition.issues[i].observations` = [`"exit_code"`, `"term_signal"`])). |

<a id="contract-lifecycle-worker-final_status"></a>
#### Resolve the final process status

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at worker disposition assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Select the first matching case in the listed order. Applies when present(`lc_worker.disposition`).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-lifecycle-worker-final_status-unreaped"></a>1. No successful reap | `lc_worker.reaped` ≠ `true` | [set_value(`lc_worker.disposition.questions.final_status.state`, `"unresolved"`), set_value(`lc_worker.disposition.questions.final_status.reason`, `"no_successful_reap"`), set_value(`lc_worker.disposition.questions.final_status.basis`, [`"reaped"`]), withhold(`lc_worker.disposition.questions.final_status.answer`), withhold(`lc_worker.disposition.questions.final_status.value`), withhold(`lc_worker.disposition.questions.final_status.issue`)]. |
| <a id="contract-lifecycle-worker-final_status-conflict"></a>2. Competing status forms | (present(`lc_worker.exit_code`) and present(`lc_worker.term_signal`)) | [set_value(`lc_worker.disposition.questions.final_status.state`, `"conflicting"`), set_value(`lc_worker.disposition.questions.final_status.issue`, `0`), withhold(`lc_worker.disposition.questions.final_status.answer`), withhold(`lc_worker.disposition.questions.final_status.value`), withhold(`lc_worker.disposition.questions.final_status.reason`), withhold(`lc_worker.disposition.questions.final_status.basis`)]. |
| <a id="contract-lifecycle-worker-final_status-signal"></a>3. Observed terminating signal | present(`lc_worker.term_signal`) | [set_value(`lc_worker.disposition.questions.final_status.state`, `"supported"`), set_value(`lc_worker.disposition.questions.final_status.answer`, `"signal"`), set_value(`lc_worker.disposition.questions.final_status.basis`, [`"reaped"`, `"term_signal"`]), withhold(`lc_worker.disposition.questions.final_status.reason`), withhold(`lc_worker.disposition.questions.final_status.issue`)]. |
| <a id="contract-lifecycle-worker-final_status-exit"></a>4. Observed exit status | present(`lc_worker.exit_code`) | [set_value(`lc_worker.disposition.questions.final_status.state`, `"supported"`), set_value(`lc_worker.disposition.questions.final_status.answer`, `"exit_code"`), set_value(`lc_worker.disposition.questions.final_status.basis`, [`"reaped"`, `"exit_code"`]), withhold(`lc_worker.disposition.questions.final_status.reason`), withhold(`lc_worker.disposition.questions.final_status.issue`)]. |
| <a id="contract-lifecycle-worker-final_status-missing"></a>5. Unusable owned status | `true` | [set_value(`lc_worker.disposition.questions.final_status.state`, `"unresolved"`), set_value(`lc_worker.disposition.questions.final_status.reason`, `"status_unusable"`), set_value(`lc_worker.disposition.questions.final_status.basis`, [`"reaped"`]), withhold(`lc_worker.disposition.questions.final_status.answer`), withhold(`lc_worker.disposition.questions.final_status.value`), withhold(`lc_worker.disposition.questions.final_status.issue`)]. |

<a id="contract-lifecycle-worker-final_status-source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Resolve the final process status](#contract-lifecycle-worker-final_status) and its descendants.** The first five branches derive the final-status claim and place the D1 conflict first in the issue array. [Evidence details](CONTRACT.md#contract-lifecycle-worker-final_status-source-details).

<a id="contract-lifecycle-worker-resolve_stop_reason"></a>
#### Copy the polling stop

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at worker disposition assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Select the first matching case in the listed order. Applies when present(`lc_worker.disposition`).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-lifecycle-worker-resolve_stop_reason-recorded"></a>1. Recorded observation | present(`lc_worker.poll_stop_reason`) | [set_value(`lc_worker.disposition.questions.stop_reason.state`, `"supported"`), set_value(`lc_worker.disposition.questions.stop_reason.answer`, `lc_worker.poll_stop_reason`), set_value(`lc_worker.disposition.questions.stop_reason.basis`, [`"poll_stop_reason"`]), withhold(`lc_worker.disposition.questions.stop_reason.value`), withhold(`lc_worker.disposition.questions.stop_reason.reason`), withhold(`lc_worker.disposition.questions.stop_reason.issue`)]. |
| <a id="contract-lifecycle-worker-resolve_stop_reason-missing"></a>2. Unrecorded observation | `true` | [set_value(`lc_worker.disposition.questions.stop_reason.state`, `"unresolved"`), set_value(`lc_worker.disposition.questions.stop_reason.reason`, `"not_recorded"`), withhold(`lc_worker.disposition.questions.stop_reason.answer`), withhold(`lc_worker.disposition.questions.stop_reason.value`), withhold(`lc_worker.disposition.questions.stop_reason.issue`), withhold(`lc_worker.disposition.questions.stop_reason.basis`)]. |

<a id="contract-lifecycle-worker-resolve_stop_reason-source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Copy the polling stop](#contract-lifecycle-worker-resolve_stop_reason) and its descendants.** A present host string is copied verbatim with its basis; absence produces the unresolved not_recorded claim. [Evidence details](CONTRACT.md#contract-lifecycle-worker-resolve_stop_reason-source-details).

<a id="contract-lifecycle-worker-resolve_collection_basis"></a>
#### Copy the final collection basis

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at worker disposition assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Select the first matching case in the listed order. Applies when present(`lc_worker.disposition`).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-lifecycle-worker-resolve_collection_basis-recorded"></a>1. Recorded observation | present(`lc_worker.collection_basis`) | [set_value(`lc_worker.disposition.questions.collection_basis.state`, `"supported"`), set_value(`lc_worker.disposition.questions.collection_basis.answer`, `lc_worker.collection_basis`), set_value(`lc_worker.disposition.questions.collection_basis.basis`, [`"collection_basis"`]), withhold(`lc_worker.disposition.questions.collection_basis.value`), withhold(`lc_worker.disposition.questions.collection_basis.reason`), withhold(`lc_worker.disposition.questions.collection_basis.issue`)]. |
| <a id="contract-lifecycle-worker-resolve_collection_basis-missing"></a>2. Unrecorded observation | `true` | [set_value(`lc_worker.disposition.questions.collection_basis.state`, `"unresolved"`), set_value(`lc_worker.disposition.questions.collection_basis.reason`, `"not_recorded"`), withhold(`lc_worker.disposition.questions.collection_basis.answer`), withhold(`lc_worker.disposition.questions.collection_basis.value`), withhold(`lc_worker.disposition.questions.collection_basis.issue`), withhold(`lc_worker.disposition.questions.collection_basis.basis`)]. |

<a id="contract-lifecycle-worker-resolve_collection_basis-source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Copy the final collection basis](#contract-lifecycle-worker-resolve_collection_basis) and its descendants.** A present host string is copied verbatim with its basis; absence produces the unresolved not_recorded claim. [Evidence details](CONTRACT.md#contract-lifecycle-worker-resolve_collection_basis-source-details).

<a id="contract-lifecycle-host_wait"></a>
### Measured host wait

Record `lc_host_wait`: `PWHostWait`.

A wait records the host boundary at which it moved on. Budgets and elapsed values use milliseconds on CLOCK_MONOTONIC.

- <a id="contract-lifecycle-host_wait-budget_ms"></a>**`budget_ms`** (integer): Allowance assigned to this wait; its owning operation defines the cap and whether other work is excluded.
- <a id="contract-lifecycle-host_wait-elapsed_ms"></a>**`elapsed_ms`** (integer?): Measured interval at stop. Absence records that the clock could not supply a valid nondecreasing interval.
- <a id="contract-lifecycle-host_wait-stop"></a>**`stop`** (string): Owning operation's reason for ending this wait. clock_unavailable denotes failed or backward time with bounded sleep fallback; setup_failed denotes an unavailable nonblocking prerequisite.
- <a id="contract-lifecycle-host_wait-excluded_ms"></a>**`excluded_ms`** (integer?): Measured synchronous work excluded from this wait's allowance. For sentinel waiting, consumed allowance is elapsed_ms minus excluded_ms; absence means this exclusion is unreported or inapplicable.
- <a id="contract-lifecycle-host_wait-native_errno"></a>**`native_errno`** (integer?): Native error captured by the wait's failing prerequisite or observation, when that branch supplies one.
- <a id="contract-lifecycle-host_wait-clock_fault"></a>**`clock_fault`** (boolean): Whether the monotonic clock failed or moved backward during this wait.

<a id="contract-lifecycle-termination"></a>
### Host termination request

Record `lc_termination`: `PWRunnerTerminationRequest`.

Each record preserves one host kill call. The return establishes whether the request was accepted by that call; the child's ending is reported by reaping.

- <a id="contract-lifecycle-termination-signal"></a>**`signal`** (integer): Signed 32-bit signal argument passed to kill.
- <a id="contract-lifecycle-termination-rc"></a>**`rc`** (integer): Signed 32-bit native kill return, retained without a signal-result allowlist.
- <a id="contract-lifecycle-termination-errno"></a>**`errno`** (integer?): Immediately captured errno when rc is -1; absent after another return.

<a id="contract-lifecycle-wait_error"></a>
### Failed host wait

Record `lc_wait_error`: `PWRunnerWaitError`.

The host records each failed waitpid call even if a later retry reaps the child.

- <a id="contract-lifecycle-wait_error-stage"></a>**`stage`** (string): Host stage of the call, including poll, exit_grace and after_termination. Admitted vocabulary: open; displayed list: illustrative: `"poll"`, `"exit_grace"`, `"after_termination"`. Unfamiliar values: The recorded stage and native error remain available without an invented known-stage interpretation.
- <a id="contract-lifecycle-wait_error-rc"></a>**`rc`** (integer): Native waitpid return; producer records this object for -1.
- <a id="contract-lifecycle-wait_error-errno"></a>**`errno`** (integer): Error captured before another native call; EINTR may be followed by a recovered wait.

<a id="contract-lifecycle-transfer_timeout"></a>
### Policy-pipe timeout

Record `lc_transfer_timeout`: `PWWorkerPolicyTransferTimeout`.

Host write counts and worker read receipts describe separate ends of the policy pipe.

- <a id="contract-lifecycle-transfer_timeout-budget_ms"></a>**`budget_ms`** (integer): Host policy-transfer allowance in milliseconds. Production assigns <!-- span limits.worker_policy_transfer.value_unit -->5,000 milliseconds<!-- /span --> from an absolute monotonic deadline established immediately after spawn; partial writes and interrupted calls keep that deadline. Actor delivery is additionally capped by the remaining shared setup allowance. This field reports the assigned allowance.
- <a id="contract-lifecycle-transfer_timeout-elapsed_ms"></a>**`elapsed_ms`** (integer): Measured transfer interval when its deadline expired.
- <a id="contract-lifecycle-transfer_timeout-bytes_written"></a>**`bytes_written`** (integer): UTF-8 policy bytes accepted by host write calls before timeout.
- <a id="contract-lifecycle-transfer_timeout-bytes_expected"></a>**`bytes_expected`** (integer): Total UTF-8 policy bytes the host attempted to send.

<a id="contract-lifecycle-transfer_error"></a>
### Policy-pipe write error

Record `lc_transfer_error`: `PWWorkerPolicyTransferError`.

This record belongs to the host's transport of the selected source bytes.

- <a id="contract-lifecycle-transfer_error-errno"></a>**`errno`** (integer): Native errno captured from the failed policy-pipe write.
- <a id="contract-lifecycle-transfer_error-bytes_written"></a>**`bytes_written`** (integer): Policy bytes accepted by preceding writes before this failure.
- <a id="contract-lifecycle-transfer_error-bytes_expected"></a>**`bytes_expected`** (integer): Total selected policy bytes the host attempted to send.

<a id="contract-lifecycle-worker_evidence"></a>
### Worker publication snapshot

Record `lc_worker_evidence`: `PWWorkerEvidence`.

The host first checks the shared region's worker identity, then acquire-reads each publication independently. Available publications retain their own scopes.

- <a id="contract-lifecycle-worker_evidence-abi_identity"></a>**`abi_identity`** (string (hex)): Host-selected worker protocol identity copied into the report after the region identity check.
- <a id="contract-lifecycle-worker_evidence-progress"></a>**`progress`** ([Worker progress](#contract-lifecycle-progress)?): Last acquired nonzero packed worker progress word, decoded into operation, stage and optional index.
- <a id="contract-lifecycle-worker_evidence-failure_publication"></a>**`failure_publication`** (integer): Raw terminal-failure publication word, including unfamiliar numeric values. Admitted vocabulary: open; displayed list: illustrative: `0`, `1`, `2`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions.
- <a id="contract-lifecycle-worker_evidence-failure_state"></a>**`failure_state`** (string): Host interpretation of the publication and eligible failure payload: absent, incomplete, published or invalid. Admitted vocabulary: closed; displayed list: exhaustive: `"absent"`, `"incomplete"`, `"published"`, `"invalid"`.
- <a id="contract-lifecycle-worker_evidence-failure"></a>**`failure`** ([Terminal worker failure](#contract-lifecycle-failure)?): Terminal worker failure payload when its publication and layout guards allow decoding.
- <a id="contract-lifecycle-worker_evidence-readiness"></a>**`readiness`** ([Readiness-write result](#contract-lifecycle-readiness)?): Worker publication of the readiness-write native result, independent of the host's receipt of the byte.
- <a id="contract-lifecycle-worker_evidence-diagnostic"></a>**`diagnostic`** ([Worker diagnostic](#contract-lifecycle-diagnostic)): Diagnostic publication state and eligible bounded diagnostic text.
- <a id="contract-lifecycle-worker_evidence-policy_read"></a>**`policy_read`** ([Worker policy receipt](#contract-lifecycle-policy_read)?): Worker EOF receipt, published before comparing received and expected lengths; missing receipt leaves delivery unknown.

<a id="contract-lifecycle-progress"></a>
### Worker progress

Record `lc_progress`: `PWWorkerProgress`.

Progress is an acquired protocol position. Numeric operation and stage codes are open; the lifecycle resolver names an unfamiliar position progress_unrecognized.

- <a id="contract-lifecycle-progress-raw"></a>**`raw`** (integer): Packed UInt32 progress value: operation in the high byte, stage in the next four bits, and one-based optional item in the low twenty bits.
- <a id="contract-lifecycle-progress-operation"></a>**`operation`** (integer): Numeric worker operation decoded from raw; known protocol order runs header validation, clock setup, policy read, parameter/compile/apply work, activation/release waits, attempts and completion. Admitted vocabulary: open; displayed list: illustrative: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`, `13`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions.
- <a id="contract-lifecycle-progress-stage"></a>**`stage`** (integer): Numeric boundary stage decoded from raw; 1 is entry and 2 is return for recognized lifecycle positions. Admitted vocabulary: open; displayed list: illustrative: `1`, `2`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions.
- <a id="contract-lifecycle-progress-index"></a>**`index`** (integer?): Zero-based item decoded from the low bits; attempts use the plan slot, parameter setup uses its parameter, and actor waits identify the next visit's first slot.

<a id="contract-lifecycle-failure"></a>
### Terminal worker failure

Record `lc_failure`: `PWWorkerFailure`.

Numeric codes retain unfamiliar values.

- <a id="contract-lifecycle-failure-operation"></a>**`operation`** (integer): Worker operation at which the terminal failure was published. Admitted vocabulary: open; displayed list: illustrative: `1`, `2`, `3`, `4`, `5`, `8`, `12`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions.
- <a id="contract-lifecycle-failure-code"></a>**`code`** (integer): PW failure classification within that operation. Admitted vocabulary: open; displayed list: illustrative: `1`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions.
- <a id="contract-lifecycle-failure-native_kind"></a>**`native_kind`** (integer): Discriminator for the retained native observation: 0 has no native result, 1 is an integer return, 2 is a null-pointer result represented by zero; unfamiliar codes retain their number. Admitted vocabulary: open; displayed list: illustrative: `0`, `1`, `2`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions.
- <a id="contract-lifecycle-failure-native_result"></a>**`native_result`** (integer?): Signed native return when native_kind supplies one; a null-pointer result is zero.
- <a id="contract-lifecycle-failure-errno"></a>**`errno`** (integer?): Native errno when the publication marks it present.
- <a id="contract-lifecycle-failure-index"></a>**`index`** (integer?): Operation-specific zero-based item, such as a parameter or attempt; absence represents the worker's no-index sentinel.
- <a id="contract-lifecycle-failure-detail"></a>**`detail`** (integer): Additional operation-specific numeric classification retained alongside the primary failure code. Admitted vocabulary: open; displayed list: illustrative: `0`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions.

<a id="contract-lifecycle-readiness"></a>
### Readiness-write result

Record `lc_readiness`: `PWWorkerReadiness`.

This is the worker's own publication of the readiness helper result. The helper retries EINTR and converts a one-byte write to success.

- <a id="contract-lifecycle-readiness-rc"></a>**`rc`** (integer): Readiness-helper result: zero after one byte was written; -1 after a persistent failure.
- <a id="contract-lifecycle-readiness-errno"></a>**`errno`** (integer?): Worker-captured errno accompanying a nonzero helper result; absent for rc zero.

<a id="contract-lifecycle-diagnostic"></a>
### Worker diagnostic

Record `lc_diagnostic`: `PWWorkerDiagnostic`.

The host exposes text only after acquiring a complete or truncated publication with a bounded length and terminating NUL.

- <a id="contract-lifecycle-diagnostic-state"></a>**`state`** (integer): Raw diagnostic publication word: 0 absent, 1 complete, 2 truncated, 3 incomplete; other values remain numeric. Admitted vocabulary: open; displayed list: illustrative: `0`, `1`, `2`, `3`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions.
- <a id="contract-lifecycle-diagnostic-status"></a>**`status`** (string): Host interpretation: absent, incomplete, unknown, complete, truncated or invalid. Invalid identifies an eligible publication whose length or terminator failed validation. Admitted vocabulary: closed; displayed list: exhaustive: `"absent"`, `"incomplete"`, `"unknown"`, `"complete"`, `"truncated"`, `"invalid"`.
- <a id="contract-lifecycle-diagnostic-length"></a>**`length`** (integer?): Retained diagnostic-byte length excluding its terminating NUL, at most <!-- span limits.worker_diagnostic.value_unit -->4,095 bytes<!-- /span --> when validation permits text extraction.
- <a id="contract-lifecycle-diagnostic-text"></a>**`text`** (string?): Diagnostic bytes decoded as UTF-8 with replacement for invalid sequences. The <!-- span limits.worker_diagnostic.value_unit -->4,095 bytes<!-- /span --> bound applies before replacement decoding. The diagnostic status carries whether the worker truncated its buffer.

<a id="contract-lifecycle-policy_read"></a>
### Worker policy receipt

Record `lc_policy_read`: `PWWorkerPolicyRead`.

At EOF the worker publishes both counts before comparing them. A header refusal, read failure or overflow leaves this receipt unavailable; both counts must fit the <!-- span limits.policy_source.value -->262,143<!-- /span -->-byte source capacity.

- <a id="contract-lifecycle-policy_read-bytes_expected"></a>**`bytes_expected`** (integer): Host-selected UTF-8 byte count from the worker's immutable header input.
- <a id="contract-lifecycle-policy_read-bytes_received"></a>**`bytes_received`** (integer): Bytes the worker read from the policy pipe when it observed EOF. Equality with bytes_expected establishes length agreement with the submitted bytes.

<a id="contract-lifecycle-disposition"></a>
### Canonical worker disposition

Record `lc_disposition`: `PWDispositionRecord`.

Run questions and per-step questions keep their individual support and conflicts.

- <a id="contract-lifecycle-disposition-questions"></a>**`questions`** ([Run lifecycle questions](#contract-lifecycle-run_questions)): Fixed set of run-level lifecycle claims.
- <a id="contract-lifecycle-disposition-steps"></a>**`steps`** (array of [Step lifecycle account](#contract-lifecycle-step)): Plan-ordered lifecycle claims for each requested step, joined only to uniquely identified worker slots.
- <a id="contract-lifecycle-disposition-issues"></a>**`issues`** (array of [Lifecycle conflict](#contract-lifecycle-issue)): Conflicting observations referenced by conflicting claims; indices are zero-based within this array.

<a id="contract-lifecycle-disposition-resolve"></a>
#### Resolving lifecycle claims

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at final worker output and plan join. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Uses [Resolve the final process status](#contract-lifecycle-worker-final_status), [Copy the polling stop](#contract-lifecycle-worker-resolve_stop_reason), [Copy the final collection basis](#contract-lifecycle-worker-resolve_collection_basis), [Project ordinary canonical step claims](#contract-lifecycle-disposition-ordinary_projection), [Project actor canonical step claims](#contract-lifecycle-disposition-actor_projection). Resolve each question from the owning worker's acquired output, unique slot identities and submitted plan. A not_reached or unpublished conclusion requires terminal collection where specified below. Resolve and publish the canonical account once. Retain competing observations as conflict issues, and derive each per-attempt summary from its canonical claims and attempt applicability.

A completed supported slot establishes publication and
can establish entry. Recognized progress at or after an attempt's entry also
establishes entry. A final earlier progress position establishes `not_reached`
only after confirmed reaping and with an incomplete slot; beside a completed
slot it produces D5. Returned-or-later terminal progress beside an incomplete
supported slot produces D5 for result publication. Live collection leaves
missing results unresolved. An unsupported attempt has inapplicable result
publication and an `unsupported` lifecycle summary.

<a id="contract-lifecycle-disposition-ordinary_projection"></a>
#### Project ordinary canonical step claims

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at per-step canonical lifecycle projection. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Binding `s`: entry in `reply.steps`. Binding `c`: entry in `reply.runner_subprocess.disposition.steps`. Binding `d`: entry in `reply.runner_subprocess.disposition.steps`. Association restriction for `c`: `reply.runner_subprocess.disposition.steps[c].step_id` = `reply.steps[s].step_id`. Association restriction for `d`: (`reply.runner_subprocess.disposition.steps[d].step_id` = `reply.steps[s].step_id` and `d` < `c`). For each `s`, `c`. Applies when (present(`reply.runner_subprocess`) and present(`reply.runner_subprocess.disposition`) and matches(`d`) = `0`).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-lifecycle-disposition-ordinary_projection-presence"></a>Both canonical claims produce the projection | Requires implies((present(`reply.runner_subprocess.disposition.steps[c].questions.step_boundary_reached`) and present(`reply.runner_subprocess.disposition.steps[c].questions.step_result_published`)), present(`reply.steps[s].attempt.lifecycle`)). |
| <a id="contract-lifecycle-disposition-ordinary_projection-copy"></a>Copy the canonical claims | Applies when (present(`reply.runner_subprocess.disposition.steps[c].questions.step_boundary_reached`) and present(`reply.runner_subprocess.disposition.steps[c].questions.step_result_published`)). [set_value(`reply.steps[s].attempt.lifecycle.boundary`, `reply.runner_subprocess.disposition.steps[c].questions.step_boundary_reached`), set_value(`reply.steps[s].attempt.lifecycle.result`, `reply.runner_subprocess.disposition.steps[c].questions.step_result_published`)]. |
| <a id="contract-lifecycle-disposition-ordinary_projection-missing"></a>Missing canonical claim | Applies when not ((present(`reply.runner_subprocess.disposition.steps[c].questions.step_boundary_reached`) and present(`reply.runner_subprocess.disposition.steps[c].questions.step_result_published`))). [withhold(`reply.steps[s].attempt.lifecycle`)]. |

<a id="contract-lifecycle-disposition-ordinary_projection-source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Project ordinary canonical step claims](#contract-lifecycle-disposition-ordinary_projection) and its descendants.** The ordinary and actor builders select the first matching canonical step; attemptLifecycle copies both claims when present and returns nil otherwise. [Evidence details](CONTRACT.md#contract-lifecycle-disposition-ordinary_projection-source-details).

<a id="contract-lifecycle-disposition-actor_projection"></a>
#### Project actor canonical step claims

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at per-step canonical lifecycle projection. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Binding `a`: entry in `reply.actors`. Binding `s`: entry in `reply.steps`. Binding `c`: entry in `reply.actors[a].subprocess.disposition.steps`. Binding `d`: entry in `reply.actors[a].subprocess.disposition.steps`. Association restriction for `c`: `reply.actors[a].subprocess.disposition.steps[c].step_id` = `reply.steps[s].step_id`. Association restriction for `d`: (`reply.actors[a].subprocess.disposition.steps[d].step_id` = `reply.steps[s].step_id` and `d` < `c`). Association restriction for `s`: `reply.steps[s].actor_id` = `reply.actors[a].actor_id`. For each `a`, `s`, `c`. Applies when (present(`reply.actors`) and present(`reply.actors[a].subprocess`) and present(`reply.actors[a].subprocess.disposition`) and matches(`d`) = `0`).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-lifecycle-disposition-actor_projection-presence"></a>Both canonical claims produce the projection | Requires implies((present(`reply.actors[a].subprocess.disposition.steps[c].questions.step_boundary_reached`) and present(`reply.actors[a].subprocess.disposition.steps[c].questions.step_result_published`)), present(`reply.steps[s].attempt.lifecycle`)). |
| <a id="contract-lifecycle-disposition-actor_projection-copy"></a>Copy the canonical claims | Applies when (present(`reply.actors[a].subprocess.disposition.steps[c].questions.step_boundary_reached`) and present(`reply.actors[a].subprocess.disposition.steps[c].questions.step_result_published`)). [set_value(`reply.steps[s].attempt.lifecycle.boundary`, `reply.actors[a].subprocess.disposition.steps[c].questions.step_boundary_reached`), set_value(`reply.steps[s].attempt.lifecycle.result`, `reply.actors[a].subprocess.disposition.steps[c].questions.step_result_published`)]. |
| <a id="contract-lifecycle-disposition-actor_projection-missing"></a>Missing canonical claim | Applies when not ((present(`reply.actors[a].subprocess.disposition.steps[c].questions.step_boundary_reached`) and present(`reply.actors[a].subprocess.disposition.steps[c].questions.step_result_published`))). [withhold(`reply.steps[s].attempt.lifecycle`)]. |

<a id="contract-lifecycle-disposition-actor_projection-source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Project actor canonical step claims](#contract-lifecycle-disposition-actor_projection) and its descendants.** The ordinary and actor builders select the first matching canonical step; attemptLifecycle copies both claims when present and returns nil otherwise. [Evidence details](CONTRACT.md#contract-lifecycle-disposition-actor_projection-source-details).

<a id="contract-lifecycle-claim"></a>
### Lifecycle claim

Record `lc_claim`: `PWDispositionClaim`.

A supported claim names its answer and observation references. An unresolved or inapplicable claim names its reason; a conflicting claim points to its issue.

- <a id="contract-lifecycle-claim-state"></a>**`state`** (string): supported, unresolved, conflicting or inapplicable, determining which accompanying fields carry the claim. Admitted vocabulary: closed; displayed list: exhaustive: `"supported"`, `"unresolved"`, `"conflicting"`, `"inapplicable"`.
- <a id="contract-lifecycle-claim-answer"></a>**`answer`** (string?): Question-specific supported answer, such as signal, exit_code, reached, published or an observed host stop reason.
- <a id="contract-lifecycle-claim-value"></a>**`value`** ([Lifecycle answer value](#contract-lifecycle-claim_value)?): Answer payload: an exit code, signal or item index as an integer, or the observed termination-request object.
- <a id="contract-lifecycle-claim-reason"></a>**`reason`** (string?): Reason the question is unresolved or inapplicable, preserving missing, unusable, nonterminal and unsupported evidence distinctions.
- <a id="contract-lifecycle-claim-issue"></a>**`issue`** (integer?): Zero-based pointer to the matching conflict in disposition.issues.
- <a id="contract-lifecycle-claim-basis"></a>**`basis`** (array of string?): Observation references supporting the answer or explaining uncertainty: raw run fields, progress, worker_failure, plan, slot and attempt_support in their question's scope.

<a id="contract-lifecycle-claim_value"></a>
### Lifecycle answer value

Record `lc_claim_value`: `PWDispositionValue`.

| Alternative | Record |
| --- | --- |
| `Integer` | `Int` |
| `Request` | [Host termination request](#contract-lifecycle-termination) |

<a id="contract-lifecycle-issue"></a>
### Lifecycle conflict

Record `lc_issue`: `PWDispositionIssue`.

- <a id="contract-lifecycle-issue-kind"></a>**`kind`** (string): conflict for a resolver-created disagreement among observations.
- <a id="contract-lifecycle-issue-rule"></a>**`rule`** (string): D1 for competing terminal status representations; D5 for incompatible terminal progress and slot publication.
- <a id="contract-lifecycle-issue-question"></a>**`question`** (string): Lifecycle question affected by this issue.
- <a id="contract-lifecycle-issue-step_index"></a>**`step_index`** (integer?): Zero-based plan step for a step issue; absent for a run-level issue.
- <a id="contract-lifecycle-issue-observations"></a>**`observations`** (array of string): Named observations involved in the conflict, resolved in the same run or step scope.
- <a id="contract-lifecycle-issue-detail"></a>**`detail`** (string): Human-readable description of the incompatible observations.

<a id="contract-lifecycle-run_questions"></a>
### Run lifecycle questions

Record `lc_run_questions`: `PWDispositionRunQuestions`.

Ordinary resolution supplies every question; absent slots preserve partial or rejected evidence for readers.

- <a id="contract-lifecycle-run_questions-final_status"></a>**`final_status`** ([Lifecycle claim](#contract-lifecycle-claim)?): Whether a successful owned reap supplies an exit code or terminating signal; competing representations produce a D1 conflict.
- <a id="contract-lifecycle-run_questions-stop_reason"></a>**`stop_reason`** ([Lifecycle claim](#contract-lifecycle-claim)?): Host polling-stop observation, or unresolved when it was not recorded.
- <a id="contract-lifecycle-run_questions-cleanup_trigger"></a>**`cleanup_trigger`** ([Lifecycle claim](#contract-lifecycle-claim)?): Recorded reason for requesting exit; inapplicable when exit_requested is false.
- <a id="contract-lifecycle-run_questions-grace_end"></a>**`grace_end`** ([Lifecycle claim](#contract-lifecycle-claim)?): Recorded end of the exit-grace stage; inapplicable when exit_requested is false.
- <a id="contract-lifecycle-run_questions-kill_request_and_result"></a>**`kill_request_and_result`** ([Lifecycle claim](#contract-lifecycle-claim)?): The observed termination request, a supported none after a recorded exit request, or the corresponding unresolved/inapplicable state.
- <a id="contract-lifecycle-run_questions-collection_basis"></a>**`collection_basis`** ([Lifecycle claim](#contract-lifecycle-claim)?): Host fact stating whether final reads followed confirmed reaping or execution might continue.
- <a id="contract-lifecycle-run_questions-progress_association"></a>**`progress_association`** ([Lifecycle claim](#contract-lifecycle-claim)?): Association of the packed progress word with no item, a step index or a parameter index; invalid packing is distinguished from an unfamiliar operation/stage.

<a id="contract-lifecycle-step"></a>
### Step lifecycle account

Record `lc_step`: `PWDispositionStep`.

- <a id="contract-lifecycle-step-index"></a>**`index`** (integer): Zero-based position of this step in the owning worker's plan.
- <a id="contract-lifecycle-step-step_id"></a>**`step_id`** (string): Submitted step identifier used to join its worker slot and public step.
- <a id="contract-lifecycle-step-slot"></a>**`slot`** (string): completed, incomplete or absent according to the uniquely associated worker slot and its completion publication. A completed slot is associated through the identifier read back from it, which must equal the submitted step identifier in UTF-8 bytes. Admitted vocabulary: closed; displayed list: exhaustive: `"completed"`, `"incomplete"`, `"absent"`.
- <a id="contract-lifecycle-step-attempt_support"></a>**`attempt_support`** (string): supported or unsupported according to whether the requested attempt has an implemented worker mapping. Admitted vocabulary: closed; displayed list: exhaustive: `"supported"`, `"unsupported"`.
- <a id="contract-lifecycle-step-questions"></a>**`questions`** ([Step lifecycle questions](#contract-lifecycle-step_questions)): Boundary, result-publication and requested-operation applicability claims for this step.

<a id="contract-lifecycle-step_questions"></a>
### Step lifecycle questions

Record `lc_step_questions`: `PWDispositionStepQuestions`.

The result and boundary questions preserve distinct observations: a call can start without publishing a completed result.

- <a id="contract-lifecycle-step_questions-step_boundary_reached"></a>**`step_boundary_reached`** ([Lifecycle claim](#contract-lifecycle-claim)?): Whether recognized progress or a supported completed slot establishes entry; terminal earlier progress can establish not_reached or conflict with a completed slot.
- <a id="contract-lifecycle-step_questions-step_result_published"></a>**`step_result_published`** ([Lifecycle claim](#contract-lifecycle-claim)?): Whether a supported completed slot is published; incomplete terminal collection can establish unpublished, while live collection remains unresolved.
- <a id="contract-lifecycle-step_questions-step_requested_operation_applicability"></a>**`step_requested_operation_applicability`** ([Lifecycle claim](#contract-lifecycle-claim)?): Whether this requested attempt maps to an implemented worker operation, as stated by attempt_support.

<a id="contract-lifecycle-attempt"></a>
### Per-attempt lifecycle projection

Record `lc_attempt`: `PWAttemptLifecycle`.

A step or extension event carries this compact projection of its canonical disposition claims.

- <a id="contract-lifecycle-attempt-summary"></a>**`summary`** (string): The current producer derives completed, started_without_result, not_reached, unsupported, unresolved or conflicting from the boundary/result claims and attempt support. The controller retains unfamiliar summary strings; it checks the recognized summaries against their corresponding claims. Admitted vocabulary: open; displayed list: illustrative: `"completed"`, `"started_without_result"`, `"not_reached"`, `"unsupported"`, `"unresolved"`, `"conflicting"`. Unfamiliar values: The controller retains an unfamiliar summary and checks the independently carried boundary and result claims.
- <a id="contract-lifecycle-attempt-boundary"></a>**`boundary`** ([Lifecycle claim](#contract-lifecycle-claim)): Copy of the owning disposition step's step_boundary_reached claim.
- <a id="contract-lifecycle-attempt-result"></a>**`result`** ([Lifecycle claim](#contract-lifecycle-claim)): Copy of the owning disposition step's step_result_published claim.

<a id="contract-lifecycle-owned_reap"></a>
### Owned child ending

Record `lc_owned_reap`: `PWOwnedReapObservation`.

- <a id="contract-lifecycle-owned_reap-pid"></a>**`pid`** (integer): Owned child PID for which the host obtained terminal wait status.
- <a id="contract-lifecycle-owned_reap-native_rc"></a>**`native_rc`** (integer): Native waitpid return equal to pid for this captured ending.
- <a id="contract-lifecycle-owned_reap-raw_status"></a>**`raw_status`** (integer): Raw terminal wait status, from which the corresponding exit code or signal is decoded.
- <a id="contract-lifecycle-owned_reap-stage"></a>**`stage`** (string): Host capture stage, including schedule, termination_gate and cleanup stages; the gate admits schedule or termination_gate for natural-departure support.
- <a id="contract-lifecycle-owned_reap-observed_ns"></a>**`observed_ns`** (integer?): Host monotonic capture time in nanoseconds, when available.
- <a id="contract-lifecycle-owned_reap-ownership_unbroken"></a>**`ownership_unbroken`** (boolean): Whether the host retained uninterrupted ownership through this wait observation.
- <a id="contract-lifecycle-owned_reap-departure_requested"></a>**`departure_requested`** (boolean): Whether the host had already requested this child's departure when it captured the ending.
- <a id="contract-lifecycle-owned_reap-capture_ordinal"></a>**`capture_ordinal`** (integer): Positive ordinal in this child's host-observation sequence, shared with its activations and gate captures.

<a id="contract-lifecycle-reap_reference"></a>
### Owned-ending reference

Record `lc_reap_reference`: `PWOwnedReapReference`.

- <a id="contract-lifecycle-reap_reference-capture_ordinal"></a>**`capture_ordinal`** (integer): Ordinal of the source actor's owned ending; its association must match that source's owned_reap record.

<a id="contract-lifecycle-spawn_failure"></a>
### Native spawn failure

Record `lc_spawn_failure`: `PWRunnerSpawnFailure`.

The host retains the failed spawn operation as a separate record before a child process exists.

- <a id="contract-lifecycle-spawn_failure-origin"></a>**`origin`** (string): Component reporting the failure, supplied by the runner host.
- <a id="contract-lifecycle-spawn_failure-operation"></a>**`operation`** (string): Failed native spawn operation, such as posix_spawn.
- <a id="contract-lifecycle-spawn_failure-executable_path"></a>**`executable_path`** (string): Executable path passed to the attempted spawn.
- <a id="contract-lifecycle-spawn_failure-return_code"></a>**`return_code`** (integer): Native spawn return code, whose error-code convention is distinct from a child exit status.
- <a id="contract-lifecycle-spawn_failure-diagnostic"></a>**`diagnostic`** (string): Human-readable native error explanation of the spawn failure.

<a id="contract-lifecycle-validator"></a>
### Validator subprocess

Record `lc_validator`: `PWRunnerValidatorSubprocess`.

The host binds each validator collection to its phase and retains accepted records through later I/O, association or cleanup failure.

For N submitted queries, the collector assigns a record allowance of max(1, N) multiplied by <!-- span limits.validator_records_per_query.value -->2<!-- /span --> and a stdout retention allowance of max(1, N) multiplied by <!-- span limits.validator_reply_bytes_per_query.value_unit -->16,384 bytes<!-- /span -->. The allowances are sized before writing the query batch. On byte overflow the host counts all bytes received, keeps the bounded prefix through its last complete LF frame, closes collection and reports byte_limit. Decoding retains complete accepted records before the first refused frame or record-count excess.

- <a id="contract-lifecycle-validator-phase_id"></a>**`phase_id`** (string?): Host-stamped phase identifier served by this collection; agrees with the containing phase.
- <a id="contract-lifecycle-validator-ordinal"></a>**`ordinal`** (integer?): Host-stamped one-based phase ordinal for this collection.
- <a id="contract-lifecycle-validator-pid"></a>**`pid`** (integer): Spawned validator PID used for collection and owned cleanup.
- <a id="contract-lifecycle-validator-term_signal"></a>**`term_signal`** (integer?): Signal decoded only from a successful waitpid result for this validator.
- <a id="contract-lifecycle-validator-exit_code"></a>**`exit_code`** (integer?): Exit status decoded only from a successful waitpid result for this validator.
- <a id="contract-lifecycle-validator-reaped"></a>**`reaped`** (boolean?): True for a confirmed owned reap, false for an unconfirmed ending, absent when unreported.
- <a id="contract-lifecycle-validator-termination_request"></a>**`termination_request`** ([Host termination request](#contract-lifecycle-termination)?): Host kill request and native return, if requested during validator cleanup.
- <a id="contract-lifecycle-validator-wait_errors"></a>**`wait_errors`** (array of [Failed host wait](#contract-lifecycle-wait_error)?): Failed waitpid observations from validator cleanup, including recovered interruptions.
- <a id="contract-lifecycle-validator-read_error"></a>**`read_error`** (string?): Host diagnostic for stdout-read failure, separate from accepted record contents.
- <a id="contract-lifecycle-validator-stdout_collection_stop"></a>**`stdout_collection_stop`** (string?): Host reason for stopping stdout collection: eof, clock_error, deadline, poll_error, byte_limit or read_error. This is fixed before the exit-grace stage.
- <a id="contract-lifecycle-validator-stdout_bytes_received"></a>**`stdout_bytes_received`** (integer?): Total stdout bytes received by the host, including bytes later rejected by frame decoding.
- <a id="contract-lifecycle-validator-probe_bytes_written"></a>**`probe_bytes_written`** (integer?): Request bytes accepted by host writes to the validator input pipe.
- <a id="contract-lifecycle-validator-probe_bytes_expected"></a>**`probe_bytes_expected`** (integer?): Serialized request-batch byte count the host intended to write.
- <a id="contract-lifecycle-validator-io_error"></a>**`io_error`** (string?): Host transport diagnostic for the first request-write or stdout-read failure selected for this collection.
- <a id="contract-lifecycle-validator-decode_fault"></a>**`decode_fault`** ([Rejected validator frame](#contract-lifecycle-decode_fault)?): First rejected stdout frame's receiver-owned diagnostic and bounded byte prefix.
- <a id="contract-lifecycle-validator-records"></a>**`records`** (array of [Accepted validator record](#contract-steps-verdict)?): Accepted verdict records in received order, including diagnostic, unexpected-ID and null-ID records, within this phase collector's record allowance.
- <a id="contract-lifecycle-validator-expected_step_ids"></a>**`expected_step_ids`** (array of string?): Submitted query IDs in the planned collection; used to check missing, duplicate and unexpected associations.
- <a id="contract-lifecycle-validator-association_issues"></a>**`association_issues`** (array of [Validator query association](#contract-lifecycle-association_issue)?): Host-computed join problems; an empty array records a complete unambiguous join for the expected queries.
- <a id="contract-lifecycle-validator-exit_grace_wait"></a>**`exit_grace_wait`** ([Measured host wait](#contract-lifecycle-host_wait)?): Measured monotonic host wait after collection closed, with production allowance <!-- span limits.validator_exit_grace.value_unit -->1,000 milliseconds<!-- /span -->, before any further termination/reap work. Those later operations can continue beyond this allowance.

<a id="contract-lifecycle-validator-associate"></a>
#### Joining accepted validator records

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at closed phase query collection. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. retain_records(`lc_validator.records`). Uses [Count expected and unexpected associations](#contract-lifecycle-validator-cardinality). A unique expected-ID record enters the per-step join only when every supplied query metadata value agrees with the submitted query. Allow/deny records must supply the complete submitted query identity. Identifier and query-metadata equality in this join is equality of UTF-8 bytes; canonically equivalent spellings with different bytes do not match. Publish association issues in expected-query order, then unexpected IDs in UTF-8 byte order, then a null-ID issue when present. Withhold each failed per-step join while retaining accepted records.

Duplicate IDs leave every record of that group at collection scope. Null IDs
remain unassociated. Diagnostic outcomes may omit query metadata; any supplied
metadata must agree.

<a id="contract-lifecycle-validator-cardinality"></a>
#### Count expected and unexpected associations

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at closed validator collection association. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Applies when (present(`lc_validator.records`) and present(`lc_validator.expected_step_ids`) and present(`lc_validator.association_issues`)).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-lifecycle-validator-cardinality-expected"></a>Expected identifier groups | Binding `e`: entry in `lc_validator.expected_step_ids`. Binding `f`: entry in `lc_validator.expected_step_ids`. Binding `v`: entry in `lc_validator.records`. Binding `i`: entry in `lc_validator.association_issues`. Association restriction for `f`: `lc_validator.expected_step_ids[f]` = `lc_validator.expected_step_ids[e]`. Association restriction for `v`: `lc_validator.records[v].step_id` = `lc_validator.expected_step_ids[e]`. Association restriction for `i`: `lc_validator.association_issues[i].step_id` = `lc_validator.expected_step_ids[e]`. For each `e`. Requires implies(matches(`v`) ≠ `1`, matches(`i`) = matches(`f`)). |
| <a id="contract-lifecycle-validator-cardinality-expected-missing"></a>Expected identifier groups › Missing group | For each `e`, `i`. Requires implies(matches(`v`) = `0`, (`lc_validator.association_issues[i].kind` = `"missing_id"` and `lc_validator.association_issues[i].count` = `0`)). |
| <a id="contract-lifecycle-validator-cardinality-expected-duplicate"></a>Expected identifier groups › Duplicate group | For each `e`, `i`. Requires implies(matches(`v`) > `1`, (`lc_validator.association_issues[i].kind` = `"duplicate_id"` and `lc_validator.association_issues[i].count` = matches(`v`))). |
| <a id="contract-lifecycle-validator-cardinality-unexpected"></a>Unexpected identifier groups | Binding `v`: entry in `lc_validator.records`. Binding `e`: entry in `lc_validator.expected_step_ids`. Binding `g`: entry in `lc_validator.records`. Binding `i`: entry in `lc_validator.association_issues`. Association restriction for `e`: `lc_validator.expected_step_ids[e]` = `lc_validator.records[v].step_id`. Association restriction for `g`: `lc_validator.records[g].step_id` = `lc_validator.records[v].step_id`. Association restriction for `i`: `lc_validator.association_issues[i].step_id` = `lc_validator.records[v].step_id`. For each `v`. Requires implies((present(`lc_validator.records[v].step_id`) and matches(`e`) = `0`), matches(`i`) = `1`). |
| <a id="contract-lifecycle-validator-cardinality-unexpected-count"></a>Unexpected identifier groups › Unexpected group count | For each `v`, `i`. Requires implies((present(`lc_validator.records[v].step_id`) and matches(`e`) = `0`), (`lc_validator.association_issues[i].kind` = `"unexpected_id"` and `lc_validator.association_issues[i].count` = matches(`g`))). |
| <a id="contract-lifecycle-validator-cardinality-unassociated"></a>Unassociated records | Binding `v`: entry in `lc_validator.records`. Binding `i`: entry in `lc_validator.association_issues`. Association restriction for `v`: absent(`lc_validator.records[v].step_id`). Association restriction for `i`: (absent(`lc_validator.association_issues[i].step_id`) and `lc_validator.association_issues[i].kind` = `"unassociated"`). Requires (implies(matches(`v`) > `0`, matches(`i`) = `1`) and implies(matches(`v`) = `0`, matches(`i`) = `0`)). |
| <a id="contract-lifecycle-validator-cardinality-unassociated-count"></a>Unassociated records › Unassociated count | For each `i`. Requires `lc_validator.association_issues[i].count` = matches(`v`). |

<a id="contract-lifecycle-validator-cardinality-source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Count expected and unexpected associations](#contract-lifecycle-validator-cardinality) and its descendants.** Groups are formed from every accepted non-null ID before metadata comparison; missing/duplicate/unexpected/null-ID groups preserve their actual counts. [Evidence details](CONTRACT.md#contract-lifecycle-validator-cardinality-source-details).

<a id="contract-lifecycle-decode_fault"></a>
### Rejected validator frame

Record `lc_decode_fault`: `PWValidatorDecodeFault`.

- <a id="contract-lifecycle-decode_fault-origin"></a>**`origin`** (string): runner_host, identifying the rejecting receiver.
- <a id="contract-lifecycle-decode_fault-kind"></a>**`kind`** (string): Receiver category utf8, json or structure for the first rejected frame. Admitted vocabulary: closed; displayed list: exhaustive: `"utf8"`, `"json"`, `"structure"`.
- <a id="contract-lifecycle-decode_fault-message"></a>**`message`** (string): Human-readable reason the frame failed structural admission.
- <a id="contract-lifecycle-decode_fault-byte_offset"></a>**`byte_offset`** (integer): Zero-based offset of the rejected frame's first byte in received stdout.
- <a id="contract-lifecycle-decode_fault-frame_bytes"></a>**`frame_bytes`** (integer): Length of that frame in bytes, excluding its LF separator.
- <a id="contract-lifecycle-decode_fault-retained_bytes"></a>**`retained_bytes`** (integer): Number of prefix bytes retained, capped at 256.
- <a id="contract-lifecycle-decode_fault-context_b64"></a>**`context_b64`** (string (base64)): Base64 encoding of the retained received-byte prefix. Decoding yields those exact bytes.
- <a id="contract-lifecycle-decode_fault-context_truncated"></a>**`context_truncated`** (boolean): True when frame_bytes exceeds retained_bytes.

<a id="contract-lifecycle-association_issue"></a>
### Validator query association

Record `lc_association_issue`: `PWValidatorAssociationIssue`.

- <a id="contract-lifecycle-association_issue-origin"></a>**`origin`** (string): runner_host, identifying the component computing the association issue.
- <a id="contract-lifecycle-association_issue-kind"></a>**`kind`** (string): missing_id, duplicate_id, query_mismatch, unexpected_id or unassociated. Admitted vocabulary: closed; displayed list: exhaustive: `"missing_id"`, `"duplicate_id"`, `"query_mismatch"`, `"unexpected_id"`, `"unassociated"`.
- <a id="contract-lifecycle-association_issue-step_id"></a>**`step_id`** (string?): Expected or unexpected ID concerned by the issue; absent for records whose verdict ID is null.
- <a id="contract-lifecycle-association_issue-count"></a>**`count`** (integer): Number of accepted records involved: zero for missing_id, one for query_mismatch, the group size for duplicate/unexpected IDs, or total null-ID records for unassociated.

<a id="contract-lifecycle-exec"></a>
### Spawned-command observation

Record `lc_exec`: `PWExecObservation`.

A completed worker exec slot separates collection, cleanup requests and the owned leader reap. Collection facts are frozen before termination requests.

- <a id="contract-lifecycle-exec-collection"></a>**`collection`** ([Exec collection](#contract-lifecycle-exec_collection)): Leader-exit and pipe observations up to the collection stop.
- <a id="contract-lifecycle-exec-cleanup"></a>**`cleanup`** ([Exec cleanup](#contract-lifecycle-exec_cleanup)): Requests to terminate the spawned process group and any leader fallback.
- <a id="contract-lifecycle-exec-reap"></a>**`reap`** ([Exec leader reap](#contract-lifecycle-exec_reap)): Final bounded wait account for the owned leader after collection and cleanup.

<a id="contract-lifecycle-exec_collection"></a>
### Exec collection

Record `lc_exec_collection`: `PWExecCollectionObservation`.

The collector can observe leader exit and pipe EOF independently; descendants may keep a stream open after the leader exits.

- <a id="contract-lifecycle-exec_collection-stop_reason"></a>**`stop_reason`** (string): leader_exit_and_eof, deadline, observation_error or clock_fault, recording the branch that stopped collection. Admitted vocabulary: closed; displayed list: exhaustive: `"leader_exit_and_eof"`, `"deadline"`, `"observation_error"`, `"clock_fault"`.
- <a id="contract-lifecycle-exec_collection-leader_exit_observed"></a>**`leader_exit_observed`** (boolean): Whether waitid observed the owned leader's exit during collection.
- <a id="contract-lifecycle-exec_collection-stdout"></a>**`stdout`** ([Exec stream observation](#contract-lifecycle-exec_stream)): EOF or native read/poll failure retained for stdout.
- <a id="contract-lifecycle-exec_collection-stderr"></a>**`stderr`** ([Exec stream observation](#contract-lifecycle-exec_stream)): EOF or native read/poll failure retained for stderr.
- <a id="contract-lifecycle-exec_collection-deadline_kind"></a>**`deadline_kind`** (string?): child or plan when the selected collection deadline expires; absent on other stop branches. The child allowance and remaining per-worker active-plan allowance are defined by the exec operation. Uses [Exec setup and child inputs](REQUEST.md#contract-probes-attempt-exec). Admitted vocabulary: closed; displayed list: exhaustive: `"child"`, `"plan"`.
- <a id="contract-lifecycle-exec_collection-waitid_errno"></a>**`waitid_errno`** (integer?): Native waitid failure which stopped leader observation; recovered EINTR is excluded.
- <a id="contract-lifecycle-exec_collection-poll_errno"></a>**`poll_errno`** (integer?): Native poll failure which stopped stream observation; recovered EINTR is excluded.
- <a id="contract-lifecycle-exec_collection-clock_fault"></a>**`clock_fault`** (integer?): Local numeric clock-fault observation when collection stopped for failed/backward time.

<a id="contract-lifecycle-exec_stream"></a>
### Exec stream observation

Record `lc_exec_stream`: `PWExecStreamObservation`.

- <a id="contract-lifecycle-exec_stream-eof"></a>**`eof`** (boolean): Whether the worker read EOF on this stream before collection stopped.
- <a id="contract-lifecycle-exec_stream-read_errno"></a>**`read_errno`** (integer?): Terminal read errno, excluding recovered EINTR and EAGAIN.
- <a id="contract-lifecycle-exec_stream-poll_revents"></a>**`poll_revents`** (integer?): Terminal error/invalid descriptor poll bits retained when they ended observation; ordinary readable/EOF handling uses its own read observation.

<a id="contract-lifecycle-exec_cleanup"></a>
### Exec cleanup

Record `lc_exec_cleanup`: `PWExecCleanupObservation`.

- <a id="contract-lifecycle-exec_cleanup-state"></a>**`state`** (string): not_requested after leader_exit_and_eof; ownership_unconfirmed when waitid failed; requested when an eligible process-group cleanup was attempted. Admitted vocabulary: closed; displayed list: exhaustive: `"not_requested"`, `"ownership_unconfirmed"`, `"requested"`.
- <a id="contract-lifecycle-exec_cleanup-group_request"></a>**`group_request`** ([Exec signal request](#contract-lifecycle-exec_signal)?): SIGKILL request to negative leader PID for the owned process group, when cleanup is requested.
- <a id="contract-lifecycle-exec_cleanup-leader_fallback"></a>**`leader_fallback`** ([Exec signal request](#contract-lifecycle-exec_signal)?): SIGKILL request to the positive leader PID after a failed group request with errno other than ESRCH.

<a id="contract-lifecycle-exec_signal"></a>
### Exec signal request

Record `lc_exec_signal`: `PWExecSignalRequest`.

This is the worker's native kill call for a spawned command, scoped to the target named here.

- <a id="contract-lifecycle-exec_signal-target"></a>**`target`** (integer): Negative leader PID for a process-group request, or positive leader PID for the fallback request.
- <a id="contract-lifecycle-exec_signal-signal"></a>**`signal`** (integer): Signal passed to kill; the exec cleanup path uses SIGKILL.
- <a id="contract-lifecycle-exec_signal-rc"></a>**`rc`** (integer): Native kill return, zero or -1.
- <a id="contract-lifecycle-exec_signal-errno"></a>**`errno`** (integer?): Positive native errno captured for rc -1; absent after success.

<a id="contract-lifecycle-exec_reap"></a>
### Exec leader reap

Record `lc_exec_reap`: `PWExecReapObservation`.

Final wait facts concern the spawned leader owned by the worker. After collection ends, the production reap allowance is <!-- span limits.exec_reap_grace.value_unit -->1,000 milliseconds<!-- /span --> of continuous time. Earlier ownership or group-request failures retain their branch priority; a recorded request and an observed reap remain separate.

- <a id="contract-lifecycle-exec_reap-stop_reason"></a>**`stop_reason`** (string): reaped, wait_error, ownership_unconfirmed, group_request_failed, clock_fault or deadline; branch priority preserves earlier ownership/group-request failures. Admitted vocabulary: closed; displayed list: exhaustive: `"reaped"`, `"wait_error"`, `"ownership_unconfirmed"`, `"group_request_failed"`, `"clock_fault"`, `"deadline"`.
- <a id="contract-lifecycle-exec_reap-last_wait"></a>**`last_wait`** ([Exec leader wait result](#contract-lifecycle-exec_wait)): Last native waitpid result, with status only when the owned leader PID returned.
- <a id="contract-lifecycle-exec_reap-clock_fault"></a>**`clock_fault`** (integer?): Local numeric clock fault encountered by the reap wait, when observed.

<a id="contract-lifecycle-exec_wait"></a>
### Exec leader wait result

Record `lc_exec_wait`: `PWExecWaitObservation`.

- <a id="contract-lifecycle-exec_wait-rc"></a>**`rc`** (integer): Native waitpid return: zero pending, -1 failure, or owned leader PID when reaped.
- <a id="contract-lifecycle-exec_wait-errno"></a>**`errno`** (integer?): Positive captured errno for rc -1, including EINTR; absent otherwise.
- <a id="contract-lifecycle-exec_wait-status"></a>**`status`** (integer?): Raw terminal wait status present exactly when rc is the owned leader PID, agreeing with the attempt's leader exit/signal fields.
<!-- END GENERATED CONTRACT lifecycle -->

## Read equipment and authority setup

Binding a worker file, inspecting its signature and inspecting a launched process establish different observations. Equipment labels and entitlement readbacks do not by themselves establish effective authority under the applied policy.

<!-- BEGIN GENERATED CONTRACT equipment -->
<a id="contract-equipment"></a>
## Equipment and authority setup

<a id="contract-equipment-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Equipment and authority setup](#contract-equipment) and its descendants.** Imported public field definitions joined to producer/decoder/assessment meanings; explicit rule and evidence gaps preserve scope. [Evidence details](CONTRACT.md#contract-equipment-support-details).

<a id="contract-equipment-inventory"></a>
### Observed service inventory

Record `eq_inventory`: `PWRunnerEquipmentInventory`.

The host inspects the selected service seal and reads its bounded worker-equipment.json before launching any actor.

- <a id="contract-equipment-inventory-path"></a>**`path`** (string): Absolute path of the service-local worker-equipment.json selected for inspection.
- <a id="contract-equipment-inventory-status"></a>**`status`** (string): verified after seal, inventory decoding and expected-identity checks; refused after a retained failure; unobserved before inspection. Admitted vocabulary: closed; displayed list: exhaustive: `"verified"`, `"refused"`, `"unobserved"`.
- <a id="contract-equipment-inventory-sha256"></a>**`sha256`** (string (hex)?): SHA-256 of inventory bytes actually read, when available. Uses [SHA-256 hexadecimal width](CONTRACT.md#contract-identity-other-sha256_hex).
- <a id="contract-equipment-inventory-schema_version"></a>**`schema_version`** (integer?): Decoded inventory schema; verified inventory has version 1.
- <a id="contract-equipment-inventory-worker_identity"></a>**`worker_identity`** (string (hex)?): Decoded worker protocol identity, required to equal the host's selected worker identity for verification. Uses [SHA-256 hexadecimal width](CONTRACT.md#contract-identity-other-sha256_hex).
- <a id="contract-equipment-inventory-unsigned_worker_sha256"></a>**`unsigned_worker_sha256`** (string (hex)?): Decoded digest identifying the shared unsigned worker input named by the inventory. Uses [SHA-256 hexadecimal width](CONTRACT.md#contract-identity-other-sha256_hex).
- <a id="contract-equipment-inventory-seal_osstatus"></a>**`seal_osstatus`** (integer?): Native service-signature validity result, when supplied by static inspection; verified inventory requires zero.
- <a id="contract-equipment-inventory-reason"></a>**`reason`** (string?): Refusal classification describing the failed inventory/seal boundary; absent for verified inventory.
- <a id="contract-equipment-inventory-error"></a>**`error`** ([Equipment diagnostic](#contract-equipment-error)?): Structured native or decoding diagnostic retained at the failed boundary.

<a id="contract-equipment-manifest"></a>
### Sealed equipment inventory file

Record `eq_manifest`: `ActorEquipmentManifest`.

The package places this JSON inventory inside each service seal after signing both worker roles. Its hashes use lowercase hexadecimal text.

- <a id="contract-equipment-manifest-schema_version"></a>**`schema_version`** (integer; as defined below): Inventory format version; the host accepts 1.
- <a id="contract-equipment-manifest-contract"></a>**`contract`** (string; as defined below): Exact public build identity which must match the host's expected contract.
- <a id="contract-equipment-manifest-worker_identity"></a>**`worker_identity`** (string; as defined below): Lowercase hexadecimal worker protocol identity expected by the host. Uses [SHA-256 hexadecimal width](CONTRACT.md#contract-identity-other-sha256_hex).
- <a id="contract-equipment-manifest-unsigned_worker_sha256"></a>**`unsigned_worker_sha256`** (string; as defined below): Lowercase hexadecimal common unsigned worker input digest. Uses [SHA-256 hexadecimal width](CONTRACT.md#contract-identity-other-sha256_hex).
- <a id="contract-equipment-manifest-workers"></a>**`workers`** (array of [Inventory worker row](#contract-equipment-manifest_worker); as defined below): Exactly two distinct role rows, selected and unentitled, providing expected signed file and entitlement identities.

<a id="contract-equipment-manifest_worker"></a>
### Inventory worker row

Record `eq_manifest_worker`: `ActorEquipmentManifest.Worker`.

Each row states the signed identity expected at a fixed service-relative worker path.

- <a id="contract-equipment-manifest_worker-role"></a>**`role`** (string; as defined below): selected or unentitled, identifying the worker role. Admitted vocabulary: closed; displayed list: exhaustive: `"selected"`, `"unentitled"`.
- <a id="contract-equipment-manifest_worker-relative_path"></a>**`relative_path`** (string; as defined below): Contents/MacOS/pw-probe-runner for selected; Contents/MacOS/pw-probe-runner-unentitled for unentitled.
- <a id="contract-equipment-manifest_worker-sha256"></a>**`sha256`** (string; as defined below): Lowercase hexadecimal SHA-256 of the signed worker file. Uses [SHA-256 hexadecimal width](CONTRACT.md#contract-identity-other-sha256_hex).
- <a id="contract-equipment-manifest_worker-cdhash"></a>**`cdhash`** (string; as defined below): Lowercase hexadecimal worker CodeDirectory hash. Uses [CodeDirectory hexadecimal width](CONTRACT.md#contract-identity-other-cdhash_hex).
- <a id="contract-equipment-manifest_worker-identifier"></a>**`identifier`** (string; as defined below): Nonempty signing identifier expected from static code inspection, bounded to <!-- span limits.equipment_signing_text.value_unit -->255 UTF-8 bytes<!-- /span -->.
- <a id="contract-equipment-manifest_worker-team_id"></a>**`team_id`** (string; required; may be null): Required key whose value is the expected signing team or null; a string is nonempty and at most <!-- span limits.equipment_signing_text.value_unit -->255 UTF-8 bytes<!-- /span -->.
- <a id="contract-equipment-manifest_worker-entitlements_xml"></a>**`entitlements_xml`** (string; as defined below): Entitlement dictionary serialized as an XML property list, at most <!-- span limits.equipment_entitlement_bytes.value_unit -->65,536 UTF-8 bytes<!-- /span -->; unentitled has an empty dictionary.

<a id="contract-equipment-binding"></a>
### Static worker binding

Record `eq_binding`: `PWRunnerEquipmentBinding`.

The host emits one row per inspected role and source. Binding establishes the chosen file’s observed identity and entitlement read-back; actors select rows by zero-based index.

- <a id="contract-equipment-binding-role"></a>**`role`** (string): selected or unentitled, the equipment role inspected. Admitted vocabulary: closed; displayed list: exhaustive: `"selected"`, `"unentitled"`.
- <a id="contract-equipment-binding-source"></a>**`source`** (string): packaged for service inventory equipment; test_override for an explicitly selected fixture path. Admitted vocabulary: closed; displayed list: exhaustive: `"packaged"`, `"test_override"`.
- <a id="contract-equipment-binding-implementation_identity"></a>**`implementation_identity`** (string): inventory_verified for packaged rows or unverified_fixture for test overrides, identifying the source of expected implementation identity. Admitted vocabulary: closed; displayed list: exhaustive: `"inventory_verified"`, `"unverified_fixture"`.
- <a id="contract-equipment-binding-relative_path"></a>**`relative_path`** (string?): Fixed service-relative path for packaged equipment; absent for an override path.
- <a id="contract-equipment-binding-path"></a>**`path`** (string): Absolute resolved worker path inspected for launch, bounded to <!-- span limits.equipment_path.value_unit -->1,023 UTF-8 bytes<!-- /span -->.
- <a id="contract-equipment-binding-status"></a>**`status`** (string): bound when path, executable, hash/signature and applicable expected-identity checks pass; refused when a boundary fails. Admitted vocabulary: closed; displayed list: exhaustive: `"bound"`, `"refused"`.
- <a id="contract-equipment-binding-reason"></a>**`reason`** (string?): Refusal reason: missing, not_regular, not_executable, outside_bundle, signature_invalid, signature_unreadable, entitlements_unreadable, worker_identity_mismatch or inspection_failed. Admitted vocabulary: closed; displayed list: exhaustive: `"missing"`, `"not_regular"`, `"not_executable"`, `"outside_bundle"`, `"signature_invalid"`, `"signature_unreadable"`, `"entitlements_unreadable"`, `"worker_identity_mismatch"`, `"inspection_failed"`.
- <a id="contract-equipment-binding-expected_sha256"></a>**`expected_sha256`** (string (hex)?): Signed-file SHA-256 digest from the packaged inventory; absent for test overrides. Uses [SHA-256 hexadecimal width](CONTRACT.md#contract-identity-other-sha256_hex).
- <a id="contract-equipment-binding-expected_cdhash"></a>**`expected_cdhash`** (string (hex)?): CodeDirectory hash from the packaged inventory; absent for test overrides. Uses [CodeDirectory hexadecimal width](CONTRACT.md#contract-identity-other-cdhash_hex).
- <a id="contract-equipment-binding-sha256"></a>**`sha256`** (string (hex)?): SHA-256 of the inspected file's actual bytes, when hashing completed. Uses [SHA-256 hexadecimal width](CONTRACT.md#contract-identity-other-sha256_hex).
- <a id="contract-equipment-binding-cdhash"></a>**`cdhash`** (string (hex)?): CodeDirectory hash read from the inspected static signature, when available. Uses [CodeDirectory hexadecimal width](CONTRACT.md#contract-identity-other-cdhash_hex).
- <a id="contract-equipment-binding-identifier"></a>**`identifier`** (string?): Signing identifier read from static inspection, when available.
- <a id="contract-equipment-binding-team_id"></a>**`team_id`** (string; present when identifier has a value; may be null): Signing team read from static inspection, or null when the signature has none or read-back is unavailable.
- <a id="contract-equipment-binding-entitlements_ref"></a>**`entitlements_ref`** (integer?): Zero-based index of this binding's observed or failed entitlement read-back in equipment_entitlements.
- <a id="contract-equipment-binding-signature_osstatus"></a>**`signature_osstatus`** (integer?): Native static-signature validity result; a bound row requires zero.
- <a id="contract-equipment-binding-entitlements_match"></a>**`entitlements_match`** (boolean?): Whether packaged inventory entitlements equal the observed dictionary; absent for an override or when that comparison was unavailable.
- <a id="contract-equipment-binding-error"></a>**`error`** ([Equipment diagnostic](#contract-equipment-error)?): Structured native or decoding error at the failed inspection boundary, when available.

<a id="contract-equipment-binding-bind"></a>
#### Binding before launch

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at actor preparation before spawn. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Applies when present(`request.actors`). Inspect the service seal, bounded inventory and both packaged worker roles; compare signed hashes, signing identity/team and entitlement dictionaries with the inventory. Resolve every actor's role and Boolean-true entitlement requirements. A preparation failure withholds every actor launch and records equipment_binding_refused with retained inspection evidence. Successful preparation selects the requested role/source path for each actor.

Both packaged roles are checked even if the specimen uses only one. Explicit
fixture overrides are inspected as additional `test_override` rows; their
`unverified_fixture` identity states their provenance. A bound override can
be selected, live-matched and executed. Failed packaged observations remain
preparation failures. A failed role never selects another role automatically.

<a id="contract-equipment-binding-binding_evidence"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Static worker binding](#contract-equipment-binding) and its descendants.** Missing unused packaged role withholds executable paths; Boolean true alone satisfies a key; live mismatch is ineligible; per-row retained observations survive failure. Context: Temporary equipment fixture with constructed inspection calls; source and assertions read. Evidence limit: Execution credit is absent; fixture inspection results support branch/retention behavior. [Evidence details](CONTRACT.md#contract-equipment-binding-binding_evidence-details).

<a id="contract-equipment-binding-bound_values"></a>
#### Packaged bound-row equalities

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at successful packaged static binding projection. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Applies when (`eq_binding.source` = `"packaged"` and `eq_binding.status` = `"bound"`).

Packaged binding includes the retained digest and entitlement equalities. Test-override bindings have no packaged baseline requirement.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-equipment-binding-bound_values-fields"></a>Produced field relationships | Requires (present(`eq_binding.sha256`) and present(`eq_binding.expected_sha256`) and `eq_binding.sha256` = `eq_binding.expected_sha256` and present(`eq_binding.cdhash`) and present(`eq_binding.expected_cdhash`) and `eq_binding.cdhash` = `eq_binding.expected_cdhash` and `eq_binding.entitlements_match` = `true`). |

<a id="contract-equipment-binding-bound_values-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Packaged bound-row equalities](#contract-equipment-binding-bound_values) and its descendants.** Packaged binding compares retained expected and observed digests and decoded entitlement equality before marking a row bound. [Evidence details](CONTRACT.md#contract-equipment-binding-bound_values-support-details).

<a id="contract-equipment-entitlements"></a>
### Entitlement read-back

Record `eq_entitlements`: `PWRunnerEquipmentEntitlements`.

Each table row belongs either to one static binding or to one running actor inspected against that binding.

- <a id="contract-equipment-entitlements-source"></a>**`source`** (string): binding for static signed-file read-back; execution for live actor read-back. Admitted vocabulary: closed; displayed list: exhaustive: `"binding"`, `"execution"`.
- <a id="contract-equipment-entitlements-binding_ref"></a>**`binding_ref`** (integer): Zero-based index of the equipment binding this read-back describes.
- <a id="contract-equipment-entitlements-actor_id"></a>**`actor_id`** (string?): Actor identifier for execution read-back; absent for binding read-back.
- <a id="contract-equipment-entitlements-status"></a>**`status`** (string): observed when raw_plist contains a valid bounded dictionary; failed when an error record describes unavailable read-back. Admitted vocabulary: closed; displayed list: exhaustive: `"observed"`, `"failed"`.
- <a id="contract-equipment-entitlements-raw_plist"></a>**`raw_plist`** (string?): Actual entitlement dictionary serialized as an XML property list, at most <!-- span limits.equipment_entitlement_bytes.value_unit -->65,536 UTF-8 bytes<!-- /span -->; absent for failed read-back.
- <a id="contract-equipment-entitlements-error"></a>**`error`** ([Equipment diagnostic](#contract-equipment-error)?): Read-back failure diagnostic, required for failed status and absent for observed status.

<a id="contract-equipment-error"></a>
### Equipment diagnostic

Record `eq_error`: `PWRunnerEquipmentError`.

Error metadata belongs to the named operation. Native errors carry their domain/code pair; decode or contract diagnostics may carry only a message.

- <a id="contract-equipment-error-operation"></a>**`operation`** (string): Failing boundary: service_seal, inventory_read, inventory_decode, worker_path, worker_hash, worker_signature, worker_entitlements, guest_code, dynamic_validity, associated_static_code or signing_information.
- <a id="contract-equipment-error-domain"></a>**`domain`** (string?): Native error domain, bounded to <!-- span limits.equipment_error_domain.value_unit -->128 UTF-8 bytes<!-- /span -->; supplied together with code.
- <a id="contract-equipment-error-code"></a>**`code`** (integer?): Native error code in domain, such as OSStatus or POSIX errno; absent together with domain for message-only diagnostics.
- <a id="contract-equipment-error-message"></a>**`message`** (string?): Human-readable diagnostic bounded to <!-- span limits.equipment_diagnostic_bytes.value_unit -->1,024 UTF-8 bytes<!-- /span -->, when supplied.

<a id="contract-equipment-actor"></a>
### Actor equipment selection

Record `eq_actor`: `PWRunnerActorEquipment`.

Selection resolves the actor’s role, binds its entitlement requirements and carries the live inspection result used for activation eligibility.

- <a id="contract-equipment-actor-requested"></a>**`requested`** (string ∪ null): Explicit selected or unentitled request; null when the request omitted equipment. Admitted vocabulary: closed; displayed list: exhaustive: `"selected"`, `"unentitled"`.
- <a id="contract-equipment-actor-resolved"></a>**`resolved`** (string): Requested role, defaulting to selected when omitted. Admitted vocabulary: closed; displayed list: exhaustive: `"selected"`, `"unentitled"`.
- <a id="contract-equipment-actor-binding_ref"></a>**`binding_ref`** (integer ∪ null): Zero-based index of the selected role/source row in equipment_bindings once that row exists.
- <a id="contract-equipment-actor-required_entitlements"></a>**`required_entitlements`** (array of string): Distinct requested entitlement keys, at most <!-- span limits.actor_required_entitlements.value -->64<!-- /span -->; each nonempty key is at most <!-- span limits.actor_entitlement_key.value_unit -->255 UTF-8 bytes<!-- /span -->.
- <a id="contract-equipment-actor-requirements_status"></a>**`requirements_status`** (string): satisfied or unsatisfied from the static entitlement dictionary; unobserved when read-back is unavailable. Admitted vocabulary: closed; displayed list: exhaustive: `"satisfied"`, `"unsatisfied"`, `"unobserved"`.
- <a id="contract-equipment-actor-missing_requirements"></a>**`missing_requirements`** (array of string?): Requested keys whose values are absent or are not Boolean true, in request order. Empty means all satisfied; absence accompanies unobserved.
- <a id="contract-equipment-actor-execution"></a>**`execution`** ([Live actor inspection](#contract-equipment-execution)): Live code and entitlement observation for the owned actor process before activation.

<a id="contract-equipment-execution"></a>
### Live actor inspection

Record `eq_execution`: `PWRunnerEquipmentExecution`.

For a setup-usable owned actor, the host inspects guest code, dynamic validity, associated static code and signing information before schedule activation.

- <a id="contract-equipment-execution-status"></a>**`status`** (string): matched when every comparison and time/ownership guard succeeds; mismatched for a differing executable/signature/entitlement requirement; inspection_failed for an unavailable inspection boundary; unobserved before eligible inspection. Admitted vocabulary: closed; displayed list: exhaustive: `"matched"`, `"mismatched"`, `"inspection_failed"`, `"unobserved"`.
- <a id="contract-equipment-execution-pid"></a>**`pid`** (integer?): Inspected actor PID, agreeing with its launch record when present.
- <a id="contract-equipment-execution-parent_pid"></a>**`parent_pid`** (integer?): Runner host PID recorded when inspection begins.
- <a id="contract-equipment-execution-observed_at_monotonic_ns"></a>**`observed_at_monotonic_ns`** (integer?): Host monotonic observation time in nanoseconds. A matched record requires valid inspection start and final clock samples, a nondecreasing final time, and both samples before the additional inspection deadline when that deadline was established. The scheduler separately guards the shared setup allowance.
- <a id="contract-equipment-execution-path"></a>**`path`** (string?): Executable path reported by live code inspection, when available.
- <a id="contract-equipment-execution-cdhash"></a>**`cdhash`** (string (hex)?): Live code's CodeDirectory hash, when available. Uses [CodeDirectory hexadecimal width](CONTRACT.md#contract-identity-other-cdhash_hex).
- <a id="contract-equipment-execution-identifier"></a>**`identifier`** (string?): Live signing identifier, when available.
- <a id="contract-equipment-execution-team_id"></a>**`team_id`** (string; present when identifier has a value; may be null): Live signing team, when supplied by the signature.
- <a id="contract-equipment-execution-entitlements_ref"></a>**`entitlements_ref`** (integer?): Zero-based index of this actor's live entitlement read-back, when reached.
- <a id="contract-equipment-execution-native_observations"></a>**`native_observations`** (array of [Live inspection call](#contract-equipment-native_observation)): Ordered attempted prefix of guest_code, dynamic_validity, associated_static_code and signing_information, preserving each OSStatus.
- <a id="contract-equipment-execution-reason"></a>**`reason`** (string?): Ineligible reason: not_launched, setup_unavailable, process_unavailable, ownership_unresolved, code_lookup_failed, dynamic_validation_failed, signing_readback_failed, executable_mismatch, signature_identity_mismatch, entitlement_mismatch, requirements_unsatisfied or inspection_deadline. Admitted vocabulary: closed; displayed list: exhaustive: `"not_launched"`, `"setup_unavailable"`, `"process_unavailable"`, `"ownership_unresolved"`, `"code_lookup_failed"`, `"dynamic_validation_failed"`, `"signing_readback_failed"`, `"executable_mismatch"`, `"signature_identity_mismatch"`, `"entitlement_mismatch"`, `"requirements_unsatisfied"`, `"inspection_deadline"`.
- <a id="contract-equipment-execution-eligible"></a>**`eligible`** (boolean): True for matched execution, making this setup-usable actor eligible for activation; false preserves the failed or unavailable inspection state.

<a id="contract-equipment-execution-inspect"></a>
#### Associating the owned process

[Runner host](CONTRACT.md#contract-identity-definitions-host) acts at after setup and before any actor activation. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Applies when present(`request.actors`). For each setup-usable child with retained ownership, inspect live code and compare path, CodeDirectory hash, identifier, team and entitlement dictionary to its bound row; recheck each required Boolean-true entitlement and the inspection deadline. Matched inspection permits activation eligibility. Mismatch or inspection failure cancels all scheduling, retains earlier setup/application publications and leaves all phases unactivated and uncollected. An unavailable setup can coexist with other usable actors when no inspection failure cancels them.

The scheduler includes inspection in its shared <!-- span limits.actor_setup_allowance.value_unit -->10,000 milliseconds<!-- /span --> monotonic setup allowance. It requires valid clock samples before and after each inspection and records inspection_deadline, cancelling scheduling, when an otherwise successful inspection reaches or exceeds that setup deadline. Before the scheduler runs, orchestration also attempts to establish an additional monotonic deadline <!-- span limits.actor_lifetime_cutoff.value_unit -->180,000 milliseconds<!-- /span --> from that initial clock sample, reusing the configured actor-lifetime duration. This additional deadline has its own clock and origin, separate from the workers' shared continuous-clock cutoff. When its initial sample is unavailable, the additional deadline comparison is absent; the scheduler's setup guard and the inspection's valid start/final clock samples still apply. When present, the additional deadline requires both inspection samples strictly before it.

Inspection retains each attempted native call and stops at its first failed
boundary. A later inspection failure preserves an earlier cancellation reason
already selected by the scheduler. Static `bound` and live `matched` express
their respective observations; the signature entitlement dictionary supplies
the values assessed at each boundary.

<a id="contract-equipment-execution-live_evidence"></a>
#### Live-inspection evidence limit

Constructed Security-call failures establish attempted-prefix retention, inspection_failed and ineligibility. Signed normal observations establish association of the selected worker with its live inspection. Spontaneous native Security failure after application remains unobserved. The optional deadline after an unavailable initial orchestration clock sample is source-supported; later inspection-clock controls concern their own samples.

<a id="contract-equipment-execution-live_evidence-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Live-inspection evidence limit](#contract-equipment-execution-live_evidence).** Live-inspection classification and the optional additional orchestration deadline have distinct inputs. Context: Static review of the cited producer and assertion branches. Evidence limit: Injected failure prefixes and later clock controls supply constructed observations. Ownership loss or a mismatch has a different outcome from native inspection failure. [Evidence details](CONTRACT.md#contract-equipment-execution-live_evidence-disposition_support-details).

<a id="contract-equipment-execution-eligibility"></a>
#### Inspection result eligibility

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at live actor inspection result projection. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Select the first matching case in the listed order.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-equipment-execution-eligibility-matched"></a>1. Matched inspection | `eq_execution.status` = `"matched"` | [set_value(`eq_execution.eligible`, `true`), set_value(`eq_execution.reason`, `null`)]. |
| <a id="contract-equipment-execution-eligibility-refused"></a>2. Refused inspection | `eq_execution.status` ∈ [`"mismatched"`, `"inspection_failed"`] | set_value(`eq_execution.eligible`, `false`). |

<a id="contract-equipment-execution-eligibility-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Inspection result eligibility](#contract-equipment-execution-eligibility).** A matched live inspection publishes eligibility; mismatched or failed inspection remains ineligible. Native ownership/deadline/entitlement checks precede these states. [Evidence details](CONTRACT.md#contract-equipment-execution-eligibility-support-details).

<a id="contract-equipment-native_observation"></a>
### Live inspection call

Record `eq_native_observation`: `PWRunnerEquipmentNativeObservation`.

Each row identifies one attempted Security-framework boundary in its observed order.

- <a id="contract-equipment-native_observation-operation"></a>**`operation`** (string): guest_code, dynamic_validity, associated_static_code or signing_information, in that order as reached. Admitted vocabulary: closed; displayed list: exhaustive: `"guest_code"`, `"dynamic_validity"`, `"associated_static_code"`, `"signing_information"`.
- <a id="contract-equipment-native_observation-attempted"></a>**`attempted`** (boolean): True for the recorded call; the observed prefix ends at the first failing boundary.
- <a id="contract-equipment-native_observation-osstatus"></a>**`osstatus`** (integer?): Native OSStatus returned by this operation, including zero for success.

<a id="contract-equipment-preparation_failure"></a>
### Actor preparation refusal

Record `eq_preparation_failure`: `PWRunnerPreparationFailure`.

Preparation stops before actor launch when the resolved plan is inconsistent or static equipment cannot be bound.

- <a id="contract-equipment-preparation_failure-stage"></a>**`stage`** (string): resolved_plan or equipment, identifying the refusing preparation boundary. Admitted vocabulary: closed; displayed list: exhaustive: `"resolved_plan"`, `"equipment"`.
- <a id="contract-equipment-preparation_failure-code"></a>**`code`** (string): inconsistent_assignment for resolved_plan; equipment_binding_refused for equipment. Admitted vocabulary: closed; displayed list: exhaustive: `"inconsistent_assignment"`, `"equipment_binding_refused"`.
- <a id="contract-equipment-preparation_failure-actor_id"></a>**`actor_id`** (string?): Actor whose entitlement requirement caused the refusal, when associated.
- <a id="contract-equipment-preparation_failure-binding_ref"></a>**`binding_ref`** (integer?): Zero-based refused binding row when one was produced or identified.
- <a id="contract-equipment-preparation_failure-reason"></a>**`reason`** (string?): Equipment refusal classification, when the failure arose from equipment preparation.

<a id="contract-equipment-preparation_failure-retain"></a>
#### Preparation refusal contents

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at actor preparation refusal before launch. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Applies when (present(`request.actors`) and present(`request.phases`)). [set_value(`reply.execution_form`, `"actors"`), set_value(`reply.normalized_outcome`, `"runner_failed"`), set_value(`reply.rc`, `1`), set_value(`reply.steps`, []), set_value(`reply.extension_events`, []), set_value(`reply.transfers`, []), set_value(`reply.resources.tokens`, []), set_value(`reply.resources.deliveries`, []), set_value(`reply.resources.handles`, []), set_value(`reply.schedule.cancelled`, `"preparation_refused"`), set_value(`reply.authority_setup.host.run.disposition`, `"not_attempted"`), set_value(`reply.authority_setup.host.regions`, []), set_value(`reply.authority_setup.host.custody`, []), retain_records(`reply.equipment_inventory`), retain_records(`reply.equipment_bindings`), retain_records(`reply.equipment_entitlements`)]. The resolved plan is inconsistent or equipment binding fails before actor launch.

Actors have `launch_refused` setup, absent launch/subprocess, and application
assessment from their declaration and unlaunched state. Phases keep their
declared identities with false arrival/completion and collection `not_reached`.
Equipment inventory/binding/read-back rows preserve whichever preparation
observations were obtained. The schedule records `preparation_refused`; host
authority run setup is `not_attempted`, regions/custody are empty, and worker
setup scopes identify their declared actors with decision `not_observed`.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-equipment-preparation_failure-retain-counts"></a>Declaration row counts | Requires (count(`reply.actors`) = count(`request.actors`) and count(`reply.phases`) = count(`request.phases`)). |
| <a id="contract-equipment-preparation_failure-retain-actors"></a>Unlaunched actor rows | Binding `a`: entry in `reply.actors`. For each `a`. [set_value(`reply.actors[a].setup_status`, `"launch_refused"`), set_value(`reply.actors[a].application_count`, `0`), withhold(`reply.actors[a].launch`), withhold(`reply.actors[a].subprocess`)]. |
| <a id="contract-equipment-preparation_failure-retain-phases"></a>Unactivated phase rows | Binding `p`: entry in `reply.phases`. For each `p`. [set_value(`reply.phases[p].arrival_observed`, `false`), set_value(`reply.phases[p].completion_observed`, `false`), set_value(`reply.phases[p].collection_status`, `"not_reached"`)]. |
| <a id="contract-equipment-preparation_failure-retain-actor_identity"></a>Actor identity in declaration order | Binding `a`: entry in `request.actors`. Binding `b`: entry in `reply.actors`. For each `a`, `b`. Applies when `a` = `b`. Requires (`request.actors[a].actor_id` = `reply.actors[b].actor_id` and `request.actors[a].sandbox.mode` = `reply.actors[b].mode` and `reply.actors[b].index` = `a`). |
| <a id="contract-equipment-preparation_failure-retain-phase_identity"></a>Phase identity in declaration order | Binding `p`: entry in `request.phases`. Binding `q`: entry in `reply.phases`. For each `p`, `q`. Applies when `p` = `q`. Requires (`request.phases[p].phase_id` = `reply.phases[q].phase_id` and `request.phases[p].actor_id` = `reply.phases[q].actor_id` and `reply.phases[q].ordinal` = (`p` + `1`) and count(`reply.phases[q].action_ids`) = count(`request.phases[p].actions`)). |
| <a id="contract-equipment-preparation_failure-retain-action_probe"></a>Retained probe action identity | Binding `p`: entry in `request.phases`. Binding `q`: entry in `reply.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `b`: entry in `reply.phases[q].action_ids`. For each `p`, `q`, `a`, `b`. Applies when (`p` = `q` and `a` = `b` and is_variant(`request.phases[p].actions[a]`, `"probe"`)). Requires `reply.phases[q].action_ids[b]` = `variant(request.phases[p].actions[a], 'probe').step_id`. |
| <a id="contract-equipment-preparation_failure-retain-action_extensionaction"></a>Retained extensionAction action identity | Binding `p`: entry in `request.phases`. Binding `q`: entry in `reply.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `b`: entry in `reply.phases[q].action_ids`. For each `p`, `q`, `a`, `b`. Applies when (`p` = `q` and `a` = `b` and is_variant(`request.phases[p].actions[a]`, `"extensionAction"`)). Requires `reply.phases[q].action_ids[b]` = `variant(request.phases[p].actions[a], 'extensionAction').step_id`. |

<a id="contract-equipment-preparation_failure-retain-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Preparation refusal contents](#contract-equipment-preparation_failure-retain).** Before-launch plan or equipment refusal enumerates the already-admitted request actors, phases and action IDs in declaration order, preserving available equipment beside empty execution collections and unlaunched/unactivated states. [Evidence details](CONTRACT.md#contract-equipment-preparation_failure-retain-support-details).

<a id="contract-equipment-authority_setup"></a>
### Authority setup account

Record `eq_authority_setup`: `PWRunnerAuthoritySetup`.

The host retains its own setup/cleanup observations and each worker’s separately acquired setup publications.

- <a id="contract-equipment-authority_setup-host"></a>**`host`** ([Host authority scopes](#contract-equipment-authority_host)): Host-owned run, shared-region and custody scopes.
- <a id="contract-equipment-authority_setup-workers"></a>**`workers`** (array of [Authority operation scope](#contract-equipment-authority_scope)): Actor-indexed worker setup scopes, one per declared actor and bound to that actor's identifier.

<a id="contract-equipment-authority_host"></a>
### Host authority scopes

Record `eq_authority_host`: `PWRunnerAuthorityHost`.

The host separates run prerequisites, actor shared regions and token custody into their owning scopes.

- <a id="contract-equipment-authority_host-run"></a>**`run`** ([Authority operation scope](#contract-equipment-authority_scope)): Run-wide prerequisite account, including core-limit setup.
- <a id="contract-equipment-authority_host-regions"></a>**`regions`** (array of [Authority operation scope](#contract-equipment-authority_scope)): Per-actor shared authority-region allocation, initialization, descriptor and cleanup observations.
- <a id="contract-equipment-authority_host-custody"></a>**`custody`** (array of [Authority operation scope](#contract-equipment-authority_scope)): Per-token host-private custody allocation, erasure and unmap observations.

<a id="contract-equipment-authority_scope"></a>
### Authority operation scope

Record `eq_authority_scope`: `PWRunnerAuthorityScope`.

A scope retains operation cells, its setup decision and ownership state. A decision and individual operation publications have separate acquisition boundaries.

- <a id="contract-equipment-authority_scope-actor_id"></a>**`actor_id`** (string?): Bound actor identifier for worker or region scope, when applicable.
- <a id="contract-equipment-authority_scope-actor_index"></a>**`actor_index`** (integer?): Zero-based actor position for worker or region scope.
- <a id="contract-equipment-authority_scope-token_ref"></a>**`token_ref`** (string?): Bound token identifier for custody scope, when applicable.
- <a id="contract-equipment-authority_scope-token_index"></a>**`token_index`** (integer?): Zero-based token position for custody scope.
- <a id="contract-equipment-authority_scope-required"></a>**`required`** (boolean?): Whether authority setup is required for the worker's admitted actor plan.
- <a id="contract-equipment-authority_scope-publication"></a>**`publication`** (string?): Worker decision acquisition: observed or not_observed; host-recorded scopes use their directly recorded disposition. Admitted vocabulary: closed; displayed list: exhaustive: `"observed"`, `"not_observed"`.
- <a id="contract-equipment-authority_scope-disposition"></a>**`disposition`** (string?): Worker decision ready, not_required or terminal_required_failure when observed; host scope state such as not_attempted, ready or failed records its own preparation.
- <a id="contract-equipment-authority_scope-primary_operation"></a>**`primary_operation`** (integer?): Slot of the first failed/rejected operation supporting the scope decision; worker terminal_required_failure requires that published primary cell.
- <a id="contract-equipment-authority_scope-operations"></a>**`operations`** (array of [Authority operation cell](#contract-equipment-authority_operation)): Independently observed operation cells in slot order, including cleanup after a setup failure.
- <a id="contract-equipment-authority_scope-ownership"></a>**`ownership`** (object with string keys and string values): Named ownership states: object_name, descriptor and mapping use not_acquired, held, released or unresolved; shared_erasure/private_erasure use not_present, performed, withheld_not_quiescent or unobserved.
- <a id="contract-equipment-authority_scope-cleanup_reference"></a>**`cleanup_reference`** ([Unresolved shared-memory name](#contract-equipment-cleanup_reference)?): Retained unresolved shared-memory name after successful creation and failed unlink, requiring ownership-aware recovery.
- <a id="contract-equipment-authority_scope-integrity_errors"></a>**`integrity_errors`** (array of string?): Detected malformed, repeated, missing-primary or mismatched-association publications; absence means the decoder found none.

<a id="contract-equipment-authority_scope-acquire"></a>
#### Acquiring setup decisions and operations

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at worker shared-region collection. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Applies when present(`request.actors`). After worker-identity agreement, acquire-load the decision snapshot first, then independently acquire-load each published operation cell. Retain independently valid operation cells even when the decision is absent. For an observed decision, validate its raw actor/required association before projecting the decision and its primary operation.

The decision's release orders prerequisite cells. Reading the decision first
keeps a newly observed decision joined to its earlier primary publication.
Each cell still has its own publication flag and kind/state guards. A cleanup
cell can therefore be retained before the terminal decision appears. Invalid
cells contribute integrity errors while independently valid observations
remain available.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-equipment-authority_scope-acquire-primary"></a>Retained primary support | Binding `o`: entry in `eq_authority_scope.operations`. Association restriction for `o`: (`eq_authority_scope.operations[o].slot` = `eq_authority_scope.primary_operation` and `eq_authority_scope.operations[o].state` ∈ [`"failed"`, `"rejected"`]). Applies when (`eq_authority_scope.publication` = `"observed"` and present(`eq_authority_scope.primary_operation`)). Requires implies(matches(`o`) = `0`, (present(`eq_authority_scope.integrity_errors`) and `"setup_primary_unpublished"` ∈ `eq_authority_scope.integrity_errors`)). A missing primary cell adds an integrity error alongside the decision and independently valid cells. |
| <a id="contract-equipment-authority_scope-acquire-decision"></a>Observed decision applicability | Applies when `eq_authority_scope.publication` = `"observed"`. Requires (implies(`eq_authority_scope.disposition` = `"terminal_required_failure"`, (`eq_authority_scope.required` and present(`eq_authority_scope.primary_operation`))) and implies(`eq_authority_scope.disposition` = `"ready"`, `eq_authority_scope.required`) and implies(`eq_authority_scope.disposition` = `"not_required"`, `eq_authority_scope.required` = `false`)). |

<a id="contract-equipment-authority_scope-publication_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Authority operation scope](#contract-equipment-authority_scope) and its descendants.** Constructed published cleanup cell survives absent decision, preserves native failure and cleanup role; corrupted publication flags yield invalid_setup_cell. Context: Constructed shared-memory buffer decoded by the production host decoder; source and assertions read. Evidence limit: The check covers cell eligibility and corrupted flags; source supplies decision-first acquisition and primary-cell validation. No execution credit. [Evidence details](CONTRACT.md#contract-equipment-authority_scope-publication_support-details).

<a id="contract-equipment-authority_operation"></a>
### Authority operation cell

Record `eq_authority_operation`: `PWRunnerAuthorityOperation`.

Each fixed slot identifies one operation once. Kind controls which native fields are meaningful; cleanup cells retain their own failures alongside the primary setup failure.

- <a id="contract-equipment-authority_operation-slot"></a>**`slot`** (integer): Zero-based fixed operation-cell position within its worker, region, custody or run scope.
- <a id="contract-equipment-authority_operation-operation"></a>**`operation`** (string): Operation registered for that scope and slot, such as descriptor_close, header_binding, shm_unlink or final_erase.
- <a id="contract-equipment-authority_operation-role"></a>**`role`** (string): setup or cleanup, according to the operation's boundary. Admitted vocabulary: closed; displayed list: exhaustive: `"setup"`, `"cleanup"`.
- <a id="contract-equipment-authority_operation-state"></a>**`state`** (string): succeeded/failed for native integer or mapping operations; accepted/rejected for validation; available/unavailable for symbols; performed for memory operations; not_attempted for an explicitly unattempted cell. Admitted vocabulary: closed; displayed list: exhaustive: `"succeeded"`, `"failed"`, `"accepted"`, `"rejected"`, `"available"`, `"unavailable"`, `"performed"`, `"not_attempted"`.
- <a id="contract-equipment-authority_operation-native_kind"></a>**`native_kind`** (string?): integer, error_code, mapping, symbol, validation or memory, identifying the observation convention. Admitted vocabulary: closed; displayed list: exhaustive: `"integer"`, `"error_code"`, `"mapping"`, `"symbol"`, `"validation"`, `"memory"`.
- <a id="contract-equipment-authority_operation-native_rc"></a>**`native_rc`** (integer?): Recorded return for integer/error_code operations; absent for mapping, symbol, validation and memory observations.
- <a id="contract-equipment-authority_operation-errno"></a>**`errno`** (integer?): Captured native errno on failed integer/mapping operations; absent for other states and kinds.
- <a id="contract-equipment-authority_operation-detail"></a>**`detail`** (string?): Operation-specific validation reason, including descriptor_missing or header magic/identity/actor_index/slot_counts/region_extent mismatch.
- <a id="contract-equipment-authority_operation-value"></a>**`value`** (integer?): Operation-specific unsigned native observation when the cell marks a value present, such as object/page size.

<a id="contract-equipment-authority_operation-slots"></a>
#### Registered operation slots

Value: `{"run":["core_limit"],"worker":["issue_symbol","consume_symbol","release_symbol","core_limit","descriptor_presence","fstat","page_size","object_size","mmap","descriptor_close","header_binding","terminal_owned_inbound_clear","rejected_mapping_munmap"],"region":["shm_open","shm_unlink","fd_cloexec","ftruncate","mmap","header_initialize","authority_duplicate","authority_spawn_dup2","close_launch_duplicate","close_original_descriptor","shared_clear","munmap"],"custody":["mmap","final_erase","munmap"]}`.

The index within each list is its fixed slot. Worker descriptor close can
belong to setup or cleanup according to the branch. Worker slots 11–12,
region slots 8–11 and custody slots 1–2 are cleanup.

<a id="contract-equipment-cleanup_reference"></a>
### Unresolved shared-memory name

Record `eq_cleanup_reference`: `PWAuthorityCleanupReference`.

A successful shm_open followed by failed shm_unlink retains this recovery reference while preserving unresolved ownership.

- <a id="contract-equipment-cleanup_reference-kind"></a>**`kind`** (string): posix_shm_name, the retained resource name form. Admitted vocabulary: closed; displayed list: exhaustive: `"posix_shm_name"`.
- <a id="contract-equipment-cleanup_reference-name"></a>**`name`** (string): Absolute POSIX shared-memory name beginning with slash, at most <!-- span limits.authority_cleanup_name.value_unit -->31 UTF-8 bytes<!-- /span -->.
- <a id="contract-equipment-cleanup_reference-host_pid"></a>**`host_pid`** (integer): Host PID recorded when the name was created.
- <a id="contract-equipment-cleanup_reference-session_nonce"></a>**`session_nonce`** (integer): Run nonce associated with creation of this named region.
- <a id="contract-equipment-cleanup_reference-recovery_state"></a>**`recovery_state`** (string): unresolved_manual: recovery must establish current ownership before acting because a reused name can identify another object. Admitted vocabulary: closed; displayed list: exhaustive: `"unresolved_manual"`.
<!-- END GENERATED CONTRACT equipment -->

## Read compiled-profile receipts

Follow a requested capture from its [policy declaration](REQUEST.md#contract-policy-spec) to the receipt’s presence, identity and producer conditions. A captured object has its stated scope; it is not an interpretation of all native enforcement behavior.

<!-- BEGIN GENERATED CONTRACT profile -->
<a id="contract-profile"></a>
## Compiled-profile receipts

Entry: cli run, runner verify, direct xpc. Recipient: controller, xpc caller, cli caller. Reports: runner reply.

The host reports the result of an optional capture of the worker's compiled policy before application.

<a id="contract-profile-receipt"></a>
### Receipt

Binding `a`: entry in `reply.actors`. Record `receipt` locations: `reply.compiled_profile`, `reply.actors[a].compiled_profile`.

The containing reply's producer contract identifies the receipt's contract.

- <a id="contract-profile-receipt-status"></a>**`status`** (string): `captured` states that the host's capture checks passed. `unavailable` states that a capture condition failed. Admitted vocabulary: closed; displayed list: exhaustive: `"captured"`, `"unavailable"`.
- <a id="contract-profile-receipt-reason"></a>**`reason`** (string?): The host names the first failing capture condition. The controller's label check accepts the carried reason string. Boundary: controller reply admission. Admitted vocabulary: open; displayed list: illustrative: `"successful_application_unconfirmed"`, `"worker_not_complete"`, `"capture_nonce_mismatch"`. Unfamiliar values: retained as the host's reason string.
- <a id="contract-profile-receipt-worker_pid"></a>**`worker_pid`** (integer): The process identifier of the worker whose output the host collected.
- <a id="contract-profile-receipt-producer"></a>**`producer`** (string?): `worker` on a captured receipt identifies the component that captured the bytes.
- <a id="contract-profile-receipt-capture_stage"></a>**`capture_stage`** (string?): `before_apply` on a captured receipt identifies when the worker captured the bytes.
- <a id="contract-profile-receipt-request_nonce"></a>**`request_nonce`** (string?): The host returns the request's capture nonce after comparing it with the worker's recorded bytes. A comparison with a separately retained request nonce supplies a consumer's request association; the controller's carried-label check has no request-nonce operand.
- <a id="contract-profile-receipt-profile_type"></a>**`profile_type`** (integer?): The supported compiler result representation is `0`.
- <a id="contract-profile-receipt-bytecode_length"></a>**`bytecode_length`** (integer?): The number of raw bytes copied from the compiled object, positive and at most <!-- span limits.compiled_profile.value_unit -->1,048,576 bytes<!-- /span -->. It counts the decoded bytes represented by `bytecode_b64`, separately for each opted-in worker.
- <a id="contract-profile-receipt-bytecode_sha256"></a>**`bytecode_sha256`** (string (hex)?): The host's SHA-256 digest of the captured bytes, presented as lowercase hexadecimal.
- <a id="contract-profile-receipt-bytecode_b64"></a>**`bytecode_b64`** (string (base64)?): The bytes copied from the compiler object passed to `sandbox_apply`, presented as base64.
- <a id="contract-profile-receipt-source_sha256"></a>**`source_sha256`** (string (hex)?): The SHA-256 digest of the UTF-8 C-string source passed to compilation, presented as lowercase hexadecimal. The host compares it with its supplied source bytes; an embedded NUL cannot establish the full source identity.
- <a id="contract-profile-receipt-source_length"></a>**`source_length`** (integer?): The supplied source's UTF-8 byte count.
- <a id="contract-profile-receipt-params_sha256"></a>**`params_sha256`** (string (hex)?): The order-independent digest of parameter names and values consumed by the worker, presented as lowercase hexadecimal.
- <a id="contract-profile-receipt-parameter_count"></a>**`parameter_count`** (integer?): The count of parameters supplied to the worker.

**Bytecode length.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-profile-receipt-bytecode_length-captured"></a>Captured byte extent | Requires implies(`receipt.status` = `"captured"`, (present(`receipt.bytecode_length`) and `receipt.bytecode_length` > `0` and `receipt.bytecode_length` ≤ `1,048,576 bytes` (`compiled_profile`) )). |

**Bytecode.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-profile-receipt-bytecode_b64-extent"></a>Captured payload extent | Applies when `receipt.status` = `"captured"`. Requires byte_length(`receipt.bytecode_b64`) = `receipt.bytecode_length`. |

<a id="contract-profile-receipt-identity"></a>
#### Captured input identity

Each parameter pair digest hashes its little-endian 32-bit key length, key bytes, little-endian 32-bit value length and value bytes. The parameter digest hashes the little-endian 32-bit count followed by sorted pair digests.

<a id="contract-profile-receipt-presence"></a>
#### Receipt presence

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at worker collection. Entry: cli run, runner verify, direct xpc. Recipient: controller, xpc caller. Reports: runner reply. Capture was requested for this worker and worker output was collected. Include the optional capture receipt in that worker output.

A failure that produces no worker output leaves the receipt absent; absence has several possible causes.

<a id="contract-profile-receipt-host"></a>
#### The host decides capture availability

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at collected worker capture decoding. Entry: cli run, runner verify, direct xpc. Recipient: controller, xpc caller. Reports: runner reply. Capture was requested for this worker and worker output was collected. The first failed condition selects the consequence.

Passing every condition produces `captured` with the capture fields.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-profile-receipt-host-application"></a>Application | Application was observed and its return code was zero. |
| <a id="contract-profile-receipt-host-application-failure"></a>Application › First failed guard reason | On failure, [set_value(`receipt.reason`, `"successful_application_unconfirmed"`)]. |
| <a id="contract-profile-receipt-host-completion"></a>Worker completion | Follows [Application](#contract-profile-receipt-host-application). The worker published done and the collected exit code is zero with no terminating signal. |
| <a id="contract-profile-receipt-host-completion-failure"></a>Worker completion › First failed guard reason | On failure, [set_value(`receipt.reason`, `"worker_not_complete"`)]. |
| <a id="contract-profile-receipt-host-capture"></a>Capture completion | Follows [Worker completion](#contract-profile-receipt-host-completion). The worker published capture completion. |
| <a id="contract-profile-receipt-host-capture-failure"></a>Capture completion › First failed guard reason | On failure, [set_value(`receipt.reason`, `"capture_not_complete"`)]. |
| <a id="contract-profile-receipt-host-status"></a>Capture status | Follows [Capture completion](#contract-profile-receipt-host-capture). The recorded capture status was accepted. |
| <a id="contract-profile-receipt-host-status-failure"></a>Capture status › First failed guard reason | On failure, [set_value(`receipt.reason`, `"worker_capture_refused"`)]. |
| <a id="contract-profile-receipt-host-pid"></a>Process association | Follows [Capture status](#contract-profile-receipt-host-status). The recorded PID equals the worker PID collected by the host. |
| <a id="contract-profile-receipt-host-pid-failure"></a>Process association › First failed guard reason | On failure, [set_value(`receipt.reason`, `"capture_worker_mismatch"`)]. |
| <a id="contract-profile-receipt-host-nonce"></a>Nonce association | Follows [Process association](#contract-profile-receipt-host-pid). The recorded nonce bytes equal the valid request nonce. |
| <a id="contract-profile-receipt-host-nonce-failure"></a>Nonce association › First failed guard reason | On failure, [set_value(`receipt.reason`, `"capture_nonce_mismatch"`)]. |
| <a id="contract-profile-receipt-host-extent"></a>Extent and type | Follows [Nonce association](#contract-profile-receipt-host-nonce). The profile type is zero and its raw byte count is positive and at most <!-- span limits.compiled_profile.value_unit -->1,048,576 bytes<!-- /span -->. |
| <a id="contract-profile-receipt-host-extent-failure"></a>Extent and type › First failed guard reason | On failure, [set_value(`receipt.reason`, `"capture_extent_or_type_invalid"`)]. |
| <a id="contract-profile-receipt-host-digest"></a>Payload digest | Follows [Extent and type](#contract-profile-receipt-host-extent). SHA-256 of the captured bytes equals the recorded digest. |
| <a id="contract-profile-receipt-host-digest-failure"></a>Payload digest › First failed guard reason | On failure, [set_value(`receipt.reason`, `"capture_bytecode_digest_mismatch"`)]. |
| <a id="contract-profile-receipt-host-input"></a>Consumed input | Follows [Payload digest](#contract-profile-receipt-host-digest). The recorded source length and digest and parameter count and digest equal the host's supplied inputs. |
| <a id="contract-profile-receipt-host-input-failure"></a>Consumed input › First failed guard reason | On failure, [set_value(`receipt.reason`, `"capture_consumed_input_mismatch"`)]. |
| <a id="contract-profile-receipt-host-failure"></a>Capture failure | On failure, [set_value(`receipt.status`, `"unavailable"`), withhold(`receipt.producer`), withhold(`receipt.capture_stage`), withhold(`receipt.request_nonce`), withhold(`receipt.profile_type`), withhold(`receipt.bytecode_length`), withhold(`receipt.bytecode_sha256`), withhold(`receipt.bytecode_b64`), withhold(`receipt.source_sha256`), withhold(`receipt.source_length`), withhold(`receipt.params_sha256`), withhold(`receipt.parameter_count`), retain_assessments(`reply.normalized_outcome`)]. |
| <a id="contract-profile-receipt-host-success"></a>Successful receipt | On success, [set_value(`receipt.status`, `"captured"`), set_value(`receipt.producer`, `"worker"`), set_value(`receipt.capture_stage`, `"before_apply"`), set_value(`receipt.profile_type`, `0`), withhold(`receipt.reason`)]. |

<a id="contract-profile-receipt-host-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [The host decides capture availability](#contract-profile-receipt-host).** The read checks construct worker bytes, corrupt each capture input and assert unavailability and withheld bytecode. Context: Constructed shared-memory bytes and injected application/termination arguments. Evidence limit: This owner credits source and check reading. The shared-memory fixture establishes host checks; the native same-pointer capture is source-supported here. [Evidence details](CONTRACT.md#contract-profile-receipt-host-support-details).

<a id="contract-profile-receipt-labels"></a>
#### The controller checks carried labels

[Controller](CONTRACT.md#contract-identity-definitions-controller) checks at reply admission. Entry: cli run, runner verify. Recipient: cli caller. Reports: runner reply. Applies when present(`receipt`).

After public producer admission and reply-capacity checks, the controller applies these conditions to every present receipt, including actor, preparation-failure and reporting-failure records. The retained nonce, bytecode, digests, lengths and counts remain the host's assertions; their production checks belong to the host capture rule.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-profile-receipt-labels-status"></a>Status vocabulary | Requires `receipt.status` ∈ [`"captured"`, `"unavailable"`]. |
| <a id="contract-profile-receipt-labels-captured"></a>Captured labels | Requires implies(`receipt.status` = `"captured"`, (`receipt.producer` = `"worker"` and `receipt.capture_stage` = `"before_apply"`)). |
| <a id="contract-profile-receipt-labels-unavailable"></a>Unavailable labels | Requires implies(`receipt.status` = `"unavailable"`, (absent(`receipt.producer`) and absent(`receipt.capture_stage`))). |
| <a id="contract-profile-receipt-labels-failure"></a>A failed label check for run | Entry: cli run. On failure, [set_value(`envelope.result.normalized_outcome`, `"malformed_runner_response"`), set_value(`envelope.result.ok`, `false`), withhold(`envelope.data.runner_sandbox_diagnostics`), retain_records(`reply`)]. For `run`, the controller refuses admission of the containing report, reports a failed result and exits with status 1. The retained report remains the host's account. |
| <a id="contract-profile-receipt-labels-verify_failure"></a>A failed label check for runner verify | Entry: runner verify. On failure, [set_value(`result.ok`, `false`), set_value(`result.exit_code`, `1`), set_value(`result.normalized_outcome`, `"malformed_runner_response"`), set_value(`runner_verify.normalized_outcome`, `"malformed_runner_response"`), set_value(`runner_verify.runner_pid`, `null`), retain_records(`runner_verify.runner_client`), retain_records(`runner_verify.runner_result`)]. `runner verify` emits its verification envelope and exits with status 1. |

<a id="contract-profile-receipt-labels-failure-support"></a>
**Support: [executed](CONTRACT.md#contract-support-grades) for [A failed label check for run](#contract-profile-receipt-labels-failure) and its descendants.** The constructed check follows admission through the public outcome, exit status, result, retained decoded report and diagnostic presence. Context: Constructed typed replies carried through the run command admission and envelope path. Evidence limit: The unit case passed against the source committed as 5e51300d; its development run is disposable. Constructed replies establish admission and retention, while native capture is a separate observation. [Evidence details](CONTRACT.md#contract-profile-receipt-labels-failure-support-details).

<a id="contract-profile-receipt-labels-verify_failure-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [A failed label check for runner verify](#contract-profile-receipt-labels-verify_failure).** A refused verify reply preserves the returned capture and decoded report, leaves runner_pid null, copies the refusal classification into data and result, and returns exit 1. Context: Read the verify command's Refused branch, payload construction, JsonResult construction and returned exit code. Evidence limit: The verify consequence is supported by these branches. The executed constructed-label case belongs to the run consequence. [Evidence details](CONTRACT.md#contract-profile-receipt-labels-verify_failure-support-details).

<a id="contract-profile-receipt-labels-example"></a>
##### An unsupported capture producer

A current-build reply carries a captured receipt whose producer is `future`. The receipt-label check refuses that reply as `malformed_runner_response`.

<a id="contract-profile-receipt-labels-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [The controller checks carried labels](#contract-profile-receipt-labels) and its descendants.** Run and runner verify use the same post-version reply admission; it checks each present top-level or actor receipt's status, producer and capture-stage labels before command-specific refusal projection. Context: Read both command routes into reply admission and the compiled-profile label loop. Evidence limit: The predicates and command dispatch are source-read. The executed constructed-label control under the run consequence supplies its separate run evidence. [Evidence details](CONTRACT.md#contract-profile-receipt-labels-support-details).

<a id="contract-profile-receipt-source"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Receipt](#contract-profile-receipt) and its descendants.** Opt-in capture copies the same compiled object before apply; the collected worker output includes the optional host-checked receipt. Fields bind the observed worker, nonce and consumed input bytes. Shared-memory and public JSON projections are distinct. Context: Read C capture, compile/apply call site, Swift output construction and ordered receipt checks. Evidence limit: Source reading establishes the branch account. Live capture behavior and platform private-layout compatibility require their native checks. [Evidence details](CONTRACT.md#contract-profile-receipt-source-details).
<!-- END GENERATED CONTRACT profile -->

## Read extension events and resources

Read native operation events, host transfers and token/delivery/handle tables together with their reference ownership. [ARCHITECTURE](ARCHITECTURE.md#contract-extensions-custody) states custody across preparation, transfer and erasure; [REQUEST](REQUEST.md#contract-extensions-operation) defines admitted operands.

<!-- BEGIN GENERATED CONTRACT extensions -->
<a id="contract-extensions-event"></a>
### Extension event

Record `event`: `PWRunnerExtensionEvent`.

- <a id="contract-extensions-event-phase_id"></a>**`phase_id`** (string): Declared phase containing the action.
- <a id="contract-extensions-event-step_id"></a>**`step_id`** (string): Declared action identifier.
- <a id="contract-extensions-event-operation"></a>**`operation`** (string): Requested issue, transfer, consume or release operation.
- <a id="contract-extensions-event-token_ref"></a>**`token_ref`** (string?): Declared token reference for issue and transfer; omitted for consume and release.
- <a id="contract-extensions-event-handle_ref"></a>**`handle_ref`** (string?): Declared handle reference for consume and release; omitted for issue and transfer.
- <a id="contract-extensions-event-call_boundary_observed"></a>**`call_boundary_observed`** (boolean): Whether the host observed the worker's release-published marker immediately before a native issue, consume or release call. Transfer uses its separate request publication.
- <a id="contract-extensions-event-result_published"></a>**`result_published`** (boolean): Whether the action's result slot was completed and observed. A false value withholds native result fields even if a call boundary was observed.
- <a id="contract-extensions-event-status"></a>**`status`** (string): `returned` when a completed native result exists; `unavailable` for a published no-call reason; `unresolved` for missing action publication; `invalid` for a completed inconsistent slot. Transfer uses its acknowledgement status.
- <a id="contract-extensions-event-native_result"></a>**`native_result`** (integer?): Published signed native result: issue uses 1 for non-null or 0 for null; consume and release retain their signed result. Consume -1 supplies no handle; another published consume result is the candidate handle.
- <a id="contract-extensions-event-errno"></a>**`errno`** (integer?): Errno captured immediately after the native call when a native result was published. Its value remains paired with that result, including zero.
- <a id="contract-extensions-event-unavailable_reason"></a>**`unavailable_reason`** (string?): Published apparatus reason such as token_unavailable, handle_unavailable, native_api_unavailable, repeated_action, authority_channel_unavailable or delivery_unavailable; omitted when no reason was published.
- <a id="contract-extensions-event-lifecycle"></a>**`lifecycle`** ([Per-attempt lifecycle projection](#contract-lifecycle-attempt)?): Assessment of the action's observed boundary/publication from its actor's disposition evidence.
- <a id="contract-extensions-event-actor_id"></a>**`actor_id`** (string?): Actor owning this action.
- <a id="contract-extensions-event-family"></a>**`family`** (string?): The implemented extension family, `file`.
- <a id="contract-extensions-event-target"></a>**`target`** (string?): Exact declared issue target, present for issue.
- <a id="contract-extensions-event-extension_class"></a>**`extension_class`** (string?): Native issue class selected from read/read_write, present for issue.
- <a id="contract-extensions-event-flags"></a>**`flags`** (integer?): Native issue flags; the implementation supplies zero.
- <a id="contract-extensions-event-delivery_ref"></a>**`delivery_ref`** (string?): Declared delivery reference for transfer and consume.
- <a id="contract-extensions-event-native_nonnull"></a>**`native_nonnull`** (boolean?): Issue result projected as true for published native 1 and false for another published native value; absent without a native result.
- <a id="contract-extensions-event-token_length"></a>**`token_length`** (integer?): Length carried by a completed issue publication, including zero when no bounded token was published. Public payload length excludes the NUL terminator.

<a id="contract-extensions-event-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Extension event](#contract-extensions-event) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. [Evidence details](CONTRACT.md#contract-extensions-event-support-details).

<a id="contract-extensions-event-issue_projection"></a>
#### Project a published issue result

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at completed issue event projection. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Applies when (`event.operation` = `"issue"` and `event.result_published` and present(`event.native_result`)). set_value(`event.native_nonnull`, `event.native_result` = `1`).

<a id="contract-extensions-event-issue_projection-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Project a published issue result](#contract-extensions-event-issue_projection).** A published issue native value projects to native_nonnull; the host custody record carries token acceptance. [Evidence details](CONTRACT.md#contract-extensions-event-issue_projection-support-details).

<a id="contract-extensions-transfer"></a>
### Host transfer observation

Record `transfer`: `PWRunnerTransferRecord`.

The transfer table reports host servicing observations. A worker can time out before the host's answer; source acknowledgement preserves this difference.

- <a id="contract-extensions-transfer-phase_id"></a>**`phase_id`** (string): Phase in which this transfer action was declared.
- <a id="contract-extensions-transfer-step_id"></a>**`step_id`** (string): Transfer action identifier.
- <a id="contract-extensions-transfer-source_actor_id"></a>**`source_actor_id`** (string): Actor owning the token and requesting the transfer.
- <a id="contract-extensions-transfer-recipient_actor_id"></a>**`recipient_actor_id`** (string): Actor assigned the inbound delivery.
- <a id="contract-extensions-transfer-token_ref"></a>**`token_ref`** (string): Requested source token.
- <a id="contract-extensions-transfer-delivery_ref"></a>**`delivery_ref`** (string): Assigned delivery resource.
- <a id="contract-extensions-transfer-request_published"></a>**`request_published`** (boolean): Whether the host observed the explicit transfer request publication.
- <a id="contract-extensions-transfer-custody_status"></a>**`custody_status`** (string): `held` when the host found accepted, unerased custody for this request; otherwise `unavailable`.
- <a id="contract-extensions-transfer-copy_status"></a>**`copy_status`** (string): `copied` after the host copied custody into the inbound slot; otherwise `not_copied`.
- <a id="contract-extensions-transfer-equality"></a>**`equality`** (string): `equal` or `unequal` after comparing acknowledged recipient bytes to custody; otherwise `not_compared`.
- <a id="contract-extensions-transfer-recipient_acknowledged"></a>**`recipient_acknowledged`** (boolean): True when the recipient published either framing acceptance or rejection. Read status to distinguish which.
- <a id="contract-extensions-transfer-source_acknowledged"></a>**`source_acknowledged`** (boolean): True only when the source published a completed action carrying the matching host acknowledgement.
- <a id="contract-extensions-transfer-status"></a>**`status`** (string): Host acknowledgement name: none, delivered, custody_unavailable, recipient_rejected, recipient_timeout, recipient_unavailable, request_invalid, host_timeout, clock_fault or copy_mismatch. Unrecognized raw acknowledgement values are retained as strings by this producer.
- <a id="contract-extensions-transfer-lifecycle"></a>**`lifecycle`** ([Per-attempt lifecycle projection](#contract-lifecycle-attempt)?): Source action's lifecycle assessment when available.
- <a id="contract-extensions-transfer-recipient_wait"></a>**`recipient_wait`** ([Measured host wait](#contract-lifecycle-host_wait)?): Host clock and stop observation for the bounded recipient-acknowledgement wait, when that wait was entered.

<a id="contract-extensions-transfer-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Host transfer observation](#contract-extensions-transfer) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. [Evidence details](CONTRACT.md#contract-extensions-transfer-support-details).

<a id="contract-extensions-transfer-delivered_receipt"></a>
#### Delivered receipt prerequisites

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at host transfer observation projection. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Applies when `transfer.status` = `"delivered"`.

The custody rule describes native framing and settlement.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-extensions-transfer-delivered_receipt-fields"></a>Produced field relationships | Requires (`transfer.request_published` and `transfer.custody_status` = `"held"` and `transfer.copy_status` = `"copied"` and `transfer.equality` = `"equal"` and `transfer.recipient_acknowledged`). |

<a id="contract-extensions-transfer-delivered_receipt-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Delivered receipt prerequisites](#contract-extensions-transfer-delivered_receipt) and its descendants.** A delivered transfer retains the request, custody, copy, recipient acknowledgement and byte-equality observations. [Evidence details](CONTRACT.md#contract-extensions-transfer-delivered_receipt-support-details).

<a id="contract-extensions-transfer-source_association"></a>
#### Source acknowledgement association

[Runner host](CONTRACT.md#contract-identity-definitions-host) reports at ordinary actor report transfer and source-event projection. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Binding `t`: entry in `reply.transfers`. Binding `e`: entry in `reply.extension_events`. Association restriction for `e`: (`reply.extension_events[e].phase_id` = `reply.transfers[t].phase_id` and `reply.extension_events[e].step_id` = `reply.transfers[t].step_id` and `reply.extension_events[e].actor_id` = `reply.transfers[t].source_actor_id` and `reply.extension_events[e].operation` = `"transfer"`). For each `t`. Applies when (absent(`reply.reporting_failure`) and present(`reply.transfers`) and present(`reply.extension_events`)).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-extensions-transfer-source_association-unique"></a>Exactly one published source event | Applies when `reply.transfers[t].source_acknowledged`. Requires matches(`e`) = `1`. |
| <a id="contract-extensions-transfer-source_association-published"></a>Published matching acknowledgement | For each `t`, `e`. Applies when (`reply.transfers[t].source_acknowledged` and `reply.extension_events[e].phase_id` = `reply.transfers[t].phase_id` and `reply.extension_events[e].step_id` = `reply.transfers[t].step_id` and `reply.extension_events[e].actor_id` = `reply.transfers[t].source_actor_id` and `reply.extension_events[e].operation` = `"transfer"`). Requires (`reply.extension_events[e].result_published` and `reply.transfers[t].status` ≠ `"none"` and implies(`reply.transfers[t].status` ∈ [`"delivered"`, `"custody_unavailable"`, `"recipient_rejected"`, `"recipient_timeout"`, `"recipient_unavailable"`, `"request_invalid"`, `"host_timeout"`, `"clock_fault"`, `"copy_mismatch"`], `reply.extension_events[e].status` = `reply.transfers[t].status`)). Unknown raw acknowledgement names and degraded records retain their raw evidence; the status equality applies to ordinary records with the listed known acknowledgement names. |

<a id="contract-extensions-transfer-source_association-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Source acknowledgement association](#contract-extensions-transfer-source_association).** Custody requires a completed source slot with the matching nonzero acknowledgement. Admitted unique actions and consistent delivery assignments identify one source transfer event; assembly maps known acknowledgement values to the same event and transfer status names. [Evidence details](CONTRACT.md#contract-extensions-transfer-source_association-support-details).

<a id="contract-extensions-resources"></a>
### Resource tables

Record `resources`: `PWRunnerResourceTables`.

The tables retain admitted resources whose producing action was not reached or remains unresolved. Declaration establishes the reference; the status supplies observed production.

- <a id="contract-extensions-resources-tokens"></a>**`tokens`** (array of [Token resource](#contract-extensions-token)): Every admitted issue resource in plan order, with its observed production and custody status.
- <a id="contract-extensions-resources-deliveries"></a>**`deliveries`** (array of [Delivery resource](#contract-extensions-delivery)): Every admitted transfer resource in plan order, with its observed delivery status.
- <a id="contract-extensions-resources-handles"></a>**`handles`** (array of [Handle resource](#contract-extensions-handle)): Every admitted consume resource in plan order, with its candidate handle and declared release observations.

<a id="contract-extensions-resources-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Resource tables](#contract-extensions-resources) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. [Evidence details](CONTRACT.md#contract-extensions-resources-support-details).

<a id="contract-extensions-token"></a>
### Token resource

Record `token`: `PWRunnerTokenRecord`.

- <a id="contract-extensions-token-token_ref"></a>**`token_ref`** (string): Declared token identifier.
- <a id="contract-extensions-token-actor_id"></a>**`actor_id`** (string): Issuing actor.
- <a id="contract-extensions-token-step_id"></a>**`step_id`** (string): Issue action identifier.
- <a id="contract-extensions-token-family"></a>**`family`** (string): Declared extension family.
- <a id="contract-extensions-token-status"></a>**`status`** (string): `issued` requires a completed non-null issue result and accepted host custody; `issued_uncustodied` retains a completed non-null result without accepted custody; `null` records native null; `unavailable` records a no-call reason; `invalid` records an inconsistent completed result. Missing publication becomes `not_reached` only with supported boundary evidence, otherwise `unresolved`.
- <a id="contract-extensions-token-token_length"></a>**`token_length`** (integer?): Length available from the issue slot's extension publication, when present.
- <a id="contract-extensions-token-last_use_step_id"></a>**`last_use_step_id`** (string?): Final declared transfer using this token, or the issue itself when no transfer is declared.

<a id="contract-extensions-token-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Token resource](#contract-extensions-token) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. [Evidence details](CONTRACT.md#contract-extensions-token-support-details).

<a id="contract-extensions-delivery"></a>
### Delivery resource

Record `delivery`: `PWRunnerDeliveryRecord`.

- <a id="contract-extensions-delivery-delivery_ref"></a>**`delivery_ref`** (string): Declared delivery identifier.
- <a id="contract-extensions-delivery-token_ref"></a>**`token_ref`** (string): Token selected for delivery.
- <a id="contract-extensions-delivery-source_actor_id"></a>**`source_actor_id`** (string): Token owner and transfer source.
- <a id="contract-extensions-delivery-recipient_actor_id"></a>**`recipient_actor_id`** (string): Actor assigned the delivery.
- <a id="contract-extensions-delivery-step_id"></a>**`step_id`** (string): Transfer action identifier.
- <a id="contract-extensions-delivery-status"></a>**`status`** (string): Host acknowledgement when a transfer observation exists; otherwise the completed slot's unavailable reason or `unrequested`. Missing publication becomes `not_reached` only with supported boundary evidence, otherwise `unresolved`.
- <a id="contract-extensions-delivery-delivered_length"></a>**`delivered_length`** (integer?): Host custody length only when the acknowledgement is delivered.
- <a id="contract-extensions-delivery-equality"></a>**`equality`** (string?): Host equality comparison when a transfer observation exists.
- <a id="contract-extensions-delivery-last_use_step_id"></a>**`last_use_step_id`** (string?): Last declared consume using this delivery, or its transfer action when no consume is declared.

<a id="contract-extensions-delivery-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Delivery resource](#contract-extensions-delivery) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. [Evidence details](CONTRACT.md#contract-extensions-delivery-support-details).

<a id="contract-extensions-handle"></a>
### Handle resource

Record `handle`: `PWRunnerHandleRecord`.

- <a id="contract-extensions-handle-handle_ref"></a>**`handle_ref`** (string): Declared handle identifier.
- <a id="contract-extensions-handle-delivery_ref"></a>**`delivery_ref`** (string): Delivery consumed to produce this candidate.
- <a id="contract-extensions-handle-actor_id"></a>**`actor_id`** (string): Consuming actor and handle owner.
- <a id="contract-extensions-handle-step_id"></a>**`step_id`** (string): Consume action identifier.
- <a id="contract-extensions-handle-status"></a>**`status`** (string): `produced` requires a completed native result other than -1; `consume_failed` records completed -1; `unavailable` records a no-call reason; `invalid` records inconsistent completed evidence. Missing publication becomes `not_reached` only with supported boundary evidence, otherwise `unresolved`.
- <a id="contract-extensions-handle-native_handle"></a>**`native_handle`** (integer?): Candidate signed handle only when status is produced.
- <a id="contract-extensions-handle-raw_equal_handles"></a>**`raw_equal_handles`** (array of string): Other declared handle references in the same actor whose slot has an equal raw native result. Equality relates raw numbers; declarations retain distinct reference identity.
- <a id="contract-extensions-handle-release_step_id"></a>**`release_step_id`** (string?): Declared release action for this handle, or null/absence when no release was declared.
- <a id="contract-extensions-handle-release_attempted"></a>**`release_attempted`** (boolean): Whether the declared release action has an observed native call-boundary marker.

<a id="contract-extensions-handle-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Handle resource](#contract-extensions-handle) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. [Evidence details](CONTRACT.md#contract-extensions-handle-support-details).
<!-- END GENERATED CONTRACT extensions -->

## Read controller findings

These are recipient checks and supported assessments over admitted evidence. Keep original observations beside findings, and follow the specified withholding scope. A finished outer result can coexist with these findings.

<!-- BEGIN GENERATED CONTRACT diagnostics -->
<a id="contract-diagnostics"></a>
## Controller findings and assessments

The controller retains the admitted host reply and publishes its own
assessment under `data.runner_sandbox_diagnostics`. Each finding has the
scope of the check that produced it. The outer result, a worker's ending,
phase order, native operation and reporting-failure form have separate
conditions.

<a id="contract-diagnostics-execution"></a>
### Execution diagnostics

Record `diagnostics` locations: `envelope.data.runner_sandbox_diagnostics`.

- <a id="contract-diagnostics-execution-process_disposition"></a>**`process_disposition`** (string): The controller's disposition projection. An ordinary worker supplies its validated lifecycle result. `no_worker` means this projection had no worker subprocess record to assess. Admitted vocabulary: closed; displayed list: exhaustive: `"no_worker"`, `"clean_exit"`, `"nonzero_exit"`, `"signaled"`, `"conflicting"`, `"unconfirmed"`, `"unrecognized"`, `"withheld"`, `"per_actor"`.
- <a id="contract-diagnostics-execution-termination_cause"></a>**`termination_cause`** (string ∪ null): A controller attribution selected from the validated lifecycle chain. Actor-form top-level diagnostics begin with null because causes belong to the actor entries.
- <a id="contract-diagnostics-execution-stop_reason"></a>**`stop_reason`** (string ∪ null): Supported ordinary-worker stop observation when its answer is one of `sentinel_deadline`, `done`, `child_reaped`, `wait_error`, `policy_write_error` or `policy_transfer_deadline`; otherwise null. Actor stop reasons belong to their actor entries.
- <a id="contract-diagnostics-execution-disposition_integrity"></a>**`disposition_integrity`** (string ∪ null): `valid` means the applicable controller checks for this projection passed; `invalid` means they produced a finding. Null means there was no worker projection to validate. When at least one actor has a worker projection, actor aggregation is valid when every actor projection is valid or has null integrity; it becomes invalid when any actor projection is invalid. With no worker projections, aggregate integrity remains null. A host's supported conflict can accompany valid integrity: the controller has checked the conflict's own evidence.
- <a id="contract-diagnostics-execution-disposition_issues"></a>**`disposition_issues`** (array of [Integrity finding](#contract-diagnostics-issue)): Controller findings at this scope, followed or preceded according to the producing check order by copied host conflict records where applicable. Actor-local findings remain in the actor entry.
- <a id="contract-diagnostics-execution-actors"></a>**`actors`** (array of [One actor's diagnostics](#contract-diagnostics-actor)?): Present for `execution_form: "actors"`, in the host's actor order. Each entry is derived from that actor's subprocess and its actions selected through the phase plan.

<a id="contract-diagnostics-execution-geometry"></a>
#### Decoded response collection bounds

[Controller](CONTRACT.md#contract-identity-definitions-controller) checks at decoded response-context admission after delivery, capture and public identity admission. Entry: cli run, runner verify. Recipient: caller, report reader. Reports: run envelope, runner verify. Binding `p`: entry in `reply.phases`. Binding `a`: entry in `reply.actors`. Applies when present(`reply`).

These bounds apply to every structurally decoded reply reaching this gate, including preparation and reporting-failure replies. Counts use the retained rows before semantic association.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-geometry-plan"></a>Phase and action tables | Requires (implies(`reply.execution_form` = `"actors"`, count(`reply.phases`) ≤ `16 items` (`actor_phases`) ) and implies((absent(`reply.execution_form`) or (present(`reply.execution_form`) and `reply.execution_form` ≠ `"actors"`)), count(`reply.phases`) ≤ `8 items` (`phase_count`) ) and count(`reply.steps`) ≤ `256 items` (`probe_steps`) and implies(present(`reply.extension_events`), count(`reply.extension_events`) ≤ (`256 items` (`probe_steps`) − count(`reply.steps`))) and sum_over(`p`, count(`reply.phases[p].action_ids`)) ≤ `256 items` (`probe_steps`) ). |
| <a id="contract-diagnostics-execution-geometry-actors_transfers"></a>Actor and transfer tables | Requires (implies(present(`reply.actors`), count(`reply.actors`) ≤ `8 items` (`actors`) ) and implies(present(`reply.transfers`), count(`reply.transfers`) ≤ `64 items` (`actor_deliveries`) )). |
| <a id="contract-diagnostics-execution-geometry-resources"></a>Resource tables | Applies when present(`reply.resources`). Requires (count(`reply.resources.tokens`) ≤ `32 items` (`actor_issues`) and count(`reply.resources.deliveries`) ≤ `64 items` (`actor_deliveries`) and count(`reply.resources.handles`) ≤ `64 items` (`actor_handles`) ). |
| <a id="contract-diagnostics-execution-geometry-equal_handles"></a>Equal-handle references | Binding `h`: entry in `reply.resources.handles`. For each `h`. Applies when present(`reply.resources`). Requires count(`reply.resources.handles[h].raw_equal_handles`) ≤ (`64 items` (`actor_handles`) − `1`). |
| <a id="contract-diagnostics-execution-geometry-validator"></a>Validator collection tables | Binding `s`: entry in `reply.steps`. Association restriction for `s`: (`reply.steps[s].phase_id` = `reply.phases[p].phase_id` and `reply.steps[s].sandbox_check.missing_reason` ≠ `"query_not_requested"`). For each `p`. Applies when present(`reply.phases[p].validator_subprocess`). An absent missing_reason is included. |
| <a id="contract-diagnostics-execution-geometry-validator-expected"></a>Validator collection tables › Expected identifiers | Requires implies(present(`reply.phases[p].validator_subprocess.expected_step_ids`), count(`reply.phases[p].validator_subprocess.expected_step_ids`) ≤ `256 items` (`probe_steps`) ). |
| <a id="contract-diagnostics-execution-geometry-validator-records"></a>Validator collection tables › Retained validator records | Applies when present(`reply.phases[p].validator_subprocess.records`). Requires (implies(matches(`s`) = `0`, count(`reply.phases[p].validator_subprocess.records`) ≤ `2 items` (`validator_records_per_query`) ) and implies(matches(`s`) > `0`, count(`reply.phases[p].validator_subprocess.records`) ≤ (matches(`s`) × `2 items` (`validator_records_per_query`)))). |
| <a id="contract-diagnostics-execution-geometry-validator-issues"></a>Validator collection tables › Association issue allowance | Applies when present(`reply.phases[p].validator_subprocess.association_issues`). Requires (implies(present(`reply.phases[p].validator_subprocess.records`), count(`reply.phases[p].validator_subprocess.association_issues`) ≤ ((matches(`s`) + count(`reply.phases[p].validator_subprocess.records`)) + `1`)) and implies(absent(`reply.phases[p].validator_subprocess.records`), count(`reply.phases[p].validator_subprocess.association_issues`) ≤ (matches(`s`) + `1`))). |
| <a id="contract-diagnostics-execution-geometry-equipment"></a>Equipment tables | Requires (implies(present(`reply.equipment_bindings`), count(`reply.equipment_bindings`) ≤ `4 items` (`equipment_static_bindings`) ) and implies(present(`reply.equipment_entitlements`), count(`reply.equipment_entitlements`) ≤ `12 items` (`equipment_entitlement_records`) )). |
| <a id="contract-diagnostics-execution-geometry-authority"></a>Authority scope tables | Applies when present(`reply.authority_setup`). Requires (count(`reply.authority_setup.workers`) ≤ `8 items` (`actors`) and count(`reply.authority_setup.host.regions`) ≤ `8 items` (`actors`) and count(`reply.authority_setup.host.custody`) ≤ `32 items` (`actor_issues`) ). |
| <a id="contract-diagnostics-execution-geometry-host_scope"></a>Host run authority scope | Applies when present(`reply.authority_setup`). Requires (count(`reply.authority_setup.host.run.operations`) ≤ `4` and count(`reply.authority_setup.host.run.ownership`) ≤ `5` and implies(present(`reply.authority_setup.host.run.integrity_errors`), count(`reply.authority_setup.host.run.integrity_errors`) ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-worker_scopes"></a>Worker authority scopes | Binding `w`: entry in `reply.authority_setup.workers`. For each `w`. Applies when present(`reply.authority_setup`). Requires (count(`reply.authority_setup.workers[w].operations`) ≤ `16 items` (`authority_setup_cells`) and count(`reply.authority_setup.workers[w].ownership`) ≤ `5` and implies(present(`reply.authority_setup.workers[w].integrity_errors`), count(`reply.authority_setup.workers[w].integrity_errors`) ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-region_scopes"></a>Host region authority scopes | Binding `r`: entry in `reply.authority_setup.host.regions`. For each `r`. Applies when present(`reply.authority_setup`). Requires (count(`reply.authority_setup.host.regions[r].operations`) ≤ `16 items` (`authority_setup_cells`) and count(`reply.authority_setup.host.regions[r].ownership`) ≤ `5` and implies(present(`reply.authority_setup.host.regions[r].integrity_errors`), count(`reply.authority_setup.host.regions[r].integrity_errors`) ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-custody_scopes"></a>Host custody authority scopes | Binding `c`: entry in `reply.authority_setup.host.custody`. For each `c`. Applies when present(`reply.authority_setup`). Requires (count(`reply.authority_setup.host.custody[c].operations`) ≤ `4` and count(`reply.authority_setup.host.custody[c].ownership`) ≤ `5` and implies(present(`reply.authority_setup.host.custody[c].integrity_errors`), count(`reply.authority_setup.host.custody[c].integrity_errors`) ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-visits"></a>Actor visits | For each `a`. Applies when present(`reply.actors`). Requires count(`reply.actors[a].visits`) ≤ `16 items` (`actor_phases`) . |
| <a id="contract-diagnostics-execution-geometry-actor_equipment"></a>Actor equipment observations | For each `a`. Applies when (present(`reply.actors`) and present(`reply.actors[a].equipment`)). Requires (count(`reply.actors[a].equipment.required_entitlements`) ≤ `64 items` (`actor_required_entitlements`) and implies(present(`reply.actors[a].equipment.missing_requirements`), count(`reply.actors[a].equipment.missing_requirements`) ≤ `64 items` (`actor_required_entitlements`) ) and count(`reply.actors[a].equipment.execution.native_observations`) ≤ `4`). |
| <a id="contract-diagnostics-execution-geometry-ordinary_lifecycle"></a>Ordinary worker disposition | Binding `d`: entry in `reply.runner_subprocess.disposition.steps`. Binding `i`: entry in `reply.runner_subprocess.disposition.issues`. Applies when (present(`reply.runner_subprocess`) and present(`reply.runner_subprocess.disposition`)). |
| <a id="contract-diagnostics-execution-geometry-ordinary_lifecycle-rows"></a>Ordinary worker disposition › Disposition rows | Requires (count(`reply.runner_subprocess.disposition.steps`) ≤ `256 items` (`probe_steps`) and count(`reply.runner_subprocess.disposition.issues`) ≤ (`1` + (`2` × `256 items` (`probe_steps`)))). |
| <a id="contract-diagnostics-execution-geometry-ordinary_lifecycle-run_references"></a>Ordinary worker disposition › Run claim references | Requires (implies(present(`reply.runner_subprocess.disposition.questions.final_status`), implies(present(`reply.runner_subprocess.disposition.questions.final_status.basis`), count(`reply.runner_subprocess.disposition.questions.final_status.basis`) ≤ `14`)) and implies(present(`reply.runner_subprocess.disposition.questions.stop_reason`), implies(present(`reply.runner_subprocess.disposition.questions.stop_reason.basis`), count(`reply.runner_subprocess.disposition.questions.stop_reason.basis`) ≤ `14`)) and implies(present(`reply.runner_subprocess.disposition.questions.cleanup_trigger`), implies(present(`reply.runner_subprocess.disposition.questions.cleanup_trigger.basis`), count(`reply.runner_subprocess.disposition.questions.cleanup_trigger.basis`) ≤ `14`)) and implies(present(`reply.runner_subprocess.disposition.questions.grace_end`), implies(present(`reply.runner_subprocess.disposition.questions.grace_end.basis`), count(`reply.runner_subprocess.disposition.questions.grace_end.basis`) ≤ `14`)) and implies(present(`reply.runner_subprocess.disposition.questions.kill_request_and_result`), implies(present(`reply.runner_subprocess.disposition.questions.kill_request_and_result.basis`), count(`reply.runner_subprocess.disposition.questions.kill_request_and_result.basis`) ≤ `14`)) and implies(present(`reply.runner_subprocess.disposition.questions.collection_basis`), implies(present(`reply.runner_subprocess.disposition.questions.collection_basis.basis`), count(`reply.runner_subprocess.disposition.questions.collection_basis.basis`) ≤ `14`)) and implies(present(`reply.runner_subprocess.disposition.questions.progress_association`), implies(present(`reply.runner_subprocess.disposition.questions.progress_association.basis`), count(`reply.runner_subprocess.disposition.questions.progress_association.basis`) ≤ `14`))). |
| <a id="contract-diagnostics-execution-geometry-ordinary_lifecycle-step_references"></a>Ordinary worker disposition › Step claim references | For each `d`. Requires (implies(present(`reply.runner_subprocess.disposition.steps[d].questions.step_boundary_reached`), implies(present(`reply.runner_subprocess.disposition.steps[d].questions.step_boundary_reached.basis`), count(`reply.runner_subprocess.disposition.steps[d].questions.step_boundary_reached.basis`) ≤ `16`)) and implies(present(`reply.runner_subprocess.disposition.steps[d].questions.step_result_published`), implies(present(`reply.runner_subprocess.disposition.steps[d].questions.step_result_published.basis`), count(`reply.runner_subprocess.disposition.steps[d].questions.step_result_published.basis`) ≤ `16`)) and implies(present(`reply.runner_subprocess.disposition.steps[d].questions.step_requested_operation_applicability`), implies(present(`reply.runner_subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis`), count(`reply.runner_subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis`) ≤ `16`))). |
| <a id="contract-diagnostics-execution-geometry-ordinary_lifecycle-issue_references"></a>Ordinary worker disposition › Conflict observation references | For each `i`. Requires (implies(present(`reply.runner_subprocess.disposition.issues[i].step_index`), count(`reply.runner_subprocess.disposition.issues[i].observations`) ≤ `16`) and implies(absent(`reply.runner_subprocess.disposition.issues[i].step_index`), count(`reply.runner_subprocess.disposition.issues[i].observations`) ≤ `14`)). |
| <a id="contract-diagnostics-execution-geometry-actor_lifecycle"></a>Actor worker disposition | Binding `d`: entry in `reply.actors[a].subprocess.disposition.steps`. Binding `i`: entry in `reply.actors[a].subprocess.disposition.issues`. For each `a`. Applies when (present(`reply.actors`) and present(`reply.actors[a].subprocess`) and present(`reply.actors[a].subprocess.disposition`)). |
| <a id="contract-diagnostics-execution-geometry-actor_lifecycle-rows"></a>Actor worker disposition › Disposition rows | Requires (count(`reply.actors[a].subprocess.disposition.steps`) ≤ `256 items` (`probe_steps`) and count(`reply.actors[a].subprocess.disposition.issues`) ≤ (`1` + (`2` × `256 items` (`probe_steps`)))). |
| <a id="contract-diagnostics-execution-geometry-actor_lifecycle-run_references"></a>Actor worker disposition › Run claim references | Requires (implies(present(`reply.actors[a].subprocess.disposition.questions.final_status`), implies(present(`reply.actors[a].subprocess.disposition.questions.final_status.basis`), count(`reply.actors[a].subprocess.disposition.questions.final_status.basis`) ≤ `14`)) and implies(present(`reply.actors[a].subprocess.disposition.questions.stop_reason`), implies(present(`reply.actors[a].subprocess.disposition.questions.stop_reason.basis`), count(`reply.actors[a].subprocess.disposition.questions.stop_reason.basis`) ≤ `14`)) and implies(present(`reply.actors[a].subprocess.disposition.questions.cleanup_trigger`), implies(present(`reply.actors[a].subprocess.disposition.questions.cleanup_trigger.basis`), count(`reply.actors[a].subprocess.disposition.questions.cleanup_trigger.basis`) ≤ `14`)) and implies(present(`reply.actors[a].subprocess.disposition.questions.grace_end`), implies(present(`reply.actors[a].subprocess.disposition.questions.grace_end.basis`), count(`reply.actors[a].subprocess.disposition.questions.grace_end.basis`) ≤ `14`)) and implies(present(`reply.actors[a].subprocess.disposition.questions.kill_request_and_result`), implies(present(`reply.actors[a].subprocess.disposition.questions.kill_request_and_result.basis`), count(`reply.actors[a].subprocess.disposition.questions.kill_request_and_result.basis`) ≤ `14`)) and implies(present(`reply.actors[a].subprocess.disposition.questions.collection_basis`), implies(present(`reply.actors[a].subprocess.disposition.questions.collection_basis.basis`), count(`reply.actors[a].subprocess.disposition.questions.collection_basis.basis`) ≤ `14`)) and implies(present(`reply.actors[a].subprocess.disposition.questions.progress_association`), implies(present(`reply.actors[a].subprocess.disposition.questions.progress_association.basis`), count(`reply.actors[a].subprocess.disposition.questions.progress_association.basis`) ≤ `14`))). |
| <a id="contract-diagnostics-execution-geometry-actor_lifecycle-step_references"></a>Actor worker disposition › Step claim references | For each `a`, `d`. Requires (implies(present(`reply.actors[a].subprocess.disposition.steps[d].questions.step_boundary_reached`), implies(present(`reply.actors[a].subprocess.disposition.steps[d].questions.step_boundary_reached.basis`), count(`reply.actors[a].subprocess.disposition.steps[d].questions.step_boundary_reached.basis`) ≤ `16`)) and implies(present(`reply.actors[a].subprocess.disposition.steps[d].questions.step_result_published`), implies(present(`reply.actors[a].subprocess.disposition.steps[d].questions.step_result_published.basis`), count(`reply.actors[a].subprocess.disposition.steps[d].questions.step_result_published.basis`) ≤ `16`)) and implies(present(`reply.actors[a].subprocess.disposition.steps[d].questions.step_requested_operation_applicability`), implies(present(`reply.actors[a].subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis`), count(`reply.actors[a].subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis`) ≤ `16`))). |
| <a id="contract-diagnostics-execution-geometry-actor_lifecycle-issue_references"></a>Actor worker disposition › Conflict observation references | For each `a`, `i`. Requires (implies(present(`reply.actors[a].subprocess.disposition.issues[i].step_index`), count(`reply.actors[a].subprocess.disposition.issues[i].observations`) ≤ `16`) and implies(absent(`reply.actors[a].subprocess.disposition.issues[i].step_index`), count(`reply.actors[a].subprocess.disposition.issues[i].observations`) ≤ `14`)). |
| <a id="contract-diagnostics-execution-geometry-step_copies"></a>Attempt lifecycle copies | Binding `s`: entry in `reply.steps`. For each `s`. Applies when present(`reply.steps[s].attempt.lifecycle`). Requires (implies(present(`reply.steps[s].attempt.lifecycle.boundary.basis`), count(`reply.steps[s].attempt.lifecycle.boundary.basis`) ≤ `16`) and implies(present(`reply.steps[s].attempt.lifecycle.result.basis`), count(`reply.steps[s].attempt.lifecycle.result.basis`) ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-extension_copies"></a>Extension lifecycle copies | Binding `e`: entry in `reply.extension_events`. For each `e`. Applies when (present(`reply.extension_events`) and present(`reply.extension_events[e].lifecycle`)). Requires (implies(present(`reply.extension_events[e].lifecycle.boundary.basis`), count(`reply.extension_events[e].lifecycle.boundary.basis`) ≤ `16`) and implies(present(`reply.extension_events[e].lifecycle.result.basis`), count(`reply.extension_events[e].lifecycle.result.basis`) ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-failed"></a>Failed collection bound | On failure, [set_value(`result.normalized_outcome`, `"malformed_runner_response"`), set_value(`result.ok`, `false`), set_value(`result.exit_code`, `1`), retain_records(`reply`)]. |
| <a id="contract-diagnostics-execution-geometry-run_refusal"></a>Run assessment after refusal | Entry: cli run. On failure, set_value(`envelope.data.runner_sandbox_diagnostics`, `null`). |
| <a id="contract-diagnostics-execution-geometry-verify_refusal"></a>Verification completion after refusal | Entry: runner verify. On failure, [set_value(`runner_verify.normalized_outcome`, `"malformed_runner_response"`), set_value(`runner_verify.runner_pid`, `null`)]. |

<a id="contract-diagnostics-execution-geometry-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Decoded response collection bounds](#contract-diagnostics-execution-geometry) and its descendants.** Collection bounds precede semantic joins and profile-context checking on run and verification admission; their refusal retains the decoded reply. Context: Read every geometry guard, both public call paths and the named constructed-control bodies. Evidence limit: The controls assert selected excess tables, reference lists, an accepted boundary and unchanged raw records. The remaining enumerated collection bounds and verification-specific projection are supported by their source branches. [Evidence details](CONTRACT.md#contract-diagnostics-execution-geometry-support-details).

<a id="contract-diagnostics-execution-admit"></a>
#### Admit the response before assessment

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at client delivery, public reply identity and bounded response context. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Uses [Decoded response collection bounds](#contract-diagnostics-execution-geometry). Check request-delivery failure and client capture status, then exact reply identity, response geometry and compiled-profile context before execution diagnostics.

A missing or foreign producer identity follows its own transport/identity
refusal. The geometry guard bounds collections before semantic joins.
The compiled-profile guard checks its status and producer/stage context,
including actor captures and reporting-failure replies. These are
preconditions for the execution-assessment path described here.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-admit-context_refusal"></a>Decoded response-context refusal | [set_value(`envelope.result.normalized_outcome`, `"malformed_runner_response"`), set_value(`envelope.result.ok`, `false`), set_value(`envelope.result.exit_code`, `1`), set_value(`envelope.data.runner_sandbox_diagnostics`, `null`), retain_records(`reply`)]. The controller's response geometry or compiled-profile context check rejects a structurally decoded host reply. The controller returns the selected exit status with the decoded host reply still available in the envelope. |

<a id="contract-diagnostics-execution-project"></a>
#### Project one worker or aggregate actors

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at typed worker lifecycle interpretation after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Run the worker lifecycle validation against its native records, assigned actions and reporting form. Project a validated ending by the ending-mapping and stop-reason rules, then publish the validated host conflicts at that worker scope.

For the actor form, the controller computes each worker's projection
separately. It then sets the top-level disposition to `per_actor` when any
entry differs from `no_worker`, and aggregates the actor integrity values.

The two concrete scopes below bind each source subprocess to its own output
fields. Their lifecycle prerequisites are the actual helper check in each
invocation, including retained reporting-failure replies.

<a id="contract-diagnostics-execution-actor_rows"></a>
#### Actor projection rows

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at worker projection after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Binding `a`: entry in `reply.actors`. Binding `d`: entry in `envelope.data.runner_sandbox_diagnostics.actors`. Association restriction for `d`: `d` = `a`. Applies when `reply.execution_form` = `"actors"`.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-actor_rows-coverage"></a>Positional coverage | Requires (present(`envelope.data.runner_sandbox_diagnostics.actors`) and implies(present(`reply.actors`), count(`envelope.data.runner_sandbox_diagnostics.actors`) = count(`reply.actors`)) and implies(absent(`reply.actors`), count(`envelope.data.runner_sandbox_diagnostics.actors`) = `0`)). |
| <a id="contract-diagnostics-execution-actor_rows-identity"></a>Copied actor identity | For each `a`, `d`. Requires `envelope.data.runner_sandbox_diagnostics.actors[d].actor_id` = `reply.actors[a].actor_id`. Its label is copied even when that actor has no subprocess. Duplicate labels retain their separate positions and remain subject to the reply-wide association checks. |

<a id="contract-diagnostics-execution-ordinary"></a>
#### Ordinary worker projection

Actor: [Controller](CONTRACT.md#contract-identity-definitions-controller). Boundary: worker projection after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Applies when ((absent(`reply.execution_form`) or (present(`reply.execution_form`) and `reply.execution_form` ≠ `"actors"`)) and present(`reply.runner_subprocess`)).

The source is `reply.runner_subprocess`; the output is the ordinary
execution diagnostic record, before reply-wide findings are appended.

<a id="contract-diagnostics-execution-ordinary-lifecycle_check"></a>
##### Worker lifecycle validation

[Controller](CONTRACT.md#contract-identity-definitions-controller) checks at one worker lifecycle validation before projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Applies when ((absent(`reply.execution_form`) or (present(`reply.execution_form`) and `reply.execution_form` ≠ `"actors"`)) and present(`reply.runner_subprocess`)). For reply.runner_subprocess and its assigned actions under the carried reporting form, the controller's lifecycle validation returns no failed-check findings, before validated host conflicts are copied.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-ordinary-lifecycle_check-local_failure"></a>Local lifecycle findings | On failure, [set_value(`envelope.data.runner_sandbox_diagnostics.process_disposition`, `"withheld"`), set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"unknown"`), set_value(`envelope.data.runner_sandbox_diagnostics.disposition_integrity`, `"invalid"`), set_value(`envelope.data.runner_sandbox_diagnostics.stop_reason`, `null`)]. |

<a id="contract-diagnostics-execution-ordinary-mapping"></a>
##### Ending mapping

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Select the first matching case in the listed order. Applies when (((absent(`reply.execution_form`) or (present(`reply.execution_form`) and `reply.execution_form` ≠ `"actors"`)) and present(`reply.runner_subprocess`)) and (present(`reply.runner_subprocess.disposition`) and present(`reply.runner_subprocess.disposition.questions.final_status`))). Requires [Worker lifecycle validation](#contract-diagnostics-execution-ordinary-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-execution-ordinary-mapping-clean"></a>1. Clean exit | (`reply.runner_subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.final_status.answer` = `"exit_code"` and present(`reply.runner_subprocess.disposition.questions.final_status.value`) and is_variant(`reply.runner_subprocess.disposition.questions.final_status.value`, `"Integer"`) and variant(`reply.runner_subprocess.disposition.questions.final_status.value`, `"Integer"`) = `0`) | [set_value(`envelope.data.runner_sandbox_diagnostics.process_disposition`, `"clean_exit"`), set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `null`)]. |
| <a id="contract-diagnostics-execution-ordinary-mapping-nonzero"></a>2. Other exit status | (`reply.runner_subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.final_status.answer` = `"exit_code"`) | [set_value(`envelope.data.runner_sandbox_diagnostics.process_disposition`, `"nonzero_exit"`), set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"unknown"`)]. |
| <a id="contract-diagnostics-execution-ordinary-mapping-signal"></a>3. Signaled ending | (`reply.runner_subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.final_status.answer` = `"signal"`) | [set_value(`envelope.data.runner_sandbox_diagnostics.process_disposition`, `"signaled"`), set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"unknown"`)]. |
| <a id="contract-diagnostics-execution-ordinary-mapping-conflict"></a>4. Supported conflict | `reply.runner_subprocess.disposition.questions.final_status.state` = `"conflicting"` | [set_value(`envelope.data.runner_sandbox_diagnostics.process_disposition`, `"conflicting"`), set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"unknown"`)]. |
| <a id="contract-diagnostics-execution-ordinary-mapping-unconfirmed"></a>5. Unresolved or inapplicable ending | `reply.runner_subprocess.disposition.questions.final_status.state` ∈ [`"unresolved"`, `"inapplicable"`] | [set_value(`envelope.data.runner_sandbox_diagnostics.process_disposition`, `"unconfirmed"`), set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"unknown"`)]. |
| <a id="contract-diagnostics-execution-ordinary-mapping-other"></a>6. Other admitted ending | `true` | [set_value(`envelope.data.runner_sandbox_diagnostics.process_disposition`, `"unrecognized"`), set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"unknown"`)]. Lifecycle validation has already checked the integer exit value and supported-conflict evidence. |

<a id="contract-diagnostics-execution-ordinary-stop"></a>
##### Supported stop reason

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Select the first matching case in the listed order. Applies when (((absent(`reply.execution_form`) or (present(`reply.execution_form`) and `reply.execution_form` ≠ `"actors"`)) and present(`reply.runner_subprocess`)) and present(`reply.runner_subprocess.disposition`)). Follows [Host-cleanup attribution](#contract-diagnostics-execution-ordinary-cause). Requires [Worker lifecycle validation](#contract-diagnostics-execution-ordinary-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-execution-ordinary-stop-recognized"></a>1. Recognized supported stop | (present(`reply.runner_subprocess.disposition.questions.stop_reason`) and `reply.runner_subprocess.disposition.questions.stop_reason.state` = `"supported"` and present(`reply.runner_subprocess.disposition.questions.stop_reason.answer`) and `reply.runner_subprocess.disposition.questions.stop_reason.answer` ∈ [`"sentinel_deadline"`, `"done"`, `"child_reaped"`, `"wait_error"`, `"policy_write_error"`, `"policy_transfer_deadline"`]) | [set_value(`envelope.data.runner_sandbox_diagnostics.stop_reason`, `reply.runner_subprocess.disposition.questions.stop_reason.answer`), set_value(`envelope.data.runner_sandbox_diagnostics.disposition_integrity`, `"valid"`)]. |
| <a id="contract-diagnostics-execution-ordinary-stop-absent"></a>2. No supported recognized stop | `true` | [set_value(`envelope.data.runner_sandbox_diagnostics.stop_reason`, `null`), set_value(`envelope.data.runner_sandbox_diagnostics.disposition_integrity`, `"valid"`)]. |

<a id="contract-diagnostics-execution-ordinary-cause_chain"></a>
##### Carried host-cleanup chain

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-ordinary-cause_chain-facts"></a>Required claims and native request result | Requires (present(`reply.runner_subprocess.disposition`) and present(`reply.runner_subprocess.disposition.questions.final_status`) and `reply.runner_subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.final_status.answer` = `"signal"` and present(`reply.runner_subprocess.disposition.questions.final_status.value`) and is_variant(`reply.runner_subprocess.disposition.questions.final_status.value`, `"Integer"`) and present(`reply.runner_subprocess.disposition.questions.cleanup_trigger`) and `reply.runner_subprocess.disposition.questions.cleanup_trigger.state` = `"supported"` and present(`reply.runner_subprocess.disposition.questions.grace_end`) and `reply.runner_subprocess.disposition.questions.grace_end.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.grace_end.answer` = `"exhausted"` and present(`reply.runner_subprocess.disposition.questions.kill_request_and_result`) and `reply.runner_subprocess.disposition.questions.kill_request_and_result.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.kill_request_and_result.answer` = `"requested"` and present(`reply.runner_subprocess.disposition.questions.kill_request_and_result.value`) and is_variant(`reply.runner_subprocess.disposition.questions.kill_request_and_result.value`, `"Request"`) and `variant(reply.runner_subprocess.disposition.questions.kill_request_and_result.value, 'Request').rc` = `0` and `variant(reply.runner_subprocess.disposition.questions.kill_request_and_result.value, 'Request').signal` = variant(`reply.runner_subprocess.disposition.questions.final_status.value`, `"Integer"`)). |

<a id="contract-diagnostics-execution-ordinary-cause"></a>
##### Host-cleanup attribution

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Select the first matching case in the listed order. Applies when (((absent(`reply.execution_form`) or (present(`reply.execution_form`) and `reply.execution_form` ≠ `"actors"`)) and present(`reply.runner_subprocess`)) and (present(`reply.runner_subprocess.disposition`) and present(`reply.runner_subprocess.disposition.questions.final_status`) and `reply.runner_subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.final_status.answer` = `"signal"`)). Follows [Ending mapping](#contract-diagnostics-execution-ordinary-mapping). Requires [Worker lifecycle validation](#contract-diagnostics-execution-ordinary-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-execution-ordinary-cause-deadline_expiry"></a>1. Deadline expiry | ([Required claims and native request result](#contract-diagnostics-execution-ordinary-cause_chain-facts) and `reply.runner_subprocess.disposition.questions.cleanup_trigger.answer` = `"deadline_expiry"`) | set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"host_sentinel_deadline"`). |
| <a id="contract-diagnostics-execution-ordinary-cause-completion"></a>2. Completion | ([Required claims and native request result](#contract-diagnostics-execution-ordinary-cause_chain-facts) and `reply.runner_subprocess.disposition.questions.cleanup_trigger.answer` = `"completion"`) | set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"host_exit_grace_exhausted"`). |
| <a id="contract-diagnostics-execution-ordinary-cause-poll_wait_error"></a>3. Poll wait error | ([Required claims and native request result](#contract-diagnostics-execution-ordinary-cause_chain-facts) and `reply.runner_subprocess.disposition.questions.cleanup_trigger.answer` = `"poll_wait_error"`) | set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"host_cleanup_after_wait_error"`). |
| <a id="contract-diagnostics-execution-ordinary-cause-policy_transfer_error"></a>4. Policy transfer error | ([Required claims and native request result](#contract-diagnostics-execution-ordinary-cause_chain-facts) and `reply.runner_subprocess.disposition.questions.cleanup_trigger.answer` = `"policy_transfer_error"`) | set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"host_cleanup_after_transfer_error"`). |
| <a id="contract-diagnostics-execution-ordinary-cause-policy_transfer_timeout"></a>5. Policy transfer timeout | ([Required claims and native request result](#contract-diagnostics-execution-ordinary-cause_chain-facts) and `reply.runner_subprocess.disposition.questions.cleanup_trigger.answer` = `"policy_transfer_timeout"`) | set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"host_cleanup_after_transfer_timeout"`). |
| <a id="contract-diagnostics-execution-ordinary-cause-unknown"></a>6. No eligible recognized cleanup cause | `true` | set_value(`envelope.data.runner_sandbox_diagnostics.termination_cause`, `"unknown"`). The request result, exhausted grace and owned final status are independent observations in this chain. A successful signal request supplies its own request result; attribution requires the other carried claims and the preceding lifecycle validation. |

<a id="contract-diagnostics-execution-ordinary-host_conflicts"></a>
##### Copy validated host conflicts

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at worker projection after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Binding `i`: entry in `reply.runner_subprocess.disposition.issues`. Binding `j`: entry in `envelope.data.runner_sandbox_diagnostics.disposition_issues`. Association restriction for `j`: `j` = `i`. Applies when (((absent(`reply.execution_form`) or (present(`reply.execution_form`) and `reply.execution_form` ≠ `"actors"`)) and present(`reply.runner_subprocess`)) and present(`reply.runner_subprocess.disposition`)). Follows [Supported stop reason](#contract-diagnostics-execution-ordinary-stop). Requires [Worker lifecycle validation](#contract-diagnostics-execution-ordinary-lifecycle_check).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-ordinary-host_conflicts-coverage"></a>Copy cardinality | Requires count(`envelope.data.runner_sandbox_diagnostics.disposition_issues`) = count(`reply.runner_subprocess.disposition.issues`). |
| <a id="contract-diagnostics-execution-ordinary-host_conflicts-copy"></a>Copy each conflict's fields | For each `i`, `j`. [set_value(`envelope.data.runner_sandbox_diagnostics.disposition_issues[j].kind`, `reply.runner_subprocess.disposition.issues[i].kind`), set_value(`envelope.data.runner_sandbox_diagnostics.disposition_issues[j].detail`, `reply.runner_subprocess.disposition.issues[i].detail`), set_value(`envelope.data.runner_sandbox_diagnostics.disposition_issues[j].subject_path`, `null`), set_value(`envelope.data.runner_sandbox_diagnostics.disposition_issues[j].rule`, `reply.runner_subprocess.disposition.issues[i].rule`), set_value(`envelope.data.runner_sandbox_diagnostics.disposition_issues[j].question`, `reply.runner_subprocess.disposition.issues[i].question`), set_value(`envelope.data.runner_sandbox_diagnostics.disposition_issues[j].step_index`, `reply.runner_subprocess.disposition.issues[i].step_index`), set_value(`envelope.data.runner_sandbox_diagnostics.disposition_issues[j].observations`, `reply.runner_subprocess.disposition.issues[i].observations`)]. |

<a id="contract-diagnostics-execution-reply_checks"></a>
#### Apply reply-wide findings

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at typed reply relationship checks after worker projections. Entry: cli run. Recipient: report reader. Reports: execution diagnostics. [set_value(`diagnostics.process_disposition`, `"withheld"`), set_value(`diagnostics.termination_cause`, `"unknown"`), set_value(`diagnostics.disposition_integrity`, `"invalid"`), retain_records(`reply`), retain_assessments(`diagnostics.actors`)]. Follows [Project one worker or aggregate actors](#contract-diagnostics-execution-project). Uses [Reply-wide withholding scope](#contract-diagnostics-issue-subject-withholding_scope). One or more applicable reply-wide checks finds an invalid relationship.

The controller appends these findings to top-level `disposition_issues`.
It preserves the actor entries, an ordinary stop reason already derived,
and all host fields including step comparisons and claimed gate outcomes.
Those retained assertions can therefore appear beside the controller's
finding about them.

The reply-wide withholding scope defines the attribution limits of the retained
actor-row projections.

<a id="contract-diagnostics-execution-outer_result"></a>
#### Findings beside the completion result

Uses [Select the public result](#contract-envelope-data-select).

The envelope's result-selection rule governs completion. Individual failed
attempts and controller integrity findings remain visible beside that result.
A reply-wide withheld disposition can therefore accompany an outer successful
result.

<a id="contract-diagnostics-execution-families"></a>
#### Check families and applicability

Uses [Reply](CONTRACT.md#contract-identity-definitions-reply).

| Check family | Applicability and checked relationship | Finding scope |
| --- | --- | --- |
| Lifecycle claims | Each worker subprocess: required claims, state/basis references, owned final status, cleanup facts, progress association, slot count/order, action identity, lifecycle copies and supported conflicts. | That worker's projection; ordinary projection or one actor entry. |
| Phase and query evidence | Ordinary semantic reply: phase IDs/order, action partition, collection state, validator ownership and raw-record association, protocol violations, comparison vocabulary and the complete `query_first` chain. | Reply-wide. |
| Policy delivery/read evidence | Ordinary semantic reply with a worker policy-read receipt: bounded counts, host expected-count agreement, length-refusal detail and consistency with later worker observations. | Reply-wide. |
| Native operation observations | Ordinary semantic reply: each fresh-read, fresh-write and exec observation's applicable fields and native relationships. | Reply-wide. |
| Actor association | Ordinary semantic actor reply: actor indexes/IDs, launch/subprocess PID, visits, phase owner, event owner and matching transfer source. | Reply-wide. |
| Actor setup, equipment, application, termination and custody | Ordinary semantic reply: execution-form applicability and the actor record relationships defined by those surfaces. | Reply-wide. |
| Reporting-failure form | A reply carrying reporting_failure: degraded outcome/rc/error, origin/diagnostic/original outcome, removed comparisons and the retention-specific record form. | Reply-wide. |

The reporting-failure branch checks its degradation form while retaining the
assembled records. Worker lifecycle projections still run separately,
with their comparison-limitation requirement waived when the comparison
has been removed by degradation. The retained host records remain
available for inspection at their own observation boundaries.

<a id="contract-diagnostics-execution-vocabulary"></a>
#### Closed claim states and open answers

Lifecycle claim states are `supported`, `conflicting`, `unresolved` and
`inapplicable`. A supported claim needs an answer and sufficient resolving
basis; unresolved and inapplicable need a reason. A conflicting claim
needs the matching indexed conflict record and native observations.
Another state produces an invalid-claim finding.

Some answers and summaries are open. For example, an unfamiliar
applicability answer or lifecycle summary is retained, while a known
summary is checked against the canonical lifecycle. A supported unfamiliar
final-status answer that passes the other claim checks projects as
`unrecognized`. This differs from an unknown closed claim state, which
withholds the worker projection.

<a id="contract-diagnostics-execution-vocabulary-vocabulary_choice"></a>
##### Unconfirmed vocabulary

For ordinary and actor workers, the controller uses `unconfirmed` for both
unresolved and inapplicable final status. The retained host claim state and
reason preserve that distinction for consumers that need it.

<a id="contract-diagnostics-execution-scope_example"></a>
#### Scope example

A typed actor reply can carry a transfer naming an invalid source actor,
while another actor retains a valid clean-exit lifecycle. The controller
then publishes top-level `withheld` and an actor-evidence finding beside
that actor's `clean_exit`. If the admitted host summary is `finished`,
the outer result still reports `ok: true` and exit 0. The three values
answer the reply relationship, individual ending and host completion
questions respectively. The actor projection describes its retained row;
it does not certify associations rejected by a reply-wide finding.

<a id="contract-diagnostics-execution-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Execution diagnostics](#contract-diagnostics-execution) and its descendants.** Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches. Context: Typed controller implementation and the named constructed tests were read. Evidence limit: Actor/native family entry points and the complete gate checks were read; their detailed operation predicates have separate source owners. The scope example combines separately inspected projection and outer-result controls. [Evidence details](CONTRACT.md#contract-diagnostics-execution-support-details).

<a id="contract-diagnostics-execution-reader_evidence"></a>
#### Reader judgments

Uses [Reader applicability](#contract-actor_evidence-actor-reader_scope).

Host reporting validation, controller semantic admission and canonical-JSON
consumption interpret the same typed records at their stated scopes. Worker
lifecycle assessment remains a separate judgment over the retained native
account and its projection. A reporting failure can retain observations that
produce a lifecycle finding while satisfying the degradation form.

These readers do not promise identical admission domains. The general Python
consumer's outer-result check assumes replies within the controller's
collection-capacity domain and does not reproduce that gate. Its consistency
finding on a controller refusal for capacity alone does not establish a
violation of the controller's result-selection rule.

<a id="contract-diagnostics-execution-reader_evidence-support"></a>
**Support: [executed](CONTRACT.md#contract-support-grades) for [Reader judgments](#contract-diagnostics-execution-reader_evidence).** Preparation, identifier, membership, application precedence and degradation cases check their own expected judgments and retained consequences across the actual readers. Context: Whole canonical runner-unit case passed with zero recorded system sleep. Swift judgments over 142 typed frames were retained before encoding; exact-one Rust replay carried 143 frames including the real writer-cap fallback through envelopes, then independent Python readers completed all rows and seven JSON-only controls. Evidence limit: The corpus uses constructed records and independently expected interpretations. Eleven application-positive pairs, degradation admission, the exact contradictory-worker D1 finding and retained actor projections have separate assertions. JSON-only normalization has its own domain. Native occurrence of each constructed context has separate observation owners. [Evidence details](CONTRACT.md#contract-diagnostics-execution-reader_evidence-support-details).

<a id="contract-diagnostics-execution-reader_evidence-classifier_generation"></a>
##### Independent semantic classifiers

Host, controller and test readers retain separately authored semantic
classifiers. Agreement is checked against stated definitions and independent
expectations within each reader's scope. No generated shared classifier or
universal equivalence is promised.

<a id="contract-diagnostics-actor"></a>
### One actor's diagnostics

Record `actor_diagnostics`: `rust.ActorExecutionDiagnostics`.

- <a id="contract-diagnostics-actor-actor_id"></a>**`actor_id`** (string ∪ null): The host actor label copied into an actor-form diagnostic entry. The underlying projection helper begins with null; actor assembly supplies the label even when that actor has no subprocess record.
- <a id="contract-diagnostics-actor-process_disposition"></a>**`process_disposition`** (string): The actor's own worker projection, chosen by the actor-worker mapping below after its lifecycle checks pass. Local findings yield `withheld`; a missing subprocess record yields `no_worker`.
- <a id="contract-diagnostics-actor-termination_cause"></a>**`termination_cause`** (string ∪ null): Null for `clean_exit` or `no_worker`, otherwise `unknown` unless the validated host-cleanup chain supplies a named cause below.
- <a id="contract-diagnostics-actor-stop_reason"></a>**`stop_reason`** (string ∪ null): The actor worker's supported stop reason from the recognized set listed for execution diagnostics. Null when no supported recognized answer was projected, including when local lifecycle validation failed.
- <a id="contract-diagnostics-actor-disposition_integrity"></a>**`disposition_integrity`** (string ∪ null): `valid` when this worker's lifecycle checks passed, `invalid` when they produced a finding, and null when its subprocess record is absent. A reply-wide finding preserves this actor-local value.
- <a id="contract-diagnostics-actor-disposition_issues"></a>**`disposition_issues`** (array of [Integrity finding](#contract-diagnostics-issue)): Findings from this actor's lifecycle validation, or copied validated host conflicts after successful validation. Reply-wide actor-association or equipment findings appear in the execution-level issue list.

<a id="contract-diagnostics-actor-projection"></a>
#### Actor worker projections

Actor: [Controller](CONTRACT.md#contract-identity-definitions-controller). Boundary: worker projection after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Binding `a`: entry in `reply.actors`. Binding `d`: entry in `envelope.data.runner_sandbox_diagnostics.actors`. Association restriction for `d`: `d` = `a`. For each `a`, `d`. Applies when (`reply.execution_form` = `"actors"` and present(`reply.actors`) and present(`reply.actors[a].subprocess`)).

This scope addresses each existing subprocess, including
its degraded reporting form, before later reply-wide findings.

<a id="contract-diagnostics-actor-projection-lifecycle_check"></a>
##### Worker lifecycle validation

[Controller](CONTRACT.md#contract-identity-definitions-controller) checks at one worker lifecycle validation before projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. For each `a`, `d`. Applies when (`reply.execution_form` = `"actors"` and present(`reply.actors`) and present(`reply.actors[a].subprocess`)). For reply.actors[a].subprocess and its assigned actions under the carried reporting form, the controller's lifecycle validation returns no failed-check findings, before validated host conflicts are copied.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-actor-projection-lifecycle_check-local_failure"></a>Local lifecycle findings | On failure, [set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition`, `"withheld"`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"unknown"`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].disposition_integrity`, `"invalid"`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].stop_reason`, `null`)]. |

<a id="contract-diagnostics-actor-projection-mapping"></a>
##### Ending mapping

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. For each `a`, `d`. Select the first matching case in the listed order. Applies when ((`reply.execution_form` = `"actors"` and present(`reply.actors`) and present(`reply.actors[a].subprocess`)) and (present(`reply.actors[a].subprocess.disposition`) and present(`reply.actors[a].subprocess.disposition.questions.final_status`))). Requires [Worker lifecycle validation](#contract-diagnostics-actor-projection-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-actor-projection-mapping-clean"></a>1. Clean exit | (`reply.actors[a].subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.final_status.answer` = `"exit_code"` and present(`reply.actors[a].subprocess.disposition.questions.final_status.value`) and is_variant(`reply.actors[a].subprocess.disposition.questions.final_status.value`, `"Integer"`) and variant(`reply.actors[a].subprocess.disposition.questions.final_status.value`, `"Integer"`) = `0`) | [set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition`, `"clean_exit"`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `null`)]. |
| <a id="contract-diagnostics-actor-projection-mapping-nonzero"></a>2. Other exit status | (`reply.actors[a].subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.final_status.answer` = `"exit_code"`) | [set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition`, `"nonzero_exit"`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"unknown"`)]. |
| <a id="contract-diagnostics-actor-projection-mapping-signal"></a>3. Signaled ending | (`reply.actors[a].subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.final_status.answer` = `"signal"`) | [set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition`, `"signaled"`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"unknown"`)]. |
| <a id="contract-diagnostics-actor-projection-mapping-conflict"></a>4. Supported conflict | `reply.actors[a].subprocess.disposition.questions.final_status.state` = `"conflicting"` | [set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition`, `"conflicting"`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"unknown"`)]. |
| <a id="contract-diagnostics-actor-projection-mapping-unconfirmed"></a>5. Unresolved or inapplicable ending | `reply.actors[a].subprocess.disposition.questions.final_status.state` ∈ [`"unresolved"`, `"inapplicable"`] | [set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition`, `"unconfirmed"`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"unknown"`)]. |
| <a id="contract-diagnostics-actor-projection-mapping-other"></a>6. Other admitted ending | `true` | [set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition`, `"unrecognized"`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"unknown"`)]. Lifecycle validation has already checked the integer exit value and supported-conflict evidence. |

<a id="contract-diagnostics-actor-projection-stop"></a>
##### Supported stop reason

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. For each `a`, `d`. Select the first matching case in the listed order. Applies when ((`reply.execution_form` = `"actors"` and present(`reply.actors`) and present(`reply.actors[a].subprocess`)) and present(`reply.actors[a].subprocess.disposition`)). Follows [Host-cleanup attribution](#contract-diagnostics-actor-projection-cause). Requires [Worker lifecycle validation](#contract-diagnostics-actor-projection-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-actor-projection-stop-recognized"></a>1. Recognized supported stop | (present(`reply.actors[a].subprocess.disposition.questions.stop_reason`) and `reply.actors[a].subprocess.disposition.questions.stop_reason.state` = `"supported"` and present(`reply.actors[a].subprocess.disposition.questions.stop_reason.answer`) and `reply.actors[a].subprocess.disposition.questions.stop_reason.answer` ∈ [`"sentinel_deadline"`, `"done"`, `"child_reaped"`, `"wait_error"`, `"policy_write_error"`, `"policy_transfer_deadline"`]) | [set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].stop_reason`, `reply.actors[a].subprocess.disposition.questions.stop_reason.answer`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].disposition_integrity`, `"valid"`)]. |
| <a id="contract-diagnostics-actor-projection-stop-absent"></a>2. No supported recognized stop | `true` | [set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].stop_reason`, `null`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].disposition_integrity`, `"valid"`)]. |

<a id="contract-diagnostics-actor-projection-cause_chain"></a>
##### Carried host-cleanup chain

For each `a`, `d`.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-actor-projection-cause_chain-facts"></a>Required claims and native request result | Requires (present(`reply.actors[a].subprocess.disposition`) and present(`reply.actors[a].subprocess.disposition.questions.final_status`) and `reply.actors[a].subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.final_status.answer` = `"signal"` and present(`reply.actors[a].subprocess.disposition.questions.final_status.value`) and is_variant(`reply.actors[a].subprocess.disposition.questions.final_status.value`, `"Integer"`) and present(`reply.actors[a].subprocess.disposition.questions.cleanup_trigger`) and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.state` = `"supported"` and present(`reply.actors[a].subprocess.disposition.questions.grace_end`) and `reply.actors[a].subprocess.disposition.questions.grace_end.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.grace_end.answer` = `"exhausted"` and present(`reply.actors[a].subprocess.disposition.questions.kill_request_and_result`) and `reply.actors[a].subprocess.disposition.questions.kill_request_and_result.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.kill_request_and_result.answer` = `"requested"` and present(`reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value`) and is_variant(`reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value`, `"Request"`) and `variant(reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value, 'Request').rc` = `0` and `variant(reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value, 'Request').signal` = variant(`reply.actors[a].subprocess.disposition.questions.final_status.value`, `"Integer"`)). |

<a id="contract-diagnostics-actor-projection-cause"></a>
##### Host-cleanup attribution

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. For each `a`, `d`. Select the first matching case in the listed order. Applies when ((`reply.execution_form` = `"actors"` and present(`reply.actors`) and present(`reply.actors[a].subprocess`)) and (present(`reply.actors[a].subprocess.disposition`) and present(`reply.actors[a].subprocess.disposition.questions.final_status`) and `reply.actors[a].subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.final_status.answer` = `"signal"`)). Follows [Ending mapping](#contract-diagnostics-actor-projection-mapping). Requires [Worker lifecycle validation](#contract-diagnostics-actor-projection-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-actor-projection-cause-deadline_expiry"></a>1. Deadline expiry | ([Required claims and native request result](#contract-diagnostics-actor-projection-cause_chain-facts) and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer` = `"deadline_expiry"`) | set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"host_sentinel_deadline"`). |
| <a id="contract-diagnostics-actor-projection-cause-completion"></a>2. Completion | ([Required claims and native request result](#contract-diagnostics-actor-projection-cause_chain-facts) and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer` = `"completion"`) | set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"host_exit_grace_exhausted"`). |
| <a id="contract-diagnostics-actor-projection-cause-poll_wait_error"></a>3. Poll wait error | ([Required claims and native request result](#contract-diagnostics-actor-projection-cause_chain-facts) and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer` = `"poll_wait_error"`) | set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"host_cleanup_after_wait_error"`). |
| <a id="contract-diagnostics-actor-projection-cause-policy_transfer_error"></a>4. Policy transfer error | ([Required claims and native request result](#contract-diagnostics-actor-projection-cause_chain-facts) and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer` = `"policy_transfer_error"`) | set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"host_cleanup_after_transfer_error"`). |
| <a id="contract-diagnostics-actor-projection-cause-policy_transfer_timeout"></a>5. Policy transfer timeout | ([Required claims and native request result](#contract-diagnostics-actor-projection-cause_chain-facts) and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer` = `"policy_transfer_timeout"`) | set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"host_cleanup_after_transfer_timeout"`). |
| <a id="contract-diagnostics-actor-projection-cause-unknown"></a>6. No eligible recognized cleanup cause | `true` | set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `"unknown"`). The request result, exhausted grace and owned final status are independent observations in this chain. A successful signal request supplies its own request result; attribution requires the other carried claims and the preceding lifecycle validation. The actor scheduler never records `sentinel_deadline`, so no actor reply selects the deadline case. An actor stopped for an arrival, completion or setup timeout, a protocol violation, a withheld release or a failed setup keeps the scheduler's reason as its trigger. Its cause stays `unknown` even when the request result, exhausted grace and final status are all carried; read them in that actor's subprocess record. |

<a id="contract-diagnostics-actor-projection-host_conflicts"></a>
##### Copy validated host conflicts

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at worker projection after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Binding `i`: entry in `reply.actors[a].subprocess.disposition.issues`. Binding `j`: entry in `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues`. Association restriction for `j`: `j` = `i`. For each `a`, `d`. Applies when ((`reply.execution_form` = `"actors"` and present(`reply.actors`) and present(`reply.actors[a].subprocess`)) and present(`reply.actors[a].subprocess.disposition`)). Follows [Supported stop reason](#contract-diagnostics-actor-projection-stop). Requires [Worker lifecycle validation](#contract-diagnostics-actor-projection-lifecycle_check).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-actor-projection-host_conflicts-coverage"></a>Copy cardinality | Requires count(`envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues`) = count(`reply.actors[a].subprocess.disposition.issues`). |
| <a id="contract-diagnostics-actor-projection-host_conflicts-copy"></a>Copy each conflict's fields | For each `a`, `d`, `i`, `j`. [set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].kind`, `reply.actors[a].subprocess.disposition.issues[i].kind`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].detail`, `reply.actors[a].subprocess.disposition.issues[i].detail`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].subject_path`, `null`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].rule`, `reply.actors[a].subprocess.disposition.issues[i].rule`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].question`, `reply.actors[a].subprocess.disposition.issues[i].question`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].step_index`, `reply.actors[a].subprocess.disposition.issues[i].step_index`), set_value(`envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].observations`, `reply.actors[a].subprocess.disposition.issues[i].observations`)]. |

<a id="contract-diagnostics-actor-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [One actor's diagnostics](#contract-diagnostics-actor) and its descendants.** The mapping follows admitted final-status claims; named host causes require the supported cleanup/request/ending chain. An actor killed after its exhausted exit grace at schedule end carries the completion trigger and the completion cause; one that ended on its own signal projects unknown. Context: Full projection and lifecycle validation read; constructed cleanup and scope controls and the two live actor endings read. Evidence limit: The read cleanup test covers completion, deadline, wait-error and future-trigger cases. The live actor rows cover the completion cause and a self-signalled ending under test-seam controls. Transfer-error and transfer-timeout causes were read in source; no execution is credited. [Evidence details](CONTRACT.md#contract-diagnostics-actor-support-details).

<a id="contract-diagnostics-issue"></a>
### Integrity finding

Record `integrity_issue`: `rust.IntegrityIssue`.

- <a id="contract-diagnostics-issue-kind"></a>**`kind`** (string): Category supplied by the controller check or copied from a host conflict. Admitted vocabulary: open; displayed list: illustrative: `"missing_record"`, `"malformed_record"`, `"invalid_claim"`, `"unresolved_reference"`, `"phase_collection"`, `"ordering"`, `"policy_read"`, `"fresh_read"`, `"fresh_write"`, `"exec_observation"`, `"actor_evidence"`, `"reporting_failure"`, `"conflict"`. Unfamiliar values: An unfamiliar category remains a finding with its carried detail and scope; interpreting its specific condition requires that producer's definition.
- <a id="contract-diagnostics-issue-detail"></a>**`detail`** (string): Human-readable explanation of the failed relationship or copied host conflict. Some controller details embed a step label or position; other actor and gate findings carry a general explanation.
- <a id="contract-diagnostics-issue-subject_path"></a>**`subject_path`** (array of string?): Optional location of the inspected assertion within `data.runner_result`. The path is an ordered list of object keys and canonical zero-based decimal array positions. An empty path names the whole host result; a present null value remains an addressable target. For example, `["phases","2","termination_gate"]` names the third phase's carried gate, even when phase labels are duplicated or invalid. The controller supplies this field for owned-reap, phase-activation and termination-gate findings. Its association identifies the inspected record; projection and retention effects follow the producing check's scope. Other controller findings and copied host conflicts omit this field.
- <a id="contract-diagnostics-issue-rule"></a>**`rule`** (string?): Host conflict rule copied from the retained disposition issue, such as D1 for a final-status conflict or D5 for the supported step conflicts. Controller-created findings currently omit this field.
- <a id="contract-diagnostics-issue-question"></a>**`question`** (string?): Host question associated with a copied conflict. Controller-created findings currently omit this field even when a detail names the question.
- <a id="contract-diagnostics-issue-step_index"></a>**`step_index`** (integer?): Worker-local step index copied from a host conflict when it has step scope. A copied run-level conflict and controller-created findings omit it.
- <a id="contract-diagnostics-issue-observations"></a>**`observations`** (array of string?): Host observation-reference list copied from a validated conflict. Controller-created findings currently omit this field.

<a id="contract-diagnostics-issue-retain"></a>
#### Retain observation and finding separately

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at integrity finding construction. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. retain_records(`reply`). Construct controller findings from the failed check's kind and detail, attaching subject_path for the owned-reap, phase-activation and termination-gate checks. Publish each finding and copied validated host conflict at its producing validation scope and in the producing order.

<a id="contract-diagnostics-issue-subject"></a>
#### Finding association and effect

Uses [subject_path](#contract-diagnostics-issue-subject_path), [Apply reply-wide findings](#contract-diagnostics-execution-reply_checks), [Project one worker or aggregate actors](#contract-diagnostics-execution-project).

A subject path associates the finding with the retained assertion that its
check inspected. A gate's source and dependent records remain operands of
that check. Reply-wide findings withhold the aggregate projection and retain
the separately computed actor projections. Worker-local findings affect
that worker's projection.

<a id="contract-diagnostics-issue-subject-withholding_scope"></a>
##### Reply-wide withholding scope

Reply-wide findings withhold the aggregate and retain separately computed
actor-row projections. Each projection describes the carried subprocess and
action records selected through carried labels and IDs. It does not override
findings against identity, launch association or action membership, or
independently establish attribution to the requested actor. Worker-local
lifecycle findings still withhold that worker's projection.

<a id="contract-diagnostics-issue-subject-gate_execution"></a>
**Support: [executed](CONTRACT.md#contract-support-grades) for [Finding association and effect](#contract-diagnostics-issue-subject).** The constructed check retains both equal-label gates by positions 2 and 6, then checks owned-reap, activation and dependent-gate subjects with exact finding details/order and unchanged input records. Context: The named control passed in the completed zero-sleep unit/rust.unit case; its assertions inspect the findings returned by the production gate checker. Evidence limit: Execution covers the constructed owned-reap, activation and selected gate cases. Remaining predicate-location assignments retain their source support. Reference resolution and action-wide withholding choices have separate owners. [Evidence details](CONTRACT.md#contract-diagnostics-issue-subject-gate_execution-details).

<a id="contract-diagnostics-issue-subject-reference_execution"></a>
**Support: [executed](CONTRACT.md#contract-support-grades) for [Finding association and effect](#contract-diagnostics-issue-subject).** Forty-two retained controls cover optional/root/object/scalar/null targets, canonical array positions, malformed or unresolved paths, aggregate and actor issue locations, version gating and accumulated independent faults; 12 accept and 30 refuse. Context: The completed blackbox_e2e/checker_controls case passed with zero recorded system sleep. Each constructed input and its exact findings remain in consumer_subject_*.json and *.errors.json. Evidence limit: These controls establish reference reading and unchanged carried documents. Product predicate-to-subject selection is checked by the gate and full-reply corpus owners; the withholding definition separately governs projection scope. [Evidence details](CONTRACT.md#contract-diagnostics-issue-subject-reference_execution-details).

<a id="contract-diagnostics-issue-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Integrity finding](#contract-diagnostics-issue) and its descendants.** Gate-family findings carry locations in the retained reply while preserving existing predicates, detail, order and projection scope. Copied host issues preserve their own metadata. Context: Constructors, projection copy, actor gate checks and native validator dispatch read. Evidence limit: Locations identify inspected retained records. Existing worker-local and reply-wide projection rules govern the findings independently. [Evidence details](CONTRACT.md#contract-diagnostics-issue-support-details).
<!-- END GENERATED CONTRACT diagnostics -->

## Read the dossier

Enter through `data.specimen` for original and selected policy accounts, imports, selected binaries and available provenance. The dossier can preserve partial observations after an early refusal. Separate filesystem reads do not create a frozen filesystem snapshot.

<!-- BEGIN GENERATED CONTRACT dossier -->
<a id="contract-dossier"></a>
## Specimen dossier

The controller carries `data.specimen` on every `kind: "run"` envelope. Its policy hashes identify the held parsed source selected for delivery; its import records identify controller file reads; its runner and binary records describe selection and on-disk observations made before invocation. Native compilation, application and execution have their own reports.

<a id="contract-dossier-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Specimen dossier](#contract-dossier) and its descendants.** Declarations and collection branches establish field provenance, augmentation states, literal import closure and role-specific comparisons. Unit controls assert unavailable/partial states and comparisons against synthetic manifest baselines. Context: Read the cited producer/receiver declarations and branches; check citations identify the assertions read. Evidence limit: These read controls establish controller calculations and selected-file comparisons. A signed run with a changed request file, native compiler import parity and contemporaneous executing-image identity need separate observations. [Evidence details](CONTRACT.md#contract-dossier-support-details).

<a id="contract-dossier-collection"></a>
### Collection boundaries

<a id="contract-dossier-collection-held"></a>
#### Hold the selected request

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at request preparation before runner-client invocation and fallback compile. Entry: cli run. Recipient: cli caller, runner client, compiler helper. Reports: specimen dossier. Uses [Request](CONTRACT.md#contract-identity-definitions-request), [Byte observation](CONTRACT.md#contract-identity-definitions-bytes). A request has been parsed and controller policy changes have been resolved in memory. Serialize the held selected request once and use those bytes for client delivery and whole-request fallback compilation. Derive source hashes from its decoded UTF-8 sbpl_source string and retain the dossier even when later preparation or invocation fails.

The original path is a locator. JSON whitespace, escape spelling and subsequent edits to that file have no role in the held source hash. Actor fallback checks serialize the held resolved policy objects separately in request order. A later helper import scan can observe different import-file bytes because those files are independently opened.

<a id="contract-dossier-collection-scan"></a>
#### Scan literal imports

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at selected policy source and local import files before invocation. Entry: cli run. Recipient: cli caller. Reports: specimen dossier. The selected policy has string source within the <!-- span limits.helper_source.binary -->4 MiB<!-- /span --> source bound. Scan literal import forms, resolve absolute names as given and relative names under /System/Library/Sandbox/Profiles then /usr/share/sandbox, and record observed reads within depth 8 and count 64. Mark unresolved names, nonliteral forms, cycles, decoding failures and bound hits as incomplete.

Names retain their spelling, including a `.sb` suffix when supplied. Resolution deduplicates canonical paths and unresolved names. A file is opened once with nonblocking open, checked as regular through that descriptor, and read for both hashing and recursive scanning. Records sort by resolved path, then unresolved name. The closure hash is SHA-256 of selected source UTF-8 bytes, byte `0x1f`, then sorted `resolved_path + " " + sha256` lines joined with LF for records having both values. This identifies the scanned material even when the scan is incomplete.

<a id="contract-dossier-collection-compare"></a>
#### Compare selected files

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at selected runner/helper paths and embedded evidence manifest. Entry: cli run. Recipient: cli caller. Reports: specimen dossier. Uses [Classify the retained digest pair](#contract-dossier-binary-classify). Runner selection supplies paths and the app evidence manifest supplies role baselines where available. For a shipped path already described by its unique typed manifest entry, emit a null binary record. For another selected file, attempt its hash and retain the role baseline, available digest and independent error facts. After a dossier-only collection failure or hash mismatch, continue preparation and invocation subject to the separate selection and admission results.

A role baseline must be the unique entry at the expected path and kind with a 64-digit hexadecimal SHA-256. `match` means selected on-disk bytes matched that baseline at this read. A null role record refers to the shipped manifest description; ordinary collection does not rehash that shipped file. Worker/validator override strings must be absolute to be read; NUL-containing or over-<!-- span limits.test_override_path.value -->1,023<!-- /span -->-byte overrides are neither echoed nor opened.

<a id="contract-dossier-collection-held_example"></a>
#### Held-file example

If a caller changes the input JSON after the controller has parsed it, the client and fallback compiler still receive the controller’s held serialization. An import file changed between dossier collection and fallback compilation may produce different import observations. Compare the source hash and the separately reported closures at their named boundaries.

<a id="contract-dossier-collection-native_gap"></a>
#### Held input and file observation scope

The controller resolves and serializes the request once, then delivers that held text to the selected client and applicable helper calls. The dossier scanner and selected-file hashes describe their own reads. Literal import completeness belongs to the scanner convention; actor live equipment supplies its separate process association. Ordinary selected-file hashes remain file observations at collection time.

<a id="contract-dossier-collection-native_gap-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Held input and file observation scope](#contract-dossier-collection-native_gap).** Held request delivery, import reads and selected-file comparison have distinct boundaries. Context: Static review of the cited producer and assertion branches. Evidence limit: The file-replacement control uses controlled client/helper callbacks and exact independent held inputs; selected-file hashes do not supply an ordinary executing-image association. [Evidence details](CONTRACT.md#contract-dossier-collection-native_gap-disposition_support-details).

<a id="contract-dossier-specimen"></a>
### Run dossier

Record `specimen`: `rust.Specimen`. Uses [Specimen](CONTRACT.md#contract-identity-definitions-specimen).

- <a id="contract-dossier-specimen-request_path"></a>**`request_path`** (string ∪ null): Request-file path reported by the controller when available; null when preparation did not establish one.
- <a id="contract-dossier-specimen-policy"></a>**`policy`** ([Policy dossier](#contract-dossier-policy)): Legacy-form policy dossier. In actor form, the actor entries carry their policy observations and this slot is not applicable.
- <a id="contract-dossier-specimen-host"></a>**`host`** ([Controller host context](#contract-dossier-host)): Controller-collected operating-system context; each failed sysctl read remains null.
- <a id="contract-dossier-specimen-runner_provenance"></a>**`runner_provenance`** ([Selected runner provenance](#contract-dossier-runner) ∪ null): Selected runner metadata when selection succeeded; null when no target was established. These facts precede invocation.
- <a id="contract-dossier-specimen-app_provenance"></a>**`app_provenance`** ([App provenance](#contract-dossier-app) ∪ null): Parsed app evidence-manifest provenance when available; null when its read or supported-schema parse failed.
- <a id="contract-dossier-specimen-binaries"></a>**`binaries`** ([Selected binary observations](#contract-dossier-binaries)): Role-by-role selected-file observations; the meaning of a null role is defined beside that role.
- <a id="contract-dossier-specimen-actors"></a>**`actors`** (array of [Actor policy dossier](#contract-dossier-actor)?): Actor-form policy dossiers in request order; omitted for the legacy form.

<a id="contract-dossier-actor"></a>
### Actor policy dossier

Record `actor`: `rust.ActorDossier`.

- <a id="contract-dossier-actor-actor_id"></a>**`actor_id`** (string ∪ null): Actor identifier copied if the request value is a string; otherwise null. This copy precedes actor admission.
- <a id="contract-dossier-actor-mode"></a>**`mode`** (string ∪ null): Actor mode copied if it is a string; otherwise null. Unapplied actors receive a not-applicable policy dossier.
- <a id="contract-dossier-actor-policy"></a>**`policy`** ([Policy dossier](#contract-dossier-policy)): Policy augmentation and import observations for this actor. Missing or malformed policy objects produce not-applicable observations.

<a id="contract-dossier-policy"></a>
### Policy dossier

Record `policy`: `rust.PolicyDossier`.

- <a id="contract-dossier-policy-augmentation"></a>**`augmentation`** ([Augmentation observation](#contract-dossier-augmentation)): Controller policy-selection outcome and hashes of source strings that existed at that boundary.
- <a id="contract-dossier-policy-imports"></a>**`imports`** ([Import scan](#contract-dossier-imports)): Literal import observations for the source selected for invocation, or the reason that scan was unavailable.

<a id="contract-dossier-augmentation"></a>
### Augmentation observation

Record `augmentation`: `rust.Augmentation`.

- <a id="contract-dossier-augmentation-status"></a>**`status`** (string): `not_requested` retains unchanged source hashes; `applied` records selected augmentation output; `failed` records refusal; `not_applicable` identifies a policy slot with no applicable source preparation.
- <a id="contract-dossier-augmentation-applied"></a>**`applied`** (array of string): Applied augmentation names in controller order.
- <a id="contract-dossier-augmentation-original_sha256"></a>**`original_sha256`** (string ∪ null): SHA-256 of pre-augmentation source string UTF-8 bytes when such a string existed; otherwise null.
- <a id="contract-dossier-augmentation-applied_sha256"></a>**`applied_sha256`** (string ∪ null): SHA-256 of the selected source string, including unchanged source for not_requested. Null for failed/not_applicable and when no source string existed.
- <a id="contract-dossier-augmentation-error"></a>**`error`** (string ∪ null): Augmentation failure text for failed; otherwise null.

<a id="contract-dossier-augmentation-relationships"></a>
#### Augmentation record relationships

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at augmentation dossier projection. Entry: cli run. Recipient: report reader. Reports: specimen dossier.

Equal optional digests on not_requested include the case where no string source existed.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-dossier-augmentation-relationships-fields"></a>Produced field relationships | Requires (implies(`augmentation.status` ∈ [`"not_requested"`, `"failed"`, `"not_applicable"`], count(`augmentation.applied`) = `0`) and implies(`augmentation.status` ∈ [`"failed"`, `"not_applicable"`], absent(`augmentation.applied_sha256`)) and implies(`augmentation.status` = `"not_requested"`, `augmentation.original_sha256` = `augmentation.applied_sha256`) and implies(`augmentation.status` = `"failed"`, present(`augmentation.error`)) and implies(`augmentation.status` ∈ [`"not_requested"`, `"applied"`, `"not_applicable"`], absent(`augmentation.error`))). |

<a id="contract-dossier-augmentation-relationships-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Augmentation record relationships](#contract-dossier-augmentation-relationships) and its descendants.** The four constructors preserve optional original/selected hashes and distinct failure/error states. [Evidence details](CONTRACT.md#contract-dossier-augmentation-relationships-support-details).

<a id="contract-dossier-imports"></a>
### Import scan

Record `imports`: `rust.Imports`.

- <a id="contract-dossier-imports-status"></a>**`status`** (string): `complete` exhausted the literal closure without a reported problem; `incomplete` retained a partial/problematic scan; `failed` could not perform the scan; `not_applicable` skipped it because source preparation did not apply.
- <a id="contract-dossier-imports-closure_sha256"></a>**`closure_sha256`** (string ∪ null): Digest of the selected source plus successfully read import path/hash pairs using the defined framing.
- <a id="contract-dossier-imports-records"></a>**`records`** (array of [One import observation](#contract-dossier-import_record)): Sorted observed import records, including unresolved and failed reads. Empty when there were no imports or no scan.
- <a id="contract-dossier-imports-cycle"></a>**`cycle`** (array of string ∪ null): First detected cycle as an ordered name chain; null when no cycle was observed.
- <a id="contract-dossier-imports-exceeded"></a>**`exceeded`** (string ∪ null): First reached traversal bound, `depth` or `count`; null when neither was recorded.
- <a id="contract-dossier-imports-failure"></a>**`failure`** (string ∪ null): First collection problem, scan setup failure or reason for a not-applicable scan; null when none was recorded.

<a id="contract-dossier-imports-scope"></a>
#### Retained scan scope

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at literal import dossier projection. Entry: cli run. Recipient: report reader. Reports: specimen dossier. Binding `r`: entry in `imports.records`. Association restriction for `r`: present(`imports.records[r].error`).

These are necessary conditions for complete. The scan also classifies nonliteral forms, an observation with no dedicated carried Boolean.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-dossier-imports-scope-fields"></a>Produced field relationships | Requires (implies(`imports.status` ∈ [`"complete"`, `"incomplete"`], present(`imports.closure_sha256`)) and implies(`imports.status` ∈ [`"failed"`, `"not_applicable"`], (absent(`imports.closure_sha256`) and count(`imports.records`) = `0` and absent(`imports.cycle`) and absent(`imports.exceeded`))) and implies(`imports.status` = `"complete"`, (absent(`imports.cycle`) and absent(`imports.exceeded`) and matches(`r`) = `0`))). |

<a id="contract-dossier-imports-scope-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Retained scan scope](#contract-dossier-imports-scope) and its descendants.** Performed complete/incomplete scans retain a closure; skipped/failed scans have no records. Complete scans have no carried cycle, exceeded bound or record errors. [Evidence details](CONTRACT.md#contract-dossier-imports-scope-support-details).

<a id="contract-dossier-import_record"></a>
### One import observation

Record `import_record`: `rust.ImportRecord`.

- <a id="contract-dossier-import_record-name"></a>**`name`** (string): Literal import name found in source, retained for successful resolution and unresolved-name diagnostics.
- <a id="contract-dossier-import_record-resolved_path"></a>**`resolved_path`** (string ∪ null): Resolved path when lookup established one; null for an unresolved name.
- <a id="contract-dossier-import_record-sha256"></a>**`sha256`** (string ∪ null): SHA-256 of bytes read from the opened regular file; null when that read failed or never occurred.
- <a id="contract-dossier-import_record-size_bytes"></a>**`size_bytes`** (integer ∪ null): File size reported by metadata on the opened descriptor, when available. The hash identifies the bytes actually read.
- <a id="contract-dossier-import_record-mtime_unix"></a>**`mtime_unix`** (integer ∪ null): Opened file’s available modification time in Unix seconds; null on unavailable conversion/read.
- <a id="contract-dossier-import_record-error"></a>**`error`** (string ∪ null): Resolution, regular-file, read, text-decoding or traversal diagnostic for this entry; null when the entry was collected without such a problem.

<a id="contract-dossier-host"></a>
### Controller host context

Record `host`: `rust.HostFacts`.

- <a id="contract-dossier-host-macos_version"></a>**`macos_version`** (string ∪ null): String read from kern.osproductversion, or null when unavailable.
- <a id="contract-dossier-host-macos_build"></a>**`macos_build`** (string ∪ null): String read from kern.osversion, or null when unavailable.
- <a id="contract-dossier-host-kernel_release"></a>**`kernel_release`** (string ∪ null): String read from kern.osrelease, or null when unavailable.
- <a id="contract-dossier-host-arch"></a>**`arch`** (string ∪ null): String read from hw.machine, or null when unavailable. This is the controller host’s hardware context.

<a id="contract-dossier-app"></a>
### App provenance

Record `app`: `rust.AppProvenance`.

- <a id="contract-dossier-app-evidence_manifest_path"></a>**`evidence_manifest_path`** (string): Path to the parsed embedded evidence manifest used by this run’s controller.
- <a id="contract-dossier-app-evidence_verify"></a>**`evidence_verify`** ([Manifest hash verification](#contract-dossier-verification) ∪ null): Manifest-declared hash verification when PW_VERIFY_EVIDENCE is exactly `1`; otherwise null.

<a id="contract-dossier-binaries"></a>
### Selected binary observations

Record `binaries`: `rust.Binaries`.

A null role records use of its shipped manifest description. If selection or a manifest baseline is unavailable, the controller emits an unavailable record with the facts it could retain. Actor equipment selection has its own records.

- <a id="contract-dossier-binaries-service"></a>**`service`** ([One selected binary](#contract-dossier-binary) ∪ null): Selected host executable comparison when it needs an individual record. Null when the shipped service is described by the manifest.
- <a id="contract-dossier-binaries-worker"></a>**`worker`** ([One selected binary](#contract-dossier-binary) ∪ null): Selected normal worker comparison, including an admitted observable override path. Null when the shipped worker is described by the manifest.
- <a id="contract-dossier-binaries-validator"></a>**`validator`** ([One selected binary](#contract-dossier-binary) ∪ null): Selected validator comparison, including an admitted observable override path. Null when the shipped validator is described by the manifest.
- <a id="contract-dossier-binaries-unentitled_worker"></a>**`unentitled_worker`** ([One selected binary](#contract-dossier-binary) ∪ null): Selected unentitled-worker comparison. Null when the shipped role is described by the manifest.

<a id="contract-dossier-binary"></a>
### One selected binary

Record `binary`: `rust.BinaryRecord`.

- <a id="contract-dossier-binary-path"></a>**`path`** (string ∪ null): Selected path when the controller may retain it; null when selection or safe override projection was unavailable.
- <a id="contract-dossier-binary-actual_sha256"></a>**`actual_sha256`** (string ∪ null): Hash of selected on-disk bytes successfully read; retained independently of baseline availability.
- <a id="contract-dossier-binary-baseline_sha256"></a>**`baseline_sha256`** (string ∪ null): Normalized SHA-256 from the shipped app manifest’s unique typed role entry; null if that baseline is unavailable.
- <a id="contract-dossier-binary-verification"></a>**`verification`** (string): `match` or `mismatch` compares the two available hashes. `unavailable` means the controller could not establish that comparison.
- <a id="contract-dossier-binary-reason"></a>**`reason`** (string ∪ null): Diagnostic explaining mismatch or unavailability; null for match.

<a id="contract-dossier-binary-classify"></a>
#### Classify the retained digest pair

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at selected binary comparison record after collection. Entry: cli run. Recipient: report reader. Reports: specimen dossier. Select the first matching case in the listed order.

This rule applies to a constructed binary record. A null shipped-role record remains outside it; matching bytes at this read do not identify an executing image.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-dossier-binary-classify-match"></a>1. Equal available digests | (present(`binary.actual_sha256`) and present(`binary.baseline_sha256`) and `binary.actual_sha256` = `binary.baseline_sha256`) | [set_value(`binary.verification`, `"match"`), set_value(`binary.reason`, `null`)]. |
| <a id="contract-dossier-binary-classify-mismatch"></a>2. Different available digests | (present(`binary.actual_sha256`) and present(`binary.baseline_sha256`)) | set_value(`binary.verification`, `"mismatch"`). |
| <a id="contract-dossier-binary-classify-unavailable"></a>3. Unavailable comparison operand | `true` | set_value(`binary.verification`, `"unavailable"`). |

<a id="contract-dossier-binary-classify-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Classify the retained digest pair](#contract-dossier-binary-classify).** Available expected/actual digests select match or mismatch; missing operands retain unavailable with the collection diagnosis. [Evidence details](CONTRACT.md#contract-dossier-binary-classify-support-details).

<a id="contract-dossier-runner"></a>
### Selected runner provenance

Record `runner`: `rust.RunnerProvenance`. Uses [Signature observation](#contract-installation-signature), [Entitlement observation](#contract-installation-entitlements).

- <a id="contract-dossier-runner-runner_kind"></a>**`runner_kind`** (string): Selected connection kind, standard or byoxpc.
- <a id="contract-dossier-runner-runner_registry_id"></a>**`runner_registry_id`** (string ∪ null): Registry ID for a selected external runner; null for a built-in target.
- <a id="contract-dossier-runner-runner_service_name"></a>**`runner_service_name`** (string): Selected XPC service name to which the controller intends to connect.
- <a id="contract-dossier-runner-runner_bundle_id"></a>**`runner_bundle_id`** (string ∪ null): Selected bundle identity when available.
- <a id="contract-dossier-runner-runner_bundle_path"></a>**`runner_bundle_path`** (string ∪ null): Selected bundle path when available; this is selection metadata.
- <a id="contract-dossier-runner-runner_executable_path"></a>**`runner_executable_path`** (string ∪ null): Selected host executable path when available.
- <a id="contract-dossier-runner-runner_signature"></a>**`runner_signature`** ([Signature observation](#contract-installation-signature) ∪ null): Recorded external-host signature readback; null when no such metadata is supplied.
- <a id="contract-dossier-runner-runner_entitlements"></a>**`runner_entitlements`** ([Entitlement observation](#contract-installation-entitlements) ∪ null): Selected host entitlement metadata from the external registry or shipped evidence manifest when available.
- <a id="contract-dossier-runner-runner_worker_signature"></a>**`runner_worker_signature`** ([Signature observation](#contract-installation-signature) ∪ null): Recorded normal-worker signature readback for the selected target when available.
- <a id="contract-dossier-runner-runner_worker_entitlements"></a>**`runner_worker_entitlements`** ([Entitlement observation](#contract-installation-entitlements) ∪ null): Recorded normal-worker entitlement metadata when available.
- <a id="contract-dossier-runner-runner_validator_signature"></a>**`runner_validator_signature`** ([Signature observation](#contract-installation-signature) ∪ null): Recorded validator signature readback when available.
- <a id="contract-dossier-runner-runner_validator_entitlements"></a>**`runner_validator_entitlements`** ([Entitlement observation](#contract-installation-entitlements) ∪ null): Recorded validator entitlement metadata when available.
- <a id="contract-dossier-runner-runner_unentitled_worker_signature"></a>**`runner_unentitled_worker_signature`** ([Signature observation](#contract-installation-signature) ∪ null): Recorded unentitled-worker signature readback when available.
- <a id="contract-dossier-runner-runner_unentitled_worker_entitlements"></a>**`runner_unentitled_worker_entitlements`** ([Entitlement observation](#contract-installation-entitlements) ∪ null): Recorded unentitled-worker entitlement metadata when available.

<a id="contract-dossier-verification"></a>
### Manifest hash verification

Record `verification`: `rust.VerifyReport`.

Each comparison concerns a file read under the app root.

- <a id="contract-dossier-verification-ok"></a>**`ok`** (boolean): True when every checked manifest entry was readable and matched its declared hash; false when mismatches contains an entry.
- <a id="contract-dossier-verification-checked"></a>**`checked`** (integer): Number of manifest entries carrying a declared hash and considered by verification, including missing/unreadable files.
- <a id="contract-dossier-verification-mismatches"></a>**`mismatches`** (array of [One verification failure](#contract-dossier-mismatch)): Entries whose file was missing, unreadable or had different bytes.
- <a id="contract-dossier-verification-manifest_path"></a>**`manifest_path`** (string): Manifest path attached to this verification.
- <a id="contract-dossier-verification-schema_version"></a>**`schema_version`** (integer): Schema version read from the supported manifest.
- <a id="contract-dossier-verification-notes"></a>**`notes`** (array of string ∪ null): Notes carried by that manifest, or null when absent.

<a id="contract-dossier-mismatch"></a>
### One verification failure

Record `mismatch`: `rust.VerifyMismatch`.

- <a id="contract-dossier-mismatch-id"></a>**`id`** (string): Manifest entry identifier for the failed comparison.
- <a id="contract-dossier-mismatch-rel_path"></a>**`rel_path`** (string): Manifest-relative file path attempted under the app root.
- <a id="contract-dossier-mismatch-expected_sha256"></a>**`expected_sha256`** (string ∪ null): Declared expected hash retained for this failure.
- <a id="contract-dossier-mismatch-actual_sha256"></a>**`actual_sha256`** (string ∪ null): Hash actually read when available; null for missing/unreadable files.
- <a id="contract-dossier-mismatch-error"></a>**`error`** (string ∪ null): Missing-file or read-error text when bytes were unavailable; null for a completed read whose actual hash differs from expected.
<!-- END GENERATED CONTRACT dossier -->

## Responses from other entry points

The following interfaces have their own operations and result meanings. They
are kept separate from specimen execution. Follow [version output](#read-version-output),
the [compiler helper](#read-the-compiler-helper), the
[direct validator](#read-the-direct-validator) or
[runner administration](#read-runner-administration) according to the command used.

## Read version output

Version reports the binary’s embedded identity and provenance. It does not invoke a host or establish that a saved specimen is admissible; use the reported identity in the [request workflow](REQUEST.md).

<!-- BEGIN GENERATED CONTRACT version -->
<a id="contract-identity-version"></a>
### Version reporting

Record `version_data`: `VersionData`.

- <a id="contract-identity-version-contract"></a>**`contract`** (string): The controller's public identity, also carried in the same envelope's `build.contract`. Uses [Exact admission identity](CONTRACT.md#contract-identity-public-contract).

<a id="contract-identity-version-emit"></a>
#### Version command

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at CLI version dispatch. Entry: version. Recipient: cli caller. Reports: version. [set_value(`version_data.contract`, [Contract](#contract-identity-build-contract)), set_value(`result.ok`, `true`), set_value(`result.exit_code`, `0`), set_value(`result.rc`, `null`), set_value(`result.normalized_outcome`, `null`), set_value(`result.errno`, `null`), set_value(`result.error`, `null`), set_value(`result.stderr`, `null`), set_value(`result.stdout`, `null`)]. Uses [Envelope](CONTRACT.md#contract-identity-definitions-envelope), [Contract](#contract-identity-build-contract). The first command argument is --version or version. Emit the version envelope with its version payload and current build context; return process exit 0 after successful rendering, or 2 when envelope rendering returns an error.

Version dispatch reports the compiled context without loading a specimen or
starting the runner client. The command takes no argument: one after it is
refused with process exit 2 and an empty standard output, before anything it
names is read, and a reason is written to standard error when that stream
accepts it.
`generated_at_unix_ms` is the producer's current
wall-clock time in milliseconds since the Unix epoch; the shared serializer
uses zero if its system time precedes that epoch.

<a id="contract-identity-version-emit-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Version command](#contract-identity-version-emit).** --version succeeds, emits kind version and result.ok true, supplies populated packaged build fields, and reports candidate-plist identity in data and build. Context: Read dispatch and serializer branches; read integration test invoking the selected controller binary and independently extracting its app plist identity. Evidence limit: Check read without execution. Alias version, exact null result fields and rendering-error exit are source-established here; the cited check exercises --version success. [Evidence details](CONTRACT.md#contract-identity-version-emit-support-details).

<a id="contract-identity-version-emit-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Version command](#contract-identity-version-emit).** The first argument alone selects version dispatch, and an argument after it is refused with exit 2 and an empty standard output. Context: Static review of the cited producer and assertion branches. Evidence limit: The alias comparison covers kind, build, result and data while allowing each invocation its own timestamp. The refusal matrix has three argument vectors. [Evidence details](CONTRACT.md#contract-identity-version-emit-disposition_support-details).
<!-- END GENERATED CONTRACT version -->

## Read the compiler helper

The helper’s envelope and data describe standalone or controller-invoked compilation. Its [request forms](REQUEST.md#standalone-compiler-helper-input) are separate from specimen execution. Compilation success alone does not establish sandbox application.

<!-- BEGIN GENERATED CONTRACT helper -->
<a id="contract-policy-check_data"></a>
### Compiler-helper data

Record `check_data` locations: `helper_envelope.data`.

- <a id="contract-policy-check_data-policy_format"></a>**`policy_format`** (string): The decoded policy format, including a refused format.
- <a id="contract-policy-check_data-policy_sha256"></a>**`policy_sha256`** (string ∪ null): SHA-256 of the admitted source's UTF-8 bytes; null when input admission failed before hashing.
- <a id="contract-policy-check_data-macos_build_version"></a>**`macos_build_version`** (string ∪ null): The host macOS build observed by the helper, or null when unavailable.
- <a id="contract-policy-check_data-params_present"></a>**`params_present`** (boolean): True when params decoded as a map, including an empty map; false for omission or null.
- <a id="contract-policy-check_data-params_count"></a>**`params_count`** (integer): Number of decoded parameter-map entries.
- <a id="contract-policy-check_data-compile"></a>**`compile`** ([Last native compile stage](#contract-policy-compile) ∪ null): The last native stage attempted and its result. Null means the helper refused the input before native setup or compilation.
- <a id="contract-policy-check_data-import_inventory"></a>**`import_inventory`** ([Literal import inventory](#contract-policy-imports) ∪ null): The helper's literal-import walk performed before native compilation. Null means admission prevented the walk; an empty records list is a performed walk with no import records.

<a id="contract-policy-check_data-run_compile"></a>
#### Inventory, compile and report

[Compiler helper](CONTRACT.md#contract-identity-definitions-helper) acts at admitted diagnostic compilation. Entry: standalone helper, controller helper stdin. Recipient: caller, report reader. Reports: helper envelope. Inventory imports, prepare native parameters when needed, then compile the admitted source. Preserve the inventory even when native compilation fails.

The helper compiles in its own process. The fallback capture reports this independent attempt alongside the transport result and any retained worker evidence.

<a id="contract-policy-check_data-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Compiler-helper data](#contract-policy-check_data) and its descendants.** The adjacent field meanings and operations follow the named implementation. [Evidence details](CONTRACT.md#contract-policy-check_data-support-details).

<a id="contract-policy-check_data-verdict"></a>
#### Select the helper verdict

[Compiler helper](CONTRACT.md#contract-identity-definitions-helper) reports at last native-stage record to helper result. Entry: standalone helper, controller helper stdin. Recipient: report reader. Reports: helper envelope. Select the first matching case in the listed order. Applies when present(`helper_envelope.data.compile`).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-policy-check_data-verdict-ok"></a>1. Successful last stage | `helper_envelope.data.compile.ok` | [set_value(`helper_envelope.result.ok`, `true`), set_value(`helper_envelope.result.exit_code`, `0`), set_value(`helper_envelope.result.normalized_outcome`, `"ok"`), set_value(`helper_envelope.result.error`, `null`)]. |
| <a id="contract-policy-check_data-verdict-compile_diagnostic"></a>2. Compile failure with a diagnostic | (`helper_envelope.data.compile.stage` = `"compile"` and present(`helper_envelope.data.compile.error`)) | [set_value(`helper_envelope.result.ok`, `false`), set_value(`helper_envelope.result.exit_code`, `1`), set_value(`helper_envelope.result.normalized_outcome`, `"compile_error"`), set_value(`helper_envelope.result.error`, `helper_envelope.data.compile.error`)]. |
| <a id="contract-policy-check_data-verdict-compile_no_diagnostic"></a>3. Compile failure without a diagnostic | `helper_envelope.data.compile.stage` = `"compile"` | [set_value(`helper_envelope.result.ok`, `false`), set_value(`helper_envelope.result.exit_code`, `1`), set_value(`helper_envelope.result.normalized_outcome`, `"compile_error"`), set_value(`helper_envelope.result.error`, `"sandbox_compile_string returned NULL without a diagnostic"`)]. |
| <a id="contract-policy-check_data-verdict-setup"></a>4. Native setup failure | `true` | [set_value(`helper_envelope.result.ok`, `false`), set_value(`helper_envelope.result.exit_code`, `1`), set_value(`helper_envelope.result.normalized_outcome`, `"setup_error"`), set_value(`helper_envelope.result.error`, `helper_envelope.data.compile.error`)]. |

<a id="contract-policy-check_data-verdict-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Select the helper verdict](#contract-policy-check_data-verdict).** The helper selects its result from the last native-stage record. [Evidence details](CONTRACT.md#contract-policy-check_data-verdict-support-details).

<a id="contract-policy-check_data-metadata"></a>
#### Decoded policy metadata

[Compiler helper](CONTRACT.md#contract-identity-definitions-helper) reports at decoded helper input to report metadata. Entry: standalone helper, controller helper stdin. Recipient: report reader. Reports: helper envelope. [set_value(`check_data.policy_format`, `helper_request.policy.format`), set_value(`check_data.params_present`, present(`helper_request.policy.params`))].

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-policy-check_data-metadata-present"></a>Present parameter map | Applies when present(`helper_request.policy.params`). set_value(`check_data.params_count`, count(`helper_request.policy.params`)). |
| <a id="contract-policy-check_data-metadata-absent"></a>Absent parameter map | Applies when absent(`helper_request.policy.params`). set_value(`check_data.params_count`, `0`). |

<a id="contract-policy-check_data-metadata-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Decoded policy metadata](#contract-policy-check_data-metadata).** Metadata retains decoded format and optional-map presence/count, including an empty present map. [Evidence details](CONTRACT.md#contract-policy-check_data-metadata-support-details).

<a id="contract-policy-compile"></a>
### Last native compile stage

Record `compile` locations: `helper_envelope.data.compile`.

- <a id="contract-policy-compile-stage"></a>**`stage`** (string): Last native stage attempted: parameter object creation, one parameter assignment, or source compilation. `compile` means required parameter setup completed. Admitted vocabulary: closed; displayed list: exhaustive: `"params_create"`, `"param_set"`, `"compile"`.
- <a id="contract-policy-compile-ok"></a>**`ok`** (boolean): Whether that last stage supplied the helper's successful native result. Compilation succeeds only when the profile is non-null and the native diagnostic pointer is null.
- <a id="contract-policy-compile-error"></a>**`error`** (string ∪ null): At setup failure, helper text identifies the call and, for parameter assignment, the key. At compile, copy the native diagnostic as lossily decoded UTF-8, preserving an empty diagnostic as an empty string. A null profile with no diagnostic leaves this field null and supplies a separate explanatory summary.

<a id="contract-policy-compile-release"></a>
#### Release native resources

[Compiler helper](CONTRACT.md#contract-identity-definitions-helper) acts at native compile-call completion. Entry: standalone helper, controller helper stdin. Recipient: caller, report reader. Reports: helper envelope. Free every acquired parameter object, returned profile and native error buffer. Treat a non-null diagnostic as compile failure even when a profile was returned. Preserve the native diagnostic separately from the helper summary.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-policy-compile-release-diagnostic"></a>Retained compile diagnostic | Requires implies((`compile.stage` = `"compile"` and present(`compile.error`)), `compile.ok` = `false`). An empty native diagnostic remains present and therefore also rules out helper compile success. |

<a id="contract-policy-compile-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Last native compile stage](#contract-policy-compile) and its descendants.** The adjacent field meanings and operations follow the named implementation. Evidence limit: Native wrapper branches read. Scripted native-result controls and platform execution still need to be joined as graded owners. [Evidence details](CONTRACT.md#contract-policy-compile-support-details).

<a id="contract-envelope-helper"></a>
### Compiler-helper envelope

Actor: [Compiler helper](CONTRACT.md#contract-identity-definitions-helper). Boundary: compiler-helper envelope presentation. Entry: standalone helper, controller helper stdin. Recipient: helper caller, controller. Reports: helper envelope. Record `compiler_envelope`: `rust.HelperEnvelope`.

- <a id="contract-envelope-helper-build"></a>**`build`** ([Build identification](#contract-identity-build)): The helper binary's embedded build stamp.
- <a id="contract-envelope-helper-data"></a>**`data`** ([Compiler-helper data](#contract-policy-check_data)): Helper policy metadata, import inventory and compilation result.
- <a id="contract-envelope-helper-generated_at_unix_ms"></a>**`generated_at_unix_ms`** (integer): Helper wall-clock time at rendering, in milliseconds since the Unix epoch. An unavailable pre-epoch duration becomes zero.
- <a id="contract-envelope-helper-kind"></a>**`kind`** (string): `sbpl_check` identifies standalone or captured helper compilation.
- <a id="contract-envelope-helper-result"></a>**`result`** ([Operation result](#contract-envelope-result)): The helper operation's result, separate from any worker execution.
<!-- END GENERATED CONTRACT helper -->

## Read the direct validator

These direct commands inspect a PID or perform a native query. Their argument errors and output forms belong to this interface; the host’s separate batch line protocol is stated in [ARCHITECTURE](ARCHITECTURE.md#contract-wire-validator).

<!-- BEGIN GENERATED CONTRACT validator -->
Inherited surface support: [Implementation and evidence](ARCHITECTURE.md#contract-wire-support) (original subtree scope).

<a id="contract-wire-standalone"></a>
### Direct validator commands

Each shipped service contains `Contents/MacOS/sb_api_validator`. Direct invocation accepts `[--json] PID [operation filter_type [filter_value]]`; `--batch PID` selects the [validator query and reply line protocol](ARCHITECTURE.md#contract-wire-validator). The leading flags select distinct modes and are not combined.

<a id="contract-wire-standalone-status"></a>
#### Parse and report a PID

[Validator](CONTRACT.md#contract-identity-definitions-validator) acts at direct argv admission. Entry: validator status, validator single query, validator batch. Recipient: helper caller. Reports: validator status, validator single result, validator error. The first positional value is consumed by base-10 strtol and is positive and at most 1,073,741,824, with no trailing bytes. Accept that numeric PID. With no further arguments in direct mode, print ok or the JSON status object and exit zero. With operation arguments, continue to filter admission; batch takes no further positional arguments.

The PID-only branch performs parsing and reaches no sandbox_check call or process-existence check. Missing arguments before a PID produce stderr and exit 2, including a bare --json. An invalid supplied PID produces stderr in plain mode or pid_missing in JSON mode, with pid -1 and exit 2.

<a id="contract-wire-standalone-filters"></a>
#### Choose a native filter

Direct and batch queries share a filter-name resolver: NONE is 0, PATH is 1, GLOBAL_NAME is 2 and LOCAL_NAME is 3. Conditional SDK names are APPLEEVENT_DESTINATION, RIGHT_NAME, PREFERENCE_DOMAIN, KEXT_BUNDLE_ID, INFO_TYPE, NOTIFICATION_TYPE, XPC_SERVICE_NAME, NVRAM_VARIABLE and POSIX_IPC_NAME when their corresponding sandbox filter macros exist at compilation. `RAW:<number>` uses base-10 strtol, accepts a fully consumed value from 0 through 255 and supplies that numeric filter ID. These accepted helper names are distinct from the host planner’s eligible query pairs.

<a id="contract-wire-standalone-query"></a>
#### Run one native query

[Validator](CONTRACT.md#contract-identity-definitions-validator) acts at direct sandbox check call and stdout. Entry: validator single query. Recipient: helper caller. Reports: validator single result, validator error. An operation and recognized filter are supplied. Numeric filter ID zero requires no filter-value argument; every other ID requires exactly one. Clear errno, invoke sandbox_check for the supplied PID with SANDBOX_CHECK_NO_REPORT, and report the native rc and errno. Plain output is rc=<value> errno=<value> and exits zero for rc zero, one otherwise. JSON mode emits its single-result object and exits zero after the call, whatever its native result.

CLI filter/argument refusal exits 2. The native string printer escapes quotes, backslashes and control bytes; remaining argument bytes pass through unchanged.

<a id="contract-wire-standalone-query-execution_support"></a>
**Support: [executed](CONTRACT.md#contract-support-grades) for [Run one native query](#contract-wire-standalone-query).** RAW empty/zero direct value arity, no-report native-call flag, and direct JSON/plain versus batch output/exit for six supplied rc/errno pairs; the shipped helper separately observes selected allow, deny and unsupported-operation results against its owned native target. Context: Read the production parser/emitter and exact assertions; inspected both completed validator_batch_mode case receipts, retained argv/input/output and control.log in run 20261111T155411Z_29ef0802. Evidence limit: The return matrix substitutes the native call in a production-source build. Shipped-helper observations use the selected target and macOS build; PID-only admission, other argument errors and invalid-UTF-8 direct arguments retain source support. The overall default run has a separate reader-corpus case failure. [Evidence details](CONTRACT.md#contract-wire-standalone-query-execution_support-details).

<a id="contract-wire-standalone-meaning"></a>
#### Direct and batch validator meanings

Direct JSON denied means native rc is nonzero, including a native error; successful direct JSON reporting exits 0. Plain output exits 0 or 1 from native rc. Batch deny requires rc 1 and errno zero and retains its diagnostic classifications. An empty RAW suffix resolves to numeric zero. Direct numeric-zero filters take no value; batch treats the spelling NONE as valueless, so RAW:0 carries a value that the zero-filter native call leaves unused. Direct argv uses C strings; batch validates its JSON strings as UTF-8.

<a id="contract-wire-standalone-meaning-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Direct and batch validator meanings](#contract-wire-standalone-meaning).** Direct and batch parsing and native-result projection retain operation-specific rules. Context: Static review of the cited producer and assertion branches. Evidence limit: The controls compare selected shipped-helper RAW-zero, duplicate and native error/deny cases; status and encoding branches retain their own source support. [Evidence details](CONTRACT.md#contract-wire-standalone-meaning-disposition_support-details).

<a id="contract-wire-standalone-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Direct validator commands](#contract-wire-standalone) and its descendants.** Direct argv branches establish parsing, mode-specific output, filter resolution and exit selection; the build inventory establishes the shipped helper location. Context: Read complete main/parse/filter/error-printer branches and the signed app helper inventory. Evidence limit: PID-only admission, conditional filter names and raw C-string encoding are supported by the cited source branches. The query controls cover their selected RAW-zero and result/exit branches. [Evidence details](CONTRACT.md#contract-wire-standalone-support-details).

<a id="contract-wire-standalone_status"></a>
### Direct PID status

Record `standalone_status`: `ValidatorDirectStatus`.

- <a id="contract-wire-standalone_status-kind"></a>**`kind`** (string): sb_api_validator_status identifies the PID-only JSON branch.
- <a id="contract-wire-standalone_status-schema_version"></a>**`schema_version`** (integer): Version 1 of this direct JSON object.
- <a id="contract-wire-standalone_status-pid"></a>**`pid`** (integer): Positive PID accepted by argument parsing.
- <a id="contract-wire-standalone_status-error"></a>**`error`** (JSON value): Always null on this status branch.

**kind.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-wire-standalone_status-kind-produced"></a>Produced kind | Requires `standalone_status.kind` = `"sb_api_validator_status"`. |

**schema_version.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-wire-standalone_status-schema_version-produced"></a>Produced schema | Requires `standalone_status.schema_version` = `1`. |

**pid.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-wire-standalone_status-pid-positive"></a>Parsed positive PID | Requires `standalone_status.pid` > `0`. |

**error.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-wire-standalone_status-error-null"></a>Status diagnostic slot | Requires `standalone_status.error` = `null`. |

<a id="contract-wire-standalone_result"></a>
### Direct native result

Record `standalone_result`: `ValidatorDirectResult`.

- <a id="contract-wire-standalone_result-kind"></a>**`kind`** (string): sb_api_validator_result identifies one direct native query.
- <a id="contract-wire-standalone_result-schema_version"></a>**`schema_version`** (integer): Version 1 of this direct JSON object.
- <a id="contract-wire-standalone_result-pid"></a>**`pid`** (integer): Parsed PID passed to sandbox_check.
- <a id="contract-wire-standalone_result-operation"></a>**`operation`** (string): Operation argument passed to the native call.
- <a id="contract-wire-standalone_result-filter_type"></a>**`filter_type`** (string): Supplied symbolic or RAW filter spelling.
- <a id="contract-wire-standalone_result-filter_type_id"></a>**`filter_type_id`** (integer): Resolved numeric filter ID before OR with SANDBOX_CHECK_NO_REPORT.
- <a id="contract-wire-standalone_result-filter_value"></a>**`filter_value`** (string ∪ null): Filter string passed for a nonzero ID; null for ID zero.
- <a id="contract-wire-standalone_result-extra"></a>**`extra`** (JSON value): Always null in this producer.
- <a id="contract-wire-standalone_result-rc"></a>**`rc`** (integer): Exact native sandbox_check return.
- <a id="contract-wire-standalone_result-errno"></a>**`errno`** (integer): Native errno after clearing it before the call.
- <a id="contract-wire-standalone_result-allowed"></a>**`allowed`** (boolean): True exactly when native rc is zero.
- <a id="contract-wire-standalone_result-denied"></a>**`denied`** (boolean): True exactly when native rc is nonzero, including native errors.

**kind.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-wire-standalone_result-kind-produced"></a>Produced kind | Requires `standalone_result.kind` = `"sb_api_validator_result"`. |

**schema_version.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-wire-standalone_result-schema_version-produced"></a>Produced schema | Requires `standalone_result.schema_version` = `1`. |

**pid.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-wire-standalone_result-pid-positive"></a>Parsed positive PID | Requires `standalone_result.pid` > `0`. |

**filter_value.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-wire-standalone_result-filter_value-numeric"></a>Numeric filter argument relation | Requires (implies(`standalone_result.filter_type_id` = `0`, absent(`standalone_result.filter_value`)) and implies(`standalone_result.filter_type_id` ≠ `0`, present(`standalone_result.filter_value`))). |

**extra.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-wire-standalone_result-extra-null"></a>Direct-result extension slot | Requires `standalone_result.extra` = `null`. |

**allowed.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-wire-standalone_result-allowed-native"></a>Zero native return | Requires `standalone_result.allowed` = `standalone_result.rc` = `0`. |

**denied.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-wire-standalone_result-denied-native"></a>Nonzero native return | Requires `standalone_result.denied` = `standalone_result.rc` ≠ `0`. |

<a id="contract-wire-standalone_error"></a>
### Direct argument error

Record `standalone_error`: `ValidatorDirectError`.

- <a id="contract-wire-standalone_error-kind"></a>**`kind`** (string): sb_api_validator_error identifies a JSON-mode argument refusal.
- <a id="contract-wire-standalone_error-schema_version"></a>**`schema_version`** (integer): Version 1 of this direct JSON object.
- <a id="contract-wire-standalone_error-error"></a>**`error`** (string): pid_missing, missing_args, bad_filter, unexpected_filter_value_for_none, missing_filter_value or unexpected_extra_args names the reached refusal.
- <a id="contract-wire-standalone_error-pid"></a>**`pid`** (integer?): Parsed PID, or -1 for pid_missing; omitted for bad_filter.
- <a id="contract-wire-standalone_error-filter"></a>**`filter`** (string?): Rejected filter spelling for bad_filter; omitted for other errors.
<!-- END GENERATED CONTRACT validator -->

## Read runner administration

Runner list, install, verify, validate, reconcile and removal operations report registry and service observations under their own command obligations. [The controller reference](../controller/README.md) provides invocation syntax. Read retained cleanup ownership and uncertain absence before treating a removal result as completed recovery.

<!-- BEGIN GENERATED CONTRACT installation -->
<a id="contract-installation"></a>
## Managing runners

The controller manages external XPC services through a local registry and launchd. Registry state, on-disk signature observations, live service presence and a completed verification specimen establish different facts.

<a id="contract-installation-support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Managing runners](#contract-installation) and its descendants.** Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation. Context: Read the cited producer/receiver declarations and branches; check citations identify the assertions read. Evidence limit: These read controls use registry files and supplied cleanup/signing observations. Live launchd, GUI-session access, signing, interruption recovery and opaque metadata through all CLI transitions need separately recorded execution evidence. [Evidence details](CONTRACT.md#contract-installation-support-details).

<a id="contract-installation-dynamic_support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Managing runners](#contract-installation) and its descendants.** The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations. Context: Read the json! construction sites and their enclosing branches. Evidence limit: Field-node coverage and source review establish the declared shape; a dedicated independent output mutation control for every dynamic branch remains open. [Evidence details](CONTRACT.md#contract-installation-dynamic_support-details).

<a id="contract-installation-commands"></a>
### Command boundaries

<a id="contract-installation-commands-read"></a>
#### Read and select records

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at runner registry lookup. Entry: runner list, runner status, runner verify, runner remove, runner reconcile. Recipient: cli caller. Reports: runner registry, runner status, runner verify, runner remove, runner reconcile. The registry is readable with schema_version 1, or its path is absent. Use PW_RUNNER_REGISTRY when nonempty, otherwise HOME/Library/Application Support/PolicyWitness/runners.json. An absent file yields schema_version 1 with empty runners and pending_cleanup. For selector commands, prefer a supplied id and otherwise use service_name; an unmatched id remains a miss.

`runner list` returns the registry as `kind: "runner_registry"`. `runner status` returns the selected active record as `kind: "runner_status"`. Status and verify search `runners`; removal also resumes `pending_cleanup`. A miss returns that operation’s envelope kind, `result.normalized_outcome: "not_found"`, false `ok` and exit code 2. Unsupported registry schemas and malformed known fields refuse loading. Read-only commands can read the prior or replacement complete registry while a modifier holds its lock.

<a id="contract-installation-commands-publish"></a>
#### Publish a registry mutation

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at install, validate and remove registry transaction. Entry: runner install, runner validate, runner remove. Recipient: cli caller. Reports: runner registry. The command holds the stable sibling registry lock across its mutation and associated launchd actions. Serialize and read back the proposed registry, require lossless reserialization, write and sync a new mode-0600 file in the same directory, then atomically rename it over the registry. Refuse a busy/unavailable advisory lock or a readback that loses metadata.

The lock inode is retained across replacements. Operators must keep the lock file while any command may hold it. Unknown JSON members at the registry, runner, cleanup, ownership, signature and entitlement levels survive unrelated writes as opaque values. Known fields retain their meanings; opaque members supply no ownership observations.

<a id="contract-installation-commands-install"></a>
#### Install a selected service

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at external bundle validation, signing, registry and launchd. Entry: runner install. Recipient: cli caller, launchd. Reports: runner install, runner registry. Uses [Exact admission identity](CONTRACT.md#contract-identity-public-contract). The caller supplies an existing bundle directory; the kind defaults to byoxpc, and an explicit kind must be byoxpc. Scope defaults to user or may be explicitly system. Resolve the canonical bundle, require CFBundlePackageType XPC!, exact current PWContract, CFBundleIdentifier service identity and an existing Contents/MacOS/CFBundleExecutable. Reject conflicting active/recovery service, bundle or executable identities; verify the source seal and equipment inventory before optional signing.

An explicit service name must equal the bundle identifier. `--bundle-id` and `--executable` are refused; those identities come from the bundle. The installer refuses an existing target plist. With `--identity`, it signs the selected worker and host with the supplied entitlements, and the validator/unentitled worker without them, refreshing the sealed equipment inventory before sealing the host. Entitlements with `--allow-adhoc` can select ad-hoc signing; an ad-hoc result requires that flag. Required helpers must exist. The final recursive strict signature verification and reread of bundle identity precede registry installation.

<a id="contract-installation-commands-pending"></a>
#### Retain installation ownership

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at pending registry save before plist creation and bootstrap. Entry: runner install. Recipient: cli caller, launchd. Reports: runner install, runner registry. Bundle verification/signing and readbacks succeeded and the launchd plist has been prepared. Save a pending runner with its plist path, launchd domain, owner UID and plist hash before creating the plist or bootstrapping. Mark installed only after those requested operations and final registry save succeed; retain pending on later failure.

User scope writes HOME/Library/LaunchAgents and targets gui/<uid>, requiring access to that logged-in GUI domain. System scope writes /Library/LaunchDaemons and targets system, requiring the relevant privilege. The plist invokes the recorded executable with `--mach-service` and the service name, advertises that Mach service, sets RunAtLoad and a <!-- span limits.byoxpc_throttle_interval.value_unit -->1 second<!-- /span --> throttle, and defaults XPC_SERVICE_PATH to the bundle. `--env KEY=VALUE` requires a nonempty key; later occurrences replace earlier values. With `--skip-bootstrap`, successful plist creation completes installation; `loaded` remains a separate observation. Signing changes can precede the pending save.

<a id="contract-installation-commands-verify"></a>
#### Verify a selected service

[Controller](CONTRACT.md#contract-identity-definitions-controller), [Runner client](CONTRACT.md#contract-identity-definitions-client) acts at fixed verification specimen through reservation and execution. Entry: runner verify. Recipient: cli caller, runner host. Reports: runner verify. [set_value(`request.contract`, [Contract](#contract-identity-build-contract)), set_value(`request.specimen_id`, `"runner_verify"`), set_value(`request.run_kind`, `"runner_verify"`), set_value(`request.policy.format`, `"sbpl"`), set_value(`request.policy.sbpl_source`, `"(version 1)\n(allow default)\n"`), set_value(`request.probe_plan`, []), withhold(`request.actors`), withhold(`request.phases`), withhold(`request._test_overrides`)]. Uses [Select the verification operation result](#contract-installation-verify-select), [Request delivery failure](#contract-installation-verify-delivery_failure), [Decoded response collection bounds](#contract-diagnostics-execution-geometry). Lookup finds an external runner record. Send the held fixed verification request in a fresh invocation and apply ordinary delivery and reply admission. Under successful admission, copy a supported reply's PID and outcome; an absent reply selects runner_response_unavailable and no PID. A refused boundary selects its admission classification and no PID. The selected verification outcome and independent delivery error determine the operation result below.

The timeout defaults to <!-- span limits.runner_verify_wait.value_unit -->5,000 milliseconds<!-- /span --> and is clamped to at least one. An empty successful plan establishes the verification request’s application and completion. It supplies no per-operation prediction or attempt observations.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-installation-commands-verify-identity"></a>Selected record identity | Requires `runner_record.contract` = [Contract](#contract-identity-build-contract). |

<a id="contract-installation-commands-pending_verify"></a>
#### Pending verification

Ordinary specimen selection refuses a Pending installation. Explicit runner verify can address that recorded service after kind and contract checks, using the fixed verification request and retaining the recorded Pending state. Verification leaves the registry bytes unchanged.

<a id="contract-installation-commands-pending_verify-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Pending verification](#contract-installation-commands-pending_verify).** Explicit verification selects by recorded identity and kind/contract, independently of ordinary Pending selection. Context: Static review of the cited producer and assertion branches. Evidence limit: The control uses an owned live current service with a constructed Pending registry state and snapshots the registry around both operations. [Evidence details](CONTRACT.md#contract-installation-commands-pending_verify-disposition_support-details).

<a id="contract-installation-commands-validate"></a>
#### Refresh validation metadata

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at registered bundle and binary signature/inventory reads. Entry: runner validate. Recipient: cli caller. Reports: runner validate, runner registry. The controller loaded and locked the registry. Visit every record in runners, refresh available per-binary signature/entitlement observations, verify the bundle and equipment inventory, save the registry, and report missing/invalid counts and per-binary failures.

A missing host executable increments `missing`, marks the host signature invalid and records its entitlement error, then skips further verification for that row. A completed validate command reports `result.ok: true` and exit 0 even when missing/invalid is positive; inspect those fields. Pending cleanup records remain recovery records.

<a id="contract-installation-commands-entitlement_errors"></a>
#### Entitlement read errors and summary counts

A successful metadata read can retain an entitlement error alongside a valid signature without adding a validation failure. A failed read-back contributes a failure and unreadable signature metadata. Equipment validation applies its own entitlement requirements. The command counts invalid runners after combining the applicable failures; host and validator entitlement metadata errors alone retain their metadata scope.

<a id="contract-installation-commands-entitlement_errors-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [Entitlement read errors and summary counts](#contract-installation-commands-entitlement_errors).** Read-back failure and entitlement metadata are separate validation results. Context: Static review of the cited producer and assertion branches. Evidence limit: The injected seam checks per-role metadata and failure lists. Whole-command invalid-count consequences remain source-read alongside the separate equipment checks. [Evidence details](CONTRACT.md#contract-installation-commands-entitlement_errors-disposition_support-details).

<a id="contract-installation-commands-reconcile"></a>
#### Reconcile observations

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at registry records, launchctl print and launchd plist directories. Entry: runner reconcile. Recipient: cli caller. Reports: runner reconcile. The registry loaded successfully. Report each active and cleanup record with current service/plist observations and separate ownership classifications, and report recognizable unregistered plist candidates plus inspection errors. Leave installation resources and registry records as observed.

Candidate discovery scans readable LaunchDaemons and the user LaunchAgents directory. A com.policywitness. label, executable filename PWRunner, or unreadable/unparsed plist with that filename prefix can identify a reporting candidate. Registered label/scope pairs are suppressed from candidates. Discovery establishes a candidate for inspection; cleanup authority requires the recorded identity and the independent ownership gates.

<a id="contract-installation-commands-remove"></a>
#### Remove an owned installation

[Controller](CONTRACT.md#contract-identity-definitions-controller) acts at durable cleanup transaction, launchctl bootout and plist unlink. Entry: runner remove. Recipient: cli caller, launchd. Reports: runner remove, runner registry. The requested active record or retained cleanup record exists. Move an active record to nested pending_cleanup and save before any launchd/plist action. Inspect service and plist ownership independently; boot out only an owned service unless skip_bootout, and unlink only an owned plist after an immediate ownership recheck. Retire cleanup only after observed service absence, plist absence, no warnings and successful registry publication.

After a successful bootout, re-read a still-present service every <!-- span limits.runner_remove_poll_interval.value_unit -->50 milliseconds<!-- /span --> for at most <!-- span limits.runner_remove_teardown_wait.value_unit -->1,000 milliseconds<!-- /span --> of nominal waiting; stop at absence or unknown. Final absence is separately observed. A changed/unreadable/unowned object, failed action or failed retirement publication retains recovery and warnings. A repeated remove continues the retained record from the durable registry, including after the plist has disappeared or the original diagnostic output is gone. `--skip-bootout` can remove an owned plist; retirement still requires observed service absence. A completed remove command reports `result.ok: true` and exit 0 even when cleanup remains retained.

<a id="contract-installation-commands-ownership"></a>
#### Classify cleanup ownership

[Controller](CONTRACT.md#contract-identity-definitions-controller) checks at recorded cleanup location and current resource observations. Entry: runner remove, runner reconcile. Recipient: cli caller. Reports: runner remove, runner reconcile. Uses [Classify the typed service observation](#contract-installation-service-classify). The recorded service name, user/scope/domain and paths pass location checks. Classify plist ownership from a regular file with matching Label, complete ProgramArguments, MachServices and XPC_SERVICE_PATH; recorded ownership additionally requires matching UID and plist hash.

Absent resources are classified ambiguous for ownership and retain their independently observed absent presence. Unknown presence produces unknown ownership. Recorded cleanup paths must be absolute, have no parent traversal, end in the expected service plist, and have an immediate parent named LaunchAgents for user scope or LaunchDaemons for system scope. The location check also requires the executable parent to equal the recorded bundle’s Contents/MacOS and refuses symlinked plist ancestors. The recorded ownership supplies the full parent path. Legacy records without ownership derive the conventional plist path and use the content checks.

<a id="contract-installation-commands-ownership-disposition_support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Classify cleanup ownership](#contract-installation-commands-ownership).** Location and resource ownership checks use the recorded path and complete associated identities. Evidence limit: Acceptance of a nonconventional full parent is source-supported; this owner supplies no native occurrence for that path. [Evidence details](CONTRACT.md#contract-installation-commands-ownership-disposition_support-details).

<a id="contract-installation-commands-recovery"></a>
#### Retained cleanup example

If bootout succeeds and plist removal succeeds but the final launchctl read is unknown, the command reports both action booleans true and cleanup_retained true. Keep the recorded bundle and any operator recovery state, inspect reconcile, and repeat removal until service/plist absence and registry retirement are observed.

<a id="contract-installation-registry"></a>
### Runner registry

Record `registry`: `rust.RunnerRegistry`.

- <a id="contract-installation-registry-schema_version"></a>**`schema_version`** (integer): Supported registry layout version, currently 1.
- <a id="contract-installation-registry-runners"></a>**`runners`** (array of [One runner record](#contract-installation-runner)): Active installation records, including pending installations and installed records.
- <a id="contract-installation-registry-pending_cleanup"></a>**`pending_cleanup`** (array of [Retained cleanup transaction](#contract-installation-pending_cleanup)): Retained cleanup transactions, including nested runner identity and accumulated observations; empty by default when absent in a historical registry.

<a id="contract-installation-runner"></a>
### One runner record

Record `runner`: `rust.RunnerRecord`.

Recorded signature, entitlement and inventory values describe their named reads; later execution has its own admission and live observations.

- <a id="contract-installation-runner-state"></a>**`state`** (string): `pending` means installation ownership was saved before completion; `installed` means the requested installation transaction completed. Missing historical state defaults to installed.
- <a id="contract-installation-runner-ownership"></a>**`ownership`** ([Recorded cleanup ownership](#contract-installation-ownership) ∪ null): Recorded plist identity and location used by cleanup, or null for a historical record without it.
- <a id="contract-installation-runner-id"></a>**`id`** (string): Controller-generated registry identifier for this installation.
- <a id="contract-installation-runner-service_name"></a>**`service_name`** (string): Mach service identity selected from the bundle identifier and used for lookup/launchd.
- <a id="contract-installation-runner-bundle_path"></a>**`bundle_path`** (string): Canonical bundle location retained at installation.
- <a id="contract-installation-runner-executable_path"></a>**`executable_path`** (string): Host executable path derived from the bundle metadata.
- <a id="contract-installation-runner-bundle_id"></a>**`bundle_id`** (string ∪ null): Recorded CFBundleIdentifier, or null in a historical record without it.
- <a id="contract-installation-runner-scope"></a>**`scope`** (string): `user` selects the current gui domain; `system` selects the system launchd domain.
- <a id="contract-installation-runner-contract"></a>**`contract`** (string; omitted when empty): Public identity recorded from the verified bundle. Omitted if empty in a historical record; execution requires exact current identity.
- <a id="contract-installation-runner-signature"></a>**`signature`** ([Signature observation](#contract-installation-signature)): Host signature observation retained from installation or validation.
- <a id="contract-installation-runner-entitlements"></a>**`entitlements`** ([Entitlement observation](#contract-installation-entitlements)): Host entitlement readback and any read error.
- <a id="contract-installation-runner-installed_at_unix_ms"></a>**`installed_at_unix_ms`** (integer): Controller wall-clock Unix milliseconds recorded while preparing installation, including a pending transaction.
- <a id="contract-installation-runner-kind"></a>**`kind`** (string?): Known runner kind when recorded. Historical machme/debuggable deserialize to byoxpc; absent kind can be inferred by the selecting command.
- <a id="contract-installation-runner-worker_signature"></a>**`worker_signature`** ([Signature observation](#contract-installation-signature)?): Normal-worker signature observation when available; omitted in records without it.
- <a id="contract-installation-runner-worker_entitlements"></a>**`worker_entitlements`** ([Entitlement observation](#contract-installation-entitlements)?): Normal-worker entitlement readback when available.
- <a id="contract-installation-runner-unentitled_worker_signature"></a>**`unentitled_worker_signature`** ([Signature observation](#contract-installation-signature)?): Unentitled-worker signature observation when available.
- <a id="contract-installation-runner-unentitled_worker_entitlements"></a>**`unentitled_worker_entitlements`** ([Entitlement observation](#contract-installation-entitlements)?): Unentitled-worker entitlement readback when available.
- <a id="contract-installation-runner-unentitled_worker_sha256"></a>**`unentitled_worker_sha256`** (string?): Unentitled-worker file hash retained at installation when available.
- <a id="contract-installation-runner-worker_equipment_inventory"></a>**`worker_equipment_inventory`** (JSON value?): Post-signing sealed equipment snapshot retained as JSON. Current execution separately validates its on-disk inventory and role artifacts.
- <a id="contract-installation-runner-source_worker_equipment_inventory"></a>**`source_worker_equipment_inventory`** (JSON value?): Verified source equipment snapshot retained before installer signing, as JSON.
- <a id="contract-installation-runner-validator_signature"></a>**`validator_signature`** ([Signature observation](#contract-installation-signature)?): Validator signature observation when available.
- <a id="contract-installation-runner-validator_entitlements"></a>**`validator_entitlements`** ([Entitlement observation](#contract-installation-entitlements)?): Validator entitlement readback when available.
- <a id="contract-installation-runner-issuer_signature"></a>**`issuer_signature`** ([Signature observation](#contract-installation-signature)?): Historical extension-issuer signature metadata when available. Current install leaves it absent.
- <a id="contract-installation-runner-issuer_entitlements"></a>**`issuer_entitlements`** ([Entitlement observation](#contract-installation-entitlements)?): Historical extension-issuer entitlement metadata when available. Current install leaves it absent.

<a id="contract-installation-runner-kind-disposition_support"></a>
**Support: [check read](CONTRACT.md#contract-support-grades) for [kind](#contract-installation-runner-kind).** Registry normalization and durable cleanup preserve historical records and opaque metadata. Context: Static review of the cited producer and assertion branches. Evidence limit: The live workflow uses a current owned service and a constructed historical debuggable record; both retired aliases have separate offline controls. [Evidence details](CONTRACT.md#contract-installation-runner-kind-disposition_support-details).

<a id="contract-installation-ownership"></a>
### Recorded cleanup ownership

Record `ownership`: `rust.RunnerOwnership`.

- <a id="contract-installation-ownership-plist_path"></a>**`plist_path`** (string): Absolute launchd plist path reserved by installation.
- <a id="contract-installation-ownership-launchd_domain"></a>**`launchd_domain`** (string): Recorded gui/<uid> or system domain for that scope.
- <a id="contract-installation-ownership-owner_uid"></a>**`owner_uid`** (integer): Installer’s numeric UID, compared with the acting user and observed plist owner for cleanup.
- <a id="contract-installation-ownership-plist_sha256"></a>**`plist_sha256`** (string): Hash of the exact generated plist bytes, compared with the current file before cleanup.

<a id="contract-installation-signature"></a>
### Signature observation

Record `signature`: `rust.RunnerSignature`.

Signature facts belong to the recorded file and read time. Preserve unknown members during registry recovery.

- <a id="contract-installation-signature-team_id"></a>**`team_id`** (string ∪ null): TeamIdentifier string read from codesign metadata when available; null when absent.
- <a id="contract-installation-signature-identity"></a>**`identity`** (string ∪ null): First Authority line read from codesign metadata when available; null for unavailable authority.
- <a id="contract-installation-signature-cdhash"></a>**`cdhash`** (string ∪ null): CDHash string read from codesign metadata when available.
- <a id="contract-installation-signature-valid"></a>**`valid`** (boolean): Recorded success of the owning signature-read/verification path. During validation, host validity also requires recursive bundle verification; each helper requires its own binary verification. Failed metadata reads produce false.
- <a id="contract-installation-signature-adhoc"></a>**`adhoc`** (boolean): Whether the read signature metadata identifies ad-hoc signing.

<a id="contract-installation-entitlements"></a>
### Entitlement observation

Record `entitlements`: `rust.RunnerEntitlements`.

An empty keys/granted list with an error describes unavailable parsing. Boolean false, strings and integers do not enter granted.

- <a id="contract-installation-entitlements-raw_plist"></a>**`raw_plist`** (string ∪ null): Entitlement plist text returned by codesign, or null when none was emitted or the read was unavailable.
- <a id="contract-installation-entitlements-keys"></a>**`keys`** (array of string): Sorted names of every key in a parsed entitlement dictionary, regardless of value.
- <a id="contract-installation-entitlements-granted"></a>**`granted`** (array of string): Sorted keys whose values are JSON boolean true after plist conversion. Missing historical granted defaults to an empty list.
- <a id="contract-installation-entitlements-error"></a>**`error`** (string ∪ null): Command, byte-cap or plist-conversion failure text when readback failed; null for a completed read.

<a id="contract-installation-pending_cleanup"></a>
### Retained cleanup transaction

Record `pending_cleanup`: `rust.PendingCleanup`. Uses [Current cleanup observation](#contract-installation-cleanup_observation).

The reader accepts historical flattened cleanup records and writes the nested runner form. Unknown members at each level preserve their own nesting, including runner members named observations or cleanup_started_at_unix_ms.

- <a id="contract-installation-pending_cleanup-runner"></a>**`runner`** ([One runner record](#contract-installation-runner)): Nested retained runner record, including unknown runner/ownership/signature/entitlement members.
- <a id="contract-installation-pending_cleanup-cleanup_started_at_unix_ms"></a>**`cleanup_started_at_unix_ms`** (integer): Controller wall-clock Unix milliseconds when the active record entered cleanup.
- <a id="contract-installation-pending_cleanup-observations"></a>**`observations`** (array of JSON value): Accumulated JSON observations. Current removal appends before/after records when location checks permit inspection; historical entries remain opaque.

<a id="contract-installation-cleanup"></a>
### Removal result

Record `cleanup`: `rust.CleanupReport`.

- <a id="contract-installation-cleanup-runner_id"></a>**`runner_id`** (string): Registry identifier of the cleanup target.
- <a id="contract-installation-cleanup-service_name"></a>**`service_name`** (string): Recorded service name of that target.
- <a id="contract-installation-cleanup-plist_path"></a>**`plist_path`** (string): Resolved cleanup path, recorded ownership path when resolution failed, or empty when neither was available.
- <a id="contract-installation-cleanup-booted_out"></a>**`booted_out`** (boolean): True only when this removal’s launchctl bootout call succeeded.
- <a id="contract-installation-cleanup-plist_removed"></a>**`plist_removed`** (boolean): True only when this removal’s unlink call succeeded.
- <a id="contract-installation-cleanup-cleanup_retained"></a>**`cleanup_retained`** (boolean): True when verified absence/clean completion or publication of retirement was unavailable; continue recovery using the retained record.
- <a id="contract-installation-cleanup-retained_record"></a>**`retained_record`** ([Retained cleanup transaction](#contract-installation-pending_cleanup)?): Recovery snapshot when cleanup remains retained; omitted after retirement.
- <a id="contract-installation-cleanup-warnings"></a>**`warnings`** (array of string; omitted when empty): Diagnostics for refused, failed, uncertain or unpersisted cleanup; omitted when empty.

<a id="contract-installation-cleanup-retention"></a>
#### Retained recovery account

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at runner remove result after cleanup publication attempt. Entry: runner remove. Recipient: report reader. Reports: runner remove.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-installation-cleanup-retention-fields"></a>Produced recovery fields | Requires (`cleanup.cleanup_retained` = present(`cleanup.retained_record`) and implies((present(`cleanup.warnings`) and count(`cleanup.warnings`) > `0`), `cleanup.cleanup_retained`)). |

<a id="contract-installation-cleanup-retention-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Retained recovery account](#contract-installation-cleanup-retention) and its descendants.** An incomplete or unpersisted cleanup retains its recovery snapshot; warnings prevent clean retirement. [Evidence details](CONTRACT.md#contract-installation-cleanup-retention-support-details).

<a id="contract-installation-install"></a>
### Installation result

Record `install`: `rust.RunnerInstallData`.

- <a id="contract-installation-install-state"></a>**`state`** (string): Installed state after the requested transaction and final registry save.
- <a id="contract-installation-install-loaded"></a>**`loaded`** ([Observed service](#contract-installation-service)): Independent launchctl service observation after installation.
- <a id="contract-installation-install-runner"></a>**`runner`** ([One runner record](#contract-installation-runner)): Complete recorded runner, including signature readbacks, inventories and cleanup ownership.
- <a id="contract-installation-install-plist_path"></a>**`plist_path`** (string): Path where the installer published the launchd plist.
- <a id="contract-installation-install-bootstrapped"></a>**`bootstrapped`** (boolean): True when this command requested and successfully completed bootstrap; false with skip-bootstrap.

<a id="contract-installation-install-state_copy"></a>
#### Published installation state

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at runner install result projection. Entry: runner install. Recipient: report reader. Reports: runner install. set_value(`install.state`, `install.runner.state`).

<a id="contract-installation-install-state_copy-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Published installation state](#contract-installation-install-state_copy).** RunnerInstallData copies the returned record state. [Evidence details](CONTRACT.md#contract-installation-install-state_copy-support-details).

<a id="contract-installation-verify"></a>
### Verification result

Record `verify`: `rust.RunnerVerifyData`. Uses [Controller observation of the client process](#contract-transport-client).

This is the completion record for a selected registry entry after the client invocation returns its capture. An unmatched lookup uses RunnerNotFoundData with not_found and exit code 2. Earlier argument, registry, setup or invocation failures return without this record.

- <a id="contract-installation-verify-runner_client"></a>**`runner_client`** ([Controller observation of the client process](#contract-transport-client) ∪ null): Client subprocess result, capture and delivery admission when available.
- <a id="contract-installation-verify-runner_result"></a>**`runner_result`** ([Execution record](#contract-reply-record) ∪ null): Decoded host result when available; its presence alone precedes the controller’s full reply admission.
- <a id="contract-installation-verify-state"></a>**`state`** (string): Registry installation state read when selecting this verification target.
- <a id="contract-installation-verify-runner_id"></a>**`runner_id`** (string ∪ null): Selected registry identifier when available.
- <a id="contract-installation-verify-service_name"></a>**`service_name`** (string): Selected service to which verification was addressed.
- <a id="contract-installation-verify-runner_pid"></a>**`runner_pid`** (integer ∪ null): PID projected only from an admitted host result. Its worker/host role follows the host result’s lifecycle.
- <a id="contract-installation-verify-normalized_outcome"></a>**`normalized_outcome`** (string): Controller verification classification, also supplied in the envelope result.

<a id="contract-installation-verify-delivery_failure"></a>
#### Request delivery failure

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at runner verify completion before reply interpretation. Entry: runner verify. Recipient: report reader. Reports: runner verify. Applies when (present(`verify.runner_client`) and present(`verify.runner_client.request_delivery`) and present(`verify.runner_client.request_delivery.error`)). [set_value(`result.ok`, `false`), set_value(`result.exit_code`, `2`), set_value(`result.normalized_outcome`, `"tool_error"`), set_value(`result.error`, `verify.runner_client.request_delivery.error`), set_value(`verify.normalized_outcome`, `"tool_error"`), set_value(`verify.runner_pid`, `null`), retain_records(`verify.runner_client`), retain_records(`verify.runner_result`)].

<a id="contract-installation-verify-delivery_failure-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Request delivery failure](#contract-installation-verify-delivery_failure).** DeliveryFailed precedes capture/reply interpretation and preserves the returned observations. [Evidence details](CONTRACT.md#contract-installation-verify-delivery_failure-support-details).

<a id="contract-installation-verify-select"></a>
#### Select the verification operation result

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at verification operation result from its selected outcome and delivery observation. Entry: runner verify. Recipient: report reader. Reports: runner verify. Select the first matching case in the listed order.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-installation-verify-select-delivery"></a>1. Delivery error has precedence | (present(`verify.runner_client`) and present(`verify.runner_client.request_delivery`) and present(`verify.runner_client.request_delivery.error`)) | [set_value(`result.ok`, `false`), set_value(`result.exit_code`, `2`), set_value(`result.normalized_outcome`, `"tool_error"`)]. |
| <a id="contract-installation-verify-select-finished"></a>2. Selected finished outcome | `verify.normalized_outcome` = `"finished"` | [set_value(`result.ok`, `true`), set_value(`result.exit_code`, `0`), set_value(`result.normalized_outcome`, `verify.normalized_outcome`)]. |
| <a id="contract-installation-verify-select-other"></a>3. Other selected outcome | `true` | [set_value(`result.ok`, `false`), set_value(`result.exit_code`, `1`), set_value(`result.normalized_outcome`, `verify.normalized_outcome`)]. |

<a id="contract-installation-verify-select-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Select the verification operation result](#contract-installation-verify-select).** The verification result uses delivery failure precedence and the already selected operation outcome; unsupported retained host fields do not supply a PID. [Evidence details](CONTRACT.md#contract-installation-verify-select-support-details).

<a id="contract-installation-validate"></a>
### Validation result

Record `validate`: `rust.RunnerValidateData`.

- <a id="contract-installation-validate-updated"></a>**`updated`** (integer): Number of runners visited and saved, including missing/invalid entries.
- <a id="contract-installation-validate-missing"></a>**`missing`** (integer): Rows whose recorded host executable did not exist; further verification was skipped for those rows.
- <a id="contract-installation-validate-invalid"></a>**`invalid`** (integer): Other rows with at least one bundle/binary verification, signature-metadata readback or inventory failure.
- <a id="contract-installation-validate-failures"></a>**`failures`** (array of [One validation failure](#contract-installation-failure)): Individual failure records, potentially multiple for one invalid runner.

<a id="contract-installation-failure"></a>
### One validation failure

Record `failure`: `rust.ValidateFailure`.

- <a id="contract-installation-failure-runner_id"></a>**`runner_id`** (string): Registry identifier of the row that failed this check.
- <a id="contract-installation-failure-service_name"></a>**`service_name`** (string): Service name recorded in that row.
- <a id="contract-installation-failure-binary"></a>**`binary`** (string): Failed role or check: bundle, host, worker, unentitled_worker, validator, issuer or equipment_inventory as applicable.
- <a id="contract-installation-failure-error"></a>**`error`** (string): Failure text from the named verification/readback.

<a id="contract-installation-not_found"></a>
### Unmatched lookup

Record `not_found`: `rust.RunnerNotFoundData`.

- <a id="contract-installation-not_found-requested_id"></a>**`requested_id`** (string?): Supplied ID, omitted when none was supplied.
- <a id="contract-installation-not_found-requested_service_name"></a>**`requested_service_name`** (string?): Supplied service name, omitted when none was supplied.

<a id="contract-installation-service"></a>
### Observed service

Record `service`: `rust.ServiceObservation`.

- <a id="contract-installation-service-presence"></a>**`presence`** (string): `present` for successful launchctl print, `absent` only for its specific missing-service diagnostic naming the requested service, otherwise `unknown`.
- <a id="contract-installation-service-executable_path"></a>**`executable_path`** (string ∪ null): The unique program = line from a successful launchctl print; null when missing, ambiguous or unavailable.
- <a id="contract-installation-service-error"></a>**`error`** (string ∪ null): Inspection diagnostic for unknown presence; null for recognized present/absent.

<a id="contract-installation-service-ownership"></a>
#### Service ownership assessment

Ownership of this observed service relative to the selected runner_record. Reconciliation and cleanup copy this assessment beside the observation.

<a id="contract-installation-service-classify"></a>
#### Classify the typed service observation

[Controller](CONTRACT.md#contract-identity-definitions-controller) reports at service observation for the selected runner record after location resolution. Entry: runner reconcile, runner remove. Recipient: report reader. Reports: runner reconcile, runner remove. Select the first matching case in the listed order. Uses [Service ownership assessment](#contract-installation-service-ownership).

A raw reconciliation row containing only unknown presence after location failure has no typed ownership association.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-installation-service-classify-unknown"></a>1. Unknown presence | `service.presence` = `"unknown"` | set_value([Service ownership assessment](#contract-installation-service-ownership), `"unknown"`). |
| <a id="contract-installation-service-classify-absent"></a>2. Absent service | `service.presence` = `"absent"` | set_value([Service ownership assessment](#contract-installation-service-ownership), `"ambiguous"`). |
| <a id="contract-installation-service-classify-owned"></a>3. Matching executable | (`service.presence` = `"present"` and present(`service.executable_path`) and `service.executable_path` = `runner_record.executable_path`) | set_value([Service ownership assessment](#contract-installation-service-ownership), `"owned"`). |
| <a id="contract-installation-service-classify-unowned"></a>4. Different executable | (`service.presence` = `"present"` and present(`service.executable_path`)) | set_value([Service ownership assessment](#contract-installation-service-ownership), `"unowned"`). |
| <a id="contract-installation-service-classify-ambiguous"></a>5. No usable executable | (`service.presence` = `"present"` and absent(`service.executable_path`)) | set_value([Service ownership assessment](#contract-installation-service-ownership), `"ambiguous"`). |

<a id="contract-installation-service-classify-support"></a>
**Support: [source read](CONTRACT.md#contract-support-grades) for [Classify the typed service observation](#contract-installation-service-classify).** The typed presence and observed/recorded executable paths determine service ownership; plist ownership is independent. [Evidence details](CONTRACT.md#contract-installation-service-classify-support-details).

<a id="contract-installation-plist"></a>
### Observed plist

Record `plist`: `rust.PlistObservation`.

- <a id="contract-installation-plist-presence"></a>**`presence`** (string): `absent` for a missing path; `present` for observed metadata, including invalid content; `unknown` for inspection/read failure that prevents a reliable observation.
- <a id="contract-installation-plist-config"></a>**`config`** (JSON value ∪ null): Parsed plist JSON dictionary/value when conversion succeeded; otherwise null.
- <a id="contract-installation-plist-sha256"></a>**`sha256`** (string ∪ null): Hash of bytes read from the plist when available, including bytes whose plist conversion failed.
- <a id="contract-installation-plist-owner_uid"></a>**`owner_uid`** (integer ∪ null): Filesystem owner UID read from symlink metadata when available.
- <a id="contract-installation-plist-regular"></a>**`regular`** (boolean): True when the observed path metadata identifies a regular file; false for another type or unavailable metadata.
- <a id="contract-installation-plist-error"></a>**`error`** (string ∪ null): Metadata, regular-file, read or conversion diagnostic when present; otherwise null.

<a id="contract-installation-reconcile"></a>
### Reconciliation result

Record `reconcile`: `RunnerReconcileData`.

The result reports successful reconciliation execution even when individual inspections remain unknown.

- <a id="contract-installation-reconcile-registry_path"></a>**`registry_path`** (string): Registry path used for this read.
- <a id="contract-installation-reconcile-records"></a>**`records`** (array of [One recorded reconciliation](#contract-installation-reconcile_record)): Recorded runners and retained cleanup entries, each with current observations or a location error.
- <a id="contract-installation-reconcile-candidates"></a>**`candidates`** (array of [Unregistered candidate](#contract-installation-candidate)): Recognizable unregistered launchd plist candidates from readable directories.
- <a id="contract-installation-reconcile-inspection_errors"></a>**`inspection_errors`** (array of [Reconciliation inspection error](#contract-installation-inspection_error)): Directory, path or plist inspection failures encountered during candidate discovery.

<a id="contract-installation-reconcile_record"></a>
### One recorded reconciliation

Record `reconcile_record`: `RunnerReconcileRecord`. Uses [Observed service](#contract-installation-service), [Observed plist](#contract-installation-plist).

- <a id="contract-installation-reconcile_record-recorded_state"></a>**`recorded_state`** (string): pending, installed or pending_cleanup identifies its registry location/state.
- <a id="contract-installation-reconcile_record-runner"></a>**`runner`** ([One runner record](#contract-installation-runner)): Recorded runner retained without substituting live observations.
- <a id="contract-installation-reconcile_record-service"></a>**`service`** (JSON value): Full ServiceObservation after valid location resolution; otherwise only {"presence":"unknown"}.
- <a id="contract-installation-reconcile_record-plist"></a>**`plist`** (JSON value): Full PlistObservation after valid location resolution; otherwise only {"presence":"unknown"}.
- <a id="contract-installation-reconcile_record-plist_path"></a>**`plist_path`** (string?): Resolved plist location; omitted on location error.
- <a id="contract-installation-reconcile_record-launchd_domain"></a>**`launchd_domain`** (string?): Resolved launchd domain; omitted on location error.
- <a id="contract-installation-reconcile_record-service_ownership"></a>**`service_ownership`** (string?): Owned, unowned, ambiguous or unknown classification serialized in lowercase; omitted on location error.
- <a id="contract-installation-reconcile_record-plist_ownership"></a>**`plist_ownership`** (string?): Independent plist ownership classification; omitted on location error.
- <a id="contract-installation-reconcile_record-ownership"></a>**`ownership`** (string?): unknown on location error; omitted after successful location resolution.
- <a id="contract-installation-reconcile_record-error"></a>**`error`** (string?): Location-check refusal text; omitted after successful location resolution.

<a id="contract-installation-candidate"></a>
### Unregistered candidate

Record `candidate`: `RunnerReconcileCandidate`.

- <a id="contract-installation-candidate-recorded_state"></a>**`recorded_state`** (string): unregistered for each candidate.
- <a id="contract-installation-candidate-scope"></a>**`scope`** (string): user or system according to the directory scanned.
- <a id="contract-installation-candidate-service_name"></a>**`service_name`** (string ∪ null): Parsed Label, or null if unavailable.
- <a id="contract-installation-candidate-executable_path"></a>**`executable_path`** (string ∪ null): Parsed ProgramArguments[0], falling back to Program, or null.
- <a id="contract-installation-candidate-plist_path"></a>**`plist_path`** (string): Candidate path observed during directory enumeration.
- <a id="contract-installation-candidate-service"></a>**`service`** ([Observed service](#contract-installation-service) ∪ null): Service observation when label/domain permitted lookup; otherwise null.
- <a id="contract-installation-candidate-plist"></a>**`plist`** ([Observed plist](#contract-installation-plist)): Current candidate file observation.
- <a id="contract-installation-candidate-ownership"></a>**`ownership`** (string): unknown when config is unavailable, ambiguous when label/executable is missing, otherwise unowned.

<a id="contract-installation-inspection_error"></a>
### Reconciliation inspection error

Record `inspection_error`: `RunnerReconcileInspectionError`.

- <a id="contract-installation-inspection_error-path"></a>**`path`** (string?): Directory or plist path involved; omitted when the user LaunchAgents path could not be determined.
- <a id="contract-installation-inspection_error-presence"></a>**`presence`** (string): unknown for each inspection error.
- <a id="contract-installation-inspection_error-error"></a>**`error`** (string): Inspection or path-resolution error text.

<a id="contract-installation-cleanup_observation"></a>
### Current cleanup observation

Record `cleanup_observation`: `RunnerCleanupObservation`.

This describes the current producer’s appended values within the open observations history.

- <a id="contract-installation-cleanup_observation-phase"></a>**`phase`** (string): before or after identifies its position around attempted actions.
- <a id="contract-installation-cleanup_observation-service"></a>**`service`** ([Observed service](#contract-installation-service)): Independent service observation at this phase.
- <a id="contract-installation-cleanup_observation-plist"></a>**`plist`** ([Observed plist](#contract-installation-plist)): Independent plist observation at this phase.
- <a id="contract-installation-cleanup_observation-service_ownership"></a>**`service_ownership`** (string?): Ownership classification supporting the before decision; omitted after actions.
- <a id="contract-installation-cleanup_observation-plist_ownership"></a>**`plist_ownership`** (string?): Independent before-action plist ownership classification; omitted after actions.
- <a id="contract-installation-cleanup_observation-teardown_wait"></a>**`teardown_wait`** ([Service teardown polling](#contract-installation-cleanup_wait)?): Polling receipt on after records; omitted before actions.

<a id="contract-installation-cleanup_wait"></a>
### Service teardown polling

Record `cleanup_wait`: `RunnerCleanupWait`.

- <a id="contract-installation-cleanup_wait-reads"></a>**`reads`** (integer): Number of service observations, including the initial post-action read.
- <a id="contract-installation-cleanup_wait-waited_ms"></a>**`waited_ms`** (integer): Sum of nominal requested polling intervals; zero when no wait occurred.
- <a id="contract-installation-cleanup_wait-poll_interval_ms"></a>**`poll_interval_ms`** (integer): Current requested polling interval, <!-- span limits.runner_remove_poll_interval.value_unit -->50 milliseconds<!-- /span -->.
- <a id="contract-installation-cleanup_wait-budget_ms"></a>**`budget_ms`** (integer): Current nominal waiting bound, <!-- span limits.runner_remove_teardown_wait.value_unit -->1,000 milliseconds<!-- /span -->.
<!-- END GENERATED CONTRACT installation -->
