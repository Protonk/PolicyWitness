/* Ordinary-departure controls over the production worker. Native sandbox and
 * extension calls are substituted, so this establishes cleanup/publication
 * behavior, not native authority. Only synthetic token bytes enter memory.
 * The parent retains both mappings and never erases before its observations. */
#include <assert.h>
#include <mach/mach_time.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>
#include "pw_probe_runner_abi.h"
#include "pw_extension_channel.h"

static const char *scenario;
static pw_extension_channel_t *observed_channel;
static void *controlled_lookup(void *, const char *);
static kern_return_t controlled_timebase(mach_timebase_info_t);
static void terminal_gate(pw_shm_header_t *);
static void controlled_erase(void *, size_t);
static int controlled_sleep(const struct timespec *, struct timespec *);
#define dlsym controlled_lookup
#define sandbox_create_params controlled_create
#define sandbox_set_param controlled_set
#define sandbox_free_params controlled_free
#define sandbox_compile_string controlled_compile
#define sandbox_apply controlled_apply
#define PW_TIMEBASE_INFO controlled_timebase
#define PW_TERMINAL_PUBLISHED terminal_gate
#define pw_extension_erase controlled_erase
#define nanosleep controlled_sleep
#define main production_worker_main
#ifndef PW_TERMINAL_WORKER_SOURCE
#define PW_TERMINAL_WORKER_SOURCE "pw_probe_runner.c"
#endif
#include PW_TERMINAL_WORKER_SOURCE
#undef main
#undef dlsym
#undef pw_extension_erase
#undef nanosleep

typedef struct {
    _Atomic unsigned at_done, release_done;
    unsigned erase_calls, incomplete_erases, consume_calls, release_calls;
    unsigned sleep_observed, sleep_zero;
} observation_t;
static observation_t *rx;
static int is(const char *name) { return strcmp(scenario, name) == 0; }
static int full_zero(void) {
    /* Fixed capacity from the parent's independent mapping, never an erase
     * length, token_length, or string scan. */
    for (size_t i = 0; i < sizeof(observed_channel->token); ++i)
        if (observed_channel->token[i] != 0) return 0;
    return 1;
}
static void controlled_erase(void *bytes, size_t length) {
    pw_extension_erase(bytes, length);
    assert(bytes == observed_channel->token || extension_channel != NULL);
    rx->erase_calls++;
    if (!full_zero()) rx->incomplete_erases++;
}
static void terminal_gate(pw_shm_header_t *hdr) {
    assert(atomic_load_explicit(&hdr->done, memory_order_acquire) == 1);
    atomic_store_explicit(&rx->at_done, 1, memory_order_release);
    while (!atomic_load_explicit(&rx->release_done, memory_order_acquire)) usleep(1000);
}
static int64_t controlled_consume(const char *token) {
    assert(token[0] != 0);
    rx->consume_calls++;
    if (is("fatal_consume")) { kill(getpid(), SIGKILL); _exit(89); }
    if (is("consume_failure")) { errno = EACCES; return -1; }
    return 123;
}
static int controlled_release(int64_t handle) {
    assert(handle == 123 && full_zero());
    rx->release_calls++;
    return 0;
}
static void *controlled_lookup(void *library, const char *name) {
    (void)library;
    if (strcmp(name, "sandbox_extension_consume") == 0) return (void *)controlled_consume;
    if (strcmp(name, "sandbox_extension_release") == 0) return (void *)controlled_release;
    return NULL;
}
static kern_return_t controlled_timebase(mach_timebase_info_t info) {
    if (is("clock_setup")) return KERN_INVALID_ARGUMENT;
    return mach_timebase_info(info);
}
void *controlled_create(void) { return is("params_create") ? NULL : (void *)1; }
int controlled_set(void *p, const char *key, const char *value) {
    (void)p; (void)key; (void)value; return is("params_set") ? -3 : 0;
}
void controlled_free(void *p) { (void)p; }
void *controlled_compile(const char *source, void *p, char **error) {
    (void)source; (void)p; (void)error; return is("compile") ? NULL : (void *)1;
}
int controlled_apply(void *p) { (void)p; if (is("apply")) { errno = EACCES; return -1; } return 0; }
static int controlled_sleep(const struct timespec *requested, struct timespec *remaining) {
    (void)requested; (void)remaining;
    rx->sleep_observed++;
    rx->sleep_zero = full_zero();
    return 0;
}
static int shared_file(size_t size, void **view) {
    char path[] = "/private/tmp/pw-terminal-control.XXXXXX";
    int fd = mkstemp(path);
    assert(fd >= 0 && unlink(path) == 0 && ftruncate(fd, size) == 0);
    *view = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    assert(*view != MAP_FAILED);
    return fd;
}
int main(int argc, char **argv) {
    if (argc != 2) return 64;
    scenario = argv[1];
    void *memory;
    int region_fd = shared_file(PW_SHM_REGION_BYTES, &memory);
    int token_fd = shared_file(PW_EXTENSION_CHANNEL_BYTES, (void **)&observed_channel);
    rx = mmap(NULL, sizeof(*rx), PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANON, -1, 0);
    assert(rx != MAP_FAILED);
    observed_channel->magic = PW_EXTENSION_MAGIC;
    observed_channel->status = 1;
    strcpy(observed_channel->token, "synthetic-terminal-control");
    observed_channel->token_length = (uint32_t)strlen(observed_channel->token);
    size_t tail = observed_channel->token_length + 1;
    memset(observed_channel->token + tail, 0xa5, sizeof(observed_channel->token) - tail);
    /* Establish nonzero padding, including the last byte, before the fork. */
    unsigned tail_seeded = 1;
    for (size_t i = tail; i < sizeof(observed_channel->token); ++i)
        if ((unsigned char)observed_channel->token[i] != 0xa5) tail_seeded = 0;
    assert(tail_seeded);
    atomic_store_explicit(&observed_channel->completed, 1, memory_order_release);
    if (is("rejected_channel")) observed_channel->magic ^= 1;
    pw_shm_header_t *hdr = memory;
    hdr->abi_magic = PW_SHM_ABI_MAGIC;
    memcpy(hdr->abi_identity, PW_WORKER_ABI_IDENTITY, PW_SHM_ABI_IDENTITY_BYTES);
    hdr->extension_requested = !is("null_channel");
    hdr->step_count = (is("consume") || is("consume_failure") || is("fatal_consume")) ? 1 : is("explicit_release") ? 2 : 0;
    hdr->phase_count = 1;
    hdr->phases[0].end_slot = hdr->step_count;
    pw_shm_slot_t *slots = (void *)((char *)memory + PW_SHM_HEADER_BYTES);
    slots[0].attempt_kind = PW_ATTEMPT_EXTENSION_CONSUME;
    slots[1].attempt_kind = PW_ATTEMPT_EXTENSION_RELEASE;
    if (is("params_create") || is("params_set")) hdr->param_count = 1;
    if (is("param_capacity")) hdr->param_count = PW_SHM_MAX_PARAMS + 1;
    pw_shm_param_t *params = (void *)((char *)slots + PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES);
    strcpy(params[0].key, "KEY"); strcpy(params[0].value, "VALUE");
    void *policy;
    int policy_fd = shared_file(PW_SHM_POLICY_BYTES + 1, &policy);
    const char text[] = "(version 1)(allow default)";
    size_t size = sizeof(text) - 1;
    memcpy(policy, text, size);
    if (is("policy_nul")) ((char *)policy)[5] = 0;
    if (is("policy_overflow")) { size = PW_SHM_POLICY_BYTES; memset(policy, 'x', size); }
    assert(ftruncate(policy_fd, size) == 0);
    hdr->policy_bytes_expected = (uint32_t)size;
    if (is("length_expectation")) hdr->policy_bytes_expected = PW_SHM_POLICY_BYTES;
    if (is("length_mismatch")) hdr->policy_bytes_expected++;
    if (is("policy_overflow")) hdr->policy_bytes_expected = PW_SHM_POLICY_BYTES - 1;
    if (is("policy_read")) { close(policy_fd); policy_fd = 99999; }
    if (is("cancel")) atomic_store(&hdr->exit_requested, 1);
    if (!is("proceed_refusal") && !is("cancel")) atomic_store(&hdr->proceed, is("future_release") ? 2 : 1);
    atomic_store_explicit(&hdr->prepared, 1, memory_order_release);
    int ready[2]; assert(pipe(ready) == 0);
    char region_arg[16], token_arg[16], policy_arg[16], ready_arg[16];
    snprintf(region_arg, sizeof(region_arg), "%d", region_fd);
    snprintf(token_arg, sizeof(token_arg), "%d", token_fd);
    snprintf(policy_arg, sizeof(policy_arg), "%d", policy_fd);
    snprintf(ready_arg, sizeof(ready_arg), "%d", ready[1]);
    char *args[] = {"worker", "--shm-fd", region_arg, "--extension-fd", token_arg,
        "--policy-fd", policy_arg, "--ready-fd", ready_arg, "--proceed-wait-ms", "20",
        "--post-apply-hang-ms", is("pre_hang") ? "1" : "0",
        "--post-apply-kill-signal", is("post_signal") ? "9" : "0", NULL};
    pid_t pid = fork(); assert(pid >= 0);
    if (!pid) { close(ready[0]); int rc = production_worker_main(15, args); _exit(rc); }
    close(ready[1]);
    int status = 0, boundary_zero = -1, killed = 0;
    pid_t reaped = 0;
    for (int i = 0; i < 5000 && !reaped; ++i) {
        if (atomic_load_explicit(&rx->at_done, memory_order_acquire)
                && !atomic_load_explicit(&rx->release_done, memory_order_acquire)) {
            /* The worker is held at the actual store, unable to perform any
             * subsequent cleanup. Parent alone acquires done and scans. */
            assert(atomic_load_explicit(&hdr->done, memory_order_acquire) == 1);
            boundary_zero = full_zero();
            atomic_store_explicit(&rx->release_done, 1, memory_order_release);
        }
        reaped = waitpid(pid, &status, WNOHANG);
        assert(reaped >= 0);
        if (!reaped) usleep(1000);
    }
    if (!reaped) { killed = 1; assert(kill(pid, SIGKILL) == 0); reaped = waitpid(pid, &status, 0); }
    assert(reaped == pid);
    int final_zero = full_zero();
    pw_shm_evidence_t *e = pw_evidence(memory);
    printf("{\"scenario\":\"%s\",\"capacity\":%zu,\"tail_seeded\":%u,\"boundary_zero\":%d,"
           "\"final_zero\":%d,\"erase_calls\":%u,\"incomplete_erases\":%u,\"consume_calls\":%u,"
           "\"release_calls\":%u,\"sleep_observed\":%u,\"sleep_zero\":%u,\"cleanup_kill\":%d,"
           "\"exit_code\":%d,\"signal\":%d,\"done\":%u,\"applied\":%u,\"ack\":%u,\"completed\":%u,"
           "\"failure\":%u,\"operation\":%u,\"code\":%u,\"exit_requested\":%u,\"delivery\":%u}\n",
           scenario, sizeof(observed_channel->token), tail_seeded, boundary_zero, final_zero,
           rx->erase_calls, rx->incomplete_erases, rx->consume_calls, rx->release_calls,
           rx->sleep_observed, rx->sleep_zero, killed, WIFEXITED(status) ? WEXITSTATUS(status) : -1,
           WIFSIGNALED(status) ? WTERMSIG(status) : 0, atomic_load(&hdr->done), atomic_load(&hdr->applied),
           atomic_load(&hdr->phases[0].acknowledged), atomic_load(&slots[0].completed),
           atomic_load(&e->failure_published), e->operation, e->code, atomic_load(&hdr->exit_requested),
           hdr->extension_delivery_status);
    pw_extension_erase(observed_channel->token, sizeof(observed_channel->token));
    close(region_fd); close(token_fd); close(ready[0]);
    if (!is("policy_read")) close(policy_fd);
    assert(munmap(memory, PW_SHM_REGION_BYTES) == 0);
    assert(munmap(observed_channel, PW_EXTENSION_CHANNEL_BYTES) == 0);
    assert(munmap(policy, PW_SHM_POLICY_BYTES + 1) == 0);
    assert(munmap(rx, sizeof(*rx)) == 0);
    return 0;
}
