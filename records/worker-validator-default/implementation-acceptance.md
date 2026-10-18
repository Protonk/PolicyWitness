# Validator default implementation acceptance

Status: implemented, reviewed and accepted against the signed app. Associated
[implementation plan](../../runner/Sources/PWRunnerCore/VALIDATOR-DEFAULT-REFACTOR-PLAN.md).

## Implemented selection

The default validator path is now the host's service bundle followed by
`Contents/MacOS/sb_api_validator`. Resolution does not consult executable
availability or compute an app-level alternative. An admitted explicit
`validator_executable_path` still takes precedence. A narrow internal bundle-URL
argument supports disposable-layout controls; the production default remains
`Bundle.main.bundleURL` and introduces no request control.

Existing collection eligibility and native spawn reporting remain unchanged.
A reached failed launch retains the selected path and native return. Earlier
failure or no eligible queries produces no validator launch fact. Supported
built-in and external bundles already carry the embedded helper; manually
arranged older layouts no longer receive an implicit fallback.

Source comments now distinguish supplied overrides, selected bytes and observed
execution. Inert or unreached controls and sanitized/absent echoes retain their
existing semantics. The runner reference and architecture account describe the
single default. There is no new schema, mode, dynamic allowance record or native
intervention instrumentation. Wire versions remain 5/23/7 and layout is unchanged.

## Reviewed source and signed build

Base: `6380645181bf87f1d0ac70ea2b3188378fc16761`.
[implementation-source.json](implementation-source.json) identifies changed
source/test/doc contents and modes; unchanged inputs come from that base.
Later plan statuses, acceptance records and retention entries are bookkeeping.
The coordinator and a separate agent reviewed production behavior, test
observations and documentation before acceptance.

```sh
make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'
```

The [build log](implementation-build.log) retains output with trailing whitespace
trimmed. The app, ZIP and standalone guide were produced; eight executables and
two seals passed Developer ID, hardened-runtime and secure-timestamp checks.
Worker identity is
`4cb19db043606894ace2e978434f8805edf4c79245f3588cc68a33b36deca9e8`.
This is development acceptance, not notarization/release acceptance.

The build and first two runs used the
[pre-receipt-fix snapshot](pre-receipt-fix-source.json). The final source differs
only in one test-output expression in `OrderingTests.swift`: buffered `print`
became `FileHandle.standardOutput.write` of the complete prefixed JSON line.
Production sources, assertions, fixtures and build inputs are identical. The
coordinator and independent reviewer verified the exact delta; reversing it
reproduces the earlier file hash. Swift test sources are outside the app and
worker-identity input sets, so the signed app was retained unchanged.

## Verification

Commands ran from the repository root outside the automation sandbox, through
the checkout-locked dispatcher with fresh managed output:

```sh
PW_TEST_OUT_DIR=tests/out/runs/validator-selection-focused-20261018 tests/run.sh \
  --case runner_unit/pwrunner_core_unit_executable
PW_TEST_OUT_DIR=tests/out/runs/validator-selection-default-20261018 tests/run.sh
PW_TEST_OUT_DIR=tests/out/runs/validator-selection-receipts-20261018 tests/run.sh \
  --case runner_unit/pwrunner_core_unit_executable \
  --case source_drift/limits_documentation \
  --case source_drift/contract_versions \
  --case source_drift/architecture_documentation \
  --case source_drift/generator_contract
```

The initial [focused run](../../tests/out/runs/validator-selection-focused-20261018/run.json),
`20261018T215026Z_552be791`, passed its one case, including all 465 Swift tests.
The [full default run](../../tests/out/runs/validator-selection-default-20261018/run.json),
`20261018T215123Z_e8874e1f`, passed all 194 cases, including all 465 Swift tests,
native worker/phase/extension/exec controls, C/Swift layout agreement, signed
CLI validator failures and dossier compatibility.

The original logs retain mixed buffered and direct stdout writes: progress
messages can split receipt JSON lines. This is a test-output issue, not a failed
assertion or missing native observation. Original artifacts remain intact.
The one-line output correction follows the existing TestKit convention. It
prevents this mixed-buffering issue without claiming atomicity against arbitrary
other writers. The user's separate harness follow-up is to standardize retained
receipts as required JSON artifacts and keep console output diagnostic, with a
shared console writer and focused large-record/progress controls.

The [post-correction run](../../tests/out/runs/validator-selection-receipts-20261018/run.json),
`20261018T220505Z_efebca1e`, passed all five selected cases, including all 465 Swift tests.
All three runs had no skips, unrun cases or harness errors; their inspected app
was valid and unchanged. The final 19 source hashes and modes match the snapshot.
Generated-copy, link and whitespace checks passed.

[acceptance-credits.json](acceptance-credits.json) maps every default case to its
credited run: the five affected cases use the post-correction run, and the other
189 use the full run. Dependency review traced the test executable through
`Package.swift`/`main.swift`, plus the four source checks that cite or copy the
changed Swift test. Other default cases neither execute its receipt statement
nor require its bytes: source-list checks inspect `Sources`, the admission
control copies `ServiceAdmissionTests`/`TestKit`, and host controls compile their
own mains. The unchanged production app retains the live-case credits. These
are reviewed applicability judgments, supported by exact delta and artifact
checks, not a claim that hashes alone establish dependency coverage.

The [run account](implementation-runs.json) retains canonical case outcomes,
run identities and configuration. Managed runs retain commands, equipment,
source inputs and artifact inventories. Raw test output is gitignored and
available locally; credited runs are pinned in the retention index.

The new controls establish the bundle-local default in nested and standalone
layouts with local helpers present, absent and non-executable and executable
app-level decoys. Separate service observations retain default and explicit
override precedence, including an admitted empty override.

The six post-correction receipts in the
[Swift test log](../../tests/out/runs/validator-selection-receipts-20261018/suites/runner_unit/pwrunner_core_unit_executable/artifacts/pwrunner_core_tests.log)
parse as complete individual JSON records. Native reached launches retain the
exact selected local path and native return, ENOENT (2) or EACCES (13), matching the
encoded spawn-failure evidence; worker acknowledgement and attempts remain
available. For each unavailable helper, an excluded-query phase makes zero
validator calls and independently creates bytes `fixture-effect`, with
`not_needed` collection and no validator failure. An earlier worker-spawn
refusal likewise makes zero validator calls and retains `not_reached` without
validator subprocess or spawn-failure evidence. The receipts contain actual
native-call observations and encoded replies; independent file contents are
asserted before the owned temporary layout is removed.

Temporary layouts and lifecycle fixtures establish path selection and native
launch/error behavior, not a new live external-runner installation or helper
byte authentication. Existing signed CLI cases separately retain successful
validator, explicit override, phase, dossier and failure-path compatibility.
No release protocol, eligibility predicate or cleanup-policy change was made.
