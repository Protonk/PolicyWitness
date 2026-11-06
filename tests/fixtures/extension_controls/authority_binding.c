/* The production recipient checks preassigned slot ownership before consuming.
 * Synthetic bytes and a counted consume replacement establish association,
 * not native sandbox authority. No token or sandbox API call is performed. */
#include <stdint.h>
static uint64_t controlled_clock(unsigned stage);
#define PW_CONTINUOUS_READ(stage) controlled_clock((unsigned)(stage))
#define main production_worker_main
#include "../../../controller/tools/pw_probe_runner/pw_probe_runner.c"
#undef main
#include <assert.h>

static unsigned calls;
static int64_t counted_consume(const char *token) { assert(token[0]); calls++; return 42; }
static unsigned clock_mode, clock_observations, issue_calls;
static uint64_t clock_ticks;

static void require(int condition, const char *claim) {
    if (!condition) { fprintf(stderr, "CONTROL_REJECTED: %s\n", claim); exit(73); }
}

static uint64_t controlled_clock(unsigned stage) {
    if (!clock_mode) return mach_continuous_time();
    if (stage != PW_CLOCK_EXCHANGE_OBSERVE) return clock_ticks;
    clock_observations++;
    if (clock_mode == 1 || clock_mode == 3) {
        clock_ticks += (uint64_t)PW_AUTHORITY_EXCHANGE_WAIT_MS * 1000000u;
    } else if (clock_mode == 2) {
        /* The first request timed out. Its answer arrives while the second
         * action waits; only the subsequent second answer may end that wait. */
        if (clock_observations == 1)
            atomic_store_explicit(&authority->transfers[0].acknowledged, PW_TRANSFER_ACK_DELIVERED, memory_order_release);
        else
            atomic_store_explicit(&authority->transfers[1].acknowledged, PW_TRANSFER_ACK_CUSTODY_UNAVAILABLE, memory_order_release);
        clock_ticks++;
    } else {
        pw_authority_slot_t *out = pw_authority_outbound(authority, clock_observations == 1 ? 0 : 1);
        atomic_store_explicit(&out->acknowledged, PW_AUTHORITY_ACK_ACCEPTED, memory_order_release);
        clock_ticks++;
    }
    return clock_ticks;
}

static char *counted_issue(const char *kind, const char *target, uint32_t flags) {
    (void)kind; (void)target; (void)flags;
    issue_calls++;
    return strdup(issue_calls == 1 ? "synthetic-first-issue" : "synthetic-second-issue");
}

static void handoff_lifetimes(void) {
    size_t bytes = PW_AUTHORITY_REGION_BYTES(2, 0);
    authority = calloc(1, bytes);
    require(authority != NULL, "allocate handoff control");
    authority->outbound_count = 2;
    pw_shm_header_t header = {0}; header.actor_mode = PW_ACTOR_MODE_UNAPPLIED;
    g_hdr = &header;
    transfer_assignment[0] = 1; transfer_assignment[1] = 2;
    pw_timing_t timing = {.clock = {.numer = 1, .denom = 1}};
    pw_shm_slot_t first = {0}, second = {0}; second.ext_delivery_index = 1;
    clock_mode = 1; clock_ticks = 0; clock_observations = 0;
    attempt_extension_transfer(&first, &timing, 0);
    require(first.ext_transfer_status == PW_TRANSFER_ACK_HOST_TIMEOUT, "first transfer reaches controlled timeout");
    require(atomic_load(&authority->transfers[0].requested) == 1, "timed-out request remains independently published");
    clock_mode = 2; clock_observations = 0;
    attempt_extension_transfer(&second, &timing, 1);
    require(second.ext_transfer_status == PW_TRANSFER_ACK_CUSTODY_UNAVAILABLE && clock_observations == 2,
            "late first answer cannot complete second transfer");
    require(first.ext_transfer_status == PW_TRANSFER_ACK_HOST_TIMEOUT, "late answer cannot rewrite prior action publication");
    puts("late transfer answer kept with its own request");

    memset(outbound_attempted, 0, sizeof(outbound_attempted));
    for (unsigned i = 0; i < 2; i++) {
        outbound_assignment[i].writer = 0; outbound_assignment[i].operation = i; outbound_assignment[i].resource = i;
    }
    extension_issue = counted_issue;
    pw_shm_slot_t issue_first = {0}, issue_second = {0}; issue_second.ext_token_index = 1;
    clock_mode = 3; clock_observations = 0;
    attempt_extension_issue(&issue_first, &timing, 0);
    require(issue_first.ext_custody_status == PW_CUSTODY_TIMEOUT, "first issue reaches controlled custody timeout");
    require(!strcmp(pw_authority_outbound(authority, 0)->token, "synthetic-first-issue"),
            "custody timeout preserves host-owned publication");
    clock_mode = 4; clock_observations = 0;
    attempt_extension_issue(&issue_second, &timing, 1);
    require(issue_calls == 2 && issue_second.ext_custody_status == PW_CUSTODY_ACCEPTED && clock_observations == 2,
            "second issue awaits its own custody answer");
    erase_authority();
    require(!strcmp(pw_authority_outbound(authority, 0)->token, "synthetic-first-issue")
            && !strcmp(pw_authority_outbound(authority, 1)->token, "synthetic-second-issue"),
            "worker cleanup preserves host-owned outbound slots");
    puts("outbound publication remains immutable across timeout, next issue and worker cleanup");
    /* This fixture is now the only owner, so it performs the host's erasure. */
    memset(authority, 0, bytes); free(authority); authority = NULL; clock_mode = 0;
}

int main(void) {
    for (unsigned mutation = 0; mutation < 5; mutation++) {
        unsigned rejected = mutation > 0 && mutation < 4;
        char path[] = "/private/tmp/pw-authority-binding.XXXXXX";
        int fd;
        unsigned count = mutation == 4 ? PW_AUTHORITY_MAX_INBOUND : 1;
        unsigned outbound_count = mutation == 4 ? PW_AUTHORITY_MAX_OUTBOUND : 0;
        size_t required = PW_AUTHORITY_REGION_BYTES(outbound_count, count);
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
        host->actor_index = 1; host->inbound_count = count; host->outbound_count = outbound_count;
        pw_authority_slot_t *inbound = pw_authority_inbound(host, 0);
        inbound->writer_actor = 0;
        inbound->operation_index = 8;
        inbound->resource_index = 3;
        pw_shm_header_t header = {0};
        header.actor_mode = PW_ACTOR_MODE_UNAPPLIED; header.actor_index = 1;
        pw_authority_setup_t setup={0}; setup.required=1;setup.actor_index=header.actor_index;g_setup=&setup;
        prepare_authority(&header, fd);  /* closes fd, snapshots assignment */
        assert(header.authority_status == PW_AUTHORITY_SETUP_MAPPED);
        pw_authority_slot_t *slot = pw_authority_inbound(host, 0);
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
        require(calls == 0 && action.unavailable_code == 6, "recipient waits for host settlement before consume");
        erase_authority();
        require(slot->token[0] != 0, "worker cleanup cannot erase an unsettled inbound copy");
        atomic_store_explicit(&slot->settled, 1, memory_order_release);
        memset(&action, 0, sizeof(action)); action.ext_delivery_index = slot->resource_index;
        attempt_extension_consume_actor(&action);
        assert(calls == (rejected ? 0u : 1u));
        assert(atomic_load(&action.call_boundary) == (rejected ? 0u : 1u));
        assert(action.native_result_valid == (rejected ? 0u : 1u));
        assert(action.unavailable_code == (rejected ? 6u : 0u));
        printf("control=%u acknowledgement=%u reject_detail=%u consume_calls=%u required=%zu mapped=%zu\n",
               mutation, atomic_load(&slot->acknowledged), slot->reject_detail, calls, required, size);
        erase_authority();
        require(slot->token[0] == 0, "worker erases settled inbound bytes");
        munmap(authority, size); authority = NULL;
        munmap(host, size);
    }
    g_setup=NULL;
    handoff_lifetimes();
    return 0;
}
