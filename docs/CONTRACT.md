<!-- BEGIN GENERATED PUBLIC CONTRACT -->
# PolicyWitness contract

<a id="contract-identity"></a>
## The contract identity

PolicyWitness accepts a specimen, runs its declared sandbox experiment and
reports the observations and assessments obtained at each boundary. The
contract identifies the component responsible for each action, the conditions
under which it acts, and the meaning of the resulting records.

<a id="contract-identity-public"></a>
### Public identity

<a id="contract-identity-public-contract"></a>
#### Exact admission identity

A public contract identity is the string a build embeds for exact admission.
A specimen carries it in `contract`; controller and compiler-helper envelopes
carry it in `build.contract`; a host reply carries it in `producer.contract`;
a client capture carries its own producer identity. The app and service
property lists carry the build's value as `PWContract`. At an identity-admission
boundary, the receiver compares the arriving identity with its expected identity.
Equality supplies that boundary's identity match. Request validity, wire
structure, equipment association and supported observations have their own
conditions.

<a id="contract-identity-public-forms"></a>
#### Release and development forms

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

<a id="contract-identity-public-inputs"></a>
#### Selected build inputs

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

<a id="contract-identity-public-derive"></a>
#### Build derivation

[Build pipeline](#contract-identity-definitions-build_pipeline) acts at packaged-build identity derivation. Entry: packaged build. Recipient: build operator, compiled component. Reports: build context. Uses [Release and development forms](#contract-identity-public-forms), [Selected build inputs](#contract-identity-public-inputs). Derive the public identity from the selected source tree, embed it in compiled producers and property lists, and refuse signing if recomputation after compilation yields a different identity.

The packaged build computes the identity itself and passes that value into
its Rust and Swift producers. Swift context generation recomputes it and
refuses a supplied `PW_BUILD_CONTRACT` that differs. The pre-sign comparison
refuses a selected-source change during compilation.

**Support: [check read](#contract-support-grades) for [Build derivation](#contract-identity-public-derive).** Selected-source mutations change the digest; clean annotated release selection checks actual bytes; Swift context disagreement and the extracted pre-sign guard refuse. Context: Read generator/source walker and build-stamp/pre-sign code; read tests using disposable source copies and Git repositories, including execution of the extracted shell guard. Evidence limit: The guard control executes the pre-sign script fragment. The multiple-qualifying-tag branch has source support. Source: [build_contract.py](../docs/build_contract.py): `identity`; [source_identity.py](../docs/source_identity.py): `source_paths`; [build.sh](../build.sh): `CURRENT_BUILD_CONTRACT=`. Check: [build_contracts.py](../tests/suites/source_drift/build_contracts.py): `test_build_identity_tracks_shipped_inputs_and_requires_an_annotated_clean_release`, `test_source_copies_ignore_artifacts_and_release_checks_actual_bytes`, `test_swift_context_refuses_a_different_compilation_identity`, `test_presign_contract_guard_refuses_changed_sources`.

<a id="contract-identity-public-direct"></a>
#### Direct compilation contexts

The Rust controller and compiler helper embed a nonempty compile-time
`PW_BUILD_CONTRACT` verbatim. An absent or empty value becomes `unbound`.
A supplied `PW_BUILD_CONTRACT` spelling can be foreign or release-shaped;
build version, number, commit and describe retain their separately supplied
provenance. Ordinary SwiftPM compilation uses `unbound`; its explicitly
selected unit-test context uses `test:policy-witness`. Rust unit tests
likewise use `test:policy-witness`. A request cannot pass the controller's
identity gate when its expected identity is empty or `unbound`.

**Support: [check read](#contract-support-grades) for [Direct compilation contexts](#contract-identity-public-direct).** The non-test constant, Cargo environment tracking and receiver equality gate have separate roles. Context: Static review of the cited producer and assertion branches. Evidence limit: The control builds an isolated non-test controller with supplied and absent stamp values, then checks identity and the next refusing controller boundary. Source: [json_contract.rs](../controller/src/json_contract.rs): `BUILD_CONTRACT`; [build.rs](../controller/build.rs): `fn main`; [request_patch.rs](../controller/src/request_patch.rs): `validate_contract`. Check: [cli_contract.rs](../controller/integration/cli_contract.rs): `supplied_direct_cargo_identity_is_embedded_without_release_provenance`.

**Support: [check read](#contract-support-grades) for [Direct compilation contexts](#contract-identity-public-direct).** Absent build binding reports unbound and refuses a matching unbound request; decoded request identity matching is exact and distinguishes missing, null, mistyped and foreign values. Context: Read compile-time constants and Cargo environment tracking; read integration and constructed request tests. Evidence limit: No compilation or test execution credited here; the plain-Cargo check covers an unset environment, not the supplied-value path. Source: [json_contract.rs](../controller/src/json_contract.rs): `BUILD_CONTRACT`; [build.rs](../controller/build.rs): `cargo:rerun-if-env-changed`; [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift): `PW_UNIT_TEST_CONTEXT`; [request_patch.rs](../controller/src/request_patch.rs): `validate_contract`. Check: [cli_contract.rs](../controller/integration/cli_contract.rs): `plain_cargo_build_cannot_admit_public_requests`; [request_patch.rs](../controller/src/request_patch.rs): `request_contract_is_exact_and_required`.

<a id="contract-identity-surfaces"></a>
### Surface history

<a id="contract-identity-surfaces-stamp"></a>
#### Surface and stamp

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

<a id="contract-identity-surfaces-derive"></a>
#### Deriving the history table

[Contract generator](#contract-identity-definitions-contract_generator) reports at contract history derivation. Entry: documentation generation. Recipient: developer. Reports: surface table. Uses [Surface and stamp](#contract-identity-surfaces-stamp). Walk reachable annotated release tags in ancestry order, retain each surface's last changed stamp and removal state, and mark changed current inputs unreleased or with the explicitly prepared release.

History derivation compares a surface with its prior declared inputs. The
history reader for a released layout supplies that layout's own definition
and shape framing.

**Support: [check read](#contract-support-grades) for [Deriving the history table](#contract-identity-surfaces-derive).** Prepared stamps reproduce after tagging; changed declared text moves its surface; removal remains recorded; history-free checks retain a narrower result. Context: Read the authored-tree runtime, both retained history readers and disposable release-tree controls. Evidence limit: Check reading; these controls exercise document/history derivation and input changes, with product behavior supported at its own boundaries. Source: [runtime.py](../docs/contract/runtime.py): `release_tags`, `stamps`, `require_available_history`, `check`. Check: [build_contracts.py](../tests/suites/source_drift/build_contracts.py): `test_pending_release_reproduces_after_tagging_and_tracks_removal`, `test_stamped_source_copy_and_no_tags_clone_validate_without_erasing_stamps`.

<a id="contract-identity-surfaces-source_history"></a>
#### Source copies and release preparation

Ordinary checks without annotated history verify current authored content,
canonical shapes, the public snapshot and agreement of both carried stamp
tables. They report the historical last-change derivation as unverified.
Ordinary regeneration and explicit release preparation require every release
claimed by the carried tables and public snapshot; missing history refuses
before writing generated outputs. Released snapshots retain their historical
dependencies even when every surface has since changed.

<a id="contract-identity-surfaces-release_history"></a>
#### Known gap: Ordinary-build history requirement

An ordinary build accepts the narrower source-copy check. Requiring complete
release history for that build would change which source distributions can
build; the requirement remains a maintainer decision. Strict release
preflight requires complete history.

<a id="contract-identity-surfaces-development_review"></a>
#### Reviewing a development specimen

Review a development-asserting specimen against its original source and contract snapshot when those are available. Record the old assertion, target identity and commitments compared. When the old snapshot is unavailable, review the relevant target definitions and chosen validation against the specimen explicitly. Set the target assertion after that review.

**Support: [source read](#contract-support-grades) for [Reviewing a development specimen](#contract-identity-surfaces-development_review).** The development identity hashes selected source paths and bytes; release identity selection uses release-tag and byte checks. Evidence limit: The source establishes identity construction. The specimen review procedure is the stated reuse obligation. Source: [build_contract.py](../docs/build_contract.py): `def identity`.

<a id="contract-identity-other"></a>
### Other identities

<a id="contract-identity-other-wire"></a>
#### Wire-schema fingerprint

The typed response frame carries a SHA-256 fingerprint of its wire schema.
Its selected schema representation includes record IDs/names, field tags,
names and encoded types, optional and null representation, projections,
variants and roots. The receiver checks this fingerprint before decoding the
producer context for public identity admission. A matching fingerprint
establishes the selected wire-schema match; the public producer identity is
then checked separately.

<a id="contract-identity-other-worker"></a>
#### Worker protocol identity

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

<a id="contract-identity-other-sha256_bytes"></a>
#### SHA-256 digest length

Value: `32`.

Fixed byte length of SHA-256 digests used for the schema fingerprint, worker
identity and signed-file hashes.

<a id="contract-identity-other-sha256_hex"></a>
#### SHA-256 hexadecimal width

Uses [SHA-256 digest length](#contract-identity-other-sha256_bytes). Value: `64`.

Character length of their lowercase hexadecimal representation.

<a id="contract-identity-other-cdhash_bytes"></a>
#### CodeDirectory hash byte width

Value: `20`.

Fixed byte length of the CodeDirectory hashes admitted from equipment
inventory and code inspection.

<a id="contract-identity-other-cdhash_hex"></a>
#### CodeDirectory hexadecimal width

Uses [CodeDirectory hash byte width](#contract-identity-other-cdhash_bytes). Value: `40`.

Character length of their lowercase hexadecimal representation.

**Support: [source read](#contract-support-grades) for [Other identities](#contract-identity-other) and its descendants.** Wire fingerprint precedes producer admission; worker digest scope/framing and fixed-header mismatch have separate producers and checks. Context: Read schema identity construction, Rust bound frame decoder, worker identity generator, C bootstrap branch and Swift evidence header check. Evidence limit: Source reading only. This owner does not credit old-worker execution, every host header-read site, signature association or wire correctness. Those need their respective boundary owners. Source: [generate_porcelain.py](../docs/generate_porcelain.py): `wire_identity`; [porcelain.rs](../controller/src/porcelain.rs): `decode_bound`; [generate_worker_identity.py](../docs/generate_worker_identity.py): `identity`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `ABI identity mismatch`; [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `workerIdentityMatches`; [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `struct ActorEquipmentManifest`, `guard cdhash.count == 20`.

<a id="contract-identity-build"></a>
### Build identification

Record `build_stamp`: `rust.BuildStamp`.

Every controller and compiler-helper envelope carries these string fields
under `build`. They identify the emitting binary's compiled context.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-identity-build-contract"></a>`contract` | string; required | The public identity embedded in the emitting binary. Receiving boundaries use the exact value according to their identity-admission rule. Uses [Exact admission identity](#contract-identity-public-contract), [Release and development forms](#contract-identity-public-forms), [Direct compilation contexts](#contract-identity-public-direct). |
| <a id="contract-identity-build-version"></a>`version` | string; required | The packaged build's version string. `build.sh` uses nonempty `PW_VERSION` when supplied; otherwise it takes the leading three-part version from its Git describe value, falling back to `0.0.0`. Direct Rust compilation reads `PW_BUILD_VERSION`, falling back to `unknown` when absent. |
| <a id="contract-identity-build-number"></a>`number` | string; required | The build-number string. `build.sh` uses nonempty `PW_BUILD_NUMBER` when supplied, otherwise the Git commit count, falling back to `0`. Direct Rust compilation reads `PW_BUILD_NUMBER`, falling back to `unknown` when absent. |
| <a id="contract-identity-build-describe"></a>`describe` | string; required | The descriptive source coordinate compiled into the producer. `build.sh` uses `git describe --tags --match 'v[0-9]*' --always --dirty`, falling back to `unknown`. Direct Rust compilation reads `PW_BUILD_DESCRIBE` with an absent value falling back to `unknown`. |
| <a id="contract-identity-build-commit"></a>`commit` | string; required | The Git HEAD object name observed by the packaged build, or `unknown` when unavailable. Direct Rust compilation reads `PW_BUILD_COMMIT` with an absent value falling back to `unknown`. Describe and commit report provenance; identity admission compares the contract field. |

**Support: [check read](#contract-support-grades) for [Build identification](#contract-identity-build) and its descendants.** Envelope build fields are strings, contract is embedded, and the version command's reported contract matches the independently read candidate plist. Context: Read build shell derivation and shared Rust serializer; read unit checks and integration command/plist assertions. Evidence limit: Integration checks populated packaged provenance; override and missing-Git fallback branches have source support. Source: [json_contract.rs](../controller/src/json_contract.rs): `build_stamp`; [build.sh](../build.sh): `# ---- Build stamp`, `stamp_info_plist`. Check: [json_contract.rs](../controller/src/json_contract.rs): `every_envelope_carries_a_complete_build_stamp`, `public_identity_is_in_the_build_frame`; [cli_contract.rs](../controller/integration/cli_contract.rs): `version_flag_reports_build_stamp_and_contract`.

<a id="contract-identity-producer"></a>
### Host producer identification

Record `producer`: `PWProducer`.

The host's typed reply carries this producer record. Each field comes from the
host's compiled build context.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-identity-producer-contract"></a>`contract` | string; required | The host's public identity, independently compared by a receiver before the reply's execution records supply interpretations. Uses [Exact admission identity](#contract-identity-public-contract), [Release and development forms](#contract-identity-public-forms), [Direct compilation contexts](#contract-identity-public-direct). |
| <a id="contract-identity-producer-describe"></a>`describe` | string; required | The host build's descriptive Git coordinate, or `unknown` in the ordinary unbound Swift build context. Packaged context generation supplies the observed build description. Uses [Describe](#contract-identity-build-describe). |
| <a id="contract-identity-producer-commit"></a>`commit` | string; required | The host build's observed Git HEAD object name, or `unknown` when the compiled context has no such observation. Identity admission uses `contract`; this field retains the host's provenance. Uses [Commit](#contract-identity-build-commit). |

**Support: [source read](#contract-support-grades) for [Host producer identification](#contract-identity-producer) and its descendants.** PWProducer.current copies the compiled contract/describe/commit context; bound reply decoding compares producer.contract before decoding descendants. Context: Read the complete producer declaration/current constructor, generated Swift context producer, ordinary fallback context and Rust bound-frame path. Evidence limit: Source reading only; component signing, live peer association and a fresh packaged producer run require their respective evidence. Source: [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift): `PWProducer`; [build_contract.py](../docs/build_contract.py): `swift`; [porcelain.rs](../controller/src/porcelain.rs): `decode_bound`.

<!-- BEGIN GENERATED CONTRACT STAMPS -->
| Surface | User artifact | Last changed |
| --- | --- | --- |
| `actor_evidence` | Actor and phase evidence | v0.3.8 |
| `actors` | Actors and phases | v0.3.8 |
| `diagnostics` | Controller findings and assessments | v0.3.8 |
| `dossier` | Specimen dossier | v0.3.8 |
| `envelope` | The controller envelope | v0.3.8 |
| `equipment` | Equipment and authority setup | v0.3.8 |
| `extensions` | Extension actions and authority custody | v0.3.8 |
| `identity` | The contract identity | v0.3.8 |
| `installation` | Managing runners | v0.3.8 |
| `lifecycle` | Process and operation observations | v0.3.8 |
| `policy` | Policy source, parameters and compilation | v0.3.8 |
| `probes` | Paired probes and attempted operations | v0.3.8 |
| `profile` | Compiled-profile receipts | v0.3.8 |
| `refusals` | Request refusals and retained evidence | v0.3.8 |
| `reply` | The host report | v0.3.8 |
| `request` | Saved specimens and runner selection | v0.3.8 |
| `steps` | Predictions, attempts and comparison | v0.3.8 |
| `transport` | Reservation, invocation and client capture | v0.3.8 |
| `wire` | Binary response primitives and validator record transport | v0.3.8 |
<!-- END GENERATED CONTRACT STAMPS -->

## Definitions

<a id="contract-identity-definitions"></a>
### Shared definitions

<a id="contract-identity-definitions-policywitness"></a>
#### PolicyWitness

PolicyWitness, abbreviated PW, is the controller, runner client, runner host,
native worker, query validator and compiler helper distributed together. The
controller exposes specimen execution, runner management and version reporting.

<a id="contract-identity-definitions-build_pipeline"></a>
#### Build pipeline

The packaged build scripts and build-contract reader select source inputs,
compute and embed the public identity, and compare it again before signing.

<a id="contract-identity-definitions-contract_generator"></a>
#### Contract generator

The contract generator reads the selected authored tree, imported declarations,
canonical shapes and retained release history to produce the public document,
snapshot and surface stamps.

<a id="contract-identity-definitions-controller"></a>
#### Controller

`policy-witness` reads and prepares the request, selects equipment, invokes the
runner client, admits its records and emits the outer JSON envelope. Its
dossier and assessments are controller observations and interpretations.

<a id="contract-identity-definitions-client"></a>
#### Runner client

The runner client acquires a reservation, submits the held request over XPC
and returns a typed capture of its transport observations and received host
bytes. The controller invokes it once for a run.

<a id="contract-identity-definitions-host"></a>
#### Runner host

The XPC host admits the request, prepares worker resources, coordinates query
collection and action release, collects worker/validator observations and
produces the host reply. Specimen policy application occurs in the worker so
the host retains its reply path.

<a id="contract-identity-definitions-worker"></a>
#### Worker

The native worker receives policy input and its own action plan, applies the
declared sandbox when requested, executes released actions and publishes
bounded observations in host-provided regions. The ordinary form uses one
fresh worker; the actor form assigns a fresh worker to each actor it launches.

<a id="contract-identity-definitions-validator"></a>
#### Validator

The native `sb_api_validator` issues `sandbox_check` queries about the selected
worker process and returns query records to the host.

<a id="contract-identity-definitions-helper"></a>
#### Compiler helper

`sbpl-check` reads policy input, inventories imports and calls the native
compiler. Its compiler result is reported in its own envelope. The standalone
helper and the controller's fallback invocation have separately stated input
and invocation conditions.

<a id="contract-identity-definitions-specimen"></a>
#### Specimen

A specimen is the declared experiment: its identifier, asserted contract,
policy or actor policies, ordered phases/actions, and accepted execution
options. A saved specimen is its JSON representation in a request file.

<a id="contract-identity-definitions-request"></a>
#### Request

A request is the value presented at an entry boundary. The controller holds
the parsed request, resolves controller-owned options and sends a serialization
of the resulting value. Submitted bytes and original file bytes are distinct
artifacts; each byte observation names the artifact it covers.

<a id="contract-identity-definitions-reply"></a>
#### Reply

A host reply is the host-produced execution record, including its producer
identity, execution summary and available observations. The typed host frame
carries this record across XPC. Raw retained bytes and an admitted decoded
reply have different availability and interpretation conditions.

An ordinary semantic reply is a reply with no reporting_failure record;
this branch includes both single-worker and actor execution forms.

<a id="contract-identity-definitions-capture"></a>
#### Capture

A client capture records reservation attempts, invocation knowledge, transport
results and host reply bytes as observed by the client. A received host frame
inside an admitted capture has its own producer admission.

<a id="contract-identity-definitions-envelope"></a>
#### Envelope

An envelope is the outer JSON record emitted by the controller or compiler
helper: `kind`, generation time, build identification, result and data. Its
result describes the emitting operation; contained query, attempt and child
results retain their own meanings.

<a id="contract-identity-definitions-actor"></a>
#### Actor

An actor names a declared worker role, sandbox setup and its visits to the
schedule. Actor identity is the request's identifier and associated owned
process evidence. A numeric PID records one observation of that association.

<a id="contract-identity-definitions-phase"></a>
#### Phase

A phase groups an ordered batch of actions under one worker or actor visit.
The host's query collection precedes release of the phase's action batch
under the ordering rules. Phase completion and individual action completion
are separate observations.

<a id="contract-identity-definitions-probe"></a>
#### Probe

A probe pairs a declared sandbox query with a declared native attempt and
assigns them a step ID. Query operation/filter and attempt kind/action/target
are separate submitted operands, whose relationships the comparison records.

<a id="contract-identity-definitions-prediction"></a>
#### Prediction

A prediction is the usable result of a native sandbox query for the reported
worker, operation and filter at collection time. Excluded queries, diagnostics
and missing validator results carry their own unavailable/error observations.
`query_first` establishes a supported ordering interval before an action
batch; changes of state inside that interval remain possible.

<a id="contract-identity-definitions-observation"></a>
#### Observation

An observation records what a named component read, returned, published or
reaped at a particular boundary. Its result, origin, subject and available
timing determine its evidentiary scope. A missing publication leaves the
operation's result unresolved even when progress indicates that it began.

<a id="contract-identity-definitions-effect"></a>
#### Effect

An effect is an observable consequence of an operation, such as creation of a
file, truncation, bytes read or written, or spawning a child. Each effect claim
is bounded by its concrete observation: descriptor metadata, content/transfer
result, child PID or independent state observation.
The meaning of a successful status is specific to that operation.

<a id="contract-identity-definitions-cause"></a>
#### Cause

A cause identifies why an event occurred. Permission-shaped return values
support the `permission_failure` observation class; they leave sandbox cause
unresolved. A termination request and a later owned reap support the specific
lifecycle relationship stated by the lifecycle assessment. Query answers and
attempt returns retain their individual observation scopes.

<a id="contract-identity-definitions-assessment"></a>
#### Assessment

An assessment is a conclusion computed from named observations and declared
relations, such as query order, operation/target relation, application state
or process disposition. Its applicability and supporting observations belong
to that assessment. Raw observation retention and permission to use an
assessment are separately reported consequences of a failed check.

<a id="contract-identity-definitions-absent"></a>
#### Absent field

A field is absent when its key is omitted from the JSON object. The field's
definition determines whether omission selects a default, means unavailable
information, makes the object inapplicable or refuses the input.

<a id="contract-identity-definitions-null_value"></a>
#### Null value

`null` is an explicitly carried JSON value. Its equivalence to omission is a
field-specific rule. In output, a null observation leaves the represented
fact unavailable unless that field defines a more specific meaning.

<a id="contract-identity-definitions-optional"></a>
#### Optional field

An optional field permits the absence specified by its record definition.
Conditional presence, explicit null and omitted serialization each retain
their own stated conditions.

<a id="contract-identity-definitions-unknown"></a>
#### Unknown fact

Unknown means the available record leaves a factual question unresolved.
Missing process status, absent completed result and unavailable provenance
therefore preserve the corresponding uncertainty. An explicit observation of
absence, such as an owned service confirmed absent, has its own evidence.

<a id="contract-identity-definitions-bytes"></a>
#### Byte observation

A byte field identifies its byte source, encoding, total/retained length and
bound where applicable. Hexadecimal and base64 are representations of bytes;
decoded diagnostic text is a separate projection. UTF-8 byte counts and
character counts use the units named by each capacity.

<a id="contract-identity-definitions-closed_object"></a>
#### Closed object

A closed input object accepts its listed keys; an unknown key is refused at
the boundary enforcing that object. Map keys, such as policy parameter names,
are values in their declared domain and have their own constraints.

<a id="contract-identity-definitions-open_values"></a>
#### Open value vocabulary

An open vocabulary admits values beyond the displayed list. Its field
definition states how unfamiliar values are retained or classified. Whether
the displayed list is exhaustive is recorded separately from admission.

<a id="contract-identity-definitions-closed_values"></a>
#### Closed value vocabulary

A closed vocabulary admits the specified set of values. The rule names the
component and boundary that identifies another value as invalid, and states
the consequence for retained records and supported assessments.

**Support: [source read](#contract-support-grades) for [Shared definitions](#contract-identity-definitions) and its descendants.** Names the actual components and record relationships; comparison source distinguishes native prediction, published attempt status, permission-shaped failures and operation/target relations. Context: Read component entry/declaration code, held-request normalization/serialization/client invocation, controller capture record, request forms, validator batch native call, comparison implementation, old file-open operation and envelope serializer. Definitions provide shared terminology; operational predicates remain owned by their surfaces. Evidence limit: Source reading is narrower than a complete lifecycle, native-effect or attribution experiment. Field presence and value admission must be supplied by each owning rule; these definitions do not establish every instance. Source: [main.rs](../controller/src/main.rs): `fn main`; [run_flow.rs](../controller/src/run_flow.rs): `fn run(args:`; [runner_client.rs](../controller/src/runner_client.rs): `RunnerClientRun`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `PWRunnerService`; [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerRunSpec`; [CWorkerComparison.swift](../runner/Sources/PWRunnerCore/CWorkerComparison.swift): `comparisonEvidence`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_open_write`; [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `SANDBOX_CHECK_NO_REPORT`; [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift): `AttemptOutcome`; [json_contract.rs](../controller/src/json_contract.rs): `Envelope`.

## Running a specimen: accepted input

<a id="contract-request"></a>
### Saved specimens and runner selection

A saved specimen describes one experiment. The controller reads its file once, resolves controller options and packaged augments, and serializes the held request delivered to the client. Direct XPC callers supply the host form themselves. The standalone compiler helper accepts its own policy input.

<a id="contract-request-specimen"></a>
#### Specimen

Record `specimen`: `PWRunnerRunSpec`.

The host request objects have closed field sets. Parameter-map keys and caller labels are data within their own bounds.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-request-specimen-contract"></a>`contract` | string; as defined below | Required non-null string asserting the exact public contract identity. The controller checks it before selector parsing and augmentation; the host checks it before other request fields. Obtain the current value from the packaged version envelope. `unbound` is refused. Uses [Exact admission identity](#contract-identity-public-contract). |
| <a id="contract-request-specimen-specimen_id"></a>`specimen_id` | string; as defined below | Required non-null string caller label, echoed when it fits <!-- span limits.specimen_id.value_unit -->255 UTF-8 bytes<!-- /span -->. It may be empty. Its identity is independent of the worker PID or an actor ID. |
| <a id="contract-request-specimen-run_kind"></a>`run_kind` | string; as defined below | Optional caller label, bounded by <!-- span limits.request_label.value_unit -->63 UTF-8 bytes<!-- /span -->. Omission and null have the same meaning; it selects no execution mode. Default: `null`. |
| <a id="contract-request-specimen-policy"></a>`policy` | [Worker policy input](#contract-policy-spec); as defined below | Policy for the ordinary form. With no non-null `actors`, the policy object is required. In the actor form a non-null top-level policy is refused; each actor declares its own sandbox mode and policy. |
| <a id="contract-request-specimen-probe_plan"></a>`probe_plan` | array of [Paired probe](#contract-probes-step); as defined below | Ordinary paired probes, including an empty array for apply-only execution. Exactly one of this field and `phases` must be non-null in the ordinary form. The host represents this plan as the `main` phase. |
| <a id="contract-request-specimen-phases"></a>`phases` | array of [Phase declaration](#contract-actors-phase); as defined below | Ordered phase declarations. The ordinary form requires a nonempty array, forbids actor ownership, termination dependencies and extension actions, and uses one worker across its phases. The actor form requires phases and forbids a non-null `probe_plan`. |
| <a id="contract-request-specimen-actors"></a>`actors` | array of [Actor declaration](#contract-actors-actor); as defined below | A non-null actor array selects the actor form; an empty array is refused. Each declared actor has its own fresh worker and at least one declared visit. Omission or null selects the ordinary form. |
| <a id="contract-request-specimen-_test_overrides"></a>`_test_overrides` | [Execution overrides](#contract-request-overrides); as defined below | Optional execution controls accepted by the host request decoder. Each declared control retains its stated scope and meaning; unknown override fields are refused. |

<a id="contract-request-specimen-hold"></a>
##### Hold and deliver the selected request

[Controller](#contract-identity-definitions-controller) acts at saved-file processing. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Uses [Specimen](#contract-identity-definitions-specimen), [Request](#contract-identity-definitions-request). Read and parse the request file once; gate its contract, parse selection, resolve named augments, strip controller selector fields and serialize once for client delivery. Preserve original and selected policy observations in the specimen dossier.

<a id="contract-request-specimen-admission"></a>
##### Admission order and effects

[Runner host](#contract-identity-definitions-host) acts at request decode and whole-request admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Uses [Stop children and preserve safe metadata](#contract-refusals-request-consequence). Check contract first, decode the selected plan form and closed nested objects, check capacities, then validate policy and plan meaning. On refusal apply the runner request-refusal consequence. A host may already exist to deliver that refusal.

Admission accepts or refuses the complete plan; it preserves declared action counts. Empty ordinary plans still compile and apply the policy.

<a id="contract-request-specimen-nulls"></a>
##### Null and omission

[Runner host](#contract-identity-definitions-host) acts at request decoding. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Uses [Absent field](#contract-identity-definitions-absent), [Null value](#contract-identity-definitions-null_value), [Extension operation](#contract-extensions-operation). Treat optional null as absent where decodeIfPresent is used. Refuse present null for actor equipment, actor required_entitlements, after_termination and actor_equipment_executable_paths. Retain presence of extension operands so an inapplicable operand is refused even when null.

<a id="contract-request-specimen-capacity"></a>
##### Bounded strings and action counts

[Runner host](#contract-identity-definitions-host) acts at pre-child admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Preserve complete UTF-8 strings at accepted bounds.

Native C-string inputs also refuse embedded NUL. A paired query and attempt consumes one action; an extension action consumes one action and contributes no query. Phase and actor counts do not multiply the total action capacity.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-request-specimen-capacity-ordinary_source"></a>Ordinary source bytes | Applies when (`specimen.actors` is absent and `specimen.policy` is present and `specimen.policy.sbpl_source` is present). Requires UTF-8 byte length of `specimen.policy.sbpl_source` ≤ `262,143 UTF-8 bytes` (`policy_source`) . |
| <a id="contract-request-specimen-capacity-actor_source"></a>Actor source bytes | Binding `a`: entry in `specimen.actors`. For each `a`. Applies when (`specimen.actors` is present and `specimen.actors[a].sandbox.policy` is present and `specimen.actors[a].sandbox.policy.sbpl_source` is present). Requires UTF-8 byte length of `specimen.actors[a].sandbox.policy.sbpl_source` ≤ `262,143 UTF-8 bytes` (`policy_source`) . |
| <a id="contract-request-specimen-capacity-flat_actions"></a>Flat action count | Applies when (`specimen.actors` is absent and `specimen.probe_plan` is present). Requires count of `specimen.probe_plan` ≤ `256 items` (`probe_steps`) . |
| <a id="contract-request-specimen-capacity-phase_actions"></a>Phased action count | Binding `p`: entry in `specimen.phases`. Applies when `specimen.phases` is present. Requires sum over `p` of count of `specimen.phases[p].actions` ≤ `256 items` (`probe_steps`) . |
| <a id="contract-request-specimen-capacity-ordinary_phases"></a>Ordinary phase count | Applies when (`specimen.actors` is absent and `specimen.phases` is present). Requires count of `specimen.phases` ≤ `8 items` (`phase_count`) . |
| <a id="contract-request-specimen-capacity-actor_phases"></a>Actor phase count | Applies when (`specimen.actors` is present and `specimen.phases` is present). Requires count of `specimen.phases` ≤ `16 items` (`actor_phases`) . |
| <a id="contract-request-specimen-capacity-failure"></a>Refusal consequence | On failure, performs [Stop children and preserve safe metadata](#contract-refusals-request-consequence) for `request`. |

<a id="contract-request-specimen-apply_only"></a>
##### Apply-only specimen

This template applies a policy with no probe actions. Replace the assertion with the packaged version's `build.contract` before submission.

```json
{"contract":"<reported-contract>","specimen_id":"apply-only","policy":{"format":"sbpl","sbpl_source":"(version 1) (allow default)"},"probe_plan":[]}
```

<a id="contract-request-specimen-duplicate_keys"></a>
##### Repeated members at each entry

For the paired repeated-member cases, CLI entry keeps the last contract, policy, probe step_id, attempt target, runner selector or runner.mode value, then holds the parsed object’s serialization. Direct host entry keeps the first contract, policy, probe step_id or attempt target value in either tested order. Direct-host runner and runner.mode cases refuse with unknown_field at ["runner"] in either order. These observations concern the listed raw-input pairs, their canonical neighbours and independent file effects on the observed platform.

**Support: [check read](#contract-support-grades) for [Repeated members at each entry](#contract-request-specimen-duplicate_keys).** The controller parses raw JSON before holding its object; the direct-host cases use retained raw request bytes. Context: Static review of the cited producer and assertion branches. Evidence limit: The pinned matrix distinguishes both member orders and canonical neighbours for six fields at CLI and direct host entries. Its selected field/value pairs bound the observation. Source: [request_patch.rs](../controller/src/request_patch.rs): `parse_request`. Check: [contract.py](../tests/suites/runner_outcome_bad_request/contract.py): `duplicate_entries`.

**Support: [check read](#contract-support-grades) for [Specimen](#contract-request-specimen) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Context: Source inspection of the current implementation; no execution is credited. Evidence limit: Read the request fixture corpus loop, identity/unknown-field checks and actor parameter-capacity assertions. The apply-only template has source-level support; this owner credits no executed instance of that template. Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerRunSpec`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `admissionFailure`, `requestAdmissionFailure`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `admitSpecimen`; [run_flow.rs](../controller/src/run_flow.rs): `validate_request_contract`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `actorAdmissionFailure`. Check: [RequestContractTests.swift](../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift): `runRequestContractTests`.

<a id="contract-request-options"></a>
#### Controller selection options

Record `options`: `ControllerSelectionOptions`.

These fields extend the saved-file root at the controller entry. The controller strips all five before client delivery. A direct XPC request carrying them reaches the host unknown-field refusal.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-request-options-runner"></a>`runner` | [Nested runner selector](#contract-request-selector); null when absent | Optional nested selector object. Null means absent. Unknown nested keys are refused. |
| <a id="contract-request-options-runner_id"></a>`runner_id` | string; null when absent | Legacy registry ID selector. Null means absent; a non-string value refuses even when nested `runner.id` would override it. |
| <a id="contract-request-options-runner_service"></a>`runner_service` | string; null when absent | Legacy explicit Mach service selector. Null means absent; a non-string value refuses before nested precedence is applied. |
| <a id="contract-request-options-required_entitlements"></a>`required_entitlements` | array of string; null when absent | Legacy list of selected-worker entitlement keys required to be boolean true. Null means absent. Values must be strings. |
| <a id="contract-request-options-runner_mode"></a>`runner_mode` | string; null when absent | Legacy runner mode. Null means absent. The accepted values are `standard` and `byoxpc`. Admitted vocabulary: closed; displayed list: exhaustive: `"standard"`, `"byoxpc"`. |

<a id="contract-request-options-precedence"></a>
##### Selector precedence

[Controller](#contract-identity-definitions-controller) acts at runner selector parsing. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Validate every supplied legacy value first, then let each non-null nested value replace its corresponding legacy value. An explicit nested empty entitlement list replaces the legacy list. Refuse standard mode with an external selector and byoxpc mode without an ID or service.

CLI `--runner-mode` is parsed before reading the request and is injected into its selector processing. `machme` is refused. Selection resolution and entitlement checks precede client invocation. A resolved target identifies the requested host service; actor equipment roles remain actor declarations.

<a id="contract-request-options-failure_order"></a>
##### Selection and augmentation failure order

[Controller](#contract-identity-definitions-controller) acts at request preparation. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Uses [Controller pre-invocation refusal](#contract-refusals-controller-consequence). Retain a target-resolution error while resolving augment dossiers. Select the target-resolution error first; otherwise select an augment refusal when present. Apply the controller pre-invocation consequence to the selected failure.

**Support: [check read](#contract-support-grades) for [Controller selection options](#contract-request-options) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Context: Source inspection of the current implementation; no execution is credited. Evidence limit: Read parser and precedence controls; full registry selection and installed-equipment evidence belongs to installation and equipment. Source: [runner_select.rs](../controller/src/runner_select.rs): `parse_runner_selector_value`; [run_flow.rs](../controller/src/run_flow.rs): `strip_runner_selector`. Check: [runner_select.rs](../controller/src/runner_select.rs): `nested_runner_takes_precedence_over_legacy_top_level`, `malformed_selection_never_falls_back_or_discards_entitlements`, `optional_nulls_and_explicit_nested_empty_entitlements_have_defined_meanings`.

<a id="contract-request-selector"></a>
#### Nested runner selector

Record `selector`: `ControllerRunnerSelector`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-request-selector-id"></a>`id` | string; null when absent | Registry ID for an installed external runner. |
| <a id="contract-request-selector-service"></a>`service` | string; null when absent | Explicit external Mach service name. |
| <a id="contract-request-selector-required_entitlements"></a>`required_entitlements` | array of string; null when absent | Selected-worker entitlement keys that must read back as boolean true for selection. This demand is separate from each actor's required_entitlements. |
| <a id="contract-request-selector-mode"></a>`mode` | string; null when absent | Mode constraint applied to selection. With no mode or external selector, selection uses the packaged standard runner. Admitted vocabulary: closed; displayed list: exhaustive: `"standard"`, `"byoxpc"`. |

**Support: [source read](#contract-support-grades) for [Nested runner selector](#contract-request-selector) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Source: [runner_select.rs](../controller/src/runner_select.rs): `RunnerSelector`, `parse_runner_selector_value`.

<a id="contract-request-overrides"></a>
#### Execution overrides

Record `overrides`: `PWRunnerTestOverrides`.

These controls are admitted as request data in the current implementation, including packaged hosts. Their names identify test use; the parser applies the documented grammar and capacities. Host admission of a positive fixture value can be followed by worker argument refusal before application.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-request-overrides-worker_executable_path"></a>`worker_executable_path` | string; omitted when absent | Ordinary-worker executable override, bounded by <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span -->. Actor-form admission refuses this singular override. |
| <a id="contract-request-overrides-worker_timeout_ms"></a>`worker_timeout_ms` | integer; omitted when absent | Ordinary worker sentinel budget override in milliseconds. The host floors the supplied allowance at <!-- span limits.worker_timeout_override_floor.value_unit -->50 milliseconds<!-- /span -->; omission uses <!-- span limits.worker_sentinel_wait.value_unit -->120,000 milliseconds<!-- /span -->. Actor scheduling uses its fixed setup allowance and its fixed <!-- span limits.actor_execution_allowance.value_unit -->120,000 milliseconds<!-- /span --> execution allowance even when this field is supplied. |
| <a id="contract-request-overrides-actor_equipment_executable_paths"></a>`actor_equipment_executable_paths` | object with string keys and string values; omitted when absent | Actor equipment role-to-path map. Present maps must be nonempty and use only `selected` and `unentitled` keys; actor admission requires absolute paths. The ordinary form refuses this map. |
| <a id="contract-request-overrides-validator_executable_path"></a>`validator_executable_path` | string; omitted when absent | Validator executable override, bounded by <!-- span limits.test_override_path.value_unit -->1,023 UTF-8 bytes<!-- /span -->. The validator remains a separate child and receives query work through its own channel. |
| <a id="contract-request-overrides-validator_total_timeout_ms"></a>`validator_total_timeout_ms` | integer; omitted when absent | Cumulative validator collection budget override in milliseconds, spanning phases. Both schedulers clamp it to a minimum of <!-- span limits.validator_collection_override_floor.value_unit -->1 millisecond<!-- /span --> and their configured maximum: <!-- span limits.phase_collection_wait.value_unit -->30,000 milliseconds<!-- /span --> for the ordinary form and <!-- span limits.actor_collection_allowance.value_unit -->30,000 milliseconds<!-- /span --> for actors. Omission uses that maximum. |
| <a id="contract-request-overrides-validator_io_timeout_ms"></a>`validator_io_timeout_ms` | integer; omitted when absent | Per-validator I/O timeout override in milliseconds. The host floors the proposed allowance at <!-- span limits.validator_io_override_floor.value_unit -->50 milliseconds<!-- /span -->; omission uses <!-- span limits.validator_io_wait.value_unit -->30,000 milliseconds<!-- /span -->. The remaining aggregate collection allowance can reduce the effective timeout below that floor. |
| <a id="contract-request-overrides-worker_post_apply_hang_ms"></a>`worker_post_apply_hang_ms` | integer; omitted when absent | Positive fixture delay in milliseconds after all declared visits and actions, before terminal publication. The host forwards positive values; the worker argument parser accepts through <!-- span limits.worker_fixture_delay.value_unit -->60,000 milliseconds<!-- /span -->. A larger forwarded value causes worker argument refusal after launch. Zero and negative values are omitted by the host. |
| <a id="contract-request-overrides-worker_post_apply_kill_signal"></a>`worker_post_apply_kill_signal` | integer; omitted when absent | Positive fixture signal requested after completed actions and before terminal publication, including an unapplied actor's visits. The host forwards positive values; the worker accepts signal numbers through 31. A larger value causes worker argument refusal after launch. Zero and negative values are omitted. A signal request can return without termination; final process observations decide the ending. |
| <a id="contract-request-overrides-worker_pre_ready_hang_ms"></a>`worker_pre_ready_hang_ms` | integer; omitted when absent | Positive fixture delay in milliseconds after compilation and optional capture, before an apply worker's readiness byte and policy application. The host forwards positive values; the worker argument parser accepts through <!-- span limits.worker_fixture_delay.value_unit -->60,000 milliseconds<!-- /span -->. A larger value causes worker argument refusal after launch. Zero and negative values are omitted. The unapplied actor branch bypasses this compile/readiness path. |
| <a id="contract-request-overrides-worker_kill_before_publish_slot"></a>`worker_kill_before_publish_slot` | integer; omitted when absent | Nonnegative zero-based slot in each worker's own plan. After that attempt returns and its result payload is written, the worker raises SIGKILL before publishing completion. Negative values are omitted. The worker argument parser requires an index below <!-- span limits.probe_steps.value_unit -->256 items<!-- /span -->; an index beyond the worker's actual plan has no reached action to trigger it. |

**Support: [check read](#contract-support-grades) for [worker_timeout_ms](#contract-request-overrides-worker_timeout_ms).** Calls the production helper to compare its floor to the limits inventory; independent below/equal/above cases retain the minimum and the uncapped larger override. Context: Planning helper and newly authored constructed assertions read. Evidence limit: No test execution is credited; the check establishes the planning value, not elapsed worker time. Source: [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `timeoutMsForCWorker`. Check: [LimitsContractTests.swift](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift): `runLimitsContractTests`.

**Support: [check read](#contract-support-grades) for [worker_timeout_ms](#contract-request-overrides-worker_timeout_ms).** Actor orchestration constructs the scheduler input with its fixed allowances. Context: Static review of the cited producer and assertion branches. Evidence limit: The paired control uses a 200 ms override and a 500 ms delay, checking an ordinary timeout and actor completion with a later dependent file read. Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `runActors`. Check: [check_actor_compositions.py](../tests/suites/witness_contract/check_actor_compositions.py): `assert_timeout_applicability`.

<a id="contract-request-overrides-override_authority"></a>
##### Override admission and equipment ordering

Uses [Static worker binding](#contract-equipment-binding).

A caller whose connection passes host authorization can supply these controls. Actor equipment preparation checks the packaged inventory and both packaged role bindings before considering fixture override bindings. It retains the packaged and test_override rows with their respective implementation identities.

**Support: [check read](#contract-support-grades) for [Execution overrides](#contract-request-overrides).** The actor path retains equipment preparation and fixed scheduler applicability separately. Context: Static review of the cited producer and assertion branches. Evidence limit: Excessive positive fixture values are sent through the selected CLI and checked at the downstream worker argument boundary. Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `runActors`. Check: [check_pre_apply_failure.py](../tests/suites/witness_contract/check_pre_apply_failure.py): `main`.

**Support: [source read](#contract-support-grades) for [Execution overrides](#contract-request-overrides) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerTestOverrides`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `timeoutMsForCWorker`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `admitSpecimen`; [CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift): `collectionRemainingNs`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `collectionRemainingNs`; [ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift): `postApplyHangMs`; [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `private func prepare`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `kill_before_publish_slot`.

<a id="contract-policy"></a>
### Policy source, parameters and compilation

<a id="contract-policy-spec"></a>
#### Worker policy input

Record `spec`: `PWRunnerPolicySpec`.

Each apply actor owns a separate policy. The host bounds the selected source string and parameter map before starting workers or validators.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-policy-spec-format"></a>`format` | string; as defined below | The accepted policy representation is `sbpl`; another value is refused before worker launch. Admitted vocabulary: closed; displayed list: exhaustive: `"sbpl"`. |
| <a id="contract-policy-spec-sbpl_source"></a>`sbpl_source` | string; as defined below | Required string when applying a policy. An empty string reaches native compilation. The final source after augmentation fits <!-- span limits.policy_source.value_unit -->262,143 UTF-8 bytes<!-- /span -->, and embedded NUL is refused before child launch. |
| <a id="contract-policy-spec-params"></a>`params` | object with string keys and string values; as defined below | Optional string-to-string compiler parameter map. Omission, null and an empty map produce no native parameter setup. Supplied names remain open data. At most <!-- span limits.policy_parameters.value_unit -->1,024 items<!-- /span --> fit each policy, with keys bounded by <!-- span limits.parameter_key.value_unit -->127 UTF-8 bytes<!-- /span --> and values by <!-- span limits.parameter_value.value_unit -->383 UTF-8 bytes<!-- /span -->; native strings must be NUL-free. |
| <a id="contract-policy-spec-capture_compiled_profile"></a>`capture_compiled_profile` | boolean; as defined below | When true, request a compiled-profile receipt from the worker before application and require a valid capture_nonce. Omission, null and false leave capture unrequested. Default: `false`. |
| <a id="contract-policy-spec-capture_nonce"></a>`capture_nonce` | string; as defined below | Required with enabled capture: exactly 32 lowercase hexadecimal characters encoding the caller's nonce. A non-null nonce with capture disabled is an inapplicable-field refusal. Receipt publication and consistency checks belong to the compiled-profile surface. Required when `spec.capture_compiled_profile` = `true`. Present when `spec.capture_compiled_profile` = `true`. |
| <a id="contract-policy-spec-augments"></a>`augments` | array of string; as defined below | Controller-resolved list of named packaged SBPL fragments. Omission, null and an empty list are no-ops. The controller strips the field before delivery. The host accepts the no-op forms and refuses a nonempty unresolved list. |

<a id="contract-policy-spec-parameters"></a>
##### Prepare native compiler input

[Runner host](#contract-identity-definitions-host), [Worker](#contract-identity-definitions-worker) acts at policy preparation and compilation. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Sort parameter keys, transport their complete strings, create native parameters only for a nonempty map, and pass each key and value through sandbox_set_param before compiling the selected source. Report setup or compile failure at the observed native stage.

A supplied parameter is data for the SBPL compiler. The compiler decides how source expressions use it. Source text, selected parameter values and imported file bytes are distinct inputs.

<a id="contract-policy-spec-parameter_example"></a>
##### Parameter expressions

A source may combine a parameter with a literal suffix:

```scheme
(version 1)
(deny default)
(allow file-read* (literal (string-append (param "ROOT") "/hosts")))
```

`"params":{"ROOT":"/etc"}` supplies the value used by this expression. An unused `OPTIONAL` parameter and a referenced but missing `ROOT` exercise different compiler paths. Inspect the native compile record for the latter's outcome.

<a id="contract-policy-spec-parameter_evidence"></a>
##### Parameter example observations

Native compiler examples concern the helper invocation that produced the verdict. Worker examples use the consumed source and parameter values, then observe application and the requested fresh-file effects on concrete targets. Record the selected binaries, policy and platform with each native observation.

**Support: [check read](#contract-support-grades) for [Parameter example observations](#contract-policy-spec-parameter_evidence).** Helper metadata and native verdict are retained together. Context: Static review of the cited producer and assertion branches. Evidence limit: Helper omitted/null/empty neighbours and worker ROOT twins have distinct oracles; worker target bytes and descriptor identity are checked independently. Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `check`. Check: [cli_contract.rs](../controller/integration/cli_contract.rs): `sbpl_check_verdicts_follow_the_native_compiler`; [contract.py](../tests/suites/runner_outcome_bad_request/contract.py): `composite_parameters`.

<a id="contract-policy-spec-compile_classification"></a>
##### Worker and helper compile classification

The worker treats a null compiled-profile pointer as failure and proceeds to capture and application with a non-null profile. The helper requires a profile and no native diagnostic for success, and frees the returned profile, parameters and diagnostic it owns. A simultaneous profile and diagnostic therefore has different classifications at these two boundaries. The helper branch has an injected native-return control; native occurrence of the worker combination remains unobserved.

**Support: [check read](#contract-support-grades) for [Worker and helper compile classification](#contract-policy-spec-compile_classification).** Worker pointer acceptance and helper diagnostic-sensitive classification are separate producer rules. Context: Static review of the cited producer and assertion branches. Evidence limit: Injected helper returns check verdict and free counts. Worker simultaneous profile/diagnostic occurrence has source support only. Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `sandbox_compile_string(policy_buf`; [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `compile_with`. Check: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `a_profile_succeeds_alone_and_fails_beside_an_error_buffer`.

**Support: [source read](#contract-support-grades) for [Worker policy input](#contract-policy-spec) and its descendants.** The adjacent field meanings and operations follow the named implementation. Evidence limit: Decoder, meaning checks, parameter ordering, worker parameter snapshot/setup and compilation branches read. Native execution is not credited. Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerPolicySpec`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `policyMeaningFailure`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `workerParamsFromPolicy`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `sandbox_set_param`.

<a id="contract-policy-augments"></a>
#### Augment resolution

Augments select packaged source fragments from `Contents/Resources/Augments/<name>.sb`. Names are nonempty ASCII letters, digits or underscore. The resolver treats the fragment contents as source text.

<a id="contract-policy-augments-resolve"></a>
##### Resolve and append

[Controller](#contract-identity-definitions-controller) acts at saved-file policy normalization. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. For a nonempty augment list require a string source, validate every name, read the named resources in requested order and append a newline plus each fragment. Replace the policy source only after every requested read succeeds. Remove augments from the held policy before submission.

An empty string source is accepted at this normalization boundary. An unavailable resource produces `augment_unavailable` at the offending list element. Invalid names produce `invalid_augment_name`. A wrong list or element type produces `type_mismatch`. The original file remains unchanged because resolution edits the held JSON value.

<a id="contract-policy-augments-actors"></a>
##### Resolve actor policies in request order

[Controller](#contract-identity-definitions-controller) acts at actor policy normalization. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Resolve each actor policy object in actor order and stop after the first augment refusal. Retain each visited actor's original and selected source in its dossier. Mode and policy applicability are judged later by host admission.

<a id="contract-policy-augments-exec_baseline"></a>
##### Packaged exec baseline

`exec_baseline` appends these source rules:

```scheme
(allow process-exec*)
(allow process-fork)
(allow file-read*)
```

The `file-read*` allowance is unconditional. Using this augment changes the selected policy's file-read authority and can mask the denial a file-read experiment intended to observe. Its documented derivation used macOS 14.8.3, build 23J220, and the repository's dynamic exec helper.

<a id="contract-policy-augments-augment_semantics"></a>
##### Augment evidence scope

The resolver validates all names before file access, reads fragments in requested order and appends each with a leading newline. Native behavior is scoped to the exact fragment bytes, base policy and macOS build observed. The packaged exec_baseline fragment includes broad file-read allowance; additional prerequisites and SBPL composition on another platform require their own observations.

**Support: [source read](#contract-support-grades) for [Augment evidence scope](#contract-policy-augments-augment_semantics).** Resolver validation, ordered reads and source append define the produced policy text. Evidence limit: Resolver correctness and selected native fragment observations have distinct scopes. Source: [augments.rs](../controller/src/augments.rs): `resolve_policy_augments`.

**Support: [check read](#contract-support-grades) for [Augment resolution](#contract-policy-augments) and its descendants.** The adjacent field meanings and operations follow the named implementation. Context: Review of the named producer branches. Evidence limit: Read append/no-partial-replacement and actor-order controls. The packaged baseline source was read; its historical derivation is inherited evidence. Source: [augments.rs](../controller/src/augments.rs): `resolve_policy_augments`, `resolve_actor_augments`; [exec_baseline.sb](../runner/augments/exec_baseline.sb): `(allow process-exec*)`. Check: [augments.rs](../controller/src/augments.rs): `applies_and_strips_field`, `unknown_name_is_bad_request_without_partial_apply`, `actor_policies_resolve_at_their_own_paths_and_stop_at_the_first_refusal`.

<a id="contract-policy-helper_request"></a>
#### Standalone compiler-helper request

Record `helper_request`: `rust.CheckRequest`.

`sbpl-check --request <path>` reads a policy request file; `--request -` reads stdin. This decoder selects the policy object and ignores other root fields. It accepts input without a public-contract assertion.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-policy-helper_request-policy"></a>`policy` | [Compiler-helper policy](#contract-policy-helper_policy); as defined below | Required compiler-helper policy object. |

<a id="contract-policy-helper_request-read"></a>
##### Read helper input

[Compiler helper](#contract-identity-definitions-helper) acts at standalone argument, read and JSON boundary. Entry: standalone helper, controller helper stdin. Recipient: caller, report reader. Reports: helper envelope, stderr. Use the helper policy decoder. Usage errors, input-read errors and JSON/decode errors exit 2 and report on stderr. Successfully decoded requests proceed to helper admission and produce an envelope.

**Support: [source read](#contract-support-grades) for [Standalone compiler-helper request](#contract-policy-helper_request) and its descendants.** The adjacent field meanings and operations follow the named implementation. Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `CheckRequest`, `fn main`.

<a id="contract-policy-helper_policy"></a>
#### Compiler-helper policy

Record `helper_policy` locations: `helper_request.policy`.

The helper decoder ignores policy members outside this record, including capture and augment requests. Controller fallback supplies the already normalized policy source.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-policy-helper_policy-format"></a>`format` | string; as defined below | Require `sbpl` at helper admission. Admitted vocabulary: closed; displayed list: exhaustive: `"sbpl"`. |
| <a id="contract-policy-helper_policy-sbpl_source"></a>`sbpl_source` | string; as defined below | Require a string source at helper admission; allow an empty string for the native compiler. Bound its UTF-8 bytes by <!-- span limits.helper_source.value_unit -->4,194,304 bytes<!-- /span -->, then require a NUL-free C string. |
| <a id="contract-policy-helper_policy-params"></a>`params` | object with string keys and string values; as defined below | Optional string map. Null and absence mean no map; an empty map is present for reporting but needs no native parameter object. Reject embedded NUL in each key and value before inventory or native calls. |

<a id="contract-policy-helper_policy-admit"></a>
##### Helper admission order

[Compiler helper](#contract-identity-definitions-helper) acts at pre-inventory admission. Entry: standalone helper, controller helper stdin. Recipient: caller, report reader. Reports: helper envelope. Binding `k`: entry in `helper_policy.params`. Association restriction for `k`: (`k` contains `"\u0000"` or `helper_policy.params[k]` contains `"\u0000"`). Select the first matching case in the listed order. Stop at the first admission refusal. After format, source-presence and source-extent checks pass, construct the source C string and then parameter key/value C strings in map order; a failed conversion prevents later conversions and retains its diagnostic.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-policy-helper_policy-admit-format"></a>1. Unsupported format | `helper_policy.format` ≠ `"sbpl"` | sets `helper_envelope.result.ok` to `false`, sets `helper_envelope.result.exit_code` to `1`, sets `helper_envelope.result.normalized_outcome` to `"bad_request"`, sets `helper_envelope.data.policy_sha256` to `null`, sets `helper_envelope.data.compile` to `null`, sets `helper_envelope.data.import_inventory` to `null`. |
| <a id="contract-policy-helper_policy-admit-source"></a>2. Missing source | `helper_policy.sbpl_source` is absent | sets `helper_envelope.result.ok` to `false`, sets `helper_envelope.result.exit_code` to `1`, sets `helper_envelope.result.normalized_outcome` to `"bad_request"`, sets `helper_envelope.data.policy_sha256` to `null`, sets `helper_envelope.data.compile` to `null`, sets `helper_envelope.data.import_inventory` to `null`. |
| <a id="contract-policy-helper_policy-admit-extent"></a>3. Oversized source | (`helper_policy.sbpl_source` is present and UTF-8 byte length of `helper_policy.sbpl_source` > `4,194,304 bytes` (`helper_source`) ) | sets `helper_envelope.result.ok` to `false`, sets `helper_envelope.result.exit_code` to `1`, sets `helper_envelope.result.normalized_outcome` to `"policy_too_large"`, sets `helper_envelope.data.policy_sha256` to `null`, sets `helper_envelope.data.compile` to `null`, sets `helper_envelope.data.import_inventory` to `null`. |
| <a id="contract-policy-helper_policy-admit-source_nul"></a>4. Source NUL | (`helper_policy.sbpl_source` is present and `helper_policy.sbpl_source` contains `"\u0000"`) | sets `helper_envelope.result.ok` to `false`, sets `helper_envelope.result.exit_code` to `1`, sets `helper_envelope.result.normalized_outcome` to `"bad_request"`, sets `helper_envelope.data.policy_sha256` to `null`, sets `helper_envelope.data.compile` to `null`, sets `helper_envelope.data.import_inventory` to `null`. |
| <a id="contract-policy-helper_policy-admit-parameter_nul"></a>5. Parameter NUL | (`helper_policy.params` is present and number of matching entries for `k` > `0`) | sets `helper_envelope.result.ok` to `false`, sets `helper_envelope.result.exit_code` to `1`, sets `helper_envelope.result.normalized_outcome` to `"bad_request"`, sets `helper_envelope.data.policy_sha256` to `null`, sets `helper_envelope.data.compile` to `null`, sets `helper_envelope.data.import_inventory` to `null`. |

**Support: [source read](#contract-support-grades) for [Compiler-helper policy](#contract-policy-helper_policy) and its descendants.** The adjacent field meanings and operations follow the named implementation. Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `admit`, `CheckPolicy`.

<a id="contract-probes"></a>
### Paired probes and attempted operations

<a id="contract-probes-step"></a>
#### Paired probe

Record `step`: `PWRunnerProbeStep`.

One paired probe contributes one action and at most one eligible validator query.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-probes-step-step_id"></a>`step_id` | string; as defined below | Caller label associating a query with its attempt and result. It is unique across all actions and fits <!-- span limits.step_id.value_unit -->63 UTF-8 bytes<!-- /span --> and is NUL-free. Actor plans require it to be nonempty; ordinary plans currently accept a unique empty value. |
| <a id="contract-probes-step-sandbox_check"></a>`sandbox_check` | [Sandbox query](#contract-probes-query); as defined below | Requested prediction operation and filter. Admission validates this request independently from the attempt. |
| <a id="contract-probes-step-attempt"></a>`attempt` | [Attempt request](#contract-probes-attempt); as defined below | Requested native operation. |

<a id="contract-probes-step-read_hosts"></a>
##### Read-hosts pair

This step pairs a path query with an open-read attempt:

```json
{"step_id":"read-hosts","sandbox_check":{"operation":"file-read-data","filter":{"kind":"path","value":"/etc/hosts"}},"attempt":{"kind":"file","action":"open_read","target":"/etc/hosts"}}
```

The open-read operation's success establishes its open boundary. A `read_fresh` attempt supplies the separate read-count, content and close observations described by the step-result surface.

**Support: [source read](#contract-support-grades) for [Paired probe](#contract-probes-step) and its descendants.** The adjacent field meanings and operations follow the named implementation. Evidence limit: Grammar and uniqueness branches read. The teaching step is a template; no live result is claimed. Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerProbeStep`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `requestMeaningFailure`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-probes-query"></a>
#### Sandbox query

Record `query`: `PWRunnerSandboxCheck`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-probes-query-operation"></a>`operation` | string; as defined below | Nonempty after whitespace trimming for admission, bounded by <!-- span limits.query_operation.value_unit -->127 UTF-8 bytes<!-- /span -->, NUL-free operation string passed unchanged to prediction planning. Accepted strings remain open to native operation support. |
| <a id="contract-probes-query-filter"></a>`filter` | [Sandbox filter](#contract-probes-filter); as defined below | Closed filter kind with its applicable optional value. |

<a id="contract-probes-query-eligibility"></a>
##### Admission and eligibility

[Runner host](#contract-identity-definitions-host) acts at query admission and planning. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Uses [Excluded prediction pairs](#contract-probes-query-excluded). Check operation trimming first, filter kind next, and value applicability and trimming last; stop at the first refusal. For an admitted query, withhold native prediction when its path fails host realpath planning or its operation/filter pair is excluded; report prediction_unavailable while leaving the attempt eligible.

A path created by the attempt can be unresolved at planning and resolve in later host diagnostics. These observations have separate times and owners.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-probes-query-eligibility-trimmed"></a>Whitespace-trimmed query inputs | The operation is nonempty after trimming whitespace and newlines. For a known non-none filter, its supplied value is also nonempty after that trimming. |
| <a id="contract-probes-query-eligibility-known_filter"></a>Known filter | Requires `query.filter.kind` is one of `"none"`, `"path"`, `"global_name"`, `"local_name"`, `"iokit_registry_entry_class"`, `"iokit_user_client_class"`, `"sysctl_name"`. |
| <a id="contract-probes-query-eligibility-value_presence"></a>Applicable value | Requires ((if `query.filter.kind` = `"none"`, then `query.filter.value` is absent) and (if `query.filter.kind` ≠ `"none"`, then `query.filter.value` is present)). |
| <a id="contract-probes-query-eligibility-failure"></a>Whole-request refusal | On failure, performs [Stop children and preserve safe metadata](#contract-refusals-request-consequence) for `request`. |

<a id="contract-probes-query-excluded"></a>
##### Excluded prediction pairs

The exclusion belongs to the pair. Other operations using the same filter follow their own eligibility and native result.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-probes-query-excluded-pairs"></a>Exact excluded pairs | Requires ((`query.operation` = `"iokit-open-service"` and `query.filter.kind` = `"iokit_registry_entry_class"`) or (`query.operation` = `"iokit-open-user-client"` and `query.filter.kind` = `"iokit_user_client_class"`) or (`query.operation` = `"sysctl-read"` and `query.filter.kind` = `"sysctl_name"`) or (`query.operation` = `"mach-lookup"` and `query.filter.kind` = `"local_name"`)). |

<a id="contract-probes-query-exclusion_evidence"></a>
##### Prediction-exclusion evidence scope

The IOKit and sysctl exclusions retain the dated 2026-05-29 exploration of filter IDs 1–200. The local Mach mapping remains conservatively unresolved. Each native filter observation belongs to its recorded operation, target and platform; the finite exploration bounds the basis for the current exclusion table.

**Support: [source read](#contract-support-grades) for [Prediction-exclusion evidence scope](#contract-probes-query-exclusion_evidence).** The table preserves the dated IOKit/sysctl exploration and conservative local-Mach choice. Evidence limit: This owner reads the recorded basis and current table; it adds no native rerun credit. Source: [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `predictionUnavailableOpFilters`.

**Support: [source read](#contract-support-grades) for [Sandbox query](#contract-probes-query) and its descendants.** The adjacent field meanings and operations follow the named implementation. Source: [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `predictionUnavailableOpFilters`, `sandboxCheckFailure`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `pathFilterIsUnresolvable`.

<a id="contract-probes-filter"></a>
#### Sandbox filter

Record `filter`: `PWRunnerSandboxFilter`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-probes-filter-kind"></a>`kind` | string; as defined below | Filter representation admitted by the host. Admitted vocabulary: closed; displayed list: exhaustive: `"none"`, `"path"`, `"global_name"`, `"local_name"`, `"iokit_registry_entry_class"`, `"iokit_user_client_class"`, `"sysctl_name"`. |
| <a id="contract-probes-filter-value"></a>`value` | string; as defined below | For `none`, require absence or null. Every other kind requires a string nonempty after whitespace trimming, bounded by <!-- span limits.query_filter_value.value_unit -->511 UTF-8 bytes<!-- /span --> and NUL-free. The original string is retained and passed through unchanged. |

**Support: [source read](#contract-support-grades) for [Sandbox filter](#contract-probes-filter) and its descendants.** The adjacent field meanings and operations follow the named implementation. Source: [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `sandboxCheckFailure`; [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerSandboxFilter`.

<a id="contract-probes-attempt"></a>
#### Attempt request

Record `attempt`: `PWRunnerAttempt`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-probes-attempt-kind"></a>`kind` | string; as defined below | Native operation family selected with action. Admitted vocabulary: closed; displayed list: exhaustive: `"file"`, `"mach_lookup"`, `"sysctl"`, `"exec"`. |
| <a id="contract-probes-attempt-action"></a>`action` | string; as defined below | Closed action within its family, listed in the operation table below. An unsupported pair refuses the complete request before children. |
| <a id="contract-probes-attempt-target"></a>`target` | string; as defined below | Operation target, bounded by <!-- span limits.attempt_target.value_unit -->511 UTF-8 bytes<!-- /span --> and NUL-free. Exec requires an absolute path. Other admitted targets retain their supplied native-operation meaning. |
| <a id="contract-probes-attempt-args"></a>`args` | array of string; as defined below | Exec-only argument strings appended after target as argv[0]. Omission and null mean an empty list. A supplied array on another kind, including an empty array, is refused. At most <!-- span limits.exec_arguments.value_unit -->15 items<!-- /span --> are admitted, each NUL-free and bounded by <!-- span limits.exec_argument.value_unit -->127 UTF-8 bytes<!-- /span -->. Default: `[]`. |

<a id="contract-probes-attempt-operations"></a>
##### Native operations

The worker runs the selected operation after policy application in an apply worker, or after the unapplied actor's setup:

| Kind / action | Native operation and operation-specific consequence |
| --- | --- |
| `file / open_read` | `open(O_RDONLY)`; on an accepted descriptor, request a one-byte read and close. Aggregate success is the successful open; read and close results are discarded. |
| `file / open_write` | `open(O_WRONLY \| O_TRUNC)`; on an accepted descriptor, request a one-byte `x` write and close. Aggregate success is the successful open; write and close results are discarded. |
| `file / create` | `open(O_WRONLY \| O_CREAT, 0600)` then close. Creation mode is subject to umask. An existing file is opened without truncation or exclusive creation. |
| `file / read_fresh` | Fresh `open(O_RDONLY \| O_CLOEXEC)`, `fstat`, one read bounded by <!-- span limits.fresh_read_bytes.value_unit -->64 bytes<!-- /span -->, then close. Record each boundary and read bytes; aggregate failure selects stat, read or close failure after a successful open. |
| `file / write_fresh` | Fresh `open(O_WRONLY \| O_CLOEXEC)` of an existing target, opened `fstat`, `ftruncate(0)`, truncated `fstat`, one-byte `x` write after successful truncation, written `fstat`, then close. Preserve the first failure in the aggregate. |
| `file / create_fresh` | `lstat` before a fresh exclusive `open(O_WRONLY \| O_CLOEXEC \| O_CREAT \| O_EXCL, 0600)`, opened `fstat`, one-byte `x` write, written `fstat`, then close. Pre-open `lstat` is an independent observation. Preserve the first operation failure in the aggregate. |
| `file / unlink` | `unlink(target)` and its return/errno. |
| `file / access` | `access(target, R_OK)` and its return/errno. This is an access-check observation. |
| `mach_lookup / bootstrap_look_up` | Obtain the task bootstrap port and call `bootstrap_look_up` for the supplied name; release the returned service port on success. |
| `sysctl / read` | One `sysctlbyname` call with a <!-- span limits.sysctl_read_bytes.value_unit -->4,096 bytes<!-- /span --> buffer acquired after application. Report the call's result and errno; discard value bytes and the returned length. |
| `exec / spawn` | Prepare per-attempt child resources, call `posix_spawn` for the absolute target with the requested argv, then collect child and cleanup observations. |

A short fresh write records its native count and fails the aggregate while retaining zero native errno when the write returned a short nonnegative count. A fresh file descriptor belongs to that attempt and is closed before its result is published.

<a id="contract-probes-attempt-execute"></a>
##### Execute a declared operation

[Worker](#contract-identity-definitions-worker) acts at released action slot. Entry: worker action. Recipient: caller, report reader. Reports: runner reply. Uses [Observation](#contract-identity-definitions-observation), [Effect](#contract-identity-definitions-effect). Dispatch only the admitted kind/action pair, record the operation's native observations and publish its slot after the attempt. Preserve operation-specific success meaning alongside the aggregate result.

**Support: [source read](#contract-support-grades) for [Execute a declared operation](#contract-probes-attempt-execute).** Native operation details and aggregate return/errno projection have their own report fields. Evidence limit: This owner is source-read. Selected fresh-file, descriptor, sysctl-buffer and exec-cleanup executions need their exact operation owners. Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_read_fresh`, `attempt_file_write_fresh`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildAttemptResult`.

<a id="contract-probes-attempt-exec"></a>
##### Exec setup and child inputs

[Worker](#contract-identity-definitions-worker) acts at released exec action after setup. Entry: worker action. Recipient: caller, report reader. Reports: runner reply. After application or an actor's unapplied declaration, acquire stdout/stderr pipes and spawn actions for this released attempt, release them on setup failure and at completion, and report the failing setup call when spawning was prevented. Spawn with target as argv[0], an empty environment, /dev/null stdin, captured stdout/stderr, close-on-exec descriptor policy and a new process group.

A successful spawn supplies a child PID even if the child later exits nonzero. The child collection, termination request and owned reap remain separate observations. The production per-child collection allowance is <!-- span limits.exec_child_wait.value_unit -->10,000 milliseconds<!-- /span --> after successful spawn, capped by the remaining per-worker active-plan allowance of <!-- span limits.exec_attempt_budget.value_unit -->115,000 milliseconds<!-- /span -->. The active-plan clock starts before worker setup, includes setup and intervening work, and excludes acknowledged release waits and accepted actor parked-activation waits. Both allowances use continuous time, including system sleep. Exhausted allowance can refuse a later spawn or stop collection; clock faults retain their own boundary. Blocking native calls can outlast the allowance.

<a id="contract-probes-attempt-extension_exec"></a>
##### Extension participant restriction

[Runner host](#contract-identity-definitions-host) acts at actor admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Applies when (`request.actors` is present and `request.phases` is present). performs [Exclude exec in participating actors](#contract-extensions-operation-exec) for `request`. Uses [Extension operation](#contract-extensions-operation).

**Support: [source read](#contract-support-grades) for [Attempt request](#contract-probes-attempt) and its descendants.** The adjacent field meanings and operations follow the named implementation. Source: [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `mapAttemptKind`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_open_read`, `attempt_file_write_fresh`, `attempt_sysctl_read`; [pw_worker_exec.h](../controller/tools/pw_probe_runner/pw_worker_exec.h): `attempt_exec_spawn`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`; [pw_worker_timing.h](../controller/tools/pw_probe_runner/pw_worker_timing.h): `PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT`, `pw_timing_setup`.

<a id="contract-actors"></a>
### Actors and phases

<a id="contract-actors-actor"></a>
#### Actor declaration

Record `actor`: `PWRunnerActor`.

A specimen admits at most <!-- span limits.actors.value_unit -->8 items<!-- /span -->.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actors-actor-actor_id"></a>`actor_id` | string; as defined below | Nonempty specimen-local actor identifier, unique across actors and bounded by <!-- span limits.actor_id.value_unit -->63 UTF-8 bytes<!-- /span -->. Native transport also requires NUL-free bytes. |
| <a id="contract-actors-actor-sandbox"></a>`sandbox` | [Actor sandbox declaration](#contract-actors-sandbox); as defined below | The actor's explicit apply or unapplied declaration; application assessment is reported separately from this request. |
| <a id="contract-actors-actor-equipment"></a>`equipment` | string; as defined below | Equipment role: `selected` uses the selected runner worker; `unentitled` uses the packaged unentitled worker. Omission selects `selected`; present null is refused. Default: `"selected"`. Admitted vocabulary: closed; displayed list: exhaustive: `"selected"`, `"unentitled"`. |
| <a id="contract-actors-actor-required_entitlements"></a>`required_entitlements` | array of string; as defined below | Static and live read-back demand for boolean-true entitlement keys on this actor's executable. Omission supplies an empty list; present null is refused. Default: `[]`. |

<a id="contract-actors-actor-normalize"></a>
##### Normalize actors before launch

[Runner host](#contract-identity-definitions-host) acts at actor-plan admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Binding `a`: entry in `request.actors`. Binding `b`: entry in `request.actors`. Binding `p`: entry in `request.phases`. Association restriction for `b`: `request.actors[b].actor_id` = `request.actors[a].actor_id`. Association restriction for `p`: `request.phases[p].actor_id` = `request.actors[a].actor_id`. Applies when (`request.actors` is present and `request.phases` is present). Uses [Actor equipment selection](#contract-equipment-actor), [Static worker binding](#contract-equipment-binding). Resolve the admitted actor and resource references once into the plan indexes used for execution.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actors-actor-normalize-identity"></a>Actor identity | For each `a`. Requires (`request.actors[a].actor_id` ≠ `""` and number of matching entries for `b` = `1` and UTF-8 byte length of `request.actors[a].actor_id` ≤ `63 UTF-8 bytes` (`actor_id`) and not (`request.actors[a].actor_id` contains `"\u0000"`)). |
| <a id="contract-actors-actor-normalize-role"></a>Known equipment role | For each `a`. Requires (if `request.actors[a].equipment` is present, then `request.actors[a].equipment` is one of `"selected"`, `"unentitled"`). |
| <a id="contract-actors-actor-normalize-visits"></a>At least one declared visit | For each `a`. Requires number of matching entries for `p` > `0`. |
| <a id="contract-actors-actor-normalize-sandbox"></a>Sandbox declaration | For each `a`. Requires (`request.actors[a].sandbox.mode` is one of `"apply"`, `"unapplied"` and (if `request.actors[a].sandbox.mode` = `"apply"`, then `request.actors[a].sandbox.policy` is present) and (if `request.actors[a].sandbox.mode` = `"unapplied"`, then `request.actors[a].sandbox.policy` is absent)). |
| <a id="contract-actors-actor-normalize-entitlement_count"></a>Entitlement list capacity | For each `a`. Requires count of `request.actors[a].required_entitlements` ≤ `64 items` (`actor_required_entitlements`) . |
| <a id="contract-actors-actor-normalize-entitlement_identity"></a>Required entitlement identity | Binding `e`: entry in `request.actors[a].required_entitlements`. Binding `f`: entry in `request.actors[a].required_entitlements`. Association restriction for `f`: `request.actors[a].required_entitlements[f]` = `request.actors[a].required_entitlements[e]`. For each `a`, `e`. Requires (`request.actors[a].required_entitlements[e]` ≠ `""` and number of matching entries for `f` = `1` and UTF-8 byte length of `request.actors[a].required_entitlements[e]` ≤ `255 UTF-8 bytes` (`actor_entitlement_key`) and not (`request.actors[a].required_entitlements[e]` contains `"\u0000"`)). |
| <a id="contract-actors-actor-normalize-failure"></a>Refusal consequence | On failure, performs [Stop children and preserve safe metadata](#contract-refusals-request-consequence) for `request`. |

<a id="contract-actors-actor-fresh"></a>
##### Fresh process and retained policy

[Runner host](#contract-identity-definitions-host), [Worker](#contract-identity-definitions-worker) acts at actor process lifecycle. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Applies when `request.actors` is present. Uses [Application assessment](#contract-actor_evidence-application). Launch one fresh worker for each actor. An apply worker compiles and applies its own declared policy once before its visits; an unapplied worker publishes that declaration and executes under the restrictions already inherited by its process. Keep that worker for its successive visits.

**Support: [source read](#contract-support-grades) for [Actor declaration](#contract-actors-actor) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Evidence limit: Normalization concerns admitted declarations; worker setup and application observations have separate owners. Source: [PWRunnerActors.swift](../runner/Sources/PWRunnerCore/PWRunnerActors.swift): `PWRunnerActor`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`, `actorAdmissionFailure`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `actorApplicationAssessment`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `requestAdmissionFailure`.

<a id="contract-actors-sandbox"></a>
#### Actor sandbox declaration

Record `sandbox`: `PWRunnerActorSandbox`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actors-sandbox-mode"></a>`mode` | string; as defined below | `apply` requires a policy and asks the worker to compile/apply it; `unapplied` requires policy absence or null and records the inherited process restrictions as its starting condition. Admitted vocabulary: closed; displayed list: exhaustive: `"apply"`, `"unapplied"`. |
| <a id="contract-actors-sandbox-policy"></a>`policy` | [Worker policy input](#contract-policy-spec); as defined below | Required non-null policy for `apply`; a non-null policy is refused for `unapplied`. Each apply policy has its own source, parameters, augmentation and capture request. Required when `sandbox.mode` = `"apply"`. Present when `sandbox.mode` = `"apply"`. |

**Support: [source read](#contract-support-grades) for [Actor sandbox declaration](#contract-actors-sandbox) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Source: [PWRunnerActors.swift](../runner/Sources/PWRunnerCore/PWRunnerActors.swift): `PWRunnerActorSandbox`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-actors-phase"></a>
#### Phase declaration

Record `phase`: `PWRunnerPhase`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actors-phase-phase_id"></a>`phase_id` | string; as defined below | Nonempty identifier unique across the specimen's phases and bounded by <!-- span limits.phase_id.value_unit -->63 UTF-8 bytes<!-- /span --> and NUL-free. |
| <a id="contract-actors-phase-actor_id"></a>`actor_id` | string; as defined below | Required known actor owner in the actor form. The ordinary form requires absence or null. |
| <a id="contract-actors-phase-actions"></a>`actions` | array of [Phase action variants](#contract-actors-action); as defined below | Actions in declaration order, including an empty array. Ordinary phases contain paired probes. Actor phases may also contain extension actions. Action identifiers are unique across the whole specimen. |
| <a id="contract-actors-phase-after_termination"></a>`after_termination` | [Termination dependency](#contract-actors-after_termination); as defined below | Optional owned-termination dependency in the actor form. Absence supplies no dependency; present null is refused. The ordinary form refuses a supplied dependency. |

**phase_id.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actors-phase-phase_id-identity"></a>Required phase identity | Requires (`phase.phase_id` ≠ `""` and UTF-8 byte length of `phase.phase_id` ≤ `63 UTF-8 bytes` (`phase_id`) and not (`phase.phase_id` contains `"\u0000"`)). |

<a id="contract-actors-phase-order"></a>
##### Collect, release and advance

[Runner host](#contract-identity-definitions-host) acts at phase scheduler. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Uses [Phase](#contract-identity-definitions-phase), [Prediction](#contract-identity-definitions-prediction). Close the active phase's eligible prediction collection before releasing its actions; run those actions in declaration order. Begin the next phase's collection after the previous phase completes. In the actor form activate one actor at a time while other workers remain parked.

**Support: [source read](#contract-support-grades) for [Collect, release and advance](#contract-actors-phase-order).** The ordering claim requires a complete chain and a unique matching native prediction for the owned worker. Evidence limit: The source owner describes eligibility. Integrated collection/release and mutation observations retain their own execution owners. Source: [PWRunnerStepEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift): `eligibleOrderedStep`.

**Support: [source read](#contract-support-grades) for [Phase declaration](#contract-actors-phase) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Evidence limit: Source support here pins decoded grammar and normalized order. Runtime collection/release evidence belongs to the phase and lifecycle producer rules. Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerPhase`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`, `actorAdmissionFailure`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `admissionFailure`.

<a id="contract-actors-after_termination"></a>
#### Termination dependency

Record `after_termination`: `PWRunnerAfterTermination`.

The declaration names a source actor, while the gate reports the host's owned observation of its ending.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actors-after_termination-actor_id"></a>`actor_id` | string; as defined below | Known actor whose final declared phase occurs earlier than the dependent phase. It must differ from the dependent phase's actor. |

<a id="contract-actors-after_termination-gate"></a>
##### Validate and evaluate the dependency

[Runner host](#contract-identity-definitions-host) acts at actor admission and phase activation. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Applies when `request.actors` is present. Uses [Termination dependency](#contract-actor_evidence-gate). Before activating the dependent actor or collecting its predictions, evaluate the owned natural-reap gate. A failed evaluated gate cancels every remaining scheduled phase.

**Support: [source read](#contract-support-grades) for [Termination dependency](#contract-actors-after_termination) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Evidence limit: Admission source read; the referenced actor-evidence rule owns the runtime gate and global cancellation consequence. Source: [PWRunnerActors.swift](../runner/Sources/PWRunnerCore/PWRunnerActors.swift): `PWRunnerAfterTermination`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-actors-after_termination-declaration"></a>
##### Admit the declared dependency

[Runner host](#contract-identity-definitions-host) acts at actor plan admission before child launch. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.actors`. Binding `q`: entry in `request.phases`. Association restriction for `a`: `request.actors[a].actor_id` = `request.phases[p].after_termination.actor_id`. Association restriction for `q`: `request.phases[q].actor_id` = `request.phases[p].after_termination.actor_id`. For each `p`. Applies when (`request.actors` is present and `request.phases` is present).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actors-after_termination-declaration-source"></a>Source actor and visit | Applies when `request.phases[p].after_termination` is present. Requires (number of matching entries for `a` = `1` and `request.phases[p].after_termination.actor_id` ≠ `request.phases[p].actor_id` and number of matching entries for `q` > `0`). |
| <a id="contract-actors-after_termination-declaration-earlier"></a>Every source visit precedes this phase | For each `p`, `q`. Applies when (`request.phases[p].after_termination` is present and `request.phases[q].actor_id` = `request.phases[p].after_termination.actor_id`). Requires `q` < `p`. |
| <a id="contract-actors-after_termination-declaration-failure"></a>Refusal consequence | On failure, performs [Stop children and preserve safe metadata](#contract-refusals-request-consequence) for `request`. |

**Support: [source read](#contract-support-grades) for [Admit the declared dependency](#contract-actors-after_termination-declaration).** The dependency names a different declared actor whose final declared phase precedes the dependent phase. Source: [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-actors-action"></a>
#### Phase action variants

Record `action`: `PWRunnerPhaseAction`.

An action is one JSON object in the phase actions array. The decoder chooses an extension action when the `extension` key is present; otherwise it decodes a paired probe. A present null extension therefore selects extension decoding and fails its required object.

| Alternative | Record |
| --- | --- |
| `probe` | [Paired probe](#contract-probes-step) |
| `extensionAction` | [Extension action](#contract-extensions-action) |

<a id="contract-actors-action-identity"></a>
##### Action identity

[Runner host](#contract-identity-definitions-host) acts at plan admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Uses [Paired probe](#contract-probes-step), [Extension action](#contract-extensions-action).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actors-action-identity-flat"></a>Flat probe identities | Binding `i`: entry in `request.probe_plan`. Binding `j`: entry in `request.probe_plan`. Association restriction for `j`: `request.probe_plan[j].step_id` = `request.probe_plan[i].step_id`. For each `i`. Applies when (`request.actors` is absent and `request.probe_plan` is present). Requires number of matching entries for `j` = `1`. |
| <a id="contract-actors-action-identity-probe"></a>Phased probe identities | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: ((`request.phases[q].actions[b]` has alternative `"probe"` and `variant(request.phases[q].actions[b], 'probe').step_id` = `variant(request.phases[p].actions[a], 'probe').step_id`) or (`request.phases[q].actions[b]` has alternative `"extensionAction"` and `variant(request.phases[q].actions[b], 'extensionAction').step_id` = `variant(request.phases[p].actions[a], 'probe').step_id`)). For each `p`, `a`. Applies when (`request.phases` is present and `request.phases[p].actions[a]` has alternative `"probe"`). Requires (sum over `q` of number of matching entries for `b` = `1` and (if `request.actors` is present, then `variant(request.phases[p].actions[a], 'probe').step_id` ≠ `""`)). |
| <a id="contract-actors-action-identity-extension"></a>Phased extension identities | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: ((`request.phases[q].actions[b]` has alternative `"probe"` and `variant(request.phases[q].actions[b], 'probe').step_id` = `variant(request.phases[p].actions[a], 'extensionAction').step_id`) or (`request.phases[q].actions[b]` has alternative `"extensionAction"` and `variant(request.phases[q].actions[b], 'extensionAction').step_id` = `variant(request.phases[p].actions[a], 'extensionAction').step_id`)). For each `p`, `a`. Applies when (`request.phases` is present and `request.phases[p].actions[a]` has alternative `"extensionAction"`). Requires (sum over `q` of number of matching entries for `b` = `1` and (if `request.actors` is present, then `variant(request.phases[p].actions[a], 'extensionAction').step_id` ≠ `""`)). |
| <a id="contract-actors-action-identity-failure"></a>Refusal consequence | On failure, performs [Stop children and preserve safe metadata](#contract-refusals-request-consequence) for `request`. |

<a id="contract-actors-action-empty_id"></a>
##### Form-specific action identifiers

Ordinary-form action identifiers may be empty. Actor-form action identifiers must be nonempty so declared actions can be resolved in the actor schedule. UTF-8 capacity, NUL exclusion, uniqueness and membership are separate requirements at their owning admission boundary.

**Support: [check read](#contract-support-grades) for [Form-specific action identifiers](#contract-actors-action-empty_id).** Actor normalization rejects an empty action step_id before constructing its slot map; ordinary meaning admission tests uniqueness without a nonempty condition. Context: Static review of the cited producer and assertion branches. Evidence limit: The corpus emits separate ordinary-empty and actor-empty declaration neighbours through reporting admission; it is constructed reader evidence. Source: [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `requestMeaningFailure`. Check: [ReaderCorpusTests.swift](../runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift): `runReaderCorpusTests`.

**Support: [source read](#contract-support-grades) for [Phase action variants](#contract-actors-action) and its descendants.** The adjacent field meanings and obligations follow the named producer and admission branches. Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerPhaseAction`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `requestMeaningFailure`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-extensions"></a>
### Extension actions and authority custody

The actor form carries explicit issue, transfer, consume and release actions. A reference names a declared resource within this specimen; native results, custody acknowledgements and later file observations each have their own producing boundary.

<a id="contract-extensions-action"></a>
#### Extension action

Record `action`: `PWRunnerExtensionAction`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-extensions-action-step_id"></a>`step_id` | string; as defined below | Unique nonempty identifier across all specimen actions, bounded by <!-- span limits.step_id.value_unit -->63 UTF-8 bytes<!-- /span -->. |
| <a id="contract-extensions-action-extension"></a>`extension` | [Extension operation](#contract-extensions-operation); as defined below | Closed extension operation for the active actor. Its presence selects extension-action decoding; a null object is refused. |

**Support: [source read](#contract-support-grades) for [Extension action](#contract-extensions-action) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Source: [PWRunnerExtension.swift](../runner/Sources/PWRunnerCore/PWRunnerExtension.swift): `PWRunnerExtensionAction`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-extensions-operation"></a>
#### Extension operation

Record `operation`: `PWRunnerExtensionOperation`.

References are nonempty, NUL-free and bounded by <!-- span limits.extension_reference.value_unit -->63 UTF-8 bytes<!-- /span -->.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-extensions-operation-operation"></a>`operation` | string; as defined below | Select the operation and its exact applicable operands. Admitted vocabulary: closed; displayed list: exhaustive: `"issue"`, `"transfer"`, `"consume"`, `"release"`. |
| <a id="contract-extensions-operation-token_ref"></a>`token_ref` | string; as defined below | Required new token reference for issue; required previously assigned token owned by the active actor for transfer. Required when `operation.operation` is one of `"issue"`, `"transfer"`. Present when `operation.operation` is one of `"issue"`, `"transfer"`. |
| <a id="contract-extensions-operation-handle_ref"></a>`handle_ref` | string; as defined below | Required new handle reference for consume; required previously assigned handle owned by the active actor for release. Required when `operation.operation` is one of `"consume"`, `"release"`. Present when `operation.operation` is one of `"consume"`, `"release"`. |
| <a id="contract-extensions-operation-family"></a>`family` | string; as defined below | Required `file` for issue. Required when `operation.operation` = `"issue"`. Present when `operation.operation` = `"issue"`. |
| <a id="contract-extensions-operation-target"></a>`target` | string; as defined below | Required absolute file or directory path for issue, bounded by <!-- span limits.extension_issue_target.value_unit -->1,023 UTF-8 bytes<!-- /span -->. The exact submitted bytes reach native issuance. Required when `operation.operation` = `"issue"`. Present when `operation.operation` = `"issue"`. |
| <a id="contract-extensions-operation-authority"></a>`authority` | string; as defined below | Required `read` or `read_write` for issue, selecting `com.apple.app-sandbox.read` or `com.apple.app-sandbox.read-write`. Required when `operation.operation` = `"issue"`. Present when `operation.operation` = `"issue"`. |
| <a id="contract-extensions-operation-recipient"></a>`recipient` | string; as defined below | Required known actor ID for transfer; may name the active actor itself. Required when `operation.operation` = `"transfer"`. Present when `operation.operation` = `"transfer"`. |
| <a id="contract-extensions-operation-delivery_ref"></a>`delivery_ref` | string; as defined below | Required new delivery reference for transfer; required previously assigned delivery owned by the active recipient for consume. Required when `operation.operation` is one of `"transfer"`, `"consume"`. Present when `operation.operation` is one of `"transfer"`, `"consume"`. |

<a id="contract-extensions-operation-grammar"></a>
##### Operation grammar

| Operation | Required operands | Producing actor and consequence |
| --- | --- | --- |
| `issue` | `family`, `target`, `authority`, `token_ref` | Active actor calls native file issuance once with class selected by authority, exact target and flags zero; assigns the declared token resource. |
| `transfer` | `token_ref`, `recipient`, `delivery_ref` | Token-owning actor publishes a host request for one assigned recipient slot; assigns the delivery resource. |
| `consume` | `delivery_ref`, `handle_ref` | Recipient actor calls native consume on its usable delivered token; assigns the handle resource. |
| `release` | `handle_ref` | Consuming actor calls native release for its candidate handle. |

Each other operand must be absent. A required null operand is missing for this grammar; an extraneous null operand is inapplicable.

<a id="contract-extensions-operation-references"></a>
##### Resolve references and ownership

[Runner host](#contract-identity-definitions-host) acts at whole actor-plan admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Applies when (`request.actors` is present and `request.phases` is present). Construct the token, delivery and handle assignments and their execution indexes once from the admitted ordered resource declarations.

The same token may be transferred to multiple recipients or repeatedly to one recipient using distinct delivery references. A delivery may be consumed repeatedly using distinct handle references. Syntactic ordering establishes which resource is requested; the later resource record establishes what was observed.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-extensions-operation-references-unique_issue"></a>Unique issue assignment | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (`request.phases[q].actions[b]` has alternative `"extensionAction"` and ((`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"issue"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.token_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.token_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"transfer"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.delivery_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.token_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"consume"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.handle_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.token_ref`))). For each `p`, `a`. Applies when (`request.phases[p].actions[a]` has alternative `"extensionAction"` and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"issue"`). Requires sum over `q` of number of matching entries for `b` = `1`. |
| <a id="contract-extensions-operation-references-unique_transfer"></a>Unique transfer assignment | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (`request.phases[q].actions[b]` has alternative `"extensionAction"` and ((`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"issue"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.token_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.delivery_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"transfer"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.delivery_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.delivery_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"consume"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.handle_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.delivery_ref`))). For each `p`, `a`. Applies when (`request.phases[p].actions[a]` has alternative `"extensionAction"` and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"transfer"`). Requires sum over `q` of number of matching entries for `b` = `1`. |
| <a id="contract-extensions-operation-references-unique_consume"></a>Unique consume assignment | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (`request.phases[q].actions[b]` has alternative `"extensionAction"` and ((`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"issue"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.token_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.handle_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"transfer"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.delivery_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.handle_ref`) or (`variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"consume"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.handle_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.handle_ref`))). For each `p`, `a`. Applies when (`request.phases[p].actions[a]` has alternative `"extensionAction"` and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"consume"`). Requires sum over `q` of number of matching entries for `b` = `1`. |
| <a id="contract-extensions-operation-references-producer_transfer"></a>Earlier owned producer for transfer | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (`request.phases[q].actions[b]` has alternative `"extensionAction"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"issue"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.token_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.token_ref` and (`q` < `p` or (`q` = `p` and `b` < `a`)) and `request.phases[q].actor_id` = `request.phases[p].actor_id`). For each `p`, `a`. Applies when (`request.phases[p].actions[a]` has alternative `"extensionAction"` and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"transfer"`). Requires sum over `q` of number of matching entries for `b` = `1`. |
| <a id="contract-extensions-operation-references-producer_consume"></a>Earlier owned producer for consume | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (`request.phases[q].actions[b]` has alternative `"extensionAction"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"transfer"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.delivery_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.delivery_ref` and (`q` < `p` or (`q` = `p` and `b` < `a`)) and `variant(request.phases[q].actions[b], 'extensionAction').extension.recipient` = `request.phases[p].actor_id`). For each `p`, `a`. Applies when (`request.phases[p].actions[a]` has alternative `"extensionAction"` and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"consume"`). Requires sum over `q` of number of matching entries for `b` = `1`. |
| <a id="contract-extensions-operation-references-producer_release"></a>Earlier owned producer for release | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (`request.phases[q].actions[b]` has alternative `"extensionAction"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"consume"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.handle_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.handle_ref` and (`q` < `p` or (`q` = `p` and `b` < `a`)) and `request.phases[q].actor_id` = `request.phases[p].actor_id`). For each `p`, `a`. Applies when (`request.phases[p].actions[a]` has alternative `"extensionAction"` and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"release"`). Requires sum over `q` of number of matching entries for `b` = `1`. |
| <a id="contract-extensions-operation-references-single_release"></a>At most one handle release | Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `b`: entry in `request.phases[q].actions`. Association restriction for `b`: (`request.phases[q].actions[b]` has alternative `"extensionAction"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.operation` = `"release"` and `variant(request.phases[q].actions[b], 'extensionAction').extension.handle_ref` = `variant(request.phases[p].actions[a], 'extensionAction').extension.handle_ref`). For each `p`, `a`. Applies when (`request.phases[p].actions[a]` has alternative `"extensionAction"` and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"consume"`). Requires sum over `q` of number of matching entries for `b` ≤ `1`. |
| <a id="contract-extensions-operation-references-failure"></a>Refusal consequence | On failure, performs [Stop children and preserve safe metadata](#contract-refusals-request-consequence) for `request`. |

<a id="contract-extensions-operation-capacity"></a>
##### Bound the declared resource plan

[Runner host](#contract-identity-definitions-host) acts at pre-child admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Binding `p`: entry in `request.phases`. Binding `a`: entry in `request.phases[p].actions`. Applies when (`request.actors` is present and `request.phases` is present). Uses [Specimen](#contract-request-specimen).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-extensions-operation-capacity-issue"></a>Issue count | Association restriction for `a`: (`request.phases[p].actions[a]` has alternative `"extensionAction"` and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"issue"`). Requires sum over `p` of number of matching entries for `a` ≤ `32 items` (`actor_issues`) . |
| <a id="contract-extensions-operation-capacity-transfer"></a>Transfer count | Association restriction for `a`: (`request.phases[p].actions[a]` has alternative `"extensionAction"` and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"transfer"`). Requires sum over `p` of number of matching entries for `a` ≤ `64 items` (`actor_deliveries`) . |
| <a id="contract-extensions-operation-capacity-consume"></a>Consume count | Association restriction for `a`: (`request.phases[p].actions[a]` has alternative `"extensionAction"` and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"consume"`). Requires sum over `p` of number of matching entries for `a` ≤ `64 items` (`actor_handles`) . |
| <a id="contract-extensions-operation-capacity-release"></a>Release count | Association restriction for `a`: (`request.phases[p].actions[a]` has alternative `"extensionAction"` and `variant(request.phases[p].actions[a], 'extensionAction').extension.operation` = `"release"`). Requires sum over `p` of number of matching entries for `a` ≤ `64 items` (`actor_releases`) . |
| <a id="contract-extensions-operation-capacity-failure"></a>Refusal consequence | On failure, performs [Stop children and preserve safe metadata](#contract-refusals-request-consequence) for `request`. |

<a id="contract-extensions-operation-exec"></a>
##### Exclude exec in participating actors

[Runner host](#contract-identity-definitions-host) acts at actor-plan admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Binding `a`: entry in `request.actors`. Binding `p`: entry in `request.phases`. Binding `x`: entry in `request.phases[p].actions`. Binding `q`: entry in `request.phases`. Binding `y`: entry in `request.phases[q].actions`. Association restriction for `x`: (`request.phases[p].actions[x]` has alternative `"extensionAction"` and (`request.phases[p].actor_id` = `request.actors[a].actor_id` or (`variant(request.phases[p].actions[x], 'extensionAction').extension.operation` = `"transfer"` and `variant(request.phases[p].actions[x], 'extensionAction').extension.recipient` = `request.actors[a].actor_id`))). Association restriction for `y`: (`request.phases[q].actor_id` = `request.actors[a].actor_id` and `request.phases[q].actions[y]` has alternative `"probe"` and `variant(request.phases[q].actions[y], 'probe').attempt.kind` = `"exec"`). Applies when (`request.actors` is present and `request.phases` is present). Uses [Attempt request](#contract-probes-attempt).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-extensions-operation-exec-participants"></a>Participant exec exclusion | For each `a`. Requires (if sum over `p` of number of matching entries for `x` > `0`, then sum over `q` of number of matching entries for `y` = `0`). |
| <a id="contract-extensions-operation-exec-failure"></a>Refusal consequence | On failure, performs [Stop children and preserve safe metadata](#contract-refusals-request-consequence) for `request`. |

**Support: [source read](#contract-support-grades) for [Extension operation](#contract-extensions-operation) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Source: [PWRunnerExtension.swift](../runner/Sources/PWRunnerCore/PWRunnerExtension.swift): `actorOperands`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`, `actorAdmissionFailure`.

<a id="contract-extensions-custody"></a>
#### Custody protocol

Authority payloads occupy bounded native storage assigned to the admitted resource plan. Public records expose references, lengths, framing, status and observations. Token bytes stay in the native custody channels.

<a id="contract-extensions-custody-prepare"></a>
##### Prepare before use

[Runner host](#contract-identity-definitions-host), [Worker](#contract-identity-definitions-worker) acts at host custody preparation before launch and actor setup before application or unapplied declaration. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Applies when `request.actors` is present. Uses [Authority setup account](#contract-equipment-authority_setup). When the admitted resource plan contains a token or delivery, the host attempts to disable core dumps; after that succeeds, it prepares one authority region for every actor and a bounded custody buffer for each token. Failure of this host custody preparation prevents every actor launch. Each actor worker reaching authority setup looks up extension symbols and attempts its own core-dump limit. Required setup publishes ready after mapping and validating its assigned region; a primary failure publishes terminal_required_failure and ends the worker before policy setup. Unneeded authority selects not_required without mapping, including when the core-limit attempt failed. These worker setup operations precede application or the actor's unapplied declaration. A reached extension action reports unavailability for missing required apparatus or symbols.

<a id="contract-extensions-custody-issue"></a>
##### Issue and transfer payload ownership

[Worker](#contract-identity-definitions-worker), [Runner host](#contract-identity-definitions-host) acts at outbound token publication by the issuing worker. Entry: actor worker. Recipient: caller, report reader. Reports: runner reply. Publish a one-shot bounded token only when native issuance returned a non-null payload with length from one through <!-- span limits.extension_token_payload.value_unit -->16,383 bytes<!-- /span -->. Erase the native allocation after copying. Keep the published outbound slot immutable until the host validates, copies or rejects it, erases its payload and acknowledges it.

The slot owns one declared issue. A worker timeout or exit leaves its published bytes available for the host's later copy and erasure. Another issue uses another slot. The native return and host custody acceptance are reported independently.

<a id="contract-extensions-custody-deliver"></a>
##### Acknowledge, compare and settle delivery

[Runner host](#contract-identity-definitions-host), [Worker](#contract-identity-definitions-worker) acts at explicit transfer exchange with the named recipient worker. Entry: actor worker. Recipient: caller, report reader. Reports: runner reply. Require a valid transfer request and held host custody, copy into the assigned recipient slot, obtain recipient framing acknowledgement and compare its complete length and bytes with custody. Set delivered and publish settlement only after accepted acknowledgement and equal bytes. On failure publish the corresponding acknowledgement and withdraw the delivery.

A parked recipient validates framing. A self-transfer also services inbound work while waiting. Consumption requires settled, committed and accepted delivery. Each exchange is bounded by <!-- span limits.actor_exchange_allowance.value_unit -->5,000 milliseconds<!-- /span --> and the remaining actor budget; timeout and clock observations retain their own boundary.

<a id="contract-extensions-custody-source_answer"></a>
##### Observe the source answer

[Runner host](#contract-identity-definitions-host) acts at reply assembly after transfer. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Applies when `request.actors` is present. Set source_acknowledged only when the source action completed and its published transfer status matches the host's nonzero acknowledgement. Preserve late host answers independently of an unpublished or differently completed source action.

<a id="contract-extensions-custody-erase"></a>
##### Erase at declared last use and teardown

[Runner host](#contract-identity-definitions-host), [Worker](#contract-identity-definitions-worker) acts at resource retirement. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Applies when `request.actors` is present. Erase host-private custody at the last declared transfer (or after issue when never transferred) and at teardown. Erase worker-owned inbound payloads after their last declared consume and at normal exit once host settlement transfers ownership. At host teardown erase shared regions only for actors whose termination is established; otherwise detach the host mapping.

A last transfer retires custody even when the recipient is unavailable. Payload erasure is a memory-lifetime action; a native release request and the later access observation are separate operations.

<a id="contract-extensions-custody-native_library"></a>
##### Native extension evidence scope

Native extension issuance, consumption and release observations are scoped to the concrete policy, entitlements, resource, token bytes and macOS build. Host custody records describe the controlled publication, copying and erasure protocol. A release return records that native call; subsequent access is established by the corresponding access observation.

**Support: [source read](#contract-support-grades) for [Native extension evidence scope](#contract-extensions-custody-native_library).** Host transfer observations record custody, copying, recipient acknowledgement and equality separately. Evidence limit: Private-library allocation and opaque token behavior retain the scope of their native observations. Source: [AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift): `serviceTransfer`.

**Support: [source read](#contract-support-grades) for [Custody protocol](#contract-extensions-custody) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Evidence limit: Conditional host/worker setup, host custody service and worker issue/transfer/consume/release have source-read support here. Collected setup-account meanings are owned by the equipment surface. Native private-library behavior remains environment-specific evidence. Source: [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `var authorityRequired: Bool`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `if !plan.authorityRequired { authority = nil; return }`; [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `if let plan = input.authority`; [AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift): `init(plan: AuthorityPlan, actorCount: Int, calls: ChildProcessCalls)`, `serviceOutbound`, `serviceTransfer`, `recordSourceAcknowledgements`, `finish`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `static void prepare_authority`, `if (hdr->actor_mode == PW_ACTOR_MODE_UNAPPLIED)`, `attempt_extension_issue`, `attempt_extension_consume_actor`, `erase_authority`.

<a id="contract-extensions-examples"></a>
#### Extension experiments

These schedules keep declaration, native action, delivered payload and fresh access observations separate.

<a id="contract-extensions-examples-before_during_after"></a>
##### Before, during and after consumption

Declare actors `issuer` and `reader`. Choose the issuer's equipment and sandbox policy to exercise issuance authority, and a reader policy whose baseline denies the chosen path. Use an exact absolute target:

| Phase owner | Actions in declaration order |
| --- | --- |
| `reader` | `read_fresh` before receiving authority |
| `issuer` | issue `token_ref: "t"`, family `file`, authority `read`; transfer `t` to `reader` as `delivery_ref: "d"` |
| `reader` | consume `d` as `handle_ref: "h"`; `read_fresh`; release `h`; `read_fresh` again |

The first read supplies the baseline. The middle read supplies access during this handle's lifetime. The last read supplies a later access observation after the native release call. Compare their actual file identity and content observations. A non-null issue result, delivered bytes, consume result and release result each remain visible even when a read fails.

<a id="contract-extensions-examples-redelegation"></a>
##### Three-actor redelegation

Declare `A`, `B` and `C` with their own sandbox and equipment choices. Read the target freshly in `B` and `C` to establish their baselines. `A` issues a token and transfers it to `B`; `B` consumes that delivery, performs a fresh read, then issues its own token and transfers that token to `C`. `C` consumes its delivery and reads freshly.

The second issuance is `B`'s own native action under its then-current state. Keep the two issue events, two custody/delivery chains, two candidate handles and the readers' file observations distinct. `read_write` may name an absolute directory target; fresh writes or exclusive creation within that directory expose their own file effects.

**Support: [source read](#contract-support-grades) for [Extension experiments](#contract-extensions-examples).** Reply assembly retains extension events, transfer observations and resource accounts by their declared actions. Evidence limit: Native examples require their concrete input and selected-platform observations. Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`.

**Support: [executed](#contract-support-grades) for [Extension experiments](#contract-extensions-examples).** Concrete before/during/after access, the extracted guide JSON example, credited three-actor redelegation and separate directory authority retain native calls, custody/transfer observations and independently identified file effects. Context: Passed signed-CLI cases with their recorded policies, equipment, paths and macOS 26.7.1/25G241 arm64 environment; inspected native results, principal credit, file observations and owned cleanup. Evidence limit: The before/during/after instance splits reader actions across visits. Redelegation includes B/C control-path reads and the retained policies. Directory writes and exclusive creation form a separate experiment. The extracted guide JSON and the guide's full shell workflows have separate execution scopes. Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_extension_issue`, `attempt_file_read_fresh`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`. Check: [check_extensions.py](../tests/suites/witness_contract/check_extensions.py): `run_targets`; [check_extension_redelegation.py](../tests/suites/witness_contract/check_extension_redelegation.py): `chain`; [check_extension_directory.py](../tests/suites/witness_contract/check_extension_directory.py): `run`. Run: `20261111T155411Z_29ef0802; witness_contract/extensions, witness_contract/extension_redelegation and witness_contract/extension_directory`. Build: `Signed candidate build 1335, version 0.3.7, b6ce6d266ff281fafdae44c32061ceff018485bb dirty; development:1445cd80509c983c6894339523f9f13ad08f5e003de4cb29ce1c398527c42f28`.

**Support: [source read](#contract-support-grades) for [Extension experiments](#contract-extensions-examples) and its descendants.** Admission supports these resource chains and native operations. Context: Admission and native-operation source for the teaching schedules. Evidence limit: Native examples are scoped to their recorded policies, equipment, targets and platform. Before/during/after access was observed with an unapplied unentitled issuer and an applied selected subject, with reader actions split across visits. Three-actor redelegation was observed with the retained B/C policies and added control-path reads. Directory read-write authority was exercised separately through fresh writes and exclusive creation. Release results and later access observations retain their individual meanings. Source: [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_extension_issue`, `attempt_file_read_fresh`.

## Delivery to the host

<a id="contract-transport"></a>
### Delivery to the host

The controller, client and host report different boundaries. A client can hold a reservation without invoking execution, invoke execution without receiving a reply, or receive bytes that its controller refuses to interpret.

**Support: [check read](#contract-support-grades) for [Delivery to the host](#contract-transport) and its descendants.** Source defines all imported fields, reservation state transitions, capture gates, preservation and deadline boundaries. Controlled tests establish retry/invocation accounting, connection binding, bound-control admission, byte preservation and delivery-error precedence. Context: Read the cited producer/receiver declarations and branches; check citations identify the assertions read. Evidence limit: The Swift session checks inject clock, scheduler and connection boundaries. Rust process controls use controlled child programs. Live XPC, signed foreign-host nonreceipt and large native replies require separate execution evidence. Source: [runner_client.rs](../controller/src/runner_client.rs): `parse_runner_client_output`, `validate_capture`; [utils.rs](../controller/src/utils.rs): `run_with_stdin`; [PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift): `PWRunnerClientSession`; [PWRunnerReservation.swift](../runner/Sources/PWRunnerCore/PWRunnerReservation.swift): `PWRunnerAdmission`; [PWRunnerTransport.swift](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift): `PWRunnerClientCapture`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `reserveRunner`. Check: [main.swift](../runner/Tests/PWRunnerClientSessionTests/main.swift): `runClientSessionControls`; [ReservationAdmissionTests.swift](../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift): `runReservationAdmissionTests`; [runner_client.rs](../controller/src/runner_client.rs): `binary_reply_after_large_stdin_and_broken_pipe_preserves_delivery_precedence`, `retention_loss_precedes_decode_and_keeps_exact_prefix`.

<a id="contract-transport-authorization"></a>
#### Caller authorization

<a id="contract-transport-authorization-connection"></a>
##### Admit a connection

[Runner host](#contract-identity-definitions-host) checks at NSXPCListener connection acceptance before exporting reservation methods. Entry: cli run, runner verify, direct xpc. Recipient: xpc caller. Reports: connection acceptance. The host reads PWRunnerRequireSignedCaller from its Info.plist as a Boolean; absence or an unavailable Boolean value selects false. When true, obtain caller signing information using the connection PID and the host's own signing information; require both Team IDs to be present and equal. If a nonempty identifier allowlist is configured, also require the caller signing identifier to occur in it. Reject the connection before exporting reservation methods when these checks fail.

`PWRunnerAllowedIdentifiers` is a string array whose members are trimmed and empty members removed. An unavailable or empty resulting list leaves the identifier unrestricted within the Team ID check. The shipped template enables the signed-caller check and lists `pw-runner-client` and `com.policywitness.policy-witness`. An ad-hoc host has no Team ID and fails the enabled check. With the Boolean false, the listener accepts local connections without these signing comparisons; reservation and specimen admission still follow. These signing comparisons and public contract equality are separate checks.

**Support: [source read](#contract-support-grades) for [Caller authorization](#contract-transport-authorization) and its descendants.** The listener applies configured signing-information comparisons before exporting a service; source defaults and shipped settings are distinct. Context: Read Security lookup, Team ID and identifier comparisons, option decoding, listener call order and shipped template. Evidence limit: Source reading. The external-auth wrapper was read, but its delegated setup assertions and a signed refusal matrix are not credited by this owner. Source: [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `authorizedCaller`, `shouldAcceptNewConnection`; [Info.plist](../runner/Services/PWRunner/Info.plist): `PWRunnerRequireSignedCaller`.

<a id="contract-transport-delivery"></a>
#### Reservation and execution

<a id="contract-transport-delivery-acquire"></a>
##### Acquire an unused host

[Runner client](#contract-identity-definitions-client), [Runner host](#contract-identity-definitions-host) acts at reserveRunner control RPC. Entry: cli run, runner verify, direct xpc. Recipient: runner host, runner client. Reports: client capture, control reply. Uses [Exact admission identity](#contract-identity-public-contract). The client has a positive remaining overall allowance and has already begun fewer than <!-- span limits.reservation_attempts.value -->256<!-- /span --> acquisition attempts. Send only the reservation control; the host may grant its one unused slot to that connection. Occupied or transport-lost acquisition may reconnect within the original allowance.

The requested lease is at most <!-- span limits.reservation_lease.value_unit -->5,000 milliseconds<!-- /span --> and at most the remaining overall allowance. Each reservation RPC waits at most <!-- span limits.reservation_rpc_wait.value_unit -->5,000 milliseconds<!-- /span -->; retries wait up to <!-- span limits.reservation_retry_delay.value_unit -->100 milliseconds<!-- /span -->, shortened by the remaining allowance. Every attempt uses a new UUID. A host shares its one slot across authenticated connections. Grant, execution, expiry and abandonment advance that slot toward retirement; expiry or disconnect does not make it reusable.

<a id="contract-transport-delivery-admit_control"></a>
##### Admit the control

[Runner client](#contract-identity-definitions-client) checks at reservation and submission-control reply admission. Entry: cli run, runner verify. Recipient: runner client. Reports: client capture. Uses [Exact admission identity](#contract-identity-public-contract), [Host control reply](#contract-transport-control). Control bytes arrive before a terminal client decision. Bound the control to <!-- span limits.reservation_control_bytes.value_unit -->65,536 bytes<!-- /span -->, compare the contract before decoding descendants, validate host-instance and credential UUID syntax, and associate the callback with the active phase and attempt. Acquisition accepts granted or occupied and checks the echoed attempt and requested lease; submission accepts reservation_refused. On refusal retain control byte count and SHA-256, withhold decoded fields and end with protocol_error.

Both reservation requests and admitted control replies reject unknown keys after identity admission. Optional control fields accept JSON null as absence. Reservation acceptance establishes control admission and ownership of a slot. Peer PID and host-instance strings are assertions supplied by that peer.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-transport-delivery-admit_control-identity"></a>Typed control identity | Requires (`control.host_pid` > `0` and `control.host_pid` ≤ `2147483647` and UTF-8 byte length of `control.host_instance` = `36`). |
| <a id="contract-transport-delivery-admit_control-status"></a>Admitted status forms | Requires `control.status` is one of `"granted"`, `"occupied"`, `"reservation_refused"`. |
| <a id="contract-transport-delivery-admit_control-grant"></a>Granted reservation fields | Requires (if `control.status` = `"granted"`, then (`control.attempt_id` is present and `control.reason` is absent and `control.reservation_id` is present and UTF-8 byte length of `control.reservation_id` = `36` and `control.lease_ms` is present and `control.lease_ms` > `0` and `control.lease_ms` ≤ `5,000 milliseconds` (`reservation_lease`) )). |
| <a id="contract-transport-delivery-admit_control-occupied"></a>Occupied reservation fields | Requires (if `control.status` = `"occupied"`, then (`control.attempt_id` is present and `control.reason` is absent and `control.reservation_id` is absent and `control.lease_ms` is absent)). |
| <a id="contract-transport-delivery-admit_control-refusal"></a>Submission refusal fields | Requires (if `control.status` = `"reservation_refused"`, then (`control.attempt_id` is absent and `control.reservation_id` is absent and `control.lease_ms` is absent and `control.reason` is one of `"wrong"`, `"expired"`, `"absent"`, `"consumed"`, `"clock_error"`)). |

<a id="contract-transport-delivery-invoke"></a>
##### Invoke execution once

[Runner client](#contract-identity-definitions-client) acts at runReservedSpecimen invocation on the granting connection. Entry: cli run, runner verify. Recipient: runner host. Reports: client capture. sets `capture.submission.state` to `"invoked"`. A grant was admitted and a fresh continuous-clock sample is before the original deadline. Record the sampled invocation elapsed time before acquiring/calling the execution proxy. Make one execution invocation and preserve its observation through later error, timeout or refusal; never replay the specimen.

The host checks the connection-bound credential before interpreting the specimen. A transport error after invocation leaves receipt and execution uncertain until independent observations resolve them.

<a id="contract-transport-delivery-deadline"></a>
##### Apply the original allowance

[Controller](#contract-identity-definitions-controller), [Runner client](#contract-identity-definitions-client) acts at client launch, input delivery, acquisition and execution wait. Entry: cli run, runner verify. Recipient: cli caller. Reports: client capture, run envelope, runner verify. The controller invokes its runner client with timeout_ms clamped to at least one millisecond. Create an absolute mach_continuous_time deadline before tool resolution and process spawn and pass it to the client. The client ends on expiry and ignores later callbacks; granting a reservation never resets the deadline.

Continuous time includes machine sleep. Client clock failure ends with `local_error` and `clock_error`, preserves valid earlier readings and any positive invocation, and leaves the final reading absent. The controller drains complete stdout and stderr and waits for the client process; that collection has no independent receiver deadline. Client allowance expiry ends its wait. Host cleanup and worker termination follow their own owners and observations.

<a id="contract-transport-delivery-uncertain"></a>
##### Uncertain invocation example

A capture can contain `acquisition_stop: "granted"`, `submission: {"state":"invoked"}` and `terminal: "xpc_error"` while `runner_reply` is absent. The client crossed its execution-call boundary once; the reply was unavailable. Retrying the specimen would be a new caller decision with possible repeated effects.

<a id="contract-transport-delivery-live_evidence"></a>
##### Transport evidence scope

Controlled client connections establish the observed control-identity refusal and once-only submission behavior. Signed reservation and single-use observations concern their selected service and binaries. A foreign signed host’s receiving boundary, unbound-peer branches and native request/reply faults require their own observations. Native outcomes between the <!-- span limits.client_reply_retention.value_unit -->96,468,992 bytes<!-- /span --> client-retention cap and <!-- span limits.porcelain_frame_bytes.value_unit -->134,217,728 bytes<!-- /span --> frame limit remain unobserved in this account.

**Support: [source read](#contract-support-grades) for [Transport evidence scope](#contract-transport-delivery-live_evidence).** Control admission and submission phase changes preserve the once-only client boundary. Evidence limit: A substituted foreign control is a controlled receive observation. Native cap-interval behavior and a complete native fault matrix remain outside that observation. Source: [PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift): `reservationReply`.

<a id="contract-transport-reservation"></a>
#### Reservation request

Record `reservation`: `PWRunnerReservationRequest`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-transport-reservation-contract"></a>`contract` | string; as defined below | The client’s exact public identity. The host compares it before decoding the rest of this control. |
| <a id="contract-transport-reservation-attempt_id"></a>`attempt_id` | string; as defined below | UUID naming one acquisition attempt, echoed by granted or occupied control responses. |
| <a id="contract-transport-reservation-lease_ms"></a>`lease_ms` | integer; as defined below | Positive requested reservation lifetime in milliseconds; the host caps an accepted lease at 5,000. |

<a id="contract-transport-control"></a>
#### Host control reply

Record `control`: `PWRunnerControlReply`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-transport-control-contract"></a>`contract` | string; required | The host’s compiled public identity, checked by the client before reading the control body. |
| <a id="contract-transport-control-status"></a>`status` | string; required | The host reports `granted`, `occupied`, `invalid_request`, `unsupported_protocol` or `reservation_refused` at the corresponding boundary. |
| <a id="contract-transport-control-attempt_id"></a>`attempt_id` | string; omitted when absent | Acquisition attempt echoed when available; submission-refusal replies omit it. |
| <a id="contract-transport-control-host_pid"></a>`host_pid` | integer; required | Host-reported process identifier. A client-admitted control requires a positive value representable as signed 32-bit. |
| <a id="contract-transport-control-host_instance"></a>`host_instance` | string; required | Host-generated UUID for its admission owner, reported by that host. |
| <a id="contract-transport-control-reservation_id"></a>`reservation_id` | string; omitted when absent | Single-use UUID credential returned by a grant and supplied only on the granting connection’s execution call. Capture projection omits this credential. |
| <a id="contract-transport-control-lease_ms"></a>`lease_ms` | integer; omitted when absent | Lifetime granted in milliseconds. A client accepts a positive value no greater than the requested lease. |
| <a id="contract-transport-control-reason"></a>`reason` | string; omitted when absent | Control refusal diagnostic. Submission refusals use `wrong`, `expired`, `absent`, `consumed` or `clock_error`; invalid/unsupported acquisition controls have their own reason. |

<a id="contract-transport-capture"></a>
#### Client capture

Record `capture`: `PWRunnerClientCapture`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-transport-capture-kind"></a>`kind` | string; required | `runner_client_capture` identifies the client observation record. |
| <a id="contract-transport-capture-contract"></a>`contract` | string; required | Client producer’s public identity. The controller admits it independently of the embedded host reply’s producer. |
| <a id="contract-transport-capture-client_pid"></a>`client_pid` | integer; required | PID reported by the runner-client process; distinct from every host, worker and validator PID. |
| <a id="contract-transport-capture-clock"></a>`clock` | string; required | `mach_continuous_time_ns` names the capture’s continuous-clock readings. |
| <a id="contract-transport-capture-clock_available"></a>`clock_available` | boolean; required | Whether the client retained a usable monotonic continuous clock through its terminal decision. False accompanies a clock_error local failure. |
| <a id="contract-transport-capture-started_continuous_ns"></a>`started_continuous_ns` | integer; omitted when absent | Client session’s initial valid clock reading in nanoseconds, when available. |
| <a id="contract-transport-capture-deadline_continuous_ns"></a>`deadline_continuous_ns` | integer; omitted when absent | Absolute deadline in the same clock coordinate, inherited from the controller or derived locally when invoked directly. |
| <a id="contract-transport-capture-ended_continuous_ns"></a>`ended_continuous_ns` | integer; omitted when absent | Last valid sample at terminal completion; absent after clock failure. |
| <a id="contract-transport-capture-timeout_ms"></a>`timeout_ms` | integer; required | Positive nominal allowance supplied to the client, in milliseconds. The inherited absolute deadline accounts for time already spent before the session starts. |
| <a id="contract-transport-capture-attempts"></a>`attempts` | array of [Acquisition attempt](#contract-transport-acquisition); required | Acquisition attempts in invocation order, with one-based ordinals and unique attempt UUIDs. |
| <a id="contract-transport-capture-acquisition_stop"></a>`acquisition_stop` | string; required | `granted`, `overall_deadline`, `attempt_limit`, `protocol_error` or `local_error`. Granted remains true even if a later pre-invocation stop prevents submission. |
| <a id="contract-transport-capture-submission"></a>`submission` | [Submission observation](#contract-transport-invocation); required | The client’s irreversible execution-invocation observation. |
| <a id="contract-transport-capture-terminal"></a>`terminal` | string; required | One of `runner_reply`, `submission_refused`, `xpc_error`, `xpc_timeout`, `acquisition_failed`, `protocol_error` or `local_error`, naming the client’s final event. |
| <a id="contract-transport-capture-error"></a>`error` | [Client error](#contract-transport-error); omitted when absent | Bounded client-local or XPC diagnostic associated with a failure terminal. |
| <a id="contract-transport-capture-runner_reply"></a>`runner_reply` | [Retained host reply](#contract-transport-retained_reply); omitted when absent | Host-result bytes accepted by the client before its deadline. Presence establishes receipt of the result callback; the controller separately admits the frame and evidence. |
| <a id="contract-transport-capture-submission_refusal"></a>`submission_refusal` | [Retained control observation](#contract-transport-control_observation); omitted when absent | Count/hash and, after control admission, status and reason of a host submission refusal. Malformed control bytes retain only count/hash. |

**timeout_ms.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-transport-capture-timeout_ms-positive"></a>Positive effective allowance | Requires `capture.timeout_ms` > `0`. |

**attempts.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-transport-capture-attempts-bounded"></a>Bounded acquisition count | Requires count of `capture.attempts` ≤ `256 items` (`reservation_attempts`) . |

<a id="contract-transport-acquisition"></a>
#### Acquisition attempt

Record `acquisition`: `PWRunnerAcquisitionAttempt`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-transport-acquisition-ordinal"></a>`ordinal` | integer; required | One-based position in the capture’s acquisition-attempt array. |
| <a id="contract-transport-acquisition-attempt_id"></a>`attempt_id` | string; required | UUID generated for this attempt. The client requires matching acquisition replies. |
| <a id="contract-transport-acquisition-started_elapsed_ms"></a>`started_elapsed_ms` | integer; omitted when absent | Elapsed whole milliseconds from the client session’s initial continuous-clock sample at attempt start, when available. |
| <a id="contract-transport-acquisition-ended_elapsed_ms"></a>`ended_elapsed_ms` | integer; omitted when absent | Elapsed whole milliseconds when this attempt ended, when available; a later clock fault can leave it absent. |
| <a id="contract-transport-acquisition-outcome"></a>`outcome` | string; required | `granted`, `occupied`, `transport_error`, `timeout`, `protocol_error` or `local_error`. Only acquisition transport loss, occupied status and an RPC timeout can lead to another acquisition attempt. |
| <a id="contract-transport-acquisition-control"></a>`control` | [Retained control observation](#contract-transport-control_observation); omitted when absent | Received reservation-control count/hash and any admitted peer fields. |
| <a id="contract-transport-acquisition-error"></a>`error` | [Client error](#contract-transport-error); omitted when absent | Failure diagnostic for this attempt. A granted or occupied attempt instead carries its admitted control. |

<a id="contract-transport-control_observation"></a>
#### Retained control observation

Record `control_observation`: `PWRunnerControlObservation`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-transport-control_observation-bytes_received"></a>`bytes_received` | integer; required | Byte count of the complete received control data, including a control that fails admission. |
| <a id="contract-transport-control_observation-sha256"></a>`sha256` | string (hex); required | SHA-256 of those complete bytes, projected as lowercase hexadecimal. |
| <a id="contract-transport-control_observation-status"></a>`status` | string; omitted when absent | Control status retained only after the client admits the control. |
| <a id="contract-transport-control_observation-host_pid"></a>`host_pid` | integer; omitted when absent | Admitted peer-reported host PID. |
| <a id="contract-transport-control_observation-host_instance"></a>`host_instance` | string; omitted when absent | Admitted peer-reported admission-owner UUID. |
| <a id="contract-transport-control_observation-lease_ms"></a>`lease_ms` | integer; omitted when absent | Admitted grant lifetime when the control carries one. |
| <a id="contract-transport-control_observation-reason"></a>`reason` | string; omitted when absent | Admitted submission-refusal reason when present. |

<a id="contract-transport-invocation"></a>
#### Submission observation

Record `invocation`: `PWRunnerSubmission`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-transport-invocation-state"></a>`state` | string; required | `not_invoked` until the client crosses its execution-call boundary, then permanently `invoked`. |
| <a id="contract-transport-invocation-invoked_elapsed_ms"></a>`invoked_elapsed_ms` | integer; omitted when absent | Elapsed whole milliseconds at that boundary. Absent for not_invoked; clock-failure capture retains only a value actually sampled. |

<a id="contract-transport-retained_reply"></a>
#### Retained host reply

Record `retained_reply`: `PWRunnerReplyCapture`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-transport-retained_reply-bytes_received"></a>`bytes_received` | integer; required | Length of the complete host-result Data received by the client. |
| <a id="contract-transport-retained_reply-bytes_retained"></a>`bytes_retained` | integer; required | Length of its retained prefix, the smaller of bytes_received and <!-- span limits.client_reply_retention.value_unit -->96,468,992 bytes<!-- /span -->. |
| <a id="contract-transport-retained_reply-truncated"></a>`truncated` | boolean; required | True exactly when bytes_retained is smaller than bytes_received. The controller refuses a truncated host frame before structural decoding. |
| <a id="contract-transport-retained_reply-data_base64"></a>`data_base64` | string (base64); required | Exact retained host bytes, kept as bytes internally and rendered as base64 at public JSON projection. |

**truncated.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-transport-retained_reply-truncated-arithmetic"></a>Retention arithmetic | Requires (`retained_reply.truncated` = `retained_reply.bytes_retained` < `retained_reply.bytes_received` and `retained_reply.bytes_retained` ≤ `retained_reply.bytes_received` and `retained_reply.bytes_retained` ≤ `96,468,992 bytes` (`client_reply_retention`) and (if `retained_reply.bytes_received` ≤ `96,468,992 bytes` (`client_reply_retention`) , then `retained_reply.bytes_retained` = `retained_reply.bytes_received`) and (if `retained_reply.bytes_received` > `96,468,992 bytes` (`client_reply_retention`) , then `retained_reply.bytes_retained` = `96,468,992 bytes` (`client_reply_retention`) )). |

**data_base64.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-transport-retained_reply-data_base64-extent"></a>Exact retained byte extent | Requires decoded byte length of `retained_reply.data_base64` = `retained_reply.bytes_retained`. |

**Support: [source read](#contract-support-grades) for [Retained host reply](#contract-transport-retained_reply) and its descendants.** The constructor retains the bounded Data prefix, its original and retained lengths, and their inequality flag. Source: [PWRunnerTransport.swift](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift): `struct PWRunnerReplyCapture`.

<a id="contract-transport-error"></a>
#### Client error

Record `error`: `PWRunnerTransportError`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-transport-error-stage"></a>`stage` | string; required | Boundary at which the client reported the error: `local`, `acquisition` or `submission`. |
| <a id="contract-transport-error-reason"></a>`reason` | string; required | Machine classification for the boundary, including `clock_error`, `encoding_failed`, `input_read_failed`, `xpc_error`, `proxy_type_mismatch`, `rpc_timeout`, `overall_deadline`, `attempt_limit`, `control_too_large`, `unsupported_protocol` and `invalid_control`. The capture reader checks stage/reason/terminal compatibility. |
| <a id="contract-transport-error-domain"></a>`domain` | string; omitted when absent | Native NSError domain when available, bounded to <!-- span limits.client_error_domain.value_unit -->128 UTF-8 bytes<!-- /span --> without splitting a scalar. |
| <a id="contract-transport-error-code"></a>`code` | integer; omitted when absent | Native NSError numeric code when available. Its value belongs to that error domain. |
| <a id="contract-transport-error-message"></a>`message` | string; required | Native debug diagnostic when available, otherwise localized or supplied client text; bounded to <!-- span limits.client_error_message.value_unit -->1,024 UTF-8 bytes<!-- /span --> without splitting a scalar. |
| <a id="contract-transport-error-domain_truncated"></a>`domain_truncated` | boolean; required | Whether the original native domain exceeded its retained-byte allowance. |
| <a id="contract-transport-error-message_truncated"></a>`message_truncated` | boolean; required | Whether the original message exceeded its retained-byte allowance. |

<a id="contract-transport-client"></a>
#### Controller observation of the client process

Record `client`: `rust.RunnerClientRun`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-transport-client-argv"></a>`argv` | array of string; required | Controller-selected client executable and arguments, including connection flags, deadline and stdin-request mode. |
| <a id="contract-transport-client-started_at_unix_ms"></a>`started_at_unix_ms` | integer; required | Controller wall-clock milliseconds immediately before launching and feeding the client. |
| <a id="contract-transport-client-ended_at_unix_ms"></a>`ended_at_unix_ms` | integer; required | Controller wall-clock milliseconds after child-output collection and request-writer completion. Wall-clock reversals remain visible. |
| <a id="contract-transport-client-exit_code"></a>`exit_code` | integer; required | Client process exit code, or 1 when process status supplies no numeric exit code. A zero client exit accompanies delivery of host-result bytes and leaves host outcome to its own report. |
| <a id="contract-transport-client-request_delivery"></a>`request_delivery` | [Request stdin delivery](#contract-transport-request_delivery); null when absent | Controller’s stdin-writer observation for the one held serialized request. |
| <a id="contract-transport-client-transport"></a>`transport` | [Transport alternatives](#contract-transport-transport_value); null when absent | Admitted typed client capture or a rejected retained-byte projection; null when no bytes are retained. |
| <a id="contract-transport-client-transport_admission"></a>`transport_admission` | string; required | `accepted`, `missing`, `unsupported`, `malformed` or `delivery_failed`, naming the controller’s client-capture admission decision. |
| <a id="contract-transport-client-transport_error"></a>`transport_error` | string; null when absent | Diagnostic explaining capture refusal or absence; null for accepted capture. |
| <a id="contract-transport-client-submission"></a>`submission` | string; required | Admitted capture’s invoked/not_invoked state, otherwise `unknown`. |
| <a id="contract-transport-client-runner_reply_error"></a>`runner_reply_error` | string; null when absent | Diagnostic for a truncated, unsupported or malformed embedded host frame. Its exact retained bytes remain in the admitted client capture. |
| <a id="contract-transport-client-stdout_parse_error"></a>`stdout_parse_error` | string; null when absent | Binary frame/schema/producer decoding diagnostic when decoding was attempted. Retention loss is recorded independently before decoding. |
| <a id="contract-transport-client-stdout_truncated"></a>`stdout_truncated` | boolean; required | Whether complete client stdout exceeded the retained prefix allowance. |
| <a id="contract-transport-client-stdout_capture_error"></a>`stdout_capture_error` | string; null when absent | Retention-loss diagnostic; this blocks capture decoding even if the prefix resembles a valid frame. |
| <a id="contract-transport-client-stdout_bytes_received"></a>`stdout_bytes_received` | integer; null when absent | Original stdout byte count after complete process-output collection. |
| <a id="contract-transport-client-stdout_bytes_retained"></a>`stdout_bytes_retained` | integer; null when absent | Retained stdout prefix length, before binary frame admission. |
| <a id="contract-transport-client-stderr_bytes_received"></a>`stderr_bytes_received` | integer; null when absent | Original stderr byte count after complete process-output collection. |
| <a id="contract-transport-client-stderr_bytes_retained"></a>`stderr_bytes_retained` | integer; null when absent | Retained stderr prefix length before diagnostic text conversion. |
| <a id="contract-transport-client-capture_limit_bytes"></a>`capture_limit_bytes` | integer; required | Per-stream prefix-retention allowance, currently <!-- span limits.controller_output.value_unit -->285,212,672 bytes<!-- /span --> for the runner client. |
| <a id="contract-transport-client-stderr"></a>`stderr` | string; required | Retained stderr converted to UTF-8 text with replacement for invalid bytes. |
| <a id="contract-transport-client-stderr_truncated"></a>`stderr_truncated` | boolean; required | Whether complete stderr exceeded its retained prefix allowance. |

<a id="contract-transport-client-admit"></a>
##### Admit client and host observations

[Controller](#contract-identity-definitions-controller) checks at completed client stdout and nested host frame. Entry: cli run, runner verify. Recipient: cli caller. Reports: run envelope, runner verify. Uses [Exact admission identity](#contract-identity-public-contract). The client process and input writer completed collection. Give request-delivery failure precedence; otherwise refuse retention loss, missing capture, unsupported producer/schema or inconsistent capture. Admit the host frame separately only when its retained bytes are complete. Keep raw received bytes at the boundary that received them.

Delivery failure yields controller `tool_error` and exit 2 while retaining available client bytes. Admitted capture semantics check chronology, UUIDs, terminal combinations, control fields and retained lengths. Unsupported or malformed capture withholds submission knowledge and host interpretation. An admitted capture’s `runner_reply` can still be refused as `runner_reply_truncated`, `unsupported_runner_response` or `malformed_runner_response`. Host semantic admission follows structural decoding.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-transport-client-admit-delivery"></a>Input delivery takes precedence | Requires (if (`client.request_delivery` is present and `client.request_delivery.error` is present), then (`client.transport_admission` = `"delivery_failed"` and `client.transport_error` = `client.request_delivery.error` and `client.submission` = `"unknown"` and `client.stdout_parse_error` is absent and `client.runner_reply_error` is absent)). |
| <a id="contract-transport-client-admit-retention"></a>Retention loss precedes decoding | Requires (if (not ((`client.request_delivery` is present and `client.request_delivery.error` is present)) and `client.stdout_capture_error` is present), then (`client.transport_admission` = `"malformed"` and `client.transport_error` = `client.stdout_capture_error` and `client.submission` = `"unknown"` and `client.stdout_parse_error` is absent and `client.runner_reply_error` is absent)). |
| <a id="contract-transport-client-admit-missing"></a>Empty retained capture | Requires (if (not ((`client.request_delivery` is present and `client.request_delivery.error` is present)) and `client.stdout_capture_error` is absent and `client.stdout_bytes_retained` = `0`), then (`client.transport_admission` = `"missing"` and `client.transport_error` = `"runner client produced no capture"` and `client.submission` = `"unknown"` and `client.stdout_parse_error` is absent and `client.runner_reply_error` is absent)). |

**Support: [source read](#contract-support-grades) for [Admit client and host observations](#contract-transport-client-admit).** Completed collection first selects input-delivery error, then retained-output loss, then an empty capture. These paths preserve unknown submission and skip both frame decoders. Source: [runner_client.rs](../controller/src/runner_client.rs): `parse_runner_client_output`.

<a id="contract-transport-request_delivery"></a>
#### Request stdin delivery

Record `request_delivery`: `rust.RequestDelivery`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-transport-request_delivery-bytes_written"></a>`bytes_written` | integer; required | Number of request bytes accepted by the child’s stdin pipe according to the controller’s writes. |
| <a id="contract-transport-request_delivery-error"></a>`error` | string; null when absent | First terminal write error, including a zero-length write. Null records successful delivery by the writer; child receipt remains a separate observation. |

<a id="contract-transport-transport_value"></a>
#### Transport alternatives

Record `transport_value`: `rust.TransportCapture`.

The Rust enum is untagged: JSON contains the chosen alternative’s fields directly. `transport_admission` names which interpretation the controller established.

| Alternative | Record |
| --- | --- |
| `Rejected` | [Rejected client stdout](#contract-transport-rejected) |
| `Typed` | [Client capture](#contract-transport-capture) |

<a id="contract-transport-rejected"></a>
#### Rejected client stdout

Record `rejected`: `rust.TransportCapture.Rejected`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-transport-rejected-format"></a>`format` | string; required | `porcelain` identifies the expected client-output encoding at this collection boundary. |
| <a id="contract-transport-rejected-data_base64"></a>`data_base64` | string (base64); required | Exact retained stdout prefix, projected as base64. It can contain arbitrary, malformed or foreign bytes. |

<a id="contract-wire"></a>
### Response encoding

The host reply and client capture use typed binary frames. The controller projects admitted typed records into public JSON. Saved specimens and reservation controls use their own JSON decoders; validator query records use the separate line protocol below.

**Support: [check read](#contract-support-grades) for [Response encoding](#contract-wire) and its descendants.** The schema owns record identities/tags/types and public projections. Swift writes declared values; Rust and Python independently read their structure. The named controls reject authored scalar/record faults and preserve byte projections. Context: Read the cited producer/receiver declarations and branches; check citations identify the assertions read. Evidence limit: Shared generated tables establish agreement with the declared schema; native malformed-container and host frame-cap coverage remain separate evidence work. Source: [PWPorcelain.swift](../runner/Sources/PWRunnerCore/PWPorcelain.swift): `pwPorcelainValue`; [porcelain.rs](../controller/src/porcelain.rs): `decode_bound`; [generate_porcelain.py](../docs/generate_porcelain.py): `wire_identity`, `rust`; [porcelain.py](../tests/lib/porcelain.py): `class Reader`. Check: [porcelain.rs](../controller/src/porcelain.rs): `native_integer_width_and_boolean_values_are_not_coerced`, `authored_record_faults_are_refused_before_typed_construction`, `list_slots_and_nested_strings_share_one_budget`; [porcelain_codec.py](../tests/suites/source_drift/porcelain_codec.py): `test_homogeneous_lists_sorted_maps_variants_and_depth`.

<a id="contract-wire-frame"></a>
#### Frame grammar

<a id="contract-wire-frame-headers"></a>
##### Frame and value headers

A frame is the four ASCII bytes `PWP1`, 32 raw bytes of the schema SHA-256 fingerprint, then exactly one root value. A value is a one-byte kind, a four-byte unsigned little-endian payload length, and exactly that many payload bytes. Every multi-byte integer in the frame grammar is little-endian. Root, record and field identities are those of the declared wire schema retained with the wire surface’s canonical shape.

<a id="contract-wire-frame-primitives"></a>
##### Primitive payloads

| Kind | Payload and interpretation |
| --- | --- |
| 1 · boolean | Exactly one byte: 0 means false and 1 means true. |
| 2 · signed integer | Exactly eight bytes, two’s-complement signed 64-bit. The declared destination type also constrains its representable range. |
| 3 · unsigned integer | Exactly eight bytes, unsigned 64-bit. The declared destination type also constrains its representable range. |
| 4 · text | Strict UTF-8 bytes of the string; payload length supplies its extent. |
| 5 · bytes | Uninterpreted octets. The owning field supplies their public JSON spelling. |
| 6 · record | Unsigned two-byte record ID, then repeated unsigned two-byte field tag and complete value pairs. Tags are nonzero and strictly increasing. |
| 7 · list | Unsigned four-byte element count, followed by that many complete values of the schema’s element type. |
| 8 · ordered string map | Unsigned four-byte entry count, followed by text-key/value pairs. Keys are unique and strictly increasing by their UTF-8 bytes; values have the declared homogeneous type. |
| 9 · declared variant | Unsigned two-byte case tag, followed by exactly one complete value of that case’s declared type. |

Optional record fields are omitted from the binary record when the producer has no value. A reader requires each nonoptional field and constructs optional absence from missing tags. JSON omission and null are projection choices owned by the field definition.

<a id="contract-wire-frame-variants"></a>
##### Text enums and typed variants

Outcome, state and reason vocabularies travel as text values. Each field's named recipient checks and assessments determine the consequence of a familiar or unfamiliar value. Record references retain their declared record type; equipment references use unsigned indices into their named tables. The declared PWDispositionValue variant has case tag 1 carrying a signed integer and case tag 2 carrying PWRunnerTerminationRequest. Public JSON serializes the selected value directly.

<a id="contract-wire-frame-reader"></a>
##### Retained-byte reader

The Python retained-byte reader admits captured porcelain frames against the
declared wire schema and projects their fields for the repository's evidence
readers. The received bytes remain with their capture owner.

<a id="contract-wire-frame-admit"></a>
##### Exact structural admission

[Controller](#contract-identity-definitions-controller), [Retained-byte reader](#contract-wire-frame-reader) checks at one complete client-capture or host-reply frame. Entry: client stdout, host reply, retained frame. Recipient: controller, report reader. Reports: run envelope. Uses [Exact admission identity](#contract-identity-public-contract), [Wire-schema fingerprint](#contract-identity-other-wire). A complete frame has been retained for the requested root kind. Check frame extent/magic and exact fingerprint, then the expected root and producer identity before descendants. Refuse wrong kinds, unknown records/tags/cases, missing required fields, invalid UTF-8, out-of-range integers, impossible lengths/counts, duplicate or out-of-order fields/keys and trailing bytes.

A complete header naming another fingerprint yields unsupported schema before payload interpretation. A short fingerprint is malformed. The bound reader compares the client’s contract or host producer contract with the caller’s expected public identity; `unbound` cannot supply a positive identity admission. Successful structural decoding establishes the declared typed shape. Native-operation, lifecycle, phase, actor, equipment and custody consistency have separately named semantic readers.

<a id="contract-wire-frame-budgets"></a>
##### Receiver and writer budgets

The frame cap is <!-- span limits.porcelain_frame_bytes.value_unit -->134,217,728 bytes<!-- /span --> and the nesting limit is <!-- span limits.porcelain_nesting.value -->32<!-- /span --> values; the public schema is nonrecursive. Rust shares one <!-- span limits.porcelain_decoded_storage_bytes.value_unit -->134,217,728 bytes<!-- /span --> logical decoded-storage budget across collection slots, strings and byte arrays within each frame; slot charges use the compiled destination type’s size. Capture and embedded host reply are separate frames and separate budgets. Swift bounds encoded values and record growth so a produced frame fits its frame cap. The client retains at most <!-- span limits.client_reply_retention.value_unit -->96,468,992 bytes<!-- /span --> of a host reply. The controller collects client output before applying its <!-- span limits.controller_output.value_unit -->285,212,672 bytes<!-- /span --> per-stream retention cap. These quantities describe distinct allocation, encoding and retention operations; complete-output collection can use more memory than a retained prefix.

<a id="contract-wire-frame-identity"></a>
##### Exact wire identity

The fingerprint is SHA-256 of the compact, object-key-sorted JSON wire identity emitted by `wire_identity`: schema version; records in schema order with ID, name and fields; each field’s tag, public name, type descriptor, null rule and any byte projection; path-form and conditional-null rules; root names mapped to record IDs; and declared variant cases. Local-only fields are omitted. Source paths, mutable/default annotations and descriptive text remain source provenance. Changes to a field’s name, tag, type, optionality, null/projection rule or a newly added optional field change the fingerprint and require exact receiver agreement.

<a id="contract-wire-frame-projection"></a>
##### Public JSON projection

Bytecode, retained host frames and rejected validator context become standard base64. Digests, code-directory hashes, worker identity and fresh-read bytes become lowercase hexadecimal. Path-form fields equal to their input bytes are omitted and listed in `same_as_input`; unavailable forms remain null. Conditional-null fields are carried only when their guard has a value. Other optional fields follow their declared omit/null rule. The generated Rust serializers and independent Python projection apply these rules after typed byte admission.

**Support: [check read](#contract-support-grades) for [Frame grammar](#contract-wire-frame).** Actual decoder and writer boundaries own structural refusal and fallback. Context: Static review of the cited producer and assertion branches. Evidence limit: The huge diagnostic is constructed; writer refusal and its retained minimal frame are distinct from native production or XPC cap-interval observation. Source: [porcelain.rs](../controller/src/porcelain.rs): `pub fn decode`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `pwRunnerReportData`. Check: [porcelain.rs](../controller/src/porcelain.rs): `ordered_maps_require_unique_ascending_keys_in_actual_frames`, `generated_disposition_variant_checks_tag_payload_and_complete_body`, `actual_nested_container_frames_reach_but_do_not_exceed_depth_32`; [ReplyFailureTests.swift](../runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift): `runReplyFailureTests`.

**Support: [executed](#contract-support-grades) for [Frame grammar](#contract-wire-frame).** Literal frames exercise duplicate/descending map keys, impossible or mixed lists, generated byte kind, variant tag/payload/body and actual nested depths 32 and 33. Context: The completed unit/rust.unit case passed with zero recorded system sleep; all five named controls passed in cargo-test-bins.log. Evidence limit: The depth control uses a recursive test wrapper over the production list reader; the public schema is nonrecursive. These are structural decoder controls over constructed bytes. Source: [porcelain.rs](../controller/src/porcelain.rs): `pub fn decode`. Check: [porcelain.rs](../controller/src/porcelain.rs): `ordered_maps_require_unique_ascending_keys_in_actual_frames`, `list_counts_item_kinds_and_trailing_items_refuse_in_actual_frames`, `generated_capture_byte_field_requires_the_byte_kind`, `generated_disposition_variant_checks_tag_payload_and_complete_body`, `actual_nested_container_frames_reach_but_do_not_exceed_depth_32`. Run: `20261111T155411Z_29ef0802`. Source snapshot: `reviewed-inputs sha256:b5298841bceaea7af57843a0e2ab68de2dd2ed85edf21fd07b16ac91d5a8838e (b6ce6d26 dirty)`. Case: `unit/rust.unit`.

**Support: [executed](#contract-support-grades) for [Frame grammar](#contract-wire-frame).** A constructed 134217729-byte attempt diagnostic reaches the actual text guard twice. The independent minimal writer emits 621 bytes with evidence_retained false, empty steps/phases and preserved scalar identity and original summary; Rust and Python read the retained frame. Context: The whole fresh runner-unit case passed with zero recorded system sleep. writer-cap-receipt.json and writer-cap-minimal.pwp join the actual Swift failures to the exact-one Rust and completed Python corpus replay. Evidence limit: The diagnostic is constructed. The observation covers the production writer and fallback; native production of that diagnostic and XPC behavior between retention and frame limits retain separate evidence scopes. Source: [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `pwRunnerReportData`; [PWPorcelain.swift](../runner/Sources/PWRunnerCore/PWPorcelain.swift): `text exceeds byte limit`. Check: [ReplyFailureTests.swift](../runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift): `runReplyFailureTests`; [run_flow.rs](../controller/src/run_flow.rs): `reader_definition_corpus_cross_readers`; [reader_corpus.py](../tests/suites/runner_unit/reader_corpus.py): `replay`. Run: `20261111T162345Z_3d6c7242`. Source snapshot: `reviewed-inputs sha256:af396aadf41ba79a0d072b62d9c3f4ff1df5b5fa30d6c4ff267c53e8437dd51d (b6ce6d26 dirty; replay identity correction)`. Case: `runner_unit/pwrunner_core_unit_executable`.

<a id="contract-wire-validator"></a>
#### Validator query and reply lines

Uses [Accepted validator record](#contract-steps-verdict), [Validator subprocess](#contract-lifecycle-validator), [Rejected validator frame](#contract-lifecycle-decode_fault), [Validator query association](#contract-lifecycle-association_issue).

<a id="contract-wire-validator-query"></a>
##### Query production and native boundary

[Runner host](#contract-identity-definitions-host), [Validator](#contract-identity-definitions-validator) acts at validator --batch PID stdin and sandbox check call. Entry: eligible phase query. Recipient: validator. Reports: validator records. The host has planned an eligible query against the active worker PID. Write one JSON object per line with string step_id, operation and filter_type, and string filter_value for a non-NONE filter. The helper parses that line and calls sandbox_check with SANDBOX_CHECK_NO_REPORT only after grammar and filter admission.

The batch parser accepts a flat object with exactly the recognized key names; each supplied value is a string. NONE requires filter_value absent; other types require it present. Trailing content, raw NUL, invalid UTF-8, invalid escapes, U+0000 and unpaired surrogates are refused. Standard JSON escapes and paired Unicode surrogate escapes decode to their UTF-8 characters. Physical lines exceeding <!-- span limits.validator_query_payload.value -->65,534<!-- /span --> payload bytes are drained and yield one parse_error diagnostic. Blank lines are skipped. A repeated recognized key currently replaces the earlier parsed value.

<a id="contract-wire-validator-emit"></a>
##### Verdict production

[Validator](#contract-identity-definitions-validator) reports at batch stdout after each nonblank input line. Entry: validator batch. Recipient: runner host. Reports: validator records. The helper parsed a physical input line or performed its requested native call. Emit a newline-terminated object with kind sb_api_validator_verdict, integer schema_version 1, step_id and outcome. Native-call records carry operation, filter_type, filter_type_id, filter_value, rc, errno and error; parse/filter refusals carry recovered-or-null step_id and error without inventing native results.

Before each native call the helper clears errno. Native rc 0 is `allow`; rc 1 with errno 0 is `deny`; rc -1 with EINVAL is `unsupported_operation`; other pairs are `error`. Parse errors use `parse_error`; an unsupported filter uses `bad_filter`. Per-line failures continue to the next line, and clean batch EOF returns zero even when individual records report failures.

<a id="contract-wire-validator-read"></a>
##### Host line admission

[Runner host](#contract-identity-definitions-host) checks at validator stdout framing and decoded-record construction. Entry: validator stdout. Recipient: runner host. Reports: validator records, runner reply. Uses [Validator subprocess](#contract-lifecycle-validator). The host has received a validator output prefix within its stream allowance. Split on LF, ignore empty frames and decode a final nonempty fragment. Admit strict UTF-8 JSON objects under per-frame, record-count, primitive-type and string-byte checks. Stop at the first refused frame while preserving earlier complete records and bounded rejection context.

Every admitted object has exact kind, integer schema_version 1, a present string-or-null step_id and nonempty string outcome. Known optional strings and integer fields may be absent or null; Boolean, fractional, string-valued and overflowing numbers cannot supply native integers. Allow/deny require nonempty step_id, operation and filter_type plus integer rc and errno. Every other outcome requires string error. Extra JSON fields and unfamiliar diagnostic outcomes survive in the accepted raw line. Frame size is at most <!-- span limits.validator_reply_frame.value_unit -->8,192 bytes<!-- /span -->; string limits are <!-- span limits.validator_reply_step_id.value_unit -->63 UTF-8 bytes<!-- /span --> for step_id, <!-- span limits.validator_reply_filter_type.value_unit -->63 UTF-8 bytes<!-- /span --> for filter_type, <!-- span limits.validator_reply_outcome.value_unit -->63 UTF-8 bytes<!-- /span --> for outcome, <!-- span limits.validator_reply_operation.value_unit -->127 UTF-8 bytes<!-- /span --> for operation, <!-- span limits.validator_reply_filter_value.value_unit -->1,023 UTF-8 bytes<!-- /span --> for filter_value and <!-- span limits.validator_reply_error.value_unit -->511 UTF-8 bytes<!-- /span --> for error. Rejected context retains at most <!-- span limits.validator_fault_context.value_unit -->256 bytes<!-- /span -->. The validator subprocess account defines this phase collector's total stream and record allowances and subsequent unique-step association.

<a id="contract-wire-validator-duplicate_keys"></a>
##### Repeated native query keys

The native batch parser accepts repeated recognized string keys and keeps the last parsed value for each key. Host query serialization emits each key once. Direct-arrival batch queries retain their own parsing rule at this native boundary.

**Support: [check read](#contract-support-grades) for [Repeated native query keys](#contract-wire-validator-duplicate_keys).** The native batch parser supplies the accepted query values. Context: Static review of the cited producer and assertion branches. Evidence limit: Both member orders are retained in raw query text and checked against independently selected final strings. Source: [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `parse_probe_line`, `run_batch`. Check: [run.sh](../tests/suites/validator_batch_mode/run.sh): `batch_ndjson_roundtrip`.

<a id="contract-wire-validator-example"></a>
##### Native prediction example

For a query with step_id `read`, operation `file-read-data`, filter_type `PATH` and a concrete path, a native return rc 1/errno 0 produces outcome `deny` and error null. That record describes the native prediction for the queried worker and target at the query boundary. The separate attempt observation supplies the operation’s observed effect.

**Support: [check read](#contract-support-grades) for [Validator query and reply lines](#contract-wire-validator) and its descendants.** Constructed byte controls retain valid prefixes and raw native values, refuse invalid UTF-8/numeric types/overflow/oversized fields, and withhold guessed joins for duplicate or unknown IDs. Context: Read C query parser and batch emission, Swift framing/type validation, and the named Swift control body. Evidence limit: Check reading only. The numeric example follows the emitter branch; an observed deny prediction for a particular current host/path requires its own native run. Duplicate query-key behavior is source-read. Source: [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `parse_probe_line`, `emit_verdict`; [ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift): `decodeValidatorFrames`, `validatorStructureError`. Check: [ValidatorEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift): `runValidatorEvidenceTests`.

<a id="contract-wire-standalone"></a>
#### Direct validator commands

Each shipped service contains `Contents/MacOS/sb_api_validator`. Direct invocation accepts `[--json] PID [operation filter_type [filter_value]]`; `--batch PID` selects the line protocol above. The leading flags select distinct modes and are not combined.

<a id="contract-wire-standalone-status"></a>
##### Parse and report a PID

[Validator](#contract-identity-definitions-validator) acts at direct argv admission. Entry: validator status, validator single query, validator batch. Recipient: helper caller. Reports: validator status, validator single result, validator error. The first positional value is consumed by base-10 strtol and is positive and at most 1,073,741,824, with no trailing bytes. Accept that numeric PID. With no further arguments in direct mode, print ok or the JSON status object and exit zero. With operation arguments, continue to filter admission; batch takes no further positional arguments.

The PID-only branch performs parsing and reaches no sandbox_check call or process-existence check. Missing arguments before a PID produce stderr and exit 2, including a bare --json. An invalid supplied PID produces stderr in plain mode or pid_missing in JSON mode, with pid -1 and exit 2.

<a id="contract-wire-standalone-filters"></a>
##### Choose a native filter

Direct and batch queries share a filter-name resolver: NONE is 0, PATH is 1, GLOBAL_NAME is 2 and LOCAL_NAME is 3. Conditional SDK names are APPLEEVENT_DESTINATION, RIGHT_NAME, PREFERENCE_DOMAIN, KEXT_BUNDLE_ID, INFO_TYPE, NOTIFICATION_TYPE, XPC_SERVICE_NAME, NVRAM_VARIABLE and POSIX_IPC_NAME when their corresponding sandbox filter macros exist at compilation. `RAW:<number>` uses base-10 strtol, accepts a fully consumed value from 0 through 255 and supplies that numeric filter ID. These accepted helper names are distinct from the host planner’s eligible query pairs.

<a id="contract-wire-standalone-query"></a>
##### Run one native query

[Validator](#contract-identity-definitions-validator) acts at direct sandbox check call and stdout. Entry: validator single query. Recipient: helper caller. Reports: validator single result, validator error. An operation and recognized filter are supplied. Numeric filter ID zero requires no filter-value argument; every other ID requires exactly one. Clear errno, invoke sandbox_check for the supplied PID with SANDBOX_CHECK_NO_REPORT, and report the native rc and errno. Plain output is rc=<value> errno=<value> and exits zero for rc zero, one otherwise. JSON mode emits its single-result object and exits zero after the call, whatever its native result.

CLI filter/argument refusal exits 2. The native string printer escapes quotes, backslashes and control bytes; remaining argument bytes pass through unchanged.

**Support: [executed](#contract-support-grades) for [Run one native query](#contract-wire-standalone-query).** RAW empty/zero direct value arity, no-report native-call flag, and direct JSON/plain versus batch output/exit for six supplied rc/errno pairs; the shipped helper separately observes selected allow, deny and unsupported-operation results against its owned native target. Context: Read the production parser/emitter and exact assertions; inspected both completed validator_batch_mode case receipts, retained argv/input/output and control.log in run 20261111T155411Z_29ef0802. Evidence limit: The return matrix substitutes the native call in a production-source build. Shipped-helper observations use the selected target and macOS build; PID-only admission, other argument errors and invalid-UTF-8 direct arguments retain source support. The overall default run has a separate reader-corpus case failure. Source: [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `int main(`, `resolve_filter_type_id`. Check: [no_report.c](../tests/fixtures/validator/no_report.c): `raw_zero`, `result_meaning`; [run.sh](../tests/suites/validator_batch_mode/run.sh): `batch_ndjson_roundtrip`. Run: `20261111T155411Z_29ef0802; validator_batch_mode/predictions_do_not_report and validator_batch_mode/batch_ndjson_roundtrip`. Source snapshot: `controller/tools/sb_api_validator/sb_api_validator.c sha256 93318c0dd70ce26a0113fc0ab5fb676cf91938eda1bf2cfce3afc8d50c8ae4c6; tests/fixtures/validator/no_report.c sha256 d82d36711d15c824085a327f3dc268263f144949d8582c7ddc4682277d3a4e51; tests/suites/validator_batch_mode/run.sh sha256 da7ae5d7825202e974accd01149daff914c194a7d69d5af7bbc9c7d4a6e57897`. Build: `Selected signed candidate build 1335, version 0.3.7, commit b6ce6d266ff281fafdae44c32061ceff018485bb dirty; public identity development:1445cd80509c983c6894339523f9f13ad08f5e003de4cb29ce1c398527c42f28`.

<a id="contract-wire-standalone-meaning"></a>
##### Direct and batch validator meanings

Direct JSON denied means native rc is nonzero, including a native error; successful direct JSON reporting exits 0. Plain output exits 0 or 1 from native rc. Batch deny requires rc 1 and errno zero and retains its diagnostic classifications. An empty RAW suffix resolves to numeric zero. Direct numeric-zero filters take no value; batch treats the spelling NONE as valueless, so RAW:0 carries a value that the zero-filter native call leaves unused. Direct argv uses C strings; batch validates its JSON strings as UTF-8.

**Support: [check read](#contract-support-grades) for [Direct and batch validator meanings](#contract-wire-standalone-meaning).** Direct and batch parsing and native-result projection retain operation-specific rules. Context: Static review of the cited producer and assertion branches. Evidence limit: The controls compare selected shipped-helper RAW-zero, duplicate and native error/deny cases; status and encoding branches retain their own source support. Source: [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `resolve_filter_type_id`. Check: [run.sh](../tests/suites/validator_batch_mode/run.sh): `batch_ndjson_roundtrip`.

**Support: [source read](#contract-support-grades) for [Direct validator commands](#contract-wire-standalone) and its descendants.** Direct argv branches establish parsing, mode-specific output, filter resolution and exit selection; the build inventory establishes the shipped helper location. Context: Read complete main/parse/filter/error-printer branches and the signed app helper inventory. Evidence limit: PID-only admission, conditional filter names and raw C-string encoding are supported by the cited source branches. The query controls cover their selected RAW-zero and result/exit branches. Source: [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `int main(`, `parse_pid`, `resolve_filter_type_id`, `print_error`; [build.json](../docs/build.json): `sig_validator`.

<a id="contract-wire-standalone_status"></a>
#### Direct PID status

Record `standalone_status`: `ValidatorDirectStatus`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-wire-standalone_status-kind"></a>`kind` | string; required | sb_api_validator_status identifies the PID-only JSON branch. |
| <a id="contract-wire-standalone_status-schema_version"></a>`schema_version` | integer; required | Version 1 of this direct JSON object. |
| <a id="contract-wire-standalone_status-pid"></a>`pid` | integer; required | Positive PID accepted by argument parsing. |
| <a id="contract-wire-standalone_status-error"></a>`error` | JSON value; required | Always null on this status branch. |

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
#### Direct native result

Record `standalone_result`: `ValidatorDirectResult`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-wire-standalone_result-kind"></a>`kind` | string; required | sb_api_validator_result identifies one direct native query. |
| <a id="contract-wire-standalone_result-schema_version"></a>`schema_version` | integer; required | Version 1 of this direct JSON object. |
| <a id="contract-wire-standalone_result-pid"></a>`pid` | integer; required | Parsed PID passed to sandbox_check. |
| <a id="contract-wire-standalone_result-operation"></a>`operation` | string; required | Operation argument passed to the native call. |
| <a id="contract-wire-standalone_result-filter_type"></a>`filter_type` | string; required | Supplied symbolic or RAW filter spelling. |
| <a id="contract-wire-standalone_result-filter_type_id"></a>`filter_type_id` | integer; required | Resolved numeric filter ID before OR with SANDBOX_CHECK_NO_REPORT. |
| <a id="contract-wire-standalone_result-filter_value"></a>`filter_value` | string; null when absent | Filter string passed for a nonzero ID; null for ID zero. |
| <a id="contract-wire-standalone_result-extra"></a>`extra` | JSON value; required | Always null in this producer. |
| <a id="contract-wire-standalone_result-rc"></a>`rc` | integer; required | Exact native sandbox_check return. |
| <a id="contract-wire-standalone_result-errno"></a>`errno` | integer; required | Native errno after clearing it before the call. |
| <a id="contract-wire-standalone_result-allowed"></a>`allowed` | boolean; required | True exactly when native rc is zero. |
| <a id="contract-wire-standalone_result-denied"></a>`denied` | boolean; required | True exactly when native rc is nonzero, including native errors. |

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
| <a id="contract-wire-standalone_result-filter_value-numeric"></a>Numeric filter argument relation | Requires ((if `standalone_result.filter_type_id` = `0`, then `standalone_result.filter_value` is absent) and (if `standalone_result.filter_type_id` ≠ `0`, then `standalone_result.filter_value` is present)). |

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
#### Direct argument error

Record `standalone_error`: `ValidatorDirectError`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-wire-standalone_error-kind"></a>`kind` | string; required | sb_api_validator_error identifies a JSON-mode argument refusal. |
| <a id="contract-wire-standalone_error-schema_version"></a>`schema_version` | integer; required | Version 1 of this direct JSON object. |
| <a id="contract-wire-standalone_error-error"></a>`error` | string; required | pid_missing, missing_args, bad_filter, unexpected_filter_value_for_none, missing_filter_value or unexpected_extra_args names the reached refusal. |
| <a id="contract-wire-standalone_error-pid"></a>`pid` | integer; omitted when absent | Parsed PID, or -1 for pid_missing; omitted for bad_filter. |
| <a id="contract-wire-standalone_error-filter"></a>`filter` | string; omitted when absent | Rejected filter spelling for bad_filter; omitted for other errors. |

## The host's report

<a id="contract-policy-check_data"></a>
### Compiler-helper data

Record `check_data` locations: `helper_envelope.data`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-policy-check_data-policy_format"></a>`policy_format` | string; required | The decoded policy format, including a refused format. |
| <a id="contract-policy-check_data-policy_sha256"></a>`policy_sha256` | string; null when absent | SHA-256 of the admitted source's UTF-8 bytes; null when input admission failed before hashing. |
| <a id="contract-policy-check_data-macos_build_version"></a>`macos_build_version` | string; null when absent | The host macOS build observed by the helper, or null when unavailable. |
| <a id="contract-policy-check_data-params_present"></a>`params_present` | boolean; required | True when params decoded as a map, including an empty map; false for omission or null. |
| <a id="contract-policy-check_data-params_count"></a>`params_count` | integer; required | Number of decoded parameter-map entries. |
| <a id="contract-policy-check_data-compile"></a>`compile` | [Last native compile stage](#contract-policy-compile); null when absent | The last native stage attempted and its result. Null means the helper refused the input before native setup or compilation. |
| <a id="contract-policy-check_data-import_inventory"></a>`import_inventory` | [Literal import inventory](#contract-policy-imports); null when absent | The helper's literal-import walk performed before native compilation. Null means admission prevented the walk; an empty records list is a performed walk with no import records. |

<a id="contract-policy-check_data-run_compile"></a>
#### Inventory, compile and report

[Compiler helper](#contract-identity-definitions-helper) acts at admitted diagnostic compilation. Entry: standalone helper, controller helper stdin. Recipient: caller, report reader. Reports: helper envelope. Inventory imports, prepare native parameters when needed, then compile the admitted source. Preserve the inventory even when native compilation fails.

The helper compiles in its own process. The fallback capture reports this independent attempt alongside the transport result and any retained worker evidence.

**Support: [source read](#contract-support-grades) for [Compiler-helper data](#contract-policy-check_data) and its descendants.** The adjacent field meanings and operations follow the named implementation. Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `check`, `CheckData`.

<a id="contract-policy-check_data-verdict"></a>
#### Select the helper verdict

[Compiler helper](#contract-identity-definitions-helper) reports at last native-stage record to helper result. Entry: standalone helper, controller helper stdin. Recipient: report reader. Reports: helper envelope. Select the first matching case in the listed order. Applies when `helper_envelope.data.compile` is present.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-policy-check_data-verdict-ok"></a>1. Successful last stage | `helper_envelope.data.compile.ok` | sets `helper_envelope.result.ok` to `true`, sets `helper_envelope.result.exit_code` to `0`, sets `helper_envelope.result.normalized_outcome` to `"ok"`, sets `helper_envelope.result.error` to `null`. |
| <a id="contract-policy-check_data-verdict-compile_diagnostic"></a>2. Compile failure with a diagnostic | (`helper_envelope.data.compile.stage` = `"compile"` and `helper_envelope.data.compile.error` is present) | sets `helper_envelope.result.ok` to `false`, sets `helper_envelope.result.exit_code` to `1`, sets `helper_envelope.result.normalized_outcome` to `"compile_error"`, sets `helper_envelope.result.error` to `helper_envelope.data.compile.error`. |
| <a id="contract-policy-check_data-verdict-compile_no_diagnostic"></a>3. Compile failure without a diagnostic | `helper_envelope.data.compile.stage` = `"compile"` | sets `helper_envelope.result.ok` to `false`, sets `helper_envelope.result.exit_code` to `1`, sets `helper_envelope.result.normalized_outcome` to `"compile_error"`, sets `helper_envelope.result.error` to `"sandbox_compile_string returned NULL without a diagnostic"`. |
| <a id="contract-policy-check_data-verdict-setup"></a>4. Native setup failure | `true` | sets `helper_envelope.result.ok` to `false`, sets `helper_envelope.result.exit_code` to `1`, sets `helper_envelope.result.normalized_outcome` to `"setup_error"`, sets `helper_envelope.result.error` to `helper_envelope.data.compile.error`. |

**Support: [source read](#contract-support-grades) for [Select the helper verdict](#contract-policy-check_data-verdict).** The helper selects its result from the last native-stage record. Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `verdict`.

<a id="contract-policy-check_data-metadata"></a>
#### Decoded policy metadata

[Compiler helper](#contract-identity-definitions-helper) reports at decoded helper input to report metadata. Entry: standalone helper, controller helper stdin. Recipient: report reader. Reports: helper envelope. sets `check_data.policy_format` to `helper_request.policy.format`, sets `check_data.params_present` to `helper_request.policy.params` is present.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-policy-check_data-metadata-present"></a>Present parameter map | Applies when `helper_request.policy.params` is present. sets `check_data.params_count` to count of `helper_request.policy.params`. |
| <a id="contract-policy-check_data-metadata-absent"></a>Absent parameter map | Applies when `helper_request.policy.params` is absent. sets `check_data.params_count` to `0`. |

**Support: [source read](#contract-support-grades) for [Decoded policy metadata](#contract-policy-check_data-metadata).** Metadata retains decoded format and optional-map presence/count, including an empty present map. Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `check`.

<a id="contract-policy-compile"></a>
### Last native compile stage

Record `compile` locations: `helper_envelope.data.compile`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-policy-compile-stage"></a>`stage` | string; required | Last native stage attempted: parameter object creation, one parameter assignment, or source compilation. `compile` means required parameter setup completed. Admitted vocabulary: closed; displayed list: exhaustive: `"params_create"`, `"param_set"`, `"compile"`. |
| <a id="contract-policy-compile-ok"></a>`ok` | boolean; required | Whether that last stage supplied the helper's successful native result. Compilation succeeds only when the profile is non-null and the native diagnostic pointer is null. |
| <a id="contract-policy-compile-error"></a>`error` | string; null when absent | At setup failure, helper text identifies the call and, for parameter assignment, the key. At compile, copy the native diagnostic as lossily decoded UTF-8, preserving an empty diagnostic as an empty string. A null profile with no diagnostic leaves this field null and supplies a separate explanatory summary. |

<a id="contract-policy-compile-release"></a>
#### Release native resources

[Compiler helper](#contract-identity-definitions-helper) acts at native compile-call completion. Entry: standalone helper, controller helper stdin. Recipient: caller, report reader. Reports: helper envelope. Free every acquired parameter object, returned profile and native error buffer. Treat a non-null diagnostic as compile failure even when a profile was returned. Preserve the native diagnostic separately from the helper summary.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-policy-compile-release-diagnostic"></a>Retained compile diagnostic | Requires (if (`compile.stage` = `"compile"` and `compile.error` is present), then `compile.ok` = `false`). An empty native diagnostic remains present and therefore also rules out helper compile success. |

**Support: [source read](#contract-support-grades) for [Last native compile stage](#contract-policy-compile) and its descendants.** The adjacent field meanings and operations follow the named implementation. Evidence limit: Native wrapper branches read. Scripted native-result controls and platform execution still need to be joined as graded owners. Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `compile_with`, `CompileRecord`.

<a id="contract-policy-imports"></a>
### Literal import inventory

Record `imports`: `rust.ImportInventory`.

Absolute import names are checked as supplied. Other names are sought first under `/System/Library/Sandbox/Profiles`, then `/usr/share/sandbox`, with the literal name unchanged. The resolver follows literal imports recursively; an unevaluable import argument, unreadable/nonregular file or invalid UTF-8 scan input records an incomplete inventory.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-policy-imports-records"></a>`records` | array of [One import observation](#contract-dossier-import_record); required | Observed import records sorted by resolved path (empty for unresolved), then literal name. Each resolved file is opened once, checked as a regular file, and its held bytes are both hashed and scanned. Canonical resolved files and unresolved names are deduplicated. |
| <a id="contract-policy-imports-truncated"></a>`truncated` | boolean; required | True when the walk reached its <!-- span limits.helper_import_depth.value_unit -->8 levels<!-- /span --> depth bound or <!-- span limits.helper_import_count.value_unit -->64 records<!-- /span --> record bound; retained records describe the partial walk. |
| <a id="contract-policy-imports-cycle"></a>`cycle` | array of string; null when absent | First cycle found by revisiting a canonical path already in the active traversal chain, reported in literal import-name order. Null means the walk found no cycle. |
| <a id="contract-policy-imports-policy_closure_sha256"></a>`policy_closure_sha256` | string; required | SHA-256 of source bytes, byte 0x1F, then newline-joined sorted strings of each successfully hashed resolved path, one space and its SHA-256. The separator is included for an empty inventory. Failed imports remain error records and contribute no path/hash line. |

<a id="contract-policy-imports-holds"></a>
#### Separate reads and their identities

[Controller](#contract-identity-definitions-controller), [Compiler helper](#contract-identity-definitions-helper), [Worker](#contract-identity-definitions-worker) acts at policy preparation and import reads. Entry: cli run, standalone helper, xpc execute. Recipient: caller, report reader. Reports: run envelope, helper envelope, runner reply. Bind each digest to the bytes held by its producing read. The controller dossier walk, fallback helper walk and worker native compiler perform their own reads. Preserve import errors and bounds beside each inventory.

Files named by imports can change between these independent reads. A literal inventory describes the producer's walk; the worker compiled-profile receipt has its own observation boundary.

<a id="contract-policy-imports-native_import_agreement"></a>
#### Literal import evidence scope

The inventory walks literal imports using its documented two-directory search order and records the bytes read during that walk. The directory order is a platform convention. Native compilation examples establish their selected literal imports; collision precedence, macro-generated dependencies and files changing between independent reads retain their own evidence limits.

**Support: [source read](#contract-support-grades) for [Literal import evidence scope](#contract-policy-imports-native_import_agreement).** The scanner follows IMPORT_SEARCH_PATHS and records each resolved file read. Evidence limit: The source records that collision precedence was not established by the cited platform exploration. Source: [sbpl_imports.rs](../controller/src/sbpl_imports.rs): `resolve_import_path`.

**Support: [source read](#contract-support-grades) for [Literal import inventory](#contract-policy-imports) and its descendants.** The adjacent field meanings and operations follow the named implementation. Evidence limit: Full inventory traversal and hashing implementation read. Native search-order observations are inherited from the source comments, not reproduced here. Source: [sbpl_imports.rs](../controller/src/sbpl_imports.rs): `resolve_imports`, `read_regular_file`, `compute_closure_hash`; [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `ImportInventory`.

<a id="contract-policy-fallback"></a>
### Fallback helper capture

Record `fallback`: `rust.PolicyCheckCapture`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-policy-fallback-status"></a>`status` | string; required | Capture result, or the exact normalized_outcome from a supported helper envelope. Current capture statuses are unavailable, capture_error, parse_error, tool_error and invalid_reply. Admitted vocabulary: open; displayed list: illustrative: `"unavailable"`, `"capture_error"`, `"parse_error"`, `"tool_error"`, `"invalid_reply"`, `"ok"`, `"compile_error"`, `"setup_error"`, `"bad_request"`, `"policy_too_large"`. Unfamiliar values: A nonempty unfamiliar helper outcome is copied when kind and public identity are supported; its meaning remains producer-supplied. |
| <a id="contract-policy-fallback-tool_exit_code"></a>`tool_exit_code` | integer; required | Helper process exit code, or the capture's fallback value when unavailable. |
| <a id="contract-policy-fallback-envelope"></a>`envelope` | JSON value; null when absent | Whole parsed helper envelope retained unchanged when stdout parsed, including unsupported envelopes. Null means no retained parsed object. |
| <a id="contract-policy-fallback-stdout_raw"></a>`stdout_raw` | string; null when absent | Retained textual stdout used for capture diagnosis. |
| <a id="contract-policy-fallback-stdout_parse_error"></a>`stdout_parse_error` | string; null when absent | Parse diagnosis when retained stdout could not be decoded as the helper JSON value. |
| <a id="contract-policy-fallback-stdout_truncated"></a>`stdout_truncated` | boolean; required | Whether stdout retention truncated the child's output; truncation prevents interpreting a parsed prefix as the complete reply. |
| <a id="contract-policy-fallback-stdout_capture_error"></a>`stdout_capture_error` | string; null when absent | Capture loss diagnosis, which takes precedence over parsing and helper interpretation. |
| <a id="contract-policy-fallback-stdout_bytes_received"></a>`stdout_bytes_received` | integer; null when absent | Count of stdout bytes observed by capture. |
| <a id="contract-policy-fallback-stdout_bytes_retained"></a>`stdout_bytes_retained` | integer; null when absent | Count of stdout bytes retained within the capture limit. |
| <a id="contract-policy-fallback-stderr_bytes_received"></a>`stderr_bytes_received` | integer; null when absent | Count of stderr bytes observed by capture. |
| <a id="contract-policy-fallback-stderr_bytes_retained"></a>`stderr_bytes_retained` | integer; null when absent | Count of stderr bytes retained within the capture limit. |
| <a id="contract-policy-fallback-capture_limit_bytes"></a>`capture_limit_bytes` | integer; required | Per-stream retention limit, <!-- span limits.policy_helper_output.value_unit -->8,388,608 bytes<!-- /span -->. |
| <a id="contract-policy-fallback-stderr"></a>`stderr` | string; required | Retained stderr text, including diagnostic output when the helper produced no envelope. |
| <a id="contract-policy-fallback-stderr_truncated"></a>`stderr_truncated` | boolean; required | Whether stderr exceeded its retained capture capacity. |

<a id="contract-policy-fallback-classify"></a>
#### Fallback eligibility and classification

[Controller](#contract-identity-definitions-controller) acts at admitted client capture after xpc error. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Invoke the fallback helper when client transport admission is accepted, request delivery has no error, and the admitted client capture has terminal xpc_error. Deliver the held request on stdin. Report launch or delivery failure as unavailable; only after successful launch and delivery apply capture_error, parse_error, absent-output tool_error, then raw envelope identity/kind validation. Copy a supported envelope's nonempty outcome into status.

Support requires kind `sbpl_check`, the current non-unbound `build.contract`, and a nonempty string normalized_outcome. The capture preserves the envelope and helper process exit independently; compiler observations retain their own process owner.

**Support: [check read](#contract-support-grades) for [Fallback helper capture](#contract-policy-fallback) and its descendants.** The adjacent field meanings and operations follow the named implementation. Context: Review of the named producer branches. Evidence limit: Capture parsing, fallback eligibility and call sites, supported-outcome control and constructed fallback-selection control read; no execution credited. The malformed actor-mode policy-object path is source-read. Detailed text-byte capture mechanics are shared with the transport surface. Source: [policy_check.rs](../controller/src/policy_check.rs): `parse_policy_check_output`, `supported_outcome`; [run_flow.rs](../controller/src/run_flow.rs): `fallback_policy_check`, `let actor_policies:`; [runner_client.rs](../controller/src/runner_client.rs): `pub fn fallback_eligible`. Check: [policy_check.rs](../controller/src/policy_check.rs): `supported_outcomes_are_copied_into_status_without_a_second_verdict`; [run_flow.rs](../controller/src/run_flow.rs): `fallback_compilation_is_requested_only_for_an_admitted_xpc_error`.

<a id="contract-policy-actor_check"></a>
### Per-actor fallback capture

Record `actor_check`: `rust.ActorPolicyCheck`.

When fallback is eligible, the controller checks each actor carrying a policy object in request order, sending a separate policy-only request. A malformed mode remains a host-admission question; the controller collected these policy objects before host execution.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-policy-actor_check-actor_id"></a>`actor_id` | string; null when absent | Actor label copied from the policy-bearing actor declaration when it is a string; null otherwise. |
| <a id="contract-policy-actor_check-policy_check"></a>`policy_check` | [Fallback helper capture](#contract-policy-fallback); required | Independent helper capture for this actor's selected policy object. |

**Support: [source read](#contract-support-grades) for [Per-actor fallback capture](#contract-policy-actor_check) and its descendants.** The adjacent field meanings and operations follow the named implementation. Source: [run_flow.rs](../controller/src/run_flow.rs): `actor_fallback_checks`, `actor_policies`.

<a id="contract-extensions-event"></a>
### Extension event

Record `event`: `PWRunnerExtensionEvent`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-extensions-event-phase_id"></a>`phase_id` | string; required | Declared phase containing the action. |
| <a id="contract-extensions-event-step_id"></a>`step_id` | string; required | Declared action identifier. |
| <a id="contract-extensions-event-operation"></a>`operation` | string; required | Requested issue, transfer, consume or release operation. |
| <a id="contract-extensions-event-token_ref"></a>`token_ref` | string; omitted when absent | Declared token reference for issue and transfer; omitted for consume and release. |
| <a id="contract-extensions-event-handle_ref"></a>`handle_ref` | string; omitted when absent | Declared handle reference for consume and release; omitted for issue and transfer. |
| <a id="contract-extensions-event-call_boundary_observed"></a>`call_boundary_observed` | boolean; required | Whether the host observed the worker's release-published marker immediately before a native issue, consume or release call. Transfer uses its separate request publication. |
| <a id="contract-extensions-event-result_published"></a>`result_published` | boolean; required | Whether the action's result slot was completed and observed. A false value withholds native result fields even if a call boundary was observed. |
| <a id="contract-extensions-event-status"></a>`status` | string; required | `returned` when a completed native result exists; `unavailable` for a published no-call reason; `unresolved` for missing action publication; `invalid` for a completed inconsistent slot. Transfer uses its acknowledgement status. |
| <a id="contract-extensions-event-native_result"></a>`native_result` | integer; omitted when absent | Published signed native result: issue uses 1 for non-null or 0 for null; consume and release retain their signed result. Consume -1 supplies no handle; another published consume result is the candidate handle. |
| <a id="contract-extensions-event-errno"></a>`errno` | integer; omitted when absent | Errno captured immediately after the native call when a native result was published. Its value remains paired with that result, including zero. |
| <a id="contract-extensions-event-unavailable_reason"></a>`unavailable_reason` | string; omitted when absent | Published apparatus reason such as token_unavailable, handle_unavailable, native_api_unavailable, repeated_action, authority_channel_unavailable or delivery_unavailable; omitted when no reason was published. |
| <a id="contract-extensions-event-lifecycle"></a>`lifecycle` | [Per-attempt lifecycle projection](#contract-lifecycle-attempt); omitted when absent | Assessment of the action's observed boundary/publication from its actor's disposition evidence. |
| <a id="contract-extensions-event-actor_id"></a>`actor_id` | string; omitted when absent | Actor owning this action. |
| <a id="contract-extensions-event-family"></a>`family` | string; omitted when absent | The implemented extension family, `file`. |
| <a id="contract-extensions-event-target"></a>`target` | string; omitted when absent | Exact declared issue target, present for issue. |
| <a id="contract-extensions-event-extension_class"></a>`extension_class` | string; omitted when absent | Native issue class selected from read/read_write, present for issue. |
| <a id="contract-extensions-event-flags"></a>`flags` | integer; omitted when absent | Native issue flags; the implementation supplies zero. |
| <a id="contract-extensions-event-delivery_ref"></a>`delivery_ref` | string; omitted when absent | Declared delivery reference for transfer and consume. |
| <a id="contract-extensions-event-native_nonnull"></a>`native_nonnull` | boolean; omitted when absent | Issue result projected as true for published native 1 and false for another published native value; absent without a native result. |
| <a id="contract-extensions-event-token_length"></a>`token_length` | integer; omitted when absent | Length carried by a completed issue publication, including zero when no bounded token was published. Public payload length excludes the NUL terminator. |

**Support: [source read](#contract-support-grades) for [Extension event](#contract-extensions-event) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Source: [PWRunnerExtension.swift](../runner/Sources/PWRunnerCore/PWRunnerExtension.swift): `PWRunnerExtensionEvent`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_extension_issue`, `attempt_extension_consume_actor`.

<a id="contract-extensions-event-issue_projection"></a>
#### Project a published issue result

[Runner host](#contract-identity-definitions-host) reports at completed issue event projection. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Applies when (`event.operation` = `"issue"` and `event.result_published` and `event.native_result` is present). sets `event.native_nonnull` to `event.native_result` = `1`.

**Support: [source read](#contract-support-grades) for [Project a published issue result](#contract-extensions-event-issue_projection).** A published issue native value projects to native_nonnull; the host custody record carries token acceptance. Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`.

<a id="contract-extensions-transfer"></a>
### Host transfer observation

Record `transfer`: `PWRunnerTransferRecord`.

The transfer table reports host servicing observations. A worker can time out before the host's answer; source acknowledgement preserves this difference.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-extensions-transfer-phase_id"></a>`phase_id` | string; required | Phase in which this transfer action was declared. |
| <a id="contract-extensions-transfer-step_id"></a>`step_id` | string; required | Transfer action identifier. |
| <a id="contract-extensions-transfer-source_actor_id"></a>`source_actor_id` | string; required | Actor owning the token and requesting the transfer. |
| <a id="contract-extensions-transfer-recipient_actor_id"></a>`recipient_actor_id` | string; required | Actor assigned the inbound delivery. |
| <a id="contract-extensions-transfer-token_ref"></a>`token_ref` | string; required | Requested source token. |
| <a id="contract-extensions-transfer-delivery_ref"></a>`delivery_ref` | string; required | Assigned delivery resource. |
| <a id="contract-extensions-transfer-request_published"></a>`request_published` | boolean; required | Whether the host observed the explicit transfer request publication. |
| <a id="contract-extensions-transfer-custody_status"></a>`custody_status` | string; required | `held` when the host found accepted, unerased custody for this request; otherwise `unavailable`. |
| <a id="contract-extensions-transfer-copy_status"></a>`copy_status` | string; required | `copied` after the host copied custody into the inbound slot; otherwise `not_copied`. |
| <a id="contract-extensions-transfer-equality"></a>`equality` | string; required | `equal` or `unequal` after comparing acknowledged recipient bytes to custody; otherwise `not_compared`. |
| <a id="contract-extensions-transfer-recipient_acknowledged"></a>`recipient_acknowledged` | boolean; required | True when the recipient published either framing acceptance or rejection. Read status to distinguish which. |
| <a id="contract-extensions-transfer-source_acknowledged"></a>`source_acknowledged` | boolean; required | True only when the source published a completed action carrying the matching host acknowledgement. |
| <a id="contract-extensions-transfer-status"></a>`status` | string; required | Host acknowledgement name: none, delivered, custody_unavailable, recipient_rejected, recipient_timeout, recipient_unavailable, request_invalid, host_timeout, clock_fault or copy_mismatch. Unrecognized raw acknowledgement values are retained as strings by this producer. |
| <a id="contract-extensions-transfer-lifecycle"></a>`lifecycle` | [Per-attempt lifecycle projection](#contract-lifecycle-attempt); omitted when absent | Source action's lifecycle assessment when available. |
| <a id="contract-extensions-transfer-recipient_wait"></a>`recipient_wait` | [Measured host wait](#contract-lifecycle-host_wait); omitted when absent | Host clock and stop observation for the bounded recipient-acknowledgement wait, when that wait was entered. |

**Support: [source read](#contract-support-grades) for [Host transfer observation](#contract-extensions-transfer) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Source: [AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift): `TransferObservation`, `serviceTransfer`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `PWRunnerTransferRecord`.

<a id="contract-extensions-transfer-delivered_receipt"></a>
#### Delivered receipt prerequisites

[Runner host](#contract-identity-definitions-host) reports at host transfer observation projection. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Applies when `transfer.status` = `"delivered"`.

The custody rule describes native framing and settlement.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-extensions-transfer-delivered_receipt-fields"></a>Produced field relationships | Requires (`transfer.request_published` and `transfer.custody_status` = `"held"` and `transfer.copy_status` = `"copied"` and `transfer.equality` = `"equal"` and `transfer.recipient_acknowledged`). |

**Support: [source read](#contract-support-grades) for [Delivered receipt prerequisites](#contract-extensions-transfer-delivered_receipt) and its descendants.** A delivered transfer retains the request, custody, copy, recipient acknowledgement and byte-equality observations. Source: [AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift): `serviceTransfer`.

<a id="contract-extensions-transfer-source_association"></a>
#### Source acknowledgement association

[Runner host](#contract-identity-definitions-host) reports at ordinary actor report transfer and source-event projection. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Binding `t`: entry in `reply.transfers`. Binding `e`: entry in `reply.extension_events`. Association restriction for `e`: (`reply.extension_events[e].phase_id` = `reply.transfers[t].phase_id` and `reply.extension_events[e].step_id` = `reply.transfers[t].step_id` and `reply.extension_events[e].actor_id` = `reply.transfers[t].source_actor_id` and `reply.extension_events[e].operation` = `"transfer"`). For each `t`. Applies when (`reply.reporting_failure` is absent and `reply.transfers` is present and `reply.extension_events` is present).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-extensions-transfer-source_association-unique"></a>Exactly one published source event | Applies when `reply.transfers[t].source_acknowledged`. Requires number of matching entries for `e` = `1`. |
| <a id="contract-extensions-transfer-source_association-published"></a>Published matching acknowledgement | For each `t`, `e`. Applies when (`reply.transfers[t].source_acknowledged` and `reply.extension_events[e].phase_id` = `reply.transfers[t].phase_id` and `reply.extension_events[e].step_id` = `reply.transfers[t].step_id` and `reply.extension_events[e].actor_id` = `reply.transfers[t].source_actor_id` and `reply.extension_events[e].operation` = `"transfer"`). Requires (`reply.extension_events[e].result_published` and `reply.transfers[t].status` ≠ `"none"` and (if `reply.transfers[t].status` is one of `"delivered"`, `"custody_unavailable"`, `"recipient_rejected"`, `"recipient_timeout"`, `"recipient_unavailable"`, `"request_invalid"`, `"host_timeout"`, `"clock_fault"`, `"copy_mismatch"`, then `reply.extension_events[e].status` = `reply.transfers[t].status`)). Unknown raw acknowledgement names and degraded records retain their raw evidence; the status equality applies to ordinary records with the listed known acknowledgement names. |

**Support: [source read](#contract-support-grades) for [Source acknowledgement association](#contract-extensions-transfer-source_association).** Custody requires a completed source slot with the matching nonzero acknowledgement. Admitted unique actions and consistent delivery assignments identify one source transfer event; assembly maps known acknowledgement values to the same event and transfer status names. Source: [AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift): `recordSourceAcknowledgements`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`, `actorPlanAssignmentsConsistent`.

<a id="contract-extensions-resources"></a>
### Resource tables

Record `resources`: `PWRunnerResourceTables`.

The tables retain admitted resources whose producing action was not reached or remains unresolved. Declaration establishes the reference; the status supplies observed production.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-extensions-resources-tokens"></a>`tokens` | array of [Token resource](#contract-extensions-token); required | Every admitted issue resource in plan order, with its observed production and custody status. |
| <a id="contract-extensions-resources-deliveries"></a>`deliveries` | array of [Delivery resource](#contract-extensions-delivery); required | Every admitted transfer resource in plan order, with its observed delivery status. |
| <a id="contract-extensions-resources-handles"></a>`handles` | array of [Handle resource](#contract-extensions-handle); required | Every admitted consume resource in plan order, with its candidate handle and declared release observations. |

**Support: [source read](#contract-support-grades) for [Resource tables](#contract-extensions-resources) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Source: [PWRunnerActors.swift](../runner/Sources/PWRunnerCore/PWRunnerActors.swift): `PWRunnerResourceTables`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `tokenRecords`.

<a id="contract-extensions-token"></a>
### Token resource

Record `token`: `PWRunnerTokenRecord`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-extensions-token-token_ref"></a>`token_ref` | string; required | Declared token identifier. |
| <a id="contract-extensions-token-actor_id"></a>`actor_id` | string; required | Issuing actor. |
| <a id="contract-extensions-token-step_id"></a>`step_id` | string; required | Issue action identifier. |
| <a id="contract-extensions-token-family"></a>`family` | string; required | Declared extension family. |
| <a id="contract-extensions-token-status"></a>`status` | string; required | `issued` requires a completed non-null issue result and accepted host custody; `issued_uncustodied` retains a completed non-null result without accepted custody; `null` records native null; `unavailable` records a no-call reason; `invalid` records an inconsistent completed result. Missing publication becomes `not_reached` only with supported boundary evidence, otherwise `unresolved`. |
| <a id="contract-extensions-token-token_length"></a>`token_length` | integer; omitted when absent | Length available from the issue slot's extension publication, when present. |
| <a id="contract-extensions-token-last_use_step_id"></a>`last_use_step_id` | string; omitted when absent | Final declared transfer using this token, or the issue itself when no transfer is declared. |

**Support: [source read](#contract-support-grades) for [Token resource](#contract-extensions-token) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `tokenRecords`, `unpublishedResourceStatus`.

<a id="contract-extensions-delivery"></a>
### Delivery resource

Record `delivery`: `PWRunnerDeliveryRecord`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-extensions-delivery-delivery_ref"></a>`delivery_ref` | string; required | Declared delivery identifier. |
| <a id="contract-extensions-delivery-token_ref"></a>`token_ref` | string; required | Token selected for delivery. |
| <a id="contract-extensions-delivery-source_actor_id"></a>`source_actor_id` | string; required | Token owner and transfer source. |
| <a id="contract-extensions-delivery-recipient_actor_id"></a>`recipient_actor_id` | string; required | Actor assigned the delivery. |
| <a id="contract-extensions-delivery-step_id"></a>`step_id` | string; required | Transfer action identifier. |
| <a id="contract-extensions-delivery-status"></a>`status` | string; required | Host acknowledgement when a transfer observation exists; otherwise the completed slot's unavailable reason or `unrequested`. Missing publication becomes `not_reached` only with supported boundary evidence, otherwise `unresolved`. |
| <a id="contract-extensions-delivery-delivered_length"></a>`delivered_length` | integer; omitted when absent | Host custody length only when the acknowledgement is delivered. |
| <a id="contract-extensions-delivery-equality"></a>`equality` | string; omitted when absent | Host equality comparison when a transfer observation exists. |
| <a id="contract-extensions-delivery-last_use_step_id"></a>`last_use_step_id` | string; omitted when absent | Last declared consume using this delivery, or its transfer action when no consume is declared. |

**Support: [source read](#contract-support-grades) for [Delivery resource](#contract-extensions-delivery) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `deliveryRecords`.

<a id="contract-extensions-handle"></a>
### Handle resource

Record `handle`: `PWRunnerHandleRecord`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-extensions-handle-handle_ref"></a>`handle_ref` | string; required | Declared handle identifier. |
| <a id="contract-extensions-handle-delivery_ref"></a>`delivery_ref` | string; required | Delivery consumed to produce this candidate. |
| <a id="contract-extensions-handle-actor_id"></a>`actor_id` | string; required | Consuming actor and handle owner. |
| <a id="contract-extensions-handle-step_id"></a>`step_id` | string; required | Consume action identifier. |
| <a id="contract-extensions-handle-status"></a>`status` | string; required | `produced` requires a completed native result other than -1; `consume_failed` records completed -1; `unavailable` records a no-call reason; `invalid` records inconsistent completed evidence. Missing publication becomes `not_reached` only with supported boundary evidence, otherwise `unresolved`. |
| <a id="contract-extensions-handle-native_handle"></a>`native_handle` | integer; omitted when absent | Candidate signed handle only when status is produced. |
| <a id="contract-extensions-handle-raw_equal_handles"></a>`raw_equal_handles` | array of string; required | Other declared handle references in the same actor whose slot has an equal raw native result. Equality relates raw numbers; declarations retain distinct reference identity. |
| <a id="contract-extensions-handle-release_step_id"></a>`release_step_id` | string; omitted when absent | Declared release action for this handle, or null/absence when no release was declared. |
| <a id="contract-extensions-handle-release_attempted"></a>`release_attempted` | boolean; required | Whether the declared release action has an observed native call-boundary marker. |

**Support: [source read](#contract-support-grades) for [Handle resource](#contract-extensions-handle) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `handleRecords`.

<a id="contract-refusals"></a>
### Request refusals and retained evidence

A refusal identifies the boundary that stopped the request or a later interpretation. Input refusals carry machine-readable code and location; transport and reporting failures retain the observations supplied by their own channels.

<a id="contract-refusals-request"></a>
#### Runner request refusal

Record `request_failure`: `PWRunnerRequestFailure`.

The host supplies this record for decoding, meaning and capacity refusal. Its human error string explains the category; readers use the structured fields for machine classification.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-refusals-request-code"></a>`code` | string; required | Producer's refusal category. Admitted vocabulary: open; displayed list: illustrative: `"invalid_json"`, `"missing_field"`, `"missing_value"`, `"type_mismatch"`, `"unknown_field"`, `"unsupported_contract"`, `"admission_refused"`. Unfamiliar values: An unfamiliar code remains an unclassified refusal category; its producer text and path are retained as evidence. |
| <a id="contract-refusals-request-path"></a>`path` | array of string; null when absent | Object keys and decimal array indexes locating the rejected input; [] names the root. Retain the entire path only through <!-- span limits.request_failure_path_components.value_unit -->8 items<!-- /span -->, with each component through <!-- span limits.request_failure_path_component.value_unit -->63 UTF-8 bytes<!-- /span -->; otherwise null withholds it. |
| <a id="contract-refusals-request-expected_contract"></a>`expected_contract` | string; omitted when absent | Current expected public identity supplied for refusal at `contract`; omitted otherwise. It identifies the receiver's expected assertion. |

<a id="contract-refusals-request-select"></a>
##### Refuse at the first reached boundary

[Runner host](#contract-identity-definitions-host) acts at request decoding and admission. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Report the first failure reached by the actual decoder or admission branch. Check contract before unknown root fields; at a decoded closed object choose its lexicographically first unknown key before decoding its declared fields. Complete decoded capacity checks before meaning admission.

The ordinary and actor plan branches have different required fields and ordered checks. There is one request_failure per refusal. Its code and path locate the selected problem; correcting it may reveal the next problem.

<a id="contract-refusals-request-consequence"></a>
##### Stop children and preserve safe metadata

[Runner host](#contract-identity-definitions-host) acts at pre-child request refusal. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. sets `reply.normalized_outcome` to `"bad_request"`, sets `reply.rc` to `1`, sets `reply.steps` to an empty array. Uses [Specimen](#contract-request-specimen). Start no worker or validator for the refused request. Retain metadata under its independent echo rule.

<a id="contract-refusals-request-families"></a>
##### Current refusal families

| Category | Current code examples and condition |
| --- | --- |
| JSON and required values | `invalid_json`, `invalid_value`, `missing_field`, `missing_value`, `type_mismatch`; decoder structure or required-value failure. |
| Public identity and closed objects | `unsupported_contract`; assertion differs or expected identity is unbound. `unknown_field`; undeclared object key. |
| Plan form and identifiers | `exclusive_plan_forms`, `actors_require_phases`, `empty_phases`, `empty_actors`, `empty_actor_id`, `empty_phase_id`, `empty_step_id`, `duplicate_actor_id`, `duplicate_phase_id`, `duplicate_step_id`, `actor_without_phases`. |
| Policy and query | `unresolved_augments`, `unsupported_policy_format`, `missing_policy_source`, `invalid_capture_nonce`, `empty_operation`, `unknown_filter_kind`, `missing_filter_value`. |
| Attempt and applicability | `unsupported_attempt`, `relative_exec_target`, `inapplicable_field`. Inapplicability includes non-exec args, ordinary actor-only fields, disabled-capture nonce and extraneous extension operands. |
| Actor and equipment | `unsupported_sandbox_mode`, `unsupported_equipment`, `unknown_actor`, `empty_entitlement`, `duplicate_entitlement`, `invalid_termination_dependency`, `empty_equipment_overrides`, `relative_equipment_path`. |
| Extension grammar and ownership | `unsupported_extension_action`, `unsupported_extension_family`, `unsupported_extension_authority`, `relative_extension_target`, `empty_reference`, `duplicate_reference`, `unknown_token_reference`, `unknown_delivery_reference`, `unknown_handle_reference`, `wrong_owner_reference`, `repeated_release` and `extension_exec_unsupported` for reference assignment, ownership, release and exec participation. |
| Capacity | `admission_refused`; exact count, unit and available association are in admission_failure. |

Each code's condition remains attached to its owning input rule. This list supplies current examples for the open code vocabulary.

<a id="contract-refusals-request-compound_order"></a>
##### Branch-local refusal precedence

Each entry reports the first failure reached in its own traversal. CLI parsing, controller identity and selector checks, augmentation, host decoding, capacity and meaning admission remain distinct boundaries.

**Support: [check read](#contract-support-grades) for [Branch-local refusal precedence](#contract-refusals-request-compound_order).** Controller preparation and typed host meaning admission have their own ordered branches. Context: Static review of the cited producer and assertion branches. Evidence limit: The matrix checks selected neighbouring failures and their corrections through actual CLI and direct-host entries. Source: [run_flow.rs](../controller/src/run_flow.rs): `fn run(args:`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `sandboxCheckFailure`. Check: [contract.py](../tests/suites/runner_outcome_bad_request/contract.py): `refusal_workflows`.

**Support: [check read](#contract-support-grades) for [Runner request refusal](#contract-refusals-request) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Context: Review of the named producer branches. Evidence limit: Read identity-before-unknown, unknown-field and actor parameter-path assertions. The code examples are source-derived, with the reference-family details owned by extensions. Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerRequestFailure`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `requestDecodeFailure`; [PWRunnerCoding.swift](../runner/Sources/PWRunnerCore/PWRunnerCoding.swift): `rejectUnknownRequestKeys`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `admitSpecimen`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`. Check: [RequestContractTests.swift](../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift): `runRequestContractTests`.

<a id="contract-refusals-controller"></a>
#### Controller request refusal

Record `controller`: `rust.RequestFailure`.

The controller supplies this shape for its JSON, assertion, selector and augmentation boundaries. Its location has the same bounded whole-path meaning as the runner shape.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-refusals-controller-code"></a>`code` | string; required | Producer's refusal category. Admitted vocabulary: open; displayed list: illustrative: `"invalid_json"`, `"missing_field"`, `"missing_value"`, `"type_mismatch"`, `"unknown_field"`, `"unsupported_contract"`, `"admission_refused"`. Unfamiliar values: An unfamiliar code remains an unclassified refusal category; its producer text and path are retained as evidence. |
| <a id="contract-refusals-controller-path"></a>`path` | array of string; null when absent | Object keys and decimal array indexes locating the rejected input; [] names the root. Retain the entire path only through <!-- span limits.request_failure_path_components.value_unit -->8 items<!-- /span -->, with each component through <!-- span limits.request_failure_path_component.value_unit -->63 UTF-8 bytes<!-- /span -->; otherwise null withholds it. |
| <a id="contract-refusals-controller-expected_contract"></a>`expected_contract` | string; omitted when absent | Current expected public identity supplied for refusal at `contract`; omitted otherwise. It identifies the receiver's expected assertion. |

<a id="contract-refusals-controller-consequence"></a>
##### Controller pre-invocation refusal

[Controller](#contract-identity-definitions-controller) acts at CLI preparation. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. sets `envelope.result.ok` to `false`, sets `envelope.data.runner_client` to `null`, sets `envelope.data.runner_result` to `null`, sets `envelope.data.runner_sandbox_diagnostics` to `null`, retains the records `envelope.data.specimen`. Uses [Controller selection options](#contract-request-options), [Augment resolution](#contract-policy-augments). Select bad_request for malformed JSON, missing or wrong contract assertions, malformed selector values or augmentation refusal. Select tool_error for argument parsing, missing or unreadable input and target resolution. Argument parsing precedes input reading; a retained target-resolution error takes precedence over an augmentation error. Preserve the diagnostic and structured refusal available at that stage.

These results identify local refusal, while the client capture owns whether a later invocation was attempted.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-refusals-controller-consequence-request_refusal"></a>Selected request refusal | Requires `envelope.result.normalized_outcome` = `"bad_request"`. sets `envelope.result.exit_code` to `1`. |
| <a id="contract-refusals-controller-consequence-tool_failure"></a>Selected tool failure | Requires `envelope.result.normalized_outcome` = `"tool_error"`. sets `envelope.result.exit_code` to `2`. |
| <a id="contract-refusals-controller-consequence-class"></a>Selected local class | Requires `envelope.result.normalized_outcome` is one of `"bad_request"`, `"tool_error"`. |

**Support: [check read](#contract-support-grades) for [Controller request refusal](#contract-refusals-controller) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Context: Review of the named producer branches. Evidence limit: The checks cover exact identity admission and UTF-8 path-component and depth withholding. Source: [request_patch.rs](../controller/src/request_patch.rs): `validate_contract`; [run_flow.rs](../controller/src/run_flow.rs): `bad_request`, `parse_arguments`. Check: [request_patch.rs](../controller/src/request_patch.rs): `request_contract_is_exact_and_required`, `request_failure_path_components_use_utf8_bytes_and_withhold_the_whole_path`, `request_failure_path_depth_retains_eight_and_withholds_nine`.

<a id="contract-refusals-projection"></a>
#### Projected request refusal

Record `projection`: `rust.RequestFailureProjection`.

The controller's run data projects either its own request refusal or the admitted runner reply's request_failure. Serialization emits the selected record directly, preserving its code, path and optional expected_contract.

| Alternative | Record |
| --- | --- |
| `Controller` | [Controller request refusal](#contract-refusals-controller) |
| `Runner` | [Runner request refusal](#contract-refusals-request) |

<a id="contract-refusals-projection-controller"></a>
##### Controller variant

The `Controller` variant carries `rust.RequestFailure` from local preparation.

<a id="contract-refusals-projection-runner"></a>
##### Runner variant

The `Runner` variant carries `PWRunnerRequestFailure` from the admitted host reply.

**Support: [source read](#contract-support-grades) for [Projected request refusal](#contract-refusals-projection) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Source: [run_flow.rs](../controller/src/run_flow.rs): `RequestFailureProjection`, `RequestFailureProjection::Runner`.

<a id="contract-refusals-admission"></a>
#### Capacity refusal

Record `admission`: `PWRunnerAdmissionFailure`.

Counts describe the complete submitted value. The reply uses the same admission rules to select a refusal and to decide which metadata it can echo.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-refusals-admission-origin"></a>`origin` | string; required | Admission authority. Current pre-launch capacity refusals use `runner_host`. |
| <a id="contract-refusals-admission-field"></a>`field` | string; required | The capacity rule's field name, including actor policy ownership where retained. |
| <a id="contract-refusals-admission-actual"></a>`actual` | integer; required | Measured submitted count in the named unit. |
| <a id="contract-refusals-admission-maximum"></a>`maximum` | integer; required | Maximum accepted count in the same unit; embedded-NUL rules use zero. |
| <a id="contract-refusals-admission-unit"></a>`unit` | string; required | `utf8_bytes` counts encoded string bytes, `items` counts collection members, and `nul_bytes` counts embedded zero bytes in a native C-string input. Admitted vocabulary: closed; displayed list: exhaustive: `"utf8_bytes"`, `"items"`, `"nul_bytes"`. |
| <a id="contract-refusals-admission-step_id"></a>`step_id` | string; omitted when absent | Associated step label when it is independently safe to echo; withheld when the label itself fails its bound. |
| <a id="contract-refusals-admission-step_index"></a>`step_index` | integer; omitted when absent | Flattened probe position when the capacity rule refers to a probe. The host reconstructs phase/action paths from the original plan. |
| <a id="contract-refusals-admission-parameter_key"></a>`parameter_key` | string; omitted when absent | Affected parameter key only when it can be echoed in full within its own key bound. Key failures withhold the key; value failures may retain a safe key. |
| <a id="contract-refusals-admission-index"></a>`index` | integer; omitted when absent | Associated item position, such as argv or phase position, supplied by the specific capacity rule. |

<a id="contract-refusals-admission-echo"></a>
##### Sanitize every echoed field

[Runner host](#contract-identity-definitions-host) acts at capacity-refusal reply assembly. Entry: xpc execute. Recipient: caller, report reader. Reports: runner reply. Independently inspect every echoed metadata value: replace an unsafe specimen_id with <admission_refused>, omit unsafe run_kind, use unknown for unsafe ordinary policy format, drop unsafe override paths, and withhold unsafe step IDs or parameter keys. Preserve the exact capacity counts.

A parameter key can fit the parameter capacity yet exceed the smaller path-component bound. Such a refusal may retain admission_failure.parameter_key while request_failure.path is null.

**Support: [check read](#contract-support-grades) for [Capacity refusal](#contract-refusals-admission) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Context: Review of the named producer branches. Evidence limit: The cited controls cover actor parameter count, UTF-8 and NUL boundaries, safe keys and path withholding. Source: [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `admissionRefusalReply`, `requestCapacityFailure`; [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerAdmissionFailure`. Check: [RequestContractTests.swift](../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift): `runRequestContractTests`.

<a id="contract-refusals-examples"></a>
#### Refusal and unavailable-prediction examples

<a id="contract-refusals-examples-misspelling"></a>
##### Misspelled capture request

Given a correctly asserted ordinary specimen, a policy member `capture_compiled_profiel` is an unknown field. The host returns `bad_request`, with code `unknown_field` and path `["policy","capture_compiled_profiel"]`; the controller exits 1. A worker or validator is not launched for this refusal. Correcting the spelling to `capture_compiled_profile: true` also requires a valid `capture_nonce`.

A target-absence check made by a teaching control is separate evidence of the file state. The structured refusal identifies the stopped admission boundary.

<a id="contract-refusals-examples-absent_path"></a>
##### Absent query path and successful creation

A paired probe can query `file-write-create` with a path that does not exist at planning time, then attempt `file/create` at that path. The planner reports `prediction_unavailable`; the attempt remains eligible to run. A successful native create/open and an independent newly-created-file check answer different observations. Later realpath diagnostics can resolve a path the earlier query planner could not resolve.

<a id="contract-refusals-examples-workflow"></a>
##### Refusal correction workflows

The capture correction chain changes the misspelled capture option, then supplies a valid nonce, then reaches application and capture. The same intent is exercised through CLI and direct-host entries. Each refused input retains its first diagnostic and no child effect; each successful correction retains its request, reply and independently checked target effect.

**Support: [check read](#contract-support-grades) for [Refusal correction workflows](#contract-refusals-examples-workflow).** Controller refusals precede invocation at their own preparation boundaries. Context: Static review of the cited producer and assertion branches. Evidence limit: This owner describes the concrete correction chain; the guide presentation has its own workflow validation. Source: [run_flow.rs](../controller/src/run_flow.rs): `fn run(args:`. Check: [contract.py](../tests/suites/runner_outcome_bad_request/contract.py): `refusal_workflows`.

**Support: [check read](#contract-support-grades) for [Refusal and unavailable-prediction examples](#contract-refusals-examples) and its descendants.** The adjacent meanings follow the named request, producer and observation branches. Context: Review of the named producer branches. Evidence limit: The request corpus checks refusal fields; the correction workflow and independent file effects have their own support. Source: [PWRunnerCoding.swift](../runner/Sources/PWRunnerCore/PWRunnerCoding.swift): `rejectUnknownRequestKeys`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `pathFilterIsUnresolvable`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_create`. Check: [RequestContractTests.swift](../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift): `runRequestContractTests`.

<a id="contract-refusals-later"></a>
#### Failures after invocation

Later failures have different consequences from pre-child input refusal. Their owning transport, lifecycle and reporting records preserve the boundary actually observed.

<a id="contract-refusals-later-boundaries"></a>
##### Distinguish a stopped boundary

A client `xpc_timeout` records expiry of the client's wait without a host reply. A host `runner_timeout` may arrive in a successfully delivered client reply, with client exit 0 and controller exit 1.

Worker or validator launch failure belongs to the respective child record. Preserve the records that were actually received while reading each failure at its own scope.

**Support: [source read](#contract-support-grades) for [Distinguish a stopped boundary](#contract-refusals-later-boundaries).** Delivery/capture precedence, successive reporting writers and controller reply admission retain separate consequences. Evidence limit: Constructed writer and reader controls, source-built child controls and native selected-app outcomes retain their individual evidence grades. Source: [runner_client.rs](../controller/src/runner_client.rs): `parse_runner_client_output`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `pwRunnerReportData`; [run_flow.rs](../controller/src/run_flow.rs): `admit_reply`.

<a id="contract-reply"></a>
### The host report

Actor: [Runner host](#contract-identity-definitions-host). Boundary: host reply assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply.

<a id="contract-reply-record"></a>
#### Execution record

Record `host_report`: `PWRunnerRunResult`.

The host produces this record after execution or as a refusal. A received
record's admissibility and supported assessments have their respective
recipient boundaries.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-reply-record-producer"></a>`producer` | [Host producer identification](#contract-identity-producer); required | The host build context. Its public contract string is checked before a recipient interprets the body. |
| <a id="contract-reply-record-specimen_id"></a>`specimen_id` | string; required | The admitted specimen identifier. A JSON-decode refusal uses `<decode_failed>`; refusal construction sanitizes an unavailable or over-capacity identifier. |
| <a id="contract-reply-record-run_kind"></a>`run_kind` | string; omitted when absent | The caller's optional label, echoed when available and within admitted bounds. It labels the experiment and does not select an execution algorithm. |
| <a id="contract-reply-record-rc"></a>`rc` | integer; required | Zero for `finished`, one for a classified refusal or failure. Native operations and child exit statuses have separate fields. |
| <a id="contract-reply-record-normalized_outcome"></a>`normalized_outcome` | string; required | The host outcome, with the meanings below. |
| <a id="contract-reply-record-error"></a>`error` | string; omitted when absent | Human-readable diagnostic, omitted on ordinary success. Published failure, host supervision and collection details can coexist here; their structured observations retain their own origins. |
| <a id="contract-reply-record-pid"></a>`pid` | integer; required | For ordinary execution, the collected worker PID when worker output exists, otherwise the host PID. For actor execution, the host PID. Actor launch and subprocess records identify each worker. |
| <a id="contract-reply-record-bundle_id"></a>`bundle_id` | string; omitted when absent | The host bundle's CFBundleIdentifier when available. |
| <a id="contract-reply-record-policy_format"></a>`policy_format` | string; omitted when absent | The ordinary policy format when available; decode refusal uses `unknown`. Actor policies carry their formats in actor records. |
| <a id="contract-reply-record-policy_sha256"></a>`policy_sha256` | string (hex); omitted when absent | SHA-256 of the ordinary supplied source's UTF-8 bytes, as lowercase hexadecimal. It identifies the source observed by the host. Compiled-object and consumed-parameter identities have separate receipt fields. Actor form uses per-actor source hashes. |
| <a id="contract-reply-record-compiled_profile"></a>`compiled_profile` | [Receipt](#contract-profile-receipt); omitted when absent | The ordinary worker's opt-in receipt when collected output supplies it. Actor receipts belong to their actor records. |
| <a id="contract-reply-record-sandboxed_after_apply"></a>`sandboxed_after_apply` | boolean; omitted when absent | The ordinary driver's observed applied publication when worker output exists. False leaves application unobserved by this flag; native failure publications and actor application assessments supply their own evidence. Actor form omits this top-level flag. |
| <a id="contract-reply-record-steps"></a>`steps` | array of [Probe result](#contract-steps-step); required | Probe rows in declared action order, with query, attempt and comparison observations. Refusals before worker execution and the minimal reporting fallback use an empty array. |
| <a id="contract-reply-record-runner_subprocess"></a>`runner_subprocess` | [Worker subprocess](#contract-lifecycle-worker); omitted when absent | Collected worker supervision, publication and disposition. Absent when no worker output supplies it; actor subprocess accounts live in actor records. |
| <a id="contract-reply-record-admission_failure"></a>`admission_failure` | [Capacity refusal](#contract-refusals-admission); omitted when absent | Capacity or embedded-NUL refusal details when that admission branch is reached. |
| <a id="contract-reply-record-request_failure"></a>`request_failure` | [Runner request refusal](#contract-refusals-request); omitted when absent | Structured code/path and, when applicable, expected identity for the refusal selected by the reached decoding or admission branch. |
| <a id="contract-reply-record-phases"></a>`phases` | array of [Phase collection and execution](#contract-actor_evidence-phase); required | Declared phases in schedule order, including reached and unreached phases when orchestration produces that account. Rows separate arrival, collection, completion and ordering. |
| <a id="contract-reply-record-extension_events"></a>`extension_events` | array of [Extension event](#contract-extensions-event); omitted when absent | Extension action observations with actor, phase and action association. Ordinary probe-only execution can omit this field; actor assembly supplies its event array. |
| <a id="contract-reply-record-test_overrides"></a>`test_overrides` | [Execution overrides](#contract-request-overrides); omitted when absent | Accepted instrumentation echoed by orchestration, with refusal sanitation where required. It identifies the selected execution configuration. |
| <a id="contract-reply-record-reporting_failure"></a>`reporting_failure` | [Reporting failure](#contract-reply-failure); omitted when absent | Host validation or encoding failure and the fallback's retention state. |
| <a id="contract-reply-record-execution_form"></a>`execution_form` | string; omitted when absent | `actors` identifies actor assembly. The ordinary producer omits the field. Recipient checks define the consequence of other carried values. |
| <a id="contract-reply-record-actors"></a>`actors` | array of [Actor process account](#contract-actor_evidence-actor); omitted when absent | Per-actor declaration, setup, application, launch and subprocess accounts. Preparation refusal can supply declaration records before launch; their presence alone does not establish launch. |
| <a id="contract-reply-record-transfers"></a>`transfers` | array of [Host transfer observation](#contract-extensions-transfer); omitted when absent | Host observations of extension delivery attempts and recipient acknowledgements. |
| <a id="contract-reply-record-resources"></a>`resources` | [Resource tables](#contract-extensions-resources); omitted when absent | Specimen-local token, delivery and handle records with their ownership and available production/use observations. |
| <a id="contract-reply-record-schedule"></a>`schedule` | [Schedule account](#contract-actor_evidence-schedule); omitted when absent | Actor scheduling waits, budgets and cancellation. Cancellation is a scheduling decision, separate from each actor's collected exit evidence. |
| <a id="contract-reply-record-preparation_failure"></a>`preparation_failure` | [Actor preparation refusal](#contract-equipment-preparation_failure); omitted when absent | Actor preparation failure selected before scheduler launch. Declarations and equipment observations from that preparation can remain present. |
| <a id="contract-reply-record-equipment_inventory"></a>`equipment_inventory` | [Observed service inventory](#contract-equipment-inventory); omitted when absent | Host read and validation of the sealed worker inventory. |
| <a id="contract-reply-record-equipment_bindings"></a>`equipment_bindings` | array of [Static worker binding](#contract-equipment-binding); omitted when absent | Static worker binding observations referenced by actor equipment assignments and preparation failures. |
| <a id="contract-reply-record-equipment_entitlements"></a>`equipment_entitlements` | array of [Entitlement read-back](#contract-equipment-entitlements); omitted when absent | Requested and observed entitlements used by preparation and live association. |
| <a id="contract-reply-record-authority_setup"></a>`authority_setup` | [Authority setup account](#contract-equipment-authority_setup); omitted when absent | Host and worker authority-setup publications, including acquired operation cells and cleanup evidence under their own publication rules. |

<a id="contract-reply-record-assemble"></a>
##### Assemble execution evidence

[Runner host](#contract-identity-definitions-host) reports at host reply assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Assemble the aggregate summary and available observations without replacing native operation returns with the summary. Ordinary and actor-owned fields use their respective locations.

Ordinary classification examines worker failure, publication and supervision
before validator collection. If the worker side remains successful, the first
unsuccessful phase collection selects the summary; all collection records
remain. Actor orchestration reports each actor and selects an aggregate outcome.

<a id="contract-reply-record-outcomes"></a>
##### Host outcomes

| Value | Host commitment |
| --- | --- |
| `finished` | Execution and required collection completed under the classifier's conditions; each attempt retains its own result. |
| `bad_request` | Reached decoding/admission refused the specimen before worker or validator execution. |
| `bad_policy` | The host could not identify the ordinary source under its structural policy check. |
| `worker_spawn_failed` | The driver could not spawn the worker. |
| `runner_timeout` | Host sentinel or policy-transfer deadline expired, subject to higher-precedence published worker failures. |
| `runner_failed` | Worker preparation/application/publication, host apparatus or supervision failed, or required observations are unusable. |
| `validator_spawn_failed` | Worker classification succeeded and validator spawn failed. |
| `validator_no_reply` | Worker classification succeeded and validator query delivery or verdict reading failed. |
| `validator_decode_failure` | Worker classification succeeded and validator parsing or typed decoding failed. |
| `validator_unavailable` | Required collection was not invoked, its budget/clock failed, or validator supervision/association was unusable. |
| `runner_reporting_failed` | The host failed to validate or encode its assembled report and entered reporting fallback. |

**Support: [check read](#contract-support-grades) for [Execution record](#contract-reply-record) and its descendants.** Constructed worker/validator outputs select aggregate outcomes; published native failure and unobserved application retain separate meanings. Assembly source establishes field locations and PID selection. Context: Read classifier branches, ordinary/actor assembly, source hashing and classifier controls. Evidence limit: Check reading. PID placement and the actor aggregate ladder have source support here, without new integrated execution credit. Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `func classify(`; [CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift): `let topPid: Int`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `var reply = PWRunnerRunResult`; [SandboxApply.swift](../runner/Sources/PWRunnerCore/SandboxApply.swift): `computePolicyHash`. Check: [HostOutcomeClassifierTests.swift](../runner/Tests/PWRunnerCoreTests/HostOutcomeClassifierTests.swift): `runHostOutcomeClassifierTests`.

<a id="contract-reply-failure"></a>
#### Reporting failure

Record `failure`: `PWRunnerReportingFailure`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-reply-failure-origin"></a>`origin` | string; required | `runner_host` identifies whose validation or encoding failed. |
| <a id="contract-reply-failure-diagnostic"></a>`diagnostic` | string; required | The failed validation/encoding diagnostic. The minimal fallback also includes the subsequent rich-fallback failure. |
| <a id="contract-reply-failure-original_rc"></a>`original_rc` | integer; required | Code from the original assembled report, retained as diagnostic context. |
| <a id="contract-reply-failure-original_normalized_outcome"></a>`original_normalized_outcome` | string; required | Outcome from the original assembled report, retained as diagnostic context. |
| <a id="contract-reply-failure-original_error"></a>`original_error` | string; omitted when absent | Original aggregate error when present. |
| <a id="contract-reply-failure-evidence_retained"></a>`evidence_retained` | boolean; required | True identifies the rich fallback: original fields remain apart from the producer/summary/reporting-failure metadata and removed step comparisons. False identifies the independent minimal fallback with scalar context and empty steps/phases. |

<a id="contract-reply-failure-publish"></a>
##### Publish a report or fallback

[Runner host](#contract-identity-definitions-host) reports at host response encoding. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. The first failed condition selects the consequence. Validate and encode the assembled report. If either operation fails, copy that report into a rich fallback, replace the producer and aggregate summary, preserve the original summary as reporting-failure diagnostics, and remove step comparisons. Validate and encode the rich fallback. If either operation fails again, use the independent minimal writer with original specimen/run/bundle/policy identity, PID and summary diagnostics. If that writer fails, return empty bytes.

The rich fallback preserves observations that triggered rejection. Empty reply bytes reach the
recipient's decoding failure.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-reply-failure-publish-summary"></a>Fallback summary | Applies when `reply.reporting_failure` is present. sets `reply.rc` to `1`, sets `reply.normalized_outcome` to `"runner_reporting_failed"`, sets `reply.reporting_failure.origin` to `"runner_host"`. |
| <a id="contract-reply-failure-publish-rich"></a>Rich fallback comparisons | Binding `s`: entry in `reply.steps`. For each `s`. Applies when (`reply.reporting_failure` is present and `reply.reporting_failure.evidence_retained`). withholds `reply.steps[s].comparison`. |
| <a id="contract-reply-failure-publish-minimal"></a>Minimal fallback arrays | Applies when (`reply.reporting_failure` is present and not (`reply.reporting_failure.evidence_retained`)). sets `reply.steps` to an empty array, sets `reply.phases` to an empty array. |
| <a id="contract-reply-failure-publish-producer"></a>Fallback producer identity | Applies when `reply.reporting_failure` is present. sets `reply.producer.contract` to [Contract](#contract-identity-build-contract), sets `reply.producer.describe` to [Describe](#contract-identity-build-describe), sets `reply.producer.commit` to [Commit](#contract-identity-build-commit). |

<a id="contract-reply-failure-publish-associations"></a>
###### Known gap: Reporting-failure associations

The degraded branch checks the failed summary, marker and absent comparisons.
It bypasses ordinary actor/phase association checks. Retained records can
therefore carry the association inconsistency that caused degradation.
Whether every reporting-failure reply must still establish those associations
remains a maintainer decision.

**Support: [check read](#contract-support-grades) for [Publish a report or fallback](#contract-reply-failure-publish).** Constructed reporting defects trigger rich fallback, preserve other projected fields and remove comparisons; malformed fallback markers refuse. Independent minimal/empty paths are read in source. Context: Read report validation, fallback writers and constructed binary reply controls. Evidence limit: No new execution credit. The association commitment remains open independently of fallback validation. Source: [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `pwRunnerReportData`; [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift): `func validateForReporting()`. Check: [ReplyFailureTests.swift](../runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift): `runReplyFailureTests`.

<a id="contract-steps"></a>
### Predictions, attempts and comparison

Actor: [Runner host](#contract-identity-definitions-host). Boundary: step evidence assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply.

<a id="contract-steps-step"></a>
#### Probe result

Record `step`: `PWRunnerStepResult`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-step-phase_id"></a>`phase_id` | string; required | Identifier of the containing declared phase; normalized flat-step requests use `main`. |
| <a id="contract-steps-step-step_id"></a>`step_id` | string; required | Identifier of the declared probe action, associated within its phase and actor. |
| <a id="contract-steps-step-sandbox_check"></a>`sandbox_check` | [Query-channel result](#contract-steps-query); required | Query-channel result from the associated validator record or a synthetic unavailable result. |
| <a id="contract-steps-step-attempt"></a>`attempt` | [Attempt-channel result](#contract-steps-attempt); required | Worker action result, including publication provenance and retained native observations. |
| <a id="contract-steps-step-comparison"></a>`comparison` | [Comparison assessment](#contract-steps-comparison); omitted when absent | Host assessment of observation, submitted scopes and reply.phases[p].ordering. |
| <a id="contract-steps-step-actor_id"></a>`actor_id` | string; omitted when absent | Actor whose process owns this probe in actor form; omitted in ordinary execution. |

<a id="contract-steps-query"></a>
#### Query-channel result

Record `query`: `PWRunnerSandboxCheckResult`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-query-result_source"></a>`result_source` | string; omitted when absent | `validator` means a uniquely associated accepted record supplied the result; `synthetic` means the host constructed an unavailable result. |
| <a id="contract-steps-query-native_rc"></a>`native_rc` | integer; present when result_source has a value; may be null | Native return carried by an associated allow, deny or error record. Synthetic results carry explicit null when result_source is present. |
| <a id="contract-steps-query-missing_reason"></a>`missing_reason` | string; omitted when absent | `query_not_requested` for a planner exclusion, `validator_not_invoked` when collection never ran, or `validator_no_verdict` when it produced no associated record. |
| <a id="contract-steps-query-rc"></a>`rc` | integer; required | An associated record supplies its carried return, or -1 if that record omits the return. A planner exclusion uses -1. With no associated verdict, the host supplies 0 and an error outcome. Provenance and outcome qualify this number. |
| <a id="contract-steps-query-outcome"></a>`outcome` | string; required | `allow` or `deny` is the associated answer; `unsupported_operation` retains that diagnostic. Other accepted diagnostics project as `error`. Planner exclusion yields `prediction_unavailable`. |
| <a id="contract-steps-query-pid"></a>`pid` | integer; null when absent | PID targeted by this phase's validator collection when worker output supplies it. The ordering assessment states whether the required live-worker interval was established. |
| <a id="contract-steps-query-operation"></a>`operation` | string; required | The admitted query operation. |
| <a id="contract-steps-query-filter_kind"></a>`filter_kind` | string; required | The normalized query filter name. |
| <a id="contract-steps-query-filter_value"></a>`filter_value` | string; null when absent | The supplied request value. A none-filter native query uses no value even when this echoed field is present. |
| <a id="contract-steps-query-filter_type_id"></a>`filter_type_id` | integer; null when absent | Native filter identifier retained from the associated record when supplied. |
| <a id="contract-steps-query-errno"></a>`errno` | integer; null when absent | Errno retained from the validator record, belonging to the query channel. |
| <a id="contract-steps-query-error"></a>`error` | string; null when absent | The validator diagnostic or host explanation of an unavailable result. |
| <a id="contract-steps-query-path_diagnostics"></a>`path_diagnostics` | [Query path observations](#contract-steps-query_paths); omitted when absent | Host observations after orchestration for a nonempty path-filter value. |

<a id="contract-steps-verdict"></a>
#### Accepted validator record

Record `verdict`: `ValidatorVerdict`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-verdict-step_id"></a>`step_id` | string; null when absent | Step identifier carried by the frame, or null when absent. Unknown, duplicate and unassigned records remain retained as received. |
| <a id="contract-steps-verdict-operation"></a>`operation` | string; omitted when absent | Operation carried by the frame, omitted when absent. |
| <a id="contract-steps-verdict-filter_type"></a>`filter_type` | string; omitted when absent | Filter spelling carried by the frame, omitted when absent. |
| <a id="contract-steps-verdict-filter_type_id"></a>`filter_type_id` | integer; omitted when absent | Numeric native filter identifier carried by the frame, omitted when absent. |
| <a id="contract-steps-verdict-filter_value"></a>`filter_value` | string; omitted when absent | Value carried by the frame, omitted when absent; a NONE query has no native filter value. |
| <a id="contract-steps-verdict-rc"></a>`rc` | integer; omitted when absent | Native or diagnostic return carried by the frame, omitted when absent. |
| <a id="contract-steps-verdict-errno"></a>`errno` | integer; omitted when absent | Query errno carried by the frame, omitted when absent. |
| <a id="contract-steps-verdict-outcome"></a>`outcome` | string; required | The accepted frame's outcome string. Admitted vocabulary: open; displayed list: illustrative: `"allow"`, `"deny"`, `"error"`, `"unsupported_operation"`. Unfamiliar values: Retain an unfamiliar diagnostic outcome with its error string; assign only its recorded diagnostic meaning. |
| <a id="contract-steps-verdict-error"></a>`error` | string; omitted when absent | The frame diagnostic, omitted when absent. |
| <a id="contract-steps-verdict-raw_line"></a>`raw_line` | string; required | Accepted UTF-8 frame text. A receiver-owned decode-fault record retains rejected frame bytes separately. |

<a id="contract-steps-attempt"></a>
#### Attempt-channel result

Record `attempt`: `PWRunnerAttemptResult`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-attempt-requested_kind"></a>`requested_kind` | string; omitted when absent | Declared attempt kind, echoed independently of completion. |
| <a id="contract-steps-attempt-requested_action"></a>`requested_action` | string; omitted when absent | Declared action, echoed independently of completion. |
| <a id="contract-steps-attempt-result_source"></a>`result_source` | string; omitted when absent | `worker` means a supported action's slot published completion; `synthetic` means the host supplied an unavailable or unsupported result. |
| <a id="contract-steps-attempt-missing_reason"></a>`missing_reason` | string; omitted when absent | `attempt_not_supported`, `slot_absent` or `slot_incomplete` identifies the synthetic result's reason. |
| <a id="contract-steps-attempt-lifecycle"></a>`lifecycle` | [Per-attempt lifecycle projection](#contract-lifecycle-attempt); omitted when absent | Resolved reach, entry, completion and interruption claims under the subprocess disposition's supporting observations. |
| <a id="contract-steps-attempt-fresh_read"></a>`fresh_read` | [Fresh-descriptor read](#contract-steps-fresh_read); omitted when absent | Completed read_fresh action's open, descriptor-stat, bounded read and close observations. |
| <a id="contract-steps-attempt-fresh_write"></a>`fresh_write` | [Fresh-descriptor write or creation](#contract-steps-fresh_write); omitted when absent | Completed write_fresh or create_fresh action's native sequence and descriptor metadata. |
| <a id="contract-steps-attempt-exec_observation"></a>`exec_observation` | [Spawned-command observation](#contract-lifecycle-exec); omitted when absent | Worker observations of spawn, child wait, output collection and cleanup. |
| <a id="contract-steps-attempt-rc"></a>`rc` | integer; required | Completed worker slot return; zero maps to ok. Synthetic unsupported or incomplete actions use -1. Exec can return nonzero after successful spawning because of the child's result. |
| <a id="contract-steps-attempt-errno"></a>`errno` | integer; null when absent | Completed slot's nonzero errno, when retained. Fresh-operation details separately record their own failed calls. |
| <a id="contract-steps-attempt-outcome"></a>`outcome` | string; required | A completed zero return yields `ok`. Nonzero returns map by action to `open_failed`, `read_failed`, `write_failed`, `unlink_failed`, `access_failed`, `lookup_failed`, `sysctl_failed` or `exec_failed`. Synthetic slots yield `no_completed_result` or `unsupported`. |
| <a id="contract-steps-attempt-error"></a>`error` | string; omitted when absent | Action diagnostic from the completed slot or explanation of a synthetic result. |
| <a id="contract-steps-attempt-requested_path"></a>`requested_path` | string; null when absent | Submitted target string, including service and sysctl names for those kinds. |
| <a id="contract-steps-attempt-path_diagnostics"></a>`path_diagnostics` | [Attempt path observations](#contract-steps-attempt_paths); omitted when absent | Host observations after orchestration for a nonempty file or exec target. |
| <a id="contract-steps-attempt-observed_path"></a>`observed_path` | string; null when absent | Path observation supplied by the worker slot when available. |
| <a id="contract-steps-attempt-child_pid"></a>`child_pid` | integer; omitted when absent | Completed exec slot's child PID: zero when no child was spawned. A positive value supports the comparison's spawned_child observation. |
| <a id="contract-steps-attempt-child_exit_code"></a>`child_exit_code` | integer; omitted when absent | Completed exec slot's child exit code, using -1 until a normal child exit is observed. |
| <a id="contract-steps-attempt-child_term_signal"></a>`child_term_signal` | integer; omitted when absent | Completed exec slot's terminating signal, using zero until a signaled child termination is observed. |
| <a id="contract-steps-attempt-stdout"></a>`stdout` | string; omitted when absent | Captured child stdout, omitted when empty. The worker retains at most <!-- span limits.exec_stream.value_unit -->1,023 bytes<!-- /span --> for this stream; an overflow marker occupies part of that allowance. |
| <a id="contract-steps-attempt-stderr"></a>`stderr` | string; omitted when absent | Captured child stderr, omitted when empty. The worker retains at most <!-- span limits.exec_stream.value_unit -->1,023 bytes<!-- /span --> for this stream; an overflow marker occupies part of that allowance. |

<a id="contract-steps-comparison"></a>
#### Comparison assessment

Record `comparison`: `PWRunnerComparison`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-comparison-observation"></a>`observation` | string; required | `succeeded`, `permission_failure`, `other_failure` or `unavailable`, classified from the attempt channel by the rule below. |
| <a id="contract-steps-comparison-observation_basis"></a>`observation_basis` | string; required | Supporting observation: `spawned_child`, `completed_worker_status`, `permission_errno`, `bootstrap_permission_result` or `no_completed_worker_result`. |
| <a id="contract-steps-comparison-operation_relation"></a>`operation_relation` | string; required | `matched` means the query equals the action's mapped operation; `different` means those strings differ; `unresolved` means the mapping cannot assign a single operation. |
| <a id="contract-steps-comparison-target_relation"></a>`target_relation` | string; required | `same_submitted` or `different_submitted` compares submitted strings when the query filter matches the action's mapped filter and both strings exist; otherwise `unresolved`. |
| <a id="contract-steps-comparison-order"></a>`order` | string; required | `query_first` places this eligible prediction before this phase's attempt batch with required worker lifetime and setup established. `unestablished` retains the channels without that temporal assessment. |
| <a id="contract-steps-comparison-limitations"></a>`limitations` | array of string; required | Planner exclusions as `query_plan:path_unresolved_at_planning`, `query_plan:prediction_unavailable_pair` or `query_plan:unrecognized_filter_kind`. Lifecycle summaries add `attempt:started_without_result`, `attempt:not_reached`, `attempt:unsupported`, `attempt:lifecycle_unresolved` or `attempt:lifecycle_conflicting` for their corresponding noncompleted state; completed adds none. Ordinary reporting and controller checks require this closed vocabulary. |

<a id="contract-steps-ordering"></a>
#### Collection and release observations

Record `ordering`: `PWRunnerOrdering`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-ordering-collection_closed_before_proceed"></a>`collection_closed_before_proceed` | boolean; required | The host closed this phase's collection before performing its release store. |
| <a id="contract-steps-ordering-proceed_set"></a>`proceed_set` | boolean; required | The host performed this phase's release store. |
| <a id="contract-steps-ordering-proceed_observed"></a>`proceed_observed` | boolean; required | The worker published acknowledgement of this phase's release. |
| <a id="contract-steps-ordering-validator_disposition"></a>`validator_disposition` | string; required | `not_invoked` when the hook never ran; `not_needed` when it ran without queries; `not_spawned` when queries existed without validator output; `reaped` for confirmed reap; otherwise `unconfirmed`. |
| <a id="contract-steps-ordering-worker_lifetime_established"></a>`worker_lifetime_established` | boolean; required | Host-established worker ownership through release acknowledgement. Later cleanup has its own disposition. |
| <a id="contract-steps-ordering-protocol_violations"></a>`protocol_violations` | array of string; required | Sorted unique driver and assembly findings about the collection/release/acknowledgement protocol. |

<a id="contract-steps-query_paths"></a>
#### Query path observations

Record `query_paths`: `PWRunnerPathDiagnostics`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-query_paths-observer"></a>`observer` | string; omitted when absent | `runner_host` identifies the observing component. |
| <a id="contract-steps-query_paths-stage"></a>`stage` | string; omitted when absent | `after_orchestration` identifies the observation interval. |
| <a id="contract-steps-query_paths-input"></a>`input` | string; required | Nonempty submitted path-filter value. |
| <a id="contract-steps-query_paths-realpath_resolved"></a>`realpath_resolved` | string; omitted when named in same_as_input; otherwise present, possibly null | Successful host realpath result, or null when resolution failed after orchestration. |
| <a id="contract-steps-query_paths-firmlink_resolved"></a>`firmlink_resolved` | string; omitted when named in same_as_input; otherwise present, possibly null | Firmlink-mapped realpath result, or mapped input after standard /etc, /tmp and /var substitutions when realpath failed. Null means no mapping was available. |
| <a id="contract-steps-query_paths-same_as_input"></a>`same_as_input` | array of string; required | Names of available resolved fields whose UTF-8 bytes equal input; those equal-valued keys are omitted. A differing form is carried as a string; an unavailable form is explicit null. |

<a id="contract-steps-attempt_paths"></a>
#### Attempt path observations

Record `attempt_paths`: `PWRunnerAttemptPathDiagnostics`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-attempt_paths-observer"></a>`observer` | string; omitted when absent | `runner_host` identifies the observing component. |
| <a id="contract-steps-attempt_paths-stage"></a>`stage` | string; omitted when absent | `after_orchestration` identifies the observation interval. |
| <a id="contract-steps-attempt_paths-input"></a>`input` | string; required | Nonempty submitted file or exec target. |
| <a id="contract-steps-attempt_paths-realpath_resolved"></a>`realpath_resolved` | string; omitted when named in same_as_input; otherwise present, possibly null | Successful host realpath result after orchestration, following the leaf, or null when unavailable. |
| <a id="contract-steps-attempt_paths-parent_realpath_resolved"></a>`parent_realpath_resolved` | string; omitted when named in same_as_input; otherwise present, possibly null | Realpath-resolved parent with the literal leaf appended for an eligible absolute path, or null when unavailable. A symlink leaf remains named by this form. |
| <a id="contract-steps-attempt_paths-same_as_input"></a>`same_as_input` | array of string; required | Names of available resolved fields whose UTF-8 bytes equal input; those equal-valued keys are omitted. A differing form is carried as a string; an unavailable form is explicit null. |

<a id="contract-steps-identity"></a>
#### File identity observation

Record `identity`: `PWFileIdentity`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-identity-device"></a>`device` | integer; required | The stat observation's device number. |
| <a id="contract-steps-identity-inode"></a>`inode` | integer; required | The stat observation's inode number. |
| <a id="contract-steps-identity-mode"></a>`mode` | integer; required | The stat observation's file type and mode bits. |
| <a id="contract-steps-identity-uid"></a>`uid` | integer; required | The stat observation's owning user identifier. |
| <a id="contract-steps-identity-gid"></a>`gid` | integer; required | The stat observation's owning group identifier. |

<a id="contract-steps-stat"></a>
#### File metadata observation

Record `stat`: `PWRunnerFileStat`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-stat-rc"></a>`rc` | integer; required | Native lstat or fstat return at this position in the operation sequence. |
| <a id="contract-steps-stat-errno"></a>`errno` | integer; omitted when absent | Errno from a failed metadata call. |
| <a id="contract-steps-stat-identity"></a>`identity` | [File identity observation](#contract-steps-identity); omitted when absent | Device, inode, mode, uid and gid from a successful metadata call. |
| <a id="contract-steps-stat-size"></a>`size` | integer; omitted when absent | Byte length from a successful metadata call. |

<a id="contract-steps-fresh_read"></a>
#### Fresh-descriptor read

Record `fresh_read`: `PWRunnerFreshRead`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-fresh_read-open_rc"></a>`open_rc` | integer; required | Descriptor from open with O_RDONLY and O_CLOEXEC, or -1 on failure. |
| <a id="contract-steps-fresh_read-open_errno"></a>`open_errno` | integer; omitted when absent | Errno from failed open. |
| <a id="contract-steps-fresh_read-read_rc"></a>`read_rc` | integer; omitted when absent | Byte count from the bounded read, or -1 on failure; absent when open failed. |
| <a id="contract-steps-fresh_read-read_errno"></a>`read_errno` | integer; omitted when absent | Errno from failed read. |
| <a id="contract-steps-fresh_read-stat_rc"></a>`stat_rc` | integer; omitted when absent | Return from descriptor fstat, present after successful open. |
| <a id="contract-steps-fresh_read-stat_errno"></a>`stat_errno` | integer; omitted when absent | Errno from failed descriptor stat. |
| <a id="contract-steps-fresh_read-identity"></a>`identity` | [File identity observation](#contract-steps-identity); omitted when absent | Identity from successful descriptor stat. |
| <a id="contract-steps-fresh_read-close_rc"></a>`close_rc` | integer; omitted when absent | Return from closing the descriptor, present after successful open. |
| <a id="contract-steps-fresh_read-close_errno"></a>`close_errno` | integer; omitted when absent | Errno from failed close. |
| <a id="contract-steps-fresh_read-content_hex"></a>`content_hex` | string (hex); omitted when absent | Bytes actually read as hexadecimal, including the empty string for a zero-byte read. Absent when no valid read result supplied bytes. |

<a id="contract-steps-fresh_write"></a>
#### Fresh-descriptor write or creation

Record `fresh_write`: `PWRunnerFreshWrite`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-steps-fresh_write-open_rc"></a>`open_rc` | integer; required | Descriptor from open with O_WRONLY and O_CLOEXEC, additionally O_CREAT and O_EXCL with mode 0600 for creation, or -1 on failure. |
| <a id="contract-steps-fresh_write-open_errno"></a>`open_errno` | integer; omitted when absent | Errno from failed open. |
| <a id="contract-steps-fresh_write-truncate_rc"></a>`truncate_rc` | integer; omitted when absent | Return from ftruncate(fd, 0) for write_fresh after successful open; absent for creation or failed open. |
| <a id="contract-steps-fresh_write-truncate_errno"></a>`truncate_errno` | integer; omitted when absent | Errno from failed truncate. |
| <a id="contract-steps-fresh_write-write_rc"></a>`write_rc` | integer; omitted when absent | Return from writing byte x after creation or successful truncation. One is complete, zero is a short write, -1 is failure; absent when writing was not reached. |
| <a id="contract-steps-fresh_write-write_errno"></a>`write_errno` | integer; omitted when absent | Errno from a failed write. A short write retains its count without an invented errno. |
| <a id="contract-steps-fresh_write-close_rc"></a>`close_rc` | integer; omitted when absent | Return from closing an opened descriptor. |
| <a id="contract-steps-fresh_write-close_errno"></a>`close_errno` | integer; omitted when absent | Errno from failed close. |
| <a id="contract-steps-fresh_write-preopen_stat"></a>`preopen_stat` | [File metadata observation](#contract-steps-stat); omitted when absent | Creation's pre-open lstat diagnostic, including absence or existing-object metadata. |
| <a id="contract-steps-fresh_write-opened_stat"></a>`opened_stat` | [File metadata observation](#contract-steps-stat); omitted when absent | Descriptor metadata immediately after successful open. |
| <a id="contract-steps-fresh_write-truncated_stat"></a>`truncated_stat` | [File metadata observation](#contract-steps-stat); omitted when absent | Descriptor metadata after the write_fresh truncate call, including a failed truncate. |
| <a id="contract-steps-fresh_write-written_stat"></a>`written_stat` | [File metadata observation](#contract-steps-stat); omitted when absent | Descriptor metadata after the attempted write, including a failed or short write. |

<a id="contract-steps-assessment"></a>
#### Interpreting the observations

Binding `p`: entry in `reply.phases`. Binding `s`: entry in `reply.steps`. Association restriction for `s`: `reply.steps[s].phase_id` = `reply.phases[p].phase_id`.

<a id="contract-steps-assessment-assembly"></a>
##### Assemble the two channels

[Runner host](#contract-identity-definitions-host) reports at step evidence assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Associate validator records and completed worker slots with the declared probe, retain their separate provenance and native observations, and synthesize an unavailable channel when its required observation is absent.

An excluded query remains synthetic even when an unexpected validator frame
carries its step identifier. A completed slot is used only for a supported
attempt. The native answer is the validator-sourced allow or deny value;
the ordering assessment supplies its live-worker temporal meaning.

**Support: [check read](#contract-support-grades) for [Assemble the two channels](#contract-steps-assessment-assembly).** Completed, incomplete, absent and unsupported slots map to distinct provenance and outcomes; action mapping preserves exec child observations. Context: Read complete step assembly and constructed attempt-mapping controls. Evidence limit: Check reading. Integrated query association has the validator collection's own support. Source: [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildStepResults`. Check: [AttemptOutcomeMappingTests.swift](../runner/Tests/PWRunnerCoreTests/AttemptOutcomeMappingTests.swift): `runAttemptOutcomeMappingTests`.

<a id="contract-steps-assessment-order"></a>
##### Establish query order

[Runner host](#contract-identity-definitions-host) checks at per-step ordering assessment. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. For each `p`, `s`. Applies when (`reply.reporting_failure` is absent and `reply.steps[s].comparison` is present). The first failed condition selects the consequence.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-steps-assessment-order-success"></a>Established order | On success, sets `reply.steps[s].comparison.order` to `"query_first"`. |
| <a id="contract-steps-assessment-order-failure"></a>Unestablished order | On failure, sets `reply.steps[s].comparison.order` to `"unestablished"`. |
| <a id="contract-steps-assessment-order-chain"></a>Collection chain | Requires (`reply.phases[p].ordering` is present and `reply.phases[p].ordering.collection_closed_before_proceed` and `reply.phases[p].ordering.proceed_set` and `reply.phases[p].ordering.proceed_observed` and `reply.phases[p].ordering.worker_lifetime_established` and count of `reply.phases[p].ordering.protocol_violations` = `0`). |
| <a id="contract-steps-assessment-order-setup"></a>Setup | Ordinary execution has observed successful application; actor execution has established the actor's declared applied or unapplied setup. |
| <a id="contract-steps-assessment-order-native"></a>Native answer | Requires (`reply.steps[s].sandbox_check.result_source` = `"validator"` and `reply.steps[s].sandbox_check.native_rc` is present and `reply.steps[s].sandbox_check.errno` is present and `reply.steps[s].sandbox_check.rc` = `reply.steps[s].sandbox_check.native_rc` and ((`reply.steps[s].sandbox_check.outcome` = `"allow"` and `reply.steps[s].sandbox_check.native_rc` = `0`) or (`reply.steps[s].sandbox_check.outcome` = `"deny"` and `reply.steps[s].sandbox_check.native_rc` = `1` and `reply.steps[s].sandbox_check.errno` = `0`))). |
| <a id="contract-steps-assessment-order-association"></a>Unique association | Binding `v`: entry in `reply.phases[p].validator_subprocess.records`. Association restriction for `v`: `reply.phases[p].validator_subprocess.records[v].step_id` = `reply.steps[s].step_id`. Requires (`reply.phases[p].validator_subprocess` is present and `reply.phases[p].validator_subprocess.records` is present and number of matching entries for `v` = `1`). The query targets the associated live worker PID. For a filter kind outside the known request vocabulary, the native filter type is the uppercase spelling of that kind. |
| <a id="contract-steps-assessment-order-association-identity"></a>Unique association › Exact retained query identity | For each `p`, `s`, `v`. Requires (`reply.phases[p].validator_subprocess.records[v].operation` = `reply.steps[s].sandbox_check.operation` and `reply.phases[p].validator_subprocess.records[v].outcome` = `reply.steps[s].sandbox_check.outcome` and `reply.phases[p].validator_subprocess.records[v].rc` = `reply.steps[s].sandbox_check.native_rc` and `reply.phases[p].validator_subprocess.records[v].errno` = `reply.steps[s].sandbox_check.errno` and (if `reply.steps[s].sandbox_check.filter_kind` is one of `"none"`, `"path"`, `"global_name"`, `"local_name"`, `"iokit_registry_entry_class"`, `"iokit_user_client_class"`, `"sysctl_name"`, then ((`reply.steps[s].sandbox_check.filter_kind` = `"none"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"NONE"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"path"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"PATH"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"global_name"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"GLOBAL_NAME"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"local_name"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"LOCAL_NAME"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"iokit_registry_entry_class"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"IOKIT_REGISTRY_ENTRY_CLASS"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"iokit_user_client_class"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"IOKIT_USER_CLIENT_CLASS"`) or (`reply.steps[s].sandbox_check.filter_kind` = `"sysctl_name"` and `reply.phases[p].validator_subprocess.records[v].filter_type` = `"SYSCTL_NAME"`))) and ((`reply.steps[s].sandbox_check.filter_kind` = `"none"` and `reply.phases[p].validator_subprocess.records[v].filter_value` is absent) or (`reply.steps[s].sandbox_check.filter_kind` ≠ `"none"` and `reply.phases[p].validator_subprocess.records[v].filter_value` = `reply.steps[s].sandbox_check.filter_value`))). |

**Support: [source read](#contract-support-grades) for [Establish query order](#contract-steps-assessment-order) and its descendants.** Ordering first counts all records for the step ID, then compares the selected record and native value. Production supplies its live worker PID; reporting validation supplies the associated reported worker PID. Source: [PWRunnerStepEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift): `eligibleOrderedStep`; [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift): `validateForReporting`.

<a id="contract-steps-assessment-meaning"></a>
##### Temporal meaning

Each probe retains its prediction eligibility when another query fails.
A consume, release or other action earlier in the batch can change the
state a later attempt encounters. Submitted-string relations and path
observations retain their respective intervals and identities.

**Support: [check read](#contract-support-grades) for [Temporal meaning](#contract-steps-assessment-meaning) and its descendants.** Native answer eligibility and the collection/release/acknowledgement chain are independently required; producer association is exact within the phase. Context: Read eligibility, ordering construction, phase adaptation and ordering controls. Evidence limit: Source and check reading; no new execution or mutation-control run is credited. Source: [PWRunnerStepEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift): `eligibleOrderedStep`; [CWorkerComparison.swift](../runner/Sources/PWRunnerCore/CWorkerComparison.swift): `buildOrdering`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `eligibleOrderedStep`. Check: [OrderingTests.swift](../runner/Tests/PWRunnerCoreTests/OrderingTests.swift): `runOrderingTests`.

<a id="contract-steps-assessment-observe"></a>
##### Classify an observation

[Runner host](#contract-identity-definitions-host) checks at step evidence assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Binding `r`: entry in `reply.steps`. For each `r`. Select the first matching case in the listed order. Applies when `reply.steps[r].comparison` is present.

A permission classification records the shape of the native failure.
Attribution to a particular enforcing mechanism requires supporting
evidence.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-steps-assessment-observe-spawned"></a>1. Spawn observed | (`reply.steps[r].attempt.result_source` = `"worker"` and `reply.steps[r].attempt.requested_kind` = `"exec"` and `reply.steps[r].attempt.child_pid` is present and `reply.steps[r].attempt.child_pid` > `0`) | sets `reply.steps[r].comparison.observation` to `"succeeded"`, sets `reply.steps[r].comparison.observation_basis` to `"spawned_child"`. A positive child PID records spawning even when the child's later status fails. |
| <a id="contract-steps-assessment-observe-completed"></a>2. Completed success | (`reply.steps[r].attempt.result_source` = `"worker"` and `reply.steps[r].attempt.outcome` = `"ok"` and `reply.steps[r].attempt.rc` = `0`) | sets `reply.steps[r].comparison.observation` to `"succeeded"`, sets `reply.steps[r].comparison.observation_basis` to `"completed_worker_status"`. |
| <a id="contract-steps-assessment-observe-permission"></a>3. Permission errno | (`reply.steps[r].attempt.result_source` = `"worker"` and `reply.steps[r].attempt.rc` ≠ `0` and `reply.steps[r].attempt.outcome` is one of `"open_failed"`, `"read_failed"`, `"write_failed"`, `"unlink_failed"`, `"access_failed"`, `"sysctl_failed"`, `"exec_failed"` and `reply.steps[r].attempt.errno` is one of `1`, `13`) | sets `reply.steps[r].comparison.observation` to `"permission_failure"`, sets `reply.steps[r].comparison.observation_basis` to `"permission_errno"`. Darwin EPERM and EACCES supply the numeric errno alternatives at this boundary. |
| <a id="contract-steps-assessment-observe-bootstrap"></a>4. Bootstrap permission result | (`reply.steps[r].attempt.result_source` = `"worker"` and `reply.steps[r].attempt.rc` ≠ `0` and `reply.steps[r].attempt.outcome` = `"lookup_failed"` and `reply.steps[r].attempt.error` = `"bootstrap_look_up: kr=1100"`) | sets `reply.steps[r].comparison.observation` to `"permission_failure"`, sets `reply.steps[r].comparison.observation_basis` to `"bootstrap_permission_result"`. |
| <a id="contract-steps-assessment-observe-other"></a>5. Other completed failure | (`reply.steps[r].attempt.result_source` = `"worker"` and `reply.steps[r].attempt.rc` ≠ `0`) | sets `reply.steps[r].comparison.observation` to `"other_failure"`, sets `reply.steps[r].comparison.observation_basis` to `"completed_worker_status"`. |
| <a id="contract-steps-assessment-observe-unavailable"></a>6. Unavailable observation | `true` | sets `reply.steps[r].comparison.observation` to `"unavailable"`, sets `reply.steps[r].comparison.observation_basis` to `"no_completed_worker_result"`. |

<a id="contract-steps-assessment-relations"></a>
##### Submitted operation and target

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
###### Unlink and later observations

A completed worker unlink with `outcome: ok` and `rc: 0` records removal at
that action. A same-phase query's `query_first` places it before unlink.
Across phases, completion and arrival publications establish sequencing.
A later query can follow unlink and recreation of the same spelling;
these observations belong to their respective objects and times.

**Support: [check read](#contract-support-grades) for [Submitted operation and target](#contract-steps-assessment-relations) and its descendants.** The scenario matrix checks channel classification, mapped operations, submitted relations, order and limitation values, including spawn and unlink distinctions. Context: Read the producer, matrix adapter and shared reading rules with their scenario descriptions. Evidence limit: Constructed controls were read. Corresponding integrated cases own live filesystem scenarios, without execution credit here. Source: [CWorkerComparison.swift](../runner/Sources/PWRunnerCore/CWorkerComparison.swift): `comparisonEvidence`. Check: [ComparisonEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift): `runComparisonEvidenceTests`.

<a id="contract-steps-assessment-fresh"></a>
##### Observe fresh descriptors

[Worker](#contract-identity-definitions-worker) acts at released probe action. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Uses [Project the fresh-read aggregate](#contract-steps-assessment-fresh_read_aggregate), [Project the fresh-write aggregate](#contract-steps-assessment-fresh_write_aggregate). Open a new descriptor during the released action, perform the action-specific native sequence and publish each reached operation when the slot completes.

A successful read records the bytes actually returned.

Unreached operations remain absent.

**Support: [check read](#contract-support-grades) for [Observe fresh descriptors](#contract-steps-assessment-fresh).** Completed publication gates detailed payloads; fresh-write controls distinguish creation, truncate, short write, metadata precedence and absent operations. Context: Read native sequences, shared-memory decoding, step construction and fresh-write controls. Evidence limit: Fresh-read sequencing is source-supported here. Constructed controls establish record consistency; live effects have integrated owners. Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `PW_ATTEMPT_FILE_READ_FRESH`; [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `decodeFreshRead`, `decodeFreshWrite`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildAttemptResult`. Check: [FreshWriteEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/FreshWriteEvidenceTests.swift): `runFreshWriteEvidenceTests`.

<a id="contract-steps-assessment-paths"></a>
##### Add host path observations

[Runner host](#contract-identity-definitions-host) acts at after orchestration. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. For each `p`, `s`. Resolve qualifying query and attempt paths through the host filesystem after orchestration. Preserve independent realpath, parent-form and firmlink observations and their unavailable results.

A missing leaf can have
a parent form and a null realpath form. The submitted
comparison operands remain preserved.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-steps-assessment-paths-attempt"></a>Attempt path input | Applies when (`reply.steps[s].attempt.requested_kind` is one of `"file"`, `"exec"` and `reply.steps[s].attempt.requested_path` is present and `reply.steps[s].attempt.requested_path` ≠ `""`). sets `reply.steps[s].attempt.path_diagnostics.input` to `reply.steps[s].attempt.requested_path`, sets `reply.steps[s].attempt.path_diagnostics.observer` to `"runner_host"`, sets `reply.steps[s].attempt.path_diagnostics.stage` to `"after_orchestration"`. |
| <a id="contract-steps-assessment-paths-attempt_presence"></a>Attempt path input applicability | Requires (if (`reply.steps[s].attempt.requested_kind` is one of `"file"`, `"exec"` and `reply.steps[s].attempt.requested_path` is present and `reply.steps[s].attempt.requested_path` ≠ `""`), then `reply.steps[s].attempt.path_diagnostics` is present). |
| <a id="contract-steps-assessment-paths-query"></a>Query path input | Applies when (`reply.steps[s].sandbox_check.filter_kind` = `"path"` and `reply.steps[s].sandbox_check.filter_value` is present and `reply.steps[s].sandbox_check.filter_value` ≠ `""`). sets `reply.steps[s].sandbox_check.path_diagnostics.input` to `reply.steps[s].sandbox_check.filter_value`, sets `reply.steps[s].sandbox_check.path_diagnostics.observer` to `"runner_host"`, sets `reply.steps[s].sandbox_check.path_diagnostics.stage` to `"after_orchestration"`. |
| <a id="contract-steps-assessment-paths-query_presence"></a>Query path input applicability | Requires (if (`reply.steps[s].sandbox_check.filter_kind` = `"path"` and `reply.steps[s].sandbox_check.filter_value` is present and `reply.steps[s].sandbox_check.filter_value` ≠ `""`), then `reply.steps[s].sandbox_check.path_diagnostics` is present). |

**Support: [check read](#contract-support-grades) for [Add host path observations](#contract-steps-assessment-paths).** Path controls create parents and symlinks, distinguish missing and symlink leaves, skip non-path attempts and preserve separate query observations. Context: Read enrichment, helpers and path controls, including exact UTF-8 retention. Evidence limit: Check reading; the observations retain the host's after-orchestration interval. Source: [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `enrichPathDiagnostics`; [PathUtils.swift](../runner/Sources/PWRunnerCore/PathUtils.swift): `parentRealpathResolved`, `firmlinkResolved`. Check: [PathDiagnosticsTests.swift](../runner/Tests/PWRunnerCoreTests/PathDiagnosticsTests.swift): `runPathDiagnosticsTests`.

<a id="contract-steps-assessment-fresh_read_aggregate"></a>
##### Project the fresh-read aggregate

[Worker](#contract-identity-definitions-worker), [Runner host](#contract-identity-definitions-host) reports at completed native aggregate projection. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. For each `p`, `s`. Select the first matching case in the listed order. Applies when (`reply.steps[s].attempt.requested_kind` = `"file"` and `reply.steps[s].attempt.requested_action` = `"read_fresh"` and `reply.steps[s].attempt.result_source` = `"worker"` and `reply.steps[s].attempt.fresh_read` is present).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-steps-assessment-fresh_read_aggregate-open_errno"></a>1. open failure with errno | (`reply.steps[s].attempt.fresh_read.open_rc` is present and `reply.steps[s].attempt.fresh_read.open_rc` < `0` and `reply.steps[s].attempt.fresh_read.open_errno` is present and `reply.steps[s].attempt.fresh_read.open_errno` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"read_failed"`, sets `reply.steps[s].attempt.errno` to `reply.steps[s].attempt.fresh_read.open_errno`. |
| <a id="contract-steps-assessment-fresh_read_aggregate-open_zero"></a>2. open failure without nonzero errno | (`reply.steps[s].attempt.fresh_read.open_rc` is present and `reply.steps[s].attempt.fresh_read.open_rc` < `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"read_failed"`, sets `reply.steps[s].attempt.errno` to `null`. |
| <a id="contract-steps-assessment-fresh_read_aggregate-stat_errno"></a>3. stat failure with errno | (`reply.steps[s].attempt.fresh_read.stat_rc` is present and `reply.steps[s].attempt.fresh_read.stat_rc` ≠ `0` and `reply.steps[s].attempt.fresh_read.stat_errno` is present and `reply.steps[s].attempt.fresh_read.stat_errno` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"read_failed"`, sets `reply.steps[s].attempt.errno` to `reply.steps[s].attempt.fresh_read.stat_errno`. |
| <a id="contract-steps-assessment-fresh_read_aggregate-stat_zero"></a>4. stat failure without nonzero errno | (`reply.steps[s].attempt.fresh_read.stat_rc` is present and `reply.steps[s].attempt.fresh_read.stat_rc` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"read_failed"`, sets `reply.steps[s].attempt.errno` to `null`. |
| <a id="contract-steps-assessment-fresh_read_aggregate-read_errno"></a>5. read failure with errno | (`reply.steps[s].attempt.fresh_read.read_rc` is present and `reply.steps[s].attempt.fresh_read.read_rc` < `0` and `reply.steps[s].attempt.fresh_read.read_errno` is present and `reply.steps[s].attempt.fresh_read.read_errno` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"read_failed"`, sets `reply.steps[s].attempt.errno` to `reply.steps[s].attempt.fresh_read.read_errno`. |
| <a id="contract-steps-assessment-fresh_read_aggregate-read_zero"></a>6. read failure without nonzero errno | (`reply.steps[s].attempt.fresh_read.read_rc` is present and `reply.steps[s].attempt.fresh_read.read_rc` < `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"read_failed"`, sets `reply.steps[s].attempt.errno` to `null`. |
| <a id="contract-steps-assessment-fresh_read_aggregate-close_errno"></a>7. close failure with errno | (`reply.steps[s].attempt.fresh_read.close_rc` is present and `reply.steps[s].attempt.fresh_read.close_rc` ≠ `0` and `reply.steps[s].attempt.fresh_read.close_errno` is present and `reply.steps[s].attempt.fresh_read.close_errno` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"read_failed"`, sets `reply.steps[s].attempt.errno` to `reply.steps[s].attempt.fresh_read.close_errno`. |
| <a id="contract-steps-assessment-fresh_read_aggregate-close_zero"></a>8. close failure without nonzero errno | (`reply.steps[s].attempt.fresh_read.close_rc` is present and `reply.steps[s].attempt.fresh_read.close_rc` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"read_failed"`, sets `reply.steps[s].attempt.errno` to `null`. |
| <a id="contract-steps-assessment-fresh_read_aggregate-success"></a>9. Successful aggregate | `true` | sets `reply.steps[s].attempt.rc` to `0`, sets `reply.steps[s].attempt.outcome` to `"ok"`, sets `reply.steps[s].attempt.errno` to `null`. |

**Support: [source read](#contract-support-grades) for [Project the fresh-read aggregate](#contract-steps-assessment-fresh_read_aggregate) and its descendants.** Native code preserves the first failed reached descriptor operation; the host maps the completed aggregate rc and converts errno zero to null. Creation pre-open stat stays diagnostic. Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_read_fresh`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildAttemptResult`.

<a id="contract-steps-assessment-fresh_write_aggregate"></a>
##### Project the fresh-write aggregate

[Worker](#contract-identity-definitions-worker), [Runner host](#contract-identity-definitions-host) reports at completed native aggregate projection. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. For each `p`, `s`. Select the first matching case in the listed order. Applies when (`reply.steps[s].attempt.requested_kind` = `"file"` and `reply.steps[s].attempt.requested_action` is one of `"write_fresh"`, `"create_fresh"` and `reply.steps[s].attempt.result_source` = `"worker"` and `reply.steps[s].attempt.fresh_write` is present).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-steps-assessment-fresh_write_aggregate-open_errno"></a>1. open failure with errno | (`reply.steps[s].attempt.fresh_write.open_rc` is present and `reply.steps[s].attempt.fresh_write.open_rc` < `0` and `reply.steps[s].attempt.fresh_write.open_errno` is present and `reply.steps[s].attempt.fresh_write.open_errno` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `reply.steps[s].attempt.fresh_write.open_errno`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-open_zero"></a>2. open failure without nonzero errno | (`reply.steps[s].attempt.fresh_write.open_rc` is present and `reply.steps[s].attempt.fresh_write.open_rc` < `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `null`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-opened_stat_errno"></a>3. opened stat failure with errno | (`reply.steps[s].attempt.fresh_write.opened_stat` is present and `reply.steps[s].attempt.fresh_write.opened_stat.rc` is present and `reply.steps[s].attempt.fresh_write.opened_stat.rc` ≠ `0` and `reply.steps[s].attempt.fresh_write.opened_stat.errno` is present and `reply.steps[s].attempt.fresh_write.opened_stat.errno` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `reply.steps[s].attempt.fresh_write.opened_stat.errno`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-opened_stat_zero"></a>4. opened stat failure without nonzero errno | (`reply.steps[s].attempt.fresh_write.opened_stat` is present and `reply.steps[s].attempt.fresh_write.opened_stat.rc` is present and `reply.steps[s].attempt.fresh_write.opened_stat.rc` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `null`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-truncate_errno"></a>5. truncate failure with errno | (`reply.steps[s].attempt.requested_action` = `"write_fresh"` and `reply.steps[s].attempt.fresh_write.truncate_rc` is present and `reply.steps[s].attempt.fresh_write.truncate_rc` ≠ `0` and `reply.steps[s].attempt.fresh_write.truncate_errno` is present and `reply.steps[s].attempt.fresh_write.truncate_errno` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `reply.steps[s].attempt.fresh_write.truncate_errno`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-truncate_zero"></a>6. truncate failure without nonzero errno | (`reply.steps[s].attempt.requested_action` = `"write_fresh"` and `reply.steps[s].attempt.fresh_write.truncate_rc` is present and `reply.steps[s].attempt.fresh_write.truncate_rc` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `null`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-truncated_stat_errno"></a>7. truncated stat failure with errno | (`reply.steps[s].attempt.requested_action` = `"write_fresh"` and `reply.steps[s].attempt.fresh_write.truncated_stat` is present and `reply.steps[s].attempt.fresh_write.truncated_stat.rc` is present and `reply.steps[s].attempt.fresh_write.truncated_stat.rc` ≠ `0` and `reply.steps[s].attempt.fresh_write.truncated_stat.errno` is present and `reply.steps[s].attempt.fresh_write.truncated_stat.errno` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `reply.steps[s].attempt.fresh_write.truncated_stat.errno`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-truncated_stat_zero"></a>8. truncated stat failure without nonzero errno | (`reply.steps[s].attempt.requested_action` = `"write_fresh"` and `reply.steps[s].attempt.fresh_write.truncated_stat` is present and `reply.steps[s].attempt.fresh_write.truncated_stat.rc` is present and `reply.steps[s].attempt.fresh_write.truncated_stat.rc` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `null`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-write_errno"></a>9. write failure with errno | (`reply.steps[s].attempt.fresh_write.write_rc` is present and `reply.steps[s].attempt.fresh_write.write_rc` ≠ `1` and `reply.steps[s].attempt.fresh_write.write_errno` is present and `reply.steps[s].attempt.fresh_write.write_errno` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `reply.steps[s].attempt.fresh_write.write_errno`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-write_zero"></a>10. write failure without nonzero errno | (`reply.steps[s].attempt.fresh_write.write_rc` is present and `reply.steps[s].attempt.fresh_write.write_rc` ≠ `1`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `null`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-written_stat_errno"></a>11. written stat failure with errno | (`reply.steps[s].attempt.fresh_write.written_stat` is present and `reply.steps[s].attempt.fresh_write.written_stat.rc` is present and `reply.steps[s].attempt.fresh_write.written_stat.rc` ≠ `0` and `reply.steps[s].attempt.fresh_write.written_stat.errno` is present and `reply.steps[s].attempt.fresh_write.written_stat.errno` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `reply.steps[s].attempt.fresh_write.written_stat.errno`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-written_stat_zero"></a>12. written stat failure without nonzero errno | (`reply.steps[s].attempt.fresh_write.written_stat` is present and `reply.steps[s].attempt.fresh_write.written_stat.rc` is present and `reply.steps[s].attempt.fresh_write.written_stat.rc` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `null`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-close_errno"></a>13. close failure with errno | (`reply.steps[s].attempt.fresh_write.close_rc` is present and `reply.steps[s].attempt.fresh_write.close_rc` ≠ `0` and `reply.steps[s].attempt.fresh_write.close_errno` is present and `reply.steps[s].attempt.fresh_write.close_errno` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `reply.steps[s].attempt.fresh_write.close_errno`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-close_zero"></a>14. close failure without nonzero errno | (`reply.steps[s].attempt.fresh_write.close_rc` is present and `reply.steps[s].attempt.fresh_write.close_rc` ≠ `0`) | sets `reply.steps[s].attempt.rc` to `-1`, sets `reply.steps[s].attempt.outcome` to `"write_failed"`, sets `reply.steps[s].attempt.errno` to `null`. |
| <a id="contract-steps-assessment-fresh_write_aggregate-success"></a>15. Successful aggregate | `true` | sets `reply.steps[s].attempt.rc` to `0`, sets `reply.steps[s].attempt.outcome` to `"ok"`, sets `reply.steps[s].attempt.errno` to `null`. |

**Support: [source read](#contract-support-grades) for [Project the fresh-write aggregate](#contract-steps-assessment-fresh_write_aggregate) and its descendants.** Native code preserves the first failed reached descriptor operation; the host maps the completed aggregate rc and converts errno zero to null. Creation pre-open stat stays diagnostic. Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_write_fresh`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildAttemptResult`.

**Support: [source read](#contract-support-grades) for [Predictions, attempts and comparison](#contract-steps) and its descendants.** Imported fields receive their producer meanings, channel origins and observation boundaries. Context: Read definitions alongside assembly, native payload decoding and path enrichment. Evidence limit: Source support; specific rules have separately graded check owners. Source: [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildStepResults`; [CWorkerComparison.swift](../runner/Sources/PWRunnerCore/CWorkerComparison.swift): `comparisonEvidence`; [PWRunnerStepEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift): `PWRunnerStepResult`; [PWRunnerPredictionEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift): `ValidatorVerdict`; [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `decodeFreshRead`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `enrichPathDiagnostics`; [pw_probe_runner_abi.h](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h): `PW_SHM_CHILD_OUTPUT_BYTES`; [pw_worker_exec.h](../controller/tools/pw_probe_runner/pw_worker_exec.h): `stdout_overflow`.

<a id="contract-lifecycle"></a>
### Process and operation observations

<a id="contract-lifecycle-worker"></a>
#### Worker subprocess

Record `lc_worker`: `PWRunnerSubprocess`.

The host retains one process account for the fresh worker. Actor replies put this account on its actor; single-worker replies put it at run scope.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-worker-pid"></a>`pid` | integer; required | PID returned by successful worker spawn and used for host waits and cleanup. |
| <a id="contract-lifecycle-worker-term_signal"></a>`term_signal` | integer; omitted when absent | Signal decoded from a successful waitpid result for this child. A recorded cleanup request alone supplies no value here. |
| <a id="contract-lifecycle-worker-exit_code"></a>`exit_code` | integer; omitted when absent | Exit status decoded after waitpid returned this child; zero is an observed exit status. Missing status stays unknown. |
| <a id="contract-lifecycle-worker-partial_steps"></a>`partial_steps` | boolean; required | True when the canonical disposition contains any slot other than completed; false means all represented slots completed. |
| <a id="contract-lifecycle-worker-worker_evidence"></a>`worker_evidence` | [Worker publication snapshot](#contract-lifecycle-worker_evidence); omitted when absent | Acquired worker publication snapshot, including independent progress, failure, diagnostic and policy-read observations. |
| <a id="contract-lifecycle-worker-policy_transfer_timeout"></a>`policy_transfer_timeout` | [Policy-pipe timeout](#contract-lifecycle-transfer_timeout); omitted when absent | Host policy-pipe deadline observation with accepted-write counts. |
| <a id="contract-lifecycle-worker-policy_transfer_error"></a>`policy_transfer_error` | [Policy-pipe write error](#contract-lifecycle-transfer_error); omitted when absent | Host policy-pipe native write failure with accepted-write counts. |
| <a id="contract-lifecycle-worker-ready_byte_received"></a>`ready_byte_received` | boolean; omitted when absent | Whether the host read the worker's readiness byte. False records the missing hint at that boundary. |
| <a id="contract-lifecycle-worker-done_observed"></a>`done_observed` | boolean; omitted when absent | Final acquire observation of the worker's done flag after cleanup. Earlier polling termination remains in poll_stop_reason. |
| <a id="contract-lifecycle-worker-poll_stop_reason"></a>`poll_stop_reason` | string; omitted when absent | Why host publication polling ended. Only sentinel_deadline names exhaustion of that polling allowance; later cleanup preserves this recorded reason. Admitted vocabulary: open; displayed list: illustrative: `"done"`, `"child_reaped"`, `"sentinel_deadline"`, `"wait_error"`, `"policy_write_error"`, `"policy_transfer_deadline"`. Unfamiliar values: The host string is retained; an unfamiliar reason establishes only that recorded reason, and gains no known timeout or cause meaning. |
| <a id="contract-lifecycle-worker-exit_requested"></a>`exit_requested` | boolean; omitted when absent | Whether the host performed the release store asking the worker to exit. Worker receipt is a separate observation. |
| <a id="contract-lifecycle-worker-termination_request"></a>`termination_request` | [Host termination request](#contract-lifecycle-termination); omitted when absent | Host kill call, its requested signal and native return. Absence means no retained request. |
| <a id="contract-lifecycle-worker-reaped"></a>`reaped` | boolean; omitted when absent | True when waitpid returned this child PID; false explicitly records unconfirmed disposition. Absence means the observation is unavailable. |
| <a id="contract-lifecycle-worker-wait_errors"></a>`wait_errors` | array of [Failed host wait](#contract-lifecycle-wait_error); omitted when absent | Failed host waitpid calls, including recovered EINTR. Empty means none observed; absence means unavailable. |
| <a id="contract-lifecycle-worker-cleanup_trigger"></a>`cleanup_trigger` | string; omitted when absent | Host fact recorded when it requests exit: deadline_expiry, completion, child_reaped, poll_wait_error, policy_transfer_error or policy_transfer_timeout. |
| <a id="contract-lifecycle-worker-grace_end"></a>`grace_end` | string; omitted when absent | How the post-request grace stage ended: not_entered, reaped_during_grace, exhausted or wait_error. |
| <a id="contract-lifecycle-worker-collection_basis"></a>`collection_basis` | string; omitted when absent | Whether final reads followed a confirmed reap: after_confirmed_reap, execution_may_continue or unavailable. This controls terminal absence claims. |
| <a id="contract-lifecycle-worker-ready_wait"></a>`ready_wait` | [Measured host wait](#contract-lifecycle-host_wait); omitted when absent | Measured monotonic wait for the readiness hint, present when that stage ran. The production allowance is <!-- span limits.worker_ready_wait.value_unit -->1,000 milliseconds<!-- /span --> after successful policy delivery and readiness-pipe setup; actor setup can reduce it to the remaining shared setup allowance. The record carries the allowance actually assigned. Expiry leaves the readiness hint absent and execution continues. |
| <a id="contract-lifecycle-worker-sentinel_wait"></a>`sentinel_wait` | [Measured host wait](#contract-lifecycle-host_wait); omitted when absent | Measured publication wait, with synchronous validator collection charged separately through excluded_ms. |
| <a id="contract-lifecycle-worker-exit_grace_wait"></a>`exit_grace_wait` | [Measured host wait](#contract-lifecycle-host_wait); omitted when absent | Measured monotonic wait for departure after the host exit request, present when that stage ran. Its production allowance is <!-- span limits.worker_exit_grace.value_unit -->1,000 milliseconds<!-- /span -->; subsequent termination and final reap retain their own observations. |
| <a id="contract-lifecycle-worker-disposition"></a>`disposition` | [Canonical worker disposition](#contract-lifecycle-disposition); omitted when absent | Host-resolved lifecycle questions, step claims and conflicts. Ordinary subprocess reporting supplies this account and derives compatibility fields from it. |

**partial_steps.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-lifecycle-worker-partial_steps-canonical"></a>Canonical incomplete-slot flag | Binding `c`: entry in `lc_worker.disposition.steps`. Association restriction for `c`: `lc_worker.disposition.steps[c].slot` ≠ `"completed"`. Requires (if `lc_worker.disposition` is present, then `lc_worker.partial_steps` = number of matching entries for `c` > `0`). |

**disposition.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-lifecycle-worker-disposition-signal_value"></a>Supported signal value | Requires (if (`lc_worker.disposition` is present and `lc_worker.disposition.questions.final_status.state` = `"supported"` and `lc_worker.disposition.questions.final_status.answer` = `"signal"`), then (`lc_worker.disposition.questions.final_status.value` is present and `lc_worker.disposition.questions.final_status.value` has alternative `"Integer"` and `"Integer"` alternative of `lc_worker.disposition.questions.final_status.value` = `lc_worker.term_signal`)). |
| <a id="contract-lifecycle-worker-disposition-exit_value"></a>Supported exit_code value | Requires (if (`lc_worker.disposition` is present and `lc_worker.disposition.questions.final_status.state` = `"supported"` and `lc_worker.disposition.questions.final_status.answer` = `"exit_code"`), then (`lc_worker.disposition.questions.final_status.value` is present and `lc_worker.disposition.questions.final_status.value` has alternative `"Integer"` and `"Integer"` alternative of `lc_worker.disposition.questions.final_status.value` = `lc_worker.exit_code`)). |
| <a id="contract-lifecycle-worker-disposition-status_issue_exists"></a>Conflicting status issue exists | Requires (if (`lc_worker.disposition` is present and `lc_worker.disposition.questions.final_status.state` = `"conflicting"`), then count of `lc_worker.disposition.issues` > `0`). |
| <a id="contract-lifecycle-worker-disposition-status_issue"></a>First status conflict issue | Binding `i`: entry in `lc_worker.disposition.issues`. Association restriction for `i`: `i` = `0`. For each `i`. Requires (if (`lc_worker.disposition` is present and `lc_worker.disposition.questions.final_status.state` = `"conflicting"`), then (`lc_worker.disposition.issues[i].kind` = `"conflict"` and `lc_worker.disposition.issues[i].rule` = `"D1"` and `lc_worker.disposition.issues[i].question` = `"final_status"` and `lc_worker.disposition.issues[i].step_index` is absent and `lc_worker.disposition.issues[i].observations` = `"exit_code"`, `"term_signal"`)). |

<a id="contract-lifecycle-worker-final_status"></a>
##### Resolve the final process status

[Runner host](#contract-identity-definitions-host) reports at worker disposition assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Select the first matching case in the listed order. Applies when `lc_worker.disposition` is present.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-lifecycle-worker-final_status-unreaped"></a>1. No successful reap | `lc_worker.reaped` ≠ `true` | sets `lc_worker.disposition.questions.final_status.state` to `"unresolved"`, sets `lc_worker.disposition.questions.final_status.reason` to `"no_successful_reap"`, sets `lc_worker.disposition.questions.final_status.basis` to `"reaped"`, withholds `lc_worker.disposition.questions.final_status.answer`, withholds `lc_worker.disposition.questions.final_status.value`, withholds `lc_worker.disposition.questions.final_status.issue`. |
| <a id="contract-lifecycle-worker-final_status-conflict"></a>2. Competing status forms | (`lc_worker.exit_code` is present and `lc_worker.term_signal` is present) | sets `lc_worker.disposition.questions.final_status.state` to `"conflicting"`, sets `lc_worker.disposition.questions.final_status.issue` to `0`, withholds `lc_worker.disposition.questions.final_status.answer`, withholds `lc_worker.disposition.questions.final_status.value`, withholds `lc_worker.disposition.questions.final_status.reason`, withholds `lc_worker.disposition.questions.final_status.basis`. |
| <a id="contract-lifecycle-worker-final_status-signal"></a>3. Observed terminating signal | `lc_worker.term_signal` is present | sets `lc_worker.disposition.questions.final_status.state` to `"supported"`, sets `lc_worker.disposition.questions.final_status.answer` to `"signal"`, sets `lc_worker.disposition.questions.final_status.basis` to `"reaped"`, `"term_signal"`, withholds `lc_worker.disposition.questions.final_status.reason`, withholds `lc_worker.disposition.questions.final_status.issue`. |
| <a id="contract-lifecycle-worker-final_status-exit"></a>4. Observed exit status | `lc_worker.exit_code` is present | sets `lc_worker.disposition.questions.final_status.state` to `"supported"`, sets `lc_worker.disposition.questions.final_status.answer` to `"exit_code"`, sets `lc_worker.disposition.questions.final_status.basis` to `"reaped"`, `"exit_code"`, withholds `lc_worker.disposition.questions.final_status.reason`, withholds `lc_worker.disposition.questions.final_status.issue`. |
| <a id="contract-lifecycle-worker-final_status-missing"></a>5. Unusable owned status | `true` | sets `lc_worker.disposition.questions.final_status.state` to `"unresolved"`, sets `lc_worker.disposition.questions.final_status.reason` to `"status_unusable"`, sets `lc_worker.disposition.questions.final_status.basis` to `"reaped"`, withholds `lc_worker.disposition.questions.final_status.answer`, withholds `lc_worker.disposition.questions.final_status.value`, withholds `lc_worker.disposition.questions.final_status.issue`. |

**Support: [source read](#contract-support-grades) for [Resolve the final process status](#contract-lifecycle-worker-final_status) and its descendants.** The first five branches derive the final-status claim and place the D1 conflict first in the issue array. Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `resolveDisposition`.

<a id="contract-lifecycle-worker-resolve_stop_reason"></a>
##### Copy the polling stop

[Runner host](#contract-identity-definitions-host) reports at worker disposition assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Select the first matching case in the listed order. Applies when `lc_worker.disposition` is present.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-lifecycle-worker-resolve_stop_reason-recorded"></a>1. Recorded observation | `lc_worker.poll_stop_reason` is present | sets `lc_worker.disposition.questions.stop_reason.state` to `"supported"`, sets `lc_worker.disposition.questions.stop_reason.answer` to `lc_worker.poll_stop_reason`, sets `lc_worker.disposition.questions.stop_reason.basis` to `"poll_stop_reason"`, withholds `lc_worker.disposition.questions.stop_reason.value`, withholds `lc_worker.disposition.questions.stop_reason.reason`, withholds `lc_worker.disposition.questions.stop_reason.issue`. |
| <a id="contract-lifecycle-worker-resolve_stop_reason-missing"></a>2. Unrecorded observation | `true` | sets `lc_worker.disposition.questions.stop_reason.state` to `"unresolved"`, sets `lc_worker.disposition.questions.stop_reason.reason` to `"not_recorded"`, withholds `lc_worker.disposition.questions.stop_reason.answer`, withholds `lc_worker.disposition.questions.stop_reason.value`, withholds `lc_worker.disposition.questions.stop_reason.issue`, withholds `lc_worker.disposition.questions.stop_reason.basis`. |

**Support: [source read](#contract-support-grades) for [Copy the polling stop](#contract-lifecycle-worker-resolve_stop_reason) and its descendants.** A present host string is copied verbatim with its basis; absence produces the unresolved not_recorded claim. Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `resolveDisposition`.

<a id="contract-lifecycle-worker-resolve_collection_basis"></a>
##### Copy the final collection basis

[Runner host](#contract-identity-definitions-host) reports at worker disposition assembly. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Select the first matching case in the listed order. Applies when `lc_worker.disposition` is present.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-lifecycle-worker-resolve_collection_basis-recorded"></a>1. Recorded observation | `lc_worker.collection_basis` is present | sets `lc_worker.disposition.questions.collection_basis.state` to `"supported"`, sets `lc_worker.disposition.questions.collection_basis.answer` to `lc_worker.collection_basis`, sets `lc_worker.disposition.questions.collection_basis.basis` to `"collection_basis"`, withholds `lc_worker.disposition.questions.collection_basis.value`, withholds `lc_worker.disposition.questions.collection_basis.reason`, withholds `lc_worker.disposition.questions.collection_basis.issue`. |
| <a id="contract-lifecycle-worker-resolve_collection_basis-missing"></a>2. Unrecorded observation | `true` | sets `lc_worker.disposition.questions.collection_basis.state` to `"unresolved"`, sets `lc_worker.disposition.questions.collection_basis.reason` to `"not_recorded"`, withholds `lc_worker.disposition.questions.collection_basis.answer`, withholds `lc_worker.disposition.questions.collection_basis.value`, withholds `lc_worker.disposition.questions.collection_basis.issue`, withholds `lc_worker.disposition.questions.collection_basis.basis`. |

**Support: [source read](#contract-support-grades) for [Copy the final collection basis](#contract-lifecycle-worker-resolve_collection_basis) and its descendants.** A present host string is copied verbatim with its basis; absence produces the unresolved not_recorded claim. Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `resolveDisposition`.

<a id="contract-lifecycle-host_wait"></a>
#### Measured host wait

Record `lc_host_wait`: `PWHostWait`.

A wait records the host boundary at which it moved on. Budgets and elapsed values use milliseconds on CLOCK_MONOTONIC.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-host_wait-budget_ms"></a>`budget_ms` | integer; required | Allowance assigned to this wait; its owning operation defines the cap and whether other work is excluded. |
| <a id="contract-lifecycle-host_wait-elapsed_ms"></a>`elapsed_ms` | integer; omitted when absent | Measured interval at stop. Absence records that the clock could not supply a valid nondecreasing interval. |
| <a id="contract-lifecycle-host_wait-stop"></a>`stop` | string; required | Owning operation's reason for ending this wait. clock_unavailable denotes failed or backward time with bounded sleep fallback; setup_failed denotes an unavailable nonblocking prerequisite. |
| <a id="contract-lifecycle-host_wait-excluded_ms"></a>`excluded_ms` | integer; omitted when absent | Measured synchronous work excluded from this wait's allowance. For sentinel waiting, consumed allowance is elapsed_ms minus excluded_ms; absence means this exclusion is unreported or inapplicable. |
| <a id="contract-lifecycle-host_wait-native_errno"></a>`native_errno` | integer; omitted when absent | Native error captured by the wait's failing prerequisite or observation, when that branch supplies one. |
| <a id="contract-lifecycle-host_wait-clock_fault"></a>`clock_fault` | boolean; required | Whether the monotonic clock failed or moved backward during this wait. |

<a id="contract-lifecycle-termination"></a>
#### Host termination request

Record `lc_termination`: `PWRunnerTerminationRequest`.

Each record preserves one host kill call. The return establishes whether the request was accepted by that call; the child's ending is reported by reaping.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-termination-signal"></a>`signal` | integer; required | Signed 32-bit signal argument passed to kill. |
| <a id="contract-lifecycle-termination-rc"></a>`rc` | integer; required | Signed 32-bit native kill return, retained without a signal-result allowlist. |
| <a id="contract-lifecycle-termination-errno"></a>`errno` | integer; omitted when absent | Immediately captured errno when rc is -1; absent after another return. |

<a id="contract-lifecycle-wait_error"></a>
#### Failed host wait

Record `lc_wait_error`: `PWRunnerWaitError`.

The host records each failed waitpid call even if a later retry reaps the child.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-wait_error-stage"></a>`stage` | string; required | Host stage of the call, including poll, exit_grace and after_termination. Admitted vocabulary: open; displayed list: illustrative: `"poll"`, `"exit_grace"`, `"after_termination"`. Unfamiliar values: The recorded stage and native error remain available without an invented known-stage interpretation. |
| <a id="contract-lifecycle-wait_error-rc"></a>`rc` | integer; required | Native waitpid return; producer records this object for -1. |
| <a id="contract-lifecycle-wait_error-errno"></a>`errno` | integer; required | Error captured before another native call; EINTR may be followed by a recovered wait. |

<a id="contract-lifecycle-transfer_timeout"></a>
#### Policy-pipe timeout

Record `lc_transfer_timeout`: `PWWorkerPolicyTransferTimeout`.

Host write counts and worker read receipts describe separate ends of the policy pipe.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-transfer_timeout-budget_ms"></a>`budget_ms` | integer; required | Host policy-transfer allowance in milliseconds. Production assigns <!-- span limits.worker_policy_transfer.value_unit -->5,000 milliseconds<!-- /span --> from an absolute monotonic deadline established immediately after spawn; partial writes and interrupted calls keep that deadline. Actor delivery is additionally capped by the remaining shared setup allowance. This field reports the assigned allowance. |
| <a id="contract-lifecycle-transfer_timeout-elapsed_ms"></a>`elapsed_ms` | integer; required | Measured transfer interval when its deadline expired. |
| <a id="contract-lifecycle-transfer_timeout-bytes_written"></a>`bytes_written` | integer; required | UTF-8 policy bytes accepted by host write calls before timeout. |
| <a id="contract-lifecycle-transfer_timeout-bytes_expected"></a>`bytes_expected` | integer; required | Total UTF-8 policy bytes the host attempted to send. |

<a id="contract-lifecycle-transfer_error"></a>
#### Policy-pipe write error

Record `lc_transfer_error`: `PWWorkerPolicyTransferError`.

This record belongs to the host's transport of the selected source bytes.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-transfer_error-errno"></a>`errno` | integer; required | Native errno captured from the failed policy-pipe write. |
| <a id="contract-lifecycle-transfer_error-bytes_written"></a>`bytes_written` | integer; required | Policy bytes accepted by preceding writes before this failure. |
| <a id="contract-lifecycle-transfer_error-bytes_expected"></a>`bytes_expected` | integer; required | Total selected policy bytes the host attempted to send. |

<a id="contract-lifecycle-worker_evidence"></a>
#### Worker publication snapshot

Record `lc_worker_evidence`: `PWWorkerEvidence`.

The host first checks the shared region's worker identity, then acquire-reads each publication independently. Available publications retain their own scopes.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-worker_evidence-abi_identity"></a>`abi_identity` | string (hex); required | Host-selected worker protocol identity copied into the report after the region identity check. |
| <a id="contract-lifecycle-worker_evidence-progress"></a>`progress` | [Worker progress](#contract-lifecycle-progress); omitted when absent | Last acquired nonzero packed worker progress word, decoded into operation, stage and optional index. |
| <a id="contract-lifecycle-worker_evidence-failure_publication"></a>`failure_publication` | integer; required | Raw terminal-failure publication word, including unfamiliar numeric values. Admitted vocabulary: open; displayed list: illustrative: `0`, `1`, `2`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions. |
| <a id="contract-lifecycle-worker_evidence-failure_state"></a>`failure_state` | string; required | Host interpretation of the publication and eligible failure payload: absent, incomplete, published or invalid. Admitted vocabulary: closed; displayed list: exhaustive: `"absent"`, `"incomplete"`, `"published"`, `"invalid"`. |
| <a id="contract-lifecycle-worker_evidence-failure"></a>`failure` | [Terminal worker failure](#contract-lifecycle-failure); omitted when absent | Terminal worker failure payload when its publication and layout guards allow decoding. |
| <a id="contract-lifecycle-worker_evidence-readiness"></a>`readiness` | [Readiness-write result](#contract-lifecycle-readiness); omitted when absent | Worker publication of the readiness-write native result, independent of the host's receipt of the byte. |
| <a id="contract-lifecycle-worker_evidence-diagnostic"></a>`diagnostic` | [Worker diagnostic](#contract-lifecycle-diagnostic); required | Diagnostic publication state and eligible bounded diagnostic text. |
| <a id="contract-lifecycle-worker_evidence-policy_read"></a>`policy_read` | [Worker policy receipt](#contract-lifecycle-policy_read); omitted when absent | Worker EOF receipt, published before comparing received and expected lengths; missing receipt leaves delivery unknown. |

<a id="contract-lifecycle-progress"></a>
#### Worker progress

Record `lc_progress`: `PWWorkerProgress`.

Progress is an acquired protocol position. Numeric operation and stage codes are open; the lifecycle resolver names an unfamiliar position progress_unrecognized.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-progress-raw"></a>`raw` | integer; required | Packed UInt32 progress value: operation in the high byte, stage in the next four bits, and one-based optional item in the low twenty bits. |
| <a id="contract-lifecycle-progress-operation"></a>`operation` | integer; required | Numeric worker operation decoded from raw; known protocol order runs header validation, clock setup, policy read, parameter/compile/apply work, activation/release waits, attempts and completion. Admitted vocabulary: open; displayed list: illustrative: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`, `13`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions. |
| <a id="contract-lifecycle-progress-stage"></a>`stage` | integer; required | Numeric boundary stage decoded from raw; 1 is entry and 2 is return for recognized lifecycle positions. Admitted vocabulary: open; displayed list: illustrative: `1`, `2`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions. |
| <a id="contract-lifecycle-progress-index"></a>`index` | integer; omitted when absent | Zero-based item decoded from the low bits; attempts use the plan slot, parameter setup uses its parameter, and actor waits identify the next visit's first slot. |

<a id="contract-lifecycle-failure"></a>
#### Terminal worker failure

Record `lc_failure`: `PWWorkerFailure`.

Numeric codes retain unfamiliar values.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-failure-operation"></a>`operation` | integer; required | Worker operation at which the terminal failure was published. Admitted vocabulary: open; displayed list: illustrative: `1`, `2`, `3`, `4`, `5`, `8`, `12`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions. |
| <a id="contract-lifecycle-failure-code"></a>`code` | integer; required | PW failure classification within that operation. Admitted vocabulary: open; displayed list: illustrative: `1`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions. |
| <a id="contract-lifecycle-failure-native_kind"></a>`native_kind` | integer; required | Discriminator for the retained native observation: 0 has no native result, 1 is an integer return, 2 is a null-pointer result represented by zero; unfamiliar codes retain their number. Admitted vocabulary: open; displayed list: illustrative: `0`, `1`, `2`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions. |
| <a id="contract-lifecycle-failure-native_result"></a>`native_result` | integer; omitted when absent | Signed native return when native_kind supplies one; a null-pointer result is zero. |
| <a id="contract-lifecycle-failure-errno"></a>`errno` | integer; omitted when absent | Native errno when the publication marks it present. |
| <a id="contract-lifecycle-failure-index"></a>`index` | integer; omitted when absent | Operation-specific zero-based item, such as a parameter or attempt; absence represents the worker's no-index sentinel. |
| <a id="contract-lifecycle-failure-detail"></a>`detail` | integer; required | Additional operation-specific numeric classification retained alongside the primary failure code. Admitted vocabulary: open; displayed list: illustrative: `0`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions. |

<a id="contract-lifecycle-readiness"></a>
#### Readiness-write result

Record `lc_readiness`: `PWWorkerReadiness`.

This is the worker's own publication of the readiness helper result. The helper retries EINTR and converts a one-byte write to success.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-readiness-rc"></a>`rc` | integer; required | Readiness-helper result: zero after one byte was written; -1 after a persistent failure. |
| <a id="contract-lifecycle-readiness-errno"></a>`errno` | integer; omitted when absent | Worker-captured errno accompanying a nonzero helper result; absent for rc zero. |

<a id="contract-lifecycle-diagnostic"></a>
#### Worker diagnostic

Record `lc_diagnostic`: `PWWorkerDiagnostic`.

The host exposes text only after acquiring a complete or truncated publication with a bounded length and terminating NUL.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-diagnostic-state"></a>`state` | integer; required | Raw diagnostic publication word: 0 absent, 1 complete, 2 truncated, 3 incomplete; other values remain numeric. Admitted vocabulary: open; displayed list: illustrative: `0`, `1`, `2`, `3`. Unfamiliar values: The numeric value remains in the report. Known-branch assessments require their own recognized code and publication conditions. |
| <a id="contract-lifecycle-diagnostic-status"></a>`status` | string; required | Host interpretation: absent, incomplete, unknown, complete, truncated or invalid. Invalid identifies an eligible publication whose length or terminator failed validation. Admitted vocabulary: closed; displayed list: exhaustive: `"absent"`, `"incomplete"`, `"unknown"`, `"complete"`, `"truncated"`, `"invalid"`. |
| <a id="contract-lifecycle-diagnostic-length"></a>`length` | integer; omitted when absent | Retained diagnostic-byte length excluding its terminating NUL, at most <!-- span limits.worker_diagnostic.value_unit -->4,095 bytes<!-- /span --> when validation permits text extraction. |
| <a id="contract-lifecycle-diagnostic-text"></a>`text` | string; omitted when absent | Diagnostic bytes decoded as UTF-8 with replacement for invalid sequences. The <!-- span limits.worker_diagnostic.value_unit -->4,095 bytes<!-- /span --> bound applies before replacement decoding. The diagnostic status carries whether the worker truncated its buffer. |

<a id="contract-lifecycle-policy_read"></a>
#### Worker policy receipt

Record `lc_policy_read`: `PWWorkerPolicyRead`.

At EOF the worker publishes both counts before comparing them. A header refusal, read failure or overflow leaves this receipt unavailable; both counts must fit the <!-- span limits.policy_source.value -->262,143<!-- /span -->-byte source capacity.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-policy_read-bytes_expected"></a>`bytes_expected` | integer; required | Host-selected UTF-8 byte count from the worker's immutable header input. |
| <a id="contract-lifecycle-policy_read-bytes_received"></a>`bytes_received` | integer; required | Bytes the worker read from the policy pipe when it observed EOF. Equality with bytes_expected establishes length agreement with the submitted bytes. |

<a id="contract-lifecycle-disposition"></a>
#### Canonical worker disposition

Record `lc_disposition`: `PWDispositionRecord`.

Run questions and per-step questions keep their individual support and conflicts.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-disposition-questions"></a>`questions` | [Run lifecycle questions](#contract-lifecycle-run_questions); required | Fixed set of run-level lifecycle claims. |
| <a id="contract-lifecycle-disposition-steps"></a>`steps` | array of [Step lifecycle account](#contract-lifecycle-step); required | Plan-ordered lifecycle claims for each requested step, joined only to uniquely identified worker slots. |
| <a id="contract-lifecycle-disposition-issues"></a>`issues` | array of [Lifecycle conflict](#contract-lifecycle-issue); required | Conflicting observations referenced by conflicting claims; indices are zero-based within this array. |

<a id="contract-lifecycle-disposition-resolve"></a>
##### Resolving lifecycle claims

[Runner host](#contract-identity-definitions-host) reports at final worker output and plan join. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Uses [Resolve the final process status](#contract-lifecycle-worker-final_status), [Copy the polling stop](#contract-lifecycle-worker-resolve_stop_reason), [Copy the final collection basis](#contract-lifecycle-worker-resolve_collection_basis), [Project ordinary canonical step claims](#contract-lifecycle-disposition-ordinary_projection), [Project actor canonical step claims](#contract-lifecycle-disposition-actor_projection). Resolve each question from the owning worker's acquired output, unique slot identities and submitted plan. A not_reached or unpublished conclusion requires terminal collection where specified below. Resolve and publish the canonical account once. Retain competing observations as conflict issues, and derive each per-attempt summary from its canonical claims and attempt applicability.

A completed supported slot establishes publication and
can establish entry. Recognized progress at or after an attempt's entry also
establishes entry. A final earlier progress position establishes `not_reached`
only after confirmed reaping and with an incomplete slot; beside a completed
slot it produces D5. Returned-or-later terminal progress beside an incomplete
supported slot produces D5 for result publication. Live collection leaves
missing results unresolved. An unsupported attempt has inapplicable result
publication and an `unsupported` lifecycle summary.

<a id="contract-lifecycle-disposition-ordinary_projection"></a>
##### Project ordinary canonical step claims

[Runner host](#contract-identity-definitions-host) reports at per-step canonical lifecycle projection. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Binding `s`: entry in `reply.steps`. Binding `c`: entry in `reply.runner_subprocess.disposition.steps`. Binding `d`: entry in `reply.runner_subprocess.disposition.steps`. Association restriction for `c`: `reply.runner_subprocess.disposition.steps[c].step_id` = `reply.steps[s].step_id`. Association restriction for `d`: (`reply.runner_subprocess.disposition.steps[d].step_id` = `reply.steps[s].step_id` and `d` < `c`). For each `s`, `c`. Applies when (`reply.runner_subprocess` is present and `reply.runner_subprocess.disposition` is present and number of matching entries for `d` = `0`).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-lifecycle-disposition-ordinary_projection-presence"></a>Both canonical claims produce the projection | Requires (if (`reply.runner_subprocess.disposition.steps[c].questions.step_boundary_reached` is present and `reply.runner_subprocess.disposition.steps[c].questions.step_result_published` is present), then `reply.steps[s].attempt.lifecycle` is present). |
| <a id="contract-lifecycle-disposition-ordinary_projection-copy"></a>Copy the canonical claims | Applies when (`reply.runner_subprocess.disposition.steps[c].questions.step_boundary_reached` is present and `reply.runner_subprocess.disposition.steps[c].questions.step_result_published` is present). sets `reply.steps[s].attempt.lifecycle.boundary` to `reply.runner_subprocess.disposition.steps[c].questions.step_boundary_reached`, sets `reply.steps[s].attempt.lifecycle.result` to `reply.runner_subprocess.disposition.steps[c].questions.step_result_published`. |
| <a id="contract-lifecycle-disposition-ordinary_projection-missing"></a>Missing canonical claim | Applies when not ((`reply.runner_subprocess.disposition.steps[c].questions.step_boundary_reached` is present and `reply.runner_subprocess.disposition.steps[c].questions.step_result_published` is present)). withholds `reply.steps[s].attempt.lifecycle`. |

**Support: [source read](#contract-support-grades) for [Project ordinary canonical step claims](#contract-lifecycle-disposition-ordinary_projection) and its descendants.** The ordinary and actor builders select the first matching canonical step; attemptLifecycle copies both claims when present and returns nil otherwise. Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `attemptLifecycle`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildStepResults`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`.

<a id="contract-lifecycle-disposition-actor_projection"></a>
##### Project actor canonical step claims

[Runner host](#contract-identity-definitions-host) reports at per-step canonical lifecycle projection. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Binding `a`: entry in `reply.actors`. Binding `s`: entry in `reply.steps`. Binding `c`: entry in `reply.actors[a].subprocess.disposition.steps`. Binding `d`: entry in `reply.actors[a].subprocess.disposition.steps`. Association restriction for `c`: `reply.actors[a].subprocess.disposition.steps[c].step_id` = `reply.steps[s].step_id`. Association restriction for `d`: (`reply.actors[a].subprocess.disposition.steps[d].step_id` = `reply.steps[s].step_id` and `d` < `c`). Association restriction for `s`: `reply.steps[s].actor_id` = `reply.actors[a].actor_id`. For each `a`, `s`, `c`. Applies when (`reply.actors` is present and `reply.actors[a].subprocess` is present and `reply.actors[a].subprocess.disposition` is present and number of matching entries for `d` = `0`).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-lifecycle-disposition-actor_projection-presence"></a>Both canonical claims produce the projection | Requires (if (`reply.actors[a].subprocess.disposition.steps[c].questions.step_boundary_reached` is present and `reply.actors[a].subprocess.disposition.steps[c].questions.step_result_published` is present), then `reply.steps[s].attempt.lifecycle` is present). |
| <a id="contract-lifecycle-disposition-actor_projection-copy"></a>Copy the canonical claims | Applies when (`reply.actors[a].subprocess.disposition.steps[c].questions.step_boundary_reached` is present and `reply.actors[a].subprocess.disposition.steps[c].questions.step_result_published` is present). sets `reply.steps[s].attempt.lifecycle.boundary` to `reply.actors[a].subprocess.disposition.steps[c].questions.step_boundary_reached`, sets `reply.steps[s].attempt.lifecycle.result` to `reply.actors[a].subprocess.disposition.steps[c].questions.step_result_published`. |
| <a id="contract-lifecycle-disposition-actor_projection-missing"></a>Missing canonical claim | Applies when not ((`reply.actors[a].subprocess.disposition.steps[c].questions.step_boundary_reached` is present and `reply.actors[a].subprocess.disposition.steps[c].questions.step_result_published` is present)). withholds `reply.steps[s].attempt.lifecycle`. |

**Support: [source read](#contract-support-grades) for [Project actor canonical step claims](#contract-lifecycle-disposition-actor_projection) and its descendants.** The ordinary and actor builders select the first matching canonical step; attemptLifecycle copies both claims when present and returns nil otherwise. Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `attemptLifecycle`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildStepResults`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`.

<a id="contract-lifecycle-claim"></a>
#### Lifecycle claim

Record `lc_claim`: `PWDispositionClaim`.

A supported claim names its answer and observation references. An unresolved or inapplicable claim names its reason; a conflicting claim points to its issue.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-claim-state"></a>`state` | string; required | supported, unresolved, conflicting or inapplicable, determining which accompanying fields carry the claim. Admitted vocabulary: closed; displayed list: exhaustive: `"supported"`, `"unresolved"`, `"conflicting"`, `"inapplicable"`. |
| <a id="contract-lifecycle-claim-answer"></a>`answer` | string; omitted when absent | Question-specific supported answer, such as signal, exit_code, reached, published or an observed host stop reason. |
| <a id="contract-lifecycle-claim-value"></a>`value` | [Lifecycle answer value](#contract-lifecycle-claim_value); omitted when absent | Answer payload: an exit code, signal or item index as an integer, or the observed termination-request object. |
| <a id="contract-lifecycle-claim-reason"></a>`reason` | string; omitted when absent | Reason the question is unresolved or inapplicable, preserving missing, unusable, nonterminal and unsupported evidence distinctions. |
| <a id="contract-lifecycle-claim-issue"></a>`issue` | integer; omitted when absent | Zero-based pointer to the matching conflict in disposition.issues. |
| <a id="contract-lifecycle-claim-basis"></a>`basis` | array of string; omitted when absent | Observation references supporting the answer or explaining uncertainty: raw run fields, progress, worker_failure, plan, slot and attempt_support in their question's scope. |

<a id="contract-lifecycle-claim_value"></a>
#### Lifecycle answer value

Record `lc_claim_value`: `PWDispositionValue`.

| Alternative | Record |
| --- | --- |
| `Integer` | `Int` |
| `Request` | [Host termination request](#contract-lifecycle-termination) |

<a id="contract-lifecycle-issue"></a>
#### Lifecycle conflict

Record `lc_issue`: `PWDispositionIssue`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-issue-kind"></a>`kind` | string; required | conflict for a resolver-created disagreement among observations. |
| <a id="contract-lifecycle-issue-rule"></a>`rule` | string; required | D1 for competing terminal status representations; D5 for incompatible terminal progress and slot publication. |
| <a id="contract-lifecycle-issue-question"></a>`question` | string; required | Lifecycle question affected by this issue. |
| <a id="contract-lifecycle-issue-step_index"></a>`step_index` | integer; omitted when absent | Zero-based plan step for a step issue; absent for a run-level issue. |
| <a id="contract-lifecycle-issue-observations"></a>`observations` | array of string; required | Named observations involved in the conflict, resolved in the same run or step scope. |
| <a id="contract-lifecycle-issue-detail"></a>`detail` | string; required | Human-readable description of the incompatible observations. |

<a id="contract-lifecycle-run_questions"></a>
#### Run lifecycle questions

Record `lc_run_questions`: `PWDispositionRunQuestions`.

Ordinary resolution supplies every question; absent slots preserve partial or rejected evidence for readers.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-run_questions-final_status"></a>`final_status` | [Lifecycle claim](#contract-lifecycle-claim); omitted when absent | Whether a successful owned reap supplies an exit code or terminating signal; competing representations produce a D1 conflict. |
| <a id="contract-lifecycle-run_questions-stop_reason"></a>`stop_reason` | [Lifecycle claim](#contract-lifecycle-claim); omitted when absent | Host polling-stop observation, or unresolved when it was not recorded. |
| <a id="contract-lifecycle-run_questions-cleanup_trigger"></a>`cleanup_trigger` | [Lifecycle claim](#contract-lifecycle-claim); omitted when absent | Recorded reason for requesting exit; inapplicable when exit_requested is false. |
| <a id="contract-lifecycle-run_questions-grace_end"></a>`grace_end` | [Lifecycle claim](#contract-lifecycle-claim); omitted when absent | Recorded end of the exit-grace stage; inapplicable when exit_requested is false. |
| <a id="contract-lifecycle-run_questions-kill_request_and_result"></a>`kill_request_and_result` | [Lifecycle claim](#contract-lifecycle-claim); omitted when absent | The observed termination request, a supported none after a recorded exit request, or the corresponding unresolved/inapplicable state. |
| <a id="contract-lifecycle-run_questions-collection_basis"></a>`collection_basis` | [Lifecycle claim](#contract-lifecycle-claim); omitted when absent | Host fact stating whether final reads followed confirmed reaping or execution might continue. |
| <a id="contract-lifecycle-run_questions-progress_association"></a>`progress_association` | [Lifecycle claim](#contract-lifecycle-claim); omitted when absent | Association of the packed progress word with no item, a step index or a parameter index; invalid packing is distinguished from an unfamiliar operation/stage. |

<a id="contract-lifecycle-step"></a>
#### Step lifecycle account

Record `lc_step`: `PWDispositionStep`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-step-index"></a>`index` | integer; required | Zero-based position of this step in the owning worker's plan. |
| <a id="contract-lifecycle-step-step_id"></a>`step_id` | string; required | Submitted step identifier used to join its worker slot and public step. |
| <a id="contract-lifecycle-step-slot"></a>`slot` | string; required | completed, incomplete or absent according to the uniquely associated worker slot and its completion publication. Admitted vocabulary: closed; displayed list: exhaustive: `"completed"`, `"incomplete"`, `"absent"`. |
| <a id="contract-lifecycle-step-attempt_support"></a>`attempt_support` | string; required | supported or unsupported according to whether the requested attempt has an implemented worker mapping. Admitted vocabulary: closed; displayed list: exhaustive: `"supported"`, `"unsupported"`. |
| <a id="contract-lifecycle-step-questions"></a>`questions` | [Step lifecycle questions](#contract-lifecycle-step_questions); required | Boundary, result-publication and requested-operation applicability claims for this step. |

<a id="contract-lifecycle-step_questions"></a>
#### Step lifecycle questions

Record `lc_step_questions`: `PWDispositionStepQuestions`.

The result and boundary questions preserve distinct observations: a call can start without publishing a completed result.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-step_questions-step_boundary_reached"></a>`step_boundary_reached` | [Lifecycle claim](#contract-lifecycle-claim); omitted when absent | Whether recognized progress or a supported completed slot establishes entry; terminal earlier progress can establish not_reached or conflict with a completed slot. |
| <a id="contract-lifecycle-step_questions-step_result_published"></a>`step_result_published` | [Lifecycle claim](#contract-lifecycle-claim); omitted when absent | Whether a supported completed slot is published; incomplete terminal collection can establish unpublished, while live collection remains unresolved. |
| <a id="contract-lifecycle-step_questions-step_requested_operation_applicability"></a>`step_requested_operation_applicability` | [Lifecycle claim](#contract-lifecycle-claim); omitted when absent | Whether this requested attempt maps to an implemented worker operation, as stated by attempt_support. |

<a id="contract-lifecycle-attempt"></a>
#### Per-attempt lifecycle projection

Record `lc_attempt`: `PWAttemptLifecycle`.

A step or extension event carries this compact projection of its canonical disposition claims.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-attempt-summary"></a>`summary` | string; required | The current producer derives completed, started_without_result, not_reached, unsupported, unresolved or conflicting from the boundary/result claims and attempt support. The controller retains unfamiliar summary strings; it checks the recognized summaries against their corresponding claims. Admitted vocabulary: open; displayed list: illustrative: `"completed"`, `"started_without_result"`, `"not_reached"`, `"unsupported"`, `"unresolved"`, `"conflicting"`. Unfamiliar values: The controller retains an unfamiliar summary and checks the independently carried boundary and result claims. |
| <a id="contract-lifecycle-attempt-boundary"></a>`boundary` | [Lifecycle claim](#contract-lifecycle-claim); required | Copy of the owning disposition step's step_boundary_reached claim. |
| <a id="contract-lifecycle-attempt-result"></a>`result` | [Lifecycle claim](#contract-lifecycle-claim); required | Copy of the owning disposition step's step_result_published claim. |

<a id="contract-lifecycle-owned_reap"></a>
#### Owned child ending

Record `lc_owned_reap`: `PWOwnedReapObservation`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-owned_reap-pid"></a>`pid` | integer; required | Owned child PID for which the host obtained terminal wait status. |
| <a id="contract-lifecycle-owned_reap-native_rc"></a>`native_rc` | integer; required | Native waitpid return equal to pid for this captured ending. |
| <a id="contract-lifecycle-owned_reap-raw_status"></a>`raw_status` | integer; required | Raw terminal wait status, from which the corresponding exit code or signal is decoded. |
| <a id="contract-lifecycle-owned_reap-stage"></a>`stage` | string; required | Host capture stage, including schedule, termination_gate and cleanup stages; the gate admits schedule or termination_gate for natural-departure support. |
| <a id="contract-lifecycle-owned_reap-observed_ns"></a>`observed_ns` | integer; omitted when absent | Host monotonic capture time in nanoseconds, when available. |
| <a id="contract-lifecycle-owned_reap-ownership_unbroken"></a>`ownership_unbroken` | boolean; required | Whether the host retained uninterrupted ownership through this wait observation. |
| <a id="contract-lifecycle-owned_reap-departure_requested"></a>`departure_requested` | boolean; required | Whether the host had already requested this child's departure when it captured the ending. |
| <a id="contract-lifecycle-owned_reap-capture_ordinal"></a>`capture_ordinal` | integer; required | Positive ordinal in this child's host-observation sequence, shared with its activations and gate captures. |

<a id="contract-lifecycle-reap_reference"></a>
#### Owned-ending reference

Record `lc_reap_reference`: `PWOwnedReapReference`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-reap_reference-capture_ordinal"></a>`capture_ordinal` | integer; required | Ordinal of the source actor's owned ending; its association must match that source's owned_reap record. |

<a id="contract-lifecycle-spawn_failure"></a>
#### Native spawn failure

Record `lc_spawn_failure`: `PWRunnerSpawnFailure`.

The host retains the failed spawn operation as a separate record before a child process exists.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-spawn_failure-origin"></a>`origin` | string; required | Component reporting the failure, supplied by the runner host. |
| <a id="contract-lifecycle-spawn_failure-operation"></a>`operation` | string; required | Failed native spawn operation, such as posix_spawn. |
| <a id="contract-lifecycle-spawn_failure-executable_path"></a>`executable_path` | string; required | Executable path passed to the attempted spawn. |
| <a id="contract-lifecycle-spawn_failure-return_code"></a>`return_code` | integer; required | Native spawn return code, whose error-code convention is distinct from a child exit status. |
| <a id="contract-lifecycle-spawn_failure-diagnostic"></a>`diagnostic` | string; required | Human-readable native error explanation of the spawn failure. |

<a id="contract-lifecycle-validator"></a>
#### Validator subprocess

Record `lc_validator`: `PWRunnerValidatorSubprocess`.

The host binds each validator collection to its phase and retains accepted records through later I/O, association or cleanup failure.

For N submitted queries, the collector assigns a record allowance of max(1, N) multiplied by <!-- span limits.validator_records_per_query.value -->2<!-- /span --> and a stdout retention allowance of max(1, N) multiplied by <!-- span limits.validator_reply_bytes_per_query.value_unit -->16,384 bytes<!-- /span -->. The allowances are sized before writing the query batch. On byte overflow the host counts all bytes received, keeps the bounded prefix through its last complete LF frame, closes collection and reports byte_limit. Decoding retains complete accepted records before the first refused frame or record-count excess.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-validator-phase_id"></a>`phase_id` | string; omitted when absent | Host-stamped phase identifier served by this collection; agrees with the containing phase. |
| <a id="contract-lifecycle-validator-ordinal"></a>`ordinal` | integer; omitted when absent | Host-stamped one-based phase ordinal for this collection. |
| <a id="contract-lifecycle-validator-pid"></a>`pid` | integer; required | Spawned validator PID used for collection and owned cleanup. |
| <a id="contract-lifecycle-validator-term_signal"></a>`term_signal` | integer; omitted when absent | Signal decoded only from a successful waitpid result for this validator. |
| <a id="contract-lifecycle-validator-exit_code"></a>`exit_code` | integer; omitted when absent | Exit status decoded only from a successful waitpid result for this validator. |
| <a id="contract-lifecycle-validator-reaped"></a>`reaped` | boolean; omitted when absent | True for a confirmed owned reap, false for an unconfirmed ending, absent when unreported. |
| <a id="contract-lifecycle-validator-termination_request"></a>`termination_request` | [Host termination request](#contract-lifecycle-termination); omitted when absent | Host kill request and native return, if requested during validator cleanup. |
| <a id="contract-lifecycle-validator-wait_errors"></a>`wait_errors` | array of [Failed host wait](#contract-lifecycle-wait_error); omitted when absent | Failed waitpid observations from validator cleanup, including recovered interruptions. |
| <a id="contract-lifecycle-validator-read_error"></a>`read_error` | string; omitted when absent | Host diagnostic for stdout-read failure, separate from accepted record contents. |
| <a id="contract-lifecycle-validator-stdout_collection_stop"></a>`stdout_collection_stop` | string; omitted when absent | Host reason for stopping stdout collection: eof, clock_error, deadline, poll_error, byte_limit or read_error. This is fixed before the exit-grace stage. |
| <a id="contract-lifecycle-validator-stdout_bytes_received"></a>`stdout_bytes_received` | integer; omitted when absent | Total stdout bytes received by the host, including bytes later rejected by frame decoding. |
| <a id="contract-lifecycle-validator-probe_bytes_written"></a>`probe_bytes_written` | integer; omitted when absent | Request bytes accepted by host writes to the validator input pipe. |
| <a id="contract-lifecycle-validator-probe_bytes_expected"></a>`probe_bytes_expected` | integer; omitted when absent | Serialized request-batch byte count the host intended to write. |
| <a id="contract-lifecycle-validator-io_error"></a>`io_error` | string; omitted when absent | Host transport diagnostic for the first request-write or stdout-read failure selected for this collection. |
| <a id="contract-lifecycle-validator-decode_fault"></a>`decode_fault` | [Rejected validator frame](#contract-lifecycle-decode_fault); omitted when absent | First rejected stdout frame's receiver-owned diagnostic and bounded byte prefix. |
| <a id="contract-lifecycle-validator-records"></a>`records` | array of [Accepted validator record](#contract-steps-verdict); omitted when absent | Accepted verdict records in received order, including diagnostic, unexpected-ID and null-ID records, within this phase collector's record allowance. |
| <a id="contract-lifecycle-validator-expected_step_ids"></a>`expected_step_ids` | array of string; omitted when absent | Submitted query IDs in the planned collection; used to check missing, duplicate and unexpected associations. |
| <a id="contract-lifecycle-validator-association_issues"></a>`association_issues` | array of [Validator query association](#contract-lifecycle-association_issue); omitted when absent | Host-computed join problems; an empty array records a complete unambiguous join for the expected queries. |
| <a id="contract-lifecycle-validator-exit_grace_wait"></a>`exit_grace_wait` | [Measured host wait](#contract-lifecycle-host_wait); omitted when absent | Measured monotonic host wait after collection closed, with production allowance <!-- span limits.validator_exit_grace.value_unit -->1,000 milliseconds<!-- /span -->, before any further termination/reap work. Those later operations can continue beyond this allowance. |

<a id="contract-lifecycle-validator-associate"></a>
##### Joining accepted validator records

[Runner host](#contract-identity-definitions-host) reports at closed phase query collection. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. retains the records `lc_validator.records`. Uses [Count expected and unexpected associations](#contract-lifecycle-validator-cardinality). A unique expected-ID record enters the per-step join only when every supplied query metadata value agrees with the submitted query. Allow/deny records must supply the complete submitted query identity. Publish association issues in expected-query order, then unexpected IDs in sorted order, then a null-ID issue when present. Withhold each failed per-step join while retaining accepted records.

Duplicate IDs leave every record of that group at collection scope. Null IDs
remain unassociated. Diagnostic outcomes may omit query metadata; any supplied
metadata must agree.

<a id="contract-lifecycle-validator-cardinality"></a>
##### Count expected and unexpected associations

[Runner host](#contract-identity-definitions-host) reports at closed validator collection association. Entry: xpc execute. Recipient: controller, xpc caller. Reports: runner reply. Applies when (`lc_validator.records` is present and `lc_validator.expected_step_ids` is present and `lc_validator.association_issues` is present).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-lifecycle-validator-cardinality-expected"></a>Expected identifier groups | Binding `e`: entry in `lc_validator.expected_step_ids`. Binding `f`: entry in `lc_validator.expected_step_ids`. Binding `v`: entry in `lc_validator.records`. Binding `i`: entry in `lc_validator.association_issues`. Association restriction for `f`: `lc_validator.expected_step_ids[f]` = `lc_validator.expected_step_ids[e]`. Association restriction for `v`: `lc_validator.records[v].step_id` = `lc_validator.expected_step_ids[e]`. Association restriction for `i`: `lc_validator.association_issues[i].step_id` = `lc_validator.expected_step_ids[e]`. For each `e`. Requires (if number of matching entries for `v` ≠ `1`, then number of matching entries for `i` = number of matching entries for `f`). |
| <a id="contract-lifecycle-validator-cardinality-expected-missing"></a>Expected identifier groups › Missing group | For each `e`, `i`. Requires (if number of matching entries for `v` = `0`, then (`lc_validator.association_issues[i].kind` = `"missing_id"` and `lc_validator.association_issues[i].count` = `0`)). |
| <a id="contract-lifecycle-validator-cardinality-expected-duplicate"></a>Expected identifier groups › Duplicate group | For each `e`, `i`. Requires (if number of matching entries for `v` > `1`, then (`lc_validator.association_issues[i].kind` = `"duplicate_id"` and `lc_validator.association_issues[i].count` = number of matching entries for `v`)). |
| <a id="contract-lifecycle-validator-cardinality-unexpected"></a>Unexpected identifier groups | Binding `v`: entry in `lc_validator.records`. Binding `e`: entry in `lc_validator.expected_step_ids`. Binding `g`: entry in `lc_validator.records`. Binding `i`: entry in `lc_validator.association_issues`. Association restriction for `e`: `lc_validator.expected_step_ids[e]` = `lc_validator.records[v].step_id`. Association restriction for `g`: `lc_validator.records[g].step_id` = `lc_validator.records[v].step_id`. Association restriction for `i`: `lc_validator.association_issues[i].step_id` = `lc_validator.records[v].step_id`. For each `v`. Requires (if (`lc_validator.records[v].step_id` is present and number of matching entries for `e` = `0`), then number of matching entries for `i` = `1`). |
| <a id="contract-lifecycle-validator-cardinality-unexpected-count"></a>Unexpected identifier groups › Unexpected group count | For each `v`, `i`. Requires (if (`lc_validator.records[v].step_id` is present and number of matching entries for `e` = `0`), then (`lc_validator.association_issues[i].kind` = `"unexpected_id"` and `lc_validator.association_issues[i].count` = number of matching entries for `g`)). |
| <a id="contract-lifecycle-validator-cardinality-unassociated"></a>Unassociated records | Binding `v`: entry in `lc_validator.records`. Binding `i`: entry in `lc_validator.association_issues`. Association restriction for `v`: `lc_validator.records[v].step_id` is absent. Association restriction for `i`: (`lc_validator.association_issues[i].step_id` is absent and `lc_validator.association_issues[i].kind` = `"unassociated"`). Requires ((if number of matching entries for `v` > `0`, then number of matching entries for `i` = `1`) and (if number of matching entries for `v` = `0`, then number of matching entries for `i` = `0`)). |
| <a id="contract-lifecycle-validator-cardinality-unassociated-count"></a>Unassociated records › Unassociated count | For each `i`. Requires `lc_validator.association_issues[i].count` = number of matching entries for `v`. |

**Support: [source read](#contract-support-grades) for [Count expected and unexpected associations](#contract-lifecycle-validator-cardinality) and its descendants.** Groups are formed from every accepted non-null ID before metadata comparison; missing/duplicate/unexpected/null-ID groups preserve their actual counts. Source: [PWRunnerPredictionEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift): `validatorAssociationIssues`.

<a id="contract-lifecycle-decode_fault"></a>
#### Rejected validator frame

Record `lc_decode_fault`: `PWValidatorDecodeFault`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-decode_fault-origin"></a>`origin` | string; required | runner_host, identifying the rejecting receiver. |
| <a id="contract-lifecycle-decode_fault-kind"></a>`kind` | string; required | Receiver category utf8, json or structure for the first rejected frame. Admitted vocabulary: closed; displayed list: exhaustive: `"utf8"`, `"json"`, `"structure"`. |
| <a id="contract-lifecycle-decode_fault-message"></a>`message` | string; required | Human-readable reason the frame failed structural admission. |
| <a id="contract-lifecycle-decode_fault-byte_offset"></a>`byte_offset` | integer; required | Zero-based offset of the rejected frame's first byte in received stdout. |
| <a id="contract-lifecycle-decode_fault-frame_bytes"></a>`frame_bytes` | integer; required | Length of that frame in bytes, excluding its LF separator. |
| <a id="contract-lifecycle-decode_fault-retained_bytes"></a>`retained_bytes` | integer; required | Number of prefix bytes retained, capped at 256. |
| <a id="contract-lifecycle-decode_fault-context_b64"></a>`context_b64` | string (base64); required | Base64 encoding of the retained received-byte prefix. Decoding yields those exact bytes. |
| <a id="contract-lifecycle-decode_fault-context_truncated"></a>`context_truncated` | boolean; required | True when frame_bytes exceeds retained_bytes. |

<a id="contract-lifecycle-association_issue"></a>
#### Validator query association

Record `lc_association_issue`: `PWValidatorAssociationIssue`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-association_issue-origin"></a>`origin` | string; required | runner_host, identifying the component computing the association issue. |
| <a id="contract-lifecycle-association_issue-kind"></a>`kind` | string; required | missing_id, duplicate_id, query_mismatch, unexpected_id or unassociated. Admitted vocabulary: closed; displayed list: exhaustive: `"missing_id"`, `"duplicate_id"`, `"query_mismatch"`, `"unexpected_id"`, `"unassociated"`. |
| <a id="contract-lifecycle-association_issue-step_id"></a>`step_id` | string; omitted when absent | Expected or unexpected ID concerned by the issue; absent for records whose verdict ID is null. |
| <a id="contract-lifecycle-association_issue-count"></a>`count` | integer; required | Number of accepted records involved: zero for missing_id, one for query_mismatch, the group size for duplicate/unexpected IDs, or total null-ID records for unassociated. |

<a id="contract-lifecycle-exec"></a>
#### Spawned-command observation

Record `lc_exec`: `PWExecObservation`.

A completed worker exec slot separates collection, cleanup requests and the owned leader reap. Collection facts are frozen before termination requests.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-exec-collection"></a>`collection` | [Exec collection](#contract-lifecycle-exec_collection); required | Leader-exit and pipe observations up to the collection stop. |
| <a id="contract-lifecycle-exec-cleanup"></a>`cleanup` | [Exec cleanup](#contract-lifecycle-exec_cleanup); required | Requests to terminate the spawned process group and any leader fallback. |
| <a id="contract-lifecycle-exec-reap"></a>`reap` | [Exec leader reap](#contract-lifecycle-exec_reap); required | Final bounded wait account for the owned leader after collection and cleanup. |

<a id="contract-lifecycle-exec_collection"></a>
#### Exec collection

Record `lc_exec_collection`: `PWExecCollectionObservation`.

The collector can observe leader exit and pipe EOF independently; descendants may keep a stream open after the leader exits.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-exec_collection-stop_reason"></a>`stop_reason` | string; required | leader_exit_and_eof, deadline, observation_error or clock_fault, recording the branch that stopped collection. Admitted vocabulary: closed; displayed list: exhaustive: `"leader_exit_and_eof"`, `"deadline"`, `"observation_error"`, `"clock_fault"`. |
| <a id="contract-lifecycle-exec_collection-leader_exit_observed"></a>`leader_exit_observed` | boolean; required | Whether waitid observed the owned leader's exit during collection. |
| <a id="contract-lifecycle-exec_collection-stdout"></a>`stdout` | [Exec stream observation](#contract-lifecycle-exec_stream); required | EOF or native read/poll failure retained for stdout. |
| <a id="contract-lifecycle-exec_collection-stderr"></a>`stderr` | [Exec stream observation](#contract-lifecycle-exec_stream); required | EOF or native read/poll failure retained for stderr. |
| <a id="contract-lifecycle-exec_collection-deadline_kind"></a>`deadline_kind` | string; omitted when absent | child or plan when the selected collection deadline expires; absent on other stop branches. The child allowance and remaining per-worker active-plan allowance are defined by the exec operation. Uses [Exec setup and child inputs](#contract-probes-attempt-exec). Admitted vocabulary: closed; displayed list: exhaustive: `"child"`, `"plan"`. |
| <a id="contract-lifecycle-exec_collection-waitid_errno"></a>`waitid_errno` | integer; omitted when absent | Native waitid failure which stopped leader observation; recovered EINTR is excluded. |
| <a id="contract-lifecycle-exec_collection-poll_errno"></a>`poll_errno` | integer; omitted when absent | Native poll failure which stopped stream observation; recovered EINTR is excluded. |
| <a id="contract-lifecycle-exec_collection-clock_fault"></a>`clock_fault` | integer; omitted when absent | Local numeric clock-fault observation when collection stopped for failed/backward time. |

<a id="contract-lifecycle-exec_stream"></a>
#### Exec stream observation

Record `lc_exec_stream`: `PWExecStreamObservation`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-exec_stream-eof"></a>`eof` | boolean; required | Whether the worker read EOF on this stream before collection stopped. |
| <a id="contract-lifecycle-exec_stream-read_errno"></a>`read_errno` | integer; omitted when absent | Terminal read errno, excluding recovered EINTR and EAGAIN. |
| <a id="contract-lifecycle-exec_stream-poll_revents"></a>`poll_revents` | integer; omitted when absent | Terminal error/invalid descriptor poll bits retained when they ended observation; ordinary readable/EOF handling uses its own read observation. |

<a id="contract-lifecycle-exec_cleanup"></a>
#### Exec cleanup

Record `lc_exec_cleanup`: `PWExecCleanupObservation`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-exec_cleanup-state"></a>`state` | string; required | not_requested after leader_exit_and_eof; ownership_unconfirmed when waitid failed; requested when an eligible process-group cleanup was attempted. Admitted vocabulary: closed; displayed list: exhaustive: `"not_requested"`, `"ownership_unconfirmed"`, `"requested"`. |
| <a id="contract-lifecycle-exec_cleanup-group_request"></a>`group_request` | [Exec signal request](#contract-lifecycle-exec_signal); omitted when absent | SIGKILL request to negative leader PID for the owned process group, when cleanup is requested. |
| <a id="contract-lifecycle-exec_cleanup-leader_fallback"></a>`leader_fallback` | [Exec signal request](#contract-lifecycle-exec_signal); omitted when absent | SIGKILL request to the positive leader PID after a failed group request with errno other than ESRCH. |

<a id="contract-lifecycle-exec_signal"></a>
#### Exec signal request

Record `lc_exec_signal`: `PWExecSignalRequest`.

This is the worker's native kill call for a spawned command, scoped to the target named here.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-exec_signal-target"></a>`target` | integer; required | Negative leader PID for a process-group request, or positive leader PID for the fallback request. |
| <a id="contract-lifecycle-exec_signal-signal"></a>`signal` | integer; required | Signal passed to kill; the exec cleanup path uses SIGKILL. |
| <a id="contract-lifecycle-exec_signal-rc"></a>`rc` | integer; required | Native kill return, zero or -1. |
| <a id="contract-lifecycle-exec_signal-errno"></a>`errno` | integer; omitted when absent | Positive native errno captured for rc -1; absent after success. |

<a id="contract-lifecycle-exec_reap"></a>
#### Exec leader reap

Record `lc_exec_reap`: `PWExecReapObservation`.

Final wait facts concern the spawned leader owned by the worker. After collection ends, the production reap allowance is <!-- span limits.exec_reap_grace.value_unit -->1,000 milliseconds<!-- /span --> of continuous time. Earlier ownership or group-request failures retain their branch priority; a recorded request and an observed reap remain separate.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-exec_reap-stop_reason"></a>`stop_reason` | string; required | reaped, wait_error, ownership_unconfirmed, group_request_failed, clock_fault or deadline; branch priority preserves earlier ownership/group-request failures. Admitted vocabulary: closed; displayed list: exhaustive: `"reaped"`, `"wait_error"`, `"ownership_unconfirmed"`, `"group_request_failed"`, `"clock_fault"`, `"deadline"`. |
| <a id="contract-lifecycle-exec_reap-last_wait"></a>`last_wait` | [Exec leader wait result](#contract-lifecycle-exec_wait); required | Last native waitpid result, with status only when the owned leader PID returned. |
| <a id="contract-lifecycle-exec_reap-clock_fault"></a>`clock_fault` | integer; omitted when absent | Local numeric clock fault encountered by the reap wait, when observed. |

<a id="contract-lifecycle-exec_wait"></a>
#### Exec leader wait result

Record `lc_exec_wait`: `PWExecWaitObservation`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-lifecycle-exec_wait-rc"></a>`rc` | integer; required | Native waitpid return: zero pending, -1 failure, or owned leader PID when reaped. |
| <a id="contract-lifecycle-exec_wait-errno"></a>`errno` | integer; omitted when absent | Positive captured errno for rc -1, including EINTR; absent otherwise. |
| <a id="contract-lifecycle-exec_wait-status"></a>`status` | integer; omitted when absent | Raw terminal wait status present exactly when rc is the owned leader PID, agreeing with the attempt's leader exit/signal fields. |

**Support: [source read](#contract-support-grades) for [Process and operation observations](#contract-lifecycle) and its descendants.** Imported public field definitions joined to producer/decoder/assessment meanings; explicit rule and evidence gaps preserve scope. Source: [PWRunnerLifecycleEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerLifecycleEvidence.swift): `PWRunnerSubprocess`; [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `decodeWorkerEvidence`, `CWorkerInput`; [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `resolveDisposition`; [PWRunnerDisposition.swift](../runner/Sources/PWRunnerCore/PWRunnerDisposition.swift): `lifecycleSummary`; [PWRunnerPredictionEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift): `validatorAssociationIssues`; [ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift): `decodeValidatorFrames`, `runValidator`; [PWRunnerAttemptEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift): `execObservationEvidenceProblem`; [PWRunnerAuthoritySetup.swift](../runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift): `PWOwnedReapObservation`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `write_ready_byte`; [ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift): `readyBudgetMs`; [pw_probe_runner_abi.h](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h): `PW_SHM_DIAGNOSTIC_BYTES`; [pw_worker_timing.h](../controller/tools/pw_probe_runner/pw_worker_timing.h): `PW_EXEC_REAP_GRACE_MS`.

<a id="contract-actor_evidence"></a>
### Actor and phase evidence

<a id="contract-actor_evidence-actor"></a>
#### Actor process account

Record `ae_actor`: `PWRunnerActorResult`.

The host emits actors in request order. Each actor owns its launch, worker publications, policy receipt, equipment read-back and lifecycle account.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actor_evidence-actor-actor_id"></a>`actor_id` | string; required | Submitted actor identifier that binds this row to its phases and resources. Ordinary semantic replies require nonempty, NUL-free actor identifiers within their admitted UTF-8 capacity, distinct identifiers and request order. |
| <a id="contract-actor_evidence-actor-index"></a>`index` | integer; required | Zero-based position in the admitted actor list. |
| <a id="contract-actor_evidence-actor-mode"></a>`mode` | string; required | Submitted sandbox mode, apply or unapplied. Admitted vocabulary: closed; displayed list: exhaustive: `"apply"`, `"unapplied"`. |
| <a id="contract-actor_evidence-actor-policy_format"></a>`policy_format` | string; omitted when absent | Selected policy representation for an apply actor, when provided. |
| <a id="contract-actor_evidence-actor-policy_sha256"></a>`policy_sha256` | string (hex); omitted when absent | Host SHA-256 of the selected submitted source bytes after controller augmentation. |
| <a id="contract-actor_evidence-actor-policy_received_sha256"></a>`policy_received_sha256` | string (hex); omitted when absent | Worker SHA-256 of the bytes it actually read before compilation, when published. |
| <a id="contract-actor_evidence-actor-setup_status"></a>`setup_status` | string; required | Host setup classification: not_launched, launch_refused, transfer_failed, applied, unapplied_declared, setup_failed, authority_setup_failed, exited_before_setup or setup_timeout. Admitted vocabulary: closed; displayed list: exhaustive: `"not_launched"`, `"launch_refused"`, `"transfer_failed"`, `"applied"`, `"unapplied_declared"`, `"setup_failed"`, `"authority_setup_failed"`, `"exited_before_setup"`, `"setup_timeout"`. |
| <a id="contract-actor_evidence-actor-applied"></a>`applied` | boolean; omitted when absent | Acquired worker applied flag for apply mode when output exists; absent for an unapplied declaration or unavailable output. |
| <a id="contract-actor_evidence-actor-application_count"></a>`application_count` | integer; required | Zero or one from the final acquired applied publication, retained even when a setup deadline already ended eligibility. |
| <a id="contract-actor_evidence-actor-launch"></a>`launch` | [Actor launch context](#contract-actor_evidence-launch); omitted when absent | Host-arranged launch context once this actor process was spawned. |
| <a id="contract-actor_evidence-actor-subprocess"></a>`subprocess` | [Worker subprocess](#contract-lifecycle-worker); omitted when absent | This actor's worker lifecycle and publication account. |
| <a id="contract-actor_evidence-actor-compiled_profile"></a>`compiled_profile` | [Receipt](#contract-profile-receipt); omitted when absent | Receipt from this actor's requested compiled-profile capture, when the host has a capture result. |
| <a id="contract-actor_evidence-actor-visits"></a>`visits` | array of integer; required | In an ordinary semantic reply, the exact ordered list of one-based global phase ordinals declared for this actor, including visits whose activation never occurred. Membership comes from each phase's declared owner. |
| <a id="contract-actor_evidence-actor-equipment"></a>`equipment` | [Actor equipment selection](#contract-equipment-actor); omitted when absent | Requested and resolved worker role, entitlement requirement assessment and live execution observation. |
| <a id="contract-actor_evidence-actor-application"></a>`application` | [Application assessment](#contract-actor_evidence-application); omitted when absent | Host application-boundary assessment with its evidence basis. |
| <a id="contract-actor_evidence-actor-owned_reap"></a>`owned_reap` | [Owned child ending](#contract-lifecycle-owned_reap); omitted when absent | Host-owned waitpid ending retained for this actor and referenced by dependent termination gates. |

<a id="contract-actor_evidence-actor-account"></a>
##### Actor ownership and reporting scope

[Runner host](#contract-identity-definitions-host) reports at actor reply assembly. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Applies when `request.actors` is present. Assemble each actor's row from its declaration, launch/driver output and its own shared publications; phases retain their declared actor and action ownership. Retain the actor-indexed account and separately report schedule observations. In an ordinary executed reply, each declared action has its ordered step or extension-event record even when execution evidence is unresolved. Preparation refusals and retained reporting failures carry the distinct contents stated below.

A preparation refusal retains declarations and preparation observations while
its execution tables remain empty. A retained reporting-failure reply carries
the assembled observations and the reporting conflict, with comparison claims
removed. Its applicable guarantee is the degraded report's form: retained
actor, phase and resource associations remain available for inspection as
assembled. Ordinary consistency assessments apply on the ordinary reply path.

<a id="contract-actor_evidence-actor-reader_scope"></a>
##### Reader applicability

Uses [Check families and applicability](#contract-diagnostics-execution-families), [Publish a report or fallback](#contract-reply-failure-publish).

The host self-check, controller semantic reader and general canonical-JSON
consumer check ordinary actor relationships when `reporting_failure` is
absent. A preparation refusal belongs to the actor execution form and retains
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

**Support: [executed](#contract-support-grades) for [Reader applicability](#contract-actor_evidence-actor-reader_scope).** Constructed typed preparation, declaration and degradation neighbours retain separate host, controller, general-consumer and worker-lifecycle judgments. Context: Whole canonical runner-unit case passed with zero recorded system sleep. Swift judgments over 142 typed frames were retained before encoding; exact-one Rust replay carried 143 frames including the real writer-cap fallback through envelopes, then independent Python readers completed all rows and seven JSON-only controls. Evidence limit: The corpus uses constructed records and independently expected interpretations. Eleven application-positive pairs, degradation admission, the exact contradictory-worker D1 finding and retained actor projections have separate assertions. JSON-only normalization has its own domain. Native occurrence of each constructed context has separate observation owners. Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `actorPreparationRefusal`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`; [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift): `actorExtensionEvidenceProblem`, `validateForReporting`; [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `admission_problem`; [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `preparation_failure_valid`; [consumer.py](../tests/lib/consumer.py): `_validate_reply`; [lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py): `check_actor_records`. Check: [ReaderCorpusTests.swift](../runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift): `runReaderCorpusTests`; [run_flow.rs](../controller/src/run_flow.rs): `reader_definition_corpus_cross_readers`. Run: `20261111T162345Z_3d6c7242`. Source snapshot: `reviewed-inputs sha256:af396aadf41ba79a0d072b62d9c3f4ff1df5b5fa30d6c4ff267c53e8437dd51d (b6ce6d26 dirty; replay identity correction)`. Case: `runner_unit/pwrunner_core_unit_executable`.

<a id="contract-actor_evidence-launch"></a>
#### Actor launch context

Record `ae_launch`: `PWRunnerActorLaunch`.

The host starts each actor as a fresh process with explicit standard streams and descriptor inheritance.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actor_evidence-launch-pid"></a>`pid` | integer; required | PID obtained from this actor's successful spawn. |
| <a id="contract-actor_evidence-launch-parent_pid"></a>`parent_pid` | integer; required | PID of the runner host that spawned the actor. |
| <a id="contract-actor_evidence-launch-environment"></a>`environment` | string; required | empty: the host supplies an empty environment to the actor process. |
| <a id="contract-actor_evidence-launch-standard_streams"></a>`standard_streams` | string; required | stdin_policy_pipe_stdout_stderr_null_device: stdin carries policy bytes, while stdout and stderr are attached to the null device. |
| <a id="contract-actor_evidence-launch-inherited_descriptors"></a>`inherited_descriptors` | array of integer; required | Explicit inherited descriptor numbers: 0 policy input, 3 shared evidence, 4 readiness, and 5 only when an authority region is mapped for the actor. |

<a id="contract-actor_evidence-application"></a>
#### Application assessment

Record `ae_application`: `PWRunnerActorApplication`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actor_evidence-application-state"></a>`state` | string; required | not_requested, not_attempted, observed or unobserved. observed identifies evidence of the apply boundary, including a native apply failure; unobserved retains an unresolved result. Admitted vocabulary: closed; displayed list: exhaustive: `"not_requested"`, `"not_attempted"`, `"observed"`, `"unobserved"`. |
| <a id="contract-actor_evidence-application-basis"></a>`basis` | string; required | The specific declaration, launch state or worker/authority publication supporting state. The eleven permitted state/basis pairs are defined by the application rule below. Admitted vocabulary: closed; displayed list: exhaustive: `"unapplied_declaration"`, `"worker_not_launched"`, `"applied_publication"`, `"terminal_authority_setup_refusal"`, `"apply_failure_publication"`, `"terminal_input_refusal"`, `"terminal_parameter_refusal"`, `"terminal_compile_refusal"`, `"terminal_timing_refusal"`, `"apply_call_boundary_without_result"`, `"no_eligible_apply_publication"`. |

<a id="contract-actor_evidence-application-authority_association"></a>
##### Associated authority rows

[Runner host](#contract-identity-definitions-host) reports at actor reply assembly. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Binding `a`: entry in `reply.actors`. Binding `w`: entry in `reply.authority_setup.workers`. Association restriction for `w`: (`w` = `a` and `reply.authority_setup.workers[w].actor_index` is present and `reply.authority_setup.workers[w].actor_index` = `a` and `reply.authority_setup.workers[w].actor_id` is present and `reply.authority_setup.workers[w].actor_id` = `reply.actors[a].actor_id`). For each `a`. Applies when (`request.actors` is present and `reply.actors` is present and `reply.execution_form` = `"actors"` and `reply.reporting_failure` is absent).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actor_evidence-application-authority_association-entry"></a>One associated entry for each actor | Requires (`reply.authority_setup` is present and count of `reply.authority_setup.workers` = count of `reply.actors` and number of matching entries for `w` = `1`). |

<a id="contract-actor_evidence-application-classify"></a>
##### Application classification

[Runner host](#contract-identity-definitions-host) reports at actor reply assembly. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Binding `a`: entry in `reply.actors`. Binding `t`: entry in `reply.authority_setup.workers`. Association restriction for `t`: (`t` = `a` and `reply.authority_setup.workers[t].publication` is present and `reply.authority_setup.workers[t].publication` = `"observed"` and `reply.authority_setup.workers[t].disposition` is present and `reply.authority_setup.workers[t].disposition` = `"terminal_required_failure"` and `reply.authority_setup.workers[t].integrity_errors` is absent). For each `a`. Select the first matching case in the listed order. Applies when (`request.actors` is present and `reply.actors` is present and `reply.execution_form` = `"actors"` and `reply.reporting_failure` is absent).

Preparation refusals classify their
unlaunched rows through the first two branches. An unavailable native
authority observation is reported as an entry with publication `not_observed`.

These are the host's production assignments. Recipient checks separately
validate the carried associations, permitted state/basis pairs and source
precedence. A reporting-failure reply retains the earlier assessment under
its own reporting scope.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-actor_evidence-application-classify-unapplied"></a>1. Unapplied declaration | `reply.actors[a].mode` = `"unapplied"` | sets `reply.actors[a].application.state` to `"not_requested"`, sets `reply.actors[a].application.basis` to `"unapplied_declaration"`. |
| <a id="contract-actor_evidence-application-classify-unlaunched"></a>2. Worker absent | `reply.actors[a].launch` is absent | sets `reply.actors[a].application.state` to `"not_attempted"`, sets `reply.actors[a].application.basis` to `"worker_not_launched"`. |
| <a id="contract-actor_evidence-application-classify-applied"></a>3. Applied flag | (`reply.actors[a].applied` is present and `reply.actors[a].applied` = `true`) | sets `reply.actors[a].application.state` to `"observed"`, sets `reply.actors[a].application.basis` to `"applied_publication"`. |
| <a id="contract-actor_evidence-application-classify-authority"></a>4. Authority refusal | (`reply.authority_setup` is present and number of matching entries for `t` = `1`) | sets `reply.actors[a].application.state` to `"not_attempted"`, sets `reply.actors[a].application.basis` to `"terminal_authority_setup_refusal"`. |
| <a id="contract-actor_evidence-application-classify-apply_failure"></a>5. Native apply failure | (`reply.actors[a].subprocess` is present and `reply.actors[a].subprocess.worker_evidence` is present and `reply.actors[a].subprocess.worker_evidence.failure_state` = `"published"` and `reply.actors[a].subprocess.worker_evidence.failure` is present and `reply.actors[a].subprocess.worker_evidence.failure.operation` = `8` and `reply.actors[a].subprocess.worker_evidence.failure.code` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_result` is present and `reply.actors[a].subprocess.worker_evidence.failure.native_result` ≠ `0`) | sets `reply.actors[a].application.state` to `"observed"`, sets `reply.actors[a].application.basis` to `"apply_failure_publication"`. |
| <a id="contract-actor_evidence-application-classify-input"></a>6. Input refusal | (`reply.actors[a].subprocess` is present and `reply.actors[a].subprocess.worker_evidence` is present and `reply.actors[a].subprocess.worker_evidence.failure_state` = `"published"` and `reply.actors[a].subprocess.worker_evidence.failure` is present and ((`reply.actors[a].subprocess.worker_evidence.failure.operation` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.code` is one of `4`, `7`, `10`, `12` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `0`) or (`reply.actors[a].subprocess.worker_evidence.failure.operation` = `2` and `reply.actors[a].subprocess.worker_evidence.failure.code` is one of `2`, `3`, `9`, `13`))) | sets `reply.actors[a].application.state` to `"not_attempted"`, sets `reply.actors[a].application.basis` to `"terminal_input_refusal"`. |
| <a id="contract-actor_evidence-application-classify-parameter"></a>7. Parameter refusal | (`reply.actors[a].subprocess` is present and `reply.actors[a].subprocess.worker_evidence` is present and `reply.actors[a].subprocess.worker_evidence.failure_state` = `"published"` and `reply.actors[a].subprocess.worker_evidence.failure` is present and ((`reply.actors[a].subprocess.worker_evidence.failure.operation` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.code` = `5` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `0`) or (`reply.actors[a].subprocess.worker_evidence.failure.operation` = `3` and `reply.actors[a].subprocess.worker_evidence.failure.code` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `2`) or (`reply.actors[a].subprocess.worker_evidence.failure.operation` = `4` and ((`reply.actors[a].subprocess.worker_evidence.failure.code` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `1`) or (`reply.actors[a].subprocess.worker_evidence.failure.code` = `6` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `0`))))) | sets `reply.actors[a].application.state` to `"not_attempted"`, sets `reply.actors[a].application.basis` to `"terminal_parameter_refusal"`. |
| <a id="contract-actor_evidence-application-classify-compile"></a>8. Compile refusal | (`reply.actors[a].subprocess` is present and `reply.actors[a].subprocess.worker_evidence` is present and `reply.actors[a].subprocess.worker_evidence.failure_state` = `"published"` and `reply.actors[a].subprocess.worker_evidence.failure` is present and `reply.actors[a].subprocess.worker_evidence.failure.operation` = `5` and `reply.actors[a].subprocess.worker_evidence.failure.code` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `2`) | sets `reply.actors[a].application.state` to `"not_attempted"`, sets `reply.actors[a].application.basis` to `"terminal_compile_refusal"`. |
| <a id="contract-actor_evidence-application-classify-timing"></a>9. Timing refusal | (`reply.actors[a].subprocess` is present and `reply.actors[a].subprocess.worker_evidence` is present and `reply.actors[a].subprocess.worker_evidence.failure_state` = `"published"` and `reply.actors[a].subprocess.worker_evidence.failure` is present and `reply.actors[a].subprocess.worker_evidence.failure.operation` = `12` and ((`reply.actors[a].subprocess.worker_evidence.failure.code` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `1`) or (`reply.actors[a].subprocess.worker_evidence.failure.code` = `14` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `0`) or (`reply.actors[a].subprocess.worker_evidence.failure.code` = `15` and `reply.actors[a].subprocess.worker_evidence.failure.detail` = `1` and `reply.actors[a].subprocess.worker_evidence.failure.native_kind` = `0`))) | sets `reply.actors[a].application.state` to `"not_attempted"`, sets `reply.actors[a].application.basis` to `"terminal_timing_refusal"`. |
| <a id="contract-actor_evidence-application-classify-boundary"></a>10. Apply boundary without result | (`reply.actors[a].subprocess` is present and `reply.actors[a].subprocess.worker_evidence` is present and `reply.actors[a].subprocess.worker_evidence.progress` is present and `reply.actors[a].subprocess.worker_evidence.progress.operation` = `8` and `reply.actors[a].subprocess.worker_evidence.progress.stage` is one of `1`, `2`) | sets `reply.actors[a].application.state` to `"unobserved"`, sets `reply.actors[a].application.basis` to `"apply_call_boundary_without_result"`. |
| <a id="contract-actor_evidence-application-classify-remaining"></a>11. Remaining evidence | `true` | sets `reply.actors[a].application.state` to `"unobserved"`, sets `reply.actors[a].application.basis` to `"no_eligible_apply_publication"`. |

<a id="contract-actor_evidence-application-late_application"></a>
##### Setup deadline and later application

Final collection preserves a later applied publication and derives application_count from it after setup eligibility has ended. A setup_timeout can therefore coexist with applied true, count 1 and application state observed with basis applied_publication. The affected actor remains ineligible for phase activation and query collection.

**Support: [check read](#contract-support-grades) for [Setup deadline and later application](#contract-actor_evidence-application-late_application).** Final collection retains application independently of earlier setup eligibility. Context: Static review of the cited producer and assertion branches. Evidence limit: The read controls use 40 ms setup, 150 ms pre-ready delay and 1000 ms grace, then retain the production reply. Their timing observation is bounded to that schedule. Source: [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `ActorScheduler`. Check: [ActorSchedulerTests.swift](../runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift): `runActorSchedulerTests`; [ActorReplyTests.swift](../runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift): `runActorReplyTests`.

<a id="contract-actor_evidence-phase"></a>
#### Phase collection and execution

Record `ae_phase`: `PWRunnerPhaseResult`.

The host reports phases in declared schedule order. Observation fields record activation's consequences separately from the declared phase and action identities.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actor_evidence-phase-phase_id"></a>`phase_id` | string; required | Submitted phase identifier used by its action records and validator collection. Ordinary semantic replies require a nonempty, NUL-free identifier within its admitted UTF-8 capacity. The declared phase order determines its ordinal. |
| <a id="contract-actor_evidence-phase-ordinal"></a>`ordinal` | integer; required | One-based position in the global phase schedule. |
| <a id="contract-actor_evidence-phase-action_ids"></a>`action_ids` | array of string; required | Declared action identifiers in phase order, retained even when actions produce no execution observations. |
| <a id="contract-actor_evidence-phase-arrival_observed"></a>`arrival_observed` | boolean; required | Whether the host acquired the active worker's arrival publication for this visit. |
| <a id="contract-actor_evidence-phase-completion_observed"></a>`completion_observed` | boolean; required | Whether the host acquired completion for this visit. |
| <a id="contract-actor_evidence-phase-collection_status"></a>`collection_status` | string; required | collected, not_needed, budget_exhausted, clock_unavailable or not_reached. collected identifies an invoked collection even when validator I/O or decoding later fails. Admitted vocabulary: closed; displayed list: exhaustive: `"collected"`, `"not_needed"`, `"budget_exhausted"`, `"clock_unavailable"`, `"not_reached"`. |
| <a id="contract-actor_evidence-phase-ordering"></a>`ordering` | [Collection and release observations](#contract-steps-ordering); omitted when absent | Collection/release order observations for this phase, including host proceed store and worker acknowledgement. |
| <a id="contract-actor_evidence-phase-validator_subprocess"></a>`validator_subprocess` | [Validator subprocess](#contract-lifecycle-validator); omitted when absent | Child-process and accepted-verdict account for this phase's validator collection. |
| <a id="contract-actor_evidence-phase-validator_spawn_failure"></a>`validator_spawn_failure` | [Native spawn failure](#contract-lifecycle-spawn_failure); omitted when absent | Native validator spawn failure before a validator child existed. |
| <a id="contract-actor_evidence-phase-actor_id"></a>`actor_id` | string; omitted when absent | Actor owning this phase in actor form; absent for the single-worker form. |
| <a id="contract-actor_evidence-phase-actor_visit"></a>`actor_visit` | integer; omitted when absent | One-based visit number within this actor's declared visits, distinct from global ordinal. |
| <a id="contract-actor_evidence-phase-visit_timing"></a>`visit_timing` | [Visit intervals](#contract-actor_evidence-timing); omitted when absent | Host-measured intervals for reached visit boundaries; missing intervals retain unavailable clock/boundary observations. |
| <a id="contract-actor_evidence-phase-termination_gate"></a>`termination_gate` | [Termination dependency](#contract-actor_evidence-gate); omitted when absent | Dependency observation for a phase declaring after_termination, including gates left not_reached. |
| <a id="contract-actor_evidence-phase-activation_observation"></a>`activation_observation` | [Host activation observation](#contract-actor_evidence-activation); omitted when absent | Host release-store observation which activates this phase, with its actor-local capture ordinal and optional time. |

<a id="contract-actor_evidence-activation"></a>
#### Host activation observation

Record `ae_activation`: `PWRunnerActorActivation`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actor_evidence-activation-capture_ordinal"></a>`capture_ordinal` | integer; required | Positive sequence position of this host activation store among observations of the same child. |
| <a id="contract-actor_evidence-activation-observed_ns"></a>`observed_ns` | integer; omitted when absent | Host monotonic time in nanoseconds after the store, when the clock supplied it. |

<a id="contract-actor_evidence-timing"></a>
#### Visit intervals

Record `ae_timing`: `PWRunnerVisitTiming`.

Each interval measures two host observations in milliseconds; an unavailable or backward clock leaves that interval absent.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actor_evidence-timing-activation_to_arrival_ms"></a>`activation_to_arrival_ms` | integer; omitted when absent | Time between the host activation store and acquired worker arrival. |
| <a id="contract-actor_evidence-timing-collection_ms"></a>`collection_ms` | integer; omitted when absent | Time spent in the phase's synchronous query-collection hook. |
| <a id="contract-actor_evidence-timing-arrival_to_release_ms"></a>`arrival_to_release_ms` | integer; omitted when absent | Time from observed arrival to the host proceed release store. |
| <a id="contract-actor_evidence-timing-release_to_completion_ms"></a>`release_to_completion_ms` | integer; omitted when absent | Time from the release store to acquired worker completion. |

<a id="contract-actor_evidence-schedule"></a>
#### Schedule account

Record `ae_schedule`: `PWRunnerScheduleRecord`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actor_evidence-schedule-setup_wait"></a>`setup_wait` | [Measured host wait](#contract-lifecycle-host_wait); omitted when absent | Measured shared setup wait for the actor set. |
| <a id="contract-actor_evidence-schedule-execution_wait"></a>`execution_wait` | [Measured host wait](#contract-lifecycle-host_wait); omitted when absent | Measured schedule traversal wait, with collection excluded when separately budgeted. |
| <a id="contract-actor_evidence-schedule-lifetime_budget_ms"></a>`lifetime_budget_ms` | integer; required | Overall actor-run lifetime allowance, <!-- span limits.actor_lifetime_cutoff.value_unit -->180,000 milliseconds<!-- /span --> in the production plan. |
| <a id="contract-actor_evidence-schedule-collection_budget_ms"></a>`collection_budget_ms` | integer; required | Recorded production maximum for aggregate query collection across actor phases: <!-- span limits.actor_collection_allowance.value_unit -->30,000 milliseconds<!-- /span -->. The host reports this maximum even when `_test_overrides.validator_total_timeout_ms` reduces the allowance used for collection. |
| <a id="contract-actor_evidence-schedule-cancelled"></a>`cancelled` | string; omitted when absent | Recorded schedule cancellation reason, such as preparation_refused, execution_allowance_exhausted, an equipment failure or termination_dependency followed by its outcome; absent when no cancellation was recorded. |

<a id="contract-actor_evidence-gate"></a>
#### Termination dependency

Record `ae_gate`: `PWRunnerTerminationGate`.

The gate belongs to the dependent phase and observes the named source actor after that source’s final scheduled visit was activated.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-actor_evidence-gate-source_actor_id"></a>`source_actor_id` | string; required | Different actor named by the dependent phase's after_termination declaration. |
| <a id="contract-actor_evidence-gate-source_final_phase_id"></a>`source_final_phase_id` | string; required | Source actor's last declared phase, which must precede the dependent phase in the global schedule. |
| <a id="contract-actor_evidence-gate-condition"></a>`condition` | string; required | terminated, the supported dependency condition. Admitted vocabulary: closed; displayed list: exhaustive: `"terminated"`. |
| <a id="contract-actor_evidence-gate-outcome"></a>`outcome` | string; required | not_reached, satisfied, timed_out, ownership_lost, clock_unavailable, source_unavailable, source_departure_requested or execution_allowance_exhausted; each is defined by the gate rule below. Admitted vocabulary: closed; displayed list: exhaustive: `"not_reached"`, `"satisfied"`, `"timed_out"`, `"ownership_lost"`, `"clock_unavailable"`, `"source_unavailable"`, `"source_departure_requested"`, `"execution_allowance_exhausted"`. |
| <a id="contract-actor_evidence-gate-wait"></a>`wait` | [Measured host wait](#contract-lifecycle-host_wait); omitted when absent | Host dependency wait, with budget capped at <!-- span limits.actor_termination_wait.value_unit -->5,000 milliseconds<!-- /span --> and charged to remaining execution allowance. Absent for not_reached. |
| <a id="contract-actor_evidence-gate-observation"></a>`observation` | [Owned-ending reference](#contract-lifecycle-reap_reference); omitted when absent | Reference to the source actor's owned ending captured by the evaluated gate, when available; a late ending can remain beside a failed gate. |
| <a id="contract-actor_evidence-gate-activation_eligible"></a>`activation_eligible` | boolean; required | True exactly for a satisfied gate, allowing this dependent phase to proceed to activation. |
| <a id="contract-actor_evidence-gate-capture_ordinal"></a>`capture_ordinal` | integer; omitted when absent | Capture of the gate result in the source child's host-observation sequence; absent for not_reached and when no source session supplies a sequence. |

<a id="contract-actor_evidence-gate-prepared_association"></a>
##### Prepared actor phase and gate records

[Runner host](#contract-identity-definitions-host) reports at prepared actor reply assembly. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Binding `q`: entry in `request.phases`. Binding `p`: entry in `reply.phases`. Association restriction for `p`: `p` = `q`. Applies when (`request.actors` is present and `reply.execution_form` = `"actors"` and `reply.preparation_failure` is absent and `reply.reporting_failure` is absent).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actor_evidence-gate-prepared_association-cardinality"></a>Phase cardinality | Requires (`request.phases` is present and count of `reply.phases` = count of `request.phases`). |
| <a id="contract-actor_evidence-gate-prepared_association-rows"></a>Each phase and declared gate | For each `q`, `p`. Requires (`reply.phases[p].phase_id` = `request.phases[q].phase_id` and `reply.phases[p].ordinal` = (`q` + `1`) and `reply.phases[p].actor_id` = `request.phases[q].actor_id` and (if `request.phases[q].after_termination` is present, then (`reply.phases[p].termination_gate` is present and `reply.phases[p].termination_gate.source_actor_id` = `request.phases[q].after_termination.actor_id`)) and (if `request.phases[q].after_termination` is absent, then `reply.phases[p].termination_gate` is absent)). The scheduler installs every declared gate before cancellation, allowance and dependent availability checks, then assembly copies that gate into the phase row. Its source final phase comes from the source actor's last preceding phase in the normalized plan. Preparation refusals carry their separate before-launch phase account. |

<a id="contract-actor_evidence-gate-evaluate"></a>
##### Evaluating and applying the dependency

[Runner host](#contract-identity-definitions-host) acts at serial actor schedule before dependent activation. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Binding `q`: entry in `request.phases`. Binding `p`: entry in `reply.phases`. Association restriction for `p`: `p` = `q`. For each `q`, `p`. Applies when (`request.actors` is present and `request.phases` is present and `request.phases[q].after_termination` is present and `reply.execution_form` = `"actors"` and `reply.preparation_failure` is absent and `reply.reporting_failure` is absent). Requires [Phase cardinality](#contract-actor_evidence-gate-prepared_association-cardinality), [Each phase and declared gate](#contract-actor_evidence-gate-prepared_association-rows). Evaluate only after the schedule remains uncancelled, its allowance is positive, and the dependent actor session, usable setup, unstopped state and visit are available. Evaluation first checks the source session and final declared phase activation; unavailable source evidence gives source_unavailable. A failed evaluated gate prevents dependent activation, collection and release, and cancels every later scheduled phase regardless of its actor. Cleanup and final collection continue for launched actors.

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
| <a id="contract-actor_evidence-gate-evaluate-eligibility_assignment"></a>Eligibility assigned by evaluation | sets `reply.phases[p].termination_gate.activation_eligible` to `reply.phases[p].termination_gate.outcome` = `"satisfied"`. |
| <a id="contract-actor_evidence-gate-evaluate-satisfied"></a>Satisfied | Value: `"satisfied"`. The source final activation precedes a natural owned reap in its child sequence; both timestamps exist and activation time is at most reap time. Ownership is unbroken, departure_requested is false, budget is positive, deadline samples permit the reap, and final wait has a valid elapsed interval at most budget. The gate closes after the source's owned ending. A normal exit or signaled ending can qualify; natural means the host had not requested departure. Source final-phase completion is a separate observation from activation and owned termination. |
| <a id="contract-actor_evidence-gate-evaluate-not_reached"></a>Unreached | Value: `"not_reached"`. Cancellation, exhausted schedule allowance or an unavailable dependent actor or visit stopped traversal before this gate was evaluated. Its wait, observation and capture ordinal are absent and eligibility is false. An unavailable dependent actor can leave this gate unreached while later otherwise eligible phases remain schedulable. |
| <a id="contract-actor_evidence-gate-evaluate-source_unavailable"></a>Source unavailable | Value: `"source_unavailable"`. The source session, final activation, or required activation-before-ending order was unavailable. |
| <a id="contract-actor_evidence-gate-evaluate-execution_allowance_exhausted"></a>No remaining gate allowance | Value: `"execution_allowance_exhausted"`. Evaluation began with no positive whole-millisecond gate budget. |
| <a id="contract-actor_evidence-gate-evaluate-clock_unavailable"></a>Timing unavailable | Value: `"clock_unavailable"`. A deadline sample, required activation/reap time or final elapsed accounting was unavailable or moved backward. Retained fields provide the available context for this timing failure. |
| <a id="contract-actor_evidence-gate-evaluate-timed_out"></a>Gate timeout | Value: `"timed_out"`. The deadline or wait expired, including after a reap, or final elapsed time exceeded budget. A retained reap reference establishes that capture while this outcome records failure to establish timely satisfaction. |
| <a id="contract-actor_evidence-gate-evaluate-ownership_lost"></a>Ownership lost | Value: `"ownership_lost"`. The host's uninterrupted source ownership was lost or its source wait failed. |
| <a id="contract-actor_evidence-gate-evaluate-source_departure_requested"></a>Departure requested | Value: `"source_departure_requested"`. The host had requested the source's departure before the eligible ending. |

<a id="contract-actor_evidence-gate-check"></a>
##### Checking a carried gate

[Controller](#contract-identity-definitions-controller) checks at semantic assessment after reply admission. Entry: cli run. Recipient: cli caller. Reports: runner reply. Binding `p`: entry in `reply.phases`. Binding `s`: entry in `reply.actors`. Binding `f`: entry in `reply.phases`. Association restriction for `s`: `reply.actors[s].actor_id` = `reply.phases[p].termination_gate.source_actor_id`. Association restriction for `f`: `reply.phases[f].phase_id` = `reply.phases[p].termination_gate.source_final_phase_id`. Applies when (`reply.reporting_failure` is absent and `reply.execution_form` = `"actors"` and `reply.phases[p].termination_gate` is present). The check retains each failed condition it finds. Resolve source and final-phase joins before using s or f; missing, nonfinal, same-actor or nonpreceding associations are findings. Check owned PID/native-status agreement, all conditional gate captures, independent actor setup/equipment eligibility and activation timing.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-actor_evidence-gate-check-failed"></a>Failed carried-gate requirement | On failure, sets `envelope.data.runner_sandbox_diagnostics.disposition_integrity` to `"invalid"`, sets `envelope.data.runner_sandbox_diagnostics.process_disposition` to `"withheld"`, sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"unknown"`, retains the records `reply`, keeps the assessment `envelope.data.runner_sandbox_diagnostics.actors`. Uses [Select the public result](#contract-envelope-data-select). Append the actor_evidence finding for the failed requirement, with subject_path naming this phase's inspected termination_gate. Run result and exit status continue to follow their result-selection rule. |
| <a id="contract-actor_evidence-gate-check-unreached"></a>Unreached shape | Requires (if `reply.phases[p].termination_gate.outcome` = `"not_reached"`, then (`reply.phases[p].termination_gate.wait` is absent and `reply.phases[p].termination_gate.observation` is absent and `reply.phases[p].termination_gate.capture_ordinal` is absent)). |
| <a id="contract-actor_evidence-gate-check-timely"></a>Timely satisfied wait | Requires (if `reply.phases[p].termination_gate.outcome` = `"satisfied"`, then (`reply.phases[p].termination_gate.wait` is present and `reply.phases[p].termination_gate.wait.budget_ms` > `0` and `reply.phases[p].termination_gate.wait.budget_ms` ≤ `5000` and `reply.phases[p].termination_gate.wait.elapsed_ms` is present and `reply.phases[p].termination_gate.wait.elapsed_ms` ≤ `reply.phases[p].termination_gate.wait.budget_ms` and `reply.phases[p].termination_gate.wait.clock_fault` = `false` and `reply.phases[p].termination_gate.wait.native_errno` is absent)). Every present gate wait has budget 0–5000 and absent excluded time. An evaluated gate has a wait whose stop matches its outcome. |
| <a id="contract-actor_evidence-gate-check-sequence"></a>Source sequence | Requires (if `reply.phases[p].termination_gate.outcome` = `"satisfied"`, then (`reply.phases[f].activation_observation` is present and `reply.actors[s].owned_reap` is present and `reply.phases[f].activation_observation.capture_ordinal` < `reply.actors[s].owned_reap.capture_ordinal` and `reply.actors[s].owned_reap.capture_ordinal` < `reply.phases[p].termination_gate.capture_ordinal` and `reply.actors[s].owned_reap.ownership_unbroken` = `true` and `reply.actors[s].owned_reap.departure_requested` = `false`)). The referenced ending matches the source actor's valid PID/native wait status, has stage `schedule` or `termination_gate`, and has the reference's positive ordinal. Final activation and reap timestamps must exist in nondecreasing order; a timestamped dependent activation is at or after the reap. |
| <a id="contract-actor_evidence-gate-check-eligibility"></a>Eligibility consequence | Binding `d`: entry in `reply.actors`. Association restriction for `d`: (`reply.phases[p].actor_id` is present and `reply.actors[d].actor_id` = `reply.phases[p].actor_id` and `reply.actors[d].setup_status` is one of `"applied"`, `"unapplied_declared"` and `reply.actors[d].equipment` is present and `reply.actors[d].equipment.execution.eligible` = `true`). For each `p`. Requires ((if `reply.phases[p].termination_gate.activation_eligible` = `true`, then (`reply.phases[p].termination_gate.outcome` = `"satisfied"` and `reply.actors` is present and number of matching entries for `d` > `0`)) and (if `reply.phases[p].termination_gate.activation_eligible` = `false`, then (`reply.phases[p].activation_observation` is absent and `reply.phases[p].visit_timing` is absent and `reply.phases[p].arrival_observed` = `false` and `reply.phases[p].collection_status` = `"not_reached"` and (`reply.phases[p].ordering` is absent or (`reply.phases[p].ordering.proceed_set` = `false` and `reply.phases[p].ordering.proceed_observed` = `false`))))). |

<a id="contract-actor_evidence-gate-timeout_example"></a>
##### A timeout followed by cleanup

The source completes its final phase but remains alive when the dependency
times out. The dependent phase receives no activation, collection or release.
Cleanup later reaps the source; the gate remains `timed_out`.

**Support: [check read](#contract-support-grades) for [A timeout followed by cleanup](#contract-actor_evidence-gate-timeout_example) and its descendants.** Source phase completion, timeout, withheld dependent activation/collection/release, later source reap and unchanged timeout. Context: Real fixture child with post-apply hang and 50 ms execution allowance; test source inspected. Evidence limit: No execution credit; this assertion covers scheduler observations with shortened allowance, not public JSON or an additional later actor. Source: [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `observeTermination`. Check: [ActorSchedulerTests.swift](../runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift): `runActorSchedulerTests`.

<a id="contract-actor_evidence-gate-cancellation_evidence"></a>
##### Known gap: Termination cancellation reach

A failed evaluated termination dependency cancels every remaining scheduled phase, including later work owned by another actor. A dependent actor that is ineligible before gate evaluation has a not_reached gate and does not create that dependency failure. Whether cancellation should have narrower reach remains a maintainer decision.

**Support: [check read](#contract-support-grades) for [Termination cancellation reach](#contract-actor_evidence-gate-cancellation_evidence).** An evaluated failed gate sets global schedule cancellation; an unreached gate has a different path. Context: Static review of the cited producer and assertion branches. Evidence limit: The control distinguishes a three-worker evaluated timeout from an ineligible-dependent neighbour and retains final collection. Source: [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `ActorScheduler`. Check: [check_actor_compositions.py](../tests/suites/witness_contract/check_actor_compositions.py): `assert_gate_schedule`.

<a id="contract-actor_evidence-owned_endings"></a>
#### Observation sequences

<a id="contract-actor_evidence-owned_endings-sequence"></a>
##### Actor-local sequence

The host maintains one observation counter for each owned child. Each activation
of that actor, its owned reap and each evaluated gate waiting for it consumes
the next ordinal. Source final activation, source reap and gate closure are
comparable within that source sequence. The dependent actor's activation has
its own sequence; its timestamp supplies the cross-process temporal comparison.
A `not_reached` gate consumes no gate-capture ordinal.

**Support: [source read](#contract-support-grades) for [Actor and phase evidence](#contract-actor_evidence) and its descendants.** Imported public field definitions joined to producer/decoder/assessment meanings; explicit rule and evidence gaps preserve scope. Evidence limit: No execution credit is claimed by this owner. Source: [PWRunnerActors.swift](../runner/Sources/PWRunnerCore/PWRunnerActors.swift): `PWRunnerActorResult`; [PWRunnerAuthoritySetup.swift](../runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift): `actorApplicationAssessment`; [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `ActorScheduler`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`; [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift): `actorExtensionEvidenceProblem`; [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `gates`; [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `execution_diagnostics`; [actor_evidence.py](../tests/lib/actor_evidence.py): `validate_actor_evidence`; [lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py): `check_actor_records`; [consumer.py](../tests/lib/consumer.py): `_validate_actors`.

<a id="contract-equipment"></a>
### Equipment and authority setup

<a id="contract-equipment-inventory"></a>
#### Observed service inventory

Record `eq_inventory`: `PWRunnerEquipmentInventory`.

The host inspects the selected service seal and reads its bounded worker-equipment.json before launching any actor.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-inventory-path"></a>`path` | string; required | Absolute path of the service-local worker-equipment.json selected for inspection. |
| <a id="contract-equipment-inventory-status"></a>`status` | string; required | verified after seal, inventory decoding and expected-identity checks; refused after a retained failure; unobserved before inspection. Admitted vocabulary: closed; displayed list: exhaustive: `"verified"`, `"refused"`, `"unobserved"`. |
| <a id="contract-equipment-inventory-sha256"></a>`sha256` | string (hex); omitted when absent | SHA-256 of inventory bytes actually read, when available. Uses [SHA-256 hexadecimal width](#contract-identity-other-sha256_hex). |
| <a id="contract-equipment-inventory-schema_version"></a>`schema_version` | integer; omitted when absent | Decoded inventory schema; verified inventory has version 1. |
| <a id="contract-equipment-inventory-worker_identity"></a>`worker_identity` | string (hex); omitted when absent | Decoded worker protocol identity, required to equal the host's selected worker identity for verification. Uses [SHA-256 hexadecimal width](#contract-identity-other-sha256_hex). |
| <a id="contract-equipment-inventory-unsigned_worker_sha256"></a>`unsigned_worker_sha256` | string (hex); omitted when absent | Decoded digest identifying the shared unsigned worker input named by the inventory. Uses [SHA-256 hexadecimal width](#contract-identity-other-sha256_hex). |
| <a id="contract-equipment-inventory-seal_osstatus"></a>`seal_osstatus` | integer; omitted when absent | Native service-signature validity result, when supplied by static inspection; verified inventory requires zero. |
| <a id="contract-equipment-inventory-reason"></a>`reason` | string; omitted when absent | Refusal classification describing the failed inventory/seal boundary; absent for verified inventory. |
| <a id="contract-equipment-inventory-error"></a>`error` | [Equipment diagnostic](#contract-equipment-error); omitted when absent | Structured native or decoding diagnostic retained at the failed boundary. |

<a id="contract-equipment-manifest"></a>
#### Sealed equipment inventory file

Record `eq_manifest`: `ActorEquipmentManifest`.

The package places this JSON inventory inside each service seal after signing both worker roles. Its hashes use lowercase hexadecimal text.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-manifest-schema_version"></a>`schema_version` | integer; as defined below | Inventory format version; the host accepts 1. |
| <a id="contract-equipment-manifest-contract"></a>`contract` | string; as defined below | Exact public build identity which must match the host's expected contract. |
| <a id="contract-equipment-manifest-worker_identity"></a>`worker_identity` | string; as defined below | Lowercase hexadecimal worker protocol identity expected by the host. Uses [SHA-256 hexadecimal width](#contract-identity-other-sha256_hex). |
| <a id="contract-equipment-manifest-unsigned_worker_sha256"></a>`unsigned_worker_sha256` | string; as defined below | Lowercase hexadecimal common unsigned worker input digest. Uses [SHA-256 hexadecimal width](#contract-identity-other-sha256_hex). |
| <a id="contract-equipment-manifest-workers"></a>`workers` | array of [Inventory worker row](#contract-equipment-manifest_worker); as defined below | Exactly two distinct role rows, selected and unentitled, providing expected signed file and entitlement identities. |

<a id="contract-equipment-manifest_worker"></a>
#### Inventory worker row

Record `eq_manifest_worker`: `ActorEquipmentManifest.Worker`.

Each row states the signed identity expected at a fixed service-relative worker path.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-manifest_worker-role"></a>`role` | string; as defined below | selected or unentitled, identifying the worker role. Admitted vocabulary: closed; displayed list: exhaustive: `"selected"`, `"unentitled"`. |
| <a id="contract-equipment-manifest_worker-relative_path"></a>`relative_path` | string; as defined below | Contents/MacOS/pw-probe-runner for selected; Contents/MacOS/pw-probe-runner-unentitled for unentitled. |
| <a id="contract-equipment-manifest_worker-sha256"></a>`sha256` | string; as defined below | Lowercase hexadecimal SHA-256 of the signed worker file. Uses [SHA-256 hexadecimal width](#contract-identity-other-sha256_hex). |
| <a id="contract-equipment-manifest_worker-cdhash"></a>`cdhash` | string; as defined below | Lowercase hexadecimal worker CodeDirectory hash. Uses [CodeDirectory hexadecimal width](#contract-identity-other-cdhash_hex). |
| <a id="contract-equipment-manifest_worker-identifier"></a>`identifier` | string; as defined below | Nonempty signing identifier expected from static code inspection, bounded to <!-- span limits.equipment_signing_text.value_unit -->255 UTF-8 bytes<!-- /span -->. |
| <a id="contract-equipment-manifest_worker-team_id"></a>`team_id` | string; required; may be null | Required key whose value is the expected signing team or null; a string is nonempty and at most <!-- span limits.equipment_signing_text.value_unit -->255 UTF-8 bytes<!-- /span -->. |
| <a id="contract-equipment-manifest_worker-entitlements_xml"></a>`entitlements_xml` | string; as defined below | Entitlement dictionary serialized as an XML property list, at most <!-- span limits.equipment_entitlement_bytes.value_unit -->65,536 UTF-8 bytes<!-- /span -->; unentitled has an empty dictionary. |

<a id="contract-equipment-binding"></a>
#### Static worker binding

Record `eq_binding`: `PWRunnerEquipmentBinding`.

The host emits one row per inspected role and source. Binding establishes the chosen file’s observed identity and entitlement read-back; actors select rows by zero-based index.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-binding-role"></a>`role` | string; required | selected or unentitled, the equipment role inspected. Admitted vocabulary: closed; displayed list: exhaustive: `"selected"`, `"unentitled"`. |
| <a id="contract-equipment-binding-source"></a>`source` | string; required | packaged for service inventory equipment; test_override for an explicitly selected fixture path. Admitted vocabulary: closed; displayed list: exhaustive: `"packaged"`, `"test_override"`. |
| <a id="contract-equipment-binding-implementation_identity"></a>`implementation_identity` | string; required | inventory_verified for packaged rows or unverified_fixture for test overrides, identifying the source of expected implementation identity. Admitted vocabulary: closed; displayed list: exhaustive: `"inventory_verified"`, `"unverified_fixture"`. |
| <a id="contract-equipment-binding-relative_path"></a>`relative_path` | string; omitted when absent | Fixed service-relative path for packaged equipment; absent for an override path. |
| <a id="contract-equipment-binding-path"></a>`path` | string; required | Absolute resolved worker path inspected for launch, bounded to <!-- span limits.equipment_path.value_unit -->1,023 UTF-8 bytes<!-- /span -->. |
| <a id="contract-equipment-binding-status"></a>`status` | string; required | bound when path, executable, hash/signature and applicable expected-identity checks pass; refused when a boundary fails. Admitted vocabulary: closed; displayed list: exhaustive: `"bound"`, `"refused"`. |
| <a id="contract-equipment-binding-reason"></a>`reason` | string; omitted when absent | Refusal reason: missing, not_regular, not_executable, outside_bundle, signature_invalid, signature_unreadable, entitlements_unreadable, worker_identity_mismatch or inspection_failed. Admitted vocabulary: closed; displayed list: exhaustive: `"missing"`, `"not_regular"`, `"not_executable"`, `"outside_bundle"`, `"signature_invalid"`, `"signature_unreadable"`, `"entitlements_unreadable"`, `"worker_identity_mismatch"`, `"inspection_failed"`. |
| <a id="contract-equipment-binding-expected_sha256"></a>`expected_sha256` | string (hex); omitted when absent | Signed-file SHA-256 digest from the packaged inventory; absent for test overrides. Uses [SHA-256 hexadecimal width](#contract-identity-other-sha256_hex). |
| <a id="contract-equipment-binding-expected_cdhash"></a>`expected_cdhash` | string (hex); omitted when absent | CodeDirectory hash from the packaged inventory; absent for test overrides. Uses [CodeDirectory hexadecimal width](#contract-identity-other-cdhash_hex). |
| <a id="contract-equipment-binding-sha256"></a>`sha256` | string (hex); omitted when absent | SHA-256 of the inspected file's actual bytes, when hashing completed. Uses [SHA-256 hexadecimal width](#contract-identity-other-sha256_hex). |
| <a id="contract-equipment-binding-cdhash"></a>`cdhash` | string (hex); omitted when absent | CodeDirectory hash read from the inspected static signature, when available. Uses [CodeDirectory hexadecimal width](#contract-identity-other-cdhash_hex). |
| <a id="contract-equipment-binding-identifier"></a>`identifier` | string; omitted when absent | Signing identifier read from static inspection, when available. |
| <a id="contract-equipment-binding-team_id"></a>`team_id` | string; present when identifier has a value; may be null | Signing team read from static inspection, or null when the signature has none or read-back is unavailable. |
| <a id="contract-equipment-binding-entitlements_ref"></a>`entitlements_ref` | integer; omitted when absent | Zero-based index of this binding's observed or failed entitlement read-back in equipment_entitlements. |
| <a id="contract-equipment-binding-signature_osstatus"></a>`signature_osstatus` | integer; omitted when absent | Native static-signature validity result; a bound row requires zero. |
| <a id="contract-equipment-binding-entitlements_match"></a>`entitlements_match` | boolean; omitted when absent | Whether packaged inventory entitlements equal the observed dictionary; absent for an override or when that comparison was unavailable. |
| <a id="contract-equipment-binding-error"></a>`error` | [Equipment diagnostic](#contract-equipment-error); omitted when absent | Structured native or decoding error at the failed inspection boundary, when available. |

<a id="contract-equipment-binding-bind"></a>
##### Binding before launch

[Runner host](#contract-identity-definitions-host) acts at actor preparation before spawn. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Applies when `request.actors` is present. Inspect the service seal, bounded inventory and both packaged worker roles; compare signed hashes, signing identity/team and entitlement dictionaries with the inventory. Resolve every actor's role and Boolean-true entitlement requirements. A preparation failure withholds every actor launch and records equipment_binding_refused with retained inspection evidence. Successful preparation selects the requested role/source path for each actor.

Both packaged roles are checked even if the specimen uses only one. Explicit
fixture overrides are inspected as additional `test_override` rows; their
`unverified_fixture` identity states their provenance. A bound override can
be selected, live-matched and executed. Failed packaged observations remain
preparation failures. A failed role never selects another role automatically.

**Support: [check read](#contract-support-grades) for [Static worker binding](#contract-equipment-binding) and its descendants.** Missing unused packaged role withholds executable paths; Boolean true alone satisfies a key; live mismatch is ineligible; per-row retained observations survive failure. Context: Temporary equipment fixture with constructed inspection calls; source and assertions read. Evidence limit: Execution credit is absent; fixture inspection results support branch/retention behavior. Source: [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `ActorEquipmentPreparation`. Check: [ActorEquipmentTests.swift](../runner/Tests/PWRunnerCoreTests/ActorEquipmentTests.swift): `runActorEquipmentTests`.

<a id="contract-equipment-binding-bound_values"></a>
##### Packaged bound-row equalities

[Runner host](#contract-identity-definitions-host) reports at successful packaged static binding projection. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Applies when (`eq_binding.source` = `"packaged"` and `eq_binding.status` = `"bound"`).

Packaged binding includes the retained digest and entitlement equalities. Test-override bindings have no packaged baseline requirement.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-equipment-binding-bound_values-fields"></a>Produced field relationships | Requires (`eq_binding.sha256` is present and `eq_binding.expected_sha256` is present and `eq_binding.sha256` = `eq_binding.expected_sha256` and `eq_binding.cdhash` is present and `eq_binding.expected_cdhash` is present and `eq_binding.cdhash` = `eq_binding.expected_cdhash` and `eq_binding.entitlements_match` = `true`). |

**Support: [source read](#contract-support-grades) for [Packaged bound-row equalities](#contract-equipment-binding-bound_values) and its descendants.** Packaged binding compares retained expected and observed digests and decoded entitlement equality before marking a row bound. Source: [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `bindOne`.

<a id="contract-equipment-entitlements"></a>
#### Entitlement read-back

Record `eq_entitlements`: `PWRunnerEquipmentEntitlements`.

Each table row belongs either to one static binding or to one running actor inspected against that binding.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-entitlements-source"></a>`source` | string; required | binding for static signed-file read-back; execution for live actor read-back. Admitted vocabulary: closed; displayed list: exhaustive: `"binding"`, `"execution"`. |
| <a id="contract-equipment-entitlements-binding_ref"></a>`binding_ref` | integer; required | Zero-based index of the equipment binding this read-back describes. |
| <a id="contract-equipment-entitlements-actor_id"></a>`actor_id` | string; omitted when absent | Actor identifier for execution read-back; absent for binding read-back. |
| <a id="contract-equipment-entitlements-status"></a>`status` | string; required | observed when raw_plist contains a valid bounded dictionary; failed when an error record describes unavailable read-back. Admitted vocabulary: closed; displayed list: exhaustive: `"observed"`, `"failed"`. |
| <a id="contract-equipment-entitlements-raw_plist"></a>`raw_plist` | string; omitted when absent | Actual entitlement dictionary serialized as an XML property list, at most <!-- span limits.equipment_entitlement_bytes.value_unit -->65,536 UTF-8 bytes<!-- /span -->; absent for failed read-back. |
| <a id="contract-equipment-entitlements-error"></a>`error` | [Equipment diagnostic](#contract-equipment-error); omitted when absent | Read-back failure diagnostic, required for failed status and absent for observed status. |

<a id="contract-equipment-error"></a>
#### Equipment diagnostic

Record `eq_error`: `PWRunnerEquipmentError`.

Error metadata belongs to the named operation. Native errors carry their domain/code pair; decode or contract diagnostics may carry only a message.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-error-operation"></a>`operation` | string; required | Failing boundary: service_seal, inventory_read, inventory_decode, worker_path, worker_hash, worker_signature, worker_entitlements, guest_code, dynamic_validity, associated_static_code or signing_information. |
| <a id="contract-equipment-error-domain"></a>`domain` | string; omitted when absent | Native error domain, bounded to <!-- span limits.equipment_error_domain.value_unit -->128 UTF-8 bytes<!-- /span -->; supplied together with code. |
| <a id="contract-equipment-error-code"></a>`code` | integer; omitted when absent | Native error code in domain, such as OSStatus or POSIX errno; absent together with domain for message-only diagnostics. |
| <a id="contract-equipment-error-message"></a>`message` | string; omitted when absent | Human-readable diagnostic bounded to <!-- span limits.equipment_diagnostic_bytes.value_unit -->1,024 UTF-8 bytes<!-- /span -->, when supplied. |

<a id="contract-equipment-actor"></a>
#### Actor equipment selection

Record `eq_actor`: `PWRunnerActorEquipment`.

Selection resolves the actor’s role, binds its entitlement requirements and carries the live inspection result used for activation eligibility.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-actor-requested"></a>`requested` | string; null when absent | Explicit selected or unentitled request; null when the request omitted equipment. Admitted vocabulary: closed; displayed list: exhaustive: `"selected"`, `"unentitled"`. |
| <a id="contract-equipment-actor-resolved"></a>`resolved` | string; required | Requested role, defaulting to selected when omitted. Admitted vocabulary: closed; displayed list: exhaustive: `"selected"`, `"unentitled"`. |
| <a id="contract-equipment-actor-binding_ref"></a>`binding_ref` | integer; null when absent | Zero-based index of the selected role/source row in equipment_bindings once that row exists. |
| <a id="contract-equipment-actor-required_entitlements"></a>`required_entitlements` | array of string; required | Distinct requested entitlement keys, at most <!-- span limits.actor_required_entitlements.value -->64<!-- /span -->; each nonempty key is at most <!-- span limits.actor_entitlement_key.value_unit -->255 UTF-8 bytes<!-- /span -->. |
| <a id="contract-equipment-actor-requirements_status"></a>`requirements_status` | string; required | satisfied or unsatisfied from the static entitlement dictionary; unobserved when read-back is unavailable. Admitted vocabulary: closed; displayed list: exhaustive: `"satisfied"`, `"unsatisfied"`, `"unobserved"`. |
| <a id="contract-equipment-actor-missing_requirements"></a>`missing_requirements` | array of string; omitted when absent | Requested keys whose values are absent or are not Boolean true, in request order. Empty means all satisfied; absence accompanies unobserved. |
| <a id="contract-equipment-actor-execution"></a>`execution` | [Live actor inspection](#contract-equipment-execution); required | Live code and entitlement observation for the owned actor process before activation. |

<a id="contract-equipment-execution"></a>
#### Live actor inspection

Record `eq_execution`: `PWRunnerEquipmentExecution`.

For a setup-usable owned actor, the host inspects guest code, dynamic validity, associated static code and signing information before schedule activation.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-execution-status"></a>`status` | string; required | matched when every comparison and time/ownership guard succeeds; mismatched for a differing executable/signature/entitlement requirement; inspection_failed for an unavailable inspection boundary; unobserved before eligible inspection. Admitted vocabulary: closed; displayed list: exhaustive: `"matched"`, `"mismatched"`, `"inspection_failed"`, `"unobserved"`. |
| <a id="contract-equipment-execution-pid"></a>`pid` | integer; omitted when absent | Inspected actor PID, agreeing with its launch record when present. |
| <a id="contract-equipment-execution-parent_pid"></a>`parent_pid` | integer; omitted when absent | Runner host PID recorded when inspection begins. |
| <a id="contract-equipment-execution-observed_at_monotonic_ns"></a>`observed_at_monotonic_ns` | integer; omitted when absent | Host monotonic observation time in nanoseconds. A matched record requires valid inspection start and final clock samples, a nondecreasing final time, and both samples before the additional inspection deadline when that deadline was established. The scheduler separately guards the shared setup allowance. |
| <a id="contract-equipment-execution-path"></a>`path` | string; omitted when absent | Executable path reported by live code inspection, when available. |
| <a id="contract-equipment-execution-cdhash"></a>`cdhash` | string (hex); omitted when absent | Live code's CodeDirectory hash, when available. Uses [CodeDirectory hexadecimal width](#contract-identity-other-cdhash_hex). |
| <a id="contract-equipment-execution-identifier"></a>`identifier` | string; omitted when absent | Live signing identifier, when available. |
| <a id="contract-equipment-execution-team_id"></a>`team_id` | string; present when identifier has a value; may be null | Live signing team, when supplied by the signature. |
| <a id="contract-equipment-execution-entitlements_ref"></a>`entitlements_ref` | integer; omitted when absent | Zero-based index of this actor's live entitlement read-back, when reached. |
| <a id="contract-equipment-execution-native_observations"></a>`native_observations` | array of [Live inspection call](#contract-equipment-native_observation); required | Ordered attempted prefix of guest_code, dynamic_validity, associated_static_code and signing_information, preserving each OSStatus. |
| <a id="contract-equipment-execution-reason"></a>`reason` | string; omitted when absent | Ineligible reason: not_launched, setup_unavailable, process_unavailable, ownership_unresolved, code_lookup_failed, dynamic_validation_failed, signing_readback_failed, executable_mismatch, signature_identity_mismatch, entitlement_mismatch, requirements_unsatisfied or inspection_deadline. Admitted vocabulary: closed; displayed list: exhaustive: `"not_launched"`, `"setup_unavailable"`, `"process_unavailable"`, `"ownership_unresolved"`, `"code_lookup_failed"`, `"dynamic_validation_failed"`, `"signing_readback_failed"`, `"executable_mismatch"`, `"signature_identity_mismatch"`, `"entitlement_mismatch"`, `"requirements_unsatisfied"`, `"inspection_deadline"`. |
| <a id="contract-equipment-execution-eligible"></a>`eligible` | boolean; required | True for matched execution, making this setup-usable actor eligible for activation; false preserves the failed or unavailable inspection state. |

<a id="contract-equipment-execution-inspect"></a>
##### Associating the owned process

[Runner host](#contract-identity-definitions-host) acts at after setup and before any actor activation. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Applies when `request.actors` is present. For each setup-usable child with retained ownership, inspect live code and compare path, CodeDirectory hash, identifier, team and entitlement dictionary to its bound row; recheck each required Boolean-true entitlement and the inspection deadline. Matched inspection permits activation eligibility. Mismatch or inspection failure cancels all scheduling, retains earlier setup/application publications and leaves all phases unactivated and uncollected. An unavailable setup can coexist with other usable actors when no inspection failure cancels them.

The scheduler includes inspection in its shared <!-- span limits.actor_setup_allowance.value_unit -->10,000 milliseconds<!-- /span --> monotonic setup allowance. It requires valid clock samples before and after each inspection and records inspection_deadline, cancelling scheduling, when an otherwise successful inspection reaches or exceeds that setup deadline. Before the scheduler runs, orchestration also attempts to establish an additional monotonic deadline <!-- span limits.actor_lifetime_cutoff.value_unit -->180,000 milliseconds<!-- /span --> from that initial clock sample, reusing the configured actor-lifetime duration. This additional deadline has its own clock and origin, separate from the workers' shared continuous-clock cutoff. When its initial sample is unavailable, the additional deadline comparison is absent; the scheduler's setup guard and the inspection's valid start/final clock samples still apply. When present, the additional deadline requires both inspection samples strictly before it.

Inspection retains each attempted native call and stops at its first failed
boundary. A later inspection failure preserves an earlier cancellation reason
already selected by the scheduler. Static `bound` and live `matched` express
their respective observations; the signature entitlement dictionary supplies
the values assessed at each boundary.

<a id="contract-equipment-execution-live_evidence"></a>
##### Live-inspection evidence limit

Constructed Security-call failures establish attempted-prefix retention, inspection_failed and ineligibility. Signed normal observations establish association of the selected worker with its live inspection. Spontaneous native Security failure after application remains unobserved. The optional deadline after an unavailable initial orchestration clock sample is source-supported; later inspection-clock controls concern their own samples.

**Support: [check read](#contract-support-grades) for [Live-inspection evidence limit](#contract-equipment-execution-live_evidence).** Live-inspection classification and the optional additional orchestration deadline have distinct inputs. Context: Static review of the cited producer and assertion branches. Evidence limit: Injected failure prefixes and later clock controls supply constructed observations. Ownership loss or a mismatch has a different outcome from native inspection failure. Source: [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `inspect`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `runActors`. Check: [ActorEquipmentTests.swift](../runner/Tests/PWRunnerCoreTests/ActorEquipmentTests.swift): `runActorEquipmentTests`.

<a id="contract-equipment-execution-eligibility"></a>
##### Inspection result eligibility

[Runner host](#contract-identity-definitions-host) reports at live actor inspection result projection. Entry: xpc execute. Recipient: report reader. Reports: runner reply. Select the first matching case in the listed order.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-equipment-execution-eligibility-matched"></a>1. Matched inspection | `eq_execution.status` = `"matched"` | sets `eq_execution.eligible` to `true`, sets `eq_execution.reason` to `null`. |
| <a id="contract-equipment-execution-eligibility-refused"></a>2. Refused inspection | `eq_execution.status` is one of `"mismatched"`, `"inspection_failed"` | sets `eq_execution.eligible` to `false`. |

**Support: [source read](#contract-support-grades) for [Inspection result eligibility](#contract-equipment-execution-eligibility).** A matched live inspection publishes eligibility; mismatched or failed inspection remains ineligible. Native ownership/deadline/entitlement checks precede these states. Source: [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `inspect`.

<a id="contract-equipment-native_observation"></a>
#### Live inspection call

Record `eq_native_observation`: `PWRunnerEquipmentNativeObservation`.

Each row identifies one attempted Security-framework boundary in its observed order.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-native_observation-operation"></a>`operation` | string; required | guest_code, dynamic_validity, associated_static_code or signing_information, in that order as reached. Admitted vocabulary: closed; displayed list: exhaustive: `"guest_code"`, `"dynamic_validity"`, `"associated_static_code"`, `"signing_information"`. |
| <a id="contract-equipment-native_observation-attempted"></a>`attempted` | boolean; required | True for the recorded call; the observed prefix ends at the first failing boundary. |
| <a id="contract-equipment-native_observation-osstatus"></a>`osstatus` | integer; omitted when absent | Native OSStatus returned by this operation, including zero for success. |

<a id="contract-equipment-preparation_failure"></a>
#### Actor preparation refusal

Record `eq_preparation_failure`: `PWRunnerPreparationFailure`.

Preparation stops before actor launch when the resolved plan is inconsistent or static equipment cannot be bound.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-preparation_failure-stage"></a>`stage` | string; required | resolved_plan or equipment, identifying the refusing preparation boundary. Admitted vocabulary: closed; displayed list: exhaustive: `"resolved_plan"`, `"equipment"`. |
| <a id="contract-equipment-preparation_failure-code"></a>`code` | string; required | inconsistent_assignment for resolved_plan; equipment_binding_refused for equipment. Admitted vocabulary: closed; displayed list: exhaustive: `"inconsistent_assignment"`, `"equipment_binding_refused"`. |
| <a id="contract-equipment-preparation_failure-actor_id"></a>`actor_id` | string; omitted when absent | Actor whose entitlement requirement caused the refusal, when associated. |
| <a id="contract-equipment-preparation_failure-binding_ref"></a>`binding_ref` | integer; omitted when absent | Zero-based refused binding row when one was produced or identified. |
| <a id="contract-equipment-preparation_failure-reason"></a>`reason` | string; omitted when absent | Equipment refusal classification, when the failure arose from equipment preparation. |

<a id="contract-equipment-preparation_failure-retain"></a>
##### Preparation refusal contents

[Runner host](#contract-identity-definitions-host) reports at actor preparation refusal before launch. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Applies when (`request.actors` is present and `request.phases` is present). sets `reply.execution_form` to `"actors"`, sets `reply.normalized_outcome` to `"runner_failed"`, sets `reply.rc` to `1`, sets `reply.steps` to an empty array, sets `reply.extension_events` to an empty array, sets `reply.transfers` to an empty array, sets `reply.resources.tokens` to an empty array, sets `reply.resources.deliveries` to an empty array, sets `reply.resources.handles` to an empty array, sets `reply.schedule.cancelled` to `"preparation_refused"`, sets `reply.authority_setup.host.run.disposition` to `"not_attempted"`, sets `reply.authority_setup.host.regions` to an empty array, sets `reply.authority_setup.host.custody` to an empty array, retains the records `reply.equipment_inventory`, retains the records `reply.equipment_bindings`, retains the records `reply.equipment_entitlements`. The resolved plan is inconsistent or equipment binding fails before actor launch.

Actors have `launch_refused` setup, absent launch/subprocess, and application
assessment from their declaration and unlaunched state. Phases keep their
declared identities with false arrival/completion and collection `not_reached`.
Equipment inventory/binding/read-back rows preserve whichever preparation
observations were obtained. The schedule records `preparation_refused`; host
authority run setup is `not_attempted`, regions/custody are empty, and worker
setup scopes identify their declared actors with decision `not_observed`.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-equipment-preparation_failure-retain-counts"></a>Declaration row counts | Requires (count of `reply.actors` = count of `request.actors` and count of `reply.phases` = count of `request.phases`). |
| <a id="contract-equipment-preparation_failure-retain-actors"></a>Unlaunched actor rows | Binding `a`: entry in `reply.actors`. For each `a`. sets `reply.actors[a].setup_status` to `"launch_refused"`, sets `reply.actors[a].application_count` to `0`, withholds `reply.actors[a].launch`, withholds `reply.actors[a].subprocess`. |
| <a id="contract-equipment-preparation_failure-retain-phases"></a>Unactivated phase rows | Binding `p`: entry in `reply.phases`. For each `p`. sets `reply.phases[p].arrival_observed` to `false`, sets `reply.phases[p].completion_observed` to `false`, sets `reply.phases[p].collection_status` to `"not_reached"`. |
| <a id="contract-equipment-preparation_failure-retain-actor_identity"></a>Actor identity in declaration order | Binding `a`: entry in `request.actors`. Binding `b`: entry in `reply.actors`. For each `a`, `b`. Applies when `a` = `b`. Requires (`request.actors[a].actor_id` = `reply.actors[b].actor_id` and `request.actors[a].sandbox.mode` = `reply.actors[b].mode` and `reply.actors[b].index` = `a`). |
| <a id="contract-equipment-preparation_failure-retain-phase_identity"></a>Phase identity in declaration order | Binding `p`: entry in `request.phases`. Binding `q`: entry in `reply.phases`. For each `p`, `q`. Applies when `p` = `q`. Requires (`request.phases[p].phase_id` = `reply.phases[q].phase_id` and `request.phases[p].actor_id` = `reply.phases[q].actor_id` and `reply.phases[q].ordinal` = (`p` + `1`) and count of `reply.phases[q].action_ids` = count of `request.phases[p].actions`). |
| <a id="contract-equipment-preparation_failure-retain-action_probe"></a>Retained probe action identity | Binding `p`: entry in `request.phases`. Binding `q`: entry in `reply.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `b`: entry in `reply.phases[q].action_ids`. For each `p`, `q`, `a`, `b`. Applies when (`p` = `q` and `a` = `b` and `request.phases[p].actions[a]` has alternative `"probe"`). Requires `reply.phases[q].action_ids[b]` = `variant(request.phases[p].actions[a], 'probe').step_id`. |
| <a id="contract-equipment-preparation_failure-retain-action_extensionaction"></a>Retained extensionAction action identity | Binding `p`: entry in `request.phases`. Binding `q`: entry in `reply.phases`. Binding `a`: entry in `request.phases[p].actions`. Binding `b`: entry in `reply.phases[q].action_ids`. For each `p`, `q`, `a`, `b`. Applies when (`p` = `q` and `a` = `b` and `request.phases[p].actions[a]` has alternative `"extensionAction"`). Requires `reply.phases[q].action_ids[b]` = `variant(request.phases[p].actions[a], 'extensionAction').step_id`. |

**Support: [source read](#contract-support-grades) for [Preparation refusal contents](#contract-equipment-preparation_failure-retain).** Before-launch plan or equipment refusal enumerates the already-admitted request actors, phases and action IDs in declaration order, preserving available equipment beside empty execution collections and unlaunched/unactivated states. Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `runActors`, `actorPreparationRefusal`.

<a id="contract-equipment-authority_setup"></a>
#### Authority setup account

Record `eq_authority_setup`: `PWRunnerAuthoritySetup`.

The host retains its own setup/cleanup observations and each worker’s separately acquired setup publications.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-authority_setup-host"></a>`host` | [Host authority scopes](#contract-equipment-authority_host); required | Host-owned run, shared-region and custody scopes. |
| <a id="contract-equipment-authority_setup-workers"></a>`workers` | array of [Authority operation scope](#contract-equipment-authority_scope); required | Actor-indexed worker setup scopes, one per declared actor and bound to that actor's identifier. |

<a id="contract-equipment-authority_host"></a>
#### Host authority scopes

Record `eq_authority_host`: `PWRunnerAuthorityHost`.

The host separates run prerequisites, actor shared regions and token custody into their owning scopes.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-authority_host-run"></a>`run` | [Authority operation scope](#contract-equipment-authority_scope); required | Run-wide prerequisite account, including core-limit setup. |
| <a id="contract-equipment-authority_host-regions"></a>`regions` | array of [Authority operation scope](#contract-equipment-authority_scope); required | Per-actor shared authority-region allocation, initialization, descriptor and cleanup observations. |
| <a id="contract-equipment-authority_host-custody"></a>`custody` | array of [Authority operation scope](#contract-equipment-authority_scope); required | Per-token host-private custody allocation, erasure and unmap observations. |

<a id="contract-equipment-authority_scope"></a>
#### Authority operation scope

Record `eq_authority_scope`: `PWRunnerAuthorityScope`.

A scope retains operation cells, its setup decision and ownership state. A decision and individual operation publications have separate acquisition boundaries.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-authority_scope-actor_id"></a>`actor_id` | string; omitted when absent | Bound actor identifier for worker or region scope, when applicable. |
| <a id="contract-equipment-authority_scope-actor_index"></a>`actor_index` | integer; omitted when absent | Zero-based actor position for worker or region scope. |
| <a id="contract-equipment-authority_scope-token_ref"></a>`token_ref` | string; omitted when absent | Bound token identifier for custody scope, when applicable. |
| <a id="contract-equipment-authority_scope-token_index"></a>`token_index` | integer; omitted when absent | Zero-based token position for custody scope. |
| <a id="contract-equipment-authority_scope-required"></a>`required` | boolean; omitted when absent | Whether authority setup is required for the worker's admitted actor plan. |
| <a id="contract-equipment-authority_scope-publication"></a>`publication` | string; omitted when absent | Worker decision acquisition: observed or not_observed; host-recorded scopes use their directly recorded disposition. Admitted vocabulary: closed; displayed list: exhaustive: `"observed"`, `"not_observed"`. |
| <a id="contract-equipment-authority_scope-disposition"></a>`disposition` | string; omitted when absent | Worker decision ready, not_required or terminal_required_failure when observed; host scope state such as not_attempted, ready or failed records its own preparation. |
| <a id="contract-equipment-authority_scope-primary_operation"></a>`primary_operation` | integer; omitted when absent | Slot of the first failed/rejected operation supporting the scope decision; worker terminal_required_failure requires that published primary cell. |
| <a id="contract-equipment-authority_scope-operations"></a>`operations` | array of [Authority operation cell](#contract-equipment-authority_operation); required | Independently observed operation cells in slot order, including cleanup after a setup failure. |
| <a id="contract-equipment-authority_scope-ownership"></a>`ownership` | object with string keys and string values; required | Named ownership states: object_name, descriptor and mapping use not_acquired, held, released or unresolved; shared_erasure/private_erasure use not_present, performed, withheld_not_quiescent or unobserved. |
| <a id="contract-equipment-authority_scope-cleanup_reference"></a>`cleanup_reference` | [Unresolved shared-memory name](#contract-equipment-cleanup_reference); omitted when absent | Retained unresolved shared-memory name after successful creation and failed unlink, requiring ownership-aware recovery. |
| <a id="contract-equipment-authority_scope-integrity_errors"></a>`integrity_errors` | array of string; omitted when absent | Detected malformed, repeated, missing-primary or mismatched-association publications; absence means the decoder found none. |

<a id="contract-equipment-authority_scope-acquire"></a>
##### Acquiring setup decisions and operations

[Runner host](#contract-identity-definitions-host) reports at worker shared-region collection. Entry: xpc execute. Recipient: xpc caller, runner client, controller. Reports: runner reply. Applies when `request.actors` is present. After worker-identity agreement, acquire-load the decision snapshot first, then independently acquire-load each published operation cell. Retain independently valid operation cells even when the decision is absent. For an observed decision, validate its raw actor/required association before projecting the decision and its primary operation.

The decision's release orders prerequisite cells. Reading the decision first
keeps a newly observed decision joined to its earlier primary publication.
Each cell still has its own publication flag and kind/state guards. A cleanup
cell can therefore be retained before the terminal decision appears. Invalid
cells contribute integrity errors while independently valid observations
remain available.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-equipment-authority_scope-acquire-primary"></a>Retained primary support | Binding `o`: entry in `eq_authority_scope.operations`. Association restriction for `o`: (`eq_authority_scope.operations[o].slot` = `eq_authority_scope.primary_operation` and `eq_authority_scope.operations[o].state` is one of `"failed"`, `"rejected"`). Applies when (`eq_authority_scope.publication` = `"observed"` and `eq_authority_scope.primary_operation` is present). Requires (if number of matching entries for `o` = `0`, then (`eq_authority_scope.integrity_errors` is present and `"setup_primary_unpublished"` is one of `eq_authority_scope.integrity_errors`)). A missing primary cell adds an integrity error alongside the decision and independently valid cells. |
| <a id="contract-equipment-authority_scope-acquire-decision"></a>Observed decision applicability | Applies when `eq_authority_scope.publication` = `"observed"`. Requires ((if `eq_authority_scope.disposition` = `"terminal_required_failure"`, then (`eq_authority_scope.required` and `eq_authority_scope.primary_operation` is present)) and (if `eq_authority_scope.disposition` = `"ready"`, then `eq_authority_scope.required`) and (if `eq_authority_scope.disposition` = `"not_required"`, then `eq_authority_scope.required` = `false`)). |

**Support: [check read](#contract-support-grades) for [Authority operation scope](#contract-equipment-authority_scope) and its descendants.** Constructed published cleanup cell survives absent decision, preserves native failure and cleanup role; corrupted publication flags yield invalid_setup_cell. Context: Constructed shared-memory buffer decoded by the production host decoder; source and assertions read. Evidence limit: The check covers cell eligibility and corrupted flags; source supplies decision-first acquisition and primary-cell validation. No execution credit. Source: [AuthoritySetupRuntime.swift](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift): `decodeAuthoritySetup`. Check: [ActorAuthorityTests.swift](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift): `runActorAuthorityTests`.

<a id="contract-equipment-authority_operation"></a>
#### Authority operation cell

Record `eq_authority_operation`: `PWRunnerAuthorityOperation`.

Each fixed slot identifies one operation once. Kind controls which native fields are meaningful; cleanup cells retain their own failures alongside the primary setup failure.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-authority_operation-slot"></a>`slot` | integer; required | Zero-based fixed operation-cell position within its worker, region, custody or run scope. |
| <a id="contract-equipment-authority_operation-operation"></a>`operation` | string; required | Operation registered for that scope and slot, such as descriptor_close, header_binding, shm_unlink or final_erase. |
| <a id="contract-equipment-authority_operation-role"></a>`role` | string; required | setup or cleanup, according to the operation's boundary. Admitted vocabulary: closed; displayed list: exhaustive: `"setup"`, `"cleanup"`. |
| <a id="contract-equipment-authority_operation-state"></a>`state` | string; required | succeeded/failed for native integer or mapping operations; accepted/rejected for validation; available/unavailable for symbols; performed for memory operations; not_attempted for an explicitly unattempted cell. Admitted vocabulary: closed; displayed list: exhaustive: `"succeeded"`, `"failed"`, `"accepted"`, `"rejected"`, `"available"`, `"unavailable"`, `"performed"`, `"not_attempted"`. |
| <a id="contract-equipment-authority_operation-native_kind"></a>`native_kind` | string; omitted when absent | integer, error_code, mapping, symbol, validation or memory, identifying the observation convention. Admitted vocabulary: closed; displayed list: exhaustive: `"integer"`, `"error_code"`, `"mapping"`, `"symbol"`, `"validation"`, `"memory"`. |
| <a id="contract-equipment-authority_operation-native_rc"></a>`native_rc` | integer; omitted when absent | Recorded return for integer/error_code operations; absent for mapping, symbol, validation and memory observations. |
| <a id="contract-equipment-authority_operation-errno"></a>`errno` | integer; omitted when absent | Captured native errno on failed integer/mapping operations; absent for other states and kinds. |
| <a id="contract-equipment-authority_operation-detail"></a>`detail` | string; omitted when absent | Operation-specific validation reason, including descriptor_missing or header magic/identity/actor_index/slot_counts/region_extent mismatch. |
| <a id="contract-equipment-authority_operation-value"></a>`value` | integer; omitted when absent | Operation-specific unsigned native observation when the cell marks a value present, such as object/page size. |

<a id="contract-equipment-authority_operation-slots"></a>
##### Registered operation slots

Value: `{"run":["core_limit"],"worker":["issue_symbol","consume_symbol","release_symbol","core_limit","descriptor_presence","fstat","page_size","object_size","mmap","descriptor_close","header_binding","terminal_owned_inbound_clear","rejected_mapping_munmap"],"region":["shm_open","shm_unlink","fd_cloexec","ftruncate","mmap","header_initialize","authority_duplicate","authority_spawn_dup2","close_launch_duplicate","close_original_descriptor","shared_clear","munmap"],"custody":["mmap","final_erase","munmap"]}`.

The index within each list is its fixed slot. Worker descriptor close can
belong to setup or cleanup according to the branch. Worker slots 11–12,
region slots 8–11 and custody slots 1–2 are cleanup.

<a id="contract-equipment-cleanup_reference"></a>
#### Unresolved shared-memory name

Record `eq_cleanup_reference`: `PWAuthorityCleanupReference`.

A successful shm_open followed by failed shm_unlink retains this recovery reference while preserving unresolved ownership.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-equipment-cleanup_reference-kind"></a>`kind` | string; required | posix_shm_name, the retained resource name form. Admitted vocabulary: closed; displayed list: exhaustive: `"posix_shm_name"`. |
| <a id="contract-equipment-cleanup_reference-name"></a>`name` | string; required | Absolute POSIX shared-memory name beginning with slash, at most <!-- span limits.authority_cleanup_name.value_unit -->31 UTF-8 bytes<!-- /span -->. |
| <a id="contract-equipment-cleanup_reference-host_pid"></a>`host_pid` | integer; required | Host PID recorded when the name was created. |
| <a id="contract-equipment-cleanup_reference-session_nonce"></a>`session_nonce` | integer; required | Run nonce associated with creation of this named region. |
| <a id="contract-equipment-cleanup_reference-recovery_state"></a>`recovery_state` | string; required | unresolved_manual: recovery must establish current ownership before acting because a reused name can identify another object. Admitted vocabulary: closed; displayed list: exhaustive: `"unresolved_manual"`. |

**Support: [source read](#contract-support-grades) for [Equipment and authority setup](#contract-equipment) and its descendants.** Imported public field definitions joined to producer/decoder/assessment meanings; explicit rule and evidence gaps preserve scope. Source: [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `ActorEquipmentPreparation`; [PWRunnerEquipment.swift](../runner/Sources/PWRunnerCore/PWRunnerEquipment.swift): `pwRunnerEquipmentProblems`; [AuthoritySetupRuntime.swift](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift): `decodeAuthoritySetup`; [PWRunnerAuthoritySetup.swift](../runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift): `authoritySetupIntegrityErrors`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `actorPreparationRefusal`, `inspectionDeadline`; [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift): `actorExtensionEvidenceProblem`; [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `didSetUp`; [MonotonicDeadline.swift](../runner/Sources/PWRunnerCore/MonotonicDeadline.swift): `static func now`.

<a id="contract-profile"></a>
### Compiled-profile receipts

Entry: cli run, runner verify, direct xpc. Recipient: controller, xpc caller, cli caller. Reports: runner reply.

The host reports the result of an optional capture of the worker's compiled policy before application.

<a id="contract-profile-receipt"></a>
#### Receipt

Binding `a`: entry in `reply.actors`. Record `receipt` locations: `reply.compiled_profile`, `reply.actors[a].compiled_profile`.

The containing reply's producer contract identifies the receipt's contract.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-profile-receipt-status"></a>`status` | string; required | `captured` states that the host's capture checks passed. `unavailable` states that a capture condition failed. Admitted vocabulary: closed; displayed list: exhaustive: `"captured"`, `"unavailable"`. |
| <a id="contract-profile-receipt-reason"></a>`reason` | string; omitted when absent | The host names the first failing capture condition. The controller's label check accepts the carried reason string. Boundary: controller reply admission. Admitted vocabulary: open; displayed list: illustrative: `"successful_application_unconfirmed"`, `"worker_not_complete"`, `"capture_nonce_mismatch"`. Unfamiliar values: retained as the host's reason string. |
| <a id="contract-profile-receipt-worker_pid"></a>`worker_pid` | integer; required | The process identifier of the worker whose output the host collected. |
| <a id="contract-profile-receipt-producer"></a>`producer` | string; omitted when absent | `worker` on a captured receipt identifies the component that captured the bytes. |
| <a id="contract-profile-receipt-capture_stage"></a>`capture_stage` | string; omitted when absent | `before_apply` on a captured receipt identifies when the worker captured the bytes. |
| <a id="contract-profile-receipt-request_nonce"></a>`request_nonce` | string; omitted when absent | The host returns the request's capture nonce after comparing it with the worker's recorded bytes. A comparison with a separately retained request nonce supplies a consumer's request association; the controller's carried-label check has no request-nonce operand. |
| <a id="contract-profile-receipt-profile_type"></a>`profile_type` | integer; omitted when absent | The supported compiler result representation is `0`. |
| <a id="contract-profile-receipt-bytecode_length"></a>`bytecode_length` | integer; omitted when absent | The number of raw bytes copied from the compiled object, positive and at most <!-- span limits.compiled_profile.value_unit -->1,048,576 bytes<!-- /span -->. It counts the decoded bytes represented by `bytecode_b64`, separately for each opted-in worker. |
| <a id="contract-profile-receipt-bytecode_sha256"></a>`bytecode_sha256` | string (hex); omitted when absent | The host's SHA-256 digest of the captured bytes, presented as lowercase hexadecimal. |
| <a id="contract-profile-receipt-bytecode_b64"></a>`bytecode_b64` | string (base64); omitted when absent | The bytes copied from the compiler object passed to `sandbox_apply`, presented as base64. |
| <a id="contract-profile-receipt-source_sha256"></a>`source_sha256` | string (hex); omitted when absent | The SHA-256 digest of the UTF-8 C-string source passed to compilation, presented as lowercase hexadecimal. The host compares it with its supplied source bytes; an embedded NUL cannot establish the full source identity. |
| <a id="contract-profile-receipt-source_length"></a>`source_length` | integer; omitted when absent | The supplied source's UTF-8 byte count. |
| <a id="contract-profile-receipt-params_sha256"></a>`params_sha256` | string (hex); omitted when absent | The order-independent digest of parameter names and values consumed by the worker, presented as lowercase hexadecimal. |
| <a id="contract-profile-receipt-parameter_count"></a>`parameter_count` | integer; omitted when absent | The count of parameters supplied to the worker. |

**Bytecode length.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-profile-receipt-bytecode_length-captured"></a>Captured byte extent | Requires (if `receipt.status` = `"captured"`, then (`receipt.bytecode_length` is present and `receipt.bytecode_length` > `0` and `receipt.bytecode_length` ≤ `1,048,576 bytes` (`compiled_profile`) )). |

**Bytecode.**

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-profile-receipt-bytecode_b64-extent"></a>Captured payload extent | Applies when `receipt.status` = `"captured"`. Requires decoded byte length of `receipt.bytecode_b64` = `receipt.bytecode_length`. |

<a id="contract-profile-receipt-identity"></a>
##### Captured input identity

Each parameter pair digest hashes its little-endian 32-bit key length, key bytes, little-endian 32-bit value length and value bytes. The parameter digest hashes the little-endian 32-bit count followed by sorted pair digests.

<a id="contract-profile-receipt-presence"></a>
##### Receipt presence

[Runner host](#contract-identity-definitions-host) reports at worker collection. Entry: cli run, runner verify, direct xpc. Recipient: controller, xpc caller. Reports: runner reply. Capture was requested for this worker and worker output was collected. Include the optional capture receipt in that worker output.

A failure that produces no worker output leaves the receipt absent; absence has several possible causes.

<a id="contract-profile-receipt-host"></a>
##### The host decides capture availability

[Runner host](#contract-identity-definitions-host) reports at collected worker capture decoding. Entry: cli run, runner verify, direct xpc. Recipient: controller, xpc caller. Reports: runner reply. Capture was requested for this worker and worker output was collected. The first failed condition selects the consequence.

Passing every condition produces `captured` with the capture fields.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-profile-receipt-host-application"></a>Application | Application was observed and its return code was zero. |
| <a id="contract-profile-receipt-host-application-failure"></a>Application › First failed guard reason | On failure, sets `receipt.reason` to `"successful_application_unconfirmed"`. |
| <a id="contract-profile-receipt-host-completion"></a>Worker completion | Follows [Application](#contract-profile-receipt-host-application). The worker published done and the collected exit code is zero with no terminating signal. |
| <a id="contract-profile-receipt-host-completion-failure"></a>Worker completion › First failed guard reason | On failure, sets `receipt.reason` to `"worker_not_complete"`. |
| <a id="contract-profile-receipt-host-capture"></a>Capture completion | Follows [Worker completion](#contract-profile-receipt-host-completion). The worker published capture completion. |
| <a id="contract-profile-receipt-host-capture-failure"></a>Capture completion › First failed guard reason | On failure, sets `receipt.reason` to `"capture_not_complete"`. |
| <a id="contract-profile-receipt-host-status"></a>Capture status | Follows [Capture completion](#contract-profile-receipt-host-capture). The recorded capture status was accepted. |
| <a id="contract-profile-receipt-host-status-failure"></a>Capture status › First failed guard reason | On failure, sets `receipt.reason` to `"worker_capture_refused"`. |
| <a id="contract-profile-receipt-host-pid"></a>Process association | Follows [Capture status](#contract-profile-receipt-host-status). The recorded PID equals the worker PID collected by the host. |
| <a id="contract-profile-receipt-host-pid-failure"></a>Process association › First failed guard reason | On failure, sets `receipt.reason` to `"capture_worker_mismatch"`. |
| <a id="contract-profile-receipt-host-nonce"></a>Nonce association | Follows [Process association](#contract-profile-receipt-host-pid). The recorded nonce bytes equal the valid request nonce. |
| <a id="contract-profile-receipt-host-nonce-failure"></a>Nonce association › First failed guard reason | On failure, sets `receipt.reason` to `"capture_nonce_mismatch"`. |
| <a id="contract-profile-receipt-host-extent"></a>Extent and type | Follows [Nonce association](#contract-profile-receipt-host-nonce). The profile type is zero and its raw byte count is positive and at most <!-- span limits.compiled_profile.value_unit -->1,048,576 bytes<!-- /span -->. |
| <a id="contract-profile-receipt-host-extent-failure"></a>Extent and type › First failed guard reason | On failure, sets `receipt.reason` to `"capture_extent_or_type_invalid"`. |
| <a id="contract-profile-receipt-host-digest"></a>Payload digest | Follows [Extent and type](#contract-profile-receipt-host-extent). SHA-256 of the captured bytes equals the recorded digest. |
| <a id="contract-profile-receipt-host-digest-failure"></a>Payload digest › First failed guard reason | On failure, sets `receipt.reason` to `"capture_bytecode_digest_mismatch"`. |
| <a id="contract-profile-receipt-host-input"></a>Consumed input | Follows [Payload digest](#contract-profile-receipt-host-digest). The recorded source length and digest and parameter count and digest equal the host's supplied inputs. |
| <a id="contract-profile-receipt-host-input-failure"></a>Consumed input › First failed guard reason | On failure, sets `receipt.reason` to `"capture_consumed_input_mismatch"`. |
| <a id="contract-profile-receipt-host-failure"></a>Capture failure | On failure, sets `receipt.status` to `"unavailable"`, withholds `receipt.producer`, withholds `receipt.capture_stage`, withholds `receipt.request_nonce`, withholds `receipt.profile_type`, withholds `receipt.bytecode_length`, withholds `receipt.bytecode_sha256`, withholds `receipt.bytecode_b64`, withholds `receipt.source_sha256`, withholds `receipt.source_length`, withholds `receipt.params_sha256`, withholds `receipt.parameter_count`, keeps the assessment `reply.normalized_outcome`. |
| <a id="contract-profile-receipt-host-success"></a>Successful receipt | On success, sets `receipt.status` to `"captured"`, sets `receipt.producer` to `"worker"`, sets `receipt.capture_stage` to `"before_apply"`, sets `receipt.profile_type` to `0`, withholds `receipt.reason`. |

**Support: [check read](#contract-support-grades) for [The host decides capture availability](#contract-profile-receipt-host).** The read checks construct worker bytes, corrupt each capture input and assert unavailability and withheld bytecode. Context: Constructed shared-memory bytes and injected application/termination arguments. Evidence limit: This owner credits source and check reading. The shared-memory fixture establishes host checks; the native same-pointer capture is source-supported here. Source: [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `decodeProfileCapture`. Check: [CompiledProfileCaptureTests.swift](../runner/Tests/PWRunnerCoreTests/CompiledProfileCaptureTests.swift): `runCompiledProfileCaptureTests`.

<a id="contract-profile-receipt-labels"></a>
##### The controller checks carried labels

[Controller](#contract-identity-definitions-controller) checks at reply admission. Entry: cli run, runner verify. Recipient: cli caller. Reports: runner reply. Applies when `receipt` is present.

After public producer admission and reply-capacity checks, the controller applies these conditions to every present receipt, including actor, preparation-failure and reporting-failure records. The retained nonce, bytecode, digests, lengths and counts remain the host's assertions; their production checks belong to the host capture rule.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-profile-receipt-labels-status"></a>Status vocabulary | Requires `receipt.status` is one of `"captured"`, `"unavailable"`. |
| <a id="contract-profile-receipt-labels-captured"></a>Captured labels | Requires (if `receipt.status` = `"captured"`, then (`receipt.producer` = `"worker"` and `receipt.capture_stage` = `"before_apply"`)). |
| <a id="contract-profile-receipt-labels-unavailable"></a>Unavailable labels | Requires (if `receipt.status` = `"unavailable"`, then (`receipt.producer` is absent and `receipt.capture_stage` is absent)). |
| <a id="contract-profile-receipt-labels-failure"></a>A failed label check for run | Entry: cli run. On failure, sets `envelope.result.normalized_outcome` to `"malformed_runner_response"`, sets `envelope.result.ok` to `false`, withholds `envelope.data.runner_sandbox_diagnostics`, retains the records `reply`. For `run`, the controller refuses admission of the containing report, reports a failed result and exits with status 1. The retained report remains the host's account. |
| <a id="contract-profile-receipt-labels-verify_failure"></a>A failed label check for runner verify | Entry: runner verify. On failure, sets `result.ok` to `false`, sets `result.exit_code` to `1`, sets `result.normalized_outcome` to `"malformed_runner_response"`, sets `runner_verify.normalized_outcome` to `"malformed_runner_response"`, sets `runner_verify.runner_pid` to `null`, retains the records `runner_verify.runner_client`, retains the records `runner_verify.runner_result`. `runner verify` emits its verification envelope and exits with status 1. |

**Support: [executed](#contract-support-grades) for [A failed label check for run](#contract-profile-receipt-labels-failure) and its descendants.** The constructed check follows admission through the public outcome, exit status, result, retained decoded report and diagnostic presence. Context: Constructed typed replies carried through the run command admission and envelope path. Evidence limit: The unit case passed against the source committed as 5e51300d; its development run is disposable. Constructed replies establish admission and retention, while native capture is a separate observation. Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `admission_problem`. Check: [run_flow.rs](../controller/src/run_flow.rs): `compiled_profile_labels_determine_the_public_admission_outcome`. Run: `20261110T195016Z_0d197151`. Source snapshot: `5e51300d620e2a3ead419380977212d2c3e41ba1`.

**Support: [source read](#contract-support-grades) for [A failed label check for runner verify](#contract-profile-receipt-labels-verify_failure).** A refused verify reply preserves the returned capture and decoded report, leaves runner_pid null, copies the refusal classification into data and result, and returns exit 1. Context: Read the verify command's Refused branch, payload construction, JsonResult construction and returned exit code. Evidence limit: The verify consequence is supported by these branches. The executed constructed-label case belongs to the run consequence. Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`; [run_flow.rs](../controller/src/run_flow.rs): `pub(crate) fn admit_reply`; [json_contract.rs](../controller/src/json_contract.rs): `impl JsonResult`.

<a id="contract-profile-receipt-labels-example"></a>
###### An unsupported capture producer

A current-build reply carries a captured receipt whose producer is `future`. The receipt-label check refuses that reply as `malformed_runner_response`.

**Support: [source read](#contract-support-grades) for [The controller checks carried labels](#contract-profile-receipt-labels) and its descendants.** Run and runner verify use the same post-version reply admission; it checks each present top-level or actor receipt's status, producer and capture-stage labels before command-specific refusal projection. Context: Read both command routes into reply admission and the compiled-profile label loop. Evidence limit: The predicates and command dispatch are source-read. The executed constructed-label control under the run consequence supplies its separate run evidence. Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `pub(crate) fn admission_problem`; [run_flow.rs](../controller/src/run_flow.rs): `pub(crate) fn reply_contract`, `pub(crate) fn admit_reply`; [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`.

**Support: [source read](#contract-support-grades) for [Receipt](#contract-profile-receipt) and its descendants.** Opt-in capture copies the same compiled object before apply; the collected worker output includes the optional host-checked receipt. Fields bind the observed worker, nonce and consumed input bytes. Shared-memory and public JSON projections are distinct. Context: Read C capture, compile/apply call site, Swift output construction and ordered receipt checks. Evidence limit: Source reading establishes the branch account. Live capture behavior and platform private-layout compatibility require their native checks. Source: [pw_profile_capture.h](../controller/tools/pw_probe_runner/pw_profile_capture.h): `pw_capture_profile`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `pw_capture_profile`; [ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift): `profileCapture: input.captureCompiledProfile`; [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `decodeProfileCapture`.

## The controller's assessment and output

<a id="contract-envelope"></a>
### The controller envelope

<a id="contract-envelope-run"></a>
#### Run envelope

Actor: [Controller](#contract-identity-definitions-controller). Boundary: run envelope presentation. Entry: cli run. Recipient: cli caller. Reports: run envelope. Record `run_envelope`: `rust.RunEnvelope`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-envelope-run-build"></a>`build` | [Build identification](#contract-identity-build); required | The emitting binary's embedded build stamp, separate from nested producers. |
| <a id="contract-envelope-run-data"></a>`data` | [Run payload](#contract-envelope-data); required | Run payload, retaining observations under their admission and collection conditions. |
| <a id="contract-envelope-run-generated_at_unix_ms"></a>`generated_at_unix_ms` | integer; required | Emitter wall-clock time at rendering, in milliseconds since the Unix epoch. An unavailable pre-epoch duration becomes zero. Child spans and continuous-clock ordering have separate observations. |
| <a id="contract-envelope-run-kind"></a>`kind` | string; required | `run` identifies specimen execution. |
| <a id="contract-envelope-run-result"></a>`result` | [Operation result](#contract-envelope-result); required | The controller operation's result. Nested native and child returns retain their own scopes. |

<a id="contract-envelope-helper"></a>
#### Compiler-helper envelope

Actor: [Compiler helper](#contract-identity-definitions-helper). Boundary: compiler-helper envelope presentation. Entry: standalone helper, controller helper stdin. Recipient: helper caller, controller. Reports: helper envelope. Record `compiler_envelope`: `rust.HelperEnvelope`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-envelope-helper-build"></a>`build` | [Build identification](#contract-identity-build); required | The helper binary's embedded build stamp. |
| <a id="contract-envelope-helper-data"></a>`data` | [Compiler-helper data](#contract-policy-check_data); required | Helper policy metadata, import inventory and compilation result. |
| <a id="contract-envelope-helper-generated_at_unix_ms"></a>`generated_at_unix_ms` | integer; required | Helper wall-clock time at rendering, in milliseconds since the Unix epoch. An unavailable pre-epoch duration becomes zero. |
| <a id="contract-envelope-helper-kind"></a>`kind` | string; required | `sbpl_check` identifies standalone or captured helper compilation. |
| <a id="contract-envelope-helper-result"></a>`result` | [Operation result](#contract-envelope-result); required | The helper operation's result, separate from any worker execution. |

<a id="contract-envelope-result"></a>
#### Operation result

Record `result`: `rust.JsonResult`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-envelope-result-ok"></a>`ok` | boolean; required | For an admitted specimen result, true exactly when the host outcome is `finished`. Evidence findings and failed individual attempts can coexist with true. Other commands define success for their own operation. |
| <a id="contract-envelope-result-rc"></a>`rc` | integer; null when absent | Optional native-style result slot. Controller/helper-created results leave it null; native attempt returns remain in their nested records. |
| <a id="contract-envelope-result-exit_code"></a>`exit_code` | integer; null when absent | Selected controller/helper exit status. For a run: zero for admitted `finished`, one for an execution/refusal outcome, two for tool or input-handling errors. |
| <a id="contract-envelope-result-normalized_outcome"></a>`normalized_outcome` | string; null when absent | Selected operation label. An admitted host outcome is copied; controller and client admission failures use the classifications below. |
| <a id="contract-envelope-result-errno"></a>`errno` | integer; null when absent | Optional native errno slot. Controller/helper-created results leave it null; nested errno values concern their own operations. |
| <a id="contract-envelope-result-error"></a>`error` | string; null when absent | Human-readable diagnostic, null on successful controller/helper results. After execution admission, precedence is host error, client `stdout_capture_error`, client `stdout_parse_error`, then a generic unsuccessful-run message. |
| <a id="contract-envelope-result-stderr"></a>`stderr` | string; null when absent | Optional captured text slot. Controller/helper-created results leave it null; client and child capture text stays in its own record. |
| <a id="contract-envelope-result-stdout"></a>`stdout` | string; null when absent | Optional captured text slot. Controller/helper-created results leave it null; typed nested data carries the report. |

<a id="contract-envelope-data"></a>
#### Run payload

Actor: [Controller](#contract-identity-definitions-controller). Boundary: run payload assembly. Entry: cli run. Recipient: cli caller. Reports: run envelope. Record `run_data`: `rust.RunData`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-envelope-data-runner_sandbox_diagnostics"></a>`runner_sandbox_diagnostics` | [Execution diagnostics](#contract-diagnostics-execution); null when absent | Assessments after client/reply admission. Null for earlier refusals and tool errors. An admitted execution with no host report can still produce the controller's no-worker assessment. |
| <a id="contract-envelope-data-specimen"></a>`specimen` | [Run dossier](#contract-dossier-specimen); required | Held-input, equipment and provenance observations, including partial records on failure. |
| <a id="contract-envelope-data-policy_check"></a>`policy_check` | [Fallback helper capture](#contract-policy-fallback); null when absent | Independent helper capture after an eligible admitted client-terminal `xpc_error`. Null when fallback was not invoked. |
| <a id="contract-envelope-data-actor_policy_checks"></a>`actor_policy_checks` | array of [Per-actor fallback capture](#contract-policy-actor_check); omitted when absent | Captures for actor declarations carrying a sandbox.policy object, in request order, when fallback is eligible. Collection of these policy objects precedes host admission of sandbox mode. Omitted when fallback is ineligible or the request contains no actor policy objects. |
| <a id="contract-envelope-data-timeout_ms"></a>`timeout_ms` | integer; null when absent | Selected runner-client wait budget in milliseconds when argument parsing supplied it; null when no usable configuration was obtained. |
| <a id="contract-envelope-data-runner_client"></a>`runner_client` | [Controller observation of the client process](#contract-transport-client); null when absent | Client invocation, capture and delivery account. Null when the client was not invoked or launch failed before a capture returned. |
| <a id="contract-envelope-data-runner_result"></a>`runner_result` | [Execution record](#contract-reply-record); null when absent | Structurally decoded host reply when available, retained even if a later label gate refuses admission. Null when there is no decodable reply; an accepted capture can retain its exact bytes separately. |
| <a id="contract-envelope-data-request_failure"></a>`request_failure` | [Projected request refusal](#contract-refusals-projection); omitted when absent | Controller refusal code/path, or the host refusal projected from an admitted `bad_request` reply. Omitted when the selected result supplies none. |

<a id="contract-envelope-data-select"></a>
##### Select the public result

[Controller](#contract-identity-definitions-controller) reports at run completion after admission. Entry: cli run. Recipient: cli caller. Reports: run envelope. Select the first matching case in the listed order. Applies when `envelope.data.runner_result` is present. Client capture and host reply admission have succeeded. Follows [Apply reply-wide findings](#contract-diagnostics-execution-reply_checks). Compute diagnostics independently of the admitted host outcome and the selected run result.

`finished` can coexist with a failed file open or an integrity finding.
The observations and supported assessments state what the run establishes.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-envelope-data-select-finished"></a>1. Admitted finished outcome | `envelope.data.runner_result.normalized_outcome` = `"finished"` | sets `envelope.result.ok` to `true`, sets `envelope.result.exit_code` to `0`, sets `envelope.result.normalized_outcome` to `envelope.data.runner_result.normalized_outcome`, retains the records `envelope.data.runner_result`. |
| <a id="contract-envelope-data-select-other"></a>2. Other admitted outcome | `true` | sets `envelope.result.ok` to `false`, sets `envelope.result.exit_code` to `1`, sets `envelope.result.normalized_outcome` to `envelope.data.runner_result.normalized_outcome`, retains the records `envelope.data.runner_result`. |

<a id="contract-envelope-data-select-success_findings"></a>
###### Known gap: Success and findings

Whether result.ok and process exit should also reflect controller integrity
findings remains open. Present behavior selects success from the admitted
host outcome alone.

<a id="contract-envelope-data-classification"></a>
##### Controller classifications

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
##### Boundary precedence

[Controller](#contract-identity-definitions-controller) checks at received run data admission. Entry: cli run. Recipient: cli caller. Reports: run envelope. The first failed condition selects the consequence. Check request delivery error first, then client failure (capture admission, host frame admission and transport terminal), then decoded host producer identity and host capacity/profile-label admission. A delivery failure yields tool_error/exit 2; another refused boundary yields its classification/exit 1. Retain the available capture and structurally decoded reply, with runner_sandbox_diagnostics null. Eligible xpc_error can add independent fallback compilation.

Admission precedes evidence interpretation. The same held request supplies
client delivery and eligible ordinary fallback compilation; the helper
result describes its separate compiler invocation.

<a id="contract-envelope-data-failed_attempt"></a>
##### A finished run with a failed attempt

An admitted report says `finished` while a step says `open_failed`, rc -1
and errno 1. The controller emits result.ok true and exit 0, retains the
native failure and computes evidence findings independently.

**Support: [check read](#contract-support-grades) for [The controller envelope](#contract-envelope) and its descendants.** Constructed outcomes preserve nested native evidence and select success only for finished. A real fixture child exposes delivery refusal precedence. Rendering serializes the borrowed payload once. Context: Read completion/admission/frame code and the named constructed or fixture-child checks. Evidence limit: Check reading. The fixture child is a controlled protocol writer; native kernel execution is separate evidence. Source: [json_contract.rs](../controller/src/json_contract.rs): `render_envelope`; [run_flow.rs](../controller/src/run_flow.rs): `complete_execution`, `admit_reply`; [runner_client.rs](../controller/src/runner_client.rs): `pub fn failure`. Check: [json_contract.rs](../controller/src/json_contract.rs): `renderer_borrows_nonclone_typed_payload_and_serializes_it_once`; [run_flow.rs](../controller/src/run_flow.rs): `finished_run_preserves_successful_and_failed_attempts`, `typed_completion_preserves_native_failure_beside_finished_summary`; [runner_client.rs](../controller/src/runner_client.rs): `binary_reply_after_large_stdin_and_broken_pipe_preserves_delivery_precedence`.

<a id="contract-diagnostics"></a>
### Controller findings and assessments

The controller retains the admitted host reply and publishes its own
assessment under `data.runner_sandbox_diagnostics`. Each finding has the
scope of the check that produced it. The outer result, a worker's ending,
phase order, native operation and reporting-failure form have separate
conditions.

<a id="contract-diagnostics-execution"></a>
#### Execution diagnostics

Record `diagnostics` locations: `envelope.data.runner_sandbox_diagnostics`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-diagnostics-execution-process_disposition"></a>`process_disposition` | string; required | The controller's disposition projection. An ordinary worker supplies its validated lifecycle result. `no_worker` means this projection had no worker subprocess record to assess. Admitted vocabulary: closed; displayed list: exhaustive: `"no_worker"`, `"clean_exit"`, `"nonzero_exit"`, `"signaled"`, `"conflicting"`, `"unconfirmed"`, `"unrecognized"`, `"withheld"`, `"per_actor"`. |
| <a id="contract-diagnostics-execution-termination_cause"></a>`termination_cause` | string; null when absent | A controller attribution selected from the validated lifecycle chain. Actor-form top-level diagnostics begin with null because causes belong to the actor entries. |
| <a id="contract-diagnostics-execution-stop_reason"></a>`stop_reason` | string; null when absent | Supported ordinary-worker stop observation when its answer is one of `sentinel_deadline`, `done`, `child_reaped`, `wait_error`, `policy_write_error` or `policy_transfer_deadline`; otherwise null. Actor stop reasons belong to their actor entries. |
| <a id="contract-diagnostics-execution-disposition_integrity"></a>`disposition_integrity` | string; null when absent | `valid` means the applicable controller checks for this projection passed; `invalid` means they produced a finding. Null means there was no worker projection to validate. When at least one actor has a worker projection, actor aggregation is valid when every actor projection is valid or has null integrity; it becomes invalid when any actor projection is invalid. With no worker projections, aggregate integrity remains null. A host's supported conflict can accompany valid integrity: the controller has checked the conflict's own evidence. |
| <a id="contract-diagnostics-execution-disposition_issues"></a>`disposition_issues` | array of [Integrity finding](#contract-diagnostics-issue); required | Controller findings at this scope, followed or preceded according to the producing check order by copied host conflict records where applicable. Actor-local findings remain in the actor entry. |
| <a id="contract-diagnostics-execution-actors"></a>`actors` | array of [One actor's diagnostics](#contract-diagnostics-actor); omitted when absent | Present for `execution_form: "actors"`, in the host's actor order. Each entry is derived from that actor's subprocess and its actions selected through the phase plan. |

<a id="contract-diagnostics-execution-geometry"></a>
##### Decoded response collection bounds

[Controller](#contract-identity-definitions-controller) checks at decoded response-context admission after delivery, capture and public identity admission. Entry: cli run, runner verify. Recipient: caller, report reader. Reports: run envelope, runner verify. Binding `p`: entry in `reply.phases`. Binding `a`: entry in `reply.actors`. Applies when `reply` is present.

These bounds apply to every structurally decoded reply reaching this gate, including preparation and reporting-failure replies. Counts use the retained rows before semantic association.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-geometry-plan"></a>Phase and action tables | Requires ((if `reply.execution_form` = `"actors"`, then count of `reply.phases` ≤ `16 items` (`actor_phases`) ) and (if (`reply.execution_form` is absent or (`reply.execution_form` is present and `reply.execution_form` ≠ `"actors"`)), then count of `reply.phases` ≤ `8 items` (`phase_count`) ) and count of `reply.steps` ≤ `256 items` (`probe_steps`) and (if `reply.extension_events` is present, then count of `reply.extension_events` ≤ (`256 items` (`probe_steps`) − count of `reply.steps`)) and sum over `p` of count of `reply.phases[p].action_ids` ≤ `256 items` (`probe_steps`) ). |
| <a id="contract-diagnostics-execution-geometry-actors_transfers"></a>Actor and transfer tables | Requires ((if `reply.actors` is present, then count of `reply.actors` ≤ `8 items` (`actors`) ) and (if `reply.transfers` is present, then count of `reply.transfers` ≤ `64 items` (`actor_deliveries`) )). |
| <a id="contract-diagnostics-execution-geometry-resources"></a>Resource tables | Applies when `reply.resources` is present. Requires (count of `reply.resources.tokens` ≤ `32 items` (`actor_issues`) and count of `reply.resources.deliveries` ≤ `64 items` (`actor_deliveries`) and count of `reply.resources.handles` ≤ `64 items` (`actor_handles`) ). |
| <a id="contract-diagnostics-execution-geometry-equal_handles"></a>Equal-handle references | Binding `h`: entry in `reply.resources.handles`. For each `h`. Applies when `reply.resources` is present. Requires count of `reply.resources.handles[h].raw_equal_handles` ≤ (`64 items` (`actor_handles`) − `1`). |
| <a id="contract-diagnostics-execution-geometry-validator"></a>Validator collection tables | Binding `s`: entry in `reply.steps`. Association restriction for `s`: (`reply.steps[s].phase_id` = `reply.phases[p].phase_id` and `reply.steps[s].sandbox_check.missing_reason` ≠ `"query_not_requested"`). For each `p`. Applies when `reply.phases[p].validator_subprocess` is present. An absent missing_reason is included. |
| <a id="contract-diagnostics-execution-geometry-validator-expected"></a>Validator collection tables › Expected identifiers | Requires (if `reply.phases[p].validator_subprocess.expected_step_ids` is present, then count of `reply.phases[p].validator_subprocess.expected_step_ids` ≤ `256 items` (`probe_steps`) ). |
| <a id="contract-diagnostics-execution-geometry-validator-records"></a>Validator collection tables › Retained validator records | Applies when `reply.phases[p].validator_subprocess.records` is present. Requires ((if number of matching entries for `s` = `0`, then count of `reply.phases[p].validator_subprocess.records` ≤ `2 items` (`validator_records_per_query`) ) and (if number of matching entries for `s` > `0`, then count of `reply.phases[p].validator_subprocess.records` ≤ (number of matching entries for `s` × `2 items` (`validator_records_per_query`)))). |
| <a id="contract-diagnostics-execution-geometry-validator-issues"></a>Validator collection tables › Association issue allowance | Applies when `reply.phases[p].validator_subprocess.association_issues` is present. Requires ((if `reply.phases[p].validator_subprocess.records` is present, then count of `reply.phases[p].validator_subprocess.association_issues` ≤ ((number of matching entries for `s` + count of `reply.phases[p].validator_subprocess.records`) + `1`)) and (if `reply.phases[p].validator_subprocess.records` is absent, then count of `reply.phases[p].validator_subprocess.association_issues` ≤ (number of matching entries for `s` + `1`))). |
| <a id="contract-diagnostics-execution-geometry-equipment"></a>Equipment tables | Requires ((if `reply.equipment_bindings` is present, then count of `reply.equipment_bindings` ≤ `4 items` (`equipment_static_bindings`) ) and (if `reply.equipment_entitlements` is present, then count of `reply.equipment_entitlements` ≤ `12 items` (`equipment_entitlement_records`) )). |
| <a id="contract-diagnostics-execution-geometry-authority"></a>Authority scope tables | Applies when `reply.authority_setup` is present. Requires (count of `reply.authority_setup.workers` ≤ `8 items` (`actors`) and count of `reply.authority_setup.host.regions` ≤ `8 items` (`actors`) and count of `reply.authority_setup.host.custody` ≤ `32 items` (`actor_issues`) ). |
| <a id="contract-diagnostics-execution-geometry-host_scope"></a>Host run authority scope | Applies when `reply.authority_setup` is present. Requires (count of `reply.authority_setup.host.run.operations` ≤ `4` and count of `reply.authority_setup.host.run.ownership` ≤ `5` and (if `reply.authority_setup.host.run.integrity_errors` is present, then count of `reply.authority_setup.host.run.integrity_errors` ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-worker_scopes"></a>Worker authority scopes | Binding `w`: entry in `reply.authority_setup.workers`. For each `w`. Applies when `reply.authority_setup` is present. Requires (count of `reply.authority_setup.workers[w].operations` ≤ `16 items` (`authority_setup_cells`) and count of `reply.authority_setup.workers[w].ownership` ≤ `5` and (if `reply.authority_setup.workers[w].integrity_errors` is present, then count of `reply.authority_setup.workers[w].integrity_errors` ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-region_scopes"></a>Host region authority scopes | Binding `r`: entry in `reply.authority_setup.host.regions`. For each `r`. Applies when `reply.authority_setup` is present. Requires (count of `reply.authority_setup.host.regions[r].operations` ≤ `16 items` (`authority_setup_cells`) and count of `reply.authority_setup.host.regions[r].ownership` ≤ `5` and (if `reply.authority_setup.host.regions[r].integrity_errors` is present, then count of `reply.authority_setup.host.regions[r].integrity_errors` ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-custody_scopes"></a>Host custody authority scopes | Binding `c`: entry in `reply.authority_setup.host.custody`. For each `c`. Applies when `reply.authority_setup` is present. Requires (count of `reply.authority_setup.host.custody[c].operations` ≤ `4` and count of `reply.authority_setup.host.custody[c].ownership` ≤ `5` and (if `reply.authority_setup.host.custody[c].integrity_errors` is present, then count of `reply.authority_setup.host.custody[c].integrity_errors` ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-visits"></a>Actor visits | For each `a`. Applies when `reply.actors` is present. Requires count of `reply.actors[a].visits` ≤ `16 items` (`actor_phases`) . |
| <a id="contract-diagnostics-execution-geometry-actor_equipment"></a>Actor equipment observations | For each `a`. Applies when (`reply.actors` is present and `reply.actors[a].equipment` is present). Requires (count of `reply.actors[a].equipment.required_entitlements` ≤ `64 items` (`actor_required_entitlements`) and (if `reply.actors[a].equipment.missing_requirements` is present, then count of `reply.actors[a].equipment.missing_requirements` ≤ `64 items` (`actor_required_entitlements`) ) and count of `reply.actors[a].equipment.execution.native_observations` ≤ `4`). |
| <a id="contract-diagnostics-execution-geometry-ordinary_lifecycle"></a>Ordinary worker disposition | Binding `d`: entry in `reply.runner_subprocess.disposition.steps`. Binding `i`: entry in `reply.runner_subprocess.disposition.issues`. Applies when (`reply.runner_subprocess` is present and `reply.runner_subprocess.disposition` is present). |
| <a id="contract-diagnostics-execution-geometry-ordinary_lifecycle-rows"></a>Ordinary worker disposition › Disposition rows | Requires (count of `reply.runner_subprocess.disposition.steps` ≤ `256 items` (`probe_steps`) and count of `reply.runner_subprocess.disposition.issues` ≤ (`1` + (`2` × `256 items` (`probe_steps`)))). |
| <a id="contract-diagnostics-execution-geometry-ordinary_lifecycle-run_references"></a>Ordinary worker disposition › Run claim references | Requires ((if `reply.runner_subprocess.disposition.questions.final_status` is present, then (if `reply.runner_subprocess.disposition.questions.final_status.basis` is present, then count of `reply.runner_subprocess.disposition.questions.final_status.basis` ≤ `14`)) and (if `reply.runner_subprocess.disposition.questions.stop_reason` is present, then (if `reply.runner_subprocess.disposition.questions.stop_reason.basis` is present, then count of `reply.runner_subprocess.disposition.questions.stop_reason.basis` ≤ `14`)) and (if `reply.runner_subprocess.disposition.questions.cleanup_trigger` is present, then (if `reply.runner_subprocess.disposition.questions.cleanup_trigger.basis` is present, then count of `reply.runner_subprocess.disposition.questions.cleanup_trigger.basis` ≤ `14`)) and (if `reply.runner_subprocess.disposition.questions.grace_end` is present, then (if `reply.runner_subprocess.disposition.questions.grace_end.basis` is present, then count of `reply.runner_subprocess.disposition.questions.grace_end.basis` ≤ `14`)) and (if `reply.runner_subprocess.disposition.questions.kill_request_and_result` is present, then (if `reply.runner_subprocess.disposition.questions.kill_request_and_result.basis` is present, then count of `reply.runner_subprocess.disposition.questions.kill_request_and_result.basis` ≤ `14`)) and (if `reply.runner_subprocess.disposition.questions.collection_basis` is present, then (if `reply.runner_subprocess.disposition.questions.collection_basis.basis` is present, then count of `reply.runner_subprocess.disposition.questions.collection_basis.basis` ≤ `14`)) and (if `reply.runner_subprocess.disposition.questions.progress_association` is present, then (if `reply.runner_subprocess.disposition.questions.progress_association.basis` is present, then count of `reply.runner_subprocess.disposition.questions.progress_association.basis` ≤ `14`))). |
| <a id="contract-diagnostics-execution-geometry-ordinary_lifecycle-step_references"></a>Ordinary worker disposition › Step claim references | For each `d`. Requires ((if `reply.runner_subprocess.disposition.steps[d].questions.step_boundary_reached` is present, then (if `reply.runner_subprocess.disposition.steps[d].questions.step_boundary_reached.basis` is present, then count of `reply.runner_subprocess.disposition.steps[d].questions.step_boundary_reached.basis` ≤ `16`)) and (if `reply.runner_subprocess.disposition.steps[d].questions.step_result_published` is present, then (if `reply.runner_subprocess.disposition.steps[d].questions.step_result_published.basis` is present, then count of `reply.runner_subprocess.disposition.steps[d].questions.step_result_published.basis` ≤ `16`)) and (if `reply.runner_subprocess.disposition.steps[d].questions.step_requested_operation_applicability` is present, then (if `reply.runner_subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis` is present, then count of `reply.runner_subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis` ≤ `16`))). |
| <a id="contract-diagnostics-execution-geometry-ordinary_lifecycle-issue_references"></a>Ordinary worker disposition › Conflict observation references | For each `i`. Requires ((if `reply.runner_subprocess.disposition.issues[i].step_index` is present, then count of `reply.runner_subprocess.disposition.issues[i].observations` ≤ `16`) and (if `reply.runner_subprocess.disposition.issues[i].step_index` is absent, then count of `reply.runner_subprocess.disposition.issues[i].observations` ≤ `14`)). |
| <a id="contract-diagnostics-execution-geometry-actor_lifecycle"></a>Actor worker disposition | Binding `d`: entry in `reply.actors[a].subprocess.disposition.steps`. Binding `i`: entry in `reply.actors[a].subprocess.disposition.issues`. For each `a`. Applies when (`reply.actors` is present and `reply.actors[a].subprocess` is present and `reply.actors[a].subprocess.disposition` is present). |
| <a id="contract-diagnostics-execution-geometry-actor_lifecycle-rows"></a>Actor worker disposition › Disposition rows | Requires (count of `reply.actors[a].subprocess.disposition.steps` ≤ `256 items` (`probe_steps`) and count of `reply.actors[a].subprocess.disposition.issues` ≤ (`1` + (`2` × `256 items` (`probe_steps`)))). |
| <a id="contract-diagnostics-execution-geometry-actor_lifecycle-run_references"></a>Actor worker disposition › Run claim references | Requires ((if `reply.actors[a].subprocess.disposition.questions.final_status` is present, then (if `reply.actors[a].subprocess.disposition.questions.final_status.basis` is present, then count of `reply.actors[a].subprocess.disposition.questions.final_status.basis` ≤ `14`)) and (if `reply.actors[a].subprocess.disposition.questions.stop_reason` is present, then (if `reply.actors[a].subprocess.disposition.questions.stop_reason.basis` is present, then count of `reply.actors[a].subprocess.disposition.questions.stop_reason.basis` ≤ `14`)) and (if `reply.actors[a].subprocess.disposition.questions.cleanup_trigger` is present, then (if `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.basis` is present, then count of `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.basis` ≤ `14`)) and (if `reply.actors[a].subprocess.disposition.questions.grace_end` is present, then (if `reply.actors[a].subprocess.disposition.questions.grace_end.basis` is present, then count of `reply.actors[a].subprocess.disposition.questions.grace_end.basis` ≤ `14`)) and (if `reply.actors[a].subprocess.disposition.questions.kill_request_and_result` is present, then (if `reply.actors[a].subprocess.disposition.questions.kill_request_and_result.basis` is present, then count of `reply.actors[a].subprocess.disposition.questions.kill_request_and_result.basis` ≤ `14`)) and (if `reply.actors[a].subprocess.disposition.questions.collection_basis` is present, then (if `reply.actors[a].subprocess.disposition.questions.collection_basis.basis` is present, then count of `reply.actors[a].subprocess.disposition.questions.collection_basis.basis` ≤ `14`)) and (if `reply.actors[a].subprocess.disposition.questions.progress_association` is present, then (if `reply.actors[a].subprocess.disposition.questions.progress_association.basis` is present, then count of `reply.actors[a].subprocess.disposition.questions.progress_association.basis` ≤ `14`))). |
| <a id="contract-diagnostics-execution-geometry-actor_lifecycle-step_references"></a>Actor worker disposition › Step claim references | For each `a`, `d`. Requires ((if `reply.actors[a].subprocess.disposition.steps[d].questions.step_boundary_reached` is present, then (if `reply.actors[a].subprocess.disposition.steps[d].questions.step_boundary_reached.basis` is present, then count of `reply.actors[a].subprocess.disposition.steps[d].questions.step_boundary_reached.basis` ≤ `16`)) and (if `reply.actors[a].subprocess.disposition.steps[d].questions.step_result_published` is present, then (if `reply.actors[a].subprocess.disposition.steps[d].questions.step_result_published.basis` is present, then count of `reply.actors[a].subprocess.disposition.steps[d].questions.step_result_published.basis` ≤ `16`)) and (if `reply.actors[a].subprocess.disposition.steps[d].questions.step_requested_operation_applicability` is present, then (if `reply.actors[a].subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis` is present, then count of `reply.actors[a].subprocess.disposition.steps[d].questions.step_requested_operation_applicability.basis` ≤ `16`))). |
| <a id="contract-diagnostics-execution-geometry-actor_lifecycle-issue_references"></a>Actor worker disposition › Conflict observation references | For each `a`, `i`. Requires ((if `reply.actors[a].subprocess.disposition.issues[i].step_index` is present, then count of `reply.actors[a].subprocess.disposition.issues[i].observations` ≤ `16`) and (if `reply.actors[a].subprocess.disposition.issues[i].step_index` is absent, then count of `reply.actors[a].subprocess.disposition.issues[i].observations` ≤ `14`)). |
| <a id="contract-diagnostics-execution-geometry-step_copies"></a>Attempt lifecycle copies | Binding `s`: entry in `reply.steps`. For each `s`. Applies when `reply.steps[s].attempt.lifecycle` is present. Requires ((if `reply.steps[s].attempt.lifecycle.boundary.basis` is present, then count of `reply.steps[s].attempt.lifecycle.boundary.basis` ≤ `16`) and (if `reply.steps[s].attempt.lifecycle.result.basis` is present, then count of `reply.steps[s].attempt.lifecycle.result.basis` ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-extension_copies"></a>Extension lifecycle copies | Binding `e`: entry in `reply.extension_events`. For each `e`. Applies when (`reply.extension_events` is present and `reply.extension_events[e].lifecycle` is present). Requires ((if `reply.extension_events[e].lifecycle.boundary.basis` is present, then count of `reply.extension_events[e].lifecycle.boundary.basis` ≤ `16`) and (if `reply.extension_events[e].lifecycle.result.basis` is present, then count of `reply.extension_events[e].lifecycle.result.basis` ≤ `16`)). |
| <a id="contract-diagnostics-execution-geometry-failed"></a>Failed collection bound | On failure, sets `result.normalized_outcome` to `"malformed_runner_response"`, sets `result.ok` to `false`, sets `result.exit_code` to `1`, retains the records `reply`. |
| <a id="contract-diagnostics-execution-geometry-run_refusal"></a>Run assessment after refusal | Entry: cli run. On failure, sets `envelope.data.runner_sandbox_diagnostics` to `null`. |
| <a id="contract-diagnostics-execution-geometry-verify_refusal"></a>Verification completion after refusal | Entry: runner verify. On failure, sets `runner_verify.normalized_outcome` to `"malformed_runner_response"`, sets `runner_verify.runner_pid` to `null`. |

**Support: [check read](#contract-support-grades) for [Decoded response collection bounds](#contract-diagnostics-execution-geometry) and its descendants.** Collection bounds precede semantic joins and profile-context checking on run and verification admission; their refusal retains the decoded reply. Context: Read every geometry guard, both public call paths and the named constructed-control bodies. Evidence limit: The controls assert selected excess tables, reference lists, an accepted boundary and unchanged raw records. The remaining enumerated collection bounds and verification-specific projection are supported by their source branches. Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `claim_geometry`, `lifecycle_geometry`, `scope_geometry`, `reply_geometry`, `admission_problem`; [run_flow.rs](../controller/src/run_flow.rs): `admit_reply`; [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`. Check: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `typed_geometry_refuses_before_projection_and_retains_every_raw_record`, `typed_reference_geometry_is_checked_before_claims_and_admission_contexts`.

<a id="contract-diagnostics-execution-admit"></a>
##### Admit the response before assessment

[Controller](#contract-identity-definitions-controller) acts at client delivery, public reply identity and bounded response context. Entry: cli run. Recipient: caller, report reader. Reports: run envelope. Uses [Decoded response collection bounds](#contract-diagnostics-execution-geometry). Check request-delivery failure and client capture status, then exact reply identity, response geometry and compiled-profile context before execution diagnostics.

A missing or foreign producer identity follows its own transport/identity
refusal. The geometry guard bounds collections before semantic joins.
The compiled-profile guard checks its status and producer/stage context,
including actor captures and reporting-failure replies. These are
preconditions for the execution-assessment path described here.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-admit-context_refusal"></a>Decoded response-context refusal | sets `envelope.result.normalized_outcome` to `"malformed_runner_response"`, sets `envelope.result.ok` to `false`, sets `envelope.result.exit_code` to `1`, sets `envelope.data.runner_sandbox_diagnostics` to `null`, retains the records `reply`. The controller's response geometry or compiled-profile context check rejects a structurally decoded host reply. The controller returns the selected exit status with the decoded host reply still available in the envelope. |

<a id="contract-diagnostics-execution-project"></a>
##### Project one worker or aggregate actors

[Controller](#contract-identity-definitions-controller) acts at typed worker lifecycle interpretation after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Run the worker lifecycle validation against its native records, assigned actions and reporting form. Project a validated ending by the ending-mapping and stop-reason rules, then publish the validated host conflicts at that worker scope.

For the actor form, the controller computes each worker's projection
separately. It then sets the top-level disposition to `per_actor` when any
entry differs from `no_worker`, and aggregates the actor integrity values.

The two concrete scopes below bind each source subprocess to its own output
fields. Their lifecycle prerequisites are the actual helper check in each
invocation, including retained reporting-failure replies.

<a id="contract-diagnostics-execution-actor_rows"></a>
##### Actor projection rows

[Controller](#contract-identity-definitions-controller) reports at worker projection after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Binding `a`: entry in `reply.actors`. Binding `d`: entry in `envelope.data.runner_sandbox_diagnostics.actors`. Association restriction for `d`: `d` = `a`. Applies when `reply.execution_form` = `"actors"`.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-actor_rows-coverage"></a>Positional coverage | Requires (`envelope.data.runner_sandbox_diagnostics.actors` is present and (if `reply.actors` is present, then count of `envelope.data.runner_sandbox_diagnostics.actors` = count of `reply.actors`) and (if `reply.actors` is absent, then count of `envelope.data.runner_sandbox_diagnostics.actors` = `0`)). |
| <a id="contract-diagnostics-execution-actor_rows-identity"></a>Copied actor identity | For each `a`, `d`. Requires `envelope.data.runner_sandbox_diagnostics.actors[d].actor_id` = `reply.actors[a].actor_id`. Its label is copied even when that actor has no subprocess. Duplicate labels retain their separate positions and remain subject to the reply-wide association checks. |

<a id="contract-diagnostics-execution-ordinary"></a>
##### Ordinary worker projection

Actor: [Controller](#contract-identity-definitions-controller). Boundary: worker projection after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Applies when ((`reply.execution_form` is absent or (`reply.execution_form` is present and `reply.execution_form` ≠ `"actors"`)) and `reply.runner_subprocess` is present).

The source is `reply.runner_subprocess`; the output is the ordinary
execution diagnostic record, before reply-wide findings are appended.

<a id="contract-diagnostics-execution-ordinary-lifecycle_check"></a>
###### Worker lifecycle validation

[Controller](#contract-identity-definitions-controller) checks at one worker lifecycle validation before projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Applies when ((`reply.execution_form` is absent or (`reply.execution_form` is present and `reply.execution_form` ≠ `"actors"`)) and `reply.runner_subprocess` is present). For reply.runner_subprocess and its assigned actions under the carried reporting form, the controller's lifecycle validation returns no failed-check findings, before validated host conflicts are copied.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-ordinary-lifecycle_check-local_failure"></a>Local lifecycle findings | On failure, sets `envelope.data.runner_sandbox_diagnostics.process_disposition` to `"withheld"`, sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"unknown"`, sets `envelope.data.runner_sandbox_diagnostics.disposition_integrity` to `"invalid"`, sets `envelope.data.runner_sandbox_diagnostics.stop_reason` to `null`. |

<a id="contract-diagnostics-execution-ordinary-mapping"></a>
###### Ending mapping

[Controller](#contract-identity-definitions-controller) reports at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Select the first matching case in the listed order. Applies when (((`reply.execution_form` is absent or (`reply.execution_form` is present and `reply.execution_form` ≠ `"actors"`)) and `reply.runner_subprocess` is present) and (`reply.runner_subprocess.disposition` is present and `reply.runner_subprocess.disposition.questions.final_status` is present)). Requires [Worker lifecycle validation](#contract-diagnostics-execution-ordinary-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-execution-ordinary-mapping-clean"></a>1. Clean exit | (`reply.runner_subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.final_status.answer` = `"exit_code"` and `reply.runner_subprocess.disposition.questions.final_status.value` is present and `reply.runner_subprocess.disposition.questions.final_status.value` has alternative `"Integer"` and `"Integer"` alternative of `reply.runner_subprocess.disposition.questions.final_status.value` = `0`) | sets `envelope.data.runner_sandbox_diagnostics.process_disposition` to `"clean_exit"`, sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `null`. |
| <a id="contract-diagnostics-execution-ordinary-mapping-nonzero"></a>2. Other exit status | (`reply.runner_subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.final_status.answer` = `"exit_code"`) | sets `envelope.data.runner_sandbox_diagnostics.process_disposition` to `"nonzero_exit"`, sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"unknown"`. |
| <a id="contract-diagnostics-execution-ordinary-mapping-signal"></a>3. Signaled ending | (`reply.runner_subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.final_status.answer` = `"signal"`) | sets `envelope.data.runner_sandbox_diagnostics.process_disposition` to `"signaled"`, sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"unknown"`. |
| <a id="contract-diagnostics-execution-ordinary-mapping-conflict"></a>4. Supported conflict | `reply.runner_subprocess.disposition.questions.final_status.state` = `"conflicting"` | sets `envelope.data.runner_sandbox_diagnostics.process_disposition` to `"conflicting"`, sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"unknown"`. |
| <a id="contract-diagnostics-execution-ordinary-mapping-unconfirmed"></a>5. Unresolved or inapplicable ending | `reply.runner_subprocess.disposition.questions.final_status.state` is one of `"unresolved"`, `"inapplicable"` | sets `envelope.data.runner_sandbox_diagnostics.process_disposition` to `"unconfirmed"`, sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"unknown"`. |
| <a id="contract-diagnostics-execution-ordinary-mapping-other"></a>6. Other admitted ending | `true` | sets `envelope.data.runner_sandbox_diagnostics.process_disposition` to `"unrecognized"`, sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"unknown"`. Lifecycle validation has already checked the integer exit value and supported-conflict evidence. |

<a id="contract-diagnostics-execution-ordinary-stop"></a>
###### Supported stop reason

[Controller](#contract-identity-definitions-controller) reports at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Select the first matching case in the listed order. Applies when (((`reply.execution_form` is absent or (`reply.execution_form` is present and `reply.execution_form` ≠ `"actors"`)) and `reply.runner_subprocess` is present) and `reply.runner_subprocess.disposition` is present). Follows [Host-cleanup attribution](#contract-diagnostics-execution-ordinary-cause). Requires [Worker lifecycle validation](#contract-diagnostics-execution-ordinary-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-execution-ordinary-stop-recognized"></a>1. Recognized supported stop | (`reply.runner_subprocess.disposition.questions.stop_reason` is present and `reply.runner_subprocess.disposition.questions.stop_reason.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.stop_reason.answer` is present and `reply.runner_subprocess.disposition.questions.stop_reason.answer` is one of `"sentinel_deadline"`, `"done"`, `"child_reaped"`, `"wait_error"`, `"policy_write_error"`, `"policy_transfer_deadline"`) | sets `envelope.data.runner_sandbox_diagnostics.stop_reason` to `reply.runner_subprocess.disposition.questions.stop_reason.answer`, sets `envelope.data.runner_sandbox_diagnostics.disposition_integrity` to `"valid"`. |
| <a id="contract-diagnostics-execution-ordinary-stop-absent"></a>2. No supported recognized stop | `true` | sets `envelope.data.runner_sandbox_diagnostics.stop_reason` to `null`, sets `envelope.data.runner_sandbox_diagnostics.disposition_integrity` to `"valid"`. |

<a id="contract-diagnostics-execution-ordinary-cause_chain"></a>
###### Carried host-cleanup chain

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-ordinary-cause_chain-facts"></a>Required claims and native request result | Requires (`reply.runner_subprocess.disposition` is present and `reply.runner_subprocess.disposition.questions.final_status` is present and `reply.runner_subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.final_status.answer` = `"signal"` and `reply.runner_subprocess.disposition.questions.final_status.value` is present and `reply.runner_subprocess.disposition.questions.final_status.value` has alternative `"Integer"` and `reply.runner_subprocess.disposition.questions.cleanup_trigger` is present and `reply.runner_subprocess.disposition.questions.cleanup_trigger.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.grace_end` is present and `reply.runner_subprocess.disposition.questions.grace_end.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.grace_end.answer` = `"exhausted"` and `reply.runner_subprocess.disposition.questions.kill_request_and_result` is present and `reply.runner_subprocess.disposition.questions.kill_request_and_result.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.kill_request_and_result.answer` = `"requested"` and `reply.runner_subprocess.disposition.questions.kill_request_and_result.value` is present and `reply.runner_subprocess.disposition.questions.kill_request_and_result.value` has alternative `"Request"` and `variant(reply.runner_subprocess.disposition.questions.kill_request_and_result.value, 'Request').rc` = `0` and `variant(reply.runner_subprocess.disposition.questions.kill_request_and_result.value, 'Request').signal` = `"Integer"` alternative of `reply.runner_subprocess.disposition.questions.final_status.value`). |

<a id="contract-diagnostics-execution-ordinary-cause"></a>
###### Host-cleanup attribution

[Controller](#contract-identity-definitions-controller) acts at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Select the first matching case in the listed order. Applies when (((`reply.execution_form` is absent or (`reply.execution_form` is present and `reply.execution_form` ≠ `"actors"`)) and `reply.runner_subprocess` is present) and (`reply.runner_subprocess.disposition` is present and `reply.runner_subprocess.disposition.questions.final_status` is present and `reply.runner_subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.runner_subprocess.disposition.questions.final_status.answer` = `"signal"`)). Follows [Ending mapping](#contract-diagnostics-execution-ordinary-mapping). Requires [Worker lifecycle validation](#contract-diagnostics-execution-ordinary-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-execution-ordinary-cause-deadline_expiry"></a>1. Deadline expiry | ([Required claims and native request result](#contract-diagnostics-execution-ordinary-cause_chain-facts) and `reply.runner_subprocess.disposition.questions.cleanup_trigger.answer` = `"deadline_expiry"`) | sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"host_sentinel_deadline"`. |
| <a id="contract-diagnostics-execution-ordinary-cause-completion"></a>2. Completion | ([Required claims and native request result](#contract-diagnostics-execution-ordinary-cause_chain-facts) and `reply.runner_subprocess.disposition.questions.cleanup_trigger.answer` = `"completion"`) | sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"host_exit_grace_exhausted"`. |
| <a id="contract-diagnostics-execution-ordinary-cause-poll_wait_error"></a>3. Poll wait error | ([Required claims and native request result](#contract-diagnostics-execution-ordinary-cause_chain-facts) and `reply.runner_subprocess.disposition.questions.cleanup_trigger.answer` = `"poll_wait_error"`) | sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"host_cleanup_after_wait_error"`. |
| <a id="contract-diagnostics-execution-ordinary-cause-policy_transfer_error"></a>4. Policy transfer error | ([Required claims and native request result](#contract-diagnostics-execution-ordinary-cause_chain-facts) and `reply.runner_subprocess.disposition.questions.cleanup_trigger.answer` = `"policy_transfer_error"`) | sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"host_cleanup_after_transfer_error"`. |
| <a id="contract-diagnostics-execution-ordinary-cause-policy_transfer_timeout"></a>5. Policy transfer timeout | ([Required claims and native request result](#contract-diagnostics-execution-ordinary-cause_chain-facts) and `reply.runner_subprocess.disposition.questions.cleanup_trigger.answer` = `"policy_transfer_timeout"`) | sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"host_cleanup_after_transfer_timeout"`. |
| <a id="contract-diagnostics-execution-ordinary-cause-unknown"></a>6. No eligible recognized cleanup cause | `true` | sets `envelope.data.runner_sandbox_diagnostics.termination_cause` to `"unknown"`. The request result, exhausted grace and owned final status are independent observations in this chain. A successful signal request supplies its own request result; attribution requires the other carried claims and the preceding lifecycle validation. |

<a id="contract-diagnostics-execution-ordinary-host_conflicts"></a>
###### Copy validated host conflicts

[Controller](#contract-identity-definitions-controller) reports at worker projection after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Binding `i`: entry in `reply.runner_subprocess.disposition.issues`. Binding `j`: entry in `envelope.data.runner_sandbox_diagnostics.disposition_issues`. Association restriction for `j`: `j` = `i`. Applies when (((`reply.execution_form` is absent or (`reply.execution_form` is present and `reply.execution_form` ≠ `"actors"`)) and `reply.runner_subprocess` is present) and `reply.runner_subprocess.disposition` is present). Follows [Supported stop reason](#contract-diagnostics-execution-ordinary-stop). Requires [Worker lifecycle validation](#contract-diagnostics-execution-ordinary-lifecycle_check).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-execution-ordinary-host_conflicts-coverage"></a>Copy cardinality | Requires count of `envelope.data.runner_sandbox_diagnostics.disposition_issues` = count of `reply.runner_subprocess.disposition.issues`. |
| <a id="contract-diagnostics-execution-ordinary-host_conflicts-copy"></a>Copy each conflict's fields | For each `i`, `j`. sets `envelope.data.runner_sandbox_diagnostics.disposition_issues[j].kind` to `reply.runner_subprocess.disposition.issues[i].kind`, sets `envelope.data.runner_sandbox_diagnostics.disposition_issues[j].detail` to `reply.runner_subprocess.disposition.issues[i].detail`, sets `envelope.data.runner_sandbox_diagnostics.disposition_issues[j].subject_path` to `null`, sets `envelope.data.runner_sandbox_diagnostics.disposition_issues[j].rule` to `reply.runner_subprocess.disposition.issues[i].rule`, sets `envelope.data.runner_sandbox_diagnostics.disposition_issues[j].question` to `reply.runner_subprocess.disposition.issues[i].question`, sets `envelope.data.runner_sandbox_diagnostics.disposition_issues[j].step_index` to `reply.runner_subprocess.disposition.issues[i].step_index`, sets `envelope.data.runner_sandbox_diagnostics.disposition_issues[j].observations` to `reply.runner_subprocess.disposition.issues[i].observations`. |

<a id="contract-diagnostics-execution-reply_checks"></a>
##### Apply reply-wide findings

[Controller](#contract-identity-definitions-controller) acts at typed reply relationship checks after worker projections. Entry: cli run. Recipient: report reader. Reports: execution diagnostics. sets `diagnostics.process_disposition` to `"withheld"`, sets `diagnostics.termination_cause` to `"unknown"`, sets `diagnostics.disposition_integrity` to `"invalid"`, retains the records `reply`, keeps the assessment `diagnostics.actors`. Follows [Project one worker or aggregate actors](#contract-diagnostics-execution-project). One or more applicable reply-wide checks finds an invalid relationship.

The controller appends these findings to top-level `disposition_issues`.
It preserves the actor entries, an ordinary stop reason already derived,
and all host fields including step comparisons and claimed gate outcomes.
Those retained assertions can therefore appear beside the controller's
finding about them.

<a id="contract-diagnostics-execution-outer_result"></a>
##### Findings beside the completion result

Uses [Select the public result](#contract-envelope-data-select).

The envelope's result-selection rule governs completion. Individual failed
attempts and controller integrity findings remain visible beside that result.
A reply-wide withheld disposition can therefore accompany an outer successful
result.

<a id="contract-diagnostics-execution-families"></a>
##### Check families and applicability

Uses [Reply](#contract-identity-definitions-reply).

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
assembled records. Worker lifecycle projections still run independently,
with their comparison-limitation requirement waived when the comparison
has been removed by degradation. The retained host records remain
available for inspection at their own observation boundaries.

<a id="contract-diagnostics-execution-vocabulary"></a>
##### Closed claim states and open answers

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
###### Known gap: Unconfirmed vocabulary

For ordinary and actor workers, the controller maps both unresolved and inapplicable host final-status claims to unconfirmed while retaining the host claim. Whether to retain that merged controller vocabulary remains a maintainer decision.

<a id="contract-diagnostics-execution-scope_example"></a>
##### Scope example

A typed actor reply can carry a transfer naming an invalid source actor,
while another actor retains a valid clean-exit lifecycle. The controller
then publishes top-level `withheld` and an actor-evidence finding beside
that actor's `clean_exit`. If the admitted host summary is `finished`,
the outer result still reports `ok: true` and exit 0. The three values
answer the reply relationship, individual ending and host completion
questions respectively.

**Support: [check read](#contract-support-grades) for [Execution diagnostics](#contract-diagnostics-execution) and its descendants.** Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches. Context: Typed controller implementation and the named constructed tests were read. Evidence limit: Actor/native family entry points and the complete gate checks were read; their detailed operation predicates have separate source owners. The scope example combines separately inspected projection and outer-result controls. Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `execution_diagnostics`, `project`, `validate_lifecycle`, `admit_reply`; [run_flow.rs](../controller/src/run_flow.rs): `reply_contract`, `complete_execution`; [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `pub(super) fn validate`; [porcelain_native.rs](../controller/src/porcelain_native.rs): `pub(super) fn validate`. Check: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `typed_invalid_actor_account_keeps_independent_actor_endings`, `typed_degradation_never_certifies_surviving_comparison`, `typed_future_applicability_and_summary_remain_open_without_rewriting`; [run_flow.rs](../controller/src/run_flow.rs): `malformed_phase_claims_withhold_projection_and_preserve_raw_reply`, `execution_envelopes_preserve_raw_evidence_and_emit_only_execution_fields`.

<a id="contract-diagnostics-execution-reader_evidence"></a>
##### Reader judgments

Uses [Reader applicability](#contract-actor_evidence-actor-reader_scope).

Host reporting validation, controller semantic admission and canonical-JSON
consumption interpret the same typed records at their stated scopes. Worker
lifecycle assessment remains a separate judgment over the retained native
account and its projection. A reporting failure can retain observations that
produce a lifecycle finding while satisfying the degradation form.

**Support: [executed](#contract-support-grades) for [Reader judgments](#contract-diagnostics-execution-reader_evidence).** Preparation, identifier, membership, application precedence and degradation cases check their own expected judgments and retained consequences across the actual readers. Context: Whole canonical runner-unit case passed with zero recorded system sleep. Swift judgments over 142 typed frames were retained before encoding; exact-one Rust replay carried 143 frames including the real writer-cap fallback through envelopes, then independent Python readers completed all rows and seven JSON-only controls. Evidence limit: The corpus uses constructed records and independently expected interpretations. Eleven application-positive pairs, degradation admission, the exact contradictory-worker D1 finding and retained actor projections have separate assertions. JSON-only normalization has its own domain. Native occurrence of each constructed context has separate observation owners. Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `execution_diagnostics`; [consumer.py](../tests/lib/consumer.py): `_validate_reply`; [lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py): `check_actor_records`. Check: [run_flow.rs](../controller/src/run_flow.rs): `reader_definition_corpus_cross_readers`; [reader_corpus.py](../tests/suites/runner_unit/reader_corpus.py): `replay`. Run: `20261111T162345Z_3d6c7242`. Source snapshot: `reviewed-inputs sha256:af396aadf41ba79a0d072b62d9c3f4ff1df5b5fa30d6c4ff267c53e8437dd51d (b6ce6d26 dirty; replay identity correction)`. Case: `runner_unit/pwrunner_core_unit_executable`.

<a id="contract-diagnostics-execution-reader_evidence-classifier_generation"></a>
###### Known gap: Independent semantic classifiers

The host, controller and test readers retain independently written semantic classifiers checked against the stated definitions. Whether to generate those classifiers from one implementation remains a maintainer decision.

<a id="contract-diagnostics-actor"></a>
#### One actor's diagnostics

Record `actor_diagnostics`: `rust.ActorExecutionDiagnostics`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-diagnostics-actor-actor_id"></a>`actor_id` | string; null when absent | The host actor label copied into an actor-form diagnostic entry. The underlying projection helper begins with null; actor assembly supplies the label even when that actor has no subprocess record. |
| <a id="contract-diagnostics-actor-process_disposition"></a>`process_disposition` | string; required | The actor's own worker projection, chosen by the actor-worker mapping below after its lifecycle checks pass. Local findings yield `withheld`; a missing subprocess record yields `no_worker`. |
| <a id="contract-diagnostics-actor-termination_cause"></a>`termination_cause` | string; null when absent | Null for `clean_exit` or `no_worker`, otherwise `unknown` unless the validated host-cleanup chain supplies a named cause below. |
| <a id="contract-diagnostics-actor-stop_reason"></a>`stop_reason` | string; null when absent | The actor worker's supported stop reason from the recognized set listed for execution diagnostics. Null when no supported recognized answer was projected, including when local lifecycle validation failed. |
| <a id="contract-diagnostics-actor-disposition_integrity"></a>`disposition_integrity` | string; null when absent | `valid` when this worker's lifecycle checks passed, `invalid` when they produced a finding, and null when its subprocess record is absent. A reply-wide finding preserves this actor-local value. |
| <a id="contract-diagnostics-actor-disposition_issues"></a>`disposition_issues` | array of [Integrity finding](#contract-diagnostics-issue); required | Findings from this actor's lifecycle validation, or copied validated host conflicts after successful validation. Reply-wide actor-association or equipment findings appear in the execution-level issue list. |

<a id="contract-diagnostics-actor-projection"></a>
##### Actor worker projections

Actor: [Controller](#contract-identity-definitions-controller). Boundary: worker projection after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Binding `a`: entry in `reply.actors`. Binding `d`: entry in `envelope.data.runner_sandbox_diagnostics.actors`. Association restriction for `d`: `d` = `a`. For each `a`, `d`. Applies when (`reply.execution_form` = `"actors"` and `reply.actors` is present and `reply.actors[a].subprocess` is present).

This scope addresses each existing subprocess, including
its degraded reporting form, before later reply-wide findings.

<a id="contract-diagnostics-actor-projection-lifecycle_check"></a>
###### Worker lifecycle validation

[Controller](#contract-identity-definitions-controller) checks at one worker lifecycle validation before projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. For each `a`, `d`. Applies when (`reply.execution_form` = `"actors"` and `reply.actors` is present and `reply.actors[a].subprocess` is present). For reply.actors[a].subprocess and its assigned actions under the carried reporting form, the controller's lifecycle validation returns no failed-check findings, before validated host conflicts are copied.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-actor-projection-lifecycle_check-local_failure"></a>Local lifecycle findings | On failure, sets `envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition` to `"withheld"`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"unknown"`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_integrity` to `"invalid"`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].stop_reason` to `null`. |

<a id="contract-diagnostics-actor-projection-mapping"></a>
###### Ending mapping

[Controller](#contract-identity-definitions-controller) reports at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. For each `a`, `d`. Select the first matching case in the listed order. Applies when ((`reply.execution_form` = `"actors"` and `reply.actors` is present and `reply.actors[a].subprocess` is present) and (`reply.actors[a].subprocess.disposition` is present and `reply.actors[a].subprocess.disposition.questions.final_status` is present)). Requires [Worker lifecycle validation](#contract-diagnostics-actor-projection-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-actor-projection-mapping-clean"></a>1. Clean exit | (`reply.actors[a].subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.final_status.answer` = `"exit_code"` and `reply.actors[a].subprocess.disposition.questions.final_status.value` is present and `reply.actors[a].subprocess.disposition.questions.final_status.value` has alternative `"Integer"` and `"Integer"` alternative of `reply.actors[a].subprocess.disposition.questions.final_status.value` = `0`) | sets `envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition` to `"clean_exit"`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `null`. |
| <a id="contract-diagnostics-actor-projection-mapping-nonzero"></a>2. Other exit status | (`reply.actors[a].subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.final_status.answer` = `"exit_code"`) | sets `envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition` to `"nonzero_exit"`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"unknown"`. |
| <a id="contract-diagnostics-actor-projection-mapping-signal"></a>3. Signaled ending | (`reply.actors[a].subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.final_status.answer` = `"signal"`) | sets `envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition` to `"signaled"`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"unknown"`. |
| <a id="contract-diagnostics-actor-projection-mapping-conflict"></a>4. Supported conflict | `reply.actors[a].subprocess.disposition.questions.final_status.state` = `"conflicting"` | sets `envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition` to `"conflicting"`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"unknown"`. |
| <a id="contract-diagnostics-actor-projection-mapping-unconfirmed"></a>5. Unresolved or inapplicable ending | `reply.actors[a].subprocess.disposition.questions.final_status.state` is one of `"unresolved"`, `"inapplicable"` | sets `envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition` to `"unconfirmed"`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"unknown"`. |
| <a id="contract-diagnostics-actor-projection-mapping-other"></a>6. Other admitted ending | `true` | sets `envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition` to `"unrecognized"`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"unknown"`. Lifecycle validation has already checked the integer exit value and supported-conflict evidence. |

<a id="contract-diagnostics-actor-projection-stop"></a>
###### Supported stop reason

[Controller](#contract-identity-definitions-controller) reports at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. For each `a`, `d`. Select the first matching case in the listed order. Applies when ((`reply.execution_form` = `"actors"` and `reply.actors` is present and `reply.actors[a].subprocess` is present) and `reply.actors[a].subprocess.disposition` is present). Follows [Host-cleanup attribution](#contract-diagnostics-actor-projection-cause). Requires [Worker lifecycle validation](#contract-diagnostics-actor-projection-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-actor-projection-stop-recognized"></a>1. Recognized supported stop | (`reply.actors[a].subprocess.disposition.questions.stop_reason` is present and `reply.actors[a].subprocess.disposition.questions.stop_reason.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.stop_reason.answer` is present and `reply.actors[a].subprocess.disposition.questions.stop_reason.answer` is one of `"sentinel_deadline"`, `"done"`, `"child_reaped"`, `"wait_error"`, `"policy_write_error"`, `"policy_transfer_deadline"`) | sets `envelope.data.runner_sandbox_diagnostics.actors[d].stop_reason` to `reply.actors[a].subprocess.disposition.questions.stop_reason.answer`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_integrity` to `"valid"`. |
| <a id="contract-diagnostics-actor-projection-stop-absent"></a>2. No supported recognized stop | `true` | sets `envelope.data.runner_sandbox_diagnostics.actors[d].stop_reason` to `null`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_integrity` to `"valid"`. |

<a id="contract-diagnostics-actor-projection-cause_chain"></a>
###### Carried host-cleanup chain

For each `a`, `d`.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-actor-projection-cause_chain-facts"></a>Required claims and native request result | Requires (`reply.actors[a].subprocess.disposition` is present and `reply.actors[a].subprocess.disposition.questions.final_status` is present and `reply.actors[a].subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.final_status.answer` = `"signal"` and `reply.actors[a].subprocess.disposition.questions.final_status.value` is present and `reply.actors[a].subprocess.disposition.questions.final_status.value` has alternative `"Integer"` and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger` is present and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.grace_end` is present and `reply.actors[a].subprocess.disposition.questions.grace_end.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.grace_end.answer` = `"exhausted"` and `reply.actors[a].subprocess.disposition.questions.kill_request_and_result` is present and `reply.actors[a].subprocess.disposition.questions.kill_request_and_result.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.kill_request_and_result.answer` = `"requested"` and `reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value` is present and `reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value` has alternative `"Request"` and `variant(reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value, 'Request').rc` = `0` and `variant(reply.actors[a].subprocess.disposition.questions.kill_request_and_result.value, 'Request').signal` = `"Integer"` alternative of `reply.actors[a].subprocess.disposition.questions.final_status.value`). |

<a id="contract-diagnostics-actor-projection-cause"></a>
###### Host-cleanup attribution

[Controller](#contract-identity-definitions-controller) acts at validated worker ending projection. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. For each `a`, `d`. Select the first matching case in the listed order. Applies when ((`reply.execution_form` = `"actors"` and `reply.actors` is present and `reply.actors[a].subprocess` is present) and (`reply.actors[a].subprocess.disposition` is present and `reply.actors[a].subprocess.disposition.questions.final_status` is present and `reply.actors[a].subprocess.disposition.questions.final_status.state` = `"supported"` and `reply.actors[a].subprocess.disposition.questions.final_status.answer` = `"signal"`)). Follows [Ending mapping](#contract-diagnostics-actor-projection-mapping). Requires [Worker lifecycle validation](#contract-diagnostics-actor-projection-lifecycle_check).

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-diagnostics-actor-projection-cause-deadline_expiry"></a>1. Deadline expiry | ([Required claims and native request result](#contract-diagnostics-actor-projection-cause_chain-facts) and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer` = `"deadline_expiry"`) | sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"host_sentinel_deadline"`. |
| <a id="contract-diagnostics-actor-projection-cause-completion"></a>2. Completion | ([Required claims and native request result](#contract-diagnostics-actor-projection-cause_chain-facts) and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer` = `"completion"`) | sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"host_exit_grace_exhausted"`. |
| <a id="contract-diagnostics-actor-projection-cause-poll_wait_error"></a>3. Poll wait error | ([Required claims and native request result](#contract-diagnostics-actor-projection-cause_chain-facts) and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer` = `"poll_wait_error"`) | sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"host_cleanup_after_wait_error"`. |
| <a id="contract-diagnostics-actor-projection-cause-policy_transfer_error"></a>4. Policy transfer error | ([Required claims and native request result](#contract-diagnostics-actor-projection-cause_chain-facts) and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer` = `"policy_transfer_error"`) | sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"host_cleanup_after_transfer_error"`. |
| <a id="contract-diagnostics-actor-projection-cause-policy_transfer_timeout"></a>5. Policy transfer timeout | ([Required claims and native request result](#contract-diagnostics-actor-projection-cause_chain-facts) and `reply.actors[a].subprocess.disposition.questions.cleanup_trigger.answer` = `"policy_transfer_timeout"`) | sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"host_cleanup_after_transfer_timeout"`. |
| <a id="contract-diagnostics-actor-projection-cause-unknown"></a>6. No eligible recognized cleanup cause | `true` | sets `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause` to `"unknown"`. The request result, exhausted grace and owned final status are independent observations in this chain. A successful signal request supplies its own request result; attribution requires the other carried claims and the preceding lifecycle validation. |

<a id="contract-diagnostics-actor-projection-host_conflicts"></a>
###### Copy validated host conflicts

[Controller](#contract-identity-definitions-controller) reports at worker projection after response admission. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. Binding `i`: entry in `reply.actors[a].subprocess.disposition.issues`. Binding `j`: entry in `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues`. Association restriction for `j`: `j` = `i`. For each `a`, `d`. Applies when ((`reply.execution_form` = `"actors"` and `reply.actors` is present and `reply.actors[a].subprocess` is present) and `reply.actors[a].subprocess.disposition` is present). Follows [Supported stop reason](#contract-diagnostics-actor-projection-stop). Requires [Worker lifecycle validation](#contract-diagnostics-actor-projection-lifecycle_check).

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-diagnostics-actor-projection-host_conflicts-coverage"></a>Copy cardinality | Requires count of `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues` = count of `reply.actors[a].subprocess.disposition.issues`. |
| <a id="contract-diagnostics-actor-projection-host_conflicts-copy"></a>Copy each conflict's fields | For each `a`, `d`, `i`, `j`. sets `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].kind` to `reply.actors[a].subprocess.disposition.issues[i].kind`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].detail` to `reply.actors[a].subprocess.disposition.issues[i].detail`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].subject_path` to `null`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].rule` to `reply.actors[a].subprocess.disposition.issues[i].rule`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].question` to `reply.actors[a].subprocess.disposition.issues[i].question`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].step_index` to `reply.actors[a].subprocess.disposition.issues[i].step_index`, sets `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues[j].observations` to `reply.actors[a].subprocess.disposition.issues[i].observations`. |

**Support: [check read](#contract-support-grades) for [One actor's diagnostics](#contract-diagnostics-actor) and its descendants.** The mapping follows admitted final-status claims; named host causes require the supported cleanup/request/ending chain. Context: Full projection and lifecycle validation read; constructed cleanup and scope controls read. Evidence limit: The read cleanup test covers completion, deadline, wait-error and future-trigger cases. Transfer-error and transfer-timeout causes were read in source; no execution is credited. Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `project`, `validate_lifecycle`, `check_claim`. Check: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `typed_host_cleanup_cause_requires_all_independent_observations`, `typed_invalid_actor_account_keeps_independent_actor_endings`.

<a id="contract-diagnostics-issue"></a>
#### Integrity finding

Record `integrity_issue`: `rust.IntegrityIssue`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-diagnostics-issue-kind"></a>`kind` | string; required | Category supplied by the controller check or copied from a host conflict. Admitted vocabulary: open; displayed list: illustrative: `"missing_record"`, `"malformed_record"`, `"invalid_claim"`, `"unresolved_reference"`, `"phase_collection"`, `"ordering"`, `"policy_read"`, `"fresh_read"`, `"fresh_write"`, `"exec_observation"`, `"actor_evidence"`, `"reporting_failure"`, `"conflict"`. Unfamiliar values: An unfamiliar category remains a finding with its carried detail and scope; interpreting its specific condition requires that producer's definition. |
| <a id="contract-diagnostics-issue-detail"></a>`detail` | string; required | Human-readable explanation of the failed relationship or copied host conflict. Some controller details embed a step label or position; other actor and gate findings carry a general explanation. |
| <a id="contract-diagnostics-issue-subject_path"></a>`subject_path` | array of string; omitted when absent | Optional location of the inspected assertion within `data.runner_result`. The path is an ordered list of object keys and canonical zero-based decimal array positions. An empty path names the whole host result; a present null value remains an addressable target. For example, `["phases","2","termination_gate"]` names the third phase's carried gate, even when phase labels are duplicated or invalid. The controller supplies this field for owned-reap, phase-activation and termination-gate findings. Its association identifies the inspected record; projection and retention effects follow the producing check's scope. Other controller findings and copied host conflicts omit this field. |
| <a id="contract-diagnostics-issue-rule"></a>`rule` | string; omitted when absent | Host conflict rule copied from the retained disposition issue, such as D1 for a final-status conflict or D5 for the supported step conflicts. Controller-created findings currently omit this field. |
| <a id="contract-diagnostics-issue-question"></a>`question` | string; omitted when absent | Host question associated with a copied conflict. Controller-created findings currently omit this field even when a detail names the question. |
| <a id="contract-diagnostics-issue-step_index"></a>`step_index` | integer; omitted when absent | Worker-local step index copied from a host conflict when it has step scope. A copied run-level conflict and controller-created findings omit it. |
| <a id="contract-diagnostics-issue-observations"></a>`observations` | array of string; omitted when absent | Host observation-reference list copied from a validated conflict. Controller-created findings currently omit this field. |

<a id="contract-diagnostics-issue-retain"></a>
##### Retain observation and finding separately

[Controller](#contract-identity-definitions-controller) acts at integrity finding construction. Entry: cli run. Recipient: report reader. Reports: execution diagnostics, actor execution diagnostics. retains the records `reply`. Construct controller findings from the failed check's kind and detail, attaching subject_path for the owned-reap, phase-activation and termination-gate checks. Publish each finding and copied validated host conflict at its producing validation scope and in the producing order.

<a id="contract-diagnostics-issue-subject"></a>
##### Finding association and effect

Uses [subject_path](#contract-diagnostics-issue-subject_path), [Apply reply-wide findings](#contract-diagnostics-execution-reply_checks), [Project one worker or aggregate actors](#contract-diagnostics-execution-project).

A subject path associates the finding with the retained assertion that its
check inspected. A gate's source and dependent records remain operands of
that check. Reply-wide findings withhold the aggregate projection and retain
the separately computed actor projections. Worker-local findings affect
that worker's projection.

<a id="contract-diagnostics-issue-subject-withholding_scope"></a>
###### Known gap: Reply-wide withholding scope

A reply-wide finding withholds the aggregate projection and retains separately computed actor projections. Whether that finding should also withhold the actor conclusions remains a maintainer decision.

**Support: [executed](#contract-support-grades) for [Finding association and effect](#contract-diagnostics-issue-subject).** The constructed check retains both equal-label gates by positions 2 and 6, then checks owned-reap, activation and dependent-gate subjects with exact finding details/order and unchanged input records. Context: The named control passed in the completed zero-sleep unit/rust.unit case; its assertions inspect the findings returned by the production gate checker. Evidence limit: Execution covers the constructed owned-reap, activation and selected gate cases. Remaining predicate-location assignments retain their source support. Reference resolution and action-wide withholding choices have separate owners. Source: [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `fn gates`. Check: [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `gate_findings_locate_each_retained_assertion_by_position`. Run: `20261111T155411Z_29ef0802`. Source snapshot: `reviewed-inputs sha256:b5298841bceaea7af57843a0e2ab68de2dd2ed85edf21fd07b16ac91d5a8838e (b6ce6d26 dirty)`. Case: `unit/rust.unit`.

**Support: [executed](#contract-support-grades) for [Finding association and effect](#contract-diagnostics-issue-subject).** Forty-two retained controls cover optional/root/object/scalar/null targets, canonical array positions, malformed or unresolved paths, aggregate and actor issue locations, version gating and accumulated independent faults; 12 accept and 30 refuse. Context: The completed blackbox_e2e/checker_controls case passed with zero recorded system sleep. Each constructed input and its exact findings remain in consumer_subject_*.json and *.errors.json. Evidence limit: These controls establish reference reading and unchanged carried documents. Product predicate-to-subject selection is checked by the gate and full-reply corpus owners; reserved withholding policy remains explicit. Source: [consumer.py](../tests/lib/consumer.py): `_subject_path_problem`, `_validate_diagnostic_subjects`. Check: [checker_controls.py](../tests/suites/blackbox_e2e/checker_controls.py): `diagnostic_subject_controls`. Run: `20261111T155411Z_29ef0802`. Source snapshot: `reviewed-inputs sha256:b5298841bceaea7af57843a0e2ab68de2dd2ed85edf21fd07b16ac91d5a8838e (b6ce6d26 dirty)`. Case: `blackbox_e2e/checker_controls`.

**Support: [source read](#contract-support-grades) for [Integrity finding](#contract-diagnostics-issue) and its descendants.** Gate-family findings carry locations in the retained reply while preserving existing predicates, detail, order and projection scope. Copied host issues preserve their own metadata. Context: Constructors, projection copy, actor gate checks and native validator dispatch read. Evidence limit: Locations identify inspected retained records. Existing worker-local and reply-wide projection rules govern the findings independently. Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `IntegrityIssue`, `fn issue`, `for i in &sub.disposition`; [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `fn require`, `fn gates`; [porcelain_native.rs](../controller/src/porcelain_native.rs): `pub(super) fn validate`.

<a id="contract-dossier"></a>
### Specimen dossier

The controller carries `data.specimen` on every `kind: "run"` envelope. Its policy hashes identify the held parsed source selected for delivery; its import records identify controller file reads; its runner and binary records describe selection and on-disk observations made before invocation. Native compilation, application and execution have their own reports.

**Support: [check read](#contract-support-grades) for [Specimen dossier](#contract-dossier) and its descendants.** Declarations and collection branches establish field provenance, augmentation states, literal import closure and role-specific comparisons. Unit controls assert unavailable/partial states and comparisons against synthetic manifest baselines. Context: Read the cited producer/receiver declarations and branches; check citations identify the assertions read. Evidence limit: These read controls establish controller calculations and selected-file comparisons. A signed run with a changed request file, native compiler import parity and contemporaneous executing-image identity need separate observations. Source: [dossier.rs](../controller/src/dossier.rs): `Specimen`, `Imports`, `Binaries`; [run_flow.rs](../controller/src/run_flow.rs): `load_app_provenance`, `fn run(`, `actor_fallback_checks`; [sbpl_imports.rs](../controller/src/sbpl_imports.rs): `resolve_imports`, `compute_closure_hash`; [runner_select.rs](../controller/src/runner_select.rs): `RunnerProvenance`; [evidence.rs](../controller/src/evidence.rs): `verify_manifest`. Check: [dossier.rs](../controller/src/dossier.rs): `augmentation_records_hash_only_bytes_that_existed`, `import_scan_statuses_never_report_an_unscanned_closure_as_complete`, `builtin_run_hashes_nothing_and_reports_null_records`, `byoxpc_copies_are_compared_with_the_shipped_baselines`; [sbpl_imports.rs](../controller/src/sbpl_imports.rs): `closure_hash_excludes_unresolved_imports`, `closure_hash_is_order_invariant`.

<a id="contract-dossier-collection"></a>
#### Collection boundaries

<a id="contract-dossier-collection-held"></a>
##### Hold the selected request

[Controller](#contract-identity-definitions-controller) acts at request preparation before runner-client invocation and fallback compile. Entry: cli run. Recipient: cli caller, runner client, compiler helper. Reports: specimen dossier. Uses [Request](#contract-identity-definitions-request), [Byte observation](#contract-identity-definitions-bytes). A request has been parsed and controller policy changes have been resolved in memory. Serialize the held selected request once and use those bytes for client delivery and whole-request fallback compilation. Derive source hashes from its decoded UTF-8 sbpl_source string and retain the dossier even when later preparation or invocation fails.

The original path is a locator. JSON whitespace, escape spelling and subsequent edits to that file have no role in the held source hash. Actor fallback checks serialize the held resolved policy objects separately in request order. A later helper import scan can observe different import-file bytes because those files are independently opened.

<a id="contract-dossier-collection-scan"></a>
##### Scan literal imports

[Controller](#contract-identity-definitions-controller) acts at selected policy source and local import files before invocation. Entry: cli run. Recipient: cli caller. Reports: specimen dossier. The selected policy has string source within the <!-- span limits.helper_source.binary -->4 MiB<!-- /span --> source bound. Scan literal import forms, resolve absolute names as given and relative names under /System/Library/Sandbox/Profiles then /usr/share/sandbox, and record observed reads within depth 8 and count 64. Mark unresolved names, nonliteral forms, cycles, decoding failures and bound hits as incomplete.

Names retain their spelling, including a `.sb` suffix when supplied. Resolution deduplicates canonical paths and unresolved names. A file is opened once with nonblocking open, checked as regular through that descriptor, and read for both hashing and recursive scanning. Records sort by resolved path, then unresolved name. The closure hash is SHA-256 of selected source UTF-8 bytes, byte `0x1f`, then sorted `resolved_path + " " + sha256` lines joined with LF for records having both values. This identifies the scanned material even when the scan is incomplete.

<a id="contract-dossier-collection-compare"></a>
##### Compare selected files

[Controller](#contract-identity-definitions-controller) acts at selected runner/helper paths and embedded evidence manifest. Entry: cli run. Recipient: cli caller. Reports: specimen dossier. Uses [Classify the retained digest pair](#contract-dossier-binary-classify). Runner selection supplies paths and the app evidence manifest supplies role baselines where available. For a shipped path already described by its unique typed manifest entry, emit a null binary record. For another selected file, attempt its hash and retain the role baseline, available digest and independent error facts. After a dossier-only collection failure or hash mismatch, continue preparation and invocation subject to the separate selection and admission results.

A role baseline must be the unique entry at the expected path and kind with a 64-digit hexadecimal SHA-256. `match` means selected on-disk bytes matched that baseline at this read. A null role record refers to the shipped manifest description; ordinary collection does not rehash that shipped file. Worker/validator override strings must be absolute to be read; NUL-containing or over-<!-- span limits.test_override_path.value -->1,023<!-- /span -->-byte overrides are neither echoed nor opened.

<a id="contract-dossier-collection-held_example"></a>
##### Held-file example

If a caller changes the input JSON after the controller has parsed it, the client and fallback compiler still receive the controller’s held serialization. An import file changed between dossier collection and fallback compilation may produce different import observations. Compare the source hash and the separately reported closures at their named boundaries.

<a id="contract-dossier-collection-native_gap"></a>
##### Held input and file observation scope

The controller resolves and serializes the request once, then delivers that held text to the selected client and applicable helper calls. The dossier scanner and selected-file hashes describe their own reads. Literal import completeness belongs to the scanner convention; actor live equipment supplies its separate process association. Ordinary selected-file hashes remain file observations at collection time.

**Support: [check read](#contract-support-grades) for [Held input and file observation scope](#contract-dossier-collection-native_gap).** Held request delivery, import reads and selected-file comparison have distinct boundaries. Context: Static review of the cited producer and assertion branches. Evidence limit: The file-replacement control uses controlled client/helper callbacks and exact independent held inputs; selected-file hashes do not supply an ordinary executing-image association. Source: [run_flow.rs](../controller/src/run_flow.rs): `fn run(args:`; [sbpl_imports.rs](../controller/src/sbpl_imports.rs): `resolve_import_path`; [dossier.rs](../controller/src/dossier.rs): `fn compare`. Check: [run_flow.rs](../controller/src/run_flow.rs): `actor_fallback_uses_held_policy_objects_before_host_mode_admission`.

<a id="contract-dossier-specimen"></a>
#### Run dossier

Record `specimen`: `rust.Specimen`. Uses [Specimen](#contract-identity-definitions-specimen).

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-specimen-request_path"></a>`request_path` | string; null when absent | Request-file path reported by the controller when available; null when preparation did not establish one. |
| <a id="contract-dossier-specimen-policy"></a>`policy` | [Policy dossier](#contract-dossier-policy); required | Legacy-form policy dossier. In actor form, the actor entries carry their policy observations and this slot is not applicable. |
| <a id="contract-dossier-specimen-host"></a>`host` | [Controller host context](#contract-dossier-host); required | Controller-collected operating-system context; each failed sysctl read remains null. |
| <a id="contract-dossier-specimen-runner_provenance"></a>`runner_provenance` | [Selected runner provenance](#contract-dossier-runner); null when absent | Selected runner metadata when selection succeeded; null when no target was established. These facts precede invocation. |
| <a id="contract-dossier-specimen-app_provenance"></a>`app_provenance` | [App provenance](#contract-dossier-app); null when absent | Parsed app evidence-manifest provenance when available; null when its read or supported-schema parse failed. |
| <a id="contract-dossier-specimen-binaries"></a>`binaries` | [Selected binary observations](#contract-dossier-binaries); required | Role-by-role selected-file observations; the meaning of a null role is defined beside that role. |
| <a id="contract-dossier-specimen-actors"></a>`actors` | array of [Actor policy dossier](#contract-dossier-actor); omitted when absent | Actor-form policy dossiers in request order; omitted for the legacy form. |

<a id="contract-dossier-actor"></a>
#### Actor policy dossier

Record `actor`: `rust.ActorDossier`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-actor-actor_id"></a>`actor_id` | string; null when absent | Actor identifier copied if the request value is a string; otherwise null. This copy precedes actor admission. |
| <a id="contract-dossier-actor-mode"></a>`mode` | string; null when absent | Actor mode copied if it is a string; otherwise null. Unapplied actors receive a not-applicable policy dossier. |
| <a id="contract-dossier-actor-policy"></a>`policy` | [Policy dossier](#contract-dossier-policy); required | Policy augmentation and import observations for this actor. Missing or malformed policy objects produce not-applicable observations. |

<a id="contract-dossier-policy"></a>
#### Policy dossier

Record `policy`: `rust.PolicyDossier`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-policy-augmentation"></a>`augmentation` | [Augmentation observation](#contract-dossier-augmentation); required | Controller policy-selection outcome and hashes of source strings that existed at that boundary. |
| <a id="contract-dossier-policy-imports"></a>`imports` | [Import scan](#contract-dossier-imports); required | Literal import observations for the source selected for invocation, or the reason that scan was unavailable. |

<a id="contract-dossier-augmentation"></a>
#### Augmentation observation

Record `augmentation`: `rust.Augmentation`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-augmentation-status"></a>`status` | string; required | `not_requested` retains unchanged source hashes; `applied` records selected augmentation output; `failed` records refusal; `not_applicable` identifies a policy slot with no applicable source preparation. |
| <a id="contract-dossier-augmentation-applied"></a>`applied` | array of string; required | Applied augmentation names in controller order. |
| <a id="contract-dossier-augmentation-original_sha256"></a>`original_sha256` | string; null when absent | SHA-256 of pre-augmentation source string UTF-8 bytes when such a string existed; otherwise null. |
| <a id="contract-dossier-augmentation-applied_sha256"></a>`applied_sha256` | string; null when absent | SHA-256 of the selected source string, including unchanged source for not_requested. Null for failed/not_applicable and when no source string existed. |
| <a id="contract-dossier-augmentation-error"></a>`error` | string; null when absent | Augmentation failure text for failed; otherwise null. |

<a id="contract-dossier-augmentation-relationships"></a>
##### Augmentation record relationships

[Controller](#contract-identity-definitions-controller) reports at augmentation dossier projection. Entry: cli run. Recipient: report reader. Reports: specimen dossier.

Equal optional digests on not_requested include the case where no string source existed.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-dossier-augmentation-relationships-fields"></a>Produced field relationships | Requires ((if `augmentation.status` is one of `"not_requested"`, `"failed"`, `"not_applicable"`, then count of `augmentation.applied` = `0`) and (if `augmentation.status` is one of `"failed"`, `"not_applicable"`, then `augmentation.applied_sha256` is absent) and (if `augmentation.status` = `"not_requested"`, then `augmentation.original_sha256` = `augmentation.applied_sha256`) and (if `augmentation.status` = `"failed"`, then `augmentation.error` is present) and (if `augmentation.status` is one of `"not_requested"`, `"applied"`, `"not_applicable"`, then `augmentation.error` is absent)). |

**Support: [source read](#contract-support-grades) for [Augmentation record relationships](#contract-dossier-augmentation-relationships) and its descendants.** The four constructors preserve optional original/selected hashes and distinct failure/error states. Source: [dossier.rs](../controller/src/dossier.rs): `Augmentation`.

<a id="contract-dossier-imports"></a>
#### Import scan

Record `imports`: `rust.Imports`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-imports-status"></a>`status` | string; required | `complete` exhausted the literal closure without a reported problem; `incomplete` retained a partial/problematic scan; `failed` could not perform the scan; `not_applicable` skipped it because source preparation did not apply. |
| <a id="contract-dossier-imports-closure_sha256"></a>`closure_sha256` | string; null when absent | Digest of the selected source plus successfully read import path/hash pairs using the defined framing. |
| <a id="contract-dossier-imports-records"></a>`records` | array of [One import observation](#contract-dossier-import_record); required | Sorted observed import records, including unresolved and failed reads. Empty when there were no imports or no scan. |
| <a id="contract-dossier-imports-cycle"></a>`cycle` | array of string; null when absent | First detected cycle as an ordered name chain; null when no cycle was observed. |
| <a id="contract-dossier-imports-exceeded"></a>`exceeded` | string; null when absent | First reached traversal bound, `depth` or `count`; null when neither was recorded. |
| <a id="contract-dossier-imports-failure"></a>`failure` | string; null when absent | First collection problem, scan setup failure or reason for a not-applicable scan; null when none was recorded. |

<a id="contract-dossier-imports-scope"></a>
##### Retained scan scope

[Controller](#contract-identity-definitions-controller) reports at literal import dossier projection. Entry: cli run. Recipient: report reader. Reports: specimen dossier. Binding `r`: entry in `imports.records`. Association restriction for `r`: `imports.records[r].error` is present.

These are necessary conditions for complete. The scan also classifies nonliteral forms, an observation with no dedicated carried Boolean.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-dossier-imports-scope-fields"></a>Produced field relationships | Requires ((if `imports.status` is one of `"complete"`, `"incomplete"`, then `imports.closure_sha256` is present) and (if `imports.status` is one of `"failed"`, `"not_applicable"`, then (`imports.closure_sha256` is absent and count of `imports.records` = `0` and `imports.cycle` is absent and `imports.exceeded` is absent)) and (if `imports.status` = `"complete"`, then (`imports.cycle` is absent and `imports.exceeded` is absent and number of matching entries for `r` = `0`))). |

**Support: [source read](#contract-support-grades) for [Retained scan scope](#contract-dossier-imports-scope) and its descendants.** Performed complete/incomplete scans retain a closure; skipped/failed scans have no records. Complete scans have no carried cycle, exceeded bound or record errors. Source: [dossier.rs](../controller/src/dossier.rs): `Imports`.

<a id="contract-dossier-import_record"></a>
#### One import observation

Record `import_record`: `rust.ImportRecord`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-import_record-name"></a>`name` | string; required | Literal import name found in source, retained for successful resolution and unresolved-name diagnostics. |
| <a id="contract-dossier-import_record-resolved_path"></a>`resolved_path` | string; null when absent | Resolved path when lookup established one; null for an unresolved name. |
| <a id="contract-dossier-import_record-sha256"></a>`sha256` | string; null when absent | SHA-256 of bytes read from the opened regular file; null when that read failed or never occurred. |
| <a id="contract-dossier-import_record-size_bytes"></a>`size_bytes` | integer; null when absent | File size reported by metadata on the opened descriptor, when available. The hash identifies the bytes actually read. |
| <a id="contract-dossier-import_record-mtime_unix"></a>`mtime_unix` | integer; null when absent | Opened file’s available modification time in Unix seconds; null on unavailable conversion/read. |
| <a id="contract-dossier-import_record-error"></a>`error` | string; null when absent | Resolution, regular-file, read, text-decoding or traversal diagnostic for this entry; null when the entry was collected without such a problem. |

<a id="contract-dossier-host"></a>
#### Controller host context

Record `host`: `rust.HostFacts`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-host-macos_version"></a>`macos_version` | string; null when absent | String read from kern.osproductversion, or null when unavailable. |
| <a id="contract-dossier-host-macos_build"></a>`macos_build` | string; null when absent | String read from kern.osversion, or null when unavailable. |
| <a id="contract-dossier-host-kernel_release"></a>`kernel_release` | string; null when absent | String read from kern.osrelease, or null when unavailable. |
| <a id="contract-dossier-host-arch"></a>`arch` | string; null when absent | String read from hw.machine, or null when unavailable. This is the controller host’s hardware context. |

<a id="contract-dossier-app"></a>
#### App provenance

Record `app`: `rust.AppProvenance`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-app-evidence_manifest_path"></a>`evidence_manifest_path` | string; required | Path to the parsed embedded evidence manifest used by this run’s controller. |
| <a id="contract-dossier-app-evidence_verify"></a>`evidence_verify` | [Manifest hash verification](#contract-dossier-verification); null when absent | Manifest-declared hash verification when PW_VERIFY_EVIDENCE is exactly `1`; otherwise null. |

<a id="contract-dossier-binaries"></a>
#### Selected binary observations

Record `binaries`: `rust.Binaries`.

A null role records use of its shipped manifest description. If selection or a manifest baseline is unavailable, the controller emits an unavailable record with the facts it could retain. Actor equipment selection has its own records.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-binaries-service"></a>`service` | [One selected binary](#contract-dossier-binary); null when absent | Selected host executable comparison when it needs an individual record. Null when the shipped service is described by the manifest. |
| <a id="contract-dossier-binaries-worker"></a>`worker` | [One selected binary](#contract-dossier-binary); null when absent | Selected normal worker comparison, including an admitted observable override path. Null when the shipped worker is described by the manifest. |
| <a id="contract-dossier-binaries-validator"></a>`validator` | [One selected binary](#contract-dossier-binary); null when absent | Selected validator comparison, including an admitted observable override path. Null when the shipped validator is described by the manifest. |
| <a id="contract-dossier-binaries-unentitled_worker"></a>`unentitled_worker` | [One selected binary](#contract-dossier-binary); null when absent | Selected unentitled-worker comparison. Null when the shipped role is described by the manifest. |

<a id="contract-dossier-binary"></a>
#### One selected binary

Record `binary`: `rust.BinaryRecord`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-binary-path"></a>`path` | string; null when absent | Selected path when the controller may retain it; null when selection or safe override projection was unavailable. |
| <a id="contract-dossier-binary-actual_sha256"></a>`actual_sha256` | string; null when absent | Hash of selected on-disk bytes successfully read; retained independently of baseline availability. |
| <a id="contract-dossier-binary-baseline_sha256"></a>`baseline_sha256` | string; null when absent | Normalized SHA-256 from the shipped app manifest’s unique typed role entry; null if that baseline is unavailable. |
| <a id="contract-dossier-binary-verification"></a>`verification` | string; required | `match` or `mismatch` compares the two available hashes. `unavailable` means the controller could not establish that comparison. |
| <a id="contract-dossier-binary-reason"></a>`reason` | string; null when absent | Diagnostic explaining mismatch or unavailability; null for match. |

<a id="contract-dossier-binary-classify"></a>
##### Classify the retained digest pair

[Controller](#contract-identity-definitions-controller) reports at selected binary comparison record after collection. Entry: cli run. Recipient: report reader. Reports: specimen dossier. Select the first matching case in the listed order.

This rule applies to a constructed binary record. A null shipped-role record remains outside it; matching bytes at this read do not identify an executing image.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-dossier-binary-classify-match"></a>1. Equal available digests | (`binary.actual_sha256` is present and `binary.baseline_sha256` is present and `binary.actual_sha256` = `binary.baseline_sha256`) | sets `binary.verification` to `"match"`, sets `binary.reason` to `null`. |
| <a id="contract-dossier-binary-classify-mismatch"></a>2. Different available digests | (`binary.actual_sha256` is present and `binary.baseline_sha256` is present) | sets `binary.verification` to `"mismatch"`. |
| <a id="contract-dossier-binary-classify-unavailable"></a>3. Unavailable comparison operand | `true` | sets `binary.verification` to `"unavailable"`. |

**Support: [source read](#contract-support-grades) for [Classify the retained digest pair](#contract-dossier-binary-classify).** Available expected/actual digests select match or mismatch; missing operands retain unavailable with the collection diagnosis. Source: [dossier.rs](../controller/src/dossier.rs): `compare`.

<a id="contract-dossier-runner"></a>
#### Selected runner provenance

Record `runner`: `rust.RunnerProvenance`. Uses [Signature observation](#contract-installation-signature), [Entitlement observation](#contract-installation-entitlements).

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-runner-runner_kind"></a>`runner_kind` | string; required | Selected connection kind, standard or byoxpc. |
| <a id="contract-dossier-runner-runner_registry_id"></a>`runner_registry_id` | string; null when absent | Registry ID for a selected external runner; null for a built-in target. |
| <a id="contract-dossier-runner-runner_service_name"></a>`runner_service_name` | string; required | Selected XPC service name to which the controller intends to connect. |
| <a id="contract-dossier-runner-runner_bundle_id"></a>`runner_bundle_id` | string; null when absent | Selected bundle identity when available. |
| <a id="contract-dossier-runner-runner_bundle_path"></a>`runner_bundle_path` | string; null when absent | Selected bundle path when available; this is selection metadata. |
| <a id="contract-dossier-runner-runner_executable_path"></a>`runner_executable_path` | string; null when absent | Selected host executable path when available. |
| <a id="contract-dossier-runner-runner_signature"></a>`runner_signature` | [Signature observation](#contract-installation-signature); null when absent | Recorded external-host signature readback; null when no such metadata is supplied. |
| <a id="contract-dossier-runner-runner_entitlements"></a>`runner_entitlements` | [Entitlement observation](#contract-installation-entitlements); null when absent | Selected host entitlement metadata from the external registry or shipped evidence manifest when available. |
| <a id="contract-dossier-runner-runner_worker_signature"></a>`runner_worker_signature` | [Signature observation](#contract-installation-signature); null when absent | Recorded normal-worker signature readback for the selected target when available. |
| <a id="contract-dossier-runner-runner_worker_entitlements"></a>`runner_worker_entitlements` | [Entitlement observation](#contract-installation-entitlements); null when absent | Recorded normal-worker entitlement metadata when available. |
| <a id="contract-dossier-runner-runner_validator_signature"></a>`runner_validator_signature` | [Signature observation](#contract-installation-signature); null when absent | Recorded validator signature readback when available. |
| <a id="contract-dossier-runner-runner_validator_entitlements"></a>`runner_validator_entitlements` | [Entitlement observation](#contract-installation-entitlements); null when absent | Recorded validator entitlement metadata when available. |
| <a id="contract-dossier-runner-runner_unentitled_worker_signature"></a>`runner_unentitled_worker_signature` | [Signature observation](#contract-installation-signature); null when absent | Recorded unentitled-worker signature readback when available. |
| <a id="contract-dossier-runner-runner_unentitled_worker_entitlements"></a>`runner_unentitled_worker_entitlements` | [Entitlement observation](#contract-installation-entitlements); null when absent | Recorded unentitled-worker entitlement metadata when available. |

<a id="contract-dossier-verification"></a>
#### Manifest hash verification

Record `verification`: `rust.VerifyReport`.

Each comparison concerns a file read under the app root.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-verification-ok"></a>`ok` | boolean; required | True when every checked manifest entry was readable and matched its declared hash; false when mismatches contains an entry. |
| <a id="contract-dossier-verification-checked"></a>`checked` | integer; required | Number of manifest entries carrying a declared hash and considered by verification, including missing/unreadable files. |
| <a id="contract-dossier-verification-mismatches"></a>`mismatches` | array of [One verification failure](#contract-dossier-mismatch); required | Entries whose file was missing, unreadable or had different bytes. |
| <a id="contract-dossier-verification-manifest_path"></a>`manifest_path` | string; required | Manifest path attached to this verification. |
| <a id="contract-dossier-verification-schema_version"></a>`schema_version` | integer; required | Schema version read from the supported manifest. |
| <a id="contract-dossier-verification-notes"></a>`notes` | array of string; null when absent | Notes carried by that manifest, or null when absent. |

<a id="contract-dossier-mismatch"></a>
#### One verification failure

Record `mismatch`: `rust.VerifyMismatch`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-dossier-mismatch-id"></a>`id` | string; required | Manifest entry identifier for the failed comparison. |
| <a id="contract-dossier-mismatch-rel_path"></a>`rel_path` | string; required | Manifest-relative file path attempted under the app root. |
| <a id="contract-dossier-mismatch-expected_sha256"></a>`expected_sha256` | string; null when absent | Declared expected hash retained for this failure. |
| <a id="contract-dossier-mismatch-actual_sha256"></a>`actual_sha256` | string; null when absent | Hash actually read when available; null for missing/unreadable files. |
| <a id="contract-dossier-mismatch-error"></a>`error` | string; null when absent | Missing-file or read-error text when bytes were unavailable; null for a completed read whose actual hash differs from expected. |

<a id="contract-installation"></a>
## Managing runners

The controller manages external XPC services through a local registry and launchd. Registry state, on-disk signature observations, live service presence and a completed verification specimen establish different facts.

**Support: [check read](#contract-support-grades) for [Managing runners](#contract-installation) and its descendants.** Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation. Context: Read the cited producer/receiver declarations and branches; check citations identify the assertions read. Evidence limit: These read controls use registry files and supplied cleanup/signing observations. Live launchd, GUI-session access, signing, interruption recovery and opaque metadata through all CLI transitions need separately recorded execution evidence. Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_install`, `cmd_runner_verify`, `cmd_runner_validate`, `cmd_runner_reconcile`; [runner_manager.rs](../controller/src/runner_manager.rs): `RunnerRegistry`, `save_registry`, `install_record`, `remove_record`, `plist_ownership`, `service_ownership`, `read_back`. Check: [runner_manager.rs](../controller/src/runner_manager.rs): `install_failure_boundaries_preserve_observed_pending_state`, `legacy_metadata_survives_unrelated_writes_and_pending_cleanup`, `historical_flattened_cleanup_remains_readable_and_rewrites_with_nested_runner`, `registry_save_refuses_duplicate_known_metadata_before_publication`, `atomic_registry_replace_preserves_old_open_readers_and_failed_write`, `bootout_waits_out_launchd_teardown_within_the_budget`.

<a id="contract-installation-commands"></a>
### Command boundaries

<a id="contract-installation-commands-read"></a>
#### Read and select records

[Controller](#contract-identity-definitions-controller) acts at runner registry lookup. Entry: runner list, runner status, runner verify, runner remove, runner reconcile. Recipient: cli caller. Reports: runner registry, runner status, runner verify, runner remove, runner reconcile. The registry is readable with schema_version 1, or its path is absent. Use PW_RUNNER_REGISTRY when nonempty, otherwise HOME/Library/Application Support/PolicyWitness/runners.json. An absent file yields schema_version 1 with empty runners and pending_cleanup. For selector commands, prefer a supplied id and otherwise use service_name; an unmatched id remains a miss.

`runner list` returns the registry as `kind: "runner_registry"`. `runner status` returns the selected active record as `kind: "runner_status"`. Status and verify search `runners`; removal also resumes `pending_cleanup`. A miss returns that operation’s envelope kind, `result.normalized_outcome: "not_found"`, false `ok` and exit code 2. Unsupported registry schemas and malformed known fields refuse loading. Read-only commands can read the prior or replacement complete registry while a modifier holds its lock.

<a id="contract-installation-commands-publish"></a>
#### Publish a registry mutation

[Controller](#contract-identity-definitions-controller) acts at install, validate and remove registry transaction. Entry: runner install, runner validate, runner remove. Recipient: cli caller. Reports: runner registry. The command holds the stable sibling registry lock across its mutation and associated launchd actions. Serialize and read back the proposed registry, require lossless reserialization, write and sync a new mode-0600 file in the same directory, then atomically rename it over the registry. Refuse a busy/unavailable advisory lock or a readback that loses metadata.

The lock inode is retained across replacements. Operators must keep the lock file while any command may hold it. Unknown JSON members at the registry, runner, cleanup, ownership, signature and entitlement levels survive unrelated writes as opaque values. Known fields retain their meanings; opaque members supply no ownership observations.

<a id="contract-installation-commands-install"></a>
#### Install a selected service

[Controller](#contract-identity-definitions-controller) acts at external bundle validation, signing, registry and launchd. Entry: runner install. Recipient: cli caller, launchd. Reports: runner install, runner registry. Uses [Exact admission identity](#contract-identity-public-contract). The caller supplies an existing bundle directory; the kind defaults to byoxpc, and an explicit kind must be byoxpc. Scope defaults to user or may be explicitly system. Resolve the canonical bundle, require CFBundlePackageType XPC!, exact current PWContract, CFBundleIdentifier service identity and an existing Contents/MacOS/CFBundleExecutable. Reject conflicting active/recovery service, bundle or executable identities; verify the source seal and equipment inventory before optional signing.

An explicit service name must equal the bundle identifier. `--bundle-id` and `--executable` are refused; those identities come from the bundle. The installer refuses an existing target plist. With `--identity`, it signs the selected worker and host with the supplied entitlements, and the validator/unentitled worker without them, refreshing the sealed equipment inventory before sealing the host. Entitlements with `--allow-adhoc` can select ad-hoc signing; an ad-hoc result requires that flag. Required helpers must exist. The final recursive strict signature verification and reread of bundle identity precede registry installation.

<a id="contract-installation-commands-pending"></a>
#### Retain installation ownership

[Controller](#contract-identity-definitions-controller) acts at pending registry save before plist creation and bootstrap. Entry: runner install. Recipient: cli caller, launchd. Reports: runner install, runner registry. Bundle verification/signing and readbacks succeeded and the launchd plist has been prepared. Save a pending runner with its plist path, launchd domain, owner UID and plist hash before creating the plist or bootstrapping. Mark installed only after those requested operations and final registry save succeed; retain pending on later failure.

User scope writes HOME/Library/LaunchAgents and targets gui/<uid>, requiring access to that logged-in GUI domain. System scope writes /Library/LaunchDaemons and targets system, requiring the relevant privilege. The plist invokes the recorded executable with `--mach-service` and the service name, advertises that Mach service, sets RunAtLoad and a <!-- span limits.byoxpc_throttle_interval.value_unit -->1 second<!-- /span --> throttle, and defaults XPC_SERVICE_PATH to the bundle. `--env KEY=VALUE` requires a nonempty key; later occurrences replace earlier values. With `--skip-bootstrap`, successful plist creation completes installation; `loaded` remains a separate observation. Signing changes can precede the pending save.

<a id="contract-installation-commands-verify"></a>
#### Verify a selected service

[Controller](#contract-identity-definitions-controller), [Runner client](#contract-identity-definitions-client) acts at fixed verification specimen through reservation and execution. Entry: runner verify. Recipient: cli caller, runner host. Reports: runner verify. sets `request.contract` to [Contract](#contract-identity-build-contract), sets `request.specimen_id` to `"runner_verify"`, sets `request.run_kind` to `"runner_verify"`, sets `request.policy.format` to `"sbpl"`, sets `request.policy.sbpl_source` to `"(version 1)\n(allow default)\n"`, sets `request.probe_plan` to an empty array, withholds `request.actors`, withholds `request.phases`, withholds `request._test_overrides`. Uses [Select the verification operation result](#contract-installation-verify-select), [Request delivery failure](#contract-installation-verify-delivery_failure), [Decoded response collection bounds](#contract-diagnostics-execution-geometry). Lookup finds an external runner record. Send the held fixed verification request in a fresh invocation and apply ordinary delivery and reply admission. Under successful admission, copy a supported reply's PID and outcome; an absent reply selects runner_response_unavailable and no PID. A refused boundary selects its admission classification and no PID. The selected verification outcome and independent delivery error determine the operation result below.

The timeout defaults to <!-- span limits.runner_verify_wait.value_unit -->5,000 milliseconds<!-- /span --> and is clamped to at least one. An empty successful plan establishes the verification request’s application and completion. It supplies no per-operation prediction or attempt observations.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-installation-commands-verify-identity"></a>Selected record identity | Requires `runner_record.contract` = [Contract](#contract-identity-build-contract). |

<a id="contract-installation-commands-pending_verify"></a>
#### Pending verification

Ordinary specimen selection refuses a Pending installation. Explicit runner verify can address that recorded service after kind and contract checks, using the fixed verification request and retaining the recorded Pending state. Verification leaves the registry bytes unchanged.

**Support: [check read](#contract-support-grades) for [Pending verification](#contract-installation-commands-pending_verify).** Explicit verification selects by recorded identity and kind/contract, independently of ordinary Pending selection. Context: Static review of the cited producer and assertion branches. Evidence limit: The control uses an owned live current service with a constructed Pending registry state and snapshots the registry around both operations. Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`; [registry_recovery.py](../tests/suites/runner_byoxpc/opt_in/registry_recovery.py): `live-pending-verify`. Check: [registry_recovery.sh](../tests/suites/runner_byoxpc/opt_in/registry_recovery.sh): `registry_recovery`.

<a id="contract-installation-commands-validate"></a>
#### Refresh validation metadata

[Controller](#contract-identity-definitions-controller) acts at registered bundle and binary signature/inventory reads. Entry: runner validate. Recipient: cli caller. Reports: runner validate, runner registry. The controller loaded and locked the registry. Visit every record in runners, refresh available per-binary signature/entitlement observations, verify the bundle and equipment inventory, save the registry, and report missing/invalid counts and per-binary failures.

A missing host executable increments `missing`, marks the host signature invalid and records its entitlement error, then skips further verification for that row. A completed validate command reports `result.ok: true` and exit 0 even when missing/invalid is positive; inspect those fields. Pending cleanup records remain recovery records.

<a id="contract-installation-commands-entitlement_errors"></a>
#### Entitlement read errors and summary counts

A successful metadata read can retain an entitlement error alongside a valid signature without adding a validation failure. A failed read-back contributes a failure and unreadable signature metadata. Equipment validation applies its own entitlement requirements. The command counts invalid runners after combining the applicable failures; host and validator entitlement metadata errors alone retain their metadata scope.

**Support: [check read](#contract-support-grades) for [Entitlement read errors and summary counts](#contract-installation-commands-entitlement_errors).** Read-back failure and entitlement metadata are separate validation results. Context: Static review of the cited producer and assertion branches. Evidence limit: The injected seam checks per-role metadata and failure lists. Whole-command invalid-count consequences remain source-read alongside the separate equipment checks. Source: [runner_manager.rs](../controller/src/runner_manager.rs): `validate_record`; [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_validate`. Check: [runner_manager.rs](../controller/src/runner_manager.rs): `validation_keeps_entitlement_errors_distinct_from_failed_read_back`.

<a id="contract-installation-commands-reconcile"></a>
#### Reconcile observations

[Controller](#contract-identity-definitions-controller) acts at registry records, launchctl print and launchd plist directories. Entry: runner reconcile. Recipient: cli caller. Reports: runner reconcile. The registry loaded successfully. Report each active and cleanup record with current service/plist observations and separate ownership classifications, and report recognizable unregistered plist candidates plus inspection errors. Leave installation resources and registry records as observed.

Candidate discovery scans readable LaunchDaemons and the user LaunchAgents directory. A com.policywitness. label, executable filename PWRunner, or unreadable/unparsed plist with that filename prefix can identify a reporting candidate. Registered label/scope pairs are suppressed from candidates. Discovery establishes a candidate for inspection; cleanup authority requires the recorded identity and the independent ownership gates.

<a id="contract-installation-commands-remove"></a>
#### Remove an owned installation

[Controller](#contract-identity-definitions-controller) acts at durable cleanup transaction, launchctl bootout and plist unlink. Entry: runner remove. Recipient: cli caller, launchd. Reports: runner remove, runner registry. The requested active record or retained cleanup record exists. Move an active record to nested pending_cleanup and save before any launchd/plist action. Inspect service and plist ownership independently; boot out only an owned service unless skip_bootout, and unlink only an owned plist after an immediate ownership recheck. Retire cleanup only after observed service absence, plist absence, no warnings and successful registry publication.

After a successful bootout, re-read a still-present service every <!-- span limits.runner_remove_poll_interval.value_unit -->50 milliseconds<!-- /span --> for at most <!-- span limits.runner_remove_teardown_wait.value_unit -->1,000 milliseconds<!-- /span --> of nominal waiting; stop at absence or unknown. Final absence is separately observed. A changed/unreadable/unowned object, failed action or failed retirement publication retains recovery and warnings. A repeated remove continues the retained record from the durable registry, including after the plist has disappeared or the original diagnostic output is gone. `--skip-bootout` can remove an owned plist; retirement still requires observed service absence. A completed remove command reports `result.ok: true` and exit 0 even when cleanup remains retained.

<a id="contract-installation-commands-ownership"></a>
#### Classify cleanup ownership

[Controller](#contract-identity-definitions-controller) checks at recorded cleanup location and current resource observations. Entry: runner remove, runner reconcile. Recipient: cli caller. Reports: runner remove, runner reconcile. Uses [Classify the typed service observation](#contract-installation-service-classify). The recorded service name, user/scope/domain and paths pass location checks. Classify plist ownership from a regular file with matching Label, complete ProgramArguments, MachServices and XPC_SERVICE_PATH; recorded ownership additionally requires matching UID and plist hash.

Absent resources are classified ambiguous for ownership and retain their independently observed absent presence. Unknown presence produces unknown ownership. Recorded cleanup paths must be absolute, have no parent traversal, end in the expected service plist, and have an immediate parent named LaunchAgents for user scope or LaunchDaemons for system scope. The location check also requires the executable parent to equal the recorded bundle’s Contents/MacOS and refuses symlinked plist ancestors. The recorded ownership supplies the full parent path. Legacy records without ownership derive the conventional plist path and use the content checks.

**Support: [source read](#contract-support-grades) for [Classify cleanup ownership](#contract-installation-commands-ownership).** Location and resource ownership checks use the recorded path and complete associated identities. Evidence limit: Acceptance of a nonconventional full parent is source-supported; this owner supplies no native occurrence for that path. Source: [runner_manager.rs](../controller/src/runner_manager.rs): `record_location`, `plist_ownership`, `service_ownership`.

<a id="contract-installation-commands-recovery"></a>
#### Retained cleanup example

If bootout succeeds and plist removal succeeds but the final launchctl read is unknown, the command reports both action booleans true and cleanup_retained true. Keep the recorded bundle and any operator recovery state, inspect reconcile, and repeat removal until service/plist absence and registry retirement are observed.

<a id="contract-installation-registry"></a>
### Runner registry

Record `registry`: `rust.RunnerRegistry`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-registry-schema_version"></a>`schema_version` | integer; required | Supported registry layout version, currently 1. |
| <a id="contract-installation-registry-runners"></a>`runners` | array of [One runner record](#contract-installation-runner); required | Active installation records, including pending installations and installed records. |
| <a id="contract-installation-registry-pending_cleanup"></a>`pending_cleanup` | array of [Retained cleanup transaction](#contract-installation-pending_cleanup); required | Retained cleanup transactions, including nested runner identity and accumulated observations; empty by default when absent in a historical registry. |

<a id="contract-installation-runner"></a>
### One runner record

Record `runner`: `rust.RunnerRecord`.

Recorded signature, entitlement and inventory values describe their named reads; later execution has its own admission and live observations.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-runner-state"></a>`state` | string; required | `pending` means installation ownership was saved before completion; `installed` means the requested installation transaction completed. Missing historical state defaults to installed. |
| <a id="contract-installation-runner-ownership"></a>`ownership` | [Recorded cleanup ownership](#contract-installation-ownership); null when absent | Recorded plist identity and location used by cleanup, or null for a historical record without it. |
| <a id="contract-installation-runner-id"></a>`id` | string; required | Controller-generated registry identifier for this installation. |
| <a id="contract-installation-runner-service_name"></a>`service_name` | string; required | Mach service identity selected from the bundle identifier and used for lookup/launchd. |
| <a id="contract-installation-runner-bundle_path"></a>`bundle_path` | string; required | Canonical bundle location retained at installation. |
| <a id="contract-installation-runner-executable_path"></a>`executable_path` | string; required | Host executable path derived from the bundle metadata. |
| <a id="contract-installation-runner-bundle_id"></a>`bundle_id` | string; null when absent | Recorded CFBundleIdentifier, or null in a historical record without it. |
| <a id="contract-installation-runner-scope"></a>`scope` | string; required | `user` selects the current gui domain; `system` selects the system launchd domain. |
| <a id="contract-installation-runner-contract"></a>`contract` | string; omitted when empty | Public identity recorded from the verified bundle. Omitted if empty in a historical record; execution requires exact current identity. |
| <a id="contract-installation-runner-signature"></a>`signature` | [Signature observation](#contract-installation-signature); required | Host signature observation retained from installation or validation. |
| <a id="contract-installation-runner-entitlements"></a>`entitlements` | [Entitlement observation](#contract-installation-entitlements); required | Host entitlement readback and any read error. |
| <a id="contract-installation-runner-installed_at_unix_ms"></a>`installed_at_unix_ms` | integer; required | Controller wall-clock Unix milliseconds recorded while preparing installation, including a pending transaction. |
| <a id="contract-installation-runner-kind"></a>`kind` | string; omitted when absent | Known runner kind when recorded. Historical machme/debuggable deserialize to byoxpc; absent kind can be inferred by the selecting command. |
| <a id="contract-installation-runner-worker_signature"></a>`worker_signature` | [Signature observation](#contract-installation-signature); omitted when absent | Normal-worker signature observation when available; omitted in records without it. |
| <a id="contract-installation-runner-worker_entitlements"></a>`worker_entitlements` | [Entitlement observation](#contract-installation-entitlements); omitted when absent | Normal-worker entitlement readback when available. |
| <a id="contract-installation-runner-unentitled_worker_signature"></a>`unentitled_worker_signature` | [Signature observation](#contract-installation-signature); omitted when absent | Unentitled-worker signature observation when available. |
| <a id="contract-installation-runner-unentitled_worker_entitlements"></a>`unentitled_worker_entitlements` | [Entitlement observation](#contract-installation-entitlements); omitted when absent | Unentitled-worker entitlement readback when available. |
| <a id="contract-installation-runner-unentitled_worker_sha256"></a>`unentitled_worker_sha256` | string; omitted when absent | Unentitled-worker file hash retained at installation when available. |
| <a id="contract-installation-runner-worker_equipment_inventory"></a>`worker_equipment_inventory` | JSON value; omitted when absent | Post-signing sealed equipment snapshot retained as JSON. Current execution separately validates its on-disk inventory and role artifacts. |
| <a id="contract-installation-runner-source_worker_equipment_inventory"></a>`source_worker_equipment_inventory` | JSON value; omitted when absent | Verified source equipment snapshot retained before installer signing, as JSON. |
| <a id="contract-installation-runner-validator_signature"></a>`validator_signature` | [Signature observation](#contract-installation-signature); omitted when absent | Validator signature observation when available. |
| <a id="contract-installation-runner-validator_entitlements"></a>`validator_entitlements` | [Entitlement observation](#contract-installation-entitlements); omitted when absent | Validator entitlement readback when available. |
| <a id="contract-installation-runner-issuer_signature"></a>`issuer_signature` | [Signature observation](#contract-installation-signature); omitted when absent | Historical extension-issuer signature metadata when available. Current install leaves it absent. |
| <a id="contract-installation-runner-issuer_entitlements"></a>`issuer_entitlements` | [Entitlement observation](#contract-installation-entitlements); omitted when absent | Historical extension-issuer entitlement metadata when available. Current install leaves it absent. |

**Support: [check read](#contract-support-grades) for [kind](#contract-installation-runner-kind).** Registry normalization and durable cleanup preserve historical records and opaque metadata. Context: Static review of the cited producer and assertion branches. Evidence limit: The live workflow uses a current owned service and a constructed historical debuggable record; both retired aliases have separate offline controls. Source: [runner_manager.rs](../controller/src/runner_manager.rs): `pub enum RunnerKind`, `pub fn parse`; [registry_recovery.py](../tests/suites/runner_byoxpc/opt_in/registry_recovery.py): `historical-after-remove`. Check: [registry_recovery.sh](../tests/suites/runner_byoxpc/opt_in/registry_recovery.sh): `registry_recovery`; [runner_manager.rs](../controller/src/runner_manager.rs): `legacy_machme_kind_deserializes_as_byoxpc`, `legacy_debuggable_kind_deserializes_as_byoxpc`, `caller_facing_parse_rejects_legacy_aliases`.

<a id="contract-installation-ownership"></a>
### Recorded cleanup ownership

Record `ownership`: `rust.RunnerOwnership`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-ownership-plist_path"></a>`plist_path` | string; required | Absolute launchd plist path reserved by installation. |
| <a id="contract-installation-ownership-launchd_domain"></a>`launchd_domain` | string; required | Recorded gui/<uid> or system domain for that scope. |
| <a id="contract-installation-ownership-owner_uid"></a>`owner_uid` | integer; required | Installer’s numeric UID, compared with the acting user and observed plist owner for cleanup. |
| <a id="contract-installation-ownership-plist_sha256"></a>`plist_sha256` | string; required | Hash of the exact generated plist bytes, compared with the current file before cleanup. |

<a id="contract-installation-signature"></a>
### Signature observation

Record `signature`: `rust.RunnerSignature`.

Signature facts belong to the recorded file and read time. Preserve unknown members during registry recovery.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-signature-team_id"></a>`team_id` | string; null when absent | TeamIdentifier string read from codesign metadata when available; null when absent. |
| <a id="contract-installation-signature-identity"></a>`identity` | string; null when absent | First Authority line read from codesign metadata when available; null for unavailable authority. |
| <a id="contract-installation-signature-cdhash"></a>`cdhash` | string; null when absent | CDHash string read from codesign metadata when available. |
| <a id="contract-installation-signature-valid"></a>`valid` | boolean; required | Recorded success of the owning signature-read/verification path. During validation, host validity also requires recursive bundle verification; each helper requires its own binary verification. Failed metadata reads produce false. |
| <a id="contract-installation-signature-adhoc"></a>`adhoc` | boolean; required | Whether the read signature metadata identifies ad-hoc signing. |

<a id="contract-installation-entitlements"></a>
### Entitlement observation

Record `entitlements`: `rust.RunnerEntitlements`.

An empty keys/granted list with an error describes unavailable parsing. Boolean false, strings and integers do not enter granted.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-entitlements-raw_plist"></a>`raw_plist` | string; null when absent | Entitlement plist text returned by codesign, or null when none was emitted or the read was unavailable. |
| <a id="contract-installation-entitlements-keys"></a>`keys` | array of string; required | Sorted names of every key in a parsed entitlement dictionary, regardless of value. |
| <a id="contract-installation-entitlements-granted"></a>`granted` | array of string; required | Sorted keys whose values are JSON boolean true after plist conversion. Missing historical granted defaults to an empty list. |
| <a id="contract-installation-entitlements-error"></a>`error` | string; null when absent | Command, byte-cap or plist-conversion failure text when readback failed; null for a completed read. |

<a id="contract-installation-pending_cleanup"></a>
### Retained cleanup transaction

Record `pending_cleanup`: `rust.PendingCleanup`. Uses [Current cleanup observation](#contract-installation-cleanup_observation).

The reader accepts historical flattened cleanup records and writes the nested runner form. Unknown members at each level preserve their own nesting, including runner members named observations or cleanup_started_at_unix_ms.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-pending_cleanup-runner"></a>`runner` | [One runner record](#contract-installation-runner); required | Nested retained runner record, including unknown runner/ownership/signature/entitlement members. |
| <a id="contract-installation-pending_cleanup-cleanup_started_at_unix_ms"></a>`cleanup_started_at_unix_ms` | integer; required | Controller wall-clock Unix milliseconds when the active record entered cleanup. |
| <a id="contract-installation-pending_cleanup-observations"></a>`observations` | array of JSON value; required | Accumulated JSON observations. Current removal appends before/after records when location checks permit inspection; historical entries remain opaque. |

<a id="contract-installation-cleanup"></a>
### Removal result

Record `cleanup`: `rust.CleanupReport`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-cleanup-runner_id"></a>`runner_id` | string; required | Registry identifier of the cleanup target. |
| <a id="contract-installation-cleanup-service_name"></a>`service_name` | string; required | Recorded service name of that target. |
| <a id="contract-installation-cleanup-plist_path"></a>`plist_path` | string; required | Resolved cleanup path, recorded ownership path when resolution failed, or empty when neither was available. |
| <a id="contract-installation-cleanup-booted_out"></a>`booted_out` | boolean; required | True only when this removal’s launchctl bootout call succeeded. |
| <a id="contract-installation-cleanup-plist_removed"></a>`plist_removed` | boolean; required | True only when this removal’s unlink call succeeded. |
| <a id="contract-installation-cleanup-cleanup_retained"></a>`cleanup_retained` | boolean; required | True when verified absence/clean completion or publication of retirement was unavailable; continue recovery using the retained record. |
| <a id="contract-installation-cleanup-retained_record"></a>`retained_record` | [Retained cleanup transaction](#contract-installation-pending_cleanup); omitted when absent | Recovery snapshot when cleanup remains retained; omitted after retirement. |
| <a id="contract-installation-cleanup-warnings"></a>`warnings` | array of string; omitted when empty | Diagnostics for refused, failed, uncertain or unpersisted cleanup; omitted when empty. |

<a id="contract-installation-cleanup-retention"></a>
#### Retained recovery account

[Controller](#contract-identity-definitions-controller) reports at runner remove result after cleanup publication attempt. Entry: runner remove. Recipient: report reader. Reports: runner remove.

| Item | Requirement or consequence |
| --- | --- |
| <a id="contract-installation-cleanup-retention-fields"></a>Produced recovery fields | Requires (`cleanup.cleanup_retained` = `cleanup.retained_record` is present and (if (`cleanup.warnings` is present and count of `cleanup.warnings` > `0`), then `cleanup.cleanup_retained`)). |

**Support: [source read](#contract-support-grades) for [Retained recovery account](#contract-installation-cleanup-retention) and its descendants.** An incomplete or unpersisted cleanup retains its recovery snapshot; warnings prevent clean retirement. Source: [runner_manager.rs](../controller/src/runner_manager.rs): `remove_record`.

<a id="contract-installation-install"></a>
### Installation result

Record `install`: `rust.RunnerInstallData`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-install-state"></a>`state` | string; required | Installed state after the requested transaction and final registry save. |
| <a id="contract-installation-install-loaded"></a>`loaded` | [Observed service](#contract-installation-service); required | Independent launchctl service observation after installation. |
| <a id="contract-installation-install-runner"></a>`runner` | [One runner record](#contract-installation-runner); required | Complete recorded runner, including signature readbacks, inventories and cleanup ownership. |
| <a id="contract-installation-install-plist_path"></a>`plist_path` | string; required | Path where the installer published the launchd plist. |
| <a id="contract-installation-install-bootstrapped"></a>`bootstrapped` | boolean; required | True when this command requested and successfully completed bootstrap; false with skip-bootstrap. |

<a id="contract-installation-install-state_copy"></a>
#### Published installation state

[Controller](#contract-identity-definitions-controller) reports at runner install result projection. Entry: runner install. Recipient: report reader. Reports: runner install. sets `install.state` to `install.runner.state`.

**Support: [source read](#contract-support-grades) for [Published installation state](#contract-installation-install-state_copy).** RunnerInstallData copies the returned record state. Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_install`.

<a id="contract-installation-verify"></a>
### Verification result

Record `verify`: `rust.RunnerVerifyData`. Uses [Controller observation of the client process](#contract-transport-client).

This is the completion record for a selected registry entry after the client invocation returns its capture. An unmatched lookup uses RunnerNotFoundData with not_found and exit code 2. Earlier argument, registry, setup or invocation failures return without this record.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-verify-runner_client"></a>`runner_client` | [Controller observation of the client process](#contract-transport-client); null when absent | Client subprocess result, capture and delivery admission when available. |
| <a id="contract-installation-verify-runner_result"></a>`runner_result` | [Execution record](#contract-reply-record); null when absent | Decoded host result when available; its presence alone precedes the controller’s full reply admission. |
| <a id="contract-installation-verify-state"></a>`state` | string; required | Registry installation state read when selecting this verification target. |
| <a id="contract-installation-verify-runner_id"></a>`runner_id` | string; null when absent | Selected registry identifier when available. |
| <a id="contract-installation-verify-service_name"></a>`service_name` | string; required | Selected service to which verification was addressed. |
| <a id="contract-installation-verify-runner_pid"></a>`runner_pid` | integer; null when absent | PID projected only from an admitted host result. Its worker/host role follows the host result’s lifecycle. |
| <a id="contract-installation-verify-normalized_outcome"></a>`normalized_outcome` | string; required | Controller verification classification, also supplied in the envelope result. |

<a id="contract-installation-verify-delivery_failure"></a>
#### Request delivery failure

[Controller](#contract-identity-definitions-controller) reports at runner verify completion before reply interpretation. Entry: runner verify. Recipient: report reader. Reports: runner verify. Applies when (`verify.runner_client` is present and `verify.runner_client.request_delivery` is present and `verify.runner_client.request_delivery.error` is present). sets `result.ok` to `false`, sets `result.exit_code` to `2`, sets `result.normalized_outcome` to `"tool_error"`, sets `result.error` to `verify.runner_client.request_delivery.error`, sets `verify.normalized_outcome` to `"tool_error"`, sets `verify.runner_pid` to `null`, retains the records `verify.runner_client`, retains the records `verify.runner_result`.

**Support: [source read](#contract-support-grades) for [Request delivery failure](#contract-installation-verify-delivery_failure).** DeliveryFailed precedes capture/reply interpretation and preserves the returned observations. Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`.

<a id="contract-installation-verify-select"></a>
#### Select the verification operation result

[Controller](#contract-identity-definitions-controller) reports at verification operation result from its selected outcome and delivery observation. Entry: runner verify. Recipient: report reader. Reports: runner verify. Select the first matching case in the listed order.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-installation-verify-select-delivery"></a>1. Delivery error has precedence | (`verify.runner_client` is present and `verify.runner_client.request_delivery` is present and `verify.runner_client.request_delivery.error` is present) | sets `result.ok` to `false`, sets `result.exit_code` to `2`, sets `result.normalized_outcome` to `"tool_error"`. |
| <a id="contract-installation-verify-select-finished"></a>2. Selected finished outcome | `verify.normalized_outcome` = `"finished"` | sets `result.ok` to `true`, sets `result.exit_code` to `0`, sets `result.normalized_outcome` to `verify.normalized_outcome`. |
| <a id="contract-installation-verify-select-other"></a>3. Other selected outcome | `true` | sets `result.ok` to `false`, sets `result.exit_code` to `1`, sets `result.normalized_outcome` to `verify.normalized_outcome`. |

**Support: [source read](#contract-support-grades) for [Select the verification operation result](#contract-installation-verify-select).** The verification result uses delivery failure precedence and the already selected operation outcome; unsupported retained host fields do not supply a PID. Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`.

<a id="contract-installation-validate"></a>
### Validation result

Record `validate`: `rust.RunnerValidateData`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-validate-updated"></a>`updated` | integer; required | Number of runners visited and saved, including missing/invalid entries. |
| <a id="contract-installation-validate-missing"></a>`missing` | integer; required | Rows whose recorded host executable did not exist; further verification was skipped for those rows. |
| <a id="contract-installation-validate-invalid"></a>`invalid` | integer; required | Other rows with at least one bundle/binary verification, signature-metadata readback or inventory failure. |
| <a id="contract-installation-validate-failures"></a>`failures` | array of [One validation failure](#contract-installation-failure); required | Individual failure records, potentially multiple for one invalid runner. |

<a id="contract-installation-failure"></a>
### One validation failure

Record `failure`: `rust.ValidateFailure`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-failure-runner_id"></a>`runner_id` | string; required | Registry identifier of the row that failed this check. |
| <a id="contract-installation-failure-service_name"></a>`service_name` | string; required | Service name recorded in that row. |
| <a id="contract-installation-failure-binary"></a>`binary` | string; required | Failed role or check: bundle, host, worker, unentitled_worker, validator, issuer or equipment_inventory as applicable. |
| <a id="contract-installation-failure-error"></a>`error` | string; required | Failure text from the named verification/readback. |

<a id="contract-installation-not_found"></a>
### Unmatched lookup

Record `not_found`: `rust.RunnerNotFoundData`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-not_found-requested_id"></a>`requested_id` | string; omitted when absent | Supplied ID, omitted when none was supplied. |
| <a id="contract-installation-not_found-requested_service_name"></a>`requested_service_name` | string; omitted when absent | Supplied service name, omitted when none was supplied. |

<a id="contract-installation-service"></a>
### Observed service

Record `service`: `rust.ServiceObservation`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-service-presence"></a>`presence` | string; required | `present` for successful launchctl print, `absent` only for its specific missing-service diagnostic naming the requested service, otherwise `unknown`. |
| <a id="contract-installation-service-executable_path"></a>`executable_path` | string; null when absent | The unique program = line from a successful launchctl print; null when missing, ambiguous or unavailable. |
| <a id="contract-installation-service-error"></a>`error` | string; null when absent | Inspection diagnostic for unknown presence; null for recognized present/absent. |

<a id="contract-installation-service-ownership"></a>
#### Service ownership assessment

Ownership of this observed service relative to the selected runner_record. Reconciliation and cleanup copy this assessment beside the observation.

<a id="contract-installation-service-classify"></a>
#### Classify the typed service observation

[Controller](#contract-identity-definitions-controller) reports at service observation for the selected runner record after location resolution. Entry: runner reconcile, runner remove. Recipient: report reader. Reports: runner reconcile, runner remove. Select the first matching case in the listed order. Uses [Service ownership assessment](#contract-installation-service-ownership).

A raw reconciliation row containing only unknown presence after location failure has no typed ownership association.

| Case | When | Consequence |
| --- | --- | --- |
| <a id="contract-installation-service-classify-unknown"></a>1. Unknown presence | `service.presence` = `"unknown"` | sets [Service ownership assessment](#contract-installation-service-ownership) to `"unknown"`. |
| <a id="contract-installation-service-classify-absent"></a>2. Absent service | `service.presence` = `"absent"` | sets [Service ownership assessment](#contract-installation-service-ownership) to `"ambiguous"`. |
| <a id="contract-installation-service-classify-owned"></a>3. Matching executable | (`service.presence` = `"present"` and `service.executable_path` is present and `service.executable_path` = `runner_record.executable_path`) | sets [Service ownership assessment](#contract-installation-service-ownership) to `"owned"`. |
| <a id="contract-installation-service-classify-unowned"></a>4. Different executable | (`service.presence` = `"present"` and `service.executable_path` is present) | sets [Service ownership assessment](#contract-installation-service-ownership) to `"unowned"`. |
| <a id="contract-installation-service-classify-ambiguous"></a>5. No usable executable | (`service.presence` = `"present"` and `service.executable_path` is absent) | sets [Service ownership assessment](#contract-installation-service-ownership) to `"ambiguous"`. |

**Support: [source read](#contract-support-grades) for [Classify the typed service observation](#contract-installation-service-classify).** The typed presence and observed/recorded executable paths determine service ownership; plist ownership is independent. Source: [runner_manager.rs](../controller/src/runner_manager.rs): `service_ownership`.

<a id="contract-installation-plist"></a>
### Observed plist

Record `plist`: `rust.PlistObservation`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-plist-presence"></a>`presence` | string; required | `absent` for a missing path; `present` for observed metadata, including invalid content; `unknown` for inspection/read failure that prevents a reliable observation. |
| <a id="contract-installation-plist-config"></a>`config` | JSON value; null when absent | Parsed plist JSON dictionary/value when conversion succeeded; otherwise null. |
| <a id="contract-installation-plist-sha256"></a>`sha256` | string; null when absent | Hash of bytes read from the plist when available, including bytes whose plist conversion failed. |
| <a id="contract-installation-plist-owner_uid"></a>`owner_uid` | integer; null when absent | Filesystem owner UID read from symlink metadata when available. |
| <a id="contract-installation-plist-regular"></a>`regular` | boolean; required | True when the observed path metadata identifies a regular file; false for another type or unavailable metadata. |
| <a id="contract-installation-plist-error"></a>`error` | string; null when absent | Metadata, regular-file, read or conversion diagnostic when present; otherwise null. |

<a id="contract-installation-reconcile"></a>
### Reconciliation result

Record `reconcile`: `RunnerReconcileData`.

The result reports successful reconciliation execution even when individual inspections remain unknown.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-reconcile-registry_path"></a>`registry_path` | string; required | Registry path used for this read. |
| <a id="contract-installation-reconcile-records"></a>`records` | array of [One recorded reconciliation](#contract-installation-reconcile_record); required | Recorded runners and retained cleanup entries, each with current observations or a location error. |
| <a id="contract-installation-reconcile-candidates"></a>`candidates` | array of [Unregistered candidate](#contract-installation-candidate); required | Recognizable unregistered launchd plist candidates from readable directories. |
| <a id="contract-installation-reconcile-inspection_errors"></a>`inspection_errors` | array of [Reconciliation inspection error](#contract-installation-inspection_error); required | Directory, path or plist inspection failures encountered during candidate discovery. |

<a id="contract-installation-reconcile_record"></a>
### One recorded reconciliation

Record `reconcile_record`: `RunnerReconcileRecord`. Uses [Observed service](#contract-installation-service), [Observed plist](#contract-installation-plist).

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-reconcile_record-recorded_state"></a>`recorded_state` | string; required | pending, installed or pending_cleanup identifies its registry location/state. |
| <a id="contract-installation-reconcile_record-runner"></a>`runner` | [One runner record](#contract-installation-runner); required | Recorded runner retained without substituting live observations. |
| <a id="contract-installation-reconcile_record-service"></a>`service` | JSON value; required | Full ServiceObservation after valid location resolution; otherwise only {"presence":"unknown"}. |
| <a id="contract-installation-reconcile_record-plist"></a>`plist` | JSON value; required | Full PlistObservation after valid location resolution; otherwise only {"presence":"unknown"}. |
| <a id="contract-installation-reconcile_record-plist_path"></a>`plist_path` | string; omitted when absent | Resolved plist location; omitted on location error. |
| <a id="contract-installation-reconcile_record-launchd_domain"></a>`launchd_domain` | string; omitted when absent | Resolved launchd domain; omitted on location error. |
| <a id="contract-installation-reconcile_record-service_ownership"></a>`service_ownership` | string; omitted when absent | Owned, unowned, ambiguous or unknown classification serialized in lowercase; omitted on location error. |
| <a id="contract-installation-reconcile_record-plist_ownership"></a>`plist_ownership` | string; omitted when absent | Independent plist ownership classification; omitted on location error. |
| <a id="contract-installation-reconcile_record-ownership"></a>`ownership` | string; omitted when absent | unknown on location error; omitted after successful location resolution. |
| <a id="contract-installation-reconcile_record-error"></a>`error` | string; omitted when absent | Location-check refusal text; omitted after successful location resolution. |

<a id="contract-installation-candidate"></a>
### Unregistered candidate

Record `candidate`: `RunnerReconcileCandidate`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-candidate-recorded_state"></a>`recorded_state` | string; required | unregistered for each candidate. |
| <a id="contract-installation-candidate-scope"></a>`scope` | string; required | user or system according to the directory scanned. |
| <a id="contract-installation-candidate-service_name"></a>`service_name` | string; null when absent | Parsed Label, or null if unavailable. |
| <a id="contract-installation-candidate-executable_path"></a>`executable_path` | string; null when absent | Parsed ProgramArguments[0], falling back to Program, or null. |
| <a id="contract-installation-candidate-plist_path"></a>`plist_path` | string; required | Candidate path observed during directory enumeration. |
| <a id="contract-installation-candidate-service"></a>`service` | [Observed service](#contract-installation-service); null when absent | Service observation when label/domain permitted lookup; otherwise null. |
| <a id="contract-installation-candidate-plist"></a>`plist` | [Observed plist](#contract-installation-plist); required | Current candidate file observation. |
| <a id="contract-installation-candidate-ownership"></a>`ownership` | string; required | unknown when config is unavailable, ambiguous when label/executable is missing, otherwise unowned. |

<a id="contract-installation-inspection_error"></a>
### Reconciliation inspection error

Record `inspection_error`: `RunnerReconcileInspectionError`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-inspection_error-path"></a>`path` | string; omitted when absent | Directory or plist path involved; omitted when the user LaunchAgents path could not be determined. |
| <a id="contract-installation-inspection_error-presence"></a>`presence` | string; required | unknown for each inspection error. |
| <a id="contract-installation-inspection_error-error"></a>`error` | string; required | Inspection or path-resolution error text. |

<a id="contract-installation-cleanup_observation"></a>
### Current cleanup observation

Record `cleanup_observation`: `RunnerCleanupObservation`.

This describes the current producer’s appended values within the open observations history.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-cleanup_observation-phase"></a>`phase` | string; required | before or after identifies its position around attempted actions. |
| <a id="contract-installation-cleanup_observation-service"></a>`service` | [Observed service](#contract-installation-service); required | Independent service observation at this phase. |
| <a id="contract-installation-cleanup_observation-plist"></a>`plist` | [Observed plist](#contract-installation-plist); required | Independent plist observation at this phase. |
| <a id="contract-installation-cleanup_observation-service_ownership"></a>`service_ownership` | string; omitted when absent | Ownership classification supporting the before decision; omitted after actions. |
| <a id="contract-installation-cleanup_observation-plist_ownership"></a>`plist_ownership` | string; omitted when absent | Independent before-action plist ownership classification; omitted after actions. |
| <a id="contract-installation-cleanup_observation-teardown_wait"></a>`teardown_wait` | [Service teardown polling](#contract-installation-cleanup_wait); omitted when absent | Polling receipt on after records; omitted before actions. |

<a id="contract-installation-cleanup_wait"></a>
### Service teardown polling

Record `cleanup_wait`: `RunnerCleanupWait`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-installation-cleanup_wait-reads"></a>`reads` | integer; required | Number of service observations, including the initial post-action read. |
| <a id="contract-installation-cleanup_wait-waited_ms"></a>`waited_ms` | integer; required | Sum of nominal requested polling intervals; zero when no wait occurred. |
| <a id="contract-installation-cleanup_wait-poll_interval_ms"></a>`poll_interval_ms` | integer; required | Current requested polling interval, <!-- span limits.runner_remove_poll_interval.value_unit -->50 milliseconds<!-- /span -->. |
| <a id="contract-installation-cleanup_wait-budget_ms"></a>`budget_ms` | integer; required | Current nominal waiting bound, <!-- span limits.runner_remove_teardown_wait.value_unit -->1,000 milliseconds<!-- /span -->. |

**Support: [source read](#contract-support-grades) for [Managing runners](#contract-installation) and its descendants.** The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations. Context: Read the json! construction sites and their enclosing branches. Evidence limit: Field-node coverage and source review establish the declared shape; a dedicated independent output mutation control for every dynamic branch remains open. Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_reconcile`; [runner_manager.rs](../controller/src/runner_manager.rs): `remove_record`, `service_after_bootout`.

## Reporting the version

<a id="contract-identity-version"></a>
### Version reporting

Record `version_data`: `VersionData`.

| Field | JSON type and presence | Meaning |
| --- | --- | --- |
| <a id="contract-identity-version-contract"></a>`contract` | string; required | The controller's public identity, also carried in the same envelope's `build.contract`. Uses [Exact admission identity](#contract-identity-public-contract). |

<a id="contract-identity-version-emit"></a>
#### Version command

[Controller](#contract-identity-definitions-controller) reports at CLI version dispatch. Entry: version. Recipient: cli caller. Reports: version. sets `version_data.contract` to [Contract](#contract-identity-build-contract), sets `result.ok` to `true`, sets `result.exit_code` to `0`, sets `result.rc` to `null`, sets `result.normalized_outcome` to `null`, sets `result.errno` to `null`, sets `result.error` to `null`, sets `result.stderr` to `null`, sets `result.stdout` to `null`. Uses [Envelope](#contract-identity-definitions-envelope), [Contract](#contract-identity-build-contract). The first command argument is --version or version. Emit the version envelope with its version payload and current build context; return process exit 0 after successful rendering, or 2 when envelope rendering returns an error.

Version dispatch reports the compiled context without loading a specimen or
starting the runner client. Remaining arguments are ignored.
`generated_at_unix_ms` is the producer's current
wall-clock time in milliseconds since the Unix epoch; the shared serializer
uses zero if its system time precedes that epoch.

**Support: [check read](#contract-support-grades) for [Version command](#contract-identity-version-emit).** --version succeeds, emits kind version and result.ok true, supplies populated packaged build fields, and reports candidate-plist identity in data and build. Context: Read dispatch and serializer branches; read integration test invoking the selected controller binary and independently extracting its app plist identity. Evidence limit: Check read without execution. Alias version, trailing arguments, exact null result fields and rendering-error exit are source-established here; the cited check exercises --version success. Source: [cli.rs](../controller/src/cli.rs): `pub fn run`; [json_contract.rs](../controller/src/json_contract.rs): `JsonResult`, `now_unix_ms`. Check: [cli_contract.rs](../controller/integration/cli_contract.rs): `version_flag_reports_build_stamp_and_contract`.

**Support: [check read](#contract-support-grades) for [Version command](#contract-identity-version-emit).** Version dispatch precedes other command parsing. Context: Static review of the cited producer and assertion branches. Evidence limit: The argument matrix compares kind, build, result and data while allowing each invocation its own timestamp. Source: [cli.rs](../controller/src/cli.rs): `pub fn run`. Check: [cli_contract.rs](../controller/integration/cli_contract.rs): `version_dispatch_uses_the_first_argument`.

## Evidence support

<a id="contract-support-grades"></a>
**Support grades.** **source read:** The named source was inspected for the stated assertions. **check read:** The named source and check assertions were inspected in the stated context. **executed:** The named run exercised the stated assertions with its identified source or build.

## Rule applicability

Each linked rule states its boundary, entry, recipients, reports and conditions.

| Acting components | Rules |
| --- | --- |
| [Build pipeline](#contract-identity-definitions-build_pipeline) | [Build derivation](#contract-identity-public-derive) |
| [Contract generator](#contract-identity-definitions-contract_generator) | [Deriving the history table](#contract-identity-surfaces-derive) |
| [Controller](#contract-identity-definitions-controller) | [Version command](#contract-identity-version-emit); [Hold and deliver the selected request](#contract-request-specimen-hold); [Selector precedence](#contract-request-options-precedence); [Selection and augmentation failure order](#contract-request-options-failure_order); [Resolve and append](#contract-policy-augments-resolve); [Resolve actor policies in request order](#contract-policy-augments-actors); [Fallback eligibility and classification](#contract-policy-fallback-classify); [Controller pre-invocation refusal](#contract-refusals-controller-consequence); [Admit client and host observations](#contract-transport-client-admit); [Checking a carried gate](#contract-actor_evidence-gate-check); [The controller checks carried labels](#contract-profile-receipt-labels); [Select the public result](#contract-envelope-data-select); [Boundary precedence](#contract-envelope-data-admit); [Decoded response collection bounds](#contract-diagnostics-execution-geometry); [Admit the response before assessment](#contract-diagnostics-execution-admit); [Project one worker or aggregate actors](#contract-diagnostics-execution-project); [Actor projection rows](#contract-diagnostics-execution-actor_rows); [Worker lifecycle validation](#contract-diagnostics-execution-ordinary-lifecycle_check); [Ending mapping](#contract-diagnostics-execution-ordinary-mapping); [Supported stop reason](#contract-diagnostics-execution-ordinary-stop); [Host-cleanup attribution](#contract-diagnostics-execution-ordinary-cause); [Copy validated host conflicts](#contract-diagnostics-execution-ordinary-host_conflicts); [Apply reply-wide findings](#contract-diagnostics-execution-reply_checks); [Worker lifecycle validation](#contract-diagnostics-actor-projection-lifecycle_check); [Ending mapping](#contract-diagnostics-actor-projection-mapping); [Supported stop reason](#contract-diagnostics-actor-projection-stop); [Host-cleanup attribution](#contract-diagnostics-actor-projection-cause); [Copy validated host conflicts](#contract-diagnostics-actor-projection-host_conflicts); [Retain observation and finding separately](#contract-diagnostics-issue-retain); [Hold the selected request](#contract-dossier-collection-held); [Scan literal imports](#contract-dossier-collection-scan); [Compare selected files](#contract-dossier-collection-compare); [Augmentation record relationships](#contract-dossier-augmentation-relationships); [Retained scan scope](#contract-dossier-imports-scope); [Classify the retained digest pair](#contract-dossier-binary-classify); [Read and select records](#contract-installation-commands-read); [Publish a registry mutation](#contract-installation-commands-publish); [Install a selected service](#contract-installation-commands-install); [Retain installation ownership](#contract-installation-commands-pending); [Refresh validation metadata](#contract-installation-commands-validate); [Reconcile observations](#contract-installation-commands-reconcile); [Remove an owned installation](#contract-installation-commands-remove); [Classify cleanup ownership](#contract-installation-commands-ownership); [Retained recovery account](#contract-installation-cleanup-retention); [Published installation state](#contract-installation-install-state_copy); [Request delivery failure](#contract-installation-verify-delivery_failure); [Select the verification operation result](#contract-installation-verify-select); [Classify the typed service observation](#contract-installation-service-classify) |
| [Runner host](#contract-identity-definitions-host) | [Admission order and effects](#contract-request-specimen-admission); [Null and omission](#contract-request-specimen-nulls); [Bounded strings and action counts](#contract-request-specimen-capacity); [Admission and eligibility](#contract-probes-query-eligibility); [Extension participant restriction](#contract-probes-attempt-extension_exec); [Normalize actors before launch](#contract-actors-actor-normalize); [Collect, release and advance](#contract-actors-phase-order); [Validate and evaluate the dependency](#contract-actors-after_termination-gate); [Admit the declared dependency](#contract-actors-after_termination-declaration); [Action identity](#contract-actors-action-identity); [Resolve references and ownership](#contract-extensions-operation-references); [Bound the declared resource plan](#contract-extensions-operation-capacity); [Exclude exec in participating actors](#contract-extensions-operation-exec); [Observe the source answer](#contract-extensions-custody-source_answer); [Project a published issue result](#contract-extensions-event-issue_projection); [Delivered receipt prerequisites](#contract-extensions-transfer-delivered_receipt); [Source acknowledgement association](#contract-extensions-transfer-source_association); [Refuse at the first reached boundary](#contract-refusals-request-select); [Stop children and preserve safe metadata](#contract-refusals-request-consequence); [Sanitize every echoed field](#contract-refusals-admission-echo); [Admit a connection](#contract-transport-authorization-connection); [Host line admission](#contract-wire-validator-read); [Assemble execution evidence](#contract-reply-record-assemble); [Publish a report or fallback](#contract-reply-failure-publish); [Assemble the two channels](#contract-steps-assessment-assembly); [Establish query order](#contract-steps-assessment-order); [Classify an observation](#contract-steps-assessment-observe); [Add host path observations](#contract-steps-assessment-paths); [Resolve the final process status](#contract-lifecycle-worker-final_status); [Copy the polling stop](#contract-lifecycle-worker-resolve_stop_reason); [Copy the final collection basis](#contract-lifecycle-worker-resolve_collection_basis); [Resolving lifecycle claims](#contract-lifecycle-disposition-resolve); [Project ordinary canonical step claims](#contract-lifecycle-disposition-ordinary_projection); [Project actor canonical step claims](#contract-lifecycle-disposition-actor_projection); [Joining accepted validator records](#contract-lifecycle-validator-associate); [Count expected and unexpected associations](#contract-lifecycle-validator-cardinality); [Actor ownership and reporting scope](#contract-actor_evidence-actor-account); [Associated authority rows](#contract-actor_evidence-application-authority_association); [Application classification](#contract-actor_evidence-application-classify); [Prepared actor phase and gate records](#contract-actor_evidence-gate-prepared_association); [Evaluating and applying the dependency](#contract-actor_evidence-gate-evaluate); [Binding before launch](#contract-equipment-binding-bind); [Packaged bound-row equalities](#contract-equipment-binding-bound_values); [Associating the owned process](#contract-equipment-execution-inspect); [Inspection result eligibility](#contract-equipment-execution-eligibility); [Preparation refusal contents](#contract-equipment-preparation_failure-retain); [Acquiring setup decisions and operations](#contract-equipment-authority_scope-acquire); [Receipt presence](#contract-profile-receipt-presence); [The host decides capture availability](#contract-profile-receipt-host) |
| [Runner host](#contract-identity-definitions-host), [Worker](#contract-identity-definitions-worker) | [Prepare native compiler input](#contract-policy-spec-parameters); [Fresh process and retained policy](#contract-actors-actor-fresh); [Prepare before use](#contract-extensions-custody-prepare); [Acknowledge, compare and settle delivery](#contract-extensions-custody-deliver); [Erase at declared last use and teardown](#contract-extensions-custody-erase) |
| [Compiler helper](#contract-identity-definitions-helper) | [Read helper input](#contract-policy-helper_request-read); [Helper admission order](#contract-policy-helper_policy-admit); [Inventory, compile and report](#contract-policy-check_data-run_compile); [Select the helper verdict](#contract-policy-check_data-verdict); [Decoded policy metadata](#contract-policy-check_data-metadata); [Release native resources](#contract-policy-compile-release) |
| [Controller](#contract-identity-definitions-controller), [Compiler helper](#contract-identity-definitions-helper), [Worker](#contract-identity-definitions-worker) | [Separate reads and their identities](#contract-policy-imports-holds) |
| [Worker](#contract-identity-definitions-worker) | [Execute a declared operation](#contract-probes-attempt-execute); [Exec setup and child inputs](#contract-probes-attempt-exec); [Observe fresh descriptors](#contract-steps-assessment-fresh) |
| [Worker](#contract-identity-definitions-worker), [Runner host](#contract-identity-definitions-host) | [Issue and transfer payload ownership](#contract-extensions-custody-issue); [Project the fresh-read aggregate](#contract-steps-assessment-fresh_read_aggregate); [Project the fresh-write aggregate](#contract-steps-assessment-fresh_write_aggregate) |
| [Runner client](#contract-identity-definitions-client), [Runner host](#contract-identity-definitions-host) | [Acquire an unused host](#contract-transport-delivery-acquire) |
| [Runner client](#contract-identity-definitions-client) | [Admit the control](#contract-transport-delivery-admit_control); [Invoke execution once](#contract-transport-delivery-invoke) |
| [Controller](#contract-identity-definitions-controller), [Runner client](#contract-identity-definitions-client) | [Apply the original allowance](#contract-transport-delivery-deadline); [Verify a selected service](#contract-installation-commands-verify) |
| [Controller](#contract-identity-definitions-controller), [Retained-byte reader](#contract-wire-frame-reader) | [Exact structural admission](#contract-wire-frame-admit) |
| [Runner host](#contract-identity-definitions-host), [Validator](#contract-identity-definitions-validator) | [Query production and native boundary](#contract-wire-validator-query) |
| [Validator](#contract-identity-definitions-validator) | [Verdict production](#contract-wire-validator-emit); [Parse and report a PID](#contract-wire-standalone-status); [Run one native query](#contract-wire-standalone-query) |

## Controller findings

Each row names the record members a check reads and links each consequence with what it reaches.

| Check | Records read | Consequences and their reach |
| --- | --- | --- |
| [Admit client and host observations](#contract-transport-client-admit) | `client.request_delivery`, `client.runner_reply_error`, `client.stdout_bytes_retained`, `client.stdout_capture_error`, `client.stdout_parse_error`, `client.submission`, `client.transport_admission`, `client.transport_error` | Stated at the linked rule. |
| [Exact structural admission](#contract-wire-frame-admit) | See the linked rule. | Stated at the linked rule. |
| [Checking a carried gate](#contract-actor_evidence-gate-check) | `reply.actors`, `reply.execution_form`, `reply.phases`, `reply.reporting_failure` | [Failed carried-gate requirement](#contract-actor_evidence-gate-check-failed) (on failure): sets `envelope.data.runner_sandbox_diagnostics.disposition_integrity`, `envelope.data.runner_sandbox_diagnostics.process_disposition`, `envelope.data.runner_sandbox_diagnostics.termination_cause`; retains `reply`; keeps `envelope.data.runner_sandbox_diagnostics.actors`. |
| [The controller checks carried labels](#contract-profile-receipt-labels) | `receipt.capture_stage`, `receipt.producer`, `receipt.status` | [A failed label check for run](#contract-profile-receipt-labels-failure) (cli run, on failure): sets `envelope.result.normalized_outcome`, `envelope.result.ok`; withholds `envelope.data.runner_sandbox_diagnostics`; retains `reply`. [A failed label check for runner verify](#contract-profile-receipt-labels-verify_failure) (runner verify, on failure): sets `result.ok`, `result.exit_code`, `result.normalized_outcome`, `runner_verify.normalized_outcome`, `runner_verify.runner_pid`; retains `runner_verify.runner_client`, `runner_verify.runner_result`. |
| [Boundary precedence](#contract-envelope-data-admit) | See the linked rule. | Stated at the linked rule. |
| [Decoded response collection bounds](#contract-diagnostics-execution-geometry) | `reply.actors`, `reply.authority_setup`, `reply.equipment_bindings`, `reply.equipment_entitlements`, `reply.execution_form`, `reply.extension_events`, `reply.phases`, `reply.resources`, `reply.runner_subprocess`, `reply.steps`, `reply.transfers` | [Failed collection bound](#contract-diagnostics-execution-geometry-failed) (on failure): sets `result.normalized_outcome`, `result.ok`, `result.exit_code`; retains `reply`. [Run assessment after refusal](#contract-diagnostics-execution-geometry-run_refusal) (cli run, on failure): sets `envelope.data.runner_sandbox_diagnostics`. [Verification completion after refusal](#contract-diagnostics-execution-geometry-verify_refusal) (runner verify, on failure): sets `runner_verify.normalized_outcome`, `runner_verify.runner_pid`. |
| [Worker lifecycle validation](#contract-diagnostics-execution-ordinary-lifecycle_check) | See the linked rule. | [Local lifecycle findings](#contract-diagnostics-execution-ordinary-lifecycle_check-local_failure) (on failure): sets `envelope.data.runner_sandbox_diagnostics.process_disposition`, `envelope.data.runner_sandbox_diagnostics.termination_cause`, `envelope.data.runner_sandbox_diagnostics.disposition_integrity`, `envelope.data.runner_sandbox_diagnostics.stop_reason`. |
| [Worker lifecycle validation](#contract-diagnostics-actor-projection-lifecycle_check) | See the linked rule. | [Local lifecycle findings](#contract-diagnostics-actor-projection-lifecycle_check-local_failure) (on failure): sets `envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition`, `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_integrity`, `envelope.data.runner_sandbox_diagnostics.actors[d].stop_reason`. |
| [Classify cleanup ownership](#contract-installation-commands-ownership) | See the linked rule. | Stated at the linked rule. |

## Known gaps

| Item | Kind |
| --- | --- |
| [Ordinary-build history requirement](#contract-identity-surfaces-release_history) | behavior |
| [Reporting-failure associations](#contract-reply-failure-publish-associations) | behavior |
| [Termination cancellation reach](#contract-actor_evidence-gate-cancellation_evidence) | behavior |
| [Success and findings](#contract-envelope-data-select-success_findings) | behavior |
| [Unconfirmed vocabulary](#contract-diagnostics-execution-vocabulary-vocabulary_choice) | behavior |
| [Independent semantic classifiers](#contract-diagnostics-execution-reader_evidence-classifier_generation) | behavior |
| [Reply-wide withholding scope](#contract-diagnostics-issue-subject-withholding_scope) | behavior |
<!-- END GENERATED PUBLIC CONTRACT -->
