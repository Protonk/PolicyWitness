# Working in `runner/`

Read [README.md](README.md) for the source map, lifecycle and test seams. These
rules supplement the [root guidance](../AGENTS.md) for runner work, including
native helpers under `controller/tools/` and runner tests elsewhere in the tree.

## Preserve the runner boundaries

Keep sandbox API calls out of the host. The C worker compiles and applies the
specimen; the validator queries it. Preserve fresh hosts/workers, shared
single-use admission across connections and exit scheduling by the terminal
request owner. Keep orchestration in the host and post-apply attempts in the worker.

Preserve collection closure, release publication and worker acknowledgement.
Do not infer `query_first` from paired fields alone. Changes to the worker wait,
release store or eligibility rule require
[the ordering mutation control](../tests/OPT_IN_TESTS.md), as specified by the
root guidance. Retain partial native observations and independent cleanup
facts; a summary or requested signal must not replace an observed effect.

For request or evidence changes, update affected admission, producers, transport,
independent readers, fixtures and documentation together. Follow the
[wire contract](../docs/CONTRACT.md) and
[evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md) for versions and
claim ownership. Edit generator inputs and regenerate through the
[owning tools](../tests/suites/source_drift/README.md#generator-contracts).
Native source additions/moves require the Meson target; identity/layout changes
also require worker-identity regeneration, C/Swift agreement and layout-golden
review.

Before adding or changing an excluded pair in `predictionUnavailableOpFilters`,
retain empirical evidence
using [verify_filter_id.sh](../tests/suites/witness_contract/harness/verify_filter_id.sh)
and independent native observations. Read the tool's stated limits: candidate
filter matches do not establish general prediction/enforcement agreement.
Update the user guide's exclusion pairs and planner/unit controls together.

## Swift runner unit tests (SwiftPM)

Follow [test-selection guidance](../tests/AGENTS.md#choose-the-most-integrated-test-that-can-establish-the-behavior):
use the public CLI or an existing override when it can establish the behavior.
Use unit controls for internal branches or observations an ordinary specimen
cannot reliably produce. Constructed classifier inputs establish interpretation;
live XPC, launchd and kernel behavior require their corresponding suites.

**Adding a new unit test file.**

1. Add `Foo*Tests.swift` under [Tests/PWRunnerCoreTests/](Tests/PWRunnerCoreTests/),
   exporting `runFooTests(_ tk: TestKit)`.
2. Group assertions with `tk.group("name") { tk.run("case") { try expect...(...) } }`.
3. Register `runFooTests(tk)` in [main.swift](Tests/PWRunnerCoreTests/main.swift)
   with a one-line comment describing what it pins. Discovery alone does not
   run the tests.
4. Run `tests/run.sh --suite runner_unit --suite runner_c_worker_harness`
   against a signed build. The [suite wrapper](../tests/suites/runner_unit/README.md#run)
   provides fixture setup and result checks.

Driver tests use the app selected by `PW_APP_DIR`, defaulting to the distribution.
Build a matching candidate through the [signed pipeline](../docs/BUILD.md):
successful Swift compilation alone does not establish worker ABI/source-identity
agreement. Use [tests/AGENTS.md](../tests/AGENTS.md) for coordinated suite
selection, fresh output directories, evidence reuse and cleanup.

Build fixtures outside the inspected app. The lifecycle fixture never applies
a sandbox; controlled native-call failures and malformed validator output
establish transport/lifecycle behavior, not kernel attribution. Tests injecting
`kill`/`waitpid` faults through `ChildProcessCalls` own independent cleanup of
children they leave unreaped. When internal access is needed, use
`@testable import` and the narrowest necessary visibility change without
changing production behavior.

## Testing `normalized_outcome` failure paths via `_test_overrides`

Use [the test seam](README.md#test-seam-_test_overrides) to steer an input at a
real production boundary. Never add an override that fabricates a result such
as `force_normalized_outcome`; use a classifier unit test when the boundary
cannot be exercised.

For an override-driven CLI specimen, assert the expected outcome, supporting
native/transport evidence and the applicable override echo. The
[pre-application witness](../tests/suites/witness_contract/README.md#failure-before-published-application)
documents its bounded outcome alternatives. Diagnostics should identify the
real failed boundary without requiring exact English wording.

Check structural fields for that boundary. No observed worker means no
`runner_subprocess`; it does not generally mean `steps == []`. Admission refusals
have no steps, while a spawn failure with a nonempty plan retains synthetic
step records. Verify withheld and retained evidence independently.

**Adding a new override.**

1. Update the optional property, initializer, `CodingKeys` and decoding in
   [`PWRunnerTestOverrides`](Sources/PWRunnerCore/PWRunnerAPI.swift) together,
   preserving accepted requests and meanings.
2. Update [the key table](README.md#test-seam-_test_overrides). Source drift
   verifies property/table agreement, not admission or behavior.
3. Pass the control through the request to the real boundary, preserving
   default behavior when absent. Launchd does not preserve the invoking shell's
   environment.
4. Retain the supplied control on applicable reply paths and preserve bounded
   refusal sanitization; invalid paths must not be echoed to satisfy a test.
5. Add an integrated case in an appropriate suite and update the
   [catalog](../tests/catalog.json), owning suite description and affected
   [outcome coverage](../tests/COVERAGE.md).

**Reading override evidence.** A non-null `test_overrides` object records
supplied controls, not proof they changed execution. Empty/default controls can
be inert; an earlier failure can prevent the selected boundary from running.
Admission refusals may omit unsafe echoed values. Use the actual observations
to establish the intervention and keep steered failure-handling evidence
separate from claims about the specimen's policy.

## Sandboxed automation harnesses

An automation harness's macOS sandbox can block runner XPC lookup
(`NSCocoaErrorDomain` 4099 or error 159), unified-log access
(`log: Cannot run while sandboxed`), signing-keychain access, and Meson's Swift
discovery when swiftc cannot write its module cache. It can also make
`codesign --verify` report an invalid signature for unchanged bytes. Request
escalation and rerun the same failing command once outside the automation
sandbox, without changing the artifact under investigation. Treat a signature
failure as environmental only if the unsandboxed verification passes;
investigate any failure that remains.

This warning is intentionally repeated for agents entering through different
workflows who may mistake harness restrictions for product defects.
[source_drift](../tests/suites/source_drift/README.md#intentional-guidance-agreement)
compares the first paragraph in all four locations; edit those copies together.
The explanations that follow it are local to each document.

When the harness blocks XPC lookup before host launch, the envelope reports
`normalized_outcome: "xpc_error"`, an error diagnostic, empty `steps` and no
`runner_subprocess`. The controller's fallback `sbpl-check` result in
`data.policy_check` establishes only whether the policy compiles; it says nothing
about worker execution. An `xpc_error` alone does not establish that the harness
caused it; use the diagnostic and the unsandboxed retry.

Log access can fail even when execution succeeds. A
`sandbox_log_capture.capture_status` of `blocked` with
`blocked_reason: "Cannot run while sandboxed"` leaves the execution result
unchanged and makes log correlation unavailable. Use `--no-log-capture` when
log capture is unnecessary for the runner behavior being investigated.
