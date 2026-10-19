# Retain evidence by claim while concurrent changes land on main

## Problem and intended result

Completed development runs currently become permanent exceptions when they are
added to `RETAINED.json` without a release label. Each exception protects the
whole directory, including disposable compiler state and copied fixture trees.
Independent tasks can accumulate these exceptions faster than release cleanup
retires output. A successful test also needs a precise source identity when
other work continues to change `main`.

Make ordinary completed output expire under an explicit policy. Preserve evidence
because it supports an identified acceptance decision, maintained observation,
release, or unresolved resource recovery. Keep those claims separate from
immutable records of what actually ran. Concurrent work must neither overwrite
another task's claim nor assign an older result to a newer source revision.

This is an implementation plan. Follow [the planning guidance](../CONTRIBUTING.md#planning-a-change)
and [test working rules](AGENTS.md). Implement the phases below in order; the
policy described here is proposed behavior, not the current cleanup contract.

## Existing mechanisms and affected files

| Owner | Current behavior and proposed work |
| --- | --- |
| [test_cli.py](lib/test_cli.py) | Plans selection, validates output, acquires the checkout lock, writes ownership, then executes. Allocate a unique default output directory before execution and add the retention command entrypoint. Preserve explicit output-path validation. |
| [suite_run.py](lib/suite_run.py) | Records terminal results and checks app inventories. Add a separately versioned source/evidence manifest without relabeling historical `run.json` records. |
| [retention.py](lib/retention.py), [RETAINED.json](RETAINED.json) | Own index validation, atomic replacement, path overlap, run ownership, and ordinary pruning. Add typed claims, generations, lifecycle decisions, and migration. |
| [checkout_lock.py](lib/checkout_lock.py), [checkout_lock.sh](lib/checkout_lock.sh) | Serialize cooperating builds and test executions per checkout, including surviving descendants. Preserve these guarantees; the lock does not freeze arbitrary source edits or serialize Git commits. |
| [release_cleanup.py](lib/release_cleanup.py) | Inspects real case receipts for pending external-runner cleanup and classifies ownership. Reuse these checks for every cleanup path. |
| [release_runs.py](lib/release_runs.py) | Packs and verifies portable release evidence, including original inventories and summaries. Reuse its inventory and verification principles for development evidence; retain the existing release format reader. |
| [release_archive.py](lib/release_archive.py), [release_rotate.py](lib/release_rotate.py) | Publish verified release copies and journal cleanup. Adapt live retention access through the new claim API; preserve historical archive verification and interrupted rotation recovery. |
| [dispatcher controls](suites/dispatcher/check_retention.py) | Exercise ownership, concurrency, pruning and Makefile delegation with independent receipts. Extend these controls for claims and expiry. |
| [release rotation controls](suites/preflight/check_release_rotation.py), [publication controls](suites/preflight/check_release_publish.py) | Exercise portable evidence, interrupted transactions and retained exceptions. Add migration and cross-format controls. |
| [tests reference](README.md), [working rules](AGENTS.md), [Makefile](../Makefile), [signing guide](../docs/SIGNING.md) | Explain output, reuse, manual pruning, release retention and recovery. Update together with their owning behavior. |

The initial scratch/evidence separation targets are
[launch descriptor controls](suites/runner_unit/launch_descriptor_controls.py),
[host setup controls](suites/runner_unit/host_setup_controls.py),
[service admission controls](suites/runner_unit/service_admission_controls.py),
and [planner controls](suites/source_drift/check_planner.py). These retain copied
sources and build directories inside case artifacts. Preserve their deliberate
source mutations and command receipts while separating compiler caches and
other reproducible intermediates.

## Decisions

### Source identity and concurrent integration

Continue integrating commits onto `main`, but run acceptance against an isolated
checkout of an explicit commit. Each execution uses its own output directory
and the existing lock for its checkout. Preserve tracked guidance files when
constructing the checkout, including those in `.tmp/` and `dist/`.

For development results from uncommitted changes, capture the base revision,
binary-safe patch, relevant untracked inputs, modes and symlinks into a source
manifest. Build and test the materialized snapshot, then verify its inventory
before crediting the run. A snapshot must identify the combined tree actually
tested; it must not attribute concurrent edits to an individual task. If a stable
capture cannot be established, record development diagnostics without promoting
them to acceptance. Comparing the working tree only before and after a run does
not prove that it stayed unchanged during execution.

Keep product build provenance and test-source provenance distinct. The test
code, fixtures and helpers can change while the inspected app stays identical.
Record both identities and the existing app-integrity result.

Store acceptance against its explicit target revision and case coverage.
Reports claiming coverage of current `main` must compare that target with the
revision being reported. Use a generation check when replacing an acceptance
claim so a late submission cannot overwrite a later decision. Advancing `main`
does not rewrite old results. Carrying results forward requires the dependency
review already specified in `AGENTS.md`, with uncertain applicability causing a
rerun. Test passing is not a mechanical proof of complete dependency coverage.

Commit integration and acceptance publication need a single cooperating writer
or a serialized command queue for the shared checkout. Independent tasks may
produce run records concurrently. Neither Git's index lock nor the test checkout
lock by itself prevents unrelated edits from entering a shared commit.

### Immutable run facts and explicit retention claims

Add a separately versioned manifest for each completed run. Include the unique
run ID, task ID, source snapshot identity, test selection, commands, outcome,
app identity when applicable, cleanup status, and evidence inventory. Keep
terminal run files immutable; later corrections and evidence-reuse decisions
are separate records referring to the original facts.

Evolve `RETAINED.json` to a versioned claim index with a monotonically increasing
generation. A claim has an ID, purpose, owning task or maintained document,
referenced run/bundle IDs and hashes, a reason, creation time, and either an
expiry or a defined supersession/release condition. Store acceptance coverage
and its target source identity where applicable. Multiple claims may protect
the same evidence; releasing one does not release the others.

Missing purpose or lifetime is invalid for a new claim. A documentation claim
names its actual citation; an acceptance claim names its cases and target; a
release claim names its established tag. Temporary investigation holds require
an explicit expiry. Recovery protection derives from ownership and cleanup
receipts as well as the index and cannot disappear merely because a claim expires.

Add `lib/retention_cli.py`, exposed through proposed
`tests/run.sh --retention <inspect|promote|retain|supersede|release|gc>` commands.
The command owns index read/validation/update under the checkout lock and checks
the caller's expected generation for conflicting replacements. Independent
additions reload and merge under the lock. Dry-run output identifies retained
bytes, disposable bytes, purposes, expiry, and blocking conditions. Preserve
the existing `--prune` and Makefile interfaces through explicit compatibility
handling, then document their policy-aware behavior when enabled.

Do not require a daemon or a database. Start with the existing lock, atomic JSON
replacement, versioned manifests and journaled filesystem operations. All live
retention writers, including release helpers, must use the same API.

### Evidence bundles and worktree boundaries

Provide separate managed locations for compiler scratch and evidence at run
creation. Scratch remains tied to the run's ownership and cleanup state; it
does not become ordinary unowned `.tmp` material while a process or resource
still depends on it.

Promotion creates a new immutable bundle containing the selected case's complete
inputs, raw observations, commands, diagnostics, outcome, source identity and
app identity. Include original failures and any subsequent replacement credits
needed to interpret the claim. Preserve original paths as provenance, while
bundle reads use verified member names. Declare the included case set and the
deliberately omitted scratch; a partial-case bundle must not masquerade as the
complete original run. Retain the original run summary without rewriting it.

Exclude compiler caches, SDK modules and reproducible intermediates from newly
produced evidence. Keep mutated source inputs and supporting observations even
when they look like ordinary copied files. Hashes identify bytes; they do not
establish that a chosen subset is sufficient evidence. Review that boundary in
each converted suite. Do not trim old retained directories in place.

Use `tests/out/evidence/<bundle-digest>/` in the integration checkout as the
initial local store. Publish through a staging directory: copy, verify inventory
and summaries, flush, rename, then install the claim under the lock. Originals
remain protected until publication succeeds. Keep small cited observations in
tracked fixtures where appropriate; release evidence keeps its existing archive
location. Local protection is not an off-machine backup guarantee.

Independent worktrees keep their own run directories and execution locks. To
publish into the integration checkout, explicitly name that checkout and import
a completed verified bundle. Protect and stage the source under its own lock,
release that lock, then publish under the destination lock. Never hold two
checkout locks simultaneously. An index must not protect a mutable foreign
worktree path; deleting a worktree must not destroy already-published evidence.

### Lifecycle and cleanup policy

Use the following initial defaults in a versioned policy file, with the policy
version included in cleanup decisions:

| Class | Retention condition |
| --- | --- |
| Ordinary successful completed run | Seven days from terminal completion. |
| Ordinary failed completed run | Fourteen days from terminal completion. |
| Temporary investigation hold | Explicit expiry and reason; renewal is recorded. |
| Accepted evidence | Until explicit supersession by applicable evidence. |
| Cited observation | While its maintained citation exists, preferably in a compact bundle. |
| Release evidence | Existing verified archive and release-checkpoint policy. |
| Active execution, unknown ownership, or unresolved resource recovery | Protected independently of time and storage pressure. |

Use terminal timestamps, not directory names or modification times. Starting
the default clock at terminal completion avoids making a forgotten task-close
event an accidental permanent hold. A completed task can still extend a hold
explicitly. An expired lease alone never proves that a process exited or a
machine resource was removed.

Start with a configurable 10 GiB warning budget for local working output.
Report protected usage separately and offer eligible output in oldest-first
order. Budget pressure cannot override a claim, active execution, ambiguous
ownership or pending cleanup. This is a pressure signal, not a promise that
disk use can always be forced below the threshold.

Extend ordinary pruning with the resource checks already used by release
cleanup. Plan and revalidate under the same lock as retention updates, recording
run identity, claims generation, inventory and reasons in a cleanup journal.
Stage eligible directories into a separate ordinary-cleanup quarantine and allow
an explicit restore during a 24-hour grace period. A promotion racing with
quarantine must either establish protection before staging or fail with a
recoverable quarantine diagnostic; it cannot report success for deleted bytes.
Recheck claims and ownership before final deletion. Quarantine still consumes
space and must be reported as such.

Keep ordinary cleanup and `.release-rotation/` transactions distinct. Preserve
the release journal's existing recovery semantics and never unlink the checkout
lock. Clock anomalies should preserve uncertain output with a diagnostic.

## Execution order

1. **Introduce manifests and claim validation.** Add the schema, command API and
   generation controls without enabling automatic deletion. Read the current
   schema conservatively through an adapter; an old unmarked entry remains
   protected until explicitly migrated. Do not infer purpose or release tags
   from names. Extend ownership/claim controls and keep old archive readers.
2. **Bind runs to source snapshots.** Add unique default output allocation,
   source manifests, isolated acceptance execution, and source-specific
   acceptance publication. Establish the shared-checkout integration queue and
   test stale submissions before relying on acceptance supersession.
3. **Separate scratch and promote evidence.** Convert the named fixture producers,
   then inventory the remaining suites for retained build directories. Implement
   verified bundles and worktree import. Demonstrate that the original working
   directory can be absent while the promoted evidence still verifies.
4. **Migrate existing claims explicitly.** Inspect the current index afresh. The
   post-cleanup inventory has five local manual pins, three release entries and
   seventeen pins for absent paths; these counts are a migration starting point,
   not permission to remove newly added evidence. Promote the worker observation
   pair and the three current app-acceptance runs. Keep the successful signing
   and build-guard cases from the partly failed opt-in run: its successful rerun
   covered different cases. Verify all citations before retiring original paths.
   Record absent evidence as unavailable; do not fabricate archives or leave
   silent permanent path reservations. Preserve established release tags.
5. **Enable policy-aware cleanup.** Add expiry, budget reporting and quarantine
   controls, then switch manual pruning and release integration together. Invoke
   maintenance after task completion or as an explicit command. Unattended
   scheduling is a separate deployment choice; this plan installs no schedule.

Update `README.md`, `AGENTS.md`, the dispatcher and preflight suite references,
`catalog.json`, the Makefile help and the signing guide in their owning phase.
Keep generated documentation inputs aligned when affected; regenerate through
their owning tools. Historical archives and their embedded retention snapshots
remain unchanged. Preserve unrelated working-tree changes and commit only each
phase's reviewed files.

## Verification and completion

Use the existing dispatcher controls with independent filesystem observations;
test concurrent processes, not just sequential calls to an in-memory model.

| Control | Required observation |
| --- | --- |
| Concurrent claim additions | Both claims survive; neither silently replaces the other's index update. |
| Stale acceptance submission | A generation conflict refuses replacement; results remain attached to their tested source. |
| Main advances during execution | The isolated run and bundle retain their original source identity; current-main coverage is not invented. |
| Retain versus prune | Exactly one consistent outcome: protection before staging, or explicit quarantine refusal/recovery. |
| Interrupted ownership | Surviving protected descendants keep the execution lock; expired task metadata cannot permit deletion. |
| Pending external cleanup | Real session and registry-recovery receipts prevent ordinary and release deletion; nested synthetic fixtures do not create false holds. |
| Bundle publication failure | Missing/corrupt members, copy failures and crashes before publication leave originals protected and no valid claim pointing at incomplete evidence. |
| Partial acceptance replacement | Passing cases from a partly failed run remain credited until explicitly replaced; the original failure stays visible. |
| Worktree removal | Imported evidence verifies independently; foreign paths and symlink escapes are refused. |
| Expiry and quarantine | Boundary times, clock anomalies, restore, interrupted deletion and storage pressure produce the specified dispositions without touching protected output. |
| Migration | Old index and archive formats remain readable; unknown entries stay protected; absent paths are reported truthfully. |

Register controls in [catalog.json](catalog.json). Run the appropriate dispatcher
cases, `preflight/release_publish_controls`, `preflight/release_rotation_controls`
and `source_drift`, using fresh owned output. Run the affected runner fixture
cases after changing their scratch/evidence layout. Use the default battery for
final integration because dispatcher output and release readers are shared
infrastructure. Follow the documented unsandboxed retry procedure for equipment
restrictions. A passing parser or a clean metadata diff is insufficient.

Completion requires: no implicit permanent hold for a new ordinary run; no lost
claim under concurrent writers; no acceptance assigned to an untested source;
portable evidence independent of deleted working directories; demonstrably
bounded ordinary retention; and preserved execution/resource cleanup ownership.

## Limits and consequential risks

This work changes test evidence management, not the product wire protocol,
sandbox behavior, release signatures or historical results. It does not replace
the execution lock, add distributed storage, or promise reproducibility from a
source hash alone.

The highest-risk boundary is deciding which files are evidence. Convert producers
incrementally and require independent verification before releasing old runs.
The next is shared-checkout source mutation: a retention API cannot make an
uncoordinated working tree immutable. Isolated execution and explicit integration
ownership are requirements, not optional claims inferred from a successful test.
