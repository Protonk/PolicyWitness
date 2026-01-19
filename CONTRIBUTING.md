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

Preferred coverage options (in roughly increasing integration cost):

- Rust unit tests for pure logic
- Rust integration tests in `controller/integration/`
- Smoke scripts in `tests/suites/smoke/` against a built `PolicyWitness.app`

### Write Swift like you want it trivially reverse-engineered

The Swift runner is intentionally inspection-friendly. Optimize for clarity over cleverness:

- Prefer explicit types and straightforward control flow.
- Keep the JSON wire types small and stable (`runner/PWRunnerAPI.swift`).
- Avoid metaprogramming / reflection that makes traces and disassembly noisy.
