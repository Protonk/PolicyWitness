// Installed only in the disposable SwiftPM copy by mutations.py.
import Darwin
import Foundation
let tk = TestKit()
runOrderingGateControl(tk)
FileHandle.standardOutput.write(Data("\n\(tk.summary())\n".utf8))
exit(tk.exitCode())
