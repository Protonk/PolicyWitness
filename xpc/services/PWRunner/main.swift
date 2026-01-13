import Foundation

let listener = NSXPCListener.service()
let delegate = PWRunnerSessionDelegate()
listener.delegate = delegate
listener.resume()
RunLoop.current.run()

