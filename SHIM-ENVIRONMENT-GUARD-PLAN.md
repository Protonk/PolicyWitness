# Refuse an unvalidated toolchain environment before a shim runs

## Problem and intended result

The `/usr/bin` shims for `python3` and `git` locate their tool through
`xcodebuild -sdk <SDKROOT or macosx> -find <tool>` and validate a custom
`DEVELOPER_DIR` by running its `xcodebuild`. When that lookup fails, because
`SDKROOT` names no SDK or `DEVELOPER_DIR` is a stand-in without a working
`xcodebuild`, the shim asks `xcode-select` to request a Command Line Tools
installation. That is a machine-wide side effect on the developer's Mac, not a
test outcome, and probes that set those variables by hand have triggered it
from this repository. Outside `build.sh`, the only protection today is that
nobody does it.

The intended result: a control or probe cannot hand a shim an unvalidated
`SDKROOT` or `DEVELOPER_DIR` through the test infrastructure. The
infrastructure refuses before the shim starts, the refusal names the variable
and its value, and a control establishes that the refusal fires. Prose
warnings about the hazard then have nothing left to say.

Follow [CONTRIBUTING.md](CONTRIBUTING.md#planning-a-change) and
[tests/AGENTS.md](tests/AGENTS.md) when executing it.

## What already exists

- [`build.sh`](build.sh) reads its caller's `SDKROOT` from its starting
  environment and keeps it out of the environment until
  `xcrun --sdk … --show-sdk-path` resolves it, so its git shim never sees an
  unresolved SDK request. Its Python steps start directly.
- [`python_start.sh`](tests/lib/python_start.sh) resolves the developer
  directory with `xcode-select -p` and requires an executable
  `usr/bin/python3`. The lock front end, build and dispatcher each source
  it. A stand-in without Python refuses before a shim can run; a stand-in
  with an executable Python still passes. This resolver is the place for a
  developer-directory guard at these entry points.
- The checkout-lock owner's `child_env` in
  [`tests/lib/checkout_lock.py`](tests/lib/checkout_lock.py) drops stale
  claims and adds its own, preserving other values unchanged. It no longer
  restores bound requests. The shell front end records an environment
  witness, and the CLI owner and build session start compare it without
  repairing values. A witness does not validate an SDK or developer directory.
  A bogus SDKROOT can still reach git or a leaf Python shim in a case.
- `control_sdk_unavailable` in
  [`build_refusals.py`](tests/suites/preflight/opt_in/build_refusals.py)
  exercises the SDK refusal without exposing any shim: only a
  `sandbox-exec`-contained `xcrun` sees an unconfigured developer directory,
  through a `BASH_ENV` wrapper, and the control asserts that
  "requesting installation" never appears in the build output. Its
  `fake_developer_dir` fixture is the pattern for a developer directory that
  no shim may run with.
- `build_toolchain_switch` (opt-in) sets `DEVELOPER_DIR` and `SDKROOT` for
  real Xcode and Command Line Tools directories, which resolve by
  construction. Any guard must keep passing them.

## Approach

A short survey first: every place under `tests/` that starts a process with
`DEVELOPER_DIR` or `SDKROOT` set or modified, and whether it passes through
`child_env` or calls `subprocess` directly. The survey decides between two
mechanisms; it does not add both.

1. **A runtime guard on the shared spawn path.** `child_env` refuses a
   nonempty `SDKROOT` that `xcrun --sdk "$SDKROOT" --show-sdk-path` cannot
   resolve, and a `DEVELOPER_DIR` whose `usr/bin/xcodebuild` is absent or not
   executable, before the child starts, naming the variable and value. Direct
   `subprocess` callers that set either variable are routed through the owner
   or through one helper that applies the same check. The guard checks a value
   by existence and by resolution through `xcrun`, never by starting a shim.
   This is the lighter option if the survey finds few bypasses.
2. **A static drift check.** A `source_drift` case that fails when a test
   source assigns either variable into an environment that reaches a
   `/usr/bin` shim without the helper. Preferred only if the spawn sites are
   too varied to route through one path.

## Verification

- A control beside `control_sdk_unavailable` supplies an `SDKROOT` naming no
  SDK, and separately a stand-in `DEVELOPER_DIR`, to the guarded path and
  expects the refusal with the variable named. It keeps the existing
  assertion that "requesting installation" never appears, and runs under the
  same `sandbox-exec` containment the fixture already uses, so an escaped
  shim could not reach `xcode-select` even if the guard failed.
- `build_toolchain_switch` still passes: real toolchain directories pass the
  guard, and the provenance record still names the caller's choice.
- `source_drift` and the `preflight` opt-in controls are green, and the
  default battery is unchanged.
- Nothing reproduces the installation request on the development machine.

## Where it stops

- `build.sh`'s own request handling is unchanged.
- Shims started outside the test infrastructure, such as a probe run by hand
  in a shell, are out of scope; the guard covers what the infrastructure
  spawns.
- No change to which variables a caller may set for a real toolchain.
