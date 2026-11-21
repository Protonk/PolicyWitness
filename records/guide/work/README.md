# Basis and leads for the trust findings

This directory supports findings 4–9 of "What work can the user trust PW to
do?" in `records/guide/REQUIREMENTS-AND-EXPECTATIONS.md`. It gives the basis
for each finding, the retained specimens and replies, and the matters the work
turned up that need a decision or further checking. `scope/` does the same
for findings 2–8 of "How much of my real problem has to come into the
specimen?". Under [records/AGENTS.md](../../AGENTS.md), only the user guide
plan may link here.

## Conditions

- Written on 2026-11-20 against `main` at `b33c530b`. Ten Sonnet subagents each
  traced one ordinary use from the guide into source and tests, and ran the
  app. The main session checked the replies each finding relies on and
  reproduced finding 9 itself. Each entry below says which facts an explorer
  reported and the main session did not check.
- App: `dist/PolicyWitness.app`, built from `e7937ecc` (build 1634, contract
  `development:089e36a6b9f5327f9579b1ab165a5fe51e27e875d8ff32e74bbdf7f419c00d55`),
  on macOS build 25G241. Product sources are unchanged from `e7937ecc` to
  `b33c530b`. Every run used the built-in runner; no external runner was
  installed.
- No registered test case ran. Every run was a direct `policy-witness run` or
  `sbpl-check` invocation.
- The runs worked in a session scratch directory under `/private/tmp`, which
  does not survive a reboot. The copies in `evidence/` are the retained form.
  Absolute paths inside them refer to that scratch directory. The target
  files, links and imported profile the runs used were not retained; each
  entry says how they were set up. The specimens carry this build's contract.
  To rerun one, replace the contract and paths as the guide's quick start
  does.
- Line numbers are approximate and are those of `e7937ecc`.

## Basis by finding

### 4. Bare `(deny default)`

- `evidence/deny-default/deny.json` applies a bare `(version 1) (deny
  default)` with five steps:
  - `open_read` and `access` of a file the explorer created;
  - a `mach_lookup` of `com.apple.cfprefsd.xpc.daemon`;
  - a `sysctl` read of `hw.ncpu`;
  - an `open_read` paired with a `file-write-data` query.
- The reply (checked):
  - `finished`, with `sandboxed_after_apply: true`.
  - Every attempt is a worker result: EPERM, or `kr=1100` for the lookup.
  - The four queried steps are `query_first`.
  - The sysctl query is `prediction_unavailable`, an excluded pair.
- The lookup names `com.apple.cfprefsd.xpc.daemon`, which is a launchd job
  label, not a Mach service name; the service names are
  `com.apple.cfprefsd.daemon` and `.agent`. Under the bare policy the result
  is the same.
- Control (main session; output not retained):
  - `sandbox-exec -p '(version 1)(deny default)' /bin/cat FILE` exits 71 with
    `execvp() of '/bin/cat' failed: Operation not permitted`.
  - Adding `(allow process-exec)(allow file-read* (subpath "/usr/lib") (subpath "/System"))`
    still exits 134.
  - Adding exec of `/bin/cat` and a read of the file still exits 134. Adding
    `(allow file-read-data (literal "/"))` as well lets `cat` start. It reads
    the file and then fails with `cat: stdout: Operation not permitted`, exit
    1. The scope explorer found the same two rules enough to start
    `/bin/sleep` and a compiled probe. Under the bare policy, PW's worker
    reported the read of `/` denied
    (`scope/evidence/policy-comparison/pw/rootY.result.json`).
- Source (explorer's citation): the worker compiles the policy and signals
  ready before `sandbox_apply`, in `controller/tools/pw_probe_runner/pw_probe_runner.c`
  around lines 1570–1665.
- Tests:
  - `runner_apply_isolation_v2` adds `(allow syscall-unix) (allow syscall-mach) (allow file-test-existence)`.
    Its comment says the worker needs those rules to write its report, but the
    bare run worked without them.
  - `smoke`'s deny case uses `(allow default)`.

### 5. Extension delivery

- `evidence/extension-delivery/` holds the specimen of teaching finding 3:
  - An unapplied, unentitled `issuer`, plus `Alice` and `Bob` under one policy.
  - Phases: both readers read, the issuer issues and transfers, the recipient
    consumes, both read again, the recipient releases.
  - `ab_Alice.json` delivers to Alice and `ab_Bob.json` to Bob. The explorer
    created the target file, which was not retained.
- The replies (checked):
  - Both `finished`.
  - Each transfer is `delivered`, `equality: equal`, with both
    acknowledgements.
  - Before consumption, both reads fail with EPERM. Afterwards only the
    recipient's read succeeds.
  - The reply's token fields are `token_ref`, `token_length` and
    `token_index`; no token bytes appear.
- Explorer only:
  - `shasum` of both packaged workers matched `equipment_bindings`.
  - Actor PIDs were distinct, and each `sandbox_check.pid` equalled its actor's
    launch PID.
  - `ps` found no actor afterwards.
- Source (explorer's citation): transfer records are in
  `runner/Sources/PWRunnerCore/ActorOrchestration.swift` around 462–493.
  Issue and token erasure are in `pw_probe_runner.c` around 832–875.
- Tests:
  - `witness_contract/check_extensions.py` takes `delivered`, `equal` and the
    acknowledgements from the reply. Its independent fact is the later read's
    content against the harness's own stat; nothing compares the delivered
    bytes.
  - `sandbox_extensions_native` does not launch PW. Its native supervisor,
    issuer and consumer are the do-it-yourself version of this finding.

### 6. Re-planning per phase

- `evidence/phases/`:
  - Policy `(allow default)(deny file-read-data (literal T))`, with `T`
    absent at the start. `T` was `/private/tmp/pwB.0821ex/t` and was not
    retained.
  - Six steps: `create_fresh`, `read_fresh`, `unlink`, `read_fresh`,
    `create_fresh`, `read_fresh`.
  - `spec_phases.json` puts one action in each phase; `spec_single.json` is one
    `probe_plan`.
- The replies (checked):
  - Phased: reads 1 and 3 are `deny` and `query_first`, with EPERM. The
    unlink is `allow` and `query_first`. Read 2 is unavailable and returns
    ENOENT. Both creates are unavailable.
  - Single plan: all six steps are `prediction_unavailable` and
    `unestablished`.
  - Each run reports one worker PID. Nothing outside PW observed that worker.
- Source (explorer's citation): per-phase planning is in `CWorkerOrchestrator.swift`
  around 129–146 and `CWorkerRequestPlanning.swift` around 319–353.
- Tests: `witness_contract/check_phases.py` (`phases`, `recreation`) and
  `check_ordering.py` cover both forms. The harness creates the fixtures and
  stats them itself.
- This is close to teaching finding 2 and trust finding 1. It differs in
  being the re-planning PW does for the user.

### 7. Admission before execution

- `evidence/admission/`: two-step creates under `(allow default)`, each with a
  defect only in step 2.

  | Specimen | Defect in step 2 |
  | --- | --- |
  | `ok` | none |
  | `badlast` | `args: []` on a file attempt |
  | `longlast` | a 605-byte target |
  | `foreign` | another contract string |
  | `rt` | a target in a missing directory |

- The replies (checked):
  - `badlast`: `bad_request`, exit 1, `inapplicable_field` at
    `probe_plan.1.attempt.args`.
  - `longlast`: `bad_request` with `admission_refused`. `admission_failure`
    reports `actual` 605, `maximum` 511, unit `utf8_bytes`, origin
    `runner_host`.
  - `foreign`: `unsupported_contract` at `["contract"]`, with
    `expected_contract` naming the installed build.
  - Neither refused run has a step or a worker record. Only `ok`'s two files
    exist.
  - `rt` is `finished`: step 1 `ok`, step 2 `open_failed` with errno 2.
- Explorer only: a duplicate step ID and an unknown field (not retained) are
  also refused with no file produced. `ps` found no worker after the refusals.
- Source (explorer's citation): `admitSpecimen` in `ProbeRunner.swift` around
  202. The controller's checks are in `run_flow.rs` around 607–690 and
  `request_patch.rs` around 75–100.
- Tests: in `runner_outcome_bad_request/contract.py` the ordinary-form refusals
  are mostly single-step. Only `actor_empty_step_id` puts an effect step
  before a later defect. No test checks for an absent process independently.

### 8. Object identity from the descriptor

- `evidence/object-identity/`: the explorer created `d/real` (`hello\n`),
  `d/link`, a symlink to it, and `d/hl`, a hard link. None were retained.
  - `a.json`: `open_read` through the link, `open_read` of `/etc/hosts`,
    `read_fresh` through the link, and `open_read` of a missing name.
  - `b.json`: four phases on `d/f`: `read_fresh`, `unlink`, `create_fresh`,
    `read_fresh`.
  - `c.json`: `open_read` through the hard link and of `real`; `create_fresh`
    and `create` on the existing `real`; `open_read` of the directory.
- The replies:
  - `b` (checked): the first read reports inode 305548368. The
    `create_fresh` `written_stat` and the second read report 305548372.
  - Explorer only: `stat` gave 368 before the run and 372 after. In `a`,
    `read_fresh` through the link reported the target's inode, not the
    link's. In `c`, `create_fresh` on the existing file failed with errno 17
    while `create` returned `ok` and left the contents unchanged.
    `observed_path` follows the name used, so the hard link and `real` report
    different paths for one inode.
- Source (explorer's citations), all in `pw_probe_runner.c`:
  - `read_fresh` `fstat`: around 959–985.
  - Write stats: around 1000–1020.
  - `observed_path` through `F_GETPATH`: around 412–437.
  - `O_EXCL` create: around 1031–1058.
- Tests: `check_max_target_reply.py` compares the reported identity with the
  harness's `Path.stat()` taken after the run, which can agree only for
  unchanged files. No case compares identities across a replacement.

### 9. Helper deadline

- `evidence/helper-deadline/`:
  - `hang.sh` runs `/bin/sleep 41`.
  - `hang-deny.json` uses `(deny default)` with `exec_baseline`.
  - `hang-allow.json` uses `(allow default)`.
  - The main session ran both.
- Both runs took about 10.2 s and exited 0 with `finished`.
- Deny run:
  - `attempt.outcome` is `exec_failed` with `attempt.errno` 1.
  - The error reads `exec observation=exec child deadline errno=0; group_cleanup_errno=1; reaped=0 reap_errno=0`.
  - Both `cleanup.group_request` and `leader_fallback` show rc -1, errno 1.
  - `reap.stop_reason` is `group_request_failed`.
  - The comparison says `succeeded`, with basis `spawned_child`.
  - `ps` after return showed `hang.sh` (PID 21240, PPID 1) and its `sleep`
    (21250) alive at about 10 s and 20 s. They were gone once the sleep ended.
- Allow run: `child_term_signal` 9, `group_request` rc 0, `reap.stop_reason`
  `reaped`, and no survivor.
- An explorer reproduced the deny result with `sleep 300` and killed the
  survivors by hand.
- Source (explorer's citation): group kill and leader fallback are in
  `controller/tools/pw_probe_runner/pw_worker_exec.h` around 408–445, and the
  reap around 447–480.
- Tests: `runner_exec_lifecycle` uses `(allow default)`, so no case refuses
  the kill.

## Matters to look into

1. **A sandboxed helper can outlive its specimen** when the policy refuses the
   worker's signal (finding 9). The reply reports the failed cleanup, but the
   run is `finished` with exit 0. Whether the product should change is the
   maintainer's decision: for example, cleanup from the unsandboxed host, or
   an augment rule.
2. **`attempt.errno` reports the cleanup's EPERM** beside `exec_failed`, while
   the comparison says `succeeded`. A reader could take it for a
   permission-shaped spawn failure. Check it against the attribution rule.
3. **`sbpl-check --request` ignores `policy.augments` without notice.**
   `evidence/sbpl-check-augments/request.json` carries `exec_baseline`. The
   helper's `policy_sha256` (`60b4f729…`) equals the run's `original_sha256`,
   not its `applied_sha256` (`40af9edd…`), and its output has no augmentation
   record (checked). The guide says only that the helper's accepted subset and
   input checks differ from `run`.
4. **`runner_result.policy_sha256` is computed by the host** (`computePolicyHash`;
   `CWorkerOrchestrator.swift:220`, `ActorOrchestration.swift:440,553`). A
   match with `applied_sha256` shows the host received the augmented text.
   Only the opt-in receipt's `compiled_profile.source_sha256` shows it from
   inside the worker. The applied source is the submitted source, a newline and
   the augment file's bytes. This was checked for one run; the guide does not
   state the joiner.
5. **The receipt's source hash excludes imports.** An explorer reported that
   editing the imported file changed `closure_sha256` and the bytecode hash but
   not the source or applied hashes.
6. **`process_disposition` describes only the worker.** An explorer reported a
   validator killed at its deadline beside `clean_exit` and `valid`. The
   host's own exit, about 50 ms after its reply, is not reported anywhere.
7. **Ordinary-form `required_entitlements` is checked against the install-time
   registry record**, not the live worker. Only the actor form inspects live
   code. This was read from source by an explorer and not run.
8. **`same_submitted` compares strings.** An explorer's policy allowed the
   `/private/tmp` spelling while the query and attempt used `/tmp`. The reply
   showed an `allow` prediction beside EPERM, with `query_first` and no
   limitation. BBX-001 realpaths its targets in the harness and so does not
   meet this case. Responsibility findings 6 and 7 are related.

## Leads not yet drafted as findings

The explorers ran these in scratch; none of their runs was retained.

- **Ending the worker and recording how it ended.** After a host deadline the
  reply showed `signaled`, `host_sentinel_deadline` and `valid`. `ps` found the
  worker, validator and host gone at CLI return. Boundary: matter 6.
- **Starting each experiment in a never-sandboxed process.** Parallel runs
  showed separate hosts, workers and children in `ps`, matching each reply.
  Each actor ran in its own worker under one host. This may fit teaching
  finding 1.
- **Bounded, drained helper output.** About 200 KB of output came back as 1,007
  retained bytes with `truncated: true` and no blocked helper.
- **A clean environment and descriptor table for helpers.** This was read from
  source; the explorer's descriptor listing was blocked inside the sandbox.
- **Each actor's live process checked against its signed binary before
  activation.** Actor form only.
- **The installer signing the worker tree and rewriting the equipment
  inventory**, with entitlements read back from the signed files.
- **Cleanup ownership tracking in `runner remove`.** Its reading is
  responsibility finding 25.
- **The augmented source's hashes**, narrowed by matter 4, and the
  compiled-object receipt as a record of the applied object. A receipt is
  sensitive; none was retained.
