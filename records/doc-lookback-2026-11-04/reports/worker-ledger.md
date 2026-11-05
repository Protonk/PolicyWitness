# Worker documentation coverage ledger — stage 2A

Baseline: `ea64218b` (`lookback-ea64218b`). Reviewed scope: all `docs/WORKER.md`, lines 1–709. Scope was accepted because actor setup, authority and lifetime cut across the account, not because every unit was presumed defective.

This is a documentation reader review, not implementation verification. The initial task was to review three fresh-access observations around consumption and a release attempt, a setup-opened descriptor, and a proposed token digest, using both declaration and actor forms. W1 used only the onramp and ordinary knowledge. W2 read the whole Worker document and followed its native evidence contract link. W3 questioned actor admission, inventory applicability, digest and failed release. This ledger records the subsequent coverage audit. Reading the whole document at W2 does not make every audit finding an observed first-reading failure.

Origins: **initial-task** = raised or used in W1/W2; **questioning** = developed during W3; **audit-only** = recorded here. Dispositions: **retain** = useful as written for the stated purpose; **concern** = identifiable reader problem; **minor/optional** = possible simplification without demonstrated failure; **factual question** = account cannot settle behavior; **unsupported** = a proposed conclusion has insufficient evidence. Retain does not certify implementation truth. A unit can be retained and participate in a cross-cutting concern.

Sources actually consulted: the two onramp packet files; complete baseline `docs/WORKER.md`; baseline `docs/worker-capabilities.svg` (SVG/XML text only, during audit); baseline `tests/FAILURE-PROPAGATION-CONTRACT.md`, **Native extension evidence** (lines 187–377). Heading discovery in that contract was navigation only. No implementation, test implementation, manifest, generator, other review report, external source or native trial was consulted. All source/test citations below are unverified pointers. Other linked references are dependencies identified by the document, not sources silently credited as read.

The Markdown figure declaration, legend, caption and complete node/edge tables are reviewed. The permitted `docs/worker-capabilities.svg` was inspected as SVG/XML: all node text, cluster labels, edge IDs and endpoint titles were read. Its rendered layout was not viewed: readability at native size is unverified, not an observed failure. Its substantive resource/relationship account is covered through the exact matching IDs below. No graphical-layout verdict is claimed.

## Findings and open questions

**F1 — conflicting actor admission account (concern; initial-task, expanded in questioning).** Lines 408–422 describe activation mechanics and then say the mode is internal, under development and unreachable by admitted requests. Lines 10–20, 53–61, 193–198 and 357–380 describe actor-form behavior directly; the linked native evidence contract describes admitted actor output, and the packet identifies a public-guide actor request. Literal non-admission, stale non-admission wording, and an unnamed narrower internal mode are competing readings. None is established here. A contributor cannot confidently select an admitted actor experiment or rely on its explicit issue/transfer operations. Resolve: at this baseline, does public admission reach these actor waits, or is there a separately named internal mode? Optional edit after verification: state public/internal scope consistently. This finding is not a claim that the implementation is wrong.

**F2 — execution-form scope is inconsistent across the resource account (concern; questioning, with audit-only instances).** Lines 150–177 speak generally about worker launch and extension/exec exclusion, whereas 53–61 and 193–198 supply actor-specific qualifications. The detailed inventory mixes explicit form distinctions (S1b, S14c) with unqualified declaration-like rows (notably S14b, S19–S22 and S37). S7's single launch description and S5/S13d's token fd also need a form scope before use for actors. The contributor can identify some exceptions but lacks a reliable rule for every resource row. Consequence: applying a descriptor inheritance or static-handle lifetime claim to actors may be wrong. Resolve: which rows are common, declaration-only, or replaced/extended by actor resources, and which cited controls exercise each form? Optional edit: form labels plus a small actor resource crosswalk. The need for an applicability explanation is central here; exact test configurations properly remain in linked control documentation.

**F3 — actor narrative versus declaration-oriented detailed inventory (concern; questioning, completed in audit).** The overview expressly scopes its diagram to declarations (53–61), and the actor narrative explains authority-region, outbound/inbound slot, transfer-cell, handle-table and custody ownership (357–380). No dedicated node/edge IDs in the 84-node/55-edge detailed inventory identify those actor resources. The inventory's presentation as the detailed resource/lifetime account does not explicitly delimit that omission. Consequence: an actor-operation reviewer cannot tell whether the inventory is exhaustive for their mode or how to trace actor cleanup through it. Resolve: is this inventory deliberately declaration-only, and where is the actor resource/lifetime inventory owned? Optional edit: explicit scope and a link could suffice; duplicating a full actor graph is not assumed necessary. F2 is ambiguous applicability of existing entries; F3 is missing explanation of the actor coverage boundary.

**Q1 — token digest (factual question; initial-task/questioning; no prohibition inferred).** Lines 323–347, 382–385 and 447 establish bearer-channel separation and erasure/identity limits. The linked native evidence contract provides specimen-local references and excludes token bytes/native pointers from reply fields. Neither consulted account settles retention of token-derived digests. The W1 possible association aid remains conditional, not a requirement; W2's pending approval wording was not evidence of prohibition. Investigate whether another contract specifies digest handling and what byte scope, retention lifetime and association meaning the proposal needs. A digest would not establish native authority identity, active permission or causation merely by matching bytes. No documentation defect is asserted solely from absence.

**Q2 — state after failed release (factual question; initial-task/questioning).** Lines 330–355 and S37 establish an explicit requested release, an earlier consume handle, independent read observations, once-if-eligible language and no automatic exit-time release call. The linked contract distinguishes returned/unavailable/unresolved and includes handle_unavailable/repeated_action. Neither explains the local handle transition after returned release failure or subsequent release admission, especially by form. Investigate each form's promised eligibility and state transition; native API retry meaning is a separate question. No retry policy or prohibition is invented. A successful release still does not prove revocation.

**A1 — fresh-write discoverability (minor concern; audit-only).** The file-action comparison at 245–258 enumerates open_read/open_write/create/read_fresh; S32w/S32c and W55/W56 later describe write_fresh/create_fresh. The opening table is not expressly exhaustive, so omission is not false behavior, but a contributor choosing an operation may miss the richer evidence until the long inventory. Resolve: should this table orient all implemented file actions or a deliberate subset? Optional edit: add the two rows or explicitly link them. No observed W2 failure is claimed.

**A2 — parked actors and inbound servicing (minor clarity concern; audit-only).** Lines 372–377 say parked actors accept/reject deliveries, while 413–414 says a parked actor runs nothing of the specimen. An apparatus/action distinction can reconcile them, but the absolute wording obscures the distinction for an authority-lifetime reviewer. Resolve: does parking permit only protocol servicing, with requested native actions held? Optional edit: name that distinction locally. This is not a demonstrated runtime contradiction.

**A3 — density and optional compression (minor/optional; audit-only).** The detailed rows, check prose, repeated limitations and notes are long, but object/reference/lifetime distinctions are necessary and distinct from the short tour. Repeated assertion scope could be factored into a keyed legend only if row-specific scope stays visible. The receipt's exact hashes could live mainly in its linked receipt, but keep identity and missing-artifact limits nearby. No deletion of whole resource categories is justified merely because the initial read task did not use them.

**Unsupported conclusions retained as such:** the actor paragraph is definitely stale; actors are definitely publicly rejected; token digests are forbidden; release failure implies revocation or safe retry; L establishes current actor isolation; source/check citation presence proves behavior; unpublished worker payload becomes usable when an independent observer sees an effect. None follows from the consulted account.

## Whole-account assessment

**Purpose and ownership — retain, initial-task/audit-only.** The account connects pre-apply apparatus, ambient context, post-apply acquisitions, authority lifecycle and published evidence. That belongs in a worker implementation tour. Architecture ordering, build identity, wire fields and exact budgets are appropriately delegated by links. The worker document still owes its own form/applicability boundary (F1–F3). A standalone exhaustive protocol specification is unnecessary here.

**Sequence and connections — retain with F1–F3.** The progression from conceptual map to apparatus, launch context, operation acquisitions, supplied authority and publication gives a useful reason for keeping target opens within actions. The change table translates the account into review decisions. The detailed inventory supports targeted resource audits rather than requiring linear reading. The main difficulty is switching between common and declaration-specific explanations without a stable scope rule.

**Necessity/duplication — retain, minor compression optional.** The opening boundary, supplied-authority fresh-read explanation and change-table warning repeat a central constraint at three different decision points; this is useful repetition. The evidence/publication distinction similarly serves interpretation then mechanism then change review. The lower-level inventory and edge list give object ownership and relationship lookup beyond prose. Do not call these redundant just because they overlap. Repeated check descriptions and qualification notes are compression candidates, not established defects.

**Checkability — documentary claims only.** Operations, owners, native results, lifetimes and explicit observation bounds are usually concrete enough to investigate. Private native-state claims are explicitly limited. A cited controlled case supports its stated configuration, not every adjacent field. Form scope and current applicability remain questions. Mechanical citation checks are correctly separated from semantic validation.

## Narrative, tables, figures and framing units

Each row assesses a meaningful purpose rather than a wrapped Markdown line. Headings, blank lines, table headers and delimiters belong to their enclosing unit; they carry no omitted independent behavioral claim.

| Lines / unit | Purpose and checkable content | Assessment, connection, necessity and disposition | Origin |
| --- | --- | --- | --- |
| 1–8 | Title and experimental boundary | Retain: makes the setup-opened descriptor error concrete and explains pre-apply report storage versus attempted acquisition. Deleting it would remove the central review criterion. | initial-task |
| 10–20 | One-way setup, per-form process lifetime and ownership router | Retain with F1: resolves W1 process-lifetime uncertainty; phases share a process, unapplied actors apply none. Architecture/build/evidence links are proper dependencies, not missing worker exposition. | initial-task |
| 22–51; conceptual Mermaid | Nodes context/token/policy/acquire/extension/storage/validator/host/controller and all connecting arrows | Retain: separates reporting, bearer supply, policy and external evidence. Declaration scope is stated at 53–61. The arrows convey ordering/ownership rather than guarantees of success. Could not replace with a generic process diagram without losing the boundary. Render quality not assessed. | initial-task |
| 53–61 | Conceptual-map scope, actor additions and per-actor exec exclusion | Retain with F2/F3: useful explicit scope and delivery-versus-consume distinction. “Two more resources” is a conceptual summary, not enough to scope the entire detailed inventory. | initial-task/questioning |
| 63–66 | Collection hold and release ordinal | Retain: predictions remain external; architecture owns full ordering. No need to reproduce that protocol here. | initial-task |
| 68–75 | Worker/validator/host/controller responsibilities | Retain: avoids treating host disposition as a worker measurement. Short division of ownership is useful before limitations. | initial-task |
| 77–87 | Native-state, privacy mediation and causation limits | Retain: explicitly limits the requested before/after comparison. External-runner selection and comparison semantics reasonably link elsewhere. | initial-task |
| 89–93 | Effect versus publication example | Retain: concrete consequence of worker death; linked later section explains mechanism. Repetition has an orienting purpose. | initial-task |
| 95–97 | Missing measurement versus inherent unknowability | Retain: prevents overstating instrumentation limits. Short distinction justifies later census caveats. | audit-only |
| 99–109 | Evidence object, host/worker views and precompile map | Retain: records object/map ownership and resilience under unknown cleanup. C-harness link is an unverified test pointer; no claim of actor coverage follows. | initial-task |
| 111–115 | Retained descriptors versus EOF/host close | Retain with F2: distinguishes process references and maps; L support explicitly scoped to recorded launches. A form qualifier would help if common behavior is intended. | questioning |
| 117–129 | Storage capacities, temporaries, compiler inputs and frees | Retain: resource ownership review needs these allocations even though read task does not. Limits link owns numbers. Unknown compiled-profile destruction is explicit, not silently credited. Could split for scanning; no necessary edit established. | audit-only |
| 131–136 | Compiler receipt placement and meaning | Retain: explains why capture adds no post-apply target acquisition; receipt contract properly owns interpretation. | audit-only |
| 138–148 | Credentials, entitlements, required-key checking and augments | Retain: fresh process is not authority-free. Selection/signing links are appropriate dependencies. Empty entitlements do not imply no ambient authority. | initial-task |
| 150–165 | Spawn inheritance and observed environment/endpoints | Concern F2: generic worker language precedes actor exceptions. Distinction between examined external source and bounded L observation is good and should survive any shortening. Exact actor applicability must be stated, not inferred from a shared function citation. | questioning |
| 167–177 | Inherited context, SIGPIPE, core limit and exec exclusion | Retain with F2: context mutations are substantive experiment inputs. Observer SIGPIPE caveat avoids overcredit. Unqualified exec/extension refusal must be reconciled with per-actor exclusion at 58–60. | questioning |
| 179–191 | Setup checks, allocation and fixture limitations | Retain: failure-path evidence is scoped; fixture-contained invalid-handle use is not production proof. Mixed ActorSession/legacy issuer discussion benefits from form scope (F2). Exact fixture details could be linked, but keep the non-proof caveat. | questioning/audit-only |
| 193–198 | Single-worker collision and actor descriptor relocation/control | Retain: explicit differentiator needed by F2. Control assertion is concrete; exact configuration can live in inheritance/setup documentation. | questioning |
| 200–211 | L method, configuration, results and readiness exception | Retain: two distinct launch windows and no live publication sampling delimit interpretation. EPIPE despite eventual completion illustrates independent readiness/process observations. | questioning |
| 213–217 | L exclusions | Retain: essential prohibition against promoting a bounded census to actor/current authority proof. It is a scope qualification, not a failure finding. | questioning |
| 219–230 | L provenance, receipt and absent original artifacts | Retain; A3 optional compression: exact run/source identity is useful for reuse, missing raw evidence must remain explicit. A receipt link can carry long identifiers without losing local limits. Not inspected independently. | questioning/audit-only |
| 232–234 | Reuse requires applicability review | Retain: hashes alone cannot prove exercised conditions. Central answer to current-form evidence applicability. | questioning |
| 236–241 | Ambient-context known gaps including actor controls | Retain: distinguishes measured endpoints from absent signal/right/runtime census. Does not establish an isolation census. | questioning |
| 243–249,255–258 | File-action table introduction and contract/control links | Retain with A1: useful action-selection comparison; table subset status uncertain. Contract link appropriately owns reply fields. | initial-task/audit-only |
| 250; attempt_file_open_read | Open status with discarded read/close results | Retain: prevents calling open success a measured read; distinct from fresh read. | initial-task |
| 251; attempt_file_open_write | Truncating open with discarded write/close results | Retain: distinguishes truncation/open from observed write return. Useful beyond current task. | audit-only |
| 252; attempt_file_create | Create-or-open, inherited umask, no truncation | Retain: avoids assuming exclusive creation or replacing existing content; close remains unobserved. | audit-only |
| 253; attempt_file_read_fresh | Fresh open, metadata/read/single-close evidence | Retain: directly supplies acceptable experiment and partial-failure account. | initial-task |
| 260–273 | Exec setup and native/libc allocation boundaries | Retain: explains why post-apply resource creation includes setup and why fixed output buffers do not establish allocation-free internals. External source is cited, not locally verified. | audit-only |
| 275–285 | Per-attempt exec controls, child context and spawn/exit distinction | Retain: concrete resource-ceiling and denying-case scope; policy behavior remains case-specific. Budgets and exec contract are sensible dependencies. | audit-only |
| 287–297 | Exec collection snapshot, group/fallback cleanup and waits | Retain: cleanup and leader status have distinct witnesses; missing metadata is no cleanup fact. Detail fits ownership tour; field specification belongs to contract. | audit-only |
| 299–303 | Descendant survival gap | Retain: necessary limit on process-exit cleanup assumptions; signal/EOF/reap do not prove group absence. | audit-only |
| 305–311 | Mach references, sysctl stack buffer and no-handle calls | Retain: distinguishes retained bootstrap reference from service cleanup, and discarded sysctl contents from status. Explicit lack of right-count measurement is useful. | audit-only |
| 313–321 | Declaration issuer preparation and delivery gate | Retain: resolves external issuance timing and host-owned metadata; differs materially from actor issue. | initial-task |
| 323–332 | Preparation, borrowed channel and static handle | Retain with Q2/F2: no preparation consumption; symbols/channel/close placement concrete. Does not state failed-release state transition. Static handle belongs to declared single-worker subsection. | initial-task |
| 334–347 | Erasure owners, boundaries and interruption limits | Retain: full buffer versus inspected issuer prefix, host versus worker and erasure versus release are noninterchangeable. Q1 remains absent rather than prohibited. | initial-task |
| 349–355 | Fresh read before/during/after and native evidence link | Retain: either after-release read result accepted; no revocation assertion. “After-release” should be read with explicit native-result qualifications, as after an attempt. | initial-task |
| 357–369 | Actor setup, issue and outbound ownership | Retain with F3: distinguishes setup failure from API unavailable; exact target and publication/erasure sequencing matter. Needs inventory scope explanation, not removal. | initial-task/questioning |
| 370–380 | Transfer cells, self-transfer, inbound service, handles and cleanup | Retain with F3/A2: actor ownership/lifetimes are substantive and not equivalent to static declaration handle. Private custody cleanup independence is useful. | initial-task/questioning/audit-only |
| 382–385 | Private extension-state and identity limits | Retain: directly bounds attribution and Q1. Does not prohibit digest retention. | initial-task |
| 387–399 | Native result publication boundary | Retain: withholds partially written payload even with independently observed effect. Worker evidence contract is proper detailed dependency. | initial-task |
| 401–406 | Release wait, refusal/cancellation and terminal exit | Retain: distinguishes absence of done from effect absence and makes exit independence explicit. | initial-task |
| 408–418 | Actor activation ordinals, lifetime cutoff, setup and hashes | Retain with A2: implementation-level protocol informs resource lifetime and apparatus cost. Full scheduler design can remain in architecture. | initial-task/audit-only |
| 419–422 | Internal/development/no-admitted-request scope | Concern F1: directly unsettles which proposed experiment can run. Need factual reconciliation before choosing wording. | initial-task |
| 423–428 | Host collection/reap and explicit-acquisition boundary | Retain: map lifetime survives worker; wait cancellation and fallback cleanup separated. Private library boundary honestly qualifies completeness. | initial-task |
| 430–436 | Live-target and query_first ordering limits | Retain: collection barrier is not target immutability. Architecture and ordering evidence links own precise eligibility. | initial-task |
| 438–444 | Change-table framing and columns | Retain: turns resource account into contributor review criteria. Three columns make mechanism and consequence inspectable. | audit-only |
| 445; change open-before-apply/retain-descriptor | Previously acquired authority | Retain: directly rejects proposed setup descriptor reuse for fresh-access question. Useful deliberate repetition. | initial-task |
| 446; change pre-create exec setup | Moves acquisition outside applied conditions | Retain: same boundary applied to a distinct resource category. | audit-only |
| 447; change early consume/evidence token | Moves intervention or adds bearer authority to reporting | Retain: separates two concrete design hazards; does not settle digest handling. | initial-task |
| 448; change retry inputs/reuse worker | Substitutes experimental conditions | Retain: same-protocol interrupted I/O retries explicitly distinguished. Does not answer failed-release eligibility (Q2). | initial-task/audit-only |
| 449; change automatic augment | Changes policy including file read allowance | Retain: brief example belongs here; composition details properly linked. | audit-only |
| 450; change worker reply assembly | Couples reporting to specimen communication | Retain: architectural consequence is connected to withheld result witness. | initial-task |
| 452–455 | Remove collection hold | Retain: prior-query interpretation depends on ordering; no snapshot immutability overclaim. | initial-task |
| 457–463 | Inventory purpose and object/reference distinction | Retain with F3: central reason separate descriptors/maps/views warrant separate rows. Needs execution-form coverage boundary. | questioning |
| 465–473 | Figure node-role/color legend | Retain: mixed nodes prevent overstating a pure authority/apparatus split. Categories explain diagram; color accessibility/rendering not assessed. | audit-only |
| 475–484 | Figure edge legend, application boundary and omissions | Retain: selected relationships and unconnected ambient nodes explicitly distinguished from exhaustive graph. Does not by itself explain missing actor resources (F3). Native-size instruction is not proof of usability. | questioning/audit-only |
| 486–500 | Table abbreviations, observation scope, call-site placement and exit lifetime | Retain: L scope and cited assertions are qualified; exact review procedure reasonably linked. Exit cleanup applies only to process references, not files/other processes. | questioning |
| 502–508; worker_capabilities figure/caption/details summary | Generated figure, 84 nodes/55 edges, IDs and mechanical checks | Retain with F3/A3: count and ID relationship checked against Markdown rows in this audit. Source-symbol/citation checks explicitly do not establish relevance. SVG/XML labels and endpoints inspected; rendered layout unverified; no manifest/generator opened. | audit-only |
| 510–513; node header | Resource, acquirer, period, lifetime, teardown, authority, exec reach, role, source/check/limits columns | Retain: these are distinct contributor questions; a generic resource list would lose critical ownership. Cross-cutting form column/scope is missing (F2). | questioning/audit-only |
| 599–602; edge header | From/to, relationship kind, claim, source/check/limits | Retain: makes relation claims auditable separately from resources; complements node lifetimes. | audit-only |
| 659; Notes label | Local caveat index | Retain: links qualifications to exact IDs; repetition can be shortened only without dropping bounds. | audit-only |
| 699; claims without cited check | Explicit source-only ID list | Retain: useful audit entry point, not a defect list or claim of falsity. Mechanical agreement with rows is not semantic sufficiency. | audit-only |
| 701–702 | Details and generated-block close | Retain: presentation boundary only; no separate behavior. | audit-only |
| 704–709; Known gaps | Links to ambient, exec-descendant and private-extension-state gaps | Retain: compact navigation preserves three materially distinct limitations without restating full prose. Repetition useful; actor inventory scope is not resolved here. | audit-only |

## Generated nodes — every row

All node rows assess the named resource’s acquisition, lifetime, teardown, authority and exec-reach columns as documentary claims. Citations are evaluated for their stated assertion scope, not verified. Default disposition is retain for this resource-audit purpose; F/Q/A references mark qualifications. Default origin is audit-only; explicit initial-task/questioning marks below preserve earlier reader use. Combining rows is safe only if the separate object/reference/owner distinctions identified here survive. Repeated source paths/check descriptions can be factored without deleting those facts.

| ID; line; resource | Assessment and necessity | Origin |
| --- | --- | --- |
| `s1a`; 514; Evidence shared-memory object | Separating the backing object from descriptors/maps is necessary; immediate unlink is a request with an injected-failure caveat, not guaranteed absence. | audit-only |
| `s1b`; 515; Host shmFD | Explicitly distinguishes flags by form and host close from surviving mappings; keep as an example of needed scope labeling (F2). | questioning |
| `s2`; 516; Host evidence base mapping | Host mapping survives descriptor close and worker uncertainty; central publication-recovery ownership. Independent mapping controls are scoped to object identity, not every lifetime field. | initial-task |
| `s3a`; 517; Host ready-pipe read end | Host readiness reader ends at its wait; do not merge with worker writer lifetime. | audit-only |
| `s3b`; 518; Host ready-pipe write end | Spawn transfer and host close leave the worker endpoint; necessary separate reference. | audit-only |
| `s4a`; 519; Host policy-pipe read end | Policy read endpoint transfer is distinct from the write endpoint and child stdin replacement. | audit-only |
| `s4b`; 520; Host policy-pipe write end | Bounded delivery, EOF and descriptor closure explain host-side lifetime independently of worker fd 0. | audit-only |
| `s5`; 521; Host token-delivery duplicate tokenFD | Authority-bearing duplicate is separate from underlying object; declaration token path needs explicit form scope before actor use (F2). | questioning |
| `s6`; 522; Worker-spawn file-action handle | Spawn action handle configures descriptors but is not itself inherited authority; checked initialization caveat is useful. | audit-only |
| `s7`; 523; Fresh worker process | Fresh worker and terminal/abnormal lifetime useful; nil attributes/envp and erase-accepted-token summary need form applicability (F2). | questioning |
| `s8a`; 524; Extension channel object | Channel object contains bearer bytes and metadata; distinct from reporting object and each process view. Declaration scope should be explicit (F2/F3). | audit-only |
| `s8b`; 525; Session descriptor | Session descriptor controls map/duplicate lifetime; its cleanup assertion does not establish shared-object identity. | audit-only |
| `s8c`; 526; Host token-channel mapping | Host mapping erasure is independently owned and not proof of all copies erased. | audit-only |
| `s9`; 527; Fresh issuer process | Fresh issuer, clean reap gate and sibling relationship distinguish declaration preparation from actor-native issue; keep form scope. | audit-only |
| `s10a`; 528; Issuer zero soft/hard core limit | Issuer core-dump limit is process context, not token erasure; failure precedes mapping. | audit-only |
| `s10b`; 529; Issuer channel mapping | Issuer mapping lifetime and malformed-header exit distinguish explicit unmap from process teardown. | audit-only |
| `s10c`; 530; Issuer channel fd 3 | Issuer fd closure after map does not release mapped storage; separate endpoint row justified. | audit-only |
| `s11a`; 531; Issuer libsandbox dynamic- library handle | Loaded library makes API callable without granting entitlements; explicit no dlclose and unobserved internals useful. | audit-only |
| `s11b`; 532; Issuer issue/consume/release symbol addresses | Checked consume/release symbols are not called by issuer; preserves preparation/intervention boundary. | audit-only |
| `s12a`; 533; Native returned token allocation | Native bearer allocation bounded erase/free and oversized tail caveat matter; private allocation extent unobserved. | initial-task |
| `s12b`; 534; Token bytes in shared channel | Shared bytes lifetime, independent host erase and fatal interruption are distinct from handle state. | initial-task |
| `s13a`; 535; Worker policy fd 0 | EOF does not close retained policy fd; child replacement is explicit. | audit-only |
| `s13b`; 536; Worker evidence fd 3 | Mapping object versus fd endpoint and low-fd collision matter; collision clause needs explicit declaration scope (F2). | questioning |
| `s13c`; 537; Worker ready fd 4 | Retained readiness writer and self-dup fixture absence differ from host reader closure; fixture scope must not become actor generalization. | audit-only |
| `s13d`; 538; Worker token fd 5, if supplied | Optional token fd maps then closes; declaration channel needs form scope, actor region is not described here (F2/F3). | questioning |
| `s14a`; 539; Worker inherited stdout/stderr | Inherited stdout/stderr authority is conditional; L null-device result correctly scoped. | questioning |
| `s14b`; 540; Other inheritable ambient host descriptors | Concern F2: unqualified spawn without CLOEXEC_DEFAULT conflicts with actor exception in prose; scope as declaration if factually correct. | questioning |
| `s14c`; 541; Possible original-number alias of evidence shmFD | Explicit per-form alias distinction useful; source-only support clearly marked. Alias is not a second shared object. | questioning |
| `s15`; 542; Worker environment vector | Source account of nil envp and bounded observed environment separated; no current-form universal census follows. | questioning |
| `s16a`; 543; Credentials and signed worker entitlements, ambient policy context | Credentials/signature/ambient policy are starting substrate; required-key checks do not measure effective authority. | audit-only |
| `s16g`; 544; Working directory | Cwd affects relative resolution; L reports a configuration, not a reset by PW. | audit-only |
| `s16h`; 545; File-mode creation mask | Umask affects creation modes; explicitly source-only, no live observation credited. | audit-only |
| `s16c`; 546; Inherited resource limits | Resource limits bound native operations; extension core-limit mutation separately inventoried. | audit-only |
| `s16i`; 547; Inherited signal dispositions | Inherited dispositions and SIGPIPE intervention differ from masks; no dedicated live control claimed. | audit-only |
| `s16j`; 548; Inherited signal mask | Mask inheritance is a separate resource/context fact; absence of live measurement explicit. | audit-only |
| `s16e`; 549; Task-self, bootstrap and other initial Mach rights | Initial Mach rights are not an empty set; no full census and native inheritance remain qualified. | audit-only |
| `s16f`; 550; Executable/library mappings, runtime heaps and threads | Runtime mappings/threads preexist apply; no per-allocation provenance or total teardown census promised. | audit-only |
| `s17`; 551; Worker ignored SIGPIPE disposition | Ignored SIGPIPE supports readiness survival and affects child context; one EPIPE control does not census signals. | audit-only |
| `s18`; 552; Worker evidence base mapping | Worker shared map survives local descriptor changes; source-only map/teardown account retained. | audit-only |
| `s19`; 553; Static extension function pointers | Preparation resolves pointers without consumption. Declaration consume/release pair differs from actor issue entry point (F2/F3). | questioning |
| `s20`; 554; Worker zero soft/hard core limit | Zero core limit succeeds only on prepared path; missing symbols/local failure qualify claim, no automatic reset. | questioning |
| `s21`; 555; Worker extension-channel mapping | Accepted mapping remains after erase; rejected mapping has different cleanup. Declaration scope matters. | initial-task |
| `s22`; 556; Accepted token view in S21 (alias of S12b, no copy) | Borrowed alias, not token copy; full-buffer erase is separate from native release. Host erase cannot certify worker cleanup. | initial-task |
| `s23`; 557; Static policy_buf | Policy buffer retained storage is not a preopened target; supports acquisition-boundary audit. | audit-only |
| `s24`; 558; Static consumed_params snapshot | Snapshot is compiler input, not new resource authority; parameter control scope does not prove all allocation facts. | audit-only |
| `s25`; 559; params_obj and parameter entries | Parameter object/free has an explicit owner; native allocation internals remain unknown. | audit-only |
| `s26a`; 560; Returned compiled profile and its bytecode | Compiled object is not applied policy; no explicit free and private lifetime uncertainty preserved. | audit-only |
| `s26b`; 561; Compiler error string compile_err on failure | Compile-error string only on failure; native allocation/free source-only despite compile-refusal control. | audit-only |
| `s27`; 562; Compiled capture bytes/header inside S18 | Capture reuses evidence storage and existing task authority before apply; publication not proof of effective policy. | audit-only |
| `s28`; 563; Applied sandbox policy | One-way applied restriction persists; unapplied actor has no such application, already stated in introduction. | audit-only |
| `s29`; 564; open_read target fd | Open-only status and ignored read/close returns prevent overinterpreting bytes. | audit-only |
| `s30`; 565; open_write target fd | Truncating open can have effect even though write return is discarded; keep separate from fresh write. | audit-only |
| `s31a`; 566; create target fd | Create-or-open fd differs from persistent file; close result discarded. | audit-only |
| `s31b`; 567; Newly created filesystem object, if absent | File can persist beyond worker exit; cannot combine with descriptor teardown. | audit-only |
| `s32`; 568; Fresh target fd and read observation | Fresh open/stat/read/one close is central initial-task resource; close failure retained, no retry. | initial-task |
| `s32w`; 569; Fresh write fd and observations | Fresh write and explicit truncate evidence useful; missing from opening action table is A1, not unsupported behavior. | audit-only |
| `s32c`; 570; Exclusive child creation and fd | Exclusive create and persistent entry/bytes distinct from create-or-open; A1 discoverability only. | audit-only |
| `s33a`; 571; Bootstrap send-right reference | Unintended retained bootstrap reference is concrete lifetime claim with no independent right-count assertion. | audit-only |
| `s33b`; 572; Lookup service send right | Service deallocation attempted, return ignored; do not turn lookup success into release proof. | audit-only |
| `s34a`; 573; Exec stdout/stderr read endpoints | Worker output-read endpoints are attempt reporting resources acquired after apply, not prebuilt apparatus. | audit-only |
| `s34b`; 574; Exec stdout/stderr write endpoints | Worker close and child reference lifetime differ; combining with read ends would hide ownership. | audit-only |
| `s35a`; 575; Exec file-action heap handle | Opaque file-action allocation/teardown source account; installed allocation not independently observed. | audit-only |
| `s35b`; 576; Exec attribute heap handle | Attribute handle distinct from spawned process group; source-only ownership correctly qualified. | audit-only |
| `s36a`; 577; Exec child PID/process | Leader ownership/conditional cleanup versus survival of children needs separate process row. | audit-only |
| `s36b`; 578; Child process group | Process group addressing does not prove group absence or contain escaped descendants. | audit-only |
| `s37`; 579; Static extension handle and native extension state | Concern F2/Q2: static declaration handle differs from actor table; once/eligible and no exit release do not define failed-release local transition. | initial-task |
| `n1`; 580; Issuer-channel high duplicate spawnFD | High duplicate for issuer fd 3 avoids collision; sibling lifetime not worker inheritance. | audit-only |
| `n2`; 581; Issuer spawn file-action handle | Issuer file-action handle cleanup meaningful; fixture invalid-handle limitation preserved in note. | audit-only |
| `n3`; 582; Issuer spawn attribute handle | Issuer attribute handle distinct from worker launcher; fixture limitation prevents overcredit. | audit-only |
| `n4`; 583; Issuer stdio /dev/null descriptors 0/1/2 | Issuer stdio endpoints specified but source-only; extension tests do not independently identify them. | audit-only |
| `n5`; 584; Host copied launch argument strings | Host copied argv lifetime ends after spawn; allocation failure may produce malformed argv, not proven safe handling. | audit-only |
| `n6`; 585; Host policy byte array and request-population temporary arrays/data | Host arrays cannot be mistaken for worker acquisitions; ARC/temporary internals source-only. | audit-only |
| `n7`; 586; Host target-resolution buffer/metadata and issuer record | Host target resolution/metadata precede worker; later opened-object identity requires its own witness. | initial-task |
| `n8`; 587; Worker main-frame arguments, timing state and capture nonce | Timing/nonce frame is existing control storage, not new target authority; explicit lifetime useful. | audit-only |
| `n9a`; 588; Worker temporary pre-compile call frames | Precompile call frames separated from private native allocations; no allocation-free claim. | audit-only |
| `n9b`; 589; Capture hash/view/digest/sorting call frames | Capture hash/sort temporaries are pre-apply; does not establish permission to retain token digests (Q1). | audit-only |
| `n10`; 590; Attempt-local stack buffers, argv pointers, polls, wait status and metadata | Local buffers include discarded sysctl value; capacity/return controls have narrow scope, not full stack behavior. | audit-only |
| `n11`; 591; Post-apply outside-attempt automatic diagnostics and seam timespec | Post-apply control diagnostics use existing frames; private libc behavior remains separately inventoried. | audit-only |
| `n12`; 592; Exec child stdin /dev/null fd 0 | Child null stdin acquired by spawn actions inside attempt; avoids exposing policy stream. | audit-only |
| `n13`; 593; Libc diagnostic state reachable after apply | Fixed diagnostic destinations do not eliminate hidden libc allocation/locale behavior; source bounds retained. | audit-only |
| `x1`; 594; Validator predictions | Prediction belongs outside worker and release ordinal is separate; no inherited prediction resource. | initial-task |
| `x2`; 595; Host disposition and comparison | Host disposition joins admitted evidence, not native authority truth. | initial-task |
| `x3`; 596; Host path diagnostics | Later host path diagnosis must not become worker-time object evidence. | audit-only |
| `x5`; 597; Compiler receipt in dossier | Copied compiler receipt and applied policy evidence remain distinct. | audit-only |

## Generated edges — every row

All edges are retained for the named relationship lookup unless a cross-reference marks uncertainty. They select relationships rather than claiming a complete authority graph. Node tables own lifetimes; these edges own acquisition, delivery, exercise, publication, observation or join relations. Keeping the relation while shortening repeated citations would preserve purpose. The absence of W50 is an identifier gap, not evidence of missing coverage: 55 edge rows are present.

| ID; line; relation | Assessment, check scope and connection | Origin |
| --- | --- | --- |
| `W1`; 603; s1b → s2 (prepares): Host maps evidence descriptor | Map acquisition differs from object ownership; independent mapping challenges are stated, not verified. | audit-only |
| `W2`; 604; s1a → s1b (prepares): Host holds backing-object descriptor through worker launch | Holding backing fd through spawn is not same as mapping lifetime; keep transfer relation. | audit-only |
| `W3`; 605; s1b → s13b (prepares): Spawn action duplicates evidence descriptor | Spawn duplication explains worker evidence endpoint; object identity check scope retained. | audit-only |
| `W4`; 606; s13b → s18 (prepares): Worker maps evidence descriptor | Descriptor-to-map operation is source-only; L does not identify the backing object independently. | audit-only |
| `W5`; 607; s3b → s13c (prepares): Spawn action duplicates readiness endpoint | Readiness endpoint delivery distinct from subsequent ready observation. | audit-only |
| `W6`; 608; s4a → s13a (prepares): Spawn action duplicates policy endpoint | Policy fd delivery distinct from source-byte receipt and EOF. | audit-only |
| `W7`; 609; s4b → s23 (prepares): Policy delivery fills static source buffer | Policy stream fills static buffer; source-only relation, no new target handle. | audit-only |
| `W8`; 610; s6 → s7 (prepares): Worker launch file actions select protocol endpoints | File actions shape worker descriptors; F2 form scope applies to node/launch account. | audit-only |
| `W9`; 611; n5 → s7 (prepares): Copied argv supplies worker launch arguments | Spawn copies argv; source setup controls do not repair allocation failure caveat. | audit-only |
| `W10`; 612; n6 → s2 (prepares): Host initializes request fields and nonce | Request initialization supplies storage, not native result evidence; source-only. | audit-only |
| `W11`; 613; s23 → s26a (prepares): Compiler reads source buffer | Compilation consumes submitted buffer, distinct from applying compiled output. | audit-only |
| `W12`; 614; s24 → s25 (prepares): Snapshot entries populate compiler parameters | Snapshot populates parameter object; fixture parameter semantics not every allocator detail. | audit-only |
| `W13`; 615; s25 → s26a (prepares): Compiler receives parameter object | Compiler input transfer is separate from parameter-object cleanup. | audit-only |
| `W14`; 616; s26a → s27 (prepares): Capture reads returned compiled object | Capture reads compiled object before application; maximal metadata check does not establish permissions. | audit-only |
| `W15`; 617; s35a → s36a (prepares): Spawn file actions select child descriptors | Post-apply child descriptor configuration belongs to attempt, not host preparation. | audit-only |
| `W16`; 618; s35b → s36b (prepares): Spawn attributes select child process group | Group attributes establish cleanup addressing; descendant survival control limits inference. | audit-only |
| `W17`; 619; n2 → s9 (prepares): Issuer file actions select channel and stdio | Issuer file-action relation is declaration-specific; setup metadata does not prove all stdio identities. | audit-only |
| `W18`; 620; n3 → s9 (prepares): Issuer attributes select descriptor isolation | Issuer isolation attributes source-only; not a proof of actor worker isolation. | audit-only |
| `W19`; 621; s8b → n1 (supplies_authority): High duplicate of session descriptor | High duplicate supplies issuer launch endpoint; duplicate retains same object. | audit-only |
| `W20`; 622; n1 → s10c (supplies_authority): Issuer receives channel fd | Issuer receives channel fd; source/target endpoints separate from mapping. | audit-only |
| `W21`; 623; s10c → s10b (supplies_authority): Issuer maps channel fd | Issuer map acquires view; library allocation internals remain outside control scope. | audit-only |
| `W22`; 624; s8a → s8b (supplies_authority): Session holds channel object descriptor | Session descriptor retained independently of issuer/worker mappings. | audit-only |
| `W23`; 625; s8b → s8c (supplies_authority): Host maps authority-bearing channel | Host authority-bearing map has its own erasure lifetime. | audit-only |
| `W24`; 626; s8b → s5 (supplies_authority): Host duplicates channel for worker delivery | Worker-delivery duplicate exists in declaration path; F2 prevents assumed actor equivalence. | audit-only |
| `W25`; 627; s5 → s13d (supplies_authority): Worker receives optional token descriptor | Optional token fd delivery is not token consumption; actor region needs F3 explanation. | audit-only |
| `W26`; 628; s13d → s21 (supplies_authority): Worker maps token descriptor | Preparation maps token channel; placement control does not establish native permission. | audit-only |
| `W27`; 629; s11a → s11b (prepares): Loaded API symbols permit issuance | Callable symbols permit issuing; they are not an entitlement grant. | audit-only |
| `W28`; 630; s11b → s12a (exercises): Native issuer returns bearer allocation | Native return creates bearer allocation; private allocation internals unobserved. | audit-only |
| `W29`; 631; s12a → s12b (supplies_authority): Issuer copies accepted bearer bytes | Only accepted bounded token copied; inspected-length erase caveat in source node retained. | audit-only |
| `W30`; 632; s12b → s22 (supplies_authority): Worker borrows same bytes through its mapping | Borrowed alias relationship avoids invented copy ownership; explicitly source-only. | initial-task |
| `W31`; 633; s22 → s37 (supplies_authority): Requested consume yields native extension handle | Consume produces handle, not proof of effective permissions; static declaration scope (F2). | initial-task |
| `W32`; 634; s26a → s28 (exercises): Apply receives compiled object and imposes policy | Compiled input applied once; unapplied actor outside this edge. | audit-only |
| `W33`; 635; s33a → s33b (exercises): Lookup uses acquired bootstrap reference | Bootstrap reference used for lookup; no right-count assertion supports disposal. | audit-only |
| `W34`; 636; s31a → s31b (exercises): Successful create-open can create absent file | Create-open may create absent file; existing target case separate. | audit-only |
| `W35`; 637; s34b → s36a (exercises): Child receives output endpoints as stdout/stderr | Child output duplicates carry references beyond worker closes; stdout/stderr ownership matters. | audit-only |
| `W36`; 638; n12 → s36a (exercises): Child receives explicit stdin | Explicit null stdin prevents policy-pipe inheritance; separate from stdout reporting. | audit-only |
| `W37`; 639; s37 → s32 (exercises): Fresh read attempts access under current extension state | Fresh acquisition under then-current state does not establish release revocation; actor state needs F2 scope. | initial-task |
| `W38`; 640; s27 → s18 (publishes): Capture writes receipt into evidence mapping | Capture publication in existing evidence map is distinct from host receipt decoding. | audit-only |
| `W39`; 641; s29 → s18 (publishes): Publishes open status and available observed path | Published open result/path is not measured read success. | audit-only |
| `W40`; 642; s30 → s18 (publishes): Publishes open status; write return discarded | Write return discarded; independent file effect and worker observation kept separate. | audit-only |
| `W41`; 643; s31a → s18 (publishes): Publishes file-create attempt status from open result | Create status from open does not imply absent-target creation in existing-file control. | audit-only |
| `W42`; 644; s32 → s18 (publishes): Publishes native open/stat/read/close observations | Fresh-read published syscall evidence directly supports initial task; no revocation assertion. | initial-task |
| `W43`; 645; s33b → s18 (publishes): Publishes lookup status, not retained port authority | Lookup publication does not report retained port authority or reference counts. | audit-only |
| `W44`; 646; s36a → s18 (publishes): Publishes spawn, wait and cleanup observations | Spawn/wait/cleanup publication distinct from confirmed group absence; cited inheritance/ceiling cases are narrow. | audit-only |
| `W45`; 647; s37 → s18 (publishes): Publishes consume/release native result | Native consume/release result publication is independent from fresh read effect. | initial-task |
| `W46`; 648; s10b → s8c (publishes): Issuer publishes through same channel object | Issuer publishes via same channel object, not worker evidence region. | audit-only |
| `W47`; 649; s3a → s13c (observes): Host reads worker readiness byte | Host ready byte observation is not apply completion or all later publication. | audit-only |
| `W48`; 650; s2 → s18 (observes): Host observes publications in its retained evidence mapping, including after worker exit | Host retained view permits observations after exit; ownership and reap remain independent. | initial-task |
| `W49`; 651; s34a → s36a (observes): Worker drains child output | Output drain does not establish descendants absent; bounded child observation. | audit-only |
| `W51`; 652; s2 → x2 (joins): Host uses admitted publications | Host admits completed evidence; final acquire/reap acknowledgement caveat in note essential. | audit-only |
| `W52`; 653; x1 → x2 (joins): Host joins prediction records to attempt evidence | Query/attempt association is host join, not a causal agreement verdict. | initial-task |
| `W53`; 654; x3 → x2 (joins): Host attaches later path-resolution results | Later host path resolution remains distinct from worker-time observation. | audit-only |
| `W54`; 655; s27 → x5 (joins): Host decodes and copies receipt | Host receipt copy does not establish effective permissions or apply success. | audit-only |
| `W55`; 656; s32w → s18 (publishes): Publishes separate write and metadata observations through completed slot | Fresh-write publication preserves separate native/metadata failures; A1 affects discoverability, not row validity. | audit-only |
| `W56`; 657; s32c → s18 (publishes): Publishes separate write and metadata observations through completed slot | Exclusive-create publication preserves entry/byte observations; persistent effect needs independent evidence. | audit-only |

## Inventory qualification notes — every ID

Retain each note as a scope limiter on its own referenced resource/relation. These repeat some row caveats but serve lookup; combination is optional only if the qualification remains adjacent or directly reachable. All are audit-only coverage dispositions, except previously discussed L/form and publication limits; no new runtime findings are inferred.

| Line / ID | Qualification and assessment |
| --- | --- |
| 661; `s5` | `s5`: Setup controls observe endpoint-action failure refusing spawn with cleanup. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 662; `s6` | `s6`: Worker setup controls observe failed file-action initialization/addition refusing spawn without use of an invalid handle. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 663; `s12a` | `s12a`: Private issuance allocation internals remain unobserved. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 664; `s14a` | `s14a`: L observed read/write null-device stdout and stderr. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 665; `s14b` | `s14b`: L observed no additional numeric descriptor; the contaminated-worker control separately supplies a positive inheritance case. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 666; `s14c` | `s14c`: L observed no original-number evidence alias in its endpoint arrangement; source permits other arrangements. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 667; `s15` | `s15`: L produced identical plain and environment-displaying ps output; this is scoped to those two launches. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 668; `s16a` | `s16a`: Selected signing metadata and required-key checks do not measure effective worker authority. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 669; `s16g` | `s16g`: L observed cwd / in both launches. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 670; `s16h` | `s16h`: No live umask measurement is credited. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 671; `s16c` | `s16c`: No live resource-limit census is credited. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 672; `s16i` | `s16i`: No live inherited-signal census is credited. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 673; `s16j` | `s16j`: No live signal-mask measurement is credited. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 674; `s16e` | `s16e`: L port inspection was refused; the exact live right set remains unknown. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 675; `s16f` | `s16f`: L retained vmmap output; per-allocation origin and policy gating remain unknown. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 676; `s17` | `s17`: L pre-ready launch retained readiness errno EPIPE and later clean completion. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 677; `s19` | `s19`: Private loader/library internals remain unobserved. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 678; `s21` | `s21`: Rejected-mapping unmap failure is recorded on the preparation path. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 679; `s25` | `s25`: Private parameter-allocation internals remain unobserved. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 680; `s26a` | `s26a`: Private compiled-object lifetime inside apply remains unknown. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 681; `s33a` | `s33a`: No independent right-count control is cited for the retained bootstrap reference. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 682; `s33b` | `s33b`: No independent right-count control is cited for service-right release. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 683; `s35a` | `s35a`: The examined Apple source uses malloc/realloc; installed allocation behavior is unobserved. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 684; `s35b` | `s35b`: The examined Apple source uses malloc; installed allocation behavior is unobserved. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 685; `n2` | `n2`: Failed initialization reaches fixture-contained invalid-handle use in setup controls. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 686; `n3` | `n3`: Failed initialization reaches fixture-contained invalid-handle use in setup controls. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 687; `n4` | `n4`: Issuer stdio file actions have source support only; extension boundary controls do not assert these endpoint identities. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 688; `n5` | `n5`: Controlled strdup failure can dispatch empty or truncated argv. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 689; `n6` | `n6`: Swift allocation internals and temporary-array lifetimes have source support only. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 690; `n9a` | `n9a`: Native library internals remain unobserved. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 691; `n9b` | `n9b`: qsort/CommonCrypto internal allocation behavior remains unobserved. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 692; `n10` | `n10`: Compiler stack/page behavior remains unobserved; the sysctl checks cover supplied capacity and return handling. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 693; `n13` | `n13`: Installed libc allocation and locale internals remain unobserved. Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 694; `x1` | `x1`: No transfer into worker; release ordinal is separate Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 695; `x2` | `x2`: Host-owned interpretation under evidence contract Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 696; `x5` | `x5`: Receipt and applied-policy evidence are distinct Retain: bounds the specific row; source-only or unobserved does not mean false. |
| 697; `W4` | `W4`: Source identifies the descriptor-to-mapping operation. L does not independently identify the evidence mapping object. Retain: bounds the specific row; source-only or unobserved does not mean false. |

## SVG/XML figure exposure and relationship assessment

Origin: **audit-only**. The baseline figure artifact was read through XML text, not rendered. It has the same 84 node IDs and 55 edge IDs/endpoints as the Markdown table; the audit checked those sets and endpoints. Node labels name the same resources, with visual line wrapping represented as separate XML text elements. Each node/edge's semantic assessment is in its exact-ID row above, including unconnected nodes. Graph edge labels mostly contain only W IDs, so the table is necessary to interpret the relationship; W32 additionally says “apply restriction.” This is a usable keyed-reference design in principle, not a claim that the rendered page is readable.

Cluster labels assessed:

- `cluster_reporting` — “Reporting apparatus: prepared and attempt-time”: retain; correctly prevents equating all reporting resources with pre-apply acquisition. Exec pipe/handle nodes remain post-apply in their rows.
- `cluster_authority` — “Deliberately supplied authority / restriction”: retain; includes compiler/API resources and imposed restriction, not merely bearer bytes. Legend supplies the needed role qualification.
- `cluster_operation` — “Acquisitions by attempted operations”: retain; fresh target resources, Mach rights and child process connect acquisition to observation. A created file has a lifetime beyond its creating descriptor.
- `cluster_external` — “External evidence”: retain; validator and host/controller products remain outside the worker. Observation/join edges are not bearer transfers.

Mixed/ambient nodes outside those clusters are intentionally permitted by the legend; absence of an observation arrow is not evidence of absence of a resource. Observation arrows such as W47/W48 run from observer to observed resource, whereas publication arrows run from producer to storage; the edge-kind legend and table are necessary to distinguish them. No contradictory endpoint was found in the XML/table comparison. F2/F3 apply to the diagram's declaration-oriented labels and lack of actor-specific region/slot/custody identities just as to the table. No new layout finding was manufactured from XML exposure.

## Dependencies and factual investigation queue

Consulted dependency: `tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence` adds event statuses, pre-call/result boundaries, references/actor resource joins, and fresh-read field meaning. It resolves the W1 uncertainty about publication, not digest or failed-release retry state. Its actor output account is contrary evidence for F1, not proof of runtime admission.

Unfollowed but appropriate dependencies identified in the Worker account:

- `ARCHITECTURE.md#one-run-in-time`, `#evidence-channels-and-ownership`: full scheduler ordering and evidence ownership. This task did not need full protocol reconstruction; do not describe their contents as verified.
- `PolicyWitness.md#extension-and-fresh-read-output`, `#reading-a-comparison-record`, `#compiled-object-receipt-opt-in`, `#external-runners-byoxpc`: exact public fields, interpretation, capture and target selection.
- `tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract`, `#ordering-evidence-states`: detailed worker/ordering state claims; native-extension subsection was the only substantive contract section followed.
- `tests/suites/runner_exec_inheritance/README.md` and linked host-setup documentation: precise configurations and applicability for L/actor descriptor controls. The document owes a form crosswalk; these references properly own detailed test procedures.
- `LIMITS.md`, `BUILD.md`, `SIGNING.md#evidence-artifacts`, augment composition and runner review guidance: budgets, provenance, signing, explicit policy changes and contribution procedure. None needs wholesale duplication here.
- `worker-launch-observation.json`: L provenance/selected observations; not independently read or verified. Missing original artifacts is reported by the Worker text.

Factual investigation priority: (1) resolve actor admission and any internal-mode distinction; (2) map resource rows and checks to forms, including actor authority/custody storage ownership; (3) determine failed-release handle state and admission/retry behavior by form; (4) determine any documented token-derived digest policy and proposed digest semantics. These are questions for later authorized investigation, not instructions to inspect implementation during this stage.

## Coverage accounting and limits

The narrative/framing ledger covers lines 1–513, table scaffolding and lines 599–602, 659, 699, 701–709. The per-row ledgers cover all 84 generated nodes (514–597) and all 55 generated edges (603–657). The notes ledger covers every substantive qualification at 661–697. Whitespace/delimiters are attached to surrounding units. The conceptual Mermaid's nodes/arrows, generated figure declaration/caption/count, both ordinary tables and each row, legends, source/check distinction, no-check list and whole-account structure are explicitly assessed. No substantive Markdown unit is intentionally excluded.

Coverage is documentary and semantic, including SVG/XML labels and endpoints, not verification of cited code/tests or rendered SVG geometry. The 84/55 counts and ID enumeration were checked against the baseline Markdown. Source symbol presence, test truth, generated-artifact freshness and native behavior were not checked. The supplied actor JSON remains a request, not a successful-run observation.

The strongest initial-task benefits were the fresh-descriptor requirement, separated authority delivery/consumption/release, erasure ownership and publication boundary. The first observed conflict was actor admission. Questioning developed form applicability and bounded-census concerns. Fresh-write table discoverability, parked-actor wording and compression options are audit-only; they must not be reported as initial-reading failures.
