/* Transient authority-bearing channel. Never copy this mapping to evidence. */
#ifndef PW_EXTENSION_CHANNEL_H
#define PW_EXTENSION_CHANNEL_H
#include <stdint.h>
#include <stddef.h>
#include <stdatomic.h>
#define PW_EXTENSION_MAGIC 0x50574558u
#define PW_EXTENSION_TOKEN_BYTES 16384u
#define PW_EXTENSION_PATH_BYTES 1024u
#define PW_EXTENSION_CHANNEL_BYTES 17472u
#define PW_EXTENSION_ISSUER_WAIT_MS 5000u
/* Host initializes magic/path. Issuer writes result, publishes completed last,
 * and exits. The host must reap the issuer before admitting token delivery.
 * Worker reads only a complete, bounded token and erases it after its consume
 * decision and every ordinary departure. The host separately erases its channel
 * on every exit. Fatal termination does not promise worker erasure.
 * Native call boundary is a separate publication, not proof of native entry. */
typedef struct {
    uint32_t magic;
    _Atomic uint32_t call_boundary;
    _Atomic uint32_t completed;
    uint32_t status; /* 1 issued, 2 native NULL, 3 oversized, 4 API unavailable */
    int32_t saved_errno;
    uint32_t token_length; /* excludes NUL; not a token identifier */
    uint32_t pid, uid, euid, gid, egid;
    uint8_t reserved[20];
    char target[PW_EXTENSION_PATH_BYTES];
    char token[PW_EXTENSION_TOKEN_BYTES];
} pw_extension_channel_t;
_Static_assert(sizeof(pw_extension_channel_t) == PW_EXTENSION_CHANNEL_BYTES, "extension channel size");
_Static_assert(offsetof(pw_extension_channel_t, target) == 64, "extension path offset");
_Static_assert(offsetof(pw_extension_channel_t, token) == 1088, "extension token offset");
static inline void pw_extension_erase(void *bytes, size_t length) {
    volatile unsigned char *p = bytes;
    while (length--) *p++ = 0;
}
#endif
