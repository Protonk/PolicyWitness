/* The production recipient checks preassigned slot ownership before consuming.
 * Synthetic bytes and a counted consume replacement establish association,
 * not native sandbox authority. No token or sandbox API call is performed.
 * The scan seams count each production inbound pass, slot visit and acquire
 * load, so the scan scenarios assert exact work beside the behavior. */
#include <stdint.h>
#include <stdatomic.h>
static uint64_t controlled_clock(unsigned stage);
#define PW_CONTINUOUS_READ(stage) controlled_clock((unsigned)(stage))
static unsigned scan_passes, scan_visits, scan_loads, scan_acknowledgements;
static uint32_t scan_first_visit, scan_acknowledged_index, scan_acknowledged_problem;
static void count_scan_pass(void) { scan_passes++; }
static void count_scan_visit(uint32_t index) {
    if (!scan_visits) scan_first_visit = index;
    scan_visits++;
}
static uint32_t count_scan_load(_Atomic uint32_t *word) {
    scan_loads++;
    return atomic_load_explicit(word, memory_order_acquire);
}
static void count_scan_acknowledged(uint32_t index, uint32_t problem) {
    scan_acknowledgements++; scan_acknowledged_index = index; scan_acknowledged_problem = problem;
}
#define PW_INBOUND_SCAN_PASS() count_scan_pass()
#define PW_INBOUND_SCAN_VISIT(index) count_scan_visit((uint32_t)(index))
#define PW_INBOUND_SCAN_LOAD(word) count_scan_load(word)
#define PW_INBOUND_ACKNOWLEDGED(index, problem) count_scan_acknowledged((uint32_t)(index), (uint32_t)(problem))
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

/* ---- inbound scan scenarios ------------------------------------------------
 * Each scenario prepares a fresh file-backed region through prepare_authority
 * (distinct host and worker views), commits synthetic frames from the host
 * view and runs single production passes. A pass asserts its exact visits,
 * acquire loads, first visited index, acknowledged slot and resulting prefix;
 * the scenario then checks acknowledgement words, reject_detail, settlement,
 * consumption and erasure as the mutations above do. */
#define SCAN_NONE UINT32_MAX
static pw_shm_header_t scan_header;
static pw_authority_setup_t scan_setup;
static unsigned scan_total_passes, scan_total_visits, scan_total_loads, scan_total_acknowledgements;
static unsigned scan_consumed;
static const char *scan_consumed_token;
typedef struct { pw_authority_region_t *host; size_t size; unsigned count; } scan_region_t;

static int64_t scan_consume(const char *token) { scan_consumed++; scan_consumed_token = token; return 7; }

static scan_region_t scan_prepare(unsigned count) {
    scan_region_t region = {0};
    char path[] = "/private/tmp/pw-authority-scan.XXXXXX";
    int fd = mkstemp(path);
    require(fd >= 0 && unlink(path) == 0, "create an unlinked scan region");
    region.count = count;
    region.size = PW_AUTHORITY_REGION_BYTES(0, count);
    require(ftruncate(fd, (off_t)region.size) == 0, "size the scan region");
    region.host = mmap(NULL, region.size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    require(region.host != MAP_FAILED, "map the host view of the scan region");
    region.host->magic = PW_AUTHORITY_MAGIC;
    memcpy(region.host->identity, PW_WORKER_ABI_IDENTITY, sizeof(region.host->identity));
    region.host->actor_index = 1; region.host->inbound_count = count; region.host->outbound_count = 0;
    for (unsigned i = 0; i < count; i++) {
        pw_authority_slot_t *slot = pw_authority_inbound(region.host, i);
        slot->writer_actor = 0; slot->operation_index = 100 + i; slot->resource_index = i;
    }
    memset(&scan_header, 0, sizeof(scan_header));
    scan_header.actor_mode = PW_ACTOR_MODE_UNAPPLIED; scan_header.actor_index = 1;
    memset(&scan_setup, 0, sizeof(scan_setup));
    scan_setup.required = 1; scan_setup.actor_index = 1; g_setup = &scan_setup;
    authority = NULL;
    prepare_authority(&scan_header, fd);  /* closes fd, snapshots assignments */
    require(scan_header.authority_status == PW_AUTHORITY_SETUP_MAPPED && authority && authority != region.host,
            "scan region prepared through a separate worker view");
    require(inbound_acknowledged_prefix == 0, "preparation starts the completed prefix at zero");
    for (unsigned i = 0; i < PW_AUTHORITY_MAX_INBOUND; i++)
        require(inbound_acknowledged_local[i] == 0, "preparation clears the local acknowledgement record");
    scan_total_passes = scan_total_visits = scan_total_loads = scan_total_acknowledgements = 0;
    return region;
}

static void scan_commit(scan_region_t *region, unsigned index, uint32_t writer) {
    pw_authority_slot_t *slot = pw_authority_inbound(region->host, index);
    slot->magic = PW_AUTHORITY_MAGIC; slot->family = PW_AUTHORITY_FAMILY_FILE;
    snprintf(slot->token, sizeof(slot->token), "synthetic-scan-%02u", index);
    slot->token_length = (uint32_t)strlen(slot->token);
    slot->writer_actor = writer;
    atomic_store_explicit(&slot->committed, 1, memory_order_release);
}

static void scan_pass(const char *scenario, unsigned visits, unsigned loads, uint32_t first,
                      uint32_t acknowledged, uint32_t prefix) {
    scan_passes = scan_visits = scan_loads = scan_acknowledgements = 0;
    scan_first_visit = scan_acknowledged_index = SCAN_NONE;
    service_inbound_once();
    unsigned acknowledgements = acknowledged == SCAN_NONE ? 0u : 1u;
    if (scan_passes != 1 || scan_visits != visits || scan_loads != loads || scan_first_visit != first
        || scan_acknowledgements != acknowledgements || scan_acknowledged_index != acknowledged
        || inbound_acknowledged_prefix != prefix) {
        fprintf(stderr, "CONTROL_REJECTED: scan %s pass %u observed passes=%u visits=%u loads=%u first=%d "
                "acknowledged=%d prefix=%u; expected visits=%u loads=%u first=%d acknowledged=%d prefix=%u\n",
                scenario, scan_total_passes, scan_passes, scan_visits, scan_loads, (int)scan_first_visit,
                (int)scan_acknowledged_index, inbound_acknowledged_prefix, visits, loads, (int)first,
                (int)acknowledged, prefix);
        exit(73);
    }
    scan_total_passes++; scan_total_visits += visits; scan_total_loads += loads;
    scan_total_acknowledgements += acknowledgements;
}

/* acknowledgement[i] and detail[i] are the expected shared words. Consume
 * waits for settlement; after it only accepted deliveries reach the counted
 * consume, each with its own slot's bytes. Worker cleanup erases settled bytes. */
static void scan_finish(const char *scenario, scan_region_t *region, const uint32_t *acknowledgement,
                        const uint32_t *detail) {
    unsigned accepted = 0;
    for (unsigned i = 0; i < region->count; i++) {
        pw_authority_slot_t *slot = pw_authority_inbound(region->host, i);
        require(atomic_load(&slot->acknowledged) == acknowledgement[i] && slot->reject_detail == detail[i],
                "scan acknowledgement words and reject_detail are as today");
        accepted += acknowledgement[i] == PW_AUTHORITY_ACK_ACCEPTED;
    }
    g_hdr = &scan_header; extension_consume = scan_consume; scan_consumed = 0;
    for (unsigned i = 0; i < region->count; i++) {
        pw_shm_slot_t action = {0}; action.ext_delivery_index = i; action.ext_handle_index = i;
        attempt_extension_consume_actor(&action);
        require(action.unavailable_code == 6, "scan recipient waits for host settlement before consume");
    }
    require(scan_consumed == 0, "no scanned delivery is consumed before settlement");
    for (unsigned i = 0; i < region->count; i++) {
        pw_authority_slot_t *slot = pw_authority_inbound(region->host, i);
        if (atomic_load(&slot->committed)) atomic_store_explicit(&slot->settled, 1, memory_order_release);
    }
    for (unsigned i = 0; i < region->count; i++) {
        pw_authority_slot_t *slot = pw_authority_inbound(authority, i);
        pw_shm_slot_t action = {0}; action.ext_delivery_index = i; action.ext_handle_index = i;
        unsigned before = scan_consumed; scan_consumed_token = NULL;
        attempt_extension_consume_actor(&action);
        if (acknowledgement[i] == PW_AUTHORITY_ACK_ACCEPTED)
            require(scan_consumed == before + 1 && scan_consumed_token == slot->token && action.native_result_valid
                    && handle_valid[i] && handle_table[i] == 7, "accepted settled delivery consumes its own slot");
        else
            require(scan_consumed == before && action.unavailable_code == 6 && !action.call_boundary,
                    "unaccepted delivery never reaches consume");
    }
    erase_authority();
    for (unsigned i = 0; i < region->count; i++) {
        pw_authority_slot_t *slot = pw_authority_inbound(region->host, i);
        if (atomic_load(&slot->settled)) require(slot->token[0] == 0, "worker erases settled scanned bytes");
    }
    printf("scan=%s slots=%u passes=%u visits=%u loads=%u acknowledgements=%u prefix=%u consume_calls=%u\n",
           scenario, region->count, scan_total_passes, scan_total_visits, scan_total_loads,
           scan_total_acknowledgements, inbound_acknowledged_prefix, scan_consumed);
    require(scan_consumed == accepted, "every accepted delivery consumed once");
    munmap(authority, region->size); authority = NULL;
    munmap(region->host, region->size);
    memset(handle_valid, 0, sizeof(handle_valid)); memset(handle_table, 0, sizeof(handle_table));
}

static void scan_scenarios(void) {
    uint32_t acknowledgement[PW_AUTHORITY_MAX_INBOUND], detail[PW_AUTHORITY_MAX_INBOUND];
    const uint32_t A = PW_AUTHORITY_ACK_ACCEPTED, R = PW_AUTHORITY_ACK_REJECTED, N = SCAN_NONE;

    /* Empty slot set: a pass makes no visit and no load. */
    scan_region_t region = scan_prepare(0);
    scan_pass("empty", 0, 0, N, N, 0);
    scan_pass("empty", 0, 0, N, N, 0);
    scan_finish("empty", &region, acknowledgement, detail);

    /* Single slot: one load per pass before commit, two on the acknowledging
     * pass, then no visit. */
    region = scan_prepare(1);
    scan_pass("single", 1, 1, 0, N, 0);
    scan_pass("single", 1, 1, 0, N, 0);
    scan_commit(&region, 0, 0);
    scan_pass("single", 1, 2, 0, 0, 1);
    scan_pass("single", 0, 0, N, N, 1);
    scan_pass("single", 0, 0, N, N, 1);
    acknowledgement[0] = A; detail[0] = 0;
    scan_finish("single", &region, acknowledgement, detail);

    /* Maximum slot set, all committed in order before the first pass: each
     * pass acknowledges exactly the lowest unacknowledged slot, visiting it
     * alone; repeated servicing afterwards makes no visit and no load. */
    region = scan_prepare(PW_AUTHORITY_MAX_INBOUND);
    for (unsigned i = 0; i < PW_AUTHORITY_MAX_INBOUND; i++) scan_commit(&region, i, 0);
    for (unsigned k = 0; k < PW_AUTHORITY_MAX_INBOUND; k++) scan_pass("maximum_committed", 1, 2, k, k, k + 1);
    scan_pass("maximum_committed", 0, 0, N, N, PW_AUTHORITY_MAX_INBOUND);
    scan_pass("maximum_committed", 0, 0, N, N, PW_AUTHORITY_MAX_INBOUND);
    for (unsigned i = 0; i < PW_AUTHORITY_MAX_INBOUND; i++) { acknowledgement[i] = A; detail[i] = 0; }
    scan_finish("maximum_committed", &region, acknowledgement, detail);

    /* Maximum slot set committed one at a time in order: the pass before each
     * commit visits every slot above the prefix, so visits per pass fall from
     * 64 to 1 and then to 0 after the last acknowledgement. */
    region = scan_prepare(PW_AUTHORITY_MAX_INBOUND);
    for (unsigned k = 0; k < PW_AUTHORITY_MAX_INBOUND; k++) {
        scan_pass("maximum_incremental", PW_AUTHORITY_MAX_INBOUND - k, PW_AUTHORITY_MAX_INBOUND - k, k, N, k);
        scan_commit(&region, k, 0);
        scan_pass("maximum_incremental", 1, 2, k, k, k + 1);
    }
    scan_pass("maximum_incremental", 0, 0, N, N, PW_AUTHORITY_MAX_INBOUND);
    scan_pass("maximum_incremental", 0, 0, N, N, PW_AUTHORITY_MAX_INBOUND);
    scan_finish("maximum_incremental", &region, acknowledgement, detail);

    /* Accepted and rejected prefix: a rejection is this worker's own
     * acknowledgement, so the prefix advances past it. */
    region = scan_prepare(4);
    scan_commit(&region, 0, 0); scan_commit(&region, 1, 0);
    scan_commit(&region, 2, 2); scan_commit(&region, 3, 0);
    scan_pass("accepted_rejected", 1, 2, 0, 0, 1);
    scan_pass("accepted_rejected", 1, 2, 1, 1, 2);
    scan_pass("accepted_rejected", 1, 2, 2, 2, 3);
    require(scan_acknowledged_problem == PW_AUTHORITY_REJECT_OWNER, "wrong owner rejected with its reason");
    scan_pass("accepted_rejected", 1, 2, 3, 3, 4);
    scan_pass("accepted_rejected", 0, 0, N, N, 4);
    acknowledgement[0] = A; acknowledgement[1] = A; acknowledgement[2] = R; acknowledgement[3] = A;
    detail[0] = 0; detail[1] = 0; detail[2] = PW_AUTHORITY_REJECT_OWNER; detail[3] = 0;
    scan_finish("accepted_rejected", &region, acknowledgement, detail);

    /* Early hole: slot 0 is visited with one load on every pass and keeps the
     * prefix at 0 while slots 1 to 3 are acknowledged in index order; its
     * late commit is acknowledged next and the prefix then covers all four. */
    region = scan_prepare(4);
    scan_commit(&region, 1, 0); scan_commit(&region, 2, 0); scan_commit(&region, 3, 0);
    scan_pass("early_hole", 2, 3, 0, 1, 0);
    scan_pass("early_hole", 3, 5, 0, 2, 0);
    scan_pass("early_hole", 4, 7, 0, 3, 0);
    scan_pass("early_hole", 4, 7, 0, N, 0);
    scan_commit(&region, 0, 0);
    scan_pass("early_hole", 1, 2, 0, 0, 4);
    scan_pass("early_hole", 0, 0, N, N, 4);
    for (unsigned i = 0; i < 4; i++) { acknowledgement[i] = A; detail[i] = 0; }
    scan_finish("early_hole", &region, acknowledgement, detail);

    /* Later eligible slots: once the prefix covers slots 0 to k, a newly
     * committed slot k+1 is acknowledged on the next pass. */
    region = scan_prepare(4);
    scan_commit(&region, 0, 0); scan_commit(&region, 1, 0);
    scan_pass("later_eligible", 1, 2, 0, 0, 1);
    scan_pass("later_eligible", 1, 2, 1, 1, 2);
    scan_pass("later_eligible", 2, 2, 2, N, 2);
    scan_commit(&region, 2, 0);
    scan_pass("later_eligible", 1, 2, 2, 2, 3);
    scan_pass("later_eligible", 1, 1, 3, N, 3);
    scan_commit(&region, 3, 0);
    scan_pass("later_eligible", 1, 2, 3, 3, 4);
    scan_pass("later_eligible", 0, 0, N, N, 4);
    scan_finish("later_eligible", &region, acknowledgement, detail);

    /* A shared acknowledgement word this worker did not store is skipped as
     * today but never advances the prefix. */
    region = scan_prepare(2);
    scan_commit(&region, 0, 0);
    atomic_store_explicit(&pw_authority_inbound(region.host, 0)->acknowledged, R, memory_order_release);
    scan_commit(&region, 1, 0);
    scan_pass("foreign_acknowledgement", 2, 4, 0, 1, 0);
    scan_pass("foreign_acknowledgement", 2, 4, 0, N, 0);
    acknowledgement[0] = R; acknowledgement[1] = A; detail[0] = 0; detail[1] = 0;
    scan_finish("foreign_acknowledgement", &region, acknowledgement, detail);

    /* prepare_authority reset: a fresh region after a completed prefix starts
     * at 0 with a cleared local record (scan_prepare asserts both), so slots
     * above a new acknowledgement are visited again. */
    region = scan_prepare(4);
    for (unsigned i = 0; i < 4; i++) scan_commit(&region, i, 0);
    for (unsigned k = 0; k < 4; k++) scan_pass("reset_first", 1, 2, k, k, k + 1);
    for (unsigned i = 0; i < 4; i++) { acknowledgement[i] = A; detail[i] = 0; }
    scan_finish("reset_first", &region, acknowledgement, detail);
    require(inbound_acknowledged_prefix == 4, "first region left a completed prefix");
    region = scan_prepare(4);
    scan_commit(&region, 0, 0);
    scan_pass("reset_second", 1, 2, 0, 0, 1);
    scan_pass("reset_second", 3, 3, 1, N, 1);
    acknowledgement[0] = A;
    for (unsigned i = 1; i < 4; i++) { acknowledgement[i] = 0; detail[i] = 0; }
    scan_finish("reset_second", &region, acknowledgement, detail);
    puts("inbound scan starts at this worker's completed prefix; selection, acknowledgement and settlement unchanged");
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
    scan_scenarios();
    g_setup=NULL;
    handoff_lifetimes();
    return 0;
}
