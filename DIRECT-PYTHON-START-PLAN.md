# Start the build's Python directly, not through the /usr/bin shim

The intended result: every Python process whose environment reaches a build,
a compiler or a test case starts as the developer directory's own `python3`,
so its environment is its caller's. The machinery that records the caller's
`SDKROOT`, `CPATH`, `LIBRARY_PATH`, `MANPATH` and `LC_CTYPE` in shell,
carries them through the lock owner and restores them is deleted. A build's
request becomes the environment `build.sh` starts with. Because Python
cannot tell how it was started, a recorded witness of those variables
replaces the transport: a process that finds them changed refuses and never
repairs them. The build controls' wrappers start the same way, so wrapped
tools see what a real build sees.

Follow [CONTRIBUTING.md](CONTRIBUTING.md#planning-a-change),
[BUILD.md](docs/BUILD.md) and [tests/AGENTS.md](tests/AGENTS.md) when
executing it. This plan precedes
[SHIM-ENVIRONMENT-GUARD-PLAN.md](SHIM-ENVIRONMENT-GUARD-PLAN.md). That plan's
premises about `child_env` and the bound requests change here, so it is
revised after this one lands.

## What the shim does

Observed on 2026-10-20 on macOS 26.7.1 with Xcode 27.1 selected and the
Command Line Tools (Swift 6.3.3) installed. Environments were compared by
running `/usr/bin/env -0` as a child under `env -i` with chosen values:

- `/usr/bin/python3` runs `$(xcode-select -p)/usr/bin/python3`. Started
  either way, `sys.executable` names that binary and the version is 3.9.6,
  under Xcode and the Command Line Tools alike. The interpreter does not
  change; only its environment does.
- The shim gives Python `SDKROOT` (the developer directory's default SDK)
  and `CPATH=/usr/local/include`, appends `:/usr/local/lib` to
  `LIBRARY_PATH` and replaces `MANPATH`. Everything Python starts inherits
  them. The `git` shim does the same for `git`'s children; `/usr/bin/make`
  adds nothing.
- The developer directory's `python3` started directly with
  `PYTHONCOERCECLOCALE=0` passes its caller's environment to its children
  unchanged. The one addition is `__CF_USER_TEXT_ENCODING` when the caller
  lacks it, and login sessions already carry it. Without
  `PYTHONCOERCECLOCALE=0`, a caller with no locale gets `LC_CTYPE=C.UTF-8`.
  UTF-8 mode and the stdio encodings are the same either way.
- `/usr/bin/xcode-select -p` honors `DEVELOPER_DIR`, maps `…/Xcode.app` to
  `…/Xcode.app/Contents/Developer`, and returns a stand-in or nonexistent
  directory unchecked with status 0. That was observed under a sandbox
  profile denying Mach lookups and every exec but `xcode-select`. Xcode and
  the Command Line Tools both carry `usr/bin/python3`.

## What the repository does about it now

- The lock owner is Python started through the shim. So
  [checkout_lock.sh](tests/lib/checkout_lock.sh) records the five variables
  with shell builtins and removes them. In
  [checkout_lock.py](tests/lib/checkout_lock.py), `Requests` binds them to the
  acquisition, hands them to nested admissions, restores them in `child_env`
  and prints them for `--verify --build-requests`. A build under an owner
  without them refuses as `build_requests_missing`.
  [build.sh](build.sh) decodes and restores them (`restore_request` and the
  `LOCK_REQUESTS` loop) and keeps `SDKROOT` apart as the SDK request.
- [build_provenance.py](tests/lib/build_provenance.py) runs through the shim
  too. `invocation_environment` therefore rebuilds the environment Cargo
  inherits from the session's requests, and `ALLOWED_ENV` records only
  variables the shim leaves alone.
- The build controls' wrappers
  ([tools.py](tests/fixtures/build_refusals/tools.py),
  [forward.py](tests/fixtures/build_refusals/forward.py) and
  [build_guards/tools.py](tests/fixtures/build_guards/tools.py)) begin with
  `#!/usr/bin/python3`. Every `cargo`, `meson`, `ninja` and compiler they
  wrap therefore runs with the shim's `CPATH`, `LIBRARY_PATH` and `MANPATH`,
  which a real build does not have. The forwarders compare only variables
  the shim leaves alone (`ORACLE_ENV` and the comment above it in
  [build_refusals.py](tests/suites/preflight/opt_in/build_refusals.py)).

## Decisions

- **Only the ancestry changes.** The ancestry is the Python whose
  environment reaches a build, a compiler or a test case: the lock owner
  started by `checkout_lock.sh`, `build.sh`'s Python steps, the dispatcher
  `tests/run.sh` starts, and the three wrappers. Leaves are Python that does
  its work and exits without starting a build or a compiler. They keep
  `/usr/bin/python3`: suite scripts' heredocs, generator checks, the Makefile
  release steps and the Rust test helpers. About 250 of the repository's 257
  `/usr/bin/python3` references are leaves. The Rust ones are all
  `#[cfg(test)]`; the shipped controller never starts Python. Converting
  leaves would add no correctness, and `git` keeps the guard plan necessary
  either way.
- **A caller's `SDKROOT` is still honored.** It is how a build uses the
  Command Line Tools here, since they cannot link their newest SDK
  ([BUILD-PROVENANCE-ACCEPTANCE.md](records/BUILD-PROVENANCE-ACCEPTANCE.md)).
  With a direct owner it travels in the environment, and nothing carries it
  separately. Refusing it is a separate decision that belongs with
  requiring Xcode.
- **A build's request is the environment `build.sh` starts with.** A nested
  build takes the outermost caller's requests today only because the Python
  in between came through the shim. A caller that wants different values for
  a nested build launches it through the front end.
- **The provenance record keeps its shape and meaning.**
  `configuration.requests` is filled from the environment `build.sh` starts
  with, so the record's readers do not change.
- **The wrappers start through `env -S`.** Each form was tried as a script
  on `PATH`, reporting the environment it received:

  | First line | Wrapped tool sees the shim's values | Interpreter path containing a space |
  |---|---|---|
  | `#!/usr/bin/python3` (now) | yes | works |
  | the interpreter's absolute path, written when the wrapper is copied | no | does not start |
  | `#!/usr/bin/env -S ${PW_PYTHON} -B` | no | works |

  The last keeps the three files as committed. When `PW_PYTHON` is missing,
  it fails with a misleading `env: illegal option -- B`.

## Approach

1. **One shell resolver.** Write a sourced helper under `tests/lib/` that
   `checkout_lock.sh`, `build.sh` and `tests/run.sh` all use. It runs
   `/usr/bin/xcode-select -p` and refuses with status 2 when
   `<directory>/usr/bin/python3` is not executable. The refusal names
   `DEVELOPER_DIR` when it is set, or xcode-select's selection, and the
   directory. Otherwise it exports `PW_PYTHON` and `PYTHONCOERCECLOCALE=0`.
   It starts no shim. Each script resolves for itself rather than trusting
   an inherited `PW_PYTHON`.
2. **A witness in place of the requests.** `checkout_lock.sh` exports the
   five variables' state as it found them: set or unset, and the exact
   value. The executor chooses the encoding. It must distinguish unset from
   empty and keep every byte a variable can hold. Two places compare the
   witness with their own environment and refuse, naming the variable, when
   it is absent or differs:
   - `checkout_lock.py` when it runs as the command-line owner. Python
     callers of `owned()`, such as the dispatcher and the release scripts,
     are unaffected.
   - `build_provenance.py session-start`. For `SDKROOT` it compares the
     request `build.sh` passes it, since `build.sh` has already removed
     `SDKROOT` from its environment by then.

   Nothing restores a value. A nested front end records the witness again
   from its own environment.
3. **Delete the transport.** Remove:
   - `Requests` and its options, the admission reply's `requests` member,
     `--build-requests`, `NO_REQUESTS` and `child_env`'s restoration.
     `child_env` keeps dropping stale claims.
   - `build.sh`'s `restore_request` and `LOCK_REQUESTS` loop.
     `build.sh` instead reads `SDKROOT`'s state and value from its own
     environment before it unsets it, and passes them to `session-start`.
     SDK selection is unchanged.
   - `invocation_environment`'s rebuilding, because Cargo inherits the
     helper's own environment. Also remove `ALLOWED_ENV`'s comment about
     the shim.

   Every `build.sh` Python step uses the resolved interpreter. Decide
   whether the admission message's `v` changes. One checkout runs one copy
   of `checkout_lock.py`, so the question is only whether an owner and a
   client can straddle the edit.
4. **Start the dispatcher directly.** `tests/run.sh` sources the resolver
   and execs `PW_PYTHON`. It records no witness: cases that build do so
   through the front end, which records one.
5. **Wrappers.** Give the three wrappers the `env -S` first line. `Checkout`
   in `build_refusals.py` and the setup in `build_guards.py` already build
   every build environment explicitly and strip the five variables. They
   add `PW_PYTHON=sys.executable`, which names the direct interpreter even
   in a control that itself came through the shim. Extend the forwarders'
   comparison to `SDKROOT`, `CPATH`, `LIBRARY_PATH` and `MANPATH`, and
   delete the comment that explains their absence.
6. **Drift check.** Add a `source_drift` check. It refuses
   `/usr/bin/python3`, `env python3` and a bare `python3` command in
   `checkout_lock.sh`, `build.sh` and `tests/run.sh`, and requires the
   wrappers' first line. Register it as [tests/AGENTS.md](tests/AGENTS.md)
   requires.
7. **Documentation.** Describe the environment rule and the witness instead
   of the transport in:
   - [BUILD.md](docs/BUILD.md): the lock and requests summary, the SDK
     paragraph, the locking section and its caveat about callers started
     through the shim;
   - [tests/README.md](tests/README.md);
   - the `checkout_lock.py` docstring and usage, and the
     `checkout_lock.sh` header;
   - `build.sh`'s comments on the lock and the SDK.

   Replace `build_requests_missing` in [build.json](docs/build.json) with
   the witness refusals and regenerate with `docs/generate_build.py`.
   [architecture.json](docs/architecture.json) did not describe the request
   payload when this plan was written; confirm that when editing.

## Verification

| Check | Establishes |
|---|---|
| The started Python's children against the caller | A check runs the resolver under `env -i` with chosen values: `CPATH` unset, `LIBRARY_PATH` with a space and a trailing newline, `MANPATH` set, no locale. The environment a child of the started Python reports equals the caller's byte for byte. The same through `/usr/bin/python3` differs, so the comparison can fail. |
| Stand-in developer directory | `build.sh`, `checkout_lock.sh` and `tests/run.sh` with `DEVELOPER_DIR` naming an empty directory refuse, naming it. They run under a profile that denies Mach lookups, so an escaped shim could not reach the installer, and the output never contains "requesting installation". |
| Witness refusals | Each refuses before any write and leaves the session untouched: `/usr/bin/python3 -B tests/lib/checkout_lock.py -- /bin/bash build.sh` with no witness; the same with a witness recording `CPATH` unset, which names `CPATH`; and a build nested under a Python-only owner, at `session-start`. These replace `control_build_requests_missing`. |
| SDK requests | Every `control_sdk_requests` case records the same requests and sources as now. The nested case shows the nested build using the environment it was started with. The invalid request keeps its contained `xcrun` and its installation assertion. |
| Forwarders | Compilations receive exactly the build's `CPATH`, `LIBRARY_PATH` and `MANPATH`, unset where the caller had them unset, and the selected `SDKROOT`. A forwarder deliberately started through `/usr/bin/python3` shows the difference, so the comparison can fail. |
| Dispatcher | The default battery through the edited `tests/run.sh` passes from a shell where the four variables are unset. |

The dispatcher result was established before the change. Run
`20261020T091432Z_bec337d3` started `tests/lib/test_cli.py` directly with
`PYTHONCOERCECLOCALE=0`, after sourcing `testlib.sh` as `tests/run.sh` does.
It passed 197 of 197, with the same cases and outcomes as the 0.3.2 release
battery, and the dispatcher's environment read with `ps -wwE` held none of
the four variables. That run is in
`tests/out/runs/direct-python-dispatcher-20261020` and is not retained.

Run `source_drift`; `preflight/build_guard_controls`,
`preflight/build_refusal_controls`,
`preflight/build_toolchain_switch_controls` and
`preflight/signed_artifact_controls`;
`tests/lib/checkout_lock.sh -- cargo test --manifest-path controller/Cargo.toml`;
and the default battery against a fresh signed build. Nothing may reproduce
the installation request.

## Where it stops

- Leaves keep `/usr/bin/python3`. Release acceptance starts `tests/run.sh`
  from Python ([release_accept.py](tests/lib/release_accept.py)); if that
  Python came through the shim, the battery inherits the shim's values,
  which it does not depend on.
- A bogus `SDKROOT` still reaches `git` in the dispatcher and in cases, and
  a stand-in `DEVELOPER_DIR` that contains `usr/bin/python3` passes the
  resolver. Both remain the guard plan's. The resolver gives that plan's
  `DEVELOPER_DIR` check a place at the converted entry points.
- Which toolchains and SDKs a build accepts does not change.
- [NATIVE-BUILD-PLAN.md](NATIVE-BUILD-PLAN.md) also edits `build.sh`'s
  admission and `build_provenance.py`. The two are independent, and
  whichever lands second adapts to the other.
