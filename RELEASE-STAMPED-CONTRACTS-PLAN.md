# Reduce schema and contract numbering

Status: proposed; investigation and implementation plan only. No implementation
changes have been made for this plan.

## Basis and intended result

This investigation uses the local checkout at
`76de8ca34c0be5948e10c54709ff66d8a12ee87a` (`v0.3.4-126-g76de8ca3-dirty`),
inspected on 2026-11-08. During inspection, HEAD advanced to
`6b8d7f0c9ea5e295f6229c83171792d8f69108d9`; the intervening diff changes only
`docs/FOOTPRINT.md` and `runner/WORKER-WAIT-EXPLORATION-PLAN.md`, not the
implementations inventoried here. At the start, `JSON-AS-PORCELAIN-PLAN.md` and
`docs/FOOTPRINT.md` had pre-existing modifications; they are not changes made by
this investigation. Source inspection establishes the findings below; no new
signed build, live runner experiment, or battery result is claimed. Linked
source files describe this checkout, not necessarily the last release.

The plan follows [planning guidance](../CONTRIBUTING.md#planning-a-change) and
[records guidance](AGENTS.md). The investigation is included here so execution
and acceptance review do not need a second inventory or a permanent registry.

PolicyWitness ships an instrument: binaries, public input and evidence
contracts, and a guide. Make the release the public contract unit. Remove
independent revision sequences that do not enable a decision beyond identifying
that unit, validating the current record, or identifying its producer. This
does **not** remove admission, evidence validation, ownership checks, or exact
agreement at an unsafe component boundary.

The recommended end state is:

- One public contract identity: `release:vX.Y.Z` for a clean annotated release,
  or `development:<source-snapshot-id>` for an unreleased build. No independent
  request, reply, envelope, or XPC protocol numbers.
- One explicit assertion of the intended public contract in each saved
  specimen. There is no implicit acceptance of an older specimen, even when its
  shape remains valid. Every release is a new unit, including a release whose
  public semantics happen to be unchanged.
- Producer identity on independently produced documents and streams; nested
  records inherit their admitted producer context. Extracted evidence must
  retain that context. Provenance is not an assertion of requested intent.
- The existing exact host/worker source identity and fixed bootstrap checks
  remain. Bundle-component source agreement, signed inventory, layout checks,
  and observation validation keep their separate purposes.
- Current repository manifests and test fixtures are validated as current
  structures, without revision counters. Durable receipts identify their
  producer and retain their ownership and integrity evidence.
- A short, authored account of contract differences since one named release,
  with links to current definitions, accompanies the working guide. It has no
  per-surface counters and makes no compatibility decisions for the program.

No general backwards-compatibility promise, historical run adapter, negotiation,
capability exchange, automatic specimen migration, new schema language, or
second evidence interpretation framework is part of this work.

## Investigation: what actually moves separately

The search covered `schema_version`, protocol/ABI/version constants, generic
`version` fields, numbered profile names, release stamps, generator targets,
and their reads and writes in the controller, native helpers, runner/client,
build scripts, documentation generators, fixtures, test libraries, release
tooling and investigative fixtures. Historical fixtures, reports and archives
were distinguished from current producers. The inventory below groups copies
of one identifier together; a fixture carrying `schema_version: 27` is not
another independent contract.

The important demonstrated boundaries are these:

1. The app's Rust controller, Swift client, Swift host, C worker and C validator
   are assembled together by [build.sh](../build.sh) and
   [meson.build](../meson.build). Rust `sbpl-check` includes the controller's
   envelope renderer. There is no independently released validator, profile
   receipt library or equipment-manifest package in this checkout.
2. A copied and re-signed XPC service can be installed independently and outlive
   the app. [runner_commands.rs](../controller/src/runner_commands.rs) admits
   its advertised protocol at install and verify;
   [runner_select.rs](../controller/src/runner_select.rs) admits the registry
   protocol before run. [PWRunnerService.swift](../runner/Sources/PWRunnerCore/PWRunnerService.swift)
   and [PWRunnerClientSession.swift](../runner/Clients/PWRunnerClient/PWRunnerClientSession.swift)
   independently admit the reservation control before submission. A plist or
   registry claim alone is not proof of the live peer's participation.
3. The registry has a deliberately different lifetime and decision. Its loader
   accepts retired runner-kind spellings and optional older metadata for
   inspection/removal. Unknown equipment snapshots are retained opaquely.
   Execution validates current equipment separately. See
   [runner_manager.rs](../controller/src/runner_manager.rs), particularly
   `load_registry`, `RunnerRecord`, `PendingCleanup`, and
   `require_current_protocol`. Removing a runner requires ownership and observed
   absence, not merely a recognized protocol or label prefix.
4. Saved specimens and result JSON survive the executable. Current semantic
   readers are the Rust controller, Swift codecs, Python
   [consumer.py](../tests/lib/consumer.py),
   [document_versions.py](../tests/lib/document_versions.py), lifecycle and
   actor readers, and suite-specific checkers. They reject unsupported current
   wire numbers rather than translating historical runs. Local code and docs
   demonstrate these consumers; no evidence was found of a separately shipped
   general-purpose consumer requiring its own version sequence. External
   downstream consumers remain possible, but their existence or compatibility
   needs cannot be inferred from a schema field.
5. Build directories, registry and cleanup records, retained tests and release
   archives survive source updates. Release tooling already has narrowly bounded
   historical behavior: [release_runs.py](../tests/lib/release_runs.py) accepts
   evidence bundle schemas 2/3, and `producer_contract` requires a positively
   identified historical source when the newer execution contract is absent.
   This is an actual historical consumer, not a reason to make every persistent
   record maintain an independent counter.
6. Development combines source-built tests with signed artifacts and explicitly
   instrumented copies. Existing worker identity, source/binary hashes,
   fixture inventories and build provenance distinguish those combinations.
   An app's nearest release tag alone does not. The current worker identity
   deliberately excludes the top-level Rust controller, Swift client entry and
   session code, and C validator; it cannot serve as the whole-app identity.

### Public contracts and nested records

Disposition terms in the tables: **consolidate** means use the one release or
development contract; **remove** means keep structure/meaning validation but
stop numbering it; **replace** means an existing source/ownership identity or
the common build provenance supplies the decision; **retain** means a distinct
identifier has a demonstrated purpose that the public contract cannot serve.

| Identifier now | Producer, actual readers, copies and evidence | Decision now; proposed disposition and consequence |
| --- | --- | --- |
| Request `schema_version = 6` / `request_schema` | [contract.json](../docs/contract.json) → [generate_contract.py](../docs/generate_contract.py) → Swift `PWContract.requestSchema`, Rust `REQUEST_SCHEMA_VERSION`, Python `REQUEST_SCHEMA`. [request_patch.rs](../controller/src/request_patch.rs) checks before selectors/augments; [PWRunnerRequest.swift](../runner/Sources/PWRunnerCore/PWRunnerRequest.swift) independently checks before orchestration. Specimens, guide examples, comparison matrix and admission controls carry copies. | Establishes requested shapes **and meanings**, not producer provenance. **Consolidate** into required root `contract`. Preserve controller-first admission, direct-XPC admission, closed keys, integer/type distinctions where still relevant, bounded structured diagnostics and refusal before children/effects. Without a replacement assertion, valid-shaped old requests could silently acquire new meaning. |
| Runner reply `schema_version = 27` / `response_schema` | `PWRunnerRunResult` in [PWRunnerReply.swift](../runner/Sources/PWRunnerCore/PWRunnerReply.swift), including degraded serialization in `PWRunnerService`; Rust [run_flow.rs](../controller/src/run_flow.rs), runner verification projection, Swift decode/encode and Python consumers gate it. Generated Rust/Swift/Python copies; response golden and many fixtures. | Controls interpretation of an independently arriving reply. **Consolidate** into the reply producer's common contract/source identity. Keep admission before derived claims, unchanged raw retention and separate malformed/unsupported outcomes. A controller stamp cannot substitute for the external host's producer. |
| Controller envelope `schema_version = 12` / `controller_envelope` | [json_contract.rs](../controller/src/json_contract.rs), shared by `policy-witness` and `sbpl-check`; Python envelope reader, Rust [policy_check.rs](../controller/src/policy_check.rs), helper tests and envelope golden. The same frame is retained at `data.policy_check.envelope`. | Selects envelope interpretation and helper admission. **Consolidate** into the envelope `build` producer context. Nested helper envelopes retain their own producer because they are separate outputs. Preserve helper kind/outcome validation, status copying and opaque rejected arrays/scalars; never recover a helper claim from rejected output. |
| Runner `protocol_version = 3`, `runner_protocol`, `PWRunnerProtocolVersion` | Generated Swift/Rust/Python/plist copies; [PWRunnerTransport.swift](../runner/Sources/PWRunnerCore/PWRunnerTransport.swift), service and client reservation messages, `runner_client_capture`, Rust [runner_client.rs](../controller/src/runner_client.rs), [bundle.rs](../controller/src/bundle.rs), registry records, equipment inventory, Python [runner_client_capture.py](../tests/lib/runner_client_capture.py). Reservation and BYOXPC controls exercise it. | Refuses incompatible peers before execution and admits capture before host reply. **Consolidate** every occurrence under the common contract and source binding. Keep effect-free reservation, same-connection token ownership, single submission, absolute deadline, capture completeness and no replay after invocation. A source stamp merely printed in the final envelope would be too late. |
| `compiled_profile.schema_version = 2` | [PWRunnerProfileCapture.swift](../runner/Sources/PWRunnerCore/PWRunnerProfileCapture.swift) builds/validates the nested receipt; Rust `compiled_profile_problem`, Python consumer and actor readers, [compiled_profile.json](../tests/fixtures/contract/compiled_profile.json), Swift profile controls and live capture tests read it. Ordinary and per-actor replies use it. | Selects receipt context rules. **Remove** the independent marker; inherit admitted reply context, and require explicit context for standalone decode. Keep `worker`/`before_apply`, nonce, actor/worker PID association, status rules, completeness, byte length/hash and source/parameter bindings. The receipt is not a separately evolving compiled-profile interchange format or kernel readback. |
| Validator NDJSON `schema_version = 1` | [sb_api_validator.c](../controller/tools/sb_api_validator/sb_api_validator.c) emits verdict/error/status/result kinds. [ValidatorClient.swift](../runner/Sources/PWRunnerCore/ValidatorClient.swift) admits batch verdicts; standalone validator suites, bridge and lifecycle fixtures consume/produce the other modes and raw lines. | Host requires verdict kind, integer marker and field invariants before association. **Consolidate** producer context into the common build/contract for this independently emitted stream; no validator-specific sequence. Preserve bounded LF/UTF-8 decoding, first-fault retention, rc/errno/type checks, diagnostic vocabulary and query association. Keep kind discriminators. Raw lines exported alone need producer context. |
| `worker-equipment.json.schema_version = 1`; nested `equipment_inventory.schema_version` | [build_equipment.py](../tests/build_equipment.py) emits the signed inventory; installer rebinds it after signing. Rust `WorkerEquipmentInventory`, Swift [ActorEquipment.swift](../runner/Sources/PWRunnerCore/ActorEquipment.swift), [PWRunnerEquipment.swift](../runner/Sources/PWRunnerCore/PWRunnerEquipment.swift), Rust/Python actor-evidence validators, build evidence and BYOXPC fixtures read it. | Recognizes equipment structure. **Remove** its sequence and nested schema echo; **consolidate** its duplicate runner protocol into the service producer context. Retain service seal, two unique roles and safe relative paths, signature/CDHash/entitlement observations, common unsigned-worker hash, and exact worker identity. Registry snapshots stay opaque for recovery. Persistence of a copied inventory does not require another counter. |
| `Evidence/manifest.json.schema_version = 1`, `EVIDENCE_SCHEMA_VERSION`, `VerifyReport.schema_version` | [build-evidence.py](../tests/build-evidence.py) writes it; [evidence.rs](../controller/src/evidence.rs) loads it and echoes the number in verification; [artifact.py](../tests/lib/artifact.py), preflight, dossier and runner-selection fixtures read it. | Selects known inventory shape; verification independently compares hashes. **Remove** the sequence and report echo, use app producer context for standalone provenance. Keep expected bundle inventory, paths, binary hashes, entitlements and signature verification. The manifest and its parser ship together. `symbols.json` has no separate project schema number to remove. |

The four main counters have **12 generated constant/plist copies across four
files**, plus generated version prose in four documents and a generated table.
The generator has eight target files. The comparison matrix repeats the request
and response values; response/envelope goldens also remember version values.
This is a demonstrable maintenance footprint, not twelve independent boundaries.

### Build, installation, publication and test persistence

| Identifier now | Producer and demonstrated consumer | Disposition, decision that survives and effect of removal |
| --- | --- | --- |
| Registry `schema_version = 1`, `RUNNER_REGISTRY_SCHEMA_VERSION` | `RunnerRegistry`, `load_registry` and `save_registry` in `runner_manager.rs`; all runner commands; registry-recovery and selection controls. Stored under Library/Application Support or the test override. | **Remove** from new writes. Preserve existing legacy recovery reads and introduce no execution adapter. New records carry creator provenance per installation, not a registry-wide compatibility assertion: one registry can contain several releases. Inspection/cleanup uses a stable, narrowly specified ownership projection independent of executable contract. Unknown/malformed ownership fails closed. Details below are part of the decision, not deferred implementation work. |
| Build provenance `schema_version = 3`, `SCHEMA_VERSION` | [build_provenance.py](../tests/lib/build_provenance.py), `build-evidence.py` including substitution records, artifact inspector, archive ZIP reader, preflight mutation controls, fixture bundle builders; [SIGNING.md](../docs/SIGNING.md#evidence-artifacts). | **Consolidate** with producing build/source context. Keep the typed validator, record-size bound, required observations, output target, signed binary correspondence and archived ZIP binding. Source identity does not authenticate compilation or replace these checks. A current reader refuses unsupported producer context before deriving claims; archived bytes retain their original context. |
| Toolchain stamp `schema_version = 2`, `STAMP_SCHEMA_VERSION` | `build_provenance.py` writes/loads `builddir/pw-toolchain.json`; cache admission compares actual toolchain, target, configuration and scope; build-refusal controls. | **Remove** counter; retain typed required facts and comparison with current observed facts. Record producer source as provenance. Do **not** require entire source equality for cache reuse: that would discard caches on ordinary edits. Unknown/missing configuration still requires `PW_FRESH_BUILD=1`. The meaning of primitive recorded toolchain facts stays fixed; a change to those meanings requires fresh-state policy review, not automatic acceptance by shape. |
| Build session `schema_version = 3`, `SESSION_SCHEMA_VERSION` | `build_provenance.py` opens `controller/target/pw-build-session.json`, subsequent build helpers read it. | **Replace** the revision check with the existing live checkout-lock nonce plus the captured build source identity and full current session validation. Helpers of another source/lock hold refuse before cache deletion, stamp mutation or publication. A session is not reusable across builds. |
| Release `release.json` schema 1/2; portable evidence manifest schema 2/3; acceptance report schema 3 (older fixtures 2) | [release_archive.py](../tests/lib/release_archive.py), [release_runs.py](../tests/lib/release_runs.py), [release_accept.py](../tests/lib/release_accept.py), [release_publish.py](../tests/lib/release_publish.py), rotation; preflight release/publish/dispatcher controls. | **Replace** current emitted format counters with explicit producer source/release and the independently captured execution-contract identity. Keep exact archive/guide checksums, ZIP provenance, complete default-battery and ownership obligations. Missing family obligations must not become a historical fallback. Preserve only already-supported positive historical-source handling; do not expand it or rewrite archives. Unsupported producers remain inspectable as raw records and cannot authorize publication or cleanup. |
| `execution_contract.profile = "pw-family-evidence-1"` | [execution_contract.py](../tests/lib/execution_contract.py) captures catalog, catalog digest, reader digest, selected engines and required families; run, acceptance, release and portable bundle readers validate it. | **Remove** numbered profile, retaining a nonnumbered record-kind discriminator only if useful. **Retain** its existing content identity and independently captured source/catalog/selection. These enable the real decision: whether all required families and their setup/call/teardown and command ownership were accounted for. The tested app release cannot identify the test selection or test harness independently. Do not trust a run's self-declared weakened obligations. |
| `tests/RETAINED.json.schema_version = 1` | [retention.py](../tests/lib/retention.py), dispatcher, release archive and rotation writers; retention controls. | **Remove** counter; validate paths, entries, pins, source/run identity and overlaps directly. The tracked file already has source history; its release entries identify originating releases. Missing or unreadable index still blocks deletion. It is not necessary to add a new producer field to each hand-edited retention row. |
| Dispatcher `plan.json`, `owner.json`, `run.json` schema 1; acceptance `owner.json` schema 1 | [test_cli.py](../tests/lib/test_cli.py), [suite_run.py](../tests/lib/suite_run.py), `retention.py`, archive readers and dispatcher controls. | **Remove** format numbers; use run ID/path, live lock ownership, source provenance and execution-contract identity. Preserve owner-before-effects, terminal matching, exact selection/accounting and interruption distinctions. The owner/core cleanup facts have the same stable narrow meaning across producers; full semantic interpretation of an unfamiliar run remains unsupported. |
| `release-rotation` journal schema 2 | [release_rotate.py](../tests/lib/release_rotate.py) plans, validates and resumes a durable rename/delete transaction; rotation controls. | **Replace** with producer source, archive identity and transaction/ownership/inventory checks. Resume only with the same supported transaction implementation, before deletion; source mismatch preserves quarantine and directs use of the originating tooling. Release identity alone is insufficient because development tools can start a transaction. No independent transaction revision sequence is needed. Existing interrupted journals must be settled or retained with their original tooling; never silently adopt them. |
| Pytest selection/family/resource-owner/ownership records schema 1 | [pytest_engine.py](../tests/lib/pytest_engine.py), [pytest_family.py](../tests/lib/pytest_family.py), [pytest_resources.py](../tests/lib/pytest_resources.py), `execution_contract.py`, retention and dispatcher integration controls. | **Remove** counters. Preserve existing source hashes, selection digest, command operation IDs, live ownership and terminal closure. A resource-owner record used for cleanup must retain the narrow stable cleanup facts even when its full report is unsupported. The private length-framed protocol in `pytest_wire.py` has no version sequence. |
| Shell test-event/suite-report and artifact-report schema 1; drift report schema 1; control receipt schema 2; Meson receipt schema 1 | [testlib.sh](../tests/lib/testlib.sh), `artifact.py`, [drift_rules.py](../tests/lib/drift_rules.py), [receipts.py](../tests/lib/receipts.py), [meson_receipts.py](../tests/lib/meson_receipts.py); dispatcher, case checkers, native comparisons and archive retention. | **Remove** report/event counters; retain source/input snapshots, command evidence, completion and actual field/type checks. Where independently exported, carry the common harness producer context once. Control receipt input hashes and blobs already identify materialized inputs; a number is not evidence that the case ran. |
| Notarization report schema 1; release-attempt evidence schema 1; prune report schema 1 | [notarize.py](../notarize.py), [release_evidence.py](../tests/lib/release_evidence.py), `retention.py`; archive/publish receipts, operator inspection and release controls. | **Remove** counters; keep originating tool/source context, submission ID, archive hash, command receipts and state. Apple's observed status and submission ID remain authoritative facts, never inferred from the replacement identity. A report is not permission to resubmit or delete. |

Persistence alone justifies provenance and safe handling of unknown input. It
does not justify a private revision sequence. The persistent exceptions above
use actual ownership/transaction or independently captured source identities,
not an assertion that a versioned object is safe.

### Repository-local definitions and investigative artifacts

| Identifier now | Owner/readers and maintenance footprint | Disposition and surviving checks |
| --- | --- | --- |
| `docs/contract.json.schema_version = 1` | `generate_contract.py`, its mutation controls and build checks. | **Remove the manifest and generator entirely** after the common build stamp is wired through consumers. Do not replace it with a release-number manifest. |
| `docs/architecture.json` schema 4; `docs/build.json` schema 2; `docs/limits.json` schema 2; `docs/footprint.json` schema 1 | Respective `generate_*.py`, generated Markdown/DOT/SVG/spans, source-drift mutation cases and build freshness checks. | **Remove** only schema markers and their equality tests. Keep generators, closed fields, required records, unique IDs, citations, diagrams, prose copying, literal ownership, check/write separation and freshness checks. Each input and generator moves in the same checkout; its current shape can be validated directly. |
| Documentation `prose_baseline.json` and `build_baseline.json` schema 1 | `generate_build.py`, source-drift generators, [release_preflight.py](../tests/lib/release_preflight.py) comparing committed baselines with the preceding release. | **Remove** current format markers; keep reviewed entry structure and growth/refusal policy. Historical baseline content remains identified by the tag read with `git show`; do not rewrite it. Ignore the already-known legacy metadata field when comparing entry content, without accepting arbitrary unfamiliar baseline structures. |
| `tests/catalog.json.schema_version = 1`; `tests/requirements-pytest.lock.schema_version = 1` | `test_cli.catalog` validates cases, dependencies and engines; `pytest_packages.py` uses wheel pins and environment digest. These readers do not use the schema value to select behavior. | **Remove** dead markers. Keep catalog selection/equipment/dependency checks, exact third-party package versions and hashes, Python requirement and environment digest. This is the clearest case of presence without a decision. |
| Comparison matrix schema 1 and nested request/response numbers; reply/envelope goldens' revision metadata | [matrix.json](../tests/fixtures/comparison/matrix.json), Swift comparison tests, live comparison/extension cases; Rust [shape.rs](../controller/src/shape.rs), Swift [ContractVersionTests.swift](../runner/Tests/PWRunnerCoreTests/ContractVersionTests.swift), Python consumer and source-drift controls. | **Remove** local schema/revision metadata and bump classification. Keep independently reviewed scenario expectations and full field/type goldens. Current fixture requests are materialized with the candidate contract; captured historical fixtures are never retagged. A golden change still requires review, including additive changes. |
| Exec fixture report/inspection `version = 1` | [exec/helper.c](../tests/fixtures/exec/helper.c), `control.py`, `inspection.py`, lifecycle tests. | **Remove** report counter; retain nonce, PID/process-generation, complete flag, inherited resource and argv/environment observations, with fixture source provenance in the enclosing run. Standalone reports require that context. |
| Footprint observer and actor snapshot `version = 1`; native pause and held-phase/response/aftermath receipts' version/schema 1 | [footprint/observer.c](../tests/fixtures/footprint/observer.c), `actor_snapshot.swift`, associated witness/run-effects/C-worker checks and receipt validators. | **Remove** counters, keep source/fixture identity, clocks, units, intervals, memory/accounting and receipt-shape controls. Measured rows in `docs/footprint.json` remain tied to their original receipts; this work does not regenerate measured evidence or claim new measurements. |
| Worker-wait stamp page `PWW_STAMP_VERSION = 1` / reader `PAGE_VERSION = 1` | [pww_stamp_page.h](../tests/fixtures/worker_wait/pww_stamp_page.h), `stamp_worker.c`, [worker_wait_pilot_reader.py](../tests/suites/witness_contract/worker_wait_pilot_reader.py); binary page parser and pilot mutation controls. | **Replace** counter with admission of the existing fixture/source inventory before layout-dependent parsing; preserve magic, byte length, offsets, timebase and bounds. A detached page without its fixture identity is uninterpretable. Do not substitute the production worker identity: instrumentation is not fully identified by it. No need for another per-page hash sequence. |
| Worker-wait host export version 2 (reader also accepts 1); reader output `READER_VERSION = 10`; pilot/schedule version 3; build/staging/trial/power/clock/calibration/decomposition receipt versions 1 | [HostStamps.swift](../tests/fixtures/worker_wait/HostStamps.swift), `host_stamps.py`, fixture `build.sh`, `clock_pair.c`, pilot/check/reader scripts and controls. Reader v1 fallback uses a wider custody bracket; v2 requires commit stamps. Reader output already carries reader SHA-256 and fixture identity. | **Replace** all active counters with those producer/reader/fixture identities. Preserve current commit-stamp requirements and clock/order/refusal rules. Remove the active v1 interpretation fallback when switching current producers; historical exports stay with their originating reader/source and original numbers. Do not make missing commit stamps in a new export select the older interpretation. Retain source/binary build receipts; independently reject mixed instrumentation before deriving timing claims. |

Numbered suite names and fixture-directory labels such as
`runner_apply_isolation_v3`, `runner_smoke/v1`, `response25` and
`baseline_response12` are names/provenance, not active format negotiations.
Keep historical labels. The same applies to report/record text describing past
versions. Do not run a global numeric replacement over the repository.

### Identities that remain, and exclusions

| Identity | Why it remains / why another identity cannot do its job |
| --- | --- |
| Annotated release tag and release version | Users select a distributed binary/guide unit. A source hash alone does not name the published asset. It becomes the public contract label, with no SemVer compatibility inference. |
| Git commit, describe, dirty state and source snapshot | Locate the producer; distinguish two dirty trees with the same HEAD and `-dirty` describe. The current `build.version` is the nearest tag, so it cannot assert a development interface. Source identity is not a signature or behavioral proof. |
| `CFBundleVersion` commit-count build number | Retain as platform/package build metadata; it is not admitted as a public contract or evidence schema. No manual coordination is added. `CFBundleShortVersionString` remains platform metadata; its UI/documentation must not call an unreleased build that released interface. |
| Worker `PW_WORKER_ABI_IDENTITY`, Swift `abiIdentity`, Python `WORKER_IDENTITY`, emitted `abi_identity` | Exact source agreement before shared-memory interpretation and release is required within an execution. Release identity is too coarse for mixed development workers; whole-app identity does not currently occupy this fixed bootstrap location or cover standalone worker test builds. Retain [generate_worker_identity.py](../docs/generate_worker_identity.py), including its source scope and generated-copy checks. Do not create a new ABI ordinal. |
| Bootstrap and authority magic, identity bytes and compiled geometry | Magic is a format-family discriminator, not a revision promise. Keep old ordinal-era workers refusing the header. Keep C/Swift size/offset agreement and `abi_layout.txt`; a source hash cannot prove compiled layout. Authority-region identity uses the same worker identity, not another sequence. |
| Binary/content hashes, CDHash, LC_UUID, signed inventory and input/reader digests | Identify concrete bytes and associations. They distinguish re-signing, substitution, test inputs and archive contents; a release label cannot. Hash equality is not authentication or proof of compilation history. |
| Run/specimen/step/phase/actor IDs, reservation/host-instance UUIDs, nonces, PIDs plus generation facts, ownership and capture ordinals | Identify objects, connection ownership, observations and ordering within scopes. They do not identify a schema and remain unchanged. |
| `kind`, policy `format: "sbpl"`, outcome/status and role discriminators | Select record families or operations. Keep validation; removing schema counters does not collapse these distinctions. |
| Cargo package `version = "0.1.0"` | Cargo package identity, not the shipped interface: `json_contract.rs` uses build-time stamps. `build_provenance.py` consumes Cargo's `package_id` in compiler-artifact messages and retains it with the build judgment. Keep this static internal package metadata; release/source identity does not replace Cargo's package identifier. There is no separately published crate consumer demonstrated here and no reason to start synchronizing this value with releases. |
| SBPL `(version 1)`, Apple plist/XML versions, OS/SDK/deployment targets, Mach-O load-command/tool versions, Swift/C/Rust language/tool requirements, dependency/lockfile format versions, vendored Markdown parser `VERSION` | Externally owned syntax, platform constraints or dependency identities. Out of the numbering reduction. Keep their existing checks and pins. |

No independently maintained project schema/protocol **counter** in this
inventory is recommended for retention in current output. The retained exact
worker identity and test execution identity have concrete matching decisions;
ordinary content and object identities have their existing narrower meanings.
This is not a mandate to hash every object.

## Decisions for the replacement boundaries

### One intended contract; explicit producer context

Use the field `contract` for the caller's assertion, a string with exactly one
of the forms above. Expose the running build's value through `--version` and in
the build metadata, and use the identical value in reservation controls. This
is one identity repeated at independent trust/transport boundaries, not four
new values with a shared default.

Output producer context contains the common `contract`, release tag when
released, commit/describe, and source snapshot identity. Reuse the existing
`build` object for controller-family outputs. Supply an equivalent producer
context on standalone host replies and client captures. Normal nested evidence
inherits that admitted context; do not stamp every step, phase or profile.
The host's reply producer and client's capture producer are distinct observations
and must not overwrite one another. Externally installed host provenance is not
the controller's provenance.

Admission is exact equality, not ordering or ranges. A current reader first
admits producer context, then validates current structure and meaning. Missing,
malformed and foreign identities remain distinguishable diagnostics. Unsupported
payloads remain raw evidence, with no downstream semantic errors or recovered
claims. These labels are not authentication; signatures, source/binary binding,
native observations and evidence invariants continue to establish their own
facts.

### Saved specimen, including a shape-valid semantic change

A saved request for a release using this design must say
`"contract": "release:vX.Y.Z"`, with its actual release tag substituted.
A different release refuses it before runner selection, augmentation, helper
invocation or worker/validator creation. The host repeats admission on direct
XPC input before children. A missing contract is an error, not an implicit
current-release opt-in. An old `schema_version` alone cannot authorize execution;
accepting both markers as alternative authorities is forbidden. Replace the
request diagnostic's `expected_schema` with `expected_contract` and
`unsupported_schema` with `unsupported_contract`; retain `bad_request`, bounded
paths, distinct missing/type failures and the existing exit classification.
Do not preserve the old diagnostic keys as a second contract vocabulary.

To run a saved experiment on another release, its author reviews the intervening
contract account and guide and deliberately creates/edits a specimen asserting
the new contract. The tool must not rewrite the original, infer compatibility
from its shape, or offer a blanket ignore-contract switch. Reassertion is a user
decision, not a claim that the tool proved unchanged meaning.

Use a semantic-only control during implementation: two controlled producer
identities accept the same JSON shape and `file/open_write` spelling, but one
test implementation would append while the other truncates. The current
documented operation truncates and writes one byte. Submit a specimen asserting
the other producer and independently verify the file stays unchanged, with no
client/worker attempt. Also prove a deliberately current assertion reaches the
current operation and has the documented effect. This is a controlled mismatch
test, not a proposal to change `open_write` or support an old implementation.

Current repository specimens should be templates materialized with the tested
candidate's identity, after the harness independently admits that candidate.
Never take a saved user's request and automatically stamp it current. Fixed
historical JSON remains fixed; only constructed current fixtures are templated.

### App upgrade with an external runner still installed

The service plist, sealed inventory and registry execution metadata record its
producer contract/source. Install checks the incoming bundle before signing or
launchd mutation, preserving the current early protocol gate, and checks again
after re-signing before publishing an operational record. Re-signing must
preserve source and contract provenance while updating binary hashes and
entitlements.

Run/verify refuses a foreign or unknown installed contract before invocation.
The effect-free reservation exchanges the same contract and source identity;
the client independently checks the actual host before submitting. A matching
registry entry cannot excuse a mismatched live peer. There is no old-RPC
fallback. Another release's runner requires deliberate reinstall from the
matching app, even if both would have carried protocol 3 today.

Within a release, official components are bound to the release's source
snapshot; independently rebuilt components must match that source identity.
Different approved build flags, signatures and worker entitlements remain
separate provenance, not additional public contracts. Development peers require
the same development identity. Test overrides continue to identify themselves
as instrumented/unverified fixtures and cannot satisfy packaged selection.

### Recovery is deliberately narrower than execution

Maintain a small, stable meaning for the already-existing recovery facts:
installation ID, service name, scope/domain, owner UID, bundle/executable/plist
paths, plist hash, pending state, cleanup observations and observed absence.
This is an explicit narrow continuity obligation for resources PW owns, not a
general backwards-compatibility policy for results or execution.

The registry loader separates this recovery projection from execution metadata.
New writes omit the schema counter and retain each installation's creator
identity. Existing supported schema-1 records, retired kind aliases and absent
optional helper metadata remain inspectable/removable through the existing
recovery behavior. Preserve their original execution metadata, including the
old protocol number, as opaque legacy provenance; do not manufacture a release
identity from protocol 3. They are not executable under the new admission rule.
Unknown legacy schema values or invalid ownership remain opaque for reporting
and cannot authorize deletion. Do not broaden historical ownership acceptance.

List/status/reconcile expose unsupported execution identity and recovery state;
reconcile remains report-only. Removal locks the registry through launchd work,
validates ownership, retains durable cleanup on uncertainty and retires it only
after observed absence. If execution fields or equipment snapshots are
unreadable, that does not invalidate independently usable ownership fields.
Preserve unknown raw metadata on mutations; do not accidentally delete it by
round-tripping through a reduced typed struct.

Apply the same separation to managed test ownership. Source mismatch can block
interpreting a test result or resuming a transaction while still allowing safe
inspection. An unfinished rotation is stronger: finish it with its originating
tooling or leave its journal/quarantine protected. Do not add a migration of
interrupted transactions. Never unlink either checkout or registry lock.

### Retained result or extracted nested record

A complete retained result already needs producer provenance and original
bytes. New output carries the single release/development identity; current
semantic readers accept their supported identity and refuse others. Reading a
historical record means using its producing release's guide and reader/source,
or inspecting raw JSON without current semantic claims. No historical response
translation is added.

For an extracted profile, actor, comparison, equipment or validator record, the
extractor must carry the original enclosing producer context and its location
in the result (retain an enclosing-document hash when making a separate evidence
file). This can be a sidecar or enclosing export document; it does not require
a new export schema counter. Current standalone decode APIs must require that
context instead of defaulting to current. A bare nested object has insufficient
origin information and is not semantically admitted. Its nonce, hashes, PID and
record kind do not identify the contract that assigned its meaning.

A context label alone also does not prove association: preserve actor/worker,
nonce, source/parameter hash, scope, clock and observation checks. A nested
receipt transplanted under another valid producer context must fail its
applicable association checks, or remain explicitly unestablished.

### Mixed source states and development identity

Extend the existing build stamp rather than adding a release-contract manifest.
A clean checkout exactly at the intended annotated release tag may emit
`release:<tag>`. Every other build emits `development:<source-snapshot-id>`;
`base_release` may identify the nearest annotated tag for orientation only.
Plain Cargo/SwiftPM builds may report unbound development provenance, but must
not execute a public request or satisfy packaged peer checks with `unknown`.
Provide the same local build-context helper to supported source-test builds.
An out-of-checkout override cannot mint a released contract: it needs a captured
source package identity and is development unless release preflight establishes
the tagged source.

Compute the source snapshot automatically from actual source inputs at build
time, not by editing tracked constants. Use a deterministic, length-framed
path/type/mode/content inventory of the tracked checkout, plus newly discovered
build inputs under the existing source inventories; omit `.git` and build/test
outputs, which are not source inputs. Include working-tree modifications and
deleted paths, and reject symlink escapes or inputs the build consumes outside
the captured inventory (apart from separately recorded SDK/toolchain inputs).
The full commit and inventory digest identify the source state; two different
dirty contents at one HEAD must not share an identity. Generated build-context
files live under build output directories and are excluded from their own
input inventory. Current fixture/guide templates contain placeholders, avoiding
a source digest that must contain itself.

The inventory is build evidence, not another committed maintenance registry.
Capture it once under the checkout build lock, recheck before signing, and fail
if inputs changed during compilation. Emit one build context into Rust, Swift,
C helpers, app/service metadata and provenance. Build-generated copies may be
recreated automatically; this does not relax the existing rule that tracked
generator outputs are checked rather than silently repaired by the build.
Wire new build-generated sources into Meson/Cargo and native-source checks.

Require matching source/contract at independently arriving component outputs
and before execution submission. The packaged host validates its sealed
equipment and validator identity before activation; validator replies retain
producer context before verdict interpretation. The client checks its compiled
context against the controller's expected context before reservation. The
fallback compiler's returned context is admitted before using its outcome,
as its current schema gate is today. Maintain exact source/binary association
in bundle inventory so a merely edited plist is insufficient.

Do not substitute this common stamp for the worker's fixed bootstrap identity.
The worker still checks size, magic and identity before policy reads or
publications; the host checks identity before evidence decode and attempt
release. Keep no-ready/no-applied/no-done mismatch behavior, layout tests and
the limited meaning of host-selected `abi_identity`. Separate executions need
not have equal worker identities to be retained or compared under an appropriate
reader; within one execution agreement remains mandatory.

The conservative snapshot can change for documentation/test edits that leave
runtime semantics unchanged. That is an identification cost, not a new manual
bump duty or a claim of semantic incompatibility. Do not invalidate toolchain
caches merely for this change: recompilation of embedded context is separate
from cache compatibility. If the scope proves too costly, measure before
narrowing it; never narrow it by excluding an actual contract producer.

## Working guide, release guide and the account of differences

Keep [PolicyWitness.md](../docs/PolicyWitness.md) as a current-working-tree guide.
Its checked-in header says it describes development and links to current
contract definitions. Existing shared LIMITS/QUESTIONS/EXTENSIONS generation
continues. Do not freeze this guide to the last released semantics while code
changes underneath it.

Add one small authored document, `docs/UNRELEASED-CONTRACT.md` (proposed path).
It has a single baseline such as `Since v0.3.4`, and a short table:

| Surface | Difference a caller/reader must understand | Current definition and behavioral check |
| --- | --- | --- |
| Specimen intent | One asserted release/development contract replaces request numbering; old assertions refuse before effects. | Guide specimen section, request admission code and same-shape refusal control. |
| Evidence interpretation | Producer context replaces independent reply/envelope/nested counters; extraction must retain origin. | Guide output section and consumer/context controls. |
| Runner installation | Execution requires the selected release/source; recovery remains available across upgrades. | Guide BYOXPC section and recovery/reservation controls. |

These are illustrative initial rows, to be reconciled against the complete
diff since the named tag before publication; they are not a claim that this
checkout differs from v0.3.4 only in this proposed work. Record meaningful
structural **and semantic** differences, accepted-input/refusal changes, changed
defaults and evidence interpretation. Consolidate related edits into one
current account; no entry per commit, counter, capability list or compatibility
matrix. A reviewed statement of no public differences is allowed when true.
Links point to the owning definitions, not a duplicate field catalog.

Identification and explanation have separate jobs: the snapshot locates the
implementation; this account explains what a user must reconsider. A shape
golden cannot establish unchanged meaning. Review against the previous release's
guide, implementation and behavioral expectations is required even if goldens
are identical. A small preflight check verifies one resolvable annotated
baseline and valid definition links; it cannot certify semantic completeness.

At release, stage the guide with the exact tag, source identity and contract,
materializing example assertions for that release. Archive the reviewed contract
account with release notes; reset the working account to that release on the
next development change. Keep release history in tags/archives/git, not an
ever-growing change-history section of the working guide. Existing
`generate_limits.py --stage-guide` freshness checks remain and gain an explicit
build-context input for the header/examples; staging does not rewrite sources.

Bind the published guide to the final accepted ZIP's release/source identity
and checksum in `release.json`/`SHA256SUMS`. Current archive tooling already
copies the guide, checks assets and verifies ZIP provenance; add an assertion
that their identities agree, rather than relying on whichever `dist` guide
happens to exist. `make publish` continues to use the verified archive, never a
fresh working-tree guide. Documentation-only post-release corrections are made
in the working guide for the next release; do not silently replace an archived
guide under an existing released contract.

## Inspectable maintenance reduction

Remove `docs/contract.json`, `docs/generate_contract.py`, their eight-file
generation workflow, `include_str!`/compile dependencies for the manifest,
generated wire constants, plist ordinal, four repeated version sentences and
table. `tests/lib/contract.py` may remain for worker identity or move to an
appropriately named owner; it must not remain an unused four-counter registry.
Replace the smoke check's response/protocol comparisons with built
producer-context and guide/source agreement checks, preserving its separate
worker-identity and plist/build-stamp comparisons. Remove version-only Swift/Rust manifest tests
and `source_drift/contract_versions` obligations that exist solely to synchronize
numbers; retain/adapt identity and behavioral controls located in that case.
In particular, move or rename its `WorkerIdentityTests` instead of deleting them,
and remove only `contract` from `tests/lib/fixture_inputs.py`'s generator list
and the corresponding generator-contract declarations.

Delete the `NeedsBump`/`needs_bump` classification machinery in Rust and Swift,
its additive/breaking/already-bumped branches, tests of that classifier, golden
revision fields and instructions to bump before accepting a shape. Preserve
shape collection, type conflicts, full optional-field fixtures, explicit diffs
and review of a candidate golden. These goldens are also Python allowlists;
deleting them would weaken real validation. Preserve ABI geometry goldens
separately, with no version classification added.

Remove each local manifest/receipt equality test listed in the inventory while
retaining tests of fields, source associations, completeness and meaning.
Remove current fixture number churn; generated current specimens acquire the
candidate context at materialization. Keep raw historical fixtures byte-for-byte
and stop using current tests that merely demand their numbers look current.
Historical refusal controls may use unchanged historical specimens explicitly.

Update current obligations in root/controller/runner/test guidance,
`docs/CONTRACT.md`, guide, implementation READMEs, fixture/suite READMEs,
architecture/build manifests and generated accounts, SIGNING and release
tooling together. Replace bump rules with review of current semantics and the
short unreleased account. Do not leave prose claiming independent contracts
after their removal. All unrelated generators and their substantive checks stay.

New recurring work is bounded: automatic build-context generation/verification;
one human review of contract differences and current guide per meaningful
change; explicit specimen reassertion and BYOXPC reinstall for a new release;
context-preserving evidence extraction; publication checks associating the
guide/account with the release. Worker-identity regeneration and geometry
review remain existing obligations. Some source edits still require rebuilding
and rerunning affected behavioral tests. No substantial runtime or battery-time
savings are claimed: the evidence here establishes fewer independently edited
numbers, stale-copy refusals and number-only fixture/golden updates, not a
measured speedup.

Acceptance should show the deleted generator/constant/classifier paths and
remaining identity checks in the diff, count active numbering fields before
and after using this inventory, and distinguish legitimate structural/generator
failures from obsolete numbering failures. Do not introduce a permanent count
registry or benchmark just to prove the reduction.

## Bounded implementation sequence

Each stage is a reviewable change boundary. The work is not complete, and must
not be released as this design, until stage 5 removes the superseded machinery.
Do not run an acceptance battery against an intermediate hybrid and present it
as evidence for the final contract.

1. **Build context and explanation foundation.** Extend build stamp generation,
   source capture, runtime `--version`, package metadata, test-build helpers and
   staged guide binding. Add the unreleased account after reviewing differences
   from the chosen baseline. During this stage existing numbered admission
   remains authoritative; new context is provenance only. This temporary state
   must be labeled as such and must not mint a released contract. Verify clean
   tag, commits-after-tag, two dirty trees, out-of-checkout and mixed artifact
   cases before making the new identity authoritative.
2. **One atomic public-boundary cutover.** Change controller admission, closed
   Swift decoding, client controls/capture, service reservation and direct
   request admission, reply/degraded encoders, helper frames, Rust/Python
   readers, structured refusals and current fixtures together. Remove the four
   public counters and their alternatives in this change. Preserve raw transport
   and refusal ordering. New tests cannot pass by accepting either old or new
   markers. Current specimen templates and guide examples change with it.
3. **Installed and packaged components, nested evidence.** Complete common
   identity validation for signed service/equipment/validator manifests and
   re-signing, and remove nested profile/equipment/evidence counters. Couple
   execution changes with recovery projection tests in the same stage; never
   ship a loader that strands previously owned resources. Make context explicit
   at standalone reader/extraction APIs. Retain worker bootstrap identity and
   refresh it through its owning generator after source changes. Do not change
   wait/release/eligibility semantics as a side effect.
4. **Build/test/publication records and local manifests.** Remove local counters
   in grouped producer/reader changes. Preserve typed facts, cache rules, lock
   nonce, test execution identity, durable cleanup and positive historical-source
   requirements. Finish or preserve existing interrupted rotation before testing
   new journals. Switch investigative fixtures/readers together; leave old
   receipts and source references untouched. Update release packaging to emit
   only the new producer-bound records, and retain the existing bounded
   historical archive paths as read-only support, not additional current writers.
5. **Delete the obsolete machinery and accept.** Remove generator inputs/targets,
   bump classifiers and version-only tests/prose; simplify shape goldens without
   reducing coverage. Regenerate only surviving generated documents/worker
   identity. Review the full search inventory for live remnants, accidental
   alternate gates and mislabeled development builds. Build one final signed
   candidate and run the targeted checks and default battery below. Review the
   contract account and staged guide against emitted behavior. Do not publish
   as part of implementing this plan unless separately instructed.

Stages 2 and 3 share build-context infrastructure and must land together if the
intermediate app could select an installed service without the new live gate.
Stage 4 can be split by owner, but each producer and every current reader of its
record must change in the same subchange. Existing historical readers/markers
are bounded exceptions for original records, not fallback acceptance of new
documents with missing context. Final current producers emit no old counters;
no mutable map of old/new schema values, dual authority or per-surface epoch
survives.

## Verification and acceptance evidence

Use [tests/AGENTS.md](../tests/AGENTS.md) and
[CHANGE-VERIFICATION.md](../tests/CHANGE-VERIFICATION.md) for equipment,
ownership, evidence reuse and mandatory controls. Run all executions through
`tests/run.sh`, with a fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>` for each
separate evidence set. Use a signed candidate built through `make build
IDENTITY='Developer ID Application: …'`. Do not edit the inspected app; mutate
copies. An app/worker case uses the unsandboxed harness route when required,
with the same failing command retried once after an environmental refusal.
Do not claim source inspection or a passing Rust unit test as live XPC evidence.

| Proposition to establish | Representative positive and negative evidence |
| --- | --- |
| Obsolete obligations really disappeared | Search active source/generators/prose for all inventoried counters and bump instructions, classifying historical and external hits explicitly. Current records contain no obsolete markers. Change an ordinary current shape, review its golden, and show no missing-version-bump refusal. Break a required field/type and show substantive validation still fails. No old/new alternative admission path. |
| One caller assertion protects intent | Current contract executes; missing/malformed/foreign release/development contract refuses before selectors/augments/client effects. Direct XPC repeats this before children. Include old schema-only input and the same-shape append/truncate control above, with independent file observations and launch/call counts. Record a current accepted request with all ordinary/actor/optional semantics still valid. |
| Installed runner mismatch refuses early | Old registry entry and plist, actual foreign live reservation, forged matching registry with mismatched peer, and matching current peer. Verify no execution submission on mismatch, not merely an error envelope. Reservation timeout, lost grant/reply, occupied host, malformed capture and lost execution reply still never replay an invoked request. |
| Recovery survives refusal | With an old protocol entry, opaque future equipment snapshot, existing legacy kind alias and absent optional helper metadata: list/status/reconcile work, run/verify refuse, owned removal succeeds only after absence. Unknown ownership, altered plist hash, denied inspection, cleanup-retained and interrupted removal preserve durable records/staging. Verify raw unknown metadata is not lost on unrelated registry mutation. |
| Producer context gates semantic readers | Foreign outer envelope, foreign nested host reply, malformed client capture, foreign helper output and detached nested capture. Unsupported documents retain bytes and yield no claims or misleading cascaded shape errors. Valid current nested data passes; wrong nonce/worker/actor/source binding still fails. Compare helper status with admitted output; compilation is never worker progress. |
| Mixed source artifacts cannot claim agreement | Two development source states at one HEAD; stale Swift client, foreign host/worker, wrong validator, swapped sealed equipment and changed generated context. Correct context with incorrect binary hash fails independently. Worker mismatch exits before ready/applied/done; host withholds decode/release. Matching source but different permitted entitlements remains distinguishable and valid. |
| Exact memory geometry and observation rules remain | C/Swift compiled layout and source identity checks, C-worker lifecycle tests, actor equipment and ownership, validator framing/association, compiled-profile tests, native effect and disposition controls. Preserve evidence-preserving serialization failures and the distinction between declared identity and observed worker validation. |
| Persistence cannot weaken obligations | Changed build-session nonce/source refuses mutation; valid toolchain facts remain reusable across ordinary source edits, unknown/changed toolchain requires fresh mode. New release evidence missing required family contract fails; a fabricated old schema or absent producer cannot select historical handling. Corrupt ZIP/guide/source binding fails. Resume mismatch preserves rotation quarantine. Keep the existing positive historical-source archive controls without adding a broad release matrix. |
| Documentation/publication is one unit | Working guide describes current definitions; development header cannot impersonate last release. Source freshness, links/shared regions and behavior examples pass. Stage two different build identities and show a mixed guide/ZIP is refused. A semantic-only controlled change requires an account/guide review even with identical shape golden. No automated test claims to prove prose completeness. |

Required selection for the admission/reader change includes `unit`,
`failure_boundaries`, `runner_unit`, `runner_abi_layout` and
`runner_c_worker_harness` together, plus affected `integration`,
`runner_outcome_bad_request`, `runner_validator_failure`, `validator_batch_mode`,
`validator_bridge`, `blackbox_e2e` consumer controls and `witness_contract`
cases. Use `tests/run.sh --all --list` and the current catalog to select exact
members; preserve independent field/meaning controls rather than replacing
them with identity assertions.

For installation and reservation, include the applicable
`runner_byoxpc/registry_recovery` and `runner_byoxpc/reservation_controls`,
equipment/install/signing controls and their dependencies. For build/docs/test
persistence, run `source_drift`, `dispatcher`, `shell_helpers` and the applicable
`preflight` build provenance, signed-artifact, publish and rotation controls.
Changed worker-wait/footprint readers require their constructed controls and
current fixture provenance checks; repeat live measurement only if a changed
observation/measurement claim requires it. Old measured receipts are not
re-authored to satisfy a new reader.

Run `witness_contract/order_barrier_mutations` if the worker wait, release store
or query eligibility rule changes, as required by repository guidance. Keeping
those operations unchanged avoids making this redesign a scheduling change;
identity/refusal edits must still preserve their ordering assertions. After
targeted checks pass, run the final signed candidate through the default
`tests/run.sh` battery once. Fixes or unexplained failures justify reruns;
number-only fixture churn should no longer do so. Release acceptance later
uses the existing final-ZIP/default-battery route, with no added historical
compatibility matrix or second release-specific battery.

Preserve failed/interrupted evidence, resource cleanup records, original
archives and fixtures. Record candidate source identity, artifact inventory,
selected cases, actual results and limits in acceptance evidence. This planning
document does not itself supply that implementation evidence.

## Consequential choices and reconsideration triggers

The plan chooses strict per-release specimen reassertion and runner reinstall,
required context for extracted records, exact development identity, stable narrow
recovery facts, and same-producer transaction resumption. These are user-visible
tradeoffs, not details the executor should quietly change. Users will identify
one intended release/build instead of four schema/protocol numbers. Maintainers
will review meaning and evidence while ceasing to coordinate their independent
numeric revision sequences.

There is no unresolved choice needed to begin implementation. The exact tag for
the first release is a publication decision, not a new contract numbering task.
Reconsider a proposed removal only if investigation during execution establishes
one of these concrete conditions:

- A separately distributed validator, consumer, fixture producer or other tool
  actually requires admission independent of release/source identity. Identify
  its owner, distribution and the decision it makes; mere existing fields or
  tests are insufficient evidence.
- A cleanup operation needs changing the meaning of an existing ownership
  field, or cannot recover an already-supported installation with the proposed
  projection. Stop that subchange and design its explicit recovery boundary;
  do not silently make execution identity a cleanup prerequisite.
- Source capture cannot bind an actual compiled/generated input, or an
  instrumented artifact lacks usable fixture provenance. Fix capture or refuse
  that combination before removing its last guard. Do not guess agreement from
  an app tag or a page's shape.
- A currently supported historical archive path would lose safe inspection or
  integrity verification. Preserve the bounded existing path or require the
  originating tooling; do not weaken current family/ownership obligations to
  make old evidence pass, and do not convert archived bytes.
- The conservative development identity creates demonstrated maintenance costs
  larger than the counters removed. Measure those costs and review its input
  scope. Reintroducing per-surface compatibility epochs is a different proposal,
  not a routine optimization of this one.

Acceptance is complete when the final diff and evidence establish both halves:
the independent numbering obligations are gone from active production, and the
intent, provenance, refusal timing, ownership and exact component boundaries
assigned above still make their stated decisions.
