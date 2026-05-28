import Foundation
import Darwin

// PWRunnerWorkerWire defines the host↔worker IPC: the argv flag the
// worker keys on at startup (pwRunnerWorkerModeArgument), the inherited
// file descriptor the worker reads from and writes to
// (pwRunnerWorkerRequestFD), the length-prefixed frame format used to
// carry the request and the report across the socketpair, and the
// internal PWRunnerWorkerReport type the worker emits.
//
// The companions are WorkerProcess.swift (host side: creates the
// socketpair, posix_spawns the worker, reads the report frame) and
// WorkerEntry.swift (worker side: reads the request frame, runs the
// probe plan, writes the report frame).
//
// What does NOT belong in this file: classifier logic, sandbox apply,
// caller authentication, anything user-facing. The wire types are
// internal — production callers see only PWRunnerRunResult, which
// PWRunnerService synthesizes from PWRunnerWorkerReport.

let pwRunnerWorkerModeArgument = "--apply-and-probe-worker"
let pwRunnerWorkerRequestFD: Int32 = 3

let maxWorkerFrameBytes = 64 * 1024 * 1024

struct PWRunnerWorkerReport: Codable {
    var worker_pid: Int
    var rc: Int
    var normalized_outcome: String
    var error: String?
    var policy_sha256: String?
    var sandboxed_after_apply: Bool?
    var deny_signal_total: PWRunnerSignalResult?
    var steps: [PWRunnerStepResult]
    var instrumentation: PWRunnerInstrumentationReport?
}

enum WorkerFrameError: Error, CustomStringConvertible {
    case frameTooLarge(Int)
    case readFailed(String)
    case writeFailed(String)
    case eofBeforeFrame
    case truncatedFrame

    var description: String {
        switch self {
        case .frameTooLarge(let size):
            return "worker frame too large: \(size) bytes"
        case .readFailed(let message):
            return "worker frame read failed: \(message)"
        case .writeFailed(let message):
            return "worker frame write failed: \(message)"
        case .eofBeforeFrame:
            return "worker frame missing before EOF"
        case .truncatedFrame:
            return "worker frame truncated before EOF"
        }
    }
}

func writeWorkerFrame(fd: Int32, data: Data) throws {
    guard data.count <= maxWorkerFrameBytes else {
        throw WorkerFrameError.frameTooLarge(data.count)
    }

    var prefix = UInt32(data.count).bigEndian
    try withUnsafeBytes(of: &prefix) { raw in
        guard let base = raw.baseAddress else { return }
        try writeAll(fd: fd, base: base, count: raw.count)
    }
    try data.withUnsafeBytes { raw in
        guard let base = raw.baseAddress else { return }
        try writeAll(fd: fd, base: base, count: raw.count)
    }
}

func readWorkerFrame(fd: Int32) throws -> Data {
    var prefix = [UInt8](repeating: 0, count: 4)
    try prefix.withUnsafeMutableBytes { raw in
        guard let base = raw.baseAddress else { return }
        try readExact(fd: fd, base: base, count: raw.count, eofBeforeAny: .eofBeforeFrame)
    }
    let length = prefix.reduce(UInt32(0)) { ($0 << 8) | UInt32($1) }
    let count = Int(length)
    guard count <= maxWorkerFrameBytes else {
        throw WorkerFrameError.frameTooLarge(count)
    }
    var payload = Data(count: count)
    try payload.withUnsafeMutableBytes { raw in
        guard let base = raw.baseAddress else { return }
        try readExact(fd: fd, base: base, count: raw.count, eofBeforeAny: .truncatedFrame)
    }
    return payload
}

private func writeAll(fd: Int32, base: UnsafeRawPointer, count: Int) throws {
    var offset = 0
    while offset < count {
        let wrote = Darwin.write(fd, base.advanced(by: offset), count - offset)
        if wrote > 0 {
            offset += wrote
            continue
        }
        if wrote < 0 && errno == EINTR {
            continue
        }
        let message = wrote < 0 ? String(cString: strerror(errno)) : "write returned 0"
        throw WorkerFrameError.writeFailed(message)
    }
}

private func readExact(
    fd: Int32,
    base: UnsafeMutableRawPointer,
    count: Int,
    eofBeforeAny: WorkerFrameError
) throws {
    var offset = 0
    while offset < count {
        let got = Darwin.read(fd, base.advanced(by: offset), count - offset)
        if got > 0 {
            offset += got
            continue
        }
        if got == 0 {
            throw offset == 0 ? eofBeforeAny : WorkerFrameError.truncatedFrame
        }
        if errno == EINTR {
            continue
        }
        throw WorkerFrameError.readFailed(String(cString: strerror(errno)))
    }
}
