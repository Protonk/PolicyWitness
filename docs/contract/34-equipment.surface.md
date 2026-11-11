# Equipment and authority setup {equipment: surface}

```contract
syntax: 1
artifact: "Equipment and authority setup"
part: "report"
goldens: ["tests/fixtures/contract/surfaces/equipment.json"]
checks: ["runner_unit", "runner_byoxpc"]
```

## Observed service inventory {inventory: subject}

```contract
record: "PWRunnerEquipmentInventory"
as: "eq_inventory"
```

The host inspects the selected service seal and reads its bounded worker-equipment.json before launching any actor.

### path {path: field}

Absolute path of the service-local worker-equipment.json selected for inspection.

### status {status: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["verified", "refused", "unobserved"]
```

verified after seal, inventory decoding and expected-identity checks; refused after a retained failure; unobserved before inspection.

### sha256 {sha256: field}

```contract
uses: ["identity.other.sha256_hex"]
```

SHA-256 of inventory bytes actually read, when available.

### schema_version {schema_version: field}

Decoded inventory schema; verified inventory has version 1.

### worker_identity {worker_identity: field}

```contract
uses: ["identity.other.sha256_hex"]
```

Decoded worker protocol identity, required to equal the host's selected worker identity for verification.

### unsigned_worker_sha256 {unsigned_worker_sha256: field}

```contract
uses: ["identity.other.sha256_hex"]
```

Decoded digest identifying the shared unsigned worker input named by the inventory.

### seal_osstatus {seal_osstatus: field}

Native service-signature validity result, when supplied by static inspection; verified inventory requires zero.

### reason {reason: field}

Refusal classification describing the failed inventory/seal boundary; absent for verified inventory.

### error {error: field}

Structured native or decoding diagnostic retained at the failed boundary.

## Sealed equipment inventory file {manifest: subject}

```contract
record: "ActorEquipmentManifest"
as: "eq_manifest"
```

The package places this JSON inventory inside each service seal after signing both worker roles. Its hashes use lowercase hexadecimal text.

### schema_version {schema_version: field}

Inventory format version; the host accepts 1.

### contract {contract: field}

Exact public build identity which must match the host's expected contract.

### worker_identity {worker_identity: field}

```contract
uses: ["identity.other.sha256_hex"]
```

Lowercase hexadecimal worker protocol identity expected by the host.

### unsigned_worker_sha256 {unsigned_worker_sha256: field}

```contract
uses: ["identity.other.sha256_hex"]
```

Lowercase hexadecimal common unsigned worker input digest.

### workers {workers: field}

Exactly two distinct role rows, selected and unentitled, providing expected signed file and entitlement identities.

## Inventory worker row {manifest_worker: subject}

```contract
record: "ActorEquipmentManifest.Worker"
as: "eq_manifest_worker"
```

Each row states the signed identity expected at a fixed service-relative worker path.

### role {role: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["selected", "unentitled"]
```

selected or unentitled, identifying the worker role.

### relative_path {relative_path: field}

Contents/MacOS/pw-probe-runner for selected; Contents/MacOS/pw-probe-runner-unentitled for unentitled.

### sha256 {sha256: field}

```contract
uses: ["identity.other.sha256_hex"]
```

Lowercase hexadecimal SHA-256 of the signed worker file.

### cdhash {cdhash: field}

```contract
uses: ["identity.other.cdhash_hex"]
```

Lowercase hexadecimal worker CodeDirectory hash.

### identifier {identifier: field}

Nonempty signing identifier expected from static code inspection, bounded to <!-- span limits.equipment_signing_text.value_unit -->255 UTF-8 bytes<!-- /span -->.

### team_id {team_id: field}

Required key whose value is the expected signing team or null; a string is nonempty and at most <!-- span limits.equipment_signing_text.value_unit -->255 UTF-8 bytes<!-- /span -->.

### entitlements_xml {entitlements_xml: field}

Entitlement dictionary serialized as an XML property list, at most <!-- span limits.equipment_entitlement_bytes.value_unit -->65,536 UTF-8 bytes<!-- /span -->; unentitled has an empty dictionary.

## Static worker binding {binding: subject}

```contract
record: "PWRunnerEquipmentBinding"
as: "eq_binding"
```

The host emits one row per inspected role and source. Binding establishes the chosen file’s observed identity and entitlement read-back; actors select rows by zero-based index.

### role {role: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["selected", "unentitled"]
```

selected or unentitled, the equipment role inspected.

### source {source: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["packaged", "test_override"]
```

packaged for service inventory equipment; test_override for an explicitly selected fixture path.

### implementation_identity {implementation_identity: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["inventory_verified", "unverified_fixture"]
```

inventory_verified for packaged rows or unverified_fixture for test overrides, identifying the source of expected implementation identity.

### relative_path {relative_path: field}

Fixed service-relative path for packaged equipment; absent for an override path.

### path {path: field}

Absolute resolved worker path inspected for launch, bounded to <!-- span limits.equipment_path.value_unit -->1,023 UTF-8 bytes<!-- /span -->.

### status {status: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["bound", "refused"]
```

bound when path, executable, hash/signature and applicable expected-identity checks pass; refused when a boundary fails.

### reason {reason: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["missing", "not_regular", "not_executable", "outside_bundle", "signature_invalid", "signature_unreadable", "entitlements_unreadable", "worker_identity_mismatch", "inspection_failed"]
```

Refusal reason: missing, not_regular, not_executable, outside_bundle, signature_invalid, signature_unreadable, entitlements_unreadable, worker_identity_mismatch or inspection_failed.

### expected_sha256 {expected_sha256: field}

```contract
uses: ["identity.other.sha256_hex"]
```

Signed-file SHA-256 digest from the packaged inventory; absent for test overrides.

### expected_cdhash {expected_cdhash: field}

```contract
uses: ["identity.other.cdhash_hex"]
```

CodeDirectory hash from the packaged inventory; absent for test overrides.

### sha256 {sha256: field}

```contract
uses: ["identity.other.sha256_hex"]
```

SHA-256 of the inspected file's actual bytes, when hashing completed.

### cdhash {cdhash: field}

```contract
uses: ["identity.other.cdhash_hex"]
```

CodeDirectory hash read from the inspected static signature, when available.

### identifier {identifier: field}

Signing identifier read from static inspection, when available.

### team_id {team_id: field}

Signing team read from static inspection, or null when the signature has none or read-back is unavailable.

### entitlements_ref {entitlements_ref: field}

Zero-based index of this binding's observed or failed entitlement read-back in equipment_entitlements.

### signature_osstatus {signature_osstatus: field}

Native static-signature validity result; a bound row requires zero.

### entitlements_match {entitlements_match: field}

Whether packaged inventory entitlements equal the observed dictionary; absent for an override or when that comparison was unavailable.

### error {error: field}

Structured native or decoding error at the failed inspection boundary, when available.

### Binding before launch {bind: acts}

```contract
who: "runner host"
where: "actor preparation before spawn"
entry: ["actors"]
recipient: ["direct_host_caller", "runner_client", "controller"]
report: ["ordinary_reply", "preparation_refusal"]
free.condition: Inspect the service seal, bounded inventory and both packaged worker roles; compare signed hashes, signing identity/team and entitlement dictionaries with the inventory. Resolve every actor's role and Boolean-true entitlement requirements.
free.effect: A preparation failure withholds every actor launch and records equipment_binding_refused with retained inspection evidence. Successful preparation selects the requested role/source path for each actor.
```

Both packaged roles are checked even if the specimen uses only one. Explicit
fixture overrides are inspected as additional `test_override` rows; their
`unverified_fixture` identity states their provenance. A bound override can
be selected, live-matched and executed. Failed packaged observations remain
preparation failures. A failed role never selects another role automatically.

### Static binding evidence {binding_evidence: owner}

```contract
scope: "subtree"
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/ActorEquipment.swift","symbol":"ActorEquipmentPreparation"}
check: {"path":"runner/Tests/PWRunnerCoreTests/ActorEquipmentTests.swift","symbol":"runActorEquipmentTests","form":"test"}
pins: "Missing unused packaged role withholds executable paths; Boolean true alone satisfies a key; live mismatch is ineligible; per-row retained observations survive failure."
context: "Temporary equipment fixture with constructed inspection calls; source and assertions read."
limits: "Execution credit is absent; fixture inspection results support branch/retention behavior."
```

## Entitlement read-back {entitlements: subject}

```contract
record: "PWRunnerEquipmentEntitlements"
as: "eq_entitlements"
```

Each table row belongs either to one static binding or to one running actor inspected against that binding.

### source {source: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["binding", "execution"]
```

binding for static signed-file read-back; execution for live actor read-back.

### binding_ref {binding_ref: field}

Zero-based index of the equipment binding this read-back describes.

### actor_id {actor_id: field}

Actor identifier for execution read-back; absent for binding read-back.

### status {status: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["observed", "failed"]
```

observed when raw_plist contains a valid bounded dictionary; failed when an error record describes unavailable read-back.

### raw_plist {raw_plist: field}

Actual entitlement dictionary serialized as an XML property list, at most <!-- span limits.equipment_entitlement_bytes.value_unit -->65,536 UTF-8 bytes<!-- /span -->; absent for failed read-back.

### error {error: field}

Read-back failure diagnostic, required for failed status and absent for observed status.

## Equipment diagnostic {error: subject}

```contract
record: "PWRunnerEquipmentError"
as: "eq_error"
```

Error metadata belongs to the named operation. Native errors carry their domain/code pair; decode or contract diagnostics may carry only a message.

### operation {operation: field}

Failing boundary: service_seal, inventory_read, inventory_decode, worker_path, worker_hash, worker_signature, worker_entitlements, guest_code, dynamic_validity, associated_static_code or signing_information.

### domain {domain: field}

Native error domain, bounded to <!-- span limits.equipment_error_domain.value_unit -->128 UTF-8 bytes<!-- /span -->; supplied together with code.

### code {code: field}

Native error code in domain, such as OSStatus or POSIX errno; absent together with domain for message-only diagnostics.

### message {message: field}

Human-readable diagnostic bounded to <!-- span limits.equipment_diagnostic_bytes.value_unit -->1,024 UTF-8 bytes<!-- /span -->, when supplied.

## Actor equipment selection {actor: subject}

```contract
record: "PWRunnerActorEquipment"
as: "eq_actor"
```

Selection resolves the actor’s role, binds its entitlement requirements and carries the live inspection result used for activation eligibility.

### requested {requested: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["selected", "unentitled"]
```

Explicit selected or unentitled request; null when the request omitted equipment.

### resolved {resolved: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["selected", "unentitled"]
```

Requested role, defaulting to selected when omitted.

### binding_ref {binding_ref: field}

Zero-based index of the selected role/source row in equipment_bindings once that row exists.

### required_entitlements {required_entitlements: field}

Distinct requested entitlement keys, at most <!-- span limits.actor_required_entitlements.value -->64<!-- /span -->; each nonempty key is at most <!-- span limits.actor_entitlement_key.value_unit -->255 UTF-8 bytes<!-- /span -->.

### requirements_status {requirements_status: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["satisfied", "unsatisfied", "unobserved"]
```

satisfied or unsatisfied from the static entitlement dictionary; unobserved when read-back is unavailable.

### missing_requirements {missing_requirements: field}

Requested keys whose values are absent or are not Boolean true, in request order. Empty means all satisfied; absence accompanies unobserved.

### execution {execution: field}

Live code and entitlement observation for the owned actor process before activation.

## Live actor inspection {execution: subject}

```contract
record: "PWRunnerEquipmentExecution"
as: "eq_execution"
```

For a setup-usable owned actor, the host inspects guest code, dynamic validity, associated static code and signing information before schedule activation.

### status {status: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["matched", "mismatched", "inspection_failed", "unobserved"]
```

matched when every comparison and time/ownership guard succeeds; mismatched for a differing executable/signature/entitlement requirement; inspection_failed for an unavailable inspection boundary; unobserved before eligible inspection.

### pid {pid: field}

Inspected actor PID, agreeing with its launch record when present.

### parent_pid {parent_pid: field}

Runner host PID recorded when inspection begins.

### observed_at_monotonic_ns {observed_at_monotonic_ns: field}

Host monotonic observation time in nanoseconds. A matched record requires valid inspection start and final clock samples, a nondecreasing final time, and both samples before the additional inspection deadline when that deadline was established. The scheduler separately guards the shared setup allowance.

### path {path: field}

Executable path reported by live code inspection, when available.

### cdhash {cdhash: field}

```contract
uses: ["identity.other.cdhash_hex"]
```

Live code's CodeDirectory hash, when available.

### identifier {identifier: field}

Live signing identifier, when available.

### team_id {team_id: field}

Live signing team, when supplied by the signature.

### entitlements_ref {entitlements_ref: field}

Zero-based index of this actor's live entitlement read-back, when reached.

### native_observations {native_observations: field}

Ordered attempted prefix of guest_code, dynamic_validity, associated_static_code and signing_information, preserving each OSStatus.

### reason {reason: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["not_launched", "setup_unavailable", "process_unavailable", "ownership_unresolved", "code_lookup_failed", "dynamic_validation_failed", "signing_readback_failed", "executable_mismatch", "signature_identity_mismatch", "entitlement_mismatch", "requirements_unsatisfied", "inspection_deadline"]
```

Ineligible reason: not_launched, setup_unavailable, process_unavailable, ownership_unresolved, code_lookup_failed, dynamic_validation_failed, signing_readback_failed, executable_mismatch, signature_identity_mismatch, entitlement_mismatch, requirements_unsatisfied or inspection_deadline.

### eligible {eligible: field}

True for matched execution, making this setup-usable actor eligible for activation; false preserves the failed or unavailable inspection state.

### Associating the owned process {inspect: acts}

```contract
who: "runner host"
where: "after setup and before any actor activation"
entry: ["actors"]
recipient: ["direct_host_caller", "runner_client", "controller"]
report: ["ordinary_reply"]
free.condition: For each setup-usable child with retained ownership, inspect live code and compare path, CodeDirectory hash, identifier, team and entitlement dictionary to its bound row; recheck each required Boolean-true entitlement and the inspection deadline.
free.effect: Matched inspection permits activation eligibility. Mismatch or inspection failure cancels all scheduling, retains earlier setup/application publications and leaves all phases unactivated and uncollected. An unavailable setup can coexist with other usable actors when no inspection failure cancels them.
```

The scheduler includes inspection in its shared <!-- span limits.actor_setup_allowance.value_unit -->10,000 milliseconds<!-- /span --> monotonic setup allowance. It requires valid clock samples before and after each inspection and records inspection_deadline, cancelling scheduling, when an otherwise successful inspection reaches or exceeds that setup deadline. Before the scheduler runs, orchestration also attempts to establish an additional monotonic deadline <!-- span limits.actor_lifetime_cutoff.value_unit -->180,000 milliseconds<!-- /span --> from that initial clock sample, reusing the configured actor-lifetime duration. This additional deadline has its own clock and origin, separate from the workers' shared continuous-clock cutoff. When its initial sample is unavailable, the additional deadline comparison is absent; the scheduler's setup guard and the inspection's valid start/final clock samples still apply. When present, the additional deadline requires both inspection samples strictly before it.

Inspection retains each attempted native call and stops at its first failed
boundary. A later inspection failure preserves an earlier cancellation reason
already selected by the scheduler. Static `bound` and live `matched` express
their respective observations; the signature entitlement dictionary supplies
the values assessed at each boundary.

### Live-inspection evidence limit {live_evidence: gap}

```contract
kind: "evidence"
```

The read unit controls construct failing Security-call results and verify the
retained attempted prefix and ineligible execution. The signed-product
acceptance evidence still needs a case reaching runtime inspection failure
and asserting cancellation with earlier application observations retained.
The optional additional deadline after an unavailable orchestration clock sample is source-read; this draft credits no control of that initial failure followed by valid inspection clocks.

## Live inspection call {native_observation: subject}

```contract
record: "PWRunnerEquipmentNativeObservation"
as: "eq_native_observation"
```

Each row identifies one attempted Security-framework boundary in its observed order.

### operation {operation: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["guest_code", "dynamic_validity", "associated_static_code", "signing_information"]
```

guest_code, dynamic_validity, associated_static_code or signing_information, in that order as reached.

### attempted {attempted: field}

True for the recorded call; the observed prefix ends at the first failing boundary.

### osstatus {osstatus: field}

Native OSStatus returned by this operation, including zero for success.

## Actor preparation refusal {preparation_failure: subject}

```contract
record: "PWRunnerPreparationFailure"
as: "eq_preparation_failure"
```

Preparation stops before actor launch when the resolved plan is inconsistent or static equipment cannot be bound.

### stage {stage: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["resolved_plan", "equipment"]
```

resolved_plan or equipment, identifying the refusing preparation boundary.

### code {code: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["inconsistent_assignment", "equipment_binding_refused"]
```

inconsistent_assignment for resolved_plan; equipment_binding_refused for equipment.

### actor_id {actor_id: field}

Actor whose entitlement requirement caused the refusal, when associated.

### binding_ref {binding_ref: field}

Zero-based refused binding row when one was produced or identified.

### reason {reason: field}

Equipment refusal classification, when the failure arose from equipment preparation.

### Preparation refusal contents {retain: reports}

```contract
who: "runner host"
where: "actor preparation refusal before launch"
entry: ["actors"]
recipient: ["direct_host_caller", "runner_client", "controller"]
report: ["preparation_refusal"]
free.condition: The resolved plan is inconsistent or equipment binding fails before actor launch.
free.effect: Return runner_failed and rc 1, preserving declared actors/phases/action IDs and preparation evidence; retain empty steps, extension events, transfers and token/delivery/handle execution tables.
```

Actors have `launch_refused` setup, absent launch/subprocess, and application
assessment from their declaration and unlaunched state. Phases keep their
declared identities with false arrival/completion and collection `not_reached`.
Equipment inventory/binding/read-back rows preserve whichever preparation
observations were obtained. The schedule records `preparation_refused`; host
authority run setup is `not_attempted`, regions/custody are empty, and worker
setup scopes identify their declared actors with decision `not_observed`.

## Authority setup account {authority_setup: subject}

```contract
record: "PWRunnerAuthoritySetup"
as: "eq_authority_setup"
```

The host retains its own setup/cleanup observations and each worker’s separately acquired setup publications.

### host {host: field}

Host-owned run, shared-region and custody scopes.

### workers {workers: field}

Actor-indexed worker setup scopes, one per declared actor and bound to that actor's identifier.

## Host authority scopes {authority_host: subject}

```contract
record: "PWRunnerAuthorityHost"
as: "eq_authority_host"
```

The host separates run prerequisites, actor shared regions and token custody into their owning scopes.

### run {run: field}

Run-wide prerequisite account, including core-limit setup.

### regions {regions: field}

Per-actor shared authority-region allocation, initialization, descriptor and cleanup observations.

### custody {custody: field}

Per-token host-private custody allocation, erasure and unmap observations.

## Authority operation scope {authority_scope: subject}

```contract
record: "PWRunnerAuthorityScope"
as: "eq_authority_scope"
```

A scope retains operation cells, its setup decision and ownership state. A decision and individual operation publications have separate acquisition boundaries.

### actor_id {actor_id: field}

Bound actor identifier for worker or region scope, when applicable.

### actor_index {actor_index: field}

Zero-based actor position for worker or region scope.

### token_ref {token_ref: field}

Bound token identifier for custody scope, when applicable.

### token_index {token_index: field}

Zero-based token position for custody scope.

### required {required: field}

Whether authority setup is required for the worker's admitted actor plan.

### publication {publication: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["observed", "not_observed"]
```

Worker decision acquisition: observed or not_observed; host-recorded scopes use their directly recorded disposition.

### disposition {disposition: field}

Worker decision ready, not_required or terminal_required_failure when observed; host scope state such as not_attempted, ready or failed records its own preparation.

### primary_operation {primary_operation: field}

Slot of the first failed/rejected operation supporting the scope decision; worker terminal_required_failure requires that published primary cell.

### operations {operations: field}

Independently observed operation cells in slot order, including cleanup after a setup failure.

### ownership {ownership: field}

Named ownership states: object_name, descriptor and mapping use not_acquired, held, released or unresolved; shared_erasure/private_erasure use not_present, performed, withheld_not_quiescent or unobserved.

### cleanup_reference {cleanup_reference: field}

Retained unresolved shared-memory name after successful creation and failed unlink, requiring ownership-aware recovery.

### integrity_errors {integrity_errors: field}

Detected malformed, repeated, missing-primary or mismatched-association publications; absence means the decoder found none.

### Acquiring setup decisions and operations {acquire: reports}

```contract
who: "runner host"
where: "worker shared-region collection"
entry: ["actors"]
recipient: ["direct_host_caller", "runner_client", "controller"]
report: ["ordinary_reply", "retained_reporting_failure"]
free.condition: After worker-identity agreement, acquire-load the decision snapshot first, then independently acquire-load each published operation cell.
free.effect: Retain valid cells even when the decision is absent. For an observed decision, validate its actor/required association and primary failed/rejected cell, recording setup_primary_unpublished when that supporting cell is unavailable.
```

The decision's release orders prerequisite cells. Reading the decision first
keeps a newly observed decision joined to its earlier primary publication.
Each cell still has its own publication flag and kind/state guards. A cleanup
cell can therefore be retained before the terminal decision appears. Invalid
cells contribute integrity errors while independently valid observations
remain available.

### Publication evidence {publication_support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: {"path":"runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift","symbol":"decodeAuthoritySetup"}
check: {"path":"runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift","symbol":"runActorAuthorityTests","form":"test"}
pins: "Constructed published cleanup cell survives absent decision, preserves native failure and cleanup role; corrupted publication flags yield invalid_setup_cell."
context: "Constructed shared-memory buffer decoded by the production host decoder; source and assertions read."
limits: "The check covers cell eligibility and corrupted flags; source supplies decision-first acquisition and primary-cell validation. No execution credit."
```

## Authority operation cell {authority_operation: subject}

```contract
record: "PWRunnerAuthorityOperation"
as: "eq_authority_operation"
```

Each fixed slot identifies one operation once. Kind controls which native fields are meaningful; cleanup cells retain their own failures alongside the primary setup failure.

### slot {slot: field}

Zero-based fixed operation-cell position within its worker, region, custody or run scope.

### operation {operation: field}

Operation registered for that scope and slot, such as descriptor_close, header_binding, shm_unlink or final_erase.

### role {role: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["setup", "cleanup"]
```

setup or cleanup, according to the operation's boundary.

### state {state: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["succeeded", "failed", "accepted", "rejected", "available", "unavailable", "performed", "not_attempted"]
```

succeeded/failed for native integer or mapping operations; accepted/rejected for validation; available/unavailable for symbols; performed for memory operations; not_attempted for an explicitly unattempted cell.

### native_kind {native_kind: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["integer", "error_code", "mapping", "symbol", "validation", "memory"]
```

integer, error_code, mapping, symbol, validation or memory, identifying the observation convention.

### native_rc {native_rc: field}

Recorded return for integer/error_code operations; absent for mapping, symbol, validation and memory observations.

### errno {errno: field}

Captured native errno on failed integer/mapping operations; absent for other states and kinds.

### detail {detail: field}

Operation-specific validation reason, including descriptor_missing or header magic/identity/actor_index/slot_counts/region_extent mismatch.

### value {value: field}

Operation-specific unsigned native observation when the cell marks a value present, such as object/page size.

### Registered operation slots {slots: definition}

```contract
defines: "value"
value: {"run":["core_limit"],"worker":["issue_symbol","consume_symbol","release_symbol","core_limit","descriptor_presence","fstat","page_size","object_size","mmap","descriptor_close","header_binding","terminal_owned_inbound_clear","rejected_mapping_munmap"],"region":["shm_open","shm_unlink","fd_cloexec","ftruncate","mmap","header_initialize","authority_duplicate","authority_spawn_dup2","close_launch_duplicate","close_original_descriptor","shared_clear","munmap"],"custody":["mmap","final_erase","munmap"]}
```

The index within each list is its fixed slot. Worker descriptor close can
belong to setup or cleanup according to the branch. Worker slots 11–12,
region slots 8–11 and custody slots 1–2 are cleanup. Integer/error-code
operations publish their return; failed integer/mapping operations publish
errno. Symbol, validation and memory states carry their corresponding
observation without an invented integer return.

## Unresolved shared-memory name {cleanup_reference: subject}

```contract
record: "PWAuthorityCleanupReference"
as: "eq_cleanup_reference"
```

A successful shm_open followed by failed shm_unlink retains this recovery reference while preserving unresolved ownership.

### kind {kind: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["posix_shm_name"]
```

posix_shm_name, the retained resource name form.

### name {name: field}

Absolute POSIX shared-memory name beginning with slash, at most <!-- span limits.authority_cleanup_name.value_unit -->31 UTF-8 bytes<!-- /span -->.

### host_pid {host_pid: field}

Host PID recorded when the name was created.

### session_nonce {session_nonce: field}

Run nonce associated with creation of this named region.

### recovery_state {recovery_state: field}

```contract
vocabulary: "closed"
listed: "exhaustive"
values: ["unresolved_manual"]
```

unresolved_manual: recovery must establish current ownership before acting because a reused name can identify another object.

## Support for record meanings {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "runner/Sources/PWRunnerCore/ActorEquipment.swift", "symbol": "ActorEquipmentPreparation"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerEquipment.swift", "symbol": "pwRunnerEquipmentProblems"}, {"path": "runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift", "symbol": "decodeAuthoritySetup"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift", "symbol": "authoritySetupIntegrityErrors"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "actorPreparationRefusal"}, {"path": "runner/Sources/PWRunnerCore/PWRunnerReply.swift", "symbol": "actorExtensionEvidenceProblem"}, {"path": "runner/Sources/PWRunnerCore/ActorScheduler.swift", "symbol": "didSetUp"}, {"path": "runner/Sources/PWRunnerCore/ActorOrchestration.swift", "symbol": "inspectionDeadline"}, {"path": "runner/Sources/PWRunnerCore/MonotonicDeadline.swift", "symbol": "static func now"}]
pins: "Imported public field definitions joined to producer/decoder/assessment meanings; explicit rule and evidence gaps preserve scope."
context: "Source and check inspection during contract drafting."
limits: "No execution credit is claimed by this owner."
```
