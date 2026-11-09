# PolicyWitness public contracts

The public contract is the release. Saved specimens assert `contract`; every
independently arriving envelope, host reply and client capture names its
producer. Admission is exact. There is no negotiation, implicit acceptance,
historical translation or bypass.

A clean tree at exactly one annotated `vX.Y.Z` tag emits `release:vX.Y.Z`.
Other packaged builds emit `development:<sha256>` over the shipped source and
build inputs. The digest includes on-disk contents and paths, so shipped-input
edits change it. Ordinary documentation and test edits do not change that digest.
A dirty release tree is a development build. Release admission also compares actual scoped source bytes with the tag’s blobs; Git index flags cannot hide edited inputs. The source scope uses declared language/resource suffixes and explicit build helpers equally in Git checkouts and source copies. Incidental executables and OS files are excluded. Direct Cargo and SwiftPM builds
are `unbound` and refuse public requests and packaged peer checks.
`--version`, the envelope `build.contract`, and app/service `PWContract` report
the compiled identity. Describe and commit remain provenance, not admission keys.

To reuse a specimen with another release, inspect the surface rows changed since
its asserted release, revisit the corresponding definitions and change the
assertion yourself. PolicyWitness never rewrites a user's specimen. Reinstall
external runners from the current app when its contract changes.

## Surface stamps

The manifest [contract_surfaces.json](contract_surfaces.json) defines the scope.
The transport golden includes the complete binary record identity, including
host-reply field tags, native widths and presentation rules. Transport and
installation goldens include reservation limits and the overall client
allowance, with their counting, effects and controls.
The generator hashes canonical shape goldens and each delimited normative region
across reachable annotated release tags. A new or changed surface is stamped
`unreleased` until release preparation; removed surfaces retain a removal row.
Stamps are navigation aids and are never asserted or used for admission.

<!-- BEGIN GENERATED CONTRACT STAMPS -->
| Surface | User artifact | Last changed |
| --- | --- | --- |
| `actors` | Phases and actors | v0.3.6 |
| `dossier` | Specimen dossier | v0.3.6 |
| `envelope` | Controller and helper envelopes | v0.3.6 |
| `equipment` | Actor evidence and equipment | v0.3.6 |
| `installation` | Runner installation and reservation | v0.3.6 |
| `lifecycle` | Disposition and lifecycle evidence | v0.3.6 |
| `policy` | SBPL, params, augments and imports | v0.3.6 |
| `probes` | Probe steps | v0.3.6 |
| `profile` | Compiled-profile receipt | v0.3.6 |
| `refusals` | Exit classification and structured refusals | v0.3.6 |
| `request` | Saved specimen and runner selection | v0.3.6 |
| `steps` | Reply steps and comparison | v0.3.6 |
| `transport` | Client capture and transport | v0.3.6 |
<!-- END GENERATED CONTRACT STAMPS -->

When annotated release history is unavailable, `--check` validates the current
inputs and agreement between the two tables, but explicitly reports that stamp
derivation was not checked. Regeneration refuses to erase existing release
stamps without history. Release preflight requires annotated history and a full
derivation; `--check --require-history` requests the same completeness.

## Normative surfaces

### Saved specimen and runner selection

<!-- BEGIN CONTRACT request -->
The request root requires a string `contract` exactly equal to the running build identity. Missing, null, nonstring and foreign assertions refuse before selectors, augments, helpers or children. Unknown fields are refused after this gate. `runner`, aliases and required entitlements select one installed or bundled runner. Example: a foreign assertion plus an invalid runner selector reports the contract refusal and starts no client.

## Accepted input contract

The existing Swift `Codable` types remain the parser. Their `CodingKeys` also
define the accepted fields of every request object: the root, policy, each
phase, ordinary action/probe step, sandbox check, filter, attempt and
`_test_overrides`. An unknown key
is a `bad_request` with a bounded field path, rather than an ignored option.
For example, `policy.capture_compiled_profiel` is rejected. `policy.params`
is a dictionary of caller-chosen names to string values; its names are data,
not closed object fields. Missing required fields and wrong value types are
also rejected. Optional null values generally have the same meaning as absence. Actor `equipment`, `required_entitlements`, phase `after_termination`, and the actor equipment override map reject explicit null; omission selects their documented defaults.

The controller additionally accepts [runner selection](../controller/README.md#runner-selection-external-entitlements)
and resolves `policy.augments`. It validates selector types and every required
entitlement, including shadowed aliases; unknown nested selector fields are
errors. A non-null nested selector value takes precedence over its top-level
alias, including an explicit empty entitlement list. Selection fields are
removed before XPC delivery and their resolved meaning is recorded in runner
provenance. Direct XPC requests reject runner selection fields. Actor `required_entitlements` remains in the XPC request and is checked separately for each actor by the host. Nonempty augment lists require a
string `sbpl_source`; the controller splices the named fragments and strips
the list. A direct XPC request with unresolved fragments is rejected.

Meaning checks reject unknown attempt kind/action pairs and filter kinds before
any worker or validator is created. A non-null `attempt.args` is accepted only
for `exec/spawn`; a non-null `filter.value` is refused for `kind: "none"`;
`capture_nonce` requires enabled `capture_compiled_profile`. Enabled capture
requires a valid nonce. Exactly one non-null plan form, `probe_plan` or
`phases`, is required. Explicit phases are nonempty and have unique nonempty
phase IDs. Every ordinary action requires both query and attempt. Step IDs
must be distinct across all phases and exec targets absolute.
Known operation/filter pairs excluded from prediction still produce explicit
`prediction_unavailable` observations, with supported attempts executed normally.
Operation names passed to `sandbox_check` remain OS queries; the validator can
report `unsupported_operation`. Query and attempt scopes need not match.

Every shipped-source change changes a development contract. A clean annotated
release binds all public surfaces to that release. Additions, removals, meaning
changes and implementation fixes therefore require the specimen author to
review and assert the selected build's identity. Keep the affected normative
definition, verified examples and shape goldens current so the release stamp
table identifies the surfaces to review. There is no separate request counter
or compatibility exception for optional additions.

[Runtime admission limits](LIMITS.md) are separate from this syntax and meaning.
For example, a structurally valid plan can exceed the worker's step capacity;
the refusal names the field, actual count and maximum before any attempts.
Raising capacity accepts more plans; lowering it can refuse previously runnable
requests. The caller decides whether to revise the specimen or use a build with
more capacity; PW never truncates or reinterprets the plan. Capacity changes must
be documented and tested even when they do not change the input grammar.

Maintenance consists of the existing decoder/selector fields, their meaning
in the guide, and acceptance/refusal tests. No additional schema language or
parser generator is used. These rules protect requested intent; they do not
promise identical sandbox observations across builds or macOS versions.

The [developer lesson](REQUEST-GRAMMAR.md) works through the same specimens
used by Swift decoding/validation tests and signed CLI/direct-XPC controls.

<!-- END CONTRACT request -->

### SBPL, params, augments and imports

<!-- BEGIN CONTRACT policy -->
A policy supplies SBPL source and optional string parameters. Named augments are resolved by the controller in memory before submission; direct XPC refuses unresolved augments. Imports and hashes describe the held policy input and its closure. Example: a missing augment refuses before worker creation and leaves the input file unchanged.
<!-- END CONTRACT policy -->

### Probe steps

<!-- BEGIN CONTRACT probes -->
Each probe step has a unique step ID, a sandbox query and an attempt. Supported attempt actions and filter kinds are closed vocabularies. Predictions are observations distinct from attempts and do not establish enforcement agreement. Example: file `open_write` opens with truncation; a same-shape foreign build assertion prevents that operation.
<!-- END CONTRACT probes -->

### Phases and actors

<!-- BEGIN CONTRACT actors -->
A specimen uses either the ordinary single-worker form or named actors and phases. Every sandboxed process is fresh; an actor applies its policy once. Phases name the active actor and preserve action order. Extension transfer and consumption use explicit owned records. Example: a phase naming a nonexistent actor is refused before children.
<!-- END CONTRACT actors -->

### Controller and helper envelopes

<!-- BEGIN CONTRACT envelope -->
Every envelope carries `kind`, `generated_at_unix_ms`, `build`, `result` and `data`. `build.contract` identifies its producer. Readers admit it before semantic fields. Nested helper envelopes have independent build context. Unsupported received bytes remain available without inferred claims. Example: a foreign helper envelope claiming compilation cannot supply a successful policy-check status.
<!-- END CONTRACT envelope -->

### Specimen dossier

<!-- BEGIN CONTRACT dossier -->
The dossier records the held request path, policy provenance, imports, selected runner, host context and observed binary inventory. Unknown observations remain unknown. The submitted serialization and fallback compiler use the same held input. Example: changing the source file after admission does not change the held submission.
<!-- END CONTRACT dossier -->

### Reply steps and comparison

<!-- BEGIN CONTRACT steps -->
A host reply carries `producer.contract`, `producer.describe` and `producer.commit`. Admission is exact before interpreting steps. Comparisons relate query and attempt observations; permission-shaped failures do not prove a sandbox cause. `query_first` requires the collection/release evidence chain. Example: a foreign host reply inside a current envelope yields one unsupported diagnostic without recovered comparisons.
<!-- END CONTRACT steps -->

### Disposition and lifecycle evidence

<!-- BEGIN CONTRACT lifecycle -->
Lifecycle claims depend on native progress, collection and termination observations. Unknown or contradictory observations withhold dependent claims. An exit request is not proof of reap; successful return alone is not an effect witness. Example: an unreaped worker remains unconfirmed even after a successful termination request.
<!-- END CONTRACT lifecycle -->

### Actor evidence and equipment

<!-- BEGIN CONTRACT equipment -->
Actor evidence binds observations to the named process and service-sealed equipment. The worker ABI identity remains independent of the public build identity. Worker entitlements are read from the selected binary. Example: an equipment hash mismatch prevents use of the claimed equipment.

## Actor evidence ownership


Actor execution has no declaration reply or singular worker projection.
`actors[]` owns each launch, subprocess, application assessment and equipment
association. The `authority_setup.host` run/region/custody scopes and
`authority_setup.workers` cells retain primary setup, independent cleanup and
native-capability observations. An acquired decision does not publish another
cell, and a scheduling summary does not replace any actor's facts.

`equipment_inventory` identifies the selected service's sealed equipment
inventory. Rows of `equipment_bindings` and `equipment_entitlements` are named
by position: a binding is identified by its `role` and `source`, and
`binding_ref` and `entitlements_ref` are zero-based indexes into those two
arrays. An actor's `binding_ref` is null when no binding row was produced for
its role. `equipment_bindings` separates packaged roles from explicitly
instrumented overrides; the latter carry `unverified_fixture` implementation
identity and cannot establish packaged selection. `equipment_entitlements`
contains independently associated static and live XML read-backs. Every actor's
requirements are evaluated separately using boolean true keys, including in the
live read-back. Bounds and reserve geometry belong to [LIMITS](LIMITS.md).
Runtime inspection failure cancels all scheduled activation and retains any
already published setup/application facts. It is not a before-launch
`preparation_failure`; independent earlier cancellation remains visible.

`preparation_failure` admits only `resolved_plan/inconsistent_assignment` or
`equipment/equipment_binding_refused`, with `runner_failed`, `rc: 1` and no
launched actors. Observation arrays are empty. Unique bounded declarative phase
and action identities may remain, without claiming that those actions ran;
this is the sole exception to their normal complete observation partition.

`actors[].application` has closed state/basis pairs. Unapplied intent is
`not_requested/unapplied_declaration`. `not_attempted` requires host proof of no
launch or an eligible terminal worker branch before application.
`observed` requires an applied publication or the native apply-failure
publication. With no such source, requested application is `unobserved`.
In particular, setup timeout, `done`, process death or an auxiliary reporting
failure alone cannot establish application nonattempt.

Termination dependencies retain a source actor's `owned_reap`, including native
PID/return/raw wait status, capture stage, ownership/departure flags,
`capture_ordinal` and optional `observed_ns`. Each phase may retain
`activation_observation: {capture_ordinal, observed_ns?}`. These ordinals are
local to the source actor process, not a global process counter.
`termination_gate.observation` is `{capture_ordinal}` referencing that source
actor's owned reap. Every nonnull observation, including a failed gate's,
requires a positive matching source reap ordinal and a present later gate
`capture_ordinal`. A satisfied gate additionally requires the source's final
activation before its owned reap before gate closure, consistent child PID and
decoded wait status, unbroken ownership and no prior host departure request.
Both source final-activation and owned-reap timestamps must be present and
monotonically ordered. The gate wait also requires a usable clock, no native
wait error, and elapsed time within the positive termination-gate allowance in
[LIMITS](LIMITS.md).
An abnormal natural reap can satisfy termination; final phase completion,
`done`, a requested exit or cleanup-only reap cannot substitute.

Native facts may retain absent source timestamps after clock failure, but
cannot satisfy the dependency without them. Once dependent activation has been
stored, a missing post-store dependent timestamp retains that activation and
the already satisfied gate; it cannot turn the observed activation into absence.
A present dependent timestamp must not precede the source reap. Reached failed
gates withhold activation, collection and release even if cleanup later
observes reap.

<!-- END CONTRACT equipment -->

### Compiled-profile receipt

<!-- BEGIN CONTRACT profile -->
A compiled-profile receipt inherits its admitted host reply context. It has no independent schema marker. Status, nonce, worker binding, stage, byte count and digest must be consistent; a detached receipt grants no producer context. Example: a wrong nonce refuses the receipt even inside a current reply.
<!-- END CONTRACT profile -->

### Client capture and transport

<!-- BEGIN CONTRACT transport -->
Client capture and reservation messages carry a string `contract`. The capture and embedded host frame are independently admitted. The binary shape fingerprint guards decoding and is not a public compatibility identity. Reservation and submission failures never authorize replay after an uncertain invocation. Example: a foreign live peer behind a matching registry entry receives no specimen submission.
<!-- END CONTRACT transport -->

### Exit classification and structured refusals

<!-- BEGIN CONTRACT refusals -->
Request refusals use `bad_request`, bounded diagnostic paths and distinct missing/type/unsupported codes. Contract failures include `expected_contract`; foreign output is unsupported, malformed output remains malformed. Delivery failure takes precedence over interpreting a reply. Example: an old `schema_version`-only specimen reports missing `contract`, not an unknown-field error.
### Structured request refusals

Malformed JSON, request contract assertions, selectors, augments, field structure and
meaning, and capacity refusals report `bad_request`; the controller exits 1.
Unreadable request files, unavailable runner installations and transport failures
remain tool/execution failures. The controller exposes `data.request_failure`;
when the runner refuses the request, this is an unchanged copy of the runner's
`request_failure`. It is optional additive response/envelope information: absence
means no structured diagnostic was supplied, never that execution succeeded.

The record has `code` and `path`, plus `expected_contract` for contract-field
refusals. `path` is an array of object keys and decimal array positions, with
`[]` naming the root. It is `null` when the full location cannot be reported:
at most eight components of at most 63 UTF-8 bytes each are echoed. Refused
parameter keys are also withheld. Human-readable `error` is supplementary;
consumers use the code and path without parsing that prose.

| Codes | Meaning |
| --- | --- |
| `invalid_json` | The request could not be parsed as JSON. |
| `unsupported_contract` | The request marker names another contract. |
| `unknown_field`, `missing_field`, `missing_value`, `type_mismatch`, `invalid_value` | The named input is unknown, absent, null where required, mistyped or invalid. |
| `unsupported_policy_format`, `missing_policy_source` | The policy's structural prerequisites are absent. |
| `unknown_filter_kind`, `missing_filter_value`, `empty_operation` | A sandbox query cannot be formed from the request. |
| `unsupported_attempt`, `relative_exec_target`, `duplicate_step_id` | The plan cannot be carried out with its submitted meaning. |
| `invalid_termination_dependency` | A phase names an unknown source actor, itself, or a source whose final visit is not earlier than the dependent phase; the path identifies `phases`, its index, `after_termination`, `actor_id`. |
| `inapplicable_field`, `invalid_capture_nonce` | A supplied field cannot take effect or satisfy its prerequisites. |
| `conflicting_selector`, `unresolved_augments`, `augment_unavailable` | Controller-owned instructions conflict, remain unresolved at XPC, or name unavailable fragments. |
| `admission_refused` | Capacity or native-string admission failed; `admission_failure` retains the field, actual count, maximum and applicable positions. |

These refusals contain no steps or child-process observations. The XPC host
itself may have launched to decode a request. Capacity checks precede meaning
checks; diagnostics identify one refusal, not an exhaustive list of defects.
Retain unfamiliar codes as unclassified refusals rather than guessing their cause.

<!-- END CONTRACT refusals -->

### Runner installation and reservation

<!-- BEGIN CONTRACT installation -->
Install admits service `PWContract` before signing or launchd mutation and rechecks after signing. Registry and live-peer identities must both match for execution. Records without a contract remain listable, reconcilable and removable under the existing ownership rules. Example: an owned legacy record cannot execute but can be removed after observed absence.
Unknown record, ownership, signature, entitlements and registry metadata survives unrelated writes and pending cleanup as opaque data. A pending cleanup entry contains a nested `runner` record, `cleanup_started_at_unix_ms`, and `observations`; the reader also accepts historical flattened entries. Publication requires a lossless read-back before atomic replacement. It never establishes execution compatibility or ownership. Known retired kind aliases project as their current kind.
<!-- END CONTRACT installation -->

<!-- BEGIN CONTRACT transport_encoding -->
## Typed response transport


[porcelain.json](porcelain.json) owns response and client-capture record
structure. `generate_porcelain.py` emits the Swift writers and stored fields,
Rust owned records/readers/JSON projection, and the structural tables read by a
separately written Python reader. All three derive from the one schema, so
they cannot disagree with each other about structure; none of them checks the
schema itself. Request and reservation JSON and validator NDJSON retain their
own boundaries. JSON reply fixtures are test inputs; production reply ingestion
is binary and public JSON is projected from typed records.

A frame is `PWP1`, the SHA-256 of the schema's wire identity, and one
root value. Values have a one-byte kind, four-byte little-endian payload length,
and payload. Kinds are boolean, signed integer, unsigned integer, UTF-8 text,
bytes, record, list, ordered string map and a declared variant. Integers occupy
eight bytes; readers enforce each field's native signedness and width. Digests
travel as their bytes, and a reference from one equipment row to another is an
unsigned index into the table it names. Enumerated values such as outcomes,
states and reasons travel as text, as do the names a request chose (step,
phase, actor, token, delivery and handle names); their vocabularies and
associations are checked by semantic admission, not by the frame. Records
begin with a two-byte identity and contain strictly increasing nonzero two-byte
field tags followed by values. Lists/maps begin with a four-byte count; map keys
are unique and sorted by UTF-8 bytes. Variants begin with a two-byte case tag.
Optional fields are absent, never filled with fabricated defaults.

Readers reject unsupported fingerprints, unknown tags/records/cases, missing
required fields, incorrect kinds, invalid text, impossible lengths/counts,
duplicates and trailing data. The [primitive reader](../controller/src/porcelain.rs)
enforces byte and nesting budgets and charges decoded collection slots, strings
and bytes against one logical-storage budget per frame. These are not physical
peak-memory bounds. The client capture and the host reply it carries are
separate frames, each read under its own budget. The host writer bounds a reply
by the frame limit, while the client retains at most its smaller
[reply allowance](LIMITS.md); a larger reply arrives truncated and is refused
as `runner_reply_truncated`. The controller collects the client's complete
output before applying its retention cap; reading is not streamed and has no
receiver deadline of its own.

The fingerprint covers every record identity, field tag, field name, kind and
public presentation rule, so it is exact: any edit to those, including an added
optional field or a changed null or byte spelling, produces a different
fingerprint. Source locations, defaults and comments are outside it. There is no negotiation and no additive compatibility at this
layer. The public build contract is checked during reservation before execution. The binary fingerprint remains a structural decoder check; it supplies no independent compatibility permission.

The public envelope projects typed records. Byte fields are carried as bytes:
retained host reply bytes, compiled-profile bytecode and rejected validator
context become base64, and fresh-read content and every digest (SHA-256, code
directory hash, worker identity) become lowercase hexadecimal, only at
presentation. Unsupported or malformed input cannot become a semantic
claim. Structural admission establishes the declared shape;
named validators separately check native operations, lifecycle, phase order,
actor setup/equipment, owned endings and extension custody before projecting
claims. Conflicting observations remain publishable with dependent claims withheld.


<!-- END CONTRACT transport_encoding -->

## Maintaining the contract

Edit schema-owned record declarations in `docs/porcelain.json` and regenerate
with `tests/lib/python.sh docs/generate_porcelain.py`. Review shape changes,
update their goldens and keep each normative definition and verified example
current. No public schema counter is maintained. Run
`tests/lib/python.sh docs/generate_contract_stamps.py`; `--check` verifies
freshness without writing when annotated history is available, and reports the
verification limit otherwise. Use `--check --require-history` for a complete
derivation check. Prepare the table with `--release vX.Y.Z` before
committing and tagging; on the tagged tree ordinary `--check` must reproduce it.

The registry, provenance and other infrastructure format markers, validator
NDJSON marker and worker ABI identity retain their separate purposes. Historical
captures keep their bytes and are rejected if their producer is unsupported.
Authored request templates carry no identity; the harness asserts the independently
inspected candidate at submission. Constructed response tests supply an explicit
producer context.

## Internal host/worker identity


The XPC host and its bundle-local `pw-probe-runner` use an exact SHA-256
source identity, generated by
[generate_worker_identity.py](generate_worker_identity.py). There is no worker
ABI ordinal or compatibility negotiation. The build checks the C, Swift and
test copies before compilation and again before signing, and never writes
them; `tests/lib/python.sh docs/generate_worker_identity.py` regenerates them after an
edit to any input, and `--check` verifies them without writing. Direct
source-test builds regenerate the same way. The [build account](BUILD.md#one-build-in-time)
owns the sequence of checks and signatures.

The digest covers sorted repository-relative paths and file contents, each
length-framed: all `.c`, `.h` and `.swift` files under
`controller/tools/pw_probe_runner/` and `runner/Sources/`, plus the generator and its shared `source_identity.py` walker,
`build.sh`, `meson.build`, `meson.options` and `runner/Package.swift`.
Generated identity region bodies are excluded to avoid self-reference.
Discovery includes new helpers automatically when they are ordinary files
beneath those directories; a symlink there is refused, and the build reads
Ninja's dependency log to check that the compiler consumed nothing for the
worker and the shim beyond these inputs, the selected SDK and the developer
directory. This conservative scope includes the C wait and publication code,
Swift release and collection code, orchestration, ABI declarations and their
host mirror. Even comments or unrelated changes within those files change the
identity; there is no manual semantic-version judgment to make.

The shared header has a fixed bootstrap magic at byte 0 and 32 identity bytes
at byte 64. The worker checks the mapped region's size and these fields before
reading policy input, publishing evidence, or using layout-dependent fields.
An identity or magic mismatch exits with code 4 and no ready/applied/done
publication. The bootstrap magic also makes ordinal-era workers refuse the
header. The host checks the identity before decoding worker evidence and before
releasing attempts. These checks do not assert that a child validated the
header: `runner_subprocess.worker_evidence.abi_identity` records the
host-selected identity, including when no worker publication exists.

Equality establishes agreement on the selected source bytes. It does not prove
correct implementation, compiled layout agreement, identical compiler or SDK,
binary authenticity, runtime behavior, or sandbox cause. Compiled C/Swift layout
checks, signed artifact provenance, and lifecycle/order tests retain those
separate responsibilities. The hash is not a security authentication mechanism.

This exact-match requirement is confined to the jointly built host/worker pair.
The external runner XPC protocol, JSON request and public envelope, and binary
response contracts retain their own boundaries. Validator diagnostic JSON keeps
its own contract; it is consumed independently of this memory interface.


## Shape goldens

Shape goldens record public keys and their JSON types. Producer controls collect
the current shape and write a candidate when it differs. Review the difference,
update the golden and keep its normative definition and example current.
Missing or mistyped required fields still fail semantic admission. There is no
separate version-bump classifier.

## Build stamp

Every envelope carries `build.contract`, `build.describe`, `build.commit`,
`build.version` and `build.number`. Contract is the exact admission identity;
the remaining fields describe the build. Only an annotated release tag on a
clean tree can produce a release contract.
