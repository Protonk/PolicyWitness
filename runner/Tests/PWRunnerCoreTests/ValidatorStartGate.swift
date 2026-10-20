import Darwin
import Foundation
@testable import PWRunnerCore

/// Test equipment for validator cases whose collection deadline is short. The
/// driver starts that deadline when the spawn returns; this spawn returns only
/// after the lifecycle `.validator` fixture has written a start receipt from
/// `main`, so a cold or delayed start is not charged to the window. It appends
/// the receipt path, and an optional start delay, to the driver's arguments;
/// only that fixture reads them, never the shipped `sb_api_validator`. Waits and
/// elapsed times use CLOCK_UPTIME_RAW, which stops during system sleep, so a
/// sleep can neither expire the watchdog nor stand in for a delay. The gate
/// never reaps or signals a child: production cleanup keeps every one it spawns.
final class ValidatorStartGate {
    struct Start {
        let pid: pid_t
        let receipt: String
        let elapsedMs: UInt64
    }

    private let delayMs: Int?
    private(set) var starts: [Start] = []
    private(set) var equipmentFailures: [String] = []
    private var receiptPaths: [String] = []

    init(delayMs: Int? = nil) {
        self.delayMs = delayMs
    }

    deinit {
        for path in receiptPaths { try? FileManager.default.removeItem(atPath: path) }
    }

    var spawn: ValidatorSpawnCall {
        { [self] pid, path, actions, argv in launch(pid, path, actions, argv) }
    }

    func launch(_ pid: UnsafeMutablePointer<pid_t>, _ path: String,
                _ actions: UnsafePointer<posix_spawn_file_actions_t?>,
                _ argv: UnsafePointer<UnsafeMutablePointer<CChar>?>) -> Int32 {
        let receipt = "/tmp/pw-validator-started-" + UUID().uuidString
        receiptPaths.append(receipt)
        var arguments: [String] = []
        var index = 0
        while let argument = argv[index] {
            arguments.append(String(cString: argument))
            index += 1
        }
        arguments.append(receipt)
        if let delayMs { arguments.append(String(delayMs)) }
        let rc = withCStringArrayCopy(arguments) { nativeValidatorSpawn(pid, path, actions, $0) }
        if rc != 0 { return rc }
        let spawned = pid.pointee
        let started = clock_gettime_nsec_np(CLOCK_UPTIME_RAW)
        let expected = "started pid=\(spawned) "
        while clock_gettime_nsec_np(CLOCK_UPTIME_RAW) - started < 5_000_000_000 {
            if let text = try? String(contentsOfFile: receipt, encoding: .utf8), text.hasPrefix(expected), text.hasSuffix("\n") {
                let elapsed = (clock_gettime_nsec_np(CLOCK_UPTIME_RAW) - started) / 1_000_000
                starts.append(Start(pid: spawned, receipt: text, elapsedMs: elapsed))
                return 0
            }
            usleep(1000)
        }
        // Report success so the production collector keeps the child's
        // collection and cleanup; the case reports this failure first.
        equipmentFailures.append("validator \(spawned) wrote no start receipt naming it within 5 s of uptime")
        return 0
    }

    /// Checked before any behavioral assertion and reported as equipment.
    func requireStarts(_ count: Int) throws {
        if !equipmentFailures.isEmpty {
            throw TestFailure(message: "equipment: " + equipmentFailures.joined(separator: "; "))
        }
        if starts.count != count {
            throw TestFailure(message: "equipment: expected \(count) gated validator starts, observed \(starts.count)")
        }
    }
}
