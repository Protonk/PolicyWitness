# I2: exact compiled-capture boundary preparation

Prepared for coordinator review; no build, compiler, tests, dispatcher inspection,
native trials, formatter checks or generator checks ran. The sleep checkpoint
remains before execution. Basis: sibling investigation `../investigations/evidence-report.md`
(E2) and root [outflow plan](../../../READER-OUTFLOW-PLAN.md) (I2).

## Changes and contract judgment

[capture.c](../../../tests/suites/runner_abi_layout/capture.c) adds a dedicated
exact-capacity control before the existing small-object controls. A literal
`1024 * 1024` expected capacity is statically compared with the production cap.
Its separately allocated source contains 1 MiB plus one readable byte, filled
with a deterministic pattern depending on low and high index bits. The test
constructs the private layout independently, as the existing fixture does.

The successful call asserts completion, captured status, PID, nonce, profile
type, the exact independent length, all payload bytes, SHA-256, and an unchanged
destination guard byte. The excessive call uses that same readable allocation
at 1 MiB plus one byte, a fresh receipt and a reset destination; it asserts
completed unsupported status, zero captured length and no destination writes.
Existing unsupported-type, unreadable-object/payload, malformed-parameter,
selected-byte and parameter-digest controls remain.

The [suite README](../../../tests/suites/runner_abi_layout/README.md) describes
the assertions without claiming a recorded pass. Production behavior,
`docs/limits.json`, receipt readers and generated files are unchanged. No request,
wire or ABI contract changes, identity regeneration or layout-golden update are
required by these test-only edits.

## Assertion independence and limits

Expected size and allocation length do not read the limit manifest or derive
from the implementation cap. Changing the cap alone fails the static assertion;
rejecting equality fails captured status; truncating the read fails exact length,
full byte comparison or the digest. Expected SHA-256 is computed from the source
and independently specified length before calling capture, without calling any
production capture/digest helper or reading captured fields. Both use
CommonCrypto as the underlying SHA-256 primitive: this checks capture's selection
of bytes and extent, not CommonCrypto's cryptographic implementation. Full byte
comparison independently establishes the copy. Fresh receipts avoid stale
completion/status/length passing the new checks.

This is native memory-read/capture coverage against a constructed object. It
does not compile or apply sandbox policy, qualify private compiler layout on a
new OS, or establish Swift receipt availability after worker execution.
Compilation and actual macOS memory-read behavior remain unverified until the
deferred run. Documentation owners must not credit observed exact-size success
before that run passes.

## Deferred validation

Canonical selector, after the user's checkpoint:

```sh
PW_TEST_OUT_DIR=tests/out/runs/lookback-capture-boundary tests/run.sh --case runner_abi_layout/c_swift_layout_agreement
```

Use a fresh output name if that path exists. The existing dispatcher case
compiles and invokes `capture.c`; no new registration is needed. It requires the
macOS environment, Xcode Command Line Tools clang and macOS SDK, plus the normal
harness Python environment; it does not require a signed app or runner install.
Keep assertions enabled (the existing native compile command does not set
`NDEBUG`) and `PYTHONOPTIMIZE` unset. Preserve logs/receipts through the dispatcher.
If automation containment refuses a required operation, inspect the diagnostic
and follow the same-command unsandboxed retry rule in
[test guidance](../../../tests/AGENTS.md#sandboxed-automation-harnesses).

No separate application build is required for this isolated fixture. The
coordinator owns any broader build and verification needed by the other edits.
