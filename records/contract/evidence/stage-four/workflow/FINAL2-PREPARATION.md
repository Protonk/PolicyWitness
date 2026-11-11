# Private guide workflow candidate

This successor adds the opt-in `witness_contract/guide_workflows` test, its
fixture/account changes and one adjacent guide-owner matrix in the existing
dispatcher retention control. It is prepared for the reviewed guide postimage at
`/private/tmp/pw-contract-stage-four-guide-candidate/after/docs/PolicyWitness.md`
(guide patch `7ae36beb794409d4ce30e0851663ad9e9a2bd309f7439f4ec10130cc49fda159`).
The guide revision and its generated regions must be integrated and regenerated,
and the resulting guide staged beside the selected signed app, before execution.
No guide/test/build command has been executed during preparation.

## What is proposed

The owning test interface remains `tests/run.sh --case witness_contract/guide_workflows`.
The catalog entry is non-default and requires app, identity and GUI equipment.
The case additionally requires an empty default installed/pending registry,
because the displayed `runner validate` refreshes every record. It refuses that
precondition before staging/installing a service; unrelated records are never
removed or validated by a successful case. A foreign registry entry arriving
later is an environmental race: `updated == 1` will fail after the displayed
validation. The empty-registry precondition is an equipment/serialization
assumption, not a global lock held across the workflow. The normal per-command
registry lock continues to serialize each public command.

The case extracts actual `sh` fences using `docs/markdown_reader.py`, with exact
section and unique-content selection. It records full guide bytes/hash, selected
fence contents and source line ranges. Only APP, IDENTITY and ENT are substituted:
APP is the selected app; IDENTITY is the matching Developer ID found by the
existing test helper; ENT is an actual plist written from that app's selected
worker entitlement readback. The displayed default registry and user-scope
launchd locations remain in use. The selected app inventory is compared before
and after; the copied source is independently compared before metadata/signing.

Explicit source-preserving cuts allow the test to save durable ownership before
copy/sign/install, arm submission records before each run/verify, capture actual
exit files and make independent file/process observations. These are a fixed
workflow recipe, not a shell parser. The concatenated cuts preserve each fence.
Each retained shell script includes the fragment plus bookkeeping which saves
only the named guide variables and umask. No global `set -e` changes expected
refusal behavior. Simple commands have their shell status in command.json;
compound run/refusal/helper/install/verify/remove blocks additionally retain the
actual PW_EXIT files displayed by the guide. Missing/ambiguous sections, fences,
substitution anchors or cut markers refuse rather than selecting another block.

## Executed work when adopted

1. Read version/contract from the selected app, create the guide request, observe
   an absent target, run it, and independently observe a regular empty 0600 file.
   Revisit the existing-target guard and require the target and saved result's
   bytes/mtime to remain unchanged.
2. Execute the misspelled capture-flag refusal and corrected missing-nonce
   refusal, checking exact code/path, host boundary, no worker/validator record
   and target absence. Generate the displayed nonce and execute the corrected
   request; require a positive capture bound to nonce, worker PID, source and
   retained bytecode hash/length. This chosen healthy workflow needs `captured`;
   an unavailable receipt remains visible as a failed positive observation.
3. Execute the actual `sbpl-check --request` fence; retain compile stage/ok/error
   and source hash, with independent unchanged file observations on both targets.
   These observations identify the inspected files and their read times.
4. Execute actual list/reconcile, copy/name/sign/install, status/verify,
   service-selected create, validate/remove/list/reconcile fences. Save all
   streams/status/request/version records; independently read the installed
   plist, service state, equipment and entitlements. Require own record removal
   from both registry collections plus launchd and plist absence.

The existing constructed reader corpus supplies result-interpretation examples.
This case's positive native commands do not stand in for combined-fault readers,
foreign signer calibration, arbitrary unavailable capture branches, historical
compatibility, or the full release acceptance sequence. The report can state
which concrete workflows ran once this candidate has actually executed.

## Ownership and interruption

`artifacts/session.json` is the case's top-level work owner, so existing retention
refuses pruning until it is removed and free of cleanup_error. Its durable twin
is `PW_WORK/session.json`, written before the first app invocation. The workspace
must be a fresh `/private/tmp/pw-guide.*` directory, with exact device/inode.

The narrow `session.adopt_guide` helper owns the guide's already-created empty
`PW_WORK/runner.*/PWRunner.guide.xpc` stage before copying/signing. It records the
workspace and stage identities, exact `com.policywitness.guide.<uid>.<stage>`
service, user launchd target, bundle and plist. It adds no prefix-only deletion
rule and keeps the ordinary session removal path. The receipt is
`artifacts/byoxpc-session.json`; its durable twin is in the stage. The ordinary
BYOXPC layout retains its prior branch and cleanup behavior.

Before deleting work, cleanup validates each `run` envelope with the independent
consumer and checks its worker reap, or the specific host admission refusal
with no subprocess/steps or validator. For `runner_verify`, it checks the outer
kind/contract and validates the inner host reply before using its reap; the
workflow's success assertions separately join the verify result and selected
runner ID/service/bundle to the installed record. A missing/partial/malformed report, missing worker witness, or harness
interruption retains the work directory and external-runner ownership. A timeout
of the shell capture may leave a child CLI; the candidate records this as
`command_uncertain` and deliberately refuses automatic resource cleanup. It does
not replay any submitted request or infer a stopped worker from a historical PID.
The explicit recovery record keeps exact paths and prior observations for
inspection. The existing session helper verifies registry/plist/executable
ownership before removal and independently checks all three absence claims.

Ordinary success copies the work files into artifacts, removes the owned external
stage through the helper, compares the app inventory, records cleanup_verified,
and removes the identified work directory. The wrapper repeats cleanup
idempotently. A failed cleanup remains a failed case and retained ownership even
if the preceding native assertions completed.

## Review and verification still needed

Only Python AST parsing and independent Markdown/source inspection have occurred.
No native commands, constructed controls, shell workflows, tests, generator or
build has run. Root/independent review must settle this candidate, particularly
its empty-default-registry equipment assumption and the explicit layout adoption.
Then run source-drift/dispatcher checks for catalog/accounts and helper ownership,
the existing affected BYOXPC cleanup controls, and this opt-in via tests/run.sh on
the freshly staged signed candidate. A fresh isolated guide reader remains useful
for usability and interpretation; command success alone cannot establish those.

The candidate retains raw evidence on failures and publishes no executed support
grade merely from these proposed assertions. The broader stage-two P9 native
receipts and the new guide execution will retain separate run identities.


## Successor ownership corrections

The original frozen patch is retained at
`/private/tmp/pw-contract-stage-four-guide-workflow/guide-workflows.patch`
(SHA256 `7f44e80dc1c38d427c8d079addf33372b7e0e70bf2320e8c1f854dc39b23a55e`).
This successor addresses the six groups in the independent review
`/private/tmp/pw-contract-stage-four-guide-workflow-review/REVIEW.md`.

- Regular nonsymlink owner files and immutable path/device/inode/source/contract
  agreement are checked before trusting newer durable progress. The inner guide
  owner binds registry_path to None and compares its own receipt/durable core.
- `adopt_guide` arms the exact nested ownership core in the outer durable record
  before child persistence and before copying/signing/installing. Outer cleanup
  refuses another valid workflow's child owner. A missing auxiliary receipt can
  recover only from the exact armed durable path; an interrupted pre-copy
  adoption can retire only its exact still-empty stage.
- After machine resources and source inventory are verified, deletion keeps the
  durable work owner last. Recovery at this checkpoint uses the retained proof
  instead of re-reading output files already deleted. A missing durable file
  permits only the exact verified empty directory remainder to be removed.
- Existing top-level ownership refuses another run before any commands. Positive
  path controls use deterministic accepted naming. Verify/run results are joined
  to the actual saved installed record and service.

The new ownership controls are source candidates only. They use the existing
BYOXPC fake OS command tool, with an explicit private file modeling the default
registry and separate service/plist/record survival faults. They exercise actual
owner persistence, path inspection, file writes and deletion. One simulated
submission writes an independent effect then raises a capture interruption;
cleanup must retain ownership and never submit/remove again. Cleanup-disposition
controls inject consumer admission and exercise the actual reap/host-refusal
predicate; complete consumer behavior remains covered by its existing controls
and by the native guide workflow. The existing `shell_helpers/byoxpc_setup`
controls retain ordinary private-registry positives and the broader old-layout
fault matrix. The new dispatcher check uses its managed disposable runs and
normal prune command, preserving pending/error guide receipts and deleting the
clean neighbor.

Only AST parsing and static review have occurred. All consequence controls,
including fake commands, remain unexecuted. Needed later selections include
`shell_helpers/byoxpc_setup`, `dispatcher/retention_controls`, applicable source
drift, and the new opt-in after staging the reviewed guide with the signed app.


## V3 narrow recovery follow-up

V2 remains frozen at its original path/hash. This successor clears a stale
cleanup_error after verified work absence in both the removed:true and the
not-yet-marked-removed recovery branches. A controlled final receipt-write
failure after successful rmdir must remain recoverable, and a constructed
post-deletion checkpoint covers the adjacent absent-work branch. The prior
ignored journal_note control is replaced by observable durable-ahead progress:
newer uncertainty retains the effect/stage despite an older clear artifact,
then newer cleared uncertainty permits removal despite the older uncertain
artifact. These controls remain unexecuted source candidates.

The new external adoption boundary also uses lexists: a dangling auxiliary
receipt is existing ownership and refuses before parent arming. Its control
keeps the foreign target absent and the parent durable bytes unchanged.


## Final catalog and account follow-up

The native case is included in the catalog's complete `opt_in.include` selection.
The suite account explicitly requires no concurrent registry changes and states
that another installed record at validation fails the expected updated count,
after validation may have refreshed that record. Pending records and changes
after validation remain part of the stated equipment/concurrency assumption;
the existing assertions establish no cross-command registry lock. This follow-up
changes only catalog membership and the suite account.
