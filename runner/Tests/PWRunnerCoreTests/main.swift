import Foundation

let tk = TestKit()

FileHandle.standardOutput.write(Data("PWRunnerCore unit tests\n".utf8))

runSandboxApplyTests(tk)
runWorkerClassifyTests(tk)
runWorkerHelperTests(tk)
runWorkerFrameTests(tk)
runEnvelopeInvariantTests(tk)

FileHandle.standardOutput.write(Data("\n\(tk.summary())\n".utf8))
exit(tk.exitCode())
