#ifndef PW_WORKER_EVIDENCE_H
#define PW_WORKER_EVIDENCE_H
#include <stdatomic.h>
#include "pw_probe_runner_abi.h"

/* No allocation, libc formatting or I/O: safe after application. These helpers
 * also let C producer controls exercise the production publication protocol. */
static inline pw_shm_evidence_t *pw_evidence(void *base) {
    return (void *)((char *)base + PW_SHM_HEADER_BYTES
        + PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES + PW_SHM_MAX_PARAMS * PW_SHM_PARAM_BYTES
        + PW_SHM_CAPTURE_HEADER_BYTES + PW_SHM_CAPTURE_BYTES);
}
static inline void pw_progress(pw_shm_evidence_t *e, uint32_t op,
                               uint32_t phase, uint32_t index) {
    uint32_t item = index == UINT32_MAX ? 0 : index + 1;
    atomic_store_explicit(&e->progress, (op << 24) | (phase << 20) | item,
                          memory_order_release);
}
static inline void pw_failure(pw_shm_evidence_t *e, uint32_t op, uint32_t code,
        uint32_t kind, int32_t result, int has_errno, int32_t err,
        uint32_t index, uint32_t detail) {
    atomic_store_explicit(&e->failure_published, 2, memory_order_release);
    e->operation = op; e->code = code; e->native_kind = kind;
    e->native_result = result; e->errno_present = has_errno ? 1 : 0;
    e->errno_val = err; e->item_index = index; e->detail = detail;
    atomic_store_explicit(&e->failure_published, 1, memory_order_release);
}
/* Single immutable text publication, independent of the failure payload.
 * The caller owns a readable NUL-terminated string; at most 4095 bytes are copied.
 * NULL means no diagnostic published. No formatting/allocation/I/O is required. */
static inline void pw_diagnostic(pw_shm_evidence_t *e, const char *text) {
    if (!text) return;
    atomic_store_explicit(&e->diagnostic_state, 3, memory_order_release);
    char *dest = (char *)e + PW_SHM_EVIDENCE_HEADER_BYTES;
    uint32_t length = 0;
    while (length < PW_SHM_DIAGNOSTIC_BYTES - 1 && text[length]) {
        dest[length] = text[length];
        length++;
    }
    dest[length] = 0;
    e->diagnostic_length = length;
    atomic_store_explicit(&e->diagnostic_state, text[length] ? 2 : 1, memory_order_release);
}
#endif
