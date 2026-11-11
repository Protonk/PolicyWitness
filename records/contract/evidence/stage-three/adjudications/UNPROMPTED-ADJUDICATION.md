# Stage-three unprompted reading: truth and readability adjudication

The new reader preserves the important observation and interpretation boundaries. Its 79-entry journal also exposes two concrete account defects: an incorrect admitted Mach-attempt spelling (S3-T01, corrected by the coordinator) and missing public response-admission collection bounds (S3-T02, private correction supplied). These findings qualify acceptance of the account. The other residual questions mostly identify explicit evidence limits, reserved decisions, or implementation detail outside the displayed public meanings. Their uncertainty should not be removed by inventing guarantees or adding unrelated negative-space prose.

This is one raw-text reader sample and a targeted source adjudication, not an exhaustive implementation proof or a rendered usability study. No prompted stage-three answer was opened before this report was completed. The isolated reader was not contacted.

## Inputs, conditions and evidence grades

- The entire frozen stage-three journal, all 79 entries and its complete Close-out, was read: `/private/tmp/pw-contract-stage-three-isolated-reading-20261111/JOURNAL-FROZEN.md`, SHA-256 `64c9f500057b17f3e2f2d64363da797c3ed90cd81b2e454395054141af55eba0`. Its contract input has 5,747 lines and SHA-256 `e1aafb723c46261bffe5c4c940abd81dae222ee1aa6ff53067428ef4c17c9814`; both hashes were independently checked here.
- The journal reports one forward raw-Markdown pass, append-before-advance, no revised entries, no contract returns, no links or source checks opened. TASK.md was its other input; it later reread its own headings/uncertainties for Close-out. Its inherited context included repository-location/AGENTS orientation, which it says it did not use as contract evidence. Portions were 47–90-line groups, sometimes split across headings, tables or sentences, rather than uniformly paragraph-sized. That is a recorded method limitation, not an access violation.
- Both complete stage-one adjudications were read. For the stage-one journal, this comparison read the full heading/term search, full Close-out and selected original entries 20–21, 33–35, 67–71 and 79–86. It did not freshly reread all 101 entries. The full journal had been read during the earlier stage-one adjudication; that earlier coverage is carried evidence, not a new reading here.
- `records/contract/STAGE-TWO-DECISIONS.md` was read across its full scope, including all R/G dispositions, adopted evidence scopes and seven reserved choices. Truncated tool portions were reopened in smaller ranges. Its completed executions are inherited decision/evidence records. The prior P4/P5/P6/G20 raw audit was this adjudicator's own earlier work; it was not re-executed here.
- The complete original 16-KB producer-role revision diff was read before the coordinator added S3-T01. That revision moved seven producer relationships from `checks` to `reports`, with corresponding derived views, and yielded SHA `5bf909e329b1b57774ba9c4c723d04ea3137974cdeb752892bcad24fcd827f82`, independently checked here. The coordinator subsequently reports applying S3-T01 and regenerating SHA `33f01feb258090cfe9e34274521af1c399d5976c968c9a2a611fbd8938b2b13f`. Neither revised input was the reader's unprompted input. The original role-only revision is now preserved as `producer-role-revision.patch` / `CONTRACT-producer-role-revised.md` in the coordinator's private review directory.
- Fresh **source reading** below means the named selected source bodies were opened. Fresh **check reading** means their actual assertions were opened. It supplies no execution credit. **Carried execution** refers only to the earlier scoped receipts or the coordinator-adopted stage-two record; a reader's accurate summary does not independently verify those runs.

No shared file, product, test, build, generator or native operation was executed or modified by this adjudication. Private patch construction, expression/Python AST parsing, hashes and `git apply --check` are document/candidate checks. The coordinator owns strict model loading, rendering, source-drift and adoption. All `/private/tmp` paths here are local private artifacts, not durable repository evidence promises. No repository inbound link was added.

## Material truth dispositions

### S3-T01 — Admitted Mach-attempt spelling

The original contract at lines 910 and 930 claimed a closed `mach` family and `mach / lookup` pair. Its operation-relation table at 2728–2735 instead used `mach_lookup / bootstrap_look_up`. The reader noticed this at entry 37/U42 and correctly withheld treating the second spelling as a newly admitted pair. The account was wrong, not merely underexplained.

`PWRunnerRequest.swift` directly decodes the `kind` and `action` strings. `PWRunnerAPI.swift:23,35` defines `mach_lookup` and `bootstrap_look_up`; `CWorkerRequestPlanning.swift:111–140` admits that exact pair and returns nil for other pairs. `ProbeRunner.swift:119–121` and `ActorPlan.swift:437` turn that nil result into whole-request `unsupported_attempt`. No alias conversion occurs on these admission paths. `CWorkerComparison.swift:125` maps the same actual pair. `AttemptOutcomeMappingTests.swift` has the positive constant-based pair and checks table agreement, with several unsupported neighbors; it does not specifically test rejection of the erroneous `mach/lookup` literal pair.

Correct `probes.attempt.kind.values` and the `probes.attempt.operations` table row to the actual accepted spellings. The coordinator reports that these two authored edits and regeneration are complete. This review supplies source/check-read support, not a new native or admission test. Product acceptance stays unchanged. Stage-one journal entry 21 had repeated the incorrect `file/mach/sysctl/exec` vocabulary without resolving this discrepancy; the stage-one adjudication missed it. The new sample therefore discovers an inherited defect rather than establishing that stage-three conversion introduced it.

### S3-T02 — Public response-admission bounds are omitted

U54 is a missing public admission account. The original/current `diagnostics.execution.admit` says that geometry bounds collections before semantic joins but does not state the actual carried-record limits. Request limits alone do not supply lifecycle reference, issue, equipment, ownership-map and scope-operation bounds. Exceeding these limits changes public admission and the operation result, including on preparation/degraded replies; this is not merely a private memory-layout question.

Fresh source reading covered `claim_geometry`, `lifecycle_geometry`, `scope_geometry`, `reply_geometry` and `admission_problem` in `controller/src/porcelain_admission.rs:1662–1813,1308–1332`; `run_flow.rs::{reply_contract,admit_reply}`; and `runner_commands.rs::cmd_runner_verify` through its completion record. Both run and verification use the same geometry gate after their earlier delivery/capture/identity admission. Geometry precedes profile-label checks. A refusal retains the decoded reply, selects `malformed_runner_response`, false ok and exit 1. Run suppresses diagnostics; verify retains its own record and leaves `runner_pid` null. Earlier delivery failure still owns its separate tool_error/exit 2 branch.

The complete inventory read from that guard is:

| Carried scope | Actual bound and applicability |
| --- | --- |
| Top-level plans | Phases at most 16 only when execution_form is exactly actors, otherwise 8; steps at most 256; present extension events plus steps at most 256; sum of every phase's action_ids counts at most 256. |
| Actor/transfer/resources | Present actor rows at most 8; transfers at most 64; present resource table has at most 32 tokens, 64 deliveries, 64 handles; each handle raw_equal_handles has at most 63 entries. These counts precede relationship validation. |
| Each present phase validator | Expected-step-ID list at most 256. Let N count every retained step whose phase_id equals this carried phase_id and whose missing_reason is not query_not_requested (absent missing_reason is included); let R be present record count, otherwise zero. Records at most 2 × max(1,N), association issues at most N + R + 1. Repeated phase labels are not deduplicated for this count. |
| Top-level equipment | Present binding list at most 4, entitlement-readback list at most 12. |
| Present authority setup | Worker scopes at most 8, host region scopes at most 8, host custody scopes at most 32. Host run and each custody scope have at most 4 operations; each worker/region scope at most 16. Every scope has at most 5 ownership entries and, when present, 16 integrity errors. |
| Present ordinary/actor disposition | At most 256 disposition steps and 513 issues. Each present run claim basis has at most 14 references; each present step claim basis at most 16. Each issue has at most 16 observations when step_index is present, otherwise 14. Missing disposition/claims/basis are left to their applicable semantic checks; this guard does not make them required. |
| Lifecycle copies | Each present ordinary-step attempt lifecycle and extension-event lifecycle has at most 16 basis references in each boundary/result claim, when its basis is present. |
| Each actor | Visits at most 16. If equipment is present, required entitlements and present missing requirements each at most 64; execution native observations at most 4. |

The private successor is `geometry-successor/geometry.patch` with frozen before/after and manifest. It adds a single shared `diagnostics.execution.geometry` check with concrete typed conditions, uses twelve existing limit IDs and structured local cardinalities, and references it from run admission and `installation.commands.verify`. No new limit manifest record or free relationship is needed. Three subordinate groups are condition nodes, so one actual controller-index row is added; its explicit source-drift expected set is updated. The initial `geometry/` candidate remains preserved.

The two opened controls `typed_geometry_refuses_before_projection_and_retains_every_raw_record` and `typed_reference_geometry_is_checked_before_claims_and_admission_contexts` assert selected excess tables/reference lists, retained raw equality and an accepted count boundary. They do not independently execute every inventory cell or every verify branch. The successor owner is check_read with that limit; no executed-grade upgrade is proposed. Private AST/limit-ID/applicability checks passed; model/type loading and rendering remain coordinator-owned.

### S3-R01 — Supplied producer-role correction and inference risk

The frozen input labels seven output relationships as checks at their producer projection boundaries: delivered/source-ack transfer relationships, packaged bound-row equalities, augmentation and import dossier relationships, retained cleanup and installed-state copy. Four therefore also appeared in the derived Controller findings table. The supplied revision correctly presents those production relationships as reports and the retained relationships as child conditions or an assignment.

Freshly reopened `AuthorityCustody::{serviceTransfer,recordSourceAcknowledgements}`, actor result assembly, `ActorEquipment::bindOne`, `dossier::{Augmentation,Imports}`, `runner_manager::remove_record`, and install result construction support those production meanings. The transfer producer observes its source's completed slot and matching nonzero acknowledgement; assembly carries corresponding event/transfer labels. Packaged binding checks actual digests/signing/entitlements before setting bound. Dossier constructors establish their output fields; cleanup publishes retained_record from the same completion decision as cleanup_retained; install copies the returned record's state.

Some host relationships also have real later self-checks: `PWRunnerReply.swift:585–592` checks delivered observations and source acknowledgement. The correction must not be described as proving that none of those relations is checked anywhere. Its purpose is to identify the specific production rule being represented. The reader's entries 28, 53, 68 and 73 describe the output relationships correctly, but entry 79 accepts the closing findings index generically. That does not refute the index's misleading implication of additional controller findings. The unprompted sample never saw the corrected rendering, so it cannot validate the revision's readability.

## All journal entries: bounded grouped disposition

These groups cover entries 1–79. Acceptance concerns the recorded understanding and stated source/evidence boundary; it is not fresh source verification of every field.

| Entries | Disposition |
| --- | --- |
| 1–6 identity, roles, observations | Accept distinct public/wire/worker identities, source/configuration/equipment separation, nested artifacts and evidence-qualified effects. Component meanings arrive before the main procedures. Support-grade and equipment terms still travel long distances. |
| 7–12 requests, selection, policy, attempts | Accept entry-specific admission, observed duplicate differences, helper/worker separation and effect boundaries, subject to S3-T01's wrong Mach vocabulary. Native semantics remain observed, not inferred from the request alone. |
| 13–17 actors/extensions | Accept one worker retained across visits, declaration versus resource success, custody/delivery/source acknowledgement separation and platform-scoped examples. No release/revocation equivalence is inferred. |
| 18–24 transport/wire/validator | Accept no replay, original deadline, delivery/retention precedence, exact grammar and mode-specific meanings. Native cap-interval and complete capture predicate questions remain bounded. Constructed wire/writer controls are not promoted to native transport frequency. |
| 25–31 helper/imports/extensions/refusal | Accept independent compilation, read-specific import closure, exact fallback eligibility, resource publication and first-reached refusal. Produced relations are understood despite S3-R01's misleading original labels. |
| 32–38 host summary/steps/fresh operations | Accept finished versus native success, rich/minimal retention, exact association and first-failure aggregation. U42 catches S3-T01; U43 correctly expects a separate native-record validity check rather than accepting aggregate fall-through as complete validity. |
| 39–47 worker/lifecycle/validator/exec | Accept independent publications, owned wait status, unresolved live absence, D1/D5, exact collector joins and separate exec collection/request/reap. Full native header/numeric map and every malformed-record truth table remain delegated. |
| 48–52 actors/application/gates | Accept preparation/degradation scope, observed apply failure, late applied publication beside setup timeout, natural owned ending including signals, actor-local ordinals and global failed-gate cancellation. Current behavior does not decide the reserved cancellation policy. |
| 53–59 equipment/authority/profile | Accept sealed/static/live association, attempted-prefix limitations, independently acquired setup cells and host versus controller receipt responsibilities. Missing manual shared-name recovery procedure supplies no cleanup authority. |
| 60–66 result/diagnostics | Accept admission refusal versus finding, valid supported conflict, worker-local versus aggregate withholding, independent actor projections and exact-finished success. U54 correctly identifies the incomplete admission-capacity account. Selected subject paths identify inspected assertions without closing R-34. |
| 67–69 dossier/provenance | Accept held source, scanner-specific completeness, optional digests, shipped-role null descriptions and selected-file versus live-image scope. Complete compiler/SDK configuration is not reconstructed from these fields. |
| 70–76 installation/cleanup | Accept durable ownership before actions, Pending verify, result versus presence/retirement, historical metadata, exact service observations and nominal wait accounting. Dynamic-branch/source-only coverage remains visible. |
| 77–79 support/indexes | Accept eventual support-grade definitions and seven explicit gaps. Index recognition demonstrates navigation in raw text, not complete operational verification or rendered hierarchy; original producer-check pollution is S3-R01. |

## Disposition of every uncertainty U01–U58

“Answered” means the displayed commitment was correctly understood; it does not mean every native event was independently executed. “Detail boundary” identifies legitimate omitted implementation or workflow detail. “Limit” preserves bounded evidence/current knowledge. “Reserved” preserves a maintainer choice.

| Item | Adjudication and remaining consequence |
| --- | --- |
| U01 schema/results | Answered by request, report and diagnostics sections. No new correction. |
| U02 component roles | Answered with separate controller/client/host/worker/helper responsibilities. No shared-sandbox inference. |
| U03 build/configuration/SDK | Detail boundary. Reported build stamps, provenance and equipment observations are defined; reconstructing the full compiler/SDK environment is build evidence outside these records. Do not add an unrelated contract disclaimer or invented provenance field. |
| U04 support grades | Answered, but only formally defined at the end. The early links already target the grade definition; the reader's provisional reading was correct. A reading-order cost, not evidence conflation. |
| U05 canonical shapes/tag inventory | Detail boundary. The complete machine schema/history inputs are referenced; the text supplies grammar and field meanings. This sample did not follow them and cannot validate their sufficiency for a new codec. No extra admission guarantee follows from that silence. |
| U06 worker layout | Detail boundary. Complete internal shared-memory bytes/magic/layout are not a public specimen schema. Publication and public evidence meanings are stated; do not duplicate the ABI to answer an unrequested implementation project. |
| U07 live association | Answered: actor static/live binding and ordinary file-read dossiers have different association strength. |
| U08 generator outputs | Answered by the immediate continuation. Portion splitting, not missing meaning. |
| U09 barriers/schedules/overrides | Answered at the operational level, preserving admitted override applicability and source-versus-observed values. |
| U10 raw retention | Answered: captured prefixes, rejected capture representation and rich/minimal fallback retain distinct evidence. |
| U11 checks/withholding | Answered current scopes. Broader withholding is reserved R-34, not an ambiguity to hide. |
| U12 native effect/fresh aggregate | Answered for reported operations, subject to corrected input spelling S3-T01. Open-only versus transfer/close evidence remains explicit. |
| U13 lifecycle/cause | Answered for owned ending, reach/publication and validated host-cleanup chain. No generic sandbox-cause inference. |
| U14 request capacities/refusals | Answered request-facing counts, applicability and refusal consequences. This does not answer the distinct response capacities in U54. |
| U15 augments/dossier | Answered held-source, augmentation and scanner/read boundaries. |
| U16 selection/entitlements | Answered operation-specific selector, Pending/verify and Boolean-true readback rules. Reads retain their time/source scope. |
| U17 caller/override authority | Answered connection authorization and packaged-before-fixture ordering; fixture observations retain their provenance. |
| U18 profile validation | Answered host nonce/payload/input checks versus controller label-only admission. Accept the reader's narrowing. |
| U19 SBPL/native parameters | Limit. Arbitrary native compiler semantics are not promised by accepting bounded string inputs. Stage-two selected parameter observations do not prove every expression/platform. |
| U20 helper/fallback | Answered decoder, independent verdict and admitted-client-xpc_error trigger. |
| U21 native imports | Limit accepted in G11/G34. Literal walks and independent read times do not establish atomic native dependency closure, collision precedence or macros. Preserve the actual scoped observation. |
| U22 prediction/realpath | Answered exclusions and separate after-orchestration forms; no runtime object equality inferred from strings. |
| U23 exact joins/query_first | Answered unique native-answer and ordering chain; failed other queries need not disqualify this probe. |
| U24 exec predicates | Detail boundary after the public sequence, budgets and owned leader scope are stated. Complete malformed-exec validation is source detail; a reader cannot infer descendant absence from leader reap. No blanket cleanup promise is missing. |
| U25 extension grammar/exec exclusion | Answered participant and resource rules. |
| U26 termination dependencies | Answered present behavior and timely natural-owned conditions; R-37 cancellation reach remains reserved. |
| U27 resource/custody/native statuses | Answered; declaration, candidate handle, host delivery and later access remain separate. |
| U28 manual cleanup/all descendants | Detail/workflow boundary. The contract requires current ownership of a retained shared-memory name and exposes unconfirmed states. It grants no arbitrary-name cleanup or all-descendant absence claim. Any user recovery procedure belongs to its operational guide and needs its own evidence. |
| U29 reservation/invocation | Answered once-only invocation and uncertainty after transport loss. Missing receipt is an actual unknown, not a documentation defect. |
| U30 native cap interval | Accepted G21 limit. Production writer controls and controlled receiving faults do not establish native XPC delivery across every size between retention/frame caps. |
| U31 capture consistency predicates | Detail boundary. Public checked families and failure precedence are stated; complete UUID/chronology/terminal truth tables remain in the receiver implementation. No full independent receiver implementation was promised by this reading. |
| U32 stdin precedence | Answered pipe acceptance versus receipt and delivery failure precedence. |
| U33 porcelain | Answered grammar/identity/storage/projection. Exact schema inventory remains U05. |
| U34 reporting fallback | Answered rich/minimal/empty paths and retained association limits. |
| U35 validator framing/limits | Answered collector bounds and exact rejected context. Response-admission derived validator counts are separately supplied by S3-T02. |
| U36 helper stages/walk bounds | Answered native-stage and inventory meanings. |
| U37 degraded associations | Reserved R-36/G25. Current form and independent lifecycle duties are defined; stronger ordinary actor/phase/resource association is not silently adopted. |
| U38 echo/later failure | Answered safe metadata, channel boundaries and fallback retention. |
| U39 full host classifier | Detail boundary. Outcome scope and precedence are stated, with full live orchestration/classifier procedure in cited source. The reader correctly avoids recalculating arbitrary native history from a summary alone. No changed result meaning established. |
| U40 path forms | Answered exact submitted operands and host after-orchestration forms. |
| U41 permission shape/cause | Answered explicit classification precedence and limited attribution. |
| U42 Mach spelling | Material wrong public input vocabulary, S3-T01. Corrected authored spellings are required; no alias/product change. |
| U43 reached fresh fields | Correct expectation of a separate validity check. Freshly read porcelain_native::fresh_read_problem requires read/stat/close after a successful open and checks range, content/count and aggregate agreement; failed open forbids subsequent fields. The aggregate producer table is not complete malformed-record admission. Keep the native check-family ownership; no false fall-through acceptance is established by the journal. |
| U44 clock domains | Limit/definition boundary. Named origins/domains and local allowances are provided. No general cross-clock conversion or global elapsed bound exists in the displayed contract to reconstruct; adding one would invent a commitment. |
| U45 publication/code map | Detail boundary. Open raw numeric values and selected meaningful codes remain preserved. Full private ABI maps belong to the native source; unfamiliar values do not acquire guessed lifecycle meaning. |
| U46 claims/summary combinations | Answered state/projection/vocabulary meaning; exact exhaustive combinations remain implementation detail. Reserved R-07 preserves the unresolved/inapplicable merge question. |
| U47 late application | Answered exact precedence and scheduling eligibility distinction. Native late-setup observation and constructed classifier corpus have separate stage-two evidence. |
| U48 inventory/static/live binding | Answered scoped association chain. |
| U49 authority cells/integrity | Answered independently acquired scope decisions/operations and primary support. |
| U50 Security failures | Accepted G30 limit: normal signed association and constructed failure controls do not establish spontaneous native error frequency. Initial orchestration-clock nil likewise retains its narrower source grade. |
| U51 operation slots/recovery ref | Answered registered operation meanings and retained ownership reference. Manual procedure remains U28. |
| U52 opaque-bytecode interpretation/replay | Outside promised operation. Preserve/hash/capture identity is defined; no portable decoder/replay operation is introduced. Do not add a defensive paragraph denying unrelated capabilities. |
| U53 success/findings | Reserved R-20/G31. Current exact-finished success is clear; exit 0 remains insufficient as an integrity verdict. |
| U54 response geometry | Material missing admission limits, S3-T02. Complete source-backed inventory and shared run/verify candidate supplied above. |
| U55 selected-file baselines | Answered null shipped rows, unique role baseline and unavailable comparison operands. |
| U56 durable recovery | Answered ownership, actions, observed absence and successful retirement publication. |
| U57 service observation | Answered exact successful print/absence diagnostic/unique executable/ownership distinctions. |
| U58 dynamic output coverage | Accepted G38/source-shape evidence limit: every dynamic branch does not have an independent mutation observation. Source agreement supplies its stated scope, not a fictitious full branch execution. |

The seven explicit Known gaps remain ordinary-build history (R-29/G02), degraded associations (R-36/G25), cancellation reach (R-37), success/findings (R-20/G31), unconfirmed vocabulary (R-07), independent semantic classifiers (R-15), and reply-wide withholding scope (R-34). The reader preserves all seven. Its unrelated uncertainty about arbitrary compiler behavior, manual shared-name cleanup or portable bytecode replay does not create a new maintainer gap by itself.

## Comparison with stage one and misleading-inference risks

The strongest improvement is specificity at previously unsettled boundaries. Stage-one entries 67/84 could only retain broad reader disagreement; stage-three entries 49/64 distinguish producer-grounded scope, the actual constructed corpus, independent lifecycle assessment and JSON-only normalization. Stage-one entries 71/86 had no structured finding reference; stage-three entry 66 identifies selected positional assertion paths and keeps their withholding scope separate. Stage-two execution adds evidence to those definitions, rather than converting all readers into equivalent validators.

Stage-one duplicate-key uncertainty is replaced by stage-three entry 8's tested entry-dependent observations. It explicitly declines to generalize them to all inputs/platforms. Development review now has the adopted available-snapshot/target-definition procedure. Version trailing arguments, helper/worker verdict difference, actor timeout override applicability, Pending verification and layered cleanup location rules are stated as retained current behavior. The new reading does not continue treating those adopted decisions as unresolved acceptance choices. The seven specifically reserved choices remain visible.

Previously missing diagnostic/profile/exec/validator/transfer/readiness/grace/inspection quantities are now usable in the journal. U54 identifies the remaining distinct response-context gap rather than repeating the old entire quantity deficit. S3-T01 demonstrates that the richer text and earlier source review still did not catch every public typo: new contrast between admission and comparison tables exposed a false spelling already believed in stage one.

The fourteen earlier prompted silence topics mostly have unprompted support here: exact identity versus stamps/build/equipment, helper admission, signed overrides, open refusal vocabulary, exit versus execution, held serialization and entry-specific ordering are all distinguished. Three limits persist. First, neither raw journal tests rendered hierarchy/link use. Second, named support grades and examples do not verify actual battery selection for an arbitrary future run. Third, the shipped guide and its recovery workflows were not opened; agreement and stage-four usability remain untested. This report does not preempt the new separate prompted round.

Two recurring reading costs remain visible. Support grades are formally defined near the end despite early linked use; equipment association, dossier and profile-capture terms span long sections before full operational meaning. More specifically, ordinary semantic reply is first used before its formal definition at the diagnostics families, and the new Close-out still says it “eventually” distinguished this from ordinary request form. The earlier reader explicitly had the same temporary ambiguity. A positive local definition or direct reference at the first use would reduce a reproducible inference risk; no new semantic exception is needed. This is a readability proposal, not another established wrong outcome.

The producer-role/index correction (S3-R01) deserves direct revision reading because the original labels could suggest recipient validation where the rule actually describes produced values. The reader's correct summaries do not prove that this risk is absent for another user. Conversely, U43's concern should not be answered by relabeling producer aggregate cases as recipient checks: actual native-record validation remains separately owned. The new response-bound check should be assessed in the same way—actual shared admission, with run and verify completion consequences shown at their own scopes.

One cannot infer that 79 entries are easier than 101: the new contract is larger, the new reader used larger portions, the readers and prior exposures differ, and both were constrained against following links. Changes of mind often resolve deliberately withheld expectations rather than mistaken beliefs. The journal supports qualitative findings about these particular routes, not a measured readability improvement or a universal misunderstanding rate.

## Source/check reading and remaining work

Fresh source bodies opened for concerns: PWRunnerAttempt decoding and wire constants; mapAttemptKindOrNil; ordinary/actor meaning admission; operation comparison; the relevant AttemptOutcomeMappingTests table and assertions; all geometry helper bodies and admission caller joins; both named geometry control bodies; selected fresh_read_problem; AuthorityCustody serviceTransfer and source acknowledgement; selected actor event/transfer assembly; ActorEquipment bindOne; Augmentation and Imports constructors/scan; remove_record; install and verify completion construction; selected host transfer self-checks. Authored nodes, model expression/context/render rules, existing limits, applicable instructions and source-drift explicit index assertions were read to prepare the private candidate. The model was not imported or run.

Carried support: earlier full stage-one source adjudication; the seven-file/ten-file stage-three source reviews; stage-two P4/P5/P6/G20 raw/source audit and bounded native/effect receipts; other stage-two audit conclusions as adopted in STAGE-TWO-DECISIONS. This task does not refresh every raw artifact, all native classifiers, the entire capture predicate body, all build/history sources, every owner citation, the whole current contract, a rendered page or the guide.

Adoption requires coordinator review of S3-T02's exact inventory, imported types, run/verify applicability, new index expectation and rendered result. S3-T01 and the producer-role correction need to be included in the reader's later revision input. The prompted answers and revision response must remain separate artifacts with their own inputs and adjudications. The unprompted journal remains unchanged.
