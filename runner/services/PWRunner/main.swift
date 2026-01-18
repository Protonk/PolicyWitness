import Foundation

let args = Array(CommandLine.arguments.dropFirst())
var machServiceName: String? = nil
var idx = 0
while idx < args.count {
    if args[idx] == "--mach-service" {
        let next = idx + 1
        guard next < args.count else {
            fputs("missing value for --mach-service\n", stderr)
            exit(2)
        }
        machServiceName = args[next]
        idx = next + 1
        continue
    }
    idx += 1
}

let listener: NSXPCListener
if let machServiceName {
    listener = NSXPCListener(machServiceName: machServiceName)
} else {
    listener = NSXPCListener.service()
}
let delegate = PWRunnerSessionDelegate()
listener.delegate = delegate
listener.resume()
RunLoop.current.run()
