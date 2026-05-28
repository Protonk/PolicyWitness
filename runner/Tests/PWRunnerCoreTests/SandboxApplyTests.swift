import Foundation
import Darwin
@testable import PWRunnerCore

// Covers the runner's "the libsandbox call failed" branches that surface as
// normalized_outcome = "sandbox_apply_failed". The e2e suites cannot reach
// this outcome because the controller's preflight rejects the same input
// upstream as "bad_policy"; here we feed applySandboxPolicy a stub SandboxLib
// whose compile/apply hooks return failure, then check the error message
// the host would forward.
//
// C function pointer types (`@convention(c)`) cannot capture closure context,
// so the few tests that need to observe side effects route through
// file-scope variables that the stub closures read. Tests run serially so
// the shared state is safe; each test resets it before use.

private let dummyHandle = UnsafeMutableRawPointer(bitPattern: 0xdead)!
private let dummyProfile = UnsafeMutableRawPointer(bitPattern: 0xbeef)

// Shared state for side-effect-observing stubs. Reset at the top of any
// test that uses them.
private var stubErrMessagePtr: UnsafeMutablePointer<CChar>? = nil
private var stubFreedPointers: [UnsafeMutablePointer<CChar>] = []

// File-scope stub function values. Defined at module scope so the closure
// literals do not need to capture anything from an enclosing function.
private let stubCompileReturningNull: SandboxLib.CompileStringFn = { _, _, _ in
    nil
}
private let stubCompileReturningProfile: SandboxLib.CompileStringFn = { _, _, _ in
    dummyProfile
}
private let stubCompileWithErrBuf: SandboxLib.CompileStringFn = { _, _, errBufPtr in
    errBufPtr?.pointee = stubErrMessagePtr
    return nil
}
private let stubApplyOk: SandboxLib.ApplyFn = { _ in 0 }
private let stubApplyEACCES: SandboxLib.ApplyFn = { _ in
    errno = EACCES
    return -1
}
private let stubFreeErrorTracking: SandboxLib.FreeErrorFn = { ptr in
    if let ptr {
        stubFreedPointers.append(ptr)
    }
}
private let stubFreeErrorNoop: SandboxLib.FreeErrorFn = { _ in }

private func stubLib(
    compileString: SandboxLib.CompileStringFn,
    apply: SandboxLib.ApplyFn = stubApplyOk,
    freeError: SandboxLib.FreeErrorFn = stubFreeErrorNoop
) -> SandboxLib {
    SandboxLib(
        handle: dummyHandle,
        createParams: { nil },
        freeParams: { _ in },
        setParam: { _, _, _ in 0 },
        compileString: compileString,
        freeProfile: { _ in },
        freeError: freeError,
        apply: apply
    )
}

func runSandboxApplyTests(_ tk: TestKit) {
    tk.group("SandboxApply") {

        tk.run("compile returning NULL surfaces as apply error") {
            let lib = stubLib(compileString: stubCompileReturningNull)
            let policy = PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1) (allow default)")

            let result = applySandboxPolicy(policy, sandboxLib: lib)

            switch result {
            case .success:
                throw TestFailure(message: "expected .failure")
            case .failure(let err):
                try expectContains(err.message, "sandbox_compile_string failed")
            }
        }

        tk.run("compile error buffer is propagated and freed") {
            stubFreedPointers = []
            let errMessage = strdup("synthetic compile failure")!
            defer { free(errMessage) }
            stubErrMessagePtr = errMessage

            let lib = stubLib(
                compileString: stubCompileWithErrBuf,
                freeError: stubFreeErrorTracking
            )
            let policy = PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)")

            let result = applySandboxPolicy(policy, sandboxLib: lib)

            switch result {
            case .success:
                throw TestFailure(message: "expected .failure")
            case .failure(let err):
                try expectContains(err.message, "synthetic compile failure")
            }
            try expectEqual(
                stubFreedPointers.count, 1,
                "applySandboxPolicy must call freeError exactly once on the error buffer"
            )
            try expectEqual(stubFreedPointers.first, errMessage)
        }

        tk.run("apply returning non-zero surfaces strerror") {
            let lib = stubLib(
                compileString: stubCompileReturningProfile,
                apply: stubApplyEACCES
            )
            let policy = PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1)")

            let result = applySandboxPolicy(policy, sandboxLib: lib)

            switch result {
            case .success:
                throw TestFailure(message: "expected .failure")
            case .failure(let err):
                try expectContains(err.message, "sandbox_apply failed")
            }
        }

        tk.run("happy path returns success") {
            let lib = stubLib(
                compileString: stubCompileReturningProfile,
                apply: stubApplyOk
            )
            let policy = PWRunnerPolicySpec(format: "sbpl", sbpl_source: "(version 1) (allow default)")

            let result = applySandboxPolicy(policy, sandboxLib: lib)

            if case .failure(let err) = result {
                throw TestFailure(message: "expected .success, got .failure: \(err.message)")
            }
        }

        tk.run("missing sbpl_source is rejected before compile") {
            // We rely on the distinct error message ("missing
            // policy.sbpl_source" vs "sandbox_compile_string failed") to
            // prove compile was not called. A captured counter is not
            // possible here because the stub closure is @convention(c).
            let lib = stubLib(compileString: stubCompileReturningProfile)
            let policy = PWRunnerPolicySpec(format: "sbpl", sbpl_source: nil)

            let result = applySandboxPolicy(policy, sandboxLib: lib)

            switch result {
            case .success:
                throw TestFailure(message: "expected .failure when sbpl_source is nil")
            case .failure(let err):
                try expectContains(err.message, "missing policy.sbpl_source")
            }
        }

        tk.run("unknown format is rejected") {
            let lib = stubLib(compileString: stubCompileReturningNull)
            let policy = PWRunnerPolicySpec(format: "not-a-real-format", sbpl_source: "(version 1)")

            let result = applySandboxPolicy(policy, sandboxLib: lib)

            switch result {
            case .success:
                throw TestFailure(message: "expected .failure for unknown policy format")
            case .failure(let err):
                try expectContains(err.message, "unknown policy.format")
            }
        }
    }
}
