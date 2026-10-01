# Removing the drift verdict

Status: READY for implementation as of 2026-10-01; implementation has not
started. The matrix's response 12 columns are verified against live output
(see the scenario matrix). The S1–S3 helper removals include retirement of the
host sandbox-library admission check (D6.47). No sandbox-library identity is
collected (D6.52). One overall client deadline and controller-owned transport
failures settle the stdin handoff contract (D6.56, resolving D6.55).
The readiness gate below separates settled decisions from execution
checks. Every decision is a numbered D6 row and any later change to DESIGN or
REMOVAL is a new row; a later row supersedes an earlier row where stated. The
inventory baseline is df333b4 (request schema 3, response schema 12, worker ABI 7, controller
envelope 4); source line numbers are as of that commit.

## Premise

PolicyWitness reports `steps[].drift` (`true`, `false`, `null`) and
`steps[].comparison.conclusion` (`agreement`, `disagreement`,
`directional_consistency`, `unavailable`): verdicts about the relation between
a `sandbox_check` answer and observed enforcement. This plan removes them, the
unobserved deny-signal channel and four duplicate or constant fields; keeps
every observation and relation that fed them as typed obligations; adds a
specimen dossier; and drops reading of earlier reply versions. The reader
computes any label. PW supplies none on the wire, in test equipment or in a
guide recipe.

Code and documentation describe the shipped app. Historical names, paths and
interpretations earn no compatibility machinery. Schema numbers move with the
implementation that emits the new shape, never before it.

The unused Swift attempt, query and sandbox-application implementations from
[FIVE-FOLLIES.md, S1–S3](FIVE-FOLLIES.md#second-sweep) are also removed, with
their exclusive tests and build dependencies, and with the host
sandbox-library loader and its admission check (D6.47). R2 defines the boundaries around
the production code they share files with. S4 and S6–S9 are separately recorded
in [potential additions](DRIFT-REMOVAL-CANDIDATES.md); they are not adopted by
this plan.

## DESIGN

### D0. The one rule

The reply may describe. It may not conclude. No field in a response 13 reply
has a value space that includes a claim about the relation between the
prediction and enforcement. Descriptive values are: what was submitted, what
each channel returned and on what basis, whether the two submitted scopes
match, the order PW established by its own actions, and which obligations of a
comparison are or are not discharged, with the evidence that discharges them.
Descriptive derivations from the raw records are permitted, including channel
summaries, submitted-scope relations, ordering eligibility and obligations.
Evidence validation and selection may inspect both channels. A proposed field
fails when its value asserts agreement, disagreement, drift or consistency
between prediction and enforcement, whatever name the field uses. Derivability
alone is not a rejection rule (D6.25).

### D1. The per-step comparison record

`steps[].comparison` keeps `prediction`, `observation`, `observation_basis`,
`operation_relation`, `target_relation` and `order` unchanged. `conclusion`,
`scope` (D6.13) and `steps[].drift` are removed. Of the five removed
`limitations` strings, three become `obligations`, state stability moves to
`comparison_conditions`, and the duplicate ordering string disappears; the
remaining strings stay a list.

```json
"comparison": {
  "prediction": "deny",
  "observation": "succeeded",
  "observation_basis": "completed_worker_status",
  "operation_relation": "matched",
  "target_relation": "same_submitted",
  "order": "query_first",
  "obligations": {
    "sandbox_attribution":     { "status": "not_required" },
    "runtime_target_identity": { "status": "unestablished" },
    "target_mutation":         { "status": "none" }
  },
  "limitations": []
}
```

| Path | Type | Rule |
| --- | --- | --- |
| `obligations.sandbox_attribution.status` | string | `unestablished` when `observation` is `permission_failure` or `other_failure`, or when `limitations` contains `exec_result_failed_after_spawn`; `not_applicable` when `observation` is `unavailable`; `not_required` otherwise (D6.14) |
| `obligations.runtime_target_identity.status` | string | `unestablished` when the query's `filter_kind` is `path` or the mapped attempt filter is `path`; `not_applicable` otherwise |
| `obligations.target_mutation.status` | string | `none` when no run step qualifies under the rule below; otherwise `unordered` when `order` is `unestablished`, or `after_query` when `order` is `query_first`. `none` does not establish an unchanged target. The obligation names no step: which step removed the target is in the attempt records (D6.42) |
| `limitations` | array of string | may be empty; vocabulary unchanged: `query_plan:*`, `prediction:*`, `attempt:*` (including the lifecycle entries), `exec_query_not_full_spawn_prediction`, `compound_attempt`, `attempt_operation_unestablished`, `broad_query_operation`, `operation:*`, `target:*`, `query_filter_scope_unestablished`, `submitted_target_unavailable`, `exec_result_failed_after_spawn`, `host_path_resolution_changed`. `query_attempt_order_unestablished` is gone (it equalled `order != query_first`) |

No step qualifies unless the query has `filter_kind: path`, a nonnull submitted
`filter_value`, and no `query_plan:*` limitation. Given that, a run step
qualifies when its attempt has `result_source: worker`, `requested_kind: file`,
`requested_action: unlink`, `outcome: ok`, `rc: 0`, and `requested_path` equal to
that submitted filter value; the current step counts as a run step. Host-resolved
paths do not participate. An excluded query therefore keeps `none` even if a
later attempt removes its submitted path. That exclusion is the obligation's
whole content beyond existence, and it is a reading rule, not an otherwise
unavailable observation: the query's `filter_kind`, `filter_value`, its
`query_plan:*` limitation and every unlink attempt are all in the reply, so a
reader has every input and can apply the rule unaided. The status ships as a
convenience projection — the rule applied once by the producer instead of by
each reader — and because it replaces a field the wire carries today. Whether
that warrants a producer-side derivation at all is open, and belongs to S9 in
[the candidates document](DRIFT-REMOVAL-CANDIDATES.md); this plan retains it
(D6.26, D6.42).

No obligation's value space contains `established`. State stability does not
vary per step: the reply carries `comparison_conditions:
{ "unestablishable": ["state_stability"] }` beside `steps`, present whenever
`steps` is present, including an empty array, except on a
`runner_reporting_failed` reply, where it is withheld with every comparison
(D6.9, D6.19, D6.26).

#### Scenario matrix

The S, B and C rows specify 32 scenario expectations: a real-validator plan of
24 steps, a steered-validator plan of 7, and a pre-apply failure. R and T are
two additional failure controls with separate owners.

Seven of the nine columns — `prediction`, `observation`, `observation_basis`,
`operation_relation`, `target_relation`, `order` and `limitations` — are
unchanged by this plan, so every row's values for them were checked against
response 12 output on 2026-09-30. Twenty-five rows (including the three `as
S01` aliases) matched captured tuples in the retained `release-0.2.4-default`
evidence; the remaining rows were run live. Two live specimens and their raw
envelopes are preserved under
[tests/fixtures/comparison/baseline_response12/](tests/fixtures/comparison/baseline_response12/)
with the method and per-row provenance in that directory's README. One row was
wrong and is corrected here: S22 also carries `submitted_target_unavailable`,
because a `none` filter submits no target to compare. The `obligations` object
and `comparison_conditions` remain design expectations, since no build emits
them; I2 still owns capturing response 13 receipts, app identity and checker
output in managed output before replacement coverage is credited. The deadline
example has an existing
[generated control](tests/fixtures/disposition/a1_expected.json), whose source
and captured-versus-generated distinction are documented in the
[fixture README](tests/fixtures/disposition/README.md).
Obligations are abbreviated A (sandbox attribution), I (runtime target
identity), M (target mutation); `nr` = `not_required`, `na` =
`not_applicable`, `un` = `unestablished`.

| ID | Scenario | Pred | Observation / basis | Op | Target | Order | A | I | M | Limitations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | allow, read succeeds | allow | succeeded / completed_worker_status | matched | same | query_first | nr | un | none | |
| S02 | deny, read EPERM | deny | permission_failure / permission_errno | matched | same | query_first | un | un | none | |
| S03 | allow, mode-000 file EACCES | allow | permission_failure / permission_errno | matched | same | query_first | un | un | none | |
| S05 | query denied path, attempt other path | deny | succeeded / completed_worker_status | matched | different | query_first | nr | un | none | `target:different_submitted` |
| S06 | query write, attempt read | allow | succeeded / completed_worker_status | different | same | query_first | nr | un | none | `operation:different` |
| S07 | absent path, both channels | unavailable | other_failure / completed_worker_status | matched | same | unestablished | un | un | none | `query_plan:path_unresolved_at_planning`, `prediction:query_not_requested` |
| S08 | compound create | unavailable | succeeded / completed_worker_status | unresolved | same | unestablished | nr | un | none | `query_plan:path_unresolved_at_planning`, `prediction:query_not_requested`, `compound_attempt`, `operation:unresolved` |
| S09 | unsupported attempt kind | allow | unavailable / no_completed_worker_result | unresolved | unresolved | query_first | na | un | none | `attempt:attempt_not_supported`, `attempt_operation_unestablished`, `operation:unresolved`, `target:unresolved`, `attempt:unsupported` |
| S10 | sysctl planning exclusion | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | na | none | `query_plan:prediction_unavailable_pair`, `prediction:query_not_requested` |
| S11 | bare `process-exec` query, spawn ok | unavailable | succeeded / spawned_child | different | same | unestablished | nr | un | none | `prediction:no_usable_verdict`, `exec_query_not_full_spawn_prediction`, `operation:different` |
| S12 | `file-read*` query | allow | succeeded / completed_worker_status | unresolved | same | query_first | nr | un | none | `broad_query_operation`, `operation:unresolved` |
| S13 | mach deny, kr=1100 | deny | permission_failure / bootstrap_permission_result | matched | same | query_first | un | na | none | |
| S14 | mach unknown service, kr=1102 | allow | other_failure / completed_worker_status | matched | same | query_first | un | na | none | |
| S15 | `process-exec*`, spawn ok, exit 0 | allow | succeeded / spawned_child | matched | same | query_first | nr | un | none | `exec_query_not_full_spawn_prediction` |
| S16 | spawn ok, child exits 1 | allow | succeeded / spawned_child | matched | same | query_first | un | un | none | `exec_result_failed_after_spawn`, `exec_query_not_full_spawn_prediction` |
| S17 | spawn of mode-000 target, EACCES | allow | permission_failure / permission_errno | matched | same | query_first | un | un | none | `exec_query_not_full_spawn_prediction` |
| S18 | spawn of absent target | unavailable | other_failure / completed_worker_status | matched | same | unestablished | un | un | none | `query_plan:path_unresolved_at_planning`, `prediction:query_not_requested`, `exec_query_not_full_spawn_prediction` |
| S19 | ordered unlink of queried path | allow | succeeded / completed_worker_status | matched | same | query_first | nr | un | after_query | `host_path_resolution_changed` |
| S20 | `process-exec-interpreter` query, binary spawn | allow | succeeded / spawned_child | different | same | query_first | nr | un | none | `exec_query_not_full_spawn_prediction`, `operation:different` |
| S21 | `local_name` query, kr=1100 | allow | permission_failure / bootstrap_permission_result | matched | unresolved | query_first | un | na | none | `query_filter_scope_unestablished`, `target:unresolved` |
| S22 | `none` filter on a file query | allow | succeeded / completed_worker_status | matched | unresolved | query_first | nr | un | none | `query_filter_scope_unestablished`, `submitted_target_unavailable`, `target:unresolved` |
| S23 | allow, `access` succeeds | as S01 | | | | | | | | |
| S24 | allow, `open_write` succeeds | as S01 | | | | | | | | |
| S25 | read of the path S19 unlinked, ENOENT | allow | other_failure / completed_worker_status | matched | same | query_first | un | un | after_query | `host_path_resolution_changed` |
| B1 | steered deny, read succeeds, ordered | deny | succeeded / completed_worker_status | matched | same | query_first | nr | un | none | |
| B2 | verdict omitted, read succeeds | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | none | `prediction:validator_no_verdict` |
| B3 | verdict omitted, unlink of queried path | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | unordered | `prediction:validator_no_verdict`, `host_path_resolution_changed` |
| B4 | validator error record | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | none | `prediction:no_usable_verdict` |
| B5 | verdict omitted, read of a path B6 unlinks | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | unordered | `prediction:validator_no_verdict`, `host_path_resolution_changed` |
| B6 | allow, ordered unlink | allow | succeeded / completed_worker_status | matched | same | query_first | nr | un | after_query | `host_path_resolution_changed` |
| B7 | allow, read succeeds (control) | as S01 | | | | | | | | |
| C1 | policy fails to compile, nothing runs | unavailable | unavailable / no_completed_worker_result | matched | same | unestablished | na | un | none | `prediction:validator_not_invoked`, `attempt:slot_incomplete`, `attempt:not_reached` |
| R | `runner_reporting_failed` | no `comparison` object and no `comparison_conditions`; both fallback levels tested in `ReplyFailureTests` | | | | | | | | |
| T | allow policy, FIFO read starts after release, then worker deadline | allow | unavailable / no_completed_worker_result | matched | same | query_first | na | un | none | `attempt:slot_incomplete`, `attempt:started_without_result` |

Rows with identical objects (S01, S23, S24, B7) are one scenario under
different attempt actions, which `attempt.requested_action` distinguishes.
The pairs `attempt:attempt_not_supported` with `attempt:unsupported` (S09) and
`attempt:slot_incomplete` with `attempt:not_reached` (C1) come from the missing
reason and the disposition record respectively; both stay.

#### Specimen mechanics the rows depend on

Three facts constrain how the matrix specimens are built; all three were
established by running them.

- A step whose attempt is `unlink` reaches `operation_relation: matched` only
  when its query operation is `file-write-unlink`. S19, S25, B3, B5 and B6
  depend on this.
- A steered validator cannot omit a verdict by skipping an output line. The
  host counts uniquely associated records and refuses a short batch run-level
  with `validator_unavailable` before any comparison exists. The omitted-verdict
  rows (B2, B3, B5) require the validator I/O deadline seam that
  `runner_outcome_validator_no_reply` already uses: `_test_overrides`
  `validator_executable_path` plus `validator_io_timeout_ms`, with a stub that
  answers the other steps and then stalls. Specimen B therefore ends in
  `normalized_outcome: validator_no_reply`, not `ok`, while B1, B6 and B7 keep
  their verdicts and `query_first` order in that same reply. The matrix reader
  asserts the per-step records against a run whose run-level outcome is a
  validator failure.
- Specimen B is not idempotent: it unlinks the paths it queries, and a run that
  fails after release still performs its attempts. The case owns recreating its
  files before every run, including after a failed one.

T uses the existing `worker_attempt_in_flight_at_deadline` setup: an existing
FIFO with no writer, an allow policy, a completed validator query, the release
and acknowledgement chain, and a worker deadline while `open_read` is in
flight. The test must establish those raw facts before comparing T. Its later
unreached step may also retain an allow prediction and `query_first`; failure
to complete an attempt does not erase an earlier query. R belongs to the
reply boundary, so it is not fed through `comparisonEvidence(...)` (D6.32).

### D2. The specimen dossier

`data.specimen` is a controller-owned object under envelope 5, present on
every `kind: "run"` envelope — a completed run, `bad_request`, `xpc_error` and
the pre-execution `tool_error` failures alike, all of which carry one `data`
skeleton (D6.36). It records
the controller's request-source identity and pre-invocation observations;
whether anything ran is established by the execution records it references.
It does not embed the source or parameter values. No alias remains at a former
path.

| `data` key | Disposition |
| --- | --- |
| `app_provenance`, `runner_provenance` | move to `specimen.*`, shape unchanged |
| `policy_augmentation` | move to `specimen.policy.augmentation`, always present (D6.15) |
| `request_path` | move to `specimen.request_path` |
| `runner_service_bundle_id`, `runner_service_name`, `runner_registry_id`, `runner_service_executable` | remove; each equals or derives from a `runner_provenance` field |
| `policy_check` | stay; its `sbpl-check` output is kept verbatim, including that tool's own imports block |
| `runner_client` | stay; extend with delivery and supervision facts under D6.56 |
| `runner_result`, `runner_sandbox_diagnostics`, `runner_startup_diagnostics`, `sandbox_log_capture`, `timeout_ms` | stay; `timeout_ms` now covers the whole client operation under D6.56 |

```json
"specimen": {
  "request_path": "tests/fixtures/pw_runner/specimen_file_read_deny.json",
  "policy": {
    "format": "sbpl",
    "augmentation": { "status": "not_requested", "applied": [],
                      "original_sha256": "…", "applied_sha256": "…", "error": null },
    "imports": {
      "status": "complete",
      "basis": "controller_scan_of_applied_source",
      "closure_sha256": "…",
      "records": [
        { "name": "system.sb", "resolved_path": "/System/Library/Sandbox/Profiles/system.sb",
          "sha256": "…", "size_bytes": 12345, "mtime_unix": 1700000000, "error": null }
      ],
      "cycle": null,
      "limits": { "depth": 8, "count": 64, "file_bytes": 1048576, "total_bytes": 8388608, "wall_ms": 1000 },
      "exceeded": null,
      "failure": null
    }
  },
  "host": { "macos_version": "14.8.3", "macos_build": "23J220", "kernel_release": "23.6.0",
            "arch": "arm64", "basis": "sysctlbyname" },
  "runner_provenance": { "…": "unchanged shape" },
  "app_provenance": { "…": "unchanged shape" },
  "binaries": {
    "service":   { "manifest_id": "com.yourteam.policy-witness.PWRunner", "path": "…", "manifest_sha256": "…",
                   "manifest_lc_uuid": "…", "manifest_entitlements": {}, "manifest_entitlements_error": null,
                   "basis": "app_manifest_entry",
                   "verification": { "status": "not_compared", "actual_sha256": null,
                                     "reason": "selection is the app's own manifest entry" } },
    "worker":    { "manifest_id": "PWRunner/pw-probe-runner", "…": "same shape" },
    "validator": { "manifest_id": "PWRunner/sb_api_validator", "…": "same shape" }
  },
  "conditions": {
    "prediction_unavailable_pairs": [ { "operation": "sysctl-read", "filter_kind": "sysctl_name" } ]
  },
  "references": {
    "policy_sha256": "/data/runner_result/policy_sha256",
    "applied_profile": "/data/runner_result/applied_profile",
    "steps": "/data/runner_result/steps",
    "validator_records": "/data/runner_result/validator_subprocess/records",
    "ordering": "/data/runner_result/runner_subprocess/ordering",
    "comparison_conditions": "/data/runner_result/comparison_conditions",
    "sandbox_log_capture": "/data/sandbox_log_capture",
    "policy_check": "/data/policy_check",
    "build": "/build"
  }
}
```

| Path | Type | Rule |
| --- | --- | --- |
| `request_path` | string or null | the path given to `run`; null when no path was given (see the failure table) |
| `policy.format` | string or null | the submitted string, even when unsupported; null when absent or not a string |
| `policy.augmentation` | object | always present; `status`, `applied`, nullable `original_sha256` and `applied_sha256`, and nullable `error`, under the failure rules below (D6.28) |
| `policy.imports.status` | string | `complete`, `incomplete`, `failed`, `not_applicable`, under the scan rules below |
| `policy.imports.basis` | string | constant `controller_scan_of_applied_source`: the controller walks the source after augments, before invoking the runner; it is not evidence of what the worker's compiler read |
| `policy.imports.closure_sha256` | string or null | over the applied source and successfully hashed import records whenever the scan ran; `status` says whether the scanned closure is complete |
| `policy.imports.records[]`, `cycle` | as `sbpl-check` | unchanged shapes |
| `policy.imports.limits` | object | depth 8, count 64, imported file 1 MiB, total 8 MiB, cooperative work budget 1,000 ms, recorded with counting rules in `docs/limits.json`. Measured against the real closure: `sbpl-check` over `(import "system.sb")` resolves 2 records totalling ~13 KB and returns in 0.02 s including the compile, so the budget has roughly fifty times the headroom a representative profile needs. I4 measures the WebProcess-size specimen and the cutoff behavior before the numbers are published (D6.37) |
| `policy.imports.exceeded` | string or null | the first bound hit: `depth`, `count`, `file_bytes`, `total_bytes` or `wall_ms` |
| `policy.imports.failure` | string or null | the first scan problem, including why the scan could not start; null for a complete scan or an ordinary absence of source |
| `host.macos_version`, `macos_build`, `kernel_release`, `arch` | string or null | `kern.osproductversion`, `kern.osversion`, `kern.osrelease`, `hw.machine`; null when the read fails (D6.16) |
| `host.basis` | string | constant `sysctlbyname`: the mechanism for the four facts above |
| `binaries.*` | object | each selected executable path and its baseline metadata from the app manifest the controller already reads; `manifest_*` fields are baseline metadata, never observations of the selected binary; `verification.status` is `not_compared`, `match`, `mismatch` or `unavailable` (D6.29, D6.49) |
| `conditions.prediction_unavailable_pairs` | array | distinct `(operation, filter_kind)` pairs of steps carrying `query_plan:prediction_unavailable_pair` |
| `references` | object | RFC 6901 JSON pointers from the envelope root to every record the dossier does not own. Key set and values are fixed by envelope 5, not computed from presence; a pointer to a withheld or absent record is still present (D6.20) |

Host facts, binaries and the imports scan are gathered before invocation.
Dossier collection failures are recorded and do not change whether the request
is admitted or the runner is invoked. For a controller refusal, collect what
is available without invoking the runner. All dossier keys stay present;
unavailable scalar facts are null, lists are empty when no records exist, and
statuses explain unavailable collections. `app_provenance` may remain null,
as in its existing shape. An envelope without a runner reply has
`conditions.prediction_unavailable_pairs: []`; this means no reported pairs.

#### Request and augmentation failures

Hash only string source bytes that actually exist. `original_sha256` identifies
the pre-augmentation string; `applied_sha256` identifies the post-resolution
string selected for invocation, including the unchanged source. Neither hash
identifies parameters or proves worker compilation. Augmentation is atomic:
failure reports no applied names and no applied hash.

| Request state | `policy.format` | Augmentation | Imports |
| --- | --- | --- | --- |
| String source, no augments (also null or empty augments) | submitted string or null | `not_requested`, `applied: []`, equal source hashes, `error: null` | scan that source |
| Augments successfully applied | submitted string or null | `applied`, applied names and hashes; original hash null if no original string existed | scan the resulting source |
| Augment resolution refused | submitted string or null | `failed`, `applied: []`, original hash if available, applied hash null, refusal diagnostic | `not_applicable`, `failure: augmentation_failed` |
| Missing/malformed policy or source, no augments applied | submitted string or null | `not_applicable`, `applied: []`, both hashes null, `error: null` | `not_applicable`, no records or hash |
| No request value: the file is absent, unreadable, not JSON, or not an object | null | `not_applicable`, `applied: []`, both hashes null, `error: null` | `not_applicable`, no records or hash |
| No request path: the argument is missing or a flag value is invalid | null | as above, with `specimen.request_path: null` | `not_applicable`, no records or hash |
| Runner refusal or XPC failure after successful resolution | as collected before invocation | preserve the collected record | preserve the collected record |

Every imports object carries its basis, limits, records, cycle, exceeded and
failure keys. A scan that does not run has `records: []`, `cycle: null`,
`closure_sha256: null` and `exceeded: null`.

The table governs every `kind: "run"` envelope, because every failure before
execution already produces one. A missing argument, an invalid flag value, an
absent request file and a request that is not a JSON object all print a run
envelope today; under envelope 5 they carry the same `data` skeleton as a
completed run, with every key present and the dossier at its collected state.
One writer owns that: `cmd_run` prints the envelope for each of these, and the
`cli.rs` catch-all stays only as a last resort for an error that escapes it. The
`data.error` constant string that path emits now is removed, since `result.error`
already carries the message (R1). The uniform shape does not unify the verdict:
these keep `normalized_outcome: tool_error` and exit 2, distinct from
`bad_request` at exit 1. Dossier collection does not change any of that, and it
never converts a CLI failure into an execution: what ran is established by the
execution records the dossier references, all of which are null here.

After runner selection and augmentation, serialize the request value **once, to
a string the controller holds**, even when no patch was needed. Scan that same
string, and hand that same string to every reader. `specimen.request_path`
remains the user's original path. Replacing the original request during
collection must not change the submitted bytes (D6.30).

The readers are subprocesses, so the question is how the bytes reach them, and
the answer is not a file. `pw-runner-client` reads its request path into memory
and sends those bytes over XPC, so a temporary file is an IPC medium between two
processes PW owns: the controller writes it, the client reads it back, and
nothing else ever looks at it. One string in the controller is a stronger
version of the same-bytes guarantee than a shared file, and it is the shared
data structure the guarantee actually wants. So give the client `--request -`
and pass the serialized request on its stdin; its `usage()` text and the
client's documented surface gain that option, which is additive and is not the
`policy-witness` CLI contract. D6.56 changes the meaning of the existing
`--timeout-ms` allowance as specified below; it adds no controller flag.

A file survives in exactly one place: the `xpc_error` fallback that invokes
`sbpl-check --request <path>`. Write it there, from the same held string, and
remove it before returning; that path is rare and already an error path. This
is not only fewer calls. `write_temp_request` has no cleanup today and its
directory held 40 leftover request files on the development machine when this
was measured, each carrying policy source; the ordinary run now creates none at
all, so the leak ends by deletion rather than by a cleanup guard on every exit
(D6.50, superseding D6.38). Nothing resolves a request field relative to the
request file's directory — augments resolve against the app root and the runner
never receives a path — so no field's meaning depends on where the bytes came
from.

#### Client deadline and transport failures

The controller owns one absolute `CLOCK_MONOTONIC` deadline, established just
before client spawn from `--timeout-ms`. Startup, stdin delivery and EOF,
request acquisition in the client, XPC reply wait, output collection and client
exit consume that same allowance. Pass the deadline across the private
controller/client boundary using the existing shared-budget mechanism's clock
and validation rules; never start a fresh allowance after input delivery or
before the RPC wait. A standalone client establishes its deadline before
request acquisition. Keep the current default and minimum, and reject values
that cannot form a finite deadline. This deliberately replaces the current
reply-wait-only meaning (D6.56).

At expiry, stop request delivery and ordinary collection and start bounded
cleanup. Reuse the supervisor's fixed 1,000 ms cleanup grace for closing pipes,
owned-child termination and reaping, retaining any output collected during
cleanup. This grace buys no further request or RPC work. Record unconfirmed
cleanup as such. Ownership covers the spawned client, not its launchd-owned
XPC service or that service's children; client cleanup does not establish their
termination. Worker and validator budgets remain independent. Request
preparation/dossier collection, fallback diagnostics and optional log capture
are outside this client allowance; it is not an end-to-end CLI runtime promise.

Factor the reusable nonblocking I/O, absolute-budget, process-observation and
owned-cleanup core out of `controller/src/log_capture.rs`, then add optional
stdin delivery for `runner_client.rs`. Preserve the log boundary's behavior.
The runner-client boundary writes input while draining both output streams;
close stdin immediately after the last byte so the client can observe EOF.
Partial writes, interruptions and backpressure must not deadlock, and a broken
pipe must not terminate the controller. On a write failure, close stdin and
continue collecting available output under the original deadline. Use
`ValidatorClient.swift`'s duplex collection and write-failure controls as the
behavioral model, with Rust subprocess controls for this boundary.

Keep `JsonOutputCapture`'s strict parsing, diagnostic retention and existing
runner capture limits. The log supervisor's overflow-stop and zero-exit
requirements are boundary policies, not defaults for the runner client:
retain up to the runner limits while continuing to drain/count excess bytes
within the deadline, and keep nonzero client exit independent of received JSON.
Never parse a truncated or incompletely collected stdout prefix as a reply,
even when that prefix is valid JSON. Streaming counts describe bytes actually
read, with EOF/read-error/cutoff observations explaining incomplete collection;
do not reconstruct an `Output` from a retained prefix and call its length the
total received. Share the capture finalization rules with `utils.rs` rather
than replacing its other receivers.

Extend `data.runner_client` with `request_delivery` containing
`bytes_expected`, `bytes_written`, `stdin_closed` and nullable `error`, and a
`supervision` report using the shared budget, stream, process and cleanup
observations with a runner-client boundary. Delivery is null for a helper
invocation using the retained file-input interface; normal runs use stdin.
These are controller observations:
accepted pipe writes and closing the writer do not prove that the client read
the bytes or that XPC delivered them. Preserve existing capture and timing
fields; `exit_code` is null when no numeric exit code was observed, with signal
and reaping facts in supervision. Retain separate delivery, output, wait and
cleanup errors when they coexist. Once a child exists, return its capture and
observations on failure instead of escaping through an error path that discards
them. Before invocation, the uniform run skeleton still has null execution
records.

A delivery failure, expiry of the controller's overall deadline or failed
transport supervision makes the envelope's `result.ok` false,
`result.normalized_outcome: tool_error`, with exit 2 and a controller diagnostic.
Use this existing controller failure category; do not invent a worker or XPC
failure to represent the handoff. This result takes precedence even if captured
stdout contains an `ok` reply. Retain that complete reply unchanged in
`data.runner_result`, along with all capture and process diagnostics. D5's
version gate still controls any interpretation of it; a transport failure does
not authorize reading an unsupported reply. Where transport completes, existing
runner-result and D5 version-result selection applies. Nonzero client exit
alone must not overwrite a valid failure reply. A client-generated XPC failure
received within the allowance remains that client's reported failure.

The `xpc_error` fallback remains an independent diagnostic of a supported
reply. Failure to create or write its temporary request file becomes
`PolicyCheckCapture::unavailable`, as helper launch failure already does; retain
the original reply and startup diagnostics. Remove any owned temporary file
on every fallback exit, preserving cleanup errors without replacing the
original failure. A controller delivery error alone does not trigger fallback
compilation. I4 owns transport and fallback controls; I5 updates the documented
timeout, capture and result contracts.

#### Binary selection and comparison

The service path comes from the selected runner's executable path. Worker and
validator paths come from their admitted executable overrides when present,
otherwise from the selected XPC bundle's `Contents/MacOS` helpers. An invalid
override is reported as an unavailable selection, not silently replaced with
the built-in helper. These paths describe intended invocation; hashing does
not prove that a process launched or mapped those bytes.

For both built-in and BYOXPC selections, the baselines are the app manifest's
built-in `PWRunner` service, `PWRunner/pw-probe-runner` and
`PWRunner/sb_api_validator` entries, selected by their shipped bundle paths.
The external service identifier does not select a different baseline.
`manifest_id` names the expected baseline entry even if it is missing.
Missing, unreadable or invalid manifests/entries produce null unavailable
metadata and `verification.status: unavailable` with a reason.

The dossier does not hash a file the app already describes. `load_app_provenance`
reads the Evidence manifest on every run, and `evidence::verify_manifest`
already hashes every entry that declares a hash and reports each mismatch,
under `PW_VERIFY_EVIDENCE=1`. A per-run hash of three hand-picked entries would
be a narrower second copy of that mechanism, always on, beside the complete one
this plan leaves untouched — and for a built-in selection its answer is
constant for a given build. So:

- When the selected path is one of those manifest entries, report the baseline
  metadata from the manifest already in memory and set
  `verification.status: not_compared` with that reason and a null
  `actual_sha256`. Integrity of the app's own files belongs to
  `PW_VERIFY_EVIDENCE`, which covers every entry rather than three, and to the
  signature; a manifest that ships inside the bundle it describes cannot
  establish more than that.
- When the selected path is an executable override or a BYOXPC copy — not a
  manifest entry — hash it before invocation, because nothing else in the
  envelope identifies those bytes. Compare against the built-in baseline as
  above: equal hashes produce `match`, complete hashes that differ produce
  `mismatch`, and a re-signed BYOXPC copy may legitimately differ. An
  unreadable selected file has `actual_sha256: null` and
  `verification.status: unavailable`.

`basis` says which of these produced the record: `app_manifest_entry` or
`controller_file_hash_before_invocation`. Neither mismatch nor unavailable
changes the run outcome (D6.49). Manifest UUID and
entitlements are labeled `manifest_lc_uuid`, `manifest_entitlements` and
`manifest_entitlements_error`; existing runner provenance stays separate.
Each binary object keeps all its keys: `path` is null when selection is
unavailable, hashes and baseline metadata are nullable, and `reason` is null
only for `match`. A mismatch reason identifies the baseline comparison; an
unavailable reason identifies selection, manifest or file-read failure.

#### Import collection and bounds

The dossier's object is the envelope's import inventory of record: the
controller's own scan of the source it selected for invocation, identified by
its `basis`. `data.policy_check` keeps `sbpl-check`'s separate flat `imports`
array, `imports_cycle` and `imports_truncated` verbatim; it is null except on
the fallback paths that run that tool, so the two inventories coexist only
there. They are different observations — a different scanner, a different
moment, and only one of them bounded by these limits — and neither is a claim
about what the worker's compiler read. They may disagree, and a disagreement is
not an error. `references.policy_check` points at the tool's record so the
relation is explicit; the dossier never copies it. Because the shared I1
extraction serves both, it must keep `sbpl-check`'s existing output byte-identical
while the dossier renders the object shape (D6.35).

`complete` means the scanner exhausted the literal import closure under its
documented search paths with no unresolved names, cycles, nonliteral import
forms, decoding errors or exceeded limits. It does not mean compiler-complete:
macro evaluation and the files the worker compiler actually reads are outside
this observation. An incomplete traversal keeps every collected record and a
hash of the source plus successfully hashed imports under the existing closure
hash algorithm. `failed` means collection could not start because of a
collector failure; `not_applicable` means no post-resolution source was
available. Neither receives a closure hash.

Use one opened descriptor per unique resolved import. Open nonblocking, check
the descriptor is a regular file before reading, then read bounded chunks with
at most one extra byte to detect overflow. Reject FIFOs, devices and other
nonregular files as incomplete inventory. Hash and lex the same buffered bytes;
do not reopen a path for recursion. Collect metadata from that descriptor.
This prevents the hash and traversal from describing different reads, without
claiming an atomic snapshot of a concurrently modified file.

Top-level imports have depth 0; depth 8 is recorded without expansion. Count
each emitted unique record, including unresolved/error records, toward 64.
The 1 MiB limit applies to each imported file; 8 MiB counts the applied source
and unique imported bytes retained for hashing/lexing. Stop at the first bound,
record `exceeded`, and mark `incomplete`; no truncated file gets a full-file
hash or recursive expansion. Do not read an entire file and then check its
size. Nonliteral forms and invalid UTF-8 must not silently count as completion.

`wall_ms` is a cooperative monotonic work budget starting before the root scan.
Check it between resolution, metadata, read, hashing and lexing work, using
bounded chunks inside long loops. Stop scheduling work at expiry and report
`exceeded: wall_ms`. It does not interrupt an in-flight filesystem syscall or
bound OS scheduling delays; the docs must not promise a hard one-second return.
The normal-run scanner is synchronous and introduces no background task or new
shipped helper. Measure both representative-profile cost and cutoff behavior
in I4; a hard elapsed-time guarantee would require a new design decision.

#### Host facts and library identity

The dossier's four sysctl facts describe the environment. They do not identify
the sandbox libraries used by the worker or validator. Neither the dossier nor
the runner collects a sandbox-library identity or a shared-cache UUID (D6.52).
There is no identity-specific collector, presence rule, fallback-retention
requirement or test control. The loader and its admission check are still
removed under D6.44/47; worker and validator observations remain unchanged.

### D3. Invariants

- Producer: `PWRunnerStepResult` has no `drift` or `deny_signal` property;
  `PWRunnerComparison` has no `conclusion`, `scope` or `drift`;
  `PWRunnerAttemptResult` has no `exit_code` or `syscall_errno`;
  `PWRunnerSandboxCheckResult` has no `scope`; `PWRunnerRunResult` has no
  `deny_signal_total`; `PWRunnerSignalResult` and `Signals.swift` are gone.
  The reply-shape golden (`tests/fixtures/contract/response_shape.json`)
  records the response 13 shape.
- Encoder, replacing the clause that rejected `disagreement`; the
  `query_first` eligibility check is unchanged:

  | Condition | Rejected when |
  | --- | --- |
  | `target_mutation.status: after_query` | `order` is not `query_first` |
  | `target_mutation.status: unordered` | `order` is `query_first` |
  | `target_mutation.status: none` | a run step qualifies under D1 |
  | `target_mutation.status` other than `none` | no run step qualifies under D1, the query's `filter_kind` is not `path`, or `limitations` carries a `query_plan:*` entry |
  | `target_mutation` | carries any key but `status`; producer and consumer both check this |
  | `sandbox_attribution.status`, `runtime_target_identity.status` | disagree with the D1 rules for this step |
  | any step | carries `drift`, `conclusion`, `deny_signal`, `comparison.scope`, `sandbox_check.scope`, `attempt.exit_code` or `attempt.syscall_errno`, or one of the five removed limitation strings |
  | `comparison_conditions` | absent or not exactly `{ "unestablishable": ["state_stability"] }` while `steps` is present on an ordinary reply; present on either `runner_reporting_failed` fallback |
- Reply degradation: `runner_reporting_failed` omits every `comparison` and
  `comparison_conditions`, even when `steps: []`. `evidence_retained: false`
  still withholds step and subprocess evidence. The reply carries no library
  identity at either fallback level, because the runner reports none (D6.52).
- Consumer (`tests/lib/consumer.py`): applies D5's envelope/response gates and
  reports a different version as `unsupported`; rejects the removed keys; rejects
  `established` as any obligation status; validates obligations against raw
  evidence; requires `references` to carry exactly the fixed keys and values.
  There is no sandbox-library identity rule for the reply or dossier (D6.52).
- Controller: `permission_failures_without_record` reads `comparison.observation`;
  `validate_disposition` also checks the lifecycle entries in
  `comparison.limitations`. Failed disposition validation withholds the
  projected disposition and termination cause. Preserve those lifecycle
  checks and the reporting-failure exception. These readers and every other
  semantic projection use the response-version gate (D6.46).

### D4. Assertions and recipes

Tests assert the evidence each scenario establishes, by field. The consumer
validates and selects and may compare raw fields to test descriptive
invariants. It returns no joint prediction/enforcement verdict. Guide
recipes select an explicit combination, such as deny predicted plus attempt
succeeded, and show its submitted-scope relations, order and obligations; they
assign no label. There is no `scope` field to show (D6.13).

### D5. Versioning

- Response schema 12 → 13: the comparison record, `comparison_conditions`, and
  the removal of `drift`, `conclusion`, `comparison.scope`, `deny_signal`,
  `deny_signal_total`, `attempt.exit_code`, `attempt.syscall_errno`,
  `sandbox_check.scope`, and the `normalized_outcome` and `attempt.outcome`
  spellings retired under D6.44.
- Controller envelope 4 → 5: `data.specimen`, the `data` key dispositions, and one `data`
  skeleton for every run envelope, which removes the pre-execution `data.error`
  constant; `runner_client` gains delivery/supervision facts and a nullable
  observed exit code, with controller transport failures per D6.56.
- Request schema, request-version admission behavior and worker ABI unchanged.
  The exact-version rule here governs semantic readers of runner responses
  and controller envelopes; it does not reject existing request-1 specimens.
  The worker ABI's existing equality tripwire remains independent (D6.31).
- `docs/contract.json` is edited, and `python3 docs/generate_contract.py` run,
  with the implementation that emits the shape; `PWRunnerRunResult` defaults
  `schema_version` to the manifest constant, so an earlier bump mislabels the
  old shape.
- [CONTRACT.md](docs/CONTRACT.md) (D6.21). "When a number moves" becomes:
  "Bump a number when the rules for reading change: a field removed, its type
  or meaning changed, or a new requirement placed on readers. An added field
  alone does not require a bump, since an absent field means unknown, never
  false. A bump may still be chosen for an additive change when the addition
  is a deliberate contract; the manifest's history says so. Because host and
  worker ship together, the worker ABI bumps on any change to the
  shared-memory layout or the handshake over it." The "Reading older replies"
  section, the historical version tables and "Naming numbers in prose" are removed.
  A "Supported versions" section replaces them: "Semantic readers of runner
  responses and controller envelopes accept exactly their manifest versions;
  another version is unsupported. Raw transport retains the received bytes
  without interpreting unsupported records. Stored evidence keeps its bytes;
  current semantic readers reject unsupported versions. Request admission and
  the worker ABI follow their own contracts." "What each number identifies" gains
  one sentence per contract. Response: "`steps[].comparison` records each
  channel's observation, the submitted-scope relations, the order PW
  established and the typed obligations, with `comparison_conditions` at run
  level; it carries no joint verdict and no signal channel." Envelope: "`data.specimen` is the dossier: request path, policy
  augmentation and imports, host facts, runner and app provenance, binary
  hash comparisons, run conditions and `references` to the records it does not own;
  the raw runner reply, transport, diagnostics and log capture stay beside it."

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
| Rust `run_flow.rs`, including `complete_execution`, `project_disposition` and log correlation | Gate received reply version before reading summaries, worker PID, lifecycle or comparisons. Remove the pre-response-10 disposition fallback. Unsupported replies remain intact in `data.runner_result`; when transport completes, the controller reports `result.ok: false`, exit 1, `result.normalized_outcome: unsupported_runner_response`, a version diagnostic and no runner-derived diagnostics or log capture. Malformed version fields use the corresponding `malformed_runner_response` result. A concurrent controller transport failure keeps D6.56's `tool_error` precedence without interpreting the unsupported/malformed reply. |
| Swift `pw-runner-client` and Rust `runner_client.rs` capture | Preserve received bytes/JSON as transport, including unsupported versions and unfamiliar strings. They do not reinterpret or coerce the version. Client-generated failure replies use the current response schema and D1/D3's empty-step and reporting-failure rules. |
| Requests, worker ABI, evidence manifest and validator transcript | Retain their existing separate admission/reading rules. This plan's equality rule is not a new request-version or nested-transcript-version restriction. |

For an unsupported/malformed reply, the dossier retains controller-collected
facts and fixed references, but `prediction_unavailable_pairs` is empty; no
runner-derived condition is computed. Rust transport tests preserve unknown
bytes while semantic tests require the unsupported result. Independently test
an old and a future response, an old and a future envelope, a current envelope
containing an unsupported reply, malformed version fields, and no reply. Use
current-version fixtures for unfamiliar-value transport tests.

### D6. Recorded decisions

| # | Decision | Resolution |
| --- | --- | --- |
| 1 | Obligations | Typed (`obligations` object). No flat-limitations fallback. |
| 2 | Bumps | Response 13 and envelope 5, each landing with its implementation. |
| 3 | `steps[].deny_signal` | Removed with `deny_signal_total`, `PWRunnerSignalResult` and `Signals.swift`. |
| 4 | Imports collection | Every run with an `sbpl_source`, with basis, status, limits and failure; budgets confirmed by measurement. |
| 5 | Library identity | Per function group, with `observer` and `basis`; unavailable components explained; not a worker-side observation. Superseded by 47. |
| 6 | Provenance | Moved under `data.specimen`; no aliases at former paths. |
| 7 | Joint labels | None on the wire, in test equipment or in recipes. |
| 8 | Supported versions | Exactly the manifest numbers; any other is `unsupported`; no version branches. The captured `a1_known_loss.json` stays as bytes to check that rejection. |
| 9 | `comparison_conditions` | In the runner reply; the dossier references it. |
| 10 | `data` boundary | The D2 table. `data.specimen` on every run envelope. |
| 11 | Identity observer | The XPC host, in `SandboxLib.load`, publishing `library_identity` in the reply. No ABI change. Superseded by 47. |
| 12 | Integration mechanics | Behavior-preserving preparation on `main`; the contract integration in a worktree branch with as many commits as it needs, verified with the default battery and `--all`, reaching `main` as one fast-forward. |
| 13 | `comparison.scope` | Removed; the guide states the scope once. |
| 14 | `sandbox_attribution` with no observation | `not_applicable`. |
| 15 | `policy.augmentation` | Always present. |
| 16 | Host facts | `sysctlbyname`, no subprocess. D6.52 leaves just the four sysctl facts and their basis; they do not stand in for sandbox-library identity. |
| 17 | Binary verification | Service, worker and validator hashed on every run against their manifest entries. `PW_VERIFY_EVIDENCE` untouched. Superseded by 49. |
| 18 | Imports scan placement | Before the runner is invoked, synchronously, on the applied source. |
| 19 | Reader surfaces | The envelope and the bare reply from `pw-runner-client`. |
| 20 | References | RFC 6901 pointers, fixed keys and values, no copies. |
| 21 | CONTRACT.md | Text in D5. |
| 22 | `attempt.exit_code`, `attempt.syscall_errno` | Removed; assigned from `rc` and `errno`. |
| 23 | `sandbox_check.scope` | Removed; constant `post_sandbox`. |
| 24 | REPAIR principle | Port scenarios and invariants, never assertions or code; delete on `main` first; the matrix fixture is the single source of comparison expectations. |
| 25 | Descriptive derivation (clarifies 7) | D0 permits computed descriptive fields, validation and selection across channels. Only joint prediction/enforcement verdicts are prohibited. |
| 26 | Mutation and conditions | D1's query-exclusion guard governs both encoder and consumer (see D6.42 for the retired ID list). Both reporting-failure levels omit `comparison_conditions`; ordinary empty-step replies carry it. |
| 27 | Library observation (refines 5 and 11) | Host-resolved functions only; explicit partial observations and issues. Presence follows collection stage, including post-load refusals; both reply fallbacks retain pre-materialized identity. Superseded by 47. |
| 28 | Dossier failures (refines 10 and 15) | Nullable format/hashes, augmentation status/error and the D2 failure table. Collection failures do not change execution admission or outcome. |
| 29 | Binary provenance (refines 17) | Hash selected paths, including overrides and BYOXPC copies, against built-in manifest baselines. Prefix baseline metadata with `manifest_`; unavailable/mismatched verification is descriptive. Narrowed by 49 to selections the manifest does not already describe. |
| 30 | Import observation (refines 4 and 18) | One serialized request for all readers; hash and lex the same bounded import bytes. Nonregular files are not read. `wall_ms` is a cooperative budget, not a hard filesystem timeout. |
| 31 | Reader scope (refines 8 and 21) | Exact versions at response/envelope semantic boundaries, including production Rust; raw transport remains lossless. Request admission is unchanged. D5 defines unsupported and malformed results. |
| 32 | Matrix evidence and size controls | 32 S/B/C expectations plus R/T with explicit owners; T retains its completed prediction/order. Unlinked exploratory claims are not acceptance evidence. |
| 33 | Integration order (supersedes 24's deletion order) | Only behavior-preserving preparation on `main`. Retire contract tests in the worktree; retire live scenarios only with passing replacement controls in the same increment. |
| 34 | Documentation and readiness | Use the corrected witness introduction, add the deny-log FAQ with delivery/attribution limits, and apply the readiness checklist below. Implementation receipts and measurements remain acceptance work. |
| 35 | Import inventories (refines 4 and 30) | The dossier object is the envelope's inventory of record; `data.policy_check` keeps `sbpl-check`'s flat block verbatim on the paths that run it, referenced by `references.policy_check`. Disagreement between them is expected, not an error. The I1 extraction keeps `sbpl-check`'s output byte-identical. |
| 36 | Dossier presence on non-execution run envelopes | One `data` skeleton for every `kind: "run"` envelope, printed by `cmd_run`, with the dossier at its collected state and the pre-execution `data.error` constant removed; `tool_error` and its exit 2 are unchanged. No envelope is exempted. Verified 2026-09-30: a missing argument, an absent request file and a non-JSON or non-object request all already print a run envelope, so the superseded claim that they kept a different kind was wrong. |
| 37 | Scanner budgets (refines 4) | Measured on the real closure: 2 records, ~13 KB, 0.02 s including compile. The published numbers still wait on I4's WebProcess-size and cutoff measurements. |
| 38 | Request snapshot lifetime (refines 30) | The unconditional snapshot lands with a cleanup guard covering every exit from `cmd_run`. Nothing resolves request fields relative to the request file, so relocation is safe. Superseded by 50. |
| 39 | Identity in the minimal backstop (refines 27) | The backstop validates the collected identity with `JSONSerialization.isValidJSONObject` and omits it on failure, recording the omission. Reporting failure never traps. Superseded by 47: the reply carries no identity, so the backstop keeps its literal shape. |
| 40 | Consumer caller inventory (refines 24) | The R4 table is the complete caller list for the five removed functions, including the inline Python inside three Rust tests. Each caller moves in the same increment as the removal. |
| 41 | Maximal reply size (refines 32) | Mutation lists roughly double `runner_reply_maximum` and carry `controller_output` with them; the numbers are accepted and recomputed from the synthesizer in I4. Bounding the list instead would be a D1 change. Superseded by 42. |
| 42 | `target_mutation` carries no step list (supersedes 41, refines 26) | The obligation is `{ "status": … }` alone. The status ships as a convenience projection — the query-exclusion rule applied once by the producer rather than by each reader — and because it replaces a field the wire carries today; its inputs are all exposed in the reply, so this is a reading rule and not knowledge a reader lacks, and whether it warrants producer-side derivation is S9's open question. The step IDs did not ship, because nothing read them: the producer emitted them, the encoder checked them and the consumer rederived them from the same attempt records a reader can read. Removing them leaves the reply bound and every documented limit unchanged, and retires the ordering, duplication and invention failure modes. The cost is that a step whose queried path another step removed reports its status without naming that step. |
| 43 | Unused Swift execution helpers (S1–S3) | Remove the attempt executor, query helper and sandbox-application helper, their exclusive dependencies and helper-only tests per R2/R5. Keep production planning, path diagnostics, policy hashing, structural policy refusal and C worker/validator behavior. Coordinate source, build, test and documentation changes in I3–I5 under D6.33. |
| 44 | Retired outcome spellings (S1, S3) | DECIDED. One vocabulary decision covering two spellings whose mechanisms do not survive. `bootstrap_port_failed` is produced only by the deleted Swift Mach-lookup branch; the C-worker path yields `lookup_failed` with a `task_get_special_port` diagnostic, so the information survives. `libsandbox_unavailable` is produced only by the host loader deleted under 47. Retire both, with the API constants, the `libsandbox_path` override key, the guide, `COVERAGE.md`'s outcome matrix, `source_drift`'s counts (19 → 18 normalized outcomes, 10 → 9 attempt outcomes, 8 → 7 override keys) and the live load-failure control moving together. Both ride response 13: a vocabulary retirement after this plan lands would need its own bump. Giving either spelling a real production producer instead would amend R2's unchanged-C boundary and is not proposed. |
| 45 | C-function-pointer stubbing guidance (S3) | DECIDED: retire it. Delete the "Stubbing C function pointers" paragraph from `runner/AGENTS.md` rather than rewriting it self-contained. Its subject does not survive: every `@convention(c)` declaration under `runner/Sources/` is in `SandboxLib.swift`, which 47 deletes, so after this plan the runner has no function-pointer slots to stub. Its worked example is deleted by 43, and no other example exists — the only other `@convention(c)` occurrence in the test tree is `main.swift`'s registry comment describing that same file. A technique for a construct the tree no longer contains is a retired claim, not guidance. Whoever introduces a new function-pointer use writes guidance that fits it; D6.53 checks sandbox API use specifically, not arbitrary C function pointers. |
| 46 | Controller comparison readers (inventory correction) | D3 names both the observation reader and `validate_disposition`'s lifecycle-limitation check. Their existing effects survive; S4's possible lifecycle-copy removal is not adopted. |
| 47 | Library identity is the shared cache UUID (supersedes 5, 11, 27, 39) | The controller cache UUID was selected in place of per-function host observations, while `SandboxLib.swift` and its admission check were removed. D6.52 supersedes the identity choice and its claim about worker/validator libraries; loader retirement remains in scope. Reply-side identity, load-stage presence rules and identity-specific fallback controls are removed. |
| 48 | Host invariance rule and its checks (refines 43) | Keep the service-header rule and existing live isolation cases, with source and shipped-binary checks and no new catalog case. D6.53 supersedes the blanket source-name ban and comment-marker exception; the `preflight` assertion that `nm -u` reports no undefined `_sandbox_*` symbol remains. `otool -L` alone cannot cover direct calls through libSystem or dynamic symbol resolution. |
| 49 | Binary hashing is not duplicated (supersedes 17, narrows 29) | The controller already reads the Evidence manifest every run, and `verify_manifest` already hashes every declared entry under `PW_VERIFY_EVIDENCE=1`. The dossier therefore hashes nothing the manifest describes: a built-in selection reports baseline metadata with `verification.status: not_compared`, and only an override or BYOXPC path — which no manifest entry describes — is hashed before invocation. Measured cost avoided: 2.93 MB read and hashed per ordinary run, 96% of it the `PWRunner` binary, with a constant answer for a given build. App-file integrity stays with `PW_VERIFY_EVIDENCE` and the signature. `basis` distinguishes the two record kinds. |
| 50 | The request is a string, not a file (supersedes 38, refines 30) | One serialization held in the controller feeds the scan and every reader. `pw-runner-client` gains `--request -` and receives the bytes on stdin, since it only read the path into memory to send it; a temporary file survives only on the `xpc_error` path that invokes `sbpl-check --request <path>`, written from the same string and removed before returning. The ordinary run creates no file, so the existing leak ends by deletion rather than by a cleanup guard. The client's `usage()` and documented surface gain the option; the `policy-witness` CLI contract is unchanged. |
| 51 | One OS-facts reader (refines 16 and 35) | The I1 extraction makes the shared reader the `sysctlbyname` one, so `sbpl-check` stops spawning `/usr/bin/sw_vers -buildVersion` for a fact `kern.osversion` returns (verified identical on the development host) while its output stays byte-identical. One mechanism, one fewer process spawn, and the dossier's no-subprocess rule holds for every consumer. |
| 52 | No sandbox-library identity (supersedes 47's identity choice) | Drop `host.sandbox_cache_uuid`, its dyld read, consumer shape rule and collection/failure controls. The API observes the caller's cache; native and x86_64 probes on the same stock host return different UUIDs, so a controller observation does not identify a selected worker's or validator's libraries. No identified planned reader needs the narrower controller fact. OS build and architecture remain environment context, not an inferred library identity. Loader retirement under 44/47 is unchanged. |
| 53 | Check native sandbox API use, not wire vocabulary (supersedes 48's source rule) | The source check rejects native API bindings/calls, dynamic sandbox-symbol lookup and libsandbox loading in executable contexts. Permit schema properties, coding keys, labels, diagnostics, comments and documentation that name `sandbox_check` or libsandbox. R2 defines the checked contexts, positive/negative controls and limits of this source convention. Keep the shipped-binary check and live isolation cases. No comment-marker exemption or prose assertion is needed. |
| 54 | Retire the remaining identity test instructions (implements 47/52) | I2's R owner covers reply degradation only. I3 has no partial-identity or pre-/post-load presence controls; I4 has no UUID collector control. D5's client-generated failure rule points to D1/D3 rather than the retired D2 identity-absence rule. Preserve reporting-failure, version, channel and remaining dossier controls. |
| 55 | Stdin handoff transport review (refines 50) | D6.50 left request-delivery timeout ownership, failure reporting and transport reuse unspecified. Resolved by 56 and the D2 contract, with I4/I5 implementation, acceptance and documentation owners. |
| 56 | One client deadline and independent failure evidence (resolves 55, refines 50) | One controller-owned absolute monotonic deadline covers client startup, request delivery/acquisition, XPC wait, output collection and exit; no delivery allowance or timer restart. Existing bounded cleanup follows expiry. Reuse the Rust supervisor's core with optional stdin and boundary-specific policies, plus existing JSON capture and fallback-unavailable handling. Delivery/supervision failure produces controller `tool_error` and exit 2 while retaining any complete reply and all diagnostics unchanged; it never synthesizes a worker/XPC failure. D2 defines the observations and precedence, I4 the controls and I5 the changed timeout/capture documentation. |

`kind: "run"` is not the only kind whose `data` shape varies within one kind:
`runner_status`, `runner_verify` and `runner_remove` emit `RunnerNotFoundData`
in place of their own record. That variance is outside this plan, which changes
only the run envelope, and it is recorded here so a later reader does not read
D6.36's resolution as covering it.

Reader inventory behind D6.8 and D6.31: the Swift decoder gates at 8, 9 and 10;
`consumer.py` branches at 7, 8, 9 and 12; the Python lifecycle tools branch at
the disposition version; production Rust `project_disposition` branches at 10;
`runner_client.rs` exercises 4 through 8 as transport. D5 assigns their new
boundaries and requires an audit of direct fragment-reader callers. No
out-of-tree reader is known. Stored evidence (`records/`, retained run output,
release acceptance artifacts) keeps its bytes and is not rewritten; rejecting
its version does not authorize altering or deleting it.

## REMOVAL

"Removed" means the wire keys, the code that computes them, the invariants
that police them, the tests that assert them, and every active surface that
names or promises them: CLI help, diagnostics, test messages, comments,
docstrings, identifiers, filenames, registries and documentation. R9 lists
what stays.

### R1. Wire keys

| Key | Where | Disposition |
| --- | --- | --- |
| `steps[].drift`, `steps[].comparison.conclusion`, `steps[].comparison.scope` | runner reply | removed |
| `limitations` strings `state_stability_unestablished`, `runtime_target_identity_unestablished`, `sandbox_attribution_unestablished`, `attempt_mutation_order_unestablished`, `query_attempt_order_unestablished` | runner reply | the first becomes `comparison_conditions`, the middle three become `obligations`, the last is dropped |
| `steps[].deny_signal`, `deny_signal_total` | runner reply | removed |
| `steps[].attempt.exit_code`, `steps[].attempt.syscall_errno`, `steps[].sandbox_check.scope` | runner reply | removed (D6.22, D6.23) |
| `data.policy_augmentation`, `data.runner_provenance`, `data.app_provenance`, `data.request_path` | controller envelope | relocated under `data.specimen` |
| `data.runner_service_bundle_id`, `data.runner_service_name`, `data.runner_registry_id`, `data.runner_service_executable` | controller envelope | removed |
| `data.error` on the pre-execution `tool_error` envelope | controller envelope | removed; a constant string, superseded by the uniform `data` skeleton and `result.error` |

### R2. Producer code

| File | Symbol or site | Disposition |
| --- | --- | --- |
| `runner/Sources/PWRunnerCore/PWRunnerAPI.swift` | `PWRunnerComparison.drift` (~906), `.conclusion`, `.scope` | delete; add `obligations` |
| same | `PWRunnerStepResult.drift`: init parameter, `CodingKeys.drift`, explicit-null `encode` branch, `decodeIfPresent` (~929–987) | delete, with no legacy-only property or version-gated read |
| same | `PWRunnerStepResult.deny_signal` (~921–982), `PWRunnerRunResult.deny_signal_total` (~1720–1873), `PWRunnerSignalResult` (~857) | delete |
| same | `PWRunnerAttemptResult.exit_code`, `.syscall_errno` (~704–803); `PWRunnerSandboxCheckResult.scope`, `PWRunnerWire.sandboxCheckScopePost` (~41) | delete |
| same | encoder clauses `steps.allSatisfy({ $0.comparison == nil && $0.drift == nil })` (~1817) and `comparison.conclusion != "disagreement", step.drift != true` (~1847) | rewrite per D3 |
| same | `PWRunnerRunResult` decoder/encoder version gates and legacy-only field fallbacks | exact response gate and current invariants per D5 |
| same | `AttemptOutcome.bootstrapPortFailed` and the `libsandbox_path` row of the `_test_overrides` table (~213) | delete with the outcomes retired under D6.44 |
| same | doc comments ~133, ~157, ~726 | reword |
| `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift` | `ComparisonEvidence.conclusion` (~837); `renderLimitations()` (~843); `drift: comparison.drift` (~632); `deny_signal: nil`, `deny_signal_total: nil` (~162, ~631); comments ~24–26, ~722, ~763, ~890 | delete or reword; `renderLimitations` becomes `renderObligations` plus the descriptive list |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift` | reply degradation; the `SandboxLib.load` call site and its `libsandbox_unavailable` return | remove drift clearing and withhold comparisons/conditions through both fallback levels; delete the load call site and its refusal under D6.44 |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift` | unused execution helpers and exclusive bindings/constants; retained exclusion-set comments | remove helpers per S1/S2 below, rather than porting their `scope:` arguments; reword retained comments |
| `runner/Sources/PWRunnerCore/PathUtils.swift` | `observedPathForFd`, its `fcntl_getpath` binding, `warmFirmlinkMap` | remove; keep production path helpers and lazy firmlink map |
| `runner/Sources/PWRunnerCore/SandboxApply.swift` | `applySandboxPolicy`, `ApplyError` | remove; keep policy hashing in this file |
| `runner/Sources/PWRunnerCore/Signals.swift` | whole file; no caller under `runner/Sources` | delete, and its `XPC_RUNNER_SIGNALS_FILE` line in `build.sh` |
| `runner/Sources/PWRunnerCore/SandboxLib.swift` | whole file | delete with its seven symbol resolutions, the `libsandbox_path` override and the `libsandbox_unavailable` outcome, under D6.44 and D6.47 |

Production C worker and validator behavior is unchanged. S2 removes the unused
C query shim and its build wiring; it does not remove the production validator.
D6.44 retires the unused Mach-lookup spelling without changing the C producer.
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
  they serve query planning and host path diagnostics. No existing test calls
  `runAttempt`. D6.44 settles the outcome vocabulary; the guide
  and coverage table currently attribute `bootstrap_port_failed` to a C
  producer that does not emit it.
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
  `runner/AGENTS.md` paragraph that links it (D6.45). With `applySandboxPolicy` gone, nothing calls
  any of the loader's seven resolved functions, so `SandboxLib.swift` goes too,
  along with the `libsandbox_path` test override and the
  `libsandbox_unavailable` outcome, under D6.44 and D6.47. The hashing kept above
  is not a loader function, so `SandboxApply.swift` retains only hashing, and
  R10's search will flag a filename that no longer describes its contents.

Remove imports and comments made obsolete by these deletions. Keep the existing
filenames for files that retain production code. R5 assigns the precise test
deletions; R8 assigns the documentation changes. The helper removals themselves
introduce no new request, response or worker ABI contract.

#### The host invariance rule and its checks

The service header currently states what must not be in that file as a list of
four things S1–S3 delete — `applySandboxPolicy`, libsandbox state surviving the
load check, `runSandboxCheck`, `runAttempt` — followed by the rule they
illustrate: the host stays invariant under the policy under test so the XPC
reply path is never disrupted by a `(deny default)` specimen. The symbols are
examples; the rule is one of AGENTS.md's core ideas. **Rewrite that passage to
state the rule without naming deleted symbols; do not delete it.** After these
removals the rule is also stronger and simpler, because the host no longer
links, loads or calls libsandbox at all.

Keep the explanation in the service header, with links to the live
`runner_apply_isolation_v3/deny_default_v3_worker_reply` host/worker case and
the separate `runner_c_worker_harness/bare_deny_default` worker control. The
latter invokes the C worker directly and does not establish XPC-host behavior.
No comment text or delimiter is part of the source-check contract.

Two checks protect the rule, and they are not redundant. Measured on the
2026-10-01 build: `nm -u` on the shipped `PWRunner` executable reports
`_sandbox_check` — the shim call S2 deletes — and does not report
`_sandbox_apply`, because the loader resolves that by string through `dlsym`.
`otool -L` reports no sandbox dependency at all, in the present state, because
`sandbox_check` arrives through libSystem and the loader's symbols arrive at
runtime. So a direct call is visible to the binary check and not to a link
check, a `dlopen` by string literal is visible only in source, and no single
instrument covers both.

- **Source (`source_drift`, in its existing runner-source case).** Check native
  API use under `runner/Sources/`, with an explicit sandbox SPI name set:
  `sandbox_check`, `sandbox_apply`, `sandbox_compile_string`,
  `sandbox_create_params`, `sandbox_set_param`, `sandbox_free_params`,
  `sandbox_free_profile`, `sandbox_free_error`. Reject declarations/bindings
  to those native symbols (including Swift `@_silgen_name` bindings), direct
  calls, literal symbol lookups through `dlsym`, and literal libsandbox paths
  passed to `dlopen`. Include simple named constants supplying those lookup
  arguments, as in the loader being removed. This is a check of executable
  contexts, not token presence: `sandbox_check` remains a required request and
  response property, coding key and diagnostic label. Those uses, comments,
  SBPL text and explanatory strings are allowed. Do not ban unrelated `dlopen`
  calls or arbitrary `@convention(c)` declarations.
  Source controls must accept the retained schema/planner code and explanatory
  text, and reject reintroduced bindings, calls and dynamic lookup/load forms,
  including constants feeding them. Handle comments and string literals by
  context so examples cannot count as executable calls or hide actual lookup
  arguments. This is a mechanical source convention, not complete Swift/C
  analysis or proof against computed library/symbol names. Its limits are
  documented alongside the binary and live controls. The worker and validator
  C sources are outside this host-source scope and retain their native calls.
  The failure message identifies the prohibited native use and the host
  invariance rule; changing that rule requires an explicit design review.
- **Binary (`preflight`, in its existing artifact case).** `nm -u` on
  `PWRunner.xpc`'s executable reports no undefined `_sandbox_*` symbol. This
  catches a reintroduction arriving through a dependency or a new target, which
  a grep over `runner/Sources/` would not see. Land it in the same commit as the
  removal, so its failing state on the present build and its passing state after
  are both on the record. Do not use `otool -L`: it passes in the state the rule
  forbids, and a later reader who believes it covers this will stop looking.

Neither check adds a catalog case: both are assertions inside cases that already
run. No new live case is needed — `bare_deny_default`,
`proceed_under_bare_deny_default`, `max_slots_deny_default`,
`deny_default_v2_worker_reply`, `deny_default_v3_worker_reply` and
`witness_contract/shm_sentinel_under_deny_default` already exercise the
guarantee at their respective boundaries. Nothing asserts the text of the
comment; that would pin prose rather than behavior (D6.48/53).

### R3. Controller implementation and fixtures

Production Rust reads no removed comparison key. It does interpret legacy
lifecycle replies: remove `project_disposition`'s pre-response-10 branch and
gate semantic work in `complete_execution` and its downstream diagnostics/log
paths per D5. Three Rust tests also embed inline Python that imports the
consumer functions I3 removes — `run_flow.rs` ~2321 and ~2523 and
`log_replay_tests.rs` ~172 import `recover_evidence` and
`validate_evidence_shape` — so they move to `validate`/`denials` in the same
increment or `cargo test` breaks (D6.40).

Implement the dossier per D2: the held request string with `--request -` on the
client and a fallback-only temporary file (D6.50), binary records that hash only
non-manifest selections (D6.49), and the shared sysctl OS reader (D6.51). Move
client invocation to shared supervision with optional stdin, one deadline and
independent failure evidence per D2/D6.56. Keep log policies at their existing
boundary and extend fallback-unavailable handling to temporary-file failures.
Move the pre-execution failure envelopes into `cmd_run` so one writer owns the
run `data` skeleton; `cli.rs`'s catch-all keeps only errors that escape it.
Update tests for unsupported/malformed replies and current-version fragment
transport.

`runner_commands.rs::cmd_runner_verify` is the helper's other production caller.
Keep its file-input call supported, its 5-second default and its existing data
shape; adapt it to the shared deadline and check transport failure before using
the reply to report verification success. Apply D5's version gate before its
reply projections too. Its transport failure uses controller `tool_error` and
exit 2. The run envelope's new capture fields do not require a verification
dossier or a redesign of management-command data.

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

Every caller of the five functions I3 removes, found by exact search on
2026-09-30. Each moves to the named replacement in the same increment; the
removal is not complete while any of these still imports the old name.

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

Counts on df333b4: about 245 `drift`/`conclusion` references across 30 test
files and 120 across 10 Swift test files; the five removed limitation strings at
109 sites; `limitations` read at 125 sites; `deny_signal` at 28 suite sites, 8
Swift sites and 1 controller site; 14 catalog entries.

| Suite | Files (references) | Disposition |
| --- | --- | --- |
| `runner_unit` | `DriftClassifierTests.swift` (53) | replaced by `ComparisonEvidenceTests.swift` (REPAIR I2) |
| `runner_unit` | `EnvelopeInvariantTests.swift` (30) | version 4–7 round-trips deleted; current-shape cases updated |
| `runner_unit` | `PredictionUnavailableTests.swift` | delete only the `predictionUnavailable` group calling `runSandboxCheck` and its exclusive assertion helper; keep `predictionUnavailableQueryPlanning`, its literal expectations and `runPredictionUnavailableTests` registration; rewrite the file and registry descriptions |
| `runner_unit` | `SandboxApplyTests.swift`, `main.swift` | delete the helper-only file, `runSandboxApplyTests` registration and its comment; the `runner/AGENTS.md` paragraph linking it is deleted too (D6.45) |
| `runner_unit` | `OrderingTests.swift` (10), `ReplyFailureTests.swift` (12 plus the field-complete fixture), `ReplyMaximumTests.swift` (2), `WorkerEvidenceTests.swift` (1), comments in `AttemptOutcomeMappingTests.swift`, `CWorkerTests.swift`, `main.swift` | updated; the golden regenerates from `ReplyFailureTests` |
| `unit/rust.unit` | R3 fixtures | updated |
| `blackbox_e2e` | `checker_controls.py` (21) | rebuilt (REPAIR I3) |
| `blackbox_menagerie` | `checker_controls.py` (13), `validate_run.py` (1), `cases/core.json` (23 steps carry `expect.drift`) | `expect.drift` deleted |
| `failure_boundaries` (4), `run_effects` (2), `runner_exec_inheritance` (1), `runner_exec_lifecycle` (4), `runner_filter_sysctl_name` (6), `runner_outcome_runner_timeout` (2), `runner_outcome_validator_no_reply` (2), `runner_specimen_isolation` (1), `runner_validator_failure` (4) | check scripts | field assertions |
| `runner_exec_dac` | `check.py` (7), `check_query_scope.py` (6), `run.sh` (2) | field assertions; case id becomes `execute_permission_controls_spawn` |
| `runner_outcome_libsandbox_unavailable` | whole suite: `run.sh`, `README.md`, catalog entry | deleted with the loader under D6.44/D6.47. Its only subject is a `normalized_outcome` that ceases to exist, so nothing replaces it and no coverage moves; a successor control belongs to S14 if that distinction is ever rebuilt from the worker's dyld diagnostic |
| `runner_use_c_worker` | `run.sh` (63) | retire `drift_null_for_dac_eacces` and `drift_null_for_non_policy_failure` with passing S03, S17, S14 replacement controls in I2/I4; other assertions become field assertions |
| `witness_contract` | `check_ordering.py` (10), `check_prediction_targets.py` (6), `check_create_existing.py` (3), `check_diagnostic_transport.py` (3), `check_pre_apply_failure.py` (3), `check_removed_target.py` (2), `check_attempt_in_flight.py`, `check_termination_correlation.py`, `check_worker_evidence.py`, `check_worker_sparse.py` (1 each) | field assertions |
| `witness_contract` | `check_comparison.py` (11), `drift_determination_via_validator_seam.sh` (12), `run.sh` (6) | absorbed by `comparison_matrix` (REPAIR I2); retire the seam case with passing replacement controls |

### R6. Goldens and fixtures

| Fixture | Contains | Disposition |
| --- | --- | --- |
| `tests/fixtures/contract/response_shape.json` | `drift`, `conclusion`, `limitations`, `deny_signal`, `deny_signal_total` | regenerate from `ReplyFailureTests`; the reviewed diff is the acknowledgement |
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
- S1–S3 remove one catalog case, `runner_outcome_libsandbox_unavailable`, with
  its suite directory; the helper removals themselves remove none. The internal
  `runner_unit` registration and descriptions change per R5; its production
  planner and driver groups stay.
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
- D6.50: document `--request -` in `pw-runner-client`'s `usage()` and wherever
  the client's surface is described, and remove any account of a per-run
  temporary request file.
- S1–S3: revise the source inventory in `runner/README.md`, the `runner_unit`
  row in `tests/README.md`, `tests/suites/runner_unit/README.md`, and the unused
  apply-helper descriptions in `tests/COVERAGE.md` and
  `tests/FAILURE-PROPAGATION-CONTRACT.md`. The latter's statement that helper
  cleanup is outside the effort is superseded by D6.43. Delete the "Stubbing C
  function pointers" paragraph from `runner/AGENTS.md`, whose subject, technique
  and example all leave with `SandboxLib.swift` (D6.45). Update
  `tests/suites/source_drift/README.md`'s target list and claim that both Swift
  query callers use the exclusion set, and record the native sandbox API check
  there and in `tests/suites/preflight/README.md` with what each check sees and
  does not see. Reconcile the Mach-lookup outcome and the retired
  `libsandbox_unavailable` in `docs/PolicyWitness.md`, `tests/COVERAGE.md` and
  the `_test_overrides` table in
  [PWRunnerAPI.swift](runner/Sources/PWRunnerCore/PWRunnerAPI.swift) under
  D6.44.

### R9. Not removed

- `source_drift`, `runner_abi_layout` and every use of "drift" meaning
  docs-versus-code or layout divergence: comments in
  `CWorkerOrchestrator.swift` ~712, `AttemptOutcomeMappingTests.swift` ~96,
  `controller/src/runner_manager.rs` ~1080, `sb_api_validator.c` ~605,
  `CWorker.swift` ~47, `tests/lib/artifact.py` ~38,
  `tests/suites/dispatcher/check_selection.py` ~126.
- The `prediction_unavailable` set in `ProbeRunner.swift`, its `source_drift`
  check against the guide, and `harness/VERIFICATIONS.md`; only its
  description changes.
- S1–S3's retained production helpers listed in R2, including policy hashing
  and structural policy refusal; the planner unit controls, C worker harness,
  real worker/validator drivers and the live failure controls other than
  `runner_outcome_libsandbox_unavailable`, which goes with the outcome it
  exercises (D6.44). No removed Swift-helper test is credited as coverage of
  those production paths.
- `comparison.order`, `runner_subprocess.ordering`, `eligibleOrderedStep`, the
  release barrier and the opt-in `order_barrier_mutations` control;
  `legacy_worker_abi6` in `OrderingTests` (the ABI tripwire).
- `comparison.observation` and `permission_failures_without_record`.
- `records/`, `dist/evidence`, `dist/archive`.

### R10. Semantic completion criterion

Before and after implementation, search the vocabulary `drift`, `conclusion`,
`agreement`, `disagreement`, `consistent`, `directional_consistency`,
`verdict`, `prediction`, `enforcement`, `mismatch`, the signal-channel names,
the removed limitation strings and the former provenance paths, across CLI
help, diagnostics, test names and descriptions, identifiers, comments,
docstrings, fixtures, registries and documentation; follow aliases, callers
and generated copies; read affected passages for claims that survive without
any search term. Record every remaining match by its meaning: a current
descriptive value, an unrelated use, immutable evidence, an explicit
removed-key rejection. Completion is the explained residue, not a zero count.

Also search the S1–S3 function/type names, `PWSandboxCheckShim`,
`XPC_RUNNER_SANDBOX_SHIM`, `SandboxApplyTests`, `runSandboxApplyTests`,
`bootstrap_port_failed`, `SandboxLib`, `libsandbox_path`,
`libsandbox_unavailable`, `library_identity`, `sandbox_cache_uuid` and
`@convention(c)`. Also search
`write_temp_request`, `sw_vers` and `macos_build_version`, whose call sites
change under D6.50 and D6.51. R2's standing source check applies the narrower
native-use rule; it does not forbid retained wire vocabulary or explanatory
text. Follow build variables, target dependencies, test
registrations and contributor links as well as code callers. Search records
and this plan may name removed artifacts; active implementation and contributor
instructions must match the selected scope and the recorded resolutions.

## REPAIR

Port scenarios and invariants, never assertions or code. Every test artifact
the removal touches is classified once:

| Class | What it is | Disposition |
| --- | --- | --- |
| Scenario | A case with an independent control: a real file, a direct OS call, a steered verdict, a captured host fact | Keep. Expectations come from the D1 matrix or the case's own control. |
| Old-contract control | A control proving the checker rejects a loss expressible only in the removed contract | Delete. Re-express only when the invariant survives in D2, D3 or D5, in the current contract's wording. |
| Unused-helper control | A test whose only execution target is a removed S1–S3 helper | Delete with that helper. Retain tests of the production planner and C paths; do not port assertions to another unused implementation. |
| Legacy branch | Code, a fixture, a round-trip or prose whose purpose is reading a version no reader accepts | Delete. |
| Equipment | A shared library or helper | Rewrite from the contract: no legacy-version branches, no joint verdicts, no compatibility fallbacks. |

Keeping anything requires naming the matrix row, independent scenario control,
or D2/D3/D5 invariant it serves.

### I1. Behavior-preserving preparation on `main`

Capture the infrastructure-ledger rationale before retiring anything. Factor
`resolve_imports`, `compute_closure_hash` and the OS-facts read out of
`sbpl-check.rs` into shared Rust modules without changing output. The OS-facts
extraction also drops a subprocess: `sbpl-check`'s `macos_build_version()`
spawns `/usr/bin/sw_vers -buildVersion` for a fact `sysctlbyname("kern.osversion")`
returns, which D6.16 requires the dossier to read without a subprocess.
Verified on the development host: both return `23J220`. The shared reader is
the sysctl one and both consumers use it, so `sbpl-check`'s output stays
byte-identical while one process spawn leaves the tree; keep its
once-per-process caching (D6.51). Budgeting, single-read traversal and the
remaining dossier collection belong to I4, not this extraction. Write the unregistered matrix fixture (I2); add an exec and a sysctl
specimen under `tests/fixtures/pw_runner/`; verify the response 12 default
battery, then create the worktree (D6.12, D6.33).

No scenario or active contract check is deleted in I1. I2 through I5 are
coordinated worktree increments, not a requirement to land a broken consumer
before its producer. Register and run replacements before retiring their
predecessors in the same increment, with associated registry and documentation
updates. The default battery being green after a deletion alone is not
evidence of preserved coverage.

### I2. The matrix fixture

`tests/fixtures/comparison/matrix.json` holds the 32 S/B/C rows and T: for each,
the specimen inputs (policy, query, attempt, steered verdict if any, independent
control), raw inputs needed by the unit reader (channel results, ordering and
all run attempts with IDs), and the expected response 13 `comparison` object.
R is a reply-boundary control, recorded in the ownership table rather than as
a comparison object. Expectations are reviewed from D1 and independent
controls; they are not generated from the producer under test. The response 12
columns already carry per-row provenance from the verification receipts under
[tests/fixtures/comparison/baseline_response12/](tests/fixtures/comparison/baseline_response12/);
the fixture records the same values with the obligations added. Specimen B
follows the validator I/O deadline seam and the non-idempotent setup rule in
Specimen mechanics above. Two reader
families:

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
| R: reply degradation | `runner_unit` / `ReplyFailureTests` | internal encoder faults at both fallback levels; retain the specified evidence and withhold comparisons/conditions; no library-identity control |
| `target_mutation` status and exclusion | `ComparisonEvidenceTests`, encoder invariants and checker controls | excluded-query create/unlink, a qualifying removal in another step, unrelated/failed/synthetic unlinks, and an injected `steps` key |

The T setup already has a retained
[live reply](tests/out/runs/release-0.2.4-default/suites/witness_contract/worker_attempt_in_flight_at_deadline/artifacts/a1/run.json)
and [specimen](tests/out/runs/release-0.2.4-default/suites/witness_contract/worker_attempt_in_flight_at_deadline/artifacts/a1/specimen.json)
under the `release-0.2.4-default` entry in [RETAINED.json](tests/RETAINED.json).
They establish the existing scenario, not conformance to the proposed shape.
Link new acceptance receipts from the completed matrix README; preserve old
receipts as bytes.

Retire `runner_use_c_worker/drift_null_for_dac_eacces` only with passing S03/S17
controls, `drift_null_for_non_policy_failure` with S14, and
`witness_contract/drift_determination_via_validator_seam` with B1–B7 and its
independent controls. Their catalog entries and documentation move in that
same verified increment.

### I3. Equipment

- `tests/lib/consumer.py` exposes `validate(document)`, `steps(document)`,
  `select(steps, **fields)`, `lifecycle(document)` and `denials(document)`.
  `document` is an envelope or a bare runner reply. A version other than the
  manifest's yields one `unsupported` error under D5; malformed versions and
  no-reply envelopes follow D5's separate rules. `validate` merges
  `validate_evidence_shape`, `validate_current_build_evidence` and
  `validate_ordering` and checks obligations against raw evidence:
  `target_mutation` from D1's eligible query and qualifying rule,
  `sandbox_attribution` from `observation` and
  `exec_result_failed_after_spawn`, `runtime_target_identity` from the filter
  kinds, `references` against the fixed set. `recover_evidence`,
  `comparison_groups`, `failure_groups`, `path_reporting` and
  `step_reporting` are gone.
- `tests/lib/blackbox.py`: `validate_step` loses the drift checks and the
  alias-agreement rule; `expected.comparison` may carry `obligations`;
  `validate_run_shape` calls `validate`.
- `tests/lib/unavailable_prediction.py`, `path_diagnostics_contract.py`: field
  selections.
- `blackbox_e2e/checker_controls.py` rebuilt against `missing_path_run.json`
  regenerated at 13 and 5 from a live run. Surviving controls: injected
  removed keys; obligation contradictions per D3; missing or wrong
  `references`; missing `comparison_conditions` where required; path provenance; the ordering chain; reporting-failure
  withholding at both fallback levels; every version-boundary control in D5;
  one control feeding `pw-runner-client`
  output to `validate`. The mutation-order controls are re-expressed against
  `target_mutation`, including the exclusion and another-step cases in I2.
  Reporting-failure controls cover evidence retention and comparison/condition
  withholding at both fallback levels. No identity or load-stage control is
  carried forward (D6.54).
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

### I4. Producer and dossier, in the worktree

- Remove the S1–S3 implementations and exclusive shim/build dependencies per
  R2, coordinated with I3. Preserve the named production helpers. In the same
  commit, rewrite the service header's invariance explanation and add its two checks
  per R2: the `source_drift` native-use assertion and its positive/negative
  controls, and the `preflight` `nm -u`
  assertion, whose failing state on the pre-removal build is recorded with the
  change (D6.48/53). The `runner/AGENTS.md` stubbing paragraph is deleted in the
  same increment as its subject (D6.45); no decision here is an instruction to
  change C behavior.
- Swift per R2, D6.22 and D6.23, plus `comparison_conditions`. The comparison producer already receives the run
  attempts and already tests for a qualifying removal, so the obligation needs
  no new plumbing. The field-complete fixture in `ReplyFailureTests`
  gains the new records; the string classification in `ReplyMaximumTests`
  gains every new string key. The obligations add three short status strings per
  step and no repeated container, so `runner_reply_maximum` and the derived
  `controller_output` keep their documented values; confirm that from the
  synthesizer rather than assuming it (D6.42). The shape golden regenerates.
- Controller per D2 with Rust tests for shape, statuses, budgets, the fixed
  reference set, relocated paths, request snapshot and D5 version gates.
  Scan controls include nonregular files, changing originals, a single read
  used for both hash and recursion, nonliteral imports, decoding/read errors,
  each cutoff and cooperative deadline behavior; `docs/limits.json` gains the
  scan budgets after measurement on the largest system profile and a
  WebProcess-size specimen.
- `docs/contract.json` to 13 and 5 with these changes, then
  `python3 docs/generate_contract.py`.
- `witness_contract/dossier_witness`, new: the dossier against the specimen
  that ran and host facts the test captures independently (`sw_vers`,
  `uname`, the manifest, hashes of the selected executables). It owns live
  examples for no augments, applied augments, refused augments, malformed or
  missing policy/source, and XPC failure, plus executable overrides and
  BYOXPC selection. Use the existing BYOXPC ownership/cleanup machinery.
  Controlled Rust collectors own missing/malformed manifest, unreadable
  override file, hash mismatch on a non-manifest selection, and host-read
  failures so signed app bytes stay unchanged. One control asserts that an
  ordinary built-in run hashes no app binary and reports `not_compared`, and one
  asserts that an ordinary run leaves no file in the temp request directory.
  The dossier case includes or links those control receipts and checks every
  failure-table shape. Host-read controls cover the four sysctl facts. There
  is no shared-cache UUID collector or sandbox-library identity control
  (D6.52/54).
- Implement D2/D6.56 in the shared Rust supervision core, `runner_client.rs`,
  `run_flow.rs` and the Swift client. Keep the extraction and behavior changes
  in I4's integration increment; I1 remains behavior-preserving preparation.
  Rust subprocess controls in `runner_client.rs` own slow/partial delivery,
  simultaneous input/stdout/stderr beyond pipe capacity, early stdin closure
  with retained JSON/stderr, a non-reading child, output cutoff, signaled exit
  and failed/unconfirmed cleanup. Assert that delivery consumes the reply
  allowance and that write failure cannot restart it; check byte counts, EOF,
  truncation and concurrent faults against the independently controlled child.
  Include nonzero exit with a valid failure reply and an `ok` reply alongside
  failed delivery. `run_flow.rs` controls own `tool_error` precedence, unchanged
  reply retention, D5 gating and fallback file create/write/cleanup failures
  preserving the original `xpc_error`. Re-run the existing log-supervision
  controls to prove extraction preserves that channel's policies. The live
  `dossier_witness` case exercises the shipped client's stdin/EOF path, verifies
  the submitted request bytes and ordinary capture, and links these failure
  controls. Keep direct client file-input coverage for its existing interface;
  `runner_commands.rs` controls cover verification's preserved default and
  refusal to report success after transport failure or an unsupported reply.

### I5. Contract and registry documents

- `tests/FAILURE-PROPAGATION-CONTRACT.md`: the chapter "Derived comparisons
  and evidence joins" is replaced by the comparison record (D1), the
  invariants (D3), the scenario matrix, an ownership table naming which case
  owns which rows and invariants, and supported versions. The join table stays
  with its "Supported public conclusion" column renamed "What the record
  states". C1 through C6, the accepted-answers table, "Public representation
  and meaning", "Permanent consumer enforcement" and "Compatibility and
  acceptance gate" go.
- `docs/CONTRACT.md` per D5. `ContractVersionTests.swift`'s header comment
  ("Added keys need no bump") changes with it.
- `controller/README.md`, the runner-client usage/documentation,
  `tests/FAILURE-PROPAGATION-CONTRACT.md` and the guide explain the shared
  client deadline, controller `tool_error` precedence and independent retained
  reply. Revise `docs/limits.json`'s `client_rpc_wait` entry and the Limits
  interaction prose for the new start/end boundaries and fixed cleanup grace;
  update `controller_output` to describe bounded streaming retention, actual
  bytes read and incomplete-stdout rejection. The `sbpl-check` receiver's
  existing collection policy is unchanged. Regenerate the documented limit
  tables and guide copies with `docs/generate_limits.py`; no reply-wait-only or
  whole-stream-buffering claim may remain for the runner-client boundary.
  The `runner verify` timeout description adopts the shared deadline while
  retaining its own default.
- `tests/catalog.json`: `comparison_matrix` and `dossier_witness` added;
  `execute_permission_is_not_sandbox_drift` becomes
  `execute_permission_controls_spawn`.
- `tests/README.md`: the "Comparison evidence coverage" section becomes one
  paragraph pointing at the matrix fixture and its live and Swift readers; affected suite
  rows rewritten. `tests/COVERAGE.md` rows likewise. Suite and fixture READMEs
  follow DOCUMENTATION's infrastructure ledger.
- `runner/README.md`, `runner/AGENTS.md`, `runner/augments/README.md`,
  `controller/README.md` (including its consumer-audit table) and the
  AGENTS.md core idea per R8.
- Complete S1–S3's R8 entries, including the retained hashing/planning roles,
  the surviving shim inventory, and the D6.44–45 outcomes. Check that no active
  instructions link to the deleted test or assign production coverage to it.

### Kept scenarios

| Case | Independent control | Expectation source |
| --- | --- | --- |
| `runner_exec_dac/execute_permission_controls_spawn` | direct `posix_spawn` before and after `chmod` | S15, S17; the deny-query run expects prediction `deny`, `permission_failure`, attribution `unestablished` |
| `witness_contract/queries_precede_attempts`, `queries_use_a_pre_attempt_interval`, `query_interval_is_not_a_snapshot`, `external_mutation_between_query_and_attempt` | file bytes, native receipts, timing | S19, S25, the B rows; `order` and `target_mutation` |
| `witness_contract/prediction_target_is_independent_of_attempt_target` | file bytes | S01, S02, S05 |
| `witness_contract/create_existing_file_preserves_contents`, `run_effects/*` | file bytes and modes | S08, S24 |
| `witness_contract/pre_apply_failure_reports_no_policy_verdict`, `worker_sparse_failure`, `worker_progress_and_failure` | worker evidence | C1, T |
| `runner_validator_failure/*`, `runner_outcome_validator_no_reply` | transcripts, signals | B2, B4 |
| `runner_outcome_runner_timeout`, `witness_contract/worker_post_apply_hang_seam`, `worker_attempt_in_flight_at_deadline` | deadlines, file effects | S01 plus the lifecycle rows |
| `runner_specimen_isolation`, `runner_exec_lifecycle`, `runner_exec_inheritance` | process observations | S15, S16 |
| `failure_boundaries/*` | admission and receiver faults | shape only |
| `blackbox_e2e/BBX-001`, `BBX-002`, the menagerie cases | policy knowledge, file effects | `predict`, `attempt_ok`, `errno` |
| `runner_filter_*` | planning exclusion | S10 |

### Verification

- Default battery after I1 on `main` and after each worktree increment;
  `tests/run.sh --all` before the fast-forward, retained as the acceptance
  record, with replacement owners and dossier controls all accounted for.
  `order_barrier_mutations` runs on the integrated candidate before fast-forward.
- Before I1, capture the existing three specimens under
  `tests/fixtures/pw_runner/`. After behavior-preserving preparation and the two
  added specimens, capture all five as the response 12 baseline. On the verified
  integration candidate, diff all five against that baseline with intended
  contract changes and run-varying values explicitly accounted for. Preserve
  the inputs, app inventory and raw envelopes with the acceptance record.
- R10 over the test tree and equipment.
- An ordinary built-in run writes no file into the temp request directory and
  hashes no app binary: both are checked as controls in I4, and both are
  measurable on the integration candidate rather than argued.
- D6.56's shared-deadline, duplex capture, failure-preservation and bounded
  cleanup controls pass, including the existing log-supervision controls.
  The live stdin/EOF receipt and direct file-input coverage accompany them;
  client cleanup is never credited as XPC host or worker termination evidence.
- For S1–S3, verify both the shipped `build.sh` build and the test-only SwiftPM
  build through `runner_unit`; run `source_drift` including planner controls and
  the native-use assertion and its positive/negative controls, `preflight` including the `nm -u`
  assertion, and `runner_c_worker_harness` including its deny-default cases. The
  integrated baseline diff must show no helper-removal change to queries,
  attempts or hashing beyond separately approved contract changes. The
  disappearance of `libsandbox_unavailable` is such an approved change, so the
  baseline diff accounts for it rather than treating it as a regression. Retain
  the existing live worker and validator failure controls in the default/`--all`
  battery; `runner_outcome_libsandbox_unavailable` is deleted with its outcome
  and is not expected to run.
- The response 12 matrix verification is already recorded under
  `tests/fixtures/comparison/baseline_response12/`. Rerunning it on the
  integration candidate is the response 13 acceptance capture, and the two
  specimens there are reused for it.
- The finished consumer exposes no joint prediction/enforcement verdict.
  Descriptive validation and selection may use both channels. All D5 semantic
  readers gate versions by equality and contain no legacy interpretation branch;
  raw transport remains covered independently.
- Sub-agents cannot run the built app; live verification runs from the main
  session.

## DOCUMENTATION

The opening statement and FAQ defaults below are settled for implementation;
the ledgers and cold-reading method govern the prose review of `README.md` and
`docs/PolicyWitness.md`; R8 and the infrastructure ledger cover contributor
documents. The guide entrains `docs/QUESTIONS.md` (between the `SHARED
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
| README Flow | the **Drift** bullet | remove | a **Comparison** bullet: submitted-scope relations, order, obligations |
| README Flow | "Eligible `query_first` records establish this ordering; they do not establish a shared state snapshot" | keep | |
| FAQ | "When should I use PolicyWitness?" | revise | to witness a policy's effect on specific operations and targets, with both channels and the kernel log attached |
| FAQ | "Beyond observing drift, what does PolicyWitness's attempt channel record?" | revise | heading loses "drift" |
| FAQ | "How does PolicyWitness handle uncertainty in its verdicts?" | replace | "What does a comparison record contain, and what does it not claim?" |
| FAQ | "Can PolicyWitness return a verdict of `drift: true`?" | replace | "Does PolicyWitness decide whether `sandbox_check` and enforcement disagree?": no; what it gives instead; how to read it |
| FAQ | "Which happens first, the prediction or the attempt?" | keep | |
| Guide, Top-level fields | the `steps[].drift` and `steps[].comparison` bullets | revise | per D1 |
| Guide, Per-step shape | "`steps[].drift`: `bool \| null`"; the `exit_code` and `syscall_errno` aliases; `scope` | remove | |
| Guide, attempt outcome notes (~800, ~829, ~860, ~863, ~923, ~1071, ~1099) | "`drift` is null …" | revise | say what the comparison fields show |
| Guide, "Filter kinds where prediction is unavailable" | "documented mismatch between `sandbox_check`'s userland verdict and the kernel's actual enforcement"; "the drift pattern is not iokit-specific" | revise | state the verified fact: no filter ID in 1..200 produced a verdict matching enforcement; keep the "Currently in this category:" marker and list format that `source_drift` parses |
| Guide, Denial-log correlation | "never rewrites a comparison, drift, failure attribution or termination cause" | revise | drop "drift" |
| Guide | the specimen dossier | add | canonical paths, `references` as the map to raw records, collection basis and limits, evidence-selection recipes without labels |
| Guide, dossier section | host facts | add | OS version/build, kernel release and architecture as environment context; no claim that they identify the worker's or validator's sandbox libraries |
| Guide, Output envelope | fields described by envelope path only | revise | the bare reply from `pw-runner-client` as readable on its own, then the envelope as that reply plus the dossier, transport and log capture |
| Guide and FAQ | signal-channel descriptions and old provenance paths | remove | |
| LIMITS | import scan bounds | add | depth/count/byte limits and the cooperative time budget from I4, including filesystem-call limitations |
| LIMITS and controller/client usage | `--timeout-ms` as reply wait; runner output buffered in full | revise | one overall client deadline plus bounded cleanup, streaming retention and incomplete-stdout rules under D6.56; worker/validator and optional log budgets stay independent |
| Guide and controller output contract | runner-client transport facts and controller failure | revise | delivery and supervision observations beside the unchanged reply; controller `tool_error` precedence does not rewrite worker/XPC evidence |
| FAQ | reading the deny log | add | optional, possibly incomplete evidence; candidate correlation does not establish attempt attribution or a comparison verdict |

### Infrastructure ledger (from REPAIR)

One row per artifact REPAIR deletes, replaces, rewrites or adds, with every
document that names it found by exact search on 2026-09-30, and the
mechanically checked part marked. Everything not marked is prose that only
reading will fix. `records/` also matches and stays untouched. After I5, R10
reruns the same searches against the finished tree.

| Artifact | REPAIR | Documents naming it (hits) | Mechanically checked part |
| --- | --- | --- | --- |
| `witness_contract/drift_determination_via_validator_seam` | I2/I4 retire with passing replacement | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1), `tests/README.md` (1), `tests/suites/witness_contract/README.md` (section) | suite table row, README presence |
| `runner_use_c_worker/drift_null_for_dac_eacces` | I2/I4 retire with passing replacement | `tests/README.md` (1), `tests/suites/runner_exec_dac/README.md` (1), `tests/suites/runner_use_c_worker/README.md` (1), `tests/suites/witness_contract/README.md` (1) | suite table row |
| `runner_use_c_worker/drift_null_for_non_policy_failure` | I2/I4 retire with passing replacement | `tests/suites/runner_use_c_worker/README.md` (2), `tests/README.md` (1), `tests/COVERAGE.md` (1), `docs/PolicyWitness.md` (1) | suite table row; outcome matrix |
| `runner_exec_dac/execute_permission_is_not_sandbox_drift` | rename | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1), `tests/README.md` (1), `tests/COVERAGE.md` (1), `tests/suites/runner_exec_dac/README.md` (whole file), `tests/suites/run_capture/README.md` (1) | suite table row; outcome matrix |
| `witness_contract/check_comparison.py` | I2 absorbed | `tests/suites/witness_contract/README.md` (1) | none |
| `DriftClassifierTests.swift` | I2 replaced | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1) | none |
| S1–S3 unused Swift helpers, `SandboxApplyTests.swift` and `SandboxLib.swift` | I3/I4 remove exclusive code/tests; retain hashing and planning | `runner/README.md`, `runner/AGENTS.md` (its stubbing paragraph is deleted, D6.45), `tests/README.md`, `tests/COVERAGE.md`, `tests/FAILURE-PROPAGATION-CONTRACT.md`, `tests/suites/runner_unit/README.md` | internal test registration and builds |
| `PWSandboxCheckShim` and Swift query-helper group | I3/I4 remove target/build dependency and helper-only tests | `tests/suites/source_drift/README.md`; `runner/Package.swift` and test/production source comments | source-set agreement, surviving planner controls and both builds |
| `bootstrap_port_failed` | D6.44 retires the spelling | `docs/PolicyWitness.md`, `tests/COVERAGE.md` | outcome inventory and mapping controls |
| `runner_outcome_libsandbox_unavailable` and `libsandbox_unavailable` | D6.44/D6.47 delete the suite with the outcome | `tests/catalog.json`, `tests/README.md`, `tests/COVERAGE.md`, `tests/suites/runner_outcome_libsandbox_unavailable/README.md`, the `_test_overrides` table in `PWRunnerAPI.swift` | catalog entry, suite table row, suite count, outcome matrix, override-key count |
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
| legacy-reading vocabulary (`legacy`, `older replies`, `stored replies`, `historical`) | D6.8 | `tests/FAILURE-PROPAGATION-CONTRACT.md` (33), `tests/COVERAGE.md` (7), `docs/CONTRACT.md` (6), `tests/README.md` (5), `runner/README.md` (4), `controller/README.md` (4), `tests/suites/blackbox_e2e/README.md` (4), `tests/suites/witness_contract/README.md` (2), one each in `tests/fixtures/README.md`, `tests/fixtures/disposition/README.md`, `tests/fixtures/worker_lifecycle/README.md`, and the `runner_filter_sysctl_name`, `runner_unit`, `blackbox_menagerie` and `runner_c_worker_harness` READMEs | none beyond the rows above |

Rationale that must survive the deletion of the artifact carrying it,
captured before I1:

- **Seam case.** A stub validator supplies the verdicts so the comparison is
  exercised independently of libsandbox's answers; the transcript is not a
  native result, and expectations come from submitted scopes and independent
  file and permission controls. Goes to the matrix README's description of
  specimen B and its use of `_test_overrides.validator_executable_path`.
- **DAC EACCES case.** A permission failure under an allow prediction is not
  evidence about the sandbox. Matrix row S03 and the `sandbox_attribution`
  obligation; the `runner_exec_dac` README's first sentence keeps it for exec.
- **Unknown-service case.** `kr=1102` means the service is not registered; it
  is not a permission result. Matrix row S14 and the guide's `lookup_failed`
  note.
- **Checker controls.** Controls run without the app before the live cases;
  controlled changes must fail; combined failures report each independent
  problem; controls exercise the checker CLI without importing its
  implementation. These four sentences go to the rebuilt controls' README.
- **Disposition fixtures.** The captured-versus-generated distinction stays;
  the captured reply's sentence becomes "reported as unsupported, which is the
  check".
- **Transport test.** The controller forwards the reply unchanged, including
  unfamiliar strings. Stays as a current-version transport test.
- **Unused Swift helpers.** The removed query/apply tests exercised their own
  unused implementations. Production planner tests, source-set checks and C
  failure controls remain the coverage owners. Preserve that distinction in
  the runner-unit and failure-contract descriptions. The stubbing guidance is
  not rationale to preserve: it described how to stub `SandboxLib`'s
  `@convention(c)` slots, and no such slot survives (D6.45).

### Opening statement and defaults

Use this framing prominently at the top of the README and the guide (D6.34):

> PolicyWitness is a macOS harness that witnesses what a sandbox policy does to
> a process. Each probe step specifies a `sandbox_check` query and a separate
> attempted operation. The validator queries the worker's PID when prediction
> is available; the worker attempts its submitted operation after applying the
> policy and receiving release from the host. PolicyWitness records each
> available result and explains missing observations. It describes what each
> channel was asked, whether their submitted scopes match, the order it
> established, and the outstanding obligations of a comparison. The controller
> adds the request path, source hashes and import inventory, runner and app
> provenance, binary hash comparisons and host facts. These records identify
> observed inputs and conditions; they do not embed the full specimen. Optional
> log capture adds available kernel denial records with correlation limits.
> PolicyWitness supplies evidence for a reader's interpretation and does not
> decide whether prediction and enforcement agree.

Add a short FAQ on reading denial logs. Explain intermittent omission, the
possibility that validator queries generate records, and the difference between
a candidate association and attribution to an attempt. Missing records do not
establish allowance. The FAQ assigns no joint label.

### Method

1. Complete both ledgers. The user-facing one is built by reading the two
   documents end to end; `rg` over the R10 vocabulary is only the starting
   point.
2. Before opening a document, write a current-state brief in scratch from the
   DESIGN sections, the matrix and the built app, without reading the old
   prose. Edit against the brief. Open the old text only to find what to
   delete and what a reader still needs. Where the plan says a passage is
   replaced, the old text is not an input.
3. Review each ledger as a whole before editing; check that the kept sentences
   still make sense once the removed ones are gone.
4. History has one sanctioned form. A past-tense clause is allowed only when it
   changes what the reader does now ("a stored reply is reported as
   unsupported" qualifies; "replies before 13 carried drift" does not). Beyond
   that, one history sentence per document, as a pointer to `git log`, never
   an account. A sentence whose subject is a deleted artifact is deleted, not
   annotated; the ledgers say which artifacts those are.
5. Write in the register of one existing paragraph per document kind, each
   describing current behavior with no history: the guide's three-state
   `path_diagnostics` paragraph; the README's "Entitlements + SBPL" section;
   the AGENTS.md "Bundle layout is a contract" section; the controller
   README's "Execution and log-evidence ownership" table.
6. Edit `QUESTIONS.md` and `LIMITS.md` first, run `generate_limits.py`, then
   the guide's own prose, then the README, then the infrastructure documents.
7. Check in after each document. The next turn reads the document cold, with
   only this section loaded, and lists every sentence that would puzzle a
   reader who never saw the previous version; those are fixed before the next
   document is opened. When a bridge seems necessary, the check-in carries
   the sentence with and without it and asks whether the bare version is
   nonsensical.
8. Completion. Run `source_drift`. Search for the tell-words (no longer,
   previously, formerly, now, instead, replaces, legacy, historical, used to,
   since response, before response) and read every hit; each that stays is
   kept with a one-line reason. Reconcile `AGENTS.md`, the runner, controller
   and test READMEs, CLI help, diagnostics, comments and docstrings with the
   guide: different wording is fine, contradiction and retired claims are not.

### Deferred

How overlapping accounts across the README, guide, contracts, READMEs, AGENTS
files, help text and comments are kept in agreement when a concept changes,
beyond exact-text search and generated copies, remains outside this plan.

Retiring `libsandbox_unavailable` ends PW's named distinction between an
unusable sandbox library and a worker that failed to launch. If that
distinction is wanted, it belongs where it can be established: the worker is
the process that binds libsandbox, a worker that cannot bind dies at dyld time
with a diagnostic, and attaching that diagnostic to the existing launch-failure
record would make the distinction evidence instead of a host-side forecast.
That is a separate change, outside this plan, and nothing here forecloses it.

[DRIFT-REMOVAL-CANDIDATES.md](DRIFT-REMOVAL-CANDIDATES.md) records S4 and
S6–S9 as potential additions, with unresolved decisions and the sections each
would affect. In particular, S9 does not supersede D1 or D6.26/42: this plan
still retains `target_mutation.status`. Adoption requires a new D6 decision
and coordinated changes to the affected design, removal and acceptance text.

## Readiness and acceptance

READY means the implementation can proceed from settled contracts and assigned
checks. It does not mean the implementation exists or acceptance has passed.
The readiness review checks:

- [x] D0/D4 permit descriptive derivation and prohibit joint verdicts; D1/D3
  share one mutation rule and explicit reporting-failure exceptions.
- [x] D2 defines collection stages, partial observations, every failure shape,
  binary baselines, request identity and implementable scanner budgets.
- [x] D5 inventories semantic and transport boundaries, including production
  Rust, and preserves request admission while specifying unsupported results.
- [x] I2–I4 assign owners to all matrix/failure cases, version gates, dossier
  failures and maximum-size controls; I1 preserves coverage until replacements
  run. Unlinked exploratory claims are not counted as evidence.
- [x] Every matrix row's response 12 columns are verified against live output,
  with receipts, and the specimen mechanics the rows depend on are recorded.
  The obligations and `comparison_conditions` columns remain design
  expectations by construction.
- [x] The removal inventory is complete for shared equipment: R4 lists every
  caller of the five removed consumer functions, including inside Rust tests.
- [x] D6.36: the dossier's presence rule covers every `kind: "run"` envelope,
  including the pre-execution `tool_error` path, through one `data` skeleton.
- [x] The documentation opening and FAQ defaults are chosen, with ledgers,
  generation rules and a semantic completion review assigned.
- [x] S1–S3 have explicit removal/preservation boundaries and coordinated
  source, build, test and documentation owners under D6.43.
- [x] D6.52 drops sandbox-library identity collection, including the controller
  cache UUID; D6.54 reconciles the test owners. Loader retirement remains.
- [x] D6.53 scopes the host source check to native API use and allows retained
  wire vocabulary and explanatory text, with positive/negative controls and
  the shipped-binary check under D6.48.
- [x] D6.49–51 remove the duplicated work the dossier would have added: no
  per-run hash of a file the manifest already describes, no temporary file on an
  ordinary run, and one OS-facts reader without a subprocess.
- [x] D6.44 retires both `bootstrap_port_failed` and `libsandbox_unavailable`
  in response 13, with the API constants, override table, guide, coverage table
  and the `runner_outcome_libsandbox_unavailable` suite moving with it.
- [x] D6.45 retires the contributor stubbing guidance with its subject: no
  `@convention(c)` slot survives under `runner/Sources/`.
- [x] D6.56 resolves D6.55: one overall client deadline, controller failure
  with preserved reply/capture, shared supervision and boundary-specific
  policies, with I4 controls and I5 documentation assigned.

The readiness review is complete and the status is READY. Implementation is a
separate step. During implementation, acceptance requires the I4 profile
measurements and final limits, retained live matrix/dossier receipts, the
completed documentation ledgers, reviewed shape goldens and maximum-reply
budgets, D5 negative controls, D6.56 transport controls, R10's explained search
residue, and the Verification battery on the integration candidate. No box
above credits those future checks as complete.
