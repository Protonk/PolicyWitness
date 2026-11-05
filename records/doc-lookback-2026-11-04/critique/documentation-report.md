# Documentation emission audit

Baseline: `f25c18ed`. This report records source review and authored edits only.
No probes, tests, generators or builds were executed by this worker. The root
agent owns regeneration, guide staging, verification and acceptance evidence.

## Admission rows

The review covers all 30 admission rows. Indexed patterns substitute zero-based
decimal array positions. Field strings and request-failure path arrays are
separate contracts; declaration consume/release repetition produces a meaning
failure, not an admission_failure field. Alternative numeric capacity failures
can still precede meaning validation.

| Row | Disposition | Emission source |
| --- | --- | --- |
| `policy_source` | Add indexed actor policy source. | [workerAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorker.swift#L814); [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272) |
| `probe_steps` | Retain both literal aggregate names. | [admissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L13); [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272) |
| `policy_parameters` | Add indexed actor policy parameter count. | [admissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L13); [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272); [workerAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorker.swift#L814) |
| `step_id` | Add indexed extension-action identity; ordinary probe identity retains separate step_index. | [workerAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorker.swift#L814); [requestAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L224) |
| `attempt_target` | Retain literal target and separate step location. | [workerAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorker.swift#L814) |
| `exec_arguments` | Retain args/items and separate step location. | [workerAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorker.swift#L814) |
| `exec_argument` | Retain args/utf8_bytes and separate argument/step locations. | [workerAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorker.swift#L814) |
| `parameter_key` | Retain key; refused key is withheld in both forms. | [workerAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorker.swift#L814); [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272) |
| `parameter_value` | Add indexed actor policy value; parameter_key remains separate. | [workerAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorker.swift#L814); [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272) |
| `query_operation` | Retain literal query field and separate probe location. | [queryAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L183) |
| `query_filter_value` | Retain literal query field and separate probe location. | [queryAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L183) |
| `probe_plan_label` | Retain all three literal alternatives. | [queryAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L183) |
| `specimen_id` | Retain literal specimen_id. | [requestAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L224) |
| `request_label` | Replace actor shorthand and add extension operation/family/authority labels. | [requestAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L224) |
| `test_override_path` | Restore full _test_overrides prefix to every alternative. | [requestAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L224) |
| `phase_count` | Retain literal phases. | [admissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L13) |
| `phase_id` | Retain literal phase_id and identify separate index. | [admissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L13); [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272) |
| `extension_declarations` | Retain literal extensions. | [requestAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L224) |
| `extension_consumes` | Replace nonexistent numeric field with explicitly labeled meaning code and exact path array pattern. | [extensionMeaningFailure](../../../runner/Sources/PWRunnerCore/ProbeRunner.swift#L181) |
| `extension_releases` | Replace nonexistent numeric field with explicitly labeled meaning code and exact path array pattern. | [extensionMeaningFailure](../../../runner/Sources/PWRunnerCore/ProbeRunner.swift#L181) |
| `extension_reference` | Replace schematic names with exact indexed alternatives; include delivery and recipient operands sharing this cap. | [requestAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L224) |
| `extension_target` | Add declaration index. | [requestAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L224) |
| `actors` | Retain literal actors. | [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272) |
| `actor_phases` | Retain literal phases. | [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272) |
| `actor_issues` | Use literal extension.issue. | [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272) |
| `actor_deliveries` | Use literal extension.transfer. | [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272) |
| `actor_handles` | Use literal extension.consume. | [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272) |
| `actor_releases` | Use literal extension.release. | [actorAdmissionFailure](../../../runner/Sources/PWRunnerCore/ActorPlan.swift#L272) |
| `actor_id` | Use indexed actor declaration and phase reference. | [requestAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L224) |
| `extension_issue_target` | Use exact indexed phase/action target pattern. | [requestAdmissionFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L224) |

[requestCapacityFailure](../../../runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift#L292)
constructs the separate path: aggregate phases.actions becomes phases; probe
locations acquire their request prefix; phase_id uses its separate index;
parameter values replace value with params and the retained key; key failures
withhold the path. These transformations must not be advertised as field text.

## Authored changes

- Refusal-field strings were edited in the limits manifest; the root agent also authorized the adjacent row-scope corrections listed below.
- LIMITS defines exact placeholder expansion and separate location fields outside
  the generated tables; the generator must copy this shared explanation to the guide.
- The generator-contract account distinguishes field alternatives from the two
  meaning-only code/path rows and states that source correspondence is reviewed,
  not verified by the generator's nonempty-text check.
- The guide's parallel-running paragraph includes the client, form-dependent
  workers, per-eligible-phase validators, declaration issuer, exec children and
  terminal-XPC-error fallback compiler helpers without a fixed concurrency count.

Process review anchors: [controller launch inventory](../../../controller/README.md#what-a-run-reads-and-launches),
[runner lifecycle](../../../runner/README.md),
[actor scheduler](../../../runner/Sources/PWRunnerCore/ActorScheduler.swift),
[extension issuer](../../../runner/Sources/PWRunnerCore/ExtensionIssuer.swift), and
[fallback compiler selection](../../../controller/src/run_flow.rs#L401).
The issuer precedes declaration worker creation; actor workers persist across
phases; validators are created for eligible phases rather than once per run.

## Authorized adjacent row-scope corrections

No unmappable emission remains. After review, the root agent extended ownership
to the following adjacent descriptions; numeric values and check citations are
unchanged by this worker:

- step_id counting now distinguishes the separate ordinary step_index from the
  extension action's indexed field. This follows workerAdmissionFailure versus
  requestAdmissionFailure.
- request_label counting includes extension operation, family and authority,
  matching requestAdmissionFailure's requestLabelMaxBytes branch.
- extension_reference is titled “Extension references and recipients” and counts
  token, handle and delivery references plus transfer recipient identifiers,
  matching the _ref/recipient branch's referenceBytes cap.
- actor_id counting is restricted to actor declaration identifiers and phase
  actor references. Transfer recipients point to extension_reference, whose
  refusal alternatives include their actual indexed field.

Generated tables and the shared guide copy intentionally await the root agent's
owning generator. This source review is not execution evidence.
