# Pinned Python 3.14 for the build and test helpers

## Problem

Every Python helper in this repository runs on Xcode's bundled 3.9.6, chosen
in three places that do not know about each other: `tests/lib/python_start.sh`
resolves the developer directory's `usr/bin/python3` for `build.sh`,
`tests/run.sh`, `tests/lib/checkout_lock.sh` and `tests/lib/python.sh`;
`tests/lib/case.sh` (`test_check_python`), seven heredocs in
`tests/lib/testlib.sh` and 59 shell scripts under `tests/` start leaf checkers
through the `/usr/bin/python3` shim; and checkers start their own children
with `sys.executable`. The shim adds `SDKROOT`, `CPATH`, `LIBRARY_PATH` and
`MANPATH` to every leaf checker and its children, which the build's witness
contract exists to keep out of the build. Xcode's Python is also the reason
the repository cannot use `hashlib.file_digest`, cannot move the vendored
markdown-it-py past 3.0.0, and keeps a comment-refusal workaround in
`docs/markdown_reader.py`. The measurements this plan rests on are in
[records/PYTHON-314-TEST-MAINTENANCE.md](records/PYTHON-314-TEST-MAINTENANCE.md).

## Intended result

One resolver selects one interpreter for every Python start the repository
owns: Homebrew's `python@3.14` at its version-named keg path, checked before
any helper runs and refused by name when absent or of another minor version.
Helpers import nothing outside the standard library and the tree. The
interpreter is recorded in the build's provenance, in each test run's
configuration and in every case report, and the dispatcher checks each
report against the run. Leaf checkers start through the same resolver, so no
process in a battery inherits the shim's environment unless a control starts
the shim on purpose. The controls that establish environment preservation
cover every kind of start, and the refusal a coerced locale produces names
the cause.

Python 3.14 becomes a stated prerequisite beside Meson and Ninja. The
repository installs nothing during a build or a test execution; the operator
installs the formula once.

## Approach

### 1. The resolver

`tests/lib/python_start.sh` keeps its role: sourced by each entry point, never
trusting an inherited `PW_PYTHON`, exporting `PW_PYTHON` and
`PYTHONCOERCECLOCALE=0` after `sdk_guard.sh`. It changes what it resolves and
how it checks.

The pin lives in this file only: the required minor version `3.14` and the
path `/opt/homebrew/opt/python@3.14/bin/python3.14`. The `opt` link is
Homebrew's stable name for a formula; `/opt/homebrew/bin/python3` moves to
the next minor when one ships, and `python3.14` on `PATH` can be a pyenv,
asdf or uv shim. Nothing in the environment changes the choice; the build
controls that export `PW_PYTHON=sys.executable` do so for fixture wrappers
whose shebang reads it, and that stays as it is.

Two functions do the checking, each refusing with status 2 before any helper
starts:

- `pw_python_start` runs at every start. Any `PYTHON*` variable in the
  environment other than `PYTHONCOERCECLOCALE` and `PYTHONDONTWRITEBYTECODE`
  is the refusal `python_environment_set`, naming the variable; `PYTHONPATH`
  and `PYTHONHOME` reach the interpreter through `-B -S`, and the resolver
  refuses rather than repairs. The path is an executable regular file or a
  link to one, or the refusal is `direct_python_unavailable` with the path
  and `brew install python@3.14` in the message. Its real path is under
  `/opt/homebrew/Cellar/python@3.14/<keg>/`, where `<keg>` is `X.Y.Z` or
  `X.Y.Z_N` with `_N` a Homebrew revision, and `X.Y` is 3.14, or the
  refusal is `python_version_mismatch`, naming what was found and what is
  required. It exports `PW_PYTHON`, `PW_PYTHON_VERSION` as the upstream
  `X.Y.Z` without the revision, `PW_PYTHON_REALPATH` in full, and
  `PYTHONCOERCECLOCALE=0`. It costs 3 ms, the same as today's
  `xcode-select -p`. It takes an optional explicit path and an optional
  Cellar root so that controls can exercise each refusal against a stand-in
  tree; entry points call it with neither.
- `pw_python_probe` runs only at the five entry points (`build.sh`,
  `tests/run.sh`, `checkout_lock.sh`, `python.sh`,
  `tests/accept-release.sh`), after `pw_python_start`. It starts
  `PW_PYTHON` once as
  `"$PW_PYTHON" -I -S -B -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])'`;
  `-I` alone still imports `site`, so `-S` is part of the probe. A probe
  that fails to launch, exits nonzero or prints anything but a version is
  `direct_python_unavailable` with the status and the head of its stderr; a
  version other than `PW_PYTHON_VERSION` is `python_version_mismatch`. It
  costs the interpreter's startup, 34 ms against 29 ms for an empty
  `-c pass`, so a battery pays it a handful of times. It takes an optional
  explicit executable so that controls can exercise both outcomes with a
  stand-in; entry points call it without one.

Helper scripts start with `-B -S`; `-c` starts, which are the `testlib.sh`
heredocs, with `-B -S -P`. `-S` keeps site-packages, `.pth` files and
`sitecustomize` off `sys.path`, so the interpreter's site-packages, which
every `brew install` and `pip install` can change without a witness, are
not an input. `-P` keeps the working directory off a `-c` start's path; a
script start keeps its own directory, which is in the tree. With the
`PYTHON*` refusal, every `sys.path` entry of a helper is under the
interpreter's prefix or under the checkout: the standard library, the
script's directory, and the tree's own insertions. `-E` and `-I` are
excluded for helpers because they ignore `PYTHONCOERCECLOCALE`; from a C
locale the interpreter would then set `LC_CTYPE=C.UTF-8` for itself and its
children, and the witness would refuse the build with a remedy that names
the front end instead of the interpreter. The probe is the one isolated
start, and it runs nothing but the version print. The wrapper shebang
becomes `#!/usr/bin/env -S ${PW_PYTHON} -B -S`.

### 2. Every start the resolver owns

- The five entry points call `pw_python_start` then `pw_python_probe` where
  they source the resolver today. The Makefile recipes reach `python.sh` and
  need nothing of their own.
- `tests/lib/testlib.sh` sources `python_start.sh` right after
  `sdk_guard.sh` and calls `pw_python_start`, so `case.sh`, direct suite
  scripts and release acceptance resolve the interpreter themselves; a suite
  script started outside the dispatcher has no `PW_PYTHON` to inherit. Its
  seven `/usr/bin/python3` heredocs (the assertion guard, `now_ms` and the
  others) become `"${PW_PYTHON}" -B -S -P`, and `test_check_python` in
  `case.sh:53` becomes `"${PW_PYTHON}" -B -S`.
- The sweep. 144 lines in 59 shell scripts under `tests/` mention
  `/usr/bin/python3` (46 suite scripts, 9 fixtures, 4 in `tests/lib`,
  comments included), and three `runner_unit` scripts call a bare `python3`.
  Every invocation becomes `"${PW_PYTHON}" -B -S`. Children that a checker
  starts with `sys.executable` pass `-B -S` as well. Review the fixture
  scripts under `tests/fixtures/shell_case`, `dispatcher`, `worker_lifecycle`
  and `worker_harness` one by one: a shim start stays only where a control
  uses the shim as a deliberate negative control, and the drift check names
  those files. Do the sweep as its own commit; it touches files other agents
  edit, and the drift check shows a partial sweep as a failure.
- Files with `#!/usr/bin/env python3` or `#!/usr/bin/python3` shebangs are
  never executed through them (every start names an interpreter), so the
  shebangs are inert. Leave them or normalize them; the drift check does not
  depend on them.

### 3. Records

- Build provenance. `observe_toolchain` in `tests/lib/build_provenance.py`
  adds a `python` observation beside `cargo`, `meson` and `ninja`: the pinned
  path, its full real path including any Homebrew revision, the probed
  version and the probe's status.
  `record_shape()` requires the member under `SCHEMA_VERSION` 3. Archived
  releases keep their version-2 records: `read_zip_record` refuses a record of
  any other version (the `version-1.zip` control in
  `check_build_provenance.py` establishes it), and no routine operation
  re-reads an archived release, since `release_archive`, `release_publish`
  and `release_rotate` each verify the release they are producing. Land the
  bump with `tests/out/.release-rotation/` empty; an interrupted rotation of
  a version-2 archive could not resume afterwards. The fixture records in
  `tests/fixtures/dispatcher/fixture_bundle.py` and the `RecordTests` gain
  the member. Document it in
  [docs/SIGNING.md](docs/SIGNING.md#the-provenance-record)'s `toolchain`
  bullet with the version.
- Test runs. `resolve_config` in `tests/lib/test_cli.py` adds
  `python: {path, realpath, version}` to the configuration that `plan.json`
  and `run.json` carry. The readers compare `plan.configuration` with
  `run.configuration` (`tests/lib/retention.py:178`,
  `tests/suites/dispatcher/check_selection.py:138`); an added key passes
  through both. Document it in the output contract in `tests/README.md`.
- Case reports. The report writer in `tests/lib/testlib.sh` adds
  `interpreter: {path, realpath, version}` from the resolver's exports to
  every `report.json`, and `reconcile` in `tests/lib/suite_run.py` compares
  each report's `interpreter.realpath` with the run configuration's,
  recording an `interpreter_mismatch` harness error otherwise. Bump the
  report's `schema_version` if the output contract treats an added field as
  a version change; document the field either way.

### 4. Controls

- Preservation and identity at every kind of start.
  `LockTests.test_helper_wrapper_children_inherit_the_callers_environment`
  in `tests/suites/preflight/check_build_provenance.py` establishes the
  contract for `python.sh` from a forced C locale, and its failure diff names
  `LC_CTYPE`; it is the model. Add, beside it, the same assertion for each
  entry point plus the import boundary: `site` is not in `sys.modules`, and
  the real path of every `sys.path` entry is under the interpreter's prefix
  or under the checkout, with a message that names the entries found and
  says the resolver starts helpers with `-S` and refuses `PYTHON*` so
  nothing outside the interpreter and the tree is an input. A variant sets
  `PYTHONPATH` and expects `python_environment_set`. Add the dispatcher-driven
  and direct-suite versions as one `shell_helpers` case: a one-case probe
  suite installed with `tests/fixtures/dispatcher/repository.py`, run through
  `tests/run.sh` and as a direct suite script, whose leaf records its own
  and a child's values of the five witnessed names, `sys.version_info[:2]`,
  the real path of `sys.executable`, and the import boundary. Assert the
  five names equal the caller's (all unset under `env -i`), the version is
  3.14, the real path is under the keg, and the boundary holds. These
  controls observe
  consequences, so they catch every cause of the same signature, which a
  check for a flag would not.
- The coercion signature. In `verify_environment`
  (`tests/lib/checkout_lock.py`), when the differing name is `LC_CTYPE`, the
  witness is unset and the value is `C.UTF-8` or `UTF-8`, the refusal says
  that the helper interpreter coerced the locale and `PYTHONCOERCECLOCALE=0`
  was not honored. The opt-in `control_environment_witness_changed` in
  `tests/suites/preflight/opt_in/build_refusals.py` gains a C-locale variant
  that asserts that text.
- Resolver refusals. `ShimContainmentTests` and
  `test_entrypoints_refuse_a_stand_in_developer_directory_without_a_shim`
  make Python unavailable through a stand-in developer directory, which no
  longer selects Python. They use instead an exec-denying `sandbox-exec`
  profile (the existing `(deny process-exec)` form) that leaves the pinned
  path out, so each entry point refuses with `direct_python_unavailable`
  before any Python runs. The two functions get separate controls, since
  `pw_python_start` never runs the interpreter: `pw_python_start` with a
  stand-in path and Cellar root refuses a missing or unexecutable file, a
  `<keg>` of another minor, and a `<keg>` that is not a version, and
  accepts a revision-suffixed keg such as `3.14.8_1` with
  `PW_PYTHON_VERSION` reading `3.14.8`; `pw_python_probe` with a stand-in
  executable that prints another version refuses `python_version_mismatch`,
  and with one that exits nonzero or prints no version refuses
  `direct_python_unavailable`.
  `test_build_refuses_a_stand_in_developer_directory_before_any_python` in
  `tests/suites/source_drift/contract.py` and the `direct_python_unavailable`
  controls in `build_refusals.py` change the same way; `docs/build.json`
  cites them by symbol, so the citations follow.
- Drift. `tests/suites/source_drift/direct_python.py` widens its lexical
  scope from the six entry points and three wrappers to `case.sh`,
  `testlib.sh` and every `*.sh` under `tests/`: no `/usr/bin/python3` or bare
  `python3` command token outside the allow-list of deliberate shim
  controls; each entry point calls `pw_python_start` and `pw_python_probe`
  without arguments; each wrapper shebang is `#!/usr/bin/env -S ${PW_PYTHON}
  -B -S`. Its rejected controls get the new cases.

### 5. Documentation and generated copies

- `README.md:87-89`: `brew install meson ninja python@3.14`, and a sentence
  that the helpers run on that formula's interpreter.
- `docs/BUILD.md`: the prerequisites; the direct-Python paragraph under "The
  checkout lock" (lines 463-470), which gains the import boundary (`-B -S`,
  `-P` for `-c` starts, the `PYTHON*` refusal); the paragraph at lines
  534-540 about leaf scripts and the resolver; and the refusal table
  (`direct_python_unavailable` text, the new `python_version_mismatch` and
  `python_environment_set` rows). These come from `docs/build.json`: edit
  the refusal entries (`direct_python_unavailable` at line 1797, its
  citations at 1811-1814) and `inv_python_start` (line 4247), which carries
  the boundary sentence with citations to the resolver line and to the
  import-boundary control, then regenerate with `docs/generate_build.py`
  and review the result.
- `tests/README.md`: lines 216-219 on the dispatcher's resolution, the shell
  case setup section, and the output contract's configuration and report
  keys.
- `tests/AGENTS.md:85`: the contained-probe example starts
  `tests/lib/python.sh -I tests/lib/shim_probe.py` instead of
  `/usr/bin/python3 -I -B`.
- `tests/lib/vendor/README.md` lines 4-5 and 26: the libraries are kept so
  that a build installs nothing and helpers import only from the tree;
  `tomli` stays because Cargo 1.94 and later read TOML 1.1 for configuration
  files and `tomllib` does not; the markdown-it-py pin is no longer forced by
  the interpreter.
- `build.sh` changes (its resolver comments and the refusals it names), so
  regenerate the worker identity with `docs/generate_worker_identity.py`;
  `generate_build.py --check` and `generate_architecture.py --check` say
  what else is stale.

### Where this stops

No vendored package changes, no `hashlib.file_digest`, no markdown-it-py
re-vendoring, no RECORD check for `tomli`, no Intel or CI support, and no
change to which interpreter the product's own tools use.

## Alternatives rejected

- A `PATH` lookup or an environment variable for the interpreter: `PATH` is
  caller controlled and unwitnessed, shims live on it, and an inherited
  interpreter is an unrecorded input into provenance.
- A version floor (3.14 or newer): interpreter minors change stdlib behavior
  the tree cannot see, so moving the pin is a reviewed commit, like an Xcode
  change. The patch version floats and is recorded.
- The probe at every start: it costs an interpreter startup per shell
  start, and the keg path already names the version at the cost of today's
  resolver.
- The resolver in `case.sh` only: direct suite scripts and release
  acceptance reach `testlib.sh` without `case.sh`.
- An optional provenance member: nothing would refuse a new build that
  omits it.
- Lexical checks for `-E`, `-I` or `-S`: a check for a flag misses every
  other cause of the same signature.
- Unsetting `PYTHONPATH` and `PYTHONHOME` in the resolver: the resolver
  never repairs the caller's environment; it refuses and names the
  variable, as the SDK guard does.
- Moving the real interpreter to test refusals: it needs root; the
  exec-denying profile and the stand-in argument do not.

## Verification

1. A fresh signed build under the new resolver (`make build IDENTITY=...`),
   whose provenance record carries `toolchain.python` with the keg real path
   and a 3.14 version.
2. The default battery against that build from an unsandboxed shell, with a
   fresh `PW_TEST_OUT_DIR`. `run.json` carries the `python` configuration and
   no `interpreter_mismatch` harness error. This establishes that each
   case's shell resolved the pin. That every Python invocation inside a case
   used it is established by the drift check over suite scripts; that
   checkers' children used it, by `sys.executable`; that a start behaves as
   the resolver promises, by the `shell_helpers` case, once, from a C
   locale.
3. `tests/run.sh --suite source_drift --suite shell_helpers --suite
   dispatcher --suite preflight`, plus the opt-in groups
   `preflight/opt_in/build_refusals.py` (environment witness, direct Python
   and stand-in controls), `build_guards.py` and
   `translated_build_refusals.py`, and `tests/lib/checkout_lock.sh -- cargo
   test --manifest-path controller/Cargo.toml`.
4. The resolver's own refusals: each entry point exits 2 with the named
   refusal under the exec-denying profile; the `pw_python_start` and
   `pw_python_probe` stand-in controls refuse and accept as specified; the
   coercion variant of the witness control prints the coercion text; the
   import-boundary control passes at every start and refuses under
   `PYTHONPATH`.
5. Timing. The battery's `duration_ms` on the same build and machine grows
   by at most 10 s or 1 % of the pre-change value, whichever is larger. An
   overrun blocks completion: the leaf check costs what today's resolver
   costs, so an overrun means the probe is running at leaf starts or
   something else regressed, and either needs finding first.

Passes that would mislead, and what rules each out:

- A checker run directly instead of through `tests/run.sh` never exercises
  the resolver; the battery is the evidence, not direct runs.
- A developer shell with `LANG=en_US.UTF-8` suppresses locale coercion;
  every preservation control builds its environment with `env -i`.
- A leaf that still runs 3.9 through a missed shim line passes every test it
  passed before, and its report still declares the pin, because the report
  records the resolver's answer, not each invocation; the drift check's
  whole-tree scope is what notices.
- `/opt/homebrew/bin/python3` resolves to the same binary today, so a `PATH`
  lookup would look equivalent; the real-path check under the keg is what
  distinguishes them, and it stays although it passes trivially here.
- A battery where every live case passes under the direct-started leaf says
  nothing about the shim's `CPATH` and `LIBRARY_PATH` on this machine, where
  neither directory exists.

## What would require reconsideration

- Homebrew's keg layout on a supported machine lacks the `opt/python@3.14`
  link, places the Cellar elsewhere, or names a keg directory in a form
  other than `X.Y.Z` or `X.Y.Z_N`; the pin's location or version parse
  fails and the resolver needs the new form, recorded as such.
- The timing budget is exceeded after the probe is confirmed absent from
  leaf starts; then the resolver's cost model is wrong, not the sweep.
- An interrupted release rotation exists when the schema bump lands; finish
  or abandon it first, following `docs/SIGNING.md`.
- A live case fails only under the direct-started leaf. None of the 21
  offline cases did; the live suites have not run under it.
- Python 3.15 changes locale coercion (PEP 686); the preservation controls
  trip on the first run after a pin move, which is the intended signal.

## Follow-on work, out of scope here

- Re-vendor markdown-it-py 4.2.0 and mdurl, delete
  `_refuse_unrecognized_comments` and its test, and update the pins.
- Replace the five SHA-256 read loops with `hashlib.file_digest`.
- Give `tomli` the RECORD-digest check the Markdown parser has, and track
  its version as Cargo tracks TOML 1.1.
- Rename or split `source_drift/direct_python.py` if its widened scope reads
  badly beside the resolver.
