// Emits one unified-log record per stdin line, verbatim and public, under its
// own subsystem so the archive fixture's corpus can be inspected apart from
// everything else the host logged. It reproduces the *text* of Sandbox deny
// messages only; it proves nothing about kernel emission or authenticity.
//
// Build (from a macOS host with Command Line Tools):
//   xcrun clang -Wall -Wextra -O2 -mmacosx-version-min=14.0 -o pwqp-emit pwqp_emit.c
#include <os/log.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(void) {
    os_log_t log = os_log_create("com.policywitness.fixture", "query_predicate");
    char line[4096];
    int emitted = 0;
    printf("emitting_pid=%d\n", (int)getpid());
    fflush(stdout);
    while (fgets(line, sizeof line, stdin)) {
        size_t len = strlen(line);
        if (len && line[len - 1] == '\n') line[--len] = '\0';
        if (!len) continue;
        os_log(log, "%{public}s", line);
        emitted++;
        usleep(20000);
    }
    printf("emitted=%d\n", emitted);
    fflush(stdout);
    sleep(2);
    return 0;
}
