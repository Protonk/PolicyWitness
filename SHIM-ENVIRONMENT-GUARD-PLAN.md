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
    [build_refusals.py](tests/suites/preflight/opt_in/build_refusals.py);
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
   `xcrun` test to an `SDKROOT` given on the make command line and stops with
   `$(error …)`. An `SDKROOT` in make's environment has already passed make's
   own shim, or has already made the request before the Makefile was read.
   The [build guide](docs/BUILD.md) and the Makefile header say so, and say
   that a request belongs on the command line (`make build SDKROOT=…`) or with
   `./build.sh`. Apple's make here is 3.81; the check uses only `origin`,
   `shell` and `error`.
4. **A contained route for probes.** Turn the record's
   [probe.py](records/shim-install-request/probe.py) pattern into a helper
   under `tests/lib/`:
   - run a command under a profile that denies Mach lookups and limits writes;
   - refuse to start unless the `dscl` containment check passes;
   - report any request through the detector.

   `contained_xcrun` and `fake_developer_dir` use it. Add a line to
   [tests/AGENTS.md](tests/AGENTS.md#sandboxed-automation-harnesses) routing
   any by-hand probe of `SDKROOT` or `DEVELOPER_DIR` through it. A warning
   alone has already failed once; this gives the warning a tool to point to.

## Verification

| Check | Establishes |
|---|---|
| Detector, positive control (opt-in, beside `control_sdk_unavailable`) | A shim run under the helper with `SDKROOT` naming a missing path is reported as a blocked request, and the log shows the denied lookup. The neighbour with an empty `SDKROOT` is not reported. This is the only check that deliberately makes the shim attempt a request, so it stays out of the default battery. |
| Entry points (default battery, with the resolver's checks) | `tests/run.sh`, `checkout_lock.sh -- /usr/bin/true` and `build.sh`, with `SDKROOT` naming a missing path and then an unknown name, refuse with status 2, naming the value. They run under the helper's profile, which allows shims to execute: with the guard removed, a shim would attempt the request, and the detector would report it. An empty `SDKROOT`, `macosx` and the selected SDK path pass. |
| Makefile | `make help SDKROOT=<missing path>` and a release target refuse before any recipe, under the same containment, with no request reported. `make build SDKROOT=<selected path>` reaches `build.sh`. |
| Existing assertions | The four use the detector. Each still passes, since none sits where a shim can see a bad value. |
| Build path | `control_sdk_requests`' invalid case refuses at admission with the new message, before the `sdk` step and before any session write. `build_toolchain_switch` still passes, and the provenance record still names the caller's request. |

Then run `source_drift`, `preflight/build_provenance_controls`, the
`preflight` build control groups and the default battery. Read the log
afterwards for lookups of the installation service: only the positive
control may show one.

## Where it stops

- A shell that starts `/usr/bin/make` (or any shim) with a bad `SDKROOT`
  makes the request before repository code runs. Only documentation reaches
  it.
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
