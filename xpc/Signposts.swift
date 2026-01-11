import Foundation
import Dispatch
import os

public enum PWTraceContext {
    private static let key = "pw.trace_context" as NSString

    public static func set(correlationId: String?, planId: String? = nil, rowId: String? = nil, probeId: String? = nil) {
        var dict: [String: String] = [:]
        if let correlationId { dict["correlation_id"] = correlationId }
        if let planId { dict["plan_id"] = planId }
        if let rowId { dict["row_id"] = rowId }
        if let probeId { dict["probe_id"] = probeId }
        Thread.current.threadDictionary[key] = dict
    }

    public static func clear() {
        Thread.current.threadDictionary.removeObject(forKey: key)
    }

    public static func correlationId() -> String? {
        (Thread.current.threadDictionary[key] as? [String: String])?["correlation_id"]
    }

    public static func planId() -> String? {
        (Thread.current.threadDictionary[key] as? [String: String])?["plan_id"]
    }

    public static func rowId() -> String? {
        (Thread.current.threadDictionary[key] as? [String: String])?["row_id"]
    }

    public static func probeId() -> String? {
        (Thread.current.threadDictionary[key] as? [String: String])?["probe_id"]
    }
}

public enum PWSignposts {
    public static let subsystem = "com.yourteam.policy-witness"
    public static let categoryXpcClient = "xpc_client"
    public static let categoryXpcService = "xpc_service"
    public static let categoryQuarantineClient = "quarantine_client"
    public static let categoryQuarantineService = "quarantine_service"
    public static let categoryInheritChild = "inherit_child"

    private static let enabledKey = "pw.signposts.enabled" as NSString
    private static let envEnabled: Bool = {
        let raw = (ProcessInfo.processInfo.environment["PW_ENABLE_SIGNPOSTS"] ?? "").lowercased()
        return raw == "1" || raw == "true" || raw == "yes"
    }()

    public static func log(category: String) -> OSLog {
        OSLog(subsystem: subsystem, category: category)
    }

    public static func isEnabled() -> Bool {
        if let override = Thread.current.threadDictionary[enabledKey] as? Bool {
            return override
        }
        return envEnabled
    }

    public static func setEnabledForCurrentThread(_ enabled: Bool?) {
        if let enabled {
            Thread.current.threadDictionary[enabledKey] = enabled
        } else {
            Thread.current.threadDictionary.removeObject(forKey: enabledKey)
        }
    }

    public static func withEnabled<T>(_ enabled: Bool, _ body: () throws -> T) rethrows -> T {
        let prior = Thread.current.threadDictionary[enabledKey] as? Bool
        Thread.current.threadDictionary[enabledKey] = enabled
        defer {
            if let prior {
                Thread.current.threadDictionary[enabledKey] = prior
            } else {
                Thread.current.threadDictionary.removeObject(forKey: enabledKey)
            }
        }
        return try body()
    }
}

public struct PWSignpostSpan {
    private struct State {
        let log: OSLog
        let signpostId: OSSignpostID
        let name: StaticString
        let nameString: String
        let category: String
        let label: String
        let correlationId: String
    }

    private let state: State?

    public init(category: String, name: StaticString, label: String, correlationId: String? = nil) {
        guard PWSignposts.isEnabled() else {
            self.state = nil
            return
        }

        let log = PWSignposts.log(category: category)
        let signpostId = OSSignpostID(log: log)
        let correlationId = correlationId ?? PWTraceContext.correlationId() ?? "unknown"
        let nameString = String(describing: name)
        self.state = State(
            log: log,
            signpostId: signpostId,
            name: name,
            nameString: nameString,
            category: category,
            label: label,
            correlationId: correlationId
        )

        os_signpost(
            .begin,
            log: log,
            name: name,
            signpostID: signpostId,
            "pw_corr=%{public}s label=%{public}s",
            correlationId,
            label
        )

        #if PW_LAB_ENABLED
        let pid = Int(getpid())
        let processName = ProcessInfo.processInfo.processName
        let event = PWLabSignpostEvent(
            name: nameString,
            category: category,
            phase: "begin",
            signpost_id: signpostId.rawValue,
            timestamp_unix_ms: UInt64(Date().timeIntervalSince1970 * 1000.0),
            uptime_ns: DispatchTime.now().uptimeNanoseconds,
            pid: pid,
            process_name: processName,
            correlation_id: correlationId,
            plan_id: PWTraceContext.planId(),
            row_id: PWTraceContext.rowId(),
            probe_id: PWTraceContext.probeId(),
            label: label
        )
        PWLabSignposts.emit(event)
        #endif
    }

    public func end() {
        guard let state else { return }
        os_signpost(
            .end,
            log: state.log,
            name: state.name,
            signpostID: state.signpostId,
            "pw_corr=%{public}s label=%{public}s",
            state.correlationId,
            state.label
        )

        #if PW_LAB_ENABLED
        let pid = Int(getpid())
        let processName = ProcessInfo.processInfo.processName
        let event = PWLabSignpostEvent(
            name: state.nameString,
            category: state.category,
            phase: "end",
            signpost_id: state.signpostId.rawValue,
            timestamp_unix_ms: UInt64(Date().timeIntervalSince1970 * 1000.0),
            uptime_ns: DispatchTime.now().uptimeNanoseconds,
            pid: pid,
            process_name: processName,
            correlation_id: state.correlationId,
            plan_id: PWTraceContext.planId(),
            row_id: PWTraceContext.rowId(),
            probe_id: PWTraceContext.probeId(),
            label: state.label
        )
        PWLabSignposts.emit(event)
        #endif
    }
}
