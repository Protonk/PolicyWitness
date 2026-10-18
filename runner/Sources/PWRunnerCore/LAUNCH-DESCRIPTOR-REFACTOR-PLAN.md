# Release the host evidence descriptor after worker launch

State: implemented, reviewed and accepted against the signed app. The
[acceptance record](../../../records/worker-launch-descriptor/implementation-acceptance.md)
retains the build, full default battery, focused controls and source snapshots.
Associated investigation: [launch descriptor lifetime](LAUNCH-DESCRIPTOR-LIFETIME-PLAN.md).
The [investigation record](../../../records/worker-launch-descriptor/investigation.md)
establishes writable inheritance through an independent same-object challenge,
the surviving host mapping, and the stale-owner/reused-number failure.

## Result and scope

Make the host evidence descriptor a worker-launch resource. After successful
`posix_spawn`, close it and relinquish its numeric ownership before policy
delivery or any later validator launch. Retain the evidence mapping through
collection, release, acknowledgement reconciliation, decoding and existing
teardown. A validator launched later must no longer inherit the host's writable
reference to that object.

Keep the current pre-spawn `FD_CLOEXEC` clear, worker file actions, optional
extension-channel delivery and transfer deadline start. This change does not
alter the worker's original-number descriptor aliases, ambient inheritance,
the known closed-stdin source/destination collision, exec cleanup policy,
query ordering, wire fields or ABI layout. Request, reply and envelope versions
remain unchanged. Close failures keep the existing best-effort semantics;
do not retry a close through a potentially reused descriptor number.

## Implementation

In [CWorker.swift](CWorker.swift), represent the host's close ownership
explicitly. Before mapping, preserve the current direct cleanup on `ftruncate`
and `mmap` refusal. After mapping, deferred cleanup always unmaps and closes the
descriptor only while ownership remains. Once spawn succeeds, relinquish that
ownership and issue one close immediately after the unchanged transfer deadline
construction, before parent pipe closure and policy delivery. Native spawn refusal and earlier setup
failures retain deferred ownership. No post-spawn code needs the descriptor;
all evidence access uses `base`/`rawBase`.

Prefer a local ownership variable and straight-line cleanup over a new resource
abstraction. Do not move policy delivery, clock sampling or the phase hook.
Do not add a JSON-selected test seam. Controls may instrument copied production
sources at native call boundaries and explicit observation points, as the
existing host-setup suite does.

## Discriminating controls

Promote the investigation equipment into maintained fixtures and a registered
`runner_unit/launch_descriptor_controls` case. Run it against the signed worker
and copied current production host/validator drivers. Preserve exact source
transformations, native observations, commands and child ownership receipts.

- For high descriptor numbers, evidence self-duplication at fd 3, and separate
  extension delivery at fd 5, independently observe worker entry descriptors
  and actual worker publications, release acknowledgement, clean exit and reap.
  Preserve the pre-spawn clear; a control omitting it must lose the self-dup
  endpoint. The fd 5 fixture is delivery evidence, not native token consumption.
- A validator observer preserves all incoming descriptors, writes a fresh
  challenge through each writable candidate into unused slot 255, and is reaped
  before host readback. Submit zero slots. An independently created identical
  decoy must receive its own challenge while the true mapping remains unchanged.
  Metadata or descriptor-number similarity alone cannot establish object identity.
  Restore the old host lifetime in a disposable source control and require the
  same oracle to detect writable true-object inheritance.
- Immediately after the candidate close, open an independent sentinel that
  reuses the exact released descriptor number. It must remain open after driver
  return. A close retaining the stale deferred owner must fail this assertion.
- Observe close counts, original descriptor availability and mapping teardown
  for native spawn refusal and controlled earlier `ftruncate`, both `mmap`
  refusal forms, first/second pipe, policy no-SIGPIPE and extension-duplication
  failures. Require no worker/validator when launch is not reached, exactly one
  close of the original owned descriptor and no surviving mapping. Preserve
  errors from the refused native boundary.
- Reject altered receipts lacking the positive decoy, confusing decoy and true
  mapping, lacking writable authority, losing exact reuse, closing the sentinel
  or losing worker delivery. These checker controls supplement native controls.

Retain existing host-setup collision/fault controls and live worker, extension,
phase, terminal-publication and ordering checks. The new fixture establishes
descriptor ownership and endpoint compatibility; it does not establish that a
shipped validator modified evidence or violated collection ordering.

## Documentation and acceptance

Update `runner/README.md`, the fixture/suite accounts and applicable
`docs/architecture.json` resource lifetimes and citations. Describe current
host descriptor ownership separately from retained mappings and worker aliases.
Regenerate with `python3 docs/generate_architecture.py` and
`python3 docs/generate_worker_identity.py`; inspect generated identity agreement
and confirm unchanged layout/version values. Permanent docs/tests must not link
back to investigation records.

Build through `make build IDENTITY='...'` with the configured Developer ID
identity. Coordinate one build/test execution window per checkout and use fresh
managed output. Inspect selections before running the signed candidate's full
default battery, which must include the new case, plus existing opt-in
`runner_unit/host_setup_oracle_sensitivity`. The default live exec inheritance
checks retain the unchanged worker/exec-child endpoint constraints. Select any additional required
opt-in arising from the implementation explicitly. The production wait,
release store and eligibility predicate remain unchanged, so no new ordering
mutation obligation is introduced.

Completion requires independent true-object exclusion with a working decoy,
exact-number reuse surviving teardown, correct cleanup on launch/setup refusal,
preserved worker endpoints and mapping/publication behavior, passing signed
acceptance and an implementation acceptance record. Retain original failures
and source/equipment provenance under the repository's test-evidence rules.
