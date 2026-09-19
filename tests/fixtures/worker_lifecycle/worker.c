/* Test-only ABI producer for host lifecycle controls. No policy is compiled or
 * applied. The input text selects a fixture scenario, not a production request
 * seam. Publish payloads with the real ABI protocol; wait for exit_requested
 * before abnormal exit so the host has definitely observed done. */
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
#include "../diagnostic_transport/worker.h"

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
        if (strchr(mode, '\n') && !strncmp(mode, "close_", 6)) {
            pw_shm_evidence_t *e = pw_evidence(base);
            if (!strncmp(mode, "close_transport_beta\n", 21)) {
                transport_record(e, 1, "transport_beta");
            }
            if (!strncmp(mode, "close_report\n", 13) || !strncmp(mode, "close_hang_report\n", 18)) {
                pw_progress(e, 2, 2, UINT32_MAX);
                pw_failure(e, 239, 987654, 1, -19, 0, 0, UINT32_MAX, 123);
                pw_diagnostic(e, "controlled child closed its input");
            }
            close(0); close(4);
            if (!strncmp(mode, "close_hang_", 11)) {
                /* Test watchdog only: catches a leaked duplicate input FD without
                 * hanging the test host forever before its sentinel starts. */
                for (int i = 0; i < 5000; i++) usleep(1000);
                return 98;
            }
            return 23;
        }
        if (used == sizeof(mode) - 1) return 94;
    }
    if (!strcmp(mode, "early_exit")) return 17;
    pw_shm_evidence_t *e = pw_evidence(base);
    if (!strncmp(mode, "transport_", 10)) {
        transport_record(e, strstr(mode, "beta") != NULL, mode);
        if (!strcmp(mode, "transport_incompatible")) hdr->abi_version = 7;
        hdr->apply_rc = -1;
        atomic_store_explicit(&hdr->done, 1, memory_order_release);
        close(4);
        /* No apply claim, no fabricated attempt. Bound fixture life separately. */
        alarm(10);
        while (!atomic_load_explicit(&hdr->exit_requested, memory_order_acquire)) usleep(1000);
        return 23;
    }
    if (!strncmp(mode, "diagnostic_", 11)) {
        static char long_text[PW_SHM_DIAGNOSTIC_BYTES + 200];
        const char *text = "controlled compiler diagnostic";
        if (!strcmp(mode, "diagnostic_missing")) text = NULL;
        if (!strcmp(mode, "diagnostic_empty")) text = "";
        if (!strcmp(mode, "diagnostic_truncated")) {
            memset(long_text, 'x', sizeof(long_text) - 1);
            text = long_text;
        }
        if (!strcmp(mode, "diagnostic_after_apply")) {
            extern void *sandbox_compile_string(const char *, void *, char **);
            extern int sandbox_apply(void *);
            char *error = NULL;
            void *profile = sandbox_compile_string("(version 1)(deny default)", NULL, &error);
            if (!profile || sandbox_apply(profile)) return 99;
            atomic_store_explicit(&hdr->applied, 1, memory_order_release);
        } else { close(4); }
        pw_progress(e, 5, 2, UINT32_MAX);
        pw_failure(e, 5, 1, 2, 0, 0, 0, UINT32_MAX, 0);
        pw_diagnostic(e, text);
        hdr->apply_rc = -1;
        atomic_store_explicit(&hdr->done, 1, memory_order_release);
        /* CPU-only after application; tests prove text publication survives a
         * deny-default policy without new allocation or diagnostic I/O. */
        while (!atomic_load_explicit(&hdr->exit_requested, memory_order_acquire)) {
            atomic_signal_fence(memory_order_seq_cst);
        }
        _exit(0);
    }
    if (!strcmp(mode, "unfamiliar") || !strcmp(mode, "zero_report")) {
        int unknown = !strcmp(mode, "unfamiliar");
        pw_progress(e, 239, 2, 17);
        pw_failure(e, unknown ? 239 : 0, unknown ? 4000000001u : 0,
                   unknown ? 77 : 0, -123, 1, 0, 17, 7654321);
        /* Unfamiliar kind/result and an observed zero errno must survive. */
        hdr->apply_rc = -1;
        atomic_store_explicit(&hdr->done, 1, memory_order_release);
        close(4);
        while (!atomic_load_explicit(&hdr->exit_requested, memory_order_acquire)) usleep(1000);
        return 0;
    }
    if (!strcmp(mode, "started_attempt") || !strcmp(mode, "late_publication")) {
        pw_shm_slot_t *slot = (void *)((char *)base + PW_SHM_HEADER_BYTES);
        atomic_store_explicit(&hdr->applied, 1, memory_order_release);
        pw_progress(e, 9, 1, 0);
        slot->rc = 12345; /* Poison: never readable until completed publication. */
        if (write(4, "R", 1) != 1) return 97;
        close(4);
        while (!atomic_load_explicit(&hdr->exit_requested, memory_order_acquire)) usleep(1000);
        if (!strcmp(mode, "late_publication")) {
            slot->rc = 0;
            atomic_store_explicit(&slot->completed, 1, memory_order_release);
            pw_progress(e, 9, 2, 0);
            atomic_store_explicit(&hdr->done, 1, memory_order_release);
        }
        return 0;
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
