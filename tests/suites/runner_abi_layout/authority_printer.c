#include <stdio.h>
#include "pw_authority_region.h"
#define OFFSET(name, type, member) printf(#name "=%zu\n", offsetof(type, member))
int main(void) {
    printf("magic=%u\n", PW_AUTHORITY_MAGIC);
    printf("headerBytes=%u\n", PW_AUTHORITY_HEADER_BYTES);
    printf("slotHeaderBytes=%u\n", PW_AUTHORITY_SLOT_HEADER_BYTES);
    printf("slotBytes=%zu\n", sizeof(pw_authority_slot_t));
    printf("maxInbound=%u\n", PW_AUTHORITY_MAX_INBOUND);
    printf("maxOutbound=%u\n", PW_AUTHORITY_MAX_OUTBOUND);
    printf("maxTransfers=%u\n", PW_AUTHORITY_MAX_TRANSFERS);
    printf("maxHandles=%u\n", PW_AUTHORITY_MAX_HANDLES);
    printf("identityBytes=%u\n", PW_AUTHORITY_IDENTITY_BYTES);
    printf("exchangeWaitMs=%u\n", PW_AUTHORITY_EXCHANGE_WAIT_MS);
    printf("familyFile=%u\n", PW_AUTHORITY_FAMILY_FILE);
    printf("tokenBytes=%u\n", PW_EXTENSION_TOKEN_BYTES);
    OFFSET(magicOffset, pw_authority_region_t, magic);
    OFFSET(identityOffset, pw_authority_region_t, identity);
    OFFSET(actorIndexOffset, pw_authority_region_t, actor_index);
    OFFSET(sessionNonceOffset, pw_authority_region_t, session_nonce);
    OFFSET(inboundCountOffset, pw_authority_region_t, inbound_count);
    OFFSET(outboundCountOffset, pw_authority_region_t, outbound_count);
    OFFSET(transferCellsOffset, pw_authority_region_t, transfers);
    printf("transferCellBytes=%zu\n", sizeof(pw_authority_transfer_t));
    OFFSET(transferOperationOffset, pw_authority_transfer_t, operation_plus_one);
    OFFSET(transferRequestOffset, pw_authority_transfer_t, requested);
    OFFSET(transferAckOffset, pw_authority_transfer_t, acknowledged);
    OFFSET(transferDetailOffset, pw_authority_transfer_t, detail);
    OFFSET(slotsOffset, pw_authority_region_t, slots);
    OFFSET(slotMagicOffset, pw_authority_slot_t, magic);
    OFFSET(slotFamilyOffset, pw_authority_slot_t, family);
    OFFSET(slotWriterActorOffset, pw_authority_slot_t, writer_actor);
    OFFSET(slotOperationIndexOffset, pw_authority_slot_t, operation_index);
    OFFSET(slotResourceIndexOffset, pw_authority_slot_t, resource_index);
    OFFSET(slotTokenLengthOffset, pw_authority_slot_t, token_length);
    OFFSET(slotCommittedOffset, pw_authority_slot_t, committed);
    OFFSET(slotAcknowledgedOffset, pw_authority_slot_t, acknowledged);
    OFFSET(slotRejectDetailOffset, pw_authority_slot_t, reject_detail);
    OFFSET(slotSettledOffset, pw_authority_slot_t, settled);
    OFFSET(slotTokenOffset, pw_authority_slot_t, token);
    return 0;
}
