import Darwin
import Foundation
@testable import PWRunnerCore

/*
 * ActorAuthorityTests — the native file authority path through the scheduler
 * and the host custody module, with real workers: an unapplied actor issues
 * a token for a test-owned file, the host takes custody, an explicit transfer
 * delivers it to a parked applied actor that accepted it while parked and
 * consumes it only after its phase release, and a fresh read follows. The
 * principal three-actor shape re-issues from the consuming actor to a third.
 *
 * Every native result is read from the worker's own slot publication; custody,
 * delivery and acceptance are host and recipient facts recorded apart from it.
 * A native refusal on this host is a legitimate observation here; what these
 * cases cannot accept is a skipped call, a missing publication or a credited
 * association the evidence does not support.
 */

private func equipment(_ name: String) -> String {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent()
    let app = ProcessInfo.processInfo.environment["PW_APP_DIR"] ?? root.appendingPathComponent("dist/PolicyWitness.app").path
    return app + "/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/" + name
}

/// B issues only under a consumed read extension and has no ordinary read
/// allowance for the target; C can read only under a consumed extension.
private let bPolicy = "(version 1) (allow default) (deny file-read-data) (deny file-write*) (deny file-issue-extension) "
    + "(allow file-read-data (extension \"com.apple.app-sandbox.read\")) "
    + "(allow file-issue-extension (require-all (extension-class \"com.apple.app-sandbox.read\") (extension \"com.apple.app-sandbox.read\")))"
private let cPolicy = "(version 1) (allow default) (deny file-read-data) (deny file-write*) (allow file-read-data (extension \"com.apple.app-sandbox.read\"))"

private func freshTarget(_ name: String) throws -> String {
    let dir = FileManager.default.temporaryDirectory.appendingPathComponent("pw-actor-authority-\(getpid())", isDirectory: true)
    try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    let file = dir.appendingPathComponent(name)
    try Data("witness bytes for \(name)\n".utf8).write(to: file)
    var resolved = [CChar](repeating: 0, count: Int(PATH_MAX))
    guard realpath(file.path, &resolved) != nil else { throw TestFailure(message: "realpath failed") }
    return String(cString: resolved)
}

private func readFresh(_ id: String, _ target: String) -> CWorkerSlotInput {
    CWorkerSlotInput(stepId: id, attemptKind: .fileReadFresh, target: target)
}
private func issue(_ id: String, token: Int, target: String) -> CWorkerSlotInput {
    CWorkerSlotInput(stepId: id, attemptKind: .extensionIssue, target: "",
                     extensionOperands: CWorkerExtensionOperands(tokenIndex: UInt32(token), target: target))
}
private func transfer(_ id: String, token: Int, delivery: Int, recipient: Int) -> CWorkerSlotInput {
    CWorkerSlotInput(stepId: id, attemptKind: .extensionTransfer, target: "",
                     extensionOperands: CWorkerExtensionOperands(tokenIndex: UInt32(token), deliveryIndex: UInt32(delivery), recipientIndex: UInt32(recipient)))
}
private func consume(_ id: String, delivery: Int, handle: Int, lastUse: Bool = true) -> CWorkerSlotInput {
    CWorkerSlotInput(stepId: id, attemptKind: .extensionConsume, target: "",
                     extensionOperands: CWorkerExtensionOperands(deliveryIndex: UInt32(delivery), handleIndex: UInt32(handle), lastUse: lastUse))
}
private func release(_ id: String, handle: Int) -> CWorkerSlotInput {
    CWorkerSlotInput(stepId: id, attemptKind: .extensionRelease, target: "",
                     extensionOperands: CWorkerExtensionOperands(handleIndex: UInt32(handle)))
}

/// Build one actor's input from its visits; returns the input and each step
/// id's slot index within its own actor, the index the worker publishes.
private struct ActorBuild {
    var visits: [(phase: Int, slots: [CWorkerSlotInput])]
    var policy: String
    var applies: Bool
}

private func assemble(_ actors: [ActorBuild]) -> (ActorScheduleInput, [String: Int]) {
    var entries: [(phase: Int, actor: Int, visit: Int, slots: [CWorkerSlotInput])] = []
    for (a, actor) in actors.enumerated() {
        for (v, visit) in actor.visits.enumerated() { entries.append((visit.phase, a, v, visit.slots)) }
    }
    entries.sort { $0.phase < $1.phase }
    var localSlot: [String: Int] = [:]
    let inputs = actors.map { actor -> CWorkerInput in
        var slots: [CWorkerSlotInput] = []
        var phases: [CWorkerPhaseInput] = []
        for visit in actor.visits {
            phases.append(CWorkerPhaseInput(firstSlot: slots.count, endSlot: slots.count + visit.slots.count, globalPhase: visit.phase + 1))
            for slot in visit.slots { localSlot[slot.stepId] = slots.count; slots.append(slot) }
        }
        var input = CWorkerInput(workerExecutablePath: equipment("pw-probe-runner"), policy: actor.policy, slots: slots, phases: phases, sentinelTimeoutMs: 10_000)
        input.proceedWaitMs = 5_000
        return input
    }
    let schedule = entries.map { ActorScheduleEntry(phaseIndex: $0.phase, actorIndex: $0.actor, visit: $0.visit) }
    return (ActorScheduleInput(actors: inputs, applies: actors.map { $0.applies }, schedule: schedule), localSlot)
}

private func slot(_ outcome: ActorScheduleOutcome, _ actor: Int, _ id: String) -> CWorkerSlotResult? {
    outcome.actors[actor].output?.slots.first { $0.stepId == id }
}
private func denied(_ slot: CWorkerSlotResult?) -> Bool {
    guard let slot, slot.completed else { return false }
    return slot.rc != 0 && [EPERM, EACCES].contains(slot.errnoVal)
}
private func readable(_ slot: CWorkerSlotResult?) -> Bool { slot?.completed == true && slot?.rc == 0 }

/// Also run alone by the disposable outbound-alias mutation control. Two
/// distinct synthetic payloads expose a changed association even when both
/// publications frame correctly. No native extension operation is involved.
func runHandoffCopyBoundaryControl() throws {
    let plan = AuthorityPlan(tokens: [
        AuthorityPlanToken(index: 0, actorIndex: 0, slot: 0, lastUseSlot: 2),
        AuthorityPlanToken(index: 1, actorIndex: 0, slot: 1, lastUseSlot: 3)], deliveries: [
        AuthorityPlanDelivery(index: 0, tokenIndex: 0, sourceActorIndex: 0, recipientActorIndex: 0, slot: 2),
        AuthorityPlanDelivery(index: 1, tokenIndex: 1, sourceActorIndex: 0, recipientActorIndex: 0, slot: 3)])
    let custody = AuthorityCustody(plan: plan, actorCount: 1, calls: ChildProcessCalls())
    defer { custody.finish() }
    try expectNil(custody.setupFailure)
    let payloads = [Array("first-owned-payload\0".utf8), Array("second-owned-payload\0".utf8)]
    func publish(_ index: Int) {
        let slot = custody.regions[0].outbound(index)!
        writeU32(slot, offset: PWAuthorityLayout.slotMagicOffset, PWAuthorityLayout.magic)
        writeU32(slot, offset: PWAuthorityLayout.slotFamilyOffset, PWAuthorityLayout.familyFile)
        writeU32(slot, offset: PWAuthorityLayout.slotWriterActorOffset, 0)
        writeU32(slot, offset: PWAuthorityLayout.slotOperationIndexOffset, UInt32(index))
        writeU32(slot, offset: PWAuthorityLayout.slotResourceIndexOffset, UInt32(index))
        writeU32(slot, offset: PWAuthorityLayout.slotTokenLengthOffset, UInt32(payloads[index].count - 1))
        payloads[index].withUnsafeBufferPointer {
            slot.advanced(by: PWAuthorityLayout.slotTokenOffset).update(from: $0.baseAddress!, count: $0.count)
        }
        storeRelease(slot, offset: PWAuthorityLayout.slotAcknowledgedOffset, 0)
        storeRelease(slot, offset: PWAuthorityLayout.slotCommittedOffset, 1)
    }
    publish(0)
    var secondPublishedDuringFirstCopy = false
    custody.beforeOutboundCopy = { index in
        if index == 0 { publish(1); secondPublishedDuringFirstCopy = true }
    }
    custody.service(active: 0, phaseIndex: 0) { _ in true }
    try expectTrue(secondPublishedDuringFirstCopy, "controlled second publication was not reached")
    let firstMatches = payloads[0].withUnsafeBufferPointer { custody.tokens[0].equals($0.baseAddress!, length: $0.count - 1) }
    try expectTrue(firstMatches, "handoff copy preserves first issue bytes")
    let secondMatches = payloads[1].withUnsafeBufferPointer { custody.tokens[1].equals($0.baseAddress!, length: $0.count - 1) }
    try expectTrue(secondMatches, "handoff copy preserves second issue bytes")
    try expectEqual(custody.custody.map { $0.tokenIndex }, [0, 1])
    for index in 0..<2 {
        let slot = custody.regions[0].outbound(index)!
        try expectEqual(loadAcquire(slot, offset: PWAuthorityLayout.slotAcknowledgedOffset), PWAuthorityAck.accepted)
        try expectTrue((0..<PWAuthorityLayout.tokenBytes).allSatisfy { slot[PWAuthorityLayout.slotTokenOffset + $0] == 0 },
                       "host erased accepted outbound payload")
    }
}

func runActorAuthorityTests(_ tk: TestKit) {
    let workerPresent = FileManager.default.isExecutableFile(atPath: equipment("pw-probe-runner"))
    tk.group("actor authority: native issue, host custody, explicit transfer, consume and release") {
        tk.run("a later publication cannot replace bytes during an earlier custody copy") {
            try runHandoffCopyBoundaryControl()
        }
        tk.run("shared-region erasure requires known quiescence and unknown actors retain their bytes") {
            for quiescent in [false, true] {
                let plan = AuthorityPlan(tokens: [AuthorityPlanToken(index: 0, actorIndex: 0, slot: 0, lastUseSlot: 1)],
                    deliveries: [AuthorityPlanDelivery(index: 0, tokenIndex: 0, sourceActorIndex: 0, recipientActorIndex: 0, slot: 1)])
                let custody = AuthorityCustody(plan: plan, actorCount: 1, calls: ChildProcessCalls())
                try expectNil(custody.setupFailure)
                let region = custody.regions[0]
                guard let observed = mmap(nil, region.bytes, PROT_READ | PROT_WRITE, MAP_SHARED, region.descriptor, 0),
                      observed != MAP_FAILED else { throw TestFailure(message: "independent authority observation mapping") }
                defer { _ = munmap(observed, region.bytes) }
                let raw = observed.assumingMemoryBound(to: UInt8.self)
                let offsets = [PWAuthorityLayout.slotsOffset, PWAuthorityLayout.slotsOffset + PWAuthorityLayout.slotBytes]
                for offset in offsets {
                    memset(raw.advanced(by: offset + PWAuthorityLayout.slotTokenOffset), 0x5a, PWAuthorityLayout.tokenBytes)
                }
                custody.finish(quiescentActors: quiescent ? Set([0]) : Set())
                custody.finish() // Idempotence must not turn unknown into an erase permission.
                for offset in offsets {
                    let start = offset + PWAuthorityLayout.slotTokenOffset
                    try expectTrue((0..<PWAuthorityLayout.tokenBytes).allSatisfy { raw[start + $0] == (quiescent ? 0 : 0x5a) },
                                   "shared payload erasure follows established quiescence")
                }
            }
        }
        tk.run("one-shot source answers require a matching publication and are serviced once") {
            let plan = AuthorityPlan(tokens: [AuthorityPlanToken(index: 0, actorIndex: 0, slot: 0, lastUseSlot: 1)],
                deliveries: [AuthorityPlanDelivery(index: 0, tokenIndex: 0, sourceActorIndex: 0, recipientActorIndex: 0, slot: 1)])
            let custody = AuthorityCustody(plan: plan, actorCount: 1, calls: ChildProcessCalls())
            defer { custody.finish() }
            try expectNil(custody.setupFailure)
            let cell = custody.regions[0].transfer(0)!
            storeRelease(cell, offset: PWAuthorityLayout.transferRequestOffset, 1)
            custody.service(active: 0, phaseIndex: 0) { _ in true }
            try expectEqual(custody.transfers.count, 1)
            // Even a malformed repeated request cannot service this cell twice.
            storeRelease(cell, offset: PWAuthorityLayout.transferAckOffset, 0)
            custody.service(active: 0, phaseIndex: 0) { _ in true }
            try expectEqual(custody.transfers.count, 1)
            var result = CWorkerSlotResult(stepId: "transfer", rc: 0, errnoVal: 0, observedPath: nil, error: nil, completed: false)
            result.extensionPublication = CWorkerExtensionPublication(tokenLength: 0, custodyStatus: 0, transferStatus: PWTransferAck.custodyUnavailable)
            var output = CWorkerOutput(workerPid: 0, readyByteReceived: true, applied: false, applyRC: 0, applyErrno: 0, done: false, slots: [result, result])
            custody.recordSourceAcknowledgements([output])
            try expectFalse(custody.transfers[0].sourceAcknowledged)
            output.slots[1].completed = true
            output.slots[1].extensionPublication?.transferStatus = PWTransferAck.hostTimeout
            custody.recordSourceAcknowledgements([output])
            try expectFalse(custody.transfers[0].sourceAcknowledged)
            output.slots[1].extensionPublication?.transferStatus = PWTransferAck.custodyUnavailable
            custody.recordSourceAcknowledgements([output])
            try expectTrue(custody.transfers[0].sourceAcknowledged)
        }
        tk.run("positive calibration: an unapplied issuer supplies a parked applied reader through host custody") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let target = try freshTarget("calibration")
            let (base, index) = assemble([
                ActorBuild(visits: [(1, [issue("a_issue", token: 0, target: target), transfer("a_to_b", token: 0, delivery: 0, recipient: 1)])], policy: "", applies: false),
                ActorBuild(visits: [(0, [readFresh("b_before", target)]),
                                    (2, [consume("b_consume", delivery: 0, handle: 0), readFresh("b_after", target), release("b_release", handle: 0)])],
                           policy: cPolicy, applies: true),
            ])
            var input = base
            input.authority = AuthorityPlan(
                tokens: [AuthorityPlanToken(index: 0, actorIndex: 0, slot: index["a_issue"]!, lastUseSlot: index["a_to_b"]!)],
                deliveries: [AuthorityPlanDelivery(index: 0, tokenIndex: 0, sourceActorIndex: 0, recipientActorIndex: 1, slot: index["a_to_b"]!)])
            let scheduler = ActorScheduler(input)
            // Independent observation at B's consume phase: B accepted the
            // delivery while parked (its inbound slot is acknowledged) and has
            // completed nothing since its first visit.
            var parkedAcceptance: (acknowledged: UInt32, completedBefore: Int)? = nil
            let outcome = scheduler.run { phase, actor, _ in
                if phase == 2, actor == 1, let custody = scheduler.custody,
                   let inbound = custody.regions[1].inbound(0) {
                    parkedAcceptance = (loadAcquire(inbound, offset: PWAuthorityLayout.slotAcknowledgedOffset),
                                        scheduler.sessions[1]!.completedSlotCount)
                }
            }
            try expectNil(outcome.cancelled)
            try expectEqual(outcome.visits.map { $0.endReason }, ["completed", "completed", "completed"])
            try expectEqual(outcome.actors.map { $0.authorityRegion }, ["mapped", "mapped"])
            for record in outcome.actors {
                try expectEqual(record.output?.authorityStatus, 1, "actor \(record.index) mapped its region")
                try expectEqual(record.output?.nativeSymbols, 7, "actor \(record.index) resolved consume, release and issue")
            }
            // A's native issue: a published nonnull result with a measured length,
            // accepted into custody; the transfer delivered and the recipient
            // acknowledged while parked.
            let aIssue = slot(outcome, 0, "a_issue")!
            try expectTrue(aIssue.completed && aIssue.callBoundary)
            try expectEqual(aIssue.nativeResult, 1)
            try expectEqual(aIssue.extensionPublication?.custodyStatus, 1)
            try expectTrue((aIssue.extensionPublication?.tokenLength ?? 0) > 0)
            try expectEqual(outcome.custody.map { ($0.tokenIndex, $0.status, $0.erased) }.map { "\($0.0):\($0.1):\($0.2)" }, ["0:accepted:true"])
            try expectEqual(outcome.custody[0].length, Int(aIssue.extensionPublication!.tokenLength))
            let aTransfer = slot(outcome, 0, "a_to_b")!
            try expectTrue(aTransfer.completed && !aTransfer.callBoundary && aTransfer.nativeResult == nil)
            try expectEqual(aTransfer.extensionPublication?.transferStatus, PWTransferAck.delivered)
            try expectEqual(outcome.transfers.count, 1)
            let delivery = outcome.transfers[0]
            try expectTrue(delivery.recipientAcknowledged && delivery.equality == "equal" && delivery.copyStatus == "copied")
            try expectEqual(delivery.acknowledgement, PWTransferAck.delivered)
            try expectTrue(delivery.sourceAcknowledged)
            try expectEqual(parkedAcceptance?.acknowledged, PWAuthorityAck.accepted)
            try expectEqual(parkedAcceptance?.completedBefore, 1)
            // B: denied before, consume returned a published result, readable after
            // on a fresh descriptor, release published.
            let bBefore = slot(outcome, 1, "b_before"), bConsume = slot(outcome, 1, "b_consume")!,
                bAfter = slot(outcome, 1, "b_after"), bRelease = slot(outcome, 1, "b_release")!
            try expectTrue(denied(bBefore), "B's baseline read is denied under its policy")
            try expectTrue(bConsume.completed && bConsume.callBoundary && bConsume.nativeResult != nil)
            try expectEqual(bConsume.unavailableCode, 0)
            if bConsume.nativeResult != -1 {
                try expectTrue(readable(bAfter), "B reads the target after consuming the delivered extension")
                try expectEqual(bAfter?.freshRead?.read_rc, Int64("witness bytes for calibration\n".utf8.count))
                try expectTrue(bRelease.completed && bRelease.callBoundary && bRelease.nativeResult != nil)
            } else {
                // A published native consume failure is a legitimate observation;
                // the dependent read and release still ran and published.
                try expectTrue(bAfter?.completed == true && bRelease.completed && bRelease.unavailableCode == 2)
            }
            try expectEqual(outcome.actors[1].output?.phases.map { $0.completed }, [true, true])
        }
        tk.run("principal shape: B issues under a consumed extension and re-delegates to C") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let target = try freshTarget("principal")
            let (base, index) = assemble([
                ActorBuild(visits: [(2, [issue("a_issue", token: 0, target: target), transfer("a_to_b", token: 0, delivery: 0, recipient: 1)])], policy: "", applies: false),
                ActorBuild(visits: [(0, [readFresh("b_read_before", target)]),
                                    (3, [consume("b_consume_first", delivery: 0, handle: 0)]),
                                    (4, [readFresh("b_read_after", target), issue("b_issue", token: 1, target: target), transfer("b_to_c", token: 1, delivery: 1, recipient: 2)]),
                                    (7, [release("b_release", handle: 0)])], policy: bPolicy, applies: true),
                ActorBuild(visits: [(1, [readFresh("c_read_before", target)]),
                                    (5, [consume("c_consume_second", delivery: 1, handle: 1)]),
                                    (6, [readFresh("c_read_after", target), release("c_release", handle: 1)])], policy: cPolicy, applies: true),
            ])
            var input = base
            input.authority = AuthorityPlan(
                tokens: [AuthorityPlanToken(index: 0, actorIndex: 0, slot: index["a_issue"]!, lastUseSlot: index["a_to_b"]!),
                         AuthorityPlanToken(index: 1, actorIndex: 1, slot: index["b_issue"]!, lastUseSlot: index["b_to_c"]!)],
                deliveries: [AuthorityPlanDelivery(index: 0, tokenIndex: 0, sourceActorIndex: 0, recipientActorIndex: 1, slot: index["a_to_b"]!),
                             AuthorityPlanDelivery(index: 1, tokenIndex: 1, sourceActorIndex: 1, recipientActorIndex: 2, slot: index["b_to_c"]!)])
            let outcome = ActorScheduler.run(input) { _, _, _ in }
            try expectNil(outcome.cancelled)
            try expectEqual(outcome.visits.map { $0.endReason }, Array(repeating: "completed", count: 8))
            try expectEqual(outcome.actors.map { $0.setupStatus }, [.unappliedDeclared, .applied, .applied])
            try expectTrue(denied(slot(outcome, 1, "b_read_before")) && denied(slot(outcome, 2, "c_read_before")))
            let aIssue = slot(outcome, 0, "a_issue")!, bConsume = slot(outcome, 1, "b_consume_first")!, bIssue = slot(outcome, 1, "b_issue")!
            let bTransfer = slot(outcome, 1, "b_to_c")!, cConsume = slot(outcome, 2, "c_consume_second")!
            try expectEqual(aIssue.nativeResult, 1)
            try expectEqual(aIssue.extensionPublication?.custodyStatus, 1)
            try expectTrue(bConsume.completed && bConsume.callBoundary && bConsume.nativeResult != nil)
            // B's second issue is attempted whatever its consume returned, and
            // its native result is published by B's own process.
            try expectTrue(bIssue.completed && bIssue.callBoundary && bIssue.nativeResult != nil)
            let bIssued = bIssue.nativeResult == 1
            try expectEqual(bIssue.extensionPublication?.custodyStatus, bIssued ? 1 : 4)
            try expectEqual(outcome.custody.map { $0.tokenIndex }, bIssued ? [0, 1] : [0])
            // The second delivery is bound to B's issue, never to A's token.
            try expectEqual(outcome.transfers.map { $0.tokenIndex }, [0, 1])
            try expectEqual(outcome.transfers.map { $0.acknowledgement }, [PWTransferAck.delivered, bIssued ? PWTransferAck.delivered : PWTransferAck.custodyUnavailable])
            try expectEqual(bTransfer.extensionPublication?.transferStatus, bIssued ? PWTransferAck.delivered : PWTransferAck.custodyUnavailable)
            // C's consume and read run in every case; their results are read, not assumed.
            try expectTrue(cConsume.completed)
            if bIssued {
                try expectTrue(cConsume.callBoundary && cConsume.nativeResult != nil)
            } else {
                try expectEqual(cConsume.unavailableCode, 6)
            }
            try expectTrue(slot(outcome, 2, "c_read_after")?.completed == true)
            let chain = bConsume.nativeResult != -1 && readable(slot(outcome, 1, "b_read_after")) && bIssued
                && cConsume.nativeResult != -1 && readable(slot(outcome, 2, "c_read_after"))
            // Record the kernel's answer for the journal; either outcome is a
            // faithful witness as long as every link published.
            FileHandle.standardError.write(Data("principal chain on this host: \(chain ? "usable access through re-delegation" : "refused or unavailable at some link")\n".utf8))
            try expectTrue(slot(outcome, 1, "b_release")!.completed && slot(outcome, 2, "c_release")!.completed)
        }
        tk.run("a parked recipient never consumes before its release; repeated consume and self-transfer keep their references") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let target = try freshTarget("repeat")
            let (base, index) = assemble([
                ActorBuild(visits: [(0, [issue("a_issue", token: 0, target: target), transfer("a_to_a", token: 0, delivery: 0, recipient: 0),
                                         transfer("a_to_b", token: 0, delivery: 1, recipient: 1)]),
                                    (2, [consume("a_consume", delivery: 0, handle: 0)])], policy: "", applies: false),
                ActorBuild(visits: [(1, [consume("b_first", delivery: 1, handle: 1, lastUse: false), consume("b_again", delivery: 1, handle: 2),
                                         release("b_release_first", handle: 1), release("b_release_again", handle: 2)])], policy: cPolicy, applies: true),
            ])
            var input = base
            input.authority = AuthorityPlan(
                tokens: [AuthorityPlanToken(index: 0, actorIndex: 0, slot: index["a_issue"]!, lastUseSlot: index["a_to_b"]!)],
                deliveries: [AuthorityPlanDelivery(index: 0, tokenIndex: 0, sourceActorIndex: 0, recipientActorIndex: 0, slot: index["a_to_a"]!),
                             AuthorityPlanDelivery(index: 1, tokenIndex: 0, sourceActorIndex: 0, recipientActorIndex: 1, slot: index["a_to_b"]!)])
            let scheduler = ActorScheduler(input)
            var bCompletedAtPhase0End: Int? = nil
            var bAcceptedAtPhase1: UInt32? = nil
            let outcome = scheduler.run { phase, _, _ in
                if phase == 1 {
                    bCompletedAtPhase0End = scheduler.sessions[1]!.completedSlotCount
                    bAcceptedAtPhase1 = loadAcquire(scheduler.custody!.regions[1].inbound(0)!, offset: PWAuthorityLayout.slotAcknowledgedOffset)
                }
            }
            try expectNil(outcome.cancelled)
            try expectEqual(outcome.visits.map { $0.endReason }, ["completed", "completed", "completed"])
            try expectEqual(outcome.transfers.map { $0.acknowledgement }, [PWTransferAck.delivered, PWTransferAck.delivered])
            try expectEqual(outcome.transfers.map { $0.recipientActorIndex }, [0, 1])
            // B accepted its delivery while parked and had consumed nothing when
            // its phase arrived.
            try expectEqual(bAcceptedAtPhase1, PWAuthorityAck.accepted)
            try expectEqual(bCompletedAtPhase0End, 0)
            let first = slot(outcome, 1, "b_first")!, again = slot(outcome, 1, "b_again")!
            try expectTrue(first.completed && first.callBoundary && again.completed && again.callBoundary)
            try expectEqual(first.unavailableCode, 0)
            try expectEqual(again.unavailableCode, 0)
            // Distinct lifecycle references even when the raw handles agree.
            let releases = [slot(outcome, 1, "b_release_first")!, slot(outcome, 1, "b_release_again")!]
            for (candidate, consumeResult) in zip(releases, [first.nativeResult, again.nativeResult]) {
                try expectTrue(candidate.completed)
                try expectEqual(candidate.unavailableCode, consumeResult == -1 ? 2 : 0)
            }
            // The self-transfer delivered into A's own inbound slot; A consumed it in a later visit.
            let aConsume = slot(outcome, 0, "a_consume")!
            try expectTrue(aConsume.completed && aConsume.callBoundary)
            try expectEqual(aConsume.unavailableCode, 0)
            // Custody was erased at the token's last declared transfer.
            try expectEqual(outcome.custody.map { $0.erased }, [true])
        }
        tk.run("missing custody, unknown requests and an absent region are published as unavailability, not native results") {
            guard workerPresent else { throw TestFailure(message: "required equipment: pw-probe-runner missing; run make build") }
            let target = try freshTarget("faults")
            // A transfers a token it never issued; B consumes a delivery that never arrived.
            let (base, index) = assemble([
                ActorBuild(visits: [(0, [transfer("a_to_b", token: 0, delivery: 0, recipient: 1)])], policy: "", applies: false),
                ActorBuild(visits: [(1, [consume("b_consume", delivery: 0, handle: 0), release("b_release", handle: 0), readFresh("b_read", target)])], policy: cPolicy, applies: true),
            ])
            var input = base
            input.authority = AuthorityPlan(
                tokens: [AuthorityPlanToken(index: 0, actorIndex: 0, slot: 99, lastUseSlot: index["a_to_b"]!)],
                deliveries: [AuthorityPlanDelivery(index: 0, tokenIndex: 0, sourceActorIndex: 0, recipientActorIndex: 1, slot: index["a_to_b"]!)])
            let outcome = ActorScheduler.run(input) { _, _, _ in }
            try expectEqual(outcome.visits.map { $0.endReason }, ["completed", "completed"])
            let transfer = slot(outcome, 0, "a_to_b")!
            try expectTrue(transfer.completed && !transfer.callBoundary)
            try expectEqual(transfer.extensionPublication?.transferStatus, PWTransferAck.custodyUnavailable)
            try expectEqual(outcome.transfers.map { $0.acknowledgement }, [PWTransferAck.custodyUnavailable])
            let consume = slot(outcome, 1, "b_consume")!, release = slot(outcome, 1, "b_release")!
            try expectTrue(consume.completed && !consume.callBoundary && consume.nativeResult == nil)
            try expectEqual(consume.unavailableCode, 6)
            try expectEqual(release.unavailableCode, 2)
            try expectTrue(denied(slot(outcome, 1, "b_read")), "the independent read still ran and was denied")
            // Without an authority plan no region exists: the operations are
            // unavailable for want of the channel and ordinary actions run.
            let (plain, _) = assemble([
                ActorBuild(visits: [(0, [issue("a_issue", token: 0, target: target), readFresh("a_read", target)])], policy: "", applies: false)])
            let bare = ActorScheduler.run(plain) { _, _, _ in }
            let bareIssue = slot(bare, 0, "a_issue")!
            try expectEqual(bare.actors[0].output?.authorityStatus, 2)
            try expectTrue(bareIssue.completed && !bareIssue.callBoundary)
            try expectEqual(bareIssue.unavailableCode, 5)
            try expectTrue(readable(slot(bare, 0, "a_read")))
        }
    }
}
