/* A fresh ordinary-authority issuer. No token bytes leave its transient mapping;
 * stdout/stderr are not protocol channels and no diagnostics contain tokens. */
#include "pw_extension_channel.h"
#include <dlfcn.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>

typedef char *(*pw_issue_file_fn)(const char *, const char *, uint32_t);
int main(int argc, char **argv) {
    (void)argv;
    struct rlimit core = {0, 0};
    if (setrlimit(RLIMIT_CORE, &core) != 0) return 90;
    if (argc != 1) return 91;
    struct stat info;
    if (fstat(3, &info) || info.st_size < PW_EXTENSION_CHANNEL_BYTES) return 92;
    pw_extension_channel_t *channel = mmap(NULL, sizeof(*channel), PROT_READ | PROT_WRITE, MAP_SHARED, 3, 0);
    close(3);
    if (channel == MAP_FAILED) return 93;
    if (channel->magic != PW_EXTENSION_MAGIC ||
        memchr(channel->target, 0, sizeof(channel->target)) == NULL ||
        atomic_load_explicit(&channel->completed, memory_order_acquire)) return 94;
    channel->pid = getpid(); channel->uid = getuid(); channel->euid = geteuid();
    channel->gid = getgid(); channel->egid = getegid();
    void *library = dlopen("/usr/lib/libsandbox.dylib", RTLD_NOW | RTLD_LOCAL);
    pw_issue_file_fn issue = library ? (pw_issue_file_fn)dlsym(library, "sandbox_extension_issue_file") : NULL;
    if (!issue || !dlsym(library, "sandbox_extension_consume") || !dlsym(library, "sandbox_extension_release")) {
        channel->status = 4;
    } else {
        atomic_store_explicit(&channel->call_boundary, 1, memory_order_release);
        errno = 0;
        char *token = issue("com.apple.app-sandbox.read", channel->target, 0);
        channel->saved_errno = errno;
        if (!token) channel->status = 2;
        else {
            size_t length = strnlen(token, PW_EXTENSION_TOKEN_BYTES);
            if (length == 0 || length >= PW_EXTENSION_TOKEN_BYTES) channel->status = 3;
            else {
                memcpy(channel->token, token, length + 1);
                channel->token_length = (uint32_t)length;
                channel->status = 1;
            }
            pw_extension_erase(token, length);
            free(token);
        }
    }
    atomic_store_explicit(&channel->completed, 1, memory_order_release);
    munmap(channel, sizeof(*channel));
    return 0;
}
