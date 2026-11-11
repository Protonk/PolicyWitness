# First-reading journal

## 1. Exact identity and its source inputs — lines 1–70

**What do I now believe?** PolicyWitness runs a declared sandbox experiment and records boundary observations. Its public identity is an exact-match string carried by several producers; matching identity does not establish the other validity conditions. A clean, unambiguous annotated release tag can supply the identity; otherwise selected source paths and bytes supply a development digest. The build embeds the value and checks it again before signing.

**What supports that belief?** Lines 7–10 state the experiment/report purpose; lines 18–26 separate identity admission from other conditions. Lines 31–44 define release and development forms, and lines 49–64 identify included inputs and rejected inventory conditions. Line 69 describes build derivation and the signing refusal.

**What remains uncertain?** U01: I do not yet know the specimen schema or what observations and assessments exist. U02: I have names for controller, compiler helper, host, client capture and equipment association but not their roles or trust relationships. U03: I do not yet know the build-context record or how build configuration, signing and SDK checks constrain the digest's limited meaning.

## 2. Direct builds and historical stamps — lines 71–138

**What do I now believe?** Direct compilation can embed an arbitrary nonempty supplied identity; that alone supplies no release provenance. Unbound controllers refuse public requests. Surface stamps track selected definition/shape history, while admission still uses the exact public identity. A source copy can verify current agreement without verifying historical last-change claims.

**What supports that belief?** Lines 71–74 add the Swift recomputation and pre-sign checks. Lines 81–99 describe direct constants and their receiver gates. Lines 107–117 distinguish surface history from admission and implementation review. Lines 123–138 describe history dependence and refusals before generation.

**What remains uncertain?** U04: “check read” and its other possible support grades are not yet defined; I provisionally read it as inspection rather than execution. U05: I have not seen the surface table or the canonical shapes that determine its stamps. U03 remains: provenance is explicitly separate from supplied identity, but its records and checks are still unspecified to me.

## 3. Separate wire and worker identities — lines 139–220

**What do I now believe?** Ordinary builds may lack verified release history, whereas strict release preflight requires it. Reusing a development specimen requires an explicit comparison and target assertion. Wire schema, public identity and host/worker source identity are separate checks. A worker-reported identity alone does not associate it with an executing binary.

**What supports that belief?** Lines 142–153 describe the build-history gap and reuse procedure. Lines 161–168 order wire matching before public identity admission. Lines 173–187 define the worker digest, exit 3/4 failures and association limit. Lines 192–215 give digest and CodeDirectory widths.

**What remains uncertain?** U06: I do not yet know the typed response frame or worker shared-header layout and lifecycle. U07: I do not yet know what equipment and launch evidence establishes binary association. U04 continues because “source read” now appears as another support grade. I assume CodeDirectory hash is a code-signing identifier, without yet knowing the inspection requirements.

## 4. Producer records and named surfaces — lines 221–299

**What do I now believe?** Controller/compiler envelopes expose contract, version, number, describe and commit strings. Host replies expose contract, describe and commit, with host identity checked before execution-record interpretation. All listed public surfaces currently have an unreleased stamp. PolicyWitness comprises a controller, runner client/host, native worker, query validator and compiler helper.

**What supports that belief?** Lines 223–235 give the build record and derivation rules; lines 241–252 define the host producer record. Lines 255–277 list the surfaces. Lines 287–289 enumerate components, and lines 294–295 describe packaged build duties.

**What remains uncertain?** U03 is partly answered by the provenance fields; signing, configuration and SDK evidence remain unknown. U05 is partly answered by the surface list, but canonical shape inputs are still only referenced. U02 remains for the detailed component roles. U08: the generator description starts at lines 298–299 and continues beyond this portion; I do not yet know its full output list.

## 5. Components and boundary artifacts — lines 300–380

**What do I now believe?** The controller prepares requests and interprets admitted records; the client handles reservation/XPC transport once per run; the host coordinates workers and validators while retaining its reply path outside specimen policy application. Workers are fresh, one ordinarily or one per launched actor. Queries and attempts are distinct native operations. Original-file bytes, submitted serialization, host frames, client captures and admitted replies are distinct artifacts.

**What supports that belief?** Lines 305–330 define controller/client/host/worker responsibilities. Lines 335–346 distinguish validation and compilation. Lines 351–376 define specimen, request, reply and capture. Line 300 completes the generator outputs as document, snapshot and stamps, answering U08.

**What remains uncertain?** U02 is answered at the responsibility level. U09: reservation, query collection/action release, actor phases and bounded observation rules still need operational detail. U10: I do not yet know how raw bytes are retained when capture or reply admission fails. U06 remains for wire and shared-memory layouts.

## 6. Observation, effect and cause — lines 381–470

**What do I now believe?** Envelope status belongs to its emitting operation. Actor identity includes owned process evidence, so a PID alone is limited. A probe relates separately submitted query and attempt operands. Query-first establishes an interval before batch release, not frozen state. Missing operation publication remains unresolved even if progress began. Effects require concrete observations, and permission-shaped failures leave sandbox cause unresolved. Absence and null are field-specific.

**What supports that belief?** Lines 381–415 define envelope, actors, phases, probes and predictions. Lines 420–451 distinguish observation, effect, cause and assessment. The open-write caveat at lines 431–433 limits success to truncating open. Lines 456–470 establish absence/null/optional semantics.

**What remains uncertain?** U11: I do not yet know which checks remove assessment permission while retaining observations, or how that is encoded. U12: I need operation-specific success/effect definitions before interpreting attempts. U13: I do not yet know how owned process evidence differs from ordinary PID observations or supports lifecycle attribution. U09's ordering question is partly answered, but exact barriers remain unknown.

## 7. Request forms and admission — lines 471–560

**What do I now believe?** Unknown facts remain unresolved; explicit absence needs evidence. Closed objects and value vocabularies are boundary-specific. The controller holds one parsed file and submits one normalized serialization. The host admits a whole closed request, checks contract first and capacities before some semantics, and refuses before children. Ordinary requests require policy and exactly one non-null plan form; actor requests require nonempty actors and phases. Empty ordinary probe plans still compile/apply policy. Null has specific exceptions, including extension operand presence.

**What supports that belief?** Lines 475–509 define unknown/bytes/closedness; lines 518–536 define request forms. Lines 541–560 give hold, admission, null and capacity behavior.

**What remains uncertain?** U01 is partly answered by the top-level schema. U14: exact capacity values, required nested objects, selector fields and refusal consequences remain ahead. U15: I do not yet know the dossier's original-versus-selected policy records or packaged augments. U09 remains for actor scheduling and execution overrides.

## 8. Capacities and controller selection — lines 561–638

**What do I now believe?** Source allows 262,143 UTF-8 bytes; plans total at most 256 actions, with 8 ordinary or 16 actor phases. Repeated JSON members have observed entry-dependent outcomes: listed CLI pairs keep the last value while direct host pairs keep the first. Five controller selector fields are removed before host delivery. Every legacy selector is validated before nested non-null overrides; selection and entitlement checks precede invocation. Target-resolution failure takes precedence over augment failure.

**What supports that belief?** Lines 562–570 give capacities; lines 582–586 limit duplicate-member observations to tested cases. Lines 596–619 define selector stripping, precedence and failure order. Lines 627–633 define nested selectors and default standard selection.

**What remains uncertain?** U14 is partly answered for capacities and selectors, while refusal evidence remains pending. U16: I do not yet know external registry/service resolution or what inspecting required entitlements proves. U15 still includes augment meaning and dossier evidence. I would not generalize the duplicate-key observations to unlisted fields or platforms.

## 9. Execution overrides and policy inputs — lines 639–716

**What do I now believe?** Authorized host callers can use test-named overrides even in packaged hosts. Applicability differs by execution form: actor timing stays fixed despite an ordinary timeout override. Host acceptance can be followed by worker argument refusal. Actor inventory checks precede fixture bindings. SBPL policy parameters are sorted string data for native compilation, with bounded, NUL-free inputs. Compiled capture needs a 32-character lowercase nonce; augments are normally controller-resolved.

**What supports that belief?** Lines 640–674 describe override fields, ordering and separate boundaries. Lines 690–704 define policy fields, capacities and parameter preparation; lines 708–716 introduce a parameter-expression example.

**What remains uncertain?** U17: connection authorization and override binary-association evidence remain unspecified here. U18: the meaning and validation of compiled-profile receipts is pending. U15 remains for fragment resolution/imports. U19: the native compiler's treatment of parameters and imports is not yet fully described; I would not infer literal substitution from their string type.

## 10. Compilation classifications and augments — lines 717–795

**What do I now believe?** Worker compilation accepts a non-null profile even alongside a diagnostic; helper success additionally requires no diagnostic. Their outcomes need separate interpretation. Augments append packaged fragment source in order only after all reads succeed; actor normalization stops on first refusal. exec_baseline unconditionally broadens file-read authority. The standalone helper accepts no contract assertion and ignores other root fields; decoding/read/usage failures go to stderr with exit 2.

**What supports that belief?** Lines 717–731 describe parameter and compile observations. Lines 738–774 define fragment validation, atomic replacement, actor order and baseline scope. Lines 782–791 define helper entry and failure behavior.

**What remains uncertain?** U19 is partly answered: actual native parameter outcomes are scoped observations, not guaranteed substitution behavior. U15 is answered for augment resolution but not dossier structure. U20: helper admission, output fields and controller fallback conditions remain unknown. U21: import resolution and its relationship to selected source bytes are still pending.

## 11. Helper admission and query eligibility — lines 796–875

**What do I now believe?** Helper policy decoding ignores capture/augment members and allows a larger source than workers. Its ordered refusal checks stop before hashing, inventory and compilation. Probe IDs are globally unique; actor IDs must be nonempty but ordinary step IDs may be empty. Query operands are admitted separately from attempts. Path planning or excluded pairs can make prediction unavailable while leaving an attempt eligible; open_read success only establishes opening.

**What supports that belief?** Lines 797–818 provide helper fields and ordered consequences. Lines 831–847 define paired probes and the open/read distinction. Lines 857–871 define query grammar, eligibility and whole-request refusal.

**What remains uncertain?** U20 is answered for helper admission, while output/fallback remains pending. U22: excluded prediction pairs and host realpath behavior are not yet specified. U12 remains for concrete attempt operations and their evidence. U23: I do not yet know how query unavailability affects comparison eligibility or phase ordering claims.

## 12. Native attempts and excluded pairs — lines 876–950

**What do I now believe?** Four exact operation/filter pairs are excluded from prediction, without excluding all uses of their filters. Admitted filter strings pass unchanged. Attempt families/actions are closed, with exec-only bounded arguments. Legacy open_read/open_write success discards transfer and close outcomes; fresh file operations retain multiple boundaries and first failure. create need not create a new file. Exec acquires its resources after setup/application, uses an empty environment and a separate process group; spawn success and child success differ.

**What supports that belief?** Lines 876–900 identify exclusions and filter rules. Lines 910–932 define attempts and native consequences. Lines 943–946 specify exec inputs and continuous-time allowances, including excluded waits and possible blocking overrun.

**What remains uncertain?** U22 is answered for excluded pairs but not the full realpath observation. U12 is answered for dispatch/success semantics, with detailed evidence records still pending. U24: child collection, cleanup and clock-fault records remain unknown. U25: extension participants are introduced by the final heading, without their restriction yet stated.

## 13. Actors retain one worker across visits — lines 951–1030

**What do I now believe?** Actor plans support up to eight actors, each with visits, a unique bounded ID, explicit apply/unapplied sandbox declaration and selected/unentitled equipment role. Required entitlements are boolean-true read-back demands. Apply happens once in each fresh worker, then that worker persists across its visits. Unapplied means inherited restrictions, not unrestricted execution. Phases have unique IDs and optional owned-termination dependencies.

**What supports that belief?** Lines 969–991 define actors and normalization; lines 996–998 establish worker freshness and retained policy. Lines 1007–1010 define apply/unapplied. Lines 1018–1025 define phase fields and global action uniqueness. Line 951 refers exec restrictions to extension participation.

**What remains uncertain?** U09 is partly answered for workers and visits, but scheduler progression and dependency rules remain ahead. U16/U17 remain for static and live entitlement checks. U25 remains for exactly which extension participation excludes exec. U26: I do not yet know whether termination dependencies wait, reject, or skip when their subject remains alive.

## 14. Scheduler order and termination gates — lines 1031–1110

**What do I now believe?** Each phase collects eligible predictions, releases ordered actions, then completes before the next collection. Only one actor is active; others park. Query order needs a joined chain, not source order alone. A dependency must name another actor whose every visit precedes the dependent phase, and its runtime gate runs before activation or collection. A failed evaluated gate cancels all remaining phases. Presence of extension selects that action variant even when null.

**What supports that belief?** Lines 1036–1045 state scheduler and barrier scope. Lines 1053–1075 give dependency declaration, runtime gate and admission. Lines 1084–1110 define action selection and specimen-wide uniqueness.

**What remains uncertain?** U26 is answered about failure cancellation; exact natural-reap criteria and waiting remain pending. U09 is answered for nominal scheduler order, while evidence fields and failure paths remain ahead. U23 remains for detailed query-order eligibility. U25 remains for extension actions and participating actors.

## 15. Extension resource grammar — lines 1111–1190

**What do I now believe?** Extensions form declared issue→transfer→consume→release resource relations. Required operands must be strings; every extra operand, including null, is inapplicable. Issue calls native file issuance with exact target and flags zero. Resources share unique assignment names and must have earlier producers owned by the appropriate actor; each handle permits at most one declared release. Multiple deliveries per token and consumes per delivery are allowed. Syntax names intended resources, not successful native outcomes.

**What supports that belief?** Lines 1123–1165 define actions, operands and grammar. Lines 1170–1184 define resource normalization, reuse, unique assignments, producer order and ownership. Lines 1114–1115 reinforce form-specific action IDs.

**What remains uncertain?** U25 is partly answered for operations and declaration ownership. U27: native token/handle capacities, runtime custody, success meaning and cleanup are still ahead. I infer that a valid plan can still have unusable resources after a native failure; I need the runtime rules to know subsequent action behavior.

## 16. Custody is distinct from native authority — lines 1191–1253

**What do I now believe?** Resource counts are bounded, and any actor executing an extension action or receiving a transfer cannot contain exec probes. Token bytes stay in native channels. Required custody setup precedes policy setup and can prevent launch. Issue publication, host acceptance, recipient framing/equality and source acknowledgement are distinct observations. Delivery must settle before consume. Erasure follows declared last use and safe teardown; release success alone does not prove later loss of access.

**What supports that belief?** Lines 1191–1208 define capacities and participant exec exclusion, answering U25. Lines 1214–1226 define setup/publication; lines 1231–1239 define delivery and source acknowledgement. Lines 1244–1251 define erasure and scoped native meaning.

**What remains uncertain?** U27 is answered for payload bound and custody protocol, but exact status records and handle usability rules remain ahead. U28: I do not yet know how teardown establishes actor termination or records failures to erase safely. U17 remains for authority setup evidence fields and binary association.

## 17. Extension examples and caller authorization — lines 1254–1320

**What do I now believe?** Extension examples require separate baseline, during and after access observations, and redelegation is a second actor's own issuance. Executed support is scoped to concrete signed builds, inputs and platforms. Client reservation, invocation, receipt and interpretation are separate. Host connection authorization optionally checks equal nonempty Team IDs and an identifier allowlist; shipped settings enable it, but absent/invalid Boolean selects false. This check is separate from contract equality.

**What supports that belief?** Lines 1264–1293 describe example schedules and scoped execution. Lines 1300–1302 distinguish transport boundaries. Lines 1309–1313 define authorization settings. Line 1320 begins bounded reservation acquisition.

**What remains uncertain?** U17 is answered for connection authorization, while executable-association checks remain pending. U04 now also includes the meaning of the “executed” support grade. U29: reservation retry, one-use host lifecycle and how invocation knowledge is represented are not yet complete. U27's native outcomes remain deliberately scoped, not universal guarantees.

## 18. Once-only invocation and original deadline — lines 1321–1388

**What do I now believe?** A host's reservation slot never becomes reusable after expiry/disconnect. Acquisition can retry with new UUIDs within one deadline; execution is invoked once on the granting connection and never replayed. Control admission checks identity before descendants and retains rejected byte count/hash. Peer PID/instance remain peer assertions. Transport error after invocation leaves receipt and effects uncertain. The controller's output drain/wait has no separate deadline, so the client allowance is not a bound on all host cleanup.

**What supports that belief?** Lines 1322–1337 define slot retirement and control admission. Lines 1342–1344 define once-only execution. Lines 1349–1357 define deadline, clock failures, collection and uncertainty. Lines 1373–1388 begin control schemas.

**What remains uncertain?** U29 is answered for retry/invocation rules, but capture schema and admission remain pending. U10 remains for rejected capture/reply retention. U30: native replies between retention and frame limits are explicitly unobserved. I cannot predict their native transport behavior from this account. U06 remains for the binary frame layout.

## 19. Capture and acquisition records — lines 1389–1455

**What do I now believe?** Capture retains client identity, continuous-clock availability/readings, ordered acquisition attempts, irreversible submission state and a terminal event. A grant can coexist with no invocation. Receipt of runner_reply means callback receipt, with controller admission still outstanding. Acquisition retries follow only occupied, transport loss or RPC timeout. Rejected controls retain full count/hash while admitted peer fields remain conditional.

**What supports that belief?** Lines 1399–1414 enumerate capture fields. Lines 1433–1441 define attempt order, timings, outcomes and diagnostics. Lines 1449–1455 separate complete control-byte observations from admitted fields.

**What remains uncertain?** U29 is partly answered by capture fields; consistency constraints linking terminal, submission and attempts are still unknown. U10 remains for actual retained reply bytes and failed-capture projection. U31: the capture's PID and clock assertions are visible, but I do not yet know how the controller validates their consistency rather than trusting them wholesale.

## 20. Retained host bytes and controller process observations — lines 1456–1523

**What do I now believe?** Submission state is authoritative only after capture admission. The client retains exactly the bounded prefix of host bytes with complete/retained counts and truncation; truncated frames are refused before decode. Public base64 must decode to the retained length. Client diagnostics have byte bounds without splitting Unicode scalars. Controller process records distinguish wall-clock launch/collection times, exit status, stdin delivery and transport admission.

**What supports that belief?** Lines 1465–1466 define submission authority. Lines 1475–1492 give retained-byte arithmetic and encoding. Lines 1503–1509 define diagnostics. Lines 1518–1523 begin controller observations and admission fields.

**What remains uncertain?** U10 is partly answered for host prefixes and truncation, but rejected outer captures still need their representation. U31 remains for the capture consistency checks. U32: request_delivery and its precedence over apparently valid client output remain to be explained. I would not read a zero client exit as successful experiment execution.

## 21. Admission precedence and raw retention — lines 1524–1592

**What do I now believe?** Failed stdin delivery wins over all capture interpretation; retention loss wins over decoding, and empty output has its own missing outcome. These paths preserve unknown submission. Complete admitted capture can still contain a separately rejected host frame. Rejected client stdout is an untagged format/base64 object; retained stderr is replacement-decoded text. Successful writes establish pipe acceptance, not child receipt. Typed binary responses differ from JSON requests/controls and validator lines.

**What supports that belief?** Lines 1524–1535 give projections and stream bounds. Lines 1540–1552 specify precedence and semantic checks. Lines 1561–1562 define stdin observations. Lines 1569–1584 define retained alternatives; lines 1589–1590 introduce encoding boundaries.

**What remains uncertain?** U10 and U32 are answered for retention and delivery precedence. U31 is answered at the named-check level (chronology, UUIDs, terminal combinations and lengths), though exact predicates are not all displayed. U06 remains for frame grammar. U33: “porcelain” is now the expected binary encoding name; its primitives are still pending.

## 22. Exact binary grammar and budgets — lines 1593–1665

**What do I now believe?** Porcelain frames use PWP1, a 32-byte schema fingerprint, then one length-delimited typed root. Fixed little-endian primitives, sorted fields/maps and declared variants are enforced. Structural admission checks exact schema and producer before descendants; semantic consistency remains separate. Frame, decoded-storage and retention caps are distinct. JSON projection converts bytes and omits selected equal path forms. Constructed decoder/writer executions support specific refusal/fallback behavior, not all native transport sizes.

**What supports that belief?** Lines 1597–1619 define framing and kinds. Lines 1631–1633 define admission; lines 1638–1648 give budgets, fingerprint inputs and projections. Lines 1653–1660 distinguish constructed execution scopes.

**What remains uncertain?** U33 is answered for encoding primitives. U06 is answered for frame grammar but remains for worker shared-header layout. U05 still lacks the complete canonical record/tag inventory, which is referred to as the wire surface's canonical shape. U34: rich-to-minimal host fallback is introduced; its triggering and interpretation rules remain ahead.

## 23. Validator protocols have distinct result meanings — lines 1666–1738

**What do I now believe?** Batch queries are strict flat JSON strings with per-line failures; duplicate recognized keys keep the last. Native batch allow/deny require specific rc/errno pairs. Host reply-line admission keeps accepted prefixes, stops at the first bad frame, and permits extra raw fields/unfamiliar diagnostics. PID-only direct status checks syntax, not existence. Direct JSON, plain and batch exits/denial meanings differ; RAW numeric-zero has mode-dependent argument handling.

**What supports that belief?** Lines 1669–1679 define batch parsing and native classifications. Lines 1684–1686 define host framing/types/bounds. Lines 1705–1719 define direct PID/filter/query behavior. Lines 1726–1734 explicitly distinguish the modes and support limits.

**What remains uncertain?** U23 remains for how admitted validator records are uniquely associated and made comparison-eligible. U35: I do not yet know collector aggregate stream/record limits or rejection-context fields. I would not infer process existence from PID-only success or a sandbox deny from direct JSON's denied flag alone.

## 24. Direct validator output schemas — lines 1739–1815

**What do I now believe?** PID-status objects carry kind/version/PID and null error, establishing accepted syntax only. Direct native results retain operation/filter spelling and numeric filter ID, raw rc/errno, and booleans based solely on rc. The filter ID is recorded before adding the no-report flag. These direct output names are not equivalent to the batch allow/deny vocabulary.

**What supports that belief?** Lines 1741–1772 define status fields and predicates. Lines 1781–1792 enumerate native result fields and boolean meanings. Lines 1798–1809 constrain kind/version/PID.

**What remains uncertain?** No new uncertainty arises in these schemas. U23 and U35 remain for the host collector's use of batch records. I continue to treat the native meaning of rc/errno as belonging to the exact operation and mode already described.

## 25. Helper output is an independent compilation — lines 1816–1892

**What do I now believe?** Direct argument errors distinguish PID and filter failures without inventing native results. Helper data records source hash, platform, parameter presence/count, last native stage and import inventory. Import walking precedes compilation and survives compile failure. Fallback is a separate helper-process attempt alongside transport/worker evidence. Helper verdict selects success, compile error with native or fixed diagnostic, then setup error.

**What supports that belief?** Lines 1843–1847 define direct argument-error projections. Lines 1858–1864 define helper fields. Lines 1869–1871 give inventory/compile ordering and independent process scope. Lines 1878–1885 give verdict precedence.

**What remains uncertain?** U20 is answered for helper data/verdict, still pending fallback invocation conditions and capture. U21 remains for literal import inventory coverage and file resolution. U19 remains for native SBPL semantics beyond the reported compiler observations. U36: last native-stage details and inventory limits are not yet visible.

## 26. Literal inventories are read-specific — lines 1893–1964

**What do I now believe?** Helper stage records distinguish parameter creation/assignment from compilation and preserve native diagnostics separately from summary text; even an empty diagnostic prevents helper success. Literal import walks use a stated two-directory search, bounded recursion/count and held bytes for hash/scan. Their closure hash describes that walk, not necessarily the worker's later compiler reads. Controller, helper and worker can see changed imports independently. Fallback status may preserve an unfamiliar supported helper outcome.

**What supports that belief?** Lines 1906–1918 define native stages and cleanup. Lines 1927–1934 define inventory/search/hash. Lines 1939–1950 state separate reads and unestablished native collision precedence. Lines 1959–1964 begin fallback capture fields.

**What remains uncertain?** U21 is answered for inventory mechanics, while native collision precedence, macro dependencies and changing-file agreement remain explicitly limited. U36 is answered for stages and inventory bounds. U20 remains for when fallback runs and how supported envelopes are admitted. I cannot use a closure hash alone to identify the worker's full native compilation inputs.

## 27. Fallback trigger and extension event publication — lines 1965–2038

**What do I now believe?** Fallback occurs only after admitted xpc_error capture with successful request delivery, and uses held input; actor policies get separate helper requests in order. Capture failure precedence and helper identity/kind/outcome checks are explicit. Extension events separate pre-call marker, completed publication and native return. Missing publication withholds native results. Consume -1 yields no handle; another result is only a candidate handle. Non-null issue and custody acceptance remain distinct.

**What supports that belief?** Lines 1977–1981 state fallback eligibility/classification; lines 1989–1995 define per-actor fallback. Lines 2007–2026 define event fields. Lines 2033–2035 define issue projection.

**What remains uncertain?** U20 is answered for fallback invocation and admission. U27 is partly answered for native result/handle rules; transfer/resource accounts remain ahead. U28 remains for cleanup evidence. U37: I do not yet know what invalid completed extension slots lose, or whether event inconsistency invalidates broader actor assessments.

## 28. Delivered and source-acknowledged are separate — lines 2039–2110

**What do I now believe?** Transfer records retain host request/custody/copy/equality/recipient acknowledgement, plus independent source acknowledgement. Delivered requires the complete host/recipient chain but not a completed source answer. Acknowledged source requires a unique matching completed event and known-status equality. Resource tables include unreached/unresolved declarations. A non-null issue without host custody becomes issued_uncustodied, not issued; missing publication needs evidence before being called not_reached.

**What supports that belief?** Lines 2040–2058 define transfer fields. Lines 2065–2069 define delivered prerequisites. Lines 2074–2082 define source association. Lines 2089–2095 retain declared resources, and lines 2105–2110 begin token-status classification.

**What remains uncertain?** U27 is answered for transfer/issue status distinctions, with delivery and handle detail pending. U37 remains for broader semantic-invalidity consequences. U28 remains for cleanup/termination evidence. I would not treat source timeout as disproving a delivered host transfer.

## 29. Resource status and first refusal — lines 2111–2180

**What do I now believe?** Delivery records prefer host acknowledgement; handle production requires a published consume result other than -1. Equal raw handle numbers do not merge declared identities. Release_attempted means observing the native call marker, not successful release. Refusal codes are open and machine paths are bounded; one failure reports the actual first reached branch. Contract checks precede unknown root fields, and closed-object unknown keys precede declared-field decoding.

**What supports that belief?** Lines 2122–2130 define delivery evidence. Lines 2141–2149 define handle identity, status and release marker. Lines 2167–2175 define refusal fields and branch order.

**What remains uncertain?** U27 is answered for resource/handle status. U14 remains for the exact pre-child refusal consequence, introduced by the final heading. U37 remains for invalid record effects. U28 remains for cleanup evidence. I would not equate a produced candidate handle with proven access authority without a later access observation.

## 30. Refusal consequences at host and controller — lines 2181–2250

**What do I now believe?** Host request refusal starts no workers/validators, sets bad_request/rc 1 and empty steps, while independently safe metadata may survive. Controller preparation refusal retains the specimen dossier but no client/result/sandbox diagnostics. Malformed requests yield bad_request/exit 1; local tool/input-resolution failures yield tool_error/exit 2. Refusal precedence belongs to each traversal; correcting one error can expose another. Projection preserves either producer's structured refusal.

**What supports that belief?** Line 2181 states the host consequence. Lines 2186–2202 give example families and boundary-local order. Lines 2223–2234 give controller consequence and exits. Lines 2242–2247 define projection.

**What remains uncertain?** U14 is answered for refusal consequences and major capacities, but metadata echo rules remain ahead. U15 still needs dossier fields. U38: which metadata survives a malformed request and how later reporting failure differs from request refusal remain unknown.

## 31. Safe echo and later failures — lines 2251–2324

**What do I now believe?** Capacity refusals count complete submitted values with explicit units. Each echoed label is independently checked; an unsafe path is withheld whole, even when a parameter key can safely survive in another field. Absent-path prediction can coexist with a later successful creation and later-resolving diagnostics. Client timeout, host timeout, launch failure, unpublished operation and reporting failure identify different stopped boundaries.

**What supports that belief?** Lines 2265–2284 define capacity evidence and sanitization. Lines 2293–2307 give correction and absent-path examples. Lines 2319–2322 distinguish post-invocation failures and preservation.

**What remains uncertain?** U38 is answered for safe metadata echo, while reporting failure retention remains ahead. U22 is answered for the temporal realpath distinction; exact diagnostics fields remain pending. U34 remains for reporting fallback. U13/U24/U28 remain for lifecycle/cleanup evidence and consequences.

## 32. Host report locations and aggregate meaning — lines 2325–2395

**What do I now believe?** The host report combines summary and separately owned observations. finished means execution/required collection completed, not all attempts succeeded. Ordinary and actor evidence occupy different locations; top-level PID can be worker or host depending on form/output availability. Actor declarations may survive preparation failure without proving launch. Ordinary classification checks worker failures/publication/supervision before first unsuccessful phase collection.

**What supports that belief?** Lines 2327–2329 distinguish reporting retention forms. Lines 2345–2374 enumerate host fields and availability. Lines 2379–2384 define assembly/classification. Lines 2390–2395 start outcome commitments.

**What remains uncertain?** U01 is answered for the host record map, with subordinate observations still ahead. U34/U38 remain for reporting failure rules. U39: complete host outcome precedence and which evidence a finished claim requires remain pending. U11/U37 remain for recipient semantic admission and unsupported assessments.

## 33. Reporting fallback preserves rejected observations — lines 2396–2465

**What do I now believe?** Reporting failure first produces a rich copy with new failed summary, original summary diagnostics and no step comparisons. If that fails, an independent minimal writer keeps scalar identity/context and empty steps/phases; failure again yields empty bytes. Rich fallback may retain the association defect that caused degradation because ordinary actor/phase checks are bypassed. Therefore retention does not establish valid associations. Probe rows separate query, attempt and optional comparison.

**What supports that belief?** Lines 2411–2417 define failure fields; lines 2422–2436 define fallback stages and consequences. Lines 2441–2445 explicitly leave reporting-failure associations as a maintainer decision. Lines 2457–2462 define probe-result locations.

**What remains uncertain?** U34/U38 are answered for reporting fallback. U37 is partly answered: comparisons are removed, but association integrity is an explicit open commitment. U11 remains for controller-side semantic checks and assessment withholding. U39 remains for detailed successful-execution predicates beyond the outcome list.

## 34. Query and attempt provenance qualify scalar results — lines 2466–2535

**What do I now believe?** Query rc can be synthetic zero alongside error, so provenance/outcome must qualify it. Unassociated records remain in validator evidence; a step only uses uniquely associated accepted records. Attempt fields distinguish requested action, worker publication and synthetic missing-result reasons. Fresh/exec detail belongs to completed slots. Child spawning and later child outcome remain separate even when aggregate exec fails. Host path diagnostics happen after orchestration.

**What supports that belief?** Lines 2471–2483 define query provenance/rc/diagnostics. Lines 2493–2502 define retained validator records. Lines 2512–2529 define attempt publication, native detail and child outputs.

**What remains uncertain?** U23 remains for exact association/order predicates and comparison categories. U12 now has record locations but fresh-operation fields are ahead. U13/U24 remain for lifecycle support of unpublished attempts. U40: path diagnostics may differ from operation-time targets; their canonicalization/comparison rules remain unknown.

## 35. Comparison describes relations, not agreement — lines 2536–2606

**What do I now believe?** Comparison reports attempt observation class/basis, mapped operation relation, submitted-target relation and established/unestablished order. Target equality concerns submitted strings, not later canonical path identity. query_first needs collection/release/acknowledgement and owned lifetime. Path diagnostics explicitly identify host/after-orchestration, omit equal forms through same_as_input and preserve unavailable nulls. Leaf-following and parent-resolved forms differ.

**What supports that belief?** Lines 2538–2543 define comparison fields. Lines 2552–2557 define ordering observations. Lines 2567–2572 and 2582–2587 define query/attempt path forms. Lines 2596–2600 define stat identity components.

**What remains uncertain?** U40 is answered for diagnostic timing/forms and submitted-target comparison. U23 remains for exact eligibility and operation mapping. U41: I do not yet know the attempt observation classification's precedence or how permission-shaped evidence is kept separate from sandbox cause. U12 remains for fresh read/write field semantics.

## 36. Fresh operation boundaries and ordering prerequisites — lines 2607–2678

**What do I now believe?** Fresh read records open/stat/read/close separately and preserves empty successful content. Fresh write/create records preopen/opened/truncated/written metadata at reached boundaries; short writes retain count without invented errno. Step assembly synthesizes unavailable channels and keeps excluded queries synthetic even if a matching unexpected frame appears. query_first requires the full chain, valid setup and native allow/deny evidence, not merely a nonmissing result.

**What supports that belief?** Lines 2607–2648 define metadata and fresh operation fields. Lines 2657–2663 define two-channel assembly. Lines 2672–2678 begin the ordering prerequisites, including setup and native-answer predicates.

**What remains uncertain?** U12 is answered for fresh-operation fields and success meaning. U23 remains until the rest of the ordering/association rule appears. U41 remains for classification precedence. U13/U24 remain for how incomplete worker publication affects lifecycle claims rather than fabricated native results.

## 37. Exact query association and observation classification — lines 2679–2752

**What do I now believe?** Ordering counts every record with the step ID and requires exactly one with matching operation, outcome, rc/errno and filter/value for the live worker. Another query's failure does not remove this probe's eligibility. query_first still precedes the entire batch, so intervening actions can change state. Classification prioritizes observed spawn, then completed success, permission-shaped failure, other failure, unavailable. It does not attribute the cause. create operations have unresolved compound-operation relation; string equality does not identify runtime objects.

**What supports that belief?** Lines 2679–2687 define association. Lines 2692–2697 limit temporal meaning. Lines 2706–2723 define classification precedence. Lines 2728–2748 define mappings and unlink timing.

**What remains uncertain?** U23 and U41 are answered for ordering/association/classification. U11 remains for recipient enforcement of these predicates. U12's fresh aggregate projection is still to come. U42: the table's mach_lookup/bootstrap_look_up spelling differs from the earlier mach/lookup request spelling; I infer it names the same native operation, but this portion does not explain the naming relation.

## 38. Fresh aggregates retain first failure — lines 2753–2825

**What do I now believe?** Fresh operations continue their documented reached sequences and keep unreached fields absent; creation's preopen stat is diagnostic. Read aggregate precedence is open, stat, read, close. Write precedence begins open, opened stat, truncate, truncated stat, write, written stat, close. Missing/nonzero errno is projected separately, so a failed aggregate need not have errno. Host path enrichment remains an after-orchestration observation and preserves supplied operands.

**What supports that belief?** Lines 2754–2762 state native sequences. Lines 2769–2784 define path enrichment. Lines 2792–2803 give read projection. Lines 2813–2825 give the first thirteen write cases.

**What remains uncertain?** U12 is essentially answered, but the write table continues past this portion. U43: these aggregate tables alone can fall through when fields are absent; I expect separate fresh-record validation to enforce required reached operations, but have not yet seen that enforcement. U11 remains for recipient consistency validation.

## 39. Worker supervision preserves unknown disposition — lines 2826–2890

**What do I now believe?** Fresh-write aggregation ends with close failure then success. Worker supervision distinguishes spawn PID, owned wait status, publication, timeout, exit request, termination call and confirmed reap. A readiness timeout is merely a missing hint and execution continues. Final reads may occur while execution may continue; that constrains absence claims. Canonical disposition determines partial_steps. No successful reap leaves final status unresolved; competing exit/signal forms conflict.

**What supports that belief?** Lines 2826–2829 complete write projection. Lines 2845–2864 define worker fields, timing and collection basis. Lines 2870–2880 relate canonical claims. Lines 2889–2890 begin final-status precedence.

**What remains uncertain?** U13 is partly answered by owned wait/reap and canonical status; full disposition questions remain ahead. U28 is partly answered by collection_basis but cleanup safety rules remain pending. U06 remains for worker publication layout. U43 remains for validation of missing fresh-operation fields.

## 40. Lifecycle claims copy evidence without filling gaps — lines 2891–2960

**What do I now believe?** After confirmed reap, one exit/signal form supports final status; no usable form stays unresolved. Recorded poll stop and collection basis are copied as supported observations, while missing values remain not_recorded. Host waits use CLOCK_MONOTONIC with explicit excluded work and clock faults. kill records establish only the native request return; waitpid establishes ending. Failed waits remain visible even after recovery.

**What supports that belief?** Lines 2891–2895 complete final-status rules. Lines 2900–2918 copy recorded stop/basis. Lines 2926–2935 define wait measurements. Lines 2943–2960 distinguish termination requests and failed wait records.

**What remains uncertain?** U13 is answered for final-status evidence, but termination-cause and per-step reach/interruption rules remain ahead. U24 remains for exec-child supervision. U44: I do not yet know how host CLOCK_MONOTONIC budgets relate to the continuous-time client/worker clocks during system sleep; I will retain the named clock domains separately.

## 41. Policy transport and independent worker publications — lines 2961–3033

**What do I now believe?** Host accepted writes and worker EOF receipts describe opposite pipe ends. Policy-transfer deadlines persist through partial/interrupted writes. Worker evidence checks region identity then acquire-reads independent progress, failure, readiness, diagnostic and receipt publications. Reported ABI identity is host-selected after region checking. Progress packs open numeric operation/stage/index values; unfamiliar values survive without known lifecycle meaning.

**What supports that belief?** Lines 2969–2988 define pipe timeout/error observations. Lines 2996–3007 define worker snapshot and publication scope. Lines 3015–3022 define progress packing and unknown handling. Lines 3030–3033 begin terminal failure codes.

**What remains uncertain?** U06 is partly answered for publication structure, but not the complete shared-header byte layout. U45: I do not yet know the publication state codes/guards or the exact progress operation mapping. U13 remains for how these positions support per-action reach/completion/interruption. U44 remains for clock-domain relationships.

## 42. Publication guards and terminal reach claims — lines 3034–3105

**What do I now believe?** Readiness helper publication and host byte receipt remain separate. Diagnostic text requires completed/truncated state, bounded length and NUL terminator; invalid UTF-8 is replacement-decoded only afterward. Worker receipt publishes EOF counts before comparing them, proving length agreement only. Canonical lifecycle resolution uses unique slots and acquired progress. not_reached needs terminal collection; a completed slot versus earlier terminal progress conflicts. Live missing publication stays unresolved.

**What supports that belief?** Lines 3044–3049 define readiness. Lines 3057–3064 define diagnostic guards. Lines 3072–3077 define EOF receipt. Lines 3085–3102 define canonical resolution and D1/D5 conflict examples.

**What remains uncertain?** U45 is answered for diagnostic publication guards, but full failure/progress numeric mapping remains pending. U13 is partly answered for reach and publication; interruption/cause predicates remain ahead. U46: I do not yet know all canonical claim states, conflict rule meanings, or how these project into attempt lifecycle summaries.

## 43. Canonical claims and conflicts — lines 3106–3178

**What do I now believe?** Per-attempt lifecycle copies boundary/result claims from the first matching canonical step, with actor ownership added in actor form; missing either claim omits the projection. Claims distinguish supported, unresolved, conflicting and inapplicable, with state-specific answer/reason/issue/basis fields. D1 identifies competing status representations; D5 identifies incompatible terminal progress and slot publication. Integer/request values remain question-specific.

**What supports that belief?** Lines 3108–3129 define ordinary/actor projection. Lines 3137–3147 define claim shape. Lines 3155–3160 define values. Lines 3168–3174 define conflicts.

**What remains uncertain?** U46 is answered for claim states/conflict meanings and basic projection, but summary selection and run questions remain pending. U13 still needs host-termination attribution/interruption predicates. U11 remains for enforcement of claim shapes and joins by the controller. I would not infer a unique canonical input solely from a producer rule that takes the first match; consistency validation must establish that separately.

## 44. Lifecycle summaries and owned endings — lines 3179–3250

**What do I now believe?** Run questions separately cover final status, stop, cleanup/grace/kill and progress association. Duplicate slot IDs cannot supply a unique join. Attempt summaries derive from boundary/result/applicability but remain an open vocabulary at the controller. An owned reap records matching PID/native return, raw status, observation stage/time, uninterrupted ownership, prior departure request and a shared ordinal for gates/activations.

**What supports that belief?** Lines 3184–3190 list run questions. Lines 3198–3220 define unique slots and separate step questions. Lines 3231–3233 define summary retention. Lines 3241–3250 define owned ending evidence.

**What remains uncertain?** U46 is answered for account fields and summary names, while exact summary/interrupt classification predicates remain to come. U26 remains for the full natural-reap gate. U13 is partly answered by owned ending evidence; it still does not by itself establish cause. U11 remains for reader consistency checks.

## 45. Validator collection retains records without guessed joins — lines 3251–3322

**What do I now believe?** Gates reference an owned ending by ordinal. Native spawn failure is recorded before any child exists and is not an exit status. Validator collection budgets scale with query count; byte overflow keeps the complete LF-framed prefix and counts all received bytes. Accepted records survive later transport/cleanup failures. Only unique expected IDs with agreeing supplied metadata join to steps; allow/deny require full identity. Duplicate/null IDs remain unassociated.

**What supports that belief?** Lines 3256–3260 define reap reference. Lines 3268–3276 define spawn failures. Lines 3283–3306 define collector limits and records. Lines 3311–3317 define exact joins and preservation.

**What remains uncertain?** U35 is answered for aggregate bounds and accepted-prefix retention; decode-fault fields remain ahead. U23's association rule is reinforced with collector-side consequences. U24 remains for exec child output/cleanup. U26 remains for gate eligibility and timing. U39 remains for detailed collection-summary classification.

## 46. Association counts and rejected-frame context — lines 3323–3392

**What do I now believe?** Association issues retain actual group counts for missing, duplicate, unexpected and null IDs, with metadata mismatch separate. The first rejected validator frame retains receiver category, byte offset, frame size and exact capped prefix; earlier accepted records remain. Exec observation begins with collection facts frozen before cleanup/termination, so later reap cannot rewrite what collection observed.

**What supports that belief?** Lines 3324–3349 define issue cardinality. Lines 3357–3368 define decode-fault context. Lines 3376–3383 define association issue meaning. Lines 3390–3392 establish the exec collection/cleanup separation.

**What remains uncertain?** U35 is fully answered for collection limits and rejection context. U24 remains for exec collection/cleanup fields and their success criteria. U39 remains for aggregate phase/host classification. No new uncertainty is introduced by the association-count tables.

## 47. Exec collection, cleanup and reap — lines 3393–3463

**What do I now believe?** Exec collection observes leader exit independently of stream EOF, including descendants holding pipes open. It distinguishes child/plan deadline, observation error and clock fault. Cleanup is not requested after leader_exit_and_eof; failed waitid leaves ownership unconfirmed. Eligible cleanup signals the process group, with leader fallback only after non-ESRCH group failure. Final bounded reap concerns the owned leader and preserves earlier failure priority.

**What supports that belief?** Lines 3401–3412 define collection. Lines 3420–3426 define stream observations. Lines 3434–3440 define cleanup states. Lines 3448–3455 define signal targets/results. Lines 3461–3463 define reap allowance and priority.

**What remains uncertain?** U24 is partly answered; final reap fields and aggregate exec success rules remain ahead. U28 remains for whether leader reap establishes cleanup of every descendant; the text so far only commits to the leader and request targets. U44 remains for clock domains, though exec explicitly uses continuous time.

## 48. Actor evidence and preparation refusal — lines 3464–3537

**What do I now believe?** Exec wait status exists only when waitpid returns the owned leader; pending and failed returns remain distinct. Actor rows appear in request order and separately own host source hash, worker-received hash, setup classification, final application publication, launch/equipment and reap. Declared visits include unactivated phases. Preparation refusal retains admitted declarations/preparation observations but no execution entries, launches or applications. Degraded reporting preserves assembled associations without ordinary consistency guarantees.

**What supports that belief?** Lines 3472–3479 define exec wait fields. Lines 3492–3514 define actor records. Lines 3519–3526 define report ownership and degraded scope. Lines 3532–3537 state preparation-refusal shape.

**What remains uncertain?** U24 is answered for exec observation records, but aggregate consistency/success checks remain for the reader section. U11/U37 are partly answered by ordinary-versus-degraded applicability. U47: how application assessment distinguishes native failure, late success and setup deadline remains ahead. U26 remains for gate evaluation.

## 49. Reader scope and application-boundary assessment — lines 3538–3610

**What do I now believe?** Degraded replies receive degradation/profile checks, while a lifecycle reader can separately assess retained worker claims; ordinary actor associations remain conditional. Actor launch uses empty environment and explicit descriptors for policy/evidence/readiness/optional authority. Application assessment describes whether the apply boundary is observed, including native failure; it is not simply success. Classification has explicit precedence and ordinary replies require one associated authority row per actor.

**What supports that belief?** Lines 3544–3551 define reader applicability. Lines 3563–3571 define actor launch. Lines 3579–3584 define application states/bases. Lines 3589–3610 define authority association and begin classification with unapplied then unlaunched.

**What remains uncertain?** U47 is partly answered; remaining application cases and deadline interaction are pending. U11 is partly answered for reader scope, with detailed controller check consequences still ahead. U17 remains for static/live equipment association. U06's full shared-header layout still has only references and publication descriptions.

## 50. Application can be observed after eligibility ends — lines 3611–3678

**What do I now believe?** Applied publication outranks authority/native failure branches. Known terminal pre-apply failures support not_attempted; apply failure supports observed; apply progress without result remains unobserved. A setup timeout may later retain applied true/count 1 while still forbidding activation/query collection. Phase records separate declared IDs from arrival/completion, invoked collection and activation; collected does not imply successful I/O. Timing/ordinal observations have separate availability.

**What supports that belief?** Lines 3611–3619 complete application precedence. Lines 3624–3626 establish late-application behavior. Lines 3635–3651 define phase fields. Lines 3659–3676 define activation and intervals.

**What remains uncertain?** U47 is answered, including late-publication versus eligibility. U09 remains only for schedule budgets/cancellation detail. U26 remains for termination gates. U45 gains some operation codes (apply 8, compile 5, timing 12), but the complete progress code map is still not stated here.

## 51. Natural termination gate and cancellation — lines 3679–3750

**What do I now believe?** Actor schedules have lifetime/collection allowances, with reported collection maximum differing from a reduced override. A gate waits without requesting source departure, after final source activation and before dependent activation. Satisfaction needs owned natural reap, ordered ordinals/timestamps and timely accounting; signaled ending can qualify because natural means no host departure request. Failed evaluated gates cancel all remaining phases. Unreached gates differ: unavailable dependent actor can leave later phases schedulable. A late reap can coexist with timed_out.

**What supports that belief?** Lines 3684–3691 give schedule fields. Lines 3700–3709 define gates. Lines 3714–3719 preserve declared rows. Lines 3724–3748 define evaluation, cancellation and outcomes.

**What remains uncertain?** U26 is answered for wait, satisfaction, late ending and cancellation. U09 is answered for schedule/gate behavior at this level. U28 remains for cleanup after unconfirmed actors. U44 remains: host gate timing is monotonic while client/exec use continuous clocks, with no cross-domain conversion stated here.

## 52. Gate checking and equipment inventory — lines 3751–3824

**What do I now believe?** Controller gate findings retain the reply and actor assessments but invalidate aggregate disposition and leave termination cause unknown. Gate validity checks owned status, source-local sequence, timing and independent dependent-actor eligibility. Ordinals are per actor; cross-process order needs timestamps. Global gate-failure cancellation is current behavior, with narrower reach a maintainer decision. Actor launch preparation begins by checking service seal and bounded inventory identity.

**What supports that belief?** Lines 3754–3762 define gate check/consequences. Lines 3774–3776 state cancellation's open design question. Lines 3787–3792 explain sequences. Lines 3804–3818 define inventory observations.

**What remains uncertain?** U11 is partly answered with a concrete assessment-withholding consequence. U07/U16/U17 remain for static/live binding, now introduced by inventory. U48: the seal proves an inventory boundary, but I do not yet know how inventory hashes relate to signed worker files and the live process. The cancellation design question is open, though its current behavior is clear.

## 53. Static binding checks both packaged roles — lines 3825–3898

**What do I now believe?** Sealed inventory names exact public/worker identities and both signed worker roles with file hash, CodeDirectory hash, signing identity/team and entitlement dictionary. Static binding checks actual chosen file properties against this baseline. Both packaged roles must pass even if unused; any preparation failure prevents all actor launches. Fixture overrides add inspected rows labeled unverified_fixture and cannot rescue failed packaged equipment. No automatic role fallback occurs.

**What supports that belief?** Lines 3826–3847 define inventory rows. Lines 3854–3874 define binding evidence. Lines 3879–3886 define preparation and overrides. Lines 3893–3897 require packaged digest/entitlement equality.

**What remains uncertain?** U48 is answered for static inventory-to-file association; live process association remains pending. U07/U16/U17 still need entitlement-readback and live checks. U03's build configuration/SDK evidence is still not described by these static bindings. I would not mistake unverified_fixture for packaged implementation identity.

## 54. Live inspection binds the owned actor to static equipment — lines 3899–3972

**What do I now believe?** Entitlement rows preserve actual bounded plist dictionaries and identify static versus execution sources. Required keys must be Boolean true. Before activation, the host inspects the setup-usable owned actor's code, dynamic validity, associated static code and signing information, comparing file/signature/entitlements to binding. Mismatch or inspection failure cancels all scheduling while retaining earlier setup/application evidence. Inspection has shared setup and additional monotonic deadlines distinct from workers' continuous cutoff.

**What supports that belief?** Lines 3903–3912 define read-back. Lines 3933–3943 define actor selection. Lines 3951–3965 define live inspection fields. Lines 3970–3972 define matching, cancellation and separate deadline origins.

**What remains uncertain?** U07/U17/U48 are answered for actor static/live association. U16 is answered for actor entitlement demands, but external runner resolution is still ahead. U44 is partly answered: the clocks/deadlines are explicitly separate, not one shared timeline. U49: I do not yet know the authority setup/cleanup account's exact publication and integrity requirements.

## 55. Inspection limits and preparation-refusal shape — lines 3973–4044

**What do I now believe?** Live inspection retains an attempted prefix and stops at first failed Security call; prior cancellation reason wins. Constructed failures support branch behavior, while spontaneous native failure after apply is unobserved. Preparation refusal produces runner_failed, empty execution/resource tables, retained declaration/equipment rows and not_attempted host authority setup. Actor rows show launch_refused and zero applications, with worker authority decisions not_observed.

**What supports that belief?** Lines 3974–3984 state inspection scope/limits. Lines 3991–4009 define eligibility and native call rows. Lines 4016–4044 define preparation stages and exact retained shape.

**What remains uncertain?** U49 remains for actual authority setup scopes and operation records. U11 remains for general recipient semantic checks. U50: spontaneous Security failures are an explicit evidence limit; I cannot infer their native frequency or full integrated behavior from injected controls. Preparation-refusal representation itself is now clear.

## 56. Authority scopes retain independent operation cells — lines 4045–4115

**What do I now believe?** Authority evidence separates host run/regions/custody and one worker scope per actor. Scope decisions, operation cells and ownership/erasure states are independently observed. A failed unlink can retain a named cleanup reference. Host reads decision first, then cells; valid cells can survive absent/invalid decision, and missing primary support adds integrity error. terminal_required_failure needs required setup and a published primary failure/rejection.

**What supports that belief?** Lines 4057–4075 define scope ownership. Lines 4083–4096 define fields and cleanup state. Lines 4101–4115 define acquisition ordering and decision/primary requirements. Lines 4045–4050 finish declaration-order retention.

**What remains uncertain?** U49 is partly answered for publication/integrity. U28 is partly answered for explicit unresolved ownership, but recovery details and safe erasure prerequisites remain ahead. U51: operation-cell kinds/slot meanings and cleanup-reference identity are not yet specified. I would not treat observed decision alone as proving every associated native operation.

## 57. Authority operation slots and recovery reference — lines 4116–4188

**What do I now believe?** Authority cells have fixed registered slots, native-kind-specific states/fields and separate cleanup failures. Memory/symbol/validation observations do not invent integer returns. Failed shm_unlink after creation retains a name, host PID and nonce as unresolved_manual; recovery must establish current ownership because names can be reused. Compiled-profile receipts concern pre-apply worker capture, with host capture status and component/stage/nonce/bytecode fields.

**What supports that belief?** Lines 4124–4146 define cells and slot registry. Lines 4154–4162 define recovery references. Lines 4168–4188 introduce profile receipt scope and fields.

**What remains uncertain?** U49/U51 are answered for authority operation/publication records. U28 remains open operationally for how a caller establishes current ownership during manual recovery; the requirement is stated but no procedure is given here. U18 remains for full receipt checks and consistency limits, especially that controller label validation has no external request nonce operand.

## 58. Capture requires successful application and completion — lines 4189–4260

**What do I now believe?** Receipt bytes come from the compiler object passed to sandbox_apply, copied before apply, but captured status additionally requires observed successful apply and normal completed worker. Host checks capture publication/status, PID/nonce, type/extent/hash and source/parameter identities in order. A failure withholds capture payload/context fields and does not alter the run summary. Receipt absence is ambiguous if no worker output exists. Parameter digest framing is explicit and order-independent.

**What supports that belief?** Lines 4189–4193 define payload/input fields. Lines 4210–4218 define parameter hashing/presence. Lines 4225–4240 define ordered guards and consequences; lines 4246–4258 name first guard reasons.

**What remains uncertain?** U18 is partly answered for host capture, but controller/consumer validation and what bytecode implies about imports remain ahead. U52: a valid receipt establishes the captured object and input agreement; I do not yet know whether the document promises interpretation or replay of those opaque bytes. I would not treat pre-apply capture alone as a captured receipt after later worker failure.

## 59. Controller receipt checking is label-only — lines 4261–4333

**What do I now believe?** Host capture failures have ordered specific reasons. Controller reply admission checks receipt status/producer/stage labels, including in degraded/preparation replies; it does not recompute bytecode/input digests or compare nonce to a retained request. Label failure retains the decoded host report but rejects admission, suppresses diagnostics and returns malformed_runner_response/exit 1. Native capture/private-layout compatibility remains separately evidenced.

**What supports that belief?** Lines 4262–4292 complete host reason mapping. Lines 4301–4310 state label scope/consequences. Lines 4312–4322 distinguish run/verify support. Line 4324 states same-object capture and private-layout evidence limits.

**What remains uncertain?** U18 is answered for host versus controller responsibilities. U52 remains open: no opaque-bytecode interpretation/replay guarantee is stated. U11 is partly answered with admission-level refusal distinct from later assessment findings. I revise any expectation that controller acceptance independently validates receipt payload integrity: its stated check only validates labels, after identity/capacity.

## 60. Public success follows admitted host outcome — lines 4334–4405

**What do I now believe?** Envelopes identify the emitting operation/build and preserve nested result ownership. For admitted run results, finished alone selects ok true/exit 0, even with failed attempts or controller integrity findings. Diagnostics are computed independently. Run payload retains structurally decoded reports even if a later label gate rejects them, while raw bytes may remain only in capture. Whether findings should change success is explicitly open.

**What supports that belief?** Lines 4336–4353 define envelopes. Lines 4361–4368 define result semantics. Lines 4377–4384 define run payload. Lines 4389–4405 state result selection and the open design question.

**What remains uncertain?** U11 is partly answered: assessment findings do not necessarily refuse the whole run or change exit. U39 is answered for controller outcome selection, though complete host classifier predicates remain only summarized. U53: success/finding coupling is an explicit open commitment; I cannot use exit 0 alone to assert evidence integrity. U15 remains for dossier structure.

## 61. Admission failure versus evidence finding — lines 4406–4478

**What do I now believe?** Controller classifications preserve distinct failed delivery/capture/frame/label boundaries and retained artifacts. Admission failures suppress execution diagnostics. After admission, diagnostics may report validly supported conflict, so a nonempty issues list does not necessarily mean integrity invalid. Actor diagnostics retain separate local assessments; reply-wide findings can withhold only the aggregate projection. no_worker means no subprocess account to assess.

**What supports that belief?** Lines 4411–4424 enumerate classifications. Lines 4429–4433 give admission order. Lines 4458–4465 define diagnostics and conflict/integrity distinctions. Lines 4470–4476 restate assessment preconditions.

**What remains uncertain?** U11 is partly answered for admission versus diagnostic findings. U13 remains for named termination-cause conditions. U54: response geometry limits and individual semantic check families are introduced but not yet enumerated. U39's host finished classification is still summarized rather than fully formalized in this portion.

## 62. Worker validation gates disposition projection — lines 4479–4550

**What do I now believe?** Geometry/profile-context refusal retains decoded reply but suppresses diagnostics and fails the operation. For admitted records, each worker lifecycle is validated before projecting ending, stop reason, attribution or copied conflicts, including degraded replies. Local lifecycle failure withholds that worker's disposition and clears stop reason. Actor diagnostics preserve input position/labels even if duplicate labels later trigger broader findings. Validated ending maps clean/nonzero/signal/conflict/unresolved separately.

**What supports that belief?** Line 4480 states context refusal. Lines 4485–4498 define per-worker computation order. Lines 4503–4508 define actor positional coverage. Lines 4521–4543 define validation prerequisite and ending mapping.

**What remains uncertain?** U11 is increasingly answered for local/global scopes. U13 remains for host-cleanup attribution, referenced before its rule. U54 remains for actual lifecycle check families/geometry. U46's claim validity is required here, but the complete validation predicates still are not all displayed.

## 63. Attribution requires a validated cleanup chain — lines 4551–4620

**What do I now believe?** Host-cleanup cause needs validated signaled ending, supported cleanup trigger, exhausted grace and successful native kill requesting that same signal. Otherwise cause stays unknown. Recognized trigger selects the specific host-cleanup name. Validated host conflicts copy independently of invalidity findings. Reply-wide failures retain host assertions/comparisons and actor projections while withholding aggregate disposition; even that can coexist with outer success. Native fresh/exec field consistency is a separate reply-wide check.

**What supports that belief?** Lines 4559–4573 define cleanup chain/attribution. Lines 4578–4583 define copied conflicts. Lines 4588–4604 define reply-wide findings and result independence. Lines 4613–4620 enumerate check families.

**What remains uncertain?** U13 is answered for termination attribution. U43 is answered at the enforcement-family level: fresh field applicability/native relationships are checked, though all predicates are not printed here. U11 is largely answered for local/global consequences. U54 remains for remaining families and numeric geometry bounds. U24's aggregate exec consistency is assigned to native-operation checking but not fully enumerated.

## 64. Open answers and independently checked readers — lines 4621–4690

**What do I now believe?** Degradation-form validation and worker lifecycle validity are independent judgments. Unknown closed claim states invalidate projection; unfamiliar supported answers/summaries can survive with limited or unrecognized meaning. unresolved and inapplicable final states both project unconfirmed, with originals retained. A constructed cross-reader corpus checks scope-specific judgments, but does not establish native occurrence of every case. Semantic classifiers remain independently written.

**What supports that belief?** Lines 4621–4627 define degraded applicability. Lines 4632–4648 distinguish closed states/open answers and merged vocabulary. Lines 4653–4660 give scope example. Lines 4670–4686 define reader judgments and independent-classifier design question.

**What remains uncertain?** U11 is answered for ordinary/degraded/local/global applicability. U46 is answered for claim-state and summary handling. U54 remains for concrete geometry limits. The merged-unconfirmed vocabulary and whether classifiers should be generated are explicitly open maintainer decisions; neither prevents reading their current behavior. U43/U24 detailed native predicates remain referenced rather than fully reproduced here.

## 65. Actor-local diagnostics mirror validated worker rules — lines 4691–4760

**What do I now believe?** Each actor's diagnostic row maps only its own subprocess after local lifecycle validation. Missing subprocess yields no_worker/null integrity; local failures withhold that actor's projection. Validated ending and recognized stop rules mirror ordinary workers while preserving actor position. Actor host-cleanup attribution requires the same owned signal/exhausted grace/successful matching request chain.

**What supports that belief?** Lines 4696–4701 define actor diagnostic fields. Lines 4706–4724 establish scope and local failure. Lines 4730–4749 define ending/stop projection. Lines 4754–4758 define cleanup-chain prerequisites.

**What remains uncertain?** No new uncertainty arises; these explicit actor rules confirm the previously inferred parallel with ordinary projection. U54 remains for geometry limits. U15 remains for dossier content. U28 remains for manual cleanup recovery details beyond the ownership requirement.

## 66. Findings identify retained assertions — lines 4761–4834

**What do I now believe?** Actor cleanup causes and validated conflicts mirror ordinary projection. Findings are open categories with details; only selected owned-reap/activation/gate findings carry positional subject paths. A subject identifies the inspected assertion even with duplicate labels or null, while scope controls withholding. Whether reply-wide findings should also withhold actor conclusions is open. Dossier hashes and binary observations describe controller-held/pre-invocation artifacts, not native execution by themselves.

**What supports that belief?** Lines 4762–4783 finish actor attribution/conflict copy. Lines 4793–4799 define findings. Lines 4804–4818 define association/scope and the design gap. Lines 4830–4832 introduce dossier ownership and limits.

**What remains uncertain?** U15 is beginning to resolve through dossier scope. U11 is fully answered for finding association and withholding, with broader withholding explicitly open. U54's geometry values remain unknown. U55: I do not yet know how binary dossier baselines are chosen, especially for built-in versus external runners.

## 67. Dossier observes held source and selected files — lines 4835–4905

**What do I now believe?** Held-source hashes ignore JSON formatting and later file edits. Controller import scanning hashes its own bounded regular-file reads, even when incomplete. Shipped manifest-described binaries produce null dossier rows without rehash; other selected files are hashed against unique role baselines. Dossier mismatch/failure does not alone block invocation. Ordinary file hashes do not establish executing-image association. Actor dossiers precede mode admission and can retain malformed labels as null.

**What supports that belief?** Lines 4839–4843 define held input. Lines 4848–4852 define scanner/hash. Lines 4857–4861 define binary comparison and optional evidence verification. Lines 4870–4872 state process-association limits. Lines 4881–4904 define dossier structure.

**What remains uncertain?** U15 is partly answered for top-level dossier, with augmentation/import details ahead. U55 is answered for baseline selection and null shipped rows. U07 is now limited explicitly: actor live association exists, ordinary dossier hashes only observe files. U03 still needs app provenance/configuration fields. U54's exact response geometry remains unenumerated.

## 68. Dossier completeness is scanner-specific — lines 4906–4978

**What do I now believe?** Augmentation records preserve only source hashes that existed; failed/not-applicable states have no selected hash. A complete or incomplete import scan retains a closure digest, while failed/skipped scans do not. No cycle/bound/error is necessary but not sufficient for complete because nonliteral forms also matter. Import size/mtime are descriptor metadata; the hash identifies bytes read. Host context uses nullable sysctl observations.

**What supports that belief?** Lines 4912–4926 define augmentation relations. Lines 4934–4947 define scan states and limits. Lines 4957–4962 define import read fields. Lines 4971–4974 define host context.

**What remains uncertain?** U15 is answered for augmentation/import dossiers. U21 remains limited regarding native compiler parity, already explicitly unestablished for collisions/macros/changing files. U03 awaits app provenance. U54 remains for response geometry. I cannot reconstruct a complete scanner decision solely from absence of the listed error fields because nonliteral forms lack a dedicated Boolean.

## 69. App and selected runner provenance — lines 4979–5050

**What do I now believe?** App provenance records manifest location and optional explicitly enabled hash verification. Binary rows distinguish equal/different available digests from unavailable operands; actual hash can survive missing baseline. Null shipped-role rows remain outside this comparison. Runner provenance identifies intended service/bundle/path and recorded role signature/entitlement metadata, all before execution.

**What supports that belief?** Lines 4984–4985 define app provenance. Lines 4992–4999 define role records. Lines 5008–5027 define digest classification and process limit. Lines 5038–5050 define selected-runner fields.

**What remains uncertain?** U55 is fully answered for dossier binary/role comparisons. U03 remains partly open: this app provenance does not itself enumerate compiler/SDK/build configuration. U16 remains for external registry installation, selection and verification semantics. U54 remains for response geometry bounds. I continue to distinguish historical read-back metadata from live association.

## 70. Registry installation and verification are distinct observations — lines 5051–5124

**What do I now believe?** Manifest verification counts only entries with declared hashes. External runners use schema-1 registry and launchd with separate registry/file/live/verification facts. Mutations lock and losslessly round-trip metadata before atomic replacement; unknown metadata gives no ownership. Installation validates bundle identities/seal/equipment, optionally signs, then saves pending ownership before plist/bootstrap, retaining pending on failure. Verify runs a fresh fixed apply-only allow-default specimen; its success proves no probe operation.

**What supports that belief?** Lines 5057–5078 define verification. Lines 5083–5101 define registry lookup and mutation. Lines 5106–5117 define install/pending ordering. Lines 5122–5124 define verification request and scope.

**What remains uncertain?** U16 is partly answered for registry/install/verify, but run-time selection and cleanup ownership checks remain ahead. U56: removal/reconciliation and recovery retirement rules are not yet detailed. U03 build configuration/SDK provenance still appears delegated outside the displayed public records. U54's geometry limits remain unknown.

## 71. Durable cleanup requires independent absence — lines 5125–5198

**What do I now believe?** Pending installs cannot run ordinary specimens but can be explicitly verified without registry mutation. Validate may succeed as a command despite missing/invalid runners. Reconcile observes without modifying. Remove first durably transfers ownership into pending_cleanup, separately checks service/plist ownership, rechecks before unlink and retires only after both absences, no warnings and successful save. Successful calls alone do not establish absence; remove may exit 0 while retaining cleanup. Label prefixes identify candidates only.

**What supports that belief?** Lines 5132–5147 define pending verification/validate. Lines 5154–5158 define reconcile. Lines 5163–5175 define removal and ownership. Lines 5184–5192 define recovery and legacy preservation.

**What remains uncertain?** U56 is answered for recovery behavior and ownership gates. U16 is answered for Pending selection and verification; exact service-observation parsing remains ahead. U28's manual shared-memory recovery is distinct and still lacks a procedure. U57: I do not yet know how launchctl output yields a unique executable or unknown/absent classification.

## 72. Registry records preserve historical observations — lines 5199–5270

**What do I now believe?** Registry active rows can be pending or installed; historical missing state defaults installed, while missing contract cannot satisfy current exact admission. Role signature/entitlement and source/post-sign inventory snapshots describe past reads. Cleanup ownership binds exact plist bytes/path/domain/UID and must be combined with current observations. Signature validity is scoped to its read/verification path; during validate host validity also needs recursive bundle verification.

**What supports that belief?** Lines 5199–5201 define registry collections. Lines 5209–5234 define runner/history fields. Lines 5242–5249 define ownership. Lines 5257–5265 define signature scope.

**What remains uncertain?** U57 remains for service-presence/executable observations. U16 is largely answered for registry identities, while exact ordinary selector acceptance beyond Pending/contract remains not fully expanded here. U03 still lacks SDK/compiler/configuration record definitions. No additional interpretation is assigned to historical issuer fields beyond retained metadata.

## 73. Entitlement and cleanup output fields — lines 5271–5344

**What do I now believe?** Entitlement granted lists include only Boolean true, while keys lists include every parsed key; empty lists with error mean unavailable parsing. Cleanup transactions preserve historical opaque observations/nesting. Removal reports call success separately from retained recovery, and warnings imply retention. Cleanup completion also depends on successful publication of retirement. Install state copies the saved record, while loaded and bootstrapped remain independent observations.

**What supports that belief?** Lines 5271–5278 define entitlement semantics. Lines 5286–5292 define durable cleanup shape. Lines 5301–5317 define removal/retention. Lines 5327–5338 define installation result/state.

**What remains uncertain?** U56 is fully answered for output and retirement conditions. U57 remains for loaded/service observation parsing. U16's entitlement-readback demands are now clear for registry metadata as well as actors. U28 still lacks a manual shared-memory ownership-recovery procedure, which is a distinct resource type.

## 74. Verification result selection and validation counts — lines 5345–5417

**What do I now believe?** Verify completion exposes selected registry state and separate capture/decoded/admitted PID facts. Delivery failure keeps retained records but clears PID and selects tool_error/exit 2. Otherwise selected finished yields success; other outcomes fail. Validation counts visited, missing and otherwise-invalid rows separately, allowing multiple per-row failures. An unmatched supplied ID wins over service-name lookup.

**What supports that belief?** Lines 5345–5355 define verification data. Lines 5360–5364 give delivery precedence. Lines 5373–5377 give outcome mapping. Lines 5388–5403 define validation rows/failures. Lines 5412–5413 define unmatched lookup.

**What remains uncertain?** U16 is answered for verify lookup/result selection. U57 remains for service observation, introduced next. U54 remains for geometry values. No new uncertainty arises from these result schemas.

## 75. Presence and ownership remain independent — lines 5418–5490

**What do I now believe?** Service presence is present only after successful launchctl print, absent only for a specific diagnostic naming the requested service, otherwise unknown. A unique program line supplies executable; matching recorded path permits owned classification after location checks. Absent service has ambiguous ownership, which does not negate observed absence. Plist metadata/content/hash/error remain separate. Reconcile command success can coexist with unknown inspections and partial location-error objects.

**What supports that belief?** Lines 5422–5424 define service reads. Lines 5434–5445 define ownership classification. Lines 5456–5461 define plist observations. Lines 5469–5490 define reconciliation data and partial records.

**What remains uncertain?** U57 is answered at the documented parser/classification level. U56 is reinforced for absence versus authority. U54 remains for response geometry; U04 still awaits formal support-grade definitions. U03 remains for build settings/SDK records outside the public provenance fields shown so far.

## 76. Candidate and cleanup observation shapes — lines 5491–5564

**What do I now believe?** Unregistered candidates never gain owned classification from discovery; missing config/identity yields unknown/ambiguous. Cleanup histories retain current before/after service/plist observations, with ownership used before actions and nominal teardown polling receipt afterward. waited_ms sums requested intervals rather than measured wall time. Dynamic output shapes have source review, while an independent mutation control for every branch remains open. Version data starts with the same public identity as build.contract.

**What supports that belief?** Lines 5500–5508 define candidates. Lines 5517–5519 define inspection errors. Lines 5527–5547 define cleanup observations/waits. Line 5549 states the dynamic-branch evidence limit. Lines 5558–5560 define version identity.

**What remains uncertain?** U04 still awaits support-grade definitions. U54 geometry limits remain not displayed. U58: independent dynamic output mutation coverage is explicitly incomplete; I cannot treat source field agreement as execution evidence for every reconciliation branch. U03 build compiler/SDK detail remains outside shown version/provenance fields.

## 77. Support grades finally defined — lines 5565–5636

**What do I now believe?** Version dispatch uses the first argument, ignores remaining arguments, does not invoke a runner and reports compiled context; rendering failure changes exit. Support grades distinguish source inspection, source-plus-check inspection and named executed assertions tied to source/build. This confirms my provisional interpretation of check read. The rule-applicability table indexes acting components and does not add execution credit.

**What supports that belief?** Lines 5565–5578 define version behavior. Line 5583 defines all three grades. Lines 5587–5636 begin the rule/component index.

**What remains uncertain?** U04 is answered at line 5583. U54's response geometry limits are still not enumerated beyond wire/storage/request limits already read. U03, U05, U06 and U45 remain partly dependent on referenced build/schema/protocol sources. I will not follow those links under these reading conditions.

## 78. Rule index confirms boundary ownership — lines 5637–5700

**What do I now believe?** The index consistently assigns transport invocation to client, execution/collection/custody assembly to host/worker, and received-record interpretation to controller or retained-byte reader. It restates owners for lifecycle and profile checks already read. I do not infer new guarantees from the index links themselves.

**What supports that belief?** Lines 5637–5665 list transport, wire, step and lifecycle rule owners. Lines 5666–5680 list actor/equipment/profile owners. Lines 5681–5700 list controller projection and dossier owners.

**What remains uncertain?** The remaining questions are unchanged: exact referenced build/schema/protocol details, numeric response geometry, native evidence limits and the explicit maintainer decisions. This index has not answered them, and I have not followed its links backward or outward.

## 79. Closing indexes and explicit gaps — lines 5701–5747

**What do I now believe?** The closing tables collect rule owners, controller finding operands/consequences and seven named behavior gaps. They reinforce that admission, local lifecycle withholding, reply-wide withholding and cleanup ownership have different effects. The document ends without supplying every referenced implementation layout or every detailed validator predicate.

**What supports that belief?** Lines 5701–5717 complete the rule-owner index. Lines 5721–5735 collect controller checks. Lines 5739–5746 list ordinary-build history, degraded associations, cancellation reach, success/findings, unconfirmed vocabulary, independent classifiers and withholding scope; line 5747 closes the generated contract.

**What remains uncertain?** U03, U05, U06, U19, U21, U24, U28, U30, U31, U37, U39, U42, U43, U44, U45, U50, U52, U53, U54 and U58 have at least a residual limitation or question to classify in the close-out. The current behavior of the seven listed design gaps is stated; future maintainer choices remain open. No later passage follows to answer these residuals.

# Close-out

## 1. Reading conditions

I opened TASK.md first with `cat`, then read CONTRACT.md as raw Markdown using consecutive `sed -n` line ranges from 1 through 5747. I saw HTML anchors, generated markers, tables, literal predicates, code blocks and support citations as raw text. I did not use a rendered view, follow a link, open a cited source/check, search for project material, browse the web, inspect the repository or inspect a parent directory.

The contract was read in one forward pass. Before opening the next range, I appended the preceding numbered entry to JOURNAL.md. There are 79 entries. I never edited an earlier entry. My only file besides CONTRACT.md opened for input was TASK.md; I created JOURNAL.md and, after reaching the contract's end, read its headings and uncertainty paragraphs to prepare this close-out. I will read these same permitted files for byte hashing and journal coverage checks after writing the close-out. All shell commands used `/private/tmp/pw-contract-stage-three-isolated-reading-20261111` as their explicit working directory. No tools searched other files or opened external resources.

The assigned session already included repository-location/AGENTS orientation text in its inherited context. I did not open its referenced files or use that material as contract evidence. My beliefs above are based on the sequential contract passages. Ordinary technical meanings of names such as JSON, SHA-256, PID and UTF-8 were part of the technically competent reader stance, not additional project documents.

There is a method limitation: portions were line-bounded groups of related subsections or tables, 47–90 lines long, rather than uniformly one paragraph or a few paragraphs. Some ranges ended at a heading, midway through a table, or midway through a sentence. I recorded those unfinished questions and continued only after journaling. This preserves forward reading and append-before-next-read, but the portion size and boundary choice were not strictly paragraph-sized throughout. There were no file-access or link-following isolation violations. I did not render editorial judgments or suggestions.

## 2. Uncertainties

The status below applies to each numbered uncertainty's distinct parts. “Deferred” identifies a named source document cited by the contract that I did not open; it does not claim that I verified what that source would answer. Some broad questions divide into answered contract meaning and a residual implementation or native-evidence question.

| Item | End status and consequence |
| --- | --- |
| U01 — Specimen schema and report/assessment kinds | **Answered:** top-level input at 518–560; probe/actor/extension forms at 831–1184; host record at 2345–2374; controller result/diagnostics at 4334–4476. |
| U02 — Component roles and relationships | **Answered:** definitions at 305–376, followed by authorization/admission at 1309–1357 and 1540–1552. Each component's observation boundary is distinct. |
| U03 — Build context, signing, configuration and SDK | **Answered in part:** build/producer fields at 223–252; static/live signing evidence at 3825–3972; manifest verification at 5051–5078. **Open:** the full compiler/SDK/build-configuration evidence record and its checks are not specified here. I could identify the reported source identity and named signing observations, but could not reconstruct the exact build environment from this contract alone. |
| U04 — Support grades | **Answered:** 5581–5584 define source read, check read and executed. Earlier entry 77's pinpoint to 5583 refers to the nearby anchor; the definition is in this range. Inspection is not execution. |
| U05 — Surface table and canonical shapes | **Answered in part:** surface list at 255–277 and wire fingerprint inputs at 1641–1643. **Deferred:** `docs/contract/runtime.py` and `docs/generate_porcelain.py` are named source documents for history/shape derivation; the complete canonical record/tag inventory is not reproduced. I could read the public fields but could not independently derive every stamp or encode every record ID/tag. |
| U06 — Binary frame and worker shared-header layout/lifecycle | **Answered in part:** binary frame grammar at 1597–1648; worker publication/lifecycle account at 2845–3250. **Deferred:** `controller/tools/pw_probe_runner/pw_probe_runner_abi.h` and `runner/Sources/PWRunnerCore/CWorker.swift` for the complete native layout. I could interpret public observations but could not implement a byte-compatible shared-memory worker from this text alone. |
| U07 — Executing binary association | **Answered:** actor inventory/static binding at 3804–3897 and owned live inspection at 3951–3972. Ordinary selected-file hashes explicitly remain file observations, 4870–4872 and 5008–5027. I would not promote an ordinary dossier hash to live-image association. |
| U08 — Generator output list | **Answered:** continuation at line 300 completes public document, snapshot and surface stamps. |
| U09 — Reservation, phase barriers, scheduling and overrides | **Answered:** overrides 640–674; phase order 1036–1045; reservation 1322–1357; full query-order chain 2672–2697; schedule/gates 3684–3748. |
| U10 — Raw evidence after rejected capture/reply | **Answered:** retained host prefix 1475–1492; admission precedence and rejected stdout projection 1524–1584; rich/minimal reporting 2422–2445. |
| U11 — Checks, assessment withholding and retention | **Answered:** profile admission refusal 4301–4310; local/global diagnostics 4485–4627; state vocabulary 4632–4648; finding association 4793–4818. The open policy choice about broader withholding is listed below, distinct from current behavior. |
| U12 — Native attempt success/effect and fresh aggregates | **Answered:** operation table 921–932; attempt result 2512–2529; fresh detail 2607–2648; first-failure projections 2792–2829. A legacy open result is not a transfer result, and fresh details retain individual boundaries. |
| U13 — Owned lifecycle, reach/publication and cause | **Answered:** owned status 2845–2895; terminal reach/publication 3090–3102; canonical/owned-reap records 3137–3250; attribution chain 4559–4573. These rules support the stated lifecycle conclusions, not sandbox-cause attribution from permission errors. |
| U14 — Capacities, nested input, selectors and refusal effects | **Answered:** 562–570, 596–633, 640–704, 831–1184, 2181–2234 and 2265–2284 collectively supply the encountered bounds/forms/refusal consequences. |
| U15 — Augments and original/selected dossier | **Answered:** fragment resolution and exec baseline 738–774; held-input/scanner boundaries 4839–4872; dossier fields 4881–4962. |
| U16 — External selection and entitlement demands | **Answered at the public operation level:** selector precedence/defaults 596–633; Boolean-true demands 3933–3943 and 5271–5278; registry lookup/install 5083–5117; Pending/verify 5132–5147; verification data/result 5345–5377. Signature and registry reads remain temporally scoped. |
| U17 — Connection authorization and overrides | **Answered:** caller Team ID/identifier rules 1309–1313; packaged checks before fixture overrides 3879–3897; static/live association 3951–3972. |
| U18 — Compiled-profile receipt meaning and validation | **Answered:** host capture/input/nonce checks 4189–4292; controller label-only check and consequences 4301–4324. Host assertions and controller validation have different scopes. |
| U19 — Native parameter/compiler semantics | **Answered in part:** sorted parameter setup 701–704 and helper/worker classifications 717–731. **Open:** arbitrary native SBPL expression/parameter semantics and behavior across platforms are not specified. I could construct admitted input, but could not predict every native compile verdict without its observation. |
| U20 — Helper admission/output/fallback | **Answered:** standalone decode 782–791; admission 797–818; data/verdict 1858–1885; fallback 1977–1995. |
| U21 — Imports and native compilation agreement | **Answered in part:** literal walk/search/hash/bounds 1927–1950 and 4848–4852. **Open:** native collision precedence, macro-generated dependencies and equality across changing independent reads are explicitly limited at 1943–1950. I could interpret a scanner closure, but not assert that it identifies every worker compiler input. |
| U22 — Prediction exclusions and realpath | **Answered:** exact exclusions 876–900; unavailable-path creation example 2299–2301; path forms/time/operands 2567–2587 and 2769–2784. |
| U23 — Query association and ordering eligibility | **Answered:** exact native answer and unique identity requirements 2672–2697; collector join/retention 3311–3349. |
| U24 — Exec child collection/cleanup/clock and aggregate consistency | **Answered in part:** setup/budgets 943–946; collection/group request/leader reap 3393–3479; controller check family 4613–4620. **Deferred:** `controller/tools/pw_probe_runner/pw_worker_exec.h`, `runner/Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift` and `controller/src/porcelain_native.rs` for the complete aggregate/consistency predicates. I could distinguish reported boundaries, but could not independently recreate every malformed-exec judgment. |
| U25 — Extension operations and participant restriction | **Answered:** grammar/resource ownership 1123–1184; participant exec exclusion 1201–1208. |
| U26 — Termination dependency | **Answered:** declaration/order 1053–1075; timing, natural owned ending, failure and cancellation 3700–3748; carried-gate checking 3754–3762. |
| U27 — Token/delivery/handle capacity, custody and status | **Answered:** resource/payload bounds and custody 1191–1251; event/transfer/resource statuses 2007–2149. Reusable references do not imply successful native production; release and later access remain separate. |
| U28 — Safe teardown and cleanup recovery | **Answered in part:** shared erasure only for established actor termination at 1244–1246; collection basis 2845–2864; ownership/cleanup cells 4083–4162. **Open:** a concrete procedure for establishing current ownership of an unresolved shared-memory name, and any blanket claim that leader reap proves every descendant gone. I could retain/review recovery evidence, but could not safely automate arbitrary name cleanup or claim full descendant absence from the leader record alone. |
| U29 — Reservation and invocation knowledge | **Answered:** once-only slot/invocation/deadline 1322–1357; capture/attempt/submission fields 1399–1466; admission 1540–1552. Actual receipt after transport loss remains a deliberately unresolved fact for a particular run. |
| U30 — Native cap interval | **Open:** 1361–1363 and 1653–1660 leave native XPC behavior between host-retention and frame limits unobserved. I could apply documented structural/retention refusals, but could not claim a native transport outcome across that interval. |
| U31 — Capture consistency validation | **Answered in part:** 1540–1552 name chronology, UUID, terminal/control and retained-length checks. **Deferred:** `controller/src/runner_client.rs` (`validate_capture`) and `runner/Clients/PWRunnerClient/PWRunnerClientSession.swift` for all predicates. I could identify the checked families but could not reproduce every cross-field admission decision. |
| U32 — Request stdin delivery and precedence | **Answered:** 1540–1552 and 1561–1562. Pipe write acceptance is distinct from receipt; writer error wins. |
| U33 — Porcelain | **Answered:** 1597–1648 define the typed binary frame and public projection. |
| U34 — Reporting fallback | **Answered:** 2411–2445 define rich, minimal and empty outcomes and retention. |
| U35 — Validator collector bounds and rejected context | **Answered:** 1684–1686, 3283–3306 and 3357–3368. |
| U36 — Native helper stages and inventory bounds | **Answered:** 1906–1918 and 1927–1934. |
| U37 — Invalid extension/association consequences | **Answered in part:** event/resource invalid/unresolved forms 2007–2149; ordinary check/finding scope 4588–4627. **Open:** whether degraded reports must still establish ordinary actor/phase/resource associations, explicitly left undecided at 2441–2445. I could retain such records but could not treat their associations as ordinarily validated. |
| U38 — Safe metadata and post-invocation reporting failure | **Answered:** 2265–2284 and 2411–2445. |
| U39 — Full host outcome classifier and finished prerequisites | **Answered in part:** worker-before-validator precedence and outcome meanings 2379–2403; controller exact-finished success 4389–4405. **Deferred:** `runner/Sources/PWRunnerCore/CWorkerDisposition.swift` and `runner/Sources/PWRunnerCore/ActorOrchestration.swift` for every host classification branch. I could interpret a reported outcome's stated scope but could not independently recalculate every aggregate from arbitrary raw evidence. |
| U40 — Path diagnostics versus comparison operands | **Answered:** 2538–2543, 2567–2587, 2728–2748 and 2769–2784. |
| U41 — Permission-shaped classification and cause | **Answered:** 2706–2723 explicitly give precedence and limit attribution; host cleanup has its own independent chain at 4559–4573. |
| U42 — mach_lookup/bootstrap_look_up versus mach/lookup | **Open:** the operation-relation table at 2728–2735 uses a different spelling from the admitted request family/action at 910–930 without explicitly reconciling that name. I assumed the table refers to the same lookup operation, but could not use that spelling alone as a new admitted request pair. |
| U43 — Required reached fresh-operation fields | **Answered in part:** native-operation checks at 4613–4620 promise applicable-field/native-relationship checking. **Deferred:** `controller/src/porcelain_native.rs` and `runner/Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift` for the complete predicates. I could not build an independent complete malformed-fresh-record validator from the aggregate fall-through tables alone. |
| U44 — Clock-domain relationships | **Answered in part:** continuous time includes sleep for client/exec at 943–946 and 1349–1353; host waits explicitly use CLOCK_MONOTONIC at 2926–2935; separate setup/inspection/worker deadlines are stated at 3970–3972. **Open:** no general cross-domain conversion or common elapsed-time bound is given. I could interpret each named clock locally, but could not merge all reported times into a single timeout guarantee. |
| U45 — Native publication/progress code map | **Answered in part:** packed progress and open values 3015–3037; diagnostic guards 3057–3064; selected application codes 3611–3619. **Deferred:** `controller/tools/pw_probe_runner/pw_probe_runner_abi.h`, `runner/Sources/PWRunnerCore/CWorker.swift` and `runner/Sources/PWRunnerCore/CWorkerDisposition.swift` for the full map/guards. I could retain unfamiliar numbers but could not assign every number a lifecycle meaning. |
| U46 — Canonical claim states, conflicts and summaries | **Answered:** 3090–3102, 3137–3250 and 4632–4648 supply states, D1/D5 meaning, projection and open-summary behavior. **Deferred for exact implementation of every summary combination:** `runner/Sources/PWRunnerCore/PWRunnerDisposition.swift`, named in the lifecycle support. I could apply the described cases but not claim an exhaustive independent truth table. |
| U47 — Application failure, late success and setup timeout | **Answered:** precedence 3579–3619 and late-publication distinction 3624–3626. |
| U48 — Inventory to signed file to live process | **Answered:** 3825–3897 and 3951–3972. |
| U49 — Authority setup acquisition/integrity | **Answered:** 4057–4115 and 4124–4146. |
| U50 — Spontaneous native Security failures | **Open:** the explicit observation limit at 3982–3984 remains. I could interpret injected failure branches and normal matched observations but could not claim native occurrence/frequency or a complete integrated failure matrix. |
| U51 — Authority operation slots and cleanup reference | **Answered:** 4124–4162. Manual recovery procedure remains the separate open part of U28. |
| U52 — Bytecode interpretation/replay | **Open:** 4189–4324 define capture/identity and acknowledge private-layout compatibility limits, but supply no general decoding or replay commitment. I could preserve/hash the bytes, not promise portable interpretation or reuse. |
| U53 — Success and findings | **Open as a design decision:** 4401–4405. Current behavior is answered: admitted finished controls ok/exit independently of findings. I could not use exit 0 as an integrity verdict or predict a future changed policy. |
| U54 — Response geometry and semantic families | **Answered in part:** wire/storage limits 1638 and check families 4613–4627. **Deferred:** `controller/src/porcelain_admission.rs` for the complete response-context geometry guard. I could apply displayed bounds, but could not enumerate every collection limit from this document alone. |
| U55 — Selected-file baseline and built-in/external distinction | **Answered:** 4857–4861 and 4992–5027; manifest verification scope 5057–5078. |
| U56 — Removal/reconcile/recovery retirement | **Answered:** 5154–5192 and 5286–5338, with current observation shapes at 5527–5547. |
| U57 — launchctl service observation | **Answered:** 5422–5445 state presence, unique program-line extraction and ownership consequences. |
| U58 — Dynamic output mutation coverage | **Open evidence limit:** 5549 expressly leaves an independent mutation control for every dynamic branch open. I could use the stated source-derived shapes but could not claim every branch was independently executed or mutation-tested. |

The following distinct maintainer decisions were encountered without separate U numbers or overlap the numbered questions. Their current behavior is stated, and the prospective decision remains **open**:

- Ordinary-build release-history requirement (142–147; listed 5740): ordinary source-copy checks are accepted; I cannot demand full history of every build under this contract.
- Reporting-failure associations (2441–2445; U37): retained degraded associations are not ordinarily certified.
- Termination cancellation reach (3774–3776): failed evaluated gates cancel all later phases; I cannot assume narrower future cancellation.
- Success and findings (4401–4405; U53): findings do not currently change exact-finished success.
- Merged unconfirmed vocabulary (4645–4648): unresolved and inapplicable remain distinct only in the host claim; I cannot recover that distinction from the controller label alone.
- Independent semantic classifiers (4683–4686): implementations remain independently written; I cannot assume a single generated classifier or prove all-reader equivalence beyond the described controls.
- Reply-wide withholding scope (4814–4818): actor-local conclusions remain beside aggregate withholding; I cannot assume the aggregate finding also withdraws them.

Two carried limits did not become extra numbered questions: listed duplicate-member observations cannot be generalized to unlisted inputs/platforms (582–586, 1689–1695), and an import scan's necessary visible fields do not independently reconstruct its nonliteral-form decision (4943–4947). Both remain **open beyond the stated scope**; neither prevents reading the documented cases, but each prevents an exhaustive generalization.

## 3. Carried terms

This records terms I had to carry forward before their operational meaning arrived, plus names that remained only references. A range indicates where I first encountered the relevant meaning, not an external lookup. I treated locally labeled Source/Check/Run/Build filenames, symbols and hash strings as evidence locators, not as descriptions whose contents I knew. I did not open them. Record type labels such as `rust.BuildStamp` and `PWRunnerRunResult` identify the accompanying record; I did not need a separate language implementation definition to keep reading their field tables.

| Carried term/name/reference | First encounter; explanation or end status; meaning assumed while continuing |
| --- | --- |
| PolicyWitness / PW | 2–10; component composition 287–289. I initially assumed the tool performing the declared experiment. |
| specimen / saved specimen | 7, 18–20; definitions 351–353, schema 518–560. I carried “declared experiment/input” until the JSON forms arrived. |
| controller / compiler helper | 19–20; roles 305–307 and 342–346. I assumed request/front-end and separate compilation components. |
| host / worker / runner client | 20–23; responsibilities 312–330. I initially carried separate producers without assuming they shared sandbox state. |
| client capture / host reply / envelope | 20–23; definitions 365–384; fields 1399–1414 and 2345–2374. I assumed nested boundary records, not interchangeable results. |
| build.contract / producer.contract / PWContract | 18–24; build/producer fields 223–252. I treated them as locations carrying exact public identity. PWContract remained a property-list key, not a distinct identity. |
| equipment association | 25; static/live rules 3804–3972. I assumed a relation between selected artifacts and running workers, withholding proof until those rules. |
| build pipeline / contract generator | linked at 69 and 123; definitions 294–300. I assumed the named actors producing identity and generated documents. |
| support grades: check read, source read, executed | first support at 76, source read at 154, executed in extension examples 1287–1291; formal definitions 5581–5584. I provisionally treated read as inspection and executed as a named run, later confirmed. |
| unbound / test:policy-witness | 83–87; explained locally and identity gates at 90–99. I carried the literal sentinel/test values, not release identities. |
| surface / stamp / canonical shape | 107–117; surface table 255–277; wire representation 1597–1643. I assumed authored/shape input history. Complete shape inventory remains deferred under U05. |
| reasserting a specimen | 116–117; review obligation 151–154. I assumed an explicit caller choice to target another exact contract. |
| typed response frame / wire-schema fingerprint | 161–168; grammar 1597–1648. I assumed structured binary transport whose schema match precedes producer identity. |
| worker protocol identity / bootstrap magic / shared header | 173–187; publication account 2996–3037, but complete native layout/magic constant not reproduced. I assumed a fixed early compatibility gate, not live binary proof. |
| worker_evidence / abi_identity | 185–187; fields 2996–3007. I assumed acquired worker-region evidence; later learned reported identity is host-selected after matching. |
| CodeDirectory hash / cdhash | 205–215; static/live signature association 3825–3972. I assumed an Apple code-signing identifier; the contract defines widths and uses, not the CodeDirectory format itself. |
| XPC / NSXPCListener / Mach service | component composition and client role 287–315; authorization 1309–1313 and installation 5083–5117. I used ordinary macOS IPC/service meanings; the operating-system protocols themselves are not taught here. |
| native sandbox / SBPL / sandbox_compile_string / sandbox_apply / sandbox_set_param | policy/native component descriptions 327–346 and 690–731; operations are stated, but the SBPL language/native private APIs are not fully specified. I assumed native compiler/application calls, not guaranteed policy semantics. |
| query validator / sandbox_check | 287–289 and 335–338; line protocol/native outcomes 1669–1719. I assumed a prediction query on a selected worker, distinct from attempt enforcement. |
| SANDBOX_CHECK_NO_REPORT | source references before its prose use at 1669–1679; used in direct/batch calls through 1719. I treated it as the named native call flag. Its complete OS implementation is not explained. |
| actor / phase / probe / prediction / query_first | introduced 327–338; definitions 389–415; schemas 831–1110 and ordering 2672–2697. I carried roles, batches, paired operands and an interval claim, not per-action state immutability. |
| owned process / owned reap / natural reap | actor/PID definition 389–391 and dependency 1061; owned ending 3241–3250, natural gate 3724–3748. I assumed child ownership is stronger than numeric PID; natural later meant no host departure request, including a signal ending. |
| dossier | 307 and 541; full account 4830–5078. I assumed controller input/provenance observations, later distinguished each read/hash boundary. |
| augment / exec_baseline | 518 and 694; resolution/rules 738–774. I assumed packaged source additions; later saw unconditional file-read authority. |
| selected / unentitled equipment | override map 647 and actor fields 976–978; inventory 3825–3847. I treated these as worker roles; “unentitled” later means an empty inventory entitlement dictionary, not absence of inherited restrictions. |
| capture_compiled_profile / capture_nonce / compiled-profile receipt | 692–694; receipt 4168–4324. I assumed opt-in capture associated by nonce; host availability and controller label-only limits arrived much later. |
| after_termination | 552 and phase field 1025; declaration 1053–1075, runtime 3700–3762. I assumed dependency, without assuming completion or forced termination. |
| extension / token / delivery / handle / custody | actor-form allowance at 526 and override/null references; grammar 1123–1184, custody 1214–1251, resource records 2089–2149. I assumed native authority resources with explicit ownership, not success from declaration. |
| reservation / lease / granting connection / credential | client role 312–315; operational rules 1322–1357 and fields 1373–1466. I initially assumed a host-use allocation; later learned expiry retires the slot and execution never replays. |
| porcelain | rejected stdout format 1583; grammar 1597–1648. I carried the project's binary-encoding name until primitives appeared. |
| rich fallback / minimal fallback / degradation | writer support 1653–1660; full rule 2411–2445. I assumed fallback reports with different retained evidence; later learned rich form can preserve association inconsistencies. |
| same_as_input / firmlink / parent path form | JSON projection 1648 and path tables 2567–2587; fuller explanation 2769–2784. I assumed exact-byte omission and separate host path transformations; no runtime-object identity was implied. |
| ordinary semantic reply | ordinary/degraded references around 2074 and 2441; clarified 3519–3551 and explicitly defined 4610–4627. I eventually distinguished this from ordinary single-worker request form: it includes actors when reporting_failure is absent. |
| D1 / D5 / canonical disposition | worker compatibility predicates 2870–2895, then 3090–3102; claim/conflict definitions 3137–3174. I carried conflict codes until they were explained as status and progress/publication contradictions. |
| CLOCK_MONOTONIC / mach_continuous_time / continuous-clock cutoff | exec timing 946, client deadline 1349–1353, host waits 2926–2935; separate origins 3970–3972. I retained separate clock domains; no cross-domain conversion was assumed. |
| authority operation cell / primary operation / not_observed | setup/custody references 1219 and application 3589–3605; scope/cells 4057–4162. I assumed independently acquired native setup records, later learned decision-first acquisition and fixed slots. |
| OSStatus / Security call names | inventory seal field 3816 and live fields 3951–3965; diagnostic/native rows 3919–3926 and 4003–4009. I used native return-domain meaning; no universal error-code interpretation beyond the named operation. |
| process_disposition / disposition_integrity / subject_path | diagnostics 4458–4465 and gate consequence 3758; full projection/finding meaning 4485–4818. I carried separate conclusion, validation status and positional reference, rather than one success flag. |
| evidence manifest / role baseline / PW_VERIFY_EVIDENCE | dossier introduction 4830 and comparison 4857–4861; fields/check 4984–5078. I assumed shipped provenance description; later learned normal shipped paths are not rehashed. |
| byoxpc / standard / machme / debuggable | selectors 603–633 (machme refused at 610); external lifecycle 5083–5192; registry fields 5209–5234. I assumed connection kinds; legacy aliases are normalized only when reading old registries. |
| launchd / launchctl / LaunchAgents / LaunchDaemons / gui domain | 5083–5117; service observation 5422–5445. I used ordinary macOS service-manager meanings; command output semantics are limited to stated parsing. |
| Pending / installed / pending_cleanup | 5090–5117; Pending verification 5132–5136; schemas 5199–5234 and 5286–5292. I carried durable installation/cleanup transaction state, not observed service presence. |
| XPC_SERVICE_PATH / RunAtLoad / CFBundle keys | 5106–5117; their configured roles are stated locally. I assumed literal platform configuration keys; the platform's complete schema is outside this text. |
| unresolved_manual | 4162; ownership requirement stated there, procedure still open. I assumed retain-and-investigate, not permission to unlink a reused name. |
| source/check/run/build references and source symbols | first support citation at 76, throughout. Their labels identify evidence locators immediately; support grades at 5581–5584 later specify the credit. I did not assume the cited code was executed or that an unopened check established a broader claim than the adjacent evidence limit. |

## 4. Going back

I returned to no earlier contract passage to understand a later one. I did not follow internal anchors backward. The repeated rule/index tables at the end were encountered in forward order as part of the document, not used to reopen earlier passages. After the last entry I read my own journal's headings and uncertainty paragraphs to collect the close-out statuses. File hashing reads bytes for identity and does not constitute a second interpretive reading.

## 5. Changes of mind

Most earlier entries explicitly withheld belief while waiting for a later rule; their answered questions are recorded above rather than retroactively rewritten. The following developments changed or narrowed what I carried:

- **Entries 1–5, identity and association:** I began with an exact public identity and unnamed separate association checks. By entries 53–54 and 67, I distinguished actor static/live association from ordinary selected-file hashes. Lines 3825–3972 establish actor binding; 4870–4872 and 5020–5027 explicitly limit ordinary hashes to a file read. Identity equality never grew into general binary/runtime equivalence.
- **Entry 2, support language:** I provisionally interpreted check read as inspection rather than execution. The formal definitions at 5581–5584 confirmed and completed that belief. This was confirmation, not reversal.
- **Entries 13–14, termination dependency:** I first knew only declaration order and failed-gate cancellation. Entry 51 narrowed natural termination to an owned ending without a host departure request, potentially signaled, and distinguished unevaluated not_reached from evaluated failure. Lines 3724–3748 changed the operational model I could use.
- **Entries 15–16, extension resource production:** I inferred a syntactically valid resource could be unusable after native failure. Entries 27–29 confirmed that and separated non-null issue, accepted custody, delivered bytes, source acknowledgement and produced candidate handle through lines 2007–2149. I no longer treated a generic resource “success” as one event.
- **Entries 22 and 33, reporting fallback:** An initial rich/minimal fallback reference did not establish how much semantic trust survived. Lines 2422–2445 showed that rich fallback can retain the exact association inconsistency that caused degradation. Entries 48–49 and 64 then separated degradation acceptance from worker lifecycle findings. Retention became explicitly weaker than ordinary association validation.
- **Entries 48–50, application assessment:** Once the application fields appeared, I learned that observed includes native apply failure and that setup_timeout can coexist with a later applied publication/count 1. Lines 3579–3619 and 3624–3626 separate observed application from scheduling eligibility. I would not collapse them into a single applied/not-applied outcome.
- **Entries 57–59, receipt validation:** I initially carried “receipt validation” without a complete division of labor. Lines 4301–4310 narrowed controller acceptance to status/producer/stage labels, with nonce/bytes/digests/lengths remaining host assertions. Entry 59 explicitly revised any broader expectation of independent controller payload checking.
- **Entries 60–64, success and integrity:** The exact-finished rule at 4389–4405 established that even controller integrity findings can accompany ok true/exit 0. Lines 4588–4627 and 4653–4660 further showed aggregate withheld beside valid actor endings and outer success. I stopped treating the outer result as a combined evidence-integrity verdict.
- **Entries 70–75, cleanup success:** The command-level success rules at 5141–5147 and 5163–5167, plus output fields 5301–5317 and presence rules 5422–5445, made call success, command success, observed absence and durable retirement separate. I would not infer cleanup completion from exit 0, booted_out or plist_removed alone.

No entry was retroactively changed to reflect these later distinctions.
