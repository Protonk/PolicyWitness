# Removing the drift verdict

Status: DESIGN and REPAIR firm as of 2026-09-30; REMOVAL secured; DOCUMENTATION
held lightly. Every decision is a numbered D6 row and any later change to
DESIGN or REMOVAL is a new row. Nothing is implemented. The inventory baseline
is df333b4 (request schema 3, response schema 12, worker ABI 7, controller
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

## DESIGN

### D0. The one rule

The reply may describe. It may not conclude. No field in a response 13 reply
has a value space that includes a claim about the relation between the
prediction and enforcement. Descriptive values are: what was submitted, what
each channel returned and on what basis, whether the two submitted scopes
match, the order PW established by its own actions, and which obligations of a
comparison are or are not discharged, with the evidence that discharges them.
A proposed field fails if a reader could compute it from the other fields, or
if its value space contains a finding word (`agreement`, `disagreement`,
`drift`, `consistent`).

### D1. The per-step comparison record

`steps[].comparison` keeps `prediction`, `observation`, `observation_basis`,
`operation_relation`, `target_relation` and `order` unchanged. `conclusion`,
`scope` (D6.13) and `steps[].drift` are removed. The five typed
`limitations` strings become `obligations`; the remaining strings stay a list.

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
    "target_mutation":         { "status": "none", "steps": [] }
  },
  "limitations": []
}
```

| Path | Type | Rule |
| --- | --- | --- |
| `obligations.sandbox_attribution.status` | string | `unestablished` when `observation` is `permission_failure` or `other_failure`, or when `limitations` contains `exec_result_failed_after_spawn`; `not_applicable` when `observation` is `unavailable`; `not_required` otherwise (D6.14) |
| `obligations.runtime_target_identity.status` | string | `unestablished` when the query's `filter_kind` is `path` or the mapped attempt filter is `path`; `not_applicable` otherwise |
| `obligations.target_mutation.status` | string | `none`; `unordered` when a worker-reported successful unlink of the queried path exists anywhere in the run and `order` is `unestablished`; `after_query` when the same holds with `order: query_first`. `none` does not establish an unchanged target |
| `obligations.target_mutation.steps` | array of string | step IDs, in plan order, of every step whose worker-reported successful unlink names the queried path, including the current step; empty exactly when `status` is `none` |
| `limitations` | array of string | may be empty; vocabulary unchanged: `query_plan:*`, `prediction:*`, `attempt:*` (including the lifecycle entries), `exec_query_not_full_spawn_prediction`, `compound_attempt`, `attempt_operation_unestablished`, `broad_query_operation`, `operation:*`, `target:*`, `query_filter_scope_unestablished`, `submitted_target_unavailable`, `exec_result_failed_after_spawn`, `host_path_resolution_changed`. `query_attempt_order_unestablished` is gone (it equalled `order != query_first`) |

No obligation's value space contains `established`. State stability does not
vary per step: the reply carries `comparison_conditions:
{ "unestablishable": ["state_stability"] }` beside `steps`, present whenever
`steps` is present and withheld with the comparisons on a
`runner_reporting_failed` reply (D6.9, D6.19).

#### Scenario matrix

Every controlled scenario the repository exercises, run live on 2026-09-30
against the built app (a real-validator plan of 24 steps, a steered-validator
plan of 7, and a pre-apply failure), rewritten into the response 13 shape.
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
| S19 | ordered unlink of queried path | allow | succeeded / completed_worker_status | matched | same | query_first | nr | un | after_query [S19] | `host_path_resolution_changed` |
| S20 | `process-exec-interpreter` query, binary spawn | allow | succeeded / spawned_child | different | same | query_first | nr | un | none | `exec_query_not_full_spawn_prediction`, `operation:different` |
| S21 | `local_name` query, kr=1100 | allow | permission_failure / bootstrap_permission_result | matched | unresolved | query_first | un | na | none | `query_filter_scope_unestablished`, `target:unresolved` |
| S22 | `none` filter on a file query | allow | succeeded / completed_worker_status | matched | unresolved | query_first | nr | un | none | `query_filter_scope_unestablished`, `target:unresolved` |
| S23 | allow, `access` succeeds | as S01 | | | | | | | | |
| S24 | allow, `open_write` succeeds | as S01 | | | | | | | | |
| S25 | read of the path S19 unlinked, ENOENT | allow | other_failure / completed_worker_status | matched | same | query_first | un | un | after_query [S19] | `host_path_resolution_changed` |
| B1 | steered deny, read succeeds, ordered | deny | succeeded / completed_worker_status | matched | same | query_first | nr | un | none | |
| B2 | verdict omitted, read succeeds | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | none | `prediction:validator_no_verdict` |
| B3 | verdict omitted, unlink of queried path | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | unordered [B3] | `prediction:validator_no_verdict`, `host_path_resolution_changed` |
| B4 | validator error record | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | none | `prediction:no_usable_verdict` |
| B5 | verdict omitted, read of a path B6 unlinks | unavailable | succeeded / completed_worker_status | matched | same | unestablished | nr | un | unordered [B6] | `prediction:validator_no_verdict`, `host_path_resolution_changed` |
| B6 | allow, ordered unlink | allow | succeeded / completed_worker_status | matched | same | query_first | nr | un | after_query [B6] | `host_path_resolution_changed` |
| B7 | allow, read succeeds (control) | as S01 | | | | | | | | |
| C1 | policy fails to compile, nothing runs | unavailable | unavailable / no_completed_worker_result | matched | same | unestablished | na | un | none | `prediction:validator_not_invoked`, `attempt:slot_incomplete`, `attempt:not_reached` |
| R | `runner_reporting_failed` | no `comparison` object and no `comparison_conditions`; not run live | | | | | | | | |
| T | worker deadline, slot started without result | as C1 with `attempt:started_without_result`; not run live | | | | | | | | |

Rows with identical objects (S01, S23, S24, B7) are one scenario under
different attempt actions, which `attempt.requested_action` distinguishes.
The pairs `attempt:attempt_not_supported` with `attempt:unsupported` (S09) and
`attempt:slot_incomplete` with `attempt:not_reached` (C1) come from the missing
reason and the disposition record respectively; both stay.

### D2. The specimen dossier

`data.specimen` is a controller-owned object under envelope 5, present on
every `kind: "run"` envelope including `bad_request` and `xpc_error`. It holds
what was tested and under what conditions; the records that describe how the
run went stay where they are, and the dossier points at them. No alias remains
at a former path.

| `data` key | Disposition |
| --- | --- |
| `app_provenance`, `runner_provenance` | move to `specimen.*`, shape unchanged |
| `policy_augmentation` | move to `specimen.policy.augmentation`, always present (D6.15) |
| `request_path` | move to `specimen.request_path` |
| `runner_service_bundle_id`, `runner_service_name`, `runner_registry_id`, `runner_service_executable` | remove; each equals or derives from a `runner_provenance` field |
| `policy_check` | stay; its `sbpl-check` output is kept verbatim, including that tool's own imports block |
| `runner_client`, `runner_result`, `runner_sandbox_diagnostics`, `runner_startup_diagnostics`, `sandbox_log_capture`, `timeout_ms` | stay |

```json
"specimen": {
  "request_path": "tests/fixtures/pw_runner/specimen_file_read_deny.json",
  "policy": {
    "format": "sbpl",
    "augmentation": { "applied": [], "original_sha256": "…", "applied_sha256": "…" },
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
                   "lc_uuid": "…", "entitlements": {}, "entitlements_error": null,
                   "verification": { "status": "match", "actual_sha256": "…", "reason": null } },
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
    "library_identity": "/data/runner_result/library_identity",
    "sandbox_log_capture": "/data/sandbox_log_capture",
    "build": "/build"
  }
}
```

| Path | Type | Rule |
| --- | --- | --- |
| `request_path` | string | the path given to `run` |
| `policy.format` | string | from the request |
| `policy.augmentation` | object | today's `policy_augmentation` shape; `applied` is `[]` and the two hashes are equal when no augment was used |
| `policy.imports.status` | string | `complete`, `incomplete`, `failed`, `not_applicable` (no `sbpl_source`) |
| `policy.imports.basis` | string | constant `controller_scan_of_applied_source`: the controller walks the source after augments, before invoking the runner; it is not evidence of what the worker's compiler read |
| `policy.imports.closure_sha256` | string or null | over the resolved records whenever the scan ran; `status` says whether the closure is complete |
| `policy.imports.records[]`, `cycle` | as `sbpl-check` | unchanged shapes |
| `policy.imports.limits` | object | the five bounds in force: depth 8, count 64, file 1 MiB, total 8 MiB, 1,000 ms; provisional until the I4 measurement, then recorded in `docs/limits.json` |
| `policy.imports.exceeded` | string or null | the first bound hit: `depth`, `count`, `file_bytes`, `total_bytes` or `wall_ms` |
| `policy.imports.failure` | string or null | why `failed` |
| `host.*` | string or null | `kern.osproductversion`, `kern.osversion`, `kern.osrelease`, `hw.machine` via `sysctlbyname`; null when the read fails (D6.16) |
| `binaries.*` | object | the manifest entry for the service, worker and validator the run uses, `path` the file hashed, `verification.status` one of `match`, `mismatch`, `unavailable`; a BYOXPC runner's own copies are hashed against the app manifest's embedded-helper entries (D6.17) |
| `conditions.prediction_unavailable_pairs` | array | distinct `(operation, filter_kind)` pairs of steps carrying `query_plan:prediction_unavailable_pair` |
| `references` | object | RFC 6901 JSON pointers from the envelope root to every record the dossier does not own. Key set and values are fixed by envelope 5, not computed from presence; a pointer to a withheld or absent record is still present (D6.20) |

Host facts, binaries and the imports scan are gathered before the runner is
invoked. A `not_applicable` scan still carries `limits`, `records: []` and
null hashes; nothing in the dossier is omitted to signal a state.

Library identity is one record per function group, observed by the XPC host
in `SandboxLib.load` and published in the runner reply as `library_identity`
(D6.5, D6.11). Verified on this host on 2026-09-30: `sandbox_check` and
`sandbox_init` resolve to `/usr/lib/system/libsystem_sandbox.dylib`;
`sandbox_compile_string`, `sandbox_apply` and `sandbox_free_profile` resolve to
`/usr/lib/libsandbox.1.dylib`; neither file exists on disk, both are served
from the dyld shared cache, and separate processes report the same cache UUID.

```json
"library_identity": {
  "status": "observed",
  "observer": "runner_host",
  "shared_cache_uuid": "ca11c3f5-…",
  "images": [
    { "functions": ["sandbox_check"], "image_path": "/usr/lib/system/libsystem_sandbox.dylib",
      "in_shared_cache": true, "on_disk": { "present": false, "sha256": null }, "basis": "dladdr" },
    { "functions": ["sandbox_compile_string", "sandbox_apply"], "image_path": "/usr/lib/libsandbox.1.dylib",
      "in_shared_cache": true, "on_disk": { "present": false, "sha256": null }, "basis": "dladdr" }
  ]
}
```

The host resolves the three functions from its existing handle, calls
`dladdr` on each, reads `_dyld_get_shared_cache_uuid` and
`_dyld_shared_cache_contains_path`, and stats each image path. The record is
`status: observed` on every reply whose host performed the load check,
`status: unavailable` with the `dlopen` diagnostic when that check failed
(`libsandbox_unavailable`), and absent on a `bad_request` refusal. It is
retained on a degraded `runner_reporting_failed` reply. The claim is the
identity of the cache image every process on the host maps for each function,
plus the presence or absence of an on-disk override at observation time; it is
not a worker-side observation, and the guide says so.

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
  | `target_mutation.status: none` | `steps` is non-empty |
  | `target_mutation.status` other than `none` | `steps` is empty, the query's `filter_kind` is not `path`, or `limitations` carries a `query_plan:*` entry |
  | `sandbox_attribution.status`, `runtime_target_identity.status` | disagree with the D1 rules for this step |
  | any step | carries `drift`, `conclusion`, `deny_signal`, `comparison.scope`, `sandbox_check.scope`, `attempt.exit_code` or `attempt.syscall_errno`, or one of the five removed limitation strings |
  | `comparison_conditions` | absent while `steps` is present, or present on a `runner_reporting_failed` reply |
  | `library_identity` | absent when the host performed the load check; `observer` not `runner_host`; an image `basis` not `dladdr`; `observed` without images or a cache UUID; `unavailable` without a diagnostic or with images |
- Reply degradation: `runner_reporting_failed` omits every `comparison` and
  `comparison_conditions`; `library_identity` is retained.
- Consumer (`tests/lib/consumer.py`): accepts exactly the manifest numbers and
  reports any other as `unsupported`; rejects the removed keys; rejects
  `established` as any obligation status; validates obligations against raw
  evidence; requires `references` to carry exactly the fixed keys and values.
- Controller: the only production reader of `comparison` is
  `permission_failures_without_record`, which reads `observation`.

### D4. Assertions and recipes

Tests assert the evidence each scenario establishes, by field. The consumer
validates and selects; it returns no value computed from both channels. Guide
recipes select an explicit combination, such as deny predicted plus attempt
succeeded, and show its scope, order and obligations; they assign no label.

### D5. Versioning

- Response schema 12 → 13: the comparison record, `comparison_conditions`,
  `library_identity`, and the removal of `drift`, `conclusion`,
  `comparison.scope`, `deny_signal`, `deny_signal_total`, `attempt.exit_code`,
  `attempt.syscall_errno` and `sandbox_check.scope`.
- Controller envelope 4 → 5: `data.specimen` and the `data` key dispositions.
- Request schema and worker ABI unchanged.
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
  section, the three version tables and "Naming numbers in prose" are removed.
  A "Supported versions" section replaces them: "Every reader in this
  repository accepts exactly the numbers in the manifest and reports any other
  number as unsupported. A stored reply keeps its bytes and the meaning it had
  when written; no current tool reads it." "What each number identifies" gains
  one sentence per contract. Response: "`steps[].comparison` records each
  channel's observation, the submitted-scope relations, the order PW
  established and the typed obligations, with `comparison_conditions` and
  `library_identity` at run level; it carries no joint verdict and no signal
  channel." Envelope: "`data.specimen` is the dossier: request path, policy
  augmentation and imports, host facts, runner and app provenance, verified
  binaries, run conditions and `references` to the records it does not own;
  the raw runner reply, transport, diagnostics and log capture stay beside it."

### D6. Recorded decisions

| # | Decision | Resolution |
| --- | --- | --- |
| 1 | Obligations | Typed (`obligations` object). No flat-limitations fallback. |
| 2 | Bumps | Response 13 and envelope 5, each landing with its implementation. |
| 3 | `steps[].deny_signal` | Removed with `deny_signal_total`, `PWRunnerSignalResult` and `Signals.swift`. |
| 4 | Imports collection | Every run with an `sbpl_source`, with basis, status, limits and failure; budgets confirmed by measurement. |
| 5 | Library identity | Per function group, with `observer` and `basis`; unavailable components explained; not a worker-side observation. |
| 6 | Provenance | Moved under `data.specimen`; no aliases at former paths. |
| 7 | Joint labels | None on the wire, in test equipment or in recipes. |
| 8 | Supported versions | Exactly the manifest numbers; any other is `unsupported`; no version branches. The captured `a1_known_loss.json` stays as bytes to check that rejection. |
| 9 | `comparison_conditions` | In the runner reply; the dossier references it. |
| 10 | `data` boundary | The D2 table. `data.specimen` on every run envelope. |
| 11 | Identity observer | The XPC host, in `SandboxLib.load`, publishing `library_identity` in the reply. No ABI change. |
| 12 | Integration mechanics | Behavior-preserving preparation on `main`; the contract integration in a worktree branch with as many commits as it needs, verified with the default battery and `--all`, reaching `main` as one fast-forward. |
| 13 | `comparison.scope` | Removed; the guide states the scope once. |
| 14 | `sandbox_attribution` with no observation | `not_applicable`. |
| 15 | `policy.augmentation` | Always present. |
| 16 | Host facts | `sysctlbyname`, no subprocess. |
| 17 | Binary verification | Service, worker and validator hashed on every run against their manifest entries. `PW_VERIFY_EVIDENCE` untouched. |
| 18 | Imports scan placement | Before the runner is invoked, synchronously, on the applied source. |
| 19 | Reader surfaces | The envelope and the bare reply from `pw-runner-client`. |
| 20 | References | RFC 6901 pointers, fixed keys and values, no copies. |
| 21 | CONTRACT.md | Text in D5. |
| 22 | `attempt.exit_code`, `attempt.syscall_errno` | Removed; assigned from `rc` and `errno`. |
| 23 | `sandbox_check.scope` | Removed; constant `post_sandbox`. |
| 24 | REPAIR principle | Port scenarios and invariants, never assertions or code; delete on `main` first; the matrix fixture is the single source of comparison expectations. |

Reader inventory behind D6.8: the Swift decoder gates at 8, 9 and 10;
`consumer.py` branches at 7, 8, 9 and 12; `runner_client.rs` exercises 4
through 8; the release tooling reads no envelopes; no out-of-tree reader is
known. Stored evidence (`records/`, retained run output, release acceptance
artifacts) keeps its bytes and is not rewritten; no shipped reader reads it.

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

### R2. Producer code

| File | Symbol or site | Disposition |
| --- | --- | --- |
| `runner/Sources/PWRunnerCore/PWRunnerAPI.swift` | `PWRunnerComparison.drift` (~906), `.conclusion`, `.scope` | delete; add `obligations` |
| same | `PWRunnerStepResult.drift`: init parameter, `CodingKeys.drift`, explicit-null `encode` branch, `decodeIfPresent` (~929–987) | delete, with no legacy-only property or version-gated read |
| same | `PWRunnerStepResult.deny_signal` (~921–982), `PWRunnerRunResult.deny_signal_total` (~1720–1873), `PWRunnerSignalResult` (~857) | delete |
| same | `PWRunnerAttemptResult.exit_code`, `.syscall_errno` (~704–803); `PWRunnerSandboxCheckResult.scope`, `PWRunnerWire.sandboxCheckScopePost` (~41) | delete |
| same | encoder clauses `steps.allSatisfy({ $0.comparison == nil && $0.drift == nil })` (~1817) and `comparison.conclusion != "disagreement", step.drift != true` (~1847) | rewrite per D3 |
| same | doc comments ~133, ~157, ~726 | reword |
| `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift` | `ComparisonEvidence.conclusion` (~837); `renderLimitations()` (~843); `drift: comparison.drift` (~632); `deny_signal: nil`, `deny_signal_total: nil` (~162, ~631); comments ~24–26, ~722, ~763, ~890 | delete or reword; `renderLimitations` becomes `renderObligations` plus the descriptive list |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift` | `failed.steps[index].drift = nil` (~128) | delete; `comparison = nil` stays |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift` | comment ~151; `scope:` arguments ~187, ~248 | reword; delete |
| `runner/Sources/PWRunnerCore/Signals.swift` | whole file; no caller under `runner/Sources` | delete, and its `XPC_RUNNER_SIGNALS_FILE` line in `build.sh` |
| `runner/Sources/PWRunnerCore/SandboxLib.swift` | `load` | add the `library_identity` observation |

No C change. The dossier is Rust only.

### R3. Controller fixtures

Production Rust reads no removed key. Fixtures that construct steps with them
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

### R5. Test assertions

Counts on df333b4: about 245 `drift`/`conclusion` references across 30 test
files and 120 across 10 Swift test files; the five removed limitation strings at
109 sites; `limitations` read at 125 sites; `deny_signal` at 28 suite sites, 8
Swift sites and 1 controller site; 14 catalog entries.

| Suite | Files (references) | Disposition |
| --- | --- | --- |
| `runner_unit` | `DriftClassifierTests.swift` (53) | replaced by `ComparisonEvidenceTests.swift` (REPAIR I2) |
| `runner_unit` | `EnvelopeInvariantTests.swift` (30) | version 4–7 round-trips deleted; current-shape cases updated |
| `runner_unit` | `OrderingTests.swift` (10), `ReplyFailureTests.swift` (12 plus the field-complete fixture), `ReplyMaximumTests.swift` (2), `WorkerEvidenceTests.swift` (1), comments in `AttemptOutcomeMappingTests.swift`, `CWorkerTests.swift`, `main.swift` | updated; the golden regenerates from `ReplyFailureTests` |
| `unit/rust.unit` | R3 fixtures | updated |
| `blackbox_e2e` | `checker_controls.py` (21) | rebuilt (REPAIR I3) |
| `blackbox_menagerie` | `checker_controls.py` (13), `validate_run.py` (1), `cases/core.json` (23 steps carry `expect.drift`) | `expect.drift` deleted |
| `failure_boundaries` (4), `run_effects` (2), `runner_exec_inheritance` (1), `runner_exec_lifecycle` (4), `runner_filter_sysctl_name` (6), `runner_outcome_runner_timeout` (2), `runner_outcome_validator_no_reply` (2), `runner_specimen_isolation` (1), `runner_validator_failure` (4) | check scripts | field assertions |
| `runner_exec_dac` | `check.py` (7), `check_query_scope.py` (6), `run.sh` (2) | field assertions; case id becomes `execute_permission_controls_spawn` |
| `runner_use_c_worker` | `run.sh` (63) | `drift_null_for_dac_eacces` and `drift_null_for_non_policy_failure` deleted (S03, S17, S14); other assertions become field assertions |
| `witness_contract` | `check_ordering.py` (10), `check_prediction_targets.py` (6), `check_create_existing.py` (3), `check_diagnostic_transport.py` (3), `check_pre_apply_failure.py` (3), `check_removed_target.py` (2), `check_attempt_in_flight.py`, `check_termination_correlation.py`, `check_worker_evidence.py`, `check_worker_sparse.py` (1 each) | field assertions |
| `witness_contract` | `check_comparison.py` (11), `drift_determination_via_validator_seam.sh` (12), `run.sh` (6) | absorbed by `comparison_matrix` (REPAIR I2); the seam case deleted |

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

- `tests/catalog.json`: three ids deleted, one renamed, two added (REPAIR I5).
  `tests/RETAINED.json` and release acceptance records under `dist/` reference
  old ids and are not rewritten.
- `tests/README.md` suite-coverage rows (~293, ~296, ~300, ~312) and the
  "Comparison evidence coverage" section (~455–465); `source_drift` checks the
  table against the suites on disk.
- `tests/COVERAGE.md` rows ~25, ~27, ~30, ~31, ~83, ~84, ~86, ~87.
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

## REPAIR

Port scenarios and invariants, never assertions or code. Every test artifact
the removal touches is classified once:

| Class | What it is | Disposition |
| --- | --- | --- |
| Scenario | A case with an independent control: a real file, a direct OS call, a steered verdict, a captured host fact | Keep. Expectations come from the D1 matrix or the case's own control. |
| Old-contract control | A control proving the checker rejects a loss expressible only in the removed contract | Delete. Re-express only when the invariant survives in D3, in D3's wording. |
| Legacy branch | Code, a fixture, a round-trip or prose whose purpose is reading a version no reader accepts | Delete. |
| Equipment | A shared library or helper | Rewrite from the contract: no version branches, no derived labels, no compatibility fallbacks. |

Keeping anything requires naming the matrix row or the D3 invariant it serves.

### I1. Delete on `main`

Everything in the second and third classes whose removal leaves the default
battery green at response 12 lands on `main` before the integration worktree
opens. The rationale lines in DOCUMENTATION's infrastructure ledger are
confirmed captured first.

- Swift: the `EnvelopeInvariantTests` groups "response 7 preserves legacy
  uncertainty", the version 4 through 6 round-trips, the stored response 4
  signal object, "legacy absent or null observations remain unknown" and
  "legacy integer PID remains readable"; the `OrderingTests` case "encoder
  rejects public disagreement"; the `ReplyFailureTests` defects
  `disagreement`, `false_drift` and `true_drift`.
- Rust: the version 4 through 8 loop in `runner_client.rs`; the legacy-shape
  case in `run_flow.rs` (~2071).
- `blackbox_e2e/checker_controls.py`: `response7*`, `legacy7_difference`,
  `blanket_unknown`, `supported_agreement`, `false_drift`, `true_drift`,
  `missing_drift`, `removed_*_false_claim`, `disagreement_without_labels`,
  `order_limit`, and the synthesized response 7 envelope in `main()`.
- `tests/lib/lifecycle_contract.py`, `lifecycle_adapter.py`,
  `lifecycle_oracle.py`: the `MISSING` sentinel, `RESPONSE_WITH_DISPOSITION`,
  the legacy projection rows and transport notes, the
  `legacy_host_facts_missing` example, and every `not_reported` state that
  only a reply before the record could produce.
- `tests/lib/blackbox.py`: the `effective_filter_value` fallback.
- Cases: `runner_use_c_worker/drift_null_for_dac_eacces` (S03, S17),
  `runner_use_c_worker/drift_null_for_non_policy_failure` (S14),
  `witness_contract/drift_determination_via_validator_seam` (B1 to B7), with
  their catalog entries, `tests/README.md` rows and `tests/COVERAGE.md`
  mentions.
- Preparation that changes no emitted byte: factor `resolve_imports`,
  `compute_closure_hash` and the OS-facts read out of `sbpl-check.rs` into the
  controller library; write the matrix fixture (I2); add an exec and a sysctl
  specimen under `tests/fixtures/pw_runner/`; create the worktree (D6.12).

### I2. The matrix fixture

`tests/fixtures/comparison/matrix.json` holds the 32 rows: for each, the
specimen inputs (policy, query, attempt, steered verdict if any, independent
control) and the expected response 13 `comparison` object. Two readers:

- `witness_contract/comparison_matrix`, new: runs the three specimens through
  the CLI, checks every step against its row with `validate` and `select`, and
  keeps the independent controls `check_comparison.py` had (the direct EACCES
  open, the retained file bytes).
- `runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift`, replacing
  `DriftClassifierTests.swift`: table-driven over the same file through
  `comparisonEvidence(...)`, plus the existing host-path-provenance group;
  registered in `main.swift`.

### I3. Equipment

- `tests/lib/consumer.py` exposes `validate(document)`, `steps(document)`,
  `select(steps, **fields)`, `lifecycle(document)` and `denials(document)`.
  `document` is an envelope or a bare runner reply. A version other than the
  manifest's yields one `unsupported` error. `validate` merges
  `validate_evidence_shape`, `validate_current_build_evidence` and
  `validate_ordering` and checks obligations against raw evidence:
  `target_mutation` from every worker-reported successful unlink,
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
  `references`; missing `comparison_conditions` or `library_identity` where
  required; path provenance; the ordering chain; reporting-failure
  withholding; an unsupported version; one control feeding `pw-runner-client`
  output to `validate`. The mutation-order controls are re-expressed against
  `target_mutation`.
- Menagerie: `expect.drift` deleted from `core.json`; `validate_run.py` passes
  `expect.comparison` through. `BBX-001` and `BBX-002` `expected.json` lose
  their drift keys. Other fixtures per R6.

### I4. Producer and dossier, in the worktree

- Swift per R2, D6.22 and D6.23, plus `library_identity` and
  `comparison_conditions`. The field-complete fixture in `ReplyFailureTests`
  gains the new records; the string classification in `ReplyMaximumTests`
  gains every new string key; the shape golden regenerates.
- Controller per D2 with Rust tests for shape, statuses, budgets, the fixed
  reference set and the relocated paths; `docs/limits.json` gains the scan
  budgets after measurement on the largest system profile and a
  WebProcess-size specimen.
- `docs/contract.json` to 13 and 5 with these changes, then
  `python3 docs/generate_contract.py`.
- `witness_contract/dossier_witness`, new: the dossier against the specimen
  that ran and host facts the test captures independently (`sw_vers`,
  `uname`, the manifest, a hash of the worker binary).

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
- `tests/catalog.json`: `comparison_matrix` and `dossier_witness` added;
  `execute_permission_is_not_sandbox_drift` becomes
  `execute_permission_controls_spawn`.
- `tests/README.md`: the "Comparison evidence coverage" section becomes one
  paragraph pointing at the matrix fixture and its two readers; affected suite
  rows rewritten. `tests/COVERAGE.md` rows likewise. Suite and fixture READMEs
  follow DOCUMENTATION's infrastructure ledger.
- `runner/README.md`, `runner/AGENTS.md`, `runner/augments/README.md`,
  `controller/README.md` (including its consumer-audit table) and the
  AGENTS.md core idea per R8.

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
  record. `order_barrier_mutations` once after integration.
- Before I1 and after the fast-forward, run the five specimens under
  `tests/fixtures/pw_runner/` and diff the envelopes with run-varying values
  accounted for.
- R10 over the test tree and equipment.
- The finished `consumer.py` has no function returning a value computed from
  both channels and no branch on `schema_version` other than the equality
  check.
- Sub-agents cannot run the built app; live verification runs from the main
  session.

## DOCUMENTATION

Held lightly except for the method. The prose review covers `README.md` and
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
| Guide, dossier section | library identity | add | the host-observed basis and the on-disk override check; not a worker-side observation |
| Guide, Output envelope | fields described by envelope path only | revise | the bare reply from `pw-runner-client` as readable on its own, then the envelope as that reply plus the dossier, transport and log capture |
| Guide and FAQ | signal-channel descriptions and old provenance paths | remove | |
| LIMITS | import scan bounds | add | the normal-run depth, count, byte and time budgets from I4 |

### Infrastructure ledger (from REPAIR)

One row per artifact REPAIR deletes, replaces, rewrites or adds, with every
document that names it found by exact search on 2026-09-30, and the
mechanically checked part marked. Everything not marked is prose that only
reading will fix. `records/` also matches and stays untouched. After I5, R10
reruns the same searches against the finished tree.

| Artifact | REPAIR | Documents naming it (hits) | Mechanically checked part |
| --- | --- | --- | --- |
| `witness_contract/drift_determination_via_validator_seam` | I1 delete | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1), `tests/README.md` (1), `tests/suites/witness_contract/README.md` (section) | suite table row, README presence |
| `runner_use_c_worker/drift_null_for_dac_eacces` | I1 delete | `tests/README.md` (1), `tests/suites/runner_exec_dac/README.md` (1), `tests/suites/runner_use_c_worker/README.md` (1), `tests/suites/witness_contract/README.md` (1) | suite table row |
| `runner_use_c_worker/drift_null_for_non_policy_failure` | I1 delete | `tests/suites/runner_use_c_worker/README.md` (2), `tests/README.md` (1), `tests/COVERAGE.md` (1), `docs/PolicyWitness.md` (1) | suite table row; outcome matrix |
| `runner_exec_dac/execute_permission_is_not_sandbox_drift` | rename | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1), `tests/README.md` (1), `tests/COVERAGE.md` (1), `tests/suites/runner_exec_dac/README.md` (whole file), `tests/suites/run_capture/README.md` (1) | suite table row; outcome matrix |
| `witness_contract/check_comparison.py` | I2 absorbed | `tests/suites/witness_contract/README.md` (1) | none |
| `DriftClassifierTests.swift` | I2 replaced | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1) | none |
| `EnvelopeInvariantTests` legacy groups | I1 delete | `tests/FAILURE-PROPAGATION-CONTRACT.md` (3), `tests/COVERAGE.md` (2) | outcome matrix |
| `runner_client.rs` version loop | I1 delete | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1) | none |
| `checker_controls.py` legacy and drift controls | I1 delete, I3 rebuild | `tests/FAILURE-PROPAGATION-CONTRACT.md` (7), `tests/README.md` (6), `tests/COVERAGE.md` (2), `tests/suites/blackbox_e2e/README.md` (2), `tests/suites/blackbox_menagerie/README.md` (2), `tests/suites/runner_filter_sysctl_name/README.md` (2), `controller/README.md` (1), one each in the `smoke`, `run_effects`, `runner_byoxpc` and both iokit filter suite READMEs | suite table rows; outcome matrix |
| `consumer.py` `recover_evidence` and its groups | I3 rewrite | `tests/FAILURE-PROPAGATION-CONTRACT.md` (1), `controller/README.md` (consumer-audit table) | none |
| `consumer.py` three validators | I3 merge | `tests/FAILURE-PROPAGATION-CONTRACT.md` (2) | none |
| `blackbox.py` `effective_filter_value` fallback | I1 delete | `docs/CONTRACT.md` (1) | none |
| `blackbox.py` alias-agreement rule | I3 delete | `tests/README.md` (2), `tests/suites/blackbox_e2e/README.md` (2), `tests/suites/blackbox_menagerie/README.md` (2), `runner/README.md` (1), `docs/PolicyWitness.md` (1), one each in the `runner_filter_sysctl_name`, `runner_specimen_isolation` and `runner_outcome_runner_timeout` READMEs | suite table rows; guide per-step shape line |
| lifecycle legacy rows and sentinels | I1 delete | `tests/FAILURE-PROPAGATION-CONTRACT.md` (7), `tests/suites/blackbox_e2e/README.md` (2), `docs/CONTRACT.md` (1), `controller/README.md` (1), `tests/fixtures/disposition/README.md` (1), `tests/suites/witness_contract/README.md` (1) | none |
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

### A proposed statement of what PolicyWitness is

To be agreed before editing, then placed at the top of the README and the guide:

> PolicyWitness is a macOS harness that witnesses what a sandbox policy does to
> a process. For each probe step it records two independent observations
> against the same sandboxed PID: the answer `sandbox_check` gives for a
> submitted operation and filter, and the result of attempting that operation
> inside the worker. It records what each channel was asked, what it returned,
> whether the two submitted scopes match, the order PolicyWitness established
> between them, and which obligations of a comparison remain undischarged. It
> attaches the policy, the runner's identity and entitlements, the host's OS
> build, and the kernel's own deny log where available. PolicyWitness does not
> decide whether the prediction and the enforcement agree. It gives a reader the
> materials to decide and states what those materials cannot show.

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

### Open

- How prominent the "witness" framing should be in the README.
- Whether the FAQ gains a short question on reading the deny log as the
  kernel's account, given its known intermittent omission.
- Deferred and not part of this plan: how overlapping accounts across the
  README, guide, contracts, READMEs, AGENTS files, help text and comments are
  kept in agreement when a concept changes, beyond exact-text search and
  generated copies.
