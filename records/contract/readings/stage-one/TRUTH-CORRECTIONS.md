> Deposited after root applied the proposed text corrections and regenerated the contract. The original preparation note below retains its prior unapplied status and source-reading grade. The preserved delta and revision reading record the later document.

# Stage-one truth corrections — unapplied patch

The patch changes authored contract text and support metadata only. It has not been applied to the repository. No generator, build, test dispatcher or product command was run. The patch was constructed from the live authored files listed below while the release battery remained active.

Root owns the contract title, duplicate success-rule changes and renderer. Those areas are excluded. The diagnostics definition is moved before its first table use; its separate outer_result rule is untouched. The patch introduces no new rule, condition, effect, gap, field or surface node and preserves the sequence/count of every existing free.when/free.condition/free.dependency/free.effect key in each touched file. This is a textual drafting check, not parser or generator validation. Existing limit IDs supply every added capacity/duration/count through scalar spans; no limits input or prose exemption is changed.

## Truth and readability corrections

- envelope.data.actor_policy_checks: run_flow.rs actor_policies collects every actor.sandbox.policy object without mode filtering, then actor_fallback_checks iterates that vector. The field now agrees with policy.actor_check. Source read. The existing actor_fallback_preserves_resolved_inputs_order_and_transport_evidence check was read but covers valid apply/unapplied inputs, not a malformed-mode policy object.
- policy.fallback.classify: RunnerClientRun::fallback_eligible requires accepted transport, absent delivery error and terminal xpc_error. fallback_compilation_is_requested_only_for_an_admitted_xpc_error was read: a host outcome labelled xpc_error does not select the helper. No execution credited.
- request.overrides.worker_timeout_ms and validator_io_timeout_ms: timeoutMsForCWorker and timeoutMsForValidator use max(50, override); validator remaining collection can further reduce its effective allowance. Source read; existing planning-control ownership retained.
- transport.delivery.acquire: beginAttempt checks the prior count, then appends the next attempt. The session check explicitly expects 256 connections. State at most 256 total, fewer already begun before another starts. Source/check read only.
- request.specimen.contract/specimen_id: PWRunnerRunSpec.init(from:) requires non-null strings. Contract has explicit missing/null/type branches; specimen_id uses decode(String.self). Empty specimen_id remains accepted. Source read.
- request.overrides.override_coverage: distinguish incomplete attribution across the override set from absence of all existing controls. Current failure_boundaries and witness_contract/phases accounts already identify signed-app override cases. These accounts were read; no acceptance result is newly credited.
- identity.definitions.cause: remove incidental log-text wording that led the isolated reader to expect a later log record. Existing query/attempt/cause meanings remain.
- diagnostics.execution.families: define ordinary semantic reply before the table rather than after it. This is the nondegraded branch and includes actors.

## Quantity ownership and applicability

- profile.receipt.bytecode_length and profile.receipt.host.extent use compiled_profile (1048576 raw bytes), separately per opted-in worker. CWorker.captureBytes, decodeProfileCapture and PW_SHM_CAPTURE_BYTES establish the capacity and host predicate.
- lifecycle.diagnostic.length/text use worker_diagnostic (4095 retained bytes excluding NUL), before replacement decoding; native storage is PW_SHM_DIAGNOSTIC_BYTES=4096. The byte bound does not constrain the encoded size after invalid-byte replacement.
- steps.attempt.stdout/stderr use exec_stream (1023 retained bytes each). PW_SHM_CHILD_OUTPUT_BYTES=1024 and pw_worker_exec.h truncation logic reserve NUL; the marker takes part of retained content.
- probes.attempt.exec uses exec_child_wait (10000 ms) and exec_attempt_budget (115000 ms). Continuous time includes sleep; worker origin precedes setup; acknowledged release waits and accepted parked activation waits are excluded. The child allowance starts after spawn and is capped by remaining active-plan allowance. Blocking calls can outlast allowances. lifecycle.exec_collection.deadline_kind now references this rule.
- lifecycle.exec_reap uses exec_reap_grace (1000 ms) after collection, on continuous time; existing ownership/request failure branch priority remains. pw_worker_timing.h supplies configured values.
- lifecycle.transfer_timeout.budget_ms uses worker_policy_transfer (5000 ms), starting immediately after spawn on an absolute monotonic deadline; partial writes/EINTR do not reset it. Actor delivery is additionally capped by remaining setup time.
- lifecycle.worker.ready_wait uses worker_ready_wait (1000 ms) after successful transfer and readiness-pipe setup. ActorSession caps it by remaining setup. Expiry leaves the hint absent and execution continues.
- lifecycle.worker.exit_grace_wait and lifecycle.validator.exit_grace_wait use worker_exit_grace and validator_exit_grace (1000 ms each). These are monotonic stage waits, with subsequent cleanup/final reap separately observed.
- lifecycle.validator and records describe runValidator's recordLimit=max(1,N)*2 and byteLimit=recordLimit*8192, using validator_records_per_query and validator_reply_bytes_per_query. The stdout received count can exceed retention; on overflow the complete retained LF prefix survives. wire.validator.read references that owning subject.
- equipment.execution.inspect uses actor_setup_allowance (10000 ms) for the scheduler guard and reuses actor_lifetime_cutoff's configured scalar (180000 ms) for the additional inspection deadline. See the distinct-clock note below.

## Inspection clocks: qualification from following the caller

ActorOrchestration creates inspectionDeadline from MonotonicDeadline.now() before ActorScheduler.run. ActorEquipment.inspect checks valid start and final samples, nondecreasing final time, and strict start/end < deadline when present. A missing initial orchestration sample produces nil, so this additional deadline comparison is absent.

Following the caller qualifies that local branch: ActorScheduler.run independently brackets didSetUp with the shared setup deadline from launchAndSetUp, requires valid before/after samples, and turns an otherwise successful over-deadline inspection into inspection_deadline. The additional optional deadline therefore does not define the whole scheduling guard.

Both host guards use CLOCK_MONOTONIC. The reused actor_lifetime_cutoff inventory entry describes a different continuous-clock worker cutoff, with its own origin. No independent inspection limit ID exists; the patch uses that entry only for the actual shared configured scalar and states the different clock/origin. The existing inventory counting is not copied or broadened.

Source read: ActorOrchestration inspectionDeadline; ActorEquipmentPreparation.inspect; ActorScheduler.run/launchAndSetUp; MonotonicDeadline.now; PWActorLimits.setupMs/lifetimeMs. Existing ActorEquipmentTests cover already expired deadlines and missing/backward/late inspection clocks; they do not establish initial orchestration-clock failure followed by good scheduler/inspection samples. The existing live-inspection evidence gap carries that missing case. No runtime failure or elapsed timing is newly established.

## Review and application limits

All runtime meanings above are source-inspected; listed controls were read, not executed by this task. Existing owners remain at their existing grades. New source citations identify the actual helper/constant/caller boundary. Root should apply only after the active battery finishes, review concurrent edits in shared files, regenerate through owning tools and perform the authorized verification. The patch does not claim rendered output, symbol resolution, limit rendering, parser acceptance, fresh shapes or release credit.

The source of this work is the 101-entry unprompted reading and its Close-out, snapshot SHA256 9e3c46c13a8899512f68d9a07e6cecdfc3e2f1057bcf82bada882d3d9029185c, plus the read-only adjudication. Prompted answers were not opened while constructing this patch and will be audited separately.

## Patch preimages

- docs/contract/00-identity.surface.md: SHA256 771993f1b2049bccc9db17f765ef1224b3a417e9502d6b356f3ef8497a9fcf50; free-text keys {"condition": 1, "effect": 3}.
- docs/contract/10-request.surface.md: SHA256 58fcb06847f314289dc71f12880f8ec3f2fb15a596aab2da271ffb5082717083; free-text keys {"effect": 6}.
- docs/contract/11-policy.surface.md: SHA256 d97f7fe4c78a08ded97baa4165526b99cac1604741b7d5d769c101b7564eedbc; free-text keys {"effect": 9}.
- docs/contract/12-probes.surface.md: SHA256 ac408446acf98c9648d430fffd5e56536b8bc93dbe5227f8b51fc6e11d48e188; free-text keys {"effect": 4}.
- docs/contract/20-transport.surface.md: SHA256 7d1164ea6069e05c2326cad3db22c90febf2cad41979deb364b2eadca61bf1db; free-text keys {"condition": 6, "effect": 6}.
- docs/contract/31-steps.surface.md: SHA256 7cb933fc7a94897b1fa5ead58e451c6d4d47d89b3ab199046a0bc7402689ca14; free-text keys {"condition": 2, "effect": 5, "when": 1}.
- docs/contract/32-lifecycle.surface.md: SHA256 c75b61da34af7d5d5abf2ec6de0745aab2ef3b8ba035f69e7be5541f14db44b2; free-text keys {"condition": 2, "effect": 2}.
- docs/contract/21-wire.surface.md: SHA256 ea974cb4017238dce33ae640c13483218abe0e4ac8e852489604b6e22b5928a0; free-text keys {"condition": 6, "effect": 6}.
- docs/contract/34-equipment.surface.md: SHA256 b2d1e8bc360c934d976f0c658130639c0971f9f9b580d2499efe73b2a81f703d; free-text keys {"condition": 4, "effect": 4}.
- docs/contract/35-profile.surface.md: SHA256 a24a30b7f91ad09a395ac402413e5481817c8f3cb398233f87c6e9a269e36efb; free-text keys {"condition": 9, "effect": 2, "when": 2}.
- docs/contract/40-envelope.surface.md: SHA256 13471bf909930c6691ec6ab084d1807be41ed30ecb28071e92cf01a8c6a9f4f6; free-text keys {"condition": 1, "effect": 2, "when": 1}.
- docs/contract/41-diagnostics.surface.md: SHA256 51abff1b946539b3663cb2cdc0aab15c3090e23153212d7ec8e78906b18d2519; free-text keys {"condition": 2, "effect": 4}.
