/* Close the policy descriptor before production main. Its real read fails with
 * EBADF; that error must not be published as a zero-byte EOF receipt. */
#define main pw_worker_main
#include "pw_probe_runner.c"
#undef main
int main(int argc, char **argv) {
    close(STDIN_FILENO);
    return pw_worker_main(argc, argv);
}
