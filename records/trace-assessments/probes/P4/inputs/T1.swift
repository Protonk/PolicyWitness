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
                tokens: [AuthorityPlanToken(index: 0, actorIndex: 0, slot: index["a_issue"]!, lastUseSlot: index["a_to_b"]!, outboundPosition: 0)],
                deliveries: [AuthorityPlanDelivery(index: 0, tokenIndex: 0, sourceActorIndex: 0, recipientActorIndex: 0, slot: index["a_to_a"]!, inboundPosition: 0),
                             AuthorityPlanDelivery(index: 1, tokenIndex: 0, sourceActorIndex: 0, recipientActorIndex: 1, slot: index["a_to_b"]!, inboundPosition: 0)], inboundCounts: [1, 1], outboundCounts: [1, 0])
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
