// Public header for the PWCWorkerShim SwiftPM target.
//
// Same convention as PWSandboxCheckShim.h: Swift call sites link to
// these symbols via @_silgen_name and do not import the module. The
// declarations exist to satisfy SwiftPM's publicHeadersPath
// bookkeeping and to document the C ABI.

#ifndef PW_CWORKER_SHIM_H
#define PW_CWORKER_SHIM_H

#include <stdint.h>
#include <sys/types.h>

// Fixed-arg wrapper around shm_open(name, O_CREAT|O_RDWR|O_EXCL, mode).
// Swift can't call variadic C functions; this wrapper is the way the
// CWorker driver creates its anonymous-ish shared region.
int pw_cworker_shm_open_create(const char *name, mode_t mode);

// C11 acquire-load / release-store of a uint32_t in the shm region.
// The pointer must reference the same memory the C worker treats as
// _Atomic uint32_t (i.e. header sentinels or per-slot `completed`).
// Pairs with the worker's atomic_load_explicit / atomic_store_explicit
// calls so host and worker share the same ordering guarantees.
uint32_t pw_cworker_load_acquire_u32(const uint32_t *p);
void     pw_cworker_store_release_u32(uint32_t *p, uint32_t value);

#endif /* PW_CWORKER_SHIM_H */
