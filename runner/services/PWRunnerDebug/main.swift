import Foundation

if CommandLine.arguments.dropFirst().contains(pwRunnerWorkerModeArgument) {
    runApplyAndProbeWorker()
}

// Minimal XPC service entrypoint. launchd loads this binary as the host of
// the surrounding `.xpc` bundle and NSXPCListener.service() picks up the
// connection.
let listener = NSXPCListener.service()
let delegate = PWRunnerSessionDelegate()
listener.delegate = delegate
listener.resume()
RunLoop.current.run()
