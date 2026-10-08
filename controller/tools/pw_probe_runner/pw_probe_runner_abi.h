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
 * Host and worker ship together inside each XPC service. Their generated
 * source identity covers representation and protocol implementation, and is
 * checked before any layout-dependent work or policy input. The bootstrap
 * magic at offset 0 and 32 identity bytes at offset 64 are fixed. The magic
 * also makes ordinal-era workers refuse this header before using its layout.
 * See docs/CONTRACT.md and tests/FAILURE-PROPAGATION-CONTRACT.md.
 */
#define PW_SHM_ABI_MAGIC 0x50574944u
#define PW_SHM_ABI_IDENTITY_BYTES 32u
/* BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py) */
#define PW_WORKER_ABI_IDENTITY_HEX "52f1dc03684878c6a4d2a3511454e4df06a82b4af73c52bb8723d71681d5771c"
static const uint8_t PW_WORKER_ABI_IDENTITY[32] = {0x52, 0xf1, 0xdc, 0x03, 0x68, 0x48, 0x78, 0xc6, 0xa4, 0xd2, 0xa3, 0x51, 0x14, 0x54, 0xe4, 0xdf, 0x06, 0xa8, 0x2b, 0x4a, 0xf7, 0x3c, 0x52, 0xbb, 0x87, 0x23, 0xd7, 0x16, 0x81, 0xd5, 0x77, 0x1c};
/* END GENERATED WORKER IDENTITY */

/* Bounded so the host reserves a region of known size. 256 slots ×
 * 8 KiB + 1024 params × 512 B + bounded capture = about 3.5 MiB per run.
 * The slot cap is chosen to fit comfortably in one page-aligned
 * anonymous mapping while still being deep enough for any plausible
 * specimen plan. The param cap is sized for real-world SBPL profile
 * closures (Apple system profiles bind 100+ derived params once
 * imports are resolved), with substantial headroom. */
#define PW_SHM_POLICY_BYTES 262144u /* includes terminating NUL */
#define PW_SHM_MAX_STEPS    256u
#define PW_SHM_SLOT_BYTES   8192u
#define PW_SHM_MAX_PARAMS   1024u
#define PW_SHM_PARAM_BYTES  512u
#define PW_SHM_HEADER_BYTES 96u
/* Optional compiled-object capture. The host pre-touches this bounded region;
 * no capture pipe or post-apply allocation/file output is needed. */
#define PW_SHM_CAPTURE_HEADER_BYTES 144u
#define PW_SHM_CAPTURE_BYTES 1048576u
#define PW_SHM_CAPTURE_NONCE_BYTES 16u
#define PW_SHM_EVIDENCE_HEADER_BYTES 64u
#define PW_SHM_DIAGNOSTIC_BYTES 4096u
#define PW_SHM_REGION_BYTES                                                  \
    ((size_t)PW_SHM_HEADER_BYTES                                             \
     + ((size_t)PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES)                        \
     + ((size_t)PW_SHM_MAX_PARAMS * PW_SHM_PARAM_BYTES)                      \
     + PW_SHM_CAPTURE_HEADER_BYTES + PW_SHM_CAPTURE_BYTES                 \
     + PW_SHM_EVIDENCE_HEADER_BYTES + PW_SHM_DIAGNOSTIC_BYTES)

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
 * PW_ATTEMPT_EXEC_SPAWN uses the slot's argv inputs and child-status/output
 * fields. The worker observes spawn, bounded output and confirmed child reap
 * separately; these observations do not establish sandbox attribution.
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
 *   abi_magic, abi_identity — host writes pre-spawn; worker aborts on mismatch.
 *   step_count     — host writes pre-spawn; worker reads. 0..PW_SHM_MAX_STEPS.
 *   prepared       — host → worker. Set to 1 pre-spawn. The worker
 *                    sanity-checks (a defense against a host bug or
 *                    accidentally-uninitialised mapping) and may
 *                    abort early if 0.
 *   applied        — worker → host. Set to 1 after sandbox_apply()
 *                    returns successfully. Host's signal that the
 *                    worker is now under the policy and the validator
 *                    can safely query the worker_pid.
 *   done           — worker → host. Release-publishes a terminal payload:
 *                    either every populated slot completed after application,
 *                    OR a pre-apply failure wrote apply_rc. An acquire reader
 *                    must not infer successful application from done alone.
 *   exit_requested — host → worker. Set to 1 once the host has read
 *                    all needed results; worker polls this in the
 *                    post-done spin loop and _exit(0)s when observed.
 *   apply_rc       — worker writes the sandbox_apply return code, OR -1 on
 *                    sandbox_create_params returning NULL, sandbox_set_param
 *                    failure, the defensive parameter NUL check, or compilation
 *                    returning NULL. Those -1 values are PW status, not the
 *                    native result of the failed call. The NUL check follows
 *                    forced string termination; it is not a reliably reachable
 *                    specimen failure. Read only after acquiring applied or
 *                    done. Unpublished zeroed storage reports no call result.
 *   apply_errno    — worker writes the errno captured immediately after
 *                    a FAILED sandbox_apply (left 0 when apply
 *                    succeeded or was not called). Failure publication is done;
 *                    zero alone establishes neither success nor a call. The
 *                    parameter/compile failure paths do not write this field.
 */
typedef struct {
    uint32_t abi_magic;
    uint32_t step_count;
    _Atomic uint32_t prepared;
    _Atomic uint32_t applied;
    _Atomic uint32_t done;
    _Atomic uint32_t exit_requested;
    int32_t apply_rc;
    uint32_t param_count;            /* 0..PW_SHM_MAX_PARAMS */
    int32_t apply_errno;             /* failed-apply errno, valid with done; otherwise see above */
    uint32_t capture_requested;      /* host input; exactly 1 opts into sensitive capture */
    uint8_t capture_nonce[PW_SHM_CAPTURE_NONCE_BYTES]; /* caller's per-application identity */
    _Atomic uint32_t proceed;          /* host: collection closed, release attempts */
    _Atomic uint32_t proceed_observed; /* worker: acquired release before attempts */
    uint8_t abi_identity[PW_SHM_ABI_IDENTITY_BYTES];
} pw_shm_header_t;

_Static_assert(offsetof(pw_shm_header_t, abi_magic) == 0,
               "bootstrap magic must stay at offset 0");
_Static_assert(offsetof(pw_shm_header_t, abi_identity) == 64,
               "bootstrap identity must stay at offset 64");

/* Open numeric values: unknown operation/code values remain transportable. */
enum {
    PW_OP_HEADER = 1, PW_OP_POLICY_READ = 2, PW_OP_PARAMS_CREATE = 3,
    PW_OP_PARAM_SET = 4, PW_OP_COMPILE = 5, PW_OP_CAPTURE = 6,
    PW_OP_READY = 7, PW_OP_APPLY = 8, PW_OP_ATTEMPT = 9, PW_OP_FINISHED = 10,
    PW_OP_PROCEED = 11
};
enum { PW_PROGRESS_STARTED = 1, PW_PROGRESS_RETURNED = 2 };
enum {
    PW_FAILURE_NATIVE = 1, PW_FAILURE_SOURCE_LIMIT = 2, PW_FAILURE_POLICY_READ = 3,
    PW_FAILURE_STEP_LIMIT = 4, PW_FAILURE_PARAM_LIMIT = 5,
    PW_FAILURE_PARAM_ENCODING = 6, PW_FAILURE_UNPREPARED = 7,
    PW_FAILURE_PROCEED_TIMEOUT = 8,
    /* Embedded NUL in the policy text; detail is the byte offset. The host
     * refuses this at admission, and the reader refuses it again rather than
     * compile a prefix of the source the reply's policy_sha256 describes. */
    PW_FAILURE_SOURCE_NUL = 9
};
enum { PW_NATIVE_NONE = 0, PW_NATIVE_INTEGER = 1, PW_NATIVE_NULL = 2,
       PW_NATIVE_CLOCK = 3 };

/* Worker-owned publication contract is specified in
 * tests/FAILURE-PROPAGATION-CONTRACT.md, "Worker evidence contract".
 * All payloads immutable after
 * their publication word reaches 1 (diagnostic also accepts 2=truncated).
 * Progress is a single atomic value, never a gate for reading other storage. */
typedef struct {
    _Atomic uint32_t progress;
    _Atomic uint32_t failure_published;
    uint32_t operation;
    uint32_t code;
    uint32_t native_kind;
    int32_t native_result;
    int32_t errno_val;
    uint32_t errno_present;
    uint32_t item_index;
    uint32_t detail;
    _Atomic uint32_t ready_published;
    int32_t ready_rc;
    int32_t ready_errno;
    _Atomic uint32_t diagnostic_state;
    uint32_t diagnostic_length;
    uint32_t reserved;
} pw_shm_evidence_t;
_Static_assert(sizeof(pw_shm_evidence_t) == PW_SHM_EVIDENCE_HEADER_BYTES,
               "evidence header budget");

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
 * any slot). The runner_abi_layout suite checks the compiled field offsets
 * against the host's mirror.
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
    /* Exec output fields. child_pid > 0 establishes spawn,
     * not reaping. Zero means no child was produced (including admission or
     * setup refusal). Final status is populated only after a confirmed reap:
     * child_exit_code >= 0 is a natural exit; child_term_signal > 0 is a
     * reaped signal. The -1/0 pair also represents unconfirmed final status.
     * Attempt rc can report observation/cleanup failure independently of the
     * leader's exit code. No permission-shaped errno alone establishes a
     * sandbox cause. These fields are readable only after slot completion. */
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

/* Worker-only output, after params and before its bytecode payload. completed
 * release-publishes every other field. The host acquire-loads it; fields never
 * change afterward. Successful apply and PID must be checked separately.
 * status: 1 captured, 2 unsupported layout/type/length, 3 unreadable object,
 * 4 malformed consumed input. Zero means no complete capture. */
typedef struct {
    _Atomic uint32_t completed;
    uint32_t status;
    uint32_t profile_type;
    uint32_t bytecode_length;
    uint32_t worker_pid;
    uint32_t source_length;
    uint32_t param_count;
    uint32_t reserved;
    uint8_t source_sha256[32];
    uint8_t params_sha256[32];
    uint8_t bytecode_sha256[32];
    uint8_t request_nonce[PW_SHM_CAPTURE_NONCE_BYTES];
} pw_shm_capture_t;

_Static_assert(sizeof(pw_shm_capture_t) == PW_SHM_CAPTURE_HEADER_BYTES,
               "capture header must match its bounded ABI budget");

_Static_assert(sizeof(pw_shm_header_t) == PW_SHM_HEADER_BYTES,
               "pw_shm_header_t must be exactly PW_SHM_HEADER_BYTES");
_Static_assert(sizeof(pw_shm_slot_t) == PW_SHM_SLOT_BYTES,
               "pw_shm_slot_t must be exactly PW_SHM_SLOT_BYTES");
_Static_assert(sizeof(pw_shm_param_t) == PW_SHM_PARAM_BYTES,
               "pw_shm_param_t must be exactly PW_SHM_PARAM_BYTES");

#endif /* PW_PROBE_RUNNER_ABI_H */
