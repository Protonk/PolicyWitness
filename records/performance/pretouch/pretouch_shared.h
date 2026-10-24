/*
 * pretouch_shared.h — control block shared by the pre-touch investigation's
 * host harness (harness.c) and experimental child (child.c). Not part of the
 * application. The block occupies the start of page 0 of a region the size of
 * the production evidence region; the probe pages lie far from it.
 */
#ifndef PRETOUCH_SHARED_H
#define PRETOUCH_SHARED_H

#include <stdatomic.h>
#include <stdint.h>

#define PT_MAGIC 0x50544348u
#define PT_FORMAT 1u
/* PW_SHM_REGION_BYTES of controller/tools/pw_probe_runner/pw_probe_runner_abi.h,
 * restated so the fixture does not include the application header. build.sh
 * checks the number against the shipped worker's --version line. */
#define PT_REGION_BYTES 3674768u
#define PT_PROBE_SALT 0x5052424500000000ull
#define PT_SECOND_SALT 0x5345434f4e440000ull
#define PT_ANON_SALT 0x414e4f4e00000000ull
#define PT_STAGES 16u
#define PT_ERROR_MAX 256u

enum {
    PT_STAGE_NONE = 0, PT_STAGE_MAPPED = 1, PT_STAGE_POLICY_READ = 2, PT_STAGE_PRE_TOUCHED = 3,
    PT_STAGE_COMPILED = 4, PT_STAGE_WAIT_GO1 = 5, PT_STAGE_APPLIED = 6, PT_STAGE_WITNESSED = 7,
    PT_STAGE_WAIT_GO2 = 8, PT_STAGE_STORING = 9, PT_STAGE_STORED = 10, PT_STAGE_READBACK = 11,
    PT_STAGE_SECOND_MAP = 12, PT_STAGE_ANON_MAP = 13, PT_STAGE_DONE = 14, PT_STAGE_WAIT_GO3 = 15
};

typedef struct {
    /* Host inputs, written before spawn. */
    uint32_t magic, version, page_size, probe_page, probe_pages, second_map_page, child_pre_touch, apply;
    uint64_t nonce;
    _Atomic uint32_t go[3];
    uint32_t pad0;
    /* Child publications. stage and done are release-stored; t[] holds
     * mach_absolute_time at each stage entry. */
    _Atomic uint32_t stage;
    _Atomic uint32_t done;
    _Atomic uint32_t pages_stored;
    int32_t child_pid;
    uint64_t child_base;
    uint64_t t[PT_STAGES];
    uint64_t t_gate_seen[3];
    int32_t policy_len;
    int32_t compile_ok;
    int32_t apply_called, apply_rc, apply_errno;
    int32_t witness_open_rc, witness_open_errno;
    int32_t rusage_rc[3], rusage_errno[3];
    int64_t minflt[3], majflt[3];
    int32_t readback_ok;
    int32_t second_map_rc, second_map_errno, second_map_store_ok;
    int32_t anon_map_rc, anon_map_errno, anon_store_ok;
    int32_t exit_code_intent;
    char compile_error[PT_ERROR_MAX];
} pt_ctrl_t;
_Static_assert(sizeof(pt_ctrl_t) <= 1024, "control block must stay inside page 0");

#endif
