# Authority, equipment, signing and provenance review proposal

Status: **unaccepted proposal for the Stage 1–2 checkpoint**. No production
admission, signing, worker or schema implementation is changed by this record.
Baseline inspected: `4cd1d6c7f14e3ebacfd2dda219dda85967f64680`. Prototype
sources live under [prototype/](prototype/); execution receipts must be assessed
separately before crediting observations. Root owns all builds and executions.

## Concrete request contract

Admit these actor fields, independently of `sandbox`:

```json
{
  "actor_id": "issuer",
  "equipment": "unentitled",
  "required_entitlements": [],
  "sandbox": {"mode": "unapplied"}
}
```

| Field | Admitted value | Omission | Meaning |
| --- | --- | --- | --- |
| `actors[].equipment` | `"selected"` or `"unentitled"` | `"selected"` | Select one fixed executable owned by the selected service bundle. |
| `actors[].required_entitlements` | Array of unique, nonempty strings | `[]` | Every named key must have the boolean value `true` in the selected actor executable's entitlement read-back. |

Reject explicit null, unknown equipment values, duplicate requirement keys,
embedded NUL, empty keys, nonstring members and unknown actor keys. Proposed
bounds: 64 keys per actor and 255 UTF-8 bytes per key. With at most eight actors,
the key payload is bounded to 130,560 bytes before JSON overhead. This is an
apparatus/request bound, not an OS entitlement-name limit: 64 is generous for
an executable's asserted boolean equipment requirements, while retaining a
small bounded list for admission errors and replies. Do not serialize a separate
copy per scheduled visit. The packet must account for JSON escaping and the
existing complete-request transport limit; this bound does not override that
limit. Independent controls must exercise 64/65 and 255/256 UTF-8 bytes,
including multibyte strings, escaping and total-request exhaustion. No arbitrary
full entitlement plist belongs in this bounded per-actor list.

Equipment and policy mode form all four valid combinations. `unapplied` skips
PolicyWitness specimen policy processing; it neither removes signed
entitlements nor removes inherited restrictions. `unentitled` means **the
variant signed without supplied entitlements**. It never means unrestricted,
no sandbox, ordinary-access success, or a guaranteed ability to issue. An
unentitled actor with a nonempty requirement generally refuses equipment
binding; it must not silently select the other variant.

The built-in runner can produce identical entitlement read-backs for both
variants. Preserve their distinct equipment names and bundle paths anyway;
do not coalesce them, infer selection from equality, or choose either path by
availability. This makes a missing built-in unentitled variant observable.

Retain existing `runner.required_entitlements` and its top-level selector alias
as a requirement on the selected runner's **usual selected worker**. It is a
controller selection preflight, not a requirement on every actor and not a
claim about an unentitled actor. Actor requirements supplement it and travel
over XPC. Do not strip them with controller-owned runner selectors. A simple
mixed specimen uses issuer `unentitled`/`unapplied`, subject
`selected`/`apply`, and puts subject-specific requirements on that subject.

## Bundle and signing ownership

Each selected XPC service owns both fixed paths:

- `Contents/MacOS/pw-probe-runner`: `selected`.
- `Contents/MacOS/pw-probe-runner-unentitled`: `unentitled`.

The build compiles the existing C worker implementation once. Bundle assembly
copies that unsigned artifact into both paths; both receive the same ABI
identity and actor protocol. Sign the selected variant with the selected
runner's worker entitlements; sign the unentitled variant with the identity
alone. Separate signed hashes/CDHashes are expected even when machine code is
the same. Preserve an independently recorded pre-sign input hash and common
build identity; do not claim equality from filenames or post-sign hashes.

The enclosing XPC host keeps its current supplied-entitlement signing policy.
Changing host entitlements to make a child appear ordinary would change the
existing issuer's parent context and is outside this consolidation. The
validator remains identity-only. Remove the declaration issuer helper from
the current inventory once no declaration call path remains. Sign nested
workers and validator before the enclosing service seal and the enclosing app.
BYOXPC install must require both workers, re-sign both with the above distinction,
verify the enclosing seal and each binary, and read each binary back separately.

The host resolves equipment only inside its **own selected service bundle**;
never use the controller app's embedded path for an installed service. Resolution
checks fixed relative paths, regular executable bytes, no path/symlink escape,
valid signature, expected team/signing constraints for that installation,
entitlement read-back and matching worker build/ABI identity. Missing,
unreadable, invalid, stale or incompatible selected equipment refuses binding.
There is no fallback to another variant, the bundled service, another registered
runner, the declaration issuer, or an arbitrary request-provided path.

The same rule applies when built-in entitlements coincide. Validate both
variants in the bundle inventory and public runner validation; execution binds
the actual requested variant. Registry records gain independently named
unentitled-worker signature/entitlement/hash metadata. Existing installed
bundles without the required variant or capability can be listed, reconciled
and removed, but cannot execute the new contract by substitution. Keep pending
cleanup ownership intact. Registry read-back alone cannot make stale disk bytes
current; the launch owner performs the current inspection.

### Proposed service-local inventory (new implementation)

Add `Contents/Resources/worker-equipment.json` inside each XPC service, covered
by that service's seal. This is a new artifact and verifier, not existing
functionality of the app manifest. The build equipment-inventory emitter owns
the initial artifact, and BYOXPC installation has a corresponding writer for
the signing-dependent fields. Both follow one schema and independent controls.

The closed schema is `schema_version: 1`, `runner_protocol` (the current protocol
integer), `worker_identity` (the generator's 64-lowercase-hex build-input/ABI
identity), `unsigned_worker_sha256` (the 64-lowercase-hex hash of the one build
artifact copied twice), and `workers` with exactly two rows. Each row has
`role: selected|unentitled`, its fixed `relative_path` specified above, signed
`sha256` (64 lowercase hex), `cdhash` (40 lowercase hex), `identifier`, `team_id`
(string or null for permitted ad-hoc), and `entitlements_xml` (bounded serialized
XML entitlement plist). Both roles are required and unique; no unknown fields
are admitted. Empty entitlement read-back is serialized as an empty dictionary
plist, not an absent observation. An unentitled row with nonempty parsed
entitlements is invalid.

Bound the complete inventory to 1 MiB of UTF-8 JSON before decoding. Its two
65,536-byte entitlement XML values can expand to 786,432 JSON bytes under the
conservative sixfold escape bound; the remaining bounded metadata fits the
remainder. Paths have the existing path bound; identifier/team each have a
255-UTF-8-byte limit. The 40-hex CDHash format matches the current signing reader
and observed prototype; supporting a different representation requires changing
this versioned schema and its consumers, not accepting arbitrary hex. Compare
parsed entitlement dictionaries semantically, not XML key order.

The inventory carries no hash of its host binary, preventing a cycle with the
service seal. `worker_identity` is the existing identity generator's actual
build-input/ABI identity, not a new claim of an independent source hash.
`unsigned_worker_sha256` is sealed build provenance; the live host does not
pretend it reconstructed pre-sign bytes from a signed binary.

Build sequence: compile one worker; verify its generated identity against the
host and existing build verifier (`--version` only as build equipment, never
as a specimen-time host launch); copy common bytes twice and record their
pre-sign hash; sign/read back selected worker, unentitled worker and validator;
emit this inventory from actual signed worker bytes; sign and verify the
enclosing service and helpers; finish/sign/verify the outer app and its evidence.
The service inventory owns worker resolution; app-level evidence supplements it.

BYOXPC sequence: before mutation, verify the supplied source service seal and
its inventory against both source worker bytes; refuse missing/incompatible
inventory instead of synthesizing provenance from filenames. Preserve the
verified source inventory/build identity in installation evidence. Sign selected
worker with supplied entitlements and unentitled worker/validator without them;
read back new hashes/signatures/entitlements; regenerate the inventory while
retaining verified build identity/pre-sign provenance; sign the enclosing
service with supplied host entitlements. Verify the service and each helper
again before registry publication/bootstrap. A failed rewrite/sign/verify leaves
invalid staged equipment and the existing durable installation-recovery ownership;
never reuse old inventory hashes after re-signing bytes.

At run time, verify the selected host's own current service seal; read and admit
this bounded inventory; compare its `worker_identity` to the host's compiled
`PWShmLayout.abiIdentityHex`; then verify/hash/read back **both** fixed production
worker paths against their inventory rows, including an unused role. Actor
execution requires a complete verified pair. The ordinary nonactor route is
unchanged. Registry read-back or an external app
manifest cannot supply the expected identity. No child process is launched to
discover identity during binding. Observable replacement after static binding
is handled by the separately specified owned-live-code comparison before any
scheduled activation, with its stated race/immutability limits.

The existing binary identity/manifest machinery identifies the intended worker
implementation. It does not by itself prevent replacement between a static
inspection and spawn. The proposed live code observation below detects an
observable identity mismatch after setup and before scheduled visits. A complete
immutability guarantee is not claimed; privileged replacement and dynamic
linker behavior require their own threat model.

## Controller, direct XPC and binding sequence

1. Both public and direct-XPC admission validate actor field shapes and bounds
   into the same resolved actor operation plan, before acquiring actor resources.
2. Controller selection checks the existing runner requirements and can preflight
   actor equipment from current app/registry inspection. Its preflight is not
   authoritative evidence of worker execution.
3. The host binds each actor to a current bundle-local equipment record, including
   path, actual hash, signature, ABI/build identity, entitlement read-back and
   requirement decisions. A failure produces an equipment-binding refusal with
   the actor association and no fabricated process or policy-application result.
   The two packaged-role rows hold artifact inspections only (explicit test
   overrides add their own rows below). Evaluate and retain
   requirements separately for every actor, even when several actors name the
   same inspected path. One actor's unsatisfied requirement does not alter another
   actor's decision or turn a valid shared artifact inspection into an invalid one.
4. Only successfully bound equipment may launch. All actors resolve setup before
   schedule execution as the lifecycle proposal requires. An equipment binding
   failure should refuse the run before launching any actors, so a mixed
   arrangement cannot become a silently reduced experiment.
5. After resolving setup for the population, inspect each owned live worker while
   parked, before any scheduled activation or query collection. Obtain its
   dynamic code reference by PID, validate it, read its associated static signing
   metadata, and compare to the bound record. This adds host inspection to the
   existing parked state; it adds no pre-policy worker rendezvous or native
   wait. Any required live inspection failure withholds every scheduled
   activation and triggers bounded cleanup. Preserve already observed
   setup/application facts; do not claim that identity refusal prevented policy
   application. Unresolved cleanup retains its own failure and ownership.
   Inspection is required only for an actor with usable setup that could
   activate. An unlaunched actor records `execution.status: unobserved` with
   `reason: not_launched`; a setup-failed actor uses `reason: setup_unavailable`.
   Both remain ineligible under existing scheduling rules, and their absence of
   inspection does not newly cancel healthy actors. Only a reached required
   inspection failure for an otherwise usable actor cancels the whole schedule.

Direct XPC cannot trust entitlement assertions supplied by a controller or a
cached registry. It uses the host's same binding and live-child checks. It cannot
interpret `runner.required_entitlements` because that is a controller selector;
it can and must enforce `actors[].required_entitlements` from the request.

### Exact actor test-override proposal

Add `_test_overrides.actor_equipment_executable_paths`, a closed, nonempty
object with optional keys `selected` and `unentitled`. Each supplied value is an
absolute executable path, subject to the existing path UTF-8 bound; reject null,
nonstring values, NUL, relative paths and unknown keys. An omitted role keeps
its production path. Reject `_test_overrides.worker_executable_path` in actor
form even when the new map is present; keep that old global field for the
ordinary form. Echo the admitted override and the actual binding source.

Verify the complete sealed production inventory and both production-role
artifacts first, even when a role is overridden. An override never repairs a
missing/incompatible installation and never acts as fallback. Then inspect each
explicit override as a separate binding with `source: test_override`; actual
path/hash/signature/entitlements are mandatory observations. The source role's
production binding remains present with `source: packaged`. Actor
`binding_ref` names the override record when used. The original role selector
does not claim that override bytes have the production role's signing authority.

Production binding IDs remain `selected` and `unentitled`; override binding IDs
are `override-selected` and `override-unentitled`. Consequently there are at
most four static binding/read-back records and eight live actor read-backs.
Override read-back IDs are `binding-override-selected` and
`binding-override-unentitled`. The complete equipment-entitlement payload bound
becomes 12 × 65,536 = 786,432 raw XML bytes, conservatively 4,718,592 JSON bytes
under sixfold escaping, plus the separately bounded metadata. This maximum
includes controls and must enter the reply-cap proof; ordinary production actor
execution still has two static roles and at most ten total read-backs.

Only explicit test overrides may accept a valid ad-hoc fixture signature or a
valid signature from a different team, recording its actual identity and
`implementation_identity: unverified_fixture`. A production binding records
`implementation_identity: inventory_verified` and retains its production signing
rules. Unsigned, invalid-signature, missing, unreadable, nonregular or
nonexecutable override paths are structurally admitted as test input but refuse
equipment binding before any worker launch, using the existing closed reasons.
There is no opt-out from signature validity or live-code/path/hash comparison.
Per-actor required entitlements are checked against the actual override's
read-back and remain mandatory. An override of the `unentitled` role can carry
entitlements to observe inherited restrictions, but receives no unentitled-role
signing credit; its explicit source and read-back prevent that claim.

An override path alone supplies no trusted compiled ABI/source identity. Do not
execute it to discover one and do not accept a user-declared identity as verified.
The host still sends its current worker ABI header; the existing native worker
acceptance/refusal and setup publications determine whether that fixture reaches
usable setup. Thus an ABI-mismatching signed fixture is structurally admitted
and may launch, but the expected control outcome is setup refusal, with preserved
native/lifecycle evidence and no visits. A fixture that forges compatible replies
is constructed test evidence, never proof of production implementation identity.
For a fixture that reaches usable setup, the same required owned-live-code
inspection must match the actual override bytes before any activation. This
checks which fixture ran without upgrading its unverified source/ABI provenance.

The existing internal `CWorkerInput`, scheduler and spawn-injection factories
remain available for direct native/driver controls. Tests requiring a genuine
spawn failure after successful binding use those internal seams; a missing-path
override now tests binding refusal. Overridden executions can establish native
observations, fixture failure propagation and custody/ordering behavior along
the exercised path. They cannot establish production bundle resolution,
production-role signing authority, production source identity or effective
authority inferred from a selector. Keep separate no-override signed-equipment
controls for those properties.

## Provenance: requested, inspected and executed

Emit one run-wide table of inspected equipment, plus each actor's association.
Do not duplicate the same static inspection as several independent observations.
Proposed actor evidence contains `equipment.requested`, `equipment.resolved`,
`equipment.binding_ref`, its bounded requirements/decisions, and independently
observed process identity. Keep these three layers distinct:

| Layer | Producer and minimum facts | Limits |
| --- | --- | --- |
| Request | admitted actor selector, default resolution and requirement keys | Specifies intent only. |
| Inspected artifact | host binding record: fixed bundle/path, file identity and SHA-256, ABI/build identity, signature CDHash/team/id, entitlement read-back, validation results and observation timing | Establishes the inspected bytes and their signed metadata, not execution or effective permission. |
| Running child | host's owned spawn PID/parent identity, parked live code reference and dynamic validity, associated signing CDHash/path/entitlement read-back and inspection status | Associates an owned live process with the bound code. This is not an effective-runtime entitlement evaluation. Missing or failed inspection is explicit, never filled from static metadata. |

Host inspection consumes the remaining existing setup/lifetime allowance;
completion must precede the first scheduled activation, with a host monotonic
observation time and explicit eligibility decision. Preserve the native status of
inspection failures; neither a missing process nor a stale PID authorizes
inspection/termination of another process. A worker that exits before the
observation remains unobserved, even if a successful spawn named a valid path.

Read-back of `true` keys supports the requirement contract; it does not establish
that all entitlements are effective in the current OS or that a native call is
permitted. Record fresh access, issue, consume and release separately. Similarly,
the existing host `pid` and launch path cannot fill in a missing actor PID.

### Closed equipment evidence and refusal vocabulary

The exact run-result table names are `equipment_inventory`,
`equipment_bindings[]` and `equipment_entitlements[]`. They are present for actor
execution, including empty tables when inspection never reached a row; they are
absent for the ordinary nonactor execution form. The following shapes are
proposed schema definitions, not already emitted fields:

- `equipment_inventory`: `path` (the host's own fixed service-local inventory),
  `status: verified|refused|unobserved`, optional `sha256` (only after bytes were
  read), `schema_version`, `worker_identity`, `unsigned_worker_sha256` (only after
  successful schema admission), `seal_osstatus` (only when verification returned),
  and optional `reason`/`error`. The inventory is singular; bindings reference this
  same verified inventory. Unknown/unreadable inventory has no invented identity.
- `equipment_bindings[]`: `binding_id: selected|unentitled|override-selected|override-unentitled`,
  `role: selected|unentitled`, `source: packaged|test_override`,
  `implementation_identity: inventory_verified|unverified_fixture`,
  `relative_path` (only packaged), `path`, `status: bound|refused`, optional `reason`,
  `expected_sha256`, `expected_cdhash`, `sha256`, `cdhash`, `identifier`, `team_id`,
  `entitlements_ref`, `signature_osstatus`, `entitlements_match`, and `error`.
  Expected hashes appear only for production rows after a verified/admitted inventory supplies them;
  actual values appear only after the corresponding observation. A `bound` row
  requires, for packaged, verified inventory, matching hashes/CDHash,
  valid signature, matching parsed entitlements and host/worker identity
  compatibility. A test_override bound row instead requires the explicit override
  inspection checks above and remains unverified_fixture. `team_id: null`
  means an observed permitted ad-hoc signature; absence means not observed.
- `equipment_entitlements[]`: `entitlements_id`, `source: binding|execution`,
  `binding_ref`, optional `actor_id` (required for an execution read-back),
  `status: observed|failed`, optional `raw_plist` (the bounded XML serialization),
  and `error`.
  Canonical IDs are `binding-<binding_id>` and `execution-<actor index>`;
  at most twelve records. Do not deduplicate live actor
  observations into static observations even if their bytes match. This table
  omits a second full `granted` key list: producer and independent consumer derive
  boolean-true keys from the observed plist; per-actor requirement decisions stay
  explicit. Failed read-back has no empty plist that could be mistaken for an
  observed empty entitlement dictionary.

`error`, when present, is `{operation, domain?, code?, message?}`. Its operation
is a closed inspection step (`service_seal`, `inventory_read`, `inventory_decode`,
`worker_path`, `worker_hash`, `worker_signature`, `worker_entitlements` or one of
the four live Security operations below). Domain/code are preserved only when
the called interface returned them; a schema mismatch has a reason and bounded
message, never a fabricated native error. Domain is limited to 128 UTF-8 bytes,
message to 1,024. Expected hashes do not substitute for missing actual hashes.

Both production-role inspections and any explicit override inspections are planned;
retain each reached row even when another
refuses. If service verification/admission prevents role inspection, the binding
array is empty and the inventory refusal supplies the evidence. A binding-stage
refusal uses `normalized_outcome: runner_failed`, nonzero `rc`, no actor launch,
and the singular `preparation_failure` below. It is not `bad_request`: admitted
equipment spelling is valid even when the installation is unavailable.

Proposed per-actor `equipment` fields are `requested` (null only when the request
omitted it), `resolved` (`selected|unentitled`), `binding_ref`,
`required_entitlements`, `requirements_status` (`satisfied|unsatisfied|unobserved`),
`missing_requirements`, and `execution`. Record an omitted default in `resolved`,
not as an explicit request. `missing_requirements` is present only after successful
read-back evaluation. Failed inspection cannot satisfy requirements.

`execution` has `status` (`matched|mismatched|inspection_failed|unobserved`),
`pid` and owned-child association, `observed_at_monotonic_ns`, `path`, `cdhash`,
`identifier`, `team_id`, `entitlements_ref`,
`native_observations`, `reason`, and `eligible`. Optional facts appear only when
observed. `native_observations` is a fixed maximum of four records for
`guest_code`, `dynamic_validity`, `associated_static_code`, and
`signing_information`, each with `attempted` and its actual `osstatus` when
returned. Do not encode Security framework status as errno. Entitlement data
uses a run-wide read-back record; the full plist is not duplicated per phase.
Proposed new equipment bounds: 65,536 UTF-8 bytes per serialized XML entitlement
plist read-back before JSON encoding, at most four static bindings (two production
plus two explicit override fixtures) and eight live read-backs (one per actor,
referenced again by later phases), 1,024 UTF-8 bytes per inspection diagnostic, and
the existing path/string field bounds for paths and signature labels. Exceeding
read-back storage is `entitlements_unreadable` or `signing_readback_failed` with
`observation_limit` as the native-observation diagnostic; never truncate and then
accept requirements. The raw entitlement contribution is at most 786,432 bytes,
or conservatively 4,718,592 JSON bytes under sixfold escaping, plus bounded
labels and observations. Add this geometry to the response-cap proof rather
than assuming that existing large transport capacity proves the new bound.
This is an entitlement-payload bound, not a whole-row bound: separately account
for paths, signature labels, native statuses and diagnostics. Use the same exact
serialization definition in host production, controller equipment-dossier
interpretation, direct-XPC admission and independent readers. Compare parsed
entitlement dictionaries semantically; XML key order is not an authority difference.

Worker ABI/build identity belongs to the inspected binding. The current C worker
compares the host-provided ABI identity to its compiled constant before accepting
the header; it does not independently publish its own identity string. A matched
live CDHash associates the inspected implementation with the process. Do not
copy the host-written ABI string into an alleged worker-origin identity field.

Artifact bindings have `status: bound|refused`. Closed binding refusal reasons:
`missing`, `not_regular`, `not_executable`, `outside_bundle`,
`signature_invalid`, `signature_unreadable`, `entitlements_unreadable`,
`worker_identity_mismatch`, `inspection_failed`. The additional actor-specific
binding-stage reason `requirements_unsatisfied` belongs to that actor's requirement
decision, not to the shared artifact inspection.
Invalid public equipment spelling is request admission refusal and creates no
binding. A missing required role in an old installation uses `missing`,
with the unsupported-installation diagnostic maintained separately.

Closed execution reasons for a nonmatched result: `not_launched`,
`setup_unavailable`, `process_unavailable`, `ownership_unresolved`,
`code_lookup_failed`, `dynamic_validation_failed`, `signing_readback_failed`,
`executable_mismatch`, `signature_identity_mismatch`, `entitlement_mismatch`,
`requirements_unsatisfied`, `inspection_deadline`. A matched result has no
failure reason. Exit before inspection is unobserved/process_unavailable,
not a signed-identity mismatch.

Use singular `preparation_failure` only for a **before-launch** summary:
`{stage: "resolved_plan"|"equipment", code:
"inconsistent_assignment"|"equipment_binding_refused", actor_id?, binding_ref?,
reason?}`. Only the matching pairs resolved_plan/inconsistent_assignment and
equipment/equipment_binding_refused are valid. All per-binding inspection
facts/failures remain in their records; the singular summary does not replace
them. `reason` for equipment uses the closed binding-reason vocabulary above.

Runtime live-inspection status/reason/eligible remains exclusively in
`actors[].equipment.execution`. Any required inspection failure produces
`normalized_outcome: runner_failed` and
`schedule.cancelled: "equipment_execution_<reason>"`, using the closed
execution-reason suffix above, with **all activations withheld**. It must not
produce `preparation_failure` after actors have launched. Preserve setup,
application and cleanup observations; independent readers must reject an
already-launched runtime failure presented as a before-launch refusal.

## Source-grounded current behavior and gaps

| Source inspected | Current mechanism and consequence |
| --- | --- |
| [ActorOrchestration.swift](../../runner/Sources/PWRunnerCore/ActorOrchestration.swift), `ActorTranslation.init` | One `workerExecutablePath` becomes every actor's `CWorkerInput`. Independent per-actor paths already fit the lower scheduler input but current public translation cannot select them. |
| [ActorSession.swift](../../runner/Sources/PWRunnerCore/ActorSession.swift), launch code | Actor launch uses `posix_spawn`, empty environment, explicit FDs and null stdout/stderr. It records PID; it does not inspect the live signed executable per actor. |
| [PWRunnerActors.swift](../../runner/Sources/PWRunnerCore/PWRunnerActors.swift) | Actor request keys are currently `actor_id` and `sandbox`; actor launch has PID, parent PID and descriptor context, no per-actor equipment/read-back. |
| [runner_select.rs](../../controller/src/runner_select.rs), `enforce_required_entitlements` | Controller checks selected worker `granted` keys; boolean false and read-back failure do not satisfy requirements. Runner selector fields are controller-owned. |
| [runner_manager.rs](../../controller/src/runner_manager.rs), `sign_install_tree`, `validate_record` | Selected worker and host receive supplied entitlements; validator and declaration issuer identity-only. Per-binary read-backs/validation exist and must expand to the surviving two worker roles. |
| [check_actor_inherited_restriction.py](../../tests/suites/witness_contract/opt_in/check_actor_inherited_restriction.py) | Actual worker copy inside a minimal app bundle is signed with App Sandbox and exercised through one global override. It tests own signed restriction despite `unapplied`, not mixed worker selection. |
| [native.c](../../tests/fixtures/sandbox_extensions/native.c) | Same native fixture executable executes host/issuer/subject roles, with owned child waits, transient token channel and fresh access boundaries. It is independent equipment, not the production actor ABI. |

The production prototype deliberately enters below public admission to exercise
the existing per-actor `CWorkerInput` path. It proves nothing about the proposed
request parser, bundle ownership checks, pre-activation live identity check, registry
migration or new reply reader rules. Those remain candidate implementation tests.

## Evidence assertions inspected and applicability

Native `sandbox_extensions_native/feasibility` checks native issue/consume/release
availability and results, real handle acquisition, controlled fresh contents and
file identities, baseline and no-consume/no-predicate/different-target controls,
owned reap, issuer-live vs issuer-reaped ordering, token erasure/confinement and
allocation controls. Its checker explicitly accepts unchanged/unavailable queries,
failed native release and continued fresh access after release. It does not
require revocation or prediction/enforcement agreement. The directory case adds
fresh existing-file changes, exclusive creation and independent persistence.

Root reports fresh passes at
`tests/out/runs/extension-consolidation-native-20261105`; these artifacts are
gitignored and local-only. They replace any need to credit an unidentified old
native run. They support ordinary native authority and bounded lifetime effects,
not mixed production worker signing or XPC transport.

Retained `tests/out/runs/actor-passes-final-controls-02` (run
`20261104T201833Z_59c91237`) contains `witness_contract/actors_byoxpc` and
`witness_contract/extensions_byoxpc`. Its `review/source.json` identifies an
unknown exact source commit, base `a54da01263472b38036ed9e524a1a9d143c1cc34`,
dirty snapshot, and app build 1116; its repair commit is expressly not the build
source. `tests/RETAINED.json` marks source null. Do not relabel it baseline 4cd1.
The historical inherited-restriction observation records an ordinary worker's
owned-target read and allow query; an App Sandbox-signed copy, still unapplied,
has read failure/errno 1 and deny query for that actor PID while reading a system
file. The checker separately asserts clean reap, distinct PIDs, zero specimen
application and independently unchanged target contents. It reads entitlements
from the copy and verifies its signature. It does not establish live CDHash or
mixed signed variants. Those raw observations remain historical context; exact
dependency applicability is not mechanically established by this record, so
they are **not fresh baseline acceptance credit**. Root is rerunning current
BYOXPC controls.

Existing BYOXPC declaration controls inspect ordinary issuer signature/read-back
separately from entitled worker and host, compare dossier hashes to installed
bytes and baseline, and remove/restore the owned helper to require refusal.
They support the distinction this proposal must preserve, not an equivalence
between helper and actor variant. Existing actor BYOXPC controls hold the issuer
helper aside and still issue/consume through the actor form, but all actors use
the same selected worker. Their passing result cannot establish mixed equipment.

## Prototype and candidate controls

[run_actors.py](prototype/run_actors.py) snapshots production Swift sources,
builds a signed isolated driver, copies the actual shipped C worker twice,
signs selected/host with `allow-jit=true` and the other worker without supplied
entitlements, and uses the unchanged scheduler/custody/protocol/worker/validator.
The signed key distinguishes equipment; successful extension behavior is not
attributed to that key. The driver obtains the actual live actor code by PID
through Security APIs at collection and retains CDHash/path/read-back separately
from native observations. It includes a deliberately substituted selected
issuer and requires its live entitlement observation to reject an unentitled
claim. A separate App Sandbox-signed production-worker copy tests an unapplied
subject's owned-target restriction against ordinary and system-file controls.
This does not exercise an App Sandbox-signed XPC host or the proposed
before-activation inspection; live observations occur during collection after
activation in this prototype. Dynamic validity plus associated signing metadata
does not claim SecTask effective-runtime entitlement evaluation.

The driver owns direct actor children through the production scheduler. Its
outer group deadline is emergency containment, not proof of clean actor reap.
Retain any failed run and cleanup uncertainty. The App Sandbox experiment
records a unique container's preexistence, postexistence and attempted removal;
an unremoved container is an outstanding owned resource, not verified cleanup.
No launchd installation, registry mutation or runner removal occurs.

[run_authority.py](prototype/run_authority.py) is secondary independent-native
equipment, generated from the retained original fixture source. It varies
signed role paths and can apply a targeted read restriction in the parent
before spawning children. That contrast tests the limit of `unentitled` under
inherited restrictions. It is not a production actor execution. Root must
record its actual results or leave this contrast pending.

Required implementation controls include missing/modified/wrong-team/wrong-ABI
unentitled variants; selected replacement after static binding; identical
built-in entitlements without fallback; static vs live mismatch; direct XPC
actor requirement refusal; controller preflight pass with host refusal;
false-valued/absent/unreadable requirement keys; all four equipment/mode pairs;
mixed same-process-lifetime issuer/subject execution and re-delegation; and
negative same-selected substitution. Test identity refusal against independent
setup/application and activation observations so it cannot erase an application
or permit a scheduled action. Preserve raw observations and independent cleanup.

The review must accept or revise the field names/default, requirement bounds,
selected-only legacy runner requirement meaning, concrete bundle paths,
unchanged host signing context and the added before-activation live identity check.
The remaining non-universal claim is explicit: neither an empty read-back nor
a bounded successful prototype establishes unrestricted authority under all
supplied entitlements, inherited sandboxes or macOS versions.

## Executed production prototype observation

Root executed prototype attempt 01, which failed compilation before signing or
launch. Its diagnostic required converting the dynamic `SecCode` reference to
the associated `SecStaticCode` before reading signing information. Attempt 02
incorporates that repair and resolves the Swift build product using
`--show-bin-path`. The failed attempt remains distinct evidence.

Successful attempt 02 is retained locally at
`/private/tmp/pw-equipment-prototype-20261105-02` (outside git). The driver starts
from two byte-identical copies of app build 1140's worker, pre-sign SHA-256
`9f5e68527048d7282d6763034099c3d1978bb5ad6d4822f30109e2fc28ecb815`.
Root's command was the `run_actors.py` invocation above with this fresh output,
`dist/PolicyWitness.app` and Developer ID identity
`Developer ID Application: Adam Hyland (42D369QV8E)`.

The issuer PID 85822 published `unapplied_declared` and zero applications; subject
PID 85823 published one application. Their live code references validated,
associated CDHashes differed, and associated entitlement read-backs were `{}`
and `{"com.apple.security.cs.allow-jit":true}` respectively. Subject baseline
read failed with EPERM; issuer fresh read and subject post-consume fresh read
returned the independently retained target bytes. Consumption returned handle 1
and release returned 0. The post-release fresh read failed with EPERM in this
execution only; no revocation invariant is inferred.

The deliberate same-selected-worker substitution used PIDs 85829/85830. Native
lifecycle behavior still succeeded, while the issuer's associated read-back
contained `allow-jit=true`; the independent equipment assertion therefore
rejected its claim to unentitled equipment. This establishes why lifecycle
success alone cannot verify the authority arrangement. The signed App Sandbox
worker PID 85843 was unapplied with zero applications, failed the owned-target
read and read the system file; ordinary selected PID 85840 read the target.
All actor processes in these executions were observed reaped by the production
scheduler and had clean recorded exits.

**Cleanup remains incomplete for the App Sandbox container.** The unique owned
container did not preexist and remains at
`/Users/raccoon/Library/Containers/com.policywitness.test.equipment-5baed78c80dc4eeeb2b95b9f10113600`.
`container-ownership.json` and `remove-container.{command.json,stderr}` in attempt
02 record failed removal (`Operation not permitted`). Preserve these receipts
and the resource ownership until absence is verified; process reap is not
container removal. No registry or launchd service was installed by this prototype.

Root's exact production-prototype invocation from the repository root:

```sh
tests/lib/python.sh -B -S records/extension-consolidation-2026-11-05/prototype/run_actors.py /private/tmp/pw-equipment-prototype-20261105-02 dist/PolicyWitness.app 'Developer ID Application: Adam Hyland (42D369QV8E)'
```

The secondary invocation was:

```sh
tests/lib/python.sh -B -S records/extension-consolidation-2026-11-05/prototype/run_authority.py /private/tmp/pw-authority-inheritance-20261105-01 'Developer ID Application: Adam Hyland (42D369QV8E)'
```

This secondary run **failed**, and remains a failed investigative run. Its four
ordinary cases (`lifecycle`, `issuer_exit`, `no_consume`, `no_predicate`) finished
before the restricted-parent case and satisfied the driver's local assertions.
The restricted-parent command returned 1, so the driver stopped before its
post-command assertions; it wrote no successful overall summary.

The retained `restricted-lifecycle.stdout` nevertheless establishes narrow
observations: parent sandbox application returned 0; the signed unentitled
issuer's fresh baseline open returned -1/EPERM and the entitled subject's
pre-application fresh open also returned -1/EPERM. The subject's own
`sandbox_apply` then returned -1/EPERM and the worker exited 97, observed reaped
(raw wait status 24832). Issuer native issuance returned nonnull; the issuer
exited 0 and was also observed reaped. No consume or release occurred. Thus this
configuration supports inherited starting restrictions and refutes treating
unentitled as unrestricted; it does not establish a successful nested application
or extension lifecycle, or attribute every failed native call solely to sandbox.

`worker_erased_channel` is false, so no worker-side erasure credit is available.
The fixture's host cleanup observes both owned children reaped, erases the shared
token region after that observation, checks serialized-report token confinement
(`token_guard_passed: true`), erases its private token copy, and unmaps the regions.
The failed worker publication does not replace those separate cleanup facts.
No container or installed service is created by this independent fixture. Stop
the investigation at these bounded observations; rerunning merely to produce a
green restricted lifecycle would not resolve a requirement of this proposal.
