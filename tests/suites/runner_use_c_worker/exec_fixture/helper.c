/*
 * exec_fixture/helper.c — minimal libSystem-dynamic helper used by
 * the exec-attempt e2e tests.
 *
 * Built on demand by the suite driver via `xcrun clang` into
 * tests/out/<run>/exec_fixture/helper. Not signed, not notarized,
 * not in the app bundle — purely a test fixture.
 *
 * Default behavior: print a fixed marker line to stdout and exit 0.
 * Optional flags exercise the failure shapes the worker has to
 * surface:
 *   --exit N      exit with code N (cap at 255 for portability).
 *   --stdout-bytes N
 *                 write N bytes (deterministic 'A' fill) to stdout
 *                 before exiting. Used to exercise the worker's
 *                 truncation marker when N exceeds the slot budget.
 *   --stderr S    write S verbatim to stderr.
 *
 * Dynamic linkage against libSystem is intentional: it exercises
 * dyld + shared-cache resolution at exec time, which is what
 * `exec_baseline` has to allow. A statically-linked helper would
 * skip that surface entirely and produce a misleadingly small
 * baseline.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static void write_stdout_fill(long count) {
    /* Stream in chunks so a million-byte request doesn't allocate a
     * million-byte buffer. */
    char chunk[4096];
    memset(chunk, 'A', sizeof(chunk));
    while (count > 0) {
        size_t n = (count > (long)sizeof(chunk)) ? sizeof(chunk) : (size_t)count;
        if (fwrite(chunk, 1, n, stdout) != n) break;
        count -= (long)n;
    }
    fflush(stdout);
}

int main(int argc, char **argv) {
    int    exit_code      = 0;
    long   stdout_bytes   = -1;          /* -1 → emit the default marker */
    const char *stderr_msg = NULL;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--exit") == 0 && i + 1 < argc) {
            exit_code = atoi(argv[++i]) & 0xff;
        } else if (strcmp(argv[i], "--stdout-bytes") == 0 && i + 1 < argc) {
            stdout_bytes = strtol(argv[++i], NULL, 10);
        } else if (strcmp(argv[i], "--stderr") == 0 && i + 1 < argc) {
            stderr_msg = argv[++i];
        } else {
            fprintf(stderr, "exec_fixture: unknown arg %s\n", argv[i]);
            return 2;
        }
    }

    if (stdout_bytes >= 0) {
        write_stdout_fill(stdout_bytes);
    } else {
        fputs("exec_fixture: hello from helper\n", stdout);
        fflush(stdout);
    }
    if (stderr_msg) {
        fputs(stderr_msg, stderr);
        fputc('\n', stderr);
        fflush(stderr);
    }
    return exit_code;
}
