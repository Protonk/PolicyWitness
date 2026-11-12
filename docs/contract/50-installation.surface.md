# Managing runners {installation: surface}

```contract
syntax: 1
artifact: "Managing runners"
part: "installation"
goldens: ["tests/fixtures/contract/surfaces/installation.json"]
checks: ["unit", "runner_byoxpc"]
```

The controller manages external XPC services through a local registry and launchd. Registry state, on-disk signature observations, live service presence and a completed verification specimen establish different facts.

## Implementation and evidence {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "controller/src/runner_commands.rs", "symbol": "cmd_runner_install"}, {"path": "controller/src/runner_commands.rs", "symbol": "cmd_runner_verify"}, {"path": "controller/src/runner_commands.rs", "symbol": "cmd_runner_validate"}, {"path": "controller/src/runner_commands.rs", "symbol": "cmd_runner_reconcile"}, {"path": "controller/src/runner_manager.rs", "symbol": "RunnerRegistry"}, {"path": "controller/src/runner_manager.rs", "symbol": "save_registry"}, {"path": "controller/src/runner_manager.rs", "symbol": "install_record"}, {"path": "controller/src/runner_manager.rs", "symbol": "remove_record"}, {"path": "controller/src/runner_manager.rs", "symbol": "plist_ownership"}, {"path": "controller/src/runner_manager.rs", "symbol": "service_ownership"}, {"path": "controller/src/runner_manager.rs", "symbol": "read_back"}]
check: [{"path": "controller/src/runner_manager.rs", "symbol": "install_failure_boundaries_preserve_observed_pending_state", "form": "test"}, {"path": "controller/src/runner_manager.rs", "symbol": "legacy_metadata_survives_unrelated_writes_and_pending_cleanup", "form": "test"}, {"path": "controller/src/runner_manager.rs", "symbol": "historical_flattened_cleanup_remains_readable_and_rewrites_with_nested_runner", "form": "test"}, {"path": "controller/src/runner_manager.rs", "symbol": "registry_save_refuses_duplicate_known_metadata_before_publication", "form": "test"}, {"path": "controller/src/runner_manager.rs", "symbol": "atomic_registry_replace_preserves_old_open_readers_and_failed_write", "form": "test"}, {"path": "controller/src/runner_manager.rs", "symbol": "bootout_waits_out_launchd_teardown_within_the_budget", "form": "test"}]
pins: "Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation."
context: "Read the cited producer/receiver declarations and branches; check citations identify the assertions read."
limits: "These read controls use registry files and supplied cleanup/signing observations. Live launchd, GUI-session access, signing, interruption recovery and opaque metadata through all CLI transitions need separately recorded execution evidence."
```

## Command boundaries {commands: subject}

### Read and select records {read: acts}

```contract
who: ["identity.definitions.controller"]
where: "runner registry lookup"
entry: ["runner_list", "runner_status", "runner_verify", "runner_remove", "runner_reconcile"]
recipient: ["cli_caller"]
report: ["runner_registry", "runner_status", "runner_verify", "runner_remove", "runner_reconcile"]
free.condition: The registry is readable with schema_version 1, or its path is absent.
free.effect: Use PW_RUNNER_REGISTRY when nonempty, otherwise HOME/Library/Application Support/PolicyWitness/runners.json. An absent file yields schema_version 1 with empty runners and pending_cleanup. For selector commands, prefer a supplied id and otherwise use service_name; an unmatched id remains a miss.
retained_free: {"condition":{"kind":"raw_admission","reason":"Registry absence, unreadability and decoded schema version are filesystem/decoder outcomes before a registry value exists."},"effect":{"kind":"raw_admission","reason":"Environment path choice and command selector precedence are raw process inputs; an empty decoded registry cannot distinguish an absent file."}}
```

`runner list` returns the registry as `kind: "runner_registry"`. `runner status` returns the selected active record as `kind: "runner_status"`. Status and verify search `runners`; removal also resumes `pending_cleanup`. A miss returns that operation’s envelope kind, `result.normalized_outcome: "not_found"`, false `ok` and exit code 2. Unsupported registry schemas and malformed known fields refuse loading. Read-only commands can read the prior or replacement complete registry while a modifier holds its lock.

### Publish a registry mutation {publish: acts}

```contract
who: ["identity.definitions.controller"]
where: "install, validate and remove registry transaction"
entry: ["runner_install", "runner_validate", "runner_remove"]
recipient: ["cli_caller"]
report: ["runner_registry"]
free.condition: The command holds the stable sibling registry lock across its mutation and associated launchd actions.
free.effect: Serialize and read back the proposed registry, require lossless reserialization, write and sync a new mode-0600 file in the same directory, then atomically rename it over the registry. Refuse a busy/unavailable advisory lock or a readback that loses metadata.
retained_free: {"condition":{"kind":"native_protocol","reason":"Advisory lock ownership and its lifetime span filesystem publication and launchd actions independently of registry contents."},"effect":{"kind":"native_protocol","reason":"Serialize/readback, permission mode, sync and atomic rename are native publication steps with distinct failure points."}}
```

The lock inode is retained across replacements. Operators must keep the lock file while any command may hold it. Unknown JSON members at the registry, runner, cleanup, ownership, signature and entitlement levels survive unrelated writes as opaque values. Known fields retain their meanings; opaque members supply no ownership observations.

### Install a selected service {install: acts}

```contract
who: ["identity.definitions.controller"]
where: "external bundle validation, signing, registry and launchd"
entry: ["runner_install"]
recipient: ["cli_caller", "launchd"]
report: ["runner_install", "runner_registry"]
uses: ["identity.public.contract"]
free.condition: The caller supplies an existing bundle directory; the kind defaults to byoxpc, and an explicit kind must be byoxpc. Scope defaults to user or may be explicitly system.
free.effect: Resolve the canonical bundle, require CFBundlePackageType XPC!, exact current PWContract, CFBundleIdentifier service identity and an existing Contents/MacOS/CFBundleExecutable. Reject conflicting active/recovery service, bundle or executable identities; verify the source seal and equipment inventory before optional signing.
retained_free: {"condition":{"kind":"raw_admission","reason":"Bundle path existence, supplied/default kind and scope are command inputs before any runner record is installed."},"effect":{"kind":"environment_observation","reason":"Canonical paths, plist metadata, source seal and equipment inventory are read before the installed registry record is published."}}
```

An explicit service name must equal the bundle identifier. `--bundle-id` and `--executable` are refused; those identities come from the bundle. The installer refuses an existing target plist. With `--identity`, it signs the selected worker and host with the supplied entitlements, and the validator/unentitled worker without them, refreshing the sealed equipment inventory before sealing the host. Entitlements with `--allow-adhoc` can select ad-hoc signing; an ad-hoc result requires that flag. Required helpers must exist. The final recursive strict signature verification and reread of bundle identity precede registry installation.

### Retain installation ownership {pending: acts}

```contract
who: ["identity.definitions.controller"]
where: "pending registry save before plist creation and bootstrap"
entry: ["runner_install"]
recipient: ["cli_caller", "launchd"]
report: ["runner_install", "runner_registry"]
free.condition: Bundle verification/signing and readbacks succeeded and the launchd plist has been prepared.
free.effect: Save a pending runner with its plist path, launchd domain, owner UID and plist hash before creating the plist or bootstrapping. Mark installed only after those requested operations and final registry save succeed; retain pending on later failure.
retained_free: {"condition":{"kind":"native_protocol","reason":"Verification/signing/readback completion and prepared plist bytes are ordered preparation events before pending publication."},"effect":{"kind":"native_protocol","reason":"Pending registry persistence precedes external launchd effects; installed publication and retained pending recovery reflect their later outcomes."}}
```

User scope writes HOME/Library/LaunchAgents and targets gui/<uid>, requiring access to that logged-in GUI domain. System scope writes /Library/LaunchDaemons and targets system, requiring the relevant privilege. The plist invokes the recorded executable with `--mach-service` and the service name, advertises that Mach service, sets RunAtLoad and a <!-- span limits.byoxpc_throttle_interval.value_unit -->1 second<!-- /span --> throttle, and defaults XPC_SERVICE_PATH to the bundle. `--env KEY=VALUE` requires a nonempty key; later occurrences replace earlier values. With `--skip-bootstrap`, successful plist creation completes installation; `loaded` remains a separate observation. Signing changes can precede the pending save.

### Verify a selected service {verify: acts}

```contract
who: ["identity.definitions.controller", "identity.definitions.client"]
where: "fixed verification specimen through reservation and execution"
entry: ["runner_verify"]
recipient: ["cli_caller", "runner_host"]
report: ["runner_verify"]
uses: ["installation.verify.select", "installation.verify.delivery_failure", "diagnostics.execution.geometry"]
free.condition: Lookup finds an external runner record.
free.effect: Send the held fixed verification request in a fresh invocation and apply ordinary delivery and reply admission. Under successful admission, copy a supported reply's PID and outcome; an absent reply selects runner_response_unavailable and no PID. A refused boundary selects its admission classification and no PID. The selected verification outcome and independent delivery error determine the operation result below.
retained_free: {"condition":{"kind":"raw_admission","reason":"Registry lookup and external-runner selection precede verification; the selected record must also pass the current contract requirement."},"effect":{"kind":"native_protocol","reason":"Fresh invocation and admission traverse their own byte/capture boundaries; the fixed request and verification-specific result assignments are structured separately."}}
effects: [set_value(request.contract, ref("identity.build.contract")), set_value(request.specimen_id, "runner_verify"), set_value(request.run_kind, "runner_verify"), set_value(request.policy.format, "sbpl"), set_value(request.policy.sbpl_source, "(version 1)\n(allow default)\n"), set_value(request.probe_plan, []), withhold(request.actors), withhold(request.phases), withhold(request._test_overrides)]
```

The timeout defaults to <!-- span limits.runner_verify_wait.value_unit -->5,000 milliseconds<!-- /span --> and is clamped to at least one. An empty successful plan establishes the verification request’s application and completion. It supplies no per-operation prediction or attempt observations.

#### Selected record identity {identity: condition}

```contract
test: runner_record.contract == ref("identity.build.contract")
```

### Pending verification {pending_verify: definition}

```contract
defines: "value"
```

Ordinary specimen selection refuses a Pending installation. Explicit runner verify can address that recorded service after kind and contract checks, using the fixed verification request and retaining the recorded Pending state. Verification leaves the registry bytes unchanged.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: [{"path":"controller/src/runner_commands.rs","symbol":"cmd_runner_verify"},{"path":"tests/suites/runner_byoxpc/opt_in/registry_recovery.py","symbol":"live-pending-verify"}]
pins: "Explicit verification selects by recorded identity and kind/contract, independently of ordinary Pending selection."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/runner_byoxpc/opt_in/registry_recovery.sh","symbol":"registry_recovery","form":"test"}]
limits: "The control uses an owned live current service with a constructed Pending registry state and snapshots the registry around both operations."
```

### Refresh validation metadata {validate: acts}

```contract
who: ["identity.definitions.controller"]
where: "registered bundle and binary signature/inventory reads"
entry: ["runner_validate"]
recipient: ["cli_caller"]
report: ["runner_validate", "runner_registry"]
free.condition: The controller loaded and locked the registry.
free.effect: Visit every record in runners, refresh available per-binary signature/entitlement observations, verify the bundle and equipment inventory, save the registry, and report missing/invalid counts and per-binary failures.
retained_free: {"condition":{"kind":"native_protocol","reason":"Successful registry loading and held advisory lock are native entry observations for validation, not fields of each runner row."},"effect":{"kind":"environment_observation","reason":"Each binary's current signing/entitlement and bundle/equipment observations require fresh inspection before registry/report updates."}}
```

A missing host executable increments `missing`, marks the host signature invalid and records its entitlement error, then skips further verification for that row. A completed validate command reports `result.ok: true` and exit 0 even when missing/invalid is positive; inspect those fields. Pending cleanup records remain recovery records.

### Entitlement read errors and summary counts {entitlement_errors: definition}

```contract
defines: "value"
```

A successful metadata read can retain an entitlement error alongside a valid signature without adding a validation failure. A failed read-back contributes a failure and unreadable signature metadata. Equipment validation applies its own entitlement requirements. The command counts invalid runners after combining the applicable failures; host and validator entitlement metadata errors alone retain their metadata scope.

#### Disposition support {disposition_support: owner}

```contract
grade: "check_read"
source: [{"path":"controller/src/runner_manager.rs","symbol":"validate_record"},{"path":"controller/src/runner_commands.rs","symbol":"cmd_runner_validate"}]
pins: "Read-back failure and entitlement metadata are separate validation results."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"controller/src/runner_manager.rs","symbol":"validation_keeps_entitlement_errors_distinct_from_failed_read_back","form":"test"}]
limits: "The injected seam checks per-role metadata and failure lists. Whole-command invalid-count consequences remain source-read alongside the separate equipment checks."
```

### Reconcile observations {reconcile: acts}

```contract
who: ["identity.definitions.controller"]
where: "registry records, launchctl print and launchd plist directories"
entry: ["runner_reconcile"]
recipient: ["cli_caller"]
report: ["runner_reconcile"]
free.condition: The registry loaded successfully.
free.effect: Report each active and cleanup record with current service/plist observations and separate ownership classifications, and report recognizable unregistered plist candidates plus inspection errors. Leave installation resources and registry records as observed.
retained_free: {"condition":{"kind":"raw_admission","reason":"Registry-load success is an input-reading outcome preceding reconcile inspection, separate from a decoded registry's field values."},"effect":{"kind":"environment_observation","reason":"Active/recovery records and discovered unregistered plist candidates supply distinct filesystem/launchd observations without mutation."}}
```

Candidate discovery scans readable LaunchDaemons and the user LaunchAgents directory. A com.policywitness. label, executable filename PWRunner, or unreadable/unparsed plist with that filename prefix can identify a reporting candidate. Registered label/scope pairs are suppressed from candidates. Discovery establishes a candidate for inspection; cleanup authority requires the recorded identity and the independent ownership gates.

### Remove an owned installation {remove: acts}

```contract
who: ["identity.definitions.controller"]
where: "durable cleanup transaction, launchctl bootout and plist unlink"
entry: ["runner_remove"]
recipient: ["cli_caller", "launchd"]
report: ["runner_remove", "runner_registry"]
free.condition: The requested active record or retained cleanup record exists.
free.effect: Move an active record to nested pending_cleanup and save before any launchd/plist action. Inspect service and plist ownership independently; boot out only an owned service unless skip_bootout, and unlink only an owned plist after an immediate ownership recheck. Retire cleanup only after observed service absence, plist absence, no warnings and successful registry publication.
retained_free: {"condition":{"kind":"raw_admission","reason":"Active or nested recovery lookup applies command selector rules before cleanup ownership is inspected."},"effect":{"kind":"native_protocol","reason":"Durable pending state, immediate ownership recheck, launchd/plist actions and warning-free absence precede recovery retirement."}}
```

After a successful bootout, re-read a still-present service every <!-- span limits.runner_remove_poll_interval.value_unit -->50 milliseconds<!-- /span --> for at most <!-- span limits.runner_remove_teardown_wait.value_unit -->1,000 milliseconds<!-- /span --> of nominal waiting; stop at absence or unknown. Final absence is separately observed. A changed/unreadable/unowned object, failed action or failed retirement publication retains recovery and warnings. A repeated remove continues the retained record from the durable registry, including after the plist has disappeared or the original diagnostic output is gone. `--skip-bootout` can remove an owned plist; retirement still requires observed service absence. A completed remove command reports `result.ok: true` and exit 0 even when cleanup remains retained.

### Classify cleanup ownership {ownership: checks}

```contract
who: ["identity.definitions.controller"]
where: "recorded cleanup location and current resource observations"
entry: ["runner_remove", "runner_reconcile"]
recipient: ["cli_caller"]
report: ["runner_remove", "runner_reconcile"]
free.condition: The recorded service name, user/scope/domain and paths pass location checks.
free.effect: Classify plist ownership from a regular file with matching Label, complete ProgramArguments, MachServices and XPC_SERVICE_PATH; recorded ownership additionally requires matching UID and plist hash.
retained_free: {"condition":{"kind":"raw_admission","reason":"Recorded domain/user/path location rules validate external command targets before any native cleanup action."},"effect":{"kind":"environment_observation","reason":"Complete plist configuration remains a raw JSON value read from the filesystem; service ownership uses the separate typed observation classification."}}
uses: ["installation.service.classify"]
```

Absent resources are classified ambiguous for ownership and retain their independently observed absent presence. Unknown presence produces unknown ownership. Recorded cleanup paths must be absolute, have no parent traversal, end in the expected service plist, and have an immediate parent named LaunchAgents for user scope or LaunchDaemons for system scope. The location check also requires the executable parent to equal the recorded bundle’s Contents/MacOS and refuses symlinked plist ancestors. The recorded ownership supplies the full parent path. Legacy records without ownership derive the conventional plist path and use the content checks.

#### Cleanup location support {disposition_support: owner}

```contract
grade: "source_read"
source: [{"path":"controller/src/runner_manager.rs","symbol":"record_location"},{"path":"controller/src/runner_manager.rs","symbol":"plist_ownership"},{"path":"controller/src/runner_manager.rs","symbol":"service_ownership"}]
pins: "Location and resource ownership checks use the recorded path and complete associated identities."
limits: "Acceptance of a nonconventional full parent is source-supported; this owner supplies no native occurrence for that path."
```

### Retained cleanup example {recovery: example}

If bootout succeeds and plist removal succeeds but the final launchctl read is unknown, the command reports both action booleans true and cleanup_retained true. Keep the recorded bundle and any operator recovery state, inspect reconcile, and repeat removal until service/plist absence and registry retirement are observed.

## Runner registry {registry: subject}

```contract
record: "rust.RunnerRegistry"
as: "registry"
```



### schema_version {schema_version: field}

Supported registry layout version, currently 1.

### runners {runners: field}

Active installation records, including pending installations and installed records.

### pending_cleanup {pending_cleanup: field}

Retained cleanup transactions, including nested runner identity and accumulated observations; empty by default when absent in a historical registry.

## One runner record {runner: subject}

```contract
record: "rust.RunnerRecord"
as: "runner"
```

Recorded signature, entitlement and inventory values describe their named reads; later execution has its own admission and live observations.

### state {state: field}

`pending` means installation ownership was saved before completion; `installed` means the requested installation transaction completed. Missing historical state defaults to installed.

### ownership {ownership: field}

Recorded plist identity and location used by cleanup, or null for a historical record without it.

### id {id: field}

Controller-generated registry identifier for this installation.

### service_name {service_name: field}

Mach service identity selected from the bundle identifier and used for lookup/launchd.

### bundle_path {bundle_path: field}

Canonical bundle location retained at installation.

### executable_path {executable_path: field}

Host executable path derived from the bundle metadata.

### bundle_id {bundle_id: field}

Recorded CFBundleIdentifier, or null in a historical record without it.

### scope {scope: field}

`user` selects the current gui domain; `system` selects the system launchd domain.

### contract {contract: field}

Public identity recorded from the verified bundle. Omitted if empty in a historical record; execution requires exact current identity.

### signature {signature: field}

Host signature observation retained from installation or validation.

### entitlements {entitlements: field}

Host entitlement readback and any read error.

### installed_at_unix_ms {installed_at_unix_ms: field}

Controller wall-clock Unix milliseconds recorded while preparing installation, including a pending transaction.

### kind {kind: field}

Known runner kind when recorded. Historical machme/debuggable deserialize to byoxpc; absent kind can be inferred by the selecting command.

#### Legacy registry support {disposition_support: owner}

```contract
grade: "check_read"
source: [{"path":"controller/src/runner_manager.rs","symbol":"pub enum RunnerKind"},{"path":"controller/src/runner_manager.rs","symbol":"pub fn parse"},{"path":"tests/suites/runner_byoxpc/opt_in/registry_recovery.py","symbol":"historical-after-remove"}]
pins: "Registry normalization and durable cleanup preserve historical records and opaque metadata."
context: "Static review of the cited producer and assertion branches."
check: [{"path":"tests/suites/runner_byoxpc/opt_in/registry_recovery.sh","symbol":"registry_recovery","form":"test"},{"path":"controller/src/runner_manager.rs","symbol":"legacy_machme_kind_deserializes_as_byoxpc","form":"test"},{"path":"controller/src/runner_manager.rs","symbol":"legacy_debuggable_kind_deserializes_as_byoxpc","form":"test"},{"path":"controller/src/runner_manager.rs","symbol":"caller_facing_parse_rejects_legacy_aliases","form":"test"}]
limits: "The live workflow uses a current owned service and a constructed historical debuggable record; both retired aliases have separate offline controls."
```

### worker_signature {worker_signature: field}

Normal-worker signature observation when available; omitted in records without it.

### worker_entitlements {worker_entitlements: field}

Normal-worker entitlement readback when available.

### unentitled_worker_signature {unentitled_worker_signature: field}

Unentitled-worker signature observation when available.

### unentitled_worker_entitlements {unentitled_worker_entitlements: field}

Unentitled-worker entitlement readback when available.

### unentitled_worker_sha256 {unentitled_worker_sha256: field}

Unentitled-worker file hash retained at installation when available.

### worker_equipment_inventory {worker_equipment_inventory: field}

Post-signing sealed equipment snapshot retained as JSON. Current execution separately validates its on-disk inventory and role artifacts.

### source_worker_equipment_inventory {source_worker_equipment_inventory: field}

Verified source equipment snapshot retained before installer signing, as JSON.

### validator_signature {validator_signature: field}

Validator signature observation when available.

### validator_entitlements {validator_entitlements: field}

Validator entitlement readback when available.

### issuer_signature {issuer_signature: field}

Historical extension-issuer signature metadata when available. Current install leaves it absent.

### issuer_entitlements {issuer_entitlements: field}

Historical extension-issuer entitlement metadata when available. Current install leaves it absent.

## Recorded cleanup ownership {ownership: subject}

```contract
record: "rust.RunnerOwnership"
as: "ownership"
```



### plist_path {plist_path: field}

Absolute launchd plist path reserved by installation.

### launchd_domain {launchd_domain: field}

Recorded gui/<uid> or system domain for that scope.

### owner_uid {owner_uid: field}

Installer’s numeric UID, compared with the acting user and observed plist owner for cleanup.

### plist_sha256 {plist_sha256: field}

Hash of the exact generated plist bytes, compared with the current file before cleanup.

## Signature observation {signature: subject}

```contract
record: "rust.RunnerSignature"
as: "signature"
```

Signature facts belong to the recorded file and read time. Preserve unknown members during registry recovery.

### team_id {team_id: field}

TeamIdentifier string read from codesign metadata when available; null when absent.

### identity {identity: field}

First Authority line read from codesign metadata when available; null for unavailable authority.

### cdhash {cdhash: field}

CDHash string read from codesign metadata when available.

### valid {valid: field}

Recorded success of the owning signature-read/verification path. During validation, host validity also requires recursive bundle verification; each helper requires its own binary verification. Failed metadata reads produce false.

### adhoc {adhoc: field}

Whether the read signature metadata identifies ad-hoc signing.

## Entitlement observation {entitlements: subject}

```contract
record: "rust.RunnerEntitlements"
as: "entitlements"
```

An empty keys/granted list with an error describes unavailable parsing. Boolean false, strings and integers do not enter granted.

### raw_plist {raw_plist: field}

Entitlement plist text returned by codesign, or null when none was emitted or the read was unavailable.

### keys {keys: field}

Sorted names of every key in a parsed entitlement dictionary, regardless of value.

### granted {granted: field}

Sorted keys whose values are JSON boolean true after plist conversion. Missing historical granted defaults to an empty list.

### error {error: field}

Command, byte-cap or plist-conversion failure text when readback failed; null for a completed read.

## Retained cleanup transaction {pending_cleanup: subject}

```contract
record: "rust.PendingCleanup"
as: "pending_cleanup"
uses: ["installation.cleanup_observation"]
```

The reader accepts historical flattened cleanup records and writes the nested runner form. Unknown members at each level preserve their own nesting, including runner members named observations or cleanup_started_at_unix_ms.

### runner {runner: field}

Nested retained runner record, including unknown runner/ownership/signature/entitlement members.

### cleanup_started_at_unix_ms {cleanup_started_at_unix_ms: field}

Controller wall-clock Unix milliseconds when the active record entered cleanup.

### observations {observations: field}

Accumulated JSON observations. Current removal appends before/after records when location checks permit inspection; historical entries remain opaque.

## Removal result {cleanup: subject}

```contract
record: "rust.CleanupReport"
as: "cleanup"
```

### runner_id {runner_id: field}

Registry identifier of the cleanup target.

### service_name {service_name: field}

Recorded service name of that target.

### plist_path {plist_path: field}

Resolved cleanup path, recorded ownership path when resolution failed, or empty when neither was available.

### booted_out {booted_out: field}

True only when this removal’s launchctl bootout call succeeded.

### plist_removed {plist_removed: field}

True only when this removal’s unlink call succeeded.

### cleanup_retained {cleanup_retained: field}

True when verified absence/clean completion or publication of retirement was unavailable; continue recovery using the retained record.

### retained_record {retained_record: field}

Recovery snapshot when cleanup remains retained; omitted after retirement.

### warnings {warnings: field}

Diagnostics for refused, failed, uncertain or unpersisted cleanup; omitted when empty.

### Retained recovery account {retention: reports}

```contract
who: ["identity.definitions.controller"]
where: "runner remove result after cleanup publication attempt"
entry: ["runner_remove"]
recipient: ["report_reader"]
report: ["runner_remove"]
```



#### Produced recovery fields {fields: condition}

```contract
test: cleanup.cleanup_retained == present(cleanup.retained_record) and implies(present(cleanup.warnings) and count(cleanup.warnings) > 0, cleanup.cleanup_retained)
```

#### Source support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: {"path":"controller/src/runner_manager.rs","symbol":"remove_record"}
pins: "An incomplete or unpersisted cleanup retains its recovery snapshot; warnings prevent clean retirement."
```

## Installation result {install: subject}

```contract
record: "rust.RunnerInstallData"
as: "install"
```

### state {state: field}

Installed state after the requested transaction and final registry save.

### loaded {loaded: field}

Independent launchctl service observation after installation.

### runner {runner: field}

Complete recorded runner, including signature readbacks, inventories and cleanup ownership.

### plist_path {plist_path: field}

Path where the installer published the launchd plist.

### bootstrapped {bootstrapped: field}

True when this command requested and successfully completed bootstrap; false with skip-bootstrap.

### Published installation state {state_copy: reports}

```contract
who: ["identity.definitions.controller"]
where: "runner install result projection"
entry: ["runner_install"]
recipient: ["report_reader"]
report: ["runner_install"]
effects: set_value(install.state, install.runner.state)
```


#### Source support {support: owner}

```contract
grade: "source_read"
source: {"path":"controller/src/runner_commands.rs","symbol":"cmd_runner_install"}
pins: "RunnerInstallData copies the returned record state."
```

## Verification result {verify: subject}

```contract
record: "rust.RunnerVerifyData"
as: "verify"
uses: ["transport.client"]
```

This is the completion record for a selected registry entry after the client invocation returns its capture. An unmatched lookup uses RunnerNotFoundData with not_found and exit code 2. Earlier argument, registry, setup or invocation failures return without this record.

### runner_client {runner_client: field}

Client subprocess result, capture and delivery admission when available.

### runner_result {runner_result: field}

Decoded host result when available; its presence alone precedes the controller’s full reply admission.

### state {state: field}

Registry installation state read when selecting this verification target.

### runner_id {runner_id: field}

Selected registry identifier when available.

### service_name {service_name: field}

Selected service to which verification was addressed.

### runner_pid {runner_pid: field}

PID projected only from an admitted host result. Its worker/host role follows the host result’s lifecycle.

### normalized_outcome {normalized_outcome: field}

Controller verification classification, also supplied in the envelope result.

### Request delivery failure {delivery_failure: reports}

```contract
who: ["identity.definitions.controller"]
where: "runner verify completion before reply interpretation"
entry: ["runner_verify"]
recipient: ["report_reader"]
report: ["runner_verify"]
when: present(verify.runner_client) and present(verify.runner_client.request_delivery) and present(verify.runner_client.request_delivery.error)
effects: [set_value(result.ok, False), set_value(result.exit_code, 2), set_value(result.normalized_outcome, "tool_error"), set_value(result.error, verify.runner_client.request_delivery.error), set_value(verify.normalized_outcome, "tool_error"), set_value(verify.runner_pid, None), retain_records(verify.runner_client), retain_records(verify.runner_result)]
```


#### Source support {support: owner}

```contract
grade: "source_read"
source: {"path":"controller/src/runner_commands.rs","symbol":"cmd_runner_verify"}
pins: "DeliveryFailed precedes capture/reply interpretation and preserves the returned observations."
```

### Select the verification operation result {select: reports}

```contract
who: ["identity.definitions.controller"]
where: "verification operation result from its selected outcome and delivery observation"
entry: ["runner_verify"]
recipient: ["report_reader"]
report: ["runner_verify"]
selection: "first_match"
```


#### Delivery error has precedence {delivery: outcome}

```contract
test: present(verify.runner_client) and present(verify.runner_client.request_delivery) and present(verify.runner_client.request_delivery.error)
effects: [set_value(result.ok, False), set_value(result.exit_code, 2), set_value(result.normalized_outcome, "tool_error")]
```
#### Selected finished outcome {finished: outcome}

```contract
test: verify.normalized_outcome == "finished"
effects: [set_value(result.ok, True), set_value(result.exit_code, 0), set_value(result.normalized_outcome, verify.normalized_outcome)]
```
#### Other selected outcome {other: outcome}

```contract
test: True
effects: [set_value(result.ok, False), set_value(result.exit_code, 1), set_value(result.normalized_outcome, verify.normalized_outcome)]
```
#### Source support {support: owner}

```contract
grade: "source_read"
source: {"path":"controller/src/runner_commands.rs","symbol":"cmd_runner_verify"}
pins: "The verification result uses delivery failure precedence and the already selected operation outcome; unsupported retained host fields do not supply a PID."
```

## Validation result {validate: subject}

```contract
record: "rust.RunnerValidateData"
as: "validate"
```

### updated {updated: field}

Number of runners visited and saved, including missing/invalid entries.

### missing {missing: field}

Rows whose recorded host executable did not exist; further verification was skipped for those rows.

### invalid {invalid: field}

Other rows with at least one bundle/binary verification, signature-metadata readback or inventory failure.

### failures {failures: field}

Individual failure records, potentially multiple for one invalid runner.

## One validation failure {failure: subject}

```contract
record: "rust.ValidateFailure"
as: "failure"
```

### runner_id {runner_id: field}

Registry identifier of the row that failed this check.

### service_name {service_name: field}

Service name recorded in that row.

### binary {binary: field}

Failed role or check: bundle, host, worker, unentitled_worker, validator, issuer or equipment_inventory as applicable.

### error {error: field}

Failure text from the named verification/readback.

## Unmatched lookup {not_found: subject}

```contract
record: "rust.RunnerNotFoundData"
as: "not_found"
```

### requested_id {requested_id: field}

Supplied ID, omitted when none was supplied.

### requested_service_name {requested_service_name: field}

Supplied service name, omitted when none was supplied.

## Observed service {service: subject}

```contract
record: "rust.ServiceObservation"
as: "service"
```

### presence {presence: field}

`present` for successful launchctl print, `absent` only for its specific missing-service diagnostic naming the requested service, otherwise `unknown`.

### executable_path {executable_path: field}

The unique program = line from a successful launchctl print; null when missing, ambiguous or unavailable.

### error {error: field}

Inspection diagnostic for unknown presence; null for recognized present/absent.

### Service ownership assessment {ownership: definition}

```contract
defines: "assessment"
type: "String"
```

Ownership of this observed service relative to the selected runner_record. Reconciliation and cleanup copy this assessment beside the observation.
### Classify the typed service observation {classify: reports}

```contract
who: ["identity.definitions.controller"]
where: "service observation for the selected runner record after location resolution"
entry: ["runner_reconcile", "runner_remove"]
recipient: ["report_reader"]
report: ["runner_reconcile", "runner_remove"]
selection: "first_match"
uses: ["installation.service.ownership"]
```

A raw reconciliation row containing only unknown presence after location failure has no typed ownership association.
#### Unknown presence {unknown: outcome}

```contract
test: service.presence == "unknown"
effects: set_value(ref("installation.service.ownership"), "unknown")
```
#### Absent service {absent: outcome}

```contract
test: service.presence == "absent"
effects: set_value(ref("installation.service.ownership"), "ambiguous")
```
#### Matching executable {owned: outcome}

```contract
test: service.presence == "present" and present(service.executable_path) and service.executable_path == runner_record.executable_path
effects: set_value(ref("installation.service.ownership"), "owned")
```
#### Different executable {unowned: outcome}

```contract
test: service.presence == "present" and present(service.executable_path)
effects: set_value(ref("installation.service.ownership"), "unowned")
```
#### No usable executable {ambiguous: outcome}

```contract
test: service.presence == "present" and absent(service.executable_path)
effects: set_value(ref("installation.service.ownership"), "ambiguous")
```
#### Source support {support: owner}

```contract
grade: "source_read"
source: {"path":"controller/src/runner_manager.rs","symbol":"service_ownership"}
pins: "The typed presence and observed/recorded executable paths determine service ownership; plist ownership is independent."
```

## Observed plist {plist: subject}

```contract
record: "rust.PlistObservation"
as: "plist"
```

### presence {presence: field}

`absent` for a missing path; `present` for observed metadata, including invalid content; `unknown` for inspection/read failure that prevents a reliable observation.

### config {config: field}

Parsed plist JSON dictionary/value when conversion succeeded; otherwise null.

### sha256 {sha256: field}

Hash of bytes read from the plist when available, including bytes whose plist conversion failed.

### owner_uid {owner_uid: field}

Filesystem owner UID read from symlink metadata when available.

### regular {regular: field}

True when the observed path metadata identifies a regular file; false for another type or unavailable metadata.

### error {error: field}

Metadata, regular-file, read or conversion diagnostic when present; otherwise null.

## Reconciliation result {reconcile: subject}

```contract
record: "RunnerReconcileData"
as: "reconcile"
```

The result reports successful reconciliation execution even when individual inspections remain unknown.

### registry_path {registry_path: field}

```contract
type: "String"
```

Registry path used for this read.

### records {records: field}

```contract
type: "[RunnerReconcileRecord]"
```

Recorded runners and retained cleanup entries, each with current observations or a location error.

### candidates {candidates: field}

```contract
type: "[RunnerReconcileCandidate]"
```

Recognizable unregistered launchd plist candidates from readable directories.

### inspection_errors {inspection_errors: field}

```contract
type: "[RunnerReconcileInspectionError]"
```

Directory, path or plist inspection failures encountered during candidate discovery.

## One recorded reconciliation {reconcile_record: subject}

```contract
record: "RunnerReconcileRecord"
as: "reconcile_record"
uses: ["installation.service", "installation.plist"]
```

### recorded_state {recorded_state: field}

```contract
type: "String"
```

pending, installed or pending_cleanup identifies its registry location/state.

### runner {runner: field}

```contract
type: "rust.RunnerRecord"
```

Recorded runner retained without substituting live observations.

### service {service: field}

```contract
type: "JSON"
```

Full ServiceObservation after valid location resolution; otherwise only {"presence":"unknown"}.

### plist {plist: field}

```contract
type: "JSON"
```

Full PlistObservation after valid location resolution; otherwise only {"presence":"unknown"}.

### plist_path {plist_path: field}

```contract
type: "String"
optional: true
```

Resolved plist location; omitted on location error.

### launchd_domain {launchd_domain: field}

```contract
type: "String"
optional: true
```

Resolved launchd domain; omitted on location error.

### service_ownership {service_ownership: field}

```contract
type: "String"
optional: true
```

Owned, unowned, ambiguous or unknown classification serialized in lowercase; omitted on location error.

### plist_ownership {plist_ownership: field}

```contract
type: "String"
optional: true
```

Independent plist ownership classification; omitted on location error.

### ownership {ownership: field}

```contract
type: "String"
optional: true
```

unknown on location error; omitted after successful location resolution.

### error {error: field}

```contract
type: "String"
optional: true
```

Location-check refusal text; omitted after successful location resolution.

## Unregistered candidate {candidate: subject}

```contract
record: "RunnerReconcileCandidate"
as: "candidate"
```

### recorded_state {recorded_state: field}

```contract
type: "String"
```

unregistered for each candidate.

### scope {scope: field}

```contract
type: "String"
```

user or system according to the directory scanned.

### service_name {service_name: field}

```contract
type: "String"
optional: true
json_null: true
```

Parsed Label, or null if unavailable.

### executable_path {executable_path: field}

```contract
type: "String"
optional: true
json_null: true
```

Parsed ProgramArguments[0], falling back to Program, or null.

### plist_path {plist_path: field}

```contract
type: "String"
```

Candidate path observed during directory enumeration.

### service {service: field}

```contract
type: "rust.ServiceObservation"
optional: true
json_null: true
```

Service observation when label/domain permitted lookup; otherwise null.

### plist {plist: field}

```contract
type: "rust.PlistObservation"
```

Current candidate file observation.

### ownership {ownership: field}

```contract
type: "String"
```

unknown when config is unavailable, ambiguous when label/executable is missing, otherwise unowned.

## Reconciliation inspection error {inspection_error: subject}

```contract
record: "RunnerReconcileInspectionError"
as: "inspection_error"
```

### path {path: field}

```contract
type: "String"
optional: true
```

Directory or plist path involved; omitted when the user LaunchAgents path could not be determined.

### presence {presence: field}

```contract
type: "String"
```

unknown for each inspection error.

### error {error: field}

```contract
type: "String"
```

Inspection or path-resolution error text.

## Current cleanup observation {cleanup_observation: subject}

```contract
record: "RunnerCleanupObservation"
as: "cleanup_observation"
```

This describes the current producer’s appended values within the open observations history.

### phase {phase: field}

```contract
type: "String"
```

before or after identifies its position around attempted actions.

### service {service: field}

```contract
type: "rust.ServiceObservation"
```

Independent service observation at this phase.

### plist {plist: field}

```contract
type: "rust.PlistObservation"
```

Independent plist observation at this phase.

### service_ownership {service_ownership: field}

```contract
type: "String"
optional: true
```

Ownership classification supporting the before decision; omitted after actions.

### plist_ownership {plist_ownership: field}

```contract
type: "String"
optional: true
```

Independent before-action plist ownership classification; omitted after actions.

### teardown_wait {teardown_wait: field}

```contract
type: "RunnerCleanupWait"
optional: true
```

Polling receipt on after records; omitted before actions.

## Service teardown polling {cleanup_wait: subject}

```contract
record: "RunnerCleanupWait"
as: "cleanup_wait"
```

### reads {reads: field}

```contract
type: "UInt64"
```

Number of service observations, including the initial post-action read.

### waited_ms {waited_ms: field}

```contract
type: "UInt64"
```

Sum of nominal requested polling intervals; zero when no wait occurred.

### poll_interval_ms {poll_interval_ms: field}

```contract
type: "UInt64"
```

Current requested polling interval, <!-- span limits.runner_remove_poll_interval.value_unit -->50 milliseconds<!-- /span -->.

### budget_ms {budget_ms: field}

```contract
type: "UInt64"
```

Current nominal waiting bound, <!-- span limits.runner_remove_teardown_wait.value_unit -->1,000 milliseconds<!-- /span -->.

## Dynamic record support {dynamic_support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path": "controller/src/runner_commands.rs", "symbol": "cmd_runner_reconcile"}, {"path": "controller/src/runner_manager.rs", "symbol": "remove_record"}, {"path": "controller/src/runner_manager.rs", "symbol": "service_after_bootout"}]
pins: "The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations."
context: "Read the json! construction sites and their enclosing branches."
limits: "Field-node coverage and source review establish the declared shape; a dedicated independent output mutation control for every dynamic branch remains open."
```
