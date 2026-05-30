#include <errno.h>
#include <sandbox.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

/* Filter type IDs. The public sandbox.h does not export these constants;
 * values are determined empirically by comparing sandbox_check verdicts
 * against actual kernel enforcement (see
 * tests/suites/witness_contract/harness/verify_filter_id.sh).
 *
 * GLOBAL_NAME=2: previously documented as 16; corrected by enforcement
 * verification against the bug-report's `(deny mach-lookup (global-name
 * "com.apple.cfprefsd.xpc.daemon"))` policy. The wrong constant caused
 * the BBX-001 anomaly we had carried as "Apple's sandbox_check is
 * unreliable for global-name" — that anomaly was at least partly
 * self-inflicted by querying with the wrong filter ID.
 *
 * LOCAL_NAME=17: NOT YET re-verified by the same methodology. May also
 * be incorrect by the same pattern. No in-tree test exercises
 * local-name today. */
#ifndef SANDBOX_FILTER_PATH
#define SANDBOX_FILTER_PATH 1
#endif
#ifndef SANDBOX_FILTER_GLOBAL_NAME
#define SANDBOX_FILTER_GLOBAL_NAME 2
#endif
#ifndef SANDBOX_FILTER_LOCAL_NAME
#define SANDBOX_FILTER_LOCAL_NAME 17
#endif

int sandbox_check(pid_t pid, const char *operation, int type, ...);

static void print_json_string(const char *s) {
    putchar('"');
    if (!s) {
        putchar('"');
        return;
    }
    for (const unsigned char *p = (const unsigned char *)s; *p; ++p) {
        switch (*p) {
            case '\\': fputs("\\\\", stdout); break;
            case '"': fputs("\\\"", stdout); break;
            case '\n': fputs("\\n", stdout); break;
            case '\r': fputs("\\r", stdout); break;
            case '\t': fputs("\\t", stdout); break;
            default: putchar(*p); break;
        }
    }
    putchar('"');
}

static void print_error(const char *error, int pid) {
    printf("{\"kind\":\"sb_api_validator_error\",\"schema_version\":1,\"error\":");
    print_json_string(error);
    printf(",\"pid\":%d}\n", pid);
}

/* Map a filter_type CLI name (or the RAW:<n> escape hatch) to a numeric
 * sandbox_check filter ID. Returns >= 0 on success; -1 on unknown name
 * or malformed RAW. NONE maps to 0. Shared between per-probe and batch
 * modes so both surfaces stay in sync. */
static int resolve_filter_type_id(const char *filter_type) {
    if (!filter_type) return -1;
    if (strncmp(filter_type, "RAW:", 4) == 0) {
        char *end = NULL;
        long v = strtol(filter_type + 4, &end, 10);
        if (end && *end == '\0' && v >= 0 && v <= 255) {
            return (int)v;
        }
        return -1;
    }
    if (strcmp(filter_type, "NONE") == 0) return 0;
    if (strcmp(filter_type, "PATH") == 0) return SANDBOX_FILTER_PATH;
    if (strcmp(filter_type, "GLOBAL_NAME") == 0) return SANDBOX_FILTER_GLOBAL_NAME;
    if (strcmp(filter_type, "LOCAL_NAME") == 0) return SANDBOX_FILTER_LOCAL_NAME;
#if defined(SANDBOX_FILTER_APPLEEVENT_DESTINATION)
    if (strcmp(filter_type, "APPLEEVENT_DESTINATION") == 0) return SANDBOX_FILTER_APPLEEVENT_DESTINATION;
#endif
#if defined(SANDBOX_FILTER_RIGHT_NAME)
    if (strcmp(filter_type, "RIGHT_NAME") == 0) return SANDBOX_FILTER_RIGHT_NAME;
#endif
#if defined(SANDBOX_FILTER_PREFERENCE_DOMAIN)
    if (strcmp(filter_type, "PREFERENCE_DOMAIN") == 0) return SANDBOX_FILTER_PREFERENCE_DOMAIN;
#endif
#if defined(SANDBOX_FILTER_KEXT_BUNDLE_ID)
    if (strcmp(filter_type, "KEXT_BUNDLE_ID") == 0) return SANDBOX_FILTER_KEXT_BUNDLE_ID;
#endif
#if defined(SANDBOX_FILTER_INFO_TYPE)
    if (strcmp(filter_type, "INFO_TYPE") == 0) return SANDBOX_FILTER_INFO_TYPE;
#endif
#if defined(SANDBOX_FILTER_NOTIFICATION_TYPE)
    if (strcmp(filter_type, "NOTIFICATION_TYPE") == 0) return SANDBOX_FILTER_NOTIFICATION_TYPE;
#endif
#if defined(SANDBOX_FILTER_XPC_SERVICE_NAME)
    if (strcmp(filter_type, "XPC_SERVICE_NAME") == 0) return SANDBOX_FILTER_XPC_SERVICE_NAME;
#endif
#if defined(SANDBOX_FILTER_NVRAM_VARIABLE)
    if (strcmp(filter_type, "NVRAM_VARIABLE") == 0) return SANDBOX_FILTER_NVRAM_VARIABLE;
#endif
#if defined(SANDBOX_FILTER_POSIX_IPC_NAME)
    if (strcmp(filter_type, "POSIX_IPC_NAME") == 0) return SANDBOX_FILTER_POSIX_IPC_NAME;
#endif
    return -1;
}

/* Skip ASCII whitespace in *p. *p is advanced; returns void. */
static void skip_ws(const char **p) {
    while (**p == ' ' || **p == '\t' || **p == '\r' || **p == '\n') (*p)++;
}

/* Parse a JSON string starting at **p (pointing at the opening "). On
 * success, returns a malloc'd null-terminated string and advances *p
 * past the closing ". Returns NULL on malformed input. Recognized
 * escapes: \" \\ \/ \n \r \t \b \f. \uXXXX is NOT recognized — the
 * controller does not emit unicode escapes in probe lines.
 *
 * Caller frees the returned buffer. */
static char *parse_json_string(const char **p) {
    if (**p != '"') return NULL;
    (*p)++;
    /* Two passes: size first, then copy. Keeps the buffer tight without
     * a realloc loop. */
    const char *scan = *p;
    size_t len = 0;
    while (*scan && *scan != '"') {
        if (*scan == '\\') {
            scan++;
            if (!*scan) return NULL;
            len++;
            scan++;
        } else {
            len++;
            scan++;
        }
    }
    if (*scan != '"') return NULL;
    char *out = (char *)malloc(len + 1);
    if (!out) return NULL;
    char *w = out;
    while (**p && **p != '"') {
        if (**p == '\\') {
            (*p)++;
            switch (**p) {
                case '"':  *w++ = '"';  break;
                case '\\': *w++ = '\\'; break;
                case '/':  *w++ = '/';  break;
                case 'n':  *w++ = '\n'; break;
                case 'r':  *w++ = '\r'; break;
                case 't':  *w++ = '\t'; break;
                case 'b':  *w++ = '\b'; break;
                case 'f':  *w++ = '\f'; break;
                default:   free(out); return NULL;
            }
            (*p)++;
        } else {
            *w++ = **p;
            (*p)++;
        }
    }
    if (**p != '"') { free(out); return NULL; }
    (*p)++;
    *w = '\0';
    return out;
}

/* Parse one NDJSON probe line. Expects a flat JSON object with
 * string-only values; recognized keys are step_id (required),
 * operation (required), filter_type (required), filter_value
 * (optional). Unknown keys cause failure (so a typo is a loud error,
 * not silently dropped).
 *
 * On success, returns 0 and populates the four out parameters. The
 * caller frees all four buffers (free(NULL) is safe). On failure
 * returns -1 and *err_out is populated with a short reason. */
static int parse_probe_line(const char *line,
                            char **step_id_out,
                            char **operation_out,
                            char **filter_type_out,
                            char **filter_value_out,
                            const char **err_out) {
    *step_id_out = NULL;
    *operation_out = NULL;
    *filter_type_out = NULL;
    *filter_value_out = NULL;
    *err_out = NULL;

    const char *p = line;
    skip_ws(&p);
    if (*p != '{') { *err_out = "expected '{'"; return -1; }
    p++;
    skip_ws(&p);

    /* Empty object {} is invalid — required fields missing. */
    if (*p == '}') { *err_out = "missing required fields"; return -1; }

    /* On failure, we do NOT free the partially-parsed out-parameters
     * here — the caller frees them whether we return success or
     * failure. This lets the caller use step_id_out when it was
     * already populated before a later validation step failed, which
     * makes parse_error diagnostics actionable for the host. */
    for (;;) {
        skip_ws(&p);
        char *key = parse_json_string(&p);
        if (!key) { *err_out = "invalid key"; return -1; }
        skip_ws(&p);
        if (*p != ':') { free(key); *err_out = "expected ':'"; return -1; }
        p++;
        skip_ws(&p);
        char *value = parse_json_string(&p);
        if (!value) { free(key); *err_out = "invalid value"; return -1; }
        if (strcmp(key, "step_id") == 0) {
            if (*step_id_out) { free(*step_id_out); }
            *step_id_out = value;
        } else if (strcmp(key, "operation") == 0) {
            if (*operation_out) { free(*operation_out); }
            *operation_out = value;
        } else if (strcmp(key, "filter_type") == 0) {
            if (*filter_type_out) { free(*filter_type_out); }
            *filter_type_out = value;
        } else if (strcmp(key, "filter_value") == 0) {
            if (*filter_value_out) { free(*filter_value_out); }
            *filter_value_out = value;
        } else {
            free(key); free(value);
            *err_out = "unknown key";
            return -1;
        }
        free(key);
        skip_ws(&p);
        if (*p == ',') { p++; continue; }
        if (*p == '}') { p++; break; }
        *err_out = "expected ',' or '}'";
        return -1;
    }

    /* Reject trailing content after the closing '}'. Otherwise a
     * malformed host could append junk to a valid probe and have it
     * silently accepted — the runner relies on one NDJSON probe
     * producing one trustworthy verdict. */
    skip_ws(&p);
    if (*p != '\0') {
        *err_out = "trailing content after '}'";
        return -1;
    }

    if (!*step_id_out || !*operation_out || !*filter_type_out) {
        *err_out = "missing required field (step_id, operation, filter_type)";
        return -1;
    }
    /* NONE filter must not have a filter_value; everything else must
     * have one. Match the per-probe CLI rules so callers see a
     * consistent contract. */
    if (strcmp(*filter_type_out, "NONE") == 0) {
        if (*filter_value_out) {
            *err_out = "NONE filter must not have filter_value";
            return -1;
        }
    } else {
        if (!*filter_value_out) {
            *err_out = "filter_value required for non-NONE filter_type";
            return -1;
        }
    }
    return 0;
}

/* Emit one NDJSON verdict for a successful probe.
 * Shape: {"step_id","rc","errno","outcome","filter_type_id","error":null} */
static void emit_verdict(const char *step_id,
                         const char *operation,
                         const char *filter_type,
                         int filter_type_id,
                         const char *filter_value,
                         int rc, int err) {
    printf("{\"kind\":\"sb_api_validator_verdict\",\"schema_version\":1");
    printf(",\"step_id\":"); print_json_string(step_id);
    printf(",\"operation\":"); print_json_string(operation);
    printf(",\"filter_type\":"); print_json_string(filter_type);
    printf(",\"filter_type_id\":%d", filter_type_id);
    printf(",\"filter_value\":");
    if (filter_value) print_json_string(filter_value); else printf("null");
    printf(",\"rc\":%d", rc);
    printf(",\"errno\":%d", err);
    const char *outcome;
    if (rc == 0) outcome = "allow";
    else if (rc == 1 && err == 0) outcome = "deny";
    else outcome = "error";
    printf(",\"outcome\":\"%s\"", outcome);
    printf(",\"error\":null}\n");
    fflush(stdout);
}

/* Emit one NDJSON verdict for a probe that failed before sandbox_check.
 * step_id may be NULL when the parser couldn't recover it. */
static void emit_failure(const char *step_id,
                         const char *outcome,
                         const char *error_reason) {
    printf("{\"kind\":\"sb_api_validator_verdict\",\"schema_version\":1");
    printf(",\"step_id\":");
    if (step_id) print_json_string(step_id); else printf("null");
    printf(",\"outcome\":\"%s\"", outcome);
    printf(",\"error\":");
    print_json_string(error_reason);
    printf("}\n");
    fflush(stdout);
}

/* Run batch mode: read NDJSON probe lines from stdin until EOF, emit
 * one NDJSON verdict per line to stdout. Parse errors on any single
 * line emit a verdict with outcome="parse_error" and continue with the
 * next line — so a malformed probe doesn't abort the whole run.
 *
 * Returns 0 on clean EOF (the validator always exits zero in batch
 * mode; per-probe failures are surfaced in the verdict stream, not in
 * the exit code). */
static int run_batch(int pid) {
    /* Cap at 64 KiB per line. Probe filter_values are typically
     * short strings; this is comfortably above anything the host
     * should emit. A line longer than the cap is emitted as ONE
     * parse_error verdict (not multiple chunks-as-probes), then
     * the rest of the physical line is drained before the next
     * iteration — preserving the "one verdict per probe in input
     * order" contract under malformed input. */
    enum { LINE_MAX_BYTES = 65536 };
    char *line = (char *)malloc(LINE_MAX_BYTES);
    if (!line) return 2;

    while (fgets(line, LINE_MAX_BYTES, stdin)) {
        /* If the read filled the buffer without seeing a newline, the
         * physical line is longer than the cap. Emit one verdict and
         * drain the rest before reading the next probe. EOF
         * mid-overlong-line is treated as a valid drain endpoint. */
        size_t len = strlen(line);
        bool overlong = (len == LINE_MAX_BYTES - 1) && line[len - 1] != '\n';
        if (overlong) {
            emit_failure(NULL, "parse_error", "probe line exceeds 64 KiB cap");
            int c;
            while ((c = fgetc(stdin)) != EOF && c != '\n') {
                /* discard */
            }
            continue;
        }

        /* Skip blank lines silently so a trailing newline in the
         * input doesn't produce a spurious parse error. */
        const char *scan = line;
        while (*scan == ' ' || *scan == '\t' || *scan == '\r' || *scan == '\n') scan++;
        if (*scan == '\0') continue;

        char *step_id = NULL, *operation = NULL, *filter_type = NULL, *filter_value = NULL;
        const char *err = NULL;
        if (parse_probe_line(line, &step_id, &operation, &filter_type, &filter_value, &err) != 0) {
            emit_failure(step_id /* may be partial */, "parse_error", err ? err : "unknown");
            free(step_id); free(operation); free(filter_type); free(filter_value);
            continue;
        }

        int filter_type_id = resolve_filter_type_id(filter_type);
        if (filter_type_id < 0) {
            emit_failure(step_id, "bad_filter", "unsupported filter_type");
            free(step_id); free(operation); free(filter_type); free(filter_value);
            continue;
        }

        errno = 0;
        int rc;
        if (filter_type_id == 0) {
            rc = sandbox_check(pid, operation, 0);
        } else {
            rc = sandbox_check(pid, operation, filter_type_id, filter_value);
        }
        emit_verdict(step_id, operation, filter_type, filter_type_id, filter_value, rc, errno);

        free(step_id); free(operation); free(filter_type); free(filter_value);
    }

    free(line);
    return 0;
}

static int parse_pid(const char *s) {
    char *end = NULL;
    long v = strtol(s, &end, 10);
    if (!s || !*s || (end && *end)) {
        return -1;
    }
    if (v <= 0 || v > 1 << 30) {
        return -1;
    }
    return (int)v;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr,
                "usage:\n"
                "  %s [--json] <pid> [operation filter_type [filter_value]]\n"
                "      per-probe mode (legacy CLI; one sandbox_check call,\n"
                "      one JSON line on stdout).\n"
                "  %s --batch <pid>\n"
                "      batch mode: read NDJSON probes from stdin, write\n"
                "      NDJSON verdicts to stdout, one verdict per line.\n"
                "      Probe shape: {\"step_id\":..,\"operation\":..,\n"
                "                    \"filter_type\":..,\"filter_value\":..?}\n"
                "      filter_type: NONE | PATH | GLOBAL_NAME | LOCAL_NAME | ...\n",
                argv[0], argv[0]);
        return 2;
    }

    bool json = false;
    bool batch = false;
    int argi = 1;
    if (strcmp(argv[argi], "--batch") == 0) {
        batch = true;
        argi++;
    } else if (strcmp(argv[argi], "--json") == 0) {
        json = true;
        argi++;
    }
    if (argc - argi < 1) {
        fprintf(stderr, "missing pid\n");
        return 2;
    }

    int pid = parse_pid(argv[argi++]);
    if (pid <= 0) {
        if (json) {
            print_error("pid_missing", pid);
        } else {
            fprintf(stderr, "bad pid\n");
        }
        return 2;
    }

    if (batch) {
        /* Batch mode is exclusive of any further positional args; the
         * probes themselves come from stdin. */
        if (argc - argi != 0) {
            fprintf(stderr, "--batch takes no positional args after <pid>\n");
            return 2;
        }
        return run_batch(pid);
    }

    if (argc - argi == 0) {
        if (json) {
            printf("{\"kind\":\"sb_api_validator_status\",\"schema_version\":1,\"pid\":%d,\"error\":null}\n", pid);
        } else {
            printf("ok\n");
        }
        return 0;
    }

    if (argc - argi < 2) {
        if (json) {
            print_error("missing_args", pid);
        } else {
            fprintf(stderr, "missing args\n");
        }
        return 2;
    }

    const char *operation = argv[argi++];
    const char *filter_type = argv[argi++];

    /* Shared with batch mode (see resolve_filter_type_id). Both
     * surfaces must accept the same filter-type names; routing
     * both through one function prevents drift when new filter
     * kinds are added. The RAW:<n> escape hatch and all
     * system-conditional names live in the shared helper. */
    int filter_type_id = resolve_filter_type_id(filter_type);

    if (filter_type_id < 0) {
        if (json) {
            printf("{\"kind\":\"sb_api_validator_error\",\"schema_version\":1,\"error\":\"bad_filter\",\"filter\":");
            print_json_string(filter_type);
            printf("}\n");
        } else {
            fprintf(stderr, "bad filter\n");
        }
        return 2;
    }

    /* filter_value rules:
     *   NONE (filter_type_id == 0): must NOT have a filter_value arg.
     *   Everything else: must have exactly one filter_value arg.
     * Trailing positional args are always an error.
     */
    const char *filter_value = NULL;
    if (filter_type_id == 0) {
        if (argi < argc) {
            if (json) {
                print_error("unexpected_filter_value_for_none", pid);
            } else {
                fprintf(stderr, "filter type NONE must not be followed by a filter_value\n");
            }
            return 2;
        }
    } else {
        if (argi >= argc) {
            if (json) {
                print_error("missing_filter_value", pid);
            } else {
                fprintf(stderr, "missing filter_value for %s\n", filter_type);
            }
            return 2;
        }
        filter_value = argv[argi++];
        if (argi < argc) {
            if (json) {
                print_error("unexpected_extra_args", pid);
            } else {
                fprintf(stderr, "unexpected extra args after filter_value\n");
            }
            return 2;
        }
    }

    errno = 0;
    int rc;
    if (filter_type_id == 0) {
        /* type=0 indicates no filter argument. */
        rc = sandbox_check(pid, operation, 0);
    } else {
        rc = sandbox_check(pid, operation, filter_type_id, filter_value);
    }

    if (!json) {
        printf("rc=%d errno=%d\n", rc, errno);
        return rc == 0 ? 0 : 1;
    }

    printf("{\"kind\":\"sb_api_validator_result\",\"schema_version\":1");
    printf(",\"pid\":%d", pid);
    printf(",\"operation\":");
    print_json_string(operation);
    printf(",\"filter_type\":");
    print_json_string(filter_type);
    printf(",\"filter_type_id\":%d", filter_type_id);
    printf(",\"filter_value\":");
    if (filter_value) {
        print_json_string(filter_value);
    } else {
        printf("null");
    }
    printf(",\"extra\":null");
    printf(",\"rc\":%d", rc);
    printf(",\"errno\":%d", errno);
    printf(",\"allowed\":%s", rc == 0 ? "true" : "false");
    printf(",\"denied\":%s", rc == 0 ? "false" : "true");
    printf("}\n");
    return 0;
}
