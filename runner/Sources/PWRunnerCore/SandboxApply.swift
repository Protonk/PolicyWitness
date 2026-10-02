import Foundation
import CryptoKit
import Darwin

// Policy source hashing and the structural refusal of a policy the host
// cannot identify. The host never compiles or applies a policy itself.
private func sha256Hex(_ data: Data) -> String {
    let digest = SHA256.hash(data: data)
    return digest.map { String(format: "%02x", $0) }.joined()
}

enum PolicyHashError: Error, CustomStringConvertible {
    case missingField(String)

    var description: String {
        switch self {
        case .missingField(let field):
            return "missing policy field: \(field)"
        }
    }
}

func computePolicyHash(_ policy: PWRunnerPolicySpec) throws -> String {
    switch policy.format {
    case PWRunnerWire.policyFormatSbpl:
        guard let src = policy.sbpl_source else {
            throw PolicyHashError.missingField("sbpl_source")
        }
        return sha256Hex(Data(src.utf8))
    default:
        throw PolicyHashError.missingField("format (expected sbpl)")
    }
}
