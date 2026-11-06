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
    static let headerBytes: Int = 1152
    static let slotHeaderBytes: Int = 64
    static let slotBytes: Int = 16448
    static let maxInbound: Int = 64
    static let maxOutbound: Int = 32
    static let maxTransfers: Int = 64
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
    static let outboundCountOffset: Int = 52
    static let transferCellsOffset: Int = 128
    static let transferCellBytes: Int = 16
    static let transferOperationOffset: Int = 0
    static let transferRequestOffset: Int = 4
    static let transferAckOffset: Int = 8
    static let transferDetailOffset: Int = 12
    static let slotsOffset: Int = 1152
    static let slotMagicOffset: Int = 0
    static let slotFamilyOffset: Int = 4
    static let slotWriterActorOffset: Int = 8
    static let slotOperationIndexOffset: Int = 12
    static let slotResourceIndexOffset: Int = 16
    static let slotTokenLengthOffset: Int = 20
    static let slotCommittedOffset: Int = 24
    static let slotAcknowledgedOffset: Int = 28
    static let slotRejectDetailOffset: Int = 32
    static let slotSettledOffset: Int = 36
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
    let outboundPosition: Int
}
struct AuthorityPlanDelivery {
    let index: Int
    let tokenIndex: Int
    let sourceActorIndex: Int
    let recipientActorIndex: Int
    let inboundPosition: Int
    /// The transfer action's slot within the source actor.
    let slot: Int
    init(index:Int,tokenIndex:Int,sourceActorIndex:Int,recipientActorIndex:Int,slot:Int,inboundPosition:Int) {
        self.index=index;self.tokenIndex=tokenIndex;self.sourceActorIndex=sourceActorIndex
        self.recipientActorIndex=recipientActorIndex;self.slot=slot;self.inboundPosition=inboundPosition
    }
}
struct AuthorityPlan {
    let tokens: [AuthorityPlanToken]
    let deliveries: [AuthorityPlanDelivery]
    let inboundCounts: [Int]
    let outboundCounts: [Int]
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
    let outboundCount: Int
    let bytes: Int
    private(set) var descriptor: Int32 = -1
    private(set) var base: UnsafeMutablePointer<UInt8>?
    private(set) var failure: String?
    let setup: AuthoritySetupRecorder
    private var tornDown = false

    init(actorIndex: Int, inboundCount: Int, outboundCount: Int, sessionNonce: UInt64) {
        self.actorIndex = actorIndex
        self.inboundCount = inboundCount
        self.outboundCount = outboundCount
        bytes = PWAuthorityLayout.headerBytes + (inboundCount + outboundCount) * PWAuthorityLayout.slotBytes
        setup = AuthoritySetupRecorder(capacity:16,actor:actorIndex)
        setup.scope.ownership=["object_name":"not_acquired","descriptor":"not_acquired","mapping":"not_acquired","shared_erasure":"not_present"]
        let name = String("/pw_au_\(getpid())_\(actorIndex)".prefix(31))
        let fd = name.withCString { pw_cworker_shm_open_create($0, 0o600) }
        let openedErrno=errno
        setup.integer(0,"shm_open",fd,openedErrno)
        guard fd >= 0 else { setup.fail(0); failure="shm_open: errno=\(openedErrno)"; return }
        descriptor=fd
        setup.scope.ownership["descriptor"]="held"
        setup.scope.ownership["object_name"]="held"
        let unlinked=name.withCString { shm_unlink($0) }, unlinkErrno=errno
        setup.integer(1,"shm_unlink",unlinked,unlinkErrno)
        guard unlinked==0 else {
            setup.fail(1); failure="shm_unlink: errno=\(unlinkErrno)"
            setup.scope.ownership["object_name"]="unresolved"
            setup.scope.cleanup_reference=PWAuthorityCleanupReference(name:name,host_pid:Int(getpid()),session_nonce:sessionNonce)
            closeDescriptor(); return
        }
        setup.scope.ownership["object_name"]="released"
        let flags=fcntl(fd,F_SETFD,FD_CLOEXEC), flagsErrno=errno
        setup.integer(2,"fd_cloexec",flags,flagsErrno)
        guard flags==0 else { setup.fail(2);failure="FD_CLOEXEC: errno=\(flagsErrno)";closeDescriptor();return }
        let sized=ftruncate(fd,off_t(bytes)), sizeErrno=errno
        setup.integer(3,"ftruncate",sized,sizeErrno,value:UInt64(bytes))
        guard sized==0 else { setup.fail(3);failure="ftruncate: errno=\(sizeErrno)";closeDescriptor();return }
        let mapping=mmap(nil,bytes,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0), mapErrno=errno
        let mapOK=mapping != nil && mapping != MAP_FAILED
        setup.record(4,"mmap",mapOK ? "succeeded":"failed",kind:"mapping",error:mapOK ? nil:mapErrno,value:UInt64(bytes))
        guard mapOK, let mapped=mapping else { setup.fail(4);failure="mmap: errno=\(mapErrno)";closeDescriptor();return }
        setup.scope.ownership["mapping"]="held"
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
        writeU32(raw, offset: PWAuthorityLayout.outboundCountOffset, UInt32(outboundCount))
        setup.record(5,"header_initialize","performed",kind:"memory")
        setup.scope.disposition="ready"
    }

    func outbound(_ index: Int) -> UnsafeMutablePointer<UInt8>? {
        guard index >= 0, index < outboundCount else { return nil }
        return base?.advanced(by: PWAuthorityLayout.slotsOffset + index * PWAuthorityLayout.slotBytes)
    }
    func inbound(_ index: Int) -> UnsafeMutablePointer<UInt8>? {
        guard index >= 0, index < inboundCount else { return nil }
        return base?.advanced(by: PWAuthorityLayout.slotsOffset + (outboundCount + index) * PWAuthorityLayout.slotBytes)
    }
    func transfer(_ index: Int) -> UnsafeMutablePointer<UInt8>? {
        guard index >= 0, index < PWAuthorityLayout.maxTransfers else { return nil }
        return base?.advanced(by: PWAuthorityLayout.transferCellsOffset + index * PWAuthorityLayout.transferCellBytes)
    }

    /// The host keeps its mapping; the descriptor is needed only until spawn.
    func closeDescriptor() {
        if descriptor >= 0 {
            let fd=descriptor; descriptor = -1
            let rc=close(fd), saved=errno
            setup.integer(9,"close_original_descriptor",rc,saved,cleanup:true)
            setup.scope.ownership["descriptor"]=rc==0 ? "released":"unresolved"
        }
    }

    func eraseAll() {
        guard let base else { return }
        for i in 0..<(outboundCount + inboundCount) {
            let slot = base.advanced(by: PWAuthorityLayout.slotsOffset + i * PWAuthorityLayout.slotBytes)
            pwAuthorityClear(UnsafeMutableRawPointer(slot.advanced(by: PWAuthorityLayout.slotTokenOffset)), PWAuthorityLayout.tokenBytes)
        }
    }

    func tearDown(quiescent: Bool = true) {
        guard !tornDown else { return }
        tornDown=true
        if base != nil {
            if quiescent {
                eraseAll()
                setup.record(10,"shared_clear","performed",kind:"memory",value:UInt64((inboundCount+outboundCount)*PWAuthorityLayout.tokenBytes),cleanup:true)
                setup.scope.ownership["shared_erasure"]="performed"
            } else { setup.scope.ownership["shared_erasure"]="withheld_not_quiescent" }
        }
        if let base {
            let rc=munmap(UnsafeMutableRawPointer(base),bytes), saved=errno
            setup.integer(11,"munmap",rc,saved,cleanup:true,value:UInt64(bytes))
            setup.scope.ownership["mapping"]=rc==0 ? "released":"unresolved"
            if rc==0 { self.base=nil }
        }
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
    let setup: AuthoritySetupRecorder
    private var finished=false

    init(tokenIndex: Int) {
        self.tokenIndex = tokenIndex
        setup=AuthoritySetupRecorder(capacity:4,token:tokenIndex)
        setup.scope.ownership=["mapping":"not_acquired","private_erasure":"not_present"]
        let mapped=mmap(nil,PWAuthorityLayout.tokenBytes,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0), saved=errno
        let ok=mapped != nil && mapped != MAP_FAILED
        setup.record(0,"mmap",ok ? "succeeded":"failed",kind:"mapping",error:ok ? nil:saved,value:UInt64(PWAuthorityLayout.tokenBytes))
        if ok,let mapped {
            buffer=mapped; memset(mapped,0,PWAuthorityLayout.tokenBytes)
            setup.scope.disposition="ready";setup.scope.ownership["mapping"]="held"
        } else { setup.fail(0) }
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

    func finish() {
        guard !finished else { return };finished=true
        if let buffer {
            erase()
            setup.record(1,"final_erase","performed",kind:"memory",value:UInt64(PWAuthorityLayout.tokenBytes),cleanup:true)
            setup.scope.ownership["private_erasure"]="performed"
            let rc=munmap(buffer,PWAuthorityLayout.tokenBytes), saved=errno
            setup.integer(2,"munmap",rc,saved,cleanup:true,value:UInt64(PWAuthorityLayout.tokenBytes))
            setup.scope.ownership["mapping"]=rc==0 ? "released":"unresolved"
            if rc==0 { self.buffer=nil }
        }
    }
    deinit { finish() }
}

final class AuthorityCustody {
    let plan: AuthorityPlan
    let calls: ChildProcessCalls
    let sessionNonce: UInt64
    let setup = AuthoritySetupRecorder(capacity:4)
    private(set) var regions: [ActorAuthorityRegion]
    private(set) var tokens: [TokenCustody]
    /// Each delivery's inbound slot within its recipient's region.
    private(set) var inboundSlotOfDelivery: [Int]
    private(set) var outboundSlotOfToken: [Int]
    private(set) var custody: [CustodyObservation] = []
    private(set) var transfers: [TransferObservation] = []
    private var finished = false

    init(plan: AuthorityPlan, actorCount: Int, calls: ChildProcessCalls) {
        self.plan = plan
        self.calls = calls
        // Core dumps are disabled in the custody-owning host before any token
        // can arrive; a failure here is recorded by the first region.
        var core = rlimit(rlim_cur: 0, rlim_max: 0)
        let coreRC=setrlimit(RLIMIT_CORE,&core), coreErrno=errno
        let coreLimited=coreRC==0
        setup.integer(0,"core_limit",coreRC,coreErrno)
        if coreLimited { setup.scope.disposition="ready" } else { setup.fail(0) }
        let nonce = UInt64.random(in: UInt64.min...UInt64.max)
        sessionNonce = nonce
        let inboundCounts=plan.inboundCounts, outboundCounts=plan.outboundCounts
        let slotOfToken=plan.tokens.map { $0.outboundPosition }
        let slotOfDelivery=plan.deliveries.map { $0.inboundPosition }
        outboundSlotOfToken=slotOfToken
        inboundSlotOfDelivery=slotOfDelivery
        // No region may carry a token while this host could dump core. Setup
        // failure prevents the scheduler from launching this authority session.
        coreLimitFailure = coreLimited ? nil : "setrlimit(RLIMIT_CORE): " + String(cString: strerror(coreErrno))
        regions = coreLimited
            ? (0..<actorCount).map { ActorAuthorityRegion(actorIndex: $0, inboundCount: inboundCounts[$0],
                                                         outboundCount: outboundCounts[$0], sessionNonce: nonce) }
            : []
        tokens = coreLimited ? plan.tokens.map { TokenCustody(tokenIndex: $0.index) } : []
        // Every issue and transfer has one immutable assignment and one
        // publication cell for the entire specimen. A late answer therefore
        // cannot become the answer to a later operation.
        for token in plan.tokens where regions.indices.contains(token.actorIndex) {
            guard let slot = regions[token.actorIndex].outbound(slotOfToken[token.index]) else { continue }
            writeU32(slot, offset: PWAuthorityLayout.slotWriterActorOffset, UInt32(token.actorIndex))
            writeU32(slot, offset: PWAuthorityLayout.slotOperationIndexOffset, UInt32(token.slot))
            writeU32(slot, offset: PWAuthorityLayout.slotResourceIndexOffset, UInt32(token.index))
        }
        for delivery in plan.deliveries where regions.indices.contains(delivery.sourceActorIndex) {
            guard let cell = regions[delivery.sourceActorIndex].transfer(delivery.index) else { continue }
            writeU32(cell, offset: PWAuthorityLayout.transferOperationOffset, UInt32(delivery.slot + 1))
        }
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
        guard !finished, coreLimitFailure == nil, regions.indices.contains(active), regions[active].base != nil else { return }
        serviceOutbound(active: active, region: regions[active], phaseIndex: phaseIndex)
        // Bound one potentially waiting exchange per service pass. The
        // scheduler supplies a fresh remaining allowance on the next pass.
        for delivery in plan.deliveries where delivery.sourceActorIndex == active {
            guard let cell = regions[active].transfer(delivery.index),
                  loadAcquire(cell, offset: PWAuthorityLayout.transferRequestOffset) == 1,
                  loadAcquire(cell, offset: PWAuthorityLayout.transferAckOffset) == PWTransferAck.none,
                  !transfers.contains(where: { $0.deliveryIndex == delivery.index }) else { continue }
            serviceTransfer(delivery: delivery, cell: cell, phaseIndex: phaseIndex,
                            waitAllowanceMs: waitAllowanceMs, recipientUsable: recipientUsable)
            break
        }
    }

    /// A persistent request may outlive the source's wait. Only the source's
    /// completed action publication establishes which answer it observed;
    /// a late host answer cannot retroactively complete that publication.
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

    // Internal observation boundary for deterministic copy/slot-lifetime tests.
    // Production leaves this nil; it neither issues nor transforms authority.
    var beforeOutboundCopy: ((Int) -> Void)?

    private func serviceOutbound(active: Int, region: ActorAuthorityRegion, phaseIndex: Int) {
        for token in plan.tokens where token.actorIndex == active {
            guard let slot = region.outbound(outboundSlotOfToken[token.index]),
                  loadAcquire(slot, offset: PWAuthorityLayout.slotCommittedOffset) == 1,
                  loadAcquire(slot, offset: PWAuthorityLayout.slotAcknowledgedOffset) == PWAuthorityAck.none else { continue }
            var observation = CustodyObservation(tokenIndex: token.index, actorIndex: active, slot: token.slot,
                                                phaseIndex: phaseIndex, status: "rejected", rejectDetail: nil, length: nil)
            var problem = slotFramingProblem(slot)
            if problem == nil {
                if readU32(slot, offset: PWAuthorityLayout.slotWriterActorOffset) != UInt32(active) { problem = 3 }
                else if readU32(slot, offset: PWAuthorityLayout.slotOperationIndexOffset) != UInt32(token.slot) { problem = 4 }
                else if readU32(slot, offset: PWAuthorityLayout.slotResourceIndexOffset) != UInt32(token.index) { problem = 8 }
                else if !tokens[token.index].available { problem = 8 }
            }
            if problem == nil {
                beforeOutboundCopy?(token.index)
                let length = Int(readU32(slot, offset: PWAuthorityLayout.slotTokenLengthOffset))
                tokens[token.index].accept(from: slot.advanced(by: PWAuthorityLayout.slotTokenOffset), length: length)
                // Publication gives the host sole payload ownership. Neither
                // a timeout nor worker exit can erase or reuse this slot.
                if !tokens[token.index].framingIntact {
                    tokens[token.index].erase()
                    problem = 6
                } else {
                    observation.status = "accepted"
                    observation.length = length
                    if token.lastUseSlot == token.slot {
                        tokens[token.index].erase()
                        observation.erased = true
                    }
                }
            }
            // The host's one-shot acknowledgement follows its last payload
            // read and erasure. The worker never clears either publication.
            pwAuthorityClear(UnsafeMutableRawPointer(slot.advanced(by: PWAuthorityLayout.slotTokenOffset)), PWAuthorityLayout.tokenBytes)
            writeU32(slot, offset: PWAuthorityLayout.slotTokenLengthOffset, 0)
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
    }

    private func serviceTransfer(delivery: AuthorityPlanDelivery, cell: UnsafeMutablePointer<UInt8>, phaseIndex: Int,
                                 waitAllowanceMs: Int, recipientUsable: (Int) -> Bool) {
        let active = delivery.sourceActorIndex, slot = delivery.slot
        func answer(_ ack: UInt32, detail: UInt32) {
            writeU32(cell, offset: PWAuthorityLayout.transferDetailOffset, detail)
            storeRelease(cell, offset: PWAuthorityLayout.transferAckOffset, ack)
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
        guard readU32(cell, offset: PWAuthorityLayout.transferOperationOffset) == UInt32(slot + 1) else {
            observation.acknowledgement = PWTransferAck.requestInvalid
            answer(PWTransferAck.requestInvalid, detail: 0)
            return
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
                // This is the host's last payload read. Only now may the
                // recipient consume or erase its own copy, including itself
                // after a source-side timeout in a self-transfer.
                storeRelease(inbound, offset: PWAuthorityLayout.slotSettledOffset, 1)
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

    /// Settle a failed delivery without writing under a framing reader. The
    /// recipient owns subsequent erasure; final host cleanup requires reap.
    private func withdraw(_ inbound: UnsafeMutablePointer<UInt8>) {
        storeRelease(inbound, offset: PWAuthorityLayout.slotSettledOffset, 2)
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

    /// Always erase private custody. Erase shared regions only for actors
    /// whose termination is established; otherwise detach the host mapping.
    /// The nil default is for isolated regions with no actor process owner.
    func finish(quiescentActors: Set<Int>? = nil) {
        if finished { return }
        finished = true
        for token in tokens { token.finish() }
        for i in custody.indices { custody[i].erased = true }
        for region in regions { region.tearDown(quiescent: quiescentActors?.contains(region.actorIndex) ?? true) }
    }

    var setupObservation: PWRunnerAuthorityHost {
        PWRunnerAuthorityHost(run:setup.scope,regions:regions.map { $0.setup.scope },custody:tokens.map { $0.setup.scope })
    }
    func recorder(for actor: Int) -> AuthoritySetupRecorder? {
        regions.indices.contains(actor) ? regions[actor].setup:nil
    }

    deinit { finish() }
}

private func readU32(_ base: UnsafePointer<UInt8>, offset: Int) -> UInt32 {
    UInt32(bitPattern: readI32(base, offset: offset))
}
