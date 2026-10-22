# Python 3.14 and the test machinery's maintenance obligations

An investigation (2026-10-22, tree at `adf537a`; experiments on a detached
worktree at `9e574fc` and in disposable copies of the runner) into which code
under `tests/lib/`, the dispatcher and `tests/suites/` exists only because
the helpers run on Python 3.9, and would become unnecessary under Python
3.14. It is not a migration plan. A second pass answered three of the first
pass's open questions: the interpreter policy is settled by the operator,
the vendored TOML parser turns out to supply something the standard library
lacks, and the leaf shim question was measured through the real dispatcher
chain.

## Summary

- The repository's Python is Xcode's 3.9.6, pinned in three places: the
  resolver `tests/lib/python_start.sh` that `build.sh`, `tests/run.sh` and
  `tests/lib/checkout_lock.sh` source; the `/usr/bin/python3` shim that
  `tests/lib/case.sh:53` and 59 shell scripts under `tests/` start for leaf checkers;
  and `sys.executable` propagation inside those checkers.
- The Python tree carries no version conditionals and no import fallbacks.
  All 203 non-vendored files compile under 3.14.8 without a warning, all 49
  modules in `tests/lib/` and `docs/` import with deprecation warnings as
  errors, and the build-provenance (61), Markdown reader (36), direct-Python
  (2) and Cargo-configuration (5) controls pass under 3.14 unmodified.
- Two credible reductions remain, in order of value: retire the Markdown
  comment refusal by re-vendoring a markdown-it-py that needs Python 3.10,
  and collapse five hand-rolled SHA-256 loops to `hashlib.file_digest`.
  Each presupposes that the resolver and the leaf shim invocations agree on
  an interpreter of at least 3.11.
- The vendored `tomli` is not baggage. Cargo 1.94 parses TOML 1.1 for
  manifests and configuration files; the installed Cargo 1.99 accepts four
  TOML 1.1 forms in `.cargo/config.toml` that Python 3.14's `tomllib` refuses
  and tomli 2.4.1 accepts. Replacing it would make the build refuse
  configurations Cargo reads.
- The shim's environment mutation does reach leaf children in the real
  chain: a leaf started by `/usr/bin/python3` and its children carry
  `SDKROOT`, `CPATH`, `LIBRARY_PATH` and `MANPATH`; a leaf started by the
  direct interpreter does not. Compilers started from such a leaf get
  `-I /usr/local/include` and `-L /usr/local/lib`, and a leaf-driven build
  witnesses all four as set. On this machine neither directory exists, so
  the difference is latent; both arms pass.

## Decisions recorded from the operator

- Python 3.14 becomes an explicit development prerequisite in its own right,
  not by way of Meson. The vendor README's "nothing installed during a
  build" premise was a consequence of choosing Apple's Python and does not
  survive abandoning that choice. The replacement requirement: PolicyWitness
  identifies its selected interpreter, verifies its version, and installs
  nothing implicitly during a build or a test execution.
- No `python` equipment category. Python starts the dispatcher itself, so a
  missing or incompatible interpreter is an entry-point refusal, not a
  missing-equipment record on every selected case. Equipment checks remain
  for prerequisites individual cases may or may not need.
- Retain `tomli` under 3.14 (evidence below).
- Eliminating incidental shim mutation from the leaf machinery while keeping
  deliberate shim probes as explicit experiments is a prospective decision,
  not a finding of this record.

## What was run and observed

Commands ran from the repository root, the experiment worktree
(`/private/tmp/claude-501/-Users-raccoon-Desktop-Security-PolicyWitness/cb8347ad-28c5-4da9-97f1-b12cd9418706/scratchpad/pw-py314`)
or sibling scratch directories; all are session scratch outside the checkout
and not retained by git. "3.9" is
`/Applications/Xcode.app/Contents/Developer/usr/bin/python3` (3.9.6, the same
binary `/usr/bin/python3` shims); "3.14" is `/opt/homebrew/bin/python3.14`
(3.14.8).

### Baseline and compatibility

| Observation | Result |
| --- | --- |
| `xcode-select -p` python3 and `/usr/bin/python3 --version` | 3.9.6 both |
| `head -1 /opt/homebrew/bin/meson` | `#!/opt/homebrew/opt/python@3.14/bin/python3.14` (Meson 1.12.1) |
| Pattern sweep for `version_info`, `ImportError` fallbacks, `typing_extensions`, `backport`, `compat` outside `tests/lib/vendor/` | none; four `from __future__ import annotations`, one `typing` import (`tests/build-evidence.py:41`) |
| Sweep for APIs removed or deprecated in 3.10 to 3.14 | none; `os.walk(onerror=)` at `tests/lib/output_target.py:202` keeps its name in 3.14 |
| `compile()` of all 203 non-vendored `.py` files under 3.14 with warnings recorded | 0 syntax errors, 0 warnings |
| `importlib.import_module` of every `tests/lib/*.py` and `docs/*.py` under 3.14 with `-W error::DeprecationWarning` | 49 imported, 0 failed |
| `check_build_provenance.py` under 3.14, unmodified tree | 61 tests, OK, 71.5 s |
| `source_drift/markdown.py`, `source_drift/direct_python.py`, `CargoConfigurationTests` under 3.14, unmodified | 36, 2 and 5 tests, OK |
| `inspect.signature` on both interpreters | 3.14 adds `tomllib`, `hashlib.file_digest`, `Popen(process_group=)`, `shutil.rmtree(onexc=)`, `TemporaryDirectory(delete=, ignore_cleanup_errors=)`, `Path.copy/move/walk/info`, `tarfile` filters; `socket.LOCAL_PEERPID` is absent in both; `time.monotonic` is `mach_absolute_time()` in both |
| Locale coercion from a C locale (`env -i`), both interpreters, `-B` | default: each sets `LC_CTYPE=C.UTF-8` for itself and its child; with `PYTHONCOERCECLOCALE=0`: neither sets it. 3.14.8 and 3.9.6 agree in all four cells; `utf8_mode` is 1 in all |
| Interpreter boundary counts | `/usr/bin/python3` in 59 shell files under `tests/`, 144 lines (comments included; 46 suite scripts, 9 fixtures, 4 in `tests/lib`), plus 3 bare `python3` lines in `runner_unit`; `${PW_PYTHON}` in 8 files; `sys.executable` in 34 lines; `sys.path.insert` in 154 lines |

### TOML

| Observation | Result |
| --- | --- |
| Cargo changelog (Cargo Book, fetched 2026-10-22) | Cargo 1.94 (2026-03-05), "Added": "Cargo now parses TOML v1.1 for manifests and configuration files", PR #16415 |
| Installed toolchain | `cargo 1.99.0 (5f94df478 2026-08-27)`, `rustc 1.99.0` |
| `cargo metadata --no-deps --offline` in a crate whose `.cargo/config.toml` uses one TOML 1.1 form at a time | accepted: `"a\eb"`, `"a\x41b"`, a multiline inline table, a trailing comma in an inline table. Refused: a time value `07:32`, and also the TOML 1.0 form `07:32:00`, both at `pw.t`: a configuration value-type refusal, not a dialect one |
| The four accepted forms under 3.14's `tomllib` | all four `TOMLDecodeError` |
| The same four under the vendored tomli 2.4.1 (on 3.9 and on 3.14) | all four parse |
| `diff` of `tests/lib/vendor/tomli/` against 3.14's `tomllib` | same lineage; tomli 2.4.1 adds the TOML 1.1 forms and explicit nesting limits; `_types.py` identical |
| 2000-deep arrays and inline tables, 5000-part dotted key | `RecursionError` from tomli 2.4.1 and from `tomllib` alike |
| `tomllib` swap in `cargo_config.py`, `CargoConfigurationTests` | 3.14: 5 tests OK; 3.9: `ModuleNotFoundError`; a containment control that starts `tests/run.sh` then fails because the resolver's 3.9 cannot import it |

### Markdown and digests

| Observation | Result |
| --- | --- |
| PyPI (2026-10-22) | markdown-it-py 4.2.0 requires Python >= 3.10; tomli 2.5.0 requires >= 3.8; mdurl 0.1.2 unchanged since 2022 |
| `gh api markdown -f mode=gfm` on `a <!-- x -- y --> b`, `a <!-- plain --> b`, `a <!--> b`, `a <!--  --> b` | `<p>a  b</p>` for all four: GitHub hides each comment |
| markdown-it-py 4.2.0 (uv venv on 3.14) on the same texts, CommonMark preset plus `table`, without `text_join` | each becomes one `html_inline` token; the vendored 3.0.0 leaves `a <!-- x -- y --> b` as text |
| 4.2.0 package inspection | `markdown_it/main.py` still imports `linkify_it` when it can; `_compat.py` still present |
| `source_drift/markdown.py` under 3.14 with 4.2.0 copied over the vendored packages and `VERSION = '4.2.0'` | 30 of 36 pass; the two-hyphen refusal subtests fail with `Refused not raised`; three tests fail on the pinned strings and RECORD digests; one errors because the copy omitted the wheel's license files |
| Every tracked Markdown document (105, `git ls-files '*.md'`) parsed by the checked-in reader on 3.0.0 under 3.9 and by the worktree's reader on 4.2.0 under 3.14, dumping blocks, headings, links, list items, tables, references and every inline run's kind, lines, depth, text, code spans, pieces and leading span | identical dumps: 12,201 inline runs, 714 headings, 3,041 links, no document differs |
| `hashlib.file_digest` against the repository's 1 MiB read loop under 3.14 | identical digests for an empty file, 4 bytes, exactly 1 MiB, 3 MiB + 7 bytes, `ZipExtFile` members and tar `ExFileObject` members |

### The leaf shim, through the real dispatcher chain

Method. `tests/fixtures/dispatcher/repository.py`'s `install_runner` copied
the runner into two disposable repositories with one catalog entry, a suite
script modeled on `tests/fixtures/shell_case/python_startup.sh`, and a leaf
probe that imports no harness code. The probe records its interpreter, its
own values of `SDKROOT`, `CPATH`, `LIBRARY_PATH`, `MANPATH`, `DEVELOPER_DIR`
and `LC_CTYPE`, the values a child `/usr/bin/env` sees, the `-isysroot`,
`-I`, `-syslibroot` and `-L` arguments of a dry-run
`/usr/bin/xcrun --sdk macosx clang -###` compile and link (the form the
fixture build scripts use), `xcrun --show-sdk-path`, and what the checkout
lock front end `tests/lib/checkout_lock.sh`, started from the leaf with the
inherited claim descriptors, witnesses for its child. The "shim" arm kept
the copied `case.sh` as it is (`test_check_python` starts
`/usr/bin/python3`); the "direct" arm changed that one token to
`"${PW_PYTHON}"`, which the dispatcher already exports. Both arms ran
`bash tests/run.sh --suite probe` under the same Python 3.9.6 from a shell
with none of the six variables set.

| Observation | Shim arm | Direct arm |
| --- | --- | --- |
| Dispatcher result | `ok: true`, case passed | `ok: true`, case passed |
| Leaf interpreter | 3.9.6 (the shim exec'd the same binary) | 3.9.6 |
| Leaf's own `SDKROOT`, `CPATH`, `LIBRARY_PATH`, `MANPATH` | `.../MacOSX.sdk`, `/usr/local/include`, `/usr/local/lib`, four SDK man paths | all unset |
| Child `/usr/bin/env` | the same four values | all unset |
| `clang -###` cc1 arguments | `-isysroot .../MacOSX.sdk`, `-I /usr/local/include` | `-isysroot .../MacOSX.sdk` |
| `clang -###` ld arguments | `-syslibroot .../MacOSX.sdk`, `-L /usr/local/lib` | `-syslibroot .../MacOSX.sdk` |
| Front end witness for a leaf-driven command | `PW_ENV_WITNESS_SDKROOT`, `_CPATH`, `_LIBRARY_PATH`, `_MANPATH` all `s…` (set), `_LC_CTYPE` `u` | all five `u` |
| `/usr/local/include`, `/usr/local/lib` on this machine | absent | absent |

Contained dry runs through `tests/lib/shim_probe.py` (sandbox-exec, the
install-on-demand lookup denied) confirmed the mechanism without the shim:
with the shim's values clang emits `-I /usr/local/include` and
`-L /usr/local/lib` although neither directory exists; with
`CPATH=/opt/homebrew/include` and `LIBRARY_PATH=/opt/homebrew/lib` it emits
those; with the variables unset it emits neither. `-isysroot` was the same
SDK in every case because `xcrun --sdk macosx` selects it.

One probe in the first pass ran the bare shim with `SDKROOT=/pw/custom.sdk`
instead of using `shim_probe.py`. The shim refused the path and asked macOS
to install the Command Line Tools, which raised the install dialog on the
desktop; it was cancelled and nothing was installed. The direct interpreter
passed the same invalid value through unchanged, and `xcrun --show-sdk-path`
in its child then reported `/pw/custom.sdk`. `tests/AGENTS.md`'s rule to use
the contained helper for any by-hand `SDKROOT` or `DEVELOPER_DIR` probe
exists for exactly this.

Where the mutation can matter. Twenty-two Python files under `tests/` start
compilers, SwiftPM, Cargo, Meson or a fixture `build.sh`, so their children
run under the shim's values in the real chain. The opt-in build controls
(`preflight/opt_in/build_refusals.py:239-245`, `build_guards.py`,
`translated_build_refusals.py`) strip `DEVELOPER_DIR`, `SDKROOT`, `CPATH`,
`LIBRARY_PATH`, `MANPATH` and `LC_CTYPE` from their base environment
themselves. `source_drift/contract.py`'s constructed-checkout builds
(`BUILD_ENV_EXCLUDED` at `:41`) do not; neither do the SwiftPM receipts
(`tests/lib/build_receipt.py`), the Meson receipts
(`tests/lib/meson_receipts.py`), `runner_unit`'s host setup builds,
`sandbox_extensions_native/check.py`, `witness_contract/check_max_target_reply.py`
or the fixture builds `check_release_publish.py` and
`check_build_provenance.py` start. `build.sh` itself saves the caller's
`SDKROOT` as the SDK request and unsets it (`build.sh:210-214`) before
selecting its own, but keeps `CPATH`, `LIBRARY_PATH` and `MANPATH`, which
`invocation_environment()` in `build_provenance.py` passes to Cargo
unchanged; `cargo_config.conflicts` compares `[env]` entries only against
`SDKROOT`, `MACOSX_DEPLOYMENT_TARGET` and `DEVELOPER_DIR`, so a differing
`CPATH` or `LIBRARY_PATH` is witnessed but not judged.

What this establishes. In the real chain a shim-started leaf and its
children run with four variables a direct-started leaf does not have. On a
machine where `/usr/local/include` or `/usr/local/lib` is populated, every
compile and link a leaf starts would search them under the shim and not
under the direct interpreter, and a leaf-driven build would witness and pass
on a different environment. On this machine the compiled outputs cannot
differ, because the directories are absent and the SDK is the same. A pass
in both arms therefore tested different conditions, as the question
anticipated. Whether any case has ever depended on the difference is not
established and would need a machine with those directories populated.

### Ordinary offline cases under a direct-started leaf

A second clean worktree ran the three offline suites through `tests/run.sh`
twice: once with the stock `tests/lib/case.sh` and once with its line 53
changed from `/usr/bin/python3 "$@"` to `"${PW_PYTHON}" "$@"`. Nothing else
changed between the arms.

| Arm | `shell_helpers`, `dispatcher`, `source_drift` (21 cases) | Duration |
| --- | --- | --- |
| Stock `case.sh` (shim-started leaf) | 21 pass, `ok: true`, no harness errors | 597 s |
| `case.sh:53` → `"${PW_PYTHON}"` | 20 pass, 1 fail: `shell_helpers/python_startup` | 616 s |

The one failure is informative. `check_python_startup.py` copies the
runner, `case.sh` included, into a fixture repository and drives a probe suite
both through the dispatcher and as a direct suite script. All twelve
dispatcher-driven controls passed under the change; the direct-suite control
failed with `case.sh: line 53: PW_PYTHON: unbound variable`, because a suite
started outside the dispatcher inherits no `PW_PYTHON`. So no ordinary
offline case depended on the shim's environment, and the one-token change is
not the whole change: `case.sh` would have to resolve the interpreter itself
when it is started directly, the way the entry points do through
`python_start.sh`. The live suites, which need a signed app and an
unsandboxed shell, were not run under either arm.

Timing of the three unittest files back to back in the same worktree, 3.9
then 3.14: `check_build_provenance.py` 88.6 s and 95.2 s (earlier 3.14 runs
took 66.8 s and 71.5 s, so the file is deadline-bound and the spread is
machine load, not the interpreter); `source_drift/markdown.py` 0.9 s and
1.3 s; `direct_python.py` 0.8 s and 0.9 s.

## The interpreter boundary

`tests/lib/` is shared between the test battery and the build. `build.sh`
starts eleven of its helpers (`build_provenance.py`, `cargo_artifacts.py`,
`native_sources.py`, `signer_check.py`, `checkout_lock.py`,
`build-evidence.py` and the five `docs/generate_*.py` scripts), and every
dispatcher start imports `cargo_config` through `test_cli` → `suite_run` →
`artifact` → `build_provenance`. A stdlib feature used in a shared module is
a requirement on the build's interpreter and the dispatcher's, not only on a
suite's.

The interpreter is chosen in three independent places:

- `tests/lib/python_start.sh` resolves `xcode-select -p` and starts that
  directory's `usr/bin/python3` directly, exporting `PW_PYTHON` and
  `PYTHONCOERCECLOCALE=0`, so the `/usr/bin/python3` shim cannot insert
  `SDKROOT`, `CPATH`, `LIBRARY_PATH` or `MANPATH` into the environment the
  build witnesses ([docs/BUILD.md](../docs/BUILD.md), "The checkout lock").
  `source_drift/direct_python.py` keeps the six entry points on it.
- Leaf checkers start through the shim: `tests/lib/case.sh:53`
  (`test_check_python`), seven heredocs in `tests/lib/testlib.sh`, and 144
  lines in 59 shell scripts under `tests/` name `/usr/bin/python3`. `direct_python.py`
  excludes leaf scripts from its scope by design. The dispatcher exports
  `PW_PYTHON` into every case's environment, so the leaf side can start
  directly with a one-token change in `case.sh`; the direct arm above is
  that change.
- Checkers that start Python children pass `sys.executable` (34 lines), and
  the build controls set `PW_PYTHON=sys.executable` for the builds they
  drive.

The containment-test failure under the `tomllib` swap shows the coupling: the
checker ran on 3.14, the entry point it started resolved 3.9, and the shared
module could not import. Any reduction below holds only once the resolver
and the shim invocations agree on an interpreter of at least 3.11. That
change is the migration this record does not plan; its size is the 144
shim lines, `case.sh`, `testlib.sh` and `python_start.sh`.

## Candidates

### 1. Retire the inline-comment refusal by re-vendoring markdown-it-py

What is maintained. `docs/markdown_reader.py:277-287`
(`_refuse_unrecognized_comments`), its call at `:201`, the test
`test_an_inline_comment_containing_two_hyphens_is_refused` at
`tests/suites/source_drift/markdown.py:145-149`, and the README sentence that
a newer parser needs a newer Python. The refusal exists because markdown-it-py
3.0.0, the last release for 3.9, implements CommonMark 0.30, where an inline
comment may not contain `--`, while GitHub hides such comments.

What changes it. markdown-it-py 4.x requires Python 3.10 and reads comments
the way GitHub does; 4.2.0 agreed with `gh api markdown` on all four probed
forms, including `<!-->`. With 3.14 the pin can move.

What disappears. The method, its call, the test and the README sentence. The
`Refused` class stays for its other use (`:316`, duplicate section titles).
The `linkify_it` guard at `:33-36` stays: 4.2.0's `main.py` still imports
`linkify_it` opportunistically.

What might change. A major version of the parser. Two oracles say nothing
else changes for this repository: the 30 reader controls that passed with
4.2.0, and a dump of everything the reader reports for all 105 tracked
documents, which is identical between 3.0.0 on 3.9 and 4.2.0 on 3.14. The
second covers the corpus the generators and drift checks read; it does not
cover Markdown the repository does not yet contain.

What establishes preservation. Re-vendor per the README procedure (wheel
digest matched to PyPI, package directories byte for byte, license files
placed in the package, `RECORD` kept beside them), update `RECORDS` at
`markdown.py:27-29`, `VERSION` at `markdown_reader.py:23` and the version
strings at `markdown.py:371-375`, delete the refusal and its test, then run
`source_drift` in full so every document parses the same.

Effort. Moderate, mostly mechanical, with one judgment: adopting a major
version of a third-party parser. Gated on an interpreter of at least 3.10.

### 2. Replace five SHA-256 read loops with `hashlib.file_digest`

What is maintained. The same four-line loop in `tests/lib/artifact.py:66-71`
(`digest`), `tests/lib/build_provenance.py:329-334` (`sha256_file`) and
`:2202-2209` (`member_digest`), `tests/lib/meson_receipts.py:51-56`
(`sha256`), `tests/lib/release_runs.py:102-105` and
`tests/build-evidence.py:48-53` (`sha256_file`); about forty call sites use
the first three names.

What changes it. `hashlib.file_digest` (3.11) reads any binary file object
with `readinto`, which the zip and tar member streams here provide; digests
matched in every probed case.

What disappears. Four duplicated bodies become one call each; no helper name
needs to change. About twenty lines, and one fewer idiom to keep identical.

What might change. Nothing observable; `file_digest` consumes the stream to
EOF as the loop does. Keep the helpers' names so the call sites and the
evidence they write stay untouched.

Effort. Trivial. It is listed because it is a genuine stdlib replacement for
hand-rolled code, and ranked last because the obligation it removes is small.

### Withdrawn: the vendored `tomli`

The first pass ranked deleting `tests/lib/vendor/tomli/` for `tomllib`
first: 930 vendored lines, a README procedure, a `sys.path` insertion in
`cargo_config.py:56`, ten enumerated fixture paths, and no RECORD check
beside the package. The swap passed `CargoConfigurationTests` under 3.14.

It is withdrawn. Cargo 1.94 parses TOML 1.1 for configuration files, the
installed Cargo 1.99 accepts `\e` and `\x` escapes, multiline inline tables
and trailing commas in `.cargo/config.toml`, and 3.14's `tomllib` refuses
every one of them while tomli 2.4.1 accepts them. `Reader.load` would turn a
configuration Cargo reads into `not valid TOML` and a
`cargo_configuration_unresolved` refusal of the build. The vendored package
supplies functionality the newer standard library lacks, and the README's
reason for it should say so rather than naming Python 3.9. One obligation
does follow: tomli tracks TOML 1.1 as Cargo does, so its version should be
kept current the way the README describes, and a RECORD check like the
Markdown parser's would close the gap in how it is verified.

### Not reductions

These become available and are not worth doing for their own sake: the four
`from __future__ import annotations` lines and the `typing` names in
`build-evidence.py`; `__slots__` on `cargo_config.Leaf` versus
`dataclass(slots=True)`; `os.walk(onerror=)` versus `Path.walk(on_error=)`;
`timezone.utc` versus `datetime.UTC` (9 lines); seventeen `mkdtemp` sites with
explicit `rmtree` versus `TemporaryDirectory(delete=False)`; five `zip` calls
guarded by length assertions versus `strict=True`. None removes a mechanism
or a test.

## Non-candidates

Each of these looked like compensation and is not.

- The vendored `tomli`, above: it is ahead of the standard library, not
  behind it.
- The direct-Python start and environment witness (`python_start.sh`,
  `python.sh`, `sdk_guard.sh`, `checkout_lock.sh`, `shim_probe.py`,
  `source_drift/direct_python.py`, `PYTHONCOERCECLOCALE=0`). It compensates
  for Xcode's shim and for PEP 538 locale coercion rewriting `LC_CTYPE`, both
  of which the build's witness contract treats as inputs. A Homebrew 3.14 is
  not a shim, but the resolver, the witness and the drift check would move to
  the new interpreter, not disappear; and 3.14 still coerces the C locale.
  The shim experiment above is a reason to extend this machinery to the leaf
  side, not to retire it.
- Tar member verification in `tests/lib/release_runs.py:74-122` against
  3.12's extraction filters (default `data` in 3.14). The archive is never
  extracted; members are compared as streams to an independent inventory with
  digests, which no filter does. Adopting a filter adds a line and removes
  nothing. This is the calibration example: the stdlib feature has the right
  name and the wrong contract.
- `tests/lib/checkout_lock.py`: the hand-defined `SOL_LOCAL, LOCAL_PEERPID`
  (`:109`), the SCM_RIGHTS handoff, and `group_finished` polling `killpg`
  (`:541-556`). 3.14 has no `LOCAL_PEERPID` constant, macOS has no pidfd, and
  `Popen(process_group=)` does not replace `start_new_session`.
- The bounded probe at `tests/lib/build_provenance.py:191-268`: per-stream
  byte caps, one deadline for the whole group, SIGTERM then SIGKILL with a
  bounded cleanup report. `subprocess.run(timeout=)` kills the leader only
  and caps nothing.
- `problem()` and `harness_errors` in `tests/lib/suite_run.py` versus
  `ExceptionGroup`. The dispatcher accumulates diagnostics into `run.json`
  and continues; exceptions would end the accounting the contract requires.
- The `-B`, `PYTHONDONTWRITEBYTECODE` and `sys.dont_write_bytecode`
  convention (14 sites). 3.14 writes bytecode exactly as 3.9 does; the
  convention protects source snapshots and identity checks.
- The 154 `sys.path.insert` lines. They implement the repository's choice of
  script-local imports; no interpreter flag between 3.9 and 3.14 changes
  that.

## Recommended first experiment

Re-vendor markdown-it-py and delete the comment refusal. It is the one
remaining reduction that removes a mechanism and a test, and its oracle is
external.

1. In a worktree whose resolver and shim invocations both reach an
   interpreter of at least 3.10, vendor markdown-it-py 4.2.0 and mdurl per
   `tests/lib/vendor/README.md` (wheel digests matched to PyPI, package
   directories byte for byte, license files in the package, `RECORD` files
   beside them), set `VERSION = '4.2.0'` in `docs/markdown_reader.py`,
   update `RECORDS` and the version strings in
   `tests/suites/source_drift/markdown.py`, delete
   `_refuse_unrecognized_comments`, its call and its test, and remove the
   README sentence about needing a newer Python.
2. Accept when all of the following hold: `source_drift/markdown.py` passes
   36 minus the deleted test; `tests/run.sh --suite source_drift` passes in
   that worktree, so every tracked document still parses and every generator
   check still agrees; a document containing `text <!-- a -- b --> after`
   parses with no `Refused` and its prose excludes the comment; and
   `gh api markdown -f mode=gfm` on the same text still hides it.
3. A misleading pass to rule out: running `markdown.py` alone. The
   generators and citation checks read every tracked document through the
   reader, and only the suite exercises them.

If the operator takes the prospective decision on the leaf shim, the change
is to `tests/lib/case.sh:53` and the seven heredocs in `testlib.sh`, with
`case.sh` resolving the interpreter itself when `PW_PYTHON` is absent (a
direct suite script has none), plus extending
`source_drift/direct_python.py`'s scope to both files. Acceptance: the chain
probe above with the witness reading `u` for all four variables under a
leaf-driven front end; the three offline suites at 21 of 21, including the
direct-suite control of `shell_helpers/python_startup`; and the live battery
once, since it was not run under a direct-started leaf here.

## Discovery method for later work

1. Fix the interpreter boundary first. Read `tests/lib/python_start.sh`,
   `tests/lib/case.sh:53`, and count `grep -rl '/usr/bin/python3' tests
   --include='*.sh'`. Anything a candidate needs from a newer stdlib is a
   requirement on every process on the far side of those lines.
2. Separate the shared library from suites. `tests/lib/` modules are build
   helpers too (`grep -n PW_PYTHON build.sh`), so a change there is checked
   by the build's controls, not only a suite's.
3. Look for baggage where it actually lives here, since conditionals are
   absent. The productive searches were: `vendor` and `sys.path.insert`
   targets; a README or docstring that names a Python version or a pinned
   package version as the reason; a message that names the pinned version
   (`markdown-it-py {VERSION} reads this`); and identical bodies repeated
   across modules (`iter(lambda: stream.read(1024 * 1024), b'')`).
4. Before deleting a vendored package for a stdlib module, check what the
   package's consumers read, not what the module's name promises. The
   question for `tomli` was not "does the stdlib parse TOML" but "which TOML
   does Cargo write", answered by the installed Cargo and its changelog. A
   `diff` of the vendored code against the stdlib copy shows the surface;
   a probe of the external producer shows whether it matters.
5. Inventory the stdlib surface before guessing: count imports per module
   over the non-vendored tree, then grep each surface the newer stdlib
   touches (`hashlib.sha256()` loops, `onerror=`, `tarfile`, `killpg`,
   `start_new_session`, `flock`, `kqueue`, `selectors`, `mkdtemp`,
   `TemporaryDirectory`, `rmtree`). Confirm each supposed replacement with
   `inspect.signature` on the target interpreter, not from memory; this
   record expected `socket.LOCAL_PEERPID` and found it absent.
6. For each hit, ask in order: does the stdlib call give the same guarantee
   (bounds, never-extract, ordering, group cleanup, evidence written on
   failure)? Is the complexity tied to the interpreter, to Darwin, or to the
   evidentiary rules in `tests/AGENTS.md`? Which tests encode the current
   behavior (RECORD digests, version strings, refusal texts)? Those tests are
   both the acceptance criterion and the mechanical cost.
7. Probe in a detached worktree under the scratch directory, running the
   Python file directly under both interpreters, with a negative control:
   the old interpreter must fail where the change depends on the new
   stdlib. For anything that touches `SDKROOT` or `DEVELOPER_DIR`, go
   through `tests/lib/shim_probe.py`; the bare shim with an invalid value
   raises the Command Line Tools install dialog on the desktop. For a
   question about what reaches children in the real chain, build a
   disposable runner with `tests/fixtures/dispatcher/repository.py` and a
   one-case probe suite, and pass the lock claim's descriptors to any
   front end the probe starts. Use `gh api markdown -f mode=gfm` as
   GitHub's oracle for Markdown questions.
8. Signs the complexity is intentional: a docstring stating a contract
   ("inspected as streams, never extracted"; "a failure is recorded, never
   fatal"), a citation in `docs/build.json` or `docs/architecture.json`, or a
   `source_drift` control guarding it.

## Remaining uncertainties

- markdown-it-py 4.x on Markdown the repository does not yet contain. For
  the tracked corpus the question is closed: the reader reports the same
  structure under both versions, and the swapped controls needed no change
  to `markdown_reader.py` beyond the version pin.
- Whether any case has ever depended on the shim's `CPATH` or
  `LIBRARY_PATH` reaching a compile. This machine cannot show it; a machine
  with `/usr/local/include` or `/usr/local/lib` populated can, by running the
  chain probe there or by diffing the fixture receipts a battery writes.
- Python 3.15's default UTF-8 mode (PEP 686) and what it does to locale
  coercion. On 3.14 the question is closed: coercion and
  `PYTHONCOERCECLOCALE=0` behave exactly as on 3.9, so the environment
  witness holds unchanged. It is the next interpreter's question, not this
  one's.
- Whether the live suites (app, XPC, worker) behave the same under a
  direct-started leaf. The offline suites do; the live ones were not run.
- Performance is closed as far as it matters: the three unittest files take
  the same order of time under both interpreters, and the one long file is
  deadline-bound.
