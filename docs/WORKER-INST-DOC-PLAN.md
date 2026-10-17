# Plan: The Worker — Instrument and Constraints

## Status

Pass 1 is complete at production source
`6fd44fb15397678d29f0f96bfee2b1abbe4bbbb6`. Its work commit is recorded in the
commit receipt after this pass lands. The inventory has 78 entries. Rows 1–7, 9 and 11–14 are
verified and await adjudication; new rows 15–19 also await adjudication.
Rows 8 and 10 retain their existing ownership/limitation decisions and remain
implementing for pass 3. No row closed, no production source changed, and no
WORKER.md prose or map was written.

The pass 1 evidence ledger records the signed build, two production launch
observations, inheritance controls, source-only findings and observation
limits. The worker/host/issuer sources are unchanged from the `e901fc0`
planning baseline. The current inventory supersedes the seeded spine and
corrects overstrong survey sentences explicitly in the row details.

This is the pass 1 stop: the user compares the inventory with findings held
outside the tree and adjudicates the ready rows. Pass 2 also waits for the
outflow/migration decision. At the end of each later pass, update this Status
with the pass, opened/closed rows and the commit holding its work.

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

### Pass 1 inventory

Reviewed against `6fd44fb15397678d29f0f96bfee2b1abbe4bbbb6`. The worker,
issuer and host sources under review are byte-identical to the planning
baseline (`git diff e901fc0 HEAD -- controller/tools/pw_probe_runner
runner/Sources` is empty). The spine IDs remain traceable; suffixes split
resources whose columns differ, and N IDs add missing acquisitions. This is
the working inventory, not WORKER.md prose or the pass 2 manifest.

Period keys: **A** before compilation; **B** between compilation and apply;
**C** after apply within an attempt; **D** after apply outside an attempt.
The compile call is A's closing boundary; its returned storage first exists at
that boundary. Host-only resources can outlive the worker's entry into B/C/D;
the period column identifies acquisition, not their entire lifetime.

Role keys: **P** prepared reporting apparatus (including request delivery and
control); **A** deliberately supplied authority or policy restriction; **O**
resources acquired by the attempted operation; **E** external evidence;
**none** or multiple roles explicitly name a register row. A role describes
purpose; it never promises absence of authority or effects. Exec reporting
pipes and handles are acquired in C even though their purpose is P.

Acquirer shorthand links to the implementing source: **H** is
[`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift), **W** is
[`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c), **E** is
[`ExtensionSession`](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift),
**I** is issuer [`main`](../controller/tools/pw_probe_runner/pw_extension_issuer.c).
Other worker symbols are in
[pw_probe_runner.c](../controller/tools/pw_probe_runner/pw_probe_runner.c).
**L** is the pass 1 `runner_exec_inheritance/launch_inventory` observation
recorded below, **IC** the contaminated-worker control, **CLI** the ordinary
exec-child control. In the gating column, L observes presence under
allow-default, never the counterfactual needed to establish sandbox gating.
Source-only placement before apply is not an exemption from ambient security.

In the release column, `close`, destroy, deallocation and unmap name calls,
not inferred success. Most return values are discarded; `read_fresh` and
extension preparation retain specified native cleanup results. Process exit
reclaims that process's references, not other processes' references or file
system effects. Successful-path lifetimes are qualified by the failure paths
in the cells and the branch audit below. A descriptor's number is not object
identity. Host buffers never become worker memory merely because spawn occurs.

| ID | Resource | Acquired by | When | Held across | Released | Authority | Sandbox-gated | Reaches exec children | Role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1a | Evidence shared-memory object | H: `pw_cworker_shm_open_create`, `ftruncate` | A | Later phases; last mapping/reference may outlive worker | H requests immediate `shm_unlink`; object survives references | Shared writable input/publication storage | Source-only, host before apply | No explicit child reference; see S13b | P |
| S1b | Host `shmFD` | H: `pw_cworker_shm_open_create`; clears `FD_CLOEXEC` | A | Through driver result collection | H setup-failure `close` or final defer | Can map/resize the evidence object | Source-only, host before apply | Worker receives it; exec child excludes it | P |
| S2 | Host evidence `base` mapping | H: `mmap`, zero/populate/page-touch | A | Through collection, even if worker cleanup unconfirmed | H defer `munmap` | Read worker publications; write input/release/exit request | Source-only, host before apply | No: exec replaces address space | P |
| S3a | Host ready-pipe read end | H: `pipe`; `FD_CLOEXEC` | A | Readiness wait only | H after readiness wait or setup/spawn failure | Observe ready byte | Source-only, host before apply | No: close-on-exec | P |
| S3b | Host ready-pipe write end | H: `pipe`; `FD_CLOEXEC` | A | Through worker spawn | H immediately after spawn or failure | Supply worker readiness endpoint | Source-only, host before apply | Worker fd 4; child excludes it | P |
| S4a | Host policy-pipe read end | H: `pipe`; `FD_CLOEXEC` | A | Through worker spawn | H immediately after spawn or failure | Receive policy bytes | Source-only, host before apply | Worker fd 0 replaced in exec child | P |
| S4b | Host policy-pipe write end | H: `pipe`; `F_SETNOSIGPIPE`, `O_NONBLOCK`, `FD_CLOEXEC` | A | Through bounded policy transfer | H after transfer or setup/spawn failure | Deliver source and EOF | Source-only, host before apply | No: close-on-exec | P |
| S5 | Host token-delivery duplicate `tokenFD` | H: `fcntl(F_DUPFD_CLOEXEC, 64)` | A | Through driver return | H defer `close` | Duplicate authority-bearing channel | Source-only, host before apply | Worker fd 5; exec/extension combination refused | A |
| S6 | Worker-spawn file-action handle | H: `posix_spawn_file_actions_init`, `adddup2` | A | Through driver return | H defer destroy | Prescribes worker descriptor table | Source-only; Apple malloc implementation, row 6 | Handle no; actions determine worker state | P; setup caveat row 19 |
| S7 | Fresh worker process | H: `posix_spawn`, nil attributes/envp | A | Until exit; unconfirmed cleanup may outlive driver | W return/`_exit`, fatal signal or H termination; H `waitpid` observes reap | Executes specimen with inherited context and signed identity | Source-only spawn; L observed two lifetimes | It parents exec children; not itself inherited | none (ambient execution substrate), row 11 |
| S8a | Extension channel object | E: `pw_cworker_shm_open_create`, `ftruncate` | A | Issuer then worker; through session | E requests `shm_unlink`; last reference controls destruction | Holds transferable token and issuer metadata | Source-only, outside worker sandbox | No admitted exec+extension plan | A + E, row 17 |
| S8b | Session `descriptor` | E: `pw_cworker_shm_open_create`, `FD_CLOEXEC` | A | Through session | E deinit `close`, including setup-failure returns | Map/duplicate token channel | Source-only | No: close-on-exec except explicit delivery dup | A |
| S8c | Host token-channel `mapping` | E: `mmap`, zero/header/path writes | A | Through reply preparation | E `erase` before reply; deinit erases, unmaps | Read issuance evidence; supply/erase token | Source-only | No: address space replaced | A + E, row 17 |
| S9 | Fresh issuer process | E: `posix_spawn` with `CLOEXEC_DEFAULT`, nil envp | A | Until issuer exit; delivery requires confirmed clean reap | I return; E wait/terminate | Ordinary signed issuer authority for file token issuance | Source-only; no live issuer case rerun in pass 1 | No: sibling, reaped before worker delivery | A |
| S10a | Issuer zero soft/hard core limit | I: `setrlimit(RLIMIT_CORE)` | A | Until issuer exit | Exit; failure returns before mapping | Restricts core-dump production | Source-only | No: issuer creates no exec child | P |
| S10b | Issuer channel mapping | I: `mmap` from fd 3 | A | Until publication/exit | Normal `munmap`; malformed header exits without explicit unmap | Write token and issuance metadata | Source-only | No child | A + E, row 17 |
| S10c | Issuer channel fd 3 | E `adddup2`, received by I | A | Through I mapping attempt | I `close(3)` after `mmap`; earlier errors leave to exit | Map channel | Source-only | No child | A |
| S11a | Issuer libsandbox dynamic-library handle | I: `dlopen(RTLD_NOW \| RTLD_LOCAL)` | A | Until exit; no explicit `dlclose` | Loader/process teardown; internals unobserved | Makes private issuance API callable, not an entitlement grant | Source-only | No child | A |
| S11b | Issuer issue/consume/release symbol addresses | I: three `dlsym` calls | A | Issuance check/call; loader image remains | Automatic values end with I; no independent handle release | API entry points; consume/release are checked, not invoked | Source-only | No child | A |
| S12a | Native returned token allocation | I: `sandbox_extension_issue_file` | A | Copy/reject decision only | I bounded erase then `free`; oversized tail caveat row 18 | Bearer bytes for native extension consumption | Source-only; private internals unobserved | No: issuer storage not inherited | A |
| S12b | Token bytes in shared channel | I: `memcpy` on bounded accepted token | A | Through worker consume decision or host erase; failure branches differ | Worker/host erasure; see S22 and row 14 | Transferable extension token | Source-only | No admitted exec+extension plan | A |
| S13a | Worker policy fd 0 | H `adddup2(policyPipe[0], 0)`; W default policy fd | A | Later attempts and phases, until exit | No W `close`; exit | Read remaining policy stream; normally EOF after source receipt | L observed pre/post presence; gating unknown | No: child `addopen` replaces stdin | P, retained after use (row 2) |
| S13b | Worker evidence fd 3 | H `adddup2(shmFD, 3)`; W `parse_args` | A | Later attempts and phases, until exit | No W `close`; exit | Map backing object separately from existing mapping | L observed pre/post presence; gating unknown | No: child `CLOEXEC_DEFAULT` | P, row 2 |
| S13c | Worker ready fd 4 | H `adddup2(readyPipe[1], 4)`; W `parse_args` | A | Later attempts and phases, until exit | No W `close`; exit | Write readiness pipe; host later closes reader | L observed pre/post presence; gating unknown | No: child `CLOEXEC_DEFAULT` | P, row 2 |
| S13d | Worker token fd 5, if supplied | H `adddup2(tokenFD, 5)`; W `parse_args` | A | Through extension preparation | `prepare_extension` closes once; early main refusals leave to exit | Map token channel | Source-only; close failure published on prepared path | No admitted exec+extension plan; child flags would exclude it | A |
| S14a | Worker inherited stdout/stderr | H spawn, without replacement file actions | A | Until exit | Exit; no explicit W close | Whatever underlying endpoints allow; L saw read/write `/dev/null` | L presence only; no universal stdio rule | No: exec-child capture pipes replace 1/2 | none, row 1 |
| S14b | Other inheritable ambient host descriptors | H spawn without `CLOEXEC_DEFAULT` | A | Until exit unless a file action overwrites number | No generic W sweep; exit | Depends on inherited objects | IC demonstrates inheritance; L saw no extra numeric fd | No: exec-child `CLOEXEC_DEFAULT`; IC/CLI observed isolation | none, row 1 |
| S14c | Possible original-number alias of evidence `shmFD` | H clears `FD_CLOEXEC` and duplicates to 3 without closing source | A | Until exit if original number survives file actions | No generic W sweep; exit | Same evidence object as S13b, not a second object | Source-only possibility; L saw no extra alias | No: exec-child `CLOEXEC_DEFAULT` | P, row 1 |
| S15 | Worker environment vector | H `posix_spawn(..., nil)` | A | Until exit | Process teardown | No entries observed; potential environment-dependent behavior is source-scoped | L plain/`-E` ps identical; Apple nil-env path corroborates | No: explicit `{NULL}` child env; IC/CLI | none, row 1 |
| S16a | Credentials and signed worker entitlements, ambient policy context | Kernel/loader at H spawn; controller checks required keys | A | Until exit; SBPL/extension interventions alter effective access | Exit, not a PW reset | Starting access and restrictions; built-in manifest has empty entitlements | Source + signed manifest; effective authority not fully measured | Credentials/policy inherit subject to exec semantics; child signature supplies own entitlements | A; ambient remainder row 11 |
| S16g | Working directory | Received at H spawn; no PW reset | A | Later attempts/phases, until exit | Exit | Relative file-target resolution | L cwd `/`; gating unknown | Yes, no chdir action | none, row 11 |
| S16h | File-mode creation mask | Received at H spawn; no PW reset | A | Later attempts/phases, until exit | Exit | Reduces requested creation mode | Source-only inheritance; live value unknown | Yes, no umask action | none, row 11 |
| S16c | Inherited resource limits | Received at H spawn | A | Until exit, except extension core-limit intervention | Exit; S20 changes core limit | Caps allocation, files, core, processes etc. | Unknown live values | Yes by spawn inheritance; public extension/exec exclusion applies | none, rows 11–13 |
| S16i | Inherited signal dispositions | Received at H spawn, nil attributes | A | Until exit except S17 | W changes SIGPIPE only | Affects fatal delivery and ignored signals | Source-only; no signal census | Ignored dispositions persist, caught handlers reset by exec; row 12 | none, rows 11–12 |
| S16j | Inherited signal mask | Received at H spawn, nil attributes | A | Until exit | No PW reset | Controls blocked signal delivery | Source-only; live mask unknown | Yes, no `SETSIGMASK`; row 12 | none, rows 11–12 |
| S16e | Task-self, bootstrap and other initial Mach rights | Kernel/runtime initialization at spawn | A | Until exit or library changes | No PW general release; full live right census unavailable | Task/IPC authority, bootstrap namespace access | L `lsmp` refused; exact set unknown | Special-port inheritance/native exec rules; exact set unknown | none, row 11 |
| S16f | Executable/library mappings, runtime heaps and threads | Loader/runtime creates new image at H spawn; later library calls | A initially; later internal changes unknown | Until exit or library release | Native runtime; no PW census/teardown | Executable code, storage and runtime service access | L `vmmap` inventory; per-allocation origin and gating unknown | Not the same mappings/threads: exec loads a new image | none, row 11 |
| S17 | Worker ignored SIGPIPE disposition | W: `signal(SIGPIPE, SIG_IGN)` | A | All attempts/phases, until exit | No reset | Survive broken ready-pipe write; also changes exec-child behavior | Source-only; L pre-ready final EPIPE survived | Yes: no `SETSIGDEF`; no dedicated live signal control | P + effect on O, row 12 |
| S18 | Worker evidence `base` mapping | `map_region`: `fstat`, `mmap(MAP_SHARED)` | A | Later attempts/phases, until exit | No explicit W unmap; exit | Read requests, publish results, observe release/exit | L shared mappings observed; no mapping-identity attribution from size alone | No: exec replaces mappings and excludes fd 3 | P |
| S19 | Static extension function pointers | `prepare_extension`: `dlsym(RTLD_DEFAULT)` | A | Later attempts/phases, until exit | Static storage at exit; no dynamic handle acquired here | Callable native consume/release, no pre-apply consumption | Source-only; library internals unobserved | No admitted combination; pointer storage not inherited across exec | A |
| S20 | Worker zero soft/hard core limit | `prepare_extension`: `setrlimit(RLIMIT_CORE)` after symbols resolve | A | All later attempts/phases, until exit if call succeeds | No reset; exit | Restricts core dumping; missing symbols/setup failure qualify it | Source-only, request-dependent | No admitted exec with extension; hypothetical ABI child would inherit | P + process context, row 13 |
| S21 | Worker extension-channel mapping | `prepare_extension`: `mmap(MAP_SHARED)` | A | Accepted mapping until exit, including after erase | Rejected mapping: erase/`munmap`; accepted: no explicit unmap | Read/erase token and inspect channel admission metadata | Source-only; rejection unmap failure recorded | No admitted combination; address space replaced on exec | A + P, row 17 |
| S22 | Accepted token view in S21 (alias of S12b, no copy) | `prepare_extension`: length/NUL/header inspection | A | Until consumption decision or normal loop completion; early exits differ | `attempt_extension` or post-loop erase; host erase remains | Consumable bearer token; validation does not consume it | Source-only | No admitted combination | A; row 14 |
| S23 | Static `policy_buf` | W static storage; `read_all_from_fd` fills it | A | Later attempts/phases, until exit | No wipe or explicit release | Policy input, not a target-file descriptor | Source-only; read receipt observed in L | No: new exec image | P |
| S24 | Static `consumed_params` snapshot | W: `memcpy` from bounded shared parameters | A | Later attempts/phases, until exit | No wipe; static storage teardown | Exact compile/capture inputs; no additional access | Source-only | No: new exec image | P |
| S25 | `params_obj` and parameter entries | W: `sandbox_create_params`, `sandbox_set_param` | A | Until compile return, or parameter refusal | `sandbox_free_params` on success/failure paths after creation | Supplies named compiler inputs | Source-only; private allocation internals unobserved | No: freed before possible child spawn | A |
| S26a | Returned compiled `profile` and its bytecode | W: `sandbox_compile_string` | A (compile boundary) | Passed to capture/apply; allocation lifetime inside apply unknown | No explicit `sandbox_free_profile`; exit reclaims remaining process storage | Input to restriction application; not an applied policy by itself | Source-only, private object lifetime unknown (row 16) | No: new exec image; applied restriction separate S28 | A |
| S26b | Compiler error string `compile_err` on failure | W: `sandbox_compile_string` out parameter | A (compile boundary) | Failure reporting only | W `free` when non-null and profile null | None; diagnostic bytes | Source-only | No child on failed compile path | P |
| S27 | Compiled capture bytes/header inside S18 | `pw_capture_profile` / `pw_read_memory`: `mach_vm_read_overwrite`, hashes | B | Later attempts/phases, until exit; host copies accepted receipt | No separate allocation/unmap; S18 teardown | Read own task memory via preexisting task port; publish receipt | Source-only, pre-apply | No: new image, evidence fd excluded | P |
| S28 | Applied sandbox policy | W: `sandbox_apply(profile)` | B closing boundary | All later attempts/phases, until exit on success | One-way, no undo | Restricts starting authority; extension may augment access | Source placement; L final application/clean completion, not deny coverage | Inherited sandbox constraints; exact child policy effects not inventoried here | A |
| S29 | `open_read` target fd | `attempt_file_open_read`: `open(O_RDONLY)` | C | Attempt only on ordinary cleanup path | `close` after best-effort one-byte read; return ignored | Read opened object | Source-only; no file probe rerun in pass 1 | No: closed before later exec, which also excludes it | O |
| S30 | `open_write` target fd | `attempt_file_open_write`: `open(O_WRONLY \| O_TRUNC)` | C | Attempt only on ordinary cleanup path | `close` after unchecked one-byte write | Write/truncate opened object; actual write result unpublished | Source-only, row 3 | No: later exec excludes it | O |
| S31a | `create` target fd | `attempt_file_create`: `open(O_WRONLY \| O_CREAT, 0600)` | C | Attempt only on ordinary cleanup path | `close`, return ignored | Write existing object or create missing object | Source-only; existing-file checker inspected, not rerun | No: later exec excludes it | O |
| S31b | Newly created filesystem object, if absent | `attempt_file_create`: same `open` | C | Later attempts/phases and beyond worker exit | No automatic unlink; later action/external actor may remove | Persistent filesystem effect, mode subject to umask | Source-only; creation not implied for existing target | Child can resolve it by path, not inherited fd | O |
| S32 | Fresh target fd and read observation | `attempt_file_read_fresh`: `open(O_RDONLY \| O_CLOEXEC)`, `fstat`, `read` | C | Attempt only on successful close; close failure retained | One `close`, result published; no retry | Read and identify fresh opened object | Source-only; extension checker inspected, not rerun | No: close-on-exec and child exclusion | O |
| S33a | Bootstrap send-right reference | `attempt_mach_lookup`: `task_get_special_port` | C | Later attempts/phases, until exit after successful acquisition | No matching `mach_port_deallocate`, even when lookup fails | Bootstrap namespace request authority | Source-only; native failure remains possible | No explicit transfer; special bootstrap port inheritance is separate | O, unintended retention candidate row 15 |
| S33b | Lookup service send right | `attempt_mach_lookup`: `bootstrap_look_up` | C | Attempt on successful lookup | `mach_port_deallocate(mach_task_self(), svc)`, result ignored | Send to looked-up service | Source-only; no right-count control | No explicit port-transfer action | O |
| S34a | Exec stdout/stderr read endpoints | `exec_resources_acquire`: two `pipe` calls | C | One attempt | `exec_resources_release`, including partial setup/spawn failure | Read child output | Source-only; IC/CLI successful captures, no deny run here | No: explicit addclose and `CLOEXEC_DEFAULT` | P |
| S34b | Exec stdout/stderr write endpoints | `exec_resources_acquire`: two `pipe` calls | C | Until successful spawn in worker; child lifetime may extend | Worker closes after spawn; setup/spawn failure releases; child exit closes own refs | Child output channel | Source-only; IC/CLI observed streams | Yes, duplicated as 1/2; originals explicitly closed | P |
| S35a | Exec file-action heap handle | `exec_resources_acquire`: init, addopen/dup2/close | C | One attempt | `exec_resources_release` destroys initialized handle | Select child descriptors, including `/dev/null` | Source-only Apple malloc/realloc path; row 6 | Handle no; action effects yes | P |
| S35b | Exec attribute heap handle | `exec_resources_acquire`: init/setflags/setpgroup | C | One attempt | `exec_resources_release` destroys initialized handle | Child fd isolation and process-group choice | Source-only Apple malloc; row 6 | Handle no; flags/group effects yes | P |
| S36a | Exec child PID/process | `attempt_exec_spawn`: `posix_spawn` | C | Attempt normally; unconfirmed reap may outlive it | Wait observation, conditional group kill, bounded nonblocking reap | Execute requested target under inherited sandbox | IC/CLI observed spawn/exit; source-only failure lifetimes | This is the child; it can spawn descendants | O; row 10 |
| S36b | Child process group | Exec spawn attributes `SETPGROUP`, pgroup 0 | C | As long as members remain, possibly beyond attempt/worker | Conditional group kill request, not an absence proof | Cleanup addressing for members that remain | Source-only; lifecycle cases inspected, not rerun | Yes to descendants unless they leave group | P; row 10 |
| S37 | Static extension handle and native extension state | `attempt_extension`: consume result other than -1 | C | Across attempts/phases; requested release is not proven revocation | Explicit release action once if submitted/eligible; no automatic exit-time release call; OS teardown | Native extension access represented by handle; exact kernel state unobserved | Source-only; rows 8–9 | No admitted exec+extension plan | A + O, row 17 |
| N1 | Issuer-channel high duplicate `spawnFD` | E: `fcntl(F_DUPFD_CLOEXEC, 64)` | A | Through E initializer | E defer close; fd 3 duplicate lives in issuer | Collision-free delivery of token channel | Source-only | No: issuer sibling, duplicate close-on-exec | A |
| N2 | Issuer spawn file-action handle | E: init, `adddup2`, three `addopen` | A | Through E initializer | E defer destroy | Channel/stdio selection | Source-only; unchecked init result, row 19 | No worker memory inheritance | P |
| N3 | Issuer spawn attribute handle | E: init and `setflags(CLOEXEC_DEFAULT)` | A | Through E initializer | E defer destroy | Issuer fd isolation | Source-only; unchecked init result, row 19 | No worker memory inheritance | P |
| N4 | Issuer stdio `/dev/null` descriptors 0/1/2 | E: `posix_spawn_file_actions_addopen`, executed by native spawn | A | Issuer lifetime | Issuer exit | Read EOF/write discard | Source-only, issuer outside specimen sandbox | No: issuer creates no child | P |
| N5 | Host copied launch argument strings | `withCStringArrayCopy`: `strdup` for H/E invocations | A | Spawn call only | Helper defer `free`; Swift array lifetime | Transfer launch arguments, not token bytes | Source-only; allocation failures not explicitly refused | Arguments copied into new images, host pointers not inherited | P; setup caveat row 19 |
| N6 | Host policy byte array and request-population temporary arrays/data | H: `Array(input.policy.utf8)`, `writeString`, `captureNonceBytes` | A | Transfer/population scope; input objects may live through run | Swift scope/ARC, not worker teardown | Exact delivered inputs and nonce | Source-only; Swift allocation internals unobserved | No host memory inheritance | P |
| N7 | Host target-resolution buffer/metadata and issuer record | E: `[CChar]`, caller-buffer `realpath`, `fstatat`, strings/record | A | Through preparation; record survives into reply | Swift scope/ARC | Resolve token target before worker starts; metadata is host evidence | Source-only; no target fd held by PW call site | No | A + E, row 17 |
| N8 | Worker main-frame arguments, timing state and capture nonce | W local declarations, `pw_clock_start`, nonce `memcpy` | A | Main frame until exit; timing changes across phases | Process exit (main never returns after successful apply) | Operate release/timing protocol; no new access handle | Source-only; stack mapping visible in L | No: new exec image | P |
| N9a | Worker temporary pre-compile call frames | `parse_args`, `map_region`, `read_all_from_fd`, `pw_timing_setup`, `prepare_extension` | A | Call only | Return or process exit; no claim of byte erasure | None beyond existing pointers/rights | Source-only; native library internals unobserved | No: exec replaces stack | P |
| N9b | Capture hash/view/digest/sorting call frames | `pw_capture_profile`, `pw_consumed_params_digest`, `pw_read_memory` | B | Call only | Return or process exit; no claim of byte erasure | Read own memory with existing task right | Source-only; qsort/CommonCrypto internals unobserved | No: exec replaces stack | P |
| N10 | Attempt-local stack buffers, argv pointers, polls, wait status and metadata | `run_attempt` and each `attempt_*`, `capture_observed_path`, `drain_one`, `exec_resources_acquire` | C | Call/attempt only; output copied into S18 | Return or process exit | Use already inventoried target/child handles; no separate authority | Source-only; compiler stack/page behavior unobserved | `argv_local` strings copied; stack not inherited | O + P (working/observation storage), row 17 |
| N11 | Post-apply outside-attempt automatic diagnostics and seam timespec | `wait_for_proceed`, `proceed_refused`, W post-phase seam | D | Call, or nonreturning refusal frame until exit | Return/exit; not dynamically allocated by PW | None; diagnostic/control working storage | Source-only | No child spawned on these paths | P |
| N12 | Exec child stdin `/dev/null` fd 0 | `exec_resources_acquire` registers `addopen`; native spawn executes it | C | Child lifetime | Child closes it or exits | Read EOF without exposing policy pipe | IC/CLI observed EOF; no independent gating probe here | Yes, explicit child fd 0 | P |
| N13 | Libc diagnostic state reachable after apply | `fail_from_errno`, `exec_setup_failed`, `attempt_exec_spawn`, `attempt_mach_lookup`, `run_attempt`: `snprintf`, `strerror` | C | Library-dependent; ordinary errno table is static, fallback buffer retained | Library/exit; no PW-owned handle | Diagnostic formatting; hidden allocation/locale behavior bounded only by source studied | Source-only Apple paths; installed-library internals unobserved, row 6 | Library memory not carried across exec | P |

### Launch-inventory observation (rows 1 and 11)

The completed observation uses two production workers under the same empty
allow-default specimen: one held by the post-apply hang seam, the other by the
pre-ready seam. `lsof -p` and `ps -E -p` provide the baseline descriptors and
environment display; same-user `vmmap` succeeds and `lsmp` fails to obtain the
task port. The evidence ledger records exact commands, inputs, identities,
results and the source/timing basis for the seams.

The [contaminated-worker case](../tests/suites/runner_exec_inheritance/README.md#contaminated-worker)
is the positive control: its parent-supplied descriptor and environment value
reach the worker's exec chain. A production host's observed empty environment
or absence of extra descriptors is consequently a finding about those launches,
not a guarantee of the instrument's general inheritance policy. The pinned
xnu null-env extraction path corroborates the observed empty environment.

## Register

Pass 1 rechecks the survey at `6fd44fb`. Rows 8 and 10 retain their existing
adjudications. All other rows below await the user's decision: recommended
wording is a candidate for adjudication, not an accepted limitation or a closed
row. No production fix is authorized by this pass. Rows 15–19 are new.

| # | Candidate | Pass 1 evidence | State | Recommended disposition / existing adjudication |
| --- | --- | --- | --- | --- |
| 1 | Worker launch has a different inheritance contract from exec children | H has no close-by-default attributes; nil envp is empty in the examined Apple path and L; L observes fds 0–4, IC demonstrates an extra inherited descriptor/environment value | awaiting adjudication | Explain the launch rule and bounded observations; consider explicit descriptor isolation as a separate fix, not something L proves unnecessary |
| 2 | Policy, evidence and readiness descriptors remain open | W has no close of 0/3/4; L observes all three before/after apply; child controls exclude inherited endpoints | awaiting adjudication | Explain retention; do not claim that closing these would leave only attempt fds, since stdio/ambient inheritance remains |
| 3 | `open_write` truncates on open and attempts an unchecked write | `attempt_file_open_write` uses `O_TRUNC`, discards write/close results and reports open success | awaiting adjudication | Correct guide/tour wording to distinguish attempted byte write from an observed write; no behavior change recommended |
| 4 | `open_read` reports open success only | One-byte read and close are attempted without retaining returns | awaiting adjudication | Correct guide/tour wording; contrast published `read_fresh` observations |
| 5 | `create` opens existing files and supplies a masked creation mode | No `O_EXCL`/`O_TRUNC`; mode argument 0600, subject to inherited umask; existing-file checker asserts bytes/identity | awaiting adjudication | Explain intended open/create behavior and scope mode claim to the supplied argument |
| 6 | Exec preparation allocates after apply; formatting needs a narrower account | Apple spawn wrapper allocates both handles and can grow action storage; fixed PW diagnostic destinations do not establish library-wide allocation freedom | awaiting adjudication | Explain per-attempt allocation and diagnostic call boundary; keep architecture's already-scoped preallocation claim; correct stale comments via row 7 |
| 7 | Source comments state retired or overbroad premises | Stack/static, last-allocation, no-allocation, R5/R6 and Swift-worker comments remain; main also says every write checks its return and misdescribes fatal-signal interpretation | awaiting adjudication | Correct source comments in an adjudicated source commit with identity regeneration/build/identity validation |
| 8 | Ownership of private-extension limitation | Existing architecture paragraph and intended worker-tour location rechecked | implementing | Adjudicated: WORKER.md owns it; ARCHITECTURE links there, in pass 3/integration |
| 9 | Native release does not establish revocation; an after-release read is nevertheless observed | Checker accepts either after-release result and verifies bytes if successful; seed's “nothing observes” wording was too broad | awaiting adjudication | Keep accepted private-API scope from row 8 and correct the candidate sentence; no new universal revocation assertion |
| 10 | Exec descendants can outlive the worker/run | Group targeting and possible unconfirmed reap verified; existing accepted descendant limit remains | implementing | Adjudicated ownership move; preserve accepted scope and distinguish worker-death/unreaped-child paths |
| 11 | Ambient worker state is only partly inventoried | L observes cwd, uid/gid, fds, argv/environment and VM regions; task-port census refused; signal mask/limits/private internal state unobserved | awaiting adjudication | Explain measured starting substrate; accept explicitly bounded observation as a limitation if desired; no empty-process claim |
| 12 | Ignored SIGPIPE reaches exec children; extension-specific core-limit inheritance is unreachable in admitted plans | Spawn sets neither signal reset flag; `extensionMeaningFailure` refuses exec+extension; helper's own SIGPIPE ignore prevents independent signal evidence | awaiting adjudication | Explain signal inheritance, correct the seeded extension-to-exec claim, and reserve a signal observer for any requested stronger guarantee |
| 13 | Extension requests can change worker core limits before apply | `prepare_extension` sets both limits to zero only after requested extension symbols resolve; local failure is published | awaiting adjudication | Explain request-dependent process context and native failure branches; no change recommended |
| 14 | Worker-side token erasure is path-dependent | Proceed refusal/spin, cancellation exit, compile/parameter/apply failures and early returns can bypass post-loop erase; host `erase` is separate | awaiting adjudication | Explain exact worker/host erasure sites, including accepted mapping retained until exit; any extra worker erase requires a separate fix |
| 15 | Mach lookup retains the acquired bootstrap reference | `task_get_special_port` succeeds before lookup; only `svc` is deallocated, including on repeated lookup/failure paths | awaiting adjudication | Fix worker reference balance with success/failure and repeated-attempt regression controls; until then state retention |
| 16 | Compiled-object lifetime has no explicit PW destruction | `profile` goes to capture/apply and no `sandbox_free_profile` is declared/called; private apply ownership is unobserved | awaiting adjudication | Explain the call/ownership boundary; investigate API ownership before authorizing a free, which could otherwise be invalid |
| 17 | Several resources cross the proposed role boundaries | Token mapping carries authority and protocol metadata; native extension acquisition occurs inside an attempt; shared working storage and signal state have multiple purposes | awaiting adjudication | Keep these resources outside single-role clusters, with named roles; do not force all inventory rows into one cluster |
| 18 | Oversized issuer token erasure covers a bounded prefix | I computes bounded `strnlen`, rejects oversize, erases that length and frees; no full allocation extent is established | awaiting adjudication | Correct erasure scope and investigate safe full-buffer disposal before a fix; accepted-token path remains distinct |
| 19 | Host/issuer launch setup does not check every acquisition/setup return | H ignores file-action init/adddup2 results and shm flag/unlink results; E ignores handle init results; copied argv can contain nil after failed strdup | awaiting adjudication | Strengthen verification and explicitly refuse failed setup if adjudicated; source identifies unchecked paths, not a reproduced production failure |

### Row details

Every detail below records a candidate sentence, implementing evidence and
its limits, a possible refutation/control, and the recommendation. No new row
has an adjudication, implementation or validated after-change sentence yet.
Those fields remain pending at this pass's stop; revised candidate sentences
are not silently treated as closed rows.

**Row 1.** First candidate: “The worker's launch is not isolated the way its
children's are.” The desired claim is an exact launch inventory. H's three
mandatory and one optional `adddup2` actions coexist with native inheritance
of other non-close-on-exec descriptors. The original evidence descriptor has
its close-on-exec bit cleared; if its number is neither overwritten nor 3 it
can also survive under its original number. The two L workers had only fds
0–4; 1/2 were `/dev/null`; cwd was `/`. Plain and environment-displaying ps
outputs matched exactly, with the expected nonempty worker argv. The pinned
Apple `posix_spawn` wrapper forwards envp unchanged; `exec_extract_strings`
initializes `ip_envc` to zero and never enters its environment loop for a null
pointer. This supports empty nil-env behavior at the examined implementation,
not a portable POSIX promise. IC explicitly observes a canary environment and
inheritable fd at least 200 in the process that execs the worker, then checks
three children; CLI checks three ordinary children. Neither control asserts
that a production worker always has only five descriptors. A different host
fd inventory refutes a universal five-fd claim; it does not refute the native
inheritance rule. Recommended: explain the rule, measured configuration and
lack of an exhaustive isolation guarantee; an explicit worker launch policy
would be separate implementation scope. Candidate after adjudication: “The
host supplies the worker's protocol endpoints and leaves other descriptors to
native close-on-exec rules; the examined nil environment yields no entries.”
Exact inputs, observations and paths are in the pass 1 evidence ledger below.

**Row 2.** First candidate: “Descriptors 0, 3 and 4 stay open from launch
to exit; descriptor 5 is closed once the channel is mapped; exec children
inherit none of them.” W and `prepare_extension` establish the call sites;
L confirms 0/3/4 at both seams, IC/CLI establish child-side fd isolation.
Descriptor 5 is also closed on preparation rejection, while early main
refusals precede preparation and leave it to process exit; close failure is
reported rather than retried. Policy EOF and the closed readiness reader do
not destroy the worker's references. Refutation: a close/use omitted by this
reading or an observed child reference. Recommended: explain existing
retention. The seed's suggested alternative sentence, “after apply the worker
holds only the descriptors its attempts open,” is false even if 0/3/4 are
closed: it omits inherited stdio and row 1. No removal is authorized. The
proposed wording names cleanup calls and early-exit exceptions instead of
promising successful close on every path.

**Row 3.** First candidate: “`open_write` opens the target for writing,
truncates it to zero length and writes one byte, and reports only the open
result.” Source confirms the truncating open and a one-byte `write`, not a
successful byte transfer. The seed's proposed refutation, a final length other
than one, would not disprove that implementation: the unchecked write can
fail, and target type/external writers matter. The guide's attempt-kinds entry
omits truncation. Recommended candidate: “`open_write` calls a truncating
write-open, then attempts to write `x` and close the descriptor; its reported
status is the open result.” A deterministic controlled failed-write return
would falsify a stronger “one byte was written” claim; no probe is needed to
establish that the return is discarded. Guide/tour correction awaits decision.

**Row 4.** First candidate: “`open_read` opens the target, reads one byte
and discards it, and reports only the open result; `read_fresh` records what
it read.” `attempt_file_open_read` issues the read, but an empty file, error
or interrupted read need not produce a byte. Recommended candidate says
“attempts a one-byte read, discards its return, and attempts close.”
`attempt_file_read_fresh` separately records open/stat/read/close results and
bounded bytes. The extension checker checks identity and bytes for its during
read; that is narrower than general file semantics and was inspected, not
rerun. A failed-read control would refute any upgrade from open success to a
read observation. Source settles the present publication difference.

**Row 5.** First candidate: “`create` opens an existing target for writing
without truncating it, and creates a missing one with mode 0600.”
`attempt_file_create` supplies `O_WRONLY | O_CREAT` and mode 0600, without
`O_EXCL` or `O_TRUNC`; inherited umask can reduce the created mode. The
`witness_contract/create_existing_file_preserves_contents` checker snapshots
bytes and device/inode before/after allowed and denied write-open attempts;
it neither checks every file type nor the new-file mode. Inspected only.
Recommended candidate names the open flags and mode argument, with umask,
and explains that success can mean opening an existing file. A changed
identity or contents in that controlled case would refute preservation.

**Row 6.** First candidate: “Exec attempts allocate after apply at
PolicyWitness call sites.” `exec_resources_acquire` calls both opaque-handle
initializers inside `run_attempt`, checks their results and destroys only
initialized handles along setup failure, spawn failure and normal cleanup.
The SDK's `spawn.h` declares both types as `void *`. In pinned Apple xnu
`posix_spawn.c`, `posix_spawnattr_init` and `posix_spawn_file_actions_init`
call `malloc`; `_posix_spawn_file_actions_grow` uses `realloc` when needed.
The ordinary worker supplies an addopen, two dup2 and four close actions; the
claim is possible action-storage growth, not that a particular allocation
count was measured. `runner_c_worker_harness/exec_setup_post_apply_denied`
asserts that setup reaches spawn under its denying profile;
`runner_c_worker_harness/exec_pipes_per_attempt` exercises the descriptor ceiling. Those checks
were inspected, not rerun, and do not count heap allocations.

The pinned libc path is `snprintf` → `vsnprintf_l` → `_vsnprintf` →
`__v2printf` → ordinary `__vfprintf`. The string destination and FILE wrapper
are caller/stack storage. The examined ordinary integer/string format paths
are distinct from allocating wide-string, vector and positional-argument
paths. `strerror` returns a static table entry for known errors in a non-NLS
build; its fallback lazily allocates a retained buffer. The NLS conditional
path can open a message catalog. Thus a blanket “formatting always allocates”
is also unsupported. These are published-source conclusions, not a match of
Apple's source release to every instruction in the installed shared cache;
allocator, locale, lazy binding and private extension internals remain
unobserved. The imported xnu version differs from the running kernel patch
version. The exact pinned sources and local SDK header hash are retained.

The architecture principle already scopes preallocation to PW request,
evidence and token storage and explicitly puts exec handles after apply; it
survives this review. Recommended: explain the known handle allocations,
name libc call boundaries without a universal allocation promise, and fix the
stale no-allocation comments under row 7. A wrapper implementation without
those allocations would refute the source-specific allocation assertion;
measuring one allocation-free invocation would not establish a library-wide
promise. No allocation probe was needed or run.

**Row 7.** First candidate: “Worker source comments describe retired
premises.” Confirmed items: header's stack-fixed buffer and last-allocation
claim; attempt-section stack-only/no-allocation/R6 language; R5 declaration
comment; two Swift-worker references. The main SIGPIPE comment also claims
every write checks its return, contradicted by `open_write`, and describes a
fatal signal as a sandbox-denial source of truth. The exec setup comment's
unqualified attribution language outruns its cited Darwin measurement.
H's page-touch comment invokes R8 and states that host touching prevents
post-apply faults; host touching does not by itself prove the worker's page
tables/residency. These are leads, not behavioral proof. Recommended: one
adjudicated source-comment correction naming the exact current behaviors and
bounded controls. No behavior test validates historical prose; identity
regeneration, signed build and identity agreement are required for any source
edit. Neither source comments nor worker identity have been edited in pass 1.

**Row 8.** First candidate: “Two documents will state the private-extension
limit.” The existing architecture paragraph separates PW buffer erasure from
private allocation/retention, kernel state, identity, permissions and
revocation. Existing adjudication remains: move ownership to WORKER.md in
pass 3 and link from ARCHITECTURE. Validation will check paragraph ownership,
links and the Known gaps index. No move or after-sentence exists in pass 1.

**Row 9.** First candidate: “A successful release returns zero; nothing in
PolicyWitness observes whether access is revoked afterward.” The latter
clause is too broad: `check_extensions.py` retains the after-release fresh
read, accepting either result and checking the bytes on success. It does not
require revoked access, and a denial in one read would not by itself establish
kernel extension state or universal revocation. `attempt_extension` publishes
the native return without resetting the static handle; `release_decided`
prevents a second release. Recommended candidate: “The worker publishes the
native release result and subsequent requested access observations; a zero
release result is not an access-revocation observation.” Keep this within
row 8's accepted private-API scope, subject to the user's row 9 adjudication.
No new revocation assertion or live extension run was made.

**Row 10.** First candidate: “Exec helpers can outlive the worker.”
`attempt_exec_spawn` addresses the child's process group on exceptional
cleanup and retains leader ownership with WNOWAIT before reaping. It records
unconfirmed reap instead of inventing exit. Worker death can prevent cleanup;
descendants can leave the group. H supervises the worker, not the entire exec
tree. The lifecycle suite independently observes processes for its exercised
cases; it does not establish general tree containment. Existing adjudication
accepts the architecture's escaped-descendant limitation and moves its
paragraph in pass 3. Inventory S36 separates child, group and pipe lifetimes;
additional prose must not expand the existing acceptance into an unreviewed
claim that every child is cleaned up or every descendant is observed.

**Row 11.** First candidate: “The worker's ambient resources are
uninventoried.” L establishes a bounded census: descriptors, cwd `/`, uid 501,
gid 20, nonempty launch argv, no displayed environment additions, and readable
VM maps showing executable/library mappings, malloc regions, shared regions
and one listed main stack. It does not assign every VM region to a PW call,
prove an exhaustive thread census, or observe all effective authority.
`lsmp -p` returned 1 with `task_for_pid` failure for both signed workers;
no root escalation or modified signature was used to expand that boundary.
Signal masks, limits, exact Mach rights and library internal state remain
unknown. Recommended: explain the received substrate and, if accepted, record
the observation boundary as a Known gap. A readable independent right census
would extend the observation, not retroactively make this one complete. The
pre-ready and post-apply specimens use distinct workers, so VM address or size
differences are not within-process changes. No subtraction of them is claimed.

**Row 12.** First candidate: “Exec children inherit the worker's ignored
SIGPIPE and its zero core-dump limit.” The SIGPIPE portion follows W's
`signal` and absence of `POSIX_SPAWN_SETSIGDEF`/`SETSIGMASK` in
`exec_resources_acquire`; native exec preserves ignored dispositions and the
mask. The core-limit portion needs correction: [`extensionMeaningFailure`](../runner/Sources/PWRunnerCore/ProbeRunner.swift)
rejects extension declarations with exec probes, before worker creation.
The request-contract fixture `extension_exec` expects
`extension_exec_unsupported` from both admission paths. A directly constructed
ABI plan could mix them, but that is not admitted production behavior.
IC/CLI inspect only environment/fds; their helper ignores SIGPIPE itself, so
neither can prove inherited SIGPIPE. Recommended: explain the signal rule and
inherited ambient limits, with the extension/exec exclusion explicit. A helper
that reads disposition/mask before modifying them would test that narrower
claim if stronger verification is desired. The guard and fixture are source
review, not a freshly executed admission case.

**Row 13.** First candidate: “The core-dump limit differs between extension
and non-extension runs.” `prepare_extension` returns before symbol resolution
and `setrlimit` when no extension is requested; missing symbols also return
without setting limits. With requested/resolved APIs it sets both limits to
zero before mapping any token; failure publishes local setup evidence and
closes any supplied descriptor. Thus the positive source claim is a
conditional intervention, not that every non-extension worker has nonzero
limits. Recommended: explain that intervention and unknown inherited values.
A native limit read before/after preparation would refute any unconditional
numeric difference; source already settles the conditional call, so no probe
was added. Admission prevents this request-dependent change reaching ordinary
exec attempts in the same specimen (row 12).

**Row 14.** First candidate: “The normal-completion token erase is skipped
on the proceed-refusal path.” Confirmed `proceed_refused` and timeout/future
release paths publish done and enter `spin_for_exit`; cancellation calls
`_exit` directly. The post-loop erase is also unreachable after parameter,
compile or apply failure, and early main validation/read failures can occur
after `prepare_extension` mapped a token. `attempt_extension` erases after
its consume decision if it returns; a death during the native call can prevent
that erase too. Accepted mapping remains mapped after erasure until exit.
H's session erasure after driver return and E's deinit are separate owners,
not evidence that the worker executed its normal erase. Controlled extension
fixtures exercise interruption/erasure at selected call boundaries; they do
not cover every early-return branch. Recommended: explain these exact sites
and exceptions. A future worker-erasure guarantee needs a controlled refusal
before consume with independent channel-byte observation; not run because
source already decides the absent call. No change to release/wait logic.

**Row 15.** First candidate: “A Mach lookup attempt drops its acquired
service right but retains the bootstrap send-right reference it obtained,
including when the service lookup fails.” `attempt_mach_lookup` calls
`task_get_special_port`, returns immediately on failed lookup, and deallocates
only `svc` on success. A preexisting bootstrap port name does not eliminate
the acquired user reference. No cited current checker inspects its reference
count. Recommended: fix balanced release on both paths, with a test that
checks native acquisition/deallocation and a repeated-attempt reference count
where observation is available. This is a source finding; no leak size, port
exhaustion or experiment effect was measured. A demonstrated transfer rule
without an owned reference or an omitted matching release would refute it.
Until adjudicated, S33a records retention rather than hiding it in “attempt
only.”

**Row 16.** First candidate: “The compiled profile is retained until worker
exit.” That allocation-lifetime sentence exceeds the visible source:
`sandbox_apply` is private and may have ownership behavior not established
here. What PW itself does is keep the returned pointer, optionally read the
profile, call apply and make no explicit free call. The compiler error string
on the null-profile branch and SandboxParams do have explicit cleanup.
Capture's bounded read tests readability before apply, not ownership after
apply. Recommended: state that exact call chain and retain the internal
ownership uncertainty; investigate before adding any free. An API ownership
contract or independent native lifecycle observation could resolve it. The
absence of a PW call is source-decided; no heap-probing experiment was needed
to avoid an unsupported lifetime promise.

**Row 17.** First candidate: “Every resource belongs to one experimental
role.” The channel object/mappings carry both bearer bytes and admission or
issuer publication metadata; the consume result is deliberately supplied
authority acquired by an attempted operation; SIGPIPE state changes reporting
survival and child context. Attempt stack storage supports both the native
operation and its observation. Host target resolution is preparation for
supplied authority and an external observation. Recommended: retain the
resource/alias distinctions and name multiple roles outside clusters; ordinary
ambient execution substrate belongs outside the three experimental roles
under row 11. No duplication of an object solely to force a single role.
A resource-level decomposition with truly distinct columns can justify a
split; a color assignment cannot refute dual use. Validation in pass 2 will
review actual node/edge statements, not just SVG generation.

**Row 18.** First candidate: “The issuer erases the token before freeing
it.” I uses `strnlen(token, PW_EXTENSION_TOKEN_BYTES)`, then erases that many
bytes and calls `free`. For an accepted bounded string, all non-NUL bytes are
erased; for an oversized result, bytes beyond the scan bound are not covered.
A missing terminator within the bound is rejected, but the allocation's total
size is not learned. Existing worker-channel oversized-token controls exercise
channel admission, not the issuer's full native allocation disposal. Recommended:
state prefix erasure accurately and investigate a safe native ownership/length
contract before choosing a full-buffer disposal fix or accepting the limit.
A controlled issuer API returning a longer known allocation, with erasure
observed before free, would refute a full-erasure claim; source settles the
present bounded call. No sensitive token bytes were collected in this pass.

**Row 19.** First candidate: “The host prepares the worker's protocol
resources and refuses every failed setup before spawn.” H ignores the return
of file-action initialization and additions, unlike the C exec path; its shm
unlink/close-on-exec-clear calls are also unchecked. E checks action-add and
attribute-flag returns but ignores both handle initializations.
`withCStringArrayCopy` silently inserts a nil for failed strdup. Descriptor
actions are ordered against live numbers; H protects the optional token
source with a high duplicate but does not relocate all three other sources
before overwriting destinations. Source establishes those choices, not that
the observed host used colliding descriptors or experienced allocation
failure; L's normal launch passed. Recommended: strengthen failure/collision
verification and refuse explicit setup errors if adjudicated. A regression
control must induce the exact failure and check no unintended spawn plus
resource cleanup; a low-fd control must establish actual source/destination
collision rather than infer it from a label. No production fix or injected
failure run in pass 1. Candidate wording names requested actions and their
unchecked returns pending the decision.

### Pass 1 branch and completeness audit

- Host setup: follow shm create/unlink/flag/size/map, each pipe prerequisite,
  token duplication, spawn setup/argv, spawn failure, transfer failure,
  readiness timeout, sentinel/phase waits, worker cleanup and final collection.
  Host-side Swift objects/copies stay outside the worker. E's partial-init
  returns still reach deinit for held descriptor/mapping; issuer delivery
  requires the observed clean reap, not merely a published token.
- Worker admission before extension preparation can exit with inherited
  descriptors intact. After preparation, parameter/header/clock/read/length/NUL
  refusals can exit with the accepted mapping; params/compile/apply failures
  can publish done and spin. No general worker teardown path frees all resources
  before exit. Profile, error string, parameters and channel lifetimes are
  deliberately separate rows.
- Attempt dispatch covers none, all file actions, Mach, sysctl, exec and
  extension consume/release, plus unsupported-kind diagnostics and the
  kill-before-publication seam. Exec setup rollback, spawn refusal, observation
  failure, group signalling and unconfirmed reap were traced separately.
  Closing capture fds does not establish child/group absence.
- `unlink` and `access` acquire no PW-owned handle. `sysctlbyname` writes its
  result into a stack buffer; its libc name-translation internals remain
  unobserved. `mach_timebase_info`, `mach_continuous_time`, `getpid`, and
  `fcntl(F_GETPATH)` return metadata/values, not new owned handles at these
  call sites. Their local storage is covered by N8–N11; calling them is not
  proof that all library/kernel internals are allocation-free.
- After apply outside an attempt, `wait_for_proceed` uses atomic publication,
  local arithmetic/text, continuous-clock reads and CPU relax; cancellation
  exits. The post-loop erase uses volatile stores; the two seams call
  `nanosleep`/`kill`; done publication and `spin_for_exit` use stores/loads,
  CPU relax and `_exit`. No explicit PW dynamic allocation, descriptor, port
  or process acquisition was found there. Automatic call frames (N11) and
  unobserved native internals qualify the seed's “no acquisition” sentence.
- The worker image, main frame and temporary call frames are storage received
  or reused, not new mappings created for each C local. N8–N11 describe those
  views so stack use and capture hashing/sorting do not disappear from the
  inventory. Library-internal state remains explicitly outside call-site
  completeness. The validator, host evidence readers and log collector will
  supply pass 2's external-evidence nodes; they are not worker acquisitions.

### Pass 1 evidence ledger

**Source and build.** Production snapshot:
`6fd44fb15397678d29f0f96bfee2b1abbe4bbbb6`, clean at signed build time.
Build command: `PATH=/opt/homebrew/opt/rustup/bin:$PATH make build
IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'`.
The first sandboxed attempt stopped at keychain identity discovery (exit 2);
the same command passed outside the automation sandbox. Build 692 records
`v0.3.1-8-g6fd44fb`, `dirty: false`, worker identity
`33890392b9337f128a06b89b7d831192e5e8d809f0a5f41613e8745c2d9c9eb9`.
This was an incremental signed build under the validated toolchain, not a
fresh-cache or reproducibility claim. No worker/host source changed in pass 1.
The app's before/after test inventories match and its initial inspection
passed. The retained build transcript, manifest, provenance, source hashes and
probe script copies live in the final run's `pass1-evidence/` attachment.

**Environment.** macOS 26.7.1 (25G241), Darwin 25.6.0, arm64;
running kernel `xnu-12377.161.15.700.19~2/RELEASE_ARM64_T8142`.
The configured SDK is MacOSX27.0.sdk. Observers ran as uid 501, gid 20,
outside the automation sandbox, against unchanged Developer ID signed workers.
No BYOXPC installation, root task inspection, signature relaxation or native
worker instrumentation was used.

**Execution.** The final dispatcher command was:

```sh
PW_TEST_OUT_DIR=tests/out/runs/worker-p1-launch-final \
  tests/run.sh --case runner_exec_inheritance/launch_inventory \
               --case runner_exec_inheritance/cli
```

The dependency adds `runner_exec_inheritance/contaminated_worker`.
All three canonical cases passed, with zero failures/skips and unchanged app
inventory, run ID `20261017T215334Z_b7815087`. The earlier
`tests/out/runs/worker-p1-launch` run (ID
`20261017T215100Z_abd6b891`) also passed all three; the final run adds explicit
readiness, reaping, collection-basis and wait-error assertions. The final run
is the credited observation. Both are retained; no earlier evidence was
rewritten into the final assertion result.

| Case / input | Expected observation and possible refutation | Actual result | Evidence within the final run |
| --- | --- | --- | --- |
| `runner_exec_inheritance/launch_inventory`, pre-ready: schema 5, empty `probe_plan`, `(version 1)(allow default)`, only `worker_pre_ready_hang_ms: 20000`; CLI flags `--no-log-capture --timeout-ms 45000` | Newly observed worker PID matches final report, mandatory observers succeed before hold ends, ready wait expires and later write reports EPIPE, worker completes/reaps. Extra fd/env entries are findings, not failures. Missing observer output or PID mismatch refutes the census | Worker 38775, host 38774; fds 0/1/2/3/4; 1/2 `/dev/null`; 0/4 pipes; 3 evidence PSXSHM; cwd `/`; plain/`-E` argv identical. vmmap rc 0; lsmp rc 1. Final ready write rc -1/errno 32, completion and exit 0/reap | `suites/runner_exec_inheritance/launch_inventory/artifacts/pre_ready/`: exact `specimen.json`, `run.json`, `capture.json`, `identity.stdout`, `descriptors.stdout`, `argv.stdout`, `environment.stdout`, `mappings.stdout`, `ports.stderr`, command JSONs and `worker-after.*` |
| Same case, post-apply: same policy/empty plan, only `worker_post_apply_hang_ms: 20000` | Same census checks, successful readiness and normal completion/reap; failure to capture an identified live worker would refute the observation | Worker 38829, host 38828; same numeric fd set and endpoint classes, cwd and displayed empty environment. vmmap rc 0; lsmp rc 1. Ready rc 0, completion and exit 0/reap | Same case's `artifacts/post_apply/`, with the same exact-input, raw-output and command records |
| `runner_exec_inheritance/contaminated_worker`: existing ABI harness and shared observer; random env nonce and fd at least 200 containing 32 random bytes; three exec attempts | Same PID launch report must contain exact nonce/canary; all children must report explicit empty env, only fds 0/1/2, stdin EOF and separate stderr markers. A missing/unclean report fails, rather than standing for absence | Passed: launch contamination confirmed, all three children isolated | `suites/runner_exec_inheritance/contaminated_worker/artifacts/`: `harness.jsonl`, `harness.stderr`, `observations.json`, build logs and `assert.log` |
| `runner_exec_inheritance/cli`: existing allow-default specimen with three nonce-tagged helper execs | Each child reports complete env/fd/stdin inventory, its own identity/nonce and retained stdout/stderr; all three PIDs distinct | Passed all three ordinary exec observations | `suites/runner_exec_inheritance/cli/artifacts/`: exact `specimen.json`, envelope, stderr, observations and assertion/build logs |

Boundary placement uses the production seam's source order and observation
timing; it is not an independent live read of the applied flag. Final success
and override echoes alone would not prove when the observer ran, so elapsed
time, process identity, actual sleep-state listing and readiness behavior are
retained as well. The two captures are separate processes, not before/after
snapshots of a single worker. L's VM reports give accessible mappings, not a
call-site allocation trace. Port observer failures remain unavailable rights
evidence. No ordinary file, Mach, extension, mutation-barrier or allocation
case was freshly executed for this pass. Source-only conclusions and inspected
checkers above are not credited as live observations.

**Pinned Apple source reading.** Retrieved on 2026-10-17; downloaded copies and
SHA-256 hashes accompany the evidence attachment. The SDK header and published
sources corroborate the call contracts; the published xnu revision is not the
running kernel patch revision and libc is not an authenticated reconstruction
of the installed shared cache.

- Apple xnu `f6217f891ac0bb64f3d375211650a4c1ff8ca1ea`
  (import `xnu-12377.1.9`):
  [posix_spawn.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/spawn/posix_spawn.c)
  for handle allocation/destruction and unchanged envp forwarding;
  [kern_exec.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_exec.c)
  for the zero-count/null-env extraction path;
  [ipc_tt.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/kern/ipc_tt.c)
  for the copied bootstrap send right returned by the special-port path.
- Apple Libc `71bbe350ab79eef58113991d817ccc6165061a64`
  (import `Libc-1752.100.10`):
  [snprintf.c](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/stdio/FreeBSD/snprintf.c),
  [vsnprintf.c](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/stdio/FreeBSD/vsnprintf.c),
  [xprintf.c](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/stdio/FreeBSD/xprintf.c),
  [vfprintf.c](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/stdio/FreeBSD/vfprintf.c)
  and [strerror.c](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/string/FreeBSD/strerror.c)
  for caller/stack destinations, the ordinary formatting route and conditional
  allocation paths. No claim of an allocation-free installed libc follows.

Apple's archived [posix_spawn manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/posix_spawn.2.html)
corroborates descriptor, signal-disposition/mask, cwd, umask and resource-limit
inheritance rules used in rows 1, 11 and 12. It is an API account, not a live
signal or limit observation.

**Pass validation.** Worker identity check passed with no regeneration;
Python syntax, shell syntax and `git diff --check` passed. The six
`source_drift` cases passed across the initial run and its targeted correction:
`worker-p1-drift` (ID `20261017T220422Z_3bb718d3`) passed source manifests,
limits, contract, architecture and build-documentation cases; its generator
contract failed on the evidence table's bare timeout duration. Replacing that
prose with the actual CLI argument required no baseline exception.
`worker-p1-drift-final` (ID `20261017T220854Z_4dbe7939`) reran
`source_drift/generator_contract` successfully. Both results are retained.
No generator input changed; generated copies were checked, not hand-edited.
The inventory also passed a structural check for 78 unique IDs and all ten
nonempty columns.

The retained source attachment was collected after execution. The observer,
control scripts and production sources match those executed; the catalog was
subsequently restored to its original compact formatting outside the new
entry. That whitespace-only delta is a reviewed applicability exception,
confirmed by the retained dispatch plan and unchanged parsed catalog meaning.
Retention entries leave `source` null for the mixed production/working-tree
snapshot; the signed build's source commit and exact attachment hashes remain
explicit, rather than attributing the whole test run to the build commit. The next action is the user's review of inventory
scope against the withheld findings and adjudication of ready rows. The
outflow/migration decision remains a prerequisite to pass 2.

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
