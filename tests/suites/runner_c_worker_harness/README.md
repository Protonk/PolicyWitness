# runner_c_worker_harness

The harness also exposes `exec_inheritance <helper> <nonce> <canary-fd>` for
the `runner_exec_inheritance` suite. That case records the actual worker launch
state through the shared fixture, execs the worker in the same PID, and returns
three exec-child reports. Its assertions live with that suite; the harness
provides only the adapter to the worker ABI.

Exercises the C probe-runner (`pw-probe-runner`) directly through the same
shared-memory ABI the production host uses. Failures retain worker-side
observations without involving the XPC host.

## What's pinned

`harness.c` drives the lifecycle, attempt, pre-apply and release scenarios
below. The separate `clock_arithmetic`, `proceed_precedence` and
`exec_control_states` cases compile production worker code with deterministic
clock and native-call equipment; see [Worker timing controls](#worker-timing-controls).

### Core lifecycle

1. **happy_default_allow** — `(allow default)` policy with one
   `file_open_read /etc/hosts` slot. Asserts:
   - pre-apply ready byte received,
   - `applied` sentinel set (apply_rc=0),
   - `done` sentinel set,
   - worker clean-exited (`exit_code=0`, no SIGKILL needed),
   - slot completed with `rc=0`, `observed_path=/private/etc/hosts`.

2. **bare_deny_default** — `(deny default)` and nothing else.
   Asserts that the C worker:
   - still fires `applied` + `done`,
   - reports the kernel deny via the slot (`rc=1`, `errno` ∈
     {EPERM=1, EACCES=13}),
   - clean-exits with `exit_requested` left zero, without SIGKILL.

3. **terminal_exit_without_request** — normal completion and an empty final
   phase publish `done` and clean-exit while the harness leaves
   `exit_requested` zero. The independently retained mapping is readable after
   reap. A bounded grace timer fails a worker that waits for exit permission.

4. **max_slots_deny_default** — bare `(deny default)` with all 256
   slots populated as `PW_ATTEMPT_NONE`. Asserts that every slot
   completes across the full shared-memory region after apply. This
   pins the multi-page ABI rather than only the first-slot smoke
   path.

5. **sigkill_fallback** — a controlled post-apply hang after completed slots
   and before `done`. The harness independently requests SIGKILL and reaps the
   stalled worker. Withholding an exit request after `done` is covered by the
   prompt-exit case above.

6. **params_round_trip** — `(allow default)(deny file-read-data
   (subpath (param "TARGET")))` with `TARGET=/private/etc`. Asserts
   that `sandbox_compile_string` saw the params object (otherwise
   `apply_rc` would be `-1` for an unresolved `(param "TARGET")`),
   `sandbox_apply` succeeded, AND the kernel actually denied
   `/etc/hosts` (`rc=1`, `errno=EPERM`). The kernel deny is the
   load-bearing assertion — a passing compile alone would prove only
   that the params object existed, not that the value reached the
   profile. (`TARGET=/private/etc` rather than `/etc` is an SBPL
   semantic detail: `(subpath ...)` matches against kernel-canonical
   paths, so the symlink target is what fires the rule.)

### File attempt kinds

These exercise unlink under allow/deny policies and creation of an absent file.
The harness owns the on-disk target (it is unsandboxed); the worker is what
runs the unlink/create under the scenario policy, and the harness reports
`target_exists_after` as the durable proof.

The CLI case `witness_contract/create_existing_file_preserves_contents`
separately checks create on existing files, preserving their bytes and identities
while enforcing write permission.

The separate `fresh_write` case compiles the production `write_fresh` and
`create_fresh` paths with scripted native calls. Fifteen controls establish
the exact open/stat/truncate/write/close sequence, failed and short transfers,
metadata failures, first-failure aggregation with later failures preserved,
existing-child refusal and diagnostic pre-open metadata. It needs only clang
and neither applies a sandbox nor claims actual file effects. Live public
directory witnesses supply those independent effects.

7. **unlink_allow** — `PW_ATTEMPT_FILE_UNLINK` under `(allow default)`:
   `rc=0` and the harness-created target is gone afterward.
8. **unlink_deny** — same under `(deny default)`: `rc=1`, `errno` ∈
   {EPERM=1, EACCES=13}, and the target survives.
9. **create_allow** — `PW_ATTEMPT_FILE_CREATE` under `(allow default)`
   against an absent path: `rc=0`, `observed_path` captured from the open
   fd, and the target exists afterward.

### Exec resources are per attempt

`exec_pipes_per_attempt` sets the soft and hard descriptor limits to 64 and
runs a plan that imports `system.sb`, reads `/etc/hosts`, spawns 32
`/usr/bin/true` children and reads again. Held open together, 32 pipe pairs
would need 128 descriptors, so every child exiting cleanly rules out holding
all those pipe pairs at once in this run. Both reads and the import must
succeed under the same ceiling. Source placement in
[`exec_resources_acquire`](../../../controller/tools/pw_probe_runner/pw_worker_exec.h)
establishes acquisition within the attempt after apply; the ceiling alone does
not establish placement or spawn-handle lifetime. The
[worker tour](../../../docs/WORKER.md#acquisitions-inside-attempts) separates
these claims.

`exec_setup_post_apply_denied` runs one exec slot under bare `(deny default)`.
For this control's inputs and environment, setup must reach `posix_spawn`:
`child_pid=0`, `rc=-1`, `errno` ∈ {EPERM, EACCES} and an error naming
`posix_spawn` rather than `pipe()` or a spawn-handle call. An earlier failure
requires investigation of its boundary and native error; this control alone
cannot attribute it to a changed sandbox rule or exclude resource exhaustion.

### Exec attempt budget

`exec_attempt_budget_remainder` shortens the worker's exec attempt budget to
one second and keeps the default ten-second deadline. Six `/bin/sleep 30`
steps follow: exactly one spawns, its deadline is the budget remainder (its
error says so), and the other five are refused before `posix_spawn` with
errno 60 and no child. `exec_attempt_budget_sequence` grants 1.5 seconds with
500 ms deadlines, so several helpers are killed at their own deadline before
the refusals begin. Both plans end with a read of `/etc/hosts` that must
succeed, and both require every slot completed, `done` published within a
second of the budget edge (`done_after_applied_ms`) and a clean worker exit.
See `exec_attempt_budget` in `docs/LIMITS.md`.

### Bounded sysctl read

`sysctl_read_capacity` compiles the production `attempt_sysctl_read` with only
`sysctlbyname` substituted by
[sysctl_control.c](../../fixtures/worker_lifecycle/sysctl_control.c). Independent
call receipts require one call, the submitted target, a non-null destination
with literal 4096 input capacity, and no new value. The compiled receipts must
also agree with the limits manifest. Success and ENOMEM failure change the
length out-parameter but preserve the existing PW status and errno; a stale
errno after success must not be reported. A producer mutation shortening the
supplied capacity must fail the same literal-capacity assertion.

This is a native-call boundary control without sandbox application. It does
not measure kernel copy behavior or establish ENOMEM's cause. The
[live sysctl filter suite](../runner_filter_sysctl_name/README.md) separately
checks its specimen's denial-shaped result and unavailable prediction.

### Worker timing controls

The worker times release waits and exec attempts in one continuous Mach time
domain of relative ticks. Each control compiles the production C source with
a controlled timebase and raw counter through its compile-time seams; expected
answers are literals or the defining inequality, never the helper under test.
Each seam leaves a stale `EPERM` that no timing record may report.
The fixtures define their seams before including the worker entry source;
its private timing and exec headers remain inside that interception scope.

- `clock_arithmetic` ([clock_control.c](../../fixtures/worker_lifecycle/clock_control.c)):
  ceiling allowances at 1/1, 125/3, reciprocal and extreme ratios; the exact
  edge and one tick below; refusals for zero factors, nonpositive or
  unrepresentable durations; 128-bit products a 64-bit multiply would
  overflow; ceiling millisecond conversion of bounded deltas; checked addition
  that never saturates or writes on overflow; three one-tick exclusions summing
  to exactly 3 ticks (125 ns); equal and zero samples accepted; regression
  against the last sample (even above the origin), wrap and below-origin
  samples rejected with stage/phase/slot, after which nothing is read again;
  and clock-setup failure publications (operation 12 with a native Mach return
  or code 14 with a reason).
- `proceed_precedence` ([proceed_control.c](../../fixtures/worker_lifecycle/proceed_control.c)):
  forked children wait on real shared-memory atomics. An unusable start or
  observation fails closed with release visible; the exact edge expires and one
  tick below acknowledges; cancellation observed by its load wins; an expired
  sample precedes cancellation; a delayed pre-expiry decision still acknowledges
  and excludes only the sampled interval; a future release fails before
  cancellation; a stale phase-1 release cannot release phase 2 and repeated
  polls exclude once; a successful backwards sample fails closed; fractional
  waits add their exact tick sum; an earlier rejected exec sample refuses
  without another read, naming its origin; and an unrepresentable exclusion
  refuses. Test-only gates after the time decision and after the cancellation
  load show the sampled-time limits: a decision held beyond the allowance still
  acknowledges, and cancellation stored after its load is too late, each with a
  before-decision complement. Acknowledgement, action-start progress and a real
  `/etc/hosts` open are observed independently.
- `exec_control_states` ([exec_control.c](../../fixtures/worker_lifecycle/exec_control.c)):
  see below.

The opt-in `native_clock` case
([native_clock.sh](opt_in/native_clock.sh)) runs the production clock helpers in
fresh processes under the original `(version 2)(deny default)(allow
file-read-data)` policy, bare `(version 2)(deny default)` and `(version 2)(allow
default)`: the production order (origin before setup and application) and a
variant whose first explicit raw read follows application, three repeats each.
Every continuous sample must validate and no continuous-clock process may have a
deny record. The standalone `CLOCK_MONOTONIC` neighbour is recorded as observed;
its intermittent failure need not recur. It retains the machine, translation
state, SDK, Mach-O architectures, timebase, counts, PIDs, reaps, a separate-process
disassembly of the installed clocks and any available deny records. It reads
unified logging, so it is opt-in. Its claims are scoped to the recorded machine
and implementation; it neither proves an always user-space path nor tests an
actual system sleep.

### First touch after application

`first_touch_after_apply` asks whether a worker can publish into a page of the
evidence region that no process backed before it applied its policy. The
production worker never reaches that path: before `sandbox_apply` it writes
every page it later publishes into. The case therefore compiles the production
worker source with its `PW_TERMINAL_PUBLISHED` seam defined to store one word
into page 200 of the region
([`first_touch_control.c`](../../fixtures/worker_lifecycle/first_touch_control.c);
offset and pattern in
[`first_touch_probe.h`](../../fixtures/worker_lifecycle/first_touch_probe.h)),
links it against the real libsandbox, and runs it through the harness rows
`first_touch_v1`, `first_touch_v2` and `first_touch_v3`: bare `(deny default)`
at each profile version. Those rows skip the harness's page touch, so the
probe page, which lies inside the compiled-profile capture bytes the worker
writes only when a capture is requested, has no backing when the worker starts.

`check_first_touch.py` keeps four oracles apart:

- **Condition.** The probe page was unbacked through application: the
  harness's `mincore` samples over its own mapping before spawn, at the ready
  byte, and when the worker's `applied` word is first seen all report it
  non-resident; the ready byte was received; the host did not touch the
  page; and the page lies inside the capture bytes. The ready byte follows
  every pre-application write the worker makes to the region and precedes
  `sandbox_apply`. The `applied` sample is taken before the harness publishes
  release, while the worker is parked in its release wait, so it is after
  application by the worker's own word and before any later worker activity;
  the seam store comes after release and `done`.
- **Application.** The worker's own record: `applied`, `apply_rc` 0 and `done`.
- **Enforcement.** The worker published a native denial result for the slot's
  open of `/etc/hosts` (`rc` 1, errno EPERM or EACCES), consistent with sandbox
  enforcement. This is not an independent observation of the kernel's decision
  and does not independently establish the ordering of `sandbox_apply` and
  the seam store.
- **Publication.** Decisive: the harness read the pattern back through its
  own mapping after reap, and the worker exited 0 without a cleanup kill.
  Residency of the probe page after reap is a separate corroborating
  assertion, never a substitute for the read-back.

The seam stores only after the worker's own `applied` publication, so a
compile or apply failure publishes nothing: the publication oracle fails and
the application and enforcement records say why.

Two sensitivity controls recreate the condition a first-touch probe can get
wrong, a probe page already backed before application, and require the
unchanged condition oracle to reject it although the worker publishes the
correct value:

- `host_pretouched`: the row `first_touch_host_pretouched` backs the probe
  page from the host before spawn. The before-spawn sample rejects it.
- `worker_pretouched`: the same source built with
  `PW_FIRST_TOUCH_WORKER_PRETOUCH`, whose constructor touches the probe page
  through a private mapping before `main`, so before application, and says so
  on stderr. The host never touched the page, so only the ready-byte and
  `applied` samples reject it. This control is also what checks the residency
  sample's meaning: it passes only while `mincore` reports pages resident in
  the shared object, whichever process backed them, rather than translations
  in the sampling process.

The shipped `pw-probe-runner` runs under the same three rows. In those
executions, one open-read slot per policy, the pages resident at the ready
byte (0 and 224, the header and evidence pages) were the pages resident at
`done` and after reap, the probe page was nonresident at those samples, and the
probe word read back as zero. That is an observation of these runs, recorded in
`first-touch-report.json`, not an invariant over every plan or specimen.

Reading a failure:

- A failed **publication** with the condition, application and enforcement
  oracles satisfied means the sandboxed process's store into a never-backed
  page did not reach the host mapping, or the process did not survive it;
  the exit status and signal say which.
- A failed **condition** means the case did not observe a first touch and
  establishes nothing either way: the page was backed before application,
  the ready byte was not received, `applied` was not seen before release, or
  `mincore` failed. The assertion message names the reason.
- A failed residency **corroboration** beside a matching read-back means the
  value landed and `mincore` no longer reports the page; the sensitivity
  controls show whether the sample's meaning changed.
- A **shipped-worker** residency difference records a change in sampled page
  backing; it does not by itself identify a worker store or publication event.
  The host's ready-byte sample may occur after application, and accesses
  between samples are not traced. Other shipped-worker assertions separately
  check the probe word, application and attempt records, and exit.

None of these alone establishes that the sandbox caused the behavior. The
denied open is a worker-published native result consistent with enforcement;
the worker's `applied` word is its own record; residency is a kernel report
whose meaning is checked only by the worker-pretouched control. The case
records what was observed and leaves the explanation to investigation.
`first-touch-report.json` is written before any assertion, so a failing run
keeps every unit's oracle answers, and the first line of `assert.log` names
the failing unit and oracle.

Limits: one probe page and one 8-byte store; three bare deny-default
policies; the first touch after application is exercised only by the ad-hoc
signed seam build, never by the shipped Developer ID-signed worker, whose own
pre-application writes keep it off that path in the observed runs.

### Pre-apply self-defense

The worker refuses or survives bad input before `sandbox_apply`. The
shm-corruption branches are e2e-unreachable because the host always
populates the shm header correctly. `compile_failure` exercises a real
compilation failure and the published status word, in isolation without the
host/XPC path. The host maps this ambiguous status to `runner_failed`; it cannot
identify compilation versus parameter setup/application from that status alone. The harness — which pipes
policy straight to the worker — is the vehicle for all of them. Each asserts the exact worker exit code with no `applied`/`done`
sentinel and no ready byte (except compile_failure, which flips `done`).

10. **compile_failure** — malformed SBPL (missing close paren).
    `apply_rc=-1`, `applied` stays 0, `done` flips so the host stops
    polling, and the worker still `_exit(0)`s on the exit byte instead of
    dying. The "honest even on bad input" contract.
11. **abi_mismatch** — header ABI identity ≠ the worker's build → exit 4.
    The same case also runs `abi_magic_mismatch`: a correct identity with an
    incompatible magic prefix must refuse before publishing shared evidence.
12. **prepared_unset** — host never set `prepared=1` → exit 5.
13. **step_count_overflow** — header `step_count > PW_SHM_MAX_STEPS` → exit 6.
14. **policy_overflow** — policy text exceeds the worker's 256 KiB cap → exit 7,
    failure code 2, and no EOF receipt: the read stops before EOF. The header's
    expectation is pinned at the capacity so this refusal, not the header's
    out-of-range refusal, is the one reached.
15. **param_count_overflow** — header `param_count > PW_SHM_MAX_PARAMS` → exit 8.
16. **policy_nul** — the policy bytes carry an embedded NUL after an
    allow-default prefix and before a deny-default tail → exit 9, failure
    record operation 2, code 9, detail 26 (the NUL's offset). A C-string reader
    would otherwise compile only the prefix while `policy_sha256` described the
    whole source. The host refuses NUL at admission; this is the reader's own
    guard. The 41 equal bytes pass the length check first, so the EOF receipt
    reports 41.

### Policy delivery acknowledgement

The policy pipe carries no framing. The header's `policy_bytes_expected` is the
host's half of the acknowledgement (the submission's byte count, written before
spawn) and the worker's `policy_bytes_received` behind `policy_read_published`
is its half (the count read at EOF, published before the comparison). A header
expectation the buffer cannot hold is refused before any byte is read; after
EOF, any count that differs from the expectation is refused before the NUL scan
and any libsandbox call. `result.json` carries `policy_bytes_expected` (the
submission), `policy_bytes_written` (what the pipe carried),
`header_bytes_expected` (the header input), `policy_read_published` and, behind
a flag of 1, `policy_bytes_received`.

17. **policy_truncated_prefix** — the submitted bytes are
    `(version 1)\n(allow default)\n(deny default)\n` (each `\n` is one newline
    byte), but the pipe closes after `(allow default)\n`: 28 of 43 bytes. The contract is the one the NUL guard
    states for one byte: no prefix of the source `policy_sha256` describes is
    compiled. The worker publishes the receipt (28), refuses with operation 2,
    code 13, detail 28 and exit 11, writes no ready byte, applies nothing and
    runs no attempt.
18. **policy_whole_submission** — the same 43 bytes delivered intact: receipt
    43 of 43, applied, and the kernel denies the `/etc/hosts` open the prefix
    allowed. This is the contrast that discriminates the two policies.
19. **policy_utf8_bytes** — a valid source whose comment holds multibyte
    UTF-8: expectation and receipt count 40 bytes for 37 characters; applied.
20. **policy_at_capacity** — a valid source padded with spaces to exactly
    `PW_SHM_POLICY_BYTES - 1` bytes is accepted after EOF and applied.
21. **policy_empty_expected** — an empty source with a zero expectation: zero
    is compared, not treated as unset. The receipt reports 0, the length check
    passes, and compilation refuses the empty source on its own terms
    (operation 5, `done` with `apply_rc` -1, clean exit).
22. **policy_expectation_out_of_range** — a header expectation of
    `PW_SHM_POLICY_BYTES` cannot fit the buffer, whose final byte is the NUL →
    operation 1, code 12, detail the refused expectation, exit 10, before any
    policy byte is read; no receipt.
23. **policy_capacity_plus_one** — one byte past the capacity with the
    expectation pinned at the capacity → the read overflow refusal (code 2,
    exit 7), no receipt. Overflow stops before EOF and is not a length mismatch.
24. **policy_overdelivered** — the pipe carries the 28-byte submission plus a
    `(deny default)` tail: receipt 43 against an expectation of 28 → code 13,
    detail 43, exit 11. The comparison refuses both directions.
25. **policy_empty_short** — empty EOF against an expectation of 43 → code 13,
    detail 0, exit 11, receipt 0.
26. **policy_zero_expected** — 28 bytes against an expectation of 0 → code 13,
    detail 28, exit 11, receipt 28.

The host-side harness logic (shm setup, full-region pre-touch,
posix_spawn file actions, sentinel polling, exit-byte handling) is concentrated in
`harness.c` so the bash driver only orchestrates and asserts.

## What this suite does NOT cover

- A policy-driven `_exit` denial. The suite covers the same host-side
  SIGKILL fallback by withholding `exit_requested`; it does not prove
  that a real SBPL rule can deny `_exit`.
- A first touch after application by the shipped worker. `first_touch_after_apply`
  exercises that path only with the ad-hoc signed seam build; the shipped
  worker's own pre-application writes back every page it publishes into in
  the executions observed.
- Silent ABI *semantic* drift. The worker's runtime refusal when the
  header ABI identity disagrees is covered (abi_mismatch), and the
  header has `_Static_assert`s pinning layout sizes at compile time — but
  a change that keeps the version constant while altering a field's
  meaning (e.g. renaming/repurposing a slot field) wouldn't be caught
  here. `runner_abi_layout` guards the struct layout separately.

## Build / run

```
./build.sh                                         # produces pw-probe-runner
./tests/run.sh --suite runner_c_worker_harness
```

`harness.c` is compiled once per suite run into
`tests/out/.../harness.runner_c_worker`. It uses the `PWRunner.xpc`
bundle's copy of `pw-probe-runner`. The compiler recipe lives in
`tests/fixtures/worker_harness/build.sh`, shared with the inheritance suite
and its mutation controls. Builds use the current ABI header, so the app
must also be rebuilt after an ABI change.

Every case uses `run_harness_case` for prerequisites, compilation, and capture,
then retains its own Python assertions. `finish_from_assert_log` records their
result. The build helper fails explicitly even inside conditional callers;
a failed build cannot fall through to an older harness executable. Independent
equipment-failure controls live in `shell_helpers/worker_setup`.

## Artifacts

Each test_id writes:
- `result.json`: the JSON envelope `harness.c` emits, containing
  `{ ready_byte_received, applied, apply_rc, policy_bytes_expected,
  policy_bytes_written, header_bytes_expected, policy_read_published,
  policy_bytes_received, done, sent_sigkill, exit_code, term_signal,
  slots: [...], target_exists_after }` (`target_exists_after` is null except
  for the file unlink/create scenarios; the policy byte counts are the
  submission, what the pipe was asked to carry, the header's expectation and,
  only behind `policy_read_published == 1`, the worker's EOF receipt).
- `harness.stderr`: stderr from the harness (and the worker, since
  stderr is inherited).
- `assert.log`: stdout/stderr of the Python assertion block.

The first case that compiles the harness also retains `build.log`.

`first_touch_after_apply` writes a harness envelope with a `first_touch`
object per unit (`first_touch_v1.json`, `first_touch_v2.json`,
`first_touch_v3.json`, `host_pretouched.json`, `worker_pretouched.json`,
`shipped_v1.json`, `shipped_v2.json`, `shipped_v3.json`) with the worker's
stderr beside each, the compiler commands and logs for both seam builds,
`assert.log` and `first-touch-report.json`, the per-unit dispositions and
resident-page lists the oracles judged.

The release controls exercise `proceed_never_set`, `proceed_late_after_expiry`,
`proceed_before_applied`, `proceed_delayed_observed_quiescence`,
`proceed_under_bare_deny_default`, `proceed_wait_budget_short`,
`proceed_wait_budget_long`, `proceed_expiry_release_boundary`,
`proceed_without_host_release`, and `max_slots_proceed`. They poll every slot and
attempt progress before release. Expiry forbids later attempts. The
`proceed_without_host_release` case leaves both release and exit request unset,
observes refusal and independently reaps clean exit without a cleanup kill.
It models absent host stores; it does not kill a real XPC host.
The clock substitution controls run in `runner_unit` against the real C
producer companions. ABI mismatch remains a pre-application refusal.

`exec_control_states` compiles the production exec helper with deterministic
native-call equipment and a controlled continuous counter. It checks absolute
tick deadlines across slow spawn, multiple release exclusions and intervening
work, exact plan exhaustion and child-deadline clamping, early pipe EOF and an
exited leader with open streams. Every timing stage fails closed as a local
fault with no errno: no spawn on an admission fault; group cleanup after an
observation fault; at reap, an immediate observation keeps its status and
otherwise status stays missing; a later attempt refuses because of the first
rejected sample, naming it; a native kill error survives beside the local
reason; and a child-deadline overflow refuses only its attempt, leaving the
clock usable. A subsequent rejected sample records its own stage, phase and
slot as the first sticky origin, preserved through later refusals. Interrupted
waits and failed cleanup keep their native errors.
Every reap must be nonblocking; absent status cannot become exit zero.

The control's native-call ledger is independent of the output payload. It
captures actual clock, wait, poll, read and signal calls in order, including
arguments, meaningful returns/errno/status and stream identity. The reviewed
[call-policy golden](../../fixtures/worker_lifecycle/exec_call_policy.json)
records hashes/counts for 58 attempts against the pre-refactor producer and
identifies the exact source, fixture and header bytes used. Descriptor numbers
are normalized by pipe role; all other recorded values and order remain in the
digest. A candidate must preserve this call policy. Do not refresh the golden
from a changed candidate merely to make it pass.

New branch controls independently check collection snapshots, both stream
errors and error revents, read precedence over error revents, recovered
interruptions, child/plan deadlines, no request versus successful/failed/ESRCH
group requests, separate successful/failed leader fallback, and ownership loss
without signalling. Reap controls separate native errors (including native
ETIMEDOUT), local expiry, final EINTR, successful signalling without a reap, and
clock faults with successful or missing status. Existing aggregate error
precedence remains separately asserted. Pre-spawn failure exposes no payload.

Six disposable producer mutations must fail their designated unchanged native
assertions: replacing the collection snapshot with final reap, treating ESRCH
as successful signalling, replacing the fallback result with the group result,
publishing child status after a pending wait, treating error revents as native
poll errno, and treating a local reap deadline as native wait errno. Each
variant retains its exact source/header/fixture copies and hashes, compiler
command, stdout/stderr and return status. The fixed control creates no child,
so it does not exercise process effects or publication through a real host. No
process or sandbox is created by this control; `runner_exec_lifecycle` supplies
independent live-process evidence.

The mutations replace the copied `pw_worker_exec.h` owner; the entry source
and all remaining headers are copied unchanged. Separate missing-owner controls
remove the timing or exec header and require the compiler's corresponding
include refusal, so an accidentally bypassed owner cannot supply a passing
interception control. The independent call-policy golden remains the native
behavior expectation.


`terminal_erasure` compiles the production worker with substituted native
sandbox/extension calls and a gate immediately after its terminal `done`
release-store. The parent retains a separate channel mapping, seeds nonzero
padding through its last byte and checks the fixed capacity without using the
erase argument or token length. Host erasure is withheld until observations
finish. Ordinary early returns preserve their codes and absent publications;
terminal refusal, cancellation, consumption, normal completion and pre-hang/
signal cleanup retain their distinct evidence. Fatal interruption during
consumption does not promise ordinary cleanup, and native release occurs only
for an explicit release action. Rejected and absent channels remain safe.
A shortened erase must fail the whole-buffer oracle. An erase moved after the
store/gate must fail the independent boundary oracle despite a zero buffer after
reap. These fixtures establish production control flow and memory observations,
not kernel sandbox effects; signed-worker cases establish native terminal exit.
