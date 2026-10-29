import Foundation
import Darwin

/// Versioned optional receipt for the exact compiler result supplied to apply.
/// `captured` requires a complete, checksum-verified worker capture and successful
/// application/process completion. This is not a readback of kernel state.
struct CompiledProfileCapture: Codable {
    var schema_version: Int = 2
    var status: String
    var reason: String?
    var worker_pid: Int
    var producer: String? = nil
    var capture_stage: String? = nil
    var request_nonce: String?
    var profile_type: Int?
    var bytecode_length: Int?
    var bytecode_sha256: String?
    var bytecode_b64: String?
    var source_sha256: String?
    var source_length: Int?
    var params_sha256: String?
    var parameter_count: Int?
}


// Keep context validation at the receipt boundary, including direct decoding
// and evidence-preserving reply encoding. No absent context implies a stage.
extension CompiledProfileCapture {
    var contextProblem: String? {
        guard schema_version == 2 else { return "unsupported compiled_profile schema_version" }
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
    enum CodingKeys: String, CodingKey {
        case schema_version, status, reason, worker_pid, producer, capture_stage, request_nonce, profile_type, bytecode_length, bytecode_sha256, bytecode_b64, source_sha256, source_length, params_sha256, parameter_count
    }
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        schema_version = try c.decode(Int.self, forKey: .schema_version)
        status = try c.decode(String.self, forKey: .status)
        reason = try c.decodeIfPresent(String.self, forKey: .reason)
        worker_pid = try c.decode(Int.self, forKey: .worker_pid)
        producer = try c.decodeIfPresent(String.self, forKey: .producer)
        capture_stage = try c.decodeIfPresent(String.self, forKey: .capture_stage)
        request_nonce = try c.decodeIfPresent(String.self, forKey: .request_nonce)
        profile_type = try c.decodeIfPresent(Int.self, forKey: .profile_type)
        bytecode_length = try c.decodeIfPresent(Int.self, forKey: .bytecode_length)
        bytecode_sha256 = try c.decodeIfPresent(String.self, forKey: .bytecode_sha256)
        bytecode_b64 = try c.decodeIfPresent(String.self, forKey: .bytecode_b64)
        source_sha256 = try c.decodeIfPresent(String.self, forKey: .source_sha256)
        source_length = try c.decodeIfPresent(Int.self, forKey: .source_length)
        params_sha256 = try c.decodeIfPresent(String.self, forKey: .params_sha256)
        parameter_count = try c.decodeIfPresent(Int.self, forKey: .parameter_count)
        if let problem = contextProblem {
            throw DecodingError.dataCorrupted(.init(codingPath: decoder.codingPath, debugDescription: problem))
        }
    }
    func encode(to encoder: Encoder) throws {
        if let problem = contextProblem {
            throw EncodingError.invalidValue(self, .init(codingPath: encoder.codingPath, debugDescription: problem))
        }
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(schema_version, forKey: .schema_version)
        try c.encode(status, forKey: .status)
        try c.encodeIfPresent(reason, forKey: .reason)
        try c.encode(worker_pid, forKey: .worker_pid)
        try c.encodeIfPresent(producer, forKey: .producer)
        try c.encodeIfPresent(capture_stage, forKey: .capture_stage)
        try c.encodeIfPresent(request_nonce, forKey: .request_nonce)
        try c.encodeIfPresent(profile_type, forKey: .profile_type)
        try c.encodeIfPresent(bytecode_length, forKey: .bytecode_length)
        try c.encodeIfPresent(bytecode_sha256, forKey: .bytecode_sha256)
        try c.encodeIfPresent(bytecode_b64, forKey: .bytecode_b64)
        try c.encodeIfPresent(source_sha256, forKey: .source_sha256)
        try c.encodeIfPresent(source_length, forKey: .source_length)
        try c.encodeIfPresent(params_sha256, forKey: .params_sha256)
        try c.encodeIfPresent(parameter_count, forKey: .parameter_count)
    }
}
