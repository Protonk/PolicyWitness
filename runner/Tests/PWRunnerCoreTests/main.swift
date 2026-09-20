import Foundation

let tk = TestKit()

FileHandle.standardOutput.write(Data("PWRunnerCore unit tests\n".utf8))

runSandboxApplyTests(tk)
runEnvelopeInvariantTests(tk)
runPredictionUnavailableTests(tk)
runFilterKindValidationTests(tk)
runDriftClassifierTests(tk)
runHostOutcomeClassifierTests(tk)
runAttemptOutcomeMappingTests(tk)
runLimitsContractTests(tk)
runCWorkerTests(tk)
runCWorkerLifecycleTests(tk)
runWorkerEvidenceTests(tk)
runCWorkerValidatorTests(tk)
runValidatorEvidenceTests(tk)
runDiagnosticTransportTests(tk)
runAugmentTests(tk)
runListenerConfigTests(tk)
runAppliedProfileCaptureTests(tk)

FileHandle.standardOutput.write(Data("\n\(tk.summary())\n".utf8))
exit(tk.exitCode())
