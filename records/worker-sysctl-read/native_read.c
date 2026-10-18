/* Investigation equipment, not a PolicyWitness worker or policy experiment.
 * Reports lengths and sentinel/canary observations; never emits sysctl values. */
#include <sys/types.h>
#include <sys/sysctl.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { max_capacity = 1024 * 1024, guard = 32 };

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    for (const char *p = argv[1]; *p; ++p)
        if (!((*p >= 'a' && *p <= 'z') || (*p >= '0' && *p <= '9') ||
              *p == '.' || *p == '_')) return 2;
    int size_only = !strcmp(argv[2], "size");
    if (!size_only && strcmp(argv[2], "read")) return 2;
    char *end = NULL;
    unsigned long capacity = strtoul(argv[3], &end, 10);
    if (!*argv[3] || *end || capacity > max_capacity) return 2;
    /* Allocate even for size-only, keeping this equipment's setup uniform.
     * A non-NULL zero-capacity read remains distinct from a size-only query. */
    unsigned char *allocation = malloc(capacity + 2 * guard);
    if (!allocation) return 3;
    memset(allocation, 0xa5, capacity + 2 * guard);
    unsigned char *buffer = allocation + guard;
    size_t returned = capacity;
    errno = 0;
    int rc = sysctlbyname(argv[1], size_only ? NULL : buffer, &returned, NULL, 0);
    int native_errno = errno;
    size_t changed = 0;
    int canaries_ok = 1;
    for (size_t i = 0; i < capacity; ++i) changed += buffer[i] != 0xa5;
    for (size_t i = 0; i < guard; ++i)
        if (allocation[i] != 0xa5 || buffer[capacity + i] != 0xa5) canaries_ok = 0;
    printf("{\"name\":\"%s\",\"mode\":\"%s\",\"buffer_is_null\":%s,"
           "\"capacity_argument\":%lu,\"returned_length\":%zu,\"rc\":%d,"
           "\"errno_after_call\":%d,\"bytes_differing_from_sentinel\":%zu,"
           "\"canaries_ok\":%s}\n", argv[1], argv[2], size_only ? "true" : "false",
           capacity, returned, rc, native_errno, changed, canaries_ok ? "true" : "false");
    free(allocation);
    return 0;
}
