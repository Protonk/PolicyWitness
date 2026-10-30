# PolicyWitness: independent review of the completed workset

Review the evolution of PolicyWitness through the completed workset, including its frozen pytest-first counterfactual, extension experiments, C and Swift refactors, documentation/checking investigations, and the separately authorized repairs that arose during the work.

Bring your own judgment. Determine what the changes accomplished, what the evidence establishes, and what this history teaches us about the proposed pytest-first arrangement. The implementing agent's acceptance records are claims to examine. You may agree with them, identify specific corrections, or conclude that a consequential decision needs reconsideration.

This is the fresh review for which the original engagement preserved its history. Its instruction to leave the counterfactual unevaluated applied to the implementing agent; evaluating that account is now in scope. A pytest migration, production repairs, and writing or preparing a handoff for `docs/CHECK.md` remain outside this assignment.

## Establish the historical frame

Work in the existing [Protonk/PolicyWitness repository](https://github.com/Protonk/PolicyWitness). Read its current root and relevant directory guidance, including `CONTRIBUTING.md`, `tests/AGENTS.md`, and `records/AGENTS.md`. Establish the actual checkout, available history, local evidence and equipment yourself. Preserve unrelated work. Use project planning guidance to organize the review without making preliminary repository tidying a requirement.

The GitHub head inspected when this prompt was prepared was `77eb987554eef10ffa3371ffb21b235097562a78`. Treat that as the completed-workset endpoint; identify later changes separately if the local repository has advanced.

Start with:

- `0c22d256:records/workset/pytest-first.md`: the frozen C0.2 account. Read it before forming your comparison with the implementation history.
- `67fff425:records/workset/checkpoint.md`: final acceptance, recovery index, evidence identities and outstanding resource protections.
- `67fff425:WORKSET-PLAN.md` and `67fff425:WORKSET-EXECUTION-PLAN.md`: the mandate as maintained during execution and its stage criteria. Trace earlier versions where scope or authority changed.

The execution baseline is `bf7e97faab75754efe719b0bad20e83b67762c15`; 69 subsequent commits, including merged branches, reach the inspected endpoint. The preceding workset-preparation commits begin at `0aa1c920`, after `a725702e`. Inspect their amendments when judging what was actually assigned.

The plans and records were intentionally retired. Recover them through git without restoring the packages into the live tree. Read the relevant commit sequences and merge parents: the final net diff omits records created and removed during the engagement.

Useful anchors follow. These are navigation aids, not findings you must endorse.

| Part | Historical anchors | Principal records |
| --- | --- | --- |
| Counterfactual | Initial `6cd868b2`; correction/freeze `0c22d256`; seal `cf0136bb` | `records/workset/pytest-first.md`, `c0-seal.md` |
| Native extensions and public integration | Native correction `b6cac0d7`; crossed comparison `8aa74027`; integration `7426fc09`; seal `29d1c797` | `records/workset/directory-native.md`, `extension-follow-on.md`, `extension-integration.md`, `e2-seal.md` |
| Binding through replay, D1 | `def5de00` through `cd6adaaf`; primary acceptance `7562d24a` | Original `records/check-support/`; inherited material in `67fff425:records/checks-before-check/inherited/` |
| Checks before CHECK, D2 | `7e9d677d` through `f9962120`; merge `bb92c213`; acceptance `96dffd56`; citation correction `590c5e42` | `67fff425:records/checks-before-check/` |
| C refactor, R1 | Design `6e40887f`; candidate `341f9441`; acceptance `96d0328e` | `67fff425:records/workset/c-refactor.md`; original plan recoverable at `6dab4430` |
| Swift refactor, R2 | Stage 1 `72165300`, corrected `9af4d3d1`, accepted `2de5b1c7`; Stage 2 `fd90eee6` | `67fff425:records/workset/swift-refactor.md`; original plan recoverable at `600a7922` |
| Workset F2 investigation and repair | Investigation `edf2c561` through `b471226a`; design `60010034`; implementation `34496c0f` through `4407d0ae`; adaptations `8500baff`; acceptance `600a7922` | `67fff425:records/workset/byoxpc-failure.md`, `f2-investigation.md`, `f2-reservation-design.md` |
| F1 correction | Independent failing expectations `55116788`; correction `8ceb04ea`; acceptance `67fff425` | `67fff425:records/checks-before-check/acceptance.md` and inherited finding |
| Final retirement | Acceptance `67fff425`; deletion `63858221`; retained verification `77eb9875` | Current `tests/RETAINED.json` and its identified local runs |

Finding labels are local to their accounts. In particular, inherited D1's “F2” concerns observation applicability and retention; the later workset F2 concerns BYOXPC transport and retirement. Keep their identities distinct.

## Reconstruct consequential changes

Explain the evolution through the decisions and observations that changed its course. Distinguish planned capability work, behavior-preserving refactors, necessary test adaptations, defects in the checking apparatus, and separately authorized behavioral repairs. Follow the causal connections into actual source and tests.

The following deserve attention:

- **Extension observations and integration.** Examine how native directory modification, absent-child creation, independent effects, and matched/crossed authority informed the public addition. Trace the initial checker corrections and later fixture adaptations. Were unsupported assumptions removed while useful rejection controls were preserved? Keep post-release observations distinct from a guarantee of revocation, and `read-write` authority distinct from an imagined write-only class.
- **C and Swift refactors.** Assess the resulting ownership and readability, and whether the adaptations preserve what tests can distinguish. Concrete leads include copied native include closures and interception, mutation anchors, shared Swift client membership, and source/citation relocation. The Swift Stage 1 visibility failure and Stage 2 citation failures are part of the history. Source-body equality, successful compilation and behavioral evidence establish different things.
- **Documentation and checking.** Examine D1's paper design, historical replays, exposure limits and corrected evaluation equipment, then D2's disposition of those findings. The B1 registry/reverse-index/census proposal was declined; C1–C5 made bounded factual and diagnostic corrections. Assess whether those decisions fit the evidence. Do not treat a faithfully generated statement or an existing citation as proof of the behavior described.
- **F1.** Trace how a check promising to reject extension APIs omitted those names while its controls derived expectations from the same implementation set. Examine the independently authored failing cases, correction and omission-sensitivity controls. Separate this demonstrated checking defect from an unestablished production host violation.
- **Workset F2.** Separate the original unattributed 4097 failures, the later instrumented lost-refusal observation, deliberately controlled reply losses, and the reservation repair. Review the change to acquisition before submission, the prohibition on replay after submission, protocol/reader changes, compatibility decisions, and preservation of native error evidence. The final combined change includes runner protocol 2 and envelope 9, while request 5 and host response 24 remain. It cannot all be described as a behavior-preserving refactor.

Choose where deeper inspection will change the assessment. These leads do not require an exhaustive line-by-line audit of every generated file.

## Evaluate the frozen counterfactual against the work

The counterfactual proposes pytest as the primary collection, fixture, execution and reporting engine, with PW-specific domain adapters and an external session/resource supervisor. It explicitly retains substantial native, lifecycle and evidence machinery. The earlier rejected subordinate pytest trial is historical evidence about a different arrangement.

Recover the actual adaptation records and inspect the corresponding changes. For consequential examples, distinguish work attributable to:

- ordinary collection, selection, fixtures, subprocess setup and reporting;
- native experiments, independent observations and outcome authority;
- resource lifetime, interruption, durable cleanup and evidence retention;
- source membership, mutation reach, documentation bindings and applicability;
- new product behavior, including the separately authorized repairs.

Then ask what the proposed arrangement would have eliminated, simplified, relocated or added. Follow responsibilities across the proposed boundary: moving bookkeeping into a plugin or supervisor still incurs its cost. Conversely, do not assume every current mechanism must survive unchanged just because its underlying obligation survives.

Use the frozen account's difficult scenarios and predictions as claims to examine, while remaining free to choose your own comparisons. Identify where subsequent work supports them, challenges them, or supplies too little evidence. A corrected account may be useful, but label the correction rather than improving the original prediction retrospectively.

Pay particular attention to whether the new demands expose a missing responsibility or an inconvenient boundary in the proposal. Consider the full workload, including failures and repairs. Comparing only the easy Python assertions would miss much of what this workset was selected to exercise.

You may choose bounded experiments or an isolated prototype if a consequential question cannot be settled by inspection. Neither is required. State what uncertainty each experiment addresses and what its result can establish. Use verified framework behavior for any decisive claim about pytest; the frozen proposal explicitly left exact version and API feasibility unestablished. Do not restart the rejected subordinate trial by default or turn this review into a migration project.

Measures such as code volume, elapsed time, fixture counts or case counts can help a particular comparison. Explain what they include and what they miss. Reach a qualified architectural assessment even if the evidence does not support a migration recommendation.

## Review acceptance and evidence applicability

The final claim is 229 distinct required cases supported by reconciled results, with caller-auth separate. It is not a claim that one complete battery passed.

Trace the chain from the original full-run failures through replacement credits and final retirement verification. The checkpoint accounts for 212 retained full-run passes, 15 F2 replacement results and two F1 source results; the final retirement entry replaces the last two with its current source checks. Inspect the attached credit accounts and actual dependencies before accepting reuse. Examine why the required selection changed during the work. Avoid adding overlapping results or treating later success as a correction to an earlier run's observations.

Distinguish mechanically established identities from judgments that changed files did not affect an executed path. Review substantive claims against source, independently authored controls and available raw evidence. An acceptance record, manifest entry or clean working tree does not by itself establish those claims.

Raw runs are gitignored and may exist only on the local machine. Establish which referenced bytes are available. A committed pin is evidence of retention intent, not a substitute for its contents. If something is unavailable, identify the conclusions that depend on it and continue the parts of the review that remain supportable.

Inspect whether the experiment's sequence remained recoverable: initial counterfactual freeze, extension seal before refactors, D1 before D2, and attributable integration of concurrent work. Where recorded, examine how findings reached the user and how changed authority entered the plans. Do not infer private conversation, effort, or quality of oversight from commit count or orderly prose.

The initial expectation of perhaps three to six retained runs was not a quota. Assess the actual retention choices in light of discoveries and replacement evidence. Likewise, assess the usefulness and recoverability of the records without treating their volume as a measure of rigor.

## Preserve the evidence while reviewing it

Keep historical source, records and runs intact. Use separate worktrees and fresh output for new experiments, following repository locking, signing, dispatch and cleanup rules. Never unlink the checkout lock or bypass retention helpers. Do not prune, unpin, rewrite or regenerate the previous engagement's evidence as part of this review.

The checkpoint identifies resources needing special preservation:

- `/private/tmp/pw-extension-directory-uge3532e`, associated with an unwitnessed worker exit;
- the baseline comparison worktree/app at `/private/tmp/pw-f2-stage1`;
- the unrelated pytest-evidence worktree and protected ownership/cleanup records.

Establish their current status without assuming that elapsed time, verified service removal or a clean repository proves a worker's exit. Consult the checkpoint and owning records before operating on those resources.

If you delegate, give assignments fixed source states and bounded questions. Coordinate any execution so one assignment cannot change another's experimental inputs. Reconcile findings before accepting a combined conclusion.

You may create review records and disposable experimental equipment. Changes to production, existing test expectations or permanent behavioral documentation require a separate decision. Report a newly exposed defect with concrete evidence and its consequences; do not repair and document it merely to finish this review.

Keep substantial committed investigative material under `records/`, associated with the review's plan where needed, and follow the repository's record and retirement conventions. Do not add a permanent named report elsewhere or resurrect the retired workset.

## Return an independent assessment

Return a cohesive report that explains:

1. What materially changed, why it changed, and which decisions remain well supported.
2. What the evolution reveals about the frozen pytest-first proposal, using concrete adaptations and their obligations.
3. Whether the acceptance and evidence-reuse claims withstand review, including any specific gaps or qualifications.
4. Which defects, architectural questions or follow-up experiments warrant my attention, and what can reasonably be left alone.

Use commit-and-path references and run identities so another reader can recover the basis for your conclusions. Distinguish your observations, the implementer's reports, and your inferences. Identify material limits of your review and any new experiments you performed.

A supported conclusion may be that the work is sound, that a bounded correction is needed, or that an important decision should be reopened. Finish when the consequential claims have an explicit assessment and remaining uncertainty is localized. A favorable verdict, a recommendation to adopt pytest, and a new implementation plan are not required deliverables.

