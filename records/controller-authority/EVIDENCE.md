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

No dispatcher run or isolated workspace has been created by this investigation.
New execution credits will identify exact case, source/test/fixture/app,
command/configuration, expected and actual observations, raw path and limits.
Review and record any failed assertion before pruning its inactive output with
the repository tools. Final acceptance distinguishes source/check reading,
constructed checks and native observations.
