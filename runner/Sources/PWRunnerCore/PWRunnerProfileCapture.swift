import Foundation
import Darwin

/// Optional receipt for the exact compiler result supplied to apply. It has no
/// version or contract field; the enclosing reply identifies the producing build.
/// `captured` requires a complete, checksum-verified worker capture and successful
/// application/process completion. This is not a readback of kernel state.
struct CompiledProfileCapture {
    // BEGIN GENERATED PORCELAIN CompiledProfileCapture
    var status: String
    var reason: String?
    var worker_pid: Int
    var producer: String? = nil
    var capture_stage: String? = nil
    var request_nonce: String?
    var profile_type: Int?
    var bytecode_length: Int?
    var bytecode_sha256: Data?
    var bytecode: Data?
    var source_sha256: Data?
    var source_length: Int?
    var params_sha256: Data?
    var parameter_count: Int?
    // END GENERATED PORCELAIN CompiledProfileCapture
}


// Keep context validation at the receipt boundary, for ordinary and
// evidence-preserving reporting. No absent context implies a stage.
extension CompiledProfileCapture {
    var contextProblem: String? {
        switch status {
        case "captured":
            guard producer == "worker", capture_stage == "before_apply" else {
                return "compiled_profile requires worker/before_apply context"
            }
        case "unavailable":
            guard producer == nil, capture_stage == nil else {
                return "unavailable compiled_profile cannot claim capture context"
            }
        default: return "invalid compiled_profile status"
        }
        return nil
    }
    func validateForReporting() throws {
        if let problem = contextProblem {
            throw PWRunnerReportingValidationError(message: problem)
        }
    }
}
