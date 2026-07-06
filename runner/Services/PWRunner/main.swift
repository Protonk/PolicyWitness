import Foundation

// Minimal XPC service entrypoint. Two launch models are supported, selected by
// argv (see pwListenerConfig):
//   - Built-in runner: launchd loads this binary as the host of the surrounding
//     `.xpc` bundle; NSXPCListener.service() picks up the connection.
//   - External / BYOXPC runner: launchd starts this binary directly as a
//     LaunchAgent mach-service and passes `--mach-service <name>`; we bind
//     NSXPCListener(machServiceName:). Using .service() here would trap in
//     xpc_main (the process was not launched as an XPCService bundle).
// The host drives the C worker (pw-probe-runner) plus batch validator
// (sb_api_validator) as separate children under CWorkerOrchestrator.
let listener: NSXPCListener
switch pwListenerConfig(argv: Array(CommandLine.arguments.dropFirst())) {
case .machService(let name):
    listener = NSXPCListener(machServiceName: name)
case .xpcService:
    listener = NSXPCListener.service()
}
let delegate = PWRunnerSessionDelegate()
listener.delegate = delegate
listener.resume()
RunLoop.current.run()
