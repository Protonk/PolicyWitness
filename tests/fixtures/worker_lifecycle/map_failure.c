/* Exercise real map_region's fstat failure without changing the host mapping.
 * Exit 3 alone cannot recover this reason; host assertions must leave it absent. */
#define main pw_worker_main
#include "pw_probe_runner.c"
#undef main
int main(int argc, char **argv) {
    close(3);
    return pw_worker_main(argc, argv);
}
