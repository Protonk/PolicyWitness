# Controller authority evidence register

Baseline and historical-evidence disposition: `BASELINE.md`.
The historical CLI runs are accepted as recorded prerequisite completion;
their raw artifacts were pruned and have not been inspected for this task.
No historical run is described as fresh or retained evidence.

| ID | Kind | Source/configuration | Result and limit |
| --- | --- | --- | --- |
| E01 | Structural, fresh | `dcc7dd0b`; contract generator `--tree-check`, bytecode disabled | Pass; complete authored structure, no runtime claim. |
| E02 | Structural, fresh | `dcc7dd0b`; contract generator `--check --require-history`, bytecode disabled | Pass; current rendering/snapshot/stamps and required annotated history. |
| E03 | Identity/metadata, fresh read | `docs/build_contract.py`, selected app plist/provenance, generated wire and worker declarations | Development identity agrees with the accepted app metadata. Does not verify signatures, runtime identity or behavior. |
| H01 | Historical prerequisite | CLI plan evaluation through its handoff at `dcc7dd0b`, accepted by maintainer for this gate | Results/dispositions recorded in `BASELINE.md`; no raw evidence available. |

One combined evaluation was selected after inspecting its dispatcher plan:

```sh
env PYTHONDONTWRITEBYTECODE=1 PW_TEST_OUT_DIR=tests/out/runs/controller-authority-evaluation PW_TEST_QUIET=1 tests/run.sh --suite unit --suite integration --case witness_contract/example_round_trip --case witness_contract/example_round_trip_controls --case blackbox_e2e/checker_controls
```

It runs outside the automation sandbox under the checkout lock. Its eight
cases exercise the current controller unit batch and formatting, named
disposition/selection controls, signed CLI behavior, live example passage and
both checker-control owners. Production/test inputs remain at `dcc7dd0b`;
HEAD at launch was `9b579bf7` (entry records only). Run
`20261113T152200Z_6453a261` passed all eight selected cases, with no skip, unrun
case or harness error, zero recorded system sleep in each case, and a valid,
unchanged selected app inventory. The live case passed all 67 assertions with
no unevaluated assertion or consumer error. Its native observation is one
development-build execution on this machine under the case's observed
prerequisites. This is one fresh evaluation, not a new ten-run sample or
release rehearsal. Raw files remain local/disposable under the named output
directory pending the investigators' review.

The example control receipt has 192 controls, all matched with no problems,
67 covered assertions, none uncovered, and the two declared support items
resting on other evidence. The consumer receipt holds 134 result controls.
Those consumer controls compare exact result-diagnostic categories and require
specified companion diagnostics; this is not an assertion that every fault
case checks the complete diagnostic set. The CLI integration batch passed 19
tests. Unit logs retain the ordinary batches and separately selected ignored
regressions; case pass is not inferred merely from a Cargo exit code.

After completion, `git diff --exit-code dcc7dd0b -- controller/src
controller/integration runner tests docs/contract docs/porcelain.json
docs/architecture.json docs/generate_architecture.py` found no changes. This
checks the named inputs mechanically; selection-dependency completeness is a
reviewed scope judgment. Investigation reports and record edits do not affect
the executed controller/consumer/fixture paths.

No isolated workspace has been created by this investigation.
New execution credits will identify exact case, source/test/fixture/app,
command/configuration, expected and actual observations, raw path and limits.
Review and record any failed assertion before pruning its inactive output with
the repository tools. Final acceptance distinguishes source/check reading,
constructed checks and native observations.

## Integration verification

At source `424f3c73`, consolidated run `20261113T155111Z_8ba29955` under
`tests/out/runs/controller-authority-verification` passed all ten source-drift
cases and `blackbox_e2e/checker_controls`: 11 pass, no skip/unrun/harness error,
zero system sleep, selected app valid before and unchanged after. The app is
still the clean accepted `a5de0c63` build; shipped source and all identities are
unchanged. VERIFICATION records exact command, dependency applicability,
structural public deltas and the final reviewed prose-only exception.

The new 134-row result receipt matches complete independently expected
diagnostic multisets, retaining 189 actual errors with no missing/unexpected
ones. Five separate actual-control-route sensitivity records prove acceptance,
extra/missing/duplicate rejection and restoration for the comparator. Five
new controller known-gap controls produce their exact intended findings or
pass after restoration. These are constructed/structural observations, not
new native contradiction or failure evidence. All credited negative controls
reach the named predicate; no unrelated failure is counted.

The investigation used two dispatcher runs total: one baseline evaluation and
one verification of changed documentation/tests. No new worktree, build,
release rehearsal or ten-run sample was created. Retention disposition will
be appended after final raw receipt review and ordinary repository pruning.

## Final retention disposition

A/B/C completed raw receipt review and accepted the result before cleanup.
`make prune` first reported a signature-facts mismatch inside the automation
sandbox. The identical preview passed outside it without artifact changes,
establishing the environmental scope of that diagnostic. The clean preview
selected only this investigation's two inactive disposable runs.

`make prune APPLY=1` then completed with no blockers, failures, missing
acceptance or unmanaged output. It removed both controller-authority run
directories, preserved the protected newest release acceptance and kept the
four release archives v0.3.4 through v0.3.7. The raw development artifacts cited
above are now **pruned and unavailable**, not retained evidence. The committed
reviews and provenance/count/limit summaries are the surviving account; no
private evidence copy or keep marker was created. Only the original worktree
remains. No machine-resource recovery obligation was created by this plan.
