# Targeted revision reading

This report concerns only the revision frozen as REVISED-CONTRACT.md, SHA-256 `fe58bde3292263eea1ebf252d2cf279fbf691e61f4476fc6fe394c55d022111a`, and its supplied DELTA.diff against the original CONTRACT.md. It is a targeted revision reading after the completed first-read journal and prompted answers. It is not another first reading, a complete rereading of the revised contract, source verification or execution evidence. All unqualified contract line references below are to this revised input; references to the old journal identify its entry or uncertainty number explicitly.

My main changes in understanding are these: the admitted Mach attempt name is now internally consistent; the previously deferred response collection limits are explicitly described, with their admission consequences; and seven relationships previously worded as checks are now clearly obligations of the producer's reported records. New local entry and recipient labels make some scopes easier to identify without changing my established distinction between production, admission and semantic assessment. Two notation limits remain in this exact input: implication grouping and how the collection guard treats omitted execution_form.

## 1. Inputs, preservation and method

I first obtained line counts for the two new files, then read DELTA.diff sequentially in portions 1–180 and 181–340. Both portions were fully visible without a tool truncation warning. All 340 lines and all 24 hunks were read before I began returning to revised passages. I then used line-numbered raw Markdown and targeted searches to inspect consequences and compared the affected beliefs with my own original journal. Links and cited implementation/check paths remained literal text.

The revised file contains 5,829 lines. The input hashes verified during this phase were:

| Input | SHA-256 |
| --- | --- |
| Original CONTRACT.md | `e1aafb723c46261bffe5c4c940abd81dae222ee1aa6ff53067428ef4c17c9814` |
| REVISED-CONTRACT.md | `fe58bde3292263eea1ebf252d2cf279fbf691e61f4476fc6fe394c55d022111a` |
| DELTA.diff | `b6653d823f6e415e45cd52b6fcc01fefd2b798cbe0f4a714927e5145db6c6224` |
| JOURNAL.md | `64c9f500057b17f3e2f2d64363da797c3ed90cd81b2e454395054141af55eba0` |
| JOURNAL-FROZEN.md | `64c9f500057b17f3e2f2d64363da797c3ed90cd81b2e454395054141af55eba0` |
| PROMPTED.md | `b80ca7ff514bd87c77545a6aaae4b098a0dc24f79a709052c6d926fe8cc17d76` |

Every shell command explicitly used `/private/tmp/pw-contract-stage-three-isolated-reading-20261111` as its working directory. No parent directory or repository file was inspected. Only the authorized inputs and this report were accessed; only REVISION-READING.md was created or changed. The hashes establish that the earlier journal and prompted artifact remain unchanged. Hashing read complete file bytes but was not counted as a substantive rereading of their text.

The initial task message identified the categories of revision, so this was cued from the outset. After I had identified and sent the two notation findings, the parent said a later narrow revision was planned and asked that this report be completed against the unchanged input. No later revision was supplied or read. That coordination does not resolve any finding in this report or provide implementation evidence.

## 2. Mach attempt spelling: a directly resolved uncertainty

**Earlier belief.** Journal entry 37 raised U42 because the request table admitted `mach / lookup`, while the later operation-relation table used `mach_lookup / bootstrap_look_up`. The original close-out kept that conflict open and explicitly declined to treat the latter spelling as a new admitted request pair. That was a real uncertainty in the original text, not a retroactive inference from this delta.

**Revised account.** The attempt kind's closed exhaustive vocabulary now includes `mach_lookup` at line 910, and the admitted operation table names `mach_lookup / bootstrap_look_up` at line 930. The native operation description is unchanged: obtain the bootstrap port, call bootstrap_look_up for the supplied name and release the returned service port on success. The delta changes both the family and action spelling in the input table rather than adding an alias explanation.

**Understanding now.** U42 is resolved at the level of the stated contract. I can use the revised pair as the documented input spelling and no longer need to infer a relationship between two differently named pairs. I cannot infer that `mach / lookup` remains an accepted alias; the revised closed list supplies no such commitment. I also cannot infer whether implementation behavior changed at this revision or whether the old prose was inaccurate. That historical/source question is outside the supplied evidence.

**Confidence.** High for the revised admitted spelling and resolution of U42; no independent implementation or native-execution verification.

## 3. Producer relationships are no longer presented as receiver checks

The delta reclassifies the following local rules from “checks” to “reports,” or expresses the projected assignment directly:

| Revised rule | What I can now say from this rule | What this rule alone does not establish |
| --- | --- | --- |
| Delivered receipt prerequisites, 2065–2073 | The host's produced delivered record retains published request, held custody, copied bytes, equality and recipient acknowledgement. | That a receiving controller independently rechecks all of these fields or rejects every contradictory received record at this rule. |
| Source acknowledgement association, 2078–2085 | Ordinary produced records with source acknowledgement carry the unique matching completed source event and the stated known-status relationships. | A universal receiver-side association check, especially for degraded records or unknown acknowledgement names. |
| Packaged bound-row equalities, 3900–3908 | A successfully produced packaged bound row carries the compared observed/expected digests and entitlement equality. | That merely receiving those equal values authenticates the file or repeats the native binding operation. |
| Augmentation relationships, 4994–5002 | The controller's constructors produce the stated empty/applied/hash/error relationships. | An independent check of a subsequently received dossier object or an invented refusal consequence. |
| Retained scan scope, 5021–5029 | The produced scan account obeys the stated necessary conditions for complete and the distinct failed/skipped form. | Sufficiency of visible fields to reconstruct the complete scanner decision or an independently validated native import closure. |
| Retained recovery account, 5392–5400 | The removal result reports the retention/record/warning relationship after the cleanup publication attempt. | A separate output-reader validation event or proof of absence from a printed flag alone. |
| Published installation state, 5418–5422 | The controller sets install.state from the returned runner record's state after publication. | A separate equality check of an independently supplied installation result, or proof that the service is loaded. |

These remain meaningful production obligations. The change does not turn them into optional commentary, nor does it imply that the producer performs no underlying checks. For example, the binding-before-launch rule at 3887 still explicitly requires inspection and comparison of the service seal, inventory and both packaged worker roles, with launch withheld on preparation failure. The narrower correction is to the role of the projected field relationships: they account for what is produced, rather than assert an additional reader enforcement operation.

My original journal entries 28, 53, 68 and 73 largely described the produced relationships correctly. Entry 53's account of static comparison remains supported by the actual preparation operation at 3887–3895. I do not need to withdraw that account merely because the later bound-row projection is now labeled “reports.” I do need to resist treating an earlier “checks” label on one of these relationships as proof of independent admission or semantic rejection by a recipient. The revised refusal index's removal of the dossier and installation projection rows reinforces that distinction; it does not supply a replacement refusal rule.

This sharpens U11's attribution of checks and the earlier prompted answers about public commitments and boundary roles. It leaves U15's dossier meaning and U56's recovery meaning intact. It does not resolve U37's open question about ordinary association guarantees for reporting-failure records. Source acknowledgement itself still applies to the ordinary path, and the bounds added elsewhere are size checks rather than that association guarantee.

Confidence is high in the role distinction. Whether any particular consumer duplicates these predicates elsewhere would require its own stated rule or evidence; I did not open code to answer that question.

## 4. Decoded response collection bounds: new usable detail

**Earlier uncertainty.** The original journal repeatedly carried U54 and ended with the complete response-context collection guard deferred to source. I knew there was a geometry admission gate before assessment, but could not enumerate its numeric domain from the original public document. The prompted answers similarly referred to capacity admission without inventing every bound.

**New boundary and scope.** Lines 4484–4486 now put an explicit controller check after delivery, capture and public identity admission, for both cli run and runner verify. It applies to every structurally decoded reply that reaches it, including preparation and reporting-failure replies. Optional collections are bounded when present. Counts refer to retained rows before semantic association. Lines 4537 and 4542–4548 place collection checks before profile-context checks and semantic assessment.

My working reading of the enumerated bounds is:

| Collection domain | Stated bound or arithmetic |
| --- | --- |
| Phase and action tables | Actor phases ≤16; ordinary/non-actor phases ≤8; steps ≤256; extension events fit within 256 minus step count; total phase action IDs ≤256. The conditional rendering has the scope limits recorded in section 7 below. |
| Actors and transfers | Actors ≤8; transfers ≤64. |
| Resource tables | Tokens ≤32; deliveries ≤64; handles ≤64; each handle's equal-handle references ≤64−1, hence 63. |
| Equipment | Static bindings ≤4; entitlement records ≤12. Per actor, required and present missing-requirement lists ≤64; native execution observations ≤4. |
| Authority table rows | Workers ≤8; host regions ≤8; host custody rows ≤32. |
| Authority operation cells | Host run and each custody scope: operations ≤4. Each worker and region scope: operations ≤16. Each named scope: ownership ≤5 and optional integrity-error list ≤16. |
| Actor visits | Each actor's visits ≤16. |
| Validator context | Expected IDs ≤256; retained records and issue allowance use the explicitly defined carried-step count, described below. |
| Ordinary and actor worker dispositions | Each disposition's step rows ≤256 and issues ≤1+2×256, hence 513. Present run-claim basis lists ≤14; present step-claim basis lists ≤16. Issue observations ≤16 when step_index is present, otherwise ≤14. |
| Copied lifecycle claims | Present attempt/extension boundary and result basis lists ≤16. |

The scalar arithmetic above is my calculation from the displayed expressions, not an execution or a claim that the limits were reached in a test. The relevant clauses are 4490–4506 and 4515–4535. The counts limit collection sizes; they do not establish uniqueness, matching identities, valid references, true native observations or semantic agreement.

**Validator counting is more specific than I previously knew.** Line 4494 defines the count from retained steps with the same phase_id, excluding only steps whose sandbox_check.missing_reason is exactly query_not_requested. Absent missing_reason is included. It expressly precedes semantic uniqueness and association checks. At 4516, zero matching steps permit at most two retained validator records; a positive count N permits at most 2N. At 4517, with R retained records, the association-issue allowance is N+R+1; if records are absent it is N+1. This is not a count of successfully and uniquely associated queries.

For example, under that reading, N=0 with two retained records permits at most three association issues; N=5 with ten records permits at most sixteen. These are arithmetic illustrations only. Duplicate or otherwise suspect carried labels can affect the preliminary count without thereby becoming valid semantic joins.

**Admission consequence.** A failed collection bound selects malformed_runner_response, false result.ok and exit 1 while retaining the decoded reply (4507). Cli run receives null runner_sandbox_diagnostics (4508). Runner verify carries the same failure classification and null runner_pid (4509); the verification operation now explicitly references the collection-bound rule in the delta at revised line 5201. This is refusal before the ordinary evidence assessment path. It differs from a later integrity finding that retains diagnostics with selected conclusions withheld and can coexist with an admitted finished result.

A raw retained report may therefore still contain finished or reporting-failure context after this new admission rule refuses it. Its presence does not select public success or establish that its observations were assessed. Conversely, a reply below every size bound has only passed the collection gate; it may still fail profile labels or semantic requirements. Nothing in this admission result alone determines whether the experiment previously executed.

**Effect on U54.** The numeric collection domain and public refusal consequences are now substantially answered in the document. The earlier inability to enumerate those bounds no longer applies in the same way. This does not resolve every semantic-family predicate previously deferred under U24, U31, U43 or U46, and the conditional-notation questions below prevent me from claiming an entirely unambiguous formal predicate transcription from this rendered text alone.

**Evidence credit.** The new support paragraph at 4537 is check read. It says every guard and both public routes were read, but limits the constructed controls to selected excess tables/reference lists, an accepted boundary and raw-record retention; other enumerated bounds and verification-specific projection have source-branch support. I read that evidence claim as text. I did not inspect those sources, run those checks or upgrade it to execution credit.

## 5. Local entry scopes and arithmetic presentation

The revision adds local actor/boundary/entry/recipient/report accounts to the host report (2338), step evidence assembly (2456), run and helper envelopes (4346, 4359), run payload (4388), and ordinary/actor worker projections (4584, 4778). The compiled-profile surface now states its entry/recipient/report span (4181), its reason vocabulary identifies controller reply admission (4195), and the two failed-label consequences explicitly label cli run and runner verify (4322–4323). These local labels make an excerpt easier to classify without borrowing the nearest section's role or treating every consequence as applying at every entry.

My earlier conclusions about the receipt do not change: host publication guards and controller carried-label admission remain separate. Adding the receipt reason's local boundary does not turn its open reason string into a new nonce or digest comparison. Likewise, the new geometry gate gives more content to the capacity step but does not supply a request-nonce operand. The original prompted distinction between a host-detected mismatch and an inconsistent nonce in an arriving otherwise admissible receipt remains intact.

The phase ordinal expressions now display separately marked operands and explicit arithmetic parentheses: q+1 in prepared phase correspondence (3727) and p+1 in preparation-refusal correspondence (4058). I read these as clarified presentation of the same zero-based-position to one-based-ordinal relation, not a changed ordering rule. New limits similarly display subtractions, products and sums with their named limits. That lets me compute 63 equal-handle references and 513 disposition issues without guessing what the words denote. These improvements do not by themselves resolve implication scope in the longer expressions.

The local scopes strengthen my answer to the earlier A1/B4 questions about who is acting and which boundary owns a statement. They still do not create a single global separator declaring all material outside a particular syntax nonbinding. Typed response transport remains described product behavior through a concrete mechanism; no delta here removes that interpretation or adds new execution evidence for it.

## 6. Status of earlier uncertainties and prompted distinctions

| Earlier item | Status after this targeted reading |
| --- | --- |
| U42: inconsistent Mach pair | Resolved for the revised stated input spelling. No alias or implementation-history conclusion added. |
| U54: unknown response collection bounds | Substantially resolved for enumerated collection guards, their pre-assessment scope and refusal effects. Formal conditional rendering retains the limits below; full semantic validators are a separate question. |
| U11: checks, withholding and retention | Refined by explicit producer-versus-reader roles and the newly detailed admission gate. The distinction between refusal and later finding remains. |
| U37: degraded actor/phase/resource associations | Still open beyond the stated degraded form. Size admission applies to degraded replies, but does not reinstate ordinary semantic association guarantees. |
| U15/U21: dossier and import scope | Produced-field relationships are clearer. Nonliteral-form classification still has no dedicated Boolean, and native compiler input equivalence is not established by scanner completeness. |
| U18: receipt publication and carried-label validation | Unchanged in substance, with clearer local entry labels and capacity context. No additional controller nonce comparison. |
| U07/U17/U48: equipment and authorization | Static production evidence is more precisely labeled. Actual static inspection and separate live/authorization boundaries remain; a copied bound row is not a new independent authentication event. |
| U56: recovery and install projection | Produced relationships are clearer; no independent result-reader check or broader cleanup ownership guarantee is added. |
| U04: evidence grades | Unchanged. The new collection rule's check-read support remains scoped as stated. |
| Prompted A1/B4: global public/background boundary | Local roles are clearer; no global formal delimiter is supplied by this delta. |
| Prompted B1: direct source-test worker-identity regeneration | Unresolved by this delta. No regeneration owner, timing or freshness procedure is added. |
| Prompted A12/B13 and B8: exit status and nonce mismatch | Earlier distinctions remain. Collection failure adds explicit detail within malformed_runner_response; exit 1 still does not identify a unique cause or prove nonexecution, and receipt-label checking remains without a request-nonce operand. |

I did not conduct a new full audit of all 58 uncertainties. The complete delta supplies no new resolution of the remaining previously recorded source-layout, build-environment, native-failure, clock-domain, replay or execution-evidence limits. That is a bounded observation about this delta, not a new proof that no other paragraph in the entire revised document could bear on them.

## 7. Ambiguities remaining in this exact revised account

**Implication grouping in rendered conditions.** I can form a plausible working reading of the bounds, and the prose about optional collections helps, but some rows render chains as “if A, then B and if C, then D and E” without enclosing each implication's consequent. The phase/action row at 4490 is the clearest case: I read the step and total-action bounds as independent requirements, and the two phase limits as separate conditional requirements. Taken as formal inline logic, however, the text does not explicitly close the first or second “then” scope before later conjunctions. Similar nesting occurs in the optional run-claim lists at 4524 and 4533 and other optional-array rows.

This matters when an early optional field is absent. A reader trying to turn the rendered string into predicates must decide whether later guarded bounds remain independent or fall inside the earlier condition. My working interpretation treats them as independent guarded conjuncts, but I have not verified that interpretation against source. Confidence is high that the intended numeric limits are displayed; lower that every implication's exact scope is unambiguously expressed by the inline notation alone. I am recording a reading limit, not asserting that an actual implementation omits these checks.

**Omitted execution_form in the phase-count guard.** The new row at 4490 uses execution_form equals actors for the 16-phase case and execution_form not equal to actors for the 8-phase case. The execution record explicitly says the ordinary producer omits the field (2371). In contrast, the ordinary worker projection explicitly spells out “absent or present and not actors” (4584, also visible in the related search matches). I infer that the new non-actor count intends to include ordinary omission, but this particular condition does not explicitly say how an absent optional field participates in the inequality. The general statement that optional collections are bounded when present does not itself define comparison of this optional scalar.

I can read the intended ordinary bound by context; I cannot claim the literal row alone resolves the missing-value comparison without a convention or additional clause. This is a narrower issue than the original U54: the limit 8 is now displayed, and the uncertainty concerns its rendered applicability to a normal omitted field. No source check was performed to establish actual behavior.

**Production does not determine all reader consequences.** Reclassifying the seven rules removes an overstrong invitation to infer reader checking, but a malformed produced relationship still needs the applicable receiving rule to determine what a consumer does with it. I do not know every possible consumer's judgment merely from these production statements. This is an intentional boundary limit in my reading, not a demand that production rules themselves include every consumer policy.

**Evidence completeness remains scoped.** The collection support distinguishes selected constructed assertions from the remaining source-supported guards and verification projection. I therefore cannot claim an independently executed control for every listed limit, all malformed combinations, or native occurrence of large replies. A textual inventory and a source-reading support claim do not resolve those evidence questions.

## 8. Exact read scope and stopping point

After all delta hunks, the completed revised-contract return reads were:

- 4480–4515 and 4516–4558: the full new collection-bound account and its neighboring admission/projection entry.
- 2039–2098: transfer observations, delivered/source association production and resource-table context.
- 3872–3921: binding evidence, actual preparation operation, revised produced equalities and entitlement context.
- 2331–2374: host report ownership, record origin and optional execution_form.
- 4989–5042: produced augmentation/import relationships and the scanner's visible-field limit.
- 5387–5425: produced recovery and installation-state relationships.

All other changed text was read in DELTA.diff, including its supplied unchanged context. I did not reopen every changed section in the full revised file, because the complete hunks already exposed those changes and their local context. I used one revised-contract search for the Mach pair/family and execution_form omission/absence terms. It returned lines 910, 930, 2371, 3593, 3602, 3722, 3732, 4584, 4592, 4605, 4619, 4636 and 4650. Search hits were read as local text, not as proof of surrounding code or implementation behavior. No search result or passage output in this phase was truncated.

Own-journal return reading comprised its heading/targeted-uncertainty search, the complete uncertainty close-out at journal lines 647–723, and selected entries at journal lines 219–226, 419–434, 539–546 and 579–586. This was necessary to identify what my original uncertainties actually said rather than relabel them from memory. I did not edit those earlier statements. The prompted body was recalled from the prior phase rather than substantively reread here; its bytes were hashed for preservation. Original CONTRACT.md and JOURNAL-FROZEN.md were also read as bytes for hashes, not returned to as textual passages in this phase.

No repository, source, test, external link or service was accessed, no subagent was used, and no product/test execution was performed. File-access isolation violations: none. The method limits are targeted rather than full revised reading, raw Markdown rather than rendered layout, cued topics, prior familiarity, inline-logic interpretation and lack of source/execution verification. The frozen earlier artifacts remain evidence of what I understood before these changes.

This report stops at the exact input identified above. Its final SHA-256 is reported separately, avoiding a self-referential file hash. Any later revision requires a separately identified reading record.
