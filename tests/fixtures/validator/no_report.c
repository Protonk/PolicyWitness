/* Compile the production validator with a recording sandbox_check. The
 * supplied native rc/errno pairs exercise its output branches; they are
 * constructed observations, with no kernel query, sandbox or child involved.
 * Every recorded native type must retain SANDBOX_CHECK_NO_REPORT. */
#include <assert.h>
#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

static struct { int type; char operation[128]; char value[128]; } recorded[64];
static int recorded_count, supplied_rc, supplied_errno;
static char captured_output[4096];
int recording_sandbox_check(pid_t pid, const char *operation, int type, ...) {
    (void)pid;
    assert(errno == 0 && recorded_count < 64);
    recorded[recorded_count].type = type;
    snprintf(recorded[recorded_count].operation, 128, "%s", operation);
    /* Numeric filter zero uses the native no-value call form. */
    if ((type & ~0x40000000) != 0) {
        va_list args;
        va_start(args, type);
        snprintf(recorded[recorded_count].value, 128, "%s", va_arg(args, const char *));
        va_end(args);
    }
    recorded_count++;
    errno = supplied_errno;
    return supplied_rc;
}
#define sandbox_check recording_sandbox_check
#define main validator_main
#include "sb_api_validator.c"
#undef main
#undef sandbox_check

/* Capture the real parser/emitter's stdout and return; the outer test log
 * retains the input, configured native pair and exact output for each call. */
static int run(int argc, char **argv, const char *stdin_text) {
    fflush(stdout);
    int saved_in = dup(STDIN_FILENO), saved_out = dup(STDOUT_FILENO);
    int in[2];
    FILE *output = tmpfile();
    assert(saved_in >= 0 && saved_out >= 0 && output && pipe(in) == 0);
    if (stdin_text) {
        size_t n = strlen(stdin_text);
        assert(write(in[1], stdin_text, n) == (ssize_t)n);
    }
    close(in[1]);
    assert(dup2(in[0], STDIN_FILENO) == STDIN_FILENO);
    close(in[0]);
    assert(dup2(fileno(output), STDOUT_FILENO) == STDOUT_FILENO);
    clearerr(stdin);
    int first_call = recorded_count;
    int rc = validator_main(argc, argv);
    fflush(stdout);
    assert(dup2(saved_in, STDIN_FILENO) == STDIN_FILENO && dup2(saved_out, STDOUT_FILENO) == STDOUT_FILENO);
    close(saved_in); close(saved_out);
    clearerr(stdin);
    rewind(output);
    size_t used = fread(captured_output, 1, sizeof(captured_output) - 1, output);
    assert(used < sizeof(captured_output) - 1 && !ferror(output));
    captured_output[used] = '\0';
    fclose(output);
    printf("constructed native rc=%d errno=%d; argv:", supplied_rc, supplied_errno);
    for (int i = 0; i < argc; i++) printf(" [%s]", argv[i]);
    printf("\ninput:%s\nexit=%d output:%s\n", stdin_text ? stdin_text : "(none)", rc, captured_output);
    for (int i = first_call; i < recorded_count; i++)
        printf("recorded type=0x%x operation=%s value=%s\n", recorded[i].type, recorded[i].operation, recorded[i].value);
    fflush(stdout);
    return rc;
}

static void string_field(const char *key, const char *value) {
    char expected[256];
    snprintf(expected, sizeof(expected), "\"%s\":\"%s\"", key, value);
    assert(strstr(captured_output, expected));
}

static void duplicate_keys(char **batch) {
    const char *keys[] = {"step_id", "operation", "filter_type", "filter_value"};
    const char *values[2][4] = {{"first", "file-read-data", "PATH", "/first"},
                              {"second", "mach-lookup", "GLOBAL_NAME", "/second"}};
    for (int key = 0; key < 4; key++) for (int order = 0; order < 2; order++) {
        char line[512];
        snprintf(line, sizeof(line), "{\"step_id\":\"%s\",\"operation\":\"%s\",\"filter_type\":\"%s\","
                 "\"filter_value\":\"%s\",\"%s\":\"%s\"}\n", values[order][0], values[order][1],
                 values[order][2], values[order][3], keys[key], values[1-order][key]);
        int before = recorded_count;
        assert(run(3, batch, line) == 0 && recorded_count == before + 1);
        for (int field = 0; field < 4; field++) string_field(keys[field], values[field == key ? 1-order : order][field]);
        assert(strcmp(recorded[before].operation, values[key == 1 ? 1-order : order][1]) == 0);
        assert(strcmp(recorded[before].value, values[key == 3 ? 1-order : order][3]) == 0);
        int filter = (key == 2 ? 1-order : order) == 0 ? SANDBOX_FILTER_PATH : SANDBOX_FILTER_GLOBAL_NAME;
        assert(recorded[before].type == (filter | SANDBOX_CHECK_NO_REPORT));
    }
}

static void raw_zero(char **batch) {
    char *filters[] = {"RAW:", "RAW:0"};
    for (int i = 0; i < 2; i++) {
        char *direct[] = {"sb_api_validator", "--json", "1", "network-outbound", filters[i], "unused", NULL};
        int before = recorded_count;
        assert(run(5, direct, NULL) == 0 && recorded_count == before + 1);
        assert(recorded[before].type == SANDBOX_CHECK_NO_REPORT);
        assert(strstr(captured_output, "\"filter_type_id\":0,\"filter_value\":null"));
        before = recorded_count;
        assert(run(6, direct, NULL) == 2 && recorded_count == before);
        string_field("error", "unexpected_filter_value_for_none");
        char line[256];
        snprintf(line, sizeof(line), "{\"step_id\":\"zero\",\"operation\":\"network-outbound\",\"filter_type\":\"%s\"}\n", filters[i]);
        assert(run(3, batch, line) == 0 && recorded_count == before);
        string_field("outcome", "parse_error");
        string_field("error", "filter_value required for non-NONE filter_type");
        snprintf(line, sizeof(line), "{\"step_id\":\"zero\",\"operation\":\"network-outbound\",\"filter_type\":\"%s\",\"filter_value\":\"unused\"}\n", filters[i]);
        assert(run(3, batch, line) == 0 && recorded_count == before + 1);
        assert(recorded[before].type == SANDBOX_CHECK_NO_REPORT && recorded[before].value[0] == '\0');
        string_field("filter_value", "unused");
        assert(strstr(captured_output, "\"filter_type_id\":0"));
    }
}

static void result_meaning(char **batch) {
    const struct { int rc, error; const char *outcome; } pairs[] = {
        {0, 0, "allow"}, {1, 0, "deny"}, {-1, EINVAL, "unsupported_operation"},
        {-1, EPERM, "error"}, {1, EPERM, "error"}, {2, 0, "error"}};
    char *direct[] = {"sb_api_validator", "--json", "1", "probe-op", "NONE", NULL};
    char *plain[] = {"sb_api_validator", "1", "probe-op", "NONE", NULL};
    const char *line = "{\"step_id\":\"result\",\"operation\":\"probe-op\",\"filter_type\":\"NONE\"}\n";
    for (size_t i = 0; i < sizeof(pairs)/sizeof(pairs[0]); i++) {
        supplied_rc = pairs[i].rc; supplied_errno = pairs[i].error;
        char numbers[96];
        snprintf(numbers, sizeof(numbers), "\"rc\":%d,\"errno\":%d", supplied_rc, supplied_errno);
        int before = recorded_count;
        assert(run(5, direct, NULL) == 0 && recorded_count == before + 1);
        string_field("kind", "sb_api_validator_result");
        assert(strstr(captured_output, numbers));
        assert(strstr(captured_output, supplied_rc == 0 ? "\"allowed\":true,\"denied\":false" : "\"allowed\":false,\"denied\":true"));
        assert(!strstr(captured_output, "\"outcome\":") && !strstr(captured_output, "\"error\":"));
        assert(run(4, plain, NULL) == (supplied_rc == 0 ? 0 : 1));
        char expected[96];
        snprintf(expected, sizeof(expected), "rc=%d errno=%d\n", supplied_rc, supplied_errno);
        assert(strcmp(captured_output, expected) == 0);
        assert(run(3, batch, line) == 0);
        assert(recorded_count == before + 3 && strstr(captured_output, numbers));
        string_field("outcome", pairs[i].outcome);
        if (i < 2) assert(strstr(captured_output, "\"error\":null"));
        else {
            assert(strstr(captured_output, "\"error\":\"") && !strstr(captured_output, "\"error\":null"));
            if (supplied_errno == EINVAL) assert(strstr(captured_output, "probe-op") && strstr(captured_output, "wildcard"));
        }
    }
}

int main(void) {
    char *batch[] = {"sb_api_validator", "--batch", "1", NULL};
    assert(run(3, batch,
        "{\"step_id\":\"p\",\"operation\":\"file-read-data\",\"filter_type\":\"PATH\",\"filter_value\":\"/x\"}\n"
        "{\"step_id\":\"g\",\"operation\":\"mach-lookup\",\"filter_type\":\"GLOBAL_NAME\",\"filter_value\":\"a.b\"}\n"
        "{\"step_id\":\"n\",\"operation\":\"network-outbound\",\"filter_type\":\"NONE\"}\n") == 0);
    assert(recorded_count == 3);
    char *single_path[] = {"sb_api_validator", "--json", "1", "file-read-data", "PATH", "/x", NULL};
    assert(run(6, single_path, NULL) == 0);
    char *single_none[] = {"sb_api_validator", "--json", "1", "network-outbound", "NONE", NULL};
    assert(run(5, single_none, NULL) == 0);
    assert(recorded_count == 5);
    const int expected_ids[] = {SANDBOX_FILTER_PATH, SANDBOX_FILTER_GLOBAL_NAME, 0, SANDBOX_FILTER_PATH, 0};
    for (int i = 0; i < 5; i++) assert(recorded[i].type == (expected_ids[i] | SANDBOX_CHECK_NO_REPORT));
    duplicate_keys(batch);
    raw_zero(batch);
    result_meaning(batch);
    for (int i = 0; i < recorded_count; i++) assert((recorded[i].type & SANDBOX_CHECK_NO_REPORT) == SANDBOX_CHECK_NO_REPORT);
    printf("ok: %d constructed native calls preserve no-report flags; duplicate keys, RAW zero and direct/batch result meanings remain distinct\n", recorded_count);
    return 0;
}
