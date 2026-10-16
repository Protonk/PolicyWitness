/* A stand-in for the C worker that reports an identity no generated constant names.
 * It passes the minimum, SDK and executable checks of the build it is planted
 * in, so only the worker identity check can tell it apart. Never runs a specimen. */
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "--version") == 0) {
        printf("pw-probe-runner abi_identity=%s region_bytes=0 max_steps=0 slot_bytes=0\n",
               "0000000000000000000000000000000000000000000000000000000000000000");
        return 0;
    }
    return 7;
}
