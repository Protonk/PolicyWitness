/* Independent native experiment. No PW ABI, classifier, or phase code.
 * The fixed gates are test apparatus; the parent queries a paused worker.
 * Tokens occupy a separate unlinked shm object, never the evidence object.
 * All roles exec the same signed binary with an explicit descriptor set.
 */
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <signal.h>
#include <spawn.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define TOKEN_CAP 16384u
#define CONTENT_CAP 64u
#define BOUNDARIES 4u
#define DEADLINE_SECONDS 20

/* Declarations independently corroborated by WebKit's SandboxSPI.h. */
typedef char *(*issue_fn)(const char *, const char *, uint32_t);
typedef int64_t (*consume_fn)(const char *);
typedef int (*release_fn)(int64_t);
typedef int (*check_fn)(pid_t, const char *, int, ...);
typedef void *(*compile_fn)(const char *, void *, char **);
typedef int (*apply_fn)(void *);
typedef void logger_fn(uint32_t, uintptr_t, uintptr_t, uintptr_t, uintptr_t, uint32_t);

/* Static, lock-free bookkeeping: first-use TLS resolution can itself allocate.
 * Count callbacks from any thread during the native-call window. */
_Static_assert(ATOMIC_LLONG_LOCK_FREE == 2 && ATOMIC_POINTER_LOCK_FREE == 2, "nonallocating counters required");
struct counts { _Atomic uint64_t calls, alloc, dealloc, vm_alloc, vm_dealloc; _Atomic uint32_t types; };
static _Atomic(struct counts *) measurement;
static void allocation_logger(uint32_t type, uintptr_t a, uintptr_t b, uintptr_t c,
                              uintptr_t result, uint32_t skip) {
    (void)a; (void)b; (void)c; (void)result; (void)skip;
    struct counts *out = atomic_load_explicit(&measurement, memory_order_relaxed);
    if (!out) return;
    out->calls++;
    out->types |= type;
    if (type & 2u) out->alloc++;
    if (type & 4u) out->dealloc++;
    if (type & 16u) out->vm_alloc++;
    if (type & 32u) out->vm_dealloc++;
}

struct file_identity { uint64_t dev, ino, mode, uid, gid, size; };
struct access_result {
    int open_attempted, open_rc, open_errno;
    int stat_attempted, stat_rc, stat_errno;
    int read_attempted, read_errno, close_attempted, close_rc, close_errno;
    int seek_attempted, seek_errno;
    int64_t read_rc, seek_rc;
    unsigned char content[CONTENT_CAP];
    struct file_identity identity;
};
struct call_result { int attempted, saved_errno; int64_t rc; struct counts allocations; };
struct evidence {
    char scenario[64], target[PATH_MAX], submitted_issue[PATH_MAX], issue_path[PATH_MAX];
    int instrument, no_consume, no_release, no_predicate, retain_fd, issuer_exits;
    int rejected_token, bad_issue_path, logger_available, syscall_logger_available;
    int capability, compile_ok, apply_count, worker_pid, issuer_pid;
    int worker_uid, worker_euid, worker_gid, worker_egid;
    int issuer_uid, issuer_euid, issuer_gid, issuer_egid;
    int inherited_target_fds, inherited_other_target_fds, fd_scan_limit;
    int preparation_rc, preparation_errno, issue_nonnull;
    uint32_t issue_flags, token_length;
    struct file_identity target_identity, issue_identity;
    struct call_result issue, apply, consume, release;
    struct counts positive_before, positive_after;
    struct access_result parent_baseline, access[BOUNDARIES], retained;
    int fds_before_consume, fds_after_consume, fds_after_release;
    _Atomic unsigned arrival, go, ack[BOUNDARIES], issued, issuer_stop, worker_done;
};
struct token_channel { char bytes[TOKEN_CAP]; };
static const char *policy_with_predicate =
    "(version 1) (allow default) (deny file-read-data) "
    "(allow file-read-data (extension \"com.apple.app-sandbox.read\"))";
static const char *policy_without_predicate =
    "(version 1) (allow default) (deny file-read-data)";

static void identity_from_stat(struct file_identity *out, const struct stat *st) {
    *out = (struct file_identity){(uint64_t)st->st_dev, st->st_ino, st->st_mode,
                                 st->st_uid, st->st_gid, (uint64_t)st->st_size};
}
static double now(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts)) _exit(90);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}
static void pause_briefly(void) {
    struct timespec ts = {0, 1000000};
    nanosleep(&ts, NULL);
}
static void erase(void *p, size_t n) {
    volatile unsigned char *bytes = p;
    while (n--) *bytes++ = 0;
}
static void read_fd(int fd, struct access_result *out) {
    struct stat st;
    out->stat_attempted = 1; errno = 0;
    out->stat_rc = fstat(fd, &st); out->stat_errno = errno;
    if (!out->stat_rc) identity_from_stat(&out->identity, &st);
    out->read_attempted = 1; errno = 0;
    out->read_rc = read(fd, out->content, sizeof(out->content)); out->read_errno = errno;
}
static void close_fd(int fd, struct access_result *out) {
    out->close_attempted = 1; errno = 0;
    out->close_rc = close(fd); out->close_errno = errno;
}
static int access_file(const char *path, struct access_result *out, int retain) {
    out->open_attempted = 1; errno = 0;
    out->open_rc = open(path, O_RDONLY | O_CLOEXEC); out->open_errno = errno;
    if (out->open_rc < 0) return -1;
    read_fd(out->open_rc, out);
    if (!retain) close_fd(out->open_rc, out);
    return retain ? out->open_rc : -1;
}
static int fd_count(int limit) {
    int count = 0;
    for (int fd = 0; fd < limit; fd++) if (fcntl(fd, F_GETFD) >= 0) count++;
    return count;
}
static int matching_fds(const struct file_identity *target, int limit) {
    int count = 0;
    for (int fd = 0; fd < limit; fd++) {
        struct stat st;
        if (!fstat(fd, &st) && (uint64_t)st.st_dev == target->dev && st.st_ino == target->ino) count++;
    }
    return count;
}
static void positive_control(struct counts *out) {
    measurement = out;
    void *p = malloc(123);
    if (p) { memset(p, 0x5a, 123); free(p); }
    void *v = mmap(NULL, 16384, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON, -1, 0);
    if (v != MAP_FAILED) munmap(v, 16384);
    measurement = NULL;
}
/* No policy or token exists in this diagnostic process. Its stderr can be
 * retained safely when investigating a platform instrumentation failure. */
static int allocation_probe(const char *symbol) {
    logger_fn **logger = dlsym(RTLD_DEFAULT, symbol);
    if (!logger) return 92;
    write(1, "install\n", 8);
    *logger = allocation_logger;
    write(1, "installed\n", 10);
    struct counts counts = {0};
    positive_control(&counts);
    write(1, "observed\n", 9);
    *logger = NULL;
    printf("callbacks=%llu alloc=%llu dealloc=%llu vm_alloc=%llu vm_dealloc=%llu\n",
           counts.calls, counts.alloc, counts.dealloc, counts.vm_alloc, counts.vm_dealloc);
    return 0;
}
static int gate(struct evidence *e, unsigned index) {
    atomic_store_explicit(&e->arrival, index + 1, memory_order_release);
    double deadline = now() + DEADLINE_SECONDS;
    while (atomic_load_explicit(&e->go, memory_order_acquire) != index + 1) {
        if (now() >= deadline) return -1;
        pause_briefly();
    }
    atomic_store_explicit(&e->ack[index], 1, memory_order_release);
    return 0;
}
static int child_main(const char *role) {
    struct evidence *e = mmap(NULL, sizeof(*e), PROT_READ | PROT_WRITE, MAP_SHARED, 3, 0);
    struct token_channel *token = mmap(NULL, sizeof(*token), PROT_READ | PROT_WRITE, MAP_SHARED, 4, 0);
    if (e == MAP_FAILED || token == MAP_FAILED) return 91;
    close(3); close(4);
    if (!strcmp(role, "--issuer")) {
        e->issuer_pid = getpid(); e->issuer_uid = getuid(); e->issuer_euid = geteuid();
        e->issuer_gid = getgid(); e->issuer_egid = getegid();
        issue_fn issue = (issue_fn)dlsym(RTLD_DEFAULT, "sandbox_extension_issue_file");
        if (!issue) return 92;
        e->issue.attempted = 1; errno = 0;
        char *raw = issue("com.apple.app-sandbox.read", e->bad_issue_path ? "" : e->issue_path, e->issue_flags);
        e->issue.saved_errno = errno;
        e->issue_nonnull = raw != NULL;
        if (raw) {
            size_t n = strnlen(raw, TOKEN_CAP);
            if (n >= TOKEN_CAP) { erase(raw, n); free(raw); return 93; }
            memcpy(token->bytes, raw, n + 1); e->token_length = (uint32_t)n;
            erase(raw, n); free(raw);
        }
        atomic_store_explicit(&e->issued, 1, memory_order_release);
        if (!e->issuer_exits) {
            double deadline = now() + DEADLINE_SECONDS;
            while (!atomic_load_explicit(&e->issuer_stop, memory_order_acquire)) {
                if (now() >= deadline) return 94;
                pause_briefly();
            }
        }
        return 0;
    }
    e->worker_pid = getpid(); e->worker_uid = getuid(); e->worker_euid = geteuid();
    e->worker_gid = getgid(); e->worker_egid = getegid();
    consume_fn consume = (consume_fn)dlsym(RTLD_DEFAULT, "sandbox_extension_consume");
    release_fn release = (release_fn)dlsym(RTLD_DEFAULT, "sandbox_extension_release");
    compile_fn compile = (compile_fn)dlsym(RTLD_DEFAULT, "sandbox_compile_string");
    apply_fn apply = (apply_fn)dlsym(RTLD_DEFAULT, "sandbox_apply");
    e->capability = consume && release && compile && apply;
    if (!e->capability) return 92;
    if (e->instrument) {
        logger_fn **logger = dlsym(RTLD_DEFAULT, "malloc_logger");
        logger_fn **syscall_logger = dlsym(RTLD_DEFAULT, "__syscall_logger");
        e->logger_available = logger != NULL; e->syscall_logger_available = syscall_logger != NULL;
        if (logger) *logger = allocation_logger;
        if (syscall_logger) *syscall_logger = allocation_logger;
        positive_control(&e->positive_before);
    }
    e->fd_scan_limit = getdtablesize();
    e->inherited_target_fds = matching_fds(&e->target_identity, e->fd_scan_limit);
    e->inherited_other_target_fds = matching_fds(&e->issue_identity, e->fd_scan_limit);
    access_file(e->target, &e->access[0], 0);
    char *error = NULL;
    void *profile = compile(e->no_predicate ? policy_without_predicate : policy_with_predicate, NULL, &error);
    e->compile_ok = profile != NULL;
    /* Do not forward arbitrary native diagnostics into retained output. */
    if (!profile) return 95;
    if (gate(e, 0)) return 96;
    e->apply.attempted = 1; e->apply_count++; errno = 0;
    e->apply.rc = apply(profile); e->apply.saved_errno = errno;
    if (e->apply.rc) return 97;
    if (gate(e, 1)) return 96;
    access_file(e->target, &e->access[1], 0);
    e->fds_before_consume = fd_count(e->fd_scan_limit);
    if (!e->no_consume && e->issue_nonnull) {
        e->consume.attempted = 1;
        measurement = e->instrument ? &e->consume.allocations : NULL;
        errno = 0; e->consume.rc = consume(token->bytes); e->consume.saved_errno = errno;
        measurement = NULL;
    }
    erase(token, sizeof(*token));
    e->fds_after_consume = fd_count(e->fd_scan_limit);
    if (gate(e, 2)) return 96;
    int retained = access_file(e->target, &e->access[2], e->retain_fd);
    if (!e->no_release && e->consume.attempted && e->consume.rc != -1) {
        e->release.attempted = 1;
        measurement = e->instrument ? &e->release.allocations : NULL;
        errno = 0; e->release.rc = release(e->consume.rc); e->release.saved_errno = errno;
        measurement = NULL;
    }
    e->fds_after_release = fd_count(e->fd_scan_limit);
    if (gate(e, 3)) return 96;
    access_file(e->target, &e->access[3], 0);
    if (retained >= 0) {
        e->retained.seek_attempted = 1; errno = 0;
        e->retained.seek_rc = lseek(retained, 0, SEEK_SET); e->retained.seek_errno = errno;
        read_fd(retained, &e->retained); close_fd(retained, &e->retained);
    }
    if (e->instrument) positive_control(&e->positive_after);
    atomic_store_explicit(&e->worker_done, 1, memory_order_release);
    return 0;
}

static int shared_region(size_t size, void **mapping) {
    char name[64]; snprintf(name, sizeof(name), "/pw-ext-%d-%08x", getpid(), arc4random());
    int fd = shm_open(name, O_RDWR | O_CREAT | O_EXCL, 0600);
    if (fd < 0) return -1;
    if (shm_unlink(name) || ftruncate(fd, (off_t)size)) { close(fd); return -1; }
    *mapping = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (*mapping == MAP_FAILED) { close(fd); return -1; }
    memset(*mapping, 0, size);
    /* Darwin shm descriptors are CLOEXEC. Use a distinct source for each
     * spawn dup2 action: dup2(fd, fd) does not clear that descriptor flag. */
    int transport_fd = fcntl(fd, F_DUPFD_CLOEXEC, 10);
    close(fd);
    return transport_fd;
}
static int spawn_role(const char *exe, const char *role, int evidence_fd, int token_fd, pid_t *pid) {
    posix_spawn_file_actions_t actions;
    posix_spawnattr_t attr;
    int rc = posix_spawn_file_actions_init(&actions);
    if (rc) return rc;
    rc = posix_spawnattr_init(&attr);
    if (rc) { posix_spawn_file_actions_destroy(&actions); return rc; }
    if (!(rc = posix_spawnattr_setflags(&attr, POSIX_SPAWN_CLOEXEC_DEFAULT)) &&
        !(rc = posix_spawn_file_actions_addopen(&actions, 0, "/dev/null", O_RDONLY, 0)) &&
        !(rc = posix_spawn_file_actions_addopen(&actions, 1, "/dev/null", O_WRONLY, 0)) &&
        !(rc = posix_spawn_file_actions_addopen(&actions, 2, "/dev/null", O_WRONLY, 0)) &&
        !(rc = posix_spawn_file_actions_adddup2(&actions, evidence_fd, 3)) &&
        !(rc = posix_spawn_file_actions_adddup2(&actions, token_fd, 4))) {
        char *argv[] = {(char *)exe, (char *)role, NULL};
        char *env[] = {"PATH=/usr/bin:/bin", "LC_ALL=C", NULL};
        rc = posix_spawn(pid, exe, &actions, &attr, argv, env);
    }
    posix_spawn_file_actions_destroy(&actions); posix_spawnattr_destroy(&attr);
    return rc;
}
static int reap(pid_t pid, int *status, double deadline) {
    for (;;) {
        pid_t rc = waitpid(pid, status, WNOHANG);
        if (rc == pid) return 1;
        if (rc < 0 && errno != EINTR) return 0;
        if (now() >= deadline) return 0;
        pause_briefly();
    }
}
static void string(FILE *f, const char *s) {
    fputc('"', f);
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
        if (*p == '"' || *p == '\\') { fputc('\\', f); fputc(*p, f); }
        else if (*p < 32 || *p >= 127) fprintf(f, "\\u%04x", *p);
        else fputc(*p, f);
    }
    fputc('"', f);
}
static void json_counts(FILE *f, struct counts c) {
    fprintf(f, "{\"callbacks\":%llu,\"alloc\":%llu,\"dealloc\":%llu,\"vm_alloc\":%llu,\"vm_dealloc\":%llu,\"type_mask\":%u}",
        c.calls, c.alloc, c.dealloc, c.vm_alloc, c.vm_dealloc, c.types);
}
static void json_call(FILE *f, const struct call_result *c) {
    fprintf(f, "{\"attempted\":%s,\"native_rc\":", c->attempted ? "true" : "false");
    if (c->attempted) fprintf(f, "%lld", c->rc); else fputs("null", f);
    fprintf(f, ",\"errno_after_zeroing\":%d,\"allocations\":", c->saved_errno);
    json_counts(f, c->allocations); fputc('}', f);
}
static void json_identity(FILE *f, const struct file_identity *i) {
    fprintf(f, "{\"device\":%llu,\"inode\":%llu,\"mode\":%llu,\"uid\":%llu,\"gid\":%llu,\"size\":%llu}",
        i->dev, i->ino, i->mode, i->uid, i->gid, i->size);
}
static void json_access(FILE *f, const struct access_result *a) {
    fprintf(f, "{\"open_attempted\":%d,\"open_rc\":%d,\"open_errno\":%d,\"stat_attempted\":%d,\"stat_rc\":%d,\"stat_errno\":%d,"
        "\"read_attempted\":%d,\"read_rc\":%lld,\"read_errno\":%d,\"close_attempted\":%d,\"close_rc\":%d,\"close_errno\":%d,"
        "\"seek_attempted\":%d,\"seek_rc\":%lld,\"seek_errno\":%d,\"identity\":",
        a->open_attempted,a->open_rc,a->open_errno,a->stat_attempted,a->stat_rc,a->stat_errno,
        a->read_attempted,a->read_rc,a->read_errno,a->close_attempted,a->close_rc,a->close_errno,
        a->seek_attempted,a->seek_rc,a->seek_errno);
    json_identity(f, &a->identity); fputs(",\"content_hex\":\"", f);
    for (int64_t i = 0; i < a->read_rc && i < CONTENT_CAP; i++) fprintf(f, "%02x", a->content[i]);
    fputs("\"}", f);
}

int main(int argc, char **argv) {
    struct rlimit no_core = {0, 0};
    if (setrlimit(RLIMIT_CORE, &no_core)) return 89;
    if (argc == 3 && !strcmp(argv[1], "--allocation-probe")) return allocation_probe(argv[2]);
    if (argc == 2 && (!strcmp(argv[1], "--worker") || !strcmp(argv[1], "--issuer"))) return child_main(argv[1]);
    if (argc != 5) { fputs("usage: native CASE TARGET ISSUANCE_TARGET instrument|plain\n", stderr); return 2; }
    const char *cases[] = {"lifecycle", "issuer_exit", "no_consume", "no_release", "no_predicate", "different_target", "issue_failure", "rejected_token", "retained_fd"};
    bool known = false;
    for (size_t i = 0; i < sizeof(cases)/sizeof(cases[0]); i++) if (!strcmp(argv[1], cases[i])) known = true;
    if (!known || (strcmp(argv[4], "instrument") && strcmp(argv[4], "plain"))) return 2;
    struct evidence *e;
    struct token_channel *token;
    int efd = shared_region(sizeof(*e), (void **)&e);
    int tfd = shared_region(sizeof(*token), (void **)&token);
    if (efd < 0 || tfd < 0) { fputs("shared-memory preparation failed\n", stderr); return 3; }
    if (strlen(argv[1]) >= sizeof(e->scenario) || strlen(argv[2]) >= PATH_MAX || strlen(argv[3]) >= PATH_MAX) return 2;
    strcpy(e->scenario, argv[1]); strcpy(e->target, argv[2]); strcpy(e->submitted_issue, argv[3]);
    e->instrument = !strcmp(argv[4], "instrument");
    e->no_consume = !strcmp(argv[1], "no_consume"); e->no_release = !strcmp(argv[1], "no_release");
    e->no_predicate = !strcmp(argv[1], "no_predicate"); e->retain_fd = !strcmp(argv[1], "retained_fd");
    e->issuer_exits = !strcmp(argv[1], "issuer_exit"); e->rejected_token = !strcmp(argv[1], "rejected_token");
    e->bad_issue_path = !strcmp(argv[1], "issue_failure"); e->issue_flags = 0;
    struct stat st;
    if (stat(e->target, &st)) { fputs("target stat failed\n", stderr); return 3; }
    identity_from_stat(&e->target_identity, &st);
    errno = 0;
    if (!realpath(e->submitted_issue, e->issue_path) || stat(e->issue_path, &st)) {
        e->preparation_rc = -1; e->preparation_errno = errno;
        fputs("issuance target preparation failed\n", stderr); return 3;
    }
    identity_from_stat(&e->issue_identity, &st);
    access_file(e->target, &e->parent_baseline, 0);
    char executable[PATH_MAX], pathbuf[PATH_MAX]; uint32_t size = sizeof(pathbuf);
    if (_NSGetExecutablePath(pathbuf, &size) || !realpath(pathbuf, executable)) return 3;
    check_fn check = (check_fn)dlsym(RTLD_DEFAULT, "sandbox_check");
    const int *no_report = dlsym(RTLD_DEFAULT, "SANDBOX_CHECK_NO_REPORT");
    if (!check || !no_report) { fputs("query capability unavailable\n", stderr); return 3; }
    struct call_result queries[BOUNDARIES] = {0};
    pid_t worker = 0, issuer = 0;
    int worker_status = -1, issuer_status = -1, worker_reaped = 0, issuer_reaped = 0, failure = 0;
    unsigned observed = 0;
    int issuer_exited_before_queries = 0, issuer_live[BOUNDARIES] = {0};
    double deadline = now() + DEADLINE_SECONDS;
    char private_token[TOKEN_CAP] = {0}; size_t private_length = 0;
    int wspawn = spawn_role(executable, "--worker", efd, tfd, &worker);
    int ispawn = wspawn ? -1 : spawn_role(executable, "--issuer", efd, tfd, &issuer);
    close(efd); close(tfd);
    if (wspawn || ispawn) { failure = 1; goto cleanup; }
    while (!atomic_load_explicit(&e->issued, memory_order_acquire)) {
        pid_t result = waitpid(issuer, &issuer_status, WNOHANG);
        if (result == issuer) {
            issuer_reaped = 1;
            if (atomic_load_explicit(&e->issued, memory_order_acquire)) break;
            failure = 8; goto cleanup;
        }
        if (result < 0 && errno != EINTR) { failure = 9; goto cleanup; }
        if (now() >= deadline) { failure = 2; goto cleanup; }
        pause_briefly();
    }
    private_length = e->token_length;
    memcpy(private_token, token->bytes, private_length);
    if (e->rejected_token) { erase(token, sizeof(*token)); strcpy(token->bytes, "invalid-native-control"); }
    if (e->issuer_exits) {
        if (!issuer_reaped) issuer_reaped = reap(issuer, &issuer_status, deadline);
        issuer_exited_before_queries = issuer_reaped;
        if (!issuer_reaped) { failure = 3; goto cleanup; }
    }
    for (unsigned i = 0; i < BOUNDARIES; i++) {
        while (atomic_load_explicit(&e->arrival, memory_order_acquire) != i + 1) {
            pid_t w = waitpid(worker, &worker_status, WNOHANG);
            if (w == worker) { worker_reaped = 1; failure = 4; goto cleanup; }
            if (w < 0 && errno != EINTR) { failure = 5; goto cleanup; }
            if (now() >= deadline) { failure = 6; goto cleanup; }
            pause_briefly();
        }
        observed++;
        if (!issuer_reaped) {
            pid_t alive = waitpid(issuer, &issuer_status, WNOHANG);
            issuer_live[i] = alive == 0;
            if (alive == issuer) issuer_reaped = 1;
        }
        queries[i].attempted = 1; errno = 0;
        queries[i].rc = check(worker, "file-read-data", 1 | *no_report, e->target);
        queries[i].saved_errno = errno;
        atomic_store_explicit(&e->go, i + 1, memory_order_release);
    }
    worker_reaped = reap(worker, &worker_status, deadline);
    if (!worker_reaped) failure = 7;
cleanup:
    atomic_store_explicit(&e->issuer_stop, 1, memory_order_release);
    int worker_kill = 0, issuer_kill = 0;
    if (worker > 0 && !worker_reaped) { worker_kill = kill(worker, SIGKILL); worker_reaped = reap(worker, &worker_status, now() + 2); }
    if (issuer > 0 && !issuer_reaped) {
        issuer_reaped = reap(issuer, &issuer_status, now() + 2);
        if (!issuer_reaped) { issuer_kill = kill(issuer, SIGKILL); issuer_reaped = reap(issuer, &issuer_status, now() + 2); }
    }
    bool worker_erased = true;
    for (size_t i = 0; i < sizeof(*token); i++) if (((unsigned char *)token)[i]) worker_erased = false;
    erase(token, sizeof(*token));
    char *json = NULL; size_t json_size = 0;
    FILE *f = open_memstream(&json, &json_size);
    if (!f) return 3;
    fputs("{\"scenario\":", f); string(f, e->scenario);
    fputs(",\"target\":", f); string(f, e->target);
    fputs(",\"submitted_issue\":", f); string(f, e->submitted_issue);
    fputs(",\"resolved_issue\":", f); string(f, e->issue_path);
    fputs(",\"issue_class\":", f); string(f, "com.apple.app-sandbox.read");
    fputs(",\"native_issue_path\":", f); string(f, e->bad_issue_path ? "" : e->issue_path);
    fputs(",\"policy\":", f); string(f, e->no_predicate ? policy_without_predicate : policy_with_predicate);
    fprintf(f, ",\"instrumented\":%d,\"host_pid\":%d,\"worker_pid\":%d,\"issuer_pid\":%d,\"worker_uid\":%d,\"worker_euid\":%d,\"worker_gid\":%d,\"worker_egid\":%d,"
        "\"issuer_uid\":%d,\"issuer_euid\":%d,\"issuer_gid\":%d,\"issuer_egid\":%d,\"compile_ok\":%d,\"apply_count\":%d,\"capability\":%d,"
        "\"inherited_target_fds\":%d,\"inherited_other_target_fds\":%d,\"fd_scan_limit\":%d,\"issue_flags\":%u,\"issue_nonnull\":%d,\"token_length\":%u,"
        "\"observed_boundaries\":%u,\"worker_done\":%u,\"failure\":%d,\"worker_reaped\":%d,\"worker_wait_status\":%d,\"issuer_reaped\":%d,\"issuer_wait_status\":%d,"
        "\"issuer_exited_before_queries\":%d,\"worker_kill_rc\":%d,\"issuer_kill_rc\":%d,\"worker_erased_channel\":%s,\"token_guard_passed\":true,"
        "\"consume_return_bits\":%zu,\"release_return_bits\":%zu,\"logger_available\":%d,\"syscall_logger_available\":%d,"
        "\"fds_before_consume\":%d,\"fds_after_consume\":%d,\"fds_after_release\":%d",
        e->instrument,getpid(),e->worker_pid,e->issuer_pid,e->worker_uid,e->worker_euid,e->worker_gid,e->worker_egid,
        e->issuer_uid,e->issuer_euid,e->issuer_gid,e->issuer_egid,e->compile_ok,e->apply_count,e->capability,
        e->inherited_target_fds,e->inherited_other_target_fds,e->fd_scan_limit,e->issue_flags,e->issue_nonnull,e->token_length,
        observed,atomic_load(&e->worker_done),failure,worker_reaped,worker_status,issuer_reaped,issuer_status,
        issuer_exited_before_queries,worker_kill,issuer_kill,worker_erased ? "true" : "false",
        sizeof(int64_t)*CHAR_BIT,sizeof(int)*CHAR_BIT,e->logger_available,e->syscall_logger_available,
        e->fds_before_consume,e->fds_after_consume,e->fds_after_release);
    fputs(",\"target_identity\":", f); json_identity(f, &e->target_identity);
    fputs(",\"issue_identity\":", f); json_identity(f, &e->issue_identity);
    fputs(",\"parent_baseline\":", f); json_access(f, &e->parent_baseline);
    fputs(",\"apply\":", f); json_call(f, &e->apply);
    /* Pointer returns are represented by null/non-null, never an address. */
    fprintf(f, ",\"issue\":{\"attempted\":%s,\"nonnull\":%s,\"errno_after_zeroing\":%d}",
        e->issue.attempted ? "true" : "false", e->issue_nonnull ? "true" : "false", e->issue.saved_errno);
    fputs(",\"consume\":", f); json_call(f, &e->consume);
    fputs(",\"release\":", f); json_call(f, &e->release);
    fputs(",\"retained\":", f); json_access(f, &e->retained);
    fputs(",\"positive_before\":", f); json_counts(f, e->positive_before);
    fputs(",\"positive_after\":", f); json_counts(f, e->positive_after);
    fputs(",\"boundaries\":[", f);
    for (unsigned i = 0; i < BOUNDARIES; i++) {
        if (i) fputc(',', f);
        fprintf(f, "{\"index\":%u,\"ack\":%u,\"issuer_waitpid_observed_live\":%d,\"query\":", i, atomic_load(&e->ack[i]), issuer_live[i]);
        json_call(f, &queries[i]); fputs(",\"access\":", f); json_access(f, &e->access[i]); fputc('}', f);
    }
    fputs("]}\n", f); fclose(f);
    bool leak = private_length && memmem(json, json_size, private_token, private_length);
    erase(private_token, sizeof(private_token));
    if (leak) { erase(json, json_size); free(json); fputs("token confinement failure; output withheld\n", stderr); return 8; }
    fwrite(json, 1, json_size, stdout); free(json);
    munmap(token, sizeof(*token)); munmap(e, sizeof(*e));
    return failure || !worker_reaped || !issuer_reaped || worker_status || issuer_status ? 1 : 0;
}
