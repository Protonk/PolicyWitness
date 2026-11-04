/* Transient authority region: one per actor, mapped by the host and by that
 * actor only. Never copy this mapping to evidence; never pass its descriptor
 * to a validator or another actor. Tokens live here only between a native
 * issue result and host custody (outbound) or between host delivery and the
 * recipient's consume (inbound); both sides erase at last declared use and on
 * every ordinary exit. */
#ifndef PW_AUTHORITY_REGION_H
#define PW_AUTHORITY_REGION_H
#include <stdint.h>
#include <stddef.h>
#include <stdatomic.h>
#include "pw_extension_channel.h"

#define PW_AUTHORITY_MAGIC 0x50574155u          /* 'PWAU' */
#define PW_AUTHORITY_HEADER_BYTES 128u
#define PW_AUTHORITY_SLOT_HEADER_BYTES 64u
#define PW_AUTHORITY_SLOT_BYTES (PW_AUTHORITY_SLOT_HEADER_BYTES + PW_EXTENSION_TOKEN_BYTES) /* 16448 */
#define PW_AUTHORITY_MAX_INBOUND 64u
#define PW_AUTHORITY_MAX_HANDLES 64u
#define PW_AUTHORITY_EXCHANGE_WAIT_MS 5000u
#define PW_AUTHORITY_IDENTITY_BYTES 32u
#define PW_AUTHORITY_REGION_BYTES(inbound) \
    ((size_t)PW_AUTHORITY_HEADER_BYTES + ((size_t)(inbound) + 1u) * PW_AUTHORITY_SLOT_BYTES)
#define PW_AUTHORITY_FAMILY_FILE 1u

/* Slot acknowledgement by its reader (host for outbound, recipient actor for
 * inbound) and the reasons a committed slot is rejected. */
enum { PW_AUTHORITY_ACK_NONE = 0, PW_AUTHORITY_ACK_ACCEPTED = 1, PW_AUTHORITY_ACK_REJECTED = 2 };
enum {
    PW_AUTHORITY_REJECT_MAGIC = 1, PW_AUTHORITY_REJECT_FAMILY = 2, PW_AUTHORITY_REJECT_OWNER = 3,
    PW_AUTHORITY_REJECT_ORDINAL = 4, PW_AUTHORITY_REJECT_LENGTH = 5, PW_AUTHORITY_REJECT_TERMINATOR = 6,
    PW_AUTHORITY_REJECT_INTERIOR_NUL = 7, PW_AUTHORITY_REJECT_RESOURCE = 8
};
/* The host's answer to a source actor's transfer request. None of these is a
 * native result; none carries an errno. */
enum {
    PW_TRANSFER_ACK_NONE = 0, PW_TRANSFER_ACK_DELIVERED = 1, PW_TRANSFER_ACK_CUSTODY_UNAVAILABLE = 2,
    PW_TRANSFER_ACK_RECIPIENT_REJECTED = 3, PW_TRANSFER_ACK_RECIPIENT_TIMEOUT = 4,
    PW_TRANSFER_ACK_RECIPIENT_UNAVAILABLE = 5, PW_TRANSFER_ACK_REQUEST_INVALID = 6,
    /* Worker-side outcomes of the request wait: no host answer within the
     * exchange allowance, or an unusable clock sample. */
    PW_TRANSFER_ACK_HOST_TIMEOUT = 7, PW_TRANSFER_ACK_CLOCK_FAULT = 8,
    /* The recipient accepted bytes that no longer equal the host's custody copy. */
    PW_TRANSFER_ACK_COPY_MISMATCH = 9
};

/* One bounded token publication. The writer fills family, writer_actor,
 * operation_index, resource_index, the bytes and token_length, then
 * release-publishes committed. The reader validates every field before
 * touching the bytes and release-publishes acknowledged. */
typedef struct {
    uint32_t magic;
    uint32_t family;
    uint32_t writer_actor;         /* outbound: the issuing actor; inbound: the host on the source's behalf (source index) */
    uint32_t operation_index;      /* source actor's slot index of the issue or transfer */
    uint32_t resource_index;       /* token index (outbound) or delivery index (inbound) */
    uint32_t token_length;         /* excludes the terminator; 1..PW_EXTENSION_TOKEN_BYTES-1 */
    _Atomic uint32_t committed;
    _Atomic uint32_t acknowledged; /* PW_AUTHORITY_ACK_* */
    uint32_t reject_detail;        /* PW_AUTHORITY_REJECT_* when rejected */
    uint8_t reserved[28];
    char token[PW_EXTENSION_TOKEN_BYTES];
} pw_authority_slot_t;
_Static_assert(sizeof(pw_authority_slot_t) == PW_AUTHORITY_SLOT_BYTES, "authority slot size");
_Static_assert(offsetof(pw_authority_slot_t, committed) == 24, "authority slot commit offset");
_Static_assert(offsetof(pw_authority_slot_t, token) == PW_AUTHORITY_SLOT_HEADER_BYTES, "authority token offset");

/* Region header. The host writes identity, nonce, actor index and inbound
 * count before spawn; the actor validates identity and actor index against
 * its evidence header before any token byte is read. The nonce is a host
 * session label, not an independently checked authentication value.
 * transfer_request names the source actor's slot index + 1; transfer_ack
 * and transfer_detail answer it. Inbound writer/operation/resource fields
 * are assigned before spawn and snapshotted privately by the recipient. */
typedef struct {
    uint32_t magic;
    uint8_t identity[PW_AUTHORITY_IDENTITY_BYTES];  /* the worker source identity */
    uint32_t actor_index;
    uint64_t session_nonce;
    uint32_t inbound_count;
    _Atomic uint32_t transfer_request;
    _Atomic uint32_t transfer_ack;    /* PW_TRANSFER_ACK_* */
    uint32_t transfer_detail;         /* delivery index on delivery; rejection detail otherwise */
    uint8_t reserved[64];
    pw_authority_slot_t outbound;
    pw_authority_slot_t inbound[];    /* inbound_count entries */
} pw_authority_region_t;
_Static_assert(offsetof(pw_authority_region_t, actor_index) == 36, "authority actor offset");
_Static_assert(offsetof(pw_authority_region_t, session_nonce) == 40, "authority nonce offset");
_Static_assert(offsetof(pw_authority_region_t, inbound_count) == 48, "authority inbound count offset");
_Static_assert(offsetof(pw_authority_region_t, transfer_request) == 52, "authority transfer request offset");
_Static_assert(offsetof(pw_authority_region_t, transfer_ack) == 56, "authority transfer ack offset");
_Static_assert(offsetof(pw_authority_region_t, transfer_detail) == 60, "authority transfer detail offset");
_Static_assert(offsetof(pw_authority_region_t, outbound) == PW_AUTHORITY_HEADER_BYTES, "authority outbound offset");

/* Framing validation shared by both readers. Returns 0 when the committed
 * slot carries one bounded, NUL-terminated token of the expected family;
 * otherwise a PW_AUTHORITY_REJECT_* reason. The bytes are read only after
 * the header fields agree. */
static inline uint32_t pw_authority_frame_problem(const pw_authority_slot_t *slot, uint32_t family) {
    if (slot->magic != PW_AUTHORITY_MAGIC) return PW_AUTHORITY_REJECT_MAGIC;
    if (slot->family != family) return PW_AUTHORITY_REJECT_FAMILY;
    uint32_t n = slot->token_length;
    if (n == 0u || n >= PW_EXTENSION_TOKEN_BYTES) return PW_AUTHORITY_REJECT_LENGTH;
    if (slot->token[n] != 0) return PW_AUTHORITY_REJECT_TERMINATOR;
    for (uint32_t i = 0; i < n; i++) if (slot->token[i] == 0) return PW_AUTHORITY_REJECT_INTERIOR_NUL;
    return 0;
}
/* The full check the host applies to an outbound publication: framing plus
 * the writer and the indexes the plan assigned to that issue. */
static inline uint32_t pw_authority_slot_problem(const pw_authority_slot_t *slot, uint32_t family,
                                                 uint32_t writer_actor, uint32_t operation_index,
                                                 uint32_t resource_index) {
    uint32_t problem = pw_authority_frame_problem(slot, family);
    if (problem) return problem;
    if (slot->writer_actor != writer_actor) return PW_AUTHORITY_REJECT_OWNER;
    if (slot->operation_index != operation_index) return PW_AUTHORITY_REJECT_ORDINAL;
    if (slot->resource_index != resource_index) return PW_AUTHORITY_REJECT_RESOURCE;
    return 0;
}
#endif
