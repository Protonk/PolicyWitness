# Contract coverage map

Stage-one reconciliation, 2026-11-10. This is the input-preservation map for
step 1 of [the staging plan](../../docs/CONTRACT-STAGING-PLAN.md), before the
structured contract replaces the current text. It inventories meanings to
carry, corrections to make, and questions to keep visible. A destination here
is a drafting assignment, not a decision to change product behavior.

The inventory began at `8dfb11522447fc7cf3d9d1ef8c574f45f372140a`.
The files read had these Git object hashes:

| Input | Object |
| --- | --- |
| `docs/CONTRACT.md` | `d1ff8c542aa034daed5bd4aea848c3243abfaa1a` |
| `docs/PolicyWitness.md` | `bd3e5e5aeeb6d1dbc693bb8e1b17897edd31aafc` |
| `docs/contract_surfaces.json` | `b5a07f358080c3df6f8227754dfc5010e7c6d8f4` |

`C` and `G` below mean those contract and guide versions and their line
numbers. The report's `L-01`–`L-48` verdicts use the older 441-line contract;
their receipt verdict is superseded as described below. Region names and row
IDs are the durable lookup keys when line numbers move. Sibling records are
named as paths, not linked from this record.

## Reading and evidence grades

| Grade | What this map establishes |
| --- | --- |
| D | The named document passage was read. Its meaning is inventoried; implementation support still needs an owner. |
| I | A prior examination supplies a source/check trace. This pass read the examination, not every underlying source or check. Preserve its finer evidence grade when attaching an owner; I is not execution credit. |
| S | This pass read the specific implementation cited in the source-confirmed corrections table. It supports the narrow assertion stated there. |
| T | This pass read a check's assertions and execution context without executing it. The R-06 constructed orchestration check added during this work is the sole T entry. |
| E | Execution observed in this pass. There are no E entries: no tests, builds, releases or experiments were run. |

All guide rows are D unless marked S or I. A guide statement alone is not an
established implementation promise. All current-contract rows are D+I: their
existing atomic claims and report verdicts are the inherited support. The map
does not upgrade suite names to checks, constructed records to product runs,
or old release summaries to verified receipts. Retained test output, where
the earlier records cite it, is gitignored and available only in the local
checkout; this pass did not reopen that evidence.

Read in this pass: `records/AGENTS.md`; the full staging plan and current
contract; the manifest; all 17 unique guide regions listed below; the full
shared extension source and the two copied failure-propagation passages;
the first-reader report's scope, all line verdicts, findings, sound statements,
unrun experiments and limits; adjudication Parts 1–4; all 15 follow-up answers
in `FRESH-ENCOUNTER-ADDENDA.md`; the isolated baseline's reading conditions
and complete U1–U61 uncertainty register; the ledger's strain and decision
registers and relevant stage notes; maintainer notes; the structure proposal's
model and surface outline; and `validators/DEFINITIONS-AND-SCOPES.md`.

The claim index was read for coverage and ownership counts. Its 332 atomic
claims across `claims/U01.md`–`claims/U20.md` are inherited, not individually
re-audited here. The report machinery chapters, original fresh-encounter
journal, complete isolated narrative and carried-term table, and every
addendum close-out paragraph were not independently reread. Their concerns
are represented through the complete adjudication and uncertainty registers;
this is not a claim of a second full source audit. Source/check attachment to
each new structured rule remains drafting work. Any uncovered meaning found
there must extend this map rather than silently disappear.

## Destination vocabulary and ownership

The 19 surface names are provisional until stage one's surface-name decision.
Definitions orient the product, actors, boundaries and records before rules.
The running operation separates input preparation, delivery, host reporting
and controller assessment. Runner management and version reporting are their
own operations. Internal generation/maintenance instructions go to
`docs/contract/README.md` or `docs/contract/AGENTS.md`; workflow examples stay
in the guide with contract definitions linked nearby.

| Proposed surface | Meaning assigned here |
| --- | --- |
| identity | Public identity forms, locations, exact-match boundaries and what equality establishes; version/build reporting. |
| request | Accepted specimen forms, defaults, selectors, normalization and admission ordering. |
| policy | Held source, params, augments, compiler/import behavior and standalone/fallback checks. |
| probes | Accepted queries, attempts and native operations, including prediction exclusions. |
| actors | Actor declarations, visits, phase scheduling and fresh-process responsibility. |
| envelope | Controller/helper records, top-level outcomes and process exit classification. |
| dossier | Controller observations of held input, imports, host and selected artifacts. |
| steps | Query/attempt records, relations and the evidentiary meaning of observations. |
| lifecycle | Worker/validator/child progress, cleanup, reap and application assessments. |
| equipment | Selection, sealed inventories, static/live association and launch apparatus. |
| profile | Compiled-profile production, fields, host gates and reader assessments. |
| transport | Reservation, request delivery, client capture, invocation knowledge and retained bytes. |
| refusals | Structured refusal records, ordering, paths, bounds and outcomes. |
| installation | Installation, registry, ownership, verification, removal and reconciliation. |
| extensions | Issue/transfer/consume/release actions and host/worker custody. |
| reply | Host reply structure, execution forms and publication ownership. |
| actor_evidence | Actor equipment/application/dependency records and their interpretation. |
| diagnostics | Findings, affected scopes, degraded reporting and later path observations. |
| wire | Typed frame/primitive encodings, fingerprints, bounds and independent admission. |

Every row below has a destination or an explicit question. `R-nn` refers to
the existing strain register in `CONTRACT-LEDGER.md`; the user makes continued
ledger maintenance optional. New `Q-nn` rows here are explicit dispositions,
not hidden additions to that ledger. `keep` preserves meaning subject to the
stated evidence grade. `correct` changes the account to current behavior.
`question` retains an unresolved meaning or missing evidence for stage two.

## Existing contract: all line verdicts

The existing `CONTRACT-CLAIMS.md` index remains the atomic inventory for these
passages. The following rows reconcile every `L` verdict rather than copying
all claims. The A references cover every adjudicated journal entry A-01–A-52.
Read with the guide inventory: a short C sentence is not the complete scope
of a surface whose guide regions carry more commitments.

| Row / old location / prior examination | Meaning and disposition | Destination / strain |
| --- | --- | --- |
| C01 · C1–15 · L-01, A-01 | Define PolicyWitness, specimen, host reply, capture and public identity; name each exact-match boundary. Replace the global bypass/negotiation denials with actual operations and their conditions. | definitions, identity, request, transport; R-21–R-24; Q-01 |
| C02 · C8–15 · L-02, A-02 | Preserve release/development forms and derivation scope; distinguish public, wire and worker identifiers. Two annotated tags and explicit build-environment identity need their actual handling stated. | identity; R-08, R-24; Q-02 |
| C03 · C17–20 · L-03, A-03 | Preserve reported identity locations and provenance fields without treating matching strings as package equality or authentication. | identity, envelope, installation; R-22; Q-01 |
| C04 · C17–20 · L-04, A-03 | Reuse is an explicit review/reassertion decision; stamps assist it. No automatic rewrite of saved specimens is promised. Development-assertion comparison baseline remains a question. | identity; maintenance; R-25; Q-03 |
| C05 · C22–56 · L-05, A-04 | Make rendered surface membership visible; hash public definitions/examples/shapes and distinguish declared changes from behavioral proof. | identity and generated surface table; R-26–R-28 |
| C06 · C32–50 · L-06, A-04 | Preserve 0.3.6 stamp/shape history, current unreleased profile change and later 0.3.7/0.3.8 snapshots. Removed surfaces retain history rows. | identity; maintenance; staging history obligation |
| C07 · C52–56 · L-07, A-05 | Ordinary checks without history retain their narrower guarantee. Release regeneration without history is a known defect; repair separately rather than describing it as acceptable release behavior. | maintenance and known gap; R-29 |
| C08 · C63–85 · L-08, A-06, A-08 | CLI parsing can fail before the request gate. Within decoded requests, exact contract admission precedes selector meaning; controller and direct-XPC responsibilities differ. | request, refusals; Q-01 |
| C09 · C65–75 · L-09, A-07 | Preserve closed fields and omission/null rules. Include the inapplicable-extension-operand null exception; the old list is incomplete. | request, extensions; Q-04 |
| C10 · C77–85 · L-10, A-08 | Selection precedence, entitlement demand, augment splicing and controller stripping are operations on held input. Direct XPC rejects selector fields; unresolved augments are refused there. | request, policy, equipment; Q-01 |
| C11 · C87–98 · L-11, A-09 | Preserve attempt/filter pairs, plan/phase uniqueness, nonce and action constraints. Structural plan decoding may precede capacity; decoder/capacity/meaning is not an unconditional total order. | request, probes, refusals; Q-04 |
| C12 · C100–106 · L-12, A-10 | Keep public exact assertion behavior; move maintainer reassertion and shape-refresh duties to maintenance. Remove historical counter/compatibility denials. | identity; maintenance; R-27, R-30, R-32 |
| C13 · C108–114 · L-13, A-11 | Preserve each capacity's subject, unit, bound and refusal consequence; requests are refused rather than truncated. Name the runtime limits source. | request, refusals, wire; Q-05 |
| C14 · C116–124 · L-14, A-12 | Separate authored request decoder agreement and generated response structure; retain request grammar/examples as inputs, move maintenance instructions. | request, wire; maintenance; R-32 |
| C15 · C116–124 · L-15, A-12 | Keep shared admission-corpus examples with individual evidence grades: injected Swift dependencies and actual CLI exercise support different claims. | request examples/owners; Q-06 |
| C16 · C129 · L-16, A-13 | Held source/params and controller normalization define run input; import observations and fallback read their own stated boundaries. | policy, dossier; Q-07 |
| C17 · C135 · L-17, A-14 | Preserve closed attempt vocabulary, query availability exclusions and separate observation/effect meaning; policy prediction has a particular query and time. | probes, steps; Q-08 |
| C18 · C141 · L-18, A-15 | Phases also apply to single-worker requests. Actors each get fresh workers; numeric PID reuse is compatible with distinct processes. | actors, reply; R-10 |
| C19 · C147 · L-19, A-16 | Independent producer admission and bounded raw-byte retention; distinguish exact host frames, parsed helper records and lossy rejected diagnostics. | envelope, transport, wire; Q-09 |
| C20 · C153 · L-20, A-17 | Dossier observes held parsed input and separate artifact/import reads. Fallback uses the held request after `xpc_error`; byte equality with the original file is not the input contract. | dossier, policy; Q-07 |
| C21 · C159 · L-21, A-18 | Define the full `query_first` chain and each comparison relation. Semantic findings preserve raw evidence and withhold conclusions at a stated scope. | steps, diagnostics; R-19, R-34, R-38 |
| C22 · C165 · L-22, A-19 | Preserve raw lifecycle facts and distinguish host assessments from controller projection, including unresolved/inapplicable to unconfirmed mapping. | lifecycle, diagnostics; R-07, R-34 |
| C23 · C171 · L-23, A-20 | Sealed inventory, selected equipment and observed actor binding are distinct evidence. Current install/binder checks have different contexts. | equipment; R-09, R-12, R-13 |
| C24 · C173–181 · L-24, A-21 | Define actor-owned records/slots and publication conditions; remove obsolete declaration-reply wording. “Acquired decision” meaning stays unresolved until replaced by a supported rule. | reply, actor_evidence; R-10, R-11 |
| C25 · C183–193 · L-25, A-22, A-23 | Preserve zero-based actor binding, per-binary static inventory, boolean-true entitlement requirements and live read-back. Overrides and runtime inspection failure need separate treatment. Reserve-geometry reference needs correction. | equipment, actor_evidence; R-09, R-12, R-13; Q-05 |
| C26 · C195–202 · L-26, A-23, A-24 | Preparation failure can retain declarations and failure evidence. Define complete positive observation partition and both preparation-failure/degraded scopes before choosing validator strength. | reply, actor_evidence, diagnostics; R-14, R-36 |
| C27 · C204–210 · L-27, A-25 | Define four application states and all 11 state/basis pairs, producer evidence and reader applicability separately. Preserve source/test coverage gaps for the signed cases. | lifecycle, actor_evidence; R-15; Q-10 |
| C28 · C212–228 · L-28, A-26, A-27 | Gate requires earlier final scheduled visit, activation and owned natural reap before dependent activation/query release; normal or signaled natural exit can satisfy it. Define all ordinal sequences and eight outcomes. Current failed evaluated gate cancels the remaining schedule. | actors, actor_evidence, lifecycle; R-16, R-17, R-37; Q-11 |
| C29 · C230–236 · L-29, A-28 | Gate/release clock failures have different temporal scopes; later cleanup clock failure preserves already established ordering. | actor_evidence, diagnostics; R-18 |
| C30 · C243 · L-30, A-29 | Current corrected receipt text assigns request nonce/input binding to host production; reader structural/internal consistency is a separate commitment. Old blanket reader refusal is superseded, not reintroduced. | profile; R-01–R-06 |
| C31 · C249 · L-31, A-30 | Preserve reservation before invocation, independent admissions and invocation knowledge; no resubmission after invocation. Foreign-host evidence currently includes instrumented peer/client checks, not every real signed-host branch. | transport; Q-01, Q-12 |
| C32 · C255–261 · L-32, A-31, A-32 | Exact assertion refusal has precedence within its boundary; retain minimal foreign-contract/unknown-field example without obsolete schema history. Delivery failure precedence needs its constructed-record grade. | refusals, transport; Q-04, Q-06 |
| C33 · C263–265 · L-33, A-32 | `bad_request` exits 1; other run failures also exit 1. Tool failures exit 2. Preserve returned request-failure data without falsely closing its open code vocabulary. | envelope, refusals; Q-04 |
| C34 · C266–271 · L-34, A-33 | Paths use string keys and decimal index strings; `[]` is root, null is withheld, limits are eight components/63 UTF-8 bytes each; parameter-key withholding is explicit. | refusals; Q-04 |
| C35 · C273–284 · L-35, A-34 | Existing code table is selected, not exhaustive; inventory current cases and preserve open-vocabulary meaning. | refusals; Q-04 |
| C36 · C286–291 · L-36, A-35 | Decode, capacity and semantic checks have actual branch precedence. A host may have launched before request refusal; workers and validators have not. | request, refusals; Q-04 |
| C37 · C296–297 · L-37, A-36, A-37 | Signed bundle, stored registry identity and live reservation identity are separate checks. Historical registry forms remain manageable; ownership and observed absence govern removal. “Opaque” preservation needs a round-trip decision and test. | installation, transport; Q-13 |
| C38 · C300–311 · L-38, A-38 | `porcelain.json` owns typed stored response structure. Generated readers agree on that structure; handwritten primitives and tagged projections still need checks. | wire; maintenance; Q-14 |
| C39 · C313–326 · L-39, A-39 | Preserve complete frame layout, primitive widths, boolean values, all endianness and enum assignments; prose currently omits some primitives. | wire; Q-14 |
| C40 · C328–339 · L-40, A-40, A-41 | Define logical decoding budgets separately from physical allocation; each frame has admission and client retention bounds. Collection and retention differ; receiver has no independent deadline. | wire, transport; Q-05, Q-15 |
| C41 · C341–345 · L-41, A-42 | Fingerprint covers field types/order/optionality, names, variants and roots; layout comments/default annotations/location/version do not all have the same role. Equal fingerprint establishes schema compatibility at the declared boundary. | wire, identity; Q-14 |
| C42 · C347–358 · L-42, A-43 | Define byte encodings and four consequences: primitive decode, public identity admission, semantic findings, degraded reporting. Define fresh content, rejected validator records and owned endings. | wire, diagnostics, steps, lifecycle; R-19, R-36 |
| C43 · C360–377 · L-43, A-44, A-45 | Move generator, shape-refresh, history and candidate-submission instructions to maintenance. Distinguish historical captures, request templates and independently inspected candidate inputs. | maintenance; R-32; Q-06 |
| C44 · C379–390 · L-44, A-46 | Manual owning-generator invocation precedes builds; builds check stale worker identity and refuse. Correct the claim that direct builds regenerate automatically. | equipment definitions; maintenance; Q-16 |
| C45 · C392–404 · L-45, A-47 | Keep worker identity's selected inputs and meaning distinct from public contract/wire identity; source/SDK/signing facts have separate evidence. | equipment, identity; maintenance; R-08 |
| C46 · C406–414 · L-46, A-48 | State actual worker bootstrap and header-check locations, mismatch/size outcomes and publication gates. Host release writes do not all repeat every header check. | equipment, lifecycle; Q-16 |
| C47 · C416–427 · L-47, A-49, A-50 | Selected-source identity supports agreement about selected inputs, while independent checks support layout/lifecycle behavior. Explain the native helper (“shim”) by role. | equipment definitions; maintenance; Q-16 |
| C48 · C428–441 · L-48, A-51, A-52 | Shape goldens normalize declared shapes, not meaning. Candidate differences require adjudicating the changed side; preserve all five build fields and identity forms. | identity, envelope; maintenance; R-28; Q-06 |

## Manifest-listed guide regions

The manifest has 17 unique guide regions, with repeated membership in several
old surfaces. It also includes C's `transport_encoding`. All are covered here;
removing guide participation from stamping must preserve their public meaning
in the structured contract first.

| Region / G lines | Old surface membership | Coverage rows |
| --- | --- | --- |
| request_form · 169–205 | request | G01–G03 |
| actors_phases · 207–254 | actors | G04–G06 |
| actors_extensions · 256–488 | actors | G07–G19 |
| request_admission · 490–613 | request, refusals | G20–G25 |
| policy_input · 615–633 | policy | G26 |
| profile · 635–676 | profile | G27–G30 |
| policy_tools · 678–881 | policy | G31–G40 |
| probes · 883–910 | probes | G41 |
| envelope · 1206–1311 | envelope | G42–G50 |
| lifecycle · 1313–1491 | lifecycle, equipment | G51–G63 |
| transport · 1493–1572 | transport | G64–G70 |
| dossier · 1574–1653 | dossier | G71–G75 |
| equipment · 1655–1737 | equipment | G76–G81 |
| steps · 1739–2014 | steps | G82–G90 |
| refusals · 2016–2111 | refusals | G91–G97 |
| operations · 2113–2286 | probes, steps | G98–G105 |
| installation · 2341–2624 | request, installation | G106–G116 |

Three copied spans must be edited at their owners and regenerated. G364–486
comes from `docs/EXTENSIONS.md:3–125`; G1671–1705 comes from
`tests/FAILURE-PROPAGATION-CONTRACT.md:270–304`; G1866–1918 comes from that
file's lines 1398–1450. Heading nesting and relative links change in the guide.
Those origins were read; the rest of the failure-propagation document was not
audited in this pass. The eventual structured contract must own the public
meaning while shared guide explanations remain generated from their owner.

### Preparing requests and scheduling work

| Row / old location | Meaning to preserve, correction or question | Destination / disposition |
| --- | --- | --- |
| G01 · request_form | Required exact `contract`, string `specimen_id`; optional `run_kind`; ordinary policy plus exactly one non-null plan, or actor form with per-actor policy and phases; optional runner selection. Keep the minimal apply-only empty `probe_plan` example. | request; keep; C08–C11 |
| G02 · request_form | Optional null generally means absent, with explicit exceptions for equipment, required entitlements, termination dependencies, override maps and inapplicable extension operands. Correct the incomplete exception list. | request, extensions; Q-04 |
| G03 · request_form | Empty plan applies policy without probes; validator queries exist only for planned eligible queries. Replace “unsupported versions” with the exact public contract boundary. | request, identity; correct; F-19 |
| G04 · actors_phases | `probe_plan` becomes `main`; `phases` is nonempty; phase IDs and step IDs obey their declared uniqueness scopes; actions have paired query/attempt parts; empty action arrays are accepted. | request, actors; keep |
| G05 · actors_phases | Each phase closes query collection before action release; actions run in declaration order; next collection follows prior completion. One fresh worker applies policy once and remains for its phases. | actors, steps; keep; R-16 |
| G06 · actors_phases | Eight phases and 256 total steps bound the request; query budget is cumulative. Ineligible fresh paths produce unavailable predictions while attempts proceed. Validator failure can leave missing predictions; release/worker loss stops progress. | actors, probes, refusals; keep; Q-05, Q-08 |
| G07 · actors_extensions | Equipment defaults to selected, with unentitled as another role; sandbox state separately chooses apply/unapplied. Inherited restrictions persist; boolean-true required entitlements concern static and live read-back, separately from runner selection demand. | actors, equipment; keep; R-09 |
| G08 · actors_extensions | Preserve the two-actor before/during/after fresh-read example and its separate issue, access and revocation observations. Native `read_write` class may name a directory; target is an exact absolute path, flags zero. Token bytes stay in custody channels. | extensions, steps; keep example; Q-06 |
| G09 · actors_extensions | Verify both sealed worker inventories before launch; associate live code before activation; role failure does not select another worker. Runtime inspection failure cancels scheduling while earlier application remains; unavailable setup can coexist with healthy actors. | equipment, actor_evidence; R-09, R-12, R-13 |
| G10 · actors_extensions | `after_termination` requires the source's final declared visit earlier than dependent phase and owned natural reap before activation/query collection; signaled natural exit can qualify and final completion is not itself required. Failed evaluated gate currently cancels all later scheduling, not only the dependent phase. | actors, actor_evidence; correct; R-16, R-17, R-37 |
| G11 · actors_extensions | Bounded apparatus is prepared before compile/apply; unavailable private symbols produce explicit no-call records. Missing publication does not establish that policy was never applied. | equipment, extensions, lifecycle; keep |
| G12 · actors_extensions / EXTENSIONS | Preserve three-actor A→B→C redelegation with baseline reads and separate custody/delivery/consume/issue chain. Each actor has one fresh policy-bearing process; other actors park while one phase is active. | actors, extensions; keep example; Q-06 |
| G13 · actors_extensions / EXTENSIONS | Issue assigns token ref with class/authority/absolute path; transfer requires owner token, recipient and new delivery ref; consume requires recipient delivery and new handle ref; release uses the consumer's handle. Refs are specimen-local, assigned once and ordered. Distinct handles permit repeated consumption; transfer may be to multiple recipients or self; a handle is released once. | request, extensions; keep |
| G14 · actors_extensions / EXTENSIONS | Any actor participating in extension actions, including receiving, cannot run exec probes; other actors can. | request, extensions, probes; keep |
| G15 · actors_extensions / EXTENSIONS | Each action publishes one immutable slot until host copy/rejection and erasure; timeouts do not reuse slots. Host settles delivery only after recipient acknowledgement and byte comparison; consumption requires usable delivery. Preserve self-transfer race handling. | extensions, actor_evidence; keep |
| G16 · actors_extensions / EXTENSIONS | Parked recipients acknowledge delivery; consume runs in their later released phase. Host custody clears at last transfer/teardown, inbound worker bytes at last use/exit; shared host memory clears only after confirmed exit, with uncertain live ownership retained. | extensions, lifecycle; keep |
| G17 · actors_extensions / EXTENSIONS | Workers launch with empty environment, policy stdin, null standard output/error and only evidence/readiness/authority descriptors; other descriptors close. Host/worker core limits precede custody-region creation. | equipment, extensions; keep; Q-17 |
| G18 · actors_extensions / EXTENSIONS | Non-null issue result plus length records native return; issued resource requires custody; delivered requires acknowledged equal bytes. Consume result other than -1 is a candidate handle; release records its native call. Unavailable is explicit no-call, not_reached requires terminal evidence, unresolved means absent publication. Fresh access is an observation at its own time. | extensions, steps; keep |
| G19 · actors_extensions / EXTENSIONS | Source acknowledgement requires matching published answer. A query cannot reproduce class-and-path issuance authority. Preserve failure distinctions: setup failure, setup timeout followed by application, reap before another activation, bounded blocked native call, uncustodied issue, recipient refusal/timeout, and symbol absence. | extensions, lifecycle, diagnostics; keep; Q-08 |
| G20 · request_admission | Preserve absent-query/create-success example and its independent file-effect witness; a prediction can be unavailable while the attempt creates a file. | request/steps examples; keep; Q-06 |
| G21 · request_admission | Misspelled `capture_compiled_profiel` yields `bad_request`, exit 1, `unknown_field` and precise path; no worker/validator executes, though host may start. Correct spelling also requires valid nonce when enabled. Preserve target-absence observation separately from refusal classification. | refusals/profile example; keep; Q-06 |
| G22 · request_admission | Grammar, meaning, capacity and observed effect are distinct; plans are refused rather than shortened. Unknown attempt/filter refuses whole request; known unavailable query can leave attempt executable. | request, refusals, probes; keep; Q-04 |
| G23 · request_admission | Paths contain keys/index strings, `[]` root, null withheld; `error` is human text, code/path are machine data; capacity counts live in admission_failure. One problem is reported per refusal. | refusals; keep; Q-04, Q-05 |
| G24 · request_admission | `args` applies only to exec, even empty; `none` filter accepts absent/null value, other accepted filters require nonempty string; enabled capture requires 32 lowercase hexadecimal nonce. | request, probes, profile; keep |
| G25 · request_admission | Assertion comes from reported build identity and is reasserted after review. Matching contract strings admit at a boundary; observation values still depend on the run. Move manual reuse instructions to guide/maintenance. | identity; keep; R-25 |

### Policy, compilation and receipt

| Row / old location | Meaning to preserve, correction or question | Destination / disposition |
| --- | --- | --- |
| G26 · policy_input | Native compiler resolves literal imports using system search and receives params through `sandbox_set_param`; preserve string-append parameter example and distinction between source syntax and supplied values. Scope arbitrary SBPL promises to actual compiler calls. | policy; keep; Q-07 |
| G27 · profile | Capture is opt-in with fresh 32-lowercase-hex nonce. Nested receipt includes status/stage, PID, nonce, type, bytecode/source/hash/count; captured stage is `before_apply`. Keep the concrete capture request and reading path. | profile; keep; R-01–R-06 |
| G28 · profile | Worker copies from the same compiled pointer before apply; host gates publication on successful application/exit and PID, nonce, extent and input/digest consistency. Unavailable reason carries no captured bytes; absent worker may mean absent receipt. Capture unavailability and policy application are separate outcomes. | profile, lifecycle; keep; R-01–R-06 |
| G29 · profile | Source hash is UTF-8 C-string input; params hash uses LE32 count and sorted pair digests with LE32 string lengths. Private parameter copies reach compiler. NUL cannot bind a complete source string. | profile, policy; keep; Q-14 |
| G30 · profile | Request binding by the producer and consistency assessment by the reader have distinct operands. Matching retained nonce/expected object supplies a consumer comparison, not an unstated refusal obligation. Storage/privacy advice stays with capture workflow. | profile; corrected current meaning; R-01–R-06 |
| G31 · policy_tools | Standalone `sbpl-check --request` reads policy and compiles in host process without applying. Controller fallback occurs only after `xpc_error` and uses held request. Compilation status is independent of worker progress. Helper has no public-contract input gate. | policy, envelope; S for helper input/gate; Q-01, Q-07 |
| G32 · policy_tools | Check order: decode, format/source/capacity/NUL, import inventory, parameter setup, compile. Initial refusal precedes import/native work. Outcomes: bad_request, policy_too_large, setup_error, compile_error, ok; absent/empty params skip setup. | policy, refusals; keep; Q-04 |
| G33 · policy_tools | Param creation/set failures identify stage; set failure names key, not value. NULL profile or non-null compiler error fails, including profile+error. Preserve native empty diagnostic versus null, summary when NULL lacks native text, and success null error. | policy, diagnostics; keep |
| G34 · policy_tools | Helper input failure returns exit 1 with success false/compiled null; usage/read/JSON errors exit 2 on stderr without envelope. Envelope records format, source hash or null, params-present including empty map, count, OS version. | envelope, policy; S for usage/read/parse dispatch; keep |
| G35 · policy_tools | Fallback capture precedence: unavailable, capture_error (including truncation before parse), parse_error, tool_error, invalid_reply; supported helper outcomes copied with whole envelope regardless of independent child exit. | policy, transport, envelope; keep; Q-07 |
| G36 · policy_tools | NULL worker compilation produces native operation 5 and runner_failed; request source/format rejection occurs before children. Preserve OPTIONAL-unused/ROOT-required parameter example. | policy, lifecycle; keep example; Q-06 |
| G37 · policy_tools | Import inventory null on initial refusal, present even on compile error; names/resolved paths/hash/size/mtime/error, system paths then `/usr/share`, absolute names retained, `.sb` rule, recursive traversal, first cycle and diamond dedup. Empty inventory differs from null; bounds produce partial/truncated results. Closure digest includes source and sorted successful paths/hashes; errors remain visible. | policy, dossier; keep; Q-07 |
| G38 · policy_tools | Augment names are alphanumeric/underscore, read packaged resources, append in requested order with newline before each; absent/null/empty list is no-op, field stripped before invocation; nonempty source required, missing file gives unknown-augment refusal. | policy, request; S for append order/newlines; keep |
| G39 · policy_tools | Preserve augmentation record even when not requested: not_requested/applied/failed/not_applicable, hashes/list/errors. Actor policies need corresponding treatment. “Allow-only” fragment intent and SBPL last-match behavior require explicit evidence rather than assuming resolver enforces content. | policy, dossier; Q-07, Q-18 |
| G40 · policy_tools | `exec_baseline` contains unconditional process-exec*, process-fork and file-read* allowances; it can mask a file-denial observation. The macOS 14.8.3 success claim is historical evidence with environment, not a universal prerequisite set. | policy/probes definitions and guide example; Q-06, Q-18 |
| G41 · probes | Preserve paired step query/attempt, string step ID, Unicode/control-character behavior, native-string NUL refusal versus host-only labels, separate bounds, and read-hosts example. | request, probes; keep; Q-05, Q-06 |

### Reports, lifecycle and transport

| Row / old location | Meaning to preserve, correction or question | Destination / disposition |
| --- | --- | --- |
| G42 · envelope | All producer envelopes carry build version/number/describe/commit/contract; version derives from nearest tag, number from commit count; plist/report identity agrees at packaging. Define value types rather than infer them from field names. | identity, envelope; keep; Q-02 |
| G43 · envelope | Separate runner reply (steps, child, phases, policy) from outer controller result/data/specimen/client/policy-check/diagnostics/timeout and from binary client capture. | definitions, reply, envelope, transport; keep |
| G44 · envelope | Correct `pid`: ordinary host reply chooses worker PID when worker output exists, otherwise host PID; actor-form top-level PID is host. Child PID and client PID have their own owners. | reply, lifecycle; S; Q-19 |
| G45 · envelope | Worker exit/signal, partial output, readiness/completion and poll-stop describe different facts. Waits use monotonic budgets and report elapsed/clock failure; reap/cleanup can exceed polling budget. Termination request signal/rc/errno differs from confirmed reap; wait errors include EINTR. | lifecycle; keep |
| G46 · envelope | Inventory cleanup trigger (six values), grace end (four), collection basis (three), and disposition state/basis pairs from their source schema; run and step scopes differ. Supported/unresolved/inapplicable/conflicting are assessments of preserved raw evidence. | lifecycle, diagnostics; keep; R-07, Q-20 |
| G47 · envelope | Controller process disposition includes `per_actor`, missing from guide's list. Cause is host_cleanup only with supporting end-to-end record; clean exit/unknown otherwise. A poll-stop reason can coexist with later clean exit. | lifecycle, envelope; R-07, R-35 |
| G48 · envelope | Current controller success follows host `finished` even when integrity findings withhold interpretations. Reply-wide and per-actor scopes can disagree in projection. State current consequence and keep intended behavior decision visible. | envelope, diagnostics; R-20, R-34, R-38 |
| G49 · envelope | runner_reporting_failed exits 1 and retains original summary. retained=true preserves observations with comparisons omitted; retained=false is minimal and lacks steps/children. This output does not certify query order. | reply, diagnostics; R-19, R-36 |
| G50 · envelope | Optional children may be absent/null; errno keys may be present null. Completed exec slots alone supply exec-child/observation fields; stdout/stderr appear when bytes exist. Missing record leaves execution fact unknown. | reply, steps; keep |
| G51 · lifecycle | Distinguish single/actors execution forms; actors form omits singular worker/policy/apply projection and lists actors in request order with setup/application/equipment/launch/subprocess/receipt. `visits` is declared phase ordinals, not only activated visits. | reply, actors, actor_evidence; S for visits; R-10, R-36; Q-19 |
| G52 · lifecycle | Phase ID/1-based ordinal, actions, arrival/completion and collection status describe each visit; collected may include partial failure. Actor visit ordinals are per actor. Later phases may have arrival even after another actor's incomplete phase under applicable failure branches. | actors, reply, actor_evidence; R-17, R-36 |
| G53 · lifecycle | Validator PID and reap status normal/signal/unknown are optional; signal does not identify sender. Phase/query ownership follows IDs and expected plan, not PID uniqueness. Duplicates/unexpected/null identifiers remain diagnostic records. | lifecycle, diagnostics, steps; keep |
| G54 · lifecycle | Validator posix_spawn failure records runner-host origin, operation, native direct return and executable path; any unfamiliar nonzero result is still failure. Preserve it when higher failure/degraded output supersedes outcome. | lifecycle, diagnostics; keep |
| G55 · lifecycle | Comparison has six relation dimensions. `query_first` requires the full collection/release/live-phase chain; before that, order is unestablished. Validator failure alone need not block release; late records excluded; death before acknowledgement breaks order while later evidence remains. | steps, actors; R-16, R-19; Q-08 |
| G56 · lifecycle | Preserve operation relation mapping: read/access→file-read-data, writes→file-write-data, unlink→file-write-unlink, exec→process-exec*, mach lookup and sysctl read. Create is unresolved; mapping and both exact submitted target strings are operands. | probes, steps; keep; Q-08 |
| G57 · lifecycle | Worker evidence includes selected ABI, latest acquired atomic progress, native failure, readiness, diagnostics and policy-input expected/received/EOF. Equal byte counts establish length only; short delivery is op 2/code 13 before compile. Contradictions preserve raw evidence while comparisons are withheld. | lifecycle, diagnostics; keep; R-19, R-36 |
| G58 · lifecycle | Startup clock op 12/code 14 fails before policy with exit 12; release wait op 11 uses expiry code 8 or clock code 14 (including backward/earlier-invalid reasons). Errno belongs to native failures; exec timing text need not carry errno. Open numeric codes remain retained. | lifecycle, diagnostics; keep; Q-20 |
| G59 · lifecycle | Diagnostic absence, empty payload, truncation, incomplete publication, replacement decoding and raw byte counts are distinct. | diagnostics; keep |
| G60 · lifecycle | Final acquire snapshot follows cleanup and keeps earlier poll stop; host write counts and worker read counts have different owners. Five-second absolute policy-transfer budget starts after spawn; timeout closes input, cleans up and skips polling; published short-delivery failure can take outcome precedence. | lifecycle, transport, refusals; keep; Q-21 |
| G61 · lifecycle | Native validator result versus synthetic query placeholder: requested-but-no-verdict has synthetic rc 0/native_rc null and reason; excluded query has rc -1/prediction_unavailable/query_not_requested. | steps, diagnostics; keep |
| G62 · lifecycle | Worker-published completed attempts, including failures, differ from synthetic no_completed_result. Lifecycle values completed, started_without_result, not_reached, unsupported, unresolved, conflicting carry different support. | steps, lifecycle; keep; R-36 |
| G63 · lifecycle | Attempt `rc` is PolicyWitness status; fresh-operation native subresults retain actual syscall returns. Source vocabulary lists need complete attachment during drafting, not inference from examples. | steps, diagnostics; keep; Q-20 |
| G64 · transport | Validator NDJSON retains accepted raw records including null IDs and association issues, input/output counts, faults and reap. Duplicate matches lack unique verdict; structurally unexpected records remain diagnostics. | diagnostics, steps, transport; keep; Q-22 |
| G65 · transport | Client records argv, timing, exit, byte counts and bounded retention; capture_error/truncation differs from parse_error. Transport states accepted/missing/unsupported/malformed/delivery_failed; invoked/not_invoked/unknown requires admitted capture evidence. | transport, envelope; keep |
| G66 · transport | Correct claim that foreign host execution can precede rejection: reservation identity admission occurs before specimen interpretation/invocation. Preserve independent capture and embedded-host admission with bounded foreign bytes. | transport, identity; correct; F-19, Q-12 |
| G67 · transport | Continuous-clock deadline covers client launch/stdin/delivery; clock fault preserves invocation knowledge while reporting local error. Acquisition attempts carry ordinal, UUID, elapsed/outcome, control bytes/hash, peer PID/status/instance/lease/reason and bounded native errors; credential omitted. Grant establishes reservation only. | transport; keep |
| G68 · transport | Exact accepted host bytes are base64 with original/retained lengths and truncation flag. Full-host-byte retention differs from host admission; client errors do not fabricate a host reply. Rejected raw client bytes are bounded and do not establish submission state. | transport, envelope, wire; keep; Q-09 |
| G69 · transport | Request stdin is delivered once; write counts/errors establish writer observation, not receipt. Delivery failure yields tool_error/exit 2 with precedence over reply interpretation; captured bytes remain. Client is null when not invoked. | transport, envelope; keep; Q-12 |
| G70 · transport | Query target PID is worker or null, never a host substitution. Native rc is authoritative for native calls; diagnostic -1/native null and missing synthetic 0 have distinct origins. | steps, diagnostics; keep |

### Dossier, extension evidence and step interpretation

| Row / old location | Meaning to preserve, correction or question | Destination / disposition |
| --- | --- | --- |
| G71 · dossier | Dossier appears for run refusal/tool failure as well as success; it records held path/input, while policy strings remain in request. Preserve augmentation status semantics G39. | dossier; keep |
| G72 · dossier | Controller literal-import scan precedes invocation: complete/incomplete/failed/not_applicable, first error/cap/cycle, once-per-import regular-file read/hash/lex, successful closure digest. This observes its own read, not later compiler imports or macro evaluation; helper inventory is separate. | dossier, policy; keep; Q-07 |
| G73 · dossier | Host sysctls may be null. Selected runner provenance includes bundle/service/path/registry identity and four binaries' signatures, entitlement keys/grants; builtin inventory comes from manifest and has no signature metadata. | dossier, equipment; keep |
| G74 · dossier | App manifest/path/optional verification flag; parse failure gives null object. Binary evidence may be null when selected manifest supplies baseline, otherwise actual hash with match/mismatch/unavailable and reason, including overrides/BYOXPC. This pre-invocation observation is separate from executed-byte evidence and run outcome. | dossier, equipment; keep; R-09, Q-01 |
| G75 · dossier | Collection failures leave partial/null/empty provenance without stopping run. Preserve jq reading examples as guide workflows and their field meanings in contract. | dossier/guide; keep; Q-06 |
| G76 · equipment | Extension events identify step/phase/actor/op/ref and boundary/result/publication/native errno/lifecycle; issue has class/flags/target/non-null/length. Transfer event is an acknowledgement, not a native sandbox call. | extensions, actor_evidence; keep |
| G77 · equipment | Transfers record exchange; resources record token/delivery/handle ownership, reference, status, raw-handle aliases, release attempt and last use. Presence of raw handle value is distinct from resource identity. | extensions, actor_evidence; keep |
| G78 · equipment / FAILURE-PROPAGATION | Custody values: issued, issued_uncustodied, null, unavailable, not_reached, unresolved. Delivery values: delivered, custody_unavailable, recipient_rejected, recipient_timeout, recipient_unavailable, request_invalid, host_timeout, clock_fault, copy_mismatch. Preserve no-call authority/channel/delivery/symbol distinctions beside each value. | extensions, actor_evidence; keep |
| G79 · equipment / FAILURE-PROPAGATION | returned requires publication; consume -1 gives no handle. Token/handle/symbol/repeated-release failures are unavailable; absent result remains unresolved despite a pre-call marker; omitted actions have no invented event. | extensions, diagnostics; keep |
| G80 · equipment | Fresh read records open/stat/read/close sequence, each rc/errno, successful count and hex extent, descriptor identity; failed open skips later calls, first failure aggregates, absent payload establishes no bytes, prefix is bounded. | probes, steps; keep |
| G81 · equipment | Fresh write records open/truncate/write/close and descriptor identities/signed sizes at opened/truncated/written stages; pre-open path metadata is diagnostic and used for exclusive create. Failed truncate skips write; failed open skips all later calls. Aggregate first failure includes short write without invented errno; observed write differs from durability. | probes, steps; keep |
| G82 · steps | requested_path preserves all target strings. Successful old open/create may report F_GETPATH; failure is explicit null; fresh operations use descriptor identity. Later host path observation is separate. | steps, diagnostics; keep |
| G83 · steps | filter_value is actual query argument except excluded-query echo. Path ID 1/global 2 and empirical global 12 require separate evidence; none ID 0 should be included, local ID 3 remains unresolved for its excluded pair. | probes, steps; Q-08, Q-18 |
| G84 · steps | Query outcomes: allow/deny from clean native result, error with native/diagnostic/synthetic origin, unsupported operation (-1/errno 22 with wildcard hint), prediction_unavailable for excluded pair or unresolved path. Missing-reason text does not necessarily explain every native error. | steps, diagnostics; keep; Q-20 |
| G85 · steps | Correct `open_failed`: file descriptor <0, not nonzero. Successful old open is not an enforcement-cause claim; replace outcome `ok (allow)` shorthand with operation observation. Preserve distinct file, mach, sysctl, exec and no_completed_result outcomes. | steps, probes; S for descriptor rule; Q-19 |
| G86 · steps / FAILURE-PROPAGATION | Preserve all 14 reading rules: query order requires chain; permission-shaped return lacks causal attribution; same path string may name changed object; state can change between query/attempt; within-phase unlink order and inter-phase completion differ; exec query concerns admission only; wildcard/create relations may be unresolved; mapping+both strings needed; later realpath is observation; unsupported relations unresolved; extensions separate; query may precede consume/release that changes later attempt state. | steps, diagnostics; keep; R-19 |
| G87 · steps | Path diagnostics run in host after orchestration, with observer/stage/input. Compact same_as_input uses exact UTF-8 bytes: omitted resolved path means same, string means different, null unresolved; names unique and representation exclusive. | diagnostics; keep |
| G88 · steps | realpath followed by firmlink handling or standardized fallback differs from syscall target. Attempt leaf resolution and resolved-parent-plus-literal-leaf are separate; relative unresolved parent is unavailable. These observations do not rewrite the submitted comparison operands. | diagnostics, steps; keep |
| G89 · steps | Preserve absent-path create example showing prediction_unavailable and successful creation with after-run realpath observation. Preserve jq examples distinguishing actual values, null and omitted compact field. | steps/guide examples; keep; Q-06 |
| G90 · steps | Limits on inferred cause, object continuity and cross-time authority belong beside each observation's positive meaning. Do not import introductory negative-space disclaimers as substitute for these concrete limits. | steps, extensions; editorial disposition; F-20 |

### Refusals, operations and runner management

| Row / old location | Meaning to preserve, correction or question | Destination / disposition |
| --- | --- | --- |
| G91 · refusals | Host outcomes include finished, runner_timeout, runner_failed, runner_reporting_failed, worker_spawn_failed, validator_spawn_failed, no_reply, decode_failure, unavailable, bad_request. finished concerns harness completion while individual attempts may fail. runner_timeout also covers policy transfer, not only poll sentinel. | reply, refusals; Q-21 |
| G92 · refusals | bad_request has no worker steps; admission_failure holds count/unit/UTF-8/items/NUL location details. Echo sanitation is per field: specimen placeholder, omitted run_kind, unknown format, dropped override path and withheld parameter keys. | request, refusals; keep; Q-04, Q-05 |
| G93 · refusals | Request failure precedence is decoder branch-specific; preserve all unknown/duplicate/meaning/capacity refusal conditions and human error versus structured fields. | refusals; keep; Q-04 |
| G94 · refusals | Client xpc_error, xpc_timeout, acquisition failure and submission refusal report local transport without a host RunResult. Invoked requests are never replayed; rejected captures leave invocation unknown. | transport, refusals; keep; Q-12 |
| G95 · refusals | Preserve timeout table: client xpc_timeout lacks host reply; host runner_timeout can arrive with client exit 0 because delivery succeeded; controller exits 1 in either case. Client wait expiry is distinct from host cancellation. | transport, envelope; keep |
| G96 · refusals | Client launch/delivery produces tool_error/exit 2. Unsupported/malformed host, capture and local errors have different retained material. Bring the controller result catalog into contract instead of leaving it only in controller README. | envelope, refusals; keep; Q-20 |
| G97 · refusals | Preserve recovery examples: inspect structured failure before changing input, repair exact assertion/field/path, retain uncertain invocation and use runner diagnostics/reconciliation. Workflow advice stays guide; refusal consequences live beside rules. | guide and refusals; keep; Q-06, Q-12 |
| G98 · operations | Filters are none, path, global_name, local_name, iokit_registry_entry_class, iokit_user_client_class, sysctl_name; none permits absent/null, others require nonempty value. Four operation/filter prediction exclusions are iokit-open-service/registry-entry-class, iokit-open-user-client/user-client-class, sysctl-read/sysctl-name, mach-lookup/local-name. | probes, request; keep; Q-08 |
| G99 · operations | Preserve empirical basis and limits of the first three excluded pairs (IDs 1–200 exploration, 2026-05-29) separately from conservative unresolved local mach mapping. Other operations with same filter follow their own query/path eligibility. | probes owners/known evidence gap; Q-18 |
| G100 · operations | Closed file operations: open_read O_RDONLY with ignored one-byte read/close results; open_write O_WRONLY\|O_TRUNC with ignored write/close results; create O_WRONLY\|O_CREAT, 0600/umask, neither exclusive nor truncating; read_fresh; write_fresh truncating existing then x; create_fresh exclusive then x; unlink; access. | probes, steps; S for old open/create operations; keep |
| G101 · operations | mach attempts use bootstrap lookup; sysctl uses one post-apply 4096-byte buffer, no sizing/retry, reporting PW status/errno while discarding value bytes and post-call length. | probes; keep |
| G102 · operations | Exec target is absolute argv[0], args follow. Its resources are acquired post-apply per attempt and released before step completion. Setup failures identify that boundary; child spawn result is distinct from eventual child exit. | probes, steps, lifecycle; keep |
| G103 · operations | Exec PID 0 means no child; exit -1 is unknown/signaled with separate signal field. Spawned child establishes spawn even if nonzero exit; aggregate rc can be exit or cleanup -1. Child stdout/stderr retained when nonempty. Query targets executable admission, not every prerequisite. | probes, steps; keep |
| G104 · operations | Exec child uses empty environment, /dev/null stdin, pipes and close-on-exec. Guide's worker-environment qualification needs scope against actor launch record. Preserve `exec_baseline` example with historical environment and actual broad effects. | equipment, probes/guide; Q-17, Q-18 |
| G105 · operations | Completed exec slot alone supplies observation: collection stop/deadline kind/faults frozen before cleanup; process-group termination request with leader fallback except ESRCH; errno on failed request; reap stop/last wait/raw status only when confirmed. Clock faults coexist with other facts. Ordinary exit+EOF does not witness all descendants; exceptional group cleanup and host-owned worker supervision differ. | lifecycle, steps; keep |
| G106 · installation | Reservation is effect-free, contains no specimen, is connection-bound/single-use and retires on expiry/abandonment. Retry may occur before invocation within limits; client marks invoked before execute and never replays. Peer PID is self-reported and lease credential omitted from reports. | transport, installation; keep |
| G107 · installation | Source bundle seal/inventory is checked before mutation; editing needs reseal. Required helpers, XPC! package type, service/bundle ID and executable derivation are validated. Signed bundle PWContract, registry and live peer identities are separate. | installation, equipment, identity; keep; Q-12 |
| G108 · installation | Entitlements require configured identity or ad hoc mode; selected worker+host receive requested entitlements, other worker/validator empty. Reinventory and recursive verification follow signing; record actual granted keys/readbacks for four binaries. | installation, equipment; keep |
| G109 · installation | user scope needs logged-in GUI, system scope admin; skip-bootstrap and environment options have stated effects. Durable pending record precedes plist/bootstrap; skip-bootstrap can finish installed plist state; failure retains ownership record. | installation; keep |
| G110 · installation | Team matching is default caller authorization; ad hoc no-team fails under team requirement; removing authorization keys opens local access. Report actual configuration rather than imply identity equality supplies authorization. Preserve xpc_error/timeout diagnosis distinction. | installation, transport; keep; Q-01 |
| G111 · installation | `runner verify` sends fixed allow-all empty plan over stdin, reports reply PID, defaults to five seconds; each request consumes fresh host, launch throttle may cause reconnect. Four-second/three-run timing is historical observation, not timing guarantee. | installation, transport/guide; Q-06, Q-18, Q-19 |
| G112 · installation | Runner selection id/service, standard/BYOXPC mode and required boolean-true selected-worker entitlements precede host execution. Preserve deny-default empty-plan smoke example. | request, installation; keep; Q-06 |
| G113 · installation | Remove writes pending ownership before checking/bootout/plist changes. Unknown metadata is retained without authorizing cleanup. Retire only after both service and plist absence; one-second wait may leave cleanup_retained/warnings; retry/skip-bootout preserve ownership. | installation; keep; Q-13 |
| G114 · installation | list reports installed and pending; reconcile reports recorded/observed ownership and candidates without mutation. Prefix-only unknown candidate is not owned or proven absent. Preserve staging/session cleanup guidance where durable recovery uses it. | installation/guide; keep; Q-13 |
| G115 · installation | Stable advisory lock plus atomic JSON permits one modifier while readers remain available. Validate bundle/helper/inventory rows; invalid entries remain diagnostic. Not-found status/verify/remove exits 2 with command-specific result kind. | installation, envelope; keep; Q-13 |
| G116 · installation | Keep manual cleanup examples with exact owned service/scope/plist/registry path and warnings to retain records until absence. Registry default path is part of user-visible configuration; commands/examples require workflow validation in stage four. | installation/guide; keep; Q-06, Q-13 |

### Value sets retained from the guide

These D-grade sets preserve useful distinctions that a field-name inventory
would lose. They supplement the row meanings above; structured definitions
must confirm each set's closed/open status and conditions from its owner.

| Account | Values / distinctions carried forward |
| --- | --- |
| G46 cleanup_trigger | deadline_expiry, completion, child_reaped, poll_wait_error, policy_transfer_error, policy_transfer_timeout. |
| G46 grace_end / collection_basis | not_entered, reaped_during_grace, exhausted, wait_error / after_confirmed_reap, execution_may_continue, unavailable. |
| G46 run questions | final_status, stop_reason, cleanup_trigger, grace_end, kill_request_and_result, collection_basis, progress_association. Each answer is supported with basis, unresolved/inapplicable with reason, or conflicting with issues. |
| G46 step questions | step_boundary_reached, step_result_published, step_requested_operation_applicability; same answer distinctions, scoped to that step. |
| G47 process disposition | no_worker, unconfirmed, clean_exit, nonzero_exit, signaled, conflicting, withheld, unrecognized; add source-confirmed prior R-35 value per_actor. |
| G47 termination cause | host_sentinel_deadline, host_exit_grace_exhausted, host_cleanup_after_wait_error, host_cleanup_after_transfer_error; null for confirmed clean exit, unknown otherwise. Keep missing host-transfer-timeout cause question with Q-20 rather than invent a value. |
| G51 setup_status | applied, unapplied_declared, setup_failed, exited_before_setup, setup_timeout, launch_refused, transfer_failed, not_launched. |
| G52 phase collection | not_reached, not_needed, collected, budget_exhausted, clock_unavailable; collected includes failure/partial collection. |
| G55 validator disposition | not_invoked, not_needed, not_spawned, reaped, unconfirmed. Empty query plan and no invocation are distinct. |
| G55 comparison | observation: succeeded, permission_failure, other_failure, unavailable; basis: completed_worker_status, permission_errno, bootstrap_permission_result, spawned_child, no_completed_worker_result; operation_relation: matched, different, unresolved; target_relation: same_submitted, different_submitted, unresolved; order: query_first, unestablished; limitations is a list. |
| G55 limitation strings | query_plan:path_unresolved_at_planning, query_plan:prediction_unavailable_pair, query_plan:unrecognized_filter_kind; attempt:lifecycle_unresolved, attempt:lifecycle_conflicting, attempt:unsupported, attempt:not_reached, attempt:started_without_result. Empty list otherwise. |
| G61/G84 query outcomes | allow, deny, error, unsupported_operation, prediction_unavailable. Preserve native versus synthetic source and the unavailable sentinel rc -1/errno null/filter_type_id null. unsupported_operation retains the wildcard hint while the attempt still runs. |
| G85 attempt outcomes | ok, read_failed, write_failed, open_failed, unlink_failed, access_failed, lookup_failed, sysctl_failed, exec_failed, unsupported, no_completed_result. `ok` needs operation-specific evidence; `no_completed_result` leaves whether the operation ran unresolved. |
| G105 exec collection | leader_exit_and_eof, deadline, observation_error, clock_fault; deadline_kind child/plan. |
| G105 exec cleanup | not_requested, ownership_unconfirmed, requested; group_request only for requested, leader_fallback only on the documented failed-group-call branch. |
| G105 exec reap | reaped, wait_error, ownership_unconfirmed, group_request_failed, clock_fault, deadline; raw status only after returned leader PID, errno only on -1. |

Extension custody/delivery sets are fully enumerated in G78; application pairs
remain R-15/Q-10 rather than being guessed from setup_status. The definitions
must also retain null/absence distinctions throughout G27–G30, G49–G54,
G61–G69, G71–G81 and G105.

## Report findings and adjudication reconciliation

The report's findings are not decisions to change behavior. This table records
their disposition, including findings whose meaning remains sound. The claim
that readers were confused is narrower than a finding that a passage lacks
needed information: silence and later prompted reasoning have distinct grades.

| Finding | Disposition in this map |
| --- | --- |
| F-01 · distributed authority | C01–C48 plus G01–G116 transfer all inventoried meaning into one source. Readers recognized missing information; they could not locate it. |
| F-02 · outline/region mismatch | Render surface membership and readable anchors from structured nodes; C05. Raw-Markdown journals cannot establish rendered-page navigation behavior. |
| F-03 · declared stamp change | C04–C07, R-25–R-29; distinguish unchanged declared inputs from unchanged implementation and observations. Development reuse remains Q-03. |
| F-04 · check names are labels | Attach exact assertion/context/limits below rules; D/I/S/E grade above. A suite label supplies no execution credit. |
| F-05 · examples | Keep useful examples with the explicit evidence inventory below; Q-06. Remove blanket “verified.” |
| F-06 · receipt producer/reader | Already corrected in current C243. Carry R-01–R-06 without reviving old text. R-06 was closed during this work by the constructed orchestration check at `5e51300d`; see its T-grade entry below. |
| F-07 · semantic findings | C21, C26, C28, C42, G48–G49; R-19, R-20, R-34, R-36, R-38. Publication, structural decoding and supported claims are separate operations. |
| F-08 · refusal vocab/order/null | C09, C11, C32–C36, G02, G22–G24; Q-04. Preserve open code vocabulary and actual branch order. |
| F-09 · entry paths/overrides | C08–C10, C31, G31, G74, G106–G110; Q-01. Define standalone helper, CLI, direct XPC, build env and signed overrides individually. |
| F-10 · identity equality | C01–C03, G66–G68, G107–G110. State comparison operands and admitted boundary; seal/authentication/equipment have separate owners. |
| F-11 · identity derivation | C02, C05, C45; Q-02. Exact input walker and two-tag handling need source-backed wording. |
| F-12 · residue/terms | Define actors, apparatus, publication, observation partition, native strings, byte records, helper and fallback. R-10, R-11, R-16, R-17, R-23, R-30–R-32. Denial removal follows current editorial direction, not a claim both readers stumbled. |
| F-13 · maintainer directions | C12–C15, C43–C48 go to maintenance. Both readers correctly recognized the audience; separation still improves the contract's obligation structure. |
| F-14 · generated structural agreement | C38–C42; Q-14. Record generators' actual guarantee and handwritten primitive/projection checks separately. |
| F-15 · equipment ambiguity | C24–C29; R-11, R-13–R-18, R-36–R-38; Q-10, Q-11. Preserve undefined promise and unrun parked-exit experiment. |
| F-16 · installation phrases | C37, G113–G116; Q-13. Opaque round-trip preservation and legacy normalization need actual definitions/evidence. |
| F-17 · worker identity | C44–C47; Q-16. Manual regeneration and actual check locations replace the broad account. |
| F-18 · unexecuted branches | Q-06, Q-10–Q-16 retain experiment and check gaps. No execution credit added here. |
| F-19 · guide disagreements | G03, G66 are current corrections; old receipt conflict is already superseded. G44/G51/G85 add narrowly source-confirmed guide corrections. |
| F-20 · sound examined statements | Retain independent exact gates, fingerprint-before-contract, bounded refusal paths/bytes, host-may-launch distinction, public expected-contract diagnostics, effect-free reservation and no replay after invocation. |

### All twenty adjudicated divergences

| Divergence | Destination / explicit disposition |
| --- | --- |
| A-D01 product/PW | C01 definitions. |
| A-D02 specimen/capture | C01, C19, G01, G43; distinguish input object, serialization and record producer. |
| A-D03 identity inventory | C02/C45, Q-02; public scope and internal scope are different definitions. |
| A-D04 direct XPC | C10, Q-01; all controller selector fields refused there, unresolved augmentation refused there. |
| A-D05 comparison scopes | C21/G55–G56/G86; each relation's operands and applicability, no invented stronger relation. |
| A-D06 parser generation | C14/C38; request authorship versus generated response structure; maintenance destination. |
| A-D07 guide referral | Manifest/guide inventory above replaces distant unlinked authority. |
| A-D08 enforcement agreement | C17/G86; state query and operation evidence with causal/time limits; no promised agreement classifier. |
| A-D09 retention | C19/C40/G68; put byte bounds beside retention. |
| A-D10 fallback trigger | C20/G31/G35; `xpc_error` and held request. |
| A-D11 declaration reply | C18/C24/G51; R-10 removes obsolete term while describing actual execution forms. |
| A-D12 acquired decision | C24; R-11 remains unresolved until a rule has actor, boundary and consequence. |
| A-D13 optional/additive | C33/C41; optional field presence is a shape condition, exact fingerprint admission is another boundary. Remove ambiguous additive wording. |
| A-D14 path representation | C34/G23; keys and index strings, not numeric JSON indices. |
| A-D15 legacy infrastructure | C37/G113; registry reading/removal and exact public execution admission are different operations. |
| A-D16 schema correctness | C38/Q-14; generated agreement has a bounded guarantee; independent correctness evidence remains explicit. |
| A-D17 content/context/endings | C42/G64/G80–G81/G105; define actual records and facts they support. |
| A-D18 templates/candidates | C43; named harness ownership and inspected-candidate workflow in maintenance. |
| A-D19 generator invoker | C44/Q-16; manual owner invocation before consuming build, checks do not write. |
| A-D20 shim/host mirror | C47; component definitions, with layout implementation detail in maintenance. |

### Silences, corrections and prompted answers

All fourteen Part-4 silences retain explicit dispositions. These are possible
reader conclusions the journals neither state nor rule out, not observed
misunderstandings.

| Silence number | Disposition |
| --- | --- |
| 1 surface end | C05/F-02; generated visible membership. |
| 2 unchanged stamp | C04–C07/F-03; declared inputs and actual behavior separated. |
| 3 suite credit | grades/F-04; exact check/assertion/context required. |
| 4 tested examples | example inventory/F-05; Q-06. |
| 5 published satisfaction | C21/C26/C28/C42; R-19, R-20, R-36, R-38. |
| 6 equal packages/authentic peer | C03/G107/G110; independent identity, signing and authorization operations. |
| 7 foreign host already ran | G66; correct guide against pre-invocation identity gate. |
| 8 helper gate | G31; standalone compiler input boundary expressly named. |
| 9 signed overrides | Q-01, R-12; inventory accepted paths/effects and unverified_fixture consequences. |
| 10 exhaustive refusal table | C35/Q-04; selected list versus open code vocabulary explicit. |
| 11 development reuse | C04/Q-03; retain missing baseline rather than infer release history. |
| 12 exit 1 inference | C33/G94–G96; complete controller classification. |
| 13 original file bytes | C20/G38/G69; parsed held input and submitted serialization separate. |
| 14 CLI selector priority | C08/Q-01; CLI option parsing precedes request admission. |

The three unclear items are now constrained by follow-up answers: answer 1
left direct-build invoker unsettled (C44); answer 2 meant the reply reader,
confirming the old receipt sentence invited that reading (C30); answer 3
distinguished source-associated ordinals from dependent actor ordinals, but
inferred the gate association (C28/R-17). Do not label that last reader belief
wrong merely because the original journal was terse.

All ten report corrections are incorporated: (1) full primitive byte order
and booleans in C39; (2) request versus response generators in C14/C38;
(3) historical registry boundary in C37; (4) optional/additive wording in
A-D13; (5) missing terms in F-12/A-D17 and Q-05/Q-22; (6) path element type
in C34; (7) reserve-geometry referral in C25/Q-05; (8) missing information
rather than presumed completeness in F-01; (9) correctly recognized
maintainer audience in F-13; (10) denial removal is editorial direction,
not reported reader difficulty, in F-12.

The 15 answers in `FRESH-ENCOUNTER-ADDENDA.md` are prompted rereading by the
first journal writer, who had prior guidance exposure. They are not the
isolated baseline's first encounter. Preserve this provenance when using them.

| Answer | Reconciled meaning / disposition |
| --- | --- |
| 1 regeneration | Writer understood nonwriting checks, left manual-versus-hook invoker open; C44/Q-16 supplies actual owner. |
| 2 receipt actor | Reader-side acceptance was intended by the reader; current host-versus-reader correction C30 supersedes that promise. |
| 3 ordinals | Four-way sequence mapping was partly inference; define it at C28/R-17. |
| 4 contract/machinery/maintenance | Reader could assign maintenance audience; generated outline still needs visible normative membership C05/F-02. |
| 5 older unchanged stamp | Review remains required; declared stamp age is not a complete behavior comparison, C04/F-03. |
| 6 verified examples | Reader took examples as supported but lacked test binding; Q-06 records exact support. |
| 7 satisfied gate missing source time | Reader correctly withheld justification but could not name diagnostic mapping; R-19/R-38 make consequence/scope concrete. |
| 8 wrong nonce | Reader inferred request-aware reader rejection; C30/R-01–R-06 preserve current producer responsibility and reader limits. |
| 9 equal identity | Prompted answer correctly separated admission, package bytes, authenticity and runtime evidence; C03/G107/G110 state actual comparisons. |
| 10 overrides | Name was not understood as access control; inventory all accepted effects and signed-build applicability Q-01/R-12. |
| 11 code table | Reader retained unfamiliar refusals without guessing; preserve open vocabulary C35/Q-04. |
| 12 development reuse | No digest-to-release baseline given; Q-03 explicit. |
| 13 exit 1 | Failure number did not identify cause; C33/G96 fills outcome account. |
| 14 file bytes | Parsed/preprocessed held request is not original serialization; C20/G38/G69. Duplicate-key path difference remains Q-07. |
| 15 no bypass | Reader limited it to described admissions and had no standalone-helper rule; Q-01/G31 replace global denial with operations. |

### Isolated baseline uncertainty register

All 61 questions have a destination below. “Answered” in that reader's
register means answered by the old prose, not independently established in
implementation. The baseline was a sequential rereading after an earlier
complete read of the supplied contract; it opened no repository sources.

| Questions | Destination / disposition |
| --- | --- |
| U1 public inputs/cleanliness; U2 surfaces; U5 canonicalization; U7 stamp command; U8 second table | C02/C05–C07; identity and maintenance. Remove missing antecedent, preserve derivation details Q-02. |
| U3 artifacts; U9 selectors; U11 grammar/defaults | C01/C08–C11/G01–G03/G24/G112; request, transport, definitions. Full field/default ownership still required in source. |
| U4 installation; U45 ownership/aliases; U46 historical forms | C37/G106–G116/Q-13; installation; actual commands in guide. |
| U6 reservation allowances; U44 native-string bounds; U50 charging | C13/C25/C40/G06/G23/G41/Q-05; put exact quantities beside bounded object, retain owning limits input. |
| U10 contract codes; U12 paths; U43 path types/withholding | C32–C36/G23/Q-04; refusals. |
| U13 augments; U19 SBPL/import holding; U25 fallback | G26/G31–G40/G72/Q-07; policy/dossier, keep examples. |
| U14 entitlements; U27 sealing; U31 roles/association | C23/C25/G07/G09/G107–G108; equipment; R-09/R-12/R-13. |
| U15 vocab/exclusions; U17 relations; U20 enforcement; U26 query_first | G41/G55–G56/G82–G86/G98–G103/Q-08; probes/steps, preserve bounded meanings. |
| U16 nonce; U38 receipt | C30/G27–G30; profile, current R-01–R-06 replaces old reader promise. |
| U18 capacity precedence | Correct the reader's “answered” conclusion using C11/C36/Q-04: some structural decoding precedes capacity. |
| U21 extensions | G08/G12–G19/G76–G81; complete action grammar and evidence meanings. |
| U22 dependency; U36 declaration; U37 ownership/departure | C28/C29/G10/R-16–R-18/R-37/Q-11; actor_evidence/lifecycle. |
| U23 envelope; U41 exits; U61 build types | G42–G50/G91–G96/C48/Q-20; envelope/reply/identity. |
| U24 retention; U39 frames; U42 optional compatibility; U49 encodings; U52 canonical fingerprint | C19/C38–C42/G68/Q-09/Q-14; wire/transport. |
| U28 worker identity; U35 application publication; U58 header | Reader's broad “answered” U28 requires the check-location qualification C46/Q-16. C27/R-15 defines application. Equipment/lifecycle. |
| U29 full lifecycle; U30 setup/cells; U32 partition; U33 prep failures; U34 application pairs | C24–C27/G45–G63/R-11/R-14/R-15/R-36; definitions first, preserve unresolved meaning. |
| U40 uncertain recovery | C31/G65/G69/G94/G106/Q-12; transport meaning, guide recovery. |
| U47 schema correctness; U53 semantic validators | C38/C42/Q-14/R-19/R-36; bounded generated agreement and semantic consequence matrix. |
| U48 validator NDJSON; U54 fresh content/context/endings | G53/G64/G80–G81/G105/Q-22; diagnostics/steps/lifecycle. |
| U51 outer deadline | C40/G45/G60/G67/G95/Q-15; each clock has own operation and consequence. |
| U55 candidate inspection; U56 build sequence; U57 worker hash framing; U59 build evidence; U60 producer controls | C43–C48/Q-06/Q-16; maintenance with precise tools/owners, no invented certification of artifacts. |

## Examples to retain with their evidence limits

These are inherited grades from F-05 and its references, not newly executed
checks. The existing 13 example sentences remain indexed by old surface.
Use exact current example contents when assigning structured IDs.

| Old example | Existing support / disposition |
| --- | --- |
| request · C63 foreign assertion plus invalid selector | Exact combination uses injected dependencies; signed default uses missing contract plus misspelled key; independent process observation is opt-in. Preserve precedence example, grade its owner. |
| policy · C129 missing augment, no worker, unchanged file | Signed default supports refusal; the unchanged-file assertion for this case was not found. Keep useful effect question explicit. |
| probes · C135 open_write truncation / foreign assertion | Default effect test supports truncation; foreign-build prevention is opt-in two-build. Keep both with separate support. |
| actors · C141 nonexistent actor | Default signed CLI and direct-XPC refusal. Inherited execution report, not independently rerun here. |
| envelope · C147 foreign helper | Constructed data supports reader classification. |
| dossier · C153 held input after file change | Injected unit dependencies; real signed fallback-held-input experiment remains open. |
| steps · C159 foreign host one diagnostic | Constructed harness-reader record; live control opt-in. Do not label it a controller product run. |
| lifecycle · C165 unreaped worker | Real host driver with fixture child plus constructed controller test; not ordinary signed product evidence. |
| equipment · C171 hash mismatch | Constructed binder bundle and default signed installer; signed run case missing. |
| profile · C243 wrong nonce | Old example was false as written and current text was repaired. R-06 public result/exit/retention consequences now have a constructed orchestration check at `5e51300d`, read here (T), not a new signed product experiment. |
| transport · C249 foreign live peer | Fake connections; opt-in instrumented host. Genuine foreign signed-host receiving boundary remains untested. |
| refusals · C255 missing contract | Default signed CLI/direct-XPC and unit case. Preserve missing contract principle without obsolete schema mechanism narrative. |
| installation · C296 legacy record removable | Unit and opt-in live control; exact unknown metadata preservation still Q-13. |

The guide examples are preserved by meaning in G01 (minimal apply-only),
G08 (two-actor access/revocation), G12 (redelegation), G20/G89 (absent path and
creation), G21 (capture typo refusal), G26/G36 (parameter/import examples),
G27 (receipt request), G38–G40 (augmentation and exec baseline), G41
(read-hosts), G75/G89 (jq interpretation), G95 (two timeout boundaries),
G102–G105 (exec observation), G107–G116 (install/verify/select/smoke/remove/
reconcile/manual recovery). Keep complete useful inputs in the guide; a
contract example may use only the portion needed to establish its rule if it
links the full workflow. No guide example is newly executed here. Each needs
a source/check owner or labelled evidence gap before it is called verified.

## Source-confirmed corrections and newly read implementation

The source below was read narrowly after consulting controller/runner working
rules and implementation introductions. No tests were run for these new
corrections. They are S, not E. The one newly read test is separately T below;
other implementation claims retain D/I grades.

| Assertion | Source actually read | Consequence |
| --- | --- | --- |
| Ordinary reply PID chooses worker output PID, otherwise host PID | [CWorkerOrchestrator.swift](../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), lines 200–226 | G44 is wrong as a universal host-PID statement. Actor form's `getpid()` and runner verify's use of reply.pid were located by search; audit those full functions when assigning owner. |
| Actor visits output is `actor.visits.map { $0 + 1 }` | [ActorOrchestration.swift](../../runner/Sources/PWRunnerCore/ActorOrchestration.swift), lines 430–449; declaration-derived visit construction located by search | G51's “activated” qualifier is wrong; separately report activation evidence. |
| Old open_read/open_write/create fail on fd < 0; positive descriptors succeed; ignored read/write/close results do not change rc | [pw_probe_runner.c](../../controller/tools/pw_probe_runner/pw_probe_runner.c), lines 434–490 | G85 correction and G100 operation distinction. |
| Standalone helper deserializes CheckRequest containing policy and does not gate `contract`; supports `--request` file or stdin and usage/read/parse exits | [sbpl-check.rs](../../controller/src/bin/sbpl-check.rs), lines 35–75 and 375–450 | G31/G34 entry boundary. Its full check/compile function remains inherited/document-only in this pass. |
| Augments append newline and contents in requested order | [augments.rs](../../controller/src/augments.rs), lines 250–282 | G38 is S for ordering only; resolver's other branches/tests remain D/I. |
| Present after_termination decodes non-optionally; missing means nil | [PWRunnerRequest.swift](../../runner/Sources/PWRunnerCore/PWRunnerRequest.swift), lines 186–199 | Preserve null exception, G02/G10. |
| Present actor equipment override map rejects empty and allows selected/unentitled keys; missing nil | [PWRunnerRequest.swift](../../runner/Sources/PWRunnerCore/PWRunnerRequest.swift), lines 275–295 | Preserve omission default and refusal scope, G02/Q-01. |

During this map's preparation, `5e51300d620e2a3ead419380977212d2c3e41ba1`
added `run_flow.rs`'s
`compiled_profile_labels_determine_the_public_admission_outcome`. This pass
read the complete added check: a synthetic app and constructed host reply
exercise the orchestration path using the compiled-profile corpus. Assertions
cover one invocation, exit 0/1, result ok, finished/malformed_runner_response,
retained structurally decodable runner result, absent fallback policy check,
and withheld sandbox diagnostics for invalid labels. R-06 is closed at this
constructed-test grade (T here; execution reported by the parent executor,
not rerun here). This establishes public classification/retention behavior
for that corpus, not fresh native receipt production or request nonce binding.

## Unresolved meanings, behavioral choices and evidence work

These dispositions keep uncertainties visible. They do not authorize silently
retiring a promise or changing behavior. Stage one states current behavior;
stage two uses the plan's executor/maintainer ownership and pause gates.
R-07, R-20, R-34, R-36's consequential applicability choices, R-37 and any
retirement/change of an unclear public promise must use that decision process.

| Item | Question / current disposition / next evidence |
| --- | --- |
| Q-01 entry-path matrix | Enumerate CLI parsing, decoded saved specimen, direct XPC, standalone sbpl-check, reply readers, PW build environment and every accepted `_test_overrides` field/effect. Name caller/build applicability and whether assertions gate each operation. Signed overrides are accepted behavior to describe, not an implied authorization policy. R-12 remains a behavioral decision. |
| Q-02 exact identities | Import public identity walk, clean-tree/tag conditions, two-tag refusal and build env override from owning source/checks; distinguish internal hash and wire fingerprint. Direct Cargo/build-env experiment is unrun. |
| Q-03 development reuse | There is no asserted release row for a development digest. State exact admission and manual review; decide/document a usable comparison workflow without inventing digest-to-release derivation. |
| Q-04 refusal completeness | Build complete field/default/code catalog from actual decoders and semantic validators; preserve open code vocabulary, inapplicable extension operands, path string encoding and branch-dependent ordering. Do not turn the partial old code table into exhaustive evidence. |
| Q-05 numeric limits | Attach actual limits and units, reservation geometry, decoding charges, native strings, query/phase/action counts and runtime allowances. Repair broken reserve-geometry referral. G's explicit 8/256/32/5-second figures do not replace all limits. |
| Q-06 example and workflow evidence | Attach named checks/assertions/context to every example; retain unsupported part as gap. Missing-augment file preservation, held-file signed fallback and signed equipment run need additional evidence. Stage four must validate full workflows and recovery. |
| Q-07 input/compiler boundaries | Distinguish controller held parsed value/serialized request from original file bytes, helper compilation, worker compilation and separate import reads. Real signed held-input fallback and CLI-versus-direct duplicate-key semantics are unrun. Actor augmentation and allow-only fragment intent require exact source owner. |
| Q-08 predictions/relations | Define whole query_first chain and all six relations, mapped operations, target operands and unavailable pairs. Current comparisons establish observations with temporal/causal limits. Preserve empirical unknowns for native local-name and other excluded pairs. |
| Q-09 retained bytes | Attach exact prefix/capture limits and representation for foreign/malformed/unparsed helper/client/host data; helper parsed JSON and exact host frame have different retention meanings. |
| Q-10 application | R-15 four states/11 pairs and R-36 applicability need canonical definitions and shared reader corpus. Eight of 11 pairs had signed evidence in prior examination; do not infer remaining pairs from reader controls. |
| Q-11 dependency timing | R-17 ordinal ownership, R-18 clocks and R-37 global cancellation are current account. Parked source exit before final activation timestamp needs independent exit witness experiment; source read alone does not establish its timing feasibility. |
| Q-12 live transport | Preserve no replay after invoked and exact preflight boundaries. Genuine foreign signed-host nonreceipt, unbound-peer branches and bounded request/reply faults need named controls. Client-side instrumented observation is narrower evidence. |
| Q-13 registry/ownership | Define legacy/retired alias projection, opaque unknown-metadata preservation, pending cleanup and absence rules. Unknown-metadata round-trip/disk persistence and flattened pending CLI path require evidence; label prefix alone establishes no ownership. |
| Q-14 wire/check correctness | Fill primitive boolean/endian/value definitions; distinguish generated stored structure from handwritten decoding/projection. Missing Rust malformed variant/count/order-key/byte/nesting controls and host writer frame-cap branch remain evidence work. |
| Q-15 large frames/deadlines | Receiver budget, client capture cap, full collection and outer deadline are distinct. Live 92–128 MiB outcome reachability is unestablished; constructed truncation classification is still a useful required check. |
| Q-16 worker identity/build | Actual regeneration owner, precompile/presign checks, bootstrap/header read/write boundaries and old-worker refusal must be supported precisely. Post-sign recheck refusal and old ordinal-era worker run are unexecuted branches. |
| Q-17 launch scope | Reconcile actor empty environment/descriptor record with exec child setup and guide's ordinary-worker environment statement. Describe each launch boundary and actual observation; do not infer one from another. |
| Q-18 empirical claims | Find retained environment/source/test receipts for filter ID exploration, global ID 12, macOS 14.8.3 exec baseline and verify timing. If unavailable, keep historical observation and missing evidence explicit, not universal guarantees. |
| Q-19 new guide corrections | Source confirms PID, visits and fd-sign corrections. Add meaningful check owners while drafting; current public document should state source behavior, not inherit conflicting guide prose. |
| Q-20 value catalogs and scopes | Resolve every currently abbreviated list from schema/source: controller/host outcomes, lifecycle states/bases, collection/cleanup/clock vocabularies, diagnostic origin and missing-reason applicability. R-35 adds per_actor. R-38 subjects/scopes are additive work; R-20/R-34 consequence changes need maintainer. |
| Q-21 timeout precedence | Guide's runner_timeout catalog omits its own policy-transfer timeout branch. Confirm source/control for short-delivery publication precedence and present both timeout origins with separate child/client deadlines. |
| Q-22 validator protocol | Name NDJSON record grammar and its producer, primitive acceptance, association, raw diagnostic retention and semantic effect. Existing high-level mention is insufficient for an independent reader. |

The drafting handoff must preserve R-11's unresolved acquired-decision
promise, R-13's live-inspection evidence gap, R-15's three implementations,
R-19's boundary consequences, R-20/R-34's projection behavior, R-29's release
history defect, R-36's ordinary/preparation/degraded definitions, R-37's
global cancellation and R-38's finding scopes. Settled R-01–R-05 meanings,
R-06's constructed orchestration check and the current receipt correction are
inputs, not questions to reopen by wording.

No repository tests, builds, release commands, commits or publications were
performed for this map. The next concrete unit is to assign the inventoried
meanings to structured definitions/rules/examples/known gaps and attach exact
owners; source/check reading must settle each D/I limitation or leave its
label visible before the generated document claims stronger support.
