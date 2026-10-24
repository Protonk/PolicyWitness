/*
 * first_touch_control.c — the production worker, compiled with a real
 * libsandbox, whose terminal-publication seam stores one word into a page of
 * the evidence region that nothing has backed before application. The
 * harness's skip-touch scenarios leave that page unbacked, sample its
 * residency before spawn and at the ready byte, and read the word back after
 * reap through the host mapping. The store runs only after the worker's own
 * `applied` publication, so a compile or apply failure publishes nothing here.
 *
 * Built with PW_FIRST_TOUCH_WORKER_PRETOUCH defined, a constructor touches
 * the probe page through a private mapping before main, that is, before
 * application: the sensitivity control whose condition the harness's
 * ready-byte sample must reject although the worker still publishes.
 */
#include <errno.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

#include "pw_probe_runner_abi.h"
#include "first_touch_probe.h"

static void first_touch_store(pw_shm_header_t *hdr);
#define PW_TERMINAL_PUBLISHED first_touch_store
#include "pw_probe_runner.c"

static void first_touch_store(pw_shm_header_t *hdr) {
    if (atomic_load_explicit(&hdr->applied, memory_order_acquire) != 1u) return;
    volatile uint64_t *word = (volatile uint64_t *)((unsigned char *)hdr + PW_FIRST_TOUCH_PROBE_OFFSET);
    *word = PW_FIRST_TOUCH_PATTERN;
}

#ifdef PW_FIRST_TOUCH_WORKER_PRETOUCH
/* Runs before main, so before the worker maps, compiles or applies. The size
 * check mirrors map_region: the object's reported size is page-rounded. The
 * stderr line is the control's own record that it touched the page; the
 * harness keeps the worker's stderr and the check requires the line. */
__attribute__((constructor)) static void first_touch_pretouch_before_main(void) {
    struct stat st;
    if (fstat(3, &st) != 0 || (size_t)st.st_size < (size_t)PW_SHM_REGION_BYTES) {
        fprintf(stderr, "first_touch_pretouch: skipped, descriptor 3 size %lld\n", (long long)st.st_size);
        return;
    }
    unsigned char *region = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED, 3, 0);
    if (region == MAP_FAILED) {
        fprintf(stderr, "first_touch_pretouch: skipped, mmap: %s\n", strerror(errno));
        return;
    }
    if (((pw_shm_header_t *)region)->abi_magic == PW_SHM_ABI_MAGIC) {
        volatile unsigned char *probe = region + PW_FIRST_TOUCH_PROBE_OFFSET;
        *probe = *probe;
        fprintf(stderr, "first_touch_pretouch: touched offset %zu before main\n", (size_t)PW_FIRST_TOUCH_PROBE_OFFSET);
    } else {
        fprintf(stderr, "first_touch_pretouch: skipped, no ABI magic\n");
    }
    munmap(region, PW_SHM_REGION_BYTES);
}
#endif
