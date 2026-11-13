# Actor setup and application evidence cycle

## Pass 1 — Reading questions and ownership

This cycle follows the submitted declaration, worker publication, host
assessment and reader validation for actor setup and application. It excludes
a general actor-lifecycle, extension-transfer or termination redesign. Reading
clarity is the criterion; neither fewer words nor fewer presentations is an
independent goal.

1. What do `mode`, `setup_status`, `applied`/`application_count` and
   `application.state`/`basis` each establish?
2. How can application be observed while setup remains unavailable, and how
   do apply and deliberately unapplied actors become eligible for queries and
   actions?
3. What do ordinary and degraded readers validate, and what facts remain
   without certifying actor associations?

| Question and exact reading defect | Authoritative owner and current presentations | Checks and proposed treatment |
| --- | --- | --- |
| 1. The guide's top-level field list calls `application` a “classified setup/application account” but does not explain its state/basis pairs. A reader can mistake `observed` for successful application, `application_count: 0` for proof of no call, or an unapplied declaration for an observed ready worker. | [Actor request](../../docs/contract/13-actors.surface.md) owns submitted mode. [Actor evidence](../../docs/contract/33-actor_evidence.surface.md), especially actor fields and Application assessment, owns the separate report meanings and ordered classification. The guide lists the fields; the runner and worker tours distinguish publication, application and disposition without walking through these readings. | `actorApplicationAssessment` in [PWRunnerAuthoritySetup.swift](../../runner/Sources/PWRunnerCore/PWRunnerAuthoritySetup.swift), worker `main` in [pw_probe_runner.c](../../controller/tools/pw_probe_runner/pw_probe_runner.c), and `assembleActorReply` in [ActorOrchestration.swift](../../runner/Sources/PWRunnerCore/ActorOrchestration.swift) implement the stages. [ReaderCorpusTests](../../runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift) has eleven source-backed constructed application pairs, wrong-pair controls and contradictory-publication controls. Add one guide interpretation section; link the field list to it. Keep the full ordered algorithm in its existing contract owner. |
| 2. The late-application example appears inside extension coverage, while the general field list offers no route to it or to setup eligibility. “Application observed” and “setup established” require a reader to reconstruct the distinction across documents. | Actor evidence's Setup deadline and later application owns the exception. Its Phase collection and execution and the equipment surface own additional conditions. The extension source/guide already carries the useful `setup_timeout`/later application example; runner README describes the producer schedule. | [ActorScheduler](../../runner/Sources/PWRunnerCore/ActorScheduler.swift) owns `setupDisposition`, `usable`, schedule traversal and final collection. [ActorSchedulerTests](../../runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift) checks no collection/activation/slot completion after setup expiry despite a later applied publication; [ActorReplyTests](../../runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift) retains the assembled counterpart. These controls use a 40 ms setup allowance, 150 ms pre-ready delay and 1000 ms grace: they do not establish general timing. Explain the contrast beside the guide's field meanings, and give the producer stages and source route in runner README. Link to the existing complete query-order account rather than duplicate its eligibility algorithm. |
| 3. The guide explains degraded check families elsewhere, but a reader arriving through `actors[].application` is not led to that scope. CONTROLLER already clearly separates retained actor projections from certified attribution; its setup/application list does not identify what the application reader actually checks. | Actor evidence's Reader applicability and Application classification separate production from recipient checks. [Diagnostics](../../docs/contract/41-diagnostics.surface.md) and [reply failure](../../docs/contract/30-reply.surface.md) own check scope and fallback form. [CONTROLLER](../../docs/CONTROLLER.md#receiving-and-evaluating-evidence) and the guide's result-reading section are useful audience explanations to retain. | [porcelain_actor.rs](../../controller/src/porcelain_actor.rs) `identity`/`application`, [PWRunnerReply.swift](../../runner/Sources/PWRunnerCore/PWRunnerReply.swift) `actorExtensionEvidenceProblem`/`validateForReporting`, [consumer.py](../../tests/lib/consumer.py) `_validate_reply`/`_validate_actors`, and [lifecycle_oracle.py](../../tests/lib/lifecycle_oracle.py) `check_actor_records` preserve their separate scopes. ReaderCorpusTests and its Rust/Python replay exercise constructed ordinary/degraded neighbours; they do not establish native occurrence. Add a short local scope paragraph and navigation in the guide, and a source-linked application-reader explanation in CONTROLLER. Preserve its attribution caveat and the existing support owners. |

No new bug is established by this map. The inspected producers and readers
explain the selected contrasts without a public meaning or owner decision.
The recently corrected apply-mode/unapplied-setup mismatch is an existing
constructed reader control, not evidence of a native scheduler occurrence.

## Proposed sequence and verification

Pass 2 adds the guide reading path and focused producer/reader navigation in
runner README and CONTROLLER. Retain the authored contract's complete
classification and adjacent evidence limits; no public meaning, interface or
support-owner change is proposed. Review every added explanatory claim against
the cited producer and reader, including preparation refusal and degraded
records. The guide must remain usable as its standalone distribution copy.

Pass 3 checks whether an existing app-owned example materially helps these
questions. The extension specimen demonstrates declared modes but does not
reliably produce a failed apply or late publication. Prefer retaining that
specimen and using field contrasts over introducing a new example command,
catalog or maintained algorithm table.

Pass 4 reviews the selected paths' support presentation and qualifications.
Keep constructed application-pair coverage, shortened-budget native timing
coverage and source inspection distinct. The existing contract support view
already derives detailed citations from each owner; retain it unless a named
reading defect requires more.

After edits, regenerate any owned copies with their generator and verify
`generate_limits.py --check` and `generate_contract_stamps.py --check`, review
the public snapshot diff, and run `source_drift` through the dispatcher. Root
coordinates those checks, commits, any build and output cleanup. No runtime or
test mutation is proposed; any concrete new counterexample will be reported
with producer/reader path and discriminating observations before changing it.

Completion will record the resulting three paths, retained arrangements,
maintenance duties, verification and remaining limits here.
