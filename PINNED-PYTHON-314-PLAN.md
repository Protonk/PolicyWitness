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
`docs/markdown_reader.py`. The investigation behind this plan is
[records/PYTHON-314-TEST-MAINTENANCE.md](records/PYTHON-314-TEST-MAINTENANCE.md);
read it for the measurements this plan relies on.

## Intended result

One resolver selects one interpreter for every Python start the repository
owns: Homebrew's `python@3.14` at its version-named keg path, verified before
any helper runs, refused by name when absent or of another minor version,
recorded in the build's provenance and in each test run's `run.json`. Leaf
checkers start through the same resolver, so no process in a battery
inherits the shim's environment unless a control starts the shim on purpose.
The existing controls that establish environment preservation extend to the
two starts they do not cover today, and the refusal a coerced locale produces
names the cause. The vendor README stops citing Python 3.9 as a reason.

Python 3.14 becomes a stated prerequisite beside Meson and Ninja. The
repository installs nothing during a build or a test execution; the operator
installs the formula once.

## Approach

### 1. The resolver

`tests/lib/python_start.sh` keeps its role (sourced by each entry point,
never trusting an inherited `PW_PYTHON`, exporting `PW_PYTHON` and
`PYTHONCOERCECLOCALE=0` after `sdk_guard.sh`) and changes what it resolves:

- The pin lives in this file only: the required minor version `3.14` and
  the path `/opt/homebrew/opt/python@3.14/bin/python3.14`. The `opt` link is
  Homebrew's stable name for a formula; `/opt/homebrew/bin/python3` moves to
  the next minor when one ships, and `python3.14` on `PATH` can be a pyenv,
  asdf or uv shim.
- Checks, in order, each refusing with status 2 before any helper starts:
  the path is an executable regular file or a link to one; its real path is
  under `/opt/homebrew/Cellar/python@3.14/<patch>/`, and that `<patch>`
  component names a 3.14 version. The first failure keeps the
  `direct_python_unavailable` refusal, with the path and `brew install
  python@3.14` in the message; the second is a new refusal,
  `python_version_mismatch`, naming what was found and what is required.
  Export the version read from the real path as `PW_PYTHON_VERSION`.
- The five entry points (`build.sh`, `tests/run.sh`, `checkout_lock.sh`,
  `python.sh`, `tests/accept-release.sh`) add one isolated probe,
  `"$PW_PYTHON" -I -B -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])'`,
  and refuse with `python_version_mismatch` when its answer differs from the
  real path's version. Leaf starts through `testlib.sh` do not probe. The
  probe costs the interpreter's startup, 34 ms here against 29 ms for an
  empty `-c pass`; the real-path check costs 3 ms, the same as today's
  `xcode-select -p`. So a battery pays the probe a handful of times and the
  leaf check once per shell start, at the cost the resolver already has.
- Only the probe runs isolated. The helpers keep `-B` and nothing else:
  `-E` or `-I` would ignore `PYTHONCOERCECLOCALE`, the interpreter would set
  `LC_CTYPE` from a C locale, and the witness would refuse the build with a
  misleading remedy. The record shows this failure.
- Put the checks in a function, `pw_python_start`, that takes an optional
  explicit path. Entry points call it without an argument; only controls pass
  one, to exercise the version and real-path refusals against a stand-in.
  The lexical drift check below forbids an argument in entry points. There is
  no environment input to the choice: the build controls that set
  `PW_PYTHON=sys.executable` do so for fixture wrappers whose shebang reads
  it, and that stays as it is.

Budget: a battery's `duration_ms` on the same build and machine grows by
at most 10 s or 1 % of the pre-change value, whichever is larger. Exceeding
it blocks completion rather than becoming follow-on work, because the cheap
leaf check makes the budget easy to meet; an overrun means the probe leaked
into leaf starts or something else regressed, and either needs finding.

### 2. Every start the resolver owns

- `build.sh`, `tests/run.sh`, `checkout_lock.sh`, `python.sh`,
  `tests/accept-release.sh`, the Makefile recipes and the
  `#!/usr/bin/env -S ${PW_PYTHON} -B` wrappers need no change beyond what
  the resolver does for them.
- `tests/lib/testlib.sh` sources `python_start.sh` right after
  `sdk_guard.sh`, so `case.sh`, direct suite scripts and release acceptance
  all resolve the interpreter themselves. The shim experiment in the record
  shows why: a suite script started outside the dispatcher has no
  `PW_PYTHON`, so `case.sh` cannot rely on the dispatcher's export. Its seven
  `/usr/bin/python3` heredocs (the assertion guard, `now_ms` and the others)
  and `test_check_python` in `case.sh:53` become `"${PW_PYTHON}"`.
- The sweep: 144 lines in 59 shell scripts under `tests/` mention
  `/usr/bin/python3` (46 suite scripts, 9 fixtures, 4 in `tests/lib`,
  comments included), and three `runner_unit` scripts call a bare `python3`.
  Every invocation becomes `"${PW_PYTHON}"`. Review the fixture scripts
  under `tests/fixtures/shell_case`, `dispatcher`, `worker_lifecycle` and
  `worker_harness` one by one: a shim start stays only where a control uses
  the shim as a deliberate negative control, and the drift check lists those
  files explicitly. Do the sweep as its own commit; it touches many files
  other agents also edit, and the drift check makes a partial sweep visible.
- Files with `#!/usr/bin/env python3` or `#!/usr/bin/python3` shebangs are
  never executed through their shebang (every start names an interpreter),
  so the shebangs are inert. Leave them or normalize them; the drift check
  should not depend on them.

### 3. Records

- Build provenance: `observe_toolchain` in `tests/lib/build_provenance.py`
  adds a `python` observation beside `cargo`, `meson` and `ninja`: the pinned
  path, its real path, the probed version, and the status of the probe.
  Bump `SCHEMA_VERSION` from 2 to 3 and make the member required in
  `record_shape()`, so a new build without it is refused rather than
  silently incomplete. Archived releases keep their version-2 records:
  `read_zip_record` refuses a record of any other version by design (the
  `version-1.zip` control in `check_build_provenance.py` establishes it),
  and nothing re-reads an archived release routinely; `release_archive`,
  `release_publish` and `release_rotate` each verify the release they are
  handling, which is a new build. One precondition follows: land the bump
  with `tests/out/.release-rotation/` empty, because an interrupted
  rotation of a version-2 archive could not resume afterwards. The fixture
  records in `tests/fixtures/dispatcher/fixture_bundle.py` and the
  `RecordTests` gain the member. Document it in
  [docs/SIGNING.md](docs/SIGNING.md#the-provenance-record)'s `toolchain`
  bullet and note the version there.
- Test runs: `resolve_config` in `tests/lib/test_cli.py` adds
  `python: {path, realpath, version}` to the configuration that `plan.json`
  and `run.json` carry. The readers compare `plan.configuration` with
  `run.configuration` (`tests/lib/retention.py:178`,
  `tests/suites/dispatcher/check_selection.py:138`); an added key passes
  through both. Document it in the output contract in `tests/README.md`.
- Case reports: the report writer in `tests/lib/testlib.sh` adds
  `interpreter: {path, realpath, version}` from the resolver's exports to
  every `report.json`, and `reconcile` in `tests/lib/suite_run.py` compares
  each report's `interpreter.realpath` with the run configuration's,
  recording an `interpreter_mismatch` harness error otherwise. That makes
  the declared interpreter per-case evidence the dispatcher checks, with the
  limits stated under verification. Bump the report's `schema_version` if
  the output contract treats an added field as a version change; document
  the field either way.

### 4. Controls

- Environment preservation at every start. `LockTests.test_helper_wrapper_children_inherit_the_callers_environment`
  in `tests/suites/preflight/check_build_provenance.py` already establishes
  the contract for `python.sh` from a forced C locale, and its failure diff
  names `LC_CTYPE`; keep it as the model. Add the same shape for the
  dispatcher and for `case.sh`: a one-case probe suite installed with
  `tests/fixtures/dispatcher/repository.py`, run through `tests/run.sh` and
  as a direct suite script, whose leaf records its own and a child's values
  of the five witnessed names plus `sys.version_info[:2]` and the real path
  of `sys.executable`. Assert the five names equal the caller's (all unset
  under `env -i`), the version is 3.14 and the real path is under the keg.
  Register it as a `shell_helpers` case; that suite needs no app.
- The coercion signature. In `verify_environment`
  (`tests/lib/checkout_lock.py`), when the differing name is `LC_CTYPE`, the
  witness is unset and the value is `C.UTF-8` or `UTF-8`, say that the helper
  interpreter coerced the locale and `PYTHONCOERCECLOCALE=0` was not honored,
  instead of advising a start through the front end. Give the opt-in
  `control_environment_witness_changed` in
  `tests/suites/preflight/opt_in/build_refusals.py` a C-locale variant that
  asserts that text. Do not add a lexical check for `-E` or `-I`.
- Resolver refusals. `ShimContainmentTests` and
  `test_entrypoints_refuse_a_stand_in_developer_directory_without_a_shim`
  currently make Python unavailable through a stand-in developer directory;
  that no longer selects Python. Replace them with an exec-denying
  `sandbox-exec` profile (the existing `(deny process-exec)` form) that
  leaves the pinned path out, so each entry point refuses with
  `direct_python_unavailable` before any Python runs; exercise
  `python_version_mismatch` and the real-path check through
  `pw_python_start` with a stand-in script that prints another version.
  `test_build_refuses_a_stand_in_developer_directory_before_any_python` in
  `tests/suites/source_drift/contract.py` and the `direct_python_unavailable`
  controls in `build_refusals.py` change the same way; `docs/build.json`
  cites them by symbol, so the citations follow.
- Drift. `tests/suites/source_drift/direct_python.py` extends its lexical
  scope from the six entry points and three wrappers to `case.sh`,
  `testlib.sh` and every `*.sh` under `tests/`: no `/usr/bin/python3` or bare
  `python3` command token outside an explicit allow-list of deliberate shim
  controls, no argument to `pw_python_start` outside controls. Its rejected
  controls get the new cases.

### 5. Documentation and generated copies

- `README.md:87-89`: `brew install meson ninja python@3.14`, and a sentence
  that the helpers run on that formula's interpreter.
- `docs/BUILD.md`: the prerequisites, the direct-Python paragraph under "The
  checkout lock" (lines 463-470), the paragraph at lines 534-540 about leaf
  scripts and the resolver, and the refusal table (`direct_python_unavailable`
  text, the new `python_version_mismatch` row). These come from
  `docs/build.json`: edit the refusal entries (`direct_python_unavailable` at
  line 1797, its citations at 1811-1814) and `inv_python_start` (line 4247),
  then regenerate with `docs/generate_build.py` and review the result.
- `tests/README.md`: lines 216-219 on the dispatcher's resolution, the shell
  case setup section, and the output contract's configuration keys.
- `tests/AGENTS.md:85`: the contained-probe example starts
  `tests/lib/python.sh -I tests/lib/shim_probe.py` instead of
  `/usr/bin/python3 -I -B`.
- `tests/lib/vendor/README.md` lines 4-5 and 26: the libraries are kept so
  that a build installs nothing, not because of Python 3.9; `tomli` stays
  because Cargo 1.94 and later read TOML 1.1 for configuration files and
  `tomllib` does not; the markdown-it-py pin is no longer forced by the
  interpreter (its move is follow-on work).
- `build.sh` changes (its resolver comments and the refusal it names), so
  regenerate the worker identity with `docs/generate_worker_identity.py`;
  `generate_build.py --check` and `generate_architecture.py --check` say
  what else is stale.

### Where this stops

No vendored package changes, no `hashlib.file_digest`, no markdown-it-py
re-vendoring, no RECORD check for `tomli`, no Intel or CI support, and no
change to which interpreter the product's own tools use. Those are listed at
the end.

## Consequential choices

- A fixed keg path, not `PATH` or an environment variable. `PATH` is caller
  controlled and unwitnessed, shims live on it, and an inherited interpreter
  would be an unrecorded input into provenance. The record argues this in
  full.
- An exact minor pin with a floating patch. Interpreter minors change stdlib
  behavior the tree cannot see (the record measured `tomllib`, locale
  coercion and parser differences); moving the pin is a reviewed commit, like
  an Xcode change. Patch versions are recorded, not constrained.
- An explicit argument to `pw_python_start` for controls, and `sandbox-exec`
  for absence. The alternative, an environment override, is what the direct
  start removed; the alternative for absence, moving the real interpreter,
  needs root.
- The resolver in `testlib.sh` rather than only `case.sh`. Direct suite
  scripts and release acceptance reach `testlib.sh` without `case.sh`, and
  the record's direct-arm failure (`PW_PYTHON: unbound variable` in a direct
  suite) is exactly a start that `case.sh` alone would miss.
- A schema bump with a required member, not an optional one. Only the
  version makes presence enforceable for new builds; the readers already
  refuse other versions by design, and archived releases are not re-read.
- The probe at entry points only, with the real path standing for the
  version at leaf starts. The Cellar path names the version, the check costs
  what today's resolver costs, and the entry points verify the probe against
  it once per battery.
- Deliberate shim starts stay only in named controls. The shim is the
  negative control for environment preservation and the subject of the
  containment probes; both need it, and the allow-list keeps every other use
  out.

## Verification

1. A fresh signed build under the new resolver (`make build IDENTITY=...`),
   whose provenance record carries `toolchain.python` with the keg real path
   and a 3.14 version.
2. The default battery against that build from an unsandboxed shell, with a
   fresh `PW_TEST_OUT_DIR`; `run.json` carries the `python` configuration,
   and no `interpreter_mismatch` harness error, so every case report
   declares the pinned interpreter and the dispatcher checked it. That is
   the whole of what the battery establishes about interpreters: each
   case's shell resolved the pin. That every Python invocation inside a case
   used it rests on the drift check over suite scripts, and that checkers'
   children used it rests on `sys.executable`. The new `shell_helpers` case
   establishes the mechanism dynamically once, from a C locale, for the
   dispatcher-driven and direct starts.
3. `tests/run.sh --suite source_drift --suite shell_helpers --suite
   dispatcher --suite preflight`, plus the opt-in groups
   `preflight/opt_in/build_refusals.py` (environment witness, direct Python
   and stand-in controls), `build_guards.py` and
   `translated_build_refusals.py`, and `tests/lib/checkout_lock.sh -- cargo
   test --manifest-path controller/Cargo.toml`.
4. The resolver's own refusals: each entry point exits 2 with the named
   refusal under the exec-denying profile; `pw_python_start` with a stand-in
   refuses `python_version_mismatch`; the coercion variant of the witness
   control prints the coercion text.
5. Timing: the battery's `duration_ms` before and after on the same build
   and machine, against the budget above.

Passes that would mislead, and what rules each out:

- A checker run directly instead of through `tests/run.sh` never exercises
  the resolver; count the battery, not direct runs, as evidence.
- A developer shell with `LANG=en_US.UTF-8` suppresses locale coercion;
  every preservation control builds its environment with `env -i`.
- A leaf that still runs 3.9 through a missed shim line passes every test it
  passed before, and its report still declares the pin, because the report
  records the resolver's answer, not each invocation; the drift check's
  whole-tree scope is what notices.
- `/opt/homebrew/bin/python3` resolving to the same binary today makes a
  `PATH` lookup look equivalent; the real-path check under the keg is what
  distinguishes them, so keep it even though it passes trivially here.
- A battery where every live case passes under the direct-started leaf says
  nothing about the shim's `CPATH` and `LIBRARY_PATH` on this machine, where
  neither directory exists. That is expected; the record explains it.

## What would require reconsideration

- Homebrew's keg layout on a supported machine lacks the `opt/python@3.14`
  link or places the Cellar elsewhere; the pin's location assumption fails
  and the resolver needs a second supported location, recorded as such.
- The per-case probe costs more than a few seconds per battery.
- An interrupted release rotation exists when the schema bump lands; finish
  or abandon it first, following `docs/SIGNING.md`.
- A live case fails only under the direct-started leaf. None of the 21
  offline cases did; the live suites were not run under it before this plan.
- Python 3.15 changes locale coercion (PEP 686); the preservation controls
  trip on the first run after a pin move, which is the intended signal.

## Follow-on work, out of scope here

- Re-vendor markdown-it-py 4.2.0 and mdurl, delete
  `_refuse_unrecognized_comments` and its test, and update the pins; the
  record has the acceptance criteria.
- Replace the five SHA-256 read loops with `hashlib.file_digest`.
- Give `tomli` the RECORD-digest check the Markdown parser has, and track
  its version as Cargo tracks TOML 1.1.
- Rename or split `source_drift/direct_python.py` if its widened scope reads
  badly beside the resolver.
