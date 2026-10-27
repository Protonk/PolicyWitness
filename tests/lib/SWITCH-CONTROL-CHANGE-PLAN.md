# Enforce toolchain-switch verification after relevant changes

## Objective and boundary

The [verification rule](../CHANGE-VERIFICATION.md#build-toolchain-switch-controls)
requires `preflight/build_toolchain_switch_controls` after changes to the
toolchain stamp's fields or comparison. Add conservative change detection,
development diagnostics and a release-acceptance gate requiring applicable
passing execution evidence. The control remains explicitly selected through
`tests/run.sh`; no ordinary build or default battery starts its two fresh
builds automatically. Commit/merge enforcement and a general framework for all
verification rules are outside this plan.

## Grounding

[build_provenance.py](build_provenance.py) owns `compatibility_fields`,
`compare_fields`, stamp admission/publication and their helpers;
[build.sh](../../build.sh) invokes them. The
[switch control](../suites/preflight/opt_in/build_toolchain_switch.py) observes
real reuse, refusal and fresh recovery under distinct toolchains. Its
`Checkout` helper in [build_refusals.py](../suites/preflight/opt_in/build_refusals.py)
copies working files, so a Git commit alone does not identify the tested bytes.
[test_cli.py](test_cli.py) selects cases and [suite_run.py](suite_run.py) records
their completion, but neither currently derives obligations from source changes.
[release_accept.py](release_accept.py) requires the default battery, while
[release_runs.py](release_runs.py) packages and verifies its portable evidence.

## Approach

1. Define one reviewed input manifest for this rule, using repository-relative
   paths and whole-file hashes. Trace the stamp's owners, callers and helpers,
   starting with `build_provenance.py`, `build.sh`, `output_target.py`,
   `cargo_config.py` and the Meson inputs; include the control, its fixture and
   harness dependencies for evidence reuse. Review that inventory before wiring
   the gate. Missing, moved or unreadable inputs and manifest changes invalidate
   a credit. Accept conservative extra runs rather than claim semantic change
   detection. Hash equality establishes identity, not completeness of this
   dependency review; uncertain applicability requires a rerun under
   [the evidence rules](../AGENTS.md#evaluate-and-reuse-evidence).
2. Capture the actual disposable checkout and verification inputs when the
   canonical case runs. Retain their hashes, source revision/working-tree state,
   configuration, equipment observations and raw build receipts with the
   dispatcher result. Detect changes during capture/execution. Credit requires
   completed passing case accounting without harness errors or sleep overlap,
   plus the control's observed differing fields, refusal and recovery evidence.
   A refreshed fingerprint or an `ok` flag alone cannot create a credit.
3. Compare current inputs with an explicitly supplied retained run and report
   missing or stale evidence during development selection/listing, without
   changing case membership or executing anything during `--list`. With no
   qualifying evidence, including initial adoption, report the required case
   and its equipment. Preserve the existing distinct-toolchain, signing and
   failure conditions; do not infer a credit from an older unbound run.
4. Apply the same validation in release acceptance before recording success.
   Match the evidence to the release candidate's established source inputs,
   not merely the checkout invoking acceptance; an unestablished match refuses.
   Keep the default battery unchanged. Copy the validated supporting evidence
   into the owned acceptance directory so portable archive verification remains
   possible after original local output is pruned. Extend acceptance/archive
   readers and controls together, preserving retention and interrupted cleanup.
   Assess record-version changes explicitly; this adds no promise to migrate
   historical evidence. Preserve original runs and use existing ownership tools.

Update the harness and preflight accounts, verification guide and
[release procedure](../../docs/SIGNING.md#release-procedure) with the implemented
inputs, evidence selection and refusal behavior. The watched inventory and
evidence format are reviewed implementation outputs, not self-certifying proofs.

## Verification and completion

Use dispatcher-reached controls for matching evidence, changed implementation
or checker inputs, removed inputs, missing/malformed/stale evidence, failed or
unrun cases, interrupted runs, mutation during execution, and a receipt whose
claimed hashes disagree with its retained inputs. Include unrelated edits that
leave the reviewed inputs unchanged, and combined faults that must remain
visible. Exercise the real acceptance path: a passing default battery cannot
override missing switch evidence, and an archive must still verify with original
run paths unavailable. Preserve cleanup/recovery controls.

Run the affected `dispatcher`, `preflight/release_controls`,
`preflight/release_publish_controls`, `preflight/release_rotation_controls` and
source-drift cases through `tests/run.sh`. Finally obtain one real matching
`preflight/build_toolchain_switch_controls` run with the required equipment and
verify its admission and invalidation by the gate. Constructed receipts establish
reader behavior, not execution of the switch. Completion requires both, with the
reviewed dependency scope and any verification limits recorded.
