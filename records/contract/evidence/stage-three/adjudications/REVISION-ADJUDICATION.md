# Stage-three targeted revision reading: truth adjudication

The revised reader's consequential interpretations are accepted within their stated scope. Its resource-table row is accurate: **32 token records, 64 delivery records and 64 handle records**. This is not a confusion with another resource capacity. All enumerated geometry quantities and both validator examples match the source guards. The two remaining notation concerns are valid limitations of the frozen input: implication grouping and applicability to an omitted execution_form. No additional material truth defect was found in the revised claims reviewed here.

This is adjudication of one cued, targeted raw-text revision reading. It is not another fresh isolated reading, a complete rereading of the revised contract, or an executed implementation control. Earlier reports and reader inputs remain unchanged.

## Exact inputs and sequence

The entire 153-line REVISION-READING.md was read, SHA-256 `d0a83ccf4cd2cecee3c314cb9798e3d0493ad24130784a86b01e7ec439d80070`. Its exact REVISED-CONTRACT.md has 5,829 lines and SHA `fe58bde3292263eea1ebf252d2cf279fbf691e61f4476fc6fe394c55d022111a`. The entire 340-line DELTA.diff, all 24 hunks, was read in two consecutive portions; its SHA is `b6653d823f6e415e45cd52b6fcc01fefd2b798cbe0f4a714927e5145db6c6224`. These hashes were independently checked here.

The reader explicitly identifies prior familiarity, cued categories, targeted returns and raw Markdown. It did not open source, tests or links. Its reported access scope and preserved input hashes are consistent with that method. This adjudicator did not communicate with it. The complete report and complete diff were available without truncation. Some combined supplementary source/orientation reads were truncated; the consequential excerpts used below were reopened in smaller portions or were already fully exposed in the complete diff. No unseen truncated material receives fresh-reading credit.

The preceding unprompted and prompted adjudications are carried comparison records, not revised by this phase. Their hashes are retained in the manifest. This phase freshly reviewed selected actual source and the two cited geometry controls. No product, generator, build, test, model import, native call or service was executed. No shared file was edited. Hashing, searches, source reading and private report creation are the only operations credited here.

## Resource labels: explicit resolution

Frozen contract line 4492 spells the operands as `reply.resources.tokens`, `reply.resources.deliveries` and `reply.resources.handles`, using `actor_issues` (32), `actor_deliveries` (64) and `actor_handles` (64). The reader's section 4 labels reproduce those array meanings. `porcelain_admission.rs:1710–1717` checks exactly those three vector lengths against 32, 64 and 64, then each handle's `raw_equal_handles` against 63.

The typed record is `PWRunnerResourceTables` (`porcelain_records.rs:3233–3257`): three required vectors named tokens, deliveries and handles. Token entries are `PWRunnerTokenRecord` (`porcelain_records.rs:4028`), carrying a token reference, actor/step, family/status and optional length/last use. This is a count of token observation records, not token byte length, arbitrary native resources or a new field called extension_tokens. The manifest's actor_issues row describes issue actions, each assigning one token reference; `PWActorLimits` independently declares issues 32, deliveries 64 and handles 64. Reusing those named limit quantities in the response gate is consistent with the current explicit guard.

No reader correction is warranted for this row. The source and contract both retain the exact array names; a different label or capacity should not be substituted on the basis of the general word “resources.”

## Full geometry and arithmetic disposition

This table covers every collection domain enumerated by the reader. Source references are to current `controller/src/porcelain_admission.rs`; contract references are to the frozen revision. All comparisons below are source reading, not executed boundary observations.

| Reader claim | Adjudication and source |
| --- | --- |
| Actor phases ≤16; other forms ≤8 | Correct working interpretation. Lines 1696–1698 compare execution_form to Some("actors"); absence and any other string take 8. The frozen row's optional-scalar notation remains under-specified, as discussed below. |
| Steps ≤256; present extension events fit within 256 minus steps | Correct, 1698–1704. The source first rejects too many steps and extension events, then enforces their combined capacity. The rendered combined inequality plus the independent step bound is equivalent over these nonnegative lengths; a separate event-only ≤256 conjunct adds no admitted case restriction. The text does not promise source short-circuit/error-string order. |
| Total phase action IDs ≤256 | Correct, 1719–1724. The implementation accumulates all phase rows with a remaining-capacity check. This is a cumulative count, not 256 per phase. |
| Actors ≤8; transfers ≤64 | Correct when their optional arrays are present, 1705–1706. Geometry does not condition these guards on execution_form being actors. |
| Tokens 32; deliveries/handles 64; equal-handle references 63 | Correct, 1710–1717. The reader's 64−1 arithmetic is exact. No uniqueness or valid-reference conclusion follows from the count. |
| Static bindings ≤4; entitlement records ≤12 | Correct for present arrays, 1748–1757. These are separate table bounds. |
| Authority workers/regions ≤8; custody rows ≤32 | Correct, 1759–1768. Optional authority_setup must exist before its required nested collections are examined. |
| Host run/custody operations ≤4; worker/region operations ≤16; ownership ≤5; present integrity errors ≤16 | Correct, 1690–1694 and 1763–1766. The ownership length is the named scope's map entry count; the limits are per scope, not one reply-wide shared operation allowance. |
| Actor visits ≤16 | Correct per retained actor, 1794–1797. |
| Actor required/missing entitlement lists ≤64; native execution observations ≤4 | Correct when equipment is present; missing_requirements remains optional, 1803–1811. |
| Validator expected IDs ≤256 | Correct when the list is present, 1738. This does not assert equality to retained step count. |
| Validator records ≤2×max(1,N); issues ≤N+R+1 | Correct, 1725–1745. N is the number of all retained steps with equal phase_id except an exact query_not_requested missing_reason. An absent missing_reason is included because None differs from Some("query_not_requested"). R is the record length, or zero when absent. The reader correctly avoids a uniqueness/success prerequisite for N. |
| N=0,R=2 permits at most 3 issues; N=5,R=10 permits at most 16 | Both arithmetic illustrations are correct. They describe these capacity guards only; they do not make the constructed records semantically valid or establish native occurrence. |
| Each present ordinary/actor disposition: steps ≤256, issues ≤513 | Correct, 1666–1669, invoked at 1789–1801. 1+2×256=513. This is per disposition, not a single combined ordinary/actor allowance. |
| Present run-claim bases ≤14; step-claim bases ≤16 | Correct, 1662–1665 and 1673–1680. The seven run fields and three step fields match RUN_QUESTIONS and STEP_QUESTIONS at 107–120. Missing claims and missing bases satisfy this size-only check; semantic completeness is separate. |
| Issue observations ≤16 with step_index, otherwise ≤14 | Correct, 1681–1683. This condition is presence of the optional index, not its semantic validity. |
| Present copied boundary/result bases ≤16 for attempts and extensions | Correct, 1771–1786. Both copies are independently bounded. |

The inventory is complete for the current `reply_geometry`, `scope_geometry`, `lifecycle_geometry` and `claim_geometry` bodies. This establishes correspondence of the displayed collection account to those functions; it is not a claim that the entire reply schema or every semantic validator was independently re-audited.

## Admission order, retention and entry-specific consequences

The reader correctly scopes the collection guard to a structurally decoded reply that has reached response-context admission. `run_flow::admit_reply` (332–360) first handles request-delivery failure, then client capture failure, then `reply_version`/`reply_contract`. Exact producer identity is checked at 96–103 before `admission_problem`. Within `admission_problem` (1308–1330), geometry precedes compiled-profile labels and has no exemption for preparation_failure or reporting_failure. A missing reply does not itself invoke geometry.

For a run reaching geometry refusal, the branch at `run_flow.rs:711–749` uses the refused outcome and exit 1, preserves runner_result in `execution_only`, and produces a failed JsonResult. `execution_only` (107–125) supplies null diagnostics. `complete_execution` (752 onward) is reached only through the admitted path and chooses success from exact finished independently of later diagnostic findings. Thus the reader correctly distinguishes refusal from an admitted reply with an integrity finding, and does not infer nonexecution from the refused result.

`cmd_runner_verify` (566–659) reaches the same admission function after its own argument/registry/selection/invocation prerequisites. Its refusal branch sets runner_pid to None, uses the selected refusal outcome and exit 1, and retains both client and decoded result in RunnerVerifyData. Earlier delivery failure remains tool_error/exit 2. An earlier argument/lookup/invocation failure is not a case of a decoded reply reaching this rule. The reader's separate run-diagnostics and verify-PID consequences match these branches. No unqualified run-only field is imposed on verification.

The new local entry labels in the consequence rows and refusal index therefore carry material scope. The reader's interpretation of them is sound. The exact run/verify consequences were source-read here; this phase supplies no new executed verification projection control.

## Producer rules, Mach spelling and phase arithmetic

| Revision category | Adjudication |
| --- | --- |
| Mach input spelling, lines 910/930 | Correctly resolves U42. Fresh PWRunnerAPI constants, request decoder and mapAttemptKindOrNil exact switch agree on mach_lookup/bootstrap_look_up. No mach/lookup alias is introduced. The reader properly leaves implementation history unproved from its document alone; this adjudication's source confirms the correction describes existing implementation. |
| Delivered transfer prerequisites | Correctly a produced relationship. AuthorityCustody::serviceTransfer retains held custody, copied bytes, recipient acknowledgement and equal bytes before assigning delivered. ActorOrchestration copies the observation into the transfer row. |
| Source acknowledgement association | Correctly a produced ordinary-path association, with known-status qualifications intact. recordSourceAcknowledgements requires a completed source slot, nonzero acknowledgement and matching published transfer status; assembly maps known statuses consistently. Admitted plan uniqueness/assignment support is carried from the earlier full source review and freshly checked index construction here. |
| Packaged bound-row equality | Correct. ActorEquipment::bindOne compares observed and expected SHA/CDHash and entitlement equality before bound; test overrides have no expected packaged baseline. Equality in a received row does not repeat this inspection. |
| Augmentation and import relationships | Correct. Dossier constructors at 74–176 establish the exact empty/hash/error relationships. Imports::scan includes a nonliteral-import condition in completeness, so the visible conditions are necessary rather than sufficient. |
| Retained cleanup account | Correct. remove_record at 1532–1655 combines observed absence with empty warnings and final persistence; failed persistence makes complete false. Both retained fields derive from !complete. A reported Boolean is not an independent absence observation. |
| Published installation state | Correct. runner_commands at 451–469 copies record.state after install_record returns; loaded is separately observed. |
| q+1 / p+1 phase ordinals | Correct presentation of the same positional rule. ActorPlan enumerates submitted phases and retains pi (360–381); assignments check phase.index equals its position (135–142). Ordinary prepared actor assembly uses phase.index+1 (349); actorPreparationRefusal independently enumerates admitted request phases and uses index+1 (533–574). |

The producer-role revision does not establish that no self-check exists. In particular `PWRunnerReply.swift:578–593` independently checks delivered prerequisites and source-acknowledgement association on its normal reporting path. The reader expressly preserves that possibility and does not infer universal consumer behavior from a reports node. Its distinction is therefore accepted. Removing dossier/install projection rows from a refusal index corrects their classification without removing their production obligations.

The unchanged nonce distinction is also accepted: the collection gate supplies no request-nonce operand, and the freshly read admission_problem still checks only status/producer/stage after geometry. The earlier full host capture-decoder review remains carried support for the host's distinct nonce guard; that decoder was not freshly reopened in this revision phase.

## The two frozen notation findings

**R1, implication grouping: valid.** Frozen row 4490 and optional-claim rows 4524/4533 conjoin unparenthesized rendered implications. The source checks each guarded requirement independently. The reader's working interpretation matches that source, but a literal reading can leave the end of one consequent unclear. Arithmetic parentheses around 64−1 or 1+2×256 alone do not close logical implications. This is a rendering limitation rather than evidence that the implementation omits later checks.

**R2, omitted execution_form: valid.** The frozen geometry row says not equal to actors without an explicit absence clause. Ordinary production omits the field, and the nearby worker projection explicitly spells out absence. The source's `as_deref() == Some("actors")` establishes the intended default eight-phase bound. The reader correctly infers that intent while declining to claim the literal optional-scalar convention is supplied by this row.

During this adjudication the current shared authoring/renderer already showed the coordinator's later changes: `_expression_text` surrounds each implies result with parentheses, and diagnostics.execution.geometry.plan explicitly includes absent execution_form in the non-actor condition. These selected source lines were read; their hashes are recorded separately in the manifest. They were not the reader's frozen input. This phase did not execute regeneration, inspect a final follow-up reading, or confer reader verification on the later output. The coordinator's report that full source_drift completed remains supplied integration evidence, not this adjudicator's execution credit.

## Earlier uncertainties and support limits

The revision reader's status table is accepted. U42 is resolved in the stated vocabulary. U54 is substantially resolved as a public collection inventory, subject to R1/R2 in its frozen input. U11 and U56 are more precisely attributed to their producing/checking boundary. U37's reserved degraded-association issue remains; size checks do not supply ordinary semantic joins. U15/U21, U18, equipment/authorization distinctions and the nonce/result distinctions keep their prior scope. Maintenance B1 remains outside the runtime contract; no new maintenance caveat is needed here.

The reader correctly leaves collection support at check-read. Fresh reading of typed_geometry_refuses_before_projection_and_retains_every_raw_record (3106–3229) confirms selected excess step/disposition/actor/phase/validator cases, unchanged raw records, a 256-step/513-issue geometry boundary and bounded diagnostic multiplicity. typed_reference_geometry_is_checked_before_claims_and_admission_contexts (3231–3309) adds run/step/issue/copy reference excesses and raw retention. These constructed assertions do not execute every inventory bound, a native large-reply event, or the whole verification operation. Source branch review fills the stated narrower support for those remaining rules without creating executed credit.

The comparison remains one reader sample with prior familiarity and explicit revision cues. The reader did not freshly audit every earlier uncertainty; the complete change set does not warrant declaring every earlier open item closed. It did recognize the intended producer/admission distinction, exact geometry arithmetic and refusal scopes, and it recorded two specific notation problems instead of silently treating its inference as formal transcription.

## Scope ledger and disposition

Freshly read in full: the revision report, all delta hunks, four geometry functions, admission_problem, both named geometry-control bodies, admit_reply, cmd_runner_verify, the selected Augmentation/Imports constructor bodies, remove_record, bindOne, serviceTransfer and recordSourceAcknowledgements. Fresh selected excerpts: frozen contract geometry/phase/source-association passages; resource types; question enumerations; run result/retention branches; install projection; Mach constants/decoder/mapping; normal actor reply self-check; actor assembly, preparation refusal and phase normalization/assignment; the three referenced limits; later renderer/geometry presentation lines. Exact file hashes are in the manifest. Source citations identify body/excerpt support rather than full-file reading.

Not freshly reviewed here: the entire revised contract outside the diff/returns, every current source/check, previous raw execution receipts, full native transport/ABI validity, all independent consumer paths, a rendered browser layout, or any later follow-up reader response. Earlier source and executed evidence retain their previous ownership and limits.

Disposition: accept the revision reader's consequential understanding and both notation findings. Do not amend its resource row. Preserve R1/R2 as findings against the frozen fe58bde input; assess any final presentation follow-up under its own input and response hashes. No product correction or new evidence-grade upgrade is proposed by this adjudication.
