/* Evidence only. Every cell and the decision have independent publications. */
#ifndef PW_AUTHORITY_SETUP_H
#define PW_AUTHORITY_SETUP_H
#include <stdint.h>
#include <stddef.h>
#include <stdatomic.h>
#define PW_SHM_AUTHORITY_SETUP_BYTES 832u
#define PW_AUTHORITY_SETUP_OPERATION_CAPACITY 16u
#define PW_AUTHORITY_SETUP_OPERATION_BYTES 48u
enum { PW_SETUP_INTEGER=1, PW_SETUP_MAPPING=2, PW_SETUP_SYMBOL=3, PW_SETUP_VALIDATION=4, PW_SETUP_MEMORY=5 };
enum { PW_SETUP_SUCCEEDED=1, PW_SETUP_FAILED=2, PW_SETUP_ACCEPTED=3, PW_SETUP_REJECTED=4,
       PW_SETUP_AVAILABLE=5, PW_SETUP_UNAVAILABLE=6, PW_SETUP_PERFORMED=7, PW_SETUP_NOT_ATTEMPTED=8 };
enum { PW_SETUP_RC=1, PW_SETUP_ERRNO=2, PW_SETUP_VALUE=4, PW_SETUP_CLEANUP=8 };
enum { PW_SETUP_READY=1, PW_SETUP_NOT_REQUIRED=2, PW_SETUP_TERMINAL_REQUIRED_FAILURE=3 };
typedef struct {
    _Atomic uint32_t published;
    uint32_t native_kind, operation, state;
    int64_t native_rc;
    int32_t saved_errno;
    uint32_t flags, detail, reserved;
    uint64_t value;
} pw_authority_setup_operation_t;
typedef struct {
    _Atomic uint32_t published;
    uint32_t disposition, primary_plus_one, required, actor_index, reserved;
    uint8_t padding[40];
    pw_authority_setup_operation_t operations[PW_AUTHORITY_SETUP_OPERATION_CAPACITY];
} pw_authority_setup_t;
_Static_assert(sizeof(pw_authority_setup_operation_t)==48, "setup cell size");
_Static_assert(offsetof(pw_authority_setup_operation_t,native_rc)==16, "setup return offset");
_Static_assert(offsetof(pw_authority_setup_operation_t,flags)==28, "setup flags offset");
_Static_assert(offsetof(pw_authority_setup_operation_t,value)==40, "setup value offset");
_Static_assert(offsetof(pw_authority_setup_t,operations)==64, "setup cells offset");
_Static_assert(sizeof(pw_authority_setup_t)==PW_SHM_AUTHORITY_SETUP_BYTES, "setup trailer size");
static inline void pw_setup_observe(pw_authority_setup_t *s, uint32_t slot, uint32_t kind,
    uint32_t state, int64_t rc, int error, uint32_t flags, uint32_t detail, uint64_t value) {
    if (!s || slot>=PW_AUTHORITY_SETUP_OPERATION_CAPACITY) return;
    pw_authority_setup_operation_t *o=&s->operations[slot];
    /* Each fixed operation is published at most once. */
    if (atomic_load_explicit(&o->published,memory_order_relaxed)) return;
    o->native_kind=kind; o->operation=slot; o->state=state; o->native_rc=rc;
    o->saved_errno=error; o->flags=flags; o->detail=detail; o->value=value;
    atomic_store_explicit(&o->published,1,memory_order_release);
}
#endif
