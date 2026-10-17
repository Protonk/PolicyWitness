/* The worker-clock control: links and calls clock_gettime(CLOCK_MONOTONIC), the
 * import the worker clock rule forbids. Never runs. */
#include <time.h>
int main(void) { struct timespec now; return clock_gettime(CLOCK_MONOTONIC, &now); }
