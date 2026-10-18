# Independent audit of the worker account — initial report

Audit ID: `worker-account-475ac0b`. Date: 2026-10-18. Brief:
`docs/WORKER-AUDIT-PROMPT.md`.

## 1. Context, coverage and method

### Revision and checkout

- Audited revision: `475ac0b7a284b784a4a65e5673f71c7f17941a5b` (`main`).
  No revision was named separately. The coordinator directed the audit at
  this clean checkout, so I audited HEAD.
- Starting status: `git status --short` was empty. A second worktree exists at
  `.tmp/wt-s1` (`b410ac3`, detached). It was not touched.
- Ending status: `git status --short` is still empty. No source, documentation,
  fixture or generated artifact was modified. Writes were confined to
  `.tmp/audits/worker-account-475ac0b/` (this report, map renders, console
  transcripts) and the two managed test-output directories listed below.

### Exposure to excluded or earlier material

Recorded so the reader can judge independence:

1. **Session start, before the audit.** The assistant's auto-memory index
   was loaded into context automatically. The user had asked for it to be
   ignored, and I did ignore it, but it had already been read. It contains
   one-line project notes, including that a worker documentation plan "pass
   1" finished on 2026-10-17, that two "withheld key findings" were
   "recovered as rows 15/16" awaiting adjudication, and notes about a BYOXPC
   launchd/"bad-neighbor" investigation. No finding content was present.
   - **Possible effect:** awareness that an earlier finding register exists.
   - **Possible priming:** the BYOXPC note could prime how I read the orphaned
     BYOXPC worker in WA-04. That observation was made directly and its
     origin is left unresolved (U2).
2. **Session start.** The workspace context listed five recent commit
   subjects, including "docs: state worker citation checks positively",
   "docs: show host path observations without object attribution" and
   "docs: state worker observations and resource lifetimes directly".
   - **Possible effect:** heightened attention to citation captions (WA-02)
     and resource lifetimes (WA-03, WA-04).
   - **Mitigation:** each of those findings rests on source or case-script
     content cited below, not on the subjects.
3. **Directory listings (~14:52 UTC).** These exposed names only, without
   content:
   - `docs/WORKER-INST-DOC-PLAN.md` (not opened);
   - `.tmp/plan-history-*`, `.tmp/worker-language-{resolution,sweep,triage}`,
     `.tmp/worker-pass5-round1` (not opened).
4. **Earlier launch evidence (~15:00 UTC).** Inspecting the credited launch
   observation exposed run names `tests/out/runs/worker-p1-launch{,-final}`.
   - **Read:** its execution metadata, raw observations,
     `pass1-evidence/provenance.json`, and the first ~1.2 KB of
     `pass1-evidence/source-scope.json`. That excerpt contained the sentence
     "Pass 1 working-tree observer and catalog; exact source copies retained.
     Other production sources match the committed signed build."
   - **Not read:** the key names of `pass1-evidence/manifest.json` were
     listed (one is `notes`), but its values were not read.
   - **Compared, not diffed:** retained source-snapshot files were compared
     by hash only.
   - **Possible effect:** the "pass 1" vocabulary in WA-06. That phrasing
     appears in `docs/WORKER.md` itself, so the finding does not depend on
     this exposure.
5. **Not opened at any point:** no plan file, finding register, earlier
   audit report, triage or root-cause summary, repair rationale, git log or
   git diff.

### Reading coverage

Read in full:

- `docs/WORKER.md`;
- `docs/generate_architecture.py` and `docs/generator_common.py`;
- the worker graph's clusters and edge lines in
  `docs/worker-capabilities.dot`. The node lines were read through the
  manifest instead.
- the worker graph entries in `docs/architecture.json`, read
  programmatically;
- `controller/tools/pw_probe_runner/pw_probe_runner.c`;
- `pw_extension_issuer.c`, `pw_extension_channel.h`, `pw_profile_capture.h`
  and `pw_worker_evidence.h`;
- `runner/Sources/PWRunnerCore/ExtensionIssuer.swift`;
- `runner/Sources/PWCWorkerShim/PWCWorkerShim.c`;
- `runCWorker` and its helpers (`CWorker.swift` lines 1–80 and 720–1623);
- in `CWorkerOrchestrator.swift`: `run` (lines 1–260);
- in `ValidatorClient.swift`: the driver (lines 1–300);
- in `ProbeRunner.swift`: lines 40–204;
- in `PWRunnerAPI.swift`: the run spec (lines 200–262) and test overrides
  (lines 540–631);
- `enforce_required_entitlements` (`controller/src/runner_select.rs`).

Also read: `sb_api_validator.c` `main` and its no-report calls, the start of
`attach_sandbox_logs`, the generator contracts G1–G11 in the source_drift
README, and the root, runner, controller, tests and scratch guidance.

Checks traced to their assertions:

- `runner_unit/host_setup_controls.py`;
- the `runner_c_worker_harness` README (lifecycle, file kinds, exec
  sections), the `bare_deny_default` and `exec_setup_post_apply_denied`
  assertions, and the harness's spawn code;
- the `runner_exec_inheritance` and `runner_exec_lifecycle` READMEs;
- `check_extension_boundaries.py`, and lines 1–140 of `check_extensions.py`;
- `attempt_outcome_matrix_enforced.sh`;
- the wrappers of the other cited `witness_contract` cases.

Read partially or not at all:

- **Host code:** `CWorker.swift` lines 80–720 (layout mirror, admission,
  `decodeWorkerEvidence`, `decodeProfileCapture`), and
  `CWorkerOrchestrator.swift` after line 260 (`planValidatorQueries`,
  `comparisonEvidence`, disposition).
- **Other sources:** `PWRunnerService.swift` (`enrichPathDiagnostics`),
  `MonotonicDeadline.swift` (`writePolicy`), the rest of `harness.c`, and the
  extension `control.c` beyond its includes.
- **Documents:** `ARCHITECTURE.md`, `PolicyWitness.md`, `LIMITS.md` and
  `FAILURE-PROPAGATION-CONTRACT.md` were consulted only by targeted search.
- **External references:** the linked Apple sources were not fetched.

The external-evidence rows x2 and x3, edge W53, the create-then-kill control
and the receipt contract are therefore unverified in their internals.

### Methods

1. **Read the account as a whole.** I read `WORKER.md` end to end and
   inspected the map visually. I rendered `docs/worker-capabilities.svg` with
   `rsvg-convert` and read native-scale tiles. The renders are in
   `.tmp/audits/worker-account-475ac0b/render/`.
2. **Traced claims to source in both directions.** Prose, inventory and edge
   claims went to source. Separately, I walked the lifecycle from worker
   preparation and launch through attempts, publication, release, spin and
   exit, looking for omitted branches.
3. **Classified every cited check.** For all 137 inventory rows, I judged
   whether the cited check exercises the production behaviour the row states
   (Appendix A).
4. **Tested the generator's guarantees.** These were assessed from its code,
   then by its own `--check` and an independent re-render.
5. **Ran existing checks.** I ran the existing cases where they could settle
   applicability or support. Section 2 lists them.

## 2. Checks run and evidence used

All commands ran from the repository root with `PYTHONOPTIMIZE` unset. The
checkout lock was free, and no build or test was running beforehand.

1. **Generator check.**
   - Command: `python3 docs/generate_architecture.py --check`
   - Result: `ok: architecture manifest: 5 graphs, 175 nodes, 176 edges; dot
     files, svg stamps and document regions current` (rc 0).
2. **Independent SVG render.** I ran `dot -Tsvg docs/worker-capabilities.dot`
   (Graphviz 16.1.0) and compared the output with the committed SVG minus its
   stamp line.
   - Result: byte-identical.
   - This goes beyond the generator, which checks only the stamp.
   - Graphviz warned "Unable to reclaim box space in spline routing for edge
     s26a -> s27" (W14).
3. **Launch run.** Run `20261018T150641Z_12585892`, output in
   `tests/out/runs/worker-audit-475ac0b-launch/`. Command:

   ```sh
   PW_TEST_OUT_DIR=tests/out/runs/worker-audit-475ac0b-launch \
     tests/run.sh --case runner_exec_inheritance/launch_inventory \
                  --case runner_exec_inheritance/cli
   ```

   - Result: 3/3 pass. The contaminated_worker case ran as a dependency.
4. **Combined check run.** Run `20261018T150739Z_fc07ecd7`, output in
   `tests/out/runs/worker-audit-475ac0b-checks/`. The command used the same
   form, with these cases:
   - `runner_unit/host_setup_controls`;
   - `runner_c_worker_harness/{bare_deny_default, compile_failure,
     create_allow, params_round_trip, exec_pipes_per_attempt,
     exec_setup_post_apply_denied}`;
   - `witness_contract/{extensions, extension_boundaries}`;
   - `runner_exec_lifecycle/{worker_dies_during_exec,
     closed_streams_leader_exit}`.

   Result: 11/11 pass.
5. **Console transcripts.** These are in scratch:
   `.tmp/audits/worker-account-475ac0b/launch-console.txt` and
   `checks-console.txt`. They were not attached to the runs.

### App under test

- **Bundle:** `dist/PolicyWitness.app`, build 699, `v0.3.1-15-ga9bb271-dirty`.
- **Worker identity:** `e1c88f81…d145`. This equals the generated identity at
  the audited revision. The identity covers every `.c/.h/.swift` file under
  `controller/tools/pw_probe_runner` and `runner/Sources`, plus the build
  files.
- **Binary hashes:**
  - `pw-probe-runner`: `3558b282…bf2e`
  - `PWRunner`: `ac6c272c…4959`
  - `policy-witness`: `cbb57a01…ba20`
- **Applicability:** the worker and host results apply to the audited
  sources. Because the build tree was dirty, controller-side applicability is
  not established, and no finding relies on controller behaviour from these
  runs.

### Earlier primary evidence examined

The earlier launch observation is run `20261017T215334Z_b7815087`, in
`tests/out/runs/worker-p1-launch-final/`.

- It was built as build 692 from `6fd44fb` with worker identity
  `33890392…9eb9`.
- Its retained source snapshot differs from the audited revision in
  `pw_probe_runner.c`, `pw_probe_runner_abi.h` and `CWorker.swift`. This was
  established by hash only; no content diff was read.

### Equipment and limits

- The runs were not blocked by an automation sandbox: XPC lookup, `lsof` and
  `ps -E` worked.
- `lsmp` was refused (`task_for_pid() failed`), as in the earlier run.
- No signal, rlimit or Mach-right census was possible as the current user.

## 3. Findings

Findings are ranked by consequence for the account. Each states the
demonstrated facts first, then any proposed correction separately. The
"Confidence" line says how far the support reaches.

### WA-01 — The validator receives a read/write descriptor for the worker's evidence object; the account presents the validator as touching the worker only by PID

**Account locations**

- `WORKER.md:43–44`: "Validator predictions join host evidence outside the
  worker; the host's release ordinal controls admission to attempts".
- Inventory row s1a (`:71`), "Held across" and "Reaches exec children".
- Row s1b (`:72`).
- Row x1 (`:149`), "Live worker PID query through separate validator … No
  worker-to-child transfer".
- Note x1 (`:216`), "release ordinal is separate".
- The map draws no validator-held reference.

**Demonstrated facts (source)**

1. The host clears close-on-exec on the evidence descriptor right after
   creating it, and keeps it open until `runCWorker` returns.
   - `runner/Sources/PWRunnerCore/CWorker.swift:931`:
     `_ = fcntl(shmFD, F_SETFD, 0)`.
   - `CWorker.swift:950–953`: a `defer` closes it at return.
2. The validator is launched inside the worker's polling loop, while that
   descriptor is open.
   - `CWorker.swift:1287` calls the phase hook.
   - `CWorkerOrchestrator.swift:133–157`: the hook calls `runValidator`.
3. The validator spawn uses nil attributes, so there is no
   `POSIX_SPAWN_CLOEXEC_DEFAULT`. Its only file actions are `dup2` onto fds 0
   and 1.
   - `ValidatorClient.swift:177–181` and `229–243`.
4. `sb_api_validator.c` performs no descriptor sweep. Its `main` and batch
   path contain no `close`, `dup` or `fcntl`.
5. The evidence contract says only that "All original validator pipe
   descriptors close on exec" (`tests/FAILURE-PROPAGATION-CONTRACT.md:1027`).
   Nothing documents the evidence descriptor.
6. The launch observations show the host's evidence descriptor number. In
   both the earlier run and my rerun, the worker held only fds 0–4, with
   evidence at fd 3 and no alias. So the host's evidence descriptor was fd 3
   itself (`adddup2(3,3)`, which is why the clear is needed). With an
   extension session the evidence descriptor is fd 4, because the session's
   descriptor takes fd 3; the worker's ready action then overwrites the
   alias. Either way the number survives into the validator, whose actions
   touch only fds 0 and 1.

**Reasoning**

Every eligible phase collection launches a third process. That process holds
a writable reference to the object that carries:

- the worker's release word (`proceed`) and `exit_requested`;
- the slot payloads and publications;
- the optional compiled-profile bytes.

It holds this while the worker is paused before release. The separation
between prediction and release is therefore maintained by the validator's
code, not by resource isolation.

Further consequences:

- With `_test_overrides.validator_executable_path`, an arbitrary executable
  receives the descriptor.
- A validator whose reap is unconfirmed extends the object's lifetime beyond
  what s1a states.

**Consequence for the account**

The inventory understates who holds the reporting object. The prose and the
x1 note convey a stronger separation between the prediction channel and the
release channel than the resources provide. This bears directly on the
"Predictions precede attempts" principle.

**Confidence:** high from source. Not directly observed.

**Distinguishing experiment**

1. Run one eligible `sandbox_check` step with
   `_test_overrides.validator_executable_path` pointing at an observer. The
   observer `fstat`s every open descriptor, records `F_GETPATH` and size, then
   execs the real validator. The existing path_query observer uses Python
   `subprocess`, which closes descriptors, so it cannot serve.
2. Read the result:
   - a POSIX shared-memory descriptor of 3,686,400 bytes (the region size `lsof`
     reports) confirms the finding;
   - its absence refutes it.

**Proposed corrections (separate from the facts)**

- **Account:** inventory the validator's reference under s1a/s1b and x1, or
  state that the release ordinal's separation is behavioural.
- **Implementation (for a later step):** restore close-on-exec on the host
  descriptor after the worker spawn, or spawn the validator with
  `POSIX_SPAWN_CLOEXEC_DEFAULT`.

### WA-02 — The "Cited check definitions" column overstates support: 46 of 137 rows cite no check that exercises the production behaviour stated

**Account locations**

- Inventory column "Cited check definitions" (`WORKER.md:69–212`).
- Closing line `:221`: "Every node and edge above cites at least one test or
  rule".
- Caption `:62`.

**Demonstrated facts**

The case-by-case classification is in Appendix A.

1. **Substitute host (18 rows).** These rows cite only `bare_deny_default`
   for host-side resources: s2, s3a, s3b, s4a, s4b, s14c, n6, W1–W3, W5–W10,
   W47, W48.
   - That case drives the worker from `harness.c`, not from `runCWorker`.
   - `harness.c` has its own `shm_open`, sets different pipe flags (no
     `F_SETNOSIGPIPE`, and only two ends close-on-exec) and passes `environ`,
     not nil envp (`harness.c:751`).
   - It therefore cannot exercise rows such as s4b ("`F_SETNOSIGPIPE`,
     `O_NONBLOCK`, `FD_CLOEXEC`") or n6 (Swift arrays).
2. **Rows the cited check never reaches (24).** Examples:
   - s25, W12 and W13 (parameters): `bare_deny_default` has none, while
     `params_round_trip` exists.
   - s26b (compile error): `compile_failure` exists.
   - s27, n9b, W14, W38 and W54 (capture): no capture is requested. Capture is
     exercised by `runner_abi_layout/c_swift_layout_agreement` and
     `witness_contract/max_targets_reply_survives`.
   - s30 and W40 (`open_write`): `run_effects/file_actions_have_exact_effects`
     exists.
   - s31b and W34 (creation of an absent file): they cite the existing-file
     case, while `create_allow` exercises creation.
   - s36b and W16 (process group): neither cited exec case observes the group;
     the lifecycle suite does.
   - W55 (controller log association): it cites `comparison_matrix`, which
     runs with `--no-log-capture` (`check_comparison_matrix.py:36`). Its source
     is the Swift `comparisonEvidence`, whereas association happens in Rust
     `attach_sandbox_logs`.
   - x5 (compiler receipt): `dossier_witness` never requests capture.
   - s16h, s16c, s16i and s16j (umask, limits, signal state): no check
     observes them.
3. **Static check (4 rows).** s33a, s33b, W33 and W43 (bootstrap and service
   rights) cite `attempt_outcome_matrix_enforced`. That case only verifies
   that the `AttemptOutcome` enum has rows in `tests/COVERAGE.md`; it
   performs no Mach lookup.
4. **Generator behaviour.**
   - It guarantees one test or rule per row (`require_test`,
     `generator_common.py:104`), not relevance. Its own docstring says "a
     definition is a place to look".
   - The four other graphs' captions add "whether a test asserts the row is not
     verified" (`generate_architecture.py:364–369`). The worker caption omits
     it (`:358`).
   - The caption complies with G10. The tabular presentation still pairs each
     row with "its" check.

**Consequence for the account**

A reader following a row's check finds, for about a third of the inventory,
nothing that tests the stated resource or branch. Relevant existing checks
are often left uncited. The account's own rule (`:519–521`) is "a check's
assertions establish its coverage". That rule cannot be applied from the
table.

**Confidence:** high. Every cited case's assertions were read, and six of the
better candidates were run and pass (Section 2). The category boundaries are
my judgement; partial-path cases are marked in Appendix A.

**Proposed correction**

- Cite the exercising cases listed in Appendix A.
- Mark rows that have no exercising check as source-only in the check column
  itself.
- Restore the non-verification caveat in the worker caption.
- Consider letting G5 accept an explicit "no exercising check" marker rather
  than forcing a placeholder.

### WA-03 — The exec process-lifetime Known gap names only descendants that leave the group; same-group survivors and survivors of worker death are omitted

**Account locations:** `WORKER.md:393–395` and the Known gaps list `:530`.
Line 394–395 says the worker signals the group "at the exec deadline and at
cleanup".

**Demonstrated facts**

1. The worker sends `kill(-pgid, SIGKILL)` only when the deadline expires,
   observation fails or a local timing fault occurs
   (`pw_probe_runner.c:1123–1130`).
2. Observation ends normally once the leader has exited and both output pipes
   reach EOF (`:1053`). A same-group descendant that has released the pipes is
   therefore never signalled.
3. The host terminates only the worker's PID (`ChildProcessState.terminate`).
4. Existing cases characterize both survival paths, and both passed on the
   current build in run `20261018T150739Z_fc07ecd7`:
   - `runner_exec_lifecycle/closed_streams_leader_exit` (opt-in) shows a
     same-group child alive after a cleanly completed exec step.
   - `runner_exec_lifecycle/worker_dies_during_exec` shows that worker death
     leaves live exec processes.

**Consequence for the account**

A reader of the Known gaps would conclude that staying in the child's group
guarantees cleanup. In fact sandboxed exec descendants can outlive the step,
later phases and the run in at least two further ways. Their effects can land
during later attempts.

The inventory rows s36a and s36b are accurate ("conditional group kill");
the prose gap is not.

**Confidence:** high (source plus passing characterization cases).

**Proposed correction**

Extend the Known gap to cover:

- same-group descendants after normal leader exit with released streams;
- exec processes alive at worker death or host termination.

Also make "at cleanup" read "on deadline or observation failure".

### WA-04 — The post-done spin has no worker-side bound; when the host is lost, a sandboxed worker spins indefinitely

**Account locations**

- `WORKER.md:474–477`: "Refusal can publish done and spin for exit …
  publishes done and waits for the host's exit request."
- Row s7, "Held across": "unconfirmed cleanup may outlive driver".

**Demonstrated facts**

1. Source:
   - `spin_for_exit` (`pw_probe_runner.c:1467–1476`) is an unbounded
     CPU-only loop.
   - The file header (`:37–39`) says the spin is "bounded by the host's
     grace timer".
   - Every terminal path that reaches `done` enters it: compile failure,
     parameter failure, apply failure, proceed refusal and normal completion.
2. Live observation during the audit, made with `ps` and `lsof` at 15:40 UTC:
   - **Process:** PID 61820,
     `pw-probe-runner --shm-fd 3 --ready-fd 4 --step-count 1
     --post-apply-hang-ms 15000`, from the BYOXPC staging copy
     `/private/tmp/pw-byoxpc-u41tqmph/PWRunner.xpc/…`. That directory no
     longer exists.
   - **Parent:** `launchd`.
   - **State:** started 2026-10-17 13:24:28 PDT; state `R`; 99.8 % CPU;
     562 CPU-minutes.
   - **Holdings:** evidence object `/pw_cw_61818`. Its host, PID 61818, is
     absent.
   - **Not mine:** this process predates my runs.

**Reasoning**

Once the host disappears, nothing writes `exit_requested` or delivers
SIGKILL. The worker keeps:

- its applied sandbox;
- its evidence mapping and descriptors;
- a CPU core, indefinitely.

**Consequence for the account**

The account treats host supervision as the bound and says nothing about the
loss of the host. The resource and lifetime picture is incomplete for a
failure path that demonstrably occurs.

**Confidence**

- Source: high.
- Observation: consistent with the source, but the binary is a different
  build (89,632 bytes against 89,248 for the current app). How the host was
  lost was not investigated; that belongs to the BYOXPC session's owner
  (U2).

**Proposed correction**

- **Account:** state that the worker has no self-timeout after `done`, and
  that host loss leaves it spinning. Add this to Known gaps.
- **Implementation (later step):** consider a bounded spin, or a parent-death
  check such as `getppid()` change or a kqueue `NOTE_EXIT` on the host.

### WA-05 — The credited production launch observation ("L") has no stated provenance and was recorded on a different worker build

**Account locations**

- `WORKER.md:51–53`: "L is the recorded production launch observation".
- Rows that credit L: s7, s13a–c, s14a–c, s15, s16a, s16e–g, s17, s18, s23,
  s28 and n8.
- Prose `:243–244` and `:289–292`.

**Demonstrated facts**

1. The document gives no run ID, build or revision for L.
2. The matching evidence is run `20261017T215334Z_b7815087`:
   - built from `6fd44fb` with worker identity `33890392…`;
   - the audited revision's identity is `e1c88f81…`;
   - the snapshot differs from HEAD in `pw_probe_runner.c`,
     `pw_probe_runner_abi.h` and `CWorker.swift`.
3. `launch_inventory` is opt-in (catalog `default: false`), so nothing
   re-establishes L when the worker changes.
4. My rerun against the current app reproduced the credited facts (run
   `20261018T150641Z_12585892`):
   - descriptors 0–4 only;
   - cwd `/`;
   - `/dev/null` stdout and stderr;
   - empty `ps -E` environment;
   - readiness errno 32 with a clean exit after the pre-ready hang;
   - `lsmp` refused.

**Consequence for the account**

The facts hold at this revision for that configuration: an empty
allow-default plan, held by pre-ready and post-apply sleep overrides. The
account, however, does not let a reader establish this. Its strongest live
observations carry no provenance and no rerun trigger.

**Confidence:** high.

**Proposed correction**

- Name the run, build and worker identity behind L.
- State that L uses sleep overrides.
- Make a worker-identity change trigger a `launch_inventory` rerun.

### WA-06 — The generated "Sandbox-gated" column carries audit-process history and understates or contradicts available observations

**Account locations**

Rows s9 (`:84`), s29 (`:121`), s31a (`:123`), s31b (`:124`), s32 (`:125`),
s34a–s35b (`:128–131`) and s36b (`:133`).

**Demonstrated facts**

1. **Process history in a current-behaviour document.**
   - "no live issuer case rerun in pass 1" (s9);
   - "no file probe rerun in pass 1" (s29);
   - "inspected, not rerun" (s31a, s32, s36b).

   Root `AGENTS.md` (Documentation) forbids change-history notes. These cells
   also describe an audit pass, not gating. All the named cases were rerun
   here and pass: `extensions`, `extension_boundaries`, `bare_deny_default`
   and the lifecycle cases.
2. **Gating understated.**
   - s29 says "Source-only", yet its own cited check (`bare_deny_default`)
     observes the denial of `open_read` under `(deny default)`.
   - s31b says "Source-only; open(O_CREAT) can create", yet `create_allow`
     observes creation.
3. **Inventory contradicts prose.** Rows s34a–s35b say "no deny run here".
   The prose (`:376–378`) relies on the denying case
   `exec_setup_post_apply_denied`. That default case is uncited, and it
   observes post-apply pipes and spawn handles succeeding under
   `(deny default)`.

**Consequence for the account**

The column meant to carry each gating claim's scope instead records which
tests someone did not rerun. It omits observations bearing on gating, and in
one place it disagrees with the prose.

**Confidence:** high.

**Proposed correction**

- Replace the process notes with the evidence that applies, citing the
  observing case.
- Keep "unknown" where nothing observes.

### WA-07 — The account does not state its scope relative to request-selectable test overrides

**Account locations**

- The account overall.
- Only "any selected post-phase seam" (`:476`) and the create-then-kill
  control hint at overrides.

**Demonstrated facts**

1. Public requests admit `_test_overrides` (bounded and echoed; see
   `PolicyWitness.md:808` and `:1331–1338`).
2. The overrides can:
   - replace the worker, validator and issuer executables
     (`PWRunnerAPI.swift:590–599`; `CWorkerOrchestrator.swift:84–85`);
   - inject a pre-ready sleep, a post-apply `nanosleep`, a post-apply
     self-signal or a kill-before-publish (`CWorker.swift:1107–1133`;
     `pw_probe_runner.c:1917–1941` and `:1447`).
3. The L observation itself depends on two of these overrides.

**Consequence for the account**

Inventory facts such as s7 "signed identity", s9 "ordinary signed issuer
authority", n5 argv contents and the post-apply syscall surface do not hold
under overrides. Nothing in the account bounds its claims to non-override
runs, or tells the reader that `test_overrides` and the dossier's `binaries`
fields identify such runs.

**Confidence:** high.

**Proposed correction:** add a short scope statement with a pointer to the
dossier and `test_overrides` fields.

### WA-08 — The list of paths that bypass worker token erasure is incomplete

**Account location:** `WORKER.md:429–433`.

**Demonstrated facts**

1. `prepare_extension` runs at `pw_probe_runner.c:1651`. These refusals come
   after it and return from `main` without erasing:
   - parameter count (exit 8);
   - expected length (10);
   - clock setup (12);
   - policy read failure or overflow (7);
   - length mismatch (11);
   - embedded NUL (9).
2. Any fatal termination outside a native call also skips the post-loop
   erase (`:1915`). This includes the kill-before-publish seam.
3. The listed paths are "compile/apply/parameter failures, proceed refusal,
   cancellation, interruption inside a native call".

**Consequence:** low. The host erases the same object and process exit drops
the mapping. Row s22 is hedged ("early exits differ"). The prose list,
however, reads as exhaustive.

**Confidence:** high.

**Proposed correction:** say "including" or list the header, policy and
clock refusals and fatal termination.

### WA-09 — Map and inventory slips: classification inconsistencies and two misattributed edge sources

**Demonstrated facts**

1. **Classification of core limits.** The issuer core limit (s10a) is
   "reporting", shown blue in the reporting cluster. The worker's equivalent
   intervention (s20) is "mixed".
2. **Issuer resources in the reporting cluster.** Issuer spawn handles and
   stdio (n2, n3, n4) sit in the reporting cluster although they serve the
   supplied-authority issuer. The legend (`:28`) says blue means reporting
   apparatus.
3. **W24's source.** W24 ("Host duplicates channel for worker delivery")
   cites `ExtensionSession`. The duplication is in `runCWorker`
   (`CWorker.swift:1083`).
4. **W30's source.** W30 ("Worker borrows same bytes") cites issuer `main`.
   The borrowing is in `prepare_extension`.
5. **Policy path drawing.** The policy path is drawn s4b→s23, leaving s13a
   (worker fd 0) as a dead end. The evidence path, by contrast, is drawn
   completely (s1b→s13b→s18).

**Consequence:** low. These blur which process a resource serves and where a
claim is implemented.

**Confidence:** high.

**Proposed correction:** reclassify s10a, n2, n3 and n4 consistently with
s20, and fix the W24 and W30 sources.

### WA-10 — Privacy consent mediation is not named among the ambient restrictions on worker attempts

**Account location:** `WORKER.md:267–278` ("Starting authority and ambient
context").

**Demonstrated facts**

- The user guide (`PolicyWitness.md:2181–2183`) warns that attempts in
  privacy-mediated folders "can stall on consent mediation, and such a stall
  is not a sandbox verdict".
- `WORKER.md` names only credentials, the signed image and inherited
  context.

**Consequence:** low to medium. This is a concrete non-SBPL restriction that
produces permission-shaped results or stalls. It bears on attribution, and it
is absent from the worker account.

**Confidence:** moderate. TCC behaviour for this launch chain was not
observed.

**Proposed correction:** name consent mediation as an ambient restriction,
linking the guide.

### WA-11 — `sysctl_read` success is bounded by an undisclosed 4,096-byte stack buffer

**Account location:** `WORKER.md:402–405`.

**Demonstrated facts**

- The account says the attempt "publishes call status, discarding the
  returned sysctl value".
- `attempt_sysctl_read` passes a 4,096-byte stack buffer
  (`pw_probe_runner.c:750–759`).
- By `sysctlbyname` semantics, a larger value fails with ENOMEM regardless of
  policy.
- No limits-inventory entry exists for this bound.

**Consequence:** low. A failure not caused by the policy goes unexplained.
It is not permission-shaped.

**Confidence:** high on the code. The behaviour was not observed.

## 4. Unresolved questions and missing evidence

- **U1 — validator inheritance (WA-01).** Settled by the observer experiment
  described under WA-01. A cheaper option: hold collection with a slow
  validator substitute and run `lsof -p` on it.
- **U2 — origin of the orphaned worker (WA-04).** How host 61818 was lost is
  unknown. Settling it requires that BYOXPC session's own records, which I did
  not open. **The process is still running and is not mine; its cleanup is
  the owner's decision.**
- **U3 — unobserved starting state (s16c, s16i, s16j, s16e).** Signal mask,
  ignored dispositions, rlimits and the Mach-right set remain unobserved. The
  account says so. Settled by a production-host launch through
  `worker_executable_path`, with an observer that records `sigprocmask`,
  `sigaction`, `getrlimit` and `task_get_special_port` and then execs the
  worker. This mirrors the contaminated-worker adapter, but via XPC.
- **U4 — bootstrap reference retention (s33a).** Its growth across repeated
  lookups has no right-count control. Settled by a seam-substituted worker
  build, as the extension controls already do, that publishes
  `mach_port_get_refs` before and after each lookup.
- **U5 — controller applicability.** The tested app came from a dirty
  `a9bb271` tree. Worker and host applicability rests on the matching worker
  identity; controller-side applicability (W55, x4) is not established. A
  clean build at the audited revision would settle it.
- **U6 — opt-in coverage.** `launch_inventory` and
  `closed_streams_leader_exit` are opt-in. The default battery does not
  re-establish L or the same-group survival characterization.
- **U7 — not verified here.** Linked Apple-source claims (spawn wrapper,
  `kern_exec`, `vfprintf`, `strerror`) and the internals of x2, x3 and W53.

**Additional observation (not a finding).** The evidence object has a
predictable name, `/pw_cw_<hostpid>`, created with `O_EXCL` and unlinked
immediately. A same-user process could pre-create the name, or open it
between creation and unlink. The extension channel uses a random name. This
is outside the account's stated claims; whether it matters depends on the
threat model.

## 5. Overall assessment

Within the coverage above, the account's source-level statements are largely
accurate and carefully hedged. These items were checked and hold:

- call-site placement relative to compile and apply;
- descriptor and mapping retention;
- unchecked host setup returns and their controlled effects;
- the extension preparation order, admission refusal and erasure points;
- the attempt table;
- the starting-state facts credited to L, which reproduce on the current
  build.

The generated copies are current, and the SVG body matches a fresh render.

The account's weaknesses are of three kinds:

1. **A material resource omission.** The validator holds the reporting
   object (WA-01). This weakens the stated separation between prediction and
   release.
2. **Incomplete lifetime and failure-path statements.** These cover exec
   survivors beyond the stated gap (WA-03) and the unbounded spin after host
   loss, which is observed live (WA-04).
3. **Evidentiary presentation.** Roughly a third of the rows cite checks that
   do not exercise them (WA-02). The gating column records audit history
   rather than the evidence that applies (WA-06). The key launch
   observation lacks provenance (WA-05).

The prose is more reliable than the inventory's evidence columns. A reader
can trust the "When" and "Release" facts I checked. A reader should not rely
on the per-row cited check as support without consulting Appendix A.

## Appendix A — Cited-check classification (137 rows)

Categories:

- **R:** the cited check exercises the row's production behaviour, through
  shipped binaries or production source in a control build.
- **S:** the cited check exercises a substitute host (`harness.c`).
- **U:** the cited check does not reach the row's resource or branch, or
  disables it.
- **D:** a static, non-behavioural check.

A row takes the best category among its cited checks.

| Cat. | Rows | Cited check | Existing checks that would exercise the row |
| --- | --- | --- | --- |
| S | s2, s3a, s3b, s4a, s4b, s14c, n6, W1, W2, W3, W5, W6, W7, W8, W9, W10, W47, W48 | `runner_c_worker_harness/bare_deny_default` | `runner_unit/host_setup_controls` (production `runCWorker`, endpoint identities and collisions); `runner_exec_inheritance/launch_inventory` (production descriptors); any production CLI case for s2, n6, W10, W48 |
| U | s16h, s16c, s16i, s16j | `bare_deny_default` | None observes these (the account says unknown) |
| U | s17 | `bare_deny_default` | `launch_inventory` pre-ready seam (EPIPE survival observed) |
| U | s25, W12, W13 | `bare_deny_default` | `runner_c_worker_harness/params_round_trip` |
| U | s26b | `bare_deny_default` | `runner_c_worker_harness/compile_failure` |
| U | s27, n9b, W14, W38, W54 | `bare_deny_default` | `runner_abi_layout/c_swift_layout_agreement` (capture controls); `witness_contract/max_targets_reply_survives` (live capture) |
| U | s30, W40 | `bare_deny_default` | `run_effects/file_actions_have_exact_effects` |
| U | W25 | `bare_deny_default` | `host_setup_controls` (worker_token cases); `witness_contract/extensions` |
| U | W51 | `bare_deny_default` | `witness_contract/comparison_matrix` |
| U | s36b, W16 | `exec_pipes_per_attempt`, `contaminated_worker` | `runner_exec_lifecycle` cases |
| U | s31b, W34 | `create_existing_file_preserves_contents` | `runner_c_worker_harness/create_allow` |
| U | W55 | `comparison_matrix` (runs `--no-log-capture`) | `witness_contract/worker_termination_and_log_correlation`; source should be `attach_sandbox_logs` |
| U | x5 | `dossier_witness` (no capture) | `max_targets_reply_survives` |
| D | s33a, s33b, W33, W43 | `attempt_outcome_matrix_enforced` | Live lookup status: `blackbox_e2e` bbx_002 and `runner_filter_local_name`. Retention: none (U4) |
| R | All other 91 rows | as cited | s16a is only partial: the entitlement gate is exercised by the Rust `entitlement_gate_*` tests, not by `launch_inventory` |

The six cases in the right-hand column that I ran (Section 2) all pass on the
current build:

- `params_round_trip`
- `compile_failure`
- `create_allow`
- `exec_setup_post_apply_denied`
- the two lifecycle cases

The other alternatives were not run.
