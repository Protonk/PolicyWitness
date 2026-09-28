/* Independent byte-stream producer for serialized reply-size controls.
 * argv: stdout byte count, stderr byte count, fill byte (0..255).
 * No PolicyWitness headers, sandbox calls or child processes. */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static long number(const char *text, long maximum) {
    char *end;
    errno = 0;
    long n = strtol(text, &end, 10);
    return errno || end == text || *end || n < 0 || n > maximum ? -1 : n;
}

static int emit(FILE *stream, long count, int byte) {
    unsigned char buffer[4096];
    memset(buffer, byte, sizeof(buffer));
    while (count > 0) {
        size_t n = count < (long)sizeof(buffer) ? (size_t)count : sizeof(buffer);
        if (fwrite(buffer, 1, n, stream) != n) return 2;
        count -= (long)n;
    }
    return fflush(stream) == 0 ? 0 : 2;
}

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    long out = number(argv[1], 1048576), err = number(argv[2], 1048576), byte = number(argv[3], 255);
    if (out < 0 || err < 0 || byte < 0) return 2;
    return emit(stdout, out, (int)byte) || emit(stderr, err, (int)byte) ? 2 : 0;
}
