// Independent RPC caller. No production parser, reservation state or client
// session is linked. Commands come from the test on stdin; replies are NDJSON.
// Reservation credentials stay in memory and are redacted from observations.
import Foundation
import Darwin
import CryptoKit

@objc protocol ReservationProtocol {
    func reserveRunner(_ request: Data, withReply reply: @escaping (Data) -> Void)
    func runReservedSpecimen(_ request: Data, reservation: String, withReply reply: @escaping (Bool, Data) -> Void)
}
@objc protocol LegacyProtocol {
    func runSpecimen(_ request: Data, withReply reply: @escaping (Data) -> Void)
}

final class Driver {
    private let service: String
    private let lock = NSLock()
    private var connections: [String: NSXPCConnection] = [:]
    private var credentials: [String: String] = [:]
    init(_ service: String) { self.service = service }
    func emit(_ tag: String, _ event: String, _ fields: [String: Any] = [:]) {
        lock.lock(); defer { lock.unlock() }
        var record = fields
        record["tag"] = tag; record["event"] = event; record["client_pid"] = Int(getpid())
        let data = try! JSONSerialization.data(withJSONObject: record, options: [.sortedKeys])
        FileHandle.standardOutput.write(data); FileHandle.standardOutput.write(Data("\n".utf8))
    }
    private func observation(_ data: Data, credential: String?) -> [String: Any] {
        var value = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] ?? [:]
        if let credential, let token = value.removeValue(forKey: "reservation_id") as? String {
            lock.lock(); credentials[credential] = token; lock.unlock()
        } else { value.removeValue(forKey: "reservation_id") }
        return ["received_bytes": data.count,
                "sha256": SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined(), "control": value]
    }
    func command(_ value: [String: Any]) throws {
        let operation = value["operation"] as! String
        let name = value["connection"] as? String ?? "owner"
        let tag = value["tag"] as! String
        if operation == "open" {
            let connection = NSXPCConnection(machServiceName: service, options: [])
            connection.remoteObjectInterface = value["legacy"] as? Bool == true
                ? NSXPCInterface(with: LegacyProtocol.self) : NSXPCInterface(with: ReservationProtocol.self)
            connection.invalidationHandler = { self.emit(name, "connection_invalidated") }
            connection.interruptionHandler = { self.emit(name, "connection_interrupted") }
            connections[name] = connection; connection.resume(); emit(tag, "opened"); return
        }
        guard let connection = connections[name] else { throw NSError(domain: "driver.missing_connection", code: 1) }
        if operation == "invalidate" { connection.invalidate(); emit(tag, "invalidated"); return }
        let proxy = connection.remoteObjectProxyWithErrorHandler { error in
            let native = error as NSError
            self.emit(tag, "rpc_error", ["domain": native.domain, "code": native.code])
        }
        if operation == "reserve" {
            let request: [String: Any] = ["protocol_version": 2,
                "attempt_id": UUID().uuidString, "lease_ms": value["lease_ms"] as? Int ?? 5000]
            let data = try JSONSerialization.data(withJSONObject: request)
            (proxy as! ReservationProtocol).reserveRunner(data) { bytes in
                self.emit(tag, "control_reply", self.observation(bytes, credential: tag))
            }
            emit(tag, "reservation_invoked"); return
        }
        let request = try Data(contentsOf: URL(fileURLWithPath: value["request"] as! String))
        if operation == "legacy_submit" {
            (proxy as! LegacyProtocol).runSpecimen(request) { bytes in
                self.emit(tag, "legacy_reply", ["received_bytes": bytes.count])
            }
            emit(tag, "legacy_invoked"); return
        }
        let key = value["credential"] as? String ?? "wrong"
        lock.lock(); let token = credentials[key] ?? UUID().uuidString; lock.unlock()
        (proxy as! ReservationProtocol).runReservedSpecimen(request, reservation: token) { host, bytes in
            if host {
                self.emit(tag, "host_reply", ["data_base64": bytes.base64EncodedString(), "received_bytes": bytes.count])
            } else { self.emit(tag, "submission_refused", self.observation(bytes, credential: nil)) }
        }
        emit(tag, "submission_invoked")
    }
}

@main struct Main {
    static func main() {
        guard CommandLine.arguments.count == 2 else { exit(2) }
        let driver = Driver(CommandLine.arguments[1])
        DispatchQueue.global().async {
            while let line = readLine() {
                do {
                    let value = try JSONSerialization.jsonObject(with: Data(line.utf8)) as! [String: Any]
                    try driver.command(value)
                } catch { driver.emit("driver", "local_error", ["message": String(describing: error)]); exit(3) }
            }
            exit(0)
        }
        RunLoop.current.run()
    }
}
