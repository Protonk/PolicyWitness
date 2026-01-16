# Test Coverage Index

This map summarizes what each suite covers and what you can claim when it
passes. For exact invariants and fixtures, see the per-suite README files under
`tests/suites/<suite>/`.

Tiers:
- **Baseline**: expected on supported hosts; run by default in `tests/run.sh --all`.
- **Extended**: broader coverage but host-dependent skips are normal.
- **Diagnostic**: validates known OS anomalies; not a product guarantee.
- **Opt-in**: manual, resource-sensitive, or environment-specific tests.

| Suite | Tier | Primary claim | Requires | Notes / artifacts |
| --- | --- | --- | --- | --- |
| `preflight` | Baseline | Codesign + entitlements metadata matches the built app bundle | `PolicyWitness.app` | `tests/out/suites/preflight/.../preflight.json` |
| `unit` | Baseline | Controller logic is correct at the unit level | Cargo toolchain | `tests/out/suites/unit/.../cargo-test-bins.log` |
| `integration` | Baseline | CLI contract + runner envelope are stable end-to-end | Built app + XPC | Uses fixtures under `tests/fixtures/pw_runner/` |
| `smoke` | Baseline | End-to-end run works and basic instrumentation ports respond | Built app + XPC | Quick scripts; see `tests/suites/smoke/` |
| `blackbox_menagerie` | Extended | SBPL + compiled-bytes ingestion and evidence correlation | Built app | Compiled profile cases may skip |
| `blackbox_e2e` | Extended | Evidence bundle matches expectations per step | Built app | Skips on host `sandbox_check` anomalies |
| `anomalies` | Diagnostic | Known OS anomalies + sandbox_check cross-check consistency | Host-dependent | Cross-check may skip if tooling is unavailable |
| `opt_in` | Opt-in | Heavy/host-sensitive paths (logs, DYLD, launchd) | See registry | `tests/OPT_IN_TESTS.md` |

## Expected skips by suite

- `preflight`: no expected skips; missing app or codesign issues should fail.
- `unit`: no expected skips; missing toolchain should fail.
- `integration`: no expected skips; missing app should fail.
- `smoke`: skip when `PolicyWitness.app` is missing or unbuilt.
- `blackbox_menagerie`: skip when `PolicyWitness.app` is missing; compiled profile registration not permitted; mismatch evidence not observed (host variance).
- `blackbox_e2e`: skip when `PolicyWitness.app` is missing; host `sandbox_check` anomalies; compiled profile registration not permitted (BBX-003).
- `anomalies`: skip when `PolicyWitness.app` is missing; cross-check tooling unavailable.
- `opt_in`: skip when required resources are unavailable (toolchain, GUI session for launchd bootstrap, sandboxed harness for XPC/log capture).
