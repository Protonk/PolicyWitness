# runner/AGENTS.md

Use [runner/README.md](README.md) for implementation and test-harness details.
Follow these rules when adding runner tests or a `_test_overrides` boundary,
including tests maintained outside this directory.

## Swift runner unit tests (SwiftPM)

**When to add a unit test rather than an e2e suite.** Follow
[test-selection guidance](../tests/AGENTS.md#choose-the-most-integrated-test-that-can-establish-the-behavior):
use the CLI or `_test_overrides` when the behavior is reachable there. Use
`runner_unit` for internal helper branches or observations an ordinary specimen
cannot reliably produce, such as failed host kill/reap or publication followed
by abnormal exit. Keep behavior requiring XPC, launchd or the kernel sandbox
in the corresponding e2e suites. Constructed classifier inputs establish
interpretation separately from live observations.

**Adding a new unit test file.**

1. Add `Foo*Tests.swift` under [Tests/PWRunnerCoreTests/](Tests/PWRunnerCoreTests/),
   exporting `runFooTests(_ tk: TestKit)`.
2. Group assertions with `tk.group("name") { tk.run("case") { try expect...(...) } }`.
3. Register `runFooTests(tk)` in [main.swift](Tests/PWRunnerCoreTests/main.swift)
   with a one-line comment describing what it pins. File discovery alone does
   not run the tests.
4. Run `tests/run.sh --suite runner_unit --suite runner_c_worker_harness`
   against a signed build. Use the suite wrapper for fixture setup and result
   checking; [the suite README](../tests/suites/runner_unit/README.md#run)
   describes direct SwiftPM setup when needed.

**Rules for lifecycle and evidence tests.**

- Build fixtures outside the inspected app. The lifecycle fixture never applies
  a sandbox, so tests using it cannot claim a policy cause.
- A test injecting `kill`/`waitpid` faults through `ChildProcessCalls` owns
  independent cleanup of any fixture child it leaves unreaped.
- Treat controlled native-call failures and malformed validator output as
  transport and lifecycle evidence; they do not establish kernel attribution.

**Promoting `private` symbols to `internal`.** When a unit test needs an internal
helper, drop `private` so `@testable import` can reach it. Keep production
behavior unchanged.

## Testing `normalized_outcome` failure paths via `_test_overrides`

Use [the test seam](README.md#test-seam-_test_overrides) to steer a real failure
at a production boundary. Never add an override that fabricates a result such
as `force_normalized_outcome`. If a boundary cannot be exercised this way,
use a unit test against the classifier.

**Anatomy of an override-driven test.** Construct a normal specimen with a
`_test_overrides` block and run it through `policy-witness run`. Assert:

- `data.runner_result.normalized_outcome == "<expected>"`.
- `data.runner_result.error` names a real artifact of the failure, such as the
  hostile path or syscall.
- `data.runner_result.test_overrides.<key>` equals the submitted value, proving
  the override was admitted and retained.
- Downstream structural fields reflect the failure boundary, such as
  `runner_subprocess == null` when no worker was observed and `steps == []`.

The sole exception to the exact-outcome assertion is documented in
[Failure before published application](../tests/suites/witness_contract/README.md#failure-before-published-application).

**Adding a new override.**

1. Update the optional property, initializer, `CodingKeys` and decoding in
   [`PWRunnerTestOverrides`](Sources/PWRunnerCore/PWRunnerAPI.swift) together.
   Preserve existing requests and meanings; see [request contract evolution](../docs/CONTRACT.md#accepted-input-contract).
2. Document the key in [the test-seam table](README.md#test-seam-_test_overrides).
   `source_drift` checks property/table agreement, not admission or decoding.
3. Plumb it from request handling to the real OS-call boundary, defaulting to
   production behavior when unset. Host controls must travel in the request;
   launchd does not preserve the invoking shell's environment.
4. Mirror it into every result on the affected path with
   `test_overrides: parsed._test_overrides`.
5. Add an integrated case using the assertions above, in an existing suite when
   appropriate. Register it in [the catalog](../tests/catalog.json); keep new
   suite or outcome descriptions in [suite coverage](../tests/README.md#suite-coverage)
   and [outcome coverage](../tests/COVERAGE.md).

**Auditing override usage.** Inspect `data.runner_result.test_overrides` in the
retained envelope. A non-null value marks a steered run: its outcome is evidence
about classifier and error-handling behavior, not the specimen's policy.
