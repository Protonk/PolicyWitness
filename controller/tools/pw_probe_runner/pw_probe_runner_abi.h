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

#include <stdint.h>

#define PW_PROBE_RUNNER_ABI_VERSION 1u

/* Bounded so the host reserves a region of known size. 256 slots ×
 * 2 KiB + 64 B header = 512 KiB + 64 B per run. The cap is chosen to
 * fit comfortably in one page-aligned anonymous mapping while still
 * being deep enough for any plausible specimen plan. */
#define PW_SHM_MAX_STEPS    256u
#define PW_SHM_SLOT_BYTES   2048u
#define PW_SHM_HEADER_BYTES 64u
#define PW_SHM_REGION_BYTES \
    ((size_t)PW_SHM_HEADER_BYTES + ((size_t)PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES))

/* Bounded string sizes inside a slot. They add up below the slot
 * budget; the remainder is reserved padding for future fields. */
#define PW_SHM_STEP_ID_MAX        64u
#define PW_SHM_TARGET_MAX        512u   /* path or mach-service name */
#define PW_SHM_OBSERVED_PATH_MAX 1024u  /* PATH_MAX on macOS */
#define PW_SHM_ERROR_MAX          256u  /* optional failure-cause string */

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
    uint32_t reserved[(PW_SHM_HEADER_BYTES / 4u) - 7u];
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

_Static_assert(sizeof(pw_shm_header_t) == PW_SHM_HEADER_BYTES,
               "pw_shm_header_t must be exactly PW_SHM_HEADER_BYTES");
_Static_assert(sizeof(pw_shm_slot_t) == PW_SHM_SLOT_BYTES,
               "pw_shm_slot_t must be exactly PW_SHM_SLOT_BYTES");

#endif /* PW_PROBE_RUNNER_ABI_H */
