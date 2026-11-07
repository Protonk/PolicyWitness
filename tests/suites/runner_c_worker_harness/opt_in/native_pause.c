/* First explicit pause after production timing setup and policy application.
 * Each invocation forks one fresh child; only the parent observes libproc or
 * writes descriptors after apply. No pause warm-up, helper thread or resource
 * preparation is added to the measured child. The handler is test equipment.
 * Loader/library internal calls before main are outside the first-use claim. */
#define main pw_worker_main
#include "pw_probe_runner.c"
#undef main
#include <libproc.h>
#include <sys/resource.h>

#define PAUSES 64
typedef struct { uint64_t begin, end; int rc, error; } pause_sample_t;
typedef struct {
    _Atomic unsigned ready, go, finished, leave, in_pause;
    int setup_rc, compile_ok, apply_rc, apply_errno, unapplied, handler_rc;
    int denial_rc, denial_errno, signals;
    uint32_t numer, denom;
    _Atomic unsigned count;
    pause_sample_t samples[PAUSES];
} report_t;
static volatile sig_atomic_t signal_count;
static void interrupted(int sig) { (void)sig; signal_count++; }
static const char *policy_source(const char *name) {
    if (!strcmp(name, "v2_original")) return "(version 2)(deny default)(allow file-read-data)";
    if (!strcmp(name, "deny_default")) return "(version 2)(deny default)";
    if (!strcmp(name, "allow_default")) return "(version 2)(allow default)";
    return NULL;
}
static void measured(report_t *r, void *region, const char *policy, const char *mode, const char *primitive) {
    pw_timing_t timing = {.proceed_ms = 60000, .budget_ms = PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT,
                          .child_ms = PW_EXEC_CHILD_DEADLINE_MS_DEFAULT};
    pw_clock_start(&timing.clock);
    r->setup_rc = pw_timing_setup(&timing, pw_evidence(region));
    r->numer = timing.clock.numer; r->denom = timing.clock.denom;
    if (r->setup_rc) _exit(67);
    struct sigaction action = {.sa_handler = interrupted};
    sigemptyset(&action.sa_mask);
    r->handler_rc = sigaction(SIGUSR1, &action, NULL);
    if (r->handler_rc) _exit(68);
    r->unapplied = !strcmp(policy, "unapplied");
    if (!r->unapplied) {
        char *error = NULL;
        void *profile = sandbox_compile_string(policy_source(policy), NULL, &error);
        r->compile_ok = profile != NULL;
        if (!profile) _exit(69);
        errno = 0;
        r->apply_rc = sandbox_apply(profile); r->apply_errno = errno;
        if (r->apply_rc) _exit(70);
    }
    atomic_store(&r->ready, 1);
    while (!atomic_load(&r->go)) cpu_relax();
    if (!strcmp(mode, "known_denial")) {
        errno = 0; r->denial_rc = open("/etc/hosts", O_RDONLY); r->denial_errno = errno;
        if (r->denial_rc >= 0) close(r->denial_rc);
    } else {
        for (unsigned i = 0; i < PAUSES; i++) {
            pause_sample_t *s = &r->samples[i];
            const struct timespec request = {.tv_sec = 0, .tv_nsec = 1000000};
            s->begin = mach_continuous_time();
            atomic_store(&r->in_pause, 1);
            errno = 0;
            if (!strcmp(primitive, "nanosleep")) {
                s->rc = nanosleep(&request, NULL); s->error = errno;
            } else {
                uint64_t ticks = 0, deadline = 0;
                if (pw_ticks_for_ms(&timing.clock, 1, &ticks) ||
                    pw_ticks_add(mach_absolute_time(), ticks, &deadline)) _exit(72);
                s->rc = mach_wait_until(deadline); s->error = 0;
            }
            atomic_store(&r->in_pause, 0);
            s->end = mach_continuous_time(); r->count++;
            if (s->rc && !(!strcmp(primitive, "nanosleep")
                          ? s->rc == -1 && s->error == EINTR : s->rc == KERN_ABORTED)) break;
        }
    }
    r->signals = signal_count;
    atomic_store(&r->finished, 1);
    while (!atomic_load(&r->leave)) cpu_relax();
    _exit(0);
}
typedef struct {
    struct proc_bsdinfo generation;
    struct rusage_info_v0 usage;
    int identity_rc, identity_errno, cpu_rc, cpu_errno;
    uint64_t begin, end;
} observation_t;
static observation_t observe(pid_t pid) {
    observation_t o = {0}; o.begin = mach_continuous_time(); errno = 0;
    o.identity_rc = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &o.generation, sizeof(o.generation));
    o.identity_errno = errno; errno = 0;
    o.cpu_rc = proc_pid_rusage(pid, RUSAGE_INFO_V0, (rusage_info_t *)&o.usage);
    o.cpu_errno = errno; o.end = mach_continuous_time(); return o;
}
static void print_observation(const observation_t *o) {
    printf("{\"begin_ticks\":%llu,\"end_ticks\":%llu,\"identity_rc\":%d,\"identity_size\":%zu,"
           "\"identity_errno\":%d,\"cpu_rc\":%d,\"cpu_errno\":%d,\"pid\":%u,\"ppid\":%u,"
           "\"start_sec\":%llu,\"start_usec\":%llu,\"user_ticks\":%llu,\"system_ticks\":%llu}",
           o->begin, o->end, o->identity_rc, sizeof(o->generation), o->identity_errno, o->cpu_rc,
           o->cpu_errno, o->generation.pbi_pid, o->generation.pbi_ppid,
           o->generation.pbi_start_tvsec, o->generation.pbi_start_tvusec,
           o->usage.ri_user_time, o->usage.ri_system_time);
}
int main(int argc, char **argv) {
    if (argc != 4 || (strcmp(argv[3], "nanosleep") && strcmp(argv[3], "mach_wait_until")) || (!policy_source(argv[1]) && strcmp(argv[1], "unapplied")) ||
        (strcmp(argv[2], "ordinary") && strcmp(argv[2], "interrupted") && strcmp(argv[2], "known_denial"))) return 64;
    report_t *r = mmap(NULL, sizeof(*r), PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    void *region = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    if (r == MAP_FAILED || region == MAP_FAILED) return 65;
    memset(r, 0, sizeof(*r)); memset(region, 0, PW_SHM_REGION_BYTES);
    pid_t pid = fork(); if (pid < 0) return 66;
    if (!pid) measured(r, region, argv[1], argv[2], argv[3]);
    mach_timebase_info_data_t tb; mach_timebase_info(&tb);
    uint64_t deadline = mach_continuous_time() + (uint64_t)10000000000ULL * tb.denom / tb.numer;
    int status = 0, reaped = 0, timed_out = 0, signal_calls = 0, signal_errors = 0;
    struct timespec observer_pause = {.tv_nsec = 100000};
    while (!atomic_load(&r->ready)) {
        reaped = waitpid(pid, &status, WNOHANG) == pid;
        if (reaped || mach_continuous_time() >= deadline) break;
        nanosleep(&observer_pause, NULL);
    }
    observation_t before = observe(pid);
    atomic_store(&r->go, 1);
    while (!reaped && !atomic_load(&r->finished) && mach_continuous_time() < deadline) {
        /* Leave first use alone, then interrupt the same 1 ms request. */
        if (!strcmp(argv[2], "interrupted") && r->count > 0 && atomic_load(&r->in_pause)) {
            signal_calls++; if (kill(pid, SIGUSR1)) signal_errors++;
        }
        reaped = waitpid(pid, &status, WNOHANG) == pid;
        nanosleep(&observer_pause, NULL);
    }
    observation_t after = observe(pid);
    if (!atomic_load(&r->finished) && !reaped) { timed_out = 1; kill(pid, SIGKILL); }
    atomic_store(&r->leave, 1);
    if (!reaped) reaped = waitpid(pid, &status, 0) == pid;
    printf("{\"version\":1,\"primitive\":\"%s\",\"requested_ns\":1000000,\"policy\":\"%s\",\"mode\":\"%s\","
           "\"pid\":%d,\"ready\":%u,\"finished\":%u,\"reaped\":%s,\"timed_out\":%d,\"exit_code\":%d,\"term_signal\":%d,"
           "\"setup_rc\":%d,\"compile_ok\":%d,\"apply_rc\":%d,\"apply_errno\":%d,\"unapplied\":%d,"
           "\"handler_rc\":%d,\"signal_calls\":%d,\"signal_errors\":%d,\"signals\":%d,"
           "\"denial_rc\":%d,\"denial_errno\":%d,\"numer\":%u,\"denom\":%u,\"before\":",
           argv[3], argv[1], argv[2], pid, atomic_load(&r->ready), atomic_load(&r->finished), reaped ? "true" : "false",
           timed_out, WIFEXITED(status) ? WEXITSTATUS(status) : -1, WIFSIGNALED(status) ? WTERMSIG(status) : 0,
           r->setup_rc, r->compile_ok, r->apply_rc, r->apply_errno, r->unapplied, r->handler_rc,
           signal_calls, signal_errors, r->signals, r->denial_rc, r->denial_errno, r->numer, r->denom);
    print_observation(&before); printf(",\"after\":"); print_observation(&after); printf(",\"samples\":[");
    for (unsigned i = 0; i < r->count; i++) {
        pause_sample_t *s = &r->samples[i];
        printf("%s{\"begin_ticks\":%llu,\"end_ticks\":%llu,\"rc\":%d,\"errno\":%d}",
               i ? "," : "", s->begin, s->end, s->rc, s->error);
    }
    printf("]}\n");
    return reaped ? 0 : 71;
}
