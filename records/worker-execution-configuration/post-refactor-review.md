# Execution configuration: remaining decisions

Status: source review complete. Review source: `f6997588555f32d1b648abd082a0ae86e18b9976`,
after the descriptor-lifetime and bounded-sysctl-disclosure implementations.
The descriptor change was accepted at
`0262dfea37cc7a04e65af5e0b10fe3f7ffac1b6f`. Their associated implementation plans
carry their signed acceptance; this configuration review ran no independent
experiment, build or test. The earlier source inventory remains a historical
record linked from the associated configuration plan. This review does not
revise that inventory or authorize further application changes. The
[reviewed source hashes](reviewed-sources.json) match both the committed files
and the final working tree.

Associated plan:
[execution configuration](../../runner/Sources/PWRunnerCore/EXECUTION-CONFIGURATION-PLAN.md).

## Recommendation

Keep the existing request and shared production path. Clarify the account of
supplied controls, retain the request with each experiment, and repair the
default-validator selection discrepancy as a separate small change. A generic
ordinary/instrumented mode, new request form or production build variant would
not establish whether a requested boundary was reached or an effect occurred.

One consequential choice merits user review now: **retire the validator's
implicit app-level fallback, or preserve it and account for the host's resolved
selection?** Retiring it is the smaller recommendation. The supported build and
external-runner installation already require the bundle-local helper. Dynamic
allowance and intervention records can remain deferred unless a consumer needs
the missing facts; they are not prerequisites for qualified retained evidence.

## What the completed refactors settle

The accepted exec evidence in
[PWRunnerAPI.swift](../../runner/Sources/PWRunnerCore/PWRunnerAPI.swift),
`PWExecObservation`, distinguishes collection before cleanup, actual signal
requests and final leader wait. The record is gated by slot completion;
absence remains unknown. It observes real driver cleanup calls, not the
execution of `_test_overrides` sleeps or self-signals. It does not supply
dynamic validator allowances, authenticate helper bytes or select stronger
descendant cleanup. Those distinctions need no new common mode flag.

The descriptor implementation in
[CWorker.swift](../../runner/Sources/PWRunnerCore/CWorker.swift), `runCWorker`,
relinquishes close ownership and closes the host evidence descriptor after
successful worker spawn and the unchanged policy-transfer deadline creation.
It retains the mapping and preserves pre-spawn refusal cleanup. The dedicated
[implementation plan](../../runner/Sources/PWRunnerCore/LAUNCH-DESCRIPTOR-REFACTOR-PLAN.md)
carries acceptance of object exclusion, descriptor reuse and worker delivery;
those observations are not new configuration experiments. Declaring a
configuration could not establish that inheritance boundary.

The sysctl implementation in
[attempt_sysctl_read](../../controller/tools/pw_probe_runner/pw_probe_runner.c)
names the existing array bound as `PW_SYSCTL_READ_BYTES`, keeps `len = sizeof(buf)`
and the one non-null read unchanged, and discloses 4096 bytes in the
[limits manifest](../../docs/limits.json). It adds no sizing call, retry or raw
length evidence. Its dedicated
[implementation plan](../../controller/tools/pw_probe_runner/SYSCTL-DISCLOSURE-REFACTOR-PLAN.md)
carries the compiled call-boundary and signed compatibility acceptance.
Neither refactor adds a request control or requires an execution-configuration
schema. Source comparison with `924a6ed` found no change in validator resolution,
control admission/echo, dynamic allowance accounting or the dossier. The
configuration recommendations below therefore survive both implementations.

## The concrete selection discrepancy

[PWRunnerService.runSpecimen](../../runner/Sources/PWRunnerCore/PWRunnerService.swift)
uses an explicit validator override if present, otherwise
[defaultValidatorExecutablePath](../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift).
The latter checks whether the bundle-local file is executable; if it is not,
it computes an app-level path. This resolution happens before the phase reaches
validator launch.

[Binaries::observe](../../controller/src/dossier.rs) independently records the
selected bundle-local validator or explicit override before invocation. It
does not implement the host fallback. A failed validator spawn records the
actual attempted path; a successful
[ValidatorOutput](../../runner/Sources/PWRunnerCore/ValidatorClient.swift) and
its public subprocess record have no resolved executable path. Therefore the
fallback can select a path different from the dossier's selection account.
This is a source branch, not evidence that an intact current bundle takes it.

The surrounding contract favors a single default:

- [build.sh](../../build.sh) embeds the validator only inside each XPC service.
  The resolver's comment claiming both bundle-local and top-level copies is
  stale.
- [app_layout.rs](../../controller/src/app_layout.rs), `SHIPPED_VALIDATOR`,
  names the bundle-local role and says production traffic never uses the
  app-level copy.
- [sign_install_tree](../../controller/src/runner_manager.rs) refuses external
  installation without the bundle-local validator. An installed runner must
  carry the complete copy; a general fallback outside its bundle is not a
  substitute for that contract.

Recommended choice: resolve the default directly to the bundle-local path,
preserve explicit overrides, and let a reached native spawn report absence or
non-executability at that path. Earlier failures and phases without eligible
queries still must not manufacture a failed launch. This changes the behavior
of manually arranged older layouts, so it deserves a compatibility decision
rather than being hidden in a comment correction.

If fallback compatibility is required, a second independent controller
executability check would not guarantee agreement across observers or times.
The alternative needs an honest host-resolved selection account (distinct from
launch, byte identity and authentication), including unreached paths and early
failures. That is larger evidence work with coordinated producer, readers,
refusal bounds and contract review. Do not rename pre-invocation hashes into
proof of what executed.

## Requested, resolved and observed

| Example | Existing facts | Remaining limit |
| --- | --- | --- |
| Ordinary retained request | No submitted overrides in the retained request; selected runner/provenance and reached process/phase evidence | A null reply echo alone cannot prove no controls were submitted. |
| `worker_timeout_ms: 1` | Echo records 1; source floors it; a reached `sentinel_wait.budget_ms: 50` records the configured allowance | Deadline exhaustion needs its own stop observation; the value neither changes the C exec budget nor bounds final cleanup. |
| Empty/default/inert override | Supplied values remain visible when echoed; source can resolve them to the ordinary behavior | Presence cannot classify an effective intervention. |
| Validator override with no eligible queries | Selected bytes and echo can exist; phase collection says no launch was needed | No validator invocation or failure follows from selection alone. |
| Post-phase signal 9 followed by reaped signal 9 | Request, observed phase progress, absent/present `done` and native fatal disposition remain separate | The matching number does not identify the sender or prove the requested self-signal call. |

Retaining the submitted specimen, invocation, source/app identity and exact
envelope is sufficient to describe these experiments accurately today. Unsafe
echo sanitization and early-response omissions must remain; filling missing
echo with defaults would create false facts. BYOXPC selection is an independent
axis, not an instrumentation class.

## Routine corrections and optional capabilities

The following source-account corrections require no design invention once
configuration work is authorized:

- `PWRunnerTestOverrides` still says presence flags a non-production run and
  that consumed overrides are mirrored. Describe supplied controls, inert and
  unreached values, sanitization and ambiguous absence instead; the runner
  README already states the central distinction correctly.
- `CWorkerInput` comments promise timeout or fatal termination from requested
  controls. Qualify them by native argument admission, reaching the boundary
  and actual outcomes. A dispatch return is not always a native attempt.
- The dossier's introductory “what ran it” phrase should describe selection
  before invocation, consistently with its detailed implementation.
- Correct stale helper-layout comments in the change that settles fallback
  behavior, so documentation continues to describe actual behavior.

Two missing facts remain possible future capabilities, not blockers:

1. **Dynamic validator allowances.** The orchestrator caps each I/O allowance
   by remaining aggregate time after planning and charges elapsed collection
   across phases. Echo/source cannot reconstruct those actual values. Current
   structured evidence records collection status and native outcomes, not a
   successful phase's resolved I/O allowance or aggregate accounting. Add
   those observations only if consumers need to compare collection budgets or
   diagnose their allocation. Existing exec and host-wait records do not fill
   this gap.
2. **Intervention entry/results.** Dedicated native entry/return observations
   would be needed to prove requested sleeps or self-signals were reached.
   Lifecycle evidence plus a retained request supports a qualified controlled
   experiment without that stronger claim. Adding instrumentation is a
   capability and disturbance choice, not required to remove a mode ambiguity.

No current requirement justifies a request split or compiling controls out of
the shipped binary. Both would add paths while leaving those missing facts
missing. Supervisor-specific configuration stays contingent on a separately
selected cleanup policy. The environment investigation can start from the
requested/resolved/observed distinction without waiting for a new schema;
machine settings, consent changes and environment-reset machinery still need
their own scoped decision.
