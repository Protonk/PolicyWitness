# Candidate battery, final verification and outflows

**Status, 2026-11-20.** Items 0–4 are complete. Work stopped on reaching item 5, the outflows, as the maintainer asked. Results are in the management plan, under "Closeout: steps 3–5".

Daughter of [TRACE-MANAGEMENT-PLAN.md](TRACE-MANAGEMENT-PLAN.md), covering
steps 3–5 of its
[remaining work](TRACE-MANAGEMENT-PLAN.md#remaining-checkpoint-and-later-work).
The management plan keeps authority over dispositions, the guide freeze and
the outflows' content rules. Its sibling,
[TRACE-ACCOUNTS-PLAN.md](TRACE-ACCOUNTS-PLAN.md), completed step 2.

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
  from the tracked plans, the ledger, the probes and step 4's evidence. The
  scratch drafts are inputs only.
- **Reviewer V7** checks each duty and judgment against its evidence.
- **Optional probe P5** gives three Sonnet readers and one Opus control the
  user-responsibility outflow alone, to test whether each duty can be acted
  on.
- **The completion check** runs in both directions:
  - every review observation has a disposition;
  - every change has identified claims behind it.

## Approval

The maintainer approved items 0–4 on 2026-11-20 and asked for work to stop
on reaching item 5 or a blocker. The step 4 opt-ins above were approved;
`runner_exec_inheritance/mutation_controls` was added under the same
authority. The agent fleet is approved at the size of
`TRACE-ACCOUNTS-PLAN.md`.

- [x] 0 Coordinator setup
- [x] 1 Step 3, W5 and V5
- [x] 2 Step 4a, W6 with coordinator review
- [x] 3 Step 4b, signed build
- [x] 4 Step 4c, verification runs
- [ ] 5 Step 5, W7, V7 and optional P5
- [ ] Prune apply after step 5
