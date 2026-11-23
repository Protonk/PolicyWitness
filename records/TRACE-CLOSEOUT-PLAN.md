# Candidate battery, final verification and outflows

**Status, 2026-11-20.** Items 0–4 are complete. Work stopped on reaching item 5, the outflows, as the maintainer asked. Results are in the management plan, under "Closeout: steps 3–5".

Daughter of [TRACE-MANAGEMENT-PLAN.md](TRACE-MANAGEMENT-PLAN.md), covering
steps 3–5 of its
[remaining work](TRACE-MANAGEMENT-PLAN.md#remaining-checkpoint-and-later-work).
The management plan keeps authority over dispositions, the guide freeze and
the outflows' content rules. The [accounts ledger](trace-assessments/ACCOUNTS-LEDGER.md)
records the completed technical passes. This plan owns their closing prune.

## Result and limits

- **Step 3.** `preflight/build_refusal_controls` no longer constructs a
  release identity. Its nested battery runs on a normally built development
  candidate. Publication refusal is credited separately.
- **Step 4.** The final source is built clean-stamped and signed, after the
  build-input commit, and verified once: offline controls, the default
  battery, the selected opt-ins and the build-refusal case.
- **Step 5.** The three closing outflows are written against step 4's
  evidence, and the management plan's completion check is run.
- **Limits.**
  - No tagged release, publication or Apple submission.
  - The guide stays frozen.
  - No prune until the outflows are written. The runs they rest on are kept
    until then.

## Order

| # | Work | Who | Gate |
| --- | --- | --- | --- |
| 0 | Commit this plan; confirm AC power, the GUI session and an empty runner registry | Coordinator | none |
| 1 | Step 3: replace `release_battery` with the two candidate sequences; development checks short of the full case | Writer W5, then reviewer V5 | Approval |
| 2 | Step 4a: the build-input commit (two stale comments; strengthen the label-admission test) with regenerated copies | Writer W6; coordinator review | Approval |
| 3 | Step 4b: a clean-stamped signed build of that commit | Coordinator | Approval |
| 4 | Step 4c: offline and drift controls, default battery, opt-ins, then `preflight/build_refusal_controls` once | Coordinator | Approval |
| 5 | Step 5: user-responsibility and maintainer-judgment outflows, release account, completion check | Writer W7, then reviewer V7; optional probe P5 | Approval |

Reasons for the order:

- **The case is adapted before the final build.** Step 4 runs it only once.
- **Build inputs change once, before the build.** The step 4 battery runs on
  the same bytes as the final source.
- **Offline controls run before the build.** A tree defect is caught before
  hours of battery time are spent.
- **The outflows follow the evidence they cite.**

## Step 3 design

This follows the scratch brief `BRIEF-CANDIDATE-BATTERY.md` of 2026-11-17.
Its pointers are refreshed here, and this section governs where the two
differ.

- **`candidate_battery`, which replaces `release_battery`.**
  - Preparation: a disposable copy of the tree, with the verified pytest
    packages, as a snapshot commit on top of the genuine imported release
    tags. There is no new tag, no release rendering and no edit to the guide,
    generated views or `docs/publication.py`. The guide, the generated
    contract and limits views, and `docs/publication.py` must each stay
    byte-identical.
  - Build: a normal full build through the unchanged `build.sh`, with
    development settings.
  - Acceptance: `live_battery.py` calls `release_accept.accept(…,
    mode='development-candidate')`. It runs real extraction, inspection,
    `--version` and the dispatcher once, with no selectors and no Apple
    stand-ins.
  - Command boundary: the case fails if acceptance invokes `stapler`,
    `spctl`, `notarytool` or any selector-bearing dispatcher command.
  - Receipt assertions:
    - `kind` is `development_candidate`;
    - the contract equals the copy's `build_contract.identity`;
    - publication is `withheld`;
    - `apple_assessment` is `not_performed`;
    - `source.app_commit` is the snapshot commit;
    - `agreement_scope` is `build_contract_inputs`.

    With the real receipt, `record_acceptance` on a release attempt must also
    refuse and leave the attempt byte-identical. That refusal file is credited
    to the refusal result.
- **`candidate_publication_refusal`, which runs no battery.**
  - Strict acceptance of the built development ZIP refuses before any
    dispatcher invocation. Accepting stand-in Apple responses must never be
    reached.
  - After an annotated release tag is placed on the copy's HEAD:
    - the release preflight refuses, naming the guide freeze, and runs no
      build tool;
    - strict acceptance of the ZIP still refuses;
    - `publication_freshness.require` refuses from source.

    The identity the tagged copy derives is recorded.
  - A relabeled build is optional and taken only if it costs one incremental
    build.
- **Kept unchanged:** `control_release_entrypoints_enforce_fresh_mode` and
  the constructed controls in the three release preflight cases.
- **Development checks** (no full case run):
  - the refusal sequence alone, as local debugging;
  - candidate preparation and build up to the battery, with the
    byte-identity and identity assertions;
  - the copy's `source_drift`;
  - the command boundary given a constructed invocation list;
  - in the checkout: `source_drift`, the three release preflight cases and
    `preflight/build_provenance_controls`.
- **Accounts:** the fixture README, the preflight README, the case's catalog
  description, `tests/CHANGE-VERIFICATION.md`, `tests/COVERAGE.md`, and
  `docs/build.json`/`BUILD.md` or `docs/SIGNING.md` wherever they describe
  the nested battery. State that it is candidate verification, not release
  acceptance.

## Step 4 selections

All runs use fresh `tests/out/runs/final-*` directories, on AC power with the
lid open.

1. **Offline:** `--suite source_drift --suite unit --suite dispatcher --suite shell_helpers`.
2. **Build:** `make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'`
   at the build-input commit. Record `--version` and the publication records.
3. **Default battery:** `tests/run.sh` with no selectors. Reread it with the
   revised battery validator against a selection saved before the run, as at
   the product checkpoint.
4. **Opt-ins:**
   - `witness_contract/order_barrier_mutations`;
   - `runner_unit/exec_reader_mutations`, `reaped_ack_mutation`,
     `host_setup_oracle_sensitivity` and `actor_handoff_mutations`;
   - `runner_exec_inheritance/mutation_controls`;
   - `runner_byoxpc/runner_install`, `registry_recovery`, `default_location`
     and `reservation_controls`.

   The BYOXPC cases follow the external-runner workflow: runner list and
   reconcile before and after, with owned resources verified absent.
   `native_pause` and `arm_wait` are excluded. They are qualification
   experiments; one fails by design, and the other needs a coordinator gate.
5. **`--case preflight/build_refusal_controls`, once.** Its receipts separate
   the candidate's execution from the strict refusals.

Run results are recorded in the management plan. A failure stays a failure,
and its cause is found before anything is rerun. A sleep-overlapped run is
not a run of record.

## Step 5 logistics

- **Writer W7** drafts `records/USER-RESPONSIBILITY-OUTFLOW.md`,
  `records/MAINTAINER-JUDGMENT-OUTFLOW.md` and the release account. It works
  from the dispositions, the accounts ledger, the reader probes and step 4's
  evidence. The two drafts under `.tmp/trace-integration/` are local and
  gitignored. Reconcile their candidates with the tracked assessments and
  the final behavior. The judgment draft ends before EXEC, WIRE and IDENT.
- **User duties.** The [guide plan](../docs/guide/USER-GUIDE-PLAN.md#sources-and-constraints)
  takes questions about what a user must supply or compare, including duties
  that would change no test. For U-27/U-28 in the scratch duty draft, compare
  a captured receipt with the intended request using a separately retained
  nonce. Distinguish the host's check of the worker's bytes, the controller's
  admission of the receipt labels, and the caller's choice of a nonce that
  distinguishes two requests. Record which comparison the consumer actually
  needs. [Receipt assessment](trace-assessments/I-receipts.md#dt-97--nonce)
- **Maintainer judgments.** Review every row assigned to this outflow in the
  [outside-the-review notes](trace-assessments/ACCOUNTS-ADDENDA.md#outside-the-review-notes)
  alongside the guide-adjacent list below. For example, the technical account
  now describes how `runner validate` treats an inaccessible executable as
  missing. The behavior decision remains open. Preserve the standing of
  unassessed rows, including the source walkers that discard listing errors.
- **Release account.** Cover the changed result and evidence meanings, what
  the converted cases enforce, which controls moved from ordinary `run` to
  `test-input run`, and what the development candidate and strict release
  checks each establish. Carry the pytest-family archive-read cost into the
  account. The [pytest evidence plan](../tests/PYTEST-EVIDENCE-PLAN.md) owns
  the reader and storage work. Include the guide overhaul's entries from the
  [product-change ledger](guide/PRODUCT-CHANGES.md) in the same account.
- **Reviewer V7** checks each duty and judgment against its evidence.
- **Optional probe P5** gives three Sonnet readers and one Opus control the
  user-responsibility outflow alone, to test whether each duty can be acted
  on.
- **The completion check** runs in both directions:
  - every review observation has a disposition;
  - every change has identified claims behind it.

## Guide-adjacent items for the maintainer-judgment outflow

The maintainer looks at each of these items while the maintainer-judgment
outflow is written. Each concerns the guide, its freeze or the publication
boundary, but none is a correction to guide text, which the freeze forbids
collecting. Each item names its source.

**Test, build and release machinery that encodes the guide**

1. **The opt-in build guard expects the old guide behavior.**
   `preflight/build_guard_controls` plants `'previous guide\n'` and expects
   the guide to be staged on success or absent after a signer refusal. At
   `07dd8599`, an isolated `generate_limits.py --stage-development` check
   accepted the frozen guide (exit 0) and refused the fixture bytes (exit 1).
   Step 4 exercised `preflight/build_refusal_controls`. A repair of the
   separate guard would need to check both success and partial output
   through `preflight/build_guard_controls` itself.
   [Build guard fixture](../tests/suites/preflight/opt_in/build_guards.py)
2. **The lesson behind item 1.** Nothing ran these opt-in cases between
   `bba8bca3` and the closeout. A product commit therefore broke them, and no
   one noticed for the whole stage. Decide whether opt-in cases that a change
   reaches need a rule or a routine.
3. **`make notarize` reaches the build on withheld or diverged source.** The
   Makefile runs the release preflight in report mode for notarization,
   which `docs/SIGNING.md` calls a rehearsal. `make release` is strict.
   Owners: `tests/lib/release_preflight.py`, `docs/SIGNING.md`.
4. **Fixtures carry their own publication-fresh source.** Four release
   controls presumed a checkout copy is publication-fresh. They now construct
   their own fresh guide regions through `contract_fixture.fresh_guide_regions`
   (`11e93191`). That is a maintenance cost of the freeze, and it should be
   revisited when the guide is next published.
5. **Which build does a surviving publication receipt describe?** In the
   isolated check above, staging left the previous `publication.json`
   byte-identical after refusing the guide. The build removes the old app
   and ZIP before it calls staging. Decide what receipt should accompany a
   partial build and check that state after a real assembly refusal with a
   previous receipt present. The isolated check exercised only staging.
   [Build assembly](../build.sh) · [Receipt writer](../docs/generate_limits.py)

**Technical owners that route to the frozen guide**

6. **Receipts.** `docs/ARCHITECTURE.md:441` sends readers to the guide for
   the compiled-object receipt's definition. `docs/LIMITS.md:304` does the
   same for its prerequisites. RESPONSE holds the complete statement. No
   recommendation requires repointing them; decide at the rewrite.
7. **The limits Control column.** Its reading rule is a shared region copied
   into the guide. Four rows were reclassified "Flag" for a `test-input run`
   control instead of changing the rule (`bd8144ea`). Decide whether the rule
   should name test controls.

**Divergences the rewrite inherits**

These come from authorized owner changes. Each was recorded where it arose.

8. **The experimental controls (seam migration).** The guide documents the
   eight controls as request data and has no `test-input run`. Its limit rows
   name `_test_overrides.*`. Owners: `docs/limits.json`, `10-request`. An
   ordinary `run` now refuses those keys, which belongs in the release
   account.
9. **`cleanup_trigger`.** The guide still calls it a fact recorded where the
   host acts. Since R13 it is derived from the stop reason at final
   collection.
10. **Actor fallback.** The guide's fallback paragraphs do not say that
    `policy_check` is null for a request with an `actors` array (R10).
11. **The import inventory (R12).** The guide lacks three things:
    `unfollowed_imports` in the helper list; that an empty record list can
    accompany unfollowed forms; and that a record error can carry a hash.
12. **`runner install`.** The guide does not say that `XPC_SERVICE_PATH` must
    be the canonical bundle path or omitted (R7).
13. **Shared regions.** Corrections made in the owners of shared regions
    leave the guide's copies diverged until regeneration. These include
    `docs/limits.json` rows, `docs/EXTENSIONS.md`, and the failure contract's
    extension-status block, where "timed out on" was removed. The rewrite
    regenerates the copies; it does not edit them.

## Closing prune

After step 5 has used the four `final-*` runs and recorded their scope,
preview the single closing cleanup with `make prune`. It covers the
technical-account runs as well as the final verification runs. Inspect the
eligible runs and blockers. Apply with `make prune APPLY=1` when approved.
The ledger and the committed probe inputs and adjudications remain available
afterward.
[Test output retention](../tests/AGENTS.md#preserve-and-clean-up-output)

## Approval

The maintainer approved items 0–4 on 2026-11-20 and asked for work to stop
on reaching item 5 or a blocker. The step 4 opt-ins above were approved;
`runner_exec_inheritance/mutation_controls` was added under the same
authority. The staffing for step 5 is specified above.

- [x] 0 Coordinator setup
- [x] 1 Step 3, W5 and V5
- [x] 2 Step 4a, W6 with coordinator review
- [x] 3 Step 4b, signed build
- [x] 4 Step 4c, verification runs
- [ ] 5 Step 5, W7, V7 and optional P5
- [ ] Preview the closing prune after step 5 and apply it when approved
