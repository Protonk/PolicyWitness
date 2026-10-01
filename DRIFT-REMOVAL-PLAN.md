# Removing the drift verdict

Status: READY for implementation; implementation has not started. The
EXECUTION section at the end states how an agent runs this plan end to end
without operator check-ins.

Inventory baseline: df333b4 (request schema 3, response schema 12, worker ABI 7,
controller envelope 4). Source line numbers and reference counts use that
baseline. Symbols, not line numbers, are authoritative: I1 moves code, so later
references drift. Locate each site by its symbol and record the resolved
location in the decision log when it differs from the plan.

## DESIGN

### D0. Field acceptance criteria

Response fields, test results and guide recipes must not assert agreement,
disagreement, drift or consistency between prediction and enforcement.
Validation and selection may inspect both channels.

| Value kind | Definition | Acceptance rule |
| --- | --- | --- |
| Observation | A measurement, received result, hash of bytes outside the document, or decision a PW process made at the time that the document does not otherwise contain | Keep |
| Classification | A PW-owned table applied to raw results: errno and kern_return sets, attempt-to-operation and filter maps, exec query spelling, termination-cause table or ordering eligibility | Keep |
| Restatement | A one-sentence document-local rule using equality, presence, membership in a schema-named set or a constant | Keep only when a production reader consumes it precomputed and removing it would change that reader's wire output; test equipment, recomputing checkers and guide prose do not qualify |
| Constant | A value fixed by the schema | Omit |

### D1. The per-step comparison record

`steps[].comparison` contains `observation`, `observation_basis`,
`operation_relation`, `target_relation`, `order` and `limitations`.

```json
"comparison": {
  "observation": "succeeded",
  "observation_basis": "completed_worker_status",
  "operation_relation": "matched",
  "target_relation": "same_submitted",
  "order": "query_first",
  "limitations": []
}
```

| Path | Type | Rule |
| --- | --- | --- |
| `observation`, `observation_basis` | string | unchanged: the attempt channel classified by the errno set, the `kr=1100` result and the spawned-child rule |
| `operation_relation`, `target_relation` | string | unchanged: the attempt mapped through PW's operation and filter table against the submitted query |
| `order` | string | unchanged: `query_first` or `unestablished` under the existing eligibility rule |
| `limitations` | array of string | may be empty; vocabulary: `query_plan:<code>` with the planner's exclusion codes (`path_unresolved_at_planning`, `prediction_unavailable_pair`, `unrecognized_filter_kind`), and the lifecycle entries `attempt:lifecycle_unresolved`, `attempt:lifecycle_conflicting`, `attempt:unsupported`, `attempt:not_reached` and `attempt:started_without_result`. |

#### Scenario matrix

The S, B and C rows specify 32 scenario expectations: a real-validator plan of
24 steps, a steered-validator plan of 7, and a pre-apply failure. R and T are
two additional failure controls with separate owners.

Response 12 baselines and per-row provenance are retained in
[tests/fixtures/comparison/baseline_response12/](tests/fixtures/comparison/baseline_response12/).
The response 13 expectations retain the five comparison values and prune each
`limitations` list to the vocabulary above. Capture response 13 runs, app
identity and checker output before crediting replacement coverage.

`Query` is a test column, not a record field: use `sandbox_check.outcome` when
`result_source` is `validator` and the outcome is `allow` or `deny`; otherwise
use `unavailable`.

| ID | Scenario | Query | Observation / basis | Op | Target | Order | Limitations |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | allow, read succeeds | allow | succeeded / completed_worker_status | matched | same | query_first | |
| S02 | deny, read EPERM | deny | permission_failure / permission_errno | matched | same | query_first | |
| S03 | allow, mode-000 file EACCES | allow | permission_failure / permission_errno | matched | same | query_first | |
| S05 | query denied path, attempt other path | deny | succeeded / completed_worker_status | matched | different | query_first | |
| S06 | query write, attempt read | allow | succeeded / completed_worker_status | different | same | query_first | |
| S07 | absent path, both channels | unavailable | other_failure / completed_worker_status | matched | same | unestablished | `query_plan:path_unresolved_at_planning` |
| S08 | compound create | unavailable | succeeded / completed_worker_status | unresolved | same | unestablished | `query_plan:path_unresolved_at_planning` |
| S09 | unsupported attempt kind | allow | unavailable / no_completed_worker_result | unresolved | unresolved | query_first | `attempt:unsupported` |
| S10 | sysctl planning exclusion | unavailable | succeeded / completed_worker_status | matched | same | unestablished | `query_plan:prediction_unavailable_pair` |
| S11 | bare `process-exec` query, spawn ok | unavailable | succeeded / spawned_child | different | same | unestablished | |
| S12 | `file-read*` query | allow | succeeded / completed_worker_status | unresolved | same | query_first | |
| S13 | mach deny, kr=1100 | deny | permission_failure / bootstrap_permission_result | matched | same | query_first | |
| S14 | mach unknown service, kr=1102 | allow | other_failure / completed_worker_status | matched | same | query_first | |
| S15 | `process-exec*`, spawn ok, exit 0 | allow | succeeded / spawned_child | matched | same | query_first | |
| S16 | spawn ok, child exits 1 | as S15 | | | | | |
| S17 | spawn of mode-000 target, EACCES | allow | permission_failure / permission_errno | matched | same | query_first | |
| S18 | spawn of absent target | unavailable | other_failure / completed_worker_status | matched | same | unestablished | `query_plan:path_unresolved_at_planning` |
| S19 | ordered unlink of queried path | as S01 | | | | | |
| S20 | `process-exec-interpreter` query, binary spawn | allow | succeeded / spawned_child | different | same | query_first | |
| S21 | `local_name` query, kr=1100 | allow | permission_failure / bootstrap_permission_result | matched | unresolved | query_first | |
| S22 | `none` filter on a file query | allow | succeeded / completed_worker_status | matched | unresolved | query_first | |
| S23 | allow, `access` succeeds | as S01 | | | | | |
| S24 | allow, `open_write` succeeds | as S01 | | | | | |
| S25 | read of the path S19 unlinked, ENOENT | as S14 | | | | | |
| B1 | steered deny, read succeeds, ordered | deny | succeeded / completed_worker_status | matched | same | query_first | |
| B2 | verdict omitted, read succeeds | unavailable | succeeded / completed_worker_status | matched | same | unestablished | |
| B3 | verdict omitted, unlink of queried path | as B2 | | | | | |
| B4 | validator error record | as B2 | | | | | |
| B5 | verdict omitted, read of a path B6 unlinks | as B2 | | | | | |
| B6 | allow, ordered unlink | as S01 | | | | | |
| B7 | allow, read succeeds (control) | as S01 | | | | | |
| C1 | policy fails to compile, nothing runs | unavailable | unavailable / no_completed_worker_result | matched | same | unestablished | `attempt:not_reached` |
| R | `runner_reporting_failed` | no `comparison` object; both fallback levels tested in `ReplyFailureTests` | | | | | |
| T | allow policy, FIFO read starts after release, then worker deadline | allow | unavailable / no_completed_worker_result | matched | same | query_first | `attempt:started_without_result` |

Run every specimen even when its comparison object matches another row.
Assert the distinguishing raw fields: `attempt.requested_action` and unlink
records for S01/S19/S23/S24/B6/B7; `attempt.requested_kind` for S03/S17 and
S07/S18; `attempt.errno` for S14/S25; `attempt.rc` and `child_exit_code` for
S15/S16; `sandbox_check.missing_reason`, `attempt.requested_action` and unlink
records for B2–B5.

#### Specimen mechanics the rows depend on

- A step whose attempt is `unlink` reaches `operation_relation: matched` only
  when its query operation is `file-write-unlink`. S19, S25, B3, B5 and B6
  depend on this.
- Specimen B uses `_test_overrides.validator_executable_path` and
  `validator_io_timeout_ms`. The stub emits deny for B1, allow for B6 and B7,
  and a valid diagnostic record for B4 (`outcome: error`, a string `error`,
  and matching step/query metadata). It omits B2, B3 and B5, flushes the four
  records, then holds stdout open until the validator I/O deadline. The host
  retains and associates those records, releases the worker and builds all
  seven step results. With the worker completing normally, the run ends in
  `normalized_outcome: validator_no_reply`; B1, B6 and B7 retain `query_first`.
  A short batch followed by clean EOF instead produces
  `validator_unavailable`; partial records remain available in either case.
  Assert the timeout outcome and every per-step record in the same reply.
- Specimen B is not idempotent: it unlinks the paths it queries, and a run that
  fails after release still performs its attempts. The case owns recreating its
  files before every run, including after a failed one.

T uses the existing `worker_attempt_in_flight_at_deadline` setup: an existing
FIFO with no writer, an allow policy, a completed validator query, the release
and acknowledgement chain, and a worker deadline while `open_read` is in
flight. The test must establish those raw facts before comparing T. Its later
unreached step may also retain an allow query answer and `query_first`;
failure to complete an attempt does not erase an earlier query. R belongs to the
reply boundary; do not feed it through `comparisonEvidence(...)`.

### D2. The specimen dossier

`data.specimen` is present on every envelope 5 `kind: "run"` result, including
completed runs, `bad_request`, `xpc_error` and pre-execution `tool_error`.
Use one `data` skeleton with no aliases at former paths. Do not embed source
or parameter values.

| `data` key | Disposition |
| --- | --- |
| `app_provenance`, `runner_provenance` | move to `specimen.*`; `runner_provenance` shape unchanged; `app_provenance` keeps `evidence_manifest_path` and `evidence_verify` |
| `policy_augmentation` | move to `specimen.policy.augmentation`, always present |
| `request_path` | move to `specimen.request_path` |
| `runner_service_bundle_id`, `runner_service_name`, `runner_registry_id`, `runner_service_executable` | remove |
| `policy_check` | stay; its `sbpl-check` output is kept verbatim, including that tool's own imports block |
| `runner_client` | stay; gains `request_delivery` |
| `runner_result`, `runner_sandbox_diagnostics`, `sandbox_log_capture`, `timeout_ms` | stay; `runner_sandbox_diagnostics` loses its `worker_pid`, `capture_status` and `first_deny` copies; `timeout_ms` keeps its meaning |
| `runner_startup_diagnostics` | remove |

```json
"specimen": {
  "request_path": "tests/fixtures/pw_runner/specimen_file_read_deny.json",
  "policy": {
    "augmentation": { "status": "not_requested", "applied": [],
                      "original_sha256": "…", "applied_sha256": "…", "error": null },
    "imports": {
      "status": "complete",
      "closure_sha256": "…",
      "records": [
        { "name": "system.sb", "resolved_path": "/System/Library/Sandbox/Profiles/system.sb",
          "sha256": "…", "size_bytes": 12345, "mtime_unix": 1700000000, "error": null }
      ],
      "cycle": null,
      "exceeded": null,
      "failure": null
    }
  },
  "host": { "macos_version": "14.8.3", "macos_build": "23J220", "kernel_release": "23.6.0",
            "arch": "arm64" },
  "runner_provenance": { "…": "unchanged shape" },
  "app_provenance": { "evidence_manifest_path": "…", "evidence_verify": null },
  "binaries": { "service": null, "worker": null, "validator": null }
}
```

Example with a worker executable override:

```json
"binaries": {
  "service": null,
  "worker": { "path": "/tmp/pw-probe-runner", "actual_sha256": "…",
              "baseline_sha256": "…", "verification": "mismatch",
              "reason": "selected bytes differ from the manifest baseline" },
  "validator": null
}
```

| Path | Type | Rule |
| --- | --- | --- |
| `request_path` | string or null | the path given to `run`; null when no path was given (see the failure table) |
| `policy.augmentation` | object | always present; `status`, `applied`, nullable `original_sha256` and `applied_sha256`, and nullable `error`, under the failure rules below. Retain these hashes on runs with no reply |
| `policy.imports.status` | string | `complete`, `incomplete`, `failed`, `not_applicable`, under the scan rules below |
| `policy.imports.closure_sha256` | string or null | over the applied source and successfully hashed import records whenever the scan ran; `status` says whether the scanned closure is complete |
| `policy.imports.records[]`, `cycle` | as `sbpl-check` | unchanged shapes |
| `policy.imports.exceeded` | string or null | the first bound hit: `depth` or `count`, the scanner's existing bounds |
| `policy.imports.failure` | string or null | the first scan problem, including why the scan could not start; null for a complete scan or an ordinary absence of source |
| `host.macos_version`, `macos_build`, `kernel_release`, `arch` | string or null | `kern.osproductversion`, `kern.osversion`, `kern.osrelease`, `hw.machine`; null when the read fails. Document the mechanism once; emit no `basis` or sandbox-library identity field |
| `binaries.<role>` | object or null | null when the selected path is the app manifest's uniquely selected, correctly typed entry for that role; otherwise `path`, `actual_sha256`, `baseline_sha256` from the manifest entry, `verification` of `match`, `mismatch` or `unavailable`, and `reason`, null only for `match` |

Host facts, binaries and the imports scan are gathered before invocation.
Dossier collection failures are recorded and do not change whether the request
is admitted or the runner is invoked. For a controller refusal, collect what
is available without invoking the runner. All dossier keys stay present;
unavailable scalar facts are null, lists are empty when no records exist, and
statuses explain unavailable collections. `app_provenance` may remain null,
as in its existing shape.

#### Request and augmentation failures

Hash only string source bytes that actually exist. `original_sha256` identifies
the pre-augmentation string; `applied_sha256` identifies the post-resolution
string selected for invocation, including the unchanged source. Neither hash
identifies parameters or proves worker compilation. Augmentation is atomic:
failure reports no applied names and no applied hash.
On completed runs, `applied_sha256` equals the reply's `policy_sha256`.

| Request state | Augmentation | Imports |
| --- | --- | --- |
| String source, no augments (also null or empty augments) | `not_requested`, `applied: []`, equal source hashes, `error: null` | scan that source |
| Augments successfully applied | `applied`, applied names and hashes; original hash null if no original string existed | scan the resulting source |
| Augment resolution refused | `failed`, `applied: []`, original hash if available, applied hash null, refusal diagnostic | `not_applicable`, `failure: augmentation_failed` |
| Missing/malformed policy or source, no augments applied | `not_applicable`, `applied: []`, both hashes null, `error: null` | `not_applicable`, no records or hash |
| No request value: the file is absent, unreadable, not JSON, or not an object | `not_applicable`, `applied: []`, both hashes null, `error: null` | `not_applicable`, no records or hash |
| No request path: the argument is missing or a flag value is invalid | as above, with `specimen.request_path: null` | `not_applicable`, no records or hash |
| Runner refusal or XPC failure after successful resolution | preserve the collected record | preserve the collected record |

Every imports object carries its status, records, cycle, closure hash,
exceeded and failure keys. A scan that does not run has `records: []`,
`cycle: null`, `closure_sha256: null` and `exceeded: null`.

`cmd_run` writes the uniform envelope for missing arguments, invalid flag
values, absent request files, invalid request objects and runner-selection
failures, including manifest failures. Keep the `cli.rs`
catch-all for errors that escape `cmd_run`. These failures use
`normalized_outcome: tool_error`, exit 2 and null execution records;
`bad_request` remains exit 1. Remove `data.error`; use `result.error`.

After runner selection and augmentation, serialize the request once into a
held string, including when no patch was needed. Scan that string and deliver
its bytes to both readers. `specimen.request_path` remains the original path;
replacing the file during collection must not change submitted bytes.

Support these helper input forms:

- `pw-runner-client run [options] <service> <request.json>`: existing file input.
- `pw-runner-client run [options] --request - <service>`: new stdin input.
- `sbpl-check --request <path|->`: existing file input, with `-` selecting stdin.

The client parses `--request -` before the service name, accepts only `-` as
that flag's value, and rejects duplicate or mixed input forms and extra
arguments. Its positional request argument remains a literal file path.
Both tools read stdin to EOF. `policy-witness run` uses stdin for normal
invocation and the `xpc_error` fallback; delete `write_temp_request`.
No `policy-witness run` path writes a temporary request file.
`policy-witness runner verify` retains its file under `pw-runner-verify`.
Preserve augment resolution against the app root.

#### Request delivery and transport failures

Spawn the client with piped stdin. A writer thread writes the held request
string and closes stdin after the last byte; the main thread collects stdout
and stderr concurrently and waits for exit. The shipped client reads its whole
request before connecting or writing output.

Keep `--timeout-ms`'s default, minimum and reply-wait meaning. Add no controller
deadline or log-supervisor dependency. Keep `JsonOutputCapture`'s parsing,
diagnostic retention, capture limits and collection behavior unchanged.

`data.runner_client` gains `request_delivery: { "bytes_written": n, "error": null | string }`.
On a `kind: run` envelope, a nonnull `runner_client` always carries this object;
before client invocation, `runner_client` itself is null. The shared capture
type permits null delivery for file-input calls; `runner verify` uses that
form but does not emit the capture in its management envelope.
It is a controller observation: an accepted pipe write
and a closed writer do not prove that the client read the bytes or that XPC
delivered them. Existing capture and timing fields and the meaning of
`exit_code` are unchanged.

A delivery error produces `result.ok: false`,
`result.normalized_outcome: tool_error`, exit 2 and a controller diagnostic.
It takes precedence over any captured reply. Retain that reply unchanged in
`data.runner_result` with the full capture; gate interpretation on its response
version. A broken pipe must not terminate the controller. When delivery
completes, use the existing runner-result and version-result selection;
nonzero client exit alone must not overwrite a valid failure reply.

Invoke fallback compilation only for a supported `xpc_error` reply. Deliver
the same held string to `sbpl-check --request -` using the writer thread.
Helper delivery or launch failure produces `PolicyCheckCapture::unavailable`
and retains the original runner reply. Client delivery error alone does not
trigger fallback compilation.

#### Binary selection and comparison

The service path comes from the selected runner's executable path. The
controller reads `_test_overrides.worker_executable_path` and
`_test_overrides.validator_executable_path` from the same parsed request value
that is serialized for invocation.
This is an observation of requested paths; the runner retains admission
ownership. Apply these rules independently to the two helper roles:

| Override value | Binary observation |
| --- | --- |
| Absent or null override object/key | Use the selected XPC bundle's `Contents/MacOS` helper. |
| Nonobject override container or nonstring nonnull key | `path: null`, `actual_sha256: null`, `verification: unavailable`, with a type diagnostic; a malformed container affects both roles. |
| String containing NUL or exceeding the runner's 1023-byte UTF-8 path echo bound | Null path and actual hash, unavailable with a NUL/length diagnostic; do not echo, truncate or read the path. |
| Empty or relative string | Retain the submitted path, null actual hash, unavailable with an empty-path or unknown runner-working-directory diagnostic. Do not resolve it against the controller's working directory. |
| Absolute string within the echo bound | Apply the manifest-path null rule below; otherwise retain the path and hash a readable regular file. A missing, unreadable or nonregular file has a null actual hash and an unavailable reason. |

Retain any available baseline hash in unavailable records. A present unusable
override never falls back to the bundle helper. These observations do not
reject or rewrite the request, enforce executable permission, or predict
runner admission. Hashing does not prove launch or mapped bytes.

Select the built-in service entry and all three binary baselines by exact
`rel_path`. Define these fixed shipped paths in `app_layout.rs`, relative to
the app root:

| Role | `rel_path` | Required `kind` |
| --- | --- | --- |
| Service | `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner` | `xpc-service` |
| Worker | `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner` | `xpc-embedded-helper` |
| Validator | `Contents/XPCServices/PWRunner.xpc/Contents/MacOS/sb_api_validator` | `xpc-embedded-helper` |

Add a uniqueness-checking exact-path lookup in `evidence.rs`. Require exactly
one entry at the expected path, then check its kind. Missing entries, duplicate
paths and wrong kinds make that role's entry unusable. Do not select or fall
back by `id`, `bundle_id` or `service_name`; no new `service_name` decoding is
needed. Built-in and BYOXPC runs use the same baseline paths, including the
bundle-local validator rather than the app-level helper.

An unusable helper entry makes only that role's baseline unavailable and does
not prevent invocation. BYOXPC selection is independent of all three baseline
lookups. A missing or malformed `sha256` string makes a requested hash comparison
unavailable, not the entry unselectable; accept 64 hexadecimal digits and
compare decoded hash values. For a parsed manifest, neither hash availability
nor helper-entry lookup failures gate built-in service selection.

When the selected path is the uniquely selected, correctly typed manifest
entry for that role, emit null and do not hash the binary. This requires no
hash comparison. Keep `PW_VERIFY_EVIDENCE` behavior unchanged.

For an executable override or BYOXPC copy, hash the selected file before
invocation and compare against the baseline entry's hash: equal hashes produce
`match`; complete hashes that differ produce `mismatch`. An unreadable selected
file, or a missing, unreadable
or invalid manifest or entry, leaves `actual_sha256` or `baseline_sha256`
null with `verification: unavailable` and a reason that identifies selection,
manifest or file-read failure. A mismatch reason identifies the baseline
comparison. `path` is null when no path was selected or it cannot be represented
under the rules above; a known but unreadable path stays present. Neither mismatch
nor unavailable changes the run outcome. The manifest's UUID and entitlements
are not echoed; existing runner provenance stays separate.

#### Controller reads on a run

Attempt to parse the app evidence manifest once in `cmd_run`, before runner
selection, and retain either the parsed value or its error for selection,
app provenance and binary records. For built-in selection, the service entry
selected above must also supply a nonempty, NUL-free `bundle_id`; a missing,
empty or NUL-containing value makes it unusable for connection. Use `bundle_id`
as the XPC connection name and resolve the executable path from `rel_path`.
Baseline hash lookup does not require `bundle_id`.
Delete `resolve_pw_runner_bundle_info` and `PWRunnerBundleInfo`.
`plist.rs` and `read_bundle_info` stay for BYOXPC install and verify.

A missing, unreadable, malformed or unsupported-schema manifest, or a missing
or unusable built-in service entry, fails built-in selection through `cmd_run`'s
uniform `tool_error` envelope and exit 2. Include the manifest path in the
diagnostic, retain available dossier facts and do not invoke the client.
`app_provenance` is null when the manifest could not be parsed and accepted.

BYOXPC selection continues through its existing registry, signature and
entitlement checks without an app manifest. If those checks pass, invoke the
runner. If the manifest itself is unavailable, all three binary roles are objects
with `verification: unavailable`, `baseline_sha256: null` and a manifest
diagnostic; retain selected paths and actual hashes where observable.
Do not emit a null binary record without the manifest entry that justifies it.

`app_provenance` contains only `evidence_manifest_path` and `evidence_verify`.
Keep `runner_provenance` unchanged.

#### Import collection and bounds

Collect the dossier import inventory before invocation from the source
selected by the controller. Keep `data.policy_check`'s separate `imports`,
`imports_cycle` and `imports_truncated` unchanged on fallback paths; otherwise
`policy_check` is null. Do not copy its inventory into the dossier or treat
disagreement between the scans as an error. Neither scan identifies what the
worker's compiler read. Preserve `sbpl-check` output during the shared-module
extraction.

Reuse the scanner's import depth 8, import count 64 and 4 MiB source cap.
Keep the `helper_import_depth`, `helper_import_count` and `helper_source` ids
and values in `docs/limits.json`; update their descriptions to include the
dossier. Add no file, total-byte or time budget.

In `dfs_visit_import`, open each unique resolved import once. Use `fstat` to
check that its descriptor is a regular file, then hash and lex the same bytes.
A nonregular file produces
an error record and an incomplete inventory. Preserve the existing search
paths: the two system profile directories and absolute import paths.

`complete` means the scanner exhausted the literal import closure under its
documented search paths with no unresolved names, cycles, nonliteral import
forms, decoding errors or exceeded bounds. It does not mean compiler-complete:
macro evaluation and the files the worker compiler actually reads are outside
this observation. An incomplete traversal keeps every collected record and a
hash of the source plus successfully hashed imports under the existing closure
hash algorithm, with `exceeded` naming the first bound hit, `depth` or
`count`. Top-level imports have depth 0; depth 8 is recorded without
expansion, and each emitted unique record, including unresolved and error
records, counts toward 64. `failed` means collection could not start because
of a collector failure; `not_applicable` means no post-resolution source was
available. Neither receives a closure hash. Nonliteral forms and invalid
UTF-8 must not silently count as completion. The scan is synchronous, with no
background task or new shipped helper.

### D3. Invariants

- Producer: `PWRunnerStepResult` has no `drift` or `deny_signal` property;
  `PWRunnerComparison` has no `prediction`, `conclusion`, `scope`, `drift` or
  `obligations`; `PWRunnerAttemptResult` has no `exit_code`, `syscall_errno`
  or `native_rc`; `PWRunnerSandboxCheckResult` has no `scope`;
  `PWRunnerRunResult` has no `deny_signal_total` or `comparison_conditions`;
  `PWRunnerSignalResult` and `Signals.swift` are gone. The reply-shape golden
  (`tests/fixtures/contract/response_shape.json`) records the response 13
  shape.
- Encoder: reject `limitations` strings outside D1's vocabulary and retain
  the `query_first`, disposition and reply-degradation checks on remaining
  properties. Remove checks on deleted properties. Assert absence of removed
  wire keys in encoded fixtures and the shape golden; do not add a strict
  unknown-key Swift decoder. Swift keeps ignoring unknown keys after the
  version gate.
- Reply degradation: `runner_reporting_failed` omits every `comparison`, even
  when `steps: []`. `evidence_retained: false` still withholds step and
  subprocess evidence.
- Consumer (`tests/lib/consumer.py`): applies D5's envelope/response gates and
  reports a different version as `unsupported`; rejects removed keys at the
  specific wire paths in R1, including `comparison.prediction`,
  `comparison.obligations` and reply-level `comparison_conditions`, and any
  `limitations` string outside D1's vocabulary; validates `observation`,
  the two relations and `order` against the raw channel fields and
  `ordering`.
- Controller: `permission_failures_without_record` reads `comparison.observation`;
  `validate_disposition` also checks the lifecycle entries in
  `comparison.limitations`. Failed disposition validation withholds the
  projected disposition and termination cause. Preserve those lifecycle
  checks and the reporting-failure exception. `runner_startup_diagnostics`
  and the `worker_pid`, `capture_status` and `first_deny` copies in
  `runner_sandbox_diagnostics` are removed; the log window still takes
  the worker PID from the reply internally. These readers and every other
  semantic projection use the response-version gate.

### D4. Assertions, recipes and reading rules

Tests assert the evidence each scenario establishes, by field. Guide recipes
select explicit field combinations, such as `sandbox_check.outcome: deny`
plus `observation: succeeded`, and show submitted-scope relations and order.

Put these reading rules in one guide section, in this order:

1. The query channel's answer is `sandbox_check.outcome` when `result_source`
   is `validator` and the outcome is `allow` or `deny`; otherwise no prediction
   was available and `sandbox_check.missing_reason` says why.
2. `attempt.missing_reason` explains an unavailable attempt channel.
3. A `permission_failure` or `other_failure` observation, or an exec attempt
   whose spawned child exited nonzero, does not attribute the failure to the
   sandbox; attribution needs a captured denial record, and
   `permission_failures_without_record` lists the steps that have none.
4. A `path` query, or an attempt whose mapped filter is `path`, never
   establishes that both channels resolved the same object at runtime.
5. No record establishes that the state the query saw is the state the
   attempt met; nothing in a reply discharges this.
6. When a query has `filter_kind: path`, a nonnull `filter_value` and no
   `query_plan:*` limitation, and any step's attempt is a worker `unlink` of
   that same submitted path with `outcome: ok` and `rc: 0`, the target was
   removed during the run; `order` says whether the removal followed the
   query, and the unlink attempt's step is the step that removed it.
7. A `process-exec*` query predicts target admission only, not every spawn
   prerequisite; the child's result is in `attempt.rc` and
   `attempt.child_exit_code`.
8. A `file`/`create` attempt has no single query operation, so
   `operation_relation` is `unresolved`.
9. A query operation containing `*`, other than `process-exec*`, resolves to
   no single attempt operation.
10. `target_relation: unresolved` means the attempt's mapped filter kind
    differs from the query's `filter_kind`, or `filter_value` or
    `requested_path` is absent; those fields show which.
11. `sandbox_check.path_diagnostics.realpath_resolved` null on a query the
    planner did not exclude means the host could not resolve the submitted
    path after the run.
12. An attempt the worker does not support has `attempt.outcome` and
    `missing_reason` saying so, and both relations `unresolved`.

### D5. Versioning

- Response schema 12 → 13: the D1 comparison record, R1 wire removals, and
  retirement of `libsandbox_unavailable` and `bootstrap_port_failed`.
- Controller envelope 4 → 5: the D2 shape and request-delivery contract.
- Request schema, request-version admission behavior and worker ABI unchanged.
  The exact-version rule here governs semantic readers of runner responses
  and controller envelopes; it does not reject existing request-1 specimens.
  The worker ABI's existing equality tripwire remains independent.
- `docs/contract.json` is edited, and `python3 docs/generate_contract.py` run,
  in the same increment as the implementation that emits the new shape.
- [CONTRACT.md](docs/CONTRACT.md). "When a number moves" becomes:
  "Bump a number when the rules for reading change: a field removed, its type
  or meaning changed, or a new requirement placed on readers. An added field
  alone does not require a bump. An absent field means unknown, never false.
  An additive contract change may also carry a bump, recorded in
  `docs/contract.json`.
  Bump the worker ABI on any change to the shared-memory layout or handshake."
  The "Reading older replies"
  section, the historical version tables and "Naming numbers in prose" are removed.
  A "Supported versions" section replaces them: "Semantic readers of runner
  responses and controller envelopes accept exactly the versions in
  `docs/contract.json`;
  another version is unsupported. Raw transport retains the received bytes
  without interpreting unsupported records. Stored evidence keeps its bytes;
  current semantic readers reject unsupported versions. Request admission and
  the worker ABI follow their own contracts." "What each number identifies" gains
  one sentence per contract. Response: "`steps[].comparison` records the
  attempt channel's classified observation, the submitted-scope relations, the
  order PW established and the planner's exclusion or lifecycle limitations."
  Envelope: "`data.specimen` is the dossier: request path, policy
  augmentation and imports, host facts, runner and app provenance, and hashes
  of any selected binary the app manifest does not describe; the raw runner
  reply, transport, diagnostics and log capture stay beside it."

#### Reader boundaries and unsupported results

Check a version before interpreting its record. Missing or noninteger version
fields are malformed; other integer versions are unsupported. For an envelope,
check its version first, then any nonnull runner reply. A current run envelope
with `runner_result: null` is valid when execution produced no reply; selectors
return no runner evidence. Unsupported documents yield one version error,
without downstream shape errors or recovered claims. No branch interprets a
previous version.

| Reader or boundary | Required change and result |
| --- | --- |
| Swift `PWRunnerRunResult` decoder/encoder | Require `PWContract.responseSchema` before semantic decoding/encoding; other versions fail with an `unsupported` diagnostic. Remove the 8/9/10 gates and legacy-only decode fallbacks; current invariants apply directly. |
| Python `consumer.py` public document readers | Share envelope/response gates; `validate` returns the single version error, and evidence accessors refuse unsupported input. `select` operates on already validated steps. Bare replies require only the response gate. |
| Python lifecycle adapter/oracle, blackbox and path/log evidence helpers | Route public document entry points through the same gates before projecting; remove legacy projections and fallbacks. Standalone raw-record validators do not pretend a fragment is a versioned document. Audit direct callers as part of I3. |
| Rust `run_flow.rs`, including `complete_execution`, `project_disposition` and log correlation | Gate received reply version before reading summaries, worker PID, lifecycle or comparisons. Remove the pre-response-10 disposition fallback. Unsupported replies remain intact in `data.runner_result`; when transport completes, the controller reports `result.ok: false`, exit 1, `result.normalized_outcome: unsupported_runner_response`, a version diagnostic and no runner-derived diagnostics or log capture. Malformed version fields use `malformed_runner_response`, also with `ok: false` and exit 1. A concurrent delivery failure takes precedence as `tool_error`; do not interpret the unsupported/malformed reply. |
| Swift `pw-runner-client` and Rust `runner_client.rs` capture | Preserve received bytes/JSON as transport, including unsupported versions and unfamiliar strings. They do not reinterpret or coerce the version. Client-generated failure replies use the current response schema and the empty-step and reporting-failure rules. |
| Requests, worker ABI, evidence manifest and validator transcript | Retain their existing separate admission/reading rules. This plan's equality rule is not a new request-version or nested-transcript-version restriction. |

`unsupported_runner_response` and `malformed_runner_response` are
controller-only outcomes, like `tool_error`; do not add them to Swift's
`NormalizedOutcome` or the runner-outcome matrix in `tests/COVERAGE.md`.
Document them, their version diagnostics and exit 1 in `controller/README.md`'s
output contract and the supported-reader rules in
`tests/FAILURE-PROPAGATION-CONTRACT.md`. `malformed_runner_response` covers
missing or noninteger response versions in received JSON; retain the existing
`runner_output_not_json` handling when no JSON reply was parsed.

For an unsupported/malformed reply, the dossier retains controller-collected
facts; no runner-derived value is computed. Rust transport tests preserve unknown
bytes while semantic tests require the unsupported result. Independently test
an old and a future response, an old and a future envelope, a current envelope
containing an unsupported reply, malformed version fields, and no reply. Use
current-version fixtures for unfamiliar-value transport tests.

Stored evidence under `records/`, retained test output and release acceptance
artifacts keeps its bytes; do not rewrite it for the new versions.

## REMOVAL

"Removed" means the wire keys, the code that computes them, the invariants
that police them, the tests that assert them, and every active surface that
names or promises them: CLI help, diagnostics, test messages, comments,
docstrings, identifiers, filenames, registries and documentation. R9 lists
what stays.

### R1. Wire keys

| Key | Where | Disposition |
| --- | --- | --- |
| `steps[].drift`, `steps[].comparison.conclusion`, `steps[].comparison.scope`, `steps[].comparison.prediction`, `steps[].comparison.obligations`, `comparison_conditions` | runner reply | removed |
| `limitations` strings `state_stability_unestablished`, `runtime_target_identity_unestablished`, `sandbox_attribution_unestablished`, `attempt_mutation_order_unestablished`, `query_attempt_order_unestablished` | runner reply | removed |
| every other `limitations` string outside D1's vocabulary: `prediction:*`, non-lifecycle `attempt:*`, `operation:*`, `target:*`, `exec_query_not_full_spawn_prediction`, `compound_attempt`, `attempt_operation_unestablished`, `broad_query_operation`, `query_filter_scope_unestablished`, `submitted_target_unavailable`, `exec_result_failed_after_spawn`, `host_path_resolution_changed` | runner reply | removed |
| `steps[].deny_signal`, `deny_signal_total` | runner reply | removed |
| `steps[].attempt.exit_code`, `steps[].attempt.syscall_errno`, `steps[].sandbox_check.scope`, `steps[].attempt.native_rc` | runner reply | removed |
| `data.runner_startup_diagnostics` | controller envelope | removed |
| `data.runner_sandbox_diagnostics.worker_pid`, `.capture_status`, `.first_deny` | controller envelope | removed |
| `data.app_provenance.app_bundle_id`, `.app_binary_rel_path`, `.app_entitlements`, `.evidence_notes` | controller envelope | removed |
| `data.policy_augmentation`, `data.runner_provenance`, `data.app_provenance`, `data.request_path` | controller envelope | relocated under `data.specimen` |
| `data.runner_service_bundle_id`, `data.runner_service_name`, `data.runner_registry_id`, `data.runner_service_executable` | controller envelope | removed |
| `data.error` on the pre-execution `tool_error` envelope | controller envelope | removed; use `result.error` |

`steps[].sandbox_check.native_rc` stays, including its validator-record
equality checks in ordering eligibility. Only the attempt-side alias is removed.

### R2. Producer code

| File | Symbol or site | Disposition |
| --- | --- | --- |
| `runner/Sources/PWRunnerCore/PWRunnerAPI.swift` | `PWRunnerComparison.drift` (~906), `.conclusion`, `.scope`, `.prediction` | delete |
| same | `PWRunnerStepResult.drift`: init parameter, `CodingKeys.drift`, explicit-null `encode` branch, `decodeIfPresent` (~929–987) | delete, with no legacy-only property or version-gated read |
| same | `PWRunnerStepResult.deny_signal` (~921–982), `PWRunnerRunResult.deny_signal_total` (~1720–1873), `PWRunnerSignalResult` (~857) | delete |
| same | `PWRunnerAttemptResult.exit_code`, `.syscall_errno`, `.native_rc` and its explicit-null encode branch (~704–803); `PWRunnerSandboxCheckResult.scope`, `PWRunnerWire.sandboxCheckScopePost` (~41) | delete |
| same | encoder clauses `steps.allSatisfy({ $0.comparison == nil && $0.drift == nil })` (~1817) and `comparison.conclusion != "disagreement", step.drift != true` (~1847) | rewrite per D3 |
| same | `PWRunnerRunResult` decoder/encoder version gates and legacy-only field fallbacks | exact response gate and current invariants per D5 |
| same | `AttemptOutcome.bootstrapPortFailed` and the `libsandbox_path` row of the `_test_overrides` table (~213) | delete |
| same | doc comments ~133, ~157, ~726 | reword |
| `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift` | `ComparisonEvidence.conclusion` (~837) and `.prediction`; the `state`, `identity`, `attribution` and `mutation` members and their enums (~816–820); `reportsTargetRemoval` (~808) and the `runAttempts` parameter of `comparisonEvidence` (~895); every `limits.append` of a string outside D1's vocabulary (~904–1000); `renderLimitations()` (~843); `drift: comparison.drift` (~632); `deny_signal: nil`, `deny_signal_total: nil` (~162, ~631); comments ~24–26, ~722, ~763, ~890 | delete or reword; `renderLimitations` returns the `query_plan:*` entry plus the lifecycle entries and nothing else |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift` | reply degradation; the `host_path_resolution_changed` append (~424); the `SandboxLib.load` call site and its `libsandbox_unavailable` return | remove drift clearing and withhold comparisons through both fallback levels; delete the limitation append, load call and refusal |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift` | unused execution helpers and exclusive bindings/constants; retained exclusion-set comments | remove helpers per S1/S2 below; reword retained comments |
| `runner/Sources/PWRunnerCore/PathUtils.swift` | `observedPathForFd`, its `fcntl_getpath` binding, `warmFirmlinkMap` | remove; keep production path helpers and lazy firmlink map |
| `runner/Sources/PWRunnerCore/SandboxApply.swift` | `applySandboxPolicy`, `ApplyError` | remove; keep policy hashing in this file |
| `runner/Sources/PWRunnerCore/Signals.swift` | whole file; no caller under `runner/Sources` | delete, and its `XPC_RUNNER_SIGNALS_FILE` line in `build.sh` |
| `runner/Sources/PWRunnerCore/SandboxLib.swift` | whole file | delete with its symbol resolutions, `libsandbox_path` override and `libsandbox_unavailable` outcome |
| `controller/src/run_flow.rs` | `RunnerStartupDiagnostics` (~133), `fallback_policy_note` (~162) and their construction in `cmd_run` (~379–396); `RunnerExecutionDiagnostics.worker_pid` (~98), `RunnerLogDiagnostics.capture_status` (~112), `first_deny` (~116) and `DenyEventReference` | delete; the log window still takes the worker PID from the reply internally, and `policy_check` keeps the fallback compile record |
| same | `write_temp_request` and its call in `cmd_run` (~353–358); `load_app_provenance`'s own manifest read (~141–143) and the four echoed header fields of `AppProvenance` (~41–45) | delete; `load_app_provenance` takes the parsed manifest |
| `controller/src/app_layout.rs` | `resolve_pw_runner_bundle_info` (~62–77), `PWRunnerBundleInfo` (~13) and the `plist` import | delete; define the three fixed shipped relative paths for selection and baselines |
| `controller/src/evidence.rs` | manifest entry lookup for built-in selection and binary baselines | add exact `rel_path` lookup that rejects duplicate matches; check the role's required `kind` |
| `controller/src/runner_select.rs` | `builtin_runner_target`'s manifest read (~159–161) and Info.plist-based entry selection | takes the parsed manifest from `cmd_run`, selects the fixed service path with uniqueness/kind checks, validates `bundle_id` for the connection name, and resolves the executable from `rel_path` |
| `controller/src/policy_check.rs` | `run_policy_check(request_path)` (~65) | takes the held request string and delivers it on stdin with `--request -` |
| `controller/src/bin/sbpl-check.rs` | `--request <path>` read (~518, ~543) | add `--request -` reading stdin to EOF; file input retained for direct use |

Production C worker and validator behavior is unchanged. S2 removes the unused
C query shim and its build wiring; it does not remove the production validator.
The dossier is Rust only.

#### S1–S3. Unused Swift execution helpers

The identifiers here refer to the second sweep in `FIVE-FOLLIES.md`, not the
D1 scenario matrix. Remove only the unused implementation and its exclusive
dependencies; the enclosing source files also contain production code.

- **S1 — attempts.** In `ProbeRunner.swift`, remove `runAttempt`, its private
  `runFileAttempt` and `runMachLookupAttempt` branches, and the exclusive
  `bootstrap_look_up` binding. In `PathUtils.swift`, remove `observedPathForFd`
  and its `fcntl_getpath` binding, plus the uncalled `warmFirmlinkMap` entry
  point. Keep `canonicalizePath`, `parentRealpathResolved`, the lazy firmlink
  map and fallback data, `firmlinkResolved` and `wellKnownSymlinksResolved`:
  they serve query planning and host path diagnostics. Remove
  `bootstrap_port_failed`; keep the C worker's `lookup_failed` outcome with
  its `task_get_special_port` diagnostic.
- **S2 — queries.** Remove `runSandboxCheck`, `currentProcessIsSandboxed`,
  their `pw_sandbox_check`/`pw_sandbox_check_noarg` bindings, private filter-ID
  constants and exclusive `predictionUnavailableRC` sentinel. Remove the
  entire `runner/Sources/PWSandboxCheckShim/` target, including its header;
  remove its target and dependency from `runner/Package.swift`. In `build.sh`,
  remove `XPC_RUNNER_SANDBOX_SHIM`, its existence check, `shim_obj` compilation
  and the corresponding link argument. Retain `PWCWorkerShim` and its wiring.
  Update `tests/suites/source_drift/check.py`'s `SHIM_DIRS`, shim-source parser
  and explanatory text to describe the surviving source set. Keep its
  build-versus-tree check and planner mutation controls. In `ProbeRunner.swift`,
  retain `validateSandboxChecks`, `knownFilterKinds`,
  `PredictionUnavailablePair` and `predictionUnavailableOpFilters`, including
  the guide/set consistency check. Production queries still use
  `sb_api_validator` through `planValidatorQueries`; neither is replaced by
  a new Swift query path.
- **S3 — sandbox application.** Remove `applySandboxPolicy` and `ApplyError`
  from `SandboxApply.swift`. Keep `computePolicyHash`, `PolicyHashError` and
  `sha256Hex`, along with the file's build entry: the service uses that code
  for source identity and structural policy refusal. Remove
  `SandboxApplyTests.swift` and its `main.swift` registration, and the
  `runner/AGENTS.md` paragraph that links it. Remove `SandboxLib.swift`, the
  `libsandbox_path` test override and `libsandbox_unavailable`.

Remove imports and comments made obsolete by these deletions. Keep the existing
filenames for files that retain production code.

#### The host invariance rule and its checks

Rewrite the service header to state that the XPC host remains unsandboxed
and does not link, load or call libsandbox. Link the live
`runner_apply_isolation_v3/deny_default_v3_worker_reply` host/worker case and
`runner_c_worker_harness/bare_deny_default` direct-worker control. Do not
attribute XPC-host coverage to the direct-worker control or assert comment
text or delimiters.

- **Source (`source_drift`, in its existing runner-source case).** Check native
  API use under `runner/Sources/`, with an explicit sandbox SPI name set:
  `sandbox_check`, `sandbox_apply`, `sandbox_compile_string`,
  `sandbox_create_params`, `sandbox_set_param`, `sandbox_free_params`,
  `sandbox_free_profile`, `sandbox_free_error`. Reject declarations/bindings
  to those native symbols (including Swift `@_silgen_name` bindings), direct
  calls, literal symbol lookups through `dlsym`, and literal libsandbox paths
  passed to `dlopen`. Include simple named constants supplying those lookup
  arguments. Permit `sandbox_check` schema properties, coding keys and
  diagnostic labels, plus comments, SBPL text and explanatory strings. Do not
  ban unrelated `dlopen` calls or arbitrary `@convention(c)` declarations.
  Source controls must accept the retained schema/planner code and explanatory
  text, and reject reintroduced bindings, calls and dynamic lookup/load forms,
  including constants feeding them. Handle comments and string literals by
  context. Document that the check does not cover computed library/symbol
  names or perform complete Swift/C analysis. The worker and validator
  C sources are outside this host-source scope and retain their native calls.
  The failure message identifies the prohibited native use and the host
  invariance rule.
- **Binary (`preflight`, in its existing artifact case).** Require `nm -u`
  on the shipped `PWRunner.xpc` executable to report no undefined `_sandbox_*`
  symbol. Record the check failing on the pre-removal build and passing after
  removal. Do not substitute `otool -L`, which misses libSystem calls and
  dynamic symbol lookup.

Add both assertions to existing catalog cases. Retain these live controls:
`bare_deny_default`, `proceed_under_bare_deny_default`,
`max_slots_deny_default`, `deny_default_v2_worker_reply`,
`deny_default_v3_worker_reply` and
`witness_contract/shm_sentinel_under_deny_default`.

### R3. Controller implementation and fixtures

Remove `project_disposition`'s pre-response-10 branch and gate semantic work
in `complete_execution` and downstream diagnostics/log paths before projecting
a reply. Update the inline Python in `run_flow.rs` ~2321 and ~2523 and
`log_replay_tests.rs` ~172 from `recover_evidence`/`validate_evidence_shape`
to `validate`/`denials` in the same increment as the consumer changes.

Implement the dossier, shared request delivery and manifest flow in D2 through
`run_flow.rs`, `runner_client.rs`, `policy_check.rs`, `runner_select.rs` and
`app_layout.rs`, with manifest entry lookup in `evidence.rs`.
Update unsupported/malformed reply and current-version fragment-transport controls.

`runner_commands.rs::cmd_runner_verify` is the helper's other production caller.
Keep its file-input call supported, its 5-second default and its existing data
shape. Its temporary request file is outside the `policy-witness run` no-temp-file
rule; it has no stdin delivery observation or delivery-failure branch.
Temporary-directory/write and client-launch errors retain `tool_error`, exit 2.
Apply D5's version gate before reply projections: unsupported or malformed
versions report the corresponding controller outcome, `ok: false`, exit 1
and null `runner_pid`, in the existing verification data shape.

Fixtures that construct steps with removed keys
become current-shaped; the legacy-shape case at ~2071 is deleted:
`controller/src/run_flow.rs` ~1638, ~2022, ~2071, ~2252, ~2394, ~2593, ~2652;
`controller/src/runner_client.rs` ~163–173; `controller/src/log_replay_tests.rs`
~14–22.

### R4. Shared consumers

| File | Sites | Disposition |
| --- | --- | --- |
| `tests/lib/consumer.py` | `comparison_groups` (~79–80); `drift` in step answers (~98); `conclusion` set (~185); reporting-failure rule (~194); projection check (~213–215); disagreement rejections (~286, ~361); mutation rule (~296); version branches at 7, 8, 9, 12 | rewritten per REPAIR I3 |
| `tests/lib/blackbox.py` | explicit-null check (~110–111); drift checks (~154–160); alias-agreement rule; `effective_filter_value` fallback | delete |
| `tests/lib/lifecycle_oracle.py` (~338–341), `tests/lib/path_diagnostics_contract.py` (~26–32) | constructed steps carry `drift` and `conclusion` | update the constructed shape |
| `tests/lib/lifecycle_contract.py`, `lifecycle_adapter.py`, `lifecycle_oracle.py`, document readers of log/path evidence | legacy projection rules and document entry points | remove legacy interpretation; preserve malformed/missing-current-evidence distinctions; apply D5 gates before recovery |

Update every caller below in the same increment as its imported function is
removed. Acceptance requires no imports of the removed names.

| Caller | Imports | Replacement |
| --- | --- | --- |
| `tests/suites/witness_contract/check_comparison.py` | `recover_evidence`, `comparison_groups`, `failure_groups`, `path_reporting`, `validate_evidence_shape`, `validate_current_build_evidence` | absorbed by `comparison_matrix` (I2); no port |
| `tests/suites/blackbox_e2e/checker_controls.py` | all five, plus both validators | rebuilt in I3 against `validate`/`steps`/`select` |
| `tests/suites/witness_contract/check_pre_apply_failure.py`, `check_termination_correlation.py`, `check_prediction_targets.py` | `recover_evidence`, `comparison_groups`/`failure_groups` | `validate` + `select` on the C1/S-row fields they assert |
| `tests/suites/witness_contract/check_deny_capture_window.py`, `log_capture_controls.py` | `recover_evidence`, `validate_evidence_shape` | `validate` + `denials` |
| `tests/suites/runner_validator_failure/check.py` | `recover_evidence`, `comparison_groups`, `failure_groups` | `validate` + `select` (B2, B4) |
| `tests/suites/runner_exec_dac/check_query_scope.py` | `recover_evidence`, `comparison_groups`, `failure_groups`, `validate_evidence_shape` | `validate` + `select` (S15, S17) |
| `tests/lib/unavailable_prediction.py` | `recover_evidence`, `comparison_groups`, `failure_groups`, `path_reporting` | field selections per I3 |
| `tests/lib/path_diagnostics_contract.py` | `recover_evidence`, `validate_evidence_shape` | field selections per I3 |
| `tests/suites/blackbox_e2e/disposition_controls.py`, `runner_outcome_validator_no_reply/check.py`, `witness_contract/check_ordering.py`, `check_max_target_reply.py`, `check_removed_target.py` | the merged validators only | `validate` |
| `controller/src/run_flow.rs` ~2321, ~2523; `controller/src/log_replay_tests.rs` ~172 | inline Python importing `recover_evidence`, `validate_evidence_shape` | `validate` + `denials`, per R3 |

### R5. Test assertions

| Suite | Files (references) | Disposition |
| --- | --- | --- |
| `runner_unit` | `DriftClassifierTests.swift` (53) | replaced by `ComparisonEvidenceTests.swift` (REPAIR I2) |
| `runner_unit` | `EnvelopeInvariantTests.swift` (30) | version 4–7 round-trips deleted; current-shape cases updated |
| `runner_unit` | `PredictionUnavailableTests.swift` | delete only the `predictionUnavailable` group calling `runSandboxCheck` and its exclusive assertion helper; keep `predictionUnavailableQueryPlanning`, its literal expectations and `runPredictionUnavailableTests` registration; rewrite the file and registry descriptions |
| `runner_unit` | `SandboxApplyTests.swift`, `main.swift` | delete the helper-only file, `runSandboxApplyTests` registration and its comment; the `runner/AGENTS.md` paragraph linking it is deleted too |
| `runner_unit` | `OrderingTests.swift` (10), `ReplyFailureTests.swift` (12 plus the field-complete fixture), `ReplyMaximumTests.swift` (2), `WorkerEvidenceTests.swift` (1), comments in `AttemptOutcomeMappingTests.swift`, `CWorkerTests.swift`, `main.swift` | updated; the golden regenerates from `ReplyFailureTests` |
| `unit/rust.unit` | R3 fixtures | updated |
| `blackbox_e2e` | `checker_controls.py` (21) | rebuilt (REPAIR I3) |
| `blackbox_menagerie` | `checker_controls.py` (13), `validate_run.py` (1), `cases/core.json` (23 steps carry `expect.drift`) | `expect.drift` deleted |
| `failure_boundaries` (4), `run_effects` (2), `runner_exec_inheritance` (1), `runner_exec_lifecycle` (4), `runner_filter_sysctl_name` (6), `runner_outcome_runner_timeout` (2), `runner_outcome_validator_no_reply` (2), `runner_specimen_isolation` (1), `runner_validator_failure` (4) | check scripts | field assertions |
| `runner_exec_dac` | `check.py` (7), `check_query_scope.py` (6), `run.sh` (2) | field assertions; case id becomes `execute_permission_controls_spawn` |
| `runner_outcome_libsandbox_unavailable` | whole suite: `run.sh`, `README.md`, catalog entry | delete with the loader; no replacement |
| `runner_use_c_worker` | `run.sh` (63) | retire `drift_null_for_dac_eacces` and `drift_null_for_non_policy_failure` with passing S03, S17, S14 replacement controls in I2/I4; other assertions become field assertions |
| `witness_contract` | `check_ordering.py` (10), `check_prediction_targets.py` (6), `check_create_existing.py` (3), `check_diagnostic_transport.py` (3), `check_pre_apply_failure.py` (3), `check_removed_target.py` (2), `check_attempt_in_flight.py`, `check_termination_correlation.py`, `check_worker_evidence.py`, `check_worker_sparse.py` (1 each) | field assertions |
| `witness_contract` | `check_comparison.py` (11), `drift_determination_via_validator_seam.sh` (12), `run.sh` (6) | absorbed by `comparison_matrix` (REPAIR I2); retire the seam case with passing replacement controls |

### R6. Goldens and fixtures

| Fixture | Contains | Disposition |
| --- | --- | --- |
| `tests/fixtures/contract/response_shape.json` | `drift`, `conclusion`, `limitations`, `deny_signal`, `deny_signal_total` | regenerate from `ReplyFailureTests`; self-accepted under EXECUTION's golden rule, with the diff summary in the acceptance record |
| `tests/fixtures/blackbox_menagerie/cases/core.json` | `expect.drift` on every step | delete the key |
| `tests/fixtures/blackbox_e2e/checker/missing_path_run.json` | synthetic response 5; baseline for both checker-control files | regenerate at 13 and 5 from a live run |
| `tests/fixtures/disposition/a1_expected.json` | generated control, envelope 3, response 10; read by `disposition_controls.py` and three `run_flow.rs` tests | regenerate at 13 and 5 |
| `tests/fixtures/disposition/a1_known_loss.json` | captured envelope 2, response 9 | keep the bytes; the check becomes the `unsupported` rejection |
| `tests/fixtures/blackbox_e2e/BBX-00{1,2}/expected.json` | drift keys | delete the keys |

### R7. Registries

- `tests/catalog.json`: four ids deleted, one renamed, two added (REPAIR I5).
  One of the four, `runner_outcome_libsandbox_unavailable`, is a whole suite
  directory, so `tests/README.md`'s suite table and the suite count
  `source_drift` derives from the suites on disk both move with it.
  `tests/RETAINED.json` and release acceptance records under `dist/` reference
  old ids and are not rewritten.
- `tests/README.md` suite-coverage rows (~293, ~296, ~300, ~312) and the
  "Comparison evidence coverage" section (~455–465); `source_drift` checks the
  table against the suites on disk.
- `tests/COVERAGE.md` rows ~25, ~27, ~30, ~31, ~83, ~84, ~86, ~87.
- Update `source_drift` inventories with the API removals: normalized outcomes
  19 → 18, attempt outcomes 10 → 9, and override keys 8 → 7. The normalized
  count and bidirectional coverage check remain Swift-only; controller-only
  version failures do not add matrix rows.
- Suite READMEs: `witness_contract` (20 references), `runner_use_c_worker`
  (12), `runner_exec_dac` (7), `blackbox_e2e` (4), `blackbox_menagerie` (3),
  `runner_specimen_isolation` (3), `runner_validator_failure` (3),
  `runner_filter_sysctl_name` (2), and one each in `run_effects`,
  `runner_exec_lifecycle`, `runner_outcome_runner_timeout`,
  `runner_outcome_validator_no_reply`, `runner_c_worker_harness`,
  `runner_byoxpc` and both iokit filter suites.

### R8. Contract and contributor text

- `tests/FAILURE-PROPAGATION-CONTRACT.md`: the chapter "Derived comparisons
  and evidence joins" (376 lines) is replaced under REPAIR I5. The "Ordering
  protocol names" row for `runner_reporting_failed` ("comparisons absent,
  drift null") is reworded.
- `docs/CONTRACT.md` per D5.
- `AGENTS.md` core idea "Predictions precede attempts": its last clause names
  `drift: true`; the barrier claim stays.
- `runner/README.md` ~74, ~230, ~240, ~260–267, ~314; `runner/AGENTS.md` ~15;
  `runner/augments/README.md` ~154; `controller/README.md` ~137–145, ~369,
  ~378 and its consumer-audit table.
- Document `--request -` in both tools' `usage()` and surface descriptions;
  remove accounts of temporary request files for `policy-witness run` and
  retain verification's file-input description. Document `request_delivery` and
  its failure result beside the unchanged `--timeout-ms` description. Describe
  built-in runner selection from the manifest entry and `app_provenance` as
  the manifest path plus verify report.
- S1–S3: revise the source inventory in `runner/README.md`, the `runner_unit`
  row in `tests/README.md`, `tests/suites/runner_unit/README.md`, and the unused
  apply-helper descriptions in `tests/COVERAGE.md` and
  `tests/FAILURE-PROPAGATION-CONTRACT.md`, including its statement that helper
  cleanup is outside the effort. Delete "Stubbing C function pointers" from
  `runner/AGENTS.md`. Update
  `tests/suites/source_drift/README.md`'s target list and claim that both Swift
  query callers use the exclusion set, and record the native sandbox API check
  there and in `tests/suites/preflight/README.md` with what each check sees and
  does not see. Reconcile the Mach-lookup outcome and the retired
  `libsandbox_unavailable` in `docs/PolicyWitness.md`, `tests/COVERAGE.md` and
  the `_test_overrides` table in
  [PWRunnerAPI.swift](runner/Sources/PWRunnerCore/PWRunnerAPI.swift).

### R9. Not removed

- `source_drift`, `runner_abi_layout` and every use of "drift" meaning
  docs-versus-code or layout divergence: comments in
  `CWorkerOrchestrator.swift` ~712, `AttemptOutcomeMappingTests.swift` ~96,
  `controller/src/runner_manager.rs` ~1080, `sb_api_validator.c` ~605,
  `CWorker.swift` ~47, `tests/lib/artifact.py` ~38,
  `tests/suites/dispatcher/check_selection.py` ~126.
- The `prediction_unavailable` set in `ProbeRunner.swift`, its `source_drift`
  check against the guide, and
  `tests/suites/witness_contract/harness/VERIFICATIONS.md`; only its
  description changes.
- S1–S3's retained production helpers listed in R2, including policy hashing
  and structural policy refusal; the planner unit controls, C worker harness,
  real worker/validator drivers and the live failure controls other than
  `runner_outcome_libsandbox_unavailable`.
- `comparison.order`, `runner_subprocess.ordering`, `eligibleOrderedStep`, the
  query-side `sandbox_check.native_rc`, the release barrier and the opt-in
  `order_barrier_mutations` control;
  `legacy_worker_abi6` in `OrderingTests` (the ABI tripwire).
- `comparison.observation` and `permission_failures_without_record`.
- The lifecycle copies in `attempt.lifecycle` and the lifecycle entries in
  `comparison.limitations`, with their Rust validation.
- The optional log channel's `deny_lines` and disclaimer fields.
- `records/`, `dist/evidence`, `dist/archive`.

### R10. Semantic completion criterion

Before and after implementation, search the vocabulary `drift`, `conclusion`,
`agreement`, `disagreement`, `consistent`, `directional_consistency`,
`verdict`, `prediction`, `enforcement`, `mismatch`, the signal-channel names,
every removed limitation string, `obligations`, `comparison_conditions`,
`references`, `prediction_unavailable_pairs`, `runner_startup_diagnostics`,
`first_deny`, `native_rc`, `supervision` and the former provenance paths, across CLI
help, diagnostics, test names and descriptions, identifiers, comments,
docstrings, fixtures, registries and documentation; follow aliases, callers
and generated copies; read affected passages for claims that survive without
any search term. Record every remaining match by its meaning: a current
descriptive value, an unrelated use, immutable evidence, an explicit
removed-key rejection.
For `native_rc`, remove attempt-side aliases and classify query-side uses as
retained evidence and ordering checks.

Also search the S1–S3 function/type names, `PWSandboxCheckShim`,
`XPC_RUNNER_SANDBOX_SHIM`, `SandboxApplyTests`, `runSandboxApplyTests`,
`bootstrap_port_failed`, `SandboxLib`, `libsandbox_path`,
`libsandbox_unavailable`, `library_identity`, `sandbox_cache_uuid` and
`@convention(c)`. Also search
`write_temp_request`, `sw_vers`, `macos_build_version`,
`resolve_pw_runner_bundle_info`, `PWRunnerBundleInfo`, `PlistBuddy`,
`app_bundle_id`, `app_binary_rel_path`, `app_entitlements` and `evidence_notes`.
Follow build variables, target dependencies, test registrations, contributor
links and code callers. Search records and this plan may name removed artifacts;
active implementation and contributor instructions must match the contract.

## REPAIR

Classify each affected test artifact:

| Class | What it is | Disposition |
| --- | --- | --- |
| Scenario | A case with an independent control: a real file, a direct OS call, a steered verdict, a captured host fact | Keep. Expectations come from the D1 matrix or the case's own control. |
| Old-contract control | A control proving the checker rejects a loss expressible only in the removed contract | Delete. Re-express only when the invariant survives in D2, D3 or D5, in the current contract's wording. |
| Unused-helper control | A test whose only execution target is a removed S1–S3 helper | Delete with that helper. Retain tests of the production planner and C paths; do not port assertions to another unused implementation. |
| Legacy branch | Code, a fixture, a round-trip or prose whose purpose is reading a version no reader accepts | Delete. |
| Equipment | A shared library or helper | Rewrite from the contract: no legacy-version branches, no joint verdicts, no compatibility fallbacks. |

Keeping anything requires naming the matrix row, independent scenario control,
or D2/D3/D5 invariant it serves.

### I1. Behavior-preserving preparation

Before retiring artifacts, capture the documentation requirements listed in
the infrastructure ledger. Extract `resolve_imports`, `compute_closure_hash`
and OS-facts collection from `sbpl-check.rs` into shared Rust modules without
changing output. Replace its `sw_vers -buildVersion` subprocess with
`sysctlbyname("kern.osversion")`, preserving once-per-process caching.
Single-read traversal and dossier collection land in I4.

Write the unregistered matrix fixture; add exec and sysctl specimens under
`tests/fixtures/pw_runner/`; run the response 12 default battery. Delete no
scenario or active contract check in I1.

Commit directly to `main`; no branch or worktree. Make one commit per
increment or coherent sub-step, under EXECUTION's exit conditions; do not push
unless the operator asks. Coordinate producer, consumer, registry
and documentation changes in each increment. Register and pass replacement
controls before retiring their predecessors in that increment.

### I2. The matrix fixture

`tests/fixtures/comparison/matrix.json` holds the 32 S/B/C rows and T: for each,
the specimen inputs (policy, query, attempt, steered verdict if any, independent
control), raw inputs needed by the unit reader (channel results and ordering),
the raw fields the live case asserts beside the record (`sandbox_check.outcome`,
`result_source`, `missing_reason`, `attempt.rc`, `errno`, `child_exit_code`,
the unlink records), and the expected response 13 `comparison` object.
Review expectations against the D1 matrix and independent controls; do not
generate them from the producer under test. Use D1's specimen mechanics for B.
R is a reply-boundary control outside the comparison fixture. Absolute paths
use the fixtures' existing `{{NAME}}` placeholder convention, expanded by both
readers. The B stub, the matrix README and the fixture live under
`tests/fixtures/comparison/`; raw captures live with their acceptance record.

Specimen B requires a new combined seven-step receipt. The retained baseline
has five steps; B2 and B4 have separate suite receipts. Keep those as row-level
baselines, and require the mixed verdict/error/stall transcript specified in
D1 before crediting B1–B7 coverage. Add a validator decode/association control
for the mixed records and retain the live transcript, all seven step results,
file effects and timeout outcome together.

Two readers share the fixture:

- `witness_contract/comparison_matrix`, new: runs the three S/B/C specimens through
  the CLI, checks every step against its row with `validate` and `select`, and
  keeps the independent controls `check_comparison.py` had (the direct EACCES
  open, the retained file bytes). The existing deadline case reads T from the
  same fixture after establishing its boundary; it owns FIFO cleanup.
- `runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift`, replacing
  `DriftClassifierTests.swift`: table-driven over the same file through
  `comparisonEvidence(...)`, plus the existing host-path-provenance group;
  registered in `main.swift`.

| Rows/invariant | Live or boundary owner | Independent control / retained receipt |
| --- | --- | --- |
| S01–S25 (S04 unused), B1–B7, C1 | `witness_contract/comparison_matrix` | native/file controls and steered-validator transcript; preserve each specimen, raw run, checker output and app inventory in managed test artifacts |
| T | `witness_contract/worker_attempt_in_flight_at_deadline` | FIFO, raw progress, validator record and release chain; assert the comparison selected from the shared fixture |
| R: reply degradation | `runner_unit` / `ReplyFailureTests` | internal encoder faults at both fallback levels; retain the specified evidence and withhold comparisons |
| `limitations` vocabulary | `ComparisonEvidenceTests`, encoder invariants and checker controls | a planner exclusion for each code, each lifecycle entry, and an injected string outside D1's vocabulary |

T's baseline is the retained
[live reply](tests/out/runs/release-0.2.4-default/suites/witness_contract/worker_attempt_in_flight_at_deadline/artifacts/a1/run.json)
and [specimen](tests/out/runs/release-0.2.4-default/suites/witness_contract/worker_attempt_in_flight_at_deadline/artifacts/a1/specimen.json)
under the `release-0.2.4-default` entry in [RETAINED.json](tests/RETAINED.json).
Capture a response 13 run and link its acceptance receipts from the matrix
README; preserve baseline receipts as bytes.

Retire `runner_use_c_worker/drift_null_for_dac_eacces` only with passing S03/S17
controls, `drift_null_for_non_policy_failure` with S14, and
`witness_contract/drift_determination_via_validator_seam` with B1–B7 and its
independent controls. Their catalog entries and documentation move in that
same verified increment.

### I3. Equipment

- `tests/lib/consumer.py` exposes `validate(document)`, `steps(document)`,
  `select(steps, **fields)`, `lifecycle(document)` and `denials(document)`.
  `document` is an envelope or a bare runner reply. A version other than the
  contract manifest's yields one `unsupported` error under D5; malformed
  versions and no-reply envelopes follow D5's separate rules. `validate` merges
  `validate_evidence_shape`, `validate_current_build_evidence` and
  `validate_ordering`, checks `observation` and the two relations against the
  raw channel fields, checks `order` against `ordering`, and rejects a
  `limitations` string outside D1's vocabulary. Reject the removed keys without
  reconstructing obligations, `references` or `comparison_conditions`.
  `recover_evidence`, `comparison_groups`, `failure_groups`, `path_reporting` and
  `step_reporting` are gone.
- `tests/lib/blackbox.py`: `validate_step` loses the drift checks and the
  alias-agreement rule; `expected.comparison` carries the D1 record;
  `validate_run_shape` calls `validate`.
- `tests/lib/unavailable_prediction.py`, `path_diagnostics_contract.py`: field
  selections.
- `blackbox_e2e/checker_controls.py` rebuilt against `missing_path_run.json`
  regenerated at 13 and 5 from a live run. Surviving controls: injected
  removed keys, including `prediction`, `obligations` and
  `comparison_conditions`; a `limitations` string outside D1's vocabulary;
  path provenance; the ordering chain; reporting-failure evidence retention
  and comparison withholding at both fallback levels; every version-boundary
  control in D5; one control feeding
  `pw-runner-client` output to `validate`. The mutation-order scenarios keep
  their file-effect and release-chain controls and assert the unlink attempt
  records and `order`.
- Menagerie: `expect.drift` deleted from `core.json`; `validate_run.py` passes
  `expect.comparison` through. `BBX-001` and `BBX-002` `expected.json` lose
  their drift keys. Other fixtures per R6.
- Retire the old-contract Swift controls in `EnvelopeInvariantTests` (legacy
  round-trips and missing-observation groups), `OrderingTests` (public
  disagreement) and `ReplyFailureTests` (`disagreement`, `false_drift`,
  `true_drift`) with the response 13 producer and surviving D3 controls.
  Replace the Rust 4–8 transport loop with current-version unfamiliar-value
  transport and independent unsupported-version preservation/rejection tests.
- Retire the S2 helper-only query group and S3 apply-helper tests precisely as
  listed in R5, in the same increment as their R2 source/build removals. Keep
  the production query-planner group and its registration. Update the
  `source_drift` inventory and contributor descriptions in that increment;
  these deletions do not retire a live scenario or a catalog entry.
- Rebuild the checker controls without the `response7*`,
  `legacy7_difference`, `blanket_unknown`, `supported_agreement`, drift
  projection, `removed_*_false_claim`, `disagreement_without_labels` and
  `order_limit` controls. Re-express only surviving contract invariants. Remove the
  `effective_filter_value` fallback and lifecycle version branches in this
  increment. Preserve distinctions needed to reject missing/malformed current
  evidence; remove `MISSING` or `not_reported` only where their sole purpose was
  reading legacy replies.

### I4. Producer and dossier

- Remove the R2 source/build artifacts with their I3 tests. In the same increment,
  update the service header and contributor guidance, add the source check and
  its positive/negative controls, and add the binary check with before/after
  receipts.
- Update the field-complete fixture in `ReplyFailureTests` and string
  classification in `ReplyMaximumTests`. Recompute `runner_reply_maximum` and
  derived `controller_output` from the synthesizer; both must be no larger
  than their baseline values. Record the values in `docs/limits.json` and
  regenerate the shape golden under EXECUTION's golden rule.
- Controller per D2 with Rust tests for shape, statuses, relocated paths, the
  held request string and D5 version gates. Scan controls include a
  nonregular file, a single read used for both hash and recursion, nonliteral
  imports, decoding/read errors and the existing depth and count cutoffs;
  `docs/limits.json` changes prose only for the scan.
- `docs/contract.json` to 13 and 5 with these changes, then
  `python3 docs/generate_contract.py`.
- `witness_contract/dossier_witness`, new: the dossier against the specimen
  that ran and host facts the test captures independently (`sw_vers`,
  `uname`, the manifest, and a hash of an override executable). It owns live
  examples for no augments, applied augments, refused augments, malformed or
  missing policy/source, and XPC failure, plus executable overrides and
  BYOXPC selection. Use the existing BYOXPC ownership/cleanup machinery.
  Controlled Rust collectors own the D2 manifest and override cases, hash
  mismatch on a non-manifest selection, and host-read failures so signed app
  bytes stay unchanged. Assert built-in selection failure through the uniform
  dossier envelope and successful BYOXPC invocation without a manifest; the
  latter reports unavailable baselines while retaining observable paths and
  hashes. Manifest-entry controls cover missing, duplicate and wrong-kind
  entries for each role; missing/empty/NUL-containing service bundle IDs;
  and absent/malformed hash strings without refusing service selection. Include
  entries whose IDs, bundle IDs or service names match at other paths and
  the app-level validator as decoys; none may substitute for a required path.
  Assert helper-entry failures affect only their baseline and do not block
  invocation. Override controls cover wrong types, NUL/overlength strings, empty
  and relative paths, missing/unreadable/nonregular files, and valid paths;
  confirm they do not change request bytes or runner admission. One control
  asserts that an ordinary built-in run hashes no app binary and reports null
  binary records; one asserts that no `policy-witness run`, the `xpc_error`
  control included, leaves a file in the temp request directory; one resolves
  the built-in runner from a synthetic app root whose service Info.plist is
  absent and whose manifest carries the entry; and one asserts that
  `app_provenance` carries exactly the manifest path and the verify report.
  The dossier case includes or links
  those control receipts and checks every failure-table shape. Host-read
  controls cover the four sysctl facts.
- Implement request delivery in `runner_client.rs`, `run_flow.rs` and the Swift
  client. Rust subprocess controls in `runner_client.rs` own a request larger than the
  pipe buffer delivered in full to a child that reads it after a delay, a
  child that exits without reading so the write fails with EPIPE and the
  controller records the error without terminating, and a delivery error
  alongside a captured failure reply. `run_flow.rs` controls own `tool_error`
  precedence, unchanged reply retention, D5 gating and a helper delivery
  failure on the fallback path preserving the original `xpc_error`.
  A `sbpl-check` control feeds the same request by file and by `--request -`
  and requires byte-identical output. The live `dossier_witness` case
  exercises the shipped client's stdin path and verifies the submitted
  request bytes. Keep direct client and helper file-input coverage for their
  existing interfaces. Client argument controls cover the two forms and
  rejection of duplicate/mixed input, missing values and extra arguments.
  `runner_commands.rs` controls cover verification's file-input path,
  preserved default, temporary-file/launch failures and refusal to project
  unsupported or malformed replies.

### I5. Contract and registry documents

- `tests/FAILURE-PROPAGATION-CONTRACT.md`: the chapter "Derived comparisons
  and evidence joins" is replaced by the comparison record (D1), the
  invariants (D3), the reading rules (D4), the scenario matrix, an ownership
  table naming which case owns which rows and invariants, and supported
  versions. The join table stays
  with its "Supported public conclusion" column renamed "What the record
  states". C1 through C6, the accepted-answers table, "Public representation
  and meaning", "Permanent consumer enforcement" and "Compatibility and
  acceptance gate" go.
- `docs/CONTRACT.md` per D5. `ContractVersionTests.swift`'s header comment
  ("Added keys need no bump") changes with it.
- `controller/README.md`, the runner-client and `sbpl-check` usage and
  documentation, `tests/FAILURE-PROPAGATION-CONTRACT.md` and the guide
  document `--request -` on both tools, `request_delivery`, and controller
  `tool_error` precedence with the retained reply. The
  controller README describes manifest-based runner selection and the reduced
  `app_provenance` shape. `docs/limits.json`'s `client_rpc_wait` and `controller_output`
  entries and the Limits interaction prose keep their meaning; the
  `helper_import_depth`, `helper_import_count` and `helper_source` entries say
  the dossier scan shares them; `runner_reply_maximum` and
  `controller_output` take their recomputed values. The `sbpl-check` receiver's
  existing collection policy is unchanged. Regenerate the documented limit
  tables and guide copies with `docs/generate_limits.py`.
- `tests/catalog.json`: `comparison_matrix` and `dossier_witness` added;
  `execute_permission_is_not_sandbox_drift` becomes
  `execute_permission_controls_spawn`. Both new cases are default cases of
  the `witness_contract` suite, which already carries `requires: ["app"]`.
  The BYOXPC part of `dossier_witness` is a separate `default: false` case
  with a wrapper under `tests/suites/witness_contract/opt_in/`, listed in the
  `opt_in` suite's include list beside `order_barrier_mutations`; it needs a
  logged-in GUI session.
- `tests/README.md`: the "Comparison evidence coverage" section becomes one
  paragraph pointing at the matrix fixture and its live and Swift readers; affected suite
  rows rewritten. `tests/COVERAGE.md` rows likewise. Suite and fixture READMEs
  follow DOCUMENTATION's infrastructure ledger.
- `runner/README.md`, `runner/AGENTS.md`, `runner/augments/README.md`,
  `controller/README.md` (including its consumer-audit table) and the
  AGENTS.md core idea per R8.
- Complete S1–S3's R8 entries, including the retained hashing/planning roles,
  the surviving shim inventory and the retired outcomes. Check that no active
  instructions link to the deleted test or assign production coverage to it.

### Kept scenarios

| Case | Independent control | Expectation source |
| --- | --- | --- |
| `runner_exec_dac/execute_permission_controls_spawn` | direct `posix_spawn` before and after `chmod` | S15, S17; the deny-query run expects `sandbox_check.outcome: deny`, `permission_failure` and `attempt.errno`, read under D4's third rule |
| `witness_contract/queries_precede_attempts`, `queries_use_a_pre_attempt_interval`, `query_interval_is_not_a_snapshot`, `external_mutation_between_query_and_attempt` | file bytes, native receipts, timing | S19, S25, the B rows; `order` and the unlink attempt records |
| `witness_contract/prediction_target_is_independent_of_attempt_target` | file bytes | S01, S02, S05 |
| `witness_contract/create_existing_file_preserves_contents`, `run_effects/*` | file bytes and modes | S08, S24 |
| `witness_contract/pre_apply_failure_reports_no_policy_verdict`, `worker_sparse_failure`, `worker_progress_and_failure` | worker evidence | C1, T |
| `runner_validator_failure/*`, `runner_outcome_validator_no_reply` | transcripts, signals | B2, B4 |
| `runner_outcome_runner_timeout`, `witness_contract/worker_post_apply_hang_seam`, `worker_attempt_in_flight_at_deadline` | deadlines, file effects | S01 plus the lifecycle rows |
| `runner_specimen_isolation`, `runner_exec_lifecycle`, `runner_exec_inheritance` | process observations | S15, S16 |
| `failure_boundaries/*` | admission and receiver faults | shape only |
| `blackbox_e2e/BBX-001`, `BBX-002`, the menagerie cases | policy knowledge, file effects | `predict`, `attempt_ok`, `errno` |
| `runner_filter_*` | planning exclusion | S10 |

### Acceptance criteria

- Default battery after I1 and after each implementation increment;
  `tests/run.sh --all` on the integrated candidate, retained as the acceptance
  record, with replacement owners and dossier controls all accounted for.
  `order_barrier_mutations` runs on the integrated candidate.
- Before I1, capture the existing three specimens under
  `tests/fixtures/pw_runner/`. After behavior-preserving preparation and the two
  added specimens, capture all five as the response 12 baseline. On the verified
  integration candidate, diff all five against that baseline with intended
  contract changes and run-varying values explicitly accounted for; the
  run-varying set and the acceptance rule are in EXECUTION. Preserve
  the inputs, app inventory and raw envelopes with the acceptance record.
- R10 over the test tree and equipment.
- No `policy-witness run` writes a temporary request file, and an ordinary
  built-in run hashes no app binary, spawns no PlistBuddy and parses the
  manifest once. Retain the I4 control receipts for each condition; the
  PlistBuddy and manifest-once conditions use EXECUTION's static receipts.
- The delivery controls pass; the live stdin receipt and direct
  file-input coverage accompany them.
- For S1–S3, verify both the shipped `build.sh` build and the test-only SwiftPM
  build through `runner_unit`; run `source_drift` including planner controls and
  the native-use assertion and its positive/negative controls, `preflight` including the `nm -u`
  assertion, and `runner_c_worker_harness` including its deny-default cases. The
  integrated baseline diff must show no helper-removal change to queries,
  attempts or hashing beyond separately approved contract changes. The
  baseline diff must account for the removed `libsandbox_unavailable` outcome.
  Retain the existing live worker and validator failure controls in the default/`--all`
  battery; `runner_outcome_libsandbox_unavailable` is deleted with its outcome
  and is not expected to run.
- Retain response 13 matrix/dossier receipts, using the matrix's baseline
  specimens on the integration candidate. Complete the documentation ledgers,
  accept shape-golden diffs under EXECUTION's golden rule and record
  recomputed reply/capture limits.
- The finished consumer exposes no joint prediction/enforcement verdict.
  Descriptive validation and selection may use both channels. All D5 semantic
  readers gate versions by equality and contain no legacy interpretation branch;
  raw transport remains covered independently.
- Sub-agents cannot run the built app; live verification runs from the main
  session, under EXECUTION's division of labor.

## DOCUMENTATION

Apply the ledgers to `README.md`, `docs/PolicyWitness.md` and contributor
documents. The guide copies `docs/QUESTIONS.md` (between the `SHARED
QUESTIONS` markers) and `docs/LIMITS.md` (between the `SHARED LIMITS` markers)
through `python3 docs/generate_limits.py`; the copied blocks are never edited
by hand, and `source_drift` checks the copies and the guide's
`prediction_unavailable` list against the Swift set.

### The ledger

Every sentence in the two documents that states a goal or a capability gets a
row: the sentence, its class (keep, revise, remove) and the replacement
direction. Seed rows:

| Document | Sentence (abridged) | Class | Direction |
| --- | --- | --- | --- |
| README ¶1 | "harness for observing differences between `sandbox_check`'s userland sandbox-prediction API and the kernel's actual enforcement" | revise | PW witnesses what a policy does to a process through two channels; it does not adjudicate between them |
| README ¶2 | "Measuring `sandbox_check`'s prediction about a process against policy enforcement requires managing process lifecycles" | revise | keep the lifecycle argument; drop "measuring against" |
| README Flow | "Each step records two evidence channels plus their comparison" | keep | with the comparison bullet rewritten |
| README Flow | the **Drift** bullet | remove | a **Comparison** bullet: observation, submitted-scope relations, order, and a pointer to the guide's reading rules |
| README Flow | "Eligible `query_first` records establish this ordering; they do not establish a shared state snapshot" | keep | |
| FAQ | "When should I use PolicyWitness?" | revise | to witness a policy's effect on specific operations and targets, with both channels and the kernel log attached |
| FAQ | "Beyond observing drift, what does PolicyWitness's attempt channel record?" | revise | heading loses "drift" |
| FAQ | "How does PolicyWitness handle uncertainty in its verdicts?" | replace | "What does a comparison record contain, and what does it not claim?" |
| FAQ | "Can PolicyWitness return a verdict of `drift: true`?" | replace | "Does PolicyWitness decide whether `sandbox_check` and enforcement disagree?": no; what it gives instead; how to read it |
| FAQ | "Which happens first, the prediction or the attempt?" | keep | |
| Guide, Top-level fields | the `steps[].drift` and `steps[].comparison` bullets | revise | per D1 |
| Guide, Per-step shape | "`steps[].drift`: `bool \| null`"; the `exit_code` and `syscall_errno` aliases; `scope`; `comparison.prediction`; `attempt.native_rc`; every removed limitation string | remove | |
| Guide | reading a comparison record | add | the twelve D4 rules, in order, one sentence each, in one section |
| Guide, attempt outcome notes (~800, ~829, ~860, ~863, ~923, ~1071, ~1099) | "`drift` is null …" | revise | say what the comparison fields show |
| Guide, "Filter kinds where prediction is unavailable" | "documented mismatch between `sandbox_check`'s userland verdict and the kernel's actual enforcement"; "the drift pattern is not iokit-specific" | revise | state the verified fact: no filter ID in 1..200 produced a verdict matching enforcement; keep the "Currently in this category:" marker and list format that `source_drift` parses |
| Guide, Denial-log correlation | "never rewrites a comparison, drift, failure attribution or termination cause" | revise | drop "drift" |
| Guide | the specimen dossier | add | canonical paths, the raw records a reader joins to, the collection mechanisms and the shared scan bounds stated once, evidence-selection recipes without labels |
| Guide, dossier section | host facts | add | OS version/build, kernel release and architecture as environment context; no claim that they identify the worker's or validator's sandbox libraries |
| Guide, Output envelope | fields described by envelope path only | revise | the bare reply from `pw-runner-client` as readable on its own, then the envelope as that reply plus the dossier, transport and log capture |
| Guide and FAQ | signal-channel descriptions and old provenance paths | remove | |
| LIMITS | the helper import and source entries | revise | the existing bounds also bound the dossier scan; no new bound |
| Controller and client usage | the request file argument | revise | `--request -` and `request_delivery`; `--timeout-ms` unchanged |
| Guide and controller output contract | runner-client transport facts and controller failure | revise | the delivery observation beside the unchanged reply; a delivery failure is a controller `tool_error` and does not rewrite worker/XPC evidence |
| Guide and controller README | `app_provenance` fields; runner selection reads Info.plist | revise | the manifest path and verify report only, with the manifest named as where the header lives; selection reads the manifest entry |
| FAQ | reading the deny log | add | optional, possibly incomplete evidence; candidate correlation does not establish attempt attribution or a comparison verdict |

### Infrastructure ledger (from REPAIR)

For each changed artifact, update every document naming it. The final column
identifies mechanical checks; review the remaining prose manually. Do not edit
`records/`. Repeat the search after implementation.

| Artifact | REPAIR | Documents naming it (hits) | Mechanically checked part |
| --- | --- | --- | --- |
| `witness_contract/drift_determination_via_validator_seam` | I2/I4 retire with passing replacement | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1), `tests/README.md` (1), `tests/suites/witness_contract/README.md` (section) | suite table row, README presence |
| `runner_use_c_worker/drift_null_for_dac_eacces` | I2/I4 retire with passing replacement | `tests/README.md` (1), `tests/suites/runner_exec_dac/README.md` (1), `tests/suites/runner_use_c_worker/README.md` (1), `tests/suites/witness_contract/README.md` (1) | suite table row |
| `runner_use_c_worker/drift_null_for_non_policy_failure` | I2/I4 retire with passing replacement | `tests/suites/runner_use_c_worker/README.md` (2), `tests/README.md` (1), `tests/COVERAGE.md` (1), `docs/PolicyWitness.md` (1) | suite table row; outcome matrix |
| `runner_exec_dac/execute_permission_is_not_sandbox_drift` | rename | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1), `tests/README.md` (1), `tests/COVERAGE.md` (1), `tests/suites/runner_exec_dac/README.md` (whole file), `tests/suites/run_capture/README.md` (1) | suite table row; outcome matrix |
| `witness_contract/check_comparison.py` | I2 absorbed | `tests/suites/witness_contract/README.md` (1) | none |
| `DriftClassifierTests.swift` | I2 replaced | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1) | none |
| S1–S3 unused Swift helpers, `SandboxApplyTests.swift` and `SandboxLib.swift` | I3/I4 remove exclusive code/tests; retain hashing and planning | `runner/README.md`, `runner/AGENTS.md` (delete its stubbing paragraph), `tests/README.md`, `tests/COVERAGE.md`, `tests/FAILURE-PROPAGATION-CONTRACT.md`, `tests/suites/runner_unit/README.md` | internal test registration and builds |
| `PWSandboxCheckShim` and Swift query-helper group | I3/I4 remove target/build dependency and helper-only tests | `tests/suites/source_drift/README.md`; `runner/Package.swift` and test/production source comments | source-set agreement, surviving planner controls and both builds |
| `bootstrap_port_failed` | remove the spelling | `docs/PolicyWitness.md`, `tests/COVERAGE.md` | outcome inventory and mapping controls |
| `runner_outcome_libsandbox_unavailable` and `libsandbox_unavailable` | delete the suite and outcome | `tests/catalog.json`, `tests/README.md`, `tests/COVERAGE.md`, `tests/suites/runner_outcome_libsandbox_unavailable/README.md`, the `_test_overrides` table in `PWRunnerAPI.swift` | catalog entry, suite table row, suite count, outcome matrix, override-key count |
| `EnvelopeInvariantTests` legacy groups | I3 retire with contract change | `tests/FAILURE-PROPAGATION-CONTRACT.md` (3), `tests/COVERAGE.md` (2) | outcome matrix |
| `runner_client.rs` version loop | I3 replace transport/version controls | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1) | none |
| `checker_controls.py` legacy and drift controls | I3 rebuild with contract change | `tests/FAILURE-PROPAGATION-CONTRACT.md` (7), `tests/README.md` (6), `tests/COVERAGE.md` (2), `tests/suites/blackbox_e2e/README.md` (2), `tests/suites/blackbox_menagerie/README.md` (2), `tests/suites/runner_filter_sysctl_name/README.md` (2), `controller/README.md` (1), one each in the `smoke`, `run_effects`, `runner_byoxpc` and both iokit filter suite READMEs | suite table rows; outcome matrix |
| `consumer.py` `recover_evidence` and its groups | I3 rewrite | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1), `controller/README.md` (consumer-audit table) | none |
| `consumer.py` three validators | I3 merge | `tests/FAILURE-PROPAGATION-CONTRACT.md` (2) | none |
| `blackbox.py` `effective_filter_value` fallback | I3 delete | `docs/CONTRACT.md` (1) | none |
| `blackbox.py` alias-agreement rule | I3 delete | `tests/README.md` (2), `tests/suites/blackbox_e2e/README.md` (2), `tests/suites/blackbox_menagerie/README.md` (2), `runner/README.md` (1), `docs/PolicyWitness.md` (1), one each in the `runner_filter_sysctl_name`, `runner_specimen_isolation` and `runner_outcome_runner_timeout` READMEs | suite table rows; guide per-step shape line |
| lifecycle legacy rows and legacy-only sentinels | I3 delete; retain missing-current-evidence controls | `tests/FAILURE-PROPAGATION-CONTRACT.md` (7), `tests/suites/blackbox_e2e/README.md` (2), `docs/CONTRACT.md` (1), `controller/README.md` (1), `tests/fixtures/disposition/README.md` (1), `tests/suites/witness_contract/README.md` (1) | none |
| Rust `project_disposition` legacy branch | I4 replace with D5 gate | `controller/README.md` output contract and consumer-audit table, `tests/FAILURE-PROPAGATION-CONTRACT.md` worker disposition contract | Rust unsupported-version controls |
| `missing_path_run.json` | I3 regenerate | `tests/suites/blackbox_e2e/README.md` (1) | none |
| `a1_expected.json`, `a1_known_loss.json` | I3 regenerate, keep | `tests/fixtures/disposition/README.md` (2), `tests/suites/blackbox_e2e/README.md` (2), `controller/README.md` (1) | none |
| menagerie `expect.drift` | I3 delete key | `tests/FAILURE-PROPAGATION-CONTRACT.md` (2), `controller/README.md` (1), `tests/suites/blackbox_e2e/README.md` (1), `tests/suites/blackbox_menagerie/README.md` (1), `tests/suites/witness_contract/README.md` (1) | none |
| BBX `expected.json` drift keys | I3 delete key | `tests/suites/blackbox_e2e/README.md` (3), `tests/OPT_IN_TESTS.md` (1), `tests/suites/runner_byoxpc/README.md` (1) | none |
| `tests/fixtures/comparison/matrix.json` | I2 new | needs `tests/fixtures/README.md`, the `witness_contract` README and the `runner_unit` README | README presence |
| `witness_contract/dossier_witness` | I4 new | needs the `witness_contract` README and `tests/README.md` | suite table row |
| legacy-reading vocabulary (`legacy`, `older replies`, `stored replies`, `historical`) | exact-version readers | `tests/FAILURE-PROPAGATION-CONTRACT.md` (33), `tests/COVERAGE.md` (7), `docs/CONTRACT.md` (6), `tests/README.md` (5), `runner/README.md` (4), `controller/README.md` (4), `tests/suites/blackbox_e2e/README.md` (4), `tests/suites/witness_contract/README.md` (2), one each in `tests/fixtures/README.md`, `tests/fixtures/disposition/README.md`, `tests/fixtures/worker_lifecycle/README.md`, and the `runner_filter_sysctl_name`, `runner_unit`, `blackbox_menagerie` and `runner_c_worker_harness` READMEs | none beyond the rows above |

Documentation requirements to capture before deleting the corresponding
artifacts:

- **Seam case.** In the matrix README, identify specimen B's
  `_test_overrides.validator_executable_path` transcript as stub output.
  Derive expectations from submitted scopes and independent file/permission
  controls, not native validator results.
- **DAC EACCES case.** Keep the `runner_exec_dac` README's statement that a
  permission failure under an allow prediction does not establish sandbox
  attribution.
- **Unknown-service case.** The guide's `lookup_failed` note identifies
  `kr=1102` as an unregistered service, not a permission result.
- **Checker controls.** Controls run without the app before the live cases;
  controlled changes must fail; combined failures report each independent
  problem; controls exercise the checker CLI without importing its
  implementation. These four sentences go to the rebuilt controls' README.
- **Disposition fixtures.** Label captured and generated fixtures separately;
  document the captured reply as an unsupported-version rejection control.
- **Transport test.** Use a current-version reply with unfamiliar strings and
  require unchanged forwarding.
- **Production coverage.** Assign planner, source-set and C failure coverage
  to their surviving tests in the runner-unit and failure-contract descriptions.

### Opening statement and defaults

Use this opening at the top of the README and guide:

> PolicyWitness records `sandbox_check` queries and attempted operations under
> macOS sandbox policies. When prediction is available, the validator queries
> the worker's PID; the worker attempts its operation after applying the policy
> and receiving release from the host. Each step records available results, missing
> observations, submitted-scope relations and ordering. The controller adds
> request identity, source hashes, imports, runner and app provenance, host
> facts and hashes of selected binaries outside the app manifest. It does not
> embed the full specimen. Optional log capture adds kernel denial records
> with correlation limits. No record asserts agreement or disagreement between
> prediction and enforcement.

Add a short FAQ on reading denial logs. Explain intermittent omission, the
possibility that validator queries generate records, and the difference between
a candidate association and attribution to an attempt. Missing records do not
establish allowance.

### Method

1. Read README and the guide end to end, complete both ledgers, and check that
   retained sentences remain coherent after removals.
2. Draft replacements from a current-state brief based on DESIGN, the matrix
   and the built app. Use old prose to locate deletions and reader needs, not
   as the source of replacement claims.
3. Describe current behavior. Keep historical clauses only when they change
   the reader's action; allow at most one `git log` pointer per document.
   Delete descriptions of removed artifacts.
4. Match these existing examples of documentation style: the guide's three-state
   `path_diagnostics` paragraph; the README's "Entitlements + SBPL" section;
   the AGENTS.md "Bundle layout is a contract" section; the controller
   README's "Execution and log-evidence ownership" table.
5. Edit `QUESTIONS.md` and `LIMITS.md` first, run `generate_limits.py`, then
   the guide's own prose, then the README, then the infrastructure documents.
6. After each document, a fresh-context reviewer (a sub-agent given only this
   Method section and the document) reads it and lists the passages that
   require knowledge of prior versions; fix those before editing the next
   document. A proposed explanatory bridge is omitted by default; record the
   sentence with and without it in the decision log. No operator check-in.
7. Run `source_drift`. Search for historical wording (no longer,
   previously, formerly, now, instead, replaces, legacy, historical, used to,
   since response, before response) and read every hit; each that stays is
   kept with a one-line reason. Reconcile `AGENTS.md`, the runner, controller
   and test READMEs, CLI help, diagnostics, comments and docstrings with the
   guide; remove contradictions and retired claims.

## EXECUTION

One orchestrating agent runs this plan end to end with no operator check-ins.
Choices the plan leaves open are made under these rules and recorded for
review afterwards, not approved beforehand.

### Decision log

`DRIFT-REMOVAL-DECISIONS.md` at the repository root, created in I1 and
committed with every increment. Dated entries hold: each judgment call with
the alternatives and the rule applied; each R10 remaining match with its
classification; the completed documentation ledgers; bridge sentences with
and without the bridge; resolved locations for plan references whose line
numbers moved; and increment progress (increment, commits, `PW_TEST_OUT_DIR`
names, receipts). On resumption after a context break, read this file before
anything else. It is review material, not documentation, and is removed at
closeout on the operator's instruction.

### Pre-authorized actions

Do not ask before: any deletion enumerated in REMOVAL; the R6 regenerations;
the catalog, `tests/RETAINED.json` and `docs/contract.json` edits named in
this plan; `tests/run.sh --prune --apply` on output directories this
execution created; BYOXPC install, verify and removal for `dossier_witness`
and the opt-in cases through the existing ownership and cleanup machinery,
with absence verified after removal; commits to `main`; writes under the
scratchpad and `tests/out/runs/`. Pushing is not pre-authorized.

### Commands and environment

| Purpose | Command |
| --- | --- |
| Build and sign | `YOLO=1 ./build.sh`, or `IDENTITY='Developer ID Application: …' ./build.sh` |
| Rust unit tests | `cargo test` in `controller/` |
| Swift unit tests | `tests/run.sh --suite runner_unit` |
| Default battery | `PW_TEST_OUT_DIR=tests/out/runs/drift-<increment> tests/run.sh` |
| Integrated candidate | `PW_TEST_OUT_DIR=tests/out/runs/drift-candidate-all tests/run.sh --all` |
| Barrier control | `tests/run.sh --case witness_contract/order_barrier_mutations` |
| One case | `tests/run.sh --case <suite>/<case>` |

Use a fresh `PW_TEST_OUT_DIR` per increment: `drift-i1-baseline` for the five
response 12 captures, `drift-i<n>` for each later default battery, and
`drift-candidate-all` for the integrated run. Register `drift-i1-baseline` and
`drift-candidate-all` in `tests/RETAINED.json` under `runs` with `path`,
`run_id`, `reason`, `source` and `app_inventory`, as the existing entries do.
Opt-in cases need a logged-in GUI session and unsandboxed execution; signing
identity resolution follows `tests/OPT_IN_TESTS.md`.

### Division of labor

Sub-agents edit source, run `cargo test` and the SwiftPM build, and act as
fresh-context reviewers. Only the orchestrating session builds the app, runs
`tests/run.sh`, touches launchd and captures receipts. Scope sub-agent tasks
so none needs the built app.

### Retry and environment policy

A live case that fails is rerun once. A failure that reproduces is a finding,
reported with its output, never recorded as flaky. The exceptions are the three
refusal signatures in AGENTS.md "Sandboxed automation harnesses": XPC lookup
refused with code 4099 or error 159, `log: Cannot run while sandboxed`, and
`codesign` reporting an unchanged signed app invalid. For those, rerun once
outside the sandbox and treat the failure as environmental only when the
unsandboxed rerun passes. Deny-line omission by the Sandbox kext is
intermittent and known: a case that fails only on missing deny lines is rerun
once and, if it reproduces, reported as a finding with its log capture.

### Static receipts

Two acceptance conditions cannot be observed at runtime without root tracing,
so their receipts are static checks in `cargo test` or `source_drift`:

- `spawns no PlistBuddy`: no caller of `plist_key_string` or `read_bundle_info`
  is reachable from `cmd_run`. Today's callers are `app_layout.rs`,
  `bundle.rs` and `runner_commands.rs`; after R2 only the BYOXPC install and
  verify paths remain.
- `parses the manifest once`: `evidence::load_manifest` has exactly one call
  site reachable from `cmd_run`. Today's two are in `run_flow.rs` and
  `runner_select.rs`.

The synthetic-app-root control with no service Info.plist is the live
complement.

### Run-varying set

For the five-specimen baseline diff and every fixture regenerated from a live
run, normalize these before comparing: process ids, including worker and
validator pids; every timestamp, `*_unix_ms`, duration and deadline value;
scratch and `tests/out` paths; `run_id` and `PW_TEST_RUN_ID` labels; the build
stamp; `sandbox_log_capture` bodies and counts; `runner_client.argv`;
`capture_nonce`; and hashes of binaries this change rebuilt. `policy_sha256`
and `applied_sha256` are not run-varying and must equal the baseline for an
unchanged specimen. Anything else that differs is either an intended contract
change listed in D1, D2 or D5, recorded as such, or a stop condition.

### Golden rule

A regenerated golden, fixture or shape diff is self-accepted when every
removed key is in R1, every added key is a D1 or D2 name, and every changed
value is in the run-varying set or is a version moving to 13 or 5. Write the
diff summary to the acceptance record and the decision log. Any other
difference is a stop condition.

### Increment exit conditions

- **I1 done when** the shared Rust modules exist with byte-identical
  `sbpl-check` output, the two specimens are added, the five response 12
  captures are retained and registered, the matrix fixture is written against
  D1, the default battery is green, the decision log exists, and the work is
  committed.
- **I2–I4 done when**, on one integrated candidate in whatever order the
  dependencies allow: `./build.sh`, `cargo test`, `runner_unit`, the default
  battery and `order_barrier_mutations` are green; every D1 row and every D2
  failure-table shape has a receipt; `docs/contract.json` is at 13 and 5 with
  generated copies regenerated; the R10 search is done with every remaining
  match classified in the decision log; and each sub-step is committed.
- **I5 done when** both ledgers are complete, `generate_limits.py` and
  `generate_contract.py` outputs are committed, `source_drift` is green,
  `--all` is green on the candidate and registered in `tests/RETAINED.json`,
  the five-specimen diff is accepted under the golden rule, and the work is
  committed.

### Stop conditions

Stop and report only when: a live run contradicts a D1 row or a D2
failure-table row; a receipt cannot be produced after the unsandboxed retry; a
change outside D1, D2 or D5 appears necessary; `--all` fails on the candidate
for a reason not already classified in the decision log; or a destructive
action outside the pre-authorized list is needed. Everything else: decide,
log, continue. No check-in is required. If the operator wants touchpoints, the
natural ones are after I1, the last point before deletions begin, and before
the final `--all` and closeout.

### Closeout

After the integrated `--all` passes and is registered: update the
`baseline_response12` README's plan references to point at
`tests/FAILURE-PROPAGATION-CONTRACT.md` and keep that directory as the
response 12 receipts; delete `DRIFT-REMOVAL-PLAN.md`,
`DRIFT-REMOVAL-CANDIDATES.md` and `FIVE-FOLLIES.md` in the closeout commit,
since `git log` is authoritative and documentation describes current
behavior; leave `DRIFT-REMOVAL-DECISIONS.md` in place for operator review and
remove it only on their instruction.
