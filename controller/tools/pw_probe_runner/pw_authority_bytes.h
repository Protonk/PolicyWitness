/* Shared bounded bearer storage and clearing; no declaration channel. */
#ifndef PW_AUTHORITY_BYTES_H
#define PW_AUTHORITY_BYTES_H
#include <stddef.h>
#define PW_EXTENSION_TOKEN_BYTES 16384u
#define PW_EXTENSION_PATH_BYTES 1024u
#define PW_EXTENSION_AUTHORITY_READ 0u
#define PW_EXTENSION_AUTHORITY_READ_WRITE 1u
static inline void pw_extension_erase(void *bytes, size_t length) {
    volatile unsigned char *p = bytes;
    while (length--) *p++ = 0;
}
#endif
