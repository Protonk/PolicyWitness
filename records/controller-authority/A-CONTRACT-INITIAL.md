# A — independent contractual authority inventory

Initial report for the controller authority plan. Investigation source: `dcc7dd0bd0634a603379ff185228abca70b5d22f`; accepted implementation/contract: `a5de0c638ff37bfa99242147fa7a8cf00a915f0d`. Dispatch HEAD is `9b579bf7`, whose additional investigation records do not redefine this subject. This report is an independent first reading, not an implementation audit, an acceptance decision, or a claim of fresh execution.

The current contract gives the controller substantial responsibility for preparing work, admitting received material, interpreting carried observations, preserving failures and publishing results. It does not give the controller direct authority to make worker effects occur or to establish their absence after lost communication. The distinction is not merely architectural preference: field meanings and failure rules repeatedly require it. The controller also originates two different requests (the example and verification specimen) and performs installation transactions that can change machine state before a successful public response exists.

## Reading method and status

The inventory below follows all nineteen authored surfaces, their subject prose and shared definitions. Stable local IDs A01–A56 group closely connected obligations without replacing the subordinate nodes. Appendix 1 records the exact controller/shared-action rule paths, local descendant paths, inherited context and claimed support. Appendix 2 lists every authored subject and its field-node inventory, including producer subjects that inform controller interpretation. Those appendices were extracted from the authored Markdown with a small in-memory reader, not from the controller-check index or the production implementation.

`who` identifies an acting component; `owner` identifies support. They are not interchangeable. Child `who` replaces the entire parent list. Inherited `when` predicates conjoin; a child's operation/recipient/report restrictions narrow its context. `uses` is a public dependency and does not transfer the referenced actor's duties. `requires` names a prerequisite, `after` orders operations, and `perform` applies an existing action to its explicit scope. A binding/selector does not by itself prove unique association. The authoring language checks relations but does not execute their conditions. Free relationships and prose remain promises, including prose around field meanings and gaps.

For each inventory row, **current promise** is a reading of the settled contract. **Prerequisites / beneficiary** identifies the information or authority the actor needs and who relies on it. **Failure / dependencies** includes downstream obligations, withholding and preservation. The separate questions table states factual uncertainty and proposed allocation; no implementation capability is credited merely because a component is named. Except where an explicit support owner is identified, support is the enclosing subject/surface owner's claim, resolved in Appendix 1 or named in the row. None of those citations was opened to inspect production or test assertions during this pass. A support grade remains the tree author's claimed grade, not newly earned evidence.

Paths in the tables are relative to `docs/contract/`: a prefix such as `request` resolves to the corresponding surface in the coverage table. A node with “descendants” includes its subordinate conditions/effects/outcomes, not unrelated sibling obligations. Canonical generated links can be formed as `docs/CONTRACT.md#contract-` followed by the node ID with dots changed to hyphens.

## Inventory: identity, originating work and preparing it

| ID | Exact authored nodes | Current promise | Prerequisites / beneficiary | Failure / dependencies |
| --- | --- | --- | --- | --- |
| A01 | `identity.public.contract`, `.forms`, `.inputs`, `.direct`; `identity.build` fields; `identity.producer.contract` | Exact identity equality admits only that identity boundary. Controller envelopes identify their own compiled context; host/capture identities remain separate. Unbound/empty expected identity cannot admit requests. Version/commit/signing facts are not substitutes for contract equality. | Embedded expected identity, arriving identity and its actual boundary; caller and every receiver. Build pipeline supplies identity, controller reports and compares it. | Refuse missing/wrong identity at its owning gate, before descendants. Different wire and worker identities have separate roles (`identity.other`). Current source identity is not proof of SDK, signing or runtime behavior. |
| A02 | `identity.version.emit` and descendants; `identity.version.contract` | First argument `--version` or `version` emits a version envelope, same identity in data/build, true/0 result and null remaining result slots; ignores trailing arguments. No specimen read or runner launch. Generation time is wall clock with pre-epoch zero. | Compiled context, clock and output capability; CLI caller. | Rendering error returns 2; successful rendering returns 0. Support explicitly separates source-only alias/trailing/error branches from the main integration check. |
| A03 | `request.specimen.emit_example`; `request.specimen.example`; `probes.step` extracted example | No-argument `example` emits one build-defined specimen plus one LF. Exit 0 promises a complete document admitted by that same build's `run`. Content/layout/labels have no cross-build stability promise. Reads no file, starts no runner, answers nothing about a caller's document. | Build's originating definition, embedded identity, preparation gate and writable/flushed stdout; caller intending a later run. | Every emission failure is exit 2; discard stdout even if complete JSON. Stderr is best-effort human explanation and cannot affect status. Host grammar admission remains `run`'s host boundary; successful emission promises no native effect. |
| A04 | `request.specimen.hold`; `dossier.collection.held`; `identity.definitions.request`; `request.specimen.duplicate_keys` | Read/parse saved file once; gate contract, resolve selectors/augments, strip controller fields, serialize selected held value once. Ordinary client and fallback use that serialization. File path is a locator, not a later input authority. | One held parsed value and selected source; caller, client, helper and dossier reader. | Later changes to the input file cannot change the held request. Listed duplicate-member observations are bounded to their tested field pairs/platform; CLI last-member and direct-host first-member behavior cannot be collapsed into one grammar. Support: `request.specimen.support`, `dossier.collection.native_gap.disposition_support`. |
| A05 | `request.specimen.contract`, `.admission`, `.nulls`, `.capacity`; `refusals.request.select`, `.consequence`, `.compound_order` | Controller identity admission precedes selector/augment interpretation. Host separately admits exact identity before closed-object decoding, capacities and complete plan meaning. Empty ordinary plans still compile/apply. | Raw request at each entry, host decoder and admitted plan; caller and report reader. | Host refusal starts no worker/validator and applies `bad_request`, rc 1, empty steps and independent safe echo. Controller must not turn its limited gate into a claim that arbitrary input satisfies host grammar. Host may already exist. |
| A06 | `request.options` fields, `.precedence`; `request.selector` fields | Validate legacy values even when shadowed; non-null nested values replace corresponding legacy values, including an empty entitlement list. Strip all five controller root keys. Parse CLI mode before file reading. Default is standard; external selection requires compatible mode. | Raw supplied selectors and CLI mode, manifest or registry target information; caller. | Wrong types/unknown nested keys/invalid mode combinations refuse before invocation. Selected-worker Boolean-true entitlements are separate from host entitlements and actor requirements. The exact selected-target capability needs B's verification; surface support is mostly selector parsing. |
| A07 | `request.options.failure_order`; `refusals.controller.consequence` and `.request_refusal`, `.tool_failure`, `.class`; `refusals.controller` fields; `refusals.projection` | Local malformed JSON/identity/selector/augment refusal is `bad_request`/1; argument/input/target-resolution error is `tool_error`/2. Argument parsing precedes input read. Retained target-resolution error outranks augmentation error. | Stage reached, available diagnostic/dossier and independently collected target/augment results; caller. | No client/result/diagnostics on pre-invocation refusal; retain dossier and structured refusal when available. Preserve full bounded code/path; oversized path is wholly withheld, not misleadingly shortened. Unknown refusal codes remain unclassified and retained. |
| A08 | `policy.augments.resolve`, `.actors`, `.augment_semantics`; `policy.spec.augments`; `dossier.augmentation` fields and `.relationships` | Validate all augment names before reads; append each named packaged fragment with LF in requested order. Replace source only after all requested reads succeed; remove augments. Actor policies visited in order, stop at first augment failure, retain visited original/selected observations. | Packaged resources and held policy object; caller and later compilers. | Invalid name/type/unavailable file has structured refusal; original saved file unchanged. Empty source accepted here; mode/applicability still belongs to host. `exec_baseline` broad file-read rule can alter experiment meaning; resolver does not promise SBPL semantics. |
| A09 | `request.overrides` fields and `.override_authority`; `actors.actor`, `actors.sandbox`, `actors.action`; `probes.query`, `.attempt`; `extensions.operation` | Host owns ordinary/actor grammar, null distinctions, capacities, references and override admission. A controller-supplied saved file is not a separate execution grammar. Accepted overrides are public request data even on packaged hosts. | Host authorization, raw form/presence and full plan; caller and native producers. | Host refusals and worker argument refusals are different reached boundaries. Controller dossier safety filtering of paths is not host admission. Actor packaged equipment checks survive fixture overrides. No new controller validation route is authorized. |

The current extracted example is an allow-default ordinary specimen labelled `example`, containing `read-hosts`: PATH `/etc/hosts`, query `file-read-data`, attempt `file/open_read`. That is the current presentation, not an immutable obligation to use this target or operation. `open_read`'s success means successful open; its one-byte read and close results are discarded. A successful round trip therefore must not silently become a guarantee of successful content reading. The emission rule is broader than its self-gate: the controller owes an originator's same-build admissibility promise even though host grammar is established later by actual submission. This is coherent as a product promise supported by cross-component checks; it does not require moving grammar admission into Rust.

## Inventory: direction, invocation and receiving evidence

| ID | Exact authored nodes | Current promise | Prerequisites / beneficiary | Failure / dependencies |
| --- | --- | --- | --- | --- |
| A10 | `identity.definitions.controller`, `.client`, `.host`, `.worker`, `.validator`; `transport.delivery.acquire`, `.invoke`, `.uncertain` | Controller invokes one client for a run. Client may retry reservation acquisition within original allowance, but invokes execution once on granting connection and never replays specimen. Host slot is not reusable after expiry/disconnect. Fresh host/worker responsibilities remain delegated to apparatus owners. | Controller launch control; client connection, reservation credential and fresh clock sample; host one-use state. Caller relies on bounded submission authority. | Invoked remains positive after later timeout/error/refusal. Lost execution reply leaves receipt/effects uncertain. A new caller retry is a new action, not recovery of an earlier result. Client/host claims are not controller-native observations. |
| A11 | `transport.delivery.deadline`; `transport.capture` clock fields; `transport.client.started_at_unix_ms`, `.ended_at_unix_ms` | Controller creates absolute continuous deadline before tool resolution/spawn, clamps nominal timeout to at least 1 ms, passes deadline unchanged. Grant does not reset it. Client expiry ignores late callbacks. | Continuous clock and actual launch boundary; run and verify callers. | Clock failure preserves prior valid readings/invocation but no invented final reading. Controller drains complete child output and waits with no independent receiver deadline; nominal client allowance is not total command-return bound. Wall-clock reversals remain raw observations. |
| A12 | `transport.authorization.connection`; `transport.delivery.admit_control`; `transport.control`, `.control_observation` | Host authorizes connection separately from identity; client admits reservation/control shape, exact identity, UUID/phase/attempt/lease associations. Controller relies on admitted client capture of those facts. | Host Security observations/configuration, client live callback context; cooperating components and caller. | Refused control retains count/hash but no decoded peer fields. Host PID/instance remain peer assertions; no kernel-generation identity is promised. Opaque reservation credential is omitted from public capture. |
| A13 | `transport.client` fields; `transport.request_delivery`; `transport.rejected`; `wire.frame.budgets`, `.projection` | Controller records chosen argv, child timing/status, write counts, capture counts/truncation, retained stderr and exact rejected stdout prefix. Accepted capture retains exact host bytes separately. Binary bytes project as base64; diagnostic text has its own lossy conversion. | Owned child process/output and joined stdin writer; caller and reader. | Successful writes establish bytes accepted by stdin pipe only. Complete collection precedes prefix cap and can consume more memory than cap. Missing child numeric status maps to recorded fallback 1. Retention loss remains explicit. |
| A14 | `transport.client.admit` and descendants; `wire.frame.admit`; `envelope.data.admit`; `diagnostics.execution.admit` | Order: request delivery failure; retention/missing/client producer/schema/semantics; host completeness/schema/producer; decoded response geometry/profile context; only then execution interpretation. | Received bytes plus expected identity, complete retention and semantic capture relationships; caller. | Delivery failure is tool_error/2, submission unknown and no decoding diagnostics. Retention loss/missing similarly skip decoding with their own classes. Unsupported/malformed capture supplies no host/submission authority. Retain bytes at actual receiver. |
| A15 | `wire.frame.admit`, `.identity`, `.projection`; `transport.retained_reply.truncated.arithmetic`, `transport.retained_reply.data_base64.extent`; `identity.other.wire` | Exact extent/magic/fingerprint/root/producer before descendants. Reject bad typed tags/ordering/counts/ranges/text/trailing bytes. Rust and retained-byte reader share a structural obligation, not necessarily one implementation. | Complete frame and requested root; controller and independent reader. | Short fingerprint malformed; other full fingerprint unsupported. Truncation prevents prefix interpretation. Successful structural decode only establishes declared shape; semantic checks follow. Byte length and encoded character length are distinct. |
| A16 | `diagnostics.execution.geometry` and all conditions/effects | Bound decoded action/phase/actor/transfer/resource/equipment/authority/validator and lifecycle-reference collections before joins. Applies to every decoded reply including preparation/degradation, run and verify. | Typed record and owned limits, before potentially expensive associations; caller. | `malformed_runner_response`, false/1, retain decoded reply; run diagnostics null; verify outcome refusal and PID null. Child entry narrowing determines command-specific effect. Conditions are a complete family, not only counts on normal successful replies. |
| A17 | `profile.receipt.labels` and descendants; `profile.receipt.reason`, `.request_nonce`, `.host` | Controller checks every present receipt's closed status and producer/stage labels after identity/geometry, including actors and degraded/preparation records. Captured means worker/before_apply; unavailable has no such labels. | Carried receipt and admitted containing producer; caller. | Refuse containing reply as malformed, preserve decoded report, withhold run diagnostics or verify PID. Controller check does not revalidate nonce/digests/bytecode/native capture; host's `.host` production check owns those. Request nonce comparison requires independently retained request operand. |
| A18 | `policy.fallback.classify`, `.fallback` fields; `policy.actor_check`; `policy.helper_request`, `.helper_policy`, `.compile`, `.imports.holds` | Eligible only after accepted client capture, no delivery error, terminal xpc_error. Ordinary helper receives held serialization; policy-bearing actors get separate held policy-only requests in order, even before host mode validity was known. | Admitted client terminal, held selected input and helper availability; caller diagnosing compilation. | Launch/delivery failure unavailable; then capture loss, parse failure, absent output, raw identity/kind validation. Supported nonempty helper outcome copied exactly; retained unsupported parsed envelope has no semantic authority. Helper result establishes independent compilation, never worker progress or cause of lost reply. |
| A19 | `refusals.later.boundaries`; `reply.failure.publish` and descendants; `reply.failure.evidence_retained` | Preserve native/transport/reporting failure scope: client timeout differs from delivered host timeout. Host validates/encodes, tries rich fallback preserving observations/removing comparisons, then minimal scalar context/empty arrays, finally empty bytes. | Host writer and available observations; controller as receiver and public reader. | Controller must admit/degrade according to actual form, not recover ordinary semantics from rejected/raw bytes. Rich retained associations may be inconsistent; minimal means evidence lost, not effect absent. Host fallback is a producer duty, not permission for controller fabrication. |

## Inventory: interpretation, preservation and public result

| ID | Exact authored nodes | Current promise | Prerequisites / beneficiary | Failure / dependencies |
| --- | --- | --- | --- | --- |
| A20 | `identity.definitions.observation`, `.effect`, `.cause`, `.assessment`, `.unknown`, `.absent`, `.null_value`; `steps.assessment.meaning`, `.observe`, `.relations` | Preserve distinction among observation, supported effect, cause and interpretation. A permission-shaped failure does not establish sandbox cause; query/attempt relation is not prediction-versus-enforcement agreement. Missing publication leaves operation result unresolved. | Named native/carried observations, scope/time and admitted field meaning; every report reader. | No causal strengthening from rc 0, exit success, matching strings, absent observation or completed-looking public output. These are shared interpretive constraints, not all express controller checks. |
| A21 | `diagnostics.execution.project`, `.ordinary.lifecycle_check`; `diagnostics.actor.projection.lifecycle_check`; `lifecycle.disposition`, `.claim`, `.issue`, `.step_questions`, `.attempt` | Validate each worker's native support, claim states/bases/references, ownership/reap, progress/slots, action mapping and lifecycle copies under its reporting form before projecting. Actor workers are separate scopes. | Admitted subprocess, its assigned plan/actions and reporting form; caller needing worker conclusions. | Local findings withhold that worker's disposition, set unknown cause/invalid integrity/null stop. Supported host conflicts can pass integrity; contradictory observations and malformed claims are different. No subprocess means no_worker projection, not proof no process/effect existed. |
| A22 | `diagnostics.execution.ordinary.mapping` and outcomes; `diagnostics.actor.projection.mapping` and outcomes; `diagnostics.execution.vocabulary` | Ordered mapping: supported zero exit → clean_exit; other exit → nonzero_exit; signal → signaled; supported conflict → conflicting; unresolved/inapplicable → unconfirmed; otherwise admitted unfamiliar ending → unrecognized. | Lifecycle validation prerequisite and final-status claim; ordinary/actor reader. | Unknown closed state is invalid and withholds. Open answers/summaries retain unknown spelling with checks on known meanings. Null observations, absence and unrecognized are not success. Gap `.vocabulary_choice` reserves the merged unconfirmed vocabulary decision. |
| A23 | `diagnostics.execution.ordinary.cause_chain.facts`, `.cause`; `diagnostics.actor.projection.cause_chain.facts`, `.cause` | Named host cleanup cause requires validated signal ending, supported cleanup trigger, exhausted grace and successful recorded matching signal request. Recognized triggers map to sentinel deadline, exhausted grace, wait error, transfer error/timeout cause names. | Independently carried request/grace/ending observations plus valid references; caller. | Unknown/unrecognized chain remains unknown. A kill request alone or signal alone cannot supply attribution. Support claims some cause alternatives only source-read. |
| A24 | `diagnostics.execution.ordinary.stop`, `.host_conflicts`; `diagnostics.actor.projection.stop`, `.host_conflicts`; `diagnostics.execution.actor_rows` | Copy only recognized supported stop reason, mark valid after local validation, then copy each validated host conflict with its fields and order. Actor diagnostics exactly cover retained actor positions and copy labels, including duplicates/no subprocess. | Positional actor association, validated local facts; caller. | Missing/unrecognized stop null. Copied conflicts omit subject_path. Duplicate actor labels remain separate rows and are judged separately by reply-wide checks. Actor aggregate valid/invalid/null uses actual worker projections. |
| A25 | `diagnostics.execution.families`, `.reply_checks`; `steps.assessment.order` and descendants; `lifecycle.validator.associate`, `.cardinality`; `actor_evidence.phase` | On ordinary semantic replies check phase IDs/order/action partition, collection/validator ownership, complete native-query association, ordering chain and comparison vocabulary. Query-first requires eligible native answer plus closed collection, release/ack, setup and worker lifetime; another query's failure does not erase an eligible one. | Complete related carried records; controller observes consistency, host produces actual ordering. | Reply-wide finding withholds aggregate, preserves raw reply/actor assessments. Duplicate/null/unexpected validator records stay collection-scoped; no guessed per-step joins. Ordering is before batch, not before every in-batch state change. |
| A26 | `diagnostics.execution.families`; `lifecycle.policy_read`; `steps.assessment.fresh_read_aggregate`, `.fresh_write_aggregate`; `steps.fresh_read`, `.fresh_write`; `lifecycle.exec` through `.exec_wait` | Check carried policy receipt counts/host expectations and later observations; check applicable fresh I/O and exec relationships. Completed publication gates payload. Preserve first failed native operation, short-write semantics, spawn versus child result, collection versus cleanup versus reap. | Ordinary semantic reply and operation-specific observations; caller. | Failed native consistency is reply-wide finding, not repair of native values. Missing receipt leaves delivery unknown. Descriptor metadata and returned bytes support specific effects; old open_read/open_write and sysctl discard some observations by design. |
| A27 | `diagnostics.execution.families`; `actor_evidence.actor.account`, `.reader_scope`; `.application.classify`, `.authority_association`, `.late_application`; `equipment.preparation_failure.retain` | Check ordinary actor identity/order/visits/PID/phase/event/transfer relationships, application precedence and setup distinctions. Preparation refusal retains declarations/inspection, zero apps and empty execution tables. Late applied publication can coexist with setup_timeout without activation eligibility. | Actor declarations carried in reply, associated worker/setup/authority evidence; caller. | Malformed associations are reply-wide findings. Reporting-failure form bypasses ordinary actor association checks; worker local validation remains separate. A body retained after failure has not become ordinary evidence again. |
| A28 | `actor_evidence.gate.check` and descendants; `.gate.evaluate`, `.prepared_association`; `.owned_endings.sequence`; `diagnostics.issue.subject_path` | Controller checks carried termination gate joins and all source/dependent prerequisites, owned PID/status, timing, ordinals and eligibility; accumulates findings. Positive source-ending chain uses source actor sequence; dependent activation time is cross-process relation. | Source final phase/actor, owned reap and dependent setup/equipment; caller. | Finding names inspected gate by positional subject_path, retains gate/native/actor conclusions, withholds aggregate. Unreached gate lacks wait/reap-reference/ordinal; evaluated failure cancels all later scheduling at host. Later cleanup reap does not retrospectively satisfy timeout. |
| A29 | `diagnostics.execution.families`; `equipment.binding.bind`, `.bound_values`; `.execution.inspect`, `.eligibility`; `.authority_scope.acquire`; `.cleanup_reference` | Check actor equipment/authority carried relationships at their stated scopes. Static binding, live matching and activation eligibility are separate. Cleanup cells have independent publication and unresolved names retain recovery identity. | Host-carried inventory, binding indices, entitlement readbacks/live observations, authority cells and lifecycle; caller. | Controller can check relations, not reproduce live Security inspection or prove erasure from absence. Fixture overrides remain unverified_fixture. Missing primary/invalid cell facts remain visible. No automatic controller cleanup authority over retained native shm names follows from their publication. |
| A30 | `diagnostics.execution.families`; `extensions.event`, `.transfer.delivered_receipt`, `.source_association`, `.resources`, `.token`, `.delivery`, `.handle` | Check ordinary actor custody/resource relationships without exposing token bytes: issue, custody acceptance, copy/equality, recipient acknowledgement and source acknowledgement remain distinct. Resource declaration does not establish production. | Associated event/transfer/resource tables and native publication status; caller. | Incomplete action remains unresolved unless boundary evidence establishes not_reached. Native release result is not proof of later access denial; equal raw handles are not equal declaration identity. Degraded records preserve inconsistent associations without ordinary validation certification. |
| A31 | `diagnostics.execution.reply_checks`; `diagnostics.issue.retain`, `.subject`, `.subject.withholding_scope`; `reply.failure.publish.associations` | Reply-wide findings follow worker projections, append in check order, withhold aggregate disposition/cause/integrity, preserve actor projections, ordinary derived stop reason and host fields including comparisons/gates. Worker-local findings affect only worker projection. | Failed check and its exact scope, retained reply; reader. | Retained assertion is not endorsed merely because present. Only gate/reap/activation findings carry positional subject_path; copied host conflicts retain their own metadata. Broader actor withholding and degraded association requirements remain explicit maintainer decisions. |
| A32 | `diagnostics.execution.families`, `.reader_evidence`; `reply.failure.publish`; `actor_evidence.actor.reader_scope` | Reporting-failure path checks degraded outcome/rc/error, marker/original summary, absent comparisons and retention form, with profile context and geometry still applicable. Lifecycle reader still judges retained workers. | Admitted typed fallback and explicit evidence_retained; caller and independent consumers. | Passing degradation-form check does not validate ordinary actor/phase joins or cure worker conflict. Retained original outcome is diagnostic context and must not drive ordinary success mapping. |
| A33 | `envelope.data.select` and outcomes; `envelope.result` fields; `diagnostics.execution.outer_result` | After successful admission copy host outcome. Exactly finished sets ok true/exit 0, every other admitted outcome false/1. Compute diagnostics independently. Error precedence: host, capture, parse, generic; top rc/errno/stdout/stderr stay null. | Admitted host outcome and command-specific evidence; CLI caller. | Finished can coexist with failed attempt and controller integrity finding. Success/findings product question is explicitly open, not a current refusal rule. Actual process exit is separate observation from reported exit_code. |
| A34 | `envelope.run`, `.data` fields, `.classification`, `.admit`; `identity.definitions.envelope`; `request.specimen.emit_example`; `identity.version.emit` | Publish outer operation kind/build/time/result/data with correct optional/null meanings. Dossier always accompanies run; runner_result may remain decoded but unadmitted after later gate; diagnostics null for early refusal. Bare example has separate publication protocol. | Serialization/output capability, held records and admission decisions; CLI caller and artifact consumers. | Contract explicitly states example write/flush failure and version rendering-error exit. It does not supply an equally explicit general run/runner-command interrupted-output/flush contract. An effect without usable envelope must remain uncertain; there is no general durable run journal promise here. See Q4. |
| A35 | `identity.definitions.assessment`; `wire.frame.reader`, `.admit`; `envelope.data.select`; `diagnostics.execution.reader_evidence.classifier_generation` | Controller reply assessment and outer-envelope construction are distinct. Independent retained-byte/canonical consumer has its own judgments; common typed schema does not establish semantic independence or native production. | Independent input/oracle and explicit admission applicability; developer/reader. | A controller's clean assessment cannot certify its subsequently assembled outer result. Shared-consumer result consistency is required by the settled plan; present surface mapping defines the relationship, but production realization/reachability stays unverified here. No fourth interpreter is proposed. |

## Inventory: dossier and machine administration

| ID | Exact authored nodes | Current promise | Prerequisites / beneficiary | Failure / dependencies |
| --- | --- | --- | --- | --- |
| A36 | `dossier` opening prose; `.specimen`, `.actor`, `.policy`; `policy.imports.holds`; `dossier.collection.held` | Retain selected-source policy hashes, original/augmented distinctions, actor-order partial dossiers and pre-invocation selection/provenance on every run envelope, including failure. | Held source strings and reached preparation stage; caller. | Hash observes decoded UTF-8 source, not original JSON bytes. Malformed/missing policy or unapplied actor is not-applicable. Later file mutation cannot rebind held source; separate imports can change. |
| A37 | `dossier.collection.scan`; `.imports.scope`; `.imports`, `.import_record`; `policy.imports.native_import_agreement` | Literal import walk, absolute unchanged or two-directory relative lookup, descriptor-held regular-file hash/scan, canonical/unresolved dedup, sorted records, depth 8/count 64 and closure framing. Preserve cycles/errors/nonliteral/bounds. | Selected string within helper source bound, filesystem reads; caller. | Complete/incomplete have closure; failed/not-applicable no scan records/closure. Closure can identify partial material and never proves native compiler import parity. Source count, file size metadata and actual hashed bytes have separate meaning. |
| A38 | `dossier.collection.compare`; `.binary.classify`; `.binary`, `.binaries`; `.app`, `.verification`, `.mismatch` | Null shipped-role record uses unique manifest description without rehash; other selected files attempt actual hash against valid unique typed baseline. Match/mismatch/unavailable classify independent available digests. Optional manifest verification only when env exactly 1. | Manifest, selected safe path and file-read result; caller. | Dossier-only failure/mismatch does not stop invocation. Failed baseline does not erase actual digest. Reject unsafe override echo/read; selected-file equality at one time is not executing-image association. Verification failures retain expected/actual/error per entry. |
| A39 | `dossier.host`; `.runner` and fields; `installation.signature`, `.entitlements` | Host sysctl failures stay null; runner provenance reports intended service/path and recorded per-role signing/entitlements. Granted keys are exactly Boolean true, not truthy values. | OS reads, manifest/registry/readback; caller. | Unavailable metadata remains unavailable, not no-entitlement/no-worker assertion. Selection metadata and live actor association are different authorities. Root/controller README supplies more selection detail than explicit rule nodes; review that seam before claiming complete selection contract. |
| A40 | `installation.commands.read`; `.registry`, `.runner`, `.pending_cleanup` | Registry path override/default, schema 1, absence → empty; id precedence without fallback after unmatched id. List/status/verify/remove/reconcile find appropriate active/recovery collections; unknown metadata survives opaque. Historical state/kind/defaults retain documented semantics. | Readable registry and command selector; operator. | Malformed known fields/unsupported schema refuse loading. Miss uses operation kind, not_found/false/2. Read-only readers may see complete prior/replacement registry, never require modifier lock. Opaque metadata supplies no ownership. |
| A41 | `installation.commands.publish` | Modifier holds stable sibling advisory lock across mutation and launchd actions; proposed registry must round-trip without loss, write/sync mode-0600 same-directory temp then atomic rename. | Lock ownership, filesystem publication capability and complete retained metadata; all operators. | Busy/unavailable lock or lossy readback refuses. Never replace lock inode to bypass owner. Atomic registry publication does not make launchd/plist changes atomic or roll back signing. |
| A42 | `installation.commands.install`; `.runner`; `equipment.manifest` | Canonical existing XPC bundle, exact contract, bundle-derived service/executable, source seal/inventory and conflict checks across active/recovery records before optional signing. Required helpers, role-specific signing, refreshed inventory, final recursive signature verification and reread precede install. | Caller-authorized bundle, signing privilege/identity/entitlements, current build and registry; operator/launchd. | Reject supplied alternate bundle-id/executable, incompatible kind/service, existing target plist, conflicts and missing helpers. Ad-hoc requires explicit allowance. Signing can mutate bundle before durable pending save; no success response is necessary for that effect to have occurred. |
| A43 | `installation.commands.pending`; `.install.state_copy`; `.install` fields; `.ownership` | Save pending ownership with plist path/domain/UID/hash before plist creation/bootstrap; installed only after requested actions and final registry save. User GUI/system privilege are real prerequisites. skip-bootstrap only changes requested operations. | Verified bundle/readbacks, prepared plist and locked registry; operator and future recovery. | Retain pending after later failure. Installed, bootstrapped and observed loaded answer different questions. No loaded inference from transaction state, no absence inference from failed public response. |
| A44 | `installation.commands.verify`, `.pending_verify`; `.verify.delivery_failure`, `.select`; `.verify` fields | Fixed allow-all apply-only request, current contract, fresh invocation; apply ordinary admission and copy PID/outcome only after admission. Pending explicit verification permitted and registry unchanged. Default 5000 ms/floor 1. | Selected external record/kind/contract, held internal request and apparatus; operator. | Delivery error tool_error/2 takes precedence; otherwise finished true/0 and others false/1. Refusal/unavailable reply gives no PID; decoded refused reply/capture retained. Empty-plan completion establishes apply-only verification, no per-operation observations; it is not the example command. |
| A45 | `installation.commands.validate`, `.entitlement_errors`; `.validate`, `.failure` | Visit every runner under lock, refresh available per-role metadata, verify bundle/inventory, save and report updated/missing/invalid plus per-binary failures. Missing host skips later checks for row. | Registry and signing/readback tools; operator. | Completed command succeeds even with missing/invalid counts. Entitlement metadata errors do not automatically imply invalid signature; applicable equipment checks separate. Pending cleanup remains recovery. |
| A46 | `installation.commands.reconcile`; `.reconcile`, `.reconcile_record`, `.candidate`, `.inspection_error` | Report independent current service/plist observations and ownership for recorded active/cleanup rows, candidates and inspection errors. Scan candidates by documented recognizable names/paths. No mutation. | Readable registry/directories/launchctl; operator planning action. | Unknown inspections retained, location-error row preserves unknown form. Candidate/prefix is not removal authority. Command success can coexist with unknown individual facts. |
| A47 | `installation.commands.ownership`; `.service.classify`; `.service`, `.plist`, `.ownership` | Validate location/domain/user/path, no traversal/symlinked plist ancestry and correct executable parent. Plist ownership requires complete content relation, additionally recorded UID/hash. Service ownership separately requires observed matching executable. | Durable selected record and fresh independent observations; operator and other installations. | Unknown/ambiguous/unowned is not permission to act. Absent presence has ambiguous ownership but still proves absence at observation. Legacy conventional/content checks differ from recorded full-parent checks; a permitted parent need not be conventional beyond rules. |
| A48 | `installation.commands.remove`; `.pending_cleanup`, `.cleanup_observation`, `.cleanup_wait` | Publish active→pending_cleanup before actions; boot out only owned service unless skipped, unlink only owned plist after immediate recheck. After bootout poll retained presence 50 ms to nominal 1000 ms, stop on absence/unknown; final observations separate. | Lock, durable ownership, current resource identity, launchd/file authority; operator and future recovery. | Failed/refused/uncertain action, changed object or failed retirement publication retains recovery/warnings. Remove can exit 0 with cleanup_retained true. No global rollback or total-time guarantee. Repeated remove resumes durable record after output/plist loss. |
| A49 | `installation.cleanup.retention`; `.cleanup` fields; `installation.commands.recovery` | Retire only observed service+plist absence, no warnings and successful publication. True cleanup_retained iff retained_record present; nonempty warnings imply retention. Action booleans record this invocation's successful calls, not final resource absence. | After observations and durable save; operator and subsequent cleanup. | Unknown final launchctl result after successful actions still retains cleanup. Keep recovery authority until absence established. Public output loss cannot erase durable pending record. Controller native-resource cleanup beyond registry scope has no implied authorization. |
| A50 | `installation.dynamic_support`; `.reconcile_record` optional fields, `.candidate`, `.cleanup_observation` | Conditional JSON fields, nulls, opaque cleanup history and nested historical conversion preserve their explicit forms. Location error and normal observation rows are alternatives, not a union of all required keys. | Correct command-specific projection and declaration reader; machine consumers. | Lossless metadata and observational scope must survive serialization; shape import alone supplies no behavior evidence. Dedicated mutation control for every dynamic branch is explicitly not claimed by support. |

## Cross-cutting obligations recovered outside the controller-check index

| ID | Exact authored nodes / source | Current promise | Prerequisites / beneficiary | Failure / dependencies |
| --- | --- | --- | --- | --- |
| A51 | `identity.definitions.policywitness`; `.host`, `.worker`; `actors.actor.fresh`; `actors.phase.order` | System uses fresh sandboxed workers, one per actor; host retains orchestration/reply path; eligible collection closes before release. Controller's direction must preserve these producers' duties. | Cooperating client/host/worker/validator lifetimes and ownership; specimen caller. | Controller cannot establish fresh worker merely from host PID or success. No host sandbox application, no reusable sandboxed process and no controller-side substitute native observations. These are system guarantees with specific owners, not demands to move execution into controller. |
| A52 | `identity.definitions.bytes`, `.absent`, `.null_value`, `.optional`, `.unknown`; `wire.frame.projection`; `transport.transport_value`; `refusals.projection`; record import model | Public serialization preserves byte-source and field-presence semantics across typed variants. Required key/null, optional absent, conditional null and same_as_input omissions differ. Input optional storage does not define admission. | Correct typed import and actual boundary, caller's meaningful expectations; all readers. | No coercion of Bool to integer, absent to successful value, rejected bytes to admitted alternative, or union alternatives into unconditional fields. `record_definitions.py` joins declarations/shapes but does not establish effect, acceptance or ownership. |
| A53 | `reply.record.pid`; `lifecycle.worker.pid`; `transport.capture.client_pid`, `.control.host_pid`; `profile.receipt.worker_pid`; `installation.verify.runner_pid` | PID meanings remain boundary-specific: host-report pid can be host or worker; worker subprocess pid is worker identity; client/control IDs are their own assertions; verify copies admitted report pid under that meaning. | Actual named record and admission; caller. | Never substitute host/client PID for missing worker evidence. Numeric PID alone supplies no generation, current ownership or cleanup authority. |
| A54 | `policy.spec.compile_classification`; `.check_data`, `.compile`; `reply.record.outcomes`; `steps.assessment.observe` | Different successful operations retain different meanings: helper profile+no-diagnostic, worker nonnull profile, host finished, successful spawn, fresh I/O and old open-only success. | Specific producer's native return and completed publication; caller. | No cross-boundary “success” normalization that erases diagnostics, child status, missing publication or independent reads. Simultaneous worker profile/diagnostic native occurrence remains unobserved in support. |
| A55 | `diagnostics.execution.reader_evidence`; `.classifier_generation`; `actor_evidence.actor.reader_scope`; `wire.frame.reader` | Host self-check, controller admission/projection and independent consumer are separate interpretive duties. Their applicable forms may legitimately differ. | Exact supplied record/admission boundary and independently expected meanings; project reviewers. | Neither agreement among readers nor a successful structural generator check proves native production or correct product allocation. Independent semantic classifier generation remains an open choice; this report does not recommend conflating them. |
| A56 | `request.specimen.emit_example.support`, `.example.support`; `identity.surfaces.stamp`; all support owner grades | Evidence credit is scoped to named assertion/context/run; examples and public gaps remain public meanings while support stays editorial. Exact callback-byte comparison and signed pipe-length observation establish different things. | Applicable retained artifacts/source identities; users/reviewers evaluating support. | Pruned historic CLI raw runs are accepted prerequisite history only. No current native execution, release credit, file-read nonoccurrence observation or broad same-platform guarantee is newly established by this report. |

## Questions, competing readings and allocation proposals

Inventory completion precedes these proposals. “Retain” below is provisional advice grounded in required information, not a maintainer decision or an assertion that code fulfills the promise.

| Question | Current promise / counterevidence | Unverified factual question | Proposed allocation / what would change the view |
| --- | --- | --- | --- |
| Q1 — originating versus admitting (A03–A05) | Emission promises same-build run admission; extraction/self-gate explicitly does not establish deep host grammar. This is not inherently inconsistent: originator can owe a product property verified by the downstream owner. | Do final emitter/preparation/host routes and independent cases establish this exact same-build property on every supported branch? No new raw execution supplied. | Retain controller originator/publication duty and host grammar owner. Reject a proposed controller grammar transfer justified only by emission ownership. A concrete emitted-but-host-refused specimen would require correction of originator or downstream promise, not a new public dry-run API. |
| Q2 — outcome success versus integrity (A31–A35) | Exact finished→true/0 currently survives integrity findings. Open gap is explicit; ordinary failed attempts are intentionally not command failure. | Which integrity findings can accompany real finished replies, and which are only constructed receiver inputs? | Preserve current mapping pending explicit maintainer choice. If changed, distinguish experiment completion, unusable aggregate assessment and failed individual action. Do not silently classify all findings or failed attempts as execution failure. |
| Q3 — scope of withholding/degradation (A27–A32) | Aggregate withheld can coexist with clean actor ending and retained invalid associations. Degraded branch deliberately bypasses ordinary actor/phase checks. | Can actor assignment information used for an apparently valid local conclusion depend on a reply-wide association that failed? Can a clean local ending be correctly associated without that failed information? | Require B/C to trace dependencies before recommending broader/narrower withholding. Retain records whatever inference policy is chosen. A local ending independent of broken transfer association is counterevidence to blanket withholding; a duplicated/misattributed worker association may support narrower dependency-sensitive limits. Any scope change needs maintainer judgment. |
| Q4 — publication after effects (A34, A42–A49) | Example has explicit write+flush/discard rule. Version gives rendering-error exit. General run envelope and runner commands lack equally specific public interrupted-output and flush semantics. Durable registry recovery exists; durable execution reporting is not promised. | Which actual writers flush, which errors reach process exit, and what can survive controller interruption after effects but before envelope publication? | First document existing behavior and retained uncertainty. Consider a narrow publication clause only after concrete writer review; it is a new/clarified public guarantee requiring adjudication. Do not infer retry safety from failed output. No durable per-run journal or universal rollback is proposed. |
| Q5 — controller's available inputs (A17, A25–A30) | Receipt labels intentionally do not compare nonce. Several host production relationships mention request operands while controller descriptions say carried reply/native relations. | Does each claimed controller check have the original/normalized request, or only echo/plan in reply? Can original-request order/membership/nonce be checked independently on its actual path? | Assign original-request comparisons only where the operand really exists. Preserve distinction between internal report consistency and request association. A host's correct production obligation does not automatically become receiver verification. |
| Q6 — ownership versus observations (A10–A19, A47–A49) | Client invoked can be known while execution unknown. Removal owns only independently identified resources; unknown absence cannot retire. | Are helper/capture-loss and final registry-save failures preserving exactly the authority/uncertainty promised, through actual public entry? | Retain controller admission/durable recovery and client once-only submission at current information holders. A transfer requires effective control and an observation back to controller. No host PID, label prefix or past path read should manufacture current authority. |
| Q7 — shared `who` (A11, A15, A18, A44, A51) | Shared actors are explicit but prose distributes tasks: controller deadline creation/client enforcement; controller invocation/client reservation; byte reader obligations for both readers. Child replacement is not additive. | Are all duties exercised at actual named owners, especially verify and fallback failure paths? | Prefer explanatory split of responsibility first. Change authored actors only if real responsibility is wrong or ambiguous enough to affect public meaning; require maintainer decision. Shared duties alone are not evidence for a framework/refactor. |
| Q8 — semantic predicate specificity (A21–A30) | `diagnostics.execution.families` describes substantial checks in prose. Local lifecycle condition partly says the implementation's validation returns no findings; this is operationally circular if read without field meanings/native support. | Does current predicate implementation check all stated relations, and are independent negative controls sensitive? | Recover explicit semantic requirements from lifecycle/native/actor surfaces, as inventory does. Do not let “validation passed” become the sole public definition. Before restructuring DSL, test concrete missing distinctions; existing forms may suffice. |
| Q9 — outer result's independent consumer (A35, A55) | Producer result mapping is explicit; selected plan requires consumer applicability independent of the result fields. A clean reply assessment precedes envelope assembly. | Do readers select applicability from admitted transport/reply even with unrelated record faults, and refuse unsupported retained bytes as mapping source? | Retain independent reader/oracle. Check missing/null/type faults and combined faults without adding a fourth interpreter. Correct reader applicability is not a reason to move production outcome selection out of controller. |
| Q10 — selection/dossier/equipment (A06, A29, A38–A39) | Selected-worker requirement is field prose; per-actor static/live checks are host duties. Dossier hashes deliberately non-gating. Registry values describe past reads. | Are some guide/README promises about external kind, pending state, manifest resolution or requirement checks under-specified in authored selection rules? Does actual path rely only on stale registry readback by design? | Keep selector/registry admission with controller and live actor inspection with host. Clarify normative gaps only after B's path reconstruction. Do not turn all dossier mismatch into refusal or all selected-file equality into process identity. |
| Q11 — retained mutable environment (A37, A42–A49) | Separate import reads can differ; signing precedes pending publication; registry atomicity does not encompass machine actions; cleanup ownership checks are observations. | Which intervals retain identity versus merely a path? Could final output promise exceed the held resource/observation? | Describe those intervals, not a fictitious atomic transaction. Existing conservative recovery may already be correct. A source/read change requires actual independent discrimination before broad refactoring. |
| Q12 — inherited vocabulary (A22, A52, A54) | Unresolved/inapplicable merge into unconfirmed is explicitly open; unknown open strings remain, closed states fail. Different operations define success differently. | Do consumers accidentally enforce a closed vocabulary where contract is open, or reinterpret omitted/null values as absence? | Retain operation-specific meanings. Any merged/split vocabulary change needs maintainer judgment and coordinated readers. Unknown behavior is not a mandate to refuse every unfamiliar string. |

No experiment is requested during this first reading: these are source/cross-examination questions, not claims whose answer requires generating another live CLI evaluation. If a later experiment is needed, the smallest useful candidates are a lost-invocation capture with independent effect/count, or an association fault that isolates whether a retained actor projection actually depends on that join. Those must be coordinator-owned and distinguish constructed interpretation from native production.

## Completeness and exposure limits

All nineteen surfaces were enumerated, including those with no literal controller actor. I recovered obligations in component definitions, field prose, shared references, ordered conditions/effects, sibling subjects, examples, open-vocabulary rules and public gaps. Appendix 1 separately enumerates rules with effective controller membership; it is a cross-check, not the inventory outline. Appendix 2 prevents the fields and producer-only surfaces from disappearing simply because their rules do not name controller. Exact math and native-operation ladders remain at their authored nodes; the inventory groups them by obligation family rather than claiming that a prose summary replaces every operand.

The evidence classes here are deliberately limited. Authoring/imported declaration structure can establish a stated shape or dependency; it cannot establish runtime reachability. The tree's constructed controls claim interpretation/failure coverage, not native generation of their inputs. Named executed support is historical metadata only in this report: no raw run was inspected or credited anew. I did not run tests, builds, generators, native helpers or commands that mutate machine resources. No worktree, commit or helper agent was created. Only this report is written.

Required guidance read: root README/AGENTS/CONTRIBUTING, controller AGENTS, docs AGENTS, contract README/AGENTS, tests AGENTS/README and records AGENTS, plus the full integration plan. The controller README was read after the authored-surface inventory had been organized; its module map and architectural summary were incidental exposure and are not implementation evidence. Root README exposed the host/worker/validator overview and the failed-open example; tests README exposed suite summaries, consumer/result-account assertions and recovery mechanics. No cited production or test assertion file was opened. `record_definitions.py` was read as the permitted import/authoring declaration model; its extraction code mentions and quotes narrow declaration/serialization patterns, which is recorded exposure, not a production implementation audit. Generated CONTRACT navigation and current extracted example were read. No ARCHITECTURE/WORKER tour or architecture manifest was used as an inventory outline.

An initial `BASELINE.md` range read unintentionally included its prerequisite-review summary (including coordinator descriptions of emitter/preparation/consumer checks and historical totals), beyond the requested entry/identity section. That exposure is recorded rather than claiming a blind packet. It was not used as an obligation inventory or accepted as independent implementation/evidence credit. No B/C/D report, interim finding or transcript was accessed; no findings were sent to those principals.

Some large initial inspection outputs were truncated. Follow-up targeted readings covered the operative controller rules and referenced producer families; the authored-node extraction in the appendices covers the complete file set without output truncation. This is a substantial obligation inventory, not a claim that every native numeric predicate has received an independent proof or every possible implication of the normative prose is settled. Cross-examination should challenge omissions using exact node IDs, especially original-request association, publication failure and selection semantics.

Consequential unresolved questions are Q2–Q5 and Q8–Q10: success under integrity findings; dependent scope of withholding/degradation; general public-output failure semantics; original-request versus carried-record authority; check specificity; independent outer-result admission; and selection's normative coverage. They cannot be resolved by silently copying current implementation into prose, by counting citations, or by majority agreement among readers. The current retained promises and explicit open decisions remain in force until adjudicated.

## Appendix 1 — exact rule/context register

The authored scan found 1907 nodes in 19 surfaces and 53 action/report/check nodes with effective controller membership. Each `AR:<node>` is a stable local sub-ID, supplementing A01–A56. These are not the complete controller obligations: field/prose/shared-system rows above are independently required. Context below is inherited by heading ancestry with local replacement. The source link identifies the authored file; subordinate IDs retain exact distinctions. Support listings are claims carried in the tree, not inspected source/assertion evidence.

### AR:identity.version.emit — Version command

Authored source: [docs/contract/00-identity.surface.md](../../docs/contract/00-identity.surface.md) at line 788. Ancestors: `identity` → `identity.version`.

Effective context: who = `identity.definitions.controller`; where = `CLI version dispatch`; entry = `version`; recipient = `cli_caller`; report = `version`.

Context/dependency derivation:

- `identity.version.emit` uses: `["identity.definitions.envelope", "identity.build.contract"]`
- `identity.version.emit` free.condition: `The first command argument is --version or version.`

Claimed support:

- `identity.version.emit.support` (check_read, self): --version succeeds, emits kind version and result.ok true, supplies populated packaged build fields, and reports candidate-plist identity in data and build.
- `identity.version.emit.disposition_support` (check_read, self): Version dispatch precedes other command parsing.

### AR:request.specimen.hold — Hold and deliver the selected request

Authored source: [docs/contract/10-request.surface.md](../../docs/contract/10-request.surface.md) at line 63. Ancestors: `request` → `request.specimen`.

Effective context: who = `identity.definitions.controller`; where = `saved-file processing`; entry = `cli_run`; recipient = `caller, report_reader`; report = `run_envelope`.

Context/dependency derivation:

- `request.specimen.hold` uses: `["identity.definitions.specimen", "identity.definitions.request"]`

Claimed support:

- `request.specimen.support` (check_read, subtree): The adjacent field meanings and obligations follow the named producer and admission branches.

### AR:request.specimen.emit_example — Emit the example specimen

Authored source: [docs/contract/10-request.surface.md](../../docs/contract/10-request.surface.md) at line 182. Ancestors: `request` → `request.specimen`.

Effective context: who = `identity.definitions.controller`; where = `CLI example dispatch`; entry = `cli_example`; recipient = `cli_caller`; report = `example_specimen`.

Context/dependency derivation:

- `request.specimen.emit_example` uses: `["identity.build.contract", "identity.definitions.specimen"]`

Claimed support:

- `request.specimen.emit_example.support` (check_read, self): Emission parses the constant, inserts the binary's identity, passes the contract gate and uses the held request's serialization before any byte is written. An argument, an empty or unbound identity, a gate refusal and a failed write or flush each return the refusal that the command maps to exit 2. The emitted file reaches the controlled client as emitted, without its framing newline. On the selected app the command exits 0 with one JSON object and one newline carrying the app's identity, repeats it byte for byte, refuses every argument, and exits 2 when stdout has no reader whether or not stderr can be written; a build without an identity prints nothing.
- `request.specimen.support` (check_read, subtree): The adjacent field meanings and obligations follow the named producer and admission branches.

### AR:request.options.precedence — Selector precedence

Authored source: [docs/contract/10-request.surface.md](../../docs/contract/10-request.surface.md) at line 328. Ancestors: `request` → `request.options`.

Effective context: who = `identity.definitions.controller`; where = `runner selector parsing`; entry = `cli_run`; recipient = `caller, report_reader`; report = `run_envelope`.

Claimed support:

- `request.options.support` (check_read, subtree): The adjacent field meanings and obligations follow the named producer and admission branches.

### AR:request.options.failure_order — Selection and augmentation failure order

Authored source: [docs/contract/10-request.surface.md](../../docs/contract/10-request.surface.md) at line 342. Ancestors: `request` → `request.options`.

Effective context: who = `identity.definitions.controller`; where = `request preparation`; entry = `cli_run`; recipient = `caller, report_reader`; report = `run_envelope`.

Context/dependency derivation:

- `request.options.failure_order` uses: `["refusals.controller.consequence"]`

Claimed support:

- `request.options.support` (check_read, subtree): The adjacent field meanings and obligations follow the named producer and admission branches.

### AR:policy.augments.resolve — Resolve and append

Authored source: [docs/contract/11-policy.surface.md](../../docs/contract/11-policy.surface.md) at line 141. Ancestors: `policy` → `policy.augments`.

Effective context: who = `identity.definitions.controller`; where = `saved-file policy normalization`; entry = `cli_run`; recipient = `caller, report_reader`; report = `run_envelope`.

Claimed support:

- `policy.augments.support` (check_read, subtree): The adjacent field meanings and operations follow the named implementation.

### AR:policy.augments.actors — Resolve actor policies in request order

Authored source: [docs/contract/11-policy.surface.md](../../docs/contract/11-policy.surface.md) at line 155. Ancestors: `policy` → `policy.augments`.

Effective context: who = `identity.definitions.controller`; where = `actor policy normalization`; entry = `cli_run`; recipient = `caller, report_reader`; report = `run_envelope`.

Claimed support:

- `policy.augments.support` (check_read, subtree): The adjacent field meanings and operations follow the named implementation.

### AR:policy.imports.holds — Separate reads and their identities

Authored source: [docs/contract/11-policy.surface.md](../../docs/contract/11-policy.surface.md) at line 569. Ancestors: `policy` → `policy.imports`.

Effective context: who = `identity.definitions.controller, identity.definitions.helper, identity.definitions.worker`; where = `policy preparation and import reads`; entry = `cli_run, standalone_helper, xpc_execute`; recipient = `caller, report_reader`; report = `run_envelope, helper_envelope, runner_reply`.

Claimed support:

- `policy.imports.support` (source_read, subtree): The adjacent field meanings and operations follow the named implementation.

### AR:policy.fallback.classify — Fallback eligibility and classification

Authored source: [docs/contract/11-policy.surface.md](../../docs/contract/11-policy.surface.md) at line 685. Ancestors: `policy` → `policy.fallback`.

Effective context: who = `identity.definitions.controller`; where = `admitted client capture after xpc_error`; entry = `cli_run`; recipient = `caller, report_reader`; report = `run_envelope`.

Claimed support:

- `policy.fallback.support` (check_read, subtree): The adjacent field meanings and operations follow the named implementation.

### AR:refusals.controller.consequence — Controller pre-invocation refusal

Authored source: [docs/contract/15-refusals.surface.md](../../docs/contract/15-refusals.surface.md) at line 153. Ancestors: `refusals` → `refusals.controller`.

Effective context: who = `identity.definitions.controller`; where = `CLI preparation`; entry = `cli_run`; recipient = `caller, report_reader`; report = `run_envelope`.

Context/dependency derivation:

- `refusals.controller.consequence` uses: `["request.options", "policy.augments"]`

Subordinate commitment nodes: `refusals.controller.consequence.request_refusal` (outcome), `refusals.controller.consequence.tool_failure` (outcome), `refusals.controller.consequence.class` (condition).

Claimed support:

- `refusals.controller.support` (check_read, subtree): The adjacent meanings follow the named request, producer and observation branches.

### AR:transport.delivery.deadline — Apply the original allowance

Authored source: [docs/contract/20-transport.surface.md](../../docs/contract/20-transport.surface.md) at line 133. Ancestors: `transport` → `transport.delivery`.

Effective context: who = `identity.definitions.controller, identity.definitions.client`; where = `client launch, input delivery, acquisition and execution wait`; entry = `cli_run, runner_verify`; recipient = `cli_caller`; report = `client_capture, run_envelope, runner_verify`.

Context/dependency derivation:

- `transport.delivery.deadline` free.condition: `The controller invokes its runner client with timeout_ms clamped to at least one millisecond.`

Claimed support:

- `transport.support` (check_read, subtree): Source defines all imported fields, reservation state transitions, capture gates, preservation and deadline boundaries. Controlled tests establish retry/invocation accounting, connection binding, bound-control admission, byte preservation and delivery-error precedence.

### AR:transport.client.admit — Admit client and host observations

Authored source: [docs/contract/20-transport.surface.md](../../docs/contract/20-transport.surface.md) at line 561. Ancestors: `transport` → `transport.client`.

Effective context: who = `identity.definitions.controller`; where = `completed client stdout and nested host frame`; entry = `cli_run, runner_verify`; recipient = `cli_caller`; report = `run_envelope, runner_verify`.

Context/dependency derivation:

- `transport.client.admit` uses: `["identity.public.contract"]`
- `transport.client.admit` free.condition: `The client process and input writer completed collection.`

Subordinate commitment nodes: `transport.client.admit.delivery` (condition), `transport.client.admit.retention` (condition), `transport.client.admit.missing` (condition).

Claimed support:

- `transport.support` (check_read, subtree): Source defines all imported fields, reservation state transitions, capture gates, preservation and deadline boundaries. Controlled tests establish retry/invocation accounting, connection binding, bound-control admission, byte preservation and delivery-error precedence.
- `transport.client.admit.selection_source` (source_read, self): Completed collection first selects input-delivery error, then retained-output loss, then an empty capture. These paths preserve unknown submission and skip both frame decoders.

### AR:wire.frame.admit — Exact structural admission

Authored source: [docs/contract/21-wire.surface.md](../../docs/contract/21-wire.surface.md) at line 73. Ancestors: `wire` → `wire.frame`.

Effective context: who = `identity.definitions.controller, wire.frame.reader`; where = `one complete client-capture or host-reply frame`; entry = `client_stdout, host_reply, retained_frame`; recipient = `controller, report_reader`; report = `run_envelope`.

Context/dependency derivation:

- `wire.frame.admit` uses: `["identity.public.contract", "identity.other.wire"]`
- `wire.frame.admit` free.condition: `A complete frame has been retained for the requested root kind.`

Claimed support:

- `wire.support` (check_read, subtree): The schema owns record identities/tags/types and public projections. Swift writes declared values; Rust and Python independently read their structure. The named controls reject authored scalar/record faults and preserve byte projections.

### AR:actor_evidence.gate.check — Checking a carried gate

Authored source: [docs/contract/33-actor_evidence.surface.md](../../docs/contract/33-actor_evidence.surface.md) at line 740. Ancestors: `actor_evidence` → `actor_evidence.gate`.

Effective context: who = `identity.definitions.controller`; where = `semantic assessment after reply admission`; entry = `cli_run`; recipient = `cli_caller`; report = `runner_reply`.

Context/dependency derivation:

- `actor_evidence.gate.check` bind.p: `reply.phases`
- `actor_evidence.gate.check` bind.s: `reply.actors`
- `actor_evidence.gate.check` bind.f: `reply.phases`
- `actor_evidence.gate.check` match.s: `reply.actors[s].actor_id == reply.phases[p].termination_gate.source_actor_id`
- `actor_evidence.gate.check` match.f: `reply.phases[f].phase_id == reply.phases[p].termination_gate.source_final_phase_id`
- `actor_evidence.gate.check` when: `absent(reply.reporting_failure) and reply.execution_form == "actors" and present(reply.phases[p].termination_gate)`
- `actor_evidence.gate.check` failure: `accumulate`
- `actor_evidence.gate.check` free.condition: `Resolve source and final-phase joins before using s or f; missing, nonfinal, same-actor or nonpreceding associations are findings. Check owned PID/native-status agreement, all conditional gate captures, independent actor setup/equipment eligibility and activation timing.`

Subordinate commitment nodes: `actor_evidence.gate.check.failed` (effect), `actor_evidence.gate.check.unreached` (condition), `actor_evidence.gate.check.timely` (condition), `actor_evidence.gate.check.sequence` (condition), `actor_evidence.gate.check.eligibility` (condition).

Claimed support:

- `actor_evidence.support` (source_read, subtree): Imported public field definitions joined to producer/decoder/assessment meanings; explicit rule and evidence gaps preserve scope.

### AR:profile.receipt.labels — The controller checks carried labels

Authored source: [docs/contract/35-profile.surface.md](../../docs/contract/35-profile.surface.md) at line 300. Ancestors: `profile` → `profile.receipt`.

Effective context: entry = `cli_run, runner_verify`; recipient = `cli_caller`; report = `runner_reply`; who = `identity.definitions.controller`; where = `reply_admission`.

Context/dependency derivation:

- `profile.receipt` bind.a: `reply.actors`
- `profile.receipt.labels` when: `present(receipt)`

Subordinate commitment nodes: `profile.receipt.labels.status` (condition), `profile.receipt.labels.captured` (condition), `profile.receipt.labels.unavailable` (condition), `profile.receipt.labels.failure` (effect), `profile.receipt.labels.verify_failure` (effect), `profile.receipt.labels.example` (example).

Claimed support:

- `profile.receipt.labels.support` (source_read, subtree): Run and runner verify use the same post-version reply admission; it checks each present top-level or actor receipt's status, producer and capture-stage labels before command-specific refusal projection.
- `profile.receipt.source` (source_read, subtree): Opt-in capture copies the same compiled object before apply; the collected worker output includes the optional host-checked receipt. Fields bind the observed worker, nonce and consumed input bytes. Shared-memory and public JSON projections are distinct.

### AR:envelope.data.select — Select the public result

Authored source: [docs/contract/40-envelope.surface.md](../../docs/contract/40-envelope.surface.md) at line 186. Ancestors: `envelope` → `envelope.data`.

Effective context: who = `identity.definitions.controller`; where = `run completion after admission`; entry = `cli_run`; recipient = `cli_caller`; report = `run_envelope`.

Context/dependency derivation:

- `envelope.data.select` after: `["diagnostics.execution.reply_checks"]`
- `envelope.data.select` when: `present(envelope.data.runner_result)`
- `envelope.data.select` free.when: `Client capture and host reply admission have succeeded.`
- `envelope.data.select` selection: `first_match`

Subordinate commitment nodes: `envelope.data.select.success_findings` (gap), `envelope.data.select.finished` (outcome), `envelope.data.select.other` (outcome).

Claimed support:

- `envelope.support` (check_read, subtree): Constructed outcomes preserve nested native evidence and select success only for finished. A real fixture child exposes delivery refusal precedence. Rendering serializes the borrowed payload once.

### AR:envelope.data.admit — Boundary precedence

Authored source: [docs/contract/40-envelope.surface.md](../../docs/contract/40-envelope.surface.md) at line 243. Ancestors: `envelope` → `envelope.data`.

Effective context: who = `identity.definitions.controller`; where = `received run data admission`; entry = `cli_run`; recipient = `cli_caller`; report = `run_envelope`.

Context/dependency derivation:

- `envelope.data.admit` failure: `first`
- `envelope.data.admit` free.condition: `Check request delivery error first, then client failure (capture admission, host frame admission and transport terminal), then decoded host producer identity and host capacity/profile-label admission.`

Claimed support:

- `envelope.support` (check_read, subtree): Constructed outcomes preserve nested native evidence and select success only for finished. A real fixture child exposes delivery refusal precedence. Rendering serializes the borrowed payload once.

### AR:diagnostics.execution.geometry — Decoded response collection bounds

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 74. Ancestors: `diagnostics` → `diagnostics.execution`.

Effective context: who = `identity.definitions.controller`; where = `decoded response-context admission after delivery, capture and public identity admission`; entry = `cli_run, runner_verify`; recipient = `caller, report_reader`; report = `run_envelope, runner_verify`.

Context/dependency derivation:

- `diagnostics.execution.geometry` when: `present(reply)`
- `diagnostics.execution.geometry` bind.p: `reply.phases`
- `diagnostics.execution.geometry` bind.a: `reply.actors`

Subordinate commitment nodes: `diagnostics.execution.geometry.plan` (condition), `diagnostics.execution.geometry.actors_transfers` (condition), `diagnostics.execution.geometry.resources` (condition), `diagnostics.execution.geometry.equal_handles` (condition), `diagnostics.execution.geometry.validator` (condition), `diagnostics.execution.geometry.validator.expected` (condition), `diagnostics.execution.geometry.validator.records` (condition), `diagnostics.execution.geometry.validator.issues` (condition), `diagnostics.execution.geometry.equipment` (condition), `diagnostics.execution.geometry.authority` (condition), `diagnostics.execution.geometry.host_scope` (condition), `diagnostics.execution.geometry.worker_scopes` (condition), `diagnostics.execution.geometry.region_scopes` (condition), `diagnostics.execution.geometry.custody_scopes` (condition), `diagnostics.execution.geometry.visits` (condition), `diagnostics.execution.geometry.actor_equipment` (condition), `diagnostics.execution.geometry.ordinary_lifecycle` (condition), `diagnostics.execution.geometry.ordinary_lifecycle.rows` (condition), `diagnostics.execution.geometry.ordinary_lifecycle.run_references` (condition), `diagnostics.execution.geometry.ordinary_lifecycle.step_references` (condition), `diagnostics.execution.geometry.ordinary_lifecycle.issue_references` (condition), `diagnostics.execution.geometry.actor_lifecycle` (condition), `diagnostics.execution.geometry.actor_lifecycle.rows` (condition), `diagnostics.execution.geometry.actor_lifecycle.run_references` (condition), `diagnostics.execution.geometry.actor_lifecycle.step_references` (condition), `diagnostics.execution.geometry.actor_lifecycle.issue_references` (condition), `diagnostics.execution.geometry.step_copies` (condition), `diagnostics.execution.geometry.extension_copies` (condition), `diagnostics.execution.geometry.failed` (effect), `diagnostics.execution.geometry.run_refusal` (effect), `diagnostics.execution.geometry.verify_refusal` (effect).

Claimed support:

- `diagnostics.execution.geometry.support` (check_read, subtree): Collection bounds precede semantic joins and profile-context checking on run and verification admission; their refusal retains the decoded reply.
- `diagnostics.execution.support` (check_read, subtree): Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches.

### AR:diagnostics.execution.admit — Admit the response before assessment

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 333. Ancestors: `diagnostics` → `diagnostics.execution`.

Effective context: who = `identity.definitions.controller`; where = `client delivery, public reply identity and bounded response context`; entry = `cli_run`; recipient = `caller, report_reader`; report = `run_envelope`.

Context/dependency derivation:

- `diagnostics.execution.admit` uses: `["diagnostics.execution.geometry"]`

Subordinate commitment nodes: `diagnostics.execution.admit.context_refusal` (outcome).

Claimed support:

- `diagnostics.execution.support` (check_read, subtree): Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches.

### AR:diagnostics.execution.project — Project one worker or aggregate actors

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 363. Ancestors: `diagnostics` → `diagnostics.execution`.

Effective context: who = `identity.definitions.controller`; where = `typed worker lifecycle interpretation after response admission`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Claimed support:

- `diagnostics.execution.support` (check_read, subtree): Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches.

### AR:diagnostics.execution.actor_rows — Actor projection rows

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 383. Ancestors: `diagnostics` → `diagnostics.execution`.

Effective context: who = `identity.definitions.controller`; where = `worker projection after response admission`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.execution.actor_rows` when: `reply.execution_form == "actors"`
- `diagnostics.execution.actor_rows` bind.a: `reply.actors`
- `diagnostics.execution.actor_rows` bind.d: `envelope.data.runner_sandbox_diagnostics.actors`
- `diagnostics.execution.actor_rows` match.d: `d == a`

Subordinate commitment nodes: `diagnostics.execution.actor_rows.coverage` (condition), `diagnostics.execution.actor_rows.identity` (condition).

Claimed support:

- `diagnostics.execution.support` (check_read, subtree): Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches.

### AR:diagnostics.execution.ordinary.lifecycle_check — Worker lifecycle validation

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 427. Ancestors: `diagnostics` → `diagnostics.execution` → `diagnostics.execution.ordinary`.

Effective context: who = `identity.definitions.controller`; where = `one worker lifecycle validation before projection`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.execution.ordinary` when: `(absent(reply.execution_form) or (present(reply.execution_form) and reply.execution_form != "actors")) and present(reply.runner_subprocess)`
- `diagnostics.execution.ordinary.lifecycle_check` free.condition: `For reply.runner_subprocess and its assigned actions under the carried reporting form, the controller's lifecycle validation returns no failed-check findings, before validated host conflicts are copied.`

Subordinate commitment nodes: `diagnostics.execution.ordinary.lifecycle_check.local_failure` (effect).

Claimed support:

- `diagnostics.execution.support` (check_read, subtree): Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches.

### AR:diagnostics.execution.ordinary.mapping — Ending mapping

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 448. Ancestors: `diagnostics` → `diagnostics.execution` → `diagnostics.execution.ordinary`.

Effective context: who = `identity.definitions.controller`; where = `validated worker ending projection`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.execution.ordinary` when: `(absent(reply.execution_form) or (present(reply.execution_form) and reply.execution_form != "actors")) and present(reply.runner_subprocess)`
- `diagnostics.execution.ordinary.mapping` requires: `["diagnostics.execution.ordinary.lifecycle_check"]`
- `diagnostics.execution.ordinary.mapping` when: `present(reply.runner_subprocess.disposition) and present(reply.runner_subprocess.disposition.questions.final_status)`
- `diagnostics.execution.ordinary.mapping` selection: `first_match`

Subordinate commitment nodes: `diagnostics.execution.ordinary.mapping.clean` (outcome), `diagnostics.execution.ordinary.mapping.nonzero` (outcome), `diagnostics.execution.ordinary.mapping.signal` (outcome), `diagnostics.execution.ordinary.mapping.conflict` (outcome), `diagnostics.execution.ordinary.mapping.unconfirmed` (outcome), `diagnostics.execution.ordinary.mapping.other` (outcome).

Claimed support:

- `diagnostics.execution.support` (check_read, subtree): Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches.

### AR:diagnostics.execution.ordinary.stop — Supported stop reason

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 506. Ancestors: `diagnostics` → `diagnostics.execution` → `diagnostics.execution.ordinary`.

Effective context: who = `identity.definitions.controller`; where = `validated worker ending projection`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.execution.ordinary` when: `(absent(reply.execution_form) or (present(reply.execution_form) and reply.execution_form != "actors")) and present(reply.runner_subprocess)`
- `diagnostics.execution.ordinary.stop` requires: `["diagnostics.execution.ordinary.lifecycle_check"]`
- `diagnostics.execution.ordinary.stop` when: `present(reply.runner_subprocess.disposition)`
- `diagnostics.execution.ordinary.stop` selection: `first_match`
- `diagnostics.execution.ordinary.stop` after: `["diagnostics.execution.ordinary.cause"]`

Subordinate commitment nodes: `diagnostics.execution.ordinary.stop.recognized` (outcome), `diagnostics.execution.ordinary.stop.absent` (outcome).

Claimed support:

- `diagnostics.execution.support` (check_read, subtree): Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches.

### AR:diagnostics.execution.ordinary.cause — Host-cleanup attribution

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 546. Ancestors: `diagnostics` → `diagnostics.execution` → `diagnostics.execution.ordinary`.

Effective context: who = `identity.definitions.controller`; where = `validated worker ending projection`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.execution.ordinary` when: `(absent(reply.execution_form) or (present(reply.execution_form) and reply.execution_form != "actors")) and present(reply.runner_subprocess)`
- `diagnostics.execution.ordinary.cause` requires: `["diagnostics.execution.ordinary.lifecycle_check"]`
- `diagnostics.execution.ordinary.cause` when: `present(reply.runner_subprocess.disposition) and present(reply.runner_subprocess.disposition.questions.final_status) and reply.runner_subprocess.disposition.questions.final_status.state == "supported" and reply.runner_subprocess.disposition.questions.final_status.answer == "signal"`
- `diagnostics.execution.ordinary.cause` selection: `first_match`
- `diagnostics.execution.ordinary.cause` after: `["diagnostics.execution.ordinary.mapping"]`

Subordinate commitment nodes: `diagnostics.execution.ordinary.cause.deadline_expiry` (outcome), `diagnostics.execution.ordinary.cause.completion` (outcome), `diagnostics.execution.ordinary.cause.poll_wait_error` (outcome), `diagnostics.execution.ordinary.cause.policy_transfer_error` (outcome), `diagnostics.execution.ordinary.cause.policy_transfer_timeout` (outcome), `diagnostics.execution.ordinary.cause.unknown` (outcome).

Claimed support:

- `diagnostics.execution.support` (check_read, subtree): Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches.

### AR:diagnostics.execution.ordinary.host_conflicts — Copy validated host conflicts

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 607. Ancestors: `diagnostics` → `diagnostics.execution` → `diagnostics.execution.ordinary`.

Effective context: who = `identity.definitions.controller`; where = `worker projection after response admission`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.execution.ordinary` when: `(absent(reply.execution_form) or (present(reply.execution_form) and reply.execution_form != "actors")) and present(reply.runner_subprocess)`
- `diagnostics.execution.ordinary.host_conflicts` requires: `["diagnostics.execution.ordinary.lifecycle_check"]`
- `diagnostics.execution.ordinary.host_conflicts` bind.i: `reply.runner_subprocess.disposition.issues`
- `diagnostics.execution.ordinary.host_conflicts` bind.j: `envelope.data.runner_sandbox_diagnostics.disposition_issues`
- `diagnostics.execution.ordinary.host_conflicts` match.j: `j == i`
- `diagnostics.execution.ordinary.host_conflicts` when: `present(reply.runner_subprocess.disposition)`
- `diagnostics.execution.ordinary.host_conflicts` after: `["diagnostics.execution.ordinary.stop"]`

Subordinate commitment nodes: `diagnostics.execution.ordinary.host_conflicts.coverage` (condition), `diagnostics.execution.ordinary.host_conflicts.copy` (effect).

Claimed support:

- `diagnostics.execution.support` (check_read, subtree): Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches.

### AR:diagnostics.execution.reply_checks — Apply reply-wide findings

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 634. Ancestors: `diagnostics` → `diagnostics.execution`.

Effective context: who = `identity.definitions.controller`; where = `typed reply relationship checks after worker projections`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.execution.reply_checks` free.condition: `One or more applicable reply-wide checks finds an invalid relationship.`
- `diagnostics.execution.reply_checks` after: `["diagnostics.execution.project"]`

Claimed support:

- `diagnostics.execution.support` (check_read, subtree): Worker-local and reply-wide projection effects, raw-record retention, open summaries, degradation applicability and outer success are distinct branches.

### AR:diagnostics.actor.projection.lifecycle_check — Worker lifecycle validation

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 832. Ancestors: `diagnostics` → `diagnostics.actor` → `diagnostics.actor.projection`.

Effective context: who = `identity.definitions.controller`; where = `one worker lifecycle validation before projection`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.actor.projection` bind.a: `reply.actors`
- `diagnostics.actor.projection` bind.d: `envelope.data.runner_sandbox_diagnostics.actors`
- `diagnostics.actor.projection` match.d: `d == a`
- `diagnostics.actor.projection` each: `["a", "d"]`
- `diagnostics.actor.projection` when: `reply.execution_form == "actors" and present(reply.actors) and present(reply.actors[a].subprocess)`
- `diagnostics.actor.projection.lifecycle_check` free.condition: `For reply.actors[a].subprocess and its assigned actions under the carried reporting form, the controller's lifecycle validation returns no failed-check findings, before validated host conflicts are copied.`

Subordinate commitment nodes: `diagnostics.actor.projection.lifecycle_check.local_failure` (effect).

Claimed support:

- `diagnostics.actor.support` (check_read, subtree): The mapping follows admitted final-status claims; named host causes require the supported cleanup/request/ending chain.

### AR:diagnostics.actor.projection.mapping — Ending mapping

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 853. Ancestors: `diagnostics` → `diagnostics.actor` → `diagnostics.actor.projection`.

Effective context: who = `identity.definitions.controller`; where = `validated worker ending projection`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.actor.projection` bind.a: `reply.actors`
- `diagnostics.actor.projection` bind.d: `envelope.data.runner_sandbox_diagnostics.actors`
- `diagnostics.actor.projection` match.d: `d == a`
- `diagnostics.actor.projection` each: `["a", "d"]`
- `diagnostics.actor.projection` when: `reply.execution_form == "actors" and present(reply.actors) and present(reply.actors[a].subprocess)`
- `diagnostics.actor.projection.mapping` requires: `["diagnostics.actor.projection.lifecycle_check"]`
- `diagnostics.actor.projection.mapping` when: `present(reply.actors[a].subprocess.disposition) and present(reply.actors[a].subprocess.disposition.questions.final_status)`
- `diagnostics.actor.projection.mapping` selection: `first_match`

Subordinate commitment nodes: `diagnostics.actor.projection.mapping.clean` (outcome), `diagnostics.actor.projection.mapping.nonzero` (outcome), `diagnostics.actor.projection.mapping.signal` (outcome), `diagnostics.actor.projection.mapping.conflict` (outcome), `diagnostics.actor.projection.mapping.unconfirmed` (outcome), `diagnostics.actor.projection.mapping.other` (outcome).

Claimed support:

- `diagnostics.actor.support` (check_read, subtree): The mapping follows admitted final-status claims; named host causes require the supported cleanup/request/ending chain.

### AR:diagnostics.actor.projection.stop — Supported stop reason

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 911. Ancestors: `diagnostics` → `diagnostics.actor` → `diagnostics.actor.projection`.

Effective context: who = `identity.definitions.controller`; where = `validated worker ending projection`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.actor.projection` bind.a: `reply.actors`
- `diagnostics.actor.projection` bind.d: `envelope.data.runner_sandbox_diagnostics.actors`
- `diagnostics.actor.projection` match.d: `d == a`
- `diagnostics.actor.projection` each: `["a", "d"]`
- `diagnostics.actor.projection` when: `reply.execution_form == "actors" and present(reply.actors) and present(reply.actors[a].subprocess)`
- `diagnostics.actor.projection.stop` requires: `["diagnostics.actor.projection.lifecycle_check"]`
- `diagnostics.actor.projection.stop` when: `present(reply.actors[a].subprocess.disposition)`
- `diagnostics.actor.projection.stop` selection: `first_match`
- `diagnostics.actor.projection.stop` after: `["diagnostics.actor.projection.cause"]`

Subordinate commitment nodes: `diagnostics.actor.projection.stop.recognized` (outcome), `diagnostics.actor.projection.stop.absent` (outcome).

Claimed support:

- `diagnostics.actor.support` (check_read, subtree): The mapping follows admitted final-status claims; named host causes require the supported cleanup/request/ending chain.

### AR:diagnostics.actor.projection.cause — Host-cleanup attribution

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 951. Ancestors: `diagnostics` → `diagnostics.actor` → `diagnostics.actor.projection`.

Effective context: who = `identity.definitions.controller`; where = `validated worker ending projection`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.actor.projection` bind.a: `reply.actors`
- `diagnostics.actor.projection` bind.d: `envelope.data.runner_sandbox_diagnostics.actors`
- `diagnostics.actor.projection` match.d: `d == a`
- `diagnostics.actor.projection` each: `["a", "d"]`
- `diagnostics.actor.projection` when: `reply.execution_form == "actors" and present(reply.actors) and present(reply.actors[a].subprocess)`
- `diagnostics.actor.projection.cause` requires: `["diagnostics.actor.projection.lifecycle_check"]`
- `diagnostics.actor.projection.cause` when: `present(reply.actors[a].subprocess.disposition) and present(reply.actors[a].subprocess.disposition.questions.final_status) and reply.actors[a].subprocess.disposition.questions.final_status.state == "supported" and reply.actors[a].subprocess.disposition.questions.final_status.answer == "signal"`
- `diagnostics.actor.projection.cause` selection: `first_match`
- `diagnostics.actor.projection.cause` after: `["diagnostics.actor.projection.mapping"]`

Subordinate commitment nodes: `diagnostics.actor.projection.cause.deadline_expiry` (outcome), `diagnostics.actor.projection.cause.completion` (outcome), `diagnostics.actor.projection.cause.poll_wait_error` (outcome), `diagnostics.actor.projection.cause.policy_transfer_error` (outcome), `diagnostics.actor.projection.cause.policy_transfer_timeout` (outcome), `diagnostics.actor.projection.cause.unknown` (outcome).

Claimed support:

- `diagnostics.actor.support` (check_read, subtree): The mapping follows admitted final-status claims; named host causes require the supported cleanup/request/ending chain.

### AR:diagnostics.actor.projection.host_conflicts — Copy validated host conflicts

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 1012. Ancestors: `diagnostics` → `diagnostics.actor` → `diagnostics.actor.projection`.

Effective context: who = `identity.definitions.controller`; where = `worker projection after response admission`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Context/dependency derivation:

- `diagnostics.actor.projection` bind.a: `reply.actors`
- `diagnostics.actor.projection` bind.d: `envelope.data.runner_sandbox_diagnostics.actors`
- `diagnostics.actor.projection` match.d: `d == a`
- `diagnostics.actor.projection` each: `["a", "d"]`
- `diagnostics.actor.projection` when: `reply.execution_form == "actors" and present(reply.actors) and present(reply.actors[a].subprocess)`
- `diagnostics.actor.projection.host_conflicts` requires: `["diagnostics.actor.projection.lifecycle_check"]`
- `diagnostics.actor.projection.host_conflicts` bind.i: `reply.actors[a].subprocess.disposition.issues`
- `diagnostics.actor.projection.host_conflicts` bind.j: `envelope.data.runner_sandbox_diagnostics.actors[d].disposition_issues`
- `diagnostics.actor.projection.host_conflicts` match.j: `j == i`
- `diagnostics.actor.projection.host_conflicts` when: `present(reply.actors[a].subprocess.disposition)`
- `diagnostics.actor.projection.host_conflicts` after: `["diagnostics.actor.projection.stop"]`

Subordinate commitment nodes: `diagnostics.actor.projection.host_conflicts.coverage` (condition), `diagnostics.actor.projection.host_conflicts.copy` (effect).

Claimed support:

- `diagnostics.actor.support` (check_read, subtree): The mapping follows admitted final-status claims; named host causes require the supported cleanup/request/ending chain.

### AR:diagnostics.issue.retain — Retain observation and finding separately

Authored source: [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md) at line 1110. Ancestors: `diagnostics` → `diagnostics.issue`.

Effective context: who = `identity.definitions.controller`; where = `integrity finding construction`; entry = `cli_run`; recipient = `report_reader`; report = `execution_diagnostics, actor_execution_diagnostics`.

Claimed support:

- `diagnostics.issue.support` (source_read, subtree): Gate-family findings carry locations in the retained reply while preserving existing predicates, detail, order and projection scope. Copied host issues preserve their own metadata.

### AR:dossier.collection.held — Hold the selected request

Authored source: [docs/contract/42-dossier.surface.md](../../docs/contract/42-dossier.surface.md) at line 27. Ancestors: `dossier` → `dossier.collection`.

Effective context: who = `identity.definitions.controller`; where = `request preparation before runner-client invocation and fallback compile`; entry = `cli_run`; recipient = `cli_caller, runner_client, compiler_helper`; report = `specimen_dossier`.

Context/dependency derivation:

- `dossier.collection.held` uses: `["identity.definitions.request", "identity.definitions.bytes"]`
- `dossier.collection.held` free.condition: `A request has been parsed and controller policy changes have been resolved in memory.`

Claimed support:

- `dossier.support` (check_read, subtree): Declarations and collection branches establish field provenance, augmentation states, literal import closure and role-specific comparisons. Unit controls assert unavailable/partial states and comparisons against synthetic manifest baselines.

### AR:dossier.collection.scan — Scan literal imports

Authored source: [docs/contract/42-dossier.surface.md](../../docs/contract/42-dossier.surface.md) at line 43. Ancestors: `dossier` → `dossier.collection`.

Effective context: who = `identity.definitions.controller`; where = `selected policy source and local import files before invocation`; entry = `cli_run`; recipient = `cli_caller`; report = `specimen_dossier`.

Context/dependency derivation:

- `dossier.collection.scan` free.condition: `The selected policy has string source within the <!-- span limits.helper_source.binary -->4 MiB<!-- /span --> source bound.`

Claimed support:

- `dossier.support` (check_read, subtree): Declarations and collection branches establish field provenance, augmentation states, literal import closure and role-specific comparisons. Unit controls assert unavailable/partial states and comparisons against synthetic manifest baselines.

### AR:dossier.collection.compare — Compare selected files

Authored source: [docs/contract/42-dossier.surface.md](../../docs/contract/42-dossier.surface.md) at line 58. Ancestors: `dossier` → `dossier.collection`.

Effective context: who = `identity.definitions.controller`; where = `selected runner/helper paths and embedded evidence manifest`; entry = `cli_run`; recipient = `cli_caller`; report = `specimen_dossier`.

Context/dependency derivation:

- `dossier.collection.compare` free.condition: `Runner selection supplies paths and the app evidence manifest supplies role baselines where available.`
- `dossier.collection.compare` uses: `["dossier.binary.classify"]`

Claimed support:

- `dossier.support` (check_read, subtree): Declarations and collection branches establish field provenance, augmentation states, literal import closure and role-specific comparisons. Unit controls assert unavailable/partial states and comparisons against synthetic manifest baselines.

### AR:dossier.augmentation.relationships — Augmentation record relationships

Authored source: [docs/contract/42-dossier.surface.md](../../docs/contract/42-dossier.surface.md) at line 194. Ancestors: `dossier` → `dossier.augmentation`.

Effective context: who = `identity.definitions.controller`; where = `augmentation dossier projection`; entry = `cli_run`; recipient = `report_reader`; report = `specimen_dossier`.

Subordinate commitment nodes: `dossier.augmentation.relationships.fields` (condition).

Claimed support:

- `dossier.support` (check_read, subtree): Declarations and collection branches establish field provenance, augmentation states, literal import closure and role-specific comparisons. Unit controls assert unavailable/partial states and comparisons against synthetic manifest baselines.
- `dossier.augmentation.relationships.support` (source_read, subtree): The four constructors preserve optional original/selected hashes and distinct failure/error states.

### AR:dossier.imports.scope — Retained scan scope

Authored source: [docs/contract/42-dossier.surface.md](../../docs/contract/42-dossier.surface.md) at line 252. Ancestors: `dossier` → `dossier.imports`.

Effective context: who = `identity.definitions.controller`; where = `literal import dossier projection`; entry = `cli_run`; recipient = `report_reader`; report = `specimen_dossier`.

Context/dependency derivation:

- `dossier.imports.scope` bind.r: `imports.records`
- `dossier.imports.scope` match.r: `present(imports.records[r].error)`

Subordinate commitment nodes: `dossier.imports.scope.fields` (condition).

Claimed support:

- `dossier.support` (check_read, subtree): Declarations and collection branches establish field provenance, augmentation states, literal import closure and role-specific comparisons. Unit controls assert unavailable/partial states and comparisons against synthetic manifest baselines.
- `dossier.imports.scope.support` (source_read, subtree): Performed complete/incomplete scans retain a closure; skipped/failed scans have no records. Complete scans have no carried cycle, exceeded bound or record errors.

### AR:dossier.binary.classify — Classify the retained digest pair

Authored source: [docs/contract/42-dossier.surface.md](../../docs/contract/42-dossier.surface.md) at line 402. Ancestors: `dossier` → `dossier.binary`.

Effective context: who = `identity.definitions.controller`; where = `selected binary comparison record after collection`; entry = `cli_run`; recipient = `report_reader`; report = `specimen_dossier`.

Context/dependency derivation:

- `dossier.binary.classify` selection: `first_match`

Subordinate commitment nodes: `dossier.binary.classify.match` (outcome), `dossier.binary.classify.mismatch` (outcome), `dossier.binary.classify.unavailable` (outcome).

Claimed support:

- `dossier.support` (check_read, subtree): Declarations and collection branches establish field provenance, augmentation states, literal import closure and role-specific comparisons. Unit controls assert unavailable/partial states and comparisons against synthetic manifest baselines.
- `dossier.binary.classify.support` (source_read, self): Available expected/actual digests select match or mismatch; missing operands retain unavailable with the collection diagnosis.

### AR:installation.commands.read — Read and select records

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 27. Ancestors: `installation` → `installation.commands`.

Effective context: who = `identity.definitions.controller`; where = `runner registry lookup`; entry = `runner_list, runner_status, runner_verify, runner_remove, runner_reconcile`; recipient = `cli_caller`; report = `runner_registry, runner_status, runner_verify, runner_remove, runner_reconcile`.

Context/dependency derivation:

- `installation.commands.read` free.condition: `The registry is readable with schema_version 1, or its path is absent.`

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.commands.publish — Publish a registry mutation

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 42. Ancestors: `installation` → `installation.commands`.

Effective context: who = `identity.definitions.controller`; where = `install, validate and remove registry transaction`; entry = `runner_install, runner_validate, runner_remove`; recipient = `cli_caller`; report = `runner_registry`.

Context/dependency derivation:

- `installation.commands.publish` free.condition: `The command holds the stable sibling registry lock across its mutation and associated launchd actions.`

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.commands.install — Install a selected service

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 57. Ancestors: `installation` → `installation.commands`.

Effective context: who = `identity.definitions.controller`; where = `external bundle validation, signing, registry and launchd`; entry = `runner_install`; recipient = `cli_caller, launchd`; report = `runner_install, runner_registry`.

Context/dependency derivation:

- `installation.commands.install` uses: `["identity.public.contract"]`
- `installation.commands.install` free.condition: `The caller supplies an existing bundle directory; the kind defaults to byoxpc, and an explicit kind must be byoxpc. Scope defaults to user or may be explicitly system.`

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.commands.pending — Retain installation ownership

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 73. Ancestors: `installation` → `installation.commands`.

Effective context: who = `identity.definitions.controller`; where = `pending registry save before plist creation and bootstrap`; entry = `runner_install`; recipient = `cli_caller, launchd`; report = `runner_install, runner_registry`.

Context/dependency derivation:

- `installation.commands.pending` free.condition: `Bundle verification/signing and readbacks succeeded and the launchd plist has been prepared.`

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.commands.verify — Verify a selected service

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 88. Ancestors: `installation` → `installation.commands`.

Effective context: who = `identity.definitions.controller, identity.definitions.client`; where = `fixed verification specimen through reservation and execution`; entry = `runner_verify`; recipient = `cli_caller, runner_host`; report = `runner_verify`.

Context/dependency derivation:

- `installation.commands.verify` uses: `["installation.verify.select", "installation.verify.delivery_failure", "diagnostics.execution.geometry"]`
- `installation.commands.verify` free.condition: `Lookup finds an external runner record.`

Subordinate commitment nodes: `installation.commands.verify.identity` (condition).

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.commands.validate — Refresh validation metadata

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 130. Ancestors: `installation` → `installation.commands`.

Effective context: who = `identity.definitions.controller`; where = `registered bundle and binary signature/inventory reads`; entry = `runner_validate`; recipient = `cli_caller`; report = `runner_validate, runner_registry`.

Context/dependency derivation:

- `installation.commands.validate` free.condition: `The controller loaded and locked the registry.`

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.commands.reconcile — Reconcile observations

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 164. Ancestors: `installation` → `installation.commands`.

Effective context: who = `identity.definitions.controller`; where = `registry records, launchctl print and launchd plist directories`; entry = `runner_reconcile`; recipient = `cli_caller`; report = `runner_reconcile`.

Context/dependency derivation:

- `installation.commands.reconcile` free.condition: `The registry loaded successfully.`

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.commands.remove — Remove an owned installation

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 179. Ancestors: `installation` → `installation.commands`.

Effective context: who = `identity.definitions.controller`; where = `durable cleanup transaction, launchctl bootout and plist unlink`; entry = `runner_remove`; recipient = `cli_caller, launchd`; report = `runner_remove, runner_registry`.

Context/dependency derivation:

- `installation.commands.remove` free.condition: `The requested active record or retained cleanup record exists.`

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.commands.ownership — Classify cleanup ownership

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 194. Ancestors: `installation` → `installation.commands`.

Effective context: who = `identity.definitions.controller`; where = `recorded cleanup location and current resource observations`; entry = `runner_remove, runner_reconcile`; recipient = `cli_caller`; report = `runner_remove, runner_reconcile`.

Context/dependency derivation:

- `installation.commands.ownership` free.condition: `The recorded service name, user/scope/domain and paths pass location checks.`
- `installation.commands.ownership` uses: `["installation.service.classify"]`

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.commands.ownership.disposition_support` (source_read, self): Location and resource ownership checks use the recorded path and complete associated identities.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.cleanup.retention — Retained recovery account

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 500. Ancestors: `installation` → `installation.cleanup`.

Effective context: who = `identity.definitions.controller`; where = `runner remove result after cleanup publication attempt`; entry = `runner_remove`; recipient = `report_reader`; report = `runner_remove`.

Subordinate commitment nodes: `installation.cleanup.retention.fields` (condition).

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.cleanup.retention.support` (source_read, subtree): An incomplete or unpersisted cleanup retains its recovery snapshot; warnings prevent clean retirement.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.install.state_copy — Published installation state

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 554. Ancestors: `installation` → `installation.install`.

Effective context: who = `identity.definitions.controller`; where = `runner install result projection`; entry = `runner_install`; recipient = `report_reader`; report = `runner_install`.

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.install.state_copy.support` (source_read, self): RunnerInstallData copies the returned record state.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.verify.delivery_failure — Request delivery failure

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 612. Ancestors: `installation` → `installation.verify`.

Effective context: who = `identity.definitions.controller`; where = `runner verify completion before reply interpretation`; entry = `runner_verify`; recipient = `report_reader`; report = `runner_verify`.

Context/dependency derivation:

- `installation.verify` uses: `["transport.client"]`
- `installation.verify.delivery_failure` when: `present(verify.runner_client) and present(verify.runner_client.request_delivery) and present(verify.runner_client.request_delivery.error)`

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.verify.delivery_failure.support` (source_read, self): DeliveryFailed precedes capture/reply interpretation and preserves the returned observations.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.verify.select — Select the verification operation result

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 633. Ancestors: `installation` → `installation.verify`.

Effective context: who = `identity.definitions.controller`; where = `verification operation result from its selected outcome and delivery observation`; entry = `runner_verify`; recipient = `report_reader`; report = `runner_verify`.

Context/dependency derivation:

- `installation.verify` uses: `["transport.client"]`
- `installation.verify.select` selection: `first_match`

Subordinate commitment nodes: `installation.verify.select.delivery` (outcome), `installation.verify.select.finished` (outcome), `installation.verify.select.other` (outcome).

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.verify.select.support` (source_read, self): The verification result uses delivery failure precedence and the already selected operation outcome; unsupported retained host fields do not supply a PID.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

### AR:installation.service.classify — Classify the typed service observation

Authored source: [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md) at line 759. Ancestors: `installation` → `installation.service`.

Effective context: who = `identity.definitions.controller`; where = `service observation for the selected runner record after location resolution`; entry = `runner_reconcile, runner_remove`; recipient = `report_reader`; report = `runner_reconcile, runner_remove`.

Context/dependency derivation:

- `installation.service.classify` selection: `first_match`
- `installation.service.classify` uses: `["installation.service.ownership"]`

Subordinate commitment nodes: `installation.service.classify.unknown` (outcome), `installation.service.classify.absent` (outcome), `installation.service.classify.owned` (outcome), `installation.service.classify.unowned` (outcome), `installation.service.classify.ambiguous` (outcome).

Claimed support:

- `installation.support` (check_read, subtree): Source establishes command dispatch, publication ordering, typed metadata and observational ownership gates. Read controls assert pending saves at failure boundaries, opaque metadata round trips, safe registry replacement and bounded post-bootout observation.
- `installation.service.classify.support` (source_read, self): The typed presence and observed/recorded executable paths determine service ownership; plist ownership is independent.
- `installation.dynamic_support` (source_read, subtree): The authored reconcile and cleanup-observation field sets match these explicit JSON producers, including location-error variants, conditional omission and null candidate observations.

## Appendix 2 — surface and field coverage register

Each row identifies a subject path and all directly owned fields (full field ID is subject ID plus the displayed suffix). Fields nested below another node remain in the rule register or the authored source. Non-controller producer subjects were included because they constrain what the controller may preserve, join or infer; their inclusion does not assign production to the controller. This is a coverage index, not a second field dictionary.

### identity — [docs/contract/00-identity.surface.md](../../docs/contract/00-identity.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `identity.public` | No direct field nodes; prose, definitions or rules. |
| `identity.surfaces` | No direct field nodes; prose, definitions or rules. |
| `identity.other` | No direct field nodes; prose, definitions or rules. |
| `identity.definitions` | No direct field nodes; prose, definitions or rules. |
| `identity.build` | `contract`, `version`, `number`, `describe`, `commit` |
| `identity.producer` | `contract`, `describe`, `commit` |
| `identity.version` | `contract` |

### request — [docs/contract/10-request.surface.md](../../docs/contract/10-request.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `request.specimen` | `contract`, `specimen_id`, `run_kind`, `policy`, `probe_plan`, `phases`, `actors`, `_test_overrides` |
| `request.options` | `runner`, `runner_id`, `runner_service`, `required_entitlements`, `runner_mode` |
| `request.selector` | `id`, `service`, `required_entitlements`, `mode` |
| `request.overrides` | `worker_executable_path`, `worker_timeout_ms`, `actor_equipment_executable_paths`, `validator_executable_path`, `validator_total_timeout_ms`, `validator_io_timeout_ms`, `worker_post_apply_hang_ms`, `worker_post_apply_kill_signal`, `worker_pre_ready_hang_ms`, `worker_kill_before_publish_slot` |

### policy — [docs/contract/11-policy.surface.md](../../docs/contract/11-policy.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `policy.spec` | `format`, `sbpl_source`, `params`, `capture_compiled_profile`, `capture_nonce`, `augments` |
| `policy.augments` | No direct field nodes; prose, definitions or rules. |
| `policy.helper_request` | `policy` |
| `policy.helper_policy` | `format`, `sbpl_source`, `params` |
| `policy.check_data` | `policy_format`, `policy_sha256`, `macos_build_version`, `params_present`, `params_count`, `compile`, `import_inventory` |
| `policy.compile` | `stage`, `ok`, `error` |
| `policy.imports` | `records`, `truncated`, `cycle`, `policy_closure_sha256` |
| `policy.fallback` | `status`, `tool_exit_code`, `envelope`, `stdout_raw`, `stdout_parse_error`, `stdout_truncated`, `stdout_capture_error`, `stdout_bytes_received`, `stdout_bytes_retained`, `stderr_bytes_received`, `stderr_bytes_retained`, `capture_limit_bytes`, `stderr`, `stderr_truncated` |
| `policy.actor_check` | `actor_id`, `policy_check` |

### probes — [docs/contract/12-probes.surface.md](../../docs/contract/12-probes.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `probes.step` | `step_id`, `sandbox_check`, `attempt` |
| `probes.query` | `operation`, `filter` |
| `probes.filter` | `kind`, `value` |
| `probes.attempt` | `kind`, `action`, `target`, `args` |

### actors — [docs/contract/13-actors.surface.md](../../docs/contract/13-actors.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `actors.actor` | `actor_id`, `sandbox`, `equipment`, `required_entitlements` |
| `actors.sandbox` | `mode`, `policy` |
| `actors.phase` | `phase_id`, `actor_id`, `actions`, `after_termination` |
| `actors.after_termination` | `actor_id` |
| `actors.action` | No direct field nodes; prose, definitions or rules. |

### extensions — [docs/contract/14-extensions.surface.md](../../docs/contract/14-extensions.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `extensions.action` | `step_id`, `extension` |
| `extensions.operation` | `operation`, `token_ref`, `handle_ref`, `family`, `target`, `authority`, `recipient`, `delivery_ref` |
| `extensions.custody` | No direct field nodes; prose, definitions or rules. |
| `extensions.examples` | No direct field nodes; prose, definitions or rules. |
| `extensions.event` | `phase_id`, `step_id`, `operation`, `token_ref`, `handle_ref`, `call_boundary_observed`, `result_published`, `status`, `native_result`, `errno`, `unavailable_reason`, `lifecycle`, `actor_id`, `family`, `target`, `extension_class`, `flags`, `delivery_ref`, `native_nonnull`, `token_length` |
| `extensions.transfer` | `phase_id`, `step_id`, `source_actor_id`, `recipient_actor_id`, `token_ref`, `delivery_ref`, `request_published`, `custody_status`, `copy_status`, `equality`, `recipient_acknowledged`, `source_acknowledged`, `status`, `lifecycle`, `recipient_wait` |
| `extensions.resources` | `tokens`, `deliveries`, `handles` |
| `extensions.token` | `token_ref`, `actor_id`, `step_id`, `family`, `status`, `token_length`, `last_use_step_id` |
| `extensions.delivery` | `delivery_ref`, `token_ref`, `source_actor_id`, `recipient_actor_id`, `step_id`, `status`, `delivered_length`, `equality`, `last_use_step_id` |
| `extensions.handle` | `handle_ref`, `delivery_ref`, `actor_id`, `step_id`, `status`, `native_handle`, `raw_equal_handles`, `release_step_id`, `release_attempted` |

### refusals — [docs/contract/15-refusals.surface.md](../../docs/contract/15-refusals.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `refusals.request` | `code`, `path`, `expected_contract` |
| `refusals.controller` | `code`, `path`, `expected_contract` |
| `refusals.projection` | No direct field nodes; prose, definitions or rules. |
| `refusals.admission` | `origin`, `field`, `actual`, `maximum`, `unit`, `step_id`, `step_index`, `parameter_key`, `index` |
| `refusals.examples` | No direct field nodes; prose, definitions or rules. |
| `refusals.later` | No direct field nodes; prose, definitions or rules. |

### transport — [docs/contract/20-transport.surface.md](../../docs/contract/20-transport.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `transport.authorization` | No direct field nodes; prose, definitions or rules. |
| `transport.delivery` | No direct field nodes; prose, definitions or rules. |
| `transport.reservation` | `contract`, `attempt_id`, `lease_ms` |
| `transport.control` | `contract`, `status`, `attempt_id`, `host_pid`, `host_instance`, `reservation_id`, `lease_ms`, `reason` |
| `transport.capture` | `kind`, `contract`, `client_pid`, `clock`, `clock_available`, `started_continuous_ns`, `deadline_continuous_ns`, `ended_continuous_ns`, `timeout_ms`, `attempts`, `acquisition_stop`, `submission`, `terminal`, `error`, `runner_reply`, `submission_refusal` |
| `transport.acquisition` | `ordinal`, `attempt_id`, `started_elapsed_ms`, `ended_elapsed_ms`, `outcome`, `control`, `error` |
| `transport.control_observation` | `bytes_received`, `sha256`, `status`, `host_pid`, `host_instance`, `lease_ms`, `reason` |
| `transport.invocation` | `state`, `invoked_elapsed_ms` |
| `transport.retained_reply` | `bytes_received`, `bytes_retained`, `truncated`, `data_base64` |
| `transport.error` | `stage`, `reason`, `domain`, `code`, `message`, `domain_truncated`, `message_truncated` |
| `transport.client` | `argv`, `started_at_unix_ms`, `ended_at_unix_ms`, `exit_code`, `request_delivery`, `transport`, `transport_admission`, `transport_error`, `submission`, `runner_reply_error`, `stdout_parse_error`, `stdout_truncated`, `stdout_capture_error`, `stdout_bytes_received`, `stdout_bytes_retained`, `stderr_bytes_received`, `stderr_bytes_retained`, `capture_limit_bytes`, `stderr`, `stderr_truncated` |
| `transport.request_delivery` | `bytes_written`, `error` |
| `transport.transport_value` | No direct field nodes; prose, definitions or rules. |
| `transport.rejected` | `format`, `data_base64` |

### wire — [docs/contract/21-wire.surface.md](../../docs/contract/21-wire.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `wire.frame` | No direct field nodes; prose, definitions or rules. |
| `wire.validator` | No direct field nodes; prose, definitions or rules. |
| `wire.standalone` | No direct field nodes; prose, definitions or rules. |
| `wire.standalone_status` | `kind`, `schema_version`, `pid`, `error` |
| `wire.standalone_result` | `kind`, `schema_version`, `pid`, `operation`, `filter_type`, `filter_type_id`, `filter_value`, `extra`, `rc`, `errno`, `allowed`, `denied` |
| `wire.standalone_error` | `kind`, `schema_version`, `error`, `pid`, `filter` |

### reply — [docs/contract/30-reply.surface.md](../../docs/contract/30-reply.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `reply.record` | `producer`, `specimen_id`, `run_kind`, `rc`, `normalized_outcome`, `error`, `pid`, `bundle_id`, `policy_format`, `policy_sha256`, `compiled_profile`, `sandboxed_after_apply`, `steps`, `runner_subprocess`, `admission_failure`, `request_failure`, `phases`, `extension_events`, `test_overrides`, `reporting_failure`, `execution_form`, `actors`, `transfers`, `resources`, `schedule`, `preparation_failure`, `equipment_inventory`, `equipment_bindings`, `equipment_entitlements`, `authority_setup` |
| `reply.failure` | `origin`, `diagnostic`, `original_rc`, `original_normalized_outcome`, `original_error`, `evidence_retained` |

### steps — [docs/contract/31-steps.surface.md](../../docs/contract/31-steps.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `steps.step` | `phase_id`, `step_id`, `sandbox_check`, `attempt`, `comparison`, `actor_id` |
| `steps.query` | `result_source`, `native_rc`, `missing_reason`, `rc`, `outcome`, `pid`, `operation`, `filter_kind`, `filter_value`, `filter_type_id`, `errno`, `error`, `path_diagnostics` |
| `steps.verdict` | `step_id`, `operation`, `filter_type`, `filter_type_id`, `filter_value`, `rc`, `errno`, `outcome`, `error`, `raw_line` |
| `steps.attempt` | `requested_kind`, `requested_action`, `result_source`, `missing_reason`, `lifecycle`, `fresh_read`, `fresh_write`, `exec_observation`, `rc`, `errno`, `outcome`, `error`, `requested_path`, `path_diagnostics`, `observed_path`, `child_pid`, `child_exit_code`, `child_term_signal`, `stdout`, `stderr` |
| `steps.comparison` | `observation`, `observation_basis`, `operation_relation`, `target_relation`, `order`, `limitations` |
| `steps.ordering` | `collection_closed_before_proceed`, `proceed_set`, `proceed_observed`, `validator_disposition`, `worker_lifetime_established`, `protocol_violations` |
| `steps.query_paths` | `observer`, `stage`, `input`, `realpath_resolved`, `firmlink_resolved`, `same_as_input` |
| `steps.attempt_paths` | `observer`, `stage`, `input`, `realpath_resolved`, `parent_realpath_resolved`, `same_as_input` |
| `steps.identity` | `device`, `inode`, `mode`, `uid`, `gid` |
| `steps.stat` | `rc`, `errno`, `identity`, `size` |
| `steps.fresh_read` | `open_rc`, `open_errno`, `read_rc`, `read_errno`, `stat_rc`, `stat_errno`, `identity`, `close_rc`, `close_errno`, `content_hex` |
| `steps.fresh_write` | `open_rc`, `open_errno`, `truncate_rc`, `truncate_errno`, `write_rc`, `write_errno`, `close_rc`, `close_errno`, `preopen_stat`, `opened_stat`, `truncated_stat`, `written_stat` |
| `steps.assessment` | No direct field nodes; prose, definitions or rules. |

### lifecycle — [docs/contract/32-lifecycle.surface.md](../../docs/contract/32-lifecycle.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `lifecycle.worker` | `pid`, `term_signal`, `exit_code`, `partial_steps`, `worker_evidence`, `policy_transfer_timeout`, `policy_transfer_error`, `ready_byte_received`, `done_observed`, `poll_stop_reason`, `exit_requested`, `termination_request`, `reaped`, `wait_errors`, `cleanup_trigger`, `grace_end`, `collection_basis`, `ready_wait`, `sentinel_wait`, `exit_grace_wait`, `disposition` |
| `lifecycle.host_wait` | `budget_ms`, `elapsed_ms`, `stop`, `excluded_ms`, `native_errno`, `clock_fault` |
| `lifecycle.termination` | `signal`, `rc`, `errno` |
| `lifecycle.wait_error` | `stage`, `rc`, `errno` |
| `lifecycle.transfer_timeout` | `budget_ms`, `elapsed_ms`, `bytes_written`, `bytes_expected` |
| `lifecycle.transfer_error` | `errno`, `bytes_written`, `bytes_expected` |
| `lifecycle.worker_evidence` | `abi_identity`, `progress`, `failure_publication`, `failure_state`, `failure`, `readiness`, `diagnostic`, `policy_read` |
| `lifecycle.progress` | `raw`, `operation`, `stage`, `index` |
| `lifecycle.failure` | `operation`, `code`, `native_kind`, `native_result`, `errno`, `index`, `detail` |
| `lifecycle.readiness` | `rc`, `errno` |
| `lifecycle.diagnostic` | `state`, `status`, `length`, `text` |
| `lifecycle.policy_read` | `bytes_expected`, `bytes_received` |
| `lifecycle.disposition` | `questions`, `steps`, `issues` |
| `lifecycle.claim` | `state`, `answer`, `value`, `reason`, `issue`, `basis` |
| `lifecycle.claim_value` | No direct field nodes; prose, definitions or rules. |
| `lifecycle.issue` | `kind`, `rule`, `question`, `step_index`, `observations`, `detail` |
| `lifecycle.run_questions` | `final_status`, `stop_reason`, `cleanup_trigger`, `grace_end`, `kill_request_and_result`, `collection_basis`, `progress_association` |
| `lifecycle.step` | `index`, `step_id`, `slot`, `attempt_support`, `questions` |
| `lifecycle.step_questions` | `step_boundary_reached`, `step_result_published`, `step_requested_operation_applicability` |
| `lifecycle.attempt` | `summary`, `boundary`, `result` |
| `lifecycle.owned_reap` | `pid`, `native_rc`, `raw_status`, `stage`, `observed_ns`, `ownership_unbroken`, `departure_requested`, `capture_ordinal` |
| `lifecycle.reap_reference` | `capture_ordinal` |
| `lifecycle.spawn_failure` | `origin`, `operation`, `executable_path`, `return_code`, `diagnostic` |
| `lifecycle.validator` | `phase_id`, `ordinal`, `pid`, `term_signal`, `exit_code`, `reaped`, `termination_request`, `wait_errors`, `read_error`, `stdout_collection_stop`, `stdout_bytes_received`, `probe_bytes_written`, `probe_bytes_expected`, `io_error`, `decode_fault`, `records`, `expected_step_ids`, `association_issues`, `exit_grace_wait` |
| `lifecycle.decode_fault` | `origin`, `kind`, `message`, `byte_offset`, `frame_bytes`, `retained_bytes`, `context_b64`, `context_truncated` |
| `lifecycle.association_issue` | `origin`, `kind`, `step_id`, `count` |
| `lifecycle.exec` | `collection`, `cleanup`, `reap` |
| `lifecycle.exec_collection` | `stop_reason`, `leader_exit_observed`, `stdout`, `stderr`, `deadline_kind`, `waitid_errno`, `poll_errno`, `clock_fault` |
| `lifecycle.exec_stream` | `eof`, `read_errno`, `poll_revents` |
| `lifecycle.exec_cleanup` | `state`, `group_request`, `leader_fallback` |
| `lifecycle.exec_signal` | `target`, `signal`, `rc`, `errno` |
| `lifecycle.exec_reap` | `stop_reason`, `last_wait`, `clock_fault` |
| `lifecycle.exec_wait` | `rc`, `errno`, `status` |

### actor_evidence — [docs/contract/33-actor_evidence.surface.md](../../docs/contract/33-actor_evidence.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `actor_evidence.actor` | `actor_id`, `index`, `mode`, `policy_format`, `policy_sha256`, `policy_received_sha256`, `setup_status`, `applied`, `application_count`, `launch`, `subprocess`, `compiled_profile`, `visits`, `equipment`, `application`, `owned_reap` |
| `actor_evidence.launch` | `pid`, `parent_pid`, `environment`, `standard_streams`, `inherited_descriptors` |
| `actor_evidence.application` | `state`, `basis` |
| `actor_evidence.phase` | `phase_id`, `ordinal`, `action_ids`, `arrival_observed`, `completion_observed`, `collection_status`, `ordering`, `validator_subprocess`, `validator_spawn_failure`, `actor_id`, `actor_visit`, `visit_timing`, `termination_gate`, `activation_observation` |
| `actor_evidence.activation` | `capture_ordinal`, `observed_ns` |
| `actor_evidence.timing` | `activation_to_arrival_ms`, `collection_ms`, `arrival_to_release_ms`, `release_to_completion_ms` |
| `actor_evidence.schedule` | `setup_wait`, `execution_wait`, `lifetime_budget_ms`, `collection_budget_ms`, `cancelled` |
| `actor_evidence.gate` | `source_actor_id`, `source_final_phase_id`, `condition`, `outcome`, `wait`, `observation`, `activation_eligible`, `capture_ordinal` |
| `actor_evidence.owned_endings` | No direct field nodes; prose, definitions or rules. |

### equipment — [docs/contract/34-equipment.surface.md](../../docs/contract/34-equipment.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `equipment.inventory` | `path`, `status`, `sha256`, `schema_version`, `worker_identity`, `unsigned_worker_sha256`, `seal_osstatus`, `reason`, `error` |
| `equipment.manifest` | `schema_version`, `contract`, `worker_identity`, `unsigned_worker_sha256`, `workers` |
| `equipment.manifest_worker` | `role`, `relative_path`, `sha256`, `cdhash`, `identifier`, `team_id`, `entitlements_xml` |
| `equipment.binding` | `role`, `source`, `implementation_identity`, `relative_path`, `path`, `status`, `reason`, `expected_sha256`, `expected_cdhash`, `sha256`, `cdhash`, `identifier`, `team_id`, `entitlements_ref`, `signature_osstatus`, `entitlements_match`, `error` |
| `equipment.entitlements` | `source`, `binding_ref`, `actor_id`, `status`, `raw_plist`, `error` |
| `equipment.error` | `operation`, `domain`, `code`, `message` |
| `equipment.actor` | `requested`, `resolved`, `binding_ref`, `required_entitlements`, `requirements_status`, `missing_requirements`, `execution` |
| `equipment.execution` | `status`, `pid`, `parent_pid`, `observed_at_monotonic_ns`, `path`, `cdhash`, `identifier`, `team_id`, `entitlements_ref`, `native_observations`, `reason`, `eligible` |
| `equipment.native_observation` | `operation`, `attempted`, `osstatus` |
| `equipment.preparation_failure` | `stage`, `code`, `actor_id`, `binding_ref`, `reason` |
| `equipment.authority_setup` | `host`, `workers` |
| `equipment.authority_host` | `run`, `regions`, `custody` |
| `equipment.authority_scope` | `actor_id`, `actor_index`, `token_ref`, `token_index`, `required`, `publication`, `disposition`, `primary_operation`, `operations`, `ownership`, `cleanup_reference`, `integrity_errors` |
| `equipment.authority_operation` | `slot`, `operation`, `role`, `state`, `native_kind`, `native_rc`, `errno`, `detail`, `value` |
| `equipment.cleanup_reference` | `kind`, `name`, `host_pid`, `session_nonce`, `recovery_state` |

### profile — [docs/contract/35-profile.surface.md](../../docs/contract/35-profile.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `profile.receipt` | `status`, `reason`, `worker_pid`, `producer`, `capture_stage`, `request_nonce`, `profile_type`, `bytecode_length`, `bytecode_sha256`, `bytecode_b64`, `source_sha256`, `source_length`, `params_sha256`, `parameter_count` |

### envelope — [docs/contract/40-envelope.surface.md](../../docs/contract/40-envelope.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `envelope.run` | `build`, `data`, `generated_at_unix_ms`, `kind`, `result` |
| `envelope.helper` | `build`, `data`, `generated_at_unix_ms`, `kind`, `result` |
| `envelope.result` | `ok`, `rc`, `exit_code`, `normalized_outcome`, `errno`, `error`, `stderr`, `stdout` |
| `envelope.data` | `runner_sandbox_diagnostics`, `specimen`, `policy_check`, `actor_policy_checks`, `timeout_ms`, `runner_client`, `runner_result`, `request_failure` |

### diagnostics — [docs/contract/41-diagnostics.surface.md](../../docs/contract/41-diagnostics.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `diagnostics.execution` | `process_disposition`, `termination_cause`, `stop_reason`, `disposition_integrity`, `disposition_issues`, `actors` |
| `diagnostics.execution.ordinary` | No direct field nodes; prose, definitions or rules. |
| `diagnostics.actor` | `actor_id`, `process_disposition`, `termination_cause`, `stop_reason`, `disposition_integrity`, `disposition_issues` |
| `diagnostics.actor.projection` | No direct field nodes; prose, definitions or rules. |
| `diagnostics.issue` | `kind`, `detail`, `subject_path`, `rule`, `question`, `step_index`, `observations` |

### dossier — [docs/contract/42-dossier.surface.md](../../docs/contract/42-dossier.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `dossier.collection` | No direct field nodes; prose, definitions or rules. |
| `dossier.specimen` | `request_path`, `policy`, `host`, `runner_provenance`, `app_provenance`, `binaries`, `actors` |
| `dossier.actor` | `actor_id`, `mode`, `policy` |
| `dossier.policy` | `augmentation`, `imports` |
| `dossier.augmentation` | `status`, `applied`, `original_sha256`, `applied_sha256`, `error` |
| `dossier.imports` | `status`, `closure_sha256`, `records`, `cycle`, `exceeded`, `failure` |
| `dossier.import_record` | `name`, `resolved_path`, `sha256`, `size_bytes`, `mtime_unix`, `error` |
| `dossier.host` | `macos_version`, `macos_build`, `kernel_release`, `arch` |
| `dossier.app` | `evidence_manifest_path`, `evidence_verify` |
| `dossier.binaries` | `service`, `worker`, `validator`, `unentitled_worker` |
| `dossier.binary` | `path`, `actual_sha256`, `baseline_sha256`, `verification`, `reason` |
| `dossier.runner` | `runner_kind`, `runner_registry_id`, `runner_service_name`, `runner_bundle_id`, `runner_bundle_path`, `runner_executable_path`, `runner_signature`, `runner_entitlements`, `runner_worker_signature`, `runner_worker_entitlements`, `runner_validator_signature`, `runner_validator_entitlements`, `runner_unentitled_worker_signature`, `runner_unentitled_worker_entitlements` |
| `dossier.verification` | `ok`, `checked`, `mismatches`, `manifest_path`, `schema_version`, `notes` |
| `dossier.mismatch` | `id`, `rel_path`, `expected_sha256`, `actual_sha256`, `error` |

### installation — [docs/contract/50-installation.surface.md](../../docs/contract/50-installation.surface.md)

| Exact subject | Direct field suffixes |
| --- | --- |
| `installation.commands` | No direct field nodes; prose, definitions or rules. |
| `installation.registry` | `schema_version`, `runners`, `pending_cleanup` |
| `installation.runner` | `state`, `ownership`, `id`, `service_name`, `bundle_path`, `executable_path`, `bundle_id`, `scope`, `contract`, `signature`, `entitlements`, `installed_at_unix_ms`, `kind`, `worker_signature`, `worker_entitlements`, `unentitled_worker_signature`, `unentitled_worker_entitlements`, `unentitled_worker_sha256`, `worker_equipment_inventory`, `source_worker_equipment_inventory`, `validator_signature`, `validator_entitlements`, `issuer_signature`, `issuer_entitlements` |
| `installation.ownership` | `plist_path`, `launchd_domain`, `owner_uid`, `plist_sha256` |
| `installation.signature` | `team_id`, `identity`, `cdhash`, `valid`, `adhoc` |
| `installation.entitlements` | `raw_plist`, `keys`, `granted`, `error` |
| `installation.pending_cleanup` | `runner`, `cleanup_started_at_unix_ms`, `observations` |
| `installation.cleanup` | `runner_id`, `service_name`, `plist_path`, `booted_out`, `plist_removed`, `cleanup_retained`, `retained_record`, `warnings` |
| `installation.install` | `state`, `loaded`, `runner`, `plist_path`, `bootstrapped` |
| `installation.verify` | `runner_client`, `runner_result`, `state`, `runner_id`, `service_name`, `runner_pid`, `normalized_outcome` |
| `installation.validate` | `updated`, `missing`, `invalid`, `failures` |
| `installation.failure` | `runner_id`, `service_name`, `binary`, `error` |
| `installation.not_found` | `requested_id`, `requested_service_name` |
| `installation.service` | `presence`, `executable_path`, `error` |
| `installation.plist` | `presence`, `config`, `sha256`, `owner_uid`, `regular`, `error` |
| `installation.reconcile` | `registry_path`, `records`, `candidates`, `inspection_errors` |
| `installation.reconcile_record` | `recorded_state`, `runner`, `service`, `plist`, `plist_path`, `launchd_domain`, `service_ownership`, `plist_ownership`, `ownership`, `error` |
| `installation.candidate` | `recorded_state`, `scope`, `service_name`, `executable_path`, `plist_path`, `service`, `plist`, `ownership` |
| `installation.inspection_error` | `path`, `presence`, `error` |
| `installation.cleanup_observation` | `phase`, `service`, `plist`, `service_ownership`, `plist_ownership`, `teardown_wait` |
| `installation.cleanup_wait` | `reads`, `waited_ms`, `poll_interval_ms`, `budget_ms` |

## Final coverage limit

The appendices preserve exact navigation and inherited context; they do not execute predicates or prove their realization. The consequential unresolved questions remain Q2–Q5 and Q8–Q10 above. Original-request association, publication completion, withholding dependency and current selection authority need cross-examination against the independent implementation and boundary reports before any public change is accepted.
