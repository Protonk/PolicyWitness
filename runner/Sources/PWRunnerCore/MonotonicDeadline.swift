import Darwin

/// Shared by the worker policy writer and the validator duplex collector.
/// One absolute CLOCK_MONOTONIC deadline; progress and EINTR never renew it.
struct MonotonicDeadline {
    static func now() -> UInt64? {
        var ts = timespec()
        guard clock_gettime(CLOCK_MONOTONIC, &ts) == 0 else { return nil }
        return UInt64(ts.tv_sec) * 1_000_000_000 + UInt64(ts.tv_nsec)
    }
    let started: UInt64?
    let deadline: UInt64?
    let clock: () -> UInt64?
    init(milliseconds: Int, clock: @escaping () -> UInt64? = MonotonicDeadline.now) {
        self.clock = clock
        started = clock()
        let budget = min(UInt64(max(0, milliseconds)), UInt64.max / 1_000_000) * 1_000_000
        deadline = started.map { $0 > UInt64.max - budget ? UInt64.max : $0 + budget }
    }
    func sample() -> (remaining: UInt64, elapsedMs: UInt64)? {
        guard let start = started, let end = deadline, let now = clock(), now >= start else { return nil }
        return (now >= end ? 0 : end - now, (now - start) / 1_000_000)
    }
    static func pollMilliseconds(_ remaining: UInt64) -> Int32 {
        // Round up sub-millisecond allowances, capped at the collector tick.
        Int32(min(100, remaining / 1_000_000 + (remaining % 1_000_000 == 0 ? 0 : 1)))
    }
}

struct PolicyTransferCalls {
    var clock: () -> UInt64? = MonotonicDeadline.now
    var write: (Int32, UnsafeRawPointer, Int) -> Int = { Darwin.write($0, $1, $2) }
    var poll: (UnsafeMutablePointer<pollfd>, Int32) -> Int32 = { Darwin.poll($0, 1, $1) }
}

enum PolicyTransferStop {
    case complete, timeout(UInt64), writeError(Int32), failed(String)
}
struct PolicyTransferResult {
    var written: Int
    var stop: PolicyTransferStop
}

/// fd must already be nonblocking and protected against SIGPIPE.
func writePolicy(_ bytes: [UInt8], fd: Int32, deadline: MonotonicDeadline,
                 calls: PolicyTransferCalls = PolicyTransferCalls()) -> PolicyTransferResult {
    var written = 0
    func stopped(_ reason: PolicyTransferStop) -> PolicyTransferResult {
        PolicyTransferResult(written: written, stop: reason)
    }
    return bytes.withUnsafeBufferPointer { buffer in
        while true {
            // Completion is decided before the clock is consulted: a transfer whose
            // last write landed as the allowance ran out is complete, not timed out.
            if written == bytes.count { return stopped(.complete) }
            guard let sample = deadline.sample() else { return stopped(.failed("CLOCK_MONOTONIC unavailable")) }
            if sample.remaining == 0 { return stopped(.timeout(sample.elapsedMs)) }
            let n = calls.write(fd, buffer.baseAddress!.advanced(by: written), bytes.count - written)
            if n > 0 { written += n; continue }
            if n == 0 { return stopped(.failed("write returned zero without progress")) }
            let error = errno
            if error == EINTR { continue }
            if error != EAGAIN && error != EWOULDBLOCK { return stopped(.writeError(error)) }
            guard let sample = deadline.sample() else { return stopped(.failed("CLOCK_MONOTONIC unavailable")) }
            if sample.remaining == 0 { return stopped(.timeout(sample.elapsedMs)) }
            var pfd = pollfd(fd: fd, events: Int16(POLLOUT), revents: 0)
            let rc = calls.poll(&pfd, MonotonicDeadline.pollMilliseconds(sample.remaining))
            if rc < 0 && errno != EINTR { return stopped(.failed("poll: errno=\(errno)")) }
            // HUP/ERR are resolved by write, preserving its actual EPIPE.
        }
    }
}
