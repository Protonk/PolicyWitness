/* Investigation-only observer. Snapshot all incoming descriptors before fopen;
 * never close or replace an incoming descriptor. The worker role then execs
 * the unmodified signed worker. The validator role does no sandbox query:
 * it challenges unused slot 255 and consumes input without emitting verdicts.
 * No request has any used slots. A host readback, not this observer's stat or
 * header match, decides shared-object identity. */
#include "pw_probe_runner_abi.h"
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#ifndef REAL_WORKER
#error REAL_WORKER required
#endif
#define LIMIT 256
#define CHALLENGE_OFFSET (PW_SHM_HEADER_BYTES + (PW_SHM_MAX_STEPS - 1) * PW_SHM_SLOT_BYTES)
_Static_assert(LIMIT * sizeof(uint32_t) <= PW_SHM_SLOT_BYTES, "challenge crosses unused slot");
_Static_assert(CHALLENGE_OFFSET + PW_SHM_SLOT_BYTES <= PW_SHM_HEADER_BYTES + PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES, "challenge leaves slots");
struct observation { int fd, flags, fdflags, mapped; struct stat st; uint32_t token; };
int main(int argc, char **argv) {
    alarm(10);
    int validator = argc > 1 && !strcmp(argv[1], "--batch");
    struct observation observations[LIMIT];
    int count = 0;
    for (int fd = 0; fd < LIMIT; fd++) {
        int flags = fcntl(fd, F_GETFL);
        if (flags < 0) { if (errno != EBADF) return 90; continue; }
        struct observation *o = &observations[count++];
        memset(o, 0, sizeof(*o)); o->fd = fd; o->flags = flags;
        o->fdflags = fcntl(fd, F_GETFD);
        if (fstat(fd, &o->st)) return 91;
    }
    for (int i = 0; i < count; i++) {
        struct observation *o = &observations[i];
        if (o->st.st_size < (off_t)PW_SHM_REGION_BYTES) continue;
        void *base = mmap(NULL, PW_SHM_REGION_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED, o->fd, 0);
        if (base == MAP_FAILED) continue;
        pw_shm_header_t *h = base;
        if (h->abi_magic == PW_SHM_ABI_MAGIC && h->step_count == 0 &&
            !memcmp(h->abi_identity, PW_WORKER_ABI_IDENTITY, PW_SHM_ABI_IDENTITY_BYTES)) {
            o->mapped = 1;
            if (validator) {
                o->token = arc4random_uniform(UINT32_MAX - 1) + 1;
                _Atomic uint32_t *cell = (void *)((char *)base + CHALLENGE_OFFSET + 4 * o->fd);
                atomic_store_explicit(cell, o->token, memory_order_release);
            }
        }
        if (munmap(base, PW_SHM_REGION_BYTES)) return 92;
    }
    FILE *f = fopen(validator ? "validator.json" : "worker.json", "w");
    if (!f) return 93;
    fprintf(f, "{\"pid\":%d,\"ppid\":%d,\"role\":\"%s\",\"fds\":[", getpid(), getppid(), validator ? "validator" : "worker");
    for (int i = 0; i < count; i++) {
        struct observation *o = &observations[i];
        fprintf(f, "%s{\"fd\":%d,\"access_mode\":%d,\"fd_flags\":%d,\"device\":%u,\"inode\":%llu,\"mode\":%u,\"size\":%lld,\"mapped\":%d,\"token\":%u}",
            i ? "," : "", o->fd, o->flags & O_ACCMODE, o->fdflags,
            (unsigned)o->st.st_dev, (unsigned long long)o->st.st_ino, (unsigned)o->st.st_mode,
            (long long)o->st.st_size, o->mapped, o->token);
    }
    fprintf(f, "]}\n");
    if (fclose(f)) return 94;
    if (validator) {
        char buf[4096]; ssize_t n;
        while ((n = read(0, buf, sizeof(buf))) != 0) if (n < 0 && errno != EINTR) return 95;
        return 0;
    }
    /* The independent fixture watchdog survives exec; no scenario needs more
     * than the five-second host sentinel plus cleanup. */
    alarm(15);
    execv(REAL_WORKER, argv);
    return 96;
}
