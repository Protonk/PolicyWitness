# Plan: The Worker — Instrument and Constraints

## Status

Pass 3 is complete at its review stop in this checkpoint
(`docs: complete worker tour pass 3 draft`). Pass 2 work is committed in
`83f61f35a96d295f2a2a94aa29740664ec2971f6`.
Pass 1 comparison and adjudication are committed in `f5e5136`: rows 15 and 16
were the two findings held outside the tree, and both were recovered. Pass 1
work remains in `90fcb1b9a1e48a1e41725e9faca3095297ee493c` against production
source `6fd44fb15397678d29f0f96bfee2b1abbe4bbbb6`.

[WORKER.md](WORKER.md) now has the resource/authority draft and generated map.
The accepted private-extension and exec-descendant gaps moved there verbatim;
the architecture tour links to their new owner. Inventory facts remain in the
manifest and prose remains authored, with no call-site completeness rule.

Rows 1–6, 8–18 are validating the draft; rows 7 and 19 remain implementing
for pass 4. Row 15 explains retention, with its fix outside this scope. Row 7
authorizes source comment corrections; row 19 authorizes stronger verification,
with production hardening subject to separate adjudication. Rows 20 and 21
opened in map review and row 22 in prose review; all three await adjudication.
No row closed and no production source changed.

All pass 3 source-drift cases passed, every generator check passed, and a second
architecture generation wrote nothing. Evidence and applicability are recorded
below. Stop here for the user's draft/register review. Pass 4 has not started;
no push or release was performed.

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

The manifest owns the inventory; the working table was migrated in pass 2.

### Inventory ownership

The pass 1 inventory is now the worker-capabilities graph in
[architecture.json](architecture.json). Its S/N identifiers preserve every
resource entry from the pass 1 commit; X identifiers add the external evidence
needed to show joins without routing predictions into the worker. The generated
[node table](WORKER.md#worker-capabilities-nodes) owns the resource facts.
The pass 1 ledger below remains the authority for which checks were actually
run. A manifest check citation establishes a definition, not assertion coverage.

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

The user adopted the recommended dispositions for rows 1–7, 9 and 11–19,
with the explicit exceptions recorded below for rows 7, 15 and 19. Rows 8 and
10 retain their existing adjudications. At that checkpoint all rows were implementing; subsequent draft re-proof
updates appear in their details. The adjudicated scope controls later changes;
the checkpoint closed no row.

| # | Candidate | Evidence | State | Adjudicated disposition / recommendation for open rows |
| --- | --- | --- | --- | --- |
| 1 | Worker launch has a different inheritance contract from exec children | H has no close-by-default attributes; nil envp is empty in the examined Apple path and L; L observes fds 0–4, IC demonstrates an extra inherited descriptor/environment value | validating | Explain the launch rule and bounded observations; consider explicit descriptor isolation as a separate fix, not something L proves unnecessary |
| 2 | Policy, evidence and readiness descriptors remain open | W has no close of 0/3/4; L observes all three before/after apply; child controls exclude inherited endpoints | validating | Explain retention; do not claim that closing these would leave only attempt fds, since stdio/ambient inheritance remains |
| 3 | `open_write` truncates on open and attempts an unchecked write | `attempt_file_open_write` uses `O_TRUNC`, discards write/close results and reports open success | validating | Correct guide/tour wording to distinguish attempted byte write from an observed write; no behavior change recommended |
| 4 | `open_read` reports open success only | One-byte read and close are attempted without retaining returns | validating | Correct guide/tour wording; contrast published `read_fresh` observations |
| 5 | `create` opens existing files and supplies a masked creation mode | No `O_EXCL`/`O_TRUNC`; mode argument 0600, subject to inherited umask; existing-file checker asserts bytes/identity | validating | Explain intended open/create behavior and scope mode claim to the supplied argument |
| 6 | Exec preparation allocates after apply; formatting needs a narrower account | Apple spawn wrapper allocates both handles and can grow action storage; fixed PW diagnostic destinations do not establish library-wide allocation freedom | validating | Explain per-attempt allocation and diagnostic call boundary; keep architecture's already-scoped preallocation claim; correct stale comments via row 7 |
| 7 | Source comments state retired or overbroad premises | Stack/static, last-allocation, no-allocation, R5/R6 and Swift-worker comments remain; main also says every write checks its return and misdescribes fatal-signal interpretation | implementing | Source comment corrections authorized for pass 4, with identity regeneration/build/identity validation |
| 8 | Ownership of private-extension limitation | Existing architecture paragraph and intended worker-tour location rechecked | validating | Adjudicated: WORKER.md owns it; ARCHITECTURE links there, in pass 3/integration |
| 9 | Native release does not establish revocation; an after-release read is nevertheless observed | Checker accepts either after-release result and verifies bytes if successful; seed's “nothing observes” wording was too broad | validating | Keep accepted private-API scope from row 8 and correct the candidate sentence; no new universal revocation assertion |
| 10 | Exec descendants can outlive the worker/run | Group targeting and possible unconfirmed reap verified; existing accepted descendant limit remains | validating | Adjudicated ownership move; preserve accepted scope and distinguish worker-death/unreaped-child paths |
| 11 | Ambient worker state is only partly inventoried | L observes cwd, uid/gid, fds, argv/environment and VM regions; task-port census refused; signal mask/limits/private internal state unobserved | validating | Explain measured starting substrate; accept the explicitly bounded observation as a limitation; no empty-process claim |
| 12 | Ignored SIGPIPE reaches exec children; extension-specific core-limit inheritance is unreachable in admitted plans | Spawn sets neither signal reset flag; `extensionMeaningFailure` refuses exec+extension; helper's own SIGPIPE ignore prevents independent signal evidence | validating | Explain signal inheritance, correct the seeded extension-to-exec claim, and reserve a signal observer for any requested stronger guarantee |
| 13 | Extension requests can change worker core limits before apply | `prepare_extension` sets both limits to zero only after requested extension symbols resolve; local failure is published | validating | Explain request-dependent process context and native failure branches; no change recommended |
| 14 | Worker-side token erasure is path-dependent | Proceed refusal/spin, cancellation exit, compile/parameter/apply failures and early returns can bypass post-loop erase; host `erase` is separate | validating | Explain exact worker/host erasure sites, including accepted mapping retained until exit; any extra worker erase requires a separate fix |
| 15 | Mach lookup retains the acquired bootstrap reference | `task_get_special_port` succeeds before lookup; only `svc` is deallocated, including on repeated lookup/failure paths | validating | Explain retention now; the reference-balance fix is separate scope |
| 16 | Compiled-object lifetime has no explicit PW destruction | `profile` goes to capture/apply and no `sandbox_free_profile` is declared/called; private apply ownership is unobserved | validating | Explain the call/ownership boundary; investigate API ownership before authorizing a free, which could otherwise be invalid |
| 17 | Several resources cross the proposed role boundaries | Token mapping carries authority and protocol metadata; native extension acquisition occurs inside an attempt; shared working storage and signal state have multiple purposes | validating | Keep these resources outside single-role clusters, with named roles; do not force all inventory rows into one cluster |
| 18 | Oversized issuer token erasure covers a bounded prefix | I computes bounded `strnlen`, rejects oversize, erases that length and frees; no full allocation extent is established | validating | Correct erasure scope and investigate safe full-buffer disposal before a fix; accepted-token path remains distinct |
| 19 | Host/issuer launch setup does not check every acquisition/setup return | H ignores file-action init/adddup2 results and shm flag/unlink results; E ignores handle init results; copied argv can contain nil after failed strdup | implementing | Strengthen verification in pass 4; production refusal/hardening requires a separate adjudication |
| 20 | Authority cluster and arrows can overstate supplied power | Map review finds ambient context in S16a and apply/entry-point edges whose original style suggested granting authority | awaiting adjudication | Keep S16a unclustered; distinguish preparation, exercising an API and imposing restriction; confirm this account at the prose stop |
| 21 | Inventory resources can be disconnected from drawn observations | Native-size map review finds ambient state and working-storage nodes without incident edges; direct observation is narrower than resource existence | awaiting adjudication | Retain visible inventory nodes and describe the graph as selected relationships, not a proof that every resource is observed; consider focused views in later work |
| 22 | Existing exec documentation upgrades bounded controls into general claims | Guide says setup is not a sandbox operation; harness README treats a descriptor ceiling as proof of post-apply placement | awaiting adjudication | Correct these documentation claims to measured setup behavior and source-established placement; no runtime change proposed |

### Row details

Each detail retains the original candidate, evidence, refutation and
recommendation. The adjudication and authorized scope follow that material;
validation and the after sentence remain to be recorded in the appropriate
pass. Adopting a disposition is not closing a row.

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

Adjudication: Explain the native launch rule and bounded observations. Explicit worker descriptor isolation is separate scope; no production change is authorized. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#starting-authority-and-ambient-context): “The worker launch uses nil spawn attributes and leaves other descriptors to native close-on-exec inheritance.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Explain retained protocol descriptors and cleanup exceptions. No descriptor-removal change is authorized. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#reporting-apparatus): “The worker retains its evidence descriptor as well as the mapping. Its policy input and readiness descriptors also stay open until exit.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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
establish that the return is discarded. The original recommendation was a guide/tour correction; adjudication follows.

Adjudication: Correct the guide and worker tour to distinguish truncating open, attempted byte write and published open result. No behavior change is authorized. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#acquisitions-inside-attempts): “Published success is the open result; the write and close returns are discarded.” Guide wording is corrected under this row's authorization.
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Correct the guide and worker tour to distinguish open success from the unpublished read and close results, contrasted with read_fresh. No behavior change is authorized. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#acquisitions-inside-attempts): “Opens read-only, attempts a one-byte read and close, and discards those latter returns.” Guide wording is corrected under this row's authorization.
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Explain intended open/create behavior and the supplied mode argument subject to umask. No behavior change is authorized. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#acquisitions-inside-attempts): “Existing targets are opened without truncation; missing targets can be created.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Explain per-attempt allocations and the diagnostic library-call boundary; preserve the scoped architecture claim. Source comment corrections belong to row 7. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#acquisitions-inside-attempts): “The examined Apple spawn implementation allocates both handles and can grow action storage.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Source comment corrections are authorized for pass 4, in their own source commit with worker-identity regeneration, signed build and covering validation. This authorizes comment corrections, not runtime behavior changes. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

**Row 8.** First candidate: “Two documents will state the private-extension
limit.” The existing architecture paragraph separates PW buffer erasure from
private allocation/retention, kernel state, identity, permissions and
revocation. Existing adjudication remains: move ownership to WORKER.md in
pass 3 and link from ARCHITECTURE. Validation will check paragraph ownership,
links and the Known gaps index. No move or after-sentence exists in pass 1.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#supplied-extension-authority): “Known gap: private extension calls may allocate or retain internal state that PW cannot inspect.” The accepted paragraph moved verbatim; ARCHITECTURE now links to its owner, and both gap indexes were updated.
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Retain the accepted private-API limitation under row 8 and explain the observed after-release read with its allowed outcomes. No universal revocation claim or native API change is authorized. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#supplied-extension-authority): “The worker publishes the native release result and any subsequent requested read observations.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Pass 3 draft re-proof in [WORKER.md](WORKER.md#acquisitions-inside-attempts): “Known gap: an exec child's descendant that leaves the child's process group can outlive the run unobserved.” The accepted paragraph moved verbatim; ARCHITECTURE now links to its owner, and both gap indexes were updated.
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Explain the measured starting substrate and accept the explicitly bounded observation as a Known gap. No new isolation guarantee or runtime change is authorized. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#starting-authority-and-ambient-context): “Known gap: the starting-state observation is bounded to the exercised launch configuration.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Explain inherited signals and correct the unreachable extension-to-exec claim. A stronger signal guarantee and dedicated observer remain separate scope. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#starting-authority-and-ambient-context): “Exec-child setup selects descriptor isolation and a new process group, while leaving ignored-signal inheritance and the signal mask to native spawn rules.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Explain request-dependent core-limit changes and their failure branches. No native behavior change is authorized. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#starting-authority-and-ambient-context): “For an extension request, preparation sets both core limits to zero after resolving the private entry points; local failure is recorded.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Explain the worker and host erase sites and early exits, including the retained accepted mapping. Additional worker erasure is separate fix scope. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#supplied-extension-authority): “Compile/apply/parameter failures, proceed refusal, cancellation and interruption inside a native call can bypass the final loop erasure.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Explain retention now; the fix is separate scope. No reference-release change or regression-control waiver is authorized in this work. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#acquisitions-inside-attempts): “Leaves the acquired bootstrap reference until process exit, including after lookup failure and repeated attempts.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Explain the capture/apply call chain and private ownership boundary. Investigate API ownership before any future free; no destruction change is authorized. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#reporting-apparatus): “The compiled profile has no explicit PW destruction call; ownership changes inside the private apply routine remain unobserved.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Draw resources with multiple roles or no role outside single-role clusters and name their roles in prose. No runtime change is authorized. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#capability-map): “White nodes have multiple roles or form the ambient execution substrate.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Correct the bounded-prefix erasure account and leave safe full-buffer disposal investigation before a future fix. No native disposal change is authorized. State: implementing. Validation and after sentence
are pending; no row closes at this checkpoint.

Pass 3 draft re-proof in [WORKER.md](WORKER.md#supplied-extension-authority): “An oversized token is rejected and that inspected prefix is erased; the allocation extent beyond the bound is unobserved.”
Validation: source/assertion review at the scope above and fresh documentation
checks in the pass 3 ledger; no new runtime observation. State: validating,
pending the draft review; not closed.

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

Adjudication: Strengthen verification in pass 4. Authorized scope is passing
and rejected controls for setup failures and descriptor collisions. The selected
exception authorizes verification; the recommendation to add production refusal
is not adopted here. Any resulting runtime hardening requires a separate
adjudication. Source instrumentation, if required for the authorized controls,
keeps the worker-identity, signed-build and covering-validation requirements.
State: implementing; verification and the after sentence remain pending. No
regression-control waiver is authorized.

**Row 20.** Map candidate: “The gold group contains deliberately supplied
authority.” S16a also contains inherited credentials and ambient policy context.
The source is host spawn and worker selection, not a complete measured authority
inventory (row 11). The first drawing also used an authority-supply arrow for
compiled-profile application and dynamic symbol resolution. That style can
falsely imply a grant where there is a restriction or merely a callable entry
point. The draft keeps S16a outside the clusters, labels apply as exercising a
restriction and uses preparation for symbol resolution. This follows the
existing mixed-role drawing rule; it does not adjudicate a stronger authority
claim. Refutation would be a source-supported separation establishing that the
whole starting context was deliberately supplied, or evidence that the revised
arrows still imply an unsupported transfer. Native-size SVG review finds no
prediction edge into the worker. No native probe was run. Recommended disposition:
explain these distinct relations and retain the mixed starting context. User
adjudication and validation for closure remain pending.

**Row 21.** Map candidate: “Every inventoried resource has a path to something
the experiment observes.” The drawing cannot support that sentence. Nodes
S10a, S14a–c, S15, S16a/c/e/f/g/h/i/j, S17, S19, S20, S26b, N4, N7–N13
(except N12) have no incident edge in the selected relationship map. Several
are implicit inputs to calls or shared working storage; some ambient state is
only partly observed by L. Their absence from a connected path is not proof
that they are inert or unobservable. The draft preserves the nodes and their
source-scoped facts instead of inventing causal or observation edges to make
them connected. Source review can refute an omitted relationship; an independent
observer could strengthen a specific fact, but no such probe was run in pass 2.
Recommended disposition: explain selected relationships and the measured
observation boundary, with focused visual views a possible later improvement.
This is awaiting adjudication, not an accepted new instrumentation guarantee.
The native-size review found readable node/edge labels after dropping redundant
edge-kind words; the full inventory requires scrolling in the SVG.

**Row 22.** Prose candidates encountered in existing owners: “None of that
setup is a sandbox operation, so under an unaugmented `(deny default)` the
denied call is `posix_spawn` itself” in the guide, and the harness README's
claim that its descriptor-ceiling result “proves that the worker creates each
attempt's pipes and spawn handles inside the attempt, after apply”. These
sentences upgrade one profile/environment observation and a peak-descriptor
control into broader gating and placement claims. The first issue is related
to rows 6–7's source-comment finding but also occurs in authored user/test
references, whose correction was not specifically adjudicated.

Source: [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
is called by the exec attempt after apply. Assertions in
[the harness](../tests/suites/runner_c_worker_harness/run.sh) check successful
setup reaching spawn for the denying case and completed children under a
resource ceiling for the per-attempt case. A worker preparing one attempt's
pipes just before apply could still meet that ceiling; a different native
implementation or resource failure could stop setup. No new runtime probe or
mutation was needed to distinguish these assertions from source placement,
and none ran in pass 3. Recommended disposition: correct the two owning
references to these scopes and link the worker tour, with no production change.
They remain unchanged pending user adjudication. The draft's positive sentence
is “The ceiling checks reuse across attempts; the denying case observes setup
reaching spawn for its profile and environment. Source establishes post-apply
placement.” This row is awaiting adjudication and remains open at the stop.

### Pass 3 draft re-proof and validation

The after sentences below are the draft under review, not closed-row claims.
Source and cited assertions were reviewed at their stated scope; no runtime
case was rerun in pass 3. Documentation machinery and the gap moves receive
fresh validation in this pass. Rows with completed documentation work are
validating pending review. Rows 7 and 19 remain implementing for pass 4, and
rows 20–22 await adjudication. No row closes at this stop.

### Pass 3 evidence ledger

Public command: `PW_TEST_OUT_DIR=tests/out/runs/worker-p3-final tests/run.sh
--suite source_drift`. Run ID: `20261017T224648Z_56da5fa6`. All selected
cases passed: `source_drift/runner_source_manifests_agree`,
`source_drift/limits_documentation`, `source_drift/contract_versions`,
`source_drift/architecture_documentation`, `source_drift/build_documentation`
and `source_drift/generator_contract`. The source/guidance controls include
passing and rejected Known gap ownership mutations in all three tours.
The generator-contract result retains the existing baseline unchanged.

Architecture regenerated twice; the second run wrote nothing. Architecture,
build, contract, worker-identity and limits check modes passed. Source review
confirmed that both accepted gap paragraphs moved verbatim, their former
locations link to the new owner, and the Known gaps indexes agree. The README,
runner reference and document graph link the new tour. The guide's file-action
wording now states the native observation under rows 3–5; row 22's broader exec
claims remain for adjudication. Receiving-side source citations were added to
selected map edges while drafting; their rendered geometry is unchanged.

This is documentation and verification evidence, not a fresh live worker run.
The retained `documentation-source/` attachment records base commit
`83f61f35a96d295f2a2a94aa29740664ec2971f6` and the tested worktree patch.
Retention source is null because the pass 3 inputs were uncommitted. Subsequent
Status, scope clarification and evidence-ledger edits plus the retention entry
are bookkeeping; prose/link and generator checks were repeated before commit.
The clarified row 19 entry records the user's selected verification-only scope,
without authorizing the original recommendation's runtime refusal change.
Production source and worker identity remain unchanged from pass 1. No row
closed, and the work stops before pass 4.

### Pass 2 evidence ledger

Destination support and its controls preceded inventory migration. The routing
checkpoint ran `source_drift/architecture_documentation` and
`source_drift/generator_contract` through the public dispatcher in
`tests/out/runs/worker-p2-routing`; both passed. This was the generator-only
checkpoint, before the capability graph was added. The final pass verification
below supersedes it for the map and destinations together.

The map preserves all S/N resource identifiers; X nodes add external evidence.
The syscall-local sysctl buffer is explicitly named in N10, which already owns
attempt-local working storage. No production source changed. The SVG was read
as a whole and in native-size crops of the dense reporting/operation and token
areas. The review opened rows 20 and 21. No row closed.

Final pass 2 verification: architecture regenerated twice (second run wrote
nothing); architecture, build, contract, worker-identity and limits check modes
passed. The full `source_drift` run in `tests/out/runs/worker-p2-final`, run ID
`20261017T223303Z_19a7b574`, passed five cases and failed
`source_drift/contract_versions`: its disposable build checkout omitted
WORKER.md and therefore refused before the intended controls. The fixture now
copies every registered destination and routes figure paths per graph.

The replacement run in `tests/out/runs/worker-p2-verified`, run ID
`20261017T223822Z_8247f3aa`, passed
`source_drift/contract_versions`, `source_drift/architecture_documentation` and
`source_drift/generator_contract`. It includes the final optional cluster-label
placement and controlled last-render refusal without requiring Graphviz in the
case. The other three full-run passes remain credited:
`source_drift/runner_source_manifests_agree`,
`source_drift/limits_documentation` and `source_drift/build_documentation`.
Reviewed applicability exception: intervening edits change architecture layout,
its controls, the contract fixture inventory and explanatory prose; they change
none of those three cases' source-set, limits or build inputs/expected outputs.
The rerun generator-contract case rechecks final prose, links and generated
ownership. No baseline exception was added.

Both full/replacement runs retain the tested base commit, worktree patch and
new document/figures in `documentation-source/`; the retention source is null
because the inputs were uncommitted. Subsequent Status and ledger additions
are bookkeeping, checked for prose/links before commit. All cited live behavior
still comes from the pass 1 ledger, not these documentation checks.

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

## Outflow

The first draft leaves the inventory in the manifest as per-resource facts
with citations and leaves the prose authored. It adds no rule tying the
inventory to call sites. This is the user's decision before pass 2 starts.
The manifest and its generated tables preserve the inventory for a later
migration; review against source remains responsible for completeness.

Modularizing the architecture, build and worker generation machinery and
migrating prose into semi-structured output are separate work. A parser over
the worker's call sites and its baseline are also separate work; this plan
does not introduce either.
