# Contributing to PolicyWitness

PolicyWitness is a research/teaching tool. Contributions are welcome, but “the product” here is not just code — it’s **inspectable behavior** plus the written contracts that explain what that behavior means.

Related docs:

- CLI contract: `runner/README.md`
- Runner architecture: `xpc/README.md`
- Signing/build: `SIGNING.md`
- Tests: `tests/README.md`

## What good contributions look like

### Documentation and tests are part of the product

If a change affects behavior, outputs, or safety boundaries, it needs matching words and some coverage.

Preferred coverage options (in roughly increasing integration cost):

- Rust unit tests for pure logic
- Rust integration tests in `runner/tests/`
- Smoke scripts in `tests/suites/smoke/` against a built `PolicyWitness.app`

### Write Swift like you want it trivially reverse-engineered

The Swift runner is intentionally inspection-friendly. Optimize for clarity over cleverness:

- Prefer explicit types and straightforward control flow.
- Keep the JSON wire types small and stable (`xpc/PWRunnerAPI.swift`).
- Avoid metaprogramming / reflection that makes traces and disassembly noisy.

## Building

The build produces a single distributable artifact:

- `PolicyWitness.app` (and `PolicyWitness.zip` for notarization)

Canonical signing/packaging procedures live in `SIGNING.md`.

The build depends on a small bundle layout contract:

- `Contents/MacOS/policy-witness`
- `Contents/MacOS/pw-runner-client`
- `Contents/XPCServices/PWRunner.xpc`
- `Contents/Resources/Evidence/manifest.json` + `symbols.json`

If you add/remove embedded executables, update `build.sh`, Evidence generation (`tests/build-evidence.py`), and any tests that assert bundle layout.

## Common contributor tasks

### Add a new probe attempt type (runner)

1. Extend the request/response types in `xpc/PWRunnerAPI.swift` (attempt kind/action, and the matching sandbox_check filter semantics).
2. Implement the attempt in `xpc/PWRunnerServiceHost.swift`.
3. Add a specimen fixture under `tests/fixtures/pw_runner/`.
4. Add at least one check:
   - `runner/tests/cli_integration.rs` (integration), or
   - a smoke script under `tests/suites/smoke/`.

### Improve run inspection (TUI)

The repository ships a minimal evidence-ledger TUI under `laboratory/`. If you change the `lab_summary.json` schema, update the TUI and its fixtures under `tests/fixtures/pw_lab/`.
