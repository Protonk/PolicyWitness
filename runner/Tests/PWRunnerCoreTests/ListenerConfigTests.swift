import Foundation
@testable import PWRunnerCore

/*
 * ListenerConfigTests — pins the argv → NSXPCListener selection.
 *
 * The runner host must bind NSXPCListener(machServiceName:) when launchd
 * starts it directly as a BYOXPC LaunchAgent mach-service (`--mach-service
 * <name>` in the generated plist), and NSXPCListener.service() when it is the
 * built-in `.xpc` bundle host. Commit b535fca collapsed both onto .service(),
 * which traps under xpc_main for the BYOXPC launch → `runner verify` times out.
 *
 * The selection lives in the pure pwListenerConfig() (Services/PWRunner/main.swift
 * is not in the SwiftPM package), so this table pins it directly. Behavior test:
 * drives the public boundary, not the switch in main.
 */
func runListenerConfigTests(_ tk: TestKit) {
    tk.group("ListenerConfig") {
        tk.run("--mach-service <name> selects a mach-service listener") {
            try expect(
                pwListenerConfig(argv: ["--mach-service", "com.x.PWRunner"])
                    == .machService("com.x.PWRunner"),
                "expected .machService(\"com.x.PWRunner\")"
            )
        }
        tk.run("no arguments selects the XPCService-bundle listener") {
            try expect(pwListenerConfig(argv: []) == .xpcService,
                       "expected .xpcService for empty argv")
        }
        tk.run("--mach-service with no following value falls back to XPCService") {
            try expect(pwListenerConfig(argv: ["--mach-service"]) == .xpcService,
                       "expected .xpcService when the flag has no value")
        }
        tk.run("--mach-service value is read even when other args precede it") {
            try expect(
                pwListenerConfig(argv: ["--other", "x", "--mach-service", "com.y.Svc"])
                    == .machService("com.y.Svc"),
                "expected .machService(\"com.y.Svc\")"
            )
        }
    }
}
