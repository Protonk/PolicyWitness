import Foundation
import CryptoKit
@testable import PWRunnerCore

// Construct wire bytes independently of the reader: changes to what is selected
// and changes outside that selection must have different effects.
func runCompiledProfileCaptureTests(_ tk: TestKit) {
    tk.group("Compiled-profile capture: bounded worker receipt") {
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
                  exit: Int32? = 0, signal: Int32? = nil) -> CompiledProfileCapture {
            b.withUnsafeBufferPointer {
                decodeProfileCapture($0.baseAddress!, workerPid: 4321, applied: applied, applyRC: rc,
                    done: done, exitCode: exit, termSignal: signal, source: source, params: params, nonce: nonce)
            }
        }
        tk.run("capture status, producer and stage are checked before binary reporting") {
            try read(fixture()).validateForReporting()
            try read(fixture(), done: false).validateForReporting()
            var future = read(fixture()); future.status = "future"
            try expectThrows { try future.validateForReporting() }
            var captured = read(fixture())
            try expectEqual(captured.status, "captured")
            try expectEqual(captured.producer, "worker")
            try expectEqual(captured.capture_stage, "before_apply")
            captured.capture_stage = "after_apply"
            try expectThrows { try captured.validateForReporting() }
            captured = read(fixture()); captured.producer = nil
            try expectThrows { try captured.validateForReporting() }
            var unavailable = read(fixture(), done: false)
            try expectNil(unavailable.producer); try expectNil(unavailable.capture_stage)
            unavailable.capture_stage = "before_apply"
            try expectThrows { try unavailable.validateForReporting() }
        }
        tk.run("capture preserves selected bytes; padding and unselected bytes are ignored") {
            var b = fixture()
            let first = read(b)
            try expectEqual(first.status, "captured")
            try expectEqual(first.bytecode, Data([10,20,30]))
            b[28] = 99; b[147] = 88
            try expectEqual(read(b).bytecode, first.bytecode)
            b[145] = 21
            b.replaceSubrange(96..<128, with: Array(SHA256.hash(data: Data([10,21,30]))))
            try expectEqual(read(b).status, "captured")
            try expect(read(b).bytecode_sha256 != first.bytecode_sha256, "changed actual object must change the receipt")
        }
        // An unavailable receipt carries status, reason and worker_pid only.
        func presentFields(_ r: CompiledProfileCapture) -> [String] {
            Mirror(reflecting: r).children.compactMap { child in
                let value = Mirror(reflecting: child.value)
                return value.displayStyle == .optional && value.children.isEmpty ? nil : child.label
            }
        }
        func withheld(_ r: CompiledProfileCapture, _ reason: String, _ context: String) throws {
            try expectEqual(r.status, "unavailable", context)
            try expectEqual(r.reason, reason, context)
            try expectEqual(r.worker_pid, 4321, context)
            try expectEqual(presentFields(r), ["status", "reason", "worker_pid"], context)
        }
        for (name, offset, reason) in [("completion", 0, "capture_not_complete"), ("status", 4, "worker_capture_refused"),
            ("type", 8, "capture_extent_or_type_invalid"), ("PID", 16, "capture_worker_mismatch"),
            ("source length", 20, "capture_consumed_input_mismatch"), ("param count", 24, "capture_consumed_input_mismatch"),
            ("source digest", 32, "capture_consumed_input_mismatch"), ("params digest", 64, "capture_consumed_input_mismatch"),
            ("payload digest", 96, "capture_bytecode_digest_mismatch"), ("nonce", 128, "capture_nonce_mismatch"),
            ("payload", 144, "capture_bytecode_digest_mismatch")] {
            tk.run("rejects corrupt \(name) without publishing bytecode") {
                var b = fixture(); b[offset] ^= 1
                try withheld(read(b), reason, name)
            }
        }
        for length: UInt32 in [0, UInt32(PWShmLayout.captureBytes + 1), UInt32.max] {
            tk.run("refuses invalid extent \(length) before payload read") {
                var b = fixture()
                for i in 0..<4 { b[12+i] = UInt8(truncatingIfNeeded: length >> (8*i)) }
                try withheld(read(b), "capture_extent_or_type_invalid", "extent \(length)")
            }
        }
        tk.run("successful capture cannot turn failed apply or incomplete/dead worker into availability") {
            let b = fixture()
            try withheld(read(b, applied: false), "successful_application_unconfirmed", "not applied")
            try withheld(read(b, rc: -1), "successful_application_unconfirmed", "apply rc -1")
            try withheld(read(b, done: false), "worker_not_complete", "done not observed")
            try withheld(read(b, exit: nil, signal: 9), "worker_not_complete", "signal 9")
            try withheld(read(b, exit: 1), "worker_not_complete", "exit 1")
        }
        // Two adjacent faults: the earlier guard in the decoder's order names the reason.
        enum Fault { case unapplied, incomplete, byte(Int) }
        let faults: [String: Fault] = ["application": .unapplied, "completion": .incomplete,
            "capture completion": .byte(0), "status": .byte(4), "PID": .byte(16), "nonce": .byte(128),
            "type": .byte(8), "byte digest": .byte(96), "input": .byte(32)]
        for (first, second, reason) in [("application", "completion", "successful_application_unconfirmed"),
            ("completion", "capture completion", "worker_not_complete"),
            ("capture completion", "status", "capture_not_complete"),
            ("status", "PID", "worker_capture_refused"), ("PID", "nonce", "capture_worker_mismatch"),
            ("nonce", "type", "capture_nonce_mismatch"), ("type", "byte digest", "capture_extent_or_type_invalid"),
            ("byte digest", "input", "capture_bytecode_digest_mismatch")] {
            tk.run("\(first) precedes \(second)") {
                var b = fixture(), applied = true, done = true
                for name in [first, second] {
                    switch faults[name]! {
                    case .unapplied: applied = false
                    case .incomplete: done = false
                    case .byte(let offset): b[offset] ^= 1
                    }
                }
                try withheld(read(b, applied: applied, done: done), reason, "\(first) + \(second)")
            }
        }
        tk.run("dictionary identity reads consumed values and ignores pair order") {
            let a = [CWorkerParam(key: "a", value: "é"), CWorkerParam(key: "z", value: "2")]
            try expectEqual(consumedParamsDigest(a), consumedParamsDigest(a.reversed()))
            var changed = a; changed[0].value = "e"
            try expect(consumedParamsDigest(a) != consumedParamsDigest(changed))
            // The same known answer as runner_abi_layout's capture.c, computed
            // from the stated framing.
            try expectEqual(consumedParamsDigest(a).map { String(format: "%02x", $0) }.joined(),
                            "5aa8848d0fbdc2f9c5bb4c59cbf358459609fe0a42982d825a40ba787a36fcb6")
        }
        tk.run("capture is opt-in and round-trips with a nonce") {
            let plain = PWRunnerPolicySpec(format: "sbpl", sbpl_source: source)
            try expectNil(plain.capture_compiled_profile)
            let requested = PWRunnerPolicySpec(format: "sbpl", sbpl_source: source,
                capture_compiled_profile: true, capture_nonce: nonce)
            let decoded = try JSONDecoder().decode(PWRunnerPolicySpec.self, from: JSONEncoder().encode(requested))
            try expectEqual(decoded.capture_nonce, nonce)
            let receipt = read(fixture())
            try receipt.validateForReporting()
            _ = try pwPorcelainEncode(receipt)
            try expectEqual(receipt.bytecode, Data([10,20,30]))
            try expectEqual(receipt.request_nonce, nonce)
        }
        tk.run("capture nonce is required and validated before spawn") {
            for n: String? in [nil, "", String(repeating: "A", count: 32), String(repeating: "0", count: 31)] {
                let input = CWorkerInput(workerExecutablePath: "/nonexistent", policy: source, slots: [],
                    captureCompiledProfile: true, captureNonce: n)
                guard case .failure(.captureNonceInvalid, _) = runCWorker(input) else {
                    throw TestFailure(message: "invalid nonce reached worker spawn")
                }
            }
        }
    }
}
