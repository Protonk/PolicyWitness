# Investigate launch descriptor ownership

[Parent and handoff scope](../../../WORKER-REDESIGN-PLAN.md).
Finding: WA-01 in the [initial audit](../../../records/worker-pass6/initial-report.md).
State: investigation complete and reviewed; the user selected close-after-spawn
with explicit ownership invalidation and retained mapping. Implementation
planning is pending; no production change is implemented.

The [investigation report](../../../records/worker-launch-descriptor/investigation.md)
records the source trace, fourteen native prototype scenarios, six rejected
checker controls, exact equipment and failed-attempt accounting at `503156f`.
It recommends closing the host descriptor after successful worker spawn with
explicit ownership invalidation, retaining the mapping and current pre-spawn
file actions. The baseline's writable same-object inheritance was established
by independent challenge/readback against a separate identical decoy.

## Starting point

In [CWorker.swift](CWorker.swift), `runCWorker` creates and maps the evidence
object, clears the descriptor's close-on-exec flag, delivers it to the worker
and defers its close until driver return. During that lifetime,
[CWorkerOrchestrator.swift](CWorkerOrchestrator.swift) invokes the validator.
[ValidatorClient.swift](ValidatorClient.swift) uses nil spawn attributes and
file actions for standard input/output. The audit identifies a source-supported
route for the validator to inherit the writable evidence object; direct
observation of that reference is outstanding.

The first candidate is to make the host descriptor a launch resource: close it
after successful worker spawn while retaining the host mapping. Compare that
with restoring close-on-exec after spawn and with explicit child descriptor
allowlists. Existing low-descriptor collision findings are constraints on these
alternatives, not evidence that any one alternative is already safe.

## Questions that distinguish the designs

- Does any host path need this descriptor after spawn, independently of the
  mapping? Where should close-once ownership end on success and each failure?
  Account for descriptor reuse and the existing deferred cleanup.
- What actually reaches a validator? An observer selected through
  `validator_executable_path` must preserve incoming descriptors. Identify the
  same evidence object and its access mode; size or descriptor number alone
  cannot establish identity. Include an observation that would reject a
  similarly shaped unrelated object.
- Which alternative also changes the worker's original-number aliases or
  ambient inheritance? Consider low descriptors, self-duplication and extension
  delivery separately. Distinguish inherited write authority from a demonstrated
  violation of collection/release ordering.

The [host setup controls](../../../tests/suites/runner_unit/host_setup_controls.py)
and [inheritance suite](../../../tests/suites/runner_exec_inheritance/README.md)
are starting points. Register rows 19, 23 and 26 in the worker documentation
plan describe distinct oracle and endpoint problems; a broad passing case does
not settle those boundaries.

## Outcome to bring back

Recommend the smallest ownership model that removes the unwanted reference,
or explain why the descriptor must remain. Give supporting observations, the
effects on each child launch, and the controls needed to distinguish a repair
from accidental absence of the reference. Identify any broader inheritance
change as a separate choice.
