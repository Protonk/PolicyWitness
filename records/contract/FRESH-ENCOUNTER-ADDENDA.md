# Close-out

This records where the reading stood at the end of the contract, without changing the accepted journal. “Journal §n” refers to section n of `FRESH-ENCOUNTER-JOURNAL.md`. “C n–m” refers to lines n–m of [docs/CONTRACT.md](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md). The follow-up review used only those two documents. It did not supply answers from the implementation or from linked documents.

## 1. Reading conditions

I read raw Markdown displayed in a terminal with line numbers, not a rendered document. I therefore saw the HTML region markers, literal links, table syntax, and headings as source text. The original contract reading was one forward pass in five nonoverlapping windows: C 1–160, 161–245, 246–325, 326–385, and 386–441. I wrote journal entries between windows. The last sentence begun in the fourth window continued in the fifth; I waited for that continuation before writing the internal-host/worker entry. I did not reopen earlier contract passages during that pass or revise earlier entries after receiving later information.

Before the original pass, I opened root `AGENTS.md`, `docs/AGENTS.md`, and `.tmp/AGENTS.md`. Root guidance had also been supplied in the conversation. Those were the only other repository documents read for the original examination. I did not open `README.md`, the linked request lesson, limits, schemas, manifests, build account, source, tests, or verification artifacts. No other agent was consulted. The journal was written as the output, not used as an independent source during that reading.

There were two subsequent activities, which did not contribute to the original end-of-document understanding:

- For the requested move and commit, I opened `records/AGENTS.md`. I also hashed the journal before and after moving it; those byte reads established that the move preserved its contents. Git status and diff-summary commands did not expose another document's substantive contents. No `records/contract/AGENTS.md` content was displayed.
- For this close-out, I reopened the accepted journal and the contract. I read the journal in three windows and the contract in two, to account for the uncertainty paragraphs and check their citations. I opened no other repository file for this task and followed no links.

The root guidance had already supplied a conceptual outline: fresh host/worker processes, separation of XPC hosting from sandboxed work, a collection/release barrier, effects requiring observations beyond `rc == 0`, and limits on sandbox-cause attribution. The journal's claims cite the contract, but my ability to recognize those concepts was not independent of that background. Part 3 identifies the places where it mattered. The `docs/` guidance also made generator ownership and the limits document familiar before I encountered them in the contract. The scratch guidance supplied no additional understanding of PolicyWitness behavior.

The recorded reading cost was carrying unresolved names and distinctions while continuing, then relating later passages to earlier ones. I did not measure reading time, count mental rereads, or test the resulting understanding. The visible file-reading sequence contains no backward visit during the original pass.

## 2. Uncertainties at the end of the document

Every journal uncertainty paragraph is accounted for below, including paragraphs that reported no consequential uncertainty. Mixed questions are split so that an answer about representation does not stand in for an answer about meaning. Repeated uncertainties refer back to the same item rather than becoming new questions.

**Answered** means the contract supplied the answer by its end. **Deferred** means it supplied a named reference that I did not open; schema and source references are identified as such, rather than presented as prose I read. **Open** means the particular detail remained unanswered without a specific referral for that detail. A generic mention of “the guide,” “documented defaults,” or named validators was not enough for me to identify a document containing the missing rule. These statuses describe my reading, not whether the information exists elsewhere.

### Journal §1

- **Answered — identity representation and nonrelease values.** C 8–15 gives `release:vX.Y.Z`, `development:<sha256>`, and `unbound`, including the latter's refusal of public requests and packaged peer checks. C 63 specifies the request's matching string assertion.
- **Answered — the general caller-facing admission failure.** C 255–284 supplies `bad_request`, exit 1, `data.request_failure`, code/path, `expected_contract`, and the refusal categories. C 147, 159, and 249 separately identify unusable helper, host, and live-peer contexts. This settled the general question; it did not supply every producer-specific diagnostic, which remains tracked below.

### Journal §2

- **Open — the exact public development-identity input inventory and hash serialization.** C 8–12 describes scope in general terms. C 392–404 later enumerates a different identity's inputs: the internal host/worker identity. I could not independently reproduce a development contract hash or confidently classify every possible file as included from this document alone. I could still use the compiled identity reported by the build.
- **Open — the exact refusal shape for an `unbound` producer.** C 13 establishes refusal, and C 255–284 supplies general classifications, but no dedicated `unbound` outcome is specified. I could not write a precise diagnostic expectation distinguishing that refusal from other incompatible-producer failures.

### Journal §3

- **Answered — identifying changed surfaces.** C 24–49 explains the scope manifest, stamps, and last-change table; C 100–106 connects it to review of normative definitions.
- **Answered — what an old external runner may do.** C 249 says a foreign live peer receives no submission, and C 296 requires matching registry/live identities while preserving legacy-record maintenance.
- **Open — the exact diagnostic for that old runner.** Those passages do not specify a missing-versus-foreign registry/live-peer code or full diagnostic record. I could predict refusal, but not confidently implement a detailed diagnostic-specific response.

### Journal §4

- **Deferred — the concrete scoped goldens and their shapes.** C 24–29 names `docs/contract_surfaces.json` as the scope reference; C 304–311 later names `docs/porcelain.json` as owner of response/capture structures. C 430–434 explains the purpose of shape goldens without displaying their complete contents. I did not follow those references and could not reproduce or compare a complete transport/installation golden. This referral does not claim that I found the golden bodies inside either file.
- **Deferred — reservation and client allowances.** `docs/LIMITS.md` is identified for runtime admission at C 108, reserve geometry at C 193, and reply allowance at C 336. I could not size a request or reservation confidently against the actual numbers.

### Journal §5

- **Answered — the command owning the stamp flags.** C 366–370 identifies `tests/lib/python.sh docs/generate_contract_stamps.py` and its check/release modes.
- **Open — the identity of “the two tables.”** C 52–56 says they agree; no later passage identifies both tables' locations. I could understand the limited check result but could not locate both comparison inputs from the prose alone.

### Journal §6

- **Answered — contract-error fields and categories.** C 261–277 supplies the controller field, record fields, and code meanings. Combined with C 63, I understood absent, null, nonstring, and foreign assertions as the missing-field, missing-value, type-mismatch, and unsupported-contract cases, with `expected_contract`.
- **Deferred — selector forms.** C 77 points to `controller/README.md#runner-selection-external-entitlements`. Without that reference I could not confidently author all supported runner-selection forms or aliases.

### Journal §7

- **Open — the exhaustive accepted-field inventory.** C 67–70 assigns it to `CodingKeys` but names no declaration file; C 121–122 points to `docs/REQUEST-GRAMMAR.md` for worked specimens, not expressly an exhaustive inventory. I could follow the stated restrictions but could not confidently author every request object from this contract alone.
- **Answered — bounded-path format.** C 266–271 defines keys/decimal positions, root `[]`, null when full reporting is impossible, eight components, and 63 UTF-8 bytes per component.
- **Open — omission defaults for the null-rejecting fields.** C 75 calls them documented defaults without identifying their values or a specific default reference. I could not confidently choose omission when the resulting actor equipment, entitlement requirement, termination dependency, or equipment override mattered.
- **Open — the complete null-versus-absence rules for other optional fields.** The qualification “generally” in C 75 is not replaced by an exhaustive rule. I could not assume that exchanging null and omission preserves every specimen's meaning.

### Journal §8

- **Deferred — selector vocabulary and selector-level entitlement comparison.** The named reference is `controller/README.md#runner-selection-external-entitlements` at C 77. I could not confidently express every selection or predict every selector-entitlement match.
- **Answered — the actor-level entitlement criterion.** C 191–193 supplies separate per-actor evaluation using boolean-true keys, including live read-back. This did not establish that every selector rule is identical to the actor rule.
- **Open — augment fragment catalog and splice order.** C 129 confirms in-memory resolution and the missing-augment consequence, but provides neither detail nor a specific catalog/order reference. I could not confidently choose an arbitrary fragment name or reason about the order-sensitive result of several fragments.

### Journal §9

- **Open — nonce validity.** C 243 adds receipt consistency and wrong-nonce refusal; C 282 names `invalid_capture_nonce`. Neither specifies valid nonce syntax. I could not confidently create a valid compiled-profile capture request from this text alone.
- **Open — complete attempt/filter vocabularies and prediction-excluded pairs.** C 135 reiterates that vocabularies are closed without enumerating them. I could not confidently author an arbitrary probe or predict every `prediction_unavailable` case. The worked-specimen reference at C 121 does not assert complete coverage of these sets.
- **Answered — the general refusal boundary and capacity/meaning order.** C 258–259 and 286–288 place meaning refusals in `bad_request`, exclude steps/child-process observations, allow host decoding, and put capacity before meaning checks.
- **Open — whether every other listed meaning check occurs before creation of any worker or validator.** C 87–88 expressly says that for unknown attempt pairs/filter kinds. Later absence of child observations does not separately prove the precise creation timing for every check. I could predict a refused plan with no reported attempted steps, but not confidently assert that no validator process was created for every malformed case.

### Journal §10

No consequential uncertainty was recorded. The qualification remains: implementation fixes require acceptance of the selected identity without necessarily changing the grammar. C 100–106 is sufficient for that belief; no missing capability arose from this paragraph.

### Journal §11

- **Deferred — numerical runtime limits and their complete scopes.** The direct reference is `docs/LIMITS.md` at C 108. I could understand refusal without truncation but could not confidently size a plan or choose between revising it and selecting a build with adequate capacity.

### Journal §12

No consequential uncertainty was recorded about preservation of intent versus repeatability of sandbox observations. C 116–122 supplied that distinction. The lesson and controls remained unopened; their absence did not prevent understanding this limitation.

### Journal §13

- **Open — import resolution and policy-input hash coverage.** C 153 adds dossier imports/provenance but no resolution or hash algorithm. I could not confidently reconstruct a policy's imported closure or verify its complete input digest.
- **Answered — the holding boundary's observable consequence.** C 153 says submission and fallback compilation use the same held input and a source-file change after admission does not alter the submission.
- **Open — exactly when and how that input is acquired and held.** C 153 supplies the stability property, not the acquisition/copying procedure. I could rely on the stated post-admission stability but could not confidently describe the internal snapshot or resource-acquisition sequence. This is the same mechanism uncertainty retained in Journal §17.

### Journal §14

- **Open — complete action/filter lists.** This is the vocabulary uncertainty in Journal §9, with the same limitation on authoring arbitrary probes. `open_write` in C 135 supplies one action's behavior, not the list.
- **Deferred — complete observation record shapes.** C 304–311 names the response/capture schema `docs/porcelain.json`. I could interpret the prediction/attempt distinction but could not confidently enumerate every field or write a complete record reader without it.
- The paragraph's qualification about possible operation failure was already settled: C 135 names the operation, not a guarantee that a given attempt succeeds. It did not leave a separate uncertainty.

### Journal §15

- **Open — complete request encodings for actor policy, equipment, phase transitions, and extension operations.** C 141 provides their roles, not their full object forms or a specifically named complete actor-request reference. I could not confidently author a general actor/extension specimen.
- **Answered — important parts of the reply-side equipment and transition representation.** C 176–193 supplies actor ownership and equipment references; C 212–236 supplies activation/reap/gate observations and their constraints.
- **Deferred — the remaining full response record structures.** `docs/porcelain.json` owns them at C 304–311. I could not enumerate all actor/equipment/extension reply fields without following that referral.
- **Open — the complete actor-lifetime overlap and cross-process scheduling rules.** C 220–236 gives termination dependencies, and C 281 constrains a source's final visit, but neither describes every scheduling case. I could reason about those specific dependencies, not confidently predict every possible actor overlap.

### Journal §16

- **Open — the complete envelope `kind`/`result` vocabularies.** Examples such as `bad_request` do not enumerate them; C 319–322 distinguishes textual vocabularies from structural framing. I could not confidently classify every envelope value.
- **Answered — how retained host bytes are presented.** C 347–350 says retained host reply bytes become base64 at presentation.
- **Deferred — the exact fields exposing retained bytes.** The named response/capture structural owner is `docs/porcelain.json` at C 304–311. I could not locate every retained-byte field from the prose alone.
- **Deferred — the full response structure containing a policy-check failure.** The same schema referral covers response shape. **Open — the particular policy-check status/code produced by the foreign-helper example.** C 147 excludes success but never names the precise alternative. I could reject the success claim, not confidently predict its complete machine-readable failure result.

### Journal §17

- **Open — holding mechanism.** This repeats Journal §13. The stable held-input promise at C 153 lets me trust that described relationship, but not specify how the snapshot is acquired or stored.
- **Open — binary-inventory observation method.** No later passage explains how the dossier obtains that inventory. I could read it as an observation, but could not confidently infer its collection method or completeness.
- **Deferred — structural representation of unknown observations.** `docs/porcelain.json` owns response structure at C 304–311, with presentation rules discussed at C 341–350. C 326 answers that absent optional fields are not filled with fabricated defaults, but does not display every unknown-value representation. I could preserve the distinction between unknown and absent fact without confidently decoding every field's null/absence spelling.
- The warning against assuming a complete inventory of environmental influences remains a limit on my belief, not a separate unanswered question.

### Journal §18

- **Open — the complete collection/release chain establishing `query_first`.** C 230–236 and 411–414 give relevant release restrictions but never enumerate the full chain. I could not independently validate a `query_first` claim against all required observations.
- **Deferred — full response fields carrying that evidence.** C 304–311 identifies `docs/porcelain.json` for record structure. Reading it would be a route to field layout, not by itself an answer to the semantic-chain question. Without it I could not confidently build a complete evidence reader.
- **Answered — the claim-level consequence of an incomplete chain.** C 165 withholds dependent claims for unknown/contradictory observations; C 351–355 separates admissible shape from validated claims. Together with C 159, I understood that an incomplete chain does not authorize `query_first`. **Deferred — its exact absent/null/status representation**, as a response-shape question, to `docs/porcelain.json`. I could withhold the conclusion, but not confidently predict the precise projected field value.

### Journal §19

- **Answered — application and termination examples of the native evidence requirements.** C 204–210 distinguishes applied/apply-failure publications, proved nonattempt, and unobserved application. C 212–236 specifies actor-owned reap and gate evidence.
- **Deferred — the complete lifecycle field layout.** `docs/porcelain.json` is the named structural owner at C 304–311. I could not enumerate a complete lifecycle record from the prose.
- **Open — an exhaustive mapping from native observations to every disposition.** The later examples do not supply every disposition or its rule. I could interpret the specified cases, but could not confidently classify every lifecycle result.

### Journal §20

- **Open — equipment sealing mechanism and equipment-hash coverage.** C 183–193 identifies inventories, bindings, and entitlement read-backs without specifying sealing or all hashed inputs. I could not independently reproduce or verify the claimed equipment seal.
- **Answered — worker ABI identity representation.** C 382–395 identifies an exact SHA-256 source identity; C 406–407 puts 32 identity bytes at shared-header byte 64; C 413–414 identifies the reported host-selected field. C 349–350 supplies lowercase hexadecimal presentation for worker identity.
- **Open — the full result of an equipment hash mismatch.** C 198–202 defines `equipment/equipment_binding_refused` when it is a preparation failure, but does not expressly map every hash mismatch to that result. I could predict nonuse of mismatched claimed equipment, not confidently assign every mismatch a preparation-failure code, stage, and complete output shape.

### Journal §21

- **Deferred — authority-setup scope/cell record shapes.** `docs/porcelain.json` is named at C 304–311. I could understand evidence ownership, but could not confidently enumerate the `authority_setup.host` and `.workers` records.
- **Open — their complete state vocabulary and the full meaning of an acquired decision.** C 178–181 establishes independent publication, not a complete decision/state definition. I could avoid treating one cell as proof of another, but could not confidently interpret every setup decision or native-capability state.

### Journal §22

- **Deferred — full equipment row shapes.** C 304–311 points to `docs/porcelain.json`. The positional-reference rules at C 183–190 were enough to understand references, not to implement every row field.
- **Open — how static and live XML read-backs are independently associated.** C 191–193 specifies their use and entitlement criterion, not the association procedure. I could not confidently reconstruct or independently validate that association.
- **Open — why a particular actor has no binding row.** C 187–188 defines the resulting null reference, not every reason for it. I could read null as no produced binding, but could not infer failure, nonattempt, or missing equipment from null alone.

### Journal §23

- **Open — the precise runtime-inspection failure marker.** C 194–196 describes cancellation and retained facts without naming the exact status/code. The schema referral covers structure, not a promised enumeration of semantic outcomes. I could not confidently match every such failure by its marker.
- **Open — the full extent of runtime inspection.** Later material does not enumerate it. I could not treat one retained inspection fact as proof that every intended check ran. The already recorded conclusions that facts survive and that actors need not all be unlaunched remained unchanged.

### Journal §24

- **Open — the complete observation partition.** C 200–202 says preparation failure is its sole exception without defining the normal partition's full membership and coverage rules. I could not confidently determine whether an arbitrary action/phase observation set was complete.
- **Deferred — bounds on retained declarative identities.** C 193 points to `docs/LIMITS.md` for bounds/reserve geometry, alongside the general admission referral at C 108. I could recognize declaration-only retention but could not confidently calculate all legal counts or identity sizes.
- The permitted preparation-failure state, `rc: 1`, and absence of launched actors were already concrete; no additional uncertainty concerned those facts.

### Journal §25

- **Open — the complete application basis vocabulary.** C 204–210 supplies several state/basis relationships, not every allowed basis. I could not confidently accept or reject every arbitrary pair.
- **Open — the eligible terminal worker branches establishing nonattempt.** Later bootstrap checks at C 406–414 do not identify the complete eligible set or make every terminal event sufficient. I could apply the explicit exclusions but could not infer `not_attempted` from an unlisted branch.

### Journal §26

- **Open — all termination-gate result states and capture-stage values.** C 220–236 discusses satisfied/failed behavior but does not enumerate complete vocabularies. I could understand the stated evidence relationships, not confidently interpret every possible value.
- **Answered — ordinal matching is not sufficient by itself.** C 220–228 adds activation/reap/gate order, PID/wait consistency, ownership, departure, timestamps, clock, wait result, and allowance requirements. C 230–236 adds missing-time and failed-gate consequences.

### Journal §27

- **Deferred — the numerical gate allowance.** C 225–226 explicitly points to `docs/LIMITS.md`. I could not confidently select an elapsed-time boundary or decide a numerical near-boundary case.
- **Open — the detailed ownership/departure flag meanings.** C 212–222 supplies their role and some required conditions, but no complete flag definitions or transition rules. I could follow the described ordering, not independently classify every flag combination.

### Journal §28

The paragraph reported no consequential uncertainty about the difference between missing source time and missing post-store dependent time. That understanding remained intact.

- **Deferred — the exact clock-failure result shape also mentioned in the paragraph.** C 304–311 names `docs/porcelain.json` for response structure. I could preserve the stated activation/gate conclusions without confidently enumerating the clock-failure fields.

### Journal §29

- **Open — receipt status/stage vocabularies.** C 243 requires consistency without enumerating them. I could not confidently classify every receipt state.
- **Open — nonce format.** This is the Journal §9 uncertainty: I could not confidently author every valid capture nonce or validate its syntax.
- **Open — the receipt digest algorithm.** C 349–350 specifies hexadecimal presentation and mentions SHA-256 among digest kinds, but does not expressly assign an algorithm to this receipt. I could not confidently recompute the receipt digest from that statement alone.
- **Open — the complete consistency relationships.** C 243 names status, nonce, worker binding, stage, byte count, and digest, with one wrong-nonce example. I could reject that example and require admitted host context, but could not independently implement complete receipt admission.
- The inability to attribute a detached receipt was already answered by C 243; it remained a prohibition, not an unresolved producer question.

### Journal §30

- **Answered — the public-contract check's position relative to execution.** C 345 places it during reservation before execution; C 296 adds the requirement that registry and live-peer identities both match.
- **Open — the full reservation/submission handshake sequence.** Those later statements do not enumerate all messages and transitions. I could not confidently implement the complete exchange.
- **Deferred — the client-capture structure reporting an uncertain invocation.** The capture schema is `docs/porcelain.json` at C 304–311. I could not enumerate its complete fields without that reference. **Open — the corresponding reservation-message state/representation and full uncertainty semantics.** C 309 leaves reservation JSON outside that schema, without giving a named replacement definition. I could not confidently classify every ambiguous invocation state.
- **Open — which pre-invocation failures permit another attempt.** C 249 denies replay authority after uncertainty; no later passage supplies an exhaustive positive retry rule. I could refrain from replay after uncertainty, but could not confidently automate retries for every other failure.

### Journal §31

- **Answered — the missing/type codes.** C 275–277 identifies the categories, while C 266–271 supplies their containing record and paths.
- **Deferred — structural representation of delivery failure in responses/captures.** C 304–311 points to `docs/porcelain.json`. **Open — its complete outcome/code vocabulary.** C 255 and 260–261 establish precedence and tool/execution classification without enumerating those outcomes. I could honor delivery precedence, but could not confidently parse every delivery-specific result or assign every code a meaning.
- Foreign output and malformed output remained different classifications; no question remained about collapsing them.

### Journal §32

- **Open — tool/execution-failure exit statuses.** C 259 assigns exit 1 to the listed request refusals, but C 260–261 does not assign statuses to unreadable files, unavailable installations, or transport failures. I could not confidently classify those cases by exit number alone.
- The optional nature of `data.request_failure` and its lack of compatibility implications were already understood; they supplied no additional outstanding uncertainty.

### Journal §33

- **Open — every representation choice for parameter-key failures.** C 266–271 gives full-location/null rules and withholds refused parameter keys, without displaying each relevant diagnostic example. I could avoid expecting the parameter name, but could not confidently predict the exact path/code for every refused parameter entry.

### Journal §34

- **Deferred — concrete native-string admission restrictions.** C 284 identifies them as admission failures; C 108 names `docs/LIMITS.md` for runtime admission. I could understand the retained count/maximum information, but could not confidently construct inputs at all native-string boundaries.
- **Open — a complete malformed-input-to-code mapping.** C 273–284 groups meanings, and C 288 explicitly supplies one diagnostic rather than all defects. The worked cases in the named `docs/REQUEST-GRAMMAR.md` lesson were not described as an exhaustive mapping. I could not confidently predict the selected code for every compound-invalid specimen.

### Journal §35

- **Open — check ordering within the capacity and meaning stages.** C 287–288 specifies their relative stage order, not all within-stage precedence. I could predict that capacity precedes meaning, but not confidently predict the winning error among every pair of defects in the same stage.
- The limits on exhaustive reporting and guessed interpretations were already settled by C 288–289; no separate uncertainty remained about them.

### Journal §36

- **Open — runner cleanup ownership rules and the observation establishing service absence.** C 296 invokes existing ownership rules and observed absence; C 297 denies that publication itself establishes ownership. Neither gives the full ownership/absence rule or names its document here. I could not confidently decide to remove an arbitrary runner record from this contract alone. The root AGENTS guidance had supplied external-runner references and cautions, but that is background from outside the contract, not a contract answer or referral.

### Journal §37

- **Open — the retired kind aliases and their mappings.** C 297 says known aliases project to current kinds without listing them. I could not confidently normalize an arbitrary historical kind.
- **Open — the exact read-back failure result.** C 297 requires lossless read-back before replacement without giving its failure record/code or complete recovery sequence. I could know that failed verification does not justify replacement, but could not confidently interpret every failure result or automate recovery from it.
- Historical flattened-entry reading did not alter the already held public-identity rule; it left no separate uncertainty about public historical compatibility.

### Journal §38

- **Deferred — the complete structural schema.** C 304–311 explicitly names `docs/porcelain.json`. I could not enumerate all response/capture records without it.
- **Open — implementation of semantic admission.** C 351–355 names categories of validators without identifying a complete semantic-admission document or implementation location. Inspecting implementation was outside the examination; this did not stop me understanding the stated division of responsibility, but I could not implement or verify all semantic rules from the contract alone.
- Shared structure still did not mean the schema itself had been independently checked. That qualification was settled at C 307–309.

### Journal §39

- **Deferred — primitive boolean encoding and byte order of numeric elements other than the stated payload length.** C 330 explicitly links the primitive reader, `controller/src/porcelain.rs`. This was a named source route, not a prose explanation or a source I inspected. Without it I could not confidently write a byte-compatible primitive encoder/decoder.
- **Deferred — concrete record identities, field tags, and declared cases.** C 304–311 assigns record structure to `docs/porcelain.json`; C 341–343 confirms those identities/tags are fingerprinted. I could understand the framing grammar, but could not populate a complete dispatch table.
- **Answered — malformed-structure handling.** C 328–330 enumerates rejected fingerprints, unknown identities/tags/cases, missing fields, wrong kinds, invalid text, impossible sizes/counts, duplicates, and trailing data.

### Journal §40

- **Deferred — numerical budgets.** `docs/LIMITS.md` is the runtime-limit reference at C 108 and the reply-allowance reference at C 336. I could not confidently calculate all frame/retention boundaries without it.
- **Deferred — exact logical-storage accounting charges.** C 330–334 identifies the primitive reader `controller/src/porcelain.rs` as the implementation of those charges. I did not open that source. I could distinguish logical accounting from physical peak memory, but could not confidently calculate a frame's full logical-storage charge.

### Journal §41

- **Deferred — the sizes of the frame, reply, and retention limits.** The named limit reference is `docs/LIMITS.md` at C 108 and 336. I could not confidently calculate the largest reply surviving each boundary.
- **Open — the complete deadline picture for other components or the overall operation.** The termination-gate allowance has its own `docs/LIMITS.md` referral at C 225–226, but C 339's lack of a receiver deadline does not settle every other component's deadline. No later passage supplies a complete timeline or a specific referral for it. I could not confidently promise a total completion bound, or conclude that there are no other timeouts.

### Journal §42

No consequential uncertainty was recorded about the wire fingerprint/public-contract distinction. Its coverage and exclusions at C 341–345 remained separate from the public development identity at C 8–12. No unresolved ability followed from this paragraph.

### Journal §43

- **Open — the complete semantic validator rules.** C 351–355 lists responsibilities, not all acceptance predicates. I could retain or withhold claims in the specified examples but could not confidently validate every native-operation, custody, lifecycle, or scheduling record.
- **Deferred — full projected field shapes.** The structural owner is `docs/porcelain.json` at C 304–311 and 362–364. I could decode the stated base64/hex categories, but could not enumerate the complete projection without that reference.

### Journal §44

No consequential uncertainty was recorded about the described regeneration/stamp sequence. C 362–370 settled the command identities and release ordering. I did not run the commands; understanding their stated responsibilities did not depend on running them.

### Journal §45

- **Open — the harness's independent candidate-inspection procedure.** C 375–377 states the responsibility but does not describe the inspection or identify its procedure. I could understand why an unasserted template differs from a submitted specimen, but could not confidently reproduce that candidate-selection process.
- **Open — the narrower registry, provenance, and other infrastructure-marker definitions.** C 372–374 says they have separate purposes without enumerating those markers. I could not confidently interpret or generate each infrastructure format.
- **Answered — the worker-identity member of that list.** C 382–420 subsequently explains its generation, source scope, handshake, and limits. This answer does not extend to the other markers or the validator NDJSON contract.

### Journal §46

- **Answered — the worker-identity input set.** C 392–404 enumerates the suffixes, directories, helpers/build files, exclusion of generated bodies, discovery rules, and compiler-consumption boundary.
- **Answered — the internal identity handshake.** C 406–414 supplies header positions, worker checks before policy/evidence access, mismatch code/publication behavior, host checks, and the reported identity's provenance. This resolves the handshake question at this entry's host/worker scope, not the external reservation handshake in Journal §30.

### Journal §47

- **Deferred — exact length-framing byte encoding for the source digest.** C 382–395 names `docs/generate_worker_identity.py` and its shared `source_identity.py` walker as the source-identity generation route. The generator is an explicitly linked source reference, not a document I opened. I could not independently reproduce the digest byte stream without that detail.
- **Answered — what I could infer about compiler/SDK inclusion from the consumption boundary.** C 416–418 expressly says equality does not establish identical compiler or SDK. The source-input enumeration at C 392–395 and permitted-consumption boundary at C 399–401 therefore did not license me to treat SDK/developer-directory contents as an equality guarantee. This settled the inference I had withheld; it did not supply the byte recipe above.

### Journal §48

- **Open — the exact result of a mapped-region-size failure.** C 407 requires the size check; C 409 assigns code 4 expressly to identity/magic mismatch. No later passage assigns that code to size failure. I could not confidently predict its exit status or publications by extending the mismatch example.
- **Open — the full `query_first` collection/release chain.** This is the same item as Journal §18. The host identity checks in C 411–414 add a condition, not the full chain. I still could not independently validate the complete ordering claim.

### Journal §49

No consequential uncertainty was recorded about the hash's evidentiary limits. C 416–420 expressly separates source equality, layout agreement, toolchain identity, authenticity, behavior, and sandbox cause. The implementations/results of the other checks were deliberately outside the examination, not missing answers I needed in order to understand this limitation. I made no claim to have verified them.

### Journal §50

- **Open — the validator diagnostic marker and exact admission rules.** C 309 and 424–425 leave validator diagnostic JSON/NDJSON at its own boundary without naming a complete definition. I could recognize its independence, but could not confidently admit an arbitrary validator diagnostic stream or generate its marker.

### Journal §51

- **Deferred — the concrete scoped goldens.** This repeats Journal §4's scope referral to `docs/contract_surfaces.json` at C 24–29, with `docs/porcelain.json` owning response/capture structure. I had not located or read the golden bodies and could not confidently reproduce an exact expected shape.
- **Open — complete producer-control procedures.** C 430–432 describes collection and candidate writing but does not identify a particular control command or full procedure. I could understand the review responsibility, but could not confidently run the complete shape-collection workflow from this passage alone.

### Journal §52

- **Open — formatting and derivation of `build.describe`, `build.commit`, `build.version`, and `build.number`.** C 438–441 names them and makes their descriptive role clear, without defining their formats or calculation. This did not obstruct exact admission using `build.contract`; it did prevent me confidently generating those four values or assigning a stronger provenance meaning to their spelling.

## 3. Carried terms

These are the meanings I used to continue reading, including names whose operational role became clear before their detailed representation did. First encounters below are within the contract; some concepts were already familiar from the prior guidance. “Not fully explained” records the limit of the meaning I carried, not a claim that the term has no definition elsewhere. Ordinary technical knowledge is distinguished from repository-specific background.

### Public objects, execution roles, and input terms

| Term or reference | First contract encounter; later explanation | Meaning I carried, and where it came from |
| --- | --- | --- |
| Saved specimen; asserted `contract`; exact admission | C 3–6; request form and gate at C 63–98 (Journal §§1, 6–9) | A persisted test/request description with an explicit identity assertion, admitted before its requested work is interpreted. The contract supplied identity exactness. Root AGENTS had already used “specimen” as the unit receiving fresh execution processes. I did not yet have a complete specimen grammar. |
| Envelope; producer; host reply; client capture | C 3–5; envelope fields at C 147, host fields at C 159, capture separation at C 249, binary production path at C 304–311 (Journal §§1, 16, 18, 30, 38) | Separately attributable records surrounding or containing execution observations. I used the ordinary software meaning of a wrapper/producer and kept the objects distinct. I did not assume that every on-wire object was JSON before reaching the binary-transport section. |
| Release identity; development identity; `unbound`; `PWContract` | C 8–15; request equality at C 63 and complete build stamp at C 438–441 (Journal §§2, 6, 52) | Build-produced labels rather than negotiable feature versions; `PWContract` was the app/service reporting name. Git tags and hashes were familiar technical concepts. The contract never specified the storage location/type of that app/service property beyond its reporting role. |
| Describe and commit; later version and number | C 15; full field names at C 438–441 (Journal §§2, 52) | Descriptive build metadata. General Git knowledge suggested what “describe” and “commit” might refer to, but I did not promote that expectation into a specified derivation or an admission rule. Version/number likewise remained descriptive fields with unknown generation rules. |
| External runner; installed/bundled runner | C 20; selection at C 63 and 77–85, execution/install checks at C 296 (Journal §§3, 6, 8, 36) | A selectable service capable of running a specimen, with installation lifecycle distinct from a single invocation. Root AGENTS had already introduced BYOXPC, launchctl, service name/scope/bundle path, and cleanup ownership. The contract supplied the identity requirements, not that background vocabulary. |
| Host, worker, controller, helper, client, validator | Host at C 4; client allowance at C 27–28; controller/helper names at C 39; worker/validator explicitly at C 87–88. Roles emerge at C 77–98, 147–159, 176–181, 304–339, and 382–414 (Journal §§1, 4, 8–9, 16–21, 38–48) | I kept front-end request handling, XPC hosting, sandboxed work, query validation, and capture distinct. The host/worker division was already supplied by root AGENTS, including keeping sandbox API calls out of the host. The contract was not my first source for that separation. Exact boundaries for every helper/validator were not fully enumerated. |
| Runner selector, aliases, required entitlements | C 63; precedence and preprocessing at C 77–85; actor checks at C 191–193 (Journal §§6–8, 23) | Instructions for choosing an execution service, with nested/top-level aliases referring to alternative locations for selection input. Entitlements were familiar macOS metadata; I initially carried that general meaning, then added the contract's boolean-true per-actor criterion. The selector vocabulary remained deferred to the named controller reference. |
| `Codable`, `CodingKeys`, `_test_overrides`, equipment override map | C 67–75 (Journal §7); no complete override grammar later | `Codable`/`CodingKeys` carried their ordinary Swift decoding/key-selection meaning. `_test_overrides` and the actor map were recognized as request objects used for explicit instrumentation; I did not invent their fields or defaults. Later `unverified_fixture` evidence at C 188–190 constrained override attribution. |
| Phases, actors, `after_termination` | Surface label at C 37; request mentions at C 69–75 and 91–94; execution at C 141; detailed dependencies at C 212–236 and 281 (Journal §§4, 7, 9, 15, 26–28, 34) | Named process participants visited by ordered phases; `after_termination` suggested a dependency on another actor's ending. Root AGENTS had already said one fresh worker per actor. I carried no complete overlap rule, and learned the final-visit and owned-reap restrictions later. |
| Policy, SBPL, parameters | Surface label at C 43; string parameter dictionary at C 72–74; policy summary at C 129 (Journal §§4, 7, 13) | Sandbox policy source with caller-supplied string substitutions/parameters. The sandbox-policy sense of SBPL came from general macOS familiarity and the repository's sandbox context; the contract never teaches its language syntax or expands the acronym. I did not infer exact substitution semantics beyond the stated parameter type. |
| Augments and named fragments | Surface label at C 43; preprocessing at C 78–85; in-memory behavior at C 129 (Journal §§4, 8, 13) | Named pieces inserted into policy source before submission. That working meaning came from “splices” in the contract. Catalog, content, and ordering stayed unknown; “in memory” prevented me treating augmentation as a required disk rewrite. |
| Imports, closure, held policy input | Imports label at C 43; held input/closure at C 129; common held submission/fallback input at C 153 (Journal §§4, 13, 17) | A policy and the imported material needed to describe its input. “Closure” used the ordinary dependency-closure idea; I did not assume particular resolution paths. “Held” meant stable for the admitted submission, with its post-admission consequence supplied at C 153, not a particular copying mechanism. |
| Probe, sandbox query, attempt, filter, operation | Probe surface at C 44; request objects at C 69–70; constraints at C 87–98; probe summary at C 135 (Journal §§4, 7, 9, 14) | A query observation paired with an attempted operation. General query/filter terminology supplied the initial meaning. Root AGENTS had already warned that predictions precede attempts and are not enforcement agreement; the contract independently stated the query/attempt separation and permitted scope mismatch. |
| `exec/spawn`, `none`, `sandbox_check`, `prediction_unavailable`, `unsupported_operation`, `open_write` | C 89–98; `open_write` at C 135 (Journal §§9, 14) | Literal operation/filter/result names. Familiar process, filesystem, and sandbox API vocabulary helped me read them. The contract explained argument eligibility, absence of prediction, unsupported OS queries, and truncating open, but not the complete operation/action catalog. I did not carry successful-return guarantees. |
| Compiled-profile capture, receipt, nonce, worker binding, stage | Profile label at C 45; nonce/capture prerequisites at C 90–91; receipt at C 243; bytecode presentation at C 347–350 (Journal §§4, 9, 29, 43) | Captured compiled policy material with a receipt tied to this request and worker. “Nonce” suggested a request-associated value from general protocol usage; I did not assume a randomness, length, or encoding rule. Receipt context and consistency were explained later, but allowed stages/statuses and full validation remained unknown. |
| Dossier, provenance, inventory, fallback compiler | Dossier label at C 38; details at C 153 (Journal §§4, 17) | A record of the input and execution context, including observed binaries, rather than a second execution result. “Fallback compiler” meant an alternate compilation path using the same held input; its trigger and implementation were never supplied. General provenance terminology helped, but did not establish inventory completeness. |

### Evidence, ownership, and lifecycle terms

| Term or reference | First contract encounter; later explanation | Meaning I carried, and where it came from |
| --- | --- | --- |
| Comparison, enforcement agreement, permission-shaped failure | Comparison label at C 48; prediction limitation at C 135; comparison/causation rule at C 159 (Journal §§4, 14, 18) | Relating query and attempt observations without treating permission-like failure as proof of sandbox cause. Root AGENTS had already stated the attribution restriction. I used ordinary permission-error knowledge, not an assumed list of sandbox-denial errno values. |
| `query_first`, collection/release evidence chain, barrier | `query_first` and chain at C 159; release restrictions at C 230–236 and 411–414 (Journal §§18, 28, 48) | An ordering claim needing collected prediction evidence and authorization to release attempts. Root AGENTS explicitly supplied “predictions precede attempts” and the collection/release barrier before this reading. The contract never supplied the complete chain, so the process model I used to keep reading was partly guidance-derived. |
| Disposition, lifecycle, native progress, effect witness | Surface label at C 42; substantive rule at C 165; application/reap cases at C 204–236 (Journal §§4, 19, 25–28) | A claim about what actually happened, supported by native observations rather than merely a successful request or return. Root AGENTS supplied “witness over interpretation” and `rc == 0` insufficiency. The contract supplied concrete limits but not every disposition's meaning. |
| Fresh process; one application per actor | C 141 (Journal §15) | No reuse of an already sandboxed process and one policy application for an actor. Root AGENTS had already explained the one-way sandbox constraint and fresh host per specimen/fresh worker per actor. I did not derive the additional fresh-host rule solely from C 141's statement about sandboxed processes. |
| Extension transfer, consumption, owned records; later extension custody | C 141; custody validation at C 354 (Journal §§15, 43) | Transfer/use of sandbox-extension authority with explicit ownership evidence. The sandbox-extension meaning came from general macOS knowledge and the policy context, not a definition in the contract. I did not know the complete token/handle transfer protocol. |
| Token, delivery, handle names | C 320–321 (Journal §39); no later operational definition | Caller-chosen names with associations checked semantically. The nearby extension-custody language suggested why such names might matter, but I did not assume that every such name belonged to a particular extension operation or infer its lifetime rules. |
| Service-sealed equipment; equipment hash | C 171; inventory/bindings at C 183–193 (Journal §§20, 22–23) | Execution equipment associated with a selected service and checked for identity before its claims are used. I did not equate “sealed” with a specified signing or cryptographic procedure. The exact seal and hash scope stayed unknown. |
| Worker ABI identity | C 171; exact source identity at C 382–404; header/reporting at C 406–414; limits at C 416–425 (Journal §§20, 46–50) | Initially an internal compatibility identity distinct from the public build identity. “ABI” carried its ordinary interface/layout association; root AGENTS had mentioned protocol/layout changes and worker-identity regeneration. The later contract made clear that this identity is a source hash and does not itself prove compiled layout agreement. I had not previously claimed that it did. |
| Declaration reply; singular worker projection | C 176; no complete object definition (Journal §21) | Forms of summary/flattened response that actor execution does not produce. I used the negative statement and the following `actors[]` ownership rule, without inventing the contents of either excluded form. |
| `authority_setup.host`, run/region/custody scopes; `.workers` cells | C 178–180 (Journal §21); no full definitions later | Separately owned records of setup, cleanup, and native-capability observations. General shared-state terminology let me read “cell” as an independently published evidence unit. I did not know the complete scope boundaries or state machine. |
| Acquired decision; native-capability observations | C 180–181 (Journal §21); not fully explained | A decision or observation within setup evidence. I carried only the stated restriction that one decision does not publish another cell. I did not assign a specific acquisition operation or native capability to the term. |
| Publication; published facts | First explicit cell use at C 180–181; application publication at C 207–210; registry publication at C 297; publishable observations at C 355; shared header at C 406–414 (Journal §§21, 25, 37, 43, 48) | Making a record/fact available in the relevant channel. For workers, later memory-interface language made shared-region publication plausible; root AGENTS had already mentioned wait/release stores. Registry publication meant verified persistent replacement. I did not assume those different uses had one common atomicity or durability rule. |
| Equipment inventory, bindings, `role`, `source`, positional references | C 183–190 (Journal §22) | An inventory with association rows indexed by zero-based references. The index rules were explicit immediately; actual role/source vocabularies and complete rows were not. I did not invent equipment roles from the generic term “worker.” |
| Instrumented override; `unverified_fixture` | C 188–190 (Journal §22) | Explicitly substituted instrumentation that cannot establish packaged selection. “Fixture” had its ordinary test-material meaning; the contract supplied the evidentiary restriction rather than a complete instrumentation procedure. |
| Static/live XML entitlement read-back | C 191–193 (Journal §§22–23) | Entitlement observations associated with selected equipment and the live execution context. General macOS/XML knowledge helped me distinguish static material from live observation. The contract did not specify the association APIs or make one read-back stand in for the other. |
| Runtime inspection; activation; cancellation | C 194–196; activation observations and stored activation at C 214–236 (Journal §§23, 26–28) | Inspection capable of preventing scheduled actor work, with activation representing permission/state to proceed. I did not know the full inspection set. Later text distinguished stored activation from obtaining a timestamp after that store. |
| `preparation_failure` | C 196; allowed categories and result at C 198–202 (Journal §§23–24) | Initially a named before-launch failure class, then the two explicitly admitted category pairs with `runner_failed`, `rc: 1`, empty observations, and no launched actors. It was explained before I needed to interpret a later instance. |
| Complete observation partition | C 202 (Journal §24); never fully defined | A normal requirement to account for declarative phase/action identities through observations, with a special preparation-failure exception. “Partition” supplied an accounting sense from general technical vocabulary; I did not infer that every declared action executed or know every member of the partition. |
| Application assessment; state/basis; eligible terminal worker branch | Application assessment at C 177; distinctions at C 204–210 (Journal §§21, 25) | Whether policy application was requested, attempted, and observed, with a reason/evidence basis. Root guidance's “specimen application” and the actor policy sentence at C 141 helped distinguish this from application software. The eligible-branch set remained unknown. |
| `done`, `ready`, `applied`; auxiliary reporting failure | `done` and reporting failure at C 209–210; ready/applied/done publication at C 409–414 (Journal §§25, 48) | Worker progress/reporting labels. I used the explicit warning that `done` or reporting failure alone cannot prove application nonattempt; later I learned these can be absent after bootstrap mismatch. I did not reconstruct the entire progress protocol. |
| Reap; owned reap; natural/abnormal/cleanup-only reap | Reap at C 165; owned evidence at C 212–228 (Journal §§19, 26–27) | A native child-termination observation/collection, distinct from requesting exit. General process/wait knowledge supplied “reap”; the contract supplied ownership and ordering requirements and the acceptance of abnormal natural termination. |
| Capture stage, `capture_ordinal`, `observed_ns` | C 213–216; matching/order/time requirements at C 217–236 (Journal §§26–28) | A stage label, source-local ordering value, and optional time observation. I read `_ns` as nanosecond-style naming from general convention, without inferring an epoch or clock implementation. The stage vocabulary stayed unknown; ordinal locality was explicitly explained. |
| Termination gate, gate closure, source final activation/visit | Gate at C 217–220; satisfaction at C 220–228; source final-visit request constraint at C 281 (Journal §§26–28, 34) | A dependency checkpoint preventing activation until specified source-ending evidence exists. “Closure” meant the gate decision/completion in this context, not the policy-import closure. The final-visit condition became concrete in the refusal table. |
| Ownership/departure flags, prior host departure request | C 213 and 222 (Journal §§26–27) | Evidence distinguishing an actor's owned natural ending from a host-requested departure or cleanup outcome. The contract gave conditions, not the full flag state machine. General process knowledge alone did not fill that gap. |
| Owned endings | C 354 (Journal §43); no separate full definition | A semantic-validation category related to observed, owned termination. I connected it to the owned-reap material already read, without assuming that the two phrases had exactly the same full domain. |

### Transport, maintenance, and references

| Term or reference | First contract encounter; later explanation | Meaning I carried, and where it came from |
| --- | --- | --- |
| Surface; surface stamp; delimited normative region; canonical shape golden | C 17–18 and 24–32; public-key/type description at C 430–434 (Journal §§3–5, 51) | Named portions of the contract and tracked expected structures whose changes guide review. General testing usage supplied “golden” as a reference artifact. Root/docs AGENTS had already introduced generator inputs, generated regions, manifests, and shape goldens. Canonical meant a stable hashing representation; its exact normalization was not explained. |
| `contract_surfaces.json`; transport/installation goldens | C 24–29 (Journal §4); fuller role, not contents, at C 430–434 | The scope manifest and reference shapes behind the stamp system. I did not open the manifest or infer exact paths/content for every golden from its name. |
| “The two tables”; stamp `--check`; release preflight | C 52–56; command owner at C 366–370 (Journal §§5, 44) | Two compared representations in the stamp workflow; the second location remained unknown. I carried `--check` as a mode of the unnamed stamp generator until the command was supplied. “Preflight” meant release preparation checks, with no assumed complete command sequence. Root guidance had already introduced release/build checks. |
| Reservation; reservation limits; overall client allowance; uncertain invocation | Allowances at C 27–28; reservation/replay rule at C 249; registry/live checks at C 296; public admission timing at C 345 (Journal §§4, 30, 36, 42) | A pre-execution admission/resource step distinct from specimen submission. “Uncertain invocation” meant insufficient confidence about whether invocation happened or its outcome; it did not imply a specific retry-safe state. The full exchange remained unknown. |
| `bad_request`, bounded path, `expected_contract`, `request_failure` | `bad_request`/path at C 71; `expected_contract` at C 255; field at C 261–277 (Journal §§7, 31–34) | A structured refusal classification and location diagnostic. I used them as labels before their full record was supplied; C 266–277 then settled the path limits and common code categories. I did not treat supplementary `error` prose as a machine protocol. |
| Old `schema_version` specimen | C 255 (Journal §31); no historical schema definition | A legacy field illustrating why the missing current contract assertion wins. I did not infer the old version's accepted values, format, or compatibility. |
| Native-string admission | C 284 (Journal §34); no concrete rule later | Admission restrictions related to strings entering native interfaces. That general meaning came from ordinary systems-programming vocabulary. I did not assume a specific NUL, encoding, or length rule beyond the stated diagnostic information; limits were deferred. |
| Registry, pending cleanup, ownership, observed absence | Registry at C 249; installation/cleanup at C 296–297 (Journal §§30, 36–37) | Persistent installation/cleanup records whose availability does not prove execution compatibility or removal authority. Root AGENTS had supplied runner list/reconcile, durable pending-cleanup ownership, and the warning that a label prefix alone is not ownership. The contract did not supply the full cleanup rule. |
| Opaque metadata, lossless read-back, atomic replacement, retired kind aliases | C 297 (Journal §37) | Preserve unrecognized values across unrelated writes and verify a replacement before publishing it. Ordinary persistence terminology supplied the working meaning. The retired alias set and exact failure result stayed unknown; I did not infer ownership from successful persistence. |
| `porcelain.json`, `generate_porcelain.py`, projection | C 304–311; presentation at C 347–355; maintenance command at C 362–364 (Journal §§38, 43–44) | The schema owner, generator, and conversion from typed records to public JSON. I did not attach Git's unrelated porcelain-command meaning to the schema filename. Roles were explicit; contents were not read. Root/docs guidance had already made generated-copy ownership familiar. |
| Validator NDJSON and its marker/contract | C 309; independence at C 372–373 and 424–425 (Journal §§38, 45, 50) | Newline-delimited JSON from general format knowledge, with a producer-specific boundary. The marker value and exact validation rules were never supplied. I did not conflate this validator stream with all the semantic validators later named at C 353–355. |
| `PWP1`, wire identity, frame, root value, record/field/case tags, variant | Binary fingerprint first at C 249; wire grammar at C 313–325; coverage at C 341–345 (Journal §§30, 39, 42) | A typed binary frame with a structural identity and tagged values. Ordinary serialization vocabulary let me follow framing before knowing tag numbers. `PWP1` was a fixed frame marker, not a public compatibility permission. Primitive encodings and actual tags remained deferred. |
| Primitive reader, logical-storage budget, decoded collection slots | C 330–334 (Journal §40) | A decoder accounting for logical objects/contents under a per-frame budget. I did not equate it with allocator use or physical peak memory. The source link identified a route to exact accounting but was not opened. |
| Frame limit, smaller reply allowance, controller retention cap | Allowance labels at C 27–28; their different collection boundaries at C 334–339 (Journal §§4, 41) | Different limits at different stages. The later passage required me to keep accepted writer size, client truncation, and post-collection controller retention separate; I had not assumed they were one shared cap. |
| Fresh-read content; code directory hash | C 349–350 (Journal §43); no full operational definition | Fresh-read content suggested bytes observed by a read operation; the contract specified their hex presentation, not the operation's complete semantics. Code directory hash had its familiar Apple code-signing association from general knowledge, without an inferred authenticity guarantee. |
| Named validators | C 353–355 (Journal §43); no names or complete rules later | Separate semantic checks for the listed domains, beyond the frame reader. I did not assume that the shared schema generated their full behavior or that they were identical to the OS-query validator of C 97–98. |
| Infrastructure format markers; independently inspected candidate; constructed response context | C 372–377 (Journal §45) | Separate format roles and explicit test provenance. The candidate was the build whose identity the harness asserts, not an identity guessed from a template. Inspection mechanics and most marker definitions remained unknown. |
| `pw-probe-runner`, worker source identity, worker ABI ordinal | C 382–385 (Journal §46); source scope at C 392–404, bootstrap at C 406–414 | The bundle-local worker binary and its exact source hash. An ABI ordinal meant an earlier numbered compatibility identifier from ordinary protocol terminology; no old ordinal history or translation was assumed. The named binary's complete implementation was not read. |
| `generate_worker_identity.py`, shared walker, identity-region bodies | C 384 and 392–396 (Journal §§46–47) | Named generation machinery; excluded generated bodies prevent self-reference. The role was clear without reading the source; byte framing remained deferred. |
| Worker/shim, host mirror, selected SDK/developer directory, Ninja dependency log | C 399–403 (Journal §47); source-equality limitations at C 416–420 | Familiar native-build concepts. “Shim” suggested interface glue and “host mirror” corresponding host-side declarations, but neither was mapped to a complete file/interface definition. I did not equate permitted compiler inputs with hashed SDK contents. Root guidance had already introduced SDK/compiler and C/Swift layout concerns. |
| Bootstrap magic, mapped shared region/header, ordinal-era worker | C 406–414 (Journal §48) | A stable initial recognition area allowing checks before layout-dependent reads. General memory-interface knowledge supplied the bootstrap idea; the contract supplied byte positions, mismatch behavior, and host-selected reporting. It did not specify every size-failure result. |
| Compiled layout checks, signed artifact provenance, lifecycle/order tests | C 418–420 (Journal §49) | Separate forms of evidence for layout, artifact origin, and behavior/order. Root AGENTS had already mentioned signing/provenance and order-barrier controls. I did not treat their mention as having inspected them or as a guarantee conveyed by the source hash. |
| Producer controls; golden candidate; version-bump classifier | C 430–434 (Journal §51) | A shape-collection workflow producing a review candidate, without a separate version-bump decision mechanism. Testing vocabulary supplied “control” and “candidate”; exact procedures were not given or run. |

The named external reading routes also remained part of the carried context: `controller/README.md#runner-selection-external-entitlements` at C 77 for selectors; `docs/LIMITS.md` at C 108, 193, 226, and 336 for limits; `docs/REQUEST-GRAMMAR.md` at C 121 for worked specimens; `controller/src/porcelain.rs` at C 330 for the primitive reader; and `docs/BUILD.md#one-build-in-time` at C 389–390 for check/signature sequencing. Their stated roles let me continue without their contents. The root/docs guidance had already made the controller/build/limits references familiar; the contract itself supplied these particular referrals. None was opened.

I also relied on ordinary technical meanings that the contract does not teach: Git annotated tags, clean/dirty trees, blobs and index flags; SHA-256 and digest bytes; Cargo, SwiftPM, Meson and Ninja as build tools; XPC and launchd as macOS service mechanisms; Swift `Codable`; JSON, NDJSON, XML, UTF-8, null, arrays, dictionaries and zero-based indexes; base64 and hexadecimal; signedness, native width, byte order, PID, return code, wait status, monotonic time, SDK, and ABI. I did not experience each as a new repository term. Where their repository-specific use needed more than the ordinary meaning—especially source scope, entitlement comparison, wait ownership, and identity admission—I retained the contract's qualifications rather than importing a more specific rule from general knowledge.

## 4. Going back

I did not reopen or redisplay an earlier contract passage to understand a later one during the original reading. The five original read windows were forward-only and did not overlap. I did not follow a cross-reference and then return. The rereading for this close-out is a separate activity described in part 1.

I did keep earlier text active in the conversation context and use it when writing later entries. Earlier line citations in the journal record those connections, not additional file visits. The following are the backward connections visible in the journal, grouped by the earlier material being reused. They describe the work of reconciling meanings without inventing a count of mental rereads.

| Earlier passage retained | Later journal entries and what made it relevant again |
| --- | --- |
| C 3–6, exact independent admission | §§2–3 used it to interpret build labels and external-runner replacement; §16 applied it to nested envelopes; §20 kept ABI identity separate; §37 distinguished historical record preservation from public-contract admission. |
| C 8–15, compiled identity versus provenance | §4 kept stamps separate from running identity; §18 kept reply describe/commit separate from admission; §42 did not transfer fingerprint exclusions to build identity; §52 reconciled the final build-stamp paragraph with the opening release conditions. |
| C 17–20, manual reuse and no specimen rewriting | §10 related all-source-change acceptance to author review; §13 related in-memory augmentation to no disk rewrite; §36 related installation gates to external-runner reinstallation. |
| C 24–32, stamp role and hashing | §10 used the navigation/admission distinction when explaining required author review. |
| C 52–56, limited stamp checking without history | §44 recognized the later generator command as the owner of the earlier flags and the same historical limitation. |
| C 63, request gate before later processing | §7 placed field checks after identity; §14 used the gate to understand prevention of truncating `open_write`; §§31 and 34 connected missing/type/unsupported diagnostics to the gate; §45 distinguished unasserted templates from submitted specimens. |
| C 77–85, preprocessing and per-actor entitlements | §13 connected the policy summary to controller-side augmentation; §23 connected live entitlement evaluation to the earlier per-actor host check. |
| C 87–98, meaning checks and separate query/attempt scope | §14 interpreted the probe summary; §18 limited comparison claims; §29 recalled capture/nonce prerequisites; §35 refined the admission-timing picture with capacity-first ordering and the host-launch allowance. |
| C 100–114, identity changes and capacity | §11 related capacity changes to author acceptance; §32 did not mistake optional diagnostics for an identity exception; §35 related refusal observations to the earlier before-attempt capacity promise. |
| C 129, held policy input | §17 used it when the dossier supplied common held submission/fallback input and the post-admission edit example. |
| C 135, predictions do not establish agreement | §18 used it alongside the query/attempt scope rule to interpret comparisons and permission-shaped failures. |
| C 147, independently admitted envelopes and retained bytes | §30 recognized the same separation for capture/host frames; §45 related historical byte retention to withheld claims; §50 preserved external admission independently of the internal memory identity. |
| C 159, host reply and `query_first` requirements | §19 connected lifecycle evidence limits to comparison limits; §29 required admitted host context for a receipt; §30 applied independent admission to embedded frames; §48 noted that bootstrap identity checks still did not supply the complete ordering chain; §50 preserved the external reply boundary. |
| C 165, unknown/contradictory observations and dependent claims | §25 applied that distinction to unobserved application; §43 recognized that conflicting observations can still be published without their dependent claims. |
| C 171, actor/equipment binding and separate ABI identity | §22 gave the binding concrete rows/references; §23 added entitlement evaluation; §46 returned to the distinction when the internal source identity was finally explained. |
| C 183–187, positional equipment references | §39 recognized their binary encoding as unsigned indexes into the named table. |
| C 194–196, runtime failure is not preparation failure and retained facts survive | §24 used it to constrain the prelaunch category; §25 retained the difference between absent evidence and proved nonattempt. |
| C 217–220, gate observations and matching ordinals | §27 added the further conditions for satisfaction instead of treating a matching ordinal as sufficient. |
| C 228, cleanup-only reap cannot substitute | §28 used it to understand why a later cleanup reap does not repair a reached failed gate. |
| C 249, capture/peer admission and structural fingerprint | §36 connected live-peer checks with registry/install checks; §38 connected the fingerprint to typed production ingestion; §42 distinguished exact structural identity from public admission; §50 kept those external boundaries independent of host/worker identity. |
| C 255 and 266–267, contract failures and expected identity | §34 combined these fields with the refusal-code table and the original request gate. |
| C 296, compatibility and ownership limits | §37 separated lossless registry publication from authorization to execute or claim ownership. |
| C 313, fingerprint in the frame | §42 connected the fingerprint's exact coverage to its previously described wire position and structural role. |
| C 352–355, structure versus semantic claims | §51 understood the later shape-golden workflow as leaving semantic admission intact. |
| C 372–373, separate infrastructure identities | §46 recognized the internal worker identity as one member of the earlier list, not a replacement for every marker. |
| C 382–414, source scope and identity checks | §49 limited what equality and bootstrap checking establish once the explicit non-authentication and non-layout guarantees appeared. |

The reading cost represented here was maintaining several distinctions at once: public identity versus structural fingerprint versus worker source identity; request intention versus observed execution; absent evidence versus observed nonattempt; and evidence publication versus permission to draw a dependent claim. I did not resolve that cost by opening implementation or another explanatory document.

## 5. Changes of mind

I have no withdrawn affirmative belief to report. By the end, I still held the journal's affirmative claims with the qualifications recorded in their entries. Later passages supplied specifics or resolved a reserved question; I did not discover that I had to replace an earlier claim with its opposite. I have not constructed an earlier, stronger belief merely to give this section a reversal.

The following are the closest changes in the specificity of my understanding. Each gives the earlier recorded position, the later one, and the passage responsible. They are refinements, not corrections to the accepted journal.

| Journal entry | Earlier recorded belief | Understanding by the end | Passage supplying the refinement |
| --- | --- | --- | --- |
| §§6 and 9 | Identity gates precede selectors/helpers/children; unknown attempt pairs and filters are rejected before workers or validators are created. | The specified early gates remain. Request-refusal output has no step/child observations, while the XPC host itself may have launched to decode. I distinguished host startup from the child/attempt activity being refused. I had not recorded a blanket claim that no host could exist. | C 286–288, recorded in §35. |
| §11 | Runtime capacity is distinct from syntax/meaning, can refuse a valid plan, and does not truncate it. | I additionally knew the ordering: capacity checks precede meaning checks, and the result identifies one refusal. “Separate” had not previously specified a chronological order. | C 287–288, recorded in §35. |
| §18 | `query_first` needs a collection/release evidence chain; the precise chain and incomplete-chain result were uncertain. | I could withhold the claim when its supporting observations were missing or contradictory, while still not reconstructing the complete chain or its projected value. This resolved the consequence more than the mechanism. | C 165 and 351–355, recorded in §§19 and 43; C 230–236 and 411–414 added particular release restrictions without supplying the whole chain. |
| §20 | Worker ABI identity is separate from public build identity; its representation was still unknown. | It is an exact SHA-256 source identity with defined input scope and header position. The reported ABI field is host-selected and is not evidence that a child validated the header. Equality has the expressly limited source-agreement meaning. I had not previously claimed authentication, layout proof, or child acknowledgement. | C 382–420, recorded in §§46–49. |
| §26 | A nonnull gate observation needs a positive matching source reap ordinal and later gate capture; ordinal locality rules out a global ordering interpretation. Whether that suffices was left unsettled. | Matching is necessary but insufficient: satisfaction also needs the specified activation/reap/closure order, consistent native facts, ownership, timestamps, usable clock, successful wait, and allowance. | C 220–236, recorded in §§27–28. |
| §30 | Capture and host frame have separate admission; an uncertain invocation does not authorize replay; the full handshake was unknown. | I additionally knew that public build-contract admission occurs during reservation before execution. The full handshake and positive retry rule remained unknown. | C 345, recorded in §42. |
| §46 | The host/worker pair uses generated exact source identity, checked before compilation/signing, with input scope and runtime handshake not yet described. | I could name the covered files/discovery rules and the header checks, mismatch behavior, and reporting limitation. The hash still did not authenticate behavior or artifacts. | C 392–420, recorded in §§47–49. |

Several apparent contrasts did **not** change my mind: accepting historical flattened registry records at C 297 did not weaken public identity admission; optional diagnostic information at C 263–264 did not create additive compatibility; matching source bytes at C 416 did not become compiled-layout or authenticity proof; and an `observed` application state at C 207–208 did not become a success claim. The journal already kept those boundaries or expressly reserved the unanswered point. No entry has been edited to incorporate the later material.


# Answers

“C” continues to identify lines of `docs/CONTRACT.md`; journal section numbers refer to the accepted journal. Neither that journal nor the preceding Close-out is revised by these answers.

For this task I first searched the two accepted artifacts for the three named entries and related terms. I then reread C 198–244 and 379–425, followed by C 1–197, 245–378, and 426–441. Collectively that covered all 441 contract lines. The per-answer search accounts below identify which passages did the work within that shared reread; they do not claim that I opened only those passages. No linked document, implementation, test, or other repository file was opened. “Remembered” identifies a belief already present in the first journal, now also reinforced by the close-out; it does not claim an uncontaminated memory experiment. Applications to the new situations are identified as reasoning done now.

## 1. Direct source-test builds and identity regeneration

**Answer.** I understood the updated C, Swift, and test identity copies to be produced by `docs/generate_worker_identity.py`, invoked through the given `tests/lib/python.sh` command after an input edit. My mental sequence was regeneration followed by compilation using the regenerated copies. I did not mean that an ordinary freshness check silently rewrites them: I explicitly understood those checks to be nonwriting.

I had not settled who invokes the generator on the direct source-test path. “Direct source-test builds regenerate the same way” made me expect that path to use the same regeneration mechanism, but I had not distinguished a source-test build/setup command invoking it from the person preparing the build invoking it beforehand. I cannot now report that I had understood automatic regeneration at a particular hook. The text identifies the writer and the after-edit requirement; it delegates the detailed check/signature sequence to the build account. Before compilation consumes the copies is my inference about the required ordering, rather than a separately specified direct-build hook.

**Contract basis.** C 382–384 names the generator. C 385–388 says the build checks copies before compilation and before signing, never writes them, and gives the regeneration and nonwriting-check commands. C 389–390 says direct source-test builds regenerate the same way and assigns the detailed sequence to the build account.

**Reading and search.** The generator/check distinction was remembered from Journal §46. I returned directly to the internal-identity passage, displayed as C 379–425, with C 382–390 decisive. The later full-document reread supplied no more precise direct-build invoker. Recognizing that I had left that invoker unspecified is a clarification now, not a newly recalled automatic-build mechanism.

**Confidence.** High about which generator produces the copies and the nonwriting nature of checks. Moderate about the inferred before-consumption ordering. I did not have a definite belief about manual versus automatic invocation or its exact hook.

## 2. Who accepts a compiled-profile receipt, and when?

**Answer.** I meant the software reading and interpreting an arrived host reply and its receipt. My concrete picture was a controller-side response reader deciding whether the receipt could be used or presented as compiled-profile evidence. I was not referring to the worker accepting a request nonce before applying the policy, or to the host deciding whether to launch the worker.

The point was response interpretation: first establish the host reply's producer context, then assess the receipt before accepting its evidentiary content. That does not locate the check at a precise worker-lifecycle moment or say that all cleanup has finished. Nor had I assigned it to a named module or decided whether every outside consumer repeats it. “Controller-side reader” was my inference about the ordinary product path; the more general belief was that whoever accepts the receipt as evidence needs more than a matching producer identity.

**Contract basis.** C 243 says the receipt inherits its admitted host-reply context, requires consistency among its fields, and is refused for a wrong nonce even inside a current reply. C 159 places host admission before interpretation of reply contents. C 347–355 describes projection from typed records and semantic checking before claims. By contrast, C 90–91 concerns the earlier request's capture/nonce prerequisites.

**Reading and search.** The distinction between host admission and receipt consistency was remembered from Journal §29. The question about the accepting actor was more specific than the belief I had recorded. I reread C 240–244, then related it to C 147–159 and 347–355 during the shared full reread. Those passages support the response-reading stage without naming one definitive implementation component.

**Confidence.** High about the distinction between request admission and accepting returned receipt evidence. Moderate about the controller-side picture. Low confidence in any more precise allocation or lifecycle timing, which I had not established.

## 3. Which ordinals share a sequence in the A-to-phase-B dependency?

**Answer.** Let D be the actor active in dependent phase B. The reading I carried, extended to this example, is:

- A's activation observation and A's owned reap belong to A's process-associated observation sequence.
- The gate's `observation.capture_ordinal` is a reference to A's owned-reap ordinal, not a new event ordinal.
- I took the gate's own later `capture_ordinal` to be comparable with that A-owned reap. Combined with the final-activation rule, I understood an A-associated order of final activation, owned reap, then gate closure.
- B's activation observation belongs to the sequence for its active actor D. I did not take its ordinal to be numerically comparable with A's ordinals, or with the gate ordinal I had associated with A. The stated cross-actor time constraint is instead that a present dependent activation timestamp must not precede A's reap timestamp.

Thus I did not mean that all four event ordinals live in one global sequence. I also did not mean that A itself necessarily increments every A-associated capture ordinal: a process-associated observation sequence is not a statement about which process writes each observation.

The first journal explicitly records local scope and the later gate ordinal, but does not spell out B's assignment. That last assignment, and the explicit four-way mapping here, are my application of that reading now. The gate's association with A is an inference from the required comparison, not an independently enumerated counter definition in the text.

**Contract basis.** C 212–216 introduces reap/activation observations and says the ordinals are local to the source actor process. C 217–220 makes the gate observation reference that reap and requires a later gate capture ordinal. C 220–224 orders final activation, owned reap, and closure and requires source timestamps. C 230–234 separately discusses dependent activation and its timestamp. C 281 excludes a dependency on the phase's own active source actor and constrains the source's final visit.

**Reading and search.** I remembered Journal §26's local-versus-global distinction. I reread C 212–236 directly for this mapping, and checked the dependency restriction at C 281 during the full reread. I did not find another passage that explicitly enumerates the namespaces of all four ordinals. The detailed mapping is reasoning now, not a claim that I originally worked through this precise example.

**Confidence.** High that I did not read a global process counter and that the gate observation references A's reap. Moderate about the full mapping, especially assigning the gate's own counter to the A-associated sequence; I would not claim the prose separately specifies its storage or writer.

## 4. Binding text, machinery, maintainers, and Typed response transport

**Answer.** I took the opening identity/admission rules and the behavioral claims in the normative regions as product commitments. That includes their qualifications, negative guarantees, refusal examples, and evidence requirements. Explanations of generators, hashing, shared records, and readers describe machinery, but their concrete assertions about what readers reject or what a build checks also led me to expect that behavior.

Instructions such as edit the schema, regenerate, review goldens, and prepare a release table address maintainers. I did not read that change in audience as making surrounding behavioral statements optional. The internal host/worker section, although outside the earlier surface regions, also states concrete behavior I expected the product to exhibit.

Because I read raw Markdown, the `BEGIN CONTRACT ...` and matching `END CONTRACT ...` comments gave me the most concrete boundary for a delimited surface region. Heading level alone did not: the request and equipment regions themselves contain additional headings. A closing marker ends that region; I did not take it to end all binding claims in the rest of the document.

I took C 300–358 to be normative transport material in its own `transport_encoding` region, elaborating typed response/capture transport. It is not inside the installation region, which ends at C 298, and its explicit structural rejection and projection rules were promises I relied on. I associated it substantively with the `transport` surface. I did not establish exactly how the manifest maps the differently named `transport_encoding` region to a stamp-table row; the document says the manifest owns that scope, and I did not open it.

**Contract basis.** C 3–20 gives the opening obligations. C 24–32 assigns scope to the manifest and describes hashing delimited normative regions. C 58–63 and the paired markers through C 298 identify the surface regions. C 300 and 358 delimit `transport_encoding`; C 328–355 contains its reader and projection requirements. C 360–370 and 430–434 address maintenance. C 382–420 gives internal identity behavior and limitations outside those earlier regions.

**Reading and search.** I remembered treating transport as substantive in Journal §§38–43 and maintenance separately in §§44 and 51. The question about exactly which stamped surface owns `transport_encoding` required a fresh look at the markers and table. I used the full-document reread, especially C 22–58, the region boundaries through C 358, and the later headings. I did not consult the manifest.

**Confidence.** High about the visible region boundaries, the product commitments I took from transport, and the maintenance audience. Moderate about mapping `transport_encoding` to the `transport` stamp; that association was an inference, not a checked manifest fact.

## 5. Reusing release X when Y's probes stamp predates X

**Answer.** Before changing the assertion, I would inspect Y's surface rows changed since X, revisit the corresponding definitions, and decide whether the specimen still expresses the intended request under Y. Relevant changes may be in request admission, policy, equipment, transport, or another surface even if `probes` has no newer stamp. I would then deliberately change the specimen to assert Y's exact contract. If using an external runner, I would follow the stated reinstallation requirement when the app contract changes.

I would read the older `probes` stamp as saying that no newer change to that tracked surface's normative region/shape has been recorded since before X. It gives me no flagged probe-surface change to review in that interval. I would continue to rely on the unchanged described probe semantics, subject to the rest of Y's contract.

I would not conclude that probe implementation bytes, all interacting surfaces, or observed sandbox results must be identical between X and Y. The stamps are navigation aids, implementation fixes still require identity acceptance, and observations are not promised identical across builds or macOS versions. An unchanged probe row does not make X's assertion admissible to Y.

**Contract basis.** C 17–20 supplies review, manual assertion changes, and external-runner reinstallation. C 24–32 defines what stamps track and denies them an admission role. C 100–106 includes implementation fixes in required build-identity review. C 116–119 limits cross-build/OS observation guarantees. C 63 still requires exact request identity.

**Reading and search.** The review procedure and stamp/admission distinction were remembered from Journal §§3–4 and 10–12. Applying them to a probes row older than X is reasoning now. Within the shared full reread I used C 17–32, 63, and 100–119; no additional source was needed.

**Confidence.** High about the required manual acceptance and the lack of an identical-observation guarantee. High about reading the table as a report of tracked last change, while not treating it as an independent implementation comparison.

## 6. What “verified examples” meant to me

**Answer.** I took it to indicate that maintainers are expected to keep examples supported by verification and aligned with the normative definitions and shape goldens. For an individual “Example:” sentence, I therefore read its stated behavior as an intended, concrete contract assertion, not as a speculative scenario. The expectation that each such example has supporting verification was an inference from the maintenance language, not something I established by tracing a particular test.

Yes: for understanding the product or writing a caller against the stated conditions, I would rely on the behavior an example explicitly describes without personally running a check first. For example, I would rely on the foreign-contract gate preventing the truncating operation described at C 135. That is reliance on the contract, not a claim that I have verified the installed artifact.

The word does not tell me the exact test, date, platform, release artifact, or breadth of verification for any particular sentence. I would not turn it into an assertion that I know every “Example:” was exercised end to end in a particular release, or that an observation will reproduce on every macOS version.

**Contract basis.** C 103–105 and 362–365 require normative definitions, verified examples, and goldens to stay current; C 430–434 repeats the definition/example maintenance relationship. C 121–122 relates the named developer lesson to particular decoding/validation and signed controls, but does not map every “Example:” sentence to a control. C 63 and 135 support the example of preventing truncation. C 118–119 limits identical-observation expectations.

**Reading and search.** I remembered the maintenance responsibility recorded in Journal §§10 and 44 and the concrete examples treated as claims throughout the journal. The question about verification of any one example is new. I checked C 100–122, 362–365, and 430–434 and looked through the whole contract for a more specific per-example verification statement; I did not find one.

**Confidence.** High that I treated examples as behavior I could rely on under their stated conditions. Moderate about inferring supporting verification for every individually labeled example. I cannot attest to the verification history of any one sentence.

## 7. A satisfied gate with no source final-activation timestamp

**Answer.** I did not read a current producer identity as a guarantee that no contradictory observation can reach my program. Such material can reach a reader as received bytes or as retained conflicting observations. The contract expressly permits conflicts to remain publishable. But the combination in the question cannot establish a valid satisfied-gate claim: the required source timestamp is absent.

I would distinguish a received field reporting “satisfied” from a semantically admitted conclusion that the dependency was satisfied. In a product projection of admitted claims, I expect the dependent claim to be withheld. If the product instead presents that combination as an admitted satisfaction claim, that would not meet the stated rule. The contract does not tell me exactly whether this case rejects a whole reply, retains a raw state while withholding another claim, or produces a particular diagnostic. It does not promise a named error field for this example.

An independent reply reader can identify the inconsistency by checking that a satisfied gate has both source final-activation and owned-reap timestamps, along with the other gate conditions. A matching contract or structural fingerprint is not that check. If my program consumes only an already validated product projection, I expect the product's semantic checks to have excluded the unsupported claim; the text does not give me a complete field-level recipe for recognizing that disposition. I therefore cannot promise that the program will find a particular ready-made “wrong” flag.

**Contract basis.** C 220–226 requires both source timestamps and the remaining satisfaction conditions. C 230–231 says absent source times cannot satisfy the dependency. C 165 withholds dependent lifecycle claims for unknown or contradictory observations. C 319–322 and 351–355 distinguish structure from semantic admission and allow conflicting observations to remain published with claims withheld. C 147 and 347–350 allow retained received bytes without making them valid claims.

**Reading and search.** The timestamp requirement and withheld-claim principle were remembered from Journal §§27–28 and 43. The distinction between what can arrive at this program and what it can accept is an application now. I compared C 212–236 with C 147–165 and 304–355, and used the rest of the full reread to look for a specific failure disposition. I found no exact diagnostic mapping for this case.

**Confidence.** High that the described evidence cannot justify satisfaction, and high that current identity is insufficient. Moderate about which representation can reach a particular consumer, because the consumer's position and the precise rejection/projection shape are not specified.

## 8. A receipt with a nonce different from the one sent

**Answer.** Yes, the wrong value can arrive as received receipt material; matching the current host contract does not make it acceptable for my request. I expect a request-aware acceptance step to refuse that receipt as evidence for the capture I asked for. I do not expect an accepted successful receipt for my request merely because its producer is current.

What I can predict about the reply is that the receipt must not be treated as valid for that request. I cannot name the exact status/code, say that its bytecode is necessarily removed, or say that the entire host reply is necessarily rejected. The sentence “a wrong nonce refuses the receipt” does not give those presentation details. In particular, I would not automatically expect `request_failure.code: invalid_capture_nonce`: that code is described among request refusals, whereas this situation concerns a received receipt's correspondence to an earlier request.

My program needs the nonce it actually sent to establish that correspondence. An otherwise self-consistent receipt cannot establish that external relationship by itself. If my program is an independent receipt reader, I would compare the received nonce with the saved expected nonce before accepting the receipt. That is my inference about what it means for my program to accept this evidence, not an express instruction in the text to duplicate a check that some specified request-aware product reader has already completed. The contract does not allocate that request-aware comparison precisely enough for me to assume every upstream projection already performed it. If I rely on an already admitted receipt, that reliance must include admission for my request's nonce, not just host identity admission.

**Contract basis.** C 90–91 establishes request capture/nonce prerequisites. C 243 requires receipt consistency and expressly refuses a wrong nonce inside a current reply. C 159 supplies the independent host-admission step. C 347–355 distinguishes retained material and structural shape from accepted claims. C 258–264 and 282 place `invalid_capture_nonce` in the request-refusal discussion.

**Reading and search.** The invalid-receipt conclusion was remembered from Journal §29. The allocation of the request comparison and the exact output shape were not established there. I reread C 90–91, 240–244, 258–284, and 347–355 within the shared full scan. This question required reasoning now about the program's saved request context; I found no receipt-specific output-code rule or definitive allocation of the check.

**Confidence.** High that the wrong nonce cannot support accepting the receipt for the sent request. High that independent acceptance needs a comparison to that request. Moderate about the expected upstream rejection point, and low about any exact projected failure spelling or retained payload shape.

## 9. Equal release contracts on apps, and an equal contract on a runner

**Answer.** For the two apps, I know that the reported public admission identity is the same and names the same release. Taking the reports as products of the described build process, both claim release builds from a clean tree at the named annotated tag, with scoped source bytes checked against that tag's blobs. Within the same release/tag history, I take them to assert the same release-bound public surfaces.

I do not take equality of that release label to establish byte-for-byte equality of the installed apps, signatures, entitlements, compiler/SDK, machine environment, or runtime observations. The label is not itself a digest of the complete installed package. Nor does it independently authenticate its own report or resolve the identity of a tag in an otherwise unspecified release history. Describe, commit, version, and number remain descriptive fields; matching `contract` alone is not a stated equality check on all those fields. I would still honor the separate binary-fingerprint, worker-identity, equipment, and entitlement checks instead of treating the public string as their result.

For a runner, equality tells me that its reported public identity passes that equality requirement. It does not by itself establish that both the registry record and the actual live peer match, that the selected worker has required entitlements/equipment, that a particular request passes other admission checks, or that an attempt will succeed or exhibit a particular sandbox outcome. A claim in a registry record is specifically insufficient when the live peer is foreign. If I have actually obtained the matching live peer's report, that resolves the live-identity part, but not the other requirements.

**Contract basis.** C 8–15 and 438–441 define release production/reporting and distinguish descriptive metadata. C 100–106 binds surfaces to the release; C 118–119 disclaims identical observations across builds/OS versions. C 171 and 183–193 separately require equipment and entitlement associations. C 249 and 296 require live-peer as well as registry identity. C 341–345 and 422–425 preserve separate contract boundaries. C 416–420 expressly limits the internal source hash's guarantees; I do not transfer stronger guarantees from that internal identity to the public release label.

**Reading and search.** I remembered the identity/provenance distinction, independent peer checks, and observation limits from Journal §§2, 12, 20, 30, 36, 42, and 49–52. The equal-installed-app scenario required combining them now. I revisited C 8–15, 100–119, 171–193, 249, 296, 341–345, 416–425, and 438–441 as part of the full reread. No package-authenticity or package-byte-equality promise was supplied there.

**Confidence.** High about the public equality requirement and the separate checks. High that identical runtime observations or installed-package bytes do not follow from the label. Moderate about a shared source baseline unless the two reports are understood within the same authentic release/tag history; the string alone does not establish that background.

## 10. What I took `_test_overrides` to be

**Answer.** I took it to be a request object for explicit testing or instrumentation overrides. The underscore and name suggested intended use by maintainers and test harnesses, but I did not read them as an access-control rule. Because it appears among accepted request objects, I took a request author who knows its accepted fields to be able to express it subject to admission rules. I saw no stated privileged-user requirement, build-mode restriction, or blanket prohibition on an ordinary caller using that object. That is an inference from its placement, not a documented authorization matrix.

I did not know its field inventory or exactly what it could change. The actor-equipment discussion separately says explicitly instrumented overrides are distinguishable from packaged roles and carry `unverified_fixture` identity. That gave me a concrete understanding that overrides can affect the equipment whose evidence a run produces, without establishing packaged selection. It does not explicitly say that all such equipment overrides are supplied through `_test_overrides`, or enumerate other capabilities of that object. I did not infer permission to bypass contract checks, fake any arbitrary observation, or alter every native outcome.

**Contract basis.** C 67–75 includes `_test_overrides` among closed request objects and separately mentions the actor equipment override map. C 188–190 describes instrumented equipment overrides and their attribution limit. C 3–6 and 63 preserve exact public admission; no override exception is stated.

**Reading and search.** The testing/instrumentation interpretation was remembered from Journal §7 and the carried-terms discussion in Close-out; Journal §22 supplied the equipment distinction. The precise “who may use it” question was not resolved in the first pass. I reread C 67–75 and 183–193 and checked the full contract for further restrictions or field definitions. I found no complete authorization or capability specification.

**Confidence.** High that it is a recognized, closed request object. Moderate about intended test/instrumentation use and the inference that its name does not itself restrict callers. Low about its full effects or any unstated mode restrictions.

## 11. Is the request-failure code table exhaustive?

**Answer.** I would treat it as the documented code meanings, not as permission to write an exhaustive switch with no unknown-code case. The contract does not expressly tell me that these are all codes any admitted reply can contain; more decisively, it tells me what to do with unfamiliar codes.

My code would preserve an unfamiliar code and its supplied diagnostic context as an unclassified refusal. It would not guess a cause, turn it into success, parse supplementary error prose to invent a classification, or assume that an unfamiliar code itself proves a foreign producer. Producer admission and interpretation of a refusal code are separate steps. Even if the table happened to cover the currently emitted set, the stated unknown-code handling would still govern my reader.

**Contract basis.** C 273–284 provides the table. C 289 explicitly says to retain unfamiliar codes as unclassified refusals rather than guessing their cause. C 266–271 instructs consumers to use code/path without parsing the error prose; C 263–264 also denies success inference from absent structured diagnostics.

**Reading and search.** This answer was remembered directly from Journal §35, supported by §§32–34. The necessary local lookup was C 263–289; the shared full-document reread did not change it. The distinction between documented meanings and an exhaustive implementation switch is an application now of the explicit unfamiliar-code instruction.

**Confidence.** High about reader behavior. I do not claim to know whether the table in fact lists every code emitted by this build.

## 12. Reusing a development-asserting specimen with a release

**Answer.** I cannot literally apply “surface rows changed since its asserted release” when the assertion is `development:<sha256>`: it names no asserted release to use as the comparison baseline. The contract gives no algorithm for turning that development digest into a release baseline, and the target's release stamps alone do not describe every difference from that development build.

The parts I can apply are deliberate author review of the target contract and manual replacement of the assertion with the target's exact release identity, plus external-runner reinstallation when applicable. I would review the target definitions relevant to the specimen and decide whether they still express what I intend. If I independently knew the development build's baseline and differences, I could use that knowledge to guide comparison, but the contract does not derive it from the digest for me. Without such a baseline, I could not claim that a release-to-release stamp comparison had covered the development-to-release change.

Even if the development build's relevant source happened to match the eventual release, its development assertion is not automatically accepted by the release. Changing the assertion is still the author's acceptance decision. This is my adaptation of the general reuse responsibility, not a fully specified development-to-release procedure found in the text.

**Contract basis.** C 8–13 defines the different identity forms. C 17–20 states the release-oriented reuse procedure and no-rewrite rule. C 29–32 derives stamps from annotated release history and excludes them from admission. C 63 requires exact identity, while C 100–106 requires review of the selected build's identity for shipped-source changes.

**Reading and search.** Manual reuse and development exactness were remembered from Journal §§2–4 and 10. The missing release baseline in this situation is reasoning now. I reread C 8–32, 63, and 100–106 and searched the rest of the contract by reading it for a development-specific reuse provision; none was supplied.

**Confidence.** High that the original development assertion does not match a release and that the stated procedure lacks that baseline conversion. Moderate about my adapted review approach, which is an inference about author responsibility rather than a separately mandated sequence.

## 13. What controller exit status 1 establishes

**Answer.** By ordinary command-line convention I would treat it as an unsuccessful invocation. From this contract alone, I cannot classify the cause from that number. The explicit rule is that the listed `bad_request` refusals make the controller exit 1; it does not give the converse rule that every exit 1 is one of those refusals, or provide a complete controller exit-code table.

The script cannot infer from status 1 alone that JSON was malformed, the contract was foreign, the runner was unavailable, transport failed, or a sandbox denied an operation. It also cannot infer the request-refusal guarantee of no step/child observations unless it first establishes that this was such a refusal. I would inspect the returned classification and, when present, `data.request_failure.code` and `.path`. Absence of that optional record would not establish success or select a particular alternative cause.

**Contract basis.** C 258–259 maps the listed request refusals to `bad_request` and exit 1. C 260–264 distinguishes tool/execution failures and makes structured diagnostics optional. C 266–271 gives their interpretation rules. C 286–289 describes request-refusal observations and diagnostic limitations, not a consequence of the integer 1 by itself. C 159 independently forbids assigning sandbox cause from permission-shaped failure alone.

**Reading and search.** I remembered the one explicit controller exit value and the unprovided tool-failure statuses from Journal §32 and Close-out's §32 accounting. The inverse-inference question is new. I checked C 255–289 and looked through the full contract for a complete exit mapping; I found none. I kept worker exit 4 and runner `rc: 1` statements separate from a controller exit-code taxonomy.

**Confidence.** High that status 1 does not identify a particular cause under the stated mapping. Calling the invocation unsuccessful uses ordinary exit-status convention as well as the failure context; the contract itself gives only the stated category-to-exit mapping.

## 14. Does the runner receive the request file's exact bytes?

**Answer.** I would not expect a byte-for-byte preservation guarantee. The controller parses and preprocesses a request: it removes selection fields and can resolve and remove augment instructions before XPC delivery. The dossier section speaks of a submitted serialization of held input, not a promise to forward the original file's serialization unchanged.

Consequently, a property of the file's whitespace or key order is not something I can rely on reaching the runner. In transformed requests, at least some submitted content necessarily differs. For an otherwise unchanged request, the contract does not specify the emitted key order, whitespace, or canonicalization, so I cannot say that its bytes must always differ either. The no-rewrite promise concerns the user's file, and the held-input promise prevents a later source-file edit from changing the admitted submission; neither promises byte-identical transport.

**Contract basis.** C 67–75 identifies decoding and field semantics. C 81–85 removes selection fields, resolves source fragments, and strips the augment list before submission. C 129 specifies in-memory augmentation and an unchanged input file in the refusal example. C 153 identifies held input and submitted serialization. C 19 says the user's specimen is never rewritten.

**Reading and search.** Preprocessing and held-input stability were remembered from Journal §§3, 8, 13, and 17. The distinction between held input and original JSON byte layout is an application now. I revisited C 17–19, 67–85, 129, and 153 within the full reread; I found no whitespace/key-order forwarding rule elsewhere.

**Confidence.** High that byte preservation cannot be assumed and that preprocessing can change submitted content. I do not claim a particular serialization format beyond what the contract states.

## 15. How broadly I read “no bypass”

**Answer.** I read it as applying to the public admission boundaries the document describes. For request files, my concrete belief covered the submission/run path and its pre-execution selection, augmentation, and helper work. I did not extend it into a claim that every shipped tool that merely opens or examines a request file must perform the same admission before doing anything with those bytes.

It also was not “the run path only” in the sense of excluding output readers: the opening sentence expressly includes independently arriving envelopes, host replies, and client captures, and their later sections require their own admission. Reading unsupported bytes for diagnostics or retaining them is different from admitting their contents as claims. Likewise, an unasserted authored test template is not yet an admitted submitted request.

I therefore understood no alternate identity, translation, or override route to obtaining public execution or semantic acceptance under these rules. I had not formed a belief about every standalone file-reading/checking utility, and the contract does not enumerate their admission boundaries here. If a tool presents its input as a public request, I expect the request gate to apply; mere file access alone does not establish that role. I cannot use this sentence to decide the behavior of an otherwise unspecified shipped command.

**Contract basis.** C 3–6 states the exact-admission/no-bypass rule in the context of specimens and independently arriving producer records. C 13 refers to public requests and packaged peer checks. C 63 gives the early request gate before selectors, augments, helpers, or children. C 147, 159, and 249 describe independent output/capture admission; C 147 and 374 retain unsupported bytes without granting semantic use. C 375–377 distinguishes authored templates from identity-asserting submission.

**Reading and search.** The strong public-admission rule was remembered from Journal §§1, 6, 16, 18, and 30. The all-shipped-tools-versus-run-path distinction was not one I had explicitly decided in the first journal. I worked it through now using C 3–20, 63, 147–159, 249, and 372–377, and the full-document scan for an exhaustive tool-scope statement. I found no such inventory or universal rule triggered merely by opening a file.

**Confidence.** High about no bypass at the expressly described public boundaries. Moderate about the inferred scope for an unspecified standalone tool; the text does not let me assign every shipped command to a boundary.
