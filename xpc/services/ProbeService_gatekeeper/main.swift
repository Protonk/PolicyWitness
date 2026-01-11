import Foundation

private func gatekeeperMode() -> String {
    if let env = ProcessInfo.processInfo.environment["PW_GATEKEEPER_MODE"], !env.isEmpty {
        return env
    }
    let home = NSHomeDirectory()
    let modePath = "\(home)/Library/Application Support/PolicyWitness/gatekeeper_mode"
    if let contents = try? String(contentsOfFile: modePath, encoding: .utf8) {
        return contents
    }
    return "accept"
}

private func gatekeeperAccepts() -> Bool {
    let raw = gatekeeperMode()
    let mode = raw.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    if mode.isEmpty {
        return true
    }
    switch mode {
    case "reject", "deny", "0", "false":
        return false
    case "accept", "allow", "1", "true":
        return true
    default:
        return true
    }
}

final class GatekeeperSessionDelegate: NSObject, NSXPCListenerDelegate {
    func listener(_ listener: NSXPCListener, shouldAcceptNewConnection newConnection: NSXPCConnection) -> Bool {
        guard gatekeeperAccepts() else {
            return false
        }
        newConnection.exportedInterface = NSXPCInterface(with: ProbeServiceProtocol.self)
        newConnection.remoteObjectInterface = NSXPCInterface(with: SessionEventSinkProtocol.self)
        newConnection.exportedObject = ProbeServiceSessionHost(connection: newConnection)
        newConnection.resume()
        return true
    }
}

let listener = NSXPCListener.service()
let delegate = GatekeeperSessionDelegate()
listener.delegate = delegate
listener.resume()
RunLoop.current.run()
