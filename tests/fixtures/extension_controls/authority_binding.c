/* The production recipient checks preassigned slot ownership before consuming.
 * Synthetic bytes and a counted consume replacement establish association,
 * not native sandbox authority. No token or sandbox API call is performed. */
#define main production_worker_main
#include "../../../controller/tools/pw_probe_runner/pw_probe_runner.c"
#undef main
#include <assert.h>

static unsigned calls;
static int64_t counted_consume(const char *token) { assert(token[0]); calls++; return 42; }

int main(void) {
    for (unsigned mutation = 0; mutation < 5; mutation++) {
        unsigned rejected = mutation > 0 && mutation < 4;
        char path[] = "/private/tmp/pw-authority-binding.XXXXXX";
        int fd;
        unsigned count = mutation == 4 ? PW_AUTHORITY_MAX_INBOUND : 1;
        size_t required = PW_AUTHORITY_REGION_BYTES(count);
        if (mutation == 4) {
            char name[32]; snprintf(name, sizeof(name), "/pw_bind_%d", getpid());
            fd = shm_open(name, O_CREAT | O_EXCL | O_RDWR, 0600);
            assert(fd >= 0 && shm_unlink(name) == 0);
        } else {
            fd = mkstemp(path);
            assert(fd >= 0 && unlink(path) == 0);
        }
        assert(ftruncate(fd, (off_t)required) == 0);
        struct stat metadata; assert(fstat(fd, &metadata) == 0);
        size_t size = (size_t)metadata.st_size;
        assert(size >= required);
        if (mutation == 4) assert(size > required && size % (size_t)getpagesize() == 0);
        pw_authority_region_t *host = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
        assert(host != MAP_FAILED);
        host->magic = PW_AUTHORITY_MAGIC;
        memcpy(host->identity, PW_WORKER_ABI_IDENTITY, sizeof(host->identity));
        host->actor_index = 1; host->inbound_count = count;
        host->inbound[0].writer_actor = 0;
        host->inbound[0].operation_index = 8;
        host->inbound[0].resource_index = 3;
        pw_shm_header_t header = {0};
        header.actor_mode = PW_ACTOR_MODE_UNAPPLIED; header.actor_index = 1;
        prepare_authority(&header, fd);  /* closes fd, snapshots assignment */
        assert(header.authority_status == PW_AUTHORITY_SETUP_MAPPED);
        pw_authority_slot_t *slot = &host->inbound[0];
        slot->magic = PW_AUTHORITY_MAGIC; slot->family = PW_AUTHORITY_FAMILY_FILE;
        strcpy(slot->token, "synthetic-binding-control");
        slot->token_length = (uint32_t)strlen(slot->token);
        if (mutation == 1) slot->writer_actor = 2;
        if (mutation == 2) slot->operation_index = 9;
        if (mutation == 3) slot->resource_index = 4;
        atomic_store_explicit(&slot->committed, 1, memory_order_release);
        service_inbound_once();
        assert(atomic_load(&slot->acknowledged) == (rejected ? PW_AUTHORITY_ACK_REJECTED : PW_AUTHORITY_ACK_ACCEPTED));
        const unsigned reasons[] = {0, PW_AUTHORITY_REJECT_OWNER, PW_AUTHORITY_REJECT_ORDINAL, PW_AUTHORITY_REJECT_RESOURCE, 0};
        assert(slot->reject_detail == reasons[mutation]);
        pw_shm_slot_t action = {0};
        action.ext_delivery_index = slot->resource_index; /* even a matching wrong reference cannot consume */
        g_hdr = &header; extension_consume = counted_consume; calls = 0;
        attempt_extension_consume_actor(&action);
        assert(calls == (rejected ? 0u : 1u));
        assert(atomic_load(&action.call_boundary) == (rejected ? 0u : 1u));
        assert(action.native_result_valid == (rejected ? 0u : 1u));
        assert(action.unavailable_code == (rejected ? 6u : 0u));
        printf("control=%u acknowledgement=%u reject_detail=%u consume_calls=%u required=%zu mapped=%zu\n",
               mutation, atomic_load(&slot->acknowledged), slot->reject_detail, calls, required, size);
        erase_authority(); munmap(authority, size); authority = NULL;
        munmap(host, size);
    }
    return 0;
}
