/* Runnable stub controller for offline dispatch controls: a real Mach-O that
 * records its own resolved path, its arguments and the marker file beside it,
 * independent of any PolicyWitness configuration. It never runs a specimen. */
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void write_json_string(FILE *out, const char *text) {
    fputc('"', out);
    for (const unsigned char *p = (const unsigned char *)text; *p; p++) {
        switch (*p) {
        case '"': fputs("\\\"", out); break;
        case '\\': fputs("\\\\", out); break;
        case '\n': fputs("\\n", out); break;
        case '\r': fputs("\\r", out); break;
        case '\t': fputs("\\t", out); break;
        default:
            if (*p < 0x20) fprintf(out, "\\u%04x", *p);
            else fputc(*p, out);
        }
    }
    fputc('"', out);
}

int main(int argc, char **argv) {
    char buffer[PATH_MAX];
    uint32_t size = sizeof buffer;
    if (_NSGetExecutablePath(buffer, &size) != 0) return 3;
    char resolved[PATH_MAX];
    if (!realpath(buffer, resolved)) return 3;
    const char *receipts = getenv("CONTROL_CONTROLLER_RECEIPTS");
    if (!receipts) return 4;
    char marker_path[PATH_MAX];
    const char *slash = strrchr(resolved, '/');
    size_t directory = slash ? (size_t)(slash - resolved) + 1 : 0;
    if (directory + strlen("controller-marker.txt") + 1 > sizeof marker_path) return 5;
    memcpy(marker_path, resolved, directory);
    strcpy(marker_path + directory, "controller-marker.txt");
    FILE *marker = fopen(marker_path, "rb");
    if (!marker) return 6;
    char content[4096];
    size_t length = fread(content, 1, sizeof content - 1, marker);
    fclose(marker);
    content[length] = '\0';
    FILE *out = fopen(receipts, "a");
    if (!out) return 7;
    fputs("{\"binary\": ", out);
    write_json_string(out, resolved);
    fputs(", \"argv\": [", out);
    for (int i = 1; i < argc; i++) {
        if (i > 1) fputs(", ", out);
        write_json_string(out, argv[i]);
    }
    fputs("], \"marker\": ", out);
    write_json_string(out, content);
    fputs("}\n", out);
    fclose(out);
    return 0;
}
