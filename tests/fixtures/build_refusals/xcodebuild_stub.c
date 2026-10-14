/* The xcodebuild of a developer directory that holds no macOS SDK.
 *
 * The /usr/bin shims validate DEVELOPER_DIR by running its xcodebuild: a
 * license check, `-sdk <name> -find <tool>` to locate the tool they stand in
 * for, and `-sdk <name> -version Path` when xcrun selects an SDK. This
 * stand-in answers the first two from the directory it lives in, so the
 * python3 and git the build script runs before selecting the SDK resolve,
 * and reports that no SDK can be located, so xcrun fails and the script's
 * own refusal is reached. The build refusal controls compile it into a
 * disposable developer directory; it is not part of any product. */
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <libgen.h>

int main(int argc, char **argv) {
    if (argc == 3 && strcmp(argv[1], "-license") == 0 && strcmp(argv[2], "check") == 0) {
        return 0;
    }
    if (argc == 5 && strcmp(argv[1], "-sdk") == 0 && strcmp(argv[3], "-find") == 0) {
        char exe[PATH_MAX];
        uint32_t size = sizeof exe;
        if (_NSGetExecutablePath(exe, &size) != 0) {
            return 1;
        }
        /* This directory first, then the toolchain the directory links to, so a
         * shim never fails to locate a tool here and never requests the
         * Command Line Tools installation it offers when a lookup fails. */
        const char *dir = dirname(exe);
        const char *patterns[] = {"%s/%s", "%s/../../Toolchains/XcodeDefault.xctoolchain/usr/bin/%s"};
        char tool[PATH_MAX];
        struct stat st;
        for (size_t i = 0; i < sizeof patterns / sizeof patterns[0]; i++) {
            snprintf(tool, sizeof tool, patterns[i], dir, argv[4]);
            if (stat(tool, &st) == 0) {
                printf("%s\n", tool);
                return 0;
            }
        }
        fprintf(stderr, "xcodebuild: error: tool '%s' not found\n", argv[4]);
        return 1;
    }
    if (argc == 5 && strcmp(argv[1], "-sdk") == 0 && strcmp(argv[3], "-version") == 0) {
        fprintf(stderr, "xcodebuild: error: SDK \"%s\" cannot be located.\n", argv[2]);
        return 1;
    }
    fprintf(stderr, "xcodebuild: error: unsupported invocation\n");
    return 1;
}
