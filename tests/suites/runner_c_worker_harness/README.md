# runner_c_worker_harness

Proves the new C probe-runner (`pw-probe-runner`, RUNNER-RESHAPE-PLAN
R5/R6/R7/R8) in isolation, before the runner host actually invokes it.
The Step 5 plan is explicit about this: build/sign/embed the helper,
prove the shared-memory ABI, then flip production traffic in Step 6.
This suite is what "prove" means.

## What's pinned

Six scenarios, each driven by `harness.c`:

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

4. **max_slots_deny_default** — bare `(deny default)` with all 256
   slots populated as `PW_ATTEMPT_NONE`. Asserts that every slot
   completes across the full shared-memory region after apply. This
   pins the multi-page R8 ABI rather than only the first-slot smoke
   path.

5. **sigkill_fallback** — happy path through `done`, then the harness
   intentionally withholds `exit_requested`. Asserts that the host-side
   grace timer sends SIGKILL and reaps the worker. This pins the R8
   fallback path without needing a synthetic SBPL rule that denies
   `_exit`.

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

The host-side harness logic (shm setup, full-region pre-touch,
posix_spawn file actions, sentinel polling, exit-byte handling) is concentrated in
`harness.c` so the bash driver only orchestrates and asserts.

## What this suite does NOT cover

- A policy-driven `_exit` denial. The suite covers the same host-side
  SIGKILL fallback by withholding `exit_requested`; it does not prove
  that a real SBPL rule can deny `_exit`.
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
