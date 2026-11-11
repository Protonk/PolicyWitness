# Managing runners {installation: surface}

```contract
syntax: 1
artifact: "Managing runners"
part: "installation"
goldens: ["tests/fixtures/contract/surfaces/installation.json"]
checks: ["unit", "runner_byoxpc"]
```

The controller manages external XPC services through a local registry and launchd. Registry state, on-disk signature observations, live service presence and a completed verification specimen establish different facts. Recovery ownership remains recorded until cleanup observes service and plist absence and publishes that retirement.

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
who: "controller"
where: "runner registry lookup"
entry: ["runner_list", "runner_status", "runner_verify", "runner_remove", "runner_reconcile"]
recipient: ["cli_caller"]
report: ["runner_registry", "runner_status", "runner_verify", "runner_remove", "runner_reconcile"]
free.condition: The registry is readable with schema_version 1, or its path is absent.
free.effect: Use PW_RUNNER_REGISTRY when nonempty, otherwise HOME/Library/Application Support/PolicyWitness/runners.json. An absent file yields empty runners and pending_cleanup. For selector commands, prefer a supplied id and otherwise use service_name; an unmatched id remains a miss.
```

`runner list` returns the registry as `kind: "runner_registry"`. `runner status` returns the selected active record as `kind: "runner_status"`. Status and verify search `runners`; removal also resumes `pending_cleanup`. A miss returns that operation’s envelope kind, `result.normalized_outcome: "not_found"`, false `ok` and exit code 2. Unsupported registry schemas and malformed known fields refuse loading. Read-only commands can read the prior or replacement complete registry while a modifier holds its lock.

### Publish a registry mutation {publish: acts}

```contract
who: "controller"
where: "install, validate and remove registry transaction"
entry: ["runner_install", "runner_validate", "runner_remove"]
recipient: ["cli_caller"]
report: ["runner_registry"]
free.condition: The command holds the stable sibling registry lock across its mutation and associated launchd actions.
free.effect: Serialize and read back the proposed registry, require lossless reserialization, write and sync a new mode-0600 file in the same directory, then atomically rename it over the registry. Refuse a busy/unavailable advisory lock or a readback that loses metadata.
```

The lock inode is retained across replacements. Operators must keep the lock file while any command may hold it. Unknown JSON members at the registry, runner, cleanup, ownership, signature and entitlement levels survive unrelated writes as opaque values. Known fields retain their meanings; opaque members supply no ownership observations.

### Install a selected service {install: acts}

```contract
who: "controller installer"
where: "external bundle validation, signing, registry and launchd"
entry: ["runner_install"]
recipient: ["cli_caller", "launchd"]
report: ["runner_install", "runner_registry"]
uses: ["identity.public.contract"]
free.condition: The caller supplies an existing bundle directory; the kind defaults to byoxpc, and an explicit kind must be byoxpc. Scope defaults to user or may be explicitly system.
free.effect: Resolve the canonical bundle, require CFBundlePackageType XPC!, exact current PWContract, CFBundleIdentifier service identity and an existing Contents/MacOS/CFBundleExecutable. Reject conflicting active/recovery service, bundle or executable identities; verify the source seal and equipment inventory before optional signing.
```

An explicit service name must equal the bundle identifier. `--bundle-id` and `--executable` are refused; those identities come from the bundle. The installer refuses an existing target plist. With `--identity`, it signs the selected worker and host with the supplied entitlements, and the validator/unentitled worker without them, refreshing the sealed equipment inventory before sealing the host. Entitlements with `--allow-adhoc` can select ad-hoc signing; an ad-hoc result requires that flag. Required helpers must exist. The final recursive strict signature verification and reread of bundle identity precede registry installation.

### Retain installation ownership {pending: acts}

```contract
who: "controller installer"
where: "pending registry save before plist creation and bootstrap"
entry: ["runner_install"]
recipient: ["cli_caller", "launchd"]
report: ["runner_install", "runner_registry"]
free.condition: Bundle verification/signing and readbacks succeeded and the launchd plist has been prepared.
free.effect: Save a pending runner with its plist path, launchd domain, owner UID and plist hash before creating the plist or bootstrapping. Mark installed only after those requested operations and final registry save succeed; retain pending on later failure.
```

User scope writes HOME/Library/LaunchAgents and targets gui/<uid>, requiring access to that logged-in GUI domain. System scope writes /Library/LaunchDaemons and targets system, requiring the relevant privilege. The plist invokes the recorded executable with `--mach-service` and the service name, advertises that Mach service, sets RunAtLoad and a <!-- span limits.byoxpc_throttle_interval.value_unit -->1 second<!-- /span --> throttle, and defaults XPC_SERVICE_PATH to the bundle. `--env KEY=VALUE` requires a nonempty key; later occurrences replace earlier values. With `--skip-bootstrap`, successful plist creation completes installation; `loaded` remains a separate observation. Signing changes can precede the pending save.

### Verify a selected service {verify: acts}

```contract
who: "controller and runner client"
where: "fixed verification specimen through reservation and execution"
entry: ["runner_verify"]
recipient: ["cli_caller", "runner_host"]
report: ["runner_verify"]
uses: ["transport.delivery", "identity.public.contract"]
free.condition: Lookup finds an external runner record whose contract matches the current public identity.
free.effect: Send a fresh fixed SBPL allow-all request with specimen_id runner_verify, run_kind runner_verify and an empty probe plan. Apply ordinary delivery and reply admission. Return exit 0 for an admitted finished result, exit 1 for other admitted/refused outcomes, and exit 2 for request-delivery failure.
```

The timeout defaults to <!-- span limits.runner_verify_wait.value_unit -->5,000 milliseconds<!-- /span --> and is clamped to at least one. The returned PID comes from an admitted host reply’s `pid`; read its subject according to that reply’s lifecycle. An empty successful plan establishes the verification request’s application and completion. It supplies no per-operation prediction or attempt observations.

### Pending verification {pending_verify: gap}

```contract
kind: "behavior"
```

Ordinary specimen selection refuses a pending installation. `runner verify` currently looks up the same pending record, checks its kind and contract, and can invoke it. Whether verification should share the pending-state gate remains unresolved; the existing pending-selection recovery control does not establish that decision.

### Refresh validation metadata {validate: acts}

```contract
who: "controller"
where: "registered bundle and binary signature/inventory reads"
entry: ["runner_validate"]
recipient: ["cli_caller"]
report: ["runner_validate", "runner_registry"]
free.condition: The controller loaded and locked the registry.
free.effect: Visit every record in runners, refresh available per-binary signature/entitlement observations, verify the bundle and equipment inventory, save the registry, and report missing/invalid counts and per-binary failures.
```

A missing host executable increments `missing`, marks the host signature invalid and records its entitlement error, then skips further verification for that row. Bundle/binary verification, signature-metadata readback and equipment-inventory failures increment `invalid` once per affected row and retain each named failure. Entitlement read errors also remain in their individual metadata objects. `updated` counts every visited runner. A completed validate command reports `result.ok: true` and exit 0 even when missing/invalid is positive; inspect those fields. Pending cleanup records remain recovery records.

### Entitlement read errors and summary counts {entitlement_errors: gap}

```contract
kind: "behavior"
```

An entitlement-read error can coexist with successful signature readback and an empty validation failures list. Equipment-inventory verification independently checks current worker entitlements; host and validator entitlement errors alone remain in their metadata. Whether the validation summary should count every such read error remains unresolved.

### Reconcile observations {reconcile: acts}

```contract
who: "controller"
where: "registry records, launchctl print and launchd plist directories"
entry: ["runner_reconcile"]
recipient: ["cli_caller"]
report: ["runner_reconcile"]
free.condition: The registry loaded successfully.
free.effect: Report each active and cleanup record with current service/plist observations and separate ownership classifications, and report recognizable unregistered plist candidates plus inspection errors. Leave installation resources and registry records as observed.
```

Candidate discovery scans readable LaunchDaemons and the user LaunchAgents directory. A com.policywitness. label, executable filename PWRunner, or unreadable/unparsed plist with that filename prefix can identify a reporting candidate. Registered label/scope pairs are suppressed from candidates. Discovery establishes a candidate for inspection; cleanup authority requires the recorded identity and the independent ownership gates.

### Remove an owned installation {remove: acts}

```contract
who: "controller"
where: "durable cleanup transaction, launchctl bootout and plist unlink"
entry: ["runner_remove"]
recipient: ["cli_caller", "launchd"]
report: ["runner_remove", "runner_registry"]
free.condition: The requested active record or retained cleanup record exists.
free.effect: Move an active record to nested pending_cleanup and save before any launchd/plist action. Inspect service and plist ownership independently; boot out only an owned service unless skip_bootout, and unlink only an owned plist after an immediate ownership recheck. Retire cleanup only after observed service absence, plist absence, no warnings and successful registry publication.
```

After a successful bootout, re-read a still-present service every <!-- span limits.runner_remove_poll_interval.value_unit -->50 milliseconds<!-- /span --> for at most <!-- span limits.runner_remove_teardown_wait.value_unit -->1,000 milliseconds<!-- /span --> of nominal waiting; stop at absence or unknown. A bootout or unlink success records that call’s success. Final absence is separately observed. A changed/unreadable/unowned object, failed action or failed retirement publication retains recovery and warnings. A repeated remove continues the retained record, including after the plist has disappeared. `--skip-bootout` can remove an owned plist; retirement still requires observed service absence. A completed remove command reports `result.ok: true` and exit 0 even when cleanup remains retained.

### Classify cleanup ownership {ownership: checks}

```contract
who: ["identity.definitions.controller"]
where: "recorded cleanup location and current resource observations"
entry: ["runner_remove", "runner_reconcile"]
recipient: ["cli_caller"]
report: ["runner_remove", "runner_reconcile"]
free.condition: The recorded service name, user/scope/domain and paths pass location checks.
free.effect: Classify service ownership from present service executable equality. Classify plist ownership from a regular file with matching Label, complete ProgramArguments, MachServices and XPC_SERVICE_PATH; recorded ownership additionally requires matching UID and plist hash.
```

A present service with a different executable is unowned; one with no unique executable observation is ambiguous. Absent resources are classified ambiguous for ownership and retain their independently observed absent presence. Unknown presence produces unknown ownership. Recorded cleanup paths must be absolute, have no parent traversal, end in the expected service plist, and have an immediate parent named LaunchAgents for user scope or LaunchDaemons for system scope. The location check also requires the executable parent to equal the recorded bundle’s Contents/MacOS and refuses symlinked plist ancestors. The recorded ownership supplies the full parent path. Legacy records without ownership derive the conventional plist path and use the content checks.

### Recorded cleanup directory {ownership_location: gap}

```contract
kind: "behavior"
```

Recorded ownership can select an absolute directory whose last component matches the scope name. Whether cleanup should also compare the entire parent path with the conventional scope directory remains unresolved.

### Retained cleanup example {recovery: example}

If bootout succeeds and plist removal succeeds but the final launchctl read is unknown, the command reports both action booleans true and cleanup_retained true. Keep the recorded bundle and any operator recovery state, inspect reconcile, and repeat removal until service/plist absence and registry retirement are observed.

### Legacy values and evidence {legacy: gap}

```contract
kind: "evidence"
```

Offline controls cover preservation of unknown nested JSON and historical cleanup forms. The complete live install/list/reconcile/remove sequence carrying unusual opaque metadata remains an evidence obligation. Legacy `machme` and `debuggable` kinds normalize to byoxpc on registry load while new CLI input rejects those aliases. That deliberate compatibility behavior and the pending-verification distinction need to stay visible during review.

## Runner registry {registry: subject}

```contract
record: "rust.RunnerRegistry"
as: "registry"
```

Unknown JSON members are retained opaquely through writes. New registries start with both collections empty.

### schema_version {schema_version: field}

Supported registry layout version, currently 1. Another value refuses loading.

### runners {runners: field}

Active installation records, including pending installations and installed records.

### pending_cleanup {pending_cleanup: field}

Retained cleanup transactions, including nested runner identity and accumulated observations; empty by default when absent in a historical registry.

## One runner record {runner: subject}

```contract
record: "rust.RunnerRecord"
as: "runner"
```

Unknown JSON members survive unrelated writes. Recorded signature, entitlement and inventory values describe their named reads; later execution has its own admission and live observations.

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

Additional members remain opaque. These values combine with current service/plist observations and location checks at cleanup.

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

An empty keys/granted list with an error describes unavailable parsing. Boolean false, strings and integers do not enter granted. Additional members remain opaque.

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

## Verification result {verify: subject}

```contract
record: "rust.RunnerVerifyData"
as: "verify"
uses: ["transport.client"]
```

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

Other rows with at least one bundle/binary verification, signature-metadata readback or inventory failure. Entitlement error fields retain their separate observations.

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

Supplied ID, omitted when none was supplied. A supplied unmatched ID takes precedence over service_name.

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

This command’s data shape is authored from its JSON producer. The result reports successful reconciliation execution even when individual inspections remain unknown.

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

This describes the current producer’s appended values within the open observations history. Recovery retains older observation shapes opaquely.

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
