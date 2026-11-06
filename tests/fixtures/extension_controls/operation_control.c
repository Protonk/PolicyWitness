/* Direct operation bodies and production dispatch with counted callbacks and a real
 * fresh file open. Synthetic tokens establish call/association boundaries,
 * never kernel authority. An inherited descriptor names the same file, so
 * matching read bytes alone cannot distinguish the disposable reuse mutant. */
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

static unsigned fresh_opens;
static int fresh_descriptor = -1;
static int inherited_fd = -1;
static const char *fresh_target;
static unsigned issued, consumed, released;

static void require(int condition, const char *claim) {
    if (!condition) {
        fprintf(stderr, "CONTROL_REJECTED: %s\n", claim);
        exit(73);
    }
}

static int counted_open(const char *path, int flags, ...) {
    require(fresh_target && !strcmp(path, fresh_target), "fresh open uses requested path");
    require(flags == (O_RDONLY | O_CLOEXEC), "fresh open uses read-only close-on-exec flags");
    fresh_opens++;
    fresh_descriptor = open(path, flags);
    return fresh_descriptor;
}

#define open counted_open
#define main production_worker_main
#include "../../../controller/tools/pw_probe_runner/pw_probe_runner.c"
#undef main
#undef open

static char *counted_issue(const char *kind, const char *path, uint32_t flags) {
    issued++;
    require(!strcmp(kind, "com.apple.app-sandbox.read") && !strcmp(path, "/controlled/issue") && flags == 0,
            "issue callback receives submitted class/path/flags");
    errno = EACCES;
    return NULL;  /* A real call to the controlled boundary, with a refusal. */
}

static int64_t counted_consume(const char *token) {
    consumed++;
    require(!strcmp(token, "synthetic-delivery-Y"), "consume selects the named delivery");
    errno = 0;
    return consumed == 1 ? 202 : 303;
}

static int counted_release(int64_t handle) {
    released++;
    require(handle == (released == 1 ? 202 : 303),
            released == 1 ? "release receives its owned candidate handle" : "dispatch release receives its own distinct handle");
    errno = 0;
    return 0;
}

int main(void) {
    size_t bytes = PW_AUTHORITY_REGION_BYTES(2, 2);
    char region_path[] = "/private/tmp/pw-operation-region.XXXXXX";
    int region_fd = mkstemp(region_path);
    require(region_fd >= 0 && unlink(region_path) == 0 && ftruncate(region_fd, (off_t)bytes) == 0,
            "create owned anonymous authority equipment");
    pw_authority_region_t *host = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, region_fd, 0);
    require(host != MAP_FAILED, "map authority equipment");
    host->magic = PW_AUTHORITY_MAGIC;
    memcpy(host->identity, PW_WORKER_ABI_IDENTITY, sizeof(host->identity));
    host->actor_index = 0; host->outbound_count = 2; host->inbound_count = 2;
    pw_authority_slot_t *out = pw_authority_outbound(host, 0);
    out->writer_actor = 0; out->operation_index = 0; out->resource_index = 5;
    pw_authority_slot_t *dispatch_out = pw_authority_outbound(host, 1);
    dispatch_out->writer_actor = 0; dispatch_out->operation_index = 17; dispatch_out->resource_index = 13;
    for (unsigned i = 0; i < 2; i++) {
        pw_authority_slot_t *in = pw_authority_inbound(host, i);
        in->writer_actor = 1; in->operation_index = 8 + i; in->resource_index = 3 + 4 * i;
    }
    pw_shm_header_t header = {0};
    header.actor_mode = PW_ACTOR_MODE_UNAPPLIED; header.actor_index = 0;
    pw_authority_setup_t setup={0}; setup.required=1;g_setup=&setup;
    prepare_authority(&header, region_fd);
    require(header.authority_status == PW_AUTHORITY_SETUP_MAPPED, "prepare authority equipment");
    g_hdr = &header;
    extension_issue = counted_issue; extension_consume = counted_consume; extension_release = counted_release;
    pw_shm_slot_t issue = {0};
    issue.ext_token_index = 5;
    strcpy(issue.ext_target, "/controlled/issue");
    pw_timing_t timing = {0};
    attempt_extension_issue(&issue, &timing, 0);
    require(issued == 1, "issue native call executed exactly once");
    require(atomic_load(&issue.call_boundary) == 1 && issue.native_result_valid == 1
            && issue.native_result == 0 && issue.native_errno == EACCES, "issue refusal retains separate native evidence");
    for (unsigned i = 0; i < 2; i++) {
        pw_authority_slot_t *in = pw_authority_inbound(host, i);
        in->magic = PW_AUTHORITY_MAGIC; in->family = PW_AUTHORITY_FAMILY_FILE;
        strcpy(in->token, i ? "synthetic-delivery-Y" : "synthetic-delivery-X");
        in->token_length = (uint32_t)strlen(in->token);
        atomic_store(&in->committed, 1);
        atomic_store(&in->acknowledged, PW_AUTHORITY_ACK_ACCEPTED);
        atomic_store(&in->settled, 1);
    }
    pw_shm_slot_t consume = {0};
    consume.ext_delivery_index = 7; consume.ext_handle_index = 9;
    attempt_extension_consume_actor(&consume);
    require(consumed == 1, "consume native call executed exactly once");
    require(consume.native_result_valid == 1 && consume.native_result == 202 && handle_valid[9]
            && handle_table[9] == 202, "consume connects its result to the requested handle");
    pw_shm_slot_t release = {0}; release.ext_handle_index = 9;
    attempt_extension_release_actor(&release);
    require(released == 1, "release native call executed exactly once");
    require(release.native_result_valid == 1 && release.native_result == 0, "release publishes its own native result");
    /* Keep the direct-body controls above: they establish callback bodies and
     * payload ownership. These fresh slots enter the real run_attempt switch,
     * with distinct nonzero issue, delivery and handle operands. No dispatcher
     * is substituted and no callback count is inferred from completed/status. */
    pw_shm_slot_t dispatch_issue = {0};
    dispatch_issue.attempt_kind = PW_ATTEMPT_EXTENSION_ISSUE;
    dispatch_issue.ext_token_index = 13;
    strcpy(dispatch_issue.ext_target, "/controlled/issue");
    run_attempt(&dispatch_issue, &timing, 3, 17, 0);
    require(issued == 2 && consumed == 1 && released == 1, "dispatch issue calls only its native issue boundary");
    require(atomic_load(&dispatch_issue.completed) == 1 && atomic_load(&dispatch_issue.call_boundary) == 1
            && dispatch_issue.native_result_valid == 1 && dispatch_issue.native_result == 0
            && dispatch_issue.native_errno == EACCES, "dispatch issue publishes its own native refusal");
    pw_shm_slot_t dispatch_consume = {0};
    dispatch_consume.attempt_kind = PW_ATTEMPT_EXTENSION_CONSUME;
    dispatch_consume.ext_delivery_index = 7; dispatch_consume.ext_handle_index = 27;
    run_attempt(&dispatch_consume, &timing, 3, 18, 0);
    require(issued == 2 && consumed == 2 && released == 1, "dispatch consume calls only its native consume boundary");
    require(atomic_load(&dispatch_consume.completed) == 1 && atomic_load(&dispatch_consume.call_boundary) == 1
            && dispatch_consume.native_result_valid == 1 && dispatch_consume.native_result == 303
            && handle_valid[27] && handle_table[27] == 303 && handle_table[9] == 202,
            "dispatch consume binds the distinct result to its named handle");
    pw_shm_slot_t dispatch_release = {0};
    dispatch_release.attempt_kind = PW_ATTEMPT_EXTENSION_RELEASE;
    dispatch_release.ext_handle_index = 27;
    run_attempt(&dispatch_release, &timing, 3, 19, 0);
    require(issued == 2 && consumed == 2 && released == 2, "dispatch release calls only its native release boundary");
    require(atomic_load(&dispatch_release.completed) == 1 && atomic_load(&dispatch_release.call_boundary) == 1
            && dispatch_release.native_result_valid == 1 && dispatch_release.native_result == 0,
            "dispatch release publishes its own native result");
    erase_authority();
    munmap(authority, bytes); authority = NULL;
    munmap(host, bytes);

    char target[] = "/private/tmp/pw-operation-read.XXXXXX";
    int writer = mkstemp(target);
    const char contents[] = "PW same object through distinct opens\n";
    require(writer >= 0 && write(writer, contents, sizeof(contents) - 1) == (ssize_t)sizeof(contents) - 1
            && close(writer) == 0, "create fresh-read equipment");
    inherited_fd = open(target, O_RDONLY | O_CLOEXEC);
    require(inherited_fd >= 0, "hold inherited descriptor counterexample");
    struct stat expected; require(fstat(inherited_fd, &expected) == 0, "observe independent file identity");
    fresh_target = target;
    pw_shm_slot_t read_slot = {0}; strcpy(read_slot.target, target);
    attempt_file_read_fresh(&read_slot);
    int inherited_survived = fcntl(inherited_fd, F_GETFD) >= 0;
    int fresh_closed = read_slot.access_open_rc >= 0 && fcntl(read_slot.access_open_rc, F_GETFD) == -1 && errno == EBADF;
    unlink(target); close(inherited_fd); /* Retire our equipment before any rejected assertion. */
    require(read_slot.rc == 0 && read_slot.access_read_rc == (ssize_t)sizeof(contents) - 1
            && !memcmp(read_slot.access_bytes, contents, sizeof(contents) - 1), "fresh read returns known bytes");
    require(read_slot.access_device == (uint32_t)expected.st_dev && read_slot.access_inode == expected.st_ino,
            "fresh read identifies the prepared object");
    require(fresh_opens == 1, "fresh read executes its own open");
    require(read_slot.access_open_rc == fresh_descriptor && fresh_descriptor != inherited_fd
            && inherited_survived && fresh_closed, "fresh read owns and closes only its new descriptor");
    puts("direct bodies and run_attempt dispatch: issue/consume/release calls, distinct delivery/handle associations and fresh descriptor ownership observed");
    return 0;
}
