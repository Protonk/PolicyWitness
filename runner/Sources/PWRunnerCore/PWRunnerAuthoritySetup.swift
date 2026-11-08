import Foundation
import Darwin

/// Bounded authority setup observations. Bearer bytes and mapping addresses never enter these records.
struct PWRunnerAuthorityOperation: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerAuthorityOperation
    var slot: Int
    var operation: String
    var role: String
    var state: String
    var native_kind: String?
    var native_rc: Int64?
    var errno: Int32?
    var detail: String?
    var value: UInt64?
    // END GENERATED PORCELAIN PWRunnerAuthorityOperation
}
struct PWAuthorityCleanupReference: Equatable {
    // BEGIN GENERATED PORCELAIN PWAuthorityCleanupReference
    var kind: String = "posix_shm_name"
    var name: String
    var host_pid: Int
    var session_nonce: UInt64
    /// A receipt cannot establish identity after name reuse. No automatic unlink is authorized.
    var recovery_state: String = "unresolved_manual"
    // END GENERATED PORCELAIN PWAuthorityCleanupReference
}
struct PWRunnerAuthorityScope: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerAuthorityScope
    var actor_id: String? = nil
    var actor_index: Int? = nil
    var token_ref: String? = nil
    var token_index: Int? = nil
    var required: Bool? = nil
    var publication: String? = nil
    var disposition: String? = nil
    var primary_operation: Int? = nil
    var operations: [PWRunnerAuthorityOperation] = []
    var ownership: [String: String] = [:]
    var cleanup_reference: PWAuthorityCleanupReference? = nil
    var integrity_errors: [String]? = nil
    // END GENERATED PORCELAIN PWRunnerAuthorityScope
}
struct PWRunnerAuthorityHost: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerAuthorityHost
    var run: PWRunnerAuthorityScope
    var regions: [PWRunnerAuthorityScope] = []
    var custody: [PWRunnerAuthorityScope] = []
    // END GENERATED PORCELAIN PWRunnerAuthorityHost
}
struct PWRunnerAuthoritySetup: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerAuthoritySetup
    var host: PWRunnerAuthorityHost
    var workers: [PWRunnerAuthorityScope]
    // END GENERATED PORCELAIN PWRunnerAuthoritySetup
    mutating func bind(actorIDs: [String], tokenRefs: [String]) {
        for i in workers.indices { if let index=workers[i].actor_index, actorIDs.indices.contains(index) { workers[i].actor_id=actorIDs[index] } }
        for i in host.regions.indices { if let index=host.regions[i].actor_index, actorIDs.indices.contains(index) { host.regions[i].actor_id=actorIDs[index] } }
        for i in host.custody.indices { if let index=host.custody[i].token_index, tokenRefs.indices.contains(index) { host.custody[i].token_ref=tokenRefs[index] } }
    }
}

struct PWOwnedReapObservation: Equatable {
    // BEGIN GENERATED PORCELAIN PWOwnedReapObservation
    var pid: Int
    var native_rc: Int32
    var raw_status: Int32
    var stage: String
    var observed_ns: UInt64?
    var ownership_unbroken: Bool
    var departure_requested: Bool
    var capture_ordinal: UInt64 = 0
    // END GENERATED PORCELAIN PWOwnedReapObservation
}
/// Ordinals share the source child's host-observation sequence. They are not
/// worker publications and do not count polling calls.
struct PWRunnerActorActivation: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerActorActivation
    var capture_ordinal: UInt64
    var observed_ns: UInt64?
    // END GENERATED PORCELAIN PWRunnerActorActivation
}
struct PWOwnedReapReference: Equatable {
    // BEGIN GENERATED PORCELAIN PWOwnedReapReference
    var capture_ordinal: UInt64
    // END GENERATED PORCELAIN PWOwnedReapReference
}

struct PWRunnerActorApplication: Equatable {
    // BEGIN GENERATED PORCELAIN PWRunnerActorApplication
    var state: String
    var basis: String
    // END GENERATED PORCELAIN PWRunnerActorApplication
}
struct PWRunnerTerminationGate {
    // BEGIN GENERATED PORCELAIN PWRunnerTerminationGate
    var source_actor_id: String
    var source_final_phase_id: String
    var condition: String = "terminated"
    var outcome: String
    var wait: PWHostWait?
    var observation: PWOwnedReapReference?
    var activation_eligible: Bool
    var capture_ordinal: UInt64? = nil
    // END GENERATED PORCELAIN PWRunnerTerminationGate
}

/// The terminal failure whitelist describes branches, not absent status fields.
func actorApplicationAssessment(mode: String, launched: Bool, applied: Bool,
                                evidence: PWWorkerEvidence?, authority: PWRunnerAuthorityScope?) -> PWRunnerActorApplication {
    func answer(_ state:String,_ basis:String)->PWRunnerActorApplication { PWRunnerActorApplication(state:state,basis:basis) }
    if mode=="unapplied" { return answer("not_requested","unapplied_declaration") }
    if !launched { return answer("not_attempted","worker_not_launched") }
    if applied { return answer("observed","applied_publication") }
    if authority?.publication=="observed",authority?.disposition=="terminal_required_failure",authority?.integrity_errors==nil {
        return answer("not_attempted","terminal_authority_setup_refusal")
    }
    if evidence?.failure_state=="published",let f=evidence?.failure {
        if f.operation==8 && f.code==1 && f.native_kind==1,let rc=f.native_result,rc != 0 {
            return answer("observed","apply_failure_publication")
        }
        if (f.operation==1 && [4,7,10,12].contains(f.code) && f.native_kind==0)
            || (f.operation==2 && [2,3,9,13].contains(f.code)) {
            return answer("not_attempted","terminal_input_refusal")
        }
        if (f.operation==1 && f.code==5 && f.native_kind==0)
            || (f.operation==3 && f.code==1 && f.native_kind==2)
            || (f.operation==4 && ((f.code==1 && f.native_kind==1) || (f.code==6 && f.native_kind==0))) {
            return answer("not_attempted","terminal_parameter_refusal")
        }
        if f.operation==5 && f.code==1 && f.native_kind==2 { return answer("not_attempted","terminal_compile_refusal") }
        if f.operation==12 && ((f.code==1 && f.native_kind==1) || (f.code==14 && f.native_kind==0) || (f.code==15 && f.detail==1 && f.native_kind==0)) {
            return answer("not_attempted","terminal_timing_refusal")
        }
    }
    if let p=evidence?.progress,p.operation==8,[1,2].contains(p.stage) {
        return answer("unobserved","apply_call_boundary_without_result")
    }
    return answer("unobserved","no_eligible_apply_publication")
}

func authoritySetupIntegrityErrors(_ setup: PWRunnerAuthoritySetup, actorIDs: [String], tokenRefs: [String]) -> [String] {
    var errors=Set<String>()
    let host=setup.host
    if actorIDs.count>8 || tokenRefs.count>32 || setup.workers.count != actorIDs.count || host.regions.count>8 || host.custody.count>32 { errors.insert("authority_setup_capacity") }
    let workerNames=["issue_symbol","consume_symbol","release_symbol","core_limit","descriptor_presence","fstat","page_size","object_size","mmap","descriptor_close","header_binding","terminal_owned_inbound_clear","rejected_mapping_munmap"]
    let regionNames=["shm_open","shm_unlink","fd_cloexec","ftruncate","mmap","header_initialize","authority_duplicate","authority_spawn_dup2","close_launch_duplicate","close_original_descriptor","shared_clear","munmap"]
    let custodyNames=["mmap","final_erase","munmap"]
    func check(_ scope:PWRunnerAuthorityScope,_ names:[String],_ capacity:Int,_ owner:String) {
        if scope.operations.count>capacity || Set(scope.operations.map{$0.slot}).count != scope.operations.count { errors.insert("authority_operation_capacity") }
        if scope.integrity_errors != nil { errors.insert("authority_publication_integrity") }
        let states:Set<String>=["succeeded","failed","accepted","rejected","available","unavailable","performed","not_attempted"]
        for o in scope.operations {
            guard names.indices.contains(o.slot),names[o.slot]==o.operation,states.contains(o.state),["setup","cleanup"].contains(o.role) else { errors.insert("authority_operation_shape");continue }
            let expectedKinds: [String]
            switch owner {
            case "worker": expectedKinds=["symbol","symbol","symbol","integer","validation","integer","integer","validation","mapping","integer","validation","memory","integer"]
            case "region": expectedKinds=["integer","integer","integer","integer","mapping","memory","integer","error_code","integer","integer","memory","integer"]
            case "custody": expectedKinds=["mapping","memory","integer"]
            default: expectedKinds=["integer"]
            }
            if o.native_kind != expectedKinds[o.slot] { errors.insert("authority_operation_kind") }
            let allowedStates: [String:Set<String>]=["integer":["succeeded","failed"],"error_code":["succeeded","failed"],"mapping":["succeeded","failed"],"symbol":["available","unavailable"],"validation":["accepted","rejected"],"memory":["performed"]]
            if o.state=="not_attempted" {
                if o.native_rc != nil || o.errno != nil || o.value != nil { errors.insert("authority_unattempted_result") }
            } else {
                if allowedStates[expectedKinds[o.slot]]?.contains(o.state) != true { errors.insert("authority_operation_state") }
                if ["integer","error_code"].contains(expectedKinds[o.slot]) && o.native_rc==nil { errors.insert("authority_native_return_missing") }
                if o.state=="failed" && ["integer","mapping"].contains(expectedKinds[o.slot]) && o.errno==nil { errors.insert("authority_errno_missing") }
            }
            if o.errno != nil && (o.state != "failed" || !["integer","mapping"].contains(o.native_kind ?? "")) { errors.insert("authority_errno_ownership") }
            if o.native_rc != nil && !["integer","error_code"].contains(o.native_kind ?? "") { errors.insert("authority_native_return_ownership") }
            if ["validation","symbol","memory"].contains(o.native_kind ?? "") && (o.native_rc != nil || o.errno != nil) { errors.insert("authority_non_native_result") }
            if owner=="worker",o.slot != 9,(o.role=="cleanup") != [11,12].contains(o.slot) { errors.insert("authority_operation_role") }
            if owner=="region",(o.role=="cleanup") != [8,9,10,11].contains(o.slot) { errors.insert("authority_operation_role") }
            if owner=="custody",(o.role=="cleanup") != [1,2].contains(o.slot) { errors.insert("authority_operation_role") }
        }
        if let primary=scope.primary_operation,!scope.operations.contains(where:{$0.slot==primary && ["failed","rejected"].contains($0.state)}) { errors.insert("authority_primary_missing") }
        let referenceStates:Set<String>=["not_acquired","held","released","unresolved"]
        let eraseStates:Set<String>=["not_present","performed","withheld_not_quiescent","unobserved"]
        for (key,value) in scope.ownership {
            if ["object_name","descriptor","mapping"].contains(key) { if !referenceStates.contains(value) { errors.insert("authority_reference_state") } }
            else if ["shared_erasure","private_erasure"].contains(key) { if !eraseStates.contains(value) { errors.insert("authority_erase_state") } }
            else { errors.insert("authority_ownership_key") }
        }
        if let reference=scope.cleanup_reference {
            if owner != "region" || reference.kind != "posix_shm_name" || reference.recovery_state != "unresolved_manual"
                || reference.name.utf8.count>31 || !reference.name.hasPrefix("/") || reference.name.contains("\0")
                || !scope.operations.contains(where:{$0.slot==0 && $0.state=="succeeded"})
                || !scope.operations.contains(where:{$0.slot==1 && $0.state=="failed"}) { errors.insert("authority_cleanup_reference") }
        }
    }
    check(host.run,["core_limit"],4,"run")
    for r in host.regions { check(r,regionNames,16,"region") }
    for c in host.custody { check(c,custodyNames,4,"custody") }
    for (i,w) in setup.workers.enumerated() {
        check(w,workerNames,16,"worker")
        if w.actor_index != i || !actorIDs.indices.contains(i) || w.actor_id != actorIDs[i] { errors.insert("authority_actor_association") }
        if w.publication=="not_observed" {
            if w.disposition != nil || w.primary_operation != nil { errors.insert("authority_unpublished_decision") }
        } else if w.publication=="observed" {
            if !["ready","not_required","terminal_required_failure"].contains(w.disposition ?? "") { errors.insert("authority_decision") }
            if w.disposition=="terminal_required_failure" && (w.required != true || w.primary_operation==nil) { errors.insert("authority_terminal_decision") }
        } else { errors.insert("authority_publication") }
    }
    for r in host.regions {
        if let i=r.actor_index,actorIDs.indices.contains(i),r.actor_id==actorIDs[i] {} else { errors.insert("authority_actor_association") }
    }
    for c in host.custody {
        if let i=c.token_index,tokenRefs.indices.contains(i),c.token_ref==tokenRefs[i] {} else { errors.insert("authority_token_association") }
    }
    return errors.sorted()
}

func actorApplicationIntegrityErrors(_ application: PWRunnerActorApplication, mode: String, launched: Bool,
                                    applied: Bool, evidence: PWWorkerEvidence?, authority: PWRunnerAuthorityScope?) -> [String] {
    let expected=actorApplicationAssessment(mode:mode,launched:launched,applied:applied,evidence:evidence,authority:authority)
    var errors:[String]=[]
    if expected != application { errors.append("application_assessment_source") }
    if applied && (mode=="unapplied" || !launched || authority?.disposition=="terminal_required_failure") { errors.append("contradictory_application_publication") }
    if applied,let f=evidence?.failure,evidence?.failure_state=="published",[1,2,3,4,5,8,12].contains(f.operation) { errors.append("contradictory_application_failure") }
    return errors
}

func terminationGateIntegrityErrors(_ gate: PWRunnerTerminationGate, activationStored: Bool, collectionInvoked: Bool, releaseStored: Bool) -> [String] {
    let outcomes:Set<String>=["not_reached","satisfied","timed_out","ownership_lost","clock_unavailable","source_unavailable","source_departure_requested","execution_allowance_exhausted"]
    var errors:[String]=[]
    if gate.condition != "terminated" || !outcomes.contains(gate.outcome) { errors.append("termination_gate_shape") }
    if gate.activation_eligible && gate.outcome != "satisfied" { errors.append("termination_gate_eligibility") }
    if (activationStored || collectionInvoked || releaseStored) && !gate.activation_eligible { errors.append("activation_before_termination_gate") }
    if let wait=gate.wait,wait.budget_ms<0 || wait.budget_ms>5000 || wait.excluded_ms != nil { errors.append("termination_gate_budget") }
    if gate.outcome != "not_reached" && gate.wait?.stop != gate.outcome { errors.append("termination_gate_wait") }
    if gate.outcome=="not_reached" && (gate.observation != nil || gate.capture_ordinal != nil || gate.wait != nil) { errors.append("termination_gate_unreached_capture") }
    if gate.outcome=="satisfied" {
        if let o=gate.observation, let capture=gate.capture_ordinal {
            if o.capture_ordinal==0 || o.capture_ordinal>=capture { errors.append("termination_gate_reap") }
        } else { errors.append("termination_gate_reap") }
        if let wait=gate.wait {
            if wait.clock_fault || wait.elapsed_ms==nil || wait.budget_ms<=0 || wait.stop != "satisfied"
                || wait.native_errno != nil || (wait.elapsed_ms ?? 0) > UInt64(max(0,wait.budget_ms)) { errors.append("termination_gate_wait") }
        } else { errors.append("termination_gate_wait") }
    }
    return errors
}
