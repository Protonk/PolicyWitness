import Foundation

// Minimal XPC service entrypoint. launchd loads this binary as the host of
// the surrounding `.xpc` bundle and NSXPCListener.service() picks up the
// connection. The host drives the C worker (pw-probe-runner) plus batch
// validator (sb_api_validator) as separate children under CWorkerOrchestrator.
let listener = NSXPCListener.service()
let delegate = PWRunnerSessionDelegate()
listener.delegate = delegate
listener.resume()
RunLoop.current.run()
