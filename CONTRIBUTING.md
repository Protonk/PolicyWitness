# Contributing to PolicyWitness

PolicyWitness is a research/teaching tool. Contributions are welcome, but “the product” here is not just code — it’s **inspectable behavior** plus the written contracts that explain what that behavior means.

Related docs:

- CLI contract: `controller/README.md`
- Runner architecture: `runner/README.md`
- Signing/build: `SIGNING.md`
- Tests: `tests/README.md`

## What good contributions look like

### Documentation and tests are part of the product

If a change affects behavior, outputs, or safety boundaries, it needs matching words and some coverage.

### Reach the most integrated test you can

Tests should fail when the code is wrong — and the more integrated the test, the less surface for the test itself to be wrong. End-to-end through the CLI is the most integrated; an `_test_overrides`-driven suite is next; a unit test against an internal helper is the last resort. Each step down the ladder is one more thing that could be wrong about your *test* rather than about the *code*: a unit test against a stub-shaped classifier can pass while the real classifier is broken. If the integrated path isn't reachable, treat that as information about the production code — usually a boundary worth exposing as an override — not a license to ship the unit test.

### Write Swift like you want it trivially reverse-engineered

The Swift runner is intentionally inspection-friendly. Optimize for clarity over cleverness:

- Prefer explicit types and straightforward control flow.
- Keep the JSON wire types small and stable (`runner/PWRunnerAPI.swift`).
- Avoid metaprogramming / reflection that makes traces and disassembly noisy.
