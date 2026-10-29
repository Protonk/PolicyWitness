#include <stdio.h>
#include "pw_extension_channel.h"
#define OFFSET(name, member) printf(#name "=%zu\n", offsetof(pw_extension_channel_t, member))
int main(void) {
    printf("magic=%u\n", PW_EXTENSION_MAGIC);
    printf("tokenBytes=%u\n", PW_EXTENSION_TOKEN_BYTES);
    printf("pathBytes=%u\n", PW_EXTENSION_PATH_BYTES);
    printf("channelBytes=%zu\n", sizeof(pw_extension_channel_t));
    printf("issuerWaitMs=%u\n", PW_EXTENSION_ISSUER_WAIT_MS);
    OFFSET(magicOffset, magic);
    OFFSET(callBoundaryOffset, call_boundary);
    OFFSET(completedOffset, completed);
    OFFSET(statusOffset, status);
    OFFSET(errnoOffset, saved_errno);
    OFFSET(tokenLengthOffset, token_length);
    OFFSET(pidOffset, pid);
    OFFSET(uidOffset, uid);
    OFFSET(euidOffset, euid);
    OFFSET(gidOffset, gid);
    OFFSET(egidOffset, egid);
    OFFSET(authorityOffset, authority);
    OFFSET(targetOffset, target);
    OFFSET(tokenOffset, token);
    return 0;
}
