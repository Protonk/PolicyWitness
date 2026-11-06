/* Controlled native entrypoints in the production actor workers. The observer
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
#include "pw_authority_region.h"

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
static pw_authority_slot_t *worker_slot_observation;
static char *issuer_allocation;
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
static void controlled_erase(void *, size_t);
static int controlled_setrlimit(int, const struct rlimit *);
static int controlled_fstat(int, struct stat *);
static void *controlled_mmap(size_t, int);
static int controlled_close(int);
static void controlled_publish(pw_authority_slot_t *);
static void controlled_inbound(pw_authority_slot_t *);
static void controlled_published(void *);
static _Noreturn void controlled_exit(int);

#define _exit controlled_exit
#define pw_extension_erase controlled_erase
#define dlsym controlled_lookup
#define PW_EXTENSION_OBSERVE(stage, release, result) interrupted((stage), (release), (result))
#define PW_EXTENSION_SETRLIMIT(resource, limit) controlled_setrlimit((resource), (limit))
#define PW_EXTENSION_FSTAT(fd, metadata) controlled_fstat((fd), (metadata))
#define PW_EXTENSION_MMAP(length, fd) controlled_mmap((length), (fd))
#define PW_EXTENSION_CLOSE(fd) controlled_close(fd)
#define PW_AUTHORITY_PUBLISH_OBSERVE(slot) controlled_publish(slot)
#define PW_INBOUND_OBSERVE(slot) controlled_inbound(slot)
#define PW_ATTEMPT_PUBLISHED(slot) controlled_published(slot)
#include "pw_probe_runner.c"
#undef dlsym
#undef pw_extension_erase
#undef _exit

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
    observe_setup();
    int clear = 1;
    if (bytes == issuer_allocation) {
        for (size_t i=0;i<length;i++) if (((unsigned char *)bytes)[i]) clear=0;
        observer->issuer_token_erased=clear;
    }
    if (worker_slot_observation && bytes==worker_slot_observation->token) {
        for (size_t i=0;i<PW_EXTENSION_TOKEN_BYTES;i++) if (worker_slot_observation->token[i]) clear=0;
        if (!clear) observer->reserved[4]++;
        observer->worker_token_erased=clear && !observer->reserved[4];
    }
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
        if (PW_CONTROL_MODE == 205) return NULL;
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
    observer->issuer_channel_closed = fcntl(5, F_GETFD) == -1 && errno == EBADF;
    if (PW_CONTROL_MODE == 1) { errno = EACCES; return NULL; }
    if (PW_CONTROL_MODE == 2) {
        char *value = malloc(PW_EXTENSION_TOKEN_BYTES + 1);
        if (!value) _exit(84);
        memset(value, 'x', PW_EXTENSION_TOKEN_BYTES); value[PW_EXTENSION_TOKEN_BYTES] = 0;
        issuer_allocation=value; errno = 0; return value;
    }
    if (PW_CONTROL_MODE == 3) { errno = 0; issuer_allocation=calloc(1,1); return issuer_allocation; }
    if (PW_CONTROL_MODE == 16) {
        char *value = malloc(PW_EXTENSION_TOKEN_BYTES);
        if (!value) _exit(84);
        memset(value, 'x', PW_EXTENSION_TOKEN_BYTES - 1);
        value[PW_EXTENSION_TOKEN_BYTES - 1] = 0;
        issuer_allocation=value; errno = 0; return value;
    }
    if (PW_CONTROL_MODE == 4) _exit(87);
    if (PW_CONTROL_MODE == 5) { sleep(30); _exit(88); }
    errno = 0;
    char *value = native_issue(kind, path, flags);
    int saved = errno;
    issuer_allocation=value;
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

static _Noreturn void controlled_exit(int status) {
    if ((PW_CONTROL_MODE==18 || PW_CONTROL_MODE==19 || PW_CONTROL_MODE==20) && status==0 && g_hdr) {
        observe_setup();
        observer->reserved[5]=atomic_load_explicit(&g_hdr->done,memory_order_acquire);
        observer->reserved[6]=atomic_load_explicit(&g_hdr->phases[g_hdr->phase_count-1].completed,memory_order_acquire);
        if (PW_CONTROL_MODE==20) _exit(87);
        // The actual process stays alive after its final phase and done stores.
        // Only a native owned reap can release the dependent actor's gate.
        sleep(PW_CONTROL_MODE==18 ? 1:10);
    }
    _exit(status);
}

static void controlled_publish(pw_authority_slot_t *slot) {
    switch (PW_CONTROL_MODE) {
    case 7: slot->token_length=PW_EXTENSION_TOKEN_BYTES; break;
    case 8: if(slot->token_length) slot->token[slot->token_length-1]=0; break;
    case 9: slot->token[slot->token_length]='x'; break;
    case 10:
        /* Corrupt authority bytes without contradicting the independently
           published issue length. This reaches native consume with valid
           framing; changing the length would instead falsify custody evidence. */
        if (slot->token_length>0 && slot->token_length<PW_EXTENSION_TOKEN_BYTES) {
            memset(slot->token,'x',slot->token_length);
            slot->token[slot->token_length]=0;
        }
        break;
    case 11: slot->magic^=1; break;
    case 12: slot->writer_actor+=1; break;
    case 13: /* Die before the release publication; the host must not read fields. */
        observer->reserved[0]=atomic_load_explicit(&slot->committed,memory_order_acquire); _exit(87);
    case 14: slot->family=99; break;
    case 15: slot->operation_index+=1; break;
    default: break;
    }
}
static void controlled_published(void *raw) {
    pw_shm_slot_t *slot=raw;
    if (PW_CONTROL_MODE==17 && slot->attempt_kind==PW_ATTEMPT_EXTENSION_ISSUE) {
        observer->reserved[0]=atomic_load_explicit(&slot->completed,memory_order_acquire);
        _exit(87);
    }
}
static void controlled_inbound(pw_authority_slot_t *slot) {
    worker_slot_observation=slot;
    if (slot->token_length>0 && slot->token_length<PW_EXTENSION_TOKEN_BYTES-1 && slot->token[slot->token_length]==0) {
        memset(slot->token+slot->token_length+1,0xa5,PW_EXTENSION_TOKEN_BYTES-slot->token_length-1);
        observer->reserved[2]=slot->token[PW_EXTENSION_TOKEN_BYTES-1]!=0;
        observer->reserved[3]=PW_EXTENSION_TOKEN_BYTES;
    }
    if (PW_CONTROL_MODE==106) {
        unsigned prefix=slot->token_length/2;
        observer->reserved[0]=prefix; observer->reserved[1]=memchr(slot->token,0,prefix)==NULL;
        interrupted(4,0,0); kill(getpid(),SIGKILL); _exit(83);
    }
    if (PW_CONTROL_MODE==116) slot->token_length=0;
    if (PW_CONTROL_MODE==117) slot->token_length=PW_EXTENSION_TOKEN_BYTES;
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
    if (p == MAP_FAILED) return p;
    pw_authority_region_t *region=p;
    switch (PW_CONTROL_MODE) {
    case 113: region->magic^=1; break;
    case 114: region->identity[0]^=1; break;
    case 115: region->actor_index+=1; break;
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
