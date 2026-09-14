import Foundation
import CryptoKit
@testable import PWRunnerCore

// Construct wire bytes independently of the reader: changes to what is selected
// and changes outside that selection must have different effects.
func runAppliedProfileCaptureTests(_ tk: TestKit) {
    tk.group("Applied-profile capture: bounded worker receipt") {
        let source = "(version 1)(allow default)"
        let params = [CWorkerParam(key: "TARGET", value: "/a")]
        let nonce = "00112233445566778899aabbccddeeff"
        func fixture() -> [UInt8] {
            var b = [UInt8](repeating: 0, count: PWShmLayout.captureHeaderBytes + PWShmLayout.captureBytes)
            func word(_ offset: Int, _ n: UInt32) {
                for i in 0..<4 { b[offset + i] = UInt8(truncatingIfNeeded: n >> (8 * i)) }
            }
            func digest(_ offset: Int, _ bytes: Data) { b.replaceSubrange(offset..<(offset + 32), with: Array(SHA256.hash(data: bytes))) }
            word(0, 1); word(4, 1); word(12, 3); word(16, 4321)
            word(20, UInt32(source.utf8.count)); word(24, 1)
            digest(32, Data(source.utf8))
            // LE lengths and literal bytes; do not ask consumedParamsDigest to
            // manufacture the digest which that same function will validate.
            let pair = Data([6,0,0,0]) + Data("TARGET".utf8) + Data([2,0,0,0]) + Data("/a".utf8)
            digest(64, Data([1,0,0,0]) + Data(SHA256.hash(data: pair)))
            digest(96, Data([10,20,30]))
            b.replaceSubrange(128..<144, with: stride(from: 0, through: 255, by: 17).map(UInt8.init))
            b.replaceSubrange(144..<147, with: [10,20,30])
            return b
        }
        func read(_ b: [UInt8], applied: Bool = true, rc: Int32 = 0, done: Bool = true,
                  exit: Int32? = 0, signal: Int32? = nil) -> AppliedProfileCapture {
            b.withUnsafeBufferPointer {
                decodeProfileCapture($0.baseAddress!, workerPid: 4321, applied: applied, applyRC: rc,
                    done: done, exitCode: exit, termSignal: signal, source: source, params: params, nonce: nonce)
            }
        }
        tk.run("capture preserves selected bytes; padding and unselected bytes are ignored") {
            var b = fixture()
            let first = read(b)
            try expectEqual(first.status, "captured")
            try expectEqual(first.bytecode_b64, Data([10,20,30]).base64EncodedString())
            b[28] = 99; b[147] = 88
            try expectEqual(read(b).bytecode_b64, first.bytecode_b64)
            b[145] = 21
            b.replaceSubrange(96..<128, with: Array(SHA256.hash(data: Data([10,21,30]))))
            try expectEqual(read(b).status, "captured")
            try expect(read(b).bytecode_sha256 != first.bytecode_sha256, "changed actual object must change the receipt")
        }
        for (name, offset) in [("completion",0), ("status",4), ("type",8), ("PID",16),
            ("source length",20), ("param count",24), ("source digest",32),
            ("params digest",64), ("payload digest",96), ("nonce",128), ("payload",144)] {
            tk.run("rejects corrupt \(name) without publishing bytecode") {
                var b = fixture(); b[offset] ^= 1
                let r = read(b)
                try expectEqual(r.status, "unavailable")
                try expectNil(r.bytecode_b64); try expectNil(r.bytecode_sha256)
            }
        }
        for length: UInt32 in [0, UInt32(PWShmLayout.captureBytes + 1), UInt32.max] {
            tk.run("refuses invalid extent \(length) before payload read") {
                var b = fixture()
                for i in 0..<4 { b[12+i] = UInt8(truncatingIfNeeded: length >> (8*i)) }
                try expectEqual(read(b).reason, "capture_extent_or_type_invalid")
            }
        }
        tk.run("successful capture cannot turn failed apply or incomplete/dead worker into availability") {
            let b = fixture()
            try expectEqual(read(b, applied: false).status, "unavailable")
            try expectEqual(read(b, rc: -1).status, "unavailable")
            try expectEqual(read(b, done: false).status, "unavailable")
            try expectEqual(read(b, exit: nil, signal: 9).status, "unavailable")
        }
        tk.run("dictionary identity reads consumed values and ignores pair order") {
            let a = [CWorkerParam(key: "a", value: "é"), CWorkerParam(key: "z", value: "2")]
            try expectEqual(consumedParamsDigest(a), consumedParamsDigest(a.reversed()))
            var changed = a; changed[0].value = "e"
            try expect(consumedParamsDigest(a) != consumedParamsDigest(changed))
        }
        tk.run("capture is opt-in and round-trips with a nonce") {
            let plain = PWRunnerPolicySpec(format: "sbpl", sbpl_source: source)
            try expectNil(plain.capture_applied_profile)
            let requested = PWRunnerPolicySpec(format: "sbpl", sbpl_source: source,
                capture_applied_profile: true, capture_nonce: nonce)
            let decoded = try JSONDecoder().decode(PWRunnerPolicySpec.self, from: JSONEncoder().encode(requested))
            try expectEqual(decoded.capture_nonce, nonce)
            let receipt = try JSONDecoder().decode(AppliedProfileCapture.self, from: JSONEncoder().encode(read(fixture())))
            try expectEqual(receipt.bytecode_b64, Data([10,20,30]).base64EncodedString())
            try expectEqual(receipt.request_nonce, nonce)
        }
        tk.run("capture nonce is required and validated before spawn") {
            for n: String? in [nil, "", String(repeating: "A", count: 32), String(repeating: "0", count: 31)] {
                let input = CWorkerInput(workerExecutablePath: "/nonexistent", policy: source, slots: [],
                    captureAppliedProfile: true, captureNonce: n)
                guard case .failure(.captureNonceInvalid) = runCWorker(input) else {
                    throw TestFailure(message: "invalid nonce reached worker spawn")
                }
            }
        }
    }
}
