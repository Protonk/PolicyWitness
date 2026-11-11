# The contract identity {identity: surface}

```contract
syntax: 1
coverage: "public"
artifact: "The contract identity"
part: "identity"
goldens: ["tests/fixtures/contract/surfaces/identity.json", "tests/fixtures/contract/envelope_shape.json"]
checks: ["source_drift", "integration"]
```

PolicyWitness accepts a specimen, runs its declared sandbox experiment and
reports the observations and assessments obtained at each boundary. The
contract identifies the component responsible for each action, the conditions
under which it acts, and the meaning of the resulting records.

## Public identity {public: subject}

### Exact admission identity {contract: definition}

```contract
defines: "value"
type: "String"
```

A public contract identity is the string a build embeds for exact admission.
A specimen carries it in `contract`; controller and compiler-helper envelopes
carry it in `build.contract`; a host reply carries it in `producer.contract`;
a client capture carries its own producer identity. The app and service
property lists carry the build's value as `PWContract`. At an identity-admission
boundary, the receiver compares the arriving identity with its expected identity.
Equality supplies that boundary's identity match. Request validity, wire
structure, equipment association and supported observations have their own
conditions.

### Release and development forms {forms: definition}

```contract
defines: "value"
type: "String"
```

`release:vX.Y.Z` names the sole annotated release tag at the build checkout's
HEAD. The build derives this form when the checkout is clean, the tag matches
`v<digits>.<digits>.<digits>`, and the selected files' actual bytes and inventory
equal that tag's blobs. More than one qualifying annotated tag on a clean
HEAD refuses identity derivation as ambiguous.

`development:<sha256>` identifies the selected source paths and bytes in
other source trees. Its digest is SHA-256 with the domain prefix
`PolicyWitness public build contract` followed by a NUL byte. For each sorted
repository-relative path, the generator appends the UTF-8 path and file bytes,
each preceded by its unsigned eight-byte big-endian length. A dirty release
checkout receives this development form. A documentation-only edit can change
the form from release to development while leaving the selected-source digest
unchanged.

### Selected build inputs {inputs: definition}

```contract
defines: "value"
```

The development digest includes `.rs`, `.c`, `.h`, `.swift`, `.sb`, `.plist`
and `.ent` files discovered under `controller/src`, `controller/tools`,
`runner/Sources`, `runner/Clients`, `runner/Services` and `runner/augments`.
It also includes `build.sh`, `meson.build`, `meson.options`,
`runner/Package.swift`, `controller/Cargo.toml`, `controller/Cargo.lock`,
`controller/build.rs`, `Info.plist`, `PolicyWitness.entitlements`,
`docs/build_contract.py`, `docs/source_identity.py`,
`tests/build_equipment.py`, `tests/build-evidence.py`, and the build helpers
`tests/lib/build_provenance.py`, `signer_check.py`, `cargo_config.py`,
`checkout_lock.py` and `output_target.py` in that same directory.

Discovery uses the same inventory in a checkout and a source copy. Missing
declared inputs, symlinks under the selected roots and nonregular source
objects refuse derivation. The digest's equality concerns those paths and
bytes; build configuration, signing identity, SDK and observed runtime
behavior are recorded and checked by their respective operations.

### Build derivation {derive: acts}

```contract
who: "build.sh and build_contract.py"
where: "packaged-build identity derivation"
entry: ["packaged_build"]
recipient: ["build_operator", "compiled_component"]
report: ["build_context"]
uses: ["identity.public.forms", "identity.public.inputs"]
free.effect: Derive the public identity from the selected source tree, embed it in compiled producers and property lists, and refuse signing if recomputation after compilation yields a different identity.
```

The packaged build computes the identity itself and passes that value into
its Rust and Swift producers. Swift context generation recomputes it and
refuses a supplied `PW_BUILD_CONTRACT` that differs. The pre-sign comparison
refuses a selected-source change during compilation.

#### Derivation support {support: owner}

```contract
grade: "check_read"
source: [{"path":"docs/build_contract.py","symbol":"identity"},{"path":"docs/source_identity.py","symbol":"source_paths"},{"path":"build.sh","symbol":"CURRENT_BUILD_CONTRACT="}]
check: [{"path":"tests/suites/source_drift/build_contracts.py","symbol":"test_build_identity_tracks_shipped_inputs_and_requires_an_annotated_clean_release","form":"test"},{"path":"tests/suites/source_drift/build_contracts.py","symbol":"test_source_copies_ignore_artifacts_and_release_checks_actual_bytes","form":"test"},{"path":"tests/suites/source_drift/build_contracts.py","symbol":"test_swift_context_refuses_a_different_compilation_identity","form":"test"},{"path":"tests/suites/source_drift/build_contracts.py","symbol":"test_presign_contract_guard_refuses_changed_sources","form":"test"}]
pins: "Selected-source mutations change the digest; clean annotated release selection checks actual bytes; Swift context disagreement and the extracted pre-sign guard refuse."
context: "Read generator/source walker and build-stamp/pre-sign code; read tests using disposable source copies and Git repositories, including execution of the extracted shell guard."
limits: "Checks were read, not run for this draft. The guard control executes a script fragment, not a full signing pipeline; multiple qualifying annotated tags are source-established here."
```

### Direct compilation contexts {direct: definition}

```contract
defines: "value"
```

The Rust controller and compiler helper embed a nonempty compile-time
`PW_BUILD_CONTRACT` verbatim. An absent or empty value becomes `unbound`.
Ordinary SwiftPM compilation uses `unbound`; its explicitly selected unit-test
context uses `test:policy-witness`. Rust unit tests likewise use
`test:policy-witness`. A request cannot pass the controller's identity gate
when its expected identity is empty or `unbound`.

#### Direct-build evidence limit {direct_evidence: gap}

```contract
kind: "evidence"
```

The direct Rust environment path is established by the compile-time constant
and Cargo's environment tracking. The available plain-Cargo integration check
removes `PW_BUILD_CONTRACT` and establishes the unbound case. A direct Cargo
build with an explicitly supplied foreign or release-form identity has not
been exercised in this examination.

#### Direct-build support {support: owner}

```contract
grade: "check_read"
source: [{"path":"controller/src/json_contract.rs","symbol":"BUILD_CONTRACT"},{"path":"controller/build.rs","symbol":"cargo:rerun-if-env-changed"},{"path":"runner/Sources/PWRunnerCore/PWRunnerAPI.swift","symbol":"PW_UNIT_TEST_CONTEXT"},{"path":"controller/src/request_patch.rs","symbol":"validate_contract"}]
check: [{"path":"controller/integration/cli_contract.rs","symbol":"plain_cargo_build_cannot_admit_public_requests","form":"test"},{"path":"controller/src/request_patch.rs","symbol":"request_contract_is_exact_and_required","form":"test"}]
pins: "Absent build binding reports unbound and refuses a matching unbound request; decoded request identity matching is exact and distinguishes missing, null, mistyped and foreign values."
context: "Read compile-time constants and Cargo environment tracking; read integration and constructed request tests."
limits: "No compilation or test execution credited here; the plain-Cargo check covers an unset environment, not the supplied-value path."
```

## Surface history {surfaces: subject}

### Surface and stamp {stamp: definition}

```contract
defines: "value"
```

A surface groups a named part of the public contract and its canonical shape
inputs. Its stamp records the last reachable annotated release at which those
declared inputs changed. A pending change is `unreleased` until a release is
prepared. A removed surface retains a removal row. The table directs review
to changed definitions; admission uses the exact public identity carried by
the request or record.

An unchanged stamp establishes equality of the inputs used by that stamp
derivation. A changed implementation can require review even when its prose
and shape inputs have remained unchanged. Reasserting a saved specimen for a
different build remains an explicit choice about the target's commitments.

### Deriving the history table {derive: reports}

```contract
who: "contract stamp generator"
where: "contract history derivation"
entry: ["documentation_generation"]
recipient: ["developer"]
report: ["surface_table"]
uses: ["identity.surfaces.stamp"]
free.effect: Walk reachable annotated release tags in ancestry order, retain each surface's last changed stamp and removal state, and mark changed current inputs unreleased or with the explicitly prepared release.
```

History derivation compares a surface with its prior declared inputs. The
history reader for a released layout supplies that layout's own definition
and shape framing. Source copies lacking annotated history can check current
inputs and agreement of carried tables; their result explicitly leaves the
historical last-change derivation unverified.

#### Surface-history support {support: owner}

```contract
grade: "check_read"
source: [{"path":"docs/contract/runtime.py","symbol":"release_tags"},{"path":"docs/contract/runtime.py","symbol":"stamps"},{"path":"docs/contract/runtime.py","symbol":"require_available_history"},{"path":"docs/contract/runtime.py","symbol":"check"}]
check: [{"path":"tests/suites/source_drift/build_contracts.py","symbol":"test_pending_release_reproduces_after_tagging_and_tracks_removal","form":"test"},{"path":"tests/suites/source_drift/build_contracts.py","symbol":"test_stamped_source_copy_and_no_tags_clone_validate_without_erasing_stamps","form":"test"}]
pins: "Prepared stamps reproduce after tagging; changed declared text moves its surface; removal remains recorded; history-free checks retain a narrower result."
context: "Read the authored-tree runtime, both retained history readers and disposable release-tree controls."
limits: "Check reading; these controls exercise document/history derivation and input changes, with product behavior supported at its own boundaries."
```

### Source copies and release preparation {source_history: definition}

Ordinary checks without annotated history verify current authored content,
canonical shapes, the public snapshot and agreement of both carried stamp
tables. They report the historical last-change derivation as unverified.
Ordinary regeneration and explicit release preparation require every release
claimed by the carried tables and public snapshot; missing history refuses
before writing generated outputs. Released snapshots retain their historical
dependencies even when every surface has since changed.

### Ordinary-build history requirement {release_history: gap}

```contract
kind: "behavior"
```

An ordinary build accepts the narrower source-copy check. Requiring complete
release history for that build would change which source distributions can
build; the requirement remains a maintainer decision. Strict release
preflight requires complete history.

### Development specimen review {development_review: gap}

```contract
kind: "meaning"
```

A development identity names a source digest, while the table is indexed by
releases. The current reuse procedure leaves the comparison baseline for a
development-asserting specimen unspecified. Exact admission still uses the
target identity; the development-to-release review workflow needs a stated
baseline or an explicit review of the relevant target definitions.

## Other identities {other: subject}

### Wire-schema fingerprint {wire: definition}

```contract
defines: "value"
```

The typed response frame carries a SHA-256 fingerprint of its wire schema.
Its selected schema representation includes record IDs/names, field tags,
names and encoded types, optional and null representation, projections,
variants and roots. The receiver checks this fingerprint before decoding the
producer context for public identity admission. A matching fingerprint
establishes the selected wire-schema match; the public producer identity is
then checked separately.

### Worker protocol identity {worker: definition}

```contract
defines: "value"
```

The host/worker protocol identity is a SHA-256 digest, carried as raw bytes or
lowercase hexadecimal using the fixed widths below. It covers sorted C/header/Swift inputs
under `controller/tools/pw_probe_runner` and `runner/Sources`, together with
`docs/generate_worker_identity.py`, `docs/source_identity.py`, `build.sh`,
`meson.build`, `meson.options` and `runner/Package.swift`. Its domain prefix is
`PolicyWitness host/worker source identity` followed by NUL; path and contents
use the same unsigned eight-byte big-endian length framing. Generated identity
region bodies are excluded while their boundary markers remain inputs.

The worker compares its embedded value and bootstrap magic with the host's
shared header before reading the remaining protocol state. A mapping failure
returns worker exit 3; a mapped header mismatch returns exit 4. Host decoding
of `worker_evidence` also requires a matching header. A reported `abi_identity` identifies
the protocol sources selected by the host; establishing the executing binary's
association uses the equipment and launch evidence.

### SHA-256 digest length {sha256_bytes: definition}

```contract
defines: "value"
type: "Int"
value: 32
```

Fixed byte length of SHA-256 digests used for the schema fingerprint, worker
identity and signed-file hashes.

### SHA-256 hexadecimal width {sha256_hex: definition}

```contract
defines: "value"
type: "Int"
value: 64
uses: ["identity.other.sha256_bytes"]
```

Character length of their lowercase hexadecimal representation.

### CodeDirectory hash byte width {cdhash_bytes: definition}

```contract
defines: "value"
type: "Int"
value: 20
```

Fixed byte length of the CodeDirectory hashes admitted from equipment
inventory and code inspection.

### CodeDirectory hexadecimal width {cdhash_hex: definition}

```contract
defines: "value"
type: "Int"
value: 40
uses: ["identity.other.cdhash_bytes"]
```

Character length of their lowercase hexadecimal representation.

### Identity distinctions support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path":"docs/generate_porcelain.py","symbol":"wire_identity"},{"path":"controller/src/porcelain.rs","symbol":"decode_bound"},{"path":"docs/generate_worker_identity.py","symbol":"identity"},{"path":"controller/tools/pw_probe_runner/pw_probe_runner.c","symbol":"ABI identity mismatch"},{"path":"runner/Sources/PWRunnerCore/CWorker.swift","symbol":"workerIdentityMatches"},{"path":"runner/Sources/PWRunnerCore/ActorEquipment.swift","symbol":"struct ActorEquipmentManifest"},{"path":"runner/Sources/PWRunnerCore/ActorEquipment.swift","symbol":"guard cdhash.count == 20"}]
pins: "Wire fingerprint precedes producer admission; worker digest scope/framing and fixed-header mismatch have separate producers and checks."
context: "Read schema identity construction, Rust bound frame decoder, worker identity generator, C bootstrap branch and Swift evidence header check."
limits: "Source reading only. This owner does not credit old-worker execution, every host header-read site, signature association or wire correctness. Those need their respective boundary owners."
```

## Shared definitions {definitions: subject}

```contract
part: "definitions"
```

### PolicyWitness {policywitness: definition}

```contract
defines: "component"
```

PolicyWitness, abbreviated PW, is the controller, runner client, runner host,
native worker, query validator and compiler helper distributed together. The
controller exposes specimen execution, runner management and version reporting.

### Controller {controller: definition}

```contract
defines: "component"
```

`policy-witness` reads and prepares the request, selects equipment, invokes the
runner client, admits its records and emits the outer JSON envelope. Its
dossier and assessments are controller observations and interpretations.

### Runner client {client: definition}

```contract
defines: "component"
```

The runner client acquires a reservation, submits the held request over XPC
and returns a typed capture of its transport observations and received host
bytes. The controller invokes it once for a run.

### Runner host {host: definition}

```contract
defines: "component"
```

The XPC host admits the request, prepares worker resources, coordinates query
collection and action release, collects worker/validator observations and
produces the host reply. Specimen policy application occurs in the worker so
the host retains its reply path.

### Worker {worker: definition}

```contract
defines: "component"
```

The native worker receives policy input and its own action plan, applies the
declared sandbox when requested, executes released actions and publishes
bounded observations in host-provided regions. The ordinary form uses one
fresh worker; the actor form assigns a fresh worker to each actor it launches.

### Validator {validator: definition}

```contract
defines: "component"
```

The native `sb_api_validator` issues `sandbox_check` queries about the selected
worker process and returns query records to the host. Each query describes
an operation and filter; the attempt later performs its separately specified
native operation.

### Compiler helper {helper: definition}

```contract
defines: "component"
```

`sbpl-check` reads policy input, inventories imports and calls the native
compiler. Its compiler result is reported in its own envelope. The standalone
helper and the controller's fallback invocation have separately stated input
and invocation conditions.

### Specimen {specimen: definition}

```contract
defines: "record"
```

A specimen is the declared experiment: its identifier, asserted contract,
policy or actor policies, ordered phases/actions, and accepted execution
options. A saved specimen is its JSON representation in a request file.

### Request {request: definition}

```contract
defines: "record"
```

A request is the value presented at an entry boundary. The controller holds
the parsed request, resolves controller-owned options and sends a serialization
of the resulting value. Submitted bytes and original file bytes are distinct
artifacts; each byte observation names the artifact it covers.

### Reply {reply: definition}

```contract
defines: "record"
```

A host reply is the host-produced execution record, including its producer
identity, execution summary and available observations. The typed host frame
carries this record across XPC. Raw retained bytes and an admitted decoded
reply have different availability and interpretation conditions.

### Capture {capture: definition}

```contract
defines: "record"
```

A client capture records reservation attempts, invocation knowledge, transport
results and host reply bytes as observed by the client. A received host frame
inside an admitted capture has its own producer admission.

### Envelope {envelope: definition}

```contract
defines: "record"
```

An envelope is the outer JSON record emitted by the controller or compiler
helper: `kind`, generation time, build identification, result and data. Its
result describes the emitting operation; contained query, attempt and child
results retain their own meanings.

### Actor {actor: definition}

```contract
defines: "record"
```

An actor names a declared worker role, sandbox setup and its visits to the
schedule. Actor identity is the request's identifier and associated owned
process evidence. A numeric PID records one observation of that association.

### Phase {phase: definition}

```contract
defines: "record"
```

A phase groups an ordered batch of actions under one worker or actor visit.
The host's query collection precedes release of the phase's action batch
under the ordering rules. Phase completion and individual action completion
are separate observations.

### Probe {probe: definition}

```contract
defines: "record"
```

A probe pairs a declared sandbox query with a declared native attempt and
assigns them a step ID. Query operation/filter and attempt kind/action/target
are separate submitted operands, whose relationships the comparison records.

### Prediction {prediction: definition}

```contract
defines: "assessment"
```

A prediction is the usable result of a native sandbox query for the reported
worker, operation and filter at collection time. Excluded queries, diagnostics
and missing validator results carry their own unavailable/error observations.
`query_first` establishes a supported ordering interval before an action
batch; changes of state inside that interval remain possible.

### Observation {observation: definition}

```contract
defines: "record"
```

An observation records what a named component read, returned, published or
reaped at a particular boundary. Its result, origin, subject and available
timing determine its evidentiary scope. A missing publication leaves the
operation's result unresolved even when progress indicates that it began.

### Effect {effect: definition}

```contract
defines: "event"
```

An effect is an observable consequence of an operation, such as creation of a
file, truncation, bytes read or written, or spawning a child. Each effect claim
is bounded by its concrete observation: descriptor metadata, content/transfer
result, child PID or independent state observation. An `open_write` success
reports its truncating open; the worker discards the following write's return.
The meaning of a successful status is specific to that operation.

### Cause {cause: definition}

```contract
defines: "assessment"
```

A cause identifies why an event occurred. Permission-shaped return values
support the `permission_failure` observation class; they leave sandbox cause
unresolved. A termination request and a later owned reap support the specific
lifecycle relationship stated by the lifecycle assessment. Query answers and
attempt returns retain their individual observation scopes.

### Assessment {assessment: definition}

```contract
defines: "assessment"
```

An assessment is a conclusion computed from named observations and declared
relations, such as query order, operation/target relation, application state
or process disposition. Its applicability and supporting observations belong
to that assessment. Raw observation retention and permission to use an
assessment are separately reported consequences of a failed check.

### Absent field {absent: definition}

```contract
defines: "value"
```

A field is absent when its key is omitted from the JSON object. The field's
definition determines whether omission selects a default, means unavailable
information, makes the object inapplicable or refuses the input.

### Null value {null_value: definition}

```contract
defines: "value"
```

`null` is an explicitly carried JSON value. Its equivalence to omission is a
field-specific rule. In output, a null observation leaves the represented
fact unavailable unless that field defines a more specific meaning.

### Optional field {optional: definition}

```contract
defines: "value"
```

An optional field permits the absence specified by its record definition.
Conditional presence, explicit null and omitted serialization each retain
their own stated conditions.

### Unknown fact {unknown: definition}

```contract
defines: "value"
```

Unknown means the available record leaves a factual question unresolved.
Missing process status, absent completed result and unavailable provenance
therefore preserve the corresponding uncertainty. An explicit observation of
absence, such as an owned service confirmed absent, has its own evidence.

### Byte observation {bytes: definition}

```contract
defines: "value"
```

A byte field identifies its byte source, encoding, total/retained length and
bound where applicable. Hexadecimal and base64 are representations of bytes;
decoded diagnostic text is a separate projection. UTF-8 byte counts and
character counts use the units named by each capacity.

### Closed object {closed_object: definition}

```contract
defines: "value"
```

A closed input object accepts its listed keys; an unknown key is refused at
the boundary enforcing that object. Map keys, such as policy parameter names,
are values in their declared domain and have their own constraints.

### Open value vocabulary {open_values: definition}

```contract
defines: "value"
```

An open vocabulary admits values beyond the displayed list. Its field
definition states how unfamiliar values are retained or classified. Whether
the displayed list is exhaustive is recorded separately from admission.

### Closed value vocabulary {closed_values: definition}

```contract
defines: "value"
```

A closed vocabulary admits the specified set of values. The rule names the
component and boundary that identifies another value as invalid, and states
the consequence for retained records and supported assessments.

### Definition grounding {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path":"controller/src/main.rs","symbol":"fn main"},{"path":"controller/src/run_flow.rs","symbol":"fn run(args:"},{"path":"controller/src/runner_client.rs","symbol":"RunnerClientRun"},{"path":"runner/Sources/PWRunnerCore/PWRunnerService.swift","symbol":"PWRunnerService"},{"path":"runner/Sources/PWRunnerCore/PWRunnerRequest.swift","symbol":"PWRunnerRunSpec"},{"path":"runner/Sources/PWRunnerCore/CWorkerComparison.swift","symbol":"comparisonEvidence"},{"path":"controller/tools/pw_probe_runner/pw_probe_runner.c","symbol":"attempt_file_open_write"},{"path":"controller/tools/sb_api_validator/sb_api_validator.c","symbol":"SANDBOX_CHECK_NO_REPORT"},{"path":"runner/Sources/PWRunnerCore/PWRunnerAPI.swift","symbol":"AttemptOutcome"},{"path":"controller/src/json_contract.rs","symbol":"Envelope"}]
pins: "Names the actual components and record relationships; comparison source distinguishes native prediction, published attempt status, permission-shaped failures and operation/target relations."
context: "Read component entry/declaration code, held-request normalization/serialization/client invocation, controller capture record, request forms, validator batch native call, comparison implementation, old file-open operation and envelope serializer. Definitions provide shared terminology; operational predicates remain owned by their surfaces."
limits: "Source reading is narrower than a complete lifecycle, native-effect or attribution experiment. Field presence and value admission must be supplied by each owning rule; these definitions do not establish every instance."
```

## Build identification {build: subject}

```contract
record: "rust.BuildStamp"
as: "build_stamp"
```

Every controller and compiler-helper envelope carries these string fields
under `build`. They identify the emitting binary's compiled context.

### Contract {contract: field}

```contract
uses: ["identity.public.contract", "identity.public.forms", "identity.public.direct"]
```

The public identity embedded in the emitting binary. Receiving boundaries use
the exact value according to their identity-admission rule.

### Version {version: field}

The packaged build's version string. `build.sh` uses nonempty `PW_VERSION`
when supplied; otherwise it takes the leading three-part version from its
Git describe value, falling back to `0.0.0`. Direct Rust compilation reads
`PW_BUILD_VERSION`, falling back to `unknown` when absent.

### Number {number: field}

The build-number string. `build.sh` uses nonempty `PW_BUILD_NUMBER` when
supplied, otherwise the Git commit count, falling back to `0`. Direct Rust
compilation reads `PW_BUILD_NUMBER`, falling back to `unknown` when absent.

### Describe {describe: field}

The descriptive source coordinate compiled into the producer. `build.sh`
uses `git describe --tags --match 'v[0-9]*' --always --dirty`, falling back
to `unknown`. Direct Rust compilation reads `PW_BUILD_DESCRIBE` with an absent
value falling back to `unknown`.

### Commit {commit: field}

The Git HEAD object name observed by the packaged build, or `unknown` when
unavailable. Direct Rust compilation reads `PW_BUILD_COMMIT` with an absent
value falling back to `unknown`. Describe and commit report provenance;
identity admission compares the contract field.

### Build-field support {support: owner}

```contract
scope: "subtree"
grade: "check_read"
source: [{"path":"controller/src/json_contract.rs","symbol":"build_stamp"},{"path":"build.sh","symbol":"# ---- Build stamp"},{"path":"build.sh","symbol":"stamp_info_plist"}]
check: [{"path":"controller/src/json_contract.rs","symbol":"every_envelope_carries_a_complete_build_stamp","form":"test"},{"path":"controller/src/json_contract.rs","symbol":"public_identity_is_in_the_build_frame","form":"test"},{"path":"controller/integration/cli_contract.rs","symbol":"version_flag_reports_build_stamp_and_contract","form":"test"}]
pins: "Envelope build fields are strings, contract is embedded, and the version command's reported contract matches the independently read candidate plist."
context: "Read build shell derivation and shared Rust serializer; read unit checks and integration command/plist assertions."
limits: "No check execution in this draft. Integration expects populated packaged provenance; override and missing-Git fallback branches are supported by source reading."
```

## Host producer identification {producer: subject}

```contract
record: "PWProducer"
as: "producer"
```

The host's typed reply carries this producer record. Each field comes from the
host's compiled build context.

### Contract {contract: field}

```contract
uses: ["identity.public.contract", "identity.public.forms", "identity.public.direct"]
```

The host's public identity, independently compared by a receiver before the
reply's execution records supply interpretations.

### Describe {describe: field}

```contract
uses: ["identity.build.describe"]
```

The host build's descriptive Git coordinate, or `unknown` in the ordinary
unbound Swift build context. Packaged context generation supplies the observed
build description.

### Commit {commit: field}

```contract
uses: ["identity.build.commit"]
```

The host build's observed Git HEAD object name, or `unknown` when the compiled
context has no such observation. Identity admission uses `contract`; this field
retains the host's provenance.

### Producer-field support {support: owner}

```contract
scope: "subtree"
grade: "source_read"
source: [{"path":"runner/Sources/PWRunnerCore/PWRunnerAPI.swift","symbol":"PWProducer"},{"path":"docs/build_contract.py","symbol":"swift"},{"path":"controller/src/porcelain.rs","symbol":"decode_bound"}]
pins: "PWProducer.current copies the compiled contract/describe/commit context; bound reply decoding compares producer.contract before decoding descendants."
context: "Read the complete producer declaration/current constructor, generated Swift context producer, ordinary fallback context and Rust bound-frame path."
limits: "Source reading only; component signing, live peer association and a fresh packaged producer run require their respective evidence."
```

## Version reporting {version: subject}

```contract
part: "version"
record: "VersionData"
as: "version_data"
```

### Reported identity {contract: field}

```contract
type: "String"
uses: ["identity.public.contract"]
```

The controller's public identity, also carried in the same envelope's
`build.contract`.

### Version command {emit: reports}

```contract
who: "policy-witness controller"
where: "CLI version dispatch"
entry: ["cli"]
recipient: ["cli_caller"]
report: ["version"]
uses: ["identity.definitions.envelope", "identity.build.contract"]
free.condition: The first command argument is --version or version.
effects: [set_value(version_data.contract, ref("identity.build.contract"))]
free.effect: Emit a kind version envelope with result.ok true, result.exit_code 0, other result fields null and the current build context; return process exit 0 after successful rendering, or 2 when envelope rendering returns an error.
```

Version dispatch reports the compiled context without loading a specimen or
starting the runner client. `generated_at_unix_ms` is the producer's current
wall-clock time in milliseconds since the Unix epoch; the shared serializer
uses zero if its system time precedes that epoch.

#### Version command support {support: owner}

```contract
grade: "check_read"
source: [{"path":"controller/src/cli.rs","symbol":"pub fn run"},{"path":"controller/src/json_contract.rs","symbol":"JsonResult"},{"path":"controller/src/json_contract.rs","symbol":"now_unix_ms"}]
check: {"path":"controller/integration/cli_contract.rs","symbol":"version_flag_reports_build_stamp_and_contract","form":"test"}
pins: "--version succeeds, emits kind version and result.ok true, supplies populated packaged build fields, and reports candidate-plist identity in data and build."
context: "Read dispatch and serializer branches; read integration test invoking the selected controller binary and independently extracting its app plist identity."
limits: "Check read without execution. Alias version, trailing arguments, exact null result fields and rendering-error exit are source-established here; the cited check exercises --version success."
```

### Trailing version arguments {arguments: gap}

```contract
kind: "behavior"
```

Current dispatch selects version reporting from the first argument and ignores
remaining arguments. The intended argument-count commitment is unresolved;
the source establishes this acceptance, while the version check exercises the
single-argument form.
