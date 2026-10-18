/* Controlled native entrypoints in the production issuer/worker. The observer
 * is test-owned POSIX shared memory, never a file containing token bytes.
 * Production binaries compile none of this instrumentation. */
#include <dlfcn.h>
#include <crt_externs.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>
#include "pw_extension_channel.h"

#ifndef PW_CONTROL_MODE
#error PW_CONTROL_MODE is required
#endif
#ifndef PW_CONTROL_CHANNEL
#error PW_CONTROL_CHANNEL is required
#endif

#define OBSERVER_BYTES 32768
typedef struct {
    uint32_t magic;
    uint32_t issuer_pid, worker_pid;
    uint32_t stage, operation, actual_returned;
    int64_t actual_result;
    uint32_t issuer_core_disabled, worker_core_disabled;
    uint32_t issuer_channel_closed, worker_channel_closed;
    _Atomic uint32_t token_length;
    uint32_t issuer_argv_clean, issuer_env_clean, worker_argv_env_clean;
    uint32_t worker_token_erased, issuer_token_erased;
    uint32_t reserved[14];
    char token[PW_EXTENSION_TOKEN_BYTES];
} observer_t;
_Static_assert(offsetof(observer_t, token) == 128, "test observer token offset");
static observer_t *observer;
static pw_extension_channel_t *worker_channel_observation;
static void *native_lookup(void *library, const char *name) { return dlsym(library, name); }
static int native_unmap(void *p, size_t n) { return munmap(p, n); }

static void observe_setup(void) {
    if (observer) return;
    int fd = shm_open(PW_CONTROL_CHANNEL, O_RDWR, 0600);
    if (fd < 0) _exit(100 + errno);
    void *p = mmap(NULL, OBSERVER_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (p == MAP_FAILED) _exit(81);
    observer = p;
    if (observer->magic != 0x43545845) _exit(82);
}

static void interrupted(unsigned stage, unsigned release, int64_t result) {
    observe_setup();
    observer->worker_pid = (uint32_t)getpid();
    observer->operation = release ? 2 : 1;
    observer->stage = stage;
    observer->actual_returned = stage == 2;
    observer->actual_result = result;
    struct rlimit limit;
    observer->worker_core_disabled = getrlimit(RLIMIT_CORE, &limit) == 0 && limit.rlim_cur == 0;
    errno = 0;
    observer->worker_channel_closed = fcntl(5, F_GETFD) == -1 && errno == EBADF;
    unsigned expected = (release ? 200 : 100) + stage;
    /* Mode 102/202 is inside the substituted operation, before its return.
     * Mode 103/203 is after the real native call returned. */
    if (PW_CONTROL_MODE == (int)(stage == 2 ? expected + 1 : stage == 3 ? expected - 1 : expected)) {
        kill(getpid(), SIGKILL);
        _exit(83);
    }
}

static char *controlled_issue(const char *, const char *, uint32_t);
static int64_t controlled_consume(const char *);
static int controlled_release(int64_t);
static void *controlled_lookup(void *, const char *);
static int controlled_unmap(void *, size_t);
static void controlled_erase(void *, size_t);
static void *controlled_memchr(const void *, int, size_t);
static int controlled_setrlimit(int, const struct rlimit *);
static int controlled_fstat(int, struct stat *);
static void *controlled_mmap(size_t, int);
static int controlled_close(int);

#define pw_extension_erase controlled_erase

#if defined(PW_CONTROL_ISSUER)
#define dlsym controlled_lookup
#define munmap controlled_unmap
#include "pw_extension_issuer.c"
#undef dlsym
#undef munmap
#else
#define dlsym controlled_lookup
#define memchr controlled_memchr
#define PW_EXTENSION_OBSERVE(stage, release, result) interrupted((stage), (release), (result))
/* Local preparation failures and channel rejections: exactly one native call
 * of prepare_extension is substituted per mode; every other call is real, so
 * the production path decides the published status, stage and native result. */
#define PW_EXTENSION_SETRLIMIT(resource, limit) controlled_setrlimit((resource), (limit))
#define PW_EXTENSION_FSTAT(fd, metadata) controlled_fstat((fd), (metadata))
#define PW_EXTENSION_MMAP(length, fd) controlled_mmap((length), (fd))
#define PW_EXTENSION_CLOSE(fd) controlled_close(fd)
#include "pw_probe_runner.c"
#undef dlsym
#undef memchr
#endif
#undef pw_extension_erase

static char *(*native_issue)(const char *, const char *, uint32_t);
static int64_t (*native_consume)(const char *);
static int (*native_release)(int64_t);

static int vector_excludes(char **values, const char *token) {
    if (!token || !*token) return 0;
    for (char **p = values; p && *p; ++p) if (strstr(*p, token)) return 0;
    return 1;
}

static void controlled_erase(void *bytes, size_t length) {
    pw_extension_erase(bytes, length);
    int clear = 1;
#if defined(PW_CONTROL_ISSUER)
    /* Issuer strings are separate allocations; length is their known bound. */
    for (size_t i = 0; i < length; ++i) if (((unsigned char *)bytes)[i]) clear = 0;
    observer->issuer_token_erased = clear;
#else
    /* Independently held mapped channel: neither the erase argument, the
     * token's reported length nor its first NUL defines this scan's bound. */
    if (!worker_channel_observation || bytes != worker_channel_observation->token) _exit(85);
    for (size_t i = 0; i < sizeof(worker_channel_observation->token); ++i)
        if ((unsigned char)worker_channel_observation->token[i]) clear = 0;
    if (!clear) observer->reserved[4]++;
    observer->worker_token_erased = clear && !observer->reserved[4];
#endif
}

static void *controlled_lookup(void *library, const char *name) {
    observe_setup();
    void *symbol = native_lookup(library, name);
    if (strcmp(name, "sandbox_extension_issue_file") == 0) {
        if (PW_CONTROL_MODE == 6) return NULL;
        native_issue = (char *(*)(const char *, const char *, uint32_t))symbol;
        return symbol ? (void *)controlled_issue : NULL;
    }
    if (strcmp(name, "sandbox_extension_consume") == 0) {
        if (PW_CONTROL_MODE == 105 || PW_CONTROL_MODE == 118) return NULL;
        native_consume = (int64_t (*)(const char *))symbol;
        return symbol ? (void *)controlled_consume : NULL;
    }
    if (strcmp(name, "sandbox_extension_release") == 0) {
        native_release = (int (*)(int64_t))symbol;
        return symbol ? (void *)controlled_release : NULL;
    }
    return symbol;
}

static char *controlled_issue(const char *kind, const char *path, uint32_t flags) {
    observer->issuer_pid = (uint32_t)getpid();
    struct rlimit limit;
    observer->issuer_core_disabled = getrlimit(RLIMIT_CORE, &limit) == 0 && limit.rlim_cur == 0;
    errno = 0;
    observer->issuer_channel_closed = fcntl(3, F_GETFD) == -1 && errno == EBADF;
    if (PW_CONTROL_MODE == 1) { errno = EACCES; return NULL; }
    if (PW_CONTROL_MODE == 2) {
        char *value = malloc(PW_EXTENSION_TOKEN_BYTES + 1);
        if (!value) _exit(84);
        memset(value, 'x', PW_EXTENSION_TOKEN_BYTES); value[PW_EXTENSION_TOKEN_BYTES] = 0;
        errno = 0; return value;
    }
    if (PW_CONTROL_MODE == 3) { errno = 0; return calloc(1, 1); }
    if (PW_CONTROL_MODE == 16) {
        char *value = malloc(PW_EXTENSION_TOKEN_BYTES);
        if (!value) _exit(84);
        memset(value, 'x', PW_EXTENSION_TOKEN_BYTES - 1);
        value[PW_EXTENSION_TOKEN_BYTES - 1] = 0;
        errno = 0; return value;
    }
    if (PW_CONTROL_MODE == 4) _exit(87);
    if (PW_CONTROL_MODE == 5) { sleep(30); _exit(88); }
    errno = 0;
    char *value = native_issue(kind, path, flags);
    int saved = errno;
    if (value) {
        observer->issuer_argv_clean = vector_excludes(*_NSGetArgv(), value);
        observer->issuer_env_clean = vector_excludes(*_NSGetEnviron(), value);
        size_t n = strnlen(value, PW_EXTENSION_TOKEN_BYTES);
        if (n < PW_EXTENSION_TOKEN_BYTES) {
            memcpy(observer->token, value, n);
            atomic_store_explicit(&observer->token_length, (uint32_t)n, memory_order_release);
        }
    }
    errno = saved;
    return value;
}

static int controlled_unmap(void *p, size_t n) {
    pw_extension_channel_t *channel = p;
    if (n == PW_EXTENSION_CHANNEL_BYTES) {
        /* Deliberately violate the immutable publication protocol. Host reaping
         * precedes delivery, so it must inspect the final malformed transport. */
        switch (PW_CONTROL_MODE) {
        case 7: channel->token_length = PW_EXTENSION_TOKEN_BYTES; break;
        case 8: if (channel->token_length) channel->token[channel->token_length - 1] = 0; break;
        case 9: channel->token[channel->token_length] = 'x'; break;
        case 10:
            pw_extension_erase(channel->token, sizeof(channel->token));
            strcpy(channel->token, "controlled-invalid-token");
            channel->token_length = (uint32_t)strlen(channel->token);
            break;
        case 11: channel->magic ^= 1; break;
        case 12: channel->pid += 1; break;
        case 13: atomic_store_explicit(&channel->completed, 0, memory_order_release); break;
        case 14: channel->status = 99; break;
        case 15: atomic_store_explicit(&channel->call_boundary, 0, memory_order_release); break;
        case 17:
            observer->reserved[0] = atomic_load_explicit(&channel->completed, memory_order_acquire);
            _exit(87);
        default: break;
        }
    }
    return native_unmap(p, n);
}

static void *controlled_memchr(const void *bytes, int value, size_t length) {
#if !defined(PW_CONTROL_ISSUER)
    if (PW_CONTROL_MODE == 106 && extension_channel && bytes == extension_channel->token) {
        /* Delivery is a mapped channel, not a stream copy. Stop halfway through
         * framing validation, after mapping/FD close and before publication. */
        size_t prefix = length / 2;
        observer->reserved[0] = (uint32_t)prefix;
        observer->reserved[1] = memchr(bytes, value, prefix) == NULL;
        interrupted(4, 0, 0);
        kill(getpid(), SIGKILL);
        _exit(83);
    }
#endif
    return memchr(bytes, value, length);
}

static int controlled_setrlimit(int resource, const struct rlimit *limit) {
    int rc = setrlimit(resource, limit);  /* the real limit still applies */
    if (PW_CONTROL_MODE == 107) { errno = EPERM; return -1; }
    return rc;
}

static int controlled_fstat(int fd, struct stat *metadata) {
    int rc = fstat(fd, metadata);
    if (PW_CONTROL_MODE == 108 || PW_CONTROL_MODE == 111) { errno = EIO; return -1; }
    if (PW_CONTROL_MODE == 112 && rc == 0) metadata->st_size = 0;  /* inspected, undersized */
    return rc;
}

static void *controlled_mmap(size_t length, int fd) {
    if (PW_CONTROL_MODE == 109) { errno = ENODEV; return MAP_FAILED; }  /* nothing mapped */
    void *p = mmap(NULL, length, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (p == MAP_FAILED || length != PW_EXTENSION_CHANNEL_BYTES) return p;
    /* The host already validated and passed this channel; the worker's own
     * inspection must reject the mutated view it maps. */
    pw_extension_channel_t *channel = p;
    worker_channel_observation = channel;
    if (channel->token_length < sizeof(channel->token) - 1 && channel->token[channel->token_length] == 0) {
        memset(channel->token + channel->token_length + 1, 0xa5,
               sizeof(channel->token) - channel->token_length - 1);
        observer->reserved[2] = channel->token[sizeof(channel->token) - 1] != 0;
        observer->reserved[3] = sizeof(channel->token);
    }
    switch (PW_CONTROL_MODE) {
    case 113: channel->magic ^= 1; break;
    case 114: atomic_store_explicit(&channel->completed, 0, memory_order_release); break;
    case 115: channel->status = 99; break;
    case 116: channel->token_length = 0; break;
    case 117: channel->token_length = PW_EXTENSION_TOKEN_BYTES; break;
    default: break;
    }
    return p;
}

static int controlled_close(int fd) {
    int rc = close(fd);  /* the descriptor really closes; only the reported result is controlled */
    if (PW_CONTROL_MODE == 110) { errno = EIO; return -1; }    /* the inspected close after mapping */
    if (PW_CONTROL_MODE == 111 || PW_CONTROL_MODE == 118) { errno = EBADF; return -1; }  /* cleanup after fstat/API lookup */
    return rc;
}

static int64_t controlled_consume(const char *token) {
    observer->worker_argv_env_clean = vector_excludes(*_NSGetArgv(), token) && vector_excludes(*_NSGetEnviron(), token);
    if (PW_CONTROL_MODE == 102) interrupted(3, 0, 0);
    if (PW_CONTROL_MODE == 104) { errno = EACCES; return -1; }
    return native_consume(token);
}
static int controlled_release(int64_t handle) {
    if (PW_CONTROL_MODE == 202) interrupted(3, 1, 0);
    if (PW_CONTROL_MODE == 204) { errno = EIO; return -1; }
    return native_release(handle);
}
