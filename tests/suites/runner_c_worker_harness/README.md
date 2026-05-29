# runner_c_worker_harness

Proves the new C probe-runner (`pw-probe-runner`, RUNNER-RESHAPE-PLAN
R5/R6/R7/R8) in isolation, before the runner host actually invokes it.
The Step 5 plan is explicit about this: build/sign/embed the helper,
prove the shared-memory ABI, then flip production traffic in Step 6.
This suite is what "prove" means.

## What's pinned

Three scenarios, each driven by `harness.c`:

1. **happy_default_allow** — `(allow default)` policy with one
   `file_open_read /etc/hosts` slot. Asserts:
   - pre-apply ready byte received,
   - `applied` sentinel set (apply_rc=0),
   - `done` sentinel set,
   - worker clean-exited (`exit_code=0`, no SIGKILL needed),
   - slot completed with `rc=0`, `observed_path=/private/etc/hosts`.

2. **bare_deny_default** — `(deny default)` and nothing else.
   This is the downstream bug-report shape the pre-Step-5 Swift
   worker died on. Asserts that the C worker:
   - still fires `applied` + `done`,
   - reports the kernel deny via the slot (`rc=1`, `errno` ∈
     {EPERM=1, EACCES=13}),
   - clean-exits in response to `exit_requested` without SIGKILL.

3. **exit_byte_clean** — happy path again, but the assertion is
   strictly on `sent_sigkill == false` and `exit_code == 0`. Pins
   the R7/R8 exit-byte contract: the worker observes
   `header.exit_requested == 1` from shared memory, calls `_exit(0)`,
   and the harness reaps it before its grace timer fires.

The host-side harness logic (shm setup, posix_spawn file actions,
sentinel polling, exit-byte handling) is concentrated in
`harness.c` so the bash driver only orchestrates and asserts.

## What this suite does NOT cover

- The SIGKILL fallback path. R5 documents it as a safety net for
  policies that would deny `_exit`, but exercising it requires a
  policy that explicitly denies the exit syscall — not a standard
  SBPL surface. The fallback exists in the harness (1 s grace
  before SIGKILL) but no scenario triggers it by design today.
- Production wiring. The runner host (PWRunnerService) still spawns
  the legacy Swift worker; it does not invoke `pw-probe-runner`.
  Step 6 wires production traffic and is gated on this suite being
  green.
- ABI version drift. The header has `_Static_assert`s pinning the
  layout sizes at compile time, but a value-level ABI change (e.g.
  renaming a slot field) wouldn't be caught here. Source-drift
  enforcement for the worker ABI is a candidate for Step 6's
  `source_drift` extension.

## Build / run

```
./build.sh                                         # produces pw-probe-runner
./tests/run.sh --suite runner_c_worker_harness
```

`harness.c` is compiled once per suite run into
`tests/out/.../harness.runner_c_worker`. It uses the `PWRunner.xpc`
bundle's copy of `pw-probe-runner`; `PWRunnerDebug.xpc`'s copy is
identical (same source, signed separately).

## Artifacts

Each test_id writes:
- `result.json`: the JSON envelope `harness.c` emits, containing
  `{ ready_byte_received, applied, apply_rc, done, sent_sigkill,
  exit_code, term_signal, slots: [...] }`.
- `harness.stderr`: stderr from the harness (and the worker, since
  stderr is inherited).
- `assert.log`: stdout/stderr of the Python assertion block.
