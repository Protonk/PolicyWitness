import Foundation
import Darwin

/// Host scopes have one immutable cell per operation. Errors are bounded integrity facts, never truncation of native facts.
final class AuthoritySetupRecorder {
    var scope: PWRunnerAuthorityScope
    let capacity: Int
    init(capacity: Int, actor: Int? = nil, token: Int? = nil) {
        self.capacity=capacity
        scope=PWRunnerAuthorityScope(actor_index: actor, token_index: token, disposition: "not_attempted")
    }
    func record(_ slot: Int, _ operation: String, _ state: String, kind: String? = nil,
                rc: Int64? = nil, error: Int32? = nil, detail: String? = nil,
                value: UInt64? = nil, cleanup: Bool = false) {
        guard slot >= 0 && slot < capacity && !scope.operations.contains(where: {$0.slot==slot}) else {
            scope.integrity_errors=["invalid_or_repeated_operation_slot"]; return
        }
        scope.operations.append(PWRunnerAuthorityOperation(slot:slot,operation:operation,
            role:cleanup ? "cleanup":"setup",state:state,native_kind:kind,native_rc:rc,
            errno:error,detail:detail,value:value))
        scope.operations.sort { $0.slot < $1.slot }
    }
    func integer(_ slot: Int, _ operation: String, _ rc: Int32, _ saved: Int32, cleanup: Bool = false, value: UInt64? = nil) {
        record(slot,operation,rc == -1 ? "failed":"succeeded",kind:"integer",rc:Int64(rc),
               error:rc == -1 ? saved:nil,value:value,cleanup:cleanup)
    }
    func fail(_ slot: Int) { if scope.primary_operation == nil { scope.primary_operation=slot }; scope.disposition="failed" }
}

enum PWAuthoritySetupLayout {
    static let bytes: Int = 832
    static let capacity: Int = 16
    static let cellBytes: Int = 48
    static let cellsOffset: Int = 64
    static let decisionOffset: Int = 0
    static let dispositionOffset: Int = 4
    static let primaryOffset: Int = 8
    static let requiredOffset: Int = 12
    static let actorOffset: Int = 16
    static let publishedOffset: Int = 0
    static let kindOffset: Int = 4
    static let operationOffset: Int = 8
    static let stateOffset: Int = 12
    static let rcOffset: Int = 16
    static let errnoOffset: Int = 24
    static let flagsOffset: Int = 28
    static let detailOffset: Int = 32
    static let reservedOffset: Int = 36
    static let valueOffset: Int = 40
    static let encodedReserve: Int = 524288
    static let names=["issue_symbol","consume_symbol","release_symbol","core_limit","descriptor_presence",
        "fstat","page_size","object_size","mmap","descriptor_close","header_binding",
        "terminal_owned_inbound_clear","rejected_mapping_munmap"]
}

func decodeAuthoritySetup(_ raw: UnsafePointer<UInt8>, actor: Int, required: Bool) -> PWRunnerAuthorityScope {
    var result=PWRunnerAuthorityScope(actor_index:actor,required:required,publication:"not_observed",
        ownership:["descriptor":"not_acquired","mapping":"not_acquired","shared_erasure":"not_present"])
    guard workerIdentityMatches(raw) else { return result }
    let base=raw.advanced(by:PWShmLayout.authoritySetupOffset)
    func u32(_ p: UnsafePointer<UInt8>,_ offset:Int)->UInt32 { UInt32(bitPattern:readI32(p,offset:offset)) }
    // Snapshot the decision first. Its release orders every prerequisite cell;
    // scanning first could miss a primary that precedes a newly observed decision.
    // Individual cell acquires remain independent when this snapshot is absent.
    let decision=loadAcquire(base,offset:0)
    var errors=Set<String>()
    if u32(base,12) != (required ? 1:0) || u32(base,16) != UInt32(actor) { errors.insert("setup_association_mismatch") }
    for i in 0..<16 {
        let cell=base.advanced(by:64+i*48), published=loadAcquire(base.advanced(by:64+i*48),offset:0)
        if published==0 { continue }
        guard published==1 && i<PWAuthoritySetupLayout.names.count else { errors.insert("invalid_setup_publication"); continue }
        let flags=u32(cell,28), kind=u32(cell,4), state=u32(cell,12), detail=u32(cell,32)
        let kinds=[1:"integer",2:"mapping",3:"symbol",4:"validation",5:"memory"]
        let states=[1:"succeeded",2:"failed",3:"accepted",4:"rejected",5:"available",6:"unavailable",7:"performed",8:"not_attempted"]
        guard flags & ~15 == 0, u32(cell,36)==0, u32(cell,8)==UInt32(i),
              let k=kinds[Int(kind)],let s=states[Int(state)],
              (i==9 || ((flags & 8 != 0)==[11,12].contains(i))),
              (flags & 2 == 0 || (state==2 && [1,2].contains(kind))),
              (flags & 1 == 0 || kind==1) else { errors.insert("invalid_setup_cell"); continue }
        let expectedKinds:[UInt32]=[3,3,3,1,4,1,1,4,2,1,4,5,1]
        let validStates:[UInt32:Set<UInt32>]=[1:[1,2],2:[1,2],3:[5,6],4:[3,4],5:[7]]
        guard kind==expectedKinds[i], (state==8 || validStates[kind]?.contains(state)==true),
              (state==8 || kind != 1 || flags & 1 != 0),
              (state != 2 || flags & 2 != 0),
              (state != 8 || flags & 7 == 0) else { errors.insert("invalid_setup_cell");continue }
        let detailName: String? = detail==0 ? nil : (i==4 && detail==1 ? "descriptor_missing" :
            (i==10 ? [1:"magic",2:"identity",3:"actor_index",4:"slot_counts",5:"region_extent"][Int(detail)] : nil))
        if detail != 0 && detailName==nil { errors.insert("invalid_setup_detail"); continue }
        let rc=cell.advanced(by:16).withMemoryRebound(to:Int64.self,capacity:1){$0.pointee}
        let value=cell.advanced(by:40).withMemoryRebound(to:UInt64.self,capacity:1){$0.pointee}
        result.operations.append(PWRunnerAuthorityOperation(slot:i,operation:PWAuthoritySetupLayout.names[i],
            role:flags & 8 != 0 ? "cleanup":"setup",state:s,native_kind:k,
            native_rc:flags & 1 != 0 ? rc:nil,errno:flags & 2 != 0 ? readI32(cell,offset:24):nil,
            detail:detailName,value:flags & 4 != 0 ? value:nil))
    }
    if decision==1 {
        let d=u32(base,4),primary=u32(base,8)
        if let disposition=[1:"ready",2:"not_required",3:"terminal_required_failure"][Int(d)], primary<=13,
           (d != 3 || (required && primary>0)), (d != 1 || required), (d != 2 || !required) {
            result.publication="observed";result.disposition=disposition
            if primary>0 { result.primary_operation=Int(primary-1) }
            if primary>0 && !result.operations.contains(where:{$0.slot==Int(primary-1) && ["failed","rejected"].contains($0.state)}) { errors.insert("setup_primary_unpublished") }
        } else { errors.insert("invalid_setup_decision") }
    } else if decision != 0 { errors.insert("invalid_setup_publication") }
    if let close=result.operations.first(where:{$0.slot==9}) { result.ownership["descriptor"]=close.state=="succeeded" ? "released":"unresolved" }
    else if result.operations.contains(where:{$0.slot==4 && $0.detail==nil}) { result.ownership["descriptor"]="held" }
    if result.operations.contains(where:{$0.slot==8 && $0.state=="succeeded"}) { result.ownership["mapping"]="held" }
    if let unmap=result.operations.first(where:{$0.slot==12}) { result.ownership["mapping"]=unmap.state=="succeeded" ? "released":"unresolved" }
    if result.operations.contains(where:{$0.slot==11}) { result.ownership["shared_erasure"]="performed" }
    if !errors.isEmpty { result.integrity_errors=errors.sorted() }
    return result
}

struct ActorTerminationDependency {
    let sourceActorIndex: Int
    let sourceFinalPhaseIndex: Int
}
struct ActorTerminationGateRecord {
    let sourceActorIndex: Int
    let sourceFinalPhaseIndex: Int
    var outcome="not_reached"
    var wait: PWHostWait? = nil
    var observation: PWOwnedReapObservation? = nil
    var activationEligible=false
    var captureOrdinal:UInt64? = nil
}
