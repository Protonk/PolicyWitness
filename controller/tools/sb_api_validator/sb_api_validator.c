#include <errno.h>
#include <sandbox.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

#ifndef SANDBOX_FILTER_PATH
#define SANDBOX_FILTER_PATH 1
#endif
#ifndef SANDBOX_FILTER_GLOBAL_NAME
#define SANDBOX_FILTER_GLOBAL_NAME 16
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
        fprintf(stderr, "usage: %s [--json] <pid> [operation filter_type filter_value]\n", argv[0]);
        return 2;
    }

    bool json = false;
    int argi = 1;
    if (strcmp(argv[argi], "--json") == 0) {
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

    if (argc - argi == 0) {
        if (json) {
            printf("{\"kind\":\"sb_api_validator_status\",\"schema_version\":1,\"pid\":%d,\"error\":null}\n", pid);
        } else {
            printf("ok\n");
        }
        return 0;
    }

    if (argc - argi < 3) {
        if (json) {
            print_error("missing_args", pid);
        } else {
            fprintf(stderr, "missing args\n");
        }
        return 2;
    }

    const char *operation = argv[argi++];
    const char *filter_type = argv[argi++];
    const char *filter_value = argv[argi++];

    int filter_type_id = -1;
    if (strcmp(filter_type, "PATH") == 0) {
        filter_type_id = SANDBOX_FILTER_PATH;
    } else if (strcmp(filter_type, "GLOBAL_NAME") == 0) {
        filter_type_id = SANDBOX_FILTER_GLOBAL_NAME;
    } else if (strcmp(filter_type, "LOCAL_NAME") == 0) {
        filter_type_id = SANDBOX_FILTER_LOCAL_NAME;
    }
#if defined(SANDBOX_FILTER_APPLEEVENT_DESTINATION)
    else if (strcmp(filter_type, "APPLEEVENT_DESTINATION") == 0) {
        filter_type_id = SANDBOX_FILTER_APPLEEVENT_DESTINATION;
    }
#endif
#if defined(SANDBOX_FILTER_RIGHT_NAME)
    else if (strcmp(filter_type, "RIGHT_NAME") == 0) {
        filter_type_id = SANDBOX_FILTER_RIGHT_NAME;
    }
#endif
#if defined(SANDBOX_FILTER_PREFERENCE_DOMAIN)
    else if (strcmp(filter_type, "PREFERENCE_DOMAIN") == 0) {
        filter_type_id = SANDBOX_FILTER_PREFERENCE_DOMAIN;
    }
#endif
#if defined(SANDBOX_FILTER_KEXT_BUNDLE_ID)
    else if (strcmp(filter_type, "KEXT_BUNDLE_ID") == 0) {
        filter_type_id = SANDBOX_FILTER_KEXT_BUNDLE_ID;
    }
#endif
#if defined(SANDBOX_FILTER_INFO_TYPE)
    else if (strcmp(filter_type, "INFO_TYPE") == 0) {
        filter_type_id = SANDBOX_FILTER_INFO_TYPE;
    }
#endif
#if defined(SANDBOX_FILTER_NOTIFICATION_TYPE)
    else if (strcmp(filter_type, "NOTIFICATION_TYPE") == 0) {
        filter_type_id = SANDBOX_FILTER_NOTIFICATION_TYPE;
    }
#endif
#if defined(SANDBOX_FILTER_XPC_SERVICE_NAME)
    else if (strcmp(filter_type, "XPC_SERVICE_NAME") == 0) {
        filter_type_id = SANDBOX_FILTER_XPC_SERVICE_NAME;
    }
#endif
#if defined(SANDBOX_FILTER_NVRAM_VARIABLE)
    else if (strcmp(filter_type, "NVRAM_VARIABLE") == 0) {
        filter_type_id = SANDBOX_FILTER_NVRAM_VARIABLE;
    }
#endif
#if defined(SANDBOX_FILTER_POSIX_IPC_NAME)
    else if (strcmp(filter_type, "POSIX_IPC_NAME") == 0) {
        filter_type_id = SANDBOX_FILTER_POSIX_IPC_NAME;
    }
#endif

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

    errno = 0;
    int rc = sandbox_check(pid, operation, filter_type_id, filter_value);

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
    print_json_string(filter_value);
    printf(",\"extra\":null");
    printf(",\"rc\":%d", rc);
    printf(",\"errno\":%d", errno);
    printf(",\"allowed\":%s", rc == 0 ? "true" : "false");
    printf(",\"denied\":%s", rc == 0 ? "false" : "true");
    printf("}\n");
    return 0;
}
