# Candidate implementation sequence

Candidate worktree: `/private/tmp/pw-pytest-exec-candidate-20261030`.
Branch: `adoption/pytest-exec-family`; starts at authorization amendment
`8fd2c825`. Accepted checkout remains at `77eb9875` with its unrelated untracked
review materials. The frozen investigation and protected resources are unchanged.

## Preparation and stage 2 checkpoint

Provisioned the five pinned wheels into the interpreter/lock-keyed package target
using `tests/setup-pytest.sh --wheels .tmp/pytest-wheels`. This is explicit setup,
not collection-time installation. The lock records wheel URLs and SHA-256 digests.
Interpreter: `/opt/homebrew/opt/python@3.14/bin/python3.14`, 3.14.9; pytest 9.0.2.

The initial implementation adds the domain/module organization and the PW command
owner, durable registry and independent source-contract reader. The ordinary F
route is still the accepted shell route. The registry is **not yet** a shared
admission dependency. `dispatcher/pytest_controls` exercises the boundary before
that switch. Its observation file is authored by the external control, not the
candidate report interpreter. Fixture registry ambiguities are deliberately
retained inside that control's evidence, without claiming a production recovery
basis. Their launcher was never invoked by the fixture controller.

No acceptance claim has yet been made. Subsequent source commits, fresh run
identities, corrections and dispositions are recorded below before final sealing.

### Consequential failure and correction

Source `46ec2289`: pinned `pytest-exec-ownership-01` and unchanged unsandboxed
repeat `pytest-exec-ownership-02` both failed after the controlled supervisor's
death. `owner.stderr` records `killpg(SIGKILL)` raising EPERM. The native peer and
owner exited (the control registered kernel exit observers before killing its
own supervisor), but settlement was never published; the registry correctly
remains checkout-blocking. This is not labelled environmental: the unsandboxed
repeat failed too. These are isolated nested fixture registries, not active
candidate-checkout ownership claims.

The correction polls/reaps before signalling and treats macOS zombie-group EPERM
as **not yet absent**, as the existing group observer already does. It never
turns EPERM into cleanup permission. The control now persists its external exit
observations before asserting the candidate's disposition. The failed runs'
empty recovery socket directories remain protected pending separately supported
bookkeeping; their paths and missing settlement are in each operation record.

Source `71558219`: pinned `pytest-exec-ownership-03` passes. External command
start, kernel exit events and physical-lock observations are in `observations.json`.
The corrected receipt moves to output-only protection and explicit recovery
closes it idempotently. The source-contract control rejects removal of family
engine/reference/state and ownership roles with its expectation fixed externally.
This checkpoint permits activating shared guards in the candidate. No production
admission behavior was changed before that observation.

Stage 3 switches only F to pytest and removes the shell block/executable native
loop. The canonical parser remains importable. Shared build admission, pruning,
release acceptance and portable readers now use the ownership/evidence contract.
New current documentation describes the public command and recovery operations.
The next observations test this integrated route; they are not acceptance yet.

Source `b1f697e1`: `pytest-exec-normal-01` is the first public candidate F run.
Nine complete passing items, unchanged 58-attempt ledger, 16 settled commands,
and unchanged accepted app inspection are retained. Diagnostic/negative controls
now run actual family source in explicitly isolated fixture checkouts; their
catalog omits app equipment only for native/reporting interventions. This does
not change F's production catalog admission. Normal accepted-app verification
and existing selection/artifact controls cover that separate boundary.

Source `7852f03a`: pinned `pytest-exec-integration-01` passes the actual-family
normal, formation, accepted-mutation, wrong-rejection, shared baseline, both
shared-finalizer classes, setup-before-yield, simultaneous body/teardown,
collection, missing-package, valid-prefix and portable semantic deletion controls.
The emitted walkthrough source paths are in its `observations.json`.

Five existing groups failed: selection's opt-in membership list had not included
the new opt-in case; release fixtures lacked the new independent producer data or
a source catalog; build refusal's C-locale stimulus inherited `LC_ALL=C.UTF-8`.
A read-only probe shows `LANG=C` with that override never coerces LC_CTYPE, with
or without `-E`. The build/refusal source is unchanged. Rerun that control with
LC_ALL absent rather than change its oracle or production behavior. Release
fixtures now declare their actual three legacy cases independently, and historical
archives retain their positive old-format identity. Current acceptance still
requires the new contract before launch; none of these corrections permits a
new family to fall back to historical interpretation.

Source `9aa2d963`: pinned `pytest-exec-integration-02` passes all selected groups,
including the complete C-worker suite. The new controls observed one completed,
one active and queued items, real command/child peer identities and kernel exits
under engine death, ordinary interruption and engine+supervisor death. Parent
states and continuation/cancellation matched independent expectations. Recovery
covered reserved, ambiguous authorization/start, durable settlement before closure,
active/live owner refusal and public recovery while ordinary admission refuses.

Walkthrough found an ordinary diagnostic defect in retained formation failures:
`expectation.json` prematurely called the proposed mutation “submitted” before
checking its anchor. The native test correctly failed formation; the receipt was
misleading. The correction preserves proposed/unformed status and pre-formation
source inventory, then publishes “submitted” only after formation. Reports also
stop linking to nonexistent native directories for bodies that never ran.
Publication-failure review added an explicit parent fallback retaining
started/incomplete (or unknown/incomplete) if the family summary cannot be
published. These changes preserve the native oracle; final controls inspect the
emitted states and receipts.

Periodic supported prune preview kept all decisive pins and the active run. It
found no disposable completed run to remove; no prior engagement evidence was
modified. The full build-refusal regression runs on fixed `9aa2d963` in
`/private/tmp/pw-pytest-exec-build-check-20261030`, separately from ongoing sources.

Source `56aaf019`: `pytest-exec-final-controls-01` passes the diagnostic corrections,
summary-publication refusal (`started/incomplete`), initial-publication refusal
(`unknown/incomplete`), accounting/retention regressions, source/generator checks,
Python startup checks and real F against the accepted app. The remaining targeted
addition exercises actual process loss in the authorization/PID-publication and
direct-return/settlement windows, beyond the already passing constructed-state
disposition table. These are isolated copies of the same owner code, with externally
observed peers and kernel exits, not production fault switches. It also checks the
shared build lock front end refuses the same pending records and that the family
summary selection agrees with the already-fixed parent collection manifest.

Source `298624d6`: pinned `pytest-exec-windows-01` passes the earlier controls and
all release readers, including clang/app refusal and shared build-front-end
ownership refusal. The first real crash-window observer failed with ENOTCONN
before identifying the engine peer. Inspection found the instrumentation kept
that socket only in a collection-hook local; return closed it while the engine
continued. This is an observer defect, not a candidate recovery result. The
correction keeps the observer socket on the plugin instance for the engine
lifetime. The failed nested fixture's reservation and any missing exit evidence
remain retained; no historical PID is signalled or reservation force-cleared.

Source `9beb44b1`: `pytest-exec-windows-02` passes every registered integration
control, including four actual crash windows. `independent-starts.json` and
`independent-exits.json` retain live peer identities and registered kernel exits.
Before command release, the owner publishes affirmative never-launch settlement
and recovery closes it. Before owner launch, before start publication and after
direct return with a surviving child, missing settlement remains a checkout hold.
External controlled peers establish and settle their actual process lifetimes;
those observer facts do not silently manufacture a missing owner receipt. The
nested fixture records and stale recovery endpoints remain protected and indexed.

Final reader review makes the independent compatibility anchor explicit: absent
new release declarations require a source in the finite historical-producer set,
whose identity is also checked against the ZIP's build provenance. The six source
IDs come from the unchanged accepted v0.2.7–v0.3.3 archive records (unsupported old
bundle schemas still refuse). A new/unknown source cannot downgrade by erasing its
contract and version fields. Historical synthetic release fixtures explicitly
declare their own known legacy source identities before mutation. The actual-family
portable control now constructs its expected source/selection contract independently
before ordinary execution, rather than taking even that initial copy from run.json.

Source `40e81695`: pinned `pytest-exec-acceptance-01` passes F and all integration
controls, including independently fixed source expectations and removal of the
outer contract/version hints. Interrupted release rotation failed because its
fresh subprocess did not inherit the parent fixture's in-memory legacy-producer
set. The fixture now carries a parent-authored source declaration outside the
mutated archive and explicitly loads it in the crash child. Production readers
still require positive provenance; their rejection was correct.

The fixed `9aa2d963` build worktree's pinned `pytest-exec-build-refusals-01` passed
all full/partial baseline/refusal rows and the first six sequences, then its
secondary-worktree fixture omitted pytest_resources.py/pytest_support.py. The
candidate explicitly copies those shared lock dependencies. Its real-default-
battery fixture also needs a verified copy of the host's pinned pytest target;
that equipment is copied explicitly, with no runtime download. Those two opt-in
integration controls now declare pytest equipment. Continue the remaining
sequences and mutation phase through the existing `--only` development entry,
wrapped by the public case in a separately sealed verification worktree; retain
the prefix and continuation as distinct evidence, not an uninterrupted full run.

Environment walkthrough also clarified two field names: `dont_write_bytecode`
and `disable_plugin_autoload` now state their actual predicates. Controls check
those predicates, absent site initialization/ambient packages, locale preservation
and the actual lock inode through pytest fd capture. The observed behavior was
already correct; the earlier field labels were ambiguous.

Final ownership review found a candidate admission gap: the shared guard ran at
checkout acquisition, but a still-unresolved family operation could be followed
by an already-selected legacy case under that same acquisition. The correction
checks resource eligibility before each invocation, without changing selection or
pytest item scheduling. The actual owner-death windows now include queued legacy
work and require an explicit ownership refusal. A dropped-native-descriptor
control and a closed-label/false-settlement control test the rejection side of
the hold contract. This is an ordinary integration correction within the selected
ownership boundary, not a change to application or native-test promises.

Source `eb4bcc11`: pinned `pytest-exec-acceptance-02` passes corrected historical
fixture handoff, selection, actual-family diagnostics and F. Source `b1cff674`:
pinned `pytest-exec-acceptance-03` passes all final ownership/accounting/cancellation/
retention controls and F. Review of its actual summary found the shared baseline
cause followed eight repeated setup tracebacks. The phase evidence was correct,
but the ordinary display made the reader scan redundant diagnostics. A final
renderer correction puts shared baseline/finalizer scope before item results and
groups the eight explicitly identified baseline setup errors. Raw phase and pytest
diagnostics remain complete; unrelated setup failures are never collapsed. The
control now inspects prominence, eight blocked bodies and preserved detailed
reports. This correction is confined to diagnosis, not native expectations.

Source `74ef845f`: pinned `pytest-exec-acceptance-04` passes all eight selected
source/startup, diagnostic and family checks. The grouped explanation is now
verified from emitted reports. Final contract review completed a bookkeeping
detail from the plan: command argv/root were retained, but no explicit environment
identity accompanied registration. Each reservation now records cwd and a digest
of the filtered inherited environment; the owner checks it before launch and
carries it into its receipt. Inherited values are not published. The existing
native descriptor/capture control also observes cwd/locale and independently
checks the recorded digest. This changes experimental accounting only.

Source `bdb007a2`: pinned `pytest-exec-acceptance-05` passes the complete registered
pytest integration controls and real F, including the final command-context
identity and emitted diagnostic experience.

Build continuation source `9cbed1b8` completed its five selected build sequences
and all 202 default-battery cases. Exactly one failed: the SDK containment fixture
in `preflight/build_provenance_controls` copied checkout_lock.py without its new
shared registry helpers. The other 201 cases, including F, passed; the release
reader correctly refused overall acceptance. `pytest-exec-build-continuation-01`
is pinned in the verification worktree. Add the two helpers to that fixture's
explicit input list, verify that existing case directly, then repeat only the
remaining release-battery and mutation sequences on fixed candidate-derived
source. No application or SDK oracle is changed.

The direct containment correction at `39c04284` passes all 68 existing provenance
checks in pinned `pytest-exec-build-provenance-01`. Remaining build controls are
observing fixed `cecfdeef` in the separate verification worktree.

Final contract audit identified one ordinary candidate defect: the native bridge
retained timeout/cancellation receipts, but returned their status to domain code
without forcing a phase failure. A controlled command that emits the designated
assertion text and then times out could therefore be credited as a rejection.
Add that actual-family control first, retain its failing observation, then refuse
timeout/cancellation in the equipment bridge after recording operation identity.
This restores the planned native completion obligation; no accepted native oracle
or production behavior changes.

Source `a562390a`: pinned `pytest-exec-timeout-control-01` proves the defect.
The external control expected failure but the actual family returned success;
the retained command receipt has `timed_out=true`, nonzero return status and the
matching assertion in stderr. The bridge correction records the completed command
reference before raising an explicit timeout/cancellation phase error. Resource
settlement remains separate and the following independent case may proceed.

Source `3e93082f`: pinned `pytest-exec-acceptance-06` passes the timeout correction
and all existing integration controls. A final adjacent check applies the same
timeout to the shared baseline: command failure must use the ordinary assertion
failure channel already cached by the baseline helper, so eight dependent setup
errors do not repeat baseline execution. The added control requires precisely
two baseline commands, no dependent bodies and a retained failed prerequisite.
