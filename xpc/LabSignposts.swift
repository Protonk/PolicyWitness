import Foundation

public struct PWLabSignpostEvent: Codable {
    public var name: String
    public var category: String
    public var phase: String
    public var signpost_id: UInt64
    public var timestamp_unix_ms: UInt64
    public var uptime_ns: UInt64
    public var pid: Int
    public var process_name: String
    public var correlation_id: String?
    public var plan_id: String?
    public var row_id: String?
    public var probe_id: String?
    public var label: String?
    public var session_token: String?
    public var service_bundle_id: String?
    public var service_name: String?
}

public enum PWLabSignposts {
    public typealias Sink = (PWLabSignpostEvent) -> Void

    private static let lock = NSLock()
    private static var sink: Sink?

    public static func setSink(_ newSink: Sink?) {
        if newSink != nil && !PWLabConfig.isEnabled() {
            return
        }
        lock.lock()
        sink = newSink
        lock.unlock()
    }

    public static func emit(_ event: PWLabSignpostEvent) {
        guard PWLabConfig.isEnabled() else { return }
        lock.lock()
        let current = sink
        lock.unlock()
        current?(event)
    }
}
