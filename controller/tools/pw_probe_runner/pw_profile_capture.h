/* Pre-apply compiled-object capture. No expected digest enters this code.
 * Every memory read is bounded; mach_vm_read_overwrite refuses an invalid
 * pointer instead of dereferencing an assumed private-API layout. */
#ifndef PW_PROFILE_CAPTURE_H
#define PW_PROFILE_CAPTURE_H
#include <CommonCrypto/CommonDigest.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "pw_probe_runner_abi.h"

typedef struct {
    uint32_t profile_type;
    uint32_t reserved;
    const void *bytecode;
    size_t bytecode_length;
} pw_compiler_profile_t;
_Static_assert(sizeof(void *) == 8 && sizeof(pw_compiler_profile_t) == 24,
               "compiled capture supports the validated 64-bit profile layout");

static void pw_digest_u32(CC_SHA256_CTX *ctx, uint32_t n) {
    unsigned char le[4] = {n & 255, (n >> 8) & 255, (n >> 16) & 255, (n >> 24) & 255};
    CC_SHA256_Update(ctx, le, sizeof(le));
}
static int pw_digest_order(const void *a, const void *b) { return memcmp(a, b, 32); }

/* Order-independent dictionary identity: SHA256(LE32 count || sorted pair
 * digests), each pair SHA256(LE32 keyBytes || key || LE32 valueBytes || value).
 * Actual C strings passed to sandbox_set_param supply the bytes, not a caller's
 * JSON digest. The worker passes a private snapshot to both setter and capture. */
static int pw_consumed_params_digest(const pw_shm_param_t *params, uint32_t count,
                                     unsigned char out[32]) {
    if (count > PW_SHM_MAX_PARAMS) return 0;
    unsigned char pairs[PW_SHM_MAX_PARAMS][32];
    for (uint32_t i = 0; i < count; i++) {
        size_t k = strnlen(params[i].key, PW_SHM_PARAM_KEY_MAX);
        size_t v = strnlen(params[i].value, PW_SHM_PARAM_VALUE_MAX);
        if (k == PW_SHM_PARAM_KEY_MAX || v == PW_SHM_PARAM_VALUE_MAX) return 0;
        CC_SHA256_CTX ctx; CC_SHA256_Init(&ctx);
        pw_digest_u32(&ctx, (uint32_t)k); CC_SHA256_Update(&ctx, params[i].key, (CC_LONG)k);
        pw_digest_u32(&ctx, (uint32_t)v); CC_SHA256_Update(&ctx, params[i].value, (CC_LONG)v);
        CC_SHA256_Final(pairs[i], &ctx);
    }
    qsort(pairs, count, 32, pw_digest_order);
    CC_SHA256_CTX ctx; CC_SHA256_Init(&ctx); pw_digest_u32(&ctx, count);
    CC_SHA256_Update(&ctx, pairs, count * 32); CC_SHA256_Final(out, &ctx);
    return 1;
}

static int pw_read_memory(const void *src, void *dst, size_t length) {
    mach_vm_size_t copied = 0;
    return src && length && mach_vm_read_overwrite(mach_task_self(),
        (mach_vm_address_t)src, length, (mach_vm_address_t)dst, &copied) == KERN_SUCCESS
        && copied == length;
}

static void pw_capture_profile(pw_shm_capture_t *out, unsigned char *payload,
                               const void *profile, const char *source, size_t source_length,
                               const pw_shm_param_t *params, uint32_t count,
                               const unsigned char nonce[PW_SHM_CAPTURE_NONCE_BYTES]) {
    memcpy(out->request_nonce, nonce, PW_SHM_CAPTURE_NONCE_BYTES);
    out->worker_pid = (uint32_t)getpid();
    out->source_length = (uint32_t)source_length;
    out->param_count = count;
    out->status = 4;
    if (source_length > UINT32_MAX || !pw_consumed_params_digest(params, count, out->params_sha256))
        goto finished;
    CC_SHA256(source, (CC_LONG)source_length, out->source_sha256);
    pw_compiler_profile_t view;
    out->status = 3;
    if (!pw_read_memory(profile, &view, sizeof(view))) goto finished;
    out->status = 2;
    /* Only the single-profile compile result (type 0) is qualified. Bundles,
     * empty results and oversized payloads are explicit unavailable captures. */
    if (view.profile_type != 0 || view.reserved != 0 || !view.bytecode_length
            || view.bytecode_length > PW_SHM_CAPTURE_BYTES || !view.bytecode)
        goto finished;
    out->status = 3;
    if (!pw_read_memory(view.bytecode, payload, view.bytecode_length)) goto finished;
    out->profile_type = view.profile_type;
    out->bytecode_length = (uint32_t)view.bytecode_length;
    CC_SHA256(payload, out->bytecode_length, out->bytecode_sha256);
    out->status = 1;
finished:
    atomic_store_explicit(&out->completed, 1u, memory_order_release);
}
#endif
