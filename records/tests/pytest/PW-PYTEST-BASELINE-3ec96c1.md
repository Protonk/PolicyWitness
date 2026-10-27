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
[the investigation plan](../../../tests/suites/preflight/PW-PYTEST-INTEGRATION-INVESTIGATION-PLAN.md)
and [the trial plan](../../../tests/suites/preflight/PW-PYTEST-TRIAL-PLAN.md).

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
| Labeled `subTest` variants | 344 | loop sizes read from source (per-method counts in the tables); the stage 0 receipt counted the same 344 |
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
| BP59 | `test_app_gates_check_required_paths_without_macho_headers_in_both_variants` | For partial (2 paths) and full (7 paths) variants and both app stages, each required path replaced by text, emptied, truncated to two magic bytes or removed refuses with `<path>: <reason>`, with the session recording every output and exactly that problem; the path is restored after each fault. | `subTest(xpc=…, stage=…, path=…, fault=…)` ×72 |
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

### Variant tables for the first refactor targets

The mutation column is the source expression applied to a copy `r` of the accepted record (BP62, BP63) or to the valid message `m` (BP44); `put(value, *keys)` assigns at the nested key path and `drop(*keys)` removes the last key. These tables are the identities a migration must preserve one for one.

**BP62 record faults.** Each variant rewrites the bundle's record file, requires the expected code among the inspector's findings, and regenerates the record afterwards (F2).

| Variant | Mutation of the record file | Expected code present |
| --- | --- | --- |
| BP62/missing entry | `r['outputs'].pop()` | `provenance_output` |
| BP62/duplicate entry | `r['outputs'].append(dict(r['outputs'][1]))` | `provenance_output` |
| BP62/invalid path | `r['outputs'][1].__setitem__('rel_path', '../escape')` | `provenance_output` |
| BP62/absolute path | `r['outputs'][1].__setitem__('rel_path', '/Contents/MacOS/x')` | `provenance_output` |
| BP62/unshipped executable | `r['outputs'].append(dict(r['outputs'][1], rel_path='Contents/MacOS/extra'))` | `provenance_output` |
| BP62/controller hash inside the seal | `r['outputs'][0].__setitem__('sha256', 'a' * 64)` | `provenance_hash` |
| BP62/wrong hash | `r['outputs'][1].__setitem__('sha256', 'b' * 64)` | `provenance_hash` |
| BP62/wrong uuid | `r['outputs'][1].__setitem__('uuid', 'FFFFFFFF-0000-0000-0000-000000000000')` | `provenance_metadata` |
| BP62/wrong sdk | `r['outputs'][1].__setitem__('sdk', '1.0')` | `provenance_metadata` |
| BP62/missing section | `r.pop('toolchain')` | `provenance` |
| BP62/other schema | `r.__setitem__('schema_version', prov.SCHEMA_VERSION + 1)` | `provenance` |
| BP62/an earlier build's schema | `r.__setitem__('schema_version', 1)` | `provenance` |
| BP62/wrong architectures | `r['outputs'][1].__setitem__('architectures', ['x86_64'])` | `provenance_metadata` |
| BP62/wrong container | `r['outputs'][1].__setitem__('container', 'fat')` | `provenance_metadata` |

**BP63 accepted neighbours.** Each is applied to a fresh copy and must leave the shape check with no problems. The partial build's record is the seventh accepted input.

| Variant | Mutation |
| --- | --- |
| BP63/xcode unknown | `r['toolchain'].__setitem__('xcode', dict(status='unknown', reason='nonzero_exit', returncode=1))` |
| BP63/meson options unknown | `r['configuration'].__setitem__('meson_options', dict(status='unknown'))` |
| BP63/stamp projection unavailable | `r['configuration']['toolchain_stamp'].__setitem__('projection', dict(status='unavailable', reason='x'))` |
| BP63/fingerprint ambiguous | `r['outputs'][0]['cargo'].__setitem__('fingerprint', dict(status='ambiguous', binding=None, limitation='x'))` |
| BP63/wrapper without a hash | `r['toolchain']['rustc'].__setitem__('wrappers', dict(wrapper=dict(source='RUSTC_WRAPPER', command='/w')))` |
| BP63/explicitly empty SDK request | `r['configuration']['requests'].__setitem__('SDKROOT', dict(state='set', value=''))` |

**BP63 section faults.** For each of the seven sections `generated_at`, `source`, `toolchain`, `configuration`, `outputs`, `signing` and `limits`, three variants: `<section> missing` (`drop(section)`), `<section> null` (`put(None, section)`) and `<section> wrong type` (`put(7, section)`). That is 21 variants with the same expectation as the named faults below.

**BP63 named faults.** Every variant is applied to a fresh copy; the shape check must report a problem, and once the copy is written to the bundle the inspector must report `provenance`.

| Variant | Mutation |
| --- | --- |
| BP63/dirty is a string | `put('no', 'source', 'dirty')` |
| BP63/an input hash missing | `drop('source', 'input_hashes', 'meson.build')` |
| BP63/worker identity not hex | `put('z' * 64, 'source', 'worker_identity')` |
| BP63/SDK version null | `put(None, 'toolchain', 'sdk', 'version')` |
| BP63/C compiler observation failed | `put(dict(status='failed', kind='timeout'), 'toolchain', 'compilers', 'c', 'observed')` |
| BP63/Swift compiler missing in a full build | `put(dict(status='not applicable', reason='partial build: the XPC pieces were not compiled'), 'toolchain', 'compilers', 'swift')` |
| BP63/rustc selection missing | `drop('toolchain', 'rustc', 'selection')` |
| BP63/rustc source unknown | `put('guess', 'toolchain', 'rustc', 'source')` |
| BP63/xcode status unknown kind | `put(dict(status='maybe'), 'toolchain', 'xcode')` |
| BP63/knob is an integer | `put(1, 'configuration', 'knobs', 'BUILD_XPC')` |
| BP63/deployment target null | `put(None, 'configuration', 'deployment_target')` |
| BP63/deployment target disagrees with the outputs | `put('1.0', 'configuration', 'deployment_target')` |
| BP63/sdkroot disagrees with the SDK | `put('/other/SDK', 'configuration', 'sdkroot')` |
| BP63/request state unknown | `put(dict(state='maybe'), 'configuration', 'requests', 'SDKROOT')` |
| BP63/request missing | `drop('configuration', 'requests', 'CPATH')` |
| BP63/set SDK request without value | `put(dict(state='set'), 'configuration', 'requests', 'SDKROOT')` |
| BP63/private request leaks its value | `put(dict(state='set', value='/private/includes'), 'configuration', 'requests', 'CPATH')` |
| BP63/SDK source contradicts request | `put('SDKROOT named by the caller', 'toolchain', 'sdk', 'source')` |
| BP63/empty stamp projection | `put({}, 'configuration', 'toolchain_stamp', 'projection')` |
| BP63/wrong replacement type | `put('garbage', 'configuration', 'build_directories', 'fresh_mode', 'replacement')` |
| BP63/absent replacement observation | `put(None, 'configuration', 'build_directories', 'fresh_mode', 'replacement')` |
| BP63/fresh mode knob disagrees | `put('0', 'configuration', 'knobs', 'PW_FRESH_BUILD')` |
| BP63/fresh mode reused a target | `r['outputs'][0]['cargo'].__setitem__('fresh', True)` |
| BP63/Meson xpc is a string | `put(dict(status='ok', values=dict(xpc='not-a-boolean')), 'configuration', 'meson_options')` |
| BP63/empty Cargo profile | `r['outputs'][0]['cargo'].__setitem__('profile', {})` |
| BP63/an output field null | `r['outputs'][1].__setitem__('uuid', None)` |
| BP63/an output tools list of strings | `r['outputs'][1].__setitem__('tools', ['ld'])` |
| BP63/a Cargo judgment null | `next((o for o in r['outputs'] if 'cargo' in o))['cargo'].__setitem__('fresh', None)` |
| BP63/a signature timestamp string | `r['outputs'][1]['signature'].__setitem__('timestamp', 'true')` |
| BP63/signing nested disagrees | `r['signing']['nested'][0].__setitem__('timestamp', True)` |
| BP63/an unknown top-level field | `put('x', 'extra')` |
| BP63/a partial knob with full outputs | `put('0', 'configuration', 'knobs', 'BUILD_XPC')` |
| BP63/a string beyond its bound | `put('x' * (prov.LINE_LIMIT + 1), 'toolchain', 'rustc', 'identity')` |
| BP63/output target missing | `drop('configuration', 'output_target')` |
| BP63/output target of another architecture | `put('x86_64', 'configuration', 'output_target', 'architecture')` |
| BP63/output target of another triple | `put('x86_64-apple-darwin', 'configuration', 'output_target', 'cargo_triple')` |
| BP63/Meson machines missing | `drop('configuration', 'meson_machines')` |
| BP63/Meson host of another architecture | `put(dict(system='darwin', cpu_family='x86_64'), 'configuration', 'meson_machines', 'host')` |
| BP63/Cargo target selection missing | `drop('toolchain', 'rustc', 'selection', 'target')` |
| BP63/Cargo target of another triple | `put('x86_64-apple-darwin', 'toolchain', 'rustc', 'selection', 'target', 'triple')` |
| BP63/the triple's release area missing | `drop('configuration', 'build_directories', 'cargo_target_release')` |
| BP63/an output architecture missing | `r['outputs'][1].pop('architectures')` |
| BP63/an output of another architecture | `r['outputs'][1].__setitem__('architectures', ['x86_64'])` |
| BP63/a universal output | `r['outputs'][1].update(architectures=['arm64', 'x86_64'], container='fat')` |
| BP63/an output of another platform | `r['outputs'][1].__setitem__('platform', '6')` |

**BP44 judgment faults.** Each mutation is applied to the `sbpl-check` message only, for fresh modes `0` and `1`; expected: status 2, `establishes no literal boolean fresh judgment` and `sbpl-check (` in stderr, and that judgment's status `unknown`. Three further variants per mode replace the message list: `absent` (the message omitted), `contradictory` (a duplicate with `fresh=True`) and `duplicated` (an identical duplicate); each expects status 2 and `sbpl-check (`.

| Variant | Mutation of the message |
| --- | --- |
| BP44/missing | `without(m, 'fresh')` |
| BP44/null | `dict(m, fresh=None)` |
| BP44/numeric zero | `dict(m, fresh=0)` |
| BP44/numeric one | `dict(m, fresh=1)` |
| BP44/string false | `dict(m, fresh='false')` |
| BP44/string true | `dict(m, fresh='true')` |
| BP44/another executable | `dict(m, executable=str(self.release / 'elsewhere'))` |
| BP44/the host release area's executable | `dict(m, executable=str(self.target / 'release' / m['target']['name']))` |
| BP44/no profile | `without(m, 'profile')` |
| BP44/empty profile | `dict(m, profile={})` |
| BP44/test profile | `dict(m, profile=dict(m['profile'], test=True))` |
| BP44/profile flag string | `dict(m, profile=dict(m['profile'], debug_assertions='false'))` |
| BP44/not a binary | `dict(m, target=dict(m['target'], kind=['lib']))` |

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
  files (`opt_in/build_refusals.py`). That dependency is why the earlier
  battery run below could be credited only through a reviewed exception before
  the fresh reference replaced it.

## Unresolved questions for a later trial

| Question | Observation that would settle it | Work depending on the answer |
| --- | --- | --- |
| Per-method cost of `RecordTests.setUp` (one fixture-host compile per method, seven per run) and of `OutputTargetTests.setUpClass` | a trial run reporting per-test durations (pytest `--durations=0`), or timing instrumentation around the two setups | whether shared immutable preparation is worth designing before parametrizing record faults |
| Whether class order matters (alphabetical under `unittest`, file order under pytest) | a trial run in file order with every method passing, and a reverse-order run | nothing in the source shows cross-class state; a passing trial in both orders would support that |
| Whether `PYTEST_CURRENT_TEST` in the host environment reaches any environment comparison | a trial run; the source shows every byte-for-byte comparison starts from `env -i` or a constructed dictionary, and `pw_python_start` refuses only `PYTHON*` names | the integration arrangement's environment policy |
| Whether default `fd` capture changes which child output survives in the retained log | comparing `assertions.log` from a trial run with and without `-s` against the reference log | the retained-evidence shape the outer case keeps |

## Execution reference

Two runs are recorded. The first is the reference a trial compares against:
it ran at a clean committed source whose traced dependencies are byte-identical
to `3ec96c1`, with the equipment recorded beside it. The second is the earlier
battery run first considered; its executed source cannot be established from
its receipts, so it stays as illustrative evidence only. Facts marked measured
come from retained run files; applicability is a judgment stated as such.

### Reference run at c700b87

| Item | Value |
| --- | --- |
| Run (measured) | `tests/out/runs/pytest-baseline-reference-20261027`, run ID `20261027T134544Z_9ea781a5`, gitignored and available only in this checkout |
| Source (measured) | `c700b8741f69e1062f9f78f05f41b7b4bc2d922a` with a clean working tree at launch, recorded in the run's `console.log` header by the same shell immediately before the command; the two commits after `3ec96c1` touch only `records/` and the plan, and `git diff --stat 3ec96c1 c700b87` over every traced dependency path is empty |
| Command (measured) | `tests/run.sh --case preflight/build_provenance_controls --case source_drift/runner_source_manifests_agree`, `PW_TEST_OUT_DIR=tests/out/runs/pytest-baseline-reference-20261027`, `PYTHONOPTIMIZE` unset; the drift case was selected to check the plan edit in the same run |
| Started and finished (measured) | 2026-10-27T13:45:44Z to 2026-10-27T13:46:59Z for the case; the run finished 2026-10-27T13:50:24Z |
| Interpreter (measured) | the pinned path, real path `/opt/homebrew/Cellar/python@3.14/3.14.9/Frameworks/Python.framework/Versions/3.14/bin/python3.14`, version `3.14.9`, identical in the dispatcher's configuration and the case report |
| Equipment (measured, transcript header) | macOS 26.7.1 build 25G241 on arm64, not translated; Xcode 27.1 build 27A9275 at `/Applications/Xcode.app/Contents/Developer`; Apple clang 21.0.0 (clang-2100.3.34.2); macOS SDK 27.0; dsymutil Apple LLVM 21.0.0; GNU Make 3.81 at both paths the controls use; Meson 1.12.1; Ninja 1.13.2 |
| Case result (measured) | `pass`, duration 74682 ms, invocation return code 0, no harness errors, `system_sleep_ms` 0, idle-sleep assertion held |
| Checker summary (measured) | `Ran 68 tests in 74.461s`, `OK` |
| Method count against the inventory (measured) | 68 logged `Class.method` names, identical to the 68 methods in the source inventory |
| Retained evidence (measured) | `report.json`, `events.jsonl` (start, step, end), `artifacts/assertions.log` (77 lines; 66 one-line `ok` entries, one split by a child's stderr, one by `Terminated: 15`), ten `artifacts/<method>/` directories from `ShimContainmentTests`, and `console.log` at the run root, attached under the checkout lock after the run ID in `owner.json` and `run.json` was verified |

Applicability at `3ec96c1` (judgment): the executed source is established by
the commit hash and the clean-tree observation, the traced dependency paths
are unchanged between the two commits, and the equipment is recorded. What
this run does not establish: per-method timing, the behavior of any pytest
host, or anything about variants beyond the method names, because the log
names methods only.

### Earlier battery run, illustrative only

Run `tests/out/runs/unify-review-final-20261024`, run ID
`20261024T225719Z_707ed1fc`: the case passed in 61544 ms on the same keg and
version, its log lists the same 68 names, and its evidence has the same shape.
Its receipts record no source revision. `8442fca` is the last commit before it
started and `87d5fb2` the first after it finished, which brackets but does not
establish the executed tree, and its equipment versions were not recorded.
Among the traced paths, only `tests/catalog.json` (two other cases'
descriptions; this case's entry is field for field identical to the current
plan) and `tests/suites/preflight/opt_in/build_refusals.py` (one added function
and one `SEQUENCES` entry; `MUTATIONS`, `REQUIRE_REBUILT` and
`_without_self_checks` unchanged) changed between `8442fca` and `3ec96c1`. It
is kept as a second observation of the same outcome, not as the reference.

## Comparison rows

Later trials and migration stages append rows here. Each row names the
baseline identifier (a method or `BPnn/label` variant), the stage, the migrated
check or the unmigrated code that now carries it, one label, and the evidence
(a run path under `tests/out/runs/` or a commit). A flagged expectation keeps
its flag until the row that corrects it names the commit.

| Baseline ID | Stage | Migrated check or unmigrated code | Label | Evidence |
| --- | --- | --- | --- | --- |
| BP01 | 0 | unmigrated `LockTests.test_unrelated_socket_cannot_handoff_a_copied_nonce_and_unheld_descriptor` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP02 | 0 | unmigrated `LockTests.test_admission_send_is_bounded_when_the_channel_queue_is_full` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP03 | 0 | unmigrated `LockTests.test_nested_scope_cannot_admit_after_acquisition_owner_exits` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP04 | 0 | unmigrated `LockTests.test_another_socket_from_the_owner_process_is_not_the_acquisition_channel` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP05 | 0 | unmigrated `LockTests.test_cancellation_bounds_a_command_and_descendant_that_ignore_signals` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP06 | 0 | unmigrated `LockTests.test_claims_are_admitted_only_by_a_live_owners_handoff` under the pytest host; 7 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP07 | 0 | unmigrated `LockTests.test_owner_exit_during_admission_creates_no_hold` under the pytest host; 2 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP08 | 0 | unmigrated `LockTests.test_protected_children_keep_the_hold_after_the_owner_dies` under the pytest host; 2 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP09 | 0 | unmigrated `LockTests.test_witness_preserves_bytes_and_nested_front_end_records_its_own` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP10 | 0 | unmigrated `LockTests.test_witness_refusals_precede_lock_writes` under the pytest host; 15 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP11 | 0 | unmigrated `LockTests.test_direct_python_children_inherit_the_callers_environment` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP12 | 0 | unmigrated `LockTests.test_forwarder_preserves_the_environment_and_a_shim_control_does_not` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP13 | 0 | unmigrated `LockTests.test_helper_wrapper_children_inherit_the_callers_environment` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP14 | 0 | unmigrated `LockTests.test_a_coerced_locale_is_named_as_such` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP15 | 0 | unmigrated `LockTests.test_helpers_import_only_the_interpreter_and_the_tree` under the pytest host; 3 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP16 | 0 | unmigrated `LockTests.test_entrypoints_refuse_an_unexecutable_interpreter_before_any_python` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP17 | 0 | unmigrated `ResolverTests.test_the_pin_resolves_and_probes_here` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP18 | 0 | unmigrated `ResolverTests.test_a_revision_suffixed_keg_is_accepted_with_its_upstream_version` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP19 | 0 | unmigrated `ResolverTests.test_the_path_checks_refuse_by_name_without_starting_anything` under the pytest host; 6 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP20 | 0 | unmigrated `ResolverTests.test_python_environment_is_refused_except_the_three_the_helpers_own` under the pytest host; 8 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP21 | 0 | unmigrated `ResolverTests.test_the_probe_refuses_a_stand_in_that_disagrees_or_fails` under the pytest host; 3 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP22 | 0 | unmigrated `ShimContainmentTests.test_detector_sent_blocked_and_neighbours` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP23 | 0 | unmigrated `ShimContainmentTests.test_constructed_gate_refusals_stop_dispatch_and_prepare` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP24 | 0 | unmigrated `ShimContainmentTests.test_constructed_sysctl_gate_refusals_stop_dispatch_and_prepare` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP25 | 0 | unmigrated `ShimContainmentTests.test_combined_profile_keeps_containment_and_reads_arm64_empty` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP26 | 0 | unmigrated `ShimContainmentTests.test_profiles_apply_and_keep_exec_restrictions` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP27 | 0 | unmigrated `ShimContainmentTests.test_structured_paths_cannot_add_profile_rules` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP28 | 0 | unmigrated `ShimContainmentTests.test_nested_sandbox_refuses_without_dispatch` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP29 | 0 | unmigrated `ShimContainmentTests.test_entrypoints_refuse_sdk_at_admission` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP30 | 0 | unmigrated `ShimContainmentTests.test_valid_sdk_requests_reach_each_entrypoints_next_boundary` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP31 | 0 | unmigrated `ShimContainmentTests.test_make_checks_command_line_and_inherited_sdk_before_recipes` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP32 | 0 | unmigrated `ProbeTests.test_cleanup_has_one_deadline_even_when_the_group_cannot_be_reaped` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP33 | 0 | unmigrated `ProbeTests.test_probes_are_bounded_and_failures_carry_no_output` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP34 | 0 | unmigrated `ProbeTests.test_comparison_inputs_are_complete_within_their_bounds` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP35 | 0 | unmigrated `StampTests.test_stamp_states_are_decided_without_adopting_unknowns` under the pytest host; 4 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP36 | 0 | unmigrated `OutputTargetStampTests.test_stamps_carry_the_output_target_and_refuse_another` under the pytest host; 5 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP37 | 0 | unmigrated `FailedObservationTests.test_failed_required_observations_refuse_compatibility_and_publication` under the pytest host; 3 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP38 | 0 | unmigrated `FreshRemovalTests.test_fresh_removal_admits_only_owned_real_directories` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP39 | 0 | unmigrated `OwnershipAndAdmissionTests.test_refused_start_does_not_create_a_missing_target_directory` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP40 | 0 | unmigrated `OwnershipAndAdmissionTests.test_session_witness_refusals_preserve_the_session_and_missing_target` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP41 | 0 | unmigrated `OwnershipAndAdmissionTests.test_helpers_refuse_without_ownership` under the pytest host; 9 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP42 | 0 | unmigrated `OwnershipAndAdmissionTests.test_cache_paths_are_admitted_before_any_write` under the pytest host; 6 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP43 | 0 | unmigrated `CargoJudgmentTests.test_cargo_judgments_bind_fingerprints_without_guessing` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP44 | 0 | unmigrated `CargoJudgmentTests.test_fresh_judgments_are_literal_booleans_bound_to_the_admitted_executable` under the pytest host; 32 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP45 | 0 | unmigrated `CargoJudgmentTests.test_requested_flags_are_attributed_by_precedence` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP46 | 0 | unmigrated `CargoConfigurationTests.test_failed_launcher_observations_never_fall_back_to_standalone_cargo` under the pytest host; 3 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP47 | 0 | unmigrated `CargoConfigurationTests.test_toml_forms_discovery_and_precedence` under the pytest host; 3 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP48 | 0 | unmigrated `CargoConfigurationTests.test_program_paths_resolve_as_cargo_resolves_them` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP49 | 0 | unmigrated `CargoConfigurationTests.test_includes_follow_cargo_order_and_refuse_what_cannot_be_read` under the pytest host; 6 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP50 | 0 | unmigrated `CargoConfigurationTests.test_env_entries_apply_as_cargo_applies_them` under the pytest host; 6 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP51 | 0 | unmigrated `OutputTripleSelectionTests.test_the_command_line_target_overrides_lower_defaults` under the pytest host; 3 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP52 | 0 | unmigrated `SdkTests.test_sdk_versions_normalize_and_unknowns_never_agree` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP53 | 0 | unmigrated `OutputTargetTests.test_fixtures_are_what_their_bytes_say` under the pytest host; 6 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP54 | 0 | unmigrated `OutputTargetTests.test_observations_are_kept_apart_from_the_decision` under the pytest host; 12 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP55 | 0 | unmigrated `OutputTargetTests.test_failed_and_inconsistent_tool_reports_refuse` under the pytest host; 7 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP56 | 0 | unmigrated `OutputTargetTests.test_runnable_code_is_found_by_header_and_dsym_data_is_not_code` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP57 | 0 | unmigrated `OutputTargetTests.test_malformed_fat_debug_slices_are_not_exempted` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP58 | 0 | unmigrated `OutputTargetTests.test_the_build_gate_records_each_stage_and_refuses_any_departure` under the pytest host; 8 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP59 | 0 | unmigrated `OutputTargetTests.test_app_gates_check_required_paths_without_macho_headers_in_both_variants` under the pytest host; 72 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP60 | 0 | unmigrated `OutputTargetTests.test_weakened_predicates_fail_these_controls` under the pytest host; 4 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP61 | 0 | unmigrated `SignatureDisplayTests.test_signature_displays_establish_class_team_and_timestamp` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP62 | 0 | unmigrated `RecordTests.test_records_are_bounded_redacted_and_complete` under the pytest host; 14 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP63 | 0 | unmigrated `RecordTests.test_records_are_validated_by_shape_in_every_reader` under the pytest host; 72 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP64 | 0 | unmigrated `RecordTests.test_the_archive_reader_validates_the_record_and_binds_its_outputs` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP65 | 0 | unmigrated `RecordTests.test_the_producer_validates_before_sealing` under the pytest host; 7 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP66 | 0 | unmigrated `RecordTests.test_helper_subcommands_are_the_ones_the_script_invokes` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP67 | 0 | unmigrated `RecordTests.test_opt_in_mutation_anchors_match_current_sources` under the pytest host; 16 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |
| BP68 | 0 | unmigrated `RecordTests.test_unknown_wrapper_hashes_never_establish_stamp_compatibility` under the pytest host; 0 subtest reports | preserved | `tests/out/runs/pytest-stage0-01` |

### Stage 0 measures

Run `20261027T160122Z_4423b81a` in `tests/out/runs/pytest-stage0-01` (gitignored,
local) ran the unchanged checker under the pytest host with the whole
`source_drift` and `dispatcher` suites, 16 cases, all passed, no harness error,
no system sleep. The receipt holds 68 collected items with one passed setup,
call and teardown report each and 344 passed subtest reports; the per-method
subtest counts equal the variant counts in the tables above.

| Measure | Value |
| --- | --- |
| Case duration, `report.json` | 73065 ms (reference 74682 ms) |
| Sum of item durations in the receipt | 72.6 s; the rest is the launcher, collection and pytest |
| `RecordTests` call durations | bounded, redacted and complete 7.3 s; validated by shape in every reader 16.6 s; archive reader 1.2 s; producer 2.0 s; helper subcommands 0.6 s; opt-in anchors 0.5 s; unknown wrapper hashes 0.5 s |
| First `OutputTargetTests` item, setup phase | 0.53 s, the class fixture's linking of the target fixtures |

The `RecordTests` figures hold `setUp`, the body and the cleanups together, so
they bound the fixture-host compile from above; stage 1 isolates it.

| BP01 | 1 | `LockTests.test_unrelated_socket_cannot_handoff_a_copied_nonce_and_unheld_descriptor` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP02 | 1 | `LockTests.test_admission_send_is_bounded_when_the_channel_queue_is_full` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP03 | 1 | `LockTests.test_nested_scope_cannot_admit_after_acquisition_owner_exits` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP04 | 1 | `LockTests.test_another_socket_from_the_owner_process_is_not_the_acquisition_channel` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP05 | 1 | `LockTests.test_cancellation_bounds_a_command_and_descendant_that_ignore_signals` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP06 | 1 | `LockTests.test_claims_are_admitted_only_by_a_live_owners_handoff` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP07 | 1 | `LockTests.test_owner_exit_during_admission_creates_no_hold` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP08 | 1 | `LockTests.test_protected_children_keep_the_hold_after_the_owner_dies` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP09 | 1 | `LockTests.test_witness_preserves_bytes_and_nested_front_end_records_its_own` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP10 | 1 | `LockTests.test_witness_refusals_precede_lock_writes` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP11 | 1 | `LockTests.test_direct_python_children_inherit_the_callers_environment` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP12 | 1 | `LockTests.test_forwarder_preserves_the_environment_and_a_shim_control_does_not` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP13 | 1 | `LockTests.test_helper_wrapper_children_inherit_the_callers_environment` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP14 | 1 | `LockTests.test_a_coerced_locale_is_named_as_such` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP15 | 1 | `LockTests.test_helpers_import_only_the_interpreter_and_the_tree` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP16 | 1 | `LockTests.test_entrypoints_refuse_an_unexecutable_interpreter_before_any_python` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP17 | 1 | `ResolverTests.test_the_pin_resolves_and_probes_here` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP18 | 1 | `ResolverTests.test_a_revision_suffixed_keg_is_accepted_with_its_upstream_version` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP19 | 1 | `ResolverTests.test_the_path_checks_refuse_by_name_without_starting_anything` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP20 | 1 | `ResolverTests.test_python_environment_is_refused_except_the_three_the_helpers_own` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP21 | 1 | `ResolverTests.test_the_probe_refuses_a_stand_in_that_disagrees_or_fails` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP22 | 1 | `ShimContainmentTests.test_detector_sent_blocked_and_neighbours` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP23 | 1 | `ShimContainmentTests.test_constructed_gate_refusals_stop_dispatch_and_prepare` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP24 | 1 | `ShimContainmentTests.test_constructed_sysctl_gate_refusals_stop_dispatch_and_prepare` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP25 | 1 | `ShimContainmentTests.test_combined_profile_keeps_containment_and_reads_arm64_empty` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP26 | 1 | `ShimContainmentTests.test_profiles_apply_and_keep_exec_restrictions` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP27 | 1 | `ShimContainmentTests.test_structured_paths_cannot_add_profile_rules` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP28 | 1 | `ShimContainmentTests.test_nested_sandbox_refuses_without_dispatch` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP29 | 1 | `ShimContainmentTests.test_entrypoints_refuse_sdk_at_admission` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP30 | 1 | `ShimContainmentTests.test_valid_sdk_requests_reach_each_entrypoints_next_boundary` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP31 | 1 | `ShimContainmentTests.test_make_checks_command_line_and_inherited_sdk_before_recipes` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP32 | 1 | `ProbeTests.test_cleanup_has_one_deadline_even_when_the_group_cannot_be_reaped` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP33 | 1 | `ProbeTests.test_probes_are_bounded_and_failures_carry_no_output` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP34 | 1 | `ProbeTests.test_comparison_inputs_are_complete_within_their_bounds` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP35 | 1 | `StampTests.test_stamp_states_are_decided_without_adopting_unknowns` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP36 | 1 | `OutputTargetStampTests.test_stamps_carry_the_output_target_and_refuse_another` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP37 | 1 | `FailedObservationTests.test_failed_required_observations_refuse_compatibility_and_publication` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP38 | 1 | `FreshRemovalTests.test_fresh_removal_admits_only_owned_real_directories` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP39 | 1 | `OwnershipAndAdmissionTests.test_refused_start_does_not_create_a_missing_target_directory` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP40 | 1 | `OwnershipAndAdmissionTests.test_session_witness_refusals_preserve_the_session_and_missing_target` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP41 | 1 | `OwnershipAndAdmissionTests.test_helpers_refuse_without_ownership` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP42 | 1 | `OwnershipAndAdmissionTests.test_cache_paths_are_admitted_before_any_write` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP43 | 1 | `CargoJudgmentTests.test_cargo_judgments_bind_fingerprints_without_guessing` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP44 | 1 | `CargoJudgmentTests.test_fresh_judgments_are_literal_booleans_bound_to_the_admitted_executable` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP45 | 1 | `CargoJudgmentTests.test_requested_flags_are_attributed_by_precedence` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP46 | 1 | `CargoConfigurationTests.test_failed_launcher_observations_never_fall_back_to_standalone_cargo` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP47 | 1 | `CargoConfigurationTests.test_toml_forms_discovery_and_precedence` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP48 | 1 | `CargoConfigurationTests.test_program_paths_resolve_as_cargo_resolves_them` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP49 | 1 | `CargoConfigurationTests.test_includes_follow_cargo_order_and_refuse_what_cannot_be_read` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP50 | 1 | `CargoConfigurationTests.test_env_entries_apply_as_cargo_applies_them` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP51 | 1 | `OutputTripleSelectionTests.test_the_command_line_target_overrides_lower_defaults` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP52 | 1 | `SdkTests.test_sdk_versions_normalize_and_unknowns_never_agree` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP53 | 1 | `OutputTargetTests.test_fixtures_are_what_their_bytes_say` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP54 | 1 | `OutputTargetTests.test_observations_are_kept_apart_from_the_decision` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP55 | 1 | `OutputTargetTests.test_failed_and_inconsistent_tool_reports_refuse` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP56 | 1 | `OutputTargetTests.test_runnable_code_is_found_by_header_and_dsym_data_is_not_code` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP57 | 1 | `OutputTargetTests.test_malformed_fat_debug_slices_are_not_exempted` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP58 | 1 | `OutputTargetTests.test_the_build_gate_records_each_stage_and_refuses_any_departure` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP59 | 1 | `OutputTargetTests.test_app_gates_check_required_paths_without_macho_headers_in_both_variants` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP60 | 1 | `OutputTargetTests.test_weakened_predicates_fail_these_controls` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP61 | 1 | `SignatureDisplayTests.test_signature_displays_establish_class_team_and_timestamp` unchanged; its directory and lock ownership now come from the `work` and `owner` fixtures (an autouse fixture on the class) | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62 | 1 | `TestRecords.test_records_are_bounded_and_redacted` carries the part of the sequence it is named for | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62 | 1 | `TestRecords.test_a_record_for_another_bundle_with_the_same_inventory_is_refused` carries the part of the sequence it is named for | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62 | 1 | `TestRecords.test_a_non_object_record_and_a_disagreeing_manifest_are_named` carries the part of the sequence it is named for | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/missing entry | 1 | `TestRecords.test_record_faults_are_named[missing entry]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/duplicate entry | 1 | `TestRecords.test_record_faults_are_named[duplicate entry]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/invalid path | 1 | `TestRecords.test_record_faults_are_named[invalid path]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/absolute path | 1 | `TestRecords.test_record_faults_are_named[absolute path]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/unshipped executable | 1 | `TestRecords.test_record_faults_are_named[unshipped executable]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/controller hash inside the seal | 1 | `TestRecords.test_record_faults_are_named[controller hash inside the seal]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/wrong hash | 1 | `TestRecords.test_record_faults_are_named[wrong hash]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/wrong uuid | 1 | `TestRecords.test_record_faults_are_named[wrong uuid]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/wrong sdk | 1 | `TestRecords.test_record_faults_are_named[wrong sdk]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/missing section | 1 | `TestRecords.test_record_faults_are_named[missing section]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/other schema | 1 | `TestRecords.test_record_faults_are_named[other schema]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/an earlier build's schema | 1 | `TestRecords.test_record_faults_are_named[an earlier build's schema]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/wrong architectures | 1 | `TestRecords.test_record_faults_are_named[wrong architectures]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP62/wrong container | 1 | `TestRecords.test_record_faults_are_named[wrong container]`, on its own copy of the accepted bundle; the regeneration step is gone | isolation-improved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63 | 1 | `TestRecords.test_the_partial_record_passes_the_shape_check` | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/xcode unknown | 1 | `TestRecords.test_accepted_neighbours_pass_the_shape_check[xcode unknown]` | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/meson options unknown | 1 | `TestRecords.test_accepted_neighbours_pass_the_shape_check[meson options unknown]` | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/stamp projection unavailable | 1 | `TestRecords.test_accepted_neighbours_pass_the_shape_check[stamp projection unavailable]` | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/fingerprint ambiguous | 1 | `TestRecords.test_accepted_neighbours_pass_the_shape_check[fingerprint ambiguous]` | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/wrapper without a hash | 1 | `TestRecords.test_accepted_neighbours_pass_the_shape_check[wrapper without a hash]` | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/explicitly empty SDK request | 1 | `TestRecords.test_accepted_neighbours_pass_the_shape_check[explicitly empty SDK request]` | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/generated_at missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[generated_at missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/generated_at null | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[generated_at null]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/generated_at wrong type | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[generated_at wrong type]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/source missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[source missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/source null | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[source null]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/source wrong type | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[source wrong type]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/toolchain missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[toolchain missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/toolchain null | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[toolchain null]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/toolchain wrong type | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[toolchain wrong type]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/configuration missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[configuration missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/configuration null | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[configuration null]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/configuration wrong type | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[configuration wrong type]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/outputs missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[outputs missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/outputs null | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[outputs null]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/outputs wrong type | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[outputs wrong type]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/signing missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[signing missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/signing null | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[signing null]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/signing wrong type | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[signing wrong type]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/limits missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[limits missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/limits null | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[limits null]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/limits wrong type | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[limits wrong type]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/dirty is a string | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[dirty is a string]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/an input hash missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[an input hash missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/worker identity not hex | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[worker identity not hex]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/SDK version null | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[SDK version null]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/C compiler observation failed | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[C compiler observation failed]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/Swift compiler missing in a full build | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[Swift compiler missing in a full build]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/rustc selection missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[rustc selection missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/rustc source unknown | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[rustc source unknown]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/xcode status unknown kind | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[xcode status unknown kind]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/knob is an integer | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[knob is an integer]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/deployment target null | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[deployment target null]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/deployment target disagrees with the outputs | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[deployment target disagrees with the outputs]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/sdkroot disagrees with the SDK | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[sdkroot disagrees with the SDK]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/request state unknown | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[request state unknown]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/request missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[request missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/set SDK request without value | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[set SDK request without value]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/private request leaks its value | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[private request leaks its value]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/SDK source contradicts request | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[SDK source contradicts request]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/empty stamp projection | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[empty stamp projection]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/wrong replacement type | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[wrong replacement type]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/absent replacement observation | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[absent replacement observation]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/fresh mode knob disagrees | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[fresh mode knob disagrees]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/fresh mode reused a target | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[fresh mode reused a target]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/Meson xpc is a string | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[Meson xpc is a string]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/empty Cargo profile | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[empty Cargo profile]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/an output field null | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[an output field null]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/an output tools list of strings | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[an output tools list of strings]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/a Cargo judgment null | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[a Cargo judgment null]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/a signature timestamp string | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[a signature timestamp string]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/signing nested disagrees | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[signing nested disagrees]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/an unknown top-level field | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[an unknown top-level field]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/a partial knob with full outputs | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[a partial knob with full outputs]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/a string beyond its bound | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[a string beyond its bound]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/output target missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[output target missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/output target of another architecture | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[output target of another architecture]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/output target of another triple | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[output target of another triple]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/Meson machines missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[Meson machines missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/Meson host of another architecture | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[Meson host of another architecture]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/Cargo target selection missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[Cargo target selection missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/Cargo target of another triple | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[Cargo target of another triple]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/the triple's release area missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[the triple's release area missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/an output architecture missing | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[an output architecture missing]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/an output of another architecture | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[an output of another architecture]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/a universal output | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[a universal output]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63/an output of another platform | 1 | `TestRecords.test_shape_faults_are_refused_by_the_shape_check_and_the_inspector[an output of another platform]`, each on a fresh copy of the record and its own bundle copy | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63 | 1 | `TestRecords.test_a_changed_linker_tool_version_alone_is_a_metadata_finding` carries the sequence's tail | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP63 | 1 | `TestRecords.test_a_signature_claim_the_display_contradicts_is_named` carries the sequence's tail | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP64 | 1 | `TestRecords.test_the_archive_reader_validates_the_record_and_binds_its_outputs` on a copy of the accepted bundle | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP65 | 1 | `TestRecords.test_the_producer_validates_before_sealing` on a copy of the accepted bundle; its seven producer variants are `subtests` reports | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP66 | 1 | `TestRecords.test_helper_subcommands_are_the_ones_the_script_invokes` on a copy of the accepted bundle | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP67 | 1 | `TestRecords.test_opt_in_mutation_anchors_match_current_sources` on a copy of the accepted bundle; its sixteen anchors are `subtests` reports | preserved | `tests/out/runs/pytest-stage1-smoke-01` |
| BP68 | 1 | `TestRecords.test_unknown_wrapper_hashes_never_establish_stamp_compatibility` on a copy of the accepted bundle | preserved | `tests/out/runs/pytest-stage1-smoke-01` |

### Stage 1 measures and decision

Run `tests/out/runs/pytest-stage1-smoke-01` (gitignored, local) ran the stage 1
checker with the `markdown_reader` drift case: both passed, no harness error, no
sleep. The receipt holds 158 collected items with one passed setup, call and
teardown report each and 258 passed subtest reports (344 less the 86 `BP62`
and `BP63` variants that became items).

| Measure | Value |
| --- | --- |
| Case duration, `report.json` | 65520 ms (stage 0 73065 ms, reference 74682 ms) |
| Fixture host compile and accepted bundle, isolated | 0.94 s, the setup phase of the first `TestRecords` item that requests the module fixtures |
| `TestRecords`, all phases | 21.0 s, against 28.7 s of `RecordTests` call phases at stage 0 |
| Record-fault variants | 14 calls, 0.18 s mean; shape-fault variants 66 calls, 0.21 s mean |
| Checker lines | +350 and −279 against stage 0, net +71 (3046 lines) |
| Organizational lines removed from the checker | 95: 57 temporary-directory, cleanup and ownership boilerplate, 33 scenario-loop and `subTest` lines, 3 regeneration lines, 2 entry-point lines; the other 184 removed lines are assertions and sequences rewritten one for one |
| Lines stage 0 added outside the controls | about 426: the launcher 250, the drift check 70 outside its tests, the fixture installer 5, the case and suite scripts 9, the catalog 6, documentation 86; the controls add 609 more, counted separately |

Judged against the decision criteria:

1. **Net machinery: not met.** Stage 1 removed 95 organizational lines and
   left the checker 71 lines longer; stage 0 added about 426 lines the
   checker's maintainers must understand. The plan's rule for this outcome
   is to reject and revert.
2. **Identity and preservation: met.** Every method and variant has a row,
   each labeled preserved or isolation-improved; the 14 record-fault variants
   are isolation-improved; no row is blocked.
3. **Maintenance surface: met.** The launcher, its rules and the vendored set
   did not change for stage 1; only the drift allowlist named the checker.
4. **Cost: met.** The case shortened by 7.5 s against stage 0 and 9.2 s
   against the reference, with the host compile isolated at 0.94 s.

Decision: reject, and revert stage 1 and then stage 0 by the plan's procedure.
The flagged expectations F1 to F4 are then corrected in `unittest` form as
separate changes.

| BP01 | closing | `LockTests.test_unrelated_socket_cannot_handoff_a_copied_nonce_and_unheld_descriptor` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP02 | closing | `LockTests.test_admission_send_is_bounded_when_the_channel_queue_is_full` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP03 | closing | `LockTests.test_nested_scope_cannot_admit_after_acquisition_owner_exits` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP04 | closing | `LockTests.test_another_socket_from_the_owner_process_is_not_the_acquisition_channel` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP05 | closing | `LockTests.test_cancellation_bounds_a_command_and_descendant_that_ignore_signals` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP06 | closing | `LockTests.test_claims_are_admitted_only_by_a_live_owners_handoff` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP07 | closing | `LockTests.test_owner_exit_during_admission_creates_no_hold` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP08 | closing | `LockTests.test_protected_children_keep_the_hold_after_the_owner_dies` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP09 | closing | `LockTests.test_witness_preserves_bytes_and_nested_front_end_records_its_own` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP10 | closing | `LockTests.test_witness_refusals_precede_lock_writes` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP11 | closing | `LockTests.test_direct_python_children_inherit_the_callers_environment` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP12 | closing | `LockTests.test_forwarder_preserves_the_environment_and_a_shim_control_does_not` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP13 | closing | `LockTests.test_helper_wrapper_children_inherit_the_callers_environment` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP14 | closing | `LockTests.test_a_coerced_locale_is_named_as_such` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP15 | closing | `LockTests.test_helpers_import_only_the_interpreter_and_the_tree` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP16 | closing | `LockTests.test_entrypoints_refuse_an_unexecutable_interpreter_before_any_python` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP17 | closing | `ResolverTests.test_the_pin_resolves_and_probes_here` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP18 | closing | `ResolverTests.test_a_revision_suffixed_keg_is_accepted_with_its_upstream_version` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP19 | closing | `ResolverTests.test_the_path_checks_refuse_by_name_without_starting_anything` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP20 | closing | `ResolverTests.test_python_environment_is_refused_except_the_three_the_helpers_own` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP21 | closing | `ResolverTests.test_the_probe_refuses_a_stand_in_that_disagrees_or_fails` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP22 | closing | `ShimContainmentTests.test_detector_sent_blocked_and_neighbours` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP23 | closing | `ShimContainmentTests.test_constructed_gate_refusals_stop_dispatch_and_prepare` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP24 | closing | `ShimContainmentTests.test_constructed_sysctl_gate_refusals_stop_dispatch_and_prepare` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP25 | closing | `ShimContainmentTests.test_combined_profile_keeps_containment_and_reads_arm64_empty` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP26 | closing | `ShimContainmentTests.test_profiles_apply_and_keep_exec_restrictions` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP27 | closing | `ShimContainmentTests.test_structured_paths_cannot_add_profile_rules` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP28 | closing | `ShimContainmentTests.test_nested_sandbox_refuses_without_dispatch` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP29 | closing | `ShimContainmentTests.test_entrypoints_refuse_sdk_at_admission` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP30 | closing | `ShimContainmentTests.test_valid_sdk_requests_reach_each_entrypoints_next_boundary` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP31 | closing | `ShimContainmentTests.test_make_checks_command_line_and_inherited_sdk_before_recipes` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP32 | closing | `ProbeTests.test_cleanup_has_one_deadline_even_when_the_group_cannot_be_reaped` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP33 | closing | `ProbeTests.test_probes_are_bounded_and_failures_carry_no_output` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP34 | closing | `ProbeTests.test_comparison_inputs_are_complete_within_their_bounds` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP35 | closing | `StampTests.test_stamp_states_are_decided_without_adopting_unknowns` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP36 | closing | `OutputTargetStampTests.test_stamps_carry_the_output_target_and_refuse_another` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP37 | closing | `FailedObservationTests.test_failed_required_observations_refuse_compatibility_and_publication` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP38 | closing | `FreshRemovalTests.test_fresh_removal_admits_only_owned_real_directories` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP39 | closing | `OwnershipAndAdmissionTests.test_refused_start_does_not_create_a_missing_target_directory` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP40 | closing | `OwnershipAndAdmissionTests.test_session_witness_refusals_preserve_the_session_and_missing_target` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP41 | closing | `OwnershipAndAdmissionTests.test_helpers_refuse_without_ownership` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP42 | closing | `OwnershipAndAdmissionTests.test_cache_paths_are_admitted_before_any_write` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP43 | closing | `CargoJudgmentTests.test_cargo_judgments_bind_fingerprints_without_guessing` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP44 | closing | `CargoJudgmentTests.test_fresh_judgments_are_literal_booleans_bound_to_the_admitted_executable` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP45 | closing | `CargoJudgmentTests.test_requested_flags_are_attributed_by_precedence` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP46 | closing | `CargoConfigurationTests.test_failed_launcher_observations_never_fall_back_to_standalone_cargo` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP47 | closing | `CargoConfigurationTests.test_toml_forms_discovery_and_precedence` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP48 | closing | `CargoConfigurationTests.test_program_paths_resolve_as_cargo_resolves_them` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP49 | closing | `CargoConfigurationTests.test_includes_follow_cargo_order_and_refuse_what_cannot_be_read` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP50 | closing | `CargoConfigurationTests.test_env_entries_apply_as_cargo_applies_them` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP51 | closing | `OutputTripleSelectionTests.test_the_command_line_target_overrides_lower_defaults` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP52 | closing | `SdkTests.test_sdk_versions_normalize_and_unknowns_never_agree` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP53 | closing | `OutputTargetTests.test_fixtures_are_what_their_bytes_say` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP54 | closing | `OutputTargetTests.test_observations_are_kept_apart_from_the_decision` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP55 | closing | `OutputTargetTests.test_failed_and_inconsistent_tool_reports_refuse` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP56 | closing | `OutputTargetTests.test_runnable_code_is_found_by_header_and_dsym_data_is_not_code` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP57 | closing | `OutputTargetTests.test_malformed_fat_debug_slices_are_not_exempted` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP58 | closing | `OutputTargetTests.test_the_build_gate_records_each_stage_and_refuses_any_departure` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP59 | closing | `OutputTargetTests.test_app_gates_check_required_paths_without_macho_headers_in_both_variants` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP60 | closing | `OutputTargetTests.test_weakened_predicates_fail_these_controls` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP61 | closing | `SignatureDisplayTests.test_signature_displays_establish_class_team_and_timestamp` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP62 | closing | `RecordTests.test_records_are_bounded_redacted_and_complete` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP63 | closing | `RecordTests.test_records_are_validated_by_shape_in_every_reader` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP64 | closing | `RecordTests.test_the_archive_reader_validates_the_record_and_binds_its_outputs` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP65 | closing | `RecordTests.test_the_producer_validates_before_sealing` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP66 | closing | `RecordTests.test_helper_subcommands_are_the_ones_the_script_invokes` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP67 | closing | `RecordTests.test_opt_in_mutation_anchors_match_current_sources` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |
| BP68 | closing | `RecordTests.test_unknown_wrapper_hashes_never_establish_stamp_compatibility` in the restored `unittest` checker, every variant as before | preserved | `tests/out/runs/pytest-trial-closing-01` |

### Closing

The trial was rejected at the end of stage 1 on criterion 1. Stage 1 and
stage 0 were reverted in that order, each by reverting its own commit, with
this record kept. Run `20261027T161845Z_320a8829` in
`tests/out/runs/pytest-trial-closing-01` (gitignored, local) then ran the
restored case with the whole `source_drift` and `dispatcher` suites: 15 cases,
all passed, no harness error, no system sleep; the checker reported `Ran 68
tests`, `OK` in 71.2 s, the case took 71425 ms, and the 68 logged names equal
the inventory. The tree outside `records/` is byte for byte the pre-trial
state. The flagged expectations are corrected next, in `unittest` form, as a
separate change.
