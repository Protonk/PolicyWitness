# Private stage-four guide candidate

This candidate changes five authored sources. It has not been applied to the checkout. No app command, test, generator, build, signing operation or guide walkthrough was executed. `before/` holds exact inputs; `after/` holds proposed authored changes; `guide-revision.patch` is their unified diff. `manifest.json` and `review.json` identify bytes and the limited static inventory performed.

The current user-directed stopping point is before creating the v0.3.8 tag, after completed changes are committed and pre-tag checks pass. The recipes below belong to that preparation. Tagged rehearsal, notarization/submission and publication remain later actions for the coordinator after resumption.

## Read the owning sources together

The six copied/generated guide regions are intentionally byte-identical in before/after. Consequently `after/docs/PolicyWitness.md` is an authored-source candidate, not the final assembled reader: its old FAQ/extension/limits/reading-rule copies remain until the owning generator runs. Read the proposed owners alongside those locations:

| Guide region | Proposed owner | Later action |
| --- | --- | --- |
| Questions | `after/docs/QUESTIONS.md`, shared markers | `generate_limits.py` copies and rebases guide links. |
| Sandbox extension coverage | `after/docs/EXTENSIONS.md`, shared markers | Generator nests level-two headings and rebases links. |
| Limits | `after/docs/LIMITS.md`, shared narrative | Generator preserves tables from `limits.json`, resolves scalar spans and copies shared text. |
| Extension statuses | `after/tests/FAILURE-PROPAGATION-CONTRACT.md` | Generator copies shared status paragraphs/tables. |
| Reading a comparison record | Same failure-propagation source | Generator copies the shared numbered list. |
| Public contract surfaces | Existing contract generator/history | Regenerate from the settled public tree at the appropriate pre-tag boundary. |

No numeric value or limit record changed. No generated file or guide copy was edited. Former `BEGIN/END CONTRACT` guide-region markers are removed because the structured contract tree now owns public facts and stamps; actual ownership markers remain.

After integrating the authored changes, the coordinator should run the owning generators and review the assembled guide, then source_drift, meaningful changed mutation controls, standalone-link/extraction checks and the pre-tag workflow evidence. Staging uses `generate_limits.py --stage-guide` only after freshness; compare its bytes with the packaged guide later. All old guide heading anchors are retained; `shape-and-producer-contract` has an explicit alias at Worker and host records. No inbound caller edit is required by this candidate.

## Scope and concrete changes

- Quick start uses a private owned directory, saved exact build contract, a saved create request, stdout/stderr/exit and an independent file observation. It supplies the variables used in later recipes.
- The refusal exercise stays adjacent to acceptance and correction: unknown capture key, corrected key with missing nonce, then fresh nonce plus a valid capture request. Each version and outcome is retained. Known pre-execution refusal is separated from uncertain invocation before any suggested retry.
- The policy/helper/augment passages distinguish selected source, parameter map presence, native compilation, application and capture. The helper has its actual `--request` command. The shipped augment's unconditional file-read allow is explicit, without a universal SBPL precedence or helper-success promise.
- Output moves to Reading a result → outcome catalog → Worker and host records → existing details. Run status, controller checks, actor-local and reply-wide scopes, validated host conflicts, degraded-form checks and worker lifecycle assessment are contiguous. The catalog now includes the controller-owned capture/transport outcomes rather than pointing to an unshipped README.
- Receiver evidence begins with known-not-invoked, invoked and unknown states plus their recovery consequences. Actor application, schedule, equipment, authority setup, owned reap and activation records are easier to locate.
- Shared questions become concise entrances to the actual workflows. Source-supported evidence limits stay visible; unsupported causal conclusions, dismissive audience advice and historical observer commentary are removed.
- Extension examples preserve their exact JSON heredoc interface, including BUILD_CONTRACT for the existing owning extractor, but the displayed commands produce a current-identity `submitted.json`, retain exits/stderr and record target metadata/hashes before and after. No tested request predicate or phase/action name changed.
- External runner preparation begins with list/reconcile and a fresh staged copy. It preserves signing/inventory consistency, captures failed install output, inspects pending ownership, verifies the fixed diagnostic request, runs a new file-effect target, then removes and confirms recovery. It avoids deleting a bundle before ownership is known. Validate/remove exit 0 is separated from their body findings.
- The ad-hoc account identifies the complete coherent source requirement. A recipe that changes only the host's signature would fail team/inventory validation; the signed same-team path is the complete worked installation sequence.

The after guide has a little more authored workflow text before owner regeneration. Its final rendered size and repeated prose must be reviewed after generation; no rendered-size improvement is claimed. This is local consolidation, preserving the guide's top-level sequence and existing examples.

## Corrections grounded in actual sources

| Correction | Source read for this candidate |
| --- | --- |
| Argument/request identity, selector and augmentation order; held request; terminal fallback; outer success and diagnostics | `controller/src/cli.rs`; `controller/src/run_flow.rs` (`cmd_run` preparation, `admit_reply`, `fallback_policy_check`, `actor_fallback_checks`, `complete_execution`); `controller/src/runner_select.rs` selector/worker requirements. |
| Exact client capture/refusal names, no replay, rejected bytes versus decoded record | `controller/src/runner_client.rs` (`failure`, `fallback_eligible`, capture admission); current contract transport and wire accounts read in prior drafting/review. |
| Lifecycle-local versus reply-wide findings; valid host conflicts; retained degradation | `controller/src/porcelain_admission.rs` (`project`, `admit_reply`, `execution_diagnostics`), plus stage-two reviewed 41-diagnostics account. |
| Finding `subject_path` | Reviewed stage-two 41-diagnostics postimage and earlier independent R38 production review; depends on that accepted additive patch being integrated and verified. Root reports stage-two readers are now applied. |
| Authority session applies only when token/delivery resources exist; every worker's setup boundary; gate cancellation | Earlier direct reads of `ActorPlan.swift`, `ActorTranslation.swift`, `ActorScheduler.swift`, `AuthorityCustody.swift`, C `prepare_authority`, and current 14/33/34 authored source truth fixes. Stage-two gate controls still supply their own evidence grade. |
| Actor application/equipment/authority navigation and phase records | `PWRunnerReply.swift` declarations plus current 33/34 authored records. `authority_setup` is top-level with host and actor-indexed worker scopes. |
| Install/verify/status/remove interface, pending registry, verify refusal, validation bodies | `controller/src/runner_commands.rs` actual command parsers and command implementations. |
| Source signature/inventory precedes installation resigning; host and worker teams agree | `controller/src/runner_manager.rs`, `verify_equipment_inventory`, and install's source-verification/signing order. |
| Ordinary versus actor worker environment | `ActorSession.swift` launch setup: actor empty environment/streams; legacy inherited environment/streams. Exec-child environment and handles were read in the prior native-worker examination. |
| Pair exclusion versus helper processing and native-call evidence | `CWorkerRequestPlanning.swift`, `PWRunnerPredictionEvidence.swift`, `ProbeRunner.swift`; `sb_api_validator.c` `resolve_filter_type_id` and verdict classifier. The old local_name blanket statement and normal-call promise were too broad. |
| EINVAL wildcard hint | Validator `emit_verdict`: it says family operations are typically queried in wildcard form; it records the actual rc/errno. |
| Helper parameters, fixed verdict stages, direct CLI | `controller/src/bin/sbpl-check.rs`; detailed helper/native controls in the prior source examination. |
| Actor dossier | `controller/src/dossier.rs` and run preparation: one policy dossier per actor source selection. |
| Extension JSON extraction | `tests/suites/witness_contract/check_extensions.py`: literal heredoc string and placeholder preserved. |
| Shared owner restrictions and staging | `docs/AGENTS.md`, `docs/generate_limits.py`, plan stage four and current user stop instruction. |

These are source/check reads. They establish what was inspected, not a newly executed native observation. The existing historical calibration descriptions retain their original platform/target scope. The missing consumer repository remains a validation limit.

## Decisions and integration dependencies kept visible

1. R-20 success remains host-finished classification even with controller integrity findings. R-34 reply-wide withholding preserves independent actor entries. R-07 retains `unconfirmed`. The candidate states current behavior directly; a maintainer change requires corresponding source/account updates before finalizing this passage.
2. R-37 remains failed evaluated-gate cancellation of the remaining schedule. An unreached gate caused by unavailable dependent setup is distinguished from an evaluated failure. R-36 keeps degradation-form checks plus independent worker lifecycle projection, with ordinary native/actor/phase relation families applying only to the nondegraded branch. No product rule is changed here.
3. The R38 subject-path paragraph follows the accepted stage-two addition. Confirm it against the final retained-envelope/corpus evidence, including duplicate labels and null assertions, before staging.
4. The release contract link is prepared for `v0.3.8`. It is not claimed remotely available before publication. Before tagging, check the local release tree/anchors; after authorized publication, check the remote URL. The archived app still carries the standalone guide rather than an invented sibling CONTRACT file.
5. Explicit guide commands have not run. In particular, plutil identity extraction, OpenSSL nonce generation, actual same-team source resealing/install and the newly retained file observations need the walkthrough receipts in `WALKTHROUGHS.md`.
6. The limited static inventory checks anchors with a simple heading scan, not the repository's full Markdown parser. The six ownership blocks compare byte-for-byte. Repository link/prose/scalar/mutation checks remain to be run through the coordinator.
7. Root may have committed other source/account changes after the manifest's base. Compare each exact preimage before applying; keep accepted stage-two field/account updates, including existing shared-owner corrections, if an overlap appears.

## Review follow-up

The preserved `reviewed-6e.patch` is exactly SHA 6e0337e1cef773b34fe221b3bc0109670f837ba178c9befe58490cb7cc41b98b. `review-followup.patch` shows only the next review corrections: apply/unapplied opening, explicit macOS 26+ arm64 prerequisite, guarded new-effect invocations for quick start/capture/BYOXPC, and one authority-setup sentence's capitalization/wrapping. The full replacement patch hash is in the manifest. Both the exact initial tree and current source copies pass private `git apply --check`; current repository guide changes are confined to generated stamp rows, which this patch preserves.
