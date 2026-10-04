/* Pins that every sandbox_check the production validator issues carries
 * SANDBOX_CHECK_NO_REPORT with the filter id intact. The production source is
 * compiled in with a recording sandbox_check: no kernel query, sandbox, child
 * or log is involved, so the check is deterministic. Without the flag a
 * denied prediction writes a kernel deny line against the worker PID, which
 * the deny-log channel cannot tell from the attempt's own line. */
#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

static int recorded_types[8];
static int recorded_count;
int recording_sandbox_check(pid_t pid, const char *operation, int type, ...) {
    (void)pid; (void)operation;
    assert(recorded_count < 8);
    recorded_types[recorded_count++] = type;
    return 0;
}
#define sandbox_check recording_sandbox_check
#define main validator_main
#include "sb_api_validator.c"
#undef main
#undef sandbox_check

/* Run one validator invocation with the given stdin text, discarding stdout. */
static void run(int argc, char **argv, const char *stdin_text) {
    int saved_in = dup(STDIN_FILENO), saved_out = dup(STDOUT_FILENO);
    int in[2];
    assert(saved_in >= 0 && saved_out >= 0 && pipe(in) == 0);
    if (stdin_text) {
        size_t n = strlen(stdin_text);
        assert(write(in[1], stdin_text, n) == (ssize_t)n);
    }
    close(in[1]);
    assert(dup2(in[0], STDIN_FILENO) == STDIN_FILENO);
    close(in[0]);
    int devnull = open("/dev/null", O_WRONLY);
    assert(devnull >= 0 && dup2(devnull, STDOUT_FILENO) == STDOUT_FILENO);
    close(devnull);
    clearerr(stdin);
    (void)validator_main(argc, argv);
    fflush(stdout);
    assert(dup2(saved_in, STDIN_FILENO) == STDIN_FILENO && dup2(saved_out, STDOUT_FILENO) == STDOUT_FILENO);
    close(saved_in); close(saved_out);
    clearerr(stdin);
}

int main(void) {
    char *batch[] = {"sb_api_validator", "--batch", "1", NULL};
    run(3, batch,
        "{\"step_id\":\"p\",\"operation\":\"file-read-data\",\"filter_type\":\"PATH\",\"filter_value\":\"/x\"}\n"
        "{\"step_id\":\"g\",\"operation\":\"mach-lookup\",\"filter_type\":\"GLOBAL_NAME\",\"filter_value\":\"a.b\"}\n"
        "{\"step_id\":\"n\",\"operation\":\"network-outbound\",\"filter_type\":\"NONE\"}\n");
    assert(recorded_count == 3);
    char *single_path[] = {"sb_api_validator", "--json", "1", "file-read-data", "PATH", "/x", NULL};
    run(6, single_path, NULL);
    char *single_none[] = {"sb_api_validator", "--json", "1", "network-outbound", "NONE", NULL};
    run(5, single_none, NULL);
    assert(recorded_count == 5);
    const int expected_ids[] = {SANDBOX_FILTER_PATH, SANDBOX_FILTER_GLOBAL_NAME, 0, SANDBOX_FILTER_PATH, 0};
    for (int i = 0; i < 5; i++) {
        if ((recorded_types[i] & SANDBOX_CHECK_NO_REPORT) != SANDBOX_CHECK_NO_REPORT) {
            printf("query %d issued without SANDBOX_CHECK_NO_REPORT: type=0x%x\n", i, recorded_types[i]);
            return 1;
        }
        if ((recorded_types[i] & ~SANDBOX_CHECK_NO_REPORT) != expected_ids[i]) {
            printf("query %d filter id changed by the flag: type=0x%x expected id %d\n", i, recorded_types[i], expected_ids[i]);
            return 1;
        }
    }
    puts("ok: 5 queries across batch and per-probe modes carry SANDBOX_CHECK_NO_REPORT with intact filter ids");
    return 0;
}
