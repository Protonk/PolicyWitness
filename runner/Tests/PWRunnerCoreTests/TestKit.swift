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

final class TestKit {
    private(set) var totalTests = 0
    private(set) var failedTests = 0
    private var failureReasons: [(test: String, reason: String)] = []

    func group(_ name: String, _ body: () -> Void) {
        FileHandle.standardOutput.write(Data("\n[\(name)]\n".utf8))
        body()
    }

    func run(_ name: String, _ body: () throws -> Void) {
        totalTests += 1
        do {
            try body()
            FileHandle.standardOutput.write(Data("  ok   \(name)\n".utf8))
        } catch let failure as TestFailure {
            failedTests += 1
            failureReasons.append((name, failure.message))
            FileHandle.standardOutput.write(Data("  FAIL \(name): \(failure.message)\n".utf8))
        } catch {
            failedTests += 1
            let msg = "unexpected throw: \(error)"
            failureReasons.append((name, msg))
            FileHandle.standardOutput.write(Data("  FAIL \(name): \(msg)\n".utf8))
        }
    }

    func exitCode() -> Int32 {
        failedTests == 0 ? 0 : 1
    }

    func summary() -> String {
        let passed = totalTests - failedTests
        return "\(passed)/\(totalTests) tests passed"
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
