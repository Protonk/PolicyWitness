# Which inputs make a developer-tool shim request an installation

Probed on 2026-10-20 on macOS 26.7.1 (25G241) with Xcode 27.1 (27A9275)
selected. The question was whether `/usr/bin/make` requests a Command Line
Tools installation for the inputs the `python3` and `git` shims are known to,
and which inputs those are.

## Finding

- `/usr/bin/make`, `python3`, `git`, `clang`, `cc`, `otool`, `lipo`,
  `strings`, `dsymutil`, `codesign_allocate` and 68 other names in
  `/usr/bin` are one file: a single inode with 78 links. They behave alike.
- Each of them asks for an installation when `SDKROOT` names a path that does
  not exist or a name no SDK has. The shim runs
  `xcodebuild -sdk <SDKROOT> -find <tool>`, that fails, and the shim looks up
  `com.apple.dt.CommandLineTools.installondemand`, the service that opens the
  installation dialog.
- An empty `SDKROOT`, and one naming an existing directory that is not an
  SDK, make no request; the shim complains or ignores it and runs the tool.
- No stand-in `DEVELOPER_DIR` made a request, in any form tried: missing,
  empty, holding only the tool, holding `usr/lib/libxcrun.dylib` and the tool,
  or shaped like `Xcode.app` with or without `xcodebuild`. Each refused with an
  error, except the Xcode-shaped one with `xcodebuild`, which ran the
  stand-in's tool.
- `/usr/bin/xcrun` (a separate binary) never made a request, including
  `xcrun -f clang` with the same failing `SDKROOT`, which runs the same
  failing `xcodebuild` lookup. `xcrun --sdk <path> --show-sdk-path` echoes any
  absolute path with status 0, existing or not; `--show-sdk-version` fails for
  a missing path and for a directory that is not an SDK.
  `/usr/bin/xcode-select -p` made no request.
- An `SDKROOT` given as a make argument (`make target SDKROOT=…`) is exported
  to recipes. A recipe's `$(MAKE)` is the developer directory's own `make`, not
  the shim, but a recipe's `/usr/bin/python3` made the request.
- `SDKROOT=… make …` makes the request before make reads any makefile, so
  nothing in a Makefile can prevent it.

## What the shim prints

The shim's messages, read from the system's shared library cache:

- request sent: `xcode-select: Failed to locate '<tool>', requesting
  installation of command line developer tools.`
- request impossible, as under the probe's sandbox: `xcode-select: Failed to
  locate '<tool>', and no install could be requested (perhaps no UI is
  present). Please install manually from 'developer.apple.com'.`
- no developer tools at all: `xcode-select: note: No developer tools were
  found, requesting install.`

A check that "requesting installation" never appears therefore detects only
a request that was actually sent. Under containment that denies Mach lookups,
an attempted request prints the second message, which that check does not
match.

## Method and containment

[probe.py](shim-install-request/probe.py) runs every shim, `xcrun` and
`xcode-select` call under `sandbox-exec` with Mach lookups denied, so no
request can reach the installer, and with writes limited to a fixture. It
first checks containment: `dscl . -read /Users/root UniqueID` must succeed
outside the profile and fail inside it (it fails with `eServerError`), and
nothing else runs otherwise. Every call starts from `PATH`, `HOME` and
`TMPDIR` plus the condition's variables. Stand-in developer directories are
links into the selected one. Afterwards the probe reads the unified log for
lookups of the installation service and attributes each to the call whose
time window contains it; the kernel's denial and launchd's
`denied lookup … Sandbox restriction` report appear for each one.

[summary.json](shim-install-request/summary.json) is the final run: 46 calls,
7 installation-service lookups (the two `SDKROOT` cases for each of the three
shims, and the recipe's `python3`), none unattributed, and no
`Install Command Line Developer Tools` process before or after. Full outputs
stayed in a scratch fixture and are not retained. To repeat it, with nothing
inherited so no shim sees the caller's variables:

```sh
env -i PATH=/usr/bin:/bin HOME="$HOME" /usr/bin/python3 -I -B \
  records/shim-install-request/probe.py /private/tmp/shim-probe-$(date -u +%Y%m%dT%H%M%SZ)
```

It needs an unsandboxed shell for `sandbox-exec` and `log show`.

## Limits

Every observation was contained. That a request goes out uncontained is
inferred from the lookup and from the shim's own messages, not observed; a
probe run by hand without containment has triggered it on this machine
before. Only the forms listed were tried. The behavior belongs to Apple's
shim and can change with an Xcode or Command Line Tools update; the probe can
be rerun to check.
