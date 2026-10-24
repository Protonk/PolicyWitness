/*
 * harness.c — host side of the pre-touch investigation. Not part of the
 * application. It prepares a POSIX shared-memory region the size of the
 * production evidence region exactly as the production host does (shm_open,
 * immediate unlink, ftruncate, one MAP_SHARED mapping, descriptor 3 by
 * posix_spawn file action, policy on descriptor 0), varies only which pages
 * are touched before the child applies its policy, and observes the child
 * independently: mincore over its own mapping, proc_pidinfo region
 * information for the child's mapping, wait4 status and resource usage, and
 * the values it reads back from the probe pages.
 *
 *   pretouch_harness --child PATH --policy-file PATH --policy-name NAME
 *       --touch none|host|child|both|prod --apply 0|1 --probe-page N
 *       --probe-pages N --second-map-page N --out PATH
 *       [--gate-deadline-ms N] [--exit-deadline-ms N]
 *
 * Touch modes before spawn: none touches nothing beyond page 0; host reads
 * and writes back one byte of each probe page; child asks the child to do
 * that before applying; both does both; prod zeroes the whole region, then
 * touches every page as the production host does, and also asks the child.
 *
 * Exit codes: 0 the unit ran and the result was written (whatever the child
 * did); 1 host setup failure; 2 usage.
 */
#define _DARWIN_C_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <libproc.h>
#include <mach/mach_time.h>
#include <signal.h>
#include <spawn.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/proc_info.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include "pretouch_shared.h"

extern char **environ;

#define MAX_PAGES 4096

typedef struct { int rc, err; uint64_t at; unsigned pages; unsigned char vec[MAX_PAGES]; } mincore_snap_t;
typedef struct { int rc, err; uint64_t at; struct proc_regioninfo ri; } region_snap_t;
typedef struct {
    const char *name;
    int state;          /* 0 not run, 1 reached, 2 child reaped first, 3 timeout */
    uint64_t start, end;
} wait_rec_t;

static uint64_t now_ticks(void) { return mach_absolute_time(); }

static void take_mincore(mincore_snap_t *s, void *base, size_t bytes, unsigned pages) {
    memset(s, 0, sizeof(*s));
    s->pages = pages;
    s->at = now_ticks();
    s->rc = mincore(base, bytes, (char *)s->vec);
    s->err = s->rc ? errno : 0;
}

static void take_region(region_snap_t *s, pid_t pid, uint64_t address) {
    memset(s, 0, sizeof(*s));
    s->at = now_ticks();
    if (address == 0) { s->rc = -2; return; }
    int n = proc_pidinfo(pid, PROC_PIDREGIONINFO, address, &s->ri, sizeof(s->ri));
    s->rc = n == (int)sizeof(s->ri) ? 0 : -1;
    s->err = s->rc ? errno : 0;
}

static void emit_mincore(FILE *f, const char *key, const mincore_snap_t *s) {
    fprintf(f, "\"%s\":{\"rc\":%d,\"errno\":%d,\"at\":%llu,\"vec\":[", key, s->rc, s->err, (unsigned long long)s->at);
    for (unsigned i = 0; i < s->pages; i++) fprintf(f, "%s%u", i ? "," : "", s->vec[i]);
    fprintf(f, "]}");
}

static void emit_region(FILE *f, const char *key, const region_snap_t *s) {
    const struct proc_regioninfo *r = &s->ri;
    fprintf(f, "\"%s\":{\"rc\":%d,\"errno\":%d,\"at\":%llu", key, s->rc, s->err, (unsigned long long)s->at);
    if (s->rc == 0) {
        fprintf(f, ",\"protection\":%u,\"max_protection\":%u,\"inheritance\":%u,\"flags\":%u,\"offset\":%llu"
                   ",\"behavior\":%u,\"user_wired_count\":%u,\"user_tag\":%u,\"pages_resident\":%u"
                   ",\"pages_shared_now_private\":%u,\"pages_swapped_out\":%u,\"pages_dirtied\":%u,\"ref_count\":%u"
                   ",\"shadow_depth\":%u,\"share_mode\":%u,\"private_pages_resident\":%u,\"shared_pages_resident\":%u"
                   ",\"obj_id\":%u,\"depth\":%u,\"address\":%llu,\"size\":%llu",
                r->pri_protection, r->pri_max_protection, r->pri_inheritance, r->pri_flags,
                (unsigned long long)r->pri_offset, r->pri_behavior, r->pri_user_wired_count, r->pri_user_tag,
                r->pri_pages_resident, r->pri_pages_shared_now_private, r->pri_pages_swapped_out,
                r->pri_pages_dirtied, r->pri_ref_count, r->pri_shadow_depth, r->pri_share_mode,
                r->pri_private_pages_resident, r->pri_shared_pages_resident, r->pri_obj_id, r->pri_depth,
                (unsigned long long)r->pri_address, (unsigned long long)r->pri_size);
    }
    fprintf(f, "}");
}

static void emit_wait(FILE *f, const wait_rec_t *w) {
    static const char *states[] = {"not_run", "reached", "child_reaped_first", "timeout"};
    fprintf(f, "\"%s\":{\"state\":\"%s\",\"start\":%llu,\"end\":%llu}", w->name, states[w->state],
            (unsigned long long)w->start, (unsigned long long)w->end);
}

static void emit_string(FILE *f, const char *s) {
    fputc('"', f);
    for (; *s; s++) {
        unsigned char ch = (unsigned char)*s;
        if (ch == '"' || ch == '\\') { fputc('\\', f); fputc(ch, f); }
        else if (ch == '\n') fputs("\\n", f);
        else if (ch < 0x20) fprintf(f, "\\u%04x", ch);
        else fputc(ch, f);
    }
    fputc('"', f);
}

static int usage(void) {
    fprintf(stderr, "usage: pretouch_harness --child PATH --policy-file PATH --policy-name NAME --touch MODE"
                    " --apply 0|1 --probe-page N --probe-pages N --second-map-page N --out PATH"
                    " [--gate-deadline-ms N] [--exit-deadline-ms N]\n");
    return 2;
}

int main(int argc, char **argv) {
    const char *child = NULL, *policy_file = NULL, *policy_name = NULL, *touch = NULL, *out = NULL;
    long apply = -1, probe_page = -1, probe_pages = -1, second_map_page = -1;
    long gate_deadline_ms = 5000, exit_deadline_ms = 5000;
    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        printf("pretouch_harness format=%u region_bytes=%u\n", PT_FORMAT, PT_REGION_BYTES);
        return 0;
    }
    for (int i = 1; i + 1 < argc; i += 2) {
        const char *k = argv[i], *v = argv[i + 1];
        if (!strcmp(k, "--child")) child = v;
        else if (!strcmp(k, "--policy-file")) policy_file = v;
        else if (!strcmp(k, "--policy-name")) policy_name = v;
        else if (!strcmp(k, "--touch")) touch = v;
        else if (!strcmp(k, "--apply")) apply = strtol(v, NULL, 10);
        else if (!strcmp(k, "--probe-page")) probe_page = strtol(v, NULL, 10);
        else if (!strcmp(k, "--probe-pages")) probe_pages = strtol(v, NULL, 10);
        else if (!strcmp(k, "--second-map-page")) second_map_page = strtol(v, NULL, 10);
        else if (!strcmp(k, "--out")) out = v;
        else if (!strcmp(k, "--gate-deadline-ms")) gate_deadline_ms = strtol(v, NULL, 10);
        else if (!strcmp(k, "--exit-deadline-ms")) exit_deadline_ms = strtol(v, NULL, 10);
        else return usage();
    }
    if (!child || !policy_file || !policy_name || !touch || !out || apply < 0 || apply > 1
        || probe_page < 1 || probe_pages < 1 || second_map_page < 1) return usage();
    int host_touch = !strcmp(touch, "host") || !strcmp(touch, "both") || !strcmp(touch, "prod");
    int child_touch = !strcmp(touch, "child") || !strcmp(touch, "both") || !strcmp(touch, "prod");
    int prod_touch = !strcmp(touch, "prod");
    if (!host_touch && !child_touch && strcmp(touch, "none") != 0) return usage();

    signal(SIGPIPE, SIG_IGN);
    mach_timebase_info_data_t tb;
    mach_timebase_info(&tb);
    long ps_l = sysconf(_SC_PAGESIZE);
    if (ps_l <= 0) { fprintf(stderr, "harness: sysconf page size\n"); return 1; }
    size_t ps = (size_t)ps_l;
    unsigned pages = (unsigned)((PT_REGION_BYTES + ps - 1) / ps);
    if (pages > MAX_PAGES || (unsigned long)(probe_page + probe_pages) > pages || (unsigned long)second_map_page >= pages
        || (second_map_page >= probe_page && second_map_page < probe_page + probe_pages)) {
        fprintf(stderr, "harness: page selection outside the %u-page region or overlapping\n", pages);
        return 2;
    }

    /* Policy bytes. */
    static char policy[65536];
    size_t policy_len = 0;
    {
        FILE *pf = fopen(policy_file, "rb");
        if (!pf) { fprintf(stderr, "harness: policy file: %s\n", strerror(errno)); return 1; }
        policy_len = fread(policy, 1, sizeof(policy) - 1, pf);
        fclose(pf);
        policy[policy_len] = '\0';
    }

    /* Result file, created exclusively before any child exists. */
    int out_fd = open(out, O_WRONLY | O_CREAT | O_EXCL, 0644);
    if (out_fd < 0) { fprintf(stderr, "harness: out %s: %s\n", out, strerror(errno)); return 1; }
    FILE *of = fdopen(out_fd, "w");

    uint64_t t_setup_start = now_ticks();
    char shm_name[32];
    snprintf(shm_name, sizeof(shm_name), "/pw_pt_%d", getpid());
    int shm_fd = shm_open(shm_name, O_CREAT | O_RDWR | O_EXCL, 0600);
    if (shm_fd < 0) { fprintf(stderr, "harness: shm_open: %s\n", strerror(errno)); return 1; }
    shm_unlink(shm_name);
    fcntl(shm_fd, F_SETFD, 0);
    if (ftruncate(shm_fd, (off_t)PT_REGION_BYTES) != 0) { fprintf(stderr, "harness: ftruncate: %s\n", strerror(errno)); return 1; }
    unsigned char *base = mmap(NULL, PT_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    if (base == MAP_FAILED) { fprintf(stderr, "harness: mmap: %s\n", strerror(errno)); return 1; }

    mincore_snap_t mc_after_map;
    take_mincore(&mc_after_map, base, PT_REGION_BYTES, pages);

    uint64_t nonce;
    arc4random_buf(&nonce, sizeof(nonce));
    volatile unsigned char *vbase = base;
    if (prod_touch) {
        memset(base, 0, PT_REGION_BYTES);
        for (size_t off = 0; off < PT_REGION_BYTES; off += ps) vbase[off] = vbase[off];
        vbase[PT_REGION_BYTES - 1u] = vbase[PT_REGION_BYTES - 1u];
    } else if (host_touch) {
        for (long i = 0; i < probe_pages; i++) {
            size_t off = (size_t)(probe_page + i) * ps;
            vbase[off] = vbase[off];
        }
    }
    pt_ctrl_t *c = (pt_ctrl_t *)base;
    c->magic = PT_MAGIC;
    c->version = PT_FORMAT;
    c->page_size = (uint32_t)ps;
    c->probe_page = (uint32_t)probe_page;
    c->probe_pages = (uint32_t)probe_pages;
    c->second_map_page = (uint32_t)second_map_page;
    c->child_pre_touch = child_touch ? 1u : 0u;
    c->apply = (uint32_t)apply;
    c->nonce = nonce;
    atomic_thread_fence(memory_order_release);

    mincore_snap_t mc_before_spawn;
    take_mincore(&mc_before_spawn, base, PT_REGION_BYTES, pages);
    region_snap_t rg_host_before_spawn;
    take_region(&rg_host_before_spawn, getpid(), (uint64_t)(uintptr_t)base);

    int policy_pipe[2];
    if (pipe(policy_pipe) != 0) { fprintf(stderr, "harness: pipe: %s\n", strerror(errno)); return 1; }
    fcntl(policy_pipe[1], F_SETFD, FD_CLOEXEC);
    posix_spawn_file_actions_t fa;
    posix_spawn_file_actions_init(&fa);
    posix_spawn_file_actions_adddup2(&fa, policy_pipe[0], 0);
    posix_spawn_file_actions_adddup2(&fa, shm_fd, 3);
    char *child_argv[] = {(char *)"pretouch_child", NULL};
    pid_t pid = 0;
    uint64_t t_spawn_start = now_ticks();
    int spawn_rc = posix_spawn(&pid, child, &fa, NULL, child_argv, environ);
    uint64_t t_spawn_end = now_ticks();
    posix_spawn_file_actions_destroy(&fa);
    close(policy_pipe[0]);
    if (spawn_rc != 0) { fprintf(stderr, "harness: posix_spawn: %s\n", strerror(spawn_rc)); return 1; }
    size_t written = 0;
    while (written < policy_len) {
        ssize_t n = write(policy_pipe[1], policy + written, policy_len - written);
        if (n < 0) { if (errno == EINTR) continue; break; }
        written += (size_t)n;
    }
    close(policy_pipe[1]);

    /* Waits. Each polls the control block and the child's status every millisecond. */
    int status = 0, reaped = 0, killed = 0;
    struct rusage child_ru;
    memset(&child_ru, 0, sizeof(child_ru));
    uint64_t gate_ticks = (uint64_t)gate_deadline_ms * 1000000ull * tb.denom / tb.numer;
    uint64_t exit_ticks = (uint64_t)exit_deadline_ms * 1000000ull * tb.denom / tb.numer;
    struct timespec ms1 = {0, 1000000};
    wait_rec_t waits[4] = {{"gate1_wait", 0, 0, 0}, {"gate2_wait", 0, 0, 0}, {"done_wait", 0, 0, 0}, {"exit_wait", 0, 0, 0}};
    mincore_snap_t mc_pre_apply, mc_post_apply, mc_post_store, mc_after_reap;
    region_snap_t rg_pre_apply, rg_post_apply, rg_post_store, rg_host_post_store;
    memset(&mc_pre_apply, 0, sizeof(mc_pre_apply)); memset(&mc_post_apply, 0, sizeof(mc_post_apply));
    memset(&mc_post_store, 0, sizeof(mc_post_store)); memset(&mc_after_reap, 0, sizeof(mc_after_reap));
    memset(&rg_pre_apply, 0, sizeof(rg_pre_apply)); memset(&rg_post_apply, 0, sizeof(rg_post_apply));
    memset(&rg_post_store, 0, sizeof(rg_post_store)); memset(&rg_host_post_store, 0, sizeof(rg_host_post_store));
    uint64_t t_go[3] = {0, 0, 0};

    for (int k = 0; k < 3 && !reaped; k++) {
        wait_rec_t *w = &waits[k];
        w->start = now_ticks();
        for (;;) {
            uint32_t st = atomic_load_explicit(&c->stage, memory_order_acquire);
            uint32_t dn = atomic_load_explicit(&c->done, memory_order_acquire);
            int ready = k == 0 ? st >= PT_STAGE_WAIT_GO1 : k == 1 ? st >= PT_STAGE_WAIT_GO2 : dn == 1u;
            if (ready) { w->state = 1; break; }
            if (dn == 1u) { w->state = 1; break; } /* an early terminal publication ends every wait */
            pid_t r = wait4(pid, &status, WNOHANG, &child_ru);
            if (r == pid) { reaped = 1; w->state = 2; break; }
            if (now_ticks() - w->start > gate_ticks) { w->state = 3; break; }
            nanosleep(&ms1, NULL);
        }
        w->end = now_ticks();
        if (k == 0) { take_mincore(&mc_pre_apply, base, PT_REGION_BYTES, pages); take_region(&rg_pre_apply, pid, c->child_base); }
        if (k == 1) { take_mincore(&mc_post_apply, base, PT_REGION_BYTES, pages); take_region(&rg_post_apply, pid, c->child_base); }
        if (k == 2) {
            take_mincore(&mc_post_store, base, PT_REGION_BYTES, pages);
            take_region(&rg_post_store, pid, c->child_base);
            take_region(&rg_host_post_store, getpid(), (uint64_t)(uintptr_t)base);
        }
        if (w->state == 3) break;
        if (k < 2) {
            t_go[k] = now_ticks();
            atomic_store_explicit(&c->go[k], 1u, memory_order_release);
        }
    }

    /* Read the probe pages and the second-mapping marker through the host mapping. */
    int probe_all_match = 1;
    uint64_t *probe_first = calloc((size_t)probe_pages, sizeof(uint64_t));
    uint64_t *probe_last = calloc((size_t)probe_pages, sizeof(uint64_t));
    for (long i = 0; i < probe_pages; i++) {
        size_t off = (size_t)(probe_page + i) * ps;
        probe_first[i] = *(volatile uint64_t *)(base + off);
        probe_last[i] = *(volatile uint64_t *)(base + off + ps - 8u);
        uint64_t v = nonce ^ (PT_PROBE_SALT | (uint64_t)i);
        if (probe_first[i] != v || probe_last[i] != v) probe_all_match = 0;
    }
    uint64_t second_marker = *(volatile uint64_t *)(base + (size_t)second_map_page * ps);
    int second_marker_match = second_marker == (nonce ^ PT_SECOND_SALT);

    /* Release the child to exit, then wait for it. */
    if (!reaped) {
        t_go[2] = now_ticks();
        atomic_store_explicit(&c->go[2], 1u, memory_order_release);
        wait_rec_t *w = &waits[3];
        w->start = now_ticks();
        for (;;) {
            pid_t r = wait4(pid, &status, WNOHANG, &child_ru);
            if (r == pid) { reaped = 1; w->state = 1; break; }
            if (now_ticks() - w->start > exit_ticks) { w->state = 3; break; }
            nanosleep(&ms1, NULL);
        }
        w->end = now_ticks();
        if (!reaped) {
            kill(pid, SIGKILL);
            killed = 1;
            wait4(pid, &status, 0, &child_ru);
            reaped = 1;
        }
    }
    uint64_t t_reaped = now_ticks();
    take_mincore(&mc_after_reap, base, PT_REGION_BYTES, pages);

    /* Snapshot of the control block after reap. */
    pt_ctrl_t cc;
    memcpy(&cc, c, sizeof(cc));

    fprintf(of, "{\"format\":%u,\"harness_pid\":%d,\"child_pid\":%d,\"child_pid_published\":%d", PT_FORMAT, getpid(), pid, cc.child_pid);
    fprintf(of, ",\"child_path\":"); emit_string(of, child);
    fprintf(of, ",\"policy_name\":"); emit_string(of, policy_name);
    fprintf(of, ",\"policy_text\":"); emit_string(of, policy);
    fprintf(of, ",\"policy_bytes\":%zu,\"policy_bytes_written\":%zu", policy_len, written);
    fprintf(of, ",\"touch\":"); emit_string(of, touch);
    fprintf(of, ",\"host_touch\":%d,\"child_pre_touch\":%d,\"prod_touch\":%d,\"apply\":%ld", host_touch, child_touch, prod_touch, apply);
    fprintf(of, ",\"page_size\":%zu,\"region_bytes\":%u,\"region_pages\":%u", ps, PT_REGION_BYTES, pages);
    fprintf(of, ",\"probe_page\":%ld,\"probe_pages\":%ld,\"second_map_page\":%ld", probe_page, probe_pages, second_map_page);
    fprintf(of, ",\"nonce\":\"%016llx\"", (unsigned long long)nonce);
    fprintf(of, ",\"timebase\":{\"numer\":%u,\"denom\":%u}", tb.numer, tb.denom);
    fprintf(of, ",\"gate_deadline_ms\":%ld,\"exit_deadline_ms\":%ld", gate_deadline_ms, exit_deadline_ms);
    fprintf(of, ",\"host_times\":{\"setup_start\":%llu,\"spawn_start\":%llu,\"spawn_end\":%llu,\"go1\":%llu,\"go2\":%llu,\"go3\":%llu,\"reaped\":%llu}",
            (unsigned long long)t_setup_start, (unsigned long long)t_spawn_start, (unsigned long long)t_spawn_end,
            (unsigned long long)t_go[0], (unsigned long long)t_go[1], (unsigned long long)t_go[2], (unsigned long long)t_reaped);
    fprintf(of, ",\"waits\":{");
    for (int i = 0; i < 4; i++) { if (i) fputc(',', of); emit_wait(of, &waits[i]); }
    fprintf(of, "}");
    fprintf(of, ",\"mincore\":{");
    emit_mincore(of, "after_map", &mc_after_map); fputc(',', of);
    emit_mincore(of, "before_spawn", &mc_before_spawn); fputc(',', of);
    emit_mincore(of, "pre_apply", &mc_pre_apply); fputc(',', of);
    emit_mincore(of, "post_apply", &mc_post_apply); fputc(',', of);
    emit_mincore(of, "post_store", &mc_post_store); fputc(',', of);
    emit_mincore(of, "after_reap", &mc_after_reap);
    fprintf(of, "}");
    fprintf(of, ",\"region\":{");
    emit_region(of, "host_before_spawn", &rg_host_before_spawn); fputc(',', of);
    emit_region(of, "child_pre_apply", &rg_pre_apply); fputc(',', of);
    emit_region(of, "child_post_apply", &rg_post_apply); fputc(',', of);
    emit_region(of, "child_post_store", &rg_post_store); fputc(',', of);
    emit_region(of, "host_post_store", &rg_host_post_store);
    fprintf(of, "}");
    fprintf(of, ",\"child\":{\"reaped\":%d,\"killed\":%d", reaped, killed);
    if (reaped && WIFEXITED(status)) fprintf(of, ",\"exit_code\":%d,\"term_signal\":null", WEXITSTATUS(status));
    else if (reaped && WIFSIGNALED(status)) fprintf(of, ",\"exit_code\":null,\"term_signal\":%d", WTERMSIG(status));
    else fprintf(of, ",\"exit_code\":null,\"term_signal\":null");
    fprintf(of, ",\"rusage\":{\"minflt\":%ld,\"majflt\":%ld,\"utime_us\":%lld,\"stime_us\":%lld}}",
            child_ru.ru_minflt, child_ru.ru_majflt,
            (long long)child_ru.ru_utime.tv_sec * 1000000 + child_ru.ru_utime.tv_usec,
            (long long)child_ru.ru_stime.tv_sec * 1000000 + child_ru.ru_stime.tv_usec);
    fprintf(of, ",\"ctrl\":{\"stage\":%u,\"done\":%u,\"pages_stored\":%u,\"child_base\":%llu,\"policy_len\":%d,\"compile_ok\":%d",
            cc.stage, cc.done, cc.pages_stored, (unsigned long long)cc.child_base, cc.policy_len, cc.compile_ok);
    fprintf(of, ",\"apply_called\":%d,\"apply_rc\":%d,\"apply_errno\":%d,\"witness_open_rc\":%d,\"witness_open_errno\":%d",
            cc.apply_called, cc.apply_rc, cc.apply_errno, cc.witness_open_rc, cc.witness_open_errno);
    fprintf(of, ",\"rusage_rc\":[%d,%d,%d],\"rusage_errno\":[%d,%d,%d],\"minflt\":[%lld,%lld,%lld],\"majflt\":[%lld,%lld,%lld]",
            cc.rusage_rc[0], cc.rusage_rc[1], cc.rusage_rc[2], cc.rusage_errno[0], cc.rusage_errno[1], cc.rusage_errno[2],
            (long long)cc.minflt[0], (long long)cc.minflt[1], (long long)cc.minflt[2],
            (long long)cc.majflt[0], (long long)cc.majflt[1], (long long)cc.majflt[2]);
    fprintf(of, ",\"readback_ok\":%d,\"second_map_rc\":%d,\"second_map_errno\":%d,\"second_map_store_ok\":%d",
            cc.readback_ok, cc.second_map_rc, cc.second_map_errno, cc.second_map_store_ok);
    fprintf(of, ",\"anon_map_rc\":%d,\"anon_map_errno\":%d,\"anon_store_ok\":%d,\"exit_code_intent\":%d",
            cc.anon_map_rc, cc.anon_map_errno, cc.anon_store_ok, cc.exit_code_intent);
    fprintf(of, ",\"compile_error\":"); cc.compile_error[PT_ERROR_MAX - 1] = '\0'; emit_string(of, cc.compile_error);
    fprintf(of, ",\"t\":[");
    for (unsigned i = 0; i < PT_STAGES; i++) fprintf(of, "%s%llu", i ? "," : "", (unsigned long long)cc.t[i]);
    fprintf(of, "],\"t_gate_seen\":[%llu,%llu,%llu]}", (unsigned long long)cc.t_gate_seen[0],
            (unsigned long long)cc.t_gate_seen[1], (unsigned long long)cc.t_gate_seen[2]);
    fprintf(of, ",\"probe\":{\"all_match\":%d,\"values\":[", probe_all_match);
    for (long i = 0; i < probe_pages; i++)
        fprintf(of, "%s{\"page\":%ld,\"first\":\"%016llx\",\"last\":\"%016llx\",\"expected\":\"%016llx\"}", i ? "," : "",
                probe_page + i, (unsigned long long)probe_first[i], (unsigned long long)probe_last[i],
                (unsigned long long)(nonce ^ (PT_PROBE_SALT | (uint64_t)i)));
    fprintf(of, "]},\"second_marker\":{\"match\":%d,\"value\":\"%016llx\"}", second_marker_match, (unsigned long long)second_marker);
    fprintf(of, "}\n");
    fclose(of);
    munmap(base, PT_REGION_BYTES);
    close(shm_fd);
    return 0;
}
