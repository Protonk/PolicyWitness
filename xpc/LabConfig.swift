import Foundation

public enum PWLabConfig {
#if PW_LAB_ENABLED
    public static let buildEnabled = true
#else
    public static let buildEnabled = false
#endif

    private static let lock = NSLock()
    private static var overrideEnabled: Bool?

    public static func isEnabled() -> Bool {
        guard buildEnabled else { return false }
        lock.lock()
        let override = overrideEnabled
        lock.unlock()
        if let override {
            return override
        }
        let raw = (ProcessInfo.processInfo.environment["PW_LAB"] ?? "").lowercased()
        return raw == "1" || raw == "true" || raw == "yes"
    }

    public static func setOverride(_ enabled: Bool?) {
        guard buildEnabled else { return }
        lock.lock()
        overrideEnabled = enabled
        lock.unlock()
    }
}
