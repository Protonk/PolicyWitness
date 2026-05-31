/*
 * runner_abi_layout printer
 *
 * Compiled against controller/tools/pw_probe_runner/pw_probe_runner_abi.h
 * at test time. Emits one KEY=VALUE line per ABI constant /
 * sizeof / offsetof that the Swift PWShmLayout enum mirrors. The
 * driver (run.sh) parses both this output and the Swift enum and
 * asserts every key has a matching Swift constant with the
 * identical numeric value.
 *
 * Parser-only source_drift can detect a missing constant but cannot
 * model compiler-applied struct padding. This printer's offsetof()
 * values are the ground truth — Swift's hand-mirrored offset
 * constants are what we're checking against.
 */

#include <stdio.h>
#include <stddef.h>

#include "pw_probe_runner_abi.h"

int main(void) {
    /* Top-level constants. Keys are the C macro spellings so a
     * reader of this file can grep them directly against the
     * header; the driver maps each C name to its Swift counterpart. */
    printf("PW_PROBE_RUNNER_ABI_VERSION=%u\n", PW_PROBE_RUNNER_ABI_VERSION);
    printf("PW_SHM_HEADER_BYTES=%u\n",         PW_SHM_HEADER_BYTES);
    printf("PW_SHM_MAX_STEPS=%u\n",            PW_SHM_MAX_STEPS);
    printf("PW_SHM_SLOT_BYTES=%u\n",           PW_SHM_SLOT_BYTES);
    printf("PW_SHM_MAX_PARAMS=%u\n",           PW_SHM_MAX_PARAMS);
    printf("PW_SHM_PARAM_BYTES=%u\n",          PW_SHM_PARAM_BYTES);
    printf("PW_SHM_REGION_BYTES=%zu\n",        (size_t)PW_SHM_REGION_BYTES);
    printf("PW_SHM_STEP_ID_MAX=%u\n",          PW_SHM_STEP_ID_MAX);
    printf("PW_SHM_TARGET_MAX=%u\n",           PW_SHM_TARGET_MAX);
    printf("PW_SHM_OBSERVED_PATH_MAX=%u\n",    PW_SHM_OBSERVED_PATH_MAX);
    printf("PW_SHM_ERROR_MAX=%u\n",            PW_SHM_ERROR_MAX);
    printf("PW_SHM_MAX_ARGV=%u\n",             PW_SHM_MAX_ARGV);
    printf("PW_SHM_ARGV_BYTES=%u\n",           PW_SHM_ARGV_BYTES);
    printf("PW_SHM_CHILD_OUTPUT_BYTES=%u\n",   PW_SHM_CHILD_OUTPUT_BYTES);
    printf("PW_SHM_PARAM_KEY_MAX=%u\n",        PW_SHM_PARAM_KEY_MAX);
    printf("PW_SHM_PARAM_VALUE_MAX=%u\n",      PW_SHM_PARAM_VALUE_MAX);

    /* sizeof cross-check: each per-struct budget macro must equal
     * the actual sizeof of the struct it bounds. The header carries
     * a _Static_assert for this; the test emits it again so a future
     * refactor that removes the static assert can't silently drift. */
    printf("sizeof.pw_shm_header_t=%zu\n",     sizeof(pw_shm_header_t));
    printf("sizeof.pw_shm_slot_t=%zu\n",       sizeof(pw_shm_slot_t));
    printf("sizeof.pw_shm_param_t=%zu\n",      sizeof(pw_shm_param_t));

    /* Header field offsets. */
    printf("offsetof.pw_shm_header_t.abi_version=%zu\n",    offsetof(pw_shm_header_t, abi_version));
    printf("offsetof.pw_shm_header_t.step_count=%zu\n",     offsetof(pw_shm_header_t, step_count));
    printf("offsetof.pw_shm_header_t.prepared=%zu\n",       offsetof(pw_shm_header_t, prepared));
    printf("offsetof.pw_shm_header_t.applied=%zu\n",        offsetof(pw_shm_header_t, applied));
    printf("offsetof.pw_shm_header_t.done=%zu\n",           offsetof(pw_shm_header_t, done));
    printf("offsetof.pw_shm_header_t.exit_requested=%zu\n", offsetof(pw_shm_header_t, exit_requested));
    printf("offsetof.pw_shm_header_t.apply_rc=%zu\n",       offsetof(pw_shm_header_t, apply_rc));
    printf("offsetof.pw_shm_header_t.param_count=%zu\n",    offsetof(pw_shm_header_t, param_count));

    /* Slot field offsets. */
    printf("offsetof.pw_shm_slot_t.step_id=%zu\n",            offsetof(pw_shm_slot_t, step_id));
    printf("offsetof.pw_shm_slot_t.attempt_kind=%zu\n",       offsetof(pw_shm_slot_t, attempt_kind));
    printf("offsetof.pw_shm_slot_t.target=%zu\n",             offsetof(pw_shm_slot_t, target));
    printf("offsetof.pw_shm_slot_t.argv_count=%zu\n",         offsetof(pw_shm_slot_t, argv_count));
    printf("offsetof.pw_shm_slot_t.argv=%zu\n",               offsetof(pw_shm_slot_t, argv));
    printf("offsetof.pw_shm_slot_t.rc=%zu\n",                 offsetof(pw_shm_slot_t, rc));
    printf("offsetof.pw_shm_slot_t.errno_val=%zu\n",          offsetof(pw_shm_slot_t, errno_val));
    printf("offsetof.pw_shm_slot_t.observed_path=%zu\n",      offsetof(pw_shm_slot_t, observed_path));
    printf("offsetof.pw_shm_slot_t.error=%zu\n",              offsetof(pw_shm_slot_t, error));
    printf("offsetof.pw_shm_slot_t.child_pid=%zu\n",          offsetof(pw_shm_slot_t, child_pid));
    printf("offsetof.pw_shm_slot_t.child_exit_code=%zu\n",    offsetof(pw_shm_slot_t, child_exit_code));
    printf("offsetof.pw_shm_slot_t.child_term_signal=%zu\n",  offsetof(pw_shm_slot_t, child_term_signal));
    printf("offsetof.pw_shm_slot_t.child_stdout=%zu\n",       offsetof(pw_shm_slot_t, child_stdout));
    printf("offsetof.pw_shm_slot_t.child_stderr=%zu\n",       offsetof(pw_shm_slot_t, child_stderr));
    printf("offsetof.pw_shm_slot_t.completed=%zu\n",          offsetof(pw_shm_slot_t, completed));

    /* Param field offsets. */
    printf("offsetof.pw_shm_param_t.key=%zu\n",   offsetof(pw_shm_param_t, key));
    printf("offsetof.pw_shm_param_t.value=%zu\n", offsetof(pw_shm_param_t, value));

    /* Region-derived offsets. Swift recomputes these from the size
     * macros; emit them here too so any miscomputation on either
     * side surfaces as a layout-guard failure rather than at runtime. */
    printf("region.slots_offset=%zu\n",
        (size_t)PW_SHM_HEADER_BYTES);
    printf("region.params_offset=%zu\n",
        (size_t)PW_SHM_HEADER_BYTES + (size_t)PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES);

    return 0;
}
