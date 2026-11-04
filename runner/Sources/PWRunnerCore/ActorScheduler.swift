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
}

/// Why one actor's setup ended, decided from its own publications.
enum ActorSetupStatus: String {
    case notLaunched = "not_launched"
    case launchRefused = "launch_refused"
    case transferFailed = "transfer_failed"
    case applied = "applied"
    case unappliedDeclared = "unapplied_declared"
    case setupFailed = "setup_failed"
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
}

struct ActorVisitRecord {
    let phaseIndex: Int
    let actorIndex: Int
    let visit: Int
    var activationStored = false
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
        let setupWait = launchAndSetUp()
        let executionWait = walkSchedule(collect: collect)
        finish()
        return ActorScheduleOutcome(actors: records, visits: visits, lifetimeCutoffTicks: lifetimeCutoffTicks,
                                    setupWait: setupWait, executionWait: executionWait, cancelled: cancelled,
                                    custody: custody?.custody ?? [], transfers: custody?.transfers ?? [])
    }

    // MARK: - Setup

    /// Launch every actor in order under one allowance, then await each
    /// actor's own setup publication. A refused or failed actor never stops
    /// the others from launching.
    private func launchAndSetUp() -> PWHostWait {
        var clock = HostWaitClock(milliseconds: input.setupAllowanceMs, pollNs: 1_000_000, calls: calls)
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
            let session = ActorSession(actorInput, processCalls: calls,
                setupRemainingMs: { Int((clock.remainingNs() ?? 0) / 1_000_000) })
            custody?.closeDescriptor(for: index)
            guard session.spawned else {
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
            session.activate(globalPhase: UInt32(entry.phaseIndex + 1))
            visit.activationStored = true
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
