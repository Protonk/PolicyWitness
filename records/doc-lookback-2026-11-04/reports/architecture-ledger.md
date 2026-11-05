# Architecture reader coverage ledger — stage 2A

Baseline: `ea64218b` (`lookback-ea64218b`). Scope: accepted A01–A22 in `architecture-scope.md`. This is a bounded reader assessment, not a behavioral implementation audit.

## Exposure and interpretation rules

The complete baseline ARCHITECTURE was read before questioning; truncated tool output was recovered in chunks. A0 used only the onramp and actor request. A1 used only those and ordinary process knowledge. A2 read the complete architecture and produced the initial task result. A3 read the accepted scope map and followed the existing failure-contract link to `tests/FAILURE-PROPAGATION-CONTRACT.md`, **Worker disposition record → Native extension evidence**, lines 187–377. No other reader-facing document was opened. A heading/keyword search of that contract preceded the section read; it was navigation, not a full-contract review.

For this audit, the topology, boundaries and BYOXPC DOT text and SVG XML labels, node/edge titles and relationships were inspected. They were **not visually rendered**. No assessment here concerns overlap, legibility, color contrast or visual layout. The document graph remains context except its three accepted coverage-ownership units. No source, tests, manifests, generators, other reports or trials were inspected. Citations printed inside the allowed document were read as document claims, not followed as implementation evidence.

Origins: **I** = initial-task observation/understanding in A2 (or explicitly identified A1 reasoning); **Q** = prompted questioning in A3; **A** = audit-only. An A disposition does not mean a first-reading failure was observed. Repeated locations inherit their question's origin, but their individual inventory coverage is audit work.

Every retained implementation or coverage statement below is a **checkable assertion, unverified here**. A source/test citation identifies a potential checking route; it is not evidence that the behavior or assertion holds. This qualification applies to every table row's complete Sources/Checks/Limits cells. Exact numeric values and named symbols need reference ownership, not repetition in explanatory prose. 'Retain' means retain the informational function, not certify every byte or implementation assertion. 'Combine' means only if the stated reading need remains available. Questions distinguish observed textual problems from candidate edits.

## Findings and resolving questions

- **F1 — public actor applicability (I):** 20–27, 75–82, 165–178, `actor_plan` at 445, B17/B19 at 467/469, actor-driver verification at 547–551. One run says only the single-worker driver is publicly reached and actor support is internal; other passages describe actor execution and public normalization. Consequence: cannot reliably select the public execution path or its validation requirements. Strong readings: actor normalization may be public while execution remains internal; alternatively the no-public-execution prose is wrong. Neither is established. **Question:** which admitted forms reach which driver at this baseline? **Edit idea:** state a form-to-driver map once and qualify the timeline; do not choose the apparently newer wording without evidence.
- **F2 — delivery wait chain (I):** 75–82, T16/T17 at 140–141 and 150–151, B18/B19 at 468–469. Parked validation, acknowledgment and usable settlement are clear, but sender completion versus answer/settlement and next activation are not narrated. Consequence: the polling proposal cannot be settled as a mere local change; circular wait remains a conditional concern. **Question:** what gates sender action/phase completion and recipient activation, including failure or unknown quiescence? **Edit idea:** one actor transfer sequence with the blocking dependencies, without copying all wire fields.
- **F3 — pre-call marker overstatement by this reader (Q):** architecture 238–241 and linked contract 324–340. My A2 table said a native consume marker meant 'A native call began.' That was too strong; architecture already says pre-call. After questioning and contract reading, I withdrew it: only publication of a pre-call boundary is established, not native entry, return or effect. This is an observed initial reader error, not proof of defective architecture wording. **Optional edit idea:** a short 'not proof of native entry' qualification could help; normative detail belongs in the existing contract.
- **F4 — execution-form scope of timeline and timing (Q):** 160–178, 180–232, 330–377, T15/T16 notes. First timeline is declaration-only; second is singular-worker and omits actor activation/delivery. Actor setup/lifetime/exchange limits are scattered away from the timing account. **Question:** which general phase/budget statements also apply to actors, unapplied and empty visits? **Edit idea:** label both timelines, then add only the actor differences and budget relationships. Exact limits can remain in LIMITS.
- **F5 — issuer helper dependency (Q):** 68–82 versus 147, 733–738 and X27 at 815. Actor form explicitly needs no issuer; missing-issuer refusal is broadly described for extension specimens. **Question:** which forms actually require the issuer? **Edit idea:** qualify capability statements by form. This is a textual scope conflict, not an established runtime defect.
- **F6 — optional evidence and fallback form association (Q for fallback; A for capture):** 61–66, 285–291, 397, `profile_capture` 438, B12 461, 489–493. Compilation fallback and optional receipt use singular policy/worker terminology. **Question:** are they admitted for actors, how is actor identity represented, and what does unapplied mean for capture? **Edit idea:** a short applicability statement plus field-reference links; no need for the full optional schema here.
- **F7 — setup/sandbox wording (A):** topology `worker` 116 and T9 135 versus 25–27 and T15 139. Generic 'yes; applies ... to itself' and 'after apply' do not naturally describe unapplied actors. **Question:** do these labels denote specimen-applied sandbox state or the executable's usual role? **Edit idea:** qualify role/state and exec applicability. Minor terminology concern unless readers use it to infer applied setup.
- **F8 — environment scope (A):** T15 139 explicitly says empty actor environment; 740–741 says worker environment unrecorded. These can coexist (configured input versus recorded observation), but scope is unclear. **Question:** is unrecorded a statement about evidence rather than unknown launch configuration, and does it cover both forms? **Edit idea:** distinguish configured environment from observed/retained environment; do not call this a proven contradiction.
- **F9 — evidence writer shorthand (A):** Transfer row 391 says 'none: the host copies, compares and acknowledges'; T17 assigns recipient acknowledgment to the parked worker. These can coexist as different acknowledgments. **Question:** can the row explicitly distinguish recipient acknowledgment, host answer and source acknowledgment? **Edit idea:** shorten the native-result cell to 'none; host transport exchange' and retain the detailed writer ownership. Minor clarity issue, not a factual contradiction.
- **F10 — graph compression (A):** topology T8 arrow is worker→host but its table includes host→worker release; T17 host→worker includes reciprocal acknowledgment. A single worker node represents multiple actor processes. Boundaries graph has no visible edge out of `actor_plan`. These diagrams work as indexed inventories but alone do not trace the actor control/data path. **Question:** is the diagram meant as inventory or complete flow? **Edit idea:** explain aggregation and connect the actor plan to execution in prose or a small trace; retain useful compact IDs.

Task conclusion remains conditional: deferring recipient acknowledgment changes a documented parked transport mechanism and can encounter bounded exchange expiry; exact circular wait depends on the missing completion/activation chain. Publication, custody, recipient acceptance, equality/settlement, source completion, consumption and effects remain distinct. The linked contract clarified host/source timeout asymmetry after questioning. No run success was inferred from the example.

## Prose and timeline units

Each row covers every substantive sentence in its listed range. Adjacent claims are grouped only where they serve the stated purpose. All line numbers refer to baseline ARCHITECTURE.

| Scope / lines | Origin | Purpose, clarity, ownership and necessity disposition |
| --- | --- | --- |
| A01 3–6 | A | Retain orientation and reader route: defines a tour between README and directory references. Appropriate scope; no need to reproduce those references. |
| A01 8–16 | I | Retain the limits of generated citation checking and Known-gap navigation. Symbol/test presence is not behavioral verification. Can shorten generation mechanics here because the later verification section owns them; preserve that qualification. |
| A02 20–27 | I | Retain causal explanation for fresh processes and one-way application, including no apply for unapplied actors. Central architectural rationale, not substitutable by a symbol link; public applicability F1 remains. |
| A02 29–36 | I | Retain independent host reply path and publication/disposition source distinction. Concrete deny-default example explains why shared mapping exists. Detailed disposition schema belongs at linked contract. |
| A02 38–43 | I | Retain host lifetime, separate controller envelope and Swift bridge explanation. Small overlap with topology is useful causal prose plus inventory, not needless duplication. |
| A02 45–52 | I | Retain reservation/acquisition/invocation/retirement distinction; directly limits safe retries. Exact capture fields appropriately delegated to guide. |
| A02 54–56 | I | Retain full reply-loss limitation and no retrieval/replay. Necessary qualification to fresh-host/reply rationale; later index should link rather than restate. |
| A03 58–60 | I | Retain separate unsandboxed validator and held live target: explains prediction ownership. Actor/unapplied phase applicability belongs with F4. |
| A03 61–66 | Q | Retain fallback trigger and separate compilation context. F6 asks actor association; automation link is appropriate optional operational detail. |
| A03 68–73 | I | Retain declaration issuer authority, timing, token channel and evidence minimization. Explicit form qualification is useful; could combine with first timeline without losing authority rationale. |
| A03 75–82 | I | Retain actor-native issue, host custody, parked delivery servicing, serial activation and failed-actor reap requirement. Central to proposal; F1/F2 need scope and gating detail, not removal. |
| A03 84–89 | I | Retain sandbox-API owner inventory and host separation. Checks are routes, not proof. Can reduce duplication with topology API column while keeping rationale visible. |
| A04 93–98 | A | Retain bundle-location granularity and bundle-local helper resolution. Exact paths appropriately delegated to README; useful to understand BYOXPC. |
| A05 160–164 | I | Retain phase collection/release and limited query_first meaning; qualify all-phases/single-worker statement (F1/F4). Contract link is appropriate for exact required evidence. |
| A05 164–171 | I | Retain session ownership and driver routing explanation but resolve public path conflict F1. Source-file tour can be shortened to the ownership distinction and links. |
| A05 172–178 | I | Retain serial actor/session/parked-wait explanation. No-public-request assertion conflicts in scope with other passages; neither statement may be silently preferred (F1). |
| A06 180–186 | I | Retain declaration admission, preparation, bounded issuance, clean-reap delivery gate and submitted-target preservation. Properly scoped; preparation is not effect evidence. |
| A06 188–198 | Q | First timeline: retain each listed host/issuer operation and channel as a declaration sequence: resolve, map/spawn, issue/publish, erase/exit, reap, validate, pass fd 5. Can combine nearby prose; explicit declaration label already supplied. |
| A06 200–209 | Q | Second timeline entry/setup: controller gates/selects/augments/serializes; EOF/XPC; host authorize/decode/admit/map/spawn; worker compile/ready/apply. Retain sequence but label single-worker form and qualify unapplied applicability F4. |
| A06 210–223 | Q | Second timeline phase loop: arrival/ownership/planning/validator/collection closure/recheck/release/ack/actions/completion/repeat/erase/done. Retain barrier flow; lacks actor activation and transport, so cannot stand as actor trace (F2/F4). |
| A06 224–232 | Q | Second timeline termination/reply: exit request/grace/reap/snapshot/disposition/evidence/erasure/reply/version admission/optional logs/envelope. Retain observer separation; nearby prose correctly prevents treating reply time as execution end. |
| A07 234–238 | I | Retain unavailable collection versus live waiting worker release eligibility, broken phase/ownership suppression and per-action publications. Directly explains partial progress; do not replace with result-code summary. |
| A07 238–244 | Q | Retain pre-call/result distinction and same-phase state changes after query. F3 records reader overstatement and prompted correction. Short explicit native-entry disclaimer optional, detailed statuses remain contract-owned. |
| A07 244–248 | I | Retain autonomous terminal exit, retained mapping and post-reap acknowledgment under unbroken ownership including abnormal exit. Necessary to avoid interpreting missing done as no prior action. |
| A08 250–257 | A | Retain admission/selection ordering as a checkable source route. Detailed function list can shorten if sequence remains; no independent validation of cited orchestration checks. |
| A08 258–267 | A | Retain declaration preparation/issuer cleanup and independent erasure checks. Could collapse source/test enumeration into a compact route; clean-reap gate must remain. |
| A08 268–269 | A | Retain authorization before request reading; short and distinct from semantic admission. |
| A08 270–273 | A | Retain closed-key/capacity/meaning/hash ordering and refusal without spawn. Public actor normalization insertion/order unclear under F1; do not assume cited symbol list resolves it. |
| A08 274–279 | I | Retain per-phase replanning and unavailable query without suppressed attempt. Essential distinction between query scope and attempted effect; exact exclusions can remain reference-owned. |
| A08 280–284 | A | Retain setup/ready-window route, but mainly source directions rather than explanation. Can combine with timeline/timing; unapplied setup needs F4 qualification. |
| A08 285–291 | A | Retain opt-in capture producer/stage and admission integrity gates. Scope/actor identity question F6; linked guide appropriately owns detailed receipt reading. |
| A08 292–298 | I | Retain barrier ownership checks, exact ordinal and independent per-phase ordering. Mutation-control route useful for this change; cited tests not inspected. |
| A08 299–302 | A | Retain per-slot completion and exec acquisition/release lifetime. Exec not in example but informs resource boundary; after-apply scope F7. Worker tour can own syscall detail. |
| A08 303–310 | I | Retain erasure-before-done and independent host cancellation/cleanup plus acknowledgment restrictions. Some overlap with 244–248 can combine; abnormal evidence distinction must remain. |
| A08 311–315 | A | Retain reply version admission, fallback trigger, disposition projection and envelope assembly; can shorten function list. F6 applies to actor fallback. |
| A09 317–325 | I | Retain timeout ending observation rather than execution, unconfirmed reap and no global deadline. Central partial-evidence limit; no safe compression to timed-out means stopped. |
| A09 327–328 | A | Retain focused worker-tour link for exec descendants and cleanup. Appropriate dependency, not missing architecture prose. |
| A10 330–335 | Q | Retain issuer clock start and excluded preparation/spawn/overrunning cleanup; explicit declaration scope. Explains nested budget composition, numeric values belong to LIMITS. |
| A10 335–345 | Q | Retain delivery, ready, sentinel and collection allowance boundaries including excluded synchronous collections and cleanup overrun. F4: singular driver account lacks actor composition; do not assign it globally. |
| A10 345–353 | Q | Retain proceed/grace/exec allowance distinctions and continuous Mach-time domain versus host clocks. Clarify actor/unapplied applicability; exact budget constants remain linked. |
| A10 354–359 | Q | Retain elapsed allowance/polling cost/expiry-starts-cleanup qualification. Can combine repeated limits routing; cannot remove distinction from total response time. |
| A11 361–369 | Q | Retain nonblocking policy delivery, timeout versus errno and host write counts versus worker receipt. Explains an important independent observation, not merely pipe mechanics. |
| A11 369–377 | Q | Retain EOF length refusal before compile and no shorter valid-prefix application, independent controls and cleanup/client-timeout limits. Check names can shorten; actor/unapplied setup scope remains F4. |
| A12 381–383 | I | Retain native single-writer and additive host/controller observations. Foundation for table interpretation; avoids inferred causation. |
| A12 400–406 | A | Retain path-enrichment/excluded-query ownership and normative contract route. Source symbol repetition could shorten; appropriate division between tour and contract. |
| A13 410–418 | A | Retain cross-owner records/guards, local version versus co-shipping/golden identity distinction. Concrete offsets/version values belong table/reference. Do not infer versioning adequacy without source review. |
| A14 483–487 | A | Retain validator framing/association, prior complete evidence and test-seam trust limit. Co-shipping is expressly not authentication; important qualification to graph guard shorthand. |
| A14 489–493 | Q | Retain fallback helper kind/version gating and opaque rejected output. F6 asks actor applicability; framing detail appropriately linked to contract. |
| A15 497–498 | A | Retain verification-mechanism purpose and suite-reference route; does not claim tests were run in this review. |
| A15 500–506 | A | Retain golden shapes/types/reader allowlists and ABI harvest plus candidate-review workflow. Could shorten workflow detail; useful to understand schema change boundaries. |
| A15 507–524 | A | Retain distinction between manifest-owned facts, source-derived identity, generator checks, explicit prose baseline and runtime evidence manifest. Most implementation mechanics are context; compress enumeration with links, preserving limits of mechanical verification. |
| A15 525–528 | A | Retain non-generated source-drift rules and equality checking mechanism. Useful check category; not independent behavior evidence. |
| A15 529–532 | A | Retain consumer role, exact versions/raw-channel validation and external-reader relevance. Normative reader requirements belong linked contract, implementation not examined. |
| A15 533–541 | A | Retain request controls, echo-does-not-prove-reach, injected-process versus separately compiled native fixtures. Necessary evidence-boundary distinctions, detailed key list appropriately external. |
| A15 542–546 | A | Retain C-harness independent worker/ABI boundary, activation wait, unapplied setup and worker policy-hash claims. Useful independent producer check, not public integration evidence. |
| A15 547–551 | A | Retain actor-driver kernel/PID/publication observation claims rather than scheduler labels. Resolve F1 public support status and avoid treating internal checks as public integration evidence. |
| A15 552–555 | A | Retain lifecycle oracle reliance on raw facts and disabled unrelated evidence. Distinct verification purpose; behavior remains unverified. |
| A15 556–560 | A | Retain artifact preflight and damaged/importing-host controls. Build checks are useful apparatus validity context; can shorten detailed inventory without removing host separation. |
| A16 589 | A | Retain guide node: copied extension coverage and sole shipped-document role identifies ownership. This row is substantive even though most document-graph mechanics are context. |
| A17 626 | A | Retain extensions_md node: identifies shared extension coverage owner, useful to avoid editing copies. Exact ownership unverified outside prose. |
| A18 702 | A | Retain D63 relation extensions_md→gen_limits for copied coverage. Compact link can preserve need; no generator audit claimed. |
| A19 711–720 | A | Retain BYOXPC Mach-service variant, bundle-local resolution, selector stripping and worker versus validator/issuer signing authority. Distinct from install procedure; do not remove authority distinctions. |
| A19 721–729 | A | Retain recursive seal/read-back and pre-invocation hashes versus baselines. Clear observation time; full provenance interpretation appropriately guide-owned. |
| A19 730–738 | Q | Retain old-record unknown observations and compatibility; administrative recovery link is context. Broad missing-issuer refusal needs F5 qualification. Shared-control assertion is checkable, not verified by cited filenames. |
| A20 740–741 | A | Retain host env versus worker/exec distinction, but clarify configuration versus recorded observation (F8). Minor uncertainty, not demonstrated inconsistency. |
| A20 743–750 | A | Retain verify consumes a real reserved host and worker-only true entitlement gate. Timing exact value may remain reference-owned. These operational surprises justify prose outside installation instructions. |
| A22 827–834 | A | Retain Known gaps index and navigation to full reply-loss limitation. It cannot certify completeness of all gaps. Do not add textual ambiguities as runtime Known gaps without behavioral evidence. |

## Generated tables and associated diagram elements

These are row-level dispositions for all accepted rows, including every column and its qualifications. Diagram nodes/edges with the same IDs inherit the row disposition **plus** the figure-level assessment below; graph labels are concise indexes, not replacements for full table semantics. Row locators are exact baseline line numbers. Native meaning/ownership and guard cells are assessed here; Sources/Checks are unverified checking routes and Limits are appropriate numeric-reference dependencies under the exposure rule above.

### A04 topology

| Line / ID | Origin | Purpose and retention / clarity assessment |
| --- | --- | --- |
| 112 / `user` | A | Retain caller ownership of request/envelope: establishes the outer boundary; no further user-process detail needed. |
| 113 / `controller` | I | Retain one-run Rust envelope owner with no sandbox API; explains independent reporting even if host fails. |
| 114 / `client` | I | Retain Swift connection owner and one absolute acquisition/execution deadline; complements reservation prose, can shorten language/location duplication. |
| 115 / `host` | I | Retain one reservation/at-most-one-execution owner and no-native-API custody role; best-effort flush is material. Exact delay can live in limits. |
| 116 / `worker` | I | Retain fresh process per actor, repeated visits, API owner and autonomous exit. Generic Sandboxed yes conflicts in scope with unapplied qualifier (F7); do not infer application from node styling. |
| 117 / `exec_child` | A | Retain inheritance and descendants-not-contained limitation. Distinct lifetime from worker; worker-tour link can own detailed cleanup mechanism. |
| 118 / `validator` | I | Retain separate per-collection unsandboxed PID query producer. Exact eligibility and empty/unapplied phase behavior need F4 account. |
| 119 / `sbpl_check` | Q | Retain compile-only controller fallback and admitted xpc_error trigger; F6 asks actor-policy association, not elimination of helper. |
| 120 / `launchd` | A | Retain OS launch role outside policy. Table duplicates diagram cluster usefully; no further OS detail required. |
| 121 / `issuer` | I | Retain declaration-only ordinary-authority native issue and clean-reap requirement. Clear scope is model for broad capability statements (F5). |
| 127 / `T1` | A | Retain argv/stdout outer channel; compact and distinct. |
| 128 / `T2` | I | Retain spawn-once, EOF request and versioned stdout capture; prevents confusing client capture with host reply. |
| 129 / `T3` | I | Retain effect-free reservation versus single submission/reply channel; essential retry boundary. |
| 130 / `T4` | A | Retain launchd XPC/Mach-service variation; detailed service installation belongs elsewhere. |
| 131 / `T5` | I | Retain policy/evidence/ready descriptors and optional declaration channel; label its form so actor fd 5 is not misread as the same protocol. |
| 132 / `T6` | I | Retain fresh per-eligible-phase validator, bundle default/override and bounded NDJSON; eligibility is not universal spawn. |
| 133 / `T7` | I | Retain query target PID and no-report flag; native observation distinct from worker attempt. |
| 134 / `T8` | I | Retain immutable arrival/ack/completion, numbered release and separate results. Diagram arrow aggregates opposite directions (F10); specify phase acknowledgment distinct from transfer acknowledgment. |
| 135 / `T9` | A | Retain exec-after-setup acquisition and bounded streams; after-apply wording needs unapplied qualification if actor exec is supported (F7). |
| 136 / `T12` | Q | Retain fallback helper channel and trigger; form mapping unresolved F6. |
| 137 / `T13` | Q | Retain declaration issuer fd/stdout/environment authority; broad missing-capability note needs form qualification F5. |
| 138 / `T14` | I | Retain transient bounded token versus publication and host eligibility/cleanup; token bytes must not become JSON evidence. |
| 139 / `T15` | I | Retain actor-specific launch, private authority mapping, activation ordinal and lifetime cutoff. Central separation from declaration fd 5; supplies setup/environment facts absent main timeline. |
| 140 / `T16` | I | Retain one-shot outbound issue and distinct transfer answer cells with custody ownership. F2 needs completion gating; timeout/reuse note is essential, exact duration can remain linked. |
| 141 / `T17` | I | Retain parked recipient framing/identity check and acknowledgment without consume. Settlement/equality and erasure notes are central to proposal; do not replace with generic successful-transfer wording. |

| Notes lines / ID | Origin | Disposition |
| --- | --- | --- |
| 145 / host | I | Retain reservation owner/expiry/disconnect rules; duplicate of opening but useful beside lifetime inventory. Could link opening instead if precise execution-owner qualification survives. |
| 146 / T5 | Q | Retain delivery deadline, byte-count/EOF comparison and before-compile refusal. Can link full 361–377 account; preserve host count versus worker receipt distinction. |
| 147 / T13 | Q | Retain cleanup-overrun qualification; exact wait value belongs limits; extension-specimen capability scope F5. |
| 148 / T14 | I | Retain bounded storage and never-retained raw token rule. Exact capacity is reference detail. |
| 149 / T15 | I | Retain who maps each region and isolation from other actors/validator; setup/lifetime limits need main timing connection F4. |
| 150 / T16 | I | Retain per-side exchange timeout as transport evidence and no stale-cell reuse. F2 asks exact wait chain, not longer timeout. |
| 151 / T17 | I | Retain equality before usable/withdrawn settlement, consume gate and separate custody/shared-erasure times. Necessary non-native authority lifecycle; no safe deletion. |

### A12 evidence channels

| Line / row | Origin | Purpose and retention / clarity assessment |
| --- | --- | --- |
| 387 / `Prediction` | I | Retain validator producer, host unavailable/path additions and steps[].sandbox_check landing. Explicit unavailable is not native verdict. |
| 388 / `Attempt` | I | Retain worker publication versus host copies/path diagnostics and attempt rc/errno landing; results alone do not establish sandbox cause. |
| 389 / `Extension preparation/issuance` | I | Retain declaration issuer-native versus host target/cleanup observations and extensions[] landing. Add form label if table used independently; actor form lacks this array per linked contract. |
| 390 / `Native lifecycle` | Q | Retain worker marker/result versus host association, actor metadata and extension_events[] landing. F3 corrects reader overclaim: marker is pre-call, not native entry. |
| 391 / `Transfer` | I | Retain transfers[] host exchange with no native result. Clarify distinct acknowledgments F9; linked contract resolves them after questioning. |
| 392 / `Resources` | I | Retain reference/owner/last-use join, not independent native producer. Essential to trace ta/db/hb and tb/dc/hc. |
| 393 / `Actor disposition` | I | Retain per-actor raw-fact host disposition versus controller projection and actor-indexed landing. No singular-worker substitute. |
| 394 / `Fresh read` | I | Retain separate syscall results/descriptor identity/bounded bytes and fresh_read landing. Independent effect observation rather than consume result. |
| 395 / `Comparison` | I | Retain host classification, submitted-scope/order/limitations. No native writer or prediction/enforcement agreement claim. |
| 396 / `Disposition` | I | Retain singular-worker host fact-derived versus controller projection, but label single-worker applicability beside actor row. |
| 397 / `Compiled-object receipt` | A | Retain before-apply worker copy and admission gates. Singular landing prompts actor applicability question F6; optional schema detail belongs guide. |
| 398 / `Dossier` | A | Retain controller-owned submitted request/augmentation/imports/host/provenance/pre-invocation hashes. Distinct from runtime effect and suitable concise inventory. |

### A13 boundaries

| Line / ID | Origin | Purpose and retention / clarity assessment |
| --- | --- | --- |
| 432 / `request_file` | A | Retain caller-owned versioned JSON start; clear record boundary. |
| 433 / `held_request` | A | Retain controller-owned one serialization, stripped selectors and augmented inputs; explains what crosses XPC. |
| 434 / `run_spec` | A | Retain host-decoded closed-key record; distinct owner from held bytes. |
| 435 / `shm_region` | I | Retain host inputs/worker outputs and fixed ABI identity; offsets are reference detail, diagram label combines pipe and region acceptably as one interface. |
| 436 / `validator_wire` | A | Retain bounded co-shipped NDJSON and local marker; exact version is reference-owned and does not authenticate override. |
| 437 / `reply` | A | Retain host reply schema versus controller envelope; golden is shape guard, not behavior proof. |
| 438 / `profile_capture` | A | Retain worker-before-apply producer versus host admission and nonce/schema. F6 asks actor-indexed or unavailable semantics. |
| 439 / `envelope` | A | Retain controller ownership and framing distinction; compact mapping useful. |
| 440 / `helper_envelope` | Q | Retain separate compile helper nested envelope and kind; actor fallback applicability unresolved F6. |
| 441 / `evidence_manifest` | A | Retain build-owned binary hash/entitlement record and own schema. Runtime provenance dependency, not generation audit. |
| 442 / `runner_registry` | A | Retain additive loading and recovery aliases as selection boundary; details appropriately outside tour. |
| 443 / `extension_preparation` | I | Retain declaration references/paths versus host resolution/metadata; before-issuer identity is not later-open identity. |
| 444 / `token_channel` | I | Retain host mapping/issuer publication/worker consumption-erasure ownership, descriptor closure and no JSON. Declaration channel differs from authority_region. |
| 445 / `actor_plan` | I | Retain normalization owners/producers/last-use map. Public-admission wording participates in F1; graph stops at plan so F10 asks connection to execution. |
| 446 / `authority_region` | I | Retain per-actor slot/answer-cell and host-only custody ownership. Header inventory can link deeper reference, but commit/ack/settlement distinction is essential. |
| 452 / `B1` | A | Retain version/selector/augmentation gate before held serialization; no new semantic defect found. |
| 453 / `B2` | A | Retain authorization/decode/capacity/meaning/hash boundary. F1 leaves actor normalization path uncertain, not proven wrong. |
| 454 / `B3` | A | Retain identity/count/partition/length/timebase pre-policy refusal guard. Graph exit-4 label is more implementation-specific than table prose; exact exit code unnecessary to central explanation. |
| 455 / `B4` | I | Retain release/acquire, ordinal/time decision, native consistency and raw disposition gates. Dense but useful; can split lifecycle versus ordering explanations without losing conditions. |
| 456 / `B5` | A | Retain phase-fresh planning and bounded strict per-phase association; exact framing belongs contract. |
| 457 / `B6` | A | Retain correct phase/step join or explicit unavailable; prevents filling missing predictions with guesses. |
| 458 / `B7` | A | Retain exact reply-version gate, validated projection and opaque refused reply. Necessary separate controller boundary. |
| 459 / `B9` | Q | Retain unchanged nested helper plus kind/version gate; F6 concerns which actor compilation, not frame validation. |
| 460 / `B10` | A | Retain exact path/kind baseline association; prevents treating any same-named binary as selected artifact. |
| 461 / `B11` | A | Retain registry target resolution and stripped selector before XPC; complements held-request row. |
| 462 / `B12` | A | Retain apply/completion/PID/nonce/identity/integrity capture gate; F6 asks applicability to unapplied/multiple actors. |
| 463 / `B13` | A | Retain declaration reference/order/capacity/exec admission before preparation. Distinguish declaration exec exclusion from per-actor B17 exclusion; exact caps reference-owned. |
| 464 / `B14` | I | Retain target preparation, native issuance, clean reap and bounded publication before delivery; scope declaration. |
| 465 / `B15` | I | Retain separate token transport and ordered worker evidence. Erasure is not native release; fatal interruption qualification essential. |
| 466 / `B16` | I | Retain no-token-byte issuer/authority/cleanup reply projection; declaration evidence boundary. |
| 467 / `B17` | I | Retain declared actors, owning phases and single-assignment producer-before-owner-use references plus per-actor exec exclusion. F1 applicability unresolved; caps can remain referenced. |
| 468 / `B18` | I | Retain framing/writer/action/token indexes, writer responsibility and equality before credit. Writer stands behind it needs F2 operational ownership explanation; not proof from mere issue rc. |
| 469 / `B19` | I | Retain actor-phase/resource-owner association, no native transfer result and setup/acknowledged-release gate. Distinguish this phase release from parked delivery ack; central partial-evidence guard. |

| Notes lines / ID | Origin | Disposition |
| --- | --- | --- |
| 473 / B4 | I | Retain autonomous terminal erasure/exit and post-reap reconciliation only with unbroken ownership; poll stop, deadline and disposition are independent. Can link fuller lifecycle prose. |
| 474 / B13 | A | Retain declaration cap reference here or link LIMITS; no need to repeat exact values in narrative. |
| 475 / B15 | I | Retain ordinary erasure versus fatal interruption and explicit native release distinction. Independently important from byte-equality gate. |
| 476 / B17 | A | Retain actor admission cap reference here or link LIMITS. Separate limits prevent applying declaration cap to actor form. |

### A21 selected BYOXPC rows

Only the accepted rows below are substantive; installation/removal administration elsewhere remains context.

| Line / ID | Origin | Purpose and retention / clarity assessment |
| --- | --- | --- |
| 765 / `bundle_copy` | A | Retain copied executable inventory/build signatures versus installer ownership; CFBundleIdentifier service-name assertion is checkable, not verified. |
| 766 / `entitlements_plist` | A | Retain host and worker supplied entitlements versus query helper authority; process whose policy is applied needs unapplied qualifier F7. |
| 767 / `install` | A | Retain sign/verify/read-back sequence for provenance; plist/bootstrap/env details can shorten here because installation guide owns procedure. |
| 768 / `signing` | A | Retain worker+host entitlements versus identity-only validator/issuer and nested-before-seal verification. Central authority distinction, not redundant procedure. |
| 770 / `registry` | A | Retain separate helper read-backs and unknown older observations; state names are context, not independently audited removal behavior. |
| 772 / `host` | A | Retain Mach-service listener, installed identity and bundle-relative helpers; same orchestration ownership, no need to repeat default path details. |
| 773 / `client` | A | Retain Mach-service connection with privileged system option; clear alternative channel. |
| 774 / `caller_auth` | A | Retain signed caller/Team-ID/optional allowlist guard inherited by copy; guard conditions are checkable. No actual authorization trial performed. |
| 775 / `selector` | A | Retain worker true-valued entitlement read-back gate and refusal for missing worker observation. Important limit: host entitlements do not satisfy request. |
| 776 / `provenance` | A | Retain separate read-backs and selected binary hashes before invocation, older issuer unknown. Detailed schema guide-owned. |
| 777 / `worker` | A | Retain worker authority and signature-before-seal; distinguish entitlements from specimen apply state (F7). |
| 778 / `validator` | A | Retain identity-only/no-entitlements authority; essential to query interpretation. |
| 779 / `verify` | A | Retain actual allow-all request consuming reservation, acquisition delay and no pre-grant submission. Exact wait value optional reference detail. |
| 780 / `validate` | A | Retain recursive and individual verification, conditional issuer handling and unknown absence without launchctl. Useful provenance limit; no need to reproduce CLI recipe. |
| 783 / `issuer` | Q | Retain ordinary-authority declaration helper and identity-only signing; add form qualification to associated broad refusal edge F5. |
| 791 / `X3` | A | Retain entitlement source into signing; concise ownership edge. |
| 792 / `X4` | A | Retain helper-before-bundle signing and strict recursive verification; central trust chain. |
| 793 / `X5` | A | Retain host signature+entitlement read-back; distinct from what selection consults. |
| 794 / `X6` | A | Retain worker signature+entitlement read-back; input to required-entitlement selection. |
| 795 / `X7` | A | Retain identity-only validator read-back; prevents conflating helper with worker authority. |
| 800 / `X12` | A | Retain request selector fields entering selection; exact field reference appropriate elsewhere. |
| 801 / `X13` | A | Retain id/service resolution and worker true-key rule; complements selector node, can combine in prose. |
| 802 / `X14` | A | Retain registry read-backs into dossier; these are recorded observations, not live re-verification. |
| 803 / `X15` | A | Retain actual selected-copy hashes observed before invocation; distinct from registry and execution effect. |
| 804 / `X16` | A | Retain connection scope/privilege into authorization; not the native sandbox boundary. |
| 805 / `X17` | A | Retain Team ID/identifier authorization; graph short label requires table qualifications rather than standalone universal rule. |
| 806 / `X18` | A | Retain copy-local worker spawn; worker multiplicity inherited from actor-form explanation/F1. |
| 807 / `X19` | A | Retain eligible copy-local validator default with explicit override; no automatic trust in override. |
| 808 / `X20` | A | Retain verify request into client; needed to explain consuming a host rather than passive inspection. |
| 809 / `X21` | A | Retain re-read validation and separate binary failures; distinguish from run-time selection and recorded provenance. |
| 814 / `X26` | A | Retain independent issuer identity/entitlement read-back; broad signing mechanics can link guide. |
| 815 / `X27` | Q | Retain copy-local issuer spawn dependency for declaration form; missing-helper extension refusal needs F5 resolution. |
| 816 / `X28` | A | Retain actual selected issuer path/hash versus shipped baseline and separate installed observations. Dependency should be explicitly form-scoped alongside X27. |

| Note / ID | Origin | Disposition |
| --- | --- | --- |
| 820 / host | A | Retain one locked connection-bound reservation, no stale retirement of execution owner and no replay. Duplicate of opening/topology may become a precise backlink if this figure remains independently readable. |

## Figure, structure and coverage dispositions

| Scope / location / elements | Origin | Assessment |
| --- | --- | --- |
| A04 100–110, 123–126, 153–156; topology embed 101, caption 103, summary 106 | A | Retain indexed topology diagram/table pairing and explicit presence-check limit. All 10 nodes and 15 edges covered individually above, including T12–T17 numbering. Cluster labels app top level / XPC bundle / macOS correctly supply a declared location grouping, not proof of process confinement. Full SVG XML relationship exposure; no rendered judgment. T5/T15 distinguish two fd-5 protocols; F10 notes aggregation/directions. Headings, column labels, detail wrapper and concluding citation sentence support lookup; repeated generation credits may shorten. |
| A12 379, 385–386 | A | Retain evidence-channel heading and writer/host-addition/landing/meaning columns. Strong comparison format for provenance; no new native result should be inferred from a non-native row. All 12 data rows covered. |
| A13 408, 420–431, 448–451, 471–481; embed 421, caption 423, summary 426 | A | Retain records-and-guards figure plus table index. All 15 nodes and 18 edges covered above. Controller/host/built-and-installed clusters help owner grouping; actor_plan/authority_region not joined into a full actor execution path (F10), which limits use as standalone flow. B3 short exit-code label can simplify. Verification caption is necessary; repeated generator mechanics optional. SVG XML inspected, not rendered. |
| A15 495 and 562–707 except A16–A18 | A | Verification heading is retained; document graph is context only. Most generator/copy relationships were read for orientation, not separately dispositioned as runtime claims. Three accepted extension-coverage ownership units are dispositioned above. No claim that the fourth figure was rendered or independently XML inspected. |
| A21 752–763, 785–788, 818–825; embed 753, caption 755, summary 758 | A | Retain BYOXPC figure/table framing and checked-citation limit. Installation, launch/connection, selection/provenance, bundle-local helpers and maintenance clusters explain relationships. All accepted nodes/edges listed individually above; other visible administration elements are context, not omitted substantive audit work. Table is unusually broad; a shorter substantive subset plus guide link could preserve tour needs, provided authority, provenance, compatibility and verify-consumes-host distinctions remain. XML inspected, no visual-layout judgment. |
| A01/A04/A13/A21 captions and IDs | A | Repeated source/test-presence qualification is useful at independently viewed diagrams. It cannot be shortened to verified behavior. Bare presence of a test citation does not settle whether that test asserts the row; no unsupported behavioral endorsement made. |
| Titles/section headings, blank lines, fences, generated delimiters and table separators within accepted ranges | A | Retain navigational/structural role; no standalone behavioral claims. Blank lines and invisible markers need no separate prose verdict. Timeline fences and endpoints are included in their sequence units. |

## Coverage and limits

A01–A22 are dispositioned. The prose inventory groups only connected purpose units; table rows and accepted diagram IDs have individual entries, with shared caption/cluster/structure treatment above. Complete row qualifications remain in scope even where this ledger summarizes them. The three coverage-ownership document-graph units are included; remaining document-generation and administrative rows are context per accepted scope.

No implementation truth, cited test sufficiency, numeric correctness, generated-output agreement or rendered-layout quality has been established by this reader. New audit-only questions about environment, applied-state terminology, optional capture and graph aggregation are questions/minor clarity concerns, not observed initial task failures. Prompted marker correction and prompted form-scope analysis do not erase A2's original wording or count as unaided discoveries. No native run or successful specimen observation exists in this exercise.

Additional reader-facing dependency used: `tests/FAILURE-PROPAGATION-CONTRACT.md` lines 187–377, Native extension evidence (via ARCHITECTURE's contract link); no further doc links opened during ledger work. Baseline diagram artifacts read: `docs/architecture-topology.dot` and `.svg`, `docs/architecture-boundaries.dot` and `.svg`, `docs/architecture-byoxpc.dot` and `.svg`. All path locators in this report are inert repository-relative text, so copied source links cannot resolve incorrectly from this report directory.
