# Prompted reading of the frozen contract

This is a separate prompted round. The completed first-reading JOURNAL.md has not been revised. The only input documents opened for this round were PROMPTS.md and the same frozen CONTRACT.md; the journal was available but was not reopened. No linked sources, checks, repository files, external documents or product executions were consulted. Line references below are to CONTRACT.md. The snapshot identity supplied for this reading is SHA-256 `9e3c46c13a8899512f68d9a07e6cecdfc3e2f1057bcf82bada882d3d9029185c`; this round did not independently verify that digest.

“Remembered” identifies a broad belief carried from the first reading, not a newly recovered quotation from the journal. “Prompted work” identifies rereading, searching or reasoning performed for these questions. Searches located passages; their hits alone are not execution evidence. Some broad search output was truncated, so relevant passages were subsequently read in narrower ranges. Confidence concerns what this document states, not whether an implementation was independently verified.

## A. Fourteen prior silences

### A1. Public commitments and the status of typed transport

The opening says the contract identifies the responsible component, conditions of action and resulting record meaning (7–10). Field definitions and clauses specifying an actor, entry, recipient, conditions and consequences state commitments at those boundaries. A surface groups public-contract definitions and canonical shape inputs (105–115). Typed response transport belongs to that public account: its schema fingerprint and separate producer-identity check are specified at 164–170, and its framing, admission and public JSON projection are specified at 1333–1392. Describing machinery does not make these receiver obligations merely background.

Remembered: identities and admission conditions were separate, and the document also addressed build/history operations. Prompted work: reread 7–26, 69–97, 105–191 and the typed-transport passages; searched for public-contract, maintenance, normative and background terminology. Build derivation explicitly addresses the build operator (69–74); stamp derivation addresses the developer (120); 144–147 leaves a build-history requirement to maintainers. Support paragraphs describe the evidence credited, while known-gap passages identify unsettled matters.

Limit and confidence: I found no global rule marking every sentence as normative, background or maintenance, nor a delimiter that makes all prose outside a surface's definitions nonbinding. Classification must follow the particular actor, boundary and stated consequence. High confidence that typed transport states public admission commitments; moderate confidence in this overall classification because the document supplies local distinctions rather than a comprehensive editorial taxonomy.

### A2. Unchanged probes stamp with a changed attempt implementation

The unchanged stamp establishes equality only of the inputs used in that stamp's derivation. It does not establish unchanged implementation or execution behavior: the document expressly says implementation changes can require review despite unchanged prose and shape inputs (105–115). It can direct review toward changed definitions and identify where declared surface inputs remained the same. Exact target identity, rather than the surface stamp, governs admission (108–110, 18–26).

Remembered: a stamp was a review aid, not an admission credential. Prompted work: reread 105–156. For the stated X-to-Y case, I infer a useful review would consider the relevant Y definitions and the changed attempt implementation/evidence before explicitly reasserting the specimen for Y. The requirement for an explicit choice about target commitments is stated at 114–115; this particular review sequence is my reasoning, not a prescribed checklist. History derivation itself depends on reachable annotated releases and their own input framing (120–126).

Limit and confidence: this document alone supplies neither the hypothetical implementation diff nor execution evidence for it. An unchanged stamp cannot credit that unseen change or prove compatibility of every experiment. High confidence in the stamp's narrow meaning; the sufficiency of a particular migration review remains undetermined.

### A3. Cited checks and a passing default battery

Those facts establish neither that the cited runner suite was selected by that battery nor that every obligation of the surface was exercised. A citation can identify a check the author read without crediting its execution. For example, the identity support explicitly says its checks were read, not run (76), and the request support says no execution is credited and its template was not submitted (531). The scope of credited evidence must come from the particular support statement and the actual run's case selection and results.

Remembered: support levels repeatedly separated source reading, check reading and execution. Prompted work: searched for default battery, battery, runner suite and related support terms, then reread representative support passages. I found no mapping here from a release's “default battery” to all cited checks. The executed receipt-label example is unusually specific: it identifies a constructed unit case, a source snapshot and a run, while excluding native capture from that claim (3395–3399).

Limit and confidence: without the actual battery selection/result record and its relationship to the cited check, I cannot credit execution of that runner suite, coverage of the whole surface or native behavior on a particular platform. High confidence that citation and execution credit are distinct; no confidence in the unstated battery membership.

### A4. Wrong-nonce refusal and who compares it

The host compares captured nonce bytes with the valid request nonce during worker collection, after successful-application, completion, capture-status and PID conditions (3359–3370). If that is the first failed condition, it publishes an unavailable receipt with reason `capture_nonce_mismatch`, retaining only status, reason and worker PID and withholding bytecode; it keeps the reply's normalized outcome (3374). The controller's received-receipt check covers status/producer/stage labels; retained nonce and payload fields remain host assertions (3381–3390).

Remembered: capture association was checked by the host, with a separate controller label check. Prompted work: searched nonce occurrences and reread 3330–3399. I did not locate an explicitly titled wrong-nonce example. The relevant support says constructed shared-memory corruption checks were read, not executed (3376). The nearby explicitly executed example concerns producer `future`, not a wrong nonce (3393–3397). I therefore do not transfer that example's execution credit to nonce comparison.

Limit and confidence: a stated refusal rule describes the committed host behavior under its conditions; the presence of an illustration does not independently prove a live native run. The described nonce controls support the host check at the declared evidence level, while native same-object capture requires separate evidence (3399). High confidence about ownership and the conditional consequence; no live wrong-nonce execution claim follows here.

### A5. Satisfied gate beside an integrity finding; reporting failure

A retained `satisfied` value remains the host's assertion. Its supported meaning requires the source final activation and natural owned reap, required timestamps, valid ordering, unbroken ownership, no requested departure and valid timing budget (2955, 2972–2974). For an ordinary semantic reply, failed gate requirements produce `actor_evidence` findings and set the top-level disposition to withheld, termination cause to unknown and integrity to invalid, while preserving the host reply, independently projected actor dispositions and run result/exit (2967). A generic integrity finding alone does not identify which gate or observation failed; its detail and level matter (2979–2981, 3553–3560).

Remembered: retention did not equal endorsement, and findings could coexist with success. Prompted work: reread the gate checks, diagnostic projection rules and degradation passages (1981–1985, 2790–2810, 2953–2981, 3543–3592). `finished` can still produce outer success and exit 0 after an integrity finding (3565–3571). For `runner_reporting_failed`, the controller checks the degradation form and retains assembled records; the ordinary actor/phase relationship checks are bypassed, while worker lifecycle projections still run independently (1981–1985, 2792–2797, 3586–3592).

Limit and confidence: neither a retained gate string nor the absence of an ordinary relationship finding in the degradation branch validates all actor relationships. Independent observations may remain usable at their own boundaries; a failed gate association need not erase a separately supported native reap. Other readers have separately stated checking scopes (2802–2810). High confidence in retention and withholding behavior; the particular gate conclusion requires the actual finding and its underlying records.

### A6. Equal release identities across apps and a live control reply

At an identity-admission boundary, equality establishes that boundary's identity match and nothing more by itself (18–26). Under normal release derivation, a release label names the qualifying annotated tag and selected source inventory/bytes (31–35); equality does not establish identical build configuration, signer, SDK or runtime behavior (62–64). Thus two apps reporting the same release identity can still differ in whether a runner was built or packaged. The reported string alone is not an independent inspection of either app.

Remembered: public, wire and worker identities had separate meanings. Prompted work: reread 18–95, 164–189 and 1122–1157. A separate runner's matching control-reply identity meets the identity condition in reservation admission (1141). It does not replace the other grant/lease fields, subsequent host-reply admission, authentication or equipment checks. Service caller authorization is separately described at 1122–1124; worker protocol identity and executing-binary association are distinguished at 184–189.

Limit and confidence: I cannot infer equal binaries, complete package contents, live worker equipment or an authenticated peer solely from equal strings. Those require their own build, seal, authorization, equipment and execution observations. High confidence about the narrow admission meaning; this document does not supply an actual build-without-runner comparison or inspect the hypothetical installations.

### A7. Saved specimen and an outdated external runner

The refusal point depends on which identity is outdated and where it is observed. A foreign assertion in the saved specimen fails the controller's contract gate before request-selector parsing and augmentation (484, 496); it never reaches client invocation. A registry record must have the current identity for execution (4029). Since selection resolution precedes client invocation (551), I infer a known stale selected record is refused during preparation; a target-resolution failure gives `tool_error`, exit 2, and no client invocation (556). The document does not explicitly assign a dedicated stale-record error here, so that precise mapping remains an inference.

Remembered: local selection, reservation and received-output gates were distinct. Prompted work: reread 475–556, 1122–1157, 1734–1793, 3476–3497 and the external-runner identity passages (3932, 3946, 4029). If the registry looked current but the live host's control identity is foreign, reservation admission fails before a conforming client sends specimen bytes (1136–1143), with a protocol-error classification (3485). A direct host contract refusal can occur after the host exists but before any worker or validator executes (501). A foreign producer discovered only in returned output is later: output refusal does not establish that execution never occurred (1150–1157, 3482).

Limit and confidence: “outdated runner” alone cannot select one of these boundaries. Inspect `result.normalized_outcome`, any structured request failure, `runner_client` transport-admission/submission facts and retained control/capture evidence, and distinguish admitted records from retained rejected bytes. Host connection/control activity can precede a pre-specimen refusal. An old producer's actual compliance also needs evidence beyond this contract (1167). High confidence in the explicitly separated gates; moderate confidence in the inferred stale-registry preparation classification.

### A8. Standalone sbpl-check on a foreign-asserting specimen

This command uses its own policy decoder, selects the root `policy` object, ignores other root members and accepts input without a public-contract assertion (702). A foreign `contract` member therefore does not trigger the saved-specimen identity gate. It also ignores unrecognized policy members, including capture and augment requests (718). Successfully decoded input then faces helper-specific format, source-size, NUL and parameter checks before import inventory or native compilation (722–729).

Remembered: standalone helper input and controller-prepared specimen input were different entry forms. Prompted work: reread 702–729 and the helper result account. Decode/read/usage errors exit 2 on stderr; helper admission refusals exit 1 with an envelope and no compile/import records (711, 729). A compile verdict concerns that helper invocation and its selected source/parameters, with compilation in the helper's own process (1524–1540). Controller fallback supplies normalized source; standalone invocation does not acquire that preprocessing merely by receiving a specimen-shaped file (718).

Limit and confidence: the compile verdict does not admit the foreign specimen for execution, certify release compatibility, establish worker application or establish probe effects. The helper envelope's build identity describes the helper, not acceptance of the ignored assertion. High confidence in the separate admission and compilation meaning; actual native compiler behavior still has the evidence limits stated for that operation.

### A9. Replacement worker and validator supplied to a signed service

A caller whose connection passes host authorization may supply `_test_overrides`; these controls are accepted as request data even by packaged hosts (491, 577, 599). The ordinary worker path and validator path have their documented bounds; the validator remains a separate child with its own query channel (581, 584). Actor admission refuses the singular ordinary-worker override and instead admits a bounded, nonempty role map using `selected` and/or `unentitled` with absolute paths (583). Current contract equality admits neither malformed overrides nor otherwise invalid requests.

Remembered: the test names did not imply a test-only gate, and actor equipment had distinct checks. Prompted work: reread 577–611, 1122–1124, 3091–3097, 3165 and 3736–3738. Actor preparation first checks the packaged inventory and both packaged roles; overrides are additional `test_override` bindings carrying `unverified_fixture` provenance. A bound fixture can be selected, live-matched and executed. Static failure prevents all actor launches; live inspection failure cancels activation but can retain earlier setup/application. Dossier hash comparisons are observations, not admission gates: mismatch alone does not stop invocation.

Limit and confidence: “signed service” does not turn arbitrary replacements into the original native worker or validator. The document does not give ordinary-worker or validator overrides the same static/live actor-equipment guarantee. Protocol/header and received-record checks remain separate from proving the replacement performed a claimed native operation. A singular worker override in an actor specimen is refused, rather than accepted with that actor guarantee. Every override still lacks the stated signed-app boundary coverage (609). High confidence in admission scope and actor ordering; native result attribution requires evidence for the actual selected executable.

### A10. exclusive_plan_forms and unfamiliar refusal codes

The refusal-code vocabulary is expressly open and the displayed list illustrative (1738). `exclusive_plan_forms` is itself listed among current plan-form examples (1761). Its meaning must be read with the owning plan rule: the ordinary form requires exactly one non-null `probe_plan` or `phases`, while the actor form requires phases and forbids non-null `probe_plan` (488–490). A code/path records the first reached problem, not every defect in the request (1745–1747).

Remembered: closed input-field sets were distinct from open refusal categories. Prompted work: reread 1734–1768 and the plan fields. An unfamiliar code remains an unclassified refusal category, with its producer text and available path retained as evidence (1738–1740). It is not rejected simply for being absent from the example list, and it is not silently mapped to a known cause. The longer families table remains illustrative too (1768).

Limit and confidence: the string alone does not establish which producer/boundary supplied it or whether execution happened. An admitted host pre-child request refusal has the separate commitment `bad_request`, `rc: 1`, empty steps and no worker/validator execution (1752). High confidence that the vocabulary is open; a new category's finer meaning remains unknown until its owning rule or producer account is available.

### A11. Development identity reused against a release

The document explicitly leaves the comparison baseline unspecified. A development identity names selected source paths and bytes through a digest; the surface-history table is indexed by releases (37–64, 152–156). The table therefore does not itself supply a release baseline for an arbitrary development assertion.

Remembered: development reuse was a named known gap. Prompted work: reread 149–156 together with the identity and stamp definitions. Exact admission still requires the target identity; the document calls for either a stated baseline or explicit review of the relevant target definitions. I infer that obtaining the target's reported identity and consciously reviewing its relevant commitments can support a new assertion, but there is no stated automatic digest-to-release compatibility calculation.

Limit and confidence: I cannot name the correct predecessor release, reconstruct the old development source from its digest, or declare unchanged behavior solely from a target stamp. High confidence that the baseline is unresolved; adequacy of a particular manual review is not established by this text.

### A12. A command exits 1

The integer alone does not identify `bad_request`, transport refusal or whether experiment execution occurred. For controller runs, exit 1 covers decoded-request refusal, missing or unsupported/malformed capture, truncated/unsupported/malformed host output, transport and reservation failures, unavailable response, and any admitted host outcome other than exact `finished` (3476–3488). Those failures occur at different times. An error after execution invocation can leave receipt and execution uncertain (1148–1150).

Remembered: outer success and nested native results were separate, and failure codes had several owners. Prompted work: reread 1791–1793, 3433–3439 and 3459–3497. A script needs the command kind and its outcome classification, then the structured refusal or admitted transport/submission records appropriate to that boundary. `result.rc` is not a replacement for nested native returns (3434). Other commands define success for their own operation (3433); for example, helper input refusal also exits 1 (729).

Limit and confidence: exit 1 alone cannot prove that no worker ran, that a sandbox denied an operation, or that a captured host report was admitted. Read the normalized outcome, request-failure fields, capture admission and submission state, then the relevant execution records. High confidence in this insufficiency; a command unspecified beyond its integer has no single stronger meaning here.

### A13. Repeated keys, serialization and original request bytes

The host receives the controller's serialized held request, not a promised byte-for-byte copy of the file. The controller reads/parses once, gates identity, parses selection, resolves augments, strips controller fields and serializes for delivery (475, 496, 536). Its held request also supplies fallback compilation (3722). Hashes of the policy source concern decoded UTF-8 source, and JSON whitespace, escape spelling and later edits to the original file do not enter that source hash (3724).

Remembered: the file path was a locator and repeated-key handling was unresolved. Prompted work: reread 475–536 and 3712–3748. The exact behavior of repeated object keys across the controller parser and Swift decoder expressly requires a paired boundary control (529). The closed-field obligations apply to the object each decoder produces. I therefore cannot say first-key-wins, last-key-wins or repeated-key refusal for this end-to-end request path from the contract.

Limit and confidence: preservation of original/selected policy observations is not a promise to retain every original JSON byte. Some decoded source content and its observations are retained; formatting and escape syntax need not survive serialization. Imports are independently opened and can change between observations (3724, 3743–3748). High confidence in held-value delivery; repeated-key semantics remain expressly open.

### A14. Invalid CLI mode versus a selector in decoded data

CLI `--runner-mode` is parsed before the request file is read or gated (551, 1793). An invalid CLI mode therefore fails argument parsing first, as `tool_error` with exit 2, even if the unread file asserts a foreign contract (1791). That is a command-line boundary, not the specimen's decoded-selector boundary.

Remembered: request identity preceded selector parsing, but command-line parsing was earlier still. Prompted work: reread 484, 496, 549–556 and 1791–1793. In decoded request data, the contract gate precedes selector parsing. A foreign assertion therefore wins over a malformed in-file selector and produces local `bad_request`, exit 1, before client invocation. If identity passes, malformed decoded selector values produce local `bad_request`; all supplied legacy values are validated before nested precedence (549).

Limit and confidence: the exact argument-parser diagnostic text is not specified here, nor does this example determine precedence among multiple malformed command-line options. Both described refusals are local and precede client execution. High confidence in the stated ordering and status distinction.

## B. Prior journal situations and clarifications

### B1. Direct source-test build and worker-identity freshness

The contract defines the worker identity's source scope and framing, names `docs/generate_worker_identity.py` among its inputs, and excludes generated identity-region bodies from the digest while retaining their markers (175–182). It also defines runtime worker/header comparisons and their failure exits (184–189). It does not say who regenerates identity copies in a direct source-test build, when that regeneration runs, or whether a freshness check rewrites, refuses or merely reports stale copies.

Remembered: the direct compilation context and worker identity were separate discussions. Prompted work: reread 69–97 and 175–191; searched for source-test, freshness, stale, regeneration and generator terms. The only regeneration wording found in this search at 136 concerns the surface-history outputs, not worker identity. Direct Rust/Swift test identity rules concern public build identity (`unbound` or `test:policy-witness`) at 81–86. Packaged-build recomputation before signing at 69–74 also does not specify direct worker-copy regeneration.

Limit and confidence: a generator pathname and a runtime digest check cannot establish its invocation or maintenance workflow. I cannot assign the requested actor, timing or freshness action from this document. High confidence that those details remain unspecified in the frozen contract; no inference about the actual build scripts is made.

### B2. Accepting a compiled-profile receipt at two boundaries

At worker collection, the host decides whether collected capture output supports publication as `captured`: the ordered conditions cover observed successful application, done and clean reap, capture completion/status, worker PID, nonce, type/extent, payload digest and consumed source/parameters (3359–3374). `captured` means those host checks passed (3329); bytes were copied before apply, but publication also depends on later application and completion checks (3338). Receipt presence itself only says capture was requested and output collected; failures without output can leave it absent (3352–3354).

Remembered: publication and received-label checking were distinct. Prompted work: reread 3320–3399. After producer admission and capacity checks, the controller checks receipt status and its producer/stage relationship, including every present receipt in ordinary, actor, preparation-failure and reporting-failure records (3381–3389). It does not independently repeat the host's nonce/digest/input comparisons; these remain host assertions (3383). A consumer can separately compare a retained request nonce, whereas the controller carried-label check has no such operand (3334).

Limit and confidence: “accepted” without naming the boundary is ambiguous. Host publication, controller admission of the containing report, and an independent consumer's request association support different conclusions. A failed label check yields malformed response, false result, exit 1 and withheld diagnostics while retaining the host report (3390). High confidence in this division; none of these statements independently verifies a particular native capture.

### B3. A's sequence, a gate for D and cross-process time

Actor A's activations, its owned reap and each evaluated gate waiting for A share A's owned-child observation sequence (3006–3010). Thus the gate for phase B of D consumes an ordinal in A's sequence. The gate's `observation.capture_ordinal` is a reference to A's already retained owned reap, not another ending or another capture (2590–2594). The gate's own capture ordinal records its later evaluation/closure. D's activation ordinal belongs to D's sequence and cannot be numerically ordered against A's ordinal as a cross-process sequence (3009–3010).

Remembered: a reap reference differed from the gate capture and sequences were child-local. Prompted work: reread 2574–2594, 2955–2974 and 3006–3011. A satisfied gate requires A's final-activation ordinal < A's owned-reap ordinal < gate-capture ordinal. A's final-activation and reap timestamps must both exist and be nondecreasing; if the dependent activation is timestamped, its time must be at or after A's reap (2973). That timestamp, rather than D's ordinal, supplies the cross-process comparison. A `not_reached` gate has no capture ordinal (3011).

Limit and confidence: these comparisons also require the correct source/final-phase joins, PID/native-status association, ownership, departure and timing-budget conditions (2967, 2972–2974). Merely seeing three increasing numbers cannot establish satisfaction, and missing required times are not repaired by ordinal order. High confidence in the sequence/reference distinction and conditional comparisons.

### B4. Product behavior, machinery and maintainers

The document binds behavior through named operations and field meanings: for example, host request admission refuses before child execution (501), and received-frame admission specifies exact checks and refusal conditions (1370–1372). It also explains machinery such as identity hashing and the binary frame grammar (37–64, 1343–1365). Those explanations can define the very public behavior receivers must follow; machinery is not automatically an exemption from the contract. Typed response transport is explicitly the `wire` surface (244) and prescribes reader admission and public projection (1333, 1370–1387).

Remembered: the text mixed runtime, build and documentation-generation recipients. Prompted work: reread the opening, surface definition, identity operations and wire clauses; searched maintenance/normative/background terms. Packaged-build identity derivation addresses the build operator and compiled components (69); history generation addresses developers (120); complete-history requirements for ordinary builds remain a maintainer decision (144–147). The degradation-association gap is another explicit maintainer decision (1981–1985). Support statements grade evidence rather than silently expanding the operation's guarantee.

Limit and confidence: I found no universal textual boundary partitioning every paragraph into binding definitions versus nonbinding background. The reliable distinctions are the named scope, recipient, operation, support limit and expressly unresolved decision. High confidence that typed transport has public commitments; moderate confidence in any broader categorization beyond these locally stated roles.

### B5. Release X to Y when Y's probes stamp predates X

A stamp older than X says the last reachable annotated release changing the probes surface's declared inputs predates X, under the history derivation; an unchanged stamp still establishes only equality of its own inputs (105–128). It does not admit an X-asserting specimen to Y or prove that all attempts have unchanged implementations. Exact admission uses Y's expected identity (18–26, 484), and reassertion remains an explicit choice about Y's commitments (114–115).

Remembered: stamp history assisted review, while exact assertions selected the build boundary. Prompted work: reread 105–156 and 484. My reasoned sequence is to obtain Y's reported contract, inspect the relevant target definitions and stamp/input history, consider relevant implementation/evidence changes even if probes stayed stamped, decide that the experiment's intended assertions fit Y, and then explicitly change the specimen assertion. The explicit assertion choice and need to review changed implementation are stated; this ordered workflow is an inference, not a supplied command sequence.

Limit and confidence: continued reliance extends to the relevant commitments actually retained at Y and observations supported under their stated conditions. It does not extend to unseen implementation equivalence or test coverage. A source copy without annotated history leaves historical last-change derivation unverified (124–126). High confidence about stamp and assertion meaning; migration sufficiency requires evidence not supplied by the hypothetical alone.

### B6. Verification claims about an individual example

The maximum warranted verification claim is the one attached to that example's applicable support statement and conditions. A template or explanatory example can illustrate specified behavior without having been executed. The apply-only template is expressly unsubmitted (520–531). By contrast, the `future` receipt-producer example has an executed constructed check with a named source snapshot and run, covering public outcome, exit, retained report and diagnostics (3395–3397); it does not establish live native capture (3397–3399).

Remembered: most examples had source/check-reading limits, and one later receipt case carried explicit execution credit. Prompted work: reread those examples and support clauses, with the nonce search distinguishing host corruption checks (3376) from the executed producer-label case. I would rely on a stated behavior as a contract commitment only at its named actor/entry/conditions, after the applicable identity and admission gates. Empirical reliance would additionally require the cited evidence's case, build/source and environment to fit the claim being made.

Limit and confidence: neither a nearby source link nor an executed neighboring case verifies every example or every descendant unless its support scope says so. No examples or tests were run in this isolated reading. High confidence in the document's stated grades; practical behavior of a new run remains unobserved.

### B7. Satisfied gate without the source final-activation time

Such a carried gate cannot establish the contract's satisfied condition. Satisfaction requires both source final-activation and reap timestamps and their nondecreasing order (2955, 2973). At production, unavailable required timing belongs to `clock_unavailable` (2959). If an otherwise admitted ordinary reply nevertheless carries `satisfied` with the missing source timestamp, the controller's semantic gate check records a failed requirement rather than making the retained assertion true (2967).

Remembered: missing evidence could invalidate a projection without deleting the original host account. Prompted work: reread 2953–2981 and 3543–3592. The controller sets top-level integrity invalid, process disposition withheld and termination cause unknown; it preserves the host reply, the claimed gate fields, independently projected actor dispositions, run result and exit (2967, 3553–3571). Consequently an admitted host outcome `finished` can still yield `ok: true` and exit 0. Missing timing in this semantic condition is not, by itself, the malformed-frame/label admission path.

Limit and confidence: this conclusion assumes the ordinary semantic branch and otherwise successful structural/producer admission. Reporting-failure records follow the narrower degradation scope (3586–3592). Independently supported native reap or actor lifecycle observations may remain, but the timely dependency cannot be certified from the incomplete satisfied gate. Findings lack structured actor/phase subjects, so attribution requires reading their details (2979–2981). High confidence in these consequences.

### B8. Returned receipt nonce differs from the submitted nonce

Two boundaries give different answers. If the host observes a mismatch between the worker's recorded nonce and its valid request nonce while producing the receipt, and earlier conditions pass, it must publish `unavailable` with `capture_nonce_mismatch`, only status/reason/worker PID, and no bytecode; its normalized outcome is unchanged (3359–3374). If the scenario instead supplies an already-returned current-producer captured receipt whose nonce differs from a separately retained submitted request, the controller's carried-label check has no request-nonce operand (3334, 3383). Correct status/producer/stage labels do not make that association check happen.

Remembered: I distinguished host production checks from controller receipt-label checks. Prompted work: reread 3329–3390 and the outer-result rules. Assuming all other admission checks pass, the controller retains that returned nonce and other receipt fields as host assertions. The mismatch alone has no stated controller reclassification or exit effect. It copies the admitted host outcome: exact `finished` gives true/exit 0; another host outcome gives false/exit 1 (3459–3469). An independent consumer's comparison can establish the failed association with its retained request (3334).

Limit and confidence: a current producer identity is not proof that every host production obligation was met. A returned contradictory captured receipt is not explained away by identity equality. Other malformed labels, capacities or structural faults can independently cause refusal, and the first host capture failure may precede the nonce condition. High confidence about these conditional outcomes; the question alone does not specify whether the mismatch was caught at production or only observed in received output.

### B9. Equal app identities and a live runner identity

Admission: an arriving identity equal to the receiver's expected identity meets that particular identity gate; other validity, structure and observation conditions remain (18–26). Build equality: normal release derivation ties the label to a clean qualifying annotated tag and the selected source inventory/bytes (31–35), but the digest's equality is explicitly limited to its selected paths and bytes, with configuration, signer, SDK and runtime behavior separate (62–64). Reported equality between installed apps does not independently prove their packaged inventory or binary equality.

Remembered: identity equality did not bundle equipment and authorization guarantees. Prompted work: reread 18–95, 1122–1143, 184–189 and actor equipment checks. A live runner's equal control identity precedes decoding of the remaining control fields; an admitted grant additionally needs valid PID/UUID/credential/lease and attempt association, while its peer PID/instance are still peer assertions (1141–1143). Caller signing authorization is separately configured and checked (1122–1124). Static actor equipment inspection and live code matching supply their own association evidence (3091–3097, 3165).

Limit and confidence: equal release strings alone cannot prove either app contains a runner, the live runner is the intended installation, every selected worker is bound to it, or the caller passed a signing check. Nor does wire-schema or worker-protocol equality substitute for those conclusions (164–189). The actual installed apps and live equipment would need separately obtained observations. High confidence in these separations; no installation was inspected here.

### B10. Who can provide _test_overrides and what the name means

A caller whose connection passes host authorization can supply these controls (599); packaged hosts admit them as request data (577). The name identifies test use, not a test-build restriction or a separate authorization class. Authorization depends on the listener's configured signed-caller and identifier checks, with public identity and reservation admission still separate (1122–1124). A caller must also meet the override grammar, capacities and plan-form restrictions (491, 581–590).

Remembered: these were actual accepted execution controls, not merely fixture documentation. Prompted work: reread the full override table and its authority/coverage notes. The controls can replace an ordinary worker, select actor role fixture executables, replace the separate validator, change worker/validator budgets, and inject post-action or pre-ready delays, signals or termination before slot publication. Their applicability and limits differ: the ordinary-worker path is refused for actors, actor role maps are refused for ordinary form, and actor scheduling retains its fixed allowance despite `worker_timeout_ms` (581–590, 604). Some excessive positive fixture values are forwarded and refused by the worker after launch, not by pre-child admission.

Limit and confidence: the name does not prove restricted access, test context, native equivalence or successful injection. Actor overrides retain packaged checks and additional fixture provenance (599, 3091–3097); ordinary/validator equipment claims cannot be inferred from that actor rule. The signed-app control coverage remains open (609). High confidence in the stated authority and controls; a particular override's actual effect requires its downstream observations.

### B11. Open refusal vocabulary and unfamiliar codes

A consumer cannot treat either displayed request-failure list as exhaustive. The `code` field explicitly has an open vocabulary with illustrative examples, and an unfamiliar value remains an unclassified refusal category whose producer text and path are retained (1738). The longer current-families table likewise supplies examples only; each code's condition belongs to its input rule (1768).

Remembered: unfamiliar diagnostic categories were retained, unlike unknown keys in closed request objects. Prompted work: reread 1734–1768. The selected code/path locates one first-reached failure, so correcting it may reveal another (1745–1747). `exclusive_plan_forms` is already among current examples (1761), illustrating why matching only the shorter displayed list is insufficient. Path retention is itself bounded and may be null (1739).

Limit and confidence: an unfamiliar code does not establish a familiar cause, a malformed response merely by novelty, or an exhaustive account of request defects. The no-child guarantee comes from an admitted host pre-child refusal at 1752, not from recognizing a string in isolation. High confidence in the open vocabulary and retention meaning; the precise semantics of a genuinely new code remain unclassified.

### B12. Development-asserting specimen moved to a release

Specified: the target's exact identity governs admission, the packaged version envelope supplies it, and reasserting a saved specimen for another build is an explicit choice about that target's commitments (18–26, 114–115, 484, 4271–4278). A development digest identifies selected source paths/bytes, whereas the table is release-indexed. The document explicitly leaves the development specimen's comparison baseline unspecified and calls for a stated baseline or explicit review of relevant target definitions (152–156).

Remembered: development reuse could not simply use the release table as though the digest were a release tag. Prompted work: reread those identity/review/version passages. Inferred practical steps are to retain the old assertion as context, obtain the target's reported release identity, identify the experiment's relevant definitions, explicitly review those target commitments and relevant implementation/evidence, and only then choose to change the assertion. Retaining the old assertion and this ordered review procedure are reasoning here; the document does not prescribe those mechanics or a migration command.

Limit and confidence: the baseline, automatic comparison method and criterion proving sufficient review remain unresolved. I cannot derive the prior source tree from its digest or credit compatibility solely from unchanged surface stamps. High confidence about the explicit target gate and stated gap; the inferred procedure is a possible way to make the required choice, not a completed compatibility demonstration.

### B13. Controller exit status 1 and the needed fields

For a controller run, exit 1 identifies a non-success result selected under the run's refusal/execution classifications. It does not uniquely identify `bad_request`, transport failure, failed native attempt or whether the execution RPC occurred (3435, 3476–3488). In particular, a failed individual attempt can coexist with `finished` and exit 0, while a host timeout or reporting failure can yield exit 1 after work occurred (3459–3469, 3488).

Remembered: process completion, host outcome, transport admission and experiment evidence were separate. Prompted work: reread 1280–1288, 1300–1302 and 3433–3497. First inspect envelope kind, `result.normalized_outcome`, `ok`, `exit_code` and error; then the structured request failure for decoded admission refusal, or `runner_client.transport_admission`, request delivery and admitted submission/terminal facts for transport cases. `submission` is `unknown` when capture was not admitted; rejected raw bytes cannot recover an invocation assertion (1284). A retained `runner_result` can require separate admission assessment before its fields are interpreted (3482–3493).

Limit and confidence: after a valid `invoked` observation, an unavailable reply can leave execution uncertain (1150, 1162). An admitted host pre-child refusal, by contrast, explicitly establishes no worker or validator (1752). Nested native records and controller diagnostics are needed for effects, ownership and integrity; the outer integer does not supply them. High confidence in the classification requirement and uncertainty boundary.

### B14. Exact file bytes versus held input

The runner receives the selected host request serialized from the controller's held parsed value. The saved-file path is read once; identity is gated, selection and augments resolved, controller selectors stripped, and the selected request serialized once for client delivery (475, 496, 536). That held serialization also supplies whole-request fallback compilation; actor fallback serializes the held resolved policy objects separately in request order (3722–3724). Direct XPC callers supply their own host form (475).

Remembered: later file edits did not change delivered input, while import files were independently read. Prompted work: reread 475–536 and 3712–3748. Original and selected policy observations are preserved in the dossier, but source hashes identify decoded UTF-8 source rather than original JSON whitespace or escape spelling. The original path remains a locator, and subsequent file edits do not change the held source (3724, 3743). Controller preprocessing can therefore change the delivered object as well as its serialization.

Limit and confidence: the contract does not promise preservation or delivery of every original request-file byte. Duplicate-key interpretation across the controller and Swift decoders remains unresolved (529); the native query parser's stated last-recognized-string behavior belongs to a different protocol and cannot fill this gap (1423). Import scans and native compilation may independently observe changed import bytes, and their parity remains unverified (3748). High confidence about held-input delivery; repeated-key consequences and exact native import parity remain open.

### B15. Admission boundaries by entry point

For a saved-specimen run, CLI argument parsing precedes file reading; the controller then gates the decoded assertion, handles selection/augmentation and serializes the held request (1791–1793, 484–556). Host listener authorization precedes exported reservation methods (1122); the runner client admits reservation control identity/fields before execution invocation, and the host checks the connection-bound credential before specimen interpretation (1134–1150). Host request admission separately checks contract first, then closed decoded structure, capacities and meaning, refusing before worker/validator execution (501–515).

For standalone `sbpl-check`, the policy decoder ignores root fields including a specimen assertion and follows its own read/decode and pre-native policy admission (702–729). Its result concerns compilation in the helper process (1522–1524). A direct host caller supplies the host form: controller-only selector fields are unknown to that decoder, controller augmentation/stripping is not supplied for it, and listener, reservation/credential and host-request boundaries retain their stated entry scopes (475, 536, 1122–1150). The specified runner-client control-admission operation names run/verify at 1141; I do not silently assign a custom direct caller every implementation check of that client.

For independently arriving output, retained bytes require the appropriate reader and expected identity. Typed capture/host frames have extent, fingerprint, root, producer and structural checks before their separately scoped semantics (1370–1372). Controller client-capture admission, host-frame admission, capacity/profile labels and semantic diagnostics remain separate (1300–1302, 3381–3390, 3493–3497). In fallback capture, supported helper envelopes require `sbpl_check`, the current non-unbound build identity and a nonempty outcome (1593–1595). A matching identity or retained record is not itself proof of originating equipment, actual invocation, native effect or all semantic relationships.

Remembered: every entry and reader had its own boundary; the same-looking JSON did not acquire a universal admission rule. Prompted work: this answer assembles the reread request, helper, reservation, typed-reader and fallback clauses above. The arrangement by entry point is my synthesis; the individual conditions are stated commitments. Limit and confidence: actual installed/live authentication, executed-image association, native effects, duplicate-key parity and the expressly differing reporting-failure reader scopes need their respective evidence (1167, 184–189, 529, 2802–2810). High confidence in the separate named gates; no actual invocation, capture or product behavior was independently tested here.

## Prompted-round close-out

All fourteen prior-silence questions and fifteen situation/clarification questions are answered above. They were considered after completion of the unprompted journal. This round used raw line-numbered contract excerpts, deliberate targeted returns and text searches; it was not another forward first reading. The search/reread activity is identified with each answer. PROMPTS.md and CONTRACT.md were the only input documents opened for content during this round, and PROMPTED.md is its separate output. The output was then read mechanically to confirm the 29 answer labels and the remembered-work-confidence markers. No linked documents or repository material were opened, no product or cited tests were run, and no journal entry was changed.

The earlier external interruption belongs to the first-reading conditions already preserved in JOURNAL.md. It supplied no evidence about the contract and did not become a premise in these prompted answers. No additional implementation conclusions have been imported from that interruption or from other agents.
