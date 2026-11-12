# Inputs to the v0.3.8 release

What the release end-game still needs from the four-stage contract work, whose outline and working records have been removed from the tree. The stages are complete apart from the final checkpoint. Everything removed is in history: `git show e4148011:docs/CONTRACT-STAGING-PLAN.md` and `git show e4148011:records/contract/CONTRACT-LEDGER.md` recover the outline and the ledger, and the same commit holds the examination, stage accounts and their evidence under `records/contract/`.

## Where the release stands

Recorded on 2026-11-12.

- `main` is prepared for `v0.3.8` and has no `v0.3.8` tag. The stamp tables and public snapshot claim the release, so the ordinary stamp check and the build refuse until the tag exists.
- `v0.3.7` is tagged locally, accepted and archived under `dist/archive/v0.3.7/` (gitignored, local only). It is unpublished and its tag has not been pushed. The branch itself has been pushed, so a clone without both tags fails the stamp check.
- The maintainer reads the contract line by line, and arranges another agent's review, before the tag. The tagged rehearsal and the Apple submission wait for the instruction to continue.
- Evidence from the earlier pre-tag rehearsals describes the builds it ran on (`8435e5d3` for the last full battery and refusal rehearsal). A later change to shipped source or the generator needs its own runs.

## Decisions open for the maintainer

Seven are stated in the contract as known gaps, each with the behavior kept meanwhile. The contract is their record.

| Known gap | Question |
| --- | --- |
| `envelope.data.select.success_findings` | Whether `result.ok` and the exit status also reflect controller integrity findings. |
| `actor_evidence.gate.cancellation_evidence` | Whether a failed termination dependency cancels only the dependent phase or the rest of the schedule. |
| `reply.failure.publish.associations` | Whether a reporting-failure reply must keep each retained record's actor and phase association. |
| `diagnostics.execution.vocabulary.vocabulary_choice` | Whether the controller keeps `unconfirmed` for both `unresolved` and `inapplicable`. |
| `diagnostics.issue.subject.withholding_scope` | Whether a reply-wide finding also withholds the per-actor conclusions. |
| `diagnostics.execution.reader_evidence.classifier_generation` | Whether the three hand-written classifiers are generated from one source. |
| `identity.surfaces.release_history` | Whether an ordinary build requires complete release history. |

Four are outside the contract.

| Item | Question | Kept meanwhile |
| --- | --- | --- |
| What ships | A release archives the guide and not the contract, while the guide's surface table names surfaces defined only in the contract. | The table stays in the guide; the archive's contents are unchanged. |
| `v0.3.7` at publication | Published as a release, or only its tag pushed. `make publish` pushes one tag, and both tags must reach the remote. | Nothing is published. |
| Footprint sample at controller exit | `witness_contract/response_footprint` refuses a final process sample whose identity read succeeds and whose re-read returns `ESRCH`. The case is in the default battery, so a small share of acceptance runs can fail on it. One battery on `d18d4925` did. | The refusal and its controls are unchanged. |
| Support in the rendered contract | Support paragraphs are about a tenth of the document. Rendering them without pins and context would remove about 3,400 words and move no stamp. | Support renders in full. |

## Checkpoint rules the release procedure does not state

The [release procedure](../../docs/SIGNING.md#release-procedure) covers the commands. These rules came from the outline.

- The executor makes the release commit and the local annotated tag and runs `make release`. The executor does not run `make publish` and pushes no tag. Publication is the maintainer's decision.
- The last development build precedes the stamp step; between that step and the tag the stamp check refuses by design. After the tag and before `make release`, run the strict preflight, then a fresh build and the default battery on the tagged tree. That exercises the release identity without a submission.
- From the tag until `dist/archive/<tag>/release.json` exists, write nothing into the working tree and run no other build or battery in the checkout. Preflight runs again after acceptance and refuses an untracked file or a new commit.
- For a failed attempt, read the retained receipts first and say whether the cause is the environment, the release tooling, a test or the product. Fix the cause where it lives and state the attempt, the failing step and the cause in the correcting commit. A passing rerun is not a diagnosis.
- Retry under the same number: commit the correction on top of the tagged commit, delete the local tag, recreate it as an annotated tag on the new commit, repeat the stamp check and run `make release` again. This holds only while the tag has not left the repository and no `dist/archive/<tag>/` exists. Do not amend the tagged commit or take the next number to get past a refusal. Once the archive exists the number is spent, and a later change to shipped source takes the next one.
- Do not add a prose or build baseline entry to pass the drift suite. Preflight refuses growth against the preceding tag, and can say so only once the tag exists.
- Stop for the maintainer when the signing identity or notary profile is absent, as distinct from unreachable inside a sandboxed harness, and when Apple asks for a policy agreement. Never submit again to resolve a pending reply.
- A case is never passed by removing it from the default battery, adding a skip or editing evidence.

## Release notes

[RELEASE-NOTES-v0.3.8.md](RELEASE-NOTES-v0.3.8.md) is a working draft. It holds the surface-by-surface account of which surfaces changed in behavior and which only in their account, which the notes owe readers because every stamp moved across these two releases. Its verification paragraphs describe the rehearsals named above and need revising against the runs that precede the tag.

The `v0.3.7` notes were written without the maintainer's supervision and are not a model for format. Their bytes are in `dist/archive/v0.3.7/evidence/release-notes.md` (gitignored, local only), which `make publish` uses unless `RELEASE_NOTES=` overrides it.
