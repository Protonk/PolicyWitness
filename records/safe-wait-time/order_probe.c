/* Deterministic observation of the current production wait, with only its
 * existing clock seam substituted. No sandbox or fake validator is involved.
 * Control stores occur inside the clock callback, before its return. */
#include <time.h>
#include <errno.h>
static int observed_clock(int phase, struct timespec *value);
#define PW_MONOTONIC_READ observed_clock
#define main unused_worker_main
#include "pw_probe_runner.c"
#undef main

static pw_shm_header_t *control;
static int mode, active_phase, observe_count;
static int observed_clock(int phase, struct timespec *value) {
    if (phase != PW_CLOCK_PROCEED_START && phase != PW_CLOCK_PROCEED_OBSERVE) {
        errno = EIO; return -1;
    }
    *value = (struct timespec){ .tv_sec = 10, .tv_nsec = 0 };
    if (phase == PW_CLOCK_PROCEED_START) {
        observe_count = 0;
        if (mode == 0) { errno = EIO; return -1; }
        return 0;
    }
    ++observe_count;
    pw_shm_slot_t *receipts = (void *)((char *)control + PW_SHM_HEADER_BYTES);
    receipts[active_phase].child_exit_code = observe_count;
    if (mode == 1) { errno = EIO; return -1; }
    /* An old release remains visible in the second phase for one observation. */
    if (mode == 8 && active_phase == 1 && observe_count == 1) return 0;
    if (mode == 9) { value->tv_sec = 9; return 0; }
    value->tv_nsec = mode == 2 || mode == 5 ? 1000000 : 999999;
    if (mode == 6) {
        /* Delayed after sampling, before the release acquire. No second clock
         * read occurs, so this exposes the limit of a sample-based deadline. */
        struct timespec delay = {.tv_nsec = 10000000};
        nanosleep(&delay, NULL);
    }
    if (mode == 4 || mode == 5 || mode == 7) atomic_store_explicit(&control->exit_requested, 1, memory_order_release);
    atomic_store_explicit(&control->proceed, mode == 7 ? 2 : (unsigned)active_phase + 1, memory_order_release);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 64;
    mode = atoi(argv[1]);
    if (mode < 0 || mode > 9) return 64;
    void *memory = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    if (memory == MAP_FAILED) return 65;
    memset(memory, 0, PW_SHM_REGION_BYTES);
    control = memory;
    pw_shm_evidence_t *e = pw_evidence(memory);
    control->phase_count = mode == 8 ? 2 : 1;
    for (unsigned i = 0; i < control->phase_count; ++i) {
        control->phases[i].first_slot = i; control->phases[i].end_slot = i + 1;
    }
    if (mode == 0 || mode == 1 || mode == 9) atomic_store(&control->proceed, 1);
    pw_shm_slot_t *slots = (void *)((char *)memory + PW_SHM_HEADER_BYTES);
    pid_t pid = fork();
    if (pid == -1) return 66;
    if (!pid) {
        for (active_phase = 0; active_phase < (int)control->phase_count; ++active_phase) {
            int64_t elapsed = wait_for_proceed(control, e, active_phase, 1);
            pw_progress(e, PW_OP_ATTEMPT, PW_PROGRESS_STARTED, active_phase);
            /* A real native open under ordinary authority independently
             * establishes that the return reached the action body. */
            int fd = open("/etc/hosts", O_RDONLY);
            slots[active_phase].rc = fd < 0 ? -1 : 0;
            slots[active_phase].errno_val = fd < 0 ? errno : 0;
            slots[active_phase].child_pid = (int32_t)elapsed; /* experiment-only receipt */
            if (fd >= 0) close(fd);
            atomic_store_explicit(&slots[active_phase].completed, 1, memory_order_release);
            atomic_store_explicit(&control->phases[active_phase].completed, 1, memory_order_release);
        }
        _exit(0);
    }
    int status = 0, killed = 0;
    pid_t reaped = 0;
    for (int i = 0; i < 2000; ++i) {
        reaped = waitpid(pid, &status, WNOHANG);
        if (reaped == pid || reaped == -1) break;
        if (atomic_load_explicit(&control->done, memory_order_acquire))
            atomic_store_explicit(&control->exit_requested, 1, memory_order_release);
        usleep(1000);
    }
    if (!reaped) { killed = kill(pid, SIGKILL) == 0; reaped = waitpid(pid, &status, 0); }
    printf("{\"mode\":%d,\"pid\":%d,\"reaped\":%s,\"status\":%d,\"killed\":%d,\"done\":%u,\"failure_published\":%u,\"operation\":%u,\"code\":%u,\"errno\":%d,\"detail\":%u,\"proceed\":%u,\"proceed_observed\":%u,\"phases\":[",
        mode,pid,reaped == pid ? "true" : "false",status,killed,atomic_load(&control->done),
        atomic_load(&e->failure_published),e->operation,e->code,e->errno_val,e->detail,
        atomic_load(&control->proceed),atomic_load(&control->proceed_observed));
    for (unsigned i = 0; i < control->phase_count; ++i)
        printf("%s{\"arrived\":%u,\"ack\":%u,\"phase_completed\":%u,\"action_completed\":%u,\"action_rc\":%d,\"elapsed_ns\":%d,\"observations\":%d}",i ? "," : "",
            atomic_load(&control->phases[i].arrived),atomic_load(&control->phases[i].acknowledged),
            atomic_load(&control->phases[i].completed),atomic_load(&slots[i].completed),slots[i].rc,slots[i].child_pid,slots[i].child_exit_code);
    puts("]}");
    return reaped == pid && status == 0 && !killed ? 0 : 67;
}
