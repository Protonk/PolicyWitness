/* Pure capture tests: no compilation or policy application. Construct the private
 * layout independently; live authored controls separately qualify that layout. */
#include <assert.h>
#include "pw_profile_capture.h"

static void exact_capacity_capture(void) {
    /* Keep the expected boundary independent of the implementation constant. */
    enum { expected_capacity = 1024 * 1024 };
    _Static_assert(PW_SHM_CAPTURE_BYTES == expected_capacity,
                   "compiled capture capacity must remain one MiB");
    unsigned char *bytes = malloc(expected_capacity + 1);
    assert(bytes != NULL);
    for (size_t i = 0; i < expected_capacity + 1; i++)
        bytes[i] = (unsigned char)(i * 37u + (i >> 8) + (i >> 16));
    /* Hash the independent source/extent before capture, never its output or
     * reported length. CommonCrypto is the checksum primitive, not the code
     * under test; this oracle checks capture's byte/extent selection. */
    unsigned char expected_digest[32];
    CC_SHA256(bytes, expected_capacity, expected_digest);
    static unsigned char payload[expected_capacity + 1];
    memset(payload, 0xa5, sizeof(payload));
    unsigned char nonce[16] = {4,5,6};
    struct { uint32_t type, padding; const void *bytes; size_t length; } profile =
        {0,0,bytes,expected_capacity};
    pw_shm_capture_t out = {0};
    pw_capture_profile(&out, payload, &profile, "source", 6, NULL, 0, nonce);
    assert(out.completed == 1 && out.status == 1 && out.worker_pid == getpid());
    assert(out.profile_type == 0 && out.bytecode_length == expected_capacity);
    assert(!memcmp(out.request_nonce, nonce, sizeof(nonce)));
    assert(!memcmp(payload, bytes, expected_capacity));
    assert(!memcmp(out.bytecode_sha256, expected_digest, sizeof(expected_digest)));
    assert(payload[expected_capacity] == 0xa5);

    /* The excessive extent is readable too: refusal must be about capacity,
     * not an invalid pointer or a short allocation. Use a fresh receipt. */
    profile.length = expected_capacity + 1;
    memset(payload, 0xa5, sizeof(payload));
    pw_shm_capture_t refused = {0};
    pw_capture_profile(&refused, payload, &profile, "source", 6, NULL, 0, nonce);
    assert(refused.completed == 1 && refused.status == 2);
    assert(refused.bytecode_length == 0);
    for (size_t i = 0; i < sizeof(payload); i++) assert(payload[i] == 0xa5);
    free(bytes);
}

int main(void) {
    exact_capacity_capture();
    static unsigned char payload[PW_SHM_CAPTURE_BYTES];
    unsigned char bytes[] = {10,20,30,99};
    unsigned char nonce[16] = {1,2,3};
    struct { uint32_t type, padding; const void *bytes; size_t length; } profile = {0,0,bytes,3};
    pw_shm_param_t params[2] = {{.key="a",.value="é"},{.key="z",.value="2"}};
    pw_shm_capture_t out = {0};
    pw_capture_profile(&out, payload, &profile, "source", 6, params, 2, nonce);
    assert(out.completed == 1 && out.status == 1 && out.worker_pid == getpid());
    assert(out.bytecode_length == 3 && !memcmp(payload, bytes, 3));
    assert(!memcmp(out.request_nonce, nonce, 16));
    unsigned char original[32]; memcpy(original, out.bytecode_sha256, 32);
    bytes[3] = 88;
    pw_capture_profile(&out, payload, &profile, "source", 6, params, 2, nonce);
    assert(!memcmp(original, out.bytecode_sha256, 32));
    bytes[1] = 21;
    pw_capture_profile(&out, payload, &profile, "source", 6, params, 2, nonce);
    assert(memcmp(original, out.bytecode_sha256, 32));
    unsigned char a[32], b[32];
    assert(pw_consumed_params_digest(params, 2, a));
    pw_shm_param_t reversed[] = {params[1],params[0]};
    assert(pw_consumed_params_digest(reversed, 2, b) && !memcmp(a,b,32));
    params[0].value[0] = 'x';
    assert(pw_consumed_params_digest(params, 2, b) && memcmp(a,b,32));
    profile.length = PW_SHM_CAPTURE_BYTES + 1;
    pw_capture_profile(&out, payload, &profile, "source", 6, params, 2, nonce);
    assert(out.status == 2);
    profile.length = 3; profile.type = 1;
    pw_capture_profile(&out, payload, &profile, "source", 6, params, 2, nonce);
    assert(out.status == 2);
    profile.type = 0; profile.bytes = (void *)1;
    pw_capture_profile(&out, payload, &profile, "source", 6, params, 2, nonce);
    assert(out.status == 3);
    pw_capture_profile(&out, payload, (void *)1, "source", 6, params, 2, nonce);
    assert(out.status == 3);
    memset(params[0].key, 'x', sizeof(params[0].key));
    pw_capture_profile(&out, payload, &profile, "source", 6, params, 2, nonce);
    assert(out.status == 4 && out.completed == 1);
    return 0;
}
