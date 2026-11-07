import Darwin
import Foundation

/*
 * ActorScheduler — the actor form's host driver. It owns every actor session
 * of one specimen and walks the global schedule serially: activate the phase's
 * actor, await its arrival, run the caller's collection against that live
 * process, release the visit ordinal, await completion, record the visit.
 *
 * The scheduler decides nothing about what a phase means and interprets no
 * attempt result; it records what it stored and what it observed. A failed
 * active actor is stopped and its quiescence established before the schedule
 * advances; unresolved termination cancels the rest of the schedule. Every
 * launched process is exit-requested, graced, killed if needed and reaped at
 * the end, and each actor's output is collected from its own region.
 *
 * Authority mailboxes are serviced while actors are parked.
 */

/// One scheduled visit: the global phase index (ordinal = index + 1), the
/// actor and that actor's local visit index into its own phase records.
struct ActorScheduleEntry {
    let phaseIndex: Int
    let actorIndex: Int
    let visit: Int
    var terminationDependency: ActorTerminationDependency? = nil
}

struct ActorScheduleInput {
    /// One driver input per actor in actor order. The scheduler assigns the
    /// actor index, mode and shared cutoff; callers supply policy, slots and
    /// the actor's own phase partition with each visit's global ordinal.
    var actors: [CWorkerInput]
    var applies: [Bool]
    var schedule: [ActorScheduleEntry]
    var setupAllowanceMs = PWActorLimits.setupMs
    var executionAllowanceMs = PWActorLimits.executionMs
    var lifetimeMs = PWActorLimits.lifetimeMs
    /// The admitted tokens and deliveries; nil when no actor issues or transfers.
    var authority: AuthorityPlan? = nil
    var didSetUp: ((_ actorIndex: Int, _ pid: pid_t) -> String?)? = nil
}

/// Why one actor's setup ended, decided from its own publications.
enum ActorSetupStatus: String {
    case notLaunched = "not_launched"
    case launchRefused = "launch_refused"
    case transferFailed = "transfer_failed"
    case applied = "applied"
    case unappliedDeclared = "unapplied_declared"
    case setupFailed = "setup_failed"
    case authoritySetupFailed = "authority_setup_failed"
    case exitedBeforeSetup = "exited_before_setup"
    case setupTimeout = "setup_timeout"

    var usable: Bool { self == .applied || self == .unappliedDeclared }
}

struct ActorSessionRecord {
    let index: Int
    var pid: pid_t?
    var parentPid: pid_t = getpid()
    var launchFailure: CWorkerRunError?
    var setupStatus: ActorSetupStatus = .notLaunched
    /// Applications observed through the worker's own publication: 0 or 1.
    var applicationCount = 0
    var output: CWorkerOutput?
    /// Why the scheduler stopped this actor before the schedule ended, if it did.
    var stopReason: String?
    /// never_launched, reaped, or unresolved (a live or unreaped child).
    var quiescence = "never_launched"
    /// The host's authority region setup for this actor: mapped, or the failure.
    var authorityRegion: String?
    var equipmentFailure: String? = nil
}

struct ActorVisitRecord {
    let phaseIndex: Int
    let actorIndex: Int
    let visit: Int
    var activationStored = false
    var activationObservation: PWRunnerActorActivation? = nil
    var arrivalObserved = false
    var collectionInvoked = false
    var collectionClosed = false
    var releaseStored = false
    var acknowledgementObserved = false
    var completionObserved = false
    var violations: [String] = []
    /// completed, or the first failure that ended the visit.
    var endReason = "not_reached"
    /// Host-measured intervals on the monotonic clock, in milliseconds; nil
    /// when the boundary was not reached or the clock was unusable. The
    /// collection interval is excluded from the schedule allowance.
    var activationToArrivalMs: UInt64?
    var collectionMs: UInt64?
    var arrivalToReleaseMs: UInt64?
    var releaseToCompletionMs: UInt64?
    var terminationGate: ActorTerminationGateRecord? = nil
}

struct ActorScheduleOutcome {
    var actors: [ActorSessionRecord]
    var visits: [ActorVisitRecord]
    var lifetimeCutoffTicks: UInt64
    var setupWait: PWHostWait?
    var executionWait: PWHostWait?
    /// Set once the remaining schedule was cancelled, with the reason.
    var cancelled: String?
    /// Host custody and transfer observations, in the order they were serviced.
    var custody: [CustodyObservation] = []
    var transfers: [TransferObservation] = []
    var authoritySetup: PWRunnerAuthoritySetup? = nil
}

/// Collection against the active actor: global phase index, actor index and
/// the live process. Runs while every other actor is parked.
typealias ActorCollectionHook = (_ phaseIndex: Int, _ actorIndex: Int, _ pid: pid_t) -> Void

final class ActorScheduler {
    let input: ActorScheduleInput
    let calls: ChildProcessCalls
    private(set) var sessions: [ActorSession?]
    private(set) var records: [ActorSessionRecord]
    private(set) var visits: [ActorVisitRecord] = []
    private var stopped: [Bool]
    private var cancelled: String?
    private var setupStartedNs: UInt64?
    private var setupDeadlineNs: UInt64?
    let lifetimeCutoffTicks: UInt64
    private(set) var custody: AuthorityCustody?

    init(_ input: ActorScheduleInput, processCalls: ChildProcessCalls = ChildProcessCalls()) {
        self.input = input
        self.calls = processCalls
        sessions = input.actors.map { _ in nil }
        records = input.actors.indices.map { ActorSessionRecord(index: $0) }
        stopped = input.actors.map { _ in false }
        lifetimeCutoffTicks = ActorScheduler.continuousCutoff(afterMs: input.lifetimeMs)
    }

    /// The absolute continuous-clock reading `ms` from now, in the raw units
    /// the worker compares against its own origin sample.
    static func continuousCutoff(afterMs ms: Int) -> UInt64 {
        var info = mach_timebase_info_data_t()
        mach_timebase_info(&info)
        let ns = UInt64(max(0, ms)) * 1_000_000
        let ticks = ns.multipliedReportingOverflow(by: UInt64(info.denom)).partialValue / UInt64(max(1, info.numer))
        let now = mach_continuous_time()
        return now > UInt64.max - ticks ? UInt64.max : now + ticks
    }

    static func run(_ input: ActorScheduleInput, processCalls: ChildProcessCalls = ChildProcessCalls(),
                    collect: ActorCollectionHook) -> ActorScheduleOutcome {
        let scheduler = ActorScheduler(input, processCalls: processCalls)
        return scheduler.run(collect: collect)
    }

    func run(collect: ActorCollectionHook) -> ActorScheduleOutcome {
        var setupWait = launchAndSetUp()
        // Inspect only usable, still-owned live workers. An inspection refusal is
        // an equipment failure, not a rewrite of the worker's setup publication.
        if let inspect=input.didSetUp {
            for index in sessions.indices where records[index].setupStatus.usable {
                guard let session=sessions[index] else { continue }
                if let before=calls.clock(),let start=setupStartedNs,let end=setupDeadlineNs,before>=start {
                    if before>=end { records[index].equipmentFailure="inspection_deadline" }
                    else if session.waitChild(stage:"equipment_inspection") != .pending {
                        records[index].equipmentFailure=session.ownershipUnbroken ? "process_unavailable":"ownership_unresolved"
                    } else {
                        records[index].equipmentFailure=inspect(index,session.pid)
                        if let after=calls.clock(),after>=before {
                            if after>=end && records[index].equipmentFailure==nil { records[index].equipmentFailure="inspection_deadline" }
                        } else if records[index].equipmentFailure==nil { records[index].equipmentFailure="inspection_deadline" }
                    }
                } else { records[index].equipmentFailure="inspection_deadline" }
                if let failure=records[index].equipmentFailure,cancelled==nil { cancelled="equipment_execution_"+failure }
            }
            if let finish=calls.clock(),let start=setupStartedNs,finish>=start { setupWait.elapsed_ms=(finish-start)/1_000_000 }
            else { setupWait.elapsed_ms=nil;setupWait.clock_fault=true }
            if records.contains(where:{$0.equipmentFailure != nil}) { setupWait.stop="equipment_inspection_failed" }
        }
        let executionWait = walkSchedule(collect: collect)
        finish()
        return ActorScheduleOutcome(actors: records, visits: visits, lifetimeCutoffTicks: lifetimeCutoffTicks,
                                    setupWait: setupWait, executionWait: executionWait, cancelled: cancelled,
                                    custody: custody?.custody ?? [], transfers: custody?.transfers ?? [],
                                    authoritySetup: PWRunnerAuthoritySetup(
                                        host:custody?.setupObservation ?? PWRunnerAuthorityHost(run:PWRunnerAuthorityScope(disposition:"not_required")),
                                        workers:records.map { record in
                                            record.output?.authoritySetup ?? PWRunnerAuthorityScope(actor_index:record.index,
                                                required:input.authority != nil,publication:"not_observed",ownership:["descriptor":"not_acquired","mapping":"not_acquired","shared_erasure":"not_present"])
                                        }))
    }

    // MARK: - Setup

    /// Launch every actor in order under one allowance, then await each
    /// actor's own setup publication. A refused or failed actor never stops
    /// the others from launching.
    private func launchAndSetUp() -> PWHostWait {
        var clock = HostWaitClock(milliseconds: input.setupAllowanceMs, pollNs: 1_000_000, calls: calls)
        setupStartedNs=clock.started
        setupDeadlineNs=clock.started.map { $0 > UInt64.max-clock.budgetNs ? UInt64.max:$0+clock.budgetNs }

        // Every authority region and custody buffer exists before the first
        // launch, with core dumps disabled in this host first.
        if let plan = input.authority {
            let custody = AuthorityCustody(plan: plan, actorCount: input.actors.count, calls: calls)
            self.custody = custody
            for index in input.actors.indices { records[index].authorityRegion = custody.regionStatus(for: index) }
            if let failure = custody.setupFailure {
                for index in input.actors.indices {
                    records[index].setupStatus = .launchRefused
                    records[index].launchFailure = .shmSetupFailed("authority setup: " + failure)
                }
                return clock.record(stop: "setup_failed")
            }
        }
        var pending = Set<Int>()
        for index in input.actors.indices {
            if cancelled != nil { break }
            if (clock.remainingNs() ?? 0) < 1_000_000 {
                records[index].setupStatus = .setupTimeout
                continue
            }
            var actorInput = input.actors[index]
            actorInput.actorIndex = UInt32(index)
            actorInput.actorMode = input.applies[index] ? 1 : 2
            actorInput.lifetimeCutoffTicks = lifetimeCutoffTicks
            actorInput.authorityFD = custody?.descriptor(for: index)
            actorInput.authorityRequired = input.authority != nil
            actorInput.authorityRecorder = custody?.recorder(for:index)
            let session = ActorSession(actorInput, processCalls: calls,
                setupRemainingMs: { Int((clock.remainingNs() ?? 0) / 1_000_000) })
            custody?.closeDescriptor(for: index)
            guard session.spawned else {
                session.tearDown()
                records[index].setupStatus = .launchRefused
                records[index].launchFailure = session.failure
                continue
            }
            sessions[index] = session
            records[index].pid = session.pid
            records[index].quiescence = "unresolved"
            if let failure = session.transferFailure {
                records[index].setupStatus = .transferFailed
                records[index].launchFailure = failure
                stopActor(index, reason: session.pollStopReason)
                continue
            }
            pending.insert(index)
        }
        var stop = "all_resolved"
        while !pending.isEmpty {
            for index in pending.sorted() {
                guard let session = sessions[index] else { pending.remove(index); continue }
                if let status = setupDisposition(session) {
                    records[index].setupStatus = status
                    if status == .applied { records[index].applicationCount = 1 }
                    if session.actorSetup != 0 && (session.authorityStatus >= 3
                        || (session.input.authorityFD != nil && session.authorityStatus != 1)) {
                        records[index].setupStatus = .setupFailed
                        records[index].launchFailure = .shmSetupFailed("worker authority setup: status=\(session.authorityStatus) detail=\(session.authorityDetail)")
                    }
                    if !records[index].setupStatus.usable { stopActor(index, reason: records[index].setupStatus.rawValue) }
                    pending.remove(index)
                }
            }
            if pending.isEmpty { break }
            if clock.expiredAfterSleeping() {
                stop = "deadline"
                for index in pending.sorted() {
                    records[index].setupStatus = .setupTimeout
                    stopActor(index, reason: ActorSetupStatus.setupTimeout.rawValue)
                }
                pending.removeAll()
            }
        }
        return clock.record(stop: stop)
    }

    /// The worker's own setup publication, or nil while it is still pending.
    private func setupDisposition(_ session: ActorSession) -> ActorSetupStatus? {
        guard session.identityMatches else { return nil }
        let authority=session.authoritySetupObservation
        if authority.integrity_errors != nil { return .setupFailed }
        if authority.disposition=="terminal_required_failure" { return .authoritySetupFailed }
        switch session.actorSetup {
        case 1:
            return session.appliedObserved && session.applyRCIsZero ? .applied : .setupFailed
        case 2:
            return session.appliedObserved ? .setupFailed : .unappliedDeclared
        default:
            if session.doneObserved { return .setupFailed }
            switch session.waitChild(stage: "setup") {
            case .reaped: return .exitedBeforeSetup
            case .failed: return .exitedBeforeSetup
            case .pending: return nil
            }
        }
    }

    // MARK: - Schedule

    private func walkSchedule(collect: ActorCollectionHook) -> PWHostWait {
        var clock = HostWaitClock(milliseconds: input.executionAllowanceMs, pollNs: 1_000_000, calls: calls)
        var stop = "schedule_complete"
        for entry in input.schedule {
            var visit = ActorVisitRecord(phaseIndex: entry.phaseIndex, actorIndex: entry.actorIndex, visit: entry.visit)
            if let dependency=entry.terminationDependency {
                visit.terminationGate=ActorTerminationGateRecord(sourceActorIndex:dependency.sourceActorIndex,
                    sourceFinalPhaseIndex:dependency.sourceFinalPhaseIndex)
            }
            defer { visits.append(visit) }
            if let cancelled {
                visit.endReason = "cancelled:" + cancelled
                continue
            }
            if (clock.remainingNs() ?? 0) == 0 {
                cancelled = "execution_allowance_exhausted"
                stop = "deadline"
                visit.endReason = "cancelled:execution_allowance_exhausted"
                continue
            }
            guard let session = sessions[entry.actorIndex],
                  records[entry.actorIndex].setupStatus.usable, !stopped[entry.actorIndex] else {
                visit.endReason = "actor_unavailable"
                continue
            }
            let index = entry.visit
            guard session.phaseOutputs.indices.contains(index) else {
                visit.endReason = "visit_out_of_range"
                continue
            }
            if let dependency=entry.terminationDependency {
                var gate=observeTermination(dependency,remainingMs:Int((clock.remainingNs() ?? 0)/1_000_000))
                gate.activationEligible=gate.outcome=="satisfied"
                visit.terminationGate=gate
                if !gate.activationEligible {
                    visit.endReason="termination_dependency:"+gate.outcome
                    cancelled=visit.endReason
                    stop="dependency_failed"
                    continue
                }
            }
            visit.activationObservation=session.activate(globalPhase: UInt32(entry.phaseIndex + 1))
            visit.activationStored = true
            // The first wait after each host store (this activation, then the
            // release) re-samples the actor's answer before it sleeps.
            var resampleArrival = true
            var resampleCompletion = false
            let activatedAt = calls.clock()
            var arrivedAt: UInt64? = nil
            var releasedAt: UInt64? = nil
            func millis(_ from: UInt64?, _ to: UInt64?) -> UInt64? {
                guard let from, let to, to >= from else { return nil }
                return (to - from) / 1_000_000
            }

            var reason: String? = nil
            let recipientUsable: (Int) -> Bool = { [self] actor in
                guard let candidate = sessions[actor], records[actor].setupStatus.usable, !stopped[actor] else { return false }
                return !candidate.doneObserved
            }
            // ---- Arrival: the activated actor publishes arrival; nothing of it
            // ran meanwhile. Any other terminal state ends the visit.
            while reason == nil {
                if session.arrived(index) { break }
                if session.doneObserved { reason = "ended_before_arrival"; break }
                switch session.waitChild(stage: "schedule") {
                case .reaped: reason = "died_before_arrival"
                case .failed: reason = "wait_error"
                case .pending: break
                }
                if reason == nil && resampleArrival {
                    resampleArrival = false
                    if clock.expiredAfterResampling({ session.arrived(index) }, budgetNs: HostWaitClock.resampleBudgetNs) { reason = "arrival_timeout" }
                    continue
                }
                if reason == nil && clock.expiredAfterSleeping() { reason = "arrival_timeout" }
            }
            if reason == nil {
                arrivedAt = calls.clock()
                visit.activationToArrivalMs = millis(activatedAt, arrivedAt)
                visit.arrivalObserved = true
                session.phaseOutputs[index].arrived = true
                session.checkPrematurePublication(index)
                session.observeAcknowledgement()
                if index > 0 && !session.completed(index - 1) {
                    session.phaseOutputs[index].violations.append("arrival_without_previous_completion")
                }
                if session.completed(index) {
                    session.phaseOutputs[index].violations.append("completion_before_release")
                }
                if !session.phaseOutputs[index].violations.isEmpty { reason = "protocol_violation" }
            }
            if reason == nil {
                switch session.waitChild(stage: "schedule") {
                case .reaped: reason = "died_before_collection"
                case .failed: reason = "wait_error"
                case .pending: break
                }
            }
            if reason == nil {
                // ---- Collection against the live, parked-at-arrival actor. Its
                // duration is excluded from the execution allowance.
                let mark = clock.mark()
                let collectionStarted = calls.clock()
                visit.collectionInvoked = true
                collect(entry.phaseIndex, entry.actorIndex, session.pid)
                clock.excludeSince(mark)
                visit.collectionMs = millis(collectionStarted, calls.clock())
                session.phaseOutputs[index].collectionClosed = true
                visit.collectionClosed = true
                session.checkPrematurePublication(index)
                switch session.waitChild(stage: "schedule") {
                case .reaped: reason = "died_during_collection"
                case .failed: reason = "wait_error"
                case .pending: break
                }
            }
            if reason == nil {
                // ---- Release: recheck ownership, arrival and order before the store.
                if (clock.remainingNs() ?? 0) == 0 { reason = "completion_timeout" }
                else if !session.doneObserved && session.arrived(index) && !session.acknowledged(index)
                    && !session.completed(index) && (index == 0 || session.completed(index - 1))
                    && session.phaseOutputs[index].violations.isEmpty {
                    session.releaseVisit(index)
                    resampleCompletion = true
                    visit.releaseStored = true
                    releasedAt = calls.clock()
                    visit.arrivalToReleaseMs = millis(arrivedAt, releasedAt)
                } else {
                    reason = "release_withheld"
                }
            }
            while reason == nil {
                session.observeAcknowledgement()
                // The active actor may publish an issued token or a transfer
                // request while it runs; the host services them here.
                let remainingMs = Int((clock.remainingNs() ?? 0) / 1_000_000)
                if remainingMs == 0 { reason = "completion_timeout"; break }
                custody?.service(active: entry.actorIndex, phaseIndex: entry.phaseIndex,
                                 waitAllowanceMs: remainingMs, recipientUsable: recipientUsable)
                if session.completed(index) { break }
                if session.doneObserved { reason = "ended_before_completion"; break }
                switch session.waitChild(stage: "schedule") {
                case .reaped: reason = "died_before_completion"
                case .failed: reason = "wait_error"
                case .pending: break
                }
                if reason == nil && resampleCompletion {
                    resampleCompletion = false
                    if clock.expiredAfterResampling({ session.completed(index) }, budgetNs: HostWaitClock.resampleBudgetNs) { reason = "completion_timeout" }
                    continue
                }
                if reason == nil && clock.expiredAfterSleeping() { reason = "completion_timeout" }
            }
            session.observeAcknowledgement()
            visit.acknowledgementObserved = session.acknowledged(index)
            visit.completionObserved = session.completed(index)
            if visit.completionObserved { visit.releaseToCompletionMs = millis(releasedAt, calls.clock()) }
            visit.violations = session.phaseOutputs[index].violations
            guard let failure = reason else {
                visit.endReason = "completed"
                continue
            }
            visit.endReason = failure
            // The active actor failed: establish that it cannot run further
            // actions before any other actor is activated.
            stopActor(entry.actorIndex, reason: failure)
            if records[entry.actorIndex].quiescence != "reaped" {
                cancelled = "unresolved_termination"
            } else if failure == "arrival_timeout" || failure == "completion_timeout" {
                cancelled = "execution_allowance_exhausted"
                stop = "deadline"
            } else if failure == "wait_error" {
                cancelled = "ownership_lost"
            }
        }
        return clock.record(stop: stop, excluded: true)
    }

    /// Natural owned termination only. This method never requests departure.
    private func observeTermination(_ dependency: ActorTerminationDependency, remainingMs: Int) -> ActorTerminationGateRecord {
        var result=ActorTerminationGateRecord(sourceActorIndex:dependency.sourceActorIndex,sourceFinalPhaseIndex:dependency.sourceFinalPhaseIndex)
        let budget=min(PWActorLimits.terminationMs,max(0,remainingMs))
        var wait=HostWaitClock(milliseconds:budget,pollNs:1_000_000,calls:calls)
        let deadline=MonotonicDeadline(milliseconds:budget,clock:calls.clock)
        let source=sessions.indices.contains(dependency.sourceActorIndex) ? sessions[dependency.sourceActorIndex]:nil
        var lastRemaining: UInt64? = nil
        func sample() -> UInt64? {
            guard let value=deadline.sample()?.remaining else { return nil }
            if let previous=lastRemaining,value>previous { return nil }
            lastRemaining=value;return value
        }
        func finish(_ reason:String)->ActorTerminationGateRecord {
            result.outcome=reason;result.wait=wait.record(stop:reason)
            result.captureOrdinal=source?.process.nextCaptureOrdinal()
            if reason=="satisfied" {
                if result.wait?.clock_fault==true || result.wait?.elapsed_ms==nil {
                    result.outcome="clock_unavailable"
                } else if let elapsed=result.wait?.elapsed_ms, elapsed>UInt64(max(0,budget)) {
                    result.outcome="timed_out"
                }
                let terminalOutcome=result.outcome
                result.wait?.stop=terminalOutcome
            }
            return result
        }
        guard let source,
              let activation=visits.first(where:{$0.phaseIndex==dependency.sourceFinalPhaseIndex && $0.actorIndex==dependency.sourceActorIndex && $0.activationStored})?.activationObservation else {
            return finish("source_unavailable")
        }
        guard budget>0 else { return finish("execution_allowance_exhausted") }
        while true {
            guard let before=sample() else { return finish("clock_unavailable") }
            if before==0 { return finish("timed_out") }
            guard source.ownershipUnbroken && source.process.ownershipUnbroken else { return finish("ownership_lost") }
            if source.process.ownedReap == nil && source.process.departureRequested { return finish("source_departure_requested") }
            let observation=source.waitChild(stage:"termination_gate")
            // A late native reap remains a fact but cannot reopen this gate.
            result.observation=source.process.ownedReap
            guard let after=sample() else { return finish("clock_unavailable") }
            if after==0 { return finish("timed_out") }
            switch observation {
            case .failed: return finish("ownership_lost")
            case .reaped:
                guard let reaped=result.observation, reaped.ownership_unbroken else { return finish("ownership_lost") }
                if reaped.departure_requested { return finish("source_departure_requested") }
                guard let reapedAt=reaped.observed_ns,let activatedAt=activation.observed_ns else { return finish("clock_unavailable") }
                guard reaped.capture_ordinal>activation.capture_ordinal && reapedAt>=activatedAt else { return finish("source_unavailable") }
                return finish("satisfied")
            case .pending: break
            }
            if wait.expiredAfterSleeping() { return finish("timed_out") }
        }
    }

    // MARK: - Termination

    /// Request exit, grace, kill if needed and reap one actor; record how
    /// that ended. Idempotent.
    private func stopActor(_ index: Int, reason: String) {
        guard let session = sessions[index], !stopped[index] else { return }
        stopped[index] = true
        records[index].stopReason = reason
        session.pollStopReason = reason
        session.requestExit()
        session.finishCleanup()
        records[index].quiescence = session.process.status != nil ? "reaped" : "unresolved"
        if records[index].quiescence == "unresolved" { cancelled = "actor_quiescence_unresolved" }
    }

    /// Stop every remaining actor, collect each output and release host resources.
    private func finish() {
        for index in sessions.indices {
            guard let session = sessions[index] else { continue }
            if !stopped[index] {
                stopped[index] = true
                session.pollStopReason = session.doneObserved ? "done" : "schedule_complete"
                session.requestExit()
                session.finishCleanup()
                records[index].quiescence = session.process.status != nil ? "reaped" : "unresolved"
            }
            let output = session.collectOutput()
            records[index].output = output
            if records[index].setupStatus == .transferFailed && output.authoritySetup?.disposition == "terminal_required_failure" {
                records[index].setupStatus = .authoritySetupFailed
            }
            // A setup deadline controls eligibility, not whether a later
            // application publication is an observed native fact.
            records[index].applicationCount = output.applied ? 1 : 0
            session.tearDown()
        }
        // Workers are stopped and reaped (or recorded unresolved) before the host
        // erases its custody and unmaps every region.
        custody?.recordSourceAcknowledgements(records.map { $0.output })
        custody?.finish(quiescentActors: Set(records.filter {
            $0.quiescence == "reaped" || $0.pid == nil
        }.map { $0.index }))
    }
}
