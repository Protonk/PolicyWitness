import Foundation

// Minimal assertion harness for the PWRunnerCore test executable. We avoid
// XCTest so the suite runs under Command Line Tools (XCTest ships with full
// Xcode, not CLT). Style mirrors XCTest closely so converting to XCTest
// later — if Xcode ever becomes a build prerequisite — is mechanical.
//
// Each test function takes a `TestKit` and calls `tk.run("name") { ... }`
// for one expectation block. Inside the block, use the `expect*` helpers;
// any thrown TestFailure marks the block failed and continues with the
// next one. `tk.exitCode()` returns 0 iff every block passed.
//
// Host and worker allowances count system sleep, so each block also records
// how long the system slept while it ran. A block that slept at least 1 ms
// gets a separate line after its result; the outcome itself is unchanged.

final class TestKit {
    private(set) var totalTests = 0
    private(set) var failedTests = 0
    private(set) var sleptFailures = 0
    private var failureReasons: [(test: String, reason: String)] = []

    /// The clock that counts system sleep and the one that does not. They share
    /// one timebase, so the gap between their advances is the sleep. Controls
    /// substitute readings.
    var sleepClocks: () -> (continuous: UInt64, uptime: UInt64) = {
        (clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW), clock_gettime_nsec_np(CLOCK_UPTIME_RAW))
    }

    func group(_ name: String, _ body: () -> Void) {
        FileHandle.standardOutput.write(Data("\n[\(name)]\n".utf8))
        body()
    }

    func run(_ name: String, _ body: () throws -> Void) {
        totalTests += 1
        let before = sleepClocks()
        var failure: String?
        do {
            try body()
        } catch let thrown as TestFailure {
            failure = thrown.message
        } catch {
            failure = "unexpected throw: \(error)"
        }
        let after = sleepClocks()
        let continuous = after.continuous &- before.continuous
        let uptime = after.uptime &- before.uptime
        // Reading the pair takes microseconds; a smaller gap is read skew.
        let sleptMs: UInt64? = continuous > uptime && continuous - uptime >= 1_000_000
            ? (continuous - uptime) / 1_000_000 : nil
        if let failure {
            failedTests += 1
            if sleptMs != nil { sleptFailures += 1 }
            failureReasons.append((name, failure))
            FileHandle.standardOutput.write(Data("  FAIL \(name): \(failure)\n".utf8))
        } else {
            FileHandle.standardOutput.write(Data("  ok   \(name)\n".utf8))
        }
        if let sleptMs {
            FileHandle.standardOutput.write(Data("       system slept \(sleptMs) ms during this case\n".utf8))
        }
    }

    func exitCode() -> Int32 {
        failedTests == 0 ? 0 : 1
    }

    func summary() -> String {
        let passed = totalTests - failedTests
        return "\(passed)/\(totalTests) tests passed"
    }

    /// Printed before the summary when any failure overlapped system sleep.
    func sleepSummary() -> String? {
        sleptFailures == 0 ? nil : "\(sleptFailures) of \(failedTests) failures overlapped system sleep"
    }
}

struct TestFailure: Error {
    let message: String
}

func expect(
    _ condition: @autoclosure () -> Bool,
    _ message: @autoclosure () -> String = "expectation failed",
    file: StaticString = #file,
    line: UInt = #line
) throws {
    if !condition() {
        throw TestFailure(message: "\(message()) (at \(file):\(line))")
    }
}

func expectTrue(
    _ condition: Bool,
    _ message: @autoclosure () -> String = "expected true",
    file: StaticString = #file,
    line: UInt = #line
) throws {
    try expect(condition, message(), file: file, line: line)
}

func expectFalse(
    _ condition: Bool,
    _ message: @autoclosure () -> String = "expected false",
    file: StaticString = #file,
    line: UInt = #line
) throws {
    try expect(!condition, message(), file: file, line: line)
}

func expectEqual<T: Equatable>(
    _ actual: T,
    _ expected: T,
    _ context: @autoclosure () -> String = "",
    file: StaticString = #file,
    line: UInt = #line
) throws {
    if actual != expected {
        let ctx = context()
        let suffix = ctx.isEmpty ? "" : " — \(ctx)"
        throw TestFailure(
            message: "expected \(expected), got \(actual)\(suffix) (at \(file):\(line))"
        )
    }
}

func expectClose(
    _ actual: Double,
    _ expected: Double,
    accuracy: Double,
    file: StaticString = #file,
    line: UInt = #line
) throws {
    if abs(actual - expected) > accuracy {
        throw TestFailure(
            message: "expected \(expected) ± \(accuracy), got \(actual) (at \(file):\(line))"
        )
    }
}

func expectNil<T>(
    _ value: T?,
    _ context: @autoclosure () -> String = "",
    file: StaticString = #file,
    line: UInt = #line
) throws {
    if let value {
        let ctx = context()
        let suffix = ctx.isEmpty ? "" : " — \(ctx)"
        throw TestFailure(
            message: "expected nil, got \(value)\(suffix) (at \(file):\(line))"
        )
    }
}

func expectNotNil<T>(
    _ value: T?,
    _ context: @autoclosure () -> String = "",
    file: StaticString = #file,
    line: UInt = #line
) throws {
    if value == nil {
        let ctx = context()
        let suffix = ctx.isEmpty ? "" : " — \(ctx)"
        throw TestFailure(
            message: "expected non-nil\(suffix) (at \(file):\(line))"
        )
    }
}

func expectContains(
    _ haystack: String,
    _ needle: String,
    file: StaticString = #file,
    line: UInt = #line
) throws {
    if !haystack.contains(needle) {
        throw TestFailure(
            message: "expected substring \(needle.debugDescription) in \(haystack.debugDescription) (at \(file):\(line))"
        )
    }
}

func expectThrows(
    _ body: () throws -> Void,
    _ verify: ((Error) throws -> Void)? = nil,
    file: StaticString = #file,
    line: UInt = #line
) throws {
    do {
        try body()
    } catch {
        try verify?(error)
        return
    }
    throw TestFailure(message: "expected throw, got success (at \(file):\(line))")
}
