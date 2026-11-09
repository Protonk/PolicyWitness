import Darwin
import Foundation

/*
 * CWorkerOrchestrator — host-side wiring that runs a single specimen
 * through the runner's C code path: pw-probe-runner for attempts +
 * sb_api_validator --batch for sandbox_check verdicts, joined into
 * one PWRunnerRunResult envelope.
 *
 * The orchestrator owns:
 *   1. Request → driver inputs translation:
 *        - probe_plan → [CWorkerSlotInput] (worker attempts)
 *        - probe_plan → [ValidatorProbe] (validator queries),
 *          skipping (op, filter) pairs in
 *          ProbeRunner.predictionUnavailableOpFilters
 *        - policy.params → [CWorkerParam]
 *   2. Driver invocation:
 *        - runCWorker(...) with a postApplied hook that runs
 *          runValidator against the sandboxed worker_pid
 *   3. Driver outputs → per-step PWRunnerStepResult:
 *        - sandbox_check from validator verdict OR synthesized
 *          prediction_unavailable result for skipped pairs
 *        - attempt from CWorker slot result
 *        - comparison records the attempt channel's classified
 *          observation, the submitted-scope relations, the order PW
 *          established and the planner's exclusion or lifecycle limits;
 *          it asserts nothing about agreement between the channels
 *   4. Classifier:
 *        - normalized_outcome from C-worker disposition +
 *          validator disposition + per-slot completed/done state
 *
 * Validation and policy-hash computation are PWRunnerService.runReservedSpecimen's
 * responsibility.
 * The orchestrator only sees a request that has already passed
 * those gates.
 */

enum CWorkerOrchestrator {

    // ---- entry point -----------------------------------------------------

    static func run(
        parsed: PWRunnerRunSpec,
        policyHash: Data,
        bundleId: String?,
        workerExecutablePath: String,
        validatorExecutablePath: String,
        equipmentBundleURL: URL = Bundle.main.bundleURL, equipmentCalls: ActorEquipmentCalls = ActorEquipmentCalls()
    ) -> PWRunnerRunResult {
        run(parsed: parsed, policyHash: policyHash, bundleId: bundleId,
            workerExecutablePath: workerExecutablePath, validatorExecutablePath: validatorExecutablePath,
            validatorSpawn: nativeValidatorSpawn, equipmentBundleURL: equipmentBundleURL, equipmentCalls: equipmentCalls)
    }

    // Tests substitute native validator launch or child-process calls; worker
    // orchestration, classification, assembly and encoding remain production.
    static func run(
        parsed: PWRunnerRunSpec,
        policyHash: Data,
        bundleId: String?,
        workerExecutablePath: String,
        validatorExecutablePath: String,
        validatorSpawn: @escaping ValidatorSpawnCall,
        validatorProcessCalls: @escaping (Int) -> ChildProcessCalls = { _ in ChildProcessCalls() },
        equipmentBundleURL: URL = Bundle.main.bundleURL, equipmentCalls: ActorEquipmentCalls = ActorEquipmentCalls()
    ) -> PWRunnerRunResult {
        switch admitSpecimen(parsed) {
        case .capacity(let refused):
            return admissionRefusalReply(parsed: parsed, refused: refused, bundleId: bundleId, policyHash: policyHash)
        case .refused(let failure):
            return requestRefusalReply(parsed: parsed, failure: failure, bundleId: bundleId, policyHash: policyHash)
        case .accepted(let admitted):
            return run(admitted: admitted, policyHash: policyHash, bundleId: bundleId,
                workerExecutablePath: workerExecutablePath, validatorExecutablePath: validatorExecutablePath,
                validatorSpawn: validatorSpawn, validatorProcessCalls: validatorProcessCalls, equipmentBundleURL: equipmentBundleURL, equipmentCalls: equipmentCalls)
        }
    }

    static func run(admitted: AdmittedSpecimen, policyHash: Data, bundleId: String?,
                    workerExecutablePath: String, validatorExecutablePath: String,
                    validatorSpawn: @escaping ValidatorSpawnCall = nativeValidatorSpawn,
                    validatorProcessCalls: @escaping (Int) -> ChildProcessCalls = { _ in ChildProcessCalls() },
                    equipmentBundleURL: URL = Bundle.main.bundleURL, equipmentCalls: ActorEquipmentCalls = ActorEquipmentCalls()) -> PWRunnerRunResult {
        let parsed = admitted.request
        if let plan = admitted.actorPlan {
            return runActors(parsed: parsed, plan: plan, bundleId: bundleId, workerExecutablePath: workerExecutablePath,
                validatorExecutablePath: validatorExecutablePath, validatorSpawn: validatorSpawn,
                validatorProcessCalls: validatorProcessCalls, equipmentBundleURL: equipmentBundleURL, equipmentCalls: equipmentCalls)
        }
        guard let policy = parsed.policy else {
            return requestRefusalReply(parsed: parsed,
                failure: PWRunnerRequestFailure(code: "missing_field", path: ["policy"]), bundleId: bundleId, policyHash: policyHash)
        }

        // ---- translation: request → driver inputs ------------------------
        let phases = parsed.executionPhases
        let actions = phases.flatMap { $0.actions }
        let workerSlots = actions.compactMap { $0.probe }.map { makeWorkerSlot(stepID: $0.step_id, attempt: $0.attempt) }
        let workerParams = workerParamsFromPolicy(policy)
        var offset = 0
        let phaseInputs = phases.map { phase -> CWorkerPhaseInput in
            defer { offset += phase.actions.count }
            return CWorkerPhaseInput(firstSlot: offset, endSlot: offset + phase.actions.count)
        }

        // _test_overrides.worker_timeout_ms drives the sentinel
        // deadline on the C-worker path. Floored at 50 ms because a
        // smaller deadline fires before any real worker can complete
        // its post-apply work and would just generate spurious
        // runner_timeouts.
        let workerInput = CWorkerInput(
            workerExecutablePath: workerExecutablePath,
            policy: policy.sbpl_source ?? "",
            params: workerParams,
            slots: workerSlots,
            phases: phaseInputs,
            sentinelTimeoutMs: timeoutMsForCWorker(
                override: parsed._test_overrides?.worker_timeout_ms
            ),
            postApplyHangMs: parsed._test_overrides?.worker_post_apply_hang_ms,
            postApplyKillSignal: parsed._test_overrides?.worker_post_apply_kill_signal,
            preReadyHangMs: parsed._test_overrides?.worker_pre_ready_hang_ms,
            killBeforePublishSlot: parsed._test_overrides?.worker_kill_before_publish_slot,
            captureCompiledProfile: policy.capture_compiled_profile == true,
            captureNonce: policy.capture_nonce
        )


        // Fresh planning occurs only after this phase's arrival. Each synchronous
        // collection closes before the driver's guarded ordinal release.
        var queryPlans = phases.map { _ in [ValidatorQueryDecision]() }
        var validatorResults = phases.map { _ -> ValidatorClientResult? in nil }
        var collectionStatuses = phases.map { _ in "not_reached" }
        var collectionRemainingNs = UInt64(max(1, min(phaseCollectionBudgetMs, parsed._test_overrides?.validator_total_timeout_ms ?? phaseCollectionBudgetMs))) * 1_000_000
        let workerResult = runCWorker(workerInput, phaseBoundary: { workerPid, index in
            guard let start = MonotonicDeadline.now() else {
                collectionStatuses[index] = "clock_unavailable"; collectionRemainingNs = 0; return
            }
            defer {
                if let end = MonotonicDeadline.now(), end >= start {
                    collectionRemainingNs -= min(collectionRemainingNs, end - start)
                } else { collectionRemainingNs = 0 }
            }
            queryPlans[index] = planValidatorQueries(phases[index].actions.compactMap { $0.probe })
            let probes = queryPlans[index].compactMap { $0.probe }
            if probes.isEmpty { collectionStatuses[index] = "not_needed"; return }
            guard let now = MonotonicDeadline.now(), now >= start else {
                collectionStatuses[index] = "clock_unavailable"; collectionRemainingNs = 0; return
            }
            let planningNs = now - start
            guard collectionRemainingNs > planningNs + 1_000_000 else {
                collectionStatuses[index] = "budget_exhausted"; return
            }
            let timeout = min(timeoutMsForValidator(override: parsed._test_overrides?.validator_io_timeout_ms),
                              Int((collectionRemainingNs - planningNs) / 1_000_000))
            let input = ValidatorClientInput(executablePath: validatorExecutablePath, targetPid: workerPid,
                probes: probes, verdictReadTimeoutMs: timeout)
            validatorResults[index] = runValidator(input, processCalls: validatorProcessCalls(index), spawn: validatorSpawn)
            collectionStatuses[index] = "collected"
        })

        let workerOutput = unwrapWorkerOutput(workerResult)
        let disposition = workerOutput.map { resolveDisposition($0, plan: actions.contains(where: { $0.probe == nil }) ? nil : parsed.probe_plan) }
        var runOutcome = classify(workerResult: workerResult, validatorResult: nil,
                                  expectedVerdictCount: 0, disposition: disposition)
        var phaseResults: [PWRunnerPhaseResult] = []
        var stepResults: [PWRunnerStepResult] = []
        let refused: Bool
        if case .failure(let error, nil) = workerResult { refused = error.isPreSpawnRefusal }
        else { refused = false }
        if !refused {
            for (index, phase) in phases.enumerated() {
                let validatorOutput = unwrapValidatorOutput(validatorResults[index])
                let hasQueries = !queryPlans[index].compactMap { $0.probe }.isEmpty
                let observation = workerOutput?.phases.indices.contains(index) == true ? workerOutput!.phases[index] : nil
                let ordering = workerOutput.map { buildPhaseOrdering($0, index: index,
                    input: phaseInputs[index], validatorOutput: validatorOutput, hasQueries: hasQueries) }
                var steps = buildStepResults(probePlan: phase.actions.compactMap { $0.probe }, queryPlan: queryPlans[index],
                    workerOutput: workerOutput, validatorOutput: validatorOutput, ordering: ordering,
                    disposition: disposition, stepOffset: phaseInputs[index].firstSlot)
                for i in steps.indices { steps[i].phase_id = phase.phase_id }
                stepResults += steps
                var spawnFailure: PWRunnerSpawnFailure?
                if case .failure(.spawnFailed(let failure), _) = validatorResults[index] { spawnFailure = failure }
                phaseResults.append(PWRunnerPhaseResult(phase_id: phase.phase_id, ordinal: index + 1,
                    action_ids: phase.actions.map { $0.stepID }, arrival_observed: observation?.arrived ?? false,
                    completion_observed: observation?.completed ?? false, collection_status: collectionStatuses[index],
                    ordering: ordering,
                    validator_subprocess: validatorOutput.map { buildValidatorSubprocess($0, phaseId: phase.phase_id, ordinal: index + 1) },
                    validator_spawn_failure: spawnFailure))
                // Worker failure has precedence; otherwise the first failed
                // collection determines the summary. Every collection is retained.
                if runOutcome.rc == 0 {
                    runOutcome = classify(workerResult: workerResult, validatorResult: validatorResults[index],
                        expectedVerdictCount: queryPlans[index].compactMap { $0.probe }.count, disposition: disposition)
                    if runOutcome.rc == 0 && ["budget_exhausted", "clock_unavailable"].contains(collectionStatuses[index]) {
                        runOutcome = ClassifiedRun(outcome: NormalizedOutcome.validatorUnavailable, rc: 1,
                            error: "phase collection unavailable: " + collectionStatuses[index])
                    }
                }
            }
        }

        let admissionFailure: PWRunnerAdmissionFailure?
        if case .failure(.admissionFailed(let record), _) = workerResult { admissionFailure = record }
        else { admissionFailure = nil }
        let topPid: Int = workerOutput.map { Int($0.workerPid) } ?? Int(getpid())
        let runnerSubprocess = workerOutput.map { buildWorkerSubprocess($0, disposition: disposition) }

        return PWRunnerRunResult(
            specimen_id: parsed.specimen_id,
            run_kind: parsed.run_kind,
            rc: runOutcome.rc,
            normalized_outcome: runOutcome.outcome,
            error: runOutcome.error,
            pid: topPid,
            bundle_id: bundleId,
            policy_format: policy.format,
            policy_sha256: policyHash,
            sandboxed_after_apply: workerOutput?.applied,
            steps: stepResults,
            runner_subprocess: runnerSubprocess,
            phases: phaseResults,
            test_overrides: parsed._test_overrides,
            compiled_profile: workerOutput?.profileCapture,
            admission_failure: admissionFailure
        )
    }

    // ---- bundle path resolution -----------------------------------------

    /// pw-probe-runner lives at `<this xpc service>/Contents/MacOS/pw-probe-runner`.
    /// The XPC service binary itself lives at
    /// `<this xpc service>/Contents/MacOS/<service-name>` — Bundle.main
    /// resolves to the service bundle. Sibling resolution.
    static func defaultWorkerExecutablePath() -> String {
        let bundleURL = Bundle.main.bundleURL
        return bundleURL
            .appendingPathComponent("Contents/MacOS/pw-probe-runner")
            .path
    }

    /// The validator belongs to this service bundle, including BYOXPC copies.
    /// Resolution does not check availability: a reached spawn records its
    /// native result, while phases without eligible queries do not launch it.
    static func defaultValidatorExecutablePath(bundleURL: URL = Bundle.main.bundleURL) -> String {
        bundleURL
            .appendingPathComponent("Contents/MacOS/sb_api_validator")
            .path
    }

}

// MARK: - Driver-result unwrapping

private func unwrapWorkerOutput(_ result: CWorkerRunResult) -> CWorkerOutput? {
    switch result {
    case .success(let out): return out
    case .failure(_, let partial): return partial
    }
}

private func unwrapValidatorOutput(_ result: ValidatorClientResult?) -> ValidatorOutput? {
    guard let result else { return nil }
    switch result {
    case .success(let out):       return out
    case .failure(_, let partial): return partial   // degraded evidence is still evidence
    }
}
