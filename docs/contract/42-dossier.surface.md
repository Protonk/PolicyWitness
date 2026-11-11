# Specimen dossier {dossier: surface}

```contract
syntax: 1
artifact: "Specimen dossier"
part: "assessment"
goldens: ["tests/fixtures/contract/surfaces/dossier.json"]
checks: ["unit", "witness_contract"]
```

The controller carries `data.specimen` on every `kind: "run"` envelope. Its policy hashes identify the held parsed source selected for delivery; its import records identify controller file reads; its runner and binary records describe selection and on-disk observations made before invocation. Native compilation, application and execution have their own reports.

## Implementation and evidence {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path": "controller/src/dossier.rs", "symbol": "Specimen"}, {"path": "controller/src/dossier.rs", "symbol": "Imports"}, {"path": "controller/src/dossier.rs", "symbol": "Binaries"}, {"path": "controller/src/run_flow.rs", "symbol": "load_app_provenance"}, {"path": "controller/src/sbpl_imports.rs", "symbol": "resolve_imports"}, {"path": "controller/src/sbpl_imports.rs", "symbol": "compute_closure_hash"}, {"path": "controller/src/runner_select.rs", "symbol": "RunnerProvenance"}, {"path": "controller/src/evidence.rs", "symbol": "verify_manifest"}, {"path": "controller/src/run_flow.rs", "symbol": "fn run("}, {"path": "controller/src/run_flow.rs", "symbol": "actor_fallback_checks"}]
check: [{"path": "controller/src/dossier.rs", "symbol": "augmentation_records_hash_only_bytes_that_existed", "form": "test"}, {"path": "controller/src/dossier.rs", "symbol": "import_scan_statuses_never_report_an_unscanned_closure_as_complete", "form": "test"}, {"path": "controller/src/dossier.rs", "symbol": "builtin_run_hashes_nothing_and_reports_null_records", "form": "test"}, {"path": "controller/src/dossier.rs", "symbol": "byoxpc_copies_are_compared_with_the_shipped_baselines", "form": "test"}, {"path": "controller/src/sbpl_imports.rs", "symbol": "closure_hash_excludes_unresolved_imports", "form": "test"}, {"path": "controller/src/sbpl_imports.rs", "symbol": "closure_hash_is_order_invariant", "form": "test"}]
pins: "Declarations and collection branches establish field provenance, augmentation states, literal import closure and role-specific comparisons. Unit controls assert unavailable/partial states and comparisons against synthetic manifest baselines."
context: "Read the cited producer/receiver declarations and branches; check citations identify the assertions read."
limits: "These read controls establish controller calculations and selected-file comparisons. A signed run with a changed request file, native compiler import parity and contemporaneous executing-image identity need separate observations."
```

## Collection boundaries {collection: subject}

### Hold the selected request {held: acts}

```contract
who: "controller"
where: "request preparation before runner-client invocation and fallback compile"
entry: ["run"]
recipient: ["cli_caller", "runner_client", "sandbox_compile_helper"]
report: ["specimen_dossier"]
uses: ["identity.definitions.request", "identity.definitions.bytes"]
free.condition: A request has been parsed and controller policy changes have been resolved in memory.
free.effect: Serialize the held selected request once and use those bytes for client delivery and whole-request fallback compilation. Derive source hashes from its decoded UTF-8 sbpl_source string and retain the dossier even when later preparation or invocation fails.
```

The original path is a locator. JSON whitespace, escape spelling and subsequent edits to that file have no role in the held source hash. Actor fallback checks serialize the held resolved policy objects separately in request order. A later helper import scan can observe different import-file bytes because those files are independently opened. Actor-form dossiers retain request order; malformed identity/mode fields become null and policy availability remains distinct from admission.

### Scan literal imports {scan: acts}

```contract
who: "controller import scanner"
where: "selected policy source and local import files before invocation"
entry: ["run"]
recipient: ["cli_caller"]
report: ["specimen_dossier"]
free.condition: The selected policy has string source within the <!-- span limits.helper_source.binary -->4 MiB<!-- /span --> source bound.
free.effect: Scan literal import forms, resolve absolute names as given and relative names under /System/Library/Sandbox/Profiles then /usr/share/sandbox, and record observed reads within depth 8 and count 64. Mark unresolved names, nonliteral forms, cycles, decoding failures and bound hits as incomplete.
```

Names retain their spelling, including a `.sb` suffix when supplied. Resolution deduplicates canonical paths and unresolved names. A file is opened once with nonblocking open, checked as regular through that descriptor, and read for both hashing and recursive scanning. Records sort by resolved path, then unresolved name. The closure hash is SHA-256 of selected source UTF-8 bytes, byte `0x1f`, then sorted `resolved_path + " " + sha256` lines joined with LF for records having both values. This identifies the scanned material even when the scan is incomplete.

### Compare selected files {compare: acts}

```contract
who: "controller"
where: "selected runner/helper paths and embedded evidence manifest"
entry: ["run"]
recipient: ["cli_caller"]
report: ["specimen_dossier"]
free.condition: Runner selection supplies paths and the app evidence manifest supplies role baselines where available.
free.effect: For a shipped path already described by its unique typed manifest entry, emit a null binary record. For another selected file, attempt its hash and compare it with the role baseline; retain independent availability and error facts. After a dossier-only collection failure or hash mismatch, continue preparation and invocation subject to the separate selection and admission results.
```

A role baseline must be the unique entry at the expected path and kind with a 64-digit hexadecimal SHA-256. `match` means selected on-disk bytes matched that baseline at this read. A null role record refers to the shipped manifest description; ordinary collection does not rehash that shipped file. Worker/validator override strings must be absolute to be read; NUL-containing or over-<!-- span limits.test_override_path.value -->1,023<!-- /span -->-byte overrides are neither echoed nor opened. Optional `PW_VERIFY_EVIDENCE=1` separately hashes the manifest entries carrying declared hashes.

### Held-file example {held_example: example}

If a caller changes the input JSON after the controller has parsed it, the client and fallback compiler still receive the controller’s held serialization. An import file changed between dossier collection and fallback compilation may produce different import observations. Compare the source hash and the separately reported closures at their named boundaries.

### Import and execution evidence {native_gap: gap}

```contract
kind: "evidence"
```

The scanner’s `complete` status exhausts its literal import search. Its search order follows the recorded platform convention; collision precedence and parity with native compilation remain unverified. A signed held-request change experiment and independent observations tying selected-file hashes to executing images remain open.

## Run dossier {specimen: subject}

```contract
record: "rust.Specimen"
as: "specimen"
uses: ["identity.definitions.specimen"]
```

### request_path {request_path: field}

Request-file path reported by the controller when available; null when preparation did not establish one.

### policy {policy: field}

Legacy-form policy dossier. In actor form, the actor entries carry their policy observations and this slot is not applicable.

### host {host: field}

Controller-collected operating-system context; each failed sysctl read remains null.

### runner_provenance {runner_provenance: field}

Selected runner metadata when selection succeeded; null when no target was established. These facts precede invocation.

### app_provenance {app_provenance: field}

Parsed app evidence-manifest provenance when available; null when its read or supported-schema parse failed.

### binaries {binaries: field}

Role-by-role selected-file observations; the meaning of a null role is defined beside that role.

### actors {actors: field}

Actor-form policy dossiers in request order; omitted for the legacy form.

## Actor policy dossier {actor: subject}

```contract
record: "rust.ActorDossier"
as: "actor"
```

### actor_id {actor_id: field}

Actor identifier copied if the request value is a string; otherwise null. This copy precedes actor admission.

### mode {mode: field}

Actor mode copied if it is a string; otherwise null. Unapplied actors receive a not-applicable policy dossier.

### policy {policy: field}

Policy augmentation and import observations for this actor. Missing or malformed policy objects produce not-applicable observations.

## Policy dossier {policy: subject}

```contract
record: "rust.PolicyDossier"
as: "policy"
```

### augmentation {augmentation: field}

Controller policy-selection outcome and hashes of source strings that existed at that boundary.

### imports {imports: field}

Literal import observations for the source selected for invocation, or the reason that scan was unavailable.

## Augmentation observation {augmentation: subject}

```contract
record: "rust.Augmentation"
as: "augmentation"
```

### status {status: field}

`not_requested` retains unchanged source hashes; `applied` records selected augmentation output; `failed` records refusal; `not_applicable` identifies a policy slot with no applicable source preparation.

### applied {applied: field}

Applied augmentation names in controller order. Empty for not_requested, failed and not_applicable.

### original_sha256 {original_sha256: field}

SHA-256 of pre-augmentation source string UTF-8 bytes when such a string existed; otherwise null.

### applied_sha256 {applied_sha256: field}

SHA-256 of the selected source string, including unchanged source for not_requested. Null for failed/not_applicable and when no source string existed.

### error {error: field}

Augmentation failure text for failed; otherwise null.

## Import scan {imports: subject}

```contract
record: "rust.Imports"
as: "imports"
```

### status {status: field}

`complete` exhausted the literal closure without a reported problem; `incomplete` retained a partial/problematic scan; `failed` could not perform the scan; `not_applicable` skipped it because source preparation did not apply.

### closure_sha256 {closure_sha256: field}

Digest of the selected source plus successfully read import path/hash pairs using the defined framing. Present for complete and incomplete scans; null for failed/not_applicable.

### records {records: field}

Sorted observed import records, including unresolved and failed reads. Empty when there were no imports or no scan.

### cycle {cycle: field}

First detected cycle as an ordered name chain; null when no cycle was observed.

### exceeded {exceeded: field}

First reached traversal bound, `depth` or `count`; null when neither was recorded.

### failure {failure: field}

First collection problem, scan setup failure or reason for a not-applicable scan; null when none was recorded.

## One import observation {import_record: subject}

```contract
record: "rust.ImportRecord"
as: "import_record"
```

### name {name: field}

Literal import name found in source, retained for successful resolution and unresolved-name diagnostics.

### resolved_path {resolved_path: field}

Resolved path when lookup established one; null for an unresolved name.

### sha256 {sha256: field}

SHA-256 of bytes read from the opened regular file; null when that read failed or never occurred.

### size_bytes {size_bytes: field}

File size reported by metadata on the opened descriptor, when available. The hash identifies the bytes actually read.

### mtime_unix {mtime_unix: field}

Opened file’s available modification time in Unix seconds; null on unavailable conversion/read.

### error {error: field}

Resolution, regular-file, read, text-decoding or traversal diagnostic for this entry; null when the entry was collected without such a problem.

## Controller host context {host: subject}

```contract
record: "rust.HostFacts"
as: "host"
```

### macos_version {macos_version: field}

String read from kern.osproductversion, or null when unavailable.

### macos_build {macos_build: field}

String read from kern.osversion, or null when unavailable.

### kernel_release {kernel_release: field}

String read from kern.osrelease, or null when unavailable.

### arch {arch: field}

String read from hw.machine, or null when unavailable. This is the controller host’s hardware context.

## App provenance {app: subject}

```contract
record: "rust.AppProvenance"
as: "app"
```

### evidence_manifest_path {evidence_manifest_path: field}

Path to the parsed embedded evidence manifest used by this run’s controller.

### evidence_verify {evidence_verify: field}

Manifest-declared hash verification when PW_VERIFY_EVIDENCE is exactly `1`; otherwise null.

## Selected binary observations {binaries: subject}

```contract
record: "rust.Binaries"
as: "binaries"
```

A null role records use of its shipped manifest description. If selection or a manifest baseline is unavailable, the controller emits an unavailable record with the facts it could retain. Actor equipment selection has its own records.

### service {service: field}

Selected host executable comparison when it needs an individual record. Null when the shipped service is described by the manifest.

### worker {worker: field}

Selected normal worker comparison, including an admitted observable override path. Null when the shipped worker is described by the manifest.

### validator {validator: field}

Selected validator comparison, including an admitted observable override path. Null when the shipped validator is described by the manifest.

### unentitled_worker {unentitled_worker: field}

Selected unentitled-worker comparison. Null when the shipped role is described by the manifest.

## One selected binary {binary: subject}

```contract
record: "rust.BinaryRecord"
as: "binary"
```

### path {path: field}

Selected path when the controller may retain it; null when selection or safe override projection was unavailable.

### actual_sha256 {actual_sha256: field}

Hash of selected on-disk bytes successfully read; retained independently of baseline availability.

### baseline_sha256 {baseline_sha256: field}

Normalized SHA-256 from the shipped app manifest’s unique typed role entry; null if that baseline is unavailable.

### verification {verification: field}

`match` or `mismatch` compares the two available hashes. `unavailable` means the controller could not establish that comparison.

### reason {reason: field}

Diagnostic explaining mismatch or unavailability; null for match.

## Selected runner provenance {runner: subject}

```contract
record: "rust.RunnerProvenance"
as: "runner"
uses: ["installation.signature", "installation.entitlements"]
```

### runner_kind {runner_kind: field}

Selected connection kind, standard or byoxpc.

### runner_registry_id {runner_registry_id: field}

Registry ID for a selected external runner; null for a built-in target.

### runner_service_name {runner_service_name: field}

Selected XPC service name to which the controller intends to connect.

### runner_bundle_id {runner_bundle_id: field}

Selected bundle identity when available.

### runner_bundle_path {runner_bundle_path: field}

Selected bundle path when available; this is selection metadata.

### runner_executable_path {runner_executable_path: field}

Selected host executable path when available.

### runner_signature {runner_signature: field}

Recorded external-host signature readback; null when no such metadata is supplied.

### runner_entitlements {runner_entitlements: field}

Selected host entitlement metadata from the external registry or shipped evidence manifest when available.

### runner_worker_signature {runner_worker_signature: field}

Recorded normal-worker signature readback for the selected target when available.

### runner_worker_entitlements {runner_worker_entitlements: field}

Recorded normal-worker entitlement metadata when available.

### runner_validator_signature {runner_validator_signature: field}

Recorded validator signature readback when available.

### runner_validator_entitlements {runner_validator_entitlements: field}

Recorded validator entitlement metadata when available.

### runner_unentitled_worker_signature {runner_unentitled_worker_signature: field}

Recorded unentitled-worker signature readback when available.

### runner_unentitled_worker_entitlements {runner_unentitled_worker_entitlements: field}

Recorded unentitled-worker entitlement metadata when available.

## Manifest hash verification {verification: subject}

```contract
record: "rust.VerifyReport"
as: "verification"
```

Entries without declared hashes are outside this calculation’s checked count. Each comparison concerns a file read under the app root.

### ok {ok: field}

True when every checked manifest entry was readable and matched its declared hash; false when mismatches contains an entry.

### checked {checked: field}

Number of manifest entries carrying a declared hash and considered by verification, including missing/unreadable files.

### mismatches {mismatches: field}

Entries whose file was missing, unreadable or had different bytes.

### manifest_path {manifest_path: field}

Manifest path attached to this verification.

### schema_version {schema_version: field}

Schema version read from the supported manifest.

### notes {notes: field}

Notes carried by that manifest, or null when absent.

## One verification failure {mismatch: subject}

```contract
record: "rust.VerifyMismatch"
as: "mismatch"
```

### id {id: field}

Manifest entry identifier for the failed comparison.

### rel_path {rel_path: field}

Manifest-relative file path attempted under the app root.

### expected_sha256 {expected_sha256: field}

Declared expected hash retained for this failure.

### actual_sha256 {actual_sha256: field}

Hash actually read when available; null for missing/unreadable files.

### error {error: field}

Missing-file or read-error text when bytes were unavailable; null for a completed read whose actual hash differs from expected.
