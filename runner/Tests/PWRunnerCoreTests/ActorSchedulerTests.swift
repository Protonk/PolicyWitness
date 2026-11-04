import Darwin
import Foundation
@testable import PWRunnerCore

/*
 * ActorSchedulerTests — the actor scheduler against the bundled worker and
 * validator. Each case launches real processes: distinct policies reach
 * distinct, identified processes and each applies once; repeated visits keep
 * those identities; parked actors are quiescent; a failed setup, a death and a
 * lost validator leave the other actors' evidence intact; the shared cutoff
 * ends parked waits with published failures.
 *
 * Independent observations here come from the kernel (sysctl process table,
 * kill(pid, 0)), from sb_api_validator against the active PID and from the
 * other sessions' own publications, not from the scheduler's labels.
 */

private func equipment(_ name: String) -> String {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent()
    let app = ProcessInfo.processInfo.environment["PW_APP_DIR"] ?? root.appendingPathComponent("dist/PolicyWitness.app").path
    return app + "/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/" + name
}

private let hosts = "/private/etc/hosts"
private let passwd = "/private/etc/passwd"
private let allowAll = "(version 1)(allow default)"
private func denyRead(_ path: String) -> String { "(version 1)(allow default)(deny file-read* (literal \"\(path)\"))" }

private func read(_ id: String, _ target: String) -> CWorkerSlotInput {
    CWorkerSlotInput(stepId: id, attemptKind: .fileOpenRead, target: target)
}

/// One actor's driver input from its visits: each visit names its global phase
/// index and carries its own slots, in schedule order.
private func actorInput(policy: String, visits: [(phase: Int, slots: [CWorkerSlotInput])],
                        killBeforePublishSlot: Int? = nil) -> CWorkerInput {
    var slots: [CWorkerSlotInput] = []
    var phases: [CWorkerPhaseInput] = []
    for visit in visits {
        phases.append(CWorkerPhaseInput(firstSlot: slots.count, endSlot: slots.count + visit.slots.count, globalPhase: visit.phase + 1))
        slots += visit.slots
    }
    var input = CWorkerInput(workerExecutablePath: equipment("pw-probe-runner"), policy: policy, slots: slots, phases: phases,
                             sentinelTimeoutMs: 10_000, killBeforePublishSlot: killBeforePublishSlot)
    input.proceedWaitMs = 5_000
    return input
}

/// The global schedule from the actors' visit lists.
private func schedule(_ visits: [[Int]]) -> [ActorScheduleEntry] {
    var entries: [ActorScheduleEntry] = []
    for (actor, phases) in visits.enumerated() {
        for (visit, phase) in phases.enumerated() { entries.append(ActorScheduleEntry(phaseIndex: phase, actorIndex: actor, visit: visit)) }
    }
    return entries.sorted { $0.phaseIndex < $1.phaseIndex }
}

private func parentPid(of pid: pid_t) -> pid_t? {
    var info = kinfo_proc()
    var size = MemoryLayout<kinfo_proc>.stride
    var mib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, pid]
    guard sysctl(&mib, UInt32(mib.count), &info, &size, nil, 0) == 0, size > 0 else { return nil }
    return info.kp_eproc.e_ppid
}

private func verdicts(pid: pid_t, validator: String = equipment("sb_api_validator")) -> [String: String] {
    let probes = [ValidatorProbe(stepId: "hosts", operation: "file-read-data", filterType: "PATH", filterValue: hosts),
                  ValidatorProbe(stepId: "passwd", operation: "file-read-data", filterType: "PATH", filterValue: passwd)]
    let result = runValidator(ValidatorClientInput(executablePath: validator, targetPid: pid, probes: probes, verdictReadTimeoutMs: 5_000))
    guard case .success(let output) = result else { return [:] }
    return Dictionary(uniqueKeysWithValues: output.verdicts.compactMap { v in v.stepId.map { ($0, v.outcome) } })
}

private func denied(_ slot: CWorkerSlotResult) -> Bool { slot.completed && slot.rc != 0 && [EPERM, EACCES].contains(slot.errnoVal) }
private func readOK(_ slot: CWorkerSlotResult) -> Bool { slot.completed && slot.rc == 0 }

@_silgen_name("proc_pidinfo")
private func actorProcInfo(_ pid: Int32, _ flavor: Int32, _ arg: UInt64, _ buffer: UnsafeMutableRawPointer, _ size: Int32) -> Int32

private func actorDescriptors(_ pid: pid_t) throws -> Set<Int32> {
    // PROC_PIDLISTFDS = 1; each proc_fdinfo is int32 fd + uint32 fdtype.
    var entries = [Int32](repeating: -1, count: 1024)
    let bytes = entries.withUnsafeMutableBytes { actorProcInfo(pid, 1, 0, $0.baseAddress!, Int32($0.count)) }
    guard bytes > 0, bytes < entries.count * 4, bytes % 8 == 0 else { throw TestFailure(message: "proc_pidinfo fd inventory failed: \(bytes), errno \(errno)") }
    return Set(stride(from: 0, to: Int(bytes) / 4, by: 2).map { entries[$0] })
}

func runActorSchedulerTests(_ tk: TestKit) {
    let workerPresent = FileManager.default.isExecutableFile(atPath: equipment("pw-probe-runner"))
    tk.group("actor scheduler: owned sessions and the serial schedule") {
        tk.run("actor launch excludes an inheritable host descriptor and original evidence endpoints") {
            let fd = open("/dev/null", O_RDONLY)
            try expectTrue(fd >= 0)
            defer { close(fd) }
            let sentinel = fcntl(fd, F_DUPFD, 97)
            try expectTrue(sentinel >= 97)
            defer { close(sentinel) }
            try expectEqual(fcntl(sentinel, F_SETFD, 0), 0)
            // Force an acquisition into a standard-stream position as well.
            // Launch must preserve source identity despite its dup2 targets.
            let savedStdin = fcntl(STDIN_FILENO, F_DUPFD_CLOEXEC, 100)
            try expectTrue(savedStdin >= 0)
            close(STDIN_FILENO)
            defer { _ = dup2(savedStdin, STDIN_FILENO); close(savedStdin) }
            let inputs = [actorInput(policy: allowAll, visits: [(0, [read("a", hosts)])]),
                          actorInput(policy: allowAll, visits: [(1, [read("b", hosts)])])]
            var inventories: [Set<Int32>] = []
            var failure: Error?
            let result = ActorScheduler.run(ActorScheduleInput(actors: inputs, applies: [true, true], schedule: schedule([[0], [1]]))) { _, _, pid in
                do { inventories.append(try actorDescriptors(pid)) } catch { failure = error }
            }
            if let failure { throw failure }
            try expectEqual(result.visits.map { $0.endReason }, ["completed", "completed"])
            try expectEqual(inventories, [Set<Int32>(0...4), Set<Int32>(0...4)])
        }
        tk.run("an exhausted execution allowance never activates an already prepared actor") {
            var input = ActorScheduleInput(actors: [actorInput(policy: allowAll, visits: [(0, [read("a", hosts)])])],
                applies: [false], schedule: schedule([[0]]))
            input.executionAllowanceMs = 0
            var collected = false
            let result = ActorScheduler.run(input) { _, _, _ in collected = true }
            try expectFalse(collected)
            try expectEqual(result.cancelled, "execution_allowance_exhausted")
            try expectFalse(result.visits[0].activationStored)
            try expectEqual(result.actors[0].output?.slots[0].completed, false)
            try expectEqual(result.actors[0].quiescence, "reaped")
        }
        tk.run("setup expiry retains an application published during cleanup without making setup usable") {
            var actor = actorInput(policy: allowAll, visits: [(0, [read("late", hosts)])])
            actor.preReadyHangMs = 150
            actor.exitGraceMs = 1_000
            var input = ActorScheduleInput(actors: [actor], applies: [true], schedule: schedule([[0]]))
            input.setupAllowanceMs = 40
            var collected = false
            let result = ActorScheduler.run(input) { _, _, _ in collected = true }
            let record = result.actors[0]
            try expectEqual(record.setupStatus, .setupTimeout)
            try expectTrue(record.output?.applied == true, "native worker must finish its delayed apply during grace")
            try expectEqual(record.applicationCount, 1, "final application publication must survive setup expiry")
            try expectFalse(collected)
            try expectFalse(result.visits[0].activationStored)
            try expectEqual(record.output?.slots[0].completed, false)
            try expectEqual(record.quiescence, "reaped")
            try expectEqual(record.output?.readyWait?.stop, "deadline")
            try expectTrue((record.output?.readyWait?.budget_ms ?? Int.max) <= 40)
        }
        tk.run("collection is excluded once but post-collection work can exhaust the release allowance") {
            var offset: UInt64 = 0
            var chargeAfterCollection = false
            var charged = false
            var calls = ChildProcessCalls()
            calls.clock = { MonotonicDeadline.now().map { $0 + offset } }
            calls.wait = { pid, status, options in
                let rc = Darwin.waitpid(pid, status, options)
                if chargeAfterCollection && !charged {
                    offset += 400_000_000
                    charged = true
                }
                return rc
            }
            var input = ActorScheduleInput(actors: [actorInput(policy: allowAll, visits: [(0, [read("held", hosts)])])],
                applies: [true], schedule: schedule([[0]]))
            input.executionAllowanceMs = 400
            let result = ActorScheduler.run(input, processCalls: calls) { _, _, _ in
                offset += 1_000_000_000
                chargeAfterCollection = true
            }
            try expectTrue(charged)
            try expectTrue(result.visits[0].collectionClosed)
            try expectFalse(result.visits[0].releaseStored)
            try expectEqual(result.cancelled, "execution_allowance_exhausted")
            try expectEqual(result.actors[0].output?.slots[0].completed, false)
            try expectTrue((result.executionWait?.excluded_ms ?? 0) >= 1_000)
            let elapsed = result.executionWait?.elapsed_ms ?? 0
            let excluded = result.executionWait?.excluded_ms ?? UInt64.max
            try expectTrue(elapsed >= excluded && elapsed - excluded >= 400)
        }
        tk.run("lost ownership cancels later activations and never invents confirmed cleanup") {
            var faultPid: pid_t?
            var signalled: [pid_t] = []
            var independentlyReaped = false
            defer {
                // The fault adapter withholds the native wait, so this fixture
                // still owns the actual child and must settle it independently.
                if let pid = faultPid, !independentlyReaped {
                    _ = Darwin.kill(pid, SIGKILL)
                    var status: Int32 = 0
                    while Darwin.waitpid(pid, &status, 0) < 0 && errno == EINTR {}
                }
            }
            var calls = ChildProcessCalls()
            calls.wait = { pid, status, options in
                if faultPid == pid { errno = ECHILD; return -1 }
                return Darwin.waitpid(pid, status, options)
            }
            calls.kill = { pid, signal in signalled.append(pid); return Darwin.kill(pid, signal) }
            let input = ActorScheduleInput(
                actors: [actorInput(policy: allowAll, visits: [(0, [read("a", hosts)])]),
                         actorInput(policy: allowAll, visits: [(1, [read("b", hosts)])])],
                applies: [true, true], schedule: schedule([[0], [1]]))
            var collections: [Int] = []
            let result = ActorScheduler.run(input, processCalls: calls) { phase, _, pid in
                collections.append(phase)
                if phase == 0 { faultPid = pid }
            }
            try expectEqual(collections, [0])
            try expectEqual(result.actors[0].quiescence, "unresolved")
            try expectFalse(result.visits[0].releaseStored)
            try expectFalse(result.visits[1].activationStored)
            try expectTrue(result.cancelled != nil)
            try expectEqual(result.actors[0].output?.collectionBasis, "execution_may_continue")
            try expectFalse(signalled.contains(faultPid!))
            try expectTrue(result.actors.allSatisfy { $0.output?.slots[0].completed == false })
            var status: Int32 = 0
            var rc: pid_t
            repeat { rc = Darwin.waitpid(faultPid!, &status, 0) } while rc < 0 && errno == EINTR
            independentlyReaped = rc == faultPid
            try expectTrue(independentlyReaped, "fixture must independently reap the child hidden by ECHILD")
            try expectEqual(result.actors[0].quiescence, "unresolved", "later fixture cleanup cannot upgrade the retained result")
        }
        tk.run("two policies reach two identified processes, each applied once, across repeated visits") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let both = [read("hosts", hosts), read("passwd", passwd)]
            let input = ActorScheduleInput(
                actors: [actorInput(policy: denyRead(hosts), visits: [(0, both), (2, both)]),
                         actorInput(policy: denyRead(passwd), visits: [(1, both), (3, both)])],
                applies: [true, true], schedule: schedule([[0, 2], [1, 3]]))
            let scheduler = ActorScheduler(input)
            var observed: [(phase: Int, actor: Int, pid: pid_t, parent: pid_t?, verdicts: [String: String],
                            otherAlive: Bool, otherCompleted: Int, otherArrivedNext: Bool, otherActivation: UInt32)] = []
            let outcome = scheduler.run { phase, actor, pid in
                let other = scheduler.sessions[1 - actor]!
                // The parked actor's next visit: B's first, A's second, B's second,
                // and none for A once its visits are spent.
                let nextVisit: Int? = [0, 1, 1, nil][phase]
                observed.append((phase, actor, pid, parentPid(of: pid), verdicts(pid: pid),
                                 kill(other.pid, 0) == 0, other.completedSlotCount,
                                 nextVisit.map { other.arrived($0) } ?? false, other.activationObserved))
            }
            try expectNil(outcome.cancelled)
            try expectEqual(outcome.visits.map { $0.endReason }, ["completed", "completed", "completed", "completed"])
            try expectEqual(outcome.visits.map { $0.actorIndex }, [0, 1, 0, 1])
            try expectTrue(outcome.visits.allSatisfy { $0.activationStored && $0.arrivalObserved && $0.collectionClosed
                && $0.releaseStored && $0.acknowledgementObserved && $0.completionObserved && $0.violations.isEmpty })
            // Each actor: its own process, applied once, reaped after a clean exit.
            let a = outcome.actors[0], b = outcome.actors[1]
            try expectEqual([a.setupStatus, b.setupStatus], [.applied, .applied])
            try expectEqual([a.applicationCount, b.applicationCount], [1, 1])
            try expectTrue(a.pid != nil && b.pid != nil && a.pid != b.pid)
            try expectEqual([a.quiescence, b.quiescence], ["reaped", "reaped"])
            for record in [a, b] {
                guard let out = record.output else { throw TestFailure(message: "missing output for actor \(record.index)") }
                try expectTrue(out.applied && out.applyRC == 0 && out.done && out.exitCode == 0)
                try expectEqual(out.actorSetup, 1)
                try expectEqual(out.activationObserved, UInt32(record.index == 0 ? 3 : 4))
                try expectEqual(out.phases.map { $0.completed }, [true, true])
                try expectEqual(out.phases.map { $0.ownershipEstablished }, [true, true])
                try expectEqual(out.policyReceivedSha256, sha256Hex(Data(input.actors[record.index].policy.utf8)))
            }
            // The attempts: A's hosts reads denied and passwd readable on both visits; B the reverse.
            let aSlots = a.output!.slots, bSlots = b.output!.slots
            try expectTrue(denied(aSlots[0]) && readOK(aSlots[1]) && denied(aSlots[2]) && readOK(aSlots[3]), "\(aSlots.map { ($0.rc, $0.errnoVal) })")
            try expectTrue(readOK(bSlots[0]) && denied(bSlots[1]) && readOK(bSlots[2]) && denied(bSlots[3]), "\(bSlots.map { ($0.rc, $0.errnoVal) })")
            // Independent: the kernel's process table names this host as parent,
            // the validator's verdicts against the live PID follow that actor's
            // policy at every visit, and the parked actor stayed alive with no
            // new completion, no arrival for its next visit and no activation.
            try expectEqual(observed.count, 4)
            for (i, o) in observed.enumerated() {
                try expectEqual(o.phase, i)
                try expectEqual(o.pid, outcome.actors[o.actor].pid!)
                try expectEqual(o.parent, getpid())
                try expectEqual(o.verdicts["hosts"], o.actor == 0 ? "deny" : "allow", "phase \(i)")
                try expectEqual(o.verdicts["passwd"], o.actor == 0 ? "allow" : "deny", "phase \(i)")
                try expectTrue(o.otherAlive, "phase \(i): parked actor alive")
                // The parked actor holds exactly the completions of its own earlier visits.
                try expectEqual(o.otherCompleted, [0, 2, 2, 4][i], "phase \(i): parked actor completions")
                try expectFalse(o.otherArrivedNext, "phase \(i): parked actor arrival")
                // The parked actor's last accepted activation is its own last visit's ordinal.
                try expectEqual(o.otherActivation, UInt32(i), "phase \(i): parked actor activation")
            }
            try expectEqual(outcome.setupWait?.stop, "all_resolved")
            try expectEqual(outcome.executionWait?.stop, "schedule_complete")
        }
        tk.run("an unapplied actor declares itself, applies nothing and reads; an applied deny-default actor is denied") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let input = ActorScheduleInput(
                actors: [actorInput(policy: "", visits: [(0, [read("hosts", hosts)])]),
                         actorInput(policy: "(version 1)(deny default)", visits: [(1, [read("hosts", hosts)])])],
                applies: [false, true], schedule: schedule([[0], [1]]))
            let outcome = ActorScheduler.run(input) { _, _, _ in }
            try expectNil(outcome.cancelled)
            try expectEqual(outcome.visits.map { $0.endReason }, ["completed", "completed"])
            let a = outcome.actors[0], b = outcome.actors[1]
            try expectEqual(a.setupStatus, .unappliedDeclared)
            try expectEqual(a.applicationCount, 0)
            try expectTrue(a.output!.applied == false && a.output!.applyRC == 0 && a.output!.done)
            try expectEqual(a.output!.actorSetup, 2)
            try expectNil(a.output!.profileCapture)
            try expectTrue(readOK(a.output!.slots[0]))
            try expectEqual(a.output!.policyReceivedSha256, sha256Hex(Data()))
            try expectEqual(b.setupStatus, .applied)
            try expectTrue(b.output!.applied && denied(b.output!.slots[0]))
        }
        tk.run("a failed setup leaves the other actor's visits intact") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let input = ActorScheduleInput(
                actors: [actorInput(policy: "(version 1)(bogus", visits: [(0, [read("hosts", hosts)]), (2, [read("hosts", hosts)])]),
                         actorInput(policy: allowAll, visits: [(1, [read("hosts", hosts)]), (3, [read("passwd", passwd)])])],
                applies: [true, true], schedule: schedule([[0, 2], [1, 3]]))
            let outcome = ActorScheduler.run(input) { _, _, _ in }
            try expectNil(outcome.cancelled)
            try expectEqual(outcome.visits.map { $0.endReason }, ["actor_unavailable", "completed", "actor_unavailable", "completed"])
            let a = outcome.actors[0], b = outcome.actors[1]
            try expectEqual(a.setupStatus, .setupFailed)
            try expectEqual(a.applicationCount, 0)
            try expectEqual(a.quiescence, "reaped")
            try expectEqual(a.stopReason, "setup_failed")
            try expectTrue(a.output!.done && !a.output!.applied && a.output!.applyRC == -1)
            try expectEqual(a.output!.actorSetup, 0)
            try expectTrue(a.output!.slots.allSatisfy { !$0.completed })
            try expectEqual(b.setupStatus, .applied)
            try expectTrue(b.output!.slots.allSatisfy(readOK))
            try expectEqual(b.output!.phases.map { $0.completed }, [true, true])
        }
        tk.run("the active actor's death is established before the next activation; later actors continue") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let input = ActorScheduleInput(
                actors: [actorInput(policy: allowAll, visits: [(0, [read("hosts", hosts)]), (2, [read("hosts", hosts)])], killBeforePublishSlot: 0),
                         actorInput(policy: allowAll, visits: [(1, [read("hosts", hosts)]), (3, [read("passwd", passwd)])])],
                applies: [true, true], schedule: schedule([[0, 2], [1, 3]]))
            var aliveAtCollection: [Bool] = []
            let scheduler = ActorScheduler(input)
            let outcome = scheduler.run { _, actor, _ in
                if actor == 1 { aliveAtCollection.append(kill(scheduler.sessions[0]!.pid, 0) == 0) }
            }
            try expectNil(outcome.cancelled)
            try expectEqual(outcome.visits.map { $0.endReason }, ["died_before_completion", "completed", "actor_unavailable", "completed"])
            let a = outcome.actors[0], b = outcome.actors[1]
            try expectEqual(a.quiescence, "reaped")
            try expectEqual(a.stopReason, "died_before_completion")
            try expectEqual(a.output!.termSignal, SIGKILL)
            try expectTrue(a.output!.applied && !a.output!.done)
            try expectTrue(outcome.visits[0].releaseStored && outcome.visits[0].acknowledgementObserved && !outcome.visits[0].completionObserved)
            try expectTrue(a.output!.slots.allSatisfy { !$0.completed })
            // By B's first collection the dead actor is already reaped, so the
            // kernel no longer knows its PID as ours.
            try expectEqual(aliveAtCollection, [false, false])
            try expectTrue(b.output!.slots.allSatisfy(readOK))
            try expectEqual(b.output!.phases.map { $0.completed }, [true, true])
        }
        tk.run("a lost validator and long collections do not consume the schedule allowance") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            var input = ActorScheduleInput(
                actors: [actorInput(policy: denyRead(hosts), visits: [(0, [read("hosts", hosts)])]),
                         actorInput(policy: allowAll, visits: [(1, [read("hosts", hosts)])])],
                applies: [true, true], schedule: schedule([[0], [1]]))
            input.executionAllowanceMs = 400
            var lost: [String: String]? = nil
            let outcome = ActorScheduler.run(input) { phase, _, pid in
                if phase == 0 { lost = verdicts(pid: pid, validator: "/nonexistent/sb_api_validator") }
                usleep(300_000)
            }
            try expectEqual(lost, [:])
            try expectNil(outcome.cancelled)
            try expectEqual(outcome.visits.map { $0.endReason }, ["completed", "completed"])
            try expectTrue(denied(outcome.actors[0].output!.slots[0]) && readOK(outcome.actors[1].output!.slots[0]))
            try expectTrue((outcome.executionWait?.excluded_ms ?? 0) >= 600)
        }
        tk.run("the shared lifetime cutoff ends parked and released waits with published timing failures") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            var input = ActorScheduleInput(
                actors: [actorInput(policy: allowAll, visits: [(0, [read("hosts", hosts)])]),
                         actorInput(policy: allowAll, visits: [(1, [read("hosts", hosts)])])],
                applies: [true, true], schedule: schedule([[0], [1]]))
            input.lifetimeMs = 400
            let outcome = ActorScheduler.run(input) { _, _, _ in usleep(800_000) }
            // A hits the cutoff inside its release wait while the collection hook
            // holds the schedule, publishes done and exits, and is reaped before the
            // host rechecks ownership after collection; B hits it while parked.
            try expectEqual(outcome.visits.map { $0.endReason }, ["died_during_collection", "ended_before_arrival"])
            for (index, expectedOp) in [(0, UInt32(11)), (1, UInt32(13))] {
                let record = outcome.actors[index]
                try expectEqual(record.quiescence, "reaped")
                guard let failure = record.output?.workerEvidence?.failure else { throw TestFailure(message: "actor \(index): no published failure") }
                try expectEqual(failure.operation, expectedOp)
                try expectEqual(failure.code, 15)
                try expectTrue(record.output!.done && record.output!.exitCode == 0)
                try expectTrue(record.output!.slots.allSatisfy { !$0.completed })
            }
        }
        tk.run("a cutoff already past refuses every actor at clock setup") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            var input = ActorScheduleInput(
                actors: [actorInput(policy: allowAll, visits: [(0, [read("hosts", hosts)])])],
                applies: [true], schedule: schedule([[0]]))
            input.lifetimeMs = 0
            let outcome = ActorScheduler.run(input) { _, _, _ in }
            try expectEqual(outcome.visits.map { $0.endReason }, ["actor_unavailable"])
            let a = outcome.actors[0]
            try expectEqual(a.setupStatus, .exitedBeforeSetup)
            try expectEqual(a.output!.exitCode, 12)
            try expectFalse(a.output!.readyByteReceived)
            guard let failure = a.output?.workerEvidence?.failure else { throw TestFailure(message: "no published failure") }
            try expectEqual([failure.operation, failure.code, failure.detail], [12, 15, 1])
        }
        tk.run("eight actors each complete one visit under the setup and execution allowances") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let actors = (0..<PWActorLimits.actors).map { i in
                actorInput(policy: i % 2 == 0 ? allowAll : denyRead(hosts), visits: [(i, [read("hosts", hosts)])])
            }
            let input = ActorScheduleInput(actors: actors, applies: actors.map { _ in true },
                                           schedule: schedule(actors.indices.map { [$0] }))
            let scheduler = ActorScheduler(input)
            var parkedActivations: [[UInt32]] = []
            let outcome = scheduler.run { phase, _, _ in
                parkedActivations.append(scheduler.sessions.enumerated().filter { $0.offset > phase }.map { $0.element!.activationObserved })
            }
            try expectNil(outcome.cancelled)
            try expectEqual(outcome.visits.map { $0.endReason }, Array(repeating: "completed", count: PWActorLimits.actors))
            try expectEqual(Set(outcome.actors.compactMap { $0.pid }).count, PWActorLimits.actors)
            for (i, record) in outcome.actors.enumerated() {
                try expectEqual(record.setupStatus, .applied, "actor \(i)")
                try expectEqual(record.output?.activationObserved, UInt32(i + 1), "actor \(i)")
                try expectEqual(i % 2 == 0 ? readOK(record.output!.slots[0]) : denied(record.output!.slots[0]), true, "actor \(i)")
            }
            try expectTrue(parkedActivations.allSatisfy { $0.allSatisfy { $0 == 0 } })
            try expectEqual(outcome.setupWait?.stop, "all_resolved")
        }
    }
}
