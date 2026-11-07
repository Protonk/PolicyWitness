/*
 * pww_stamp_page.h — layout of the worker-wait stamp page that the stamp
 * worker (stamp_worker.c) writes into the evidence region and the pilot
 * reader decodes from the host's copy. Test equipment only: no production
 * source includes this header and nothing here is a wire or evidence field.
 *
 * Placement: region pages 201 and 202 (16 KiB pages), wholly inside the
 * compiled-profile capture bytes, which the production worker writes only
 * when the host requests a capture. Page 200 belongs to the first-touch
 * control and is never written here. A requested capture whose bytecode is
 * longer than PWW_STAMP_OFFSET - capture payload start (670,832 bytes) would
 * overwrite this page; the stamp worker therefore refuses to stamp when a
 * capture is requested and records only the refusal header.
 *
 * Byte layout for readers (all integers little-endian, no padding;
 * Python struct formats in brackets, offsets from PWW_STAMP_OFFSET):
 *
 *   offset  bytes  field                                 [struct]
 *        0      4  magic        0x50575753 ('PWWS')       '<I'
 *        4      4  version      1                         '<I'
 *        8      4  numer        mach_timebase_info        '<I'
 *       12      4  denom        mach_timebase_info        '<I'
 *       16      8  origin_raw   worker_start read, ticks  '<Q'
 *       24      4  flags        PWW_FLAG_* below          '<I'
 *       28      4  pid          getpid() before apply     '<I'
 *       32      4  event_count  release-published         '<I'
 *       36      4  reserved0    0                         '<I'
 *         (header: '<4IQ4I', 40 bytes)
 *       40    240  stages[10], 24 bytes each              '<3Q' per stage
 *                    +0 count, +8 first_raw, +16 last_raw (every read
 *                    through the seam, including one validation rejects)
 *                    stage index = enum pw_clock_phase:
 *                    0 worker_start 1 proceed_start 2 proceed_observe
 *                    3 exec_admit 4 exec_observe 5 exec_reap
 *                    6 activate_start 7 activate_observe
 *                    8 exchange_start 9 exchange_observe
 *      280      8  scan.passes_activation                 '<Q'
 *      288      8  scan.passes_exchange                   '<Q'
 *      296      8  scan.visits_activation                 '<Q'
 *      304      8  scan.visits_exchange                   '<Q'
 *      312      8  scan.loads_activation                  '<Q'
 *      320      8  scan.loads_exchange                    '<Q'
 *      328    520  scan.visits_histogram[65]              '<65Q'
 *         (scan block: '<71Q', 568 bytes)
 *      848  24000  events[1000], 24 bytes each            '<4IQ' per event
 *                    +0 event, +4 phase, +8 aux, +12 reserved, +16 raw
 *    24848         end of defined bytes; the rest of the 32768 stays zero
 *
 * Reading rules:
 *  - Valid only after the worker's reap has been confirmed: stamps written
 *    after `done` or on the cancellation _exit paths are not ordered by any
 *    production publication. Decode events[0 .. event_count) only.
 *  - magic != PWW_STAMP_MAGIC or flag bit 2 clear: the page was never
 *    initialized (the worker exited before clock setup, a capture overwrote
 *    it, or the executable is not the stamp worker). Nothing is observed;
 *    zero counters on such a page are not zero counts.
 *  - Flag bit 0: a capture was requested; the header is recorded and no
 *    stamp, register or counter was written.
 *  - Flag bit 1: an append found the event array full; later events are
 *    missing and the array is a prefix.
 *  - Flag bit 3: an inbound scan pass followed a clock read that was neither
 *    activate_observe nor exchange_observe; that pass's visits and loads are
 *    in no counter.
 *  - raw values are absolute mach_continuous_time ticks, the host's
 *    continuous-clock domain; convert with numer/denom.
 *
 * Events: append order is program order in the single worker thread.
 *  1 WORKER_START            phase none; raw = origin_raw (no extra read)
 *  2 APPLIED                 phase none; read after the applied store
 *  3 PROCEED_ARRIVED         phase; read after the arrived store
 *  4 PROCEED_ORDINAL_LOADED  phase, aux=ordinal loaded; raw = that pass's
 *                            proceed_observe sample (no extra read)
 *  5 PROCEED_ACKNOWLEDGED    phase, aux=ordinal; read after proceed_observed
 *  6 ACTIVATION_LOADED       visit, aux=ordinal loaded; raw = that pass's
 *                            activate_observe sample (no extra read)
 *  7 ACTIVATION_STORED       visit, aux=ordinal; read after activation_observed
 *  8 EXCHANGE_ANSWERED       phase=attempt slot index, aux=answer; read at return
 *  9 INBOUND_OBSERVED        phase=inbound slot index, aux=clock stage of raw
 *                            (7 activate_observe, 9 exchange_observe); raw =
 *                            the same pass's preceding sample (no extra read)
 * 10 INBOUND_ACKNOWLEDGED    phase=inbound slot index, aux=problem (0 accepted);
 *                            read after the acknowledgement store
 * 11 ATTEMPT_PUBLISHED       phase=attempt slot index; read after completed store
 * 12 TERMINAL_PUBLISHED      phase none; read after the done store
 * 13 PROCEED_PASSES          phase, aux=passes in that release wait; appended
 *                            right after its PROCEED_ACKNOWLEDGED, same raw
 * 14 ACTIVATION_PASSES       visit, aux=passes in that parked wait; appended
 *                            right after its ACTIVATION_STORED, same raw
 * 15 EXCHANGE_PASSES         phase=attempt slot index, aux=passes in that
 *                            exchange wait; appended right after its
 *                            EXCHANGE_ANSWERED, same raw
 * "phase none" is UINT32_MAX.
 *
 * Pass counts are per wait, kept in the wrapper and reset by that wait's start
 * read (proceed_start, activate_start, exchange_start); they add no clock
 * read. 13 and 14 count the wait's proceed_observe or activate_observe reads,
 * one per pass including the accepting pass. 15 counts the exchange_observe
 * reads, which follow each unanswered load, and is 1 when the first load
 * returned the answer (no read): an aux of 1 does not distinguish an answer on
 * the first load from one on the second. A wait that ends without its
 * acknowledgement or answer (refusal, timeout, cutoff, cancellation) records
 * no pass event.
 *
 * Loaded events are bounded, not per pass: within one wait (one phase or
 * visit index) the first pass is recorded, and every pass whose loaded value
 * differs from the previous pass's is recorded together with that previous
 * pass. Consecutive records of one wait with different aux values therefore
 * bracket the change by two adjacent pass samples.
 *
 * Scan counters: a pass is one service_inbound_once call, attributed to the
 * caller by the last clock stage read before it. A visit is one slot index
 * examined; a load is one counted acquire load of committed or acknowledged.
 * visits_histogram[v] counts passes with v visits; 64 also holds any pass
 * with more (the production inbound bound is 64). The histogram sum equals
 * passes_activation + passes_exchange.
 */
#ifndef PWW_STAMP_PAGE_H
#define PWW_STAMP_PAGE_H

#include <stdatomic.h>
#include <stddef.h>
#include <stdint.h>

#include "pw_probe_runner_abi.h"

#define PWW_PAGE_BYTES     16384u
#define PWW_STAMP_PAGE     201u
#define PWW_STAMP_OFFSET   3293184u      /* 201 * 16384 */
#define PWW_STAMP_BYTES    32768u        /* two pages */
#define PWW_STAMP_MAGIC    0x50575753u   /* 'PWWS' */
#define PWW_STAMP_VERSION  1u
#define PWW_EVENT_CAPACITY 1000u
#define PWW_STAGE_COUNT    10u           /* enum pw_clock_phase */
#define PWW_HISTOGRAM_BUCKETS 65u
#define PWW_PHASE_NONE     UINT32_MAX

#define PWW_FLAG_CAPTURE_REFUSED   (1u << 0)
#define PWW_FLAG_EVENT_OVERFLOW    (1u << 1)
#define PWW_FLAG_INITIALIZED       (1u << 2)
#define PWW_FLAG_SCAN_ROLE_UNKNOWN (1u << 3)

enum pww_event {
    PWW_EVENT_WORKER_START = 1,
    PWW_EVENT_APPLIED = 2,
    PWW_EVENT_PROCEED_ARRIVED = 3,
    PWW_EVENT_PROCEED_ORDINAL_LOADED = 4,
    PWW_EVENT_PROCEED_ACKNOWLEDGED = 5,
    PWW_EVENT_ACTIVATION_LOADED = 6,
    PWW_EVENT_ACTIVATION_STORED = 7,
    PWW_EVENT_EXCHANGE_ANSWERED = 8,
    PWW_EVENT_INBOUND_OBSERVED = 9,
    PWW_EVENT_INBOUND_ACKNOWLEDGED = 10,
    PWW_EVENT_ATTEMPT_PUBLISHED = 11,
    PWW_EVENT_TERMINAL_PUBLISHED = 12,
    PWW_EVENT_PROCEED_PASSES = 13,
    PWW_EVENT_ACTIVATION_PASSES = 14,
    PWW_EVENT_EXCHANGE_PASSES = 15
};

typedef struct {
    uint32_t event;
    uint32_t phase;
    uint32_t aux;
    uint32_t reserved;
    uint64_t raw;
} pww_stamp_t;

typedef struct {
    uint64_t count;
    uint64_t first_raw;
    uint64_t last_raw;
} pww_stage_regs_t;

typedef struct {
    uint64_t passes_activation, passes_exchange;
    uint64_t visits_activation, visits_exchange;
    uint64_t loads_activation, loads_exchange;
    uint64_t visits_histogram[PWW_HISTOGRAM_BUCKETS];
} pww_scan_counters_t;

typedef struct {
    uint32_t magic, version;
    uint32_t numer, denom;
    uint64_t origin_raw;
    uint32_t flags;
    uint32_t pid;
    _Atomic uint32_t event_count;
    uint32_t reserved0;
    pww_stage_regs_t stages[PWW_STAGE_COUNT];
    pww_scan_counters_t scan;
    pww_stamp_t events[PWW_EVENT_CAPACITY];
} pww_stamp_page_t;

_Static_assert(PWW_STAMP_OFFSET == PWW_STAMP_PAGE * PWW_PAGE_BYTES, "stamp page index");
_Static_assert(PWW_STAMP_BYTES == 2u * PWW_PAGE_BYTES, "stamp page count");
_Static_assert(sizeof(_Atomic uint32_t) == 4u, "event_count width");
_Static_assert(sizeof(pww_stamp_t) == 24u, "event size");
_Static_assert(sizeof(pww_stage_regs_t) == 24u, "stage register size");
_Static_assert(sizeof(pww_scan_counters_t) == 568u, "scan counter size");
_Static_assert(offsetof(pww_stamp_page_t, version) == 4u, "version offset");
_Static_assert(offsetof(pww_stamp_page_t, numer) == 8u, "numer offset");
_Static_assert(offsetof(pww_stamp_page_t, denom) == 12u, "denom offset");
_Static_assert(offsetof(pww_stamp_page_t, origin_raw) == 16u, "origin offset");
_Static_assert(offsetof(pww_stamp_page_t, flags) == 24u, "flags offset");
_Static_assert(offsetof(pww_stamp_page_t, pid) == 28u, "pid offset");
_Static_assert(offsetof(pww_stamp_page_t, event_count) == 32u, "event count offset");
_Static_assert(offsetof(pww_stamp_page_t, reserved0) == 36u, "reserved offset");
_Static_assert(offsetof(pww_stamp_page_t, stages) == 40u, "stage registers offset");
_Static_assert(offsetof(pww_stamp_page_t, scan) == 280u, "scan counters offset");
_Static_assert(offsetof(pww_stamp_page_t, scan.visits_histogram) == 328u, "histogram offset");
_Static_assert(offsetof(pww_stamp_page_t, events) == 848u, "events offset");
_Static_assert(offsetof(pww_stamp_t, raw) == 16u, "event raw offset");
_Static_assert(sizeof(pww_stamp_page_t) == 24848u, "stamp page size");
_Static_assert(sizeof(pww_stamp_page_t) <= PWW_STAMP_BYTES, "stamp page fits two pages");

/* Placement inside the capture bytes and after the first-touch page (200). */
#define PWW_CAPTURE_BYTES_START                                                 \
    ((size_t)PW_SHM_HEADER_BYTES + (size_t)PW_SHM_MAX_STEPS * PW_SHM_SLOT_BYTES \
     + (size_t)PW_SHM_MAX_PARAMS * PW_SHM_PARAM_BYTES + PW_SHM_CAPTURE_HEADER_BYTES)
#define PWW_CAPTURE_BYTES_END (PWW_CAPTURE_BYTES_START + PW_SHM_CAPTURE_BYTES)
_Static_assert(PWW_STAMP_OFFSET >= PWW_CAPTURE_BYTES_START, "stamp page starts inside the capture bytes");
_Static_assert(PWW_STAMP_OFFSET + PWW_STAMP_BYTES <= PWW_CAPTURE_BYTES_END, "stamp page ends inside the capture bytes");
_Static_assert(PWW_STAMP_OFFSET >= 201u * PWW_PAGE_BYTES, "stamp page must not reach the first-touch page 200");
_Static_assert(PWW_STAMP_OFFSET - PWW_CAPTURE_BYTES_START == 670832u, "capture payload bytes before the stamp page");

#endif
