/*
 * pw_probe_runner_abi.h — shared-memory ABI between the runner host
 * (Swift, unsandboxed) and pw-probe-runner (C, sandboxed worker).
 *
 * Per RUNNER-RESHAPE-PLAN.md R5/R8. The host mmaps a single anonymous
 * shared region pre-spawn, populates step inputs, pre-touches every
 * page, and hands the FD to the worker via posix_spawn file actions.
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
 * ABI version 2 adds a fixed-size params region after the slots so
 * the host can deliver `policy.params` (SBPL parameters used inside
 * the policy text via `(param "NAME")`). v1 hosts must NOT spawn a
 * v2 worker: the worker checks abi_version on entry and aborts on
 * mismatch.
 */
#define PW_PROBE_RUNNER_ABI_VERSION 2u

/* Bounded so the host reserves a region of known size. 256 slots ×
 * 2 KiB + 16 params × 512 B + 64 B header = 520 KiB + 64 B per run.
 * The cap is chosen to fit comfortably in one page-aligned anonymous
 * mapping while still being deep enough for any plausible specimen
 * plan. */
#define PW_SHM_MAX_STEPS    256u
#define PW_SHM_SLOT_BYTES   2048u
#define PW_SHM_MAX_PARAMS   16u
#define PW_SHM_PARAM_BYTES  512u
#define PW_SHM_HEADER_BYTES 64u
#define PW_SHM_REGION_BYTES                                                  \
    ((size_t)PW_SHM_HEADER_BYTES                                             \
     + ((size_t)PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES)                        \
     + ((size_t)PW_SHM_MAX_PARAMS * PW_SHM_PARAM_BYTES))

/* Bounded string sizes inside a slot. They add up below the slot
 * budget; the remainder is reserved padding for future fields. */
#define PW_SHM_STEP_ID_MAX        64u
#define PW_SHM_TARGET_MAX        512u   /* path or mach-service name */
#define PW_SHM_OBSERVED_PATH_MAX 1024u  /* PATH_MAX on macOS */
#define PW_SHM_ERROR_MAX          256u  /* optional failure-cause string */

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
 */
typedef enum {
    PW_ATTEMPT_NONE             = 0,
    PW_ATTEMPT_FILE_OPEN_READ   = 1,
    PW_ATTEMPT_FILE_OPEN_WRITE  = 2,
    PW_ATTEMPT_FILE_CREATE      = 3,
    PW_ATTEMPT_FILE_UNLINK      = 4,
    PW_ATTEMPT_FILE_ACCESS      = 5,
    PW_ATTEMPT_MACH_LOOKUP      = 6,
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
 */
typedef struct {
    /* Inputs (host writes pre-spawn; worker reads post-apply). */
    char     step_id[PW_SHM_STEP_ID_MAX];
    uint32_t attempt_kind;                       /* pw_attempt_kind_t */
    char     target[PW_SHM_TARGET_MAX];

    /* Outputs (worker writes post-apply; host reads once completed). */
    int32_t  rc;
    int32_t  errno_val;
    char     observed_path[PW_SHM_OBSERVED_PATH_MAX];
    char     error[PW_SHM_ERROR_MAX];
    _Atomic uint32_t completed;

    /* Reserved padding so the slot stays exactly PW_SHM_SLOT_BYTES.
     * A future field that pushes past this budget breaks the
     * _Static_assert below at compile time. */
    uint8_t  reserved[PW_SHM_SLOT_BYTES
                      - PW_SHM_STEP_ID_MAX
                      - sizeof(uint32_t)
                      - PW_SHM_TARGET_MAX
                      - sizeof(int32_t)
                      - sizeof(int32_t)
                      - PW_SHM_OBSERVED_PATH_MAX
                      - PW_SHM_ERROR_MAX
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
