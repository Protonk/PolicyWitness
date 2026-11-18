<!-- BEGIN GENERATED PUBLIC CONTRACT -->
# Public commitments and their support

Start with the changed declaration, implementation, generated interface or check
in the changed-item index. Follow its candidate commitment to the complete
statement in REQUEST, RESPONSE or ARCHITECTURE. Read the operation, applicability,
consequence and support qualification together. Then return to the cited source
and check to establish what actually changed.

The review can find that implementation changed while a promise held, that its
supporting evidence changed, that the promise needs deliberate revision, or that
implementation and promise disagree. A matching hash, resolving link or passing
shape check does not select among these outcomes.

[REQUEST](REQUEST.md) teaches declarations and their obligations;
[RESPONSE](RESPONSE.md) teaches returned records and their interpretation.
[ARCHITECTURE](ARCHITECTURE.md) holds the cross-process protocols. This document
keeps identity derivation, shared definitions, surface history and the indexes
that connect those statements to their support.

The [authored surface tree](contract/README.md) owns public meaning. The separate
presentation map places whole subjects; moving a statement alone changes no
public payload. The commitment index covers every routing unit. Source and
interface associations are partial: an absent association is an unknown, and a
source citation is evidence with the stated scope, not a declaration of every
behavior that source can affect.

The [interface account](../controller/interface/README.md) and the generator's
`--interface-report` describe the selected structured facts compared by the
interface join. Resolved identifiers do not establish prose, free conditions or
the admission-class binding. Retained mutations describe the source snapshot
that was exercised; they are not new trials of this tree.

<!-- BEGIN GENERATED CONTRACT identity -->
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
`controller/build.rs`, `controller/src/test_inputs/read.json`, `Info.plist`,
`PolicyWitness.entitlements`,
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

<a id="contract-identity-public-derive-support"></a>
**Support: [check read](#contract-support-grades) for [Build derivation](#contract-identity-public-derive).** Selected-source mutations change the digest; clean annotated release selection checks actual bytes; Swift context disagreement and the extracted pre-sign guard refuse. Context: Read generator/source walker and build-stamp/pre-sign code; read tests using disposable source copies and Git repositories, including execution of the extracted shell guard. Evidence limit: The guard control executes the pre-sign script fragment. The multiple-qualifying-tag branch has source support. [Evidence details](#contract-identity-public-derive-support-details).

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

<a id="contract-identity-public-direct-disposition_support"></a>
**Support: [check read](#contract-support-grades) for [Direct compilation contexts](#contract-identity-public-direct).** The non-test constant, Cargo environment tracking and receiver equality gate have separate roles. Context: Static review of the cited producer and assertion branches. Evidence limit: The control builds an isolated non-test controller with supplied and absent stamp values, then checks identity and the next refusing controller boundary. [Evidence details](#contract-identity-public-direct-disposition_support-details).

<a id="contract-identity-public-direct-support"></a>
**Support: [check read](#contract-support-grades) for [Direct compilation contexts](#contract-identity-public-direct).** Absent build binding reports unbound and refuses a matching unbound request; decoded request identity matching is exact and distinguishes missing, null, mistyped and foreign values. Context: Read compile-time constants and Cargo environment tracking; read integration and constructed request tests. Evidence limit: No compilation or test execution credited here; the plain-Cargo check covers an unset environment, not the supplied-value path. [Evidence details](#contract-identity-public-direct-support-details).

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

<a id="contract-identity-surfaces-derive-support"></a>
**Support: [check read](#contract-support-grades) for [Deriving the history table](#contract-identity-surfaces-derive).** Prepared stamps reproduce after tagging; changed declared text moves its surface; removal remains recorded; history-free checks retain a narrower result. Context: Read the authored-tree runtime, both retained history readers and disposable release-tree controls. Evidence limit: Check reading; these controls exercise document/history derivation and input changes, with product behavior supported at its own boundaries. [Evidence details](#contract-identity-surfaces-derive-support-details).

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

<a id="contract-identity-surfaces-development_review-disposition_support"></a>
**Support: [source read](#contract-support-grades) for [Reviewing a development specimen](#contract-identity-surfaces-development_review).** The development identity hashes selected source paths and bytes; release identity selection uses release-tag and byte checks. Evidence limit: The source establishes identity construction. The specimen review procedure is the stated reuse obligation. [Evidence details](#contract-identity-surfaces-development_review-disposition_support-details).

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

<a id="contract-identity-other-support"></a>
**Support: [source read](#contract-support-grades) for [Other identities](#contract-identity-other) and its descendants.** Wire fingerprint precedes producer admission; worker digest scope/framing and fixed-header mismatch have separate producers and checks. Context: Read schema identity construction, Rust bound frame decoder, worker identity generator, C bootstrap branch and Swift evidence header check. Evidence limit: Source reading only. This owner does not credit old-worker execution, every host header-read site, signature association or wire correctness. Those need their respective boundary owners. [Evidence details](#contract-identity-other-support-details).

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

<a id="contract-identity-definitions-support"></a>
**Support: [source read](#contract-support-grades) for [Shared definitions](#contract-identity-definitions) and its descendants.** Names the actual components and record relationships; comparison source distinguishes native prediction, published attempt status, permission-shaped failures and operation/target relations. Context: Read component entry/declaration code, held-request normalization/serialization/client invocation, controller capture record, request forms, validator batch native call, comparison implementation, old file-open operation and envelope serializer. Definitions provide shared terminology; operational predicates remain owned by their surfaces. Evidence limit: Source reading is narrower than a complete lifecycle, native-effect or attribution experiment. Field presence and value admission must be supplied by each owning rule; these definitions do not establish every instance. [Evidence details](#contract-identity-definitions-support-details).
<!-- END GENERATED CONTRACT identity -->

<!-- BEGIN GENERATED CONTRACT STAMPS -->
| Surface | User artifact | Last changed |
| --- | --- | --- |
| `actor_evidence` | Actor and phase evidence | unreleased |
| `actors` | Actors and phases | unreleased |
| `diagnostics` | Controller findings and assessments | unreleased |
| `dossier` | Specimen dossier | unreleased |
| `envelope` | The controller envelope | unreleased |
| `equipment` | Equipment and authority setup | unreleased |
| `extensions` | Extension actions and authority custody | unreleased |
| `identity` | The contract identity | unreleased |
| `installation` | Managing runners | unreleased |
| `lifecycle` | Process and operation observations | unreleased |
| `policy` | Policy source, parameters and compilation | unreleased |
| `probes` | Paired probes and attempted operations | unreleased |
| `profile` | Compiled-profile receipts | unreleased |
| `refusals` | Request refusals and retained evidence | unreleased |
| `reply` | The host report | unreleased |
| `request` | Saved specimens and runner selection | unreleased |
| `steps` | Predictions, attempts and comparison | unreleased |
| `transport` | Reservation, invocation and client capture | unreleased |
| `wire` | Binary response primitives and validator record transport | unreleased |
<!-- END GENERATED CONTRACT STAMPS -->

## Find a commitment

| Identity | Complete statement |
| --- | --- |
| `identity.public` | [Public identity](#contract-identity-public) |
| `identity.surfaces` | [Surface history](#contract-identity-surfaces) |
| `identity.other` | [Other identities](#contract-identity-other) |
| `identity.definitions` | [Shared definitions](#contract-identity-definitions) |
| `request.specimen` | [Specimen](REQUEST.md#contract-request-specimen) |
| `request.options` | [Controller selection options](REQUEST.md#contract-request-options) |
| `request.selector` | [Nested runner selector](REQUEST.md#contract-request-selector) |
| `request.overrides` | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `policy.spec` | [Worker policy input](REQUEST.md#contract-policy-spec) |
| `policy.augments` | [Augment resolution](REQUEST.md#contract-policy-augments) |
| `policy.helper_request` | [Standalone compiler-helper request](REQUEST.md#contract-policy-helper_request) |
| `policy.helper_policy` | [Compiler-helper policy](REQUEST.md#contract-policy-helper_policy) |
| `probes.step` | [Paired probe](REQUEST.md#contract-probes-step) |
| `probes.query` | [Sandbox query](REQUEST.md#contract-probes-query) |
| `probes.filter` | [Sandbox filter](REQUEST.md#contract-probes-filter) |
| `probes.attempt` | [Attempt request](REQUEST.md#contract-probes-attempt) |
| `actors.actor` | [Actor declaration](REQUEST.md#contract-actors-actor) |
| `actors.sandbox` | [Actor sandbox declaration](REQUEST.md#contract-actors-sandbox) |
| `actors.phase` | [Phase declaration](REQUEST.md#contract-actors-phase) |
| `actors.after_termination` | [Termination dependency](REQUEST.md#contract-actors-after_termination) |
| `actors.action` | [Phase action variants](REQUEST.md#contract-actors-action) |
| `extensions.action` | [Extension action](REQUEST.md#contract-extensions-action) |
| `extensions.operation` | [Extension operation](REQUEST.md#contract-extensions-operation) |
| `extensions.examples` | [Extension experiments](REQUEST.md#contract-extensions-examples) |
| `envelope.run` | [Run envelope](RESPONSE.md#contract-envelope-run) |
| `envelope.result` | [Operation result](RESPONSE.md#contract-envelope-result) |
| `envelope.data` | [Run payload](RESPONSE.md#contract-envelope-data) |
| `identity.build` | [Build identification](RESPONSE.md#contract-identity-build) |
| `identity.producer` | [Host producer identification](RESPONSE.md#contract-identity-producer) |
| `reply.record` | [Execution record](RESPONSE.md#contract-reply-record) |
| `reply.failure` | [Reporting failure](RESPONSE.md#contract-reply-failure) |
| `refusals.request` | [Runner request refusal](RESPONSE.md#contract-refusals-request) |
| `refusals.controller` | [Controller request refusal](RESPONSE.md#contract-refusals-controller) |
| `refusals.projection` | [Projected request refusal](RESPONSE.md#contract-refusals-projection) |
| `refusals.admission` | [Capacity refusal](RESPONSE.md#contract-refusals-admission) |
| `refusals.examples` | [Refusal and unavailable-prediction examples](RESPONSE.md#contract-refusals-examples) |
| `refusals.later` | [Failures after invocation](RESPONSE.md#contract-refusals-later) |
| `transport.capture` | [Client capture](RESPONSE.md#contract-transport-capture) |
| `transport.acquisition` | [Acquisition attempt](RESPONSE.md#contract-transport-acquisition) |
| `transport.control_observation` | [Retained control observation](RESPONSE.md#contract-transport-control_observation) |
| `transport.invocation` | [Submission observation](RESPONSE.md#contract-transport-invocation) |
| `transport.retained_reply` | [Retained host reply](RESPONSE.md#contract-transport-retained_reply) |
| `transport.error` | [Client error](RESPONSE.md#contract-transport-error) |
| `transport.client` | [Controller observation of the client process](RESPONSE.md#contract-transport-client) |
| `transport.request_delivery` | [Request stdin delivery](RESPONSE.md#contract-transport-request_delivery) |
| `transport.transport_value` | [Transport alternatives](RESPONSE.md#contract-transport-transport_value) |
| `transport.rejected` | [Rejected client stdout](RESPONSE.md#contract-transport-rejected) |
| `policy.imports` | [Literal import inventory](RESPONSE.md#contract-policy-imports) |
| `policy.fallback` | [Fallback helper capture](RESPONSE.md#contract-policy-fallback) |
| `policy.actor_check` | [Per-actor fallback capture](RESPONSE.md#contract-policy-actor_check) |
| `steps.step` | [Probe result](RESPONSE.md#contract-steps-step) |
| `steps.query` | [Query-channel result](RESPONSE.md#contract-steps-query) |
| `steps.verdict` | [Accepted validator record](RESPONSE.md#contract-steps-verdict) |
| `steps.attempt` | [Attempt-channel result](RESPONSE.md#contract-steps-attempt) |
| `steps.comparison` | [Comparison assessment](RESPONSE.md#contract-steps-comparison) |
| `steps.ordering` | [Collection and release observations](RESPONSE.md#contract-steps-ordering) |
| `steps.query_paths` | [Query path observations](RESPONSE.md#contract-steps-query_paths) |
| `steps.attempt_paths` | [Attempt path observations](RESPONSE.md#contract-steps-attempt_paths) |
| `steps.identity` | [File identity observation](RESPONSE.md#contract-steps-identity) |
| `steps.stat` | [File metadata observation](RESPONSE.md#contract-steps-stat) |
| `steps.fresh_read` | [Fresh-descriptor read](RESPONSE.md#contract-steps-fresh_read) |
| `steps.fresh_write` | [Fresh-descriptor write or creation](RESPONSE.md#contract-steps-fresh_write) |
| `steps.assessment` | [Interpreting the observations](RESPONSE.md#contract-steps-assessment) |
| `actor_evidence.actor` | [Actor process account](RESPONSE.md#contract-actor_evidence-actor) |
| `actor_evidence.launch` | [Actor launch context](RESPONSE.md#contract-actor_evidence-launch) |
| `actor_evidence.application` | [Application assessment](RESPONSE.md#contract-actor_evidence-application) |
| `actor_evidence.phase` | [Phase collection and execution](RESPONSE.md#contract-actor_evidence-phase) |
| `actor_evidence.activation` | [Host activation observation](RESPONSE.md#contract-actor_evidence-activation) |
| `actor_evidence.timing` | [Visit intervals](RESPONSE.md#contract-actor_evidence-timing) |
| `actor_evidence.schedule` | [Schedule account](RESPONSE.md#contract-actor_evidence-schedule) |
| `actor_evidence.gate` | [Termination dependency](RESPONSE.md#contract-actor_evidence-gate) |
| `actor_evidence.owned_endings` | [Observation sequences](RESPONSE.md#contract-actor_evidence-owned_endings) |
| `lifecycle.worker` | [Worker subprocess](RESPONSE.md#contract-lifecycle-worker) |
| `lifecycle.host_wait` | [Measured host wait](RESPONSE.md#contract-lifecycle-host_wait) |
| `lifecycle.termination` | [Host termination request](RESPONSE.md#contract-lifecycle-termination) |
| `lifecycle.wait_error` | [Failed host wait](RESPONSE.md#contract-lifecycle-wait_error) |
| `lifecycle.transfer_timeout` | [Policy-pipe timeout](RESPONSE.md#contract-lifecycle-transfer_timeout) |
| `lifecycle.transfer_error` | [Policy-pipe write error](RESPONSE.md#contract-lifecycle-transfer_error) |
| `lifecycle.worker_evidence` | [Worker publication snapshot](RESPONSE.md#contract-lifecycle-worker_evidence) |
| `lifecycle.progress` | [Worker progress](RESPONSE.md#contract-lifecycle-progress) |
| `lifecycle.failure` | [Terminal worker failure](RESPONSE.md#contract-lifecycle-failure) |
| `lifecycle.readiness` | [Readiness-write result](RESPONSE.md#contract-lifecycle-readiness) |
| `lifecycle.diagnostic` | [Worker diagnostic](RESPONSE.md#contract-lifecycle-diagnostic) |
| `lifecycle.policy_read` | [Worker policy receipt](RESPONSE.md#contract-lifecycle-policy_read) |
| `lifecycle.disposition` | [Canonical worker disposition](RESPONSE.md#contract-lifecycle-disposition) |
| `lifecycle.claim` | [Lifecycle claim](RESPONSE.md#contract-lifecycle-claim) |
| `lifecycle.claim_value` | [Lifecycle answer value](RESPONSE.md#contract-lifecycle-claim_value) |
| `lifecycle.issue` | [Lifecycle conflict](RESPONSE.md#contract-lifecycle-issue) |
| `lifecycle.run_questions` | [Run lifecycle questions](RESPONSE.md#contract-lifecycle-run_questions) |
| `lifecycle.step` | [Step lifecycle account](RESPONSE.md#contract-lifecycle-step) |
| `lifecycle.step_questions` | [Step lifecycle questions](RESPONSE.md#contract-lifecycle-step_questions) |
| `lifecycle.attempt` | [Per-attempt lifecycle projection](RESPONSE.md#contract-lifecycle-attempt) |
| `lifecycle.owned_reap` | [Owned child ending](RESPONSE.md#contract-lifecycle-owned_reap) |
| `lifecycle.reap_reference` | [Owned-ending reference](RESPONSE.md#contract-lifecycle-reap_reference) |
| `lifecycle.spawn_failure` | [Native spawn failure](RESPONSE.md#contract-lifecycle-spawn_failure) |
| `lifecycle.validator` | [Validator subprocess](RESPONSE.md#contract-lifecycle-validator) |
| `lifecycle.decode_fault` | [Rejected validator frame](RESPONSE.md#contract-lifecycle-decode_fault) |
| `lifecycle.association_issue` | [Validator query association](RESPONSE.md#contract-lifecycle-association_issue) |
| `lifecycle.exec` | [Spawned-command observation](RESPONSE.md#contract-lifecycle-exec) |
| `lifecycle.exec_collection` | [Exec collection](RESPONSE.md#contract-lifecycle-exec_collection) |
| `lifecycle.exec_stream` | [Exec stream observation](RESPONSE.md#contract-lifecycle-exec_stream) |
| `lifecycle.exec_cleanup` | [Exec cleanup](RESPONSE.md#contract-lifecycle-exec_cleanup) |
| `lifecycle.exec_signal` | [Exec signal request](RESPONSE.md#contract-lifecycle-exec_signal) |
| `lifecycle.exec_reap` | [Exec leader reap](RESPONSE.md#contract-lifecycle-exec_reap) |
| `lifecycle.exec_wait` | [Exec leader wait result](RESPONSE.md#contract-lifecycle-exec_wait) |
| `equipment.inventory` | [Observed service inventory](RESPONSE.md#contract-equipment-inventory) |
| `equipment.manifest` | [Sealed equipment inventory file](RESPONSE.md#contract-equipment-manifest) |
| `equipment.manifest_worker` | [Inventory worker row](RESPONSE.md#contract-equipment-manifest_worker) |
| `equipment.binding` | [Static worker binding](RESPONSE.md#contract-equipment-binding) |
| `equipment.entitlements` | [Entitlement read-back](RESPONSE.md#contract-equipment-entitlements) |
| `equipment.error` | [Equipment diagnostic](RESPONSE.md#contract-equipment-error) |
| `equipment.actor` | [Actor equipment selection](RESPONSE.md#contract-equipment-actor) |
| `equipment.execution` | [Live actor inspection](RESPONSE.md#contract-equipment-execution) |
| `equipment.native_observation` | [Live inspection call](RESPONSE.md#contract-equipment-native_observation) |
| `equipment.preparation_failure` | [Actor preparation refusal](RESPONSE.md#contract-equipment-preparation_failure) |
| `equipment.authority_setup` | [Authority setup account](RESPONSE.md#contract-equipment-authority_setup) |
| `equipment.authority_host` | [Host authority scopes](RESPONSE.md#contract-equipment-authority_host) |
| `equipment.authority_scope` | [Authority operation scope](RESPONSE.md#contract-equipment-authority_scope) |
| `equipment.authority_operation` | [Authority operation cell](RESPONSE.md#contract-equipment-authority_operation) |
| `equipment.cleanup_reference` | [Unresolved shared-memory name](RESPONSE.md#contract-equipment-cleanup_reference) |
| `profile.receipt` | [Receipt](RESPONSE.md#contract-profile-receipt) |
| `extensions.event` | [Extension event](RESPONSE.md#contract-extensions-event) |
| `extensions.transfer` | [Host transfer observation](RESPONSE.md#contract-extensions-transfer) |
| `extensions.resources` | [Resource tables](RESPONSE.md#contract-extensions-resources) |
| `extensions.token` | [Token resource](RESPONSE.md#contract-extensions-token) |
| `extensions.delivery` | [Delivery resource](RESPONSE.md#contract-extensions-delivery) |
| `extensions.handle` | [Handle resource](RESPONSE.md#contract-extensions-handle) |
| `diagnostics.execution` | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `diagnostics.actor` | [One actor's diagnostics](RESPONSE.md#contract-diagnostics-actor) |
| `diagnostics.issue` | [Integrity finding](RESPONSE.md#contract-diagnostics-issue) |
| `dossier.collection` | [Collection boundaries](RESPONSE.md#contract-dossier-collection) |
| `dossier.specimen` | [Run dossier](RESPONSE.md#contract-dossier-specimen) |
| `dossier.actor` | [Actor policy dossier](RESPONSE.md#contract-dossier-actor) |
| `dossier.policy` | [Policy dossier](RESPONSE.md#contract-dossier-policy) |
| `dossier.augmentation` | [Augmentation observation](RESPONSE.md#contract-dossier-augmentation) |
| `dossier.imports` | [Import scan](RESPONSE.md#contract-dossier-imports) |
| `dossier.import_record` | [One import observation](RESPONSE.md#contract-dossier-import_record) |
| `dossier.host` | [Controller host context](RESPONSE.md#contract-dossier-host) |
| `dossier.app` | [App provenance](RESPONSE.md#contract-dossier-app) |
| `dossier.binaries` | [Selected binary observations](RESPONSE.md#contract-dossier-binaries) |
| `dossier.binary` | [One selected binary](RESPONSE.md#contract-dossier-binary) |
| `dossier.runner` | [Selected runner provenance](RESPONSE.md#contract-dossier-runner) |
| `dossier.verification` | [Manifest hash verification](RESPONSE.md#contract-dossier-verification) |
| `dossier.mismatch` | [One verification failure](RESPONSE.md#contract-dossier-mismatch) |
| `identity.version` | [Version reporting](RESPONSE.md#contract-identity-version) |
| `policy.check_data` | [Compiler-helper data](RESPONSE.md#contract-policy-check_data) |
| `policy.compile` | [Last native compile stage](RESPONSE.md#contract-policy-compile) |
| `envelope.helper` | [Compiler-helper envelope](RESPONSE.md#contract-envelope-helper) |
| `wire.standalone` | [Direct validator commands](RESPONSE.md#contract-wire-standalone) |
| `wire.standalone_status` | [Direct PID status](RESPONSE.md#contract-wire-standalone_status) |
| `wire.standalone_result` | [Direct native result](RESPONSE.md#contract-wire-standalone_result) |
| `wire.standalone_error` | [Direct argument error](RESPONSE.md#contract-wire-standalone_error) |
| `installation.commands` | [Command boundaries](RESPONSE.md#contract-installation-commands) |
| `installation.registry` | [Runner registry](RESPONSE.md#contract-installation-registry) |
| `installation.runner` | [One runner record](RESPONSE.md#contract-installation-runner) |
| `installation.ownership` | [Recorded cleanup ownership](RESPONSE.md#contract-installation-ownership) |
| `installation.signature` | [Signature observation](RESPONSE.md#contract-installation-signature) |
| `installation.entitlements` | [Entitlement observation](RESPONSE.md#contract-installation-entitlements) |
| `installation.pending_cleanup` | [Retained cleanup transaction](RESPONSE.md#contract-installation-pending_cleanup) |
| `installation.cleanup` | [Removal result](RESPONSE.md#contract-installation-cleanup) |
| `installation.install` | [Installation result](RESPONSE.md#contract-installation-install) |
| `installation.verify` | [Verification result](RESPONSE.md#contract-installation-verify) |
| `installation.validate` | [Validation result](RESPONSE.md#contract-installation-validate) |
| `installation.failure` | [One validation failure](RESPONSE.md#contract-installation-failure) |
| `installation.not_found` | [Unmatched lookup](RESPONSE.md#contract-installation-not_found) |
| `installation.service` | [Observed service](RESPONSE.md#contract-installation-service) |
| `installation.plist` | [Observed plist](RESPONSE.md#contract-installation-plist) |
| `installation.reconcile` | [Reconciliation result](RESPONSE.md#contract-installation-reconcile) |
| `installation.reconcile_record` | [One recorded reconciliation](RESPONSE.md#contract-installation-reconcile_record) |
| `installation.candidate` | [Unregistered candidate](RESPONSE.md#contract-installation-candidate) |
| `installation.inspection_error` | [Reconciliation inspection error](RESPONSE.md#contract-installation-inspection_error) |
| `installation.cleanup_observation` | [Current cleanup observation](RESPONSE.md#contract-installation-cleanup_observation) |
| `installation.cleanup_wait` | [Service teardown polling](RESPONSE.md#contract-installation-cleanup_wait) |
| `extensions.custody` | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `transport.authorization` | [Caller authorization](ARCHITECTURE.md#contract-transport-authorization) |
| `transport.delivery` | [Reservation and execution](ARCHITECTURE.md#contract-transport-delivery) |
| `transport.reservation` | [Reservation request](ARCHITECTURE.md#contract-transport-reservation) |
| `transport.control` | [Host control reply](ARCHITECTURE.md#contract-transport-control) |
| `wire.frame` | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `wire.validator` | [Validator query and reply lines](ARCHITECTURE.md#contract-wire-validator) |

## Follow a changed item

Declarations own meaning; source and check citations supply the stated support. A file association identifies candidates for review, not every behavior that file can affect.

| Changed item | Relationship | Candidate commitment |
| --- | --- | --- |
| `ActorEquipmentManifest` | imported record declaration | [Sealed equipment inventory file](RESPONSE.md#contract-equipment-manifest) |
| `ActorEquipmentManifest.Worker` | imported record declaration | [Inventory worker row](RESPONSE.md#contract-equipment-manifest_worker) |
| `CompiledProfileCapture` | imported record declaration | [Receipt](RESPONSE.md#contract-profile-receipt) |
| `ControllerRunnerSelector` | imported record declaration | [Nested runner selector](REQUEST.md#contract-request-selector) |
| `ControllerSelectionOptions` | imported record declaration | [Controller selection options](REQUEST.md#contract-request-options) |
| `PWAttemptLifecycle` | imported record declaration | [Per-attempt lifecycle projection](RESPONSE.md#contract-lifecycle-attempt) |
| `PWAuthorityCleanupReference` | imported record declaration | [Unresolved shared-memory name](RESPONSE.md#contract-equipment-cleanup_reference) |
| `PWDispositionClaim` | imported record declaration | [Lifecycle claim](RESPONSE.md#contract-lifecycle-claim) |
| `PWDispositionIssue` | imported record declaration | [Lifecycle conflict](RESPONSE.md#contract-lifecycle-issue) |
| `PWDispositionRecord` | imported record declaration | [Canonical worker disposition](RESPONSE.md#contract-lifecycle-disposition) |
| `PWDispositionRunQuestions` | imported record declaration | [Run lifecycle questions](RESPONSE.md#contract-lifecycle-run_questions) |
| `PWDispositionStep` | imported record declaration | [Step lifecycle account](RESPONSE.md#contract-lifecycle-step) |
| `PWDispositionStepQuestions` | imported record declaration | [Step lifecycle questions](RESPONSE.md#contract-lifecycle-step_questions) |
| `PWDispositionValue` | imported record declaration | [Lifecycle answer value](RESPONSE.md#contract-lifecycle-claim_value) |
| `PWExecCleanupObservation` | imported record declaration | [Exec cleanup](RESPONSE.md#contract-lifecycle-exec_cleanup) |
| `PWExecCollectionObservation` | imported record declaration | [Exec collection](RESPONSE.md#contract-lifecycle-exec_collection) |
| `PWExecObservation` | imported record declaration | [Spawned-command observation](RESPONSE.md#contract-lifecycle-exec) |
| `PWExecReapObservation` | imported record declaration | [Exec leader reap](RESPONSE.md#contract-lifecycle-exec_reap) |
| `PWExecSignalRequest` | imported record declaration | [Exec signal request](RESPONSE.md#contract-lifecycle-exec_signal) |
| `PWExecStreamObservation` | imported record declaration | [Exec stream observation](RESPONSE.md#contract-lifecycle-exec_stream) |
| `PWExecWaitObservation` | imported record declaration | [Exec leader wait result](RESPONSE.md#contract-lifecycle-exec_wait) |
| `PWFileIdentity` | imported record declaration | [File identity observation](RESPONSE.md#contract-steps-identity) |
| `PWHostWait` | imported record declaration | [Measured host wait](RESPONSE.md#contract-lifecycle-host_wait) |
| `PWOwnedReapObservation` | imported record declaration | [Owned child ending](RESPONSE.md#contract-lifecycle-owned_reap) |
| `PWOwnedReapReference` | imported record declaration | [Owned-ending reference](RESPONSE.md#contract-lifecycle-reap_reference) |
| `PWProducer` | imported record declaration | [Host producer identification](RESPONSE.md#contract-identity-producer) |
| `PWRunnerAcquisitionAttempt` | imported record declaration | [Acquisition attempt](RESPONSE.md#contract-transport-acquisition) |
| `PWRunnerActor` | imported record declaration | [Actor declaration](REQUEST.md#contract-actors-actor) |
| `PWRunnerActorActivation` | imported record declaration | [Host activation observation](RESPONSE.md#contract-actor_evidence-activation) |
| `PWRunnerActorApplication` | imported record declaration | [Application assessment](RESPONSE.md#contract-actor_evidence-application) |
| `PWRunnerActorEquipment` | imported record declaration | [Actor equipment selection](RESPONSE.md#contract-equipment-actor) |
| `PWRunnerActorLaunch` | imported record declaration | [Actor launch context](RESPONSE.md#contract-actor_evidence-launch) |
| `PWRunnerActorResult` | imported record declaration | [Actor process account](RESPONSE.md#contract-actor_evidence-actor) |
| `PWRunnerActorSandbox` | imported record declaration | [Actor sandbox declaration](REQUEST.md#contract-actors-sandbox) |
| `PWRunnerAdmissionFailure` | imported record declaration | [Capacity refusal](RESPONSE.md#contract-refusals-admission) |
| `PWRunnerAfterTermination` | imported record declaration | [Termination dependency](REQUEST.md#contract-actors-after_termination) |
| `PWRunnerAttempt` | imported record declaration | [Attempt request](REQUEST.md#contract-probes-attempt) |
| `PWRunnerAttemptPathDiagnostics` | imported record declaration | [Attempt path observations](RESPONSE.md#contract-steps-attempt_paths) |
| `PWRunnerAttemptResult` | imported record declaration | [Attempt-channel result](RESPONSE.md#contract-steps-attempt) |
| `PWRunnerAuthorityHost` | imported record declaration | [Host authority scopes](RESPONSE.md#contract-equipment-authority_host) |
| `PWRunnerAuthorityOperation` | imported record declaration | [Authority operation cell](RESPONSE.md#contract-equipment-authority_operation) |
| `PWRunnerAuthorityScope` | imported record declaration | [Authority operation scope](RESPONSE.md#contract-equipment-authority_scope) |
| `PWRunnerAuthoritySetup` | imported record declaration | [Authority setup account](RESPONSE.md#contract-equipment-authority_setup) |
| `PWRunnerClientCapture` | imported record declaration | [Client capture](RESPONSE.md#contract-transport-capture) |
| `PWRunnerComparison` | imported record declaration | [Comparison assessment](RESPONSE.md#contract-steps-comparison) |
| `PWRunnerControlObservation` | imported record declaration | [Retained control observation](RESPONSE.md#contract-transport-control_observation) |
| `PWRunnerControlReply` | imported record declaration | [Host control reply](ARCHITECTURE.md#contract-transport-control) |
| `PWRunnerDeliveryRecord` | imported record declaration | [Delivery resource](RESPONSE.md#contract-extensions-delivery) |
| `PWRunnerEquipmentBinding` | imported record declaration | [Static worker binding](RESPONSE.md#contract-equipment-binding) |
| `PWRunnerEquipmentEntitlements` | imported record declaration | [Entitlement read-back](RESPONSE.md#contract-equipment-entitlements) |
| `PWRunnerEquipmentError` | imported record declaration | [Equipment diagnostic](RESPONSE.md#contract-equipment-error) |
| `PWRunnerEquipmentExecution` | imported record declaration | [Live actor inspection](RESPONSE.md#contract-equipment-execution) |
| `PWRunnerEquipmentInventory` | imported record declaration | [Observed service inventory](RESPONSE.md#contract-equipment-inventory) |
| `PWRunnerEquipmentNativeObservation` | imported record declaration | [Live inspection call](RESPONSE.md#contract-equipment-native_observation) |
| `PWRunnerExtensionAction` | imported record declaration | [Extension action](REQUEST.md#contract-extensions-action) |
| `PWRunnerExtensionEvent` | imported record declaration | [Extension event](RESPONSE.md#contract-extensions-event) |
| `PWRunnerExtensionOperation` | imported record declaration | [Extension operation](REQUEST.md#contract-extensions-operation) |
| `PWRunnerFileStat` | imported record declaration | [File metadata observation](RESPONSE.md#contract-steps-stat) |
| `PWRunnerFreshRead` | imported record declaration | [Fresh-descriptor read](RESPONSE.md#contract-steps-fresh_read) |
| `PWRunnerFreshWrite` | imported record declaration | [Fresh-descriptor write or creation](RESPONSE.md#contract-steps-fresh_write) |
| `PWRunnerHandleRecord` | imported record declaration | [Handle resource](RESPONSE.md#contract-extensions-handle) |
| `PWRunnerOrdering` | imported record declaration | [Collection and release observations](RESPONSE.md#contract-steps-ordering) |
| `PWRunnerPathDiagnostics` | imported record declaration | [Query path observations](RESPONSE.md#contract-steps-query_paths) |
| `PWRunnerPhase` | imported record declaration | [Phase declaration](REQUEST.md#contract-actors-phase) |
| `PWRunnerPhaseAction` | imported record declaration | [Phase action variants](REQUEST.md#contract-actors-action) |
| `PWRunnerPhaseResult` | imported record declaration | [Phase collection and execution](RESPONSE.md#contract-actor_evidence-phase) |
| `PWRunnerPolicySpec` | imported record declaration | [Worker policy input](REQUEST.md#contract-policy-spec) |
| `PWRunnerPreparationFailure` | imported record declaration | [Actor preparation refusal](RESPONSE.md#contract-equipment-preparation_failure) |
| `PWRunnerProbeStep` | imported record declaration | [Paired probe](REQUEST.md#contract-probes-step) |
| `PWRunnerReplyCapture` | imported record declaration | [Retained host reply](RESPONSE.md#contract-transport-retained_reply) |
| `PWRunnerReportingFailure` | imported record declaration | [Reporting failure](RESPONSE.md#contract-reply-failure) |
| `PWRunnerRequestFailure` | imported record declaration | [Runner request refusal](RESPONSE.md#contract-refusals-request) |
| `PWRunnerReservationRequest` | imported record declaration | [Reservation request](ARCHITECTURE.md#contract-transport-reservation) |
| `PWRunnerResourceTables` | imported record declaration | [Resource tables](RESPONSE.md#contract-extensions-resources) |
| `PWRunnerRunResult` | imported record declaration | [Execution record](RESPONSE.md#contract-reply-record) |
| `PWRunnerRunSpec` | imported record declaration | [Specimen](REQUEST.md#contract-request-specimen) |
| `PWRunnerSandboxCheck` | imported record declaration | [Sandbox query](REQUEST.md#contract-probes-query) |
| `PWRunnerSandboxCheckResult` | imported record declaration | [Query-channel result](RESPONSE.md#contract-steps-query) |
| `PWRunnerSandboxFilter` | imported record declaration | [Sandbox filter](REQUEST.md#contract-probes-filter) |
| `PWRunnerScheduleRecord` | imported record declaration | [Schedule account](RESPONSE.md#contract-actor_evidence-schedule) |
| `PWRunnerSpawnFailure` | imported record declaration | [Native spawn failure](RESPONSE.md#contract-lifecycle-spawn_failure) |
| `PWRunnerStepResult` | imported record declaration | [Probe result](RESPONSE.md#contract-steps-step) |
| `PWRunnerSubmission` | imported record declaration | [Submission observation](RESPONSE.md#contract-transport-invocation) |
| `PWRunnerSubprocess` | imported record declaration | [Worker subprocess](RESPONSE.md#contract-lifecycle-worker) |
| `PWRunnerTerminationGate` | imported record declaration | [Termination dependency](RESPONSE.md#contract-actor_evidence-gate) |
| `PWRunnerTerminationRequest` | imported record declaration | [Host termination request](RESPONSE.md#contract-lifecycle-termination) |
| `PWRunnerTestOverrides` | imported record declaration | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `PWRunnerTokenRecord` | imported record declaration | [Token resource](RESPONSE.md#contract-extensions-token) |
| `PWRunnerTransferRecord` | imported record declaration | [Host transfer observation](RESPONSE.md#contract-extensions-transfer) |
| `PWRunnerTransportError` | imported record declaration | [Client error](RESPONSE.md#contract-transport-error) |
| `PWRunnerValidatorSubprocess` | imported record declaration | [Validator subprocess](RESPONSE.md#contract-lifecycle-validator) |
| `PWRunnerVisitTiming` | imported record declaration | [Visit intervals](RESPONSE.md#contract-actor_evidence-timing) |
| `PWRunnerWaitError` | imported record declaration | [Failed host wait](RESPONSE.md#contract-lifecycle-wait_error) |
| `PWValidatorAssociationIssue` | imported record declaration | [Validator query association](RESPONSE.md#contract-lifecycle-association_issue) |
| `PWValidatorDecodeFault` | imported record declaration | [Rejected validator frame](RESPONSE.md#contract-lifecycle-decode_fault) |
| `PWWorkerDiagnostic` | imported record declaration | [Worker diagnostic](RESPONSE.md#contract-lifecycle-diagnostic) |
| `PWWorkerEvidence` | imported record declaration | [Worker publication snapshot](RESPONSE.md#contract-lifecycle-worker_evidence) |
| `PWWorkerFailure` | imported record declaration | [Terminal worker failure](RESPONSE.md#contract-lifecycle-failure) |
| `PWWorkerPolicyRead` | imported record declaration | [Worker policy receipt](RESPONSE.md#contract-lifecycle-policy_read) |
| `PWWorkerPolicyTransferError` | imported record declaration | [Policy-pipe write error](RESPONSE.md#contract-lifecycle-transfer_error) |
| `PWWorkerPolicyTransferTimeout` | imported record declaration | [Policy-pipe timeout](RESPONSE.md#contract-lifecycle-transfer_timeout) |
| `PWWorkerProgress` | imported record declaration | [Worker progress](RESPONSE.md#contract-lifecycle-progress) |
| `PWWorkerReadiness` | imported record declaration | [Readiness-write result](RESPONSE.md#contract-lifecycle-readiness) |
| `RunnerCleanupObservation` | imported record declaration | [Current cleanup observation](RESPONSE.md#contract-installation-cleanup_observation) |
| `RunnerCleanupWait` | imported record declaration | [Service teardown polling](RESPONSE.md#contract-installation-cleanup_wait) |
| `RunnerReconcileCandidate` | imported record declaration | [Unregistered candidate](RESPONSE.md#contract-installation-candidate) |
| `RunnerReconcileData` | imported record declaration | [Reconciliation result](RESPONSE.md#contract-installation-reconcile) |
| `RunnerReconcileInspectionError` | imported record declaration | [Reconciliation inspection error](RESPONSE.md#contract-installation-inspection_error) |
| `RunnerReconcileRecord` | imported record declaration | [One recorded reconciliation](RESPONSE.md#contract-installation-reconcile_record) |
| `ValidatorDirectError` | imported record declaration | [Direct argument error](RESPONSE.md#contract-wire-standalone_error) |
| `ValidatorDirectResult` | imported record declaration | [Direct native result](RESPONSE.md#contract-wire-standalone_result) |
| `ValidatorDirectStatus` | imported record declaration | [Direct PID status](RESPONSE.md#contract-wire-standalone_status) |
| `ValidatorVerdict` | imported record declaration | [Accepted validator record](RESPONSE.md#contract-steps-verdict) |
| `VersionData` | imported record declaration | [Version reporting](RESPONSE.md#contract-identity-version) |
| `build.sh: # ---- Build stamp` | source support | [Build identification](RESPONSE.md#contract-identity-build) |
| `build.sh: CURRENT_BUILD_CONTRACT=` | source support | [Build derivation](#contract-identity-public-derive) |
| `build.sh: stamp_info_plist` | source support | [Build identification](RESPONSE.md#contract-identity-build) |
| `command.example` | interface association; see the partial join | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `command.test_input` | interface association; see the partial join | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/build.rs: cargo:rerun-if-env-changed` | source support | [Direct compilation contexts](#contract-identity-public-direct) |
| `controller/build.rs: fn main` | source support | [Direct compilation contexts](#contract-identity-public-direct) |
| `controller/integration/cli_contract.rs: example_prints_one_request_and_refuses_every_argument` | check support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `controller/integration/cli_contract.rs: example_write_failures_exit_2_without_a_panic` | check support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `controller/integration/cli_contract.rs: interface_cases_hold_on_the_signed_controller` | check support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/integration/cli_contract.rs: plain_cargo_build_cannot_admit_public_requests` | check support | [Direct compilation contexts](#contract-identity-public-direct) |
| `controller/integration/cli_contract.rs: sbpl_check_verdicts_follow_the_native_compiler` | check support | [Parameter example observations](REQUEST.md#contract-policy-spec-parameter_evidence) |
| `controller/integration/cli_contract.rs: supplied_direct_cargo_identity_is_embedded_without_release_provenance` | check support | [Direct compilation contexts](#contract-identity-public-direct) |
| `controller/integration/cli_contract.rs: supplied_direct_cargo_identity_is_embedded_without_release_provenance` | check support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `controller/integration/cli_contract.rs: supplied_direct_cargo_identity_is_embedded_without_release_provenance` | check support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/integration/cli_contract.rs: test_input_cli_refusals_and_write_failures_exit_2_safely` | check support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/integration/cli_contract.rs: test_input_publishes_read_from_the_installed_binary` | check support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/integration/cli_contract.rs: test_input_publishes_read_from_the_installed_binary` | check support | [Developer read body](REQUEST.md#contract-request-specimen-read_input) |
| `controller/integration/cli_contract.rs: version_dispatch_uses_the_first_argument` | check support | [Version command](RESPONSE.md#contract-identity-version-emit) |
| `controller/integration/cli_contract.rs: version_flag_reports_build_stamp_and_contract` | check support | [Build identification](RESPONSE.md#contract-identity-build) |
| `controller/integration/cli_contract.rs: version_flag_reports_build_stamp_and_contract` | check support | [Version command](RESPONSE.md#contract-identity-version-emit) |
| `controller/src/augments.rs: actor_policies_resolve_at_their_own_paths_and_stop_at_the_first_refusal` | check support | [Augment resolution](REQUEST.md#contract-policy-augments) |
| `controller/src/augments.rs: applies_and_strips_field` | check support | [Augment resolution](REQUEST.md#contract-policy-augments) |
| `controller/src/augments.rs: resolve_actor_augments` | source support | [Augment resolution](REQUEST.md#contract-policy-augments) |
| `controller/src/augments.rs: resolve_policy_augments` | source support | [Augment resolution](REQUEST.md#contract-policy-augments) |
| `controller/src/augments.rs: resolve_policy_augments` | source support | [Augment evidence scope](REQUEST.md#contract-policy-augments-augment_semantics) |
| `controller/src/augments.rs: unknown_name_is_bad_request_without_partial_apply` | check support | [Augment resolution](REQUEST.md#contract-policy-augments) |
| `controller/src/bin/sbpl-check.rs: CheckData` | source support | [Compiler-helper data](RESPONSE.md#contract-policy-check_data) |
| `controller/src/bin/sbpl-check.rs: CheckPolicy` | source support | [Compiler-helper policy](REQUEST.md#contract-policy-helper_policy) |
| `controller/src/bin/sbpl-check.rs: CheckRequest` | source support | [Standalone compiler-helper request](REQUEST.md#contract-policy-helper_request) |
| `controller/src/bin/sbpl-check.rs: CompileRecord` | source support | [Last native compile stage](RESPONSE.md#contract-policy-compile) |
| `controller/src/bin/sbpl-check.rs: ImportInventory` | source support | [Literal import inventory](RESPONSE.md#contract-policy-imports) |
| `controller/src/bin/sbpl-check.rs: a_profile_succeeds_alone_and_fails_beside_an_error_buffer` | check support | [Worker and helper compile classification](REQUEST.md#contract-policy-spec-compile_classification) |
| `controller/src/bin/sbpl-check.rs: admit` | source support | [Compiler-helper policy](REQUEST.md#contract-policy-helper_policy) |
| `controller/src/bin/sbpl-check.rs: check` | source support | [Compiler-helper data](RESPONSE.md#contract-policy-check_data) |
| `controller/src/bin/sbpl-check.rs: check` | source support | [Decoded policy metadata](RESPONSE.md#contract-policy-check_data-metadata) |
| `controller/src/bin/sbpl-check.rs: check` | source support | [Parameter example observations](REQUEST.md#contract-policy-spec-parameter_evidence) |
| `controller/src/bin/sbpl-check.rs: compile_with` | source support | [Last native compile stage](RESPONSE.md#contract-policy-compile) |
| `controller/src/bin/sbpl-check.rs: compile_with` | source support | [Worker and helper compile classification](REQUEST.md#contract-policy-spec-compile_classification) |
| `controller/src/bin/sbpl-check.rs: fn main` | source support | [Standalone compiler-helper request](REQUEST.md#contract-policy-helper_request) |
| `controller/src/bin/sbpl-check.rs: verdict` | source support | [Select the helper verdict](RESPONSE.md#contract-policy-check_data-verdict) |
| `controller/src/cli.rs: pub fn run` | source support | [Version command](RESPONSE.md#contract-identity-version-emit) |
| `controller/src/cli.rs: pub fn run` | source support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `controller/src/cli.rs: pub fn run` | source support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/src/dossier.rs: Augmentation` | source support | [Augmentation record relationships](RESPONSE.md#contract-dossier-augmentation-relationships) |
| `controller/src/dossier.rs: Binaries` | source support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/dossier.rs: Imports` | source support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/dossier.rs: Imports` | source support | [Retained scan scope](RESPONSE.md#contract-dossier-imports-scope) |
| `controller/src/dossier.rs: Specimen` | source support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/dossier.rs: augmentation_records_hash_only_bytes_that_existed` | check support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/dossier.rs: builtin_run_hashes_nothing_and_reports_null_records` | check support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/dossier.rs: byoxpc_copies_are_compared_with_the_shipped_baselines` | check support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/dossier.rs: compare` | source support | [Classify the retained digest pair](RESPONSE.md#contract-dossier-binary-classify) |
| `controller/src/dossier.rs: fn compare` | source support | [Held input and file observation scope](RESPONSE.md#contract-dossier-collection-native_gap) |
| `controller/src/dossier.rs: import_scan_statuses_never_report_an_unscanned_closure_as_complete` | check support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/dossier.rs: pub fn observe_with_validator_control` | source support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/dossier.rs: validator_control_follows_the_request_key_rules_and_names_the_flag` | check support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/evidence.rs: verify_manifest` | source support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/example.rs: fn emit` | source support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `controller/src/example.rs: only_complete_output_with_a_successful_flush_succeeds` | check support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `controller/src/example.rs: pub fn cmd_example` | source support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `controller/src/example.rs: pub fn render` | source support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `controller/src/example.rs: refusals_are_typed_and_write_nothing` | check support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `controller/src/example.rs: rendered_document_is_the_constant_with_the_given_identity` | check support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `controller/src/example_document.rs: EXAMPLE_DOCUMENT` | extracted example | [Read-hosts pair](REQUEST.md#contract-probes-step-read_hosts) |
| `controller/src/example_document.rs: EXAMPLE_DOCUMENT` | extracted example | [Emitted example](REQUEST.md#contract-request-specimen-example) |
| `controller/src/example_document.rs: EXAMPLE_DOCUMENT` | source support | [Emitted example](REQUEST.md#contract-request-specimen-example) |
| `controller/src/interface/commands.rs: pub fn select_form` | source support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/interface/run_args.rs: pub fn classify` | source support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/interface/runner_kind.rs: pub const fn rule` | source support | [kind](RESPONSE.md#contract-installation-runner-kind) |
| `controller/src/json_contract.rs: BUILD_CONTRACT` | source support | [Direct compilation contexts](#contract-identity-public-direct) |
| `controller/src/json_contract.rs: Envelope` | source support | [Shared definitions](#contract-identity-definitions) |
| `controller/src/json_contract.rs: JsonResult` | source support | [Version command](RESPONSE.md#contract-identity-version-emit) |
| `controller/src/json_contract.rs: build_stamp` | source support | [Build identification](RESPONSE.md#contract-identity-build) |
| `controller/src/json_contract.rs: every_envelope_carries_a_complete_build_stamp` | check support | [Build identification](RESPONSE.md#contract-identity-build) |
| `controller/src/json_contract.rs: impl JsonResult` | source support | [A failed label check for runner verify](RESPONSE.md#contract-profile-receipt-labels-verify_failure) |
| `controller/src/json_contract.rs: now_unix_ms` | source support | [Version command](RESPONSE.md#contract-identity-version-emit) |
| `controller/src/json_contract.rs: public_identity_is_in_the_build_frame` | check support | [Build identification](RESPONSE.md#contract-identity-build) |
| `controller/src/json_contract.rs: render_envelope` | source support | [The controller envelope](RESPONSE.md#contract-envelope) |
| `controller/src/json_contract.rs: renderer_borrows_nonclone_typed_payload_and_serializes_it_once` | check support | [The controller envelope](RESPONSE.md#contract-envelope) |
| `controller/src/main.rs: fn main` | source support | [Shared definitions](#contract-identity-definitions) |
| `controller/src/policy_check.rs: parse_policy_check_output` | source support | [Fallback helper capture](RESPONSE.md#contract-policy-fallback) |
| `controller/src/policy_check.rs: supported_outcome` | source support | [Fallback helper capture](RESPONSE.md#contract-policy-fallback) |
| `controller/src/policy_check.rs: supported_outcomes_are_copied_into_status_without_a_second_verdict` | check support | [Fallback helper capture](RESPONSE.md#contract-policy-fallback) |
| `controller/src/porcelain.rs: actual_nested_container_frames_reach_but_do_not_exceed_depth_32` | check support | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `controller/src/porcelain.rs: authored_record_faults_are_refused_before_typed_construction` | check support | [Response encoding](ARCHITECTURE.md#contract-wire) |
| `controller/src/porcelain.rs: decode_bound` | source support | [Other identities](#contract-identity-other) |
| `controller/src/porcelain.rs: decode_bound` | source support | [Host producer identification](RESPONSE.md#contract-identity-producer) |
| `controller/src/porcelain.rs: decode_bound` | source support | [Response encoding](ARCHITECTURE.md#contract-wire) |
| `controller/src/porcelain.rs: generated_capture_byte_field_requires_the_byte_kind` | check support | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `controller/src/porcelain.rs: generated_disposition_variant_checks_tag_payload_and_complete_body` | check support | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `controller/src/porcelain.rs: list_counts_item_kinds_and_trailing_items_refuse_in_actual_frames` | check support | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `controller/src/porcelain.rs: list_slots_and_nested_strings_share_one_budget` | check support | [Response encoding](ARCHITECTURE.md#contract-wire) |
| `controller/src/porcelain.rs: native_integer_width_and_boolean_values_are_not_coerced` | check support | [Response encoding](ARCHITECTURE.md#contract-wire) |
| `controller/src/porcelain.rs: ordered_maps_require_unique_ascending_keys_in_actual_frames` | check support | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `controller/src/porcelain.rs: pub fn decode` | source support | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `controller/src/porcelain_actor.rs: fn gates` | source support | [Integrity finding](RESPONSE.md#contract-diagnostics-issue) |
| `controller/src/porcelain_actor.rs: fn gates` | source support | [Finding association and effect](RESPONSE.md#contract-diagnostics-issue-subject) |
| `controller/src/porcelain_actor.rs: fn identity` | source support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `controller/src/porcelain_actor.rs: fn require` | source support | [Integrity finding](RESPONSE.md#contract-diagnostics-issue) |
| `controller/src/porcelain_actor.rs: gate_findings_locate_each_retained_assertion_by_position` | check support | [Finding association and effect](RESPONSE.md#contract-diagnostics-issue-subject) |
| `controller/src/porcelain_actor.rs: gates` | source support | [Actor and phase evidence](RESPONSE.md#contract-actor_evidence) |
| `controller/src/porcelain_actor.rs: preparation_failure_valid` | source support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `controller/src/porcelain_actor.rs: pub(super) fn validate` | source support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/porcelain_admission.rs: IntegrityIssue` | source support | [Integrity finding](RESPONSE.md#contract-diagnostics-issue) |
| `controller/src/porcelain_admission.rs: admission_problem` | source support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `controller/src/porcelain_admission.rs: admission_problem` | source support | [Decoded response collection bounds](RESPONSE.md#contract-diagnostics-execution-geometry) |
| `controller/src/porcelain_admission.rs: admission_problem` | source support | [A failed label check for run](RESPONSE.md#contract-profile-receipt-labels-failure) |
| `controller/src/porcelain_admission.rs: admit_reply` | source support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/porcelain_admission.rs: check_claim` | source support | [One actor's diagnostics](RESPONSE.md#contract-diagnostics-actor) |
| `controller/src/porcelain_admission.rs: claim_geometry` | source support | [Decoded response collection bounds](RESPONSE.md#contract-diagnostics-execution-geometry) |
| `controller/src/porcelain_admission.rs: execution_diagnostics` | source support | [Actor and phase evidence](RESPONSE.md#contract-actor_evidence) |
| `controller/src/porcelain_admission.rs: execution_diagnostics` | source support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/porcelain_admission.rs: execution_diagnostics` | source support | [Reader judgments](RESPONSE.md#contract-diagnostics-execution-reader_evidence) |
| `controller/src/porcelain_admission.rs: fn issue` | source support | [Integrity finding](RESPONSE.md#contract-diagnostics-issue) |
| `controller/src/porcelain_admission.rs: for i in &sub.disposition` | source support | [Integrity finding](RESPONSE.md#contract-diagnostics-issue) |
| `controller/src/porcelain_admission.rs: lifecycle_geometry` | source support | [Decoded response collection bounds](RESPONSE.md#contract-diagnostics-execution-geometry) |
| `controller/src/porcelain_admission.rs: project` | source support | [One actor's diagnostics](RESPONSE.md#contract-diagnostics-actor) |
| `controller/src/porcelain_admission.rs: project` | source support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/porcelain_admission.rs: pub(crate) fn admission_problem` | source support | [The controller checks carried labels](RESPONSE.md#contract-profile-receipt-labels) |
| `controller/src/porcelain_admission.rs: reply_geometry` | source support | [Decoded response collection bounds](RESPONSE.md#contract-diagnostics-execution-geometry) |
| `controller/src/porcelain_admission.rs: scope_geometry` | source support | [Decoded response collection bounds](RESPONSE.md#contract-diagnostics-execution-geometry) |
| `controller/src/porcelain_admission.rs: typed_degradation_never_certifies_surviving_comparison` | check support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/porcelain_admission.rs: typed_future_applicability_and_summary_remain_open_without_rewriting` | check support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/porcelain_admission.rs: typed_geometry_refuses_before_projection_and_retains_every_raw_record` | check support | [Decoded response collection bounds](RESPONSE.md#contract-diagnostics-execution-geometry) |
| `controller/src/porcelain_admission.rs: typed_host_cleanup_cause_requires_all_independent_observations` | check support | [One actor's diagnostics](RESPONSE.md#contract-diagnostics-actor) |
| `controller/src/porcelain_admission.rs: typed_invalid_actor_account_keeps_independent_actor_endings` | check support | [One actor's diagnostics](RESPONSE.md#contract-diagnostics-actor) |
| `controller/src/porcelain_admission.rs: typed_invalid_actor_account_keeps_independent_actor_endings` | check support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/porcelain_admission.rs: typed_reference_geometry_is_checked_before_claims_and_admission_contexts` | check support | [Decoded response collection bounds](RESPONSE.md#contract-diagnostics-execution-geometry) |
| `controller/src/porcelain_admission.rs: validate_lifecycle` | source support | [One actor's diagnostics](RESPONSE.md#contract-diagnostics-actor) |
| `controller/src/porcelain_admission.rs: validate_lifecycle` | source support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/porcelain_native.rs: pub(super) fn validate` | source support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/porcelain_native.rs: pub(super) fn validate` | source support | [Integrity finding](RESPONSE.md#contract-diagnostics-issue) |
| `controller/src/request_patch.rs: parse_request` | source support | [Repeated members at each entry](REQUEST.md#contract-request-specimen-duplicate_keys) |
| `controller/src/request_patch.rs: request_contract_is_exact_and_required` | check support | [Direct compilation contexts](#contract-identity-public-direct) |
| `controller/src/request_patch.rs: request_contract_is_exact_and_required` | check support | [Controller request refusal](RESPONSE.md#contract-refusals-controller) |
| `controller/src/request_patch.rs: request_failure_path_components_use_utf8_bytes_and_withhold_the_whole_path` | check support | [Controller request refusal](RESPONSE.md#contract-refusals-controller) |
| `controller/src/request_patch.rs: request_failure_path_depth_retains_eight_and_withholds_nine` | check support | [Controller request refusal](RESPONSE.md#contract-refusals-controller) |
| `controller/src/request_patch.rs: validate_contract` | source support | [Direct compilation contexts](#contract-identity-public-direct) |
| `controller/src/request_patch.rs: validate_contract` | source support | [Controller request refusal](RESPONSE.md#contract-refusals-controller) |
| `controller/src/run_flow.rs: RequestFailureProjection` | source support | [Projected request refusal](RESPONSE.md#contract-refusals-projection) |
| `controller/src/run_flow.rs: RequestFailureProjection::Runner` | source support | [Projected request refusal](RESPONSE.md#contract-refusals-projection) |
| `controller/src/run_flow.rs: actor_fallback_checks` | source support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/run_flow.rs: actor_fallback_checks` | source support | [Per-actor fallback capture](RESPONSE.md#contract-policy-actor_check) |
| `controller/src/run_flow.rs: actor_fallback_uses_held_policy_objects_before_host_mode_admission` | check support | [Held input and file observation scope](RESPONSE.md#contract-dossier-collection-native_gap) |
| `controller/src/run_flow.rs: actor_policies` | source support | [Per-actor fallback capture](RESPONSE.md#contract-policy-actor_check) |
| `controller/src/run_flow.rs: admit_reply` | source support | [Decoded response collection bounds](RESPONSE.md#contract-diagnostics-execution-geometry) |
| `controller/src/run_flow.rs: admit_reply` | source support | [The controller envelope](RESPONSE.md#contract-envelope) |
| `controller/src/run_flow.rs: admit_reply` | source support | [Distinguish a stopped boundary](RESPONSE.md#contract-refusals-later-boundaries) |
| `controller/src/run_flow.rs: bad_request` | source support | [Controller request refusal](RESPONSE.md#contract-refusals-controller) |
| `controller/src/run_flow.rs: compiled_profile_labels_determine_the_public_admission_outcome` | check support | [A failed label check for run](RESPONSE.md#contract-profile-receipt-labels-failure) |
| `controller/src/run_flow.rs: complete_execution` | source support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/run_flow.rs: complete_execution` | source support | [The controller envelope](RESPONSE.md#contract-envelope) |
| `controller/src/run_flow.rs: control_spellings_are_their_keys_and_only_test_input_run_admits_them` | check support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/run_flow.rs: emitted_example_reaches_the_client_as_the_emitted_document` | check support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `controller/src/run_flow.rs: execution_envelopes_preserve_raw_evidence_and_emit_only_execution_fields` | check support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/run_flow.rs: fallback_compilation_is_requested_only_for_an_admitted_xpc_error` | check support | [Fallback helper capture](RESPONSE.md#contract-policy-fallback) |
| `controller/src/run_flow.rs: fallback_policy_check` | source support | [Fallback helper capture](RESPONSE.md#contract-policy-fallback) |
| `controller/src/run_flow.rs: finished_run_preserves_successful_and_failed_attempts` | check support | [The controller envelope](RESPONSE.md#contract-envelope) |
| `controller/src/run_flow.rs: fn controls_object` | source support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/run_flow.rs: fn parse_arguments` | source support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/run_flow.rs: fn run(` | source support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/run_flow.rs: fn run(args:` | source support | [Held input and file observation scope](RESPONSE.md#contract-dossier-collection-native_gap) |
| `controller/src/run_flow.rs: fn run(args:` | source support | [Shared definitions](#contract-identity-definitions) |
| `controller/src/run_flow.rs: fn run(args:` | source support | [Refusal correction workflows](RESPONSE.md#contract-refusals-examples-workflow) |
| `controller/src/run_flow.rs: fn run(args:` | source support | [Branch-local refusal precedence](RESPONSE.md#contract-refusals-request-compound_order) |
| `controller/src/run_flow.rs: integer_controls_pass_every_signed_64_bit_decimal_through_unchanged` | check support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/run_flow.rs: let actor_policies:` | source support | [Fallback helper capture](RESPONSE.md#contract-policy-fallback) |
| `controller/src/run_flow.rs: load_app_provenance` | source support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/run_flow.rs: malformed_control_syntax_is_refused_before_any_run_work` | check support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/run_flow.rs: malformed_phase_claims_withhold_projection_and_preserve_raw_reply` | check support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/run_flow.rs: parse_arguments` | source support | [Controller request refusal](RESPONSE.md#contract-refusals-controller) |
| `controller/src/run_flow.rs: pub(crate) fn admit_reply` | source support | [The controller checks carried labels](RESPONSE.md#contract-profile-receipt-labels) |
| `controller/src/run_flow.rs: pub(crate) fn admit_reply` | source support | [A failed label check for runner verify](RESPONSE.md#contract-profile-receipt-labels-verify_failure) |
| `controller/src/run_flow.rs: pub(crate) fn reply_contract` | source support | [The controller checks carried labels](RESPONSE.md#contract-profile-receipt-labels) |
| `controller/src/run_flow.rs: reader_definition_corpus_cross_readers` | check support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `controller/src/run_flow.rs: reader_definition_corpus_cross_readers` | check support | [Reader judgments](RESPONSE.md#contract-diagnostics-execution-reader_evidence) |
| `controller/src/run_flow.rs: reader_definition_corpus_cross_readers` | check support | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `controller/src/run_flow.rs: reply_contract` | source support | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `controller/src/run_flow.rs: strip_runner_selector` | source support | [Controller selection options](REQUEST.md#contract-request-options) |
| `controller/src/run_flow.rs: test_input_run_delivers_the_held_request_unchanged_and_the_controls_beside_it` | check support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/run_flow.rs: test_input_run_usage_refusals_invoke_no_client_and_read_no_app_root` | check support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/run_flow.rs: typed_completion_preserves_native_failure_beside_finished_summary` | check support | [The controller envelope](RESPONSE.md#contract-envelope) |
| `controller/src/run_flow.rs: validate_request_contract` | source support | [Specimen](REQUEST.md#contract-request-specimen) |
| `controller/src/runner_client.rs: RunnerClientRun` | source support | [Shared definitions](#contract-identity-definitions) |
| `controller/src/runner_client.rs: binary_reply_after_large_stdin_and_broken_pipe_preserves_delivery_precedence` | check support | [The controller envelope](RESPONSE.md#contract-envelope) |
| `controller/src/runner_client.rs: binary_reply_after_large_stdin_and_broken_pipe_preserves_delivery_precedence` | check support | [Delivery to the host](RESPONSE.md#contract-transport) |
| `controller/src/runner_client.rs: fn submission_arguments` | source support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/runner_client.rs: only_an_experimental_submission_names_a_controls_object` | check support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/runner_client.rs: parse_runner_client_output` | source support | [Distinguish a stopped boundary](RESPONSE.md#contract-refusals-later-boundaries) |
| `controller/src/runner_client.rs: parse_runner_client_output` | source support | [Delivery to the host](RESPONSE.md#contract-transport) |
| `controller/src/runner_client.rs: parse_runner_client_output` | source support | [Admit client and host observations](RESPONSE.md#contract-transport-client-admit) |
| `controller/src/runner_client.rs: pub fn failure` | source support | [The controller envelope](RESPONSE.md#contract-envelope) |
| `controller/src/runner_client.rs: pub fn fallback_eligible` | source support | [Fallback helper capture](RESPONSE.md#contract-policy-fallback) |
| `controller/src/runner_client.rs: retention_loss_precedes_decode_and_keeps_exact_prefix` | check support | [Delivery to the host](RESPONSE.md#contract-transport) |
| `controller/src/runner_client.rs: validate_capture` | source support | [Delivery to the host](RESPONSE.md#contract-transport) |
| `controller/src/runner_commands.rs: cmd_runner_install` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_commands.rs: cmd_runner_install` | source support | [Published installation state](RESPONSE.md#contract-installation-install-state_copy) |
| `controller/src/runner_commands.rs: cmd_runner_reconcile` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_commands.rs: cmd_runner_validate` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_commands.rs: cmd_runner_validate` | source support | [Entitlement read errors and summary counts](RESPONSE.md#contract-installation-commands-entitlement_errors) |
| `controller/src/runner_commands.rs: cmd_runner_verify` | source support | [Decoded response collection bounds](RESPONSE.md#contract-diagnostics-execution-geometry) |
| `controller/src/runner_commands.rs: cmd_runner_verify` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_commands.rs: cmd_runner_verify` | source support | [Pending verification](RESPONSE.md#contract-installation-commands-pending_verify) |
| `controller/src/runner_commands.rs: cmd_runner_verify` | source support | [Request delivery failure](RESPONSE.md#contract-installation-verify-delivery_failure) |
| `controller/src/runner_commands.rs: cmd_runner_verify` | source support | [Select the verification operation result](RESPONSE.md#contract-installation-verify-select) |
| `controller/src/runner_commands.rs: cmd_runner_verify` | source support | [The controller checks carried labels](RESPONSE.md#contract-profile-receipt-labels) |
| `controller/src/runner_commands.rs: cmd_runner_verify` | source support | [A failed label check for runner verify](RESPONSE.md#contract-profile-receipt-labels-verify_failure) |
| `controller/src/runner_manager.rs: RunnerRegistry` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: atomic_registry_replace_preserves_old_open_readers_and_failed_write` | check support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: bootout_waits_out_launchd_teardown_within_the_budget` | check support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: caller_facing_parse_rejects_legacy_aliases` | check support | [kind](RESPONSE.md#contract-installation-runner-kind) |
| `controller/src/runner_manager.rs: for RunnerKind` | source support | [kind](RESPONSE.md#contract-installation-runner-kind) |
| `controller/src/runner_manager.rs: historical_flattened_cleanup_remains_readable_and_rewrites_with_nested_runner` | check support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: install_failure_boundaries_preserve_observed_pending_state` | check support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: install_record` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: legacy_debuggable_kind_deserializes_as_byoxpc` | check support | [kind](RESPONSE.md#contract-installation-runner-kind) |
| `controller/src/runner_manager.rs: legacy_machme_kind_deserializes_as_byoxpc` | check support | [kind](RESPONSE.md#contract-installation-runner-kind) |
| `controller/src/runner_manager.rs: legacy_metadata_survives_unrelated_writes_and_pending_cleanup` | check support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: plist_ownership` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: plist_ownership` | source support | [Classify cleanup ownership](RESPONSE.md#contract-installation-commands-ownership) |
| `controller/src/runner_manager.rs: read_back` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: record_location` | source support | [Classify cleanup ownership](RESPONSE.md#contract-installation-commands-ownership) |
| `controller/src/runner_manager.rs: registry_save_refuses_duplicate_known_metadata_before_publication` | check support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: remove_record` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: remove_record` | source support | [Retained recovery account](RESPONSE.md#contract-installation-cleanup-retention) |
| `controller/src/runner_manager.rs: save_registry` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: service_after_bootout` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: service_ownership` | source support | [Managing runners](RESPONSE.md#contract-installation) |
| `controller/src/runner_manager.rs: service_ownership` | source support | [Classify cleanup ownership](RESPONSE.md#contract-installation-commands-ownership) |
| `controller/src/runner_manager.rs: service_ownership` | source support | [Classify the typed service observation](RESPONSE.md#contract-installation-service-classify) |
| `controller/src/runner_manager.rs: validate_record` | source support | [Entitlement read errors and summary counts](RESPONSE.md#contract-installation-commands-entitlement_errors) |
| `controller/src/runner_manager.rs: validation_keeps_entitlement_errors_distinct_from_failed_read_back` | check support | [Entitlement read errors and summary counts](RESPONSE.md#contract-installation-commands-entitlement_errors) |
| `controller/src/runner_select.rs: RunnerProvenance` | source support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/runner_select.rs: RunnerSelector` | source support | [Nested runner selector](REQUEST.md#contract-request-selector) |
| `controller/src/runner_select.rs: malformed_selection_never_falls_back_or_discards_entitlements` | check support | [Controller selection options](REQUEST.md#contract-request-options) |
| `controller/src/runner_select.rs: nested_runner_takes_precedence_over_legacy_top_level` | check support | [Controller selection options](REQUEST.md#contract-request-options) |
| `controller/src/runner_select.rs: optional_nulls_and_explicit_nested_empty_entitlements_have_defined_meanings` | check support | [Controller selection options](REQUEST.md#contract-request-options) |
| `controller/src/runner_select.rs: parse_runner_selector_value` | source support | [Controller selection options](REQUEST.md#contract-request-options) |
| `controller/src/runner_select.rs: parse_runner_selector_value` | source support | [Nested runner selector](REQUEST.md#contract-request-selector) |
| `controller/src/sbpl_imports.rs: closure_hash_excludes_unresolved_imports` | check support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/sbpl_imports.rs: closure_hash_is_order_invariant` | check support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/sbpl_imports.rs: compute_closure_hash` | source support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/sbpl_imports.rs: compute_closure_hash` | source support | [Literal import inventory](RESPONSE.md#contract-policy-imports) |
| `controller/src/sbpl_imports.rs: read_regular_file` | source support | [Literal import inventory](RESPONSE.md#contract-policy-imports) |
| `controller/src/sbpl_imports.rs: resolve_import_path` | source support | [Held input and file observation scope](RESPONSE.md#contract-dossier-collection-native_gap) |
| `controller/src/sbpl_imports.rs: resolve_import_path` | source support | [Literal import evidence scope](RESPONSE.md#contract-policy-imports-native_import_agreement) |
| `controller/src/sbpl_imports.rs: resolve_imports` | source support | [Specimen dossier](RESPONSE.md#contract-dossier) |
| `controller/src/sbpl_imports.rs: resolve_imports` | source support | [Literal import inventory](RESPONSE.md#contract-policy-imports) |
| `controller/src/test_input.rs: argument_target_and_identity_refusals_write_nothing` | check support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/src/test_input.rs: complete_publication_requires_all_writes_and_flush` | check support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/src/test_input.rs: fn emit_template` | source support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/src/test_input.rs: fn render_template` | source support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/src/test_input.rs: fn render_template` | source support | [Developer read body](REQUEST.md#contract-request-specimen-read_input) |
| `controller/src/test_input.rs: malformed_templates_refuse_before_output` | check support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/src/test_input.rs: members_outside_the_assigned_positions_are_published_as_embedded` | check support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/src/test_input.rs: pub fn cmd_test_input` | source support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `controller/src/test_input.rs: pub fn cmd_test_input` | source support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/src/test_input.rs: read_input_preserves_target_identity_and_fixed_workload` | check support | [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input) |
| `controller/src/utils.rs: run_with_stdin` | source support | [Delivery to the host](RESPONSE.md#contract-transport) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: ABI identity mismatch` | source support | [Other identities](#contract-identity-other) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: PW_ATTEMPT_FILE_READ_FRESH` | source support | [Observe fresh descriptors](RESPONSE.md#contract-steps-assessment-fresh) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_extension_consume_actor` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_extension_consume_actor` | source support | [Extension event](RESPONSE.md#contract-extensions-event) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_extension_issue` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_extension_issue` | source support | [Extension event](RESPONSE.md#contract-extensions-event) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_extension_issue` | source support | [Extension experiments](REQUEST.md#contract-extensions-examples) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_file_create` | source support | [Refusal and unavailable-prediction examples](RESPONSE.md#contract-refusals-examples) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_file_open_read` | source support | [Attempt request](REQUEST.md#contract-probes-attempt) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_file_open_write` | source support | [Shared definitions](#contract-identity-definitions) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_file_read_fresh` | source support | [Extension experiments](REQUEST.md#contract-extensions-examples) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_file_read_fresh` | source support | [Execute a declared operation](REQUEST.md#contract-probes-attempt-execute) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_file_read_fresh` | source support | [Project the fresh-read aggregate](RESPONSE.md#contract-steps-assessment-fresh_read_aggregate) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_file_write_fresh` | source support | [Attempt request](REQUEST.md#contract-probes-attempt) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_file_write_fresh` | source support | [Execute a declared operation](REQUEST.md#contract-probes-attempt-execute) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_file_write_fresh` | source support | [Project the fresh-write aggregate](RESPONSE.md#contract-steps-assessment-fresh_write_aggregate) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_sysctl_read` | source support | [Attempt request](REQUEST.md#contract-probes-attempt) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: capture_observed_path` | source support | [Predictions, attempts and comparison](RESPONSE.md#contract-steps) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: erase_authority` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: if (hdr->actor_mode == PW_ACTOR_MODE_UNAPPLIED)` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: kill_before_publish_slot` | source support | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: pw_capture_profile` | source support | [Receipt](RESPONSE.md#contract-profile-receipt) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: sandbox_compile_string(policy_buf` | source support | [Worker and helper compile classification](REQUEST.md#contract-policy-spec-compile_classification) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: sandbox_set_param` | source support | [Worker policy input](REQUEST.md#contract-policy-spec) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: static void prepare_authority` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `controller/tools/pw_probe_runner/pw_probe_runner.c: write_ready_byte` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `controller/tools/pw_probe_runner/pw_probe_runner_abi.h: PW_SHM_CHILD_OUTPUT_BYTES` | source support | [Predictions, attempts and comparison](RESPONSE.md#contract-steps) |
| `controller/tools/pw_probe_runner/pw_probe_runner_abi.h: PW_SHM_DIAGNOSTIC_BYTES` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `controller/tools/pw_probe_runner/pw_profile_capture.h: pw_capture_profile` | source support | [Receipt](RESPONSE.md#contract-profile-receipt) |
| `controller/tools/pw_probe_runner/pw_worker_exec.h: attempt_exec_spawn` | source support | [Attempt request](REQUEST.md#contract-probes-attempt) |
| `controller/tools/pw_probe_runner/pw_worker_exec.h: stdout_overflow` | source support | [Predictions, attempts and comparison](RESPONSE.md#contract-steps) |
| `controller/tools/pw_probe_runner/pw_worker_timing.h: PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT` | source support | [Attempt request](REQUEST.md#contract-probes-attempt) |
| `controller/tools/pw_probe_runner/pw_worker_timing.h: PW_EXEC_REAP_GRACE_MS` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `controller/tools/pw_probe_runner/pw_worker_timing.h: pw_timing_setup` | source support | [Attempt request](REQUEST.md#contract-probes-attempt) |
| `controller/tools/sb_api_validator/sb_api_validator.c: SANDBOX_CHECK_NO_REPORT` | source support | [Shared definitions](#contract-identity-definitions) |
| `controller/tools/sb_api_validator/sb_api_validator.c: emit_verdict` | source support | [Validator query and reply lines](ARCHITECTURE.md#contract-wire-validator) |
| `controller/tools/sb_api_validator/sb_api_validator.c: int main(` | source support | [Direct validator commands](RESPONSE.md#contract-wire-standalone) |
| `controller/tools/sb_api_validator/sb_api_validator.c: int main(` | source support | [Run one native query](RESPONSE.md#contract-wire-standalone-query) |
| `controller/tools/sb_api_validator/sb_api_validator.c: parse_pid` | source support | [Direct validator commands](RESPONSE.md#contract-wire-standalone) |
| `controller/tools/sb_api_validator/sb_api_validator.c: parse_probe_line` | source support | [Validator query and reply lines](ARCHITECTURE.md#contract-wire-validator) |
| `controller/tools/sb_api_validator/sb_api_validator.c: parse_probe_line` | source support | [Repeated native query keys](ARCHITECTURE.md#contract-wire-validator-duplicate_keys) |
| `controller/tools/sb_api_validator/sb_api_validator.c: print_error` | source support | [Direct validator commands](RESPONSE.md#contract-wire-standalone) |
| `controller/tools/sb_api_validator/sb_api_validator.c: resolve_filter_type_id` | source support | [Direct validator commands](RESPONSE.md#contract-wire-standalone) |
| `controller/tools/sb_api_validator/sb_api_validator.c: resolve_filter_type_id` | source support | [Direct and batch validator meanings](RESPONSE.md#contract-wire-standalone-meaning) |
| `controller/tools/sb_api_validator/sb_api_validator.c: resolve_filter_type_id` | source support | [Run one native query](RESPONSE.md#contract-wire-standalone-query) |
| `controller/tools/sb_api_validator/sb_api_validator.c: run_batch` | source support | [Repeated native query keys](ARCHITECTURE.md#contract-wire-validator-duplicate_keys) |
| `docs/build.json: sig_validator` | source support | [Direct validator commands](RESPONSE.md#contract-wire-standalone) |
| `docs/build_contract.py: def identity` | source support | [Reviewing a development specimen](#contract-identity-surfaces-development_review) |
| `docs/build_contract.py: identity` | source support | [Build derivation](#contract-identity-public-derive) |
| `docs/build_contract.py: swift` | source support | [Host producer identification](RESPONSE.md#contract-identity-producer) |
| `docs/contract/00-identity.surface.md` | authored declaration | [Build identification](RESPONSE.md#contract-identity-build) |
| `docs/contract/00-identity.surface.md` | authored declaration | [Shared definitions](#contract-identity-definitions) |
| `docs/contract/00-identity.surface.md` | authored declaration | [Other identities](#contract-identity-other) |
| `docs/contract/00-identity.surface.md` | authored declaration | [Host producer identification](RESPONSE.md#contract-identity-producer) |
| `docs/contract/00-identity.surface.md` | authored declaration | [Public identity](#contract-identity-public) |
| `docs/contract/00-identity.surface.md` | authored declaration | [Surface history](#contract-identity-surfaces) |
| `docs/contract/00-identity.surface.md` | authored declaration | [Version reporting](RESPONSE.md#contract-identity-version) |
| `docs/contract/10-request.surface.md` | authored declaration | [Controller selection options](REQUEST.md#contract-request-options) |
| `docs/contract/10-request.surface.md` | authored declaration | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `docs/contract/10-request.surface.md` | authored declaration | [Nested runner selector](REQUEST.md#contract-request-selector) |
| `docs/contract/10-request.surface.md` | authored declaration | [Specimen](REQUEST.md#contract-request-specimen) |
| `docs/contract/11-policy.surface.md` | authored declaration | [Per-actor fallback capture](RESPONSE.md#contract-policy-actor_check) |
| `docs/contract/11-policy.surface.md` | authored declaration | [Augment resolution](REQUEST.md#contract-policy-augments) |
| `docs/contract/11-policy.surface.md` | authored declaration | [Compiler-helper data](RESPONSE.md#contract-policy-check_data) |
| `docs/contract/11-policy.surface.md` | authored declaration | [Last native compile stage](RESPONSE.md#contract-policy-compile) |
| `docs/contract/11-policy.surface.md` | authored declaration | [Fallback helper capture](RESPONSE.md#contract-policy-fallback) |
| `docs/contract/11-policy.surface.md` | authored declaration | [Compiler-helper policy](REQUEST.md#contract-policy-helper_policy) |
| `docs/contract/11-policy.surface.md` | authored declaration | [Standalone compiler-helper request](REQUEST.md#contract-policy-helper_request) |
| `docs/contract/11-policy.surface.md` | authored declaration | [Literal import inventory](RESPONSE.md#contract-policy-imports) |
| `docs/contract/11-policy.surface.md` | authored declaration | [Worker policy input](REQUEST.md#contract-policy-spec) |
| `docs/contract/12-probes.surface.md` | authored declaration | [Attempt request](REQUEST.md#contract-probes-attempt) |
| `docs/contract/12-probes.surface.md` | authored declaration | [Sandbox filter](REQUEST.md#contract-probes-filter) |
| `docs/contract/12-probes.surface.md` | authored declaration | [Sandbox query](REQUEST.md#contract-probes-query) |
| `docs/contract/12-probes.surface.md` | authored declaration | [Paired probe](REQUEST.md#contract-probes-step) |
| `docs/contract/13-actors.surface.md` | authored declaration | [Phase action variants](REQUEST.md#contract-actors-action) |
| `docs/contract/13-actors.surface.md` | authored declaration | [Actor declaration](REQUEST.md#contract-actors-actor) |
| `docs/contract/13-actors.surface.md` | authored declaration | [Termination dependency](REQUEST.md#contract-actors-after_termination) |
| `docs/contract/13-actors.surface.md` | authored declaration | [Phase declaration](REQUEST.md#contract-actors-phase) |
| `docs/contract/13-actors.surface.md` | authored declaration | [Actor sandbox declaration](REQUEST.md#contract-actors-sandbox) |
| `docs/contract/14-extensions.surface.md` | authored declaration | [Extension action](REQUEST.md#contract-extensions-action) |
| `docs/contract/14-extensions.surface.md` | authored declaration | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `docs/contract/14-extensions.surface.md` | authored declaration | [Delivery resource](RESPONSE.md#contract-extensions-delivery) |
| `docs/contract/14-extensions.surface.md` | authored declaration | [Extension event](RESPONSE.md#contract-extensions-event) |
| `docs/contract/14-extensions.surface.md` | authored declaration | [Extension experiments](REQUEST.md#contract-extensions-examples) |
| `docs/contract/14-extensions.surface.md` | authored declaration | [Handle resource](RESPONSE.md#contract-extensions-handle) |
| `docs/contract/14-extensions.surface.md` | authored declaration | [Extension operation](REQUEST.md#contract-extensions-operation) |
| `docs/contract/14-extensions.surface.md` | authored declaration | [Resource tables](RESPONSE.md#contract-extensions-resources) |
| `docs/contract/14-extensions.surface.md` | authored declaration | [Token resource](RESPONSE.md#contract-extensions-token) |
| `docs/contract/14-extensions.surface.md` | authored declaration | [Host transfer observation](RESPONSE.md#contract-extensions-transfer) |
| `docs/contract/15-refusals.surface.md` | authored declaration | [Capacity refusal](RESPONSE.md#contract-refusals-admission) |
| `docs/contract/15-refusals.surface.md` | authored declaration | [Controller request refusal](RESPONSE.md#contract-refusals-controller) |
| `docs/contract/15-refusals.surface.md` | authored declaration | [Refusal and unavailable-prediction examples](RESPONSE.md#contract-refusals-examples) |
| `docs/contract/15-refusals.surface.md` | authored declaration | [Failures after invocation](RESPONSE.md#contract-refusals-later) |
| `docs/contract/15-refusals.surface.md` | authored declaration | [Projected request refusal](RESPONSE.md#contract-refusals-projection) |
| `docs/contract/15-refusals.surface.md` | authored declaration | [Runner request refusal](RESPONSE.md#contract-refusals-request) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Acquisition attempt](RESPONSE.md#contract-transport-acquisition) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Caller authorization](ARCHITECTURE.md#contract-transport-authorization) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Client capture](RESPONSE.md#contract-transport-capture) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Controller observation of the client process](RESPONSE.md#contract-transport-client) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Host control reply](ARCHITECTURE.md#contract-transport-control) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Retained control observation](RESPONSE.md#contract-transport-control_observation) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Reservation and execution](ARCHITECTURE.md#contract-transport-delivery) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Client error](RESPONSE.md#contract-transport-error) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Submission observation](RESPONSE.md#contract-transport-invocation) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Rejected client stdout](RESPONSE.md#contract-transport-rejected) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Request stdin delivery](RESPONSE.md#contract-transport-request_delivery) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Reservation request](ARCHITECTURE.md#contract-transport-reservation) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Retained host reply](RESPONSE.md#contract-transport-retained_reply) |
| `docs/contract/20-transport.surface.md` | authored declaration | [Transport alternatives](RESPONSE.md#contract-transport-transport_value) |
| `docs/contract/21-wire.surface.md` | authored declaration | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `docs/contract/21-wire.surface.md` | authored declaration | [Direct validator commands](RESPONSE.md#contract-wire-standalone) |
| `docs/contract/21-wire.surface.md` | authored declaration | [Direct argument error](RESPONSE.md#contract-wire-standalone_error) |
| `docs/contract/21-wire.surface.md` | authored declaration | [Direct native result](RESPONSE.md#contract-wire-standalone_result) |
| `docs/contract/21-wire.surface.md` | authored declaration | [Direct PID status](RESPONSE.md#contract-wire-standalone_status) |
| `docs/contract/21-wire.surface.md` | authored declaration | [Validator query and reply lines](ARCHITECTURE.md#contract-wire-validator) |
| `docs/contract/30-reply.surface.md` | authored declaration | [Reporting failure](RESPONSE.md#contract-reply-failure) |
| `docs/contract/30-reply.surface.md` | authored declaration | [Execution record](RESPONSE.md#contract-reply-record) |
| `docs/contract/31-steps.surface.md` | authored declaration | [Interpreting the observations](RESPONSE.md#contract-steps-assessment) |
| `docs/contract/31-steps.surface.md` | authored declaration | [Attempt-channel result](RESPONSE.md#contract-steps-attempt) |
| `docs/contract/31-steps.surface.md` | authored declaration | [Attempt path observations](RESPONSE.md#contract-steps-attempt_paths) |
| `docs/contract/31-steps.surface.md` | authored declaration | [Comparison assessment](RESPONSE.md#contract-steps-comparison) |
| `docs/contract/31-steps.surface.md` | authored declaration | [Fresh-descriptor read](RESPONSE.md#contract-steps-fresh_read) |
| `docs/contract/31-steps.surface.md` | authored declaration | [Fresh-descriptor write or creation](RESPONSE.md#contract-steps-fresh_write) |
| `docs/contract/31-steps.surface.md` | authored declaration | [File identity observation](RESPONSE.md#contract-steps-identity) |
| `docs/contract/31-steps.surface.md` | authored declaration | [Collection and release observations](RESPONSE.md#contract-steps-ordering) |
| `docs/contract/31-steps.surface.md` | authored declaration | [Query-channel result](RESPONSE.md#contract-steps-query) |
| `docs/contract/31-steps.surface.md` | authored declaration | [Query path observations](RESPONSE.md#contract-steps-query_paths) |
| `docs/contract/31-steps.surface.md` | authored declaration | [File metadata observation](RESPONSE.md#contract-steps-stat) |
| `docs/contract/31-steps.surface.md` | authored declaration | [Probe result](RESPONSE.md#contract-steps-step) |
| `docs/contract/31-steps.surface.md` | authored declaration | [Accepted validator record](RESPONSE.md#contract-steps-verdict) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Validator query association](RESPONSE.md#contract-lifecycle-association_issue) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Per-attempt lifecycle projection](RESPONSE.md#contract-lifecycle-attempt) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Lifecycle claim](RESPONSE.md#contract-lifecycle-claim) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Lifecycle answer value](RESPONSE.md#contract-lifecycle-claim_value) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Rejected validator frame](RESPONSE.md#contract-lifecycle-decode_fault) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Worker diagnostic](RESPONSE.md#contract-lifecycle-diagnostic) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Canonical worker disposition](RESPONSE.md#contract-lifecycle-disposition) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Spawned-command observation](RESPONSE.md#contract-lifecycle-exec) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Exec cleanup](RESPONSE.md#contract-lifecycle-exec_cleanup) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Exec collection](RESPONSE.md#contract-lifecycle-exec_collection) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Exec leader reap](RESPONSE.md#contract-lifecycle-exec_reap) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Exec signal request](RESPONSE.md#contract-lifecycle-exec_signal) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Exec stream observation](RESPONSE.md#contract-lifecycle-exec_stream) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Exec leader wait result](RESPONSE.md#contract-lifecycle-exec_wait) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Terminal worker failure](RESPONSE.md#contract-lifecycle-failure) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Measured host wait](RESPONSE.md#contract-lifecycle-host_wait) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Lifecycle conflict](RESPONSE.md#contract-lifecycle-issue) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Owned child ending](RESPONSE.md#contract-lifecycle-owned_reap) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Worker policy receipt](RESPONSE.md#contract-lifecycle-policy_read) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Worker progress](RESPONSE.md#contract-lifecycle-progress) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Readiness-write result](RESPONSE.md#contract-lifecycle-readiness) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Owned-ending reference](RESPONSE.md#contract-lifecycle-reap_reference) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Run lifecycle questions](RESPONSE.md#contract-lifecycle-run_questions) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Native spawn failure](RESPONSE.md#contract-lifecycle-spawn_failure) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Step lifecycle account](RESPONSE.md#contract-lifecycle-step) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Step lifecycle questions](RESPONSE.md#contract-lifecycle-step_questions) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Host termination request](RESPONSE.md#contract-lifecycle-termination) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Policy-pipe write error](RESPONSE.md#contract-lifecycle-transfer_error) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Policy-pipe timeout](RESPONSE.md#contract-lifecycle-transfer_timeout) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Validator subprocess](RESPONSE.md#contract-lifecycle-validator) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Failed host wait](RESPONSE.md#contract-lifecycle-wait_error) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Worker subprocess](RESPONSE.md#contract-lifecycle-worker) |
| `docs/contract/32-lifecycle.surface.md` | authored declaration | [Worker publication snapshot](RESPONSE.md#contract-lifecycle-worker_evidence) |
| `docs/contract/33-actor_evidence.surface.md` | authored declaration | [Host activation observation](RESPONSE.md#contract-actor_evidence-activation) |
| `docs/contract/33-actor_evidence.surface.md` | authored declaration | [Actor process account](RESPONSE.md#contract-actor_evidence-actor) |
| `docs/contract/33-actor_evidence.surface.md` | authored declaration | [Application assessment](RESPONSE.md#contract-actor_evidence-application) |
| `docs/contract/33-actor_evidence.surface.md` | authored declaration | [Termination dependency](RESPONSE.md#contract-actor_evidence-gate) |
| `docs/contract/33-actor_evidence.surface.md` | authored declaration | [Actor launch context](RESPONSE.md#contract-actor_evidence-launch) |
| `docs/contract/33-actor_evidence.surface.md` | authored declaration | [Observation sequences](RESPONSE.md#contract-actor_evidence-owned_endings) |
| `docs/contract/33-actor_evidence.surface.md` | authored declaration | [Phase collection and execution](RESPONSE.md#contract-actor_evidence-phase) |
| `docs/contract/33-actor_evidence.surface.md` | authored declaration | [Schedule account](RESPONSE.md#contract-actor_evidence-schedule) |
| `docs/contract/33-actor_evidence.surface.md` | authored declaration | [Visit intervals](RESPONSE.md#contract-actor_evidence-timing) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Actor equipment selection](RESPONSE.md#contract-equipment-actor) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Host authority scopes](RESPONSE.md#contract-equipment-authority_host) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Authority operation cell](RESPONSE.md#contract-equipment-authority_operation) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Authority operation scope](RESPONSE.md#contract-equipment-authority_scope) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Authority setup account](RESPONSE.md#contract-equipment-authority_setup) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Static worker binding](RESPONSE.md#contract-equipment-binding) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Unresolved shared-memory name](RESPONSE.md#contract-equipment-cleanup_reference) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Entitlement read-back](RESPONSE.md#contract-equipment-entitlements) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Equipment diagnostic](RESPONSE.md#contract-equipment-error) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Live actor inspection](RESPONSE.md#contract-equipment-execution) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Observed service inventory](RESPONSE.md#contract-equipment-inventory) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Sealed equipment inventory file](RESPONSE.md#contract-equipment-manifest) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Inventory worker row](RESPONSE.md#contract-equipment-manifest_worker) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Live inspection call](RESPONSE.md#contract-equipment-native_observation) |
| `docs/contract/34-equipment.surface.md` | authored declaration | [Actor preparation refusal](RESPONSE.md#contract-equipment-preparation_failure) |
| `docs/contract/35-profile.surface.md` | authored declaration | [Receipt](RESPONSE.md#contract-profile-receipt) |
| `docs/contract/40-envelope.surface.md` | authored declaration | [Run payload](RESPONSE.md#contract-envelope-data) |
| `docs/contract/40-envelope.surface.md` | authored declaration | [Compiler-helper envelope](RESPONSE.md#contract-envelope-helper) |
| `docs/contract/40-envelope.surface.md` | authored declaration | [Operation result](RESPONSE.md#contract-envelope-result) |
| `docs/contract/40-envelope.surface.md` | authored declaration | [Run envelope](RESPONSE.md#contract-envelope-run) |
| `docs/contract/41-diagnostics.surface.md` | authored declaration | [One actor's diagnostics](RESPONSE.md#contract-diagnostics-actor) |
| `docs/contract/41-diagnostics.surface.md` | authored declaration | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `docs/contract/41-diagnostics.surface.md` | authored declaration | [Integrity finding](RESPONSE.md#contract-diagnostics-issue) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [Actor policy dossier](RESPONSE.md#contract-dossier-actor) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [App provenance](RESPONSE.md#contract-dossier-app) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [Augmentation observation](RESPONSE.md#contract-dossier-augmentation) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [Selected binary observations](RESPONSE.md#contract-dossier-binaries) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [One selected binary](RESPONSE.md#contract-dossier-binary) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [Collection boundaries](RESPONSE.md#contract-dossier-collection) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [Controller host context](RESPONSE.md#contract-dossier-host) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [One import observation](RESPONSE.md#contract-dossier-import_record) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [Import scan](RESPONSE.md#contract-dossier-imports) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [One verification failure](RESPONSE.md#contract-dossier-mismatch) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [Policy dossier](RESPONSE.md#contract-dossier-policy) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [Selected runner provenance](RESPONSE.md#contract-dossier-runner) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [Run dossier](RESPONSE.md#contract-dossier-specimen) |
| `docs/contract/42-dossier.surface.md` | authored declaration | [Manifest hash verification](RESPONSE.md#contract-dossier-verification) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Unregistered candidate](RESPONSE.md#contract-installation-candidate) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Removal result](RESPONSE.md#contract-installation-cleanup) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Current cleanup observation](RESPONSE.md#contract-installation-cleanup_observation) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Service teardown polling](RESPONSE.md#contract-installation-cleanup_wait) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Command boundaries](RESPONSE.md#contract-installation-commands) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Entitlement observation](RESPONSE.md#contract-installation-entitlements) |
| `docs/contract/50-installation.surface.md` | authored declaration | [One validation failure](RESPONSE.md#contract-installation-failure) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Reconciliation inspection error](RESPONSE.md#contract-installation-inspection_error) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Installation result](RESPONSE.md#contract-installation-install) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Unmatched lookup](RESPONSE.md#contract-installation-not_found) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Recorded cleanup ownership](RESPONSE.md#contract-installation-ownership) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Retained cleanup transaction](RESPONSE.md#contract-installation-pending_cleanup) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Observed plist](RESPONSE.md#contract-installation-plist) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Reconciliation result](RESPONSE.md#contract-installation-reconcile) |
| `docs/contract/50-installation.surface.md` | authored declaration | [One recorded reconciliation](RESPONSE.md#contract-installation-reconcile_record) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Runner registry](RESPONSE.md#contract-installation-registry) |
| `docs/contract/50-installation.surface.md` | authored declaration | [One runner record](RESPONSE.md#contract-installation-runner) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Observed service](RESPONSE.md#contract-installation-service) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Signature observation](RESPONSE.md#contract-installation-signature) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Validation result](RESPONSE.md#contract-installation-validate) |
| `docs/contract/50-installation.surface.md` | authored declaration | [Verification result](RESPONSE.md#contract-installation-verify) |
| `docs/contract/runtime.py: check` | source support | [Deriving the history table](#contract-identity-surfaces-derive) |
| `docs/contract/runtime.py: release_tags` | source support | [Deriving the history table](#contract-identity-surfaces-derive) |
| `docs/contract/runtime.py: require_available_history` | source support | [Deriving the history table](#contract-identity-surfaces-derive) |
| `docs/contract/runtime.py: stamps` | source support | [Deriving the history table](#contract-identity-surfaces-derive) |
| `docs/generate_porcelain.py: rust` | source support | [Response encoding](ARCHITECTURE.md#contract-wire) |
| `docs/generate_porcelain.py: wire_identity` | source support | [Other identities](#contract-identity-other) |
| `docs/generate_porcelain.py: wire_identity` | source support | [Response encoding](ARCHITECTURE.md#contract-wire) |
| `docs/generate_worker_identity.py: identity` | source support | [Other identities](#contract-identity-other) |
| `docs/source_identity.py: source_paths` | source support | [Build derivation](#contract-identity-public-derive) |
| `example.document` | interface association; see the partial join | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `result.admitted_finished` | interface association; see the partial join | [Admitted finished outcome](RESPONSE.md#contract-envelope-data-select-finished) |
| `result.admitted_other` | interface association; see the partial join | [Other admitted outcome](RESPONSE.md#contract-envelope-data-select-other) |
| `result.local_request_refusal` | interface association; see the partial join | [Selected request refusal](RESPONSE.md#contract-refusals-controller-consequence-request_refusal) |
| `result.tool_failure` | interface association; see the partial join | [Selected tool failure](RESPONSE.md#contract-refusals-controller-consequence-tool_failure) |
| `run.control.validator_executable_path` | interface association; see the partial join | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `run.control.validator_io_timeout_ms` | interface association; see the partial join | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `run.control.validator_total_timeout_ms` | interface association; see the partial join | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `run.control.worker_kill_before_publish_slot` | interface association; see the partial join | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `run.control.worker_post_apply_hang_ms` | interface association; see the partial join | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `run.control.worker_post_apply_kill_signal` | interface association; see the partial join | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `run.control.worker_pre_ready_hang_ms` | interface association; see the partial join | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `run.control.worker_timeout_ms` | interface association; see the partial join | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `run.option.runner_mode` | interface association; see the partial join | [Selector precedence](REQUEST.md#contract-request-options-precedence) |
| `runner/Clients/PWRunnerClient/PWRunnerClientSession.swift: PWRunnerClientSession` | source support | [Delivery to the host](RESPONSE.md#contract-transport) |
| `runner/Clients/PWRunnerClient/PWRunnerClientSession.swift: reservationReply` | source support | [Transport evidence scope](ARCHITECTURE.md#contract-transport-delivery-live_evidence) |
| `runner/Clients/PWRunnerClient/PWRunnerClientSession.swift: submitExperiment` | source support | [Experimental submission](REQUEST.md#contract-request-overrides-experimental) |
| `runner/Services/PWRunner/Info.plist: PWRunnerRequireSignedCaller` | source support | [Caller authorization](ARCHITECTURE.md#contract-transport-authorization) |
| `runner/Sources/PWRunnerCore/ActorEquipment.swift: ActorEquipmentPreparation` | source support | [Equipment and authority setup](RESPONSE.md#contract-equipment) |
| `runner/Sources/PWRunnerCore/ActorEquipment.swift: ActorEquipmentPreparation` | source support | [Static worker binding](RESPONSE.md#contract-equipment-binding) |
| `runner/Sources/PWRunnerCore/ActorEquipment.swift: bindOne` | source support | [Packaged bound-row equalities](RESPONSE.md#contract-equipment-binding-bound_values) |
| `runner/Sources/PWRunnerCore/ActorEquipment.swift: guard cdhash.count == 20` | source support | [Other identities](#contract-identity-other) |
| `runner/Sources/PWRunnerCore/ActorEquipment.swift: inspect` | source support | [Inspection result eligibility](RESPONSE.md#contract-equipment-execution-eligibility) |
| `runner/Sources/PWRunnerCore/ActorEquipment.swift: inspect` | source support | [Live-inspection evidence limit](RESPONSE.md#contract-equipment-execution-live_evidence) |
| `runner/Sources/PWRunnerCore/ActorEquipment.swift: private func prepare` | source support | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `runner/Sources/PWRunnerCore/ActorEquipment.swift: struct ActorEquipmentManifest` | source support | [Other identities](#contract-identity-other) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: PWRunnerTransferRecord` | source support | [Host transfer observation](RESPONSE.md#contract-extensions-transfer) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: actorApplicationAssessment` | source support | [Actor declaration](REQUEST.md#contract-actors-actor) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: actorPreparationRefusal` | source support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: actorPreparationRefusal` | source support | [Equipment and authority setup](RESPONSE.md#contract-equipment) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: actorPreparationRefusal` | source support | [Preparation refusal contents](RESPONSE.md#contract-equipment-preparation_failure-retain) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: assembleActorReply` | source support | [Actor and phase evidence](RESPONSE.md#contract-actor_evidence) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: assembleActorReply` | source support | [Extension event](RESPONSE.md#contract-extensions-event) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: assembleActorReply` | source support | [Project a published issue result](RESPONSE.md#contract-extensions-event-issue_projection) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: assembleActorReply` | source support | [Extension experiments](REQUEST.md#contract-extensions-examples) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: assembleActorReply` | source support | [Source acknowledgement association](RESPONSE.md#contract-extensions-transfer-source_association) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: assembleActorReply` | source support | [Project actor canonical step claims](RESPONSE.md#contract-lifecycle-disposition-actor_projection) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: assembleActorReply` | source support | [Project ordinary canonical step claims](RESPONSE.md#contract-lifecycle-disposition-ordinary_projection) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: collectionRemainingNs` | source support | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: deliveryRecords` | source support | [Delivery resource](RESPONSE.md#contract-extensions-delivery) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: handleRecords` | source support | [Handle resource](RESPONSE.md#contract-extensions-handle) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: if !plan.authorityRequired { authority = nil; return }` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: inspectionDeadline` | source support | [Equipment and authority setup](RESPONSE.md#contract-equipment) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: runActors` | source support | [Live-inspection evidence limit](RESPONSE.md#contract-equipment-execution-live_evidence) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: runActors` | source support | [Preparation refusal contents](RESPONSE.md#contract-equipment-preparation_failure-retain) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: runActors` | source support | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: runActors` | source support | [worker_timeout_ms](REQUEST.md#contract-request-overrides-worker_timeout_ms) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: tokenRecords` | source support | [Resource tables](RESPONSE.md#contract-extensions-resources) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: tokenRecords` | source support | [Token resource](RESPONSE.md#contract-extensions-token) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: unpublishedResourceStatus` | source support | [Token resource](RESPONSE.md#contract-extensions-token) |
| `runner/Sources/PWRunnerCore/ActorOrchestration.swift: var reply = PWRunnerRunResult` | source support | [Execution record](RESPONSE.md#contract-reply-record) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: actorAdmissionFailure` | source support | [Actor declaration](REQUEST.md#contract-actors-actor) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: actorAdmissionFailure` | source support | [Phase declaration](REQUEST.md#contract-actors-phase) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: actorAdmissionFailure` | source support | [Extension operation](REQUEST.md#contract-extensions-operation) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: actorAdmissionFailure` | source support | [Specimen](REQUEST.md#contract-request-specimen) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: actorPlanAssignmentsConsistent` | source support | [Source acknowledgement association](RESPONSE.md#contract-extensions-transfer-source_association) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Actor and phase evidence](RESPONSE.md#contract-actor_evidence) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Phase action variants](REQUEST.md#contract-actors-action) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Form-specific action identifiers](REQUEST.md#contract-actors-action-empty_id) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Actor declaration](REQUEST.md#contract-actors-actor) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Termination dependency](REQUEST.md#contract-actors-after_termination) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Admit the declared dependency](REQUEST.md#contract-actors-after_termination-declaration) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Phase declaration](REQUEST.md#contract-actors-phase) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Actor sandbox declaration](REQUEST.md#contract-actors-sandbox) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Extension action](REQUEST.md#contract-extensions-action) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Extension experiments](REQUEST.md#contract-extensions-examples) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Extension operation](REQUEST.md#contract-extensions-operation) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Source acknowledgement association](RESPONSE.md#contract-extensions-transfer-source_association) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Attempt request](REQUEST.md#contract-probes-attempt) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Paired probe](REQUEST.md#contract-probes-step) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: normalizeActorPlan` | source support | [Runner request refusal](RESPONSE.md#contract-refusals-request) |
| `runner/Sources/PWRunnerCore/ActorPlan.swift: var authorityRequired: Bool` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `runner/Sources/PWRunnerCore/ActorScheduler.swift: ActorScheduler` | source support | [Actor and phase evidence](RESPONSE.md#contract-actor_evidence) |
| `runner/Sources/PWRunnerCore/ActorScheduler.swift: ActorScheduler` | source support | [Setup deadline and later application](RESPONSE.md#contract-actor_evidence-application-late_application) |
| `runner/Sources/PWRunnerCore/ActorScheduler.swift: ActorScheduler` | source support | [Termination cancellation reach](RESPONSE.md#contract-actor_evidence-gate-cancellation_evidence) |
| `runner/Sources/PWRunnerCore/ActorScheduler.swift: didSetUp` | source support | [Equipment and authority setup](RESPONSE.md#contract-equipment) |
| `runner/Sources/PWRunnerCore/ActorScheduler.swift: if let plan = input.authority` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `runner/Sources/PWRunnerCore/ActorScheduler.swift: observeTermination` | source support | [A timeout followed by cleanup](RESPONSE.md#contract-actor_evidence-gate-timeout_example) |
| `runner/Sources/PWRunnerCore/ActorScheduler.swift: walkSchedule` | source support | [Collect, release and advance](REQUEST.md#contract-actors-phase-order) |
| `runner/Sources/PWRunnerCore/ActorSession.swift: postApplyHangMs` | source support | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `runner/Sources/PWRunnerCore/ActorSession.swift: profileCapture: input.captureCompiledProfile` | source support | [Receipt](RESPONSE.md#contract-profile-receipt) |
| `runner/Sources/PWRunnerCore/ActorSession.swift: readyBudgetMs` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `runner/Sources/PWRunnerCore/AuthorityCustody.swift: TransferObservation` | source support | [Host transfer observation](RESPONSE.md#contract-extensions-transfer) |
| `runner/Sources/PWRunnerCore/AuthorityCustody.swift: finish` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `runner/Sources/PWRunnerCore/AuthorityCustody.swift: init(plan: AuthorityPlan, actorCount: Int, calls: ChildProcessCalls)` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `runner/Sources/PWRunnerCore/AuthorityCustody.swift: recordSourceAcknowledgements` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `runner/Sources/PWRunnerCore/AuthorityCustody.swift: recordSourceAcknowledgements` | source support | [Source acknowledgement association](RESPONSE.md#contract-extensions-transfer-source_association) |
| `runner/Sources/PWRunnerCore/AuthorityCustody.swift: serviceOutbound` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `runner/Sources/PWRunnerCore/AuthorityCustody.swift: serviceTransfer` | source support | [Custody protocol](ARCHITECTURE.md#contract-extensions-custody) |
| `runner/Sources/PWRunnerCore/AuthorityCustody.swift: serviceTransfer` | source support | [Native extension evidence scope](ARCHITECTURE.md#contract-extensions-custody-native_library) |
| `runner/Sources/PWRunnerCore/AuthorityCustody.swift: serviceTransfer` | source support | [Host transfer observation](RESPONSE.md#contract-extensions-transfer) |
| `runner/Sources/PWRunnerCore/AuthorityCustody.swift: serviceTransfer` | source support | [Delivered receipt prerequisites](RESPONSE.md#contract-extensions-transfer-delivered_receipt) |
| `runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift: decodeAuthoritySetup` | source support | [Equipment and authority setup](RESPONSE.md#contract-equipment) |
| `runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift: decodeAuthoritySetup` | source support | [Authority operation scope](RESPONSE.md#contract-equipment-authority_scope) |
| `runner/Sources/PWRunnerCore/CWorker.swift: CWorkerInput` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `runner/Sources/PWRunnerCore/CWorker.swift: decodeFreshRead` | source support | [Predictions, attempts and comparison](RESPONSE.md#contract-steps) |
| `runner/Sources/PWRunnerCore/CWorker.swift: decodeFreshRead` | source support | [Observe fresh descriptors](RESPONSE.md#contract-steps-assessment-fresh) |
| `runner/Sources/PWRunnerCore/CWorker.swift: decodeFreshWrite` | source support | [Observe fresh descriptors](RESPONSE.md#contract-steps-assessment-fresh) |
| `runner/Sources/PWRunnerCore/CWorker.swift: decodeProfileCapture` | source support | [Receipt](RESPONSE.md#contract-profile-receipt) |
| `runner/Sources/PWRunnerCore/CWorker.swift: decodeProfileCapture` | source support | [The host decides capture availability](RESPONSE.md#contract-profile-receipt-host) |
| `runner/Sources/PWRunnerCore/CWorker.swift: decodeWorkerEvidence` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `runner/Sources/PWRunnerCore/CWorker.swift: runCWorker` | source support | [Collect, release and advance](REQUEST.md#contract-actors-phase-order) |
| `runner/Sources/PWRunnerCore/CWorker.swift: workerIdentityMatches` | source support | [Other identities](#contract-identity-other) |
| `runner/Sources/PWRunnerCore/CWorkerComparison.swift: buildOrdering` | source support | [Establish query order](RESPONSE.md#contract-steps-assessment-order) |
| `runner/Sources/PWRunnerCore/CWorkerComparison.swift: comparisonEvidence` | source support | [Shared definitions](#contract-identity-definitions) |
| `runner/Sources/PWRunnerCore/CWorkerComparison.swift: comparisonEvidence` | source support | [Predictions, attempts and comparison](RESPONSE.md#contract-steps) |
| `runner/Sources/PWRunnerCore/CWorkerComparison.swift: comparisonEvidence` | source support | [Classify an observation](RESPONSE.md#contract-steps-assessment-observe) |
| `runner/Sources/PWRunnerCore/CWorkerComparison.swift: comparisonEvidence` | source support | [Submitted operation and target](RESPONSE.md#contract-steps-assessment-relations) |
| `runner/Sources/PWRunnerCore/CWorkerDisposition.swift: attemptLifecycle` | source support | [Project actor canonical step claims](RESPONSE.md#contract-lifecycle-disposition-actor_projection) |
| `runner/Sources/PWRunnerCore/CWorkerDisposition.swift: attemptLifecycle` | source support | [Project ordinary canonical step claims](RESPONSE.md#contract-lifecycle-disposition-ordinary_projection) |
| `runner/Sources/PWRunnerCore/CWorkerDisposition.swift: func classify(` | source support | [Execution record](RESPONSE.md#contract-reply-record) |
| `runner/Sources/PWRunnerCore/CWorkerDisposition.swift: resolveDisposition` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `runner/Sources/PWRunnerCore/CWorkerDisposition.swift: resolveDisposition` | source support | [Resolve the final process status](RESPONSE.md#contract-lifecycle-worker-final_status) |
| `runner/Sources/PWRunnerCore/CWorkerDisposition.swift: resolveDisposition` | source support | [Copy the final collection basis](RESPONSE.md#contract-lifecycle-worker-resolve_collection_basis) |
| `runner/Sources/PWRunnerCore/CWorkerDisposition.swift: resolveDisposition` | source support | [Copy the polling stop](RESPONSE.md#contract-lifecycle-worker-resolve_stop_reason) |
| `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift: collectionRemainingNs` | source support | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift: let topPid: Int` | source support | [Execution record](RESPONSE.md#contract-reply-record) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: admissionFailure` | source support | [Phase declaration](REQUEST.md#contract-actors-phase) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: admissionFailure` | source support | [Specimen](REQUEST.md#contract-request-specimen) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: admissionRefusalReply` | source support | [Capacity refusal](RESPONSE.md#contract-refusals-admission) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: mapAttemptKind` | source support | [Attempt request](REQUEST.md#contract-probes-attempt) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: overridePathAdmissions` | source support | [Experimental submission](REQUEST.md#contract-request-overrides-experimental) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: pathFilterIsUnresolvable` | source support | [Sandbox query](REQUEST.md#contract-probes-query) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: pathFilterIsUnresolvable` | source support | [Refusal and unavailable-prediction examples](RESPONSE.md#contract-refusals-examples) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: requestAdmissionFailure` | source support | [Actor declaration](REQUEST.md#contract-actors-actor) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: requestAdmissionFailure` | source support | [Specimen](REQUEST.md#contract-request-specimen) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: requestCapacityFailure` | source support | [Capacity refusal](RESPONSE.md#contract-refusals-admission) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: timeoutMsForCWorker` | source support | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: timeoutMsForCWorker` | source support | [worker_timeout_ms](REQUEST.md#contract-request-overrides-worker_timeout_ms) |
| `runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift: workerParamsFromPolicy` | source support | [Worker policy input](REQUEST.md#contract-policy-spec) |
| `runner/Sources/PWRunnerCore/CWorkerStepResults.swift: buildAttemptResult` | source support | [Execute a declared operation](REQUEST.md#contract-probes-attempt-execute) |
| `runner/Sources/PWRunnerCore/CWorkerStepResults.swift: buildAttemptResult` | source support | [Observe fresh descriptors](RESPONSE.md#contract-steps-assessment-fresh) |
| `runner/Sources/PWRunnerCore/CWorkerStepResults.swift: buildAttemptResult` | source support | [Project the fresh-read aggregate](RESPONSE.md#contract-steps-assessment-fresh_read_aggregate) |
| `runner/Sources/PWRunnerCore/CWorkerStepResults.swift: buildAttemptResult` | source support | [Project the fresh-write aggregate](RESPONSE.md#contract-steps-assessment-fresh_write_aggregate) |
| `runner/Sources/PWRunnerCore/CWorkerStepResults.swift: buildStepResults` | source support | [Project actor canonical step claims](RESPONSE.md#contract-lifecycle-disposition-actor_projection) |
| `runner/Sources/PWRunnerCore/CWorkerStepResults.swift: buildStepResults` | source support | [Project ordinary canonical step claims](RESPONSE.md#contract-lifecycle-disposition-ordinary_projection) |
| `runner/Sources/PWRunnerCore/CWorkerStepResults.swift: buildStepResults` | source support | [Predictions, attempts and comparison](RESPONSE.md#contract-steps) |
| `runner/Sources/PWRunnerCore/CWorkerStepResults.swift: buildStepResults` | source support | [Assemble the two channels](RESPONSE.md#contract-steps-assessment-assembly) |
| `runner/Sources/PWRunnerCore/CWorkerStepResults.swift: eligibleOrderedStep` | source support | [Establish query order](RESPONSE.md#contract-steps-assessment-order) |
| `runner/Sources/PWRunnerCore/MonotonicDeadline.swift: static func now` | source support | [Equipment and authority setup](RESPONSE.md#contract-equipment) |
| `runner/Sources/PWRunnerCore/PWPorcelain.swift: pwPorcelainValue` | source support | [Response encoding](ARCHITECTURE.md#contract-wire) |
| `runner/Sources/PWRunnerCore/PWPorcelain.swift: text exceeds byte limit` | source support | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `runner/Sources/PWRunnerCore/PWRunnerAPI.swift: AttemptOutcome` | source support | [Shared definitions](#contract-identity-definitions) |
| `runner/Sources/PWRunnerCore/PWRunnerAPI.swift: PWProducer` | source support | [Host producer identification](RESPONSE.md#contract-identity-producer) |
| `runner/Sources/PWRunnerCore/PWRunnerAPI.swift: PW_UNIT_TEST_CONTEXT` | source support | [Direct compilation contexts](#contract-identity-public-direct) |
| `runner/Sources/PWRunnerCore/PWRunnerAPI.swift: runReservedExperiment` | source support | [Experimental submission](REQUEST.md#contract-request-overrides-experimental) |
| `runner/Sources/PWRunnerCore/PWRunnerActors.swift: PWRunnerActor` | source support | [Actor declaration](REQUEST.md#contract-actors-actor) |
| `runner/Sources/PWRunnerCore/PWRunnerActors.swift: PWRunnerActorResult` | source support | [Actor and phase evidence](RESPONSE.md#contract-actor_evidence) |
| `runner/Sources/PWRunnerCore/PWRunnerActors.swift: PWRunnerActorSandbox` | source support | [Actor sandbox declaration](REQUEST.md#contract-actors-sandbox) |
| `runner/Sources/PWRunnerCore/PWRunnerActors.swift: PWRunnerAfterTermination` | source support | [Termination dependency](REQUEST.md#contract-actors-after_termination) |
| `runner/Sources/PWRunnerCore/PWRunnerActors.swift: PWRunnerResourceTables` | source support | [Resource tables](RESPONSE.md#contract-extensions-resources) |
| `runner/Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift: execObservationEvidenceProblem` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift: PWOwnedReapObservation` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift: actorApplicationAssessment` | source support | [Actor and phase evidence](RESPONSE.md#contract-actor_evidence) |
| `runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift: authoritySetupIntegrityErrors` | source support | [Equipment and authority setup](RESPONSE.md#contract-equipment) |
| `runner/Sources/PWRunnerCore/PWRunnerCoding.swift: rejectUnknownRequestKeys` | source support | [Refusal and unavailable-prediction examples](RESPONSE.md#contract-refusals-examples) |
| `runner/Sources/PWRunnerCore/PWRunnerCoding.swift: rejectUnknownRequestKeys` | source support | [Runner request refusal](RESPONSE.md#contract-refusals-request) |
| `runner/Sources/PWRunnerCore/PWRunnerDisposition.swift: lifecycleSummary` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `runner/Sources/PWRunnerCore/PWRunnerEquipment.swift: pwRunnerEquipmentProblems` | source support | [Equipment and authority setup](RESPONSE.md#contract-equipment) |
| `runner/Sources/PWRunnerCore/PWRunnerExtension.swift: PWRunnerExtensionAction` | source support | [Extension action](REQUEST.md#contract-extensions-action) |
| `runner/Sources/PWRunnerCore/PWRunnerExtension.swift: PWRunnerExtensionEvent` | source support | [Extension event](RESPONSE.md#contract-extensions-event) |
| `runner/Sources/PWRunnerCore/PWRunnerExtension.swift: actorOperands` | source support | [Extension operation](REQUEST.md#contract-extensions-operation) |
| `runner/Sources/PWRunnerCore/PWRunnerLifecycleEvidence.swift: PWRunnerSubprocess` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift: ValidatorVerdict` | source support | [Predictions, attempts and comparison](RESPONSE.md#contract-steps) |
| `runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift: validatorAssociationIssues` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift: validatorAssociationIssues` | source support | [Count expected and unexpected associations](RESPONSE.md#contract-lifecycle-validator-cardinality) |
| `runner/Sources/PWRunnerCore/PWRunnerReply.swift: actorExtensionEvidenceProblem` | source support | [Actor and phase evidence](RESPONSE.md#contract-actor_evidence) |
| `runner/Sources/PWRunnerCore/PWRunnerReply.swift: actorExtensionEvidenceProblem` | source support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `runner/Sources/PWRunnerCore/PWRunnerReply.swift: actorExtensionEvidenceProblem` | source support | [Equipment and authority setup](RESPONSE.md#contract-equipment) |
| `runner/Sources/PWRunnerCore/PWRunnerReply.swift: func validateForReporting()` | source support | [Publish a report or fallback](RESPONSE.md#contract-reply-failure-publish) |
| `runner/Sources/PWRunnerCore/PWRunnerReply.swift: validateForReporting` | source support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `runner/Sources/PWRunnerCore/PWRunnerReply.swift: validateForReporting` | source support | [Establish query order](RESPONSE.md#contract-steps-assessment-order) |
| `runner/Sources/PWRunnerCore/PWRunnerRequest.swift: PWRunnerAdmissionFailure` | source support | [Capacity refusal](RESPONSE.md#contract-refusals-admission) |
| `runner/Sources/PWRunnerCore/PWRunnerRequest.swift: PWRunnerOverrideSource` | source support | [Experimental submission](REQUEST.md#contract-request-overrides-experimental) |
| `runner/Sources/PWRunnerCore/PWRunnerRequest.swift: PWRunnerPhase` | source support | [Phase declaration](REQUEST.md#contract-actors-phase) |
| `runner/Sources/PWRunnerCore/PWRunnerRequest.swift: PWRunnerPhaseAction` | source support | [Phase action variants](REQUEST.md#contract-actors-action) |
| `runner/Sources/PWRunnerCore/PWRunnerRequest.swift: PWRunnerPolicySpec` | source support | [Worker policy input](REQUEST.md#contract-policy-spec) |
| `runner/Sources/PWRunnerCore/PWRunnerRequest.swift: PWRunnerProbeStep` | source support | [Paired probe](REQUEST.md#contract-probes-step) |
| `runner/Sources/PWRunnerCore/PWRunnerRequest.swift: PWRunnerRequestFailure` | source support | [Runner request refusal](RESPONSE.md#contract-refusals-request) |
| `runner/Sources/PWRunnerCore/PWRunnerRequest.swift: PWRunnerRunSpec` | source support | [Shared definitions](#contract-identity-definitions) |
| `runner/Sources/PWRunnerCore/PWRunnerRequest.swift: PWRunnerRunSpec` | source support | [Specimen](REQUEST.md#contract-request-specimen) |
| `runner/Sources/PWRunnerCore/PWRunnerRequest.swift: PWRunnerSandboxFilter` | source support | [Sandbox filter](REQUEST.md#contract-probes-filter) |
| `runner/Sources/PWRunnerCore/PWRunnerRequest.swift: PWRunnerTestOverrides` | source support | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `runner/Sources/PWRunnerCore/PWRunnerReservation.swift: PWRunnerAdmission` | source support | [Delivery to the host](RESPONSE.md#contract-transport) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: PWRunnerService` | source support | [Shared definitions](#contract-identity-definitions) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: authorizedCaller` | source support | [Caller authorization](ARCHITECTURE.md#contract-transport-authorization) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: decodeExperimentalSubmission` | source support | [Experimental submission](REQUEST.md#contract-request-overrides-experimental) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: enrichPathDiagnostics` | source support | [Predictions, attempts and comparison](RESPONSE.md#contract-steps) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: enrichPathDiagnostics` | source support | [Add host path observations](RESPONSE.md#contract-steps-assessment-paths) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: pwRunnerReportData` | source support | [Distinguish a stopped boundary](RESPONSE.md#contract-refusals-later-boundaries) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: pwRunnerReportData` | source support | [Publish a report or fallback](RESPONSE.md#contract-reply-failure-publish) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: pwRunnerReportData` | source support | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: requestDecodeFailure` | source support | [Runner request refusal](RESPONSE.md#contract-refusals-request) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: reserveRunner` | source support | [Delivery to the host](RESPONSE.md#contract-transport) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: runSubmission` | source support | [Experimental submission](REQUEST.md#contract-request-overrides-experimental) |
| `runner/Sources/PWRunnerCore/PWRunnerService.swift: shouldAcceptNewConnection` | source support | [Caller authorization](ARCHITECTURE.md#contract-transport-authorization) |
| `runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift: PWRunnerStepResult` | source support | [Predictions, attempts and comparison](RESPONSE.md#contract-steps) |
| `runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift: eligibleOrderedStep` | source support | [Collect, release and advance](REQUEST.md#contract-actors-phase-order) |
| `runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift: eligibleOrderedStep` | source support | [Establish query order](RESPONSE.md#contract-steps-assessment-order) |
| `runner/Sources/PWRunnerCore/PWRunnerTransport.swift: PWRunnerClientCapture` | source support | [Delivery to the host](RESPONSE.md#contract-transport) |
| `runner/Sources/PWRunnerCore/PWRunnerTransport.swift: struct PWRunnerReplyCapture` | source support | [Retained host reply](RESPONSE.md#contract-transport-retained_reply) |
| `runner/Sources/PWRunnerCore/PathUtils.swift: firmlinkResolved` | source support | [Add host path observations](RESPONSE.md#contract-steps-assessment-paths) |
| `runner/Sources/PWRunnerCore/PathUtils.swift: parentRealpathResolved` | source support | [Add host path observations](RESPONSE.md#contract-steps-assessment-paths) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: admitSpecimen` | source support | [Runner request refusal](RESPONSE.md#contract-refusals-request) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: admitSpecimen` | source support | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: admitSpecimen` | source support | [Specimen](REQUEST.md#contract-request-specimen) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: policyMeaningFailure` | source support | [Worker policy input](REQUEST.md#contract-policy-spec) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: predictionUnavailableOpFilters` | source support | [Sandbox query](REQUEST.md#contract-probes-query) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: predictionUnavailableOpFilters` | source support | [Prediction-exclusion evidence scope](REQUEST.md#contract-probes-query-exclusion_evidence) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: requestMeaningFailure` | source support | [Phase action variants](REQUEST.md#contract-actors-action) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: requestMeaningFailure` | source support | [Form-specific action identifiers](REQUEST.md#contract-actors-action-empty_id) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: requestMeaningFailure` | source support | [Paired probe](REQUEST.md#contract-probes-step) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: sandboxCheckFailure` | source support | [Sandbox filter](REQUEST.md#contract-probes-filter) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: sandboxCheckFailure` | source support | [Sandbox query](REQUEST.md#contract-probes-query) |
| `runner/Sources/PWRunnerCore/ProbeRunner.swift: sandboxCheckFailure` | source support | [Branch-local refusal precedence](RESPONSE.md#contract-refusals-request-compound_order) |
| `runner/Sources/PWRunnerCore/SandboxApply.swift: computePolicyHash` | source support | [Execution record](RESPONSE.md#contract-reply-record) |
| `runner/Sources/PWRunnerCore/ValidatorClient.swift: decodeValidatorFrames` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `runner/Sources/PWRunnerCore/ValidatorClient.swift: decodeValidatorFrames` | source support | [Validator query and reply lines](ARCHITECTURE.md#contract-wire-validator) |
| `runner/Sources/PWRunnerCore/ValidatorClient.swift: runValidator` | source support | [Process and operation observations](RESPONSE.md#contract-lifecycle) |
| `runner/Sources/PWRunnerCore/ValidatorClient.swift: validatorStructureError` | source support | [Validator query and reply lines](ARCHITECTURE.md#contract-wire-validator) |
| `runner/Tests/PWRunnerClientSessionTests/main.swift: runClientSessionControls` | check support | [Experimental submission](REQUEST.md#contract-request-overrides-experimental) |
| `runner/Tests/PWRunnerClientSessionTests/main.swift: runClientSessionControls` | check support | [Delivery to the host](RESPONSE.md#contract-transport) |
| `runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift: runActorAuthorityTests` | check support | [Authority operation scope](RESPONSE.md#contract-equipment-authority_scope) |
| `runner/Tests/PWRunnerCoreTests/ActorEquipmentTests.swift: runActorEquipmentTests` | check support | [Static worker binding](RESPONSE.md#contract-equipment-binding) |
| `runner/Tests/PWRunnerCoreTests/ActorEquipmentTests.swift: runActorEquipmentTests` | check support | [Live-inspection evidence limit](RESPONSE.md#contract-equipment-execution-live_evidence) |
| `runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift: runActorReplyTests` | check support | [Setup deadline and later application](RESPONSE.md#contract-actor_evidence-application-late_application) |
| `runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift: runActorSchedulerTests` | check support | [Setup deadline and later application](RESPONSE.md#contract-actor_evidence-application-late_application) |
| `runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift: runActorSchedulerTests` | check support | [A timeout followed by cleanup](RESPONSE.md#contract-actor_evidence-gate-timeout_example) |
| `runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift: runActorSchedulerTests` | check support | [Collect, release and advance](REQUEST.md#contract-actors-phase-order) |
| `runner/Tests/PWRunnerCoreTests/AttemptOutcomeMappingTests.swift: runAttemptOutcomeMappingTests` | check support | [Assemble the two channels](RESPONSE.md#contract-steps-assessment-assembly) |
| `runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift: runComparisonEvidenceTests` | check support | [Classify an observation](RESPONSE.md#contract-steps-assessment-observe) |
| `runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift: runComparisonEvidenceTests` | check support | [Submitted operation and target](RESPONSE.md#contract-steps-assessment-relations) |
| `runner/Tests/PWRunnerCoreTests/CompiledProfileCaptureTests.swift: runCompiledProfileCaptureTests` | check support | [The host decides capture availability](RESPONSE.md#contract-profile-receipt-host) |
| `runner/Tests/PWRunnerCoreTests/ExperimentalSubmissionTests.swift: runExperimentalSubmissionTests` | check support | [Experimental submission](REQUEST.md#contract-request-overrides-experimental) |
| `runner/Tests/PWRunnerCoreTests/FreshWriteEvidenceTests.swift: runFreshWriteEvidenceTests` | check support | [Observe fresh descriptors](RESPONSE.md#contract-steps-assessment-fresh) |
| `runner/Tests/PWRunnerCoreTests/HostOutcomeClassifierTests.swift: runHostOutcomeClassifierTests` | check support | [Execution record](RESPONSE.md#contract-reply-record) |
| `runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift: runLimitsContractTests` | check support | [worker_timeout_ms](REQUEST.md#contract-request-overrides-worker_timeout_ms) |
| `runner/Tests/PWRunnerCoreTests/OrderingTests.swift: runOrderingTests` | check support | [Establish query order](RESPONSE.md#contract-steps-assessment-order) |
| `runner/Tests/PWRunnerCoreTests/PathDiagnosticsTests.swift: runPathDiagnosticsTests` | check support | [Add host path observations](RESPONSE.md#contract-steps-assessment-paths) |
| `runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift: runReaderCorpusTests` | check support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift: runReaderCorpusTests` | check support | [Form-specific action identifiers](REQUEST.md#contract-actors-action-empty_id) |
| `runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift: runReplyFailureTests` | check support | [Publish a report or fallback](RESPONSE.md#contract-reply-failure-publish) |
| `runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift: runReplyFailureTests` | check support | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `runner/Tests/PWRunnerCoreTests/RequestContractTests.swift: runRequestContractTests` | check support | [Capacity refusal](RESPONSE.md#contract-refusals-admission) |
| `runner/Tests/PWRunnerCoreTests/RequestContractTests.swift: runRequestContractTests` | check support | [Refusal and unavailable-prediction examples](RESPONSE.md#contract-refusals-examples) |
| `runner/Tests/PWRunnerCoreTests/RequestContractTests.swift: runRequestContractTests` | check support | [Runner request refusal](RESPONSE.md#contract-refusals-request) |
| `runner/Tests/PWRunnerCoreTests/RequestContractTests.swift: runRequestContractTests` | check support | [Specimen](REQUEST.md#contract-request-specimen) |
| `runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift: runReservationAdmissionTests` | check support | [Delivery to the host](RESPONSE.md#contract-transport) |
| `runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift: runValidatorEvidenceTests` | check support | [Validator query and reply lines](ARCHITECTURE.md#contract-wire-validator) |
| `runner/augments/exec_baseline.sb: (allow process-exec*)` | source support | [Augment resolution](REQUEST.md#contract-policy-augments) |
| `runner_kind.byoxpc@run_option` | interface association; see the partial join | [Selector precedence](REQUEST.md#contract-request-options-precedence) |
| `runner_kind.standard@run_option` | interface association; see the partial join | [Selector precedence](REQUEST.md#contract-request-options-precedence) |
| `rust.ActorDossier` | imported record declaration | [Actor policy dossier](RESPONSE.md#contract-dossier-actor) |
| `rust.ActorExecutionDiagnostics` | imported record declaration | [One actor's diagnostics](RESPONSE.md#contract-diagnostics-actor) |
| `rust.ActorPolicyCheck` | imported record declaration | [Per-actor fallback capture](RESPONSE.md#contract-policy-actor_check) |
| `rust.AppProvenance` | imported record declaration | [App provenance](RESPONSE.md#contract-dossier-app) |
| `rust.Augmentation` | imported record declaration | [Augmentation observation](RESPONSE.md#contract-dossier-augmentation) |
| `rust.Binaries` | imported record declaration | [Selected binary observations](RESPONSE.md#contract-dossier-binaries) |
| `rust.BinaryRecord` | imported record declaration | [One selected binary](RESPONSE.md#contract-dossier-binary) |
| `rust.BuildStamp` | imported record declaration | [Build identification](RESPONSE.md#contract-identity-build) |
| `rust.CheckData` | imported record declaration | [Compiler-helper data](RESPONSE.md#contract-policy-check_data) |
| `rust.CheckPolicy` | imported record declaration | [Compiler-helper policy](REQUEST.md#contract-policy-helper_policy) |
| `rust.CheckRequest` | imported record declaration | [Standalone compiler-helper request](REQUEST.md#contract-policy-helper_request) |
| `rust.CleanupReport` | imported record declaration | [Removal result](RESPONSE.md#contract-installation-cleanup) |
| `rust.CompileRecord` | imported record declaration | [Last native compile stage](RESPONSE.md#contract-policy-compile) |
| `rust.HelperEnvelope` | imported record declaration | [Compiler-helper envelope](RESPONSE.md#contract-envelope-helper) |
| `rust.HostFacts` | imported record declaration | [Controller host context](RESPONSE.md#contract-dossier-host) |
| `rust.ImportInventory` | imported record declaration | [Literal import inventory](RESPONSE.md#contract-policy-imports) |
| `rust.ImportRecord` | imported record declaration | [One import observation](RESPONSE.md#contract-dossier-import_record) |
| `rust.Imports` | imported record declaration | [Import scan](RESPONSE.md#contract-dossier-imports) |
| `rust.IntegrityIssue` | imported record declaration | [Integrity finding](RESPONSE.md#contract-diagnostics-issue) |
| `rust.JsonResult` | imported record declaration | [Operation result](RESPONSE.md#contract-envelope-result) |
| `rust.PendingCleanup` | imported record declaration | [Retained cleanup transaction](RESPONSE.md#contract-installation-pending_cleanup) |
| `rust.PlistObservation` | imported record declaration | [Observed plist](RESPONSE.md#contract-installation-plist) |
| `rust.PolicyCheckCapture` | imported record declaration | [Fallback helper capture](RESPONSE.md#contract-policy-fallback) |
| `rust.PolicyDossier` | imported record declaration | [Policy dossier](RESPONSE.md#contract-dossier-policy) |
| `rust.RequestDelivery` | imported record declaration | [Request stdin delivery](RESPONSE.md#contract-transport-request_delivery) |
| `rust.RequestFailure` | imported record declaration | [Controller request refusal](RESPONSE.md#contract-refusals-controller) |
| `rust.RequestFailureProjection` | imported record declaration | [Projected request refusal](RESPONSE.md#contract-refusals-projection) |
| `rust.RunData` | imported record declaration | [Run payload](RESPONSE.md#contract-envelope-data) |
| `rust.RunEnvelope` | imported record declaration | [Run envelope](RESPONSE.md#contract-envelope-run) |
| `rust.RunnerClientRun` | imported record declaration | [Controller observation of the client process](RESPONSE.md#contract-transport-client) |
| `rust.RunnerEntitlements` | imported record declaration | [Entitlement observation](RESPONSE.md#contract-installation-entitlements) |
| `rust.RunnerExecutionDiagnostics` | imported record declaration | [Execution diagnostics](RESPONSE.md#contract-diagnostics-execution) |
| `rust.RunnerInstallData` | imported record declaration | [Installation result](RESPONSE.md#contract-installation-install) |
| `rust.RunnerNotFoundData` | imported record declaration | [Unmatched lookup](RESPONSE.md#contract-installation-not_found) |
| `rust.RunnerOwnership` | imported record declaration | [Recorded cleanup ownership](RESPONSE.md#contract-installation-ownership) |
| `rust.RunnerProvenance` | imported record declaration | [Selected runner provenance](RESPONSE.md#contract-dossier-runner) |
| `rust.RunnerRecord` | imported record declaration | [One runner record](RESPONSE.md#contract-installation-runner) |
| `rust.RunnerRegistry` | imported record declaration | [Runner registry](RESPONSE.md#contract-installation-registry) |
| `rust.RunnerSignature` | imported record declaration | [Signature observation](RESPONSE.md#contract-installation-signature) |
| `rust.RunnerValidateData` | imported record declaration | [Validation result](RESPONSE.md#contract-installation-validate) |
| `rust.RunnerVerifyData` | imported record declaration | [Verification result](RESPONSE.md#contract-installation-verify) |
| `rust.ServiceObservation` | imported record declaration | [Observed service](RESPONSE.md#contract-installation-service) |
| `rust.Specimen` | imported record declaration | [Run dossier](RESPONSE.md#contract-dossier-specimen) |
| `rust.TransportCapture` | imported record declaration | [Transport alternatives](RESPONSE.md#contract-transport-transport_value) |
| `rust.TransportCapture.Rejected` | imported record declaration | [Rejected client stdout](RESPONSE.md#contract-transport-rejected) |
| `rust.ValidateFailure` | imported record declaration | [One validation failure](RESPONSE.md#contract-installation-failure) |
| `rust.VerifyMismatch` | imported record declaration | [One verification failure](RESPONSE.md#contract-dossier-mismatch) |
| `rust.VerifyReport` | imported record declaration | [Manifest hash verification](RESPONSE.md#contract-dossier-verification) |
| `tail.example` | interface association; see the partial join | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `test_input.form.run` | interface association; see the partial join | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `tests/fixtures/validator/no_report.c: raw_zero` | check support | [Run one native query](RESPONSE.md#contract-wire-standalone-query) |
| `tests/fixtures/validator/no_report.c: result_meaning` | check support | [Run one native query](RESPONSE.md#contract-wire-standalone-query) |
| `tests/lib/actor_evidence.py: validate_actor_evidence` | source support | [Actor and phase evidence](RESPONSE.md#contract-actor_evidence) |
| `tests/lib/consumer.py: _subject_path_problem` | source support | [Finding association and effect](RESPONSE.md#contract-diagnostics-issue-subject) |
| `tests/lib/consumer.py: _validate_actors` | source support | [Actor and phase evidence](RESPONSE.md#contract-actor_evidence) |
| `tests/lib/consumer.py: _validate_actors` | source support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `tests/lib/consumer.py: _validate_diagnostic_subjects` | source support | [Finding association and effect](RESPONSE.md#contract-diagnostics-issue-subject) |
| `tests/lib/consumer.py: _validate_reply` | source support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `tests/lib/consumer.py: _validate_reply` | source support | [Reader judgments](RESPONSE.md#contract-diagnostics-execution-reader_evidence) |
| `tests/lib/lifecycle_oracle.py: check_actor_records` | source support | [Actor and phase evidence](RESPONSE.md#contract-actor_evidence) |
| `tests/lib/lifecycle_oracle.py: check_actor_records` | source support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `tests/lib/lifecycle_oracle.py: check_actor_records` | source support | [Reader judgments](RESPONSE.md#contract-diagnostics-execution-reader_evidence) |
| `tests/lib/porcelain.py: class Reader` | source support | [Response encoding](ARCHITECTURE.md#contract-wire) |
| `tests/suites/blackbox_e2e/checker_controls.py: diagnostic_subject_controls` | check support | [Finding association and effect](RESPONSE.md#contract-diagnostics-issue-subject) |
| `tests/suites/runner_byoxpc/opt_in/registry_recovery.py: historical-after-remove` | source support | [kind](RESPONSE.md#contract-installation-runner-kind) |
| `tests/suites/runner_byoxpc/opt_in/registry_recovery.py: live-pending-verify` | source support | [Pending verification](RESPONSE.md#contract-installation-commands-pending_verify) |
| `tests/suites/runner_byoxpc/opt_in/registry_recovery.sh: registry_recovery` | check support | [Pending verification](RESPONSE.md#contract-installation-commands-pending_verify) |
| `tests/suites/runner_byoxpc/opt_in/registry_recovery.sh: registry_recovery` | check support | [kind](RESPONSE.md#contract-installation-runner-kind) |
| `tests/suites/runner_outcome_bad_request/contract.py: composite_parameters` | check support | [Parameter example observations](REQUEST.md#contract-policy-spec-parameter_evidence) |
| `tests/suites/runner_outcome_bad_request/contract.py: duplicate_entries` | check support | [Repeated members at each entry](REQUEST.md#contract-request-specimen-duplicate_keys) |
| `tests/suites/runner_outcome_bad_request/contract.py: refusal_workflows` | check support | [Refusal correction workflows](RESPONSE.md#contract-refusals-examples-workflow) |
| `tests/suites/runner_outcome_bad_request/contract.py: refusal_workflows` | check support | [Branch-local refusal precedence](RESPONSE.md#contract-refusals-request-compound_order) |
| `tests/suites/runner_unit/reader_corpus.py: replay` | check support | [Reader applicability](RESPONSE.md#contract-actor_evidence-actor-reader_scope) |
| `tests/suites/runner_unit/reader_corpus.py: replay` | check support | [Reader judgments](RESPONSE.md#contract-diagnostics-execution-reader_evidence) |
| `tests/suites/runner_unit/reader_corpus.py: replay` | check support | [Frame grammar](ARCHITECTURE.md#contract-wire-frame) |
| `tests/suites/source_drift/build_contracts.py: test_build_identity_tracks_shipped_inputs_and_requires_an_annotated_clean_release` | check support | [Build derivation](#contract-identity-public-derive) |
| `tests/suites/source_drift/build_contracts.py: test_pending_release_reproduces_after_tagging_and_tracks_removal` | check support | [Deriving the history table](#contract-identity-surfaces-derive) |
| `tests/suites/source_drift/build_contracts.py: test_presign_contract_guard_refuses_changed_sources` | check support | [Build derivation](#contract-identity-public-derive) |
| `tests/suites/source_drift/build_contracts.py: test_source_copies_ignore_artifacts_and_release_checks_actual_bytes` | check support | [Build derivation](#contract-identity-public-derive) |
| `tests/suites/source_drift/build_contracts.py: test_stamped_source_copy_and_no_tags_clone_validate_without_erasing_stamps` | check support | [Deriving the history table](#contract-identity-surfaces-derive) |
| `tests/suites/source_drift/build_contracts.py: test_swift_context_refuses_a_different_compilation_identity` | check support | [Build derivation](#contract-identity-public-derive) |
| `tests/suites/source_drift/contract_tree_controls.py: test_example_document_is_extracted_from_its_cited_constant` | check support | [Emitted example](REQUEST.md#contract-request-specimen-example) |
| `tests/suites/source_drift/contract_tree_controls.py: test_example_document_refusals_name_the_source` | check support | [Emitted example](REQUEST.md#contract-request-specimen-example) |
| `tests/suites/source_drift/generators.py: test_example_source_edit_is_stale_until_regeneration_and_moves_content_and_identity` | check support | [Emitted example](REQUEST.md#contract-request-specimen-example) |
| `tests/suites/source_drift/porcelain_codec.py: test_homogeneous_lists_sorted_maps_variants_and_depth` | check support | [Response encoding](ARCHITECTURE.md#contract-wire) |
| `tests/suites/validator_batch_mode/run.sh: batch_ndjson_roundtrip` | check support | [Direct and batch validator meanings](RESPONSE.md#contract-wire-standalone-meaning) |
| `tests/suites/validator_batch_mode/run.sh: batch_ndjson_roundtrip` | check support | [Run one native query](RESPONSE.md#contract-wire-standalone-query) |
| `tests/suites/validator_batch_mode/run.sh: batch_ndjson_roundtrip` | check support | [Repeated native query keys](ARCHITECTURE.md#contract-wire-validator-duplicate_keys) |
| `tests/suites/witness_contract/check_actor_compositions.py: assert_gate_schedule` | check support | [Termination cancellation reach](RESPONSE.md#contract-actor_evidence-gate-cancellation_evidence) |
| `tests/suites/witness_contract/check_actor_compositions.py: assert_timeout_applicability` | check support | [worker_timeout_ms](REQUEST.md#contract-request-overrides-worker_timeout_ms) |
| `tests/suites/witness_contract/check_example_round_trip.py: evaluate` | check support | [Emitted example](REQUEST.md#contract-request-specimen-example) |
| `tests/suites/witness_contract/check_extension_directory.py: run` | check support | [Extension experiments](REQUEST.md#contract-extensions-examples) |
| `tests/suites/witness_contract/check_extension_redelegation.py: chain` | check support | [Extension experiments](REQUEST.md#contract-extensions-examples) |
| `tests/suites/witness_contract/check_extensions.py: run_targets` | check support | [Extension experiments](REQUEST.md#contract-extensions-examples) |
| `tests/suites/witness_contract/check_pre_apply_failure.py: main` | check support | [Execution overrides](REQUEST.md#contract-request-overrides) |
| `tests/suites/witness_contract/check_test_input_seam.py: evaluate` | check support | [Experimental submission](REQUEST.md#contract-request-overrides-experimental) |
| `tests/suites/witness_contract/check_test_input_seam.py: evaluate` | check support | [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run) |
| `tests/suites/witness_contract/example_round_trip.sh: example_round_trip` | check support | [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example) |
| `tests/suites/witness_contract/example_round_trip.sh: example_round_trip` | check support | [Emitted example](REQUEST.md#contract-request-specimen-example) |

<a id="contract-notation"></a>
## Reading the notation

Record entries state field types, presence, meanings, vocabularies and local
requirements. Expressions state requirements,
not executable validation or evidence that a condition occurred.

**Fields.** A bare type requires the key. `T?` represents an absent value by
omitting the key; otherwise the field carries T. It does not mean JSON null.
`T ∪ null` keeps the key present and represents absence by JSON null.
These suffixes apply to the whole field value, including an array or map,
not to its elements. Exceptional omission and input requirements remain explicit.
Array and map types describe their elements and values. Hex and base64 name
the string projection, not a different byte payload. Vocabulary openness,
whether its displayed values are exhaustive, and unfamiliar-value meaning
are separate facts; field-specific conditions still apply.

**Expressions.** Dotted paths select members; bracketed indices select entries
in their declared collections. Literals use JSON spelling, including `null`,
`true`, `false` and `[]`. Lists retain their members; an effect list groups
consequences, whereas `set_value(path, [])` assigns an empty array. Parentheses
preserve grouping. `and`, `or`, `not`, comparisons, `+`, `−`, `×`, `//`
(integer division) and `%` (remainder) have their ordinary meanings. `∈` and
`∉` mean membership and nonmembership in the displayed list.

| Form | Meaning |
| --- | --- |
| `present(x)`, `absent(x)` | Presence or absence of x in the rule's record domain; interpret its JSON representation through the field definition. A literal null, a false value and an omitted key are distinct. |
| `implies(c, r)` | If condition c holds, requirement r must hold; this imposes no converse. |
| `count(x)`, `length(x)` | Entry count of a collection, or length of the operand. |
| `utf8_length(text)`, `byte_length(payload)` | UTF-8 byte length of decoded text; decoded byte length of a byte payload, independently of its hex/base64 character width. |
| `contains(text, fragment)` | Text contains the fragment, including a displayed embedded NUL. |
| `is_variant(x, label)`, `variant(x, label)` | Test the declared alternative; project that alternative. The projection supplies no guard by itself. |
| `matches(i)` | Count candidates in binding i's domain satisfying its association restriction in the current outer scope. |
| `sum_over(i, term)` | Sum the term over that domain and restriction; zero for no candidates. |
| `later(collection, i)` | Members of the collection after index i. |
| `set_value(target, value)` | Set the named target to the value. |
| `perform(action, scope)`, `prevent(action, scope)` | Perform or prevent the linked action for the named scope. |
| `withhold(target)` | Withhold that target. |
| `retain_records(target)`, `retain_assessments(target)` | Retain the named records; keep the named assessment. These are distinct obligations. |
| `emit(target, value)` | Report the target as the value. |

Linked definitions retain their authoritative meaning. A displayed limit gives
its current value, unit and limit identifier. A binding declares a domain;
its association restriction selects candidates, without asserting cardinality.
“For each” quantifies the listed indices outermost first and applies to child
obligations. Child indices extend that scope. An aggregate binds its own index;
`matches(i) = 1` does not bind i for a later expression. Bindings without
“For each” retain their stated symbolic scope.

Rules state acting components, boundary, entries, recipients and reports.
Child rows inherit context, bindings, applicability and quantified scope;
local context is shown where it changes. Parent and child applicability conjoin.
Subordinate rows name their parent. “First matching case” uses listed order;
“first failed condition” and accumulation remain distinct failure policies.
Trigger labels and explicit scopes govern effects; no notation broadens them
to other workers, recipients or entry points.


## Evidence support

<a id="contract-support-grades"></a>
**Support grades.** **source read:** The named source was inspected for the stated assertions. **check read:** The named source and check assertions were inspected in the stated context. **executed:** The named run exercised the stated assertions with its identified source or build.

<a id="contract-identity-public-derive-support-details"></a>
### Build derivation — Derivation support

[Local support](#contract-identity-public-derive-support).

Source: [build_contract.py](../docs/build_contract.py): `identity`; [source_identity.py](../docs/source_identity.py): `source_paths`; [build.sh](../build.sh): `CURRENT_BUILD_CONTRACT=`. Check: [build_contracts.py](../tests/suites/source_drift/build_contracts.py): `test_build_identity_tracks_shipped_inputs_and_requires_an_annotated_clean_release`, `test_source_copies_ignore_artifacts_and_release_checks_actual_bytes`, `test_swift_context_refuses_a_different_compilation_identity`, `test_presign_contract_guard_refuses_changed_sources`.

<a id="contract-identity-public-direct-disposition_support-details"></a>
### Direct compilation contexts — Disposition support

[Local support](#contract-identity-public-direct-disposition_support).

Source: [json_contract.rs](../controller/src/json_contract.rs): `BUILD_CONTRACT`; [build.rs](../controller/build.rs): `fn main`; [request_patch.rs](../controller/src/request_patch.rs): `validate_contract`. Check: [cli_contract.rs](../controller/integration/cli_contract.rs): `supplied_direct_cargo_identity_is_embedded_without_release_provenance`.

<a id="contract-identity-public-direct-support-details"></a>
### Direct compilation contexts — Direct-build support

[Local support](#contract-identity-public-direct-support).

Source: [json_contract.rs](../controller/src/json_contract.rs): `BUILD_CONTRACT`; [build.rs](../controller/build.rs): `cargo:rerun-if-env-changed`; [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift): `PW_UNIT_TEST_CONTEXT`; [request_patch.rs](../controller/src/request_patch.rs): `validate_contract`. Check: [cli_contract.rs](../controller/integration/cli_contract.rs): `plain_cargo_build_cannot_admit_public_requests`; [request_patch.rs](../controller/src/request_patch.rs): `request_contract_is_exact_and_required`.

<a id="contract-identity-surfaces-derive-support-details"></a>
### Deriving the history table — Surface-history support

[Local support](#contract-identity-surfaces-derive-support).

Source: [runtime.py](../docs/contract/runtime.py): `release_tags`, `stamps`, `require_available_history`, `check`. Check: [build_contracts.py](../tests/suites/source_drift/build_contracts.py): `test_pending_release_reproduces_after_tagging_and_tracks_removal`, `test_stamped_source_copy_and_no_tags_clone_validate_without_erasing_stamps`.

<a id="contract-identity-surfaces-development_review-disposition_support-details"></a>
### Reviewing a development specimen — Disposition support

[Local support](#contract-identity-surfaces-development_review-disposition_support).

Source: [build_contract.py](../docs/build_contract.py): `def identity`.

<a id="contract-identity-other-support-details"></a>
### Other identities — Identity distinctions support

[Local support](#contract-identity-other-support).

Source: [generate_porcelain.py](../docs/generate_porcelain.py): `wire_identity`; [porcelain.rs](../controller/src/porcelain.rs): `decode_bound`; [generate_worker_identity.py](../docs/generate_worker_identity.py): `identity`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `ABI identity mismatch`; [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `workerIdentityMatches`; [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `struct ActorEquipmentManifest`, `guard cdhash.count == 20`.

<a id="contract-identity-definitions-support-details"></a>
### Shared definitions — Definition grounding

[Local support](#contract-identity-definitions-support).

Source: [main.rs](../controller/src/main.rs): `fn main`; [run_flow.rs](../controller/src/run_flow.rs): `fn run(args:`; [runner_client.rs](../controller/src/runner_client.rs): `RunnerClientRun`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `PWRunnerService`; [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerRunSpec`; [CWorkerComparison.swift](../runner/Sources/PWRunnerCore/CWorkerComparison.swift): `comparisonEvidence`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_open_write`; [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `SANDBOX_CHECK_NO_REPORT`; [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift): `AttemptOutcome`; [json_contract.rs](../controller/src/json_contract.rs): `Envelope`.

<a id="contract-identity-build-support-details"></a>
### Build identification — Build-field support

[Local support](RESPONSE.md#contract-identity-build-support).

Source: [json_contract.rs](../controller/src/json_contract.rs): `build_stamp`; [build.sh](../build.sh): `# ---- Build stamp`, `stamp_info_plist`. Check: [json_contract.rs](../controller/src/json_contract.rs): `every_envelope_carries_a_complete_build_stamp`, `public_identity_is_in_the_build_frame`; [cli_contract.rs](../controller/integration/cli_contract.rs): `version_flag_reports_build_stamp_and_contract`.

<a id="contract-identity-producer-support-details"></a>
### Host producer identification — Producer-field support

[Local support](RESPONSE.md#contract-identity-producer-support).

Source: [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift): `PWProducer`; [build_contract.py](../docs/build_contract.py): `swift`; [porcelain.rs](../controller/src/porcelain.rs): `decode_bound`.

<a id="contract-identity-version-emit-support-details"></a>
### Version command — Version command support

[Local support](RESPONSE.md#contract-identity-version-emit-support).

Source: [cli.rs](../controller/src/cli.rs): `pub fn run`; [json_contract.rs](../controller/src/json_contract.rs): `JsonResult`, `now_unix_ms`. Check: [cli_contract.rs](../controller/integration/cli_contract.rs): `version_flag_reports_build_stamp_and_contract`.

<a id="contract-identity-version-emit-disposition_support-details"></a>
### Version command — Disposition support

[Local support](RESPONSE.md#contract-identity-version-emit-disposition_support).

Source: [cli.rs](../controller/src/cli.rs): `pub fn run`. Check: [cli_contract.rs](../controller/integration/cli_contract.rs): `version_dispatch_uses_the_first_argument`.

<a id="contract-request-specimen-emit_example-support-details"></a>
### Emit the example specimen — Emission support

[Local support](REQUEST.md#contract-request-specimen-emit_example-support).

Source: [example.rs](../controller/src/example.rs): `pub fn render`, `fn emit`, `pub fn cmd_example`; [cli.rs](../controller/src/cli.rs): `pub fn run`. Check: [example.rs](../controller/src/example.rs): `rendered_document_is_the_constant_with_the_given_identity`, `refusals_are_typed_and_write_nothing`, `only_complete_output_with_a_successful_flush_succeeds`; [run_flow.rs](../controller/src/run_flow.rs): `emitted_example_reaches_the_client_as_the_emitted_document`; [cli_contract.rs](../controller/integration/cli_contract.rs): `example_prints_one_request_and_refuses_every_argument`, `example_write_failures_exit_2_without_a_panic`, `supplied_direct_cargo_identity_is_embedded_without_release_provenance`; [example_round_trip.sh](../tests/suites/witness_contract/example_round_trip.sh): `example_round_trip`.

<a id="contract-request-specimen-emit_test_input-support-details"></a>
### Publish a developer read input — Publication support

[Local support](REQUEST.md#contract-request-specimen-emit_test_input-support).

Source: [test_input.rs](../controller/src/test_input.rs): `fn render_template`, `fn emit_template`, `pub fn cmd_test_input`; [cli.rs](../controller/src/cli.rs): `pub fn run`. Check: [test_input.rs](../controller/src/test_input.rs): `read_input_preserves_target_identity_and_fixed_workload`, `malformed_templates_refuse_before_output`, `members_outside_the_assigned_positions_are_published_as_embedded`, `argument_target_and_identity_refusals_write_nothing`, `complete_publication_requires_all_writes_and_flush`; [cli_contract.rs](../controller/integration/cli_contract.rs): `test_input_publishes_read_from_the_installed_binary`, `test_input_cli_refusals_and_write_failures_exit_2_safely`, `supplied_direct_cargo_identity_is_embedded_without_release_provenance`.

<a id="contract-request-specimen-read_input-support-details"></a>
### Developer read body — Body support

[Local support](REQUEST.md#contract-request-specimen-read_input-support).

Source: [test_input.rs](../controller/src/test_input.rs): `fn render_template`. Check: [cli_contract.rs](../controller/integration/cli_contract.rs): `test_input_publishes_read_from_the_installed_binary`.

<a id="contract-request-specimen-example-support-details"></a>
### Emitted example — Example support

[Local support](REQUEST.md#contract-request-specimen-example-support).

Source: [example_document.rs](../controller/src/example_document.rs): `EXAMPLE_DOCUMENT`. Check: [contract_tree_controls.py](../tests/suites/source_drift/contract_tree_controls.py): `test_example_document_is_extracted_from_its_cited_constant`, `test_example_document_refusals_name_the_source`; [generators.py](../tests/suites/source_drift/generators.py): `test_example_source_edit_is_stale_until_regeneration_and_moves_content_and_identity`; [example_round_trip.sh](../tests/suites/witness_contract/example_round_trip.sh): `example_round_trip`; [check_example_round_trip.py](../tests/suites/witness_contract/check_example_round_trip.py): `evaluate`.

<a id="contract-request-specimen-duplicate_keys-disposition_support-details"></a>
### Repeated members at each entry — Disposition support

[Local support](REQUEST.md#contract-request-specimen-duplicate_keys-disposition_support).

Source: [request_patch.rs](../controller/src/request_patch.rs): `parse_request`. Check: [contract.py](../tests/suites/runner_outcome_bad_request/contract.py): `duplicate_entries`.

<a id="contract-request-specimen-support-details"></a>
### Specimen — Support

[Local support](REQUEST.md#contract-request-specimen-support).

Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerRunSpec`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `admissionFailure`, `requestAdmissionFailure`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `admitSpecimen`; [run_flow.rs](../controller/src/run_flow.rs): `validate_request_contract`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `actorAdmissionFailure`. Check: [RequestContractTests.swift](../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift): `runRequestContractTests`.

<a id="contract-request-options-support-details"></a>
### Controller selection options — Support

[Local support](REQUEST.md#contract-request-options-support).

Source: [runner_select.rs](../controller/src/runner_select.rs): `parse_runner_selector_value`; [run_flow.rs](../controller/src/run_flow.rs): `strip_runner_selector`. Check: [runner_select.rs](../controller/src/runner_select.rs): `nested_runner_takes_precedence_over_legacy_top_level`, `malformed_selection_never_falls_back_or_discards_entitlements`, `optional_nulls_and_explicit_nested_empty_entitlements_have_defined_meanings`.

<a id="contract-request-selector-support-details"></a>
### Nested runner selector — Support

[Local support](REQUEST.md#contract-request-selector-support).

Source: [runner_select.rs](../controller/src/runner_select.rs): `RunnerSelector`, `parse_runner_selector_value`.

<a id="contract-request-overrides-worker_timeout_ms-floor_support-details"></a>
### worker_timeout_ms — Floor support

[Local support](REQUEST.md#contract-request-overrides-worker_timeout_ms-floor_support).

Source: [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `timeoutMsForCWorker`. Check: [LimitsContractTests.swift](../runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift): `runLimitsContractTests`.

<a id="contract-request-overrides-worker_timeout_ms-disposition_support-details"></a>
### worker_timeout_ms — Actor applicability support

[Local support](REQUEST.md#contract-request-overrides-worker_timeout_ms-disposition_support).

Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `runActors`. Check: [check_actor_compositions.py](../tests/suites/witness_contract/check_actor_compositions.py): `assert_timeout_applicability`.

<a id="contract-request-overrides-experimental-support-details"></a>
### Experimental submission — Experimental admission support

[Local support](REQUEST.md#contract-request-overrides-experimental-support).

Source: [PWRunnerAPI.swift](../runner/Sources/PWRunnerCore/PWRunnerAPI.swift): `runReservedExperiment`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `decodeExperimentalSubmission`, `runSubmission`; [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerOverrideSource`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `overridePathAdmissions`; [PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift): `submitExperiment`. Check: [ExperimentalSubmissionTests.swift](../runner/Tests/PWRunnerCoreTests/ExperimentalSubmissionTests.swift): `runExperimentalSubmissionTests`; [main.swift](../runner/Tests/PWRunnerClientSessionTests/main.swift): `runClientSessionControls`; [check_test_input_seam.py](../tests/suites/witness_contract/check_test_input_seam.py): `evaluate`.

<a id="contract-request-overrides-test_input_run-support-details"></a>
### Run with test controls — Command support

[Local support](REQUEST.md#contract-request-overrides-test_input_run-support).

Source: [run_args.rs](../controller/src/interface/run_args.rs): `pub fn classify`; [commands.rs](../controller/src/interface/commands.rs): `pub fn select_form`; [test_input.rs](../controller/src/test_input.rs): `pub fn cmd_test_input`; [run_flow.rs](../controller/src/run_flow.rs): `fn parse_arguments`, `fn controls_object`; [runner_client.rs](../controller/src/runner_client.rs): `fn submission_arguments`; [dossier.rs](../controller/src/dossier.rs): `pub fn observe_with_validator_control`. Check: [run_flow.rs](../controller/src/run_flow.rs): `control_spellings_are_their_keys_and_only_test_input_run_admits_them`, `integer_controls_pass_every_signed_64_bit_decimal_through_unchanged`, `malformed_control_syntax_is_refused_before_any_run_work`, `test_input_run_delivers_the_held_request_unchanged_and_the_controls_beside_it`, `test_input_run_usage_refusals_invoke_no_client_and_read_no_app_root`; [runner_client.rs](../controller/src/runner_client.rs): `only_an_experimental_submission_names_a_controls_object`; [dossier.rs](../controller/src/dossier.rs): `validator_control_follows_the_request_key_rules_and_names_the_flag`; [cli_contract.rs](../controller/integration/cli_contract.rs): `interface_cases_hold_on_the_signed_controller`; [check_test_input_seam.py](../tests/suites/witness_contract/check_test_input_seam.py): `evaluate`.

<a id="contract-request-overrides-disposition_support-details"></a>
### Execution overrides — Fixture-value support

[Local support](REQUEST.md#contract-request-overrides-disposition_support).

Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `runActors`. Check: [check_pre_apply_failure.py](../tests/suites/witness_contract/check_pre_apply_failure.py): `main`.

<a id="contract-request-overrides-support-details"></a>
### Execution overrides — Support

[Local support](REQUEST.md#contract-request-overrides-support).

Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerTestOverrides`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `timeoutMsForCWorker`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `admitSpecimen`; [CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift): `collectionRemainingNs`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `collectionRemainingNs`; [ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift): `postApplyHangMs`; [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `private func prepare`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `kill_before_publish_slot`.

<a id="contract-policy-spec-parameter_evidence-disposition_support-details"></a>
### Parameter example observations — Disposition support

[Local support](REQUEST.md#contract-policy-spec-parameter_evidence-disposition_support).

Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `check`. Check: [cli_contract.rs](../controller/integration/cli_contract.rs): `sbpl_check_verdicts_follow_the_native_compiler`; [contract.py](../tests/suites/runner_outcome_bad_request/contract.py): `composite_parameters`.

<a id="contract-policy-spec-compile_classification-disposition_support-details"></a>
### Worker and helper compile classification — Disposition support

[Local support](REQUEST.md#contract-policy-spec-compile_classification-disposition_support).

Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `sandbox_compile_string(policy_buf`; [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `compile_with`. Check: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `a_profile_succeeds_alone_and_fails_beside_an_error_buffer`.

<a id="contract-policy-spec-support-details"></a>
### Worker policy input — Support

[Local support](REQUEST.md#contract-policy-spec-support).

Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerPolicySpec`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `policyMeaningFailure`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `workerParamsFromPolicy`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `sandbox_set_param`.

<a id="contract-policy-augments-augment_semantics-disposition_support-details"></a>
### Augment evidence scope — Disposition support

[Local support](REQUEST.md#contract-policy-augments-augment_semantics-disposition_support).

Source: [augments.rs](../controller/src/augments.rs): `resolve_policy_augments`.

<a id="contract-policy-augments-support-details"></a>
### Augment resolution — Support

[Local support](REQUEST.md#contract-policy-augments-support).

Source: [augments.rs](../controller/src/augments.rs): `resolve_policy_augments`, `resolve_actor_augments`; [exec_baseline.sb](../runner/augments/exec_baseline.sb): `(allow process-exec*)`. Check: [augments.rs](../controller/src/augments.rs): `applies_and_strips_field`, `unknown_name_is_bad_request_without_partial_apply`, `actor_policies_resolve_at_their_own_paths_and_stop_at_the_first_refusal`.

<a id="contract-policy-helper_request-support-details"></a>
### Standalone compiler-helper request — Support

[Local support](REQUEST.md#contract-policy-helper_request-support).

Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `CheckRequest`, `fn main`.

<a id="contract-policy-helper_policy-support-details"></a>
### Compiler-helper policy — Support

[Local support](REQUEST.md#contract-policy-helper_policy-support).

Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `admit`, `CheckPolicy`.

<a id="contract-policy-check_data-support-details"></a>
### Compiler-helper data — Support

[Local support](RESPONSE.md#contract-policy-check_data-support).

Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `check`, `CheckData`.

<a id="contract-policy-check_data-verdict-support-details"></a>
### Select the helper verdict — Source support

[Local support](RESPONSE.md#contract-policy-check_data-verdict-support).

Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `verdict`.

<a id="contract-policy-check_data-metadata-support-details"></a>
### Decoded policy metadata — Source support

[Local support](RESPONSE.md#contract-policy-check_data-metadata-support).

Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `check`.

<a id="contract-policy-compile-support-details"></a>
### Last native compile stage — Support

[Local support](RESPONSE.md#contract-policy-compile-support).

Source: [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `compile_with`, `CompileRecord`.

<a id="contract-policy-imports-native_import_agreement-disposition_support-details"></a>
### Literal import evidence scope — Disposition support

[Local support](RESPONSE.md#contract-policy-imports-native_import_agreement-disposition_support).

Source: [sbpl_imports.rs](../controller/src/sbpl_imports.rs): `resolve_import_path`.

<a id="contract-policy-imports-support-details"></a>
### Literal import inventory — Support

[Local support](RESPONSE.md#contract-policy-imports-support).

Source: [sbpl_imports.rs](../controller/src/sbpl_imports.rs): `resolve_imports`, `read_regular_file`, `compute_closure_hash`; [sbpl-check.rs](../controller/src/bin/sbpl-check.rs): `ImportInventory`.

<a id="contract-policy-fallback-support-details"></a>
### Fallback helper capture — Support

[Local support](RESPONSE.md#contract-policy-fallback-support).

Source: [policy_check.rs](../controller/src/policy_check.rs): `parse_policy_check_output`, `supported_outcome`; [run_flow.rs](../controller/src/run_flow.rs): `fallback_policy_check`, `let actor_policies:`; [runner_client.rs](../controller/src/runner_client.rs): `pub fn fallback_eligible`. Check: [policy_check.rs](../controller/src/policy_check.rs): `supported_outcomes_are_copied_into_status_without_a_second_verdict`; [run_flow.rs](../controller/src/run_flow.rs): `fallback_compilation_is_requested_only_for_an_admitted_xpc_error`.

<a id="contract-policy-actor_check-support-details"></a>
### Per-actor fallback capture — Support

[Local support](RESPONSE.md#contract-policy-actor_check-support).

Source: [run_flow.rs](../controller/src/run_flow.rs): `actor_fallback_checks`, `actor_policies`.

<a id="contract-probes-step-support-details"></a>
### Paired probe — Support

[Local support](REQUEST.md#contract-probes-step-support).

Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerProbeStep`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `requestMeaningFailure`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-probes-query-exclusion_evidence-disposition_support-details"></a>
### Prediction-exclusion evidence scope — Disposition support

[Local support](REQUEST.md#contract-probes-query-exclusion_evidence-disposition_support).

Source: [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `predictionUnavailableOpFilters`.

<a id="contract-probes-query-support-details"></a>
### Sandbox query — Support

[Local support](REQUEST.md#contract-probes-query-support).

Source: [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `predictionUnavailableOpFilters`, `sandboxCheckFailure`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `pathFilterIsUnresolvable`.

<a id="contract-probes-filter-support-details"></a>
### Sandbox filter — Support

[Local support](REQUEST.md#contract-probes-filter-support).

Source: [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `sandboxCheckFailure`; [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerSandboxFilter`.

<a id="contract-probes-attempt-execute-disposition_support-details"></a>
### Execute a declared operation — Operation observation support

[Local support](REQUEST.md#contract-probes-attempt-execute-disposition_support).

Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_read_fresh`, `attempt_file_write_fresh`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildAttemptResult`.

<a id="contract-probes-attempt-support-details"></a>
### Attempt request — Support

[Local support](REQUEST.md#contract-probes-attempt-support).

Source: [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `mapAttemptKind`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_open_read`, `attempt_file_write_fresh`, `attempt_sysctl_read`; [pw_worker_exec.h](../controller/tools/pw_probe_runner/pw_worker_exec.h): `attempt_exec_spawn`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`; [pw_worker_timing.h](../controller/tools/pw_probe_runner/pw_worker_timing.h): `PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT`, `pw_timing_setup`.

<a id="contract-actors-actor-support-details"></a>
### Actor declaration — Support

[Local support](REQUEST.md#contract-actors-actor-support).

Source: [PWRunnerActors.swift](../runner/Sources/PWRunnerCore/PWRunnerActors.swift): `PWRunnerActor`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`, `actorAdmissionFailure`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `actorApplicationAssessment`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `requestAdmissionFailure`.

<a id="contract-actors-sandbox-support-details"></a>
### Actor sandbox declaration — Support

[Local support](REQUEST.md#contract-actors-sandbox-support).

Source: [PWRunnerActors.swift](../runner/Sources/PWRunnerCore/PWRunnerActors.swift): `PWRunnerActorSandbox`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-actors-phase-order-disposition_support-details"></a>
### Collect, release and advance — Barrier observation support

[Local support](REQUEST.md#contract-actors-phase-order-disposition_support).

Source: [PWRunnerStepEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift): `eligibleOrderedStep`.

<a id="contract-actors-phase-order-schedule_support-details"></a>
### Collect, release and advance — Schedule advancement support

[Local support](REQUEST.md#contract-actors-phase-order-schedule_support).

Source: [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `runCWorker`; [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `walkSchedule`. Check: [ActorSchedulerTests.swift](../runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift): `runActorSchedulerTests`.

<a id="contract-actors-phase-support-details"></a>
### Phase declaration — Support

[Local support](REQUEST.md#contract-actors-phase-support).

Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerPhase`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`, `actorAdmissionFailure`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `admissionFailure`.

<a id="contract-actors-after_termination-support-details"></a>
### Termination dependency — Support

[Local support](REQUEST.md#contract-actors-after_termination-support).

Source: [PWRunnerActors.swift](../runner/Sources/PWRunnerCore/PWRunnerActors.swift): `PWRunnerAfterTermination`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-actors-after_termination-declaration-support-details"></a>
### Admit the declared dependency — Source support

[Local support](REQUEST.md#contract-actors-after_termination-declaration-support).

Source: [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-actors-action-empty_id-disposition_support-details"></a>
### Form-specific action identifiers — Disposition support

[Local support](REQUEST.md#contract-actors-action-empty_id-disposition_support).

Source: [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `requestMeaningFailure`. Check: [ReaderCorpusTests.swift](../runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift): `runReaderCorpusTests`.

<a id="contract-actors-action-support-details"></a>
### Phase action variants — Support

[Local support](REQUEST.md#contract-actors-action-support).

Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerPhaseAction`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `requestMeaningFailure`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-extensions-action-support-details"></a>
### Extension action — Support

[Local support](REQUEST.md#contract-extensions-action-support).

Source: [PWRunnerExtension.swift](../runner/Sources/PWRunnerCore/PWRunnerExtension.swift): `PWRunnerExtensionAction`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`.

<a id="contract-extensions-operation-support-details"></a>
### Extension operation — Support

[Local support](REQUEST.md#contract-extensions-operation-support).

Source: [PWRunnerExtension.swift](../runner/Sources/PWRunnerCore/PWRunnerExtension.swift): `actorOperands`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`, `actorAdmissionFailure`.

<a id="contract-extensions-custody-native_library-disposition_support-details"></a>
### Native extension evidence scope — Disposition support

[Local support](ARCHITECTURE.md#contract-extensions-custody-native_library-disposition_support).

Source: [AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift): `serviceTransfer`.

<a id="contract-extensions-custody-support-details"></a>
### Custody protocol — Support

[Local support](ARCHITECTURE.md#contract-extensions-custody-support).

Source: [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `var authorityRequired: Bool`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `if !plan.authorityRequired { authority = nil; return }`; [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `if let plan = input.authority`; [AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift): `init(plan: AuthorityPlan, actorCount: Int, calls: ChildProcessCalls)`, `serviceOutbound`, `serviceTransfer`, `recordSourceAcknowledgements`, `finish`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `static void prepare_authority`, `if (hdr->actor_mode == PW_ACTOR_MODE_UNAPPLIED)`, `attempt_extension_issue`, `attempt_extension_consume_actor`, `erase_authority`.

<a id="contract-extensions-examples-disposition_support-details"></a>
### Extension experiments — Reply assembly support

[Local support](REQUEST.md#contract-extensions-examples-disposition_support).

Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`.

<a id="contract-extensions-examples-execution_support-details"></a>
### Extension experiments — Native schedule execution support

[Local support](REQUEST.md#contract-extensions-examples-execution_support).

Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_extension_issue`, `attempt_file_read_fresh`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`. Check: [check_extensions.py](../tests/suites/witness_contract/check_extensions.py): `run_targets`; [check_extension_redelegation.py](../tests/suites/witness_contract/check_extension_redelegation.py): `chain`; [check_extension_directory.py](../tests/suites/witness_contract/check_extension_directory.py): `run`. Run: `20261111T155411Z_29ef0802; witness_contract/extensions, witness_contract/extension_redelegation and witness_contract/extension_directory`. Build: `Signed candidate build 1335, version 0.3.7, b6ce6d266ff281fafdae44c32061ceff018485bb dirty; development:1445cd80509c983c6894339523f9f13ad08f5e003de4cb29ce1c398527c42f28`.

<a id="contract-extensions-examples-support-details"></a>
### Extension experiments — Example support

[Local support](REQUEST.md#contract-extensions-examples-support).

Source: [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_extension_issue`, `attempt_file_read_fresh`.

<a id="contract-extensions-event-support-details"></a>
### Extension event — Support

[Local support](RESPONSE.md#contract-extensions-event-support).

Source: [PWRunnerExtension.swift](../runner/Sources/PWRunnerCore/PWRunnerExtension.swift): `PWRunnerExtensionEvent`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_extension_issue`, `attempt_extension_consume_actor`.

<a id="contract-extensions-event-issue_projection-support-details"></a>
### Project a published issue result — Source support

[Local support](RESPONSE.md#contract-extensions-event-issue_projection-support).

Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`.

<a id="contract-extensions-transfer-support-details"></a>
### Host transfer observation — Support

[Local support](RESPONSE.md#contract-extensions-transfer-support).

Source: [AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift): `TransferObservation`, `serviceTransfer`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `PWRunnerTransferRecord`.

<a id="contract-extensions-transfer-delivered_receipt-support-details"></a>
### Delivered receipt prerequisites — Source support

[Local support](RESPONSE.md#contract-extensions-transfer-delivered_receipt-support).

Source: [AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift): `serviceTransfer`.

<a id="contract-extensions-transfer-source_association-support-details"></a>
### Source acknowledgement association — Source support

[Local support](RESPONSE.md#contract-extensions-transfer-source_association-support).

Source: [AuthorityCustody.swift](../runner/Sources/PWRunnerCore/AuthorityCustody.swift): `recordSourceAcknowledgements`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`, `actorPlanAssignmentsConsistent`.

<a id="contract-extensions-resources-support-details"></a>
### Resource tables — Support

[Local support](RESPONSE.md#contract-extensions-resources-support).

Source: [PWRunnerActors.swift](../runner/Sources/PWRunnerCore/PWRunnerActors.swift): `PWRunnerResourceTables`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `tokenRecords`.

<a id="contract-extensions-token-support-details"></a>
### Token resource — Support

[Local support](RESPONSE.md#contract-extensions-token-support).

Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `tokenRecords`, `unpublishedResourceStatus`.

<a id="contract-extensions-delivery-support-details"></a>
### Delivery resource — Support

[Local support](RESPONSE.md#contract-extensions-delivery-support).

Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `deliveryRecords`.

<a id="contract-extensions-handle-support-details"></a>
### Handle resource — Support

[Local support](RESPONSE.md#contract-extensions-handle-support).

Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `handleRecords`.

<a id="contract-refusals-request-compound_order-disposition_support-details"></a>
### Branch-local refusal precedence — Disposition support

[Local support](RESPONSE.md#contract-refusals-request-compound_order-disposition_support).

Source: [run_flow.rs](../controller/src/run_flow.rs): `fn run(args:`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `sandboxCheckFailure`. Check: [contract.py](../tests/suites/runner_outcome_bad_request/contract.py): `refusal_workflows`.

<a id="contract-refusals-request-support-details"></a>
### Runner request refusal — Support

[Local support](RESPONSE.md#contract-refusals-request-support).

Source: [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerRequestFailure`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `requestDecodeFailure`; [PWRunnerCoding.swift](../runner/Sources/PWRunnerCore/PWRunnerCoding.swift): `rejectUnknownRequestKeys`; [ProbeRunner.swift](../runner/Sources/PWRunnerCore/ProbeRunner.swift): `admitSpecimen`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`. Check: [RequestContractTests.swift](../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift): `runRequestContractTests`.

<a id="contract-refusals-controller-support-details"></a>
### Controller request refusal — Support

[Local support](RESPONSE.md#contract-refusals-controller-support).

Source: [request_patch.rs](../controller/src/request_patch.rs): `validate_contract`; [run_flow.rs](../controller/src/run_flow.rs): `bad_request`, `parse_arguments`. Check: [request_patch.rs](../controller/src/request_patch.rs): `request_contract_is_exact_and_required`, `request_failure_path_components_use_utf8_bytes_and_withhold_the_whole_path`, `request_failure_path_depth_retains_eight_and_withholds_nine`.

<a id="contract-refusals-projection-support-details"></a>
### Projected request refusal — Support

[Local support](RESPONSE.md#contract-refusals-projection-support).

Source: [run_flow.rs](../controller/src/run_flow.rs): `RequestFailureProjection`, `RequestFailureProjection::Runner`.

<a id="contract-refusals-admission-support-details"></a>
### Capacity refusal — Support

[Local support](RESPONSE.md#contract-refusals-admission-support).

Source: [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `admissionRefusalReply`, `requestCapacityFailure`; [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift): `PWRunnerAdmissionFailure`. Check: [RequestContractTests.swift](../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift): `runRequestContractTests`.

<a id="contract-refusals-examples-workflow-disposition_support-details"></a>
### Refusal correction workflows — Disposition support

[Local support](RESPONSE.md#contract-refusals-examples-workflow-disposition_support).

Source: [run_flow.rs](../controller/src/run_flow.rs): `fn run(args:`. Check: [contract.py](../tests/suites/runner_outcome_bad_request/contract.py): `refusal_workflows`.

<a id="contract-refusals-examples-support-details"></a>
### Refusal and unavailable-prediction examples — Support

[Local support](RESPONSE.md#contract-refusals-examples-support).

Source: [PWRunnerCoding.swift](../runner/Sources/PWRunnerCore/PWRunnerCoding.swift): `rejectUnknownRequestKeys`; [CWorkerRequestPlanning.swift](../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift): `pathFilterIsUnresolvable`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_create`. Check: [RequestContractTests.swift](../runner/Tests/PWRunnerCoreTests/RequestContractTests.swift): `runRequestContractTests`.

<a id="contract-refusals-later-boundaries-disposition_support-details"></a>
### Distinguish a stopped boundary — Later-outcome support

[Local support](RESPONSE.md#contract-refusals-later-boundaries-disposition_support).

Source: [runner_client.rs](../controller/src/runner_client.rs): `parse_runner_client_output`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `pwRunnerReportData`; [run_flow.rs](../controller/src/run_flow.rs): `admit_reply`.

<a id="contract-transport-support-details"></a>
### Delivery to the host — Implementation and evidence

[Local support](RESPONSE.md#contract-transport-support).

Source: [runner_client.rs](../controller/src/runner_client.rs): `parse_runner_client_output`, `validate_capture`; [utils.rs](../controller/src/utils.rs): `run_with_stdin`; [PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift): `PWRunnerClientSession`; [PWRunnerReservation.swift](../runner/Sources/PWRunnerCore/PWRunnerReservation.swift): `PWRunnerAdmission`; [PWRunnerTransport.swift](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift): `PWRunnerClientCapture`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `reserveRunner`. Check: [main.swift](../runner/Tests/PWRunnerClientSessionTests/main.swift): `runClientSessionControls`; [ReservationAdmissionTests.swift](../runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift): `runReservationAdmissionTests`; [runner_client.rs](../controller/src/runner_client.rs): `binary_reply_after_large_stdin_and_broken_pipe_preserves_delivery_precedence`, `retention_loss_precedes_decode_and_keeps_exact_prefix`.

<a id="contract-transport-authorization-support-details"></a>
### Caller authorization — Authorization support

[Local support](ARCHITECTURE.md#contract-transport-authorization-support).

Source: [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `authorizedCaller`, `shouldAcceptNewConnection`; [Info.plist](../runner/Services/PWRunner/Info.plist): `PWRunnerRequireSignedCaller`.

<a id="contract-transport-delivery-live_evidence-disposition_support-details"></a>
### Transport evidence scope — Disposition support

[Local support](ARCHITECTURE.md#contract-transport-delivery-live_evidence-disposition_support).

Source: [PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift): `reservationReply`.

<a id="contract-transport-retained_reply-source-details"></a>
### Retained host reply — Source for these relationships

[Local support](RESPONSE.md#contract-transport-retained_reply-source).

Source: [PWRunnerTransport.swift](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift): `struct PWRunnerReplyCapture`.

<a id="contract-transport-client-admit-selection_source-details"></a>
### Admit client and host observations — Capture refusal selection source

[Local support](RESPONSE.md#contract-transport-client-admit-selection_source).

Source: [runner_client.rs](../controller/src/runner_client.rs): `parse_runner_client_output`.

<a id="contract-wire-support-details"></a>
### Response encoding — Implementation and evidence

[Local support](ARCHITECTURE.md#contract-wire-support).

Source: [PWPorcelain.swift](../runner/Sources/PWRunnerCore/PWPorcelain.swift): `pwPorcelainValue`; [porcelain.rs](../controller/src/porcelain.rs): `decode_bound`; [generate_porcelain.py](../docs/generate_porcelain.py): `wire_identity`, `rust`; [porcelain.py](../tests/lib/porcelain.py): `class Reader`. Check: [porcelain.rs](../controller/src/porcelain.rs): `native_integer_width_and_boolean_values_are_not_coerced`, `authored_record_faults_are_refused_before_typed_construction`, `list_slots_and_nested_strings_share_one_budget`; [porcelain_codec.py](../tests/suites/source_drift/porcelain_codec.py): `test_homogeneous_lists_sorted_maps_variants_and_depth`.

<a id="contract-wire-frame-disposition_support-details"></a>
### Frame grammar — Decoder and writer boundary support

[Local support](ARCHITECTURE.md#contract-wire-frame-disposition_support).

Source: [porcelain.rs](../controller/src/porcelain.rs): `pub fn decode`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `pwRunnerReportData`. Check: [porcelain.rs](../controller/src/porcelain.rs): `ordered_maps_require_unique_ascending_keys_in_actual_frames`, `generated_disposition_variant_checks_tag_payload_and_complete_body`, `actual_nested_container_frames_reach_but_do_not_exceed_depth_32`; [ReplyFailureTests.swift](../runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift): `runReplyFailureTests`.

<a id="contract-wire-frame-rust_execution-details"></a>
### Frame grammar — Executed Rust wire controls

[Local support](ARCHITECTURE.md#contract-wire-frame-rust_execution).

Source: [porcelain.rs](../controller/src/porcelain.rs): `pub fn decode`. Check: [porcelain.rs](../controller/src/porcelain.rs): `ordered_maps_require_unique_ascending_keys_in_actual_frames`, `list_counts_item_kinds_and_trailing_items_refuse_in_actual_frames`, `generated_capture_byte_field_requires_the_byte_kind`, `generated_disposition_variant_checks_tag_payload_and_complete_body`, `actual_nested_container_frames_reach_but_do_not_exceed_depth_32`. Run: `20261111T155411Z_29ef0802`. Source snapshot: `reviewed-inputs sha256:b5298841bceaea7af57843a0e2ab68de2dd2ed85edf21fd07b16ac91d5a8838e (b6ce6d26 dirty)`. Case: `unit/rust.unit`.

<a id="contract-wire-frame-writer_execution-details"></a>
### Frame grammar — Executed writer fallback receipt

[Local support](ARCHITECTURE.md#contract-wire-frame-writer_execution).

Source: [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `pwRunnerReportData`; [PWPorcelain.swift](../runner/Sources/PWRunnerCore/PWPorcelain.swift): `text exceeds byte limit`. Check: [ReplyFailureTests.swift](../runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift): `runReplyFailureTests`; [run_flow.rs](../controller/src/run_flow.rs): `reader_definition_corpus_cross_readers`; [reader_corpus.py](../tests/suites/runner_unit/reader_corpus.py): `replay`. Run: `20261111T162345Z_3d6c7242`. Source snapshot: `reviewed-inputs sha256:af396aadf41ba79a0d072b62d9c3f4ff1df5b5fa30d6c4ff267c53e8437dd51d (b6ce6d26 dirty; replay identity correction)`. Case: `runner_unit/pwrunner_core_unit_executable`.

<a id="contract-wire-validator-duplicate_keys-disposition_support-details"></a>
### Repeated native query keys — Disposition support

[Local support](ARCHITECTURE.md#contract-wire-validator-duplicate_keys-disposition_support).

Source: [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `parse_probe_line`, `run_batch`. Check: [run.sh](../tests/suites/validator_batch_mode/run.sh): `batch_ndjson_roundtrip`.

<a id="contract-wire-validator-support-details"></a>
### Validator query and reply lines — Validator protocol support

[Local support](ARCHITECTURE.md#contract-wire-validator-support).

Source: [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `parse_probe_line`, `emit_verdict`; [ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift): `decodeValidatorFrames`, `validatorStructureError`. Check: [ValidatorEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ValidatorEvidenceTests.swift): `runValidatorEvidenceTests`.

<a id="contract-wire-standalone-query-execution_support-details"></a>
### Run one native query — Direct-query execution support

[Local support](RESPONSE.md#contract-wire-standalone-query-execution_support).

Source: [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `int main(`, `resolve_filter_type_id`. Check: [no_report.c](../tests/fixtures/validator/no_report.c): `raw_zero`, `result_meaning`; [run.sh](../tests/suites/validator_batch_mode/run.sh): `batch_ndjson_roundtrip`. Run: `20261111T155411Z_29ef0802; validator_batch_mode/predictions_do_not_report and validator_batch_mode/batch_ndjson_roundtrip`. Source snapshot: `controller/tools/sb_api_validator/sb_api_validator.c sha256 93318c0dd70ce26a0113fc0ab5fb676cf91938eda1bf2cfce3afc8d50c8ae4c6; tests/fixtures/validator/no_report.c sha256 d82d36711d15c824085a327f3dc268263f144949d8582c7ddc4682277d3a4e51; tests/suites/validator_batch_mode/run.sh sha256 da7ae5d7825202e974accd01149daff914c194a7d69d5af7bbc9c7d4a6e57897`. Build: `Selected signed candidate build 1335, version 0.3.7, commit b6ce6d266ff281fafdae44c32061ceff018485bb dirty; public identity development:1445cd80509c983c6894339523f9f13ad08f5e003de4cb29ce1c398527c42f28`.

<a id="contract-wire-standalone-meaning-disposition_support-details"></a>
### Direct and batch validator meanings — Disposition support

[Local support](RESPONSE.md#contract-wire-standalone-meaning-disposition_support).

Source: [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `resolve_filter_type_id`. Check: [run.sh](../tests/suites/validator_batch_mode/run.sh): `batch_ndjson_roundtrip`.

<a id="contract-wire-standalone-support-details"></a>
### Direct validator commands — Direct-command support

[Local support](RESPONSE.md#contract-wire-standalone-support).

Source: [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c): `int main(`, `parse_pid`, `resolve_filter_type_id`, `print_error`; [build.json](../docs/build.json): `sig_validator`.

<a id="contract-reply-record-classification-details"></a>
### Execution record — Classification support

[Local support](RESPONSE.md#contract-reply-record-classification).

Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `func classify(`; [CWorkerOrchestrator.swift](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift): `let topPid: Int`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `var reply = PWRunnerRunResult`; [SandboxApply.swift](../runner/Sources/PWRunnerCore/SandboxApply.swift): `computePolicyHash`. Check: [HostOutcomeClassifierTests.swift](../runner/Tests/PWRunnerCoreTests/HostOutcomeClassifierTests.swift): `runHostOutcomeClassifierTests`.

<a id="contract-reply-failure-publish-support-details"></a>
### Publish a report or fallback — Fallback support

[Local support](RESPONSE.md#contract-reply-failure-publish-support).

Source: [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `pwRunnerReportData`; [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift): `func validateForReporting()`. Check: [ReplyFailureTests.swift](../runner/Tests/PWRunnerCoreTests/ReplyFailureTests.swift): `runReplyFailureTests`.

<a id="contract-steps-assessment-assembly-support-details"></a>
### Assemble the two channels — Assembly support

[Local support](RESPONSE.md#contract-steps-assessment-assembly-support).

Source: [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildStepResults`. Check: [AttemptOutcomeMappingTests.swift](../runner/Tests/PWRunnerCoreTests/AttemptOutcomeMappingTests.swift): `runAttemptOutcomeMappingTests`.

<a id="contract-steps-assessment-order-source-details"></a>
### Establish query order — Order association source

[Local support](RESPONSE.md#contract-steps-assessment-order-source).

Source: [PWRunnerStepEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift): `eligibleOrderedStep`; [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift): `validateForReporting`.

<a id="contract-steps-assessment-order-support-details"></a>
### Establish query order — Ordering support

[Local support](RESPONSE.md#contract-steps-assessment-order-support).

Source: [PWRunnerStepEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift): `eligibleOrderedStep`; [CWorkerComparison.swift](../runner/Sources/PWRunnerCore/CWorkerComparison.swift): `buildOrdering`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `eligibleOrderedStep`. Check: [OrderingTests.swift](../runner/Tests/PWRunnerCoreTests/OrderingTests.swift): `runOrderingTests`.

<a id="contract-steps-assessment-observe-support-details"></a>
### Classify an observation — Classification support

[Local support](RESPONSE.md#contract-steps-assessment-observe-support).

Source: [CWorkerComparison.swift](../runner/Sources/PWRunnerCore/CWorkerComparison.swift): `comparisonEvidence`. Check: [ComparisonEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift): `runComparisonEvidenceTests`.

<a id="contract-steps-assessment-relations-support-details"></a>
### Submitted operation and target — Comparison support

[Local support](RESPONSE.md#contract-steps-assessment-relations-support).

Source: [CWorkerComparison.swift](../runner/Sources/PWRunnerCore/CWorkerComparison.swift): `comparisonEvidence`. Check: [ComparisonEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift): `runComparisonEvidenceTests`.

<a id="contract-steps-assessment-fresh-support-details"></a>
### Observe fresh descriptors — Publication support

[Local support](RESPONSE.md#contract-steps-assessment-fresh-support).

Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `PW_ATTEMPT_FILE_READ_FRESH`; [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `decodeFreshRead`, `decodeFreshWrite`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildAttemptResult`. Check: [FreshWriteEvidenceTests.swift](../runner/Tests/PWRunnerCoreTests/FreshWriteEvidenceTests.swift): `runFreshWriteEvidenceTests`.

<a id="contract-steps-assessment-paths-support-details"></a>
### Add host path observations — Path support

[Local support](RESPONSE.md#contract-steps-assessment-paths-support).

Source: [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `enrichPathDiagnostics`; [PathUtils.swift](../runner/Sources/PWRunnerCore/PathUtils.swift): `parentRealpathResolved`, `firmlinkResolved`. Check: [PathDiagnosticsTests.swift](../runner/Tests/PWRunnerCoreTests/PathDiagnosticsTests.swift): `runPathDiagnosticsTests`.

<a id="contract-steps-assessment-fresh_read_aggregate-source-details"></a>
### Project the fresh-read aggregate — Aggregate source

[Local support](RESPONSE.md#contract-steps-assessment-fresh_read_aggregate-source).

Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_read_fresh`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildAttemptResult`.

<a id="contract-steps-assessment-fresh_write_aggregate-source-details"></a>
### Project the fresh-write aggregate — Aggregate source

[Local support](RESPONSE.md#contract-steps-assessment-fresh_write_aggregate-source).

Source: [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `attempt_file_write_fresh`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildAttemptResult`.

<a id="contract-steps-support-details"></a>
### Predictions, attempts and comparison — Record-field support

[Local support](RESPONSE.md#contract-steps-support).

Source: [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildStepResults`; [CWorkerComparison.swift](../runner/Sources/PWRunnerCore/CWorkerComparison.swift): `comparisonEvidence`; [PWRunnerStepEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerStepEvidence.swift): `PWRunnerStepResult`; [PWRunnerPredictionEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift): `ValidatorVerdict`; [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `decodeFreshRead`; [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift): `enrichPathDiagnostics`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `capture_observed_path`; [pw_probe_runner_abi.h](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h): `PW_SHM_CHILD_OUTPUT_BYTES`; [pw_worker_exec.h](../controller/tools/pw_probe_runner/pw_worker_exec.h): `stdout_overflow`.

<a id="contract-lifecycle-worker-final_status-source-details"></a>
### Resolve the final process status — Source for these relationships

[Local support](RESPONSE.md#contract-lifecycle-worker-final_status-source).

Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `resolveDisposition`.

<a id="contract-lifecycle-worker-resolve_stop_reason-source-details"></a>
### Copy the polling stop — Source for these relationships

[Local support](RESPONSE.md#contract-lifecycle-worker-resolve_stop_reason-source).

Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `resolveDisposition`.

<a id="contract-lifecycle-worker-resolve_collection_basis-source-details"></a>
### Copy the final collection basis — Source for these relationships

[Local support](RESPONSE.md#contract-lifecycle-worker-resolve_collection_basis-source).

Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `resolveDisposition`.

<a id="contract-lifecycle-disposition-ordinary_projection-source-details"></a>
### Project ordinary canonical step claims — Projection source

[Local support](RESPONSE.md#contract-lifecycle-disposition-ordinary_projection-source).

Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `attemptLifecycle`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildStepResults`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`.

<a id="contract-lifecycle-disposition-actor_projection-source-details"></a>
### Project actor canonical step claims — Projection source

[Local support](RESPONSE.md#contract-lifecycle-disposition-actor_projection-source).

Source: [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `attemptLifecycle`; [CWorkerStepResults.swift](../runner/Sources/PWRunnerCore/CWorkerStepResults.swift): `buildStepResults`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`.

<a id="contract-lifecycle-validator-cardinality-source-details"></a>
### Count expected and unexpected associations — Source for these relationships

[Local support](RESPONSE.md#contract-lifecycle-validator-cardinality-source).

Source: [PWRunnerPredictionEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift): `validatorAssociationIssues`.

<a id="contract-lifecycle-support-details"></a>
### Process and operation observations — Support for record meanings

[Local support](RESPONSE.md#contract-lifecycle-support).

Source: [PWRunnerLifecycleEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerLifecycleEvidence.swift): `PWRunnerSubprocess`; [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `decodeWorkerEvidence`, `CWorkerInput`; [CWorkerDisposition.swift](../runner/Sources/PWRunnerCore/CWorkerDisposition.swift): `resolveDisposition`; [PWRunnerDisposition.swift](../runner/Sources/PWRunnerCore/PWRunnerDisposition.swift): `lifecycleSummary`; [PWRunnerPredictionEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift): `validatorAssociationIssues`; [ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift): `decodeValidatorFrames`, `runValidator`; [PWRunnerAttemptEvidence.swift](../runner/Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift): `execObservationEvidenceProblem`; [PWRunnerAuthoritySetup.swift](../runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift): `PWOwnedReapObservation`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `write_ready_byte`; [ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift): `readyBudgetMs`; [pw_probe_runner_abi.h](../controller/tools/pw_probe_runner/pw_probe_runner_abi.h): `PW_SHM_DIAGNOSTIC_BYTES`; [pw_worker_timing.h](../controller/tools/pw_probe_runner/pw_worker_timing.h): `PW_EXEC_REAP_GRACE_MS`.

<a id="contract-actor_evidence-actor-reader_scope-support-details"></a>
### Reader applicability — Reader definition support

[Local support](RESPONSE.md#contract-actor_evidence-actor-reader_scope-support).

Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `actorPreparationRefusal`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`; [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift): `actorExtensionEvidenceProblem`, `validateForReporting`; [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `admission_problem`; [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `preparation_failure_valid`; [consumer.py](../tests/lib/consumer.py): `_validate_reply`; [lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py): `check_actor_records`. Check: [ReaderCorpusTests.swift](../runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift): `runReaderCorpusTests`; [run_flow.rs](../controller/src/run_flow.rs): `reader_definition_corpus_cross_readers`. Run: `20261111T162345Z_3d6c7242`. Source snapshot: `reviewed-inputs sha256:af396aadf41ba79a0d072b62d9c3f4ff1df5b5fa30d6c4ff267c53e8437dd51d (b6ce6d26 dirty; replay identity correction)`. Case: `runner_unit/pwrunner_core_unit_executable`.

<a id="contract-actor_evidence-actor-reader_scope-setup_support-details"></a>
### Reader applicability — Setup declaration check support

[Local support](RESPONSE.md#contract-actor_evidence-actor-reader_scope-setup_support).

Source: [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift): `actorExtensionEvidenceProblem`; [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `fn identity`; [consumer.py](../tests/lib/consumer.py): `_validate_actors`. Check: [ReaderCorpusTests.swift](../runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift): `runReaderCorpusTests`; [reader_corpus.py](../tests/suites/runner_unit/reader_corpus.py): `replay`.

<a id="contract-actor_evidence-application-late_application-disposition_support-details"></a>
### Setup deadline and later application — Disposition support

[Local support](RESPONSE.md#contract-actor_evidence-application-late_application-disposition_support).

Source: [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `ActorScheduler`. Check: [ActorSchedulerTests.swift](../runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift): `runActorSchedulerTests`; [ActorReplyTests.swift](../runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift): `runActorReplyTests`.

<a id="contract-actor_evidence-gate-timeout_example-support-details"></a>
### A timeout followed by cleanup — Example support

[Local support](RESPONSE.md#contract-actor_evidence-gate-timeout_example-support).

Source: [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `observeTermination`. Check: [ActorSchedulerTests.swift](../runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift): `runActorSchedulerTests`.

<a id="contract-actor_evidence-gate-cancellation_evidence-disposition_support-details"></a>
### Termination cancellation reach — Disposition support

[Local support](RESPONSE.md#contract-actor_evidence-gate-cancellation_evidence-disposition_support).

Source: [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `ActorScheduler`. Check: [check_actor_compositions.py](../tests/suites/witness_contract/check_actor_compositions.py): `assert_gate_schedule`.

<a id="contract-actor_evidence-support-details"></a>
### Actor and phase evidence — Support for record meanings

[Local support](RESPONSE.md#contract-actor_evidence-support).

Source: [PWRunnerActors.swift](../runner/Sources/PWRunnerCore/PWRunnerActors.swift): `PWRunnerActorResult`; [PWRunnerAuthoritySetup.swift](../runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift): `actorApplicationAssessment`; [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `ActorScheduler`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `assembleActorReply`; [ActorPlan.swift](../runner/Sources/PWRunnerCore/ActorPlan.swift): `normalizeActorPlan`; [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift): `actorExtensionEvidenceProblem`; [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `gates`; [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `execution_diagnostics`; [actor_evidence.py](../tests/lib/actor_evidence.py): `validate_actor_evidence`; [lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py): `check_actor_records`; [consumer.py](../tests/lib/consumer.py): `_validate_actors`.

<a id="contract-equipment-binding-binding_evidence-details"></a>
### Static worker binding — Static binding evidence

[Local support](RESPONSE.md#contract-equipment-binding-binding_evidence).

Source: [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `ActorEquipmentPreparation`. Check: [ActorEquipmentTests.swift](../runner/Tests/PWRunnerCoreTests/ActorEquipmentTests.swift): `runActorEquipmentTests`.

<a id="contract-equipment-binding-bound_values-support-details"></a>
### Packaged bound-row equalities — Source support

[Local support](RESPONSE.md#contract-equipment-binding-bound_values-support).

Source: [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `bindOne`.

<a id="contract-equipment-execution-live_evidence-disposition_support-details"></a>
### Live-inspection evidence limit — Disposition support

[Local support](RESPONSE.md#contract-equipment-execution-live_evidence-disposition_support).

Source: [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `inspect`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `runActors`. Check: [ActorEquipmentTests.swift](../runner/Tests/PWRunnerCoreTests/ActorEquipmentTests.swift): `runActorEquipmentTests`.

<a id="contract-equipment-execution-eligibility-support-details"></a>
### Inspection result eligibility — Source support

[Local support](RESPONSE.md#contract-equipment-execution-eligibility-support).

Source: [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `inspect`.

<a id="contract-equipment-preparation_failure-retain-support-details"></a>
### Preparation refusal contents — Source support

[Local support](RESPONSE.md#contract-equipment-preparation_failure-retain-support).

Source: [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `runActors`, `actorPreparationRefusal`.

<a id="contract-equipment-authority_scope-publication_support-details"></a>
### Authority operation scope — Publication evidence

[Local support](RESPONSE.md#contract-equipment-authority_scope-publication_support).

Source: [AuthoritySetupRuntime.swift](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift): `decodeAuthoritySetup`. Check: [ActorAuthorityTests.swift](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift): `runActorAuthorityTests`.

<a id="contract-equipment-support-details"></a>
### Equipment and authority setup — Support for record meanings

[Local support](RESPONSE.md#contract-equipment-support).

Source: [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift): `ActorEquipmentPreparation`; [PWRunnerEquipment.swift](../runner/Sources/PWRunnerCore/PWRunnerEquipment.swift): `pwRunnerEquipmentProblems`; [AuthoritySetupRuntime.swift](../runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift): `decodeAuthoritySetup`; [PWRunnerAuthoritySetup.swift](../runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift): `authoritySetupIntegrityErrors`; [ActorOrchestration.swift](../runner/Sources/PWRunnerCore/ActorOrchestration.swift): `actorPreparationRefusal`, `inspectionDeadline`; [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift): `actorExtensionEvidenceProblem`; [ActorScheduler.swift](../runner/Sources/PWRunnerCore/ActorScheduler.swift): `didSetUp`; [MonotonicDeadline.swift](../runner/Sources/PWRunnerCore/MonotonicDeadline.swift): `static func now`.

<a id="contract-profile-receipt-host-support-details"></a>
### The host decides capture availability — Source and constructed capture checks

[Local support](RESPONSE.md#contract-profile-receipt-host-support).

Source: [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `decodeProfileCapture`. Check: [CompiledProfileCaptureTests.swift](../runner/Tests/PWRunnerCoreTests/CompiledProfileCaptureTests.swift): `runCompiledProfileCaptureTests`.

<a id="contract-profile-receipt-labels-failure-support-details"></a>
### A failed label check for run — Constructed run labels

[Local support](RESPONSE.md#contract-profile-receipt-labels-failure-support).

Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `admission_problem`. Check: [run_flow.rs](../controller/src/run_flow.rs): `compiled_profile_labels_determine_the_public_admission_outcome`. Run: `20261110T195016Z_0d197151`. Source snapshot: `5e51300d620e2a3ead419380977212d2c3e41ba1`.

<a id="contract-profile-receipt-labels-verify_failure-support-details"></a>
### A failed label check for runner verify — Verification refusal source

[Local support](RESPONSE.md#contract-profile-receipt-labels-verify_failure-support).

Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`; [run_flow.rs](../controller/src/run_flow.rs): `pub(crate) fn admit_reply`; [json_contract.rs](../controller/src/json_contract.rs): `impl JsonResult`.

<a id="contract-profile-receipt-labels-support-details"></a>
### The controller checks carried labels — Shared label admission source

[Local support](RESPONSE.md#contract-profile-receipt-labels-support).

Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `pub(crate) fn admission_problem`; [run_flow.rs](../controller/src/run_flow.rs): `pub(crate) fn reply_contract`, `pub(crate) fn admit_reply`; [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`.

<a id="contract-profile-receipt-source-details"></a>
### Receipt — Capture and presence source

[Local support](RESPONSE.md#contract-profile-receipt-source).

Source: [pw_profile_capture.h](../controller/tools/pw_probe_runner/pw_profile_capture.h): `pw_capture_profile`; [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c): `pw_capture_profile`; [ActorSession.swift](../runner/Sources/PWRunnerCore/ActorSession.swift): `profileCapture: input.captureCompiledProfile`; [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift): `decodeProfileCapture`.

<a id="contract-envelope-support-details"></a>
### The controller envelope — Envelope support

[Local support](RESPONSE.md#contract-envelope-support).

Source: [json_contract.rs](../controller/src/json_contract.rs): `render_envelope`; [run_flow.rs](../controller/src/run_flow.rs): `complete_execution`, `admit_reply`; [runner_client.rs](../controller/src/runner_client.rs): `pub fn failure`. Check: [json_contract.rs](../controller/src/json_contract.rs): `renderer_borrows_nonclone_typed_payload_and_serializes_it_once`; [run_flow.rs](../controller/src/run_flow.rs): `finished_run_preserves_successful_and_failed_attempts`, `typed_completion_preserves_native_failure_beside_finished_summary`; [runner_client.rs](../controller/src/runner_client.rs): `binary_reply_after_large_stdin_and_broken_pipe_preserves_delivery_precedence`.

<a id="contract-diagnostics-execution-geometry-support-details"></a>
### Decoded response collection bounds — Response-bound support

[Local support](RESPONSE.md#contract-diagnostics-execution-geometry-support).

Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `claim_geometry`, `lifecycle_geometry`, `scope_geometry`, `reply_geometry`, `admission_problem`; [run_flow.rs](../controller/src/run_flow.rs): `admit_reply`; [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`. Check: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `typed_geometry_refuses_before_projection_and_retains_every_raw_record`, `typed_reference_geometry_is_checked_before_claims_and_admission_contexts`.

<a id="contract-diagnostics-execution-support-details"></a>
### Execution diagnostics — Controller finding support

[Local support](RESPONSE.md#contract-diagnostics-execution-support).

Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `execution_diagnostics`, `project`, `validate_lifecycle`, `admit_reply`; [run_flow.rs](../controller/src/run_flow.rs): `reply_contract`, `complete_execution`; [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `pub(super) fn validate`; [porcelain_native.rs](../controller/src/porcelain_native.rs): `pub(super) fn validate`. Check: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `typed_invalid_actor_account_keeps_independent_actor_endings`, `typed_degradation_never_certifies_surviving_comparison`, `typed_future_applicability_and_summary_remain_open_without_rewriting`; [run_flow.rs](../controller/src/run_flow.rs): `malformed_phase_claims_withhold_projection_and_preserve_raw_reply`, `execution_envelopes_preserve_raw_evidence_and_emit_only_execution_fields`.

<a id="contract-diagnostics-execution-reader_evidence-support-details"></a>
### Reader judgments — Corpus support

[Local support](RESPONSE.md#contract-diagnostics-execution-reader_evidence-support).

Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `execution_diagnostics`; [consumer.py](../tests/lib/consumer.py): `_validate_reply`; [lifecycle_oracle.py](../tests/lib/lifecycle_oracle.py): `check_actor_records`. Check: [run_flow.rs](../controller/src/run_flow.rs): `reader_definition_corpus_cross_readers`; [reader_corpus.py](../tests/suites/runner_unit/reader_corpus.py): `replay`. Run: `20261111T162345Z_3d6c7242`. Source snapshot: `reviewed-inputs sha256:af396aadf41ba79a0d072b62d9c3f4ff1df5b5fa30d6c4ff267c53e8437dd51d (b6ce6d26 dirty; replay identity correction)`. Case: `runner_unit/pwrunner_core_unit_executable`.

<a id="contract-diagnostics-actor-support-details"></a>
### One actor's diagnostics — Actor projection support

[Local support](RESPONSE.md#contract-diagnostics-actor-support).

Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `project`, `validate_lifecycle`, `check_claim`. Check: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `typed_host_cleanup_cause_requires_all_independent_observations`, `typed_invalid_actor_account_keeps_independent_actor_endings`.

<a id="contract-diagnostics-issue-subject-gate_execution-details"></a>
### Finding association and effect — Executed gate finding locations

[Local support](RESPONSE.md#contract-diagnostics-issue-subject-gate_execution).

Source: [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `fn gates`. Check: [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `gate_findings_locate_each_retained_assertion_by_position`. Run: `20261111T155411Z_29ef0802`. Source snapshot: `reviewed-inputs sha256:b5298841bceaea7af57843a0e2ab68de2dd2ed85edf21fd07b16ac91d5a8838e (b6ce6d26 dirty)`. Case: `unit/rust.unit`.

<a id="contract-diagnostics-issue-subject-reference_execution-details"></a>
### Finding association and effect — Executed reference-form controls

[Local support](RESPONSE.md#contract-diagnostics-issue-subject-reference_execution).

Source: [consumer.py](../tests/lib/consumer.py): `_subject_path_problem`, `_validate_diagnostic_subjects`. Check: [checker_controls.py](../tests/suites/blackbox_e2e/checker_controls.py): `diagnostic_subject_controls`. Run: `20261111T155411Z_29ef0802`. Source snapshot: `reviewed-inputs sha256:b5298841bceaea7af57843a0e2ab68de2dd2ed85edf21fd07b16ac91d5a8838e (b6ce6d26 dirty)`. Case: `blackbox_e2e/checker_controls`.

<a id="contract-diagnostics-issue-support-details"></a>
### Integrity finding — Finding construction support

[Local support](RESPONSE.md#contract-diagnostics-issue-support).

Source: [porcelain_admission.rs](../controller/src/porcelain_admission.rs): `IntegrityIssue`, `fn issue`, `for i in &sub.disposition`; [porcelain_actor.rs](../controller/src/porcelain_actor.rs): `fn require`, `fn gates`; [porcelain_native.rs](../controller/src/porcelain_native.rs): `pub(super) fn validate`.

<a id="contract-dossier-support-details"></a>
### Specimen dossier — Implementation and evidence

[Local support](RESPONSE.md#contract-dossier-support).

Source: [dossier.rs](../controller/src/dossier.rs): `Specimen`, `Imports`, `Binaries`; [run_flow.rs](../controller/src/run_flow.rs): `load_app_provenance`, `fn run(`, `actor_fallback_checks`; [sbpl_imports.rs](../controller/src/sbpl_imports.rs): `resolve_imports`, `compute_closure_hash`; [runner_select.rs](../controller/src/runner_select.rs): `RunnerProvenance`; [evidence.rs](../controller/src/evidence.rs): `verify_manifest`. Check: [dossier.rs](../controller/src/dossier.rs): `augmentation_records_hash_only_bytes_that_existed`, `import_scan_statuses_never_report_an_unscanned_closure_as_complete`, `builtin_run_hashes_nothing_and_reports_null_records`, `byoxpc_copies_are_compared_with_the_shipped_baselines`; [sbpl_imports.rs](../controller/src/sbpl_imports.rs): `closure_hash_excludes_unresolved_imports`, `closure_hash_is_order_invariant`.

<a id="contract-dossier-collection-native_gap-disposition_support-details"></a>
### Held input and file observation scope — Disposition support

[Local support](RESPONSE.md#contract-dossier-collection-native_gap-disposition_support).

Source: [run_flow.rs](../controller/src/run_flow.rs): `fn run(args:`; [sbpl_imports.rs](../controller/src/sbpl_imports.rs): `resolve_import_path`; [dossier.rs](../controller/src/dossier.rs): `fn compare`. Check: [run_flow.rs](../controller/src/run_flow.rs): `actor_fallback_uses_held_policy_objects_before_host_mode_admission`.

<a id="contract-dossier-augmentation-relationships-support-details"></a>
### Augmentation record relationships — Source support

[Local support](RESPONSE.md#contract-dossier-augmentation-relationships-support).

Source: [dossier.rs](../controller/src/dossier.rs): `Augmentation`.

<a id="contract-dossier-imports-scope-support-details"></a>
### Retained scan scope — Source support

[Local support](RESPONSE.md#contract-dossier-imports-scope-support).

Source: [dossier.rs](../controller/src/dossier.rs): `Imports`.

<a id="contract-dossier-binary-classify-support-details"></a>
### Classify the retained digest pair — Source support

[Local support](RESPONSE.md#contract-dossier-binary-classify-support).

Source: [dossier.rs](../controller/src/dossier.rs): `compare`.

<a id="contract-installation-support-details"></a>
### Managing runners — Implementation and evidence

[Local support](RESPONSE.md#contract-installation-support).

Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_install`, `cmd_runner_verify`, `cmd_runner_validate`, `cmd_runner_reconcile`; [runner_manager.rs](../controller/src/runner_manager.rs): `RunnerRegistry`, `save_registry`, `install_record`, `remove_record`, `plist_ownership`, `service_ownership`, `read_back`. Check: [runner_manager.rs](../controller/src/runner_manager.rs): `install_failure_boundaries_preserve_observed_pending_state`, `legacy_metadata_survives_unrelated_writes_and_pending_cleanup`, `historical_flattened_cleanup_remains_readable_and_rewrites_with_nested_runner`, `registry_save_refuses_duplicate_known_metadata_before_publication`, `atomic_registry_replace_preserves_old_open_readers_and_failed_write`, `bootout_waits_out_launchd_teardown_within_the_budget`.

<a id="contract-installation-commands-pending_verify-disposition_support-details"></a>
### Pending verification — Disposition support

[Local support](RESPONSE.md#contract-installation-commands-pending_verify-disposition_support).

Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`; [registry_recovery.py](../tests/suites/runner_byoxpc/opt_in/registry_recovery.py): `live-pending-verify`. Check: [registry_recovery.sh](../tests/suites/runner_byoxpc/opt_in/registry_recovery.sh): `registry_recovery`.

<a id="contract-installation-commands-entitlement_errors-disposition_support-details"></a>
### Entitlement read errors and summary counts — Disposition support

[Local support](RESPONSE.md#contract-installation-commands-entitlement_errors-disposition_support).

Source: [runner_manager.rs](../controller/src/runner_manager.rs): `validate_record`; [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_validate`. Check: [runner_manager.rs](../controller/src/runner_manager.rs): `validation_keeps_entitlement_errors_distinct_from_failed_read_back`.

<a id="contract-installation-commands-ownership-disposition_support-details"></a>
### Classify cleanup ownership — Cleanup location support

[Local support](RESPONSE.md#contract-installation-commands-ownership-disposition_support).

Source: [runner_manager.rs](../controller/src/runner_manager.rs): `record_location`, `plist_ownership`, `service_ownership`.

<a id="contract-installation-runner-kind-disposition_support-details"></a>
### kind — Legacy registry support

[Local support](RESPONSE.md#contract-installation-runner-kind-disposition_support).

Source: [runner_kind.rs](../controller/src/interface/runner_kind.rs): `pub const fn rule`; [runner_manager.rs](../controller/src/runner_manager.rs): `for RunnerKind`; [registry_recovery.py](../tests/suites/runner_byoxpc/opt_in/registry_recovery.py): `historical-after-remove`. Check: [registry_recovery.sh](../tests/suites/runner_byoxpc/opt_in/registry_recovery.sh): `registry_recovery`; [runner_manager.rs](../controller/src/runner_manager.rs): `legacy_machme_kind_deserializes_as_byoxpc`, `legacy_debuggable_kind_deserializes_as_byoxpc`, `caller_facing_parse_rejects_legacy_aliases`.

<a id="contract-installation-cleanup-retention-support-details"></a>
### Retained recovery account — Source support

[Local support](RESPONSE.md#contract-installation-cleanup-retention-support).

Source: [runner_manager.rs](../controller/src/runner_manager.rs): `remove_record`.

<a id="contract-installation-install-state_copy-support-details"></a>
### Published installation state — Source support

[Local support](RESPONSE.md#contract-installation-install-state_copy-support).

Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_install`.

<a id="contract-installation-verify-delivery_failure-support-details"></a>
### Request delivery failure — Source support

[Local support](RESPONSE.md#contract-installation-verify-delivery_failure-support).

Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`.

<a id="contract-installation-verify-select-support-details"></a>
### Select the verification operation result — Source support

[Local support](RESPONSE.md#contract-installation-verify-select-support).

Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_verify`.

<a id="contract-installation-service-classify-support-details"></a>
### Classify the typed service observation — Source support

[Local support](RESPONSE.md#contract-installation-service-classify-support).

Source: [runner_manager.rs](../controller/src/runner_manager.rs): `service_ownership`.

<a id="contract-installation-dynamic_support-details"></a>
### Managing runners — Dynamic record support

[Local support](RESPONSE.md#contract-installation-dynamic_support).

Source: [runner_commands.rs](../controller/src/runner_commands.rs): `cmd_runner_reconcile`; [runner_manager.rs](../controller/src/runner_manager.rs): `remove_record`, `service_after_bootout`.

## Rule applicability

Each linked rule states its boundary, entry, recipients, reports and conditions.

| Acting components | Rules |
| --- | --- |
| [Build pipeline](#contract-identity-definitions-build_pipeline) | [Build derivation](#contract-identity-public-derive) |
| [Contract generator](#contract-identity-definitions-contract_generator) | [Deriving the history table](#contract-identity-surfaces-derive) |
| [Controller](#contract-identity-definitions-controller) | [Version command](RESPONSE.md#contract-identity-version-emit); [Hold and deliver the selected request](REQUEST.md#contract-request-specimen-hold); [Emit the example specimen](REQUEST.md#contract-request-specimen-emit_example); [Publish a developer read input](REQUEST.md#contract-request-specimen-emit_test_input); [Selector precedence](REQUEST.md#contract-request-options-precedence); [Selection and augmentation failure order](REQUEST.md#contract-request-options-failure_order); [Run with test controls](REQUEST.md#contract-request-overrides-test_input_run); [Resolve and append](REQUEST.md#contract-policy-augments-resolve); [Resolve actor policies in request order](REQUEST.md#contract-policy-augments-actors); [Fallback eligibility and classification](RESPONSE.md#contract-policy-fallback-classify); [Controller pre-invocation refusal](RESPONSE.md#contract-refusals-controller-consequence); [Admit client and host observations](RESPONSE.md#contract-transport-client-admit); [Checking a carried gate](RESPONSE.md#contract-actor_evidence-gate-check); [The controller checks carried labels](RESPONSE.md#contract-profile-receipt-labels); [Select the public result](RESPONSE.md#contract-envelope-data-select); [Boundary precedence](RESPONSE.md#contract-envelope-data-admit); [Decoded response collection bounds](RESPONSE.md#contract-diagnostics-execution-geometry); [Admit the response before assessment](RESPONSE.md#contract-diagnostics-execution-admit); [Project one worker or aggregate actors](RESPONSE.md#contract-diagnostics-execution-project); [Actor projection rows](RESPONSE.md#contract-diagnostics-execution-actor_rows); [Worker lifecycle validation](RESPONSE.md#contract-diagnostics-execution-ordinary-lifecycle_check); [Ending mapping](RESPONSE.md#contract-diagnostics-execution-ordinary-mapping); [Supported stop reason](RESPONSE.md#contract-diagnostics-execution-ordinary-stop); [Host-cleanup attribution](RESPONSE.md#contract-diagnostics-execution-ordinary-cause); [Copy validated host conflicts](RESPONSE.md#contract-diagnostics-execution-ordinary-host_conflicts); [Apply reply-wide findings](RESPONSE.md#contract-diagnostics-execution-reply_checks); [Worker lifecycle validation](RESPONSE.md#contract-diagnostics-actor-projection-lifecycle_check); [Ending mapping](RESPONSE.md#contract-diagnostics-actor-projection-mapping); [Supported stop reason](RESPONSE.md#contract-diagnostics-actor-projection-stop); [Host-cleanup attribution](RESPONSE.md#contract-diagnostics-actor-projection-cause); [Copy validated host conflicts](RESPONSE.md#contract-diagnostics-actor-projection-host_conflicts); [Retain observation and finding separately](RESPONSE.md#contract-diagnostics-issue-retain); [Hold the selected request](RESPONSE.md#contract-dossier-collection-held); [Scan literal imports](RESPONSE.md#contract-dossier-collection-scan); [Compare selected files](RESPONSE.md#contract-dossier-collection-compare); [Augmentation record relationships](RESPONSE.md#contract-dossier-augmentation-relationships); [Retained scan scope](RESPONSE.md#contract-dossier-imports-scope); [Classify the retained digest pair](RESPONSE.md#contract-dossier-binary-classify); [Read and select records](RESPONSE.md#contract-installation-commands-read); [Publish a registry mutation](RESPONSE.md#contract-installation-commands-publish); [Install a selected service](RESPONSE.md#contract-installation-commands-install); [Retain installation ownership](RESPONSE.md#contract-installation-commands-pending); [Refresh validation metadata](RESPONSE.md#contract-installation-commands-validate); [Reconcile observations](RESPONSE.md#contract-installation-commands-reconcile); [Remove an owned installation](RESPONSE.md#contract-installation-commands-remove); [Classify cleanup ownership](RESPONSE.md#contract-installation-commands-ownership); [Retained recovery account](RESPONSE.md#contract-installation-cleanup-retention); [Published installation state](RESPONSE.md#contract-installation-install-state_copy); [Request delivery failure](RESPONSE.md#contract-installation-verify-delivery_failure); [Select the verification operation result](RESPONSE.md#contract-installation-verify-select); [Classify the typed service observation](RESPONSE.md#contract-installation-service-classify) |
| [Runner host](#contract-identity-definitions-host) | [Admission order and effects](REQUEST.md#contract-request-specimen-admission); [Null and omission](REQUEST.md#contract-request-specimen-nulls); [Bounded strings and action counts](REQUEST.md#contract-request-specimen-capacity); [Experimental submission](REQUEST.md#contract-request-overrides-experimental); [Admission and eligibility](REQUEST.md#contract-probes-query-eligibility); [Extension participant restriction](REQUEST.md#contract-probes-attempt-extension_exec); [Normalize actors before launch](REQUEST.md#contract-actors-actor-normalize); [Collect, release and advance](REQUEST.md#contract-actors-phase-order); [Validate and evaluate the dependency](REQUEST.md#contract-actors-after_termination-gate); [Admit the declared dependency](REQUEST.md#contract-actors-after_termination-declaration); [Action identity](REQUEST.md#contract-actors-action-identity); [Resolve references and ownership](REQUEST.md#contract-extensions-operation-references); [Bound the declared resource plan](REQUEST.md#contract-extensions-operation-capacity); [Exclude exec in participating actors](REQUEST.md#contract-extensions-operation-exec); [Observe the source answer](ARCHITECTURE.md#contract-extensions-custody-source_answer); [Project a published issue result](RESPONSE.md#contract-extensions-event-issue_projection); [Delivered receipt prerequisites](RESPONSE.md#contract-extensions-transfer-delivered_receipt); [Source acknowledgement association](RESPONSE.md#contract-extensions-transfer-source_association); [Refuse at the first reached boundary](RESPONSE.md#contract-refusals-request-select); [Stop children and preserve safe metadata](RESPONSE.md#contract-refusals-request-consequence); [Sanitize every echoed field](RESPONSE.md#contract-refusals-admission-echo); [Admit a connection](ARCHITECTURE.md#contract-transport-authorization-connection); [Host line admission](ARCHITECTURE.md#contract-wire-validator-read); [Assemble execution evidence](RESPONSE.md#contract-reply-record-assemble); [Publish a report or fallback](RESPONSE.md#contract-reply-failure-publish); [Assemble the two channels](RESPONSE.md#contract-steps-assessment-assembly); [Establish query order](RESPONSE.md#contract-steps-assessment-order); [Classify an observation](RESPONSE.md#contract-steps-assessment-observe); [Add host path observations](RESPONSE.md#contract-steps-assessment-paths); [Resolve the final process status](RESPONSE.md#contract-lifecycle-worker-final_status); [Copy the polling stop](RESPONSE.md#contract-lifecycle-worker-resolve_stop_reason); [Copy the final collection basis](RESPONSE.md#contract-lifecycle-worker-resolve_collection_basis); [Resolving lifecycle claims](RESPONSE.md#contract-lifecycle-disposition-resolve); [Project ordinary canonical step claims](RESPONSE.md#contract-lifecycle-disposition-ordinary_projection); [Project actor canonical step claims](RESPONSE.md#contract-lifecycle-disposition-actor_projection); [Joining accepted validator records](RESPONSE.md#contract-lifecycle-validator-associate); [Count expected and unexpected associations](RESPONSE.md#contract-lifecycle-validator-cardinality); [Actor ownership and reporting scope](RESPONSE.md#contract-actor_evidence-actor-account); [Associated authority rows](RESPONSE.md#contract-actor_evidence-application-authority_association); [Application classification](RESPONSE.md#contract-actor_evidence-application-classify); [Prepared actor phase and gate records](RESPONSE.md#contract-actor_evidence-gate-prepared_association); [Evaluating and applying the dependency](RESPONSE.md#contract-actor_evidence-gate-evaluate); [Binding before launch](RESPONSE.md#contract-equipment-binding-bind); [Packaged bound-row equalities](RESPONSE.md#contract-equipment-binding-bound_values); [Associating the owned process](RESPONSE.md#contract-equipment-execution-inspect); [Inspection result eligibility](RESPONSE.md#contract-equipment-execution-eligibility); [Preparation refusal contents](RESPONSE.md#contract-equipment-preparation_failure-retain); [Acquiring setup decisions and operations](RESPONSE.md#contract-equipment-authority_scope-acquire); [Receipt presence](RESPONSE.md#contract-profile-receipt-presence); [The host decides capture availability](RESPONSE.md#contract-profile-receipt-host) |
| [Runner host](#contract-identity-definitions-host), [Worker](#contract-identity-definitions-worker) | [Prepare native compiler input](REQUEST.md#contract-policy-spec-parameters); [Fresh process and retained policy](REQUEST.md#contract-actors-actor-fresh); [Prepare before use](ARCHITECTURE.md#contract-extensions-custody-prepare); [Acknowledge, compare and settle delivery](ARCHITECTURE.md#contract-extensions-custody-deliver); [Erase at declared last use and teardown](ARCHITECTURE.md#contract-extensions-custody-erase) |
| [Compiler helper](#contract-identity-definitions-helper) | [Read helper input](REQUEST.md#contract-policy-helper_request-read); [Helper admission order](REQUEST.md#contract-policy-helper_policy-admit); [Inventory, compile and report](RESPONSE.md#contract-policy-check_data-run_compile); [Select the helper verdict](RESPONSE.md#contract-policy-check_data-verdict); [Decoded policy metadata](RESPONSE.md#contract-policy-check_data-metadata); [Release native resources](RESPONSE.md#contract-policy-compile-release) |
| [Controller](#contract-identity-definitions-controller), [Compiler helper](#contract-identity-definitions-helper), [Worker](#contract-identity-definitions-worker) | [Separate reads and their identities](RESPONSE.md#contract-policy-imports-holds) |
| [Worker](#contract-identity-definitions-worker) | [Execute a declared operation](REQUEST.md#contract-probes-attempt-execute); [Exec setup and child inputs](REQUEST.md#contract-probes-attempt-exec); [Observe fresh descriptors](RESPONSE.md#contract-steps-assessment-fresh) |
| [Worker](#contract-identity-definitions-worker), [Runner host](#contract-identity-definitions-host) | [Issue and transfer payload ownership](ARCHITECTURE.md#contract-extensions-custody-issue); [Project the fresh-read aggregate](RESPONSE.md#contract-steps-assessment-fresh_read_aggregate); [Project the fresh-write aggregate](RESPONSE.md#contract-steps-assessment-fresh_write_aggregate) |
| [Runner client](#contract-identity-definitions-client), [Runner host](#contract-identity-definitions-host) | [Acquire an unused host](ARCHITECTURE.md#contract-transport-delivery-acquire) |
| [Runner client](#contract-identity-definitions-client) | [Admit the control](ARCHITECTURE.md#contract-transport-delivery-admit_control); [Invoke execution once](ARCHITECTURE.md#contract-transport-delivery-invoke) |
| [Controller](#contract-identity-definitions-controller), [Runner client](#contract-identity-definitions-client) | [Apply the original allowance](ARCHITECTURE.md#contract-transport-delivery-deadline); [Verify a selected service](RESPONSE.md#contract-installation-commands-verify) |
| [Controller](#contract-identity-definitions-controller), [Retained-byte reader](ARCHITECTURE.md#contract-wire-frame-reader) | [Exact structural admission](ARCHITECTURE.md#contract-wire-frame-admit) |
| [Runner host](#contract-identity-definitions-host), [Validator](#contract-identity-definitions-validator) | [Query production and native boundary](ARCHITECTURE.md#contract-wire-validator-query) |
| [Validator](#contract-identity-definitions-validator) | [Verdict production](ARCHITECTURE.md#contract-wire-validator-emit); [Parse and report a PID](RESPONSE.md#contract-wire-standalone-status); [Run one native query](RESPONSE.md#contract-wire-standalone-query) |

## Controller findings

Each row names the record members a check reads and links each consequence with what it reaches.

| Check | Records read | Consequences and their reach |
| --- | --- | --- |
| [Admit client and host observations](RESPONSE.md#contract-transport-client-admit) | `client.request_delivery`, `client.runner_reply_error`, `client.stdout_bytes_retained`, `client.stdout_capture_error`, `client.stdout_parse_error`, `client.submission`, `client.transport_admission`, `client.transport_error` | Stated at the linked rule. |
| [Exact structural admission](ARCHITECTURE.md#contract-wire-frame-admit) | See the linked rule. | Stated at the linked rule. |
| [Checking a carried gate](RESPONSE.md#contract-actor_evidence-gate-check) | `reply.actors`, `reply.execution_form`, `reply.phases`, `reply.reporting_failure` | [Failed carried-gate requirement](RESPONSE.md#contract-actor_evidence-gate-check-failed) (on failure): sets `envelope.data.runner_sandbox_diagnostics.disposition_integrity`, `envelope.data.runner_sandbox_diagnostics.process_disposition`, `envelope.data.runner_sandbox_diagnostics.termination_cause`; retains `reply`; keeps `envelope.data.runner_sandbox_diagnostics.actors`. |
| [The controller checks carried labels](RESPONSE.md#contract-profile-receipt-labels) | `receipt.capture_stage`, `receipt.producer`, `receipt.status` | [A failed label check for run](RESPONSE.md#contract-profile-receipt-labels-failure) (cli run, on failure): sets `envelope.result.normalized_outcome`, `envelope.result.ok`; withholds `envelope.data.runner_sandbox_diagnostics`; retains `reply`. [A failed label check for runner verify](RESPONSE.md#contract-profile-receipt-labels-verify_failure) (runner verify, on failure): sets `result.ok`, `result.exit_code`, `result.normalized_outcome`, `runner_verify.normalized_outcome`, `runner_verify.runner_pid`; retains `runner_verify.runner_client`, `runner_verify.runner_result`. |
| [Boundary precedence](RESPONSE.md#contract-envelope-data-admit) | See the linked rule. | Stated at the linked rule. |
| [Decoded response collection bounds](RESPONSE.md#contract-diagnostics-execution-geometry) | `reply.actors`, `reply.authority_setup`, `reply.equipment_bindings`, `reply.equipment_entitlements`, `reply.execution_form`, `reply.extension_events`, `reply.phases`, `reply.resources`, `reply.runner_subprocess`, `reply.steps`, `reply.transfers` | [Failed collection bound](RESPONSE.md#contract-diagnostics-execution-geometry-failed) (on failure): sets `result.normalized_outcome`, `result.ok`, `result.exit_code`; retains `reply`. [Run assessment after refusal](RESPONSE.md#contract-diagnostics-execution-geometry-run_refusal) (cli run, on failure): sets `envelope.data.runner_sandbox_diagnostics`. [Verification completion after refusal](RESPONSE.md#contract-diagnostics-execution-geometry-verify_refusal) (runner verify, on failure): sets `runner_verify.normalized_outcome`, `runner_verify.runner_pid`. |
| [Worker lifecycle validation](RESPONSE.md#contract-diagnostics-execution-ordinary-lifecycle_check) | See the linked rule. | [Local lifecycle findings](RESPONSE.md#contract-diagnostics-execution-ordinary-lifecycle_check-local_failure) (on failure): sets `envelope.data.runner_sandbox_diagnostics.process_disposition`, `envelope.data.runner_sandbox_diagnostics.termination_cause`, `envelope.data.runner_sandbox_diagnostics.disposition_integrity`, `envelope.data.runner_sandbox_diagnostics.stop_reason`. |
| [Worker lifecycle validation](RESPONSE.md#contract-diagnostics-actor-projection-lifecycle_check) | See the linked rule. | [Local lifecycle findings](RESPONSE.md#contract-diagnostics-actor-projection-lifecycle_check-local_failure) (on failure): sets `envelope.data.runner_sandbox_diagnostics.actors[d].process_disposition`, `envelope.data.runner_sandbox_diagnostics.actors[d].termination_cause`, `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_integrity`, `envelope.data.runner_sandbox_diagnostics.actors[d].stop_reason`. |
| [Classify cleanup ownership](RESPONSE.md#contract-installation-commands-ownership) | See the linked rule. | Stated at the linked rule. |

## Known gaps

| Item | Kind |
| --- | --- |
| [Ordinary-build history requirement](#contract-identity-surfaces-release_history) | behavior |
| [Termination cancellation reach](RESPONSE.md#contract-actor_evidence-gate-cancellation_evidence) | behavior |
<!-- END GENERATED PUBLIC CONTRACT -->
