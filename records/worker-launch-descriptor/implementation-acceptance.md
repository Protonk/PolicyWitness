# Launch descriptor implementation acceptance

Status: implemented, reviewed and accepted against the signed app. Associated
[implementation plan](../../runner/Sources/PWRunnerCore/LAUNCH-DESCRIPTOR-REFACTOR-PLAN.md).

## Implemented ownership

The host's evidence descriptor now lasts through worker spawn. On success,
the existing policy-transfer deadline is constructed at the same point, then
the host relinquishes close ownership and closes the descriptor before policy
delivery or later validator launch. Its mapping remains through collection,
release, final acknowledgement reconciliation, decoding and existing teardown.
Pre-spawn refusals preserve their original close/unmap cleanup. Deferred cleanup
cannot close a different owner that reuses the released number.

The coordinator reviewed the production ownership change, copied-source
instrumentation, independent object/reuse/unmap observations, deliberate defects
and documentation. The pre-spawn close-on-exec clear, child file actions,
worker original-number aliases and separate extension endpoint remain unchanged.
No ordering predicate, wire field, ABI geometry or cleanup policy changed.
Request/response/envelope versions remain 5/23/7.

## Signed candidate and source

The base is `924a6ed048a805d8f5633e3b720fbed64ad00ccc`.
[implementation-source.json](implementation-source.json) identifies changed
source/test/doc contents for the signed build. Unchanged files come from that
base. [acceptance-source.json](acceptance-source.json) records the same contents
and file modes for default acceptance. The new shell wrapper's executable bit
was corrected before testing; no app input changed after the build. Later plan
statuses, acceptance records and retention entries are bookkeeping.

```sh
make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'
```

The [build log](implementation-build.log) preserves output with trailing
whitespace trimmed. The signed app, ZIP and standalone guide were produced;
eight executables and two seals passed Developer ID, hardened-runtime and secure
timestamp checks. Worker identity is
`c61a48d78974584cbf9e5b0113c6c24a17e3ef9b968f841821f2a0794216648f`.
This is development acceptance, not notarization/release acceptance.

## Verification

Commands ran from the repository root outside the automation sandbox through
the checkout-locked dispatcher, with fresh managed output:

```sh
PW_TEST_OUT_DIR=tests/out/runs/descriptor-controls-20261018 tests/run.sh \
  --case runner_unit/launch_descriptor_controls \
  --case runner_unit/host_setup_controls \
  --case runner_unit/host_setup_oracle_sensitivity
PW_TEST_OUT_DIR=tests/out/runs/descriptor-default-20261018 tests/run.sh
```

The [targeted run](../../tests/out/runs/descriptor-controls-20261018/run.json),
`20261018T210338Z_5fe2c7c7`, passed all three cases with no skips, unrun cases or
harness errors. Its inspected app was valid and unchanged. An earlier planning
refusal identified the new wrapper's missing executable bit; it created no
owned run and is retained separately in the targeted run's supplement.

The [full default run](../../tests/out/runs/descriptor-default-20261018/run.json),
`20261018T210511Z_0355e284`, passed all 193 cases with no skips, unrun cases
or harness errors. This includes all 461 Swift tests, the new descriptor case,
compiled C/Swift layout agreement and live worker, validator, phase, extension
and exec-inheritance cases. Its inspected app was valid and unchanged. The
18 changed source/test/doc contents and executable modes still match the
acceptance snapshot. Final generated-copy, link and whitespace checks passed.

[implementation-runs.json](implementation-runs.json) retains run identities,
configuration and canonical case outcomes; each full run record also retains
exact case commands, equipment and artifact inventories. Raw test evidence is
gitignored and available locally; both runs are pinned in the retention index.
No older-source test results are needed for acceptance.

## What the controls establish

The [descriptor receipts](../../tests/out/runs/descriptor-controls-20261018/suites/runner_unit/launch_descriptor_controls/artifacts/controls/results.json)
cover 19 native scenarios: three candidate endpoint arrangements, eleven
setup/native-spawn refusals, and five deliberate source defects. Seven altered
receipts separately test the assertions. The copied current host/validator
drivers use the unchanged signed worker; the validator observer makes no sandbox
query. This is ownership/control evidence, not a claim that the shipped validator
modified evidence or violated ordering.

At original descriptor numbers 16, 3 and 17, the candidate's validator could
write the independent decoy but could not write the true host evidence mapping.
Restoring the old lifetime exposed the true object in all three arrangements.
Independent cross-mapping challenges establish identity; matching descriptor
numbers, stat fields, size or header bytes alone are insufficient.

The candidate's exact-number reuse sentinel survived driver return; keeping a
stale deferred owner closed it and failed the fixed assertion. Worker reporting,
release/acknowledgement, clean exit and independent reap confirmation remained
intact. The removed-clear control independently observed fd 3 absent at worker
entry, exit 3 and no application/done, with confirmed reap, before requiring the
candidate assertion to reject it. A generic worker failure cannot satisfy it.
Separate fd 5 delivery establishes the endpoint, not native token consumption.

The eleven refusal scenarios preserve one close, no invented child and full
mapping teardown where mapping had succeeded. A native observer remembers the
acquisition extent independently of the requested unmap length and scans that
complete rounded range before and immediately after unmap. The positive mapping
and subsequent absence are required; native rc or requested length alone cannot
prove cleanup. Refusal calls use substituted EIO except the real missing-target
spawn refusal. Existing host setup and sensitivity cases retain their own
characterization limits, including known endpoint/collision blind spots.

All new scenario command-group inventories were empty after exit, and successful
worker paths independently confirmed the host's reap. Source copies, exact
transformations, call/run commands, child ownership and observations are retained.

## Scope retained

Close remains best effort with no retry through a stale number; close-error
injection is not claimed. Existing unchecked setup operations, low-descriptor
collisions, worker aliases and exec-child inheritance policy are separate.
The retained mapping preserves reporting; no broader inheritance allowlist,
supervisor, descendant-containment claim or new request control was added.
