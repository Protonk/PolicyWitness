import Foundation
@testable import PWRunnerCore

// Constructed public records exercise each reader's stated domain. Raw encoding
// deliberately follows a separate host judgment so rejected records survive.
func runReaderCorpusTests(_ tk: TestKit) {
    tk.group("public reader definitions and applicability") {
        tk.run("retain typed preparation, declaration and degraded neighbours") {
            guard let artifacts = ProcessInfo.processInfo.environment["PW_TEST_ARTIFACTS"] else {
                throw TestFailure(message: "PW_TEST_ARTIFACTS is required")
            }
            let directory = URL(fileURLWithPath: artifacts).appendingPathComponent("reader-corpus", isDirectory: true)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            var rows: [[String: Any]] = []
            func emit(_ id: String, _ reply: PWRunnerRunResult, accepts: Bool,
                      rule: String, requiredIssues: [String] = [], lifecycleLike: String? = nil, projectionsLike: String? = nil) throws {
                var value = reply
                // Use the service's existing post-orchestration path observation,
                // also used by the live actor receipt controls.
                value.steps = enrichPathDiagnostics(steps: value.steps)
                var row: [String: Any] = ["id": id, "expected_semantic": accepts, "rule": rule,
                    "required_issues": requiredIssues, "origin": "typed_swift"]
                if id == "ordinary-overlong-step" { row["required_consumer_issues"] = ["invalid phase action_ids"] }
                else if id.hasSuffix("-combined") {
                    row["required_consumer_issues"] = ["actor visits disagree with schedule", "phase/action identity exceeds admitted grammar"]
                } else { row["required_consumer_issues"] = requiredIssues }
                if let lifecycleLike { row["lifecycle_like"] = lifecycleLike }
                if let projectionsLike { row["projections_like"] = projectionsLike }
                do {
                    try value.validateForReporting()
                    row["host_accepts"] = true
                } catch let error as PWRunnerReportingValidationError {
                    row["host_accepts"] = false; row["host_diagnostic"] = error.message
                }
                try pwPorcelainEncode(value).write(to: directory.appendingPathComponent(id + ".pwp"))
                rows.append(row)
            }
            func degrade(_ source: PWRunnerRunResult, retain: Bool = true) -> PWRunnerRunResult {
                var reply = source
                reply.reporting_failure = PWRunnerReportingFailure(diagnostic: "constructed reader corpus",
                    original_rc: source.rc, original_normalized_outcome: source.normalized_outcome,
                    original_error: source.error, evidence_retained: retain)
                reply.rc = 1; reply.normalized_outcome = NormalizedOutcome.runnerReportingFailed
                reply.error = "constructed reporting failure"
                for i in reply.steps.indices { reply.steps[i].comparison = nil }
                return reply
            }
            func ordinary(_ id: String = "s") -> PWRunnerRunResult {
                let probe = PWRunnerProbeStep(step_id: id,
                    sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
                        filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
                    attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts"))
                var steps = buildStepResults(probePlan: [probe], queryPlan: planValidatorQueries([probe]),
                    workerOutput: nil, validatorOutput: nil)
                steps[0].phase_id = "main"
                return PWRunnerRunResult(specimen_id: "reader-corpus", rc: 1,
                    normalized_outcome: NormalizedOutcome.workerSpawnFailed, error: "constructed no worker",
                    pid: 42, policy_format: "sbpl", steps: steps,
                    phases: [PWRunnerPhaseResult(phase_id: "main", ordinal: 1, action_ids: [id],
                        arrival_observed: false, completion_observed: false, collection_status: "not_reached")])
            }
            let ordinaryBase = ordinary()
            try emit("ordinary", ordinaryBase, accepts: true, rule: "ordinary action declaration")
            try emit("ordinary-empty-step", ordinary(""), accepts: true, rule: "ordinary admission allows an empty step ID")
            try emit("ordinary-utf8-step", ordinary(String(repeating: "é", count: 31) + "x"), accepts: true,
                rule: "63 UTF-8 bytes, not character count")
            try emit("ordinary-overlong-step", ordinary(String(repeating: "é", count: 32)), accepts: false,
                rule: "ordinary step capacity", requiredIssues: ["phase/action identity exceeds admitted grammar"])
            // applyRC is a producer observation, not a field of the carried
            // reply. Preserve the ordering builder's evidence of its conflict.
            func orderedOrdinary(applyRC: Int32) -> PWRunnerRunResult {
                let probe = PWRunnerProbeStep(step_id: "s",
                    sandbox_check: PWRunnerSandboxCheck(operation: "file-read-data",
                        filter: PWRunnerSandboxFilter(kind: "path", value: "/etc/hosts")),
                    attempt: PWRunnerAttempt(kind: "file", action: "open_read", target: "/etc/hosts"))
                let queryPlan = planValidatorQueries([probe])
                let validator = ValidatorOutput(validatorPid: 7, verdicts: [
                    ValidatorVerdict(stepId: "s", operation: "file-read-data", filterType: "PATH", filterTypeId: 1,
                        filterValue: "/etc/hosts", rc: 0, errnoVal: 0, outcome: "allow", rawLine: "constructed control")
                ], reaped: true, expectedProbes: queryPlan.compactMap { $0.probe })
                let worker = CWorkerOutput(workerPid: 42, readyByteReceived: true, applied: true, applyRC: applyRC,
                    applyErrno: 0, done: true, exitCode: 0,
                    slots: [CWorkerSlotResult(stepId: "s", rc: 0, errnoVal: 0, completed: true)],
                    pollStopReason: "done", reaped: true, waitErrors: [], hookInvoked: true,
                    proceedSet: true, proceedObserved: true, proceedOwnershipEstablished: true,
                    collectionBasis: "after_confirmed_reap")
                let classified = classify(workerResult: .success(worker), validatorResult: .success(validator),
                    expectedVerdictCount: 1)
                let ordering = buildOrdering(worker, validatorOutput: validator, hasQueries: true)
                return PWRunnerRunResult(specimen_id: "ordering-reader-corpus", rc: classified.rc,
                    normalized_outcome: classified.outcome, error: classified.error, pid: 42,
                    policy_format: "sbpl", sandboxed_after_apply: worker.applied,
                    steps: buildStepResults(probePlan: [probe], queryPlan: queryPlan, workerOutput: worker,
                        validatorOutput: validator, ordering: ordering), runner_subprocess: buildWorkerSubprocess(worker),
                    phases: [constructedPhase(worker, ids: ["s"], validator: validator)])
            }
            let ordered = orderedOrdinary(applyRC: 0)
            try expectEqual(ordered.steps[0].comparison?.order, "query_first")
            try emit("ordering-ordinary", ordered, accepts: true, rule: "successful producer application and complete query chain")
            let inconsistentApply = orderedOrdinary(applyRC: -1)
            try expectEqual(inconsistentApply.sandboxed_after_apply, true)
            try expectEqual(inconsistentApply.steps[0].comparison?.order, "unestablished")
            try expectEqual(inconsistentApply.phases[0].ordering?.protocol_violations, ["release_without_successful_application"])
            try emit("ordering-apply-status-conflict", inconsistentApply, accepts: true,
                rule: "constructed applied publication with nonzero producer-only applyRC retains its order violation")
            rows[rows.count - 1]["producer_apply_rc"] = -1
            var forcedOrder = inconsistentApply
            forcedOrder.steps[0].comparison?.order = "query_first"
            try emit("ordering-apply-status-forced-order", forcedOrder, accepts: false,
                rule: "a carried application flag cannot erase the producer's ordering violation",
                requiredIssues: ["query_first lacks eligible prediction and complete ordering chain"])
            rows[rows.count - 1]["required_consumer_issues"] = ["s: query_first lacks eligible record or ordering chain"]
            // This deliberately altered record is no longer the producer's
            // output. No recipient can recover the missing internal status.
            forcedOrder.phases[0].ordering?.protocol_violations = []
            try emit("ordering-erased-apply-status-conflict", forcedOrder, accepts: true,
                rule: "synthetic erased-violation reply has no carried nonzero applyRC to disprove query_first")
            let documents = try actorShapeDocuments()
            let preparations = documents.filter { $0.preparation_failure != nil && $0.reporting_failure == nil }
            try expectTrue(!preparations.isEmpty, "preparation fixture family missing")
            for (n, preparation) in preparations.enumerated() {
                let prefix = "preparation-\(n)"
                try emit(prefix, preparation, accepts: true, rule: "before-launch declarations and retained equipment")
                func change(_ name: String, rule: String = "preparation has no execution evidence",
                            accepts: Bool = false, issues: [String] = [], _ mutate: (inout PWRunnerRunResult) -> Void) throws {
                    var value = preparation; mutate(&value)
                    try emit(prefix + "-" + name, value, accepts: accepts, rule: rule, requiredIssues: issues)
                }
                try change("region") {
                    $0.authority_setup!.host.regions = [PWRunnerAuthorityScope(actor_id: $0.actors![0].actor_id,
                        actor_index: 0, required: true, disposition: "not_attempted")]
                }
                try change("custody") {
                    $0.authority_setup!.host.custody = [PWRunnerAuthorityScope(token_ref: "constructed", token_index: 0,
                        required: true, disposition: "not_attempted")]
                }
                try change("arrival") { $0.phases[0].arrival_observed = true }
                try change("completion") { $0.phases[0].completion_observed = true }
                try change("proceed") {
                    $0.phases[0].ordering = PWRunnerOrdering(collection_closed_before_proceed: false,
                        proceed_set: true, proceed_observed: false, validator_disposition: "not_invoked",
                        worker_lifetime_established: false, protocol_violations: [])
                }
                try change("missing-events", rule: "actor event list is present even when empty") { $0.extension_events = nil }
                try change("empty-action", rule: "actor action ID is nonempty") { $0.phases[0].action_ids[0] = "" }
                try change("nul-action", rule: "action ID is a C string") { $0.phases[0].action_ids[0] = "a\u{0}b" }
                try change("overlong-action", rule: "action ID UTF-8 capacity") { $0.phases[0].action_ids[0] = String(repeating: "é", count: 32) }
                try change("utf8-action", rule: "at-bound actor action ID", accepts: true) { $0.phases[0].action_ids[0] = String(repeating: "é", count: 31) + "x" }
                try change("empty-phase", rule: "phase ID is nonempty") { $0.phases[0].phase_id = "" }
                try change("nul-phase", rule: "phase ID is a C string") { $0.phases[0].phase_id = "p\u{0}q" }
                try change("overlong-phase", rule: "phase ID UTF-8 capacity") { $0.phases[0].phase_id = String(repeating: "é", count: 32) }
                try change("utf8-phase", rule: "at-bound phase ID", accepts: true) { $0.phases[0].phase_id = String(repeating: "é", count: 31) + "x" }
                try change("actor-index", rule: "actor table position is its index") { $0.actors![0].index = 1 }
                func renamedActor(_ value: inout PWRunnerRunResult, _ name: String) {
                    let old = value.actors![0].actor_id
                    value.actors![0].actor_id = name
                    for i in value.phases.indices where value.phases[i].actor_id == old { value.phases[i].actor_id = name }
                    for i in value.authority_setup!.workers.indices where value.authority_setup!.workers[i].actor_id == old {
                        value.authority_setup!.workers[i].actor_id = name
                    }
                    for i in value.equipment_entitlements!.indices where value.equipment_entitlements![i].actor_id == old {
                        value.equipment_entitlements![i].actor_id = name
                    }
                    if value.preparation_failure?.actor_id == old { value.preparation_failure?.actor_id = name }
                }
                try change("empty-actor", rule: "actor ID is nonempty") { renamedActor(&$0, "") }
                try change("nul-actor", rule: "actor ID is a C string") { renamedActor(&$0, "a\u{0}b") }
                try change("overlong-actor", rule: "actor ID UTF-8 capacity") { renamedActor(&$0, String(repeating: "é", count: 32)) }
                try change("utf8-actor", rule: "at-bound actor ID", accepts: true) { renamedActor(&$0, String(repeating: "é", count: 31) + "x") }
                try change("missing-visits", rule: "visits records declared membership") { $0.actors![0].visits = [] }
                try change("extra-visit", rule: "visits is exact") { $0.actors![0].visits.append(99) }
                try change("visit-order", rule: "visits is ordered") {
                    let repeated = $0.actors!.firstIndex { $0.visits.count > 1 }!
                    $0.actors![repeated].visits.reverse()
                }
                try change("actor-visit", rule: "actor_visit counts declarations") { $0.phases[0].actor_visit = 2 }
                try change("combined", rule: "combined grammar and visit faults remain visible",
                    issues: ["phase/action identity exceeds admitted grammar", "actor visits disagree with schedule"]) {
                    $0.phases[0].phase_id = String(repeating: "p", count: 64)
                    $0.actors![0].visits.append(99)
                }
                let degraded = degrade(preparation)
                try emit(prefix + "-degraded", degraded, accepts: true, rule: "degradation retains preparation", lifecycleLike: prefix)
                var inconsistent = degraded; inconsistent.actors![0].index = 99; inconsistent.phases[0].actor_visit = 99
                try emit(prefix + "-degraded-association", inconsistent, accepts: true,
                    rule: "kept degraded form permits retained association conflicts", lifecycleLike: prefix)
                inconsistent.actors = []
                try emit(prefix + "-degraded-empty-actors", inconsistent, accepts: true,
                    rule: "degraded form has no ordinary actor-list requirement")
            }
            let preparation = preparations[0]
            var wrongForm = ordinaryBase
            wrongForm.preparation_failure = preparation.preparation_failure
            try emit("ordinary-preparation", wrongForm, accepts: false, rule: "preparation is an actor-form record")
            let reissued = try reportedReply(wrongForm)
            try expectEqual(reissued.reporting_failure?.evidence_retained, true)
            try expectEqual(reissued.preparation_failure?.code, wrongForm.preparation_failure?.code)
            try emit("host-degraded-ordinary-preparation", reissued, accepts: true,
                rule: "actual host degradation retains the refused preparation assertion")
            try emit("degraded-ordinary-preparation", degrade(wrongForm), accepts: true,
                rule: "degradation retains otherwise inapplicable assertions")
            var minimal = PWRunnerRunResult(specimen_id: "minimal", rc: 1,
                normalized_outcome: NormalizedOutcome.runnerFailed, pid: 42, policy_format: nil, steps: [])
            minimal = degrade(minimal, retain: false)
            try emit("degraded-minimal", minimal, accepts: true, rule: "minimal degradation has no execution collections")
            var bad = minimal; bad.rc = 0
            try emit("degraded-bad-summary", bad, accepts: false, rule: "degraded summary must fail")
            bad = degrade(ordinaryBase); bad.steps[0].comparison = ordinaryBase.steps[0].comparison
            try emit("degraded-comparison", bad, accepts: false, rule: "degradation removes comparisons")
            bad = degrade(ordinaryBase, retain: false)
            try emit("degraded-unretained-steps", bad, accepts: false, rule: "minimal retention flag matches collection absence")
            var actorBase = documents[0]
            actorBase.steps = enrichPathDiagnostics(steps: actorBase.steps)
            try emit("actor-complete", actorBase, accepts: true, rule: "ordinary actor evidence")
            let appliedActor = actorBase.actors!.firstIndex { $0.mode == "apply" && $0.setup_status == "applied" }!
            var mismatchedSetup = actorBase
            mismatchedSetup.actors![appliedActor].setup_status = "unapplied_declared"
            try emit("actor-apply-declares-unapplied", mismatchedSetup, accepts: false,
                rule: "ordinary actor identity checks reject a setup declaration inconsistent with mode; extension subreader does not own identity",
                requiredIssues: ["apply actor cannot declare an unapplied setup"])
            rows[rows.count - 1]["expected_extensions"] = true
            let retainedSetup = try reportedReply(mismatchedSetup)
            try emit("host-degraded-actor-setup", retainedSetup, accepts: true,
                rule: "host rejection retains the inconsistent setup declaration and removes comparisons")
            rows[rows.count - 1]["expected_reporting_failure"] = true
            rows[rows.count - 1]["reporting_failure_observed"] = retainedSetup.reporting_failure?.evidence_retained == true
                && retainedSetup.actors?[appliedActor].setup_status == "unapplied_declared"
                && retainedSetup.steps.allSatisfy { $0.comparison == nil }
            let retainedWorker = degrade(actorBase)
            try emit("degraded-actor-lifecycle-valid", retainedWorker, accepts: true,
                rule: "degradation retains independently valid worker lifecycle claims")
            rows[rows.count - 1]["expected_lifecycle_findings"] = [] as [[String: Any]]
            // The observed owned exit stays zero. Only the carried claim changes;
            // degradation admits that record without certifying its assertion.
            try expectEqual(retainedWorker.actors![0].actor_id, "A")
            try expectEqual(retainedWorker.actors![0].subprocess?.reaped, true)
            try expectEqual(retainedWorker.actors![0].subprocess?.exit_code, 0)
            try expectNil(retainedWorker.actors![0].subprocess?.term_signal)
            try expectEqual(retainedWorker.actors![0].subprocess?.disposition?.questions.final_status?.answer, "exit_code")
            var conflictingClaim = retainedWorker
            conflictingClaim.actors![0].subprocess?.disposition?.questions.final_status?.value = .integer(17)
            try emit("degraded-actor-lifecycle-wrong-exit", conflictingClaim, accepts: true,
                rule: "admitted degradation retains a worker claim contradicted by its owned exit")
            rows[rows.count - 1]["expected_lifecycle_findings"] = [[
                "rule": "D1", "kind": "wrong_answer", "question": "final_status", "step_index": NSNull(),
                "detail": "actor 'A': expected {'state': 'supported', 'answer': 'exit_code', 'value': 0}, record says 'exit_code' 17"
            ]] as [[String: Any]]
            var fallback = degrade(actorBase)
            fallback.steps[0].attempt.requested_kind = "retained_future_operation"
            try emit("degraded-native-relationship", fallback, accepts: true,
                rule: "ordinary native-operation semantics do not classify degraded form")
            // Eleven pairs alone do not establish their source. This baseline has
            // successful apply: each alternative pair is an ineligible neighbour.
            let pairs = [("not_requested", "unapplied_declaration"), ("not_attempted", "worker_not_launched"),
                ("not_attempted", "terminal_authority_setup_refusal"), ("not_attempted", "terminal_input_refusal"),
                ("not_attempted", "terminal_parameter_refusal"), ("not_attempted", "terminal_compile_refusal"),
                ("not_attempted", "terminal_timing_refusal"), ("observed", "applied_publication"),
                ("observed", "apply_failure_publication"), ("unobserved", "apply_call_boundary_without_result"),
                ("unobserved", "no_eligible_apply_publication")]
            guard let applyIndex = actorBase.actors?.firstIndex(where: { $0.mode == "apply" && $0.applied == true }) else {
                throw TestFailure(message: "applied baseline missing")
            }
            for (i, pair) in pairs.enumerated() {
                var value = actorBase
                value.actors![applyIndex].application = PWRunnerActorApplication(state: pair.0, basis: pair.1)
                try emit("application-pair-\(i)", value, accepts: i == 7, rule: "application pair requires its eligible source")
            }
            let applicationFixtures = try readerApplicationFixtures()
            try expectEqual(Set(applicationFixtures.map { $0.expected.basis }), Set(pairs.map { $0.1 }))
            try expectEqual(applicationFixtures.count, pairs.count)
            for fixture in applicationFixtures {
                let identity = "application-positive-" + fixture.id
                try emit(identity, fixture.reply, accepts: true,
                    rule: "production assembly over eligible " + fixture.expected.basis + " observations")
                rows[rows.count - 1]["application_expected"] = ["actor_id": fixture.actorID,
                    "state": fixture.expected.state, "basis": fixture.expected.basis]
                let index = fixture.reply.actors!.firstIndex { $0.actor_id == fixture.actorID }!
                rows[rows.count - 1]["application_matches_expected"] = fixture.reply.actors![index].application == fixture.expected
                var wrong = fixture.reply
                let alternative = fixture.expected.basis == "no_eligible_apply_publication"
                    ? PWRunnerActorApplication(state: "unobserved", basis: "apply_call_boundary_without_result")
                    : PWRunnerActorApplication(state: "unobserved", basis: "no_eligible_apply_publication")
                wrong.actors![index].application = alternative
                try emit(identity + "-wrong-assessment", wrong, accepts: false,
                    rule: "assessment keeps the exact source eligibility and precedence",
                    requiredIssues: ["application assessment violates source precedence"])
                if fixture.expected.basis.hasPrefix("terminal_") || fixture.expected.basis == "apply_failure_publication" {
                    var contradictory = fixture.reply
                    contradictory.actors![index].applied = true
                    contradictory.actors![index].application_count = 1
                    contradictory.actors![index].application = PWRunnerActorApplication(state: "observed", basis: "applied_publication")
                    try emit(identity + "-contradictory-applied", contradictory, accepts: false,
                        rule: "an applied flag cannot erase a terminal pre-apply or failed-apply publication",
                        requiredIssues: ["contradictory application publication"])
                }
            }
            // Worker-not-launched outranks the otherwise eligible catch-all pair.
            var precedence = preparation
            guard let absentApply = precedence.actors?.firstIndex(where: { $0.mode == "apply" }) else {
                throw TestFailure(message: "unlaunched apply actor missing")
            }
            precedence.actors![absentApply].application = PWRunnerActorApplication(state: "unobserved", basis: "no_eligible_apply_publication")
            try emit("application-precedence", precedence, accepts: false, rule: "source precedence outranks eligible catch-all",
                requiredIssues: ["application assessment violates source precedence"])
            if let gateBase = documents.first(where: { $0.reporting_failure == nil && $0.phases.contains { $0.termination_gate?.outcome == "satisfied" } }) {
                try emit("gate-satisfied", gateBase, accepts: true, rule: "owned, ordered and clocked source ending")
                var missing = gateBase
                let gatePhase = missing.phases.firstIndex { $0.termination_gate?.outcome == "satisfied" }!
                try expectEqual(gatePhase, 3, "the inspected gated fixture's dependent phase moved")
                try expectEqual(missing.phases[gatePhase].phase_id, "b_consume")
                let gate = missing.phases[gatePhase].termination_gate!
                let source = missing.phases.firstIndex { $0.phase_id == gate.source_final_phase_id }!
                missing.phases[source].activation_observation!.observed_ns = nil
                try emit("gate-missing-source-time", missing, accepts: false, rule: "satisfied requires both source times",
                    requiredIssues: ["satisfied termination gate lacks natural owned reap after final activation"], projectionsLike: "gate-satisfied")
                rows[rows.count - 1]["required_subject_issues"] = [[
                    "detail": "satisfied termination gate lacks natural owned reap after final activation",
                    "subject_path": ["phases", "3", "termination_gate"]]]
                try emit("gate-degraded-missing-source-time", degrade(missing), accepts: true,
                    rule: "degradation retains gate assertion without ordinary certification", projectionsLike: "gate-satisfied")
            } else { throw TestFailure(message: "satisfied gate baseline missing") }
            let manifest: [String: Any] = ["domain": "constructed typed replies; no sandboxed worker execution", "cases": rows]
            try JSONSerialization.data(withJSONObject: manifest, options: [.prettyPrinted, .sortedKeys])
                .write(to: directory.appendingPathComponent("swift.json"))
            for row in rows {
                if row["expected_reporting_failure"] != nil {
                    try expectEqual(row["reporting_failure_observed"] as? Bool, true,
                        "\(row["id"]!): host failed to retain degraded evidence without comparisons")
                }
                if row["application_expected"] != nil {
                    try expectEqual(row["application_matches_expected"] as? Bool, true,
                        "\(row["id"]!): producer application pair disagrees with the eligible source")
                }
                try expectEqual(row["host_accepts"] as? Bool, row["expected_semantic"] as? Bool,
                    "\(row["id"]!): \(row["host_diagnostic"] ?? "accepted")")
            }
        }
    }
}
