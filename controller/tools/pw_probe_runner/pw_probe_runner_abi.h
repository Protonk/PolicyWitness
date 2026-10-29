/*
 * pw_probe_runner_abi.h — shared-memory ABI between the runner host
 * (Swift, unsandboxed) and pw-probe-runner (C, sandboxed worker).
 *
 * The host mmaps a single anonymous shared region pre-spawn,
 * populates step inputs, pre-touches every page, and hands the FD
 * to the worker via posix_spawn file actions.
 * After the worker's sandbox_apply() returns successfully it reads its
 * own inputs from the slots, runs each attempt as stack-only POSIX
 * code with preallocated PW-owned result storage, writes results to the same slots,
 * erases accepted token bytes, publishes done, and exits without host permission.
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
#define PW_WORKER_ABI_IDENTITY_HEX "6f777628d0b0f233f6e26f99222e8f78cd0920bb94b842b5bf2d0c4b2e29a9a7"
static const uint8_t PW_WORKER_ABI_IDENTITY[32] = {0x6f, 0x77, 0x76, 0x28, 0xd0, 0xb0, 0xf2, 0x33, 0xf6, 0xe2, 0x6f, 0x99, 0x22, 0x2e, 0x8f, 0x78, 0xcd, 0x09, 0x20, 0xbb, 0x94, 0xb8, 0x42, 0xb5, 0xbf, 0x2d, 0x0c, 0x4b, 0x2e, 0x29, 0xa9, 0xa7};
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
#define PW_SHM_MAX_PHASES 8u
#define PW_SHM_PHASE_BYTES 32u
#define PW_SHM_HEADER_BYTES 448u
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
#define PW_SHM_FRESH_READ_BYTES    64u
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
    PW_ATTEMPT_FILE_READ_FRESH  = 9,
    PW_ATTEMPT_EXTENSION_CONSUME = 10,
    PW_ATTEMPT_EXTENSION_RELEASE = 11,
    PW_ATTEMPT_FILE_WRITE_FRESH = 12,
    PW_ATTEMPT_FILE_CREATE_FRESH = 13,
} pw_attempt_kind_t;

/* Host inputs partition the slots in order. Each worker publication is written
 * once, independently of the latest release ordinal in the region header. */
typedef struct {
    uint32_t first_slot;
    uint32_t end_slot;
    _Atomic uint32_t arrived;
    _Atomic uint32_t acknowledged;
    _Atomic uint32_t completed;
    uint8_t reserved[12];
} pw_shm_phase_t;
_Static_assert(sizeof(pw_shm_phase_t) == PW_SHM_PHASE_BYTES, "phase size drift");

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
 *                    completed execution, a pre-apply failure, or a refusal
 *                    while waiting for phase release. An acquire reader must
 *                    not infer application or slot completion from done alone.
 *   exit_requested — host → worker. Cancellation sampled before phase
 *                    acknowledgement. It is not permission to exit after
 *                    done; terminal publication is followed by _exit(0).
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
 *   policy_bytes_expected — host writes pre-spawn: the UTF-8 byte count of
 *                    the submission it writes to the policy pipe, immutable for
 *                    the worker's lifetime. Zero is a valid expectation. The
 *                    worker refuses a value above PW_SHM_POLICY_BYTES - 1 before
 *                    reading any policy byte (operation 1, code 12), and after
 *                    EOF refuses a delivered count that differs (operation 2,
 *                    code 13, detail the received count) before the NUL scan
 *                    and any libsandbox call. The pipe itself carries no
 *                    framing; this input is what tells a prefix apart from a
 *                    complete shorter submission.
 *   policy_bytes_received, policy_read_published — worker → host. Once the
 *                    read returns at EOF the worker stores the count it read
 *                    and release-publishes the flag, before the length
 *                    comparison. A header refusal, read error or overflow
 *                    publishes nothing here. An acquire of 1 is the only gate
 *                    for reading the count; it establishes the completed read,
 *                    not acceptance, compilation or application.
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
    _Atomic uint32_t proceed;          /* host: release ordinal, phase index + 1 */
    _Atomic uint32_t proceed_observed; /* worker: latest acquired release ordinal */
    uint8_t abi_identity[PW_SHM_ABI_IDENTITY_BYTES];
    uint32_t phase_count;
    uint32_t extension_requested;
    _Atomic uint32_t extension_delivery_published;
    uint32_t extension_delivery_status; /* PW_DELIVERY_*: 1 delivered, 2 token unavailable, 3 channel rejected, 4 API unavailable, 5 local setup failed */
    uint32_t extension_delivered_bytes;
    /* Delivery failure account, valid with extension_delivery_published and a
     * failure status. stage names the first failing preparation stage
     * (PW_DELIVERY_STAGE_*); native_rc and errno are that stage's call result
     * when it made a native call, otherwise 0 and not evidence. cleanup_stage
     * and cleanup_errno record a close or unmap failure observed while undoing
     * earlier setup after the first failure; they never change the status. */
    uint32_t extension_delivery_stage;
    int32_t extension_delivery_native_rc;
    int32_t extension_delivery_errno;
    uint32_t extension_delivery_cleanup_stage;
    int32_t extension_delivery_cleanup_errno;
    uint32_t policy_bytes_expected;            /* host input; see ownership above */
    uint32_t policy_bytes_received;            /* worker: count read at EOF */
    _Atomic uint32_t policy_read_published;    /* worker: 1 publishes the count */
    uint8_t reserved[44];
    pw_shm_phase_t phases[PW_SHM_MAX_PHASES];
} pw_shm_header_t;

_Static_assert(offsetof(pw_shm_header_t, abi_magic) == 0,
               "bootstrap magic must stay at offset 0");
_Static_assert(offsetof(pw_shm_header_t, abi_identity) == 64,
               "bootstrap identity must stay at offset 64");
_Static_assert(offsetof(pw_shm_header_t, policy_bytes_expected) == 136
               && offsetof(pw_shm_header_t, policy_read_published) == 144
               && offsetof(pw_shm_header_t, phases) == 192,
               "policy transfer fields are carved from the reserved bytes; no offset moves");

/* Open numeric values: unknown operation/code values remain transportable. */
enum {
    PW_OP_HEADER = 1, PW_OP_POLICY_READ = 2, PW_OP_PARAMS_CREATE = 3,
    PW_OP_PARAM_SET = 4, PW_OP_COMPILE = 5, PW_OP_CAPTURE = 6,
    PW_OP_READY = 7, PW_OP_APPLY = 8, PW_OP_ATTEMPT = 9, PW_OP_FINISHED = 10,
    PW_OP_PROCEED = 11,
    /* Mach timebase initialization and duration preparation. Temporally it
     * follows header validation (1) and precedes the policy read (2). */
    PW_OP_CLOCK_SETUP = 12
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
    PW_FAILURE_SOURCE_NUL = 9, PW_FAILURE_PHASE_LAYOUT = 10,
    PW_FAILURE_PHASE_RELEASE = 11,
    /* Host input policy_bytes_expected exceeds PW_SHM_POLICY_BYTES - 1; detail
     * is the refused expectation. Refused before any policy byte is read. */
    PW_FAILURE_LENGTH_EXPECTATION = 12,
    /* The count read at EOF differs from policy_bytes_expected; detail is the
     * received count. Like code 9, this refuses to compile a prefix (or an
     * extension) of the source the reply's policy_sha256 describes. */
    PW_FAILURE_SOURCE_LENGTH = 13,
    /* A local worker timing refusal with no native result or errno; detail
     * is a PW_TIME_REASON_* value, never milliseconds. */
    PW_FAILURE_TIME_INVALID = 14
};
/* Kind 3 is the historical CLOCK_MONOTONIC failure; the current worker's
 * continuous clock has no native error return and never publishes it. */
enum { PW_NATIVE_NONE = 0, PW_NATIVE_INTEGER = 1, PW_NATIVE_NULL = 2,
       PW_NATIVE_CLOCK = 3 };
/* Detail values for PW_FAILURE_TIME_INVALID and exec timing diagnostics.
 * Only a rejected raw sample is BACKWARDS_COUNTER; PRIOR_CLOCK_FAULT refuses
 * later timed work after such a rejection. The others are operation-local
 * arithmetic refusals that leave the clock usable. */
enum {
    PW_TIME_REASON_INVALID_TIMEBASE = 1, PW_TIME_REASON_INVALID_DURATION = 2,
    PW_TIME_REASON_BACKWARDS_COUNTER = 3, PW_TIME_REASON_UNREPRESENTABLE_DELTA = 4,
    PW_TIME_REASON_DEADLINE_OVERFLOW = 5, PW_TIME_REASON_PRIOR_CLOCK_FAULT = 6
};

/* Completed exec evidence codes. Zero is absence, never an observation.
 * These fields are immutable only after the slot's completed publication. */
enum {
    PW_EXEC_COLLECTION_COMPLETE = 1, PW_EXEC_COLLECTION_DEADLINE = 2,
    PW_EXEC_COLLECTION_ERROR = 3, PW_EXEC_COLLECTION_CLOCK_FAULT = 4
};
enum { PW_EXEC_DEADLINE_CHILD = 1, PW_EXEC_DEADLINE_PLAN = 2 };
enum {
    PW_EXEC_CLEANUP_NOT_REQUESTED = 1, PW_EXEC_CLEANUP_OWNERSHIP_UNCONFIRMED = 2,
    PW_EXEC_CLEANUP_REQUESTED = 3
};
enum {
    PW_EXEC_REAP_REAPED = 1, PW_EXEC_REAP_WAIT_ERROR = 2,
    PW_EXEC_REAP_OWNERSHIP_UNCONFIRMED = 3, PW_EXEC_REAP_GROUP_REQUEST_FAILED = 4,
    PW_EXEC_REAP_CLOCK_FAULT = 5, PW_EXEC_REAP_DEADLINE = 6
};
#define PW_SHM_EXEC_EVIDENCE_BYTES 112u

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

/* Fresh write observations are valid only after the containing slot completes.
 * rc == -2 is unattempted; failed calls retain errno, successful stat calls
 * retain descriptor/path identity and size. Preopen lstat is diagnostic only. */
#define PW_SHM_FILE_STAT_BYTES 48u
#define PW_SHM_FRESH_WRITE_BYTES 232u
typedef struct {
    int32_t rc, errno_val;
    uint32_t mode, uid, gid, reserved;
    uint64_t device, inode;
    int64_t size;
} pw_file_stat_t;
typedef struct {
    int32_t open_rc, open_errno, truncate_rc, truncate_errno;
    int64_t write_rc;
    int32_t write_errno, close_rc, close_errno;
    uint32_t reserved;
    pw_file_stat_t preopen_stat, opened_stat, truncated_stat, written_stat;
} pw_fresh_write_t;
_Static_assert(sizeof(pw_file_stat_t) == PW_SHM_FILE_STAT_BYTES, "file stat observation size");
_Static_assert(sizeof(pw_fresh_write_t) == PW_SHM_FRESH_WRITE_BYTES, "fresh write observation size");

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
    /* Immutable pre-call marker; does not establish native entry or return. */
    _Atomic uint32_t call_boundary;
    uint32_t native_result_valid;
    int64_t native_result;
    int32_t native_errno;
    uint32_t unavailable_code; /* 1 no token, 2 no handle, 3 API absent, 4 repeated action */
    int32_t access_open_rc, access_open_errno;
    int64_t access_read_rc;
    int32_t access_read_errno, access_close_rc, access_close_errno;
    int32_t access_stat_rc, access_stat_errno;
    uint32_t access_mode;
    uint64_t access_device, access_inode;
    uint32_t access_uid, access_gid;
    uint8_t access_bytes[PW_SHM_FRESH_READ_BYTES];


    /* Optional post-spawn exec evidence carved from reserved bytes. Valid is
     * exactly 1 after assembly; completed remains the sole read gate. Errno,
     * revents and clock-reason zero mean absent. Request state and fallback
     * presence distinguish an unmade call from a successful zero return.
     * Reap status is meaningful only when wait_rc equals child_pid. */
    uint32_t exec_valid;
    uint32_t exec_collection_stop, exec_leader_exit_observed;
    uint32_t exec_stdout_eof, exec_stderr_eof, exec_deadline_kind;
    int32_t exec_waitid_errno, exec_poll_errno;
    int32_t exec_stdout_read_errno, exec_stderr_read_errno;
    int32_t exec_stdout_poll_revents, exec_stderr_poll_revents;
    uint32_t exec_collection_clock_fault, exec_cleanup_state;
    int32_t exec_group_target, exec_group_signal, exec_group_rc, exec_group_errno;
    uint32_t exec_fallback_present;
    int32_t exec_fallback_target, exec_fallback_signal, exec_fallback_rc, exec_fallback_errno;
    uint32_t exec_reap_stop;
    int32_t exec_reap_wait_rc, exec_reap_wait_errno, exec_reap_status;
    uint32_t exec_reap_clock_fault;

    pw_fresh_write_t fresh_write;

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
                      - sizeof(_Atomic uint32_t)
                      - 156u - PW_SHM_EXEC_EVIDENCE_BYTES - PW_SHM_FRESH_WRITE_BYTES];
} pw_shm_slot_t;

_Static_assert(offsetof(pw_shm_slot_t, exec_valid) == 6136,
               "exec evidence must consume only the prior slot reserve");
_Static_assert(offsetof(pw_shm_slot_t, fresh_write) - offsetof(pw_shm_slot_t, exec_valid)
               == PW_SHM_EXEC_EVIDENCE_BYTES, "exec evidence field budget");
_Static_assert(offsetof(pw_shm_slot_t, fresh_write) == 6248,
               "fresh write must consume only the prior slot reserve");

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
