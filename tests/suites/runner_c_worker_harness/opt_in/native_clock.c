/* Native applicability of the worker's continuous clock: the production clock
 * helpers in a fresh process under a real applied profile. One invocation is
 * one configuration; the parent makes no clock read and forks the measured
 * child, which applies the profile and records into inherited shared memory
 * (post-apply writes to a descriptor may be denied). No permission is added
 * for the clock. First explicit use does not establish that the loader or
 * native libraries made no earlier internal call.
 *
 *   native-clock <policy> <variant> <samples>
 *   policy:  v2_original | deny_default | allow_default
 *   variant: production        origin before setup and application, as in main
 *            first_after_apply timebase before application, first raw read after
 *            old_clock         clock_gettime(CLOCK_MONOTONIC) after application
 */
#define main pw_worker_main
#include "pw_probe_runner.c"
#undef main

typedef struct {
    int compile_ok, apply_rc, apply_errno, setup_rc;
    uint32_t numer, denom, setup_code, setup_detail;
    int32_t setup_native;
    uint64_t valid, rejected, first_reason, elapsed_first, elapsed_last;
    uint64_t old_failures, old_first_index;
    int old_first_errno;
    _Atomic unsigned finished;
} native_report_t;

static const char *policy_source(const char *name) {
    if (!strcmp(name, "v2_original")) return "(version 2)(deny default)(allow file-read-data)";
    if (!strcmp(name, "deny_default")) return "(version 2)(deny default)";
    if (!strcmp(name, "allow_default")) return "(version 2)(allow default)";
    return NULL;
}

static void measured(native_report_t *r, const char *source, const char *variant, uint64_t count,
                     pw_shm_evidence_t *e) {
    pw_timing_t timing = {.proceed_ms = 60000, .budget_ms = PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT,
                          .child_ms = PW_EXEC_CHILD_DEADLINE_MS_DEFAULT};
    int production = !strcmp(variant, "production"), old = !strcmp(variant, "old_clock");
    if (production) pw_clock_start(&timing.clock);
    if (!old) {
        r->setup_rc = pw_timing_setup(&timing, e);
        r->numer = timing.clock.numer; r->denom = timing.clock.denom;
        if (r->setup_rc) {
            r->setup_code = e->code; r->setup_detail = e->detail; r->setup_native = e->native_result;
            _exit(69);
        }
    }
    char *error = NULL;
    void *profile = sandbox_compile_string(source, NULL, &error);
    r->compile_ok = profile != NULL;
    if (!profile) _exit(67);
    errno = 0;
    r->apply_rc = sandbox_apply(profile);
    r->apply_errno = errno;
    if (r->apply_rc) _exit(68);
    if (old) {
        for (uint64_t i = 0; i < count; i++) {
            struct timespec now;
            errno = 0;
            if (clock_gettime(CLOCK_MONOTONIC, &now) != 0 && r->old_failures++ == 0) {
                r->old_first_errno = errno; r->old_first_index = i;
            }
        }
    } else {
        if (!production) pw_clock_start(&timing.clock);
        for (uint64_t i = 0; i < count; i++) {
            uint64_t elapsed = 0;
            uint32_t reason = pw_clock_sample(&timing.clock, PW_CLOCK_PROCEED_OBSERVE, 0, PW_CLOCK_NO_SCOPE, &elapsed);
            if (reason) { if (r->rejected++ == 0) r->first_reason = reason; continue; }
            if (r->valid++ == 0) r->elapsed_first = elapsed;
            r->elapsed_last = elapsed;
        }
    }
    atomic_store(&r->finished, 1u);
    _exit(0);
}

int main(int argc, char **argv) {
    if (argc != 4) return 64;
    const char *source = policy_source(argv[1]);
    uint64_t count = strtoull(argv[3], NULL, 10);
    if (!source || !count || (strcmp(argv[2], "production") && strcmp(argv[2], "first_after_apply")
                              && strcmp(argv[2], "old_clock"))) return 64;
    native_report_t *r = mmap(NULL, sizeof(*r), PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    void *region = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    if (r == MAP_FAILED || region == MAP_FAILED) return 65;
    memset(r, 0, sizeof(*r));
    pid_t pid = fork();
    if (pid < 0) return 66;
    if (!pid) measured(r, source, argv[2], count, pw_evidence(region));
    int status = 0;
    pid_t reaped = waitpid(pid, &status, 0);
    printf("{\"policy\":\"%s\",\"variant\":\"%s\",\"samples\":%llu,\"pid\":%d,\"reaped\":%s,"
           "\"exit_code\":%d,\"term_signal\":%d,\"finished\":%u,\"compile_ok\":%d,\"apply_rc\":%d,"
           "\"apply_errno\":%d,\"setup_rc\":%d,\"setup_code\":%u,\"setup_detail\":%u,\"setup_native\":%d,"
           "\"numer\":%u,\"denom\":%u,\"valid\":%llu,\"rejected\":%llu,\"first_reason\":%llu,"
           "\"elapsed_first\":%llu,\"elapsed_last\":%llu,\"old_failures\":%llu,\"old_first_index\":%llu,"
           "\"old_first_errno\":%d}\n",
           argv[1], argv[2], (unsigned long long)count, pid, reaped == pid ? "true" : "false",
           WIFEXITED(status) ? WEXITSTATUS(status) : -1, WIFSIGNALED(status) ? WTERMSIG(status) : 0,
           atomic_load(&r->finished), r->compile_ok, r->apply_rc, r->apply_errno, r->setup_rc,
           r->setup_code, r->setup_detail, r->setup_native, r->numer, r->denom,
           (unsigned long long)r->valid, (unsigned long long)r->rejected, (unsigned long long)r->first_reason,
           (unsigned long long)r->elapsed_first, (unsigned long long)r->elapsed_last,
           (unsigned long long)r->old_failures, (unsigned long long)r->old_first_index, r->old_first_errno);
    return reaped == pid ? 0 : 70;
}
