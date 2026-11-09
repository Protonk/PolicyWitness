# Local release retention

## Intended result

Keep the four newest complete local release archives, including their portable
test evidence, and keep only the newest archived release's unpacked acceptance
directory with its nested battery. Remove discretionary test-result pins and
the exception that retains the newest completed development run. Development
output may accumulate between cleanup operations; successful release packaging
and explicit pruning are the cleanup checkpoints.

Replace the tracked `tests/RETAINED.json` index with one central policy and
protection derived from release records. A generated report may explain the
decision, but it is not another editable retention authority. Active work,
unknown ownership and unresolved resource cleanup remain deletion blockers.
They do not create discretionary evidence pins.

Support the current release workflow without maintaining deprecated operating
paths across versions. Remove obsolete readers, writers, fixtures and wrappers
with their callers. A temporary migration reader must have a specific remaining
storage obligation and an explicit removal condition; it is not a general
compatibility layer. Stage implementation and destructive cleanup deliberately,
without turning that pacing into indefinite support for the old workflow.

This document plans implementation and the subsequent local cleanup. Adding
the plan does not perform either. Git history, annotated release tags and
GitHub releases remain intact. Tags are still needed for public surface-stamp
derivation. Shipped runtime behavior and public contracts are outside this
change.

## Starting point

The inspection on 2026-11-09 was made after `v0.3.6` was archived and published,
at commit `53546e2c` (`Retain the 0.3.6 release evidence`). These are observations
of local records and paths, not a fresh verification of archive contents.
Refresh the inventory before applying cleanup.

| Local material | Observed state |
| --- | --- |
| Release archives | `v0.2.7`, `v0.2.8`, and `v0.3.0` through `v0.3.6` |
| Portable evidence formats | Schema 1 through `v0.3.3`; schema 3 for `v0.3.4` through `v0.3.6` |
| Unpacked release evidence | Only the `v0.3.6` acceptance directory remains; the older manifests' working paths are absent |
| Release acceptance | `tests/out/release-acceptance/run-037c2f300b5f44f186b75c91facb15ec`, owner `accept-b9249da88e604c44a251ab5cf2c5947b` |
| Explicit development pins | `runs/release-contracts-doc-review-26` and `runs/release-contracts-release-preflight-31` |
| Existing release rotation | All inspected archive journals report completion; `tests/out/.release-rotation/` is empty |
| Current footprint receipts | [FOOTPRINT.md](docs/FOOTPRINT.md#provenance-of-measured-rows) cites the `v0.3.6` archive |

The initial cutoff removes `v0.2.7`, `v0.2.8` and `v0.3.0`. Applying the window
to the remaining current inventory also removes `v0.3.1` and `v0.3.2`, leaving
`v0.3.3` through `v0.3.6`. The earlier five-to-four example preceded the new
release: it would have kept `v0.3.2` through `v0.3.5`. Implementation must compute
the window from the execution-time inventory rather than hard-code either set.

Release-linked material also exists outside `dist/archive/`:

- Each archived attempt leaves a `dist/evidence/*.archived` pointer naming its
  archive's evidence directory.
- `dist/evidence/20261011T021113Z-ivihc2y5/` identifies a superseded `0.2.8`
  attempt and contains its ZIP, guide and portable test evidence.
- `dist/evidence/20261011T021044Z-1ehlxaed/` records a notarization lookup whose
  submission ID matches the `v0.2.7` archive.
- `dist/evidence/20261031T022350Z-lsw7xveb/` identifies a failed `0.3.4` attempt,
  which remains within the current window.

These associations come from records, hashes and submission IDs. Directory
names and timestamps alone do not establish them. Failed or superseded attempts
do not consume a slot in the release window; settled attempts associated with
an expired release become eligible alongside that release.

## One policy and derived protection

Make `tests/lib/retention.py` the policy, inventory and cleanup owner. Keep the
archive count there, and fold the candidate, blocker and quarantine logic from
`release_cleanup.py` and `release_rotate.py` into it. Remove the index-specific
`retiring` journal state, `check_retention` and entry validation. Update callers
and remove those two modules; do not retain forwarding wrappers for their old
entry points. Keep the supported release and prune commands routed through the
single policy owner.

Move run-directory ownership, disposition and shared receipt helpers into a
small `run_ownership.py` module. Keep the existing lock implementation in
`checkout_lock.py`; do not introduce another lock or ownership protocol. Have
callers supply derived protection to output-creation helpers, avoiding a
circular import between ownership and policy. The dispatcher, acceptance
writer, archiver and pruners obtain protection from the same policy owner.

The default archive root is this checkout's `dist/archive/`. An alternate
distribution root must be an explicit shared policy input wherever archiving,
output replacement and pruning interact; a custom `DIST_DIR` must not silently
create release evidence that the dispatcher cannot protect.

Order complete archived releases numerically by `(major, minor, patch)` across
the archive root. Keep the four newest, or every complete archive when four or
fewer exist. Require the archive directory, release record, asset identity and
evidence manifest to agree.
Ignore staging directories as release candidates, and report unrecognized or
inconsistent material without deleting it. Publication is not required to enter
the window: successful verified local archival is the existing checkpoint.
A failed build, failed acceptance, tag alone or incomplete archive cannot
advance the window.

Derive acceptance-to-archive handoff protection from existing unarchived
attempt records in `dist/evidence/`. Share the predicate used by
[find_latest](tests/lib/release_archive.py): accepted notarization, successful
acceptance and an accepted ZIP hash equal to the current final ZIP. Bind the
attempt's `acceptance.json` path to its acceptance owner before protecting it.
Zero matches means no completed handoff; ambiguous matches or inconsistent
records are blockers. Active acceptance remains covered by its existing
lifetime lock. A valid interrupted handoff remains protected until archiving
or supersession is established from the records. No new lease, handoff journal
or recovery protocol is needed.

The newest complete archived release supplies the protected acceptance path
and run identity. Protect that acceptance directory as a whole (the directory
holding the recorded `acceptance.json`, not the `release-acceptance/`
container), including its nested battery, from both cleanup and dispatcher
output replacement. Preserve ancestor/descendant overlap checks. A missing
protected working path remains reserved and is reported; a different owner at
that path must not be treated as the release's acceptance. An empty archive
inventory in a fresh checkout is a valid state; an unreadable or contradictory
inventory must not become an empty protection set.

Remove `tests/RETAINED.json`, its handwritten entry validation and mutation
interfaces, suggested-pin messages, and the post-release instruction to commit
the index. Existing archive manifests may retain their historical `retained`
objects as immutable provenance. Reading a path and run ID from those objects
does not reinstate the old manual-pin policy. New archives still need a bound
acceptance identity and original working location, but no separate mutable
index. Preserve shared JSON-writing utilities used by other receipts.

## Release order, expiration and footprint transcription

Require new local releases to increase numerically. Preflight refuses a target
at or below the newest complete local archive; the archiver repeats the check
under the checkout lock before exposing a new archive. Thus `0.3.7` after
`0.4.0` is refused before build/notarization, rather than accepted with
immediately unprotected acceptance output. Cleanup also refuses an older
checkpoint when a newer complete release exists.

The window always retains its newest complete archive, so that archive supplies
the released-once guard for every version expired by this policy. Keep the
existing destination-collision refusal as well. Remove expired archive
directories completely; do not create permanent `retired.json` placeholders or
a separate release-history ledger. This guarantee covers managed local history;
it does not reconstruct releases in a fresh checkout with no local archives.
Unreadable or inconsistent history remains a blocker. Running release or prune
scripts from historical checkouts against the migrated layout is unsupported;
preserving their former path-existence guard is not a migration requirement.

An unpublished archive may expire under the same window. Publish it while its
complete archive is retained; after expiry `make publish VERSION=...` cannot
publish that release from local storage. Publication failure does not create a
pin or change the window.

Move footprint transcription into the next release-preparation commit.
Before tagging release N+1, transcribe release N's archived measurement receipts
into `docs/footprint.json`, regenerate `docs/FOOTPRINT.md`, and update its
provenance. The N+1 tagged tree still reports N's measurements, as tagged trees
already do; main may lag until that preparation. After N+1 is archived there
is no required post-tag retention/footprint commit.

Add a preflight check that FOOTPRINT's measured-row provenance names the newest
complete local archive available before the proposed release, with the matching
acceptance and battery identities. This is a provenance-freshness check, not a
claim that the transcribed numbers have been independently verified. Keep the
existing manual review and generator checks. If no complete local archive
exists, report that the comparison is unavailable rather than inventing one;
an existing but unreadable archive is a refusal. Preparation and transcription
precede committing/tagging, so this check does not require editing a tagged
tree. In the normal sequence the cited archive is newest at preparation and
still inside the window after the next release.

## Cleanup and recovery

Provide one planner for archive retention and disposable test output, exposed
through a read-only preview and an explicit apply operation. Use it after
successful archival in `make release` and for independent catch-up pruning.
An ordinary test run does not trigger a sweep. Share classification and
protection while keeping the entry points' unfinished-output rules explicit:

| Entry point | Unfinished-output rule |
| --- | --- |
| `make prune` / `tests/run.sh --prune`, including `--apply` | Preserve interrupted and ambiguous output. Clean eligible completed output and expired release material only. |
| Explicit `--unfinished <name>` | Retain the existing targeted operation for one owned unfinished direct run, subject to protection and resource checks; do not broaden it into a sweep. |
| Successful release checkpoint | May retire owned unfinished output only when it started before that release battery, after ownership and resource checks. Newer unfinished work stays. |

Explicit catch-up pruning does not borrow an old release's timestamp to gain
checkpoint deletion powers. Identify the entry-point mode in the preview and
journal. Update `make prune` and its documented archive-cleanup scope together
with that integration.

The plan names kept, eligible and blocked paths, with identities and reasons.
It covers expired archive directories, positively linked attempt directories
and pointer files, older unpacked acceptance directories, and eligible managed
development output. All completed managed development runs, including failures,
are eligible; there is no newest-run exception. Unfinished output follows the
entry-point rules above. Active acceptance, unresolved pytest ownership,
pending BYOXPC cleanup, redirects and unknown ownership remain blocked. The
pruner never settles machine resources by deleting their receipts.

Apply takes the existing stable `tests/.checkout.lock`, reloads the policy and
inventory, and rechecks each target's identity and bytes. It records a durable
transaction before staging directories into quarantine. Store the transaction
receipt beneath a retained release's evidence, outside every selected target;
when no complete archive exists, use `dist/evidence/retention/` for the
administrative receipt rather than synthesizing a release. Use quarantine on
the same filesystem as each source. Record the relationship between the
distribution and test-output quarantine areas. Do not delete a release that
contains an unfinished cleanup journal.

Resumption checks the original inventory and remaining quarantined bytes. It
must tolerate partial deletion, preserve replacements created at original
paths, and finish pointer cleanup without leaving unexplained dangling links.
An `.archived` pointer to a retired payload is removed with that payload.
A completed transaction is a no-op when resumed. A later explicit pruning
operation may create a new transaction against the same current release; it
must not overwrite an earlier receipt. Recheck the retained release set if
archival advanced after preview.

Existing completed `evidence/rotation.json` files remain historical receipts.
An unfinished old transaction can only be resumed by the current
`release_rotate.py` and index, so check for one before the implementation
replaces them: every archive journal must report completion and
`tests/out/.release-rotation/` must be empty. Resolve any exception with the
current tools first. The current verifier refuses the schema-1 archives, so an
unfinished journal in one of them could not be resumed and is a stop for
review. Afterwards the new planner treats an unfinished old journal or leftover
quarantine as a blocker. Do not reinterpret an old journal under the new policy
or remove `tests/.checkout.lock`.

## Current evidence verification and temporary historical inspection

[The evidence reader](tests/lib/release_runs.py) currently accepts portable
bundle schemas 2 and 3. No local archive uses bundle schema 2; the observed
`v0.3.4` through `v0.3.6` archives use bundle schema 3 and carry execution
contracts. Local schema-1 bundles are already outside its acceptance support.
Make the ordinary reader and writer current-format-only during the main
implementation, without waiting for `v0.3.3` to expire. The remaining schema-1
storage needs a separate, temporary inspector for retention classification.

The current formats have different counters: `release.json` uses schema 2,
the portable bundle manifest uses schema 3, and acceptance uses schema 3.
Removing bundle schema 2 must not remove current release records. The
`execution_contract` describes captured test selection and family obligations;
it is distinct from the public build identity such as `release:v0.3.6`.

Make the following reader and producer changes together:

- Require an independently supplied, validated execution contract in
  `release_runs.pack` and `verify_bundle`; remove the optional-contract defaults,
  schema-2 packing branch and conditional bypass of semantic verification.
  `battery_source` accepts only the current bundle layout. Make
  `producer_contract` require the current release record and its contract,
  removing its historical-source exception and `HISTORICAL_PRODUCERS` from the
  ordinary reader.
- Remove `release_archive.battery_record`'s contract-free path, including for a
  catalog with no pytest families. New archival compares acceptance against
  the current checkout's independently captured default contract and validates
  the nested battery. Always write the current release record with that
  contract; remove the schema-1 record-writing branch.
- When rereading an existing archive, use the execution contract captured in
  its release record as the independent expectation for its portable bundle.
  Do not substitute the current checkout's catalog or recapture its defaults:
  retained schema-3 archives remain readable as the catalog evolves. Preserve
  ZIP/provenance binding, transport inventories and hashes, default-selection
  checks, family phase accounting and resource-closure assertions.
- Convert `check_release_publish.make_dist` and its rotation consumers to
  current acceptance, battery and release records. Capture the expected
  contract before mutations, outside the mutable evidence under test. Remove
  the synthetic historical-producer allowlisting,
  `expected-historical-producers.json` fixture sidecar and child-process
  restoration of that allowlist. The small three-case catalog may remain;
  its current dispatcher engine label `legacy` is unrelated to old bundle
  formats. Native family obligations retain their separate integration
  coverage.

Update direct `pack` and `verify_bundle` calls in the rotation controls to
supply the independent contract. Preserve their default-selection, malformed
battery-reference and transport-integrity assertions; a missing argument or an
earlier format refusal must not stand in for the intended diagnostic. Update
portable-copy assertions to the current bundle format while retaining their
independent inspection of stored files and symlinks after working paths are gone.

In `pytest_integration.py`, separate the `contract-copy` mutation into a
schema-3 bundle missing its contract and an explicitly downgraded bundle.
Otherwise the new format refusal would replace the intended missing-contract
assertion with an earlier failure. Keep independent expectations outside the
repacked evidence and require each control to reach its stated boundary.
Remove the positive allowlisted historical-neighbor assertion; keep missing
producer-contract refusals and the semantic deletion controls for engine
references, family evidence, ownership and operation receipts. Old-format
negative controls remain refusals, not supported-format fixtures.

Update the reader's module description, producer/test comments, signing
procedure and preflight/distribution references with the new support boundary.
Remove the promise that historical schema-2 bundles remain readable. Do not
retain an alternate verifier, upgrade converter or compatibility switch for
them.

Calling the ordinary full verifier on every local archive would block initial
retirement and classification of retained `v0.3.3`, so keep that operation
separate from the temporary storage inspection below.

Add narrowly scoped storage inspection for the recognized historical layout:
bind the version, source identity, asset hashes, manifest hash, declared bundle
hashes, original paths and run IDs. Validate containment without following
links or executing archived programs. This establishes which stored bytes are
being retained or retired; it does not establish current semantic acceptance
or restore historical publishing support. Do not regenerate or migrate old
archives. Corruption or an unsupported layout is an explicit blocker, never
permission to delete by directory name.

Keep the four-archive window during migration; do not reduce it to three to
avoid legacy inspection. Use the six established source identities currently
listed in `release_runs.HISTORICAL_PRODUCERS` to anchor positive recognition;
move them into the temporary inspector with the archive/hash checks above.
Do not leave them in acceptance verification. Missing current-format fields
alone never establish a historical producer.

The inspector is temporary. Its retirement trigger is that the last local
schema-1 archive has expired, every associated deletion has completed and no
journal or quarantine still needs its reader. With this inventory that occurs
when the next increasing release displaces `v0.3.3`, unless cleanup is blocked.
Then remove the inspector and its historical-producer identities. No bundle
schema-2 acceptance branch survives the main implementation. Retire positive
schema-1 inspection fixtures with the inspector, while retaining ordinary
refusal coverage for unsupported or falsely relabeled formats. There is no
permanent historical-storage reader after that condition is met.

## Evidence dependencies

Review live documentation dependencies before retiring evidence. Update claims
to cite a retained release only when its observations actually support them;
otherwise make the availability limit explicit or obtain replacement evidence
as part of the owning work. Do not preserve development pins by copying their
contents to an ungoverned directory. Existing tracked fixtures and historical
records are source material and are not automatic cleanup targets.

The publisher uploads the release ZIP, guide and checksums, not the portable
test bundle. Archive retirement deliberately removes that local evidence.
Preserve release tags and published assets; no new backup service or remote
deletion is part of this change. The current root app, ZIP and guide are build
outputs, not expired archives selected by a filename or embedded old version.

## Implementation surfaces

| Owner | Work |
| --- | --- |
| [retention.py](tests/lib/retention.py), [checkout_lock.py](tests/lib/checkout_lock.py), [test_cli.py](tests/lib/test_cli.py), [release_accept.py](tests/lib/release_accept.py) | Make retention the policy/cleanup owner, move run ownership helpers out, replace index-derived protection and remove manual-pin output without replacing the lock protocol. |
| [release_archive.py](tests/lib/release_archive.py), [release_runs.py](tests/lib/release_runs.py), [execution_contract.py](tests/lib/execution_contract.py) | Require current records and independently captured execution contracts; remove legacy packing/admission and contract-free verification. Publish the complete archive atomically, remove index writes, preserve archive-to-acceptance binding and isolate temporary storage inspection. |
| [release_preflight.py](tests/lib/release_preflight.py), [publication helper](tests/lib/release_publish.py) | Enforce release ordering from the newest complete archive, preserve destination-collision checks, check footprint provenance freshness and refuse publication without a complete archive. |
| [release_rotate.py](tests/lib/release_rotate.py), [release_cleanup.py](tests/lib/release_cleanup.py), [Makefile](Makefile) | Consolidate cleanup into retention and remove the old modules and callers without compatibility wrappers. Preserve entry-point deletion limits and implement resumable archive retirement without permanent per-version markers. |
| [Dispatcher fixtures](tests/fixtures/dispatcher/repository.py), [retention controls](tests/suites/dispatcher/check_retention.py), [release rotation controls](tests/suites/preflight/check_release_rotation.py), [publication controls](tests/suites/preflight/check_release_publish.py) | Replace handwritten-index fixtures with independent release inventories and migrate release fixtures to captured current contracts. Remove historical allowlist sidecars and obsolete pin/index assertions while retaining ownership, integrity and filesystem boundaries. |
| [Live release-battery fixture](tests/fixtures/release/live_battery.py), [pytest integration controls](tests/suites/dispatcher/pytest_integration.py) | Derive acceptance protection without the real index. Split downgraded-format and missing-contract controls, remove positive historical-producer acceptance, and preserve native family and unresolved-resource assertions. |
| [Source drift rules](tests/suites/source_drift/check.py), [planner mutation controls](tests/suites/source_drift/check_planner.py) | Keep the bare/default battery and `--prune` routing restrictions coherent with the Makefile. Preserve mutation sensitivity when the prune recipe changes. |
| [Preflight wrapper](tests/suites/preflight/run.sh), [catalog](tests/catalog.json) | Replace step text and descriptions promising pins, newest-development retention or index retirement. |
| [SIGNING.md](docs/SIGNING.md), [BUILD.md](docs/BUILD.md), [distribution README](dist/README.md), [distribution rules](dist/AGENTS.md), [test README](tests/README.md), [test rules](tests/AGENTS.md), [preflight reference](tests/suites/preflight/README.md) | Describe the window, single unpacked acceptance, lock holders, explicit/checkpoint cleanup limits and recovery. Remove indefinite retention, manual pins and historical bundle-verification promises; distinguish current release-record schema 2 from portable bundle schema 3. |
| [Footprint manifest](docs/footprint.json), [FOOTPRINT.md](docs/FOOTPRINT.md), [documentation rules](docs/AGENTS.md) | Move transcription to the next release preparation, preserve receipt attribution and explain that provenance freshness does not verify measured values. |

Also update affected catalog descriptions, fixture input declarations, release
acceptance controls and remaining references to `RETAINED.json`, including
dated availability statements in worker and comparison documentation. Follow
generator ownership for generated accounts. Review build-input declarations if
new imports become dependencies of build helpers; regenerate only the accounts
whose owning inputs actually change.

## Verification and migration

Use disposable fixture repositories through the existing dispatcher. Retire
tests whose only purpose was handwritten-index syntax, arbitrary pins or index
replacement. Keep independent byte inventories and real child-process failure
controls for the mechanisms that survive.

| Proposition | Required observation |
| --- | --- |
| The window is exact | Inventories with zero through six releases retain at most four complete archives; five-to-four and six-to-four transitions select the right versions. Test numeric ordering across `0.3.9`/`0.3.10` and a minor-version boundary. Failed attempts and incomplete archives never displace a release. |
| Release order and released-once checks survive pruning | With expired archive paths completely absent, current preflight and direct archival refuse expired tags using the newest retained archive. `0.3.7` after `0.4.0`, an existing destination and an older cleanup checkpoint are refused. Expiry never removes the newest archive; unreadable history is not treated as empty. |
| Only current acceptance and an actual handoff are protected | Dispatcher replacement and pruning refuse overlaps with current acceptance. Accepted unarchived attempts matching the final ZIP protect their recorded acceptance; foreign hashes, ambiguity and changed owners cannot manufacture protection or deletion authority. Older acceptance and settled development output become eligible, even the newest development run. |
| Entry-point powers remain distinct | Ordinary explicit prune preserves interrupted/ambiguous runs regardless of age; targeted `--unfinished` affects only its named eligible run; a release checkpoint alone uses the battery-start cutoff. Exercise active, pending-resource and newer-unfinished blockers in every mode. |
| Linked copies are selected by evidence | Matching pointers, superseded assets and known attempt receipts expire together. Similar names, unrelated files, tracked historical fixtures, the current app and remote assets are untouched. |
| Historical inspection is bounded | Recognized schema-1 storage can be classified without passing current semantic acceptance; malformed identities, hashes, layouts and redirects block mutation. Surviving archive bytes remain unchanged, apart from the transaction receipt added to the release that holds it. Its retirement test requires no remaining legacy archive or dependent transaction. |
| Current evidence requires its captured contract | Schema-3 fixtures verify with independently captured contracts, including a valid contract with no pytest families. Missing producer or bundle contracts and schema-2 downgrades fail at their respective boundaries. Fully repacked semantic deletions still reach family/ownership verification. A later checkout catalog does not replace a retained archive's captured contract. |
| Preview is read-only | Independent before/after inventories show no writes, including when no archive exists or a blocker is encountered. |
| Apply is serialized and recoverable | Real competing processes respect the stable lock; abrupt exits after staging, policy recheck, partial deletion and pointer cleanup resume correctly. A replacement at an original path survives. An unfinished old journal or leftover old quarantine blocks apply. Remove the obsolete index crash case; exercise the surviving transaction boundaries directly. |
| Publication and acceptance still bind exact bytes | Failed archive construction cannot advance protection or delete evidence. A prune competing with the acceptance-to-archive handoff preserves its evidence. The default extracted-app battery remains the release acceptance source; publishing still verifies its archive. |
| Footprint preparation cannot silently stay behind | Preflight refuses provenance older than the newest complete local archive or with wrong acceptance/battery identities; fresh provenance passes without requiring measurements from the not-yet-built release. Missing local history is reported separately from invalid history. |

Run the affected `dispatcher/retention_controls`,
`preflight/release_controls`, `preflight/release_publish_controls` and
`preflight/release_rotation_controls`, plus affected dispatcher ownership,
pytest-resource and source-drift cases, through `tests/run.sh` with fresh output.
Exercise the release sequence in its existing controlled fixture environment;
do not notarize or publish merely to test retention. Credit the exact commands,
source state and results before permitting destructive migration.

With the simplified reader, perform full read-only verification of the actual
`v0.3.4`, `v0.3.5` and `v0.3.6` archives, using each archive's captured execution
contract. The starting inventory's format/field inspection is not this check.
Verify any subsequently archived current-format release too. Failure blocks
reader acceptance and destructive migration; do not silently restore a legacy
bypass to make it pass. These checks do not rebuild, extract into the managed
acceptance directory, or modify historical bytes.

Confirm that no old cleanup transaction is unfinished before the implementation
replaces its recovery path. Implement the policy, callers, fixtures and
documentation together, then:

1. Refresh the local inventory under the new preview. Check every old pin for
   active ownership or resource-recovery obligations, without converting it to
   another indefinite pin. Confirm the preview reports no old journal or
   quarantine blocker.
2. Review the explicit cutoff and window decisions. With the observed inventory,
   retire releases before `v0.3.1`, then `v0.3.1` and `v0.3.2`, retaining
   `v0.3.3` through `v0.3.6`. If another release exists, recompute the window.
3. Apply through the new helper when no build, battery or acceptance is active.
   Remove eligible linked material and non-release working results. Report
   blockers as incomplete cleanup rather than silently expanding the policy.
4. Verify the surviving archive set, the current acceptance identity, pointer
   targets and completed transaction receipt. Confirm no unexpected quarantine
   remains and that the remaining archives' inventories are unchanged apart
   from the receipt added to the release that holds it.

Completion means the tracked manual index and its live consumers are gone,
one policy governs replacement and cleanup, the ordinary reader and writer have
no legacy-format or missing-contract path, the old cleanup modules and wrappers
are gone, and the required controls pass. The local migration has either reached
the declared window or names each unresolved ownership/resource blocker.
Future successful archival enforces the same window; footprint transcription
happens in the next release preparation, with no required post-tag
retention/footprint commit. Retire the temporary historical machinery when its
stated condition is met.
