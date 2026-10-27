/*
 * child.c — the pre-touch investigation's experimental worker. Not part of
 * the application. It follows the shipped worker's order: map the inherited
 * descriptor 3, read the policy from descriptor 0, compile, apply, then
 * publish only through the mapping. The host's control block decides whether
 * this process touches the probe pages before application and whether it
 * applies at all; after application it stores a nonce-derived value into each
 * probe page, reads it back, and tries a second mapping of descriptor 3 and an
 * anonymous mapping. Three host gates in shared memory let the host take
 * snapshots between stages. All waits are spins on shared words timed with
 * mach_absolute_time; nothing after application allocates or sleeps.
 *
 * Exit codes: 0 completed; 3 descriptor or mapping failure; 4 control block
 * refused; 5 compile failure; 6 apply failure; 7 a host gate timed out.
 */
#define _DARWIN_C_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <mach/mach_time.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>

#include "pretouch_shared.h"

extern int sandbox_apply(void *profile);
extern void *sandbox_compile_string(const char *str, void *params, char **error);

static uint64_t gate_deadline_ticks;

static void stage(pt_ctrl_t *c, uint32_t s) {
    c->t[s] = mach_absolute_time();
    atomic_store_explicit(&c->stage, s, memory_order_release);
}

static void record_rusage(pt_ctrl_t *c, int k) {
    struct rusage ru;
    memset(&ru, 0, sizeof(ru));
    int rc = getrusage(RUSAGE_SELF, &ru);
    c->rusage_rc[k] = rc;
    c->rusage_errno[k] = rc ? errno : 0;
    c->minflt[k] = ru.ru_minflt;
    c->majflt[k] = ru.ru_majflt;
}

static int wait_gate(pt_ctrl_t *c, int k) {
    uint64_t start = mach_absolute_time();
    for (;;) {
        if (atomic_load_explicit(&c->go[k], memory_order_acquire) != 0u) {
            c->t_gate_seen[k] = mach_absolute_time();
            return 1;
        }
        if (mach_absolute_time() - start > gate_deadline_ticks) return 0;
        for (int i = 0; i < 1000; i++) __asm__ volatile("yield" ::: "memory");
    }
}

static _Noreturn void finish(pt_ctrl_t *c, int code) {
    c->exit_code_intent = code;
    atomic_store_explicit(&c->done, 1u, memory_order_release);
    stage(c, PT_STAGE_DONE);
    stage(c, PT_STAGE_WAIT_GO3);
    if (!wait_gate(c, 2) && code == 0) code = 7;
    _exit(code);
}

static ssize_t read_all(int fd, char *buf, size_t cap) {
    size_t total = 0;
    while (total < cap - 1) {
        ssize_t n = read(fd, buf + total, cap - 1 - total);
        if (n < 0) { if (errno == EINTR) continue; return -1; }
        if (n == 0) break;
        total += (size_t)n;
    }
    buf[total] = '\0';
    return total == cap - 1 ? -2 : (ssize_t)total;
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "--version") == 0) {
        printf("pretouch_child format=%u region_bytes=%u\n", PT_FORMAT, PT_REGION_BYTES);
        return 0;
    }
    mach_timebase_info_data_t tb;
    if (mach_timebase_info(&tb) != 0 || tb.numer == 0 || tb.denom == 0) return 3;
    gate_deadline_ticks = (uint64_t)10000000000ull * tb.denom / tb.numer; /* 10 s */

    struct stat st;
    if (fstat(3, &st) != 0 || (size_t)st.st_size < PT_REGION_BYTES) return 3;
    unsigned char *base = mmap(NULL, PT_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED, 3, 0);
    if (base == MAP_FAILED) return 3;
    pt_ctrl_t *c = (pt_ctrl_t *)base;
    if (c->magic != PT_MAGIC || c->version != PT_FORMAT || c->page_size == 0) return 4;
    c->child_pid = getpid();
    c->child_base = (uint64_t)(uintptr_t)base;
    stage(c, PT_STAGE_MAPPED);

    static char policy[65536];
    ssize_t plen = read_all(0, policy, sizeof(policy));
    c->policy_len = (int32_t)plen;
    stage(c, PT_STAGE_POLICY_READ);

    const size_t ps = c->page_size;
    volatile unsigned char *probe0 = base + (size_t)c->probe_page * ps;
    if (c->child_pre_touch) {
        /* The production host's touch: read a byte of each page and write it back. */
        for (uint32_t i = 0; i < c->probe_pages; i++) {
            volatile unsigned char *p = probe0 + (size_t)i * ps;
            *p = *p;
        }
    }
    stage(c, PT_STAGE_PRE_TOUCHED);

    void *profile = NULL;
    if (c->apply) {
        char *err = NULL;
        profile = sandbox_compile_string(policy, NULL, &err);
        c->compile_ok = profile != NULL;
        if (!profile) {
            snprintf(c->compile_error, sizeof(c->compile_error), "%s", err ? err : "(no error text)");
            if (err) free(err);
            stage(c, PT_STAGE_COMPILED);
            finish(c, 5);
        }
    }
    stage(c, PT_STAGE_COMPILED);
    record_rusage(c, 0);

    stage(c, PT_STAGE_WAIT_GO1);
    if (!wait_gate(c, 0)) finish(c, 7);

    if (c->apply) {
        c->apply_called = 1;
        int rc = sandbox_apply(profile);
        int e = errno;
        c->apply_rc = rc;
        c->apply_errno = rc ? e : 0;
        if (rc != 0) { stage(c, PT_STAGE_APPLIED); finish(c, 6); }
    }
    stage(c, PT_STAGE_APPLIED);

    /* Witness that the policy is in force: a file open the deny-default
     * policies refuse and the allow-default policy permits. */
    int fd = open("/etc/hosts", O_RDONLY);
    c->witness_open_rc = fd;
    c->witness_open_errno = fd < 0 ? errno : 0;
    if (fd >= 0) close(fd);
    stage(c, PT_STAGE_WITNESSED);
    record_rusage(c, 1);

    stage(c, PT_STAGE_WAIT_GO2);
    if (!wait_gate(c, 1)) finish(c, 7);

    stage(c, PT_STAGE_STORING);
    for (uint32_t i = 0; i < c->probe_pages; i++) {
        uint64_t v = c->nonce ^ (PT_PROBE_SALT | i);
        volatile uint64_t *first = (volatile uint64_t *)(probe0 + (size_t)i * ps);
        volatile uint64_t *last = (volatile uint64_t *)(probe0 + (size_t)i * ps + ps - 8u);
        *first = v;
        *last = v;
        atomic_store_explicit(&c->pages_stored, i + 1u, memory_order_release);
    }
    record_rusage(c, 2);
    stage(c, PT_STAGE_STORED);

    int ok = 1;
    for (uint32_t i = 0; i < c->probe_pages; i++) {
        uint64_t v = c->nonce ^ (PT_PROBE_SALT | i);
        if (*(volatile uint64_t *)(probe0 + (size_t)i * ps) != v
            || *(volatile uint64_t *)(probe0 + (size_t)i * ps + ps - 8u) != v) ok = 0;
    }
    c->readback_ok = ok;
    stage(c, PT_STAGE_READBACK);

    /* A second mapping of the same descriptor after application. */
    void *m2 = mmap(NULL, PT_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED, 3, 0);
    c->second_map_rc = m2 == MAP_FAILED ? -1 : 0;
    c->second_map_errno = m2 == MAP_FAILED ? errno : 0;
    if (m2 != MAP_FAILED) {
        *(volatile uint64_t *)((unsigned char *)m2 + (size_t)c->second_map_page * ps) = c->nonce ^ PT_SECOND_SALT;
        c->second_map_store_ok = 1;
    }
    stage(c, PT_STAGE_SECOND_MAP);

    /* A fresh anonymous page after application. */
    void *a = mmap(NULL, ps, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
    c->anon_map_rc = a == MAP_FAILED ? -1 : 0;
    c->anon_map_errno = a == MAP_FAILED ? errno : 0;
    if (a != MAP_FAILED) {
        *(volatile uint64_t *)a = c->nonce ^ PT_ANON_SALT;
        c->anon_store_ok = *(volatile uint64_t *)a == (c->nonce ^ PT_ANON_SALT);
    }
    stage(c, PT_STAGE_ANON_MAP);

    finish(c, 0);
}
