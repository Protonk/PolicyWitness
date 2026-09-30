# Removing the drift verdict

Status: DESIGN firm as of 2026-09-30. The D1 scenario matrix and the D2
dossier fragment are written from live output; every decision is a numbered
D6 row, and any later change to DESIGN or REMOVAL is a new row. Nothing here is
implemented. The inventory baseline is df333b4
with request schema 3, response schema 12, worker ABI 7 and controller envelope
4. Source line numbers below are as of that commit and will move.

## Premise

PolicyWitness reports `steps[].drift` as `true`, `false` or `null`, and
`steps[].comparison.conclusion` as one of `agreement`, `disagreement`,
`directional_consistency` or `unavailable`. Both are verdicts about the
relation between a `sandbox_check` answer and observed enforcement. Neither is
sound as a product surface:

1. `drift: true` was deliberately made unreachable (encoder and consumers reject
   it) so that no plausible-looking determination could be built on top of it
   by agents or readers. It has been unreachable since response 8.
2. Drift between the prediction API and enforcement was always speculation. The
   Sandbox kernel extension evaluates the target PID's compiled profile for
   both the query and the hook. Every difference this repository has ever
   recorded was an input-materialization or coverage gap, never the evaluator
   answering the same question two ways: BBX-001 was a wrong filter ID; the
   three `prediction_unavailable` pairs were found by scanning filter IDs 1..200
   and finding none that matched; the deny log names `/private/etc/hosts` while
   the query took `/etc/hosts`; bare `process-exec` is rejected by the query
   while the hook is `process-exec*`; one spawn exercises exec, fork and
   file-read hooks while one query covers one. What PW can witness is the gap
   between the question the API lets you ask and the question the hook asks.
3. `drift: false` and `conclusion: unavailable` erase distinctions. `false`
   reads as "no drift" when it means allow predicted, success observed, matched
   submitted scope, no unordered mutation. `unavailable` collapses eight
   situations into one word, including the only interesting one (deny predicted,
   attempt succeeded, order established, no deny record). At summary level that
   case is indistinguishable from "the validator never ran."

The change: remove the verdict fields, keep every observation and relation that
fed them, and gather the specimen evidence a reader needs into one place. The
reader computes any label. PW supplies no joint verdict on the wire, in a
canonical test reducer, or in a guide recipe.

Repair size determines the work breakdown, not the desired design. 

Current code and documentation should describe the shipped app; 
historical names, paths and interpretations do not earn
compatibility machinery merely by having existed. Schema changes are planned
explicitly, including an envelope bump for the dossier. An anticipated schema
reset before 0.5.0 does not excuse mismatched schema numbers and emitted shapes
in the meantime.

The four sections below are executed in order. DESIGN is firm and REMOVAL is
secured. REPAIR and DOCUMENTATION are held lightly and are the next sections to
firm before execution.

## DESIGN

### D0. The one rule

The reply may describe. It may not conclude. No field in a response 13 reply
has a value space that includes a claim about the relation between the
prediction and enforcement. Descriptive values are: what was submitted, what
each channel returned and on what basis, whether the two submitted scopes
match, the order PW established by its own actions, and which obligations of a
comparison are or are not discharged, with the evidence that discharges them.

The test for a proposed field: can a reader compute any joint label from the
other fields? If yes, the label does not ship. If a field's value space contains
a word that sounds like a finding (`agreement`, `disagreement`, `drift`,
`consistent`), it does not ship.

### D1. Layer one: the per-step comparison record

`steps[].comparison` stays. Its name is accurate: it compares the two
submitted scopes and records what each channel observed. Its content changes.

| Field | Disposition | Notes |
| --- | --- | --- |
| `scope` | **remove** | Constant `submitted_operation_and_target` on every step. The guide states the scope once (D6.13). |
| `prediction` | keep | `allow`, `deny`, `unavailable`. Native verdict or its absence. |
| `observation` | keep | `succeeded`, `permission_failure`, `other_failure`, `unavailable`. The controller's `permission_failures_without_record` reads this field; it must survive unchanged. |
| `observation_basis` | keep | Names the worker fields that support `observation`. |
| `operation_relation` | keep | `matched`, `different`, `unresolved`. |
| `target_relation` | keep | `same_submitted`, `different_submitted`, `unresolved`. |
| `order` | keep | `query_first`, `unestablished`. A claim about PW's own actions, already gated by the eligibility rule and the encoder. |
| `conclusion` | **remove** | No replacement. |
| `steps[].drift` | **remove** | No replacement. |
| `limitations` | restructure | See below. |

`limitations` today is a flat list of strings rendered from a typed Swift value
(`ComparisonEvidence`) plus descriptive notes appended by the classifier. The
typed part becomes a typed wire object; the descriptive notes stay a list.

Selected shape (D1-B):

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

Rules for `obligations`:

- Only obligations whose status varies per step are per-step fields.
  `sandbox_attribution` is `not_required` for a success, `unestablished` for
  any failure, and `not_applicable` when there is no completed observation
  (D6.14). `runtime_target_identity` is `unestablished` for a path scope
  and `not_applicable` otherwise. `target_mutation` is `none`, `unordered` (a
  worker-reported successful unlink of the queried path anywhere in the run
  while order is unestablished) or `after_query` (the same with `query_first`),
  and names the steps that reported the unlink. `none` means no qualifying
  mutation was reported; it does not establish an unchanged target.
- No obligation's value space contains `established`. Runtime identity varies
  only between `unestablished` and `not_applicable`. State stability does not
  vary per step and is stated once, at run level, in the runner reply's
  `comparison_conditions` (see the fragment below), as a condition of every
  comparison this runner produces.
- `query_attempt_order_unestablished` disappears from `limitations`. It was
  defined as exactly `order != query_first` and the consumer already enforces
  that equivalence.
- `limitations` keeps only descriptive notes that have no typed home:
  `query_plan:*`, `prediction:*`, `attempt:*` (including the lifecycle
  limitations), `exec_query_not_full_spawn_prediction`, `compound_attempt`,
  `attempt_operation_unestablished`, `broad_query_operation`, `operation:*`,
  `target:*`, `query_filter_scope_unestablished`, `submitted_target_unavailable`,
  `exec_result_failed_after_spawn`, `host_path_resolution_changed`. Their
  vocabulary does not change.

D1-B is the implementation target. There is no flat-limitations fallback based
on repair cost. Inventory and assertion counts determine how to prepare and
verify the change.

Wire fragment for response 13, as the shape golden will record it:

| Path | Type | Rule |
| --- | --- | --- |
| `comparison.obligations.sandbox_attribution.status` | string | `unestablished` when `observation` is `permission_failure` or `other_failure`, or when `limitations` contains `exec_result_failed_after_spawn`; `not_applicable` when `observation` is `unavailable`; `not_required` otherwise |
| `comparison.obligations.runtime_target_identity.status` | string | `unestablished` when the query's `filter_kind` is `path` or the mapped attempt filter is `path`; `not_applicable` otherwise |
| `comparison.obligations.target_mutation.status` | string | `none`, `unordered` or `after_query` |
| `comparison.obligations.target_mutation.steps` | array of string | step IDs, in plan order, of every step whose worker-reported successful unlink names the queried path, including the current step; empty exactly when `status` is `none` |
| `comparison.limitations` | array of string | may be empty; contains none of the five removed strings |

Run-level conditions live in the runner reply, not only in the controller
dossier, because the runner produces the comparisons and `pw-runner-client`
emits the reply on its own. The reply gains
`comparison_conditions: { "unestablishable": ["state_stability"] }` beside
`steps`, present whenever `steps` is present and withheld with the comparisons
on a `runner_reporting_failed` reply. The dossier references it (D2).
The bare reply is a reader surface (D6.19), so the field stays in the reply and
the dossier points at it through `references` (D2, D6.20).

#### Scenario matrix

Every controlled scenario the repository exercises, run live on 2026-09-30
against the built app (three specimens: a real-validator plan of 24 steps, a
steered-validator plan of 7, and a pre-apply failure), then rewritten into the
response 13 shape by the rules above. Columns: prediction; observation with its
basis; operation and target relation; order; obligations as A (sandbox
attribution), I (runtime target identity), M (target mutation), with `nr` =
`not_required`, `na` = `not_applicable`, `un` = `unestablished`; then the
remaining `limitations`.

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

What the matrix establishes:

- **No collapse.** Rows with identical objects (S01, S23, S24, B7) are the same
  scenario under different attempt actions, which `attempt.requested_action`
  distinguishes. Every pair of rows that means something different differs in
  at least one field. B1, the case that today reads `unavailable` like S07 and
  S09, is now the only row with deny, succeeded, matched, same, `query_first`,
  no obligation outstanding and no limitation.
- **New information.** S19, S25 and B6 today render nothing for an ordered
  unlink; `after_query` with the unlinking step now says so. B3 and B5 today
  carry the same string; the `steps` list now says whether the step unlinked
  the path itself or another step did.
- **Every string has a home.** The five removed strings map to obligations, to
  `order`, or to the run-level condition. Every other string observed live
  appears unchanged in the last column. The pairs `attempt:attempt_not_supported`
  with `attempt:unsupported` (S09) and `attempt:slot_incomplete` with
  `attempt:not_reached` (C1) come from two sources, the missing reason and the
  disposition record, and both stay.
- **Readable without a label.** Each row answers what each channel saw, whether
  the scopes match, whether PW ordered the query first, and what is
  outstanding. Nothing in a row needs the reader to know a mapping.

The live outputs are retained in the session scratchpad, not in the repository;
the matrix is the record. During I2/I3 the same three specimens become the
`check_comparison.py` expectations and the shape golden's fixture.

### D2. Layer two: the specimen dossier

A reader investigating one run needs, in one place: what was compiled, what
each channel was asked, what the evaluator returned, what the kernel reported,
and the conditions of the run. Most of this exists in the envelope today,
scattered under `data.*`; other evidence needs collection on the normal run path.

Create a controller-owned object `data.specimen`, with controller envelope 5.
It holds what was tested and under what conditions. Everything else under
`data` describes how the run went: transport, the raw runner reply, process
diagnostics and log capture. Those records stay where they are and the guide
maps them to the dossier. No alias remains at a former path.

Disposition of every current `data` key:

| Key | Disposition | Reason |
| --- | --- | --- |
| `app_provenance` | move to `specimen.app_provenance` | provenance |
| `policy_augmentation` | move to `specimen.policy_augmentation` | what was compiled |
| `request_path` | move to `specimen.request_path` | where the input came from |
| `runner_provenance` | move to `specimen.runner_provenance` | provenance |
| `runner_service_bundle_id` | remove | equals `runner_provenance.runner_bundle_id` |
| `runner_service_name` | remove | equals `runner_provenance.runner_service_name` |
| `runner_registry_id` | remove | equals `runner_provenance.runner_registry_id` |
| `runner_service_executable` | remove | the basename of `runner_provenance.runner_executable_path` |
| `policy_check` | stay | diagnostic fallback compile on the `xpc_error` path; its `sbpl-check` output is kept verbatim, including that tool's own imports block, and is not cross-referenced with the dossier's scan |
| `runner_client` | stay | transport |
| `runner_result` | stay | the raw runner reply |
| `runner_sandbox_diagnostics` | stay | projection of the run |
| `runner_startup_diagnostics` | stay | how the run went |
| `sandbox_log_capture` | stay | the kernel's account, with its own status |
| `timeout_ms` | stay | client budget beside `runner_client` |

`data.specimen` is present on every `kind: "run"` envelope, including
`bad_request` and `xpc_error` results, since the request file was read in every
such case. Each collected item carries its own status; nothing in the dossier
is omitted to signal failure.

| Item | Today | Dossier disposition |
| --- | --- | --- |
| Policy source hash, format | `runner_result.policy_sha256`, `policy_format` | reference |
| Submitted vs applied source, augments | `data.policy_augmentation` (only when augments applied) | **move** to `specimen.policy.augmentation`, always present, `applied: []` when no augment was used (D6.15) |
| Parameter identity, compiled bytecode | `runner_result.applied_profile` (opt-in receipt) | reference; stays opt-in |
| Imports scan (`policy_closure_sha256`, per-import path/hash/mtime, completeness, truncation, cycle) | only in `sbpl-check` output, which runs only on the `xpc_error` path | **add** as `specimen.policy.imports`: collect on every applicable source-policy run, with explicit scan basis, limits and failures |
| macOS product version and build | only `sbpl-check` (`macos_build_version` via `sw_vers`) | **add** as `specimen.host`: `macos_version`, `macos_build`, `kernel_release`, `arch`, read with `sysctlbyname` (D6.16) |
| libsandbox identity | none | **add** in the runner reply as `library_identity`, observed by the XPC host per function group (see below); the dossier references it (D6.11) |
| Runner identity and entitlements | `data.runner_provenance` | **move** to `specimen.runner_provenance`, shape unchanged |
| App evidence metadata and verification | `data.app_provenance` | **move** to `specimen.app_provenance`, shape unchanged |
| Worker binary hash and entitlements | in the evidence manifest on disk, referenced by `data.app_provenance.evidence_manifest_path` | **add** as `specimen.binaries`: the service, worker and validator manifest entries, each verified against the file the run uses (D6.17) |
| Build stamp, contract versions | `build`, `runner_result.schema_version`, envelope `schema_version`, `worker_evidence.abi_version` | reference |
| What each query asked | `validator_subprocess.records[]` (operation, filter type and ID, value, rc, errno, raw line) | reference |
| What each attempt did | `steps[].attempt` (requested kind/action/path, observed path, errno, child status) | reference |
| Host path forms | `steps[].sandbox_check.path_diagnostics`, `steps[].attempt.path_diagnostics` | reference |
| Ordering | `runner_subprocess.ordering`, `steps[].comparison.order` | reference |
| Planning exclusions in this run | `steps[].sandbox_check.outcome == prediction_unavailable` plus `query_plan:*` | **add** as `specimen.conditions.prediction_unavailable_pairs`: the distinct pairs excluded in this run |
| Kernel's own account | `data.sandbox_log_capture` with its capture status and known omission | reference |
| Run-level comparison conditions | nowhere; today rendered as `state_stability_unestablished` on every step | **add** in the runner reply as `comparison_conditions.unestablishable: ["state_stability"]` (D1); the dossier references it, and the guide gives it one sentence of meaning |

The dossier is a closed list: inputs each channel fed the evaluator, the
evaluator's outputs, the kernel's independent account, and the run conditions.
Anything else proposed for it needs a reason under one of those four heads.

#### Dossier fragment

The shape for envelope 5, with the two open items marked:

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
| `request_path` | string | the path given to `run`, as today |
| `policy.format` | string | from the request; `sbpl` today |
| `policy.augmentation` | object | today's `policy_augmentation` shape, always present; `applied` is `[]` and the two hashes are equal when no augment was used |
| `policy.imports.status` | string | `complete`, `incomplete`, `failed`, `not_applicable` |
| `policy.imports.basis` | string | constant `controller_scan_of_applied_source`: the controller walks the source after augments, before invoking the runner; it is not evidence of what the worker's compiler read |
| `policy.imports.closure_sha256` | string or null | over the resolved records, computed whenever the scan ran; `status` says whether the closure is complete |
| `policy.imports.records[]` | array | the `sbpl-check` import record shape, unchanged |
| `policy.imports.cycle` | array or null | as `sbpl-check` |
| `policy.imports.limits` | object | the five bounds in force, so a reader knows what `incomplete` was measured against |
| `policy.imports.exceeded` | string or null | the first bound hit: `depth`, `count`, `file_bytes`, `total_bytes` or `wall_ms` |
| `policy.imports.failure` | string or null | why `failed`, when the scan could not run at all |
| `host.*` | string or null each | `kern.osproductversion`, `kern.osversion`, `kern.osrelease`, `hw.machine`; null when the read fails |
| `binaries.*` | object | the manifest entry for the service, worker and validator the run uses, with `path` the file hashed and `verification.status` one of `match`, `mismatch`, `unavailable`; for a BYOXPC runner the bundle's own copies are hashed against the app manifest's embedded-helper entries |
| `conditions.prediction_unavailable_pairs` | array | distinct `(operation, filter_kind)` pairs of steps carrying `query_plan:prediction_unavailable_pair`; `[]` when none |
| `references` | object | RFC 6901 JSON pointers from the envelope root to every record the dossier does not own, one key per row marked reference in the table above. The key set and the pointer values are fixed by envelope 5, not computed from presence: a pointer to a record the reply withheld or never produced is still present, and the reader finds the withholding where the reply states it. Nothing is copied. |

Collection order: host facts, binaries and the imports scan are gathered before
the runner is invoked, so a hung or refused runner still leaves a complete
dossier. A `not_applicable` scan still carries `limits`, `records: []` and null
hashes; nothing is omitted to signal a state.

Imports collection is a controller-side scan of source and files, not proof of
the exact inputs consumed by the worker's compiler. Report unresolved imports,
incomplete scanning, truncation, cycles and collection failures explicitly;
non-source specimens need an explicit not-applicable result. The existing
resolver bounds depth and count but reads imported files without a byte bound.
Reuse it with explicit byte and collection budgets, and record the limits in
`docs/limits.json`. Measure a WebProcess-size profile to establish budgets and
improve the implementation, not to reconsider default collection. An incomplete
scan must remain distinguishable from a complete one, including when it has a
hash.

Provisional budgets, to be confirmed by the I4 measurement: the helper's depth 8
and count 64 are reused; each imported file is bounded at 1 MiB and the whole
scan at 8 MiB and 1,000 ms. The host's 478 system profiles total 2.06 MB and the
largest is 43.6 KB, so these bounds are generous for real inputs and exist to
keep a hostile import chain from stalling a run. Exceeding any bound yields
`incomplete` with the bound named.

Library identity names what was observed and in which process, per function.
Verified on this host on 2026-09-30: `sandbox_check` and `sandbox_init` resolve
to `/usr/lib/system/libsystem_sandbox.dylib`; `sandbox_compile_string`,
`sandbox_apply` and `sandbox_free_profile` resolve to
`/usr/lib/libsandbox.1.dylib`. Neither file exists on disk; both are served from
the dyld shared cache (`_dyld_shared_cache_contains_path` is true for each), and
two separate processes report the same cache UUID. The record lives in the
runner reply as `library_identity`, one entry per function group:

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

The claim is exactly this: the cache image every process on the host maps for
each function, plus the presence or absence of an on-disk override at
observation time. It is not a worker-side observation, and the guide says so.

The XPC host observes (D6.11). It already loads libsandbox in `SandboxLib.load`
as its pre-spawn check, shares the bundle with both children and spawns the
worker with an empty environment, so it is the nearest observer short of the
worker. From its existing handle it resolves the functions the children use,
`sandbox_check` for the validator and `sandbox_compile_string` and
`sandbox_apply` for the worker, calls `dladdr` on each, reads
`_dyld_get_shared_cache_uuid` and `_dyld_shared_cache_contains_path`, and stats
each image path. The record is present with `status: observed` on every reply
whose host performed the load check, and with `status: unavailable` plus the
`dlopen` diagnostic when that check failed (`libsandbox_unavailable`); a
`bad_request` refusal carries none, since no process work happened. It is
retained on a degraded `runner_reporting_failed` reply because it is an
observation, not a comparison claim. Worker-published identity would need
shared-memory transport and an ABI bump; that is not part of this change, and
the ABI stays at 7.

### D3. Invariants

- Producer: `PWRunnerStepResult` has no `drift` or `deny_signal` property. `PWRunnerComparison`
  has no `conclusion` property and no `drift` accessor. The reply-shape golden
  (`tests/fixtures/contract/response_shape.json`) has neither key under
  `steps[]`, omits `deny_signal`, and has `obligations` under `comparison`.
  `PWRunnerRunResult` has no `deny_signal_total`, and `PWRunnerSignalResult` and
  `Signals.swift` are gone (R2).
- Encoder: the response 8 clause that rejects `disagreement` becomes the
  obligation-consistency table below. The `query_first` eligibility check is
  unchanged.

  | Condition | Rejected when |
  | --- | --- |
  | `target_mutation.status: after_query` | `order` is not `query_first` |
  | `target_mutation.status: unordered` | `order` is `query_first` |
  | `target_mutation.status: none` | `steps` is non-empty |
  | `target_mutation.status` other than `none` | `steps` is empty, the query's `filter_kind` is not `path`, or `limitations` carries a `query_plan:*` entry |
  | `sandbox_attribution.status` | disagrees with the D1 fragment's rule for this step's `observation` and `limitations` |
  | `runtime_target_identity.status` | disagrees with the D1 fragment's rule for this step's filter kinds |
  | any step | carries `drift`, `conclusion`, `deny_signal` or `comparison.scope`, or one of the five removed limitation strings |
  | `comparison_conditions` | absent while `steps` is present, or present on a `runner_reporting_failed` reply |
- Reply degradation: `runner_reporting_failed` still omits every `comparison`.
  `order` is a claim about PW's actions and is withheld with the rest.
  `library_identity` is an observation and is retained.
- `library_identity`: present exactly when the host performed its libsandbox
  load check; `observer` is `runner_host` and every image's `basis` is `dladdr`;
  `status: observed` requires a non-empty `images` array and a shared cache
  UUID, `status: unavailable` requires a diagnostic and no images.
- Consumer (`tests/lib/consumer.py`): for the new contract, reject
  `steps[].drift`, `steps[].deny_signal` and
  `steps[].comparison.conclusion`, reject `established` as any obligation
  status, and validate obligations against their supporting evidence. Apply the
  legacy-reader policy below to existing version branches; unsupported versions
  must not silently receive current-schema interpretations.
- Controller: no production reader of `drift` or `conclusion` exists; the only
  production reader of `comparison` is `permission_failures_without_record`,
  which reads `observation`.
- Dossier: `references` carries exactly the fixed key set with the fixed
  pointer values. The consumer rejects a missing key, an extra key or a
  different pointer.

### D4. Direct evidence assertions and reader recipes

Remove the historical joint labels and their classifier without relocating them
to an official reducer. `tests/lib/consumer.py` recovers and validates the
observations, scope relations, ordering and obligations. Scenario expectations
belong to tests and assert the evidence each scenario establishes. Replace
`comparison_groups` keyed by the old conclusions with direct evidence access or
concrete selections that preserve the distinctions between missing evidence,
different scopes and observed outcomes.

Guide recipes may select an explicit combination, such as deny predicted plus
attempt succeeded, and show the associated scope, ordering and limitations.
They do not assign `agreement`, `disagreement`, `directional_consistency` or a
joint `unavailable` verdict. Single-channel absence values such as
`prediction: unavailable` remain descriptive and are unaffected.

### D5. Versioning

- Response schema 12 → 13 for the completed comparison, the signal removal,
  the run-level `comparison_conditions` field and the host-observed
  `library_identity` record. The current contract description
  must specify the descriptive fields and typed obligations, the absence of joint
  verdicts and unobserved signal keys, and the scope of each claim.
- Controller envelope 4 → 5 for `data.specimen` and provenance relocation.
  Bump for the dossier even if its final shape were purely additive.
- Request schema and worker ABI remain unchanged. Library identity is
  host-observed (D2), so no shared-memory transport is added and the ABI stays
  at 7.
- Edit `docs/contract.json` and regenerate its copies with the implementation
  that emits the corresponding shape. A preparatory manifest bump would make
  `PWRunnerRunResult` label the old shape with the new number, because its
  initializer defaults to `PWContract.responseSchema`.
- Revise [CONTRACT.md](docs/CONTRACT.md) as follows (D6.21). Its "When a
  number moves" paragraph becomes: "Bump a number when the rules for reading
  change: a field removed, its type or meaning changed, or a new requirement
  placed on readers. An added field alone does not require a bump, since an
  absent field means unknown, never false. A bump may still be chosen for an
  additive change when the addition is a deliberate contract; the manifest's
  history says so. Because host and worker ship together, the worker ABI bumps
  on any change to the shared-memory layout or the handshake over it." Its
  "Reading older replies" section, the three version tables and "Naming numbers
  in prose" are removed; `git log -- docs/contract.json` is the history. In
  their place, a "Supported versions" section: "Every reader in this repository
  accepts exactly the numbers in the manifest and reports any other number as
  unsupported. A stored reply keeps its bytes and the meaning it had when
  written; no current tool reads it." The "What each number identifies" list
  gains one sentence per contract describing the current shape. Response:
  "`steps[].comparison` records each channel's observation, the submitted-scope
  relations, the order PW established and the typed obligations, with
  `comparison_conditions` and `library_identity` at run level; it carries no
  joint verdict and no signal channel." Envelope: "`data.specimen` is the
  dossier: request path, policy augmentation and imports, host facts, runner
  and app provenance, verified binaries, run conditions and `references` to
  the records it does not own; the raw runner reply, transport, diagnostics and
  log capture stay beside it."
- Keep schema numbers and emitted behavior aligned at every integration point.
  The user guide describes the shipped app.

### D6. Recorded decisions

| # | Decision | Resolution |
| --- | --- | --- |
| 1 | Typed obligations or flat limitations | D1-B. No repair-cost fallback; counts determine work breakdown and verification. |
| 2 | Schema bumps and integration | One response bump to 13 for the final response shape, plus envelope 5 for the dossier. Each bump lands with its implementation. Request/ABI bump if their contracts change. |
| 3 | Remove `steps[].deny_signal` | Yes, regardless of repair size. Audit `deny_signal_total`, types, helpers, fixtures and prose; remove parts serving only the abandoned channel. |
| 4 | Imports collection | Every applicable source-policy run, with explicit scan basis, completeness, limits and failures. Measure large profiles to set budgets; collection is not conditional on being cheap. |
| 5 | libsandbox identity | Per function group, observed by the XPC host (D6.11): image path, whether the shared cache serves it, on-disk presence and hash, and the shared cache UUID, with `observer` and `basis` stated. Unavailable components are explained. The claim names the cache image every process maps; it is not a worker-side observation, and the guide says so. |
| 6 | Move existing provenance under `data.specimen` | Yes for relevant controller-owned provenance and augmentation. Give each a canonical home without compatibility aliases; preserve raw channel records where their ownership matters. |
| 7 | Historical labels and reducer | Remove both the labels and the proposed canonical reducer. Tests assert evidence directly; recipes select concrete combinations without joint verdicts. |
| 8 | Supported versions for every reader | Exactly the manifest numbers. Any other version is reported as `unsupported`; no version branches remain. The one legacy artifact that survives is the captured `a1_known_loss.json`, kept as bytes to check that rejection. |
| 9 | Where run-level comparison conditions live | In the runner reply as `comparison_conditions`, because the runner produces comparisons and `pw-runner-client` emits the reply alone. The dossier references it. |
| 10 | The `data` boundary | The table in D2: four keys move, four duplicates are removed, seven stay. `data.specimen` is present on every run envelope. |
| 11 | Library identity observer | The XPC host, in `SandboxLib.load`, published in the runner reply as `library_identity`; the dossier references it. No ABI change. |
| 12 | Integration mechanics | Preparation lands on `main` as behavior-preserving commits. The contract integration (I2, I3, I4) is done in a worktree on a branch with as many commits as it needs, verified there with the default battery and `--all`, and reaches `main` as one fast-forward. No intermediate shape is ever on `main` under the final numbers. |
| 13 | `comparison.scope` | Removed. It was the same constant on every step; the guide states the scope once. |
| 14 | `sandbox_attribution` with no observation | `not_applicable`. Today's code renders nothing for this case, which reads as `not_required`; a missing observation has nothing to attribute. |
| 15 | `policy.augmentation` presence | Always present in the dossier, with `applied: []` and equal hashes when no augment was used. |
| 16 | Host facts | Read with `sysctlbyname` (`kern.osproductversion`, `kern.osversion`, `kern.osrelease`, `hw.machine`), no subprocess; the values equal `sw_vers` output on this host. |
| 17 | Binary verification | The service, worker and validator the run uses are hashed on every run and compared with their manifest entries. The whole-manifest `PW_VERIFY_EVIDENCE` path is untouched. |
| 18 | Imports scan placement | Before the runner is invoked, synchronously, on the applied source; provisional budgets in D2. |
| 19 | Reader surfaces | The controller envelope and the bare runner reply printed by `pw-runner-client` are both reader surfaces. Run-level evidence the runner produces (`comparison_conditions`, `library_identity`) lives in the reply; the dossier points at it. |
| 20 | How the dossier references records it does not own | A `references` object of RFC 6901 JSON pointers from the envelope root, one per referenced record, with a fixed key set and fixed values. No copies. |
| 21 | CONTRACT.md | The version tables, "Reading older replies" and "Naming numbers in prose" go; a "Supported versions" section and one current-shape sentence per contract replace them; the bump rule permits deliberate additive bumps (text in D5). |

### Legacy readers and retained evidence

The reader inventory is closed (D6.8). The Swift decoder gates at 8, 9 and 10,
`consumer.py` branches at 7, 8, 9 and 12, `runner_client.rs` exercises versions
4 through 8, the release tooling reads no envelopes, and no out-of-tree reader
is known. None of these is a current workflow that needs an older version, so
every branch goes and every reader accepts exactly the manifest numbers.
Keep a legacy reader or version branch only for an identified current workflow.
Record its caller, supported versions and concrete purpose in the implementation
inventory. An old fixture, link or retained envelope does not itself establish
that need. Remove branches, model properties, round-trip tests and compatibility
prose whose sole purpose is historical preservation. Do not add legacy-only
properties to current producer models as a default requirement.

Stored evidence retains its original bytes and meaning. `records/`, retained
run output and release acceptance artifacts are not rewritten to the new shape.
Their preservation does not obligate the shipped implementation to read them.
Unsupported versions must be identified as unsupported wherever a remaining
reader would otherwise interpret them using the current contract. Distinguish
captured evidence from synthetic test fixtures: regenerate fixtures for current
scenarios, and retain legacy fixtures only for a documented current reader
workflow. Historical explanation belongs in git unless it is needed to operate
a supported reader today.

## REMOVAL

This section is a starting inventory. "Removed" means: the wire keys, the code
that computes them, the invariants that police them, the tests that assert them,
and every active surface that names or promises them. This includes CLI help,
diagnostics, test messages, comments, docstrings, identifiers, filenames,
registries and overlapping documentation. Counts and file lists are not a closed
removal boundary. R9 identifies evidence and unrelated meanings that stay; the
legacy-reader policy governs compatibility code.

### R1. Wire keys

| Key | Where | Disposition |
| --- | --- | --- |
| `steps[].drift` | runner reply | removed |
| `steps[].comparison.conclusion` | runner reply | removed |
| `comparison.limitations` strings `state_stability_unestablished`, `runtime_target_identity_unestablished`, `sandbox_attribution_unestablished`, `attempt_mutation_order_unestablished`, `query_attempt_order_unestablished` | runner reply | removed from `limitations` (D1-B); the first is stated once at run level, the middle three become `obligations`, the last is dropped |
| `steps[].deny_signal` | runner reply | removed, regardless of repair cost |
| `steps[].comparison.scope` | runner reply | removed (D6.13) |
| `deny_signal_total` | runner reply | audit with the signal channel; remove if it serves only historical behavior |
| `data.policy_augmentation`, `data.runner_provenance`, `data.app_provenance`, `data.request_path` | controller envelope | relocate under `data.specimen`; remove former paths without compatibility aliases |
| `data.runner_service_bundle_id`, `data.runner_service_name`, `data.runner_registry_id`, `data.runner_service_executable` | controller envelope | removed; each duplicates or derives from `runner_provenance` |

### R2. Producer code

| File | Symbol or site | Disposition |
| --- | --- | --- |
| `runner/Sources/PWRunnerCore/PWRunnerAPI.swift` | `PWRunnerComparison.drift` (computed, ~906) | delete |
| same | `PWRunnerComparison.limitations` | keep; vocabulary shrinks |
| same | `PWRunnerComparison.conclusion` | delete; add `obligations` |
| same | `PWRunnerStepResult.drift`, its `init` parameter, `CodingKeys.drift`, the explicit-null `encode` branch and `decodeIfPresent` (~929–987) | delete; no default legacy-only property or version-gated read |
| same | `PWRunnerStepResult.deny_signal` (~921–982), `PWRunnerRunResult.deny_signal_total` (~1720–1873) and `PWRunnerSignalResult` (~857) | delete all three; the orchestrator sets both fields to nil unconditionally |
| same | encoder invariant: `steps.allSatisfy({ $0.comparison == nil && $0.drift == nil })` (~1817) and `comparison.conclusion != "disagreement", step.drift != true` (~1847) | rewrite per D3 |
| same | doc comments at ~133 ("known to drift from kernel enforcement"), ~157 ("`drift` is null for these steps"), ~726 ("the orchestrator's drift classifier") | reword |
| `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift` | `ComparisonEvidence.conclusion` (~837) | delete |
| same | `ComparisonEvidence.renderLimitations()` (~843) | becomes `renderObligations()` plus the descriptive list |
| same | `drift: comparison.drift` in step assembly (~632) | delete |
| same | `deny_signal: nil` in step assembly and `deny_signal_total: nil` in run assembly | remove with the corresponding model fields |
| same | header comment (~24–26), comments at ~722, ~763, ~890 | reword |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift` | degrade path `failed.steps[index].drift = nil` (~128) | delete the line; `comparison = nil` stays |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift` | comment ~151 ("userland-vs-kernel drift is broader than iokit") | reword; the pair set itself is untouched |
| `runner/Sources/PWRunnerCore/Signals.swift` | `installDenySignalHandler`, `denySignalCount`, the SIGUSR1 handler | delete the file; nothing under `runner/Sources` calls either function. Remove its `XPC_RUNNER_SIGNALS_FILE` line from `build.sh`, which `source_drift` checks against the tree |

The verdict-key removal needs no C change and no Rust production reader change.
The dossier is Rust only. Library identity is observed by the XPC host
(D6.11): a Swift addition in `SandboxLib.swift` and the reply model, with no C
change and no ABI bump.

### R3. Controller fixtures

Production Rust reads neither verdict key. These test fixtures construct steps
with them and become current-shaped; the legacy-shape case at ~2071 is deleted
under D6.8:

- `controller/src/run_flow.rs` at ~1638, ~2022, ~2071, ~2252, ~2394, ~2593,
  ~2652.
- `controller/src/runner_client.rs` ~163–173.
- `controller/src/log_replay_tests.rs` ~14–22.

### R4. Shared consumers

| File | Sites | Disposition |
| --- | --- | --- |
| `tests/lib/consumer.py` | `comparison_groups` keyed by `conclusion` (~79–80); `drift_present`/`drift` in step answers (~98); allowed `conclusion` set (~185); reporting-failure rule (~194); projection check (~213–215); disagreement rejections (~286, ~361); mutation rule reading `conclusion` (~296) | replace joint-label groups with direct evidence access/selections (D4); presence rejections and obligations validation per D3; delete the version branches at 7, 8, 9 and 12 and reject any non-manifest version as `unsupported` (D6.8) |
| `tests/lib/blackbox.py` | explicit-null check (~110–111); type and expected-value checks (~154–160); related signal assertions | replace removed-field assertions with direct evidence expectations and absence checks; no legacy handling remains |
| `tests/lib/lifecycle_oracle.py` | constructed reply steps carry `drift: None` and `conclusion` (~338–341) | update the constructed shape |
| `tests/lib/path_diagnostics_contract.py` | constructed step carries `drift=None` and `conclusion` (~26–32) | update |

### R5. Test assertions

Classes: **a** asserts a `drift` value; **b** asserts a `conclusion` value;
**c** tests the disagreement prohibition or the projection rule; **d** asserts
explicit-null key presence; **e** name or description only.

| Suite or target | Files | Classes | Notes |
| --- | --- | --- | --- |
| `runner_unit` | `DriftClassifierTests.swift` (53 refs) | a b c | Rename to `ComparisonEvidenceTests.swift`; the scenarios stay, the assertions move to fields and obligations |
| `runner_unit` | `EnvelopeInvariantTests.swift` (30) | a b c | Delete the version 4–7 round-trips (D6.8); update current-shape cases |
| `runner_unit` | `OrderingTests.swift` (10), `ReplyFailureTests.swift` (12 plus the field-complete fixture), `ReplyMaximumTests.swift` (2), `WorkerEvidenceTests.swift` (1), `main.swift` comment | a c d | The reply-shape golden regenerates from `ReplyFailureTests` |
| `runner_unit` | `AttemptOutcomeMappingTests.swift`, `CWorkerTests.swift` | e | Comments say "drift classifier"; reword |
| `unit/rust.unit` | R3 fixtures | a b | |
| `blackbox_e2e` | `checker_controls.py` (21) | a b c d | Negative controls that mutate `conclusion`/`drift` become controls that inject the removed keys and expect rejection |
| `blackbox_menagerie` | `checker_controls.py` (13), `validate_run.py` (1), `cases/core.json` (23 of 23 steps carry `expect.drift`) | a d | Replace `expect.drift` with expectations on the prediction, observation and relevant scope/order/obligation evidence |
| `failure_boundaries` | `check.py` (4) | a | |
| `run_effects` | `check_file_actions.py` (2) | a b | |
| `runner_exec_dac` | `check.py` (7), `check_query_scope.py` (6), `run.sh` (2) | a b e | Case id `execute_permission_is_not_sandbox_drift` becomes `execute_permission_is_unattributed_failure` |
| `runner_exec_inheritance` | `check.py` (1) | a | |
| `runner_exec_lifecycle` | `check.py` (2), `check_edges.py` (2) | a b | |
| `runner_filter_sysctl_name` | `checker_controls.py` (6) | a d | |
| `runner_outcome_runner_timeout` | `check.py` (2) | a | |
| `runner_outcome_validator_no_reply` | `check.py` (2) | a | |
| `runner_specimen_isolation` | `check.py` (1) | a | |
| `runner_use_c_worker` | `run.sh` (63) | a e | `drift_null_for_dac_eacces` becomes `dac_eacces_is_unattributed_permission_failure` and `drift_null_for_non_policy_failure` becomes `unknown_service_is_other_failure`; five descriptions in the catalog |
| `runner_validator_failure` | `check.py` (3), `check_signal.py` (1) | a b d | |
| `witness_contract` | `check_comparison.py` (11), `check_ordering.py` (10), `check_prediction_targets.py` (6), `check_removed_target.py` (2), `check_attempt_in_flight.py` (1), `check_create_existing.py` (3), `check_diagnostic_transport.py` (3), `check_pre_apply_failure.py` (3), `check_termination_correlation.py` (1), `check_worker_evidence.py` (1), `check_worker_sparse.py` (1) | a b | `check_comparison.py` is the primary C1 owner beside the seam case |
| `witness_contract` | `drift_determination_via_validator_seam.sh` (12), `run.sh` (6) | a b e | Becomes `comparison_evidence_via_validator_seam`; it stays the C1 owner |

Total as counted on df333b4: about 245 references across 30 test files, 120
across 10 Swift test files, 14 in `tests/catalog.json`. The five removed
limitation strings appear at 109 sites (`attempt_mutation_order_unestablished`
28, `sandbox_attribution_unestablished` 25, `state_stability_unestablished` 23,
`query_attempt_order_unestablished` 23, `runtime_target_identity_unestablished`
10), and `limitations` is read at 125 sites, 32 of them in
`DriftClassifierTests.swift`. `deny_signal` appears at 28 test-suite sites, 8
Swift test sites and 1 controller site. Provenance-path references and semantic
references are found through R11. Preserve
scenario coverage by replacing verdict assertions with assertions on the
evidence those scenarios establish; remove assertions whose only purpose was the
obsolete contract.

### R6. Goldens and fixtures

| Fixture | Contains | Disposition |
| --- | --- | --- |
| `tests/fixtures/contract/response_shape.json` | `drift: boolean` (~178), `conclusion: string`, `limitations: array` (~220–221), `deny_signal` and `deny_signal_total` | regenerate from the updated `ReplyFailureTests` fixture; review all removals and additions as the acknowledgement |
| `tests/fixtures/blackbox_menagerie/cases/core.json` | `expect.drift` on every step | rewrite expectations |
| `tests/fixtures/blackbox_e2e/checker/missing_path_run.json` | synthetic, response 5, no envelope number; the baseline for `blackbox_e2e/checker_controls.py` and `blackbox_menagerie/checker_controls.py` | regenerate at response 13 and envelope 5 from a live run |
| `tests/fixtures/disposition/a1_expected.json` | generated control, envelope 3 and response 10; read by `disposition_controls.py` and three `run_flow.rs` tests | regenerate at 13 and 5 |
| `tests/fixtures/disposition/a1_known_loss.json` | captured envelope, envelope 2 and response 9; `disposition_controls.py` checks that the reader rejects it as the legacy reply it is | keep the bytes; the check becomes the `unsupported` rejection under D6.8 |

### R7. Registries

- `tests/catalog.json`: four case ids and five descriptions name drift (listed
  in R5). Renaming an id changes evidence paths; `tests/RETAINED.json` and
  release acceptance records under `dist/` reference old ids and are not
  rewritten.
- `tests/README.md` suite-coverage rows for `blackbox_e2e` (~300),
  `witness_contract` (~312, ~457, ~462), `runner_use_c_worker` (~296),
  `runner_validator_failure` (~293). `source_drift` checks this table against
  the suites on disk.
- `tests/COVERAGE.md` rows ~25, ~27, ~30, ~31, ~83, ~84, ~86, ~87.
- Suite READMEs with references: `witness_contract` (20), `runner_use_c_worker`
  (12), `runner_exec_dac` (7), `blackbox_e2e` (4), `blackbox_menagerie` (3),
  `runner_specimen_isolation` (3), `runner_validator_failure` (3),
  `runner_filter_sysctl_name` (2), and one each in `run_effects`,
  `runner_exec_lifecycle`, `runner_outcome_runner_timeout`,
  `runner_outcome_validator_no_reply`, `runner_c_worker_harness`,
  `runner_byoxpc`, both iokit filter suites.

### R8. Contract text that states the removed claims

These are implementation-level documents. They belong to REMOVAL and REPAIR,
not to DOCUMENTATION, because they are read by contributors rather than users.

- [tests/FAILURE-PROPAGATION-CONTRACT.md](tests/FAILURE-PROPAGATION-CONTRACT.md):
  the "Supported public conclusion" column of the claim/evidence review; the C1
  row of the consumer-question baseline (it asks "which steps report
  established agreement"); the accepted-answer table, which speaks of
  agreement, unavailable and directional consistency throughout; the
  `drift=false projects…` and `drift=null covers…` paragraphs under "Public
  representation and meaning"; the "Ordering protocol names" row for
  `runner_reporting_failed` ("comparisons absent, drift null"); the "Permanent
  consumer enforcement" table and its "explicit drift projection" sentence; the
  "Compatibility and acceptance gate" paragraph on preserved drift values and the
  encoder's disagreement rejection. Restate C1 in terms of evidence and explain
  the current design rationale without adding a change-history narrative. The
  restated C1: "For each step, what did each channel observe and on what basis,
  do the submitted operation and target match, was the query ordered before the
  attempt batch, and which obligations remain undischarged?"
- [docs/CONTRACT.md](docs/CONTRACT.md): describe response 13 and envelope 5,
  revise the additive-change bump rule, and remove blanket backward-reading
  promises. Audit older-version clauses against the legacy-reader policy;
  historical rows are not automatically retained.
- [AGENTS.md](AGENTS.md) core idea "Predictions precede attempts" ends with
  "`drift: true` is unreachable until a separate evidence contract exists."
  Reword; the barrier claim stays.
- [runner/README.md](runner/README.md) ~74, ~230, ~240, ~260–267, ~314;
  [runner/AGENTS.md](runner/AGENTS.md) ~15 ("the orchestrator's drift
  computation"); [runner/augments/README.md](runner/augments/README.md) ~154;
  [controller/README.md](controller/README.md) ~137–145 (output contract),
  ~369, ~378.

### R9. Not removed

- The `source_drift` suite and every use of "drift" meaning docs-versus-code
  divergence: `tests/suites/source_drift/*`, `runner_abi_layout` ("layout
  drift"), comments "can't silently drift apart" in
  `CWorkerOrchestrator.swift` ~712, `AttemptOutcomeMappingTests.swift` ~96,
  `controller/src/runner_manager.rs` ~1080, `sb_api_validator.c` ~605,
  `CWorker.swift` ~47, `tests/lib/artifact.py` ~38,
  `tests/suites/dispatcher/check_selection.py` ~126.
- The `prediction_unavailable` planning set in `ProbeRunner.swift`, its
  `source_drift` agreement check against the user guide, and
  `tests/suites/witness_contract/harness/VERIFICATIONS.md`. The pair set is
  evidence; only its description changes (see DOCUMENTATION).
- `records/` is never edited.
- `comparison.order`, `runner_subprocess.ordering`, `eligibleOrderedStep`, the
  release barrier and the opt-in `order_barrier_mutations` control.
- `comparison.observation` and the controller's
  `permission_failures_without_record`.
- Stored evidence retains its original bytes and meaning. Legacy reader code,
  synthetic fixtures and round-trip tests are subject to the DESIGN policy and
  are not protected merely by a stored reply's existence.
- `dist/evidence` and `dist/archive` release acceptance records.

### R10. Still to secure before REMOVAL is final

1. Signal channel: closed. The inventory is in R2 (two model fields, one struct,
   one source file with no callers, one `build.sh` line) and R5 (28 suite sites,
   8 Swift test sites, 1 controller site, six documentation sites). All of it
   goes.
2. Fixtures: closed; see R6.
3. Reader workflows: closed by D6.8; see "Legacy readers and retained evidence".
4. Counts: closed; see the totals under R5.
5. Golden path: closed. `ContractVersionTests.swift` compares the golden, writes
   a candidate under the case artifacts and reports `ok`, `missing_golden`,
   `needs_bump` or `update`. Its header comment says "Added keys need no bump";
   revise it with the CONTRACT.md rule change in D5.
6. Dossier ownership, paths and identity basis: closed by D2 and D6.9–11. The
   imports budgets are provisional until the I4 measurement.

### R11. Semantic removal completion criterion

Run multiple searches before and after implementation, followed by contextual
reading. Search exact keys and symbols, case and naming variants, and related
language: `drift`, `conclusion`, `agreement`, `disagreement`, `consistent`,
`directional_consistency`, `verdict`, `prediction`, `enforcement`, `mismatch`,
signal-channel names, removed limitation strings and former provenance paths.
Follow discovered aliases, callers and generated copies; inspect filenames and
registry entries as well as file contents.

Cover CLI usage/help, runtime and test diagnostics, test names and descriptions,
function/type/variable names, code comments and docstrings, fixtures, registries,
and contributor and user documentation. Read affected passages and call sites
for claims that survive without any of the search terms. Preserve useful
overlapping documentation while making every account describe current behavior.

Record remaining matches by their actual meaning: a current descriptive channel
value, an unrelated use such as source drift, immutable evidence, an explicit
removed-key rejection, or a documented current legacy-reader workflow. Planning
text that names removal targets is expected. Completion requires explaining
surviving semantic references, not merely reaching zero matches for one word or
exhausting the initial inventory. The broader documentation-overlap review is
parked under DOCUMENTATION and is not a prerequisite for this removal.

## REPAIR

Held lightly as a work breakdown. Preparation may span as many turns as needed;
repair size does not change the selected design. Each integration point is
audited and leaves the default battery green with schema numbers matching the
emitted contracts.

### I1. Inventory and preparation

- Run the initial R11 searches. R10 is closed; only the I4 budget measurement
  remains open.
- Specify the final response and dossier shapes, provenance ownership, collection
  limits and any required identity transport before integrating code changes.
- Prepare shared collectors and other internal refactors where they can land
  without changing emitted behavior. Prepare the contract and test updates for
  integration, keeping documents about the shipped app accurate meanwhile.
- Do not advance `docs/contract.json` or regenerate new version constants as a
  standalone preparation step.
- Create the integration worktree and branch (D6.12) before the first change
  that alters an emitted shape.

### I2 and I3. Producer and consumers together

Producer, consumers and the dossier in I4 form one coordinated contract
integration: response 13 and envelope 5 describe their completed shapes. I2/I3
and I4 are work packages, not permission to publish intermediate shapes under
the final numbers. In particular, moving state stability out of step limitations
must land with the reply's `comparison_conditions` field.

- Swift producer changes per R2, including signal-channel removal, plus the
  `library_identity` observation in `SandboxLib.load` and its reply field. The
  field-complete fixture in `ReplyFailureTests` gains the record so the golden
  records it. Remove legacy
  decoding unless the audit identifies a current workflow that needs it; scope
  any retained support explicitly without restoring removed current fields.
- Edit `docs/contract.json` for response 13 and envelope 5 with the implementation,
  include any required request/ABI bump, and run `python3 docs/generate_contract.py`.
  Review the generated copies together with the code that emits the new shapes.
- Update `docs/CONTRACT.md` per D5. Rewrite the affected sections of
  `tests/FAILURE-PROPAGATION-CONTRACT.md` (R8): revise C1 and its current rationale,
  restate accepted answers through evidence, replace projection rules with typed
  obligations, and update enforcement owners and supported reader behavior.
- Regenerate the reply-shape golden; review the diff as the acknowledgement.
- `consumer.py`: direct evidence access and selections (D4), removed-key
  rejections and obligation validation (D3), explicit supported-version
  handling, and acceptance of a bare runner reply as well as an envelope
  (D6.19). One checker control exercises `pw-runner-client` output directly.
  No canonical joint-label reducer.
- `blackbox.py`, `lifecycle_oracle.py`, `path_diagnostics_contract.py` per R4.
- Every suite in R5: replace class-a and class-b assertions with the scenario's
  direct evidence expectations, convert class-c to injected-key rejections and
  obligation checks, replace obsolete class-d requirements with absence checks
  where useful, and rename class-e. Remove historical-only cases while retaining
  meaningful scenario coverage.
- Fixtures per R6, registries per R7.
- Rust fixtures per R3.
- Renames: `DriftClassifierTests.swift` → `ComparisonEvidenceTests.swift`
  (and its registration in `main.swift`);
  `drift_determination_via_validator_seam` → `comparison_evidence_via_validator_seam`;
  `drift_null_for_dac_eacces` → `dac_eacces_is_unattributed_permission_failure`;
  `drift_null_for_non_policy_failure` → `unknown_service_is_other_failure`;
  `execute_permission_is_not_sandbox_drift` → `execute_permission_is_unattributed_failure`. Update
  `tests/catalog.json`, `tests/README.md` and `tests/COVERAGE.md` in the same
  increment so `source_drift` passes.

### I4. The dossier

- Integrate with I2/I3 under envelope 5. Controller: `data.specimen` per D2 and
  its `data` disposition table; the run-level condition itself is in the runner
  reply (D6.9).
  Move controller-owned provenance and augmentation to their canonical dossier
  paths, remove old aliases, and update all readers and fixtures for those paths.
- Reuse the `sw_vers` helper and import resolver from
  `controller/src/bin/sbpl-check.rs`; factor them into the controller library
  rather than shelling out to the helper. Collect imports for every applicable
  source-policy run with the scan basis, completeness, budgets and failure states
  described in D2. Preserve the distinct not-applicable case.
- Library identity is produced by the runner (I2, D6.11); the dossier
  references it.
- Inline the worker's and validator's evidence-manifest entries.
- Tests: presence, ownership and shape under `unit/rust.unit`; meaningful cases
  for incomplete/failed import collection, its limits, non-applicable specimens
  and unavailable identity components; and a live `witness_contract` case that
  checks the dossier against the specimen and independently captured host facts.
  Verify that identity claims have the stated process basis and that removed
  provenance paths are absent. Test any new transport at its owning boundary.
- Measure collection on a WebProcess-size profile. Reuse appropriate depth/count
  caps, add byte and collection budgets, update `docs/limits.json` for the normal
  run path, and regenerate its documentation. Measurements inform implementation
  and budgets; they do not determine whether collection remains enabled.

### I5. Implementation documents

The R8 list minus the contract documents integrated with I2/I3: `runner/README.md`,
`runner/AGENTS.md`, `runner/augments/README.md`, `controller/README.md`,
`tests/README.md`, `tests/COVERAGE.md`, the suite READMEs, and the AGENTS.md
core idea. Update the mechanically checked portions with implementation so the
integration remains green; finish the semantic sweep across all these surfaces
and those found in R11. `source_drift` enforces only the parts that are tabulated.

### Verification

- Default battery after each integration point; `tests/run.sh --all` once at the
  end and retained as the acceptance record for the completed contract changes.
- The rule in AGENTS.md requires `order_barrier_mutations` only when the wait,
  release store or eligibility rule changes. None of them changes here. Run it
  once anyway after integration, because comparison assembly is on its path.
- The comparison set is the three fixtures under `tests/fixtures/pw_runner/`
  (`specimen_file_read_deny`, `specimen_mach_deny`,
  `specimen_path_diagnostics_strict`) plus an exec and a sysctl specimen added
  before integration so every attempt kind is compared. Compare before/after
  envelopes with run-varying values accounted for. Review removed keys, changed limitation strings, typed
  obligations, dossier additions, provenance relocation and version numbers.
  Confirm that surviving observations and their evidence have not been lost or
  reinterpreted, and that every comparison has its run-level conditions.
- Complete R11's semantic searches and contextual review. Reconcile remaining
  references against their actual meanings and the documented legacy-reader
  exceptions; passing tests alone does not establish complete removal.
- Sub-agents cannot run the built app; live verification runs from the main
  session.

## DOCUMENTATION

Held lightly, except for the method and the requirement to describe current
shipped behavior. The primary prose review covers `README.md` and
`docs/PolicyWitness.md`; R8 and R11 cover overlapping contributor docs, help and
implementation text. The guide mechanically entrains `docs/QUESTIONS.md`
(between the `SHARED QUESTIONS` markers) and `docs/LIMITS.md` (between the
`SHARED LIMITS` markers) through `python3 docs/generate_limits.py`; the copied
blocks in the guide are never edited by hand, and `source_drift` checks the
copies and the guide's `prediction_unavailable` list against the Swift set.

Remove historical explanations, old label mappings and compatibility links that
have no current use. Git retains the history. Any documentation for a retained
legacy reader must explain a supported current workflow, not keep the retired
product model alive in the guide.

### Why this section is separate

Humans and agents read these two documents first and form durable assumptions
about what PW is for and what it can do. A sentence that survives the edit
while still promising a verdict will be believed. So the edit is preceded by a
ledger, and the ledger is reviewed before any prose changes.

### The ledger

Every sentence in the two documents that states a goal or a capability gets a
row: the sentence, its classification (keep, revise, remove), and the
replacement text if revised. Seed rows found so far:

| Document | Sentence (abridged) | Class | Direction |
| --- | --- | --- | --- |
| README ¶1 | "harness for observing differences between `sandbox_check`'s userland sandbox-prediction API and the kernel's actual enforcement" | revise | PW witnesses what a policy does to a process through two channels evaluated by the same kernel evaluator; it does not adjudicate between them |
| README ¶2 | "Measuring `sandbox_check`'s prediction about a process against policy enforcement requires managing process lifecycles" | revise | Keep the lifecycle argument; drop "measuring against" |
| README Flow | "Each step records two evidence channels plus their comparison" | keep | With the comparison bullet rewritten |
| README Flow | the **Drift** bullet | remove | Replace with a **Comparison** bullet: submitted-scope relations, order, obligations, no label |
| README Flow | "Eligible `query_first` records establish this ordering; they do not establish a shared state snapshot" | keep | |
| FAQ | "When should I use PolicyWitness?" ("compares … predictions with the observed results … investigating disagreement") | revise | Use it to witness a policy's effect on specific operations and targets, with both channels and the kernel log attached |
| FAQ | "Beyond observing drift, what does PolicyWitness's attempt channel record?" | revise | Heading loses "drift" |
| FAQ | "How does PolicyWitness handle uncertainty in its verdicts?" | remove and replace | New question: "What does a comparison record contain, and what does it not claim?" |
| FAQ | "Can PolicyWitness return a verdict of `drift: true`?" | remove and replace | New question: "Does PolicyWitness decide whether `sandbox_check` and enforcement disagree?" Answer: no, by design; what it gives you instead; how to read it |
| FAQ | "Which happens first, the prediction or the attempt?" | keep | |
| Guide, Output envelope → Top-level fields | the `steps[].drift` and `steps[].comparison` bullets | revise | Per D1; add `obligations` |
| Guide, Per-step shape | "`steps[].drift`: `bool \| null`" | remove | |
| Guide, attempt outcome notes (~800, ~829, ~860, ~863, ~923, ~1071, ~1099) | "`drift` is null …" | revise | Say what the comparison fields show instead |
| Guide, "Filter kinds where prediction is unavailable" | "documented mismatch between `sandbox_check`'s userland verdict and the kernel's actual enforcement", "the drift pattern is not iokit-specific" | revise | State the verified fact: no filter ID in 1..200 produced a verdict matching enforcement, so the query cannot be made to ask the hook's question; keep the "Currently in this category:" marker and the pair list format that `source_drift` parses |
| Guide, Denial-log correlation | "never rewrites a comparison, drift, failure attribution or termination cause" | revise | Drop "drift" |
| Guide | new section: the specimen dossier | add | Canonical provenance paths and the map to raw channel records; collection basis and limits; concrete evidence-selection recipes without joint verdicts |
| Guide, dossier section | library identity | add | State the host-observed basis and the on-disk override check; say plainly that it is not a worker-side observation |
| Guide, Output envelope | fields are described by envelope path only | revise | Document the bare reply printed by `pw-runner-client` as readable on its own, then the envelope as that reply plus the dossier, transport and log capture (D6.19); the dossier's `references` are the map |
| Guide and FAQ | signal-channel descriptions and old provenance paths | revise/remove | Describe surviving evidence channels and canonical dossier paths; no historical aliases or migration narrative |
| LIMITS | import and dossier collection bounds | revise/add | Describe the normal-run depth/count, byte and collection budgets selected in I4 |

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

1. Complete the ledger for both documents. Use multiple `rg` searches with the
   vocabulary and surface coverage in R11, including signal terminology and
   former provenance paths. Build the ledger by reading the documents end to
   end, since misleading claims may contain none of the search terms.
2. Review the ledger as a whole before any edit. Check that the kept sentences
   still make sense once the removed ones are gone.
3. Edit `QUESTIONS.md` and `LIMITS.md` first, run `generate_limits.py`, then
   edit the guide's own prose, then the README.
4. Re-read both documents as a new reader. Then run `source_drift`.
5. Reconcile `AGENTS.md`'s core ideas, runner/controller/test READMEs, CLI help,
   diagnostics, comments and docstrings with the current evidence model. They
   may retain audience-specific detail and different wording, but must not
   contradict the guide or preserve retired claims. Use R11 to account for
   remaining matches.

### Holding pen: overlapping documentation (deferred)

PolicyWitness intentionally documents behavior in overlapping places, often with
different wording for different readers. That friction is accepted. The problem
to revisit is how to maintain agreement between those accounts when a concept
changes: exact-text searches and generated-copy checks cannot find every stale
promise or historical assumption.

This subsection holds a later review; it does not authorize a documentation
reorganization, deduplication project or new tooling as part of drift removal.
The current removal must still update every affected surface through R11.

Questions and inventory for whoever returns to this:

- Map overlapping subjects across the README, user guide, QUESTIONS/LIMITS,
  CONTRACT, runner/controller/test READMEs, AGENTS files, CLI help, diagnostics,
  test descriptions, comments and docstrings. Identify each account's audience,
  purpose and source of authority.
- Distinguish generated copies and enforced tables from manually maintained
  restatements. Record generator inputs and outputs, including
  `generate_limits.py` and `generate_contract.py`, and which relationships
  `source_drift` actually checks.
- Identify where different wording is useful and where it hides conflicting or
  obsolete claims. Consider how agents should search, read and reconcile those
  passages without assuming identical text or a single comprehensive document.
- Identify historical links, compatibility explanations and redundant promises
  that have no present role. Evaluate them against current shipped behavior and
  actual reader workflows, not preservation for its own sake.

The later review should produce a map of the overlaps and concrete maintenance
recommendations. Whether any material should move, be generated, be removed or
remain independently worded is open. No general consolidation decision is made
here, and this deferred review does not block completion of the present plan.

### Held lightly

- Whether `comparison` keeps its name. The recommendation is to keep it because
  it accurately names the submitted-scope relations and collected observations.
- How prominent the "witness" framing should be. The name of the project
  argues for very.
- Whether the FAQ should gain a question on reading the deny log as the
  kernel's account, given the known intermittent omission. Probably yes, short.
