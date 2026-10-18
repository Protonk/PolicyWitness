/* Independent child receipt: observes the descriptors actually installed by spawn.
 * It neither applies a policy nor implements the worker/issuer protocol. */
#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>
#ifndef RECEIPT_PATH
#error RECEIPT_PATH must name the per-run child receipt
#endif
int main(int argc, char **argv) {
    struct stat states[4];
    const int fds[] = {0, 3, 4, 5};
    int results[4];
    for (int i = 0; i < 4; ++i) results[i] = fstat(fds[i], &states[i]);
    FILE *out = fopen(RECEIPT_PATH, "w");
    if (!out) return 91;
    fprintf(out, "{\"pid\":%d,\"argc\":%d,\"fds\":[", getpid(), argc);
    for (int i = 0; i < 4; ++i) {
        fprintf(out, "%s{\"fd\":%d,\"rc\":%d", i ? "," : "", fds[i], results[i]);
        if (!results[i]) fprintf(out, ",\"device\":%u,\"inode\":%llu,\"mode\":%u",
            (unsigned)states[i].st_dev, (unsigned long long)states[i].st_ino, (unsigned)states[i].st_mode);
        fprintf(out, "}");
    }
    fprintf(out, "]}\n");
    return fclose(out) == 0 ? 0 : 92;
}
