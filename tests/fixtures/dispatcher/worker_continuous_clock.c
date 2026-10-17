/* A permitted worker clock import: continuous Mach time. Never runs. */
#include <mach/mach_time.h>
int main(void) { return (int)(mach_continuous_time() & 1u); }
