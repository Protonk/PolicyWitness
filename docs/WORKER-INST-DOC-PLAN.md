# Plan: The Worker — Instrument and Constraints

## Status

No pass has started. The plan is grounded at `e901fc0`. Worker, host and
helper sources there are those of v0.3.1, since `6fd9f06` and `e901fc0`
changed only this file, and `8ccbc53` still carries them unchanged. The
uncommitted BYOXPC investigation files and catalog additions in the working
tree are not evidence for this plan. The seed register was surveyed from source
at `e901fc0`; cited runtime cases were inspected, not rerun.

A second source-only survey on 2026-10-17, at the same worker sources, seeded
the inventory spine, pinned the inventory periods to symbols, moved rows 2, 3,
4, 5, 7 and 9 to awaiting adjudication with recommended dispositions, added
rows 12 to 14, and recorded the user's adjudication of rows 8 and 10. Findings
that survey withheld from the register are held by the user outside the tree;
the pass 1 stop compares the inventory against them.

At the end of every pass, update this section with the pass reached, the
register rows opened and closed, and the commit holding the pass's work.

## What this plan produces

`docs/WORKER.md`, titled **The Worker: Instrument and Constraints**, is the
third developer tour beside [ARCHITECTURE.md](ARCHITECTURE.md) and
[BUILD.md](BUILD.md). Its organizing question is: **what can the worker carry
across the sandbox boundary without compromising the experiment?** It is
written for a contributor who has read the repository README, needs to judge a
proposed worker change, and does not need PolicyWitness sold to them. It is
organized by resources and the authority they carry, not by time or source
file. A generated capability map is its principal figure.

Writing the document is also an assessment of the worker, as writing the
architecture and build tours assessed the run and the build. An accurate
account of an awkward instrument contains awkward sentences. A sentence that
is hard to write, or a generated row the prose cannot agree with, is how a
defect is found. The precedent is `63927cd`. The architecture plan's account
of the worker before apply had to say that it created exec pipes under a
descriptor budget. The premise behind that was false. Moving the pipes inside
the attempt removed the budget, its limits and seven harness cases.

The work proceeds in passes. Each finding is recorded in the register, decided
by the user, then fixed or accepted, and finally re-proved in the text.
Production changes happen only through adjudicated rows, in their own commits.
The writer never repairs the implementation to make a sentence true.

## How the assessment works

### The scope rule

Every sentence in WORKER.md states what the worker does, at a scope where it
could be wrong: what it holds, when it acquires it, what it publishes. When the
true scope needs an exception, the sentence carries the exception, and the
exception opens a register row. No hard sentence is dropped. None is softened
into a negative ("does not establish …") or moved elsewhere to avoid it.

Negative statements have two homes in the document. A Known gap paragraph
records a guarantee the user has accepted as incomplete. A link to the owning
contract says what a field does not mean. The guarded qualifications in this
plan are working material for the register, not the document's register. A
responsible reader, perhaps superintending their own fork, can tell from
accurate positive claims what PolicyWitness is not.

### Evidence

Keep three kinds of evidence distinct:

- **Mechanical grounding:** a cited symbol exists, a test is defined, a
  generated region is current. It detects drift; it does not establish
  behavior.
- **Assertion coverage:** what a cited check actually asserts, in which
  configurations, and what it leaves untested. A suite's name or a passing run
  is not coverage evidence.
- **Observed behavior:** a recorded probe or case reaches the path and
  observes the effect. It holds for the revision, inputs and environment
  exercised. A cited case is not a freshly executed case.

Mark source-only conclusions as such.

### The register

Each row moves through `open → investigating → awaiting adjudication →
implementing → validating → closed`. The user decides each disposition:

- correct the document, including a source comment;
- fix the worker or host;
- strengthen verification;
- accept a limitation, written as a Known gap;
- intended behavior that needs explaining.

A row can carry more than one disposition. A documentation-only resolution
skips implementation but not validation. Reopen a row when new evidence
contradicts its decision or a change invalidates the evidence it rested on.

Give each investigated row a detail entry under its number, below the register
table:

- the sentence as it first had to be written, and the claim it was reaching for;
- implementing symbols, cited checks and what they assert;
- the hypothesis and the observation that would refute it;
- for any probe, its exact inputs, expected and actual results, and evidence
  path;
- the recommended disposition with its reasoning, the user's adjudication and
  the scope of any authorized change;
- the validation, and the sentence after the change.

The before and after sentences are the re-proof. A row closes when the
document says something accurate about the changed or accepted instrument.

A broad suite passing does not discard a counterexample. Weakening a promise,
adding a prose baseline exception, or narrowing a check merely to make the
document and tests agree is an adjudication, not an edit.

### Changes a row authorizes

A fix keeps a failing reproduction and adds a regression control that
distinguishes the defect from the fix. It lands in its own commit, naming the
row number.

Changing worker or host source means regenerating the worker identity
(`python3 docs/generate_worker_identity.py`) before building, making a signed
build, and running the exact cases that cover the changed path. Changing the
phase wait, the release store or query eligibility also requires
`witness_contract/order_barrier_mutations`. Follow
[the maintenance checklist](../AGENTS.md#maintenance-checklist-when-changing-things)
for request, evidence or layout changes. A change that would alter the wire
contract goes back to the user as separate scope.

## Editorial decisions

Organize the account around three experimental roles: **prepared reporting
apparatus, deliberately supplied authority, and resources acquired by the
attempted operation**. Evidence that arrives from outside the worker forms a
fourth group. The roles describe what a resource is for in the experiment.
They do not claim that reporting apparatus carries no authority or has no
effects. Membership is a finding, not a premise: a resource that fits no role,
or two, is drawn outside the role clusters and opens a row.

- Treat the boundary as policy application inside an already-running process.
  The worker already has executable code, native libraries, memory and process
  context. A fresh worker is not an empty process. Later phases use the same
  applied worker and can observe effects of earlier actions.
- State the post-apply surface at its actual extent. Where PolicyWitness's own
  post-apply calls allocate, open or create something, say so. Where a
  library's internal behavior is unobserved, name the call and say its
  internals are unobserved.
- Use ordinary file access, exec and an explicit extension experiment as the
  principal examples. Include Mach lookup and sysctl in the inventory without
  expanding into a catalogue of sandbox operations.
- Explain ordering as a condition of meaningful comparison. Link to the
  architecture tour for the protocol and the evidence contract for
  eligibility. A release ordinal is not a verdict delivered to the worker.
- Separate intentional ignorance from missing evidence. The worker
  deliberately does not classify prediction/enforcement agreement, while an
  unpublished native result is unavailable evidence. Neither licenses an
  inferred cause.
- Describe current behavior. Source comments are leads, not evidence; a stale
  comment is itself a register row.

## The inventory

Pass 1 completes an inventory of everything the worker holds or acquires. It
is complete over PolicyWitness's own call sites, from the host's spawn
preparation in [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) to
the worker's exit, including the extension issuer's path into the worker.

"Acquires" means creating or receiving any of:

- memory or a mapping;
- a descriptor;
- a Mach port or right;
- a process;
- authority: entitlements, policy, an extension token.

The inventory also covers what the worker receives without asking: inherited
descriptors, spawn attributes, environment and process context.

| Column | Records |
| --- | --- |
| Resource | What is held, named as the source names it |
| Acquired by | Process and call site (symbol) |
| When | One of the four periods below |
| Held across | The attempt only; later attempts in the phase; later phases; until exit |
| Released | Call site, or at exit |
| Authority | What the resource lets the worker do that it otherwise could not, or none |
| Sandbox-gated | Observed (cite the case), source-only, or unknown |
| Reaches exec children | Yes, no or unknown, with the inheritance rule that decides it; the [inheritance suite](../tests/suites/runner_exec_inheritance/README.md) observes environment and descriptors only |
| Role | One of the three roles or external evidence; none or several opens a row |

The periods are fixed by symbols in
[pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c):

- **Before compilation** ends at the `sandbox_compile_string` call in `main`
  and includes the host's preparation and the issuer's path.
- **Between compilation and apply** holds the capture, the pre-ready seam and
  the ready byte, and ends at `sandbox_apply`.
- **After apply within an attempt** is the body of `run_attempt`.
- **After apply outside an attempt** is `wait_for_proceed`, the erase after
  the phase loop, the two post-phase seams, the done publication and
  `spin_for_exit`.

Call-site completeness does not reach library internals, such as what
`sandbox_compile_string`, the extension routines or libc formatting allocate.
Record the call and mark its internal behavior unobserved, unless a source or
probe establishes it.

The working table lives in this plan until pass 2 turns it into the map's
manifest nodes and deletes it, because the manifest owns it.

### Inventory spine

The spine was seeded from source on 2026-10-17. It lists each acquisition
call site in source order, with the resource and the acquiring call only.
Every other column is pass 1's; in particular, nothing in the spine says when
or whether a resource is released. Extend the spine where the reading finds an
acquisition it lacks, and merge rows only where every column agrees. The spine
omits calls that return values without a handle (`mach_timebase_info`,
`mach_continuous_time`, `getpid`, `fcntl(F_GETPATH)`) and the attempts that
acquire nothing beyond stack storage (`unlink`, `access`, `sysctl_read`);
confirm those omissions. External-evidence producers (the validator, the log
collector, the host's readers) hold nothing in the worker and belong to pass
2's fourth group. Library-internal allocation at any post-apply site is row
6's question.

| # | Resource | Acquired by |
| --- | --- | --- |
| S1 | Evidence region object and the host's descriptor to it; name unlinked at once, `FD_CLOEXEC` cleared, sized by `ftruncate` | Host, [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift): `pw_cworker_shm_open_create` |
| S2 | Host mapping of the evidence region; zeroed, populated, every page touched, `prepared` stored | Host, `runCWorker`: `mmap` |
| S3 | Ready pipe, both ends `FD_CLOEXEC`; the write end becomes worker descriptor 4 | Host, `runCWorker`: `pipe` |
| S4 | Policy pipe, write end `F_SETNOSIGPIPE` and `O_NONBLOCK`; the read end becomes worker descriptor 0 | Host, `runCWorker`: `pipe` |
| S5 | Token delivery duplicate of the session's delivery descriptor; becomes worker descriptor 5 | Host, `runCWorker`: `fcntl(F_DUPFD_CLOEXEC, 64)` |
| S6 | Spawn file actions for the worker: four `adddup2` entries, no spawn attributes | Host, `runCWorker`: `posix_spawn_file_actions_init` |
| S7 | The worker process, spawned with nil attributes and nil environment | Host, `runCWorker`: `posix_spawn` |
| S8 | Extension channel object, the host's descriptor (`FD_CLOEXEC`) and the host's mapping, with magic and resolved target written | Host, [`ExtensionSession`](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift): `pw_cworker_shm_open_create`, `mmap` |
| S9 | The issuer process, spawned with `POSIX_SPAWN_CLOEXEC_DEFAULT`, the channel at descriptor 3 and stdio from `/dev/null` | Host, `ExtensionSession`: `posix_spawn` |
| S10 | The issuer's channel mapping and zero core-dump limit | Issuer, [`main`](../controller/tools/pw_probe_runner/pw_extension_issuer.c): `setrlimit`, `mmap` |
| S11 | libsandbox handle and three resolved symbols in the issuer | Issuer, `main`: `dlopen`, `dlsym` |
| S12 | The token, written into the channel with its length | Issuer, `main`: `sandbox_extension_issue_file` |
| S13 | Worker descriptors 0, 3, 4 and 5, by explicit file action | Received; numbers read by [`parse_args`](../controller/tools/pw_probe_runner/pw_probe_runner.c) |
| S14 | Worker descriptors 1 and 2, and any host descriptor without `FD_CLOEXEC` | Received; no PolicyWitness call site sets them (row 1) |
| S15 | Worker environment, from a nil `envp` | Received (row 1) |
| S16 | Worker process context: signal dispositions and mask, resource limits, working directory, umask, task and bootstrap ports, loaded libraries and their threads | Received (row 11) |
| S17 | `SIGPIPE` disposition `SIG_IGN` | Worker, [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c): `signal` |
| S18 | Worker mapping of the evidence region, `PW_SHM_REGION_BYTES`, `MAP_SHARED` | Worker, [`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c): `fstat`, `mmap` |
| S19 | Native extension entry points in static pointers | Worker, [`prepare_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c): `dlsym(RTLD_DEFAULT)` |
| S20 | Zero core-dump limit, only when `extension_requested` | Worker, `prepare_extension`: `setrlimit(RLIMIT_CORE)` |
| S21 | Worker mapping of the extension channel, `PW_EXTENSION_CHANNEL_BYTES`, `MAP_SHARED` | Worker, `prepare_extension`: `fstat`, `mmap` |
| S22 | The token bytes inside that mapping, admitted by the length and NUL rules | Worker, `prepare_extension`: channel inspection |
| S23 | Policy source buffer, `static`, `PW_SHM_POLICY_BYTES`, filled from descriptor 0 | Worker, `main`: `read_all_from_fd` |
| S24 | Consumed parameter snapshot, `static`, `PW_SHM_MAX_PARAMS` entries | Worker, `main`: `memcpy` |
| S25 | SandboxParams object | Worker, `main`: `sandbox_create_params`, `sandbox_set_param` |
| S26 | Compiled profile object, and the compiler's error string on failure | Worker, `main`: `sandbox_compile_string` |
| S27 | Nothing new: profile memory read through the task port into the capture region of S18 | Worker, [`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_profile_capture.h): `mach_vm_read_overwrite` |
| S28 | The applied policy, a restriction of the worker's own authority | Worker, `main`: `sandbox_apply` |
| S29 | Target descriptor of `open_read`, with one byte read | Worker, [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c): `open(O_RDONLY)` |
| S30 | Target descriptor of `open_write`, with one byte written | Worker, [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c): `open(O_WRONLY \| O_TRUNC)` |
| S31 | Target descriptor of `create`, and the file it may create | Worker, [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c): `open(O_WRONLY \| O_CREAT, 0600)` |
| S32 | Target descriptor of `read_fresh`, with identity and a bounded read | Worker, [`attempt_file_read_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c): `open(O_RDONLY \| O_CLOEXEC)`, `fstat`, `read` |
| S33 | Mach rights taken by the lookup attempt | Worker, [`attempt_mach_lookup`](../controller/tools/pw_probe_runner/pw_probe_runner.c): `task_get_special_port`, `bootstrap_look_up` |
| S34 | Two exec capture pipes | Worker, [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c): `pipe` |
| S35 | Exec spawn handles, flagged `POSIX_SPAWN_CLOEXEC_DEFAULT` and `POSIX_SPAWN_SETPGROUP` | Worker, `exec_resources_acquire`: `posix_spawn_file_actions_init`, `posix_spawnattr_init` |
| S36 | The exec child and its process group, spawned with an empty environment | Worker, [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_probe_runner.c): `posix_spawn` |
| S37 | Extension handle in static storage, from the token of S22 | Worker, [`attempt_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c): `extension_consume` |

The survey found no acquisition after apply outside an attempt. Confirm that
along `wait_for_proceed`, the post-loop erase, the two seams and
`spin_for_exit`.

### Launch-inventory observation (rows 1 and 11)

Source cannot decide what the launchd-managed host leaves open, or what a nil
environment yields. The observation that decides it: one production worker,
under an allow-default specimen, held by the post-apply hang seam and
inspected from outside during the hang; a second worker held by the pre-ready
hang seam gives the pre-apply state. The baseline instruments are `lsof -p`
for descriptors and `ps -E -p` for the environment. Add mappings and Mach
rights only if a same-user observer can obtain them against the signed worker,
and state the boundary either way. The
[contaminated-worker case](../tests/suites/runner_exec_inheritance/README.md#contaminated-worker)
is the positive control: it shows a worker carrying what its parent left open,
so an empty finding against the real host is a finding about the host, not
about the instrument. The nil-environment half can also be decided by reading
xnu's spawn path; the reading and the observation should agree.

## Register

Rows 1 to 11 come from the planning survey and rows 12 to 14 from the second
survey. Evidence is what each survey saw in source at `e901fc0`, source-only
unless noted, and is verified again before a row changes state. Rows 8 and 10
are adjudicated; the rest await pass 1 or the user. Later rows are added as
passes find them.

| # | Candidate | Survey evidence | State | Disposition |
| --- | --- | --- | --- | --- |
| 1 | The worker's launch is not isolated the way its children's are | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) calls `posix_spawn` with file actions for fds 0, 3, 4 and optionally 5, no spawn attributes and a nil environment. The issuer ([`ExtensionSession`](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift)) and exec children ([`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c)) set `POSIX_SPAWN_CLOEXEC_DEFAULT`. Which other host descriptors the worker inherits (stdio included), and what the nil environment yields, is unobserved; the dossier records neither. Decided by the launch-inventory observation under The inventory, with the contaminated-worker case as its control. | open | |
| 2 | Pre-apply descriptors stay open after apply | The worker does not close the policy descriptor, the shared-region descriptor or the ready pipe after use, so all three are held across apply and every attempt. [`prepare_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c) closes the token descriptor after mapping. Exec children do not inherit them. Confirmed 2026-10-17: the worker has no `close` of descriptors 0, 3 or 4, and `prepare_extension` closes 5 after mapping. Whether any experiment is affected is a disposition, not a survey question. | awaiting adjudication | Recommended: intended behavior that needs explaining; see the row detail. |
| 3 | `open_write` truncates and writes | [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c) opens with `O_WRONLY \| O_TRUNC`, writes one byte, ignores the write and close results and reports open success. The guide's [attempt kinds](PolicyWitness.md#attempt-kinds-the-runner-implements) entry says only "exercise file ops on `target`"; the survey found no document stating the truncation. Confirmed 2026-10-17. | awaiting adjudication | Recommended: correct the document; see the row detail. |
| 4 | `open_read` reports open success only | [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c) reads one byte, "so the kernel observes the read", and discards the result. `read_fresh` is the action that records a read. Confirmed 2026-10-17. | awaiting adjudication | Recommended: correct the document; see the row detail. |
| 5 | `create` opens an existing file without truncating it | [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) uses `O_WRONLY \| O_CREAT` without `O_EXCL`; its comment calls this "semantics callers depend on". The [existing-file create](../tests/suites/witness_contract/README.md#create-on-an-existing-file) case checks bytes and identity. Confirmed 2026-10-17. | awaiting adjudication | Recommended: intended behavior that needs explaining; see the row detail. |
| 6 | Exec attempts allocate after apply at PolicyWitness call sites | Since `63927cd`, `exec_resources_acquire` initializes spawn file actions and attributes inside the attempt. On Darwin these are opaque handles whose init functions allocate (verify against the SDK's libc before relying on this). `fail_from_errno` formats with `snprintf` and `strerror` after apply. The [Runner simplicity](ARCHITECTURE.md#principles-as-enforced-constraints) principle names request, evidence and token storage as preallocated; the inventory decides whether that sentence holds at its stated scope. Decided by reading xnu's libsyscall spawn wrapper, where the handle init functions are defined, and the libc formatting calls: a citation, not a probe. | open | |
| 7 | Worker source comments describe retired premises | The header calls reading the policy into a stack buffer "the LAST allocation attempt before sandbox_apply()", yet parameter creation and `sandbox_compile_string` (commented as allocating internally) follow it. The attempt section says "No allocations post-apply" per "R6". The comments cite R5 and R6, which nothing else in the tracked tree defines, and "the Swift worker". Confirmed 2026-10-17, with one more item: the header calls the policy buffer stack-fixed, and `main` declares it `static`. | awaiting adjudication | Recommended: correct the source comments; see the row detail. |
| 8 | Two documents will state the private-extension limit | ARCHITECTURE has it as a Known gap under its principles; WORKER.md will state it beside its inventory. Decide which document owns the paragraph and which links to it. | implementing | Adjudicated 2026-10-17: WORKER.md owns the paragraph and ARCHITECTURE.md links to it. Lands with pass 3 and the integration work. |
| 9 | Release is not revocation | [check_extensions.py](../tests/suites/witness_contract/check_extensions.py) permits access after a successful release ("A successful release does not itself require access revocation"); nothing checks revocation. Confirmed 2026-10-17: the checker accepts either result of the after-release read. | awaiting adjudication | Recommended: accept, inside row 8's paragraph; see the row detail. |
| 10 | Exec helpers can outlive the worker | ARCHITECTURE's Known gap covers descendants that leave the child's process group. Worker death during exec can leave helpers alive. This has row 8's ownership question, plus whether to accept it. | implementing | Adjudicated 2026-10-17: WORKER.md owns the paragraph and ARCHITECTURE.md links to it; the limitation stays accepted as ARCHITECTURE states it today. Lands with pass 3 and the integration work. |
| 11 | The worker's ambient resources are uninventoried | No source or control establishes the full set of descriptors, ports, threads and library mappings the worker holds at apply. Row 1 is the part PolicyWitness controls; this row is the rest. A stronger claim would need an independently observed launch inventory or targeted instrumentation with a stated observation boundary. Decided, within its stated boundary, by the launch-inventory observation under The inventory. | open | |
| 12 | Exec children inherit the worker's ignored `SIGPIPE` and its zero core-dump limit | `main` sets `SIGPIPE` to `SIG_IGN`; [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c) sets only `POSIX_SPAWN_CLOEXEC_DEFAULT` and `POSIX_SPAWN_SETPGROUP`, so an ignored disposition survives the exec; `prepare_extension` zeroes `RLIMIT_CORE` when an extension is requested, and limits are inherited. The inheritance observer, [helper.c](../tests/fixtures/exec/helper.c), reports environment and descriptors and ignores `SIGPIPE` itself, so no case observes either. The explicit-descriptor and empty-environment contract is narrower than a clean child. | open | |
| 13 | The core-dump limit differs between extension and non-extension runs | `prepare_extension` returns before `setrlimit` when `extension_requested` is 0, so process context is a function of the request. | open | |
| 14 | The normal-completion token erase is skipped on the proceed-refusal path | The timeout and refusal paths of [`wait_for_proceed`](../controller/tools/pw_probe_runner/pw_probe_runner.c) publish `done` and spin without returning, so the erase after the phase loop in `main` is not reached. The erase at the consume decision and the host's erase of the shared pages still apply. The sentence about erasure stands with its exception. | open | |

### Row details

**Row 2.** Candidate sentence: "Descriptors 0, 3 and 4 stay open from launch
to exit; descriptor 5 is closed once the channel is mapped; exec children
inherit none of them." Symbols: `main`, `prepare_extension`,
`exec_resources_acquire`. After the host closes its ends, descriptor 0 reads
EOF and descriptor 4 has no reader; descriptor 3 backs a mapping that outlives
it. Refutation: a post-apply use of any of the three, or a child holding one.
Recommended: explain as intended behavior, with the inheritance suite as the
child-side evidence. The alternative is a fix that closes all three before
apply, which shortens the sentence to "after apply the worker holds only the
descriptors its attempts open" at the cost of a worker change, identity
regeneration and a signed build, for no change in what any attempt can observe.

**Row 3.** Candidate sentence: "`open_write` opens the target for writing,
truncates it to zero length and writes one byte, and reports only the open
result." Symbol: `attempt_file_open_write`. Refutation: a run after which the
target's length is not one byte. Recommended: correct the document, in the
guide's attempt-kinds entry and the worker tour; no worker change.

**Row 4.** Candidate sentence: "`open_read` opens the target, reads one byte
and discards it, and reports only the open result; `read_fresh` records what
it read." Symbols: `attempt_file_open_read`, `attempt_file_read_fresh`.
Recommended: correct the document, in the same places as row 3.

**Row 5.** Candidate sentence: "`create` opens an existing target for writing
without truncating it, and creates a missing one with mode 0600." Symbol:
`attempt_file_create`; the existing-file create case checks bytes and
identity. Recommended: intended behavior that needs explaining; the case is
its evidence.

**Row 7.** Items: the header's "stack-fixed buffer" and "LAST allocation
attempt before sandbox_apply()", the attempt section's "No allocations
post-apply" and its "R6", the "R5" at the SPI declarations, and the two
"Swift worker" references. Recommended: correct the source comments in one
commit. That changes worker source, so it follows "Changes a row authorizes":
identity regeneration, a signed build and the identity check. Comments are
leads, not evidence, so no behavioral case covers them.

**Row 9.** Candidate sentence: "A successful release returns zero; nothing in
PolicyWitness observes whether access is revoked afterward." Symbol:
`attempt_extension`; [check_extensions.py](../tests/suites/witness_contract/check_extensions.py)
accepts either outcome of the after-release read. Recommended: accept, as the
revocation clause of row 8's paragraph, which ARCHITECTURE already states. A
case asserting the after-release read under the denying policy would be new
evidence and is separate scope if wanted.

## Passes

Each pass ends with a commit of its work and an update to Status. A pass
marked *stop* ends with a review with the user before the next pass starts.

**Pass 1: inventory** (*stop*). Fill the spine's remaining columns and extend
it where the reading finds an acquisition it lacks. Verify the rows already
awaiting adjudication rather than re-deriving them, and take any further row
that source decides to "awaiting adjudication" with a recommended disposition.
Decide row 6 from source. Run the launch-inventory observation for rows 1 and
11 with its control, and design any other probe, with a control that could
refute its hypothesis, only where source cannot decide a row and the answer
would change the document. Write no prose. At the stop, the user reviews the
inventory's scope, compares it with the findings withheld from the register,
and adjudicates the rows ready for it.

**Pass 2: map.** Add destination support to the generator with its controls,
as described below. Then add manifest nodes and edges from the inventory and
render. Read the SVG at normal size as an assessment, not just a legibility
check. Look for:

- an edge that implies authority flowing where none does;
- a resource drawn inside a role it only partly fits;
- a node with no path to anything the experiment observes.

Each such reading becomes a row. A matching SVG stamp does not establish
legibility.

**Pass 3: prose** (*stop*). Draft from the section briefs against the map,
under the scope rule. Every hard sentence becomes a row that keeps the
sentence as it was written. At the stop, the user reviews the draft with the
register.

**Pass 4: changes.** Implement the adjudicated rows as described under
"Changes a row authorizes", re-prove each in the document and regenerate. This
pass recurs after any later stop that adjudicates new rows.

**Pass 5: challenge.** Read in both directions:

- from each material claim to its implementation, assertions and observations;
- along the worker from spawn to exit, looking for operations, descriptors,
  branches and failure paths the account omits.

Challenge universal words: "every", "only", "before", "after apply", "fixed",
"fresh". Counterexamples go back to the register, not to the editor.

**Pass 6: plan-blind audit** (*stop*). A fresh agent that has not seen this
plan reads WORKER.md, the map and the cited sources. It reports claims it
cannot support and omissions it finds. Commit the audit prompt as its own file
so the auditor sees a clean tree. Keep the report under `.tmp/audits/`, so
that its numbers do not trip the prose baseline. Findings enter the register
for the user to adjudicate, and pass 4 follows.

**Closeout.**

- Complete the integration work.
- Move the register's substance into a record under `records/`, linked only
  from this plan.
- Delete this plan.

The document is ready to publish when every material claim has a supported
account or an accepted limitation, each implemented fix has its validation,
and no open row could change what the document says.

## Proposed document structure

The writer may change heading wording and paragraph balance. A finding that
the structure itself misrepresents the worker is a register row.

### 1. The experimental question

Introduce the tension between surviving the specimen and staying exposed to
what it tests. Establish the host/worker split briefly. The worker applies the
policy and conducts attempts. The unsandboxed host arranges queries, collects
publications and replies. Explain why opening a target beforehand asks a
different question from opening it under the specimen policy. Place the tour
beside the run and build tours as an account of the instrument, not a
normative contract.

### 2. What the worker holds

The map and the generated inventory tables go here. Prose explains each role
through its principal examples and names the resources that fit no role.

- Distinguish the backing mapping from its descriptor. Results are published
  through mapped memory; the token mapping has different authority, ownership
  and erasure rules.
- State where the policy and ready descriptors stand after apply, as row 2's
  disposition decides, without presenting them as result paths.
- Contrast the worker's launch with the explicit descriptor and
  empty-environment contract for exec children, which excludes the worker's
  reporting descriptor. Rows 1 and 12 decide how, and row 12 decides what
  that contract leaves out.

### 3. What can become an observation

Explain the operational knowledge the worker needs: attempt kinds and targets,
bounded arguments, phase partitions and ordinals, time allowances, extension
handle state, native returns and publication state. It compiles through
libsandbox; it is not a policy interpreter deciding what should happen. Build
the section on three distinctions:

1. **A native call and a published result.** Progress is a latest atomic
   milestone, not a trace. A pre-call marker establishes reaching that
   boundary, while immutable payload becomes readable only through
   publication. Use the create-then-kill-before-publication control: the
   independently observed file exists while the reply withholds the completed
   result. Explain why reading partially written payload would be wrong.
2. **An attempted operation and the effect recorded.** Contrast `open_read`
   with `read_fresh`, then cover `open_write`, `create`, and an exec child's
   nonzero exit after successful spawning. Rows 3 to 5 settle the wording.
   Link to the action reference for the full catalogue.
3. **Firsthand evidence and external observations.** Predictions originate in
   the validator, and disposition and comparison assembly belong to the host.
   Later path enrichment is a host observation; logs and dossier assembly are
   outside the worker. Neither predictions nor logs become the worker's
   explanation of a failure.

Link to the existing ownership and comparison contracts rather than copying
their tables. Validator queries use no-report mode. Eligible `query_first`
records establish order, not a snapshot. An unchanged path spelling does not
establish an unchanged object.

### 4. Changes that would change the experiment

Short design-review cases. Each names the tempting change, the question it
would answer instead, and the current behavior. The current-behavior column is
a set of claims for pass 5 to confirm, each with its evidence; one that does
not hold is a row. Do not present hypothetical changes as discovered bugs.

| Tempting change | Question it would answer instead | Current behavior to confirm |
| --- | --- | --- |
| Open a target before apply, or keep its descriptor across extension phases. | Use of previously acquired authority rather than fresh acquisition under current conditions. | Fresh reads open and close within each action. |
| Prepare all exec pipes and handles before apply, for reliability. | Moves attempt setup outside the specimen; can hide setup restrictions or exhaustion. | Setup happens per attempt, after apply; descriptor-ceiling and bare-deny controls test different aspects. |
| Warm up an extension by consuming before apply, or hide tokens in reporting state. | Introduces authority before the declared intervention. | Symbols are resolved without calling consume or release; a separate channel carries the token; lifecycle results are published at the requested actions. |
| Retry with a changed path, extra authority or a friendlier policy; reuse a sandboxed worker for a new specimen. | Substitutes changed conditions for the submitted experiment. | No such retry exists; interrupted I/O and process-observation loops do retry within their protocols. |
| Add `exec_baseline` automatically so an experiment runs. | Changes the tested policy; its broad file-read allowance can override the denial under investigation. | Augmentation is explicit and accounted for in the resolved source. |
| Move interpretation or reporting into the sandboxed process, or treat success or missing output as self-explanatory. | Makes replies depend on specimen-controlled communication, or imports unsupported conclusions. | Assembly is external, and missing publication is distinguished from a missing effect. |

Explain the ordering risk briefly. Removing the hold until collection closes
would let worker effects change what supposedly prior queries see. The intact
hold does not freeze external actors, and it does not stop earlier actions
within a phase from changing conditions for later ones.

### 5. Where the instrument stops

Explain how a contributor assesses a new capability. Identify its authority,
its acquisition point, its native observation and publication mechanism, and
an independent control that could falsify the claim. Working rules stay in
AGENTS files.

Limits sit beside the promises they limit. A Known gap paragraph comes only
from a row adjudicated as an accepted limitation. Intentional semantic limits
are explained as behavior rather than labeled gaps. The private-extension and
exec-descendant paragraphs move here from ARCHITECTURE under rows 8 and 10.
The document ends with **Known gaps**, indexing those paragraphs in document
order.

## The capability map

Add a graph to [architecture.json](architecture.json), routed to WORKER.md and
rendered as `docs/worker-capabilities.dot` and `docs/worker-capabilities.svg`.
The map answers "what kind of resource or evidence is this, and which boundary
does it cross?" It is not a timeline, a sequence diagram or a copy of the
process topology.

- One node per inventory resource. Merge entries only where the inventory
  shows them identical in every column.
- The node facts are the inventory columns. The node's first source cites the
  acquisition call site, so the citation sits next to the claim it most needs
  to support.
- Clusters for the three roles and external evidence, labeled in text as well
  as color. The generator allows a node in at most one cluster and permits
  unclustered nodes. A resource with two roles or none stays outside the
  clusters, and the prose names it.
- Edge kinds by role (prepares, supplies authority, exercises, publishes,
  observes, joins), added to the manifest's shared styles. Edge ids use a
  prefix no other graph uses, such as `W`.
- Draw evidence and token mappings as separate nodes. Make the application
  boundary legible without implying it erases preexisting resources.
- Edges among external evidence join collected evidence. None implies a
  prediction or explanation sent into an attempt.
- Include an accessible description in the document. The caption may promise
  that citations resolve and checks are defined, not that they prove the
  behavior. Use limit placeholders for durations and sizes.

The generator currently admits one destination:
[`load_manifest`](generate_architecture.py) requires an exact set of top-level
keys under schema 2, and `SPAN_DOCUMENTS` names only ARCHITECTURE.md. The
change is bounded:

1. Add an optional per-graph document destination, defaulting to the
   top-level one, and advance the manifest schema. This is not a wire-version
   change. Register the destinations, and keep strict rejection of unknown
   fields, escaping paths and duplicate outputs.
2. Route the new graph to WORKER.md, leaving the existing figures in
   ARCHITECTURE.md. Update rendering, SVG links and tooltips, inventories,
   self-citation exclusions and check/write paths for each destination.
   Validate every document and finish rendering before writing any output.
3. Register WORKER.md for architecture spans. ARCHITECTURE's sentence saying
   how many figures it generates renders the `architecture.graphs` span, which
   counts every manifest graph; revise it to count the figures embedded there,
   using per-graph spans where prose needs counts. Register WORKER.md with the
   limits span owner only if a value is essential; prefer links to limits.
4. Update [architecture controls](../tests/suites/source_drift/architecture.py)
   and [generator ownership controls](../tests/suites/source_drift/generators.py).
   Add passing and rejected controls for:
   - routing;
   - stale regions or figures in either document;
   - invalid destinations;
   - duplicate ownership;
   - broken markers in the second document;
   - a render failure that leaves both documents and all figures untouched.

   Keep idempotence, citation-definition and no-self-citation checks.

ARCHITECTURE's document graph gains the new document and its edges.

## Supporting evidence

Use these anchors when reviewing claims against evidence. Source location,
test definition, controlled interpretation and live observation establish
different things.

| Claim area | Implementation and normative anchors | Controls and their limits |
| --- | --- | --- |
| Prepared mapping, delivery and identity | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift), [`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [internal identity](CONTRACT.md#internal-hostworker-identity). | [C harness](../tests/suites/runner_c_worker_harness/README.md): bare-deny/full-region publication, identity mismatch, NUL and truncated-policy refusals; [ABI suite](../tests/suites/runner_abi_layout/README.md). Tested publication is narrower than universal survival. |
| Publication versus effect | [`run_attempt`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`pw_progress`](../controller/tools/pw_probe_runner/pw_worker_evidence.h), [`buildAttemptResult`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [worker evidence](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract). | [Death before publication](../tests/suites/witness_contract/README.md#death-after-the-native-return-before-publication) and [its checker](../tests/suites/witness_contract/check_killed_before_publication.py) observe the file effect independently and require withholding its unpublished result. |
| File observations | [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_file_read_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [fresh-read semantics](PolicyWitness.md#extension-and-fresh-read-output). | [Existing-file create](../tests/suites/witness_contract/README.md#create-on-an-existing-file) checks bytes and identity; [extension checks](../tests/suites/witness_contract/check_extensions.py) inspect fresh descriptor identity and bytes. Source establishes which older action returns are discarded. |
| Per-attempt exec acquisition | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`exec_resources_release`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_probe_runner.c). | [C harness exec controls](../tests/suites/runner_c_worker_harness/README.md#exec-resources-are-per-attempt), [their assertions](../tests/suites/runner_c_worker_harness/run.sh) and [public exec cases](../tests/suites/runner_use_c_worker/README.md). The descriptor ceiling rules out holding all steps' pipes at once; source establishes placement after apply. |
| Exec-child isolation/lifetime | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [execution limits](LIMITS.md#execution-budgets). | [Inheritance](../tests/suites/runner_exec_inheritance/README.md) contaminates the worker and reads explicit child state; [lifecycle](../tests/suites/runner_exec_lifecycle/README.md) observes processes independently. Neither establishes a clean worker environment or general process-tree containment, and the observer reports environment and descriptors, not signal state or limits (row 12). |
| Timing and ordering | [`pw_timing_setup`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`wait_for_proceed`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift), [`buildOrdering`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift); [ordering evidence](../tests/FAILURE-PROPAGATION-CONTRACT.md#ordering-evidence-states). | [Timing controls](../tests/suites/runner_c_worker_harness/README.md#worker-timing-controls) test sampled decisions; [gated effects/external mutation](../tests/suites/witness_contract/README.md#predictions-before-attempts) test observed ordering and snapshot limits. The opt-in barrier mutation control tests detection of bypass. |
| Extension authority | [`ExtensionSession`](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift), [issuer source](../controller/tools/pw_probe_runner/pw_extension_issuer.c), [`prepare_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c), [`attempt_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [extension evidence](../tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence). | [Extension boundaries](../tests/suites/witness_contract/README.md#native-extension-boundaries), [native fixtures](../tests/fixtures/extension_controls/README.md) and [fresh-read checks](../tests/suites/witness_contract/check_extensions.py). The live checker permits access after successful release; it does not verify revocation. |
| Prediction and comparison | [`planValidatorQueries`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), [`comparisonEvidence`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), [validator source](../controller/tools/sb_api_validator/sb_api_validator.c); [claim/evidence review](../tests/FAILURE-PROPAGATION-CONTRACT.md#claimevidence-review). | [Independent targets](../tests/suites/witness_contract/README.md#independent-prediction-and-attempt-targets), [comparison matrix](../tests/suites/witness_contract/README.md#comparison-matrix) and [unit controls](../runner/Tests/PWRunnerCoreTests/ComparisonEvidenceTests.swift). Constructed records test interpretation, not kernel causation. |
| External observations | [`resolveDisposition`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift), [`enrichPathDiagnostics`](../runner/Sources/PWRunnerCore/PWRunnerService.swift), [`attach_sandbox_logs`](../controller/src/run_flow.rs); [ownership](ARCHITECTURE.md#evidence-channels-and-ownership). | [Termination/log correlation](../tests/suites/witness_contract/README.md#termination-and-denial-log-correlation) and [controller ownership](../controller/README.md#execution-and-log-evidence-ownership). A log match is a candidate association, not a worker-native explanation or unique causal event. |
| Starting authority/policy | [`enforce_required_entitlements`](../controller/src/runner_select.rs), [augment implementation](../controller/src/augments.rs); [BYOXPC](PolicyWitness.md#external-runners-byoxpc) and [augment limits](../runner/augments/README.md#exec_baseline-composition-limits). | [Selection controls](../controller/src/runner_select.rs), [BYOXPC suite](../tests/suites/runner_byoxpc/README.md), [augment unit tests](../runner/Tests/PWRunnerCoreTests/AugmentTests.swift). Entitlement read-back is not an inventory of every source of authority. |
| Compiler receipt | [`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_profile_capture.h), [`decodeProfileCapture`](../runner/Sources/PWRunnerCore/CWorker.swift); [receipt contract](PolicyWitness.md#compiled-object-receipt-opt-in). | [Capture controls](../runner/Tests/PWRunnerCoreTests/CompiledProfileCaptureTests.swift) and [dossier witness](../tests/suites/witness_contract/README.md#specimen-dossier). Compiler bytes, application publication and effective permissions remain distinct. |

## Integration work

| Existing owner | Relationship to the new tour |
| --- | --- |
| [Repository README](../README.md#documentation) | Add the worker tour beside the architecture and build tours, with its experimental-design purpose. |
| [Architecture tour](ARCHITECTURE.md) | Keeps temporal orchestration, topology, ordering and channel ownership. Link from the Runner simplicity principle to the new account. Under rows 8 and 10, its private-extension and exec-descendant Known gap paragraphs move to WORKER.md, the places they stood link there, and its Known gaps index shrinks to match. Update the document graph and the figure-count sentence. |
| [Build tour](BUILD.md) and [signing reference](SIGNING.md) | Keep compilation, identity generation, signing and provenance. Link to them from starting authority; add a reciprocal link near native compilation if useful. |
| [Runner reference](../runner/README.md) | Keeps the source map, lifecycle and test seams. Add a worker-tour link near the architecture link. |
| [Wire contract](CONTRACT.md), [request grammar](REQUEST-GRAMMAR.md), [user guide](PolicyWitness.md), [limits](LIMITS.md), [evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md) | Keep accepted inputs, fields, capacities and claims. Link to existing anchors rather than copying tables or creating a normative vocabulary. A row may correct one of them, as row 3 may for the guide. |

Extend [`check_known_gap_index`](../tests/suites/source_drift/check.py) to the
new tour. Extend the disposable-checkout controls in
[check_planner.py](../tests/suites/source_drift/check_planner.py) and the
document graph's account of that rule. Update the
[source-drift reference](../tests/suites/source_drift/README.md) for the
destination, manifest schema and gap coverage. Existing catalog cases can own
these controls.

The prose and link scan already covers `docs/*.md`. Use backticked-symbol
labels for symbol links and filename labels for file links. Do not add prose
baseline exceptions for unverified citations or copied constants. Edit
generator inputs and authored regions, then regenerate through their owners;
never hand-edit generated tables, DOT or SVG.

## Verification

Documentation passes (2, 3, 5 and the integration) regenerate affected
outputs, require a second generation to change nothing, run the check modes,
and run `source_drift` with fresh output:

```sh
python3 docs/generate_architecture.py
python3 docs/generate_architecture.py
python3 docs/generate_architecture.py --check
python3 docs/generate_build.py --check
python3 docs/generate_contract.py --check
python3 docs/generate_worker_identity.py --check
python3 docs/generate_limits.py --check
tests/run.sh --suite source_drift --list
PW_TEST_OUT_DIR=tests/out/runs/worker-doc-REPLACE_WITH_PASS_AND_NAME \
  tests/run.sh --suite source_drift
```

If another generator's inputs changed, run that generator before its check.
`source_drift` checks generated ownership, links, citations, spans, baseline
and build refusals. It does not establish runtime semantics.

Pass 4 changes to worker or host source need what "Changes a row authorizes"
lists: identity regeneration, a signed build, the row's reproduction and
regression control, and the exact covering cases. Record each case's
canonical ID, the source and build it applied to, and its actual result in the
row's detail entry. A probe in pass 1 or 5 follows the same recording rule.
Follow [test guidance](../tests/AGENTS.md#choose-and-run-verification) for
equipment, locking and sandboxed-harness retries. Never bypass a refusal or
reuse unrelated evidence for a pass.

## Acceptance

- The map and prose distinguish prepared reporting resources, supplied
  authority, acquisitions under the policy and external observations without
  reconstructing a timeline. Resources that fit no role are drawn and named.
- The inventory is complete over PolicyWitness's call sites, as defined above,
  and the manifest owns it.
- Every material claim is supported, or is an adjudicated accepted limitation
  written as a Known gap. No open row could change the account.
- Every closed row has its before and after sentences, its adjudication and,
  for a change, its reproduction, regression control and validation.
- No sentence upgrades a native return, publication flag, hash, log candidate
  or path spelling beyond what its owning contract permits.
- Generated outputs are reproducible and owned. Links, citations, gap indexes
  and source-drift controls pass without new baseline exceptions. Existing
  figure destinations and count meanings remain correct.
- Documentation and its machinery land in documentation commits. Any
  production change lands in its own adjudicated commit.

## Outflow (provisional)

Two things are outflow, not this plan: modularizing the generation machinery
so the architecture, build and worker accounts share it, and migrating prose
into semi-structured output locked to the app's characteristics.

As this plan stands, the first draft leaves the inventory in the manifest as
per-resource facts with citations, and leaves the prose authored. It adds no
rule tying the inventory to the worker's call sites. Such a rule would add a
parser over the C worker and a baseline. Build it only if a pass shows the
inventory drifting from source.

The state the first draft must leave for a later migration agent is to be
settled with the user before pass 2, and this section revised then. That
decision may change how pass 2 shapes the manifest.
