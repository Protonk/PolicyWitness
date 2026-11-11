/* Include the actual implementation to inspect its private production default.
 * No worker is launched and no policy is applied by this executable. */
// Renaming main removes its implicit return-zero rule; this entry is never called.
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wreturn-type"
#define main pw_worker_main
#include "../../../controller/tools/pw_probe_runner/pw_probe_runner.c"
#undef main
#pragma clang diagnostic pop

/* Call the actual argument parser without starting the worker. Expected
 * refusal diagnostics stay local to these constructed calls. */
static int fixture_delay_argument(const char *flag, long value, long *observed) {
    char number[32];
    snprintf(number, sizeof(number), "%ld", value);
    char *arguments[] = {"worker-limits", "--shm-fd", "0", "--ready-fd", "1",
                         (char *)flag, number};
    int saved_error = dup(STDERR_FILENO);
    int quiet = open("/dev/null", O_WRONLY);
    if (saved_error < 0 || quiet < 0) {
        if (saved_error >= 0) close(saved_error);
        if (quiet >= 0) close(quiet);
        return -2;
    }
    if (dup2(quiet, STDERR_FILENO) < 0) { close(quiet); close(saved_error); return -2; }
    close(quiet);
    pw_args_t parsed;
    int result = parse_args(7, arguments, &parsed);
    fflush(stderr);
    if (dup2(saved_error, STDERR_FILENO) < 0) { close(saved_error); return -2; }
    close(saved_error);
    if (result == 0) {
        *observed = strcmp(flag, "--pre-ready-hang-ms") == 0
            ? parsed.pre_ready_hang_ms : parsed.post_apply_hang_ms;
    }
    return result;
}

static long fixture_delay_capacity(const char *flag) {
    long observed = -1;
    /* Independent boundary oracle; a manifest edit cannot change these calls. */
    if (fixture_delay_argument(flag, -1, &observed) != -1
        || fixture_delay_argument(flag, 0, &observed) != 0 || observed != 0
        || fixture_delay_argument(flag, 60000, &observed) != 0 || observed != 60000
        || fixture_delay_argument(flag, 60001, &observed) != -1) return -1;
    long low = 0, high = 131072;
    if (fixture_delay_argument(flag, high, &observed) != -1) return -1;
    while (high - low > 1) {
        long middle = low + (high - low) / 2;
        int result = fixture_delay_argument(flag, middle, &observed);
        if (result == 0 && observed == middle) low = middle;
        else if (result == -1) high = middle;
        else return -1;
    }
    return low;
}

int main(void) {
    long pre_ready = fixture_delay_capacity("--pre-ready-hang-ms");
    long post_apply = fixture_delay_capacity("--post-apply-hang-ms");
    if (pre_ready < 0 || post_apply != pre_ready) {
        fprintf(stderr, "fixture delay parser boundary/calibration failed\n");
        return 1;
    }
    printf("exec_child_wait=%ld\n", PW_EXEC_CHILD_DEADLINE_MS_DEFAULT);
    printf("exec_reap_grace=%ld\n", PW_EXEC_REAP_GRACE_MS);
    printf("exec_attempt_budget=%ld\n", PW_EXEC_ATTEMPT_BUDGET_MS_DEFAULT);
    printf("worker_proceed_wait=%ld\n", PW_PROCEED_WAIT_MS_DEFAULT);
    printf("worker_fixture_delay=%ld\n", pre_ready);
    return 0;
}
