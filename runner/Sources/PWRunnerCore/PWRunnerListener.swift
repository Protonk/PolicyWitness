import Foundation

/// How the PWRunner host should bind its `NSXPCListener`.
///
/// - `.xpcService` is the built-in path: launchd loads the surrounding `.xpc`
///   bundle and `NSXPCListener.service()` picks up the connection.
/// - `.machService` is the external / BYOXPC path: launchd starts the executable
///   directly as a LaunchAgent mach-service (the plist that `runner install`
///   generates passes `--mach-service <name>` and a `MachServices` key). That
///   process was NOT launched as an XPCService bundle, so `.service()` traps in
///   `xpc_main`; it must bind `NSXPCListener(machServiceName:)` instead.
public enum PWListenerConfig: Equatable {
    case machService(String)
    case xpcService
}

/// Pure argv → listener-config mapping. `--mach-service <name>` selects a
/// mach-service listener; anything else (including no arguments, or the flag
/// with no following value) falls back to the XPCService-bundle listener.
///
/// This is deliberately a standalone, side-effect-free function so the
/// selection is unit-testable in `PWRunnerCore` — the executable entrypoint
/// (`Services/PWRunner/main.swift`) is not part of the SwiftPM test package.
public func pwListenerConfig(argv: [String]) -> PWListenerConfig {
    var i = 0
    while i < argv.count {
        if argv[i] == "--mach-service", i + 1 < argv.count {
            return .machService(argv[i + 1])
        }
        i += 1
    }
    return .xpcService
}
