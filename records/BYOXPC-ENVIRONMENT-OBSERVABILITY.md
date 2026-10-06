# BYOXPC environment settings do not have a worker read-back

Investigation, 2026-10-06. No product changes.

## Observation

Two installations supplied `PW_BYOXPC_CANARY=byoxpc-canary` and
`DYLD_PRINT_ENV=1` through `runner install --env`. One host had no entitlements;
the other had `com.apple.security.cs.allow-dyld-environment-variables = true`.
The saved launchd plists and job listings contain the settings in both cases.
The embedded worker and validator retained their build signatures.

Under an allow-all specimen, `/usr/bin/env` exited zero without stdout. An
existing process-inspection fixture, run as a second exec attempt, explicitly
reported `env_count: 0`, `env_value: null`, `complete: true`, and a PID matching
the envelope's child PID, with successful child exit. Both installations gave
these observations.

This witnesses the exec child's empty environment. It does **not** establish
whether the variable was present in the host or worker, or where a DYLD
variable disappeared. The worker explicitly supplies `empty_envp` to
`posix_spawn` in [pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c).
Consequently this route cannot discriminate an empty worker environment from
a populated one. Launchd configuration is not a read-back of process state.

The investigation's original proposed `/usr/bin/env` inference was therefore
invalid. The host-to-worker environment question remains unobserved here;
changing an environment contract or adding a new probe was outside scope.

## Reproduction and receipts

Install two owned copies with identical `--env` arguments and the two host
entitlement plists above. Build the existing
[exec fixture](../tests/fixtures/exec/build.sh), placing its executable in an
owned directory under `/private/tmp`. Submit two `exec/spawn` steps under
`(version 1)(allow default)`: `/usr/bin/env`, then the fixture with arguments
`--inspect byoxpc-environment --read-fd 200`. Compare child exit and explicit
fixture reports, not just top-level `normalized_outcome`.

The [without-entitlement receipts](../tests/out/runs/byoxpc-investigation-20261006/env-disabled-tmp/)
and [with-entitlement receipts](../tests/out/runs/byoxpc-investigation-20261006/env-enabled-tmp/)
contain exact specimens, launchd plists, signing read-backs and
`environment/stdout` envelopes. Both copies were removed with absence verified.

Earlier runs with the observer executable under this checkout's Desktop path
returned top-level `ok`, while that child hit its ten-second deadline without
an inspection report. Those observations survive in
[env-disabled](../tests/out/runs/byoxpc-investigation-20261006/env-disabled/)
and [env-enabled](../tests/out/runs/byoxpc-investigation-20261006/env-enabled/).
The same fixture bytes worked from `/private/tmp`. The cause of the
location-sensitive failure is unassigned; empty or missing output from those
failed children supplies no environment evidence.

## Scope

macOS 14.8.9 (23J631), arm64, user scope, Team `42D369QV8E`. The selected app
reports build `435`, `33ad847-dirty`; the checkout was `e2115cf`. Its exact
[inventory](../tests/out/runs/byoxpc-investigation-20261006/baseline/source-inventory.json)
was unchanged after the investigation. No request test overrides were used.
The linked receipts and orchestration are gitignored local evidence, pinned
in `tests/RETAINED.json`. This result concerns observation boundaries, not a
general claim that DYLD exceptions have no effect.
