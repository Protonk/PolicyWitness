/* Test-only native call boundaries in the real C producer. */
#if defined(PW_CONTROL_CREATE)
#define sandbox_create_params pw_controlled_create
#elif defined(PW_CONTROL_SET)
#define sandbox_set_param pw_controlled_set
#else
#define sandbox_apply pw_controlled_apply
#endif
#include "pw_probe_runner.c"
#if defined(PW_CONTROL_CREATE)
void *pw_controlled_create(void) { errno = 777; return NULL; }
#elif defined(PW_CONTROL_SET)
int pw_controlled_set(void *params, const char *key, const char *value) {
    (void)params; (void)key; (void)value;
    static int calls;
    errno = 777; /* Must not be claimed as meaningful for this API. */
    return ++calls == 2 ? -23 : 0;
}
#else
int pw_controlled_apply(void *profile) {
    (void)profile;
    errno = EACCES;
    return -37;
}
#endif
