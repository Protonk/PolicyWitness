#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <CommonCrypto/CommonDigest.h>
/* Private libsandbox API; layout as commonly reported: type, then bytecode pointer and length. */
struct sb_profile { uint32_t type; uint32_t pad; const void *data; size_t len; };
struct sb_profile *sandbox_compile_string(const char *src, void *params, char **err);
void sandbox_free_profile(struct sb_profile *);
int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    FILE *f = fopen(argv[i], "r"); if (!f) { perror(argv[i]); continue; }
    static char buf[1<<20]; size_t n = fread(buf, 1, sizeof buf - 1, f); buf[n] = 0; fclose(f);
    char *err = NULL;
    struct sb_profile *p = sandbox_compile_string(buf, NULL, &err);
    if (!p) { printf("%s\tcompile_failed\t%s\n", argv[i], err ? err : "?"); continue; }
    unsigned char md[32]; CC_SHA256(p->data, (CC_LONG)p->len, md);
    printf("%s\ttype=%u\tlen=%zu\tsha256=", argv[i], p->type, p->len);
    for (int k = 0; k < 8; k++) printf("%02x", md[k]);
    printf("...\n");
    sandbox_free_profile(p);
  }
  return 0;
}
