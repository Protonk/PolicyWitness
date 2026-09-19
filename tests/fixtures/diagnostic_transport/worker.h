/* Test-only inputs. The JSON oracle is maintained independently of these C
 * literals. These publications establish transport, never actual native calls. */
#ifndef PW_TRANSPORT_FIXTURE_H
#define PW_TRANSPORT_FIXTURE_H
static void transport_record(pw_shm_evidence_t *e, int beta, const char *mode) {
    const uint32_t op = beta ? 8 : 239;
    const uint32_t code = beta ? 4000000179u : 4000000001u;
    const uint32_t kind = beta ? 1 : 77;
    const int32_t result = beta ? -37 : -123;
    const int32_t error = beta ? 13 : 0;
    const uint32_t index = beta ? UINT32_MAX : 17;
    const uint32_t detail = beta ? 1234567890u : 7654321u;
    pw_progress(e, op, PW_PROGRESS_RETURNED, index);
    if (!strcmp(mode, "transport_absent") || !strcmp(mode, "transport_unpublished") ||
        !strcmp(mode, "transport_malformed")) {
        /* Poison payload exists without a committed publication, or with an
         * invalid structural errno flag. Never publish then revise a record. */
        e->operation = op; e->code = code; e->native_kind = kind;
        e->native_result = result; e->errno_val = error;
        e->errno_present = !strcmp(mode, "transport_malformed") ? 2 : 1;
        e->item_index = index; e->detail = detail;
        uint32_t state = !strcmp(mode, "transport_absent") ? 0 :
                         !strcmp(mode, "transport_unpublished") ? 2 : 1;
        atomic_store_explicit(&e->failure_published, state, memory_order_release);
    } else {
        pw_failure(e, op, code, kind, result, 1, error, index, detail);
    }
    if (!strcmp(mode, "transport_beta_truncated")) {
        char text[PW_SHM_DIAGNOSTIC_BYTES + 200];
        memset(text, 'T', sizeof(text) - 1); text[sizeof(text) - 1] = 0;
        pw_diagnostic(e, text);
    } else if (!strcmp(mode, "transport_bad_text")) {
        e->diagnostic_length = PW_SHM_DIAGNOSTIC_BYTES;
        atomic_store_explicit(&e->diagnostic_state, 1, memory_order_release);
    } else {
        pw_diagnostic(e, beta ? "beta native detail: café / 4000000179" :
                               "alpha opaque detail: snowman ☃ / 4000000001");
    }
}
#endif
