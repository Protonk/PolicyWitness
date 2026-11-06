// Compiled only into a disposable host. No bearer bytes or addresses are read.
import Darwin
import Foundation

func footprintSnapshot(_ scheduler: ActorScheduler, phase: Int, actor: Int) {
    let begin = mach_continuous_time()
    var actors = [[String: Any]]()
    for (index, optional) in scheduler.sessions.enumerated() {
        guard let session = optional else { continue }
        let raw = session.rawBase
        let visits: [[String: Any]] = session.input.phases.indices.map { visit in
            let base = session.phaseBase(visit)
            return ["visit": visit,
                "global_phase": UInt32(bitPattern: readI32(base, offset: PWShmLayout.phaseGlobalPhaseOffset)),
                "arrived": loadAcquire(base, offset: PWShmLayout.phaseArrivedOffset),
                "acknowledged": loadAcquire(base, offset: PWShmLayout.phaseAcknowledgedOffset),
                "completed": loadAcquire(base, offset: PWShmLayout.phaseCompletedOffset)]
        }
        let slots: [[String: Any]] = session.input.slots.indices.map { slot in
            let base = raw.advanced(by: PWShmLayout.slotsOffset + slot * PWShmLayout.slotBytes)
            let completed = loadAcquire(base, offset: PWShmLayout.slotCompletedOffset)
            let boundary = loadAcquire(base, offset: PWShmLayout.slotCallBoundaryOffset)
            let valid = completed == 1 ? readI32(base, offset: PWShmLayout.slotNativeResultValidOffset) : 0
            var row: [String: Any] = ["slot": slot, "step_id": session.input.slots[slot].stepId,
                "attempt_kind": session.input.slots[slot].attemptKind.rawValue, "completed": completed, "call_boundary": boundary,
                "native_valid": valid, "native_not_minus_one": valid == 1 && readI64(base, offset: PWShmLayout.slotNativeResultOffset) != -1]
            if let operands = session.input.slots[slot].extensionOperands {
                row["operands"] = ["token_index": operands.tokenIndex, "delivery_index": operands.deliveryIndex,
                    "handle_index": operands.handleIndex, "recipient_index": operands.recipientIndex,
                    "last_use": operands.lastUse] as [String: Any]
            } else { row["operands"] = NSNull() }
            return row
        }
        actors.append(["actor_index": index, "pid": Int(session.pid), "setup": session.actorSetup,
            "authority_status": session.authorityStatus,
            "activation": loadAcquire(raw, offset: PWShmLayout.activationOffset),
            "activation_observed": session.activationObserved,
            "proceed": loadAcquire(raw, offset: PWShmLayout.proceedOffset),
            "evidence_progress": loadAcquire(raw.advanced(by: PWShmLayout.evidenceOffset), offset: PWShmLayout.evidenceProgressOffset),
            "visits": visits, "slots": slots])
    }
    var regions = [[String: Any]](), tokens = [[String: Any]](), deliveries = [[String: Any]]()
    if let custody = scheduler.custody {
        regions = custody.regions.map { ["actor_index": $0.actorIndex, "bytes": $0.bytes,
            "inbound_count": $0.inboundCount, "outbound_count": $0.outboundCount, "host_mapping": $0.base != nil] }
        tokens = custody.plan.tokens.map { token in
            let buffer = custody.tokens[token.index]
            return ["token_index": token.index, "actor_index": token.actorIndex, "last_use_slot": token.lastUseSlot,
                "accepted": buffer.accepted, "length": buffer.length, "erased": buffer.erased, "mapping_available": buffer.available]
        }
        deliveries = custody.plan.deliveries.map { delivery in
            let region = custody.regions[delivery.recipientActorIndex]
            var row: [String: Any] = ["delivery_index": delivery.index, "token_index": delivery.tokenIndex,
                "source_actor": delivery.sourceActorIndex, "recipient_actor": delivery.recipientActorIndex,
                "inbound_position": delivery.inboundPosition]
            if let slot = region.inbound(delivery.inboundPosition) {
                // Publication acquisitions precede dependent length metadata.
                row["committed"] = loadAcquire(slot, offset: PWAuthorityLayout.slotCommittedOffset)
                row["acknowledged"] = loadAcquire(slot, offset: PWAuthorityLayout.slotAcknowledgedOffset)
                row["settled"] = loadAcquire(slot, offset: PWAuthorityLayout.slotSettledOffset)
                row["length"] = UInt32(bitPattern: readI32(slot, offset: PWAuthorityLayout.slotTokenLengthOffset))
            }
            row["host_equality"] = custody.transfers.last(where: { $0.deliveryIndex == delivery.index })?.equality ?? "not_observed"
            return row
        }
    }
    var timebase = mach_timebase_info_data_t(); mach_timebase_info(&timebase)
    let row: [String: Any] = ["version": 1, "scope": "instrumented_host_pre_collection", "host_pid": Int(getpid()),
        "phase_index": phase, "active_actor": actor, "begin_ticks": begin, "end_ticks": mach_continuous_time(),
        "timebase_numer": timebase.numer, "timebase_denom": timebase.denom,
        "actors": actors, "regions": regions, "tokens": tokens, "deliveries": deliveries]
    guard let data = try? JSONSerialization.data(withJSONObject: row, options: [.sortedKeys]), data.count < 262144 else { fatalError("footprint metadata bound") }
    let path = URL(fileURLWithPath: FOOTPRINT_SNAPSHOT_DIRECTORY).appendingPathComponent("\(getpid())-\(phase).json")
    do { try data.write(to: path, options: [.withoutOverwriting]) } catch { fatalError("footprint snapshot publication") }
}
