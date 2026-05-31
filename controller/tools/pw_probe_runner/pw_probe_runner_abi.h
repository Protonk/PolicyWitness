/*
 * pw_probe_runner_abi.h — shared-memory ABI between the runner host
 * (Swift, unsandboxed) and pw-probe-runner (C, sandboxed worker).
 *
 * The host mmaps a single anonymous shared region pre-spawn,
 * populates step inputs, pre-touches every page, and hands the FD
 * to the worker via posix_spawn file actions.
 * After the worker's sandbox_apply() returns successfully it reads its
 * own inputs from the slots, runs each attempt as stack-only POSIX
 * code (no allocations post-apply), writes results to the same slots,
 * and spins until the host requests exit.
 *
 * Both sides include THIS header so the layout cannot drift. A
 * compile-time _Static_assert at the bottom pins the slot/header
 * sizes so a future field addition that pushes past the budgets is a
 * loud build break rather than a silent overrun.
 *
 * Synchronization
 * ---------------
 * All sentinels are _Atomic uint32_t. Stores use release ordering;
 * loads use acquire. Each sentinel has one writer and many readers
 * (or one reader). Field ownership is documented per-field.
 *
 * The slot's `completed` field is written LAST by the worker after
 * all other slot outputs are durable; the host MUST acquire-load
 * `completed` first and only read other slot outputs once
 * `completed == 1`. This release/acquire pair makes the slot's
 * non-atomic fields safe to read without per-field synchronization.
 */

#ifndef PW_PROBE_RUNNER_ABI_H
#define PW_PROBE_RUNNER_ABI_H

#include <stddef.h>
#include <stdint.h>

/*
 * ABI version 4 grows the slot from 2 KiB to 8 KiB to carry exec-attempt
 * payload: a bounded argv table plus child status + stdout/stderr capture.
 * Existing field offsets shift because the argv table is interposed
 * between the inputs and the v3 outputs; the version bump makes this
 * a hard host↔worker compatibility boundary, defended by the
 * abi_version check at worker entry. In practice host + worker ship
 * together (the worker binary is bundle-local inside each XPC service),
 * so the check is a defense-in-depth tripwire rather than a live
 * compatibility boundary.
 */
#define PW_PROBE_RUNNER_ABI_VERSION 4u

/* Bounded so the host reserves a region of known size. 256 slots ×
 * 8 KiB + 1024 params × 512 B + 64 B header = ~2.56 MiB per run.
 * The slot cap is chosen to fit comfortably in one page-aligned
 * anonymous mapping while still being deep enough for any plausible
 * specimen plan. The param cap is sized for real-world SBPL profile
 * closures (Apple system profiles bind 100+ derived params once
 * imports are resolved), with substantial headroom. */
#define PW_SHM_MAX_STEPS    256u
#define PW_SHM_SLOT_BYTES   8192u
#define PW_SHM_MAX_PARAMS   1024u
#define PW_SHM_PARAM_BYTES  512u
#define PW_SHM_HEADER_BYTES 64u
#define PW_SHM_REGION_BYTES                                                  \
    ((size_t)PW_SHM_HEADER_BYTES                                             \
     + ((size_t)PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES)                        \
     + ((size_t)PW_SHM_MAX_PARAMS * PW_SHM_PARAM_BYTES))

/* Bounded string sizes inside a slot. They add up below the slot
 * budget; the remainder is reserved padding for future fields. */
#define PW_SHM_STEP_ID_MAX        64u
#define PW_SHM_TARGET_MAX        512u   /* path, mach-service name, or sysctl name */
#define PW_SHM_OBSERVED_PATH_MAX 1024u  /* PATH_MAX on macOS */
#define PW_SHM_ERROR_MAX          256u  /* optional failure-cause string */

/* Bounded argv table for exec attempts. argv_count is the number of
 * populated entries [0..PW_SHM_MAX_ARGV]; entries beyond it are
 * undefined. Each entry holds a NUL-terminated string up to
 * PW_SHM_ARGV_BYTES - 1 bytes. The runner host enforces both bounds
 * before shm allocation. */
#define PW_SHM_MAX_ARGV          16u
#define PW_SHM_ARGV_BYTES        128u

/* Per-stream child output capture for exec attempts. Sized to give
 * useful diagnostic context without ballooning the slot; output past
 * the buffer is truncated and tagged. */
#define PW_SHM_CHILD_OUTPUT_BYTES 1024u

/* Bounded string sizes inside a param slot. SBPL param names are
 * typically short identifiers; values can be paths or other long
 * strings. Sized to keep pw_shm_param_t at PW_SHM_PARAM_BYTES exactly. */
#define PW_SHM_PARAM_KEY_MAX     128u
#define PW_SHM_PARAM_VALUE_MAX   384u

/*
 * Attempt kinds. Wire-stable across host and worker: new kinds MUST
 * be appended; existing values MUST NOT be renumbered. A slot whose
 * kind the worker does not recognize completes with
 * rc = -1, errno_val = ENOSYS, completed = 1, and a descriptive
 * error string — the host can then surface it as an unsupported
 * attempt rather than as a worker crash.
 *
 * PW_ATTEMPT_NONE means "the host filled this slot but no attempt
 * should run." The worker still writes completed = 1 so the host
 * can distinguish "received but skipped" from "worker died before
 * reaching this slot."
 *
 * PW_ATTEMPT_EXEC_SPAWN is declared at ABI v4 so the host↔worker
 * shm layout carries the necessary argv / child-status fields, but
 * the worker does not yet implement the `case` for it — a slot with
 * kind=EXEC_SPAWN currently lands in the default branch and reports
 * the unsupported-attempt outcome. The implementation lands in a
 * later change (the runtime exec path).
 */
typedef enum {
    PW_ATTEMPT_NONE             = 0,
    PW_ATTEMPT_FILE_OPEN_READ   = 1,
    PW_ATTEMPT_FILE_OPEN_WRITE  = 2,
    PW_ATTEMPT_FILE_CREATE      = 3,
    PW_ATTEMPT_FILE_UNLINK      = 4,
    PW_ATTEMPT_FILE_ACCESS      = 5,
    PW_ATTEMPT_MACH_LOOKUP      = 6,
    PW_ATTEMPT_SYSCTL_READ      = 7,
    PW_ATTEMPT_EXEC_SPAWN       = 8,
} pw_attempt_kind_t;

/*
 * Region header. Lives at offset 0; slot[i] lives at
 * offset PW_SHM_HEADER_BYTES + i * PW_SHM_SLOT_BYTES.
 *
 * Field ownership:
 *   abi_version    — host writes pre-spawn; worker reads, aborts on mismatch.
 *   step_count     — host writes pre-spawn; worker reads. 0..PW_SHM_MAX_STEPS.
 *   prepared       — host → worker. Set to 1 pre-spawn. The worker
 *                    sanity-checks (a defense against a host bug or
 *                    accidentally-uninitialised mapping) and may
 *                    abort early if 0.
 *   applied        — worker → host. Set to 1 after sandbox_apply()
 *                    returns successfully. Host's signal that the
 *                    worker is now under the policy and the validator
 *                    can safely query the worker_pid.
 *   done           — worker → host. Set to 1 after every populated
 *                    slot has completed = 1.
 *   exit_requested — host → worker. Set to 1 once the host has read
 *                    all needed results; worker polls this in the
 *                    post-done spin loop and _exit(0)s when observed.
 *   apply_rc       — worker writes the sandbox_apply return code so
 *                    the host can classify "applied=0 because apply
 *                    failed" without inferring from worker exit.
 */
typedef struct {
    uint32_t abi_version;
    uint32_t step_count;
    _Atomic uint32_t prepared;
    _Atomic uint32_t applied;
    _Atomic uint32_t done;
    _Atomic uint32_t exit_requested;
    int32_t apply_rc;
    uint32_t param_count;            /* 0..PW_SHM_MAX_PARAMS */
    uint32_t reserved[(PW_SHM_HEADER_BYTES / 4u) - 8u];
} pw_shm_header_t;

/*
 * Per-step slot. Inputs are written by the host pre-spawn; outputs
 * are written by the worker post-apply. `completed` is written LAST
 * by the worker so a host that sees completed == 1 (acquire-load)
 * can read every other output field with regular loads — the
 * release/acquire pair on `completed` synchronizes the rest of the
 * slot.
 *
 * argv_count + argv carry exec-attempt input; child_pid /
 * child_exit_code / child_term_signal / child_stdout / child_stderr
 * carry exec-attempt output. Non-exec attempts leave the exec fields
 * zeroed (the region is memset to zero by the host before populating
 * any slot). Both ends of the exec wiring land in a later change;
 * checkpoint 2 defines the layout so a future field-offset drift
 * across host and worker is caught by the runner_abi_layout suite.
 */
typedef struct {
    /* Inputs (host writes pre-spawn; worker reads post-apply). */
    char     step_id[PW_SHM_STEP_ID_MAX];
    uint32_t attempt_kind;                       /* pw_attempt_kind_t */
    char     target[PW_SHM_TARGET_MAX];
    uint32_t argv_count;                         /* exec: 0..PW_SHM_MAX_ARGV */
    char     argv[PW_SHM_MAX_ARGV][PW_SHM_ARGV_BYTES];

    /* Outputs (worker writes post-apply; host reads once completed). */
    int32_t  rc;
    int32_t  errno_val;
    char     observed_path[PW_SHM_OBSERVED_PATH_MAX];
    char     error[PW_SHM_ERROR_MAX];
    /* Exec output fields (ABI v4). Populated by the run_attempt
     * EXEC_SPAWN case. Sentinel conventions when no child ran:
     *   child_pid          == 0  (spawn failed; errno_val carries the
     *                              posix_spawn errno; child_exit_code
     *                              and child_term_signal stay at -1/0)
     *   child_exit_code    == -1 (child was signaled OR no child ran)
     *   child_term_signal  == 0  (child clean-exited OR no child ran)
     * When child_pid > 0 the spawn succeeded — exactly one of
     * child_exit_code (clean exit) or child_term_signal (signal
     * termination) carries the verdict. The drift classifier reads
     * child_pid to distinguish a sandbox-blocked spawn (child_pid==0,
     * errno EPERM/EACCES → strong deny) from a child non-zero exit
     * (child_pid>0, rc!=0 → non-policy failure). */
    int32_t  child_pid;
    int32_t  child_exit_code;
    int32_t  child_term_signal;
    char     child_stdout[PW_SHM_CHILD_OUTPUT_BYTES];
    char     child_stderr[PW_SHM_CHILD_OUTPUT_BYTES];
    _Atomic uint32_t completed;

    /* Reserved padding so the slot stays exactly PW_SHM_SLOT_BYTES.
     * A future field that pushes past this budget breaks the
     * _Static_assert below at compile time. */
    uint8_t  reserved[PW_SHM_SLOT_BYTES
                      - PW_SHM_STEP_ID_MAX
                      - sizeof(uint32_t)                       /* attempt_kind */
                      - PW_SHM_TARGET_MAX
                      - sizeof(uint32_t)                       /* argv_count */
                      - (PW_SHM_MAX_ARGV * PW_SHM_ARGV_BYTES)
                      - sizeof(int32_t)                        /* rc */
                      - sizeof(int32_t)                        /* errno_val */
                      - PW_SHM_OBSERVED_PATH_MAX
                      - PW_SHM_ERROR_MAX
                      - sizeof(int32_t)                        /* child_pid */
                      - sizeof(int32_t)                        /* child_exit_code */
                      - sizeof(int32_t)                        /* child_term_signal */
                      - PW_SHM_CHILD_OUTPUT_BYTES              /* child_stdout */
                      - PW_SHM_CHILD_OUTPUT_BYTES              /* child_stderr */
                      - sizeof(_Atomic uint32_t)];
} pw_shm_slot_t;

/*
 * SBPL params delivered to the worker. Host populates [0..param_count)
 * pre-spawn; worker reads pre-apply and passes each key/value through
 * sandbox_create_params + sandbox_set_param before calling
 * sandbox_compile_string. Keys and values must be NUL-terminated; the
 * worker re-applies a terminating NUL at the field boundary defensively
 * before sandbox apply (matching the slot string treatment).
 *
 * The params region lives at offset
 * PW_SHM_HEADER_BYTES + PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES.
 */
typedef struct {
    char key[PW_SHM_PARAM_KEY_MAX];
    char value[PW_SHM_PARAM_VALUE_MAX];
} pw_shm_param_t;

_Static_assert(sizeof(pw_shm_header_t) == PW_SHM_HEADER_BYTES,
               "pw_shm_header_t must be exactly PW_SHM_HEADER_BYTES");
_Static_assert(sizeof(pw_shm_slot_t) == PW_SHM_SLOT_BYTES,
               "pw_shm_slot_t must be exactly PW_SHM_SLOT_BYTES");
_Static_assert(sizeof(pw_shm_param_t) == PW_SHM_PARAM_BYTES,
               "pw_shm_param_t must be exactly PW_SHM_PARAM_BYTES");

#endif /* PW_PROBE_RUNNER_ABI_H */
