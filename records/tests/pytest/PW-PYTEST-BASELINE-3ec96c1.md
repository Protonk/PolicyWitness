# pytest migration baseline for build_provenance_controls: revision 3ec96c1

A whole-file snapshot of
[check_build_provenance.py](../../../tests/suites/preflight/check_build_provenance.py)
at `3ec96c1791bcecfc4ef719c91f2de07ba184e988` (`main`, clean working tree,
read on 2026-10-26), with the execution reference a later trial compares
against. Every later trial or migration stage appends comparison rows at the
end, using only the labels preserved, isolation-improved, blocked and revised.
The source findings below stay as written; corrections to flagged expectations
land as separate changes and are then named in the row that flagged them.
Repository links to this record belong only in
[the investigation plan](../../../tests/suites/preflight/PW-PYTEST-INTEGRATION-INVESTIGATION-PLAN.md).

Everything in the source baseline is source-derived. Measured behavior appears
only in the execution reference and is labeled there. The case is reached only
through the public dispatcher as `tests/run.sh --case preflight/build_provenance_controls`;
this record names no other way to start it.

## Summary counts

| Quantity | Count | How counted |
| --- | --- | --- |
| Source lines | 2975 | `wc -l` |
| Classes deriving from `unittest.TestCase` | 17 | 16 with test methods and `StampFixture`, a base class with `setUp` only |
| Test methods | 68 | `def test_` at class indentation; identifiers BP01 to BP68 below |
| `subTest` sites | 35 | `with self.subTest(` occurrences, in 29 methods |
| Labeled `subTest` variants | about 350 | loop sizes read from source (per-method counts in the tables); not an execution count |
| Methods with unlabeled multi-scenario loops | 15 | loops without `subTest`, listed per row |
| Methods that retain artifacts in the case directory | 10 | every `ShimContainmentTests` method |
| Native compiles per execution | 1 in `OutputTargetTests.setUpClass`, 1 per `RecordTests` method (7), 2 single-file compiles elsewhere | source reading |
| Flagged expectations | 9 | the numbered list below |

## Source baseline

### Invocation boundary at 3ec96c1

The chain from the public command to the checker, as the sources at this
revision describe it:

1. `tests/run.sh` resolves and probes the pinned Homebrew `python@3.14`
   interpreter (`tests/lib/python_start.sh`), sources `testlib.sh`, and starts
   `tests/lib/test_cli.py` with `-B -S`.
2. `test_cli.py` reads `tests/catalog.json`, selects
   `preflight/build_provenance_controls` (`requires: ["clang"]`, default
   member, standard context, no dependencies), resolves the configuration,
   takes `tests/.checkout.lock`, replaces eligible output, writes `owner.json`
   and `plan.json`, and hands over to `suite_run.execute`.
3. `suite_run.execute` checks the `clang` prerequisite with `shutil.which`,
   starts the catalog command (the preflight suite script under `bash`) in its
   own session through the lock scope's `popen` (the case inherits the held lock descriptor and claim
   variables as a protected child), with an environment that drops every
   inherited `PW_TEST_*` value and sets `PW_APP_DIR`, `PW_BIN`, `PW_BIN_PATH`,
   `PW_TEST_OUT_DIR`, `PW_TEST_EVENTS`, `PW_TEST_RUN_ID`, `PW_TEST_QUIET`,
   `PYTHONDONTWRITEBYTECODE=1` and `PW_TEST_CASES`.
4. The case script sources `case.sh`, selects the case by `test_selected`,
   calls `test_begin preflight build_provenance_controls` (creates
   `suites/preflight/build_provenance_controls/artifacts/`, exports
   `PW_TEST_ARTIFACTS` and `PW_TEST_SCRATCH`, writes the start event), emits
   one `helpers` step, then `test_check_python` starts the checker file with
   the pinned interpreter and `-B -S`, both streams redirected to
   `artifacts/assertions.log`.
5. A nonzero checker exit prints the log to stderr and `test_fail` writes a
   failed report and exits 1 before any success event. A zero exit reaches
   `test_pass`, which removes `scratch/`, writes the end event to both event
   streams and `report.json` with the case's own interpreter resolution.
6. `suite_run.reconcile` requires exactly one start and one end event per
   case, a report whose status agrees with the end event, an interpreter real
   path equal to the dispatcher's, no remaining `scratch/` and no `.build`
   tree; `account` refuses undeclared skips (this case declares none).

Inside the checker: `ROOT` is derived from `__file__`; `tests/lib` and
`tests/fixtures/dispatcher` are inserted at the front of `sys.path`; the
production helpers `build_provenance`, `cargo_config`, `checkout_lock`,
`output_target`, `signer_check`, `fixture_bundle` and `shim_probe` are imported
in-process; `PYTHON = sys.executable` names the interpreter every child
Python receives, always with `-B -S` and often `-P`. The module ends in
`unittest.main(verbosity=2)`: classes are loaded in alphabetical order and
methods alphabetically within a class, each method gets a fresh instance,
`setUp` and `addCleanup` run per method, a `subTest` failure is recorded and
the loop continues, the method line and the `Ran N tests` summary go to
stderr, and the process exits 1 on any failure or error and 0 otherwise. The
outer case therefore passes only when every method passes; it has no
visibility into individual methods beyond the log text.

Responsibilities an inner framework would assume inside this boundary:
collection from the one explicitly named file, per-method execution and
failure accounting, per-method and per-variant reporting, and the exit status
handed back to `test_run_logged`. Selection, prerequisites, the checkout lock,
output ownership, interruption, accounting and retention stay with the
dispatcher.

### Module-level machinery

| Name | Role | Classification |
| --- | --- | --- |
| `environment(env)` | replaces `os.environ` for a block and restores it | organizational |
| `run_main(argv, env)` | calls `build_provenance.main` in-process under a controlled environment with both streams captured; returns status, stdout, stderr | organizational; the in-process subject boundary of every helper subcommand check |
| `fake_observation(**overrides)` | a complete toolchain observation of the production shape | constructed input |
| `write_compilers`, `write_configured_output` | Meson introspection files of the shape Meson 1.12 writes | constructed input |
| `NAMES`, `LIB`, `CLAIM`, `PINNED_PYTHON` | the witnessed variable names, the helper directory, the claim variable names, the pinned interpreter path | constants |
| `clean_env()` | this process's environment without the dispatcher's lock claim and witnesses | organizational; evidence that the checker runs under the dispatcher's claim |
| `witnessed(env)` | adds exact environment witnesses and `PYTHONCOERCECLOCALE=0` | constructed input |
| `own(test, root)` | an in-process lock owner for the test's duration (an `ExitStack` closed by `addCleanup`) and a claimed, witnessed child environment | organizational; shared by nine methods across six classes |
| `lock_free(root)` | whether the lock can be taken now, through a separate open | independent observation |
| `wait_for`, `alive` | polling with a deadline; `kill(pid, 0)` liveness | organizational helpers that are themselves observation instruments in lock controls |
| `WRAPPER`, `FAKE_OWNER`, `ADMISSION_CLIENT` | child-process programs for lifetime and admission controls | constructed input |
| `oracle_name`, `oracle` | Mach-O header and load-command reader independent of the helper under test | independent observation |
| `target_fixtures(work)` | real Mach-O fixtures linked with the selected SDK plus malformed files | constructed input needing `clang`, `lipo`, `dsymutil` |

### Inventory conventions

Identifiers `BP01` to `BP68` follow file order (execution order under
`unittest` is alphabetical). A labeled variant is written `BPnn/label`; an
unlabeled loop scenario is identified by its loop index and the values the
table names. "Recording" says how an outcome reaches the record: a plain
assertion fails the method; a `subTest` failure is recorded with its label and
the loop continues; retained artifacts are files copied into the case's
`artifacts/` directory; everything else lives in `/private/tmp` temporary
directories removed by `addCleanup`. The orderings described as sequences are
within one method and matter to the expectation.

### LockTests

`setUp`: a `pw-lock-` temporary directory under `/private/tmp` (cleanup
registered), `root = work/checkout` with `tests/`, the lock path, and
`launcher = bash tests/lib/checkout_lock.sh --root <root> --`. Helpers:
`script()` writes a child program; `admit()` runs `checkout_lock.admit` in a
child given only a claim and reports admission or refusal plus whether the
child could take the lock through a separate open; `lifetime(mode)` and
`check_lifetime()` observe a killed owner and wrapper while a grandchild runs.

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP01 | `test_unrelated_socket_cannot_handoff_a_copied_nonce_and_unheld_descriptor` | A separate process reads the public owner record, opens the lock inode and answers an admission over its own socket pair with that descriptor. Expected: child exit 0, stdout `REFUSED: the channel was not created by the acquisition owner`, lock still held. | single; independent observation by `lock_free` |
| BP02 | `test_admission_send_is_bounded_when_the_channel_queue_is_full` | In-process acquire and `bind_channel`; the datagram queue is filled until `EAGAIN`/`ENOBUFS`; `admit(timeout=0.1)` raises `Refusal` within 2 s; lock held. Sockets and descriptor closed in `finally`. | single; elapsed-time bound |
| BP03 | `test_nested_scope_cannot_admit_after_acquisition_owner_exits` | A child under the launcher takes a nested `owned` scope, signals ready, waits, then tries `admit` under its own claim. The launcher owner is killed first. Expected: lock still held by the nested scope, result `refused`, then the lock frees. `finally` releases and kills. | single |
| BP04 | `test_another_socket_from_the_owner_process_is_not_the_acquisition_channel` | A different socket pair's descriptor substituted as the channel: `Refusal` matching `does not belong to this acquisition`. | single |
| BP05 | `test_cancellation_bounds_a_command_and_descendant_that_ignore_signals` | Launcher started in-process with `GROUP_GRACE=.2`, `KILL_GRACE=2`, running a command that ignores SIGINT/SIGTERM and spawns a sleeping grandchild with inherited descriptors. For each signal: lock held, owner exits `128+signum` within 5 s, both pids gone within 5 s, lock free. | unlabeled loop over SIGINT, SIGTERM (2); `finally` SIGKILLs the pids |
| BP06 | `test_claims_are_admitted_only_by_a_live_owners_handoff` | Sequence: a valid handoff is admitted with the scope nonce; seven refused claims each leave the real hold in place (child status 2, needle present, `refused held`); after the loop the lock file inode and bytes are unchanged, in-process `acquire` and the launcher report `checkout busy`; after the scope exits both worktrees are free; an unheld descriptor claim on a free lock is refused without creating a hold (`refused free`); a nested launcher chain is admitted twice (`ok: admitted by the owner` ×2) and prints `nested`. | `subTest(claim=…)` ×7: stale claim (never passed), closed descriptors, another open on the lock inode, wrong nonce over the real channel, another worktree, another worktree asked of this owner, malformed claim without a channel |
| BP07 | `test_owner_exit_during_admission_creates_no_hold` | A fake owner acquires the lock, binds a channel, launches the admission client, prints `received` and then exits or is killed. Expected: client reports `refused: the owner of this claim is gone`, `session-start` status 2, the client could take the lock itself, lock free, no session file. | `subTest(owner=…)` ×2: exit, killed |
| BP08 | `test_protected_children_keep_the_hold_after_the_owner_dies` | `lifetime('pass')` satisfies every observation (held while running, grandchild survives the kills, hold persists, competitor refused, released after the last exit, competitor then succeeds); `lifetime('drop')` must fail that check and show no hold after the kill. Then a trapping bash command under the launcher: SIGINT and SIGTERM to the launcher yield exit 130/143, the trap word in the marker, lock free; SIGKILL leaves the lock held until the orphaned command is killed by process group. | two unlabeled lifetimes; `subTest(signal=…)` ×2: int, term; SIGKILL sequence unlabeled |
| BP09 | `test_witness_preserves_bytes_and_nested_front_end_records_its_own` | A nested launcher chain with byte-exact values (`CPATH=''`, `LIBRARY_PATH` of bytes 1–255 plus newline, `MANPATH` with a space and newline): outer witness equals the caller's values, inner records `CPATH=/inner/include`; Python-only ownership leaves a supplied `CPATH` alone. | single |
| BP10 | `test_witness_refusals_precede_lock_writes` | `checkout_lock.py --root … -- /usr/bin/true` with one witness missing, changed or malformed: exit 2, `environment witness` and the name in stderr, no lock file created. | `subTest(name=…, fault=…)` ×15 (5 names × 3 faults) |
| BP11 | `test_direct_python_children_inherit_the_callers_environment` | Under `env -i` with fixed values, a script records `env -0` before and from a child Python after. Direct pinned Python: byte-identical sets. `/usr/bin/python3` shim: sets differ (negative control). | unlabeled loop ×2 |
| BP12 | `test_forwarder_preserves_the_environment_and_a_shim_control_does_not` | A copy of `tests/fixtures/build_refusals/forward.py` with `PW_PYTHON` a symlink in a directory with spaces, run directly and through the shim; the receipt's direct environment has every witnessed name `None`, the shim's differs and sets `CPATH`. | single |
| BP13 | `test_helper_wrapper_children_inherit_the_callers_environment` | `tests/lib/python.sh` under `env -i` passes the fixed values through to a child; `/usr/bin/python3 -B` does not. | unlabeled loop ×2 |
| BP14 | `test_a_coerced_locale_is_named_as_such` | With witnesses saying unset: `LC_CTYPE=C.UTF-8` refuses naming coercion and `PYTHONCOERCECLOCALE=0 was not honored`; `en_US.UTF-8` refuses with `start through tests/lib/checkout_lock.sh` and without `coerced`. In-process via `mock.patch.dict`. | single |
| BP15 | `test_helpers_import_only_the_interpreter_and_the_tree` | From a C locale, a working directory outside the checkout and no `PYTHON*` variable: `site` not imported, every `sys.path` entry inside the interpreter prefix or the tree (the script start may also keep the script directory), `LC_CTYPE` unset. Then `PYTHONPATH` set makes the script start exit 2 with `python_environment_set` and `PYTHONPATH`. | `subTest(label)` ×3: python.sh script, inline, stdin; plus one unlabeled refusal |
| BP16 | `test_entrypoints_refuse_an_unexecutable_interpreter_before_any_python` | Under a `sandbox-exec` profile that permits only `bash` and `dirname`, each entry point with `PW_PYTHON=/usr/bin/false` exits 2 with `direct Python unavailable`, names the pinned path, never names `/usr/bin/false`, and triggers no installation request. | unlabeled loop ×4: `tests/lib/checkout_lock.sh`, `tests/run.sh`, `tests/lib/python.sh`, `tests/accept-release.sh` |

### ResolverTests

`setUp`: a `pw-resolver-` temporary directory. `resolve()` sources
`python_start.sh` in a child bash with the caller's environment minus
`PYTHON*`; `keg()` writes stand-in kegs.

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP17 | `test_the_pin_resolves_and_probes_here` | The real pin resolves and probes: exit 0, path equals the pin, version `3.14.x`, real path inside the Cellar and fully resolved. | single; depends on this machine's Homebrew keg |
| BP18 | `test_a_revision_suffixed_keg_is_accepted_with_its_upstream_version` | Keg `3.14.8_1` through an opt symlink: version `3.14.8`, real path of the stand-in. | single |
| BP19 | `test_the_path_checks_refuse_by_name_without_starting_anything` | Each stand-in path refuses with the named reason, the path (or `HEAD`) in stderr and empty stdout. | `subTest(label)` ×6: missing, a symlink escaping its keg, not executable, outside the cellar, another minor, an unversioned keg |
| BP20 | `test_python_environment_is_refused_except_the_three_the_helpers_own` | `PYTHONPATH`, `PYTHONHOME`, `PYTHONSAFEPATH`, `PYTHONWARNINGS` refuse with `python_environment_set` and the name; `PYTHONOPTIMIZE=0`, `PYTHONOPTIMIZE=''`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONCOERCECLOCALE=0` are accepted. | `subTest(name)` ×4 refused, ×4 accepted (see F3) |
| BP21 | `test_the_probe_refuses_a_stand_in_that_disagrees_or_fails` | A probe that prints `3.9.6`, prints no version, or fails: exit 2 with the named reason and the probe path. | `subTest(label)` ×3 |

### ShimContainmentTests

`setUp`: a `pw-shim-` temporary directory; when `PW_TEST_ARTIFACTS` is set, a
cleanup copies the whole work directory to `artifacts/<method name>/`. These
are the only retained artifacts of the case. `checkout()` copies fifteen real
tree files (`build.sh`, `Makefile`, `tests/run.sh`, `tests/accept-release.sh`,
`tests/suites/unit/run.sh`, five `tests/lib` shell helpers,
`checkout_lock.py`, `Info.plist`, `PolicyWitness.entitlements`, the runner
`Info.plist` and `Entitlements.plist`) into a disposable checkout.

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP22 | `test_detector_sent_blocked_and_neighbours` | `installation_requests` recognizes three phrases and ignores two neighbours; `install_denials` matches only the recorded pid. | single, pure functions |
| BP23 | `test_constructed_gate_refusals_stop_dispatch_and_prepare` | Good gate observations yield no errors; each fault yields errors, and with `execute` mocked both `prepare` and `run` raise `ContainmentError` after exactly three gate executions, writing no `invocation.json`; an empty result set is an error. | unlabeled loop: 6 faults × 2 modes = 12; fixture directories named by index |
| BP24 | `test_constructed_sysctl_gate_refusals_stop_dispatch_and_prepare` | With the fixed unreadable-arm64 rule, the sysctl observations are required; nine constructed faults (missing records, readable arm64 inside, nonzero or incomplete reads, translation inside, failed outside reads) each refuse in both modes with `execute` and `sysctl_checks` mocked; call counts (3, 1); no `invocation.json`. | unlabeled loop: 9 faults × 2 modes = 18; labels appear only in assertion messages |
| BP25 | `test_combined_profile_keeps_containment_and_reads_arm64_empty` | Real `prepare` with the rule: no errors, outside read shows `UniqueID: 0`, inside shows `eServerError`, permitted exit 0, exact sysctl tuples outside and inside (the denied arm64 read exits 0 with empty output), profile text carries the deny rules and ends with the rule; an arbitrary rule raises `ValueError` and writes no profile. | single; retained `combined/` |
| BP26 | `test_profiles_apply_and_keep_exec_restrictions` | Plain and exec-restricted profiles pass containment; `/usr/bin/true` under the restricted prefix exits 71 with `execvp()` in stderr, 0 otherwise; `exec-check.json` written. | unlabeled loop ×2 (restricted False/True); retained |
| BP27 | `test_structured_paths_cannot_add_profile_rules` | A write path containing quote and parenthesis characters appears JSON-quoted in the profile beside `(deny mach-lookup)`. | single |
| BP28 | `test_nested_sandbox_refuses_without_dispatch` | `shim_probe.py` started under an outer `sandbox-exec`: exit 2, permitted check 71 with `sandbox_apply`, marker not created, no `invocation.json`; `outer-result.json` written. | single; retained |
| BP29 | `test_entrypoints_refuse_sdk_at_admission` | Three unresolvable `SDKROOT` values × six entry points in the copied checkout under containment: exit 2, `admission: SDKROOT=<value> does not resolve`, no installation request, no downstream marker in stdout, and no `tests/.checkout.lock`, `controller/target` or `dist` created. | unlabeled loop 3 × 6 = 18; each result retained as `<i>-<j>.json` |
| BP30 | `test_valid_sdk_requests_reach_each_entrypoints_next_boundary` | Empty, `macosx` and the selected SDK path × five entries: expected exit and stdout marker (`usage:` 0, `usage:` 0, `reached` 0, empty 0, `Checking limits documentation` 2), no installation request. Uses the real `xcrun --show-sdk-path` and the real `tests/run.sh` and `tests/accept-release.sh`. | unlabeled loop 3 × 5 = 15; retained JSON |
| BP31 | `test_make_checks_command_line_and_inherited_sdk_before_recipes` | Five invalid `make` invocations (both `/usr/bin/make` and the developer directory's make, command-line and inherited `SDKROOT`, a refusal override, a shell-metacharacter value) exit 2 with `admission: SDKROOT=`, no progress line, no installation request, and the metacharacter creates no file; with `build.sh` replaced by a stub, three valid requests reach `build reached: <request>`; removing `sdk_guard.sh` makes make exit 2 before the build. | unlabeled loops 5 + 3 + 1; retained JSON |

### ProbeTests

`setUp`: a `pw-probe-` temporary directory. `timed()` wraps `prov.probe`
with a monotonic clock; `gone()` observes a recorded pid from outside with
`kill(pid, 0)` and `ps`.

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP32 | `test_cleanup_has_one_deadline_even_when_the_group_cannot_be_reaped` | With `CLEANUP_TIMEOUT=.2`, `TERM_GRACE=.05`, `group_gone` sleeping its whole allowance and `killpg` mocked: `terminate_group` returns `failed` in under 0.32 s. | single; timing bound (F5) |
| BP33 | `test_probes_are_bounded_and_failures_carry_no_output` | Sixteen sequential scenarios: nonzero exit (status, kind, code; planted canary absent from the record), empty output, missing tool, good first line, malformed version, stdout overflow from `yes` (kind, stream, cleanup, byte counts within `limit` and `3×limit`, under 5 s), stderr flood and the 8192-byte counterexample against a 64-byte cap with exit 0, both streams at 60000 bytes complete, exact limit accepted, limit+1 overflow, a 30 s sleep under a 1 s timeout, a tool trapping TERM and an orphaned pipe writer each `timeout`/`complete` within `1 + TERM_GRACE + CLEANUP_TIMEOUT + 2` s with the pid observed gone, and `required()` refusing with status 2 naming `nonzero_exit`. | one method, unlabeled scenarios; timing bounds (F5); independent process observation |
| BP34 | `test_comparison_inputs_are_complete_within_their_bounds` | Two identities equal within `LINE_LIMIT` both read as `oversized_output`; `compare_fields` on `None` reports `unavailable`; an oversized configured command is `oversized` and the compiler observation `oversized_output`; a long version line is `oversized_output`. | single (F1) |

### StampFixture and its three subclasses

`StampFixture.setUp`: a `pw-stamp-` temporary root with `controller/`;
`own()`; `session-start` with `BUILD_XPC=0` must succeed; `fake_observation()`
installed as `prov.observe_toolchain` (restored by cleanup). `configure()`
writes `build.ninja` and the introspection files; `check`, `publish` and
`extend` call `run_main`. The class itself contributes no test.

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP35 | `StampTests.test_stamp_states_are_decided_without_adopting_unknowns` | One lifecycle: unconfigured directory needs no stamp (0, `not configured`); configured without a stamp refuses (2, `has no pw-toolchain.json`, `PW_FRESH_BUILD=1`) and writes nothing; publish succeeds with scope `{'xpc': False}` and the C identity; republish refuses (`already holds`); unchanged reuse passes with identical bytes; a changed C identity refuses as changed (1) and a failed rustc observation as unavailable (2), bytes intact; a configuration the stamp does not describe refuses (2); malformed, unsupported, elsewhere and fieldless stamps each refuse without being rewritten; a stamp without a configuration is unknown (2, `no configuration`); after a Swift configuration, `extend --xpc 0` leaves the stamp intact and `extend --xpc 1` extends only the Swift fields and `output.swift_target` with `published_at` unchanged; a reuse check with Swift passes, a changed Swift identity refuses (1); an extension that would change another field refuses (`cannot be extended`) leaving bytes intact; the session carries `toolchain`. | `subTest(stamp=…)` ×4 inside the sequence: malformed, unsupported, elsewhere, fieldless |
| BP36 | `OutputTargetStampTests.test_stamps_carry_the_output_target_and_refuse_another` | The published fields carry exactly the output-target set; a schema-1 stamp refuses (`unsupported schema`, `PW_FRESH_BUILD=1`) unrewritten; a missing `output.link_arch` refuses; each changed target field refuses reuse (1, `is configured for output <field>`) before any toolchain probe (the probe recorder stays empty); a directory configured for `x86_64` arch or cpu family does not describe the stamp (2, exact message); a configuration moved to `x86_64` link arch makes `extend` refuse (2, `no longer describes the output target`) unrewritten; restored configuration passes; Swift extension records `output.swift_target`, a changed value refuses (1), a Catalyst-configured Swift target refuses extension (2); a partial reconfiguration without a Swift target still passes a full check. | `subTest(field=…)` ×5: output.cpu_family, output.system, output.c_arch, output.link_arch, output.cargo_triple |
| BP37 | `FailedObservationTests.test_failed_required_observations_refuse_compatibility_and_publication` | A failed rustc observation of each kind refuses publication (2, `required toolchain observation failed: rustc.command`) without writing a stamp; after a valid publish, a failed C observation refuses reuse naming `compilers.c.identity (output_overflow)`, an oversized configured command names `compilers.c.command (oversized_output)`, bytes intact; `prov.collect` over a session with the failed observation raises `Refusal` naming `rustc (output_overflow)`. | `subTest(publication=…)` ×3: output_overflow, oversized_output, timeout |

### FreshRemovalTests

`setUp`: a `pw-fresh-` checkout with release, debug, triple-release and
Meson directories, seven sentinel files inside and outside the removable
areas, `own()` and a successful `session-start`. `intact()` rereads every
sentinel.

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP38 | `test_fresh_removal_admits_only_owned_real_directories` | Removal replaces `builddir`, `controller/target/release` and the triple's release area, keeps the triple directory, unlinks a symlink inside without following it, leaves every sentinel, and records `removed: true` for the three roots with the triple path; a second removal records `existed: false` without error; a symlinked triple release area refuses (`… is a symlink`) before removing anything; a symlinked `controller/target/release` refuses (`the build admits only real directories`) leaving the admitted sibling; a file in place of the directory refuses (`is not a directory`); an immutable file (`chflags uchg`, cleared in `finally`) makes removal fail with status 1, `could not remove`, `fresh.failed == 'builddir'`, and stops before the next root. | single sequence |

### OwnershipAndAdmissionTests

`setUp`: a `pw-admit-` checkout with `controller/`, an `outside` tree with
sentinel files, and the session path. `outside_inventory()` snapshots the
outside tree (symlink flag and bytes); `start()` runs `session-start`.

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP39 | `test_refused_start_does_not_create_a_missing_target_directory` | Without witnesses: 2, `environment witness missing for SDKROOT`, no `controller/target`; with a `builddir` symlink to the outside tree: 2, `is a symlink`, no `controller/target`. | single |
| BP40 | `test_session_witness_refusals_preserve_the_session_and_missing_target` | For an absent and then an existing session, each witnessed name missing or changed refuses (2, name in stderr) and leaves the previous session bytes or the missing parent directory; a valid start with `--sdk-request-state set` records the exact request value including its newline. | unlabeled loop 2 × 5 × 2 = 20; assertion messages carry name and fault |
| BP41 | `test_helpers_refuse_without_ownership` | With no claim, `session-start`, `fresh-remove` and `stamp-publish` refuse (`build helpers mutate only under an owned build`) leaving session, caches and stamp untouched; under ownership the session records the scope nonce; a session with a missing, foreign or malformed nonce makes `fresh-remove` and `stamp-publish` refuse (`the session is stale`) without removing a cache or publishing; the valid neighbours succeed; after the owner's channel closes, a start refuses (`the owner of this claim is gone`). | `subTest(helper=…, claim='none')` ×3; `subTest(session=…, helper=…)` ×6 |
| BP42 | `test_cache_paths_are_admitted_before_any_write` | Each of six cache components symlinked to the outside tree refuses (`(nothing was written or removed)`) with the outside inventory unchanged and no session; `builddir` as a file, a directory at the session path, a hard-linked session file and a foreign owner uid (mocked `getuid`) each refuse with their message; a missing owned `controller/target` is created and recorded; a path replaced between admission and use refuses `state.save()` and `fresh_remove_admitted` (`was replaced after admission`), with the outside tree and the moved directory intact. | `subTest(symlink=…)` ×6; the rest sequential |

### CargoJudgmentTests

`setUp`: a `pw-cargo-` root with the triple's release area, `own()` and a
successful `session-start`. `unit()` writes an executable, its hard-linked or
copied `deps` file and a fingerprint of the requested kind; `judge()` writes
the messages file and runs `cargo-judge` with `RUSTFLAGS='-C opt-level=1'`.

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP43 | `test_cargo_judgments_bind_fingerprints_without_guessing` | Three units and a stale sibling: judgments bind by hard link (fresh false, observed, metadata hash, effective flags, source agreement) and by identical bytes (fresh true), report `unavailable` without a fingerprint, and never attribute the sibling; published paths are redacted; fresh mode refuses the reused target by name; ambiguous, malformed, unsupported and oversized fingerprints are reported as such with `None` flags and agreement; a malformed messages file refuses (2, `malformed`). | single sequence |
| BP44 | `test_fresh_judgments_are_literal_booleans_bound_to_the_admitted_executable` | For both fresh modes: valid messages judge every target `fresh: false`; thirteen mutations of one message (missing, null, numeric and string `fresh`, another or the host area's executable, missing, empty, test or string-flagged profile, a non-binary kind) refuse (2, `establishes no literal boolean fresh judgment`, the target named, judgment `unknown`); an absent, contradictory or duplicated message refuses naming the target. | outer unlabeled loop ×2; `subTest(fault=…, fresh_mode=…)` ×26; `subTest(fault=…, fresh_mode=…)` ×6 |
| BP45 | `test_requested_flags_are_attributed_by_precedence` | `CARGO_ENCODED_RUSTFLAGS` over `RUSTFLAGS` (and attribution against the encoded value alone), an empty encoded value, target rules that are unresolved under `cfg()` rules, the output triple's rules over the compiler host's, `CARGO_TARGET_*` rules, resolved triple-only rules, `build.rustflags`, `CARGO_BUILD_RUSTFLAGS` over a file, and `none`. | single sequence |

### CargoConfigurationTests

`setUp`: a `pw-cargo-config-` work tree with a Cargo home, an invocation
directory `a/b/c`, a `bin` with stand-in compilers and a minimal environment.
`write()`, `selected()` and `unresolved()` wrap `cargo_config.load` and
`selection`.

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP46 | `test_failed_launcher_observations_never_fall_back_to_standalone_cargo` | With `which` mocked, a failed launcher probe of each kind raises `Unresolved` with and without `RUSTUP_TOOLCHAIN`; a `which` that finds only cargo raises too. | `subTest(kind=…)` ×3 |
| BP47 | `test_toml_forms_discovery_and_precedence` | Inline, dotted and table forms select the same compiler; discovery from the invocation directory upward with Cargo home lowest, a deeper file winning, `config` preferred over `config.toml`, Cargo home inside the walk read once; environment precedence `RUSTC` over `CARGO_BUILD_RUSTC` over `build.rustc` with overridden sources recorded and relative paths resolved from the invocation directory; an empty `RUSTC_WRAPPER` disables a configured wrapper. | `subTest(form=…)` ×3; rest sequential |
| BP48 | `test_program_paths_resolve_as_cargo_resolves_them` | Config-relative paths resolve from the parent of `.cargo`, bare names from the child `PATH`; an absent tool, an array value, an empty `RUSTC` and a `PATH` without a compiler each raise `Unresolved` with the named reason. | single |
| BP49 | `test_includes_follow_cargo_order_and_refuse_what_cannot_be_read` | Include order and relative-path resolution, the graph order and an optional absent include; required-missing, non-TOML, malformed entry, malformed file, cycle and type-conflict includes refuse; depth, file count, file size and total size bounds refuse. | `subTest(include=…)` ×6; four unlabeled bounds |
| BP50 | `test_env_entries_apply_as_cargo_applies_them` | `[env]` entries with and without an inherited caller value (plain, forced, unforced, field-merged, relative); four malformed entry forms refuse; a forced `PATH` selects the alternate compiler and a forced deployment target that differs is a conflict while an equal one is not; the summary carries neither the unrelated value nor the replaced `PATH`, and flags the replacement. | `subTest(inherited=…)` ×2; `subTest(env=…)` ×4; rest sequential |

### OutputTripleSelectionTests and SdkTests

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP51 | `OutputTripleSelectionTests.test_the_command_line_target_overrides_lower_defaults` | `--target` overrides `CARGO_BUILD_TARGET` and `build.target`, recorded as overridden; list and absent forms; non-string targets raise `Unresolved`; the summary carries the selection only when present. | `subTest(value=…)` ×3 combined with `assertRaises` |
| BP52 | `SdkTests.test_sdk_versions_normalize_and_unknowns_never_agree` | Version normalization and `parse_build_version` over constructed `otool` text (fields, tools, problems for `n/a`, duplication, no build version, missing `LC_UUID`); a real probe compiled with `xcrun clang`, `own()` and `session-start`: `output_metadata` agrees with `xcrun --show-sdk-version`, `sdk-check` accepts the equivalent numeric form and refuses `1.2` (`built against SDK`), `n/a` (`not a numeric version`) and a source file. | single; compiles one file |

### OutputTargetTests

`setUpClass` creates a `pw-output-target-` directory and `target_fixtures()`
once for the class (four linked executables, a one-slice fat file, a Catalyst
executable, truncated, short-header, text, empty, class-file and missing
entries, an x86_64 debug executable with its dSYM, a universal debug
executable with its dSYM, and three `lipo` combinations); `tearDownClass`
removes it. `observe()` calls `output_target.observe` with the production
probe and metadata reader.

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP53 | `test_fixtures_are_what_their_bytes_say` | The oracle reads each expected fixture's container, architectures, file type 2 and platform; the x86_64 dSYM is `MH_DSYM`; the truncated copy keeps its header and loses its platform; the missing path is absent. | `subTest(fixture=…)` ×6 |
| BP54 | `test_observations_are_kept_apart_from_the_decision` | For each expected fixture the observation has no problems and matches the oracle, `target_problems` yields exactly the listed reasons, and `describe` starts with the path; each malformed fixture yields exactly its reason with architectures (or, for the truncated file, the platform) unknown. | `subTest(fixture=…)` ×12 |
| BP55 | `test_failed_and_inconsistent_tool_reports_refuse` | Seven constructed `lipo` reports leave architectures unknown and refuse; a failed metadata read yields `no readable LC_BUILD_VERSION platform`; the probe is `/usr/bin/lipo -archs <path>` with 4096-byte bounds. | `subTest(report=…)` ×7 |
| BP56 | `test_runnable_code_is_found_by_header_and_dsym_data_is_not_code` | The bundle scan finds code by header (a renamed universal file, a torn file), skips a dSYM companion by file type, reads every slice of the fat dSYM fixtures as `MH_DSYM` from their tables, keeps a mixed debug/code container and a thin x86_64 file hidden under a DWARF path as code, and raises `OSError` on an unreadable directory (`chmod 0`, restored by cleanup). | single sequence |
| BP57 | `test_malformed_fat_debug_slices_are_not_exempted` | Eleven mutations of the universal dSYM (two truncations, nine patched table or header fields) all stay in the code inventory and each refuses. | unlabeled loop ×11; assertion message names the path |
| BP58 | `test_the_build_gate_records_each_stage_and_refuses_any_departure` | Under an owned session the declared target is recorded; the cargo stage accepts the thin arm64 fixture; the native stage with the thin fixture plus each departing fixture refuses naming only the departing output and records one problem; an assembled bundle with every required output and two dSYM companions passes; a universal file under a dSYM path refuses at packaging; an absent and an empty bundle refuse with their messages; all four stages are recorded; without ownership the gate refuses (2). | `subTest(output=…)` ×8: thin-x86_64, universal, one-slice-fat, thin-arm64e, catalyst-arm64, truncated, text, missing |
| BP59 | `test_app_gates_check_required_paths_without_macho_headers_in_both_variants` | For partial (3 paths) and full (7 paths) variants and both app stages, each required path replaced by text, emptied, truncated to two magic bytes or removed refuses with `<path>: <reason>`, with the session recording every output and exactly that problem; the path is restored after each fault. | `subTest(xpc=…, stage=…, path=…, fault=…)` ×80 |
| BP60 | `test_weakened_predicates_fail_these_controls` | Four textual weakenings of `tests/lib/output_target.py` (container rule removed, predicate reduced to membership, substring name match, platform rule removed), each applied once to a copy loaded from a file: the original refuses the named fixture, the weakened copy accepts it. | `subTest(weakening=…)` ×4 |

### SignatureDisplayTests and RecordTests

`RecordTests.setUp`: a `pw-record-` temporary directory and one run of
`tests/fixtures/dispatcher/build.sh` (nine `clang` invocations, `codesign`,
`lipo`, `dsymutil`; output discarded) per method. `app()` lays out a fake
bundle with `fixture_bundle.bundle`; `problems()` returns the inspector's
`(code, path)` pairs for the bundle's manifest; `rewrite()` mutates the record
file in place; `partial()` derives the partial build's record.

| ID | Method | Exercises and expectations | Variants and recording |
| --- | --- | --- | --- |
| BP61 | `SignatureDisplayTests.test_signature_displays_establish_class_team_and_timestamp` | A valid display has no problems and is timestamped, readable and hardened; `Signed Time` yields one `no secure timestamp` problem; another team, a development chain, an Apple Development leaf, an ad hoc signature (team `None`), a missing runtime flag, a doubled display (not readable, `ambiguous`), an unsigned observation and a teamless identity each yield their named problem; the observation string carries `timestamp=secure`. | unlabeled sequence ×11 |
| BP62 | `RecordTests.test_records_are_bounded_redacted_and_complete` | Redaction of home-prefixed strings and lists and `forbidden_content` for home paths and the `PATH` value; a valid bundle has no problems; another bundle's record (same inventory, changed bytes) is refused by hash or metadata; fourteen named record mutations each produce their expected code, the record being regenerated after each; a non-object record yields exactly `[('provenance', RECORD_PATH)]`; a manifest hash that disagrees with the record is named. | `subTest(case=…)` ×14 (F2, F4) |
| BP63 | `RecordTests.test_records_are_validated_by_shape_in_every_reader` | The partial record and six optional-unknown neighbours pass the shape check; every required section missing, null and wrong-typed (21) and 45 named nested faults each fail the shape check on a fresh copy and, written to the bundle, make the inspector report `provenance`; a changed linker tool version alone passes the shape check and yields exactly `provenance_metadata`; a signature claim contradicting the display yields exactly `provenance_signature`. | `subTest(neighbour=…)` ×6; `subTest(fault=…)` ×66 |
| BP64 | `RecordTests.test_the_archive_reader_validates_the_record_and_binds_its_outputs` | ZIP archives of the partial outputs: the reader returns the record and controller hash; an oversized record is refused (`beyond … bytes`) and the inspector reports `exceeds`; a null deployment target is `invalid provenance record`; changed load commands or signature facts pass the shape check but are refused by the reader naming them; a member with changed bytes `differs from its provenance record`; a missing member is named; a one-slice fat member whose load commands and rehashed digest agree is refused on `architectures or container`; a schema-1 record is refused by shape and reader; a record missing an output's architectures is invalid. | unlabeled loop ×2 inside a sequence |
| BP65 | `RecordTests.test_the_producer_validates_before_sealing` | `prov.collect` over a constructed session and toolchain produces a record that passes the shape check with thin arm64 outputs and the declared target; seven session faults (null or disagreeing deployment target, absent requests, an odd xcode shape, a non-boolean judgment, missing or x86_64 Meson machines) raise `Refusal` with their messages; an x86_64 helper compiled over `sbpl-check` with the manifest updated is refused from its bytes. | `subTest(producer=…)` ×7; compiles one file |
| BP66 | `RecordTests.test_helper_subcommands_are_the_ones_the_script_invokes` | `docs/generate_build.py` parses `build.sh`; the helper subcommands it invokes equal `SUBCOMMANDS` minus `inspect`, which exists. | single |
| BP67 | `RecordTests.test_opt_in_mutation_anchors_match_current_sources` | `opt_in/build_refusals.py` is loaded as a module; each of its 16 `MUTATIONS` changes its named source in memory; `build.sh` contains `REQUIRE_REBUILT` once and `_without_self_checks` changes it. | `subTest(refusal=…, mutation=…)` ×16 |
| BP68 | `RecordTests.test_unknown_wrapper_hashes_never_establish_stamp_compatibility` | A missing wrapper or a wrapper without a digest compares as `unavailable`; a hashed wrapper compares equal to itself. | single |

## Flagged expectations

Flags stay here until a correction lands; the row then names the commit.
None has been reproduced as a failure.

- **F1 (BP34).** `self.assertIsNotNone(stamped)` follows
  `stamped = dict(observation=seen[0])` and cannot fail. The surrounding
  assertions still establish the oversized reading; the line asserts nothing.
- **F2 (BP62).** The fault loop rewrites the bundle's record, asserts, then
  regenerates the record inside the `subTest` block. A failed assertion leaves
  the mutated record in place and the next variant mutates a mutated record,
  so one failure can change the variants after it. The plan names this as an
  inspected risk. Regenerating in a `finally` or mutating a fresh copy per
  variant would be an isolation improvement.
- **F3 (BP20).** The accepted-variable loop uses `PYTHONOPTIMIZE` twice as a
  `subTest` label (values `0` and empty), so two variants share one identity in
  any report.
- **F4 (BP62 and the suite README).** The "another bundle" refusal accepts
  either `provenance_hash` or `provenance_metadata`; the suite README says the
  record "is refused by hash and load-command metadata". Either the assertion
  or the account should say which.
- **F5 (BP02, BP32, BP33).** Elapsed-time bounds (2 s, 0.32 s, 5 s, and
  `1 + TERM_GRACE + CLEANUP_TIMEOUT + 2` s) and the stdout overflow byte
  bound depend on host load and pipe buffering. The dispatcher records system
  sleep per invocation; a failure that overlapped sleep is not product
  evidence. These are limits of the observation, not wrong expectations.
- **F6 (BP23, BP24, BP29, BP30, BP31, BP40, BP57, BP61, BP33).** Scenario
  loops without `subTest` identify a failing scenario only through the
  assertion message or a retained file name. Outcomes of individual scenarios
  are not separable in the log.
- **F7 (BP06).** The `closed descriptors` claim assumes descriptors 250 and
  251 are closed in the child. Nothing establishes that; a child with those
  descriptors open would exercise a different refusal path.
- **F8 (BP17, BP30, BP31, BP52).** Expectations are bound to this machine's
  Homebrew keg, Xcode developer directory, selected SDK and `make`. The
  catalog declares only `clang`; the interpreter is implied by the dispatcher.
  These are environment couplings to record, not defects.
- **F9 (BP67).** The expectation depends on a module outside this suite's
  files (`opt_in/build_refusals.py`), which is why the execution reference
  below needed a reviewed exception.

## Unresolved questions for a later trial

| Question | Observation that would settle it | Work depending on the answer |
| --- | --- | --- |
| Per-method cost of `RecordTests.setUp` (one fixture-host compile per method, seven per run) and of `OutputTargetTests.setUpClass` | a trial run reporting per-test durations (pytest `--durations=0`), or timing instrumentation around the two setups | whether shared immutable preparation is worth designing before parametrizing record faults |
| Whether class order matters (alphabetical under `unittest`, file order under pytest) | a trial run in file order with every method passing, and a reverse-order run | nothing in the source shows cross-class state; a passing trial in both orders would support that |
| Whether `PYTEST_CURRENT_TEST` in the host environment reaches any environment comparison | a trial run; the source shows every byte-for-byte comparison starts from `env -i` or a constructed dictionary, and `pw_python_start` refuses only `PYTHON*` names | the integration arrangement's environment policy |
| Whether default `fd` capture changes which child output survives in the retained log | comparing `assertions.log` from a trial run with and without `-s` against the reference log | the retained-evidence shape the outer case keeps |

## Execution reference

Recorded separately from the source baseline. Facts marked measured come
from retained run files; applicability is a judgment stated as such.

| Item | Value |
| --- | --- |
| Run (measured) | `tests/out/runs/unify-review-final-20261024`, run ID `20261024T225719Z_707ed1fc`, gitignored and available only in this checkout |
| Command (measured) | the default battery (`plan.json` selection mode `default`, 196 cases); this case ran as invocation 1 under the preflight suite's catalog command with `PW_TEST_CASES=build_provenance_controls` |
| Started and finished (measured) | 2026-10-24T22:57:20Z to 2026-10-24T22:58:22Z for the case; the whole run finished 2026-10-24T23:11:36Z |
| Interpreter (measured) | `/opt/homebrew/opt/python@3.14/bin/python3.14`, real path `/opt/homebrew/Cellar/python@3.14/3.14.9/Frameworks/Python.framework/Versions/3.14/bin/python3.14`, version `3.14.9`; the same keg and version resolve at `3ec96c1` |
| Case result (measured) | `pass`, duration 61544 ms, invocation return code 0, no harness errors, `system_sleep_ms` 0 |
| Checker summary (measured) | `Ran 68 tests in 61.360s`, `OK` |
| Method count against the inventory (measured) | 68 logged `Class.method` names, identical to the 68 methods in the source inventory |
| Retained evidence (measured) | `report.json`, `events.jsonl` (start, step, end), `artifacts/assertions.log` (77 lines; 66 one-line `ok` entries, one entry split by a child's stderr, one by `Terminated: 15`), and ten `artifacts/<method>/` directories from `ShimContainmentTests` |
| Source revision (judgment) | the run receipts record no revision; `8442fca` is the last commit before the run started and `87d5fb2` the first after it finished, so the tree was `8442fca` plus any uncommitted change, which the receipts cannot exclude |

### Applicability at 3ec96c1

Traced dependencies of the executed path: the catalog entry; `tests/run.sh`,
`test_cli.py`, `suite_run.py`, `retention.py`, `artifact.py`,
`python_start.sh`, `sdk_guard.sh`, `testlib.sh`, `case.sh`; the case script;
the checker; its imports (`build_provenance`, which imports `cargo_config`,
`checkout_lock` and `output_target`; `signer_check`; `shim_probe`;
`fixture_bundle`, which imports `seal_tool`; the vendored `tomli`); the files
it reads, copies or executes (`build.sh`, `Makefile`, `tests/accept-release.sh`,
`tests/suites/unit/run.sh`, `tests/lib/python.sh`, `checkout_lock.sh`,
`Info.plist`, `PolicyWitness.entitlements`, the runner `Info.plist` and
`Entitlements.plist`, `tests/fixtures/build_refusals/forward.py`,
`docs/generate_build.py`, `tests/fixtures/dispatcher/build.sh` with its C
sources, `tests/suites/preflight/opt_in/build_refusals.py`); and the
equipment (`xcrun clang`, `lipo`, `dsymutil`, `otool`, `codesign`,
`sandbox-exec`, `make`, `xcode-select`, `chflags`, `pgrep`, `ps`).

Mechanically checked:

- `git diff --stat 8442fca HEAD` over every traced repository path reports
  changes only in `tests/catalog.json` and
  `tests/suites/preflight/opt_in/build_refusals.py`.
- The case entry in the run's `plan.json` equals the entry the current
  `--list` prints, field for field; the catalog change touched two other
  cases' descriptions.
- The 68 test names in the retained log equal the current inventory.

Reviewed exception: the `build_refusals.py` delta adds one function definition
and one entry to `SEQUENCES`. `MUTATIONS` (16 entries), `REQUIRE_REBUILT` and
`_without_self_checks`, the only names BP67 reads, are unchanged, and the
module's only top-level statement besides definitions is its `__main__` guard,
so loading the changed module executes one additional `def`. The result for
BP67 is retained on that reading.

Judgments the reader should weigh: the working tree at run time is assumed to
match `8442fca`; equipment versions at run time are not recorded apart from
the interpreter; the artifact-integrity records concern the app, which this
case does not use. No fresh run was made for this record because no named
question needed an observation the case can supply.

## Comparison rows

Later trials and migration stages append rows here. Each row names the
baseline identifier (a method or `BPnn/label` variant), the stage, the migrated
check or the unmigrated code that now carries it, one label, and the evidence
(a run path under `tests/out/runs/` or a commit). A flagged expectation keeps
its flag until the row that corrects it names the commit.

| Baseline ID | Stage | Migrated check or unmigrated code | Label | Evidence |
| --- | --- | --- | --- | --- |
