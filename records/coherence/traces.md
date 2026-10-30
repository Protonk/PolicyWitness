# Trace findings and verification sequence

Codex, 2026-10-30. The associated plan fixes the initial sample. This file records
new attributable findings; earlier acceptance records remain historical and unchanged.

Initial state: isolated branch `review/pytest-coherence` at review baseline
`809ef178`; no execution observations or repairs yet. The accepted checkout is
`77eb9875` with its three pre-existing untracked review paths. All older worktrees,
pins and protected resources remain untouched.

## Localized finding: portable evidence account

Direct trace 1 found a stale consumer account: `docs/SIGNING.md` says only
portable schema 2 is supported, and `release_runs.battery_source` uses that same
obsolete description in three diagnostics. The completed candidate emits schema
3 with a producer contract; schema 2 remains historical transport evidence, with
positive producer identification at the release boundary. `tests/README.md`
already describes both correctly. The immediate sibling scan found no other
current guide making the schema-2-only claim. The preflight README's schema-2
*provenance record* describes a different object and remains correct.

Repair the guide and diagnostics, without changing admission or historical
allowlist policy. Expected discrimination: schema 2 and source-bound schema 3
positive controls still verify; unsupported format, missing family declaration,
missing terminal ownership and false historical downgrade still refuse. Existing
release controls and pytest portable controls cover those behaviors; generator
and source checks cover the edited guide. No production/oracle change is needed.
