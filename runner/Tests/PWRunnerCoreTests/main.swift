import Foundation

let tk = TestKit()

FileHandle.standardOutput.write(Data("PWRunnerCore unit tests\n".utf8))

runSandboxApplyTests(tk)
runEnvelopeInvariantTests(tk)
runPredictionUnavailableTests(tk)
runFilterKindValidationTests(tk)
runCWorkerTests(tk)
runCWorkerValidatorTests(tk)
runAugmentTests(tk)

FileHandle.standardOutput.write(Data("\n\(tk.summary())\n".utf8))
exit(tk.exitCode())
