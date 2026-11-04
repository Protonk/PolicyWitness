import Darwin
import Foundation

/*
 * AuthorityCustody — the host side of the actor form's transient authority
 * channels. One authority region per actor (a separate shared object from
 * the evidence region, mapped by the host and that actor only), bounded
 * host custody buffers for admitted tokens, and the servicing of the active
 * actor's outbound publications and transfer requests.
 *
 * Nothing here is a native sandbox call. Tokens are copied between fixed
 * native buffers, compared for equality, erased at their last declared use
 * and at teardown, and never enter Swift strings, logs, diagnostics or the
 * reply. Every acceptance and acknowledgement is a host or recipient fact,
 * recorded separately from the issuing actor's native result.
 */

// Checked against compiled C sizeof/offsetof by runner_abi_layout.
enum PWAuthorityLayout {
    static let magic: UInt32 = 0x50574155
    static let headerBytes: Int = 128
    static let slotHeaderBytes: Int = 64
    static let slotBytes: Int = 16448
    static let maxInbound: Int = 64
    static let maxHandles: Int = 64
    static let identityBytes: Int = 32
    static let exchangeWaitMs: Int = 5000
    static let familyFile: UInt32 = 1
    static let tokenBytes: Int = 16384
    static let magicOffset: Int = 0
    static let identityOffset: Int = 4
    static let actorIndexOffset: Int = 36
    static let sessionNonceOffset: Int = 40
    static let inboundCountOffset: Int = 48
    static let transferRequestOffset: Int = 52
    static let transferAckOffset: Int = 56
    static let transferDetailOffset: Int = 60
    static let outboundOffset: Int = 128
    static let slotMagicOffset: Int = 0
    static let slotFamilyOffset: Int = 4
    static let slotWriterActorOffset: Int = 8
    static let slotOperationIndexOffset: Int = 12
    static let slotResourceIndexOffset: Int = 16
    static let slotTokenLengthOffset: Int = 20
    static let slotCommittedOffset: Int = 24
    static let slotAcknowledgedOffset: Int = 28
    static let slotRejectDetailOffset: Int = 32
    static let slotTokenOffset: Int = 64
}

/// The admitted tokens and deliveries, by global resource index, with the
/// actions that produce and last use them. Action slots are the issuing or
/// sending actor's own slot indexes (its position in that actor's input),
/// which is what the worker names in its publications and requests.
struct AuthorityPlanToken {
    let index: Int
    let actorIndex: Int
    /// The issue action's slot within the issuing actor.
    let slot: Int
    /// The issuing actor's slot of the token's last declared use: its final
    /// transfer, or the issue itself when it is never transferred.
    let lastUseSlot: Int
}
struct AuthorityPlanDelivery {
    let index: Int
    let tokenIndex: Int
    let sourceActorIndex: Int
    let recipientActorIndex: Int
    /// The transfer action's slot within the source actor.
    let slot: Int
}
struct AuthorityPlan {
    var tokens: [AuthorityPlanToken]
    var deliveries: [AuthorityPlanDelivery]
}

/// One token's host custody account.
struct CustodyObservation {
    let tokenIndex: Int
    let actorIndex: Int
    let slot: Int
    var phaseIndex: Int
    /// accepted, or rejected with the framing reason.
    var status: String
    var rejectDetail: UInt32?
    var length: Int?
    var erased = false
}

/// One explicit transfer as the host serviced it. No native result; the
/// recipient's acknowledgement is its own framing acceptance, not consumption.
struct TransferObservation {
    let deliveryIndex: Int
    let tokenIndex: Int
    let sourceActorIndex: Int
    let recipientActorIndex: Int
    let slot: Int
    var phaseIndex: Int
    var requestObserved = true
    var custodyStatus: String
    var copyStatus: String
    var equality: String
    var recipientAcknowledged = false
    var recipientRejectDetail: UInt32?
    /// The PW_TRANSFER_ACK_* value the host stored for the source.
    var acknowledgement: UInt32
    var sourceAcknowledged = false
    var recipientWait: PWHostWait?
}

@_silgen_name("pw_extension_clear")
private func pwAuthorityClear(_ bytes: UnsafeMutableRawPointer, _ length: Int)

/// One actor's authority region: created, unlinked and mapped by the host
/// before launch; the actor maps the inherited descriptor itself.
final class ActorAuthorityRegion {
    let actorIndex: Int
    let inboundCount: Int
    let bytes: Int
    private(set) var descriptor: Int32 = -1
    private(set) var base: UnsafeMutablePointer<UInt8>?
    private(set) var failure: String?

    init(actorIndex: Int, inboundCount: Int, sessionNonce: UInt64) {
        self.actorIndex = actorIndex
        self.inboundCount = inboundCount
        bytes = PWAuthorityLayout.headerBytes + (inboundCount + 1) * PWAuthorityLayout.slotBytes
        let name = String("/pw_au_\(getpid())_\(actorIndex)".prefix(31))
        let fd = name.withCString { pw_cworker_shm_open_create($0, 0o600) }
        guard fd >= 0 else { failure = "shm_open: " + String(cString: strerror(errno)); return }
        guard name.withCString({ shm_unlink($0) }) == 0 else {
            failure = "shm_unlink \(name): " + String(cString: strerror(errno)); close(fd); return
        }
        guard fcntl(fd, F_SETFD, FD_CLOEXEC) == 0 else {
            failure = "FD_CLOEXEC: " + String(cString: strerror(errno)); close(fd); return
        }
        guard ftruncate(fd, off_t(bytes)) == 0 else {
            failure = "ftruncate: " + String(cString: strerror(errno)); close(fd); return
        }
        guard let mapped = mmap(nil, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0), mapped != MAP_FAILED else {
            failure = "mmap: " + String(cString: strerror(errno)); close(fd); return
        }
        memset(mapped, 0, bytes)
        descriptor = fd
        let raw = mapped.assumingMemoryBound(to: UInt8.self)
        base = raw
        writeU32(raw, offset: PWAuthorityLayout.magicOffset, PWAuthorityLayout.magic)
        PWShmLayout.abiIdentity.withUnsafeBytes { identity in
            raw.advanced(by: PWAuthorityLayout.identityOffset).update(from: identity.bindMemory(to: UInt8.self).baseAddress!,
                                                                    count: PWAuthorityLayout.identityBytes)
        }
        writeU32(raw, offset: PWAuthorityLayout.actorIndexOffset, UInt32(actorIndex))
        writeU64(raw, offset: PWAuthorityLayout.sessionNonceOffset, sessionNonce)
        writeU32(raw, offset: PWAuthorityLayout.inboundCountOffset, UInt32(inboundCount))
    }

    var outbound: UnsafeMutablePointer<UInt8>? { base?.advanced(by: PWAuthorityLayout.outboundOffset) }
    func inbound(_ index: Int) -> UnsafeMutablePointer<UInt8>? {
        guard index >= 0, index < inboundCount else { return nil }
        return base?.advanced(by: PWAuthorityLayout.outboundOffset + (index + 1) * PWAuthorityLayout.slotBytes)
    }

    /// The host keeps its mapping; the descriptor is needed only until spawn.
    func closeDescriptor() {
        if descriptor >= 0 { close(descriptor); descriptor = -1 }
    }

    func eraseAll() {
        guard let base else { return }
        for i in 0...inboundCount {
            let slot = base.advanced(by: PWAuthorityLayout.outboundOffset + i * PWAuthorityLayout.slotBytes)
            pwAuthorityClear(UnsafeMutableRawPointer(slot.advanced(by: PWAuthorityLayout.slotTokenOffset)), PWAuthorityLayout.tokenBytes)
        }
    }

    func tearDown() {
        eraseAll()
        if let base { _ = munmap(UnsafeMutableRawPointer(base), bytes) }
        base = nil
        closeDescriptor()
    }

    deinit { tearDown() }
}

/// Host custody of one admitted token: a fixed anonymous buffer, filled from
/// an accepted outbound publication and erased at the token's last declared
/// use or at teardown.
final class TokenCustody {
    let tokenIndex: Int
    private var buffer: UnsafeMutableRawPointer?
    private(set) var length = 0
    private(set) var accepted = false
    private(set) var erased = false

    init(tokenIndex: Int) {
        self.tokenIndex = tokenIndex
        if let mapped = mmap(nil, PWAuthorityLayout.tokenBytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON, -1, 0), mapped != MAP_FAILED {
            buffer = mapped
            memset(mapped, 0, PWAuthorityLayout.tokenBytes)
        }
    }

    var available: Bool { buffer != nil }

    /// Copy `length + 1` bytes from a slot's token field into custody.
    func accept(from token: UnsafePointer<UInt8>, length: Int) {
        guard let buffer, length > 0, length < PWAuthorityLayout.tokenBytes else { return }
        memcpy(buffer, token, length + 1)
        self.length = length
        accepted = true
        erased = false
    }

    /// The custody copy's own framing after the copy: terminator in place and
    /// no interior NUL. A writer that withdrew mid-copy fails this.
    var framingIntact: Bool {
        guard let buffer, accepted else { return false }
        let bytes = buffer.assumingMemoryBound(to: UInt8.self)
        if bytes[length] != 0 { return false }
        for i in 0..<length where bytes[i] == 0 { return false }
        return true
    }

    func copy(to token: UnsafeMutablePointer<UInt8>) -> Bool {
        guard let buffer, accepted, !erased else { return false }
        memcpy(token, buffer, length + 1)
        return true
    }

    func equals(_ token: UnsafePointer<UInt8>, length other: Int) -> Bool {
        guard let buffer, accepted, !erased, other == length else { return false }
        return memcmp(buffer, token, length + 1) == 0
    }

    func erase() {
        if let buffer { pwAuthorityClear(buffer, PWAuthorityLayout.tokenBytes) }
        length = 0
        erased = true
        accepted = false
    }

    deinit {
        erase()
        if let buffer { _ = munmap(buffer, PWAuthorityLayout.tokenBytes) }
    }
}

final class AuthorityCustody {
    let plan: AuthorityPlan
    let calls: ChildProcessCalls
    let sessionNonce: UInt64
    private(set) var regions: [ActorAuthorityRegion]
    private(set) var tokens: [TokenCustody]
    /// Each delivery's inbound slot within its recipient's region.
    private(set) var inboundSlotOfDelivery: [Int]
    private(set) var custody: [CustodyObservation] = []
    private(set) var transfers: [TransferObservation] = []
    private var finished = false

    init(plan: AuthorityPlan, actorCount: Int, calls: ChildProcessCalls) {
        self.plan = plan
        self.calls = calls
        // Core dumps are disabled in the custody-owning host before any token
        // can arrive; a failure here is recorded by the first region.
        var core = rlimit(rlim_cur: 0, rlim_max: 0)
        let coreLimited = setrlimit(RLIMIT_CORE, &core) == 0
        let coreErrno = errno
        let nonce = UInt64.random(in: UInt64.min...UInt64.max)
        sessionNonce = nonce
        var inboundCounts = Array(repeating: 0, count: actorCount)
        var slotOfDelivery: [Int] = []
        for delivery in plan.deliveries {
            slotOfDelivery.append(inboundCounts[delivery.recipientActorIndex])
            inboundCounts[delivery.recipientActorIndex] += 1
        }
        inboundSlotOfDelivery = slotOfDelivery
        // No region may carry a token while this host could dump core. Setup
        // failure prevents the scheduler from launching this authority session.
        coreLimitFailure = coreLimited ? nil : "setrlimit(RLIMIT_CORE): " + String(cString: strerror(coreErrno))
        regions = coreLimited
            ? (0..<actorCount).map { ActorAuthorityRegion(actorIndex: $0, inboundCount: inboundCounts[$0], sessionNonce: nonce) }
            : []
        tokens = coreLimited ? plan.tokens.map { TokenCustody(tokenIndex: $0.index) } : []
        // Before spawn, bind each inbound slot to its admitted delivery. The
        // recipient snapshots these non-authority fields before application;
        // a later committed frame must match that assignment.
        for delivery in plan.deliveries where regions.indices.contains(delivery.recipientActorIndex) {
            guard let slot = regions[delivery.recipientActorIndex].inbound(slotOfDelivery[delivery.index]) else { continue }
            writeU32(slot, offset: PWAuthorityLayout.slotWriterActorOffset, UInt32(delivery.sourceActorIndex))
            writeU32(slot, offset: PWAuthorityLayout.slotOperationIndexOffset, UInt32(delivery.slot))
            writeU32(slot, offset: PWAuthorityLayout.slotResourceIndexOffset, UInt32(delivery.index))
        }
    }
    private let coreLimitFailure: String?

    var setupFailure: String? {
        if let coreLimitFailure { return coreLimitFailure }
        if let region = regions.first(where: { $0.failure != nil }) {
            return "actor \(region.actorIndex) authority region: \(region.failure!)"
        }
        if let token = tokens.first(where: { !$0.available }) {
            return "token \(token.tokenIndex) custody allocation failed"
        }
        return nil
    }

    func regionStatus(for actor: Int) -> String {
        if let failure = coreLimitFailure { return "host_setup_failed: " + failure }
        guard regions.indices.contains(actor) else { return "absent" }
        return regions[actor].failure.map { "setup_failed: " + $0 } ?? "mapped"
    }

    func descriptor(for actor: Int) -> Int32? {
        guard coreLimitFailure == nil, regions.indices.contains(actor), regions[actor].failure == nil else { return nil }
        return regions[actor].descriptor
    }

    func closeDescriptor(for actor: Int) {
        guard regions.indices.contains(actor) else { return }
        regions[actor].closeDescriptor()
    }

    // MARK: - Servicing

    /// One pass for the active actor: accept or reject a committed outbound
    /// token and answer a transfer request exactly once.
    func service(active: Int, phaseIndex: Int, waitAllowanceMs: Int = PWAuthorityLayout.exchangeWaitMs,
                 recipientUsable: (Int) -> Bool) {
        guard !finished, coreLimitFailure == nil, regions.indices.contains(active), let base = regions[active].base else { return }
        serviceOutbound(active: active, region: regions[active], phaseIndex: phaseIndex)
        let request = loadAcquire(base, offset: PWAuthorityLayout.transferRequestOffset)
        if request != 0 && loadAcquire(base, offset: PWAuthorityLayout.transferAckOffset) == PWTransferAck.none
            && !transfers.contains(where: { $0.sourceActorIndex == active && $0.slot == Int(request) - 1 }) {
            serviceTransfer(active: active, region: regions[active], slot: Int(request) - 1, phaseIndex: phaseIndex,
                            waitAllowanceMs: waitAllowanceMs, recipientUsable: recipientUsable)
        }
    }

    /// A withdrawn request can mean timeout, and a later request can replace
    /// it before the host samples zero. Only the source's completed action
    /// publication establishes which answer it actually observed.
    func recordSourceAcknowledgements(_ outputs: [CWorkerOutput?]) {
        for i in transfers.indices {
            let transfer = transfers[i]
            guard outputs.indices.contains(transfer.sourceActorIndex),
                  let output = outputs[transfer.sourceActorIndex], output.slots.indices.contains(transfer.slot) else { continue }
            let slot = output.slots[transfer.slot]
            transfers[i].sourceAcknowledged = slot.completed && transfer.acknowledgement != PWTransferAck.none
                && slot.extensionPublication?.transferStatus == transfer.acknowledgement
        }
    }

    private func serviceOutbound(active: Int, region: ActorAuthorityRegion, phaseIndex: Int) {
        guard let slot = region.outbound else { return }
        guard loadAcquire(slot, offset: PWAuthorityLayout.slotCommittedOffset) == 1,
              loadAcquire(slot, offset: PWAuthorityLayout.slotAcknowledgedOffset) == PWAuthorityAck.none else { return }
        let resource = Int(readU32(slot, offset: PWAuthorityLayout.slotResourceIndexOffset))
        let operation = Int(readU32(slot, offset: PWAuthorityLayout.slotOperationIndexOffset))
        let token = plan.tokens.indices.contains(resource) ? plan.tokens[resource] : nil
        var observation = CustodyObservation(tokenIndex: resource, actorIndex: active, slot: operation, phaseIndex: phaseIndex,
                                             status: "rejected", rejectDetail: nil, length: nil)
        var problem = slotFramingProblem(slot)
        if problem == nil {
            if readU32(slot, offset: PWAuthorityLayout.slotWriterActorOffset) != UInt32(active) { problem = 3 }
            else if token == nil || token!.actorIndex != active { problem = 8 }
            else if token!.slot != operation { problem = 4 }
            else if !tokens[resource].available { problem = 8 }
        }
        if problem == nil {
            let length = Int(readU32(slot, offset: PWAuthorityLayout.slotTokenLengthOffset))
            tokens[resource].accept(from: slot.advanced(by: PWAuthorityLayout.slotTokenOffset), length: length)
            // The copy is credited only if the writer still stands behind it
            // and the copied bytes frame one token on their own.
            if loadAcquire(slot, offset: PWAuthorityLayout.slotCommittedOffset) != 1 || !tokens[resource].framingIntact {
                tokens[resource].erase()
                problem = 6
            } else {
                observation.status = "accepted"
                observation.length = length
                if token!.lastUseSlot == operation {
                    tokens[resource].erase()
                    observation.erased = true
                }
            }
        }
        if let problem {
            observation.status = "rejected:" + (PWAuthorityAck.rejectNames[problem] ?? String(problem))
            observation.rejectDetail = problem
            writeU32(slot, offset: PWAuthorityLayout.slotRejectDetailOffset, problem)
            storeRelease(slot, offset: PWAuthorityLayout.slotAcknowledgedOffset, PWAuthorityAck.rejected)
        } else {
            storeRelease(slot, offset: PWAuthorityLayout.slotAcknowledgedOffset, PWAuthorityAck.accepted)
        }
        custody.append(observation)
    }

    private func serviceTransfer(active: Int, region: ActorAuthorityRegion, slot: Int, phaseIndex: Int,
                                 waitAllowanceMs: Int, recipientUsable: (Int) -> Bool) {
        guard let base = region.base else { return }
        func answer(_ ack: UInt32, detail: UInt32) {
            writeU32(base, offset: PWAuthorityLayout.transferDetailOffset, detail)
            storeRelease(base, offset: PWAuthorityLayout.transferAckOffset, ack)
        }
        guard let delivery = plan.deliveries.first(where: { $0.slot == slot && $0.sourceActorIndex == active }) else {
            transfers.append(TransferObservation(deliveryIndex: -1, tokenIndex: -1, sourceActorIndex: active, recipientActorIndex: -1,
                slot: slot, phaseIndex: phaseIndex, custodyStatus: "unknown_request", copyStatus: "not_copied",
                equality: "not_compared", acknowledgement: PWTransferAck.requestInvalid))
            answer(PWTransferAck.requestInvalid, detail: 0)
            return
        }
        var observation = TransferObservation(deliveryIndex: delivery.index, tokenIndex: delivery.tokenIndex,
            sourceActorIndex: active, recipientActorIndex: delivery.recipientActorIndex, slot: slot, phaseIndex: phaseIndex,
            custodyStatus: "unavailable", copyStatus: "not_copied", equality: "not_compared", acknowledgement: PWTransferAck.none)
        defer {
            transfers.append(observation)
            // Last use retires custody even when the recipient is unavailable.
            if let token = plan.tokens.first(where: { $0.index == delivery.tokenIndex }), token.lastUseSlot == slot,
               tokens.indices.contains(delivery.tokenIndex) {
                tokens[delivery.tokenIndex].erase()
                for i in custody.indices where custody[i].tokenIndex == delivery.tokenIndex { custody[i].erased = true }
            }
        }
        let custodyEntry = tokens.indices.contains(delivery.tokenIndex) ? tokens[delivery.tokenIndex] : nil
        guard let custodyEntry, custodyEntry.accepted, !custodyEntry.erased else {
            observation.acknowledgement = PWTransferAck.custodyUnavailable
            answer(PWTransferAck.custodyUnavailable, detail: 0)
            return
        }
        observation.custodyStatus = "held"
        let recipient = delivery.recipientActorIndex
        guard regions.indices.contains(recipient), regions[recipient].failure == nil,
              let inbound = regions[recipient].inbound(inboundSlotOfDelivery[delivery.index]),
              recipientUsable(recipient) else {
            observation.acknowledgement = PWTransferAck.recipientUnavailable
            answer(PWTransferAck.recipientUnavailable, detail: 0)
            return
        }
        // Copy into the recipient's assigned slot and commit.
        writeU32(inbound, offset: PWAuthorityLayout.slotMagicOffset, PWAuthorityLayout.magic)
        writeU32(inbound, offset: PWAuthorityLayout.slotFamilyOffset, PWAuthorityLayout.familyFile)
        writeU32(inbound, offset: PWAuthorityLayout.slotWriterActorOffset, UInt32(active))
        writeU32(inbound, offset: PWAuthorityLayout.slotOperationIndexOffset, UInt32(slot))
        writeU32(inbound, offset: PWAuthorityLayout.slotResourceIndexOffset, UInt32(delivery.index))
        writeU32(inbound, offset: PWAuthorityLayout.slotTokenLengthOffset, UInt32(custodyEntry.length))
        writeU32(inbound, offset: PWAuthorityLayout.slotRejectDetailOffset, 0)
        storeRelease(inbound, offset: PWAuthorityLayout.slotAcknowledgedOffset, PWAuthorityAck.none)
        guard custodyEntry.copy(to: inbound.advanced(by: PWAuthorityLayout.slotTokenOffset)) else {
            observation.acknowledgement = PWTransferAck.custodyUnavailable
            answer(PWTransferAck.custodyUnavailable, detail: 0)
            return
        }
        observation.copyStatus = "copied"
        storeRelease(inbound, offset: PWAuthorityLayout.slotCommittedOffset, 1)
        // The recipient validates and acknowledges while parked or, for a
        // self-transfer, inside its own request wait.
        var clock = HostWaitClock(milliseconds: min(PWAuthorityLayout.exchangeWaitMs, waitAllowanceMs), pollNs: 1_000_000, calls: calls)
        var ack = PWAuthorityAck.none
        var stop = "acknowledged"
        while true {
            ack = loadAcquire(inbound, offset: PWAuthorityLayout.slotAcknowledgedOffset)
            if ack != PWAuthorityAck.none { break }
            if !recipientUsable(recipient) { stop = "recipient_unavailable"; break }
            if clock.expiredAfterSleeping() { stop = "deadline"; break }
        }
        observation.recipientWait = clock.record(stop: stop)
        switch ack {
        case PWAuthorityAck.accepted:
            observation.recipientAcknowledged = true
            let length = Int(readU32(inbound, offset: PWAuthorityLayout.slotTokenLengthOffset))
            if custodyEntry.equals(inbound.advanced(by: PWAuthorityLayout.slotTokenOffset), length: length) {
                observation.equality = "equal"
                observation.acknowledgement = PWTransferAck.delivered
                answer(PWTransferAck.delivered, detail: UInt32(delivery.index))
            } else {
                observation.equality = "unequal"
                observation.acknowledgement = PWTransferAck.copyMismatch
                withdraw(inbound)
                answer(PWTransferAck.copyMismatch, detail: 0)
            }
        case PWAuthorityAck.rejected:
            observation.recipientAcknowledged = true
            observation.recipientRejectDetail = readU32(inbound, offset: PWAuthorityLayout.slotRejectDetailOffset)
            observation.acknowledgement = PWTransferAck.recipientRejected
            withdraw(inbound)
            answer(PWTransferAck.recipientRejected, detail: observation.recipientRejectDetail ?? 0)
        default:
            observation.acknowledgement = stop == "deadline" ? PWTransferAck.recipientTimeout : PWTransferAck.recipientUnavailable
            withdraw(inbound)
            answer(observation.acknowledgement, detail: 0)
        }
    }

    /// A delivery the recipient cannot consume: erase the bytes and drop the
    /// commit so no later consume finds an accepted slot.
    private func withdraw(_ inbound: UnsafeMutablePointer<UInt8>) {
        pwAuthorityClear(UnsafeMutableRawPointer(inbound.advanced(by: PWAuthorityLayout.slotTokenOffset)), PWAuthorityLayout.tokenBytes)
        writeU32(inbound, offset: PWAuthorityLayout.slotTokenLengthOffset, 0)
        storeRelease(inbound, offset: PWAuthorityLayout.slotCommittedOffset, 0)
    }

    /// Framing only: magic, family, bounded length, terminator, no interior NUL.
    private func slotFramingProblem(_ slot: UnsafePointer<UInt8>) -> UInt32? {
        if readU32(slot, offset: PWAuthorityLayout.slotMagicOffset) != PWAuthorityLayout.magic { return 1 }
        if readU32(slot, offset: PWAuthorityLayout.slotFamilyOffset) != PWAuthorityLayout.familyFile { return 2 }
        let length = Int(readU32(slot, offset: PWAuthorityLayout.slotTokenLengthOffset))
        if length == 0 || length >= PWAuthorityLayout.tokenBytes { return 5 }
        let token = slot.advanced(by: PWAuthorityLayout.slotTokenOffset)
        if token[length] != 0 { return 6 }
        for i in 0..<length where token[i] == 0 { return 7 }
        return nil
    }

    // MARK: - Teardown

    /// Erase every custody buffer and region after the workers have stopped.
    func finish() {
        if finished { return }
        finished = true
        for token in tokens { token.erase() }
        for i in custody.indices { custody[i].erased = true }
        for region in regions { region.tearDown() }
    }

    deinit { finish() }
}

private func readU32(_ base: UnsafePointer<UInt8>, offset: Int) -> UInt32 {
    UInt32(bitPattern: readI32(base, offset: offset))
}
