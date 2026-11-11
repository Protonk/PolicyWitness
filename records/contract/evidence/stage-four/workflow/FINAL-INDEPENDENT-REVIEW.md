# Independent guide workflow successor review

Recommendation: adopt the final source candidate for the planned stage-four verification sequence. The six original correction groups are resolved at source level. The new controls exercise actual ownership persistence, cleanup and file preservation through existing helpers. Execution credit awaits those controls and the native guide workflow.

Final patch: `/private/tmp/pw-contract-stage-four-guide-workflow-final/guide-workflows.patch`
SHA256: `349521e18cc0c9e1703af8e19ee9e222153a22fdb34fe9699485d23bbc17c56a`
Candidate manifest SHA256: `d9db8b3179790102147805bbb9cedd0ae51b8ee770c5294dc12cb5452d0cd2ee`.
All twelve final postimage hashes match that manifest by independent standard-library file hashing.

Original independent findings remain at `/private/tmp/pw-contract-stage-four-guide-workflow-review/REVIEW.md`, SHA256 `ff4d3f7229c1a3002c9cc7e310f2708db2dbb39e6e858e3073d465c1f562ddb9`. The original, V2 and V3 candidates are preserved. I read the V2 changed functions and controls, the complete V3 recovery delta, and the final one-line consequence assertion against those frozen predecessors.

## Resolution of the six groups

| Original concern | Final implementation and meaningful control |
| --- | --- |
| Interrupted outer deletion | Cleanup persists `cleanup_verified` after resolving machine resources and comparing the source app, deletes ordinary work children while retaining `session.json`, then removes that owner and the empty directory. Re-entry at the verified checkpoint skips already-verified output files. The control deletes an earlier evidence child, fails a later directory deletion, checks the retained owner and remaining marker, then resumes while making any re-read of the deleted output fail. Separate exact verified-empty and unverified missing-owner neighbors distinguish recoverable deletion progress. |
| Ownership chain and newer durable progress | `owner_object` requires regular nonsymlink owner files. Outer cleanup validates the durable workspace and compares WORK_CORE with the artifact owner; nested cleanup compares GUIDE_CORE, and the outer `external` core binds the actual child to its planned workspace/stage/source. Adoption arms that core before child persistence and before copy/sign/install. A different valid session receipt, foreign durable path, changed identity and owner symlink refuse before OS calls or foreign writes. Missing auxiliary output recovers only from the recorded durable location. The revised durable-ahead control makes newer uncertainty retain an effect/stage, then makes newer cleared progress permit removal despite the older artifact; this exercises which journal actually governs cleanup. |
| Default-registry scope | The guide branch requires `registry_path is None` before common cleanup can select or delete a registry. A constructed foreign registry/lock remains byte-identical and no OS invocation occurs. Existing ordinary BYOXPC controls continue to own private-registry behavior. The default-registry fake is explicitly stored in the control's private directory. |
| Random invalid positive fixture name | Positive paths now use `secrets.token_hex`, satisfying the existing alphanumeric grammar deterministically. The ownership predicate is unchanged. |
| Preserve an existing work owner | `Workflow.__init__` refuses a preexisting owner using `lexists` before guide/app commands or replacement ownership. The control preserves its exact bytes and observes zero command calls. Adoption also uses `lexists` for the auxiliary receipt: the final dangling-link control requires the foreign target to remain absent, parent durable bytes and in-memory external field to remain unchanged, the stage to remain empty, and zero OS calls. |
| Returned runner identity | Verify now joins `runner_id`, `service_name`, and host `bundle_id` to the saved installation; the service-selected create also requires that bundle identifier. Existing request, status, plist, effect, contract and worker-reap checks remain. These are native workflow assertions and await execution. |

During successor review I found two further narrow points; the final candidate corrects both. Verified work absence now clears a stale `cleanup_error` both before and after `removed` was set. A control injects failure in the final artifact save after successful `rmdir`, observes the error receipt and absent work directory, retries, and requires the clean completed receipt. The earlier unused `journal_note` control was replaced by the observable durable-ahead progress pair described above.

## Consequence controls and bounded meanings

The control implementation uses the actual outer cleanup, `session.adopt_guide`, `session.cleanup`, existing fake OS command executable, ordinary filesystem operations, and dispatcher disposable-repository/prune machinery. It adds no cleanup service or native test harness.

- A simulated invocation writes an independent effect and raises a capture interruption. The actual workflow persists uncertainty and the cleanup path preserves both owners/effect, emits no removal, and records one submission. This establishes the fixture's conservative response when executed; shipped client no-replay behavior retains its separate reservation controls.
- Reaped and exact admission-refusal neighbors permit cleanup; unreaped output retains it. These controls explicitly inject consumer admission and exercise the actual reap/refusal predicates. They therefore support that decision boundary, while the real native workflow runs the independent consumer on complete run envelopes or the inner verify reply.
- Fake service, plist and registry survival faults each block staging deletion. Success and recorded partial-install neighbors remove the owned resources; uncertain installation without recovery identity retains them. The fake command log excludes install/run/verify during recovery. Existing `shell_helpers/byoxpc_setup` owns the larger ordinary-layout fault matrix.
- Dispatcher retention uses actual managed disposable runs and ordinary prune. It preserves complete byte inventories for pending/error owners and removes the clean neighbor. The outer top-level receipt is the integration point; nested fixture receipts are separate evidence.
- Installed and pending foreign-registry rows stop the workflow before copy/sign/install/validate/remove. The exact nonempty collections are supplied by a constructed envelope seam and command calls are recorded; this is an entry-control check rather than a live default-registry mutation experiment.

The guide command cuts, substitutions, native file/compiled-profile assertions and staged-guide byte equality are unchanged from the original review except for stronger runner identity joins. The native result claims remain contingent on those commands completing on the staged signed app.

## Residual limits and selections

The initial empty default registry remains an equipment/serialization prerequisite. A concurrent external writer can add an entry before the guide's `runner validate`, which refreshes all `registry.runners`; the `updated == 1` assertion detects that disagreement afterward. Parent explicitly retained this limit. No cross-command registry lock is claimed.

The shared helper now reads its initial ownership receipt through `owner_object` for both layouts; guide-specific core checks remain confined to the guide branch. Run `shell_helpers/byoxpc_setup` to check ordinary layout preservation, `dispatcher/retention_controls` for the prune integration, applicable source-drift/catalog checks, and `witness_contract/guide_workflows` after integrating/regenerating the reviewed guide and staging its exact bytes alongside the signed app. The new ownership controls run inside that opt-in before native guide commands. The existing constructed reader and reservation cases continue to establish their separate interpretation/transport scopes.

No tests, candidate controls, shell workflow, app invocation, build, generator, product import or shared edit occurred in this review. The author's AST check is recorded as author-provided preparation only. Native signing/GUI/sandbox eligibility, capture availability, actual service/plist retirement and final release acceptance remain for the authorized execution sequence. Conservative retention after missing evidence has a manual inspection/recovery requirement; no automatic request replay is added.

## Opened scope

For the successor I read all revised outer cleanup/owner functions, helper adoption and guide/core checks, the full new ownership-control module, the fake default-registry/removal branches, dispatcher retention addition, final native runner-identity assertions, and candidate notes/manifests. I compared all final postimage hashes. I also read the existing dispatcher `Controls.pruning()` command/effect pattern before assessing its extension. Original guide, helper/retention source and command-source coverage is enumerated in the preserved first review; those unchanged portions are carried forward rather than represented as fresh exhaustive reads.

The full fake signing/installation implementation and full independent consumer were not re-reviewed; changed fake cleanup branches and actual reader call scopes were inspected. This report contains source/control-reading conclusions and artifact-hash observations only.
