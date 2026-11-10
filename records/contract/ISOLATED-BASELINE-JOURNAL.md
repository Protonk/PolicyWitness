Line numbers count the pasted raw Markdown, including blank lines, with the title as line 1. I had already read the document in the preceding turn; this journal records a sequential rereading, with each entry written before advancing to the next portion.

### 1. Exact identity and reuse — lines 1–20

**What do I now believe?** Saved specimens and independently arriving outputs participate in exact producer/build admission. A clean tree at one annotated release tag produces a release identity; other packaged builds use a digest of scoped shipped paths and contents. Dirty release trees become development builds, and direct Cargo/SwiftPM builds are unbound and refuse public requests and packaged peer checks. Reuse requires the author to review changes and assert the selected release; external runners must be reinstalled when the app contract changes.

**What supports that belief?** Lines 3–6 establish exact admission; 8–15 specify identity construction, on-disk verification, exclusions and reporting; 17–20 assign reuse and reinstall work to the user.

**What remains uncertain?** U1: Which exact inputs and cleanliness rules determine the public identity? U2: What are the surfaces and where do their changes appear? U3: What makes an artifact a saved specimen or a client capture, and how do the named producers relate? U4: What installation procedure and ownership rules govern external runners?

### 2. Stamps guide review — lines 22–50

**What do I now believe?** Surface stamps track canonical shapes and delimited normative text across reachable annotated releases. New or changed surfaces remain unreleased until preparation; removals remain represented. All thirteen displayed surfaces last changed at v0.3.6. I would use this table to navigate review, never as an admission assertion. This answers where entry 1’s surface changes appear.

**What supports that belief?** Lines 24–32 define scope, inputs and stamp purpose; 35–49 associate surfaces with artifacts and display their last-change release.

**What remains uncertain?** U5: What precisely constitutes a shape golden and its canonical form? U6: What limits govern reservations and client output? The manifest, rather than this table alone, owns the exact surface scope.

### 3. Checks with and without history — lines 52–56

**What do I now believe?** A history-free check is a limited check of current inputs and table agreement, with that limitation reported. Regeneration preserves existing release stamps when history is unavailable. Release preflight and the require-history option demand full derivation.

**What supports that belief?** Lines 52–56 distinguish those checks and forbid erasing release stamps without history.

**What remains uncertain?** U7: Which command provides these options, and how is a release table prepared? U8: What is the second of the two tables?

### 4. The request gate comes first — lines 58–63

**What do I now believe?** The request root must contain a string contract matching the running build. A missing, null, mistyped or foreign assertion takes precedence over unknown fields and runner selection; it starts no client. Runner selection resolves to one installed or bundled runner.

**What supports that belief?** Line 63 supplies both the admission ordering and the example combining a foreign assertion with an invalid selector.

**What remains uncertain?** U9: What are the selector fields and aliases? U10: Which structured codes distinguish missing, null, mistyped and foreign assertions?

### 5. Closed request objects — lines 65–75

**What do I now believe?** Swift decoding keys define accepted request fields. Unknown keys, missing required fields and wrong types are refused; parameter names are dictionary data and remain caller-chosen. Optional null usually acts like absence, but the listed actor, entitlement, termination and override fields reject explicit null.

**What supports that belief?** Lines 67–75 establish the parser, closed objects, parameter exception and null exceptions.

**What remains uncertain?** U11: What is the complete request grammar, including the listed fields’ omission defaults? U12: How are diagnostic paths bounded and represented?

### 6. Controller resolution and XPC delivery — lines 77–85

**What do I now believe?** The controller checks even shadowed selectors, gives non-null nested values precedence, records their resolved meaning and removes selection fields before XPC. Actor entitlements survive for separate host checks. The controller splices named augments into a required source string and removes their list; direct XPC rejects unresolved selection or augments.

**What supports that belief?** Lines 77–83 specify selector validation, precedence and delivery; 83–85 distinguish actor requirements and augment processing.

**What remains uncertain?** U13: Which augment names exist and how are fragments combined? U14: What exactly satisfies an actor’s entitlement requirement? The selector reference is now identified as the controller README.

### 7. Meaning checks and prediction limits — lines 87–98

**What do I now believe?** The plan must choose exactly one non-null form; explicit phases and all step identities meet the stated uniqueness rules. Arguments, filter values and profile capture have applicability constraints. Unknown attempt/filter vocabulary is rejected before workers or validators. A known pair lacking prediction can still execute its supported attempt, and query and attempt scopes may differ.

**What supports that belief?** Lines 87–94 enumerate admission rules; 95–98 distinguish unavailable prediction, unsupported OS queries and attempt execution.

**What remains uncertain?** U15: What are the complete attempt/filter vocabularies and prediction exclusions? U16: What makes a capture nonce valid? U17: What does a query/attempt comparison claim when their scopes differ?

### 8. Changes require a fresh assertion — lines 100–106

**What do I now believe?** Optional additions and implementation fixes receive no compatibility exception. A shipped-source change alters a development identity, and the specimen author reviews and asserts the selected build. Maintaining definitions, examples and goldens supports identifying affected surfaces.

**What supports that belief?** Lines 100–106 connect all public surfaces to build identity and explicitly reject a separate request counter or optional-addition exception.

**What remains uncertain?** No new uncertainty; entry 1’s question about the exact shipped-input scope remains.

### 9. Capacity is separate from grammar — lines 108–122

**What do I now believe?** Structurally valid requests may fail runtime capacity checks before attempts. Refusals identify the count and limit; PW does not shrink or reinterpret the plan. The request decoder and tests remain the maintenance mechanism, without another request schema/parser generator. These guarantees preserve intent without promising identical observations across builds or macOS versions.

**What supports that belief?** Lines 108–114 define capacity refusal and its consequences; 116–122 identify maintenance, observational limits and the request-grammar lesson.

**What remains uncertain?** U18: Where do capacity and meaning checks fall relative to one another? Numerical limits are deferred to LIMITS.md; the request lesson offers further grammar examples.

### 10. Policy input and probe effects — lines 124–135

**What do I now believe?** Policy augmentation happens in memory and a missing augment leaves the input file unchanged. Imports and hashes describe held policy input and its closure. Probe predictions do not establish enforcement agreement; attempts have their own effects, including truncation for open_write. A foreign contract blocks even a same-shape request.

**What supports that belief?** Line 129 states input handling and the missing-augment example; line 135 distinguishes predictions from attempts and names the truncating operation.

**What remains uncertain?** U19: What is SBPL’s syntax and how are imports resolved and held? U20: What does enforcement agreement require beyond prediction? The augment catalogue and probe vocabularies remain unspecified here.

### 11. Fresh actors and ordered phases — lines 136–142

**What do I now believe?** Execution has either an ordinary single worker or named actors and phases. Each sandboxed process is fresh and each actor applies policy once. Phases preserve action order and identify the active actor; an unknown actor is refused before children. Extension transfer and consumption have explicit ownership records.

**What supports that belief?** Line 141 gives these execution and ownership commitments.

**What remains uncertain?** U21: What are the extension transfer, consumption and custody rules? U22: How are dependencies between an actor’s termination and later phases established?

### 12. Envelopes do not confer nested trust — lines 144–149

**What do I now believe?** Each envelope has the five named top-level fields. Its producer contract is admitted before interpreting semantic fields; nested helper envelopes have their own context. A foreign helper’s compilation claim cannot become successful policy-check status. Received unsupported bytes remain available.

**What supports that belief?** Line 147 states the required fields, independent admission, byte retention and helper example; this makes the independently arriving envelope rule in entry 1 more concrete.

**What remains uncertain?** U23: What are the types and meanings of kind, result and data, and how are unsupported bytes presented? U24: Does byte availability mean all output is retained without a size limit?

### 13. Held input and the dossier — lines 150–155

**What do I now believe?** The dossier records input and execution provenance without filling unknown observations. Submission and fallback compilation use the same held input, so editing the source file after admission does not change that submission.

**What supports that belief?** Line 153 enumerates dossier content and explicitly tests held-input behavior with a subsequent source-file edit.

**What remains uncertain?** U25: What triggers fallback compilation? U19 remains in part: how and when is the import closure held? I would not extend the source-file example into a complete import snapshot algorithm.

### 14. Host admission and limited comparisons — lines 156–161

**What do I now believe?** A host reply has its own producer identity and provenance. Its contract is checked before steps; a current enclosing envelope does not admit a foreign host reply. Comparisons relate query and attempt observations without proving sandbox causation from permission-shaped failures. query_first requires a collection/release evidence chain.

**What supports that belief?** Line 159 supplies the producer fields, comparison limits and the one-unsupported-diagnostic example.

**What remains uncertain?** U26: What observations and rules constitute the collection/release chain for query_first? Entry 7’s question about cross-scope comparisons and entry 10’s question about enforcement agreement are only bounded, not fully resolved.

### 15. Evidence limits and equipment binding — lines 162–173

**What do I now believe?** Lifecycle claims require native evidence; unknown or contradictory observations withhold dependent claims. Requesting exit does not establish reap, and successful return does not establish an effect. Actor observations bind to a named process and sealed equipment; hash mismatch blocks claimed equipment. Worker ABI identity is separate from public identity.

**What supports that belief?** Line 165 states the lifecycle restrictions; 171 states equipment binding, binary entitlement read-back and identity separation.

**What remains uncertain?** U27: How is equipment sealed and verified? U28: What does the worker ABI identity cover and prove? U29: Which native observations suffice for lifecycle claims other than the specific exclusions stated here?

### 16. Actors own their observations — lines 174–181

**What do I now believe?** Actor execution has no declaration reply or single-worker projection. Each actors entry owns its launch, subprocess, application assessment and equipment association. Setup scopes and worker cells retain their own setup, cleanup and native-capability observations; a scheduling summary cannot replace actor facts.

**What supports that belief?** Lines 176–181 assign ownership and explicitly prevent one acquired decision from publishing another cell.

**What remains uncertain?** U30: What are run/region/custody scopes, cells, acquired decisions and native-capability observations in operational terms? The phrase declaration reply names something excluded without defining its former shape.

### 17. Equipment references and live inspection — lines 183–196

**What do I now believe?** Equipment references are zero-based positions in their named arrays, and absent bindings use null. Instrumented overrides have unverified_fixture identity and do not establish packaged selection. Static and live entitlement read-backs are independently associated; every actor’s requirements use boolean true keys, including live results. Runtime inspection failure cancels scheduled activation while preserving existing facts and earlier cancellation.

**What supports that belief?** Lines 183–190 define inventory and references; 191–196 establish read-backs, actor-specific checks and failure behavior. This answers entry 6’s question about how actor requirements are satisfied.

**What remains uncertain?** U31: Which roles and sources are legal, and how are static/live read-backs associated with the correct equipment? Bounds and reserve geometry are explicitly deferred to LIMITS.md; the sealing mechanism remains uncertain.

### 18. Preparation failure has a narrow shape — lines 198–202

**What do I now believe?** Only the two listed category/reason pairs qualify as preparation_failure. They require runner_failed, rc 1, no launched actors and empty observation arrays. Bounded unique declarative identities may survive without implying execution, as the sole exception to the normal complete observation partition.

**What supports that belief?** Lines 198–202 enumerate accepted failures, required state and the declarative-identity exception; this sharpens the runtime/preparation distinction in entry 17.

**What remains uncertain?** U32: What is the normal complete observation partition, and how does a reader verify it? U33: What exactly produces inconsistent_assignment or equipment_binding_refused?

### 19. Application absence requires evidence — lines 204–210

**What do I now believe?** Unapplied intent is not_requested/unapplied_declaration. Requested application is observed only with an applied or native apply-failure publication; otherwise it is unobserved unless the required proof supports not_attempted. Timeout, done, death or reporting failure alone cannot establish nonattempt. I infer that observed describes evidentiary status, not necessarily successful application.

**What supports that belief?** Lines 204–210 specify the states and their evidence; the explicit apply-failure source supports the inference about observed.

**What remains uncertain?** U34: Which terminal branches are eligible, and what are all allowed state/basis pairs? U35: What exactly counts as an applied or apply-failure publication?

### 20. Termination gates need an owned sequence — lines 212–228

**What do I now believe?** Every non-null gate observation references a positive source reap ordinal and has a later gate ordinal, even when the gate failed. Satisfaction additionally requires final activation before owned reap before closure, consistent PID/wait status, continuous ownership, no prior host departure request, ordered source timestamps and a valid bounded wait. Ordinals are source-process-local. Abnormal natural reap can satisfy termination; completion, done, requested exit or cleanup-only reap cannot.

**What supports that belief?** Lines 212–226 specify records, ordering and wait conditions; 227–228 distinguish qualifying reap from substitutes. This supplies much of entry 11’s dependency evidence.

**What remains uncertain?** U36: How are termination dependencies declared and invalid ones rejected? U37: What precisely are ownership/departure transitions and capture stages? The positive gate allowance is deferred to LIMITS.md.

### 21. Source and dependent clock failures differ — lines 230–238

**What do I now believe?** Absent source timestamps prevent satisfaction even when native facts remain. A missing dependent timestamp after activation storage preserves the activation and already satisfied gate; a present timestamp must not predate source reap. Later cleanup reap does not rehabilitate a reached failed gate. This narrows entry 20: its required timestamps belong to the source sequence, not every later event.

**What supports that belief?** Lines 230–236 explicitly distinguish source clock failure, post-store dependent clock failure and failed-gate consequences.

**What remains uncertain?** No new uncertainty; the exact capture-stage and ownership transitions from entry 20 remain unresolved.

### 22. Receipts inherit context but need validation — lines 240–245

**What do I now believe?** A compiled-profile receipt inherits producer context from an admitted host reply and has no independent schema marker. Its listed fields must be mutually consistent; a matching surrounding reply does not excuse a wrong nonce. A detached receipt supplies no producer context.

**What supports that belief?** Line 243 establishes inherited context, consistency requirements and the wrong-nonce example. I now distinguish these receipts from the independently admitted envelopes and host replies in entries 12 and 14.

**What remains uncertain?** U38: What are the receipt’s permitted statuses, stages and exact consistency checks? The capture nonce validity rules remain unknown.

### 23. Captures, reservations and uncertain delivery — lines 246–251

**What do I now believe?** Client captures and reservations carry contract strings. A capture and its embedded host frame are independently admitted. A binary fingerprint guards decoding but grants no compatibility permission. A matching registry record does not authorize submission to a foreign live peer, and failure after uncertain invocation does not authorize replay.

**What supports that belief?** Line 249 states these separate checks and the replay restriction. It partially answers entry 1’s question about a client capture by identifying its embedded host frame.

**What remains uncertain?** U39: What is the binary frame format and what does its fingerprint cover? U40: How does a caller determine whether invocation occurred and recover without unauthorized replay? The full capture structure remains unknown.

### 24. Request refusal is distinct from execution failure — lines 252–265

**What do I now believe?** Malformed JSON through capacity refusal produces bad_request and controller exit 1. File-read, installation-availability and transport failures remain execution/tool failures. Contract failures include expected_contract; foreign and malformed output remain distinct, and delivery failure takes priority over reply interpretation. The controller copies a runner’s structured failure unchanged; absence of that optional diagnostic says nothing about success.

**What supports that belief?** Lines 255 and 258–264 establish classifications, precedence, propagation and optionality.

**What remains uncertain?** U41: Which exit codes and structured shapes represent execution failures and foreign or malformed outputs? U42: Does optional additive information imply any compatibility allowance, despite entry 8’s rule?

### 25. Bounded machine-readable diagnostics — lines 266–271

**What do I now believe?** Structured request failures contain code and path, plus expected_contract for contract-field refusals. Paths use object keys and decimal array positions; an empty array means root and null means the full location cannot be reported. At most eight components of 63 UTF-8 bytes each are echoed, and refused parameter keys are withheld. Consumers use code/path rather than parsing error prose.

**What supports that belief?** Lines 266–271 give the fields, limits and consumer rule, answering entry 5’s bounded-path question.

**What remains uncertain?** U43: Are array positions encoded as strings or numbers? For withheld parameter keys, does the entire path become null or use another representation?

### 26. Refusal codes and validation order — lines 273–289

**What do I now believe?** The table distinguishes foreign contract, absent field, null required value and type mismatch, answering entry 4’s code question. A termination dependency cannot name an unknown actor, itself or an actor whose final visit is not earlier; its diagnostic locates after_termination.actor_id. Capacity precedes meaning checks, answering entry 9. Refusals contain no steps or child observations, although the XPC host may already have launched. Only one defect is reported; unfamiliar codes remain unclassified.

**What supports that belief?** Lines 275–284 define codes and diagnostic details; 286–289 state execution limits, ordering and treatment of unfamiliar codes.

**What remains uncertain?** U44: What are native-string admission limits? The dependency field is now located, but its full request shape remains part of the deferred grammar question.

### 27. Installation checks and legacy records — lines 291–298

**What do I now believe?** Installation checks service identity before signing or launchd changes and again after signing; execution needs both registry and live-peer matches. Contractless records can still be managed under ownership rules. Unknown metadata survives unrelated writes and pending cleanup. Cleanup records accept nested and historical flattened forms; publication requires lossless read-back before atomic replacement but establishes neither ownership nor execution compatibility.

**What supports that belief?** Lines 296–297 give admission timing, legacy management, cleanup representation and preservation requirements.

**What remains uncertain?** U45: How are ownership and observed absence established, and which retired kind aliases are recognized? Entry 1’s installation-procedure question is only partly answered. U46: How do accepted historical registry forms fit the opening ban on historical translation?

### 28. One response schema, separate boundaries — lines 300–311

**What do I now believe?** Response and capture structure comes from porcelain.json through generated Swift/Rust code and tables used by a separately written Python reader. Their shared derivation aligns structure but does not check the schema itself. Production ingestion is binary and public JSON is a typed projection; request/reservation JSON and validator NDJSON have separate boundaries. This confines entry 9’s no-generator rule to requests.

**What supports that belief?** Lines 304–311 state schema ownership, generation, shared limits and the production/test distinction.

**What remains uncertain?** U47: What independently establishes that the schema itself is correct? U48: What is the validator NDJSON contract? Exact response/capture field questions are now deferred to porcelain.json.

### 29. Binary frame grammar — lines 313–326

**What do I now believe?** A frame contains PWP1, a schema wire-identity hash and one typed root. Values have kind/length/payload framing; integer storage is eight bytes while admission enforces native widths. Records use ordered nonzero field tags, maps unique UTF-8-sorted keys, and variants case tags. Optional fields are absent. Text-carried enum and caller-name associations require semantic checking beyond shape.

**What supports that belief?** Lines 313–326 specify this grammar, byte transport for digests and unsigned equipment references.

**What remains uncertain?** U49: What are the numeric kind/record/field/case assignments, boolean encoding, and byte order of integer payloads and other multibyte fields? The excerpt specifies little-endian payload lengths but not every primitive encoding.

### 30. Rejection budgets and retention limits — lines 328–339

**What do I now believe?** Readers reject the listed structural defects and enforce per-frame byte, nesting and logical-storage budgets. Capture and host frames each have their own budget; these are not peak-memory guarantees. A host-valid reply may exceed the smaller client allowance and be refused as runner_reply_truncated. The controller collects all client output before its retention cap, without streamed reading or its own receiver deadline. This answers entry 12: byte availability is not unlimited retention.

**What supports that belief?** Lines 328–339 define rejection, accounting, truncation and collection behavior.

**What remains uncertain?** U50: What are the exact budget values and charging rules? U51: What outer deadline, if any, bounds overall client execution? LIMITS.md and the named primitive reader are identified for allowance/accounting details.

### 31. Optional fields still change the fingerprint — lines 341–345

**What do I now believe?** The wire fingerprint includes record identities, tags, field names, kinds and public presentation rules; even optional-field additions or changed null/byte spellings change it. Locations, defaults and comments do not. There is no additive compatibility or negotiation here; reservation checks the public contract before execution. This resolves entry 24’s question: optional diagnostic presence does not grant cross-version compatibility.

**What supports that belief?** Lines 341–345 enumerate hash scope, exclusions and the separation between decoder checking and compatibility permission.

**What remains uncertain?** U52: How is the schema wire identity canonically serialized before hashing? Entry 23’s fingerprint-scope question is otherwise answered.

### 32. Presentation follows semantic validation — lines 347–358

**What do I now believe?** Binary byte fields gain base64 or lowercase-hex spelling only at public presentation, according to their listed categories. Shape admission does not establish semantic claims: named validators check operations, lifecycle, ordering, equipment, endings and custody. Conflicting observations can be published while dependent claims remain withheld.

**What supports that belief?** Lines 347–355 assign presentation forms and separate structural from semantic admission, answering entry 12’s question about presenting retained unsupported host bytes.

**What remains uncertain?** U53: What are the named validators and their complete acceptance predicates? U54: What exactly are fresh-read content, rejected validator context and owned endings? Their presentation or validation role is stated, but not their complete meaning.

### 33. Release-table maintenance — lines 360–370

**What do I now believe?** Record changes go through docs/porcelain.json and its generator, then reviewed goldens, normative definitions and examples. The stamp generator supports ordinary and require-history checks. Release preparation uses --release before commit/tag, and a check on the tagged tree must reproduce the table. This answers entry 3’s command and release-preparation questions.

**What supports that belief?** Lines 362–370 name the commands and sequence and reiterate that no public schema counter exists.

**What remains uncertain?** No new uncertainty. Entry 3’s second-table question and the canonicalization questions remain unresolved in the text read so far.

### 34. Infrastructure formats and test templates — lines 372–377

**What do I now believe?** Infrastructure and validator markers and worker identity have purposes separate from public admission. Unsupported historical captures preserve bytes without being admitted. Authored request templates omit identity; the harness supplies an independently inspected candidate assertion at submission, and response tests explicitly supply producer context. I infer that the historical registry handling in entry 27 concerns infrastructure representation, not permission to execute a foreign public contract.

**What supports that belief?** Lines 372–377 distinguish marker purposes, historical capture handling and test construction; entry 27 recorded that publication never establishes execution compatibility.

**What remains uncertain?** U55: How does the harness inspect the candidate, and when is a request treated as an authored template rather than a saved specimen? The operational boundary is still unspecified.

### 35. Internal identity generation and checks — lines 379–390

**What do I now believe?** The XPC host and bundle-local worker use an exact SHA-256 source identity, without ABI ordinals or negotiation. The build checks C, Swift and test copies before compilation and signing without rewriting them; explicit regeneration follows input edits. Direct source-test builds use the same regeneration method. The detailed build/signing sequence belongs to BUILD.md.

**What supports that belief?** Lines 382–390 specify identity generation, check timing, regeneration and the build reference.

**What remains uncertain?** U56: Which operations in the full build sequence regenerate rather than merely check, particularly for direct source tests? BUILD.md is named for that sequence. Entry 15’s identity-scope question remains pending.

### 36. Worker source scope — lines 392–404

**What do I now believe?** Worker identity hashes sorted, length-framed repository paths and file contents across the named C/Swift directories and build helpers. Generated identity bodies are excluded. New ordinary helpers enter automatically; symlinks are refused. Compiler inputs are checked using Ninja’s dependency log against the declared inputs plus SDK/developer directories. Even comments change this identity. This answers the scope part of entry 15 for the worker identity, not the public development digest.

**What supports that belief?** Lines 392–404 enumerate the scope, exclusions, discovery and dependency check.

**What remains uncertain?** U57: What framing details and generated-region delimiters are needed to reproduce the hash independently? The generator and shared walker are named, but not opened. The exact public-build scope from entry 1 is still a separate question.

### 37. Bootstrap checks and recorded identity — lines 406–414

**What do I now believe?** The worker checks mapped size, bootstrap magic at byte 0 and the 32 identity bytes at byte 64 before input, evidence or layout-dependent access. Magic/identity mismatch exits 4 without ready/applied/done publication; the host also checks before evidence decoding and attempt release. A reported abi_identity is host-selected and does not establish that the child validated the header.

**What supports that belief?** Lines 406–414 state check order, mismatch behavior, old-worker refusal and the explicit limit on the recorded identity.

**What remains uncertain?** U58: What is the magic value and complete shared-memory layout? U35 is narrowed by the named publication states, but their payloads and evidentiary predicates remain unspecified.

### 38. What internal equality proves — lines 416–425

**What do I now believe?** Internal identity equality establishes agreement on selected source bytes only. It does not prove correctness, compiled layout, toolchain equality, authenticity, behavior or sandbox cause, and is not authentication. Other checks retain those responsibilities. This identity requirement belongs to the jointly built host/worker pair; external transport and validator diagnostics retain independent boundaries.

**What supports that belief?** Lines 416–425 explicitly enumerate the evidentiary limits and identity boundary, completing entry 15’s question about what worker identity proves.

**What remains uncertain?** U59: Which layout, signing and lifecycle/order checks establish the separate properties in a particular build? The text names the responsibilities but supplies no results. The validator’s own contract remains unspecified here.

### 39. What shape goldens record — lines 426–434

**What do I now believe?** Shape goldens record public keys and JSON types. Producer controls collect shapes and write changed candidates for review alongside definitions and examples. They do not remove semantic checks for required fields and do not provide a separate version-bump classifier. This answers the basic meaning part of entry 2’s golden question.

**What supports that belief?** Lines 430–434 define the artifact and review process; entry 2 also recorded that transport goldens include binary identity and presentation details.

**What remains uncertain?** U60: Which producer controls collect these shapes, and how are they run? Canonicalization and the second table remain unspecified.

### 40. Complete envelope build stamp — lines 435–441

**What do I now believe?** Every envelope’s build stamp has contract, describe, commit, version and number. Only contract is the admission identity; the rest describe the build. Release identity still requires a clean annotated release tree, consistent with entry 1’s more specific one-tag condition.

**What supports that belief?** Lines 438–441 enumerate the build fields and distinguish admission from description.

**What remains uncertain?** U61: What are the types and conventions for build.version, build.number, describe and commit? The contract has ended without resolving the remaining open questions.

## Close-out

### 1. Reading conditions

I read the raw Markdown supplied in chat, including its comments, tables and link destinations. I used an in-memory copy to establish the 441 line numbers and expose successive portions. I saved each journal entry before advancing; I did not revise earlier entries.

This was a sequential rereading, not an unexposed first reading: I had already read the complete document in the preceding turn. During the journal pass, I did not reopen earlier contract passages. I consulted the saved journal entries when auditing uncertainties.

I opened nothing besides the supplied contract. I did not follow links, inspect project files, search for the project or consult external sources. The tool use numbered and held the supplied text and journal in memory.

### 2. Uncertainties

Where a question had several parts with different outcomes, I separate those outcomes below. A deferred status identifies the destination named by this contract; it does not claim that the unopened destination necessarily answers every detail.

| Question | Status at the end and practical consequence |
| --- | --- |
| **U1 — Public identity inputs and cleanliness** | **Open.** Lines 8–15 establish broad rules, but do not enumerate the public source suffixes/helpers or every cleanliness condition. The later detailed scope is expressly for worker identity. I could not independently reproduce every public development digest or decide every release-tree edge case. |
| **U2 — Surfaces and change navigation** | **Answered:** lines 24–49 provide the scope mechanism and surface/change table. The exact manifest-defined scope is **deferred** to `contract_surfaces.json` (line 24); without it I could not audit the complete surface-to-input mapping. |
| **U3 — Specimens, captures and producers** | **Answered at the relationship level:** requests assert identity (63); the controller prepares XPC delivery (77–85); envelopes and host replies identify their producers (147, 159); captures embed independently admitted host frames (249). Complete request and capture structures are **deferred** to `REQUEST-GRAMMAR.md` and `porcelain.json` (121–122, 304–311). I could not construct every specimen or decode every capture from this contract alone. |
| **U4 — External-runner installation and ownership** | **Open** beyond the checks in lines 296–297. No complete installation procedure or ownership test is supplied or assigned to a named installation document. I could not confidently perform all installation, reconciliation or removal steps. |
| **U5 — Shape goldens and canonicalization** | Their basic content is **answered** by lines 430–434, with transport-specific content at 25–28. Canonicalization is **deferred** to the named stamp generator, `docs/generate_contract_stamps.py` (29–31, 366). I could not independently reproduce stamp hashes without that implementation. |
| **U6 — Reservation and client allowances** | **Deferred** to `LIMITS.md`, identified for runtime limits and reply allowance (108–114, 335–337). I could not choose safe reservation sizes or predict all capacity refusals. |
| **U7 — Stamp command and release preparation** | **Answered:** lines 366–370 name the generator, checking options and preparation-before-tagging sequence. |
| **U8 — The second table** | **Open.** No later passage identifies it. I could not independently compare the two tables referenced at lines 52–54. |
| **U9 — Selector fields and aliases** | **Deferred** to `../controller/README.md#runner-selection-external-entitlements` (77). I could apply the stated precedence rule but could not confidently author every supported selector. |
| **U10 — Contract-refusal codes** | **Answered:** lines 255 and 276–277 distinguish foreign assertions, absent fields, required null values and mistyped values; line 63 establishes their gate priority. |
| **U11 — Complete request grammar and omission defaults** | Request examples and decoding/validation treatment are **deferred** to `REQUEST-GRAMMAR.md` (121–122). The complete field/default inventory remains **open** within this contract: no named source is specifically assigned all the omitted defaults. I could not confidently author every supported request form. |
| **U12 — Bounded diagnostic paths** | **Answered:** lines 266–271 specify root, null, component and byte limits. The finer encoding questions are retained separately as U43. |
| **U13 — Augment catalogue and combination rules** | **Open.** In-memory splicing and prerequisites are stated, but names and detailed combination behavior are not. I could not confidently select arbitrary augments or predict their complete resulting source. |
| **U14 — Actor entitlement satisfaction** | **Answered:** lines 191–193 require separate actor evaluation using boolean true keys, including live read-back. |
| **U15 — Attempt/filter vocabularies and prediction exclusions** | Request grammar examples are **deferred** to `REQUEST-GRAMMAR.md` (121–122). The exhaustive prediction-exclusion set remains **open**. I could not confidently enumerate all accepted operations or predict which supported pairs lack predictions. |
| **U16 — Valid capture nonce** | **Open.** Lines 90–91 and 243 require validity and consistency without specifying the validity rule. I could not confidently generate a valid nonce from this text alone. |
| **U17 — Comparisons across different scopes** | **Open.** Line 159 bounds comparisons and causation, but gives no complete cross-scope interpretation rule. I could not confidently assign a stronger comparison meaning. |
| **U18 — Capacity versus meaning-check order** | **Answered:** lines 286–288 put capacity checks first. |
| **U19 — SBPL syntax and import resolution/holding** | **Open.** Lines 129 and 153 describe held input and provenance but not SBPL syntax or the import-closure snapshot procedure. I could not confidently write arbitrary policy source or reproduce import handling under concurrent edits. |
| **U20 — Enforcement agreement** | **Open.** Lines 135 and 159 state what prediction and permission-shaped failures do not establish; no sufficient positive criterion follows. I could not certify enforcement agreement from these observations alone. |
| **U21 — Extension transfer, consumption and custody** | **Open.** Lines 141 and 353–355 require records and validation without enumerating the rules. I could not confidently author or validate an extension-transfer sequence. |
| **U22 — Termination dependency evidence** | **Answered:** lines 212–236 establish owned reap, ordering, timestamps, wait conditions and failure effects; line 281 adds invalid dependency relationships. The numerical allowance is **deferred** to `LIMITS.md` (225–226), preventing exact timeout configuration. |
| **U23 — Envelope fields and unsupported-byte presentation** | Record structure is **deferred** to `porcelain.json` (304–311); complete `kind`, `result` and `data` meanings remain **open** here. Retained host-byte presentation is **answered** by lines 347–351: base64. I could not implement every envelope interpretation from this contract alone. |
| **U24 — Unlimited byte retention** | **Answered:** lines 328–339 impose budgets and a smaller client allowance, with truncation refusal and collection-before-retention behavior. |
| **U25 — Fallback compilation trigger** | **Open.** Line 153 specifies shared held input but not when fallback occurs. I could not predict when the fallback compiler runs. |
| **U26 — `query_first` evidence chain** | **Open.** Later passages discuss collection/release constraints but never enumerate the complete chain required by line 159. I could not independently validate every `query_first` claim. |
| **U27 — Equipment sealing and verification** | **Open.** Hash mismatch and static/live associations are described, but the sealing and verification procedure is not. I could not independently establish that equipment is service-sealed. |
| **U28 — Worker identity scope and proof** | **Answered:** lines 382–404 define generation and scope; 406–425 define checks, limitations and the internal boundary. |
| **U29 — Other sufficient lifecycle evidence** | **Open** beyond the particular application and termination rules in lines 204–236. I could not implement complete lifecycle admission for every claim. |
| **U30 — Setup scopes, cells, decisions and excluded declaration reply** | **Open.** Lines 176–181 assign ownership but do not define the operational model or excluded historical reply shape. I could not confidently interpret every setup cell or reconstruct that former projection. |
| **U31 — Equipment roles, sources and association mechanism** | **Open** beyond the positional references and separate read-backs in lines 183–193. I could not validate every role/source combination or independently establish each static/live association. Reserve geometry is **deferred** to `LIMITS.md` (193). |
| **U32 — Complete observation partition** | **Open.** Line 202 names it without defining its full membership or verification rule. I could not validate completeness outside the stated preparation-failure exception. |
| **U33 — Preparation-failure triggers** | **Open.** Lines 198–202 specify accepted labels and output constraints, but not all triggering conditions. I could recognize the permitted shape without predicting every classification. |
| **U34 — Eligible terminal branches and full state/basis vocabulary** | **Open.** Lines 204–210 establish several states and evidence rules without a complete branch or pair inventory. I could not implement exhaustive application-state validation. |
| **U35 — Applied/apply-failure publications** | **Open.** Lines 406–414 add bootstrap and publication restrictions, but do not define the complete publication payloads or predicates. I could not independently derive every application assessment from worker evidence. |
| **U36 — Dependency declaration and refusal** | The field location and invalid relationships are **answered** by line 281, alongside the null rule at 75. Complete request form is **deferred** to `REQUEST-GRAMMAR.md`; I could not construct every dependency-bearing request solely from the refusal path. |
| **U37 — Ownership/departure transitions and capture stages** | **Open.** Their required properties are stated in lines 212–228, but their full state transitions are not. I could not independently validate every owned-reap history. |
| **U38 — Receipt statuses, stages and consistency predicates** | **Open.** Line 243 lists consistency dimensions without their complete vocabulary or predicates. I could not fully validate a compiled-profile receipt. |
| **U39 — Frame outline and fingerprint scope** | **Answered:** lines 313–326 describe the frame grammar; 341–345 define fingerprint coverage and exclusions. The remaining primitive details are U49. |
| **U40 — Uncertain invocation and recovery** | **Open.** Line 249 prohibits deriving replay permission from failure but supplies no complete recovery procedure. I could not confidently retry after uncertain invocation. |
| **U41 — Execution/output failure shapes and exits** | Response record structure is **deferred** to `porcelain.json` (304–311). The complete exit-code and classification mapping remains **open**. I could not implement every execution-failure branch from the stated request exit code alone. |
| **U42 — Additive diagnostic compatibility** | **Answered:** lines 341–345 explicitly exclude additive compatibility, including optional-field additions. Optional diagnostic presence in lines 263–264 does not create admission permission. |
| **U43 — Path element encoding and parameter withholding** | Element representation is **deferred** to `porcelain.json`, which owns response structure (304–311). The precise representation used specifically when parameter keys are withheld remains **open** in the prose. I could not reproduce every diagnostic path exactly. |
| **U44 — Native-string admission limits** | **Deferred** to `LIMITS.md`, the named runtime-admission reference (108–114), with native-string refusal identified at 284. I could not preflight every string against its capacity rules. |
| **U45 — Ownership, observed absence and retired aliases** | **Open.** Lines 296–297 name these conditions without the full tests or alias list. I could not confidently remove every legacy record or normalize every retired kind. |
| **U46 — Historical registry forms versus exact admission** | **Answered at the boundary level:** lines 297 and 372–374 separate infrastructure representation from execution compatibility and public producer admission. I infer that accepting historical registry shapes does not authorize historical public requests or replies. |
| **U47 — Independent schema correctness** | **Open.** Lines 307–309 explicitly say the three derived readers do not check the schema itself; no later passage supplies a complete independent check. I could not treat their structural agreement as proof of schema correctness. |
| **U48 — Validator NDJSON contract** | **Open.** Lines 309, 372–373 and 424–425 preserve its separate boundary without naming its definition. I could not implement or admit validator diagnostics fully. |
| **U49 — Exact wire encodings and numeric assignments** | **Deferred** to `porcelain.json` for record structure and the named primitive reader, `../controller/src/porcelain.rs`, for primitive decoding (304–311, 330). I could not independently implement a byte-compatible reader using only this contract. |
| **U50 — Budget values and charging rules** | **Deferred** to `LIMITS.md` and `../controller/src/porcelain.rs` (330–337). I could not predict every budget rejection or reproduce logical-storage accounting exactly. |
| **U51 — Outer execution deadline** | **Open.** Lines 338–339 rule out a receiver deadline of its own but do not settle every possible outer deadline. I could not infer a maximum total wait. |
| **U52 — Canonical wire-identity serialization** | **Open.** The schema, generator and fingerprint coverage are named, but the exact canonical hash serialization is not specified or expressly assigned to a named explanation. I could not independently reproduce the fingerprint from this prose alone. |
| **U53 — Named validators and full predicates** | **Open.** Lines 353–355 list validation responsibilities without enumerating validators or complete predicates. I could not reproduce semantic admission for all reply records. |
| **U54 — Fresh-read content, rejected validator context, owned endings** | **Open** as complete semantic definitions. Their presentation/validation roles are stated at 348–355. I could preserve their prescribed encodings, but not confidently interpret every associated claim. |
| **U55 — Candidate inspection and template boundary** | **Open.** Lines 375–377 state the harness’s responsibility without its inspection procedure or complete artifact classification rule. I could not reproduce the submission harness confidently. |
| **U56 — Build regeneration/check sequence** | **Deferred** to `BUILD.md#one-build-in-time` (389–390). I could not reproduce the complete source-test, compilation and signing sequence solely from this contract. |
| **U57 — Worker-hash framing and exclusion delimiters** | **Deferred** to `generate_worker_identity.py` and its shared `source_identity.py` walker (384–388, 392–396). I could not reproduce the exact digest independently without those details. |
| **U58 — Bootstrap magic and full shared-memory layout** | **Open.** Lines 406–414 give offsets and behavior, but not the magic value or complete layout. I could not implement a compatible worker header from this text alone. |
| **U59 — Separate checks and results for a particular build** | The build/signing sequence is **deferred** to `BUILD.md` (389–390). The exact full set of layout/lifecycle checks and their results for a particular artifact remain **open**. I could not certify that artifact’s layout agreement, authenticity or runtime behavior from source-identity equality. |
| **U60 — Producer controls** | **Open.** Lines 430–432 describe their action without identifying commands. I could not collect all golden candidates confidently. |
| **U61 — Build metadata types and conventions** | Record types are **deferred** to `porcelain.json` (304–311). The complete conventions for `version`, `number`, `describe` and `commit` remain **open**. I could admit by contract while avoiding assumptions about how to parse or compare those provenance values. |

Entries 8, 21 and 33 introduced no distinct uncertainties. Their carried questions are covered above. Repeated questions about augments, vocabularies, imports, sealing, capture structure, nonce rules, canonicalization and validator boundaries retain the statuses assigned to their original IDs.

### 3. Carried terms

“Not explained” below means that the document never supplied the particular meaning I needed beyond its stated constraints. I used conventional technical meanings where indicated, without treating those assumptions as additional commitments.

| Term, name or reference | First encounter; later explanation | Meaning carried while reading |
| --- | --- | --- |
| **PolicyWitness / PW** | Title, line 1; PW abbreviation at 113. No standalone product definition. | I treated these as names for the system whose sandbox requests, execution and evidence the contract governs. |
| **Public contract / admission** | Lines 3–6; concrete gates at 63, 147, 159, 249 and 296. | I initially read admission as accepting an artifact for interpretation or execution under an exact identity match; later passages separated the boundaries. |
| **Saved specimen** | Line 3; request root at 63, plan rules at 87–98, template distinction at 375–377. | A saved, user-authored execution request asserting a build identity. Its complete format remained external. |
| **Envelope; helper envelope** | Envelope at 4; helpers at 63; explained at 147. | An output wrapper with producer context; nested helpers later proved independently admitted. |
| **Host reply** | Line 4; producer fields at 159 and binary ingestion at 304–326. | A response from the execution host, separate from its enclosing envelope. |
| **Client capture** | Line 4; embedded host frame at 249; structural owner at 304. | A client-produced transport result containing host output, with its own admission boundary. |
| **Producer** | Line 5; field locations at 147, 159 and 249. | The component responsible for a particular arriving artifact, rather than the outermost wrapper’s producer for everything inside it. |
| **Clean/dirty tree; annotated tag; tag blobs; index flags** | Lines 8–12. No general Git explanation or exhaustive cleanliness test. | Conventional Git concepts; I did not assume a particular implementation of “clean” beyond the explicit on-disk comparison. |
| **`vX.Y.Z`, release and development identities** | Lines 8–13. Forms are explained immediately; numeric-version policy is not. | A tagged release naming form and an exact packaged-build identifier, without assuming semantic-version compatibility. |
| **SHA-256** | Line 9 as `sha256`; later fingerprints and worker identities. Algorithm not explained. | The conventional digest algorithm, with separate input scopes for each use. |
| **Shipped source/build inputs; source scope** | Lines 9–12; public scope remains unenumerated. Worker scope appears at 392–404. | The declared packaged inputs, without substituting the later worker-only scope. |
| **Cargo; SwiftPM; packaged peer checks** | Lines 12–13. Build tools are not introduced; peer checks later gain examples at 249 and 296. | Conventional Rust/Swift build systems, and checks between packaged components before public execution. |
| **`PWContract`; `--version`; describe/commit provenance** | Lines 14–15; complete envelope build fields at 438–441. | Ways to report identity and descriptive build metadata. I did not assume formatting conventions beyond those stated. |
| **Surface / surface row / surface stamp** | Lines 17–18; explained at 24–49. | A named public-contract area whose last change helps navigate review. |
| **`contract_surfaces.json`** | Line 24. Not opened. | The authority for which inputs belong to which surfaces. |
| **Golden; canonical shape golden** | Lines 25 and 29; basic definition at 430–434. | A stored reference shape. I carried “canonical” as a deterministic representation without knowing its algorithm. |
| **Reservation; overall client allowance** | Lines 27–28; reservation identity at 249 and 345; retention behavior at 335–339. | A pre-submission arrangement and a client resource allowance, with exact limits still external. |
| **The generator; release preparation; release preflight** | Lines 29–31 and 55; commands and preparation at 366–370. | Stamp generation and release-time verification/preparation operations. |
| **The two tables** | Line 53. Never identified as a pair. | Two expected-agreeing representations, one apparently the displayed stamp table; I did not assign a location to the other. |
| **Actors and phases** | Table at 37; input mentions at 69–75; execution explanation at 141. | Named processes and ordered execution segments, later refined by actor-owned evidence. |
| **Dossier** | Table at 38; explained at 153. | A collected account of held input, provenance, host context and binary observations. |
| **Equipment** | Table at 40; null rule at 75; evidence/inventory treatment at 171 and 183–196. | Execution equipment associated with actors and sealed by the selected service; the exact sealing mechanism remained unknown. |
| **Disposition / lifecycle** | Table at 42; evidence restrictions at 165 and later application/gate rules. | Claims about execution progress, effects and ending, requiring observations rather than inferred success. |
| **SBPL; policy** | Table at 43; source and parameters at 129. SBPL syntax never explained. | A sandbox policy language and the policy supplied for application. I did not invent syntax. |
| **Params** | Table at 43; string-valued caller-named dictionary at 72–74. | Policy parameters, later distinguished from closed object fields. |
| **Augments** | Table at 43; controller handling at 78–85 and 129. | Named source fragments spliced into policy source before submission. |
| **Imports; input closure** | Imports at 43; closure at 129. No complete resolution procedure. | Referenced policy inputs and their transitive input set; that transitive reading was an assumption. |
| **Probe steps; query; attempt; filter** | Probe table row at 44; request-object names at 69; rules at 87–98 and 135. | A query/prediction side and an actual attempted operation, with filters shaping queries. Exact vocabularies remained unknown. |
| **Compiled-profile receipt** | Table at 45; capture fields at 90–91; receipt explanation at 243. | Evidence associated with capturing a compiled policy profile, later known to inherit host context. |
| **Refusal** | Table at 46; request classification at 71 and 255–289. | A rejected request or unsupported output, later separated from execution/tool failure. |
| **Runner; installed/bundled runner; aliases** | External runners at 20; selection at 63 and 77–85. | A selectable execution installation/component. The controller README owns complete selector details. |
| **Required entitlements** | Line 63; actor distinction at 83; boolean/live checks at 191–193. | Required capability keys, checked separately for selection and each actor. |
| **Swift `Codable` / `CodingKeys`** | Lines 67–68. No general explanation. | Conventional Swift serialization machinery and its accepted field-name enumeration. |
| **`_test_overrides`; actor equipment override map** | Lines 70 and 75; instrumented override consequences at 188–190. | Test/instrumentation configuration, without assuming its full field set or defaults. |
| **`bad_request`; bounded field path** | Line 71; classification at 255–264 and path rules at 266–271. | A structured request rejection and a limited location within the input. |
| **`after_termination`** | Line 75; gate evidence at 212–236 and request path at 281. | A phase dependency on another actor’s termination. |
| **Controller; XPC; host; worker; helper** | Controller at 77, XPC/host at 82–83, worker at 88, helper at 63. Roles develop throughout. | Controller prepares/submits; host handles execution; workers perform actor work; helpers produce auxiliary output. XPC retained its conventional interprocess meaning. |
| **Runner provenance** | Lines 82–83; dossier at 153. | Recorded resolved selection and descriptive origin information, not admission permission. |
| **Validator; prediction; `sandbox_check`** | Validator at 88, prediction at 95, `sandbox_check` at 97. Validator output boundary at 309 and 424–425. | A component/query mechanism producing observations about sandbox operations; I did not equate prediction with enforcement. |
| **`capture_nonce`; `capture_compiled_profile`** | Lines 90–91; consistency at 243. | A correlation value and an enabled capture operation; validity and detailed capture behavior remained unspecified. |
| **`probe_plan`; explicit `phases`** | Lines 91–94; ordinary versus actor execution at 141. | Mutually exclusive plan forms; complete object grammar remained outside this text. |
| **The guide; `REQUEST-GRAMMAR.md`; signed CLI/direct-XPC controls** | Lines 117 and 121–122. Guide not uniquely identified; lesson not opened. | A prose explanation and executable/checking examples of request acceptance. CLI retained its conventional command-line meaning. |
| **`LIMITS.md` / LIMITS** | Line 108; further references at 193, 226 and 336. Not opened. | The named source for runtime capacities, reserve geometry and allowances. |
| **Extension transfer/consumption/custody** | Line 141; validator responsibility at 354. Full rules never explained. | Ownership-sensitive transfer and use of sandbox-related capabilities; the exact extension model remained an assumption. |
| **`kind`, `result`, `data`; `generated_at_unix_ms`** | Line 147; structural owner at 304. Complete meanings not given. | Envelope discriminator/outcome/payload fields; I read the timestamp name as Unix milliseconds without assuming its wire type. |
| **Policy-check status; fallback compiler** | Lines 147 and 153. No full procedure or trigger. | Auxiliary policy compilation/checking and a fallback compilation path using held input. |
| **`query_first`; collection/release evidence chain** | Line 159; related constraints later, no complete definition. | An ordering claim requiring evidence that query collection preceded release of attempts. That operational reading remained an inference. |
| **Reap; native progress; effect witness** | Line 165. Specific owned-reap requirements at 212–236. | Conventional OS child-status collection, directly observed progress, and evidence of an actual effect. |
| **Service-sealed equipment; worker ABI identity** | Line 171; internal identity explained at 382–425. | Bound execution equipment and a separate host/worker agreement identifier. ABI retained its conventional interface meaning until the exact source-hash mechanism appeared. |
| **Declaration reply; singular worker projection** | Line 176. Only their absence is stated. | Possible summary/projection forms excluded from actor execution; I did not reconstruct their historical shapes. |
| **`authority_setup.host`; run/region/custody scopes; `authority_setup.workers`; cells; acquired decision; native-capability observations** | Lines 178–181. Ownership is described, operational details are not. | Separately owned setup evidence compartments; I did not infer one cell from another. |
| **`equipment_inventory`; binding `role`/`source`; static/live read-backs** | Lines 183–193. References are explained; role vocabularies and association mechanisms are not. | Inventory plus positionally referenced associations and separate file/static versus running-process observations. |
| **`unverified_fixture`; instrumented overrides** | Lines 189–190. Consequences explained there. | Non-packaged-selection test equipment, without a packaged implementation claim. |
| **XML; reserve geometry** | Lines 191 and 193. XML not explained; geometry deferred to LIMITS. | Conventional XML entitlement material and the arrangement/sizing of reserved resources. |
| **`preparation_failure`** | Line 196; defined at 198–202. | A narrowly admitted before-launch failure category. |
| **`resolved_plan/inconsistent_assignment`; `equipment/equipment_binding_refused`; `runner_failed`; `rc`** | Lines 198–200. Shapes and required result are given; full causes are not. | Closed failure labels and a return/result code, without expanding their triggering predicates. |
| **Complete observation partition** | Line 202. Never fully explained. | A requirement to account for observations across declarative identities, without assuming its exact partition. |
| **Application state/basis; eligible terminal worker branch** | Lines 204–210. Several states explained, full inventory absent. | A claimed application status paired with its evidentiary justification. |
| **Applied / apply-failure / `done` publication** | Lines 207–210; bootstrap/publication constraints at 406–414. | Worker-published evidence, not merely process exit or a host request. Payload definitions remained unknown. |
| **`owned_reap`; capture stage; ownership/departure flags** | Lines 212–214; gate requirements through 236. | Reap evidence retained under host ownership, with contextual stage and departure facts. Full transitions remained unknown. |
| **`capture_ordinal`; `observed_ns`; activation and gate observations** | Lines 214–225. Local ordering and timestamp requirements explained there. | Source-local observation sequence numbers and, by name, nanosecond timestamps. I did not assume a specific clock API. |
| **Receipt status, worker binding, stage and byte count** | Line 243. Consistency required but full semantics absent. | Fields tying captured profile material to a worker and capture event. |
| **Binary shape fingerprint / schema wire identity** | Line 249; frame at 313 and coverage at 341–345. | A structural decoding identity, separate from public compatibility permission. |
| **Registry; live peer; uncertain invocation; replay** | Line 249; installation treatment at 296–297. | Stored installation metadata, the actual contacted process, and possible repeat submission after uncertain delivery. |
| **`schema_version`** | Line 255. Only historical-only specimen behavior explained. | An older marker that cannot replace the required public contract assertion. |
| **`request_failure`; `expected_contract`; `admission_failure`** | Lines 255, 261 and 284; diagnostic structure at 266–284. | Machine-readable refusal material, expected build identity and capacity details. |
| **Native-string admission** | Line 284. Exact rules not explained. | Constraints on strings crossing native boundaries, without assuming particular byte or NUL rules. |
| **`launchd`; signing; ownership; observed absence** | Line 296. General mechanisms not explained. | Conventional macOS service management and artifact signing, plus project-specific ownership/removal evidence. |
| **Pending cleanup; retired kind aliases; lossless read-back** | Line 297. Cleanup shape and preservation obligation explained; aliases not enumerated. | Persisted cleanup state and normalization of known legacy names, preserving opaque metadata. |
| **`porcelain.json` / `docs/porcelain.json`** | Lines 304 and 362. Not opened. | The response/capture schema, not a request schema. |
| **`generate_porcelain.py`** | Line 305; invocation at 363. Not opened. | Generator of response writers, readers and structural tables. |
| **Swift, Rust, Python, C** | Swift at 67; Rust/Python at 306–307; C at 385. No language introductions. | Conventional programming-language names; independent language implementations did not imply an independent schema source. |
| **Validator NDJSON** | Line 309; separate marker/boundary at 372–373 and 424–425. | Newline-delimited JSON diagnostics with an independent contract. |
| **`PWP1`; kinds; record identities/tags; variants** | Lines 313–325. Structural roles explained there; numeric encodings incomplete. | Frame marker and typed binary grammar elements, without inventing missing tag assignments. |
| **Primitive reader, `../controller/src/porcelain.rs`** | Line 330. Not opened. | The implementation enforcing primitive decoding and resource budgets. |
| **Logical-storage budget** | Lines 331–333. Charged categories and non-physical nature explained there. | An accounting limit for decoded logical content, not a peak-memory limit. |
| **Fresh-read content; rejected validator context; code directory hash; owned endings** | Lines 348–354. Presentation/validation roles stated, full meanings absent. | Content from a fresh read, retained diagnostic context, a signing-related digest, and ownership-qualified endings; these were working interpretations. |
| **Base64; lowercase hexadecimal** | Lines 349–350. No codec explanation. | Conventional byte presentation encodings, applied only at projection. |
| **`tests/lib/python.sh`; `docs/generate_contract_stamps.py`** | Lines 363 and 366. Not opened. | The named execution wrapper and stamp-generation command. |
| **Infrastructure format markers; harness; inspected candidate; constructed response tests** | Lines 372–377. Roles partly explained, inspection procedure absent. | Non-admission format markers and test machinery supplying explicit identity context. |
| **`pw-probe-runner`; `generate_worker_identity.py`** | Lines 382–384. Roles explained there; generator not opened. | Bundle-local worker executable and its source-identity generator. |
| **`BUILD.md#one-build-in-time`** | Line 389. Not opened. | The named account of build checks and signature ordering. |
| **`source_identity.py`; worker/source directories; build helper paths** | Lines 394–395. Not opened. | Explicit inputs and the shared source-discovery implementation for worker hashing. |
| **`meson.build`; `meson.options`; Ninja; SDK; developer directory; shim** | Lines 395–400. Build roles partly given; shim not identified precisely. | Conventional build configuration/dependency machinery and toolchain inputs; “shim” was carried as a native bridging component. |
| **Bootstrap magic; shared header; ordinal-era workers** | Lines 406–411. Offsets and refusal behavior given, full layout absent. | A stable early recognition value in shared memory, including rejection by older ordinal-based workers. |
| **`runner_subprocess.worker_evidence.abi_identity`** | Lines 413–414. Meaning explained immediately, but enclosing records remain external. | The host-selected identity field, without treating it as evidence that the child checked it. |
| **Compiled layout checks; signed artifact provenance; lifecycle/order tests** | Lines 418–420. Responsibilities named, procedures/results absent. | Separate evidence for properties the source hash cannot prove. |
| **Producer controls; version-bump classifier** | Lines 430–434. Control action described, controls unnamed; classifier expressly absent. | Test/control machinery collecting shape candidates, without an additional version-change categorizer. |
| **`build.version`; `build.number`** | Lines 438–441. Descriptive role stated, types/conventions absent. | Build metadata excluded from admission decisions. |

### 4. Going back

I did not return to an earlier contract passage during the journal pass. Earlier line references in later entries came from the accumulated journal and the reading already completed, rather than reopening the raw text.

The earlier full-document read happened before this task was assigned; it was prior exposure, not a return prompted by a later passage in this journal.

For the close-out I returned to every entry’s uncertainty paragraph. That was an audit of the journal, not another reading of the contract. I used it to consolidate repeated questions and preserve unresolved parts instead of silently dropping them.

### 5. Changes of mind

No recorded affirmative belief was overturned. The entries were generally bounded enough that later passages supplied distinctions or resolved questions rather than contradicting them. These were the material refinements:

| Earlier entry and belief | Later understanding | Passage responsible |
| --- | --- | --- |
| **Entry 12:** unsupported received bytes remain available; unlimited retention was still an explicit question. | Availability is constrained by frame budgets and the smaller client reply allowance. Collection before the controller’s retention cap also does not promise bounded peak memory or a receiver deadline. | Lines 328–339; recorded in entry 30. |
| **Entry 20:** gate satisfaction requires the stated ordered timestamps. | Those required timestamps belong to the source sequence. A missing timestamp after dependent activation has been stored preserves that activation and the satisfied gate. | Lines 230–236; recorded in entry 21. |
| **Entries 12 and 14:** envelopes and host replies each require their own producer admission. | A compiled-profile receipt is a different case: it inherits admitted host context while retaining its own consistency checks. I did not extend independent producer admission to every nested artifact. | Line 243; recorded in entry 22. |
| **Entry 24:** `request_failure` is optional additive information; whether that implied compatibility remained a question. | Optional presence supplies no additive compatibility. Adding an optional field changes the exact fingerprint. | Lines 341–345; recorded in entry 31. |
| **Entry 27:** historical registry shapes are accepted, leaving their relation to the opening historical-translation prohibition uncertain. | I read the acceptance as infrastructure-format handling, with public execution and producer admission still exact. This is an inference supported by the explicit separation of purposes. | Lines 297 and 372–374; recorded in entry 34. |
| **Entry 15:** worker ABI identity is independent of public identity, with its scope and proof still unknown. | It is an exact source digest for the jointly built pair. Equality establishes selected-source agreement, while layout, authenticity, runtime behavior and sandbox cause remain separate questions. | Lines 382–425; recorded in entries 35–38. |