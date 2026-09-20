/* Include the actual implementation to inspect its private production default.
 * No worker is launched and no policy is applied by this executable. */
// Renaming main removes its implicit return-zero rule; this entry is never called.
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wreturn-type"
#define main pw_worker_main
#include "../../../controller/tools/pw_probe_runner/pw_probe_runner.c"
#undef main
#pragma clang diagnostic pop

int main(void) {
    printf("exec_child_wait=%ld\n", PW_EXEC_CHILD_DEADLINE_MS_DEFAULT);
    return 0;
}
