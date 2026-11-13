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
