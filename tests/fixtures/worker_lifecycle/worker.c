/* Test-only ABI producer for host lifecycle controls. No policy is compiled or
 * applied. The input text selects a fixture scenario, not a production request
 * seam. Publish payloads with the real ABI protocol; wait for exit_requested
 * before abnormal exit so the host has definitely observed done. */
#include "pw_probe_runner_abi.h"
#include <errno.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    struct stat st;
    /* Darwin may round the backing object to a page boundary. Match the real
     * worker's minimum-size check; map only the ABI region. */
    if (fstat(3, &st) || st.st_size < (off_t)PW_SHM_REGION_BYTES) return 90;
    void *base = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED, 3, 0);
    if (base == MAP_FAILED) return 91;
    pw_shm_header_t *hdr = base;
    if (hdr->abi_version != PW_PROBE_RUNNER_ABI_VERSION ||
        atomic_load_explicit(&hdr->prepared, memory_order_acquire) != 1) return 92;
    char mode[128] = {0};
    size_t used = 0;
    for (;;) {
        ssize_t n = read(0, mode + used, sizeof(mode) - 1 - used);
        if (n < 0 && errno == EINTR) continue;
        if (n < 0) return 93;
        if (!n) break;
        used += (size_t)n;
        if (used == sizeof(mode) - 1) return 94;
    }
    int complete = !strcmp(mode, "complete_hang") || !strcmp(mode, "complete_exit_0") ||
                   !strcmp(mode, "complete_exit_17") || !strcmp(mode, "complete_signal");
    int failure = !strcmp(mode, "reported_failure_hang");
    if (!complete && !failure && strcmp(mode, "no_report_hang")) return 95;
    if (complete) {
        pw_shm_slot_t *slots = (void *)((char *)base + PW_SHM_HEADER_BYTES);
        if (hdr->step_count > PW_SHM_MAX_STEPS) return 96;
        hdr->apply_rc = 0;
        atomic_store_explicit(&hdr->applied, 1, memory_order_release);
        for (uint32_t i = 0; i < hdr->step_count; i++) {
            slots[i].rc = 0;
            slots[i].errno_val = 0;
            snprintf(slots[i].observed_path, sizeof(slots[i].observed_path), "fixture-observation");
            atomic_store_explicit(&slots[i].completed, 1, memory_order_release);
        }
        atomic_store_explicit(&hdr->done, 1, memory_order_release);
    } else if (failure) {
        hdr->apply_rc = -1;
        atomic_store_explicit(&hdr->done, 1, memory_order_release);
    }
    /* Readiness follows publication in this fixture to make driver fault
     * controls deterministic; this is not production readiness coverage. */
    if (write(4, "R", 1) != 1) return 97;
    close(4);
    for (;;) {
        if (atomic_load_explicit(&hdr->exit_requested, memory_order_acquire)) {
            if (!strcmp(mode, "complete_exit_0")) _exit(0);
            if (!strcmp(mode, "complete_exit_17")) _exit(17);
            if (!strcmp(mode, "complete_signal")) {
                signal(SIGTERM, SIG_DFL);
                kill(getpid(), SIGTERM);
                _exit(98);
            }
        }
        usleep(1000);
    }
}
