# Final targeted revision reading

Both notation ambiguities recorded in REVISION-READING.md are resolved in the final text at the level of the rendered contract. The phase/action and optional-claim conditions now visibly delimit their implications, and the eight-phase branch explicitly includes omitted execution_form. Relocating the definition of “ordinary semantic reply” to the reply definitions confirms the distinction I had already reached: it includes both single-worker and actor execution forms when reporting_failure is absent. It does not denote successful execution, admission success or the single-worker form alone.

This is a targeted follow-up against FINAL-CONTRACT.md, SHA-256 `96649e66153c0670d111b4235817ffda15f4a8ac12e9dd62f3dddc0a91a21eb4`. It is not a fresh reading of the whole contract, an independent source check or execution evidence. Unless another artifact is named, line numbers below refer to FINAL-CONTRACT.md. No earlier artifact was edited.

## 1. Inputs and complete delta reading

The supplied FINAL-DELTA.diff has SHA-256 `7757178b704e6e6334924dd6738c9f7127385fdac790abcfb0abbb60bf429d01`, 377 lines and 29 hunks against the unchanged REVISED-CONTRACT.md. I read it sequentially in bounded portions 1–100, 101–200, 201–280, 281–330 and 331–377. All returned portions were fully visible; none was truncated. I completed the full delta before returning to selected final-contract passages.

The delta moves the ordinary-semantic definition from the later check-family account to the early reply definition, adds explicit implication grouping across multiple rules, and makes the non-actor phase-bound condition explicit about omission. The grouping changes appear in input applicability, actor declarations/identities, reservation and capture relations, helper output, transfer association, query identity, lifecycle and validator relations, gate conditions, authority scope, compiled-profile labels, collection bounds, actor projection coverage, dossier relationships and recovery fields. I read all these hunks, rather than restricting the delta reading to the two previously flagged rows.

That broad presentation change is not evidence that each affected implementation branch changed. I assessed what the new text commits to and whether I can now read its condition scopes. I did not compare the rendering against generator input or program logic.

## 2. Implication grouping: resolved

The former ambiguity was whether a later requirement in an inline “if A, then B and if C, then D and E” expression remained independent or belonged inside an earlier consequent. In the final phase/action row at line 4493, the conditions are visibly grouped into separate conjuncts:

- An actor-form implication sets the phase bound to 16.
- An explicit absent-or-present-non-actor implication sets the phase bound to 8.
- The step bound of 256 is outside those implications.
- The extension-event bound is inside its own presence implication.
- The sum of phase action-ID counts is independently bounded by 256.

This closes the uncertainty I recorded for the earlier line 4490. For example, omission of extension_events does not make the total-action-ID bound disappear, and an actor-form reply does not escape the step bound because the non-actor antecedent is false. Those are readings of the displayed conjunction, not test results.

The same improvement is visible in the exact optional-claim case that concerned me. At 4527 and 4536, each run question has its own parenthesized implication; inside that implication a second, separately parenthesized presence guard bounds its basis. Therefore, an absent final_status question does not make a later present stop_reason question's basis unlimited. The step-claim groups at 4528 and 4537 behave similarly. At 4508–4509, the boundary and result basis guards are separate. The validator zero/positive-count alternatives and present/absent-record issue allowances at 4519–4520 are also separately grouped.

A further concrete case is actor equipment at 4505: the optional missing_requirements list's guard now closes before the native_observations bound. The latter is a separate requirement within the rule's actor/equipment applicability, rather than something I must infer to be outside the missing-list condition.

My previous working interpretation of these predicates is now supported directly by their grouping. I do not need to supply a convention about where “then” ends for these changed conditions. The nested notation remains long, but length is not the same as unresolved logical scope. I found no new grouping contradiction in the complete delta or the targeted return reads.

**Status and confidence:** the previously identified implication-grouping ambiguity is resolved, with high confidence at the document-reading level. I do not claim a complete formal verification of every expression in all 5,831 lines, nor source equivalence or executed boundary behavior.

## 3. Omitted execution_form: resolved

Line 4493 now makes the eight-phase antecedent explicit: execution_form is absent, or it is present and differs from actors. The 16-phase condition applies when execution_form is actors. The previous report's uncertain inference that ordinary omission belongs to the eight-phase case is no longer required.

This also agrees with the ordinary worker projection's explicit absent-or-present-non-actor condition at 4587. The two statements refer to different operations—collection admission and worker projection—but now visibly agree on the relevant form distinction. The collection gate still precedes semantic association, and its limits apply to preparation and reporting-failure replies reaching it (4487–4489).

The following conclusions follow directly from the rendered guard, assuming a structurally decoded reply reaches this gate:

| Carried execution_form | Phase-count requirement at this gate |
| --- | --- |
| Absent | At most 8 phases. |
| Present as actors | At most 16 phases. |
| Present with another value | At most 8 phases under this guard. |

Passing that last size condition does not establish that every other execution_form value is semantically admitted. It only answers the size-check branch. A reply with an omitted form and nine phases now unambiguously fails this requirement; a reply with actors and sixteen phases satisfies this individual requirement but can still fail other bounds or later checks. These are hypothetical clause applications, not inputs I submitted to the product.

On a collection-bound failure the stated consequence remains malformed_runner_response, false result.ok, exit 1 and retention of the decoded reply; run has null diagnostics and verify has null runner_pid (4510–4512). The final delta does not change that consequence or turn it into a post-admission integrity finding.

**Status and confidence:** the omitted-field ambiguity is resolved, with high confidence at the text level. The final condition supplies the missing branch directly; no assumption about inequality on absent optional values is needed for the eight-phase case.

## 4. The earlier ordinary-semantic definition

The final reply definition states at 371–372 that an ordinary semantic reply has no reporting_failure record and that this branch includes both single-worker and actor execution forms. The delta shows that this same definition previously appeared in the later check-family section; the later location now refers to the reply definition (4685). It is a relocation of the stated meaning, not evidence of a new execution form or new validity rule.

This does not reverse my completed first-read understanding. Journal entry 64 already separated degradation-form validation from worker lifecycle validity and marked the ordinary/degraded/local/global applicability distinction answered. The earlier revision report likewise kept collection admission, ordinary semantic associations and degraded retention separate. What changes for me here is where the definition becomes available: the meaning is explicit before the later actor field and association accounts use it. I cannot claim how an otherwise uninformed first reader would have behaved; I am already familiar with the later definition and the questions.

The relocated text makes two independent distinctions easier to keep explicit:

| Execution form | Reporting-failure record | Ordinary semantic branch? | Phase bound at the collection gate |
| --- | --- | --- | --- |
| Single-worker form, normally omitting execution_form | Absent | Yes. | 8. |
| Actor form | Absent | Yes. | 16. |
| Single-worker form | Present | No; reporting-failure scope applies. | 8. |
| Actor form | Present | No; reporting-failure scope applies. | 16. |

This table combines the definition at 371–372, the collection rule at 4487–4493 and the later check-family applicability at 4689–4701. It assumes the relevant records reach those boundaries and does not certify that an arbitrary combination is otherwise a valid reply. In particular, ordinary semantic does not select the eight-phase limit: an actor reply can be ordinary semantic and retain the actor limit of sixteen.

A preparation refusal can also belong to the ordinary semantic branch when it lacks reporting_failure. Its content and applicable checks remain those of its preparation account. Lines 3539–3547 expressly describe retained declarations with no launch, execution or successful application observations. Calling that account ordinary semantic does not assert that a worker ran or that the result succeeded.

The actor visits field at 3517 illustrates why the distinction matters. Its ordinary-semantic requirement describes the actor's exact declared visit list, including visits never activated; it cannot mean “single-worker only,” since the field is on an actor. The early definition resolves that possible category confusion before this use. Conversely, the heading “Ordinary worker projection” at 4585 has its own explicit execution-form condition and run-scoped subprocess source (4587–4590). I do not replace that local condition with the broader ordinary-semantic definition.

Absence of reporting_failure is not an admission certificate or a statement that every relationship is true. It identifies the branch whose applicable semantic checks must be considered. The reply definition itself distinguishes retained raw bytes from an admitted decoded reply (366–369). The collection gate remains before semantic association (4487–4489). The later check-family table still distinguishes worker-local validation, reply-wide ordinary checks, actor-specific relationships and reporting-failure form (4689–4701).

**Status and confidence:** high confidence that the relocation clarifies the already stated meaning without changing these conclusions. It exposes the importance of keeping execution form and reporting form separate, but I found no new contradiction in the relevant passages.

## 5. What remains limited

The two notation findings from REVISION-READING.md no longer remain open against this final input. U54's earlier collection-bound uncertainty is now answered for the displayed numeric collection domain, applicable branches and refusal effects, without those two particular rendering qualifications. That still does not amount to a complete independent implementation of every semantic validator. U42's Mach spelling resolution from the earlier revision is unaffected by this delta.

The final definition does not resolve the previously open policy question about enforcing ordinary actor/phase/resource associations on reporting-failure records. Lines 3555–3562 retain the degraded scope and separate worker-lifecycle reader, and 4695–4701 preserve degradation-form checking and independent worker projections. Applying collection size limits to a degraded reply is not the same as validating its ordinary semantic joins.

The previous distinctions between production obligations and receiver checks also remain. Parenthesizing a produced field relationship does not turn it into a new independent reader check. Likewise, clarified receipt label predicates do not add a controller request-nonce comparison, and collection refusal remains distinct from a later finding that can coexist with an admitted finished result.

The collection-rule support at 4540 is still a check-read account with selected constructed controls and separately source-supported branches. The final delta supplies no new run establishing every limit or native malformed-reply condition. I did not open cited source or tests, perform product execution, or treat the presence of cleaner notation as stronger implementation evidence.

I found no additional blocking reading ambiguity in the changed conditions and returned passages. This is bounded to the complete delta and the targeted reads listed below. It is not a claim that the entire contract is free of every ambiguity, that every support statement has been independently verified, or that all previously deferred implementation/native-evidence questions are resolved. No editorial changes are proposed by this report.

## 6. Exact scope, hashes and preservation

After reading all 377 delta lines, I returned to these FINAL-CONTRACT.md ranges as line-numbered raw Markdown:

- 343–384: request/reply definitions and the newly early ordinary-semantic definition.
- 4484–4543: the complete collection-bound account, changed implication scopes, omitted-form branch, refusal effects and support paragraph.
- 3507–3565: actor fields, visit meaning, preparation and degraded reader applicability.
- 4681–4712: the relocated-definition reference, semantic check families and degraded behavior.
- 4583–4601: ordinary worker projection and its explicit form condition.

One search of FINAL-CONTRACT.md used the terms ordinary semantic, single-worker, Ordinary worker projection, Reader applicability, and Check families and applicability. The visible matches were at lines 371–372, 2852, 3517, 3535, 3537, 3557, 3561, 3564, 3657, 4585, 4683, 4685 and 4740. The search located context; cited links were not followed. I also reread my own JOURNAL.md lines 507–514, entry 64, to check whether the moved definition reversed the belief recorded at the end of that original portion. The other earlier reports were recalled from the completed phases and read as bytes only for preservation hashes in this phase.

Every shell command explicitly used `/private/tmp/pw-contract-stage-three-isolated-reading-20261111`. There was no directory traversal, repository inspection, source/check opening, external browsing, service access, product/test execution or delegation. No tool output was truncated in this phase. File-access isolation violations: none. The reading was cued, comparative and targeted; it was not a new sequential first reading or a visual render review.

The complete bytes of the authorized inputs and earlier reports were hashed to verify identity and preservation. This byte hashing was not substantive reading of all their text. Verified values were:

| File | SHA-256 |
| --- | --- |
| FINAL-CONTRACT.md, 5,831 lines | `96649e66153c0670d111b4235817ffda15f4a8ac12e9dd62f3dddc0a91a21eb4` |
| FINAL-DELTA.diff, 377 lines / 29 hunks | `7757178b704e6e6334924dd6738c9f7127385fdac790abcfb0abbb60bf429d01` |
| REVISED-CONTRACT.md | `fe58bde3292263eea1ebf252d2cf279fbf691e61f4476fc6fe394c55d022111a` |
| DELTA.diff | `b6653d823f6e415e45cd52b6fcc01fefd2b798cbe0f4a714927e5145db6c6224` |
| Original CONTRACT.md | `e1aafb723c46261bffe5c4c940abd81dae222ee1aa6ff53067428ef4c17c9814` |
| JOURNAL.md | `64c9f500057b17f3e2f2d64363da797c3ed90cd81b2e454395054141af55eba0` |
| JOURNAL-FROZEN.md | `64c9f500057b17f3e2f2d64363da797c3ed90cd81b2e454395054141af55eba0` |
| PROMPTED.md | `b80ca7ff514bd87c77545a6aaae4b098a0dc24f79a709052c6d926fe8cc17d76` |
| REVISION-READING.md | `d0a83ccf4cd2cecee3c314cb9798e3d0493ad24130784a86b01e7ec439d80070` |

FINAL-REVISION-READING.md is the only file created or modified in this phase. Its completed hash is reported separately to avoid a self-referential hash. This reading stops at the exact final input identified above; the earlier records remain frozen accounts of earlier understanding.
