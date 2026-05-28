import Foundation
import Darwin
@testable import PWRunnerCore

// Length-prefixed framing used between the host and worker over a socketpair.
// The happy path is exercised by every passing e2e run; these tests pin the
// failure boundaries (truncation, oversized prefix, empty frame, EOF before
// any data) that production code handles but no specimen can reach.

private func makePipe() throws -> (read: Int32, write: Int32) {
    var fds = [Int32](repeating: 0, count: 2)
    let rc = pipe(&fds)
    guard rc == 0 else {
        let message = String(cString: strerror(errno))
        throw TestFailure(message: "pipe() failed: \(message)")
    }
    return (fds[0], fds[1])
}

private func writeRaw(_ fd: Int32, _ bytes: [UInt8]) {
    _ = bytes.withUnsafeBytes { raw in
        Darwin.write(fd, raw.baseAddress, raw.count)
    }
}

func runWorkerFrameTests(_ tk: TestKit) {
    tk.group("PWRunnerWorkerWire framing") {

        tk.run("roundtrips arbitrary bytes") {
            let (r, w) = try makePipe()
            defer { close(r) }

            let payload = Data([0x00, 0xff, 0x42, 0x10, 0x80, 0x7e, 0x01])
            try writeWorkerFrame(fd: w, data: payload)
            close(w)

            let received = try readWorkerFrame(fd: r)
            try expectEqual(received, payload)
        }

        tk.run("roundtrips a zero-length frame") {
            // Zero-length frames are valid; the worker never emits one
            // today, but the framing layer must not special-case it.
            let (r, w) = try makePipe()
            defer { close(r) }

            try writeWorkerFrame(fd: w, data: Data())
            close(w)

            let received = try readWorkerFrame(fd: r)
            try expectEqual(received.count, 0)
        }

        tk.run("EOF before any bytes raises .eofBeforeFrame") {
            let (r, w) = try makePipe()
            defer { close(r) }

            // Close the write end immediately — reader sees EOF on the
            // first read. The host uses this to distinguish a worker that
            // died before posix_spawn from one that died mid-write.
            close(w)

            try expectThrows({ _ = try readWorkerFrame(fd: r) }) { error in
                guard let frameError = error as? WorkerFrameError else {
                    throw TestFailure(message: "expected WorkerFrameError, got \(error)")
                }
                if case .eofBeforeFrame = frameError {
                    return
                }
                throw TestFailure(message: "expected .eofBeforeFrame, got \(frameError)")
            }
        }

        tk.run("truncated prefix raises .truncatedFrame") {
            let (r, w) = try makePipe()
            defer { close(r) }

            // Write 2 of the 4 prefix bytes, then EOF.
            writeRaw(w, [0x00, 0x00])
            close(w)

            try expectThrows({ _ = try readWorkerFrame(fd: r) }) { error in
                guard let frameError = error as? WorkerFrameError else {
                    throw TestFailure(message: "expected WorkerFrameError, got \(error)")
                }
                if case .truncatedFrame = frameError {
                    return
                }
                throw TestFailure(message: "expected .truncatedFrame, got \(frameError)")
            }
        }

        tk.run("truncated body raises .truncatedFrame") {
            let (r, w) = try makePipe()
            defer { close(r) }

            // Announce 100 bytes of body, then send only 5 and close.
            writeRaw(w, [0, 0, 0, 100])
            writeRaw(w, [1, 2, 3, 4, 5])
            close(w)

            try expectThrows({ _ = try readWorkerFrame(fd: r) }) { error in
                guard let frameError = error as? WorkerFrameError else {
                    throw TestFailure(message: "expected WorkerFrameError, got \(error)")
                }
                if case .truncatedFrame = frameError {
                    return
                }
                throw TestFailure(message: "expected .truncatedFrame, got \(frameError)")
            }
        }

        tk.run("oversized prefix is rejected before allocating") {
            let (r, w) = try makePipe()
            defer { close(r) }

            // Send a 4-byte prefix that claims a 2-GiB frame — well above
            // maxWorkerFrameBytes (64 MiB). The reader must bail before
            // allocating a 2-GiB Data buffer.
            writeRaw(w, [0x80, 0x00, 0x00, 0x00])
            close(w)

            try expectThrows({ _ = try readWorkerFrame(fd: r) }) { error in
                guard let frameError = error as? WorkerFrameError else {
                    throw TestFailure(message: "expected WorkerFrameError, got \(error)")
                }
                if case .frameTooLarge(let n) = frameError {
                    try expectTrue(n > maxWorkerFrameBytes)
                    return
                }
                throw TestFailure(message: "expected .frameTooLarge, got \(frameError)")
            }
        }

        tk.run("write rejects oversized payload without touching the fd") {
            // The write end is never used because the size check fires
            // first; passing -1 means any accidental write() call would
            // fail loudly with EBADF.
            let claimedSize = maxWorkerFrameBytes + 1
            var huge = Data(count: claimedSize)

            try expectThrows({ try writeWorkerFrame(fd: -1, data: huge) }) { error in
                guard let frameError = error as? WorkerFrameError else {
                    throw TestFailure(message: "expected WorkerFrameError, got \(error)")
                }
                if case .frameTooLarge(let n) = frameError {
                    try expectEqual(n, claimedSize)
                    return
                }
                throw TestFailure(message: "expected .frameTooLarge, got \(frameError)")
            }
            // Touch huge to keep ARC from optimizing it away too early.
            huge[0] = 0
        }
    }
}
