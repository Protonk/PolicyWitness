import Darwin
import Foundation
@testable import PWRunnerCore

// Independent test input, not reconstructed from the receiver's output or enums.
private func transportInputs() throws -> [String: Any] {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    return try JSONSerialization.jsonObject(with: Data(contentsOf:
        root.appendingPathComponent("tests/fixtures/diagnostic_transport/cases.json"))) as! [String: Any]
}

func runDiagnosticTransportTests(_ tk: TestKit) {
    tk.group("unfamiliar diagnostic transport") {
        tk.run("independent ABI bytes preserve both open codes and distinct payloads through Codable") {
            for input in try transportInputs()["worker"] as! [[String: Any]] {
                let f = input["failure"] as! [String: Any]
                let progress = input["progress"] as! [String: Any]
                let text = input["text"] as! String
                let raw = UnsafeMutableRawPointer.allocate(byteCount: PWShmLayout.regionBytes, alignment: 8)
                defer { raw.deallocate() }
                raw.initializeMemory(as: UInt8.self, repeating: 0, count: PWShmLayout.regionBytes)
                func word(_ offset: Int, _ value: UInt32) { raw.storeBytes(of: value, toByteOffset: offset, as: UInt32.self) }
                let e = PWShmLayout.evidenceOffset
                word(0, 6)
                for (key, offset) in [("operation", PWShmLayout.evidenceOperationOffset),
                    ("code", PWShmLayout.evidenceCodeOffset), ("native_kind", PWShmLayout.evidenceNativeKindOffset),
                    ("detail", PWShmLayout.evidenceDetailOffset)] {
                    word(e + offset, (f[key] as! NSNumber).uint32Value)
                }
                word(e + PWShmLayout.evidenceNativeResultOffset, UInt32(bitPattern: (f["native_result"] as! NSNumber).int32Value))
                word(e + PWShmLayout.evidenceErrnoValOffset, (f["errno"] as! NSNumber).uint32Value)
                word(e + PWShmLayout.evidenceErrnoPresentOffset, 1)
                word(e + PWShmLayout.evidenceItemIndexOffset, (f["index"] as? NSNumber)?.uint32Value ?? UInt32.max)
                let index = (progress["index"] as? NSNumber)?.uint32Value
                word(e + PWShmLayout.evidenceProgressOffset,
                     (progress["operation"] as! NSNumber).uint32Value << 24 | 2 << 20 | (index.map { $0 + 1 } ?? 0))
                word(e + PWShmLayout.evidenceFailurePublishedOffset, 1)
                word(e + PWShmLayout.evidenceDiagnosticStateOffset, 1)
                word(e + PWShmLayout.evidenceDiagnosticLengthOffset, UInt32(text.utf8.count))
                for (i, byte) in text.utf8.enumerated() {
                    raw.storeBytes(of: byte, toByteOffset: e + PWShmLayout.evidenceHeaderBytes + i, as: UInt8.self)
                }
                let base = raw.assumingMemoryBound(to: UInt8.self)
                guard let evidence = decodeWorkerEvidence(base) else { throw TestFailure(message: "supported ABI rejected") }
                let bytes = try pwRunnerEncodeJSON(evidence)
                let decoded = try pwRunnerDecodeJSON(PWWorkerEvidence.self, from: bytes)
                guard let wire = try JSONSerialization.jsonObject(with: pwRunnerEncodeJSON(decoded)) as? [String: Any],
                      let forwardedFailure = wire["failure"] as? [String: Any] else {
                    throw TestFailure(message: "unfamiliar failure record missing after forwarding")
                }
                try expectTrue(NSDictionary(dictionary: forwardedFailure).isEqual(to: f), "unfamiliar payload changed: \(wire)")
                try expectEqual(decoded.diagnostic.text, text)
                try expectEqual(decoded.diagnostic.length, UInt32(text.utf8.count))
                try expectEqual(decoded.progress?.operation, (progress["operation"] as! NSNumber).uint32Value)
                try expectEqual(decoded.progress?.index, index)
                // Recognition and structural acceptance are independent.
                for (publication, state): (UInt32, String) in [(0, "absent"), (2, "incomplete"), (9, "invalid")] {
                    word(e + PWShmLayout.evidenceFailurePublishedOffset, publication)
                    try expectEqual(decodeWorkerEvidence(base)?.failure_state, state)
                    try expectNil(decodeWorkerEvidence(base)?.failure)
                }
                word(e + PWShmLayout.evidenceFailurePublishedOffset, 1)
                word(e + PWShmLayout.evidenceErrnoPresentOffset, 2)
                try expectEqual(decodeWorkerEvidence(base)?.failure_state, "invalid")
                word(e + PWShmLayout.evidenceErrnoPresentOffset, 1)
                word(0, 7)
                try expectNil(decodeWorkerEvidence(base))
            }
        }
        tk.run("validator open diagnostics survive host encoding beside a known decode failure") {
            let inputs = try transportInputs()["diagnostics"] as! [[String: Any]]
            var bytes = Data()
            for (i, input) in inputs.enumerated() {
                let record: [String: Any] = ["kind": "sb_api_validator_verdict", "schema_version": 1,
                    "step_id": "s\(i)", "outcome": "future_transport_\(i)", "error": "controlled diagnostic",
                    "diagnostic": input]
                bytes.append(try JSONSerialization.data(withJSONObject: record)); bytes.append(10)
            }
            bytes.append(contentsOf: [255, 10])
            let received = decodeValidatorFrames(bytes)
            try expectEqual(received.fault?.kind, "utf8")
            try expectEqual(received.verdicts.count, 2)
            let out = ValidatorOutput(validatorPid: 321, verdicts: received.verdicts,
                exitCode: 0, reaped: true, waitErrors: [], decodeFault: received.fault,
                expectedProbes: (0..<2).map { ValidatorProbe(stepId: "s\($0)", operation: "file-read-data", filterType: "NONE") })
            let forwarded = try pwRunnerDecodeJSON(PWRunnerValidatorSubprocess.self,
                from: pwRunnerEncodeJSON(buildValidatorSubprocess(out)))
            try expectEqual(forwarded.pid, 321)
            try expectEqual(forwarded.decode_fault?.kind, "utf8")
            for (i, v) in (forwarded.records ?? []).enumerated() {
                guard let original = try JSONSerialization.jsonObject(with: Data(v.rawLine.utf8)) as? [String: Any],
                      let diagnostic = original["diagnostic"] as? [String: Any] else {
                    throw TestFailure(message: "validator diagnostic missing after forwarding")
                }
                try expectTrue(NSDictionary(dictionary: diagnostic).isEqual(to: inputs[i]))
                try expectNil(v.rc)
                try expectEqual(v.outcome, "future_transport_\(i)")
            }
            try expectEqual(forwarded.records?.count, 2)
        }
    }
}
