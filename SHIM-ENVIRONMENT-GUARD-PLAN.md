# Refuse an unresolvable SDK request before a developer-tool shim runs

## Problem and intended result

Most developer tools in `/usr/bin` are one shim: `make`, `python3`, `git`,
`clang`, `cc`, `otool`, `lipo`, `strings`, `dsymutil` and 69 other names are
links to a single file. When `SDKROOT` names a path that does not exist or a
name no SDK has, the shim's `xcodebuild -sdk <SDKROOT> -find <tool>` fails
and the shim asks for a Command Line Tools installation. That is a
machine-wide side effect on the developer's Mac, not a test outcome. A probe
run by hand from this repository has triggered it, despite written warnings
about exactly that. [SHIM-INSTALL-REQUEST-PROBE.md](records/SHIM-INSTALL-REQUEST-PROBE.md)
records a contained probe of which inputs cause the request and which do not.

The intended result:

- No repository entry point hands a shim an `SDKROOT` that names no SDK. The
  entry point refuses before any shim starts, naming the variable and its
  value.
- The checks that guard against the request can fail. Today they can only see
  a request that was actually sent.
- A probe of an SDK or developer-directory value has a contained way to run.
- The one entry point no repository code can protect, a shell starting
  `/usr/bin/make` with a bad `SDKROOT`, is documented.

Follow [CONTRIBUTING.md](CONTRIBUTING.md#planning-a-change) and
[tests/AGENTS.md](tests/AGENTS.md) when executing it.

## What the probe established

- The request needs `SDKROOT` naming a missing path or an unknown SDK name.
  An empty `SDKROOT`, or one naming an existing directory that is not an SDK,
  makes none.
- `DEVELOPER_DIR` does not cause it. No stand-in tried (missing, empty, holding
  the tool, holding `libxcrun.dylib`, Xcode-shaped with or without
  `xcodebuild`) made a request. A stand-in complete enough to run is a
  wrong-toolchain question, not an installation one.
- `/usr/bin/xcrun` and `/usr/bin/xcode-select -p` never make the request, so
  they can validate a value. `xcrun --sdk <path> --show-sdk-path` echoes any
  absolute path with status 0, so it validates nothing by itself;
  `--show-sdk-version` fails for a missing path and for a non-SDK directory.
- `SDKROOT=… make …` makes the request before make reads a makefile.
  `make target SDKROOT=…` exports the value to recipes, where a
  `/usr/bin/python3` step makes it; `$(MAKE)` is the real make and does not.
- The shim prints `requesting installation of command line developer tools`
  only when the request is sent. Where Mach lookups are denied it prints
  `and no install could be requested (perhaps no UI is present)` instead, and
  the unified log shows a denied lookup of
  `com.apple.dt.CommandLineTools.installondemand`.

## What already exists

- [`build.sh`](build.sh) keeps the caller's `SDKROOT` out of its environment
  until `xcrun --sdk … --show-sdk-path` names an existing directory and
  `--show-sdk-version` reports a number, and refuses otherwise at its `sdk`
  step. No shim it starts sees an unresolved request. That two-part test is
  the one a guard needs.
- [`python_start.sh`](tests/lib/python_start.sh) runs at the start of
  `build.sh`, the lock front end
  [checkout_lock.sh](tests/lib/checkout_lock.sh) and
  [tests/run.sh](tests/run.sh), before any shim. It runs only
  `xcode-select -p`. The owner and the dispatcher are direct Python, and the
  dispatcher's own commands (`caffeinate`, `launchctl`, `codesign`) are not
  the shim, so nothing before the first command or case starts one. After
  that, a
  case's `git`, `clang` or leaf `python3`, or a build script Cargo runs under
  `checkout_lock.sh -- cargo test`, inherits whatever `SDKROOT` the caller
  gave.
- The repository's own spawn sites are already safe. Each place under
  `tests/` that sets `SDKROOT` or `DEVELOPER_DIR` gives a process one of:
  - a value that resolves: `build_toolchain_switch`, and `control_sdk_requests`
    with `macosx` or the selected path;
  - a value `build.sh` removes before any shim:
    `control_sdk_requests`' empty and invalid requests;
  - a value only a contained `xcrun` sees: `contained_xcrun` and
    `fake_developer_dir` in
    [build_refusals.py](tests/suites/preflight/opt_in/build_refusals.py).
    Both profiles deny Mach lookups and process execution, allowing only
    `/usr/bin/xcrun` to execute. `fake_developer_dir` checks that
    `/usr/bin/true` is refused, then observes `xcrun`'s actual
    `invalid DEVELOPER_DIR path` diagnostic. The denied exec alone cannot
    establish that the profile applied;
  - a stand-in developer directory under a profile that forbids executing
    any shim: the resolver checks in
    [check_build_provenance.py](tests/suites/preflight/check_build_provenance.py)
    and [contract.py](tests/suites/source_drift/contract.py);
  - plain data: the `SDKROOT='/sdk'` in `check_build_provenance.py` reaches
    only `cargo_config`, which starts no process.

  The exposure is the caller's environment arriving through an entry point,
  and probes run by hand.
- Four assertions say "requesting installation" never appears: two in
  `build_refusals.py`, one each in `check_build_provenance.py` and
  `contract.py`. Under their containment a blocked attempt prints the other
  message, so they cannot fail on it. None currently sits where a shim could
  see a bad value, so nothing has been hidden.
- `build_toolchain_switch` (opt-in) sets `DEVELOPER_DIR` and `SDKROOT` for
  real Xcode and Command Line Tools directories. Any guard must keep passing
  them.

## Approach

1. **A detector that can fail.** One shared test helper reports a request,
   sent or blocked, from a process's output. It matches `requesting install`
   (both sent forms) and `no install could be requested`. Where a control
   also reads the unified log, it counts lookups of the installation service
   during the control. The four assertions use it.
2. **Refuse at the entry points.** The entry check validates a set, nonempty
   `SDKROOT` the way `build.sh` does: `xcrun --sdk "$SDKROOT" --show-sdk-path`
   must name an existing directory and `--show-sdk-version` must report a
   number. Otherwise it refuses with status 2, naming the value. An empty
   `SDKROOT` passes. It runs only `xcrun`, never a shim. It sits beside the
   resolver, so `tests/run.sh`, `checkout_lock.sh` and `build.sh` each apply
   it before any shim can start.

   **Decided:** an invalid caller request to `build.sh` refuses at the
   `admission` step, no longer at `sdk`. Every build passes through this
   check: a direct build when it hands itself to the front end, and a nested
   one when `build.sh` sources the resolver. One rule in one place, applied
   before any shim, is worth more than keeping the build's refusal where it
   was. Exempting the build path would need the front end to tell a build
   from other commands.

   The `sdk` step keeps its own `xcrun` test, unchanged. It still selects the
   SDK, and it still refuses a developer directory without one. Update the
   refusal's step and message in [build.json](docs/build.json), then
   regenerate. Also update `control_sdk_requests`' invalid case and the SDK
   paragraph in [BUILD.md](docs/BUILD.md).
3. **The Makefile.** Before any recipe, a parse-time check applies the same
   `xcrun` test to any nonempty `SDKROOT`, inherited or given on the make
   command line, and stops with `$(error …)` on failure. The Makefile never
   defines `SDKROOT` itself, so its origin does not distinguish anything the
   guard needs. Apple's make here is 3.81; the check uses only `shell` and
   `error`. A valid nonempty value costs two `xcrun` calls per parse; release
   parses the Makefile three times through its recursive targets.

   The developer directory's real make, invoked directly or through
   `xcrun make`, bypasses the shim and can otherwise pass a bad inherited
   value to a recipe's `/usr/bin/python3`. The check covers that path too.
   The [build guide](docs/BUILD.md) and the Makefile header state the limit:
   `/usr/bin/make` with a bad inherited `SDKROOT` makes the request before
   the Makefile is read. Any other make reaches the check. They direct
   callers to put a request on the command line (`make build SDKROOT=…`)
   or use `./build.sh`.
4. **A contained route for probes.** Turn the record's
   [probe.py](records/shim-install-request/probe.py) pattern into a helper
   under `tests/lib/`:
   - generate the profile from helper-owned rules with a fixed blanket
     `(deny mach-lookup)` and limited writes. Callers supply structured write
     paths and an optional exec allow-list, never SBPL text. An exec
     allow-list adds `(deny process-exec)` and literal allowances for those
     paths; no caller input can express a Mach rule;
   - always allow the helper's check executables for the selected mode.
     `/usr/bin/dscl` must be able to execute inside the final profile, so an
     exec restriction cannot substitute for its Mach-dependent check;
   - refuse to start unless `/usr/bin/dscl . -read /Users/root UniqueID`
     exits 0 outside with `UniqueID: 0` in stdout, completes with a nonzero
     status inside, and a command permitted by the final profile succeeds
     inside it. Use `/usr/bin/true` for the plain profile and the allowed
     tool for an exec-restricted profile;
   - report any request through the detector.

   `contained_xcrun` and `fake_developer_dir` keep an exec allow-list of
   `/usr/bin/xcrun`; the helper additionally permits `/usr/bin/dscl` for its
   check. Their successful run check uses `/usr/bin/xcrun --version` with a
   known-good developer environment, before introducing the probe's invalid
   values. The checks and requested command use the same final profile.
   `/usr/bin/true` remains outside this allow-list: retain its refusal as an
   exec-restriction assertion after establishing that commands can run, and
   retain the actual invalid-developer-directory diagnostic from `xcrun`.
   No developer-tool shim is added to these callers' exec allowances.

   A successful permitted command establishes that the profile applies and
   commands can run. A denied exec cannot establish that: both exec denial
   and failure to apply the profile can exit 71 with `Operation not permitted`.
   Without the success check, `dscl` and every probe could fail before
   execution, yielding no detected requests from shims that never ran. A
   failed or missing containment prerequisite stops the helper before it
   starts the requested command.

   Factor the gate's decision into a pure function over collected check
   results. Rejected unit controls feed it constructed results for outside
   failure, outside success without `UniqueID: 0`, inside `dscl` success,
   failed permitted execution, and missing or incomplete results. Also
   check that a refused decision prevents command dispatch. The public
   helper collects its own results using its fixed checks; these controls
   introduce no profile override or caller-supplied check results. Separately,
   run the helper under an outer `sandbox-exec` to exercise a real nested
   `sandbox_apply` failure and establish that the requested command never
   starts. Keep the constructed decision evidence distinct from that live
   failure.

   Mach-denial log evidence is not a prerequisite for the helper. Where a
   control already reads the unified log, record denial evidence matched by
   PID when available. The fixed blanket deny guards the installation
   service independently of why `dscl` failed; the opt-in positive control
   requires evidence that the installation-service lookup itself was denied.

   Add a line to
   [tests/AGENTS.md](tests/AGENTS.md#sandboxed-automation-harnesses) routing
   any by-hand probe of `SDKROOT` or `DEVELOPER_DIR` through it. A warning
   alone has already failed once; this gives the warning a tool to point to.

## Verification

| Check | Establishes |
|---|---|
| Containment helper (default battery, in `preflight/build_provenance_controls`; no app or shim needed for these checks) | Exercise both plain and exec-restricted profiles: outside `dscl` exits 0 with `UniqueID: 0`, inside `dscl` executes and fails, and the profile's permitted success command exits 0. The xcrun-restricted profile also refuses `/usr/bin/true` after the successful tool run. Structured path inputs preserve the fixed Mach deny and the requested exec restriction. Constructed inputs to the gate decision cover each refusal, including inside `dscl` success, without a profile override; a refused decision prevents dispatch. A separate outer-sandbox control produces a real nested `sandbox_apply` failure and no requested-command execution. The helper needs no unified-log access to pass its gate. |
| Detector, positive control (opt-in, beside `control_sdk_unavailable`) | A shim run under the helper with `SDKROOT` naming a missing path is reported as a blocked request, and the log shows the denied installation-service lookup attributed by PID. The neighbour with an empty `SDKROOT` is not reported. This is the only check that deliberately makes the shim attempt a request, so it stays out of the default battery. |
| Entry points (default battery, with the resolver's checks) | `tests/run.sh --help`, `checkout_lock.sh -- /usr/bin/true` and `build.sh`, with `SDKROOT` naming a missing path and then an unknown name, refuse with status 2 and the new guard's admission diagnostic naming `SDKROOT` and its value. Run under the helper's containment and assert no request is reported. In isolated fixtures, assert no checkout-lock or build-session writes; the dispatcher does not print help, and the build does not reach lock verification, generator checks or SDK selection. An empty `SDKROOT`, `macosx` and the selected SDK path pass admission, with harmless continuations establishing that each entry point reaches its next boundary. |
| Makefile, command-line request | `make help SDKROOT=<missing path>` and a release target refuse before any recipe, under the same containment, with no request reported. `make build SDKROOT=<selected path>` reaches `build.sh`. |
| Makefile, inherited request | The developer directory's real make, with an inherited `SDKROOT` naming a missing path, refuses before any recipe under the same containment, with no request reported. Exercise a release target whose first recipe would otherwise start `/usr/bin/python3`. |
| Existing assertions | The four use the detector. Each still passes, since none sits where a shim can see a bad value. |
| Build path | `control_sdk_requests`' invalid case refuses at admission with the new message, before the `sdk` step and before any session write. `build_toolchain_switch` still passes, and the provenance record still names the caller's request. |

The default entry-point checks establish early refusal. Removing the guard
from `checkout_lock.sh -- /usr/bin/true` lets it exit 0 without starting a
shim. Removing it from `build.sh` lets the build take the lock, remove
`SDKROOT`, run generator checks and refuse at `sdk` with status 2 and the
requested value in its message. Status 2 and the value alone therefore do
not establish admission refusal. `tests/run.sh --help` reaches no test case
or shim, and these checks do not run cases under the Mach-lookup denial.
The separate opt-in positive control establishes detection of a blocked
installation request.

Then run `source_drift`, `preflight/build_provenance_controls`, the
`preflight` build control groups and the default battery. Read the log
afterwards for lookups of the installation service: only the positive
control may show one.

## Where it stops

- A shell that starts `/usr/bin/make` (or any shim) with a bad inherited
  `SDKROOT` makes the request before repository code runs. Only documentation
  reaches it. Any other make reaches the Makefile's check before its recipes.
- `DEVELOPER_DIR` gets no installation guard: the probe found no form that
  makes the request. Whether to refuse a stand-in developer directory that
  can run tools is a separate toolchain question. A build records what ran
  in its provenance.
- A case that sets its own bad `SDKROOT` and then runs a shim is not caught at
  the entry point. The current tree has none, and the test-change rules plus
  the contained route cover new ones.
- The behavior is Apple's and was observed on one machine
  (macOS 26.7.1, Xcode 27.1). Rerun the probe after an Xcode or Command Line
  Tools update.
