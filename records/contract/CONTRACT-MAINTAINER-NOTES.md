# Maintainer's close readings of CONTRACT.md

Readings the maintainer supplied during stage 4 of the plan in
`records/contract/CONTRACT-CONTACT-PLAN.md`, kept verbatim. The strain
register in `records/contract/CONTRACT-LEDGER.md` cites them by heading.
Sibling artifacts are named by path without links, under the records link
rule.

## C:243, the compiled-profile paragraph (2026-11-09)

Claims `K-243-1` to `K-243-9`. Register rows `R-01` to `R-05`.

I'd like to focus just on the paragraph in C:243.

The paragraph repeatedly uses the language of a precise contract while leaving the operative relationships unspecified. “Inherits,” “admitted,” “context,” “consistent,” “grants,” and “refuses” each suggest an established rule. Reading closely, we keep having to supply the actor, the comparison, the relevant boundary, or the consequence ourselves. The final example then supplies a concrete rule that the implementation does not perform.

“A compiled-profile receipt inherits its admitted host reply context” has a useful meaning: the receipt is interpreted under the public contract identified by its enclosing host reply. It carries no independent build identity. But “inherits” describes an interpretive relationship, not an operation that transfers information into the receipt. “Admitted” also needs care. The controller checks the reply’s producer contract before checking the receipt; receipt validation is itself part of deciding whether to admit the reply. The sentence cannot mean that the reply has already passed every check before its receipt is examined. Its defensible meaning is narrower: the enclosing reply’s identity must match before the receipt receives semantic interpretation.

“It has no independent schema marker” adds a useful qualification, provided “schema marker” means a separate version or compatibility identity. The receipt still has a structure defined by the shared wire schema. It simply has no independent contract or version field. This should be an uncomplicated fact, yet the guide still tells readers to require a “nested receipt version,” and the source comment still calls the receipt “Versioned.” The surrounding documentation does not consistently describe even this basic property.

“Status, nonce, worker binding, stage, byte count and digest must be consistent” is where the paragraph becomes substantially less informative than its tone suggests. Consistent with what? These items do not participate in one common consistency relation. A captured status requires the producer and stage labels `worker` and `before_apply`; an unavailable status excludes those labels. The captured nonce is compared with the requested nonce. The recorded PID is compared with the worker PID the host is collecting from. The byte count is checked against capacity and determines how many bytes the host reads. The bytecode digest is compared with the host’s calculation over those bytes. “Worker binding” gives a PID comparison the appearance of a broader, unspecified identity guarantee.

Those relationships also have different owners. The host checks nonce, PID, extent and digest while collecting the worker’s capture. The controller’s receipt-specific semantic validation checks status, producer and stage. The list conceals that division of responsibility. Some comparisons require information outside the receipt, so a reader could not perform them merely by inspecting its fields. The host additionally checks source and parameter identities, which the list does not clearly name. Even `captured` carries a substantial condition left unstated here: the host requires successful application and successful worker completion before publishing that status. The paragraph offers a checklist of nouns where it owes the reader actual rules.

The semicolon then joins this incomplete account of consistency to “a detached receipt grants no producer context.” This clause does not explain consistency. It changes the subject back to the relationship between the receipt and its enclosing reply, without saying that it has done so.

“Producer context” is particularly ill-chosen because the reply and the receipt both have something named `producer`, with different meanings. The reply’s producer record identifies its build through `contract`, `describe` and `commit`. The receipt’s producer string says `worker`; its stage says `before_apply`. A receipt extracted from its reply can still contain that producer label, a worker PID, a nonce and a stage. It has not lost all information about its production. What it lacks is the enclosing reply’s build identity. Calling both things “context” prevents the reader from knowing which information the sentence denies.

“Grants” adds another undefined operation. There is no special detached-receipt admission path implementing this denial. The defensible point is that extracting the receipt does not make it independently identify its producing build. That is a limitation on the information retained with an extracted object. The sentence presents it as though the receipt were an authority capable of granting something.

“Example: a wrong nonce refuses the receipt even inside a current reply” is the paragraph’s most emphatic sentence and its least accurate one. “Even” appears intended to establish that matching build identity does not excuse invalid contents. That distinction is valuable. But “current” must mean a matching producer contract, rather than recency or completed validation, and the example must actually demonstrate the second check. This one does not.

“Wrong nonce” also collapses two different failures. A malformed nonce in the request causes request refusal before capture. A nonce in the worker’s capture that differs from the requested nonce causes the host to construct an `unavailable` receipt with reason `capture_nonce_mismatch`. That receipt is published. Its bytecode and associated capture fields are withheld. The result is not accurately described as “refusing the receipt.”

The grammar makes the nonce the refusing agent, which might pass as shorthand if the responsible component and consequence were otherwise clear. Here those are exactly the facts omitted. Does the host reject worker data? Does the controller reject the enclosing reply? Does it discard only the receipt? Does the specimen fail? The sentence gives the reader no way to distinguish those outcomes.

## C:165-236 and C:351-355, lifecycle, equipment and the publication rule (2026-11-10)

Claims `K-165-*` to `K-236-*` and `K-351-*` to `K-355-*`. Register rows
`R-07` to `R-20`.

I’d like to focus on C:165–236 and C:351–355. Many of the individual statements are intelligible, but their relationship remains uncertain. The passages alternate between describing what the host does, what a record contains, what a reader checks, and what a consumer may conclude. The same words—particularly “requires,” “observed,” “facts” and “claims”—carry us across those changes without identifying them.

C:165 says that unknown or contradictory observations “withhold dependent claims.” This is an important commitment, but “dependent claims” has no concrete referent here. Which output is withheld, and how is that withholding represented? The example supplies an actual consequence: an unreaped worker remains unconfirmed despite a successful termination request. That is considerably more useful than the general formula because it distinguishes two observations and names the resulting assessment. The general sentence should support that understanding elsewhere. At present, it leaves the reader to discover separately what counts as a claim and where its supported, unconfirmed or invalid status appears.

C:171 begins with an association between observations, processes and equipment. “The worker ABI identity remains independent of the public build identity” then interrupts that subject. Nothing in the surrounding sentences establishes why their relationship matters to the equipment association being described. “Independent” also leaves the relevant distinction unspecified: separate purposes, different inputs, different values, or different checks? Their source scopes overlap. The useful fact concerns what each identity governs and whether one can substitute for the other. The sentence invokes that distinction without explaining its consequence here.

“Actor evidence binds observations to the named process and service-sealed equipment” also sounds more complete than the explanation that follows. The mechanism includes checking packaged equipment, inspecting a running process and validating the reported associations. Those operations establish different things. A consumer needs to understand what the association asserts before the inventory, binding and entitlement fields can explain how it is represented.

C:176–181 introduces the actor records by denying a “declaration reply” and “singular worker projection,” neither of which is defined. The positive statement that `actors[]` carries each actor’s launch, subprocess, application assessment and equipment association does useful work. The preceding denial mainly asks the reader to imagine alternatives that the document has not described.

“An acquired decision does not publish another cell, and a scheduling summary does not replace any actor’s facts” has the same difficulty. There is a concrete mechanism behind the first clause: the host acquire-loads a decision and reads operation-cell publications separately. But the sentence gives the reader neither that mechanism nor a usable account of the resulting records. The second clause provides no field named “scheduling summary” and no defined operation called “replace.” A concrete case—setup timeout can coexist with an observed application, and both remain reported—would establish a meaningful relationship. I do not see what this standalone sentence adds once those records and their consequences are adequately described.

C:183–196 moves from positional references to equipment classification, entitlement requirements and cancellation. The individual facts are useful, but their purposes are not consistently apparent. For example, override rows “cannot establish packaged selection” appears to limit what the row establishes, rather than whether the override can execute. The text should make that distinction discoverable from the named fields. Similarly, runtime inspection failure cancels activation while preserving earlier setup/application observations. That is a substantive behavior, not merely a qualification to the entitlement fields immediately preceding it.

C:198–202 becomes especially difficult because it explains preparation failure through an undefined normal case. “Observation arrays are empty” does not identify the arrays, and actor and equipment records can remain—including observations supporting the preparation refusal itself. “The sole exception to their normal complete observation partition” then invokes a rule that has not been stated in recognizable terms. The underlying relationship concerns declared action identities and their corresponding observation records. A reader cannot assess an exception to that relationship from the phrase “complete observation partition.” Nor does “sole” account for the separate handling of reporting-failure replies.

C:204–210 contains a distinction worth making very clear. The application assessment separates unapplied intent, established nonattempt, observed application activity and insufficient evidence. `observed` includes an observed apply failure. `unobserved` therefore does not mean that application failed, just as `not_attempted` requires more than an absence of success evidence. The passage supplies parts of this meaning through exclusions involving timeout, `done`, death and reporting failure. Those exclusions become much easier to interpret once the states themselves have clear meanings. “Closed state/basis pairs” announces a restriction without giving the reader the complete set it restricts.

C:212–228 begins with the contents of `owned_reap`, then proceeds into reference shapes, ordinals, timestamps and wait conditions. The purpose of the termination dependency remains largely implicit. The reader needs to know what decision these requirements govern: whether the dependent phase may activate, collect queries and release attempts. Without that, “a satisfied gate additionally requires” reads as another record-consistency rule, although the gate also controls execution.

The ordinal sentence contains necessary information, even if its present wording can go. The host maintains a separate observation sequence for each actor. An actor’s activations, its reap and gate closures referring to it use that sequence; a dependent actor’s activation uses the dependent actor’s sequence. “These ordinals are local to the source actor process” is too broad following “Each phase may retain” an activation observation. It also obscures that the host maintains the counter. The consumer needs the positive definition of the sequence and its ownership to know which ordinal comparisons are meaningful.

C:230–236 preserves a cogent distinction, but its wording obscures the order that explains it. “Native facts may retain absent source timestamps” makes absence sound like something a fact retains. The records retain observations; a timestamp may be absent. Missing source timestamps prevent satisfaction of the dependency. A clock failure after the dependent activation store leaves an activation that has already occurred, so the activation and already satisfied gate remain recorded. A later cleanup reap likewise does not reopen a failed gate. These are different consequences of failures at different moments. Presented as qualifications to “native facts,” they look more arbitrary than they are.

C:351–355 finally says that conflicting observations remain publishable with dependent claims withheld. This materially affects how the earlier requirements must be read. A received record can still contain a gate marked `satisfied` even when the controller finds the supporting evidence inconsistent. The retained field expresses the host’s report; the controller’s integrity findings and withheld disposition appear elsewhere. The word “requires” in the earlier passage does not, by itself, tell a consumer that.

“Unsupported or malformed input cannot become a semantic claim” supplies little help. What input, at which boundary, and which claims? The actual consequences are informative: retained bytes and diagnostics when decoding fails; potentially retained decoded records when admission fails; preserved observations with integrity issues when later checks find contradictions; and distinct handling for a host reporting failure. Calling all of this “cannot become a semantic claim” hides the behavior a consumer must recognize.

There is also a consequential gap between these integrity findings and overall success: `result.ok` currently follows the host’s `finished` outcome independently of the controller’s integrity findings. A consumer can therefore encounter success, a retained affirmative host field and a controller assessment withholding the associated conclusion. These passages need to make that combination intelligible. At present, the reader has to reconstruct which component is speaking, what its statement establishes, and which later qualification governs it.

## C:3-56, C:100-106 and C:430-434, identity, stamps and shape goldens (2026-11-10)

Claims `K-3-*` to `K-56-*`, `K-100-*` to `K-106-*` and `K-430-*` to
`K-434-*`. Register rows `R-21` to `R-32`.

I’d like to focus on C:3–56, C:100–106 and C:430–434. Taken together, these passages should let a developer establish which contract applies and find what that contract commits to. They currently give considerable attention to maintaining contract artifacts while leaving parts of that reader-facing task implicit.

At C:3–6, “The public contract is the release” sounds definitive before either term has been explained. Development builds also have contracts, so “release” cannot simply mean an annotated release. More fundamentally, an identity names the applicable contract; it does not state that contract’s commitments. The opening should establish what the contract governs and how a specimen or received artifact identifies it.

“Saved specimens assert `contract`” and “every independently arriving envelope, host reply and client capture names its producer” describe different relationships. The specimen names the contract it requests; the received artifacts identify the contract under which they were produced. “Names its producer” can suggest an individual process identity or authenticated origin, while the relevant admission value is the reported build contract. “Admission is exact” becomes useful once the reader knows which values are compared.

I would remove “There is no negotiation, implicit acceptance, historical translation or bypass.” The positive admission rule can establish that a matching assertion is required and describe the consequence of a mismatch. Historical evidence handling has concrete behavior of its own. “Bypass” makes an especially expansive assurance without defining the routes it covers. The contract has enough work describing actual operations without enumerating imagined alternatives around them.

C:8–15 combines the forms of identity, their derivation and their observable locations. The release, development and unbound forms are useful distinctions. So are `--version`, envelope metadata and bundle metadata. But the direct answer about where the identity is reported arrives after source suffixes, Git index flags and incidental files. Those details explain how a build derives an identity; they do not themselves tell someone holding an application which contract governs it.

The developer needs to connect the identity reported by that application with the definitions they are reading. An account of digest construction cannot supply that connection by itself. It is worth distinguishing the information needed to identify the applicable contract from the information needed to build or adjust it.

C:17–20 introduces a reasonable responsibility: review the changed surfaces before updating a specimen’s assertion. “Revisit the corresponding definitions” needs a dependable destination. The developer should be able to reach those definitions through `CONTRACT`, with their relationship to the relevant identity made clear. Changing the assertion also follows a decision: review may establish that the selected contract is unsuitable for the intended specimen. Updating the string supplies the admission condition; it does not establish that the specimen still means what its author intends.

The external-runner instruction is comparatively concrete. It identifies an operational consequence of changing contracts: installed runners need replacement.

At C:24, “The manifest … defines the scope” delegates an essential question before explaining what “scope” means. Is this the scope of public commitments, the membership of each surface, or the inputs whose changes move a stamp? Those are related questions, but they are not interchangeable.

The intended direction is for `CONTRACT` to be generated and to remain the public account a developer engages with. Generation changes where authors edit the contract; it need not diminish the authority or completeness of the document readers receive. The manifest can own surface membership and references as authoring inputs. Their substance should be rendered in a form that tells the developer what each surface contains. Reading JSON should not be a prerequisite for discovering what this document covers.

The sentences about transport and installation goldens have a similar problem. They identify maintenance artifacts containing particular information. Knowing that a golden includes field tags, native widths or reservation limits does not tell the reader what those requirements are. The reader needs the definitions, with a clear account of their reach.

The surface table can provide useful navigation to those definitions. Its “Last changed” column needs a precise object, however. The machinery records changes to the specified definition text and golden inputs. It does not independently discover every implementation change that affects behavior. The table’s usefulness therefore depends on a maintenance responsibility that should be stated plainly.

C:52–56 exposes a related distinction between agreement and verification. Without release history, `--check` validates current artifacts and checks that the tables in `CONTRACT.md` and `PolicyWitness.md` agree. It prints “ok: contract inputs current; stamp derivation not checked” and exits 0. Two tables can agree while carrying the same incorrect historical claim.

“Check” is a reasonable name for the narrower operations actually performed. The consequential question is what successful completion certifies. If the requested operation is verification of the stamps, missing history prevents that operation from completing. A warning in the output would alert a person but leave automation with the same successful status.

There is a practical reason for the existing behavior: ordinary builds invoke this command, including builds from source copies without Git history. Changing the default would change build behavior. That deserves an explicit decision about what those builds require. The prose should state the present exit behavior and the narrower result, rather than relying on “explicitly reports” to convey the distinction. It should also identify “the two tables.” Preserving existing stamps during regeneration is a separate protection; preserving them does not verify them.

At C:100–106, “review and assert” joins a human judgment to an enforced comparison. The application can establish that the assertion matches. The review must establish whether the selected contract gives the specimen’s instructions and observations the meanings its author intends.

The next sentence changes addressee: “Keep the affected normative definition, verified examples and shape goldens current” addresses maintainers. Its “so” carries a substantive dependency. The table identifies affected surfaces because maintainers update the material it hashes. The machinery checks agreement among those artifacts; maintaining their correspondence with behavior remains a responsibility of the project.

I would remove “There is no separate request counter or compatibility exception for optional additions.” The positive identity and comparison rules can state the operative requirement without recalling a different versioning scheme.

C:430–434 gives a useful bounded description of shape goldens: public keys and JSON types. It should keep that meaning distinct from permitted values, relationships and behavioral commitments. “Producer controls collect the current shape and write a candidate when it differs” omits that the difference fails the check. The candidate supports review of that failure.

“Review the difference, update the golden” then assumes that updating the reference is the outcome of review. A difference may instead reveal an unintended producer change. The review decides which side needs correction. Keeping the normative definition and example current is a further task, because agreement on shape does not establish agreement on meaning.

“Missing or mistyped required fields still fail semantic admission” introduces another mechanism without identifying it. Those requirements are enforced by readers and decoders, independently of the maintenance comparison. “Still” provides reassurance about a relationship the paragraph has not explained. “There is no separate version-bump classifier” can be removed.

The positive account is that a shape difference fails a check and produces a candidate whose acceptance requires judgment. The generator and goldens can keep declared artifacts in agreement. The text still needs to give developers a clear route from the identity they observe to the commitments under which they act.

## R-20 and the guide's account of a result (2026-11-10)

Register row `R-33`. Draft in
`records/contract/GUIDE-RESULT-ACCOUNT-DRAFT.md`.

R-20 exposes a problem in the guide’s organization as well as an unresolved decision about success.

The controller README gives a more direct account of responsibility than the user guide: CLI status follows the admitted runner outcome; the received reply is preserved; the controller separately validates evidence and produces diagnostics. A user should be able to learn those relationships from the guide without visiting an implementation reference. The guide needs that clarity in terms of public fields and observable behavior.

The relevant explanations are also separated by hundreds of lines. G:1218–1294 introduces the envelope, integrity findings and reporting failure. G:2024–2041 defines `finished`, connects it to `result.ok` and exit 0, and describes the failure outcomes. Understanding one ordinary result requires assembling these passages across unrelated material. These are parts of one explanation, and they should be readable together.

I propose a moderate consolidation around the guide’s output-envelope introduction. That contiguous account should establish:

1. **What each part of the output represents.** `data.runner_result` contains the host’s report. `data.runner_sandbox_diagnostics` contains the controller’s findings about its evidence. The outer `result` and CLI exit status classify the run according to the documented outcome rules.

2. **What success means.** Define `finished` beside the explanation of `result.ok` and exit 0. State whose assessment supplies that outcome and how the controller uses it. The distinction between successful harness execution and successful individual attempts belongs here.

3. **How integrity findings qualify the reported evidence.** Explain where invalidity and withheld claims appear, which received fields remain visible, and how these findings affect—or currently do not affect—the outer result and exit status.

4. **What reporting failure preserves.** Explain `runner_reporting_failed`, retained observations, omitted comparisons and the minimal reply alongside the ordinary result, so a reader can distinguish the available forms of evidence.

The `normalized_outcome` catalog should be adjacent to this account. Detailed descriptions of native observations, lifecycle records and individual attempt kinds can remain in their respective sections, with references from this introduction. A reader interpreting the top-level result should not have to traverse those details to discover what success certifies.

The README’s terseness is useful because it identifies the relationships directly. The guide can then give the additional explanation a user needs. Copying function names into the guide would contribute little; explaining which component supplied each public assessment would contribute a great deal.

For R-20 specifically, the consolidated passage must make the current combination legible: a host reports `finished`, the controller reports invalid evidence and withholds a disposition claim, and the command nevertheless reports `result.ok: true` and exits 0. That combination should be understandable from one passage. Its explanation should not depend on finding “These fields do not change `normalized_outcome`” far from the definition connecting that outcome to success.

Consolidate the existing explanations so the guide has one complete account, rather than adding another summary alongside the scattered versions. A local draft showing the proposed placement and resulting text would make this reviewable.

Keep the behavioral decision in R-20 open. Making the current semantics easy to understand will let us judge whether they are the semantics we want; it does not itself approve retaining them.

## R-14, the observation partition and preparation failure (2026-11-10)

R-14 introduces an exception to a rule it has never made intelligible. “Complete observation partition” means that the declared actions correspond exactly to the step and extension-event records, with associated uniqueness and ordering requirements. That is useful information about reading a reply. Here it appears only as something preparation failure is excused from satisfying. The wording also obscures the distinction between having a record for an action and having evidence that the action ran.

“Observation arrays are empty” is neither sufficiently specific nor a safe general description. Actor and phase records remain, and equipment records can retain actual findings from the failed preparation. The reply contains a mixture of declarations, failure evidence and empty execution records. Calling some unspecified subset “observation arrays” leaves the reader unable to distinguish those categories.

“Sole exception” is also inaccurate: reporting-failure replies bypass the normal partition check too. These cases have different meanings. Preparation failure can leave a declared plan without execution records because nothing launched; reporting failure can retain records whose consistency could not be established. The paragraph’s account of completeness does not accommodate both.

The three validators’ different conditions are concerning, but “presence versus validity” does not yet establish different acceptance: Swift and Rust separately flag an invalid preparation-failure record, so the difference may concern which diagnostics appear. Python’s omission of explicit checks on host regions, custody and phase arrival/completion is a more concrete discrepancy. We currently have differing implementations without an established account of where their final judgments diverge.

## R-07, the vocabulary of withholding and the scope of "dependent" (2026-11-10)

Register rows `R-07`, `R-34` and `R-35`.

The translation from `unresolved` in the host’s claim to `unconfirmed` in the controller’s process summary smells like additional vocabulary without an established difference in meaning. Different fields and different speakers can justify different terms, but they do not automatically do so. Here the reader encounters two descriptions of the same missing final-status evidence without being told whether the controller has made another judgment or merely renamed the host’s assessment. The uncertainty about the vocabulary is unnecessary uncertainty layered onto the uncertainty being reported.

“Dependent claims” is the more consequential ambiguity. It sounds like a precise promise: a missing or contradictory observation prevents the conclusions that require it. But a semantic validation finding can set the overall process disposition to `withheld`, while individual actors retain `clean_exit` assessments. The original host claims also remain visible. Those behaviors may be coherent, but the sentence does not establish their relationship. A consumer cannot tell which conclusions the finding invalidates, which remain independently supported, or whether the overall `withheld` status governs the assessments beneath it. “Dependent” carries the entire promise of selective withholding here; its scope is exactly what needs to be crystal clear.
