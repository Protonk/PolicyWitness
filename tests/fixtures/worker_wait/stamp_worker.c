/*
 * stamp_worker.c — the production worker (pw_probe_runner.c, included below)
 * with its wait-measurement seams defined to store into the stamp page laid
 * out in pww_stamp_page.h. Test equipment only. The binary reports the
 * production abi_identity because that identity is a digest of the production
 * sources, not of this wrapper: it is not the production worker, and records
 * must name its actual bytes and substitution provenance.
 *
 * Before application, inside the clock-setup seam (after map_region, the
 * header checks and prepare_authority, before any policy byte), the wrapper
 * calls the real mach_timebase_info, then writes both stamp pages and
 * initializes the header. When the host requested a compiled-profile capture,
 * whose bytes contain the stamp page, it writes only the header with the
 * capture-refused flag and stamps nothing.
 *
 * After application the seams only read mach_continuous_time directly and
 * store into the pre-written page: no allocation, sleep, I/O or new resource.
 * pw_clock_sample is never called from a seam, so the worker's clock history
 * and sticky fault are unchanged. Decision seams (*_LOADED, inbound observed)
 * record the pass's existing sample; a new read follows only a production
 * store, and the wait's pass count is appended with that same read. These
 * in-loop stores and reads still change timing; see README.md.
 */
#include <mach/mach_time.h>
#include <stdatomic.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>

#include "pww_stamp_page.h"

static uint64_t pww_continuous_read(uint32_t stage);
static kern_return_t pww_timebase_info(mach_timebase_info_data_t *info);
static void pww_stamp(uint32_t event, uint32_t phase, uint32_t aux);
static void pww_stamp_waited(uint32_t event, uint32_t phase, uint32_t aux, uint32_t passes_event);
static void pww_loaded(uint32_t event, uint32_t phase, uint32_t value, uint64_t now);
static void pww_scan_pass(void);
static void pww_scan_visit(uint32_t index);
static uint32_t pww_scan_load(_Atomic uint32_t *word);
static void pww_inbound_observed(void);
static void pww_attempt_published(const pw_shm_slot_t *slot);

#define PW_CONTINUOUS_READ(stage) pww_continuous_read((uint32_t)(stage))
#define PW_TIMEBASE_INFO(info) pww_timebase_info(info)
#define PW_APPLIED_PUBLISHED(hdr) ((void)(hdr), pww_stamp(PWW_EVENT_APPLIED, PWW_PHASE_NONE, 0u))
#define PW_PROCEED_ARRIVED(phase) pww_stamp(PWW_EVENT_PROCEED_ARRIVED, (uint32_t)(phase), 0u)
#define PW_PROCEED_ORDINAL_LOADED(phase, ordinal, now) \
    pww_loaded(PWW_EVENT_PROCEED_ORDINAL_LOADED, (uint32_t)(phase), (uint32_t)(ordinal), (uint64_t)(now))
#define PW_PROCEED_ACKNOWLEDGED(phase, ordinal) \
    pww_stamp_waited(PWW_EVENT_PROCEED_ACKNOWLEDGED, (uint32_t)(phase), (uint32_t)(ordinal), PWW_EVENT_PROCEED_PASSES)
#define PW_ACTIVATION_LOADED(visit, ordinal, now) \
    pww_loaded(PWW_EVENT_ACTIVATION_LOADED, (uint32_t)(visit), (uint32_t)(ordinal), (uint64_t)(now))
#define PW_ACTIVATION_STORED(visit, ordinal) \
    pww_stamp_waited(PWW_EVENT_ACTIVATION_STORED, (uint32_t)(visit), (uint32_t)(ordinal), PWW_EVENT_ACTIVATION_PASSES)
#define PW_EXCHANGE_ANSWERED(slot_index, value) \
    pww_stamp_waited(PWW_EVENT_EXCHANGE_ANSWERED, (uint32_t)(slot_index), (uint32_t)(value), PWW_EVENT_EXCHANGE_PASSES)
#define PW_INBOUND_SCAN_PASS() pww_scan_pass()
#define PW_INBOUND_SCAN_VISIT(index) pww_scan_visit((uint32_t)(index))
#define PW_INBOUND_SCAN_LOAD(word) pww_scan_load(word)
#define PW_INBOUND_OBSERVE(slot) ((void)(slot), pww_inbound_observed())
#define PW_INBOUND_ACKNOWLEDGED(index, problem) \
    pww_stamp(PWW_EVENT_INBOUND_ACKNOWLEDGED, (uint32_t)(index), (uint32_t)(problem))
#define PW_ATTEMPT_PUBLISHED(slot) pww_attempt_published(slot)
#define PW_TERMINAL_PUBLISHED(hdr) ((void)(hdr), pww_stamp(PWW_EVENT_TERMINAL_PUBLISHED, PWW_PHASE_NONE, 0u))
#include "../../../controller/tools/pw_probe_runner/pw_probe_runner.c"

_Static_assert(PW_CLOCK_EXCHANGE_OBSERVE + 1 == PWW_STAGE_COUNT, "stage registers cover enum pw_clock_phase");
_Static_assert(sizeof(pw_clock_stage_names) / sizeof(*pw_clock_stage_names) == PWW_STAGE_COUNT,
               "stage registers cover every named stage");
_Static_assert(PW_AUTHORITY_MAX_INBOUND + 1u == PWW_HISTOGRAM_BUCKETS, "histogram covers 0..max inbound visits");

/* NULL until initialized, and forever when stamping is refused. */
static pww_stamp_page_t *pww_page;
static uint64_t pww_origin_raw;
static uint32_t pww_origin_read;
static uint32_t pww_last_stage = PWW_PHASE_NONE;
static uint64_t pww_last_raw;
/* The current scan pass: caller role (0 unknown, 1 activation, 2 exchange),
 * last visited index and visit count for the histogram. */
static uint32_t pww_scan_role, pww_scan_index = PWW_PHASE_NONE, pww_pass_visits;
/* Observe reads since the current proceed, activation and exchange wait's
 * start read, indexed by pass event - PWW_EVENT_PROCEED_PASSES. */
static uint32_t pww_wait_passes[3];

/* Per-wait state for the bounded *_LOADED records. Each phase or visit index
 * has exactly one wait in a worker's life, so a new index is a new wait. */
typedef struct {
    uint32_t phase, value, previous_recorded;
    uint64_t previous_now;
} pww_wait_t;
static pww_wait_t pww_proceed_wait = {PWW_PHASE_NONE, 0u, 0u, 0u};
static pww_wait_t pww_activation_wait = {PWW_PHASE_NONE, 0u, 0u, 0u};

/* Single writer: the worker's only thread. The count is release-published
 * after each record so a reader bounded by it never decodes a partial one. */
static void pww_append(uint32_t event, uint32_t phase, uint32_t aux, uint64_t raw) {
    pww_stamp_page_t *page = pww_page;
    uint32_t count = atomic_load_explicit(&page->event_count, memory_order_relaxed);
    if (count >= PWW_EVENT_CAPACITY) { page->flags |= PWW_FLAG_EVENT_OVERFLOW; return; }
    page->events[count] = (pww_stamp_t){event, phase, aux, 0u, raw};
    atomic_store_explicit(&page->event_count, count + 1u, memory_order_release);
}

/* The worker_start read precedes the mapping, so it is kept here and entered
 * into the page at initialization. Returns the identical value it read. */
static uint64_t pww_continuous_read(uint32_t stage) {
    uint64_t raw = mach_continuous_time();
    if (stage == PW_CLOCK_WORKER_START && !pww_origin_read) { pww_origin_raw = raw; pww_origin_read = 1u; }
    pww_last_stage = stage;
    pww_last_raw = raw;
    switch (stage) {
    case PW_CLOCK_PROCEED_START: pww_wait_passes[0] = 0u; break;
    case PW_CLOCK_PROCEED_OBSERVE: pww_wait_passes[0]++; break;
    case PW_CLOCK_ACTIVATE_START: pww_wait_passes[1] = 0u; break;
    case PW_CLOCK_ACTIVATE_OBSERVE: pww_wait_passes[1]++; break;
    case PW_CLOCK_EXCHANGE_START: pww_wait_passes[2] = 0u; break;
    case PW_CLOCK_EXCHANGE_OBSERVE: pww_wait_passes[2]++; break;
    default: break;
    }
    pww_stamp_page_t *page = pww_page;
    if (page && stage < PWW_STAGE_COUNT) {
        pww_stage_regs_t *regs = &page->stages[stage];
        if (!regs->count) regs->first_raw = raw;
        regs->last_raw = raw;
        regs->count++;
    }
    return raw;
}

static void pww_initialize(const mach_timebase_info_data_t *info) {
    if (!g_hdr || pww_page) return;
    pww_stamp_page_t *page = (pww_stamp_page_t *)((unsigned char *)g_hdr + PWW_STAMP_OFFSET);
    const int refused = g_hdr->capture_requested == 1u;
    /* Writing both pages here keeps first-touch faults out of the timed paths. */
    if (!refused) memset(page, 0, PWW_STAMP_BYTES);
    page->magic = PWW_STAMP_MAGIC;
    page->version = PWW_STAMP_VERSION;
    page->numer = info->numer;
    page->denom = info->denom;
    page->origin_raw = pww_origin_read ? pww_origin_raw : 0u;
    page->pid = (uint32_t)getpid();
    page->reserved0 = 0u;
    atomic_store_explicit(&page->event_count, 0u, memory_order_relaxed);
    if (refused) { page->flags = PWW_FLAG_INITIALIZED | PWW_FLAG_CAPTURE_REFUSED; return; }
    page->flags = PWW_FLAG_INITIALIZED;
    pww_page = page;
    if (pww_origin_read) {
        page->stages[PW_CLOCK_WORKER_START] = (pww_stage_regs_t){1u, pww_origin_raw, pww_origin_raw};
        pww_append(PWW_EVENT_WORKER_START, PWW_PHASE_NONE, 0u, pww_origin_raw);
    }
}

static kern_return_t pww_timebase_info(mach_timebase_info_data_t *info) {
    kern_return_t kr = mach_timebase_info(info);
    pww_initialize(info);
    return kr;
}

/* One read after the production store that precedes the seam. */
static void pww_stamp(uint32_t event, uint32_t phase, uint32_t aux) {
    if (!pww_page) return;
    uint64_t raw = mach_continuous_time();
    pww_append(event, phase, aux, raw);
}

/* The ending store's record, then the wait's pass count under the same raw.
 * An exchange answered on its first load has read no observe sample and
 * counts as one pass. */
static void pww_stamp_waited(uint32_t event, uint32_t phase, uint32_t aux, uint32_t passes_event) {
    if (!pww_page) return;
    uint64_t raw = mach_continuous_time();
    uint32_t passes = pww_wait_passes[passes_event - PWW_EVENT_PROCEED_PASSES];
    if (passes_event == PWW_EVENT_EXCHANGE_PASSES && !passes) passes = 1u;
    pww_append(event, phase, aux, raw);
    pww_append(passes_event, phase, passes, raw);
}

/* No read: `now` is the pass's validated origin-relative sample. Records the
 * wait's first pass, and each changed value with the pass before it. */
static void pww_loaded(uint32_t event, uint32_t phase, uint32_t value, uint64_t now) {
    pww_wait_t *wait = event == PWW_EVENT_PROCEED_ORDINAL_LOADED ? &pww_proceed_wait : &pww_activation_wait;
    const int first = wait->phase != phase;
    const int changed = !first && wait->value != value;
    if (pww_page) {
        if (changed && !wait->previous_recorded)
            pww_append(event, phase, wait->value, wait->previous_now + pww_origin_raw);
        if (first || changed) pww_append(event, phase, value, now + pww_origin_raw);
    }
    *wait = (pww_wait_t){phase, value, (uint32_t)(first || changed), now};
}

/* Both callers sample the clock earlier in the same pass, so the last stage
 * read names the wait that is servicing inbound slots. */
static void pww_scan_pass(void) {
    pww_scan_role = pww_last_stage == PW_CLOCK_ACTIVATE_OBSERVE ? 1u
                  : pww_last_stage == PW_CLOCK_EXCHANGE_OBSERVE ? 2u : 0u;
    pww_scan_index = PWW_PHASE_NONE;
    pww_pass_visits = 0u;
    pww_stamp_page_t *page = pww_page;
    if (!page) return;
    if (!pww_scan_role) { page->flags |= PWW_FLAG_SCAN_ROLE_UNKNOWN; return; }
    if (pww_scan_role == 1u) page->scan.passes_activation++;
    else page->scan.passes_exchange++;
    page->scan.visits_histogram[0]++;
}

static void pww_scan_visit(uint32_t index) {
    pww_scan_index = index;
    pww_stamp_page_t *page = pww_page;
    if (!page || !pww_scan_role) return;
    if (pww_scan_role == 1u) page->scan.visits_activation++;
    else page->scan.visits_exchange++;
    if (pww_pass_visits < PWW_HISTOGRAM_BUCKETS - 1u) {
        page->scan.visits_histogram[pww_pass_visits]--;
        page->scan.visits_histogram[++pww_pass_visits]++;
    }
}

/* Exactly the production scan's acquire load; the count follows it. */
static uint32_t pww_scan_load(_Atomic uint32_t *word) {
    uint32_t value = atomic_load_explicit(word, memory_order_acquire);
    pww_stamp_page_t *page = pww_page;
    if (page && pww_scan_role) {
        if (pww_scan_role == 1u) page->scan.loads_activation++;
        else page->scan.loads_exchange++;
    }
    return value;
}

/* Between eligibility and the acknowledgement store: no read. raw is the
 * pass's preceding sample and aux names its clock stage. */
static void pww_inbound_observed(void) {
    if (pww_page) pww_append(PWW_EVENT_INBOUND_OBSERVED, pww_scan_index, pww_last_stage, pww_last_raw);
}

static void pww_attempt_published(const pw_shm_slot_t *slot) {
    if (!pww_page) return;
    uint64_t raw = mach_continuous_time();
    uintptr_t first = (uintptr_t)g_hdr + PW_SHM_HEADER_BYTES;
    pww_append(PWW_EVENT_ATTEMPT_PUBLISHED, (uint32_t)(((uintptr_t)slot - first) / PW_SHM_SLOT_BYTES), 0u, raw);
}
