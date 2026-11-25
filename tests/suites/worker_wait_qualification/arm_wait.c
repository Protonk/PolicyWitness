/* First explicit ARM wait after application. The supervisor owns the child,
 * observes its generation before/after a silent interval and reaps it. There
 * is no test handler or post-apply I/O in the measured child. This is an
 * applicability screen, not the production release/activation protocol. */
#define main pw_worker_main
#include "pw_probe_runner.c"
#undef main
#include <libproc.h>
#include <sys/resource.h>
#include <sys/sysctl.h>

#define TRACE_COUNT 64
#define CUTOFF_NS 500000000ULL
#define LOCAL_TIMEOUT_NS 100000ULL
typedef struct { uint64_t begin, end, counter, deadline; } arm_sample_t;
typedef struct {
    _Atomic unsigned ready, go, entered, first_returned, finished, leave;
    int setup_rc, compiled, apply_rc, apply_errno, unapplied;
    uint32_t numer, denom;
    uint64_t frequency, start, end, cutoff, passes, max_span;
    unsigned stored;
    arm_sample_t samples[TRACE_COUNT];
} arm_report_t;
static volatile sig_atomic_t stopping;
static void stop_supervisor(int signal) { (void)signal; stopping = 1; }
static uint64_t continuous_ns(void) {
    mach_timebase_info_data_t tb;
    if (mach_timebase_info(&tb) || !tb.denom) _exit(80);
    return (uint64_t)((__uint128_t)mach_continuous_time() * tb.numer / tb.denom);
}
static uint64_t counter(void) {
    uint64_t value;
    __asm__ volatile("isb\n\tmrs %0, cntvct_el0" : "=r"(value) :: "memory");
    return value;
}
__attribute__((noinline)) static void arm_wfe(void) {
    __asm__ volatile("wfe" ::: "memory");
}
__attribute__((noinline)) static void arm_wfet(uint64_t deadline) {
    /* WFET X17: LLVM's armv8.7a-wfxt.s independently fixes d5031011.
     * Apple's assembler rejects .arch_extension wfxt; keep the rest of the
     * executable at the baseline ISA and inspect these actual output bytes. */
    register uint64_t until __asm__("x17") = deadline;
    __asm__ volatile(".inst 0xd5031011" :: "r"(until) : "memory");
}
static const char *profile(const char *name) {
    if (!strcmp(name, "allow_default")) return "(version 2)(allow default)";
    if (!strcmp(name, "deny_default")) return "(version 2)(deny default)";
    if (!strcmp(name, "file_read")) return "(version 2)(deny default)(allow file-read-data)";
    return NULL;
}
static void child(arm_report_t *r, void *region, const char *policy, int timed) {
    signal(SIGTERM, SIG_DFL); signal(SIGINT, SIG_DFL);
    pw_timing_t timing = {.proceed_ms=60000, .budget_ms=PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT,
                          .child_ms=PW_EXEC_CHILD_DEADLINE_MS_DEFAULT};
    pw_clock_start(&timing.clock);
    r->setup_rc = pw_timing_setup(&timing, pw_evidence(region));
    r->numer = timing.clock.numer; r->denom = timing.clock.denom;
    if (r->setup_rc) _exit(67);
    /* Reading configuration is not a wait warm-up. Record the frequency even
     * for WFE, but only read/use the virtual count for the timed candidate. */
    __asm__ volatile("mrs %0, cntfrq_el0" : "=r"(r->frequency));
    if (!r->frequency) _exit(68);
    r->unapplied = !strcmp(policy, "unapplied");
    if (!r->unapplied) {
        char *error = NULL;
        void *compiled = sandbox_compile_string(profile(policy), NULL, &error);
        r->compiled = compiled != NULL;
        if (!compiled) _exit(69);
        errno = 0; r->apply_rc = sandbox_apply(compiled); r->apply_errno = errno;
        if (r->apply_rc) _exit(70);
    }
    atomic_store_explicit(&r->ready, 1, memory_order_release);
    while (!atomic_load_explicit(&r->go, memory_order_acquire)) cpu_relax();
    uint64_t start = mach_continuous_time(), span = 0, cutoff = 0;
    if (pw_ticks_for_ms(&timing.clock, 500, &span) || pw_ticks_add(start, span, &cutoff)) _exit(71);
    r->start = start; r->cutoff = cutoff;
    uint64_t passes = 0, maximum = 0;
    for (;;) {
        uint64_t begin = mach_continuous_time();
        if (begin < start) _exit(72);
        if (begin >= cutoff) { r->end = begin; break; }
        uint64_t now = 0, deadline = 0;
        if (timed) {
            now = counter();
            __uint128_t ticks = ((__uint128_t)r->frequency * LOCAL_TIMEOUT_NS + 999999999) / 1000000000;
            if (ticks > UINT64_MAX || pw_ticks_add(now, (uint64_t)ticks, &deadline)) _exit(73);
        }
        if (!passes) atomic_store_explicit(&r->entered, 1, memory_order_release);
        if (timed) arm_wfet(deadline); else arm_wfe();
        uint64_t end = mach_continuous_time();
        if (end < begin) _exit(74);
        if (!passes) atomic_store_explicit(&r->first_returned, 1, memory_order_release);
        if (end - begin > maximum) maximum = end - begin;
        if (passes < TRACE_COUNT) {
            r->samples[passes] = (arm_sample_t){begin, end, now, deadline};
            r->stored++;
        }
        passes++;
    }
    r->passes = passes; r->max_span = maximum;
    atomic_store_explicit(&r->finished, 1, memory_order_release);
    while (!atomic_load_explicit(&r->leave, memory_order_acquire)) cpu_relax();
    _exit(0);
}
typedef struct {
    struct proc_bsdinfo generation;
    struct rusage_info_v0 usage;
    uint64_t begin, end;
    int identity_rc, identity_errno, cpu_rc, cpu_errno;
} arm_observation_t;
static arm_observation_t observe(pid_t pid) {
    arm_observation_t o = {0}; o.begin = mach_continuous_time(); errno = 0;
    o.identity_rc = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &o.generation, sizeof(o.generation));
    o.identity_errno = errno; errno = 0;
    o.cpu_rc = proc_pid_rusage(pid, RUSAGE_INFO_V0, (rusage_info_t *)&o.usage);
    o.cpu_errno = errno; o.end = mach_continuous_time(); return o;
}
static void print_observation(arm_observation_t *o) {
    printf("{\"begin\":%llu,\"end\":%llu,\"identity_rc\":%d,\"identity_size\":%zu,\"identity_errno\":%d,"
           "\"cpu_rc\":%d,\"cpu_errno\":%d,\"pid\":%u,\"ppid\":%u,\"start_sec\":%llu,\"start_usec\":%llu,"
           "\"user_ticks\":%llu,\"system_ticks\":%llu}",
           o->begin,o->end,o->identity_rc,sizeof(o->generation),o->identity_errno,o->cpu_rc,o->cpu_errno,
           o->generation.pbi_pid,o->generation.pbi_ppid,o->generation.pbi_start_tvsec,
           o->generation.pbi_start_tvusec,o->usage.ri_user_time,o->usage.ri_system_time);
}
static void pause_until(uint64_t until) {
    while (!stopping) {
        uint64_t now = continuous_ns(); if (now >= until) break;
        uint64_t delta = until - now;
        struct timespec ts = {.tv_sec=(time_t)(delta/1000000000), .tv_nsec=(long)(delta%1000000000)};
        if (nanosleep(&ts, NULL) && errno != EINTR) break;
    }
}
int main(int argc, char **argv) {
    if (argc != 3 || (strcmp(argv[1],"wfe") && strcmp(argv[1],"wfet")) ||
        (!profile(argv[2]) && strcmp(argv[2],"unapplied"))) return 64;
    int timed = !strcmp(argv[1],"wfet"), feature = 0; size_t size = sizeof(feature);
    errno = 0; int feature_rc = sysctlbyname("hw.optional.arm.FEAT_WFxT", &feature, &size, NULL, 0);
    int feature_errno = errno;
    if (timed && (feature_rc || size != sizeof(feature) || feature != 1)) return 65;
    arm_report_t *r = mmap(NULL,sizeof(*r),PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANON,-1,0);
    void *region = mmap(NULL,PW_SHM_REGION_BYTES,PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANON,-1,0);
    if (r == MAP_FAILED || region == MAP_FAILED) return 66;
    memset(r,0,sizeof(*r)); memset(region,0,PW_SHM_REGION_BYTES);
    signal(SIGTERM,stop_supervisor); signal(SIGINT,stop_supervisor);
    pid_t pid = fork(); if (pid < 0) return 66;
    if (!pid) child(r,region,argv[2],timed);
    uint64_t deadline = continuous_ns()+5000000000ULL;
    int status = 0, reaped = 0, rescued = 0;
    while (!stopping && !atomic_load_explicit(&r->ready,memory_order_acquire) && continuous_ns()<deadline) {
        if (waitpid(pid,&status,WNOHANG)==pid) { reaped=1; break; }
        pause_until(continuous_ns()+1000000);
    }
    arm_observation_t before = observe(pid);
    uint64_t silent_begin = mach_continuous_time();
    atomic_store_explicit(&r->go,1,memory_order_release);
    /* No inspection, waitpid, explicit signal or publication during silence. */
    pause_until(continuous_ns()+150000000ULL);
    uint64_t silent_end = mach_continuous_time();
    arm_observation_t after = observe(pid);
    unsigned finished_at_after = atomic_load_explicit(&r->finished,memory_order_acquire);
    pause_until(continuous_ns()+400000000ULL);
    if (!reaped) reaped = waitpid(pid,&status,WNOHANG)==pid;
    unsigned finished = atomic_load_explicit(&r->finished,memory_order_acquire);
    if (!reaped && (!finished || stopping)) { rescued=1; kill(pid,SIGKILL); }
    atomic_store_explicit(&r->leave,1,memory_order_release);
    if (!reaped) {
        uint64_t end = continuous_ns()+1000000000ULL;
        while (continuous_ns()<end) {
            if (waitpid(pid,&status,WNOHANG)==pid) { reaped=1; break; }
            pause_until(continuous_ns()+1000000);
        }
        if (!reaped) {
            rescued=1; kill(pid,SIGKILL);
            pid_t got; do { got=waitpid(pid,&status,0); } while (got<0 && errno==EINTR);
            reaped=got==pid;
        }
    }
    printf("{\"version\":1,\"primitive\":\"%s\",\"policy\":\"%s\",\"pid\":%d,\"supervisor_pid\":%d,"
           "\"feature\":%d,\"feature_rc\":%d,\"feature_errno\":%d,\"feature_size\":%zu,"
           "\"ready\":%u,\"entered\":%u,\"first_returned\":%u,\"finished\":%u,\"finished_at_after\":%u,"
           "\"rescued\":%d,\"reaped\":%d,\"exit_code\":%d,\"term_signal\":%d,\"supervisor_interrupted\":%d,"
           "\"setup_rc\":%d,\"compiled\":%d,\"apply_rc\":%d,\"apply_errno\":%d,\"unapplied\":%d,"
           "\"numer\":%u,\"denom\":%u,\"frequency\":%llu,\"start\":%llu,\"end\":%llu,\"cutoff\":%llu,"
           "\"passes\":%llu,\"max_span\":%llu,\"silent_begin\":%llu,\"silent_end\":%llu,"
           "\"local_timeout_ns\":%llu,\"before\":",
           argv[1],argv[2],pid,getpid(),feature,feature_rc,feature_errno,size,
           r->ready,r->entered,r->first_returned,finished,finished_at_after,rescued,reaped,
           WIFEXITED(status)?WEXITSTATUS(status):-1,WIFSIGNALED(status)?WTERMSIG(status):0,stopping,
           r->setup_rc,r->compiled,r->apply_rc,r->apply_errno,r->unapplied,r->numer,r->denom,
           r->frequency,r->start,r->end,r->cutoff,r->passes,r->max_span,silent_begin,silent_end,LOCAL_TIMEOUT_NS);
    print_observation(&before); printf(",\"after\":"); print_observation(&after); printf(",\"samples\":[");
    for (unsigned i=0;i<r->stored && i<TRACE_COUNT;i++) {
        arm_sample_t *s=&r->samples[i];
        printf("%s{\"begin\":%llu,\"end\":%llu,\"counter\":%llu,\"deadline\":%llu}",i?",":"",s->begin,s->end,s->counter,s->deadline);
    }
    printf("]}\n");
    return reaped ? 0 : 75;
}
