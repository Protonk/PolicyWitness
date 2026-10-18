/* Investigation-only ABI producer. No sandbox call or native attempt. */
#include "pw_probe_runner_abi.h"
#include "pw_worker_evidence.h"
#include <errno.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    alarm(10); /* Independent fixture watchdog; firing fails the experiment. */
    struct stat st;
    if (fstat(3, &st) || st.st_size < (off_t)PW_SHM_REGION_BYTES) return 90;
    void *base = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED, 3, 0);
    if (base == MAP_FAILED) return 91;
    pw_shm_header_t *h = base;
    if (h->abi_magic != PW_SHM_ABI_MAGIC ||
        memcmp(h->abi_identity, PW_WORKER_ABI_IDENTITY, PW_SHM_ABI_IDENTITY_BYTES) ||
        atomic_load_explicit(&h->prepared, memory_order_acquire) != 1 ||
        h->phase_count != 1 || h->step_count != 1) return 92;
    char gate[1024] = {0};
    size_t used = 0;
    for (;;) {
        ssize_t n = read(0, gate + used, sizeof(gate) - used - 1);
        if (n < 0 && errno == EINTR) continue;
        if (n < 0) return 93;
        if (n == 0) break;
        used += (size_t)n;
        if (used == sizeof(gate) - 1) return 94;
    }
    h->apply_rc = 0;
    atomic_store_explicit(&h->applied, 1, memory_order_release);
    atomic_store_explicit(&h->phases[0].arrived, 1, memory_order_release);
    if (write(4, "R", 1) != 1) return 95;
    close(4);
    while (atomic_load_explicit(&h->proceed, memory_order_acquire) != 1 || access(gate, F_OK)) usleep(1000);
    atomic_store_explicit(&h->phases[0].acknowledged, 1, memory_order_release);
    atomic_store_explicit(&h->proceed_observed, 1, memory_order_release);
    pw_shm_slot_t *slot = (void *)((char *)base + PW_SHM_HEADER_BYTES);
    slot->rc = 0;
    slot->errno_val = 0;
    atomic_store_explicit(&slot->completed, 1, memory_order_release);
    atomic_store_explicit(&h->phases[0].completed, 1, memory_order_release);
    pw_progress(pw_evidence(base), PW_OP_FINISHED, PW_PROGRESS_RETURNED, UINT32_MAX);
    atomic_store_explicit(&h->done, 1, memory_order_release);
    _exit(0); /* Deliberately never reads exit_requested. */
}
