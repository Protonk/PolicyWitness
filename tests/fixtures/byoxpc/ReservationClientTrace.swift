// Only the lost-helper-capture arrangement compiles this with copied client
// sources. It records the actual selector call and gates stdout publication.
import Foundation
import Darwin

enum ReservationClientTrace {
    private static var directory: String? { ProcessInfo.processInfo.environment["PW_RESERVATION_CLIENT_TRACE"] }
    static func event(_ name: String, _ fields: [String: Any] = [:]) {
        guard let directory else { return }
        var record = fields
        record["event"] = name; record["pid"] = Int(getpid())
        do {
            let bytes = try JSONSerialization.data(withJSONObject: record, options: [.sortedKeys])
            try bytes.write(to: URL(fileURLWithPath: directory).appendingPathComponent("\(getpid())-\(name).json"), options: .atomic)
        } catch { _exit(94) }
    }
    static func beforeEmit(_ capture: PWRunnerClientCapture) {
        guard let directory else { return }
        event("capture_ready", ["terminal": capture.terminal, "submission": capture.submission.state])
        let start = DispatchTime.now().uptimeNanoseconds
        while access(directory + "/allow", F_OK) != 0 {
            if DispatchTime.now().uptimeNanoseconds - start >= 20_000_000_000 { event("gate_watchdog"); _exit(95) }
            usleep(1000)
        }
    }
}
