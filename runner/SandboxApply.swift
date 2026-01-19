import Foundation
import CryptoKit
import Darwin

// Policy hashing and single-shot sandbox apply path.
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

struct ApplyError: Error, CustomStringConvertible {
    var message: String

    var description: String { message }
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

func applySandboxPolicy(
    _ policy: PWRunnerPolicySpec,
    sandboxLib: SandboxLib
) -> Result<Void, ApplyError> {
    // `sandbox_set_param` is an underspecified private API. Keep key/value C
    // strings alive until compilation completes to avoid relying on copy rules.
    var paramCStringAllocs: [UnsafeMutablePointer<CChar>] = []
    defer {
        for ptr in paramCStringAllocs {
            free(ptr)
        }
    }

    // Create params if present.
    let paramsObj: SandboxLib.SandboxParams?
    if let params = policy.params, !params.isEmpty {
        guard let obj = sandboxLib.createParams() else {
            return .failure(ApplyError(message: "sandbox_create_params failed (returned NULL)"))
        }
        for (key, value) in params.sorted(by: { $0.key < $1.key }) {
            guard let keyDup = strdup(key) else {
                sandboxLib.freeParams(obj)
                return .failure(ApplyError(message: "strdup failed for param key"))
            }
            guard let valueDup = strdup(value) else {
                free(keyDup)
                sandboxLib.freeParams(obj)
                return .failure(ApplyError(message: "strdup failed for param value"))
            }
            paramCStringAllocs.append(keyDup)
            paramCStringAllocs.append(valueDup)

            let rc: Int32 = sandboxLib.setParam(obj, keyDup, valueDup)
            if rc != 0 {
                sandboxLib.freeParams(obj)
                return .failure(
                    ApplyError(message: "sandbox_set_param failed for key \(key): rc=\(rc)")
                )
            }
        }
        paramsObj = obj
    } else {
        paramsObj = nil
    }
    defer { sandboxLib.freeParams(paramsObj) }

    switch policy.format {
    case PWRunnerWire.policyFormatSbpl:
        guard let src = policy.sbpl_source else {
            return .failure(ApplyError(message: "missing policy.sbpl_source"))
        }
        var errBuf: UnsafeMutablePointer<CChar>?
        let profile: SandboxLib.SandboxProfile? = src.withCString { cStr in
            sandboxLib.compileString(cStr, paramsObj, &errBuf)
        }
        if let errBuf {
            let message = String(cString: errBuf)
            sandboxLib.freeError(errBuf)
            return .failure(ApplyError(message: "sandbox_compile_string failed: \(message)"))
        }
        guard let profile else {
            return .failure(ApplyError(message: "sandbox_compile_string failed (no profile and no error)"))
        }
        defer { sandboxLib.freeProfile(profile) }
        let rc = sandboxLib.apply(profile)
        if rc != 0 {
            return .failure(ApplyError(message: "sandbox_apply failed: \(String(cString: strerror(errno)))"))
        }
        return .success(())

    default:
        return .failure(ApplyError(message: "unknown policy.format (expected sbpl)"))
    }
}
