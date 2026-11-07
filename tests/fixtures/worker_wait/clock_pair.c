/*
 * clock_pair.c: calibration pair for the worker-wait pilot's timestamp
 * instrument, independent of PolicyWitness. The parent forks a writer and a
 * reader that share one anonymous MAP_SHARED mapping. Per trial the reader
 * stamps and release-stores the ready word, then polls the published word
 * with the selected pacing. The writer polls ready with yield hints, stamps
 * its arm on seeing it, optionally sleeps the injected delay, stamps the
 * publication, stores that stamp in the mailbox, release-stores the published
 * word and stamps again. Every stamp is mach_continuous_time. The parent
 * prints raw ticks and per-trial records as one JSON object on stdout.
 *
 * Judgments belong to the Python reader. This program fails (nonzero exit,
 * stderr diagnostic, JSON with "status": "failed") only on mechanics:
 * arguments, a child error or wait timeout, a protocol value, a mailbox
 * mismatch or the watchdog. It applies no sandbox and runs no host or worker
 * code, so it measures neither real loop.
 *
 *   clock_pair --mode busy|sleep2|sleep1 --inject 0|1|2|3 --trials N
 *              --read-overhead-samples N [--inject-method nanosleep|mach_wait_until]
 */
#include <errno.h>
#include <inttypes.h>
#include <mach/mach_time.h>
#include <signal.h>
#include <stdatomic.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#if !defined(__aarch64__)
#error "clock_pair paces with the arm64 yield hint, as the worker's cpu_relax does"
#endif

#define HINTS_PER_PASS 1000u
#define MAX_TRIALS 5000u
#define MIN_OVERHEAD_SAMPLES 1000ull
#define MAX_OVERHEAD_SAMPLES 50000000ull
#define CHILD_WAIT_NS 2000000000ull /* bound on any single wait inside a child */
#define WATCHDOG_GRACE_S 2u
#define HISTOGRAM_BUCKETS 65

enum mode { MODE_BUSY, MODE_SLEEP2, MODE_SLEEP1 };
enum method { METHOD_NONE, METHOD_NANOSLEEP, METHOD_MACH_WAIT_UNTIL };
enum failure { F_NONE, F_TIMEOUT, F_PROTOCOL, F_ABORTED, F_INJECT_SLEEP, F_PACE_SLEEP };
static const char *const failure_names[] = {
    "none", "wait_timeout", "protocol_value", "aborted_by_parent", "inject_sleep_failed", "pacing_sleep_failed"};
static const char *const mode_names[] = {"busy", "sleep2", "sleep1"};
static const char *const method_names[] = {"none", "nanosleep", "mach_wait_until"};

typedef struct {
    uint64_t armed_raw, published_raw, post_store_raw, ready_passes;
    int64_t sleep_rc, sleep_errno;
    _Atomic uint32_t complete;
    uint32_t reserved;
} writer_record_t;

typedef struct {
    uint64_t ready_raw, first_pass_raw, last_negative_raw, pass_sample_raw, observed_raw, published_raw_seen;
    uint64_t passes, max_pass_interval_ticks;
    uint32_t has_last_negative;
    _Atomic uint32_t complete;
} reader_record_t;

/* Each word with a different writer sits on its own 128-byte line. */
typedef struct {
    _Alignas(128) _Atomic uint32_t ready;     /* reader: trial index + 1 it now polls for */
    _Alignas(128) _Atomic uint32_t published; /* writer: trial index + 1 it has published */
    uint64_t mailbox_raw;                     /* writer: publication stamp of that trial */
    _Alignas(128) _Atomic uint32_t abort_requested;
    _Alignas(128) _Atomic uint32_t writer_state; /* 0 running, 1 finished, 2 failed */
    uint32_t writer_failure, writer_failure_trial, writer_failure_value;
    _Alignas(128) _Atomic uint32_t reader_state;
    uint32_t reader_failure, reader_failure_trial, reader_failure_value;
    uint64_t pass_histogram[HISTOGRAM_BUCKETS]; /* reader: pass intervals, bucket = bit length of ticks */
} control_t;

typedef struct {
    uint64_t n, total_ticks, zero_delta_reads, max_delta_ticks;
} overhead_t;

static mach_timebase_info_data_t tb;
static volatile sig_atomic_t alarm_fired;

static uint64_t ticks_to_ns(uint64_t ticks) { return (uint64_t)(((__uint128_t)ticks * tb.numer) / tb.denom); }
static uint64_t ns_to_ticks(uint64_t ns) { return (uint64_t)(((__uint128_t)ns * tb.denom) / tb.numer); }
static int64_t diff_ns(uint64_t later, uint64_t earlier) {
    return later >= earlier ? (int64_t)ticks_to_ns(later - earlier) : -(int64_t)ticks_to_ns(earlier - later);
}
static unsigned bucket(uint64_t ticks) { return ticks ? 64u - (unsigned)__builtin_clzll(ticks) : 0u; }

static inline void relax_pass(void) {
    for (unsigned k = 0; k < HINTS_PER_PASS; k++) __asm__ volatile("yield" ::: "memory");
}

/* Map the pages this child will touch before its first timed access. */
static void pretouch(void *base, size_t bytes) {
    long page = sysconf(_SC_PAGESIZE);
    volatile unsigned char *p = base;
    for (size_t off = 0; off < bytes; off += (size_t)page) p[off] = p[off];
    if (bytes) p[bytes - 1] = p[bytes - 1];
}

static int fail_child(_Atomic uint32_t *state, uint32_t *failure, uint32_t *trial, uint32_t *value,
                      enum failure why, uint32_t at, uint32_t seen) {
    *failure = (uint32_t)why;
    *trial = at;
    *value = seen;
    atomic_store_explicit(state, 2u, memory_order_release);
    return 1;
}
#define WRITER_FAIL(why, at, seen) \
    fail_child(&c->writer_state, &c->writer_failure, &c->writer_failure_trial, &c->writer_failure_value, why, at, seen)
#define READER_FAIL(why, at, seen) \
    fail_child(&c->reader_state, &c->reader_failure, &c->reader_failure_trial, &c->reader_failure_value, why, at, seen)

static int writer(control_t *c, writer_record_t *rec, uint32_t trials, uint64_t inject_ns, enum method method) {
    const uint64_t limit = ns_to_ticks(CHILD_WAIT_NS);
    pretouch(rec, sizeof(*rec) * trials);
    atomic_fetch_add_explicit(&c->published, 0u, memory_order_relaxed);
    (void)atomic_load_explicit(&c->ready, memory_order_relaxed);
    for (uint32_t i = 0; i < trials; i++) {
        const uint32_t want = i + 1u;
        uint64_t passes = 0, armed;
        const uint64_t start = mach_continuous_time();
        for (;;) {
            uint32_t v = atomic_load_explicit(&c->ready, memory_order_acquire);
            if (v == want) {
                armed = mach_continuous_time();
                passes++;
                break;
            }
            passes++;
            if (v != i) return WRITER_FAIL(F_PROTOCOL, i, v);
            if (atomic_load_explicit(&c->abort_requested, memory_order_relaxed)) return WRITER_FAIL(F_ABORTED, i, v);
            if (mach_continuous_time() - start > limit) return WRITER_FAIL(F_TIMEOUT, i, v);
            relax_pass();
        }
        int64_t rc = 0, err = 0;
        if (method == METHOD_NANOSLEEP) {
            struct timespec ts = {.tv_sec = (time_t)(inject_ns / 1000000000ull),
                                  .tv_nsec = (long)(inject_ns % 1000000000ull)};
            errno = 0;
            rc = nanosleep(&ts, NULL);
            err = rc ? errno : 0;
        } else if (method == METHOD_MACH_WAIT_UNTIL) {
            rc = mach_wait_until(mach_absolute_time() + ns_to_ticks(inject_ns));
        }
        rec[i].sleep_rc = rc;
        rec[i].sleep_errno = err;
        if (rc != 0) return WRITER_FAIL(F_INJECT_SLEEP, i, (uint32_t)rc);
        const uint64_t published = mach_continuous_time();
        c->mailbox_raw = published;
        atomic_store_explicit(&c->published, want, memory_order_release);
        const uint64_t after = mach_continuous_time();
        rec[i].armed_raw = armed;
        rec[i].published_raw = published;
        rec[i].post_store_raw = after;
        rec[i].ready_passes = passes;
        atomic_store_explicit(&rec[i].complete, 1u, memory_order_release);
    }
    atomic_store_explicit(&c->writer_state, 1u, memory_order_release);
    return 0;
}

static int reader(control_t *c, reader_record_t *rec, uint32_t trials, enum mode mode) {
    const uint64_t limit = ns_to_ticks(CHILD_WAIT_NS);
    const struct timespec pace = {.tv_sec = 0, .tv_nsec = mode == MODE_SLEEP2 ? 2000000L : 1000000L};
    pretouch(rec, sizeof(*rec) * trials);
    atomic_fetch_add_explicit(&c->ready, 0u, memory_order_relaxed);
    (void)atomic_load_explicit(&c->published, memory_order_relaxed);
    for (uint32_t i = 0; i < trials; i++) {
        const uint32_t want = i + 1u;
        uint64_t passes = 0, first = 0, previous = 0, last_negative = 0, max_interval = 0, sample, observed = 0;
        uint32_t has_negative = 0;
        const uint64_t ready = mach_continuous_time();
        atomic_store_explicit(&c->ready, want, memory_order_release);
        for (;;) {
            sample = mach_continuous_time();
            uint32_t v = atomic_load_explicit(&c->published, memory_order_acquire);
            if (v == want) observed = mach_continuous_time();
            passes++;
            if (passes == 1) {
                first = sample;
            } else {
                uint64_t d = sample - previous;
                c->pass_histogram[bucket(d)]++;
                if (d > max_interval) max_interval = d;
            }
            previous = sample;
            if (v == want) break;
            if (v != i) return READER_FAIL(F_PROTOCOL, i, v);
            if (atomic_load_explicit(&c->abort_requested, memory_order_relaxed)) return READER_FAIL(F_ABORTED, i, v);
            if (sample - ready > limit) return READER_FAIL(F_TIMEOUT, i, v);
            last_negative = sample;
            has_negative = 1;
            if (mode == MODE_BUSY) {
                relax_pass();
            } else if (nanosleep(&pace, NULL) != 0) {
                return READER_FAIL(F_PACE_SLEEP, i, (uint32_t)errno);
            }
        }
        rec[i].ready_raw = ready;
        rec[i].first_pass_raw = first;
        rec[i].last_negative_raw = last_negative;
        rec[i].has_last_negative = has_negative;
        rec[i].pass_sample_raw = sample;
        rec[i].observed_raw = observed;
        rec[i].published_raw_seen = c->mailbox_raw;
        rec[i].passes = passes;
        rec[i].max_pass_interval_ticks = max_interval;
        atomic_store_explicit(&rec[i].complete, 1u, memory_order_release);
    }
    atomic_store_explicit(&c->reader_state, 1u, memory_order_release);
    return 0;
}

static overhead_t read_overhead(uint64_t n) {
    overhead_t o = {.n = n};
    const uint64_t first = mach_continuous_time();
    uint64_t previous = first;
    for (uint64_t k = 0; k < n; k++) {
        uint64_t current = mach_continuous_time();
        uint64_t d = current - previous;
        if (d == 0) o.zero_delta_reads++;
        if (d > o.max_delta_ticks) o.max_delta_ticks = d;
        previous = current;
    }
    o.total_ticks = previous - first;
    return o;
}

static void print_overhead(const char *key, const char *when, overhead_t o) {
    uint64_t total_ns = ticks_to_ns(o.total_ticks);
    printf(",\"%s\":{\"when\":\"%s\",\"n\":%" PRIu64 ",\"total_ticks\":%" PRIu64 ",\"total_ns\":%" PRIu64
           ",\"per_read_ns\":%.3f,\"zero_delta_reads\":%" PRIu64 ",\"max_delta_ticks\":%" PRIu64 "}",
           key, when, o.n, o.total_ticks, total_ns, (double)total_ns / (double)o.n, o.zero_delta_reads,
           o.max_delta_ticks);
}

static void print_u64_or_null(const char *key, int present, uint64_t value) {
    if (present) printf(",\"%s\":%" PRIu64, key, value);
    else printf(",\"%s\":null", key);
}

static void print_child(const char *name, pid_t pid, int reaped, int status, uint32_t state, uint32_t failure,
                        uint32_t trial, uint32_t value) {
    printf("\"%s\":{\"pid\":%d,\"reaped\":%s", name, (int)pid, reaped ? "true" : "false");
    if (reaped && WIFEXITED(status)) printf(",\"exit_code\":%d,\"term_signal\":null", WEXITSTATUS(status));
    else if (reaped && WIFSIGNALED(status)) printf(",\"exit_code\":null,\"term_signal\":%d", WTERMSIG(status));
    else printf(",\"exit_code\":null,\"term_signal\":null");
    printf(",\"state\":\"%s\",\"failure\":\"%s\"", state == 1u ? "finished" : state == 2u ? "failed" : "running",
           failure < sizeof(failure_names) / sizeof(failure_names[0]) ? failure_names[failure] : "unknown");
    if (state == 2u) printf(",\"failure_trial\":%u,\"failure_value\":%u}", trial, value);
    else printf(",\"failure_trial\":null,\"failure_value\":null}");
}

static void describe_child(char *out, size_t size, const char *name, pid_t pid, int reaped, int status,
                           uint32_t state, uint32_t failure, uint32_t trial) {
    char how[48];
    if (pid < 0) snprintf(how, sizeof(how), "not started");
    else if (!reaped) snprintf(how, sizeof(how), "not reaped");
    else if (WIFEXITED(status)) snprintf(how, sizeof(how), "exit %d", WEXITSTATUS(status));
    else if (WIFSIGNALED(status)) snprintf(how, sizeof(how), "signal %d", WTERMSIG(status));
    else snprintf(how, sizeof(how), "status %d", status);
    snprintf(out, size, "%s %s, %s", name, how, state == 1u ? "finished" : state == 2u ? "failed" : "running");
    if (state == 2u)
        snprintf(out + strlen(out), size - strlen(out), " (%s at trial %u)",
                 failure < sizeof(failure_names) / sizeof(failure_names[0]) ? failure_names[failure] : "unknown", trial);
}

static void on_alarm(int sig) {
    (void)sig;
    alarm_fired = 1;
}

static int usage(const char *why) {
    fprintf(stderr, "clock_pair: %s\nusage: clock_pair --mode busy|sleep2|sleep1 --inject 0|1|2|3 --trials N "
                    "--read-overhead-samples N [--inject-method nanosleep|mach_wait_until]\n", why);
    return 2;
}

static int parse_u64(const char *text, uint64_t lo, uint64_t hi, uint64_t *out) {
    char *end = NULL;
    if (!text || !*text || *text == '-' || *text == '+') return -1;
    errno = 0;
    unsigned long long v = strtoull(text, &end, 10);
    if (errno || *end || v < lo || v > hi) return -1;
    *out = v;
    return 0;
}

int main(int argc, char **argv) {
    int mode = -1, method = METHOD_NANOSLEEP, method_given = 0;
    uint64_t inject_ms = UINT64_MAX, trials = 0, samples = 0;
    for (int i = 1; i < argc; i += 2) {
        if (i + 1 >= argc) return usage("missing value");
        const char *k = argv[i], *v = argv[i + 1];
        if (!strcmp(k, "--mode") && mode < 0) {
            for (int m = 0; m < 3; m++) if (!strcmp(v, mode_names[m])) mode = m;
            if (mode < 0) return usage("unknown mode");
        } else if (!strcmp(k, "--inject") && inject_ms == UINT64_MAX) {
            if (parse_u64(v, 0, 3, &inject_ms)) return usage("inject must be 0, 1, 2 or 3");
        } else if (!strcmp(k, "--trials") && !trials) {
            if (parse_u64(v, 1, MAX_TRIALS, &trials)) return usage("trials must be 1..5000");
        } else if (!strcmp(k, "--read-overhead-samples") && !samples) {
            if (parse_u64(v, MIN_OVERHEAD_SAMPLES, MAX_OVERHEAD_SAMPLES, &samples))
                return usage("read-overhead-samples must be 1000..50000000");
        } else if (!strcmp(k, "--inject-method") && !method_given) {
            method_given = 1;
            if (!strcmp(v, "nanosleep")) method = METHOD_NANOSLEEP;
            else if (!strcmp(v, "mach_wait_until")) method = METHOD_MACH_WAIT_UNTIL;
            else return usage("unknown inject method");
        } else {
            return usage("unknown or repeated argument");
        }
    }
    if (mode < 0 || inject_ms == UINT64_MAX || !trials || !samples) return usage("missing required argument");
    if (inject_ms == 0) method = METHOD_NONE;
    if (mach_timebase_info(&tb) != KERN_SUCCESS || !tb.numer || !tb.denom) {
        fprintf(stderr, "clock_pair: mach_timebase_info failed\n");
        return 1;
    }
    const uint32_t n = (uint32_t)trials;
    const uint64_t inject_ns = inject_ms * 1000000ull;
    const unsigned watchdog_s = 5u + (unsigned)((trials * (inject_ms + 10u) + 999u) / 1000u);

    const overhead_t before = read_overhead(samples);

    const size_t page = (size_t)sysconf(_SC_PAGESIZE);
    const size_t writer_off = (sizeof(control_t) + 127u) & ~(size_t)127u;
    const size_t reader_off = (writer_off + sizeof(writer_record_t) * n + 127u) & ~(size_t)127u;
    const size_t bytes = ((reader_off + sizeof(reader_record_t) * n) + page - 1u) & ~(page - 1u);
    unsigned char *base = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    if (base == MAP_FAILED) {
        fprintf(stderr, "clock_pair: mmap: %s\n", strerror(errno));
        return 1;
    }
    memset(base, 0, bytes);
    control_t *c = (control_t *)base;
    writer_record_t *wrec = (writer_record_t *)(base + writer_off);
    reader_record_t *rrec = (reader_record_t *)(base + reader_off);

    const uint64_t start_continuous = mach_continuous_time(), start_absolute = mach_absolute_time();
    fflush(NULL);
    pid_t wpid = fork();
    if (wpid < 0) {
        fprintf(stderr, "clock_pair: fork writer: %s\n", strerror(errno));
        return 1;
    }
    if (wpid == 0) _exit(writer(c, wrec, n, inject_ns, (enum method)method) ? 10 : 0);
    pid_t rpid = fork();
    if (rpid == 0) _exit(reader(c, rrec, n, (enum mode)mode) ? 11 : 0);
    int fork_errno = rpid < 0 ? errno : 0;

    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = on_alarm;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGALRM, &sa, NULL); /* no SA_RESTART: waitpid returns EINTR */
    if (rpid < 0) atomic_store_explicit(&c->abort_requested, 1u, memory_order_relaxed);
    alarm(watchdog_s);

    int wstatus = 0, rstatus = 0, wreaped = 0, rreaped = 0, stage = 0, sigkill_sent = 0, wait_errno = 0;
    while (!(wreaped && (rreaped || rpid < 0))) {
        int status;
        pid_t p = waitpid(-1, &status, 0);
        if (p < 0) {
            if (errno == EINTR) {
                if (alarm_fired) {
                    alarm_fired = 0;
                    if (stage == 0) {
                        stage = 1;
                        atomic_store_explicit(&c->abort_requested, 1u, memory_order_relaxed);
                        alarm(WATCHDOG_GRACE_S);
                    } else {
                        stage = 2;
                        sigkill_sent = 1;
                        if (!wreaped) kill(wpid, SIGKILL);
                        if (!rreaped && rpid > 0) kill(rpid, SIGKILL);
                    }
                }
                continue;
            }
            wait_errno = errno;
            break;
        }
        if (p == wpid) {
            wstatus = status;
            wreaped = 1;
        } else if (p == rpid) {
            rstatus = status;
            rreaped = 1;
        } else {
            continue;
        }
        if (!(WIFEXITED(status) && WEXITSTATUS(status) == 0))
            atomic_store_explicit(&c->abort_requested, 1u, memory_order_relaxed);
    }
    alarm(0);
    const uint64_t end_continuous = mach_continuous_time(), end_absolute = mach_absolute_time();
    const overhead_t after = read_overhead(samples);

    const uint32_t wstate = atomic_load_explicit(&c->writer_state, memory_order_acquire);
    const uint32_t rstate = atomic_load_explicit(&c->reader_state, memory_order_acquire);
    char failure[256] = "";
    uint32_t complete_trials = 0, mailbox_mismatches = 0;
    for (uint32_t i = 0; i < n; i++) {
        int w = wreaped && atomic_load_explicit(&wrec[i].complete, memory_order_acquire);
        int r = rreaped && atomic_load_explicit(&rrec[i].complete, memory_order_acquire);
        if (w && r) {
            complete_trials++;
            if (rrec[i].published_raw_seen != wrec[i].published_raw) mailbox_mismatches++;
        }
    }
    if (fork_errno) snprintf(failure, sizeof(failure), "fork reader: %s", strerror(fork_errno));
    else if (wait_errno) snprintf(failure, sizeof(failure), "waitpid: %s", strerror(wait_errno));
    else if (stage) {
        char w[120], r[120];
        describe_child(w, sizeof(w), "writer", wpid, wreaped, wstatus, wstate, c->writer_failure, c->writer_failure_trial);
        describe_child(r, sizeof(r), "reader", rpid, rreaped, rstatus, rstate, c->reader_failure, c->reader_failure_trial);
        snprintf(failure, sizeof(failure), "watchdog expired after %u s%s; %s; %s", watchdog_s,
                 sigkill_sent ? ", children killed" : ", abort requested", w, r);
    } else if (!(WIFEXITED(wstatus) && WEXITSTATUS(wstatus) == 0) || wstate != 1u ||
             !(WIFEXITED(rstatus) && WEXITSTATUS(rstatus) == 0) || rstate != 1u) {
        char w[120], r[120];
        describe_child(w, sizeof(w), "writer", wpid, wreaped, wstatus, wstate, c->writer_failure, c->writer_failure_trial);
        describe_child(r, sizeof(r), "reader", rpid, rreaped, rstatus, rstate, c->reader_failure, c->reader_failure_trial);
        snprintf(failure, sizeof(failure), "a child did not finish: %s; %s", w, r);
    } else if (complete_trials != n)
        snprintf(failure, sizeof(failure), "%u of %u trials complete", complete_trials, n);
    else if (mailbox_mismatches)
        snprintf(failure, sizeof(failure), "%u trials saw a mailbox stamp other than the writer's", mailbox_mismatches);

    printf("{\"version\":1,\"fixture\":\"worker_wait_clock_pair\",\"status\":\"%s\",\"failure\":",
           failure[0] ? "failed" : "complete");
    if (failure[0]) printf("\"%s\"", failure);
    else printf("null");
    printf(",\"clock\":\"mach_continuous_time\",\"timebase\":{\"numer\":%u,\"denom\":%u}", tb.numer, tb.denom);
    printf(",\"mode\":\"%s\"", mode_names[mode]);
    if (mode == MODE_BUSY) printf(",\"pacing\":{\"kind\":\"yield_hints\",\"hints_per_pass\":%u}", HINTS_PER_PASS);
    else printf(",\"pacing\":{\"kind\":\"nanosleep\",\"requested_ns\":%d}", mode == MODE_SLEEP2 ? 2000000 : 1000000);
    printf(",\"writer_pacing\":{\"kind\":\"yield_hints\",\"hints_per_pass\":%u}", HINTS_PER_PASS);
    printf(",\"injected_ms\":%" PRIu64 ",\"injected_requested_ns\":%" PRIu64 ",\"inject_method\":\"%s\"", inject_ms,
           inject_ns, method_names[method]);
    printf(",\"trials_requested\":%u,\"trials_complete\":%u,\"read_overhead_samples\":%" PRIu64, n,
           complete_trials, samples);
    printf(",\"child_wait_limit_ns\":%llu,\"watchdog\":{\"seconds\":%u,\"grace_seconds\":%u,\"stage\":%d,"
           "\"sigkill_sent\":%s}", CHILD_WAIT_NS, watchdog_s, WATCHDOG_GRACE_S, stage, sigkill_sent ? "true" : "false");
    printf(",\"parent_pid\":%d,\"children\":{", (int)getpid());
    print_child("writer", wpid, wreaped, wstatus, wstate, c->writer_failure, c->writer_failure_trial,
                c->writer_failure_value);
    putchar(',');
    print_child("reader", rpid, rreaped, rstatus, rstate, c->reader_failure, c->reader_failure_trial,
                c->reader_failure_value);
    printf("}");
    printf(",\"clock_start\":{\"continuous_raw\":%" PRIu64 ",\"absolute_raw\":%" PRIu64 "}", start_continuous,
           start_absolute);
    printf(",\"clock_end\":{\"continuous_raw\":%" PRIu64 ",\"absolute_raw\":%" PRIu64 "}", end_continuous,
           end_absolute);
    print_overhead("read_overhead", "before_fork", before);
    print_overhead("read_overhead_after", "after_reap", after);
    printf(",\"pass_histogram\":{\"unit\":\"ticks\",\"bucket\":\"bit_length\",\"counts\":[");
    for (int b = 0; b < HISTOGRAM_BUCKETS; b++) printf("%s%" PRIu64, b ? "," : "", rreaped ? c->pass_histogram[b] : 0);
    printf("]}");
    printf(",\"trials\":[");
    for (uint32_t i = 0; i < n; i++) {
        int w = wreaped && atomic_load_explicit(&wrec[i].complete, memory_order_acquire);
        int r = rreaped && atomic_load_explicit(&rrec[i].complete, memory_order_acquire);
        const writer_record_t *x = &wrec[i];
        const reader_record_t *y = &rrec[i];
        printf("%s{\"index\":%u,\"writer_complete\":%s,\"reader_complete\":%s", i ? "," : "", i, w ? "true" : "false",
               r ? "true" : "false");
        print_u64_or_null("ready_raw", r, y->ready_raw);
        print_u64_or_null("armed_raw", w, x->armed_raw);
        print_u64_or_null("published_raw", w, x->published_raw);
        print_u64_or_null("post_store_raw", w, x->post_store_raw);
        print_u64_or_null("first_pass_raw", r, y->first_pass_raw);
        print_u64_or_null("last_negative_raw", r && y->has_last_negative, y->last_negative_raw);
        print_u64_or_null("pass_sample_raw", r, y->pass_sample_raw);
        print_u64_or_null("observed_raw", r, y->observed_raw);
        print_u64_or_null("published_raw_seen", r, y->published_raw_seen);
        print_u64_or_null("passes", r, y->passes);
        print_u64_or_null("max_pass_interval_ticks", r, y->max_pass_interval_ticks);
        print_u64_or_null("writer_ready_passes", w, x->ready_passes);
        if (w) printf(",\"sleep_rc\":%" PRId64 ",\"sleep_errno\":%" PRId64, x->sleep_rc, x->sleep_errno);
        else printf(",\"sleep_rc\":null,\"sleep_errno\":null");
        if (w && r) printf(",\"latency_ns\":%" PRId64, diff_ns(y->observed_raw, x->published_raw));
        else printf(",\"latency_ns\":null");
        if (w) printf(",\"actual_injected_ns\":%" PRId64 "}", diff_ns(x->published_raw, x->armed_raw));
        else printf(",\"actual_injected_ns\":null}");
    }
    printf("]}\n");
    if (fflush(stdout) != 0 || ferror(stdout)) {
        fprintf(stderr, "clock_pair: writing stdout failed\n");
        return 1;
    }
    if (failure[0]) {
        fprintf(stderr, "clock_pair: %s\n", failure);
        return 1;
    }
    return 0;
}
