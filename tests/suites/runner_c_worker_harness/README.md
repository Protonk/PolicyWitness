# runner_c_worker_harness

Proves the C probe-runner (`pw-probe-runner`) in isolation. The
harness drives the same shared-memory ABI the production runner
host uses, so a failure here is a clean signal that the worker ABI
itself broke rather than the host wiring around it.

## What's pinned

Fifteen scenarios, each driven by `harness.c`. The first six are the
core lifecycle; the rest cover individual attempt kinds and the worker's
pre-apply self-defense branches.

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
   - clean-exits in response to `exit_requested` without SIGKILL.

3. **exit_byte_clean** — happy path again, but the assertion is
   strictly on `sent_sigkill == false` and `exit_code == 0`. Pins
   the exit-byte contract: the worker observes
   `header.exit_requested == 1` from shared memory, calls `_exit(0)`,
   and the harness reaps it before its grace timer fires.

4. **max_slots_deny_default** — bare `(deny default)` with all 256
   slots populated as `PW_ATTEMPT_NONE`. Asserts that every slot
   completes across the full shared-memory region after apply. This
   pins the multi-page ABI rather than only the first-slot smoke
   path.

5. **sigkill_fallback** — happy path through `done`, then the harness
   intentionally withholds `exit_requested`. Asserts that the host-side
   grace timer sends SIGKILL and reaps the worker. Pins the SIGKILL
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

### File attempt kinds

These drive the two attempt kinds that no other suite executes. The
harness owns the on-disk target (it is unsandboxed); the worker is what
runs the unlink/create under the scenario policy, and the harness reports
`target_exists_after` as the durable proof.

7. **unlink_allow** — `PW_ATTEMPT_FILE_UNLINK` under `(allow default)`:
   `rc=0` and the harness-created target is gone afterward.
8. **unlink_deny** — same under `(deny default)`: `rc=1`, `errno` ∈
   {EPERM=1, EACCES=13}, and the target survives.
9. **create_allow** — `PW_ATTEMPT_FILE_CREATE` under `(allow default)`
   against an absent path: `rc=0`, `observed_path` captured from the open
   fd, and the target exists afterward.

### Pre-apply self-defense

The worker refuses or survives bad input before `sandbox_apply`. The
shm-corruption branches are e2e-unreachable because the host always
populates the shm header correctly; `compile_failure` is the same branch
a real `sandbox_apply_failed` run takes (malformed SBPL now reaches the
worker, where compile and apply failure are indistinguishable), exercised
here in isolation without the host/XPC path. The harness — which pipes
policy straight to the worker — is the vehicle for all of them. Each asserts the exact worker exit code with no `applied`/`done`
sentinel and no ready byte (except compile_failure, which flips `done`).

10. **compile_failure** — malformed SBPL (missing close paren).
    `apply_rc=-1`, `applied` stays 0, `done` flips so the host stops
    polling, and the worker still `_exit(0)`s on the exit byte instead of
    dying. The "honest even on bad input" contract.
11. **abi_mismatch** — header `abi_version` ≠ the worker's build → exit 4.
12. **prepared_unset** — host never set `prepared=1` → exit 5.
13. **step_count_overflow** — header `step_count > PW_SHM_MAX_STEPS` → exit 6.
14. **policy_overflow** — policy text exceeds the worker's 256 KiB cap → exit 7.
15. **param_count_overflow** — header `param_count > PW_SHM_MAX_PARAMS` → exit 8.

The host-side harness logic (shm setup, full-region pre-touch,
posix_spawn file actions, sentinel polling, exit-byte handling) is concentrated in
`harness.c` so the bash driver only orchestrates and asserts.

## What this suite does NOT cover

- A policy-driven `_exit` denial. The suite covers the same host-side
  SIGKILL fallback by withholding `exit_requested`; it does not prove
  that a real SBPL rule can deny `_exit`.
- Silent ABI *semantic* drift. The worker's runtime refusal when the
  header `abi_version` disagrees is covered (abi_mismatch), and the
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
bundle's copy of `pw-probe-runner`.

## Artifacts

Each test_id writes:
- `result.json`: the JSON envelope `harness.c` emits, containing
  `{ ready_byte_received, applied, apply_rc, done, sent_sigkill,
  exit_code, term_signal, slots: [...], target_exists_after }`
  (`target_exists_after` is null except for the file unlink/create
  scenarios).
- `harness.stderr`: stderr from the harness (and the worker, since
  stderr is inherited).
- `assert.log`: stdout/stderr of the Python assertion block.
