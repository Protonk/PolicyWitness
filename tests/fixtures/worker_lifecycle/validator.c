/* Validator lifecycle equipment: no sandbox calls, selected only by the query
 * operation in driver tests. Flush a valid record before exit/signal/cleanup.
 * The independent alarm bounds fixture lifetime even if host cleanup fails. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
int main(void) {
    alarm(10);
    char *line = NULL;
    size_t cap = 0;
    if (getline(&line, &cap, stdin) <= 0) return 90;
    int multibyte = strstr(line, "multibyte") != NULL;
    int io_hang = strstr(line, "io_hang") != NULL;
    int hang = strstr(line, "hang") != NULL;
    int nonzero = strstr(line, "nonzero") != NULL;
    int signaled = strstr(line, "signal") != NULL;
    int close_input = strstr(line, "close_input") != NULL;
    /* Echo the independently submitted query, then append native evidence. */
    char *end = strrchr(line, '}');
    if (!end) return 91;
    *end = '\0';
    char *query = strdup(line);
    free(line); line = NULL; cap = 0;
    if (!close_input) while (getline(&line, &cap, stdin) > 0) {}
    free(line);
    if (close_input) {
        /* Close input BEFORE producing more than one host read's worth of
         * output. The host must drain despite EPIPE; sleeps are unnecessary. */
        close(STDIN_FILENO);
        for (int i = 0; i < 32768; i++) putchar(' ');
    }
    printf("%s,\"kind\":\"sb_api_validator_verdict\",\"schema_version\":1,\"rc\":0,\"errno\":0,\"outcome\":\"allow\"}\n", query);
    free(query);
    if (multibyte) {
        fputs("{\"kind\":\"sb_api_validator_verdict\",\"schema_version\":1,\"step_id\":\"tail\",\"outcome\":\"future_937\",\"error\":\"", stdout);
        putchar(0xe2); fflush(stdout); usleep(30000);
        putchar(0x82); fflush(stdout); usleep(30000);
        putchar(0xac); fputs("\"}\n", stdout);
    }
    if (close_input) { putchar(0xff); putchar('\n'); }
    fflush(stdout);
    close(STDIN_FILENO);
    if (!io_hang) close(STDOUT_FILENO);
    if (hang) sleep(8);
    if (signaled) kill(getpid(), SIGTERM);
    return nonzero ? 23 : 0;
}
