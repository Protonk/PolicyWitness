/* Independent Q1/Q2 apparatus adapted from the native extension fixture.
 * No production PW ABI, classifier, or phase code. Token bytes occupy only
 * two anonymous-after-unlink mappings and the issuer's native allocation.
 * Child evidence publications never contain token bytes or token hashes.
 */
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <libproc.h>
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
#include <sys/proc_info.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define TOKEN_CAP 16384u
#define CONTENT_CAP 128u
#define EVENT_CAP 65536u
#define EVENT_COUNT 48u
#define FD_CAP 256u
#define POLICY_CAP (PATH_MAX * 3u)
#define LOCK_CAP 16u
#define TOKEN_MAGIC UINT32_C(0x42545031)
#define NS_PER_SECOND UINT64_C(1000000000)

typedef char *(*issue_fn)(const char *, const char *, uint32_t);
typedef int64_t (*consume_fn)(const char *);
typedef void *(*compile_fn)(const char *, void *, char **);
typedef int (*apply_fn)(void *);
typedef int (*check_fn)(pid_t, const char *, int, ...);
extern char **environ;

struct identity { uint64_t device, inode, mode, uid, gid, size; };
struct call { bool attempted; int64_t rc; int error; };
struct access_observation {
    struct call open, identity_check, read, close;
    int descriptor;
    struct identity identity;
    unsigned char bytes[CONTENT_CAP];
};
struct fd_entry {
    int fd, stat_rc, stat_errno;
    uint32_t native_type;
    struct identity identity;
};
struct fd_snapshot {
    int inventory_rc, inventory_errno, scan_limit;
    size_t count;
    bool complete;
    struct fd_entry descriptors[FD_CAP];
};
struct json { char bytes[EVENT_CAP]; size_t used; bool failed; };
struct event {
    uint64_t when;
    char stage[40], status[16];
    char details[EVENT_CAP];
};
struct role_state {
    _Atomic unsigned published, acknowledged;
    _Atomic unsigned ready, application_ok, accepted, completed;
    struct event events[EVENT_COUNT];
};
struct token_channel {
    uint32_t magic, length;
    unsigned char bytes[TOKEN_CAP];
};
struct shared {
    char arrangement[3], trial_id[160], executable[PATH_MAX];
    char a[PATH_MAX], b[PATH_MAX];
    char issuer_policy[POLICY_CAP], recipient_policy[POLICY_CAP];
    struct identity a_identity, b_identity;
    uint64_t deadline;
    _Atomic unsigned issue_release, transfer_release, consume_release, issuer_exit;
    _Atomic unsigned issue_ready, delivery_ready, consume_permitted;
    struct role_state role[2];
};

static const char extension_class[] = "com.apple.app-sandbox.read";
static const char a_content[] = "PolicyWitness browser pilot target A\n";
static const char b_content[] = "PolicyWitness browser pilot target B\n";
static const char *role_names[] = {"issuer", "recipient"};
static uint64_t global_sequence;
static bool output_failed;
static bool channel_cleanup_pending;

static uint64_t monotonic_ns(void) {
    struct timespec t;
    /* Without the clock there is no trustworthy native deadline. The driver
     * retains prior publications and owns bounded process-group cleanup. */
    if (clock_gettime(CLOCK_MONOTONIC, &t)) _exit(90);
    return (uint64_t)t.tv_sec * NS_PER_SECOND + (uint64_t)t.tv_nsec;
}
static void brief_pause(void) {
    const struct timespec t = {0, 1000000};
    (void)nanosleep(&t, NULL);
}
static void erase(void *p, size_t length) {
    volatile unsigned char *b = p;
    while (length--) *b++ = 0;
}
static bool all_zero(const void *p, size_t length) {
    const unsigned char *b = p;
    for (size_t i = 0; i < length; i++) if (b[i]) return false;
    return true;
}
static void jf(struct json *j, const char *format, ...) {
    if (j->failed) return;
    va_list args;
    va_start(args, format);
    int n = vsnprintf(j->bytes + j->used, sizeof(j->bytes) - j->used, format, args);
    va_end(args);
    if (n < 0 || (size_t)n >= sizeof(j->bytes) - j->used) { j->failed = true; return; }
    j->used += (size_t)n;
}
static void js(struct json *j, const char *s) {
    if (!s) { jf(j, "null"); return; }
    jf(j, "\"");
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
        if (*p == '"' || *p == '\\') jf(j, "\\%c", *p);
        else if (*p < 32 || *p >= 127) jf(j, "\\u%04x", *p);
        else jf(j, "%c", *p);
    }
    jf(j, "\"");
}
static void hex(struct json *j, const unsigned char *p, size_t length) {
    jf(j, "\"");
    for (size_t i = 0; i < length; i++) jf(j, "%02x", p[i]);
    jf(j, "\"");
}
static const char *boolean(bool value) { return value ? "true" : "false"; }
static void identify(struct identity *i, const struct stat *s) {
    *i = (struct identity){(uint64_t)(uint32_t)s->st_dev, (uint64_t)s->st_ino,
        s->st_mode, s->st_uid, s->st_gid, (uint64_t)s->st_size};
}
static void ji(struct json *j, const struct identity *i) {
    jf(j, "{\"device\":%" PRIu64 ",\"inode\":%" PRIu64 ",\"mode\":%" PRIu64
        ",\"uid\":%" PRIu64 ",\"gid\":%" PRIu64 ",\"size\":%" PRIu64 "}",
        i->device, i->inode, i->mode, i->uid, i->gid, i->size);
}
static bool same_identity(const struct identity *a, const struct identity *b) {
    return a->device == b->device && a->inode == b->inode;
}
static void jc(struct json *j, const struct call *c, const char *reason) {
    if (c->attempted) jf(j, "{\"status\":\"attempted\",\"rc\":%" PRId64 ",\"errno\":%d}", c->rc, c->error);
    else { jf(j, "{\"status\":\"unavailable\",\"reason\":"); js(j, reason); jf(j, "}"); }
}
static void access_file(const char *path, struct access_observation *a) {
    memset(a, 0, sizeof(*a)); a->descriptor = -1;
    a->open.attempted = true; errno = 0;
    int fd = open(path, O_RDONLY | O_CLOEXEC); int saved = errno;
    a->open.rc = fd; a->open.error = saved; a->descriptor = fd;
    if (fd < 0) return;
    struct stat s;
    a->identity_check.attempted = true; errno = 0;
    int rc = fstat(fd, &s); saved = errno;
    a->identity_check.rc = rc; a->identity_check.error = saved;
    if (!rc) identify(&a->identity, &s);
    a->read.attempted = true; errno = 0;
    ssize_t count = read(fd, a->bytes, sizeof(a->bytes)); saved = errno;
    a->read.rc = count; a->read.error = saved;
    a->close.attempted = true; errno = 0;
    rc = close(fd); saved = errno;
    a->close.rc = rc; a->close.error = saved;
}
static void ja(struct json *j, const char *path, const struct access_observation *a) {
    jf(j, "{\"path\":"); js(j, path); jf(j, ",\"descriptor\":");
    if (a->descriptor < 0) jf(j, "null"); else jf(j, "%d", a->descriptor);
    jf(j, ",\"open\":"); jc(j, &a->open, "boundary_not_reached");
    jf(j, ",\"identity_check\":"); jc(j, &a->identity_check, "open_failed");
    jf(j, ",\"read\":"); jc(j, &a->read, "open_failed");
    jf(j, ",\"close\":"); jc(j, &a->close, "open_failed");
    jf(j, ",\"identity\":");
    if (a->identity_check.attempted && !a->identity_check.rc) ji(j, &a->identity); else jf(j, "null");
    jf(j, ",\"content_hex\":");
    hex(j, a->bytes, a->read.attempted && a->read.rc > 0 ? (size_t)a->read.rc : 0);
    jf(j, "}");
}
static void snapshot(struct fd_snapshot *out) {
    memset(out, 0, sizeof(*out));
    struct proc_fdinfo fds[FD_CAP];
    out->scan_limit = getdtablesize();
    errno = 0;
    int count = proc_pidinfo(getpid(), PROC_PIDLISTFDS, 0, fds, sizeof(fds));
    out->inventory_errno = errno; out->inventory_rc = count;
    out->complete = count > 0 && count < (int)sizeof(fds) && (size_t)count % sizeof(fds[0]) == 0;
    if (count < 0) return;
    out->count = (size_t)count / sizeof(fds[0]);
    if (out->count > FD_CAP) out->count = FD_CAP;
    for (size_t n = 0; n < out->count; n++) {
        struct fd_entry *v = &out->descriptors[n];
        v->fd = fds[n].proc_fd; v->native_type = fds[n].proc_fdtype;
        struct stat s; errno = 0;
        v->stat_rc = fstat(v->fd, &s); v->stat_errno = errno;
        if (!v->stat_rc) identify(&v->identity, &s);
    }
}
static const char *fd_type(const struct fd_entry *v) {
    if (!v->stat_rc) {
        mode_t mode = (mode_t)v->identity.mode;
        if (S_ISREG(mode)) return "regular";
        if (S_ISDIR(mode)) return "directory";
        if (S_ISCHR(mode)) return "character";
        if (S_ISFIFO(mode)) return "pipe";
        if (S_ISSOCK(mode)) return "socket";
    }
    return "other";
}
static void j_snapshot(struct json *j, const char *boundary,
                       const struct fd_snapshot *s, const struct shared *e) {
    jf(j, "{\"boundary\":"); js(j, boundary);
    jf(j, ",\"inspection_complete\":%s,\"scan_limit\":%d,\"inventory_rc\":%d,\"inventory_errno\":%d,\"descriptors\":[",
        boolean(s->complete), s->scan_limit, s->inventory_rc, s->inventory_errno);
    for (size_t n = 0; n < s->count; n++) {
        const struct fd_entry *v = &s->descriptors[n];
        if (n) jf(j, ",");
        jf(j, "{\"fd\":%d,\"type\":", v->fd); js(j, fd_type(v));
        jf(j, ",\"native_type\":%u,\"stat_rc\":%d,\"stat_errno\":%d,\"identity\":", v->native_type, v->stat_rc, v->stat_errno);
        if (!v->stat_rc) ji(j, &v->identity); else jf(j, "null");
        jf(j, ",\"matches_a\":%s,\"matches_b\":%s}",
            boolean(!v->stat_rc && same_identity(&v->identity, &e->a_identity)),
            boolean(!v->stat_rc && same_identity(&v->identity, &e->b_identity)));
    }
    jf(j, "]");
    if (!s->complete) jf(j, ",\"reason\":\"descriptor_inventory_incomplete\"");
    jf(j, "}");
}
static void j_process(struct json *j, pid_t pid) {
    struct proc_bsdinfo info = {0};
    errno = 0;
    int rc = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &info, sizeof(info)); int saved = errno;
    char path[PROC_PIDPATHINFO_MAXSIZE] = {0};
    errno = 0;
    int path_rc = proc_pidpath(pid, path, sizeof(path)); int path_errno = errno;
    struct stat s; struct identity executable_identity = {0};
    errno = 0;
    int stat_rc = path_rc > 0 ? stat(path, &s) : -1; int stat_errno = errno;
    if (!stat_rc) identify(&executable_identity, &s);
    jf(j, "{\"pid\":%d,\"identity_rc\":%d,\"identity_errno\":%d,\"ppid\":%u,\"pgid\":%u,"
        "\"uid\":%u,\"euid\":%u,\"gid\":%u,\"egid\":%u,\"start_identity\":",
        pid, rc, saved, info.pbi_ppid, info.pbi_pgid, info.pbi_ruid, info.pbi_uid, info.pbi_rgid, info.pbi_gid);
    if (rc == (int)sizeof(info)) jf(j, "{\"seconds\":%" PRIu64 ",\"microseconds\":%" PRIu64 "}",
        (uint64_t)info.pbi_start_tvsec, (uint64_t)info.pbi_start_tvusec);
    else jf(j, "null");
    jf(j, ",\"executable_path\":"); js(j, path_rc > 0 ? path : NULL);
    jf(j, ",\"executable_rc\":%d,\"executable_errno\":%d,\"executable_stat_rc\":%d,\"executable_stat_errno\":%d,\"executable_identity\":",
        path_rc, path_errno, stat_rc, stat_errno);
    if (!stat_rc) ji(j, &executable_identity); else jf(j, "null");
    jf(j, "}");
}
static int write_bytes(const char *bytes, size_t length) {
    while (length) {
        ssize_t n = write(STDOUT_FILENO, bytes, length);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        bytes += n; length -= (size_t)n;
    }
    return 0;
}
static void emit(const char *role, pid_t pid, const char *stage, const char *status,
                 uint64_t when, unsigned producer_seq, const char *details) {
    if (output_failed) return;
    char prefix[512];
    int n = snprintf(prefix, sizeof(prefix), "{\"schema_version\":1,\"seq\":%" PRIu64
        ",\"role\":\"%s\",\"pid\":%d,\"stage\":\"%s\",\"status\":\"%s\",\"monotonic_ns\":%" PRIu64,
        ++global_sequence, role, pid, stage, status, when);
    if (n < 0 || (size_t)n >= sizeof(prefix) || write_bytes(prefix, (size_t)n)) { output_failed = true; return; }
    if (producer_seq) {
        n = snprintf(prefix, sizeof(prefix), ",\"producer_seq\":%u", producer_seq);
        if (n < 0 || write_bytes(prefix, (size_t)n)) { output_failed = true; return; }
    }
    if (write_bytes(",\"details\":", 11) || write_bytes(details, strlen(details)) || write_bytes("}\n", 2)) output_failed = true;
}
static void supervisor_event(const char *stage, const char *status, struct json *j) {
    emit("supervisor", getpid(), j->failed ? "serialization_failure" : stage,
         j->failed ? "interrupted" : status, monotonic_ns(), 0,
         j->failed ? "{\"reason\":\"fixed_event_capacity_exceeded\"}" : j->bytes);
}
static bool publish(struct shared *e, unsigned role, const char *stage,
                    const char *status, struct json *j, bool wait_ack) {
    struct role_state *state = &e->role[role];
    unsigned n = atomic_load_explicit(&state->published, memory_order_relaxed);
    if (n >= EVENT_COUNT || j->failed) return false;
    struct event *v = &state->events[n];
    v->when = monotonic_ns();
    (void)snprintf(v->stage, sizeof(v->stage), "%s", stage);
    (void)snprintf(v->status, sizeof(v->status), "%s", status);
    memcpy(v->details, j->bytes, j->used + 1);
    atomic_store_explicit(&state->published, n + 1, memory_order_release);
    if (!wait_ack) return true;
    while (atomic_load_explicit(&state->acknowledged, memory_order_acquire) < n + 1) {
        if (monotonic_ns() >= e->deadline) return false;
        brief_pause();
    }
    return true;
}
static bool unavailable(struct shared *e, unsigned role, const char *stage,
                        const char *reason, const char *boundary) {
    struct json j = {0}; jf(&j, "{\"reason\":"); js(&j, reason);
    if (boundary) { jf(&j, ",\"boundary\":"); js(&j, boundary); }
    jf(&j, "}"); return publish(e, role, stage, "unavailable", &j, true);
}
static bool wait_gate(const struct shared *e, const _Atomic unsigned *gate) {
    while (!atomic_load_explicit(gate, memory_order_acquire)) {
        if (monotonic_ns() >= e->deadline) return false;
        brief_pause();
    }
    return true;
}
static void lookup_json(struct json *j, const void *address) {
    Dl_info info = {0};
    int rc = address ? dladdr(address, &info) : 0;
    jf(j, "{\"available\":%s,\"dladdr_rc\":%d,\"image\":", boolean(address != NULL), rc);
    js(j, rc ? info.dli_fname : NULL); jf(j, "}");
}
static void loaded_images(struct json *j) {
    uint32_t count = _dyld_image_count();
    jf(j, "{\"loaded_images\":[");
    for (uint32_t n = 0; n < count; n++) {
        if (n) jf(j, ","); js(j, _dyld_get_image_name(n));
    }
    jf(j, "],\"count\":%u}", count);
}
static void j_environment(struct json *j) {
    jf(j, "[");
    for (size_t n = 0; environ && environ[n]; n++) {
        if (n) jf(j, ",");
        js(j, environ[n]);
    }
    jf(j, "]");
}

static bool child_snapshot(struct shared *e, unsigned role, const char *boundary,
                           const struct fd_snapshot *already) {
    struct fd_snapshot s;
    if (!already) { snapshot(&s); already = &s; }
    struct json j = {0}; j_snapshot(&j, boundary, already, e);
    return publish(e, role, "fd_snapshot", "attempted", &j, true);
}
static bool child_read(struct shared *e, unsigned role, const char *stage, bool applied) {
    const char *boundary = !strcmp(stage, "read_before") ? "before_read_before" : "before_read_after";
    if (!applied) {
        return unavailable(e, role, "fd_snapshot", "recipient_application_unavailable", boundary) &&
            unavailable(e, role, stage, "recipient_application_unavailable", NULL);
    }
    if (!child_snapshot(e, role, boundary, NULL)) return false;
    struct access_observation a;
    access_file(e->a, &a);
    struct json j = {0}; ja(&j, e->a, &a);
    return publish(e, role, stage, "attempted", &j, true);
}
static bool token_valid(const struct token_channel *token, bool *header, bool *length,
                        bool *terminator, bool *embedded) {
    *header = token->magic == TOKEN_MAGIC;
    *length = token->length > 0 && token->length < TOKEN_CAP;
    *terminator = *length && token->bytes[token->length] == 0;
    *embedded = *length && memchr(token->bytes, 0, token->length) == NULL;
    return *header && *length && *terminator && *embedded;
}
static int child_main(unsigned role) {
    /* These fixed local observations precede mappings, descriptor closure,
     * symbol resolution, policy compilation, and all target operations. */
    struct fd_snapshot entry;
    snapshot(&entry);
    const struct rlimit core_limit = {0, 0};
    errno = 0; int core_rc = setrlimit(RLIMIT_CORE, &core_limit); int core_errno = errno;
    errno = 0;
    struct shared *e = mmap(NULL, sizeof(*e), PROT_READ | PROT_WRITE, MAP_SHARED, 3, 0);
    int evidence_map_errno = errno;
    errno = 0; int evidence_close = close(3); int evidence_close_errno = errno;
    if (e == MAP_FAILED) return 91;
    errno = 0;
    struct token_channel *token = mmap(NULL, sizeof(*token), PROT_READ | PROT_WRITE, MAP_SHARED, 4, 0);
    int token_map_errno = errno;
    errno = 0; int token_close = close(4); int token_close_errno = errno;
    bool mapped = token != MAP_FAILED;
    bool setup_ok = mapped && core_rc == 0 && evidence_close == 0 && token_close == 0;
    bool ordinary_finish = false;
    char *raw = NULL;
    struct json j = {0};
    jf(&j, "{\"process\":"); j_process(&j, getpid());
    jf(&j, ",\"core_limit\":{\"rc\":%d,\"errno\":%d},\"environment\":", core_rc, core_errno);
    j_environment(&j); jf(&j, "}");
    if (!publish(e, role, "process_entry", "attempted", &j, true)) goto cleanup;
    if (!child_snapshot(e, role, "entry", &entry)) goto cleanup;
    j = (struct json){0};
    jf(&j, "{\"evidence\":{\"descriptor\":3,\"map_succeeded\":true,\"map_errno\":%d,\"close\":{\"rc\":%d,\"errno\":%d}},"
        "\"token\":{\"descriptor\":4,\"map_succeeded\":%s,\"map_errno\":%d,\"close\":{\"rc\":%d,\"errno\":%d}},\"initial_token_zero\":%s}",
        evidence_map_errno, evidence_close, evidence_close_errno, boolean(mapped), token_map_errno,
        token_close, token_close_errno, boolean(mapped && all_zero(token, sizeof(*token))));
    if (!publish(e, role, "channel_mapped", "attempted", &j, true)) goto cleanup;

    void *library = dlopen("/usr/lib/libsandbox.dylib", RTLD_NOW | RTLD_LOCAL);
    void *issue_symbol = library && role == 0 ? dlsym(library, "sandbox_extension_issue_file") : NULL;
    void *consume_symbol = library && role == 1 ? dlsym(library, "sandbox_extension_consume") : NULL;
    void *compile_symbol = library ? dlsym(library, "sandbox_compile_string") : NULL;
    void *apply_symbol = library ? dlsym(library, "sandbox_apply") : NULL;
    issue_fn issue = (issue_fn)issue_symbol;
    consume_fn consume = (consume_fn)consume_symbol;
    compile_fn compile = (compile_fn)compile_symbol;
    apply_fn apply = (apply_fn)apply_symbol;
    j = (struct json){0}; jf(&j, "{\"library_opened\":%s,\"requested_library\":\"/usr/lib/libsandbox.dylib\",\"issue\":", boolean(library != NULL));
    if (role == 0) lookup_json(&j, issue_symbol); else jf(&j, "{\"status\":\"omitted\",\"reason\":\"recipient_role\"}");
    jf(&j, ",\"consume\":");
    if (role == 1) lookup_json(&j, consume_symbol); else jf(&j, "{\"status\":\"omitted\",\"reason\":\"issuer_role\"}");
    jf(&j, ",\"compile\":"); lookup_json(&j, compile_symbol);
    jf(&j, ",\"apply\":"); lookup_json(&j, apply_symbol); jf(&j, "}");
    if (!publish(e, role, "symbols", "attempted", &j, true)) goto cleanup;
    j = (struct json){0}; loaded_images(&j);
    if (!publish(e, role, "images", "attempted", &j, true)) goto cleanup;
    const char *policy = role == 0 ? e->issuer_policy : e->recipient_policy;
    bool symbols_ok = compile && apply && (role == 0 ? issue != NULL : consume != NULL);
    void *profile = NULL;
    if (setup_ok && symbols_ok) {
        char *error = NULL; errno = 0;
        profile = compile(policy, NULL, &error); int saved = errno;
        /* Native diagnostic/allocation contents are deliberately not retained. */
        (void)error;
        j = (struct json){0}; jf(&j, "{\"policy\":"); js(&j, policy);
        jf(&j, ",\"nonnull\":%s,\"errno\":%d}", boolean(profile != NULL), saved);
        if (!publish(e, role, "policy_compile", "attempted", &j, true)) goto cleanup;
    } else {
        j = (struct json){0}; jf(&j, "{\"policy\":"); js(&j, policy);
        jf(&j, ",\"reason\":\"%s\"}", setup_ok ? "required_symbol_unavailable" : "child_setup_failed");
        if (!publish(e, role, "policy_compile", "unavailable", &j, true)) goto cleanup;
    }
    bool applied = false;
    if (profile) {
        if (!child_snapshot(e, role, "before_apply", NULL)) goto cleanup;
        j = (struct json){0};
        if (role == 0 && !strcmp(e->arrangement, "C0")) {
            applied = true;
            jf(&j, "{\"reason\":\"C0_ordinary_authority_baseline\",\"application_count\":0}");
            if (!publish(e, role, "apply", "omitted", &j, true)) goto cleanup;
        } else {
            errno = 0; int rc = apply(profile); int saved = errno;
            applied = rc == 0;
            jf(&j, "{\"rc\":%d,\"errno\":%d,\"application_count\":1}", rc, saved);
            if (!publish(e, role, "apply", "attempted", &j, true)) goto cleanup;
        }
    } else {
        if (!unavailable(e, role, "fd_snapshot", "compiled_policy_unavailable", "before_apply")) goto cleanup;
        j = (struct json){0}; jf(&j, "{\"reason\":\"compiled_policy_unavailable\",\"application_count\":0}");
        if (!publish(e, role, "apply", "unavailable", &j, true)) goto cleanup;
    }
    atomic_store_explicit(&e->role[role].application_ok, applied ? 1u : 0u, memory_order_release);
    if (role == 0) {
        atomic_store_explicit(&e->role[role].ready, 1, memory_order_release);
        if (!wait_gate(e, &e->issue_release)) goto cleanup;
        if (applied) {
            if (!child_snapshot(e, role, "before_issue", NULL)) goto cleanup;
            j = (struct json){0};
            jf(&j, "{\"call_boundary_published\":true,\"extension_class\":"); js(&j, extension_class);
            jf(&j, ",\"path\":"); js(&j, e->a); jf(&j, ",\"flags\":0}");
            if (!publish(e, role, "issue_begin", "attempted", &j, true)) goto cleanup;
            errno = 0; raw = issue(extension_class, e->a, 0); int saved = errno;
            j = (struct json){0}; jf(&j, "{\"nonnull\":%s,\"errno\":%d}", boolean(raw != NULL), saved);
            if (!publish(e, role, "issue_result", "attempted", &j, true)) goto cleanup;
            bool bounded = false; size_t length = 0;
            if (raw) {
                length = strnlen(raw, TOKEN_CAP);
                bounded = length > 0 && length < TOKEN_CAP;
                if (bounded) { memcpy(token->bytes, raw, length + 1); token->length = (uint32_t)length; token->magic = TOKEN_MAGIC; }
                size_t erased = length < TOKEN_CAP ? length + 1 : length;
                erase(raw, erased); bool zero = all_zero(raw, erased); free(raw); raw = NULL;
                j = (struct json){0};
                jf(&j, "{\"inspected_bytes\":%zu,\"erased_bytes\":%zu,\"zero_confirmed\":%s,\"allocation_extent_observed\":false,\"terminator_within_bound\":%s}",
                    erased, erased, boolean(zero), boolean(length < TOKEN_CAP));
                if (!publish(e, role, "raw_token_erasure", "attempted", &j, true)) goto cleanup;
            } else {
                j = (struct json){0}; jf(&j, "{\"reason\":\"native_issue_null\"}");
                if (!publish(e, role, "raw_token_erasure", "omitted", &j, true)) goto cleanup;
            }
            j = (struct json){0};
            jf(&j, "{\"published\":%s,\"length\":%zu,\"length_valid\":%s,\"terminator_valid\":%s,\"embedded_nul_absent\":%s",
                boolean(bounded), length, boolean(bounded), boolean(bounded), boolean(bounded));
            if (!bounded) jf(&j, ",\"reason\":\"%s\"", length ? "native_token_exceeds_bound" : "native_token_absent_or_empty");
            jf(&j, "}");
            if (!publish(e, role, "token_publication", bounded ? "attempted" : "unavailable", &j, true)) goto cleanup;
            atomic_store_explicit(&e->issue_ready, bounded ? 1u : 2u, memory_order_release);
        } else {
            if (!unavailable(e, role, "fd_snapshot", "issuer_application_unavailable", "before_issue") ||
                !unavailable(e, role, "issue_begin", "issuer_application_unavailable", NULL) ||
                !unavailable(e, role, "issue_result", "issuer_application_unavailable", NULL) ||
                !unavailable(e, role, "raw_token_erasure", "issuance_unavailable", NULL) ||
                !unavailable(e, role, "token_publication", "issuance_unavailable", NULL)) goto cleanup;
            atomic_store_explicit(&e->issue_ready, 2, memory_order_release);
        }
        if (!wait_gate(e, &e->issuer_exit)) goto cleanup;
    } else {
        if (!child_read(e, role, "read_before", applied)) goto cleanup;
        atomic_store_explicit(&e->role[role].ready, 1, memory_order_release);
        if (!wait_gate(e, &e->transfer_release)) goto cleanup;
        bool accepted = false;
        if (mapped && atomic_load_explicit(&e->delivery_ready, memory_order_acquire) == 1) {
            bool header, length, terminator, embedded;
            accepted = token_valid(token, &header, &length, &terminator, &embedded);
            j = (struct json){0};
            jf(&j, "{\"accepted\":%s,\"length\":%u,\"header_valid\":%s,\"length_valid\":%s,\"terminator_valid\":%s,\"embedded_nul_absent\":%s}",
                boolean(accepted), token->length, boolean(header), boolean(length), boolean(terminator), boolean(embedded));
            if (!publish(e, role, "transfer_acceptance", "attempted", &j, true)) goto cleanup;
        } else {
            if (!unavailable(e, role, "transfer_acceptance", mapped ? "token_delivery_unavailable" : "token_mapping_unavailable", NULL)) goto cleanup;
        }
        atomic_store_explicit(&e->role[role].accepted, accepted ? 1u : 2u, memory_order_release);
        if (!wait_gate(e, &e->consume_release)) goto cleanup;
        if (!strcmp(e->arrangement, "C6")) {
            j = (struct json){0}; jf(&j, "{\"reason\":\"C6_consumption_omitted\"}");
            if (!publish(e, role, "consume_begin", "omitted", &j, true) ||
                !publish(e, role, "consume_result", "omitted", &j, true)) goto cleanup;
        } else if (applied && accepted && consume && atomic_load_explicit(&e->consume_permitted, memory_order_acquire) == 1) {
            j = (struct json){0}; jf(&j, "{\"call_boundary_published\":true}");
            if (!publish(e, role, "consume_begin", "attempted", &j, true)) goto cleanup;
            errno = 0; int64_t rc = consume((const char *)token->bytes); int saved = errno;
            j = (struct json){0}; jf(&j, "{\"rc\":%" PRId64 ",\"errno\":%d,\"return_bits\":64}", rc, saved);
            if (!publish(e, role, "consume_result", "attempted", &j, true)) goto cleanup;
        } else {
            const char *reason = !applied ? "recipient_application_unavailable" : !accepted ? "transfer_not_accepted" :
                !consume ? "consume_symbol_unavailable" : "transfer_equality_unavailable";
            if (!unavailable(e, role, "consume_begin", reason, NULL) || !unavailable(e, role, "consume_result", reason, NULL)) goto cleanup;
        }
        if (!child_read(e, role, "read_after", applied)) goto cleanup;
    }
    ordinary_finish = true;
cleanup:
    if (raw) {
        size_t n = strnlen(raw, TOKEN_CAP);
        erase(raw, n < TOKEN_CAP ? n + 1 : n); free(raw); raw = NULL;
    }
    j = (struct json){0};
    if (mapped) {
        erase(token, sizeof(*token));
        jf(&j, "{\"buffer\":\"%s\",\"capacity\":%u,\"zero_confirmed\":%s}",
            role == 0 ? "issued" : "delivered", (unsigned)sizeof(*token), boolean(all_zero(token, sizeof(*token))));
        (void)publish(e, role, "token_erasure", "attempted", &j, ordinary_finish);
    } else {
        jf(&j, "{\"reason\":\"mapping_unavailable\"}");
        (void)publish(e, role, "token_erasure", "unavailable", &j, ordinary_finish);
    }
    j = (struct json){0}; jf(&j, "{\"exit_code\":%d,\"ordinary_finish\":%s}", ordinary_finish ? 0 : 96, boolean(ordinary_finish));
    (void)publish(e, role, "child_exit", "attempted", &j, ordinary_finish);
    atomic_store_explicit(&e->role[role].completed, 1, memory_order_release);
    if (mapped) (void)munmap(token, sizeof(*token));
    (void)munmap(e, sizeof(*e));
    return ordinary_finish ? 0 : 96;
}

struct child {
    pid_t pid;
    unsigned collected;
    bool launched, reaped;
    int wait_status;
    uint64_t start_seconds, start_microseconds;
    bool start_known;
};
static int shared_region(const char *label, size_t size, void **mapped) {
    char name[80];
    (void)snprintf(name, sizeof(name), "/pw-browser-%d-%08x", getpid(), arc4random());
    errno = 0;
    int fd = shm_open(name, O_RDWR | O_CREAT | O_EXCL, 0600); int open_errno = errno;
    if (fd < 0) {
        struct json j = {0}; jf(&j, "{\"channel\":"); js(&j, label);
        jf(&j, ",\"operation\":\"shm_open\",\"rc\":%d,\"errno\":%d,\"cleanup_pending\":false}", fd, open_errno);
        supervisor_event("channel_resource", "attempted", &j); return -1;
    }
    errno = 0; int unlink_rc = shm_unlink(name); int unlink_errno = errno;
    struct json j = {0}; jf(&j, "{\"channel\":"); js(&j, label);
    jf(&j, ",\"name\":"); js(&j, name);
    jf(&j, ",\"owner_pid\":%d,\"created_exclusively\":true,\"descriptor\":%d,\"unlink_rc\":%d,\"unlink_errno\":%d,\"cleanup_pending\":%s}",
        getpid(), fd, unlink_rc, unlink_errno, boolean(unlink_rc != 0));
    supervisor_event("channel_resource", "attempted", &j);
    if (unlink_rc) { channel_cleanup_pending = true; close(fd); return -1; }
    errno = 0; int resize_rc = ftruncate(fd, (off_t)size); int resize_errno = errno;
    void *p = MAP_FAILED; int map_errno = 0;
    if (!resize_rc) {
        errno = 0; p = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); map_errno = errno;
    }
    int transport = -1, duplicate_errno = 0;
    if (p != MAP_FAILED) {
        memset(p, 0, size);
        errno = 0; transport = fcntl(fd, F_DUPFD_CLOEXEC, 64); duplicate_errno = errno;
    }
    errno = 0; int close_rc = close(fd); int close_errno = errno;
    j = (struct json){0}; jf(&j, "{\"channel\":"); js(&j, label);
    jf(&j, ",\"preparation\":{\"ftruncate\":{\"status\":\"attempted\",\"rc\":%d,\"errno\":%d},\"mmap\":", resize_rc, resize_errno);
    if (!resize_rc) jf(&j, "{\"status\":\"attempted\",\"succeeded\":%s,\"errno\":%d}", boolean(p != MAP_FAILED), map_errno);
    else jf(&j, "{\"status\":\"unavailable\",\"reason\":\"ftruncate_failed\"}");
    jf(&j, ",\"duplicate\":");
    if (p != MAP_FAILED) jf(&j, "{\"status\":\"attempted\",\"rc\":%d,\"errno\":%d}", transport, duplicate_errno);
    else jf(&j, "{\"status\":\"unavailable\",\"reason\":\"mapping_unavailable\"}");
    jf(&j, ",\"close\":{\"status\":\"attempted\",\"rc\":%d,\"errno\":%d}},\"cleanup_pending\":false}", close_rc, close_errno);
    supervisor_event("channel_preparation", "attempted", &j);
    if (p == MAP_FAILED || transport < 0 || close_rc) {
        if (transport >= 0) close(transport);
        if (p != MAP_FAILED) munmap(p, size);
        return -1;
    }
    *mapped = p;
    return transport;
}
static void j_channel(struct json *j, int fd, size_t size) {
    struct stat s; struct identity i = {0};
    errno = 0; int rc = fstat(fd, &s); int saved = errno;
    if (!rc) identify(&i, &s);
    jf(j, "{\"descriptor\":%d,\"size\":%zu,\"identity_rc\":%d,\"identity_errno\":%d,\"identity\":", fd, size, rc, saved);
    if (!rc) ji(j, &i); else jf(j, "null");
    jf(j, "}");
}
static int parse_locks(const char *value, int fds[LOCK_CAP], size_t *count) {
    *count = 0;
    if (!value || !*value) return 0;
    const char *p = value;
    while (*p) {
        char *end = NULL; errno = 0;
        long fd = strtol(p, &end, 10);
        if (errno || end == p || fd < 0 || fd > INT_MAX || *count == LOCK_CAP || (*end && *end != ',')) return -1;
        if (fcntl((int)fd, F_GETFD) < 0) return -1;
        /* Relocate apparatus lifetime descriptors before reserving 3/4. */
        int duplicate = fcntl((int)fd, F_DUPFD_CLOEXEC, 128);
        if (duplicate < 0) return -1;
        fds[(*count)++] = duplicate;
        p = *end ? end + 1 : end;
        if (*end && !*p) return -1;
    }
    return 0;
}
static int spawn_role(const char *executable, unsigned role, int evidence_fd,
                      int token_fd, const int *locks, size_t lock_count, pid_t *pid) {
    posix_spawn_file_actions_t actions;
    posix_spawnattr_t attributes;
    int rc = posix_spawn_file_actions_init(&actions);
    if (rc) return rc;
    rc = posix_spawnattr_init(&attributes);
    if (rc) { posix_spawn_file_actions_destroy(&actions); return rc; }
    rc = posix_spawnattr_setflags(&attributes, POSIX_SPAWN_CLOEXEC_DEFAULT);
    if (!rc) rc = posix_spawn_file_actions_adddup2(&actions, evidence_fd, 3);
    if (!rc) rc = posix_spawn_file_actions_adddup2(&actions, token_fd, 4);
    for (size_t n = 0; !rc && n < lock_count; n++)
        rc = posix_spawn_file_actions_adddup2(&actions, locks[n], 32 + (int)n);
    for (int n = 0; !rc && n < 3; n++)
        rc = posix_spawn_file_actions_addopen(&actions, n, "/dev/null", n ? O_WRONLY : O_RDONLY, 0);
    if (!rc) {
        char *argv[] = {(char *)executable, role == 0 ? "issuer" : "recipient", NULL};
        char *environment[] = {"PATH=/usr/bin:/bin", "LC_ALL=C", NULL};
        rc = posix_spawn(pid, executable, &actions, &attributes, argv, environment);
    }
    posix_spawnattr_destroy(&attributes);
    posix_spawn_file_actions_destroy(&actions);
    return rc;
}
static bool drain(struct shared *e, struct child children[2]) {
    bool any = false;
    for (unsigned role = 0; role < 2; role++) {
        struct role_state *state = &e->role[role];
        unsigned count = atomic_load_explicit(&state->published, memory_order_acquire);
        if (count > EVENT_COUNT) { output_failed = true; return any; }
        while (children[role].collected < count) {
            unsigned n = children[role].collected;
            const struct event *v = &state->events[n];
            emit(role_names[role], children[role].pid, v->stage, v->status, v->when, n + 1, v->details);
            struct json j = {0};
            jf(&j, "{\"child_role\":\"%s\",\"child_pid\":%d,\"producer_seq\":%u,\"acknowledged_stage\":\"%s\"}",
                role_names[role], children[role].pid, n + 1, v->stage);
            supervisor_event("publication_ack", "attempted", &j);
            children[role].collected++;
            /* An acknowledgement follows successful pipe publication, never just
             * inspection of a producer's in-memory result. */
            if (!output_failed) atomic_store_explicit(&state->acknowledged, n + 1, memory_order_release);
            any = true;
        }
    }
    return any;
}
static int poll_child(unsigned role, struct child *child, bool report_pending) {
    if (!child->launched || child->reaped) return 0;
    int status = 0; errno = 0;
    pid_t rc = waitpid(child->pid, &status, WNOHANG); int saved = errno;
    if (rc == child->pid) { child->reaped = true; child->wait_status = status; }
    if (rc != 0 || report_pending) {
        struct json j = {0};
        jf(&j, "{\"child_role\":\"%s\",\"child_pid\":%d,\"rc\":%d,\"errno\":%d,\"wait_status\":",
            role_names[role], child->pid, rc, saved);
        if (rc == child->pid) jf(&j, "%d", status); else jf(&j, "null");
        jf(&j, ",\"reaped\":%s,\"exit_code\":", boolean(child->reaped));
        if (rc == child->pid && WIFEXITED(status)) jf(&j, "%d", WEXITSTATUS(status)); else jf(&j, "null");
        jf(&j, ",\"term_signal\":");
        if (rc == child->pid && WIFSIGNALED(status)) jf(&j, "%d", WTERMSIG(status)); else jf(&j, "null");
        jf(&j, "}"); supervisor_event("child_reap", "attempted", &j);
    }
    return rc < 0 && saved != EINTR ? -1 : 0;
}
static bool await_flag(struct shared *e, struct child children[2],
                       const _Atomic unsigned *flag, const char **failure) {
    while (!atomic_load_explicit(flag, memory_order_acquire)) {
        (void)drain(e, children);
        if (atomic_load_explicit(flag, memory_order_acquire)) return !output_failed;
        for (unsigned role = 0; role < 2; role++) {
            if (poll_child(role, &children[role], false)) { *failure = "child_wait_failed"; return false; }
            if (children[role].reaped && !atomic_load_explicit(flag, memory_order_acquire)) {
                *failure = "child_exited_before_required_publication"; return false;
            }
        }
        if (output_failed) { *failure = "event_output_failed"; return false; }
        if (monotonic_ns() >= e->deadline) { *failure = "execution_deadline"; return false; }
        brief_pause();
    }
    (void)drain(e, children);
    return !output_failed;
}
static bool sbpl_escape(const char *path, char *escaped, size_t capacity) {
    size_t n = 0;
    for (const unsigned char *p = (const unsigned char *)path; *p; p++) {
        if (*p < 32 || *p >= 127) return false;
        if (*p == '\\' || *p == '"') { if (n + 1 >= capacity) return false; escaped[n++] = '\\'; }
        if (n + 1 >= capacity) return false;
        escaped[n++] = (char)*p;
    }
    escaped[n] = 0; return true;
}
static bool policies(struct shared *e) {
    const char *prefix = "(version 1)\n(allow default)\n(deny file-write*)\n(deny file-issue-extension)\n";
    char path[PATH_MAX * 2u];
    if (!sbpl_escape(!strcmp(e->arrangement, "C5") ? e->b : e->a, path, sizeof(path))) return false;
    int n;
    if (!strcmp(e->arrangement, "C0") || !strcmp(e->arrangement, "C1"))
        n = snprintf(e->issuer_policy, sizeof(e->issuer_policy), "%s(allow file-issue-extension)\n", prefix);
    else if (!strcmp(e->arrangement, "C3")) n = snprintf(e->issuer_policy, sizeof(e->issuer_policy), "%s", prefix);
    else n = snprintf(e->issuer_policy, sizeof(e->issuer_policy),
        "%s(allow file-issue-extension\n  (require-all\n    (extension-class \"%s\")\n    (literal \"%s\")))\n",
        prefix, !strcmp(e->arrangement, "C4") ? "com.apple.app-sandbox.read-write" : extension_class, path);
    if (n < 0 || (size_t)n >= sizeof(e->issuer_policy)) return false;
    n = snprintf(e->recipient_policy, sizeof(e->recipient_policy),
        "(version 1)\n(allow default)\n(deny file-read-data)\n%s",
        !strcmp(e->arrangement, "C7") ? "" : "(allow file-read-data (extension \"com.apple.app-sandbox.read\"))\n");
    return n >= 0 && (size_t)n < sizeof(e->recipient_policy);
}
struct target_creation { struct call open, write, close; };
static bool create_target(const char *path, const char *content, struct target_creation *out) {
    memset(out, 0, sizeof(*out));
    out->open.attempted = true; errno = 0;
    int fd = open(path, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0600); int saved = errno;
    out->open.rc = fd; out->open.error = saved;
    if (fd < 0) return false;
    out->write.attempted = true; errno = 0;
    ssize_t n = write(fd, content, strlen(content)); saved = errno;
    out->write.rc = n; out->write.error = saved;
    out->close.attempted = true; errno = 0;
    int rc = close(fd); saved = errno;
    out->close.rc = rc; out->close.error = saved;
    return n == (ssize_t)strlen(content) && rc == 0;
}
static void j_target(struct json *j, const char *path, const char *content,
                     const struct access_observation *baseline, const struct target_creation *creation) {
    jf(j, "{\"path\":"); js(j, path);
    jf(j, ",\"identity\":");
    if (baseline->identity_check.attempted && !baseline->identity_check.rc) ji(j, &baseline->identity); else jf(j, "null");
    jf(j, ",\"known_content_hex\":"); hex(j, (const unsigned char *)content, strlen(content));
    jf(j, ",\"creation\":{\"open\":"); jc(j, &creation->open, "not_started");
    jf(j, ",\"write\":"); jc(j, &creation->write, "open_failed");
    jf(j, ",\"close\":"); jc(j, &creation->close, "open_failed");
    jf(j, "},\"baseline\":"); ja(j, path, baseline); jf(j, "}");
}
static bool baseline_ok(const struct access_observation *a, const char *content) {
    return a->open.attempted && a->open.rc >= 0 && a->identity_check.attempted && !a->identity_check.rc &&
        S_ISREG((mode_t)a->identity.mode) && a->read.attempted && a->read.rc == (int64_t)strlen(content) &&
        !memcmp(a->bytes, content, strlen(content)) && a->close.attempted && !a->close.rc;
}

static void remember_start(struct child *c) {
    struct proc_bsdinfo info = {0};
    int rc = proc_pidinfo(c->pid, PROC_PIDTBSDINFO, 0, &info, sizeof(info));
    c->start_known = rc == (int)sizeof(info);
    if (c->start_known) { c->start_seconds = info.pbi_start_tvsec; c->start_microseconds = info.pbi_start_tvusec; }
}
static bool current_owned_child(const struct child *c) {
    struct proc_bsdinfo info = {0};
    int rc = proc_pidinfo(c->pid, PROC_PIDTBSDINFO, 0, &info, sizeof(info));
    if (rc != (int)sizeof(info)) return false;
    /* An unreaped direct child's PID cannot be reused. If its start identity
     * was obtainable at launch, require the same identity as well. */
    return info.pbi_ppid == (uint32_t)getpid() && info.pbi_pgid == (uint32_t)getpgrp() &&
        (!c->start_known || (c->start_seconds == info.pbi_start_tvsec && c->start_microseconds == info.pbi_start_tvusec));
}
static void cleanup_child(struct shared *e, struct child children[2], unsigned role) {
    struct child *c = &children[role];
    if (!c->launched || c->reaped) return;
    (void)poll_child(role, c, false);
    if (c->reaped) return;
    uint64_t deadline = monotonic_ns() + 2 * NS_PER_SECOND;
    bool owned = current_owned_child(c);
    struct json j = {0};
    if (owned) {
        errno = 0; int rc = kill(c->pid, SIGKILL); int saved = errno;
        jf(&j, "{\"child_role\":\"%s\",\"child_pid\":%d,\"signal\":%d,\"rc\":%d,\"errno\":%d,\"ownership_revalidated\":true}",
            role_names[role], c->pid, SIGKILL, rc, saved);
        supervisor_event("child_signal", "attempted", &j);
    } else {
        jf(&j, "{\"child_role\":\"%s\",\"child_pid\":%d,\"signal\":%d,\"reason\":\"current_child_ownership_unconfirmed\"}",
            role_names[role], c->pid, SIGKILL);
        supervisor_event("child_signal", "unavailable", &j);
    }
    while (!c->reaped && monotonic_ns() < deadline) {
        (void)drain(e, children);
        if (poll_child(role, c, false)) break;
        if (!c->reaped) brief_pause();
    }
    if (!c->reaped) (void)poll_child(role, c, true);
}
static void query_record(struct shared *e, pid_t issuer, check_fn check, const int *flag,
                         int filter, bool ready) {
    struct json j = {0};
    jf(&j, "{\"operation\":\"file-issue-extension\",\"caller_pid\":%d,\"target_pid\":%d,\"filter_id\":%d,\"filter_value\":",
        getpid(), issuer, filter);
    js(&j, filter == 1 ? e->a : NULL);
    if (flag) jf(&j, ",\"no_report_flag\":%d,\"type_argument\":%d", *flag, filter | *flag);
    else jf(&j, ",\"no_report_flag\":null,\"type_argument\":null");
    bool available = check && flag && ready;
    if (available) {
        errno = 0;
        int rc = filter == 0 ? check(issuer, "file-issue-extension", *flag) :
            check(issuer, "file-issue-extension", filter | *flag, e->a);
        int saved = errno;
        jf(&j, ",\"rc\":%d,\"errno\":%d", rc, saved);
    } else jf(&j, ",\"reason\":\"%s\"", !ready ? "issuer_preparation_or_application_unavailable" : "query_api_or_flag_unavailable");
    jf(&j, "}"); supervisor_event("query", available ? "attempted" : "unavailable", &j);
}
static bool stage_published(const struct shared *e, unsigned role, const char *stage, const char *boundary) {
    unsigned count = atomic_load_explicit(&e->role[role].published, memory_order_acquire);
    if (count > EVENT_COUNT) count = EVENT_COUNT;
    char marker[96] = {0};
    if (boundary) (void)snprintf(marker, sizeof(marker), "\"boundary\":\"%s\"", boundary);
    for (unsigned n = 0; n < count; n++) {
        const struct event *v = &e->role[role].events[n];
        if (!strcmp(v->stage, stage) && (!boundary || strstr(v->details, marker))) return true;
    }
    return false;
}
static void interruptions(const struct shared *e, const struct child children[2]) {
    static const struct { const char *stage, *boundary; unsigned roles; } expected[] = {
        {"process_entry", NULL, 3}, {"fd_snapshot", "entry", 3}, {"channel_mapped", NULL, 3},
        {"symbols", NULL, 3}, {"images", NULL, 3}, {"policy_compile", NULL, 3},
        {"fd_snapshot", "before_apply", 3}, {"apply", NULL, 3},
        {"fd_snapshot", "before_issue", 1}, {"issue_begin", NULL, 1}, {"issue_result", NULL, 1},
        {"raw_token_erasure", NULL, 1}, {"token_publication", NULL, 1},
        {"fd_snapshot", "before_read_before", 2}, {"read_before", NULL, 2},
        {"transfer_acceptance", NULL, 2}, {"consume_begin", NULL, 2}, {"consume_result", NULL, 2},
        {"fd_snapshot", "before_read_after", 2}, {"read_after", NULL, 2},
        {"token_erasure", NULL, 3}, {"child_exit", NULL, 3}
    };
    struct json j = {0}; jf(&j, "{\"missing_publications\":["); bool first = true;
    for (unsigned role = 0; role < 2; role++) {
        for (size_t n = 0; n < sizeof(expected) / sizeof(expected[0]); n++) {
            if (!(expected[n].roles & (1u << role)) || stage_published(e, role, expected[n].stage, expected[n].boundary)) continue;
            if (!first) jf(&j, ","); first = false;
            jf(&j, "{\"role\":\"%s\",\"pid\":%d,\"stage\":", role_names[role], children[role].pid);
            js(&j, expected[n].stage);
            if (expected[n].boundary) { jf(&j, ",\"boundary\":"); js(&j, expected[n].boundary); }
            jf(&j, ",\"status\":\"%s\",\"reason\":\"%s\"",
                children[role].launched ? "interrupted" : "unavailable",
                children[role].launched ? "no_child_publication_before_termination" : "child_not_launched");
            if (!strcmp(expected[n].stage, "issue_result") || !strcmp(expected[n].stage, "consume_result"))
                jf(&j, ",\"call_boundary_published\":%s,\"native_return_observed\":false",
                    boolean(stage_published(e, role, role == 0 ? "issue_begin" : "consume_begin", NULL)));
            jf(&j, "}");
        }
    }
    jf(&j, "],\"source\":\"supervisor_inventory_of_unpublished_boundaries\"}");
    supervisor_event("interrupted_stages", "attempted", &j);
}
static int supervisor_main(const char *arrangement, const char *trial_id,
                           const char *trial_dir, const char *lock_csv) {
    struct json j = {0};
    const struct rlimit core_limit = {0, 0};
    errno = 0; int core_rc = setrlimit(RLIMIT_CORE, &core_limit); int core_errno = errno;
    (void)signal(SIGPIPE, SIG_IGN);
    jf(&j, "{\"trial_id\":"); js(&j, trial_id); jf(&j, ",\"arrangement\":"); js(&j, arrangement);
    jf(&j, ",\"process\":"); j_process(&j, getpid());
    jf(&j, ",\"core_limit\":{\"rc\":%d,\"errno\":%d},\"environment\":", core_rc, core_errno);
    j_environment(&j); jf(&j, "}");
    supervisor_event("supervisor_start", "attempted", &j);
    if (core_rc) return 89;

    int locks[LOCK_CAP] = {0}; size_t lock_count = 0;
    if (parse_locks(lock_csv, locks, &lock_count)) {
        j = (struct json){0}; jf(&j, "{\"reason\":\"invalid_inherited_lock_descriptors\"}");
        supervisor_event("equipment_failure", "attempted", &j); return 3;
    }
    struct shared *e = NULL;
    struct token_channel *issued = NULL, *delivered = NULL;
    int efd = shared_region("evidence", sizeof(*e), (void **)&e);
    int ifd = efd >= 0 ? shared_region("issued_token", sizeof(*issued), (void **)&issued) : -1;
    int dfd = ifd >= 0 ? shared_region("delivered_token", sizeof(*delivered), (void **)&delivered) : -1;
    if (efd < 0 || ifd < 0 || dfd < 0) {
        j = (struct json){0}; jf(&j, "{\"reason\":\"shared_channel_setup_failed\",\"cleanup_pending\":%s}", boolean(channel_cleanup_pending));
        supervisor_event("equipment_failure", "attempted", &j); return 3;
    }
    (void)snprintf(e->arrangement, sizeof(e->arrangement), "%s", arrangement);
    if (strlen(trial_id) >= sizeof(e->trial_id)) return 2;
    (void)snprintf(e->trial_id, sizeof(e->trial_id), "%s", trial_id);
    char executable[PATH_MAX], image[PATH_MAX]; uint32_t image_size = sizeof(image);
    if (_NSGetExecutablePath(image, &image_size) || !realpath(image, executable)) return 3;
    (void)snprintf(e->executable, sizeof(e->executable), "%s", executable);
    int a_len = snprintf(e->a, sizeof(e->a), "%s/A", trial_dir);
    int b_len = snprintf(e->b, sizeof(e->b), "%s/B", trial_dir);
    if (a_len < 0 || b_len < 0 || (size_t)a_len >= sizeof(e->a) || (size_t)b_len >= sizeof(e->b)) return 2;
    struct target_creation creation[2] = {0};
    bool created_a = create_target(e->a, a_content, &creation[0]);
    bool created_b = create_target(e->b, b_content, &creation[1]);
    char canonical[PATH_MAX];
    bool canonical_a = realpath(e->a, canonical) != NULL;
    if (canonical_a) (void)snprintf(e->a, sizeof(e->a), "%s", canonical);
    bool canonical_b = realpath(e->b, canonical) != NULL;
    if (canonical_b) (void)snprintf(e->b, sizeof(e->b), "%s", canonical);
    struct access_observation baseline[2];
    access_file(e->a, &baseline[0]); access_file(e->b, &baseline[1]);
    e->a_identity = baseline[0].identity; e->b_identity = baseline[1].identity;
    bool policy_ready = policies(e);
    bool targets_ok = created_a && created_b && canonical_a && canonical_b && policy_ready &&
        baseline_ok(&baseline[0], a_content) && baseline_ok(&baseline[1], b_content);
    j = (struct json){0}; jf(&j, "{\"a\":"); j_target(&j, e->a, a_content, &baseline[0], &creation[0]);
    jf(&j, ",\"b\":"); j_target(&j, e->b, b_content, &baseline[1], &creation[1]);
    jf(&j, ",\"issuer_policy\":"); js(&j, e->issuer_policy);
    jf(&j, ",\"recipient_policy\":"); js(&j, e->recipient_policy);
    jf(&j, ",\"extension_class\":"); js(&j, extension_class);
    jf(&j, ",\"flags\":0,\"canonical_a\":%s,\"canonical_b\":%s,\"preparation_ok\":%s}",
        boolean(canonical_a), boolean(canonical_b), boolean(targets_ok));
    supervisor_event("targets_prepared", "attempted", &j);
    j = (struct json){0}; jf(&j, "{\"evidence\":"); j_channel(&j, efd, sizeof(*e));
    jf(&j, ",\"issued_token\":"); j_channel(&j, ifd, sizeof(*issued));
    jf(&j, ",\"delivered_token\":"); j_channel(&j, dfd, sizeof(*delivered));
    jf(&j, ",\"issued_initial_zero\":%s,\"delivered_initial_zero\":%s,\"child_lock_descriptors\":[",
        boolean(all_zero(issued, sizeof(*issued))), boolean(all_zero(delivered, sizeof(*delivered))));
    for (size_t n = 0; n < lock_count; n++) { if (n) jf(&j, ","); jf(&j, "%d", 32 + (int)n); }
    jf(&j, "]}"); supervisor_event("channel_setup", "attempted", &j);
    void *query_library = dlopen("/usr/lib/libsandbox.dylib", RTLD_NOW | RTLD_LOCAL);
    void *query_symbol = query_library ? dlsym(query_library, "sandbox_check") : NULL;
    const int *no_report = query_library ? (const int *)dlsym(query_library, "SANDBOX_CHECK_NO_REPORT") : NULL;
    check_fn check = (check_fn)query_symbol;
    j = (struct json){0}; jf(&j, "{\"library_opened\":%s,\"requested_library\":\"/usr/lib/libsandbox.dylib\",\"api\":", boolean(query_library != NULL)); lookup_json(&j, query_symbol);
    jf(&j, ",\"flag\":"); lookup_json(&j, no_report);
    jf(&j, ",\"no_report_flag\":");
    if (no_report) jf(&j, "%d", *no_report); else jf(&j, "null");
    jf(&j, "}"); supervisor_event("query_capability", "attempted", &j);
    j = (struct json){0}; loaded_images(&j); supervisor_event("images", "attempted", &j);

    struct child children[2] = {0};
    const char *failure = targets_ok ? NULL : "target_or_policy_preparation_failed";
    bool deadline_reached = false;
    uint64_t began = monotonic_ns();
    e->deadline = began + 20 * NS_PER_SECOND;
    if (failure || output_failed) goto cleanup;
    /* No other operation intervenes between the shared deadline start and
     * these first spawn operations beyond the local failure check. */
    for (unsigned role = 0; role < 2; role++) {
        errno = 0;
        int rc = spawn_role(e->executable, role, efd, role == 0 ? ifd : dfd, locks, lock_count, &children[role].pid);
        int saved = errno;
        children[role].launched = rc == 0;
        if (!rc) remember_start(&children[role]);
        j = (struct json){0};
        jf(&j, "{\"child_role\":\"%s\",\"rc\":%d,\"errno\":%d,\"child_pid\":%d,\"process\":",
            role_names[role], rc, saved, children[role].pid);
        if (!rc) j_process(&j, children[role].pid); else jf(&j, "null");
        jf(&j, "}"); supervisor_event("child_launch", "attempted", &j);
        if (rc) { failure = "child_spawn_failed"; goto cleanup; }
    }
    /* Only apparatus descriptors were passed; all target descriptors closed
     * before either launch. Supervisor mapping descriptors are now expendable. */
    close(efd); efd = -1; close(ifd); ifd = -1; close(dfd); dfd = -1;
    if (!await_flag(e, children, &e->role[0].ready, &failure) ||
        !await_flag(e, children, &e->role[1].ready, &failure)) goto cleanup;
    bool issuer_ready = atomic_load_explicit(&e->role[0].application_ok, memory_order_acquire) == 1;
    query_record(e, children[0].pid, check, no_report, 0, issuer_ready);
    query_record(e, children[0].pid, check, no_report, 1, issuer_ready);
    j = (struct json){0};
    jf(&j, "{\"issuer_pid\":%d,\"recipient_pid\":%d,\"queries_collected\":2,\"issuer_ready\":true,\"recipient_ready\":true}", children[0].pid, children[1].pid);
    supervisor_event("issue_release", "attempted", &j);
    atomic_store_explicit(&e->issue_release, 1, memory_order_release);
    if (!await_flag(e, children, &e->issue_ready, &failure)) goto cleanup;
    bool header = false, length = false, terminator = false, embedded = false;
    bool ready = atomic_load_explicit(&e->issue_ready, memory_order_acquire) == 1 &&
        token_valid(issued, &header, &length, &terminator, &embedded);
    if (ready) {
        delivered->magic = issued->magic; delivered->length = issued->length;
        memcpy(delivered->bytes, issued->bytes, issued->length + 1);
    }
    unsigned publication = 0;
    for (unsigned n = 0; n < children[0].collected; n++)
        if (!strcmp(e->role[0].events[n].stage, "token_publication")) publication = n + 1;
    j = (struct json){0};
    jf(&j, "{\"ready\":%s,\"length\":%u,\"header_valid\":%s,\"length_valid\":%s,\"terminator_valid\":%s,"
        "\"embedded_nul_absent\":%s,\"issuer_publication_producer_seq\":%u",
        boolean(ready), issued->length, boolean(header), boolean(length), boolean(terminator), boolean(embedded), publication);
    if (!ready) jf(&j, ",\"reason\":\"bounded_token_publication_unavailable\"");
    jf(&j, "}"); supervisor_event("transfer_ready", ready ? "attempted" : "unavailable", &j);
    atomic_store_explicit(&e->delivery_ready, ready ? 1u : 2u, memory_order_release);
    atomic_store_explicit(&e->transfer_release, 1, memory_order_release);
    if (!await_flag(e, children, &e->role[1].accepted, &failure)) goto cleanup;
    bool accepted = atomic_load_explicit(&e->role[1].accepted, memory_order_acquire) == 1;
    bool equal = ready && accepted && delivered->length == issued->length &&
        memcmp(issued->bytes, delivered->bytes, issued->length + 1) == 0;
    j = (struct json){0};
    if (ready && accepted) jf(&j, "{\"equal\":%s,\"length\":%u,\"terminator_compared\":true}", boolean(equal), issued->length);
    else jf(&j, "{\"reason\":\"accepted_transfer_unavailable\"}");
    supervisor_event("transfer_equality", ready && accepted ? "attempted" : "unavailable", &j);
    j = (struct json){0};
    jf(&j, "{\"recipient_pid\":%d,\"accepted\":%s,\"equality_confirmed\":%s}", children[1].pid, boolean(accepted), boolean(equal));
    supervisor_event("consume_release", "attempted", &j);
    atomic_store_explicit(&e->consume_permitted, equal ? 1u : 2u, memory_order_release);
    atomic_store_explicit(&e->consume_release, 1, memory_order_release);
    if (!await_flag(e, children, &e->role[1].completed, &failure)) goto cleanup;
    atomic_store_explicit(&e->issuer_exit, 1, memory_order_release);
    while (!children[0].reaped || !children[1].reaped) {
        (void)drain(e, children);
        for (unsigned role = 0; role < 2; role++)
            if (poll_child(role, &children[role], false)) { failure = "child_wait_failed"; goto cleanup; }
        if (output_failed) { failure = "event_output_failed"; goto cleanup; }
        if (monotonic_ns() >= e->deadline) { failure = "execution_deadline"; goto cleanup; }
        if (!children[0].reaped || !children[1].reaped) brief_pause();
    }
    (void)drain(e, children);
    if (children[0].wait_status || children[1].wait_status) failure = "child_abnormal_exit";
cleanup:
    deadline_reached = monotonic_ns() >= e->deadline;
    if (deadline_reached && !failure) failure = "execution_deadline";
    if (output_failed && !failure) failure = "event_output_failed";
    if (failure) {
        j = (struct json){0}; jf(&j, "{\"reason\":"); js(&j, failure); jf(&j, "}");
        supervisor_event("equipment_failure", "attempted", &j);
    }
    cleanup_child(e, children, 0); cleanup_child(e, children, 1);
    (void)drain(e, children);
    if (failure) interruptions(e, children);
    bool all_reaped = (!children[0].launched || children[0].reaped) && (!children[1].launched || children[1].reaped);
    j = (struct json){0};
    if (all_reaped) {
        struct access_observation after[2];
        access_file(e->a, &after[0]); access_file(e->b, &after[1]);
        jf(&j, "{\"a\":{\"path\":"); js(&j, e->a); jf(&j, ",\"read\":"); ja(&j, e->a, &after[0]);
        jf(&j, "},\"b\":{\"path\":"); js(&j, e->b); jf(&j, ",\"read\":"); ja(&j, e->b, &after[1]); jf(&j, "}}");
    } else jf(&j, "{\"reason\":\"child_absence_unconfirmed\"}");
    supervisor_event("targets_after", all_reaped ? "attempted" : "unavailable", &j);
    erase(issued, sizeof(*issued)); erase(delivered, sizeof(*delivered));
    j = (struct json){0};
    jf(&j, "{\"issued\":{\"capacity\":%u,\"zero_confirmed\":%s},\"delivered\":{\"capacity\":%u,\"zero_confirmed\":%s},\"children_absent\":%s}",
        (unsigned)sizeof(*issued), boolean(all_zero(issued, sizeof(*issued))), (unsigned)sizeof(*delivered),
        boolean(all_zero(delivered, sizeof(*delivered))), boolean(all_reaped));
    supervisor_event("supervisor_token_erasure", "attempted", &j);
    j = (struct json){0};
    jf(&j, "{\"elapsed_seconds\":%.9f,\"deadline_reached\":%s,\"equipment_failure\":%s,\"reason\":",
        (double)(monotonic_ns() - began) / (double)NS_PER_SECOND, boolean(deadline_reached), boolean(failure != NULL || !all_reaped));
    js(&j, failure);
    jf(&j, ",\"issuer_reaped\":%s,\"recipient_reaped\":%s,\"issuer_wait_status\":%d,\"recipient_wait_status\":%d,\"all_children_reaped\":%s,\"output_failed\":%s}",
        boolean(children[0].reaped), boolean(children[1].reaped), children[0].wait_status, children[1].wait_status,
        boolean(all_reaped), boolean(output_failed));
    supervisor_event("supervisor_complete", "attempted", &j);
    if (efd >= 0) close(efd);
    if (ifd >= 0) close(ifd);
    if (dfd >= 0) close(dfd);
    for (size_t n = 0; n < lock_count; n++) close(locks[n]);
    munmap(issued, sizeof(*issued)); munmap(delivered, sizeof(*delivered)); munmap(e, sizeof(*e));
    return failure || !all_reaped || output_failed ? 1 : 0;
}
int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "issuer")) return child_main(0);
    if (argc == 2 && !strcmp(argv[1], "recipient")) return child_main(1);
    if ((argc != 5 && argc != 6) || strcmp(argv[1], "supervise") ||
        strlen(argv[2]) != 2 || argv[2][0] != 'C' || argv[2][1] < '0' || argv[2][1] > '7') {
        fputs("usage: pilot supervise C0..C7 TRIAL_ID TRIAL_DIR [LOCK_FDS_CSV]\n", stderr); return 2;
    }
    return supervisor_main(argv[2], argv[3], argv[4], argc == 6 ? argv[5] : "");
}
