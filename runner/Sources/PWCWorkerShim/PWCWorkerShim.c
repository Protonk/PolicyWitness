#include <fcntl.h>
#include <stdatomic.h>
#include <stdint.h>
#include <sys/mman.h>
#include <sys/types.h>

/*
 * Minimal C shim for the Swift CWorker driver. Swift handles most of
 * the syscalls via Darwin (mmap, posix_spawn, pipe, waitpid, etc),
 * but two functions need C wrappers:
 *
 *   1. C11 acquire/release atomics on a raw memory address — Swift
 *      has no first-class way to do these, and the shm sentinels in
 *      controller/tools/pw_probe_runner/pw_probe_runner_abi.h are
 *      _Atomic uint32_t with release/acquire ordering guarantees the
 *      worker depends on.
 *   2. shm_open is variadic ("int shm_open(const char *, int, ...)"
 *      with a mode arg conditional on O_CREAT). Swift's Darwin
 *      doesn't import variadic C functions, so the host needs a
 *      thin fixed-arg trampoline.
 */

uint32_t pw_cworker_load_acquire_u32(const uint32_t *p) {
    const _Atomic uint32_t *ap = (const _Atomic uint32_t *)p;
    return atomic_load_explicit(ap, memory_order_acquire);
}

void pw_cworker_store_release_u32(uint32_t *p, uint32_t value) {
    _Atomic uint32_t *ap = (_Atomic uint32_t *)p;
    atomic_store_explicit(ap, value, memory_order_release);
}

int pw_cworker_shm_open_create(const char *name, mode_t mode) {
    return shm_open(name, O_CREAT | O_RDWR | O_EXCL, mode);
}
